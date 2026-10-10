# 補件：`6615db6` WSL 收據的出處、來源綁定與缺失清單

回應 PR #183 審查留言 issuecomment-6100284952（dot）。

**本檔只歸檔「已存在」的證據並說明出處：沒有重跑任何測試、沒有進 WSL、沒有補造任何紀錄。**
找不到的一律標「缺失」。每項結論都標明依據類型：

- 【記錄】本目錄內某個檔案直接記載（附檔名與行號）。
- 【推導】由記錄加上 runner 程式碼推出來，不是當時親眼看到的輸出；附推導依據。
- 【獨立重算】在 Windows 端用 git 物件重新算一次，與當時的 WSL 記錄比對。
- 【缺失】沒有紀錄。

原始檔來源：本機 scratchpad（下稱 SP）
`C:\Users\Yang\AppData\Local\Temp\claude\D--geometry-axiom\f46787ac-6918-4891-81a1-b3d8a9aa653c\scratchpad`，
收據在 `SP\wsl-ci\<sha 前 8 碼>[-標籤]\`。歸檔副本逐一用 `cmp` 與 SP 原檔比對為位元相同；
本目錄的 `SHA256SUMS` 記錄所有原始證據檔的 sha256，`.gitattributes` 設 `-text` 讓任何平台 checkout 都不改行尾，
`sha256sum -c SHA256SUMS`（在本目錄執行）應全數通過。

## 0. 對照 dot 的三點

| dot 要求 | 補件位置 | 仍缺 |
|---|---|---|
| 1. native、assembly、documents、grid、space、timber 六組 per-job 原始 log／results | `receipts/6615db61/<job>-job.log`、`<job>-result.json`（native 另有 `native-run_all-logs/`，190 個檔）；canvas 沿用既有 `canvas-job.log`，新增 `canvas-result.json`。逐 job 出自哪一輪見 §2 | 無（六組齊全）。注意 `receipt.json` 是 R7 的聚合版，見 §2、§4 |
| 2. 各輪命令、退出碼、完整 SHA／來源同一性、逐輪互斥、raw 雜湊、二進位身分 | §1（SHA 與來源同一性）、§2（輪次與雜湊）、§3（命令與退出碼）、§4（互斥）、§5（二進位）、`SHA256SUMS` | R1–R6 的命令原文、呼叫端退出碼、逐輪互斥／暖機紀錄；二進位檔本身的 sha256；見 §8 |
| 3. P73 計時原 log 與診斷／還原版來源差異 | §7；`receipts/5bf5a6d5-p73-timing/canvas-job.log:1747`（437ms）；`p73-source/`（腳本與重生 patch）；`receipts/798d8387-p73-baseline/` | 兩個 WSL-only 提交物件本身拿不到（只存在 WSL 的 `/root/p73-verify/src`），改以腳本＋重生 patch＋指紋比對綁定，見 §7 |

## 1. 受測對象與來源同一性

| 項目 | 值 | 依據 |
|---|---|---|
| 受測 SHA（PR #180 合併 head） | `6615db613a75fbad43116d85251782b5083479df` | 【記錄】七個 `*-result.json` 的 `sha` 欄、七個 `*-job.log` 第 1 行 |
| tree | `80b3ad21bf2d1b457ed9a360ae72e3497af42824` | 【獨立重算】`git rev-parse 6615db6^{tree}` |
| 合併提交 | `c254e1f1d6b0980170f3ffc8b855cd696654bd46`，parents = `5cc1ffa1ee85120eca14258b86b715151cad274f`（main 基線）＋`6615db6` | 【獨立重算】`c254e1f^{tree}` 與 `6615db6^{tree}` 相同，所以合進 main 的內容就是受測內容；`git diff --stat 6615db6 c254e1f` 為空 |
| 工作流程檔 sha256 | `faddb699f3be004bbfc5a8fe5948cf58a621d0826db4cd3bf0a77dc097be9fd0` | 【記錄】`receipts/6615db61/receipt.json` 的 `workflow_sha256`（R7 寫入）；【獨立重算】`git show 6615db6:.github/workflows/integration-tests.yml` 的 sha256 相符 |
| 來源指紋（`geometry-web/runtime_version.py` 的 `source_version`） | `290ebaee1760b3983e98fc4da27bc9154d3a151e2723e24265c4c129aaa2f070` | 見下 |

**來源指紋**是該腳本對 `current_geometry.c`、`公理層.md`、`geometry-web/`、`geometry-core/` 下的原始碼與靜態資產逐位元算出的 sha256，
路徑相對於 repo 根，所以與 clone 位置無關。它在七個 job 都出現：

- 六個瀏覽器 job：`assembly-job.log`、`documents-job.log`、`grid-job.log`、`canvas-job.log`、`space-job.log`、`timber-job.log` 的**第 52 行**
  （`runtime_version.py --probe` 輸出，`"fresh": true`），值全為上列 `290ebaee…`。【記錄】
- native：`native-run_all-logs/py_test_local_launcher.log` 第 1、2 行（`LOCAL_LAUNCHER_PATH_CHECK` 內嵌的 runtime 物件），值同為 `290ebaee…`。【記錄】
- 【獨立重算】：在 Windows 端以 `git clone` ＋ `git -c core.autocrlf=false -c core.eol=lf checkout --detach 6615db6` 取出乾淨 tree，
  用 `p73-source/runtime_fingerprint_posix_order.py`（載入該 tree 自己的 `runtime_version.py`，只把排序改成與 Linux 相同的區分大小寫；
  Windows 的 `Path` 排序不分大小寫，直接呼叫會得到不同值 `ed30c2cc…`；改成區分大小寫排序後即與記錄相同，所以判斷是排序差異不是內容差異）算出 `290ebaee…`，與七個 job 的記錄相同。

所以七個 job 的受測原始碼，與 git 裡的 `6615db6` 在指紋涵蓋範圍內位元相同，彼此也相同。
指紋**不涵蓋** `tests/`、`.github/`、`geometry-guide/` 大部分檔案等；那部分的同一性只靠「每輪都從 `6615db6` 的乾淨 clone 跑」這條推導：
`ci_run.py` 在每個 job 開跑前斷言 `git rev-parse HEAD == sha` 且 `git status --porcelain` 為空（【推導】來自 `runner/ci_run.py` 的 `do_job`，斷言失敗 job 就不會產生 `job.log`）。

## 2. 七個 job 各出自哪一輪

**事實：本收據是七次獨立的 `wsl_ci.sh` 呼叫（R1–R7），每次只跑一個 job，全部寫進同一個輸出目錄 `SP\wsl-ci\6615db61\`；
`ci_run.py` 每次結束都把「目錄內現有的所有 job 結果」合併成一份 `receipt.json`／`README.md`，後一輪覆寫前一輪**（【推導】：`runner/ci_run.py` 的 `main()` 聚合迴圈與 `write_text`；
輪次拆分本身的證據是下面列的 runid 與時間）。
所以現存的 `receipts/6615db61/receipt.json` 與 `README.md` 是 **R7（timber）那一輪的聚合版**，其頂層欄位只屬於 R7，不能代表前六輪。

依據：

- 七個 job 的 WSL 端 runid（`/root/ga-ci/runs/6615db61-<日期>-<時分秒>/<job>/repo`，見各 `*-job.log` 第 1 行）全不相同，分別是下表的 7 個。【記錄】
  若用 `all` 一次跑，七個 job 會共用同一個 runid。
- `receipt.json` 頂層的 `runroot` 是 `/root/ga-ci/runs/6615db61-20261010-180428`，即 timber 的 runid；`wall_seconds_this_invocation` = 193.2 秒
  （≈ timber 一個 job 的 172.8 秒＋clone），不是七個 job 加總（約 5282 秒）；`exclusivity.during_run.samples` = 12（每 15 秒一次，約 180 秒）。【記錄】
- `SP\wsl-ci\6615db61\` 下沒有任何 `<job>.prev-<stamp>` 目錄（`ci_run.py` 重跑同一個 job 時會把舊目錄改名成這個樣子），
  各 job 的 `seconds` 與 `seconds_first_run` 相同（差 0.1 秒是四捨五入），native 的 result.json 沒有 `flaky` 區塊。【記錄】
  所以每個 job 的結果都是該輪的第一次完整執行，沒有被較晚的重跑取代；也沒有看到被覆蓋的同 SHA 舊 job 目錄。
  （無法排除有人手動刪過舊目錄；那不會留紀錄。）

| 輪 | job | WSL 端 runid（`6615db61-…`） | 開始–結束（UTC+8，10-10） | 測試命令退出碼 | job 秒數 | 歸檔 log（`receipts/6615db61/`） | log sha256 | result.json sha256 |
|---|---|---|---|---|---|---|---|---|
| R1 | native | 20261010-163001 | 16:30:29–16:49:56 | 0 | 1167.9 | `native-job.log` | `f3d821f01a22d0faee4cf63e6da0d55a4a9a415ab0595e43a9af0e54d99584a9` | `cdb0436c0f62216efec01f149b291d98c93b61c2dd5f3e62ee773dc89ded180f` |
| R2 | assembly | 20261010-165030 | 16:50:52–16:55:39 | 0 | 287.5 | `assembly-job.log` | `0d1c8a0fb3dc70e7f298959e822de193b8cb1ae67d5f59398d9db364cdca9a22` | `6fe54653bc342ba683483f45da9a2949f1db270e7fcf5effe7ff2660afb0fbea` |
| R3 | documents | 20261010-165549 | 16:56:10–16:57:19 | 0 | 68.9 | `documents-job.log` | `6b8c1a5ee03843e4ed0a3d1ff4f7b0a501e01d59f14454f4e02b2b2483352a41` | `63e1709b0b116352acd24136f31382a92a5bdced0c87b22bab8d735139140b40` |
| R4 | grid | 20261010-165728 | 16:57:43–17:08:04 | 0 | 620.8 | `grid-job.log` | `7d53b41528377c822e68a0d661d550a3bef85e2804692ed48971c3177dabd686` | `203d8d92db281babb14c78f6e9c1a76b3245a3a2d13449fd81fa7e2140ba2c84` |
| R5 | canvas | 20261010-170814 | 17:08:42–17:53:04 | 0 | 2662.7 | `canvas-job.log`（既有） | `3e881320979763d5b4de8205f882b482c5f0d43624548158901359eff553bbb1` | `f50a44ecb89f537b204ad139d4588429c62e9f3dfd6d7802cb3d9e59b3a594fc` |
| R6 | space | 20261010-175532 | 17:57:14–18:02:15 | 0 | 301.4 | `space-job.log` | `871a1d5137a25ae93524e74f43d7b04dbd49c234e1cbde27d732051a0057d94c` | `f6ec7782f19eadc70fd32f49f5d237db79799f62e4762abcacc9f5f412f76382` |
| R7 | timber | 20261010-180428 | 18:05:35–18:08:28 | 0 | 172.8 | `timber-job.log` | `527e54dfa00d2703926cabaf5effdbc65f6499d86f61b9e6b1fefdf1c0effe0b` | `98e6ee1a534354c5a07da64301a440cf9eee41f878ab32048c32ef4321669f87` |

（開始／結束時間來自各 `*-result.json` 的 `started`／`ended`，原值是 UTC，上表已加 8 小時。
runid 的時間戳是 `ci_run.py` 開始執行的時刻，比 job 開始早約 15–100 秒（R6 102 秒、R7 67 秒最久），這段是等待安靜、暖機與 clone。）

每個 job 的步驟退出碼【記錄，見各 `*-result.json` 的 `steps`】：

| job | 步驟（退出碼／秒） |
|---|---|
| native | `Build and run non-browser suites` 0／1167.7（內含 `python3 tests/run_all.py --build`；`native-job.log:231` 為 `exit 0：完整非瀏覽器登錄測試…`） |
| assembly | `Build current native executables` 0／47.8；`Run actual browser regression group` 0／239.4 |
| documents | 0／49.8；0／18.8 |
| grid | 0／46.1；0／574.2 |
| canvas | 0／49.1；0／2613.1 |
| space | 0／47.9；0／253.1 |
| timber | 0／49.4；0／123.0 |

「Install Chinese fonts」步驟在六個瀏覽器 job 都是 `skipped-already-installed`（`fonts-noto-cjk 1:20230817+repack1-3` 已裝），`actions/checkout` 以本地 clone 取代，三個 `upload-artifact` 步驟略過。

各輪之間的 job 不重疊：R1→R2 間隔 56 秒、R2→R3 31 秒、R3→R4 24 秒、R4→R5 38 秒、R5→R6 250 秒、R6→R7 200 秒（由上表時間算出）。
也就是說七個 job **都是單獨跑**，沒有兩個 job 同時競爭同一台 WSL VM（【推導】；`receipt.json` 的 `max_parallel: 2` 是 runner 的上限設定，不是實際並行度）。

## 3. 各輪命令與退出碼

| 輪 | 命令 | 呼叫端（`ci_run.py`）退出碼 | 依據 |
|---|---|---|---|
| R7 | `wsl -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_ci.sh 6615db613a75fbad43116d85251782b5083479df timber` | 0（推導） | 命令【記錄】於 `receipts/6615db61/README.md`「How it was run」；退出碼：該輪聚合出 `7/7 green`，依 `runner/ci_run.py` 的 `main()`「全部 job 都在且無 red／undetermined → 0」，故為 0 |
| R1–R6 | 推定同形式：`… wsl_ci.sh 6615db613a75fbad43116d85251782b5083479df <job>`，`<job>` 依序為 `native`、`assembly`、`documents`、`grid`、`canvas`、`space` | 推定 3（`PARTIAL`） | **命令原文與呼叫端退出碼【缺失】**：各輪的 `README.md`、`receipt.json` 被下一輪覆寫，runner stdout 沒有存檔（SP 的 `wsl-ci\` 下有 `pr169.stdout`、`pr179.stdout`、`pr184-run.stdout` 等其他次執行的 stdout，沒有 `6615db61` 的；另在 SP 與本機 `~/.claude/projects` 的工作階段紀錄中以 runid 搜尋，也沒找到）。推定依據：runid 各不相同、每輪輸出目錄只新增一個 job，且 `main()` 在「聚合時尚未湊齊 7 個 job」時 `return 3`，湊齊才 `return 0` |
| 全部 | 每個 job 內部執行的 shell 腳本，逐字記在各 `*-job.log` 的 `##[group]Run …` 區塊（`ulimit -s 16384`、`npm run build`、`start_local.py --port <port>`、`case "$GEOMETRY_BROWSER_SUITE" in …` 等），是從 `6615db6` 自己的 `.github/workflows/integration-tests.yml` 讀出，只有 `/tmp` 路徑與埠號被改寫（`*-result.json` 的 `port_rewrite`、`env`） | 見 §2 表「測試命令退出碼」，全為 0 | 【記錄】 |

