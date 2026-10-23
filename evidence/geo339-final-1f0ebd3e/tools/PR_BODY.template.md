柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。這是 #324 的 Codex 替代線；本輪新增真 M 的架構三條與帳本 check 收據，並在 Linux 依原 schema 刷新四檔。

**11 個正式整合列目前為 3 PASS／1 RED／7 UNRUN。** 帳本仍紅，完整 native／expected 與六 browser 尚未跑，不宣稱可合併。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 目前公開來源 F | `<PRODUCT_F>` |
| 本輪四個原檢查 execution M | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| 原142 importer／三 predicate execution S | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| 本輪 evidence E | `<EVIDENCE_E>` |
| 前一公開 evidence E | `dcdf22655e0cf8ed47cd0b7f66d89f3a7beca694` |
| Grok 原 head／PR-local base | `4e176e830b691269cc72d021ce7e1bc0b167d621`／`7dae5f21c7ca401e660450d437e60ba566218da8` |
| 已普通 merge 的 #340 source | `4d3a17c306cad42057589c5cfd964f1c32b755c4` |
| head／正文分支 | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |
| PR base | `codex/kernel-without-woodworking-20261023`（#340） |

本輪 source F 只在前一 evidence E 之上更新兩個非執行性架構衍生檔：report／receipt；四檔都完整封存，但 manifest／scan 原 bytes 不變。功能改動仍是原兩個 Python leaf 與 expected host_sources39→45，保 noWood13 及上游其它 registry。M→F 的604架構 executable inputs／三個原 judge bytes相同；F 沒有重新執行本輪測試，不能把 execution M 改寫成 F 或 evidence E。

唯一 current-state 矩陣如下。前八列加最後三列是所述11個正式整合列；其餘為既有指定 importer／predicate／registry 結果，分列原 execution，不混進正式列的通過數。`null` 是未跑，沒有新增 skip。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
| native-and-full-expected | UNRUN；不以142局部方法代 aggregate | `null` | `null` |
| canvas | UNRUN | `null` | `null` |
| assembly | UNRUN | `null` | `null` |
| documents | UNRUN | `null` | `null` |
| grid | UNRUN | `null` | `null` |
| space | UNRUN | `null` | `null` |
| timber | UNRUN | `null` | `null` |
| mutation-check | **RED**：123定義／110紀錄；107 stale、3 retired、13 unrun | `1` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| registry-list | 原 discovery 清點，非 expected gate | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| affected-importers | 指定9/9 module、142/142，非完整 native | 九個原 runner 各 `0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-list | 原正常斷言撤回／恢復 | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-dict | 原正常斷言撤回／恢復 | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-feature | 原正常斷言撤回／恢復 | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| architecture-contract | PASS；604inputs／334owned／270excluded、798edges／0diagnostics | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| architecture-tests | PASS；205原方法、0 skip | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| product-architecture-tests | PASS；18原方法、0 skip | `0` | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |

本輪四個原 CLI 沒有 selector、expected 更新、skip 或斷言變更：

```text
python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python3 -B tests/test_architecture_contract.py
python3 -B tests/test_product_architecture.py
python3 -B tests/mutate.py --check
```

原 `--check` 紅是 freshness／未跑紀錄，含 C/include closure、oracle 與舊 bridge execution tool/head 不符；blocked／crashed均0，不是缺件、import失敗或編譯假紅。本輪沒有重產／編輯帳本，也不把 root 的 b6／未定 final L 帳本拿來填綠。root L 尚未含本線 faces 修正，其 host_sources仍39；即使原 workflow／六 judge bytes同，也不能沿用其結果為 #339 同源通過。

Linux 四檔沿既有 `geometry-product-architecture-receipt/1`。相對原ec8收據，604 path set 相同，只有 owned W `geometry-templates/woodworking/geometry_woodworking/model_sources.py` 的 LF hash改變；其餘603及三judge原 bytes同。新 receipt 的 sourceBaseHead 是真M，closure重新計算；manifest根範圍／layer／exclusion／reason／route／W guard／928與55政策原字不變。scan stdout逐 bytes相同並不等於完整LF closure未變。另在同M真跑既有 manifest digest 控制0/1/0，唯一正常紅為 `run_axiom_mutations.py` 的 EXCLUSION_DIGEST；只用外部原manifest，不改source或tests。P17舊反證保歷史身份。

受驗工作樹先由純evidence E回到真detached M；215份E公開副本、6,632,969 bytes以同filesystem逐檔rename保原inode/hash，不刪原件。原完整604 executable Git inventory與實體inventory均核，避免sparse隱藏輸入；另補原帳本真正oracle所需的tests/*.py／*.c、fixtures scene與root scene，合1119個必要原Git inputs，初末raw／LF／HEAD/tree／clean全同。沒有新clone，不碰root live ROOT／SEED／cache，不編譯或開Chrome。Chrome／Node／Python版本輸出也隨原環境保存。

本輪新原件見 `evidence/geo339-final-1f0ebd3e/`，包含四原command、完整stdout/stderr／環境／SHA／原exit、完整四產物、Linux adapter、已實跑manifest反證、1119-input身份清單及原缺件／準備失敗歷史。`raw/original-light-checks-and-architecture-M1f0ebd3e.tar.gz` 逐member對原件核，不把outer0當裁判0。215份已公開E副本不重包，保全manifest／rename events完整列冊；其原Git E仍可解析。

既有證據仍保 `evidence/geo324-final-57b68014/`：host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16、host_native30、default_native13，共指定九module142。三predicate各真0/1/0；它們的mock native transport不當成真browser。原公開pipes／wrapper事前pin限制、環境缺fixture重試、publisher／peer自身schema誤讀與manifest時點澄清等歷史皆保，不回寫舊報告。M的registry-list0不代expected。

審查依據為fresh handoff `e9a1b4abfe8df2bf99b7166db451fc3b7629f41f` 的 `handoff/pr-reviews/324.md` 最後【ChatGPT 審查】與轉交；同ref的339.md僅同步標頭，沒有新留言。未修改公理／決策、未force push、未合併PR。

接續順序是本線固定來源的帳本全量更新與檢查、完整native／expected、六原browser；沿原35分鐘native及各browser CI時限／golden，canvas與性能獨占。架構三綠不涵蓋全部tests語意，不解決仍紅的帳本或七個UNRUN正式項。
