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
|projection-close|舊 close 在新 open 讀來源中／顯示後兩個時序，各六個 check；一般取消與 Escape 各一|14|
|font-layout|固定 check 8；fontCheck 六次各一；header width 1382/1160/900/680/600 各一|19|
|space-flow|固定 check 21；兩個 viewport 迴圈各兩次；draft 9；inline guards 四種 action 各一，direction 額外一|39|
|profile-space|`profile_space_test.js` 明列 60 個唯一 case；固定 check 57，1400／690／390px 的版面 check 各一|60|
|timber-material|固定 check 42；六種 tamper 各一|48|
|timber-source-guards|history 前段 5；其後 source／reload／context 各一|8|
|timber-history-guard|既有 HISTORY_ONLY 前段，原提前返回仍保留|5|
|browser-health|uncaught exceptions 與 console errors 各一|2|

R12 加入前的 **full-space-suite = 242**：原五個 space 功能群組 224，加 projection-close 14、setup／health 4。原 228 的全部斷言及五群數量保留；新增 close 回歸不是既有正式紅燈的豁免。本次加入獨立 `profile-space` 60，預設完整集合為 **302**；原六個功能群組與 setup／health 的 242 項均不變。這是來源盤點，不表示實跑已通過。
它原本就不含 timber-material／timber-source-guards，不新增這些執行責任。

#159 的正式回歸重用 first create 的真 native producer 模型；1400×900 與 390×844 各 11 個獨立 `check`，合計 22。逐項為原 Undo／Redo／Save DOM 身分、44px 實際 hit target 與無溢出、庫內移除的一步 history、Undo 完整模型原值、Undo 焦點保留、真 Ctrl+Y、真 Ctrl+Z、真 Tab 至 Redo、Enter 啟動及 disabled 後轉可用 Undo、再次鍵盤復原、原 Save 節點和控制不被替換。兩個 viewport 迴圈後另有單次 4 個 `check`：真「使用目前面」讀取唯一 surface 101 並輸入 raw height 3210 後，有效 builder 禁止庫內 Undo／Redo／移除與快捷鍵，保留 draft／source／model；返回畫布 Undo 撤銷原模型建立而不改 world；來源 history 過期後重新進庫仍可 Redo 且保留 raw；庫內 Redo 完整恢復 first model、world 與 raw 3210。每輪最後復原移除，末段復原建立模型的原 undo 步；後續既有 core edit 正常清除剩餘 redo，原本混合 native／metadata 的 undo 次序不變。模型完整 JSON、所有 raw 設定、來源 dump 與 native revision 同時核對。新增合計 26 檢查只屬預設 height/library 群；跨專案 lease 的延遲回覆拒絕另由獨立 guard 瀏覽器驗收，不能把此群說成已覆蓋。

所有既有 primary filter 與 HISTORY_ONLY 的範圍保持：

|filter|功能群組|含 setup／health 的斷言數|
|---|---|---:|
|SPACE_FLOW_ONLY|space-flow|43|
|SPACE_STYLE_ONLY|font-layout|23|
|PROJECTION_PLACEMENT_ONLY|projection-placement、font-layout|59|
|PROJECTION_CLOSE_ONLY|projection-close|18|
|SPACE_PROFILE_ONLY|profile-space|64|
|TIMBER_ONLY|timber-material、timber-source-guards、font-layout|79|
|TIMBER_ONLY + TIMBER_HISTORY_ONLY|timber-material、timber-history-guard、font-layout|76|
|TIMBER_GUARDS_ONLY|timber-source-guards|12|
|TIMBER_GUARDS_ONLY + TIMBER_HISTORY_ONLY|timber-history-guard|9|

partial 的 completed:true 只表示它宣告的 included 群组完成，仍明列 filters／omitted，不能當全量。
本腳本目前沒有平台 skip 分支；沒有新增自動豁免。`tests/run_all.py` 原具名平台 skip 規則維持。
手機尺寸模擬、stubbed save handle 與 TEMP download 仍不代表實體 iOS 或 OS chooser 驗證。

## R12／Q38j 的一般入口與證據範圍

補丁基底 `11eddfdb4d7b1f76aedfe001e084a3840790bedc`。`profile-space` 從一般新增物件選單建立斷面、三個構件及拉伸件，再由物件清單進面、面屬性的「建立空間」選取來源。原生指令只準備既有平面與角材；新增的斷面、構件、拉伸件、逐條選擇、確認、歷史、方案與檔案操作均走產品控制。

