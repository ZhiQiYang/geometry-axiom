# GEO-261 雲端驗收進度

固定受驗來源：`2bfbfa58f5522ded03996ec073e23f0ccd129b68`。後續僅證據提交不冒稱為新受驗產品 SHA。

- 2026-10-22T14:19:24.173947+00:00 — **copy-callers-and-targeted-native**：2bfbfa58＋具名dirty診斷：footprint窄讀候選N64仍2.067×、已撤回；caller診斷定位35.27GB可見memops。永久raw測試首輪65含1fail/1error，修接線後82全綠，新8負控正常0/1/0；不是新最終驗收，P189仍待修
  下一步：量測保留完整格式驗證的8-byte placement header，補公開API差分與永久測試，再凍結公開SHA重產帳本、Linux架構四檔並完整重跑。原始資料：`raw/copy-callers-and-targeted-native.raw.tar.gz`。

產品與測試紅燈先記錄分類，完成整輪後集中修正；需拍板項目另記 QUESTIONS.md。不 force push、不合併。
