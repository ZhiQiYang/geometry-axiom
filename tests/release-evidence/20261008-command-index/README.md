# 最小啟動與測試命令索引（2026-10-08）

本檔只整理現行來源裡的啟動與測試命令、工作目錄與前置條件。不是第二份產品說明，不是驗收通過聲明，也不是合併授權。沒有改產品語意、公理或安全設定。

## 身分

| 名稱 | SHA | 這份索引怎麼用它 |
| --- | --- | --- |
| main | `5cc1ffa1ee85120eca14258b86b715151cad274f` | 不是本工作樹。候選程式沒有進 main。 |
| 候選 #170 | `ce0958ca700753172338fe291a17e781da89465a` | 本索引的基底。分支 `docs/runbook-index-20261008` 從這裡開出。 |

`geometry-web/docs/RELEASE-CANDIDATE.md` 寫的整合分支名稱是 `codex/final-release-closeout-20261008`。那不是 main，文中的受測 head 也不能改標成 `ce0958c`。

PR161 原十項腳本與舊 155 項 UI oracle 仍是缺件。出處：`tests/INTEGRATION-GATES.md`、`geometry-web/docs/RELEASE-CANDIDATE.md`。沒有改寫成已找回。

Hosted CI run [37751080937](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37751080937) 的七個 jobs 在 step 前因帳務／支出限制失敗，`steps` 是空的。這是未執行，不是測試失敗，也不是通過。原文保留，這次沒有重查 GitHub。

## 標記

- **已實際執行**：這次真的跑了該命令。下面寫明它只證明什麼。
- **僅來源核對**：只對過現行檔案或文件，沒有跑該命令。`Test-Path` 與讀檔不算整條驗收已跑。

這次沒有開瀏覽器、沒有起服務、沒有跑 CDP 或大型測試。除下一節兩條 `wslpath` 外，啟動與測試命令都是僅來源核對。

## 已實際執行（只核對 WSL 路徑）

```text
wsl.exe -d Ubuntu-24.04 --user root --exec wslpath -u D:/geometry-axiom
wsl.exe -d Ubuntu-24.04 --user root --exec wslpath -u D:/geometry-axiom-docs-index
```

結果分別是 `/mnt/d/geometry-axiom` 與 `/mnt/d/geometry-axiom-docs-index`。WSL 另印了 systemd user session 警告，路徑仍有印出。沒有因此執行 `mutate.py`，也沒有啟動服務。

同一輪只確認檔案在不在：repository 根目錄沒有 `start.ps1`（在 `geometry-web/start.ps1`）；`geometry-web/reference_smoke.js` 不在工作區。這不是驗收。

## 啟動

### Windows 一般入口

來源：`geometry-web/start.ps1`、`geometry-web/README.md`、`geometry-web/start_local.py`。**僅來源核對。**

工作目錄是 repository 根。不要執行根目錄的 `.\start.ps1`，該路徑不存在。

```powershell
powershell -NoProfile -File .\geometry-web\start.ps1 -Port 8765
```

前置：Windows Python；WSL 發行版預設 `Ubuntu-24.04`（`-Distro` 可改）；該發行版有 `gcc`。連接埠已有服務時只探 `/runtime`，對得上目前版本才沿用並結束；對不上就拒絕，不開舊服務，也不停止其他程序。核心編譯到 `/tmp/geometry-tests/axiom-runtime-<guid>/`，不是 `%TEMP%\geometry-tests\bridge.exe`。`GEOMETRY_BRIDGE` 是 `wsl.exe` 指令字串。未設 `GEOMETRY_FEEDBACK_DIR` 時，回報寫進 repo 的 `feedback/`。`start.ps1` 裡沒有已證明失效的路徑註解，這次沒改它的行為。

```text
python3 geometry-web/start_local.py --port 8765
```

**僅來源核對。** `start_local.py` 在非 Linux 直接拒絕。Windows 不要貼這條。Linux 才用它；產物在 TEMP 下按 checkout 隔離，或 `--binary-dir` 指定的 TEMP 專用目錄。連接埠被占用就拒絕，不停止既有服務。