執行時使用的 runner 版本：`runner/` 內的 `wsl_ci.sh`（SP 檔案時間 10-09 22:50）、`ci_job.py`（10-10 04:36）、`ci_run.py`（10-10 06:15）、`baseline_sources.txt`（10-10 04:31）
都早於 R1 開始時間（10-10 16:30），且與本 PR `runner/` 內副本位元相同（`cmp`），所以歸檔的 runner 就是這七輪所用的版本（【推導】，依檔案修改時間；修改時間不是密碼學證據）。
`wsl_locked.sh`（排隊鎖）建立於 10-11 01:27，晚於這七輪，這七輪**沒有**經過排隊鎖，本 PR 不收。

## 4. 逐輪互斥紀錄

runner 的規則 3 在每次呼叫開頭等待其他 session 的編譯／測試程序結束（記為 `environment_quiesce`），跑程中每 15 秒取樣（`exclusivity.during_run`），並有暖機紀錄（`warm_up`）與工具版本（`tools`）。
這些都寫在**聚合 `receipt.json` 的頂層，每次呼叫覆寫一次**，所以：

**R7（timber）有完整紀錄【記錄】，來源 `receipts/6615db61/receipt.json`：**

- `environment_quiesce`：`waited_seconds` 5.0、`exclusive_at_start` true、`still_busy_foreign` []、`still_busy_system` []、`foreign_activity_seen` []、`loadavg` 2.61／0.66／0.22、`vm_uptime_seconds` 52。
  （等了一個 5 秒週期；`foreign_activity_seen` 為空，所以被等的不是他人測試，推測是 VM 剛開機的系統雜務，但紀錄本身不足以證明。）
