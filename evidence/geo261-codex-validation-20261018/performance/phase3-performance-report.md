# GEO-261 第三階段：正式效能基準與 gprof

同機、同 `-O2`、同場景與指令的比較確認整合版在建立／修改路徑有顯著退化：cold **22.05 倍**、load_scene **26.94 倍**、model legacy **16.06 倍**。常駐每輪九段量測時間合計的中位數為 **52.997 → 1,286.739 ms（24.28 倍）**；兩個 dump 讀取階段沒有一致退化。

四份 integration profile 中，`geo_sha_block` 占 **99.28–99.66% 的可見 CPU 取樣**。這確認 SHA 壓縮運算是主要可見 CPU 熱點；與固定來源的 H 全 World、K bound-state eager SHA 路徑吻合，支持優先驗證減少重複 SHA 的修正。**這不是 H／K／provider metadata 的精確成本分攤，也不是修正已成功的證據。** 本報告只記 baseline，沒有修後或撤回量測。

## 身分、環境與執行

| 項目 | 實際內容 |
| --- | --- |
| main | `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425` |
| integration | `e64aa6359d600f43313ec9d7ba1112c465b6a40c` |
| 共用 scene SHA-256 | `c3c0ba589285ef5ecd835b89a38174ebe050c85c4b8814510e139f72550f1f7c` |
| 執行工具 SHA-256 | `46b806df559fc54fe8d00ebab2a342f4eef5506dc8c241e74306e32b3f1dff7b` |
| normal | 2026-10-18 12:08:50–12:09:33 UTC；exit 0；outer 42.847 s |
| gprof | 2026-10-18 12:10:33–12:11:25 UTC；exit 0；outer 51.709 s |
| OS／kernel | Debian GNU/Linux 13.6（trixie）；Linux 6.18.55 x86_64 |
| 工具版本 | GCC 14.2.0；Python 3.12.14；Node 24.19.0；Google Chrome 155.0.8059.84 |
| 資源 | 5 logical CPUs；stack 16 MiB |
| 編譯 | 兩版 `-std=c11 -O2`；gprof 另加 `-g -pg -fno-omit-frame-pointer` |

兩份來源用獨立 archive 與 build output，沒有混入後來修正。[inputs manifest](artifacts/inputs/manifest.json) 保存完整共同指令；[工具](measure_geo261.py)、[normal invocation](normal-invocation.json)、[profile invocation](profile-invocation.json) 保存實際命令與身分。run 目錄使用 UTC+8，不是另一輪執行。Node／Chrome／OS 版本引自同機 [第二階段環境收據](../browser-e64aa635/environment.json)，本輪為非瀏覽器量測。

六個 browser 已於 12:03:50 UTC 完成，root 確認本輪沒有其他測試或建置。normal 開始 loadavg 0.062／0.517／0.858，profile 0.203／0.478／0.809；這是開始快照，並非全程負載監控。

八份 build manifest 記錄實際 compiler dependency 閉包：main bridge／model 各 **2 個 `.c`**，integration 各 **56 個 `.c`**。它們由同一 unity TU 編入，gprof 均 `pg=true`，沒有漏掉額外被 include 的原生來源；libc／libm 未插樁。編譯命令、binary SHA、dependency、source manifests 與 link maps 均在公開清單。

## 成功完整性

每個 run 都有 **305 筆量測樣本、288 個成功 bridge 回應、21 個成功 model payload**，`summary.complete=true`，沒有 `failure.json`。分析時再讀原始 JSON 核對所有 `ok`、preview 的 `preview.valid`、dump text、model 未放置角材為空；量測工具另驗 schema、EOF、exit 0 及無額外 stdout。resident 的 stderr 是 I8a preview 敘述，原文保留，沒有把 stderr 非空直接當失敗。這些成功門檻不取代完整幾何驗收。

## Normal：相同工作負載耗時

