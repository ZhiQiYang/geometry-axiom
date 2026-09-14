# DOM 合約(測試依賴清單)

> 立案 2026-09-13(Phase 0 產出);Phase 1 改版更新。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。
> 來源:UI-REDESIGN-PLAN.md 附錄 B §7(cdp_test.js 依賴清單)+ §7 測試合約。

## 必須保留的 DOM id

| id | 用途 | 測試依賴點 |
|---|---|---|
| `#app` | 三列殼(.app-shell) | 子層數/高度量測(58/1fr/28) |
| `#cv` | 三視圖 SVG(覆層,z-index 5) | `hasAttribute("hidden")` 切換檢查、rect 量測 |
| `#world` | `#cv` 內容群組 | `childElementCount` |
| `#overlay` | `#cv` 疊層 | 繪圖預覽層 |
| `#canvasViewport` | 中央畫布容器 | rect 量測、`.show-grid` 切換 |
| `#ocv` | 物件畫布 SVG(主畫布,常駐可見) | rect 量測(須等於 canvasViewport) |
| `#oroot` | `#ocv` 內容群組 | 卡片/連線掛點 |
| `#edgeGroup` | `#oroot` 內的連線層 | `.edge-path`/`.edge-label` 計數 |
| `#cardLayer` | `#oroot` 內的卡片層 | `.ocard` 掛點 |
| `#viewToolbar` | 三視圖工具列(覆層內) | `hidden` 切換檢查 |
| `#focusBar` | 工作區返回列 | `hidden` 切換檢查 |
| `#status` | 狀態列文字(在 `.statusbar` 內) | 中文文案比對(改文案必同步改測試) |
| `#cmd` | 指令輸入(在 `.statusbar` 內) | 存在性檢查 |
| `#btnObj` | 三視圖鍵(`#viewSwitch` segmented 內,click=toggle 覆層) | `.click()`、rect |
| `#btnCanvasView` | `#viewSwitch` 的物件畫布鍵 | `.click()` |
| `#btnUndo` / `#btnRedo` | 復原/重做 | `.click()` |
| `#btnZoom` | fit-all(已移入 `.canvas-controls`) | `.click()` |
| `#btnNewRect` | ＋面·矩形 | `.click()` |
| `#btnNewPoly` | ＋面·多邊形 | `.click()` |
| `#btnNewSpace` | ＋空間 | `.click()` |
| `#btnBox6` | 快速六面盒(Phase 4 才接對話框) | 存在性 |
| `#btnBack` / `#crumb` / `#btnHole2` | focusBar 內控制 | `.click()`、textContent |
| `#objectList` | 左欄物件清單容器 | 子列計數 |
| `#objectCountBadge` / `#faceCount` / `#spaceCount` | 數量徽標 | textContent |
| `#inspectorContent` / `#inspectorEmpty` | 右欄檢視器 | `hidden` 切換檢查 |
| `#emptyState` | 空狀態插圖 | `hidden` 切換檢查 |
| `#snapToggle` / `#gridToggle` | 吸附/格線開關(`.canvas-controls` 內 `.mini-toggle` 鈕) | `.on` class、`aria-pressed` |
| `#filterAll` | 篩選 chips「全部顯示」(S6 新增) | `.click()` |
| `#minimapToggle` | 小地圖收合鈕(S6 新增) | `.click()`、`.minimap-shell.collapsed` |
| `#statusSummary` | 狀態列右側物件摘要(S6 新增) | textContent |
| `#zoomInButton` / `#zoomOutButton` / `#zoomLevelButton` / `#homeButton` | 縮放控制 | `.click()` |
| `#searchInput` | 搜尋框(左欄頂 `.sidebar-search` 內) | `input` 事件驅動 `oc.search` |
| `#fileMenu` / `#fileMenuPop` | 檔案選單(含 `#btnOpen #btnScene #btnEx #btnClear`) | `hidden`、`.click()` |
| `#sceneList` / `#sceneMenuBtn` / `#sceneMenuPop` / `#sceneMenuLabel` | 場景選單(品牌旁;`.scene-item[data-path]` 載入) | `hidden`、`.click()` |
| `#minimap` | 小地圖 canvas | `pointerdown` 導航;`oc.mmTf` 座標換算 |
| `#toastRegion` | toast 容器 | `.toast` 子元素計數 |
| `#objectWorkspace` | 面內/空間工作區覆層(fixed, z45) | `hidden` 切換檢查 |
| `#workspaceBackButton` / `#workspaceBackLabel` / `#workspaceDoneButton` | 工作區返回 | `.click()` |
| `#workspaceTitle` / `#workspaceEyebrow` / `#workspaceTypeIcon` | 工作區標題列 | textContent |
| `#faceWorkspaceTools` | 面內工具列 | `[data-face-tool]` 子鈕 |
| `#faceUndoButton` / `#faceRedoButton` / `#workspaceFitButton` | 工作區 undo/redo/fit | `.click()` |
| `#objectWorkspaceContent` / `#faceWorkspaceLayout` | 工作區三欄容器 | 存在性 |
| `#faceLayerList` / `#faceLayerCount` | 左欄面內物件清單 | 子列 |
| `#faceSnapToggle` / `#faceGridToggle` / `#faceGridSizeSelect` | 吸附/格線/格距 | `checked`/`value` |
| `#faceEditorViewport` / `#faceEditorSvg` / `#faceEditorRoot` | 面編輯器畫布 | rect 量測、pointer 事件目標 |
| `#faceCoordinateReadout` | 游標 uv 讀數 | textContent |
| `#faceInspectorContent` | 面內右欄檢視器 | 放置表單/投影面板掛點 |
| `#workspaceToolStatus` / `#workspaceSelectionStatus` | 工作區狀態列 | textContent |
| `#placeOX` / `#placeOY` / `#placeOZ` / `#placeU` / `#placeV` / `#placeSubmit` | 放置表單欄位(檢視器內,兩處共用) | `value`/`.click()` |
| `#projToggle` / `#projBody` / `#projViews` | 投影面板 | `[data-view]` 群組計數 |
| `#canvasModeHint` | 主畫布建面模式浮標(S6 新增) | `hidden`、textContent |
| `#feGuidePick` | 面內參考線 u/v 方向小選單 | `hidden`、`[data-axis]` 鈕 |
| `#placeFlow` | 建面→放置→收成員流程條(S6 新增,兩處檢視器共用) | `.pf-step.done/.current` |
| `#placeValid` | 放置表單 u⊥v 即時驗證(S6 新增) | textContent、`.ok/.bad` |
| `[data-filter-type]` | 顯示類型篩選 chips(button,`aria-pressed`) | `aria-pressed`、`.click()` |
| `#faceInspectorTabs` / `[data-fi-tab]` | 面內檢視器分頁 屬性/角材/網格(S6 新增) | `.active`、`.click()`、`[data-fi-pane]` 顯隱 |
| `#workspacePlaceTag` | 工作區放置膠囊(B9:天花·z=N / 游離) | textContent、`.placed/.free` |
| `#faceCanvasHint` | 面內模式浮標——**限多步工具**(redraw)顯示 | `hidden`、textContent |
| `#feZoomOut` / `#feZoomLevel` / `#feZoomIn` / `#feZoomFit` | 面內左下縮放列(B8) | `.click()`、百分比 textContent |
| `#feApplyCard` | 投影套用灰底卡(B7,含 `#feCutStrip`/`#feApplyProj`) | 存在性、子元素 |
| `.fl-group` | 圖層分組標題(邊界/參考線/角材/網格/柱樑投影) | textContent |
| `.ws-kbd-hints` | 工作區狀態列右側快捷鍵(B1) | `kbd` 文字 L/R/Esc |
| `#spaceStageTabs` / `[data-ss-tab]` | 空間舞台分頁 平面示意/三視圖(C1) | `.active`、`.click()`、`[data-ss-pane]` 顯隱 |
| `#v3Panel` / `[data-v3-view]` / `[data-v3-layer]` | 三視圖左欄:視圖+圖層勾選(D1) | `hidden`、`checked` |
| `#v3PickPanel` / `#v3PickInfo` / `#v3HoverInfo` | 三視圖右欄:pick 結果+游標位置(D1) | textContent |
| `.v3-seg` / `[data-v3-tool]` | 三視圖工具 segmented(D2;`#tool` 保留為 `.v3-native-select` 隱藏相容) | `.active`、`.click()` |
| `.v3-zoom` / `#v3ZoomOut` `#v3ZoomLevel` `#v3ZoomIn` `#v3ZoomFit` | 三視圖縮放列(D2) | `.click()`、百分比 |
| `.slot-row` / `.slot-face` / `.slot-empty` | 空間六槽列(C3 語意名+軸向副標;空槽放置鈕) | `.on`、`.click()` |
| `.rc-acts` / `.rc-act` | 構件列 hover 動作鈕(C4) | `.click()` |
| `.space-member-thumb` | 成員列內嵌縮圖(C1,替代已移除的 `#spaceFaceGrid`) | svg 子元素 |
| `text[data-fs0]` | 三視圖文字反比縮放基準(D3;`v3FixText` 依 `transform().s` 換算 mm 字級,螢幕 px 恆定) | `font-size` 屬性 |

