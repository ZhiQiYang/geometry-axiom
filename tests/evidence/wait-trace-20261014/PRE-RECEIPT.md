# Task 13 baseline before receipt diagnostic correction

Product tested head: `3dc7266024df9ff5ad71e84b20a985e09a476b8a`; before/after HEAD identical.
Full native: 89 suites, 2785 pass / 0 fail / 1 named Windows GDI
skip, Node 706/706; actual exit0, 653.330 seconds. Original
run_all --build used, without filters/allow-skip/update-expected. See complete/.

History is retained: root native.json is the first complete exit1 run (Node
registration/expected mismatch, not an assertion failure); final/native logs
are an incomplete second run whose process disappeared when the tool session
became unavailable, actual exit unknown. Its mixed archive includes unfinished
second-run and older first-run artifacts and is not a full receipt. scope-interrupted/ is a controlled stop (actual -15) to fix missing non-api fetch and HTTP-header coverage, not a full pass. The complete
run started with an empty private log directory and a detached capture driver.

Final unit/mutation controls are under scope-final/: seven Python and three Node tests;
seven mutations each actual1 -> restoration0. Two added acceptance tests were
first run red before fixing timer boundaries and adding the workflow gate.
These are diagnostic hook controls, not new tests/mutate.py/C mutation coverage.
The shell kernel strings are test doubles, not WSL execution. Real isolated
bridge smoke/trace is separate from the mocked-native HTTP unit comparison.

Native artifacts: 204 members, individually byte/SHA inventoried.
Binary hashes and sidecars are provided without executable bytes. No continuous
source monitoring or independent binary-byte referee claim is made.
Initial missing-module shell exit was not retained; that log is not a parent
exit receipt. The first run's brief added/reverted assertion is disclosed in
the historical README. Unverified: active local WSL train deployment/trace
archival, formal seven jobs, full canvas and the historical timeout cause.

Shared workflow change is separately described in geometry-web/docs/WAIT-TRACE.md.
No C/SSOT/reader/BACKLOG/decision queue/ledger changes. GEO-219: 無新入口.
