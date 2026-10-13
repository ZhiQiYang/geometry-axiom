# 三個 PR 的真瀏覽器驗收契約(核對員產出,只讀來源)

核對日期 2026-10-06。head 以 `gh pr view --json headRefOid` 重新確認,三者皆與派工單相同,未變:
main `6562fa53`;#152 `a15d73a3`;#134 `77c3847f`;#156 `2a7d9cba`。#137 不在範圍。
`git fetch` 後 origin/main 仍是 `6562fa53`。三個 PR 皆 OPEN;#134、#156 是 draft;#152 PR 本文自稱已退出 draft。
(未用 worktree,全部以 `git show <sha>:path` 讀取;唯一寫入是 scratchpad 內暫存的 #152 CLI 乾跑,已刪。)

## 0. 共通前提

### 0.1 AGENTS.md 一般要求(三個 head 的 AGENTS.md 逐字相同,md5 5537810d...)
- A1 開啟/重啟應用:一般入口 `geometry-web/start.ps1`(`-Port` 1024–65535,預設 8765);既有服務不可只因能連線就沿用,
  須 `python geometry-web/runtime_version.py --probe <port>` 成功(`/runtime` 的 `schema=geometry-runtime/1`、`fresh:true`、
  `version` 等於該 checkout 的 source_version、`root` 等於該 checkout 路徑)。404/指紋不符/不同 repo/`fresh:false` 都不算成功。
  出處:AGENTS.md:86-97;runtime_version.py:169-178;serve.py:326-329。
- A2 不得把使用者在用的服務當測試服務重置;只停自己啟動的 PID(AGENTS.md:94-97 + 記憶 kill-only-own-verified-pids)。
  使用者的服務很可能佔 8765,測試請用別的 port 並用各 PR 自己的 checkout。
- A3 編出的 exe 一律放 `%TEMP%\geometry-tests\`,不放 repo(SAC 會擋 repo 內新編 exe,WinError 4551)。bridge 被擋=環境問題,
  與程式失敗分開記錄,不去動安全設定(AGENTS.md:232-253)。
- A4 跑 cdp_test 必須同時給同一個 `GEOMETRY_FEEDBACK_DIR`(TEMP 下專用目錄)給 serve.py 與 node,否則 P38 會寫進 repo 的 feedback/
  (AGENTS.md:261-269;cdp_test.js:11-20 會強制檢查)。
- A5 「保存/重開、undo/redo、鍵盤、中斷恢復」是任務層通則,非 AGENTS.md 字面條文(AGENTS.md 只要求真瀏覽器操作與環境隔離;
  UI 減重紀律 GEO-219 在 AGENTS.md:279-286)。下面各條標「[通則]」者為我依通則判定是否適用,owner 可裁剪。
- A6 UI 減重(GEO-219):每個工作畫面常駐說明區塊 <= 3 塊;新增可見入口須寫明減項。#134 的 BACKLOG 新段已寫減項(見 R-12)。

### 0.2 啟動(適用 #134、#156,即需要 geometry-web 的兩個 PR)
- 服務入口:`python geometry-web/serve.py <port>`(serve.py:61 `PORT=int(sys.argv[1])`;只綁 127.0.0.1,serve.py:514-515)。
- 必要環境變數:`GEOMETRY_BRIDGE`(含參數,serve.py:52-60;未設則找同目錄 `web_bridge.exe`,SAC 可能擋)、`GEOMETRY_MODEL_BASE`
  (空間建模元件;沒給時 start.ps1 會用 `modeling.base.startup_base_transport()` 判斷,見 start.ps1:27-39)、`GEOMETRY_FEEDBACK_DIR`(A4)。
  Windows 一般入口 `geometry-web\start.ps1 -Port <空閒埠>` 會在 WSL 用 gcc 編 web_bridge 到 /tmp 並設 `GEOMETRY_BRIDGE=wsl.exe -d Ubuntu-24.04 ...`
  (start.ps1:18-41);前提是本機 WSL Ubuntu-24.04 與 gcc 存在(我沒驗)。
- 需要原生 exe:是(bridge;#134 還依賴 native `grid-rule-query` 等,PR 全程只改 JS/CSS/測試,未改任何 .c,所以 bridge 以 main 或該 head 的 C 編都行,
  但必須是目前 C 的編譯結果)。注意:`%TEMP%\geometry-tests\bridge.exe` 時間 Oct 4 19:07,而 main 最後一次動 native/核心是
  fedd15d(2026-10-04 20:41 +08:00),**該 exe 可能比目前 C 舊**;不可直接沿用,須重編並驗二進位真的換了(AGENTS.md:246)。
- 每個 PR 用自己 head 的 checkout(`git worktree add --detach <path> <sha>`),在該 checkout 內啟動服務,否則 `/runtime.root` 與 version 對不上。
- 判讀:`GET /runtime` -> `{schema:"geometry-runtime/1", version, fresh, root, pid, session}`。pass=`fresh===true` 且 root=該 worktree 路徑
  且 `runtime_version.py --probe <port>` 結束碼 0;QA 過程中改了任何 geometry-web 檔(含 git checkout)會使 fresh 變 false、首頁回 409 要求重啟。
- 對照組(基線):同一操作在 main(6562fa53)checkout/另一埠重做一次,以證明新行為不是環境造成(PR 都宣稱 main 重現了缺陷)。
- 既有輔助自動化(不能取代真 UI 驗收):見各 PR 第 3 節。

### 0.3 視口
- 桌面 1382×804、手機 390×844(三 PR 一致)。#134 的 P88 自帶測 1280/390 兩寬,可另補 1280。每條驗收預設兩視口都做,除非條目另註。
- 通用 pass:`document.documentElement.scrollWidth <= innerWidth`(390 時 PR152 的 qa_notes 要求恰為 390)、無 console error/uncaught exception。

---
# 一、#152 私人 Geometry work manager(a15d73a3)

## 1.1 性質與啟動
- 與 geometry-web/serve.py **不是同一個服務**。它是獨立的 Python 標準庫工具:`geometry-web/work-manager/cli.py serve`(server.py:113-115),
  只用 http.server 綁 127.0.0.1(host 只准 127.0.0.1/localhost,server.py:29-31),靜態面板在 `work-manager/static/`,資料用 SQLite。
  **不需要原生 exe、不需要 GEOMETRY_BRIDGE/MODEL_BASE/FEEDBACK_DIR、不需要 `/runtime`**(沒有該路由;server.py 只有 `/`、`/style.css`、`/app.js`、
  `/api/state`、`/api/export`、`/favicon.ico`)。AGENTS(work-manager/AGENTS.md:13)明說「不使用產品 feedback 目錄」。
- 淨差異(`git diff origin/main a15d73a`)只有 `geometry-web/work-manager/` 21 檔 +6621;`gh pr view --json files` 另列出 app.js、
  source-inspector-app.js 等產品檔,那是因為 PR 含 main 的合併歷史,**對 main 的淨差異不含產品檔**(已用 git diff --stat 排除產品檔確認)。
- 啟動命令(在 checkout 根目錄):
  ```
  python geometry-web/work-manager/cli.py --data-dir <TEMP>\wm-qa import-snapshot geometry-web/work-manager/fixtures/synthetic-demo.json
  python geometry-web/work-manager/cli.py --data-dir <TEMP>\wm-qa serve --port <空閒埠,例 8791>
  ```
  `--data-dir` 是全域選項,必須放在子命令之前(cli.py:22、25-35)。出處:README.md:9-23。
  本機 `python3` 是 WindowsApps 的 Store 別名(`C:\Users\Yang\AppData\Local\Microsoft\WindowsApps\python3`),`python` 才是 3.14(C:\Python314);
  README 全寫 python3,Windows 上請用 `python`。
- 驗證服務身分:`GET /api/state` 200 JSON,含 `state_hash`、`store_health.status=="ok"`;`serve` 啟動時 stdout 印
  `{"url":"http://127.0.0.1:<port>","mode":"loopback-read-only","persistent_service":false}`(server.py:115)。
- 程式指紋:服務啟動後若 work-manager 的 .py/static 被改,`/api/state` 回 503「工具程式已更新,請重啟 serve」(server.py:77)。QA 中不要改該目錄任何檔。
- 私有資料:資料目錄放 TEMP,**不要用預設 `.local/`**(在 checkout 內,雖 gitignore);截圖不得進 repo、不得提交。

## 1.2 合成資料
- `geometry-web/work-manager/fixtures/synthetic-demo.json`(唯一提交的 fixture;3 個 task、1 個 source `synthetic-demo` as_of 2026-10-06T01:00:00Z)。
  我乾跑 `import-snapshot` + `reconcile`(暫存目錄,已刪)得到的基準值:
  - 3 工作:DEMO-HOLD(execute 批准 required;execution unknown;delivery approval_blocked;next_action_mode wait)、
    DEMO-READY(unknown/unknown;next_action_code continue_work,mode write,唯一 ready)、
    DEMO-REVIEW(execution stopped;有 PR #2 pending、證據 demo-evidence-2 passed;delivery approval_blocked(merge 批准 required);alert delivery_gap warning)。
  - `ready_counts = {all:1, read_only:0, write:1, wait:2}`;`alerts` 共 5 筆(approval_required×2、owner_missing×2(HOLD、READY)、delivery_gap×1);
    `store_health.status=ok`、row_count sources1/snapshots1/events5;`coverage.count=0`、`pr_links` 只有 #2(example.com)。
  - `state_hash` 前 10 碼我跑出 `79f7e18372`,`payload_hash` 前 10 碼 `f0857fcd51`(`generated_at` 不入 hash;但**freshness 入 state_hash**)。
  - **時效陷阱**:`STALE_AFTER_HOURS=24`(store.py:34),source as_of=2026-10-06T01:00Z,故 **2026-10-07T01:00Z 之後** 這份 fixture 會變 stale、
    出現 stale 警示、state_hash 改變。若 QA 跨日,預期值須改為 stale 版,且 UI 不應顯示為 live/current。
- fixture **沒有** issue_inventory/pr_inventory、umbrella、CI、多 source,因此涵蓋面板(#coverage)、umbrella、CI runs、stale 來源、store_health invalid 這些區塊在 demo 下都是空狀態。
  要驗它們需另造合成 snapshot,結構參考 `test_coverage.py:17-60`(issue_row/pr_row、`issue_inventory={"repository","complete","issues":[...]}`、
  repo 名用 `synthetic-work-qa/alpha`)與 `schema.json`、README.md:91-97。**禁止**用真實 GitHub/issue 快照、owner thread、feedback 或使用者私人場景。

## 1.3 驗收條目(PR 宣稱要驗的)
PR 本文宣稱:1440/390 面板、同一 state hash、XSS-safe 文字渲染、失敗保留上一份畫面、私存截圖。PR 本文**承認** current-head 的 desktop/390 瀏覽器驗證 BLOCKED
(Chromium 無法建 AF_UNIX socket),因此下列全部尚無 a15d73a3 的瀏覽器證據,不可沿用舊收據。
視口:桌面 1382×804 與 390×844(PR/截圖腳本用 1440×1000 與 390×844,見缺口 G-152-3)。

| 編號 | 操作(真 UI) | 預期可觀察結果 / pass 條件 | 出處 |
|---|---|---|---|
| W-01 | 瀏覽器開 `http://127.0.0.1:<port>/`(另開 `http://localhost:<port>/` 各一次) | 兩種主機名皆 200;`document.title==="Geometry 工作管理"`;h1「Geometry 工作管理」;`document.documentElement.dataset.stateLoaded==="true"`;`body.dataset.stateHash` 為 64 hex | static/index.html:7,16;app.js:857-859;server.py:60-69 |
| W-02 | 載入後立即另開終端跑 `cli.py --data-dir <同> reconcile` | 面板 `#state-hash` 文字 === CLI `state_hash` === `/api/state` 的 `state_hash`(同一資料、同一分鐘內;若不同須比 `payload_hash` 並解釋是 freshness 差) | README.md:128;index.html:90 |
| W-03 | 讀 `#task-count`、`#ready-count`、`#ready-mode-counts`、`#filter-summary`、`#alert-count` | 「3 工作」;「1 項動作」;模式計數含 write 1/read_only 0(文字以 UI 實況為準,數值須對應 `ready_counts`);「顯示 3 / 3 筆登記紀錄 …」;alert-count 5(未過期時) | app.js:303,639-640,697 |
| W-04 | 看 `#task-rows .task-row[data-task-id]` | 3 列 DEMO-HOLD/DEMO-READY/DEMO-REVIEW(順序以 UI 為準);五欄(工作/來源、執行、交付、執行者/版本、下一步)與上列 fixture 狀態一致;DEMO-REVIEW 顯示「執行:stopped 類」「交付:受批准阻擋」而**不是 done**;沒有任何列顯示完成 | README.md:116-117 |
| W-05 | 點工作名稱展開 DEMO-REVIEW;再點 ✕/關閉鈕;用鍵盤 Tab 到名稱按 Enter/Space 重做 | 展開後出現證據(demo-evidence-2,passed,標明綁定 head bbbb…)、PR #2「review pending」、所有權紀錄;`https://example.com/...` 以連結呈現;關閉後焦點回到該列(app.js:562,652 有 focus 還原邏輯,以實測為準) | app.js:414-492,556-590 |
| W-06 | `#search-input` 輸入 `example/review`;再輸入不存在的字串;清空;`#status-filter` 逐個選項切換 | 輸入 review 時剩 1 列且 `#filter-summary` 為「顯示 1 / 3 …」;無匹配時 `#queue-empty` 顯示「沒有符合條件的工作。」且 `.task-row` 為 0;清空恢復 3 列;篩選「可進行」只剩 DEMO-READY | app.js:601-640,687 |
| W-07 | 點「可進行的下一步」區的 DEMO-READY 項;點模式計數鈕(write/wait) | 前者展開並捲到 DEMO-READY 列(openTask);後者設置篩選(setFilter)並更新 `#filter-summary` | app.js:99-125,295-330 |
| W-08 | 點 `#refresh-button` | 按下期間文字「讀取中…」,完成後回「重新讀取狀態」;`#status-message`(sr-only,aria-live)含「已讀取 3 …」;資料沒變則 `state_hash` 不變,`generated-at` 更新 | app.js:835-876 |
| W-09 | 讀取失敗保留畫面:只結束**自己啟動的** serve PID,按「重新讀取狀態」;再用同 data-dir 重啟 serve 後再按 | 結束後:`#fetch-error` 可見、文字含「狀態讀取失敗」與「畫面保留上次成功讀取的資料與雜湊」;3 列與 `state_hash` 不變;重啟後按重讀:`#fetch-error[hidden]` 回復、畫面更新。這也是「中斷恢復」+「保存/重開」(資料目錄不變則 payload_hash 相同) | app.js:862-873;README.md:25,132 |
| W-10 | XSS 渲染:另造合成 snapshot(僅 title 欄塞 `<img src=x onerror=...>`、`javascript:` URL 於 refs/pr.url)以另一 data-dir 匯入並開面板 | 惡意字串以純文字顯示;`document.querySelectorAll('img').length` 不含該注入、無腳本執行(用 console 無新輸出、自訂 `window.__xss` 旗標為 undefined);`javascript:` 不成為可點擊 `<a href>`(safeURL 白名單) | app.js:59-75;qa_notes.md:23-28 |
| W-11 | 點 `#export-button`「匯出備份」(或直接 GET `/api/export`) | 回 200,`Content-Disposition: attachment; filename="geometry-work-backup.json"`,JSON 帶 checksum;下載檔只放 TEMP,**不入 repo**;(下載須先向 owner 取得許可,見 5.2) | server.py:86-88 |
| W-12 | 唯讀/來源限制(HTTP 層,可用 javascript_tool 的 fetch 與 curl 輔助) :POST/PUT/PATCH/DELETE/OPTIONS `/api/state`;GET 時偽 `Host`、跨 Origin;GET `/nope` | 寫入類 405 且 `Allow: GET`;Host 非 `127.0.0.1:<port>`/`localhost:<port>` 或 Origin/`Sec-Fetch-Site` 不同源回 403;未知路徑 404;`/favicon.ico` 204;程式也不應綁 0.0.0.0(`netstat` 看 LISTEN 位址是 127.0.0.1) | server.py:60-109 |
| W-13 | 版面:1382×804 與 390×844 各取整頁與可視;逐區滾動(同步帶、可進行、佇列、警示、涵蓋、排程、來源、操作說明) | 兩視口 `scrollWidth<=innerWidth`(390 時恰 390);390 下表格改為堆疊(每個 `td[data-label]` 有標籤);alerts 區 `#alerts-list` 可捲動且可聚焦(`tabindex=0`,role=region);文字無被截斷或重疊;CSS 斷點 1450/1100/850/560 | qa_notes.md:27-29;style.css:247,251,266,282;index.html:72 |
| W-14 | [通則:鍵盤] 從頁面頂 Tab:第一個停點、Enter;Tab 到各按鈕、展開鈕、`details.operations-help`(Enter/Space 開合) | 第一停點為「跳到工作佇列」skip-link(可見,top:10px),Enter 後焦點/捲動到 `#work-queue`;所有互動元件有 3px `#2f78c4` focus-visible 外框;無鍵盤陷阱 | index.html:12;style.css:32,40 |
| W-15 | 點 `#copy-hash-button`;點 `#print-button` | 複製:文字短暫變「已複製」(1.8s),`#status-message`「已複製完整狀態雜湊。」;若剪貼簿被擋則顯示「無法使用剪貼簿,已選取雜湊…」且雜湊被選取(兩者皆算 pass,記錄是哪一種);列印:`window.print()` 被呼叫(在 CDP/headless 環境可能無對話框,記錄為 skipped 而非 pass) | app.js:880-893 |
| W-16 | 保存/重開:停自己的 serve,同 `--data-dir` 重啟,重開頁面 | `payload_hash` 相同、3 列相同(freshness 未過 24h 則 state_hash 也同);`export` 後 `--data-dir <新目錄> restore` 再 reconcile 的 `payload_hash` 與原相同(CLI 輔助驗) | README.md:30-35,130-134 |
| W-17 | 資料邊界:QA 結束 `git -C <worktree> status --short` | 空(無 .local、無 png/sqlite);截圖/匯出只在 TEMP | work-manager/.gitignore;AGENTS.md:6-8 |
| W-18 | 空狀態/來源失敗(owner 要不要驗見缺口 G-152-5):用空 data-dir `serve`,開面板 | `#task-count` 為「待核/0」類而非假成功;`#source-mode`「尚未讀取」→ 讀後不虛構完成;`#coverage-overview-summary`「尚未匯入 issue 清單;登記工作數不代表完整覆蓋。」 | index.html:35,42;app.js:187 |
| W-19 | 另造含 inventory/umbrella 的合成快照(依 1.2 說明)開面板,看 `#coverage` 與 `#schedule` | 依 `coverage` 欄位:issue 覆蓋、`tr[data-issue-number]`、`tr[data-pr-number]`;umbrella 顯示為彙總、不可派工、不被算 done;「已映射≠已驗收」說明可見。若 owner 不願造資料,此條降為「依賴 CLI 測試證據」 | README.md:91-97;app.js:178-282 |
| W-20 | console/network 健康 | 無 pageerror、無 console.error;請求只有 `/`、`/style.css`、`/app.js`、`/api/state`(+favicon 204);全部 same-origin、無外部連線 | server.py:94-100 |

## 1.4 AGENTS.md 一般要求對應
- 保存/重開:W-16。中斷恢復:W-09。鍵盤:W-14。undo/redo:**不適用**(唯讀面板,無編輯動作;work-manager/AGENTS.md:11,13)。
- work-manager/AGENTS.md:13「UI 驗 desktop 與 390px」=W-13;「不使用產品 feedback 目錄」=本工具不需 GEOMETRY_FEEDBACK_DIR,QA 勿給。

## 1.5 既有自動化(輔助,不能取代 1.3)
- 單元/整合:`python -m unittest discover -s geometry-web/work-manager -p "test_*.py" -v`,預期 `Ran 142 tests ... OK`(分項:acceptance46、
  adapter8、adapter_independent13、coverage9、legacy_upgrade6、review_regressions25、store35,我逐檔數 `def test_` 加總 142,與 PR/qa_notes 一致)。
  這些測試含真 subprocess CLI 與 loopback HTTP,**沒有瀏覽器**。
- 截圖:`python geometry-web/work-manager/screenshot.py --url http://127.0.0.1:<port> [--out-dir <TEMP>] [--full-page]`:需要 Playwright(Python)+Chromium;
  `--chromium` 預設取 `shutil.which("chromium")`/`google-chrome`,Windows 通常為 None 則用 Playwright 內建;視口固定 1440×1000 與 390×844;
  檢查 `scrollWidth>width` 就丟錯;只有 desktop.png/mobile-390.png/capture.json。**預設 out-dir 在 checkout 內 `.local/screenshots`,必須 `--out-dir` 指到 TEMP**。
  它是截圖與寬度的輔助,不驗互動(搜尋、展開、失敗保留等)。
- PR 沒有任何已提交的瀏覽器互動測試檔(qa_notes.md:23-28 的 Playwright mock 腳本沒提交)。

---
# 二、#134 #61 切片 2:原生來源規則子線顯示與追溯(77c3847f)

## 2.1 啟動
- 要用 geometry-web 服務(見 0.2)與原生 bridge。在 `77c3847` 的 checkout 內:
  `python geometry-web/serve.py <port>`,環境 `GEOMETRY_BRIDGE=<TEMP>\geometry-tests\bridge-pr134.exe`(以該 head 的 C 重編)、`GEOMETRY_MODEL_BASE=<TEMP>\geometry-tests\model-base-pr134.exe`、
  `GEOMETRY_FEEDBACK_DIR=<TEMP>\geometry-tests\fb-pr134`(出處 AGENTS.md:182-211,261-269)。或用 start.ps1(WSL gcc 路線)。
- 判讀:`/runtime` fresh:true、root=該 worktree;`python geometry-web/runtime_version.py --probe <port>` 退出 0。
- 本 PR 的 BACKLOG 新段與 DOM-CONTRACT 新段(DOM-CONTRACT.md:1042-1049,BACKLOG.md:4206-4213)是契約來源;**沒有**獨立的切片 2 驗收文件(slice1 的是 `geometry-web/docs/ISSUE61-SLICE1-20261005.md`,BACKLOG 說切片 2 的實測會「回填」該檔,但本 PR 未更新它,見缺口 G-134-1)。

## 2.2 合成資料
- 全部在 `geometry-web/grid_rule_lines_test.js`(P88)內以 `line ...` 原生指令作者:兩個 boundary(面 1:矩形 1200×800;面 2:L 形 + 一個孔 `hole 170,80 ...`),
  一個共享來源 grid-system + 規則「Native inner lines」,兩個 binding/applied grid,signed cell `(-2,1)` 與大索引 `('9007199254740993','-9007199254740995')`。
  無任何使用者專案、feedback、PDF。QA 的**初始世界**可以照這個夾具以原生指令(或等價的正式 UI)建立,但**被驗證的行為**必須走真 UI(畫布、檢查器、面板、Save/Open)。
- 對照組:main 同一夾具,正式畫布、角材選項、guide 來源子線皆 0(BACKLOG.md:4213 的「先釘住 main 缺口」),在 main 重現後才有「修復」意義。

## 2.3 驗收條目
PR 本文宣稱(以下 R-xx 皆「PR 宣稱要驗」,除標 [通則] 者)。視口:1382×804 與 390×844(P88 原測 1280/390,可補 1280)。
**重要**:PR 本文列的證據綁在 `ea7b656`(凍結來源),current head `77c3847` 是 d1d51d8 + 合入最新 main 的 merge(含 297 檔、16121+ 行的 main 前進),
本 PR 自己也沒有 current-head 瀏覽器證據,所以下列全部要在 77c3847 重驗。

| 編號 | 操作(真 UI) | 預期 / pass 條件 | 出處 |
|---|---|---|---|
| R-01 | 建立夾具:新專案 -> 兩個面(1:矩形;2:L 形含孔)-> 建「來源網格」(`#btnNewGridSystem`;390 為 `#btnQuickGrid`)-> `#igRuleAdd` 新增規則(`#igRuleName`=Native inner lines、選 cell)-> `#igRulePreview` -> impact 對話框 `#impact-confirm` | 來源內顯示 `[data-ig-source-rule="1"]`,其 `data-ig-rule-ref="none"`(來源/配置唯讀視圖**不**製造可放置引用);兩個配置(binding)各自出現 `[data-ig-result-rule]` | DOM-CONTRACT.md:1046-1047;grid_rule_lines_test.js:35 |
| R-02 | 進入面 1,左/右欄開「components」分頁(`#faceInspectorTabs [data-fi-tab="components"]`),在 `.grid-rule-details` 選規則與 cell(`[data-rule-focus-key]`、`#gridRuleCellI`/`#gridRuleCellJ`),按 `[data-rule-exact]` | 畫布出現 `.face-rule-line`(stroke)、`.face-rule-hit`(命中)、`[data-rule-label]` 標籤;線段座標與同一 native `grid-rule-query` 回傳完全一致(exact cell);面內顯示 source→binding→applied grid 的追溯文字;`[data-rule-focus-status]` 顯示完成/零可見/拒絕之一 | DOM-CONTRACT.md:1043-1045;P88 check「exact cell 線段與 native 相同」 |
| R-03 | 對每條線(u/v 軸、innerIndex)點擊 `.face-rule-hit` 取 anchor,看角材工具 `#tbAnchor` 與 guide 來源 `#refGuideSource` 選項 | 選項顯示「來源規則 `<systemId>/<ruleKey>` · 套用 `<appliedGridId>`」;值為完整 8 欄 RuleLineRef(appliedGrid、system、rule、signed cell、axis、inner index);四數 bounds 全部有限(finite);父 cell 與孔/凹形邊界裁切後線段不越出;**首次點擊選取/標籤不改 native、raw、history** | DOM-CONTRACT.md:1047;reference-ui.js diff(rule label);P88 checks |
| R-04 | 390 視口重做 R-02/R-03;抽屜(`#toggleLeft/#toggleRight/#workspaceToggleRight`)開關後再操作 | 觸控目標高度足夠(P88 以 `390 面 N source/cell 觸控高度` 檢查,閾值以測試內為準);inspector 與畫布**無水平溢出**;`.face-rule-hit` 被右抽屜遮擋時要先關抽屜才可點(P88 以此處理) | PR 本文「390px 溢出」;P88 check |
| R-05 | 切換「共用參考線隱藏」(`#faceReferenceVisibility`) | 隱藏時 rule hit/anchor 同步停用,World/history 零寫入(undo 堆疊長度不變、`dump` 不變) | P88 check「共用參考線隱藏同時停用 rule hit/anchor 且零寫入」 |
| R-06 | 在面內點 `[data-rule-source]`(來源 jump) | 導到同一來源編輯器並定位該 `systemId/ruleKey`;**讀取完成後**才退出面內,凹形/孔 boundary 快取與 boundary 卡保留;jump 零寫入;延遲時中途換 view 不會被後到的 jump 拉回(detached/stale 零定位) | DOM-CONTRACT.md:1043;P88 checks |
| R-07 | 來源規則改動:在來源編輯器改規則 -> 預覽(影響摘要列兩個配置與兩面)-> 先**取消** -> 再確認 -> undo -> redo | 取消後 World 與 history 逐字不變;確認後單步更新全部配置,ruleKey 不重配;undo 一步回原樣、redo 一步重做 [通則:undo/redo] | P88 checks |
| R-08 | 高密度規則(大量 cell):以 exact 與 sample 兩種查詢檢視 | sample 有界並明示 incomplete;查詢零寫入;用真正 cell 的 exact 仍可完整定位;晚返回的 sample/exact 不覆寫新的 raw 欄位值與鍵盤 focus(焦點仍在輸入框,raw 字串保留 `9007199254740993`/`-9007199254740995`) | DOM-CONTRACT.md:1045;P88 checks |
| R-09 | 既有 guide 流程:用 `#tbAnchor`/`#refGuideSource` 選規則線建 guide(含進階入口);再試一個錯誤 source;at-line native 拒絕後修 selector 重試 | guide 引用為真 gridrule 引用(不翻 U/V);錯 source 時 native 拒絕、保留同一表單全部輸入(含角色/截面)、World/undo/redo 零寫入;只修 selector 後同表單重試成功,history 單步 | PR 本文「native 拒絕後刷新快照並保留同一表單續試」 |
| R-10 | direct at-line 角材:選規則線 -> 手動選截面與角色 -> 放置 | 角材由 native 驗證支撐與父 cell 足跡;未選截面/角色不得自動猜;單規則「引用數」只計該規則的 guide/timber(不過度計入整來源) | DOM-CONTRACT.md:1047;P88 checks |
| R-11 | 引用鎖:在有引用的規則上開來源影響預覽 | 預覽的確認鈕不可按(`#impact-confirm` disabled/不可用);強行操作也零 World 寫入 | P88 checks |
| R-12 | 一般手動格線(沒有來源規則的面):進面並操作一般格線 | **零 rule query**(不得送 `grid-rule-query`;可在 console 掛 `apiRequest`/攔截 `/api` 看命令);面不被空 query 重建;UI 減項:規則資訊併入既有 GridEditor,沒有新增工具列/獨立管理器,常駐說明 <=3 塊 | PR 本文;BACKLOG.md:4208-4211;DOM-CONTRACT.md:1049;AGENTS.md:279-286 |
| R-13 | 同來源另一格的**手動子格草稿**存在時,遇持有的晚回應 | DOM、raw 字串、焦點、native preview、history/World 均不變(只讀回應不踩草稿) | PR 本文 |
| R-14 | 刪除最後一條規則 | stroke/hit/selection/密度標示全清;之前晚返的 exact 回應**零 paint、零 write** | PR 本文 |
| R-15 | newid/native await 跨 await 守衛:在建角材的 `newid` 與 native 準備期間(以 fetch 延遲注入 `/api` 的 `newid`、`timber`/place 命令回應)切面、換 context、undo、換 session,再放行 | 全部情況零 `history-begin`/`timber`/`place`,World 與 history 不變;同 ID/同輸入新 context 的晚返回也零寫入 | P88 checks(newid 系列);PR 本文 |
| R-16 | **Save → 新空白專案 → Open**:在 390 與桌面各做,含兩面、大 signed cell | 下載的 ZIP 內含兩個配置與 guide/direct 的 typed 引用;重開後場景 dump 逐字相同、來源 key 與 signed binding 相同;面內重開後 rule line 畫布(裁切後)與存前一致(目視+座標) | P88 checks「真 Save ZIP…」「新空白 context 真重開逐字場景」 |
| R-17 | [通則:鍵盤] 在 `#gridRuleFocusKey`、cell 輸入、`[data-rule-exact]`、`.face-rule-hit`(tabbable?以 DOM 實況為準)用 Tab/Enter/Space/Esc | 可用鍵盤完成 R-02 的查詢與選取;焦點順序合理;Esc 關閉 impact 保留 raw(DOM-CONTRACT:1039 先前契約) | AGENTS.md(UI 減重);DOM-CONTRACT.md:1039 |
| R-18 | 全程 console | 無未捕捉例外(P88 最後一檢「本切片無新增未捕捉瀏覽器例外」) | P88 末段 |

R-xx 中「未列任何 P88 對應」者(R-04 閾值、R-17)為我依契約文字推導;**SR24 實體手機觸控、iOS/Windows、OS 鍵盤/IME/檔案選擇器/下載位置**
PR 明講仍由人工驗,不在本次瀏覽器 QA 內,應在報告中列「未驗」。

## 2.4 既有自動化(輔助)
- 真瀏覽器整合:`geometry-web/grid_rule_lines_test.js`(P88)經 cdp_test.js 載入。單跑範圍:
  `GEOMETRY_GRID_SYSTEM_ONLY=1`(cdp_test.js:7007-7013 同一旗標依序跑 grid_system_test、grid_rule_editor_test(P87)、grid_rule_lines_test(P88);
  此旗標只能設 1 且不能與其他 scope 旗標併用,cdp_test.js:15-18)。
  指令(同 AGENTS.md:261-269 的型式):
  ```
  set GEOMETRY_FEEDBACK_DIR=%TEMP%\geometry-tests\fb-pr134 ; set GEOMETRY_BRIDGE=...bridge-pr134.exe ; python geometry-web/serve.py <port>
  GEOMETRY_FEEDBACK_DIR=<同> GEOMETRY_TEST_URL=http://localhost:<port>/ GEOMETRY_GRID_SYSTEM_ONLY=1 GEOMETRY_CDP_PORT=<chrome埠> node geometry-web/cdp_test.js
  ```
  預期:golden 的段落計數 P70=113、P87=60、P88=105 全 pass、0 fail;完整(無 scope)為 84 段/2159 pass/0 fail/0 skip(cdp_sections.golden.json;
  PR 本文:原 83 段 2054 + P88 105);例外總計 1 為既有 P38 刻意注入的 fb-auto-probe(其餘 0)。完整跑極耗資源/時間,主機僅 ~650MB 記憶體,
  建議只跑 GEOMETRY_GRID_SYSTEM_ONLY=1,且與瀏覽器 QA 不要同時開。
- 單元:`node --test tests/test_grid_rule_lines.js`(RuleLineRef 編解碼、query decoder 拒絕、用量計數;預期 3 個 test 全 pass);
  `tests/test_source_inspector.js`(這個 head 的版本);aggregate `python tests/run_all.py`(expected count 510->513,PR 稱 68 suites/2160 pass);
  不需要瀏覽器,但 test_source_inspector 需 `GEOMETRY_TEST_BRIDGE`(run_all.py:86)。
- CI:PR 稱 08b2ef79 的 GitHub Actions 全 7 job 失敗但 steps/logs 空,「原因未定位」;memory 顯示本帳號 Actions 被計費擋(ci-billing-blocked),先看 annotation 再判斷,不算 pass 也不算程式失敗。

---
# 三、#156 #118 guide 準備所有權與取消檢查(2a7d9cba)

## 3.1 啟動
同 0.2:在 `2a7d9cb` 的 checkout 內啟動 serve.py + bridge(本 PR 只改 app.js、reference-ui.js、tests/test_source_inspector.js,**無 native 變更**),
同樣必須重編 bridge、`/runtime` fresh、root 對得上。PR 本文自承 current-head 瀏覽器 gate **BLOCKED**(AF_UNIX),全數瀏覽器數字(caller9/9、guide9/9、card5/5、CDP2054 等)
屬舊 tree,**且那些 caller/guide/card 腳本不在 PR 內**(只有 VM 層的 `tests/test_source_inspector.js` 在),所以本 PR 目前沒有可直接重跑的瀏覽器測試檔。

## 3.2 合成資料
無專屬夾具。用 repo 內既有原生指令作者的最小世界即可:一個 boundary 面(例如 `boundary 1 outline 0,0 1200,0 1200,800 0,800`,P88/其他 CDP 測試皆用此形式)與
至少一個可用 `檢查` 的非工作區卡(例如 grid-system 或 parameter 卡,kindOpenMode != "workspace")。不得用使用者專案。

## 3.3 驗收條目
PR 宣稱兩項修復:(甲)新建 guide 時,舊程式在 `newid` 等待期間若使用者按 Back/換面,guide 仍會落在新面;現在整個準備鏈(`snap` -> `newid` -> `emitLine`)
都以原始 edit/focus/context/history/native/guide 來源當所有權,過期即零寫入。(乙)已取消的卡片「檢查」(DraftGate 取消)不再改變草稿/選取/面板;
接受時才選取目標並開既有檢查器。視口 1382×804 與 390×844(PR 稱 caller/guide/card 皆測 1382/390)。

| 編號 | 操作(真 UI) | 預期 / pass 條件 | 出處 |
|---|---|---|---|
| G-01 | 進面(物件卡「進入」或 `#inspEnter`),在面內編輯器(`#feGuidePick` 路徑)以 U/V 方向鈕新增一條 guide;基線:同樣在 main 做一次 | 正常情況 guide 數 +1、ID0 也是合法 guide ID(`ids.guide` 0 不被當錯);面板可見新 guide 且 `dump` 有對應 `guide` 行;history 多 1 步,undo 一步移除、redo 一步恢復 [通則:undo/redo] | app.js diff:5757-5760,10140-10143;reference-ui.js createReferenceGuide |
| G-02 | 拖曳新增 guide(`fe.drag.kind==="guideNew"` 路徑),在畫布上從面內空白處拖出一條線;同 G-01 驗證 | 同 G-01(拖曳與選單兩個入口都要驗,因為兩個 caller 各刪了一個多餘 `await api("newid")`) | app.js diff;feUp |
| G-03 | **Back 後晚到(核心缺陷)**:以 javascript_tool 暫時包住 `window.fetch`(只針對 POST `/api` 且 body 命令為 `snap ...` 或 `newid`),把回應延後到手動放行;觸發 G-01/G-02 的新增,在回應放行**前**按可見的 Back(`#workspaceBackButton`);放行 | 放行後:**沒有**新 guide(物件清單/dump 的 guide 數不變)、沒有寫入、undo 堆疊長度不變、畫面仍在 Back 後的狀態(沒被拉回該面);無未捕捉例外;baseline(main)應重現「晚到 guide 仍被建立」才算對照成立。兩視口 × 兩入口(drag/picker)× 兩階段(延遲 snap、延遲 newid) | PR 本文「Main real UI counters reproduced...」;test_source_inspector.js 新 harness |
| G-04 | **同面重入**:延遲期間 Back 後立刻重新進入**同一個面**(同 boundary/surface ID),再放行 | 舊手勢仍零寫入(同 ID 不得被當同一手勢);重入後的新手勢正常可建 guide 一次 | PR 本文「same-face reentry」 |
| G-05 | 延遲期間改變其他來源:換 context(新專案/Open)、history(undo/redo 別的步)、換 service session(重啟自己的 serve) | 各情況放行後零寫入、不拋錯(以 console 與 toast 為準) | test_source_inspector 的 expired 清單(focus、same-ID context、history、session) |
| G-06 | 移動既有 guide(面內拖 guide 線),過程中延遲 `snap`,期間用別的手段改了該 guide(刪掉重建同 ID,或改成 datum 共用基準)後放行 | 零寫入(重用 ID 不授權原來源);datum guide 拖動時出現既有 toast「這條線共用空間基準,請在「共用基準」修改來源」;正常未改動時 move 成功且 undo/redo 單步 | reference-ui.js moveReferenceGuide;PR 本文 |
| G-07 | native 拒絕 `newid`(難以真 UI 造成;可用 fetch 包裝把 `newid` 回應改成 `{ok:false,error:"..."}`) | toast 顯示錯誤原因(或預設「無法取得參考線識別,未新增。」);零寫入 | reference-ui.js diff |
| G-08 | **取消的卡片「檢查」**:先造一份未提交草稿(例如參數卡編輯中或格線草稿使 `DraftGate.ask()` 會跳確認),在物件畫布另一張非工作區卡(`.card-enter` 標「檢查」)按檢查,對確認對話框選**取消**;桌面與 390 都做,390 先關閉抽屜 | 取消後:草稿內容、目前選取、各面板/抽屜開關狀態與按檢查前完全相同;**390 下不得開出原本關閉的右抽屜**(main 會錯開);沒有選取改變 | app.js diff:2268-2276;PR 本文 |
| G-09 | 同上改選**接受**(確認放棄草稿) | 目標卡被選取,既有檢查器(右欄/390 抽屜,kind 為 grid-system/parameter 且 innerWidth<=900 時開右抽屜)開啟;面板只在接受後才 `closePanels()` | app.js diff |
| G-10 | 卡片鍵盤路徑 [通則] :Tab 到 `.card-enter`,Enter 與 Space 各一次,分別對 workspace 型與 inspector 型卡 | workspace 型(boundary/space/assembly/grid-binding/無限格線 system)走既有進入且 `closePanels()`;inspector 型走 G-08/G-09 同語意;Space 不捲動頁面 | app.js:2257-2278 |
| G-11 | 回歸:正常 guide 建立/移動/刪除、角材放置流程不受影響(各做一次 happy path);Save -> 新空白 -> Open 後 guide 仍在且 ID 不變 [通則:保存/重開] | 與 main 行為相同(除缺陷修正外);重開後 dump 逐字一致 | PR 本文「normal drag/picker creation once, move and visible face undo/redo」 |
| G-12 | console | 無未捕捉例外 | PR 本文 |

## 3.4 既有自動化(輔助)
- `node --test tests/test_source_inspector.js`:PR 稱 25/25(含新增 guidePreparationHarness/guideCallerHarness 的 VM 探針);這是 `vm.runInNewContext`
  把 app.js/reference-ui.js 片段丟進沙盒,**不是瀏覽器**;需要 `GEOMETRY_TEST_BRIDGE`(run_all.py:86 的 `'test_source_inspector': ['bridge']`)。
  可用環境變數 `GEOMETRY_REFERENCE_UI_JS`/`GEOMETRY_GUIDE_APP_JS` 指向 main 版檔案做 red 對照。
- 完整 CDP 與 Space、aggregate(68 suites / 2158 pass / 0 fail / 1 具名 Windows GDI skip)都是 PR 自述,對應舊 tree;資源重,建議不跑。
- CI:run 37409009040 七 job 失敗、steps 空,PR 自承原因未驗證。

---
# 四、跨 PR 事項
- #134 與 #156 都改 app.js、reference-ui.js;`git merge-tree --write-tree 77c3847 2a7d9cb` 無衝突(單獨驗收各自 head 即可,不需合併版)。
  #152 與兩者互不相交。三者各用獨立 checkout/埠/FEEDBACK_DIR,不並行啟動 Chrome(記憶體)。
- 順序建議:#152(輕,不需 bridge)-> #156 -> #134(P88 最重)。

# 五、歧義與缺口(需 owner 回答)
## 5.1 PR 文件互相矛盾/未寫清
- G-152-1 PR #152 本文第一段稱「僅新增 work-manager/」,`gh` 的檔案清單卻列出 app.js、source-inspector-app.js、space-workspace.css 等產品檔;
  我用 `git diff origin/main a15d73a` 確認**淨差異只有 work-manager 21 檔**(清單差異來自合併歷史)。請 owner 確認以淨差異為準。
- G-152-2 README.md:13 把 demo 匯入 `--data-dir /tmp/geometry-work-demo`,但 README.md:20 的 `serve --port 8765` 沒帶同一個 `--data-dir`,
  會讀預設 `.local/` 的另一份空資料。請 owner 確認 QA 應統一帶 `--data-dir`;`/tmp` 在 Windows 要換 `%TEMP%`;README 全用 `python3`,本機該名稱是 Store 別名。
- G-152-3 screenshot.py 固定 1440×1000;派工單要求桌面 1382×804。兩者是否都要(建議都做,1382 在 CSS 1100–1450 區間,1440 在 >=1450 前,
  寬度斷點行為可能不同,style.css:247)。
- G-152-4 面板「列印/存檔」、複製剪貼簿在自動化瀏覽器的預期未寫;我把 pass 定義成「兩種分支擇一並記錄」。需 owner 確認是否接受。
- G-152-5 空資料 / store_health invalid / 含 inventory 的面板狀態,README 與 PR 沒有 UI 預期文字;demo fixture 也涵蓋不到。
  要驗須自造合成快照(W-18/W-19)或舊版 SQLite(test_legacy_upgrade.py 內有建構法)。owner 決定是否列入必驗,否則降為「CLI 測試證據」。
- G-134-1 #134 PR 本文寫「實測與精確 head 會回填切片驗收紀錄」,但本 PR 沒有切片 2 的驗收文件;本文的證據綁在 `ea7b656`/`d1d51d8`,
  current head `77c3847` 是其後合入 main 的 merge。**所有數字(2159、P88=105 等)對 current head 均未驗**。DOM-CONTRACT/BACKLOG 的新段是我能找到的唯一契約。
- G-134-2 BACKLOG 說切片 2 後 #61/#62 不關閉,SR24 實體手機(觸控/鍵盤/IME/下載位置)與 iOS/Windows 人工待驗;QA 報告應明列「未驗」。
- G-134-3 R-03/R-04/R-17 的數值閾值(觸控高度、bounds 容差)在 P88 測試碼內,契約文字沒有;QA owner 若要嚴格判定需讀 grid_rule_lines_test.js 對應 check。
- G-156-1 #156 所述的瀏覽器腳本(caller9/9、guide9/9、card5/5)**不在 PR 內**,且延遲注入(「delayed first ID response」)沒有說明用什麼機制。
  我在 G-03 提議用 `window.fetch` 包裝延遲 POST `/api`;請 owner 確認可接受(它屬測試儀器,不改產品碼)。
- G-156-2 「取消的卡片檢查」需要先有未提交草稿才會觸發 `DraftGate.ask()`;PR 未說明用哪一種草稿。我暫列參數卡編輯或格線草稿,需 owner 或實測確認哪個真的會跳確認。
- G-156-3 PR 本文末段「Existing surface-ID0 picker behavior remains outside this fix」:surface ID 0 的 picker 行為不在本修復範圍,QA 遇到不要判失敗,只記錄。

## 5.2 需要 owner 事前回答/許可
1. 下載:W-11 匯出備份、R-16 的 ZIP 會下載檔案(只落 TEMP,約小檔),依規則下載需使用者許可;請明示授權檔名/來源/位置,否則 QA 只能用 CDP 攔截而不落地。
2. bridge 要不要用 WSL gcc 路線(start.ps1)還是 Windows 本機編譯;SAC 擋時的政策是否允許改走 WSL。
3. #152 是否真的要求 1440 與 1382 兩者;是否要求 XSS/匯出/唯讀 API(W-10~W-12)這些需造資料/下載/curl 的項目。
4. 是否允許 QA owner 啟動 Chrome 同時再跑 cdp_test(記憶體 ~650MB 風險);我建議 #134 的自動化只跑 `GEOMETRY_GRID_SYSTEM_ONLY=1`。
5. 時效:#152 fixture 24h 後 stale(2026-10-07T01:00Z),跨日需換預期。

## 5.3 我最不確定的三點
1. #134/#156 的 bridge 版本:`%TEMP%\geometry-tests\bridge.exe`(Oct 4 19:07)是否已含 main 的最後 native 改動(fedd15d,Oct 4 20:41 +08)。我只比時間戳,**沒驗**
   時區與二進位內容;若不重編,「基線在 main 重現缺陷」的對照可能是舊核心造成。
2. #134 R-02~R-11 的具體 DOM 互動序列是我從 P88 測試碼與 DOM-CONTRACT 新段推出,並未實際操作;`.face-rule-hit` 是否可鍵盤聚焦、
   點擊座標如何取(在 SVG 內),要實測才知,契約文字沒寫。P88 內部閾值(觸控高度等)我沒逐行讀完。
3. #156 G-03/G-08 的觸發方法(fetch 包裝、哪種草稿跳出 DraftGate)是我設計的重現配方,不是 PR 提供的;配方若無法在真 UI 重現 main 的缺陷,
   則對照組不成立,該條須回報「無法重現基線」而非 pass。
