# Native execution handoff — complete recovery F passed

Authoritative execution source: **cbf0fb621888596aa14ad5f2349b503e23b1b72d**.

The complete original native workflow command passed in this task's cloud container: **exit 0**, **230 suites**, **5329 counted tests/assertions = 5328 pass + 0 fail + 1 permitted Windows GDI harness skip**. The expected-count and registry checks passed. The workflow's mutation ledger check returned **0** with **123 records, 114 killed, 1 crashed, 5 equivalent, 3 retired, 0 stale/survived/invalid/blocked**. This validates the saved ledger; it is not a new execution of every mutant.

- Original command: `ulimit -s 16384` then `python3 tests/run_all.py --build`.
- F r2 request: 2026-10-27 02:57:31.561 UTC (10:57:31 Taipei).
- F r2 completion: 2026-10-27 03:28:58.722 UTC (11:28:58 Taipei).
- Command elapsed: **1886.996 seconds (31m27s)**; original **2100-second** limit preserved, **no timeout**.
- Source, tests, assertions, expected counts and workflow unchanged. Detached checkout `/workspace/geo337-native-F-cbf0fb62` remained clean.
- Native output sampled every five seconds: maximum **7,118,848 allocated bytes** (~6.79 MiB). Exact per-device free capacity before/after and samples are in the receipt. No SHM, bind, symlink or mount namespace was used.
- Current container PID 1 is `tail`; the executed launcher adds a process-local child subreaper so exited adopted children are actually reaped. The original process-group test passed **12/12**, with no skipped or relaxed assertion. Selftest, helper source, original launcher streams, reaped-PID log and immutable source binding are preserved.
- After completion, no live process with the F checkout cwd or owned binary executable path remained (`OWNED_PROCESSES_AFTER.json`: empty).

## Evidence directories

- `../F-complete/`: authoritative F result, full original stdout/stderr, exact argv/environment/SHA, timeout/stack, native output archive, fingerprints, all suite logs, samples, hashes, archive verification and summary.
- `../a4bd-withdrawn/`: complete earlier **a4bd77e8090f5a82f0c8934c30c5335782293922** execution, started before the target correction. It returned **1** after 1882.501 seconds, with 5327 pass / 1 zombie-reaping failure / 1 allowed skip, plus separate stale-ledger exit 1. Not F acceptance.
- `../F-interrupted/`: first F launcher attempt stopped safely via runner SIGINT cleanup because its reaper used an unavailable procfs children interface. Actual **exit 130**, 129.954 seconds, no timeout. Its original outputs and launcher exception transcript are retained. Not a complete acceptance run.
- `README.md` in this audit directory records the earlier space diagnosis; that report predates the explicit native execution assignment. Its read-only scope statement describes that initial phase.

The prior completed-failure/interruption evidence was published at **1202060804dc05b9d9eb58994be7cf7a3254e05d**, branch `codex/train337-native-validation-20261027`, and all 46 manifest files were retrieved from the remote commit and verified byte-for-byte by size and SHA-256. The final publication adds the complete F receipt, without changing product branches. The enclosing MANIFEST covers every published artifact; the final remote verification receipt is generated after the final commit is pushed.

This native receipt does not claim completion of separately owned browser/card/extra168 work or a GitHub Actions runner execution. No main merge or deployment was performed.
