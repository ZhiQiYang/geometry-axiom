# GEO-300 前置進度

目前候選產品 SHA：`c493b7315d0cd3b16014add96af969c49ebf4660`。目前基底：`codex/train-337-continue-20261024` 的 `a6072dde8eac809e93ccd9373946dea98fa5c362`。本分支只有 `codex/geo300-prerequisites-20261024` owner 寫入，沒有寫正式 train。

| 項目 | 結果 |
|---|---|
| 一般 merge 新 train | exit 0，零衝突；沒有 rebase／force push |
| 相對新基底的非 evidence 差異 | 恰三個原產品／測試 leaf |
| 靜核 | 108 項／0；23 個 control 錨點全部唯一 |
| 合流獨立對抗靜審 | 58 項／0 findings，範圍限來源與控制設計 |
| 原九方法＋新一方法／五新反證 | 本候選全部 UNRUN |
| 操作及效能 | UNMEASURED，沒有新數值門檻或加速倍率聲稱 |
| shared expected count 9→10、架構及全帳本 | 待主代理合流處理，子代理未改或重產 |

原產品算法保持已審的 active bitmap／最後一次穩定壓緊；超過既有 face capacity 保原 memmove 後備。最壞配對 O(F²)、insertion sort、call-growth、cut-list 平方儲存都未解決，不冒稱容量 512 前置已完成。

首版 S576d3e1b／Eea3187ac 的 108 靜查含一個既存 free-end 三命中失敗，原 raw 完整保留在歷史封包。新基底已採 root 的精確單行維護，故本輪全部錨點唯一；F4f 的原九方法 1/0/1/0 證據只證該單行 leaf，不挪作本候選通過。

下一步依主代理排程，在 noWood、faces43、GEO260 retry 之後取得 C 時槽，固定本候選新 SHA 跑完整十方法、所有原十八與五新控制，以及受影響 source／Reading A 原裁判。整個優化撤回預期仍語意等價，不冒作被殺；成本觀測另排。所有正式收據需要原命令／退出碼／完整輸出／環境／SHA 並經另一代理核對。
