# Heat Smart Orkney — Demand Response Valuation

Capstone consultancy project (AiB 2026). Sizing the £/year prize from residential demand
response on the Orkney Isles. The narrative brief is in [`Project.md`](Project.md); the
engineering blueprint for the notebook pipeline is in [`pla.md`](pla.md).

## Quickstart

```bash
pip install -r requirements.txt        # or: conda env create -f environment.yml && conda activate hso
make test                              # unit tests
make all                               # execute notebook + render HTML + slides
```

The deliverable is `HSO_report.ipynb`, rendered to `reports/HSO_report.html` (technical
report for Kaluza's data team) and `reports/HSO_report.slides.html` (executive deck for
the board).

## Layout

| Path | Purpose |
| --- | --- |
| `Data/` | Raw CSVs (turbine telemetry + residential demand) |
| `src/` | Importable, tested Python modules — the analytical engine |
| `tests/` | Pytest unit tests for `src/` |
| `config/assumptions.yaml` | Central numeric assumption register |
| `config/scenarios.yaml` | Price / penetration scenarios |
| `outputs/` | Generated caches, figures, tables (gitignored) |
| `reports/` | Rendered HTML / PDF / slides (gitignored) |
| `HSO_report.ipynb` | The notebook — single source for all rendered artefacts |

## Deliverable formats

| Output | Audience | Command |
| --- | --- | --- |
| `reports/HSO_report.html` | Kaluza data team | `make html` |
| `reports/HSO_report.pdf`  | Submission archive | `make pdf` |
| `reports/HSO_report.slides.html` | CEO / board | `make slides` |

## Three core questions

1. How much energy is currently curtailed annually across the Orkney Isles?
2. How much can curtailment be reduced at different DR penetration levels?
3. How many households are needed to deliver each level?
