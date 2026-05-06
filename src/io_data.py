"""Schema-validated loaders for the two raw CSVs.

Functions here are the only place the rest of the codebase touches the filesystem.
Returning a typed pandas frame plus a SHA-256 hash gives the notebook a stable cache
key for downstream parquet writes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "Data"

TURBINE_FILE = DATA_DIR / "Turbine_telemetry.csv"
DEMAND_FILE = DATA_DIR / "Residential_demand.csv"

TURBINE_SCHEMA = {
    "Timestamp": "string",
    "Power_kw": "float64",
    "Setpoint_kw": "float64",
    "Wind_ms": "float64",
}
DEMAND_SCHEMA = {
    "Timestamp": "string",
    "Demand_mean_kw": "float64",
    "N_households": "Int64",
}


@dataclass(frozen=True)
class LoadResult:
    """Container for a loaded dataframe and the hash of its raw source file."""

    df: pd.DataFrame
    sha256: str
    path: Path

    @property
    def short_hash(self) -> str:
        return self.sha256[:12]


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_columns(df: pd.DataFrame, schema: dict[str, str], path: Path) -> None:
    missing = set(schema) - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {sorted(missing)}")


def load_turbine(path: Path | None = None) -> LoadResult:
    """Load ``Turbine_telemetry.csv`` with parsed UTC timestamps."""
    path = Path(path) if path else TURBINE_FILE
    df = pd.read_csv(path, dtype=TURBINE_SCHEMA)
    _validate_columns(df, TURBINE_SCHEMA, path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)
    return LoadResult(df=df, sha256=_file_hash(path), path=path)


def load_demand(path: Path | None = None) -> LoadResult:
    """Load ``Residential_demand.csv`` with parsed UTC timestamps."""
    path = Path(path) if path else DEMAND_FILE
    df = pd.read_csv(path, dtype=DEMAND_SCHEMA)
    _validate_columns(df, DEMAND_SCHEMA, path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)
    return LoadResult(df=df, sha256=_file_hash(path), path=path)
