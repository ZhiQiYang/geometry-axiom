# 連線恢復後沒有清除 `connection.error`，舊錯誤訊息一直留著

（草稿，2026-10-20。來源：分析 GEO-261 整合分支 `09ab5f79` 的 canvas job 時發現；這次不修。）

## 現象

`recoverConnection()` 成功恢復後，把 `connection.phase` 設回 `"ready"`，但 `connection.error` 仍保留上一次失敗的字串。

在 `09ab5f79` 的 canvas job 裡，P72B 失敗時 `FATAL_UI` 印出：

```
"connection":{"phase":"ready","error":"無法確認載入結果，已暫停編輯。請確認服務後重試。"}
```

這句錯誤是約 20 分鐘前 P61-10／P61-11 刻意注入 `/upload/confirm` 失敗時留下的。兩條斷言當時都通過（job.log 第 912-913 行）；從 P53 的 reload（job.log 第 845 行）之後就沒有任何頁面導覽，所以字串一路留到 P72B。它與 P72B 的失敗無關，卻讓診斷者誤以為載入確認逾時了。

## 程式位置（`geometry-web/app.js`，整合分支 `09ab5f79`）

- `:492`：初始值是 `connection = { phase: "loading", known: false, error: "", recovering: false }`。
- `:564-567` `connectionFailed(message)`：設 `phase = "error"`、`error = message`。
- `:568-603` `recoverConnection()`：`:570` 設 `phase = "loading"`；`:593` 設 `phase = "ready"; connection.known = true;`，**沒有清 `error`**。
- `:625` `apiRequest()`：phase 是 `"loading"` 時會擋下修改類指令，回傳 `error: connection.error || "場景尚未讀取完成"`。

錯誤來源之一是 `geometry-web/reference-workspace.js:1990-1991`：`uploadScene()` 的 `/upload` 或 `/upload/confirm` 拋錯（逾時、HTTP 非 ok、回應不是 JSON）時呼叫 `connectionFailed("無法確認載入結果，已暫停編輯。請確認服務後重試。")`。

## 影響

1. **使用者看得到（輕微）**：下一次重試期間 phase 是 `"loading"`，此時送出的修改指令會從 `:625` 拿到上一次的舊錯誤（例如「無法確認載入結果…」），而不是「場景尚未讀取完成」。
2. **診斷誤導**：測試框架的 `FATAL_UI` 和 `cdp_test.js:3603` 的 `Missing control` 診斷都會印出 `connection.error`。phase 已經是 ready 時，這個欄位看起來像目前的錯誤。
3. `showConnectionState()`（`:547-563`）只在 `phase === "error"` 時顯示 `error`，所以畫面上的連線提示本身不受影響。

## 建議修法（未實作）

在 `app.js:593` 轉為 ready 時一併清掉：

```js
connection.phase = "ready"; connection.known = true; connection.error = "";
```

另外檢查其他把 phase 設回 `"ready"` 的地方（例如首次載入路徑）有沒有同樣的問題，一併處理。

## 驗收

- 在 P61-10 與 P61-11（`cdp_test.js:6606-6616`）`await recoverConnection()` 之後的斷言加上 `connection.error === ""`。
- 在 P53 重試恢復（`cdp_test.js:6360-6363`）之後也加同一條。
- 突變控制：拿掉 `connection.error = ""` 時，這幾條必須轉紅，失敗訊息要能指出殘留的舊字串。
- 斷言數會增加，`cdp_sections.golden.json` 對應段（P53、P57）必須用 `GEOMETRY_CDP_UPDATE_GOLDEN=1` 在完整模式零失敗下更新。
