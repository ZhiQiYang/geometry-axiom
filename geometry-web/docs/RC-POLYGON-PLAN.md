# RC 柱樑 + 正交多邊形面內編輯規劃(SSOT)

> 立案 2026-09-13;同日依使用者補充需求(B-1 投影規則、B-2 三維物件、B-3 一等物件)修訂 v1.1。
> 本檔是實作 agent 的**唯一事實來源**:任何與本檔衝突的推測,以本檔為準;
> 本檔沒寫的設計取捨,不得自行決定,寫進 §9 決策佇列停手等使用者。
> 上位檔:`../公理層.md`(驗收基準)、`../geometry-model-v2.md`、`UI-REDESIGN-PLAN.md`(既有 UI 架構,其 §0/§5.1/§8 全部沿用)。

---

## 0. 給實作 agent 的工作守則(先讀)

1. **真相在 bridge,不在瀏覽器。** 沿用 UI-REDESIGN-PLAN §5.1 分層:快照 + 相機 + 選取 + 拖曳暫存,所有修改走 `line <DSL>`。
2. **C 端本規劃可改**(`current_geometry.c`、`web_bridge.c`),但每個新 DSL/bridge 指令必須同時做到(缺一不算完成):
   a. 語法寫進本檔附錄 A;
   b. `../公理層.md` 同步加定義(D)與不變量(I)/推演規則(R);
   c. 交易式重驗,參照 `world_replace_object` 與 `apply_delete_line` 的做法(失敗整筆回滾);
   d. `canvas_test.js` 加 case;
   e. 新增變異/邊界 `.scene` 夾具(`_mut_*.scene` 慣例,非法案例要斷言拒絕);
   f. `web_bridge.c` 的 `render`/`objects`/`dump`/`newid`/`delete`/`pick`/`obstacles` 同步;
   g. `geometry-guide/make_guide.py` 重跑且 `check_panels.py` 全過。
3. **每個階段都有裁判**(§7)。沒過裁判的階段不算完成,不得進下一階段;commit 訊息第一行「RC/多邊形 Phase N:<摘要>」附裁判摘要。
4. **核心與前端衝突時,核心贏。** 正交、整數 mm、交易語意、凍結語意不可在前端繞過。
5. 讀檔守則:大檔用 `sed -n`/`grep -n` 分段讀,不整檔讀。
6. 回報格式:每階段結束 ≤60 行,列「改了哪些檔 + 裁判摘要(pass/fail 數與失敗項)+ 未做/卡住」。不貼大段原始碼。

---

## 1. 背景與目標

- **主題 A**:面內工作區目前只能拖頂點/拖邊/開口/凹口。目標是讓空間邊界面的外環能用「畫」的方式建立任意正交多邊形,並補上尺寸導向的編輯(鍵入長度、邊長清單、對齊吸附、參數化凹口、形狀庫、點邊切 fixity)。
- **主題 B**:空間需要 RC 柱與 RC 樑。它們是:
  - **三維物件**(B-2):World 裡的房間座標軸對齊方塊(AABB,x/y/z 三個整數區間),不是面上的記號;
  - **空間的障礙物、不是成員面**(R3):掛在空間下(可游離,見 §9 Q7),不影響 closed;
  - **物件畫布的一等物件**(B-3):有卡片、canvas-pos、contains 連線、檢視器表單;
  - **投影是推導+明確套用**(B-1/B-2):`obstacles <face_id>` 回傳各面的 uv 鬼影分類,面內畫半透明鬼影不改 boundary;使用者確認清單後「套用」才轉真幾何,且**套用後與柱樑無連結**(快照式,R7)。
- 主題 A 全程不改 C 端;主題 B 需要 C 端新物件、新指令、新 STYLE。

## 2. 🔒 已拍板決定(來自交辦文,不得改)

