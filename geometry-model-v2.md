# geometry-model v2 草案（待拍板）

> 目的：把 `current_geometry.c` 的「空間邊界面」拆成對齊 TimberScript 語意的物件模型。
> 狀態：**草案**。標 🔒 的是已拍板，標 ❓ 的等你決定，其餘是我的提議。

## 0. 已定方向（🔒）

- 只走建構子：物件沒有原地修改（無 mutator）。
- 修正 = 同名重新建構（重綁），不是例外通道。
- 重宣告是交易：提交前重驗所有依賴者，任一不過 → 整筆拒絕，World 留在舊狀態。
- 需要同時改多處才合法的修正 → 回場景檔改、reset 重放（檔案是 SSOT，互動列是探索用）。
- 游離面（不屬於任何 Space 的邊界面）**允許**。
- 承載面命名 **`PlacementSurface`**。
- 舊 `surface` 指令**不留**別名；既有 .scene 檔實作時一併改寫成 `placement`。
- 邊界面 fixity 不寫的預設：**全 FIXED**（同 TS）。
- 參考線錨點語意 = **凍結**：place 當下把交點凍成 uv，之後動線不重放角材（寫入公理）。
- 邊界面與承載面**分兩個物件**；DSL 給合體簡寫（一行同時建邊界+承載面）。
- 懸臂：**只有 auto 模式要求兩端頂到擋面**；明寫長度維持可懸空（向後相容）。
- `timber` 長度欄位：明寫 `timber id L A B` 與 auto `timber id A B` **分語法**。
- `at-edge` 定址：`e<索引>` = 外輪廓邊；`h<孔索引>e<邊索引>` = 孔邊。
- auto 角材：place 當下凍結推導出的中線與長度，之後只重驗不重新計算。
- 網格定位是**中心線對齊**（格線座標 = 角材中線），不是角點；
  at-edge 是**貼邊**（footprint 貼齊邊向材料側展一個寬度）。
- 「延伸到最長」與「防碰撞」是同一條公理：跨距 = footprint 不穿過
  任何實體（輪廓外、孔、已放角材）的連續合法區間全程；正面積重疊拒絕、
  零面積相接是合法接觸。

## 1. 物件圖

```
World（畫布 = 容器，現有）
├── Space[]               空間：建構子參數 = 一組邊界面；範圍/封閉由成員推導
├── SpaceBoundarySurface[] 空間邊界面：純局部 2D 多邊形 + 孔 + 邊語意（對齊 TS）
├── PlacementSurface[]    承載面：3D frame + 引用邊界面的輪廓（= 現在的 SpaceBoundarySurface 改名轉型）
├── GuideLine[]           參考線：活在承載面上（現有，不動）
├── ReferenceGrid[]       參考網格：承載面上的參考線座標集（u/v 各一組）
├── Timber[]              角材：放在承載面上；端面擋面檢查查邊界面的 fixity
└── (Room 由 Space 取代)
```

關鍵切分：**邊界面是純局部 2D（不帶世界位置）；世界位置只活在承載面的 frame 上。** 這跟 TS 一致（U/V 是切片自己的座標系，世界對應是匯出偏好），也保住 .c 的三視圖命脈——3D 嵌入沒有消失，是集中到了承載面。

## 2. 資料結構草稿（C）

```c
/* ---- 空間邊界面：空間的實體邊界，純局部 2D ---- */

typedef enum {
    EDGE_FREE = 0,        /* 外側無垂直實體面可釘（挑空/陽角/門洞…） */
    EDGE_FIXED = 1        /* 有：牆、樓板、樑底、柱面、陰角 */
} EdgeFixity;

typedef enum {
    BOUNDARY_UNSPECIFIED,
    BOUNDARY_ROOM_PLAN,       /* 平面圖視角：可有柱/樑投影 */
    BOUNDARY_WALL_ELEVATION   /* 立面 */
} BoundaryKind;

typedef enum {
    CORNER_CONVEX,            /* 外圍凸角：角材只能頂到邊 */
    CORNER_CONCAVE            /* 凹角（反射角）：可有 RC 錨定延伸 */
} CornerKind;

typedef struct {
    Point2 *vertices;         /* 正交多邊形頂點環（UV，順時針或逆時針擇一寫死）*/
    size_t vertex_count;
    /* 每頂點的凹凸角、每邊的 fixity——由環推導/宣告 */
} PolygonLoop2;

typedef struct {
    SurfaceId id;
    BoundaryKind kind;
    PolygonLoop2 outline;               /* 外輪廓 */
    PolygonLoop2 *holes;                /* 內孔（柱投影等）*/
    size_t hole_count;
    EdgeFixity *edge_fixity;            /* 外輪廓每邊一值；孔邊另有 hole_fixity */
    EdgeFixity *hole_fixity;
    /* ROOM_PLAN 專屬 */
    struct { Rect2 rect; CornerClass cls; } *columns;
    struct { Rect2 rect; int64_t z_lo, z_hi; } *beams;
} SpaceBoundarySurface;

/* ---- 承載面：角材釘上去的那面（3D 嵌入在這裡）---- */

typedef struct {
    SurfaceId id;
    SurfaceFrame frame;       /* origin + U + V + N，照舊 */
    SurfaceId boundary_id;    /* 0 = 游離/自帶矩形 */
    SurfaceRegion2 rect;      /* boundary_id == 0 時用的矩形範圍（向後相容）*/
    /* 有效範圍 = boundary 的 outline −（日後）樑投影裁切；查詢時才推導 */
} PlacementSurface;

/* ---- 空間：建構子參數定義全部 ---- */

typedef struct {
    uint32_t id;
    SurfaceId *boundaries;    /* 成員 = 建構時傳入，之後不可變 */
    size_t boundary_count;
    /* 推導結果（只讀衍生）：各軸 [min,max]、封閉與否 */
    int64_t room_min[3], room_max[3];
    bool closed;
} Space;
```

