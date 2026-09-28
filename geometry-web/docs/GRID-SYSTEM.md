# 畫布上的無限網格系統

依 `公理層.md` D29／D30／I37／R32 與 `geometry-core/INFINITE-GRID-PROPOSAL.md`。驗收見 BACKLOG GEO-215；GEO-214 是先前有限排法的歷史紀錄。

## 建立網格

在物件畫布選「網格系統」，輸入名稱、u/v 兩方向的間距與基準。每條格線向兩端無限延伸，格線以正負整數索引無限排列，沒有條數、總寬或總高。至少設定一軸；cell 對齊需要兩軸。

等距來源 `repeat PHASE STEP` 的第 k 條線位於 `PHASE+k*STEP`。面材與縫來源 `repeat-panel PANEL gap GAP from ANCHOR` 的週期為 `PANEL+GAP`，縫中心相位為 `ANCHOR+PANEL+floor(GAP/2)`。

網格不需要邊界、放置或材料。卡片位置只整理工作區。編輯工作區支援平移、縮放；過密時標示抽樣，格距、索引及 cell 大小不隨抽樣改變。

## 與邊界對齊

建立「網格配置」，選擇來源與邊界，尚未放置的邊界也可使用。在圖上選實際外輪廓或孔洞頂點、任意 cell，再指定 cell 內的角、邊中點或中心。本版 u 向右、v 向下；左上角為 (0,0)，中心為 (1/2,1/2)。

確認後配置成為獨立物件，保存來源、邊界、穩定頂點身分、cell 正負索引及精確比例。修改間距仍對齊同一個 cell 位置；放大邊界只增加取用的線，不重編索引。同一來源可建立多個配置。

首次選點在同一交易內初始化頂點身分。之後移動頂點或擴大邊界使用保留身分的編輯；引用中的頂點不能直接刪除。存檔保留編號高水位，不把刪除過的身分分配給新點。整數 mm 仍是尺寸基準；半毫米等結果明確拒絕，不四捨五入。

## 套用到面

配置可套用到使用同一邊界的已放置承載面。可見段由核心按邊界扣孔裁切，無限線本身不受裁切影響。角材引用真正的 signed 索引，不引用抽樣清單的位置。

子網格引用真正的 cell (i,j)，四邊為 i/i+1 與 j/j+1；外接框不冒充格線。超過 4096 格不逐格列舉，可直接指定正負 cell 索引。座標與合法性由核心預覽檢查。

變更使用預覽／確認交易；違規時保留原世界。復原重做包含依賴。被使用的來源、配置與頂點不能直接刪除。

## 保存與相容

正式「保存」的 .gcanvas 包含未套用的來源、配置、頂點身分、cell、比例與卡片位置。重開保留關聯，不另存失去來源的展開線段。

舊 explicit、series start step count、panel 及 from-system origin 保持有限排法，標示「有限排法」，不自動轉成無限網格。新建立流程使用無限來源。本版同名軸對齊，不旋轉、鏡射、縮放，也不自動生成角材。

## 保存語法示例

```text
boundary 1 outline 100,200 2500,200 2500,1800 100,1800
boundary-vertex-keys 1 outer 1 2 3 4 next-key 5
grid-system 7 name-hex 36303078343030 main-along none u repeat 0 600 v repeat 0 400
grid-binding 3 on-boundary 1 from-system 7 vertex-key 1 cell -2 1 anchor 0 1 0 1
canvas-pos grid-system 7 120 80
canvas-pos grid-binding 3 450 80
```

唯讀查詢：`grid-query system|binding|grid ID rect U0 V0 U1 V1 mode exact|sample limit N`。精確查詢超量回報所需數量，抽樣查詢明示 stride；查詢容量不足不使來源失效。