### 空間範例入口

來源：`geometry-web/README.md`、`geometry-web/start-space-model.ps1`。**僅來源核對。**

```powershell
powershell -File .\geometry-web\start-space-model.ps1 -Port 18841
```

工作目錄是 repository 根。前置：WSL／GCC／Windows Python，以及空閒連接埠。入口是 `http://127.0.0.1:18841/#engineering-spec-v1`。不停止其他服務。

### 版本探針

來源：`geometry-web/README.md`、`AGENTS.md` 的 GEO-231 描述（本輪未改 `AGENTS.md`）。**僅來源核對。**

```powershell
python geometry-web/runtime_version.py --probe 8765
```

從 repository 根執行。404、指紋不符、不同 repository、`fresh:false` 都不是成功。固定 `X-Geometry-Release` 不是目前程式版本。這次沒有對任何埠探針。不要停止或重用協調登記裡已占用的埠（登記寫 8915、8921、9521；本索引沒有再探）。

### 原生 Windows 編譯路徑

來源：`geometry-web/README.md`。**僅來源核對。**

```bat
cd geometry-web
build.bat
python serve.py 8765
```

這會在 repo 內產生 `geometry-web\web_bridge.exe`。Smart App Control 可能擋住新的未簽章 exe（WinError 4551）。它不是 fresh sidecar 的一鍵路徑。一般開啟仍用上一節的 `start.ps1`。`python serve.py 8765` 的埠引數與 `serve.py` 檔頭一致。

## 非瀏覽器測試

來源：`tests/README.md`、`tests/binaries.py`、`tests/_bridge.py`。**僅來源核對。** 工作目錄是 repository 根。

```powershell
python tests/binaries.py status
python tests/run_all.py
python tests/run_all.py --build
```

Windows 產物在 `%TEMP%\geometry-tests\`：`core.exe`、`bridge.exe`、`model-base.exe`，旁有 `.fingerprint.json`。Linux 同一登錄是 `/tmp/geometry-tests/`，檔名沒有 `.exe`。SAC 擋住時，`binaries.py` 等 15 秒、最多 3 次；仍擋則報環境阻擋且不寫 sidecar。完整 `run_all.py` 的 exit 0 只代表已登錄的非瀏覽器 suites，不是 CDP。`--only` 不能當完整驗收。

手動編譯後若把 `GEOMETRY_TEST_BRIDGE` 指到 `geometry-web\web_bridge.exe`，現行 `_bridge.py` 仍要求 fresh sidecar，否則 `SkipTest`。編譯步驟本身不寫 sidecar。

建模與 bridge 契約還要已核對的 exe。**僅來源核對。**

```powershell
$env:GEOMETRY_TEST_BRIDGE = "$env:TEMP\geometry-tests\bridge.exe"
$env:GEOMETRY_MODEL_BASE = "$env:TEMP\geometry-tests\model-base.exe"
python tests/test_modeling_runtime.py
python tests/test_bridge_integrity.py
```

`test_modeling_transport.py` 兩支都要。只設一個會在來源說明裡碰到 `BASE_COMPILER` 或假的 `KeyError`。缺編譯器時不要把 skip 記成產品失敗。

WSL 上的變異裁判，來源是 `tests/README.md`。**僅來源核對。**

```sh
cd /mnt/d/geometry-axiom-docs-index
ulimit -s 65536
python3 tests/mutate.py
```

主工作樹才是 `/mnt/d/geometry-axiom`。必須換成這份 checkout 的 `wslpath`。這條不驗證 Windows GDI。不要對其他正在使用的工作樹執行。

## 瀏覽器測試

這次沒有跑。來源：`geometry-web/README.md`、`geometry-web/cdp_test.js`、`geometry-web/space_model_test.js`、`geometry-web/canvas_test.js`。**僅來源核對。**

工作目錄是 `geometry-web`。先在別的終端用同一個 `GEOMETRY_FEEDBACK_DIR` 啟動獨立埠。不要沿用正在使用的服務。

```bat
cd geometry-web
set GEOMETRY_TEST_URL=http://127.0.0.1:8799/
set GEOMETRY_FEEDBACK_DIR=%TEMP%\geometry-tests\fb-cdp
node cdp_test.js
```

`cdp_test.js` 與 `space_model_test.js` 在開啟瀏覽器前就要求 `GEOMETRY_TEST_URL`，以及位於系統 TEMP 之下的絕對 `GEOMETRY_FEEDBACK_DIR`。未設時不會連到 8765，也不會重置場景。服務與測試必須指向同一實際目錄。Windows 用 `%TEMP%\...`，WSL 用該次服務看得到的 `/tmp/...` 或 `/mnt/<磁碟>/...`，不要混用。

```bat
node canvas_test.js direct
```

`direct` spawn 的是腳本同目錄的 `web_bridge.exe`，不讀 `GEOMETRY_TEST_BRIDGE`，也不檢查 fresh。不加 `direct` 且未設 `GEOMETRY_TEST_URL` 時，預設打 `http://localhost:8765/api`。

