# F9 native 完整原件核對

審查 2208 項，0 個證據錯誤；native 原 exit 1，CI35 gate 0。230 suite、5329 計數：5327 pass／1 fail／1 具名 Windows GDI skip。

唯一失敗：`Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，斷言 `I24 submission policy must not change K files`，實際差異 `geometry-core/kernel/source.c`。

- 本 peer exit 0 表示收據完整且紅燈分類可信；native 正式結果仍為 1，不標 READY。
- 未重新執行任何 suite／產品或改來源。未重新讀 ELF payload；完整 cache/sidecar 封包由獨立 collector 接手。
- 原 per-suite 內部 stdout/stderr 是原 run_all 合併保存方式；沒有冒稱原未另存的 capture_output 管線存在。
- exit-code-only 原件沒有 test 級計數，保留原 ok／mutation freshness exit0，不補造斷言數。
- 必要 browser/owner 整合皆由原總表列為另驗；此 native 結果不外推其通過。
- 唯一紅是固定整合基底的 K 路徑禁止變更 assertion；是否為舊基底範圍不適用列車需另核授權／來源歷史，不能據本收據免除或放寬。
