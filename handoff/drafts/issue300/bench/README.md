# issue #300 微基準:角材容量 64 與 512 的載入時間、單條指令時間、堆疊餘裕

> **狀態:只寫、沒跑。** 寫作期間沒有建置、沒有跑核心或 bridge、沒有跑任何 repo 測試、沒有建 worktree、沒有 clone、沒有用 WSL。
> 原始碼一律用 `git show 603e4195:<path>` 讀(603e4195 = GEO-261 整合分支最終版)。
> 唯一做過的驗證是 Windows 端的純文字 / 純 Python 檢查(毫秒到數十秒的小行程,沒有編譯):
> `bash -n bench.sh`、`python gen_scene.py --selftest`、`python drive.py selftest`(對內建的假 bridge)、`python fit.py --selftest`。
> 它們只證明「腳本自己的邏輯」,**不證明核心會接受產生出來的場景**(見第 8 節;`bench.sh` 的 sanity 階段會在正式量測前擋下這件事)。

## 1. 要回答什麼

`DESIGN.md` 提出兩個風險,這組腳本直接量它們:

1. **`contact_order` 線性掃描 => 每條指令約 O(N^3)**(DESIGN §9.1)。草稿預測:n=310 約 50~110 s、n=512 約 7~13 分鐘;原調查報告用 n<=64 的二次式外推得 22~27 s / 53~70 s。本基準量「整份載入」與「單條指令」對 N 的冪次,並估算 F1 客廳(約 110 支)與五房整套(約 300 支)在容量 512 下的載入時間。
2. **堆疊餘裕**(DESIGN §8):512 時 3 份 World 約 16.04 MiB,超過 16 MiB;目前靠「同一條呼叫鏈最多 2 份」撐住。本基準在 `ulimit -S -s` 由 16384 KiB 逐步降低,記錄最小可通過的堆疊。

另外附帶量到:`sizeof(World)`(容量 64 與 512 各一個)、同一個 N 下容量放大的純開銷、各行程峰值 RSS。

## 2. 檔案

| 檔 | 用途 |
|---|---|
| `gen_scene.py` | `gen_scene.py N [--family single\|house]`:產生 N 支角材的場景(純文字)。`--selftest`:與已知良好的 `calib/f3-00.scene` 逐句、逐矩形比對。 |
| `bench.sh` | 外殼:自我搬家到 ext4、用 `git archive` 取 603e4195 原始碼、複製一份套 `patch.diff`(只套產品檔)、各編一支 bridge(`gcc -std=c11 -O2 geometry-web/web_bridge.c -lm`)、呼叫 `drive.py` 與 `fit.py`。 |
| `drive.py` | 量測驅動:對 bridge 送 `loadfile` / `line` 並在用戶端計時;sanity;堆疊階梯;可續跑、有預算、有逾時。`selftest` 用內建假 bridge 驗證自己。 |
| `fit.py` | 讀 TSV,擬合冪次(log-log 斜率與 `a+b*N^k`),估算 N=110 / N=300 / N=512,依判準給結論。`--demo` 印合成資料的範例報告(只看格式)。 |
| `calib/f3-00.scene` | 探針(core-probe)產生、**已被核心整場接受**的 48 支房間,從 `feat/framing-core-probe-20261017` 原樣複製。當作「已知良好」對照與產生器的格式基準。 |

執行時產生(都在 `BENCH_ROOT=/var/tmp/ga-bench300`,ext4):`src64/`、`src512/`、`bin/cap64/bridge`、`bin/cap512/bridge`、`scenes/`、`out/bench.tsv`、`out/fit.md`、`out/env.txt`、`out/build-cap*.log`。結果另複製到 `bench/results/`(Windows 可見)。

## 3. 量了什麼(TSV 的 `kind`)

TSV 欄位:`N  cap  kind  seconds  rc  family  rep  cpu_s  rss_kb  stack_kib  note`。前五欄就是題目要求的「N、容量、指令類型、秒數、rc」。`cap` 是容量(64 或 512)。

