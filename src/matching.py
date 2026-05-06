"""§9 — supply-demand matching: how much curtailment can N households absorb?

For each half-hour ``t`` in the overlap year:

    supply(t)         = curtailed kWh in that half-hour (from §7)
    per_household(t)  = absorbable kWh per enrolled household (from §8)
    absorbed(t, N)    = min(supply(t), N * per_household(t))

Sum over t to get avoided MWh/year as a function of N. Saturating ``1 − exp``
is fitted to the resulting curve to characterise the diminishing-returns shape
and pull out N_50, N_80, N_max headlines.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


HALF_HOUR_HOURS = 0.5


@dataclass
class MatchingResult:
    """Output of :func:`avoided_curtailment_curve`."""

    table: pd.DataFrame  # columns: N, avoided_mwh, avoided_pct
    annual_curtailment_mwh: float
    fit_params: dict[str, float]  # asymptote, N0
    headlines: dict[str, float | int]  # N_50, N_80, N_max, etc.


def supply_half_hourly(per_row: pd.DataFrame, year: int = 2017) -> pd.DataFrame:
    """Aggregate row-level ``lost_kwh`` to half-hourly supply (kWh).

    Single-turbine basis. Fleet scaling is applied separately so the matching
    engine can sweep fleet sizes without re-aggregating.
    """
    df = per_row.loc[per_row["Timestamp"].dt.year == year, ["Timestamp", "lost_kwh"]].copy()
    if df.empty:
        return pd.DataFrame(columns=["Timestamp", "supply_kwh"])
    half = (
        df.set_index("Timestamp")["lost_kwh"]
        .resample("30min")
        .sum()
        .rename("supply_kwh")
        .reset_index()
    )
    return half


def join_supply_demand(
    supply: pd.DataFrame,
    per_hh: pd.DataFrame,
    *,
    fleet_size: int = 500,
    fleet_correlation: float = 1.0,
) -> pd.DataFrame:
    """Inner-join supply (per-turbine, half-hourly) and per-household kWh.

    Supply is multiplied by fleet_size * correlation here so downstream code
    sees Orkney-wide curtailment.
    """
    s = supply.copy()
    s["supply_kwh"] = s["supply_kwh"] * fleet_size * fleet_correlation
    out = s.merge(per_hh, on="Timestamp", how="inner")
    return out


def avoided_curtailment_curve(
    joined: pd.DataFrame,
    n_grid: list[int],
) -> MatchingResult:
    """Sweep ``N`` and compute avoided curtailment in MWh/year + saturation fit."""
    if joined.empty:
        empty = pd.DataFrame({"N": n_grid, "avoided_mwh": 0.0, "avoided_pct": 0.0})
        return MatchingResult(
            table=empty,
            annual_curtailment_mwh=0.0,
            fit_params={"asymptote_mwh": 0.0, "N0": float("nan")},
            headlines={},
        )

    supply = joined["supply_kwh"].values
    per_hh = joined["per_hh_kwh"].values
    annual_mwh = supply.sum() / 1000.0

    rows = []
    for N in n_grid:
        absorbed = np.minimum(supply, N * per_hh)
        avoided_mwh = absorbed.sum() / 1000.0
        rows.append(
            {
                "N": int(N),
                "avoided_mwh": float(avoided_mwh),
                "avoided_pct": float(avoided_mwh / annual_mwh * 100.0) if annual_mwh > 0 else 0.0,
            }
        )
    table = pd.DataFrame(rows)

    fit_params, headlines = _fit_saturation(table["N"].values, table["avoided_mwh"].values, annual_mwh)
    return MatchingResult(
        table=table,
        annual_curtailment_mwh=annual_mwh,
        fit_params=fit_params,
        headlines=headlines,
    )


def _saturation(n, asymptote, n_zero):
    return asymptote * (1.0 - np.exp(-np.asarray(n) / max(n_zero, 1e-6)))


def _fit_saturation(
    n: np.ndarray,
    avoided_mwh: np.ndarray,
    annual_mwh: float,
) -> tuple[dict[str, float], dict[str, float | int]]:
    if avoided_mwh.max() <= 0 or annual_mwh <= 0:
        return {"asymptote_mwh": 0.0, "N0": float("nan")}, {}
    # Cap the upper bound at exactly annual_mwh — physically impossible to
    # absorb more than the total supply, regardless of what curve_fit converges to.
    p0 = (annual_mwh * 0.9, max(1.0, n.max() / 4))
    bounds = ([0.5 * annual_mwh, 1.0], [annual_mwh, 1e7])
    try:
        popt, _ = curve_fit(_saturation, n, avoided_mwh, p0=p0, bounds=bounds, maxfev=20000)
        asymptote, n_zero = popt
    except Exception:
        asymptote, n_zero = annual_mwh, max(1.0, n.max() / 4)

    def _hh(pct: float) -> float:
        target = pct * annual_mwh
        if target >= asymptote:
            return float("inf")
        return n_for_target(asymptote, n_zero, target)

    def _to_int(x: float) -> int | float:
        return float("inf") if not np.isfinite(x) else int(x)

    headlines = {
        "asymptote_mwh": float(asymptote),
        "N0": float(n_zero),
        "N_50_pct_avoided": _to_int(_hh(0.50)),
        "N_80_pct_avoided": _to_int(_hh(0.80)),
        "N_95_pct_avoided": _to_int(_hh(0.95)),
    }
    return {"asymptote_mwh": float(asymptote), "N0": float(n_zero)}, headlines


def n_for_target(asymptote: float, n_zero: float, target_mwh: float) -> float:
    """Invert the saturation: solve for N given a target avoided-MWh."""
    if target_mwh >= asymptote:
        return float("inf")
    if target_mwh <= 0:
        return 0.0
    ratio = 1.0 - target_mwh / asymptote
    return float(-n_zero * np.log(ratio))


def households_for_targets(
    result: MatchingResult,
    target_pcts: list[float],
) -> pd.DataFrame:
    """Inverse Q3 lookup: households needed to hit each avoidance % target."""
    asymptote = result.fit_params["asymptote_mwh"]
    n_zero = result.fit_params["N0"]
    if not np.isfinite(n_zero) or asymptote <= 0:
        return pd.DataFrame({"target_pct": target_pcts, "N_households": [float("nan")] * len(target_pcts)})
    rows = []
    for pct in target_pcts:
        target_mwh = (pct / 100.0) * result.annual_curtailment_mwh
        rows.append({"target_pct": pct, "N_households": n_for_target(asymptote, n_zero, target_mwh)})
    return pd.DataFrame(rows)


def representative_week(
    joined: pd.DataFrame,
    n_compare: tuple[int, int] = (500, 5000),
) -> pd.DataFrame:
    """Slice the highest-curtailment week and compute absorption for two N values.

    Used by §9 Figure 9.2: a story-telling time-series that shows visually how
    a low-N versus high-N enrolment fills the curtailment troughs.
    """
    if joined.empty:
        return pd.DataFrame()
    weekly = (
        joined.assign(week=joined["Timestamp"].dt.isocalendar().week)
        .groupby("week")["supply_kwh"]
        .sum()
        .sort_values(ascending=False)
    )
    if weekly.empty:
        return pd.DataFrame()
    top_week = int(weekly.index[0])
    week_df = joined.loc[joined["Timestamp"].dt.isocalendar().week == top_week].copy()
    n_low, n_high = n_compare
    week_df[f"absorbed_kwh_n{n_low}"] = np.minimum(week_df["supply_kwh"], n_low * week_df["per_hh_kwh"])
    week_df[f"absorbed_kwh_n{n_high}"] = np.minimum(week_df["supply_kwh"], n_high * week_df["per_hh_kwh"])
    return week_df
