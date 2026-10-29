# GEO-261 actual-product dependency contract

`product-architecture.json` is the executable inventory for the current product.
Run it with the conservative scanner; a zero exit status requires every owned
source and every dependency to pass:

```powershell
python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python -B tests/test_architecture_contract.py
python -B tests/test_product_architecture.py
```

This replaces the earlier synthetic-fixture-only evidence for the dependency
gate. It does not replace algorithm ownership review, native no-template builds,
runtime import blocking, mutation receipts, browser acceptance, or SSOT checks.

## Complete inventory and responsibilities

The current inventory contains 607 executable files: 338 owned sources and 269
individually named exclusions. The five complete roots are `geometry-core`,
`geometry-app`, `geometry-templates`, `geometry-web`, and `geometry-guide`.
`current_geometry.c` is an additional standalone source. The real
`rule_cases.runtime` imports `tests.binaries`, so `tests/__init__.py` and
`tests/binaries.py` are also owned runtime sources despite their directory name.
New executable files anywhere under these roots fail until accounted for.

| Layer | Files | Actual responsibility |
|---|---:|---|
| K | 70 | Public neutral C stores/evaluators/source/transaction APIs, the Python geometry kernel, and explicit integer one-dimensional allocation conservation, including private implementation headers |
| W | 68 | Woodworking policy, material/recipe interpretation, construction, layout, support, cutting allocation/loss policies and presentation; rectangular-grid second-template witness |
| H | 194 | Native World/scene/command/transaction adapters and composition, Python application and compatibility facades, browser/server UI, guide authoring, and workspace tooling |
| vendor | 6 | Individually digest-locked browser PDF and ZIP dependencies, accessible only from H |

The 338 sources contain 190 C/header/include files, 75 Python files, 69 JavaScript
files, and 4 HTML files. The canonical self-contained axiom reader and its
generator are included. The separate work-manager is included as H tooling,
although its own instructions distinguish it from the Geometry product UI.

Legacy `geometry-core/*.inc` paths are **not** automatically labeled K. Their
manifest purposes record concrete host duties such as scene parsing, candidate
scheduling, serialization, source/provider composition, and compatibility names.
Conversely, the neutral native implementation is owned by K even when H includes
it in a unity build. This classification is a reviewed responsibility claim;
dependency scanning alone cannot prove that every remaining H function is free
of misplaced domain policy. It must not be cited as that stronger result.

All exclusions have an exact path, individual reason, and SHA-256 using explicitly
declared CRLF-to-LF normalization. There are 120 historical evidence programs,
57 other documentation/reproduction/snapshot/GEO-262/framing-template tooling programs, 67 dedicated test drivers,
and 25 engineering-spec prototype files. The prototype's `AGENTS.md` explicitly
states it is not the production application. The manifest has no directory
exemption. An owned dependency on any excluded file fails. Historical evidence
and prototype programs have not been certified as active product dependencies.

The six vendor files have raw-byte digests and an explicit H-only trust bundle.
Their internal code, runtime loaders, WebAssembly and non-source assets are
**trusted, not statically verified**. K/W access to that bundle is rejected.
Only exact existing Windows/process C headers, the optional H-only
`playwright.sync_api` screenshot driver and the H-only Windows file-time stat
import `ctypes` receive external-module allowances.

## Audited host routes

The ordinary browser module routes explicitly map `templates/woodworking.js` to
the W frontend, `kernel/interval-allocation.js` to the K conservation checker,
`templates/woodworking-cutting.js` to the fixed W cutting provider, and
`application.js` to H composition. `runtime_version.py` owns these exact HTTP
asset mappings; the index loads K and both W providers before composition.
The work-manager's root
`/app.js` resolves to its own static app. The two literal PDF module imports map
to the pinned PDF vendor source. These mappings create normal graph edges.

The existing scenario iframe is the single `scenarioEditorFrame` element in
`geometry-web/index.html`. `scenario-workspace.js` binds it with
`frame:$('scenarioEditorFrame')`, assigns
`owner.frame.src='/?scenario='+context` once, and resets to `about:blank` at two
sites. The fixed prefix keeps all suffix text in the same-origin root URL's
query/fragment portion. The actual host first applies `urlsplit(self.path)`,
uses `route.path` for routing, parses the scenario query, and serves the existing
index document for `/`. No alternate HTML document is created.

The exact embed declaration names the HTML element, driver, receiver, query
value, root-query prefix, target document and occurrence counts. Both the driver
and HTTP router have LF-normalized digests requiring review when changed. The
scanner checks the finite assignment spelling, normalizes explicit iframe URLs,
and adds HTML-to-driver/target and driver-to-target edges. Only H endpoints can
declare this route. Unregistered iframe elements, `srcdoc`, external or other
unmapped URLs, extra static query keys, and other embedded-document/plugin tags
remain rejected. This is a digest-locked audited H route, **not** a general
JavaScript alias/dataflow or server-routing proof; arbitrary host runtime effects
remain outside the static graph.

