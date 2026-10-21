# #300 bench 草稿與舊結果：只讀盤點

本次完整讀過 `bench.sh`（287 行）、`drive.py`（864 行）、`fit.py`（594 行）、`gen_scene.py`（375 行）、`calib/f3-00.scene`（212 行）及 `results/` 全部五個原件。兩份建置 log 各 443 行：完整讀取兩檔 bytes，逐行比較後讀完共同 424 行與全部 19 處差異。README 由主審代理完整讀取，本次另核對與工具行為有關的指定段落。

來源是交接分支 commit `59796b1af9259eb23d30134c2ce5a56317a06091` 的 `handoff/drafts/issue300/bench/`。全程未執行 bench、生成器、selftest、fit、測試或建置，未改產品或原稿；僅新增本外部說明。以下為靜態判讀，不是新驗收，也不替使用者決定容量或門檻。

## 舊結果實際證明的範圍

`results/env.txt:1–7` 記錄 2026-10-20T06:56:24Z、來源 `603e4195cf4336321f8c6aa2b90d7ee8969e0572`、patch SHA-256 `8cfaa00217914ff77c3341a91f241de9847f89431d0eedca53d2ffe29e9aeb17`，環境為 WSL2 kernel 6.6.114.1、AMD Ryzen 5 7535HS、12 CPU、約 7.7 GB 記憶體、gcc 13.3.0；啟動前 soft stack 8192 KiB、hard unlimited。

`results/STATUS:1` 明確是 **SANITY-FAILED rc=3**。`bench.tsv` 只有表頭加 15 列：

| 原件行號 | 內容 | 可以說什麼 |
|---|---|---|
| 2–3 | cap64 World 4,759,448 bytes；cap512 World 5,605,272 bytes | 舊二進位回報的 World 大小；不能推實際呼叫鏈堆疊峰值。 |
| 4–5 | calib48：18.337452／19.870240 s，均 rc0 | 舊環境兩容量的已知場景 sanity 接受。 |
| 6–13 | single N16/32/48/64，兩容量均 rc0 | 這四個生成場景在舊環境接受；N64 分別 59.616386／58.634075 s。只有各一次 sanity。 |
| 14 | house N128、cap512、300.002229 s、rc3、got=timeout | 300 秒未取得完整 loadfile 回應；沒有拒絕理由，也沒有完成時間。 |
| 15 | N65、cap64、rc0、error「角材的數量超過上限」 | 這列 rc0 是 sanity oracle 如預期看到容量拒絕，不是產品接受第65支。 |
| 16 | N65、cap512、71.848979 s、rc0 | 舊環境此場景接受第65支。 |

第15列 `got=ok` 字樣容易誤讀。`drive.py:351–358` 的 `st=="ok"` 表示收到可解析 JSON；在拒絕分支只有 `!got_ok && reject_substr in error` 才算 good。因此該列不是錯放行，只是協定狀態與業務結果共用 ok 字樣。

沒有任何 `load`、`line-*`、`load-modelbase`、`stack:*` 正式列；沒有 fit.md／fit.json，沒有完整測試或突變證據。不得宣稱立方／四次已證、512 可行／不可行已定、N300 時間已測、16 MiB 有兩 MiB 餘裕，或目前最終 L 的效能。兩份 build log 只有格式截斷警告與末尾 time：cap64 real/user/sys=41.726/40.822/1.207 s；cap512=41.578/40.648/1.230 s（各 `:441–443`）。後續 sanity 可執行支持「曾有可執行 bridge」；原件沒有獨立 build argv/exit receipt、binary SHA、STAMP 或完整 bridge JSON，不能把未保存的細節補成原始證據。

## 命令與來源契約

草稿入口為 `bash bench.sh all`，設計外包 WSL 鎖（`bench.sh:4–7`）；其他子命令 build/sanity/stack/run/fit/status/selftest 見 `:9–19、245–287`。這些只是已讀設計，本次全未執行。

預設環境（`:21–42、68–85`）：

- `BENCH_REPO=/mnt/d/geometry-axiom`、`BENCH_SHA=603e4195`、patch=`../patch.diff`。
- `BENCH_ROOT=/var/tmp/ga-bench300`；結果固定追加 `out/bench.tsv`；預設複製到 Windows drafts/issue300/bench/results。
- soft budget 1500 s、hard extra 240 s、主量測單指令 timeout 900 s；reps3、首個成功 load 超過20 s則降為1次。
- cap64/512；single N16/32/64/128/256/512；house N128/256/512；可選 model-base。
- stack rungs 16384→4096 KiB、二分解析度256 KiB；所有正常量測外層設16384 KiB（`:218–221`）。
- **CC 預設 gcc；找不到才改 cc**（`:84–85`），與 L native 的「父環境 CC absent、CI/default cc」不是同一字面編譯契約。後續若採用，必須獨立記錄實際 argv、編譯器身分，不能直接沿用舊 gcc 成績。