| kind | 內容 | 說明 |
|---|---|---|
| `load` | `loadfile <整份場景>` | 整份載入。`serve.py` 的 `BRIDGE_TIMEOUT` 是 30 s,就是這一個 bridge 呼叫。 |
| `line-grid` | `line grid <同一個定義重宣告>` | 只觸發「全量重驗」、不新增角材。最乾淨的「重驗成本」。每行程 3 次。 |
| `line-delete` / `line-timber` / `line-place` | 刪掉最後一支副支 / 重新宣告 / 重新放置 | 互動式「加一支角材」的成本(`line-timber` 只是宣告,應近乎零;`line-place` 才是重驗)。每行程 2 輪,做完世界回到原狀。 |
| `worldbytes` | `section-profile-read` 的 `nativeBytes.world` | `note=world=<bytes>`。預期 4759448(容量 64)與 5605272(容量 512),DESIGN §6 計算值,未量測。 |
| `stack:<工作負載>` | 在 `stack_kib` 的堆疊上限下跑一個工作負載 | `rc=0` 通過;`-11` / `139` 是 SIGSEGV(堆疊爆了);`126` 是 ulimit 設不上去。工作負載:#211 的三個場景(`ax_r13` / `ax_r10` / `ax_r17`)與 `gen64`(N=64 場景 + 重驗 + 一次 `snap`,碰 `reference_snap` 的大框架)。 |
| `sanity-calib` / `sanity-gen` / `sanity-cap65` | 先決驗證 | `rc=0` 符合預期,`rc=3` 不符。 |
| `load-modelbase` | `model-base <場景>` 的整個行程牆鐘 | 只有 `BENCH_MODEL_BASE=1` 才有。 |

**怎麼從 bridge 量單條指令的時間**:bridge 是「stdin 一行指令、stdout 一行 JSON」,`drive.py` 在用戶端記錄「寫出指令」到「讀回那一行 JSON」的牆鐘(`time.perf_counter`)。這包含管線往返與 JSON 序列化(微秒到毫秒級,N 大時可忽略),也包含 `cmd_line` 本身為了 `deletedObjects` 先 `malloc` 並複製整份 World 的成本——這正是互動式使用者實際付的成本。`cpu_s`(`/proc/<pid>/schedstat`)與 `rss_kb`(`VmHWM`)是盡力讀取,讀不到就空白。每個重複用一個**新的 bridge 行程**(含 `loadfile` 之後的第一次操作,冷快取),不是同一行程連跑。

每個 (家族, N, 容量) 一個 unit,預設重複 3 個行程:`load` 3 個樣本、`line-grid` 9 個、`line-delete/-timber/-place` 各 6 個;`fit.py` 對所有成功樣本取中位數。第一次 `load` 超過 `BENCH_REP_CUTOFF`(20 s)就只做 1 次(N 大時一次就要好幾分鐘)。

## 4. 場景

`gen_scene.py` 產生**矩形房間**,句型逐句照探針已被核心接受的 F2~F5 / ex3700 房間:2 支邊界材、m 支主支(`at-line grid u`)、2 支沿牆主支(`at-face e3/e1`)、(m+1) 個 bay x r 排副支(`at-line grid v ... between 左右擋面`)。格線間距沿用 oracle 的 918(u)與 367(v)。`--selftest` 在 f3-00 的參數下逐句重現全部 98 行語句與 48 個 oracle 矩形。

兩個家族:

* `single`:一個房間、一個承載面,N 支都在同一個 placement。P(同面角材數)= M(World 角材數)= N,是**最壞情形**,也是 `contact_order` 假說直接針對的情形。N = 16 / 32 / 64 / 128 / 256 / 512。
* `house`:五個房間、五個承載面,支數比例取探針 golden 各房最大排法 F1:F2:F3:F4:F5 = 111:57:48:28:43(合計 287)。P 只有 N 的一部分,M 仍是 N。N = 128 / 256 / 512(N >= 100)。五房整套(約 300)用內插估。

`python gen_scene.py --table` 印出各 N 的尺寸(第一個房間):

