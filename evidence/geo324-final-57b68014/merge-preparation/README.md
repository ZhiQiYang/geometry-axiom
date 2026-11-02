目前僅準備，未執行 merge 或產品裁判。root 正做 memo 效能短獨占，必須收到明確 release 後才執行。

執行：`python3 /tmp/geo324-owner-20261024/merge_train_50493347.py`。

原 ordinary merge 邏輯保留：只允許 expected host_sources 39→45 聯集；兩 leaf 必須等原 Grok blob；SSOT/決策 blob 必須等 incoming train。拒絕額外產品差異。capture 先驗 c387 SHA 才 import，封各命令 argv/環境/SHA/exit/stdout/stderr。先前 E c880 clean，incoming 5049 改三檔範圍只含架構 manifest、未改三個 #324 leaf/expected（預先唯讀查證，不代替執行時 guard）。
