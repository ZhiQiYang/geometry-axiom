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

目前清單含 610 個可執行檔案：333 個登記來源與 277 個逐檔排除項目。 The five complete roots are `geometry-core`,
`geometry-app`, `geometry-templates`, `geometry-web`, and `geometry-guide`.
`current_geometry.c` is an additional standalone source. The real
`rule_cases.runtime` imports `tests.binaries`, so `tests/__init__.py` and
`tests/binaries.py` are also owned runtime sources despite their directory name.
New executable files anywhere under these roots fail until accounted for.

| Layer | Files | Actual responsibility |
|---|---:|---|
| K | 69 | Public neutral C stores/evaluators/source/transaction APIs and the Python geometry kernel, including their private implementation headers |
| W | 67 | Woodworking policy, material/recipe interpretation, construction, layout, support and presentation; rectangular-grid second-template witness |
| H | 191 | Native World/scene/command/transaction adapters and composition, Python application and compatibility facades, browser/server UI, guide authoring, and workspace tooling |
| vendor | 6 | Individually digest-locked browser PDF and ZIP dependencies, accessible only from H |

The 333 sources contain 190 C/header/include files, 75 Python files, 64 JavaScript
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
declared CRLF-to-LF normalization. 前次封存清單的分類為 120 個歷史證據程式、57 個其他文件／重現／快照／GEO-262／framing 工具、66 個專用測試驅動器及 25 個工程規格原型檔；後續明列新增的收尾工具見本報告末尾各次刷新紀錄。 The prototype's `AGENTS.md` explicitly
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
the W frontend and `application.js` to H composition. The work-manager's root
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

The post-merge GEO-261 integration (`96ade86b`) refresh freezes source HEAD
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

本次最新封存來源為 `7afacf656912edccc7eb84cb9590990bccae1166`。實際 CLI 掃描結束碼為 0，含 333 個登記來源、796 條依賴邊及 0 項診斷。
通用掃描器測試 205 項：通過 205、略過 0；產品架構測試 18 項：通過 18、略過 0。
獨立枚舉核對全部 610 個來源的 LF 雜湊與指定 Git commit；來源集合、來源／裁判 bytes 及 HEAD 在每條命令後和封存前均保持一致。

When new provider files are integrated, the root inventory must first fail
closed, then receive individually reviewed source entries. Re-run the product
scan and product tests and regenerate the receipt; rerun the generic scanner
suite if its scanner or test sources changed. Old fingerprints do not certify
new files or changed sources.

## 2026-10-21 Linux 有限刷新

來源 SHA：`4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c`。本次變更只有以下已審閱的既有排除項目雜湊，以及逐檔明列的收尾驗證工具；既有來源責任分類、來源根目錄、獨立來源名單及守門政策維持既有內容。

- 既有 digest 更新 `geometry-web/cdp_test.js`：已逐字核對 4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c 的差異：既有完整瀏覽器驗收驅動器只將 P52-5 的機會式固定等待改為共用 15000ms 截止時間的 references／交易就緒等待，要求查詢前後 busy 皆為 false，保留原幾何斷言及章節計數；逾時與 API 失敗列出最後狀態。此檔由驗收流程執行，非產品入口。
- 既有 digest 更新 `geometry-web/grid_inspector_rename_test.js`：已逐字核對 4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c 的差異：既有 P72B 網格檢查器重命名驗收模組新增短 helper，兩處導航復用 cdp_navigation 的新文件 marker、document complete 及應用 ready 等待，避免 reload 後誤把舊頁 ready 當成新頁完成；清理導航 marker 並保留既有 50 項斷言。此檔由 CDP 驅動器載入，非產品入口。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/p189_verify.py`：GEO-261 收尾的專用 P-189 三方載入效能驗證工具；按指定 Git 版本與場景產生器建置隔離 bridge，保存 dump 位元組等價、交錯時間、完整來源 SHA 與裁判自證收據。這是外部驗收與報告工具，不是幾何核心、木工模板或宿主執行期來源。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/p189_verify_build.py`：P-189 初始建置階段實際執行工具的完整原始來源封存，raw SHA-256 為 0ed8674c90dc670b37a63a91187f633d7cf11190bb9584a7081dd6a5358dbc7c；只供對照原建置收據與重現當時行為。這是歷史驗收工具版本，不是本次最新正式量測器，不由產品執行期依賴，也不將新版本驗收結果追認為此舊版實跑。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/p189_verify_equivalence.py`：P-189 dump 等價階段實際執行工具的完整原始來源封存，raw SHA-256 為 c10eea2b116f2595a0a5dcab2dbdbd76d09c5e41e5339102ab109bc1e32049d2；只供對照原等價收據與重現當時行為。這是歷史驗收工具版本，不是本次最新正式量測器，不由產品執行期依賴，也不把不同階段工具雜湊混稱同一版本。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/p52_probe.js`：GEO-261 收尾的專用 P52 診斷與突變驗證工具；從明示工作樹擷取原 CDP helpers 及 P52，記錄點擊、API、references 與版本雜湊，並可於記憶體注入／撤回等待修正及延遲控制。只由獨立驗收命令啟動，不由產品入口或服務載入，不改寫產品來源。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/p72_probe.js`：GEO-261 收尾的專用 P72B 導航診斷與突變驗證工具；擷取既有 CDP 啟動器並執行完整 50 項 P72B 驗收，只於記憶體安裝／撤回導航等待，透過暫停真正 reload 文件與 app.js 請求重現舊頁 ready 誤判及候選新文件等待。raw SHA-256 為 11f85b9f10e296ea4864d7a8d9a8e460a1fe9a2070b6ab5271756b1f13f230ae；只由隔離驗收命令啟動，不是產品或服務入口，不被產品來源依賴。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/q38_controls.py`：交接 commit 59796b1af9259eb23d30134c2ce5a56317a06091 的 Q38 十二項對照突變定義，保留原始 bytes 供證據重現；由隔離驗收根目錄載入 tests/section_profile_mutation_check.py 並沿用其 baseline 與裁判。其歷史註解並非產品承諾；本次明列登記為測試工具，不允許產品來源依賴。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py`：GEO-261 收尾的有限架構收據重產工具；獨立枚舉完整來源、核對指定 Git commit、保留舊四檔，僅更新明列既有 exclusion digest 或本工具目錄內明列的新 exclusion，實跑三條架構驗收與撤回／依賴負控制後產出新四檔。它是外部稽核工具，不是 K／W／H 產品來源，也不提供執行期能力。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/run_controls.py`：GEO-261 收尾的 Q38 十二項交接控制調度與核對工具；呼叫明示 controls 腳本及既有真正裁判，分別保留原始裁判結束碼與預期結果核對結束碼，核對 baseline、完整控制集合及工作樹還原。只服務驗收，不構成產品功能或執行入口。
- 新增逐檔工具排除 `geometry-core/domain-decoupling/closeout-tools/run_gates.py`：GEO-261 收尾的 Q38／§7 專用測試調度器；在明示隔離工作樹呼叫既有 section-profile 與 card-reference 裁判，設定暫存目錄及 stack，保存命令、結束碼、來源 SHA 與工作樹還原狀態。只由驗收命令啟動，不被產品執行期依賴。