| 工作負載／phase | n（各版本） | main median / p95（ms） | integration median / p95（ms） | 中位數倍率 |
| --- | ---: | ---: | ---: | ---: |
| `cold_start_dump` | 7 | 49.506 / 60.793 | 1091.693 / 1217.233 | 22.05× |
| `reset` | 15 | 0.754 / 1.973 | 80.578 / 94.560 | 106.82× |
| `load_scene` | 15 | 30.848 / 59.025 | 831.183 / 955.596 | 26.94× |
| `read_dump` | 15 | 1.863 / 5.230 | 0.608 / 1.253 | 0.33× |
| `canvas_position` | 15 | 3.174 / 5.827 | 81.933 / 100.676 | 25.81× |
| `unused_spec_create` | 15 | 5.736 / 11.268 | 86.643 / 106.607 | 15.11× |
| `unused_spec_replace` | 15 | 4.178 / 8.488 | 81.761 / 95.007 | 19.57× |
| `preview_spec` | 15 | 4.296 / 6.153 | 81.040 / 98.209 | 18.86× |
| `cancel_preview` | 15 | 0.432 / 0.741 | 38.826 / 51.753 | 89.88× |
| `read_final_dump` | 15 | 0.560 / 1.268 | 0.733 / 1.361 | 1.31× |
| `model-legacy` | 7 | 54.709 / 63.319 | 878.460 / 977.433 | 16.06× |
| `model-neutral` | 7 | 未量測 | 899.644 / 1110.398 | 不比較 |

完整 [摘要](artifacts/runs/20261018T200850689427-normal/summary.json)、[逐樣本](artifacts/runs/20261018T200850689427-normal/samples.json)、[環境](artifacts/runs/20261018T200850689427-normal/environment.json) 保留 min／max／sum 與所有原值。倍率只用 normal 中位數相除，沒有使用 `-pg` 時間。

- cold 每版 7 次，是 spawn 前到第一個 dump 回應，包含初始化、IPC、輸出；不是清除 OS cache，也不是純初始化 CPU 時間。
- resident 每版 15 輪，九段各自計時至完整回應行，含 IPC／序列化，Python 解碼驗證在停表後。前置啟動 dump 與 `section-profile-read` 已排除。每輪先相加再取中位數為 **52.997104／1,286.739146 ms，24.279424 倍**，不是九個中位數相加，也不是整輪 wall time。
- reset 的 106.82 倍來自 0.754 → 80.578 ms，絕對增加約 **79.824 ms**；不能冒稱整套 suite 倍率。使用者提供 bridge_integrity 60／612 秒是背景，不是本工具重新量出的結果。
- model 每模式 7 次，計完整 native 程序 spawn 到退出，不含 Python facade 的解碼、provider 綁定或後續運算。integration neutral **899.644 ms**，legacy **878.460 ms**，相差 **21.184 ms**；這是兩組獨立程序中位數差，**不是純來源圖時間**。legacy stdout 每次 2,815 bytes，neutral 每次 55,216 bytes；額外建圖、序列化、輸出均可能貢獻差額。
- integration legacy 本身已慢 16.06 倍，不能把所有退化歸給 neutral 或 #289。main neutral 未量測，不拿不同功能相除。
- native 回報 World：main **4,114,656 bytes**，integration **4,759,192 bytes**，增加 **644,536 bytes（15.66%）**。這是完整快照的真實資料大小，不能把大小增幅直接換成退化倍率。
- n=7／15 的 nearest-rank p95 都是本次 max，不能當穩健尾延遲或信賴區間。工具先 main 後 integration，未交錯隨機化；讀取的亞毫秒級差異易受排程影響，不宣稱普遍讀取加速或退化。

## gprof：SHA block 是主要可見 CPU 熱點

