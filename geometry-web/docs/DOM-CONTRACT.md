# DOM 合約(測試依賴清單)

> 立案 2026-09-13(Phase 0 產出);Phase 1 改版更新。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。
> 來源:UI-REDESIGN-PLAN.md 附錄 B §7(cdp_test.js 依賴清單)+ §7 測試合約。

## 第二輪新增與行為變更（2026-09-22）

| id / class | 契約 |
|---|---|
| `#toggleLeft` / `#toggleRight` | 主畫布窄螢幕抽屜，`aria-expanded` 與可見狀態一致 |
| `#workspaceToggleLeft` / `#workspaceToggleRight` | 面／空間的抽屜，不得打開或露出背後主畫布欄位 |
| `[data-close-panel]` / `body.drawer-left-open` / `body.drawer-right-open` | 關閉與 Escape；關閉後焦點回開啟鈕 |
| `#cmdToggle` / `#cmdPanel` | 指令列預設 hidden；`:` 開啟並 focus；Escape 收合 |
| `#edgeLabelLayer` / `.edge-label-item.active` | `#cardLayer` 上方標籤；只顯示選取或 hover 空間的標籤 |
| `.card-enter` | 非精簡卡的進入／檢查鈕；Enter/Space 可操作；精簡卡保留雙擊 |
| `.inspector-footer` | 放置送出按鈕的 sticky 區，游離面在預設桌面高度可直接操作 |
| `#edgeLengthN` / `#edgeFixedN` / `#edgeFreeN` | 穩定焦點 id，邊界重繪後還原鍵盤目標 |
| `#placeDetails` / `#projectionDetails` / `.ib-row` | 原生 details 摺疊，重繪保留 open 狀態 |
| `#tbPlace` | 以當前角材設定啟動 timber 工具，焦點回面畫布 |
| `.fl-empty` | 五類圖層的空狀態；有可建操作者提供分頁入口 |
| `#spaceWorkspaceTools` / `#spaceAddMembers` / `#spacePlaceColumn` / `#spacePlaceBeam` | 空間工作區中間工具群 |
| `#workspaceKeyHints` | 面內 L/R/T/Esc；空間點放柱／拖放樑／Esc |
| `body.v3-picked` | 有三視圖選取才展開右欄；主畫布 `[data-tool]` 在三視圖 disabled |
| `.is-busy` | 觸發按鈕上的 spinner；不降低全頁透明度 |

移除 `#btnScene`（由場景選單載入）與 `#workspaceDoneButton`（只保留返回）。
`#btnDatums` 移進檔案選單；`#faceShapeButton` 移到屬性頁外環邊下方；
工作區 undo/redo/fit 移到右側操作群；尺寸 chip 移入 `#spaceStageTabs`；`.space-plan-head` 移除。
七個測試寬度：1382、1160、900、680、600、390、320 px。桌面欄寬 260/320；三視圖左欄 200。
共用頂列／狀態列高為 56/32；寬度 ≤560 px 時頂列改為 96 px 的兩列，狀態列仍為 32 px。
主畫布第一列為場景與選取／平移，第二列為抽屜、復原／重做、視圖與檔案操作；
面／空間工作區第一列為返回、標題與操作，第二列為工具群。所有頂列按鈕必須在畫面寬度內可達。
`--topbar-h` 同時決定主畫布與工作區的頂列、畫布剩餘高度、抽屜頂部與 toast 起點，不得個別寫死 56 px。
`.app-shell` 與 `.object-workspace` 必須明定單欄 `minmax(0,1fr)`，子列不得以內容最小寬度撐開畫面。
600 px 以上維持既有單列配置。

空槽現在記錄 `pendingSlot`，引導建立或選取游離面，使用者確認尺寸與原點後一次交易放置並收進原空間。
不得以「空槽點擊就立即 placed:true」為測試前提；空空間沒有可推導尺寸。

## 必須保留的 DOM id

