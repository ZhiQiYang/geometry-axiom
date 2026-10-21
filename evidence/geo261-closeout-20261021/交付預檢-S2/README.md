# S2 交付預檢與外層收據補件

本包只補齊已存在的五份 JSON 與四份具名退出碼，並保留一次有限預檢的原件、更正與限制；沒有修改主 repo、舊子包或其 manifest，沒有產最終總索引，也不代表 L2／E2 驗收完成。

外層收據補件包含 cc ledger publication-check、P-189 final-L／codec／contact packaging，以及本輪 architecture-S2 包裝收據。前四份各有真 0 退出碼原件；architecture 包裝收據沒有獨立同 stem 碼檔，沒有補造。GCC 歷史 publication-check 及具名退出碼早已存在於 ledger-A-gcc/integration，未重複當成缺件。

預檢讀取時 19,540 檔／208,687,311 bytes。40 份清單、21,333 筆引用的 hash／提供的 bytes 相符，沒有禁用類型／magic／symlink／執行權限問題；原定 ignore 三行模型使全部路徑可收錄。第一次預檢因將 #300 的原件索引誤套為全包 exact set 回 1；首次外層核對因同名判缺而將已改名收錄 GCC 原件誤列缺件回 1。兩次真碼與原稿均保留，後續只讀判讀／hash 分類為 0；沒有重跑整包或改寫舊結果。

所有原件 bytes 保持不變；ignore-model/、其 .git 與任何 .py 均排除。方法只以 code.txt 保存，無執行權限。本包來源索引排除自身，copy-check 另在總根的交付預檢-S2-copy-check.json，不能誤當最終 artifact-index。
