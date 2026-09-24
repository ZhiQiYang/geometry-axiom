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

### 5.A.1 逐點閉合(2026-09-22 設計澄清,🔒 Q13–Q16)

> 依據:`C:\Users\Yang\AppData\Local\Temp\claude\D--geometry-axiom\23bd2335-f432-41f4-8811-dc7307f19014\scratchpad\clarify\摘要.md`
> §3(12 條建議)、§4(狀態畫面串)、§6(紅燈候選,已由 Q13–Q16 全部收斂,不再是紅燈)。
> 範圍:主畫布「面·多邊形」(P,`objDrawDown`/`drawPolyPreview`/`objEmitFace`)與面內工作區
> 「重畫外環」(e,`feDown`/`feMove`/`feUp`/`feRedrawClose`/`feDedupe`)兩處逐點畫正交外輪廓的
> 互動,全部純前端、不改 C 端。以下每條對應設計澄清摘要 §3 的 `diff#n`。

#### 5.A.1.0 共用模組(對應 diff#12,🔒 Q15;常規決定:落點與匯出方式,使用者反對可改)

- 新檔 `geometry-web/polydraft.js`:純邏輯、不碰 DOM、不送 bridge;`index.html` 現況是
  classic script(`index.html:527-528` 依序載入 `reference-ui.js`→`app.js`,無
  `type="module"`),`polydraft.js` 依同慣例掛 `window.PolyDraft`,`<script src="polydraft.js">`
  需插在 `app.js` 之前——這是 HTML 改動,不在本節四份文件的交付範圍內,留給下一個實作
  agent 去加。可用 Node 直接呼叫純函式做單元測試,不需要 headless Chrome、不需要 bridge。
- 完整模組合約(狀態形狀、函式簽名、錯誤碼、兩處呼叫端怎麼接)見
  `geometry-web/docs/POLYDRAFT-API.md`,是本節與該檔的共同 SSOT;本節只寫「行為」,不重複列簽名。
- 主畫布 P 呼叫點取代 `objDrawDown`/`drawPolyPreview` 的手寫軸鎖與閉合判斷;面內 e 呼叫點
  取代 `feDown`(redraw 分支)/`feMove`/`feRedrawClose`/`feDedupe` 的手寫版本。

#### 5.A.1.1 工具啟用狀態(diff#1)

- 觸發:點物件庫「面·多邊形」卡片或按 P(此前 `oc.tool`/`oc.drawTool` 非 poly)。
- 行為:工具卡片(`#btnNewPoly` 所在的 `.quick-create` 卡)加 `.active`;啟用當下若
  `[data-tool="select"]` 原本亮著,要移除其 `.active`(P/V 互切,同時只有一顆亮)。
- 預期畫面:`#btnNewPoly` 父卡出現 `.active`;`[data-tool="select"]` 同時失去 `.active`。
- cdp 斷言編號預留:`§P21-1`。

#### 5.A.1.2 浮標三段 + 可點「閉合」鈕(diff#2)

- 觸發:`oc.drawTool==="poly"` 期間。
- 行為:`#canvasModeHint` 內容改三段結構——`.hint-tool`(工具名,如「面·多邊形」)、
  `.hint-context`(情境提示,依 §5.A.1.13 狀態轉移表的「畫面」切換)、`.hint-kbd`
  (kbd 提示,如 `Esc`/`Enter`);`oc.poly.length>=3` 時額外顯示可點按鈕 `#polyCloseBtn`
  (文案「閉合」),點擊等同觸發 §5.A.1.7 的閉合判定。
- 面內 `#faceCanvasHint` **不在本次改動範圍**:它已依 UIUX-FIX-PLAN B6 限定 redraw 等多步
  工具才顯示,維持既有一行文字;設計澄清 §5.2 已載明 diff#1–4/#6–8/#11 的方向是「把面內
  既有行為搬到主畫布」,不是反向替面內加三段浮標。
- 預期畫面:`#canvasModeHint` 三個子元素皆存在且各自 `textContent` 非空;`oc.poly.length<3`
  時 `#polyCloseBtn` 為 `hidden`。
- cdp 斷言編號預留:`§P21-2`。

#### 5.A.1.3 格線吸附(diff#3,🔒 Q15 工程預設)

