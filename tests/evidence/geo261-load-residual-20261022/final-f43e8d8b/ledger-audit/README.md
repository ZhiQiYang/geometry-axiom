# #323 帳本完整重產收據封存

受驗來源 `b823903e44aea091b70fd2f45b74dff6229776dc`。此目錄只整理既有已完成檔案，沒有重跑產品、測試或編譯，也沒有修改 Git 工作樹。

初次 `--check` 原退出碼 1；重產中的 precheck/full-ledger/checkafter 為 1/0/0，來源前後皆同 S 且乾淨。78 筆含 75 筆同 S execution：70 killed、4 equivalent、M20 crashed；另 3 retired。M20 不列 killed。W vocabulary 是唯讀完整聯集核對，不代替架構三裁判。

`SUMMARY.json` 是數量及結果索引；`RAW_PATHS.json` 保原路徑、指令 streams 核對、bridge streams 與工具；`archives/*.tar.gz` 內含完整 inner/outer 指令、原 stdout/stderr、環境、收據、前後來源指紋、新舊 ledger、bridge build/tests 原 logs、fingerprints 及來源閉包。每包小於 95 MiB；`inventories/*.members.json` 的每個 member 路徑、bytes、SHA256 已從實際壓縮包逐個讀回核對。`SHA256SUMS` 核本目錄所有出版檔（自身除外）。

原 `tests/mutate.py` 對 core 內層 compile/test 未落盤完整 streams：attempt 只留結構化 result 和原 stdout/stderr SHA。這些原 ledger 資料及完整 full-ledger 正式命令 stdout/stderr 全保留；沒有憑雜湊反推或偽造未捕獲的原 stream。18 個 bridge 的 baseline/mutant/restored build/test streams 全數保留。

原工具會刪除 core 暫存 C，bridge 亦恢復原來源。因此 `reconstructed-not-captured/` 明確是此次由原工具純轉換／原字節 replace 重建的 57 core 和 18 bridge variants，不聲稱當時已留存。core 逐檔比對當次 fingerprint.generated_source_sha256；bridge 比對當次 mutant sidecar.files 的原 LF source hash。完整證明列 `RECONSTRUCTED.json`。

`EXCLUDED.json` 逐檔記錄可重建 source clone（含 .git）、ELF 和 object 的原路徑、大小、SHA 與 metadata；來源閉包與原工具另行保留。所有原檔仍在原位，沒有刪除。
