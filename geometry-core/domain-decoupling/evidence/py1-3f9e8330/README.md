# GEO-261 PY1 frozen-source receipt

Executed source: `3f9e833008cb6f4db2ec7bc075be55745016b245`.
The runner uses a Git archive of that exact commit, so later worktree changes
are excluded. `summary.json` records the archive file hashes, exact commands,
runner hash, Python version and per-suite results. Raw unittest and process
logs are adjacent to the summary.

```text
python tests/geometry_kernel_receipt.py --source 3f9e833008cb6f4db2ec7bc075be55745016b245 --out "%TEMP%/geometry-tests/geo261-py1-3f9e8330-rerun"
```

| Suite | Discovered | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| geometry | 20 | 20 | 0 | 0 |
| compatibility | 1 | 1 | 0 | 0 |
| isolation | 2 | 2 | 0 | 0 |

The isolation suite actually executes a kernel-only installation with blocked
host/template imports. Its shared-source control test mutates hole containment
and source normal sign, requires both pure and legacy oracles to fail, then
restores the source and requires both to pass. These controls are scoped to
the shared geometry implementation. Native model reconstruction and full
definition/source graph decoupling were not executed or claimed here.

The first receipt-runner setup attempt omitted the unchanged test runner's
`binaries.py` dependency and failed at import before discovering these suites.
The checked-in runner includes that dependency and clears inherited native
override variables. The recorded rerun above is the successful frozen-source
execution; it compiled or executed no native binary.
