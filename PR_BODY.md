oracle正式驗收固定產品F `3d681636902371ecc528b20f51eea33e272581c9`；本分支只公開精確執行準備，**八phase全部未執行**。

| 唯一 current state | SHA／原exit | 範圍 |
|---|---|---|
| 產品source F | `3d681636902371ecc528b20f51eea33e272581c9` | 原oracle/probe輸入85檔與F13 mode/blob逐筆相同，仍須同F重跑 |
| evidence head | `6c2a27171033023c277ba5205129bdffa08987d3` | 自有準備prefix，沒有產品變更 |
| Git/AST/hash準備 | 0 | 68 tracked fixture/scenes；AST60方法，尚非Ran60 |
| 獨立checkout／clone／build | 未執行 | root給slot後才建立REQUEST所列tiny sparse checkout |
| oracle quick | 未跑 | 原selftest --quick，不write-expected |
| 完整probe unittest | 未跑 | 原test_gen_scenes.py -v，實際數須等於原宣告並無skip |
| C4 baseline/撤回/還原 | 未跑 | 原判官預期0/1/0，具名bad8/0/8 |
| probe baseline/撤回/還原 | 未跑 | 原單方法預期0/1/0，具名正常AssertionError2!=1 |
| 對抗審查 | 計畫80344609靜審已完成，F3d binding待覆核 | 不冒動態通過 |
| 全域mutation ledger | 本子項未產 | root在共同最終SHA統一處理 |

完整future argv/獨立checkout步驟/85檔SHA256/原Git streams在 `evidence/geo288-oracle-preparation-3d681636/`。driver原hash cfea72a0、capture c387、outer68256d90不改；自己持R3、16MiB stack、原assert/完整streams/時限，紅仍收齊，不以crash/skip冒kill。等待grid/native＋P52窗口後的root時槽，不加Chrome/Node/編譯裁判。此八phase不取代七workflow、歷史159source mutants或真正native run_probe.sh全場。

最不確定的是尚未執行的quick耗時與原反證結果。沒有force push、沒有合併PR、沒有改公理或決策佇列。