60 項涵蓋 Q01 精確世界範圍與材料量、未定位排除、不預勾選、共同角材／拉伸件開關、不扣交疊提示、三種視窗尺寸、取消零寫入、一次確認一步歷史、Undo／Redo、保存空間頂面取值、F1b 明選與整筆來源快照更新、空清單移除、改高保留快照、方案保存、第 20 版專案下載與重新載入，以及真來源讀取和預覽延後回覆的過期守門。冷開測試先用一般入口建立空專案、重載頁面，再用一般「開啟專案」檔案控制讀入真下載檔；不宣稱服務重啟、原生 OS 選檔器、實體裝置或 L4 人工驗收。

`tests/test_profile_space_browser_contract.js` 只核對頁內程式語法、具名 case 清單及新舊群組盤點。`tests/test_r12_browser_evidence.py` 核對證據分類器與凍結來源完整性。這兩個純 Node／Python gate 都不能代替真瀏覽器成功收據。

```sh
node --test tests/test_space_test_floor.js tests/test_profile_space_browser_contract.js
python3 -m unittest discover -s tests -p test_r12_browser_evidence.py
python3 tests/r12_browser_evidence.py --preflight
python3 tests/r12_browser_evidence.py --out /tmp/r12-profile-browser-evidence --withdrawals
```

最後一行須使用未存在、位於 repo 之外的輸出目錄，並以 `GEOMETRY_CHROME` 指定已安裝的瀏覽器。runner 凍結來源清單與每檔 bytes／SHA-256，用原 `tests/binaries.py` 重建原生程式，每次執行各自啟動服務與瀏覽器，核對前後 `/runtime`。它不新增 sandbox 旗標、不修改既有時限；先取得完整 64 項 partial 綠燈，才逐一撤回六個具名接線並要求對應斷言紅、還原後完整綠燈。啟動失敗、缺少報告、逾時、非具名失敗或來源過期一律阻擋，不能記作 killed 或 0／1／0。

若 checkout 將 `evidence/`、`tests/evidence/` 或 `tests/release-evidence/` 歷史收據設為 sparse，缺少的 skip-worktree 項目以完整 index blob 清單另存 `sparse-archives.json`，不列入已複製來源。這三個目錄不是本群 runtime、native registry 或 browser harness 的來源。其他缺檔，包括被設為 sparse 的應用或測試程式，仍在啟動前拒絕；不以略過缺檔冒稱完整副本。

本群未新增 canvas 正常段，`geometry-web/cdp_sections.golden.json` 與 `geometry-web/canvas_shards.json` 保持原件；沒有手填 golden 或從失敗輸出重設段計數。partial 成功仍不能代替原完整 space suite 與完整 canvas 執行；真瀏覽器的執行狀態及產物需在交付證據另外列明。

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

## PR #197 投影 close 競態

2026-10-12 三版本診斷在舊 #202 的 placement 後段抓到可信 close 延後到下一次 open 才送达：原 harness 680（插樁 682）的 top 重開，不是 #199 原 678、#197 原 401 或 #202 原 387 的已重現根因。原始正式紅燈保留。

產品修正只在 `app.js` 的 FaceProjection 閉包。取消、Escape、套用及前往放置都同步結束自己持有的 session；只推進同一 generation 的 serial，不讓晚到的 native close 通知清除新 session。既有來源／history／project／API 新鮮度检查不變。無新 UI 入口。

`projection_close_probe.js` 只供測試：延後呼叫 app 實際登記的 close listener，保留瀏覽器原 event 的 isTrusted／timeStamp；不派送合成 close，不編造 API 資料，不修改產品閉包。第一個時序在真 surfaces 回覆讀取暫停時釋放舊 close，第二個在新 dialog 已顯示後釋放。實際輸入仍走 CDP pointer／keyboard。移除 listener 的修正版 callbackCount 可以為零，仍須觀測到真的 native close。結果另存 `projection-close-proof.json`，明列受控時序，不宣稱自然重現原首紅。

純 Node 14 題執行同一產品閉包；DOM／API 是有限夾具，不能代替真瀏覽器。修前 6 過／8 敗；修後 14 過，六個針對性突變均斷言紅、逐次還原 14 過。最初 13 題的 6 過／7 敗保留；第一版證明腳本在 M2 的 CRLF 錨點失敗，沒有算作偵測成功，第二版修正換行處理後完成。新 14 題依該完整單檔實跑數登記於原生 runner，不改其他 suite 的預期數量。本段提交時真瀏覽器及修正版正式七 job 尚待執行。
