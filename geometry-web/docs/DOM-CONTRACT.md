# DOM 合約(測試依賴清單)

> 立案 2026-09-13(Phase 0 產出);Phase 1 改版更新。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。
> 來源:UI-REDESIGN-PLAN.md 附錄 B §7(cdp_test.js 依賴清單)+ §7 測試合約。

## 回報收件匣（GEO-183，2026-09-24，cdp_test §P38）

`feedback.js` 在 `app.js` 之前載入，動態在 `body` 末端掛 `#fbRoot`（不在 `#app` 內，不影響殼層量測）。

| id / class / 全域 | 契約 |
|---|---|
| `#fbRoot` | 回報 UI 根節點；畫面快照會把它移除 |
| `#fbButton` | 右下常駐「回報」鈕；不在頂列、不在 `#app` 內；面／空間工作區中仍可見 |
| `#fbPanel` / `#fbNote` / `[data-fb-kind]` / `#fbPick` / `#fbTarget` / `#fbSend` / `#fbCancel` | F8 開關；開啟時焦點在 `#fbNote`；Esc 只關面板（不進 app 的 Esc 階梯）；Ctrl+Enter 送出 |
| `#fbPickHover` / `body.fb-picking` | 「指出位置」模式：下一次點擊只記錄元素，**不交給 app**；Esc 取消回面板 |
| `[data-fb-target]` | 只出現在 `page.html` 快照裡，標使用者指到的元素 |
| `window.fbRecord(k, data)` | app.js 在 `apiRequest` / `toast` / `setStatus` 呼叫；`feedback.js` 未載入時 `?.` 略過 |
| `window.geometryFeedback` | `{events, open, close, quickMark, describe}`，測試讀 `events` |

## 多邊形 UI/UX 審查修正與 Delete 快捷鍵（GEO-184/185，2026-09-24，cdp_test §P39/§P40）

> GEO-186(b,同日)移除畫布多邊形工具後，本節的 `poly-snap-grid`、`oc.polyStash`、
> `.hint-kbd`（多邊形）三列契約隨機器一併移除；下列為仍存在的契約。

