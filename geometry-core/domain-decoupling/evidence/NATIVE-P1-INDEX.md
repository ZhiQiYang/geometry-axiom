# GEO-261 P1 targeted execution evidence

These packages preserve completed targeted execution records, including failed runs and separately authorized diagnostics. They do not establish full GEO-261/P1 acceptance, complete fixture reopening, the full aggregate, or browser acceptance.

| Package | Completed receipts | Scope |
|---|---:|---|
| [Original sealed package](native-p1-20261016/README.md) | 24 | Original baseline and targeted native runs, their failures and later corrections. All 203 published files remain unchanged. |
| [Append-only follow-up](native-p1-followup-20261016/README.md) | 4 | Original 6f1 and 14ab test runs, the 6f1 `runs` failure diagnostic, and the 14ab two-case timing diagnostic. The default dump is an extraction attachment, not a fifth run. |
| [Authority-source follow-up](native-p1-authority-20261017/README.md) | 22 | Eleven build gates, nine executed focused batches and both f8c reload diagnostics through source `12422c69`. Two additional prepared focused bundles remain UNRUN. All 278 files in the preceding packages remain unchanged. |
| [Closed-batch follow-up](native-p1-closeouts-20261017/README.md) | 12 | Five build gates, five focused batches through source `fa5deb70`, and both de62/f22 diagnostics. It also preserves the watchdog selftest failure and correction and the fa5 stderr reconstruction as separate evidence. All 393 files in the preceding packages remain unchanged; the still-live `599f3414` preparation and execution are excluded. |

The follow-up's two original test runs remain failed:

- `6f1fd92f6886d6512c355baba4435e297b4e9664`: discovered 101 methods; executed 83, with 81 passes and two assertion failures. Two additional setup compilation errors prevented 18 methods from running.
- `14ab395d56ce1dcabe43e65b5311776a8d3e6221`: executed 101 methods; 98 passes, one assertion failure, and two original timeouts at 20 and 30 seconds.

The separate timing diagnostic rebuilt binaries identical to those in the original 14ab record. Rollback completed in 18.850039 seconds and imports in 43.040446 seconds, each with exit 0 under a 120-second observation watchdog. This does not change the original time limits or failed acceptance result.

The prepared PF-3 continuation (50 original methods and its original 19-mutation driver) and the original 27-method section-profile suite were not executed for these candidate freezes. Each package's README describes exact source commitments, source manifests, original logs, verification commands, and its checksum manifest. A package-verifier success certifies retained evidence consistency, not product correctness.

The authority-source pack preserves 536 original files as 435 exact content blobs, plus the hashes and sizes of 22 omitted source archives. It retains the initial invalid `load` diagnostic as well as the corrected `loadfile` attempt that reached the actual owned-record failure. The nine focused runs retain their original failed outcomes and remaining UNRUN methods. Later `15187`, `18ed` and `de62` work is outside this immutable pack; passing methods from different source SHAs are never combined into a same-SHA acceptance claim.

The closed-batch pack preserves 370 original files as 295 exact content blobs, with the hashes and sizes of ten omitted source archives. Its five focused outcomes remain `15187`: 0 PASS / 4 FAIL / 57 UNRUN; `18ed`: 61 PASS; `de62`: 37 PASS / 4 FAIL / 189 UNRUN; `f22`: 52 PASS / 2 FAIL / 166 UNRUN; and `fa5`: 17 PASS / 2 FAIL / 257 UNRUN. The diagnostic wrappers' successful capture exits are not product-test passes. The README and machine-readable limitations retain missing original logs and launch-time provenance gaps; later analysis does not repair those historical gaps.
