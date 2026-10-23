# #314 正式雲端驗收

固定受驗 F：`cc67e2518f6ab331b5ab9fdbcd5bd6334134377f`。七項原測試、原完整 ASM 與三條架構裁判均通過。後續 E 只保存證據，不冒稱 E 受驗。

| 原 workflow job | 原測試退出 | 原秒數 | 原 CI 分鐘 | 超時 | 原發布退出 |
|---|---:|---:|---:|---|---:|
| native | 0 | 1706.287485 | 35 | False | 0 |
| canvas | 0 | 1694.863328 | 35 | False | 0 |
| assembly | 0 | 184.638563 | 15 | False | 1 |
| documents | 0 | 61.946722 | 10 | False | 0 |
| grid | 0 | 441.984781 | 15 | False | 0 |
| space | 0 | 204.675091 | 15 | False | 0 |
| timber | 0 | 121.760853 | 20 | False | 0 |

原 native：227 suites，5268 計數＝5267 pass、0 fail、1 允許的 Windows GDI skip；`mutation:check` 原退出0。每項來源前後為乾淨 F。

原完整 ASM 工具與 outer 均0：baseline／restored pass，三 mutants 具名正常斷言 killed，六 controls 符合原判準；原 timeout120不變。F 三架構原退出0／0／0，inner／outer均0。

canvas 原2267／0、full／golden matched；P73 原行1830「空空間不畫假邊界，提供加入成員入口」與1855「整輪沒有未處理瀏覽器例外」均通過；後者僅指P73模組。canvas整個原footer仍有P38預期注入的uncaughtBrowserExceptions=1，行561／563／564保留，不改稱整個canvas零例外。P52-5原行773同步等待240ms，只是正常job紀錄，不冒作獨立main／fix專項。

assembly150／0、grid356／0均原partial／golden not compared；documents47／0，原footer未有scope/completed欄，不補造。space242／0為full-space-suite，原omitted兩timber組；timber79／0為partial，原omitted五space組。完整原groups、範圍與行號見BROWSER_SCOPE_FACTS.json，沒有擴稱未執行範圍。

原assembly發布退出1：原publisher的assembly-*封包守門撞到既有assembly-final專項封包，因此原seven wrapper及outer均退出1。其餘六個原發布退出0。整輪完成後只用原publisher改唯一label為assembly-workflow補發布，實際退出0、遠端同且乾淨；原測試沒有重跑、原receipt／退出碼沒有改寫。PUBLICATION_REPAIR.json與完整原stderr／命令另存，不能把補發布0冒作原wrapper0。

新S不帶IDs整份原mutate.py與strict --check均0，100 records＝91 killed＋5 equivalent＋M20 crashed＋3 retired，97 execution全真新S；M20不算斷言killed。舊容量失敗2、M110 invalid、ASM anchor collector1及舊ASM外層1均保留。Linux四檔真來源L、F再跑三裁判；各來源角色詳SOURCE_HANDOFF.json，不將S／L／E改標F。

FORMAL_METRICS.json及本檔只整理原收據，不是新裁判。原工具未落盤的core內層streams不補造；Windows GDI／MSVC未動態驗證；超起始容量facts／realloc／OOM、確認後段逐分支故障、混合parameter-package Q3與完整P177全域動態計數不由靜態審查外推。本分支未與#323或combined補丁疊合驗收。沒有合併或force push，公理層與決策佇列未改。