| 家族 | N | 主支 | 排數 | 寬 x 高 (mm) | 每 m^2 |
|---|---|---|---|---|---|
| single | 16 / 32 / 64 | 1 / 3 / 4 | 6 / 7 / 12 | 1848x2534 / 3684x2901 / 4602x4736 | 3.4 / 3.0 / 2.9 |
| single | 128 / 256 / 512 | 6 / 9 / 14 | 17 / 25 / 33 | 6438x6571 / 9192x9507 / 13782x12443 | 3.0 / 2.9 / 3.0 |
| house | 300 (5 房) | 6(F1 房) | 16 | 6438x6204 | 3.0 |

最後一支副支是葉節點(沒有別的角材依賴它),`line-delete / -timber / -place` 就對它做。場景內容只由 N 與家族決定(確定性),`note` 裡有 `sha=` 前 8 碼可核對。

## 5. 執行步驟

### 5.1 先決條件
WSL(Ubuntu-24.04)需有 `gcc`、`python3`(3.8+)、`git`、`tar`、`flock`、`setpriv`(util-linux)。不需要網路。`/mnt/d/geometry-axiom` 必須有 `603e4195`(或 `~/ga-ci/mirrors/*.git` 有)。

### 5.2 (選用、很輕)自測
```
wsl -d Ubuntu-24.04 -- bash /mnt/d/geometry-axiom-work/drafts/issue300/bench/bench.sh selftest
```
三個純 Python 自測,約 20 秒,不編譯。

### 5.3 正式量測(經 WSL 的鎖)
```
wsl -d Ubuntu-24.04 -- env WSL_CI_LABEL=issue300-bench bash <scratchpad>/wsl-ci/wsl_locked3.sh run \
    'bash /mnt/d/geometry-axiom-work/drafts/issue300/bench/bench.sh all'
```
`bench.sh` 啟動時先把自己和 `drive.py` 等複製到 `/var/tmp/ga-bench300/run-<時間>/` 再 exec 副本,所以執行中改動 D 槽上的原檔是安全的。

`all` 依序做:build -> worldbytes -> sanity -> stack -> run -> fit -> 複製結果。**每次佔用有上限**:軟預算 `BENCH_BUDGET_SEC=1500`(含建置),預測做不完的 unit 會延後;硬期限 = 軟預算 + `BENCH_HARD_EXTRA_SEC=240`(正在跑的指令會被殺掉並記 rc=125,下次重做)。合計 <= 29 分鐘,在 30 分鐘內。

結束碼:`0` 全部完成;`10` 預算用完、還有 unit 沒做(**用同一個指令再跑一次就會接著做**,TSV 是追加的,做完的 unit 不會重做);`3` sanity 失敗(不要信任何量測);`2` 建置失敗;`66` 找不到 SHA 或 patch;`75` 鎖被占用;`70` 環境錯誤。

### 5.4 建議的時段安排
(以下時間都是**估計、未量測**)

| 時段 | 指令 | 預期 |
|---|---|---|
| 1 | 預設 `all` | 建置(兩份 400 KB 單一翻譯單元,平行編)數分鐘;sanity < 1 分鐘;stack 數分鐘;其餘預算給 run,通常做完 N <= 128 兩種容量,可能到 256。 |
| 2.. | 同一個指令重複,直到結束碼 0 | 每次接著做延後的 unit。 |
| 專用大 N | `BENCH_NS=512 BENCH_HOUSE_NS=512 BENCH_CAPS=512 BENCH_REPS=1 BENCH_FORCE=1 BENCH_RUN_TIMEOUT=1500 bash .../bench.sh run` | single N=512 的 `load` 依草稿預測可能要 7~13 分鐘。`BENCH_FORCE=1` 是必要的:否則預測值超過剩餘預算就會一直被延後。單一指令不能跨鎖時段:若它在硬期限(約 29 分鐘減建置/堆疊的時間)內做不完,會記 rc=125 並在下次從頭重做;這種情況只能放寬 `BENCH_BUDGET_SEC` / `BENCH_HARD_EXTRA_SEC` 並由主迴圈決定鎖多久。`BENCH_RUN_TIMEOUT` 先到則記 rc=124(代表 > 該秒數),這本身就是一種結果;之後調高逾時要重做,加 `BENCH_RETRY_TIMEOUTS=1`。 |

