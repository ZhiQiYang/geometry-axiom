# #54 單房候選：2026-10-06 收尾驗收

本輪修正已開始的 Space／中鍵 pan 被房間候選路由攔截，以及取消選房後舊起點誤吃 pan 放開事件。產品差異只在 `app.js` 的 `feMove`／`feUp`；沿用既有 pan、草稿、核心提交及保存格式。

基準為 main `5e0e92b850209e9e2895612148694c1d1e1e4815`。PR63、64、76 及後續修正已存在，2026-10-03 的待開發文字是歷史狀態。本輪沒有重建辨識引擎、擴大 #87 多房範圍、增加持久候選 schema，或修改公理、floor、golden、Source Inspector、PDF 資源生命週期。

## 原六項驗收與新增證據

| 原驗收 | main 已有實作 | 本輪測試與判準 |
|---|---|---|
| 校準後只選目標房間 | `RoomOutlineWorkspace.start/up/acquire`；向量優先、本地 raster 備援 | 正式 UI 從檔案匯入、選頁、兩點校準開始，PDF／影像各驗矩形、L、凹口；另驗框選、來源位移／90°旋轉、390 px 窄視窗。 |
| 疊圖、修正、尺寸核對、失敗明示 | 原有候選、逐邊尺寸、補點及明確分隔工具 | 逐角循環順序 oracle、內外點、真的尺寸變更及逐邊入值；門洞拒絕、鄰房連通警告、人工分隔重取，不把搜尋框當房間。 |
| 確認前原面不變，取消／失敗保全，undo／redo | 既有 `emitBoundary` 交易與候選確認收據 | 真 native `dump`、有序頂點、候選取消、非法自交拒絕、確認後 UI undo／redo；pan 同時核對候選完整 snapshot、來源 basis、review 與正式 dump。 |
| 非機密矩形／L／凹口及成本比較 | 自製 `room_outline_fixture.js`／既有公開 PDF | 新獨立 oracle 不呼叫產品演算法生成 expected；PDF／影像六例比較相同校準來源、相機、原面、工具、展開狀態及相同最終有序輪廓。兩路都含真尺寸修正與每條邊入值。 |
| 真 Save／空白 Open／來源對位／接續投影 | 既有 `.gcanvas`、來源 bytes、校準、receipt、投影及空間模型 | 真下載 `.gcanvas`，關閉整個 context；新 context 經 UI New 核實空白，再 UI Open 實體檔。精確比來源 bytes／頁／變換／校準／收據與原生頂點。空間比完整 base scene、binding、settings、所有邊及獨立面積×高度，保存含 model 檔再空白 Open。 |
| 原有矩形／候選／已確認／重核區分 | `reviewState` 以來源 basis 與幾何 fingerprint 綁定 | 檢查四種狀態、來源替換／重新校準要求重核且不縮放正式幾何；真 Worker 結果在取消、重校準、離開／重進面、換頁／換來源後不能覆活舊候選。 |

## 可重現的測試

- [`tests/test_room_outline_closeout.js`](../../tests/test_room_outline_closeout.js)：24 個獨立精確幾何／freshness 測試。循環只允許起點與方向變化，保留邊鄰接；獨立線段交叉／接觸判斷。含穿過室內的尺寸干擾、四方向、門洞 jamb、12 頂點連通環、PDF CTM／viewport、區域填色障礙及受控 Worker 回呼。
- [`tests/room_outline_acceptance_browser.js`](../../tests/room_outline_acceptance_browser.js)：上述正式 UI 路徑與六例成本比較；預設跑全部 10 個正常場景及反例。`page.evaluate` 讀取狀態，不代替 UI 寫幾何或保存。
- [`tests/room_outline_pan_browser.js`](../../tests/room_outline_pan_browser.js)：原生／來源／初始校準是明示的 API fixture，後續 pan 使用真鍵鼠。覆蓋選房中、待確認、已核對、先放 Space 再放滑鼠、中鍵、H 與取消後 pan。額外 `pointercancel` 是注入生命週期事件，並重現 capture release、清除合成事件留下的文字選取；另驗真 pointerup 抵達且無原生 drag-and-drop。
- [`tests/room_outline_worker_browser.js`](../../tests/room_outline_worker_browser.js)：真正執行產品 Worker，攔留其原始 `MessageEvent`；真 UI 失效操作後，故意把原結果送回 consumer。舊 callback 不得清掉新工作，新 callback 才能生成正確有序候選。初始 native／來源／校準是 API fixture。

上列連結相對於 repository root 的路徑為 `tests/…`。每個 browser harness 都必須指向獨立服務；會操作／重置該服務的合成場景。使用已安裝的 Node、Playwright、Chromium 與 C compiler，無新增相依套件。