## 3. DSL 語法草案

```
# 邊界面：局部 2D 多邊形。space 欄位可有可無（游離）
boundary 1 kind room_plan outline (0,0) (4000,0) (4000,3000) (0,3000) fixity F F F F
boundary 1 hole column (1800,1200) (2200,1600)          # 追加孔；同一物件的續寫
boundary 1 hole fixity F F F F

# 承載面：3D frame + 掛邊界（不掛就自帶 rect，= 現在的 surface 行為）
placement 1 on boundary 1 origin 0 0 2500 u +x v +y
placement 2 origin 0 0 2500 u +x v +y rect 0 0 4000 3000   # 向後相容寫法

# 空間：建構子參數 = 邊界面清單。建構當下跑槽位一致性，不過就拒絕
# 零成員 = 空容器（無界、恆非封閉）；加面 = 同 id 重宣告成員清單
space 1                       # 空容器
space 1 boundary 1 2 3 4      # 重宣告 = 更新成員（仍過建構驗證）

# 畫布座標：展示中繼資料，不參與幾何推導；存 World、跟 dump 走
canvas-pos boundary 1 100 200   # 面卡位置
canvas-pos space 1 500 60       # 空間卡位置

# 合體簡寫：一行同時建邊界面 + 承載面（兩物件、一次宣告）
surface 1 origin 0 0 2500 u +x v +y outline (0,0) (4000,0) (4000,3000) (0,3000)
#   等價於 boundary 1 outline (...) + placement 1 on boundary 1 origin ...

# 現有指令不動；place/guide 的目標面一律是承載面
#   舊 `surface id ox oy oz +x +y min min max max` 指令移除，
#   五份既有 .scene 改寫為 placement … rect …
guide / move / reset  照舊

# 參考網格：一個物件 = 一組參考線座標（🔒 網格即參考線集合）
grid 3 on 1 u 300 900 1500      # u 座標集（線沿 V 走）
grid 3 on 1 v 600 1200          # 同 id 第二行補另一軸

# 角材：明寫長度與 auto 長度語法分開（🔒）
timber 1 1800 27 33             # 明寫 L=1800，只能 at / at-guides
timber 2 27 33                  # auto，只能 at-grid / at-edge；L 由跨距推導

# 放置（明寫長度）：角點錨法
place 1 on 1 at 500 300 +u +n
place 1 on 1 at-guides 1 2 +v +n

# 放置（auto）：中心線錨法，長度 = 中線上連續合法區間全程
place 2 on 1 at-grid 3 u 2 +v +n          # 中線 = 格線座標
place 2 on 1 at-edge e3 -v +n             # 貼外輪廓第 3 邊
place 2 on 1 at-edge h1e2 through 1500 +u +n  # 孔 1 第 2 邊 + 區間選擇器
```

## 4. 不變量（公理層清單初稿）

構造保證（建構子/守門員擋）：
1. 承載面 frame：U、V 單位正交且 U×V=N（現有）
2. 邊界面輪廓：正交、閉合、非自交、無零長邊；孔全在外輪廓內且互不重疊
3. fixity 數量 = 邊數，缺一拒絕；不寫預設全 FIXED（🔒）
4. Space：成員面互不矛盾（現有槽位邏輯升格為建構前置條件）；非法空間建不出來；
   零成員空容器合法（畫布「先建空間再放面」用）
5. 角材放置：整個 A0 面在承載面有效範圍內且不跨孔（取代現在的對角點凸性捷徑）
6. 端面只頂自由邊 → 拒絕（V_FREE_EDGE_END）
7. 重宣告：新物件建得出來 + 所有依賴者重驗全過，才提交；否則整筆回滾
8. 參考線 offset 恆在範圍內（現有）；多邊形後參考線可能被截成多段——**行為改變點**
9. 網格座標嚴格遞增、落在承載面外接區間內（🔒）
10. 同面角材 footprint 正面積不得重疊（端邊相接 = 零面積 = 合法）（🔒）
11. auto 角材兩端各需恰好一個涵蓋全寬的擋面：輪廓邊、孔邊、已放角材側面；
    無擋面/多擋面/擋面是 FREE → 拒絕（🔒 auto 模式才要求兩端頂死）

推演規則（寫死，不靠測試）：
- 拾取 = 畫家演算法最後畫的命中（現有，補寫成規則）
- 移動參考線不重放以其交點為錨的角材（🔒 凍結語意）
- A0 = 接觸面（現有語意，補寫）
- auto 跨距：切點（輪廓+孔+已放 footprint）→ 逐 cell 合法檢查 → 合併
  → through/at-edge 接觸範圍選段（歧義列舉拒絕）→ 兩端擋面驗證
- auto 中線與長度 place 當下凍結；revalidate 只重驗不重算（🔒）

## 6. 已知行為差異（相對現版）

- 參考線在多邊形上可能被截斷成多段：GuideLine 的「線段」從一段變成段列，`guide_line_get_local_segment` 回傳型別要改，三視圖/拾取跟著改
- 放置檢查從「兩角點」變「矩形 ⊆ 多邊形 − 孔」
- scene 檔 `surface`/`edge` 語意改變：edge 由邊界面輪廓推導，`edge id 面 種類` 的四種 enum 寫法退場