| 版本／workload | gmon 程序數 | flat 最末累積 s | SHA block self s | 原始 % time | block／SHA calls（原符號） |
| --- | ---: | ---: | ---: | ---: | ---: |
| main／bridge-cold | 7 | 0.00 | — | 無時間樣本 | 63 / 7 |
| main／bridge-resident | 1 | 0.00 | — | 無時間樣本 | 534 / 106 |
| main／model-legacy | 7 | 0.00 | — | 無時間樣本 | 未列出 |
| integration／bridge-cold | 7 | 4.16 | 4.15 | 99.64% | 15,304,751 / 1,827 |
| integration／bridge-resident | 1 | 14.55 | 14.50 | 99.66% | 53,019,413 / 6,306 |
| integration／model-legacy | 7 | 4.35 | 4.32 | 99.31% | 15,304,688 / 1,820 |
| integration／model-neutral | 7 | 4.14 | 4.11 | 99.28% | 15,304,814 / 1,841 |

flat 最末 cumulative 與 self 保留原顯示精度，`% time` 直接引用原文；四捨五入的 self 相加可能不等於顯示總數（例如 cold），不從四捨五入值反推百分比。main 使用 `eng_sha_block`／`eng_sha256`；main legacy 未列 SHA。三份 main 都是 **`no time accumulated`**，不代表零 CPU 或函式未執行；全零 self／inclusive 的名稱排序不能當實際熱點排名。

integration resident 的 `geo_sha_block` 為 **14.50 s、53,019,413 次原始符號呼叫**，`geo_sha256` 為 **6,306 次**。其他可見 self 僅 `geo_sha256` 0.02 s，`app_candidate_bind_core`、`geo_candidate_provider_hash`、`geo_json_space` 各 0.01 s。三種原始前 20 在文末；零值不冒稱已精確排序的次要熱點。

**不能用 inclusive 精確分配 H／K／provider 成本。** resident callgraph 把 `geo_sha256` 的 14.50 s children 按呼叫數平均攤給 caller：provider 原符號的 3,145／6,306 得到約 7.23 s，遂顯示 7.25 s inclusive。此法不辨識 payload 大小；它不證明小型 provider metadata 實際花了 7.25 s。

原圖另列 `geo_candidate_provider_hash` 3,615 direct + 1,320 recursive，以及 World factory → provider 2,250 邊。這些**不能按符號字面當真 source 函式呼叫**。既有 `-O2 -pg` binary 的局部反組譯證實 provider 本體無自我呼叫；factory 實際呼叫九次 `app_candidate_bind_core`，其 tail-jump 進帶 mcount 的 bind-state clone 並直接做 SHA。原圖存在 clone／tail-call 歸屬失真，未追定 gprof 內部哪個映射步驟所致，不能據此重建精確 H/K/provider 次數。見 [局部反組譯原文](profile-attribution-readonly.txt) 與 [判讀](profile-attribution-readonly.md)。未更改 flags、重建或重跑。

| 版本／workload | self 前 20 | inclusive 前 20 | calls 前 20 | 完整 callgraph／gprof |
| --- | --- | --- | --- | --- |
| main／bridge-cold | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-cold/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-cold/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-cold/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/main/bridge-cold/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/main/bridge-cold/full-gprof.txt) |
| main／bridge-resident | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-resident/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-resident/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/bridge-resident/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/main/bridge-resident/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/main/bridge-resident/full-gprof.txt) |
| main／model-legacy | [CSV](artifacts/runs/20261018T201033419459-gprof/main/model-legacy/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/model-legacy/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/main/model-legacy/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/main/model-legacy/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/main/model-legacy/full-gprof.txt) |
| integration／bridge-cold | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-cold/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-cold/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-cold/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/integration/bridge-cold/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/integration/bridge-cold/full-gprof.txt) |
| integration／bridge-resident | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-resident/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-resident/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/bridge-resident/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/integration/bridge-resident/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/integration/bridge-resident/full-gprof.txt) |
| integration／model-legacy | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-legacy/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-legacy/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-legacy/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/integration/model-legacy/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/integration/model-legacy/full-gprof.txt) |
| integration／model-neutral | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-neutral/top20-self.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-neutral/top20-inclusive.csv) | [CSV](artifacts/runs/20261018T201033419459-gprof/integration/model-neutral/top20-calls.csv) | [圖](artifacts/runs/20261018T201033419459-gprof/integration/model-neutral/callgraph.txt)／[原文](artifacts/runs/20261018T201033419459-gprof/integration/model-neutral/full-gprof.txt) |

