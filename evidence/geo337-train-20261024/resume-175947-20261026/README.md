# 本輪完整原件與明確外部輸出索引

此包保留本輪新指令、時間、退出碼、環境、錯誤、結果與所有獨有輸出。只有 INDEX.json 明列的 24 份 fresh API stdout gzip 容器不重包；其完整 raw stdout 逐 byte 相同於固定 E9 的完整 manifest／raw payload，逐筆列 commit/path/Git OID/bytes/SHA256 與 30 個路徑別名。

本次唯一 git ls-tree stdout、全部 stderr 與新 reader／清理輸出均在 archive。不宣稱 archive 包含外部 gzip 容器，也不保證重新壓縮的 gzip bytes 相同；所有本地原件仍保留。原 maps 預檢 exit 1 不改寫，清理結果與產品驗收分開。
