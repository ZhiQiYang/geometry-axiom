# 非瀏覽器登錄與必要正式整合驗證

`python tests/run_all.py --build` 嚴格執行已登錄的非瀏覽器 suites，
逐 suite 比對 `run_all.expected.json`。exit 0 只證明這個範圍，
不代表尚未接上產品的模組或下列正式整合驗證已完成。
既有 floors、具名平台 skip 清單與實際測試斷言維持。

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
