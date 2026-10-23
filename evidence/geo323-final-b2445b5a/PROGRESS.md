# #323 雲端驗收進度

固定受驗來源：`b2445b5a270d60fdf48b07f6edddbe91266d8aa2`。後續提交只保存證據，沒有冒稱已在證據提交重跑產品。

- 2026-10-23T15:15:04.217675+00:00 — **completed-baseline**：原8stage全部終態：175ABC等價、PF3原0；36timing/4gprof保原N64綠、N32與calls紅；完整native5200pass/2fail/1具名WindowsGDI允許skip，另ledger STALE。兩test-control drift保原失敗。scheduler傳輸TOP缺口照實RECOVERY，不冒全綠。候選完全未套未測。
  下一步：依使用者階段性停止，交接已跑原件與未套候選；後續owner按root次序確認finalbase再修，原門檻不變，現在不開新測試。原始資料：`raw/completed-baseline-01.tar.gz`、`raw/completed-baseline-02.tar.gz`、`raw/completed-baseline-03.tar.gz`、`raw/completed-baseline-04.tar.gz`、`raw/completed-baseline-05.tar.gz`、`raw/completed-baseline-06.tar.gz`。

- 2026-10-23 15:18 UTC：本輪已依使用者要求停止新實作／測試。原 S 仍是 b2445b5a，產品、tests、公理、決策與原判官均未再改動；未套四檔候選。全部原八stage及三套診斷已封，正式native為5200pass/2fail/1具名WindowsGDI允許skip，帳本closure另STALE；N64綠、N32/calls紅保真。
- 第一封存 E1 `0d5b4043bea5cc1e1a6a427075760bc6e30aaa8e` 已一般push。六包共229482052bytes、14138members；原封存器逐member roundtrip。producer另核六個Git blobs逐bytes/hash同原包，7036個原streams／命令metadata全涵蓋，53個可重建項明列，原stdout/stderr排除0。205298659bytes巨型stdout以四個獨立gzip ranges與精確mapping無損保留，原檔未刪；完整串接hash仍778f023db9aba56fa84bd85b8ff32c016aec5bb0d9470b445653b0bd3989e174。producer檢查不冒充獨立公開包peer。
- 原scheduler UI傳輸後缺TOP RESULT／最外console exit未知，PID已殭屍且無活scheduler；原八stage source守門／完整輸出／實退出已存，未重跑或補造成功。詳見RECOVERY.json。
- 接手入口：HANDOFF.md、BASELINE_CURRENT_SUMMARY.json、QUESTIONS.md、unapplied-candidate/。新控制0/1/0、修後三套、新final完整v3與帳本／架構刷新均未開始；本輪沒有323 browser新結果。停止後不自動續跑。

- 出版收尾的第一次全cached whitespace check原exit2，原因是原GitHub stderr行尾空白與原unified patch的空白context；原件與輸出照存，未trim任何raw或改patch hash。續封僅對新寫PROGRESS/HANDOFF/QUESTIONS做排版gate，不是產品測試assert或數值放寬。
