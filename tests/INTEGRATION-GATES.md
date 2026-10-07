# 非瀏覽器登錄與必要正式整合驗證

`python tests/run_all.py --build` 嚴格執行已登錄的非瀏覽器 suites，
逐 suite 比對 `run_all.expected.json`。exit 0 只證明這個範圍，
不代表尚未接上產品的模組或下列正式整合驗證已完成。
既有 floors、具名平台 skip 清單與實際測試斷言維持。

## #123 S1 模型庫歷史入口（#159 瀏覽器收尾）

非瀏覽器：`node --test tests/test_workspace_shell_history.js`，另由
`python tests/run_all.py --only workspace_shell_history` 登錄執行。
28-case fixture 執行正式 shell／owner admission 函式及 `ContextHistory`，涵蓋同節點移入／還原、ID唯一、
鍵盤與可見入口同路由、busy／Save／readonly、零點校準、nested modal及owner重入。
它沒有真實DOM layout、native bridge、瀏覽器focus或`.gcanvas`往返證據。

本切片的正式驗收須在 exact candidate、fresh native/runtime、隔離服务／profile／TEMP 執行，
不可使用使用者正在編輯的服務。以下是正式驗收條件，不能由 nonbrowser green 代替；
本次實跑結果與平台限制見 `BACKLOG.md` 的 #159 條目：

1. 1382×804與390×844，正式範例→預覽→建立→關閉→模型庫；移除後不離開庫，
   真點同一 `#btnUndo` 還原相同模型ID，再 `#btnRedo`，以及Ctrl+Z/Y/Shift+Z。
   模型庫按鈕可見、中心hit-test可達、至少44px、無水平溢出，保存狀態仍可讀。
2. pending native Undo 期間，再按Undo/Redo、模型移除、保存均不另發mutation；
   source/context/session切換或關閉／重開後，舊回覆不復活舊owner。零點校準、
   參數／房間／面草稿與nested confirmation不被自動取消或捨棄。
3. 真readonly lease下不可Undo/Redo／移除，但仍能開啟既有3D查看；
   modal內文字輸入保留原生文字復原，Esc與原生confirm/cancel行為不變。
4. 退出模型庫／切網格或工程工作區後，原按鈕移回、ID各僅一份，其他殼層沒有新增history能力；
   新增入口不能改保存按鈕的原生user activation。保存取消零副作用；真`.gcanvas`保存、
   新專案與重開保留模型ID及資料，Undo的dirty狀態不能冒稱已寫檔。
5. 另跑原`cdp_test.js`及`space_model_test.js`正式範圍，保留各自scope、count、
   native身份、terminal exit與未驗項。不得降低既有floor／golden補過。

`space_model_test.js` 的既有 height/library 群新增 26 個正式斷言：1400×900／390×844
各 11 項庫內移除、鍵盤、焦點、同節點及完整模型／原生來源檢查，另有 4 項有效 scene
草稿保護、metadata Undo 後失效來源快取不鎖庫、Redo 復原模型並保留 raw 設定。
獨立盤點為 height/library 86→112、預設 full Space 202→228；其他群與 timber 範圍不變，
不是從成功執行回填預期數。跨專案、延遲回覆、真 download／filechooser 另用隔離瀏覽器驗收。

實體手機、IME與OS picker人工驗證另列；source-only／VM不作替代。
## #144 ResizeObserver 通知與真錯保全

`node:feedback_events` 是 41 項受控 Node VM 測試：32 個獨立 event-shaped
predicate 真值案例、三個單 guard 移除反證、notice 合併、真錯／rejection／console、
原 20 秒／300 秒節流，以及 browser harness runtime 拒絕條件。這些值可明設
`isTrusted`，不代表瀏覽器曾派出可信事件，不取代下列 38 項正式 browser gate。

`geometry-web/feedback_resize_observer_test.js` 登記為必要獨立 browser gate，
不在 aggregate 執行；它位於 geometry-web 而非 tests 的自動發現目錄。
先在乾淨凍結 checkout 建立／核對當前 native binaries，再以已安裝的 Python、
Chrome 執行（GEOMETRY_PYTHON 可指定同一 Python）：

```sh
python3 tests/run_all.py --build
GEOMETRY_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_PYTHON=python3 \
GEOMETRY_CHROME=/path/to/installed/chrome node geometry-web/feedback_resize_observer_test.js --keep
```

