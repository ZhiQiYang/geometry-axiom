# GEO-261 雲端驗收進度

固定受驗來源：`b6646d10751a0d85a2f03f5d24fbe1073cb78980`。後續僅證據提交不冒稱為新受驗產品 SHA。

- 2026-10-22T15:32:50.015029+00:00 — **preseal-full-ledger**：P=b6646d10751a0d85a2f03f5d24fbe1073cb78980 整份帳本重產：原 mutation --check/full/--check 退出 1/0/0；78 筆、75 execution 全綁 P（core57＋bridge18，retired3）；獨立 provenance audit 通過，分類 {"crashed": 1, "equivalent": 4, "killed": 70, "retired": 3}。這是帳本產物準備收據，尚非最終 F 正式驗收。
  下一步：root 另行將已封存 after 帳本安裝到整合分支，以英文訊息單獨 commit 並一般 push 為 L；再於 L 重產 Linux 架構四檔、於 A 跑完整 census，固定 F 後跑完整正式清單。原始資料：`raw/preseal-full-ledger.raw.tar.gz`。

產品與測試紅燈先記錄分類，完成整輪後集中修正；需拍板項目另記 QUESTIONS.md。不 force push、不合併。
