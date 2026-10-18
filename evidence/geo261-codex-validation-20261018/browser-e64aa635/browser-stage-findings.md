# 六個瀏覽器 job：原始基準診斷附記

測試 SHA：`e64aa6359d600f43313ec9d7ba1112c465b6a40c`。

本附記補充固定 parser 報告的分類；原始 logs、result、footer、斷言及 golden 均未修改。提案不是已套用修正。

| job | 原始結果 | 通過／失敗斷言 | 分類與限制 |
|---|---|---:|---|
| canvas | failed；exit 1 | 1593 / 1 | 已定位測試接線根因；修正尚未實跑 |
| assembly | failed；exit 1 | 115 / 1 | 待定位（格式預期過時只是候選）；兩個子條件何者為 false 尚未知 |
| documents | passed；exit 0 | 47 / 0 | 無已見失敗；僅適用該 CI scope |
| grid | passed；exit 0 | 350 / 0 | 無已見失敗；僅適用該 CI scope |
| space | failed；exit 1 | 127 / 2 | 待根因定位：頁面 fetch signal 逾時；效能退化為候選 |
| timber | failed；exit 1 | 24 / 2 | 待根因定位：example preview 的 UI 等待逾時；效能退化為候選 |

## Canvas：第 13 題

P72B 在正式新專案 confirm 停止。產品 reference-workspace.js 的完整 dirty／clean 訊息與原 fatal 相符；測試的共用 newProject 漏接 expectNativeDialog。修法只登記本次精確確認，原非預期對話框仍 fatal，全部原斷言保留。

另以 source 獨立枚舉 17 個 check callsite：1 + 7×5 + 4 + 4 + 6 = 50。P72B 歸入 P72，故精確 golden 候選為 P72 52→102、總數 2211→2261，其他 83 段不變。2f015dfd 新增 plugin 未更新 golden，0e7c38bb 改指紋比較但不增減斷言，83727e 只把 P70 加 4。原始本輪 P72=53 是舊 52 加 P72B 第一個通過；原 footer 明列 run did not complete，尚未比較 full golden。

外部提案已完成獨立靜態二審。預定自有分支 codex/geo261-fix-canvas-dialog-census-20261018 尚未建立，沒有修正 commit SHA。修後真 COMPOSITION_ONLY、撤回兩個 JS hunk 轉紅、完整 canvas／golden 負控均未執行。

## Assembly：第 14 題待診斷

原文為 `P77 assertion failed: G07 未完成實例草稿保存第8版 false`。這是複合斷言的實際 false；本次沒有把 baseline.saved 的 bytes／format／drafts 封存。不能由版本歷史猜成已觀測 format16/17，也不能把草稿存在視為已通過。

待定位：格式預期過時只是候選，兩個 AND 子條件何者為 false 尚未知。已二審的外部診斷提案保留完整原 AND，只加 saved 診斷並在 check 前封存同一 __generationBytes 的真 gcanvas 與 JSON；提案 patch SHA-256 為 c0f135d9bcfaf21d21309b6ae9e7823d1ba6e0d08e290e8b8ae613d1af28bc31，尚未 apply／執行。

唯讀定位確認 unpack／validate 不升版，格式選擇發生於 pack；但沒有本輪真 saved raw，不能由此斷定失敗子條件。main/e64 的該測試與 project-store 同 bytes，main 未動態跑，因此不能判成已證實既有問題。正式修法、修後與突變證據尚未具備；後續未執行斷言不列通過。

## Space：頁面逾時與衍生完整性診斷

本輪 127 個通過／2 個失敗斷言、completed=false；兩個 FAIL 是 complete browser flow 的 TimeoutError，以及流程中止後 space group completeness 的診斷，不是兩個獨立產品缺陷。外層 15 分鐘 job 未逾時（work472.037秒）；原訊息是 TimeoutError: signal timed out，與 120 秒 CDP watchdog 的 CDP timeout: Runtime.evaluate 不同。

