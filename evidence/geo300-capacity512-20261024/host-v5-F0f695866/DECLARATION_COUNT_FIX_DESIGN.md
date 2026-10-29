# #348 未放置宣告計數：測試缺陷與精確修正稿

目前公開產品／測試 S：`400a6d0ca50f3aca104fb569c77c8ef753c93355`。本稿尚未套用、編譯或執行。先前 H 靜審沒有查出這項讀取端選錯，不能因此把原 H 測試寫成通過。

根因在 `tests/test_geo261_timber_capacity_host.py::assert_count`：它把 `objects.timbers` 當成宣告列表。`geometry-web/web_bridge.c::cmd_objects`（約 924 行）明確略過 `!t->placed`。本 suite 的 512 場景全為未放置宣告，原斷言 `list(range(1,count+1)) == [item['id'] for item in response['timbers']]` 必會把空列表誤判為容量丟資料。這是新測試缺陷，非產品容量紅燈；仍待真正常 AssertionError 留存。

不用 `engineering-read`：`engineering_bridge.inc::cmd_engineering_read` 傳入 `json_engineering_state(...,false)`，沒有 geometry.timbers。真來源是 `dump`：`cmd_dump` 呼叫 `world_dump_dsl`，再由 `geometry-core/references.inc::reference_dump` 的第一個 timber_count 迴圈輸出每筆 timber 宣告；只有稍後 place 迴圈才篩選 placed。此 suite 沒有 assembly-owned 或 engineering-derived 宣告。

精確修正只有原 helper：保留 `objects`，但驗它 `ok=true` 且 `timbers=[]`；另外 `dump` 必 `ok=true`，逐條取得 timber 聲明，驗完整 ID 序列等於 1..count。此序列等式同時禁止缺項、重複、排序漂移；full-capacity redeclare 的再次計數也必仍只有 ID 512 一筆。額外禁止任何 place 聲明，確立此 suite 真為 unplaced。原完整 dump 拒絕前後比較（含 revision／definition_sha256）、原 512/513、原 safe missing-ID 反證、原 7 ABI 具名 compiler 反證與時限全部不改；方法數仍 5，registry／expected 不變。

正式時槽後：先在新 F 執行原 H suite；另在 private closure **只撤回此 helper 修正**，真編譯產物與產品碼不變，執行原 `test_each_real_declaration_retains_legacy_64_and_admits_up_to_512`，首個 count=64 檢查必正常 AssertionError、退出 1，訊息含預期 1..64 與實際 []。它不是編譯失敗、timeout 或 crash。恢復原 bytes 後同一方法退出 0；固定／撤回／恢復各保存完整指令、原輸出、SHA、環境與 exit。若實際首紅較早，例如宣告被拒，先分類，不冒充此刀成功。

本修正為 tests/*.py 變更，後續依 root 規則更新 ledger／architecture 所需收據；本代理不自行重產全帳本。原 H suite 的 512 都仍是未放置案例，不替代另份真正放置計畫。
