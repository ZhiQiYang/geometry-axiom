# 獨立 space suite 群組完整性（#86）

`space_model_test.js` 既有真 Chromium/CDP 行為斷言與 browser exception／console error 守門全部保留。
`space_test_floor.js` 只加固定 census：每個選定群組都要正常返回，且通過斷言數嚴格等於預期、失敗數為零。
`SPACE_RESULT` 與 `result.json` 都列出 scope、各群 expected/passed/failed/completed、整體 completed 與完整性差異。
故意漏群、群內提前返回、外層提前返回或拋例外均不能回報完整成功；增加斷言也須先重新盤點。
沒有由實測生成 expected 的更新捷徑。

## 獨立靜態盤點

基底 main `a1ae53e5ce32cfbd2ab17cf6ab99ca8d4abaa77d`。
以下取自既有 `check` 呼叫、明列迴圈夾具數及 helper 呼叫；不是接受「實際跑到的數量」。

|群組|獨立盤點|預期|
|---|---|---:|
|setup|服務 release 與 capabilities 各一|2|
|space-height-library|run 的建模／保存／legacy／既有面流程 74；wallHeightEditingRegression 12；#159 libraryHistoryRegression 的 desktop／390px 各 11，迴圈後有效／過期 builder 歷史 4|112|
|projection-lifecycle|projectionLifecycleRegression 18|18|
|projection-placement|projectionPlacementRegression 14；source race 兩次各一，closeFirst 額外一；GEO-244 原圖方向、保存重開及拒絕／取消 13；正式投影方向與未確認選單同步 6|36|
|font-layout|固定 check 8；fontCheck 六次各一；header width 1382/1160/900/680/600 各一|19|
|space-flow|固定 check 21；兩個 viewport 迴圈各兩次；draft 9；inline guards 四種 action 各一，direction 額外一|39|
|timber-material|固定 check 42；六種 tamper 各一|48|
|timber-source-guards|history 前段 5；其後 source／reload／context 各一|8|
|timber-history-guard|既有 HISTORY_ONLY 前段，原提前返回仍保留|5|
|browser-health|uncaught exceptions 與 console errors 各一|2|

預設 **full-space-suite = 228**：五個 space 功能群組 224，加 setup／health 4。原 GEO-244 的 196 保留，另增方向同步 6，再增 #159 模型庫歷史回歸 26。
它原本就不含 timber-material／timber-source-guards，不新增這些執行責任。

#159 的正式回歸重用 first create 的真 native producer 模型；1400×900 與 390×844 各 11 個獨立 `check`，合計 22。逐項為原 Undo／Redo／Save DOM 身分、44px 實際 hit target 與無溢出、庫內移除的一步 history、Undo 完整模型原值、Undo 焦點保留、真 Ctrl+Y、真 Ctrl+Z、真 Tab 至 Redo、Enter 啟動及 disabled 後轉可用 Undo、再次鍵盤復原、原 Save 節點和控制不被替換。兩個 viewport 迴圈後另有單次 4 個 `check`：真「使用目前面」讀取唯一 surface 101 並輸入 raw height 3210 後，有效 builder 禁止庫內 Undo／Redo／移除與快捷鍵，保留 draft／source／model；返回畫布 Undo 撤銷原模型建立而不改 world；來源 history 過期後重新進庫仍可 Redo 且保留 raw；庫內 Redo 完整恢復 first model、world 與 raw 3210。每輪最後復原移除，末段復原建立模型的原 undo 步；後續既有 core edit 正常清除剩餘 redo，原本混合 native／metadata 的 undo 次序不變。模型完整 JSON、所有 raw 設定、來源 dump 與 native revision 同時核對。新增合計 26 檢查只屬預設 height/library 群；跨專案 lease 的延遲回覆拒絕另由獨立 guard 瀏覽器驗收，不能把此群說成已覆蓋。

所有既有 primary filter 與 HISTORY_ONLY 的範圍保持：

|filter|功能群組|含 setup／health 的斷言數|
|---|---|---:|
|SPACE_FLOW_ONLY|space-flow|43|
|SPACE_STYLE_ONLY|font-layout|23|
|PROJECTION_PLACEMENT_ONLY|projection-placement、font-layout|59|
|TIMBER_ONLY|timber-material、timber-source-guards、font-layout|79|
|TIMBER_ONLY + TIMBER_HISTORY_ONLY|timber-material、timber-history-guard、font-layout|76|
|TIMBER_GUARDS_ONLY|timber-source-guards|12|
|TIMBER_GUARDS_ONLY + TIMBER_HISTORY_ONLY|timber-history-guard|9|

partial 的 completed:true 只表示它宣告的 included 群组完成，仍明列 filters／omitted，不能當全量。
本腳本目前沒有平台 skip 分支；沒有新增自動豁免。`tests/run_all.py` 原具名平台 skip 規則維持。
手機尺寸模擬、stubbed save handle 與 TEMP download 仍不代表實體 iOS 或 OS chooser 驗證。

## 可重跑的公開反例與驗證

先以同一 exact checkout 的 native bridge／model-base 啟動專用隔離服務，設定：

```sh
export GEOMETRY_TEST_URL=http://127.0.0.1:18886/
export GEOMETRY_FEEDBACK_DIR=/tmp/geometry-86/feedback
export GEOMETRY_CHROME=/usr/bin/chromium
export GEOMETRY_CHROME_FLAGS='--no-sandbox --disable-dev-shm-usage'
export GEOMETRY_CDP_PORT=19486
node --test tests/test_space_test_floor.js tests/test_cdp_floor.js
python3 tests/space_group_counterexample.py --ref HEAD
python3 tests/space_group_counterexample.py --ref HEAD --full-omit
node geometry-web/space_model_test.js
GEOMETRY_TIMBER_ONLY=1 node geometry-web/space_model_test.js
```

負例腳本只把已提交公開 harness 放進 TEMP，移除 font 群呼叫、群內 return 或 throw；保留其他行為斷言與收尾。
結果與 log／截圖／Chrome profile 路徑會印出。它核對 helper bytes 對上指定 ref；若不符即拒絕。
在舊基底 checkout 搭配同版隔離服務，加 `--ref a1ae53e5ce32cfbd2ab17cf6ab99ca8d4abaa77d --expect-vulnerable`
可驗證原漏跑／提前返回 exit 0、原例外 exit 1；再加 `--full-omit` 可驗證完整模式也能漏一群仍綠。
修補版上述負例必 exit 1、completed:false；counterexample 驗證器本身 exit 0 代表成功證明拒絕，不能混成 suite 成功。
精確 PR head 的實際命令、exit 與 SPACE_RESULT 另附 PR 驗收紀錄。
