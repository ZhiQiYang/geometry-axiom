# geometry-web UI/UX 修正規劃(SSOT)

> 立案 2026-09-14。依 `docs/uiux-review/` 審查套件(規格 S1–S6、問題 A1–A11 / B1–B9 / C1–C5 / D1–D3 / F1–F2 / E1–E8)重整介面。
> **C 端零改動**;保留 DOM-CONTRACT 所有既有 id/class,只改層級與樣式;新增元素用 §S6 的新 id 並補進 DOM-CONTRACT.md。
> UI-REDESIGN-PLAN.md §2 的 🔒 決定與 §3 常規決定不變。
> 視覺目標:`docs/uiux-review/建議-主畫布 v2.dc.html`、`建議-面內工作區 v2.dc.html`(DOM 結構見同目錄,非逐行複製)。
> 視覺原則與問題清單:`docs/uiux-review/UI-REVIEW-SPEC.md`、`review-data.js`、`ADDENDUM-互動回饋.md`。

---

## 0. 工作守則

1. **真相在 bridge,不在瀏覽器**;本檔只動 `index.html` / `app.css` / `app.js` / `cdp_test.js` / `_cursor_test.js` / `docs/DOM-CONTRACT.md` / 截圖。
2. 每階段先確認起點綠燈(`node canvas_test.js direct` + `node cdp_test.js`),做完加該階段測試段,**全 ✓ 且 exit 0 才 commit**;沒過閘不進下一階段。
3. 同一階段連續失敗 2 輪且沒有新線索 → 停手回報。
4. 每階段結束用 headless Chrome 截圖存 `docs/screens/uiux-phaseN-*.png`。
5. 工作暫存檔不入庫(`_tmp/`、探針腳本等)。
6. 改 DOM id/class → 先改 DOM-CONTRACT.md → 同步改測試 → 跑裁判。
7. 已實作項目不重做:E1–E6 互動回饋(commit `879ce91`)、中鍵平移、Esc 語意已在線;Phase 2 只補缺口與裁判。

---

## 1. 問題索引(30 + 8 條 → 階段映射)

| 階段 | 問題 id |
|---|---|
| Phase 1 | **A1**(頂列溢出 P0)、**A2**(清單樣式 P1)、**A11**(對比/熱區 P3,字級熱區部分)、S1 全域 token、**E8**(800px 頂列,與 A1 同源) |
| Phase 2 | **E1–E6**(已交付,補裁判即可)、**E7**(主畫布工具回饋殘缺) |
| Phase 3 | **F1**(三步流程 P1)、**A7**(放置表單無引導 P2)、**A8**(游離面無下一步 P2) |
| Phase 4 | **A3**(左欄擁擠 P1)、**A4**(字級 P1)、**A5**(連線一致性 P2)、**A6**(六槽 ±X P2)、**A9**(狀態列 P2)、**A10**(小地圖/縮放列 P3)、**F2**(六面盒第一格 P2)、**A11 殘餘** |
| Phase 5 | **B1–B9** 面內工作區全部 |
| Phase 6 | **C1–C5** 空間工作區 + **D1–D3** 三視圖總覽 |

---

## Phase 1:頂列溢出 + 清單樣式 + 全域 token(A1 A2 A11 E8 / S1)

### 改動範圍

- `app.css :root`:`--topbar-h: 56px`、`--statusbar-h: 32px`、`--left-w: 260px`、`--right-w: 320px`;body 13px;`--faint` 僅裝飾線/停用態,文字一律 `--muted`。
- `index.html` 頂列(12–55):
  - 左:brand + 場景下拉(按鈕觸發選單;`#sceneList` 保留 id 在選單容器,內含「開啟…」「載入範例」選項)。
  - 中:`#tool-group` 4 顆 icon+文字+`<kbd>`(V/H/R/P)——`data-tool` 保留。
  - 右 `.top-actions` 固定 5 件:`#btnUndo` `#btnRedo` | `#viewSwitch` segmented「物件畫布|三視圖」(`#btnObj` 保留 id 於三視圖鍵)| `#fileMenu`「檔案 ▾」(`#btnOpen` `#btnScene` `#btnEx` `#btnClear` 收進選單)| `#btnExport` 主鈕。`#btnZoom` 移到畫布縮放列;`#searchInput` 移到左欄頂端。
