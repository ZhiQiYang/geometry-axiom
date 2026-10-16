# GEO-261 P1 targeted execution evidence

These packages preserve completed targeted execution records, including failed runs and separately authorized diagnostics. They do not establish full GEO-261/P1 acceptance, complete fixture reopening, the full aggregate, or browser acceptance.

| Package | Completed receipts | Scope |
|---|---:|---|
| [Original sealed package](native-p1-20261016/README.md) | 24 | Original baseline and targeted native runs, their failures and later corrections. All 203 published files remain unchanged. |
| [Append-only follow-up](native-p1-followup-20261016/README.md) | 4 | Original 6f1 and 14ab test runs, the 6f1 `runs` failure diagnostic, and the 14ab two-case timing diagnostic. The default dump is an extraction attachment, not a fifth run. |

The follow-up's two original test runs remain failed:

- `6f1fd92f6886d6512c355baba4435e297b4e9664`: discovered 101 methods; executed 83, with 81 passes and two assertion failures. Two additional setup compilation errors prevented 18 methods from running.
- `14ab395d56ce1dcabe43e65b5311776a8d3e6221`: executed 101 methods; 98 passes, one assertion failure, and two original timeouts at 20 and 30 seconds.

The separate timing diagnostic rebuilt binaries identical to those in the original 14ab record. Rollback completed in 18.850039 seconds and imports in 43.040446 seconds, each with exit 0 under a 120-second observation watchdog. This does not change the original time limits or failed acceptance result.

The prepared PF-3 continuation (50 original methods and its original 19-mutation driver) and the original 27-method section-profile suite were not executed for these candidate freezes. Each package's README describes exact source commitments, source manifests, original logs, verification commands, and its checksum manifest. A package-verifier success certifies retained evidence consistency, not product correctness.
