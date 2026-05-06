"""Consistent plot styling for the HSO report.

A single helper applies the same matplotlib style across every figure so the report
and the slide deck look like one coherent document.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

PALETTE = {
    "wind": "#1f77b4",
    "curtailment": "#d62728",
    "demand": "#2ca02c",
    "absorbed": "#9467bd",
    "neutral": "#7f7f7f",
}


def apply_style() -> None:
    """Apply the project plot style. Call once at the top of the notebook."""
    plt.rcParams.update(
        {
            "figure.figsize": (8.0, 4.5),
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "legend.frameon": False,
            "legend.fontsize": 10,
            "font.family": "sans-serif",
        }
    )