- `index.html` 左欄:`#searchInput` 區塊(34px、placeholder「搜尋物件(名稱或 id)」、kbd `/`)置於物件庫之上。
- `app.js` `renderObjectList()`(2997–3052):列內層改 `.row-copy > strong(12.5/600) + small(11 muted)`;圖示套 `.row-icon.face/.space/.column/.beam` 型別色;游離列加徽章。
- `app.css`:`.tool-group`/`top-actions` 熱區 ≥28px(圖示鈕 30–34);RWD 1160px 以下工具群收 icon-only,但 `.top-actions` 左緣不得壓過 `.tool-group` 右緣(grid `minmax` + `overflow` 規則,不用絕對定位)。
- E8:面內 `object-workspace-topbar` 的 RWD(741–768)同原則修——800px 時工具群不得整排消失,改 icon-only 保留。
- `docs/DOM-CONTRACT.md`:新增 `#fileMenu` `#viewSwitch`;版面檢查點改 56/32/260/320;`#btnZoom` 位移敘述;`#btnEx`/`#btnClear`/`#btnScene`/`#btnOpen` 位置敘述。

### 裁判(cdp_test.js §1 更新 + 新斷言)

1. `#app` 三列:56 / 1fr / 32;`.workspace` 三欄 260 / 1fr / 320。
2. **A1 防溢出**:1382px 與 1160px 兩個寬度下 `.top-actions` `getBoundingClientRect().right ≤ innerWidth` 且 `left > .tool-group 的 right`;800px 下 `.top-actions` 不遮 `.tool-group`(或工具群 icon-only 仍存在 `data-tool`)。
3. `#searchInput` 在 `.sidebar-left` 內;`#fileMenu` 含 `#btnOpen` `#btnScene` `#btnEx` `#btnClear`;`#viewSwitch` 含 `#btnObj`。
4. `.object-row .row-copy strong` 存在且 `getComputedStyle().fontSize ≥ 12px`。
5. E8:800px 寬開面內工作區,`#faceWorkspaceTools` 可見鈕數 ≥ 5。
6. 既有測試全 ✓(搜尋框位移後 `searchInput` 事件不變;`#btnZoom` 位移後 cdp 呼叫點改新位置)。
7. `_cursor_test.js` 全 ✗ 0(篩選 chips、搜尋、800px 斷言相容)。

### DoD

上列斷言全 ✓;canvas_test 不動全 pass;截圖 `docs/screens/uiux-phase1-*.png`;commit「UI/UX Phase 1:…」。

---

## Phase 2:互動回饋補齊(E1–E8)

### 現況盤點(commit `879ce91` 已交付)

| 項 | 狀態 | 本階段動作 |
|---|---|---|
| E1 參考線點一下→u/v 小選單 | ✅ 已做 | 裁判已在 P14 |
| E2 開口只點→toast | ✅ 已做 | 裁判已在 P14 |
| E3 凹口點面內→toast+邊高亮 | ✅ 已做 | 裁判已在 P14 |
| E4 角材 L 空→toast+`#tbLen` 標紅 | ✅ 已做 | 裁判已在 P14 |
| E5 工具切換狀態列/游標/浮標 | ✅ 已做 | 裁判已在 P14 |
| E6 Esc 兩段式 | ✅ 已做 | 裁判已在 P14 |
| E7 主畫布 `＋面·矩形` 點一下無反應 | ⚠ 部分:`setOcTool` 已有狀態列手勢與 `ocCursor()` 切 `.tool-rect/.tool-poly` 類,但 **CSS 未定義游標**;單點已有 toast「矩形:請拖出範圍」;**多邊形工具點擊是合法手勢**,缺「模式進行中」的畫布指示 | 補 CSS 游標 + 畫布角落模式浮標(比照 `#faceCanvasHint`,只在 rect/poly 進行中顯示);poly 逐點時狀態列顯示已點數 |
| E8 800px 面內工具列被 RWD 收掉 | ✅ 併入 Phase 1 修(同源) | Phase 1 裁判涵蓋 |

