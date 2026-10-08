# 外環邊未送出文字的重繪證據

這包只記第二階段找到的邊長覆寫。它不是 PR #170 的格線輪，也不能與 316、328、346 相加。

產品修正在 `geometry-web/app.js`。檢查器整段換掉時，只保留同一個 boundary 上、模型長度沒有變的 `input[data-edge-len]`。被核心拒絕的那一格先回到模型值，避免把 `0` 或過期草稿寫回去。焦點只在重繪當下仍在那一格、而且這個 pane 裡沒有別的控制項時補回。

依賴草稿 PR #170（`fix/rule-guide-focus-20261008` @ `e176681f34c634d0fdd2dca364a8d7d44cc51808`）。#170 的 `reapplyInspectorFocus` 沒有改。這不是隱藏的 `#refGuideExpr`。

## 身分

- 工作樹：`D:\geometry-axiom-inspector-draft`
- 分支：`fix/inspector-draft-redraw-20261008`
- 起點：`e176681f34c634d0fdd2dca364a8d7d44cc51808`，當時只有 `app.js` 未提交
- 服務：`http://127.0.0.1:8915/`，沒有使用 8914
- runtime：`f2804c8068805409ccc06cddea3fac6219f768706f9276e981948f1142a286b2`，fresh，root 是這個工作樹
- 第一輪 pid 38592，session `05d1d8e0dda64605b0dbb959a251dafa`，bridge child 38084
- 重開後 pid 28948，session `d42ea450e1c14192a57a0c7a6609f44f`
- bridge 沒有重編。SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`，大小 783872，最後寫入 2026-10-08 20:13:39 +08:00
- 探針在本機暫存，不進 git。Chrome profile 與回報目錄也不進 git

## 第一輪（乾淨服務，結束碼 1）

通過 13、失敗 1、未驗 1。失敗是三視圖按鈕被擋住，不是邊長斷言失敗。

- 1280 輸入 `0` 後 Tab：欄位回到模型 `200`，boundary JSON 不變
- 1280 與 390：持有 `line ` 時直邊是 `4242`，phase 仍是 `held`
- 釋放並等到橫向 `defaultValue` 變成新長度後：直邊值 `4242`、直邊模型仍是 `140`，橫向值與模型都是 `240`，焦點留在直邊
- 1280 持有中改去按指令欄：直邊 `5151` 還在，焦點留在 `cmd`，橫向模型成為 `255`
- 1280 另一個面的邊長是 `4000/3000/4000/3000`，沒有 `7171`
- 面內那次沒等到邊長欄，後來證實是進入工作區後太早查 DOM。三視圖 `#btnObj` hit false。這兩項不算產品通過

畫面：`shots/edge-mainEdge-1280.png`、`shots/edge-mainEdge-390.png`、`shots/focus-left-1280.png`。

## 面內拒絕重繪（重開服務後）

預覽確認沒有完成，狀態是 `I8a: missing/invalid preview token; cannot apply`。橫向從打進去的 `4040` 回到模型 `4000`。直邊仍是 `4242`，模型仍是 `3000`。焦點沒有回到 `edgeLength1`。

這證明面內「拒絕後重繪」留得住另一格未送出的數字，也沒有把焦點搶回去。它沒有證明面內成功套用後的重繪。影響對話框還開著，返回鈕被 `.reference-impact` 蓋住，所以三視圖晚回覆仍是未驗。畫面：`shots/face-reject-1280.png`。

## 未驗

主畫布三視圖的晚回覆、面內成功套用、實體滑鼠、IME、真實裝置、完整主 UI 與 golden。port 8914 在這輪結束時已經沒有在聽，本輪沒有對它送停止。
