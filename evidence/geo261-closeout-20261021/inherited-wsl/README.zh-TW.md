# 交接的 WSL 歷史原件

以下三檔逐位元組取自交接分支 commit `59796b1af9259eb23d30134c2ce5a56317a06091` 的 `handoff/canvas-7dae5f21/`，並以 `git show <commit>:<path>` 核對原件。

**這是使用者交接的歷史證據，不是本次雲端工作階段的重跑。** 原結果包含 canvas 的 P52-5 失敗、P68 timeout，以及另一次建置逾時；不得把這些檔案列為本次通過收據。其餘歷史 job 的結果也只能依原 receipt 的來源與時間陳述。

| 原始檔案 | bytes | SHA-256 |
|---|---:|---|
| `receipt-7jobs.json` | 22999 | `ba969526c2135d7cfdc66d8a3cec808dce47b65b9bdfeecddff6caa9dc0190f4` |
| `canvas-run1-job.log` | 149791 | `8c0ef4bef8a27098707533313b7598d62924b01037e40b4e5d342792520b0c27` |
| `canvas-r2-job.log` | 4971 | `d5a810456f072097b53c8dbb47f9b5d1301db609b6ef4d93753e500934deeb9a` |

本次新增的測試結果由各自的來源 SHA、命令、結束碼與新收據證明；本目錄不取代它們。