### 改動範圍

- `app.css`:`.canvas-viewport.tool-rect, .tool-poly { cursor: crosshair }`;`#canvasModeHint` 浮標樣式(新 id,補 DOM-CONTRACT)。
- `app.js` `setOcTool`(3332)/`ocCursor`(3323):rect/poly 啟用時顯示 `#canvasModeHint`(內容=手勢說明);`objDrawDown`(2915)poly 每次點擊後狀態列報「已點 N 頂點 · 點回起點閉合」;Esc 取消時 hint 收回。
- `index.html`:`#canvasViewport` 內加 `<div id="canvasModeHint" hidden>`。

### 裁判(cdp_test.js 新增 §P15)

1. rect 工具 → `#canvasModeHint` 可見且含「拖出矩形」;游標 `crosshair`(getComputedStyle)。
2. rect 單點 → toast「拖出範圍」出現(P14 既有行為保留)。
3. poly 工具點兩下 → `#status` 含「N 頂點」;Esc 後 hint 隱藏。
4. select 工具 → hint 隱藏、游標回 default。
5. P14 既有 12 項全綠不回歸。

### DoD

斷言全 ✓;截圖 `uiux-phase2-*.png`;commit。

---

## Phase 3:建面→放置→收成員流程條 + 放置表單(F1 A7 A8)

### 改動範圍

- `app.js` `renderInspector()`(3053+) / `placeFormHTML()`(2772)/ `bindPlaceForm()`:
  - **#placeFlow**(新 id):boundary 面檢視器頂部流程條 `1 建面 ✓ → 2 放置 → 3 收進空間`;進度由 `placed` 與 `surfaces` 成員關係推導;游離面附限制說明段(無參考線/不進三視圖/不算封閉)。
  - 放置表單改版:6 預設 3×2 radio 卡(`[data-place-preset]` 保留,改樣式不換機制);origin 三欄保留 `#placeOX/OY/OZ`;`#placeU/#placeV` 下拉保留。
  - **#placeValid**(新 id):u⊥v 即時驗證——通過顯示「u ⊥ v · 法向 +Z(天花)」(由 surfaces/u×v 推法向名),不通過禁用 `#placeSubmit`;主鈕文案「放置這片面」/已放置「重綁」。
  - 屬性 dl:id、範圍(「0–4000 × 0–3000」格式)、外環、孔、所屬空間。
  - 底部動作:`#inspEnter` `#inspLocate` 並排;`#inspDelete` 全寬危險樣式,文案「刪除面 N(可 Ctrl+Z 復原)」;空間另有 `#inspMembers` 主鈕「＋收成員」。
- `app.js` `faceCard()`(817):游離徽章改 10.5px 可點(`data-insp-scroll="place"` → 選取+捲檢視器至放置區);已放置副標「已放置 · 天花 z=2500」(法向推名)。
- `app.js` `renderObjectList()`:游離列同徽章(已在 Phase 1 做一半)。
- `docs/DOM-CONTRACT.md`:新增 `#placeFlow` `#placeValid`。

### 裁判(cdp_test.js 新增 §P16)

