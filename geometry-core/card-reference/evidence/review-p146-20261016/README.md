# P-146：可獨立處理的審查修正

雲端 native,非正式 WSL 收據。本輪依 #253 的 P-146，不提前處理須等 #256／#193 合併的 B1／B2／S1。
產品及測試來源為 `417ea06df4a7f63d9b92f5b9255cbc1514512622`；`95475492` 只修突變範圍及裁判，產品／測試碼不變。最終交付 head 與實跑完整 native 的來源分別列在 PR 留言及 `summary.json`，不把之後的證據提交冒稱成已跑過的來源。

## S3 與結構診斷

拒絕 helper 只在 `preview.violations[].message` 中核對原因；CR08／CR22／CR26／CR28／CR32 另明確檢查網格、卡片、欄位 id。
新增 `P146_ERROR_FIELDS_ONLY`，從真正的非法原生預覽出發，把標記放在 after 資料，確認它不能充當錯誤訊息。重新引入整包 JSON 比對後，該方法必須轉紅。
SAME_CARD 拒絕逐軸卡片 id，COMPLETE_MAPPING 指出缺少完整兩欄；兩類訊息分開，grid_card_read／grid_card_mark 的錯誤指名網格 id。

`before.stderr` 是新測試對未修產品的實跑：34 方法、2 failures（CR07／CR11）、0 errors／skips；`after.stderr` 是修正後 34 方法全綠。兩者是修前／修後控制，沒有當成突變 killed。

## 真突變

最終依 `mutation-delivery-index.json` 採認 49 筆實際轉紅／還原重編回綠證據。`mutations/report.json` 首輪與 `mutations-retake/report.json` 皆先跑完整 34 方法綠基準。
首輪 M11-undo 誤改共用 restore，確認時就破壞映射，失敗落在 C 探針前提 exit 3；雖然舊裁判當時記 killed，最終明確排除此筆。修正只破壞 Undo 呼叫點後，重跑已在 `CANDIDATE_LIFECYCLE one undo` 的正式 dump 比對直接轉紅，還原重編綠。
新裁判排除 C 探針非語意失敗碼（setup／異常結束不算 killed）；索引重查所有原始 stderr、逐筆 patch、產品／測試 SHA，保留未變的 48 筆，再採用新 M11-undo，共 50 次嘗試、49 筆有效證據。兩個 epoch 原始報告都保留，沒有改寫首敗或把排除筆算進成功數。
其中 48 筆修改原生產品碼，1 筆是重新引入整包 JSON 比對的測試 helper 負對照，不能把它冒稱成原生產品碼突變。
包含原有 44 筆及 5 筆診斷退化：整包 JSON 誤判、使用處漏欄位路徑、SAME_CARD／COMPLETE_MAPPING／MODE_SCOPE 缺少網格身分。
編譯失敗、啟動失敗、timeout、error、skip 不算 killed。

| 改寫項 | 破壞的一般邏輯 |
| --- | --- |
| M07 | 候選失敗仍洩漏整個候選到正式 World，不再指定第一個整卡網格。 |
| M11-undo | 對所有相同網格身分的整卡快照，故意不還原 v 欄位映射；不判斷特定欄位值。expiry／revalidation 原已是一般邏輯。 |
| M13-unused | 錯誤省略沒有配置引用的網格定義，不判斷 fixture 網格 id。 |
| M18-closure | 錯誤只保留整卡直接指向的卡片，漏掉傳遞依賴，不判斷 fixture 卡片 id。其他 M18 仍破壞來源保存或能力邏輯。 |
| M20 | 錯誤讓所有整卡來源略過 stagger 驗證，不判斷欄位 id／值。 |

另一套 `official/` 是本分支官方 50 筆帳本，並非上述 49 筆：隔離結果檔分 ID 執行、合併後官方 `--check` exit 0，42 killed／1 crashed／4 equivalent／3 retired；0 survived／stale／blocked／invalid。crashed M20 為同夾具連三次 SIGSEGV，沒有改列 killed。
這不是尚未合併 #193 的新 59 筆帳本；上游接入後須按整合來源另核。

## 當步取值與記憶體

`P146_CARD_DIRECT_REBUILT_CURRENT_VALUE` 正式驗 `[delete P, put P(a=99,b=47), 轉直接值]` 的捕捉及正式結果為 [99,47]；`P146_CARD_DIRECT_MISSING_SOURCE` 正式驗缺來源時拒絕且錯誤含三種身分。
NATIVE-CONTRACT 已改正成「該步存在就讀當下值，包括已重建；該步不存在或來源非法才拒絕」。逐欄舊快取缺陷沒有在本支越界改動。

`memory-committed/report.json` 由真核心型別編譯執行，並以同一份 ParameterState 宣告扣除捕捉成員對照。
本基底 Linux x86-64／gcc 14.2 ABI：GridCardCapture=40 bytes，256 格為 10,240 bytes，count=8 bytes，每份 World 固定增加 10,248 bytes；Undo／Redo 各 32 槽，共增加 655,872 bytes，其他快照另計。
上限對齊 `ENG_OPERATION_MAX=256`，每個操作最多一筆 direct capture，包內不允許解除。清零能移除歷史內容，不能消除固定配置空間；協定與 PR 正文均明列此成本。

## 原始證據與未驗範圍

`raw-evidence.zip` 內含命令、編譯／測試輸出、來源／裁判／binary SHA-256、官方分片與完整 native 逐 suite logs；沒有執行檔。`MANIFEST.json` 列每個檔案的 bytes／SHA-256，ZIP 外另附 SHA-256。
完整 native 的命令、受測 head、工作樹狀態、計數與 exit 以 `native/receipt.json`、`native/stdout.log` 及外層 `summary.json` 為準；expected 只因本輪實跑將整卡 31→34，其餘數量不改。
`native-sandbox/` 是本輪先前未帶網路權限的失敗控制：HTTP suite 出現 PermissionError／EPERM，Node 測試群組持續未結束；只對該 aggregate 自己的 Node process group 送 SIGTERM，記錄在 network-termination.json。該次 exit 1 及所有輸出保留，不當成產品失敗或最終通過；其暫存 expected 僅作失敗原件，未套用為版本化測試門檻。之後在允許本機 HTTP 的網路權限下重跑完整 native，沒有改產品或延長等待。

B1 等 #256 合併後的版本防線與註解；B2／S1 等 #193 依 P-141／P-142 合併後的共用引用守門、拒絕訊息及改綁對照。之後依序一般 merge main，並重跑逐欄重建得到 99 的具名案例。
CR18 啟用身分帳／M12、CR24／M23 UI、正式 WSL 七項及 aggregate 列出的獨立 owner／browser 驗證，均未在本輪宣稱通過。

請 Claude 核對；本記錄不自行宣告可合併或驗收通過。
