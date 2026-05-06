"""Unit tests for src.valuation."""

from __future__ import annotations

import math

import pytest

from src.valuation import (
    CostStack,
    kaluza_revenue,
    payback_grid,
    payback_years,
    per_household_value,
    tornado_sensitivity,
    value_avoided,
)


def test_value_avoided_three_scenarios():
    res = value_avoided(1000.0, price_low=35, price_central=45, price_high=55)
    assert res.table.loc[res.table.scenario == "low", "gbp_per_year"].iloc[0] == 35_000.0
    assert res.central_gbp_per_year == 45_000.0
    assert res.table.loc[res.table.scenario == "high", "gbp_per_year"].iloc[0] == 55_000.0


def test_kaluza_revenue_share_proportional():
    rev = kaluza_revenue(1000.0, price_central=45, kaluza_share=0.333)
    assert abs(rev - 1000.0 * 45 * 0.333) < 1e-9


def test_kaluza_revenue_validates_share():
    with pytest.raises(ValueError):
        kaluza_revenue(1000.0, price_central=45, kaluza_share=1.5)


def test_cost_stack_total():
    cs = CostStack(retrofit_gbp=100.0, quantum_heater_gbp=600.0)
    assert cs.per_household_capex == 700.0


def test_payback_years_simple():
    cs = CostStack(retrofit_gbp=100.0, quantum_heater_gbp=600.0)
    yrs = payback_years(100, cost_stack=cs, annual_revenue_gbp=10_000)
    assert yrs == 7.0  # 70_000 capex / 10_000 revenue


def test_payback_years_subsidy_reduces():
    cs = CostStack()
    full = payback_years(100, cost_stack=cs, annual_revenue_gbp=10_000, subsidy_fraction=0.0)
    half = payback_years(100, cost_stack=cs, annual_revenue_gbp=10_000, subsidy_fraction=0.5)
    assert half < full
    assert abs(half - full / 2) < 1e-9


def test_payback_years_zero_revenue_is_inf():
    cs = CostStack()
    assert math.isinf(payback_years(100, cost_stack=cs, annual_revenue_gbp=0.0))


def test_payback_grid_shape():
    cs = CostStack()
    grid = payback_grid(
        n_households_grid=[100, 1000],
        avoided_mwh_per_n={100: 10.0, 1000: 100.0},
        price_central=45,
        kaluza_share=0.333,
        cost_stack=cs,
        subsidy_tiers=[0.25, 0.5, 0.75, 1.0],
    )
    assert len(grid) == 2 * 4
    assert {"N", "subsidy", "payback_years"} == set(grid.columns)


def test_tornado_sorts_by_swing():
    df = tornado_sensitivity(
        central_gbp_per_year=100.0,
        parameters=[
            ("a", 100.0, 80.0, 110.0),  # swing = 30
            ("b", 100.0, 50.0, 200.0),  # swing = 150
            ("c", 100.0, 95.0, 105.0),  # swing = 10
        ],
    )
    assert list(df["parameter"]) == ["b", "a", "c"]


def test_per_household_value_zero_when_no_households():
    assert per_household_value(1000.0, 0, 45.0) == 0.0


def test_per_household_value_correct():
    assert per_household_value(1000.0, 100, 45.0) == 450.0
