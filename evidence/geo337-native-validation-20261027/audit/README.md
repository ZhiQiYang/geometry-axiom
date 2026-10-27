# GEO-337 native space audit — 2026-10-27

Read-only source/evidence audit; no native acceptance run performed.

## Identity and scope

- Managed environment: `ccarenv_b64_Y2NhcmVudl85OTczZTJlODY3ZDg4MTkxOTE0ZjhhNWU4NTBiZjg2NA`.
- Checkout: `/workspace/geometry-axiom`, branch `work`, HEAD `405f8c5e1a637a16cbe47470faf5ae1fa02b8676`; working tree clean before and after inspection.
- Audited F: `cbf0fb621888596aa14ad5f2349b503e23b1b72d`, read with `git show`/`git grep`, without checkout changes.
- F9 evidence read at `e1efab34d970a052a8082fa62e478ad13a0625ae`; its launcher pins `4f8a794f4167c3562eb182045102e86e9e37cca9`, not F.
- Also fetched recovered-evidence branch tip `45dd4d662eac9297eda8473742c9943a1cb336cb`.
- Writes: fetched Git objects/FETCH_HEAD in this repo, downloaded two source files `/tmp/geo337-cbf-binaries.py` and `/tmp/geo337-cbf-workflow.yml`, and this audit directory. No branch push, issue message, source/test edit, deletion, native run, or replacement of `/tmp/geometry-tests`.

## Verified findings

1. F `tests/binaries.py:47` hardcodes Linux OUT_DIR to `/tmp/geometry-tests`; TMPDIR does not redirect it. `tests/run_all.py:43` puts logs under that OUT_DIR.
2. F workflow native command is `ulimit -s 16384` followed by `python3 tests/run_all.py --build`; timeout remains 35 minutes. Searches for `disk_usage`, `statvfs`, `134217728`, and `128 MiB` in F tests and workflows (excluding archived evidence) found no free-space gate.
3. `evidence/geo337-train-20261024/F9-native-start/root-launcher.py:13` asserts `/tmp` free bytes >= 134217728. This is launcher admission, not product/CI validation. Other train resource plans also carry the reserve, so it is not exclusive to that file. `current-F8-full123-start/root-accepted-resource-budget.json` explicitly says: `This is a resource estimate, not a test threshold.`
4. The broad claim that no other test scripts hardcode /tmp is false. Examples at F: `tests/k2a_lifecycle_mutate.py:3`, `tests/k2a_lifecycle_browser_mutate.py:3`, `tests/geo198/remove_fix.py:39`, `tests/geo246/ci_job.py:96`; `tests/integration/scenario_context_lifecycle.py:5` checks a resolved /tmp prefix. No references to the two lifecycle mutation scripts or scenario_context_lifecycle were found in run_all.py or test_*.py. These findings do not establish a native dependency on the real path of `/tmp/geometry-tests`.
5. Targeted searches found no native assertion requiring OUT_DIR's resolved path to equal `/tmp/geometry-tests`. This is static evidence, not proof that a symlink run passes.
6. Current environment differs from the old low-space container: measured available bytes were `/tmp` 17871798272, `/workspace` 30906425344, `/dev/shm` 17871880192 after fetch. `/tmp` is writable tmpfs; `/dev/shm` is read-only in the current execution sandbox despite its backing tmpfs rw superblock. No SHM ELF execution test was performed.
7. Before the coordination instruction arrived, the sole capability probe `unshare -m --propagation private true` returned exit 1, `unshare: unshare failed: Operation not permitted`. No mount was attempted, no namespace change succeeded, and no alternate route was attempted after rejection. This was an OS/sandbox error, not an automatic approval-review rejection.

## Execution recommendation for the owning task

Do not rerun native or touch shared output while another owner runs F/F-prime acceptance. In this environment, sufficient writable tmpfs already exists at /tmp; no bind or symlink is needed. Recheck capacity and ownership at launch time. Retain historical launcher and failure originals unchanged; a revised launcher should resolve output and TMPDIR paths, stat their actual devices, group resource estimates per device without double-counting shared free capacity, and preserve the 64 MiB publication reserve. Keep source SHA, tests, assertions, workflow and timeouts unchanged. Record pre/post device/free-byte data and five-second sampled allocated/apparent output size (label as sampled maximum, not an exact peak).

No full-delivery deficit has been recomputed: current free space alone does not prove a complete package and roundtrip fit. Historical run results are not F acceptance. No privileged action is needed for this audit or for preparing an owner-specific launcher; any future native run still needs coordination of the shared output owner.
