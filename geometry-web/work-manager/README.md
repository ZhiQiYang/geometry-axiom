# Geometry 工作管理

把「下一個能做什麼、誰接手、交付在哪裡」收斂到同一個本機狀態。這是雲端開發環境內可重啟的 CLI 與唯讀繁中面板，不是 24/7 託管服務。未安裝額外套件的 Python 3 即可操作資料與 HTTP；截圖另使用環境已安裝的 Playwright／Chromium。

只修改本目錄。Geometry 產品、共用 writer、正典閱讀器及使用者回報完全分離。既有 [實作佇列](../../geometry-guide/IMPLEMENTATION-QUEUE-20261004.md) 與 [審查佇列](../../geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md) 仍是可引用的原始規格；工具以已校驗事件記錄它們的工作狀態，沒有另外產生一份人工維護的百分比表。

## 啟動與操作

在 repo 根目錄執行：

```sh
python3 geometry-web/work-manager/cli.py --help
python3 geometry-web/work-manager/cli.py import-snapshot geometry-web/work-manager/fixtures/synthetic-demo.json
python3 geometry-web/work-manager/cli.py reconcile
python3 geometry-web/work-manager/cli.py list-ready
python3 geometry-web/work-manager/cli.py list-alerts
python3 geometry-web/work-manager/cli.py serve --port 8765
```

面板網址 `http://127.0.0.1:8765`。HTTP 只綁 loopback，只讀取，沒有公開部署。預設資料目錄是工具下 `.local/`；以 `--data-dir <private-directory>` 指定另一份私有資料。合成 demo 與真隊列請用不同的 data-dir，避免混淆。

更新工具程式後，停止自己的 `serve` 行程（前景終端可按 Ctrl+C），再執行同一啟動指令。執行中的服務會核對程式指紋；程式已變更時回 503，避免舊 API 與新 CLI 各說各話。不停止 Geometry 產品服務。

`import-snapshot FILE` 接受 [schema.json](schema.json) 的單一來源快照；`record-assignment FILE`、`record-result FILE` 各登記一個明示事件。輸出 JSON 可供 dot 直接讀取；重試必須沿用原 event_id，不要每次產生新 ID。工具只登記已決定的派工，不會啟動 agent 或呼叫外部寫入 API。

```sh
python3 geometry-web/work-manager/cli.py record-assignment <private-assignment.json>
python3 geometry-web/work-manager/cli.py record-result <private-result.json>
python3 geometry-web/work-manager/cli.py export <private-backup.json>
python3 geometry-web/work-manager/cli.py --data-dir <new-private-directory> restore <private-backup.json>
python3 geometry-web/work-manager/screenshot.py --url http://127.0.0.1:8765
```

截圖預設留 `.local/screenshots/desktop.png`、`mobile-390.png`，另有帶 state_hash 的 `capture.json`；不會上傳。390px 是真瀏覽器 viewport，並檢查水平溢出；加 `--full-page` 可另取完整長頁。截圖可能含私有任務資料，不得提交。

## 事件最小範例

所有時間使用含時區 ISO 8601。source.version 對該來源遞增，event.version 對同 source／task／kind 遞增。ID 永久穩定；同 ID 不同內容會拒绝整个交易。

```json
{
  "schema_version": 1,
  "source": {
    "id": "operator-example",
    "kind": "operator",
    "version": 1,
    "as_of": "2026-10-06T01:00:00Z",
    "status": "ok"
  },
  "events": [{
    "event_id": "assignment-example-1",
    "task_id": "DEMO-READY",
    "kind": "assignment",
    "version": 1,
    "occurred_at": "2026-10-06T01:00:00Z",
    "data": {"owner_thread": "synthetic-owner", "execution_status": "active"}
  }]
}
```

task 事件定義 title、refs、scope、files、branch、dependencies、approval_constraints、required_acceptance、not_before、head_sha。assignment 記 owner_thread 與 execution_status；result 記 PR、證據與執行終態；github 表達已查核的 PR 觀測。完整實例見合成 fixtures；輸入是 metadata，不接受 task transcript、token、私人原稿或 feedback 內容。

## 狀態與權限界線

- `execution_status` 是執行器狀態，`delivery_status` 是依證據推導的交付狀態。in-progress、issue close 或 test count 都不等於驗收完成。阻塞永遠不算 done。
- 完成需要明列 required acceptance，每項有符合當前 SHA 的通過證據，再加相同 head 的 PR 整合證據。head 改變即使舊 pass 失效。CI 缺 steps 或 runner=0 表示未執行。
- owner 停止但沒有 PR 是待接續；已有 PR 則待審／待驗／待整合。缺 owner、來源失聯、未來日期、依賴 cycle 與 scope 檔案衝突均可查警示。
- `execute` 的批准約束會阻止派工；`merge`／`publish` 等約束不會因執行完成自動解除。工具不批准、不合併、不發布、不重試被拒的外部動作。
- `list-ready` 列出可進行的下一步，可能是唯讀審查，不等於可派出執行器。派工仍核對明示 scope/files、批准、依賴、衝突及來源；操作者接續 blocked 工作時需填 reason 留追溯。`record-result` 不能冒充開工派工。
- 無直接 cloud task API 時使用 validated snapshot，來源明示 `manual_snapshot`、as_of、version。失敗抓取以 error 來源觀測記錄，不清空既有資料。資料不會因網頁 refresh 變成 live。

CLI `reconcile`、HTTP `GET /api/state` 及 UI 使用同一個 `state_hash`。`generated_at` 是讀取時間，不是假造同步時間。UI 用文字節點呈現輸入，安全 URL 白名單，失敗時保留上一份畫面並顯示錯誤。API 拒絕寫入、跨 origin、陌生 Host 與任意檔案路徑。

## 保存與恢復

SQLite transaction 保護完整批次，事件 append-only。export 產生可攜備份與 checksum；restore 先驗證 checksum 和內容，失敗不改原資料。cloud 重啟後若 workspace 仍在，重跑 `serve` 即可；若整個執行環境被重建，必須從先前私存的 export 恢復。工具不保證環境外保存，也不自行上傳私人備份。

`.gitignore` 是工具範圍的允許清單，只收程式、文件及 synthetic fixtures。SQLite、快照、截圖與原始事件不進 git；不要 `git add -f`。一般應保持 `.local/` 目錄 0700、私有資料檔 0600。

## 驗證

```sh
python3 -m unittest discover -s geometry-web/work-manager -p 'test_*.py' -v
python3 geometry-web/work-manager/screenshot.py
```

只跑本工具所需檢查，不以 Geometry 產品測試數字冒充本工具的資料正確性，也不以合成測試冒充任何產品工單完成。
