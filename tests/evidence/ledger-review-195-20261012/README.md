# #195 帳本審查修正原件

回覆 6111899500／6111939990。受核為前 head ef719904913a50803c20fe632d93c0954042ea2e 加 dirty BACKLOG 修文；不是乾淨新 head 的產品驗收。

before.json：六處未開始與即時 open draft #192／#193 不符，exact/sample 與同 head I25a／I37／R32 的採納不符，共7項，exec 工具實際 exit1。after／restored：0項、直接子行程 exit0。

本次原腳本保護集合比前輪只提45／46更廣：45條含🔒、208條含「使用者」，聯集247條，逐字逐序全同。唯讀記憶體副本的modify／delete／reorder各只故意破壞一項保護文字／順序，實際exit1、指名保護失敗；另新子行程重讀未變異BACKLOG，restored exit0。沒有寫入變異或改SSOT／🔒。這些是文件audit負控制，不冒稱產品mutant killed。

audit.py、receipts.py、五次命令／直接exit／stdout hash、全部JSON與stderr、原PR192／193讀取快照在此。重播時先把pr192.json／pr193.json複製到/tmp/geometry-195-pr192.json／geometry-195-pr193.json，再於repo根目錄執行python3 <本目錄>/audit.py after；它依原ef7199 Git blob核保護原文，PR快照只重現當時核對，不代表未來即時狀態。

M1六處同步進行中／draft，保留#182 I44關聯、#193疊#192、未合併及最終驗收未完成。M2既定exact/sample API移出不採納清單、列已採納且有實作；驗收另依版本／原收據，REPEAT_PANEL及Q36其他未採納語義保留。沒有把程式存在說成產品全驗收。

原K1進度／#169合併祖先／I44歷史更正／SR16-SR23／P88／PF14-24紀錄不變。產品C／INC／JS、SSOT／正典／白話／決策、tests／期望／core ledger不變；未跑產品、WSL或七job，無新覆蓋需重產核心帳本。既有#185／#187／#191／#200文字衝突仍由唯一整合owner逐段保留各方增量，不整檔選邊、不宣稱已整合。維持draft、不合併、無新UI入口。

SHA256SUMS列全部payload（不自雜湊）。原前輪audit未取得，本目錄是本次獨立重做原件，沒有代替前輪補造收據，也不能解除B1正式最終SHA七job。