| id | 用途 | 測試依賴點 |
|---|---|---|
| `#app` | 三列殼(.app-shell) | 子層數/高度量測(`--topbar-h`/1fr/32；≤560 px 頂列 96，其餘 56) |
| `#cv` | 三視圖 SVG(工具列下方的 flex 剩餘高度) | `hasAttribute("hidden")` 切換檢查、rect 量測 |
| `#world` | `#cv` 內容群組 | `childElementCount` |
| `#overlay` | `#cv` 疊層 | 繪圖預覽層 |
| `#canvasViewport` | 中央畫布容器 | rect 量測、`.show-grid` 切換 |
| `#ocv` | 物件畫布 SVG(主畫布,常駐可見) | rect 量測(須等於 canvasViewport) |
| `#oroot` | `#ocv` 內容群組 | 卡片/連線掛點 |
| `#edgeGroup` | `#oroot` 內的連線層 | `.edge-path` 計數；標籤改在 `#edgeLabelLayer` |
| `#cardLayer` | `#oroot` 內的卡片層 | `.ocard` 掛點 |
| `#viewToolbar` | 三視圖工具列(畫布頂部固定列) | `hidden` 切換檢查 |
| `#focusBar` | 工作區返回列 | `hidden` 切換檢查 |
| `#status` | 狀態列文字(在 `.statusbar` 內) | 中文文案比對(改文案必同步改測試) |
| `#cmd` | 指令輸入(預設收起的 `#cmdPanel` 浮層內) | 存在性檢查 |
| `#btnObj` | 三視圖鍵(`#viewSwitch` 內,click=setView3(true),重複點擊維持選定) | `.click()`、rect |
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
| `#busyIndicator` | 狀態列左側 busy 進度指示(spinner+「套用中…」,§P20 新增) | `hidden`(`mutate()` 超過 400 ms 才顯示、結束隱藏) |
| `#zoomInButton` / `#zoomOutButton` / `#zoomLevelButton` / `#homeButton` | 縮放控制 | `.click()` |
| `#searchInput` | 搜尋框(左欄頂 `.sidebar-search` 內) | `input` 事件驅動 `oc.search` |
| `#fileMenu` / `#fileMenuPop` | 檔案選單(含 `#btnOpen #btnDatums #btnEx #btnClear`) | `hidden`、`.click()` |
| `#sceneList` / `#sceneMenuBtn` / `#sceneMenuPop` / `#sceneMenuLabel` | 場景選單(品牌旁;`.scene-item[data-path]` 載入) | `hidden`、`.click()` |
| `#minimap` | 小地圖 canvas | `pointerdown` 導航;`oc.mmTf` 座標換算 |
| `#toastRegion` | toast 容器 | `.toast` 子元素計數 |
| `#objectWorkspace` | 面內/空間工作區覆層(fixed, z45) | `hidden` 切換檢查 |
| `#workspaceBackButton` / `#workspaceBackLabel` | 工作區返回 | `.click()` |
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
| `#faceInspectorTabs` / `[data-fi-tab]` | 面內檢視器分頁 屬性/參考線/角材/網格(v2 新增 guide) | `.active`、`.click()`、`[data-fi-pane]` 顯隱 |
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
| `#v3ZoomBar` / `.v3-zoom` / `#v3ZoomOut` `#v3ZoomLevel` `#v3ZoomIn` `#v3ZoomFit` | 三視圖獨立左下縮放列(D2 修正:移出 `#viewToolbar`,樣式沿用 `.canvas-controls`;主畫布左下縮放列/小地圖在 `body.v3-mode` 下讓位) | `hidden` 切換、rect 左下位置、`.click()`、百分比 |
| `.slot-row` / `.slot-face` / `.slot-empty` | 空間六槽列(C3 語意名+軸向副標;空槽放置鈕。`data-slot-preset` 存 `PLACE_PRESETS` 鍵、`data-slot-label` 存中文方位名,點擊帶入該槽 u/v 預設並選取對應游離面) | `.on`、`.click()` |
| `.rc-acts` / `.rc-act` | 構件列 hover 動作鈕(C4;`.rc-act` `min-height:28px` 與旁邊 `.face-layer-del` ✕ 熱區一致) | `.click()`、`getBoundingClientRect().height` |
| `.space-member-thumb` | 成員列內嵌縮圖(C1,替代已移除的 `#spaceFaceGrid`) | svg 子元素 |
| `text[data-fs0]` | 三視圖文字反比縮放基準(D3;`v3FixText` 依 `transform().s` 換算 mm 字級,螢幕 px 恆定) | `font-size` 屬性 |
| `#box6Dialog` / `#box6Submit` / `#box6W` / `#box6D` / `#box6H` / `#box6Floor` | 快速六面盒對話框 | `hidden`、`.click()`、`value`/`checked` |
| `#memberDialog` / `#memberCheckList` / `#memberSubmit` / `#memberDialogTitle` | 編輯空間成員對話框 | `hidden`、`.click()`、勾選列 |
| `#spEditMembers` | 空間檢視器動態鈕(非靜態 DOM) | `.click()` 開 `#memberDialog` |
| `#spaceWorkspaceLayout` | 空間工作區三欄容器(`#faceWorkspaceLayout` 互斥顯隱) | `hidden` 切換檢查 |
| `#spaceMemberList` | 空間工作區左欄成員列 | 子列計數 |
| `#spaceInspectorContent` | 空間工作區右欄檢視器(六槽列掛點) | 存在性 |
| `#rcErr` | RC 對話框表單內錯誤提示(BF4:驗證失敗顯示) | `hidden`、textContent |

