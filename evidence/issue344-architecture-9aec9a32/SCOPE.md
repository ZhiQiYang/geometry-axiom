# 原件範圍與讀法

本批是 S344 `9aec9a32630fc65f94c53d49e99969e546574d6e` 的完整架構驗收原流，沒有壓縮或省略已完成的子命令。`originals/` 保留正式 driver 全部原件，`outer/` 保留來源材料化、資源、stack 與正式外層，`source-publication/` 是此前單 hash commit/push；兩份 host EXEC_FINAL 另列。原命令中的絕對路徑保持原文，不改寫 execution SHA。

每個 `subcommands.json` 對應 `subcommands/NNNNNN/` 的原 request、result、stdin.bin、stdout.bin、stderr.bin。負控制的 exit 1 仍原樣保留；三條原正式 judge 的 exit 為 0/0/0。604 inputs、原 Git blob/raw/LF 閉包、三裁判及兩份 SSOT 前後核對在正式原件中。

`originals/new/` 是實際產生的四檔；同一 bytes 採入產品路徑。manifest 及 scan 本來已與這次輸出一致，因此該採用提交只變更 report、receipt 與新 evidence。四檔 sourceBaseHead 仍為 S344，後續 evidence head 不冒充執行來源。未重跑 C、native、Node strict9、Chrome、mutation ledger 或性能。

`adapter-preparation/` 保留實際 driver、差分、dry-plan 原流；dry-plan -O 的 1 屬工具入口拒絕，不是產品反證。`actual-peer/` 與其他 peer 目錄保存獨立檢查程式與報告，peer 0 不代產品 gate。所有原始外部檔案仍保留，未清除 fixtures、git objects 或其他來源。

`COPYMAP.json` 列每個選定來源及 SHA256。它不自我雜湊；publisher 原流另存於雲端及後續 publication peer。唯讀驗證可按原 map 比對 Git blob。沒有把尚未公開的 Git push 收據放進其自己的提交。
