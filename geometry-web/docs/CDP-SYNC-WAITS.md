# 瀏覽器測試的同步等待

PR #197 的 `0361df58` 等待修正切片只調整測試與測試 helper，該切片
沒有改產品。整個 PR 另包含 `3837ceb1` 的 FaceProjection 產品修正：
取消、Escape、保存後與離開流程同步結束當次 session，移除會在之後交付的
全域 close 清理，避免舊視窗的 close 事件使新 session 失效。
原 context、history、面身分、來源與保存守門仍保留；既有斷言期望值與
`cdp_sections.golden.json` 未放寬。新增生命週期斷言另計，不下修舊群組。

此產品修正已有 14 項純 Node 回歸、六個具名突變及各次還原結果；
真 Chrome 的受控舊碼／M1 各為 15 過 4 敗，修正／還原各為 18/18。
Chrome 收據僅涵蓋 partial/projection-close，含兩種舊 close 延後交付時序、
普通取消與 Escape；不能代替最終 head 的七 job、完整 canvas 與 golden 驗收，
也不回填歷史 401／678／387 首次失敗的根因。

## 期限契約

依 2026-10-11 PR #197 的裁決，§7 頂點等待採 15 秒硬門檻。
`makeSettle` 的條件等待與選用診斷共用一個截止時間：

- 尚未完成的求值由 timer 截止；求值返回後仍核對時間，避免晚到的 true 被接受。
- 診斷只能使用剩餘時間；截止後不新增診斷請求。無法取得時明寫 unavailable。
- soft 只讓呼叫端繼續執行，仍回傳 `ok:false` 並印出站點。
- §7 將 `ok` 納入原本唯一的頂點 verdict。逾時立即判紅，跳過補等與晚到讀值。
- 如期成功仍保留原本的頂點比較、刷新收尾與單一 verdict。

P80 / P88 的成功條件與原先匯出數量、指紋、hit-test 判斷保持不變。
這個截止時間約束測試等待，不取消已送到瀏覽器的原生工作。

## 可重跑的純 Node 回歸

```text
node --test tests/test_cdp_settle.js
node --test tests/test_cdp_card_position.js tests/test_cdp_evaluation.js
```

新增的 10 個測試執行實際 helper；§7 案例擷取實際站點，僅替換其依賴，
用假時鐘測如期成功、晚到、永久 pending、診斷 pending 與單一 verdict。
它已登記為 `node:cdp_settle`，沒有調整既有 suite 數量或瀏覽器 golden。

在修正前 `ade253ad0de61fe5d12e5053d162afffb95f901c` 的程式上，
10 項中 6 項因上述缺口失敗；修正後 10/10，既有相關測試 30/30。
逐一移除「§7 納入 ok」「返回後核時」「等待競速 timer」「診斷剩餘時間」
四項保護，新增測試均因對應原因失敗；還原後 10/10。

本機原始紀錄與移除修正的腳本在本次派工 scratchpad 的
`board-local-codex/verify_pr197.py`、`pr197-unit-results.json` 及同名前綴 log。
純 Node 結果不代表真實瀏覽器延遲注入、canvas×2、grid×1 或七 job 全量通過；
那些結果必須另附待合併 head 的實跑收據。

真實瀏覽器注入腳本為 `tests/evidence/cdp_sync_proof.py`。它在全新 Linux
暫存 clone 中保留原斷言，只限定執行段落；19 個情境分別涵蓋三站基線、
舊測試延遲紅／新測試延遲綠、永久不更新、錯誤匯出與頂點超時晚到。
所有產品變異僅存在暫存 clone；每案另存 patch、runtime、原始 log、耗時
與退出碼，最後還原。發生非預期結果就停止，不能拿啟動失敗冒充突變命中。
執行必須經 WSL 排隊鎖，`--runner-tools` 使用同一份 `wsl-ci` 隔離取樣器。

## P11 RC creation response

P11 的建立指令完成後，原生 `objects` 已包含新柱／樑，但 `renderObjects`
可能仍在等它自己的回應及畫布刷新。柱與樑卡片讀取各加 15 秒、有期限的
條件等待；逾時納入原有 verdict，不能接受晚到值。原有建立、拖曳、連線、
搜尋與檢視器斷言不變，golden 仍要求 P11 的 12 項通過斷言。

以真實 native 回應延後 4 秒交付的六案 Chrome 對照：舊碼無延遲 12/0；
舊碼延遲 8/3（柱卡片、障礙連線、樑卡片）；修正 12/0；移除柱等待 9/2；
移除樑等待 11/1；還原 12/0。每案獨立服務與 profile，原生三支 binary
前後 SHA／sidecar／freshness 相同。只延後已收到的真實 JSON，未改 payload、
補送 HTTP 或改既有斷言；觀測原 `renderObjects` promise 並原樣回傳。

此為 partial/P11-native-response-delay-probe，未比較 golden，不能替代新
head 的完整 canvas。原 a389de37 一次完整觀測實際 2204/3、golden mismatch，
P11 的兩項失敗及斷言數不足原件保留。該輪 P69 成功也不解釋先前的 P69
逾時；本修正只處理六案所證明的 RC 卡片讀取等待缺口。