### 已移除(Phase 6)

- `#spaceFaceGrid`:成員面卡片格 → 併入左欄成員列縮圖(`.space-member-thumb`)。
- `#spProjRefresh`:手動刷新鈕 → `renderObjects` 成功後自動 `renderSpaceWorkspace()`(含 `renderSpaceProjection`)。

## 必須保留的 class

| class | 用途 | 測試依賴點 |
|---|---|---|
| `.topbar` / `.workspace` / `.statusbar` | 三列殼區塊 | 子層序/欄寬量測 |
| `.ocard` | 物件卡片(SVG `<g>`) | `querySelectorAll` 計數、rect;`dataset.kind`/`dataset.id` 須保留;`.selected` 標記選取 |
| `.edge-path` / `.edge-label` | contains 連線 | `#edgeGroup` 內計數 |
| `.object-row` | 左欄清單列 | 搜尋過濾後計數 |
| `.ocard-frame` | 卡片外框 rect | hover/selected 視覺掛點 |
| `.object-row` | 左欄清單列 | `dataset.kind`/`dataset.id`;`.selected` |
| `[data-tool]` | 頂列工具鈕(select/pan/rect/poly) | `dataset.tool`、`.active` |
| `[data-filter-type]` | 顯示類型篩選(face/space) | `checked` 狀態 |
| `[data-icon]` | 圖示插槽 | hydrateIcons 填充 |
| `[data-face-tool]` | 面內工具鈕(select/guide/hole/pan/insert/timber/redraw) | `dataset.faceTool`、`.active`、`.disabled`(游離面 guide 停用) |
| `#faceShapeButton` `#shapeDialog` `#shapeW` `#shapeD` `#shapeA` `#shapeB` `shapeKind` | 形狀庫(RC P1:L/U/T 外環生成) | `.click()`、`value`、radio checked |
| `#notchDialog` `#notchW` `#notchD` `#notchSubmit` `#notchClose` `#notchCancel` | 參數化凹口對話框(RC P2:insert 點邊後開) | `hidden`、`.click()`、`value` |
| `#feLenInput` | 鍵入長度浮動框(RC P2:重畫中數字鍵) | `hidden`、`value`、`.style.left/top` |
| `[data-edge-len]` | 邊長清單輸入(RC P2:`data-edge-len="<i>"`) | `value` + `change` 事件 |
| `#tbLen` `#tbA` `#tbB` `#tbDir` `#tbSide` | 角材放置參數表單(Q3) | `value` 讀寫 |
| `#gridU` `#gridV` `#gridCreate` | 網格建立表單(Q3) | `value`、`.click()`、游離面 disabled |
| `.face-timber` / `.face-grid-line` | 面內角材足跡/網格線(Q3) | `#faceEditorRoot` 內計數 |
| `[data-face-hit]` | 面編輯器命中層(`v:<loop>:<i>`/`e:<loop>:<i>`/`g:<id>:<axis>`) | pointerdown 命中(非同步 bhit 已由它取代) |
| `[data-place-preset]` | 放置預設鈕 | `dataset.placePreset`、`.click()` |
| `[data-proj-check]` | 投影視圖勾選 | `checked` |
| `[data-view]` | 投影面板視圖群組(`<g data-view="0|1|2">`) | 計數(天花面預設只有 2) |
| `[data-fix-edge]` | fixity F/X 切換鈕 | `dataset.fixEdge`、`.click()` |
| `.fixity-btn` / `.place-form` / `.proj-svg` / `.inspector-block` | 檢視器元件 | 存在性 |
| `.toast` | 錯誤提示元素 | `#toastRegion` 內計數 |

