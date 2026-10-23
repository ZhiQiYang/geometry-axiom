# #318 閱讀 A：來源實作中，動態驗收待排程

依 issue 留言 6357744513 第 3 版及 2026-10-23 核可閱讀 A，boundary 固定段在定位外輪廓邊端點可有正長度的部分角材接觸；仍拒絕零角材接觸、裸露可放下料寬的 RC 面與借用此款的其他角色／延伸段。

已落核可 SSOT 四處差異、oracle 建構／C8 的獨立重算，以及原生 W／span／between／兩條重驗 caller；H 只交付來源事實與報錯。新測試保精確定位、真 RC 跨度、FEATURE 回傳幾何、具名來源與碰撞守門；目前沒有動態綠燈，不宣稱完成驗收。

| 項目 | 唯一 current state |
|---|---|
| 目前來源／evidence head | `c264f4eea40493133e3d3409dd834d68c861e8d5` |
| 閱讀 A 第一批產品 | `41cf5594011d9d13f401319ccf676c741263dbcc` |
| native 第一批／collector 補漏 | `0df78e9f12fad311279c2a458a1cfecf1583b1c2`／`59f42f7d64f09b555aaf6bb47872cdb961b827a8` |
| 普通合入前棒 | `15a735951a36b6fe52e0291152f335139e6921ad`，內含 #314／#323 |
| SSOT 授權範圍 | D11 一句、I19 例外三、R6(d)(e)；其他公理與決策佇列不改 |
| AST／JSON／hash／錨點／diff 靜態核 | exit 0；不是幾何／編譯／測試結果 |
| 原生 W／span／between／R6(e) | 已落來源；5 方法、9 真來源撤回控制待執行 |
| 原生真 CLI place/loadfile/rebuild | 未跑；已放次序風險見下及 QUESTIONS.md |
| canonical 同步與三閱讀器裁判 | 未跑 |
| oracle 新 13 方法、builder/checker 0/1/0 | 已備來源；未跑 |
| 舊 selftest 與 expected 遷移 | 當前正例／歷史負控分開；528／1056 拒絕清單只移 I19-only，其他類別值不改；尚未跑 |
| 當前 golden 非空核心限制見證 | 待小型觀察及逐欄遷移；不能放寬非空／矩形綁定／id 非 index 斷言 |
| 矩形逐毫米／凹角 579／528+1056 全掃 | 未跑；固定身份正向 coverage 已落，quick/full 不准依已見房間過濾 |
| 全域突變 | M140–M148 已登記，全部 unrun；不冒 killed |
| 架構原裁判／衍生收據 | 未跑／待共同最終來源刷新 |
| 完整帳本 | 子代理不產；主代理在共同最終 SHA 整份重產一次 |
| 本輪允許 skip | 無宣告；未跑不算通過 |

證據位於 `evidence/issue318-reading-a-20261023/`。同儕靜審已獨立核對授權條文與凍結 528／1056 身份；又抓出 `reference_check_all()` 原全寬漏線，已補入 W 共同判官，動態反證仍待排程。主代理 #288 P88 獨占 heavy 時，本分支未並跑編譯、Chrome、bench、oracle 或 scan。

最不確定處是最簡 13 mm 兩支同向 boundary 的實際初放／重建順序。靜讀看到重建先清 placed、依原 order 評估、接觸來源略過未放者；目前未找到合法批次豁免。這不是已實測死結，也不以人工 placed=true 型別測例冒稱 CLI 成功。若真無合法路徑，需釐清核可閱讀 A 如何在保留「已放」與鎖定依賴語意下表示；不擅改公理，完整疑點見 `QUESTIONS.md`。

不 force push、不合併 PR。此 head 仍非給末棒的 complete source baton；#288 未進 main，改 base 由主代理處理。
