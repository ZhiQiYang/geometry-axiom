# P88 原紅燈與分類（修正前）

受驗產品 SHA：`13d02c1db7022145a52ee063286a558e595eb212`。本文件依本次重新 fetch 的 `handoff/pr-reviews/288.md` 最新 head `22ad28f` 審查，公開原收據事實；不是新測試通過聲明。

原完整 canvas 指令來自同 SHA `.github/workflows/integration-tests.yml`，job/process exit 為 **1**，耗時 **1051.678589028 秒**，在原 **35 分鐘** CI 時限內。原 `CDP_RESULT` 是 full scope、1502 passed／0 failed、`completed=false`，golden 為 `not compared (run did not complete)`。fatal 中斷不能當作 1502／0 全綠。

精確失敗條件：

```text
UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")
```

來源是 `geometry-web/grid_rule_lines_test.js` 的 `focusedCtl`（原第 27 行），390px 場景第 121 行 `choose('#refGuideMode','advanced')`。它在發送 Home／ArrowDown／Enter 前，要求真正 keyboard focus 是目標 select；保留原 **25000ms** 精確判斷。原最後 click 事件落在 `#refGuideSourceFields` 的「來源比例」label，原最終 active 為 `refGuideRatio`。原 log 沒有 mousePressed 的 target、量測 rect、scrollTop 或節點 identity，所以不能據此補造 mousedown 因果。

目前分類：**阻擋驗收的焦點／輸入時序失敗，產品重繪與測試點擊同步的責任尚待確認**。不是 golden 計數不符、CI 超時或已證實的環境故障。原 helper 在一次 hit-test 後跨 CDP 發送 mousePressed／mouseReleased；產品有非同步 query→inspector 重繪鏈。這是需要測量的時序窗口，尚不足以直接斷言產品 bug 或測試 bug。

相同 F 的原 grid job 已通過同一 390px 情境；舊 `8f76f2b7d6f669670e5834310bfc26495b4a4aa6` 完整 canvas 曾通過。現在依使用者要求，在不改產品／測試／golden／斷言／時限的 `13d02c1d` 上，獨占執行三次完整 canvas，每次獨立 HTTP/CDP 埠、Chrome profile 與暫存目錄，全部保留紅綠結果。三次尚未完成前不宣稱穩定紅或間歇紅。

原件：`/tmp/g288s7/workflow/canvas/receipt.json` 與 `steps/03.stdout`（唯一 `CDP_RESULT` 位於第 1620 行）；完整逐項診斷已在 `p88-diagnosis/DIAGNOSIS.md` 保留。新三次工具只加入顯式埠及 profile 隔離，差異、原 driver 與雜湊另存 `driver-binding.diff`、`original_run_workflow_round.py.txt`、`BINDING.json`。
