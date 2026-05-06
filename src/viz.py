"""Consistent plot styling for the HSO report.

We standardise on **Plotly** for the report charts so the rendered HTML
artefact is interactive (hover tooltips, pan, zoom). Matplotlib remains
available for ad-hoc work but is not used by the notebook.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

PALETTE = {
    "wind": "#1f77b4",
    "curtailment": "#d62728",
    "demand": "#2ca02c",
    "absorbed": "#9467bd",
    "neutral": "#7f7f7f",
}


def apply_style() -> None:
    """Register the project's default plotly template."""
    template = go.layout.Template()
    template.layout = go.Layout(
        font=dict(family="Inter, Helvetica, Arial, sans-serif", size=12),
        title=dict(font=dict(size=14)),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis=dict(showgrid=True, gridcolor="#eeeeee", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#eeeeee", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=20, t=60, b=50),
        hovermode="x unified",
        colorway=[
            PALETTE["wind"], PALETTE["curtailment"], PALETTE["demand"],
            PALETTE["absorbed"], PALETTE["neutral"], "#ff7f0e", "#17becf",
        ],
    )
    pio.templates["hso"] = template
    pio.templates.default = "hso"
    # Inline rendering: plotly.js is embedded directly in the notebook
    # output, so the rendered HTML and slide deck work offline.
    pio.renderers.default = "notebook"


def figure(title: str, *, height: int = 420, width: int | None = None) -> go.Figure:
    """Return a styled, empty plotly figure with our default layout."""
    fig = go.Figure()
    fig.update_layout(title=title, height=height, width=width)
    return fig
