"""Unit tests for src.cleaning regime taxonomy and helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.cleaning import (
    add_interval_column,
    clean_demand,
    clean_turbine,
    detect_gaps,
    estimate_interval,
)


def _make_turbine_frame(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2017-06-01", periods=n, freq="1min", tz="UTC")
    wind = rng.uniform(2.0, 12.0, size=n)
    nameplate = 900.0
    power = np.clip((wind / 12.0) ** 3 * nameplate, 0, nameplate)
    setpoint = np.full(n, nameplate)
    return pd.DataFrame(
        {"Timestamp": ts, "Power_kw": power, "Setpoint_kw": setpoint, "Wind_ms": wind}
    )


def test_clean_turbine_normal_only():
    df = _make_turbine_frame()
    out, ledger = clean_turbine(df)
    assert ledger.rows_in == ledger.rows_out
    assert "regime" in out.columns
    assert ledger.regime_counts["normal"] == len(out)
    assert ledger.regime_counts["curtailed"] == 0


def test_clean_turbine_tags_curtailment():
    df = _make_turbine_frame(120)
    # Force a 30-minute curtailment block: setpoint at 50% of nameplate.
    df.loc[40:69, "Setpoint_kw"] = 450.0
    df.loc[40:69, "Power_kw"] = 400.0  # below the reduced setpoint
    out, ledger = clean_turbine(df)
    assert ledger.regime_counts["curtailed"] == 30


def test_clean_turbine_tags_storm():
    df = _make_turbine_frame(60)
    df.loc[10:25, "Wind_ms"] = 32.0  # above the 30 m/s peak cutout
    out, ledger = clean_turbine(df)
    assert ledger.regime_counts["storm"] >= 16


def test_clean_turbine_drops_negative_power():
    df = _make_turbine_frame(50)
    df.loc[5, "Power_kw"] = -10.0
    out, ledger = clean_turbine(df)
    assert ledger.negative_power_dropped == 1
    assert ledger.rows_out == 49


def test_clean_turbine_drops_duplicates():
    df = _make_turbine_frame(20)
    dup = df.iloc[[5]]
    df = pd.concat([df, dup], ignore_index=True)
    out, ledger = clean_turbine(df)
    assert ledger.duplicates_dropped == 1


def test_clean_turbine_tags_downtime():
    df = _make_turbine_frame(60)
    df.loc[20:30, "Power_kw"] = 0.0
    df.loc[20:30, "Wind_ms"] = 8.0  # well above cut-in
    out, ledger = clean_turbine(df)
    assert ledger.regime_counts["downtime"] >= 5


def test_estimate_interval_minute():
    ts = pd.Series(pd.date_range("2017-01-01", periods=10, freq="1min"))
    assert estimate_interval(ts) == pd.Timedelta("1min")


def test_estimate_interval_half_hour():
    ts = pd.Series(pd.date_range("2017-01-01", periods=10, freq="30min"))
    assert estimate_interval(ts) == pd.Timedelta("30min")


def test_detect_gaps_finds_skipped_minutes():
    ts = pd.Series(
        pd.to_datetime(
            [
                "2017-01-01 00:00",
                "2017-01-01 00:01",
                "2017-01-01 00:02",
                "2017-01-01 00:30",  # 28-min gap
                "2017-01-01 00:31",
            ]
        )
    )
    gaps = detect_gaps(ts, pd.Timedelta("1min"))
    assert len(gaps) == 1


def test_clean_demand_excludes_anomaly():
    ts = pd.date_range("2017-01-01", periods=10, freq="30min", tz="UTC")
    df = pd.DataFrame(
        {
            "Timestamp": ts,
            "Demand_mean_kw": np.linspace(0.2, 0.5, 10),
            "N_households": [5000] * 5 + [30000] * 5,
        }
    )
    out, ledger = clean_demand(df, exclude_anomaly=True, anomaly_n_threshold=15000)
    assert ledger["rows_in"] == 10
    assert ledger["rows_anomaly"] == 5
    assert len(out) == 5


def test_add_interval_column_caps_gaps():
    ts = pd.to_datetime(
        ["2017-01-01 00:00", "2017-01-01 00:01", "2017-01-01 02:00"]
    )
    df = pd.DataFrame({"Timestamp": ts, "Power_kw": [1.0, 1.0, 1.0]})
    out = add_interval_column(df)
    assert (out["interval_hours"] <= 1.0).all()
