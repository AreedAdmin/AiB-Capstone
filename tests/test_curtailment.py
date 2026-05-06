"""Unit tests for src.curtailment (Q1)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.curtailment import (
    aggregate_for_heatmap,
    annual_single_turbine_mwh,
    attach_counterfactual,
    bootstrap_annual_ci,
    daily_timeseries,
    fleet_size_sensitivity,
    quantify_curtailment,
    scale_to_fleet,
)


class _FlatCurve:
    """Stub curve that returns a constant rated power above cut-in."""

    rated_kw = 900.0
    cut_in_ms = 3.0
    rated_ms = 12.0

    def predict(self, wind):
        wind = np.atleast_1d(np.asarray(wind, dtype=float))
        out = np.where(wind >= self.cut_in_ms, self.rated_kw, 0.0)
        if isinstance(wind, np.ndarray) and wind.ndim:
            return out
        return float(out[0])


def _make_year_frame(year: int = 2017) -> pd.DataFrame:
    """Build a 1-min frame across one full year with one curtailed minute."""
    ts = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="1min", tz="UTC", inclusive="left")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "Power_kw": 500.0,
            "Setpoint_kw": 900.0,
            "Wind_ms": 8.0,
            "regime": "normal",
        }
    )
    return df


def test_attach_counterfactual_zero_when_normal():
    df = _make_year_frame().head(100)
    out = attach_counterfactual(df, _FlatCurve())
    assert (out["lost_kw"] == 0).all()
    assert (out["lost_kwh"] == 0).all()


def test_attach_counterfactual_lost_when_curtailed():
    df = _make_year_frame().head(60)  # 60 minutes
    df.loc[10:19, "regime"] = "curtailed"
    df.loc[10:19, "Power_kw"] = 200.0
    df.loc[10:19, "Setpoint_kw"] = 200.0
    out = attach_counterfactual(df, _FlatCurve())
    # Each curtailed minute: expected 900 − actual 200 = 700 kW for 1/60 h.
    expected_per_row_kwh = 700 * (1 / 60)
    lost_total = out["lost_kwh"].sum()
    assert abs(lost_total - 10 * expected_per_row_kwh) < 1e-6


def test_annual_single_turbine_mwh_filters_to_year():
    ts = pd.to_datetime(["2016-12-31 23:58", "2017-01-01 00:01", "2017-12-31 23:59"], utc=True)
    df = pd.DataFrame({"Timestamp": ts, "lost_kwh": [100.0, 100.0, 100.0]})
    mwh = annual_single_turbine_mwh(df, year=2017)
    # 200 kWh in 2017 = 0.2 MWh
    assert abs(mwh - 0.2) < 1e-9


def test_scale_to_fleet_multiplies():
    assert scale_to_fleet(100.0, fleet_size=500, fleet_correlation=1.0) == 50000.0
    assert scale_to_fleet(100.0, fleet_size=500, fleet_correlation=0.85) == 42500.0


def test_scale_to_fleet_validates_inputs():
    import pytest

    with pytest.raises(ValueError):
        scale_to_fleet(100.0, 0)
    with pytest.raises(ValueError):
        scale_to_fleet(100.0, 500, fleet_correlation=1.5)


def test_fleet_size_sensitivity_grid_shape():
    grid = fleet_size_sensitivity(100.0, fleet_sizes=[250, 500], correlations=[0.85, 1.0])
    assert len(grid) == 4
    assert set(grid["fleet_size"]) == {250, 500}


def test_quantify_curtailment_end_to_end():
    df = _make_year_frame()
    df.loc[100:200, "regime"] = "curtailed"
    df.loc[100:200, "Power_kw"] = 100.0
    df.loc[100:200, "Setpoint_kw"] = 100.0
    res = quantify_curtailment(df, _FlatCurve(), fleet_size=10, fleet_correlation=1.0)
    assert res.annual_mwh_fleet == res.annual_mwh_single_turbine * 10


def test_aggregate_for_heatmap_dimensions():
    df = _make_year_frame()
    df.loc[100:160, "regime"] = "curtailed"
    df.loc[100:160, "Power_kw"] = 100.0
    out = attach_counterfactual(df, _FlatCurve())
    grid = aggregate_for_heatmap(out, year=2017)
    assert grid.shape[0] >= 1  # at least one month present
    assert grid.shape[1] <= 24


def test_daily_timeseries_monotone_cumulative():
    df = _make_year_frame()
    df.loc[100:200, "regime"] = "curtailed"
    df.loc[100:200, "Power_kw"] = 100.0
    out = attach_counterfactual(df, _FlatCurve())
    daily = daily_timeseries(out, year=2017)
    cum = daily["cumulative_mwh"].values
    assert (np.diff(cum) >= -1e-9).all()


def test_bootstrap_annual_ci_returns_finite_band():
    df = _make_year_frame()
    df.loc[::200, "regime"] = "curtailed"
    df.loc[::200, "Power_kw"] = 100.0
    out = attach_counterfactual(df, _FlatCurve())
    lo, hi = bootstrap_annual_ci(out, year=2017, n_boot=20, block_days=7)
    assert np.isfinite(lo) and np.isfinite(hi)
    assert hi >= lo