| # | 決定 | 含義 |
|---|---|---|
| R1 | 柱 = 矩形足跡 w×d;預設高度 = 地板到樓板 | 高度可由空間槽位推導;`z z0 z1` 可明寫覆寫 |
| R2 | 樑 = 軸向桿件,寬×深;頂面貼樓板 | 樑底 = 頂面 − 深;走向軸平行(x 或 y) |
| R3 | 柱樑是**空間的障礙物**,不是空間成員面 | 不進 `space … boundary …` 成員清單;不影響 closed 推導 |
| R4 | 預設尺寸按鈕:柱 500/600/700/800 見方;樑 300×500、350×600、400×700(寬×深,mm) | 物件庫與空間工作區共用;**加自訂 w×d 輸入**(🔒 Q3) |
| R5 | 衍生/套用操作必須是**使用者明確觸發** | 按下前先列出會改動的面與改法,確認才送;不自動、不連動 |
| R6 | 柱樑要出現在三視圖、投影面板、物件畫布 | `render`/`pick`/`objects`/`canvas-pos`/`newid` 全鏈 |
| R7 | 投影套用是**快照式** | 套用當下以推導值生成孔/凹口/拆分/新面;之後柱樑變動不回寫(同凍結語意)。重套用 = 先還原或再對新幾何重算,流程見 §5.B.6 |
| R8 | 柱樑是房間座標 AABB | x/y/z 三個整數區間;進 undo 快照、dump、loadfile、delete |
| R9 | 投影規則只有已放置面能接收 | 平面/立面由 **placement 法向**決定(±Z=平面,水平=立面);boundary 的 `kind` 只當驗證用(room_plan 可警告) |
| R10 | 孔/凹口/拆分是**同一條「足跡與輪廓接觸關係」規則**的退化 | 實作成單一函式,五種接觸情況用夾具全覆蓋;新生成的邊 fixity 一律 F |
| R11 | z 推導失敗 = 報錯不猜 | 省略 z 時從所屬空間 ±Z 槽面高程推;沒有空間或推不出 → 拒絕 |
| R12 | DSL 語法(交辦文給定) | `column id [in <space>] at x y size w d [z z0 z1]`、`beam id [in <space>] along x\|y from a to b at c width w depth d [top z]` |

## 3. 常規決定(我定的,屬工程慣例;若使用者反對可改)

| # | 決定 | 理由 |
|---|---|---|
| P1 | 單位一律 mm 整數;尺寸標註顯示 mm | 核心無浮點 |
| P2 | `objects` 回傳加 `columns[]`、`beams[]` 兩個**獨立陣列**,不併入 `faces` | B-3 明定;卡片層各自處理 |
| P3 | `canvas-pos` kind 擴充 `column\|beam`;`newid` 加 `column`/`beam` 命名空間 | B-3 明定;`WORLD_MAX_CANVAS_POS` 同步加大 |
| P4 | `delete column|beam <id>` 擴充既有 delete 指令表 | Q1 已建的模式 |
| P5 | 重畫外環期間孔環先**隱藏不編**,送出時一併重宣告 | 孔是否還在新外環內由核心 I2 驗;不過 → toast |
| P6 | 畫邊鍵入長度與邊長清單,傳播規則 = 既有 `applyVertexEdit`/`applyEdgeEdit` 約束傳播 | 已在核心語意內,不另造 solver |
| P7 | 三視圖柱樑用新 STYLE 常數(接在現有 0–12 後):13=COLUMN、14=BEAM;柱=實心填色輪廓、樑=深色描邊 | web 端 STYLE 表與 app.js 同步改,防錯位(§8-11) |
| P8 | 空間工作區「平面示意圖」= 自定 SVG 平面投影(吃 space bbox + 柱樑足跡),不重用 `render` 仰視圖 | 仰視圖含全部面太雜;平面示意只需 XY 足跡 |
| P9 | 變異夾具沿用 `_mut_*.scene` 慣例,放 repo 根目錄 | 既有命名 |
| P10 | `obstacles <face_id>` 鬼影在面內編輯器用半透明 hatch/虛線層畫,**不改 boundary** | 鬼影是推導視覺;套用才成真幾何 |
| P11 | 柱樑物件庫卡片命名沿用「柱 N」「樑 N」 | 核心無名稱欄位(C7) |

## 4. 非目標(明確不做)

- 柱樑的結構計算、配筋、載重——永遠不做。
- 柱樑與角材(timber)的自動碰撞檢查、自動扣料——本層只存資料。
- 非軸對齊柱樑(斜柱、斜樑、圓柱、變截面)。
- 柱樑變動後對已套用面幾何的**自動回寫**(R7 快照式,只能手動重套用)。
- 任意多邊形(非正交)、樣條、倒圓角。
- 柱樑的三維拖曳/3D 編輯器;編輯一律走檢視器表單重宣告。

