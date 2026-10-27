# WSL CI-equivalent receipt for a6f4013364e21bcb7239b5dcc25caac0f6d61f77

Generated 2026-10-27T06:35:29+08:00.  **Verdict: PARTIAL (1 of 7 jobs run: native): green=[] red=['native'] undetermined=[]**

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/d/geometry-axiom-work/wsl-ci-tools/wsl_ci.sh a6f4013364e21bcb7239b5dcc25caac0f6d61f77 native

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=final-a6f4-native2

Method: the jobs, env, matrix and `run:` scripts are read from the SHA's own `.github/workflows/integration-tests.yml` (sha256 b491142a6767e785)
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

- baseline sources used by rule 2: [] 
- exclusivity at start: YES (waited 0.0s; still busy foreign=[] system=[]; seen while waiting=[])
- exclusivity during the run: NO (319 samples; foreign processes seen={'/bin/sh /usr/bin/apt-key --quiet --readonly --keyring /usr/share/keyrings/google-chrome.gpg verify -': 2}; max sampled 1-min loadavg=5.18)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | red | 1 | 5326 | 2 | 1 | 4748.4 | 35 / 105 | OVER CI limit (WSL) x2.09, not red by itself |

### native: red

- exit code 1
- rule 2 (flaky re-run) did not excuse: failed counts of the failing rows do not add up to the run_all total ([2] vs 2); not excused: ['mutation:check', 'node:tests-js']
- failed_suites:
    - mutation:check
    - node:tests-js
- failure_details:
    -   mutation:check
    -     - STALE M61(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M62(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M63(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M64(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M65(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M66(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M67(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -     - STALE M68(原 killed):裁判已變(run_tests.py 或被 TESTS 引用的夾具內容不同);bridge source/oracle restoration
    -   node:tests-js
    -     - ✖ delivered engineering project reopens through a private real service, retains seven bound sources and rejects tampering atomically (38489.389493ms)
    -     - ✖ K2a review B1 legacy live-ref capacity survives ordinary discard, UndoRedo and cold ZIP (14920.396238ms)
    -     - ✖ failing tests:
    -     - ✖ delivered engineering project reopens through a private real service, retains seven bound sources and rejects tampering atomically (38489.389493ms)
    -     - ✖ K2a review B1 legacy live-ref capacity survives ordinary discard, UndoRedo and cold ZIP (14920.396238ms)
- rule 2 (flaky re-run): qualifies=False ; reasons: failed counts of the failing rows do not add up to the run_all total ([2] vs 2); not excused: ['mutation:check', 'node:tests-js']
    - mutation:check: first run FAILED (mutation inventory freshness (not test assertions); exit 1；日誌 /tmp/geometry-tests/run_all-logs/mutation_check.log) | in main baseline: {'mutation:check::*': None} | re-runs: #1 FAIL (exit 1, 17.9s), #2 FAIL (exit 1, 16.9s) | excused=False | failed test(s) NOT failing in any main baseline receipt: ['mutation:check::*']
    - node:tests-js: first run FAILED (日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log) | in main baseline: {'node:tests-js::*': None} | re-runs: #1 PASS (exit 0, 303.8s) | excused=False | failed test(s) NOT failing in any main baseline receipt: ['node:tests-js::*']

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 230, "expected_items": 5329, "ran_suites": 230, "mismatches": ["mutation:check: exit-code-only suite did not report ok (- / mutation inventory freshness (not test assertions); exit 1；日)"], "missing_in_log": [], "extra_in_log": [], "equal": false}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.
