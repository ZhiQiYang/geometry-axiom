本審稿迭代紀錄（不屬正式產品測試）

1. 初稿靜態 AST 解譯未涵蓋 B2_TESTS 名稱，Python KeyError，exit 1；保留 audit_actual.initial.py。
2. 增加安全 AST 常數名稱／字串 %／slice 後，讀到四個原 Git check_output stderr 為 inherited None，初稿誤假定獨立捕獲，KeyError path，exit 1；保留 audit_actual.second.py。
3. 明列四個 Git inherited stderr 後，7,619 項只餘一個審稿假設錯誤：原入口正常結束為 SystemExit(0)，不是 None。保留 audit_actual.third.py 與 REVIEW.initial-assumption-errors.json。
4. 修正為精確 SystemExit(0)，不更改任何產品、原 stdout/stderr、判決或已完成指令。最終審核輸出另存 AUDIT.stdout.bin/AUDIT.stderr.bin/AUDIT.result.json。
