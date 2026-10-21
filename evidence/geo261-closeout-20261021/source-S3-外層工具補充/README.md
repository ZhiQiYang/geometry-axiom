# S3 發布及採入的外層工具補充

本補充在 `source-S3-binding` 與 `source-S3-adoption` 已封裝後新增，保留 root 提供的完整工具觀察轉錄，以及發布／採入方法原碼，不修改兩個子包的索引或 SUMS。

工具觀察檔記 publication session 47163／chunk ca64fb 與 adoption session 54176／chunk e1660d 真 0；它是 root 對實際工具回覆的事後轉錄，不是 raw transport，也不是本封裝重新 wait。兩支 Python 僅按原 bytes 轉存 `.txt` 供閱讀，沒有執行；原命令 stdout／stderr／退出碼見相應來源子包。

此包不宣稱 S3 帳本或 L3 驗收完成。原件清單列四份來源複本；另外三檔是本 README、原件清單與 SHA256SUMS。SUMS 覆蓋除自身外所有檔案。