1. 游離面檢視器:`#placeFlow` 存在、第 1 步 `done`、第 2 步 `current`;限制說明文字存在。
2. `u=+x v=+x` → `#placeSubmit.disabled === true` 且 `#placeValid` 含「必須垂直」類文字;`u=+x v=+y` → 解除禁用、`#placeValid` 含「+Z」。
3. 預設卡點「天花」→ `#placeU=+x` `#placeV=+y`;送出後 `placed:true`、`#placeFlow` 第 3 步亮、`#placeSubmit` 文案「重綁」。
4. 游離面卡徽章可點 → 檢視器捲到放置區(`#placeFlow` 或放置表單 `getBoundingClientRect().top` 在視口內)。
5. `#inspDelete` 文案含「Ctrl+Z」。

### DoD

斷言全 ✓;截圖 `uiux-phase3-*.png`;commit。

---

## Phase 4:主畫布其餘(A3 A4 A5 A6 A9 A10 F2 + A11 殘餘)

### 改動範圍

- `index.html` 左欄(58–117)+ `app.css`:
  - 物件庫 3×2 icon 鈕 56px 單行標籤;`#btnBox6` 移第一格並標「建議起點」(F2);6 顆 id 全保留。
  - 篩選改單列 chips `[data-filter-type]`(`aria-pressed`、計數保留 `#faceCount` 等);右側「全部顯示」。
  - 「格線吸附/顯示格線」移到畫布縮放列:`#snapToggle`/`#gridToggle` 保留 id,改 `aria-pressed` 按鈕(原 checkbox 語意由 class 切換,`ocCursor`/gridToggle handler 同步改)。
  - `#objectList` `flex:1`。
- `app.js` `faceCard()`/`spaceCard()`/drawObjects:卡片 OC 200×156、SP 240×196;標題列 40px(型別點+名稱 12.5+副標 10.5+狀態膠囊 10.5);footer 11px;**zoom < 0.75 → `.ocard` 加 `.compact` 只留標題列**(A4;門檻為待拍板項 Q3)。
- `app.js` `drawOcEdges()`(1151):包含=實線 `#929bad`、障礙=虛線 `6 4` `#b1894f`;標籤 11px 膠囊「包含」「障礙」;`.edge-path/.edge-label/.edge-group-item` 保留。
- `app.js` `spaceCard()`(897)+ `renderSpaceInspector()`(1628):六槽改 天花/地板/前牆/後牆/左牆/右牆 + 軸向副標(±Z/±Y/±X 對應表,方位命名見待拍板項 Q4);footer「開放 · 缺 天花、左牆」。
- `index.html`/`app.css` 狀態列(188–199):32px/11.5px;左=目前工具 icon+名+context hint;右=物件摘要(「N 物件 · M 空間開放 · K 游離」)+ `#cmd`(mono、`›` 前綴、↑↓ 歷史、`:` 聚焦);`#btnEx #btnClear` 已在 Phase 1 收進 `#fileMenu`;`#status` 保留(測試比對),成功訊息**同時**發 `.toast.ok` 短暫 toast(停留時間見待拍板項 Q2)。
- `index.html` 畫布(164–175):左下縮放列 = `− % ＋ | fit(#btnZoom 位移至此) 原點(#homeButton) | #snapToggle #gridToggle`;右下小地圖 150×96 可收合(收合鈕)。
- `app.css` A11 殘餘:`.face-layer-del` ≥28px、switch 20×36、`--faint` 文字用途清零。

### 裁判(cdp_test.js 新增 §P17)

1. 物件庫鈕 6 顆高度 ≥50px、首格為 `#btnBox6` 且含「建議起點」。
2. chips:`[data-filter-type]` 為 button/aria-pressed,關「柱」→ `oc.showColumn===false` 且 `aria-pressed="false"`;「全部顯示」還原。
3. zoom 強制 0.5 → `.ocard.compact` 存在;1.0 → 無。
4. 建 space+柱:`#edgeGroup .edge-path`(實線灰)+ `.edge-group-item`(虛線琥珀,`stroke-dasharray` 非空);label 全中文「包含」「障礙」。
5. 空間卡槽位含「天花」字樣且不再出現「+X 0」;footer 含「缺 」。
6. statusbar `getComputedStyle().height==="32px"`、`.status-right` 摘要含「物件」;成功操作(建面)後 `#toastRegion .toast.ok` ≥1。
7. `#snapToggle`/`#gridToggle` 在 `.canvas-controls` 內且 `aria-pressed` 語義正確;小地圖 `minimap-shell` 寬 150px、有收合鈕。
8. `_cursor_test` 篩選段改用 chips 後全 ✗ 0。