- `exclusivity.during_run`：12 個樣本、`foreign_processes_seen_during_run` {}、`exclusive_during_run` true、`max_loadavg_1min_sampled` 3.76。
- `warm_up`：chrome_1 38.8 秒、chrome_2 1.1 秒、gcc 1.3 秒、node 2.9 秒（皆 rc 0）。
- `tools`：Chrome 153.0.8010.47、Node v24.21.0、npm 11.19.0、Python 3.12.3、gcc 13.3.0、Ubuntu 24.04.5、kernel 6.6.114.1-microsoft-standard-WSL2、12 CPU、7559 MB。

**R1–R6 的逐輪互斥、暖機、VM 運行時間與工具版本紀錄【缺失】**（原因：同 §3，被下一輪的 `receipt.json` 覆寫，且沒有 stdout）。
頂層那份 R7 紀錄**不能**當成前六輪的互斥證據。

能提供的只有以下間接資料，**它們不等於互斥紀錄**：

1. 【記錄】六個瀏覽器 job 與 native 的 `*-result.json` 都有 `leftover_processes_killed: []`（job 結束時沒有殘留的、帶本 job 標記的程序）。這只說明本 job 自己沒漏程序，不說明有沒有別人的程序。
2. 【推導】SP 裡所有 `wsl-ci/*/*/result.json` 的 job 起訖時間：`6615db61` 這七輪的前一個有紀錄的 WSL CI job 是 `798d8387\canvas`（結束於 10-10 16:15:17），後一個是 `5bf5a6d5-p73-timing\canvas`（開始於 18:48:44），
   這兩者之間沒有任何其他有收據的 runner job 與 R1–R7 重疊。SP 的 `q5-probe\`（H2 的 WSL Chrome 探針）檔案時間在 13:06–15:13 與 18:15–18:26，R1–R7 期間（16:30:29–18:08:28）沒有任何檔案落在其中。
   但這只涵蓋「有留檔」的工作，看不到其他 session 以 `wsl` 直接執行而沒留檔的命令。
3. 【記錄】工具版本在前後兩個有紀錄的時間點相同：`798d8387`（結束於 16:15）與 R7（18:08）的 `tools` 完全一致（Chrome 153.0.8010.47／Node v24.21.0／gcc 13.3.0／12 CPU／7559 MB）。R1–R6 夾在中間，但它們自己的 `tools` 沒存。
4. 【記錄】R7 的 `vm_uptime_seconds` 是 52，代表 R7 開跑時 WSL VM 才剛開機；`798d8387` 的最後一輪是 9925 秒。R6 與 R7 之間 VM 重開過；R1–R6 是否共用同一次開機，**【缺失】**。

## 5. 原生二進位身分

- 【記錄】native：`native-job.log:16–28`。`run_all.py --build` 把 `bridge`、`core`、`engjson`、`integrity`、`model-base` 建到 `/tmp/geometry-tests`，
  `[binaries]` 區塊（第 22–28 行）逐一寫「`fresh　來源與 binary SHA-256 相符`」及建置時間（bridge 16:30:51、core 16:31:04、engjson 16:31:05、integrity 16:31:21、model-base 16:31:34，皆 +08:00）。`gdi` 為 `n/a 僅 Windows`。
- 【記錄】六個瀏覽器 job：第 11–17 行 `core／bridge／model-base: built — 建好 /tmp/ga-ci/<runid>/<job>/geometry-runtime/<20 碼 id>/…` 與 `LOCAL_RUNTIME {…}`；`<20 碼 id>` 每個 job 不同（`649b9fffb7f1c5e66950`、`b0a7080b180033f30382`、`9a79aeb7549cd758df3e`、`36620889aed00ed310b8`、`a5c353b54cb342c139b3`、`89a432e73ffa7886acc0`），
  是建置目錄名，不是二進位內容雜湊。
- 【記錄】來源指紋 `290ebaee…`（§1）證明「建出這些二進位的原始碼」相同；編譯器為 gcc 13.3.0（R7 `tools`，R1–R6 見 §4 缺失）。
- **【缺失】二進位檔本身的 sha256**：native 只留下「相符」這個狀態字串，沒有雜湊值；瀏覽器 job 的 `core／bridge／model-base` 在 `/tmp/ga-ci/…` 下，WSL 內的暫存檔沒有歸檔，log 裡沒有印它們的雜湊。

## 6. 測試條件、時限與 partial 的實際範圍

完整說明與表格在 `README.md` 的「測試條件」一節。這裡只放出處：

- 時限：每個 job 的 hard watchdog = 該 job 在 `6615db6` workflow 的 `timeout-minutes` ×3（【記錄】各 `*-job.log` 第 2 行，如 native「ci timeout 15 min (hard watchdog 45 min)」）。
- 超過原 CI 時限的兩個：native 1167.9 秒 > 15 分鐘（900 秒），×1.30；canvas 2662.7 秒 > 35 分鐘（2100 秒），×1.27。其餘五個在原時限內。【記錄】`receipt.json` 的 `over_ci_timeout`、`ci_limit_ratio`；本檔另以秒數自行相除核對。
- assembly（R2）與 grid（R4）的 `CDP_RESULT.scope.mode` 是 `partial`（`assembly-job.log:217`、`grid-job.log:433`），`goldenCompare` 為 `not compared (partial mode)`。
  那是 workflow 自己的設計：`GEOMETRY_ASSEMBLY_ONLY=1`／`GEOMETRY_GRID_SYSTEM_ONLY=1` 只跑 `cdp_test.js` 的一部分段落（逐字見各瀏覽器 job log 的 `case "$GEOMETRY_BROWSER_SUITE" in` 區塊，如 `assembly-job.log:39`；也可對照 `git show 6615db6:.github/workflows/integration-tests.yml`）。
  實際跑的段落：assembly = P77（134 斷言）＋P82（16）= 150；grid = P70（117）＋P71（9）＋P78（23）＋P87（60）＋P88（137）= 346。這些段落在 canvas（R5，`mode: full`）裡有相同的計數。
- timber（R7）也是 `partial`（`GEOMETRY_TIMBER_ONLY=1`，`timber-job.log:140`）：跑 `timber-material`、`timber-source-guards`、`font-layout`，略過 `space-height-library`、`projection-lifecycle`、`projection-placement`、`space-flow`。
  space（R6）是 `full-space-suite`，略過 `timber-material`、`timber-source-guards`（`space-job.log:299`）。

## 7. P73：437ms 計時、診斷版與還原版

### 7.1 437ms 綁到原 log

- 【記錄】`receipts/5bf5a6d5-p73-timing/canvas-job.log` **第 1747 行**：
  `P73_WAIT_MS {"createToBusyClearMs":190,"busyClearToRowMs":437}`，緊接第 1748 行 `P73 選已知邊一半產生引用式，位置與走向用語一致 ✓`。
  該 log 的 sha256 `0257ddc075ee9ff4aa5b5826042373e0dd313ff664838b5fefb38c4dff4f0632`；同一目錄 `canvas-result.json` 為 `07225b76855a39b98c0efd09b350130844fbd19526de36d228b61678a6037017`。
- 該輪結果【記錄】：exit 0、2207 過／0 敗、`completed:true`、`goldenCompare:"matched"`（`canvas-job.log` 的 `CDP_RESULT` 在第 2375 行），耗時 3302.8 秒（原 CI 時限 35 分鐘的 ×1.57），
  `uncaughtBrowserExceptions` 1，即第 578 行 `[EXPECTED EXCEPTION] Error: fb-auto-probe`（`6615db61` 的 `canvas-job.log:578` 同樣有）。
- 兩個數字的意思：`createToBusyClearMs` 是點 `#refGuideCreate` 到 `!oc.busy` 成立；`busyClearToRowMs` 是從那一刻到 `fe.guides` 出現目標 guide 且 `[data-edit-guide]` DOM 列渲染完成。
  `wait()` 以 `sleep(50)` 輪詢（`geometry-web/cdp_test.js` 的 `waitForUI`），上限 30000ms（`geometry-web/uiux_review_test.js:57`），所以 437 是**解析度約 50ms 的上界**，不是事件的精確時戳。
