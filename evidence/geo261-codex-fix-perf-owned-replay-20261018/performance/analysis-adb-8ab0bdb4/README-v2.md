# A/D+B：8ab0bdb4 正式效能量測分析 v2

受測來源 `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6`，main 對照 `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425`。normal 與 gprof 都完整退出 0；**正式 registry bridge 兩輪各 24/24 零 skip，86.818／36.493 秒 = 2.37903159510043×，≤2 倍目標未通過**。以下倍率只取 normal，同輪 main 為分母；profile 時間不作退化倍率。

| 工作／樣本數 | e64 normal 中位數 ms（相對同輪 main） | A/D normal 中位數 ms（相對同輪 main） | A/D+B normal 中位數 ms（相對同輪 main） | 本輪 main ms |
|---|---:|---:|---:|---:|
| resident load_scene／15 | 831.183（26.945×） | 92.893（3.423×） | **50.800（2.021380×）** | 25.132 |
| cold_start_dump／7 | 1091.693（22.052×） | 184.419（3.651×） | **186.136（3.636984×）** | 51.179 |
| model-legacy／7 | 878.460（16.057×） | 170.292（3.644×） | **220.971（4.571126×）** | 48.341 |
| model-neutral／7 | 899.644 | 163.509 | **195.707** | 未量測 counterpart |

三版本為 e64 `e64aa635`、A/D `57d916fb`、A/D+B `8ab0bdb4`；各有自己的同輪 main，不能把不同輪次當成交錯配對實驗。本輪 load_scene 範圍 36.254–87.686 ms，p95 87.686 ms；2.021380× 不四捨五入冒充 ≤2。其餘 normal 各段完整值見 [36 列比較 CSV](normal-comparison.csv)：本輪 reset 9.553 ms／17.623×、canvas_position 7.731 ms／2.819×、unused_spec_create 10.361 ms／2.174×、unused_spec_replace 10.715 ms／3.144×、preview_spec 7.887 ms／2.245×、cancel_preview 3.074 ms／8.165×；小操作的倍率仍須連絕對耗時一起看。

這輪 model-neutral 中位數比 legacy 少 25.264 ms，**不能解讀為建圖是負成本**。兩者各只有 7 個非配對程序樣本，legacy 範圍 163.156–337.390 ms、neutral 171.188–250.184 ms。A/D→A/D+B 的 model_base、model_native、model_runtime、modeling/base、modeling/engine Git bytes 全無差異；不得把這個跨輪波動歸因於 B。此 model 指標是直接 C subprocess 牆鐘，不包含 Python model_native／decoder／runtime。

## gprof 能支持的原因與界線

原 e64 的主要可見瓶頸是 `geo_sha_block`：cold／resident／model-legacy／model-neutral 的原 flat self 分別 4.15／14.50／4.32／4.11 秒，占取樣的 99.64／99.66／99.31／99.28%。A/D 大幅消除了重複完整候選 SHA；B 在已有外層交易的 loadfile 進一步減少逐行候選建立。原 gprof 記錄如下，保持相同工作數，**這是記錄的 calls，不是牆鐘倍率**：

| workload | e64 geo_sha_block calls | A/D calls | A/D+B calls |
|---|---:|---:|---:|
| bridge-cold | 15,304,751 | 3,794 | 3,794 |
| bridge-resident（含 startup） | 53,019,413 | 12,842 | 8,177 |
| model-legacy | 15,304,688 | 3,731 | 3,731 |
| model-neutral | 15,304,814 | 3,857 | 3,857 |

resident 的 `app_world_candidate_create` 記錄由 250→145，`app_candidate_bind_core` 2250→1305，`geo_sha256` 1236→711；cold 與兩種 model 的候選建立都保持 70。這與 B 只讓 web bridge 的外層 candidate 重用 file replay 相符，不支持「B 已優化 model-base」的說法。

本輪尚不足以指定剩餘牆鐘時間的主要函式。integration cold／legacy 的 flat 都明示 **no time accumulated**；resident 原 flat 累計只有 **0.04 秒**，neutral 只有 **0.01 秒**，且唯一非零項是 `_init`。resident 原 flat 的 `reference_contact_facts`、`wood_contact_collect_stops` 各 25%；`wd_write`、`geo_region_is_valid`、`reference_guide_clip_text`、`wood_eng_version_definition` 各 12.5%。每列秒數顯示為 0.01，**不可相加成 0.06 秒**；少量量化樣本不足以確定其名次或瓶頸比例。inclusive 的 main 0.04、world_validate_derived 0.03、app_scene_candidate_apply 0.02、wood_world_validate_members 0.02 也不能跨呼叫層加總。

