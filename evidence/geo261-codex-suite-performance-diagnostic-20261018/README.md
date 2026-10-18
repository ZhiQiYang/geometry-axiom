# GEO-261：完整 bridge suite 的剩餘效能診斷

原正式動態驗收仍是 **main 38.161 秒、candidate 81.171 秒，2.1270669008×，未達 ≤2×**。本輪補做原完整 suite 的分段觀測、動態 gprof 與 static-libc gprof，沒有新產品修正。所有診斷固定在 main `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425` 與 candidate `68eed6fb0e488003ca0a4d8614a9460a637d979e`；即使本報告從較新的 integration `a25d975bdcc809bc63593d5b434663083395444b` 封存，也不是測過 a25。

## 實際結果

| 模式 | main | candidate | 每版實際呼叫 |
| --- | --- | --- | --- |
| 原正式 normal | 24/24，零 skip，38.161 s | 24/24，零 skip，81.171 s | 原未插樁驗收；[收據](formal/verification.json) |
| 加觀測 normal | 24/24，零 skip；suite.json 61.13 s | 24/24，零 skip；suite.json 85.18 s | 251 bridge／run_once、252 inspect |
| 動態 gprof | 24/24，零 skip；suite.json 58.98 s | 24/24，零 skip；suite.json 86.15 s | 251 bridge、252 inspect、251 gmon |
| static-libc gprof | 24/24，零 skip；unittest 71.652 s | 24/24，零 skip；unittest 74.244 s | 251 bridge、252 inspect、251 gmon |

六個診斷 run 均 diagnostic_complete=true；252 inspect 含 startup 一次。各 run 的 [normal main](dynamic/normal-main/receipt.json)、[normal candidate](dynamic/normal-candidate/receipt.json)、[動態 main](dynamic/gprof-main/receipt.json)、[動態 candidate](dynamic/gprof-candidate/receipt.json)、[static main](static/gprof-main/receipt.json)、[static candidate](static/gprof-candidate/receipt.json) 綁定固定 source、binary、sidecar、flags 與結果。static suite.json 為72.44／74.35秒，與 unittest footer 的計時包覆不同；所有診斷 wall 都含觀測，不能取代正式2.127。

## 已有證據支持到哪裡

效能問題分成兩個階段。原 e64 的大量整份快照 SHA 已有前段 profile 與 A/D 修正證據；本輪固定68已含那些修正及 B/default owned replay。現在 static-libc profile 顯示，**資料搬移、比較與清零是主要已列樣本類別**，其中 memcmp 的額外樣本最大；尚無 caller／bytes 證據可精確分配到某個 H／K／borrowed pin site。

| gprof 原 implementation 符號，self samples 秒 | main static | candidate static |
| --- | ---: | ---: |
| __memmove_avx512_unaligned_erms | 19.24 | 21.44 |
| __memcmp_evex_movbe | 0.60 | 6.42 |
| __memset_avx512_unaligned_erms | 0.05 | 1.10 |
| 已列全部 self 樣本 | 20.80 | 30.70 |

candidate 前三者28.96／30.70＝94.33%。這是 static link 樣本分布，不能把 +5.82 秒 memcmp 樣本直接換算成原動態81.171秒中的成本。main 的搬移樣本也很高，因此不能把所有 copy 成本視為新回歸。

nm 證明 memcpy／memmove AVX512 variants 在 candidate 同為0x4f2c00；gprof 選的是共用 implementation 名稱，不等於 source 全呼叫 memmove。libc 沒有 mcount，calls 空白／null 必須保留，無完整 caller arcs，也無 bytes 計數。static ELF 實際無 PT_INTERP／DT_NEEDED，各有43個指定 libc 符號，見 [link 驗證](identity/static/static-link-verification.json)。

動態 gprof 只有0.08／0.33秒主 executable self 樣本，單靠它無法解釋 child CPU；static variant 補進 libc text 後才看到上述分布。`-static`／`-pg` 都會改變成本，不能拿 static main/candidate 的 wall 比宣稱達標。

## Python 與 child process 範圍

加觀測 normal 的251個 child process，user CPU為12.727963／23.014989秒，system為16.503916／21.141180秒；這是**整個 child 生命週期**，包含 exec 前準備、startup、libc、C 應用及 system，不能稱純C引擎。原 `_bridge.run_once` 沒有preexec_fn；尚無syscall追蹤可分配exec前成本。

