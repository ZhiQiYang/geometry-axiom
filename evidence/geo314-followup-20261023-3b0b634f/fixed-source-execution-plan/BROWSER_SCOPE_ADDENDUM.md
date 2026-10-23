# P72B 真 browser 範圍與待跑指令

此為 v2 README 的精確補充，不改凍結的 driver／README／PREPARATION。尚未執行 Chrome、HTTP server 或編譯。

固定 source `3b0b634feb54266700cc61f26c34d7aeac4c0314` 的原 `cdp_test.js:7137–7140` 沒有 P72B-only flag。原支援的 `GEOMETRY_COMPOSITION_ONLY=1` 會完整呼叫 `composition_canvas_test.js` 與 `grid_inspector_rename_test.js`，對應原 golden P72=52、P72B=50。原部分模式明確不做整體 golden 比較；要保存這個標示，不會將「部分 102」冒 full canvas。v2 README 的「若只跑原 P72B section」只能理解為待排的 section 覆蓋，不能據此發明不存在的原入口。

取得獨立 browser 時槽後，在上述工具建立並驗過 clean/同 S 的 source checkout，另以新的專有 runtime、feedback、profile、socket 目錄及未佔用埠執行。建議保留 19814（第一原服務）、19815（第二全新原服務）、9644（CDP），啟動前由 metadata collector 檢查，不能連到其它既有服務。

原 build：`npm run build`。原服務兩次分別為 `python3 -u geometry-web/start_local.py --port 19814` 與 `python3 -u geometry-web/start_local.py --port 19815`，各自保存完整 server stdout/stderr。兩個原 `runtime_version.py --probe` 必須成功且 repository/source 身份正確；不能只看 port 有回覆。用 `GEOMETRY_GRID_RENAME_FRESH_URL=http://127.0.0.1:19815/` 讓原 P72B reopen 走真正新 native 服務，不只 reload 原 JS context。

原 browser argv 是 `node geometry-web/cdp_test.js`，有效環境至少明列：

```text
GEOMETRY_TEST_URL=http://127.0.0.1:19814/
GEOMETRY_GRID_RENAME_FRESH_URL=http://127.0.0.1:19815/
GEOMETRY_COMPOSITION_ONLY=1
GEOMETRY_CDP_PORT=9644
GEOMETRY_CHROME=/workspace/geo261-environment/bin/google-chrome
GEOMETRY_CHROME_FLAGS=--no-sandbox
GEOMETRY_CHROME_PROFILE=<本輪專有 TEMP 目錄>/chrome-profile
GEOMETRY_FEEDBACK_DIR=<本輪專有 TEMP 目錄>/feedback
```

TEMP/TMPDIR 必須和 `os.tmpdir()` 同一已封存環境，feedback 為其專有子目錄；清掉其它原 scope flag、GEOMETRY_CDP_UPDATE_GOLDEN、NODE_OPTIONS 與 PYTHONOPTIMIZE。保存 Chrome/Node/fonts 原版本指令與 exit，保 16MiB stack。原 canvas workflow CI 35 分鐘時限不擴大；若此局部原入口非零或未完整終態，照原輸出記紅。原 P72B=50 不改、原完整世界／幾何／歷史／專案保存與新服務重開 assertions 不改，不刪自帶新建雙軸反例。

此項目前仍 UNRUN。後續執行 wrapper 需先精確記錄啟停 argv、PID 身分、環境與 SHA；只停本輪兩服務與其 bridge／Chrome。此計畫不授權刪 cache、停止其它使用中的服務，或改 source／測試／公理／決策佇列。