Windows 請將路徑換成當前已驗證的 bridge.exe／Python／Chrome；本命令不授權
修改安全設定或改用他人正在操作的服務。Harness 自建隔離 TEMP feedback、profile
與服務，沿用現有 38 個斷言與真 RO 前提，不以 synthetic ErrorEvent 冒充可信 RO。
開始、每次重新載入及結束都要求 production runtime probe 的 fresh/root/source，
比對自有 PID/session、乾淨 Git head 與來源指紋；每頁另核 runtime meta 與實際
served feedback.js bytes。HTTP 200、跨服務 session 或 source 變更都不能算通過。
identity 前後紀錄與 38 項結果應保留；若沒有真 browser，保持 required gate 未驗。
Bridge 另透過既有 `binaries.require_fresh` 核對來源／SHA-256／sidecar，未證明 fresh
即在啟動瀏覽器前拒絕；不以目錄中最近一支 exe 的名稱或成功啟動當來源證據。
若 Windows binary 身分或 SAC 仍受阻，保留該環境結果，不能修改 registry 或安全設定繞過。
實體手機／IME／OS picker、舊版 Chrome 第二句訊息及 Firefox/Safari 仍須分別標明。

## #44／#77 新增模組的實際登錄

| 原測試檔 | 非瀏覽器實際測試數 | 執行方式／範圍 |
| --- | ---: | --- |
| `test_model_update.py` | 22 | 真 bridge 與 model-base；獨立 Python suite |
| `test_model_update.js` | 39 | 模型更新契約、隔離候選及控制器 |
| `test_room_collection.js` | 31 | 房間集合／控制器；原有私有暫存編譯 bridge 和測試 owner fixture 保留 |
| `test_issue77_workspace.js` | 6 | 工作區模組；不是產品 app 接線驗收 |
| `test_issue77_attachment.js` | 4 | 純 payload／native-reference 契約；正式 owner 五項完整移至下列入口 |

四個 Node 檔共 80 tests，既有 `node:tests-js` 294 → 374。
Python 新增獨立 22 tests，不併入 Node 數量。
共同自製 PDF/payload 夾具 `issue77_attachment_fixture.js` 不註冊任何 test，
不把 Node 對空腳本的假性一項成功計入 floor。

## #77 必需的正式 owner 五項驗證

入口 `tests/integration/issue77_attachment_owner.js` 保留原五項完整斷言：

1. 真 ZIP roundtrip 與原 PDF 恰保存一份，重開再保存仍保留 attachment。
2. 未知 envelope version、kind、schema、capability、缺能力及重複 kind 拒絕，不能靜默丟資料。
3. 來源閉包與最終 native object hooks 拒絕遺失來源／房間引用。
4. ContextHistory rename、unlink、native delete、同 ID undo/redo、unknown history 快照。
5. 讀寫 context guard、遲到寫入隔離及房間 metadata 與 native 同一步交易。

未配置正式 owner test adapter 時，直接執行：

```sh
node tests/integration/issue77_attachment_owner.js
```

入口輸出機器可讀 JSON：`status: pending_implementation`、
`required: 5`、`executed: 0`、`passed: 0`，逐項列出缺口，exit 3。
這表示五項尚未透過正式 adapter 執行，不能用它判定目前產品 owner 是否已實作；也不是 skip 或 pass，不加入 `ALLOWED_SKIPS`。
`run_all.py` 顯示這個必需入口與範圍，不在非瀏覽器合計中假算五項。

owner 實作後，以 test-only shim **映射真產品 registry／envelope／pack／unpack／history／transaction API**：

```sh
GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER=/tmp/real-owner-shim.js \
  node --test tests/integration/issue77_attachment_owner.js
```

shim 不得另造 store／ZIP envelope／history 來取代正式接線。
配置了 shim 卻少必要方法會立即 setup fail（exit 1），不允許跳過。
只有這五項真 owner gates 全部實跑通過，才可聲稱 attachment 正式整合通過。

PR124 合流後，本 repo 已提供 `tests/integration/wp60_actual_owner_adapter.js`。
它映射實際有限 registry、formal reader、ContextHistory 與房間交易；不註冊另一份 registry。
後兩項各使用真 /10 與含已提交 native rule 的 /11 `.gcanvas`，保留原五個 test names：

```sh
ulimit -s 16384
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge \
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER=tests/integration/wp60_actual_owner_adapter.js \
GEOMETRY_OWNER_GATE_DIR=/tmp/geometry-owner-five-evidence \
  node --test tests/integration/issue77_attachment_owner.js
```

