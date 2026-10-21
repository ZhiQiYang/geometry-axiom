S3 全量帳本與 L3 發布證據。

帳本真實來源 S3 `19401ca5448e162ee6140fed37b64b83b31ddec8`，由候選分支 `codex/geo261-host-authority-anchor-fix-20261021` 的公開提交建立全新 detached worktree。準備時候選 checkout 為 `/workspace/geo261-host-authority-anchor-fix`；共享主分支之後正常 FF 到同一 S3。L3 `6589248c9a94bdf0460d8f84dd1610e51048188b` 的唯一父提交為 S3，只變更 `tests/mutants_results.json`。75 筆 execution.head 保留真正 S3，沒有重標為 L3 重跑。

`python3 -B -u tests/mutate.py`、`python3 -B tests/mutate.py --check`、`python3 -B tests/mutate.py --check --killers` 三階段均真碼 0；supervisor finally、父 wait、互動工具最終回覆、必要 validator 也為 0。當輪開始 `2026-10-21T04:54:14.467562+00:00`，完成 `2026-10-21T05:39:15.019258+00:00`。78 筆為 70 killed、僅 M20 crashed、4 equivalent、3 retired；逐 ID 與 S3 原帳本一致。M20 偵測到崩潰，不能稱斷言殺死。

當輪原 JSON 5,170,289 bytes，SHA256 `52aa08ac9e0c88f96b81d35f985b7fadfbb746086ec8b99d7ae10fd3043d3178`。全部 57 core 與 18 bridge 均實跑；core baseline 165，bridge baseline/restored 各 27 方法。363 份來源/oracle原件、184 個 closure 檔與 165 場景在開始前綁定 Git S3；包含本次唯一變更的 host-authority 測試。CC/PYTHONOPTIMIZE absent、預設 cc、16 MiB stack、core 0，使用空新 cache。沒有因 test-only 或 oracle 相同跳過 core。

原 supervisor/launcher/validator/importer bytes 不變，prepare 只改精確單 test 差分守門、備份與 S3 標籤。四份架構metadata及611輸入與A2/L2/S3相同，sourceBaseHead仍為原S2，不冒稱S3重產架構。匯入器的 `sourceA2`／`ledgerL2` 與舊備註是歷史命名；其數值實際為上述 S3／L3，`S3-L3實際來源綁定.json` 只附加說明；真正來源以原 Git blob/parent/only-file/push/remote 收據核對，不能把舊 note 當成執行來源。

本輪所有執行中與最後觀察保留原貌：初始 exit null 不是最終碼，最後真碼看 session-observation-final 與 durable wait。S3準備時曾只讀誤找 publication.json，改讀原 receipt.json；原 cat 單行工具輸出與真碼轉錄仍收錄，未另 redirect stdout/stderr 或保存 raw transport，不算產品紅。若另有接受器或傳輸事件，以當輪原件逐項為準，不把A2的歷史03:25斷線套到S3。

L3發布保存原JSON逐bytes、default check 0、普通push 0及remote exact。工具回覆轉錄不冒稱raw transport或重新wait。本包不重跑ledger/check/發布，也不宣稱L3其他驗收完成。工具歷史自測保留原日期，非S3當輪重做；M36歷史7143與136探針不冒稱本輪重做，當輪核心基線依165場景原收據。

核心raw限制：既有工具沒有另存每個core子程序原stdout/stderr，只有結構化oracle result與其hash，頂層mutate.stdout不能補足。bridge原raw與sidecar按正式validator清單收錄。後補獨審的實際範圍與任何首次誤判依原件，不能由封包推造未做檢查。

`執行原件/` 為原frozen publish全快照，保其巢狀索引與sums；`後補收據/` 收後來新增原件，不修改歷史索引。根原件清單只列原樣copy項；根SHA256SUMS精確涵蓋除自己外全部檔案，包含生成說明與nested inventories，沒有自含循環。全部0644；方法原碼以.txt保存，不新增產品工具或可執行副本。封包/獨審結束碼另置包外。