## 5. 規格

### 5.A 主題 A:正交多邊形面內工具(全部走 `boundary` 重宣告,不改 C 端)

| 工具 | 快捷鍵 | 行為 | 送出 |
|---|---|---|---|
| 選取/拖曳 | v | 既有 + **單擊邊(無位移)= 切換該邊 fixity** F↔X;位移>閾值才是拖曳 | `boundary … fixity …` |
| 重畫外環 | e | 軸鎖點擊逐點畫:起點後每段自動鎖水平/垂直;點回起點或 Enter 閉合;Esc 取消;即時預覽 + 各段長度標註;送出前**自動去共線頂點**;孔環暫存一併重宣告(P5) | `boundary <id> outline … [hole …] [fixity …]` |
| 鍵入長度 | (重畫中)數字鍵 | 畫邊途中按數字 → 游標旁浮動輸入框累積;Enter = 該段長度定為輸入值,繼續下一段;Esc 清輸入不取消 | 同上 |
| 參數化凹口 | i | 點邊後彈小對話框:寬 w、深 d(預設沿用 Q2 自動值);確認 → 構造 4 頂點凹口重宣告 | `boundary …` |
| 形狀庫 | (對話框) | 工具列「形狀」鈕 → 對話框選形(L/U/T,🔒 Q2)+ 參數輸入 → 生成外環取代現外環 | `boundary …` |
| 檢視器邊長清單 | — | 右欄「邊」清單:每列 邊i、方向、長度 input、fixity 鈕;改長度 → 既有約束傳播(P6),重宣告 | `boundary …` |
| 拖邊對齊吸附 | (select 拖邊中) | 移動邊座標對其他頂點的同 u/同 v 吸附(閾值隨 zoom 反比);命中時畫對齊參考線 + 相鄰邊即時長度標註 | 放開 → `boundary …` |

錯誤政策不變:核心拒絕 → toast 原文 + 回到快照。

### 5.B 主題 B:RC 柱與 RC 樑

#### 5.B.1 物件模型(C 端)

```c
typedef struct {
    SurfaceId id;
    uint32_t space_id;          /* 0 = 游離(§9 Q7) */
    Coord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;   /* AABB,房間座標 */
} RcColumn;

typedef struct {
    SurfaceId id;
    uint32_t space_id;
    int axis;                   /* 沿 x 或沿 y */
    Coord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;   /* AABB;頂面 z_hi = 樓板或明寫 top */
} RcBeam;
```

World 加 `columns[WORLD_MAX_RC]`、`beams[WORLD_MAX_RC]`(上限暫定各 32);undo 快照自動涵蓋(World 是 POD memcpy)。

#### 5.B.2 DSL(🔒 R12)

```
column <id> [in <space_id>] at <x> <y> size <w> <d> [z <z0> <z1>]
beam   <id> [in <space_id>] along x|y from <a> to <b> at <c> width <w> depth <d> [top <z>]
```

- `at x y` = 足跡**左下角**;`along x from a to b at c` = 沿 x 軸、x∈[a,b]、y∈[c−w/2, c+w/2](中心線對齊,同 at-grid 慣例;w 為奇數時多的 1mm 在 +y 側,I13 慣例)。
- 省略 `in <space>` = 游離(**允許,但 z/top 必須明寫**,🔒 Q7);省略 `z`/`top` → 從所屬空間 ±Z 槽推導,推不出 → 拒絕(R11)。
- 同 id 重宣告 = 交易式重綁(檢視器表單修改走此路)。
- `delete column|beam <id>`;`newid` 加 `"column"`/`"beam"`;`dump` 行序:`… space → column → beam → canvas-pos`。

#### 5.B.3 不變量(附錄 B 詳列)

- I15 柱足跡 ⊆ 所屬空間平面範圍(游離柱不檢此條);兩柱正面積不得相交(邊相接合法)。
- I16 樑走向軸平行(語法保證);樑足跡 ⊆ 空間平面範圍;柱樑、樑樑相交不檢。
- I17 空間重宣告使推導範圍縮小 → 柱樑一併重驗,不過整筆回滾;刪空間 → 柱樑變游離(不跟著刪)。

#### 5.B.4 三視圖與 pick