adapter 先檢查兩支 binary 的 freshness receipts，再自建 disposable loopback app/service，
對 `/runtime` 驗 exact source／fresh／root。TEMP evidence 記錄原始 native receipts 所支持的
條件，結束只關閉本測試 browser/service group。五項不加入非瀏覽器 floor，也不計內部
checks 為額外 test cases。unknown-history 負例是未經本頁 observer 的真 native preview，
再由正式 owner 觀察真 confirm，要求重新關聯並保留原始 pins／歷史值／PDF。

## #77 必需的四個真瀏覽器入口

T4 逐房顯示修復另有必要的正式 gate：
`tests/test_shared_room_display_browser.js`。以隔離 `GEOMETRY_TEST_URL`、TEMP
`GEOMETRY_FEEDBACK_DIR` 與 `GEOMETRY_ROOM_DISPLAY_OUT` 執行；最終證據設定
`GEOMETRY_REQUIRE_CLEAN=1`。使用 repo-authored `issue77-two-rooms.pdf`，API 僅作
初始校準頁／原幾何夾具與唯讀裁判。真 UI 明選採用、取消／手動新房間、透明度／鎖定／對位、
Undo/Redo、下載完整 ZIP、新空白 context Open 在 1280 與 390px 各跑；未知 schema、
缺能力、錯型 display、8MiB manifest 超限檔從正常 Open 拒絕且保住整體狀態。
初始 crop 是明示夾具 `[10,20,580,360]`，不冒稱此 gate 有 pointer crop import；
真正 PDF import／手動矩形仍由 #48 formal gate 驗證。它不算入非瀏覽器 floor，
不取代既有四項 #77 gates 或 full CDP／Space。

以下四個腳本使用 Playwright、實際 Chromium、app 與 native；不是 `node --test` suites。
它們在 `NODE_EXCLUDED` 逐檔登記具體原因，非瀏覽器合計**未執行、未驗證**，
不把 script 未跑或臨時 prototype adapter 成功當產品整合完成。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_exit_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_recovery_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:18951/ \
GEOMETRY_FEEDBACK_DIR=/tmp/issue77-formal-feedback \
  node tests/test_issue77_remove_browser.js
