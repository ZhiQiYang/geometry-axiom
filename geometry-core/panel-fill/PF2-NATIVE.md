# PF-2 原生切片

依看板 2026-10-13 21:30 的指定任務 11，以已採納的 `公理層.md`
D42／D43、I52／I55／I56、R42 為準。舊 tasks/PF.md 的切片順序與 base
由此次看板取代。base 為 main `2004c6c8`；沒有可見 UI 入口。

## 定義與交易

沿用 PF-1 的 `panel-fill-read`、`panel-fill-preview <JSON 檔>`、
`panel-fill-confirm <token>`、`panel-fill-cancel <token>`。
交易 schema 為 `panel-fill-transaction/1`，包含 `expectedRevision` 及 `operations`。
新增兩種 operation：

```json
{"op":"put-panel-fill","value":{
  "id":1,"finishSurfaceId":1,"panel":{"id":"board","version":1},
  "lengthAlong":"v","origin":[0,0],"gap":3,"pattern":"straight",
  "threshold":{"parameterId":90,"fieldId":1}
}}
```

```json
{"op":"delete-panel-fill","id":1}
```

交丁改用 `"pattern":"stagger"`，並加
`"stagger":{"axis":"u","value":20}`。
gap 及 stagger.value 分別接受直接整數，或
`{"parameterId":90,"fieldId":2}`；每欄恰一個來源。
直排不得帶 stagger。threshold 必須明引正值 dimension 欄位；沒有隱藏的 8 mm 常數。
長向指 D26 length 欄位，不依數值大小或正方形猜方向。

材料及參數仍透過各自既有工程交易先發布；不偷偷把 publish-material／put-parameter
塞進只顯示完成面與試排的交易。試排與完成面可在同一 panel-fill 候選一起修改或刪除。
確認沿用候選重验、令牌過期及整包復原。工程參數預覽也顯示重新推導的試排。

## 讀取結果

`state.panelFills[]` 含 `definition` 及每次重算的 `derived`：

- `tiles`：signed i／j、完整板本體矩形 body、whole、按 R42 排序的 fragments。
  每分片有追溯鍵 `[fillId,i,j,fragmentIndex]`、精確 area、逆時針 outer、順時針 holes。
  各環由最小 `(u,v)` 頂點起走，去掉同一直線上的細分點；孔及分片依最小頂點排序。
- `tileCount`、`fragmentCount`、`wholeCount`、`cutCount`：整片／裁切的計數以原板片為單位，
  分片另計。裁切片的尺寸可直接從完整輪廓取得，沒有另藏「窄條」尺寸門檻。
  SSOT 未定窄條警告值；不套用木工模板的收邊下限，不以承接門檻 X 冒充窄條門檻。
- `seamLines`：D43 縫線座標及 signed k；交丁另有板列 band p 及中心到中心 range。
  依 band 與完成面 bbox 的正長度交集列舉，包含上下半縫及負 band；僅點接觸不列。
  這是縫線身分與座標，**不是有效板縫段或承接結論**。
- `obstacles[].panelLayer`：R41／I53 的正體積判定；timberLayer 仍為 null。

`panel_layout_math.h` 同時供有限 PANEL_LAYOUT、無限 REPEAT_PANEL 與 PF-2 使用：
週期、本體起點、整數縫中心、負奇數也適用的最低位元交丁。
有限主格保留原 from／k≥0／停止條件；PF-2 依 R42 使用雙向 signed 板列。
裁切以輪廓、孔及遇障礙矩形的精確座標分格，按正長度邊相接求材料分量，
追蹤材料在左的邊界，拆開接觸孔環；不以 bbox 或面積合併不同分片。

## 容量與保存

最多 16 份試排；每份完整 bbox 列舉最多 1024 個板本體候選，
每片每裁切軸最多 128 個座標、4096 條輪廓細分邊；每份輸出最多 32768 個輪廓頂點、
4096 條縫線。這是公開的執行器資源限制；不聲稱是所有合法幾何的普遍上限。
任何超限在提交前拒絕完整候選，回報 UNSUPPORTED／CAPACITY，不截斷。
超出 D1 的輸出板本體、裁切頂點、世界面上頂點或縫 band 亦明確拒絕。

原生 scene 以 `panel-fill <id> definition-hex <canonical JSON hex>` 保存定義，
在完成面及完整工程／參數來源之後；需先宣告 panel-fill/1、engineering-spec/1、parameters/1。
重開重新驗來源及裁切，沒有板片、縫段或颜色 cache。此切片不提供新的完整專案前端保存入口。
能力保持 `panel-fill-native/1`、`complete:false`，不宣稱整套 panel-fill/1 完成。

## 驗收界線

| PF 項 | 本片實跑範圍 | 留給後續切片 |
|---|---|---|
| PF01 | PF-1 原 frame／孔驗收及試排面上 D1 拒絕 | 板背框架、衍生宿主 |
| PF02 | 101／204、實際有限 PANEL_LAYOUT 及 D29 REPEAT_PANEL 交叉比對 | 無 |
| PF03 | 面內／面外起點、負索引、兩軸交丁奇偶；獨立逐 cell 不漏板／不重板 | 有效接縫與主格整合 |
| PF04 | L 形、孔、障礙切開、僅點相接、孔環接觸拆環與 ordered loops | 有效縫段兩側相鄰關係 |
| PF07 | 定義取消、過期令牌、單次 Undo／Redo、參數候選重算 | 從試排引用的主格／角材 |
| PF08／09 | 2600／2400／2480／2491 的面材層、垂直面、反向 n、開區間 | 角材層及板背宿主 |
| PF11 | 原生 scene 定義 dump／全新 load／逐字重算 | 真瀏覽器 profile／正式完整專案 |
| PF12 | 原有限排板及 D29 不變；完整 native 的既有回歸 | 列車七項 |
| PF13 | 完整枚舉超限、D1 世界頂點、缺厚度及 9.5 厚度拒絕、空障礙不豁免 | 其餘衍生宿主容量 |
| PF16／18 | PF-1 原投影接觸及 PF-2 障礙孔／斷開裁切 | 邊材、角色、I19 候選 |

PF05／06、PF10、PF14／15、PF17、PF19～22 的完整結論屬後續切片，沒有拿提案表當通過收據。
PF23／24 另見 r2.1 amendment 的補充例子，完整驗收屬 PF-3，不列本片已驗項目。
依 P-098 的順序，衍生宿主先由 PF-H 接入，再接 PF-3 effectiveSeams/support、
PF-6 建議、PF-4 網格及 PF-5 的高度／方向／樑；本片各對應結果仍明示 pending。
產品 PR 的正式七項由合併列車驗證；雲端 native 或 sanitizer 不能代替 WSL／瀏覽器收據。
