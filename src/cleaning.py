"""§5 — timestamp hygiene, gap detection, regime taxonomy.

Regime taxonomy (turbine):

    normal      — uncurtailed, within wind envelope
    curtailed   — setpoint reduced below nameplate threshold
    downtime    — power reads zero with sufficient wind for >= 5 consecutive minutes
    storm       — wind speed beyond storm-cutout thresholds
    anomaly     — physically implausible (e.g. negative power)

Demand cleaning is lighter: identify and optionally exclude the Sept-Oct 2017
``N_households`` jump (HSO FAQ flags this as anomalous).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

REGIMES = ("normal", "curtailed", "downtime", "storm", "anomaly")

CUT_IN_MS_DEFAULT = 3.0  # below this, zero power is expected, not downtime


@dataclass
class CleaningLedger:
    """Row-level accounting of every cleaning rule applied."""

    rows_in: int
    rows_out: int
    duplicates_dropped: int
    nat_dropped: int
    negative_power_dropped: int
    overshoot_count: int
    regime_counts: dict[str, int]

    def as_table(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                ("rows_in", self.rows_in),
                ("rows_out", self.rows_out),
                ("duplicates_dropped", self.duplicates_dropped),
                ("NaT_timestamps_dropped", self.nat_dropped),
                ("negative_power_dropped", self.negative_power_dropped),
                ("overshoot_setpoint_flagged", self.overshoot_count),
                *[(f"regime_{k}", v) for k, v in self.regime_counts.items()],
            ],
            columns=["metric", "value"],
        )


def _detect_nameplate(setpoints: pd.Series) -> float:
    """Estimate nameplate capacity as the modal setpoint (rounded to nearest kW)."""
    rounded = setpoints.round().dropna()
    if rounded.empty:
        raise ValueError("setpoint series is empty — cannot detect nameplate")
    return float(rounded.mode().iloc[0])


def _rolling_mean_ms(wind: pd.Series, ts: pd.Series, window_min: int = 10) -> pd.Series:
    """Rolling mean wind speed by elapsed time, robust to gaps."""
    return (
        pd.Series(wind.values, index=ts)
        .rolling(f"{window_min}min", min_periods=1)
        .mean()
        .values
    )


def clean_turbine(
    df: pd.DataFrame,
    *,
    nameplate_threshold: float = 0.99,
    storm_mean_ms: float = 25.0,
    storm_peak_ms: float = 30.0,
    cut_in_ms: float = CUT_IN_MS_DEFAULT,
    downtime_min_consecutive: int = 5,
) -> tuple[pd.DataFrame, CleaningLedger]:
    """Clean and regime-tag the turbine telemetry.

    Returns a tuple ``(clean_df, ledger)``. ``clean_df`` carries an added column
    ``regime`` whose values are one of :data:`REGIMES`.
    """
    rows_in = len(df)
    df = df.sort_values("Timestamp").reset_index(drop=True)

    nat_dropped = int(df["Timestamp"].isna().sum())
    df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)

    dup_mask = df.duplicated(subset=["Timestamp"], keep="first")
    duplicates_dropped = int(dup_mask.sum())
    df = df.loc[~dup_mask].reset_index(drop=True)

    # Drop physically impossible negative power.
    neg_mask = df["Power_kw"] < 0
    negative_power_dropped = int(neg_mask.sum())
    df = df.loc[~neg_mask].reset_index(drop=True)

    nameplate = _detect_nameplate(df["Setpoint_kw"])
    df["nameplate_kw"] = nameplate

    # Setpoint relationship.
    setpoint_norm = df["Setpoint_kw"] / nameplate
    overshoot = df["Power_kw"] > df["Setpoint_kw"] + 1e-3  # tiny tolerance
    overshoot_count = int(overshoot.sum())

    # Storm cutout — uses 10-minute rolling mean and 1-minute peak proxy (= raw value).
    rolling_mean = _rolling_mean_ms(df["Wind_ms"], df["Timestamp"], window_min=10)
    storm_mask = (rolling_mean > storm_mean_ms) | (df["Wind_ms"] > storm_peak_ms)

    # Downtime: zero power with wind > cut-in for N consecutive samples.
    zero_with_wind = (df["Power_kw"] <= 0.5) & (df["Wind_ms"] >= cut_in_ms)
    # Run-length encode the boolean so we can require >= N consecutive.
    grp = (zero_with_wind != zero_with_wind.shift()).cumsum()
    run_len = zero_with_wind.groupby(grp).transform("size")
    downtime_mask = zero_with_wind & (run_len >= downtime_min_consecutive)

    # Curtailed: setpoint below nameplate threshold AND not a storm event.
    curtailed_mask = (setpoint_norm < nameplate_threshold) & ~storm_mask

    # Anomaly: any leftover overshoot (power > setpoint by more than tolerance).
    anomaly_mask = overshoot

    regime = pd.Series("normal", index=df.index, dtype="object")
    # Order matters: anomaly tagged last so it wins over normal but not the physical
    # storm/downtime/curtailed labels.
    regime[curtailed_mask] = "curtailed"
    regime[downtime_mask] = "downtime"
    regime[storm_mask] = "storm"
    # Anomaly sits over normal only (not over curtailed/storm/downtime physical labels).
    anomaly_only = anomaly_mask & (regime == "normal")
    regime[anomaly_only] = "anomaly"

    df["regime"] = regime
    regime_counts = {k: int((regime == k).sum()) for k in REGIMES}

    ledger = CleaningLedger(
        rows_in=rows_in,
        rows_out=len(df),
        duplicates_dropped=duplicates_dropped,
        nat_dropped=nat_dropped,
        negative_power_dropped=negative_power_dropped,
        overshoot_count=overshoot_count,
        regime_counts=regime_counts,
    )
    return df, ledger


def detect_gaps(ts: pd.Series, expected_interval: pd.Timedelta) -> pd.DataFrame:
    """Return a frame of (gap_start, gap_end, duration) where successive timestamps
    are further apart than ``expected_interval`` * 1.5.
    """
    ts_sorted = ts.sort_values().reset_index(drop=True)
    deltas = ts_sorted.diff()
    threshold = expected_interval * 1.5
    gap_mask = deltas > threshold
    return pd.DataFrame(
        {
            "gap_start": ts_sorted[gap_mask.shift(-1, fill_value=False)].values,
            "gap_end": ts_sorted[gap_mask].values,
            "duration": deltas[gap_mask].values,
        }
    )


def clean_demand(
    df: pd.DataFrame,
    *,
    exclude_anomaly: bool = True,
    anomaly_n_threshold: int = 15000,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean residential demand and optionally exclude the N_households anomaly.

    The HSO FAQ flags Sept-Oct 2017 (where ``N_households`` jumps to ~32k) as
    suspicious. We tag those rows and drop them when ``exclude_anomaly=True``.
    """
    rows_in = len(df)
    df = df.sort_values("Timestamp").reset_index(drop=True)
    df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)
    df = df.loc[~df.duplicated("Timestamp", keep="first")].reset_index(drop=True)
    df = df.loc[df["Demand_mean_kw"] > 0].reset_index(drop=True)

    df["is_anomaly"] = df["N_households"].astype("Int64") > anomaly_n_threshold
    rows_anomaly = int(df["is_anomaly"].sum())

    if exclude_anomaly:
        df = df.loc[~df["is_anomaly"]].drop(columns=["is_anomaly"]).reset_index(drop=True)

    return df, {"rows_in": rows_in, "rows_out": len(df), "rows_anomaly": rows_anomaly}


def estimate_interval(ts: pd.Series) -> pd.Timedelta:
    """Estimate the modal sampling interval, in pandas Timedelta units."""
    deltas = ts.sort_values().diff().dropna()
    if deltas.empty:
        raise ValueError("not enough timestamps to estimate interval")
    mode = deltas.mode().iloc[0]
    return pd.Timedelta(mode)


def add_interval_column(df: pd.DataFrame, ts_col: str = "Timestamp") -> pd.DataFrame:
    """Add ``interval_hours`` column based on per-row delta to *next* sample.

    Used by :mod:`src.curtailment` to compute energy from instantaneous power.
    The last row gets the modal interval as its assumed forward-look.
    """
    df = df.copy()
    deltas = df[ts_col].diff().shift(-1)
    fallback = deltas.mode().iloc[0] if not deltas.dropna().empty else pd.Timedelta(minutes=1)
    deltas = deltas.fillna(fallback)
    # Convert to hours; clip pathological gaps so a single missed week doesn't
    # explode the energy integral.
    hours = deltas.dt.total_seconds() / 3600.0
    df["interval_hours"] = np.clip(hours, 0.0, 1.0)  # cap at 1h
    return df
