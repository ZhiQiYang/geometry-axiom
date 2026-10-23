# Rectangular template validation ledger

Base: `8906afad764cb28323115e731f02041ccbecc5d5`.

This slice adds `tests/test_rectangular_template.py` to `tests/run_all.py` and
`tests/run_all.expected.json`: new suite count 0 → 11. No existing count changes.

Local preparation, 2026-10-16, Windows:

- `python tests/test_rectangular_template.py RectangularTemplateSourceIsolation -v`
  exited 0: 1 passed, 0 failed, 0 skipped.
- AST discovery counted 11 test methods; the registered expected count is 11.
- Native compilation/execution was intentionally deferred to the coordinated
  `p1_validation` queue. No local compiler or WSL build was started. The ten
  native tests and their negative controls are not claimed passed here.

The native receipt must identify the frozen source commit and record actual
pass/fail/skip counts. This ledger is a preparation record, not a substitute
for that receipt or the complete GEO-261/product acceptance gates.
