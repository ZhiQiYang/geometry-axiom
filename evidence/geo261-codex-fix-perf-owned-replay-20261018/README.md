# A/D+B：檔案重放修正與驗證證據

受測產品為 `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6`，基底為已合入 A/D 的 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，修正分支為 `codex/geo261-fix-perf-owned-replay-20261018`。兩次完整候選正控制各 **153/153**，成本三段、語義負控與原始協定比較均已完成；**正式 bridge_integrity 為 main 36.493 秒、候選 86.818 秒，2.37903159510043 倍，仍未達 ≤2 倍驗收門檻**。本報告不代表整合分支全部驗收通過。

B 讓已有外層候選的檔案載入重用其候選，逐行隔離重放、還原失敗行與 operation bytes，釋放逐行來源圖，最後保留完整驗證與發布守門。A/D 審查補強也在同一受測來源：K 的保存原件／目前 bytes 兩次 SHA 改為明確呼叫，原 memcmp 與 fallback 保留；H 測試補上精確 K provider 計數，並以延遲建構子重跑原 H client 的參數正負例；沒有新增產品 provider 守門。沒有更動公理、刪除原斷言或採用後續 default-owned-replay 提案。

## 功能結果與三段證據

| 項目 | 受測來源 | 結果 |
|---|---|---|
| 支援但未啟用的成本前控 | b05374d2 | 1 run／1 failure，6.157 秒；真 native 精確 `ASSERT:file-replay-inner-candidate-cost`。 |
| 修後八模組候選回歸 | 8ab0bdb4 | 153/153，54.155 秒。 |
| 只撤去 B opt-in 呼叫 | 341611df | 1 run／1 failure，29.786 秒；同一成本 ASSERT 轉紅。 |
| 恢復完整候選回歸 | 8ab0bdb4 | 153/153，46.628 秒；成本及所有控制的共同正控制。 |
| I8a／rollback／operation／graph／helper 語義控制 | 六個獨立控制提交 | 02–07 均保留真 native 紅燈與精確首個 ASSERT；下列界線不省略。 |
| 四態原始協定 | e9／b053／3416／8ab | 六個案例、三個非基底狀態對基底，共 **54 組 stdin／stdout／stderr 逐 byte 全等**。 |
| 六個真產品案例 | e9、8ab | 每版六案例各 exit 0，共 **12 對 stdout／stderr 逐 byte 全等**。 |

兩輪是相同 153 個方法，不能算成 306 個不同測試。八模組計數為 18、17、17、7、20、53、11、10；B 的十個 `FILE_REPLAY_JSON` 案例均 exit 0。完整 stdout 另外包含 D 的預期負控 ASSERT，不能宣稱整份 stdout 沒有 ASSERT。第一輪後段與 archive build 並行，這些功能時間不作效能比率。

02 的 valid fixture 先命中 `file-replay-i8a-refused`，是有效 I8a 拒絕語義 kill；invalid fixture 仍有 D1／D6b 拒絕，先在 `file-replay-i8a-keeps-inner-owner` 計數檢查轉紅，後續原錯誤、prefix、live／preview／scope 斷言未跑，沒有證據稱 invalid 被接受。03 真檔案 parser 入口先命中 byte rollback；04 先命中 operation bytes 還原；05 先命中逐行 graph release，並未走完後續 fallback。06、07 只證 helper body 守門，**不冒稱撤掉 production callsite 已被測出**。外層 verdict ASSERT 不重複算獨立 kill；最後恢復輪是共同正控制，並非每個控制後立即各跑一次。

六個產品案例為 lifecycle、wood-tamper、host-tamper、before-tamper、revision、cancel。其 stderr 各為 **372／456／456／456／456／442 bytes**；非空內容是應保留的 I8a preview／stale／missing-token 診斷，stdout 都空。原先 e9 單一 372-byte lifecycle 收據仍保存，不代替另外五個案例。 **372-byte 原 literal 斷言仍保留**；本次新增 e9／8ab 六案例的真 baseline 差分作證據，沒有刪除或弱化該斷言，也不宣稱已解除既有單元測試對診斷措辭的維護耦合。個別 native confirm 見證不能單獨代表 JSON dispatcher、K enum 或 B 快路徑；各自的測試、原始協定與單點控制另有原件。

詳細來源、每輪原文與分類見 [功能報告](functional/README.md)、[人工台帳](functional/manual-ledger.json)、[精確產品差異](functional/source-final.patch)、[提交清單](functional/source-commits.txt)。成本原文見 [前控](functional-before-cost-correct-command/command.stderr)、[撤回](functional-withdraw-opt-in-cost/command.stderr)、[恢復](functional-restored-candidate-regressions/command.stderr)。所有測試結果皆人工核對原輸出；collector 不自行推斷 pass 或 kill。