- **樣本數 n=1**（一次計時輪）。`6615db61` 那次 canvas 通過時沒有計時標記，沒有第二個毫秒數。

### 7.2 診斷版與還原版：兩個提交拿不到，改附什麼

- `5bf5a6d5f647ab330a2ec783f30ac25eed96083d`（診斷版：在 `6615db6` 上只加兩個 `Date.now()` 時間戳與一行 `P73_WAIT_MS` 輸出）與
  `c7ed80aa07010cc326a702afff81ef73db4c4ce8`（還原版：在診斷版之上把兩行改回 `798d838` 的 `sleep(180)` 寫法）是 **WSL-only 本地提交，從未 push**。
  【獨立重算】`git -C D:/geometry-axiom cat-file -t 5bf5a6d5f647ab330a2ec783f30ac25eed96083d` 與 `… c7ed80aa07010cc326a702afff81ef73db4c4ce8` 都回 `fatal: git cat-file: could not get object info`；
  這台 Windows 機器的 git 物件庫裡沒有它們。它們只存在於 WSL 內的 `/root/p73-verify/src`（`WSL_CI_REPO`，見 `receipts/5bf5a6d5-p73-timing/receipt.json` 的 `source_repo`）。
  本任務規定不進 WSL，所以**附不了這兩個提交物件，也附不了 `git diff 6615db6 <sha>` 的原件**。