- `scene_draw_view` 對每個柱/樑,把 AABB 用 `VIEW_FRAMES[v]` 的右向量/下向量取區間,畫投影矩形;新 STYLE 13/14(P7)。
- `pick` 命中柱樑回傳 kind 與描述;`objects` 回傳 `columns[]`/`beams[]`(id、space、六區間、cx/cy/hasPos)。

#### 5.B.5 面上投影 = `obstacles` 推導(鬼影)

- 新 bridge 指令 `obstacles <face_id>`(face_id = boundary id):
  1. 找該 boundary 的 placement;沒有 → `{ok:false}`(R9 只有已放置面能接收)。
  2. 法向 ±Z → 平面投影;法向水平 → 立面投影。
  3. 對空間內每個柱/樑,把 AABB 投影到該面 uv 空間得矩形,並用**單一接觸分類函式**(R10)判定:
     - 平面:柱足跡在輪廓內部 → `hole`;貼一邊 → `notch`;貼兩邊(角落) → `corner`;樑 → `strip`(貫穿條帶)。
     - 立面:貼牆柱 → `split`(拆左右);搭牆樑 → `top_notch`(w×d 頂邊凹口);邊樑 → `top_drop`(整段降樑深)。
  4. 回傳 `{ok,face,kind:"plan"|"elevation",items:[{id,type:"column"|"beam",cls,rect:[u0,v0,u1,v1],…}]}`。
- 面內編輯器:有 placement 的面自動(或開關)顯示鬼影層——半透明 + 分類圖例,**不進 boundary**(P10)。

#### 5.B.6 套用(apply)= 鬼影轉真幾何(使用者明確觸發,R5/R7)

- 面內編輯器「投影」區:列出 `obstacles` 回傳的每筆改法(「柱1 → 孔 400×400 @(1800,1200)」「樑2 → 拆兩片」),使用者勾選/確認後送出。
- 套用落點 = **新 C 指令 `apply-proj`**(🔒 Q4):單一函式完成分類+改寫+空間成員重宣告,整筆交易,失敗全回滾。
- 套用結果(同一分類函式):
  - `hole` → 加孔環,fixity 全 F;`notch`/`corner` → 外環加凹口頂點;
  - `split`(立面貼牆柱)→ 牆拆成左右兩片 boundary + 柱露出側面生成新立面 boundary;**原 id 給面積最大片**(🔒 Q9),其餘新 id;
  - `strip`(樑過天花)→ **預設不裁**(🔒 Q8),清單中勾選才執行:天花拆兩片 + 樑底生成新平面投影面(z=top−深)+ 樑兩側生成新立面;
  - `top_notch` → 牆頂邊留 w×d 凹口;`top_drop` → 牆頂邊整段降樑深(外環重寫)。
- **拆分會改 id 與空間成員**:原 boundary 拆分後,空間成員清單以 `space <id> boundary …` 重宣告更新(原 id 給哪片見 §9 Q9);整串走 `mutate`,失敗回滾。
- **重套用流程**:套用後與柱樑無連結(R7)。重套用 = 使用者先把上次產生的孔/凹口/拆片手動復原(或 undo),再對新鬼影重按一次;UI 在按鈕旁提示「上次套用的結果不會自動撤銷」。

#### 5.B.7 物件畫布一等物件(B-3)

- 物件庫:「＋柱」「＋樑」按鈕 + 預設尺寸下拉(R4);建立 → 卡片(`.ocard`,`dataset.kind="column"|"beam"`)。
- 卡片預覽:柱 = 足跡矩形 + 高度標註;樑 = 跨度條帶 + 寬×深標註。
- 檢視器:位置/尺寸表單 → 同 id 重宣告(交易式);雙擊卡片 = 選取並聚焦檢視器(🔒 Q10,不做小型工作區)。
- `space → column/beam` contains 連線(空間卡 → 柱樑卡);空間工作區「收構件」= 把游離柱樑 `in <space>` 重宣告,移除 = `in` 改游離或 delete。
- 篩選加「柱」「樑」兩類;計數、搜尋同步。

#### 5.B.8 空間工作區

- 平面示意圖面板(P8):空間 XY 範圍 + 柱足跡(實心 + 尺寸標)+ 樑條帶(走向 + 寬度標);點放柱、拖放樑。
- 左欄「構件」清單:柱樑各一列(id、尺寸、所屬、✕ 刪除);「收構件」勾選游離柱樑加入。

