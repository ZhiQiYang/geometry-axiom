# GEO-261 native baseline receipt

This is an executed native baseline, not acceptance of the decoupling implementation.

- Source HEAD: `1c80751150d0767ba52509537caf8d5542769ccb`
- Command: `ulimit -s 16384; python3 -u tests/run_all.py --build`
- Exit: `1`
- Counted results: 2821 total; 2731 passed; 89 failed; 1 skipped.
- Interval (UTC): 2026-10-15T18:22:56Z to 2026-10-15T18:46:43Z.
- Counted values mix unit tests, native scene cases, and JavaScript assertions; they are not end-to-end scenario counts.
- Before/after tracked source identical: `True` (14575 files).
- Before tracked-manifest SHA-256: `c55a996f57900b3f2120f0a3568fd2fcc52d1bd77c6704a6c8e9f7be4e5b28b6`.
- After tracked-manifest SHA-256: `c55a996f57900b3f2120f0a3568fd2fcc52d1bd77c6704a6c8e9f7be4e5b28b6`.
- Raw aggregate log SHA-256: `253f74940f8dc9eefafed758f3b651aea29a91d43cca11a3337daba2ba0b2f74`.

Tools: Python 3.12.3; gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0; Node v24.21.0.

The detached Linux checkout uses private mount/network namespaces and a private `/tmp`.
The precise launch command, suite rows, and skip details are in `summary.json`;
the aggregate output is `run_all.log`, with process status in `exit.txt`.
Full per-suite logs and tracked-file manifests are retained in the external evidence directory.

No expected-count update or mutation ledger regeneration was performed.
`mutation:check` in the aggregate verifies the existing ledger only.
No browser job was executed. The oracle selftest was not run because
`geometry-core/framing-template/oracle/` is absent at this HEAD.
