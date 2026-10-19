# GEO-261 P0 native candidate receipt

This validates the proposal/test candidate at the exact source SHA below. It is not acceptance of an implemented core/template split.

- Source HEAD: `17a25e92c75e8c89063e36ca329729980d8ea6a9`
- Command: `ulimit -s 16384; python3 -u tests/run_all.py --build --update-expected`
- Aggregate exit: `0`; expected semantic comparison exit: `0`; tracked source comparison exit: `0`; combined exit: `0`.
- Counted results: 2856 total; 2855 passed; 0 failed; 1 skipped.
- Interval (UTC): 2026-10-15T18:56:56Z to 2026-10-15T19:20:22Z.
- The declared count grows from 2,827 to 2,856 through 29 proposal contract tests; old 88 suite declarations unchanged: `True`.
- Generated expected JSON equals the frozen candidate's original parsed JSON: `True`.
- Expected original bytes restored only after semantic equality: `True`.
- Before/after tracked source identical after expected formatting restoration: `True` (14580 files).
- Before tracked-manifest SHA-256: `5496232b4515869739dd2e1db2fe57af8201700509ce300fff67972c79f1d9e7`.
- After tracked-manifest SHA-256: `5496232b4515869739dd2e1db2fe57af8201700509ce300fff67972c79f1d9e7`.
- Raw aggregate log SHA-256: `6112a27a9ec3ebceb20453abae8fc3bb653fd32cbdb8140de3473df0311b524c`.

Tools: Python 3.12.3; gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0; Node v24.21.0.

Counts mix unit tests, native scenes, and JavaScript assertions; they are not end-to-end scenario counts. The skip details and per-suite rows are in `summary.json`. Raw before/generated expected files, parsed copies, formatting diff, and semantic-comparison receipt are retained in this directory. Full tracked manifests and per-suite logs remain external.

The existing native mutation ledger was checked, not regenerated. No browser job was executed. The oracle selftest was not run because `geometry-core/framing-template/oracle/` is absent at this SHA. The Windows development worktree was not written by this validation.
