"""§7 — counterfactual energy + fleet scaling (Question 1).

For each row tagged ``curtailed`` by :mod:`src.cleaning`, the counterfactual
power is the value the power curve predicts at that row's wind speed. The
curtailed energy is then ``max(0, expected − actual) * interval_hours``.

The fleet scaling step lifts the single-turbine result to an Orkney-wide
fleet via two assumption-driven multipliers:

* ``fleet_size`` — number of equivalent turbines (HSO FAQ: 500).
* ``fleet_correlation`` — fraction of the fleet curtailed simultaneously.

Both are swept in §10's sensitivity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.cleaning import add_interval_column
from src.power_curve import PowerCurveProtocol


@dataclass
class CurtailmentResult:
    """All artefacts for §7's headline number."""

    per_row: pd.DataFrame  # row-level counterfactual + lost_kwh
    annual_mwh_single_turbine: float
    annual_mwh_fleet: float
    fleet_size: int
    fleet_correlation: float
    headline_year: int

    def headline_table(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                ("Headline year", self.headline_year),
                ("Single-turbine annual curtailment (MWh)", round(self.annual_mwh_single_turbine, 1)),
                ("Fleet size (turbines)", self.fleet_size),
                ("Fleet correlation factor", self.fleet_correlation),
                ("Fleet annual curtailment (MWh)", round(self.annual_mwh_fleet, 1)),
            ],
            columns=["metric", "value"],
        )


def attach_counterfactual(
    df: pd.DataFrame,
    curve: PowerCurveProtocol,
) -> pd.DataFrame:
    """Add ``expected_kw``, ``lost_kw``, ``lost_kwh`` columns.

    Operates on the cleaned & regime-tagged turbine frame from §5. Rows where
    ``regime != 'curtailed'`` get ``lost_kw = 0`` so downstream sums are correct.
    """
    if "regime" not in df.columns:
        raise ValueError("expected a regime column from src.cleaning.clean_turbine")
    out = add_interval_column(df, ts_col="Timestamp")
    expected = np.asarray(curve.predict(out["Wind_ms"].values))
    expected = np.where(np.isfinite(expected), expected, 0.0)
    out["expected_kw"] = expected

    is_curtailed = out["regime"] == "curtailed"
    lost_kw = np.where(is_curtailed, np.maximum(0.0, expected - out["Power_kw"].values), 0.0)
    out["lost_kw"] = lost_kw
    out["lost_kwh"] = lost_kw * out["interval_hours"].values
    return out


def annual_single_turbine_mwh(per_row: pd.DataFrame, year: int = 2017) -> float:
    """Sum ``lost_kwh`` over the calendar year and convert to MWh."""
    mask = per_row["Timestamp"].dt.year == year
    if not mask.any():
        return 0.0
    kwh = float(per_row.loc[mask, "lost_kwh"].sum())
    return kwh / 1000.0


def scale_to_fleet(
    annual_mwh_single: float,
    fleet_size: int,
    fleet_correlation: float = 1.0,
) -> float:
    """Lift the single-turbine MWh figure to fleet level."""
    if fleet_size <= 0:
        raise ValueError("fleet_size must be positive")
    if not 0.0 <= fleet_correlation <= 1.0:
        raise ValueError("fleet_correlation must lie in [0, 1]")
    return annual_mwh_single * fleet_size * fleet_correlation


def quantify_curtailment(
    df: pd.DataFrame,
    curve: PowerCurveProtocol,
    *,
    fleet_size: int = 500,
    fleet_correlation: float = 1.0,
    headline_year: int = 2017,
) -> CurtailmentResult:
    """End-to-end §7 pipeline: counterfactual → annual sum → fleet scale."""
    per_row = attach_counterfactual(df, curve)
    single = annual_single_turbine_mwh(per_row, year=headline_year)
    fleet = scale_to_fleet(single, fleet_size, fleet_correlation)
    return CurtailmentResult(
        per_row=per_row,
        annual_mwh_single_turbine=single,
        annual_mwh_fleet=fleet,
        fleet_size=fleet_size,
        fleet_correlation=fleet_correlation,
        headline_year=headline_year,
    )


def fleet_size_sensitivity(
    annual_mwh_single: float,
    fleet_sizes: list[int],
    correlations: list[float],
) -> pd.DataFrame:
    """Return a (fleet_size × correlation) sensitivity grid in MWh."""
    rows = []
    for n in fleet_sizes:
        for c in correlations:
            rows.append(
                {
                    "fleet_size": n,
                    "correlation": c,
                    "annual_mwh": scale_to_fleet(annual_mwh_single, n, c),
                }
            )
    return pd.DataFrame(rows)


def aggregate_for_heatmap(per_row: pd.DataFrame, year: int = 2017) -> pd.DataFrame:
    """Build a (month × hour-of-day) MWh heatmap dataframe.

    Used by §7's Figure 7.2: where in the year the curtailment clusters.
    """
    df = per_row.loc[per_row["Timestamp"].dt.year == year].copy()
    df["month"] = df["Timestamp"].dt.month
    df["hour"] = df["Timestamp"].dt.hour
    grid = (
        df.groupby(["month", "hour"])["lost_kwh"].sum().div(1000.0).unstack(fill_value=0.0)
    )
    return grid


def daily_timeseries(per_row: pd.DataFrame, year: int = 2017) -> pd.DataFrame:
    """Daily MWh time series for §7 Figure 7.1 / 7.3."""
    df = per_row.loc[per_row["Timestamp"].dt.year == year].copy()
    daily = (
        df.assign(date=df["Timestamp"].dt.date)
        .groupby("date")["lost_kwh"]
        .sum()
        .div(1000.0)
        .rename("daily_mwh")
        .reset_index()
    )
    daily["cumulative_mwh"] = daily["daily_mwh"].cumsum()
    return daily


def bootstrap_annual_ci(
    per_row: pd.DataFrame,
    year: int = 2017,
    n_boot: int = 200,
    block_days: int = 7,
    alpha: float = 0.10,
    rng_seed: int = 42,
) -> tuple[float, float]:
    """Block-bootstrap a (low, high) CI on annual single-turbine MWh.

    Resamples by week-long blocks of days to preserve the autocorrelation
    structure that would be destroyed by a naive row-level bootstrap.
    """
    rng = np.random.default_rng(rng_seed)
    df = per_row.loc[per_row["Timestamp"].dt.year == year].copy()
    if df.empty:
        return (0.0, 0.0)
    df["date"] = df["Timestamp"].dt.date
    daily = df.groupby("date")["lost_kwh"].sum().sort_index().values / 1000.0
    n_days = len(daily)
    if n_days == 0:
        return (0.0, 0.0)
    n_blocks = int(np.ceil(n_days / block_days))
    samples = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n_days, n_blocks)
        rolled = np.concatenate([
            np.take(daily, range(s, s + block_days), mode="wrap") for s in starts
        ])[:n_days]
        samples[i] = rolled.sum()
    lo = float(np.quantile(samples, alpha / 2))
    hi = float(np.quantile(samples, 1 - alpha / 2))
    return lo, hi