- 主畫布:新變數 `oc.gridMm`(預設 250,可選 100/250/300/500,選單 `#polyGridSize`);第一點
  與每段落點前先過 `PolyDraft.snapToGrid`;`#snapToggle`(既有)同時管卡片拖放(既有固定
  20mm 網格)與多邊形頂點吸附(`oc.gridMm`)——同一顆開關管兩種不同間距的吸附,是刻意的
  行為,不需要統一成同一個數字。
- 面內 e:格距**不改**,沿用 UIUX-FIX-PLAN B4 既有「依 zoom 挑 10/25/50/100/250/500/1000,
  螢幕間距 ≥24px」規則與 `#faceGridSizeSelect`/`#faceSnapToggle`;呼叫 `PolyDraft` 時傳入
  該規則算出的當下格距值,不傳固定 250。
- 這是本節唯一「兩處故意用不同格線來源」的參數,對應設計澄清摘要 §6 紅燈候選 3——已收斂
  為「維持兩套,不統一」:主畫布是自由座標、無既定比例尺;面內已有 B4 🔒 的 zoom 相依格距,
  服務對象不同,合併成單一來源反而會破壞面內既有的可讀性設計。
- 預期畫面:`snapOn` 為真時,主畫布多邊形草稿頂點座標必為 `oc.gridMm` 的整數倍。
- cdp 斷言編號預留:`§P21-3`。

#### 5.A.1.4 即時預覽:獨立草稿層(diff#4)

- 主畫布:新 `<g id="polyDraftLayer">` 掛在 `#oroot` 內(`#edgeGroup`/`#cardLayer` 之後);
  pointermove 時只清空重繪這個 group,**不**呼叫 `drawObjects()`(現況每次 move 都整個重畫,
  見現況地圖 §1.B)。內容:已定段實線(`.draft-edge`)+ 橡皮筋虛線(`.draft-rubber`)+
  淡綠預覽面(`.draft-preview-face`,已定頂點與游標連成的暫定多邊形)+ 中點 mm 標註
  (`.draft-edge-len`)+ 已定頂點圓點(`.draft-vertex`)+ 起點空心圓(`.draft-start-vertex`)。
- 面內 e:新增 `<g id="feDraftLayer">` 掛在 `#faceEditorRoot` 內,共用同一組 class 名稱,但吃
  `fe.panX/panY/zoom` 換算,不吃 `oc.*`。
- 預期畫面:草稿進行中,對應草稿層子元素數 >0;游標移動不觸發整份 `drawObjects()`/
  `drawFaceEditor()` 重繪(量測方式由實作 agent 決定,寫斷言時註明)。
- cdp 斷言編號預留:`§P21-4`。

#### 5.A.1.5 鍵入長度(diff#5)

- 主畫布:新增 `#ocLenInput`(沿用 `.fe-len-input` 樣式),行為與面內 `#feLenInput` 對等:
  畫邊途中按數字鍵→浮動框累積→Enter 呼叫 `PolyDraft.applyTypedLength` 把該段定長、接續
  下一段;Esc(第一層)只清 `typed`,不取消整段草稿(見 §5.A.1.8)。
- 面內 e:**不改**,沿用既有 `#feLenInput`/`feRedrawApplyLen()`,內部改呼叫
  `PolyDraft.applyTypedLength`(行為不變,只換實作)。
- 預期畫面:按數字鍵後 `#ocLenInput.hidden===false` 且 `value` 等於已鍵入字串;Enter 後草稿
  多一段、長度等於輸入值。
- cdp 斷言編號預留:`§P21-5`。

#### 5.A.1.6 對齊參考線(diff#6)

- 兩處皆新增:自由座標(未鍵入長度、未落在格線吸附點的移動中游標)若與既有任一頂點的 x 或 y
  在 **±8 螢幕像素**內,吸附到該軸並畫虛線參考線(`.draft-align-guide`,掛在各自草稿層)。
  這是「畫線途中」的新吸附,與 §5.A「拖邊對齊吸附」(既有,拖曳既有邊時的吸附)是不同時機
  的兩段規格,不衝突(設計澄清摘要 §5.2 比對表已確認)。