## 必須保留的全域(classic script 頂層可見)

| 名稱 | 內容 | 測試依賴點 |
|---|---|---|
| `oc` | 物件畫布狀態物件 | `oc.on`、`oc.faces`、`oc.spaces`、`oc.focus`、`oc.sel`、`oc.tool`、`oc.panX/panY/zoom`、`oc.drawTool`、`oc.rect/card/pan`、`oc.showFace/showSpace`、`oc.search`、`oc.surfs`、`oc.busy`、`oc.mmTf` |
| `api` | `api(cmd)` → bridge | 測試直接送 `api("line …")`、`api("objects")` |
| `layout` | 三視圖版面 | `screenToView` 等路徑間接依賴 |
| `leaveFocus` | 退出工作區焦點 | 測試呼叫 `leaveFocus()` |
| `enterFocus` | 進入工作區焦點 | 雙擊/檢視器按鈕觸發 |
| `mutate` | 多行 DSL 交易(失敗回滾+toast) | 空間成員重宣告/六面盒使用 |
| `toast` | 錯誤提示(bridge error 原文) | `#toastRegion` 子元素 |
| `fe` | 面內工作區狀態 | `fe.tool`、`fe.panX/panY/zoom`、`fe.drag/work`、`fe.guides`、`fe.projViews` |
| `renderObjects` | 重拉 objects/surfaces 並重繪畫布 | 測試在送指令後手動觸發刷新 |

