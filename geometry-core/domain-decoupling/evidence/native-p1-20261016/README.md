# GEO-261 P1 portable targeted evidence

This package preserves completed targeted runs, including their failures and later corrections. It does **not** claim full P1 acceptance, the full aggregate, complete fixture reopening, or browser acceptance. Start with `readable/RESULTS.md`; read an individual `summary.json`, original log and source manifest together when assessing that run.

`CONTENT-MANIFEST.json` maps every original relative evidence path to its SHA-256, byte count and content-addressed archive entry. `raw-evidence.tar.xz` contains the exact original bytes, deduplicated across receipts. `readable/` provides byte-identical copies of the overviews, runners, discovery records and principal summaries. No product binary, full checkout or repeated mutant source tree is included. Native artifacts are represented by their original build commands, fingerprint sidecars, compiler output and recorded hashes; a fresh rebuild remains necessary to execute them.

Verify the package with any Python 3.11+ installation (no product execution or dependency installation):

```sh
python verify_publication.py . --report ../verification-local.json
```

This checks the raw archive and each blob, every retained file and readable copy, all recorded runner identities, source commit object identities and original unittest terminal counts. A zero exit means the **evidence package** is internally verified; it does not turn a failed product run into a pass. Existing reports are never overwritten.

Verify recorded source manifests against a Git repository that has the named commits, without checking out a revision or compiling:

```sh
python verify_publication.py . --repo /path/to/geometry-axiom --all-git-sources --report ../verification-git-local.json
```

The source plan declares the one initial rename receipt's partial manifest and checkout CRLF variants. Old-region receipts use the named old product plus exactly four added judge files from the declared judge commit; an overlay may not replace an original product file. Every other source plan claims a complete archived or clean-checkout manifest. `source-commits/` preserves original raw Git commit objects; the verifier recomputes their Git object IDs. Obtaining those commits and their trees is a reviewer prerequisite for the optional Git comparison.

The verifier reads Git archives with per-command `core.autocrlf=false` and `core.eol=lf`, matching the original Linux archives. It does not change repository configuration. This is necessary on Windows because `git archive` otherwise follows the machine's checkout line-ending settings; original `-text` files retain their exact stored bytes.

Recover an original log or manifest by its path in `CONTENT-MANIFEST.json`:

```sh
python extract_evidence.py . --path native-closure-a3aeef41-v1/unittest.log --out recovered
python extract_evidence.py . --path native-closure-a3aeef41-v1/source-before.json --out recovered
```

Omit `--path` to recover all catalogued raw evidence. The extractor verifies the archive and each requested file and refuses to overwrite existing files. The retained launchers and runner files describe the exact executed commands and environment, including historical absolute paths; they are audit records, not a promise that the original local runtime is portable. `readable/runtime/wsl_locked3.sh` is the actual serialization wrapper, whose SHA-256 matches the baseline execution receipt.

The package deliberately preserves the unsuccessful producer v3, rename v1/v2, insufficient first region controls, parameter/annotation/datum compilation failures, original datum text assertion failure, the 99ee support control survivor and the a3 grid impact-preview assertion failure. Successful later receipts remain separate. Expected-red region receipts preserve raw unittest exit 1 even when their differential referee passes. Interrupted or superseded preparation has no passing result.

The compatibility producer's subdivision input is a recorded rejection; it is not relabeled as a supported package. The prepared whole-inventory reopening tools are not executed evidence here. The full final candidate's fixture and UI gates remain outstanding until separately authorized and completed.

All source and runner before/after comparisons are retained. `RUNNER-PROVENANCE.json` identifies exact matching runner bytes. `SOURCE-PROVENANCE.json` identifies exact source commitments and overlay rules. `.gitattributes` disables line-ending conversion in this package so a Git round trip preserves the recorded bytes.

`VERIFICATION.json` records the package author's actual verification. `PACKAGE-SHA256.json` covers the complete published file set, including that report and the verification tools; the verifier checks these additional file hashes and rejects any extra or missing file when the checksum manifest is present. Keep new local verification reports outside the package, as shown above. These are packaging checks and do not execute any new product test.
