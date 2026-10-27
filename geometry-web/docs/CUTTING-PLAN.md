# K1 裁切、餘料與採購

依 D46–D50、I58–I62、R47–R50、提案 r1.1 及 P-047 實作。原生核心只提供具型別 `terminal`；前端以一次 `references` 的正式已放置角材求料單及裁切需求，不解析來源顯示字串。

在角材料單的「料單檢視」選擇「裁切與採購」，將當次範圍加入需求清單。可在另一承載面重開並加入範圍；各範圍以 timber id 聯集去重。切換專案 context 清空範圍。單位與排序僅影響顯示。

對話框保存使用者明示的鋸縫、加工餘量、留用下限、原材種類與宣告餘料。沒有工程數值預設；新列的每一欄均須填寫，材料須明選「未設定」或提供固定版本三元鍵。被宣告餘料引用的原材截面與材料鍵鎖定；名稱、新料長度與新料端修整仍可編輯。編輯須一次通過既有 plain JSON 容量與設定守門，失敗不改附件、revision 或歷史。

設定保存為 `cutting-settings/1` 功能附件，`.gcanvas` 使用 `geometry-canvas/17` 並宣告 `cutting-plan/1`。它不進入 World、場景 dump 或模型交換包；方案與範圍不保存。未提供此讀取能力、舊格式、未知附件版本或缺能力標記均拒絕。

P-047：只有裁切設定的編輯及其復原／重做還原宣告；方案、預覽、匯出及無關復原不改清單。`nextStockKey`／`nextRemnantKey` 保存下一個未用 key（例如用過 key 1 後為 2），0 表示耗盡。每個 context 的系統高水位跨 Undo/Redo 保留；第一次建立後復原至空設定時，仍保留空附件中的高水位，避免保存重開後重用實物標記。

求值依提案 0–5 階段與 INVALID > UNSUPPORTED > INCOMPLETE 的優先序；任何診斷都不輸出部分方案。FFD 先依可用長度與 key 選餘料，再用已開新料，需求件依加工長度遞減與 id 遞增。每支料收尾後驗座標、鋸縫、修整與剩料守恆，以及每件需求恰一次。只有 COMPLETE 能匯出固定 30 欄、BOM、CRLF 的 mm CSV。

匯出重新核對世界指紋、設定指紋、context/frame、revision 與範圍；遲到回覆、來源變更及取消均不得產生下載；連點只處理一次。F4a 與模型快照共用的 CSV 序列化剔除新增 terminal，既有 CSV 不變。

GEO-219 減項：把既有獨立「排序」控制合併為「料單檢視」，保留原來兩種排序及 DOM id，加入裁切檢視。沒有新增常駐工具列。裁切對話框只有一塊常駐操作說明，狀態與拒絕原因按需顯示；料單原有狀態列維持。

前端求值、附件／ZIP、metadata owner 及匯出 race 測試在 `tests/test_cutting_*.js`，以 `python tests/run_all.py --only cutting` 執行。`tests/mutate_k1_frontend.py --out <TEMP>/mutations.json` 在一次性副本移除各行為並保留紅燈診斷，不改工作區。真 native／瀏覽器另由 `cdp_test.js` 的 P89 執行；未取得瀏覽器與 WSL 收據前不可宣稱完整驗收。
