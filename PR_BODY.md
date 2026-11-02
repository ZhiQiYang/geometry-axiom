把原完整 canvas 拆成 legacy／extensions 真執行單位；保留原 assertions、golden、等待條件與每 job 35 分鐘上限，嚴核原件同 run／attempt、來源與精確聯集。

完整 current head：**e5b0bc23b04e872a68b066bd5b51d57e2c104943**。base `feat/r06-bay-repeat` @ `7a876ed6a772f3bb5fff0f9644421d6ec6e6cea4`，依賴 #363 與 #344；**Draft／未達合併條件**。最新 main 已合 #354 到 e02057b4c725d6f03ae52c3bc30776bf9442b0cf；本候選尚未採它，不能把本輪綠燈移標新合流來源。只用一般 merge／快轉推送，Codex不合main。

| 唯一 current-state gate | 真結果、execution 與限制 |
|---|---|
| 正式 CI | **已實跑且原件全核**：[41424542378](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41424542378)，12/12 success、attempt1；API head D，真execution ea163769f8f570ac06b56906ceb8cdf7dc220a1a與D同tree。10ZIP／654members／12logs、原聚合器逐byte復驗0，獨立peer10669 checks PASS；兩種SHA不混用 |
| 原完整 canvas 參照 | **已實跑** D，`python -B tests/release_gate.py --url http://127.0.0.1:18847/ --output <fresh-out>/gate --timeout 2100 -- node geometry-web/cdp_test.js`；10:01:47.502878–10:31:38.930845Z，exit0，2317過／0敗／0skip，86段golden逐段全等，原P38預期例外1；737來源與3native/sidecars前後一致；無partial/shard/modifier |
| 三native片＋coverage | **已實跑／原件復驗0**：235/235套、5460 counted／5459 pass／1原允許GDI skip；原coverage真0/1/0。原`python -B tests/native_shard_receipts.py --input <originals> --parts 3 --output <new>` 在精確CI execution復驗0，summary bytes等官方 |
| 新預期數量 | 原full-only producer在S1=9829461187ff5fb5bfeb87ca0bc0a4b5a00645a2真執行235套，2075.059秒、**原exit1保留**：舊集合Counter及4個稀疏checkout缺原Git ZIP案例。只取原CLI生成資料，新增19/12兩row、原233列不變。補3份原Git ZIP後原Node aggregate獨立756/0/0、exit0；沒有拼接舊report或把1改0。D本地原coverage0/1/0、新suite19/12皆0；D正式三片、coverage及原ZIP逐byte核收均已通過，才接受本候選expected資料；原census exit1沒有改判 |
| 真UI harness撤回／恢復 | **已實跑0/1/0**：D／local M aec3ea1bdcf46f2416dfa7cb79d28221673c315a／D，唯一S2 predicate多false&&9bytes；原`canvas_evidence.py run --shard legacy`每相2100不變。482.395251／484.041772／480.055233秒；F/R898pass0fail0skip／62golden matched；M897pass2fail0skip＝唯一S2 false＋原golden section1 14→13後果。Python原拒CANVAS_PROCESS_FAILED:1，同M真journal另由原Node具名CANVAS_ASSERTION_FAILED: S2 結構:拒絕1；peer9662 checks PASS。M未推，所有local run_id0，不冒GHA |
| 真artifact負控制 | **已實跑**原CLI對6個私有真原件拷貝各exit1：缺片／錯attempt／stdout bytes改動／duplicate manifest shard／錯manifest.plan_sha256／偽assertion summary；原件恢復0且summary逐byte等官方。duplicate/plan只改manifest欄位，不外推整ZIP重複或實際golden payload破壞。舊S1不完整原件拒CANVAS_PROCESS_FAILED、D拒舊source CANVAS_WRONG_HEAD也保留；非真UI反證替代 |
| caller窄修 | 已採8e3c80bc78953626878e00a0bcfc211e88c65bbf：只用Node原os.tmpdir建立geometry-tests截圖父目錄，&&保準備失敗非零；FS0/1/0及獨立peer PASS。D本輪extensions CI已success，不改JS/assert/golden/wait/timeout |
| 帳本 | 原S=76d311cf1507708bc63bba2ab6e4f0c3f68cabb0 manual41397499686，10/10綠、9ZIP hash、原verify0，123=114killed／1crashed／5equivalent／3retired，7cache負控strict1。正式ledger b39b1f20fa267628ee656cf40464af7812ae70d5a19aef52e3a53054eb4599fe採S1再到D；185原judge來源閉包未變、D原--check0，120execution仍S，不重標D或執行下載ELF |
| 架構 | S1原三CLI0／205+18，607來源input逐LF hash與D全等，335owned+272excluded／803edges；四canonical產物已採D，execution仍S1、政策985/55不變。不是宣稱在D重新執行三條 |
| 已保留歷史紅件 | 首輪S1 CI7綠5紅：legacy898/62成功，extensions929過但P76截圖ENOENT fatal1、native兩新expected缺列及complete拒絕；第一個count外層2100 timeout124／child-15。後來維護步驟外部預算修正6300只屬原full-only writer排程，實際2075仍小於2100；正式CI/完整canvas35min從未放寬 |
| 尚未完成 | **最新main／上游同源合流未跑**：此D不含main#354的新K1產品，#363及#344仍為上游；之後僅一般merge收斂，依實際改動跑受影響正式項。D獨立驗證全齊不等於最新main整合通過，維持draft。#355 UI15不在本PR驗收內 |

[固定E完整原件與目前進度](https://github.com/ZhiQiYang/geometry-axiom/tree/48da3fa2b054ca74da2e13277db1522a6e6133ce/evidence/cloud-resume-20261102/canvas-sharding)，含完整參照原流、兩輪count原件、各次環境紅件、具名反證準備與source/expected/canonical身份。先前S1與D execution分開，raw不正規化，不重跑有效原樣本。完整聯集仍是legacy62／898＋extensions24／1419＝86／2317，含零assertion鍵與P83→P86原順序；幾何產品碼、公理／正典閱讀器／決策佇列未改。


真harness原件：[307檔封包與SHA256](https://github.com/ZhiQiYang/geometry-axiom/tree/48da3fa2b054ca74da2e13277db1522a6e6133ce/evidence/cloud-resume-20261102/canvas-sharding/harness-control-publication)，gzip900623B／d77cc507e750c620ba2bbba2e39519f1e83a20f07f6fa38e2514a1c016b3a446；[獨立peer](https://github.com/ZhiQiYang/geometry-axiom/blob/48da3fa2b054ca74da2e13277db1522a6e6133ce/evidence/cloud-resume-20261102/canvas-sharding/harness-control-publication/PEER_FINAL_HARNESS_REVIEW.json)。F/M/R各737來源、3native/sidecar及golden前後一致；M只有cdp差，F/R內容相同。原P38預期例外每相1。

環境紅件不改判：F01原ENOSPC只捕捉0斷言，實際完整計數unknown；F02真completed:false/0assert、SingletonSocket路徑過長。均無mutation credit；修正僅短且獨立SHM TMP/profile、原Chrome/CDP smoke與輸出依賴，未改產品斷言／時限。peer只證目前15個記錄PID沒有活程序，未追認歷史所有後代。保留原raw，沒有將環境錯誤當產品紅或把恢復綠覆寫舊紅。
