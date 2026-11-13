# WSL CI-equivalent receipt for 5afa469056af90a0ad3f82ea6bc4b229ba8de226

Generated 2026-10-10T23:27:17+08:00.  **Verdict: 7/7 green (no flaky-rerun-pass)**

Note: PR #184 head 5afa469056af90a0ad3f82ea6bc4b229ba8de226 (axiom/adopt-panel-fill-pf0-20261010): PF-0 r2 adopted into 公理層, all 7 jobs, parallel 1, rules 1-3 in force.

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh 5afa469056af90a0ad3f82ea6bc4b229ba8de226 all

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=pr184

Method: the jobs, env, matrix and `run:` scripts are read from the SHA's own `.github/workflows/integration-tests.yml` (sha256 faddb699f3be004b)
and executed verbatim in an ext4 clean clone (one clone per job, `core.autocrlf=false`, detached at the SHA).  Deviations from GitHub:

- actions/checkout replaced by the local clone; actions/upload-artifact skipped (nothing to upload to).
- `sudo apt-get` steps skipped only when every package is already installed (recorded per job); otherwise the job is BLOCKED, never run with sudo.
- `/tmp/` paths and the service port are rewritten per job and TMPDIR is set per job so that two jobs run side by side; CDP ports are the yml's own.
- CI=true, GITHUB_ACTIONS=true, RUNNER_OS=Linux set to mirror the runner; PATH limited to Linux dirs with /opt/node/bin first.
- A per-job PATH shim `python -> /usr/bin/python3` (GitHub's ubuntu image ships python-is-python3; this WSL distro does not and 11 node tests spawn plain `python`).
- Every step runs in a private mount namespace (`unshare -m`) where `/tmp/geometry-tests` (hardcoded by tests/binaries.py) is a per-job dir, because other sessions share this WSL distro and hold `/tmp/geometry-tests/run_all.lock`.
- Before jobs start: wait (bounded) for boot housekeeping / foreign sessions' test load to end, and prime Chrome/gcc/node page caches (recorded in receipt.json `environment_quiesce`, `warm_up`).
- Up to 1 jobs run concurrently on one 12-core WSL VM (the workflow's own max-parallel is 2, but on separate runners).
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
- exclusivity during the run: YES (329 samples; foreign processes seen={}; max sampled 1-min loadavg=4.23)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | green | 0 | 2610 | 0 | 1 | 1135.9 | 15 / 45 | OVER CI limit (WSL) x1.26, not red by itself |
| assembly | green | 0 | 150 | 0 | n/a | 278.2 | 15 / 45 | within (x0.31) |
| documents | green | 0 | 47 | 0 | n/a | 66.5 | 10 / 30 | within (x0.11) |
| grid | green | 0 | 346 | 0 | n/a | 592.2 | 15 / 45 | within (x0.66) |
| canvas | green | 0 | 2207 | 0 | n/a | 2548.5 | 35 / 105 | OVER CI limit (WSL) x1.21, not red by itself |
| space | green | 0 | 228 | 0 | n/a | 301.4 | 15 / 45 | within (x0.33) |
| timber | green | 0 | 79 | 0 | n/a | 181.2 | 20 / 60 | within (x0.15) |

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 83, "expected_items": 2611, "ran_suites": 83, "mismatches": [], "missing_in_log": [], "extra_in_log": [], "equal": true}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.
