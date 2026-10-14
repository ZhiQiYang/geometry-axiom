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

## 整合與撤修對照

一般合入 main `caf49852a4b40d4e61bdf76480c79b43bb5a3676`，merge commit `86136a42f9a409236af143af56234c5ecaea4ddb`。唯一衝突為 expected 表，三方值與選擇在 `main-integration.json`；保留 Node703、ownership13、grid15，以及 main engineering compatibility28，未調低期望數。核心 C、subgrid 實作、核心裁判／變異定義與帳本逐 byte 等於 main（`main-core-equality.json`），CRLF 保留。

在此整合來源下，每案修前／修後／撤修／還原均實際執行，actual exits 為 1／0／1／0，合計 16 次。只對自己啟動並驗證 PID=PGID 的程序群做 STOP/CONT，nominal duty=0.12、period=0.1 s。對照只改 timeout 選項，案例本體不改；這是雲端期限反證，不能取代 WSL 量測。

| 案例 | 修前 ms | 修後 ms | 撤修 ms | 還原 ms |
|---|---:|---:|---:|---:|
| ordinary130956 | 6342.545045 | 9880.091641 | 6241.698925 | 11492.731376 |
| ordinary131072 | 6053.472389 | 9701.762677 | 6557.130961 | 8145.865920 |
| orphan130955 | 10465.219774 | 14872.268105 | 13620.621440 | 17599.439551 |
| orphan130956 | 12557.596933 | 15219.248411 | 13766.756893 | 17339.022877 |

負對照 8 次均為原 5000／10000 ms timeout cancellation（不是語意 assertion kill）；修後與還原 8 次各 1 pass／0 fail／0 cancelled。取消的數值是回報點。`controls-summary.json`、原執行器、原 stdout／stderr／receipt／wrapper bytes／signals／實際 bridge 與 fingerprint 都在 `cloud-controls-originals.tar.gz`，附逐件 inventory。

最初直接讀共用 mutant cache 時，`--check` 報告 45 stale（執行檔與 main 帳本歷史收據不同）；原診斷 stdout／stderr 保留於 `mutation-freshness.*`，該診斷命令沒有獨立保存 OS status，不冒充正式 native 首跑。共用目錄放的是其他來源的歷史二進位，未刪除或改寫它們。完整 native 使用工具支援的獨立 `MUTATE_CACHE=/tmp/geometry-wake25-201/native-mutant-cache`，其中沒有舊 mutant 執行檔；`--check` 驗既有 main 的來源／閉包／裁判／變異／執行收據一致性，40 killed／1 crashed／4 equivalent／3 retired、0 stale。這是歷史收據檢查，**沒有新編譯或執行核心變異，也沒有宣稱重驗缺席的 mutant binary bytes**。

完整 native 原件僅包含本輪開始後寫入的 suite 日誌；共用目錄較早的其他分支日誌獨立排除並逐件列於 `native-log-selection.json`。`cloud-native-originals.tar.gz` 附實際二進位／fingerprint、逐 suite 原件與退出碼。`executed-sources.tar.gz` 保存本輪來源 bytes，排除歷史 evidence／release-evidence；全 tracked 檔案執行前後 hash 清冊另列，沒有以歷史來源冒充本輪。

## 完整雲端 native

受測乾淨 head `213532433b3739466295f6de7776769c4ccc0ca9`、base `caf49852a4b40d4e61bdf76480c79b43bb5a3676`，命令 `ulimit -s 16384; python3 -u tests/run_all.py --build`。87/87 suites，2758 pass／0 fail／1 具名 Windows GDI skip，實際 OS exit 0，822.379 秒。Node703/703、reader41/41（詳原表）；所有 tracked 檔案執行前後 hash 相同，結束 git status 為空。實際 child status 先寫 `native-actual-exit.json`，再做任何後處理，沒有把 helper 狀態當 child 狀態。

這是雲端完整非瀏覽器登錄測試，不是 WSL 收據、正式七項或完整 CDP。保留第9班首紅／Rule2；P-104 四案新期限與 main 整合已交付，新固定來源仍須本機正式列車驗收。preflight／legacy兩案舊期限未改，不能因本輪雲端綠燈就宣稱其 WSL 已驗收。20份新WSL TAP仍由本機原件持有人核對，雲端未聲稱獨立取得。

本輪完整 Node 日誌含原 Rule2 六個具名案例，全部通過（數值見 `native-six-cases.json`）；四案子集沒有被移算成完整703。sum-of-suite 表列792.3秒，實際 child wall822.379秒含建置與runner前後處理，不混用兩者。

封包重開驗證：controls 67／native 216／sources 1342 個 member 全部 bytes／SHA 核符；五支原生執行檔與各自 fingerprint 的執行檔 hash、全部來源引用也核符（`delivery-verification.json`）。fingerprint 依 `binaries.py:_normalized_sha` 將 CRLF 正規化為 LF；archive inventory 另保留原始 bytes hash，二者不混用。來源封包明確納入位於歷史 evidence 目錄內但實際被 include 的 C 檔，以及本輪實際 materialize 的 engineering JSON HARNESS；完整閉包優先於目錄排除規則。一般未驗的 UI 圖片未打包，全 tracked hash 仍另存。