## 效能結果與主因

正式 main 為 `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425`。兩輪使用真 registry `--build --only py:test_bridge_integrity`，各 **24/24、零 skip／failure**；比率只取 unittest 秒數，未把建置計入。68 份共同測試／helper／fixture 的四份正式快照與固定 Git 版本逐一核對；兩版 runner 登錄與 binary scanner 的集合仍有差異，suite 內 freshness 掃描成本尚未另行拆分。

| 同輪 normal 工作 | main 中位數 | 8ab 中位數 | 倍率 |
|---|---:|---:|---:|
| resident load_scene，15 樣本 | 25.132 ms | 50.800 ms | 2.021380 |
| cold_start_dump，7 樣本 | 51.179 ms | 186.136 ms | 3.636984 |
| model-legacy，7 樣本 | 48.341 ms | 220.971 ms | 4.571126 |
| model-neutral，7 樣本 | 無 counterpart | 195.707 ms | 不計 |

normal 與 gprof 每輪皆完整 305 samples／23 groups，全部退出 0。原 e64 的主要可見瓶頸是 `geo_sha_block`，四種工作 flat self 約占 99%；A/D 消除了反覆完整候選摘要。B 進一步把 resident 的 candidate create 記錄由 250 降至 145、bind_core 2250 降至 1305、SHA 呼叫 1236 降至 711。cold 與 model 的候選建立仍各 70，不能宣稱 B 已優化 model-base。

本輪 gprof 對剩餘成本的取樣太少：cold／legacy 為 no time accumulated，resident 累計 0.04 秒、neutral 0.01 秒；無法據此指定剩餘牆鐘主因。`-O2` 的 inline／nearest-symbol 歸屬、provider_hash 假遞迴與未插樁 libc 亦限制解讀，不能把未解釋時間全部歸給 memcpy／memcmp。完整原值及限制見 [效能 v2 報告](performance/analysis-adb-8ab0bdb4/README-v2.md)、[本輪前 20 self／inclusive](performance/analysis-adb-8ab0bdb4/top20-adb-integration.md)、[三版本與 main 共 840 列](performance/analysis-adb-8ab0bdb4/top20-self-inclusive.csv)、[正式 bridge 比較](performance/analysis-adb-8ab0bdb4/bridge-registry-comparison.md)。不同歷史輪次各以自己的同輪 main 作分母，不視為交錯配對實驗。

## 無效執行、封存與環境

初次 `before-cost` 誤用不存在的方法，只有 unittest loader synthetic error，**產品方法實際未執行**；不能當成本前控。首次 archive main bridge 試跑沒有 registry sidecar，雖 exit 0，但 24 方法共 **149 次 skip 事件**，不能算成 149 個方法，也不能算 24 項通過或效能樣本。兩輪原件皆保留，正式結果另有真正執行記錄。

23 個功能 stage 的 667 個 receipt 原件已逐 bytes／SHA 核對，另經獨立審查。公開資料的 `.scene.txt`、`.raw` 只為逐 byte 資料別名，映射保留原路徑與 hash，不假裝為新執行；產品 ELF 與工具程式不在此 payload。暫存 native client 已清除，registry ELF 也未另封存，其 binary hash 為當輪原記錄，沒有冒用目前 `/tmp` 或 archive binary 重算。持久 archive binaries 則有另行真 hash 核對。

四份大型正式 bridge `before.source.json`／`after.source.json` 留在外部原證據，依既有 collector 守門不納公開 payload、不改名繞過。精確省略清單見 [publication-omissions.json](publication-omissions.json)，當輪身份及 68 份共同輸入的核對保留在原 receipt 與 [bridge-registry-verification.json](performance/analysis-adb-8ab0bdb4/bridge-registry-verification.json)。**只憑此公開 payload 不能重新計算未公開的四份全量來源清單**；公開驗證資料是已完成的逐項人工核對記錄。原 516 檔 performance 白名單在外部保留供稽核，本封裝採其中 512 檔；完整公開集合以 [inventory.json](inventory.json) 為準。

環境：Debian GNU/Linux 13.6、Linux 6.18.55 x86_64、GCC Debian 14.2.0-19、Python 3.12.14、Node v24.19.0、Google Chrome 155.0.8059.84（另有 Chromium 154.0.8037.57）；child stack 16 MiB。版本原文隨各 stage 保存，本題不啟動瀏覽器。

## 未完成項目

效能分類仍為產品退化：正式 bridge 的 2.379 倍尚未達標，剩餘成本待進一步量測。本分支未重跑整套非瀏覽器、六瀏覽器、全部 mutation、產品架構或最終 census；直接 unittest 綠燈不代表 expected 已更新或 strict 全量已完成。其他獨立修正與後續 default 提案不混入此結論，最終合流來源仍須重驗。
