# 最終 owner／browser gates：待執行命令

2026-10-17；本文件只做原始入口核對，**未執行測試、WSL、native 或瀏覽器**。範圍固定為 `tests/run_all.py:345–371` 的 **1 owner + 22 browser**，另加 fragment-heap 診斷及 grid-inspector native 變異探針，共 25 個入口。Claude 的正式七項 train 維持原分工；不擴展其他 `NODE_EXCLUDED`。

初次核對基底為 `12260aeb667f86a773d37e24d026dc844e6afc2f`。root 隨後將四支 harness 的啟動相容性修正提交至 `43305271770760a690e360ce18ce11cc07f35ea2`：multi／rule app／rule races 支援 `GEOMETRY_CHROME`，feedback 支援 `GEOMETRY_CHROME_FLAGS`；本文件已讀回修改，所有 browser runtime 仍未跑。**先由 owner 指定最終完整 SHA、凍結 clean checkout，再執行下列命令。** 若候選繼續變更，舊收據不可改標成新版本。

## 1. 一次性前提與 native 準備（Linux／WSL bash）

只在已分配的 WSL 執行時段依序跑；保留原有共享鎖／排程紀律。所有服務、runner、binary receipt 必須位於同一個可互見 Linux PID 的環境，使用一致的 WSL checkout 路徑。不要把下列命令直接貼進 PowerShell。`FINAL_SHA` 由最終來源 owner 指定，不自動把目前 HEAD 當最終版本。

```bash
set -euo pipefail
export ROOT=/mnt/d/geometry-axiom-work/geo261-integration
cd "$ROOT"
: "${FINAL_SHA:?Set the final approved full commit SHA first}"
test "${#FINAL_SHA}" -eq 40
test "$(git rev-parse HEAD)" = "$FINAL_SHA"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
RUN=$(mktemp -d /tmp/geo261-owner-final.XXXXXX)
export RUN
export TMPDIR="$RUN" PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
export NODE_PATH=/mnt/c/Users/Yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules
export PYTHONPATH=/var/tmp/geo261-python-playwright-1.62.0-v2/venv/lib/python3.12/site-packages
export GEOMETRY_CHROME=/opt/google/chrome/chrome
export GEOMETRY_CHROME_FLAGS='--no-sandbox --disable-dev-shm-usage'
export GEOMETRY_EXPECTED_SHA="$FINAL_SHA" GEOMETRY_ISOLATED_SERVICE=1 GEOMETRY_REQUIRE_CLEAN=1
export GEOMETRY_REPO="$ROOT" GEOMETRY_VERIFY_ROOT="$ROOT" GEOMETRY_RUNTIME_ROOT="$ROOT"
unset PYTHONOPTIMIZE GEOMETRY_ACCEPT_DIRTY GEOMETRY_ROOM_SCENARIOS
unset GEOMETRY_GRID_WORKSPACE_SOURCE GEOMETRY_TEST_REFERENCE_WORKSPACE GEOMETRY_GRID_INSPECTOR_SOURCE
unset GEOMETRY_BRIDGE_WSL GEOMETRY_MODEL_BASE_WSL_DISTRO GEOMETRY_MANAGED_PREVIEW
git rev-parse HEAD HEAD^{tree} > "$RUN/source.txt"
node --version > "$RUN/node-version.txt"
python3 --version > "$RUN/python-version.txt"
node -p 'require.resolve("playwright")' > "$RUN/node-playwright.txt"
python3 -c 'from playwright.sync_api import sync_playwright' > "$RUN/python-playwright.txt" 2>&1
ulimit -s 16384
python3 geometry-web/start_local.py --build-only --binary-dir "$RUN/bin" > "$RUN/build.log" 2>&1
export GEOMETRY_TEST_CORE="$RUN/bin/core"
export GEOMETRY_TEST_BRIDGE="$RUN/bin/bridge" GEOMETRY_BRIDGE="$RUN/bin/bridge"
export GEOMETRY_BRIDGE_EXECUTABLE="$RUN/bin/bridge" GEOMETRY_MODEL_UPDATE_BRIDGE="$RUN/bin/bridge"
export GEOMETRY_SCENARIO_BRIDGE="$RUN/bin/bridge" GEOMETRY_MODEL_BASE="$RUN/bin/model-base"
export GEOMETRY_SCENARIO_BASE="$RUN/bin/model-base"
```

