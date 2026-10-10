# WSL CI-equivalent receipt for 72a3cbf44814d86606531e6fcbd811aeab11548f

Generated 2026-10-10T09:11:55+08:00.  **Verdict: red: native, grid, canvas**

Note: PR #179 head 72a3cbf44814d86606531e6fcbd811aeab11548f (codex/adopted-ui-single-room-closeout-20261009; base codex/safe-resume-closeout-20261009; contains PR #169 head a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e), merge-base with main = 5cc1ffa1, all 7 jobs, parallel 1, rules 1-3 in force. integration-tests.yml sha256 identical to the #169 run (faddb699f3be004b).

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh 72a3cbf44814d86606531e6fcbd811aeab11548f all

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=pr179

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
- exclusivity during the run: YES (211 samples; foreign processes seen={}; max sampled 1-min loadavg=3.65)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| native | red | 1 | 2575 | 20 | 1 | 1088.4 | 15 / 45 | OVER CI limit (WSL) x1.19, not red by itself |
| assembly | green | 0 | 150 | 0 | n/a | 269.4 | 15 / 45 | within (x0.3) |
| documents | green | 0 | 47 | 0 | n/a | 61.5 | 10 / 30 | within (x0.1) |
| grid | red | 1 | 54 | 0 | n/a | 93.9 | 15 / 45 | within (x0.1) |
| canvas | red | 1 | 1244 | 0 | n/a | 1239.3 | 35 / 105 | within (x0.59) |
| space | green | 0 | 228 | 0 | n/a | 284.9 | 15 / 45 | within (x0.32) |
| timber | green | 0 | 79 | 0 | n/a | 169.7 | 20 / 60 | within (x0.14) |

### native: red

- exit code 1
- rule 2 (flaky re-run) did not excuse: run_all reported other problems besides failing suites: ['expected-count mismatch section', 'expected-count mismatch row note', 'registry check failure', 'unregistered test files']; not excused: ['py:test_rule_case_executor', 'node:hover_pick_scheduler']
- failed_suites:
    - py:test_rule_case_executor
    - node:hover_pick_scheduler
- failure_details:
    -   py:test_rule_case_executor
    -     - test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup [error] ProcessLookupError: [Errno 3] No such process
    -   node:hover_pick_scheduler
    -     - ✖ 120 same-frame moves make one request at the final point (4.418653ms)
    -     - ✖ slow bridge has one in-flight hover and one latest queued point (1.996719ms)
    -     - ✖ leaving before a frame prevents dispatch (3.847408ms)
    -     - ✖ late leave reply cannot resurrect hover; selection stays visible (1.811347ms)
    -     - ✖ moving outside all views supersedes an in-flight pick (2.122303ms)
    -     - ✖ scene change before dispatch and during response invalidates hover (2.221664ms)
    -     - ✖ view transforms, hidden canvas and changed history reject stale replies (1.709983ms)
    -     - ✖ pointerdown uses the exact point directly and supersedes hover (2.365145ms)
- rule 2 (flaky re-run): qualifies=False ; reasons: run_all reported other problems besides failing suites: ['expected-count mismatch section', 'expected-count mismatch row note', 'registry check failure', 'unregistered test files']; not excused: ['py:test_rule_case_executor', 'node:hover_pick_scheduler']
    - py:test_rule_case_executor: first run FAILED (test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup [error] ProcessLookupError: [Errno 3] No such process) | in main baseline: {'py:test_rule_case_executor::test_rule_case_executor.SyntheticNativeFailureBoundaries.test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup': '5cc1ffa1-attempt3-red-1-flaky-test'} | re-runs: #1 FAIL (exit 1, 5.3s), #2 FAIL (exit 1, 5.4s) | excused=False | failure reproduced in 2 re-run(s)
    - node:hover_pick_scheduler: first run FAILED (日誌 /tmp/geometry-tests/run_all-logs/node_hover_pick_scheduler.log) | in main baseline: {'node:hover_pick_scheduler::*': None} | re-runs: #1 FAIL (exit 1, 0.7s), #2 FAIL (exit 1, 0.6s) | excused=False | failed test(s) NOT failing in any main baseline receipt: ['node:hover_pick_scheduler::*']

### grid: red

- exit code 1

### canvas: red

- exit code 1

## native: expected-count and skip cross-check

- expected comparison: {"available": true, "expected_suites": 83, "expected_items": 2595, "ran_suites": 83, "mismatches": ["py:test_serve: expected 45, got 46"], "missing_in_log": [], "extra_in_log": [], "equal": false}
- skip: py:test_gdi_contract x1 allowed=True (skip：requires compiled Windows GDI contract harness ×1（其中 1 個在具名允許清單，平台固有，不計入 exit 3）；日誌 /tmp/geometry-tests/run_all-logs/py_test_gdi_contract.log)

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.