## 6. 階段計畫

每階段:範圍 → 裁判 → DoD。**過閘才 commit、才進下一段。**

> 執行狀態(2026-09-14):Phase 1 `f7c3318` · Phase 2 `1cfd172` · Phase 3 `b068b2d` ·
> Phase 4 `3cfc810` · Phase 5 `9fa30e2` · Phase 6 `ce02a80` — 全部過閘提交。

### Phase 1 重畫外環 + 形狀庫(純前端)

- `index.html` 工具列加 `data-face-tool="redraw"`(e)+「形狀」鈕 + `#shapeDialog`;`app.js` 軸鎖畫點狀態機(預覽、長度標註、去共線、Enter/點起點閉合、Esc 取消)、形狀庫對話框。
- 裁判(cdp_test 新段 P9):L 形 6 點閉合 → 外環 6 頂點全正交;Esc → 不變;共線點被去掉;形狀庫 L 4000/3000/臂 1000 → 6 頂點、面積正確。
- DoD:全 ✓;兩套裁判綠;DOM-CONTRACT 補新 id。

### Phase 2 尺寸導向編輯(純前端)

- 鍵入長度、邊長清單、拖邊對齊吸附+標註、參數化凹口對話框、單擊邊切 fixity。
- 裁判(P10):邊長改 4000→5000;拖邊吸附同 v 頂點;凹口 w800 d400 尺寸正確;單擊翻 fixity、拖曳平移不誤觸;鍵入 1500 → 段長恰 1500。
- DoD:全 ✓。

### Phase 3 C 端柱樑物件(§0-2 清單全做)

- `current_geometry.c`:`RcColumn`/`RcBeam`、World 陣列、`column`/`beam`/`delete`/`newid`、dump、revalidate;`scene_draw_view` AABB 投影 + STYLE 13/14;`pick` 命中。
- `web_bridge.c`:`objects` 加 `columns[]`/`beams[]`、STYLE 同步;`canvas-pos` kind 擴充。
- `公理層.md`:D13/D14、I15-I17、R7/R8(快照式、分類函式)。
- `canvas_test.js` 新 case;夾具:`_mut_col_overlap.scene`、`_mut_col_outside.scene`、`_mut_beam_diag.scene`(語法拒絕)、`_mut_col_noz.scene`(推不出 z 拒絕)。
- `make_guide.py` 重跑、`check_panels.py` 過。
- 裁判:canvas_test 全 pass;bridge 手驗 column/beam/delete/dump→loadfile→dump 逐字相同;cdp_test 不敗壞。
- DoD:兩套綠 + 夾具過 + 導讀過檢。

### Phase 4 物件畫布一等物件(前端)

- 物件庫「＋柱」「＋樑」+ 尺寸下拉;卡片、預覽、檢視器表單(重宣告)、canvas-pos 拖曳、contains 連線、篩選/搜尋/計數。
- 裁判(P11):建柱→卡片出現→拖卡片→dump 含 `canvas-pos column`;`in` 空間→edgeGroup 連線;搜尋「柱 1」命中;刪除→卡片消失。
- DoD:全 ✓;DOM-CONTRACT 更新。

### Phase 5 空間工作區 + obstacles 鬼影(C bridge + 前端)

- `obstacles <face_id>` bridge 指令 + 核心分類函式;面內鬼影層;空間工作區平面示意圖、構件清單、收構件、點放柱/拖放樑。
- 裁判(P12):五種接觸情況的 `obstacles` 預期輸出(獨立柱=hole、貼牆柱=split/notch、角柱=corner、搭牆樑=top_notch、邊樑=top_drop);鬼影元素計數;點放柱/拖樑→dump;越界→toast。
- DoD:全 ✓ + `.scene` 夾具各一最小案例。

### Phase 6 套用(apply)按鈕

- 確認清單 UI + 套用指令(落點依 §9 Q4)+ 空間成員重宣告 + 重套用提示。
- 裁判(P13):柱→天花孔/凹口/角落凹口各一;貼牆柱→牆拆兩片+新立面+成員更新;搭牆樑→頂邊凹口;邊樑→頂邊整段降;樑過天花裁/不裁兩路徑;拆分後 `objects`/`render` 一致。
- DoD:全 ✓。

### Phase 7 收尾

