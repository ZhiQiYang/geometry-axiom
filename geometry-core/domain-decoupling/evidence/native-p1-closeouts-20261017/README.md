# Native P1 closed receipts through fa5deb70

This append-only package preserves historical evidence. **It is not a current-product acceptance certificate.** All original failures and UNRUN methods remain failures and UNRUN. The 599 preparation and every later 599 execution artifact are excluded; that source needs a separate package after closure.

The exact selection is the 370 closed files from external preparation catalog SHA-256 `f3f798090b191811eb2386226cbf7d6c1234df255e89ee865732f382191c4455`. Its separate preparation-only section was not copied. No original receipt, predecessor package, product source, or Git history was changed by packaging. Only pure-Python archive/hash validation and read-only Git inspection ran; no C compilation, product tests, browser/Node execution, or WSL launch ran.

## Historical outcomes

| Source prefix | Common build gate | Planned methods | Actually run | Passed | Failed methods | UNRUN | Failure events |
|---|---|---:|---:|---:|---:|---:|---:|
| `15187e71` | 5 stages PASS | 61 | 4 | 0 | 4 | 57 | 4 |
| `18edda3f` | 5 stages PASS | 61 | 61 | 61 | 0 | 0 | 0 |
| `de62cd68` | 5 stages PASS | 230 | 41 | 37 | 4 | 189 | 6 |
| `f22dcccc` | 5 stages PASS | 220 | 54 | 52 | 2 | 166 | 2 |
| `fa5deb70` | 5 stages PASS | 276 | 19 | 17 | 2 | 257 | 2 |

Build gates prove only their recorded compile/link stages; they add zero product-test methods. The de62 failure-event count includes three subtest failures within one failed method. Counts from different source SHAs must not be added into a same-SHA acceptance claim. `original-259-cross-sha-coverage-18edda3f.json` remains a cross-SHA index over eight retained source receipts, with both same-SHA and current-product-all-259-pass inferences explicitly false.

Every source SHA and tree is in `CONTENT-MANIFEST.json`. The five raw Git commit objects are under `source-commits/`; their Git object SHA-1 and tree headers were checked. `SOURCE-PROVENANCE.json` binds 12 source-before/source-after receipt pairs to their exact selected-source manifests. Read-only `git ls-tree -r -l -z` comparisons matched complete Git object manifests and all ten selected manifest mode/blob/size entries. All ten omitted source tar archives were read as data: member size, SHA-256 and Git blob SHA-1 matched the retained selected manifests. No omitted source tar or compiled binary is included.

## Diagnostics and explicit gaps

- `diagnostic-de62-parameter-v1`: wrapper exit 0 means capture completed. Its graph, prefix and depth cases each exit 1. Depth output reaches only cached=0/count=64 before stopping. It is not acceptance or a mutation kill, and existing product object files were not recompiled.
- `diagnostic-f22-version-v1`: wrapper exit 0 means capture completed; the product case exits 1 at the original inventory assertion. The 54 existing object records, read-only diagnostic insertion, commands and raw outputs remain bound to their original source. Preview output alone does not show an applied candidate.
- `fa5-version-output-analysis-v1`: the two 431-byte and 407-byte stderr files were reconstructed exactly from existing captured Python string literals. This is analysis of old receipts, not a new run. Successful baseline output and negative-case stdout were not retained and cannot be reconstructed from these receipts. The original fa5 17 passed / 2 failed / 257 UNRUN stays RED.
- Watchdog synthetic selftests retain both rounds: 9 tests / 1 failure, then 9 tests / 0 failures. Recovered source bytes for the first round match SHA-256 `868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac`, the summary's end-of-run disk hash. This does **not** prove the bytes loaded at execution start. Neither round retained a per-method unittest log; the first failed method is unidentified, and parser/sentinel assertions have aggregate evidence only. A 60-minute configured envelope is not a 60-minute elapsed selftest; synthetic waits were short.
- The fa5 build-gate `launch.ps1` bytes are present, but the original gate's runner hash map did not include that file. Its historical launch anchor remains absent. Focused-run launcher and watchdog claims that were actually hashed remain checked.
- External `wsl_locked3.sh` references remain references to bytes in the first immutable package. They do not become new execution-time hash attestations.

These limitations are machine-readable in `CONTENT-MANIFEST.json.evidenceLimitations`. `RUNNER-PROVENANCE.json` checks every retained explicit before/after runner claim. `missingRunnerClaimCount: 0` means those recorded claims resolve; it does not mean execution provenance is complete.

## Layout and verification

370 logical files total 99,518,011 raw bytes. Exact content deduplication stores 295 SHA-256 blobs totaling 79,097,380 bytes in `raw-evidence.tar.xz`; raw byte order, CRLF and UTF-16 logs are preserved. `CONTENT-MANIFEST.json.files` maps each original logical path to `blobs/<sha256>`, byte count and original/source/target hashes. Selected `readable/` files are byte-identical convenience copies, never replacements for original evidence. `omitted` retains ten source archive hashes and sizes without their source-tree bytes.

The preceding packages are immutable: `native-p1-20261016`, `native-p1-followup-20261016`, and `native-p1-authority-20261017`. `PREDECESSORS.json` records all 393 package files including each seal. The new package has zero logical-path overlap. Five unique content hashes (34,120 bytes) already occur in the predecessors; retaining them under new receipt paths preserves each closed batch's provenance.

The four helper scripts use the existing portable evidence schema. They never execute any archived runner or product command. `prepare_publication.py` refuses to replace a prepared package; `finalize_publication.py` refuses to replace a seal. `extract_evidence.py` validates then reconstructs original logical paths into a new destination, with byte and path safety checks. A source checkout is not reconstructed.

```text
python verify_publication.py . --predecessors
python verify_publication.py . --originals D:/geometry-axiom-work/geo261-evidence/p1 --predecessors
python extract_evidence.py . --out D:/chosen/new/evidence-directory
```

The committed `VERIFICATION.json` records the unsealed byte comparison against all 370 originals before sealing. `PACKAGE-SHA256.json` seals every package file other than itself, including that report and these helpers. A final sealed verification also checks every package hash. Verification success means artifact consistency; complete native acceptance, current default adoption and current browser acceptance are not claimed.
