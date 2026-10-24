PF-2 的完成面若沿某軸完全位於板縫內，原本會逐列檢查不存在的板本體。原 R10 P2 輸入實測會掃 5,000 萬個空 row，才由原縫線容量拒絕。本修正利用既有交丁的奇偶兩相位，確認實際 row 範圍是否可能有板；僅所有相位都空時省掉 body 迴圈。

raw seam 列舉、4096 容量、錯誤類型、裁切與有板時的順序保留。小測例要求零片合法且保有六條 raw seams，包含另一相位有板、負 row、轉置與貼齊邊界。成本測試使用真函式呼叫數，沒有新時間門檻。draft 疊在 #346；順序 #343 → #346 → 本 PR → 512，後續 512 一般 merge 本分支。參照 #128 R10 P2 與 #300 前置，不關閉 #128 或 #300。

## 唯一 current-state

| 欄位／gate | 目前值或退出碼 | 精確界線 |
|---|---|---|
| product SHA | `324034812bb6effca68e0413bc0468595337b317` | 產品一 leaf、測試兩 leaf、expected 10→13；正式前後乾淨 |
| evidence head | `eb93fbe977b381f67afbf997623f9699d0cb0f0b` | 此提交只加／更新證據；正式 execution SHA 仍為 S324 |
| base | #346／`a5f1806fb3cad2dada1a56e79e01d54f9f86700f` | source parent；未改別人的分支 |
| `python3 -B tests/test_geo261_panel_native.py` | **0：13 methods、0 skip** | 用獨審 passive observer/runpy 執行原入口、封存所有子程序；原 60 秒不變 |
| 原 NativeBuild compile/link | **93 次全 0** | 原旗標／300 秒限制；compile error 不算反證 |
| 原十個 semantic controls | **10 個正常具名 ASSERT exit 1**；同 suite 正例 exit 0 | 保留原方法順序，不假稱每個舊控制另有恢復執行 |
| 三個新 semantic controls | **各 0／1／0** | 一相位誤略過、丟 seams、誤拒合法空板；完整 stderr 原文已封存 |
| 整段優化撤回／恢復 | **0／1／0** | fixed calls 2／2；withdrawn 5,000／50,000,000；restored 2／2 |
| `python3 -B formula_probe.py` | 0 | 純 Python 1150 案、488 全空、19 首 phase 空而後有板，與 C 證據分列 |
| 來源及原件靜審 | 239/0、40/0、23/0、658/0 | 草稿、companion、公開 source、前一版 E/D 包 |
| 正式 wrapper 獨審 | 31/0 | 四個純 parser 負例拒絕假綠；不冒稱產品執行 |
| 新 formal 原件／E/D 獨審 | **進行中** | 正式已跑，但仍待另一代理核對這份新公開證據 |
| PF-1／PF-2／PF-3、完整 native、受影響 browser | **UNRUN** | 不借其他 SHA／工作線的歷史通過 |
| 最終突變帳本／架構三裁判與收據 | **UNRUN** | 主代理依最終來源統一重產；子代理沒有另跑帳本 |
| 允許的 skip | **本 suite 實際 0 skip** | 沒有新增允許 skip；其餘未跑仍 UNRUN |
| 合併狀態 | **NOT READY** | 待整合、帳本／架構與新證據審查 |

成本撤回的精確失敗是 `ASSERT:empty-axis-work-independent-of-empty-row-count`，正常 OS exit 1。六次測量均保留 status 7（`WOOD_PANEL_SEAM_LIMIT`）、clip-status 0 與輸出清空斷言。三個新語意反證為 `ASSERT:empty-first-phase-keeps-other-parity`、`ASSERT:empty-axis-zero-pieces-with-raw-seams`、`ASSERT:empty-axis-legal`；每組前後正例都實際返回 0。

[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/eb93fbe977b381f67afbf997623f9699d0cb0f0b/evidence/issue128-empty-panel-rows-20261024/PROGRESS.md)、[FORMAL_SUMMARY.json](https://github.com/ZhiQiYang/geometry-axiom/blob/eb93fbe977b381f67afbf997623f9699d0cb0f0b/evidence/issue128-empty-panel-rows-20261024/FORMAL_SUMMARY.json) 與 [FORMAL_RAW_INDEX.json](https://github.com/ZhiQiYang/geometry-axiom/blob/eb93fbe977b381f67afbf997623f9699d0cb0f0b/evidence/issue128-empty-panel-rows-20261024/FORMAL_RAW_INDEX.json) 綁定 1,250 個新原件。正式 archive 共 3,308,093 bytes，SHA-256 `ca40b62ec0462b02ecc1dd8727f4317bf03cf0a8ece286cf302b968725b0adda`。每項保留指令、退出碼、完整 stdout/stderr、環境、SHA、實際 native 執行檔 hash、負例 C 與 93 條 compile/link 原件。原草稿 322 原件 archive 與歷史 UNRUN 進度仍在 Git 歷史中。

之前 `git add` 的 ignored 提示 exit 1、companion peer 初 matcher 誤判與封裝 parser 的時序調整，都保留原件；不把它們算成 C 產品反證。正式 source checkout 僅補實際需要的 131 個 Git 檔；OUT/TMP 隔離在 workspace，未碰全專案 native 的 global cache。

本片不改公理、決策佇列或 UI。staggered raw seam 自身的空外層尚未優化；JSON 精度、PF UI 回執與 allocator 契約另案。最不確定的是尚未跑的整合及最終帳本／架構；局部正式綠燈不代表整個 PR 或 #128 已完成。