## 測試自注入

| 名稱 | 用途 |
|---|---|
| `window.__pd` | cdp_test 注入的 pointerdown 探針(測試端自掛,非產品碼) |

## `#status` 文案比對點(cdp_test 引用的中文)

- 「面 N:拖頂點/邊編輯」進入面編輯後
- 「✓ 空間 N(空容器)已建立」建空間後
- 「已復原」/「已重做」undo/redo 後
- 「物件畫布:…雙擊卡片進入…」leaveFocus/返回後
- 其他成功訊息以「✓」開頭;改文案必須同步改 cdp_test.js

## Phase 2 檢查點(cdp_test §9e/9f)

- `space 1 boundary 10 11`(經 `#cmd`,成員須為已放置 surface)→ `#edgeGroup .edge-path` = 2、label 全為 `contains`
- `searchInput` 輸入「面 1」→ `.ocard` 剩 1 張、`.object-row` 剩 1 列(詞邊界,不命中「面 10」)
- 面卡/空間卡為原型 node 視覺:header 圓點+名稱+副標、preview、footer;空間卡有六槽佔用格

## UI/UX Phase 1(A1/A2/S1/E8,cdp_test §1)

- `#app` 三列:topbar 56px / workspace 1fr / statusbar 32px;`.workspace` 三欄 260 / 1fr / 320。
- 頂列三段:`.brand`(含 `#sceneList` 場景選單)→ `.tool-group`(`[data-tool]` 鈕含 `<kbd>` V/H/R/P)→ `.top-actions`(右群 5 件:`#btnUndo #btnRedo` + `#viewSwitch` + `#fileMenu` + `#btnExport`)。
- `#viewSwitch` segmented:`.seg` 鈕 `#btnCanvasView`(物件畫布)與 `#btnObj`(三視圖,toggle 語意不變);`.active` 標目前視圖。
- `#fileMenu` > `#fileMenuPop` 內含 `#btnOpen #btnScene #btnEx #btnClear`(`.menu-item`);`.menu-pop` 開關由 `bindMenu`/`closeMenus` 控。
- `#sceneList` 不再是 `<select>`:`#sceneMenuBtn`(顯示 `#sceneMenuLabel` 目前場景)+ `#sceneMenuPop`(`.scene-item[data-path]` 各場景 + 開啟/載入範例)。
- `#searchInput` 移到 `.sidebar-left > .sidebar-search`;`#btnZoom` 移到 `.canvas-controls`。
- A1 防溢出:`.top-actions` 右緣 ≤ viewport 且左緣 > `.tool-group` 右緣(1382/1160 皆斷)。
- 物件列:`.object-row > .row-icon.{face|space|column|beam} + .row-copy > strong(12.5/600)+small(11) + (.row-badge 游離)`。
- E8:800px 下 `#faceWorkspaceTools .workspace-tool` 可見鈕 ≥5(橫向捲動而非消失)。
- 主畫布快捷鍵增 R(矩形)/P(多邊形)。