- 改附（由弱到強三層）：
  1. **產生它們的腳本原檔**：`p73-source/make_p73_timing.py`、`p73-source/make_p73_revert.py`（SP `wsl-ci/` 原檔，位元相同）。
  2. **重生 patch**（檔名含 `regenerated`，不是原提交）：用 `p73-source/run_original_script.py` **原封不動**執行上述兩腳本（唯一改動是把 `/root/p73-verify/src` 這個路徑字面值換成 Windows 端的 clone），
     在 `6615db6` 的乾淨 checkout 上依序產生診斷狀態與還原狀態，再 `git diff --full-index`：
     - `p73-source/p73-timing.vs-6615db6.regenerated.patch`（`6615db6` → 診斷狀態，2 增 1 刪；加的行即 `__p73t0`／`__p73t1`／`P73_WAIT_MS`）。
     - `p73-source/p73-revert.vs-6615db6.regenerated.patch`（`6615db6` → 還原狀態）。它與 `git diff --full-index 6615db6 798d838` **位元相同**（已 `cmp`）。
     - `p73-source/p73-revert.vs-timing.regenerated.patch`（診斷狀態 → 還原狀態，即還原版相對診斷版的差異）。
     重生過程產生的本地提交 SHA（診斷 `b99179d1f795ba7b0e540eb609ca4888a9e943aa`、還原 `3b874a826f8833719db3a20dbe5253dfeb505770`）**不等於**原 WSL 提交的 SHA（提交時間不同），沒有任何證明力，只記錄在此以便重現。
  3. **與原提交的內容綁定，不靠 SHA，靠來源指紋**（§1 同一個 `source_version`，涵蓋 `geometry-web/*.js`，所以 `uiux_review_test.js` 的任何位元差異都會改變它）：

