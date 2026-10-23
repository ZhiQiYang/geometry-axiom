# GEO-261 F3：繪圖身份不再取自中文字串

`replay` 現在讀取 draw text operation 的可選 `member-face` annotation。構件身份、面身份與短標籤
由結構資料提供；完整文字仍用於 tooltip/aria。`data-timber-id` / `data-timber-face` 等既有 DOM
契約、縮放、樣式、標籤最後覆畫順序與輸入 ops 維持。缺少或格式不正確的 annotation 會保留完整
純文字，不由字面內容猜身份。沒有新 UI 操作或說明。

此片依賴原生 producer #273，凍結來源 `b370f753f22d0d119835c59d23b0a78344f8ee55`。該 producer
保留原 `t`，直接由真構件／面產生欄位；兩片須一起整合，再執行目前版本的 runtime gate。

## 實際驗證

`node --test tests/test_draw_annotation.js`：7/7 通過，exit 0，無 skip。測試從實際 app.js 擷取完整
replay 函式，使用 DOM double；涵蓋六面、uint32 最大身份、翻譯文字、誤導文字、純文字、壞 metadata、
原有幾何／樣式／圖層順序及文字注入。此為單元驗證，不是瀏覽器或 native producer 實跑。

延伸既有 TEMP 真來源控制腳本：五個基準 suite，119 discovered，117 pass、2 個 Windows symlink
權限 skip；全部子程序 exit 0。九個負控制皆對指定測試產生斷言失敗（exit 1），沒有語法／載入錯誤。
新增控制把 annotation 重新由 `角材…` 文字推導，翻譯與結構身份測試轉紅。來源逐 byte 未變，TEMP
已移除，完整 raw logs 和 receipt 已提交於 `evidence/frontend-f3/`。

新增 `node:draw_annotation` 7；既有 suite 的 expected 未改。真瀏覽器操作、原生 producer 4 測試與
完整 run_all／舊夾具重建仍待整合版驗收，尚未宣稱通過。

追加實跑 `python tests/run_all.py --only draw_annotation`：exit 0，7 pass / 0 fail / 0 skip，
registry 與 expected 通過；明確為部分執行。先前嘗試使用不存在的 `--receipt` 參數被 argparse
拒絕，未執行 suite；改由外層 capture 保存真子程序 exit 與原始輸出後成功。
