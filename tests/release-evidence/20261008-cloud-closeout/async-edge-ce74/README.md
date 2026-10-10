# #173 ce74 在整合候選的限定重播

實跑候選 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`（前後 clean），含 #173 `ce74dc949168b597e33ec00110ce57f26ae51ff8`；main 為 `5cc1ffa1ee85120eca14258b86b715151cad274f`。原探針與儀器碼未改，Chromium 保持 sandbox。

| 操作 | main / face × 1400 / 390 結果 | 完整 World |
| --- | --- | --- |
| 拒絕等待期間，在原 input 再輸入 5151 | 4 PASS，保留新草稿，model 4000 | 逐字不變 |
| 拒絕等待期間，重繪 input 後再輸入 5151 | 4 PASS，保留新草稿，model 4000 | 逐字不變 |
| 成功套用 4200，等待期間另邊輸入 4242 | 4 PASS，4200 正式生效，4242 留草稿 | 只 A 外環右邊 4000→4200；孔、placement、canvas-pos 不變 |
| 拒絕等待期間重繪，沒有再次輸入 | 4 FAIL，已拒絕 2000 仍留在新 input，model 4000 | 逐字不變 |

程序 exit 1；16 個原 change callback 均等到完整 promise settled，沒有頁面或前置錯誤。#173 尚不具備整體完成條件。Owner 下一步：依提交工作身分處理重繪後的拒絕復原，清掉仍屬已拒絕提交的值，同时保留較新的輸入；沿用這份未改的探針回歸。

`binding.json` 連結完整 SHA、命令、stdout/stderr、runtime、來源與腳本 hash、dirty diff、逐案原結果、32 個完整 dump 的 trace callId。`.scene` 是從私存原始 trace 的 dump 回覆逐字抽出，再逐 byte 複製到本包；不是另一次查詢。`independent-review-extract.json` 是唯讀獨審原件的衍生索引，原件 hash 與私存位置明列。`SHA256SUMS` 可在本目錄執行 `sha256sum -c SHA256SUMS`。

公開子集包含原結果／收據、3 個原腳本、完整 dump、6 張已檢視的合成未命名專案截圖。16 份完整 trace 與含 session 的原身分資料留在私存，hash 在 binding 中；沒有公開私人圖紙。Bridge 實際 `/proc` 身分是在本輪之後、同一 runtime/session 唯讀核對，並與原啟動／建置收據連結，沒有冒稱 pre-run 檢查。

兩個 pane 都是 `view3=false`。這輪成功操作仍含 sibling 草稿；普通成功套用及正常切換到三視圖 B 的晚回覆補驗是另一份探針，不在本包。重繪是明示呼叫產品 renderer 的競態探針，沒有宣稱某個自然 UI 事件已觸發該重繪；不代表真實手機、IME 或完整 Geometry 驗收。歷史作者原 #173 探針仍未取得。

原始 browser trace 有 JS 回應狀態與 runtime/session 標頭，但沒有回應 body；檔案系統／提交來源 hash 不冒充當時 browser body hash。CSS hash 是同提交的補充索引，這輪未驗 CSS。

在同路徑 checkout、已證明 fresh 的隔離服務及獨占 browser slot 下，保留原 hash 重播：

```sh
python browser_probe.py --url http://127.0.0.1:18971/ --out /workspace/closure-evidence/replay-unique --only edges
```

原腳本會 reset 隔離測試 World；不可指向使用者工作中的服務。歷史原實跑命令與 exit 在 `browser-edges-integration-ce74.command.json`。