### 已移除(Phase 6)

- `#spaceFaceGrid`:成員面卡片格 → 併入左欄成員列縮圖(`.space-member-thumb`)。
- `#spProjRefresh`:手動刷新鈕 → `renderObjects` 成功後自動 `renderSpaceWorkspace()`(含 `renderSpaceProjection`)。

## 必須保留的 class

| class | 用途 | 測試依賴點 |
|---|---|---|
| `.topbar` / `.workspace` / `.statusbar` | 三列殼區塊 | 子層序/欄寬量測 |
| `.ocard` | 物件卡片(SVG `<g>`) | `querySelectorAll` 計數、rect;`dataset.kind`/`dataset.id` 須保留;`.selected` 標記選取 |
| `.edge-path` / `.edge-label` | contains 連線 | `#edgeGroup` / `#edgeLabelLayer` 各自計數 |
| `.object-row` | 左欄清單列 | 搜尋過濾後計數 |
| `.ocard-frame` | 卡片外框 rect | hover/selected 視覺掛點 |
| `.object-row` | 左欄清單列 | `dataset.kind`/`dataset.id`;`.selected` |
| `[data-tool]` | 頂列工具鈕(select/pan); rect/poly 改由物件庫與 R/P 快捷鍵啟動 | `dataset.tool`、`.active` |
| `[data-filter-type]` | 顯示類型篩選(face/space) | `checked` 狀態 |
| `[data-icon]` | 圖示插槽 | hydrateIcons 填充 |
| `[data-face-tool]` | 面內工具鈕(select/guide/hole/pan/insert/timber/redraw) | `dataset.faceTool`、`.active`、`.disabled`(游離面 guide 停用) |
| `#faceShapeButton` `#shapeDialog` `#shapeW` `#shapeD` `#shapeA` `#shapeB` `shapeKind` | 形狀庫(RC P1:L/U/T 外環生成) | `.click()`、`value`、radio checked |
| `#notchDialog` `#notchW` `#notchD` `#notchSubmit` `#notchClose` `#notchCancel` | 參數化凹口對話框(RC P2:insert 點邊後開) | `hidden`、`.click()`、`value` |
| `#feLenInput` | 鍵入長度浮動框(RC P2:重畫中數字鍵) | `hidden`、`value`、`.style.left/top` |
| `[data-edge-len]` | 邊長清單輸入(RC P2:`data-edge-len="<i>"`) | `value` + `change` 事件 |
| `#tbAnchor` `#tbSelector` `#tbA` `#tbB` `#tbDir` `#tbSide` | 角材引用、截面與方向；長度由引擎推導 | `value` 讀寫 |
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
| `curScene` | 目前場景 `{path,name}` | P29 載入範例後比對路徑 |
| `closeMenus` | 關閉所有 `.menu-pop` | P28 開檔案選單前 |
| `setView3` | 開／關三視圖 | P24–P30 準備場 |
| `selectObject` | 選物件並開檢視器 | P25 樑套用 |
| `resetSceneFocus` | 離開焦點並重繪 | P23 上傳後 |
| `feRenderProjection` | 面內投影重繪 | P27 面投影拖曳 |
| `dragging` | 三視圖參考線拖曳狀態 | P27 取消拖曳須 `started` |

