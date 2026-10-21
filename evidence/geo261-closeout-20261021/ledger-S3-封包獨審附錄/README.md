# S3 帳本凍結包的獨立複核

本輪只讀複核相鄰 `../ledger-S3-cc/`，沒有修改該凍結包、重跑突變或執行產品。接受器實跑原碼為 `command-code.txt`，原 stdout／stderr、父程序真 wait 與三項只讀 Git 命令分別保留；沒有首次失敗或重新執行。

真結束碼 0，父程序等待 0.6405133200023556 秒。2,409 檔、45,078,348 bytes、2,408 筆根 sums，以及 nested sums 的 exact set／hash 均通過。2,405 個原件逐 bytes 與索引來源路徑相同。根 index SHA256 `a83861a1ec28f1cd553536788e4e428c60694f665e09b18bfaf9efaab563c9c3`，根 sums SHA256 `b6bc4f66c39c92ad186dca2c29ca318ef005dfeda83153ddfbc32e989ee29e2a`。

75 execution 全部仍標 S3 `19401ca5448e162ee6140fed37b64b83b31ddec8`；78 checksum、source／closure／oracle／mutant／tool 與新 L3 snapshot 相符。L3 是 `6589248c9a94bdf0460d8f84dd1610e51048188b`，parent S3、唯一帳本差異、Git blob、5,170,289 bytes／SHA256 `52aa08ac9e0c88f96b81d35f985b7fadfbb746086ec8b99d7ae10fd3043d3178` 相符。原 publication 的歷史欄名與別名說明一致，沒有誤稱 ledger 在 L3 重產。

亦核原 363 份來源備份、三 phase 的完整輸出雜湊與真碼、父 wait／工具觀察、原方法沿革與封包結果不自含。封包所有檔為 0644／UTF-8，未含禁用副檔名、magic 或 symlink。只在指定子包及其索引所列原件範圍讀取，未重 hash 所有 cached binaries，未掃完整 final-bundle。

peer.json SHA256 `8eb5b27e17ee115bdefb5d28af2ecff9f1b73872f47aa3f4a784eb96c6b1873e`。此結果是封包與來源綁定核對，不取代帳本本體記錄的判決限制、正式 default-check、其餘 L3 驗收或後續 PR 複審。
