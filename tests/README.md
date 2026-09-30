# 核心與保存完整性測試

## 一鍵入口

```sh
python tests/binaries.py status           # 每支原生二進位：fresh / stale / missing（stale 會說明是指紋不符還是沒有 sidecar）
python tests/binaries.py build [名稱…]    # 只重編 stale/missing 的；fresh 的印「沿用」且完全不碰檔案
python tests/run_all.py                   # 跑完所有非瀏覽器測試，印 suite / 測試數 / pass / fail / skip / 秒 / 備註
python tests/run_all.py --build           # 先 build 過期或缺少的二進位，再跑
python tests/run_all.py --only bridge     # 只跑名稱含子字串的 suite（可重複給）；--list 列出全部 suite 與其需求【局部跑，不能當完整驗收】
python tests/run_all.py --allow-skip      # skip 不影響 exit code
python tests/run_all.py --update-expected # 完整跑之後重寫 tests/run_all.expected.json（新增／刪除測試後才用）
```

**bridge 測試的共用模組 `tests/_bridge.py`**：所有靠 bridge 的 Python 測試（`test_bridge_integrity`、`test_reference_contract`、`test_datum_contract`、
`test_subgrid_contract`、`test_grid_system_contract`、`test_infinite_grid_contract`、`test_engineering_core`、`test_parameters_core`、
`test_engineering_model_sources`、`test_modeling_transport`）都只透過它找 bridge（`find_bridge()`）與說話（`BridgeSession`／`run_once`）。
環境變數統一為 `GEOMETRY_TEST_BRIDGE`（舊名 `GEOMETRY_ENGINEERING_BRIDGE` 仍讀、會印一次棄用提醒；`binaries.py` 與 JS 測試暫時還設／讀舊名）。
沒設變數時用 `binaries.py` 的 fresh bridge；stale／missing 一律 **skip 並說明怎麼建置**，**不會**再退回未檢查新舊的 `geometry-web/web_bridge.exe`（非 Windows 才會自動用 `cc` 編到 `/tmp/geometry-tests`）。
每個 `tests/test_*.py` 兩種方式都能跑：`python tests/test_x.py` 與 `python -m unittest tests.test_x`（在 repo 根目錄；`tests/__init__.py` 讓 `tests` 成為套件）。

