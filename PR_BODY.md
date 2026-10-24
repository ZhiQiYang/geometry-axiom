下料清單原本在每一個 group 內保存完整容量的 member ID 陣列。本修正改為報表自有的單一 ID 池，各 group 保存 offset／count；保留原分組、排序、群內宣告順序與按值 copy 後的自含資料。ID 儲存由 O(N²) 改為 O(N)，分組與排序時間仍為 O(N²)，容量仍是 64。

本 PR 是 #300 前置，疊在 #343。後續順序是 #343 → #346 → #128 P2 → 512；此 PR 不關閉 #300。原 report-policy 的 11 方法、9 組反證已在實際 product SHA 執行通過。

## 唯一 current-state

| 欄位／gate | 目前值或退出碼 | 精確界線 |
|---|---|---|
| product SHA／實際 execution HEAD | `39273bc0229fbbb16565134e1f8fad3a0d598c31` | execution tree `01fbacdde254c2b12d7de74e7f9d78dd4243b052`，初末 clean |
| evidence head | `eaf15e239324a6464a04740647afccce3a3c17c7` | 只增加正式原件與進度，產品 closure 不變 |
| 準備前 checkout | `a5f1806fb3cad2dada1a56e79e01d54f9f86700f` | 原 driver 明確切回 S392 執行；不把準備 HEAD 冒稱 execution HEAD |
| 原 report-policy suite | **0** | 11 方法、0 skip；原 CLI text／還原比較包含在內 |
| 原四組＋新增五組反證 | **9 × 0/1/0** | 正常具名 assertion 紅；完整命令、stdout／stderr 與恢復均保留 |
| 編譯／連結 | **83 × 0** | storage mutant 的 client 與 cut 使用同一份 mutated header |
| outer／reaper／原 suite | **0／0／0** | 原 16 MiB stack、case timeout、斷言與 golden 不變 |
| 獨立實績審查 | **2279/0** | 603 原件逐 bytes/hash；另有 locator 澄清窄審 12/0 |
| 完整 native／browser／效能 | **UNRUN** | 不借 #343 或列車的歷史收據 |
| 最終帳本／架構三裁判與收據 | **UNRUN** | 主代理依最終組合來源統一處理，沒有另行重產帳本 |
| 允許的 skip | 無新增；本 suite 實際 **0 skip** | 未跑項不是 skip 或 pass |
| 合併狀態 | **NOT READY** | 尚待列車整合驗收與最新審查 |

正式入口為 `env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/geo300-cut-list-storage-20261024/formal-tools/launch_report_suite.py`；launcher SHA-256 `7a15af7d663b307abc128695ffc1205afb42eed6ca31154d394bb4d551498e13`。原命令在 2026-10-24T01:04:27.713901+00:00～01:04:33.962775+00:00 執行，環境、來源 SHA、退出碼、完整 streams 都已保存。

九組控制分別驗 unplaced／role／fixity／length order／pool offsets／pool values／pool reverse／exact capacity／linear group storage；所有撤回均命中原具名 assertion，放回均恢復 0，沒有把編譯失敗當成功反證。

[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/eaf15e239324a6464a04740647afccce3a3c17c7/evidence/geo300-cut-list-storage-20261024/PROGRESS.md) 與 [formal-S392/RAW_INDEX.json](https://github.com/ZhiQiYang/geometry-axiom/blob/eaf15e239324a6464a04740647afccce3a3c17c7/evidence/geo300-cut-list-storage-20261024/formal-S392/RAW_INDEX.json) 綁定 603 members、3,455,626 bytes 的完整原件包，SHA-256 `a6c35f31f6c1da542d04e2f2ffed849c20aabde1d1e7d829ccb79349c2df67a2`。原 fixture、準備歷史與 private TMP runtime payload 全保留。

原 receipt 的 `native_execution_log` 是已配置但未產生的 JSONL locator；實際完整流在 `wood-report/observed/receipt.json` 與 `observed/commands/`。另有 cleanup audit 真正留下原 NativeBuild `build-log.json` 與編譯來源；它與不存在的 JSONL 不同。`LOCATOR_CORRECTION.json` 附加更正路徑說明，原 receipt／封包不回寫。文字 streams 是原 decoded text 的 UTF-8 保存，不冒稱 pre-decode OS pipe bytes。

環境準備 R1 因舊 Git 不支援 `sparse-checkout add --no-cone` 退出 129，當時沒有修改 fixture／產品；R2 依原 non-cone 設定補入 `room_a.scene` 成功，370 bytes 與 S392 Git fixture 完全一致，原 sparse patterns 保留。這兩份原輸出皆公開；它們不改變後續 suite 的真 exit 0。

最不確定的是尚未執行的整合與容量 512 行為；本片不宣稱效能倍數改善或 512 可用，不修改公理、決策佇列或 K。舊 Ea5 矩陣與靜態準備只留在 Git 歷史，這裡只有一份 current-state。
