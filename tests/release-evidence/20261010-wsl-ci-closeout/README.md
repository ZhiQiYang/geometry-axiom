# 2026-10-10 收攏鏈的 WSL CI 等價驗證收據

本目錄收存 PR #180（`fix/closeout-wsl-red-20261010`，合併 head
`6615db613a75fbad43116d85251782b5083479df`，簡稱 `6615db6`；merge commit `c254e1f`）
在合併前用 WSL 跑的 GitHub Actions 等價驗證，以及相關探針與判讀。全部是文件/證據，不含產品碼。

> **先讀這段。** 這裡的「7 個 job 全過」是**本機 WSL 自訂條件**下的結果，**不是 GitHub Actions 的結果，
> 也不是「原 CI 全條件通過」**：runner 時限是原 CI 的 ×3；native（1167.9 秒）與 canvas（2662.7 秒）
> 都超過原 CI 的 15／35 分鐘上限；assembly、grid（以及 timber）是 workflow 設計上的 partial 範圍，
> 沒有 golden 比對；七個 job 是分七次獨立呼叫跑的。細節見下面「測試條件」。
> 本 PR 的收據只覆蓋 `6615db6`，**不覆蓋 #182、#184**。

導覽：各 job 原始 log 出自哪一輪、命令與退出碼、sha256、互斥紀錄、二進位身分、P73 診斷／還原版來源，
以及所有「缺失」項，集中在 [`PROVENANCE.md`](PROVENANCE.md)；所有原始檔雜湊在 `SHA256SUMS`。

## 為什麼用 WSL 代替 CI

GitHub Actions 因帳號計費被阻擋，無法當合併裁判。改用本機 WSL2
（Ubuntu 24.04, Chrome 153）執行與 `.github/workflows/integration-tests.yml`
等價的流程：從受測 SHA 自己的 workflow 讀出 job、env、matrix 與 run script，
在 clean detached clone 上逐字執行；`actions/checkout` 以本地 clone 取代、
artifact upload 略過（無處上傳）。

## 測試條件（與原 CI 的差異，不得省略）

### 環境與流程差異

| 項目 | 原 CI（`6615db6` 的 workflow） | 這些收據 |
|---|---|---|
| 執行環境 | GitHub `ubuntu-latest` runner | 本機 WSL2：Ubuntu 24.04.5 LTS、kernel 6.6.114.1-microsoft-standard-WSL2、12 CPU、7559 MB（最後一輪 R7 的 `tools` 紀錄；前六輪的 `tools` 沒存，只知道前後兩個有紀錄的時間點相同） |
| 工具版本 | 映像自帶 | Chrome 153.0.8010.47、Node v24.21.0、npm 11.19.0、Python 3.12.3、gcc 13.3.0、git 2.43.0 |
| 時限 | `timeout-minutes`：native 15、assembly 15、documents 10、grid 15、canvas 35、space 15、timber 20 | hard watchdog = 原時限 **×3**；超過原時限只標記、不判紅，撞到 watchdog（exit 124）才紅 |
| checkout／artifact | `actions/checkout`、`actions/upload-artifact` | 以本地乾淨 clone（`core.autocrlf=false`，detached 在受測 SHA）取代；upload 略過 |
| 字型安裝 | `apt-get install fonts-noto-cjk` | 略過（`fonts-noto-cjk 1:20230817+repack1-3` 已安裝；runner 只在「全部已安裝」時才略過，從不 sudo） |
| 路徑／埠號 | `/tmp/...`、埠 18839 | `/tmp` 路徑與埠號逐 job 改寫（browser job 18841–18846）；私有 mount namespace 隔離 `/tmp/geometry-tests`；補 `python -> python3` shim |
| 暖機與等待 | 無 | 開跑前有界等待安靜、預熱 Chrome／gcc／node 的 page cache（只有 R7 的耗時有記錄：Chrome 38.8 秒、gcc 1.3 秒、node 2.9 秒） |
| 並行度 | matrix `max-parallel: 2`（不同 runner） | 這七個 job 是**七次獨立的 `wsl_ci.sh` 呼叫、依序單獨執行**（R1–R7，時間不重疊），不是一次 `all` |
| 呼叫入口 | — | 沒有經過後來才建立的排隊鎖（`wsl_locked.sh` 建於 10-11） |

### 時限對照