```

先以目前 exact head 的隔離服務驗 `/runtime` 與 fresh binary closure；
回報／截圖／browser profile 放 TEMP，不使用使用者服務或私人圖紙。
正式產品須提供 RoomCollectionWorkspace、來源／房間 UI、F attachment 接線、
草稿離開及恢復的 owner guard、實際完整 ZIP 保存重開。
`GEOMETRY_ISSUE77_BROWSER_ADAPTER` 是明示的 prototype evidence 選項；
若使用，報告必須標 prototype，不能代替上述正式 owner 五項驗證。

既有 `geometry-web/cdp_test.js` 與 `geometry-web/space_model_test.js`
仍另外執行，各自完成及 floor 相符才是其範圍的證據。


## #46 獨立快照模組的登錄與外部門檻

snapshot/diff/review-native 三個 Node 檔（23／18／18）加入
NODE_TEST_FILES，完整 census 發現 Node 374 → 433；Python
test_scenario_verify 35 tests 加入 PY_NEEDS，要求 fresh bridge＋model-base。
既有 floors 及 ALLOWED_SKIPS 不變；新增數量取自完整 census，不以空腳本或 skip 補足。
Linux cloud 的完整 candidate census 在 process-local 16 MiB stack 下實跑；
8 MiB stack 曾使未修改的 native integrity／subgrid 基線崩潰，不能用它的 fail／skip
調低 floor。owner 套用登錄後，POSIX 的正式凍結 head 驗收命令為：

    ulimit -s 16384
    python tests/run_all.py --build

本 patch 的 candidate census 不能替代正式已發布 runner 在最終 head 的 strict 驗收。
這些測試只證明獨立快照／原 bytes／格式／origins／隔離 native 核驗，
不代表產品 A/B 入口、whole adopt 或 recoverable history 已完成。

以下兩個既有腳本在 NODE_EXCLUDED 逐檔登記原因，aggregate 未執行、
不計 pass/skip；仍須另外執行並保留證據。

先用 tests/binaries.py 建置 receipt-backed runtime；一般 npm .build 產物
沒有這份 freshness receipt，不能替代。Playwright／Chromium由驗證環境提供。

    python tests/binaries.py build bridge model-base
    GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base node tests/scenario_browser_check.cjs

這是 ephemeral loopback 的獨立 module browser gate：1280／390、
真正 ZIP download／file input 重開、原 bytes、B 不改 A、fork／replacement diff、
latecontext／tamper；禁止 live upload。沒有正式產品 UI/adoption 的驗收語意。

    GEOMETRY_SCENARIO_PROJECT_MODULE=/absolute/path/to/actual-owner/project-store.js GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base node --test tests/test_scenario_grid_interface.js

GridDraft 使用真正 owner project-store／同目錄 feature-attachments validator；
PR104 尚未在 main 的這個 slice 維持注入 interface，
不是以 unsupported 丟棄已批准 raw 草稿。缺 owner 注入時原腳本的具名 skip
絕不能當 compatibility pass，也不加入 ALLOWED_SKIPS。
真正 validator 必須實跑 raw 非法／未完成輸入、獨立 A/B、ZIP 重開、unknown kind/cap 拒絕。
正式 saving adapter 合 main 後，owner 再把此檔移入 NODE_TEST_FILES、重做 census；
不能在本 patch 預先假算第 434 項。

Linux cloud 的 scenario Python suite 為 35/35；Windows 目前有 8 個
temporary-shebang fixture skips。這些沒有平台豁免，Windows strict 會拒絕全過；
須由後續 test owner 解決 fixture portability，不能使用 allow-skip 冒充完整驗收。

## #116 B 情境選單

`tests/test_issue116_browser.js` 是必跑的真原生／瀏覽器 gate，獨立於非瀏覽器 aggregate。
提供隔離 `GEOMETRY_TEST_URL`、TEMP `GEOMETRY_FEEDBACK_DIR`，並以 `NODE_PATH` 指向
既有 Playwright runtime（本機可用 Codex bundled packages），執行 `node tests/test_issue116_browser.js`。
它驗 `/runtime` repository/fresh、真右鍵及數值欄位、取消不改、精確凹口確認、單步 undo/redo、
完整 `.gcanvas` 保存／重開、過期上下文拒寫、鍵盤及搜尋、孔邊快捷限制與核心角色拒絕、390/720px 可達性。
截圖／驗證專案只寫 TEMP；不寫使用者 feedback 或已提交 golden。
另跑無 scope flag 的 `geometry-web/cdp_test.js`，包括原選取／游標及所有既有共用介面回歸。
PR #114 正式多房間 owner 與實體 iOS／IME／系統選檔仍須 dot 整合後驗收，不能以本 gate 代替。

## #48 正式 app 證據流程

`geometry-web/evidence_links_integration_test.js` 的 110 個檢查獨立於非瀏覽器 aggregate；真 app/store/native、1280/390px、原圖手動矩形和欄位選擇、完整 ZIP 保存／新空白 context 重開、刪除／ID 重建、evidence-only bytes、undo/redo、32 個 staged navigation race 和非法匯入零提交。只使用自製 PDF。另保留既有 independent adapter 67 項，不把 memory-backend 結果當正式保存證據。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:18962/ \
GEOMETRY_REQUIRE_CLEAN=1 \
GEOMETRY_EVIDENCE_TEST_DIR=/tmp/issue48-formal \
node geometry-web/evidence_links_integration_test.js
```

服務须是 exact head 的 fresh receipt-backed runtime；TEMP 結果記 head/tree/runtime，禁止用戶 8765。共用 app 行為另跑無 scope flag 的 CDP，82 段 golden 維持。非瀏覽器新增 evidence store 7 項、控制器 28→29、shared-reader races 48→54；補登錄 main 已存在的 grid definition diagram 8 項，沒有降低原 floors。

#131 的 `tests/test_issue123_create_feedback_browser.py` 是需指定服務／TEMP輸出的獨立 Playwright 腳本，明確登錄在 `PY_BROWSER_GATES`，不冒充 unittest 的空測試。既有四個 store VM fixture 現提供瀏覽器原生 `structuredClone`，原 assertions 維持；新增三項 PDF 資源回歸使 494→497。#48 新增真 core-only fallback scope/bytes、undo/redo保存及新 context 重開；原 80 項全部保留，正式 gate 增至110。

## #46 正式方案操作生命週期

`tests/test_scenario_workflow_browser.js` 是必要的正常流程 gate，使用下列相同環境
另指定自己的 TEMP output，必須與 lifecycle gate 串行。
在 1280/390px 都以正常 UI 保存 A、fork B、同一正式 app 修改 B 的參數，核對 A
完整記錄不變、比較、整體採用、一筆 history 的 undo/redo、真 ZIP Save，以及
新空白 context 真重開。瀏覽器 download fallback 實際下載；OS 系統 picker 未在 headless 驗證。
首次教學卡只按正常「知道了」關閉，不移除 DOM、不強迫點擊。