## Erratum / findings (appended by hand after the run; the machine verdict above is unchanged: red: native, grid, canvas)

Tested SHA 72a3cbf44814d86606531e6fcbd811aeab11548f = PR #179 head (base branch codex/safe-resume-closeout-20261009).  integration-tests.yml sha256 is identical to the #169 run (faddb699f3be004b), so the job set/timeouts are the same.

### Determinism (information only; first full run is the verdict)
- canvas alone again (`72a3cbf4-pr179-canvas-rerun`): red, 1244 pass / 0 fail, completed=false, identical FATAL, 1159 s, exclusive YES.
- grid alone again (`72a3cbf4-pr179-grid-rerun`): red, 54 pass / 0 fail, completed=false, identical FATAL, 94 s, exclusive YES.
- 4 of 4 runs (canvas x2, grid x2) die at the same step with the byte-identical payload
  `Grid control unreachable #igSurface {"x":1213,"y":1147.65625,"w":304,"h":38,"hit":false,"disabled":false}`
  right after the assertion "P70 套用只列出同邊界承載面" (geometry-web/grid_system_test.js line 161: `choose('#igSurface', surface)`, the apply-to-surface <select>).
  The helper scrolls the control to the centre and retries 12 times; the control stays at y=1147 in a 1400x900 headless Chrome => not scrollable into view.  => deterministic, not flaky.
- canvas FATAL_UI in the first run carried a connection error text ("無法確認載入結果，已暫停編輯"), the grid job (same fatal) did not: it is a consequence of the P57-P61 pending pdf.worker requests, not the cause.
- The run stops at P70 (1244 assertions), so the sections after P70 (including P73) were NOT executed: 0 failed assertions here does not mean the rest is green.

### Comparison with the two #169 canvas failures (receipt a7bff8f4-pr169)
- "拖卡片無效" (card pos, drag wrong card): now `[[1,60,60],[2,-20,10]] -> [[1,180,120],[2,-20,10]] ✓ 拖卡片有效` in all runs => that failure is gone.
- "P73 選已知邊一半產生引用式，位置與走向用語一致 ✗": NOT EVALUATED (the run dies in P70 before P73) => cannot be called fixed.

### native
- first run: 2575 pass / 20 fail / 1 skip (total 2596), exit 1, 1088 s (over CI limit x1.19, not red by itself).
- run_all.expected.json comparison: 83 suites expected, 83 ran; mismatch `py:test_serve: expected 45, got 46` (commit f5638ec/05e5939 added a test to tests/test_serve.py without bumping tests/run_all.expected.json).
- registry check fails: 5 test files exist but are not registered in tests/run_all.py (they would never run): tests/browser_race_ownership_instrumentation.js (168fc94), tests/issue123_adopted_slices_browser.cjs (2703e47), tests/issue123_caption_browser.cjs (bb7e630), tests/room_outline_direct_rows_browser.js (2703e47), tests/test_scenario_resume_checkpoint.js (128afbe).  tests/run_all.py is untouched between a7bff8f4 and 72a3cbf.
- node:hover_pick_scheduler: 19/19 fail, deterministic, not in any main baseline: `Missing source region: async function render()`.  tests/test_hover_pick_scheduler.js slices app.js by that exact signature; commit 1d016a5 changed it to `async function render(current = presentationCurrent())` and the test was not updated.
- py:test_rule_case_executor::...test_exited_leader_cannot_leave_descendants_or_unbounded_pipe_cleanup failed once in the full run (ProcessLookupError) and also failed in MAIN attempt3 (known flake).  Runner caveat: both standalone re-runs show the suite row 40 total / 40 passed / 0 failed, but the runner's re-run verdict is derived from run_all's exit code, which stays 1 because `--only` still applies this SHA's registry/expected-count failures.  So "failure reproduced in 2 re-run(s)" in the table above is an artefact for this one suite; on its own merits it would qualify as flaky-rerun-pass.  The native job is red regardless (hover_pick_scheduler + expected-count + registry are real and deterministic).  Rules not changed.

### Ancestry note
- 72a3cbf contains #169 head a7bff8f4 and #176 head 9029a8f6, but NOT #177 head 37c217e3 (3 commits missing: e660b77 docs, 3b2cc64 test [patch-equivalent 5a78811 is present], 37c217e docs) and NOT #178 head 4a57b121 (1 docs commit 4a57b12 missing).  merge-base(72a3cbf, 4a57b121) = 128afbec.  What was tested is the content of 72a3cbf only.

### Environment hygiene
- WSL exclusive at start and during the first run (211 samples, no foreign processes).  No sudo; nothing pushed/commented; D:\geometry-axiom only fetched.