252次 fingerprint 區間扣除同scope已記錄的proc掃描後，Python CPU殘餘為2.583607／8.079550秒；inspect整體殘餘2.897139／8.632001秒（包含fingerprint，不能相加）。扣法為 own.after probe 加所有descendant before/after，排除own.before；仍含其餘觀測成本，不能當未插樁純freshness。原檔案集合52／192不是時間估計，原scanner／freshness／sidecar未被快取或放寬。[逐事件算式](analysis/normal-event-scoped-known-probe.csv)、[24項child CPU](analysis/normal-case-child-cpu.csv)、[精確摘要](analysis/normal-analysis.json) 可核對；兩份normal原events／children也完整收錄。

另須更正採樣時鐘術語：本機libc __profil使用ITIMER_PROF，計process及system代其執行時間，所以gprof samples**不是pure user CPU**；它仍沒有kernel stack／symbols，無法精確拆出page fault／syscall。主樣本20.80秒高於main child user14.844687秒不應被誤算成另一種純CPU分攤。[本機唯讀反組譯／header](analysis/profil-timer-readonly.txt)、[身份](analysis/profil-timer-inputs.json) 留證。

## 原始前20與完整graph

| 版本 | self前20 | inclusive前20 | calls前20 | 原full／callgraph |
| --- | --- | --- | --- | --- |
| 動態main | [self](dynamic/gprof-main/gprof-report/top20-self_seconds.csv) | [inclusive](dynamic/gprof-main/gprof-report/top20-inclusive_seconds.csv) | [calls](dynamic/gprof-main/gprof-report/top20-calls.csv) | [full](dynamic/gprof-main/gprof-report/full.txt)／[graph](dynamic/gprof-main/gprof-report/callgraph.txt) |
| 動態candidate | [self](dynamic/gprof-candidate/gprof-report/top20-self_seconds.csv) | [inclusive](dynamic/gprof-candidate/gprof-report/top20-inclusive_seconds.csv) | [calls](dynamic/gprof-candidate/gprof-report/top20-calls.csv) | [full](dynamic/gprof-candidate/gprof-report/full.txt)／[graph](dynamic/gprof-candidate/gprof-report/callgraph.txt) |
| static main | [self](static/gprof-main/gprof-report/top20-self_seconds.csv) | [inclusive](static/gprof-main/gprof-report/top20-inclusive_seconds.csv) | [calls](static/gprof-main/gprof-report/top20-calls.csv) | [full](static/gprof-main/gprof-report/full.txt)／[graph](static/gprof-main/gprof-report/callgraph.txt) |
| static candidate | [self](static/gprof-candidate/gprof-report/top20-self_seconds.csv) | [inclusive](static/gprof-candidate/gprof-report/top20-inclusive_seconds.csv) | [calls](static/gprof-candidate/gprof-report/top20-calls.csv) | [full](static/gprof-candidate/gprof-report/full.txt)／[graph](static/gprof-candidate/gprof-report/callgraph.txt) |

O2 inline／cycle／PC歸屬限制保留：動態provider_hash原graph仍呈17077+2744自遞迴，但source沒有該遞迴；不能把原符號calls當精確source API呼叫量或用inclusive作payload大小加權分攤。SHA已不是本輪static樣本主因，不代表可刪任何exact SHA或tamper保護。

## 證據清單與未驗項

[每個原run檔案hash](identity/run-files-manifest.json)涵蓋六個完成run的4,118個原檔；[1,004份gmon完整hash](identity/measured-gmon-manifest.json)合計508,913,252 bytes，全部原gmon實際SHA已複核，留在外部而不重複放進Git。每份gprof inputs仍綁定對應binary與child。六個[實際binary身份](identity/binaries-retained-externally.json)保留，binary/object與整份來源快照不公開；四份來源檔案hash manifest、原sidecar／build receipt、兩份[工具身份](identity/tool-identities.json)提供身份鏈。工具source不在此精簡公開包，這不是可獨立執行的完整工具鏈；原凍結工具與原件仍保留外部。

最小下一修方向是先定位大memcmp的真正site／calls／bytes，再評估封閉owned caller內的重複檢查。H generic publish中的equal callback可竄改資料；不能直接刪除其後K檢查。只讀owned validator／固定pure equality／原K最後檢查的候選正另行審查，尚未採用、未實跑，public tamper／decoy、provider/OOM錯誤與原斷言不放寬。本輪沒有新修正分支或產品SHA，不能宣稱已達≤2或完成全量驗收。

環境：Debian13、Linux6.18.55 x86_64、GCC14.2.0、Python3.12.14、GNU gprof2.44、stack16MiB。沿用同環境既有版本收據為Node24.19.0／Chrome155.0.8059.84；本診斷沒有執行Node或Chrome。最早v1曾因kernel缺/proc task children介面導致observer失敗，但原suite仍24/24；v2改純Python stat/ppid掃描，原v1保留，沒有把工具故障算成產品紅。