`tests/test_scenario_lifecycle_browser.js` 是必要的獨立正式 app／native gate，
登錄於 `NODE_EXCLUDED`；非瀏覽器 aggregate 不冒算其 assertions。
以隔離 URL、TEMP feedback 與 `GEOMETRY_SCENARIO_OUT` 執行，凍結驗收另設
`GEOMETRY_REQUIRE_CLEAN=1`。同一 native root 的瀏覽器測試必須串行。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:18991/ \
GEOMETRY_FEEDBACK_DIR=/tmp/scenario-feedback \
GEOMETRY_SCENARIO_OUT=/tmp/scenario-lifecycle \
node tests/test_scenario_lifecycle_browser.js
```

它從正常 UI 建立 A、複製及隔離編輯 B，只持有真實 export、unpack 或 disposable
verifier 的回覆，於正常 Cancel 後等候原按鈕 handler 的真正終態；要求
World、catalog、dirty/saved、context/revision 與 undo/redo 完全不變。
Capture 的真 native dump 等待涵蓋關窗及重開；原子採用涵蓋已提交 confirm
回覆等待期間的關窗、新修改與雙向歷史阻擋，以及真 Undo/Redo。
未知 confirm 結果沿正常 reconnect 重取精確終態，不重送 confirm。
中斷 ticket 修補後，建立回覆連續遺失兩次必須保留同一 request 身分與 native B，
**不再自動捨棄**。原本「lost create 立即 close」的斷言已由下列恢復／保全 gates 取代：

- create 前以真 IndexedDB strict transaction 同時完成完整 A checkpoint 與 exact ticket，
  未確認的 creating ticket 經十次真 reload／Edit（超過未改動的 cap8）仍不產生新 tuple、
  import 或隱含 close
- 真 child import 已在 native confirm、回覆仍被持有，以及 active B 原生修改後，
  reload 保留 ticket 與 B；既有 Edit 明示中斷 Resume 不可用，不重匯舊 catalog
- B 在第一次 native request 前已阻擋一般編輯；同源 standalone B 的真 bootstrap
  同樣不 import／reset／覆寫恢復包。它不是 metadata-only Resume 的實作或驗收
- 真瀏覽器讀取 A／B1／B2 的 IndexedDB keys 與 Web Locks；B 使用 native-context
  專屬 namespace，第二次 B 不覆寫第一份恢復包，也不污染 A
- 真 identified discard prompt 先拒絕再同意；拒絕保留 ticket／B，同意才 exact close。
  Cancel 的兩次 close 回覆遺失保留 durable retiring identity；reload 後第一次 Edit
  只重試原 close，下一次獨立 Edit 才能配置新 context
- export／unpack／verifier，以及 durable Finish checkpoint 後、close 發送前的持有區間，
  B 的原生修改、Undo／Redo、metadata owner 寫入都必須拒絕，iframe 維持 inert
- Finish 的真 strict IndexedDB transaction 同時寫入一般 A recovery、獨立完整 immutable
  receipt 與 retiring ticket；交易 complete 以前不能發 native close。核對 receipt digest、
  manifest／source closure／B scene，A native World 不變且恰增加一筆「保存候選方案」history
- Finish close 回覆遺失後，ticket／immutable receipt 保留；一般 recovery 不改 receipt，
  reload 恢復完成的完整 A，且已確認的較新 A metadata 不被舊 receipt 回滾。exact close
  重試不得再新增 history、create 或丟失完整 A

原 Capture／Cancel／whole-adopt／unknown-confirm／Undo／Redo gates 保留。
reload 的比較只要求可持久保存的 project identity、World、catalog、草稿及 dirty／saved；
不把本來只屬於該文件的 context token、revision 或 Undo history 冒稱為 reload 後復原。
所有材料是 synthetic；不把 timeout、未完成 Promise 或 memory DOM 結果當 pass。

**本次中斷 ticket 修補的瀏覽器狀態：未執行。** 環境的 browser／AF_UNIX EPERM
限制未解除，本次只做腳本語法與 diff whitespace 檢查，沒有啟動 Chromium。
上述所有新增／改寫路徑以及保留的 lifecycle 路徑，均須在可用的真 browser／native
環境另跑；Node storage fixture 或 HTTP/native 等價結果不替代 IndexedDB／Web Locks／
reload／iframe UI 驗收。BFCache、取消 beforeunload、跨 profile／origin、實體手機及
OS 系統 picker 不在本腳本已編寫的 coverage 內，仍屬另行待驗；不算 pass／skip。

正常 `test_scenario_workflow_browser.js` 另以真 PDF import、手動矩形與明選參數欄位建立證據，
移除圖頁後保存 A/B，要求根專案與兩份 leaf closure 共用恰一份原始 PDF bytes。
1280/390px 比較區必須可見左200 mm／右300 mm，不以 base64 原始內容充當可讀驗收。
另外三份命令歷史 archive 先走真 disposable native 驗證，再用正式比較按鈕驗 reset、
reset後同ID重建及CRLF；顯示必須來自該驗證的 `load-prepare.final_scene`，
不能把原始歷史命令當成目前定義，也不能自行在前端重播命令或求值。

`tests/integration/scenario_context_lifecycle.py` 在同來源的空閒隔離服務上逐次建立、
原生修改、精確退休300個真 native contexts；另驗 idempotent replay、舊請求拒絕、
8個 active 上限、子 bridge 全部回收及 root dump/revision 不变。
提供 `GEOMETRY_TEST_URL`、TEMP `GEOMETRY_SCENARIO_OUT`，凍結驗收加 `GEOMETRY_REQUIRE_CLEAN=1`。
它是外部 HTTP/native gate，不加入 Python unit census，也不能用300輪 mock unit代替。

非瀏覽器 `test_scenario_project_store.js` 另驗真正 /14 ZIP 的完整 A/B 與
evidence-only 原 PDF bytes closure、嚴格 schema/capability、雜湊、容量及
ContextHistory 單步 undo/redo；其 fixture 不冒稱 native/PDF.js 或 UI 驗收。

正式 gate 現也覆蓋 #77 shared-room 來源，沿既有原頁歷史／核對 disclosure 掛同一 `#refRecordDetails` host：手動框選／明選 field0、兩附件共存且原 PDF 一份、真 ZIP/new-context重開、覆核／重新綁定與 guarded canvas 定位。正常 native edit/delete/recreation 事件直接更新同一 host，測試不呼叫 `ui.refresh()`；未保存文字原樣保留。真 PDF Worker 計數包含三次 export 及 automatic recovery snapshot，要求 created=terminated 且 live reader document 仍可讀；純 VM 回歸另涵蓋成功／尺寸拒絕／取消／load失敗，不能以 fake PDF 冒稱實際 UI。