## 測試自注入

| 名稱 | 用途 |
|---|---|
| `window.__pd` | cdp_test 注入的 pointerdown 探針(測試端自掛,非產品碼) |
| `window.__apiLog` | cdp_test 包裝 `api` 記錄送出的 cmd(驗證「不送指令」類斷言,非產品碼) |

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

- `#app` 桌面三列:topbar 56px / workspace 1fr / statusbar 32px;`.workspace` 三欄 260 / 1fr / 320。≤560 px 頂列依上方手機契約改為 96px。
- 頂列三段:`.brand`(含 `#sceneList` 場景選單)→ `.tool-group`(`[data-tool]` 鈕含 `<kbd>` V/H/R/P)→ `.top-actions`(右群 5 件:`#btnUndo #btnRedo` + `#viewSwitch` + `#fileMenu` + `#btnExport`)。
- `#viewSwitch` segmented:`.seg` 鈕 `#btnCanvasView`(物件畫布)與 `#btnObj`(三視圖,toggle 語意不變);`.active` 標目前視圖。
- `#fileMenu` > `#fileMenuPop` 內含 `#btnOpen #btnDatums #btnEx #btnClear`(`.menu-item`);`.menu-pop` 開關由 `bindMenu`/`closeMenus` 控。
- `#sceneList` 不再是 `<select>`:`#sceneMenuBtn`(顯示 `#sceneMenuLabel` 目前場景)+ `#sceneMenuPop`(`.scene-item[data-path]` 各場景 + 開啟/載入範例)。
- `#searchInput` 移到 `.sidebar-left > .sidebar-search`;`#btnZoom` 移到 `.canvas-controls`。
- A1 防溢出:`.top-actions` 右緣 ≤ viewport 且左緣 > `.tool-group` 右緣(1382/1160 皆斷)。
- 物件列:`.object-row > .row-icon.{face|space|column|beam} + .row-copy > strong(12.5/600)+small(11) + (.row-badge 游離)`。
- E8:800px 下 `#faceWorkspaceTools .workspace-tool` 可見鈕 ≥5(橫向捲動而非消失)。
- 主畫布快捷鍵增 R(矩形)/P(多邊形)。

## Phase 1 版面檢查點(cdp_test §1,五項)

1. `#app` 桌面三列:topbar 56px / workspace 1fr / statusbar 32px；≤560 px 頂列改為 96px
2. `.workspace` 三欄:左 260px / 中 1fr / 右 320px
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
  C4:不彈 `confirm()`,直接刪除,成功後 toast 提示可 Ctrl+Z 復原(對齊空間工作區 `renderSpaceRc` 構件列 ✕)。
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
- 控制卡 `#feApplyCard`(動態插入,灰底):`.fe-ob-cut > #feCutStrip`(裁切條帶)+ `#feApplyProj`(文案隨勾數變「套用 N 項投影」,0 勾 disabled)+ `.fe-ob-note` 快照說明。
- `feApplyProj()`(全域)送 `apply-proj`,成功後 `fe.work` 清空、`feLoadGuides`+`renderFaceLayers`+`renderFaceInspector` 重繪;失敗保留草稿(核心已回滾)。
- 語意:拆分=原 id 留最大面積片+其餘新 id+孔隨片走(R10);拆片/生成面退出空間成員變游離(R11);重套已存在的孔=退化拒絕(快照無連結,R8)。

## 對抗審查漂移修正(cdp_test §P20)

