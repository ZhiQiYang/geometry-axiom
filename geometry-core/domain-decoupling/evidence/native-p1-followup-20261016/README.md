# GEO-261 P1 follow-up evidence — four additional receipts

This appendix preserves **four completed execution receipts** after the original sealed 24-receipt package: two original native test runs and two separately authorized diagnostics. The extracted default dump is an attachment to the original failure, not another execution. The original package in `../native-p1-20261016/` remains byte-for-byte unchanged; `PREDECESSOR.json` pins all 203 of its files to published commit `3de118155ae4ee4233db473e67ea39caf1769396` in PR #286.

| Receipt | Frozen source | Original result |
|---|---|---|
| `native-candidate-6f1fd92f-v1` | `6f1fd92f6886d6512c355baba4435e297b4e9664` | Discovered 101; ran 83, with 81 passes and two assertion failures. Two additional `setUpClass` compilation errors prevented 18 methods from executing. Zero skips. |
| `section-runs-diagnostic-6f1fd92f-v1` | Same 6f1 source | Recompiled the unchanged original `runs` harness once; byte-identical binary, observed exit 1 and `ASSERT:run-negative-refused error=I35: literal dimension must be integer mm in D1 range`. Capture completion is not product acceptance. |
| `native-candidate-14ab395d-v1` | `14ab395d56ce1dcabe43e65b5311776a8d3e6221` | Ran all 101: 98 pass, one default-dump assertion failure, and two original process timeouts at 20/30 seconds. Zero skips. |
| `timeout-diagnostic-14ab395d-v1` | Same 14ab source | Recompiled the two unchanged original harnesses using their original NativeBuild flags. Both binaries match their original hashes. Each case ran once with a separate 120-second diagnostic watchdog: rollback exit 0 at 18.850039 seconds; imports exit 0 at 43.040446 seconds. Neither watchdog fired. |

The original 14ab acceptance result remains **98 passes, one failure, two timeouts**. Its entire 140-file receipt is unchanged before and after the timing diagnostic. The prepared PF-3 50-method run and original 19-mutation driver, and the original 27-method section-profile suite, did not execute. No full P1, whole-inventory fixture, full aggregate or browser acceptance is claimed.

The default dump in `readable/14ab-readonly-diagnostics/default-scene.actual-dump.txt` is the exact 524-byte, 13-line text extracted from the original failed assertion. Its provenance retains that assertion and the original result hash. It starts with canonical `boundary` and `placement` declarations; the original test instead looked for `surface`.

The timing measurements retain distinct raw clocks and do not normalize CPU values or derive a percentage:

| Case | Monotonic elapsed seconds | wait4 user seconds | wait4 system seconds | max RSS KiB |
|---|---:|---:|---:|---:|
| rollback | 18.850039136999953 | 18.691966999999998 | 0.066816 | 106048 |
| imports | 43.04044604899997 | 43.760246 | 0.11066 | 106048 |

These observations do not identify a specific internal hotspot or change the original time limits. The imports binary's retained `nm` output reports `g_world` as 4,215,368 bytes; that symbol size does not describe all allocations.

`CONTENT-MANIFEST.json` maps every original relative path to its exact SHA-256, byte count and content-addressed entry in `raw-evidence.tar.xz`. The archive deduplicates repeated source manifests and build inputs; it contains no product executables, object files or complete source checkouts. The files named `stdout.bin`/`stderr.bin` are original captured UTF-8 text, not executable binaries. `readable/` contains byte-identical summaries, original unittest logs, commands, runners, measurements and principal outputs. Original absolute paths in those audit records are preserved and are not portable execution instructions.

Verify with Python 3.11+ from this directory, keeping reports outside the sealed package:

```sh
python verify_publication.py . --report ../followup-local-verification.json
```

This verifies the archive, every raw/readable file, runner identities, exact result and log counts, build input hashes, diagnostic output and binary-hash chains, default-dump extraction, complete source before/after manifests, and all original predecessor files. The verifier requires the unchanged predecessor package beside this appendix. Verification exit 0 means the **evidence package** is consistent; it cannot turn a failed test into a pass. Binaries are represented by recorded hashes, not retained executable bytes.

To compare the 15,978-file source manifests against both exact Git commits without compiling or creating a checkout:

```sh
python verify_publication.py . --repo /path/to/geometry-axiom --all-git-sources --report ../followup-git-verification.json
```

Git archives use per-command `core.autocrlf=false` and `core.eol=lf`; repository configuration is unchanged. `source-commits/` retains the two raw Git commit objects, whose object IDs are recomputed by the verifier.

Recover any original retained file by its catalog path, without overwriting an existing file:

```sh
python extract_evidence.py . --path native-candidate-14ab395d-v1/source-before.json --out recovered
```

Omit `--path` to extract all retained evidence. The inherited extractor, checksum finalizer and base verifier follow the original package format; `verify_followup.py` adds checks for the four new receipts and predecessor preservation. `.gitattributes` disables line-ending conversion. `VERIFICATION.json` records the actual packaging checks, and `PACKAGE-SHA256.json` freezes the exact published file set. Packaging executes no product tests, C compiler or WSL command.
