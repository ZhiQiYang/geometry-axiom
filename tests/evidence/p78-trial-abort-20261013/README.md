# #209：P78 有界時間線診斷

本交付定位到**受控 timeout 後的恢復缺口**，沒有證明 6855f9b1 歷史首紅的唯一根因，也沒有修改產品行為。

同一雲端產品來源，未改 P78 的完整局部基線 23/0；renderer CPU 20 倍節流下，首個 ready 仍通過。加上一次明示的 18 秒 bridge 鎖內等待後，原 15 秒 AbortSignal timeout 使 trial 與 connection 轉為 error，原 20 秒 ready 等候失敗；移除注入後，同 CPU20 前綴再次通過。

當前工作區仍是 modal dialog，真實 `#connectionRetry` 中心點無法命中按鈕。診斷直接呼叫既有 `recoverConnection()` 能使 connection 回 ready，但同一 trial 仍 error；再以真實控制項將寬度改為 2401，新候選才 ready。這個直接函式呼叫**不是使用者已成功操作重試的證明**。原生查詢稍後仍回 `ok:true, exact:true`，server 因 client 已離線而 BrokenPipe；fetch abort 沒有取消已持有鎖的 server／bridge 工作。

## 授權、owner、来源

- [Claude 指派](https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6130640423)、[領取回執](https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6130753641)。owner 是本雲端 Codex，只有 `test/p78-trial-abort-timeline-20261013` 這一線。
- 領取前讀看板 `ops/agent-board@05383d5c2594c3e7ef24d4ef27a2af17fe9584ef` 的 `BOARD-cloud-codex.md`、AGENTS、產品願景、D29／I8／I8a、#209 及 #188 最新相關留言。指定分支當時不存在；checkout 沒有 `.agents/skills`，feedback 清單無未處理項目。
- base main `1bf661028d55b3ebbd48a02f010116ac9185b81f`；六次測時 git HEAD 都是佔位 `ab0f95bfcd43075b45414de7eb2fbfa52ff31240`，診斷工具當時未提交，精確 bytes／雜湊分別保存在 raw 包的 `p78-tools-v1/`、`p78-tools-v2/` 及每輪 sources-before／after。不可把後來的提交 SHA 回填為測時 HEAD。
- `historical-source-comparison.json` 比較 51 個路徑（gcc `-MM` 的實際 C include 閉包及九個相關 JS／Python 路徑），逐 bytes 與 #188 head `6855f9b11478e7fad30ab3c0f268ffc985b5dda1` 相同。這不表示兩者整棵 repository、先前 P1–P77 狀態或環境相同。
- 只新增 `tests/diagnostics/p78_*`、本證據目錄。產品、公理、舊鎖行、原測試、golden、設定、安全政策未改；沒有 WSL／全量 runner、合併、force push 或刪分支。

## 原始命令與實際結果

cwd 為 `/workspace/geometry-axiom`。每輪的 `identity.json` 保留 wrapper argv、server argv、URL／PID、runtime 身分；`commands.json` 保留各子命令、exit、elapsed。下列 exit 是实际 wrapper／browser 結束碼，不是啟動或 inProgress。

| 輪次（raw 包目錄） | 額外參數 | browser 秒數 | exit | 實際範圍／結果 |
|---|---|---:|---:|---|
| p78-baseline-01 | 預設 CPU1、hold0、full | 21.381 | 0 | **獨立 P78 23/0**、0 JS exceptions |
| p78-cpu20-01 | CPU20、prefix | 6.837 | 0 | 1 原斷言＋首個原 ready 等候；非完整 P78 |
| p78-held18-cpu20-01 | CPU20、hold18、prefix | 36.664 | 1 | 首個原 ready 逾時；保留 v1 診斷自身的後續 sentinel 錯誤 |
| p78-restored-cpu20-01 | CPU20、prefix | 7.857 | 0 | 移除 hold 的前綴對照 |
| p78-held18-cpu20-02 | CPU20、hold18、prefix | 37.280 | 1 | 相同 ready 紅；v2 收齊恢復及新候選，無 harness error |
| p78-restored-cpu20-02 | CPU20、prefix | 7.140 | 0 | v2 移除 hold，前綴回綠 |

```sh
python3 tests/diagnostics/p78_run.py --out /tmp/p78-baseline-01
python3 tests/diagnostics/p78_run.py --out /tmp/p78-cpu20-01 --bridge /tmp/p78-baseline-01/bridge --cpu-rate 20 --mode prefix
python3 tests/diagnostics/p78_run.py --out /tmp/p78-held18-cpu20-01 --bridge /tmp/p78-baseline-01/bridge --cpu-rate 20 --hold 18 --mode prefix
python3 tests/diagnostics/p78_run.py --out /tmp/p78-restored-cpu20-01 --bridge /tmp/p78-baseline-01/bridge --cpu-rate 20 --mode prefix
python3 tests/diagnostics/p78_run.py --out /tmp/p78-held18-cpu20-02 --bridge /tmp/p78-baseline-01/bridge --cpu-rate 20 --hold 18 --mode prefix
python3 tests/diagnostics/p78_run.py --out /tmp/p78-restored-cpu20-02 --bridge /tmp/p78-baseline-01/bridge --cpu-rate 20 --mode prefix
```