查進度:`bash bench.sh status`。結果在 `/var/tmp/ga-bench300/out/` 與 `bench/results/`(含 `STATUS`:`DONE` 或 `PARTIAL`)。收尾後 `rm -rf /var/tmp/ga-bench300` 可回收空間(約數百 MB)。若被 TaskStop 中斷,bridge 由 `setpriv --pdeathsig KILL` 跟著死;仍可用 `pgrep -af ga-bench300` 確認沒有殘留。

### 5.5 只重跑分析
```
python3 fit.py /mnt/d/geometry-axiom-work/drafts/issue300/bench/results/bench.tsv --min-n 64 --f1-n 110 --house-n 300 --load-limit 30 --stack-margin-mib 2
```

## 6. 預期輸出(格式示意與預期量級)

`bench.tsv` 開頭(**數字是示意,不是量測**):
```
N    cap  kind        seconds   rc  family  rep  cpu_s     rss_kb  stack_kib  note
0    64   worldbytes  0.000000  0                                              world=4759448
0    512  worldbytes  0.000000  0                                              world=5605272
128  512  load        (秒)      0   single  1    (秒)      (KB)               sha=xxxxxxxx
128  512  line-place  (秒)      0   single  1    (秒)      (KB)
64   512  stack:gen64 0.4       0   stack   0                      11264      out=xxxxxxxxxx
64   512  stack:gen64 0.2       -11 stack   0                      10240      no reply to: loadfile
```
`fit.py` 的報告分七節:涵蓋範圍、冪次、立方假說、容量 64 對 512 同 N 的比值、估算、堆疊、判準與結論。

預期量級(**預期,不是結果**):

* `worldbytes`:4759448 / 5605272(差 845824 = 448 x 1888)。不是這兩個數字 => DESIGN §6 全部重算。
* 同 N 下容量 512 / 容量 64:約 1.1~1.3x(DESIGN §7:S 相關部分 +17.77%)。明顯大於 1.3 => 容量放大本身有額外成本(例如 `AppContactFacts` 的 memset)。
* 若 DESIGN §9.1 成立:`line-*` 的最後三點斜率約 2.8~3.2,`load` 約 3.8~4.2(`load` 斜率 - 1 = 等效每指令斜率)。斜率會隨 N 增加而爬升(固定成本被稀釋),所以只信 N >= 128 的區段;若最大 N < 256,不能據此否定立方。
* 堆疊:最小通過約 `2S` 加數百 KiB,約 10.7~11 MiB(餘裕約 5 MiB)。若貼近 `3S` = 16.04 MiB => 有 3 份 World 的呼叫鏈。

## 7. 如何判讀「512 可行與否」

兩個**建議判準**(**由主迴圈定案**;`fit.py` 的 `--load-limit` / `--stack-margin-mib` 可改):

1. **五房整套(N 約 300)載入 <= 30 s**。依據:`serve.py` 的 `BRIDGE_TIMEOUT = 30 s`,整份載入是單一 bridge 呼叫。優先用 `house` 家族的內插值;只有 `single` 曲線時,它是上界(`single` 通過 => `house` 必通過;`single` 沒過 => 判定「未定」,要補 `house` 資料)。
2. **16 MiB 堆疊下至少 2 MiB 餘裕**:`16384 KiB - 所有工作負載都通過的最小堆疊 >= 2048 KiB`。