| job | 原 CI 上限 | WSL watchdog（×3） | 實測 | 對原上限 |
|---|---|---|---|---|
| native | 15 分（900 秒） | 45 分 | **1167.9 秒（19 分 28 秒）** | **超過，×1.30（多 267.9 秒）** |
| assembly | 15 分 | 45 分 | 287.5 秒 | 內，×0.32 |
| documents | 10 分 | 30 分 | 68.9 秒 | 內，×0.11 |
| grid | 15 分 | 45 分 | 620.8 秒 | 內，×0.69 |
| canvas | 35 分（2100 秒） | 105 分 | **2662.7 秒（44 分 23 秒）** | **超過，×1.27（多 562.7 秒）** |
| space | 15 分 | 45 分 | 301.4 秒 | 內，×0.33 |
| timber | 20 分 | 60 分 | 172.8 秒 | 內，×0.14 |

比值由實測秒數除以原上限秒數自行核對（1167.9/900＝1.298；2662.7/2100＝1.268），與各 `*-result.json`／`receipt.json` 的
`ci_limit_ratio`（1.3、1.27）一致。這兩個 job 在原 CI 時限下會不會過，**未驗**（硬體不同，不能由此推論）。

### 範圍：哪些 job 是 partial（哪一輪、哪些部分）

「partial」是測試 harness 自己的 `scope.mode`。assembly 與 grid 是 workflow 設計上的子集
（`GEOMETRY_ASSEMBLY_ONLY=1`／`GEOMETRY_GRID_SYSTEM_ONLY=1`，只跑 `cdp_test.js` 的部分段落），
不是 WSL 才有的降級；但它們**沒有 golden 比對**，不能代表完整 canvas 流程，也不能寫成「完整通過」。

| job | 輪 | harness 範圍 | 實跑內容 | 斷言 | golden |
|---|---|---|---|---|---|
| native | R1 | `run_all.py --build` 全 83 suite | 與 `tests/run_all.expected.json` 逐項相符 | 2610 過／0 敗／1 允許 skip（合計 2611） | — |
| assembly | R2 | **partial**（`GEOMETRY_ASSEMBLY_ONLY`） | 段落 P77（134）、P82（16） | 150／0 | 不比對（partial mode） |
| documents | R3 | 無 scope 欄位 | `documents_browser_test.js` | 47／0 | — |
| grid | R4 | **partial**（`GEOMETRY_GRID_SYSTEM_ONLY`） | 段落 P70（117）、P71（9）、P78（23）、P87（60）、P88（137） | 346／0 | 不比對（partial mode） |
| canvas | R5 | **full** | 全部段落 | 2207／0，`completed:true` | matched（84 段） |
| space | R6 | full-space-suite | 略過 `timber-material`、`timber-source-guards` | 228／0 | — |
| timber | R7 | **partial**（`GEOMETRY_TIMBER_ONLY`） | `timber-material`、`timber-source-guards`、`font-layout`；略過 `space-height-library`、`projection-lifecycle`、`projection-placement`、`space-flow` | 79／0 | — |

assembly 與 grid 的各段落，在 canvas（full）那一輪也跑了且計數相同（P77 134、P82 16、P70 117、P71 9、P78 23、P87 60、P88 137）。

### 不覆蓋的範圍

- 本 PR 的收據只針對 `6615db6`（#180 合併 head，tree 與 merge commit `c254e1f` 相同）與其 P73／⑤ 驗證。
  **#182、#184 的 head 不是 `6615db6`，本目錄不覆蓋它們**；它們各自的驗證不在本 PR，也不能引用本目錄當證據。
- 沒有任何 GitHub Actions 執行紀錄。

## Runner 與裁判規則

`runner/` 是當時的執行器（`wsl_ci.sh` 入口，`ci_run.py`/`ci_job.py` 主體，
`make_teeth.py` 牙齒驗證產生器，`baseline_sources.txt` 基線清單）。
三條裁判規則：

1. **Timeout**：hard watchdog = yml 的 `timeout-minutes` × 3.0。超過 CI 上限只標記
   不判紅；撞到 watchdog（exit 124）才是紅。
2. **Flaky**（僅 native）：失敗 suite 在同一 clone 單獨重跑（至多 2 次），只有
   「重跑通過且每個失敗 test id 在 main 基線收據裡也失敗」才算 flaky-rerun-pass；
   瀏覽器 job 任何斷言失敗即紅，不可免除。
