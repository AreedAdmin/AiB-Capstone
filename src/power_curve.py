"""§6 — power-curve construction.

Three fits are provided. The binned-mean curve is the **headline** method
(transparent, defensible, monotone-by-construction). Isotonic and 4-parameter
sigmoid are robustness checks compared against it.

Every fit exposes the same interface:

    pc.predict(wind_ms) -> expected_kw

so :mod:`src.curtailment` can stay agnostic about which curve was selected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.isotonic import IsotonicRegression


@dataclass
class CurveDiagnostics:
    """Holds the headline curve parameters reported in §6."""

    cut_in_ms: float
    rated_ms: float
    rated_kw: float
    cut_out_ms: float | None
    rmse_kw: float
    r2: float
    n_points: int


class PowerCurveProtocol(Protocol):
    def predict(self, wind_ms: np.ndarray | float) -> np.ndarray | float: ...


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_uncurtailed(df: pd.DataFrame) -> pd.DataFrame:
    """Return the subset of rows fit-eligible (regime == ``normal``)."""
    if "regime" not in df.columns:
        raise ValueError("expected a regime column from src.cleaning.clean_turbine")
    out = df.loc[df["regime"] == "normal", ["Wind_ms", "Power_kw"]].dropna()
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Binned-mean curve (headline)
# ---------------------------------------------------------------------------


@dataclass
class BinnedMeanCurve:
    """Bin (wind, power) by 1 m/s and average. Monotonic envelope enforced
    so the fit is non-decreasing up to the rated knee, then flat.
    """

    bin_width: float = 1.0
    bins: np.ndarray = field(default_factory=lambda: np.array([]))
    values: np.ndarray = field(default_factory=lambda: np.array([]))
    counts: np.ndarray = field(default_factory=lambda: np.array([]))
    rated_kw: float = 0.0
    cut_in_ms: float = 0.0
    rated_ms: float = 0.0
    cut_out_ms: float | None = None

    @classmethod
    def fit(cls, wind: np.ndarray, power: np.ndarray, bin_width: float = 1.0) -> "BinnedMeanCurve":
        wind = np.asarray(wind, dtype=float)
        power = np.asarray(power, dtype=float)
        mask = np.isfinite(wind) & np.isfinite(power) & (wind >= 0)
        wind, power = wind[mask], power[mask]

        max_w = float(np.ceil(wind.max() / bin_width) * bin_width) if wind.size else 30.0
        edges = np.arange(0.0, max_w + bin_width, bin_width)
        idx = np.digitize(wind, edges) - 1
        n_bins = len(edges) - 1

        means = np.full(n_bins, np.nan)
        counts = np.zeros(n_bins, dtype=int)
        for b in range(n_bins):
            sel = idx == b
            counts[b] = int(sel.sum())
            if counts[b] > 0:
                means[b] = power[sel].mean()

        # Enforce monotonic non-decreasing rise up to the modal max bin.
        if np.any(np.isfinite(means)):
            cummax = np.fmax.accumulate(np.where(np.isfinite(means), means, -np.inf))
            cummax = np.where(np.isfinite(means), cummax, np.nan)
            means = np.where(np.isfinite(means), np.maximum(means, cummax), means)

        rated_kw = float(np.nanmax(means)) if np.any(np.isfinite(means)) else 0.0
        # Cut-in: lowest bin centre with mean power above the noise floor
        # (max of 5 kW absolute or 1% of rated). The 5% rule used elsewhere is
        # too aggressive on a smooth sigmoid ramp because the first metres of
        # the ramp are physically real but small relative to rated.
        bin_centres = edges[:-1] + bin_width / 2
        cut_in_threshold = max(5.0, 0.01 * rated_kw)
        cut_in_idx = np.where((means >= cut_in_threshold) & np.isfinite(means))[0]
        cut_in_ms = float(bin_centres[cut_in_idx[0]]) if cut_in_idx.size else 0.0

        # Rated speed: lowest bin centre where mean is within 5% of rated.
        # 2% is too tight on noisy data and pushes the estimate into the
        # asymptote region; 5% matches the operational "rated" definition.
        rated_idx = np.where(np.isfinite(means) & (means >= 0.95 * rated_kw))[0]
        rated_ms = float(bin_centres[rated_idx[0]]) if rated_idx.size else cut_in_ms

        return cls(
            bin_width=bin_width,
            bins=bin_centres,
            values=means,
            counts=counts,
            rated_kw=rated_kw,
            cut_in_ms=cut_in_ms,
            rated_ms=rated_ms,
            cut_out_ms=None,
        )

    def predict(self, wind_ms):
        wind = np.atleast_1d(np.asarray(wind_ms, dtype=float))
        out = np.full_like(wind, np.nan, dtype=float)
        finite = np.isfinite(self.values)
        if not finite.any():
            return out if wind.shape != () else float(out)
        bin_centres = self.bins[finite]
        bin_values = self.values[finite]
        # Below physical cut-in: hard zero, regardless of bin-mean noise floor.
        below_cut_in = wind < self.cut_in_ms
        out[below_cut_in] = 0.0
        # Above the highest finite bin: clip to rated.
        above = wind > bin_centres[-1]
        out[above] = self.rated_kw
        # Otherwise interpolate linearly between bin centres.
        mid = ~(below_cut_in | above)
        if mid.any():
            out[mid] = np.interp(wind[mid], bin_centres, bin_values)
        if isinstance(wind_ms, (int, float)):
            return float(out[0])
        return out


# ---------------------------------------------------------------------------
# Isotonic curve
# ---------------------------------------------------------------------------


@dataclass
class IsotonicCurve:
    iso: IsotonicRegression = field(default_factory=lambda: IsotonicRegression(out_of_bounds="clip"))
    rated_kw: float = 0.0

    @classmethod
    def fit(cls, wind: np.ndarray, power: np.ndarray) -> "IsotonicCurve":
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(wind, power)
        return cls(iso=iso, rated_kw=float(np.max(iso.predict(np.asarray(wind)))))

    def predict(self, wind_ms):
        wind = np.atleast_1d(np.asarray(wind_ms, dtype=float))
        out = self.iso.predict(wind)
        if isinstance(wind_ms, (int, float)):
            return float(out[0])
        return out


# ---------------------------------------------------------------------------
# 4-parameter sigmoid
# ---------------------------------------------------------------------------


def _sigmoid(w, rated, midpoint, slope, cut_in):
    expo = -slope * (w - midpoint)
    expo = np.clip(expo, -50.0, 50.0)
    return rated / (1.0 + np.exp(expo)) * (w >= cut_in)


@dataclass
class SigmoidCurve:
    rated_kw: float = 0.0
    midpoint_ms: float = 8.0
    slope: float = 0.8
    cut_in_ms: float = 3.0

    @classmethod
    def fit(cls, wind: np.ndarray, power: np.ndarray) -> "SigmoidCurve":
        rated_guess = float(np.quantile(power, 0.99))
        p0 = (rated_guess, 8.0, 0.8, 3.0)
        bounds = ([0.5 * rated_guess, 4.0, 0.1, 0.0], [1.5 * rated_guess, 14.0, 5.0, 6.0])
        try:
            popt, _ = curve_fit(_sigmoid, wind, power, p0=p0, bounds=bounds, maxfev=10000)
        except Exception:
            popt = p0
        rated, midpoint, slope, cut_in = popt
        return cls(
            rated_kw=float(rated),
            midpoint_ms=float(midpoint),
            slope=float(slope),
            cut_in_ms=float(cut_in),
        )

    def predict(self, wind_ms):
        wind = np.atleast_1d(np.asarray(wind_ms, dtype=float))
        out = _sigmoid(wind, self.rated_kw, self.midpoint_ms, self.slope, self.cut_in_ms)
        if isinstance(wind_ms, (int, float)):
            return float(out[0])
        return out


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def diagnostics(curve: PowerCurveProtocol, wind: np.ndarray, power: np.ndarray) -> CurveDiagnostics:
    """Compute RMSE, R², cut-in / rated / cut-out for a fitted curve."""
    pred = np.asarray(curve.predict(wind))
    actual = np.asarray(power)
    err = pred - actual
    rmse = float(np.sqrt(np.nanmean(err**2)))
    ss_res = float(np.nansum(err**2))
    ss_tot = float(np.nansum((actual - np.nanmean(actual)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    cut_in = float(getattr(curve, "cut_in_ms", 0.0))
    rated_ms = float(getattr(curve, "rated_ms", getattr(curve, "midpoint_ms", 0.0)))
    rated_kw = float(getattr(curve, "rated_kw", float(np.nanmax(pred))))
    cut_out = getattr(curve, "cut_out_ms", None)

    return CurveDiagnostics(
        cut_in_ms=cut_in,
        rated_ms=rated_ms,
        rated_kw=rated_kw,
        cut_out_ms=cut_out,
        rmse_kw=rmse,
        r2=r2,
        n_points=int(len(actual)),
    )


def bootstrap_curve_ci(
    wind: np.ndarray,
    power: np.ndarray,
    *,
    n_boot: int = 50,
    bin_width: float = 1.0,
    alpha: float = 0.05,
    rng_seed: int = 42,
) -> pd.DataFrame:
    """Bootstrap a per-bin (low, median, high) envelope for the binned-mean curve."""
    rng = np.random.default_rng(rng_seed)
    n = len(wind)
    headline = BinnedMeanCurve.fit(wind, power, bin_width=bin_width)
    bins = headline.bins
    rows = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        c = BinnedMeanCurve.fit(wind[idx], power[idx], bin_width=bin_width)
        # Project resampled curve onto the headline bin grid by interpolating
        # the raw bin values, NOT through predict() (which zeroes below the
        # resampled cut-in and would distort the envelope).
        finite = np.isfinite(c.values)
        if finite.any():
            row = np.interp(bins, c.bins[finite], c.values[finite])
        else:
            row = np.full_like(bins, np.nan)
        rows.append(row)
    arr = np.vstack(rows)
    lo = np.nanpercentile(arr, 100 * alpha / 2, axis=0)
    hi = np.nanpercentile(arr, 100 * (1 - alpha / 2), axis=0)
    return pd.DataFrame(
        {
            "wind_ms": bins,
            "mean_kw": headline.values,
            "low_kw": lo,
            "high_kw": hi,
            "n": headline.counts,
        }
    )