## #61 第一切片的正式 reader 與 orphan 入口

`tests/test_grid_rule_reader_browser.js` 必跑 34 項，獨立於非瀏覽器 aggregate。
提供隔離服務 `GEOMETRY_TEST_URL`、TEMP `GEOMETRY_FEEDBACK_DIR` 和
`GEOMETRY_RULE_READER_OUT`，以現有 Playwright 執行；凍結驗收設 `GEOMETRY_REQUIRE_CLEAN=1`。
真 native prepare 後只竄改 detached 回覆的 canonical scene、能力、snapshot 完整性或 field pin。
實際 UI file chooser 的四個拒絕各需零 confirm、一次候選 cancel、原 World/context/raw/history frame 不變。
合法 /13 ZIP 則須通過真 evidence snapshot、保留 rule/highwater/raw/evidence/PDF，沿正式 Save 保留 models/faceProjections。
歷史證據 pin 的合法定義差異仍沿既有 needs-reassociation 語意，不增加拒絕條件。

P87 的 60 項由無 scope full CDP 執行；新增的 14 項為 edit/delete 各自走正式
「關閉 raw → 來源卡片刪除 → emptyNewGridSystem 續編 → 唯讀 Save → 新空白 context 真開檔 → 返回 → 明確捨棄」。
這段不使用 fixture API 或 refresh/renderObjects 補 UI 狀態。83 段共 2054，原 82 段完全不變。
34、60 是 assertions，並非端到端 scenario 數；實體手機／系統 chooser 仍有具名人工未驗界線。

## #49 正式規則案例與獨立 owner gates

正式入口沿既有組構工作區按需開啟六個有限案例，不新增幾何求值器。
`rule-cases` / `rule-case-workbench-data/1` 使用新的 `geometry-canvas/15`；
`/1–14` 及其能力守門不變。完整 root/A/B manifest 仍受既有 8 MiB 與 room
lifecycle reserve 限制。保留前以同一 detached snapshot 驗證閉包、hash、有限
typed records／predicates 及原始 receipt，再同步核對原 context／lease，提交一筆
共同 metadata history。no-op 為零筆；Undo/Redo 恢復整份原始資料。