七份 profile 每份同目錄另存 `functions.json`、`cycles.json`、`flat-profile.txt`、`profile-inputs.json`，raw `gmon.out` 亦列入公開清單。

解讀邊界：

1. self 是 10 ms 粒度的可見 CPU 取樣；約 99% 不能轉稱 normal wall time 的 99%。inclusive 是 callgraph 推分，祖先子孫重疊，不能加總。calls 表為原圖 direct + recursive；root／spontaneous 未提供 count 的列不稱真正零次。
2. libc／libm 未 `-pg`，memcpy／memcmp／malloc 或等待成本未完整呈現，榜外不能排除。inline／clone 改變符號歸屬，provider 圖計數不能當 metadata 真次數。
3. resident profile 含一次預設世界初始化、前置 dump、`section-profile-read`、15 輪及退出，不是單一 phase 圖。cold／model 各合併 7 個 gmon。
4. normal 與 profile 是不同執行；不能拿 normal wall time 除 profile calls 算 ns/candidate，也不能用 profile wall time作倍率。profile 摘要全部 `ratio_to_main=null`。

## 根因定位、修正與未驗項

以下位置皆對應固定 **e64** archive，而非後來產品修改：`geometry-app/native/world_candidate.inc:26` 傳 `sizeof(World)`；`app_candidate.c:35,77` 在 before／after capture 無條件算完整 SHA，`:88–89` 後續才用 byte-exact cache 或 SHA fallback。World factory `:32–40` 另綁九份 K state，`geometry-core/kernel/candidate.c:87,127` eager hash before／current，`:94–95` 做比對。這些均進 codec 的 SHA block，與大量壓縮取樣及修改路徑退化吻合。

| 項目 | 分類／目前結論 | 分支、SHA 與三證據 |
| --- | --- | --- |
| 本輪 normal／profile 命令 | 全部成功，沒有工作負載失敗 | 原回應與退出完整保存 |
| 候選 SHA 工作量 | 產品效能問題；SHA block 為主要可見 CPU 熱點，H 全 World／K bound-state eager capture 是已定位重複來源 | 本報告僅 e64 修前；沒有修後、撤回或效能修正提交 SHA |
| provider metadata／operation seal | 保留完整性；gprof 歸屬與推分不足以證其真成本 | 不因 inclusive 排名刪除或延後 provider 封印 |
| 複製／memcmp | 本次不能獨立量化，不能因榜外宣稱排除 | 修後若仍重要再依證據補測 |
| #289 source graph | neutral 程序中位數多 21.184 ms；未隔離純建圖／Python facade | 不稱為全部 timeout 唯一根因 |
| HK deferred SHA（A）、publish 重複 check（D）、巢狀 candidate（B） | 外部候選／設計對應已定位路徑 | 後續採用與 commit、三證據另報；本階段不宣稱已修復或加速 |

後續須保留預設 eager API 與所有既有斷言、exact SHA256／byte guards、配置失敗 fallback、provider 完整性、發布判決；依主題保存修前、修後、撤回轉紅，並重跑相同 normal 工作負載。A／D 同一主題分支、B 另一分支。外部 patch 不能當已提交修正；本報告不混入後續實作狀態。

**尚未量測**：真 SHA payload MB/s、明確 candidate lifecycle ns／CPU 時間、硬體 cycles。現有工具沒有獨立總 payload bytes 或 lifecycle 計時，不由 blockcalls 推吞吐，也不以秒乘 GHz 假造 cycles；補測需明確 scope。

**尚未完成驗收**：修後三證據、原 timeout 內完整 model_update／space_modeling／Node suites、bridge_integrity 與全量最終驗收、修後六 browser、最終 mutation／architecture 收據。前兩階段紅燈不被本次代表性工作負載成功覆蓋。

## 公開原始檔案