### DoD

斷言全 ✓;截圖 `uiux-phase4-*.png`;commit。

---

## Phase 5:面內工作區(B1–B9)

### 改動範圍

- `app.js` `ICON_PATHS`(8):補 `guide/hole/notch/timber/redraw/column/beam`;`index.html` 面內工具列(212–226)每鈕 icon+文字+`<kbd>`;左欄「說明」區塊(254–257)移除,快捷鍵移狀態列右側(B1)。
- `index.html`/`app.js` 右欄:`#faceInspectorTabs [data-fi-tab]` 三頁「屬性|角材|網格」;`#tbLen #tbA #tbB #tbDir #tbSide` 與 `#gridU #gridV #gridCreate` 各歸其頁,游離面兩頁顯示停用說明(B2)。
- `app.js` `renderFaceInspector()`(2620):
  - 屬性 dl(id、尺寸、面積扣孔、外環/孔、所屬空間)。
  - 「外環邊」表:索引徽章+方向文字(→上/↓右…)、長度欄統一樣式+mm、`[data-fix-edge]` `.fixity-btn` 改 segmented、標題附「F 固定 · X 自由」(B3)。
  - 「放置」已放置時摺成摘要 3 欄+「重綁…」;「投影視圖」摺疊列標題顯示預設視圖名(B2)。
- `app.js` `drawFaceEditor()`(1966):
  - 格距依 zoom 選(螢幕間距 ≥24px,序列 10/25/50/100/250/500/1000),主格線每 4 格;`#faceGridSizeSelect` 只管吸附(B4)。
  - 邊中點長度標註(11.5px 白底)、參考線末端標 `u = 1500`、原點標 `0,0 · u→ v↓`(B5)。
  - 右下讀數 `u 1850 v 600 mm` 11.5px(B8)。
- `index.html`:`#faceCanvasHint` 常駐移除——只在多步工具(redraw、poly 類)顯示(B6);左下縮放列 `− % ＋ fit | 吸附 格線 格距`(B8)。
- `app.js` `renderFaceLayers()`(2506):分組標題 邊界/參考線/角材/網格/柱樑投影;列 38px(icon 26 + strong 12 + small 11 + hover 28px 刪除鈕);投影群組底部灰底卡 `#feApplyCard`(新 id)含 `#feCutStrip` + `#feApplyProj` + 一句快照說明;移除 `.fe-ob-ctrl` `#b48` 虛線與 `.mini-btn`(B7)。
- `index.html` 頂列:麵包屑「空間 N / ● 面 M」+ 放置膠囊(天花·z=2500 / 游離);「← 物件畫布」返回鈕(B9)。
- `docs/DOM-CONTRACT.md`:新增 `#faceInspectorTabs [data-fi-tab]` `#feApplyCard`;`#faceCanvasHint` 用途敘述改「多步工具限定」。

### 裁判(cdp_test.js 新增 §P18)

1. 面內工具鈕皆含 `svg`+`kbd`;「說明」區塊不存在。
2. `[data-fi-tab]` 三頁,切「角材」頁 → `#tbLen` 可見;游離面角材頁含停用說明。
3. 「外環邊」表列含方向文字與 mm;`.fixity-btn` segmented 兩段。
4. zoom 0.17(fit)下格線間距(量兩條主格線 px)≥24px 的 4 倍、格線數 < 60;zoom 2 時格距變小檔位。
5. SVG 內存在邊長標註文字與 `0,0 · u→ v↓` 原點標。
6. `#faceCanvasHint` 在 select 工具 hidden;redraw 工具進入後可見。
7. `#feApplyCard` 存在、含 `#feCutStrip`/`#feApplyProj`;無 `#b48` 字樣。
8. 麵包屑含「空間 1 / 面 」與「天花」膠囊(放置面);游離面含「游離」。
9. 狀態列右側含 `L`/`R`/`Esc` kbd。