v1 的 prefix 完成 sentinel 錯套到「原測試失敗後的新候選 ready」診斷，故第一個紅輪在補證末段多一筆 harness.error；原 P78 timeout 已先發生且 exit1 保留。v2 僅限 sentinel 在原 P78 呼叫內生效，另保存 trial 原生回應全文及錯誤截圖。只為修正此蒐證缺口追加紅／移除注入對照；所有舊輪均保留。

這是**故障注入及移除注入的反證**，不是產品「修前紅／修後綠／撤修再紅」。產品沒有修正，不能冒領那三項驗收。每輪原 API 15000ms、P78 20000ms、server bridge timeout 30s 均不變。工具另有單次 browser 外層 300s 上限，不代替或放寬原等待。

## v2 紅輪：request p78-20、instance 1／候選 seq 2

詳見 `summary.json`，原件在 `p78-held18-cpu20-02/browser.jsonl`／`server.jsonl`。各列 elapsed 只在同一時鐘內計算：browser 用 performance.now，server 用 monotonic_ns；epoch 僅供粗略交叉定位，沒有把不同 monotonic 原點直接相減。

| 階段 | 觀測 |
|---|---|
| 候選建立→fetch | 283.3ms（含原 180ms debounce 與 renderer 排程） |
| HTTP handler→bridge queue | 28.716ms |
| bridge lock 等候 | 0.012ms；本輪不是觀測到既有長排隊 |
| 明示注入 | lock 已取得、stdin.write 前 hold 18000.206ms |
| 原 AbortSignal | fetch 起 15028.9ms，reason `TimeoutError: signal timed out` |
| fetch reject | 15103.8ms；`apiRequest` → `connectionFailed`，app.js:684／565 |
| trial 處理 | grid-trial.js:57 接收 `ok:false`；seq=serial=2，pending 清除、trial=error |
| bridge 真實 I/O | 注入結束後 stdin.flush→stdout 收到 35.954ms；含 IPC／OS 排程，**不是 C 內部純運算時間** |
| server 結束 | HTTP handler 起 18067.895ms；原生回成功 JSON，但 client 已斷線 |
| 原 ready 等候 | 20000ms 上限失敗，未延長，首紅保留 |
| 有界觀察 | 等候失敗後再觀察 3 秒，仍 error，無新 trial request |
| 真實重試按鈕 | visible size、disabled=false，但 hit=false（目前 modal 阻隔） |
| 直接呼叫恢復（診斷） | connection ready；同候選 trial 仍 error／ghosts=0 |
| 真實改寬 2401 | 新候選 seq4／p78-24，headers 278.6ms，trial ready／ghosts=5 |

移除 hold 的 v2 對照：p78-20／seq2，headers 94.5ms，bridge I/O 2.670ms，無 fetch rejection、ready 通過。**CPU20 只節流 Chromium renderer**，沒有宣稱節流 server／native 或模擬 WSL 全機 CPU／IO 壓力。

`fetch.signal.abort` 本身不代表請求失敗：成功 fetch 的 signal 之後仍可能自然到期。摘要以 `fetch.reject` 判斷拒絕，並保留 CDP request／loadingFailed 及完整時間線，沒有把所有 signal 事件計為 abort 失敗。request ID 是觀測用 `X-P78-Request-ID` header，沒有把唯讀 trial 改為帶產品 mutation receipt 的請求。

## 對 #209 第 1 題的回答與最小提案

原碼的 timeout 是 15 秒。當前候選收到 transport 失敗時會回報錯誤並轉 `trialState=error`，不是本輪觀測到永遠 pending。它不自動重試：render 的 key 未改，`newKey!==key` 不成立；connection 恢復本身也沒有清除 trial 的 error／key。這是原碼路徑分析，加上上述有界觀察；不把幾秒觀察誇張成無限時間實驗。

最小待授權產品提案：重用既有重新連線操作，讓它在當前 modal 可觸達；連線恢復後，只對仍屬當前 context／候選且因 transport 失敗的**唯讀**試擺使快取失效並重新查詢。保留候選代次 fencing、World 不變、15s／20s 期限；不得順帶重播任何有副作用的 API。後續需另證真實使用者路徑、舊候選晚回不覆寫、新 context 不重試，以及產品修前／修後／撤修反證。本 PR 只交證據及提案。

## 歷史界線與最小補證