短命 case binding 捕獲第一個 await 前的 workspace stamp，核對 selected native
session／revision／runtime，使用獨立 case counter、pending cancel tombstone 與
high-water；logical project/frame 是 frontend host observation，不是 server 的
logical project 身分認證。metadata commit 會改變 history／revision stamp，
不保證 frame／token 旋轉；成功後明確 retire/remount。關閉案例只撤銷案例
binding／adapter，不能關閉 native context 或使 live assembly candidate 失效。
未知或已退休 B 回覆 410，不能 fallback root。

以下入口均需獨立隔離 HTTP service、fresh verified bridge、TEMP output；
同一 formal native root 串行，凍結驗收設定 `GEOMETRY_REQUIRE_CLEAN=1`。

| 入口 | 實際 assertions | 範圍 |
| --- | ---: | --- |
| `tests/test_rule_case_workbench_http.py` | 19 | 真 native adapter、六案例、run/cancel、原始語義與歷史未核信；已加入 aggregate |
| `tests/rule-case-workbench-controller.cjs` | 17 | standalone HTTP/native owner 控制器 lifecycle；需 `GEOMETRY_RULE_CASE_TEST_URL`，不是 formal app gate |
| `tests/rule-case-workbench-browser.cjs` | 91 | 原 owner 元件 desktop45／390px46，需 standalone URL 與 `GEOMETRY_RULE_CASE_BROWSER_EVIDENCE`；不是保存流程 |
| `tests/test_rule_case_app_browser.js` | 76 | 1280／390px 正常入口、六案例、啟用控件文字對比、真失敗與重跑、單步 retain／Undo/Redo、真 ZIP Save／新空白 context Open 及 root/A/B完整資料；需 `GEOMETRY_RULE_CASE_APP_OUT` |
| `tests/test_rule_case_app_races.js` | 30 | 兩寬度 held GET／create、取消晚到、retention／native／history／context、live assembly candidate、B退休410；需 `GEOMETRY_RULE_CASE_RACE_OUT` |

formal 兩項另提供 `GEOMETRY_TEST_URL`、TEMP `GEOMETRY_FEEDBACK_DIR`，
結果記錄 exact head/tree、clean 與 `/runtime`。正常 Save 下載實際 `.gcanvas`
ZIP，再從新的空白 context 使用正式檔案輸入重開；不以 memory-backend
roundtrip 或舊 source 的 full receipt 代替。PR141 的九份 owner 檔案逐 blob 重用。
所有保存或載回 receipts 均為歷史未核信，只有此次 controlled native run 可顯示
本次核對；timeout、crash、缺輸出或未知 runtime 都不能冒算 pass。

完整非瀏覽器 census 的既有 Node525 → 537：store七項、prepared history與
原 stamp三項、full manifest／caller snapshot兩項。新 host13及owner HTTP19
獨立登錄；原 floors、平台具名例外、未知格式／能力／容量拒絕都維持。
瀏覽器三項在 `REQUIRED_BROWSER_GATES` 顯示必要數量，不併入 aggregate。
共用 reader／history／registry 的受影響 gates，以及無 scope flag 的 full
CDP／Space、timber partial、native300仍須另驗；本節本身不宣稱已全部通過。

## #54 單房候選的純幾何與三個必要 browser gates

`tests/test_room_outline_closeout.js` 登錄為獨立
`node:room_outline_closeout` pure suite，實跑 24 tests；不需要 native binary。
其中 VM 回呼測試只代表 cache／freshness 契約，真正 native dump 保全由下列 browser gates 驗。
本次只新增這個 expected entry（24），原有各 suite floor／具名 skip／CDP golden 全不變。

```sh
python3 tests/run_all.py --list
python3 tests/run_all.py --only node:room_outline_closeout
```

第二條是 **partial run**，不是完整非瀏覽器 census。第一條會拒絕未登錄檔案。
三支 browser scripts 均在 `NODE_EXCLUDED` 記錄理由，並在
`REQUIRED_BROWSER_GATES` 列為必跑；**aggregate 不會執行，不計入 pass／skip**。
`--list` 及結束摘要顯示實際範圍，不能把未跑的 browser gate 當成功。

