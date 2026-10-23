# #314 完整 native 診斷：進行中

固定來源 P2：`291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6`。原 `run_all.py --build` 在 detached sparse 副本執行；只配置原 binaries.OUT_DIR 為私有輸出，原 flags／smoke／fingerprint／suite／expected／judge 不變。主 #314 分支帳本沒有寫入。此為診斷，不是最終正式驗收。

已完成核心 165／165。原 mutation:check 如實為 75 stale、3 retired、22 unrun，正式帳本需全份重產，沒有跳過或代填綠燈。227 項仍繼續跑，待終態一次收齊紅燈。

目前 assembly 的兩條失敗原因分開處理：

1. **測試工具錨點過期**：`tests/assembly_mutation_check.py` 的 cancelled-preview 還釘舊 `app_candidate_discard(...->control)`。產品已改由 `app_world_candidate_discard(...)` 同時清除有序證據；工具需語意重新下錨，原取消 guard、8 tags／3 cases／6 controls 與正常 ASSERT 保留。
2. **環境缺少 orphan 回收**：`test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left` 的兩個 sleep 為 PPID 1／state Z；本次外部 native 啟動器沒有套既有 subreaper。這一條不改產品或測試斷言，原 raw 留存，終態後在既有 `reap_children.py` 環境只重跑受影響項。往後所有含子行程／負控制的診斷與正式驗收都外包原 reaper。

沒有向正在執行的 native 注入或更改任何東西。完整 stdout／stderr、固定前後來源、工具／OUT_DIR 適配、ledger 前後 bytes／patch 與觀察到的 temp build 產物待終態同封；observer 明列 observed-only 與 missing，不誇稱全部捕獲。其餘紅燈尚待收齊，未完成項不列通過。
