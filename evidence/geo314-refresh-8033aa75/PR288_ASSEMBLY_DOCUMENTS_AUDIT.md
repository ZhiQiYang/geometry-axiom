# #288 assembly／documents 原收據唯讀對抗審

2026-10-23 UTC。只讀原 JSON／小 stdout，不重跑已綠項、不重新分類 skip 或放寬判準。審查 execution SHA 為 `13d02c1db7022145a52ee063286a558e595eb212`；日後來源變動是否重跑由新閉包另定，本檔不改標舊實跑。

| 原 job | 原 receipt | 真 build／browser step rc | 原 job exit | 秒數／原 CI 限 | 原 scope |
| --- | --- | --- | ---: | --- | --- |
| assembly | `/tmp/g288s7/workflow/assembly/receipt.json` | `steps/1/result=0`、`steps/3/result=0`；watchdog 均 false | 0 | 184.69214885101246 秒／15 分；over_ci_timeout=false | partial、filters=[GEOMETRY_ASSEMBLY_ONLY]；150 passed assertions、0 failed、skip=[]；P77=134、P82=16；golden not compared (partial mode) |
| documents | `/tmp/g288s7/workflow/documents/receipt.json` | `steps/1/result=0`、`steps/3/result=0`；watchdog 均 false | 0 | 63.94284767500358 秒／10 分；over_ci_timeout=false | 原 DOCUMENTS_RESULT 為47 passedAssertions／0 failedAssertions，viewport=[1400,900,390,844]；coverage 是真 pointer／keyboard navigation 加 synthetic file fixtures、PDF／safe Markdown checks |

兩份原 receipt 的 status 均為「完成」，checkout_before／after 均為 `/tmp/g288f-13d02c1d`、同 F13、status 空；均有原 ended。原命令、版本、暫存目錄、獨立埠與 stdout／stderr 保存於各原 job 目錄。receipt SHA256：

- assembly：`6dbbfc002f0d2b5623be16d7519da38493aff16a4be2b91b8e3ce58c086847d9`。
- documents：`9d97dae4e6e710e68c274685c764e7bea4b2a26fda0609b407dea18852ba2219`。

assembly 原 `03.stdout:193` 是唯一 CDP_RESULT，completed=true、uncaughtBrowserExceptions=0、firstNetworkFailure=null。firstTransportFailure **不是 null**：原 `03.stdout:74` 明列 `assembly-confirm 13` 的 `Injected lost success response`，context 是 `=== P77 review #33 #35 #36 #37 ===`。鄰近原具名斷言包括「遺失成功回覆由精確回執恢復而非重送確認 ✓」「回執也失敗時保留草稿並鎖住編輯 ✓」「未知结果只用鍵盤返回重連再開不盲送也不刪草稿 ✓」。這是原測項刻意注入且其恢復斷言通過，不能抹除 transport 記錄，也不能只看到 FAILURE 字樣就判 job 紅。原 footer 自己明列 assertion counts 不是 end-to-end scenario counts。

documents 原 `03.stdout:49` 是 DOCUMENTS_RESULT；它**沒有 schema、scope 或 completed 欄位**，不能補造。原 literal PASS 包含不執行不可信 Markdown、不遠端載圖／請求、late read 不覆寫新檔、PDF 真翻頁／mobile refit、場景／草稿／undo 保持、不產生 uncaught exception 或 failed asset request。只保原47/0與 coverage，不外推完整 canvas 或整套視覺 golden。

未發現這兩個 F13 原 job 被 outer 0 掩蓋、超正式 CI 限、partial 被誤稱 full、原缺欄被補造或刻意負控被抹除的證據。這是原證據 scope 複核，不產生新的 gate；F13 後的 runtime JS 變更不能借本檔冒稱在新 F 重跑。
