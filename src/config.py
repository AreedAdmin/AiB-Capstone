"""Configuration loader. Reads ``config/assumptions.yaml`` and ``config/scenarios.yaml``.

Centralising config access in one helper keeps the notebook free of file-path literals
and makes papermill parameter overrides trivial to wire up.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


def load_assumptions(path: Path | None = None) -> dict[str, Any]:
    """Load the central assumption register."""
    path = path or (CONFIG_DIR / "assumptions.yaml")
    with open(path, "r") as fh:
        return yaml.safe_load(fh)


def load_scenarios(path: Path | None = None) -> dict[str, Any]:
    """Load the penetration / price scenario grid."""
    path = path or (CONFIG_DIR / "scenarios.yaml")
    with open(path, "r") as fh:
        return yaml.safe_load(fh)
