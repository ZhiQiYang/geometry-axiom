# P-154：模型包版本的網頁載入邊界

`project-store.js:382` 的 `validateModelPackage` 是結構檢查，`pack/unpack` 也只是容器處理；它們本身不呼叫原生版本驗證。正式專案載入的信任邊界在 `ReferenceWorkspace.readProjectContext`，不能把低階 ZIP 讀寫成功當成已載入目前工程。

| 支援的入口 | 到原生驗證的路徑 |
| --- | --- |
| 檔案開啟／importBytes | `reference-workspace.js:1791` → `importProjectData:1886` → `readProjectContext:1807` |
| 本機恢復 | `reference-workspace.js:306` → `readProjectContext` |
| 試改續接點 | `reference-workspace.js:1621` → `readProjectContext` |
| 候選方案 | `reference-workspace.js:1697` → `readProjectContext` |
| 方案目錄內的子快照 | `reference-workspace.js:1835` 遞迴 `readProjectContext` |

`readProjectContext:1819–1823` 對每份模型先 `await verifyStoredModel(model)`，之後才把模型放入隔離 context。`verifyStoredModel:1745` 逐包處理 space、volume、clearance、walls，以及 /2 的 timbers；每包先 POST `/model/verify`。`serve.py:694–695` 呼叫原生建模執行器的 `verify_package`，舊版整卡能力由 B1 防線回 `UNSUPPORTED/AXIOM_VERSION`。驗證與來源重播完成後，才可能進入場景 upload/prepare、upload/confirm 與 context 替換。

新建／修改的 `addSpaceModel`、`updateSpaceModel` 是內部提交 API，接收 `/model/space-preview` 或模型更新流程的原生產出；它們不是外部模型包檔案的開啟入口。Undo/Redo 保留已建立／已驗證 context。外部保存資料的上述開啟、恢復及方案入口共用同一條原生驗證路徑，因此本輪未在結構檢查器複製 Python 的版本表或另加第二套版本政策。

`probe_model_admission.cjs <新輸出目錄>` 使用既有測試 VM harness、真 `reference-workspace.js` 與私有真服務。它把正式範例模型包改為採納前精確版本加整卡能力，以正常 pack 重算容器能力與格式。結構檢查／unpack 通過後，真正 import 只呼叫一次 `/model/verify`，取得原生 `AXIOM_VERSION`，且 context、完整狀態、history、模型數及原生 dump 全部不變。

`--omit-verification` 僅在 VM 內撤除一般的 `await verifyStoredModel` 呼叫，不修改 repo 產品檔。在獨立私有服務上，探針轉紅於具名 `P154_MODEL_ADMISSION` 斷言，並觀察到 upload/prepare、upload/confirm 與模型進入 context。這證明探針確實覆蓋驗證邊界；原始結果不是單靠靜態搜尋或受控成功回覆推測。實跑 head、完整請求紀錄與原件以 PR 的交付證據為準。
