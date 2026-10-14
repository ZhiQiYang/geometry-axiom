# K2a-A 相容／共用來源邊界（2026-10-12 臺北時間）

回覆 ChatGPT 6113090394、dot 6113125187，僅 #201。本輪 M1 已修；B1 有實跑反例、容量方案仍待裁決；B2 正式整合／七組仍阻擋。

M1 修改前：原 selectParameterPin 同意 lost P1→V 已用 P2，原 writer 在 flush 拒「不得純移除」，指定 doesNotThrow 斷言紅。修改後只在原 setGridDraft 增加六行：以舊 raw 的有限參數來源欄位逐欄核對，每個原 P1 欄位都須改為 value.inputRefs 中未 lost、不同參數卡的對應來源，才允許已有 P2 或多欄共用；不能借既有 P2 冒充刪除。沒有單拔 old.inputRefs 排除條件。

原 handler／writer 的 VM（DOM/confirm 為 fake，非 Native E2E）現在驗：拒純刪 refs／raw 不變，state/history 原子；拒未確認、選擇還原；確認 P1→P2、去重、兩欄原樣保存；Undo 還原 lost P1，Redo 還原共用 P2；真 ZIP pack/unpack 逐項比對草稿。既有同物件、同卡不同欄重取拒例保留。K2a races 9/9。三個新指定突變分別「拒共用目標」「略過 raw 對應」「跳過確認」均 baseline/build/指定 AssertionError 紅/restored 綠，無語法、setup 或 skip 冒充。

第一次完整流程的產品斷言全部過，但 default TEMP mutation binaries 與原 ledger 執行收據不同（45 stale），整體 exit 1 且拒絕更新 expected；完整失敗 log 保留。沒有改 ledger 或刪他線快取；改以獨立的空 MUTATE_CACHE 做原工具明定的 clean-checkout metadata 檢查，原 core/source/oracle closure 與內嵌完整執行收據仍符，0 stale。沒有宣稱找回原 exe 或重跑核心突變。以此明確隔離快取重跑完整流程。

完整非瀏覽器 83 suites：2642 pass／0 fail／1 允許 GDI skip，Node 677/677，expected 由 --build --update-expected 自動產生。執行期間沒有再修改產品／測試或提交；程式 head 4b0d5399668d855408efc8fdd32d18931be14e5f，只有測試流程完成後寫出的 expected 與證據另行提交。這不是正式 WSL 七組。

乾淨同一 4b0d5399 上額外跑原登記 Native browser 42 assertions、ZIP 25 assertions，共 67；before/after head/tree/status/來源 SHA 與 fresh runtime、兩個原生 session、實際 bridge PID/exe/SHA 相符。正常容量與新接納預留的 Native 刪除→Undo→Redo→真 ZIP 冷開仍成立；沒有用這些正例否定 B1 的舊包反例。完整 CDP 54f 收據是歷史來源的驗證，RW 本輪已改，不能再當最新來源完整 CDP 通過。另三 gates、候選完整 CDP／正式整合均未於本輪重跑。

B1 已獨立重現，尚未修：以精確 base 49c391f2afbcee17bb2647fce74c3c5532a01527 的真 pack/unpack，20 個 grid-binding 引用，raw 欄位 ≤4096 字元，envelope 131071 bytes、draft 130954 bytes，寫出 geometry-canvas/13、grid-editor-draft/2 真 ZIP；base 讀回完整附件相同。現 reader 因 240-byte 預留拒絕（131194 >131072）。原 importBytes VM 亦拒，API/fetch 0 次、專案／history 不變；這是缺陷重現，不是重開通過。I68 的 reader acceptance doesNotReject 斷言仍紅，原 ZIP、script、log 皆保留於 legacy/。

需 Claude／使用者裁決的具體容量方案（未實作）：保留新草稿接納的最壞預留，讓原合法舊包以原容量範圍讀入；自動 lost/orphan 與單份升集合只獲「標記的精確增量」，raw/id/指紋不得截斷或自動改寫。保存重開要可辨識此有界形態：去除這些自動標記與升版外殼後仍須滿足原各層 byte 上限，各標記本身仍走嚴格 validator；一般 payload 不獲額外空間。此例單份 lost 額度上限為 20×12＝240 bytes，外殼／孤兒／能力增量須逐層按實際結構計算，不能只給任意全域大上限。saved 後的 /17 不應依檔名、宣稱年代或不可信布林免驗；具體辨識與新建／更新的額度隔離須一併評審。

這項選擇允許歷史草稿補標後物理大小超過現行 128 KiB，涉及工程容量政策；看板明定「屬於政策選擇的，才停下標『需 Claude 裁決』」。因此沒有自行放寬容量，也沒有單拔 reader reserve。已向使用者提出上述有界方案，尚未取得裁決。B1 的 base ZIP→head 補標→保存再開完整比對，因首步讀取仍拒而未成立。

current_geometry.c、核心帳本、公理／白話／閱讀器／BACKLOG／決策佇列均未改。mutate 無新覆蓋；本輪原 mutate.py --check 0 stale，沒有手編帳本。舊 41 個指定反例及候選 5 個的收據保留為歷史，不冒稱在新 RW 上全部重跑。

未驗／阻擋：B1 有界相容政策與遷移；B2 唯一整合 owner 回收 bundle merge-resolution／terminal 修正、#199 合併後 merge commit、凍結最終 SHA 的完整 CDP／完整非瀏覽器／正式或代理 WSL 七組。#199 查詢仍 open，沒有提前合併。沒有執行 WSL。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。GEO-219：無新入口。維持 draft/base axiom 分支；K2a-B/PF 暫停，不合併、force push、關 PR/issue。

| 驗收 | 本輪狀態與理由 |
|---|---|
| M01 | 既有並存驗收；本輪 Native/ZIP 正例過 |
| M02 | 一般真 ZIP 過；新增舊容量包邊界未過（B1） |
| M03 | 既有同 draftId 續開；本輪非瀏覽器回歸過 |
| M04 | 本輪 Native confirm/Undo、VM Undo/Redo 過 |
| M05 | 既有 pin 守門；專項 UI 本輪未重跑 |
| M06 | 本輪 Native 刪除/Undo/Redo、掃描過 |
| M07 | 本輪非瀏覽器同目標拒過 |
| M08 | 本輪非瀏覽器第 17 份拒過 |
| M09 | 本輪非瀏覽器草稿引用拒過 |
| M10 | 一般三格式/新容量預留正例過；歷史容量遷移未成立 |
| M11 | 一般 format/capability 負例過；舊 reader 範圍仍有 B1 |
| M12 | 純移除/抹旗標拒及合法共用替換過，新增 3 指定突變 |
| M13 | 原 1280/390 收據保留；本輪未重跑該 browser gate |
| M14 | 本輪 Native 同 ID 不復活過 |
| M14b | 一般 lost 冷開/同卡拒過；歷史近限包未通過首步 |
| M15 | 既有 repin 回歸；專項兩方 UI 本輪未重跑 |
