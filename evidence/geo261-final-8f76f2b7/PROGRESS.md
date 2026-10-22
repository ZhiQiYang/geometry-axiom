# GEO-261 雲端驗收進度

固定受驗來源：`8f76f2b7d6f669670e5834310bfc26495b4a4aa6`。後續僅證據提交不冒稱為新受驗產品 SHA。

- 2026-10-22T19:55:53.075131+00:00 — **fixed-source-preparation**：新受驗 SHA 已公開；runtime省工只重用已驗相同路徑集合的排序／Path，完整雙枚舉與逐檔讀取保留；P3 帳本 --check 0／0 stale、原 runtime 31／0，Linux架構四檔已重產、原三裁判 0；本輪正式完整清單尚待執行
  下一步：在隔離乾淨同 SHA 依序重跑 native、六個 browser、全部專項並逐項正常推送進度；舊輪原紅不改寫。原始資料：`raw/fixed-source-preparation.raw.tar.gz`。

- 2026-10-22T19:58:12.497277+00:00 — **cloud-space-maintenance**：環境維護：舊輪冷存首試因 hardlink 保護退出 1、原件未刪；支援僅目錄內 hardlink 拓樸後真退出 0；104478 regular files／8380951355 bytes、884 組 hardlinks 逐檔全 hash／metadata／pathset 核同後保留原路徑 symlink；正式產品或判準未改
  下一步：持續新 SHA 正式驗收；逐項保留實際原退出及完整輸出。原始資料：`raw/cloud-space-maintenance.raw.tar.gz`。

- 2026-10-22T20:07:32.801537+00:00 — **controlled-proof-preparation**：同新 SHA 的 P73 controlled callback 與 P52 runtime 撤回／恢復工具已綁定並完成靜態準備；原測試、predicate、量測 protocol 與數值 gate 未改；尚未執行任何本輪額外自證，不預填綠燈
  下一步：等待本輪正式清單收齊，再依同 SHA 正式 baseline 串行執行，保留所有實際退出碼。原始資料：`raw/controlled-proof-preparation.raw.tar.gz`。

產品與測試紅燈先記錄分類，完成整輪後集中修正；需拍板項目另記 QUESTIONS.md。不 force push、不合併。