| 狀態 | 原 WSL log 記錄的 `version`（第 52 行） | Windows 端重算 |
|---|---|---|
| `6615db6`（真實提交） | `290ebaee…`（`6615db61` 六個瀏覽器 job log） | `290ebaee…` 相符 |
| 診斷狀態（原 `5bf5a6d5`） | `a0ec3871c05a9f84f85085b12935f13f5868435e3a4f1a7dd636bb6983e3b9c0`（`5bf5a6d5-p73-timing/canvas-job.log:52`） | 重生的診斷狀態 `a0ec3871…` 相符 |
| 還原狀態（原 `c7ed80aa`） | `f7ba23a02f82b85f5d66b39e7e1a3ed966ebf793e08fea2b41e7ee3f66d59548`（`c7ed80aa-p73-revert/canvas-job.log:52`） | 重生的還原狀態 `f7ba23a0…` 相符 |
| `798d838`（`6615db6` 的父提交，真實提交） | `f7ba23a0…`（`798d8387-p73-baseline/canvas-job.log:52`） | `798d838` 真實 checkout 重算 `f7ba23a0…` 相符 |

  結論【獨立重算】：(a) 原診斷版的指紋涵蓋範圍內，內容與「`6615db6` ＋ 該腳本的兩處替換」位元相同；
  (b) 原還原版的指紋與 `798d838` 相同，且重生的還原狀態 tree id（`9bbe5b820de957e2219e1e5d30d54274568dfe2b`）等於 `798d838` 的 tree id，所以「還原版」＝把測試檔恢復成 `798d838` 的寫法，沒有別的差異（在指紋範圍內）。
  **限制**：指紋不涵蓋 `tests/`、`.github/` 等；原提交若在這些路徑另有改動，這個比對看不出來。兩支腳本只改 `geometry-web/uiux_review_test.js`，且用 `git commit -am` 提交，沒有證據顯示有其他改動，
  但「原提交物件本身」仍屬【缺失】。