| id / class / 全域 | 契約 |
|---|---|
| 主畫布 `Delete` / `Backspace` | 有 `oc.sel` 且無繪圖工具（`oc.drawTool`/`oc.rect`）時呼叫 `deleteObject`；輸入框內不作用 |
| `--grid-x` / `--grid-y` | 由 `ocGridApply()` 設為 `oc.panX/panY`，格線隨平移對齊畫布座標；`--grid-size` 間距 <8px 時改畫 5/25/…倍疏線（GEO-187） |
| `.toast-region` | 浮標可見時下移到浮標下方（取代舊的「有 toast 就隱藏浮標」） |

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
| `#faceInspectorTabs` / `[data-fi-tab]` | 面內檢視器分頁 屬性/形狀/參考線/角材/網格/底圖(v2 新增 guide;形狀頁 GEO-188;底圖頁 GEO-190,共 6 頁) | `.active`、`.click()`、`[data-fi-pane]` 顯隱 |
| `#workspacePlaceTag` | 工作區放置膠囊(B9:天花·z=N / 游離) | textContent、`.placed/.free` |
| `#faceCanvasHint` | 面內模式浮標——**限多步工具**(redraw)顯示 | `hidden`、textContent |
| `#feZoomOut` / `#feZoomLevel` / `#feZoomIn` / `#feZoomFit` | 面內左下縮放列(B8) | `.click()`、百分比 textContent |
| `#feApplyCard` | 投影套用灰底卡(B7,含 `#feCutStrip`/`#feApplyProj`) | 存在性、子元素 |
| `.fl-group` | 圖層分組標題(邊界/參考線/角材/網格/柱樑投影) | textContent |
| `.ws-kbd-hints` | 工作區狀態列右側快捷鍵(B1) | `kbd` 文字 L/R/Esc |
| `#spaceStageTabs` / `[data-ss-tab]` | 空間舞台分頁 平面示意/三視圖(C1) | `.active`、`.click()`、`[data-ss-pane]` 顯隱 |
| `#v3Panel` / `[data-v3-view]` / `[data-v3-layer]` | 三視圖左欄:視圖+圖層勾選(D1) | `hidden`、`checked` |
| `#v3PickPanel` / `#v3PickInfo` / `#v3HoverInfo` | 三視圖右欄:pick 結果+游標位置(D1) | textContent |
| `.v3-seg` / `[data-v3-tool]` | 三視圖工具 segmented(D2;`#tool` 保留為 `.v3-native-select` 隱藏相容);四件 view/rect/hole/edit,舊 `poly` 已依 🔒 Q17 移除(GEO-181) | `.active`、`.click()`、數量 4 且無 `poly` |
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
| `#feActionBar` / `[data-fe-act]` | 面內選邊/角/點/角材後的浮動操作列(GEO-188;`op:notch`/`op:extend`/`op:push`/`op:corner`/`op:hole`/`fixity`;GEO-191 角材選取只有 `delete`) | `hidden`、`.click()`、`.on` |
| `#feOpPanel` / `[data-fe-param]` / `[data-fe-keep]` / `[data-fe-anchor]` / `[data-fe-dir]` / `[data-fe-ax]` / `[data-fe-ay]` / `#feOpApply` / `#feOpCancel` | 就地參數面板(GEO-188/170;`input` 事件即時預覽,`[data-fe-keep]` 是「留下」欄與切掉連動,Enter/`#feOpApply` 套用) | `hidden`、`value`、`.click()` |
| `#feCtxMenu` | 面內右鍵選單(GEO-192;內容 = `feActionsFor(fe.sel)`,與 `#feActionBar` 同一份資料來源) | `hidden`、`[data-fe-act]` 清單與 `#feActionBar` 逐一相同、`.click()` |

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
| `[data-tool]` | 頂列工具鈕(select/pan); rect 由物件庫與 R 快捷鍵啟動,P 是一次性動作(建面卡→進面內,非工具態) | `dataset.tool`、`.active` |
| `[data-filter-type]` | 顯示類型篩選(face/space) | `checked` 狀態 |
| `[data-icon]` | 圖示插槽 | hydrateIcons 填充 |
| `[data-face-tool]` | 面內工具鈕(select/guide/hole/pan/timber/redraw;`insert` 已於 GEO-188 移除) | `dataset.faceTool`、`.active`、`.disabled`(游離面 guide 停用) |
| `#faceShapeButton` `#shapeDialog` `#shapeW` `#shapeD` `#shapeA` `#shapeB` `shapeKind` | 形狀庫(RC P1:L/U/T 外環生成) | `.click()`、`value`、radio checked |
| ~~`#notchDialog` …~~ | 參數化凹口對話框(RC P2)**已於 GEO-188 移除**,凹口改走 `#feActionBar` → `#feOpPanel` | — |
| `#feLenInput` | 鍵入長度浮動框(RC P2:重畫中數字鍵) | `hidden`、`value`、`.style.left/top` |
| `[data-edge-len]` | 邊長清單輸入(RC P2:`data-edge-len="<i>"`) | `value` + `change` 事件 |
| `#tbAnchor` `#tbSelector` `#tbA` `#tbB` `#tbDir` `#tbSide` | 角材引用、截面與方向；長度由引擎推導 | `value` 讀寫 |
| `#tbSelected` / `#tbSelDelete` | 角材頁頂端「已選角材」摘要與刪除鈕(GEO-191;`fe.sel.kind==="timber"` 時才出現) | 存在性、textContent、`.click()` |
| `.face-layer-row[data-timber-id]` | 左欄角材列(GEO-191;`.sel` 同步畫布選取,hover/click 有掛鉤) | `dataset.timberId`、`.sel`、mouseenter/mouseleave/click |
| `#gridU` `#gridV` `#gridCreate` | 網格建立表單(Q3) | `value`、`.click()`、游離面 disabled |
| `.face-timber` / `.face-grid-line` | 面內角材足跡/網格線(Q3;GEO-191 角材矩形加 `data-face-hit`、`.sel`/`.hover`) | `#faceEditorRoot` 內計數 |
| `[data-face-hit]` | 面編輯器命中層(`v:<loop>:<i>`/`e:<loop>:<i>`/`g:<id>:<axis>`/`t:<id>`(GEO-191 角材,只在 `.tool-select` 下吃事件)) | pointerdown 命中(非同步 bhit 已由它取代) |
| `.fe-ghost-handle` / `[data-fe-handle]` | 就地操作預覽矩形的四條可拖曳邊(GEO-192 B;`left`/`right`/`top`/`bottom`,只在 select 工具且 `fe.op` 時畫出) | `#faceEditorRoot` 內計數、`.click()`(實際互動走 pointerdown/move/up,見 `feApplyGhostDrag`) |
| `[data-place-preset]` | 放置預設鈕 | `dataset.placePreset`、`.click()` |
| `[data-proj-check]` | 投影視圖勾選 | `checked` |
| `[data-view]` | 投影面板視圖群組(`<g data-view="0|1|2">`) | 計數(天花面預設只有 2) |
| `[data-fix-edge]` | fixity F/X 切換鈕 | `dataset.fixEdge`、`.click()` |
| `.face-edge-sel` / `.fe-point-mark` / `[data-fe-ghost="sub\|add"]` / `.fe-feat-hi` | 面編輯器:選取邊高亮、操作預覽矩形(紅=減、綠=加)、形狀頁特徵高亮(GEO-188) | `#faceEditorRoot` 內計數、`width`/`height` 屬性 |
| `[data-fi-tab="shape"]` / `.fe-feat[data-feat]` / `[data-feat-num]` / `[data-feat-side]` / `[data-feat-mirror="x|y"]` / `[data-feat-del]` | 檢視器「形狀」頁(GEO-188;本次工作階段特徵清單,改數字 `change` 落地、鏡射、刪除) | `.active`、計數、`value`+`change`、`.click()` |
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
| `fe` | 面內工作區狀態 | `fe.tool`、`fe.panX/panY/zoom`、`fe.drag/work`、`fe.guides`、`fe.projViews`、`fe.sel/op/feats/selFeat`(GEO-188;`fe.sel={kind:"timber",id}` GEO-191)、`fe.hoverTimber`(GEO-191) |
| `feStartOp` / `feApplyOp` / `feCancelOp` / `feRectBool` | 形狀編輯(GEO-188):就地操作與正交矩形布林 | 測試直接呼叫 `feCancelOp()`;`feRectBool(loops,op,rect)` 純函式 |
| `feDeleteTimber` | 刪角材共用路徑(GEO-191;`delete timber <id>` + 清選取/重載) | 測試可直接呼叫 `feDeleteTimber(id)` |
| `feActionsFor` / `feRunAction` | 浮動列/右鍵選單共用的動作清單與處理器(GEO-192 C) | 測試比對 `#feActionBar`/`#feCtxMenu` 的 `[data-fe-act]` 清單逐一相同 |
| `feHandleDblClick` / `feDblOpenFor` | 雙擊的選取+開面板邏輯(GEO-192 D,由 `fevp` 的 `pointerdown` 自己判斷雙擊後呼叫,不掛原生 `dblclick`) | 不建議測試直接呼叫,走真滑鼠雙擊(見 cdp_test §P44 說明) |
| `feApplyGhostDrag` / `fePinchRect` | 拖預覽矩形邊(GEO-192 B)/Alt 拖頂點捏缺口(GEO-192 A)的純幾何計算 | 純函式,不碰 DOM |
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
- 主畫布快捷鍵增 R(矩形)/P(建面卡→面內畫外環,GEO-186(b) 後非持續工具)。

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

