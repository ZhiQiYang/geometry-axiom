R02 UI-1 將既有 PF-1～3＋PF-H 原生能力接到 App 的面內屬性檢查器。物件面 →「面設定…」→「完成面與鋪排…」可走建立／編輯、預覽、確認／取消及正式保存重開。原投影設定合併進同一入口，投影與完成面互不改寫，「依此平面建立空間」仍可達。前端只組定義及呈現原生結果，不新增幾何算法。

依據：[採納方向 A](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6436162095)、[完整設計與驗收](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)。

**Draft／未達合併條件。** 審查6474493782的兩項D44產品缺漏已修並有377項真UI回歸；新版五組撤回正在執行，完整canvas待後續獨占，尚不宣稱全綠。 #343 → #346 → #347 來源鏈尚未閉合，UI15 未跑；不宣稱 PF-6／PF-4／PF-5 或整體 R02 完成。全域 `complete:false` 保持不變。

## 唯一 current-state 矩陣

- 完整 PR head／本輪 evidence head：`c2d99c4289582d4fba44404a3651b0480d4e6e3f`。
- 基底：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
- 新固定產品／驗收來源 F：`a66b2022aa9603b5b2a6fc7b201d6b68a0d54bc6`。其後只更新本輪架構receipt與證據。
- D44前完整canvas execution source：`82257ab8b76e4eb36a9c26539125c83649485487`。其後已修改parameters／PF呈現及測試，舊full不移標為新F通過。
- 六組 UI 反證 execution source：`fdd94809e9e2bce05a7be5c1f6dbef6eae2bf92f`；本輪後續只修 archive mutation 工具錨點、過時的未知格式測試、census 與架構產物。該六組屬D44前來源；新F將另跑原三UI13及兩項D44修復反證，不移標舊execution SHA。
- [完整原件與進度](https://github.com/ZhiQiYang/geometry-axiom/tree/c2d99c4289582d4fba44404a3651b0480d4e6e3f/evidence/r02-ui1-20261028)：每包附逐檔 SHA256，保存命令、退出碼、完整輸出、環境、來源及原紅燈。舊狀態只保留在歷史 PROGRESS，不作目前結論。

| 案例 | 實際狀態與範圍 |
|---|---|
| UI01 入口／減項 | 已實跑：真物件面→面設定、投影共存、建立空間可達；原投影入口、重複屬性／確認列合併 |
| UI02 明選來源 | 已實跑：未放置 D3、完整明設 frame、固定材料版本、正方形選軸、typed 來源、明選柱；樑與多障礙組合未跑 |
| UI03 精確值 | D44新流程已實跑：零既有dimension仍提議8mm，既有參數卡獨立預覽／確認，返回原面帶真正ParameterRef；亦可明選既有來源。另已實跑：X=17/2 wire 與畫面、大面積9999999800000001、負索引交丁；厚度9.5、負gap、等於period的stagger由原生拒絕 |
| UI04 結果誠實 | D44修後已實跑原生supported逐子段紅／藍、精確座標及左右實寬；不足仍可確認保存。另已實跑：PF05/23/24左右實寬與分段、X重判、nonSeams、零片、1mm裁片、內層error；既有host與三支角材的舊／新中心線、長度、host、world pose及完整dependencies可見 |
| UI05 生命周期 | 新來源草稿取消零變更、獨立一筆history／Undo／Redo、取消PF保留來源已實跑；新來源返回之任意並行導航故障組合未全驗。另已實跑：取消、晚token、確認掉回覆後同requestId查復、切面／新專案與Undo、同dump歷史往返、同id刪除重建、晚A不覆蓋新B；未外推任意並行故障組合 |
| UI06 no-op／原子性 | 已實跑：同定義零POST／history／revision／dirty，同值不同來源保留差異；每次實質確認只一筆history及一次definition-changed |
| UI11 保存 | D44新建8mm欄位之ParameterRef與精確值已真保存重開；完整原流程已實跑：真下載.gcanvas→fresh BrowserContext正式開啟；dump逐byte與完整references/PF狀態逐欄相同，未知能力／缺來源／篡改零替換。共用同一原生服務，非另一原生程序／OS picker |
| UI12 可操作性 | 已實跑：390／720／1280px、確認按鈕可命中、焦點、Esc回入口、CDP composition Enter不確認；實體IME／觸控／輔具未跑 |
| UI13 真入口與撤線 | 新版377項基準已實跑，五組撤回尚待終態。D44前原件：349項真UI基準；面設定handler、preview HTTP、confirm回執三項必要撤線各具不同具名紅及0／1／0，另焦點／下游影響／場景同步三組亦0／1／0 |
| UI14 分片能力 | 已實跑：僅本片supportedActions、PF6／4／5明示限制且無空動作；全域complete:false，scope完整性獨立判斷 |
| UI15 同源整合 | **未跑／未達合併條件**：#343→#346→#347未閉合，不借S324舊收據。其他工作線的同檔／保存格式整合仍待各owner合流時處理 |

## 實際執行與 gate

雲端環境：Node v24.19.0、Google Chrome156.0.8078.73（原沙箱）、Noto CJK、16 MiB stack。各命令的隔離目錄、伺服器/runtime核對與完整環境見原件。以下不冒稱本機 Claude WSL 或 GitHub CI 已跑。

| 實際命令／驗收 | execution SHA | 終態 |
|---|---|---|
| D44修後 `GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js` | `cf58aeb61b25c55262b55193a0511f5bb2c8e516` | 377／0／0，exit0，192.075秒；partial；其後F僅登記test hash／提高本段count |
| `d44-ui-mutations.py --root /tmp/r02-d44-mutations --output /workspace/r02-ui1-evidence/d44-ui-mutations --timeout 2100 -- python3 /workspace/r02-ui1-evidence/tools/r02-browser-run-v2.py pf` | F | 正式baseline377／0／0已完成；三UI13＋8mm預填＋紅色撤回尚待整輪終態 |
| `python3 tests/run_all.py --only node:tests-js --only node:panel_fill_ui_contract --only node:parameter_confirmation_settlement`（原process-local reaper包覆） | F | 785／0／0，133.148秒，exit0；非完整native |
| 三條原architecture裁判（同下列命令） | F | 604檔／798edges／0diagnostics、205及18tests，各exit0；Linux scan／receipt／report已更新 |
| `MUTATE_CACHE=/tmp/r02-ledger-final-cache python3 tests/mutate.py --check` | F | exit0，70killed／1crashed／4equivalent／3retired，0stale／blocked／survived；無需對同一有效closure重產 |
| `GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js` | `f7d8802cc7a01c76d35f173473cbe45a80165c89` | 349／0／0，exit0，198.350秒；partial |
| `python3 tests/panel_fill_ui_mutations.py`（完整參數見收據） | `fdd94809e9e2bce05a7be5c1f6dbef6eae2bf92f` | 六組各具名0／1／0；7份正向349／0／0＋6份具名紅，原來源全部恢復；1544.301秒 |
| D44前完整 `node geometry-web/cdp_test.js` | `82257ab8b76e4eb36a9c26539125c83649485487` | 2616／0／0，exit0，1906.993秒；86段strict golden matched。新F尚未重跑full，不移標 |
| `GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` | `ffa22ad9245021c17c0a827847270bc5882cbb69` | 356／0／0，exit0，441.562秒；grid scope |
| `node geometry-web/space_model_test.js` | 同上 | 242／0，exit0，183.846秒；full-space scope，timber兩組非本scope |
| `python3 tests/run_all.py --build --update-expected` | 同上 | 完整226 suites，5221pass／4fail／1原允許GDI skip，1942.533秒，**原exit1**。數量核收獨立exit0，不是產品全綠 |
| `python3 /workspace/r02-ui1-evidence/tools/reap-owned.py python3 tests/run_all.py --build --only py:test_assembly_mutation_check --only py:test_mutation_anchors --only node:tests-js` | `79049d7e0c4a60f7a5e2ff4c7023cd713f0c387f` | 修後只重跑受影響三套，763／0／0，128.444秒，exit0；原strict expected啟用，**不是第二次完整native通過** |
| `MUTATE_CACHE=/tmp/r02-ledger-final-cache python3 tests/mutate.py --check` | 同上 | exit0：70killed／1crashed／4equivalent／3retired，0stale／blocked／survived；M20是原三次同夾具SIGSEGV，不冒稱assertion-killed |
| `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | 同上 | exit0，604檔／798edges／0diagnostics |
| `python3 -B tests/test_architecture_contract.py`；`python3 -B tests/test_product_architecture.py` | 同上 | 205／18 tests，各exit0；Linux manifest/scan/receipt與本片report已更新 |

另外已實跑：四套原生PF 92／0／0、新native wire9／0／0、三份Node契約／保存38／0／0。完整帳本78筆均重產；首輪／中斷／舊cache絕對路徑造成的BLOCKED保留，最終bridge18項全killed。來源詳封包，未移標至本輪head。

原native四個fail的處理：容器PID1留下zombie，使用只回收自身孤兒的process-local subreaper，原kill／期限／斷言不變；archive A01/A02只更新同一guard的文字錨點，六原具名反證均0／1／0；格式測試加入已採/19正向案例，未知版本改驗/20，所有降版／缺能力斷言保留，撤回會同名轉紅。原完整結果與修後局部結果分開，沒有宣稱整輪exit0。

原85段canvas golden未放寬；P128已由349提高至本片完整流程實跑377（partial計數）。新F strict full尚待執行，未以partial冒稱full比對通過。

依使用者提供，CI受帳號計費阻擋；已觀測run40701559129七jobs皆runner_id=0、steps=[]，沒有實際產品測試。不能把這種failure當產品紅綠，也沒有可核實的WSL新收據。

未改公理層、正典閱讀器、決策佇列；PF2-NATIVE／PF3-NATIVE／BACKLOG依設計§9.2～9.4擬補全文記錄本片與GEO-219減項。PF-bearing scenario leaf仍fail closed；未修改#352／#353／#354分支，未合併main。

D44新增保存斷言初輪368／1原件保留：新斷言誤讀legacy state；修為版本化uiContract精確view，期望8/1未變。該輪原dump／references／完整state保存比較已過，原gcanvas確實保留來源91:1；不把這個測試欄位錯誤描述成產品遺失資料。round7含完整失敗與修後377原件。
