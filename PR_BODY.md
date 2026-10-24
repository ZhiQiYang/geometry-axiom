成功恢復連線時清除 `connection.error` 的過時錯誤，保留失敗狀態、編輯停用與原協定守門。這是 #320 的替代實作線 #344。本輪用一般 merge 納入整合列車產品 F2bbe；未改寫歷史，未改公理、決策、golden、時限或斷言。

唯一 current-state 矩陣：

| 項目 | 來源／原退出碼 | 現況與界線 |
|---|---|---|
| 產品 SHA | S1=`5402765c795769a77a7b249de1e3db80045a41de` | 一般雙親 merge：原 E0=`42790be40eee56efada08de84ab2acb1681df981` 與 train F=`2bbe54f19b2d19e8a816530f0c4edca950629a34`；這是來源合流，並非測試執行 |
| Evidence head | E=`c9303843208a9e4f90085075acec920a3da1e856` | 本輪 `evidence/issue344-converged-5402765c/` 只新增收據；產品仍 S1 |
| 一般 merge／來源核對 | merge 0；39 原 Git 與 48 blob proof 獨審475／0 | 無衝突；所有 F registry rows 保留，另加原 `node:connection_recovery` count9；相對 F 只有下述五個非證據路徑 |
| whitespace 診斷 | 完整 staged diff check **2**；五個來源路徑 check **0** | 原 48 個歷史 evidence 路徑警告完整保存，48 個結果 blob 全等 F；沒有刪改封存證據換取0 |
| 新 S1 Node9／完整 native | **UNRUN** | 本輪未執行 Node 或原生裁判；舊 VM 不能轉標為 S1 已跑 |
| 新 S1 完整 canvas fixed／withdrawn／restored | **UNRUN / UNRUN / UNRUN** | 原完整預設 canvas、35 分鐘、golden 與具名 P53/P61 assertions 不變；新 S1 的 app-only 撤回來源 V1 尚未建立 |
| 其餘五 browser jobs | **UNRUN** | 不借原 train 或舊 #344 SHA 的綠燈移標 |
| mutation check／完整帳本 | **UNRUN on S1** | 帳本由 root 在最後共同來源統一重產；本輪未重產、未改 execution.head。F2bbe 的既有 freshness 紅不能當成 S1 的新執行 |
| 架構三裁判／四檔 | **UNRUN on S1** | app 為 H 層來源；待最後來源判定 closure 與重產，不把 root 其他來源的四檔移標 |
| base 收斂 | 已納入 F2bbe 產品 | 未追隨其後每個純證據 head；root 若有新產品 F，先一般 merge 並按受影響閉包重驗 |
| 歷史 VM 與舊撤回來源 | S0=`7b45013da647b791acda8f5977475e4123d5f8c4` 原 Node 0/1/0；V0=`082feb0662fea32131f3f7fb8ca451679ab6421d` | 每階段9案、pass9/6/9、零skip；只屬 S0 的替身 VM。V0 單親 S0、只撤 app clear 一行，不能當成 S1 的 V1 |
| 允許 skip／合併狀態 | 無新增 skip；**未 READY** | 本輪沒有產品測試執行；完整 canvas 三相及上述正式項未完成，不合併 PR |

相對 F 的五個非證據路徑只有 `geometry-web/app.js`、`geometry-web/cdp_test.js`、`tests/run_all.py`、`tests/run_all.expected.json`、`tests/test_connection_recovery.js`。registry 是全部 F rows 加回原 count9；其他四檔逐 blob 等 E0。核心 C/H/inc、原生介面、SSOT、workflow 與 golden 逐 Git 閉包未因本次合流再改。整合列車內既有產品修正與其歷史收據全部保留。

S0 的原命令為 `node --test --test-reporter=spec tests/test_connection_recovery.js`，每階段原300秒。撤回時三個正常具名斷言為 `successful recovery kept stale error`、`completed retry kept stale error`、`loading echoed stale error`。DOM、transport 與 ReferenceWorkspace 為明示替身；它們不能代替真 Chrome、HTTP 或原生恢復測試。完整歷史原件保持在 `evidence/issue320-final-7b45013d/` 與 `evidence/issue344-real-cdp-preparation-7b45013d/`，不重寫其判決。

下一步在 root 排程允許時，從最終 S 建立唯一 app clearline 撤回的乾淨 V，保其他 tracked blobs/modes 完全相同；真正執行原 full canvas S/V/S 三相，HTTP19681/19682/19683、CDP9731/9732/9733 與獨立 TMP/profile，canvas 獨占。fixed/restored 必須完整 matched；撤回須原 P53-3、P61-10、P61-11 stale-error 正常斷言，並保全部協定、dump/source/1600 診斷。crash、timeout、前置 clean-SHA 拒絕或其他 golden 差異不能冒有效反證。此處是尚未執行計畫。

本輪原 merge argv／exit／完整 stdout、stderr／環境／SHA、三份 registry、五檔閉包、原 whitespace2 與 48 blob 保全、獨立475核對均隨新收據封存。新的 PR 留言同步檔尚無留言（已讀 handoff `5a02993f` 的 `handoff/pr-reviews/344.md`）；這不代表審查已判可合併。
