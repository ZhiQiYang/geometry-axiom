# P73 等待修正的驗證判讀（6615db6 canvas）

問題：commit `6615db6` 把 P73「選已知邊一半產生引用式」的固定 `sleep(180)` 改成
「等 `fe.guides` 出現目標 guide 且 `[data-edit-guide]` DOM 列渲染完成」。
它改的是測試不是產品——要確認這是正當時序修正，不是蓋掉產品缺陷。

## 第一步：連線錯誤「無法確認載入結果」的因果（純讀碼）

- 訊息唯一來源：`geometry-web/reference-workspace.js:1888`，在 `uploadScene` 對
  `fetch("/upload"|"/upload/confirm")` 的 catch 裡呼叫 `connectionFailed(...)`。
  屬於場景載入路徑，與 P73 的參考線建立路徑無關。
- `connectionFailed` 定義在 `geometry-web/app.js:553-556`：`phase="error"` +
  `error=message`。`recoverConnection()`（app.js:557-592）成功時只設
  `phase="ready"`（:582），**全 codebase 沒有任何地方清掉 `connection.error`**。
- 因此 `phase:"ready"` + 舊 error 字串並存 = 某次 error 後已復原、error 是殘留欄位。
- 是誰製造這次 error？`geometry-web/cdp_test.js:6564-6575` 的 **P61-10 / P61-11**
  （「=== P57–P61. PDF 與專案保存(GEO-198) ===」段，在 P73 之前執行且通過）：
  刻意把 `window.fetch` 包成對 `/upload/confirm` 丟 TypeError →
  `ReferenceWorkspace.importBytes` → uploadScene catch → `connectionFailed` 同一訊息
  → 斷言 `blocked`（phase==='error'）→ `recoverConnection()` 復原。
  頁面沒有自動復原迴圈；`recoverConnection` 只被啟動、retry 按鈕與這些測試 eval 呼叫
  （app.js:593/10712、cdp_test.js:6568/6574/6614/6624/6634/6635、project-ui.js:76）。
- `cdp_test.js:7116-7133 fatal()`：斷言失敗後只記 FATAL_NETWORK、eval UI 狀態、
  截圖，然後才 `chrome?.kill()` + `process.exit(1)`。擷取 FATAL_UI 之前
  **不做任何會讓進行中請求失敗的事**（不關連線、不 abort、不停服務）。
- FATAL_UI 的 `events`（`wsl-ci/798d8387/canvas/job.log:1750` 與
  `wsl-ci/c7ed80aa-p73-revert/canvas/job.log:1750`）最後 10 筆全是 `ok:true`
  的 api 呼叫（guide create → objects → surfaces → references → boundary…），
  失敗事件不在視窗內 → 錯誤遠早於 P73 斷言。
- 判斷：**三者皆非**。錯誤不是 fatal 的副作用（harness 不動連線），也不是
  「參考線列沒渲染的原因」（它發生在更早的刻意注入測試，復原後 api 全成功，
  包括攜帶 guide 資料的 `references`）。它是 P61-10/11 故意製造、復原後
  永不清除的殘留欄位；通過的那次同樣存在（P61-10/11 一樣跑過一樣過），
  只是沒有 FATAL 就永遠不會被倒出來——所以 6615db61 job.log 出現 0 次
  不代表它沒發生，只代表沒被 dump。

## 第二步：等待實測毫秒數

WSL-only commit `5bf5a6d5f647ab330a2ec783f30ac25eed96083d`（在 6615db6 上只加
兩個 `Date.now()` 時間戳與一行 `P73_WAIT_MS` 記錄），收據
`wsl-ci/5bf5a6d5-p73-timing/`。

- `job.log:1747`：`P73_WAIT_MS {"createToBusyClearMs":190,"busyClearToRowMs":437}`
- 即：guide-create 點擊 → `!oc.busy` 成立 190ms；`!oc.busy` → `[data-edit-guide]`
  列渲染完成 **437ms**。舊的 `sleep(180)` 在列出現前 ~257ms 就檢查，必然落空。
- 437ms 屬「幾百毫秒」，符合提交訊息所述非同步刷新鏈
  （obstacles→references→dump→source-inspect）所需時間；不是逾時/重試型等待。
- 該次 canvas 全綠：exit 0，2207 過 / 0 敗，`completed:true`，
  `goldenCompare:"matched"`（84 段）——同時是 6615db6 的第二次通過確認。

## 第三步：還原 `sleep(180)` 的突變驗證

WSL-only commit `c7ed80aa07010cc326a702afff81ef73db4c4ce8`（把那 2 行還原成
798d838 的舊式，diff vs 6615db6 只有這一處），收據
`wsl-ci/c7ed80aa-p73-revert/`。

- canvas exit 1：`job.log:1747` `P73 選已知邊一半產生引用式，位置與走向用語一致 ✗ false`
  → `job.log:1748` `FATAL: P73 assertion failed …`。1624 過 / 1 敗，
  與 798d8387 基線失敗逐項相同。
- `job.log:1750` FATAL_UI 同樣出現 `phase:"ready"` + 殘留
  「無法確認載入結果，已暫停編輯。請確認服務後重試。」——兩次失敗一致再現，
  佐證它是 P61 注入測試的固定殘留，與 P73 成敗無關。
- 該次 FATAL_UI 的 events 更直接顯示時序：`click` 於 refGuideCreate
  （t=…446）→ guide api ok（t=…787）→ references/boundary 還在跑（t=…854/868），
  刷新鏈在 FATAL 擷取時仍未結束——正是 `sleep(180)` 涵蓋不到的鏈。

## 附註：`wait` 的實際逾時

`uiux_review_test.js:57` `wait=cdp.makeWait(waitForUI,30000)` →
`cdp_test.js:213-217` 每 50ms 輪詢、逾時丟錯。**確認為 30 秒**，與提交訊息一致。

## 最終結論

**「等待是正當的時序修正，可合併。」**

依據：(1) 新等待是確定性完成條件（guide 存在 + DOM 列渲染），上限 30s；
(2) 實測需求 437ms，舊 180ms 是真的不夠，不是產品在重試/逾時中自愈；
(3) 還原後在同一環境同一斷言必紅（第二次獨立再現），證明通過與否由
「等不等列渲染」決定，而非產品行為改變；(4) FATAL_UI 的連線錯誤證實為
P61-10/11 刻意注入測試留下、復原後不清除的殘留欄位，兩次失敗都出現、
通過時也存在（只是不被 dump），與 P73 無因果。

### 最不確定處

FATAL_UI 的 `events` 只保留最後 10 筆，無法直接指出 `connectionFailed`
發生的確切時間點；但全 codebase 只有 uploadScene 會產生該訊息，而套件中
唯一會讓它失敗又復原的路徑就是 P61-10/11（及其後的 P6x 復原測試）。
即使假設它來自某次真實暫態失敗，也不改變結論：失敗後 phase 已復原為 ready、
後續 api 全 `ok:true`、且 P73 的資料面斷言（`apiRequest('references')` 找得到
guide）成立——缺的一直只有 DOM 列渲染。
