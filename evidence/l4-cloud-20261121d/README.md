# R22 單房輪廓、R19 柱旁壁邊材的 L4 核對

2026-11-21 在 main `2562aee65c9f21a9ffdfd684100102d764bc2eb4` 上操作真 App。R22 原已核對向量 PDF 點取，本輪補走框選、人工修正、影像來源及分隔重取。R19 首次在 App 以真柱投影和成組放置走完閱讀 A 的一種接法。

| 需求 | 已走的操作與結果 | 層級 |
|---|---|---|
| [R22 的 105 張逐步截圖、結果與重現腳本](main-2562aee6/R22/README.md) | 匯入並校準向量 PDF，框選取得 1960 × 1160 mm 內緣。人工修正凹口及邊長後能確認。匯入 PNG 到新描繪面，在連通兩房的門洞畫分隔線後，重取只包含目標房間。兩種來源均確認寫入，並從 UI 復原、重做。 | L4 → L4，擴大已核範圍 |
| [R19 的 13 張逐步截圖、結果與重現腳本](main-2562aee6/R19/README.md) | 建立六面盒及貼角 RC 柱，將柱投影套用到天花面，得到 13 mm 牆階。成組預覽兩支各長 500 mm、寬 27 mm 的壁邊材，端面木材接觸 14 mm。確認後同時出現，一次復原同時移除，重做回復兩支。 | L3 → L4，限這個閱讀 A 場景 |

**R22 的復原提示有誤。** 在 PDF 或 PNG 來源核對外環並確認後，按一次復原。預期提示隨外環回到未核對狀態。實際上，外環與核對狀態已還原，右欄仍寫「已確認來源輪廓，可復原／重做及保存專案。」同一個畫面的下方則寫「尚未依此來源核對輪廓」。[PNG 復原畫面](main-2562aee6/R22/png/27-undo-result.jpg)

R22 也留有套用到既有面的拒絕案例。凹口切到現有角材的擋面時，App 會擋下確認。PNG 分隔選取成功後，若替換範例原本有角材的面，該角材會出現三段可能跨距，App 同樣保留原面。在新描繪面可以確認同一個 PNG 候選。[既有面的連動診斷](main-2562aee6/R22/png-existing-face/result.json)

## 執行環境

兩條路徑均在 Windows 本機、1400 × 900、Chrome 157、Node 24.15.0 執行。開工先用 headless Chrome 的 CDP 傳送滑鼠事件，核取方塊由未勾選變為勾選。R19 在 headless 分頁操作。R22 的 headless 分頁未出現可用鍵盤操作的系統選檔框，因此在獨立 Windows 桌面執行有頭 Chrome，從 App 點選匯入，向瀏覽器的原生「開啟」視窗鍵入實體檔案路徑並按 Enter。兩種 Chrome 都先準備設定檔，啟動前後帳戶密碼錯誤計數均為 0。

服務先在 Git Bash 設定 `ulimit -s 16384`、`LANG=C.UTF-8` 和各自獨立的 `GEOMETRY_FEEDBACK_DIR`，再啟動 `geometry-web/serve.py`。本機無 WSL 發行版，原生執行檔用 MSVC 從上述 main 編譯，直接讀 PE 標頭核實三支程式的 stack reserve 各為 16 MiB。每條路徑都先通過 `geometry-web/runtime_version.py --probe`。執行環境版本為 `c1f26294660703c72b0475cdee39f09cec4035ae74143bfb48c7ce5af42e1544`。

| 服務 | 探針 | 用途 |
|---|---|---|
| 18851 | [fresh: true](main-2562aee6/environment/probe-18851.json) | R22 向量 PDF 與 PNG |
| 18852 | [fresh: true](main-2562aee6/environment/probe-18852.json) | R19 首次嘗試。測試登錄表的 MSVC 參數取消了 `_WIN32`，產生預覽候選碼時走到 `/dev/urandom`，因而受阻。 |
| 18854 | [fresh: true](main-2562aee6/environment/probe-18854.json) | R19 正式走查。同一份 bridge 原始碼保留 `_WIN32`，走 Windows 的 `rand_s`。完整編譯命令、原始檔與執行檔的雜湊見[建置收據](main-2562aee6/environment/win32-target/bridge-build-raw-files.json)。 |

產品操作都透過畫面上的控制項完成。腳本讀取畫面文字、前端狀態與座標，R19 也讀取點按預覽時 App 自己收到的候選結果。兩項正式結果、額外拒絕案例與截圖的檔案雜湊以原始位元組計算。在本目錄執行 `sha256sum -c SHA256SUMS` 可逐檔核對。

本輪涵蓋的影像來源為一份 PNG。390 px、實體觸控、其他影像格式、其他柱／牆配置，以及本輪新增路徑保存後的冷開均未核對。使用者驗收（L5）待使用者確認。操作方法參考 [PR #436](https://github.com/ZhiQiYang/geometry-axiom/pull/436)。