每條前提命令均須成功才往下。已知 Node 24、CJS Playwright／playwright-core **1.62.1** 與 Chrome 路徑來自既有環境資料；本 agent 沒有重新探測。root 的 00:38 P1 preflight 已確認 `/usr/bin/python3.12` 為 3.12.3、`find_spec('playwright')` 為 None。P1 dependency v1 未能從官方 PyPI 取得指定的 Python Playwright 1.62.1，原始失敗保留；v2 已標為 **PREPARED**：Python Playwright **1.62.0**、greenlet 3.5.6、pyee 13.0.1、typing_extensions 4.16.0。每個 wheel 先核對官方 SHA，再離線安裝至 `/var/tmp/geo261-python-playwright-1.62.0-v2/venv`，`pip check` 已通過；未啟動 browser／driver、未跑產品測試。證據：`p1/python-playwright-prep-v2/result`，summary SHA-256 前綴 `da1d6f6e…`。

上節只在本次 shell／子行程設定 `PYTHONPATH` 指向該 venv 的 Python 3.12 site-packages，不改 system/repo，也不改 `python3` 指令的解析。**系統 `/usr/bin/python3` 3.12.3 的 import-only 映射已實跑一次成功**：Playwright sync_api、greenlet（含 cp312 extension）、pyee、typing_extensions 均從指定 site-packages 解析，未啟動 Playwright driver／browser。收據：[map-check-v2 summary](D:/geometry-axiom-work/geo261-evidence/p1/python-playwright-map-check-v2/result/summary.json)，SHA-256 `8bef59faa0e05781d104e601d32d6024dd8df951fcbdc138a5132d6f06b5cdbb`。先前 map-check-v1 因外部檢查器命名 `inspect.py` 遮蔽標準庫而 exit 1，其失敗附件保留；v2 使用新目錄及 `probe_imports.py`，sys.path 不含 v1。這未執行未來 namespace 的 `python` alias；正式 gate 前仍保留實際 interpreter／套件來源並通過上列 import。Python 1.62.0 與既有 Node 1.62.1 分開記錄，不能用其中一者的準備結果代替另一者或冒充 browser gate 通過。

同次 preflight 的 host 沒有 `python`。`test_rule_case_app_races.js:9` 硬編此名稱，`PYTHON=python3` 不能覆寫；root 的既定不可變私有 namespace 會在取得鎖後建立指向 3.12 的 `python` symlink，仍須在該 namespace 內以 `python --version` 核對後才跑 races，不另外修改 host。K2a helper 硬編 `python3`、`ps --ppid`、`/proc`，不能直接改用 Windows runner。

既有 vendor（fflate、PDF.js／CMap／fonts）、夾具及 CJK 字型需在最終凍結前備妥；`start_local.py` 不會補裝這些資源。缺項保留 blocked，不臨時下載或替換產品資產。native 輸出及 sidecar 全在 TEMP；不要用別的 checkout／舊 binary 冒充 freshness。

## 2. 一般產品服務：每一列建立新的專屬服務

以下 20 列各跑一次。每次先選表中 `ROW`，建立該列新目錄；不要重用非空輸出。`18871` 為待檢查的專屬 port，若被占用，改成其他空閒非 8765 port，不能停止占用者。服務的 feedback 與 runner 必須是同一目錄。

```bash
export ROW=k2a-drafts
export GATE_RUN="$RUN/$ROW"
test ! -e "$GATE_RUN"
mkdir -m 700 "$GATE_RUN"
export GEOMETRY_FEEDBACK_DIR="$GATE_RUN/feedback"
export GEOMETRY_TEST_URL=http://127.0.0.1:18871/
mkdir "$GEOMETRY_FEEDBACK_DIR" "$GATE_RUN/k2a"
set +m
setsid python3 geometry-web/start_local.py --port 18871 --binary-dir "$RUN/bin" > "$GATE_RUN/service.log" 2>&1 &
SERVICE_PID=$!
printf '%s\n' "$SERVICE_PID" > "$GATE_RUN/service.pid"
```

等本列服務完成啟動，再做 preflight；探測失敗不得啟動 browser。尤其 pan 的內部 `check()` 只記錄身分錯誤，之後仍會 `api('reset')`（`room_outline_pan_browser.js:23,32–34`），外層必須先擋住錯服務。