| 觀察 | 意義 | 建議動作 |
|---|---|---|
| `sanity` 失敗,且 `sanity-calib` 通過、`sanity-gen` 失敗 | 產生器的句型被核心拒絕 | 看 `note` 的錯誤字串,修 `gen_scene.py`;**不要量**。 |
| `sanity-calib` 也失敗 | 建置或環境問題 | 看 `build-cap*.log`。 |
| `sanity-cap65` 不符 | 兩支 bridge 的容量不是 64 / 512(patch 沒套上或舊執行檔) | 刪 `bin/` 重建。 |
| `line-*` 斜率接近 3,且判準 1 FAIL | `contact_order` 立方成立且超標 | 512 先不上。先另開單把 `contact_order` 改成預建 `id->order` 表(DESIGN §9.1),再重量。 |
| 斜率接近 3,判準 1 PASS | 立方存在但目前規模可接受 | 512 可行;把單房 N=512 的值記成上限警示。 |
| 斜率約 2 | 立方假說不成立,DESIGN §9.1 高估 | 重驗的 O(M^2) 項(`reference_check_all` 內層迴圈)才是主要成本;`line-grid` 與 `line-place` 比值可看出是否主要在重驗。 |
| `house` 明顯比 `single` 便宜 | 成本主要由 P(同面角材數)決定 | 估五房整套用 `house` 值,不要用 `single`。 |
| 判準 2 FAIL(最小通過堆疊 >= 14.4 MiB) | 存在 3 份 World 的鏈(DESIGN §8 的盲點) | 512 先不上;處置方向是縮小 World 或把按值 World 改成 `malloc`,不是調高 ulimit。 |
| 兩項都 PASS | 依建議判準 512 可行 | 仍要記得:堆疊階梯只涵蓋 4 個工作負載。 |
| `rc=124`(逾時)或 `PARTIAL` | 該 N 太慢或預算不足 | 逾時本身就是證據(> `BENCH_RUN_TIMEOUT` 秒);要量更大的 N 另排專用時段。 |

## 8. 限制與我最不確定的地方

1. **場景是否被核心接受,寫作時完全沒驗證**。`gen_scene.py` 的句型與幾何模型已和 f3-00 逐句、逐矩形對齊,但「很多支」「很大房間」「五個承載面在同一個 World」都是核心沒被餵過的規模/組合。這就是 `sanity` 階段存在的原因;被拒絕時 `note` 會帶核心的錯誤字串。
2. **代表性**:真實 F 房間的密度是 3.8~5.3 支/m^2(F1:95~111 支 / 20.76 m^2),產生器約 3.0 支/m^2(真實房間多了孔邊垂直料、縫上料等)。但成本主要隨支數(P、M)與擋面重疊對數變,不隨 mm 密度變,我判斷影響小——**這是判斷,不是量到的**。`single` N=512 是一個 13.8 m x 12.4 m 的房間,現實不存在,它只是最壞情形的標尺。
3. **`line-grid` 是否被核心接受未驗證**(同一個 grid 定義重宣告)。若被拒(`rc=1`),`fit.py` 會略過,仍有 `line-place` 可用。
4. **單條指令的時間是用戶端牆鐘**,含管線與 JSON;在毫秒以下的小 N 會有數十微秒的底噪,所以斜率只看大 N 的區段。沒有做 CPU 釘選(可用 `BENCH_CPU`)。鎖已確保沒有別的重行程,但 WSL2 本身的排程抖動無法排除;`env.txt` 記錄了開始時的 `uptime` 與前三名 CPU 行程。
5. **只量了 bridge 路徑**(`loadfile` 與 `line`)。CLI 的 `--scene` 與 `model-base`(`BENCH_MODEL_BASE=1` 才量)是另一條路徑,差別在 `model-base` 開候選池、CLI 另外要出 SVG。
6. **堆疊階梯**只涵蓋 #211 的三個場景與一個 N=64 場景(含 `snap`),和 N 無關(框架大小由容量決定)。DESIGN §8 提到的「函式指標派發的呼叫鏈」若不在這四個負載上,階梯看不到。`ulimit -S -s` 只限制軟上限,與 CI 的 `ulimit -s 16384` 在這一點等價。
7. **`patch.diff` 是對 09ab5f79 寫的**,我用 `git diff --numstat 09ab5f79 603e4195 -- <patch 動到的 15 個檔>` 確認這 15 個檔在兩個提交之間逐位元相同(輸出為空),所以應該能直接套;`bench.sh` 會先 `git apply --check`,失敗就停在建置階段。patch 只套產品檔,不套 `tests/` 與 `ARCHITECTURE.md`。
8. **預算預測**:`drive.py` 用「同家族同容量上一個 N 的 `load` 時間 x (N/N')^4 x 1.15」預測下一個 unit 要多久(指數 4 是 `load` 的最壞預期,可用 `--pred-exp` 改)。預測偏低時會被硬期限擋下並記 rc=125,下次重做;預測偏高時會多延後一次。
9. 建置時間、整個 `all` 的時間都沒有量過,第 5.4 節的估計只是估計。