- 閾值換算:`PolyDraft` 本體只吃 scene 座標,±8px 的螢幕閾值由呼叫端各自用 `oc.zoom`/
  `fe.zoom` 換算成 scene 距離(`8/zoom`)後傳入 `PolyDraft.snapToVertices`。
- 預期畫面:游標移到既有頂點 ±8px 內 → 該點 x 或 y 被吸附、畫面出現一條貫穿該軸的虛線;
  若吸附對象恰為起點且已可閉合(`pts.length>=3`),額外在 `.hint-context` 提示
  「點下這一點後即可直角閉合」。
- cdp 斷言編號預留:`§P21-6`。

#### 5.A.1.7 閉合判定與自動補直角(diff#7,🔒 Q15;對應紅燈候選 1,已收斂)

- 三種閉合觸發,兩處通用:①點回起點(螢幕距離 ≤12px,既有半徑不變)②按 Enter ③雙擊。
- **自動補直角**(`PolyDraft.tryClose` 內部邏輯;`L`=末點、`F`=起點):
  1. 若 `L` 與 `F` 已同軸(同 x 或同 y),不需要補角,直接收尾。
  2. 否則,兩個候選角點是 `(L.x,F.y)` 與 `(F.x,L.y)`;先選「與最後一段軸向交錯」的那個
     ——正交多邊形相鄰邊必交錯,兩個候選中恰有一個與末段軸向垂直,以此為主判準(取代
     「兩個都試」的枚舉)。
  3. 該候選若與草稿自身各邊及既有邊(不含頭尾相鄰邊)相交或共線重疊,退而選另一個候選。
  4. 兩個候選都不行 → 錯誤碼 `NO_CORNER`,浮標/toast 顯示警示,**不閉合**,草稿停留原狀態
     (狀態轉移表狀態 5 停留)。
- 閉合前**必跑**:①(需要時)插入補角頂點 ②去共線(等同既有 `feDedupe`)③頂點數 `<4`
  或送核心前用 shoelace 自檢面積為 0(自交/退化)→ 前端擋下,toast 對應錯誤碼訊息,
  **不送核心**(`TOO_FEW`/`DEGENERATE`)。
- 兩處都做(🔒 Q15),差異只在收尾後的呼叫:主畫布呼叫 `objEmitFace`(建新 boundary);
  面內呼叫既有 `feRedrawClose` 的核心部分(整份重宣告既有 boundary 的 `loops[0]`)。
- 預期畫面:末段與起點不同軸時,閉合前預覽出現一個空心方塊轉折記號
  (`.draft-corner-preview`);成功閉合送出的 `outline` 點列比使用者實際點的多 1 個
  (補角頂點)。
- cdp 斷言編號預留:`§P21-7`(需覆蓋:同軸免補角、單一候選合法、單一候選交叉退而選另一、
  兩候選皆交叉→`NO_CORNER`)。

#### 5.A.1.8 錯誤與退回(diff#8)

- 前端先驗(送核心前先擋):下一段與既有邊相交 → 錯誤碼 `CROSS`;沿原邊回頭/重疊(新點落在
  最後一段同一軸線上且方向與該段相反)→ 錯誤碼 `BACKTRACK`。兩者發生時橡皮筋線轉紅
  (`.draft-rubber.error`)、浮標 `.hint-context` 改警示文字、**點擊該位置不落點**。
- 對抗審查 finding-3(2026-09-22)修正並補上原本沒寫的一段:鍵入長度(Enter 套用 `typed`)
  算出的候選點跑**同一套**驗證(`PolyDraft.applyTypedLength` 內部呼叫同一支
  `evaluateNextPoint`),回傳同一組錯誤碼(`CROSS`/`BACKTRACK`/`TOO_MANY`/`OUT_OF_RANGE`)
  時,持久回饋比照滑鼠落點:狀態列 + 橡皮筋轉紅(`.draft-rubber.error`,`cur` 沿用上一次
  pointermove 算出的方向,不因為改用鍵盤輸入就消失);主畫布額外疊上 `.hint-context`
  警示文字(面內工作區沒有 `#canvasModeHint` 這個容器,只有狀態列 + 紅橡皮筋兩項)。
  `typed` 保留不清空,讓使用者接著訂正——清數字(Esc 第一階/`clearTyped`)或移動游標
  (`previewMove` 整包換掉預覽)才會消,不是一次性 toast 就結束。
