# 原生介面契約索引

本檔定位既有實作的保證與限制，不新增公理或第二套回執儲存。
依據：[#240 R14](https://github.com/ZhiQiYang/geometry-axiom/issues/240#issuecomment-6177689490)
與 [P-143](https://github.com/ZhiQiYang/geometry-axiom/issues/240#issuecomment-6196384131)。
基準來源：main `1c80751150d0767ba52509537caf8d5542769ccb`。
行為驗收仍以 `公理層.md` I64、I67、R52 為準。

## 回執三層

| 層 | 介面／來源 | 保證的邊界 |
|---|---|---|
| T1 命令結果取回 | `serve.py::recorded_api`；`native_context.py::NativeContext` | 同一 native context 的 session＋requestId，綁定命令與快取結果；查詢不重跑命令。不是永久交易日誌。 |
| T2 原生提交回覆 | `engineering_bridge.inc::batch_confirm` | 以 token、kind、revision 與 before World 核對同一候選，重新驗證後提交原生定義。不是全部專案附件的證明。 |
| T3 整筆專案交易證明 | I64／I67／R52；各功能自己的確認、附件及 history 接線 | 須核對同筆 World 與附件增量、來源、候選及復原單位。**各功能接線尚未逐一核對**，不宣稱 R52 已端到端成立。 |

### T1：命令結果取回

發行者是目前請求所屬的 native context。`NativeContext` 建立新的 session、
`api_receipts` 記憶體字典與 `receipt_lock`；另一個 context 的回執不能互用。
`recorded_api` 在該鎖內完成 ack、查詢、命令執行及結果寫入。

- 命令請求帶 `session`、`requestId` 與 `cmd`。識別字須符合目前程式的
  `[a-f0-9-]{36}` 完整比對；這是字元／長度檢查，不是完整 UUID 語義驗證。
  未提供 requestId／receipt 的舊路徑直接呼叫 bridge，沒有這份快取保護。
- 首次命令將 `(cmd, response_bytes)` 存入該 requestId。相同識別與命令再次抵達時
  取原結果；改成不同命令則拒絕，不呼叫 bridge。這是防護，不是讓前端重送的建議；
  I64／I67 要求回覆未知時查回執，不重送、不推定結果。
- 查詢帶 `session`、`receipt`，回 `{ok: true, result: <原結果>}`，不呼叫 bridge。
  查詢比原命令先抵達時，封存 `(None, 操作未送達錯誤)`；晚到命令不執行。
  即使晚命令帶同 id 的 ack，這種取消封存也不會被 ack 清除。
- `ack` 每次最多處理 `MAX_RECEIPTS=256` 個項目，只移除已有命令結果的項目
  （tuple 第一項不是 None）。ack 是附在請求上的確認欄位，不是另一個必定呼叫
  bridge 的操作；六組測試裡的第二次 bridge 呼叫來自帶 ack 的新命令。
- 容量為 256 份未清除項目，包含提早查詢的取消封存。滿載時新識別拒絕，
  不執行 bridge；已有結果仍可查詢。容量不代表時間保存期限。
- ack 清除後再查同 id，舊結果已不存在，查詢會產生「操作未送達」的取消封存。
  此時不能將該文字當成原命令從未執行的歷史證明：原命令可能早已成功並被 ack。
- 換 session 後舊 session 的命令與查詢拒絕。這是程序／context 生命週期內的快取，
  不保證跨服務重啟恢復。測試只模擬 context 換代，沒有真的重啟服務。
- **外層 `ok:true` 只表示有一份 result，內層 `result.ok` 才是原命令結果。**
  例如提早查詢的外層為 true、內層為 false。快取到連線錯誤也不會自動證明
  原生操作已提交或未提交；未知結果不能靠快取包裝變成確證。

對應測試：`tests/test_recorded_api_receipts.py` 的六個具名方法。
它們從目前 `serve.py` 的 AST 選取原函式與常數，只替換 native context 與 bridge，
逐項核對結果、快取及 bridge 呼叫次數，不 import／啟動整支服務。
既有 `tests/test_serve.py` 另覆蓋服務與進行中請求，不由這六題取代。

### T2：原生提交回覆

`batch_confirm` 先驗 preview token、kind、ready、valid；再驗沒有歷史群組進行中、
definition revision 相符，且目前 World 定義等於 preview.before。
之後驗版本不可變及候選 World 合法；過期或非法即拒絕，不改交另一份候選。

成功回覆包含：

| 欄位 | 意義 |
|---|---|
| `ok` | 本次原生確認成功。 |
| `history_changed` | 前後定義是否不同；不同才記 history、安裝候選並增加修訂。 |
| `before_revision` | 提交前的定義修訂。 |
| `revision` | 提交後的定義修訂；無變更時不增加。 |
| `transaction_id` | 此次確認的 preview token。不能當作跨 session 的永久唯一 id。 |
| `definition_sha256` | 只有成功算出雜湊時才附，不能假定每份 ok 回覆都有。 |

回覆另由 `json_deleted_objects` 附刪除資訊；具體功能須按其回覆契約使用。
`batch_confirm` 只是其中一個原生確認入口，不能推定首房或所有功能都使用它。
上述是固定來源的契約定位，本任務沒有執行原生提交驗收。

### T3：整筆專案交易證明與未驗範圍

I64 的首房交易將 World、新 D3、SourcePlane、RoomCollection、房間記錄及相關草稿
放在同一復原單位。R52 的候選工作延續還須證明指定新增量，以及其餘附件與
群組內草稿符合該條要求；純 World hash 或 T2 的成功欄位不足以代替。
各功能須將自己的候選、來源、context／history frame、原生回覆與實際附件增量對齊。

**各功能接線尚未逐一核對；T3 仍未驗。** 後續驗證須包括：原生成功但其他附件
多變一項時，候選工作不得延續；以及失敗／復原／重做是否整筆一致。
本索引與 T1 受控測試不宣稱 R52 端到端成立，也不新增永久回執儲存或跨重啟政策。
