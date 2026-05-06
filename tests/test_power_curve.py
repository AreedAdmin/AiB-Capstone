"""Unit tests for src.power_curve."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.power_curve import (
    BinnedMeanCurve,
    IsotonicCurve,
    SigmoidCurve,
    bootstrap_curve_ci,
    diagnostics,
    filter_uncurtailed,
)


def _synthetic_curve(n: int = 5000, seed: int = 0):
    """Synthetic generator that matches real turbine physics: below cut-in the
    turbine outputs exactly zero (no measurement noise leaks through), then
    rises through the ramp region with Gaussian noise, then plateaus at rated
    with reduced noise.
    """
    rng = np.random.default_rng(seed)
    wind = rng.uniform(0, 20, size=n)
    rated = 900.0
    midpoint = 9.0
    slope = 0.7
    cut_in = 3.0
    expo = -slope * (wind - midpoint)
    expo = np.clip(expo, -50, 50)
    base = rated / (1 + np.exp(expo))
    noise = rng.normal(0, 25.0, size=n)
    power = np.where(wind < cut_in, 0.0, np.clip(base + noise, 0, rated))
    return wind, power


def test_filter_uncurtailed_only_normal():
    df = pd.DataFrame(
        {
            "Wind_ms": [4, 5, 6, 7],
            "Power_kw": [100, 200, 300, 400],
            "regime": ["normal", "curtailed", "normal", "storm"],
        }
    )
    out = filter_uncurtailed(df)
    assert len(out) == 2
    assert set(out["Wind_ms"]) == {4, 6}


def test_binned_mean_curve_recovers_rated_power():
    wind, power = _synthetic_curve()
    pc = BinnedMeanCurve.fit(wind, power)
    assert 850 < pc.rated_kw < 950
    assert 2.0 <= pc.cut_in_ms <= 4.5
    # Synthetic sigmoid plateaus around 12-15 m/s; 95% rule lands in this band.
    assert 10.0 <= pc.rated_ms <= 15.0


def test_binned_mean_predict_below_cut_in_is_zero():
    wind, power = _synthetic_curve()
    pc = BinnedMeanCurve.fit(wind, power)
    assert pc.predict(0.5) == 0.0


def test_binned_mean_predict_clips_to_rated():
    wind, power = _synthetic_curve()
    pc = BinnedMeanCurve.fit(wind, power)
    assert abs(pc.predict(40.0) - pc.rated_kw) < 1e-6


def test_binned_mean_predict_array_in_array_out():
    wind, power = _synthetic_curve()
    pc = BinnedMeanCurve.fit(wind, power)
    out = pc.predict(np.array([1.0, 8.0, 14.0]))
    assert out.shape == (3,)
    assert out[0] == 0.0
    assert out[2] >= out[1]


def test_isotonic_curve_monotonic():
    wind, power = _synthetic_curve()
    iso = IsotonicCurve.fit(wind, power)
    grid = np.linspace(0, 20, 50)
    pred = iso.predict(grid)
    assert np.all(np.diff(pred) >= -1e-9)


def test_sigmoid_curve_recovers_parameters():
    wind, power = _synthetic_curve()
    sig = SigmoidCurve.fit(wind, power)
    assert 850 < sig.rated_kw < 950
    assert 7.0 <= sig.midpoint_ms <= 11.0


def test_diagnostics_reports_low_rmse_for_perfect_fit():
    wind, power = _synthetic_curve()
    pc = BinnedMeanCurve.fit(wind, power)
    d = diagnostics(pc, wind, power)
    assert d.rmse_kw < 100  # noise sd was 25
    assert d.r2 > 0.9


def test_bootstrap_ci_produces_finite_envelope():
    wind, power = _synthetic_curve(n=2000)
    ci = bootstrap_curve_ci(wind, power, n_boot=10)
    finite = ci.dropna(subset=["mean_kw"])
    assert (finite["low_kw"] <= finite["mean_kw"]).all()
    assert (finite["high_kw"] >= finite["mean_kw"]).all()
