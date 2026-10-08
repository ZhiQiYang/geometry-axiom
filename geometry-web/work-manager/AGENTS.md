# 工作工具的範圍與資料

本目錄是 Geometry 工作管理工具，不是 Geometry 產品介面或第二份公理閱讀器。
只更動本目錄，不碰共用 writer 的產品檔或既有排程來源文件。

SQLite、匯入快照、owner thread、原始事件、截圖、匯出備份與本機路徑屬私有執行資料。
預設放 `.local/`；不得 force-add。提交只含工具程式、文件及 `fixtures/synthetic*.json`。
合成 fixture 不得含真 cloud task ID、私人原稿或使用者回報。

工作狀態只從 store.py 產生；CLI、HTTP API 和 UI 共用其 state_hash。
匯入不是授權；工具不得發 GitHub 寫入、派出 agent、批准、merge 或發布。
新增來源先校驗，來源不可用時保留舊資料並明示來源時間，不假裝常駐 live。
測試只跑本工具，UI 驗 desktop 與 390px；不使用產品 feedback 目錄。
