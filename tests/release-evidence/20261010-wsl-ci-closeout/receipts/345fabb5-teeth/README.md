# WSL CI-equivalent receipt for 345fabb5d5bd37245ed2c73184cee3f6c8322aa3

Generated 2026-10-10T05:05:28+08:00.  **Verdict: PARTIAL (1 of 7 jobs run: native): green=[] red=['native'] undetermined=[]**

Note: TEETH RUN, not a CI result: main 5cc1ffa1 plus ONE WSL-only commit 345fabb5d5bd37245ed2c73184cee3f6c8322aa3 (never pushed) - M1 test_feedback_store assertion always wrong; M2 test_cli_args fails on first execution only; M3 test_rule_case_executor known flake injected on first execution only. Expected: native red naming M1 and M2; M3 excused as flaky-rerun-pass.

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh 345fabb5d5bd37245ed2c73184cee3f6c8322aa3 native

Environment overrides used: WSL_CI_REPO=/root/ga-ci/teeth-src WSL_CI_LABEL=teeth

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

- baseline sources used by rule 2: ['/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1-attempt3-red-1-flaky-test', '/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1'] 
- exclusivity at start: YES (waited 0.0s; still busy foreign=[] system=[]; seen while waiting=[])
- exclusivity during the run: YES (50 samples; foreign processes seen={}; max sampled 1-min loadavg=3.67)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | red | 1 | 2155 | 3 | 1 | 778.7 | 15 / 45 | within (x0.85) |

### native: red

- exit code 1
- rule 2 (flaky re-run) did not excuse: not excused: ['py:test_cli_args', 'py:test_feedback_store']
- failed_suites:
    - py:test_cli_args
    - py:test_feedback_store
    - py:test_rule_case_executor
- failure_details:
    -   py:test_cli_args
    -     - test_cli_args.CliArgs.test_unknown_option [failure] AssertionError: TEETH-ONLY M2: fails on the first execution only
    -   py:test_feedback_store
    -     - test_feedback_store.FeedbackStore.test_ids_increment_per_day [failure] ?                                                  ^^^
    -   py:test_rule_case_executor
    -     - test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup [error] ProcessLookupError: [Errno 3] No such process
- rule 2 (flaky re-run): qualifies=False ; reasons: not excused: ['py:test_cli_args', 'py:test_feedback_store']
    - py:test_cli_args: first run FAILED (test_cli_args.CliArgs.test_unknown_option [failure] AssertionError: TEETH-ONLY M2: fails on the first execution only) | in main baseline: {'py:test_cli_args::test_cli_args.CliArgs.test_unknown_option': None} | re-runs: #1 PASS (exit 0, 1.7s) | excused=False | failed test(s) NOT failing in any main baseline receipt: ['py:test_cli_args::test_cli_args.CliArgs.test_unknown_option']
    - py:test_feedback_store: first run FAILED (test_feedback_store.FeedbackStore.test_ids_increment_per_day [failure] ?                                                  ^^^) | in main baseline: {'py:test_feedback_store::test_feedback_store.FeedbackStore.test_ids_increment_per_day': None} | re-runs: #1 FAIL (exit 1, 1.0s), #2 FAIL (exit 1, 1.0s) | excused=False | failed test(s) NOT failing in any main baseline receipt: ['py:test_feedback_store::test_feedback_store.FeedbackStore.test_ids_increment_per_day']
    - py:test_rule_case_executor: first run FAILED (test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup [error] ProcessLookupError: [Errno 3] No such process) | in main baseline: {'py:test_rule_case_executor::test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup': '5cc1ffa1-attempt3-red-1-flaky-test'} | re-runs: #1 PASS (exit 0, 4.6s) | excused=True

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 69, "expected_items": 2159, "ran_suites": 69, "mismatches": [], "missing_in_log": [], "extra_in_log": [], "equal": true}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.
