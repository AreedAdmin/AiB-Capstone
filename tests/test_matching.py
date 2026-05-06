"""Unit tests for src.matching (Q2 + Q3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.matching import (
    avoided_curtailment_curve,
    households_for_targets,
    join_supply_demand,
    n_for_target,
    representative_week,
    supply_half_hourly,
)


def _make_joined(n_periods: int = 48 * 7) -> pd.DataFrame:
    """Build a synthetic joined frame with bursty supply and steady per-hh demand."""
    ts = pd.date_range("2017-06-01", periods=n_periods, freq="30min", tz="UTC")
    supply = np.zeros(n_periods)
    # Three curtailment bursts of 5 half-hours, 2000 kWh each (per turbine).
    for start in (10, 80, 200):
        supply[start : start + 5] = 2000.0
    per_hh_kwh = np.full(n_periods, 0.05)  # half-hour absorbable per household
    return pd.DataFrame({"Timestamp": ts, "supply_kwh": supply, "per_hh_kwh": per_hh_kwh})


def test_supply_half_hourly_resample():
    ts = pd.date_range("2017-06-01", periods=120, freq="1min", tz="UTC")
    df = pd.DataFrame({"Timestamp": ts, "lost_kwh": np.ones(120)})
    s = supply_half_hourly(df, year=2017)
    assert len(s) == 4  # 120 minutes / 30 = 4 buckets
    assert (s["supply_kwh"] == 30.0).all()


def test_join_supply_demand_applies_fleet():
    ts = pd.date_range("2017-06-01", periods=4, freq="30min", tz="UTC")
    supply = pd.DataFrame({"Timestamp": ts, "supply_kwh": [10.0] * 4})
    per_hh = pd.DataFrame({"Timestamp": ts, "per_hh_kwh": [0.05] * 4})
    out = join_supply_demand(supply, per_hh, fleet_size=500, fleet_correlation=1.0)
    assert (out["supply_kwh"] == 5000.0).all()


def test_join_supply_demand_correlation_dampens():
    ts = pd.date_range("2017-06-01", periods=2, freq="30min", tz="UTC")
    supply = pd.DataFrame({"Timestamp": ts, "supply_kwh": [10.0, 10.0]})
    per_hh = pd.DataFrame({"Timestamp": ts, "per_hh_kwh": [0.05, 0.05]})
    out = join_supply_demand(supply, per_hh, fleet_size=500, fleet_correlation=0.85)
    assert (out["supply_kwh"] == 4250.0).all()


def test_avoided_curve_monotone_non_decreasing():
    joined = _make_joined()
    res = avoided_curtailment_curve(joined, n_grid=[0, 100, 500, 1000, 5000, 10000])
    avoided = res.table["avoided_mwh"].values
    assert (np.diff(avoided) >= -1e-9).all()


def test_avoided_curve_zero_at_zero_households():
    joined = _make_joined()
    res = avoided_curtailment_curve(joined, n_grid=[0, 1000])
    assert res.table.loc[res.table["N"] == 0, "avoided_mwh"].iloc[0] == 0.0


def test_avoided_curve_caps_at_total_supply():
    joined = _make_joined()
    res = avoided_curtailment_curve(joined, n_grid=[0, 1_000_000])
    big_n = res.table["avoided_mwh"].iloc[-1]
    assert abs(big_n - res.annual_curtailment_mwh) < 1e-6


def test_n_for_target_inverts_saturation():
    asymptote, n_zero = 100.0, 1000.0
    n = n_for_target(asymptote, n_zero, 50.0)
    # 1 - 50/100 = 0.5; -ln(0.5) = 0.693
    assert abs(n - n_zero * np.log(2)) < 1e-6


def test_n_for_target_target_above_asymptote_is_inf():
    assert n_for_target(100.0, 1000.0, 200.0) == float("inf")


def test_households_for_targets_increasing_with_pct():
    joined = _make_joined()
    res = avoided_curtailment_curve(joined, n_grid=[0, 100, 500, 1000, 2000, 5000, 10000, 50000])
    targets = households_for_targets(res, [25, 50, 80])
    n_vals = targets["N_households"].values
    assert n_vals[0] < n_vals[1] < n_vals[2]


def test_representative_week_returns_columns():
    joined = _make_joined()
    week = representative_week(joined, n_compare=(500, 5000))
    assert "absorbed_kwh_n500" in week.columns
    assert "absorbed_kwh_n5000" in week.columns
    assert (week["absorbed_kwh_n5000"] >= week["absorbed_kwh_n500"] - 1e-9).all()


def test_avoided_curve_records_fit_headlines():
    joined = _make_joined()
    res = avoided_curtailment_curve(joined, n_grid=[0, 100, 1000, 5000, 20000, 100000])
    assert "N_50_pct_avoided" in res.headlines
    assert res.headlines["N_50_pct_avoided"] > 0
