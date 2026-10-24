本分支封存固定 R 的一次 K node hint 診斷，供 #338 列車後續效能決策引用。沒有產品或測試修改，也不取代原正式驗收。

| current-state 項目 | 值／結果 |
| --- | --- |
| 原 product/source SHA R | `a22df116c7e9f6b7d074451f1c8052d59e7e4f3e` |
| 受測變體 | R + 私有外部儀表；非 clean R 正式效能樣本 |
| evidence head | `c650099273f502d2161240f977f68e4d9f546ef6` |
| gcc 與單次 N64 bridge | 原退出 0／0；原 `-O1 -fno-inline -pg`，stack 16 MiB |
| 輸出等價 | stdout 逐 byte 等原 R；stderr 扣除唯一診斷 JSON 行後逐 byte 相同 |
| 診斷覆蓋 | 10 家族、overflow 0；原 R 入口計數相符 |
| K 策略、產品、tests、公理 | 未修改 |
| 正式 N64/main | 原 R `1.3369644933292553 > 1.3`，仍紅；本分支未重抽樣 |
| 原 compare | 三個既有 stdout 差異保留，沒有新 graph/guard 差異的修復宣稱 |
| 完整 native／browser／ledger／架構 | 本診斷未執行或重產，不冒稱通過 |
| merge 狀態 | 診斷證據，非產品 READY-TO-MERGE；不開獨立替代 PR |

實測 node calls 2,364,478、hint hits 626,713、conflicts 1,733,685；find existing 1,499,086、新 node 238,679。19/5-byte definition 與 2/4-byte pose 合占 82.36% conflicts，兩者 hint 槽交集 63、聯集 69。這是槽分布，未量 victim→incoming，不能宣稱每次跨家族逐出。

下一步保持 K 產品不動，先由 W 工作線修原 plane/query 熱點並正式重測。現有 hint hits 免 hash，不能無條件提前 full hash。後續 shadow cache 只可先作觀測設計；本次沒有新增策略、數值門檻或正式時間樣本。

完整原輸入、source closure、儀表、命令、環境、退出碼、stdout/stderr、二進位 hash、gmon 與準備失敗收據隨證據封存；原 ELF 保留於雲端原路徑。R1/R2 的非 0 是空間／診斷工具前置分類問題，均未執行 C；不是 mutation kill。詳細限制及獨立審查見 evidence 內檔案。