```bash
python3 geometry-web/runtime_version.py --probe 18871 > "$GATE_RUN/runtime-before.json"
test "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pid"])' "$GATE_RUN/runtime-before.json")" = "$SERVICE_PID"
ps -o pid,ppid,pgid,args -p "$SERVICE_PID" > "$GATE_RUN/service-process.txt"
RELEASE=(python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$GATE_RUN/receipt" --)
```

`start_local.py` 的 `execve` 保持啟動 PID；保留 service log、PID、`/runtime`。runner 首次取得 native 後，核對本服務直接子行程的 `/proc/<bridge-pid>/exe` 及 hash 是否為 `$GEOMETRY_TEST_BRIDGE`，把觀察記入本列證據。K2a helper 已自行保存此 live-child 核對；其他列須由執行 owner 觀察。`release_gate.py` 驗的是指定 binary 與 sidecar，不能單靠它宣稱 live native 身分已證明。

表內命令包含完整 release wrapper 呼叫。`N` 是登錄的預期斷言數，**不是本文件的實跑數**。wrapper 對這些入口只記 command-only／`completionVerified:false`；須另外讀原 gate 的結果、完整輸出及實際 census，不能只看 exit 0。

所有前提／PID probe 保持 `set -euo pipefail`；任何失敗都停止該 shell，不執行表內命令。只有本列所有 preflight（K2a ZIP 含第二服務）成功後，先執行 `set +e`，**只執行一列表內命令**，然後立刻執行以下三行保存失敗碼並恢復 fail-fast；再進行本列清理。不可在 `set +e` 期間做下一列 preflight。

```bash
GATE_EXIT=$?
set -e
printf '%s\n' "$GATE_EXIT" > "$GATE_RUN/exit-code.txt"
```

