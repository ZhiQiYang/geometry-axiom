# #201 P-095 orphan ZIP 具名預算與量測

基線 `36e51b5d840c407066913f6a50bd8ab2102b4e27`。只替 130955 / 130956-byte orphan collection ZIP 兩案設定 `ORPHAN_COLLECTION_ZIP_TIMEOUT_MS = 10000`；一般測試仍是 5000 ms。測試名稱、數量、fixture、三次 pack/unpack、cold read、移除其他 draft、Undo/Redo、manifest、容量與 metadata-only native API 斷言完全保留。`body-equality.json` 記錄原測試本體逐位元相同的 SHA-256；沒有修改產品或 expected。

## 原始量測

`profile-preload.cjs.txt` 是本次实际執行的 instrumentation。profile 使用原基線、已由 registry 編譯的 bridge；`profile-497120.json` 為有測試的 worker，另一份為 parent。profile / actual-source 各自 exit 0、2/2。測試本體没有磁碟寫入或 Python 子行程；before hook 的 catalog fixture 子行程不屬於測試本體，成功的 execFileSync API 不提供其 PID。ZIP 產物在記憶體。

| 階段（ms） | 130955 | 130956 |
| --- | ---: | ---: |
| 測試本體 | 2130.103 | 1926.997 |
| plain-JSON jsonBytes（1406 / 1462 次） | 1128.069 | 1155.625 |
| pack（3 次，含驗證） | 905.850 | 817.298 |
| unpack / cold-read（3 次，含解析及驗證） | 359.549 | 335.253 |
| manifest（3 次，含驗證） | 337.153 | 306.230 |
| unpack manifest parse + validate | 303.330 | 292.172 |
| ZIP generate（3 次） | 8.139 | 2.843 |
| deepEqual（5 次） | 0.289 | 0.257 |

這些是 nested inclusive 計時，不能相加。JSON parse 與緊接的容量驗證合併計時；沒有將合併時間誤標為單純 parse。主要成本是產品現有的重複 plain-JSON 容量驗證，縮減 roundtrip 或 payload 會移除原驗收範圍。因此採 P-095 允許的兩案具名預算。正式 WSL train6 回報最慢 5878.7 ms（review comment 6147195327），10000 ms 小於其 3 倍；這份 receipt 沒有宣稱自行執行 WSL。

## 受控移除 / 還原

`run_controls.py.txt` 為本次實際執行程式，重現時須從上述基線開始，並將其 repo / out 路徑改成自己的 clone / output。程式產生保留原 module filename 的 wrapper，各案獨立執行；只暫停自己新建、確認 PID = PGID 的 process group，100 ms period、nominal CPU duty 0.3。所有 signals、argv、PID/PGID、開始時間、原始碼/wrapper SHA、actual exit 都在各 receipt。此為受控排程壓力，沒有聲稱所有執行得到完全相同 CPU。timeout 是取消失敗，沒有冒充 semantic assertion failure 或 mutant killed。

| 案例 | 舊 5s（exit 1） | 修正 10s（exit 0） | 移除（exit 1） | 還原（exit 0） |
| --- | ---: | ---: | ---: | ---: |
| 130955 | 5839.759 | 7565.027 | 5452.609 | 7057.856 |
| 130956 | 5028.845 | 7801.329 | 5341.755 | 7068.890 |

表中為 Node case duration_ms；process wall time 另在 receipts。8 個 stdout/stderr 均保存。10s 也小於本機壓力對照最慢 7801.329 ms 的 3 倍。實際 tracked source 的兩案結果見 actual-source stdout（3019.874 / 1961.973 ms）。

## 完整 native

完整 runner receipt 後續加入此目錄。mutation-check 僅為既有執行檔及 ledger 的 freshness 檢查：40 killed / 1 crashed / 4 equivalent / 3 retired、0 stale / blocked；本次沒有重新執行 core mutants。native source 與 oracle 均無修改，不把 freshness 檢查說成新增 mutation 執行。
