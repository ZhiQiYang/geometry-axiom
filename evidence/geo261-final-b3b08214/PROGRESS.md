# GEO-261 雲端驗收進度

固定受驗來源：`b3b08214b27d4468ef75aeeb48bd02f8893cd86b`。後續僅證據提交不冒稱為新受驗產品 SHA。

- 2026-10-22T14:23:26.227132+00:00 — **placement-header-candidate**：b3b08214＋明確dirty patch的候選診斷：build=0，36筆交錯皆ok，N16/32/48/64 candidate/main分別0.9963/1.1482/1.6197/1.8049，原2×判準四點綠；old是上一候選而非正式base，所以仍不是最終P189驗收
  下一步：完成新header公開API等價與具名突變控制，凍結並推送產品SHA，整份重產帳本、Linux架構四檔與完整census，然後在公開最終SHA完整重跑。原始資料：`raw/placement-header-candidate.raw.tar.gz`。

產品與測試紅燈先記錄分類，完成整輪後集中修正；需拍板項目另記 QUESTIONS.md。不 force push、不合併。