```sh
mkdir -p /tmp/issue54/bin /tmp/issue54/fb-normal /tmp/issue54/fb-worker /tmp/issue54/fb-cdp
gcc -std=c11 -O2 geometry-web/web_bridge.c -lm -o /tmp/issue54/bin/web_bridge
gcc -std=c11 -O2 geometry-core/model_base.c -lm -o /tmp/issue54/bin/model_base

# 各服務各開一個終端，並依測試使用 8896 / 8897 / 8898 與不同 feedback 目錄。
GEOMETRY_BRIDGE=/tmp/issue54/bin/web_bridge GEOMETRY_MODEL_BASE=/tmp/issue54/bin/model_base \
GEOMETRY_FEEDBACK_DIR=/tmp/issue54/fb-normal python3 geometry-web/serve.py 8896
```

```sh
node --test tests/test_room_outline.js tests/test_room_outline_worker.js \
  tests/test_room_outline_closeout.js tests/test_project_store.js tests/test_reference_workspace_races.js

GEOMETRY_TEST_URL=http://127.0.0.1:8896/ \
GEOMETRY_ROOM_ACCEPTANCE_DIR=/tmp/issue54/normal-final node tests/room_outline_acceptance_browser.js

GEOMETRY_TEST_URL=http://127.0.0.1:8897/ \
GEOMETRY_WORKER_OUTPUT=/tmp/issue54/worker-final node tests/room_outline_worker_browser.js

# 與 CDP 共用服務時務必依序執行。
GEOMETRY_TEST_URL=http://127.0.0.1:8898/ \
GEOMETRY_PAN_OUTPUT=/tmp/issue54/pan-final node tests/room_outline_pan_browser.js

GEOMETRY_TEST_URL=http://127.0.0.1:8898/ GEOMETRY_FEEDBACK_DIR=/tmp/issue54/fb-cdp \
GEOMETRY_CHROME=/usr/bin/chromium GEOMETRY_CHROME_FLAGS=--no-sandbox \
GEOMETRY_CDP_PORT=9448 node geometry-web/cdp_test.js
```

本次只動面編輯 pointer 路由，依 AGENTS 跑完整 `cdp_test.js`；空間產品程式未變。上述專用 UI 測試另外實走投影及模型保存重開，不宣稱跑過完整 `space_model_test.js`。最終 exact-SHA、命令 exit、統計及 runtime 指紋記於本分支 PR，不用開發中 run 冒充最終驗收。

## 釘紅與證據界線

- 原 main 真 Space 拖曳 `(80,45)` 在選房與候選狀態均只產生 `(0,0)`；H 對照為 `(80,45)`。擴充鍵鼠 regression 在 main 為 22 pass／6 camera fail（exit 1）。原生 dump 不變，沒有 browser error。原 P79 的 H 工具切換斷言沒有真的拖曳，不能代替此證據。
- 僅修 `feMove` 後，一般 pan 正常。注入取消的反例先發現測試殘留文字選取導致原生拖放；清除該注入副作用後，真 pan pointerup 被舊房間選取吞掉，picking 消失、drag 卡在 pan（26 pass／3 fail，exit 1）。因此 `feUp` 也依既有 drag kind 優先完成 pan；沒有修改共享的取消／導航 handler。
- Raster 框選初估受採樣影響，不承諾精確 mm。該例核對逐角誤差不超過一個來源像素，明示 raw 座標，且拒絕以框選矩形充數；之後人工修正及正式／重開幾何仍要求精確 authored oracle。沒有放寬舊 golden。
- 空間接續例明確選擇 boundary-only、關閉厚牆；不可解讀成所有凹口材料牆均已驗證。
- 成本是合成鍵鼠動作數及含 automation settle 的機器經過時間，非真人操作時間。是否改善以實際結果為準，不預設候選更快。
- Worker 晚回覆是「真計算結果＋consumer fault injection」，不是聲稱已被 terminate 的 Worker 自然還會送訊息，也不是記憶體回收測試。
- Save 使用產品真的下載備援；只在瀏覽器起始時隱藏 `showSaveFilePicker` capability。Open 經 Playwright file chooser seam。沒有假寫 archive、沒有 `exportBytes/importBytes` 代替 UI；真 OS picker、IME、實體手機仍未驗。
- Library 現行 consumer helper 取得私人 bytes 受阻：`library download request failed: hosted apps tools/list request failed: network`，exit 1。沒有取得私人檔、猜 URL、繞拒絕權限或要求重傳；歷史私人 CaseA 的 `edge-open/tooManySegments` 不能冒充本輪結果。公開交付僅含自製合成資料。

原議題是否整單關閉仍由 root／使用者審查，本 PR 不自動關單、合併或部署。