| 必跑 script | 完整預設檢查數 | 真實範圍／明示測試接點 |
|---|---:|---|
| `room_outline_acceptance_browser.js` | 253 | 10 正常場景加反例；真 UI PDF／影像匯入、校準、修正及逐邊入值、取消／確認／undo／redo、實體下載、新空白 context Open、來源 bytes／校準／有序輪廓／receipt、boundary-only model 保存重開。只隱藏可選 OS Save capability，走產品真下載分支。 |
| `room_outline_pan_browser.js` | 32 | 真鍵鼠 Space／中鍵／H 及取消後 pan、camera delta、完整草稿與 native dump 保全、接續選房。初始場景／來源／校準是 API fixture；pointercancel 為明示注入。 |
| `room_outline_worker_browser.js` | 78 | 六個真 UI 失效情境、12 個真 native Workers；真計算結果在 consumer 處攔留／晚送，舊回呼不能復活或清新工作。初始 fixture 與晚 consumer 送達注入均明示。 |

每個 gate 使用自己專屬的服務／native process／TEMP 輸出。
以同份產品來源編譯 bridge/model-base，記錄編譯命令、binary hash、HEAD、
`/runtime` 的 repository／fresh／fingerprint／session；安裝好的 Playwright 與 Chromium
由執行環境提供。不得使用使用者服務、私人圖紙或共用 feedback 目錄。
服務建立命令與完整原驗收映射見
[`issue54-closeout-20261006.md`](../geometry-web/docs/issue54-closeout-20261006.md)。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:8896/ GEOMETRY_ROOM_ACCEPTANCE_DIR=/tmp/issue54/normal-final node tests/room_outline_acceptance_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:8897/ GEOMETRY_WORKER_OUTPUT=/tmp/issue54/worker-final node tests/room_outline_worker_browser.js
GEOMETRY_TEST_URL=http://127.0.0.1:8898/ GEOMETRY_PAN_OUTPUT=/tmp/issue54/pan-final node tests/room_outline_pan_browser.js
```

正式 UI 必須使用完整 default，不設 `GEOMETRY_ROOM_SCENARIOS` 或
`GEOMETRY_ROOM_EXTRA_CASES=0`；focused development run 不能代替此 gate。
修改 app pointer 路由另外依 AGENTS 跑無 scope flag 的 `geometry-web/cdp_test.js`，
與 pan 共用服務時依序執行。此計數是 assertions，非 253／32／78 個 end-to-end scenarios。
實機手機、IME、OS picker、真人時間與尚未取得的私人來源仍各自保持未驗。
此 gate 驗既有單房流程，不能據此宣稱整個 #54 效率目標完成。

## #54 候選尺寸 Enter 等價套用

`tests/room_outline_keyboard_browser.js` 是另一個必要的獨立 browser gate，
已在 `NODE_EXCLUDED` 註明原因，並由 `REQUIRED_BROWSER_GATES` 登錄 **396 assertions**。
aggregate 不執行、不計入 pass／skip；不改既有 floor 或 golden。

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:8901/ GEOMETRY_ENTER_OUT=/tmp/room-keyboard node tests/room_outline_keyboard_browser.js
```

使用自己的服務、native process 和 feedback 目錄，依上節建立環境。
完整預設包含 1440×1000 與 390×1000 的 64 個操作案例；
`GEOMETRY_ENTER_CASES=core` 僅供釘紅或開發，不替代完整 gate。
正式 UI 匯入自製 PDF、校準並選房後，對照同起點的 click／真鍵盤 Enter，
驗非第 1 邊、完整有序座標、焦點／值／選邊、連按、同值套用、非法值、
review／Confirm、source 與 native dump 保全。
Shift／Ctrl／Alt／Meta 和 held-key repeat 均核對真事件的旗標；
composition／229／defaultPrevented 與舊 DOM 晚投遞是明示合成事件。
舊 input 暫接到隱藏 fixture 容器，用來驗 connected-but-not-current guard，
finally 移除；不呼叫應用狀態 setter 或改幾何 API 製造通過。

非法尺寸沿用按鈕拒絕後的原 review 狀態；成功套用才清 reviewed。
相同尺寸再次 Enter 仍等價於再次按套用，不是去重。
數字欄輸入 `1e309` 實際被 HTML 正規化成空值，不能聲稱 Infinity 到達 validator。
實體 IME／手機與真人時間未驗。這只證明 Enter 可取代此步的按鈕點按，
不代表整個流程操作數或完成時間已改善。
