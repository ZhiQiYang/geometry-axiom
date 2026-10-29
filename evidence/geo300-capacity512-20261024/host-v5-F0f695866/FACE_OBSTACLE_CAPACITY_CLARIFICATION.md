# FaceObstacle 64：靜審範圍補正

來源：`400a6d0ca50f3aca104fb569c77c8ef753c93355`。原 15/0 靜審 JSON 與 helper 保留，不回寫。

原報告 `truncation_contract` 的「or corrupted input counts」過於寬泛，依 backlog 的對抗審查收斂如下：呼叫者傳入較小 cap 時，原函式會回傳 prefix；**腐敗的 RC count 不在 admission invariant 內，也未獲安全認證**。迴圈的 `n < cap` 約束輸出數量，不約束讀取索引 i；若前項被篩掉，過大的 column_count／beam_count 仍可能越界讀取原陣列。不能用輸出截斷宣稱這種輸入安全。

正式 admission 下仍為至多 32 柱加 32 樑，兩個產品呼叫者都傳入 cap=64，且每個物件至多產生一項；512 支角材不參與此 collector。此結論僅為靜態來源及基數檢查，不包含實際放置、stack 或效能通過。