## Phase 1 版面檢查點(cdp_test §1,五項)

1. `#app` 三列:topbar 58px / workspace 1fr / statusbar 28px
2. `.workspace` 三欄:左 242px / 中 1fr / 右 326px
3. `.topbar` 子層序:brand → tool-group → top-actions
4. `#ocv` 在 `#canvasViewport` 內且同大小(誤差 ≤2px)
5. `#status`、`#cmd` 都在 `.statusbar` 裡;另存 `phase1.png` 截圖

## 變更程序

1. 改 DOM id / class / 全域名 → 先改本表 → 同步改 cdp_test.js / canvas_test.js → 跑裁判。
2. 新增測試依賴 → 補進本表對應小節。

## Phase 5 收尾(cdp_test §P5/P5b)

- 鍵盤(§5.8)實機檢查:主畫布 `v`→select、`h`→pan、`1`→`oc.zoom=1`、`f`→fit、空白→`oc.spacePan=true`、`/`→聚焦 `#searchInput`;面內 `1`→`fe.zoom=1`。
- 投影互動:`#spaceProjSvg` 內最末 `<g>` 為 hover overlay;`#projViews .proj-svg` 末 `<g>` 同。pointermove → `pick`,按住參考線拖 → `drag`。
- `#hovertxt` 承接 `setHover` 文案(pick 描述)。
- 檢視器新增動態按鈕 `#inspMembers`(space 選取時),開 `#memberDialog`。
- busy 互斥:`body.oc-busy` 期間所有 `button/input/select` 視覺停用。

## Q1 delete(cdp_test §P6)

- DSL:`delete boundary|placement|guide|grid|timber|space <id>`(line 指令,核心交易重驗)。
- 檢視器動態鈕 `#inspDelete` → `deleteObject(kind,id)`(全域);surface 對先 `delete placement` 再 `delete boundary` 經 mutate。
- 面內圖層列參考線列有 `.face-layer-del` ✕ 鈕 → `emitLine("delete guide <id>")`。

## RC Phase 4 柱樑一等物件(cdp_test §P11)

