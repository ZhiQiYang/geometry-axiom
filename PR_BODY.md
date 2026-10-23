# #318 閱讀 A：來源實作中，動態驗收待排程

依 issue 留言 6357744513 第 3 版及 2026-10-23 核可閱讀 A，boundary 固定段在定位外輪廓邊端點可有正長度的部分角材接觸；仍拒絕零角材接觸、裸露可放下料寬的 RC 面與借用此款的其他角色／延伸段。

已落核可 SSOT 四處差異、oracle 建構／C8 的獨立重算，以及原生 W／span／between／兩條重驗 caller；H 只交付來源事實與報錯。新測試保精確定位、真 RC 跨度、FEATURE 回傳幾何、具名來源與碰撞守門；正式動態驗收尚未跑；小型觀察已完成，不宣稱完成驗收。

| 項目 | 唯一 current state |
|---|---|
| 目前產品來源（含 canonical） | `ae74e51bba1efef48949c077635966273a9e8990` |
| evidence head（後續僅收據／獨立驗證工具） | `573fbfe0365055935a0e792ed30bdbc222cd38f3` |
| 閱讀 A 第一批產品 | `41cf5594011d9d13f401319ccf676c741263dbcc` |
| native 第一批／collector 補漏 | `0df78e9f12fad311279c2a458a1cfecf1583b1c2`／`59f42f7d64f09b555aaf6bb47872cdb961b827a8` |
| 普通合入前棒 | 原15a73595與最新combined `6cad1a3cb76d7bd910125a1d70ecfffdc9183813`，內含 #314／#323 與最新單行anchor維護；incoming先經獨立靜審 |
| 最新source merge產品聯集 | merge前後20559個非evidence blob＋mode逐筆相同；普通push/lsremote0、source clean；已正式交noWood接剩餘source |
| SSOT 授權範圍 | D11 一句、I19 例外三、R6(d)(e)；其他公理與決策佇列不改 |
| AST／JSON／hash／錨點／diff 靜態核 | exit 0；不是幾何／編譯／測試結果 |
| 原生 W／span／between／R6(e) | 已落來源；7 方法、10 W/caller 控制＋1 真 H collector 控制待執行 |
| 原生真 CLI place/loadfile/rebuild | 未跑；已放次序風險見下及 QUESTIONS.md |
| canonical 同步與三閱讀器裁判 | 原機械同步各次 exit0（最新固定來源1cd2fc21，含 M150）；`--check`／reader unittest 未跑，不宣稱三裁判全綠 |
| oracle 新 13 方法、builder/checker 0/1/0 | 已備來源；未跑 |
| 舊 selftest 與 expected 遷移 | 當前正例／歷史負控分開；528／1056 拒絕清單只移 I19-only，其他類別值不改；尚未跑 |
| 一次小型 oracle 觀察 | 固定乾淨2039b477，8 build，exit0、0.668秒；非正式 selftest／scan |
| 當前 golden 非空核心限制見證 | 已依觀察逐欄遷移至 FZ120 的 I22 延伸段；精確非空四元組、矩形綁定、id 非 index／舊三元組反證全保。正式 generator/selftest 與撤回0/1/0未跑 |
| 原8房64排法與params | 原 golden 後綴 bytes 完全不改；未把見證房加入 rooms |
| P182 當前精確預期 | FZ107左上Y→3667、FZ114右上Y→491；FZ114左上X保3544，因3656仍MAIN_ON_EXTENSION、3604仍碰撞。不改偏好／門檻 |
| 矩形逐毫米／凹角 579／528+1056 全掃 | 未跑；固定身份正向 coverage 已落，quick/full 不准依已見房間過濾 |
| 全域突變 | M140–M150 已登記，全部 unrun；不冒 killed |
| 架構原裁判／衍生收據 | 未跑／待共同最終來源刷新 |
| 完整帳本 | 子代理不產；主代理在共同最終 SHA 整份重產一次 |
| 本輪允許 skip | 無宣告；未跑不算通過 |

證據位於 `evidence/issue318-reading-a-20261023/`。短暫 Git auth 128 原錯誤與恢復後一般 push/ls-remote 0 收據均保存，沒有 force 或改 root/global config。同儕靜審已獨立核對授權條文與凍結 528／1056 身份；又抓出 `reference_check_all()` 原全寬漏線，已補入 W 共同判官，動態反證仍待排程。主代理 #288 P88 獨占 heavy 時，本分支只在明示允許範圍做來源編輯與正典機械生成；唯一8build小型觀察是在原診斷終態之後、取得R3獨占鎖的明示窗口完成，沒有並跑編譯、Chrome、bench或scan。真 H collector 另有含實際 bridge/current_geometry/references 鏈的已放 World 見證與 M149 精準撤回，仍未編譯，也不取代 CLI 可達性驗證。

最不確定處是最簡 13 mm 兩支同向 boundary 的實際初放／重建順序。靜讀看到重建先清 placed、依原 order 評估、接觸來源略過未放者；目前未找到合法批次豁免。這不是已實測死結，也不以人工 placed=true 型別測例冒稱 CLI 成功。若真無合法路徑，需釐清核可閱讀 A 如何在保留「已放」與鎖定依賴語意下表示；不擅改公理，完整疑點見 `QUESTIONS.md`。

不 force push、不合併 PR。共享來源已正式交末棒 noWood；其接 source 與登記 expected13，不代表本分支正式驗收已完成。#288 未進 main，改 base 由主代理處理。

來源靜讀另修正既有 I19 錯碼歸因，裸 RC 拒絕維持 V_CUT_PRIORITY（M150），保原 mapper 歸 I19；也維護前棒 #314 2args→6args 的唯一過期控制錨點，23 方法與所有斷言不改，11 錨點與同儕不可變審查原件已封存。這些沒有動態通過聲明。

小型觀察的完整argv／exit／原stream／環境／SHA與新舊golden逐欄對照於 `small-observation-2039b477/`。FZ120當前／withdrawn全部60支料與縫完全相同，只解除id3固定段I19，保id1延伸段I22；STEP20當前buildable，逐支幾何與1831/3639縫保持原值。正式小型golden source撤回工具已備，未跑、不當 killed；noWood同儕已獨立靜核此不可變來源，未見靜態blocker；全文與raw metadata收據已封。獨立golden撤回工具已補四輸入隔離/hash、末HEAD/clean、PASS marker、asserts enabled與R3非阻塞獨占鎖，仍未執行。