- README/BACKLOG 更新、DOM-CONTRACT 補齊、§9 回寫、verifier 對 §5 逐條 read-back。
- 裁判:兩套測試全綠 + verifier 無缺口。

## 7. 測試合約

- 沿用 UI-REDESIGN-PLAN §7:同一支 cdp_test.js 加段(P9–P13),計數 ✓/✗;canvas_test.js 加 C 端 case;新 DOM 依賴進 DOM-CONTRACT.md。
- C 端夾具命名:`_mut_col_*.scene`、`_mut_beam_*.scene`;接觸分類最小案例:`_rc_col_free.scene`、`_rc_col_wall.scene`、`_rc_col_corner.scene`、`_rc_beam_cross.scene`、`_rc_beam_edge.scene`。
- **重放保真**:每個含柱樑的夾具 `dump → loadfile → dump` 必須逐字相同(B-2 裁判)。
- **三視圖比對**:以 SVG 後端輸出比對柱樑投影矩形(預期 rect 值寫進測試)。
- 跑法不變:`python serve.py 8765` + `node canvas_test.js direct` + `node cdp_test.js`。

## 8. 已知陷阱(本期新增,沿用前期 §8 全部)

1. 正交多邊形改邊長不是「動一個點」——垂直於移動軸的邊要整串傳播(P6);直搬 v_{i+1} 會造斜邊被核心拒絕。
2. 畫點去共線:連點同線上的點,送出前必須去掉,否則核心 I2 拒絕。
3. `column/beam` 的 `in <space>` 是**空間 id**,與 guide/grid 的 `on <placement>` 不同層,解析器勿混。
4. z 推導依賴空間 ±Z 槽;半開放空間推不出 → 拒絕不猜(R11)。
5. 樑頂貼樓板:沒有天花成員時上界未定 → `top` 必須明寫,否則拒絕。
6. dump 行序:柱樑在 `space` 之後(依賴順序 I9);`canvas-pos` kind 值擴充後,舊場景檔不含柱樑行 → 向後相容(讀不到就沒有)。
7. `objects` 的 `columns[]`/`beams[]` 是獨立陣列,不進 `faces`/`spaces`;前端卡片層要各自處理 dataset.kind。
8. 孔 vs 凹口 vs 拆分是同一分類函式的退化:足跡完全在內=hole、貼一邊=notch、貼兩鄰邊=corner、貫穿/貼對邊=split;**角點相切=退化拒絕**,不猜。
9. `pick`/`render` ops 序:柱樑畫在面之後(畫家演算法 R1)hover 才拿得到。
10. 邊長清單 index 與 `data-face-hit="e:0:i"` 的邊序一致(頂點 i → i+1)。
11. **STYLE 表錯位前例**:UI-REDESIGN-PLAN §8-11 已記;新增 STYLE 13/14 時 C 端 enum、`web_bridge.c` 映射、app.js `STYLE` 表三處同步,測試以「柱 ops 的 s 值」斷言。
12. 鬼影是推導顯示不是資料:`obstacles` 結果**不進** `boundary`,前端不得把鬼影 rect 當已套用。
13. 拆分改 id:拆出多片後 `space … boundary …` 成員清單要一併重宣告,整串在 `mutate` 裡,失敗回滾;卡片 canvas-pos 對被退役的 id 要清掉。
14. `obstacles` 的 face_id 是 **boundary id**;游離面(無 placement)→ `{ok:false}`。

## 9. 決策佇列(2026-09-13 全部拍板 🔒)

| # | 問題 | 決定 | 落點 |
|---|---|---|---|
| Q1 | 柱樑 DSL 語法與歸屬 | 已由 B-2 交辦文給定 | R12 |
| Q2 | 形狀庫範圍 | **L/U/T 三種**,架構留擴充 | Phase 1 |
| Q3 | 預設尺寸 | 照 R4 四+三顆鈕,**加自訂 w×d 輸入** | Phase 4/5 |
| Q4 | 套用落點 | **新 C 指令** `apply-proj`,單一函式交易重驗含空間成員更新 | Phase 6,附錄 A |
| Q5 | 數值輸入互動 | **游標旁浮動輸入框**,數字累積 Enter 定長 | Phase 2 |
| Q6 | 柱樑高度語意 | 已由 B-2 給定 | R11 |
| Q7 | 柱樑可否游離 | **可,但 z 必須明寫** | §5.B.2 |
| Q8 | 樑過天花條帶預設 | **預設不裁**,套用清單中使用者勾選才裁 | §5.B.6 |
| Q9 | 拆分後原 id 歸屬 | **原 id 給面積最大片**,其餘新 id | §5.B.6 |
| Q10 | 柱樑卡片雙擊 | **只開檢視器**,不做小型工作區 | §5.B.7 |