- 物件庫:`#btnNewColumn`/`#btnNewBeam` → `#rcDialog`(`.dialog`),欄位 `#rcW/#rcD/#rcSpace/#rcX/#rcY/#rcZ0/#rcZ1`(柱)、`#rcAxis/#rcA/#rcB/#rcC/#rcTop`(樑);預設尺寸列 `#rcPresets`;`#rcSubmit` 建立。
- 篩選列加 `data-filter-type="column"|"beam"`,計數 `#columnCount`/`#beamCount`。
- 卡片 `.ocard[data-kind="column"|"beam"]`:柱預覽=足跡矩形+h 標註,樑=跨度條帶+w×d。
- `objects` 回傳 `columns[]`/`beams[]`,元素 `{id,space,box:[xlo,ylo,zlo,xhi,yhi,zhi],axis?,cx,cy,hasPos}`。
- 空間→柱樑畫 `#edgeGroup .edge-group-item`,label `障礙·柱`/`障礙·樑`(非成員,語意=障礙物)。
- 檢視器:柱 `#rcfX/#rcfY/#rcfW/#rcfD/#rcfZ0/#rcfZ1`,樑 `#rcfAxis/#rcfA/#rcfB/#rcfC/#rcfW/#rcfD/#rcfTop`,共用 `#rcfSpace`/`#rcfApply` → 同 id 重宣告。
- 雙擊柱樑卡 = 只選取開檢視器(🔒 Q10,無工作區)。

## RC Phase 5 障礙物鬼影 + 空間平面圖(cdp_test §P12)

- bridge:`obstacles <boundary_id>` → `{ok,face,kind:"plan"|"elevation",items:[{id,type:"column"|"beam",cls,rect:[u0,v0,u1,v1]}]}`;cls ∈ hole|notch|corner|split|strip|top_notch|top_drop;未放置面 `ok:false`(R9)。
- 面內編輯器 `#faceEditorRoot` 畫 `.obstacle-ghost[data-cls]` 半透明矩形 + `.obstacle-ghost-label`;圖層列 `#faceLayerList` 追加「N 投影·鬼影」只讀列(無 ✕)。
- 空間工作區左欄:`#spaceRcList`(本空間構件,列點擊=移出成游離)、`#spaceRcFreeList`(游離構件,列點擊=收進)、`#spaceRcCount`;每列附 `.face-layer-del` ✕ → `delete column|beam <id>`。
- 中央 `#spacePlanSvg`:`.space-plan-floor` 地板輪廓、`.space-plan-col`、`.space-plan-beam` 足跡、`.space-plan-preview` 拖曳預覽;`.space-plan-label` 含 id+實際尺寸(如 `柱1 400×400`);尺寸選擇 `#planColSize`、`#planBeamSize`(值如 `350x600`,選 `custom` 顯示 `#planColCustom`/`#planBeamW`/`#planBeamD` 自訂輸入)。
- 互動:點一下 → `column <newid> in <sid> at <x-s/2> <y-s/2> size s s`;水平/垂直拖 >60mm → `beam <newid> in <sid> along x|y from .. to .. at .. width w depth d`。

## RC Phase 6 apply-proj 套用(cdp_test §P13,canvas_test §M)

- DSL:`apply-proj <boundary_id> <item>… [cut-strip]`;item = 裸 id(柱樑皆套)或 `c<id>`/`b<id>` 型別消歧(R12);單一交易,任何一步失敗全回滾。
- 圖層列 `#faceLayerList` 的鬼影列改為 `.fe-ob-row` + 勾選框 `.fe-ob-check[data-item-id][data-item-type]`;`strip` 項預設不勾(🔒 Q8 不裁)。
- 控制列 `.fe-ob-ctrl`:`#feCutStrip`(裁切條帶)+ `#feApplyProj`(文案隨勾數變「套用 N 項投影」,0 勾 disabled)+ `.fe-ob-note` 快照說明。
- `feApplyProj()`(全域)送 `apply-proj`,成功後 `fe.work` 清空、`feLoadGuides`+`renderFaceLayers`+`renderFaceInspector` 重繪;失敗保留草稿(核心已回滾)。
- 語意:拆分=原 id 留最大面積片+其餘新 id+孔隨片走(R10);拆片/生成面退出空間成員變游離(R11);重套已存在的孔=退化拒絕(快照無連結,R8)。
