# WSL CI-equivalent receipt for 5cc1ffa1ee85120eca14258b86b715151cad274f

Generated 2026-10-10T04:52:01+08:00.  **Verdict: PARTIAL (1 of 7 jobs run: native): green=['native'] red=[] undetermined=[]**

Note: MAIN baseline (attempt 5): native only, rules 1-3 in force; other sessions stopped

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh 5cc1ffa1ee85120eca14258b86b715151cad274f native

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=(none)

Method: the jobs, env, matrix and `run:` scripts are read from the SHA's own `.github/workflows/integration-tests.yml` (sha256 eaf3a2dc4a3b5beb)
and executed verbatim in an ext4 clean clone (one clone per job, `core.autocrlf=false`, detached at the SHA).  Deviations from GitHub:

- actions/checkout replaced by the local clone; actions/upload-artifact skipped (nothing to upload to).
- `sudo apt-get` steps skipped only when every package is already installed (recorded per job); otherwise the job is BLOCKED, never run with sudo.
- `/tmp/` paths and the service port are rewritten per job and TMPDIR is set per job so that two jobs run side by side; CDP ports are the yml's own.
- CI=true, GITHUB_ACTIONS=true, RUNNER_OS=Linux set to mirror the runner; PATH limited to Linux dirs with /opt/node/bin first.
- A per-job PATH shim `python -> /usr/bin/python3` (GitHub's ubuntu image ships python-is-python3; this WSL distro does not and 11 node tests spawn plain `python`).
- Every step runs in a private mount namespace (`unshare -m`) where `/tmp/geometry-tests` (hardcoded by tests/binaries.py) is a per-job dir, because other sessions share this WSL distro and hold `/tmp/geometry-tests/run_all.lock`.
- Before jobs start: wait (bounded) for boot housekeeping / foreign sessions' test load to end, and prime Chrome/gcc/node page caches (recorded in receipt.json `environment_quiesce`, `warm_up`).
- Up to 2 jobs run concurrently on one 12-core WSL VM (the workflow's own max-parallel is 2, but on separate runners).
- Tool versions differ from GitHub's ubuntu-latest image: see receipt.json `tools`.

## Referee rules (decided by the main loop; applied mechanically by this runner)

1. **Timeout**: each job's hard watchdog = the SHA's yml `timeout-minutes` x 3.0 (WSL is slower than a CI runner; the CI limit is an infrastructure limit, not a correctness referee).
   Elapsed time is recorded as measured; exceeding the CI limit is flagged "over CI limit (WSL)" and is NOT red by itself.  Hitting the watchdog (exit 124) is red.
2. **Flaky tests** (native job only): when `run_all.py` ends with failing suites, each failing suite is re-run ALONE in the same clone (`run_all.py --only <suite>`, up to 2 attempts).
   Verdict green ("flaky-rerun-pass") only if a re-run passes AND every failed test id of that suite also failed in a MAIN baseline receipt (`rule2_baseline_sources` in receipt.json); everything else stays red.
   Browser jobs have no per-test identity and are never excused (any failure = red).  The first run's numbers are never rewritten: the receipt keeps exit code and counts of the first run and lists the re-runs separately.
3. **Exclusive**: before starting, wait (bounded) until no other session's compile/test processes are running in this WSL VM; sample for them every 15 s during the run.  Both are recorded in `exclusivity`.

## Rule 1/2/3 evidence

- baseline sources used by rule 2: ['/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1-attempt3-red-1-flaky-test'] ['5cc1ffa1 skipped: it is the output dir of this very run (a run never excuses itself)']
- exclusivity at start: YES (waited 0.0s; still busy foreign=[] system=[]; seen while waiting=[])
- exclusivity during the run: YES (51 samples; foreign processes seen={}; max sampled 1-min loadavg=3.93)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | green | 0 | 2158 | 0 | 1 | 781.5 | 15 / 45 | within (x0.87) |

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 69, "expected_items": 2159, "ran_suites": 69, "mismatches": [], "missing_in_log": [], "extra_in_log": [], "equal": true}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.
