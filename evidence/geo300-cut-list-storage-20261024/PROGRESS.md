# GEO-300 cut-list storage progress

PR #346；product SHA：39273bc0229fbbb16565134e1f8fad3a0d598c31。原基底 #343，分支 codex/geo300-cut-list-storage-20261024。容量仍 64；本片只把群內 ID 改為單一自有池，保持按值 copy、自有資料與原排序，分群／排序時間仍 O(N²)。

## 唯一 current-state

| 項目 | 結果／界線 |
|---|---|
| 實際執行 HEAD／tree | 39273bc0229fbbb16565134e1f8fad3a0d598c31／01fbacdde254c2b12d7de74e7f9d78dd4243b052 |
| 準備前 checkout | a5f1806fb3cad2dada1a56e79e01d54f9f86700f；driver 切回真正 S392 執行，結束仍 S392 clean |
| 原完整 report-policy suite | exit 0；11 方法、0 skip，原 16 MiB stack 與 timeout 不變 |
| 原四＋新五反證 | 9 組均正常 assertion 0/1/0；完整 argv／stdout／stderr 見 formal-S392 原件 |
| 編譯／連結 | 83 條均 exit 0；storage mutant 的 client 與 cut 共用同一 header bytes |
| 原 CLI 報表與還原 | 原測試逐 bytes 比較通過，包含在上述 11 方法 |
| 獨立實跑／封包審查 | 2279 checks／0；603 封存原件逐 bytes/hash 核對 |
| 完整 native、browser、效能、帳本、架構 | UNRUN；不借其他 SHA 的收據，不標 READY |
| 512 容量 | 後續獨立分支；本 S 仍 64 |

正式入口：`env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/geo300-cut-list-storage-20261024/formal-tools/launch_report_suite.py`。launcher SHA-256：7a15af7d663b307abc128695ffc1205afb42eed6ca31154d394bb4d551498e13。正式時間 2026-10-24T01:04:27.713901+00:00 ～ 01:04:33.962775+00:00；outer、reaper、原 suite 均 0。環境、指令、來源 SHA、結束碼及原完整 streams 全存 formal-S392。

原 receipt 的 native_execution_log 是「已配置但未產生」的 JSONL locator；真正完整執行流在 `wood-report/observed/receipt.json` 與 `observed/commands/`。另外 cleanup audit 確實留下原 NativeBuild build-log.json 及編譯來源。兩者分開說明於 LOCATOR_CORRECTION.json；原 receipt 與原封包不回寫。

環境準備 R1：舊 Git 不支援 `sparse-checkout add --no-cone`，退出 129，沒有修改 fixture／產品。R2 依既有 non-cone 模式 `git sparse-checkout add /room_a.scene` 成功；370 bytes fixture 與 S392 Git 原件逐 bytes 相同，舊 sparse patterns 全留。R1、R2 原指令與輸出皆封存，不把準備錯誤當產品失敗。

完整正式原件 archive：`formal-S392/original-report-suite-fixture-and-control-streams.tar.gz`，603 members、3,455,626 bytes、SHA-256 a6c35f31f6c1da542d04e2f2ffed849c20aabde1d1e7d829ccb79349c2df67a2。原靜態準備 archive、fixture 與 private TMP runtime payload 全保留。

下一步：依列車最終來源由主代理安排受影響整合、帳本與架構；後續順序 #343 → #346 → #128 P2 → 512。NOT READY。

## 歷史

Ea5 及更早版本的靜態準備、UNRUN 矩陣見 Git 歷史與 STATIC_PREPARATION_ORIGINALS.tar.gz；它們不再是 current-state。
