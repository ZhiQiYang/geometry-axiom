# R8 三差根因紀錄對抗審查

最終結論：修正文句範圍後通過，424 項唯讀核對、exit0、0未解發現。未改分支、產品、公理、測試或比較器；未執行C、突變或效能量測。

- 150個原件完整 inventory／大小／hash相符。原 Git 收件流保持不變，另以不可變 commit 獨立讀回各引用文件、引入 parent／祖先關係與具名差異。
- 三對完整stdout只有第一行JSON的 `error` 增加具名後綴；第二行dump逐byte相同。stderr各只多同一個後綴；這是診斷原因核對，沒有把刪後綴操作用於正式比較器或改寫原件。
- 六份壓縮有序圖與原件一致，解壓bytes／hash符合原equivalence。base/fix圖相同，原guards報告逐對相同；原普通與trace exit0不代表場景接受。原三場景仍 `SCENE_INVALID`，原compare仍exit1。
- 固定base與F8整條I22的 **raw bytes完全相同**，不必靠換行正規化；兩者早已要求「訊息指名料件、定位邊與超出的區間」。既有契約要求可追溯至 `1ee76768…`，它是固定base祖先。
- 原base與引入parent的contacts.c完全相同；引入 `6366304e…` 與F8的contacts.c完全相同。拒絕條件不變；引入提交補上edge_index及低／高區間訊息。P8低／高現行明確斷言要求的tokens在舊base bytes中不存在。
- 報告沒有把exact三差改判pass，也沒有把B′或具名差異政策寫成已核准。A明確維持既有紅燈；B／C需另行裁決，原效能分母與P-189範圍沒有自動改動。在已固定的舊bytes、I22及現行斷言同時保持不變的條件下，未找到可使此gate轉綠的產品修法；此結論限於現行契約，不聲稱證明所有未來設計都不可能。

審查找到並已修正的文件問題：`INTRODUCING_COMMIT.patch` 原本只有診斷相關五檔，REPORT卻容易被讀成整個commit的完整diff。作者現已列出五檔並明確寫「不代表該提交全部檔案」。原patch、collector、FACTS及收件流均未更動；也澄清「維持A」和「沒有採用新B′／具名政策」之間的文字歧義。

最初實質範圍發現保存在 `REVIEW.json`。第二輪 `REVIEW_FINAL.json` 的單一誤報是 reviewer過度精確比對中文句型（預期「整個提交」、實際已正確寫「該提交全部檔案」）；只修reviewer matcher，未要求修改已正確的受審文件。最終通過以 **REVIEW_ACCEPTED.json** 為準。

限制：各場景guards核對原equivalence report，不聲稱從未留存的逐場景guard檔重新推導；這份唯讀歸因不代新的產品撤回／恢復驗收、完整列車驗收或P-189。

最終受審REPORT SHA256：`337c42769598af8c4ca46bf440970e0e3e0fbf767367e773730beca46823b7de`。

最終受審inventory SHA256：`140d3c1c0d24ac7f61fae9beb38c1e03edb84b22f195d99a6a92a126283b4e5b`。

REVIEW_ACCEPTED.json SHA256：`bb74c86a13b68925d4dae7e3714ef88940547e5fd51b319c0ddf36c3a41d0ec3`。