- 共線(往前延伸,同軸且方向與最後一段相同):`PolyDraft.place` 直接**延長合併**——取代
  末頂點,不新增頂點。
- Backspace:兩處都支援,退回最後一個已定頂點;若只剩 1 點再退 → 回到「未落筆」狀態。
- Esc 階梯(🔒 Q14,**只**新增主畫布 P 專屬三段,**不修改**面內既有 Esc 🔒 七階梯——見
  §5.A.1.16 差異表):
  1. 第一次 Esc:若 `typed` 非空 → 只清 `typed`,浮標與草稿不變。
  2. 第二次 Esc(`typed` 已空、`pts.length>0`):清整份草稿(`oc.poly=[]`),浮標提示
     「再按 Esc 離開」(措辭比照面內既有 toast「再按 Esc 返回」)。
     **GEO-185(2026-09-24)補**:清掉的頂點暫存在 `oc.polyStash`,此時 Ctrl+Z 先還原草稿、不動世界;
     落新點或離開工具才丟。浮標 kbd 改寫「Backspace 退一點 · Enter 閉合 · Esc 清草稿」(舊「Esc 退回」會被讀成退一點)。
  3. 第三次 Esc(`pts.length===0`,工具仍是 poly):`oc.drawTool=null`,離開工具回 select。
  - 若使用者在某階梯之間又落了新點,階梯重置回第 1 階(`typed` 判斷優先)。
- 預期畫面:交叉/回頭時草稿層橡皮筋 stroke 變紅;Backspace 後頂點數 -1、狀態列頂點數同步
  遞減;Esc 三段各自的中繼提示可見。
- cdp 斷言編號預留:`§P21-8`。

#### 5.A.1.9 閉合後落點(diff#9)

- **取代**現行兩種舊行為(HEAD 版「質心+`canvas-pos`+`centerOnNode`」、工作區未提交版
  「`selectObject`+`centerOnNode`+`renderObjects()`的 homeless 自動排格」,見現況地圖
  §1.B):新規則是卡片座標 = 多邊形 bbox 左上角 `(bbox.x0, bbox.y0)`,直接送
  `canvas-pos boundary <id> <bbox.x0> <bbox.y0>`;**不呼叫** `centerOnNode`,也**不**觸發
  `renderObjects()` 的 `nextCardPosition()` 自動排格分支——多邊形閉合這一刻已經有明確座標
  (繪製位置本身),不屬於「沒有座標才自動找空位」的通用規則。
- 視野**不移動**(`oc.panX`/`oc.panY` 不變)。
- 選中新面並開檢視器(`selectObject("boundary", id)`)。
- toast:內容含頂點數與 bbox 尺寸,例如
  `✓ 面 <id> 已建立 · <N> 頂點 · <W>×<H> mm · Ctrl+Z 復原`。
- 與 `pendingSlot` 流程(codex 未提交變更引入,見現況地圖 §1.B/§2)共存:若
  `pendingSlot && pendingSlot.bid==null`,閉合後仍照現行邏輯把新 id 填入
  `pendingSlot.bid` 並 `enterFocus("face", id)`——這段**不受本節影響**;bbox 落點規則只
  決定「沒有 `pendingSlot` 時卡片放哪」,有 `pendingSlot` 時卡片馬上被帶進面內工作區,
  兩者不衝突。
- cdp 斷言編號預留:`§P21-9`(須涵蓋:無 `pendingSlot` 時 `canvas-pos` 等於 bbox 左上、
  `oc.panX/panY` 不變、toast 含頂點數與尺寸)。

#### 5.A.1.10 閉合後:外環邊 · 尺寸確認清單(diff#10,🔒 Q16;對應紅燈候選 2,已收斂)