- A3:`.quick-create-grid` 改 `repeat(3,1fr)`(3 欄 × 2 列,原為 2 欄 × 3 列)。
- A4:`faceCard()`/`spaceCard()` 卡片標題 `font-size` 11.5 → 12.5(S1 token)。
- A9:`.toast.ok svg` 新增著色 `color: var(--face)`(比照 `.toast.error svg`)。
- A10/A11:`#minimapToggle` 熱區 20×20 → 28×28。
- B1:`renderFaceLayers()` 圖層列 `.face-layer-icon` 改用 `icon("rectangle"/"hole"/"guide"/"timber"/"grid")` SVG,不再塞 ▱▨⌖▤╬ 純文字。
- B3:`.fixity-btn` 高度 26→28;`.fixity-btn.seg` 26×22→28×28。
- B9:`workspaceEyebrow` 麵包屑補 §S3 格式的 `●` 分隔點,完整格式「空間 N / ● 面 M」。
- toast 避讓小地圖:`.toast-region` `bottom` 42px → 122px(壓在 `.minimap-shell` right14/bottom14/高96 之上,≥118)。
- busy 進度指示:`#busyIndicator`(狀態列左側,spinner+「套用中…」)——`mutate()` 飛行中 `hidden=false`,結束 `hidden=true`;不改變既有 `body.oc-busy` 按鈕停用機制。

## 面·多邊形逐點閉合(polydraft,2026-09-22 設計澄清,🔒 Q13–Q16,cdp_test §P34/§P35)