`phase3-publication-inventory.json` 逐檔列公開來源、目標相對路徑、bytes、SHA-256。包含兩個固定 run 全部原始回應／stderr／逐樣本、七份完整 gprof／三種前 20／raw gmon、工具／輸入／build 身分；未混入後續修正 run。可重建 executable 留本地並列 hash，公開重建命令。原 `profile-inputs.json` 絕對路徑保持原樣。本報告沒有發布留言或 push。

## integration resident：三種原始前 20

calls 忠實保留 gprof 原歸屬，**不代表已確認的 source 函式真次數**；provider 異常已說明，self 相同零值只是原 CSV 排序。

### self前 20

| 原始符號 | self s | children s | inclusive s | direct / recursive / total calls |
| --- | ---: | ---: | ---: | ---: |
| `geo_sha_block` | 14.50 | 0.00 | 14.50 | 53,019,413 / 0 / 53,019,413 |
| `geo_sha256` | 0.02 | 14.50 | 14.52 | 6,306 / 0 / 6,306 |
| `app_candidate_bind_core` | 0.01 | 0.00 | 0.01 | 2,250 / 0 / 2,250 |
| `geo_candidate_provider_hash` | 0.01 | 7.24 | 7.25 | 3,615 / 1,320 / 4,935 |
| `geo_json_space` | 0.01 | 0.00 | 0.01 | 未提供 |
| `app_asm_context` | 0.00 | 0.00 | 0.00 | 1,301 / 0 / 1,301 |
| `app_assembly_saved_dimensions` | 0.00 | 0.00 | 0.00 | 343 / 0 / 343 |
| `app_boundary_compose` | 0.00 | 0.00 | 0.00 | 1,030 / 0 / 1,030 |
| `app_boundary_policy` | 0.00 | 0.00 | 0.00 | 16 / 0 / 16 |
| `app_boundary_region_definition` | 0.00 | 0.00 | 0.00 | 16 / 0 / 16 |
| `app_boundary_stage` | 0.00 | 0.00 | 0.00 | 16 / 0 / 16 |
| `app_candidate_call` | 0.00 | 0.00 | 0.00 | 235 / 0 / 235 |
| `app_candidate_check` | 0.00 | 1.39 | 1.39 | 440 / 220 / 660 |
| `app_candidate_create` | 0.00 | 0.58 | 0.58 | 250 / 0 / 250 |
| `app_candidate_evaluate <cycle 2>` | 0.00 | 0.54 | 0.54 | 235 / 0 / 235 |
| `app_contact_facts` | 0.00 | 0.00 | 0.00 | 5,145 / 0 / 5,145 |
| `app_contact_resolve_stops <cycle 1>` | 0.00 | 0.00 | 0.00 | 2,058 / 0 / 2,058 |
| `app_dp_context` | 0.00 | 0.00 | 0.00 | 344 / 0 / 344 |
| `app_eng_context` | 0.00 | 0.00 | 0.00 | 5,469 / 0 / 5,469 |
| `app_eng_serializable` | 0.00 | 0.00 | 0.00 | 172 / 0 / 172 |

### 含子呼叫累積前 20

