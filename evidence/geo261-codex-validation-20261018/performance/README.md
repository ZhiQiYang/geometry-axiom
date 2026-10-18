# GEO-261 效能量測工具

來源快照、原生建置、正式 normal 與 gprof 已完成；2026-10-18 六個瀏覽器 job 結束後，兩個量測 stage 均退出 0。結果與限制見 [第三階段正式報告](phase3-performance-report.md)。後續修正量測仍須在機器沒有其他測試或建置時執行 `measure` 與 `profile`。所有程式與產物都在本目錄，原始 `/workspace/geometry-axiom` 只接受讀取 Git objects；不切換分支、不建立 worktree。

固定比較 main `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425` 與整合分支 `e64aa6359d600f43313ec9d7ba1112c465b6a40c`。這是歷史 pinned 比較；不會把後來更新的遠端 head 混進結果。

預設維持以上兩個 SHA。後續量測已提交的修正候選時，可明確使用 `--integration-sha <完整40位SHA>`；另有 `--main-sha`。只接受完整小寫 SHA，並必須使用新的 `--output`；若目錄已屬於另一組來源即拒絕，不覆蓋或混用舊證據。每一個 prepare/build/measure/profile 階段都須傳同一組參數。這項參數化僅經 AST 語法檢查，尚未用於新候選量測；工作負載與計時方法未改變。

## 執行

```bash
python3 /workspace/geo261-validation-20261018/performance/measure_geo261.py prepare
python3 /workspace/geo261-validation-20261018/performance/measure_geo261.py build
python3 /workspace/geo261-validation-20261018/performance/measure_geo261.py measure
python3 /workspace/geo261-validation-20261018/performance/measure_geo261.py profile
```

`prepare` 用 `git archive` 建立兩份隔離的原生來源快照，保留原始 bytes（包含 `current_geometry.c` 的 CRLF），記錄每個檔案雜湊。只取原生 `.c/.h/.inc` 與建置 registry 等必要檔案；不讀取或複製 `.codex/`、`feedback/`，也不複製歷史 evidence。兩版的 `room_a.scene` 必須 bytes 全等，才建立共用輸入。

`build` 依序編四個正常 binary 與四個 gprof binary。兩版皆使用同一 `gcc`、`-std=c11 -O2`；profile 另外加 `-g -pg -fno-omit-frame-pointer`，不關閉內聯或其他最佳化。可用 `--cc /absolute/path/to/gcc` 指定。未修改產品檔案、依賴、測試或任何斷言。

所有 stage 可以分開重跑。建置會沿用指令、編譯器版本、來源 pin 及 binary 雜湊全部相符的產物；身份不同時拒絕覆寫，請另給 `--output /workspace/geo261-validation-20261018/performance/另一個目錄`。量測每次建立新 run 目錄，保留失敗日誌；不覆寫舊量測。

預設冷啟動 7 次、常駐行程 15 輪、每種 model-base 模式 7 次。若 gprof 的 self samples 太少，可在 profile 階段增加輪數：

```bash
python3 /workspace/geo261-validation-20261018/performance/measure_geo261.py profile --cold-repeats 12 --rounds 60 --model-repeats 12
```

程式設定至少 16 MiB stack，每條命令預設逾時 120 秒。`--timeout` 可明確調整。所有版本與工作負載依序執行；工具內的 lock 防止同一輸出目錄兩份量測互撞，但不會停止其他程序。失敗不計成成功樣本，也不自動改斷言或跳過失敗命令。

## 真實建置與 gprof 覆蓋

已檢查兩個 pin：本次產品入口是 `geometry-web/start_local.py` → `tests/binaries.py::_compile`；這兩個 pin 都沒有 `geometry-app/native/build.py`。腳本從各自 archive 載入實際 registry，以攔截 compiler invocation 的方式取得原始 argv，然後加量測旗標；不使用自行猜測的建置命令。

`web_bridge.c` 與 `model_base.c` 都 include `current_geometry.c`，後者再由 `kernel_unity.inc`、`woodworking_unity.inc`、`candidate_unity.inc` 等 include 真正的原生 `.c`。因此這兩個 pinned 產品 binary 是 unity translation unit，不可額外把被 include 的 `.c` 再 link 一次。

