"""Heat Smart Orkney analytical modules.

Each submodule maps to a numbered section of the report:

* :mod:`src.io_data`       — §5.1 schema-validated loaders
* :mod:`src.cleaning`      — §5.2-5.3 timestamp hygiene + regime taxonomy
* :mod:`src.power_curve`   — §6 power-curve fitting
* :mod:`src.curtailment`   — §7 counterfactual energy + fleet scaling (Q1)
* :mod:`src.demand`        — §8 residential demand profiles + flex decomposition
* :mod:`src.matching`      — §9 supply-demand matching (Q2 + Q3)
* :mod:`src.valuation`     — §10 £/year valuation + sensitivities
* :mod:`src.viz`           — consistent plot styling
"""

__version__ = "0.1.0"