全部 integration 前 20 self／inclusive 原值見 [四份表](top20-adb-integration.md)；含 main 與三版本共 840 列見 [完整 CSV](top20-self-inclusive.csv)。零時間同值按函式名稱排序，不能稱為有效熱點排名。原編譯維持 `-O2`，gprof 有 inline／nearest-symbol 錯歸屬及平均分攤限制；`provider_hash` 仍出現假遞迴，其記錄的 calls 也不能當成 provider 原始碼的真呼叫數；不能拿其 inclusive 精分 H／K／provider 成本。callgraph 的 cycle 不是 CPU cycles。libc 未以 `-pg` 插樁，沒列出 memcpy／memcmp 不表示其沒有成本；本輪也沒有證據將未解釋時間全部歸給它們。

## 身分、原件與完成度

唯讀核對 e64、A/D、A/D+B 三組共 **24 個實際 binary hash、1,035 個來源檔實例與固定 Git blob／source manifest**；來源總數依序為 284＋59、287＋59、287＋59。原 tar 沒有另存，`archive_sha256` 只轉錄原 manifest，沒有冒稱重新核 tar。每個 binary 的 source SHA、原 compile argv、實際 C 閉包、`-O2`／`-pg`、原 mcount undefined-symbol 證據均一致；沒有重新執行 compiler 或 nm。

六輪（各版本 normal／gprof）**每輪皆 305 samples、23 groups**：兩端 cold 各 7、兩端 resident 九段各 15、main legacy 7、integration legacy／neutral 各 7；逐 iteration 與原 timing／response 及 summary 中位數／p95／ratio 核對。每輪另核 288 個 bridge 原回應、21 份 model 原輸出；每個 profile run 37 個實際 gmon hash 與 profile binary 一致。本次未發現 identity、計數或原件對照錯誤，細項在 [verification.json](verification.json)，精簡數值在 [results-v2.json](results-v2.json)。

本輪四 stage 的原 argv 相互獨立，原 stdout／stderr hash、UTC、exit 0 與固定工具前後身分全部吻合：`measure_geo261.py` SHA `46b806df…`、stage recorder SHA `e0e9dc40…`。measure 為 UTC 13:58:17.167602–13:58:25.119695，profile 為 13:58:25.120164–13:58:34.475866。依主代理明確排程通知，build 與 native functional 並行，**build 耗時不作效能比較**；measure／profile 獨占，無其他 root tests／build。這個排程說明來自主代理，不能冒稱 recorder 自動證明全機 CPU 排他。

原件：新 [normal summary](../artifacts-adb-8ab0bdb4/runs/20261018T215817250874-normal/summary.json)、[gprof summary](../artifacts-adb-8ab0bdb4/runs/20261018T215825197230-gprof/summary.json)、[stage receipt](../artifacts-adb-8ab0bdb4/stage-records/20261018T135817166992Z/receipt.json)；舊 [e64 normal](https://github.com/ZhiQiYang/geometry-axiom/blob/d5423381bcdfa7c67366bedca92eb47a06209879/evidence/geo261-codex-validation-20261018/performance/artifacts/runs/20261018T200850689427-normal/summary.json)、[A/D normal](https://github.com/ZhiQiYang/geometry-axiom/blob/875235e2227d93336b798d9b4548e2c2fa67c3fe/evidence/geo261-codex-fix-perf-candidate-sha-20261018/performance/artifacts-ad-57d916fb/runs/20261018T203438052503-normal/summary.json)。本報告只新增外部分析資料，未執行產品、gprof、build、測試或修改 repo；正式 bridge ≤2 倍未通過，全量非瀏覽器及六瀏覽器驗收也未因此完成。

## 正式 bridge 追加驗證

完整分層計時、68 份共同輸入、registry binary／sidecar 身分及 runner／scanner 差異見 [bridge-registry-comparison.md](bridge-registry-comparison.md)。原 main archive 試跑雖 exit 0，但 24 方法共 149 次 skip，因缺 sidecar 而無效，保留原文並排除所有倍率。正式兩輪 source／head／status 均穩定；對照來源 full SHA 不變。外部 v1 README／results 保留作當時歷史狀態，請以本 v2 判讀目前 bridge 結論。