`phase_source` 先查本機 ext4 mirrors，再查 BENCH_REPO（`:103–124`），以固定 full SHA archive 產品根目錄與三個 stack scene（`:132–138`）；src512=src64加產品 patch，排除 tests/* 與 ARCHITECTURE.md（`:148–164`）。因此單是 benchmark 建置不等於完整 #300 patch 的測試／架構驗收。

編譯 argv 是 `$CC -std=c11 -O2 geometry-web/web_bridge.c -o <bin>/bridge.new -lm`；可選 `geometry-core/model_base.c`（`:177–182`）。兩容量平行編譯（`:189–195`）。來源快取 stamp 只用 SHA、patch hash；binary stamp 用 SHA、patch hash、CC版本第一行、固定flags與model開關（`:126、150、172–174`），沒有驗證暫存來源／binary bytes未被手改，也沒有把編譯器完整路徑或工具腳本 hash 綁入 TSV。

續跑 TSV 沒有 source SHA／patch hash／compiler／tool hash 欄位（`drive.py:46、64–109`）。`unit_state:395–405` 只按 family/N/cap/rep 讀舊 load 列。即使換 BENCH_SHA 令 binary 重編，只要沿用同 BENCH_ROOT，舊 TSV 仍會被當已完成；env.txt 又在每次重寫（`bench.sh:200–209`）。未來必須以全新來源隔離目錄或明確驗證來源指紋，不能拿現成 out 續成另一 SHA 的結果。

## 停止條件與實際缺口

| 設計／聲稱 | 實際實作與風險 |
|---|---|
| README:85「含build合計≤29分鐘」 | 沒有包全流程的外層 timeout。build 的 wait 無期限（bench.sh:178、195）；worldbytes 固定60秒（drive.py:311）；sanity 每次 load 固定300秒（330–350）且不看budget。stack一次probe把同一 timeout 用於多條指令（563–570），可跨越剩餘時間。此硬上限尚未由程式保證。 |
| sanity失敗停止 | bench.sh:269 確實 publish SANITY-FAILED 並退出。正常 run/stack/all 都必先完整sanity（265–270），每次都重跑，無resume跳過。 |
| 提高 BENCH_RUN_TIMEOUT 可重試 | 只作用於主run；sanity仍固定300秒，且 house128 不受 BENCH_FAMILIES/NS篩選（drive.py:364–378）。因此舊house128 timeout 在未修工具前會一直擋主量測；--retry-timeouts亦只影響load單元。 |
| 校準成功但生成場景失敗＝句型錯誤 | drive.py:383–385 把timeout/crash/協定錯誤與明確拒絕合併，統一宣稱「產生器寫出核心不接受句型」。舊row14只有timeout，不能作此歸因。 |
| run exit0全部完成 | unit_state:400–401 把reject、timeout、crash、protocol error視為確定性完成；cmd_run:542 只因deferred返回10，其他可能exit0。DONE rc0不是產品測試全綠。 |
| 所有步驟完成才記單元完成 | unit_state只看load。run_process:446–458 的line-grid/delete/timber/place失敗只break，load仍是0；下次可直接跳過該單元。硬期限若在line階段到達，load列仍可使unit完成，缺少完整line數量自證。 |
| 中斷保證帶走bridge | bench.sh:99只TERM直接子程序；drive.py:117–128僅在setpriv可用時才加pdeathsig，無強制要求或原件記錄。未證全部環境的清理保證。 |
| all確實完成stack與fit | bench.sh:276的phase_stack rc被後面的phase_run覆蓋；280的phase_fit rc未併入final rc。build失敗有處理，但不能由最終0倒推stack/fit成功。 |
| worldbytes失敗會阻擋 | drive.py:326寫unreadable rc2後，327仍return0；bench.sh:268看不到這項失敗。 |
| modelbase符合相同截止 | drive.py:479–489用max(1,剩餘時間)，截止已過仍可啟動；timeout一律記124而非硬期限125；未比對model內容與bridge幾何。 |

## 夾具與裁判能說到哪裡

calib檔有一個surface、一個grid、48個timber/place；角色及矩形來自F3探針註解。`gen_scene.py:25–26` 自承幾何自測不是核心接受證據。其 selftest 也不是完整語句逐byte／逐順序重現：`:299–306` 只固定前8支，後續place去掉id後排序比較、timber以去id後的multiset比較、矩形排序比較。README:50「逐句重現全部98行」應限定此正規化方法；不是本次或任何大N的真核心驗收。

主run的具體工作負載是fresh bridge→loadfile→同一grid宣告3次→刪除/重建/重新放置第一個房間的末支副支各2輪（`drive.py:419–458`，`gen_scene.py:237–247`）。只有 `resp.ok` 判定，沒有幾何、revision、刪除集合、來源圖或輸出bytes oracle；同一grid指令反覆送出也未證是實際改動而非相同定義重驗。單元順序按N/family/cap，並非交錯隨機比較，慢load又只做一次；不能由少數樣本宣告小幅回歸或純容量成本。

`Bridge.cmd:180–201` 是送入stdin後等一行JSON的牆鐘，CPU/RSS只是盡力採樣。`run_modelbase:485` 只找stdout前200bytes的 `"ok":true` 子字串，亦不是語意等價裁判。舊TSV保留結果摘要但沒有原始回應；sanityCPU欄未落盤（330–341）。

## fit／堆疊結論不可直接當 gate

- fit.py只採成功樣本（67–73），沒有檢查STATUS、sanity總結果或同來源指紋；timeout只出現在涵蓋表，不參與時間下界或總判定。沒有正式load列時資料不足，不能把sanity數字當其已擬合曲線。
- `:344–358、441–448` 把single曲線稱為house上界，甚至由上界PASS推house PASS。這是未證假說；較多宿主、不同依賴結構與求值順序的成本不由總N與單面P直接給出嚴格上界。log-log外插的兩個估計範圍（178–192）亦不是統計信賴區間或安全界。
- `:242–243` 的「load斜率−1」與 `:301–304` 的「N<256所以不能否定立方」，都是模型假說，不能由有限量測證明漸近複雜度；本次更沒有正式量測點。
- stack只有ax_r13/ax_r10/ax_r17/gen64（drive.py:547–559）；每rung存out摘要hash，但未比較不同rung的hash（565–589）。只有ok與exit oracle，沒證明輸出一致。
- driver把126、timeout、protocol error與signal都作rung failure（618–655）；fit又把rc1刪掉、其他非0全部視為失敗（384–409）。因此「stack fail」不等於已證堆疊溢位；SIGSEGV本身也不能單憑訊號確認成因。
- fit.py:376–409沒有要求全部四個工作負載齊備；只要部分有pass就能形成min_stack。若16384沒有測，只要較低rung成功也可在454–459得到PASS；無效／缺失負載及非單調結果沒有全面阻擋。不能據此聲稱「所有負載都過」。
- fit.py:421與README:153說「堆疊和N無關、N64足以代表」。固定容量只能約束部分單一框架大小，不能證明遞迴深度、live frames數、其他工作負載與N無關。World大小的兩／三倍也不能直接推實際峰值或是哪條呼叫鏈。
- README:131的「至少2 MiB餘裕」算式對應最小通過≤14 MiB；其:142卻用「最小通過≥14.4 MiB」當FAIL描述，門檻文字不一致。fit.py:458–459用精確2 MiB。且門檻本身仍是建議，不能由本代理或程式替使用者定案。
- README:130及fit.py:358援引30秒bridge timeout；只讀目前程式serve.py仍有30.0，但這只說明服務期限，不是使用者已批准512或單一house workload的完整可用性門檻。
- fit.py:559–590在報告FAIL或資料不足時仍exit0；這是報告工具完成狀態，不是驗收通過。

## 完成核對與最大不確定

完整讀檔／原件SHA-256核對均以Python `Path.read_bytes`，exit0；沒有import或執行這四支腳本。突變自證與工具誤判的動態正反控制本次均未執行。未驗：生成器真核驗（除歷史sanity）、完整raw回應、正式曲線、stack ladder、model-base、來源圖及容量512產品測試。

最大不確定是舊house128 timeout的真正成本所在：目前只知道未在300秒完成，沒有profile／完整回應可以分辨求值成本、環境競爭或其他阻塞。這不能歸因為場景句型，也不能外推到最終L或直接決定#300採納與否。

原件SHA-256（路徑相對bench/）：

| 原件 | SHA-256 |
|---|---|
| bench.sh | 76f361556fbe6a04a42afaa6114069417509460084e384ce16b3fe83a71dfa1f |
| drive.py | 34b6ccafaf07d4184f95cebd1fb462dea280f2d977b2e97c42db060e68078ca1 |
| fit.py | 6098027dab002b2fef4587f708c3f2194ee65982caaf340c6900be7342388b9d |
| gen_scene.py | 347142beb7aa06c39969cd5bce35bacddc0734046eb7853e84d96f1ff9ef7c91 |
| calib/f3-00.scene | 35e24fb0a483ffd6fee8dd99f751edeb127418481aa717816af804cd218024b2 |
| results/STATUS | 37ab9be176ed57b5c71d528bc836edd6a8257818a802e69677bbd1efe3ddfe12 |
| results/bench.tsv | bd2b54264a5bf4841e220e4470be70365785e11eb048c5365a9146963bab8c3a |
| results/build-cap512.log | b64a261865f43d03609749dd2e7d78e6d66aabe8b63c8dd110ae6055936659b9 |
| results/build-cap64.log | 03384be2bd177acc9fa507f3b6e1196493013c83703e94f1310cb252d58658ee |
| results/env.txt | 337bd6ecacebcc25ff71ed55857725581cdc47004ad47862bfc76f7fb36d87de |

