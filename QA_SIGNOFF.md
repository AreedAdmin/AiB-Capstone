# QA Signoff — HSO_report.ipynb

This document tracks final QA before submission. The technical
checklist is in `pla.md` §8. Two team members must sign here before
the deliverable is considered done.

## Checklist

- [ ] Notebook runs end-to-end on a clean clone with `make all` in <5 min.
- [ ] All ~64 unit tests pass (`pytest -q`).
- [ ] Three rendered artefacts exist under `reports/`:
  - [ ] `HSO_report.html` (technical report for Kaluza data team)
  - [ ] `HSO_report.slides.html` (executive deck for the board)
  - [ ] `HSO_report.pdf` (optional — requires LaTeX)
- [ ] Every figure has a caption.
- [ ] Every numeric claim is f-stringed from a cached cell — no hand-typed
      numbers in prose.
- [ ] Active-voice audit passed.
- [ ] Spell-check + grammar pass on every markdown cell.
- [ ] References dated ≤ 2017 only (per HSO FAQ).
- [ ] Assumption register (`config/assumptions.yaml`) printed in §11
      appendix and matches headline numbers.
- [ ] Slide deck rehearsed in 8 minutes.

## Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Project Lead | _to assign_ | | |
| QA Lead | _to assign_ | | |
