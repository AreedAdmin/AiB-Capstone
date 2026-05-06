.PHONY: help install test lint notebook html pdf slides all clean

help:
	@echo "make install   - install Python deps via pip (requirements.txt)"
	@echo "make test      - run unit tests"
	@echo "make lint      - run ruff + black --check"
	@echo "make notebook  - execute HSO_report.ipynb in place"
	@echo "make html      - render notebook to HTML"
	@echo "make pdf       - render notebook to PDF"
	@echo "make slides    - render notebook to reveal.js slides"
	@echo "make all       - notebook + html + pdf + slides"
	@echo "make clean     - remove generated outputs"

install:
	pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check src tests
	black --check src tests

notebook:
	jupyter nbconvert --to notebook --execute --inplace HSO_report.ipynb

html: notebook
	@mkdir -p reports
	jupyter nbconvert --to html HSO_report.ipynb --output-dir reports

pdf: notebook
	@mkdir -p reports
	jupyter nbconvert --to pdf HSO_report.ipynb --output-dir reports

slides: notebook
	@mkdir -p reports
	jupyter nbconvert --to slides HSO_report.ipynb --output-dir reports \
		--SlidesExporter.reveal_scroll=True

all: notebook html slides

clean:
	rm -rf outputs/cache/* outputs/figures/* outputs/tables/* outputs/runs/*
	rm -rf reports/*.html reports/*.pdf reports/*_files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
