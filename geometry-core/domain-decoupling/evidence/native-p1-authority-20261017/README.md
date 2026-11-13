# GEO-261 historical authority-source evidence, through 12422c69

This append-only pack preserves 11 finalized closeouts: 11 build-gate receipts,
9 executed focused-test receipts, 2 separate f8c reload diagnostics, and the
prepared files for 2 focused batches that remained **UNRUN**. Every result stays
attached to its original source SHA. The preceding two evidence packs are
unchanged. Source `15187` is outside this pack's authorized cutoff.

| Source | Build gate | Focused result | Methods run | Passed | Failed methods | UNRUN |
|---|---|---|---:|---:|---:|---:|
| [72d6835c](readable/closeout-72d6835c.json) | FAIL | UNRUN | 0 | 0 | 0 | 259 |
| [a8831ca0](readable/closeout-a8831ca0.json) | PASS | FAIL | 111 | 107 | 4 | 148 |
| [808b8e69](readable/closeout-808b8e69.json) | PASS | FAIL | 37 | 36 | 1 | 121 |
| [042dac48](readable/closeout-042dac48.json) | PASS | FAIL | 12 | 9 | 3 | 117 |
| [f8c3e0f2](readable/closeout-f8c3e0f2.json) | PASS | FAIL | 4 | 1 | 3 | 117 |
| [5fe3bfd5](readable/closeout-5fe3bfd5.json) | PASS | FAIL | 23 | 21 | 2 | 87 |
| [4cb65713](readable/closeout-4cb65713.json) | PASS | FAIL | 16 | 15 | 1 | 105 |
| [3e774212](readable/closeout-3e774212.json) | PASS | FAIL | 4 | 1 | 3 | 117 |
| [344935de](readable/closeout-344935de.json) | FAIL | UNRUN | 0 | 0 | 0 | 121 |
| [4004a1cf](readable/closeout-4004a1cf.json) | PASS | FAIL | 31 | 30 | 1 | 61 |
| [12422c69](readable/closeout-12422c69.json) | PASS | FAIL | 15 | 11 | 4 | 57 |

The a883 run has **15 failure events**, including 12 subtest failures, across
4 failed methods. The method column does not replace that original event count.
All nine executed focused receipts have zero errors and zero skips. A PASS build
gate covers its five recorded compile/link stages; it does not imply test or
runtime acceptance. Earlier passes must not be combined into a same-SHA
259-method pass. No full P1, PF-3, full aggregate, compatibility, browser, or
current-product acceptance is claimed here.

Both f8c diagnostic attempts are retained. The [v1 capture](readable/diagnostic-f8c3e0f2-bridge-reload-v1/result/summary.json)
used the unknown `load` command and never entered `loadfile`; its process exit 0
is not a product pass. The [v2 capture](readable/diagnostic-f8c3e0f2-bridge-reload-v2/result/summary.json)
used `loadfile` once and captured `SCENE_INVALID`, `line 25: I42: invalid owned
record`, followed by an empty dump. It ran no focused methods and no compiler.
Its exit 0 describes capture completion while the product reload failed.

`CONTENT-MANIFEST.json` maps all **536 original files** (212,962,724 logical bytes)
to exact source paths, SHA-256 digests, lengths and target archive entries.
`raw-evidence.tar.xz` stores 435 distinct byte sequences in **2,028,420 bytes**.
The 91 readable copies are byte-identical to the archive and originals. Text
encoding, line endings, trailing bytes, empty captures and UTF-16 launcher logs
are preserved without normalization. Large Git-object and omitted-path manifests
remain compressed; the pack contains no compiled binaries or complete source
checkouts. The 22 omitted selected-source tar archives retain their exact
original hashes and sizes in the manifest.

`SOURCE-PROVENANCE.json` binds the 11 raw Git commit objects and every completed
receipt's selected source before/after manifests. These are selected source
closures, not whole-repository execution evidence. `RUNNER-PROVENANCE.json`
records 113 exact runner/recipe/selection hash claims. Binary and build-artifact
hashes remain in the original receipts; omitted binary bytes are not claimed as
independently verified. The previously published external lock wrapper is linked
by its existing catalog hash, without inventing a new execution-time attestation.

Verify the standalone pack with Python 3.11+:

```sh
python -B verify_publication.py .
```

To also compare all 536 files byte-for-byte with the original P1 directory and
check the 278 unchanged predecessor-package files:

```sh
python -B verify_publication.py . --originals /path/to/geo261-evidence/p1 --predecessors --report /path/outside/package/verification.json
```

Validation checks every archive member and readable copy, exact source/target
hash mapping, raw commit identity, selected source hashes, runner identities,
closeout receipt hashes, original focused method outcomes and both diagnostic
captures. `VERIFICATION.json` records the completed original-byte check before
sealing; `PACKAGE-SHA256.json` then freezes the exact package file set. The
default verifier also checks this final seal. Verification success establishes
evidence consistency and does not change any historical failure or UNRUN status.

Recover one original file, or omit `--path` to recover all retained files:

```sh
python -B extract_evidence.py . --path closeout-12422c69.json --out /path/to/recovered
```

The extractor refuses existing output files and extraction inside this package.
Original absolute paths and commands are historical records, not portable launch
instructions. The preparation, validation, extraction and sealing scripts execute
no retained runner, product test, C compiler or WSL command. `.gitattributes`
disables line-ending conversion for every packaged file.
