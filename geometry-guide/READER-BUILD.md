# 正典閱讀器同步與驗證

唯一閱讀器仍是 `geometry-guide/公理層-閱讀器.html`。請勿把診斷頁、設計專案或另存版本當成正典。

## 執行

需要 Python 3 與 Node.js；不需安裝 Python / npm 套件，不連網。

```sh
python geometry-guide/sync_axiom_reader.py
python geometry-guide/sync_axiom_reader.py --check
python tests/test_axiom_reader.py
```

同步器讀取 `公理層.md`、`geometry-guide/公理層-白話.md`，以及版控中的正典 HTML。
既有 HTML 提供版面、互動腳本、歷史例圖與批註資料；同步器從目前 Markdown 重新建立全部條文、白話、子款、段落與導覽。
這是可重現的原位同步流程，不是另一套閱讀器。連續執行的輸出逐位元組相同；不產生第二份 HTML 或 `dist/`。

如需帶入另一份同源批註備份：

```sh
python geometry-guide/sync_axiom_reader.py --review-json /path/to/exported-review.json
```

同 `documentId` 與 `baseDocumentHash` 的資料才可合併；同一批註／提案／修訂 ID 內容衝突時拒絕，不覆蓋其中一方。
未送出草稿也只在無衝突時保留。內容驗證失敗時，不覆寫正典。

## 完整性與追溯

1. `documentHash` 與 blocks 的 `[id, source, separator]` 一致。
2. `clause-data` 與 `axiom-review-data.clauses` 全等。
3. 每條 body / plain 的有序 blocks 串接等於整節全文。
4. 每個 source / originalSource 雜湊正確。
5. 可編輯段落的靜態 DOM textContent 等於閱讀器自己的 `inline(source)` 結果。

此外，body 必須逐字等於獨立讀取的 `公理層.md` 原文，plain 必須等於白話來源，subs 必須重新解析；驗證不從 blocks 自行反推預期值。
測試另有獨立逐行解析器，及「內部雜湊全自洽但違反 SSOT」的故障注入，避免再次出現全文與子款一起重複卻自驗通過。

原文分段互不重複；`separator` 保留來源的換行，可能為單換行、雙換行或空字串，最後一段必為空。
未改文字的段落優先保留原 ID；改版不修改批註的原始快照、不自動 resolve，也不聲稱使用者已確認新的措辭。
若新條文刪除了仍被批註引用的段落而無法保留身份，生成器會拒絕，讓衝突可被明確處理。

歷史例圖與實錄保留原樣，清楚標示未按本次來源重跑，不能充當新功能驗收證據。
CLI 的五道結構驗證不等同真實瀏覽器、iOS 鍵盤或下載行為驗證；實際 UI 驗證結果應另列於交付記錄。

## 範圍

- `sync_axiom_reader.py` 是正典同步入口；`make_axiom_reader.py` 仍只供舊追溯診斷用途。
- 既有正典 HTML 是版本化 UI 模板的一部分；若缺失，從 Git 還原它再同步，不自行製作替代閱讀器。
- 同步不改 `公理層.md`、不重跑幾何例圖、不替使用者採納批註。
- GEO-131/133 見證圖(`geometry-guide/witness/<條號>.svg`,規範見 `witness/規範.md`)由同步器**讀檔嵌入**(引擎樣式與見證圖樣式都換成閱讀器深色,角色色不動),不執行引擎;
  圖的幾何位元組是否仍與夾具/引擎一致,由 `python geometry-guide/witness.py --check` 守。
  見證圖或 manifest 變了就要重跑同步,否則 `tests/test_axiom_reader.py` 的冪等測試會失敗——那是預期的警報。
- 原有 `snapshotAt` / `updatedAt` 是批註歷史時間，保留原值；來源同步以確定性的 `ssot-*` snapshot ID、父 snapshot 與檔案雜湊辨識，不偽造批准事件或當前日期。
