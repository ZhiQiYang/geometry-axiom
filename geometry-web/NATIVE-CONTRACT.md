# 原生介面契約索引

本文件定位既有介面的保證與限制，不新增公理或回執儲存。依據：[公理層 I64、I67、R52](../公理層.md)、[#240 R14](https://github.com/ZhiQiYang/geometry-axiom/issues/240#issuecomment-6177689490) 與 [P-143](https://github.com/ZhiQiYang/geometry-axiom/issues/240#issuecomment-6196384131)。

## 回執三層

「取回命令結果」、「原生確認回覆」與「整筆專案交易證明」分屬三層。取得前一層不代表後一層已成立。

### T1：命令結果取回

入口是 [`serve.py::recorded_api`](serve.py)，狀態屬於 [`NativeContext`](native_context.py) 的 `session`、`api_receipts` 與 `receipt_lock`。

- 命令請求帶 `session`、`requestId`、`cmd`，可帶 `ack` 清單。`requestId` 須符合現有的 36 字元小寫十六進位／連字號格式；session 須等於目前原生 context 的 session。沒有 requestId／receipt 的舊式請求直接轉發 bridge，不享有這個結果取回保證。
- 回執以該 context 的 session 加 requestId 識別，並綁定原命令字串。**結果仍在表內時**，相同 id／命令取得原結果；同 id 改命令拒絕，不能把它當成另一個操作。這是防重執行守門，不是鼓勵前端重送；I64／I67 仍要求未知結果時查回執、不重送。
- 查詢為 `{"session":"…","receipt":"…"}`。已存在的結果直接取回，不再呼叫 bridge。查詢比原命令先到時，會封存「操作未送達，場景未變更；請重新操作。」；之後晚到的同 id 命令不執行。查不到不能推成「可安全重放同 id」。
- 一般命令直接回內層操作結果；receipt 查詢回 `{"ok":true,"result":{…}}`。外層 `ok:true` 只表示取得一份 result，操作成敗須看 `result.ok`。例如提早查詢的外層為 true、內層為 false。若取回的是 bridge 連線／逾時錯誤，也不能憑該錯誤推定 World 已提交或未提交。
- 每個 context 的記憶體表上限為 256 筆（`MAX_RECEIPTS`），包含提早查詢封存的 id。先處理本請求 `ack` 清單的前 256 項，清除其中已綁命令的結果；**處理後仍滿**才拒絕新 id 的命令及查詢，不呼叫 bridge，既有 id 仍可查詢。若表內 256 筆皆為已綁命令結果，同一新 id 命令請求帶其中一筆 ack，會先騰出空位，再執行新命令並保存結果。若同一 session 早查詢滿 256 個不同 id，這些封存項無法被 ack 清除，之後新命令一律回「未確認的操作結果過多」，只能換 session 才能取得空表。這是容量耗盡的後果，不是恢復保證。
- 後續請求的 `ack` 最多處理前 256 筆。它清除已綁命令的結果；提早查詢封存的取消項不會被 ack 清除。已清除的 id 無永久歷史可查：再查詢會得到新封存的未送達結果。因此收到結果後應完成當地核對再 ack，不能把 ack 後的查詢當成舊操作的證據。
- **ack 清除後若直接以相同 id 重送相同命令，命令會再執行一次。** 例如 X 執行、Y 帶 ack 清除 X、同 id 再送 X，bridge 序列為 X、Y、X。客戶端 ack 後不得再用同一 id 重送；前一項的「先查詢而封存取消」不能被誤讀成 ack 仍保有原結果。
- `receipt_lock` 在 `ask_bridge` 執行期間仍被持有。同一 context 的其他回執請求最多等待 `BRIDGE_TIMEOUT = 30` 秒，逾時回「操作結果仍在處理」，不能據此推定原操作結果。
- 原生 context 建立時產生新 session。換 context／服務重啟後，舊 session 請求拒絕；這不是跨重啟的耐久回執或永久交易日誌。

這層保證只涉及傳輸結果與防重執行，不證明 JS 附件、dirty 或 history 已同步完成。正式函式測試見 [`tests/test_recorded_api_receipts.py`](../tests/test_recorded_api_receipts.py)：執行目前原函式與受控 context／bridge，不啟動服務；涵蓋六組基本情境及上述邊界，皆核對 bridge 的命令與呼叫次數。換 session 與鎖逾時是受控 fixture，不是實際重啟或 30 秒併發壓力測試。

### T2：原生提交回覆

[`engineering_bridge.inc::batch_confirm`](engineering_bridge.inc) 是一個既有原生確認入口，供 engineering／assembly／section-profile／panel-fill 等 batch 的各自包裝呼叫；不代表每個功能都走此入口。

它先核對 preview token、kind、ready／valid；若原生歷史群組仍開啟（`g_hist_grouping`）、definition revision 已變或 before World 不符，即以 `STALE` 拒絕。接著執行 `assembly_versions_immutable`，再以 `world_revalidate` 重驗候選，兩者通過後才提交。當 World 定義改變時記錄原生歷史並增加 revision；無變更時不增加。

| 成功回覆欄位 | 保證與限制 |
| --- | --- |
| `ok` | 此次原生確認成功；不能代替前端附件驗證。 |
| `history_changed` | World 定義是否改變及是否記錄原生歷史；不表示所有 JS 附件 history 已完成。 |
| `before_revision`、`revision` | 原生確認前後的定義修訂。 |
| `transaction_id` | 本次確認使用的 preview token，不是 T1 的 requestId，也不是耐久全域交易 id。 |
| `definition_sha256` | 只有 `eng_definition_hash` 成功才附上，不能假設一定存在；只涵蓋原生定義，不認證全部 JS 附件。 |

回覆另由 `json_deleted_objects` 列出刪除物件資訊。失敗可回 `TOKEN`、`STALE` 或 `INVALID` 等錯誤，不能當作成功回執。上述為介面索引，本任務不新增 batch_confirm 原生驗收。

### T3：整筆專案交易證明

I64 要求首房交易把 World、平面、集合、房間與草稿作為同一復原單位；I67 要求匯入取消／失敗／過期不改 World、附件、dirty 與 history。R52 的候選工作延續還須證明：只新增指定的一個平面、集合、房間記錄與 D3，其餘規定附件不變，且草稿等於同一群組剛寫入的值（未寫入者仍沒有草稿）。不能證明時候選工作過期。

既有接線位置包含 [`reference-workspace.js`](reference-workspace.js) 的 `prepareFeatureConfirmation`、`beginFeatureConfirmation`、`assemblyConfirmationCurrent` 等 context／frame／revision／session／附件守門；各功能仍須對應自己的候選、確認、歷史與回覆恢復路徑，不能只因找到這幾個函式便推成全數完成。

**各功能接線尚未逐一核對，T3 列為未驗；不宣稱 R52 已端到端成立。** T1 取回結果或 T2 的 ok／World hash 均不足以證明其餘附件不變，也不足以證明一次 Undo／Redo 還原完整專案。本次函式測試只驗 T1，不把替身測試當成 T2／T3、HTTP、瀏覽器或正式 WSL 收據。