- 主畫布 boundary 檢視器(`renderInspector()` 的 `sel.kind==="boundary"` 分支)新增一段,
  插在既有屬性 dl 之後、「操作」按鈕之前:標題「外環邊 · 尺寸確認」,每列 索引、方向文字、
  長度 mm 輸入、F/X fixity 切換——**沿用**面內既有 `renderFaceInspector()` 的
  `.edge-list`/`.edge-row` 樣式,但 id 改用 `main` 前綴
  (`#mainEdgeLength${i}`/`#mainEdgeFixed${i}`/`#mainEdgeFree${i}`)避免與面內版本
  (`#edgeLength${i}` 等)在同一份 DOM 中 id 撞號(兩個檢視器面板同時存在於 DOM,只是可見
  性不同時開)。`data-edge-len`/`data-fix-edge`/`data-fix-val` 屬性沿用既有命名(這些是
  scoped `querySelectorAll` 用,不要求全域唯一)。
- 編輯邏輯**共用同一份**(🔒 Q16):把面內既有的「改長度→`applyEdgeLen`傳播→
  `emitBoundary`」與「點 F/X→切 fixity→`emitBoundary`」抽成共用委交函式(建議簽名
  `commitEdgeLength(bid, loops, i, newLen)`/`commitEdgeFixity(bid, loops, i, val)`,
  回傳 `Promise<boolean>`),兩處各自只傳入不同的「送出後重繪」回呼(面內
  `feAfterChange`;主畫布 `renderObjects()+renderInspector()`)。這兩個共用函式
  **不屬於** `polydraft.js`(會呼叫 `emitBoundary`/bridge,違反 polydraft.js 純邏輯不碰
  bridge 的原則),留在 `app.js` 內,是既有 `bindPlaceForm`/`renderFaceInspector` 綁定邏輯
  的重構,先在此記錄以免三個實作 agent 各自重造一份。
- 預期畫面:主畫布選取一個已閉合的 boundary → 檢視器出現「外環邊 · 尺寸確認」清單,列數
  等於外環頂點數;改任一列長度 → `emitBoundary` 送出、清單依新外環重繪。
- cdp 斷言編號預留:`§P21-10`。

#### 5.A.1.11 狀態列文案(diff#11)

- 既有文案「多邊形:已點 N 頂點 · 點回起點閉合(Esc取消)」**保留**(cdp_test 既有比對點,
  不得變動字面);hover 於草稿線段時額外在浮標(不是 `#status`)顯示「本段 N mm」。
- 成功閉合時**同時**發 `#status` 文字更新與 `.toast.ok`(見 §5.A.1.9),兩者不互斥。
- cdp 斷言編號預留:`§P21-11`(沿用既有 `#status` 文案斷言,新增 toast 存在性斷言)。

#### 5.A.1.12 共用草稿狀態機(diff#12,🔒 Q15)

- `polydraft.js` 同時承載主畫布 P 與面內 e 的:軸鎖、共線合併/回頭拒絕、補直角、格線吸附、
  頂點對齊吸附、Backspace、鍵入長度、閉合前驗證(`TOO_FEW`/`DEGENERATE`)。
- 兩處**不共用**的部分(各自在 `app.js` 呼叫端處理,不進 `polydraft.js`):
  - Esc 階梯(主畫布 3 段 vs 面內既有 7 段 🔒,§5.A.1.8/§5.A.1.16)。
  - `gridMm` 來源(§5.A.1.3)。
  - 座標系與送出後動作(主畫布→`objEmitFace`/bbox 落點;面內→`feRedrawClose` 的重宣告
    既有 boundary)。
  - 尺寸確認清單的 DOM id 前綴(§5.A.1.10)。
- 完整介面見 `geometry-web/docs/POLYDRAFT-API.md`。

#### 5.A.1.13 狀態轉移表(摘自設計澄清摘要 §4,補上兩處差異欄)