### DoD

斷言全 ✓;截圖 `uiux-phase5-*.png`;commit。

---

## Phase 6:空間工作區 + 三視圖總覽(C1–C5 D1–D3)

### 改動範圍

- `index.html`/`app.js` 空間工作區(274–320):
  - 中央改 `#spaceStageTabs [data-ss-tab]`「平面示意|三視圖」佔滿高度;`#spaceFaceGrid` 移除,左欄成員列 hover 縮圖(`previewFaceSvg` 小圖),點擊 `enterFocus`(C1)。
  - `#planColSize #planBeamSize` 保留 id、外觀改 chip 下拉;「點放柱 · 拖放樑」改 tooltip(C2)。
  - `renderSpaceRc()`(1431):構件列動作鈕 hover 顯示(28px);刪除走 toast+「可 Ctrl+Z 復原」,不用 `confirm()`(C4)。
  - `renderSpaceInspector()`(1628):槽位面名+軸向副標;空槽「＋放置一片面到這裡」點擊帶入對應預設開放置(C3)。
  - 移除 `#spProjRefresh`;`mutate` 成功後自動 `renderSpaceProjection()`(C5)。
- `app.js` 三視圖總覽(`#cv` 覆層、`#viewToolbar`):
  - **D1**:左欄改「視圖(正面/側面/仰視勾選)+圖層(面/參考線/角材/柱樑)」,右欄顯示 pick 結果+`#hovertxt` 移入——**或**主畫布內分割面板(待拍板項 Q1)。
  - `#tool #workSurf #newZ` 改 segmented+下拉樣式;加左下縮放列(D2)。
  - TITLE/LABEL 改 HTML 疊字或 zoom 反比縮放(D3;法線方向性與 SVG 文字相容性,實作時二選一並記錄理由)。
- `docs/DOM-CONTRACT.md`:新增 `#spaceStageTabs [data-ss-tab]`;`#spaceFaceGrid` 移除記錄;`#spProjRefresh` 移除記錄;`#viewToolbar` 結構更新。

### 裁判(cdp_test.js 新增 §P19)

1. `[data-ss-tab]` 兩頁切換,`#spacePlanSvg`/`#spaceProjSvg` 輪流可見;`#spaceFaceGrid` 不存在。
2. 構件列 hover/click 動作鈕可點;刪除後 toast 含「Ctrl+Z」。
3. 空槽列含「放置一片面」且點擊有反應(開放置或選取)。
4. `#spProjRefresh` 不存在;mutate(收成員)後 `#spaceProjSvg` 內容自動更新。
5. D1 所選方案落地:三視圖開啟時左欄出現視圖/圖層勾選,右欄出現 pick 結果容器。
6. `#tool` segmented 存在(非原生 select 樣式);三視圖縮放列存在。
7. TITLE/LABEL 在 zoom 0.5/2 下 px 字級不變(HTML 疊字)或反比縮放後可讀。

### DoD

斷言全 ✓;截圖 `uiux-phase6-*.png`;commit。

---

## 決策佇列(2026-09-14 使用者拍板 🔒)

| # | 問題 | 決定 |
|---|---|---|
| Q1 | D1 三視圖左右欄改法 | 🔒 **換左右欄內容**:三視圖開啟時左欄改「視圖勾選+圖層」、右欄改 pick 結果+hover 描述(S5 方案 a) |
| Q2 | 成功訊息 `.toast.ok` 停留時間 | 🔒 **2000ms**;錯誤 toast 維持 3600ms |
| Q3 | `.ocard.compact` 觸發門檻 | 🔒 **zoom < 0.75** |
| Q4 | 六槽方位命名 | 🔒 y=0(N=−Y)=**前牆**、y=D(N=+Y)=後牆、x=0(N=−X)=左牆、x=W(N=+X)=右牆、+Z=天花、−Z=地板 |

