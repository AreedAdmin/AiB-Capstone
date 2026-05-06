"""§8 — residential demand modelling and flexible-load decomposition.

A household's demand decomposes into three layers:

* **Baseline (always-on)** — lights, fridge, standby. Not DR-addressable.
* **Variable** — total minus baseline. The envelope of every shiftable kWh.
* **Flexible** — the share of the variable layer that DR can dispatch
  (heating + immersion). Configured by ``f_flex`` in the assumption register.

The headline output for §9 is :func:`per_household_dr_capacity`, which gives the
maximum kWh a single enrolled household can absorb in a given half-hour, capped
by both half-hour kW capacity and the daily flexible-energy budget.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

HALF_HOUR_HOURS = 0.5


@dataclass
class DemandProfile:
    """Aggregated demand statistics for a household population."""

    daily_profile: pd.DataFrame  # index = half-hour-of-day, cols = mean/p10/p90
    seasonal_profile: pd.DataFrame  # index = (season, hh), cols = mean
    weekday_weekend: pd.DataFrame  # index = (is_weekend, hh), cols = mean


@dataclass
class FlexDecomposition:
    """Per-row baseline / variable / flexible decomposition."""

    df: pd.DataFrame  # adds baseline_kw, variable_kw, flexible_kw columns
    baseline_kw: float
    f_flex: float

    def daily_flexible_kwh_per_household(self) -> float:
        """Mean daily flexible-energy budget per household (kWh)."""
        return float(self.df["flexible_kw"].sum()) * HALF_HOUR_HOURS / max(
            1, self.df["Timestamp"].dt.normalize().nunique()
        )


def half_hour_of_day(ts: pd.Series) -> pd.Series:
    """Encode each timestamp into 0..47 half-hour-of-day."""
    return ts.dt.hour * 2 + (ts.dt.minute >= 30).astype(int)


def season_label(ts: pd.Series) -> pd.Series:
    """Northern-hemisphere meteorological season label."""
    month = ts.dt.month
    return pd.Series(
        np.select(
            [month.isin([12, 1, 2]), month.isin([3, 4, 5]), month.isin([6, 7, 8])],
            ["winter", "spring", "summer"],
            default="autumn",
        ),
        index=ts.index,
    )


def build_profile(df: pd.DataFrame) -> DemandProfile:
    """Compute mean / 10 / 90 percentile daily profile + season + weekday splits."""
    if "Demand_mean_kw" not in df.columns:
        raise ValueError("expected Demand_mean_kw column")
    work = df.copy()
    work["hh"] = half_hour_of_day(work["Timestamp"])
    work["season"] = season_label(work["Timestamp"])
    work["is_weekend"] = work["Timestamp"].dt.dayofweek.isin([5, 6])

    daily = (
        work.groupby("hh")["Demand_mean_kw"]
        .agg(mean="mean", p10=lambda s: s.quantile(0.10), p90=lambda s: s.quantile(0.90))
    )

    seasonal = (
        work.groupby(["season", "hh"])["Demand_mean_kw"].mean().rename("mean").reset_index()
    )
    weekday_weekend = (
        work.groupby(["is_weekend", "hh"])["Demand_mean_kw"].mean().rename("mean").reset_index()
    )
    return DemandProfile(daily_profile=daily, seasonal_profile=seasonal, weekday_weekend=weekday_weekend)


def decompose_flex(
    df: pd.DataFrame,
    *,
    f_flex: float = 0.40,
    baseline_window: str = "24h",
) -> FlexDecomposition:
    """Decompose into baseline / variable / flexible.

    Baseline is the rolling daily minimum of mean demand — a defensible proxy
    for always-on load. Variable = total - baseline. Flexible = ``f_flex``
    times variable, the share DR can dispatch.
    """
    if not 0.0 <= f_flex <= 1.0:
        raise ValueError("f_flex must lie in [0, 1]")
    work = df.sort_values("Timestamp").copy()
    work = work.set_index("Timestamp")
    rolling_min = work["Demand_mean_kw"].rolling(baseline_window, min_periods=1).min()
    work["baseline_kw"] = rolling_min.values
    work["variable_kw"] = (work["Demand_mean_kw"] - work["baseline_kw"]).clip(lower=0.0)
    work["flexible_kw"] = work["variable_kw"] * f_flex
    work = work.reset_index()
    return FlexDecomposition(
        df=work,
        baseline_kw=float(rolling_min.mean()),
        f_flex=f_flex,
    )


def per_household_dr_capacity(
    flex: FlexDecomposition,
    *,
    availability: float = 0.70,
    headroom_multiplier: float = 1.5,
) -> pd.DataFrame:
    """kWh a single enrolled household can absorb in a given half-hour.

    Two caps:

    1. **kW headroom**: a household can take ``flexible_kw * headroom_multiplier``
       (i.e. it can absorb a bit more than its average flexible draw thanks to
       thermal storage in tanks/walls).
    2. **Availability**: only a fraction of enrolled homes are available at any
       given event; we apply that as a multiplier on the absorbable kWh.

    Returns a frame indexed by Timestamp with column ``per_hh_kwh``.
    """
    if not 0.0 <= availability <= 1.0:
        raise ValueError("availability must lie in [0, 1]")
    if headroom_multiplier <= 0:
        raise ValueError("headroom_multiplier must be positive")

    work = flex.df[["Timestamp", "flexible_kw"]].copy()
    abs_kw = work["flexible_kw"] * headroom_multiplier * availability
    work["per_hh_kwh"] = abs_kw * HALF_HOUR_HOURS
    return work[["Timestamp", "per_hh_kwh"]]


def f_flex_sweep(
    df: pd.DataFrame,
    fractions: list[float],
) -> pd.DataFrame:
    """Daily kWh-per-household budget across a list of f_flex values."""
    rows = []
    for f in fractions:
        flex = decompose_flex(df, f_flex=f)
        rows.append({"f_flex": f, "daily_kwh_per_hh": flex.daily_flexible_kwh_per_household()})
    return pd.DataFrame(rows)