原 trace 落在 space_model_test.js:1457 的 importBytes。readProjectContext 逐個驗證模型，reference-workspace.js:1749–1750 的 /model/verify 及 :1760–1761 的 /model/space-replay 各有 30 秒 AbortSignal，是靜態因果候選。現有證據未辨識唯一失敗 endpoint，也未定位 native 熱點，不能先把它等同已證實的 SHA-256 成本。

space/server.log 有三個 serve.py:702 的 model 路由 BrokenPipe 寫回；但 serve.py:333 的 log_message 為靜音，沒有最後 HTTP path/time 可配對。space harness 也沒有 Network 事件收據，所以不能把最後 BrokenPipe 指定為本次 verify 或 replay，更不能排除先前刻意取消預覽留下的寫回。

setup2、projection-lifecycle18、projection-close14 已完成；space-height-library93/expected112 未完成，projection-placement/font-layout/space-flow/browser-health 都尚未完成。242 是全 scope 預期 census，不能填成通過。兩個完整失敗原文及 groups 保存在本附記 JSON 及 [原始結果](space/artifacts/space-results/result.json)。保留原 30秒／120秒／900秒上限，待效能量測修正後原時限重測，不放寬 timeout。

## Timber：範例預覽的 UI 等待逾時

本輪 24／2、completed=false。space_model_test.js:1118 呼叫 example，:316 透過預設 30000ms wait（:132–138）等待 resultSummary 非空且 stale=false；原 UI 收據仍是 previewing、resultSummary=null、stale=true、connection=ready。這是 harness UI 條件等待逾時，不是 120秒 CDP watchdog，也不是外層 20分鐘工作逾時（work254.365秒）。

24 個通過是 setup2 加 timber-material22；79 是原完整 scope census，不得算作已通過。另一個 FAIL 是衍生 group completeness，並非第二個獨立產品缺陷。完整原 UI JSON／stack 與未完成群組見附記 JSON 及 [原始結果](timber/artifacts/space-results/result.json)。效能退化是待量測候選，尚未證實唯一 endpoint／native 熱點；原上限全部保留，待效能根因後重測。

## 其他範圍及未驗

- documents：無已見失敗；僅適用該 CI scope。未監聽 consoleAPICalled，不能宣稱 console 無錯；只檢查 Runtime 例外、HTTP >=400 與外部請求，未監聽 Network.loadingFailed。成功 footer 沒有 schema、scope 或 completed，完整性依成功專用 footer、零失敗與正常退出判讀。
- grid：無已見失敗；僅適用該 CI scope。consoleAPICalled 僅列印 [console]，未保留類型，也沒有獨立 console.error gate。非預期例外會增加 failedAssertions；僅 full canvas 的 P38 刻意注入 fb-auto-probe，仍會計入 uncaughtBrowserExceptions，因此該欄不等於非預期例外數。
- space：待根因定位：頁面 fetch signal 逾時；效能退化為候選。原 browser-health 群組要求未捕捉例外及 console.error 都為零；另以固定群組斷言 census 核對完整性。timber 的限定範圍仍會跑 browser-health。
- timber：待根因定位：example preview 的 UI 等待逾時；效能退化為候選。原 browser-health 群組要求未捕捉例外及 console.error 都為零；另以固定群組斷言 census 核對完整性。timber 的限定範圍仍會跑 browser-health。

全量明細、實際命令、起迄／timeout／底層 exit、runtime ownership 與每個原文 hash 見 [固定報告](browser-stage-report.md) 及 [JSON](browser-stage-results.json)。本附記 JSON 另鎖上述兩檔與每 job 原 test/result hash，未從註冊數或剩餘 scope 推算通過數。

本輪未套任何修正，已套用修正分支清單為空。效能根因、修正後同源全量／六 job，以及每個修正的撤回證據均須另輪記錄；不能將不同來源的零散通過拼成整合驗收通過。