**不重編的原因**：這台機器的 Smart App Control（SAC）會擋「新出現」的未簽章 exe（WinError 4551、`橋接器連線中斷`）。
`binaries.py` 給每支 exe 一個來源指紋（sha256：編譯指令＋主來源＋`current_geometry.c`＋`geometry-core/` 與
`geometry-web/` 下所有 `.c/.h/.inc`，CRLF 先換成 LF），寫在 exe 旁的 `*.fingerprint.json`；來源沒變就絕不重編。
編完會先啟動一次讓 SAC 評估，被擋就等 15 秒重試、最多 3 次，仍被擋則報「環境阻擋」且**不寫 sidecar**
（這支就不算 fresh；再跑 build 只重試啟動，不會再編一支新的）。「環境阻擋」與「編譯失敗」分開報。
所有產物在 `%TEMP%\geometry-tests\`（非 Windows 是 `/tmp/geometry-tests/`），不會寫進 repo。

| 二進位 | 來源 | 環境變數（`run_all.py` 會替子行程全部設好） |
|---|---|---|
| core（`core.exe`） | `current_geometry.c`（`/U_WIN32`，無視窗版） | `GEOMETRY_TEST_CORE`（`test_cli_args`）；`run_tests.py` 以參數吃；`polydraft_test.js` 固定讀 `%TEMP%\geometry-tests\core.exe` |
| bridge（`bridge.exe`） | `geometry-web/web_bridge.c`（`/U_WIN32`） | `GEOMETRY_TEST_BRIDGE`、`GEOMETRY_ENGINEERING_BRIDGE` |
| model-base（`model-base.exe`） | `geometry-core/model_base.c`（`/U_WIN32`） | `GEOMETRY_MODEL_BASE` |
| gdi harness（`gdi-contract.exe`，僅 Windows） | `tests/gdi_contract_harness.c` | `GEOMETRY_TEST_GDI_HARNESS`（`test_gdi_contract`） |
| integrity（`integrity.exe`） | `tests/test_core_integrity.c` | 無，`run_all.py` 直接執行 |
| engjson（`engineering-json-test.exe`） | `test_engineering_json.py` 內嵌的 `HARNESS` | `GEOMETRY_TEST_ENGINEERING_JSON`（第 6 個，只有 `test_engineering_json.py` 讀；沒設就照舊自己編） |

`run_all.py` 的 exit code（多種並存時取編號小的）：**0** 完整跑且全部成立（見下）；**1** 有 fail、suite 崩潰／逾時、發現數與 `run_all.expected.json` 不符、或 `tests/` 下有未登記的測試檔；
**2** 有環境阻擋或二進位過期（過期的 exe **不會**被拿去跑，相依的 suite 標「環境：二進位過期，未跑」）、canvas shim 沒有留下轉向標記、另一個 `run_all`／`build` 正在跑（鎖檔）；
**3** 只有 skip（`--allow-skip` 時不算）；**4** `--simulate-missing` 示範跑（否則會是 0；示範跑絕不回 0）。

**「exit 0」的意思**（只對完整跑成立，即沒用 `--only`／`--extra-py`／`--simulate-missing`）：每個 suite 都跑了；每個 suite 發現到的測試數與 `tests/run_all.expected.json`
**嚴格相等**（新增、刪除或少載入測試都會紅，並印「預期 N、實得 M」；沒登記的 suite 也紅；任何 py suite／node suite 發現 0 個測試一律紅）；沒有 fail；沒有 skip。
唯一的 skip 豁免是 `run_all.py` 裡的具名允許清單 `ALLOWED_SKIPS`：suite、完整 test id、理由子字串、平台四者都相符才算（目前只有 Windows 上
`py:test_cli_args` 的 `/dev/full` POSIX 測試）；其餘 skip 一律算 skip。`node:model_viewer` 是腳本式、只有結束碼，expected 裡標 `exit-code-only`，表格備註欄註明、測試數欄顯示 `-`。
用了 `--only`／`--extra-py`／`--simulate-missing` 的跑，結尾一律印「部分／示範執行，不可當完整驗收」並列出用了哪些旗標，措辭不會出現「全過」。
`--update-expected` 只能單獨用在完整跑；有環境問題、崩潰／逾時、0 個測試、不在允許清單的 skip 或未登記檔時拒絕重寫（有 test 級 fail 仍可記下發現數，例如目前的 `test_gdi_contract`，fail 與數量無關）。

Python 測試以 `tests/_unittest_runner.py` 跑，回報 test 級數字：class 級 `SkipTest` 算成它真正擋掉的 test 數；模組載入時就 `SkipTest` 的檔用 AST 數出它的 test 方法數（數不出來寫「至少 1」並在備註說明）。
**新增測試檔必須登記**：`tests/test_*.py` 進 `run_all.py` 的 `PY_NEEDS`（不需二進位也寫 `[]`）；`tests/*.js|*.cjs|*.mjs` 進 `NODE_TEST_FILES`／`NODE_SCRIPT_FILE`／`NODE_EXCLUDED`（夾具如 `reference_pdf_fixture.js` 放排除清單並寫理由）。未登記的檔會讓 run_all 判 fail 並指名。
子行程環境：外殼繼承來的 `GEOMETRY_*` 全部清掉，只留 run_all 自己設的（開頭的 `[環境]` 行會列出清掉了哪些、設了哪些；`CC` 照舊繼承並印出）。
逾時（每個 suite 各有上限）會殺掉整棵行程樹（Windows `taskkill /T /F`、POSIX 行程群組 SIGKILL），不是只殺直接子行程。
`binaries.py build` 與 `run_all.py` 各持一個鎖檔（`%TEMP%\geometry-tests\build.lock`、`run_all.lock`；行程結束由作業系統自動釋放），兩個同時跑會明確報錯退出（exit 2）。
`--simulate-missing GEOMETRY_MODEL_BASE` 可模擬缺少某個環境變數，檢查 skip 是否看得見（部分測試缺 bridge 變數時會改用舊的預設 exe，別拿它判定對錯）。

**不在一鍵入口內**：`geometry-web/cdp_test.js`、`geometry-web/space_model_test.js` 需要 Chrome，另行執行（見 AGENTS.md「跑 cdp_test」）；表格最後一列會提醒。
`canvas_test.js direct` 把 bridge 寫死成 `geometry-web/web_bridge.exe`（不檢查新舊、沒有覆寫），`run_all.py` 用一個暫存 preload 把那次 spawn 轉到 `GEOMETRY_TEST_BRIDGE`，測試檔本身不動；preload 只在真的改寫了那次 spawn 時才寫一筆標記檔，run_all 沒看到標記就把這個 suite 判為環境問題（exit 2）、備註寫明不採信。


GEO-223 參數卡：`python -m unittest tests.test_parameters_core`（同時設定 `GEOMETRY_TEST_BRIDGE` 與 `GEOMETRY_MODEL_BASE`），`node --test tests/test_parameters_project_store.js`。正式操作測試 `parameter_workflow_test.js` 已納入完整 `cdp_test.js`；`GEOMETRY_PARAMETERS_ONLY=1` 僅供開發，不能代替完整回歸。原生產物在 Windows 放暫存目錄。

GEO-130 建模執行器及實際 CLI／HTTP：

```sh
python3 tests/test_modeling_runtime.py
python3 tests/test_modeling_transport.py
```

18 組正式向量、獨立網格檢查與驗證界線見 `geometry-core/MODELING-VALIDATION.md`。

跨面共用基準的提案、逐條追溯與實際驗收見
[`DATUM-PROPOSAL.md`](../geometry-core/DATUM-PROPOSAL.md)、
[`DATUM-VALIDATION.md`](../geometry-core/DATUM-VALIDATION.md)。
新測試使用同一 C bridge，不在測試內另做幾何求解：

```sh
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/test_datum_contract.py
python3 tests/test_axiom_reader.py
```

`_ax_i7_guide_out_of_range.scene` 現為接受案例：I7 放寬的是參考線存在條件，
零可見段合法；網格生成限制與角材守門員並未放寬。

`run_tests.py` 驗證既有場景的接受／拒絕、尺寸與文字輸出。
`test_feedback_store.py`（GEO-183）驗證回報收件匣的寫入、編號、INBOX 與 `feedback_cli.py`，寫在暫存目錄、不需要 bridge。
`test_guide_panels.py`（GEO-175）驗證導讀頁每個面板的符號與 callout 都還在目前的 `current_geometry.c` 裡；
改 C 後若紅燈，改 `geometry-guide/make_guide.py` 的面板設定並重跑它。
`test_core_integrity.c` 驗證承載面重綁後的世界座標、Space 範圍、交易回滾及 undo/redo。
`test_bridge_integrity.py` 使用獨立 bridge 程序，驗證不完整指令、存檔重載、auto 支撐義務及所有接受型場景的幾何往返。

以下輸出目錄須先建立；執行測試時可在專案外工作，避免 SVG 測試產物覆寫工作中的圖。

Unix（gcc）：

```sh
mkdir -p /tmp/geometry-tests
gcc -std=c11 -O2 current_geometry.c -lm -o /tmp/geometry-tests/core
gcc -std=c11 -O2 geometry-web/web_bridge.c -lm -o /tmp/geometry-tests/bridge
gcc -std=c11 -O2 tests/test_core_integrity.c -lm -o /tmp/geometry-tests/integrity
/tmp/geometry-tests/integrity
python3 tests/run_tests.py /tmp/geometry-tests/core
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/test_bridge_integrity.py
```

Windows（本工作樹；MSBuild `cl`）：

```bat
mkdir %TEMP%\geometry-tests
tests\_clw.bat current_geometry.c %TEMP%\geometry-tests\core.exe
tests\_clw.bat tests\test_core_integrity.c %TEMP%\geometry-tests\integrity.exe
cd geometry-web
build.bat
cd ..
%TEMP%\geometry-tests\integrity.exe
python tests\run_tests.py %TEMP%\geometry-tests\core.exe
set GEOMETRY_TEST_BRIDGE=%CD%\geometry-web\web_bridge.exe
python tests\test_bridge_integrity.py
```

記憶體／未定義行為驗證：將編譯選項換成
`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer`，重跑同一組測試。

Windows 可用現有 `tests/_clw.bat` 編譯 C 測試；bridge 依 `geometry-web/build.bat` 使用 `/U_WIN32`。
以環境變數 `GEOMETRY_TEST_BRIDGE` 指定剛編譯的 bridge，避免測到過時的 exe。
上面兩段是手動流程，沒有任何新舊檢查（`geometry-web\web_bridge.exe` 是不在 `%TEMP%` 的舊習慣位置，也沒人驗它是不是最新）；
日常請用最上面的一鍵入口。手動用 `_clw.bat` 編的 core 是含視窗程式碼的版本，在本機曾被 SAC 連擋多次，一鍵入口的 core 改用 `/U_WIN32` 版（與 `_cl.bat`、`mutate.py` 一致）。

## 新公理與保存格式

2026-09-18 的 D6–D7 / I12–I13 已廢除自由座標、明寫角材長度與凍結保存。
`test_reference_contract.py` 驗證具名規格、有理引用、依賴重算、I8a 預覽／確認／取消、
過期預覽、奇數板縫、交易群組與引用往返。執行：

```sh
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/test_reference_contract.py
```

新版 dump 只保存引用式與 `at-line` / `at-face`，並依依賴順序重放。
舊 `at` / `at-guides` / `at-grid` / `at-edge`、明寫 L、`grid-ref`、`span-auto` 都拒絕；
不能從已丟失來源的裸座標反推引用。專案內示例已改成新規格，故意測拒絕的夾具保留舊輸入。
完整語法與核對紀錄見 [公理實作核對](../geometry-core/README.md)。

## 其餘缺陷的回歸

bridge 測試另涵蓋 32 組樑中線／奇偶寬度的三次重載、面分類保存、失敗放置的草稿與 redo、拖曳群組及取消，以及數值上限。
幾何定義座標／尺寸限於 ±100,000,000 mm；ID 仍可用完整 uint32 範圍。
`geometry-web/cdp_test.js` 的 P24–P30 會實際點擊樑的套用、拖曳並復原／重做，以及在兩種視窗寬度開啟檔案選單並載入範例；也檢查外框／孔四種方向組合的淨面積。
可用 `GEOMETRY_REPAIR_SCREENSHOT_DIR` 指定這組互動的額外截圖目錄。

## 測試檔一覽（一句話）

Python（`run_all.py` 逐檔跑；各檔需要的二進位見 `python tests/run_all.py --list`）：

- `test_axiom_reader.py`：公理層閱讀器同步腳本的完整性 assert（五道）。
- `test_bridge_integrity.py`、`test_reference_contract.py`、`test_datum_contract.py`：bridge 的存檔往返、具名規格／引用、跨面共用基準。
- `test_grid_system_contract.py`、`test_infinite_grid_contract.py`、`test_subgrid_contract.py`：格網系統（有限／無限）與子格網對 bridge 的黑箱驗收。
- `test_engineering_core.py`、`test_parameters_core.py`：工程規格與參數卡由真的 bridge 求值；`test_parameters_core` 的模型包／雜湊驗證獨立成一個 test，缺 `GEOMETRY_MODEL_BASE` 時顯示為 skip。
- `test_engineering_json.py`：工程內容 JSON／SHA-256／base64 的獨立原生小工具驗收（二進位由 binaries.py 提供，見 `GEOMETRY_TEST_ENGINEERING_JSON`）。
- `test_engineering_model_compatibility.py`、`test_engineering_model_sources.py`、`test_engineering_transport.py`：工程能力邊界與已知公理相容、原生工程來源經模型包的往返、工程傳輸層。
- `test_modeling_runtime.py`、`test_modeling_degenerate.py`、`test_modeling_transport.py`、`test_space_modeling.py`：建模執行器、退化幾何輸入、實際 CLI／HTTP、平面／面轉空間的建模驗收。
- `test_serve.py`：`geometry-web/serve.py` 的請求大小界線、路由、空指令與 bridge 框架（bridge 以 mock 代替，不需要 exe）。
- `test_witness_diagnostics.py`、`test_witness_marks.py`：見證圖的拒絕診斷要指名真實來源指令與規則；見證圖 SVG 的碰撞與停止標記獨立重算。
- `test_cli_args.py`：core 執行檔的命令列參數契約（子行程，不含視窗）；`test_gdi_contract.py`：Windows GDI 資源釋放的函式層整合（非視窗 E2E）。
- `test_feedback_store.py`、`test_guide_panels.py`：回報收件匣；導讀頁面板與 `current_geometry.c` 的一致。

Node（`node --test tests/*.js` 一次跑；`test_model_viewer.cjs` 是腳本式、以 exit code 判定）：

- `test_project_store.js`、`test_face_projection_store.js`、`test_space_model_store.js`、`test_engineering_project_store.js`、`test_parameters_project_store.js`：各版本專案封存檔的讀寫、降級拒絕與獨立保存。
- `test_reference_workspace_races.js`：參考圖工作區的排程競態（VM 內的假 DOM，不是 E2E）。
- `test_cdp_floor.js`：`cdp_test.js` 每段斷言數地板的純比對邏輯（不啟動瀏覽器）。
- `test_model_viewer.cjs`：模型檢視畫布的繪製呼叫契約。`reference_pdf_fixture.js` 只是夾具產生器，不是測試。

工具（不是 pass/fail 測試，`run_all.py` 不跑）：`fuzz_scene.py`（場景解析器的確定性 fuzz，固定使用已編好的 bridge）、
`mutate.py` 與 `mutants_results.json`（核心 C 原始碼的變異測試與其逐筆判決）、`run_tests.py`（場景夾具的接受／拒絕裁判，`run_all.py` 會以 core 呼叫）。

`mutate.py`（GEO-225 起）：`python tests/mutate.py` 整批跑、`<id>…` 只跑指定、`--check` 只讀結果檔並彙總、`--selftest` 驗它自己的誠實性機制。
每筆判決帶來源／include 閉包／變異／裁判（`run_tests.py` + 被 `TESTS` 引用的夾具）四組雜湊，任一與現況不符即標 `stale`、不計入 killed；
錨點找不到或不唯一標 `invalid`。變異 exe 依指紋快取在 `%TEMP%\geometry-tests\mutants\<id>\`，來源沒變就不重編（避免撞 Smart App Control）。
缺少 sidecar，或 sidecar 是舊版只憑結果紀錄補發的 `adopted` 身分，皆須重建；結果雜湊不能證明磁碟上的 exe 內容。
判決類別：killed / survived / equivalent / retired / blocked（環境阻擋或崩潰，見 決策佇列 Q28）/ invalid / stale。

Windows 的 SAC 持續擋住新編 exe 時，可使用已安裝的 WSL/GCC 執行同一裁判：

```sh
cd /mnt/d/geometry-axiom
ulimit -s 65536
python3 tests/mutate.py
```

Linux 變異程式快取在 `/tmp/geometry-tests/mutants/`，編譯指令也納入指紋；不共用 Windows exe。
結果仍由同一份 `run_tests.py` 與 138 個夾具判定。這不驗證 Windows 專用 GDI。
