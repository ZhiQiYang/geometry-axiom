# 測試缺口（最多三條，2026-10-08）

當初只讀 `D:\geometry-axiom-focus390` @ `ce0958ca700753172338fe291a17e781da89465a`，沒有在那次改測試。其後 #171 `fd5b8c8` 補了第一條裡的正式規則線案例，共用助手仍在。不把非同步審查裡未重現的五項疑點寫成缺陷。#174 已經在別的工作樹修晚回覆，下面三條不是那兩項，也不要拿去重開 #173。

選這三條是因為現在的綠燈可以由「載入沒發生」或「壞寫入來得比較晚」騙過。

## 1. 來源子規則 roundtrip 載入前沒有 reset

- 檔案：`tests/test_grid_subdivision_oracle.py`
- 函式：共用 `roundtrip`，第 303–309 行。這支助手沒有改寫。
- 已補的是另一條，不是這支助手：PR #171 `fd5b8c8` 的 `test_formal_rule_line_timber_undo_redo_survives_reset_load`。它先 undo／redo，再 `reset`，證明指定集合是空的，然後才 `loadfile`。
- 仍抓不到：其他呼叫點仍走不重置的助手。載入若變成 no-op，那些呼叫仍然會過。
- 對照：`tests/test_grid_system_contract.py` 的 `roundtrip` 第 123–132 行會先 `reset`。
- 本輪不再改這支助手，也不把 12 個呼叫點改寫。不要改 `app.js`。

## 2. GEO244「重開」比對的是尚未清掉的同一份記憶體

- 檔案：`geometry-web/space_model_test.js`
- 案例：`drawingAlignmentRegression` 裡的檢查「GEO244 project import restores aligned source and saved model without inferred geometry」，約第 710–714 行。緊接著第 716–717 行的像素檢查只看重開後的最終畫面。
- 現在抓不到：匯出時場景已經等於 `aligned`，模型也還在記憶體。`importBytes` 若沒有換世界，`scene()===aligned` 與模型 JSON 相等仍會過。名稱寫「restores」，斷言沒有先看到空白世界或新的 context。第 717 行 `reopened.lower>25 && reopened.upper<10` 只看兩點像素，畫面相近就過，不核對定義位元組。
- 交給：唯一瀏覽器擁有者。該檔在 #174 工作樹已有未提交修改，本輪不競寫。

## 3. newid 晚回只用固定 sleep 斷言「沒有寫入」

- 檔案：`geometry-web/grid_rule_lines_test.js`
- 位置：模組內 `race` 迴圈，約第 126–129 行。檢查名稱是「newid ${race} 漂移後零 history-begin/timber/place/World/history」。同一檔第 137 行還有 `sleep(300)`，用來等延遲 exact query。
- 現在抓不到：`__ruleRelease()` 之後固定 `sleep(250)`，再看 `__ruleWrites.length===0`。250 毫秒內寫入抓得到；更晚的 `line ` 寫入發生在斷言之後，這條已經算過。名稱承諾零寫入，觀察窗卻是時鐘而不是「這次回覆已經結束」。
- 交給：瀏覽器 QA（`D:\geometry-axiom-async-qa`）。不要改 #173 的檢查器焦點，也不要把未重現的五項疑點加進這個測試。

## 另列：判定式自檢，不是產品變異

`geometry-web/grid_rule_lines_test.js` 約第 167 行，`lateGuide` 裡的檢查「搶回引用式會被判失敗」是：

`stole(id)=>id==='refGuideExpr'`，然後要求 `stole('refGuideExpr')===true` 且 `stole(目前 activeElement id)===false`。

這只證明該判定式把字串 `refGuideExpr` 看成搶焦點，並讀到當時焦點不是那個 id。它沒有改產品、沒有注入會搶焦點的變異。真正的產品斷言是其後第 173 行「舊查詢不搶回焦點」。`ce0958c` 已把證據文案改成這個意思。不要把第 167 行寫進通過數，也不要把它當成變異測試已跑。
