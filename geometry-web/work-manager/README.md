# Geometry 工作管理

把「下一個能做什麼、誰接手、交付在哪裡」收斂到同一個本機狀態。這是雲端開發環境內可重啟的 CLI 與唯讀繁中面板，不是 24/7 託管服務。未安裝額外套件的 Python 3 即可操作資料與 HTTP；截圖另使用環境已安裝的 Playwright／Chromium。

只修改本目錄。Geometry 產品、共用 writer、正典閱讀器及使用者回報完全分離。既有 [實作佇列](../../geometry-guide/IMPLEMENTATION-QUEUE-20261004.md) 與 [審查佇列](../../geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md) 仍是可引用的原始規格；工具以已校驗事件記錄它們的工作狀態，沒有另外產生一份人工維護的百分比表。

## 啟動與操作

在 repo 根目錄執行：

```sh
python3 geometry-web/work-manager/cli.py --help
python3 geometry-web/work-manager/cli.py --data-dir /tmp/geometry-work-demo import-snapshot geometry-web/work-manager/fixtures/synthetic-demo.json
python3 geometry-web/work-manager/cli.py reconcile
python3 geometry-web/work-manager/cli.py list-ready
python3 geometry-web/work-manager/cli.py list-ready --mode read_only
python3 geometry-web/work-manager/cli.py list-ready --mode write
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

| 欄位 | 契約 |
| --- | --- |
| `source` | `id`、`kind`、遞增 `version`、`as_of`、`status`；可加 `source_sha`、`url`、`error`。`manual_snapshot` 明示人工核對，不代表 live API。 |
| `event` | 永久 `event_id`、穩定 `task_id`、`kind`、同 source/task/kind 遞增 `version`、`occurred_at`、`data`。 |
| `task.data` | `title`、`refs[{kind,url,number?}]`、`scope`、repo-relative `files[]`、`branch`、`dependencies[]`、`required_acceptance[]`、`approval_constraints[]`、`not_before`、完整 `head_sha`；必要時加 `head_tree_sha`。 |
| `assignment.data` | `owner_thread`、`execution_status`、`reserved`、`reason`、`files`。active 必須有 owner；`record-assignment` 另核對範圍與派工條件。 |
| `result.data` | `head_sha`、`execution_status`、`owner_thread`、`summary`、`pr`、`evidence[]`、`completed_actions[]`。 |
| `pr` | `number`、`url`、`head_sha`、`merged`、`merged_head_sha`、`merge_commit_sha`、`draft`、`review_state`、獨立的 `reviewed_sha`、`ci[]`。aggregate approved 缺少正確 reviewed_sha 仍待核。 |
| `evidence[]` | 不可改寫的 `id`、`criterion`、`kind`、`timestamp`、原始 `sha`、`result`，可加 `url`、`summary`、`expires_at`、`runner_id`、`steps`。新嘗試必須新 ID。 |
| `approval_constraints[]` | `action`、`status: required/granted/denied`、`reason`、`scope: action/completion`；省略 scope 預設 completion，未批准就不算完成、不釋放依賴。 |
| `completed_actions[]` | `action`、當次 `next_action_pin` 填入的 `input_pin`、`timestamp`、`summary`；只消耗已核對的同一輸入，不授權外部動作。 |

登記一次核對的最小 result data：

```json
{
  "completed_actions": [{
    "action": "verify_acceptance",
    "input_pin": "0000000000000000000000000000000000000000000000000000000000000000",
    "timestamp": "2026-10-06T01:00:00Z",
    "summary": "合成範例：已核對仍缺 Windows 證據，等待新輸入"
  }]
}
```

上方 pin 是佔位符，實際操作必須取 `inspect TASK` 當次回傳的 `next_action_pin`，包在完整 result 事件快照後交 `record-result`。收據不會把未知驗收改成通過；head、owner、驗收或其他相關輸入改變後會產生新 pin。

## 狀態與權限界線

- `execution_status` 是執行器狀態，`delivery_status` 是依證據推導的交付狀態。in-progress、issue close 或 test count 都不等於驗收完成。阻塞永遠不算 done。
- 完成需要明列 required acceptance、有效通過證據、獨立綁定 reviewed_sha 的審查與相同 head 的 PR 整合證據，以及未被 completion 約束阻擋。head 改變即使舊 pass 失效。CI 缺 steps 或 runner=0 表示未執行。
- 同 criterion 依目前 head 選取證據；較晚到達的舊 head pass 不會覆蓋現在 head 的證據。現在 head 的較新失敗／過期證據仍會讓驗收失效。同 task/evidence ID 的內容衝突會整批拒絕。
- 同樹測試只接受 `kind=local_test` 明示 `tree_sha` 與 `equivalent_head_sha`，且與 task 的完整 tree/head 相符；原始 tested SHA 保留。這不能替代 CI 或 source review 的 exact-head 證據。`postmerge_test` 可綁已確認的 `pr.merge_commit_sha`，不把 merge commit 改寫成 PR head。
- owner 停止但沒有 PR 是待接續；已有 PR 則待審／待驗／待整合。缺 owner、來源失聯、未來日期、依賴 cycle 與 scope 檔案衝突均可查警示。
- `execute` 的批准約束會阻止派工；`merge`／`publish` 等約束不會因執行完成自動解除。`scope=action` 可單獨限制未來操作，保留已完成整合的歷史事實；不能用未填 scope 的 hold 放行完成。工具不批准、不合併、不發布、不重試被拒的外部動作。
- `list-ready` 分 `read_only`／`write`，並回傳 `ready_counts`；`next_action_mode=wait` 的 owner 執行中／待批准項目不算可派工。已記錄的同輸入核對不再重複排隊。派工仍核對明示 scope/files、批准、依賴、衝突及來源；操作者接續 blocked 工作時需填 reason 留追溯。`record-result` 不能冒充開工派工。
- 無直接 cloud task API 時使用 validated snapshot，來源明示 `manual_snapshot`、as_of、version。失敗抓取以 error 來源觀測記錄，不清空既有資料。資料不會因網頁 refresh 變成 live。

成功的新快照若再次包含相同 immutable event，可提升該事件的觀測水位與任務 `last_verified_at`，不新增事件、不修改原始 occurred_at。局部快照未包含的任務不會一起變 fresh，失敗 fetch 也不刷新上次成功核對時間。

CLI `reconcile`、HTTP `GET /api/state` 及 UI 使用同一個 `state_hash`，包含 freshness 的顯示狀態；`payload_hash` 排除來源核對時間，表示工作資料的語義內容。`generated_at` 是讀取時間，不是假造同步時間。UI 用文字節點呈現輸入，安全 URL 白名單，失敗時保留上一份畫面並顯示錯誤。API 拒絕寫入、跨 origin、陌生 Host 與任意檔案路徑。

## 保存與恢復

SQLite transaction 保護完整批次，事件 append-only；完整投影也在提交前驗證，錯誤不留下無法重開的半成品。export 產生可攜備份與 checksum；restore 先驗證 checksum 和內容，失敗不改原資料。cloud 重啟後若 workspace 仍在，重跑 `serve` 即可；若整個執行環境被重建，必須從先前私存的 export 恢復。工具不保證環境外保存，也不自行上傳私人備份。

`.gitignore` 是工具範圍的允許清單，只收程式、文件及 synthetic fixtures。SQLite、快照、截圖與原始事件不進 git；不要 `git add -f`。一般應保持 `.local/` 目錄 0700、私有資料檔 0600。

## 驗證

```sh
python3 -m unittest discover -s geometry-web/work-manager -p 'test_*.py' -v
python3 geometry-web/work-manager/screenshot.py
```

只跑本工具所需檢查，不以 Geometry 產品測試數字冒充本工具的資料正確性，也不以合成測試冒充任何產品工單完成。