| 狀態 | 進入條件 | 主畫布 P 專屬差異 | 面內 e 專屬差異 | 離開到 |
|---|---|---|---|---|
| 1 啟用工具 | 點卡片/按 P(面內按 e) | 取消「選取」高亮(§5.A.1.1) | 既有 `[data-face-tool]` 互斥機制不變 | 放第一點→2;Esc→回上一工具 |
| 2 起點與第一段 | `pts.length===1` | 格線吸附用 `oc.gridMm` | 格線吸附用 fe 當下 zoom 格距 | 繼續累點;數字鍵→3;Backspace→回 1 |
| 3 鍵入長度 | 按數字鍵 | `#ocLenInput` | `#feLenInput`(既有) | Enter 定長續下一段;Esc 只清數字 |
| 4 對齊吸附 | 自由座標 ±8px 內 | `#polyDraftLayer` 畫參考線 | `#feDraftLayer` 畫參考線 | 落點吸附;移開游標取消提示 |
| 5 閉合就緒 | `pts.length>=3` 且距起點 ≤12px | `#polyCloseBtn` 可點 | 既有點/Enter/雙擊 | 閉合成功→7;兩候選皆交叉→停留 |
| 6 錯誤 | 下一段交叉/回頭 | 橡皮筋紅 + 浮標警示 | 橡皮筋紅 + 浮標警示 | 移開游標→回 2/3/4(依游標位置) |
| 7 閉合後 | `commit()` 成功 | bbox 左上落點,視野不跳(§5.A.1.9) | 既有 `feAfterChange` 重繪面內畫布 | 主畫布:放置流程;面內:留在面內 |

- 任何時候 Ctrl+Z 且有建立紀錄 → `undo()`;此行為**不變**,不屬本節新增範圍。

#### 5.A.1.14 cdp_test.js 斷言編號預留

新段 `§P21`(緊接既有最後一個 RC/UIUX 段之後;實作時依 `cdp_test.js` 當下最大編號續號,
若 `P21` 已被占用則往後遞補並同步更新本節與 DOM-CONTRACT 的編號)。`P21-1` 至 `P21-11`
依序對應 §5.A.1.1–§5.A.1.11;`P21-12` 起另加 diff#12 的模組層級測試(Node 直接呼叫
`PolyDraft.*` 純函式,不需要 headless Chrome)。

> **diff#10 實作紀錄**:2026-09-22 只實作 §5.A.1.10(主畫布外環邊清單),`P21`/`P22`/`P23`
> 當時都已被既有段落占用,依上述規則遞補為 `cdp_test.js §P33`(`P33-1`–`P33-9`)。其餘
> diff#1–9/11/12(`polydraft.js` 本體)尚未實作,之後接手的 agent 撿號時 `P21`–`P23`、
> `P33` 都已占用,請從當下 `cdp_test.js` 最大編號繼續遞補,不要沿用本節寫死的 `P21`。

> **diff#1–9/11 實作紀錄**:2026-09-22 續,實作主畫布 P 工具本體(`objPolyOpts`/
> `objDrawDown`/`objPolyTryClose`/`objPolyEnter`/`objPolyBackspace`/`objPolyEscStep`/
> `objPolyPreviewMove`/`renderPolyDraftLayer`/`ocLenShow`/`objEmitFace`)。`P34` 當時是
> 當下最大編號之後第一個未占用段,依規則使用(`P34-1`–`P34-15`)。

> **diff#12 面內段實作紀錄**:2026-09-22 續,實作面內「重畫外環」e 呼叫端
> (`feDown`/`feMove`/`feSetTool`/Esc 階梯第4·6級/鍵入長度鍵盤掛勾改呼叫 `PolyDraft.*`,
> `#feDraftLayer` 已掛載),`P35` 是當下最大編號之後第一個未占用段(`P35-1`–`P35-9`,
> 部分子編號如 `P35-5a/5b`、`P35-7a`–`7d` 因驗證項目較多再細分)。舊版面內手寫軸鎖函式
> `feDedupe`/`feRedrawClose`/`feRedrawApplyLen` 已移除,由 `feDraftTryClose`/
> `feCommitDraft`/`feDraftApplyLen` 取代;新增 `feGridStep()`(抽出既有 B4 格距計算)、
> `feDraftOpts()`/`feSyncDraftMirror()`/`feDraftPreviewMove()`/`renderFeDraftLayer()`。
> `fe.drag`/`fe.lenBuf` 兩個既有欄位改為鏡射 `fe.draft`(對等 `oc.polyDraft`)的相容欄位,
> 讓 `cdp_test.js` 既有 §P9/§P10(直接呼叫 `feDown`/`feMove`、讀 `fe.drag.pts`/`fe.lenBuf`)
> 與 B6 Esc 七階梯測試不必更動就繼續通過。詳見 `POLYDRAFT-API.md` 與 `DOM-CONTRACT.md`。