## 10. 交辦 prompt(拍板後直接貼)

```
繼續執行 D:\knowledgebase\geometry-web\docs\RC-POLYGON-PLAN.md 的 Phase <N>。
先讀該檔 §0、§2、§3、§5、§6 Phase <N>、§7、§8、附錄 A/B;原始碼用 sed -n 分段讀。
規則:真相在 bridge;新 DSL 指令要完成 §0-2 全清單;沒寫的設計取捨不做、寫進 §9 停手;
每階段裁判沒過不得宣告完成。完成後回報 ≤60 行。
```

---

## 附錄 A:新 DSL / bridge 指令(🔒 R12 + 待 Q4/Q7 收尾)

```
column <id> [in <space>] at <x> <y> size <w> <d> [z <z0> <z1>]
beam   <id> [in <space>] along x|y from <a> to <b> at <c> width <w> depth <d> [top <z>]
delete column|beam <id>
canvas-pos column|beam <id> <x> <y>
# newid   → + "column":N、"beam":N
# objects → + "columns":[{"id","space","box":[xlo,ylo,zlo,xhi,yhi,zhi],"cx","cy","hasPos"}]
#             "beams":[同構,另含 "axis":"x"|"y"]
# obstacles <boundary_id> → {ok,face,kind:"plan"|"elevation",
#   items:[{id,type:"column"|"beam",cls:"hole"|"notch"|"corner"|"strip"|"split"|"top_notch"|"top_drop",
#           rect:[u0,v0,u1,v1]}]}
# 套用指令(🔒 Q4,新 C 指令,整筆交易含空間成員重宣告):
#   apply-proj <boundary_id> <item>… [cut-strip]
#     item = 裸 id(柱樑皆套)或 c<id>/b<id> 型別消歧(R12:柱樑共用數值 id 空間)
#     cut-strip = 對 strip 項執行裁切(🔒 Q8 預設不帶,套用=不動幾何)
#     拆分時原 id 給面積最大片(🔒 Q9),新片用對應命名空間 newid;
#     孔隨片重分配(R10);拆片/生成面退出空間成員變游離(R11)
#     上限:條帶裁切最多 +4 面 → WORLD_MAX_BOUNDARIES/PLACEMENTS 8→16
# dump 行序:boundary → placement → guide → grid → timber → place → space → column → beam → canvas-pos
```

## 附錄 B:公理層新增條文(草稿,Phase 3 同步寫入 公理層.md)

- **D13 RC 柱(RcColumn)**:World 中房間座標的軸對齊方塊(AABB),可屬於某空間或游離;
  是空間的障礙物,不是成員,不參與 closed 推導。省略 z → [空間下界, 空間上界]。
- **D14 RC 樑(RcBeam)**:同 D13 的 AABB,走向軸平行;頂面 z_hi = 空間上界或明寫 top,
  底面 = z_hi − 深。
- **I15** 柱足跡 ⊆ 所屬空間平面範圍;兩柱正面積不得相交(邊相接合法);游離柱不檢範圍。
- **I16** 樑足跡 ⊆ 空間平面範圍;柱樑、樑樑相交不檢(不同層)。
- **I17** 空間重宣告使推導範圍縮小 → 柱樑一併重驗,不過整筆回滾;刪空間 → 柱樑變游離。
- **R7** 面上投影分類 = 單一「足跡×輪廓接觸關係」函式:完全在內=hole、貼一邊=notch、
  貼兩鄰邊=corner、貫穿=strip/split;角點相切=退化拒絕。新邊 fixity 一律 F。
- **R8** 套用是快照式衍生:觸發當下以推導值生成孔/凹口/拆片/新面,之後與柱樑無連結;
  重套用 = 手動復原後對新鬼影再套用。
- **R9** 只有已放置面可接收投影;平面/立面由 placement 法向決定,boundary.kind 僅作驗證。