舊 manifest 以 `EXCLUSION_DIGEST` 轉紅；新版掃描及兩套測試均實際重跑。既有 digest 更新逐項撤回時須以目標檔案的 `EXCLUSION_DIGEST`、結束碼 1 拒絕。新增工具逐項移除登記時須以 `SOURCE_UNREGISTERED`、結束碼 1 拒絕；逐項破壞新工具 digest 時須以 `EXCLUSION_DIGEST`、結束碼 1 拒絕；再以實際 H 來源文字於記憶體加入對每個新工具的靜態依賴，須以 `DEPENDENCY_EXCLUDED`、結束碼 1 拒絕。上述是架構清單的突變自證，不冒充產品修正的行為突變自證。

四份舊產物逐位元組保存在外部證據目錄的 `previous/`；新收據記錄舊產物雜湊、原來源 SHA、本次完整輸入閉包、命令、結束碼、略過項及原始日誌雜湊。此處只驗靜態依賴；未執行原生、瀏覽器、Q38、卡片參照或 P-189 驗收，不能由本收據推定那些關卡通過。

## 2026-10-21 Linux 有限刷新

來源 SHA：`7afacf656912edccc7eb84cb9590990bccae1166`。本次變更只有以下已審閱的既有排除項目雜湊，以及逐檔明列的收尾驗證工具；既有來源責任分類、來源根目錄、獨立來源名單及守門政策維持既有內容。

- 既有 digest 更新 `geometry-core/domain-decoupling/closeout-tools/p72_probe.js`：已逐字核對 7afacf656912edccc7eb84cb9590990bccae1166 與前次封存 c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3 的唯一來源差異；raw SHA-256 為 6884e80a843834630b777d2add24e1c07c12ccc33f075a18f02403256d0dfcbc。此版停用無效的 Document 暫停控制，改為明示測試驅動器延後發送真正 Page.reload，先讀取瀏覽器的舊頁真實條件值，再於 stale-first 控制送出 reload 並暫停真正 app.js 請求；hold-navigation 控制則保持未發送 reload，以驗候選就緒等待期限。app.js 放行計時在求值前設置，避免控制本身堵住清理。這是既有 P72B 導航診斷與突變驗證工具的控制排程修正，非產品入口；不改產品導航模組、原 50 項斷言、來源責任分類或守門政策。此理由只記錄工具靜態審閱，瀏覽器控制結果另由各自原始證據證明。

舊 manifest 以 `EXCLUSION_DIGEST` 轉紅；新版掃描及兩套測試均實際重跑。既有 digest 更新逐項撤回時須以目標檔案的 `EXCLUSION_DIGEST`、結束碼 1 拒絕。新增工具逐項移除登記時須以 `SOURCE_UNREGISTERED`、結束碼 1 拒絕；逐項破壞新工具 digest 時須以 `EXCLUSION_DIGEST`、結束碼 1 拒絕；再以實際 H 來源文字於記憶體加入對每個新工具的靜態依賴，須以 `DEPENDENCY_EXCLUDED`、結束碼 1 拒絕。上述是架構清單的突變自證，不冒充產品修正的行為突變自證。

四份舊產物逐位元組保存在外部證據目錄的 `previous/`；新收據記錄舊產物雜湊、原來源 SHA、本次完整輸入閉包、命令、結束碼、略過項及原始日誌雜湊。此處只驗靜態依賴；未執行原生、瀏覽器、Q38、卡片參照或 P-189 驗收，不能由本收據推定那些關卡通過。