| ROW | N | 待執行命令 | 原始輸出／特別前提 |
|---|---:|---|---|
| k2a-drafts | 27 | `"${RELEASE[@]}" env GEOMETRY_BROWSER_RECEIPT="$GATE_RUN/k2a/result" node tests/k2a_drafts_browser.cjs` | K2a preflight／final receipt；另寫死 `/tmp/k2a-chooser-1280.png`、`390.png`，需獨占 `/tmp`，跑後保留至本列目錄。 |
| k2a-native | 42 | `"${RELEASE[@]}" env GEOMETRY_BROWSER_RECEIPT="$GATE_RUN/k2a/result" node tests/k2a_native_browser.cjs` | cold page 與 parameter page 仍用同一服務。 |
| k2a-source-repin | 14 | `"${RELEASE[@]}" env GEOMETRY_BROWSER_RECEIPT="$GATE_RUN/k2a/result" node tests/k2a_source_repin_browser.cjs` | K2a receipt＋stdout。 |
| k2a-zip | 89 | `"${RELEASE[@]}" env GEOMETRY_BROWSER_RECEIPT="$GATE_RUN/k2a/result" GEOMETRY_FRESH_TEST_URL=http://127.0.0.1:18872/ node tests/k2a_zip_browser.cjs` | 必須另開下述第二個空服務；兩份 receipt 的 session 必須不同。 |
| k2a-rule-repin | 35 | `"${RELEASE[@]}" env GEOMETRY_BROWSER_RECEIPT="$GATE_RUN/k2a/result" node tests/k2a_rule_repin_browser.cjs` | K2a receipt＋stdout。 |
| room-multi | 34 | `"${RELEASE[@]}" env GEOMETRY_MULTIROOM_OUT="$GATE_RUN/evidence" node tests/room_multi_candidate_browser.js` | results／screens；Chrome override 依賴本次啟動修正已進最終 commit。 |
| section-profile | 68 | `"${RELEASE[@]}" env GEOMETRY_SECTION_EVIDENCE="$GATE_RUN/evidence" node tests/test_section_profile_browser.js` | 1440／390、結果／ZIP／screens；OUT 外置且 new/empty。 |
| q38-save | 18 | `"${RELEASE[@]}" env GEOMETRY_Q38_SAVE_OUT="$GATE_RUN/evidence" python3 tests/integration/q38_save_roundtrip.py` | Python Playwright；`result.json`、`run.json`；新 browser，仍同一 server session。 |
| model-history | 35 | `"${RELEASE[@]}" env GEOMETRY_MODEL_HISTORY_OUT="$GATE_RUN/evidence" python3 tests/integration/model_library_history_browser.py` | Python Playwright；`result.json`／fixtures／screens；真 Web Locks。 |
| save-roundtrip | 33 | `"${RELEASE[@]}" env GEOMETRY_SAVE_EVIDENCE="$GATE_RUN/evidence" GEOMETRY_CDP_PORT=9422 node tests/integration/save_roundtrip_acceptance.cjs` | Node 22+／repo qa_cdp；9422 必須空；fresh profiles，服務 PID/session 保持相同。 |
| rule-app | 76 | `"${RELEASE[@]}" env GEOMETRY_RULE_CASE_APP_OUT="$GATE_RUN/evidence" node tests/test_rule_case_app_browser.js` | `results.json`／真 ZIP／screens；Chrome override 依賴本次修正。 |
| rule-races | 30 | `"${RELEASE[@]}" env GEOMETRY_RULE_CASE_RACE_OUT="$GATE_RUN/evidence" node tests/test_rule_case_app_races.js` | `results.json`；需要 `python`；內部方案 B 的新 session，不是第二個 URL。 |
| room-keyboard | 396 | `"${RELEASE[@]}" env GEOMETRY_ENTER_OUT="$GATE_RUN/evidence" GEOMETRY_ENTER_CASES=full node tests/room_outline_keyboard_browser.js` | 必須 full，不能設 core；結果／screens。 |
| room-acceptance | 253 | `"${RELEASE[@]}" env -u GEOMETRY_ROOM_SCENARIOS GEOMETRY_ROOM_EXTRA_CASES=1 GEOMETRY_ROOM_ACCEPTANCE_DIR="$GATE_RUN/evidence" node tests/room_outline_acceptance_browser.js` | 預設全部十情境＋extra；結果／screens。 |
| room-pan | 32 | `"${RELEASE[@]}" env GEOMETRY_PAN_OUTPUT="$GATE_RUN/evidence" node tests/room_outline_pan_browser.js` | `results.json`；preflight 不可省略；reset／pointercancel 為原 harness 的明示操作。 |
| room-worker | 78 | `"${RELEASE[@]}" env GEOMETRY_WORKER_OUTPUT="$GATE_RUN/evidence" node tests/room_outline_worker_browser.js` | `results.json`；真 Worker＋明示 late-consumer injection。 |
| grid-reader | 34 | `"${RELEASE[@]}" env GEOMETRY_RULE_READER_OUT="$GATE_RUN/evidence" node tests/test_grid_rule_reader_browser.js` | `results.json`／真 ZIP／screens。 |
| evidence-adapter | 67 | `"${RELEASE[@]}" env GEOMETRY_EVIDENCE_TEST_DIR="$GATE_RUN/evidence" node geometry-web/evidence_links_browser_check.js` | stdout JSON 的 passed／screens；injected-memory attachment backend，不能替代下列 integration。 |
| evidence-integration | 110 | `"${RELEASE[@]}" env GEOMETRY_EVIDENCE_TEST_DIR="$GATE_RUN/evidence" node geometry-web/evidence_links_integration_test.js` | `results.json`／errors／coverage／screens；正式 PDF／ZIP／history。 |
| raw-provenance | 207 | `"${RELEASE[@]}" env GEOMETRY_RAW_PIN_OUT="$GATE_RUN/evidence" python3 geometry-web/grid_raw_provenance_browser_test.py` | Python Playwright；`result.json` completed/passed/failed/exceptions；1290／390。 |

K2a ZIP 的第二個服務，在本列 preflight 後、gate 前啟動；記下獨立 PID，確認 runtime root/version 相同且 PID/session 與第一服務不同。不能用第二個 tab 或新 context 代替。

```bash
setsid python3 geometry-web/start_local.py --port 18872 --binary-dir "$RUN/bin" > "$GATE_RUN/fresh-service.log" 2>&1 &
FRESH_SERVICE_PID=$!
printf '%s\n' "$FRESH_SERVICE_PID" > "$GATE_RUN/fresh-service.pid"
```

啟動完成後執行 `python3 geometry-web/runtime_version.py --probe 18872 > "$GATE_RUN/fresh-runtime-before.json"`，核對其中 PID 等於 `FRESH_SERVICE_PID`。K2a ZIP helper 會再驗兩服務並各自寫前後 receipt。