3. **Exclusive**：開跑前有界等待其他 session 的編譯/測試行程結束，跑程中每 15 秒
   取樣，兩者都記錄。**注意：這些互斥紀錄寫在聚合 `receipt.json` 的頂層、每次呼叫覆寫一次，
   所以 `receipts/6615db61/receipt.json` 的互斥／暖機／工具版本只屬最後一輪（timber）；
   前六輪的逐輪互斥紀錄缺失**，見 `PROVENANCE.md` §4。

**牙齒驗證**：`receipts/345fabb5-teeth/` 證明裁判不是橡皮圖章——在 main 上加一個
只存在 WSL 的突變 commit（M1 恆錯斷言、M2 首次必敗非基線、M3 基線已知 flake
首次注入），native 如預期紅並點名 M1/M2、M3 被正確免除。

## 合併 head `6615db6`：WSL 自訂條件下 7 個 job 全過（無 flaky-rerun-pass）

收據 `receipts/6615db61/`。**`receipt.json` 與其 `README.md` 的總結 verdict「7/7 green」是最後一輪（timber）
把前面各輪的 job 結果合併出來的聚合版**；逐 job 的原始 log／結果在同目錄的 `<job>-job.log`、`<job>-result.json`
（native 另有 `native-run_all-logs/`）。上節的條件全部適用。

| job | 輪 | exit | 斷言 | 原始 log／結果（`receipts/6615db61/`） |
|---|---|---|---|---|
| native | R1 | 0 | 2610 過 / 0 敗 / 1 允許 skip（合計 2611，83 suite，與 `tests/run_all.expected.json` 完全相符） | `native-job.log`、`native-result.json`、`native-run_all-logs/` |
| assembly | R2 | 0 | 150 / 0（partial，P77＋P82） | `assembly-job.log`、`assembly-result.json` |
| documents | R3 | 0 | 47 / 0 | `documents-job.log`、`documents-result.json` |
| grid | R4 | 0 | 346 / 0，completed:true（partial，P70／P71／P78／P87／P88） | `grid-job.log`、`grid-result.json` |
| canvas | R5 | 0 | 2207 / 0，completed:true，golden matched（84 段），P73 ✓ | `canvas-job.log`、`canvas-result.json` |
| space | R6 | 0 | 228 / 0（full-space-suite，略過 timber 兩群組） | `space-job.log`、`space-result.json` |
| timber | R7 | 0 | 79 / 0（partial） | `timber-job.log`、`timber-result.json` |

其他收據：`5cc1ffa1`（main 基線）、`a7bff8f4-pr169`、`72a3cbf4-pr179`
（PR #179 head，grid/canvas 紅的修前基線）、`798d8387-p73-baseline`（`6615db6` 的父提交，
P73 紅的修前基線）、`5bf5a6d5-p73-timing` 與 `c7ed80aa-p73-revert`（P73 驗證，見下）。

## P73 判讀（全文：`p73-verdict.md`；來源綁定：`PROVENANCE.md` §7）

`6615db6` 把 canvas P73 的固定 `sleep(180)` 改成等 `[data-edit-guide]` 列實際渲染
（上限 30 秒）。因為改的是測試，合併前做了三項驗證：

- 加時間戳重跑：`!oc.busy` 成立到 DOM 列出現實測 **437ms**——舊 180ms 真的不夠，
  新等待是確定性完成條件，不是掩蓋。該次 canvas 全綠（6615db6 第二次確認）。
  原 log：`receipts/5bf5a6d5-p73-timing/canvas-job.log` 第 1747 行
  `P73_WAIT_MS {"createToBusyClearMs":190,"busyClearToRowMs":437}`。這是**單一樣本**，
  且 `wait()` 以 50ms 間隔輪詢，437 是約 50ms 解析度的上界。
- 還原 `sleep(180)` 重跑：同一斷言必紅（`receipts/c7ed80aa-p73-revert/`，`canvas-job.log` 第 1747 行 ✗），
  與修前基線 `798d8387`（`receipts/798d8387-p73-baseline/`）逐項相同。
- FATAL_UI 裡的 `connection.error`「無法確認載入結果」是 **P61-10/P61-11 刻意
  注入斷線測試留下的殘留欄位**（復原後沒有程式清它），通過的 run 也存在，
  與 P73 成敗無因果。

