# E3 待執行交付驗證方法

此包只保存尚未執行的 `verify_E3.py` 原碼文字、原 E2 版本、差分與方法綁定。沒有 E3 提交、沒有 E3 成功收據，也未執行產品或重跑先前控制。

新版 18,120 bytes，SHA256 `6e1ac9bffab679486606fd3513762d167990c8b725b015778cf329a85590e279`。只替換三個常數值：L 為 `6589248c9a94bdf0460d8f84dd1610e51048188b`；SNAPSHOT_HASH 為 `3420121fdc8a24cdff5335762ffdd07db82a531c5efea7ca32aedd3f7f50bd43`；LEDGER_HASH 為 `52aa08ac9e0c88f96b81d35f985b7fadfbb746086ec8b99d7ae10fd3043d3178`。反向替換後逐 bytes 還原 E2 原件，SHA256 `99e6cdbafec586a97c37382216ad14737a173f6e394af3bde2685464d59db9e1`；AST 核對通過。所有其他邏輯保留，未將版本號替換成新的成功宣告。

未來 E 只能增加 `evidence/geo261-closeout-20261021/` 的資料證據，並精確附加既定 `.gitignore` 三行與 `.gitattributes` 一行。總 `artifact-index.json` 排序且 exact set（自身除外），外部 review 再鎖包含 index 的全集與兩設定檔前後 bytes。來源、closure／oracle／tool、帳本必與真 L3 快照相符；不允許用舊 L2 快照只改標題。

允許原始 source 以 `.txt` 保存，包含合法 shebang；拒絕可執行副檔名、執行 bit、symlink 及指定可執行二進位 magic，保留合法 PNG／gcanvas 等資料。原方法已處理直接從已驗 bytes 載入正式裁判與其四個本地模組，避免既存 pycache 代換。本輪只改三個 pin，未重跑原 57 個純資料控制；原控制與首次方法審查沿革仍在既有 `交付驗證方法/` 與 `交付驗證方法-L2/`。

實際 E verifier 結果需在 E 完成後另留 repository 外，不能為把 E 自身 SHA 寫回證據而無限新增提交。此處原碼為方法交付，最終總 index 與 review 尚待所有正式 L3 結果及最終草稿凍結後產生。