## 面·多邊形逐點閉合(polydraft,2026-09-22 設計澄清,🔒 Q13–Q16;GEO-186(b) 後改為面內專用,cdp_test §P34/§P35)

> 規格本體見 `RC-POLYGON-PLAN.md` §5.A.1;共用邏輯模組合約見 `POLYDRAFT-API.md`。
>
> **GEO-186(b,2026-09-24 拍板):主畫布不再有 mm 繪圖的多邊形工具。** 同一張畫布混用
> 「mm 繪圖」與「固定 200×156 卡片排版」兩套座標是 GEO-186 的根因——畫 4000×3000
> 的房間要縮到 2–5%,閉合後產生的卻是 200×156 縮圖卡片、還被放到多邊形左上角,
> 縮成一個點(GEO-187「找不到卡片」)。
>
> 現行流程:P 鍵/「＋面·多邊形」按一下 = `objNewPolyFace()` 建預設外環
> (4000×3000 矩形佔位)的面卡、卡片落在當下視野中心 → `enterFocus("face",id)`
> 自動進入面內工作區 → `feSetTool("redraw")` 直接以實際 mm 逐點畫外環
> → Esc 回畫布。pendingSlot 流程同樣支援:槽位「＋放置」備妥 rect 工具時按 P,
> 新面自動帶入 `pendingSlot.bid`、進面內直接開「放置」頁。
> 對應斷言:`cdp_test.js` §P34(新流程接線)。
>
> 畫布端逐點閉合機器已整份移除:`oc.polyDraft`/`oc.poly`/`oc.polyPreview`/`oc.polyStash`/
> `oc.gridMm`、`#polyDraftLayer`/`#polyCloseBtn`/`#ocLenInput`/`#polyGridSize`、
> `renderPolyDraftLayer`/`objPoly*`/`ocLenShow`、`.canvas-viewport.tool-poly`/
> `poly-snap-grid`、`.quick-create.active`。PolyDraft 狀態機行為由
> `polydraft_test.js` 單元測試 + 面內 §P35/§P36 覆蓋。
>
> **實作進度**(2026-09-22 diff#12 面內段):面內 e 呼叫端(`feDown`/`feMove`/`feSetTool`/
> Esc 階梯的第4·6級/鍵入長度鍵盤掛勾)全部呼叫 `PolyDraft.*`,`#feDraftLayer` 已掛載;
> 對應斷言在 `cdp_test.js` §P33(外環邊清單)、§P35(面內 diff#12)。舊版面內手寫軸鎖函式
> `feDedupe`/`feRedrawClose`/`feRedrawApplyLen` 已移除,由 `feDraftTryClose`/
> `feCommitDraft`/`feDraftApplyLen` 取代。

| id / class | 歸屬 | 契約 |
|---|---|---|
| `#canvasModeHint` | 主畫布 | 三段結構容器:`.hint-tool`/`.hint-context`/`.hint-kbd` 三個子元素常駐(`renderCanvasModeHint()` 產生);GEO-186(b) 後只有 rect 工具使用,`hidden = oc.drawTool !== "rect"`、三段為固定文字(「矩形」「在畫布上拖出範圍建立游離面」「Esc 取消」);`enterFocus`/`leaveFocus`/`ocCursor` 都會重算 |
| `#feDraftLayer` | 面內 | `<g>` 掛在 `#faceEditorRoot` 內、`drawFaceEditor()` 每次清空重建時掛在最後一個子節點(在其他內容之上);動態建立,不寫進 `index.html`。`renderFeDraftLayer()` 只清空重繪這個 group,pointermove 走 `feDraftPreviewMove()`,不觸發 `drawFaceEditor()` |
| `.draft-edge` / `.draft-rubber` / `.draft-preview-face` / `.draft-vertex` / `.draft-start-vertex` / `.draft-edge-len` / `.draft-corner-preview` / `.draft-align-guide` | 面內 | 草稿層內部元素 class(定義在 `app.css`);GEO-186(b) 後只有 `#feDraftLayer` 使用;`.draft-rubber.error` = 交叉/回頭警示態(變紅) |
| `#feLenInput` | 面內 | 鍵入長度浮動框;`feLenShow()` 讀 `fe.lenBuf`/`fe.drag.cur`/`fe.drag.pts`(兩者皆是鏡射 `fe.draft` 的相容欄位,見下) |
| `#mainEdgeLength${i}` / `#mainEdgeFixed${i}` / `#mainEdgeFree${i}` | 主畫布 | 主畫布 boundary 檢視器「外環邊 · 尺寸確認」清單(RC-POLYGON-PLAN §5.A.1.10);與面內 `#edgeLength${i}`/`#edgeFixed${i}`/`#edgeFree${i}` 同構,id 前綴不同(同一 DOM 中兩個檢視器面板同時存在,避免撞號);`data-edge-len`/`data-fix-edge`/`data-fix-val` 屬性沿用既有命名 |
| `.edge-list` / `.edge-row` | 共用(既有 class 延伸用途) | 主畫布版本沿用面內既有樣式 class;`querySelectorAll` 需以各自 pane 為根(`#inspectorContent` vs `#faceInspectorContent`)避免互相命中 |

全域狀態:

- `oc.drawTool`(`'rect' | 'hole' | null`;GEO-186(b) 後不再有 `'poly'`——P 是一次性動作)。
- `ocDrawCount`(number,`drawObjects()` 每次整份重畫累加一次的頂層 `let`;原 diff#4 的
  可觀測訊號,畫布草稿層移除後暫無消費者,保留供除錯)。
- `fe.draft`(面內 `PolyDraft` state;`feSetTool`/`resetSceneFocus`/`leaveFocus`/
  `openFaceWorkspace`/收尾成功後重置為 `PolyDraft.createState()`)。
- `fe.draftPreview`(`feDraftPreviewMove()` 的最近一次 `PolyDraft.previewMove()` 回傳)。
- `fe.drag`(既有欄位,語意改變:redraw 進行中時**不是**原始資料,是 `fe.draft` 的鏡射
  `{kind:"redraw", pts: fe.draft.pts, cur: fe.draft.cur}`,由 `feSyncDraftMirror()` 在
  每次 `fe.draft` 變動後同步;`fe.draft.pts.length===0` 時鏡射為 `null`——與舊版「未落
  第一點前 `fe.drag` 為 null」的語意完全一致,cdp_test 既有 §P9/§P10/B6-Esc 測試直接讀
  這個欄位,不需要更新)。
- `fe.lenBuf`(既有欄位,同樣改為鏡射 `fe.draft.typed` 的相容字串,供 `feLenShow()`/既有
  測試/面內既有 Esc 階梯第4級直接讀取)。
- `feGridStep()`(抽出既有 B4「依 zoom 挑 10/25/50/100/250/500/1000,螢幕間距 ≥24px」
  格距計算,`drawFaceEditor()` 畫格線與 `feDraftOpts()` 的 PolyDraft `gridMm` 共用
  同一份;面內 redraw 的格線吸附因此不是固定 `#faceGridSizeSelect` 值,是 B4 zoom 相依值
  ——對應 POLYDRAFT-API.md §6)。

不變:`#faceCanvasHint`(既有一行文字,未升級成三段浮標)、`feLenShow()` 函式本體、
面內既有 `#edgeLength${i}`/`#edgeFixed${i}`/`#edgeFree${i}`、面內 Esc 階梯的其餘五級
(輸入框焦點不攔截/收選單/關對話框/收方向小選單/離開工作區,`#feGuidePick` 等,
只有第4級「清鍵入長度」與第6級「清草稿」內部改呼叫 `PolyDraft.clearTyped`/清空 state)、
`polydraft.js`/`polydraft_test.js` 本體。

`serve.py` 的靜態檔白名單含 `/polydraft.js`(與 `/app.js`/`/reference-ui.js` 同組)——
`index.html` 在 `app.js` 之前插入 `<script src="polydraft.js">`,
沒有這行白名單瀏覽器會拿到 404、整個模組載入失敗。
## GEO-188 形狀編輯(cdp_test §P7b)

- select 工具**單擊邊 = 選取**(`fe.sel={kind:"edge",loop,i}`,畫布 `.face-edge-sel`),浮出 `#feActionBar`:
  外環邊 `op:notch`/`op:extend`/`op:push` + `fixity`;孔邊只有 `fixity`;外環凸角(`v:0:<i>`)只有 `op:corner`。
  Phase 2 的「單擊邊切 fixity」**改走** `#feActionBar [data-fe-act="fixity"]`(§9f 測試同步改)。
- 點操作 → `fe.op` + `#feOpPanel`(`[data-fe-param]` 數字 `input` 即時重畫 `[data-fe-ghost]`);
  Enter / `#feOpApply` → `feRectBool` 布林 → `emitBoundary` 交易;面消失或拆成兩片 → toast,不送指令。
- 成功後特徵記進 `fe.feats[bid]`(**只在本次工作階段**,不進 .scene);每次 `feAfterChange` 用
  `feFeatAlive` 驗活,對不上現況(含 undo)的自動剔除。
- Esc 階梯在「方向小選單」之後新增兩階:面板開著 → 關面板;有選取 → 清選取;再來才是原本的草稿/離開。

## GEO-189 描繪指定多邊形(cdp_test §P7c)

- 重畫外環:`redraw` 工具下 `keydown` 數字累積到 `fe.lenBuf`;`ArrowRight/Left/Down/Up` = 以該方向套一段;
  沒點第一點就打數字 → 草稿從 `(0,0)` 起;`Enter` 無數字 = 閉合(末點與起點不同軸自動補角),成功後 `feSetTool("select")`;
  `Backspace` 無數字 = 退一點。
- select 單擊面內空白 → `fe.sel={kind:"point",x,y}`,畫布 `.fe-point-mark`,浮動列只有 `op:hole`;
  面板欄位 `w`/`d`(高)/`dx`/`dy` + `[data-fe-ax]`/`[data-fe-ay]` 起算邊。點面外空白 → 清選取。
- 切角面板 `[data-fe-keep="w|d"]`(留 u/v 邊)與 `[data-fe-param="w|d"]` 連動;凹口面板 `[data-fe-keep="d"]`(留底)。
- 「開口」拖矩形(`hole` 工具)改走 `feRectBool`,矩形先裁到外環外接框,記進 `fe.feats`(type 由 `feClassifyRect` 判 hole/notch/corner)。
- 圖層列孔列有 `.face-layer-del`(拿掉那一環重宣告)。
- 特徵建立時以 `feNearestSides` 定下 `ax`/`ay`(較近一側),`feFeatMeta` 以現況外接框起算距邊。套用後不再自動選取該特徵(無 `.fe-feat-hi.sel` 殘留)。

## GEO-190 面內底圖臨摹(cdp_test §P42)

> 🔒 拍板:狀態只存 `oc.underlays[bid]`(本次瀏覽器工作階段記憶體),不寫 `.scene`/`localStorage`;
> `api("dump")` 輸出不得出現任何底圖資訊。

- 右欄檢視器第 6 分頁 `[data-fi-tab="underlay"]`(順序:屬性/形狀/參考線/角材/網格/底圖,共 6 頁;
  `#faceInspectorTabs [data-fi-tab]` 計數由 5 改 6)。沒載圖時分頁只有 `#ulFile`(`<input type=file accept="image/*">`)
  與一行說明;載入後才出現其餘欄位。
- 分頁欄位:`#ulOpacity`(range 0–1)、`#ulLock`(checkbox)、`#ulX`/`#ulY`(number mm,左上角在面座標的 mm,
  含義不因旋轉改變)、`#ulRot`(select 0/90/180/270)、`#ulScale`(唯讀顯示 `<mmPerPx> mm/px`)、
  `#ulCalibStart`(按鈕,進入量比例尺)、`#ulCalibDist`(number mm)+`#ulCalibApply`、`#ulRemove`。
- 畫布:`#feUnderlay`(`<image>`)是 `#faceEditorRoot` **第一個子節點**(在格線/面之下),
  `drawFaceEditor()` 每次清空重建時依 `oc.underlays[bid]` 重掛。
  `transform="rotate(rot,cx,cy) translate(x,y) scale(mmPerPx)"`(`cx,cy` 是未旋轉時圖片中心的面座標)、
  `opacity` 依 `ul.opacity`。**只有**「底圖」分頁作用中(`fe.fiTab==="underlay"`)、`fe.tool==="select"`、
  且未鎖定(`!ul.locked`)時 `pointer-events="auto"`,其餘情況 `"none"`——不擋既有的點邊/點角/點面/畫外環。
  切分頁(`fiShowTab`)、切工具(`feSetTool`)都會透過 `feUlSyncPointerEvents()` 就地同步這個屬性,不整份重畫。
- 量比例尺:`#ulCalibStart` → `fe.ulCalib={pts:[]}`(圖片原始像素座標,最多存 2 點,`feUlCalibAddPoint` 用
  `.slice(-2)`);畫布上 `<g id="feUnderlayCalib">` 用 `feUlImgToMm` 換算成面 mm 畫兩點與連線。進行中的
  `pointerdown`(不論落在哪、不論工具)一律被攔截去記校準點,不進 `feDown`。兩點齊了才允許填距離、
  `#ulCalibApply`(或 `feUnderlayApplyScale(distMm)`)套用:`mmPerPx = distMm / 兩點的px距離`,
  `x/y` 不變;套用後 `fe.ulCalib=null`,`#feUnderlayCalib` 消失。Esc 階梯在「就地操作面板」之前插一階:
  量比例尺進行中 → 只清 `fe.ulCalib`,不離開工作區。切離「底圖」分頁或切離 `select` 工具都會連帶取消
  進行中的量比例尺。
- 拖曳底圖:分頁作用中、`select` 工具、未鎖定,`pointerdown` 落在 `#feUnderlay` 上(且不是量比例尺進行中)
  → `fe.ulDrag={x0,y0,cx,cy}`,`pointermove` 只改 `oc.underlays[bid].x/y` 與 `#feUnderlay` 的 `transform`
  屬性(不呼叫 `drawFaceEditor()`,同 pan 的作法),`pointerup` 才 `renderFaceInspector()` 同步 `#ulX`/`#ulY`。
  `.fe-grid-line`/`.fe-origin-mark`(面內格線與原點標)在 `app.css` 設 `pointer-events:none`——這兩者本來就
  沒有任何點擊處理,但底圖插在最底層時,滑鼠剛好按在這些線上會讓 `e.target` 變成線而不是 `#feUnderlay`。
- 測試用全域(cdp_test 用它們避開檔案對話框與滑鼠模擬):`feUnderlaySet(bid,{src,imgW,imgH})`
  (建立預設狀態:`mmPerPx=外接框寬/imgW`、`x,y=`外接框左上、`rot=0`、`opacity=0.5`、`locked=false`,並重畫)、
  `feUnderlayCalibStart()`、`feUnderlayCalibPoint([px,py])`(直接餵圖片 px 座標)、
  `feUnderlayApplyScale(distMm)`、`feUnderlayRemove(bid)`。

## GEO-191 面內角材可選取(cdp_test §P43)

不做就地改錨點/方向/截面(語意未拍板);只做選取、高亮、可刪。

- 角材矩形(`.face-timber`,`drawFaceEditor()` 「角材 A0 足跡」段;`feTimberRect(t2)` 算矩形,
  drawFaceEditor 與 `feSelAnchor` 共用同一份算法,不各自重算)加 `data-face-hit="t:<id>"`;
  只有 `.face-editor-viewport.tool-select` 下 `pointer-events:auto`,其餘工具一律 `none`
  ——不擋既有的點邊/點角/點面/畫外環/放角材落點。
- select 工具下命中 `t:<id>`(`feDown`)→ `fe.sel={kind:"timber",id}`,清 `fe.op`/`fe.selFeat`;
  畫布該矩形加 `.sel`;左欄該列(`.face-layer-row[data-timber-id="<id>"]`)同步加 `.sel`。
  `#feActionBar` 浮出,只有一顆 `[data-fe-act="delete"]`;位置沿用 `feSelAnchor`/`fePlaceOverlays`
  既有擺法(矩形中心上方)。
- 角材頁(`fiShowTab("timber")`)頂端出現 `#tbSelected`:「已選角材 `<id>`」+ 宣告摘要
  (`L×A×B`、`@(u,v)`、`dir/side`、`role`——欄位照 `references` 指令 `timbers[].geometry` 有什麼就顯示什麼,
  見 `feTbSelectedHTML()`)+ `#tbSelDelete` 刪除鈕,走 `feDeleteTimber(id)` 共用路徑
  (`delete timber <id>` 走 `emitLine`/mutate,可 Ctrl+Z)。
- 左欄角材列:`mouseenter`/`mouseleave` 切 `fe.hoverTimber` → 畫布矩形加/清 `.hover`;
  點列(非 `.face-layer-del` ✕ 鈕)= 與畫布點選相同效果(選取+高亮+同步 `renderFaceInspector`)。
- 點面內空白(非角材)行為不變(GEO-189「點」選取);點外環邊/角行為不變——這兩條路徑
  若先前選的是角材,順帶 `renderFaceLayers()` 清掉左欄殘留的 `.sel`。
- Esc 既有階梯「有選取 → 清」自然涵蓋 timber(`fe.sel=null` 即可),一併清左欄 `.sel`。
- `feAfterShapeChange`(邊界變更/`feAfterChange` 收尾)與 `feDeleteTimber` 都會驗:
  選取的 timber id 若已不在 `fe.timbers` → 清 `fe.sel`。

## GEO-192 面內工作區的四種游標互動(cdp_test §P44)

- **A. Alt + 拖外環凸角 = 捏缺口**:`feDown` 的 `k==="v"` 分支,`ev.altKey` 且該點是外環
  (`loop===0`)凸角時進 `fe.drag={kind:"pinch",...}`,不進既有 `vertex` 拖曳;孔環頂點與
  非凸角一律照舊。拖曳中畫 `.fe-ghost.sub`(與就地操作減料預覽同一套視覺);矩形算法見
  `fePinchRect()`(頂點到游標,吸附 `feGridStep()`,裁到鄰邊長)。放開時矩形 ≥1mm 才送出,
  走與切角面板套用完全相同的路徑:`feRectBool("sub",rect)` → `emitBoundary` → 記進
  `fe.feats` `type:"corner"`(`feNearestSides` 定 `ax`/`ay`)。Esc 走既有「有 `fe.drag` → 清」
  那一階(`feSyncDraftMirror` 順便把 `fe.drag` 歸零),不用額外處理。
- **B. 拖預覽矩形的邊改尺寸**:`#feOpPanel` 開著、`fe.tool==="select"` 時,預覽矩形四邊
  各加一條 `<line class="fe-ghost-handle" data-fe-handle="left|right|top|bottom">`(見
  `drawFaceEditor`);`feDown` 命中它進 `fe.drag={kind:"opHandle",side,baseRect}`,
  `feMove` 呼叫 `feApplyGhostDrag(d,pt)` 即時改 `fe.op.params` 並 `feSyncOverlays()`+
  `drawFaceEditor()`,`feUp` 只結束拖曳、不套用(仍要 Enter/`#feOpApply`)。欄位對應規則
  (主迴圈定案,寫在 `feApplyGhostDrag` 函式註解):與母邊平行的邊界動 `w`(連動改
  `anchor:"start"`/`dist` 讓另一側不動)、垂直於母邊且不與母邊重合的邊界動 `d`(或 push
  的 `dist`);point/corner 目標比照對應欄位。`feSyncOverlays()` 的 `show` 判斷放行
  `fe.drag.kind==="opHandle"`,拖曳中面板才不會被既有的「有 `fe.drag` 就隱藏」邏輯關掉。
- **C. 右鍵選單**:`#feCtxMenu`(`role="menu"`,動態填 `[data-fe-act]` 按鈕)。內容來自
  `feActionsFor(fe.sel)`——`#feActionBar` 與 `#feCtxMenu` 共用這個函式,清單保證逐一相同;
  點擊都走共用的 `feRunAction(act)`。`fevp` 的 `contextmenu` 事件先呼叫
  `feClickSelectBlank`/`feClickSelectHit`(與左鍵單擊、`feUp` 的未移動分支、雙擊共用同一段
  選取邏輯,不複製)再 `feCtxMenuShow(clientX,clientY)`;面外空白右鍵不顯示選單。關閉走
  `feCtxMenuHide()`:點選單外(`document` capture 階段的 `pointerdown`)、Esc(階梯在
  「量比例尺」之前新增一階)、滾輪/縮放、`feSyncOverlays()` 發現不該顯示浮動列時。
- **D. 雙擊**:**不掛原生 `dblclick` 事件**——單擊選取本身會呼叫 `drawFaceEditor()` 整份
  重繪 SVG、`feSyncOverlays()` 重建 `#feActionBar` 的按鈕,第一下處理完那個節點就已經被
  拔掉,原生 `dblclick` 的 target 常常冒泡不到任何監聽器(`ev.detail` 在這個測試 harness
  送出的 `pointerdown` 上也量不到可靠的連續點擊數)。改成 `fevp` 的 `pointerdown` 監聽器
  自己量這次與 `fe.lastPD`(上一次 pointerdown 的時間/螢幕座標)的時間差/位移,450ms 內、
  ≤6px 視為雙擊,呼叫 `feHandleDblClick(pt,ev,onOverlay)`(`onOverlay`=這次點在
  `#feActionBar`/`#feOpPanel`/`#feCtxMenu`/`#feGuidePick` 上,此時改沿用第一下已經定案的
  `fe.sel`,不重新命中畫布)並 `ev.preventDefault()` 壓下這一下補發的 `click`,避免浮動列
  按鈕(例如角材的「刪除」)被誤觸發。這段判斷刻意放在既有的「點在浮動 UI 上就 return」
  之前,否則第二下如果剛好落在第一下才冒出來的按鈕上會被那條 return 攔截。實際開哪個
  面板由 `feDblOpenFor(sel)` 決定:外環邊 → `notch`;外環凸角 → `corner`;面內空白 →
  `hole`(該點為選取點);角材 → `fiShowTab("timber")`。拖曳中(`fe.drag`)不處理;
  參考線/面外空白無作用。
