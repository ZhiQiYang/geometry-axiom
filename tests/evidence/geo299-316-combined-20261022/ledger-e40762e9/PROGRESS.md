# #299+#316 整份突變帳本與追溯同步

本輪帳本來源 S：`e40762e99b078335d78c65a3a2682a0c9ab875d0`。原整份 `python3 tests/mutate.py` 真退出 2，外層真退出 1：67 個 core execution 已完成，但 fresh bridge checkout 因雲端 workspace ENOSPC 受阻；原 checkafter 與 source_after 錄製未能開始，原缺項保留。另行只讀 HEAD／status／diff 證明來源仍是 S 且乾淨，沒有補寫原收據。

修好容量後，同 S 以全新 private cache 只環境重跑原 18 個 bridge IDs，原命令真 0；其後原 strict `python3 tests/mutate.py --check` 真 0，環境重試外層 subreaper 真 0。新 scratch 僅 sparse 排除已公開 evidence，其 C include closure、原完整 Python／scene oracle hashes、原工具 bytes 與原 RESTORED 方法名單均核同。原 67 個 core 紀錄逐值保留，沒有改 execution SHA／挑綠重跑；這是兩個環境 phase 完成整份重產，不能稱單次原 full 命令退出 0。

帳本 88 筆，85 筆實跑 `execution.head` 全為 S；原 verdict 分布為 `{'killed': 80, 'equivalent': 4, 'crashed': 1, 'retired': 3}`，M20 crashed 與 killed 分欄。新 M89–M98 的原 verdict／why／killed_by 完整見 SUMMARY.json；未將保存帳本的提交冒成其實跑來源。

將原 ledger bytes 安裝後，僅以原同步器重建唯一正典，再跑原 `--check`、完整 reader suite 與安裝後原 `mutate.py --check`，各真 0；是否改變 HTML bytes 見 SUMMARY.json。公理層、決策佇列、BACKLOG bytes 全保留。

封包保存原 primary 指令、退出碼、完整 stdout／stderr、安全環境、SHA、原工具、collector 順序前置失敗、追溯生成 Git patch，以及三個已公開乾淨舊比較 clone 的雲端容量修復完整命令／guard／每檔 hash／空間前後收據；每個 member 已逐 bytes／SHA256 核同。完整暫存 build／test raw 已放入 complete-ledger-raw/；原 core 內層未落盤 streams 仍如實明列，不冒稱已保存。

下一步：一般推送帳本保存提交 L；在 L 以 Linux 重產架構 manifest／scan／report／receipt 四檔及三條原裁判，然後固定正式驗收 F。

## 完整原 raw 封存已完成

`complete-ledger-raw/` 已封 1195 members／53359955 原 bytes，包含全部原 bridge build／test stdout／stderr、fingerprints／sidecars、原 67 個 core JSON 每段 bytes 核同，以及固定 S 的 184 個 C closure 與 397 個原 flat Python／根 scene inputs。78 個 top-level streams、216 個 bridge stream references 已核原 hashes。

85 份 variants 僅由原純 helper 重建並匹配原 fingerprint／sidecar，明標 reconstructed-not-captured。clone 子樹未遍歷／未 hash，完整排除項照列；其餘 ELF／objects 逐檔 hash。每包小於95 MiB，全部 member 已自實際封包逐 bytes／SHA256 核同。原 full2／outer1與缺 checkafter／source_after、collector preflight1、同 S 環境 retry0／strictcheck0 分欄保留。

L 首次 publisher 在任何 commit/push 前因主工作樹 sparse 定義排除 tests/evidence 而於原 git add 退出1。原收據已保 publication-first-sparse-attempt/；只撤我方兩個暫存 index entries，工作檔 bytes不變，再以 Git 原 --sparse 精確加入本目錄。沒有 force-add、force-push、merge 或改忽略規則以外的產品判準。
