R02 UI-1 將既有完成面／鋪排原生能力接到 App 的面內屬性檢查器。從物件面進入「面設定…」→「完成面與鋪排…」，可建立／編輯、預覽、確認／取消、保存及重開；投影與完成面共存，依平面建立空間仍可達。表單只組定義，幾何由原生推導。採用 [#128 方向 A](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6436162095) 與[完整契約](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)。

**Draft／未達合併條件。** #343 → #346 → #347 尚未同源閉合，UI15 未跑；本片不宣稱 PF-6／PF-4／PF-5 或整體 R02 完成，`complete:false` 保持不變。

## 唯一 current-state 矩陣

- 完整 head／證據 head：`b609c16095d8dbbc539e2b3b3127c61cf9e96893`。
- 基底：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
- 固定產品與測試來源 F：`fdd94809e9e2bce05a7be5c1f6dbef6eae2bf92f`；其後為架構產物／證據。F 的 bridge 帳本尚在重產，不能稱整體全綠。
- 真 UI 基準執行：`f7d8802cc7a01c76d35f173473cbe45a80165c89`，349 pass／0 fail／0 skip，exit 0，198.350 秒。F 只再修反證工具並登記實測 P128、架構清單及帳本進度；六組反證正在 F 的獨立 clean checkout 執行。
- [進度與原件索引](https://github.com/ZhiQiYang/geometry-axiom/tree/b609c16095d8dbbc539e2b3b3127c61cf9e96893/evidence/r02-ui1-20261028)：三份 receipts-round 封包逐檔附 hash、完整輸出、命令、環境與 execution SHA。歷史紅燈保留；不與本矩陣混用。

| 案例 | 實際狀態與範圍 |
|---|---|
| UI01 入口／減項 | 已實跑：真物件面→面設定、投影共存、空間入口可達；原投影入口與重複屬性／確認區合併 |
| UI02 明選來源 | 已實跑：未放置 D3、完整明設 frame、固定材料版本、正方形選軸、typed 來源、明選柱；樑與多障礙組合未跑 |
| UI03 精確值 | 已實跑：X=17/2 wire 與 DOM、大面積9999999800000001、負索引交丁；厚度9.5、負gap、等於period的stagger皆原生拒絕 |
| UI04 結果誠實 | 已實跑：PF05/23/24左右實寬與分段、X重判、nonSeams、零片、1mm裁片、內層error；確認前既有宿主與三支角材前後影響可見 |
| UI05 生命周期 | 已實跑：取消、晚token、掉確認回覆同requestId查復、切面／新專案與Undo、同dump歷史往返、同id刪除重建、晚A不覆蓋新B；未外推任意並行故障組合 |
| UI06 no-op／原子性 | 已實跑：同定義零POST／history／revision／dirty；同值不同來源保留差異；每次實質確認只一筆history及一次通知 |
| UI11 保存 | 已實跑：真下載.gcanvas→fresh BrowserContext正式開啟、dump逐byte與完整references/PF狀態逐欄相同；未知能力／缺來源／篡改皆零替換。共用同一原生服務，非另一原生程序／OS picker |
| UI12 可操作性 | 已實跑：390／720／1280、可命中確認、焦點、Esc回入口、CDP composition Enter不確認；實體IME／觸控／輔具未跑 |
| UI13 真入口與撤線 | 真入口349斷言基準已過；三項必要撤線及焦點／影響／場景同步三項反證執行中，尚未列整組通過 |
| UI14 分片能力 | 已實跑：僅本片supportedActions、後片明示限制、無空動作；全域complete:false且scope完整性獨立判斷 |
| UI15 同源整合 | **未跑／未達合併條件**。#343→#346→#347來源鏈未閉合，不借S324局部舊收據 |

## 實際命令與 gate

命令在雲端、16 MiB stack、Node v24.19.0、Google Chrome156.0.8078.73（原沙箱）、已安裝 Noto CJK 下執行。精確 runner 與環境在封包 tools/result.json。

- `GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js`：上述真 UI 基準349／0／0，exit0；**partial，不冒稱完整canvas**。
- `GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -B tests/test_panel_fill_ui_contract.py`：來源 `11217428a8ebe6fa255892c5919a18c0c43af62c`，9／0／0，exit0。
- `GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -B -m unittest tests.test_panel_fill_finish_surface tests.test_panel_fill_layout tests.test_panel_fill_host tests.test_panel_fill_support`：來源 `1b63a0498bf941da5b83866d7234afb25d7aefb4`，92／0／0，exit0。
- `node --test tests/test_panel_fill_ui_contract.js tests/test_panel_fill_project_store.js tests/test_scenario_project_store.js`：來源 `f9f0759aee4c94b1293516e95a5a953c6d497798`，38／0／0，exit0。既有更廣保存回歸105pass、24個缺native fixture的原有skip另列，不當完整native通過。
- F 上 `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`：exit0，604執行檔、0 diagnostics；`python3 -B tests/test_architecture_contract.py`：205案exit0；`python3 -B tests/test_product_architecture.py`：18案exit0。Linux重產scan／receipt，本片報告放evidence，歷史PRODUCT-ARCHITECTURE.md不改。
- `python3 -u tests/mutate.py`：原全輪exit2；core60已實跑52 killed／1 crashed／4 equivalent／3 retired，bridge18環境前置受阻。已修隔離checkout及舊ELF含不同絕對路徑的cache問題，以原支援的`MUTATE_CACHE=/tmp/r02-ledger-final-cache`接續18項。最終`--check`尚待終態，沒有調低二進位相等守門。
- 完整native census、完整canvas、相關grid／space及本機Claude WSL job：**目前未收完，不列已過**。原85段golden保持原值，只新增實測P128=349；full仍須嚴格比對。

依使用者提供，CI受帳號計費阻擋。已觀測run40701559129七jobs皆runner_id=0、steps=[]，沒有實際產品執行；不拿該failure當產品紅綠。

本片未改公理層、正典閱讀器或決策佇列；PF2-NATIVE／PF3-NATIVE／BACKLOG只增設計§9.2–9.4擬補文字。PF-bearing scenario leaf仍fail closed，不宣稱該組合可用。未動#352／#353／#354分支，未合併main。
