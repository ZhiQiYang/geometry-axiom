# 重用已排序的平面群範圍，減少接觸去重的重複搜尋

同一個 contact index 的 `out`、排序和 rank 在去重期間保持不變，原本每次 insert／covered 都重新二分搜尋完整平面群。本修改在排序結束後重用既有 scratch 保存群邊界，明確傳入原 face ordinal；不增堆疊陣列，不改 active、fixity、完整座標比較、穩定順序或公開介面。

以下是唯一 current-state 矩陣；原 R1 與 R5 記錄僅供歷史核對。

| 項目 | SHA／結果 |
|---|---|
| 上游產品來源 R | `a22df116c7e9f6b7d074451f1c8052d59e7e4f3e` |
| 本次產品／測試來源 F | `df66452e7a514032453bea93b8b18ab74d7b1457` |
| 主代理已一般合流 | `8d2a69421560b83c0b69f3e82db8f5e97ccc037b`；下列 36 方法與反證實際跑在 F，未移標 |
| evidence head | `f7a389deafed64f0f3137c0086a7033841c709e3` |
| 原 wood-contact／contact-sources／reading-A | 14／15／7；36/36、零 skip，三套 exit 0；354 次 compile/link 全 0 |
| 完整產品優化撤回 | 五處精確撤回；39 個語意案例全綠；16 faces 的 insert 比較次數 0／84／0、正常 exit 0／1／0 |
| 五個細控制 | 每組原 baseline／mutant／restored = 0／1／0，具名 assertion；非 crash／編譯失敗／timeout |
| 原完整座標反證 | `indexed-plane-coordinate` = 0／1／0；原 `indexed-full-coordinate-plane` 斷言保留 |
| 四行測試反例補強的自證 | 同 F 原 guard-controls 方法 0／1／0；撤回首紅 `Guard survived: indexed-plane-coordinate`，最後來源還原乾淨 |
| 允許的 skip | 無；本次正式三套沒有 skip |
| 尚未跑／仍未通過 | 本 F 完整 native、六 browser、最終帳本、架構收據及正式 wall gates 尚未跑；歷史 R5 的 N64/main 仍紅 |
| 合併狀態 | 非 READY-TO-MERGE；主代理另跑整合來源的統一驗收 |

獨立審查核過產品 42/0、companion 198/0＋補強 19/0、正式 R2 原流 3915/0，以及四行補強自證工具／原流 4183/0。證據目錄 `evidence/geo343-plane-ranges-df66452e/` 封存原始命令、退出碼、完整輸出、環境、來源 SHA、編譯當時的變體 C 和觀測限制。

第一次來源 `7c4a40a…` 的產品正例與新增反證已過，但原兩成員的完整座標突變案例不足，造成 wood 13/14；後兩套因原 100 MiB 空間守門未跑。原 exit 1、精確 assertion、環境限制均保留。補強只加入第三個同第一完整平面的較晚成員，沒有刪測試、放寬原斷言或時限。

歷史 R5（R=`a22df116…`）N64/main = **1.3369644933292553 > 1.3**，本次沒有重抽舊樣本，也不把工作量或 gprof 當成正式 wall 通過。下一步由主代理以整合後可解析來源重產帳本／架構並跑受影響正式驗收；本分支不自行合併 PR。
