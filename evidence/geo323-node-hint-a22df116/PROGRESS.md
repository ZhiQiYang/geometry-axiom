本分支只封存 K 節點 hint 診斷證據，沒有修改產品、tests、帳本、架構或公理。固定原來源 R=`a22df116c7e9f6b7d074451f1c8052d59e7e4f3e`；本次受測變體為「R + 私有外部儀表」，不可冒稱 clean R 正式效能樣本。

已完成一次原 N64 loadfile 診斷，實際 gcc／bridge 均正常退出 0，stack 16 MiB，stdout 與原 R profile 逐 byte 相同；非診斷 stderr 相同。187 私有 source leaves；10 個 provider/key-size 家族，overflow 0。node calls 2,364,478、hint hit 626,713、conflict 1,733,685，find existing 1,499,086、新 node 238,679；三個總入口計數與原 R gprof 相符。

WOOD_DEFINITION 19/5 bytes 與 MEMBER_POSE 2/4 bytes 合占 82.36% conflicts，使用 hint 槽集合交集 63、聯集 69。沒有觀測 victim→incoming 配對，不能把槽集合重疊當成每一次逐出因果。完整索引目前不呈現嚴重長 probe 鏈；詳細原數值與限制見 ANALYSIS.md、原 DIAGNOSTIC.json。

R1 的 workspace 空間 guard 與 R2 的 regex relative-include 分類錯誤均在 compile 前停止，原非 0 收據保留；沒有混成 mutation kill 或重抽正式時間樣本。R3 僅把 30 個原 guarded public K fallback 分類正確，原 185 個 source paths／真正 K headers／gcc flags 全保留，未補 shim。

下一步依主代理決定保持 K 策略不動，先由 W 工作線修原 plane/query 熱點並跑原正式效能。現有 626,713 次 hint 命中免 hash，不能無條件提前 full hash 而忽略成本。可準備後續 shadow 計數方案，但本分支沒有實作或執行該方案。

原 R N64/main=`1.3369644933292553` 仍高於原 1.3 門檻；既有 compare 三個 stdout 差異也沒有被此診斷修復。本分支不是 READY-TO-MERGE 產品驗收，也不宣稱整列車全綠。沒有新增 PR，供主代理一般 merge 證據。