每列結束保留原始 terminal exit、receipt、gate census、runtime／process／feedback。核對 `$SERVICE_PID` 仍是本列且 group leader，再以 `kill -TERM -- "-$SERVICE_PID"` 停止自己建立的 group，`wait "$SERVICE_PID" || true` 並檢查已記錄的服務／bridge 已退出；K2a 第二服務同理。被 TERM 結束的服務 wait 狀態不算 gate exit。若 preflight 失敗導致 shell 先結束，只能依本列已記錄的 PID/command 核對並清理自己啟動的 group，不可用錯誤 runtime 的 PID 決定停止對象。`set +m` 關閉本 shell 的 job control，使 `setsid` 不因背景 job 已是 group leader 而另 fork，PID 仍須以 runtime 核對。不得廣域 `pkill`、停止使用者服務或清 browser storage。Save helper 的 `close()` 仍含 Windows `taskkill`（`qa_cdp.js:274`）且保留明示 profile；WSL 執行 owner 須核對自有 Chrome 已退出，保留本次私有 TMPDIR，不因它回傳便宣稱清理完成。

## 3. 三個不同生命週期的入口

它們不使用上節的 `RELEASE` prefix，也不拿另一服務的 `/runtime` 當身分證明。各自建立新的 `$GATE_RUN`（同上 `ROW`／mkdir／feedback 準備，不啟動一般 app 服務），保留終端輸出與 exit。前提成功後，同樣只在單一 gate 命令前 `set +e`，緊接著用上節三行保存退出碼並恢復 `set -e`。

| ROW／N | 待執行命令 | 服務與保留證據 |
|---|---|---|
| issue77-owner／5 | `env PYTHON=python3 GEOMETRY_OWNER_GATE_DIR="$GATE_RUN/evidence" GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER="$ROOT/tests/integration/wp60_actual_owner_adapter.js" node tests/integration/issue77_attachment_owner.js > "$GATE_RUN/command.log" 2>&1` | 真 adapter 自選 port、自啟獨立產品服務／browser；驗 receipt-backed bridge/base 與 runtime root/fresh。保留 TAP **5 tests**、`service.log`、`evidence.json`、feedback；4 條 OWNER 診斷不另加成 9。缺 adapter 是 exit 3 pending，不能算 pass。原 adapter 未保存結尾 runtime/live bridge hash/完整退出觀察，執行 owner 另核對其自啟程序結束，不能把輸出擴大宣稱為完整 lifecycle receipt。 |
| feedback-resize／38 | `env GEOMETRY_PYTHON=python3 node geometry-web/feedback_resize_observer_test.js --repo "$ROOT" --keep > "$GATE_RUN/command.log" 2>&1` | 自選兩 port、自啟產品服務及 Chrome；不需 Playwright。繼承 fresh `GEOMETRY_BRIDGE` 和 Chrome／flags。`--keep` 必須保留自建 TEMP feedback/profile；從 stdout 保存 `[start]`、`[identity:start/end]`、`[keep]` 路徑及 38 項完成數。未帶 keep 會刪證據。 |
| rule-workbench／91 | `env GEOMETRY_RULE_CASE_TEST_URL=http://127.0.0.1:18873/ GEOMETRY_RULE_CASE_BROWSER_EVIDENCE="$GATE_RUN/evidence" node tests/rule-case-workbench-browser.cjs > "$GATE_RUN/command.log" 2>&1` | 先在另一個已設同環境的終端執行下列 standalone server。它不是一般 app 根頁；`/runtime` 為 404，`release_gate.py` 不適用。 |

```bash
python3 geometry-web/rule_case_workbench_standalone.py --port 18873 > "$GATE_RUN/standalone-service.log" 2>&1
```

standalone 的 `GEOMETRY_TEST_BRIDGE` 必須是同一 fresh receipt-backed binary；服務只綁 loopback，port 被占即停，不替換他人。保留凍結 SHA/tree、命令、PID、native 路徑/sidecar/hash、stdout 與 `browser.json`。其 open/execute 協定有 session／native identity／cleanup 欄位，但原 browser artifact 只留 `{url,checks,results}`，沒有完整 runtime／live-native／cleanup receipt；結果必須明載這個證據邊界，不拿別的服務補造。完成後只在啟動此服務的終端 Ctrl+C，核對其 native 子行程結束。

三個入口都能使用最終 own source；**owner gate 的真 adapter 已在 repo，不必等待外部 owner 注入**。本表不新增 owner 替身。歷史十項原始腳本與 Claude 七項 train 的執行歸屬仍由既定 owner 負責。

