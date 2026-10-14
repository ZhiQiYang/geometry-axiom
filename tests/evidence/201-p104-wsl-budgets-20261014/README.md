# P-104：四案依完整 WSL 觀測設定個別期限

本次只改 `test_reference_workspace_races.js` 四個案例的 timeout 註冊選項；測試名稱、案例本體、斷言、一般預設 5000 ms 和 Node 703 期望數不變。

依據：[P-104](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6153429711)、[完整觀測審查](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6154048328)。

| 案例 | 新五次最大 ms | 第9班三輪最大 ms | 個別期限 ms | 對較大觀測的倍數 |
|---|---:|---:|---:|---:|
| ordinary 130956 | 1343.738923 | 5851.711680 | 15000 | 2.563 |
| ordinary 131072 | 1424.075100 | 8789.908087 | 22000 | 2.503 |
| orphan 130955 | 2344.725358 | 12359.045071 | 31000 | 2.508 |
| orphan 130956 | 2346.162281 | 8105.571139 | 21000 | 2.591 |

公式為 `ceil(2.5 * max(全部已報告 WSL 觀測) / 1000) * 1000`，逐案落在 2–3 倍。`budget-basis.json` 保留三輪值和新五次最大值；20 筆新值完整保存在 `wsl-twenty-measurements.json`。第6班三輪 orphan 最大 6557.867129 ms，亦低於第9班兩案的最大值。

第9班取消的 duration 是逾時回報點，不是完整完成成本；這個公式以所有已知觀測作有界餘裕，不能證明下班負載的成本上界。下一班正式 native 仍須驗收。

## 原件與核驗範圍

- 第9班 head `90659e6190b592feeb06fab263a16175538eb64a`、base `23ca8961d87a8b76591afebb403164e4c62c339f`、#201 source `3f1664fb5c43ad49f76ee97853d8d5923197f7c3`。原 native `2751/3/1`、canvas `707/1`，皆 exit 1，Rule 2 不豁免，首紅保持。
- 雲端獨立 GET 已公開的 258 則第9班 archive 分片，重組 ZIP `074059a093c1c9e466fc8372e279e79bd7e0602a2bddb9982d233208008752d9`（11787610 bytes）。`train9-download-receipt.json` 保存所有 comment IDs。沒有新增 base64 貼文。
- 三份 `train9-*.log` 是其內層 archive 的原始 Node 日誌；逐件對原 index 的 SHA/bytes 核符，路徑在 `selected-train9-members.json`。只聲明核驗此外層 hash 與三份選定原件，沒有聲稱逐件核完所有來源／二進位閉包。
- 新五次量測由本機工人在 WSL `wsl_locked3.sh run` 執行，**不是雲端 WSL 實跑**。公開原報告存於 `wsl-five-runs-report.md`（[來源](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6153963816)）。JSON 是公開逐筆數值與 receipt 摘錄；雲端目前沒有取得 20 份完整 TAP，不宣稱已核驗它們的檔案 hash。
- [本機交付說明](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6160470969)：原件在 Windows scratchpad 的 `board-local-codex/pr201-p104-wsl-20261014` 及 `-public` 目錄；依本機 04:30 看板不新增 109 則 base64 鏡像。既有來源擷取失敗、事後補回 C 檔及原退出碼均保留。核對完整 20 TAP 由持有原件的本機審查完成。

## 已執行的雲端檢查

- `node --check`：exit 0。
- `verify_registration.cjs` 比較 a09 前後 78 個本檔註冊：名稱／順序／所有 callback bytes 完全相同，只有四個 timeout 選項不同。它未執行案例本體，不是 78 案通過收據。
- 四案實跑：4 pass、0 fail、0 cancelled、exit 0；原 stdout/stderr 與退出碼記錄在此。此輪在合入新 main **之前**，不冒充整合後 native 或正式收據。
- 第9班 Rule 2 另出現 preflight 16117.022889 ms（15000 deadline）與 legacy live-ref 8920.980304 ms（5000 deadline）。原始三輪與摘要均保留，沒有把四案子集冒充完整 703 案，也沒有在本次悄悄調整這兩案。

這是測試期限修正，不變更產品、公理、核心裁判或期望數。歷史 P-095／M2 證據保持原樣。