## Findings and executable controls

The first whole-product run reported 28 diagnostics. Exact module/routes and
ordered Python package search roots resolved manifest mistakes. Actual source
changes expanded the neutral document getter token-paste macro and made two
sets of include paths unambiguous. No existing token-paste, include-ambiguity,
dynamic-import, embedded-document, or layer guard was removed. The final scan
is stored in `product-architecture-scan.json`; its source/manifest/scanner
fingerprints belong in the accompanying receipt, not an implied future version.

The earlier enclosure/definition integration refresh ran its previous manifest against the merged
product and correctly failed with `SOURCE_UNREGISTERED` for the new H enclosure
adapter. Independent inventory found exactly five new files and no stale
exclusion, vendor, driver or router digests. The refresh adds the H enclosure
adapter, the K enclosure source header/implementation, and the W authored
definition source header/implementation. Each has an explicit responsibility;
new W identities and canonical schema strings are forbidden in K. No source was
reclassified to hide a dependency. Scanning these entries also exposed an
ambiguous W `document.h` include; the source owner changed it to
`../native/document.h` and merged that fix normally. The refreshed verification
used integration source HEAD `47160841738e38c24ef4ee05c291467c760d1e99`.

The preceding region-key ledger integration refresh first ran that manifest against
source HEAD `1ee2a890d7a734f381eac8c716910939818315db` and correctly failed with
`SOURCE_UNREGISTERED` for `geometry-core/kernel/region_key_sources.c`.
Independent inventory found exactly two new K files, its implementation and
public header, and no stale exclusion, vendor, driver or router digests. They
own neutral vertex-key ledger serialization and consume typed K region geometry
for coordinates in the same candidate. The refresh adds their individual
responsibilities without changing any previous classification, scanner guard,
test or product source. The final scan and 18-test run require this HEAD and
every source input hash to remain unchanged throughout verification.

The preceding linear-definition/version-source refresh first ran the previous
manifest through the actual CLI against source HEAD
`d371420ec1922adb3df382a6cc2799b39bef7370`. It exited 1 with
`SOURCE_UNREGISTERED` for `geometry-core/kernel/linear_definition_sources.c`.
Independent enumeration found exactly four new K files: the public headers and
implementations for `linear_definition_sources` and `version_sources`. No
exclusion, vendor, driver or router digest was stale. The linear-definition
provider serializes authored datum/guide definitions, preserving expression
mode, completeness, ordered signed terms and complete opaque source keys without
evaluating quantities. The version provider serializes immutable identity,
content, fingerprint, schema and typed fields; field quantities consume the
returned complete definition. Their individually reviewed K responsibilities do
not introduce a W/H dependency. This refresh changes only the manifest and its
derived scan, report and receipt, retaining every previous classification,
exclusion and scanner guard.

The preceding grid-codec and historical-evidence refresh froze source HEAD
`4a13551cc8aac3e116b53486fe44637c07374d49`. The previous manifest's actual CLI
run exited 1 with `SOURCE_UNREGISTERED` for the new sealed evidence pack's
`extract_evidence.py`. Independent enumeration found exactly two new W sources,
`grid_definition_codec.c` and `.h`, plus four historical Python publication
helpers. The codec owns woodworking grid authored/value wire formats for
systems, bindings, applications and rules; its W schemas and cache semantics
remain outside K. Each historical helper receives an individual exclusion,
purpose and LF-normalized hash, checked against its sealed package's raw-byte
digest. No directory exemption was added. The new closure also captures 29
changed previously sealed inputs; every existing exclusion, vendor and embedded
route digest remains current.

The same refresh inventories concrete W guards from the actual W-owned native
C/header/include files. It preserves all 751 prior forbidden identifiers and
10 prior forbidden strings, adding 162 `Wood*`/`WOOD_*`/`wood_*` executable
identifiers and 45 `wood`/`woodworking` namespaced string literals, for totals of
913 and 55. These include all eight public codec functions, its three schema/
capacity macros, `wood_grid_decode_system`, and
`woodworking.face-application-check/1`. Neutral `Geo*`/`GEO_*` and generic names
were not added. The receipt records the exact additions and their source-file
provenance. Separate static probes pass the actual K `geometry.c` text with one
added identifier or string at a time through the unchanged scanner: all 207 are
rejected with the expected guard, while a neutral identifier remains accepted.
These in-memory probes neither modify source/test files nor increase the
18-test product-suite count.

The preceding host-authority and train19-evidence refresh froze source HEAD
`47d3bb4bcccddeeb034dd5899a7aa15c9cab0768`. The previous manifest's actual CLI
run exits 1 with `EXCLUSION_DIGEST` for
`geometry-web/cdp_test.js`. Independent
enumeration finds exactly three new historical Python evidence drivers:
`geometry-web/docs/evidence/geo263-20261016/compile_probe.py`, that directory's
`verify.py`, and
`geometry-web/docs/evidence/geo263-p153-20261016/verify.py`. Each receives an
exact path, purpose and LF-normalized digest; the receipt also records its raw
digest and the matching blob at the frozen Git head. These scripts were read,
not executed. No directory or filename-pattern exclusion is introduced.

