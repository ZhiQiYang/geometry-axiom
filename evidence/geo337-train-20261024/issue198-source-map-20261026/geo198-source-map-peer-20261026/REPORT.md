# #198 新映射包對抗審查

審查 exit 0，無必改文字。這份新映射可作關閉候選的支援資料，不能直接宣告 issue 已完成。

A 舊查詢確誤列 hole，但 apply 在後續重驗拒絕，dump 不變；並未成功提交錯孔。B 舊清單為空，修正後精確 split 並成功套用。歷史 native、bridge、scene 三組撤回各 exit1、恢復各 exit0，仍綁其原始來源；probe明記允許dirty狀態，不能只用head稱乾淨驗收。

F13固定來源13d02c1db7022145a52ee063286a558e595eb212，222197B archive與5份選件hash匹配，原workflow/step exit0且未超CI；432／165／51與A/B/strip PASS正確。未重跑或宣稱整tar重新驗畢。

補充：F13與main的整個current_geometry.c記錄hash相同（f91cfa7d…），不是只有函式相同；但一個完整C檔、18個方法與3個fixture仍不等於完整依賴閉包。原報告已明說不得移標F13全綠到main/newF。#291 D:憑證未讀、ghost瀏覽器行為未由本映射驗證，也都明示。

#198只能保持關閉候選：負責人仍須核對完整issue範圍與目前來源有效正式收據。本審查沒有關issue、改產品、編譯、native、Git/API或新下載，也不新增公理、門檻或golden。

詳細pins、可/不可結論與分項審查見REVIEW.json。此輪只審新包，未重核其他已交付版本。
