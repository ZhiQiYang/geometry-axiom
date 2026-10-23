# #314 進度：受影響的五套隔離診斷

產品／測試 SHA：`291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6`。七份舊雙軸場景已由未修改 F2 官方 bridge 產生，收據見 `../geo314-legacy-fixtures-f2/`。

| 獲准的 suite | 結果 | 退出碼 |
|---|---:|---:|
| `test_geo314_stagger_commit.py` | 45／45 | 0 |
| `test_geo314_commit_paths.py` | 11／11 | 0 |
| `test_geo314_ordered_facts.py` | 14／14 | 0 |
| `test_geo261_wood_grid_application.py` | 23／23 | 0 |
| `test_mutation_freshness.py` | 74／74 | 0 |

全部 failed／skipped／error 均 0。這五套只是隔離診斷，尚不是 #314 完整驗收；本輪沒有修改產品或放寬測試斷言。

- 每 suite 都使用全新外部 TMPDIR；`GEOMETRY_TEST_BRIDGE` 明指官方私有 bridge，原 explicit freshness 驗證保留，沒有 fallback 到共享 cache。適配器僅設定原 `tests/binaries.py` 的 OUT_DIR，原編譯 flags／smoke／fingerprint／judge 均未改；adapter 原始碼、hash、前後設定及官方 sidecar 同封。
- H 六項及 W 十一項負控制均為 baseline 0／撤回 1／恢復 0，且精確具名正常 ASSERT；原 argv／完整 stdout／stderr／退出碼在各 suite `stdout.raw` 的 CONTROL_JSON。沒有以 crash、compile error、timeout 當 kill。
- M110／MP3 單獨拿掉 confirm 基線，被 preview 拒絕遮蔽，原觀測明列 equivalent。MP1＋MP3 配對撤回後，真 archive preview／confirm 的正常具名 ASSERT 轉紅。
- freshness 新控制實際使用舊保存收據呼叫 `check_pass`：單改 C harness 或巢狀 legacy scene，舊 record 變 STALE 1；恢復原 bytes 後回 0。不是僅比較 hash。
- before／after HEAD、status、patch 一致且乾淨。來源 bytes、原判官／wrapper、完整 stdout／stderr、環境、正式 bridge、NativeBuild 全部 inputs／binaries／完整 build-log 同封。診斷實際 shell 先執行 `ulimit -s 16384`。

待辦：受影響舊幾何／更名 suites 的完整回歸、正式 mutation ledger 全份重產、架構 H 新來源登錄及四檔重產／三原裁判、最終 SHA 的 native／六 browser／專項／效能驗收、PR 正文。以上未跑項目不列通過；M99–M120 正式帳本尚待執行，不把此診斷代填成 killed。

下一步由主代理排程；本診斷結束後暫停額外編譯，避免干擾 #323 正式效能量測。
