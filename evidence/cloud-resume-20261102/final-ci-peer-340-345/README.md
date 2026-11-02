本目錄是 PR340／PR345 最終 F CI 的獨立唯讀原件審查。

詳見 REVIEW.json：包含所有輸入 SHA256、24 個 ZIP 的 1334 個實際 member SHA256、20 個 logical gates、各 native 237/237 聯集與 5421/5420/1、canvas 2286/86 golden/P38，以及 PR345 attempt／documents／POST403 來源。

本次只執行自寫 Python hashing／解析與唯讀 Git 查詢；沒有執行產品、ELF、Chrome 或原 verifier，沒有下載、改 source、branch 或 PR。M→F derived ledger/cache 不在本次重核範圍。

審查核對數：3574；失敗：0。

兩個最終 F 的十個 logical gates 原件各自通過；PR345 的通過來自九個原 attempt1 成功與一個新 attempt2 documents，沒有把繼承列計作重新執行。

PR345 相對指定 main 的唯一測試程式差異為 tests/test_rule_case_workbench_http.py；未將整個 test tree 說成與 main 相同。retry 發起人未知，root POST 403 未被當作成功重跑。
