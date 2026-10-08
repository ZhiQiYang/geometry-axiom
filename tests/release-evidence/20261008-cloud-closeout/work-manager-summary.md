# 工作管理器的有界交付

`bdd1bf7812ba6126aab9ddffced43cd200ac977e` 修正同一 PR observation 再匯入時遺失原 task 事件、錯誤建立來源新版的問題；只重用同來源 immutable 事件，不抄入其他來源的 scope、批准或審查資料。兩個新增合成回歸修前失敗，修後完整工具 suite 144 通過；獨立 source 與邊界審查見 `inventory/adapter-review.json`。

**本檔最新已匯入的是 v5，來源截至 `2026-10-08T18:59:48.094425+00:00`。** [整合草稿 PR #176](https://github.com/ZhiQiYang/geometry-axiom/pull/176) 當時 head 為 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`、base 為 `codex/final-release-closeout-20261008`；main 重新核對為 `5cc1ffa1ee85120eca14258b86b715151cad274f`。v5 匯入發布後全部 32 個 open PR 與 27 個 open issue metadata，沒有預填之後的證據文件提交。各 GET 有自己的時間、命令、stdout／stderr、退出碼與雜湊，並非同時點的 GitHub 交易快照。

v5 前逐 byte 保存 v4 SQLite、副本 export、舊收據 manifest 與公開摘要。首次匯入 inserted 33／duplicates 58，其中只新增 **1 個工作引用（#176）**；事件數不是完成工作數。同一 observation 再轉換的 snapshot 完全一致，重複匯入 inserted 0／duplicates 91／source_updated false，DB bytes 不變。reconcile／list-ready／list-alerts 同一 state hash `f5bb906a0175ba8f6dd433a23bfbbbcbcfaafaae74452a4be18e0485dd39249e`，store health 為 ok；59 項 ready 全為 read_only、write 0，沒有派工。既有 owner、scope、批准、review 與驗收證據逐欄未改。

這次新納入的深度 CI 原件為 #173 `181fc76049b2b2d001957d2ee0008448bbf5b024`（18:39 已取得）及 #176 的上述 head（18:59 新取得）。各 1 run／7 jobs 均 runner 0、steps 空，每組分別保留 7 份帳務未啟動註解及 7 份 Ubuntu migration notice；均為**未執行**，不是產品測試 pass 或 fail。其餘 30 個相同 head 的 CI JSON 與原 runner／steps 收據保留，不把 metadata 更新時間冒稱重新驗 CI。374 個 alerts 中的 32 個 `ci_failed` 是 workflow metadata，須連同 224 個 `ci_not_run` 解讀；owner_missing／scope_unknown 各 59 只表示這份 metadata ledger 缺資料，不能據此搶接本機 writer。

v5 前後 repository HEAD 都是 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，工具 Python 來源與 v4 相同。後續證據文件提交若改變 #176 head，應追加私人 v6 觀測並在 PR 交付摘要記錄，不能倒填為 v5 已觀測或原測試 head。#168 已取消與 #169 待批准的審查留言仍暫停。

本輪另以全新私人 ledger 匯入保存的 GitHub observation。v1 核對截至 2026-10-08T15:40:24.624360+00:00；v2 加入全部 31 個精確 PR head 的 CI runner/steps。每筆 source 都保留原核對時間與完整 SHA，兩版重複匯入均不建立新來源版或改 DB，並執行 reconcile、list-ready、list-alerts。58 項 ready 都只有 read_only，write 為 0；來源審查不是派工或批准。舊私人 DB 未取得，沒有升級或覆蓋它。

Python 3.12.14／Playwright 1.62.0／Chromium 151.0.7922.173，sandbox 保持啟用。在桌面 1382×804 與 390×844 以合成資料驗 W19 去重、父子／scope狀態、UI/API/CLI hash 與時間一致、搜尋、Tab/Enter/Space、明細焦點、真 UI 匯出後在新 store 恢復，以及 beforeprint/PDF。實跑 `3a48cf5bacb9a295e15046e5ca0cb021e50c54db`；工具七個來源檔與後續9a4136d逐檔相同，未冒稱整個 repository 一直乾淨。

原 75 個名義 checks 中有兩條 future composite 用錯 membership oracle，現只保留 73 個有效原檢查。原輪與判定修正保留。另用最小真 UI 補驗：兩寬度 all+Future可見→ready+Future空結果→ready+ChildReady正控制→write+Future空結果，16 項有界 checks 通過；兩輪不相加為使用情境或整體產品驗收。兩份独立 browser 審查亦完成。

SQLite、snapshots、owner thread、原始事件、工具截圖及匯出備份遵守 work-manager/AGENTS.md 留私有。`work-manager-private-receipt-hashes.json` 只標識本輪可取原件，沒有把 hash 當公開原件。歷史私人66-check harness/raw與舊DB仍unknown。實體手機、IME、OS列印對話框與CI實際runner執行仍不在本輪範圍證據內。

合成 unit suite 可從 repository 根目錄重現：

```sh
python3 -m unittest discover -s geometry-web/work-manager -p 'test_*.py' -v
```

這些成果屬工作工具，不能代替 Geometry 的幾何、專案或保存驗收。

歷史來源版本 v3：保存 v2 後只追加 #171 fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d、#173 c0def319b49a45512489535b6bea526ccb5f6aec、#174 5083a456b1caff33fbc56c5fa10927582432a283、#175 1127531f3aab472e01a4a99c03ef7b739b1b8ae5 及各 head 的 CI。其餘 27 PR、27 issues 原核對時間保留；重複匯入 inserted 0、source_updated false、DB bytes 不變。reconcile／ready／alerts 同一 state hash，當時為 58 read_only／write 0；整合新 PR 的後續觀測見上方 v5。

歷史 v4 的範圍明確限於 **#173 `ce74dc949168b597e33ec00110ce57f26ae51ff8` 的 metadata 與精確 head CI**，當時沒有匯入另外取得的完整 31-PR 刷新。來源為 `github-closeout-20261008-api-read`，截至 `2026-10-08T17:24:31.304218+00:00`。1 run／7 jobs 均 runner 0、steps 空，7 份帳務未啟動註解與另 7 份 Ubuntu migration notice 分開保留，不能稱產品測試 pass 或 fail。

v4 前已逐 byte 保存 v3 SQLite、副本 export 及舊收據 manifest。首次匯入 inserted 1／duplicates 1；同 observation 再轉換得到完全相同 snapshot，重複匯入 inserted 0／duplicates 2／source_updated false，DB bytes 不變。未輸入的 **27 issues＋30 PR，共 57 個既有 task 的完整投影及核對時間均不變**。reconcile／list-ready／list-alerts 同 hash、store health 為 ok，仍為 58 read_only／write 0、364 alerts；metadata 缺 owner 不表示本機無人負責。

v4 操作時候選為 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，前後 HEAD 相同且工作樹乾淨，工具 Python 來源與 v3 相同。當時 main pin 沿用 `5cc1ffa1ee85120eca14258b86b715151cad274f` 的既有來源並核本地 origin/main；v5 才重新讀取遠端 main。v4 時尚未建立整合 draft PR，後來取得的 #176 不倒寫進 v4。兩版匯入都不等於產品驗收、review 批准或新派工；舊 browser 證據不改綁新候選。