#### 5.A.1.15 舊測試相容性提醒(承現況地圖 §5)

`cdp_test.js` 既有 §9c/§9d(HEAD `cdp_test.js:342-383`,物件畫布多邊形 6 點閉合 + 2 步
undo)**與本節行為不相容**:§9d 假設「閉合送出後還會自動補一筆 `canvas-pos`(homeless
排格)」,但 §5.A.1.9 已改成閉合當下就直接算好 bbox 左上送 `canvas-pos`、建立時就帶座標,
不會落入 `renderObjects()` 的 homeless 分支——undo 步數可能從 2 步變 1 步。實作 agent
交件前**必須**實跑 §9c/§9d 並依實際行為更新斷言(不得只信舊註解);這是既有測試被本節
行為變更影響到的既知風險,已在此明記,不算「需拍板」。

> **diff#12 面內段舊斷言更新紀錄**(2026-09-22):基線 345 ✓ / 3 ✗,3 條紅斷言都在
> `cdp_test.js`「P15. 主畫布模式回饋 E7」段(與面內段本身無關,是主畫布 P 工具 diff#3
> 吸附預設開之後的既有殘留紅燈,一併在本輪修掉):
> 1. 「E7 poly 狀態列」(舊斷言假設點兩下、螢幕距離 60px 一定各自落點,不會被吸附合併)
>    ——`#snapToggle` 現在預設 `class="on"`、`oc.gridMm` 預設 250mm,60px 遠小於
>    250mm,兩點會被吸到同一格點、第二點被 `PolyDraft.place` 的「與末點重合視為忽略」
>    規則吞掉。**改法**:選「在測試裡明確關閉 snapToggle」(§5.A.1.15 授權的二選一之
>    一),用完即還原成頁面預設,不影響其他斷言。
> 2. 「E7 Esc 清草稿」(舊斷言假設單次 Esc 就整段清空+隱浮標+離開工具)——與 🔒 Q14
>    (§5.A.1.8)三段式矛盾:第一次 Esc 只清草稿(浮標仍可見、仍在工具內),第二次才
>    離開。**改法**:拆成兩條斷言各驗一次 Esc 後的狀態,斷言數量因此 +1(不減)。
> 三條斷言都改「語意」不改「範圍」——沒有放寬任何驗收標準,只是把假設換成拍板後的
> 正確行為。修正後 `cdp_test.js` 全綠(見 `DOM-CONTRACT.md` 面內段落的實作進度說明)。

#### 5.A.1.16 主畫布 P 與面內 e 差異速查(對照 §5.A.1.12)

| 項目 | 主畫布 P | 面內 e |
|---|---|---|
| Esc 階梯 | 3 段(本節新定,§5.A.1.8) | 既有 7 段 🔒(UIUX-FIX-PLAN「Esc 三段式決定」段,不動;只有第4/6級內部改呼叫 `PolyDraft.clearTyped`/清空 state) |
| gridMm 來源 | 固定選單 100/250/300/500,預設 250 | `feGridStep()`(B4 zoom 相依格距;舊版 `feSnap()` 實際吃的是固定 `#faceGridSizeSelect`,這是 diff#12 面內段修正後才真的接上 B4) |
| 座標系 | world/scene mm(`oc.panX/panY/zoom`) | 面 uv mm(`fe.panX/panY/zoom`) |
| 草稿層 | `#polyDraftLayer`(diff#1–11 新增,動態掛在 `#oroot`) | `#feDraftLayer`(diff#12 面內段新增,動態掛在 `#faceEditorRoot`,同一作法) |
| 鍵入長度框 | `#ocLenInput`(新) | `#feLenInput`(既有 id/樣式不變) |
| 送出對象 | 新 boundary(`objEmitFace`) | 既有 boundary 的 `loops[0]` 重宣告(`feCommitDraft`,取代舊版 `feRedrawClose`) |
| 閉合後 | bbox 左上落點+toast+選中(§5.A.1.9) | 既有 `feAfterChange` 重繪 |

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
繼續執行 D:\knowledgebase\geometry\geometry-web\docs\RC-POLYGON-PLAN.md 的 Phase <N>。
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
