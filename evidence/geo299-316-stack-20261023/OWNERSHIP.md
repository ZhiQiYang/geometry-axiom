# #299＋#316 新整合基底準備

本次唯一 owner 為 `own_299_316_combined`，工作 repository 為 `/tmp/g261-next299316`，來源分支為 `codex/geo299-316-combined-20261022`。本次開始時乾淨 HEAD 為 `139ab64ca5f88e89bb4e95921675b998457026aa`；其中歷史正式產品 SHA 為 `5bfadf187e615ba0fb8466753b63ce3044ef7d1c`。舊正式結果保留其原執行 SHA，不能當成尚未產生的新整合結果。

共用檔案交接順序為 #323 → #314 → #299＋#316 → #318 → 不帶木工建置。收到 #314 已推送分支後，先一般 merge，再處理真正的 union/conflict；不重新套用舊 combined patch 覆蓋先前修正。整合分支只由主代理寫入。

可能交集包含 `current_geometry.c`、`tests/mutate.py`、`tests/run_tests.py`、`tests/test_geo261_mutation_migration.py`、`tests/run_all.expected.json`、唯一正典 HTML 與追溯資料。`current_geometry.c` 保留 CRLF。原生木工 leaves 為 contacts/contact_world/world_validation；#318 在本棒交接前僅準備 repo 外候選。正典依原同步器重建，不手改嵌入 JSON。

combined 的既有突變 ID 固定 M89–M98，共十個；靜態 AST 檢查各 old anchor 在原產品檔恰一次。這不是帳本 freshness 或 mutation execution。#314 既有 M99–M120，新增對抗邊界預計 M121，須由主代理統籌；combined 不使用 M99 之後 ID。完整帳本只由主代理在最後 SHA 整份重產一次。

本次已在自己的 repository fetch handoff，固定來源為 `ea2748248d47563f8559638ccb70ec0ed21910d9`。其中不存在 `handoff/pr-reviews/299.md` 與 `316.md`；不假稱讀到不存在的審查。已完整保存 combined README、指定 rebased patch 與八個 `_gen` 輸入。handoff 分支不合入產品。

目前不執行 compiler、Chrome、benchmark 或大 IO，以配合主代理 R3 測試槽。之後採獨立暫存目錄、原斷言與原工具範圍，所有動態結果待正式排程。