The updated H reference adapter composes placement definitions and returned
geometry, member facts, enclosure/obstacle facts and candidate version inventory
through the registered K/W providers. The model adapter obtains parameter
semantics and section-profile definitions through the same source graph. The
world-validation callbacks consume those composed facts while W retains its
policy role. These remain existing H sources; this audit does not prove all H
behavior or native acceptance. The W section-profile provider adds three
definition-copy accessors: `wood_sp_sources_profile_definition`,
`wood_sp_sources_member_definition` and `wood_sp_sources_run_definition`.
All 913 previous forbidden identifiers and 55 strings are preserved, and the
three accessors raise the identifier total to 916. A fresh lexical inventory of
all W-native sources finds no additional W-namespaced string guard. Three
separate in-memory K-source probes reject those identifiers, and a neutral
probe passes; they do not increase the 18-test suite count. No source is
reclassified and no scanner or product test changes in this audit.

This refresh captures 11 changed previously sealed executable inputs,
including the newly merged H/W accessors and train19 browser sources. Two
existing test-driver exclusions, `geometry-web/cdp_test.js` and
`geometry-web/grid_system_test.js`, require reviewed hash updates for train19's
double-click/hit checks and stagger-rename coverage. Their exact paths and
test-only responsibilities remain unchanged; the receipt records old/new LF
digests, raw digests and current Git blobs. All other exclusion, vendor and
embed-route digests remain current. The Python default
change in #289 was not part of that 47d3bb4 frozen source and was not certified by that historical audit.