## 非目標

- C 端、bridge、DSL 一律不動。
- 深色模式、rename、localStorage、拖曳排序等不在審查清單內的功能。
- `_cursor_test.js` 只在既有斷言因 DOM 位移需調時改(改座標/選擇器,不弱化斷言)。

---

## Bugfix 2026-09-14(13 缺陷修復,使用者拍板 🔒)

> 立案 2026-09-14。依兩輪獨立驗證的審查結果修 13 個缺陷(協定層 3 + 前端 10)。
> 每階段:先加會咬住錯誤的測試 → 修 → `canvas_test direct` 與 `cdp_test` 雙綠 → 一個 commit。
> 本節為決策 SSOT;之後產出前後逐條對照,不靜默改動。
> **C 端例外範圍**:僅 `../current_geometry.c` 的 undo/redo/history 相關函式可動;其餘 C 端邏輯不碰。

### L1 undo/redo 與 canvas-pos 🔒

- C 端修:`history_undo`/`history_redo` 還原 World 快照後,把**還原前**的 `canvas_pos`/`canvas_pos_count` 複製回去。
- 依據:canvas-pos 本來就不入歷史(`apply_interactive_tokens` 跳過記快照,current_geometry.c:3525-3529),所以 undo/redo 也不該把它倒回快照值。
- 不採前端重送方案。

### L2 undo 粒度=交易分組 🔒

- C 端 history 加群組機制:`line history-begin` / `line history-end` / `line history-abort` 三條 DSL 橋接指令,於 `apply_interactive_tokens` 攔截。
- `mutate()` 的多行 = 一步;undo/redo 整組進退。
- 群組內某行失敗 → 核心自動復原起點快照並關閉群組,整組回滾且不留半套用;`history-abort` 供主動放棄。
- 群組中 `undo`/`redo`/`history-begin` → ok:false;`history-end`/`history-abort` 無群組 → ok:false。
- 六面盒必須 1 次 Ctrl+Z 全退。

### L3 serve.py 跨站防護 🔒

- POST 時 `Origin` 存在且不是 `http://127.0.0.1:<port>` / `http://localhost:<port>` → 403。
- `Host` 主機名非 `127.0.0.1`/`localhost` → 403。
- 無 `Origin` 的請求(curl、測試腳本)照常放行;不要求自訂 header。

### 階段對照

| 階段 | 範圍 | 驗收 |
|---|---|---|
| 1 協定層 | `serve.py`、`web_bridge.c` | cmd 含 \r\n→ok:false;超長→整行丟棄恰回一行;Origin/Host 檢查;canvas_test §N |
| 2 一按就壞 | `app.js`(+`serve.py` upload 回 path) | btnZoom 無例外;zoom 無 NaN;upload 後 curScene 正確;換場景清焦點 |
| 3 undo | `current_geometry.c`、`app.js` | L1 pos 保留;群組一步進退;失敗整組回滾;busy 守衛 |
| 4 功能錯誤 | `app.js` | toRoom 用 getScreenCTM;六面盒跳格;面內 undo 刷新;RC 表單驗證;Esc 輸入框守衛 |
| 5 文件 | DOM-CONTRACT/README/UI-REDESIGN-PLAN | 尺寸矛盾、.fe-ob-ctrl、8 id、鍵盤清單、upload 位置、canvas-pos 描述 |

### Esc 三段式決定 🔒

README §5.8 原寫「取消草稿→退出工具→返回」與實作不符。決定:**改文件為實際行為**——
實作階梯是「輸入框焦點不攔截 → 收選單 → 關對話框 → 清鍵入長度 → 收方向小選單 → 清草稿 → 離開工作區」,
不新增「退工具」一階(會改變 cdp_test:495/548 依賴的既有行為)。
