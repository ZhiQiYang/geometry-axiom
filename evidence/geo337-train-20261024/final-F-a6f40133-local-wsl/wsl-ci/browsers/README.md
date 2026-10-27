# WSL CI-equivalent receipt for a6f4013364e21bcb7239b5dcc25caac0f6d61f77

Generated 2026-10-27T08:20:01+08:00.  **Verdict: PARTIAL (6 of 7 jobs run: assembly, documents, grid, canvas, space, timber): green=['assembly', 'documents', 'grid', 'space', 'timber'] red=['canvas'] undetermined=[]**

## How it was run

Command (from Windows):

    wsl -d Ubuntu-24.04 -- bash /mnt/d/geometry-axiom-work/wsl-ci-tools/wsl_ci.sh a6f4013364e21bcb7239b5dcc25caac0f6d61f77 canvas,assembly,documents,grid,space,timber

Environment overrides used: WSL_CI_REPO=(default) WSL_CI_LABEL=final-a6f4-browsers

Method: the jobs, env, matrix and `run:` scripts are read from the SHA's own `.github/workflows/integration-tests.yml` (sha256 b491142a6767e785)
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

- baseline sources used by rule 2: [] 
- exclusivity at start: YES (waited 0.0s; still busy foreign=[] system=[]; seen while waiting=[])
- exclusivity during the run: YES (330 samples; foreign processes seen={}; max sampled 1-min loadavg=2.16)

## Per-job results (exit code and counts are those of the FIRST full run of each job)

| job | verdict | exit | passed | failed | skipped | seconds | CI limit (min) / watchdog (min) | vs CI limit |
|---|---|---|---|---|---|---|---|---|
| assembly | green | 0 | 150 | 0 | n/a | 322.7 | 15 / 45 | within (x0.36) |
| documents | green | 0 | 47 | 0 | n/a | 109.3 | 10 / 30 | within (x0.18) |
| grid | green | 0 | 356 | 0 | n/a | 633.1 | 15 / 45 | within (x0.7) |
| canvas | red | 1 | 2265 | 3 | n/a | 2636.9 | 35 / 105 | OVER CI limit (WSL) x1.26, not red by itself |
| space | green | 0 | 242 | 0 | n/a | 362.2 | 15 / 45 | within (x0.4) |
| timber | green | 0 | 79 | 0 | n/a | 243.1 | 20 / 60 | within (x0.2) |

### canvas: red

- exit code 1
- failed_assertion_lines:
    - P52-3 H(長度軸u) at-line guide 2 A27 +u-n ✗ {"band":{"x":-80,"y":1987,"w":4160,"h":27,"clip":"url(#face-material-clip)","label":"橫向定位示意","hoverNull":true},"expCross":[1987,2014],"sent":[],"rng":null,"exp
    - P52-3 H(長度軸u) at-line guide 2 A27 -u+n ✗ {"band":{"x":-80,"y":1987,"w":4160,"h":27,"clip":"url(#face-material-clip)","label":"橫向定位示意","hoverNull":true},"expCross":[1987,2014],"sent":["line timber 4 27

Logs: `<job>/job.log`; per-job structured data: `<job>/result.json`; aggregate: `receipt.json`.