## 4. 兩個 native 診斷入口

兩者依序執行於同一最終 clean checkout，各用新輸出目錄；不需要產品服務，不套 URL wrapper。原生失敗、逾時或依賴缺失不可記成斷言成功。

```bash
test ! -e "$RUN/fragment-heap"
set +e
python3 tests/diagnostics/run_fragment_heap_gate.py --output "$RUN/fragment-heap" > "$RUN/fragment-heap.log" 2>&1
FRAGMENT_EXIT=$?
set -e
printf '%s\n' "$FRAGMENT_EXIT" > "$RUN/fragment-heap.exit"
test ! -e "$RUN/grid-inspector-mutation"
set +e
python3 tests/diagnostics/grid_inspector_mutation_probe.py --out "$RUN/grid-inspector-mutation" --native > "$RUN/grid-inspector-mutation.log" 2>&1
GRID_MUTATION_EXIT=$?
set -e
printf '%s\n' "$GRID_MUTATION_EXIT" > "$RUN/grid-inspector-mutation.exit"
```

| 入口 | 驗收／平台限制 |
|---|---|
| fragment heap | Linux `resource/RLIMIT_STACK`、`cc`（或明確 `--cc`），hard limit 至少 16 MiB；自行在 TEMP 建 core／bridge／fault bridge，保存 `receipt.json`、`commands.json`、binary/source hash 與每階段 raw logs。原有五階段 build/stack/OOM 必須完整成功；兩個 malloc OOM ordinal 皆需覆蓋。下游原入口固定寫 `/tmp/fragment-stack.svg`，`TMPDIR` 不會改它，因此沿用獨占 WSL 時段／私有 `/tmp`，完成後另保存該 SVG。不是替代 Claude mutation train。 |
| grid-inspector mutation | 明確繼承 fresh `GEOMETRY_TEST_BRIDGE`，Node＋Python；四 variant × VM/native 共 **8 commands**。原版／恢復：VM 9 pass、native 3 pass；omit-stagger VM 7 assertion failures，freeze-reference VM 4 assertion failures；兩 mutant native 要是 3 tests 中有真正 `AssertionError`／FAIL，不能是 ERROR。以原腳本 `receipt.json` 的每筆 `passed`／`assertionOutcome` 和 logs 為準；這是預期紅綠控制，不是額外產品通過數。 |

## 5. 去重、邊界與交付勾選

- **沒有可從 22 項中刪掉的相同入口。** full CDP 的 room 插件是 `room_outline_test.js`；Space 的 Save 插件是 `save_reopen_synthetic_test.js`；十項原始 driver 自行實作流程，均未呼叫這 22 支入口。共用 helper、相同 Save/Open 名稱或部分 UI 路徑，不等於同一 oracle。
- `grid_inspector_rename_test.js` 已由 full CDP／composition 呼叫，**不要另當獨立 gate 再跑一次**。需要新原生程序 reopen 時，將第二個同候選空服務的 `GEOMETRY_GRID_RENAME_FRESH_URL` 交給 Claude 的既定 full CDP run；未設只能宣稱 fresh JS context。這項補強不擴大本表 25 入口。
- 每列交付：最終 SHA/tree、實際 command/env、來源不變、原生 fresh、專屬 URL/PID/session／profile／TEMP、原 gate 預期及實得 census、exit、raw log／輸出路徑；失敗與 blocked 原樣保留。一般 wrapper 的 command-only 不能改寫為 completion verified。
- 所有 fresh browser／context 均不代表 fresh native service；只有明確第二服務的 K2a ZIP，以及 Claude full CDP 的 fresh-native reopen 可作該項聲明。下載 fallback／file chooser 不冒充 OS Save picker；顯式 race／故障注入與實體手機、IME、人工操作各自保留範圍。
- 四個啟動修正的來源證據：`room_multi_candidate_browser.js:280`、`test_rule_case_app_browser.js:15`、`test_rule_case_app_races.js:14` 現讀 `GEOMETRY_CHROME || '/usr/bin/chromium'`；`feedback_resize_observer_test.js:9,134–135` 現讀空白分隔 `GEOMETRY_CHROME_FLAGS`。原先三個 hard-coded path 與 root Chrome args 問題是**靜態發現**；本文件未將其說成實跑失敗或已實跑修復。最終 SHA 必須含 `4330527` 的修正，環境依賴也須先驗明；不更動 assertion、count 或 timeout。
