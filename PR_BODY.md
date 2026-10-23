柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。這是 #324 的 Codex 替代線；原 M 架構三條與帳本 check、Linux 四檔仍保實際身份；本次補最新339審查、獨立CI原因與最終F復驗準備，未新增產品實跑。

**11 個正式整合列目前為 3 PASS／1 RED／7 UNRUN。** 帳本仍紅，完整 native／expected 與六 browser 尚未跑，不宣稱可合併。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 目前公開來源 F | `38da31bcac91db631e6325e40b228f8604810e82` |
| 本輪四個原檢查 execution M | `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599` |
| 原142 importer／三 predicate execution S | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| 本輪 evidence E | `e9ee6d088b0cad4e3984aa2842a50acc311c2351` |
| 前一公開 evidence E | `47fd6a79090be021e853ba5016cbf6f14016b9aa` |
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
| affected-importers | 歷史指定9/9 module、142/142；本F重跑仍UNRUN，非完整 native | 九個原 runner 各 `0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-list | 歷史原正常斷言撤回／恢復；本F仍UNRUN | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-dict | 歷史原正常斷言撤回／恢復；本F仍UNRUN | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-feature | 歷史原正常斷言撤回／恢復；本F仍UNRUN | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
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

原 `--check` 紅是 freshness／未跑紀錄，含 C/include closure、oracle 與舊 bridge execution tool/head 不符；blocked／crashed均0，不是缺件、import失敗或編譯假紅。本輪沒有重產／編輯帳本，也不把 root 的 b6／最終L7af帳本拿來填綠。root L7af尚未含本線 faces 修正，其 host_sources仍39；即使原 workflow／六 judge bytes同，也不能沿用其結果為 #339 同源通過。

Linux 四檔沿既有 `geometry-product-architecture-receipt/1`。相對原ec8收據，604 path set 相同，只有 owned W `geometry-templates/woodworking/geometry_woodworking/model_sources.py` 的 LF hash改變；其餘603及三judge原 bytes同。新 receipt 的 sourceBaseHead 是真M，closure重新計算；manifest根範圍／layer／exclusion／reason／route／W guard／928與55政策原字不變。scan stdout逐 bytes相同並不等於完整LF closure未變。另在同M真跑既有 manifest digest 控制0/1/0，唯一正常紅為 `run_axiom_mutations.py` 的 EXCLUSION_DIGEST；只用外部原manifest，不改source或tests。P17舊反證保歷史身份。

受驗工作樹先由純evidence E回到真detached M；215份E公開副本、6,632,969 bytes以同filesystem逐檔rename保原inode/hash，不刪原件。原完整604 executable Git inventory與實體inventory均核，避免sparse隱藏輸入；另補原帳本真正oracle所需的tests/*.py／*.c、fixtures scene與root scene，合1119個必要原Git inputs，初末raw／LF／HEAD/tree／clean全同。沒有新clone，不碰root live ROOT／SEED／cache，不編譯或開Chrome。Chrome／Node／Python版本輸出也隨原環境保存。

本輪新原件見 `evidence/geo339-final-1f0ebd3e/`，包含四原command、完整stdout/stderr／環境／SHA／原exit、完整四產物、Linux adapter、已實跑manifest反證、1119-input身份清單及原缺件／準備失敗歷史。`raw/original-light-checks-and-architecture-M1f0ebd3e.tar.gz` 逐member對原件核，不把outer0當裁判0。215份已公開E副本不重包，保全manifest／rename events完整列冊；其原Git E仍可解析。

既有證據仍保 `evidence/geo324-final-57b68014/`：host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16、host_native30、default_native13，共指定九module142。三predicate各真0/1/0；它們的mock native transport不當成真browser。原公開pipes／wrapper事前pin限制、環境缺fixture重試、publisher／peer自身schema誤讀與manifest時點澄清等歷史皆保，不回寫舊報告。M的registry-list0不代expected。

最新已讀審查為fresh handoff `bfa19d004c1461e6740c192697a6c54896a98791` 的 `handoff/pr-reviews/339.md`，2026-10-23 22:39:42 UTC／head47fd。B1仍是帳本與七正式列未完；B3要求最終F（或新固定等價head）重跑142 importer、三predicate正常0/1/0及aggregate。本F工具已按原493路徑真Git metadata綁定、同原判官／斷言／時限，全部只是準備／UNRUN，沒有用歷史S結果抵免新要求。

B2 Actions [40032957675](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40032957675) 的七required job仍failure。已獨立取得七份check-run annotations，各明載「recent account payments have failed **or** your spending limit needs to be increased」；runner_id0、steps空。13原Git／gh命令均0並完整封存，不沿#338猜測，不把notice的Ubuntu遷移當失敗原因，也不能區分付款與上限兩者。此輪只讀分類，沒有修帳戶／重跑CI；B2未解除，產品未跑不算pass或skip。

C1：本#339為唯一owner替代線，舊#324凍結；root統一handoff重導向，這裡不推Grok或操作關PR。C2：base#340仍未合draft，待root排普通merge新穩定base收斂，無rebase或forcepush。所有新的原件與原F工具binding在 `evidence/geo339-review-followup-F38da/`，未修改公理／決策，未合併PR。

接續順序是本線固定來源的帳本全量更新與檢查、完整native／expected、六原browser；沿原35分鐘native及各browser CI時限／golden，canvas與性能獨占。架構三綠不涵蓋全部tests語意，不解決仍紅的帳本或七個UNRUN正式項。
