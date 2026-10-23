# Default owned replay：gprof 原件唯讀複核

本文件整理既有原件的獨立唯讀複核，未執行產品、測試、編譯、量測或 gprof，未更改原證據。讀取範圍為摘要、環境紀錄、各工作負載的 flat/functions/top20 小文字，以及 cold/resident 的局部 callgraph；未重新雜湊大型執行檔或 gmon。

本輪原件：`../artifacts-adbd-68eed6fb/runs/20261018T224925766853-gprof/`。摘要記錄 complete=true，main 為 `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425`，integration 為 `68eed6fb0e488003ca0a4d8614a9460a637d979e`。對照原件：`../artifacts-adb-8ab0bdb4/runs/20261018T215825197230-gprof/`。

## 七組原件與稀疏取樣

設定為 cold_repeats=7、rounds=15、model_repeats=7、stack_limit=[16777216,-1]，共 37 份 gmon。resident 是一個包含啟動與 15 輪、每輪九段命令的進程，不能解讀為已扣除啟動成本。

| 工作負載 | gmon 份數 | flat 累計 self | 非零 self 與原 gprof 符號計數 |
|---|---:|---:|---|
| main bridge-cold | 7 | 0 | no time accumulated |
| main bridge-resident | 1 | 0 | no time accumulated |
| main model-legacy | 7 | 0 | no time accumulated |
| integration bridge-cold | 7 | 0.01 秒 | geo_placement_definition_decode：100%，calls=1778 |
| integration bridge-resident | 1 | 0.04 秒 | 下列四項各 0.01 秒、25% |
| integration model-legacy | 7 | 0.01 秒 | main：100%；原 flat 未列 calls |
| integration model-neutral | 7 | 0 | no time accumulated |

resident 四項為 `wood_grid_world_valid_direct`（calls=172）、`wood_world_validate_members`（172）、`app_world_candidate_create`（138）及 `reference_asm_guide`（原 flat 未列 calls，callgraph 為 spontaneous）。後者與 legacy 的 main 均不可把 functions.json 的補值 0 解讀成實際未呼叫。

gmon 份數不是 CPU 取樣數。原報表雖標示每 sample 為 0.01 秒，這些累計 self 極少，不能據此建立穩定的熱點排序；no time accumulated 也不代表沒有執行或沒有成本。累計值採 flat 的 cumulative 欄，不能任意加總四捨五入後的各函式 self；舊 8ab resident 有六列各印 0.01 秒，累計卻是 0.04 秒。

## 8ab → 68eed 的原 gprof 符號計數

以下 calls 僅是原 gprof 符號計數，不視為精確的 source-level 函式呼叫次數。

| integration 工作負載 | app_world_candidate_create | app_candidate_bind_core | geo_sha256 | geo_sha_block |
|---|---:|---:|---:|---:|
| bridge-cold | 70 → 21 | 630 → 189 | 357 → 112 | 3794 → 1617 |
| bridge-resident | 145 → 138 | 1305 → 1242 | 711 → 676 | 8177 → 7866 |
| model-legacy | 70 → 70 | 630 → 630 | 350 → 350 | 3731 → 3731 |
| model-neutral | 70 → 70 | 630 → 630 | 371 → 371 | 3857 → 3857 |

`app_candidate_create_with_deferred_sha` 的相應計數也從 70/145/70/70 變為 21/138/70/70。cold 減少 49，與七次啟動、每次省去七個 inner candidate 的預期結構相符；resident 減少七，與只在一次啟動執行 default、其後 15 輪沒有 default 命令的結構相符。這是原符號計數與產品結構的相容性觀察，不是 gprof 對精確 source-level 次數的獨立證明。

上述四組的 `geo_eval_source` 原符號計數依序為 15225、60810、15225、16520，兩版均未變。此結論只限固定工作負載及原符號計數，不推論所有圖工作量、配置量或記憶體成本不變。兩個 model 模式的上述計數未變，不能把 normal 時間波動歸因於本次 default 修改。

## 歸屬及成本解讀界線

本輪 `geo_candidate_provider_hash` 的原符號計數分別為 cold 294（direct 252＋recursive 42）、resident 1797（1581＋216）、legacy 980（840＋140）、neutral 980（840＋140）。cold 的 world-create→provider 弧及 bind-core 計數均為 189；resident 均為 1242，分別與 21×9、138×9 相符。然而 provider 的 callgraph 子項仍混有 copy_text、digest_matches 及自遞迴歸屬，延續既有 O2 inline／nearest-symbol 歸屬問題，不能宣稱 provider 真正遞迴或把這些數字當成原始碼實際呼叫次數。

inclusive 會依呼叫計數平均分攤，不能精確拆成 H、K、provider metadata 的各自成本；inclusive 各列也不能相加當總成本。未以 -pg 插樁的 libc 不提供可據以排除成本的 memcpy/memcmp 列，函式未出現在報表不代表其成本不存在。

profile 執行時間不能當 normal 效能倍率；摘要也明記 profile_times_are_not_regression_ratios=true。這些資料不能嚴格推出真實 bytes/sec 或 CPU cycles；cycles.json 的 cycles 是 callgraph 遞迴環，不是 CPU cycles。此輪稀疏 self 不足以另立新的效能主因，也不足以判定 neutral 來源圖可省略。

## 既有四態 raw 收據

另已唯讀核對 `../../fixes/perf-default-replay/raw-comparison.json` 及 support/enabled/withdrawn/restored 的六流程原始 stdin/stdout/stderr。每態六流程共 80 個 response，各流程均 exit=0、ok=true、exception=null；相對 support，三態 × 六流程 × 三串流共 54/54 逐 bytes 相同，未正規化輸出。已檢查的原串流長度、雜湊與收據相符。

凍結 driver 為 14248 bytes、SHA-256 `7cfbcbd4d0bd0440be5c03075e08b4ac087b208815ce81d682f3b703b3cccc07`；restored 收據記錄 source 為 `68eed6fb0e488003ca0a4d8614a9460a637d979e`。此 raw 比較支持這六個指定流程的輸出相同，不擴張為任意輸入等價，也不把 capture 的單輪耗時當效能證據。
