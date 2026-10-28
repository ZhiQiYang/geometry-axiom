R02 UI-1 把 main 已有的 PF-1～3＋PF-H 接到 App：既有物件面 →「屬性」→「面設定…」→「完成面與鋪排…」，走建立／編輯、原生預覽、確認／取消、正式保存及 fresh BrowserContext 重開。原投影入口合併，投影與完成面互不改寫，建立空間仍可達。前端只組定義與呈現原生結果。

**Draft／未達合併條件。UI15 未跑：#343 → #346 → #347 來源鏈未閉合。** 未擴充 PF-6／4／5，畫面明示能力限制，整體 `complete:false` 保留。未合併 main、未動 #352／#353／#354 分支。

依據：[採納 A](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6436162095)、[完整設計](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)、[D44 審查](https://github.com/ZhiQiYang/geometry-axiom/pull/355#issuecomment-6474493782)。未改公理層、正典閱讀器、決策佇列；三份指定文件依設計 §9.2–9.4，BACKLOG 記錄 GEO-219 的入口／屬性區／確認列減項。

## 唯一 current-state 矩陣

- 完整 PR／evidence head：`bf184092957ed3f99855e22df81f7915fa96dc28`。
- 固定產品與最新完整 canvas execution F2：`74d638686edc9861e9ed9d3409af4adf02350f8e`。
- 基底：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
- D44 五項反證 execution F1：`a66b2022aa9603b5b2a6fc7b201d6b68a0d54bc6`。F2 另加參數來源準備的 navigation／focus／create request 守門及真 UI 反例；舊收據保留實際來源，不冒稱 F2 重跑。
- [原始收據與進度](https://github.com/ZhiQiYang/geometry-axiom/tree/bf184092957ed3f99855e22df81f7915fa96dc28/evidence/r02-ui1-20261028)：各包有 archive 與逐檔 SHA256，命令、exit、完整 stdout／stderr、環境、來源、失敗原件均保留。舊 PROGRESS 區段只作歷史。

| 本片驗收 | 實際狀態與界線 |
|---|---|
| UI01 入口與減項 | 已實跑：真物件面→面設定，原投影共存、空間建立可達，單一確認列；未新增工作區、分頁或全域按鈕 |
| UI02 明選來源 | 已實跑：未放置 D3、明設 frame、固定面材版本、正方形選軸、typed 來源、PF-H 原生配發 ID、明選柱；樑／多障礙組合未跑 |
| UI03 精確值 | 已實跑：零 dimension 時明確提議新建8mm，既有參數卡另行預覽／確認／Undo，返回重新讀取真正 ParameterRef；可改選既有17/2，wire及DOM精確值、大面積、負索引交丁與原生非法值拒絕 |
| UI04 誠實結果 | 已實跑：PF05／23／24 原生每一子段 supported 決定紅藍，精確 range、左右實寬與X逐項對照；不足仍可確認保存。零片／1mm／內層error、既有host及角材前後中心線／長度／host／world pose／dependencies均有真UI斷言 |
| UI05 生命周期 | 已實跑：來源草稿取消零寫入、獨立一次history與Undo/Redo、取消PF保留已確認來源；來源read晚回覆不得退出新面。另有晚token、同requestId查復、歷史往返、切面／專案、同id重建及晚A／新B見證；任意並行故障組合未窮舉 |
| UI06 no-op／原子性 | 已實跑：同定義零POST／history／revision／dirty；同值不同來源保留身分；實質PF確認一次history與一次definition-changed |
| UI11 正式保存 | 已實跑：真下載.gcanvas，fresh BrowserContext正式開啟，dump逐byte、references及PF精確狀態逐欄相同，新建8mm欄位的真正ParameterRef保留；未知能力／缺來源／篡改零替換。共用同一原生服務，未冒稱另一原生程序或OS picker |
| UI12 操作 | 已實跑：390／720／1280px、可命中控制、焦點、Esc回入口、CDP composition Enter不確認；實體IME／觸控／輔具未跑 |
| UI13 撤線必紅 | F1三必要接線與兩D44修復各具名0／1／0，六份377／0／0正向＋五份指定紅；F2來源準備守門另具名0／1／0，前後各381／0／0、無timeout。D44前另六組反證原件保留，不移標 |
| UI14 能力 | 已實跑：僅本片supportedActions，PF6／4／5明示不可用、無空動作，全域complete:false與scope完整性分開 |
| UI15 同源整合 | **未跑／未達合併條件**：#343→#346→#347仍diverged；不借S324舊收據。其他owner之同檔／保存格式整合待後續合流 |

## 實際執行結果

環境：Linux、Node v24.19.0、Google Chrome156.0.8078.73（原沙箱）、Noto CJK、16MiB stack。CDP各run獨立profile／暫存，服務及runtime來源有核對；完整canvas獨占，原2100秒時限不變。完整參數見各receipt，不宣稱WSL已跑。

| Gate／實際命令 | execution SHA | 結果 |
|---|---|---|
| 完整 `node geometry-web/cdp_test.js`（`r02-browser-run-v2.py canvas`） | F2 | 前次環境中斷，無exit／CDP_RESULT，不計通過；獨立背景恢復輪於2026-10-28T18:16:13.492780Z啟動，原2100秒／strict golden，尚無終態 |
| `d44-owner-mutation.py --root /tmp/r02-d44-mutations --output /workspace/r02-ui1-evidence/d44-owner-mutation --timeout 2100 -- python3 /workspace/r02-ui1-evidence/tools/r02-browser-run-v2.py pf` | F2 | baseline381／0、撤回UI05_D44_PREPARATION_OWNER具名6／1、restored381／0；0／1／0，421.561秒，外層exit0，raw hash與恢復來源已核對 |
| `d44-ui-mutations.py --root /tmp/r02-d44-mutations --output /workspace/r02-ui1-evidence/d44-ui-mutations --timeout 2100 -- python3 /workspace/r02-ui1-evidence/tools/r02-browser-run-v2.py pf` | F1 | 五組具名0／1／0，11次CDP，1293.054秒，外層exit0、無timeout，產品bytes恢復 |
| `GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js` | `a7a05ecf13076f0dcf5fd89d1ef6c8a9118ac836` | 381／0／0，203.807秒，exit0；其後F2僅test digest與本段golden計數 |
| `python3 tests/run_all.py --only node:tests-js --only node:panel_fill_ui_contract --only node:parameter_confirmation_settlement`（process-local reaper包覆） | F1 | 785／0／0，133.148秒，exit0，partial |
| `node tests/test_parameter_confirmation_settlement.js` | F2 | 16／0／0，exit0 |
| `MUTATE_CACHE=/tmp/r02-ledger-final-cache python3 tests/mutate.py --check` | F2 | exit0：70killed／1crashed／4equivalent／3retired，0stale／blocked／survived；M20仍是原三次SIGSEGV，不稱assertion-killed |
| `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | F2 | exit0，604檔／798edges／0diagnostics |
| `python3 -B tests/test_architecture_contract.py`；`python3 -B tests/test_product_architecture.py` | F2 | 205與18tests，各exit0；Linux manifest／scan／receipt及本片report已更新 |
| 完整native `python3 tests/run_all.py --build --update-expected` | `ffa22ad9245021c17c0a827847270bc5882cbb69` | **原exit1**：226suites，5221pass／4fail／1原允許GDI skip，1942.533秒；原件保留 |
| 原三個失敗suite修後 `run_all.py --build --only py:test_assembly_mutation_check --only py:test_mutation_anchors --only node:tests-js`（原process-local reaper包覆） | `79049d7e0c4a60f7a5e2ff4c7023cd713f0c387f` | 763／0／0，128.444秒，strict expected啟用；**不是第二次完整native通過** |
| `GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` | `ffa22ad9245021c17c0a827847270bc5882cbb69` | 356／0／0，exit0，441.562秒，partial |
| `node geometry-web/space_model_test.js` | 同上 | 242／0，exit0，183.846秒，full-space scope，不含timber兩組 |

原生PF四套92、新wire9、Node契約／保存38與全帳本78重產原件均已交付，執行來源見各包；本輪純H與JS測試修補以check證明帳本未過期。完整native原紅分為容器孤兒zombie、archive兩錨點漂移、舊未知格式測試拒絕已採/19；環境回收器只reap自身子程序，六原archive反證及格式撤回證據保留，未減斷言／時限。原golden85段不改，只增加本片實跑P128=381。

新增來源準備競態原紅：`0f37836d…` 的 UI05_D44_PREPARATION_OWNER，6／1、exit1；late read使focus=null、active=paramName。另D44新保存斷言初輪368／1是誤讀legacy view；修為版本化uiContract精確欄位，期望8/1與原保存斷言不變。兩份失敗均保留。

依使用者訊息，CI受帳號計費阻擋；已觀測舊run40714662993七jobs為runner_id=0、steps=[]，沒有產品執行證據。最新F2的CI實跑與本機Claude WSL結果未取得，不能將未派runner的failure當產品紅綠。

F2 完整 canvas 前次執行於17:47:27啟動、18:10:23最後輸出停P77，執行session消失且無exit／CDP_RESULT，gzip未封尾；分類環境中斷、原因未確證，不推定timeout或通過。round10逐byte保留原件。後續改以獨立背景程序承接同一裁判、固定F2、原2100秒與strict golden；後輪終態分列上表，不覆寫前輪。

後續啟用條件依設計§5.0／UI15：先閉合#343→#346→#347，在新的最終來源跑PF-1／PF-2／PF-H／PF-3、完整native與受影響browser；保留零片與raw seams、第二相位有板、負索引／轉置、原容量拒絕及成本反證。來源合流若改產品／測試，重新核帳本與架構；本片舊收據只保留其實際execution，不借S324或本次F2替代整合驗收。WSL須照原workflow保留canvas wait trace與原時限，本輪Linux trace-disabled收據不冒稱WSL收據。