診斷版（`5bf5a6d5`）與還原版（`c7ed80aa`）是只存在 WSL 的本地提交，**git 物件拿不到**；
`p73-source/` 附產生它們的腳本、重生的 patch，以及用來源指紋把重生狀態綁回原 log 的比對
（診斷／還原狀態的指紋與原 WSL log 記錄相符），做法與限制見 `PROVENANCE.md` §7.2。

## ⑤ 探針（Issue #123 空間卡第二下點擊被 #btnZoom 接走）

`q5-probe/`：忠實移植原始重現（空間卡 `.ocard[data-kind="space"][data-id="1"]
.ocard-frame` 真實雙擊，只用 `Input.dispatchMouseEvent`），slots/beam ×
1400/390 四格。這是 WSL 內的探針，不是原 CI job。結果：

| SHA | slots-1400 | slots-390 | beam-1400 | beam-390 |
|---|---|---|---|---|
| main `5cc1ffa1` | ✓ | **✗ 落在 #btnZoom** | ✓ | ✓ |
| 鏈頂 `72a3cbf4` | ✓ | ✓ | ✓ | ✓ |
| 合併 head `6615db6` | ✓ | ✓ | ✓ | ✓ |

main 的失敗訊息指名 `#btnZoom`，且 4 取 1 敗圖樣與原始證據一致——探針有牙齒。

## 未驗項

- **GitHub Actions 上的實際執行**：從未跑過（計費阻擋）；本目錄所有結果都是 WSL 自訂條件。
- 原 CI 時限下 native、canvas 是否通過（兩者在 WSL 都超過原上限）。
- assembly／grid／timber 的 partial 範圍以外的部分，除非在 canvas／space 那輪另有覆蓋（見上表）。
- #182、#184 的 head（本目錄不覆蓋）。
- 實機（非 WSL2 虛擬機）上的瀏覽器行為。
- Windows 原生環境的全量測試（native 基線只在 WSL/Linux 跑過）。
- Resume 的當機、重載、跨 session 情境（本次只驗 bounded Resume，收據見
  `tests/evidence/cloud-takeover-20261009/safe-resume/`）。
- Issue #123 其餘 43 項已知競態（本次只驗 ⑤ 空間卡雙擊）。
- 缺失的原始紀錄（前六輪的命令原文與呼叫端退出碼、逐輪互斥、二進位檔雜湊、兩個 WSL-only 提交的 git 物件等）：
  完整清單見 `PROVENANCE.md` §8。

## 目錄索引

| 路徑 | 內容 |
|---|---|
| `README.md` | 本檔：結論、測試條件、結果表 |
| `PROVENANCE.md` | 補件：七輪出處、命令與退出碼、sha256、互斥、二進位身分、P73 來源綁定、缺失清單 |
| `SHA256SUMS` | 本目錄所有原始證據檔（不含 README.md、PROVENANCE.md、SHA256SUMS、.gitattributes 這四個說明／設定檔）的 sha256；在本目錄執行 `sha256sum -c SHA256SUMS` |
| `.gitattributes` | `* -text`：任何平台 checkout 都不轉行尾，雜湊才對得上 |
| `p73-verdict.md` | P73 判讀全文 |
| `runner/` | 當時的執行器 |
| `receipts/6615db61/` | 合併 head 的聚合收據＋七個 job 的原始 log／結果 |
| `receipts/5cc1ffa1/`、`345fabb5-teeth/`、`a7bff8f4-pr169/`、`72a3cbf4-pr179/` | main 基線、牙齒驗證、#169、#179 |
| `receipts/798d8387-p73-baseline/`、`5bf5a6d5-p73-timing/`、`c7ed80aa-p73-revert/` | P73：修前基線、計時、還原 |
| `p73-source/` | P73 診斷／還原版的產生腳本、重生 patch、指紋重算腳本 |
| `q5-probe/` | ⑤ 探針 |

## 路徑說明

各收據 README 與 log 裡出現的絕對路徑
（`/mnt/c/Users/Yang/.../scratchpad/`、`/root/ga-ci/`、`/tmp/ga-ci/` 等）
是當時本機 WSL 執行環境的實際路徑，為收據的一部分，不應視為可重現的固定位置。

另外：`q5-probe/*/build.log.txt` 與 `server.log.txt` 原檔名是 `build.log` /
`server.log`，因 root `.gitignore` 全域忽略這兩個檔名，收進來時加了 `.txt`
後綴，內容未改動。
