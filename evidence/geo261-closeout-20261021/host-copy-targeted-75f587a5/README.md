# 75f 的 H/K 定向證據

分支 `codex/geo261-p189-host-copy-trial-20261021`，commit `75f587a5e96dbd1460cf1d9be781ca6fa06fd993`，parent `85dc4fff44ce49b27f831b21cbdcb662c863302c`。本包只收 H/v1、H/original-correction、K 與固定 top-level peer／commit 收據；後續 footprint 候選另案，未收進本包。

H 的 65 個定向測試、18 個明列控制與 4 個局部 sanitizer 案原件留在 raw/H/v1；sanitizer 只儀器化 H translation unit，K/W 未儀器化。整套 65 項中的 43 個具名 ASSERT 非零命令不能全部稱為 H 控制。K 的 36 個定向測試、26 個具名控制與真 wait 收據留在 raw/K。完整計數、來源綁定與限制見 reviews/host-copy-package-source-review.json；各組測試有重疊，不能相加當成獨立案例總數。定向收據執行時未 commit 的狀態照原文保存，local-commit.json 將來源 bytes 綁到 75f。

H/v1 的四個「原版」見證曾因 references.inc 轉接遺漏而使用錯誤基準，不可當原版驗證。獨立發現報告與原錯誤紀錄完整保留；H/original-correction 是新 out 的修正，原版四案真 0，93 個已記命令皆 0，peer 接受。沒有獨立保存的最外層 run_original 結束碼檔，不從 passed 推造頂層工具 0。修正未更改候選產品 bytes 或重跑候選；不能用修正覆寫錯誤歷史。

P-189 原件另見 ../p189-host-copy-trial-75f587a5；該輪四點綠也不能替代完整 ledger／架構／七項正式驗收。本包沒有執行產品、沒有重抽效能樣本或撤回負控制。

artifact-mapping 逐檔綁原 bytes/hash；外部 .py/.c 等保存為 0644 純文字來源快照，不新增正式工具入口。SHA256SUMS 涵蓋除自身外所有檔案。最不確定是未完成全套來源驗收與實際環境中的性能餘裕。
