# #323 雲端驗收進度

固定受驗來源：`b2445b5a270d60fdf48b07f6edddbe91266d8aa2`。後續提交只保存證據，沒有冒稱已在證據提交重跑產品。

- 2026-10-23T15:15:04.217675+00:00 — **completed-baseline**：原8stage全部終態：175ABC等價、PF3原0；36timing/4gprof保原N64綠、N32與calls紅；完整native5200pass/2fail/1具名WindowsGDI允許skip，另ledger STALE。兩test-control drift保原失敗。scheduler傳輸TOP缺口照實RECOVERY，不冒全綠。候選完全未套未測。
  下一步：依使用者階段性停止，交接已跑原件與未套候選；後續owner按root次序確認finalbase再修，原門檻不變，現在不開新測試。原始資料：`raw/completed-baseline-01.tar.gz`、`raw/completed-baseline-02.tar.gz`、`raw/completed-baseline-03.tar.gz`、`raw/completed-baseline-04.tar.gz`、`raw/completed-baseline-05.tar.gz`、`raw/completed-baseline-06.tar.gz`。
