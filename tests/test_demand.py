"""Unit tests for src.demand."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.demand import (
    build_profile,
    decompose_flex,
    f_flex_sweep,
    half_hour_of_day,
    per_household_dr_capacity,
    season_label,
)


def _make_demand_frame(days: int = 14, n_households: int = 5000) -> pd.DataFrame:
    ts = pd.date_range("2017-06-01", periods=days * 48, freq="30min", tz="UTC")
    hh = np.arange(48)
    profile = 0.2 + 0.3 * (np.sin(np.linspace(0, 2 * np.pi, 48)) + 1) / 2
    demand = np.tile(profile, days)
    rng = np.random.default_rng(0)
    demand = demand + rng.normal(0, 0.02, size=demand.size)
    return pd.DataFrame(
        {"Timestamp": ts, "Demand_mean_kw": np.clip(demand, 0.05, None), "N_households": n_households}
    )


def test_half_hour_of_day_range():
    ts = pd.Series(pd.date_range("2017-01-01", periods=48, freq="30min"))
    hh = half_hour_of_day(ts)
    assert hh.min() == 0
    assert hh.max() == 47


def test_season_label_winter_summer():
    ts = pd.Series(pd.to_datetime(["2017-01-15", "2017-07-15", "2017-04-15"]))
    s = season_label(ts)
    assert list(s) == ["winter", "summer", "spring"]


def test_build_profile_shape():
    df = _make_demand_frame()
    p = build_profile(df)
    assert p.daily_profile.shape == (48, 3)
    assert {"mean", "p10", "p90"} == set(p.daily_profile.columns)
    assert (p.daily_profile["p90"] >= p.daily_profile["mean"]).all()


def test_decompose_flex_baseline_below_total():
    df = _make_demand_frame()
    flex = decompose_flex(df, f_flex=0.4)
    assert (flex.df["baseline_kw"] <= flex.df["Demand_mean_kw"] + 1e-9).all()
    assert (flex.df["variable_kw"] >= -1e-9).all()
    assert (flex.df["flexible_kw"] <= flex.df["variable_kw"] + 1e-9).all()


def test_decompose_flex_validates_f_flex():
    df = _make_demand_frame(days=2)
    with pytest.raises(ValueError):
        decompose_flex(df, f_flex=1.5)


def test_per_household_dr_capacity_zero_when_no_availability():
    df = _make_demand_frame()
    flex = decompose_flex(df, f_flex=0.4)
    cap = per_household_dr_capacity(flex, availability=0.0)
    assert (cap["per_hh_kwh"] == 0).all()


def test_per_household_dr_capacity_scales_with_availability():
    df = _make_demand_frame()
    flex = decompose_flex(df, f_flex=0.4)
    low = per_household_dr_capacity(flex, availability=0.5)["per_hh_kwh"].sum()
    high = per_household_dr_capacity(flex, availability=0.9)["per_hh_kwh"].sum()
    assert high > low
    assert abs(high / low - 0.9 / 0.5) < 1e-6


def test_f_flex_sweep_monotone():
    df = _make_demand_frame()
    sweep = f_flex_sweep(df, [0.20, 0.40, 0.60])
    assert (np.diff(sweep["daily_kwh_per_hh"]) > 0).all()


def test_per_household_dr_capacity_validates_availability():
    df = _make_demand_frame(days=2)
    flex = decompose_flex(df, f_flex=0.4)
    with pytest.raises(ValueError):
        per_household_dr_capacity(flex, availability=1.5)
