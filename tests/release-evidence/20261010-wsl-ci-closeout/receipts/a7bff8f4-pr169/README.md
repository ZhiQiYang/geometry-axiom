# WSL CI-equivalent receipt for a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e

Generated 2026-10-10T06:14:20+08:00.  **Verdict: red: canvas**

Note: PR #169 head a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e (codex/final-release-closeout-20261008), merge-base = main 5cc1ffa1, all 7 jobs, parallel 1, rules 1-3 in force.

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e all

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=pr169

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
- exclusivity at start: YES (waited 5.0s; still busy foreign=[] system=[]; seen while waiting=[])
- exclusivity during the run: NO (256 samples; foreign processes seen={'/opt/google/chrome/chrome --type=gpu-process --no-sandbox --headless=new --ozone-platform=headless -': 168, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=25377 --enable-crash-reporter=, --n': 34, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=27409 --enable-crash-reporter=, --n': 6, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=27906 --enable-crash-reporter=, --n': 64, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=32387 --enable-crash-reporter=, --n': 38, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=35207 --enable-crash-reporter=, --n': 20, '/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=999 --enable-crash-reporter=, --noe': 208, '/opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-handler-pid=25377 --enable-c': 14, '/opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-handler-pid=27409 --enable-c': 1, '/opt/google/chrome/chrome --type=renderer --top-chrome-webui --crashpad-handler-pid=27906 --enable-c': 29}; max sampled 1-min loadavg=4.16)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | green | 0 | 2592 | 0 | 1 | 1067.3 | 15 / 45 | OVER CI limit (WSL) x1.19, not red by itself |
| assembly | green | 0 | 150 | 0 | n/a | 263.8 | 15 / 45 | within (x0.29) |
| documents | green | 0 | 47 | 0 | n/a | 57.6 | 10 / 30 | within (x0.1) |
| grid | green | 0 | 316 | 0 | n/a | 516.7 | 15 / 45 | within (x0.57) |
| canvas | red | 1 | 1593 | 2 | n/a | 1628.2 | 35 / 105 | within (x0.77) |
| space | green | 0 | 228 | 0 | n/a | 293.4 | 15 / 45 | within (x0.33) |
| timber | green | 0 | 79 | 0 | n/a | 161.7 | 20 / 60 | within (x0.13) |

### canvas: red

- exit code 1
- failed_assertion_lines:
    - card pos: [[1,60,60],[2,-20,10]] -> [[1,60,60],[2,100,80]] ✗ 拖卡片無效 {"readOK":true,"nativeExists":true,"localExists":true,"nativeCx":60,"nativeCy":60,"hasPos":true,"localCx":60,"localCy":60,"localHasPo
    - P73 選已知邊一半產生引用式，位置與走向用語一致 ✗ false

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 83, "expected_items": 2593, "ran_suites": 83, "mismatches": [], "missing_in_log": [], "extra_in_log": [], "equal": true}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.

## Erratum (appended by hand after the run)

- "exclusivity during the run: NO" above is a false positive of the sampler: the foreign processes listed are all Chrome gpu/renderer children
  of this run's own Chrome (Chrome rewrites its environ, so the WSL_CI_JOB_TAG marker was not visible).  ci_run.py now also accepts processes whose
  ancestor carries the tag; the later canvas runs (`5cc1ffa1-canvas-info-main`, `a7bff8f4-pr169-canvas-rerun`) report exclusivity YES during the run.
- INFORMATION ONLY, verdict unchanged: canvas alone on MAIN 5cc1ffa1 = green (2054 pass / 0 fail, completed, golden matched, 1907 s);
  canvas alone on the PR head again = red with the identical 1593 pass / 2 fail (same two assertions, same fatal P73), 1641 s.  => deterministic, differential.
