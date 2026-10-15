# P-116 測試先行基準，尚非產品交付

來源：一般 merge main ea034fac 後的 635a949435f1064dc721306cd5b384652835d35c，
另有 test_panel_fill_host.py 與登記的未提交增量；核心產品來源同該 merge head。
執行命令 `bash -c 'ulimit -s 16384; python3 tests/test_panel_fill_host.py'`。
Linux，不是 WSL。

`before.*` 首輪 actual exit 1，發現 21 題、4 題失敗：import 了 PF2 的測試類別，
unittest 一併發現其 17 題。這是測試發現範圍疏漏，原件保留。
改成 module import 後 `contract-red.*` 只發現本套 4 題、4 題失敗、actual exit 1。
四題均在 put-derived-placement 被現行 panel-fill 交易拒絕，
尚未到達後續映射、鍵、D7 或保存斷言，不把這些項目算成已驗。

key-hex:[來源,段號,總段數] 的 JSON 十六進位編碼為測試先行的傳輸契約，
不是現行 DSL 支援聲明。產品實作後還須補缺鍵／索引拒絕等負例與實際讀回。
未實作產品、未跑完整 native、未執行 mutate，不算任何新增 killed。
P-116 原數學 oracle 与合法場景的五段／三段推導不變；沒有 R43 實跑收據。