| 原始符號 | self s | children s | inclusive s | direct / recursive / total calls |
| --- | ---: | ---: | ---: | ---: |
| `main` | 0.00 | 14.54 | 14.54 | 未提供 |
| `geo_sha256` | 0.02 | 14.50 | 14.52 | 6,306 / 0 / 6,306 |
| `geo_sha_block` | 14.50 | 0.00 | 14.50 | 53,019,413 / 0 / 53,019,413 |
| `geo_candidate_provider_hash` | 0.01 | 7.24 | 7.25 | 3,615 / 1,320 / 4,935 |
| `geo_candidate_evaluate <cycle 2>` | 0.00 | 5.34 | 5.34 | 235 / 0 / 235 |
| `app_world_candidate_create` | 0.00 | 5.10 | 5.10 | 250 / 0 / 250 |
| `apply_scene_line <cycle 2>` | 0.00 | 4.47 | 4.47 | 219 / 0 / 219 |
| `apply_scene_line_candidate.constprop.0 <cycle 2>` | 0.00 | 2.93 | 2.93 | 219 / 0 / 219 |
| `app_replace_world.constprop.0` | 0.00 | 2.56 | 2.56 | 16 / 0 / 16 |
| `cmd_replace_world` | 0.00 | 2.40 | 2.40 | 15 / 0 / 15 |
| `app_world_candidate_publish` | 0.00 | 1.83 | 1.83 | 220 / 0 / 220 |
| `app_world_candidate_seal` | 0.00 | 1.48 | 1.48 | 235 / 0 / 235 |
| `app_candidate_check` | 0.00 | 1.39 | 1.39 | 440 / 220 / 660 |
| `geo_candidate_seal` | 0.00 | 0.94 | 0.94 | 235 / 235 / 470 |
| `app_candidate_create` | 0.00 | 0.58 | 0.58 | 250 / 0 / 250 |
| `app_candidate_evaluate <cycle 2>` | 0.00 | 0.54 | 0.54 | 235 / 0 / 235 |
| `boundary_geometry_hash` | 0.00 | 0.14 | 0.14 | 60 / 0 / 60 |
| `eng_definition_hash` | 0.00 | 0.11 | 0.11 | 46 / 0 / 46 |
| `json_boundary_preview` | 0.00 | 0.07 | 0.07 | 15 / 0 / 15 |
| `json_reference_preview` | 0.00 | 0.07 | 0.07 | 15 / 0 / 15 |

### 呼叫數前 20

| 原始符號 | self s | children s | inclusive s | direct / recursive / total calls |
| --- | ---: | ---: | ---: | ---: |
| `geo_sha_block` | 14.50 | 0.00 | 14.50 | 53,019,413 / 0 / 53,019,413 |
| `geo_eval_source <cycle 1>` | 0.00 | 0.00 | 0.00 | 60,810 / 0 / 60,810 |
| `geo_source_edge` | 0.00 | 0.00 | 0.00 | 60,810 / 0 / 60,810 |
| `geo_source_node` | 0.00 | 0.00 | 0.00 | 60,810 / 0 / 60,810 |
| `wd_read_text.constprop.0` | 0.00 | 0.00 | 0.00 | 27,675 / 0 / 27,675 |
| `reference_sources_ensure` | 0.00 | 0.00 | 0.00 | 21,183 / 0 / 21,183 |
| `wood_grid_coordinate_source <cycle 1>` | 0.00 | 0.00 | 0.00 | 18,294 / 0 / 18,294 |
| `wood_contact_source_decode` | 0.00 | 0.00 | 0.00 | 16,660 / 0 / 16,660 |
| `geo_loop_contains_point` | 0.00 | 0.00 | 0.00 | 15,498 / 0 / 15,498 |
| `geo_loop_point_on_edge` | 0.00 | 0.00 | 0.00 | 15,498 / 0 / 15,498 |
| `timber_a0_footprint_uv` | 0.00 | 0.00 | 0.00 | 14,205 / 0 / 14,205 |
| `wd_write` | 0.00 | 0.00 | 0.00 | 14,143 / 0 / 14,143 |
| `wood_definition_sources_boundary <cycle 1>` | 0.00 | 0.00 | 0.00 | 6,110 / 6,110 / 12,220 |
| `geo_frame_direction` | 0.00 | 0.00 | 0.00 | 12,124 / 0 / 12,124 |
| `geo_rectangle_footprint` | 0.00 | 0.00 | 0.00 | 11,781 / 0 / 11,781 |
| `clip_loop_order` | 0.00 | 0.00 | 0.00 | 11,085 / 0 / 11,085 |
| `geo_source_copy_text` | 0.00 | 0.00 | 0.00 | 10,068 / 0 / 10,068 |
| `wood_definition_sources_placement <cycle 1>` | 0.00 | 0.00 | 0.00 | 9,225 / 0 / 9,225 |
| `wd_reader <cycle 1>` | 0.00 | 0.00 | 0.00 | 8,383 / 0 / 8,383 |
| `wood_contact_source_collection_view` | 0.00 | 0.00 | 0.00 | 8,330 / 0 / 8,330 |

