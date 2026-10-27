# Complete recovery F native execution

Executed SHA: `cbf0fb621888596aa14ad5f2349b503e23b1b72d` in clean detached checkout `/workspace/geo337-native-F-cbf0fb62`.

- Actual native exit **0**; timeout **False**; all **230 suites** executed.
- Counted total **5329**, pass **5328**, fail **0**, skip **1**. The original permitted Windows GDI harness skip is visible in stdout.
- Elapsed **1886.996 seconds**, original cap **2100 seconds**; stack **16384 KiB**.
- Request time UTC: `2026-10-27T02:57:31.561377+00:00`. Completion UTC: `2026-10-27T03:28:58.722331+00:00`.
- Command: `ulimit -s 16384` then `python3 tests/run_all.py --build`. No source, assertion, test inventory, expected count, workflow, or timeout changes. Checkout clean after run: **True**.
- Ledger row: `mutation:check                                       -     -     -     -     5.6  mutation inventory freshness (not test assertions); exit 0`.
- Five-second sampled maximum output: **7118848 allocated bytes**, **5479012 logical bytes**. This is a sampled maximum, not an exact instantaneous peak.

## Environment deviations and originals

The current environment has sufficient writable tmpfs at `/tmp`; no SHM, bind mount, symlink, or mount namespace is used. Fixed native output remains `/tmp/geometry-tests`; TMPDIR points to the owned receipt temp directory on /workspace. Device/free-byte data before and after, plus five-second samples, are retained.

Container PID 1 is `tail`, which did not reap killed orphans in the prior a4bd run. This launcher uses process-local `PR_SET_CHILD_SUBREAPER` and reaps only its adopted exited children, identified by parent PID and zombie state. It does not relax the test's empty-process-group assertion. The same original assembly mutation suite passed 12/12 in this run. `REAPER.json`, `REAPED.json`, `reaper.original.py`, and its actual selftest record document the adjustment. Launcher/helper bytes match the previously published commit; see `LAUNCHER_BINDING.json`.

`stdout.bin`/`stderr.bin` are the original native streams; `launcher.stdout.bin`/`launcher.stderr.bin` are separate outer-launcher streams. `native-output.original.tar.gz` retains binaries, fingerprints, and all suite logs. The original end-of-run `SHA256.json` was verified before adding documentation; `ARCHIVE_VERIFICATION.json` verifies every archived regular file against owned output. The enclosing publication MANIFEST covers later additions too.

The withdrawn a4bd complete failure and interrupted first F launcher attempt remain separate evidence directories, with their actual SHAs and exits. They are not relabelled as this attempt. No GitHub Actions execution is claimed by this local container receipt.
