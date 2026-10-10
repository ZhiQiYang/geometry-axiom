# verify-3 為什麼不計入通過

`runs/focus390-verify-3/probe.log` 結束碼 1。1280 的 Tab／Enter 已是 `tab-enter-kept-input`。390 的紀錄是：

`CASE tabEnter 390 tab-missed BUTTON#workspaceToggleRight BUTTON#fileMenuBtn BUTTON#fileMenuBtn BUTTON#`

當時探針在取樣前送了 Escape。390px 右側抽屜是開的。`app.js` 的全域鍵盤處理在抽屜開著時把 Escape 當成關閉抽屜，並把焦點還給 `drawerTrigger`（`#workspaceToggleRight`）。下一次 Tab 因此從頁首按鈕走到 `#fileMenuBtn`，沒有從 `#refGuideMode` 出發。

同一輪的桌面與 390 查詢完成焦點、等待中改值、離開面、舊回覆不搶 `#refGuideCreate`，在 log 裡是通過的。那些項目改由沒有送 Escape 的 verify-4 整輪重跑，verify-4 結束碼 0。verify-3 的狀態、截圖與 log 保留，不用來改寫 verify-4 的通過數。
