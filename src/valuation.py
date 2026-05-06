"""§10 — £/year valuation, subsidy break-even, tornado sensitivity.

Convention: every monetary figure is in pounds sterling. MWh × £/MWh = £.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ValuationResult:
    """Three-scenario valuation of avoided curtailment."""

    table: pd.DataFrame  # scenario, mwh, gbp_per_mwh, gbp_per_year
    central_gbp_per_year: float


def value_avoided(
    avoided_mwh: float,
    *,
    price_low: float,
    price_central: float,
    price_high: float,
) -> ValuationResult:
    """Convert avoided MWh to £/year across three price scenarios."""
    rows = [
        {"scenario": "low", "avoided_mwh": avoided_mwh, "gbp_per_mwh": price_low,
         "gbp_per_year": avoided_mwh * price_low},
        {"scenario": "central", "avoided_mwh": avoided_mwh, "gbp_per_mwh": price_central,
         "gbp_per_year": avoided_mwh * price_central},
        {"scenario": "high", "avoided_mwh": avoided_mwh, "gbp_per_mwh": price_high,
         "gbp_per_year": avoided_mwh * price_high},
    ]
    table = pd.DataFrame(rows)
    return ValuationResult(table=table, central_gbp_per_year=avoided_mwh * price_central)


# ---------------------------------------------------------------------------
# Cost stack & break-even
# ---------------------------------------------------------------------------


@dataclass
class CostStack:
    """Per-household one-off install + assumed-zero recurring cost.

    Per the HSO FAQ: 'Assume a simplified cost structure with fixed costs per
    control equipment installation. All other infrastructure costs are assumed
    to be amortised over time.'
    """

    retrofit_gbp: float = 100.0
    quantum_heater_gbp: float = 600.0

    @property
    def per_household_capex(self) -> float:
        return self.retrofit_gbp + self.quantum_heater_gbp


def kaluza_revenue(
    avoided_mwh: float,
    *,
    price_central: float,
    kaluza_share: float,
) -> float:
    """Kaluza's annual revenue at a given value-share."""
    if not 0.0 <= kaluza_share <= 1.0:
        raise ValueError("kaluza_share must lie in [0, 1]")
    return avoided_mwh * price_central * kaluza_share


def payback_years(
    n_households: int,
    *,
    cost_stack: CostStack,
    annual_revenue_gbp: float,
    subsidy_fraction: float = 0.0,
) -> float:
    """Years to recoup capex per the simplified cost stack."""
    if n_households <= 0:
        return float("inf")
    if annual_revenue_gbp <= 0:
        return float("inf")
    capex = n_households * cost_stack.per_household_capex * (1.0 - subsidy_fraction)
    return capex / annual_revenue_gbp


def payback_grid(
    n_households_grid: list[int],
    avoided_mwh_per_n: dict[int, float],
    *,
    price_central: float,
    kaluza_share: float,
    cost_stack: CostStack,
    subsidy_tiers: list[float],
) -> pd.DataFrame:
    """Payback-period heatmap (subsidy × penetration)."""
    rows = []
    for n in n_households_grid:
        avoided = avoided_mwh_per_n.get(n, 0.0)
        revenue = kaluza_revenue(avoided, price_central=price_central, kaluza_share=kaluza_share)
        for sub in subsidy_tiers:
            yrs = payback_years(n, cost_stack=cost_stack, annual_revenue_gbp=revenue,
                                subsidy_fraction=sub)
            rows.append({"N": n, "subsidy": sub, "payback_years": yrs})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tornado sensitivity
# ---------------------------------------------------------------------------


@dataclass
class TornadoRow:
    parameter: str
    low_value: float
    high_value: float
    gbp_low: float
    gbp_high: float

    def swing(self) -> float:
        return abs(self.gbp_high - self.gbp_low)


def tornado_sensitivity(
    central_gbp_per_year: float,
    parameters: list[tuple[str, float, float, float]],
) -> pd.DataFrame:
    """Build a tornado chart frame from ±perturbations.

    ``parameters`` is a list of ``(name, central_value, low_value, high_value)``
    tuples already evaluated to £/year at low and high. We accept this
    pre-evaluated form so that callers (the notebook) wire each parameter to
    the full pipeline and inject the resulting £/year here.
    """
    rows = []
    for name, central, low, high in parameters:
        rows.append({
            "parameter": name,
            "central": central,
            "low_value": low,
            "high_value": high,
            "swing": abs(high - low),
        })
    df = pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)
    df["central_gbp_per_year"] = central_gbp_per_year
    return df


def per_household_value(avoided_mwh: float, n_households: int, price_central: float) -> float:
    """£/household/year of avoided-curtailment value."""
    if n_households <= 0:
        return 0.0
    return (avoided_mwh * price_central) / n_households
