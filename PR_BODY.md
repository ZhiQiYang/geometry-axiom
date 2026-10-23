固定產品 F `3d681636902371ecc528b20f51eea33e272581c9` 的 oracle 原八階段已真終態：**符合全部原八階段要求**。本分支只有驗收證據，不改產品或原裁判。

| 唯一 current state | SHA／原 exit | 結果及範圍 |
|---|---|---|
| product source F | `3d681636902371ecc528b20f51eea33e272581c9` | 乾淨獨立 checkout；85 input raw/mode/blob 綁定 |
| evidence head | `9dfdac7bbded443ff5d9624d1c8fdfa7adc0ccac` | `evidence/geo288-oracle-final-3d681636/` 原 receipts 與完整 raw archive |
| oracle quick | `0` | 原 selftest.py --quick，未 write-expected／重產 golden |
| complete probe unittest | `0` | 原 test_gen_scenes.py -v，宣告與真 Ran 60，原無條件 OK 判準 |
| C4 baseline / withdrawn / restored | `0/1/0` | 原具名 C4NEG bad 8/0/8 與正常 stderr 判準 |
| probe baseline / withdrawn / restored | `0/1/0` | 原單方法；撤回必正常 AssertionError: 2 != 1，非載入/崩潰 |
| original driver / outer / top | `0/0/0` | 原 cfea/c387/6825/7d84 未改；明列 top env -u PYTHONOPTIMIZE |
| source before / after | 相同 F，status 空 | 85 raw hashes 全同；隔離撤回僅單一 intended target，逐 bytes 還原 |
| allowed skips | 無 | 八階段均執行，退出 1 只限兩個原撤回反證 |
| still red / unrun | 本八階段無紅／未跑 | 不外推其他 owner gates |
| adversarial review | 靜態18項通過；actual + public pending | #314 owner 接獨立唯讀審查，未標審過 |
| global mutation ledger | 本子項未產 | root 在共同最終 SHA 統一處理 |

原指令、環境、完整 stdout/stderr、退出碼、SHA、input manifests、撤回/還原 target bytes、原始 patch hex 都封於 receipts 及原 archive，逐檔 SHA256 見 ORIGINAL_RAW_INDEX.json/PACKAGE.json。原 R3 排他鎖整段持有至 source-after；16 MiB stack；無重試、放寬斷言或新增門檻。

限制：這八階段不取代 native／六 browser、歷史159 source mutants 或真正 native run_probe.sh 全場。完整 probe unittest 內含 fake-core shell controls；原頂層 unittest 未持久化的內層 child streams 不補造。最不確定的是本子項範圍外的其他 gates，以及待獨立覆核的公開 package；不把準備或靜審當動態驗收。
