# 已知晚回覆與 390px 入口：限定交付

本包接續 [#177](https://github.com/ZhiQiYang/geometry-axiom/pull/177) draft 的第一批 edge 修復，保留原始失敗與後續通過。#177 的 base 是 #176 分支 `codex/integration-closeout-20261008-r2`，依賴 #169 → #176 → #177；沒有合併、部署或審查留言。

## 同一凍結候選的原再現

最終受測候選 `cb8d4e70d1659458017658d52139e2843cc5ba72` 前後工作樹乾淨；以下原 probe 都在 1400px 與 390px 執行，退出碼 0、completed true。每組獨立記錄，不相加成完整驗收。原 probe 收據：[replacement](rounds/final-cb8d4e7-replacement/receipt.public.json)、[Cross-B](rounds/final-cb8d4e7-cross-b/receipt.public.json)、[held-bhit](rounds/final-cb8d4e7-held-bhit/receipt.public.json)、[held-proj](rounds/final-cb8d4e7-held-proj/receipt.public.json)、[card-r3](rounds/final-cb8d4e7-card-r3/receipt.public.json)。

| 原 probe | 乾淨基底 `9029a8f6bc00a9ff8de1d2b0deb844f331e032e3` | 乾淨最終 `cb8d4e70d1659458017658d52139e2843cc5ba72` |
|---|---|---|
| replacement 拒絕殘值 | 12 pass / 4 fail，exit 1 | 16 pass / 0 fail |
| Cross-B | 4 pass / 4 fail，exit 1 | 8 pass / 0 fail |
| held-bhit | 0 pass / 2 fail，exit 1 | 2 pass / 0 fail |
| held-proj 既有回歸 | 2 pass / 0 fail，exit 0 | 2 pass / 0 fail |
| C2/C4 原卡片入口／樣式流程 | 3 pass / 1 fail，exit 1、completed false | 4 pass / 0 fail |

基底 Cross-B 的缺陷是 A 的成功晚回重啟 B 編輯，token `2 → 3`；原案例 handles `5 → 5`、World 不變，沒有擴大宣稱資料污染。修後，B 的操作 token、可見手把和模型狀態不變，World 只包含已提交的預期 A 變更；原 World dumps 在每輪 `world/` 逐 byte 保留，可核 before、gate、B-ready、release、expected。

基底 held-bhit 在 A 已放開／切到 B 後，A 的舊命中回覆清掉 B 手把並復活 `editDrag`。修後所有 gesture 的退休先於等待回覆，回覆必須仍屬同一個工作區、編輯世代與存活 pointer。held-proj 保留既有 `5083a456b1caff33fbc56c5fa10927582432a283` 回歸，沒有重修。

基底 390px 空間卡片第一次選取縮短畫布，第二次同座標命中 `#btnZoom`，原 slots 流程逾時；失敗與 completed false 保留。修後 mobile Inspector 使用覆蓋位置，畫布座標保持，正常雙擊進入工作區。原始 pointer／dblclick／幾何觀測保留在 card 各輪 `entry/`；導覽後的最終 click/dblclick 可能重新指向 BODY，判準以兩次 pointerdown 和最後工作區狀態為準，沒有猜測後續事件的 target。

## 新輸入、新工作區與新手勢控制

中間 `1d016a56c7d765d693ffbd6e18cc93ff335c8275` 的原 Cross-B 8/0 及 replacement 16/0 各自保留。原 replacement 確认較新同欄位／替換欄位輸入 `5151`、兄弟邊草稿 `4242` 以及合法成功 `4200`，拒絕後 World 不變。

正式 20 案補測包含同 edit 的 pointer-up、A bhit 晚回時仍在進行的 B 手勢、A 成功晚回時 B drag／hole 草稿、pointercancel、lost capture、舊 pointer-up 提交回覆時新的同編輯手勢，以及 Zoom 正常單擊。1400px 與 390px 均執行，失敗輪和後續通過輪獨立保留：

- clean `168fc94382702815535333672ce59f1fa8c4b69d`：16 pass / 4 fail、exit 1、completed false。兩個 Zoom 為測試腳本 SyntaxError；兩個 lostcapture 在未先建立實際 capture 的前提下逾時。沒有把此輪報為 20 通過。
- clean `b9587960de2c5b29993e7433a51447015058e352`：20 pass / 0 fail、exit 0、completed true。這次只修 Zoom 測試語法與 capture 前提，產品 app 與 168fc 相同；原 oracle 沒有放寬。兩版實際執行 Python／instrumentation 原件及雜湊在各輪 `source/`。

同一 clean 最終候選 cb8d4e7 又跑正式 [20 案新手勢控制](rounds/final-cb8d4e7-formal20/receipt.public.json) 20/0、completed true、exit 0，與 [EDGE38](rounds/final-cb8d4e7-formal38/receipt.public.json) 38/0、completed true、exit 0。實際受測 SHA 均是 `cb8d4e70d1659458017658d52139e2843cc5ba72`，沒有將 b958 或 992e 的舊通過改標。正式 EDGE 自行建立服務，actualFormalNativeBindings 是實際私有測試服務；外部 19176 是 orchestration label。

native World 仍使用完整 dumps 與獨立預期模型比對；B 手勢可继续移動并正式提交，不能只由 token 穩定或靜止手把推得通過。capture loss 透過既有 DOM API 注入；pointercancel 使用 CDP touchCancel 發出 UA 事件；這些不是實體觸控裝置驗收。

## 原件、公開投影與來源

[manifest.json](manifest.json) 按輪次列出完整受測 SHA、dirty、開始／結束時間、來源/runtime/native 身分、執行檔與腳本 SHA-256、命令、退出碼、原始 log/result 路徑標籤與原件雜湊。每輪 `receipt.public.json` 留下實際 live bridge 直屬 PID、parent、binary SHA-256，不只依靠 `/runtime`。

沒有私人路徑的 log/results 逐 byte 公開；含機器／feedback 路徑者明示 `publicProjection`，只替換路徑，原件完整保留在雲端 scratch，大小與原件 SHA-256 不變。私人 feedback、圖片、trace/profile、native binary/sidecar、queue DB／事件／owner thread 沒有收入 Git。所有 World dumps 是本包合成 fixture。

`probe/provenance.public.json` 記錄 #176 原再現來源、原始与实际执行脚本雜湊、函式／oracle 同一性。公開重播副本只將機器根目錄換為 `GEOMETRY_EVIDENCE_REPO` 或目前目錄；需另給 `--bridge`，並明示公開副本不是本輪實際執行檔。不要把發布副本雜湊填回舊收據。

## 範圍與下一步

這些是合成 API fixture 的限定真瀏覽器欄位／正常 pointer 操作，沒有 force click、無限重試或削弱斷言。它們不等於完整 CDP／完整 Space、Windows/GDI、golden、真手機/IME/OS chooser 驗收。

歷史完整 CDP `2207/0/0` 仍綁乾淨 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；9029 是後續文件／證據提交。#173 原完整 Windows 仍 1692 pass / 2 fail、exit 1、completed false，原件雲端未核收；P74/P75 不相加，未宣稱本輪核過 golden。

安全 Resume、#123 既定 UI、#54 單房操作成本、兩處過期 INTEGRATION-GATES 文件及現有工作管理資料核對由 root 接續。缺少的私人 queue 原件保持 unknown，不另造空資料庫。新公理、跨專案未定政策、額外費用或 #87 多房擴張留決策點。
