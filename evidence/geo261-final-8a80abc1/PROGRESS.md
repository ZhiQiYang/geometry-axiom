# GEO-261 雲端驗收進度

固定受驗來源：`8a80abc1402b0c4c394969025c93a6019b4bb91d`。後續僅證據提交不冒稱為新受驗產品 SHA。

- 2026-10-22T17:32:37.248516+00:00 — **mutation-freshness-after-reader**：P2 canonical HTML-only修復後原mutation --check真退出0，78=70killed/1crashed/4equivalent/3retired，0stale；C/所有test來源不變。既有全帳本execution P與artifact L仍有效，沒有偽改head或不必要重產
  下一步：在同乾淨P2重產HTML-only架構四檔、嚴格審三count並固定F，原完整七項與專項全部重跑。原始資料：`raw/mutation-freshness-after-reader.raw.tar.gz`。

- 2026-10-22T17:39:31.997952+00:00 — **architecture-html-refresh**：Linux 四檔重產完成；原架構三裁判退出碼皆 0。唯一輸入變更是正典閱讀器 I11 trace，manifest 與 scan 逐位元組不變；601/333/796、零診斷。這是 P2 準備收據，最終 F 尚待固定並完整重跑。
  下一步：安裝已重產四檔，採用嚴格核對的三筆套件數量後固定 F；完整重跑七項與專項。原始資料：`raw/architecture-html-refresh.raw.tar.gz`。

- 2026-10-22T17:40:18.869272+00:00 — **census-count-proposal**：完整 A census 的紅燈原樣保留；三個新增回歸套件實測 9/9、19/19、19/19。兩個純 JSON 核對命令皆 0，只提案既有 count 的 7→9、17→19、15→19；不採舊 unit 正規化、不刪測試、不降低斷言。P2 閱讀器修復後 51 項原裁判已綠；最終 F 仍須嚴格完整 native。
  下一步：只安裝三筆 count 差分並正常推送固定 F，開始同 F 的完整七項與專項。原始資料：`raw/census-count-proposal.raw.tar.gz`。

產品與測試紅燈先記錄分類，完成整輪後集中修正；需拍板項目另記 QUESTIONS.md。不 force push、不合併。