每次編譯使用 compiler 的 `-MMD` 產生**實際 dependency 閉包**；每個 `*.manifest.json` 列出真正編入的所有原生 `.c`、各檔雜湊及 `pg: true/false`。同時保留原始/實際命令、link map、undefined symbols，profile binary 必須含 `mcount` 或 `__fentry__`。若 registry 出現外部 `.o/.a`、不同旗標或另一本 `build.py`，工具會停下，避免未插樁的原生元件漏進結果。libc/libm 是系統函式庫，不聲稱它們有 `-pg`，所以 memcpy/memcmp 的歸屬仍需 perf 補充。

## 分段與成功條件

冷啟動每次啟動新 bridge，送一個 `dump`，計時從 `Popen` 前到第一個完整回應。這包含產品本來會做的預設世界建立；integration 的這段包含 9 條 DSL 加外層候選。冷啟動獨立列出，避免誤算成首條編輯的耗時。

常駐量測只有一個 bridge：先完成啟動 `dump`，再以 `section-profile-read` 收錄實際 World bytes，這兩筆不納入常駐各段統計。每輪依序使用完全相同的指令：

| 分段 | 指令 |
| --- | --- |
| reset | `reset` |
| load_scene | `loadfile <兩版共用 room_a.scene 絕對路徑>` |
| read_dump | `dump` |
| canvas_position | `line canvas-pos boundary 1 60 60` |
| unused_spec_create | `line spec PERF_VALUE 100` |
| unused_spec_replace | `line spec PERF_VALUE 200` |
| preview_spec | `line preview spec 主支1中線 900` |
| cancel_preview | `line cancel-preview` |
| read_final_dump | `dump` |

常駐每段從 write 前計時到讀完該段完整 JSON，後續解析與記錄時間不計入該段。每個回應必須是有效 JSON 且 `ok === true`；preview 另要求 `valid === true`；dump 必須帶字串 text；程序最終必須乾淨 EOF、退出 0，不能有額外無配對回應。所有原始 JSON 和 stderr 均保留。

model-base 使用相同共同場景，量從啟動到完整程序結束的時間：main legacy、integration legacy、integration `--neutral-sources`。預設 main e980cb0d pin 沒有 neutral 模式，因此不拿不存在的能力當失敗；若自訂 main pin，本腳本仍不量測其 neutral 模式，也不推定它是否支援。模型回應必須 `ok === true`、schema 正確、沒有未放置角材；neutral 另要求成功 legacySnapshot 與 neutralSources。摘要額外列出 integration 同一 binary 的 neutral 減 legacy 中位數差額，用來辨別完整來源圖的額外成本。

## 產物與判讀

預設產物在 `artifacts/`：

- `sources/<版本-SHA>/source-manifest.json`：原始 source bytes 身份。
- `build/<版本>/<normal 或 gprof>/`：binary、編譯 stdout/stderr、實際命令、原生閉包、link map。
- `inputs/`：共同場景、命令清單與雜湊。
- `runs/<台北時間-normal>/summary.csv`：各段樣本數、中位數、p95、min/max、相對 main 倍率；`samples.json` 保留逐次數值。
- `runs/<台北時間-gprof>/<版本>/<workload>/`：所有 `gmon.out`、`full-gprof.txt`、`flat-profile.txt`、完整 `callgraph.txt`、`functions.json`、`top20-self.csv`、`top20-inclusive.csv`、`top20-calls.csv`。
- `responses.jsonl`、`stdout.raw`、`stdout.json`、`stderr.log`：逐命令原文與模型原文；逾時也保留已捕獲輸出。量測錯誤另寫 `failure.json`，不產生 complete 成功摘要。

前 20 的「累積」定義為 callgraph 的 self + children，反映該函式與被呼叫路徑耗時；不是 flat profile 由上而下相加的 cumulative seconds。遞迴呼叫另列 direct/recursive calls；cycle 合計另存 `cycles.json`，不混進函式榜。gprof 使用取樣、內聯與 cycle 分配會限制精度，完整原文是判讀依據；profile 的時間不產生退化倍率，倍率只讀 normal 結果。

gprof 的常駐工作負載仍會含一次程序初始化，因為未在產品加入 profiler 控制碼；它與單獨的冷啟動 profile 分開保存。增加常駐輪數可以降低那一次初始化的占比。不要以這份工具的產出取代全量測試、瀏覽器驗收或修正前後及突變證據。