- `p73-source/p73_diag.py`：H1 階段另一支診斷腳本（在 P73 斷言前插入 `DIAG-P73` 輸出，1 秒後再讀一次 `fe.guides`），推定對應 PR #180 正文第 6 節所稱的「複本診斷」（兩者內容吻合，但沒有留下直接連結的紀錄）。
  它**不是** 437ms 那一輪用的程式；其執行輸出（`DIAG-P73` 行）**【缺失】**：SP 內任何檔案都不含 `DIAG-P73`。PR #180 正文引用的「`fe.guides=[1,2,3]`，+1000ms 後 `[1,2,3,4]`」因此沒有原始輸出可核。

### 7.3 其餘 P73 原始 log（對照組）

| 檔案 | 內容 | 重點行 |
|---|---|---|
| `receipts/6615db61/canvas-job.log` | 合併 head，P73 通過 | `:1747 ✓`；`:2374 CDP_RESULT` |
| `receipts/c7ed80aa-p73-revert/canvas-job.log` | 還原 `sleep(180)`，P73 轉紅 | `:1747 ✗ false`、`:1748 FATAL: P73 assertion failed`、`:1750 FATAL_UI`（含殘留的「無法確認載入結果」） |
| `receipts/798d8387-p73-baseline/canvas-job.log` | `6615db6` 的父提交（修前基線），P73 紅 | `:1747 ✗ false`、`:1748 FATAL`、`:1750 FATAL_UI` |