> 規格本體見 `RC-POLYGON-PLAN.md` §5.A.1;共用邏輯模組合約見 `POLYDRAFT-API.md`。
> 範圍:主畫布「面·多邊形」(P)與面內工作區「重畫外環」(e)共用同一份 `polydraft.js`
> 狀態機。下表「歸屬」欄標明「主畫布」「面內」「共用」三種,共用 = 兩處各自掛在自己的
> 草稿層下,class 名相同、掛載節點不同。
>
> **實作進度**(2026-09-22 續,diff#12 面內段):diff#1–9/11(主畫布 P 工具本體)、diff#10
> (外環邊 · 尺寸確認清單)、diff#12 的**面內 e 呼叫端**(`feDown`/`feMove`/`feSetTool`/
> Esc 階梯的第4·6級/鍵入長度鍵盤掛勾全部改呼叫 `PolyDraft.*`,`#feDraftLayer` 已掛載)
> 全部已實作;對應斷言在 `cdp_test.js` §P33(diff#10)、§P34(主畫布 diff#1–9/11)、§P35
> (面內 diff#12;`§P21`–`§P23`/`§P33`/`§P34` 實作當下均已被既有段落占用,依
> RC-POLYGON-PLAN §5.A.1.14 的重號規則遞補為 §P35)。舊版面內手寫軸鎖函式
> `feDedupe`/`feRedrawClose`/`feRedrawApplyLen` 已移除(不是薄包裝),由
> `feDraftTryClose`/`feCommitDraft`/`feDraftApplyLen` 取代,行為與主畫布 `objPoly*` 系列
> 對等。`polydraft.js` 本體不受本輪影響(該模組由另一 agent 同時維護 `tryClose` 的收尾
> 驗證,本輪只讀)。

| id / class | 歸屬 | 契約 |
|---|---|---|
| `#canvasModeHint` | 主畫布(既有 id,契約擴充) | 三段結構容器:`.hint-tool`/`.hint-context`/`.hint-kbd` 三個子元素常駐(`renderCanvasModeHint()` 產生);`oc.polyDraft.pts.length>=3` 時額外含可見的 `#polyCloseBtn`(既有 textContent/hidden 契約不變,只是內容結構化;rect 工具沿用同一容器,三段內容改為固定文字,聚合 textContent 仍含「拖出範圍」等既有子字串) |
| `.hint-tool` / `.hint-context` / `.hint-kbd` | 主畫布 | `#canvasModeHint` 內三段內容,`textContent` 依 RC-POLYGON-PLAN §5.A.1.13 狀態轉移表的「畫面」欄切換 |
| `#polyCloseBtn` | 主畫布 | 「閉合」可點鈕(`.hint-close-btn`);`hidden` 由 `oc.polyDraft.pts.length<3` 控制;`.click()` 等同觸發 §5.A.1.7 閉合判定(`objPolyTryClose()`) |
| `#polyDraftLayer` | 主畫布 | `<g>` 掛在 `#oroot` 內、`drawObjects()` 每次清空重建時緊接在 `#edgeGroup`/`#cardLayer`/`#edgeLabelLayer` 之後重新掛上;`renderPolyDraftLayer()` 只清空重繪這個 group,pointermove 走 `objPolyPreviewMove()`,不觸發 `drawObjects()`(可觀測訊號:`ocDrawCount`,見下) |
| `#feDraftLayer` | 面內 | `<g>` 掛在 `#faceEditorRoot` 內、`drawFaceEditor()` 每次清空重建時掛在最後一個子節點(在其他內容之上);比照 `#polyDraftLayer` 動態建立,不寫進 `index.html`。`renderFeDraftLayer()` 只清空重繪這個 group,pointermove 走 `feDraftPreviewMove()`,不觸發 `drawFaceEditor()`(取代舊版直接畫在 `#faceEditorRoot` 的 `d0.kind==="redraw"` 分支,已移除) |
| `.draft-edge` / `.draft-rubber` / `.draft-preview-face` / `.draft-vertex` / `.draft-start-vertex` / `.draft-edge-len` / `.draft-corner-preview` / `.draft-align-guide` | 共用 | 草稿層內部元素 class(定義在 `app.css`,無容器範圍限制);主畫布版本掛在 `#polyDraftLayer`,面內版本掛在 `#feDraftLayer`,結構一一對應(`renderFeDraftLayer()`/`renderPolyDraftLayer()` 是同一份邏輯的 `oc.*`/`fe.*` 版本);`.draft-rubber.error` = 交叉/回頭警示態(變紅) |
| `#ocLenInput` | 主畫布 | 鍵入長度浮動框,`class="fe-len-input"` 沿用既有樣式(比照 `#feLenInput`);`hidden`/`value`/`.style.left/top` 由 `ocLenShow()` 控制 |
| `#polyGridSize` | 主畫布 | 格線間距下拉(值 100/250/300/500,預設 250),掛在 `.canvas-controls` 內、`#snapToggle`/`#gridToggle` 旁;`change` 事件寫入 `oc.gridMm` |
| `#feLenInput` | 面內(既有 id/樣式不變) | 鍵入長度浮動框;`feLenShow()` 本體未改(讀 `fe.lenBuf`/`fe.drag.cur`/`fe.drag.pts`,兩者皆是鏡射 `fe.draft` 的相容欄位,見下) |
| `#mainEdgeLength${i}` / `#mainEdgeFixed${i}` / `#mainEdgeFree${i}` | 主畫布 | 主畫布 boundary 檢視器「外環邊 · 尺寸確認」清單(RC-POLYGON-PLAN §5.A.1.10);與面內 `#edgeLength${i}`/`#edgeFixed${i}`/`#edgeFree${i}` 同構,id 前綴不同(同一 DOM 中兩個檢視器面板同時存在,避免撞號);`data-edge-len`/`data-fix-edge`/`data-fix-val` 屬性沿用既有命名 |
| `.edge-list` / `.edge-row` | 共用(既有 class 延伸用途) | 主畫布版本沿用面內既有樣式 class;`querySelectorAll` 需以各自 pane 為根(`#inspectorContent` vs `#faceInspectorContent`)避免互相命中 |
| `.quick-create.active` | 主畫布 | diff#1(§5.A.1.1):目前只有 `#btnNewPoly` 在 `setOcTool("poly")`/離開時切這個 class(`#btnNewRect` 未跟進,範圍限定 P 工具) |

新增全域狀態:

- `oc.gridMm`(number,主畫布多邊形格線吸附間距,預設 250)。
- `oc.polyDraft`(`PolyDraft.createState()` 起始的共用草稿狀態機 state;`place`/`backspace`/
  `applyTypedLength`/`clearTyped` 等呼叫後整包替換,不原地改)。
- `oc.poly`(相容既有測試/呼叫端保留,鏡射 `oc.polyDraft.pts`——每次 `oc.polyDraft` 重新指派時
  同步 `oc.poly = oc.polyDraft.pts`,兩者共享同一陣列參考,不是深拷貝)。
- `oc.polyPreview`(最近一次 `PolyDraft.previewMove()` 回傳:`{cur,guides,closeReady,error,
  cornerPreview}`,供 `renderPolyDraftLayer()`/`renderCanvasModeHint()`/`ocLenShow()` 讀取)。
- `ocDrawCount`(number,`drawObjects()` 每次整份重畫累加一次的頂層 `let`;diff#4 cdp 斷言用它
  證明 pointermove 沒有觸發整份物件層重繪)。
- `fe.draft`(面內 `PolyDraft` state,對等 `oc.polyDraft`;`feSetTool`/`resetSceneFocus`/
  `leaveFocus`/`openFaceWorkspace`/收尾成功後重置為 `PolyDraft.createState()`)。
- `fe.draftPreview`(對等 `oc.polyPreview`,`feDraftPreviewMove()` 的最近一次回傳)。
- `fe.drag`(既有欄位,語意改變:redraw 進行中時**不是**原始資料,是 `fe.draft` 的鏡射
  `{kind:"redraw", pts: fe.draft.pts, cur: fe.draft.cur}`,由 `feSyncDraftMirror()` 在
  每次 `fe.draft` 變動後同步;`fe.draft.pts.length===0` 時鏡射為 `null`——與舊版「未落
  第一點前 `fe.drag` 為 null」的語意完全一致,cdp_test 既有 §P9/§P10/B6-Esc 測試直接讀
  這個欄位,不需要更新)。
- `fe.lenBuf`(既有欄位,同樣改為鏡射 `fe.draft.typed` 的相容字串,供 `feLenShow()`/既有
  測試/面內既有 Esc 階梯第4級直接讀取)。
- `feGridStep()`(新函式,抽出既有 B4「依 zoom 挑 10/25/50/100/250/500/1000,螢幕間距
  ≥24px」格距計算,`drawFaceEditor()` 畫格線與 `feDraftOpts()` 的 PolyDraft `gridMm` 共用
  同一份;面內 redraw 的格線吸附因此不是固定 `#faceGridSizeSelect` 值,是 B4 zoom 相依值
  ——這是刻意的行為改動,對應 POLYDRAFT-API.md §6)。

不變(本節不改動):`#faceCanvasHint`(既有一行文字,未升級成三段浮標,見
RC-POLYGON-PLAN §5.A.1.2)、`feLenShow()` 函式本體、面內既有 `#edgeLength${i}`/
`#edgeFixed${i}`/`#edgeFree${i}`(§5.A.1.10 只新增主畫布版本)、面內 Esc 階梯的其餘五級
(輸入框焦點不攔截/收選單/關對話框/收方向小選單/離開工作區,`#feGuidePick` 等,
UIUX-FIX-PLAN 既有七階梯不變,只有第4級「清鍵入長度」與第6級「清草稿」內部改呼叫
`PolyDraft.clearTyped`/清空 state)、`polydraft.js`/`polydraft_test.js` 本體、舊三視圖
殭屍 `tool==="poly"`(`canvasDown/Move/Up`)。

diff#12 面內接法唯一偏離 POLYDRAFT-API.md 字面(「index.html 改動…留給下一個實作
agent」)的地方:`#feDraftLayer` **沒有**寫進 `index.html`,原因是主畫布 P 工具實作時
(diff#1–11)已經改用「`drawObjects()`/`drawFaceEditor()` 每次清空重建時動態掛 `<g>`」
的作法(`#polyDraftLayer` 同樣不在 `index.html`),面內段沿用同一precedent 保持兩處一致,
不引入「一個寫死 HTML、一個動態掛」的不對稱。

`serve.py` 的靜態檔白名單追加 `/polydraft.js`(與 `/app.js`/`/reference-ui.js` 同組)——
`index.html` 依 POLYDRAFT-API.md 要求在 `app.js` 之前插入 `<script src="polydraft.js">`,
沒有這行白名單瀏覽器會拿到 404、整個模組載入失敗,屬於讓本節可運作的必要最小改動。