The preceding GEO-261 integration refresh froze source HEAD
`8394ef601c3d2407f51191339fad261929c1769a`. The merge of main `4b975a3d` (train
#312, GEO-262) and the GEO-262 re-anchor had already registered every new
executable file in the manifest, so independent enumeration finds 591 files,
none unregistered, none missing and no stale exclusion, vendor, driver or router
digest. Compared with the previous sealed manifest those commits added one H
source, `geometry-core/card_reference.inc`, 14 individually named exclusions
(nine GEO-262 tooling files under `geometry-core/card-reference/` and five
retained native-P1 evidence helpers) and updated five pinned digests:

- `geometry-web/assembly_generation_test.js` (exclusion LF digest)
- `geometry-web/cdp_test.js` (exclusion LF digest)
- `geometry-web/feedback_resize_observer_test.js` (exclusion LF digest)
- `geometry-web/marquee_test.js` (exclusion LF digest)
- `geometry-web/serve.py` (pinned scenario-route router digest)

The reviewed reason for each is recorded in the receipt. The router change
touches only `recorded_api` receipt handling; the scenario iframe route the
digest protects is not in that diff, and the iframe controls still pass against
the new digest.

Running that manifest through the actual CLI nevertheless exits 1 with one
`DEPENDENCY_UNRESOLVED`: `geometry-app/geometry_app/source_closure.py:40`
imports `ctypes` (and `ctypes.wintypes`) under `os.name == "nt"` for the
stat-signature source-inventory memo introduced by `c8de5a40`. The product suite
failed its complete-graph test for the same reason. This audit resolves it with
an exact **H-only** external-module allowance for `ctypes`, not the all-layer
standard-library list, because `ctypes` can load native libraries and K/W must
not gain that capability. In-memory probes append `import ctypes` to an actual K
and an actual W Python source and both are rejected; the actual H file is
accepted. This is a policy decision recorded for review, not a change to any
product source.

A fresh lexical inventory of all 60 W-owned native C files finds two W
identifiers added by the GEO-262 card reference, `wood_grid_card_definitions`
and `wood_grid_card_error`, and no new string guard. All 916 previous forbidden
identifiers and 55 strings are retained (9 identifiers and 3 strings no longer
occur in current W sources and are kept anyway), for totals of 918 and 55. Two
in-memory K-source probes reject the new identifiers and a neutral probe passes;
the HEAD manifest accepted the same text, so the new guards are what reject it.

69 previously sealed executable inputs changed (45 H, 6 K, 14 W and 4 excluded
test drivers), and 15 executable files are new. The Python default source commit
`8f36f1a0dd7e1244c92aca926c0a80079451e7f0` that the previous report left outside
its frozen source is now an ancestor of this HEAD (`git merge-base
--is-ancestor` exit 0); its runtime behavior and native coverage still require
their independent execution receipts, which this audit does not certify. No
scanner, product test or product source changes in this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`277bfdd3`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The preceding post-merge GEO-261 integration (`96ade86b`) refresh froze source HEAD
`96ade86bdb5fbcdad581b36afdd180a96fca7999`. The previous sealed audit (receipt
commit `854660a7`) froze source head `8394ef60`; since then the integration
branch gained 111 commits (first-parent merges: `96ade86b` (geo261: merge #321
source graph index (9f21280d) into the integration line), `6300d887` (geo261:
merge integration 390a5f33 into rootcat), `ce708ef5` (geo261: merge integration
d3746972 into rootcat), `e1eafff0` (geo261: merge integration 3e600772 into
rootcat), `c3613a6e` (geo261: merge Codex root-catalog exact-set fix
(4e0def58)), `71b11b43` (geo261: merge main adbaebf9 (framing train #307, #315,
#317))). Independent enumeration finds 601 executable files, 10 of them
unregistered in the manifest, all of them new since the previous sealed audit.
Running the committed manifest through the actual CLI nevertheless exits 1 with
`SOURCE_UNREGISTERED` for
`geometry-core/framing-template/core-probe/gen_scenes.py`; the scanner stops at
the first omission in sorted order, so the complete list comes from the
independent enumeration:

- `geometry-core/framing-template/core-probe/gen_scenes.py` (exclusion: core-probe scene generator)
- `geometry-core/framing-template/core-probe/mutation_check.py` (exclusion: core-probe mutation harness)
- `geometry-core/framing-template/core-probe/parse_results.py` (exclusion: core-probe result parser)
- `geometry-core/framing-template/core-probe/scene_reader.py` (exclusion: core-probe independent scene reader)
- `geometry-core/framing-template/core-probe/test_gen_scenes.py` (exclusion: core-probe unit tests)
- `geometry-core/framing-template/oracle/framing_oracle.py` (exclusion: framing oracle (executable reference specification))
- `geometry-core/framing-template/oracle/make_golden.py` (exclusion: oracle golden generator)
- `geometry-core/framing-template/oracle/quote_check.py` (exclusion: oracle verbatim-quote checker)
- `geometry-core/framing-template/oracle/render.py` (exclusion: oracle HTML renderer)
- `geometry-core/framing-template/oracle/selftest.py` (exclusion: oracle self-test suite)

All 10 are registered as exclusions with an exact path, an individual reason
and, for exclusions, an LF-normalized SHA-256 (the receipt also records raw
digests and the matching Git blob at the frozen head). The classification is a
reviewed responsibility claim: each file is probe, test, reference-oracle or
verification tooling for the framing template, which is not yet implemented in
the product: none is a product entry point, and the only executable wiring found
is that `tests/run_all.py` (outside the inventoried roots) runs
`geometry-core/framing-template/oracle/selftest.py` as the
`oracle:framing-selftest` suite and `run_probe.sh` feeds the generated scenes to
the native core in WSL.
`geometry-core/framing-template/oracle/framing_oracle.py` is an executable
reference specification that implementations must match, not the W
implementation of the framing template; if that template is implemented later,
its sources are registered as W then. No owned source depends on them: the scan
rejects an owned dependency on any excluded file, and a text search of the 327
owned non-vendor sources finds no mention of the new paths or their directories.
The exclusions do not certify that these tools are free of product dependencies.

In-memory controls on the final manifest remove each new entry in turn and the
unchanged scanner fails with `SOURCE_UNREGISTERED` at exactly that path;
corrupting the digest of each new exclusion fails with `EXCLUSION_DIGEST` at
that path. They neither modify source or test files nor change the product-suite
test count.

The committed manifest had already been edited since the previous sealed audit
(`715b8e2f`). This audit verifies those edits against the bytes on disk instead
of assuming them:

- `geometry-web/cdp_floor.js` (exclusion LF digest)
- `geometry-web/cdp_test.js` (exclusion LF digest)
- `geometry-web/grid_inspector_rename_test.js` (exclusion LF digest)

The reviewed reason for each is recorded in the receipt.

A fresh lexical inventory of all 60 W-owned native C files finds no new W
identifier or string guard. All 918 previous forbidden identifiers and 55
strings are retained, for totals of 918 and 55.

8 previously sealed executable inputs changed (3 H, 1 K, 1 W and 3 excluded test
drivers), and 10 executable files are new. The scanner and both architecture
test files are byte-identical to the previously sealed ones; no product source
is changed by this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`854660a7`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The preceding post-merge GEO-261 integration (`76df2d81`) refresh froze source HEAD
`76df2d816abfee02d3bb9eb545d7fb5c12150801`. The previous sealed audit (receipt
commit `ec1238cd`) froze source head `96ade86b`; since then the integration
branch gained 6 commits (first-parent merges: `546e2eb2` (Merge remote-tracking
branch 'origin/architecture/geo261-integration-20261016' into
architecture/geo261-integration-20261016)). Independent enumeration finds 601
executable files, 0 of them unregistered in the manifest, all of them new since
the previous sealed audit. Running the committed manifest through the actual CLI
nevertheless exits 1 with `EXCLUSION_DIGEST` for `geometry-web/cdp_test.js`; the
scanner stops at the first omission in sorted order, so the complete list comes
from the independent enumeration:

This audit re-pinned the stale exclusion digest(s) `geometry-web/cdp_test.js`,
`geometry-web/grid_rule_lines_test.js` after review.

A fresh lexical inventory of all 60 W-owned native C files finds no new W
identifier or string guard. All 918 previous forbidden identifiers and 55
strings are retained, for totals of 918 and 55.

4 previously sealed executable inputs changed (2 H and 2 excluded test drivers),
and 0 executable files are new. The scanner and both architecture test files are
byte-identical to the previously sealed ones; no product source is changed by
this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`ec1238cd`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The preceding post-merge GEO-261 integration (`0369579e`) refresh froze source HEAD
`0369579ef93b9046130d756e072f59c394654b09`. The previous sealed audit (receipt
commit `3f00d03d`) froze source head `76df2d81`; since then the integration
branch gained 3 commits (first-parent merges: no first-parent merge).
Independent enumeration finds 601 executable files, 0 of them unregistered in
the manifest, all of them new since the previous sealed audit. Running the
committed manifest through the actual CLI nevertheless exits 1 with
`EXCLUSION_DIGEST` for `geometry-web/grid_inspector_rename_test.js`; the scanner
stops at the first omission in sorted order, so the complete list comes from the
independent enumeration:

This audit re-pinned the stale exclusion digest(s)
`geometry-web/grid_inspector_rename_test.js` after review.

A fresh lexical inventory of all 60 W-owned native C files finds no new W
identifier or string guard. All 918 previous forbidden identifiers and 55
strings are retained, for totals of 918 and 55.

1 previously sealed executable inputs changed (1 excluded test drivers), and 0
executable files are new. The scanner and both architecture test files are
byte-identical to the previously sealed ones; no product source is changed by
this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`3f00d03d`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The preceding post-merge GEO-261 integration (`01e63145`) refresh froze source HEAD
`01e631453bba840b3839d6cf13635c55eb0470b6`. The previous sealed audit (receipt
commit `82e0db0b`) froze source head `0369579e`; since then the integration
branch gained 3 commits (first-parent merges: no first-parent merge).
Independent enumeration finds 601 executable files, 0 of them unregistered in
the manifest, all of them new since the previous sealed audit. The committed
manifest already passes the actual CLI.

A fresh lexical inventory of all 60 W-owned native C files finds no new W
identifier or string guard. All 918 previous forbidden identifiers and 55
strings are retained, for totals of 918 and 55.

1 previously sealed executable inputs changed (1 W and 0 excluded test drivers),
and 0 executable files are new. The scanner and both architecture test files are
byte-identical to the previously sealed ones; no product source is changed by
this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`82e0db0b`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The post-merge GEO-261 integration (`0548c05c`) refresh freezes source HEAD
`0548c05cccbb7b35def6bbc3d6b285004be676e5`. The previous sealed audit (receipt
commit `ac39346e`) froze source head `01e63145`; since then the integration
branch gained 3 commits (first-parent merges: no first-parent merge).
Independent enumeration finds 601 executable files, 0 of them unregistered in
the manifest, all of them new since the previous sealed audit. The committed
manifest already passes the actual CLI.

A fresh lexical inventory of all 60 W-owned native C files finds no new W
identifier or string guard. All 918 previous forbidden identifiers and 55
strings are retained, for totals of 918 and 55.

0 previously sealed executable inputs changed (0 excluded test drivers), and 0
executable files are new. The scanner and both architecture test files are
byte-identical to the previously sealed ones; no product source is changed by
this audit.

The previous four audit outputs are preserved byte-for-byte in the external run
directory and the previous sealed outputs were re-read from Git commit
`ac39346e`. The new receipt links their raw/LF digests, the previous receipt
creation time and source head.

The manifest, scan, report and receipt are excluded from the product
input closure because they are derived audit artifacts. Manifest and scan are
hashed separately; the receipt never hashes itself. Audit-only commits therefore
do not create a self-referential fingerprint loop.

`test_product_architecture.py` contains 18 portable tests. Its shared setup first
validates the actual repository roots, so a new unlisted file cannot disappear
when the snapshot is built. A temporary input-tree control invokes that same
setup path with an unregistered executable and requires rejection before any
copy. It then copies the actual owned/excluded product files byte-for-byte and
runs the full graph once. Controls
then reparse modified real files while retaining edges only from unchanged
snapshot files. They require rejection for a concrete C identifier, direct and
transitive C template dependencies, a direct Python template import, a transitive
Python host import (including the package initializer), an unlisted source and a
changed exclusion. The iframe controls cover external/unmapped source URLs,
extra queries, `srcdoc`, unregistered element IDs, non-H routes, driver/router
digest changes, and an external assignment even after updating its digest.

The removal check creates a separate tree containing **all 69 actual K files**
and no `geometry-app` or `geometry-templates` directory, then scans that complete
K tree. This is static missing-template evidence only. It neither compiles C nor
executes Python product modules, and must not be reported as native/runtime
no-template validation. Native execution remains in the serialized P1 queue.

At the previously sealed source HEAD `0548c05cccbb7b35def6bbc3d6b285004be676e5`, the
actual CLI scan exits 0 with 333 owned sources, 796 dependency edges and no
diagnostics. All 18 actual product tests pass with no skips. Independent
enumeration matches all 601 input hashes, both raw and LF-normalized. The
generic scanner suite was executed at this HEAD: 205 tests, 204 passed, 0 failed
and 1 skipped (a skip is not a pass). HEAD and all product, scanner and test raw
and LF hashes remain fixed throughout this finite refresh.

When new provider files are integrated, the root inventory must first fail
closed, then receive individually reviewed source entries. Re-run the product
scan and product tests and regenerate the receipt; rerun the generic scanner
suite if its scanner or test sources changed. Old fingerprints do not certify
new files or changed sources.

## 雲端 Linux 有限重產：P73 來源修正後

本輪來源固定於 `08dede0bf7f9206b5df5fefb6a27180128518c35`，上一份收據產物提交為 `60425b629aee9f74f4e62ea88af9882bc8968881`。新 Linux 封裝器沿用原 scanner、generic tests 與 product tests，沒有使用或冒充舊 Windows driver。manifest 登記、所有政策與排除理由均未修改。

獨立檔案系統與 Git tree inventory 共 601 個 executable inputs；owned 333、excluded 268、edges 796、diagnostics 0。LF input closure 是 `7a7d301e6e4cf6c7b7557a65bdd2e93d7e433be4d5773f835b567a7cbf6e0429`。

相對上一份 sealed receipt 改變的既有輸入：`geometry-web/app.js`。四檔是衍生稽核產物，排除於來源 closure；receipt 不雜湊自身。

- `python -B tests/test_architecture_contract.py`：退出 0；205 tests，205 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。
- `python -B tests/test_product_architecture.py`：退出 0；18 tests，18 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。

以上只證明本輪有限靜態契約與其控制，不宣稱 native、mutation ledger、瀏覽器、P52、Q38、§7 或 P-189 已執行。既有歷史段落與其原來源／結果保留。

## 雲端 Linux 有限重產：W placement-contact 政策更新

本輪來源固定於 `aa02a65e9d3923cc14c13340f05ed16c8b7d4fce`，上一份收據產物提交為 `f2c8837aeba3c49eacbd77b5161f07c819204263`。新 Linux 封裝器沿用原 scanner、generic tests 與 product tests，沒有使用或冒充舊 Windows driver。來源登記、分類與排除理由保持原值；完整 W C 詞彙盤點保留全部舊 guard，僅新增本輪兩個 W identifier。新 manifest 在 repo 外完整驗證樹受測，原來源 checkout 不變。

本輪新增政策：`WoodMemberPlacementContact`、`wood_definition_sources_placement_contact`；forbiddenIdentifiers 918 → 920。原三條 preflight 結果另存，不用新結果覆寫。逐新增識別字的舊政策接受／新政策拒絕及 neutral 接受是額外靜態 probe，不增加兩個正式 suite 方法數；未執行舊 Windows supplemental。

獨立檔案系統與 Git tree inventory 共 601 個 executable inputs；owned 333、excluded 268、edges 796、diagnostics 0。LF input closure 是 `8ce86d3b98b664ca87ba1edd60d9f5506c61a6744357769f1d4c100aedb7d78f`。

相對上一份 sealed receipt 改變的既有輸入：`current_geometry.c`、`geometry-app/native/reference_sources.inc`、`geometry-core/kernel/placement_sources.c`、`geometry-core/kernel/placement_sources.h`、`geometry-core/kernel/source.c`、`geometry-templates/woodworking/native/contact_sources.c`、`geometry-templates/woodworking/native/definition_sources.c`、`geometry-templates/woodworking/native/definition_sources.h`。四檔是衍生稽核產物，排除於來源 closure；receipt 不雜湊自身。

- `python -B tests/test_architecture_contract.py`：退出 0；205 tests，205 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。
- `python -B tests/test_product_architecture.py`：退出 0；18 tests，18 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。

以上只證明本輪有限靜態契約與其控制，不宣稱 native、mutation ledger、瀏覽器、P52、Q38、§7 或 P-189 已執行。既有歷史段落與其原來源／結果保留。

## 雲端 Linux 有限重產：canonical HTML trace 同步後

本輪來源固定於 `8a80abc1402b0c4c394969025c93a6019b4bb91d`，上一份收據產物提交為 `a12d184ec1865ad078700cea2387ac69e82ab62a`。新 Linux 封裝器沿用原 scanner、generic tests 與 product tests，沒有使用或冒充舊 Windows driver。本次恰一個既有 H canonical HTML input 同步；manifest 登記、920個既有 guard、所有政策、排除理由及 route/vendor digests 均保持原 bytes，不把上一輪新增兩個 W guard 重算為本輪新生成。

獨立檔案系統與 Git tree inventory 共 601 個 executable inputs；owned 333、excluded 268、edges 796、diagnostics 0。LF input closure 是 `e9d9b00ba23d939206dc90ba0199defb4c7e543b4339f8a1beba6a9935266fd0`。

相對上一份 sealed receipt 改變的既有輸入：`geometry-guide/公理層-閱讀器.html`。四檔是衍生稽核產物，排除於來源 closure；receipt 不雜湊自身。

- `python -B tests/test_architecture_contract.py`：退出 0；205 tests，205 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。
- `python -B tests/test_product_architecture.py`：退出 0；18 tests，18 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。

以上只證明本輪有限靜態契約與其控制，不宣稱 native、mutation ledger、瀏覽器、P52、Q38、§7 或 P-189 已執行。既有歷史段落與其原來源／結果保留。

## 雲端 Linux 有限重產：P73 來源修正後

本輪來源固定於 `55b9fb6479485361d9e2283a95e4355f5fca76db`，上一份收據產物提交為 `c9e6b45492e6016a1b5c91934fa3c9a674435431`。新 Linux 封裝器沿用原 scanner、generic tests 與 product tests，沒有使用或冒充舊 Windows driver。manifest 登記、所有政策與排除理由均未修改。

獨立檔案系統與 Git tree inventory 共 601 個 executable inputs；owned 333、excluded 268、edges 796、diagnostics 0。LF input closure 是 `303ee650da50d92a0397a5556bdf5b94c3066c941f1e5f850a79ea83638493dd`。

相對上一份 sealed receipt 改變的既有輸入：`geometry-web/runtime_version.py`。四檔是衍生稽核產物，排除於來源 closure；receipt 不雜湊自身。

- `python -B tests/test_architecture_contract.py`：退出 0；205 tests，205 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。
- `python -B tests/test_product_architecture.py`：退出 0；18 tests，18 passed、0 failed、0 skipped；原始 stdout／stderr 與完整命令在本輪收據。

以上只證明本輪有限靜態契約與其控制，不宣稱 native、mutation ledger、瀏覽器、P52、Q38、§7 或 P-189 已執行。既有歷史段落與其原來源／結果保留。

## 雲端 Linux 有限重產：合入 main 的六個 oracle／probe exclusion digest

固定實際來源為 `f79aa057521929597a9af4b204b709110414ac03`，上份架構產物提交為 `8f76f2b7d6f669670e5834310bfc26495b4a4aa6`。原manifest的三裁判依原值記錄1／0／5；最後的5是setUpClass因digest拒絕且Ran 0 tests，不能算已跑產品18方法。只在repo外完整驗證樹更新下列六個既有exclusion的LF digest，原來源checkout與三裁判bytes保持不變。

`geometry-core/framing-template/core-probe/gen_scenes.py`、`geometry-core/framing-template/core-probe/test_gen_scenes.py`、`geometry-core/framing-template/oracle/framing_oracle.py`、`geometry-core/framing-template/oracle/make_golden.py`、`geometry-core/framing-template/oracle/render.py`、`geometry-core/framing-template/oracle/selftest.py`。所有source登記、root、layer、排除理由、router/vendor digest、W guard與其他政策都保持原值；未新增exclusion或目錄豁免。

獨立物理與Git tree inventory為601 executable、333 owned、268 excluded；原scanner記796 edges、0 diagnostics。LF input closure：`f2a91b9b3962b2302600a5d21313f5655cc94ad081770d2a208c05d6cb4337e4`。

- `python -B tests/test_architecture_contract.py`：原退出0，205 tests／205 passed／0 failed／0 skipped；完整原命令、cwd、stdout／stderr另存。
- `python -B tests/test_product_architecture.py`：原退出0，18 tests／18 passed／0 failed／0 skipped；完整原命令、cwd、stdout／stderr另存。

本輪只證靜態架構契約；不代表native、帳本、瀏覽器、P52、Q38、§7或P-189已重跑。舊Windows supplemental未執行；既有歷史來源與結果保持原角色。四檔為衍生產物，receipt不雜湊自身。

## 雲端 Linux 有限重產：P88 一個 test-driver exclusion digest

固定實際來源為 `4b588fb63c9cc8fe5ba7570618f353c0d00d3816`，上份架構產物提交為 `13d02c1db7022145a52ee063286a558e595eb212`。原manifest的三裁判依原值記錄1／0／5；最後的5是setUpClass因digest拒絕且Ran 0 tests，不能算已跑產品18方法。只在repo外完整驗證樹更新下列一個既有exclusion的LF digest，原來源checkout與三裁判bytes保持不變。

`geometry-web/grid_rule_lines_test.js`。所有source登記、root、layer、排除理由、router/vendor digest、W guard與其他政策都保持原值；未新增exclusion或目錄豁免。

獨立物理與Git tree inventory為601 executable、333 owned、268 excluded；原scanner記796 edges、0 diagnostics。LF input closure：`856c3b984182066af9feefca934a066dec4d1c127fee7f1a662fd9f3c154f853`。

- `python -B tests/test_architecture_contract.py`：原退出0，205 tests／205 passed／0 failed／0 skipped；完整原命令、cwd、stdout／stderr另存。
- `python -B tests/test_product_architecture.py`：原退出0，18 tests／18 passed／0 failed／0 skipped；完整原命令、cwd、stdout／stderr另存。

本輪只證靜態架構契約；不代表native、帳本、瀏覽器、P52、Q38、§7或P-189已重跑。舊Windows supplemental未執行；既有歷史來源與結果保持原角色。四檔為衍生產物，receipt不雜湊自身。

## 【dot】R354-01：裁切來源登記與完整靜態重驗

基底 `b5b33ed1e55d3187108af7cddbca71d2a256c5d2` 加本次 P/T 補丁；不是遠端新 head。來源按 Git blob SHA 驗證後材料化，衍生收據以完整 inputs 雜湊綁定實測來源。

- `cutting-settings.js` 登記為 H：裁切專案附件 schema、保存高水位與 canonical codec 宿主邊界；含現有設定驗證，不宣稱已抽出獨立 W 政策。
- `cutting-plan.js` 登記為 H：消費既有 H `timber-schedule.js` 的原生導出，編排求值與 CSV，不冒稱中立 K。
- `cutting-workspace.js` 登記為 H：DOM、專案附件與 session 宿主。
- `cutting_plan_test.js` 為具名 CDP 測試排除；與 `cdp_test.js` 均重算精確 LF digest。未縮 sourceRoots、未放寬來源及依賴斷言。

原 scanner 完整掃描通過；generic 架構測試 205/205，product 架構測試 18/18。原始命令、退出碼、輸出雜湊見本輪 receipt。此為有限靜態依賴證據，不代表 native、瀏覽器或完整產品驗收。前述歷史區段仍是各自歷史來源的記錄。

## 【dot】R357-01：裁切責任與固定模板邊界

本輪基底為 `cd4bc8803016943e6ec7bf98f0c90bc0312cfa06` 加工作樹差異，尚不是新的遠端 head。來源閉包及實際驗證命令由本輪 receipt 綁定；歷史 R354-01 區段只代表當時的來源與有限靜態結果。

- K `geometry-core/interval-allocation.js` 只驗明示的整數區間、具型別需求身分、消耗及末餘。需求身分完整正規化後恰出現一次；配置必須在可用區間內，正長度區間不能重疊，總和以 BigInt 精確相加等於輸入全長。K 不決定木工材料、角色、鋸縫、端修或留用門檻。
- W `geometry-templates/woodworking/cutting.js` 實際承接 D46–D50、I58/I59/I61、R47–R49 的材料/無序截面配對、設定數值與宣告限制、原材在用保護、餘料優先、FFD 排列、末刀、端修、剩料分類與耗損彙總。切序先轉成明示配置及消耗區間，共用守恆只呼叫 K。它不引用 H 設定、料單、專案儲存或畫面。
- H `cutting-plan.js` 保留原生快照及既有 `timber-schedule.js` 的需求轉接、公開結果包裝與 CSV；`cutting-settings.js` 保留附件 schema、key 高水位、歷史保存及 canonical fingerprint，領域政策固定委派 W。H 不再持有 FFD、材料配對或耗損分類實作。
- H `geometry-app/application.js` 無條件組裝 frozen `woodworking/1` 裁切 provider；缺少固定 W 就拒絕啟動，沒有選擇器、停用入口或任意插件註冊。公開呼叫、附件格式、requires 與 CSV 契約不因此分層新增版本。

原 920 個 forbidden identifier 與全部既有字串政策保持，另加入實際 W 的 `GeometryWoodworkingCutting`、`materialKey`、`stockIdentity`、`sectionKey`、`kerf`、`minRemnant`、`allowance` 七個具名識別字；不是以移除 guard 接受新 K。原 scanner 的未知計算式 property key、dynamic global 及依賴方向限制保持原樣。

`test_product_architecture.py` 新增四個實際來源負向方法：K 摻入木工政策識別字、K 讀取固定模板字串、K 引用 W，以及 W 引用 H 設定/料單/組裝。原無模板測試擴大到整個 `geometry-core`，實際涵蓋第一支 K JavaScript，並保持全部原斷言。這些靜態控制仍不代替裁切數值差分、mutation 或真瀏覽器驗收。

本輪實跑原 `architecture_contract.py`：退出 0，607 executable inputs、338 owned、269 exclusions、810 edges、0 diagnostics；原 generic suite 205/205，product suite 22/22（含新增四個邊界控制），均退出 0。完整命令、時間及 stdout/stderr SHA-256 列於 receipt；LF source closure 為 `695b1cdf7d1ed965587f5672e4dd81da4f9bc661ff3291c6bf7a435a53e1e566`。這三條命令未執行 native、K1 mutation、瀏覽器、完整 run_all 或實體裝置驗收。