WSL 全內配方（`geometry-web/README.md`）的 `gcc -o /opt/geometry/web_bridge` 假設工作目錄是 `geometry-web`。`GEOMETRY_TEST_URL` 與 `GEOMETRY_FEEDBACK_DIR` 在該段的 `node cdp_test.js` 有設。Chrome、Node 與 `/opt/geometry` 是否已安裝，見下方待確認。

Linux 交付閘來源是 `tests/INTEGRATION-GATES.md`、`tests/release_gate.py`。**僅來源核對。**

```sh
python3 tests/release_gate.py --url http://127.0.0.1:18970/ \
  --output /tmp/new-release-evidence -- node geometry-web/cdp_test.js
```

呼叫端仍須先設與服務相同的 TEMP `GEOMETRY_FEEDBACK_DIR`，以及 receipt-backed 的 `GEOMETRY_TEST_BRIDGE`、`GEOMETRY_MODEL_BASE`。`release_gate.py` 只替子行程寫入 `GEOMETRY_TEST_URL`。`--output` 必須在 checkout 外且是新目錄。exit 0 只覆蓋該次命令，不是完整產品驗收，也不是合併授權。Windows 不要原樣貼 `/tmp` 與 `python3`。`start_local.py` 不能在 Windows 執行。

## 回報工具

來源：`geometry-web/feedback_cli.py`、`geometry-web/README.md`。**僅來源核對。** 工作目錄是 repository 根。

```powershell
python geometry-web/feedback_cli.py replay <id>
```

載回世界用的是 `GEOMETRY_CORE`，預設 `%TEMP%\geometry-tests\core.exe`。`run_all.py` 設的是 `GEOMETRY_TEST_CORE`，不會自動帶入。回報目錄是 `GEOMETRY_FEEDBACK_DIR`，預設 repo 的 `feedback/`。

## 來源待確認

1. `python -m unittest tests.test_bridge_integrity` 是否仍失敗：`AGENTS.md` 寫會因 `import run_tests` 失敗；現行 `tests/test_bridge_integrity.py` 沒有 `import run_tests`。這次沒跑，所以 `tests/README.md` 那句「兩種方式都能跑」沒有整段刪掉。
2. `geometry-web/README.md` 的 WSL 一次性路徑 `/opt/geometry`、`/opt/node`、`google-chrome` 是否已存在：文件要求事先準備，這次沒有在 WSL 列出這些路徑。
3. `RELEASE-CANDIDATE.md` 的「目前整合分支」與 `INTEGRATION-GATES.md` 的「包含 main `5cc1ffa` 與 PR162 候選 `bc1f6fe`」都沒改。後者兩個 SHA 仍是 `ce0958c` 的祖先，但不是 tip 的完整描述。
4. Hosted CI 與 10／155 缺件只轉述 repo 內原文，這次沒有重查 GitHub。
