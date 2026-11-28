# T58：X5-C1 在真瀏覽器復原後未保住相同的專案附件

**不採入本片。** 依 #455 留言 7238557844 第 5 點，P 後 P2056 未綠，已移出整片 T／P。這是退片重現說明，不是產品實作、成本或 CI 收據。

## 重現輸入

取 #205 留言 7237870102 的分段，依序串接、解碼；唯一套用基底是 PR #468 的 `077a3aba9e09d9bc43fdc38bef4ab537a4fefe88`。T（253662 bytes，SHA-256 `ebbc6bb2dd6976c1afd33b4ca6e0050effad6b322109523dee9cd6358870d33a`）及 P（131885 bytes，SHA-256 `d4e318ccc09307801e492d064a9d054e019715755d75ff4a972bb10452395064`）依序 apply-check／apply 均為 0；31＋15 檔逐檔符合證據包 manifest。T 的 Native、Node、W、runtime 均紅在指定斷言。P 後四者轉綠，九項來源撤回均為 0／1／0。

在**原樣套上 T、P 的工作樹**上使用獨立的本機服務（不要連到使用中的專案）。以下為 1400 px 原段的重現命令；P2056 自己切換視窗大小：

```sh
ulimit -s 16384
npm run build
export GEOMETRY_TEST_URL=http://127.0.0.1:18839/
export GEOMETRY_FEEDBACK_DIR="$(node -p 'require("node:os").tmpdir()')/t58-fb"
export GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$GEOMETRY_FEEDBACK_DIR"
python3 -u geometry-web/start_local.py --port 18839 >/tmp/t58-server.log 2>&1 &
server=$!; trap 'kill "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT
for n in $(seq 1 30); do
  kill -0 "$server" || exit 1
  python3 -B geometry-web/runtime_version.py --probe 18839 >/dev/null 2>&1 && break
  sleep 1
done
python3 -B geometry-web/runtime_version.py --probe 18839 >/dev/null || exit 1
GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P2056 node geometry-web/cdp_test.js
```

## 第一個失敗點

非 root（uid 1002），Google Chrome 158.0.8127.36，runtime `fresh:true`。最後一條命令 exit **1**；下列為原始輸出節錄：

```text
P2056 OLD_V2_OWNER_AND_FRESH_FACE 1400 ✓
P2056 DIRECT_N1_PIN 1400 ✓
P2056 G_ALL_74_MEMBERS 1400 ✓
P2056 NATIVE_R41_LAYER_VERTICES 1400 ✓
P2056 CANCEL_ZERO 1400 ✓
P2056 CONFIRM_ONE_HISTORY 1400 ✓
P2056 FORMAL_RC_NO_ADOPTION_RECEIPT 1400 ✓
P2056 UNDO_WHOLE_COLUMN_GROUP 1400 ✗ false
FATAL: P2056 assertion failed: UNDO_WHOLE_COLUMN_GROUP 1400 false
FATAL_NETWORK: {"failures":[],"pendingAssets":[]}
```

原段 `passedAssertions:14`、`failedAssertions:1`、`uncaughtBrowserExceptions:0`。不是進場失敗；舊骨架、新面、來源明選、74 支預覽、一筆確認都已跑到。原 T 的 `geometry-web/canvas_sections/P2056.js:160` 在點擊面內復原並等待空閒後，要求 `undone.world===before.world && same(undone.features,committed.features)`。它失敗即停，原段沒有進到 390、重做及存檔重開。

- **390 px 另測**：只在樹外測試副本另取段名 `P92056`，以原 `stage-module` 產生候選，把相同兩個寬度的執行次序對調。產品服務仍跑原 T＋P。`GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P92056 node geometry-web/cdp_test.js` → exit 1，`P92056 UNDO_WHOLE_COLUMN_GROUP 390 ✗ false`，也是 14 項通過後第 15 項失敗。
- **拆開合取式定位**：樹外 `P92057` 診斷沿用 1400 優先，只為同一斷言多輸出當次快照比較。`GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P92057 node geometry-web/cdp_test.js` → exit 1：`P92057 UNDO_WHOLE_COLUMN_GROUP 1400 ✗ {"worldMatch":true,"featuresMatch":false,"beforeBytes":6199,"undoBytes":6199,"removed":[],"added":[]}`。World dump 已回到預覽前，但專案附件與確認後不全等。尚不能由此指認哪一筆附件或哪一層造成差異。

兩個診斷段都不是交付段、不是 P2056 收據，不採入。重出時應分開比對按復原前後的 World 與專案附件，保留原先的兩項相等要求。既有 N1／R03 局部瀏覽器回歸（P4314 的 44 項、P205 的 25 項）均為 exit 0，不能替代 P2056。
