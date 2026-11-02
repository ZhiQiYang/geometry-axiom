# #299+#316 帳本原始輸出封存

固定來源 S：`e40762e99b078335d78c65a3a2682a0c9ab875d0`。本工具只整理已完成檔案及以原純函式重建突變來源；沒有執行產品、裁判、編譯、Git 寫入或安裝 ledger。

原整份重產 full 命令退出 2、outer 退出 1，fresh bridge checkout 因 ENOSPC 失敗；原 checkafter／source_after 沒有錄到，保持缺漏。collector 順序前置查核另外退出 1，發生於任何 mutate 命令前。修好雲端容量後同 S 只重跑原受影響 bridge IDs，原 strict check 接續通過；完整結果分欄見 SUMMARY.json，不能稱單次 full 命令通過。

動態帳本 88 筆、85 execution 均綁 S；分類 `{'killed': 80, 'equivalent': 4, 'crashed': 1, 'retired': 3}`。原 67 個 core 紀錄逐 JSON value bytes 等同，完整證明在 PRESERVED_CORE_RECORDS.json。原 RESTORED 方法數 27，不依舊交接口頭數字增加或刪除。

RAW_PATHS.json 記所有原命令 stdout／stderr 及 bridge baseline／mutant／restored build/test streams 核對；archives 每包 raw 不超過80 MiB、壓縮檔小於95 MiB，inventories 每個 member 已自實際封包逐 bytes／SHA256 核回。來源 include closure、完整 flat Python judges、根 scene inputs 及實際外部工具版本另行保存。

原 core 內層 compile／attempt streams 未全部落盤，只留結構化結果及原 hashes；不以 hash 反推不存在的 stdout。RECONSTRUCTED.json 的 85 個 variants 明標 reconstructed-not-captured，core 比對原 fingerprint generated_source_sha256，bridge 比對原 mutant sidecar LF source hash，不能稱當時已捕獲原暫存 C。

EXCLUDED.json 對可重建 scratch／Git 子樹只記目錄 metadata、不讀內容也不假稱算過 hash；C closure／judge inputs 已獨立保存。其餘 ELF／objects 逐檔存原路徑、bytes、SHA256。所有原檔仍留原位。
