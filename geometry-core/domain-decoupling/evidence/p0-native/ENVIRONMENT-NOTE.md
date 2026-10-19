# GEO-261 baseline environment correction

All attempts use source `1c80751150d0767ba52509537caf8d5542769ccb` in the same unchanged detached Linux checkout. Each execution gets its own private `/tmp` and loopback network namespace.

1. `baseline/`: full `ulimit -s 16384; python3 -u tests/run_all.py --build` completed with exit **1**, 2,821 counted checks: 2,731 passed, 89 failed, one expected Windows GDI harness skip. The sole failing suite was `node:tests-js` (609 passed, 89 failed; 698 registered instead of expected 704).
2. Inspection of the raw Node log found `spawn python ENOENT` / `spawnSync python ENOENT`. WSL has `/usr/bin/python3`, but the deliberately restricted PATH had no `python` executable, and several existing JavaScript tests invoke that name. One module failed during load, accounting for the six missing registered tests.
3. `baseline-node-python/`: a private `/tmp/geo261-bin/python` symlink to `/usr/bin/python3` was added first in PATH. The unchanged source was rerun using `--build --only node:tests-js`. Result: exit **0**, **704 passed, zero failed, zero skipped** in 151.4 suite seconds. Before/after manifests are identical to the initial full run. No product, test, expected-count, host configuration, or installed dependency was modified.
4. `baseline-full-python/`: the separate full rerun with the corrected private PATH completed at 2026-10-15 19:16:01 UTC with exit **0**. All 88 suites ran; 2,827 counted checks comprise **2,826 passed, zero failed, one expected Windows GDI harness skip**. The 14,575 tracked files have identical before/after manifests and both Git statuses are empty. See its `exit.txt`, `summary.json`, and unedited aggregate log.

The initial failed full receipt is preserved. The targeted retry is not relabeled as a complete passing run. The Windows GDI skip is explicitly allowed by the repository runner and is not hidden.
