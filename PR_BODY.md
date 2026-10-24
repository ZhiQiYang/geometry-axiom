容量 512 分支目前固定來源為 `73b21e64dce72f0d16ca29e18559c51815b9724d`。本次只修驗收的安全哨兵：一欄 `timber` 會先被 dispatcher 的四欄最低語法拒絕，無法驗證 handler 的容量守門；改用 `timber 513 27 33` 跨過 dispatcher，撤除容量守門時仍會在 handler 的 `count<5` 檢查拒絕，避免追加第 513 筆越界。原一欄負例繼續驗語法拒絕、完整 dump 與歷史不變。

| Current state | 證據來源與結果 |
|---|---|
| Product C SHA | `400a6d0ca50f3aca104fb569c77c8ef753c93355`；本次沒有改產品 C |
| Current test/source SHA | `73b21e64dce72f0d16ca29e18559c51815b9724d` |
| Evidence head | `9a8584f57be7935604c3bad4c2481945a6ec3d9f` |
| 三個受影響的 H 方法 | 在 F73 執行，原退出 0、3/3、零 skip |
| count helper 撤回／恢復 | F73 真 0/1/0，正常具名 AssertionError |
| population helper 撤回／恢復 | F73 真 0/1/0，原 I9 拒絕與完整 raw 保留 |
| unplaced replay helper 撤回／恢復 | F73 真 0/1/0，獨立原 I9 負例，不被哨兵遮蔽 |
| 哨兵測試修正撤回／恢復 | F73 補跑真 0/1/0，精確 `host-capacity-first-incomplete-declaration`；不是編譯錯或越界 |
| W 容量 7 方法 | 歷史 F0f 原 7/7 全綠；本次 F73 沒有重新跑整組 |
| H ABI 兩方法 | 歷史 F0f 兩方法通過；本次定向範圍沒有重跑 |
| 512 placed load / sequential history | 歷史 F0f 兩個原 600 秒 `TimeoutExpired` 仍未解；本次沒有重跑／沒有放寬時限 |
| Full native / 六個 browser / 帳本／架構 | 此分支目前來源尚未完成；待產品根因修正與後續整合驗收 |
| 允許 skip | 無；缺跑一律列 UNRUN／環境原因 |
| 整體狀態 | 不是 READY-TO-MERGE；兩個 512 placed 問題仍擋住容量驗收 |

F73 第一輪 partial 原 driver／外層退出 **1**：前十個 phase 符合預期，最後三個哨兵修正 phase 被原 100 MiB 環境容量守門標 `UNRUN_ENVIRONMENT`。保留該原退出碼；環境回收後，另用新 OUT 只補這三個缺跑 phase，真退出 **0**、0/1/0、雙 observer complete、來源還原且 clean。沒有重跑原已綠十個 phase 或舊 U 的效能樣本。

歷史 F0f 全批原件的 W7 退出 0、H7 退出 1；H7 包含三個哨兵 assertion 與兩個原 600 秒 timeout。當時三個 helper 的實際三態皆是 1/1/1，不能當成已完成反證。該完整紅包有 6369 個原 member，gzip SHA256 `dbe988b880024aee708d85d3b0364adf5ab61c9587f861271d8e2170755b37a7`，已獨立逐位元組核對及分類。原 `TimeoutExpired` 沒有正常 CompletedProcess returncode，照實記 null；四份 scene 是執行中事後保全，沒有冒稱事前捕捉。

F73 使用另版 v2 observer，在原 command／run 前保留實際 loadfile bytes。這是功能測試的輸入保全，不能拿其額外讀檔當效能測量。保留原 64 witnesses；容量契約先前依授權同步為 512/513 與 3328，其他 golden 與原時限保留。仍未證明完整 512 placed 世界、stack 峰值或容量效能驗收通過。

下一步：先定位兩個 512 placed 逾時的真根因，正常合入主列車的新前置修正後，再在新的可解析來源執行受影響正式驗收。此線不合併 PR、不 force push、不修改決策佇列或未核可公理。

兩批完整原件保存在 `evidence/geo300-capacity512-20261024/formal-F73b21e64/`。F0f 紅包逐原 byte 獨審 25485/0、原流分類 1809/0；F73 包 5901 member 已逐原 byte 獨審 23643/0，原 phase／具名反證另核 171/0。六個刻意建立的 symlink/FIFO 自驗 fixture 只保存 lstat／readlink 描述，未循連結或讀 FIFO。這些是原件完整性與定向驗收結論，不替代兩個 512 placed 正式方法。主代理目前優先修正 #338 的效能紅燈；本線後續一般 merge 與重測依列車的驗收結果安排，沒有預報改善。