樣本數：通過 2 次（`6615db61`、`5bf5a6d5`）、紅 2 次（`798d8387`、`c7ed80aa`），各自獨立一輪。

## 8. 缺失清單（彙總）

1. R1–R6 各輪的命令原文與 `ci_run.py` 呼叫端退出碼（R1–R6 為推定；R7 命令有記錄、退出碼為推導）。
2. R1–R6 各輪的逐輪互斥紀錄（`environment_quiesce`、`exclusivity`、`warm_up`、VM 運行時間）；現存頂層欄位只屬 R7。
3. R1–R6 各輪自己的 `tools` 版本紀錄（僅有前後兩個時間點相同的間接資料，見 §4 第 3 點）。
4. 各輪 runner stdout。
5. 二進位檔（`core`、`bridge`、`model-base`、native 的 5 個執行檔）本身的 sha256；只有「相符」狀態字串與建置目錄 id。
6. 原 WSL-only 提交 `5bf5a6d5…`、`c7ed80aa…` 的 git 物件（只在 WSL `/root/p73-verify/src`）；以腳本＋重生 patch＋指紋比對替代。
7. `p73_diag.py` 的執行輸出（PR #180 正文所稱 `fe.guides` 的 +1000ms 觀察）。
8. 瀏覽器 job 的三個 `upload-artifact` 步驟（assembly／grid／documents 截圖）的產物：本來就沒有上傳目的地，runner 略過，不是遺漏；PNG 依規定不收。

## 9. 自行核對

```
# 在本目錄：所有原始檔雜湊
sha256sum -c SHA256SUMS

# 來源指紋（需要有 6615db6 的 clone）
git clone --no-checkout <repo> src && cd src
git -c core.autocrlf=false -c core.eol=lf checkout --detach 6615db613a75fbad43116d85251782b5083479df
python -I <本目錄>/p73-source/runtime_fingerprint_posix_order.py .
#  期望 290ebaee1760b3983e98fc4da27bc9154d3a151e2723e24265c4c129aaa2f070
git -c core.autocrlf=false -c core.eol=lf checkout --detach 798d838741d545f029f68dba69679f83d9cebc27
python -I <本目錄>/p73-source/runtime_fingerprint_posix_order.py .
#  期望 f7ba23a02f82b85f5d66b39e7e1a3ed966ebf793e08fea2b41e7ee3f66d59548

# 重生診斷／還原狀態（在 6615db6 的 clone 內；腳本內的 BASE 常數就是 6615db6）
git -c core.autocrlf=false -c core.eol=lf checkout --detach 6615db613a75fbad43116d85251782b5083479df
python -I <本目錄>/p73-source/run_original_script.py <本目錄>/p73-source/make_p73_timing.py <該 clone 的絕對路徑>
python -I <本目錄>/p73-source/runtime_fingerprint_posix_order.py .   # 期望 a0ec3871c05a9f84f85085b12935f13f5868435e3a4f1a7dd636bb6983e3b9c0
python -I <本目錄>/p73-source/run_original_script.py <本目錄>/p73-source/make_p73_revert.py <該 clone 的絕對路徑>
python -I <本目錄>/p73-source/runtime_fingerprint_posix_order.py .   # 期望 f7ba23a02f82b85f5d66b39e7e1a3ed966ebf793e08fea2b41e7ee3f66d59548
```

注意：原腳本會 `git remote remove origin`、`git reset --hard` 並對 clone 做提交，只可在拋棄式 clone 內執行。