歷史 [6127063994](https://github.com/ZhiQiYang/geometry-axiom/pull/188#issuecomment-6127063994) 是兩筆 grid-trial-query 在 19608／19328ms 後 `The user aborted a request.`、connection error，canvas1573.5s 中止、1317 個前置斷言、FULL 未完成、golden 未比；首輪 wrapper1。[6128918479](https://github.com/ZhiQiYang/geometry-axiom/pull/188#issuecomment-6128918479) 只證同 head 後續單 canvas2207/0。兩份原始收據沒有重寫。本次讀取核對相關留言，**未再下載重核歷史 256 份原件**。

本輪是**一筆 TimeoutError**，原歷史是兩筆 AbortError 文案；未知包含：舊 Chrome 版本／abort reason、事件迴圈延遲、當時候選是否被取代、browser／server／bridge 排隊，以及 P1–P77 的前置狀態。不能用本輪 hold18 或單 canvas 綠反推歷史環境慢、唯一產品根因或 #188 合併門檻。

可執行最小補證（**只交原 WSL owner 在可用且已授權的獨占時段執行，本雲端未啟動 WSL**）：

1. 在原擁有的 `6855f9b11478e7fad30ab3c0f268ffc985b5dda1` checkout，先確認工作樹及既有服務歸屬；使用本 PR 的工具，指定原 checkout 根目錄，不切換／改寫別人的分支。
2. Node 必須能 `require('playwright')`，並有 Python3、gcc 和該 WSL 的實際 Chrome；工具不安裝依賴或改設定。選一個不存在的 TEMP 目錄，跑**無 hold、CPU1 的單次前綴**：

```sh
P78_SOURCE_ROOT=/absolute/path/to/owned/6855f9b1-checkout GEOMETRY_CHROME=/usr/bin/google-chrome python3 /absolute/path/to/this-pr/tests/diagnostics/p78_run.py --out /tmp/p78-wsl-natural-209 --mode prefix
python3 /absolute/path/to/this-pr/tests/diagnostics/p78_summarize.py /tmp/p78-wsl-natural-209 > /tmp/p78-wsl-natural-209-summary.json
```

3. 回傳完整輸出目錄、實際 shell exit、原 Chrome 可執行檔雜湊／版本及歷史 job.log／receipt。這個最小單測仍不保留 P1–P77，通過只能排除該次單測，不能補造歷史時間線。若必須收完整上下文，需原正式 runner owner 在其下一次已授權 canvas 輪接入同樣觀測；本工具沒有宣稱已接入全量 runner，也不以本 PR 再排一次全量。

## 環境、原件與核驗

- Linux 雲端；Chromium154.0.8037.57、Node24.19.0、Python3.12.14、gcc14.2.0。Browser plugin 不可用，使用已安裝 Playwright 啟動自有 Chromium，再以專案 CDP helpers／原 P78 真實點擊；没有依賴安裝。
- 編譯命令 `gcc -std=c11 -O2 geometry-web/web_bridge.c -o /tmp/p78-baseline-01/bridge -lm`，exit0。六輪沿用這支實際 ELF，前後 SHA256 `133f374ea6575febe2c474053b2507d280eed07cc4fe6e83bf14387870779924`，原始 binary 在包內。v2 identity 另存 Python、Node、gcc、Chromium launcher 與 ELF 的 hash。
- 每輪獨立 server／browser；runtime fresh、PID／root 核對；server 結束 exit0，bridge.close 的實際 exit 記在 server.jsonl。所有來源、binary 前後相同。結束時沒有存活的測試 node／server／bridge／Chromium；容器 PID1 尚未回收的 Chromium zombie 另存 `processes-after.txt`，不冒稱全程序表空白。
- 首輪桌面1400×1000＋P78 原390×844檢查過；故障與節流只驗桌面。頁面 title／URL、非空內容、實際操作、console／pageerror 原件都在包內；未見框架 overlay，0 JS exceptions。預期 timeout／connection error 與明示非法 stagger 的 native stderr 原文保留。沒有聲稱整個 app 或 full canvas 綠，所有輪 `goldenCompared=false`。
- `raw.tar.xz`：989520 bytes，SHA256 `1bc1eb1eecb3442cd94959f49d8f9e3316b1f7d3e95f83636596bc50c9db84ef`。124 個成員已逐 bytes／SHA 核過；`manifest.json` 是可獨立驗算的清單，`verification.json` 是本輪結果。包括全命令／退出碼／runtime、server／browser JSONL、實際注入後 served JS、sources 前後、bridge binary、截圖及兩版工具。`summary.json` 是衍生摘要，不取代原件。

可重算摘要：解包到新的 TEMP 目錄後，將六個輪次目錄傳給 `tests/diagnostics/p78_summarize.py`；程式只讀取 raw，不啟動應用。任何新跑都須使用不存在的 `--out`，工具會拒絕覆寫舊輪。
