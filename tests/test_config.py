"""Smoke tests for config loaders."""

from __future__ import annotations

from src.config import load_assumptions, load_scenarios


def test_assumptions_load_minimum_keys():
    a = load_assumptions()
    for key in (
        "n_households_orkney",
        "fleet_size",
        "f_flex",
        "availability",
        "wholesale_price_gbp_per_mwh",
    ):
        assert key in a, f"missing assumption: {key}"


def test_assumptions_value_ranges():
    a = load_assumptions()
    assert 0.0 < a["f_flex"] < 1.0
    assert 0.0 < a["availability"] <= 1.0
    assert a["fleet_size"] > 0
    assert a["wholesale_price_gbp_per_mwh"] > 0


def test_scenarios_load():
    s = load_scenarios()
    assert "penetration_grid" in s
    assert "price_scenarios" in s
    assert s["penetration_grid"][0] == 0
    assert s["price_scenarios"]["low"] < s["price_scenarios"]["high"]
