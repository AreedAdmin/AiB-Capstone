#!/usr/bin/env bash
# Re-build the notebook from tools/build_notebook.py, execute it end-to-end,
# and render HTML + slides into reports/. Run from repo root.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> regenerating HSO_report.ipynb from tools/build_notebook.py"
python3 tools/build_notebook.py

echo "==> executing notebook end-to-end"
jupyter nbconvert --to notebook --execute --inplace HSO_report.ipynb

echo "==> rendering HTML report"
jupyter nbconvert --to html HSO_report.ipynb --output-dir reports

echo "==> rendering reveal.js slide deck"
jupyter nbconvert --to slides HSO_report.ipynb --output-dir reports \
    --SlidesExporter.reveal_scroll=True

echo
echo "Done. Outputs:"
ls -la reports/HSO_report.html reports/HSO_report.slides.html 2>/dev/null
