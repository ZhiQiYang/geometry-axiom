# DOM 合約(測試依賴清單)

> 立案 2026-09-13(Phase 0 產出);Phase 1 改版更新。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。

## GEO-208 角材結構建模（目前合約）

- `#timber-space-v1` 連線完成後自動開「角材骨架範例」，`#smTryTimberFrame` 可隨時載入。範例不改使用者世界。服務 `/model/capabilities` 宣告 `space_preview_schemas`；確認支援 `/2` 才顯示「角材結構建模版」。舊服務明示未啟用，納入角材的請求不降級送出。
- `#smIncludeTimbers` 為建模選擇；`#smTimberCount`、`#smTimberCandidates` 顯示精確所選放置的角材與尺寸／世界高度。`#smTimberEmpty`、`#smBackToTimbers` 提供零支引導。候選與場景快照一致後才能採用。
- `#smShowTimbers` 只控制真實角材 mesh 顯示；`#smShowRoof` 只作用於空間殼。`#smTimberVolume` 獨立列材料量，`#smTimberReview`／`#smTimberReviewList` 在建立前核對支數及高度。`#smExportKind` 的 `timbers` 選項匯出完整角材套件。
- 新請求的 `input.timbers` 是非空 typed roots；省略時沿用 preview `/1`，有角材時為 `/2`，保存為 `geometry-canvas/4`。舊 `/1–3` 可讀且不補入角材；匯入在替換目前專案前完成五種套件驗證與保存輸入重建。
- 詳見 `TIMBER-IN-SPACE.md`；測試為 backend、project-store、model-viewer 及 `space_model_test.js`，`GEOMETRY_TIMBER_ONLY=1` 可單跑角材瀏覽器段。

## GEO-207 平面投影定義（版本及角材擴充見 GEO-208）

- `window.FaceProjection` 整合於現有 `app.js`，樣式在 `app.css`；沿用現有工作區。頁面與建模視窗的版本由 GEO-208 服務能力檢查決定。
- `[data-fp-edit][data-fp-placement]` 開啟指定面／放置的設定，`[data-fp-build][data-fp-placement]` 進入建立空間。面卡片、物件清單、面標題及檢查器呈現同一份定義；沒有定義時明說尚未指定。
- `#fpDialog` 原生 modal 包含 `#fpPlacement`（放置面）、`#fpPurpose`（`general`／`space-boundary-plan`）、`#fpView`（`top`／`bottom`）、`#fpInterior`（確認輪廓內為室內淨空、牆厚向外）、`#fpZ`（唯讀圖面高度）與 `#fpOutline`（世界座標投影示意）。`#fpApply` 保存設定，`#fpApplyBuild` 接續建模，`#fpCancel` 放棄草稿。
- 俯視為沿 −Z 看向 XY 平面，仰視為沿 +Z；`#fpOutline` 及建模輪廓依實際放置座標繪製。面內原本的 u→／v↓ 畫布標為「輪廓編輯圖」，不冒充世界俯視。改觀看方向不修改輪廓、放置、z 或材料牆外側方向。
- 只接受已放置水平面。未放置／垂直面提供放置操作引導；同邊界有多個放置時逐一設定，不按原始面編號共用。一般面可清除用途定義。
- `#smProjectionCallout`／`#smSetProjection` 引導自己的平面先完成定義；`#smProjectionSummary` 顯示已保存語意。尚未定義時禁止平面預覽及建立；組合既有面模式不受此限制。設定完成保留已填牆底、牆高與牆厚，但使舊預覽失效。
- `#smBottomHelp` 區分圖面 z 與牆底；`#smHeight` 新模型預設 3000 mm，`#smThickness` 預設 100 mm，牆底仍須明填。`[data-sm-view="top"]`／`[data-sm-view="bottom"]` 分別為真實 3D 俯視／仰視。
- `ReferenceWorkspace.getFaceProjection(bid, placementId)` 回傳複本或 `null`；`getFaceProjections(bid)` 列各放置；`setFaceProjection(bid, placementId, definitionOrNull)` 為可復原的本機操作，觸發 `face-projections-changed`。
- 專案有 `faceProjections` 或模型 `source.projection` 快照時使用 `geometry-canvas/3`；舊 `/1`、`/2` 可讀。刪除、重派或轉垂直的放置清除定義，復原恢復；水平平移及 z 改動保留。模型保留建立時快照，修改牆高沿用快照；舊模型標明未保存投影定義。
- 完整操作及資料契約見 `FACE-PROJECTION.md`；回歸包括 `test_face_projection_store.js`、`test_model_viewer.cjs`、`space_model_test.js` 與完整 `cdp_test.js`。

## GEO-205 從面建立空間（第一版，投影及格式更新見 GEO-207）

- `#btnSpaceModelTrial` 開矩形範例，`#btnSpaceModels`／`#spaceModelCount` 開模型庫；它們位於獨立 `.space-model-entry`，原 `.start-options` 仍保留兩個入口。面工具列 `#btnFaceSpaceModel` 使用目前面。
- `#smWorkspace` 為原生 modal，內含版本標記及三步引導。`#space-model-v1` 在連線完成後自動開範例，預覽不修改核心世界。
- `#smTryRectangle`／`#smTryLShape`／`#smUseCurrent` 切來源；`#smMode` 選 `plan` 或 `faces`。`#smBottom`／`#smHeight` 獨立於來源 z；自己的面牆底初始留空，牆高預設 3000 mm。`#smThickness` 預設 100 mm。新試用範例亦使用 3000 mm，已存模型保留原值。
- `[data-sm-edge]` 明確選擇側邊，`#smFloor`／`#smCeiling` 選面用途，`#smHoles` 明示貫穿孔；`[data-sm-face]`／`[data-sm-orientation]`／`[data-sm-purpose]` 組合既有面；`[data-sm-obstacle]` 選柱樑。
- `#smPreview` 經 `/model/space-preview` 取得經驗證的模型。`#smCanvas` 使用真實 mesh，支援旋轉、縮放、平移及角度切換；`#smShowRoof` 只影響顯示。`#smVolume`／`#smClearance`／`#smWallVolume` 分別呈現三種量，未定不顯示零。
- `#smReviewJump` 可直接到核對清單；`#smGeneratedFaces` 列各面朝向及用途，`#smConfirmFaces` 確認後才啟用 `#smCreate`。設定改動使舊預覽失效；自己的來源在建立前再讀 dump 比對。
- `#smLibrary`／`#smLibraryList` 列已建立模型，`[data-sm-open-model]` 重開模型，`[data-sm-remove-model]` 移除並可復原。`#smSave` 保存 `.gcanvas`，`#smExportKind`／`#smExport` 匯出指定角色套件。
- 平面模式的 `[data-sm-edit-height]`／`#smEditHeightButton` 打開 `#smHeightEditPanel`，以 `#smEditHeight` 修改正整數牆高；`#smCancelHeightEdit` 取消。沿用保存輸入及來源，只改高度並重新預覽；核對後 `#smCreate` 顯示「更新空間」，經 `updateSpaceModel` 更新同一 ID。過期預覽、模型被復原或上下文改變均不可覆寫舊資料。組合面模式不顯示此入口。
- ≤720px 用 `#smTabPreview`／`#smTabSetup` 切頁，`#smMobileNext` 直接到核對或保存；桌面低視窗縮小留白，保持可見模型及 44px 操作目標。
- `ReferenceWorkspace` 的 `addSpaceModel/updateSpaceModel/removeSpaceModel/getSpaceModels` 管理不可變紀錄；`tryLocalHistory(cmd)` 在發送核心 undo／redo 前分流本機步驟。`space-models-changed` 通知模型庫刷新。
- 含模型保存 `geometry-canvas/2`，全部模型驗證及重建比對成功才 `/upload`；失敗保留場景與專案。完整契約見 `SPACE-MODELING.md`，回歸為 `space_model_test.js` 及 `cdp_test.js` P65。

## 2026-09-27 UI/UX 審查更新（以本節為目前合約）

- 主頂列 `.tool-group` 顯示選取／平移與 `#btnNewRect`／`#btnNewPoly` 四種工具；左欄 `.start-options` 是描面、六面盒兩張起點卡，`.quick-create-grid` 只有 `#btnNewSpace`、`#btnNewColumn`、`#btnNewBeam` 一列。`#sceneList` 位於 `#fileMenuPop` 內，主頂列顯示 `[data-project-name]`／`[data-project-status]`。保存控制 `[data-project-action="save"]` 會在進出工作區時移動同一個 DOM 節點，工作區掛點為 `#workspaceProjectActions`；`#btnSaveProject` 是「另存新檔」選單入口。
- `#objectWorkspace` 只有 `.object-workspace-topbar` 和 `.object-workspace-statusbar`；已移除 `.workspace-project-bar`／`.workspace-file-menu`。工作區頂列借用主頂列的 `#fileMenu`，Esc 關閉 `#fileMenuPop` 而不離開工作區。`#shapeToolButton` 開啟 `#shapeToolPop [data-shape-action]`；選操作後以 `fe.queuedShapeAction` 等待邊／角，開口轉入既有開口工具。外環邊的浮動列和右鍵選單含 `[data-fe-act="timber"]`，沿選邊預填並放置角材。
- `#faceInspectorTabs [data-fi-tab]` 順序是 `prop,shape,components,underlay`，右欄對應 `[data-fi-pane]`。原 `guide,timber,grid` 仍可傳給 `fiShowTab()`，會打開構件頁並捲到 `[data-component-section]`。形狀庫 `#faceShapeButton` 由程式移入形狀頁；角材表單 `#tbPlace` 直接提交同一筆宣告與放置交易。`#faceReferenceSummary` 顯示來源，`[data-reference-step]` 表示選頁／校準／描外環。未放置面標示「未放置」。
- 空間左欄 `#spaceAddMembers` 在成員面標題旁；`#spaceSizeTools` 依平面圖放柱／樑工具移到頂列，三視圖不顯示放置工具。三視圖矩形工具使用 `#v3PlaneControls`、`#v3ToolbarSurf`、`#v3ExistingZ`、`#newZ` 顯示並修改工作面與高度。
- 審查項目與驗收流程見 `UIUX-REVIEW-2026-09-27.md`；下列舊節保留各階段的歷史決策，若其 DOM 位置或頁數不同，以本節為準。
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
| `#tbPlace` | 以當前表單設定直接送出 timber＋place 單一交易；畫布工具的點線放置仍可用 |
| `.fl-empty` | 五類圖層的空狀態；有可建操作者提供分頁入口 |
| `#spaceWorkspaceTools` / `#spaceAddMembers` / `#spacePlaceColumn` / `#spacePlaceBeam` | 空間工作區中間工具群 |
| `#workspaceKeyHints` | 面內 L/R/T/Esc；空間點放柱／拖放樑／Esc |
| `body.v3-picked` | 有三視圖選取才展開右欄；主畫布 `[data-tool]` 在三視圖 disabled |
| `.is-busy` | 觸發按鈕上的 spinner；不降低全頁透明度 |

移除 `#btnScene`（由場景選單載入）與 `#workspaceDoneButton`（只保留返回）。
`#btnDatums` 移進檔案選單；`#faceShapeButton` 現位於形狀頁的基底外環；
工作區 undo/redo/fit 移到右側操作群；尺寸 chip 跟隨 `#spaceWorkspaceTools` 中的放柱／放樑工具；`.space-plan-head` 移除。
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
| `#sceneList` / `#sceneMenuBtn` / `#sceneMenuPop` / `#sceneMenuLabel` | 範例選單(檔案選單內;`.scene-item[data-path]` 載入) | `hidden`、`.click()` |
| `#minimap` | 小地圖 canvas | `pointerdown` 導航;`oc.mmTf` 座標換算 |
| `#toastRegion` | toast 容器 | `.toast` 子元素計數 |
| `#objectWorkspace` | 面內/空間工作區覆層(fixed, z45) | `hidden` 切換檢查 |
| `#workspaceBackButton` / `#workspaceBackLabel` | 工作區返回 | `.click()` |
| `#workspaceTitle` / `#workspaceEyebrow` / `#workspaceTypeIcon` | 工作區標題列 | textContent |
| `#faceWorkspaceTools` | 面內工具列 | `[data-face-tool]` 子鈕 |
| `#faceUndoButton` / `#faceRedoButton` / `#workspaceFitButton` | 工作區 undo/redo/fit | `.click()` |
| `#objectWorkspaceContent` / `#faceWorkspaceLayout` | 工作區三欄容器 | 存在性 |
| `#faceLayerList` / `#faceLayerCount` | 左欄面內物件清單 | 子列 |
| `#faceReferenceVisibility` / `[data-ref-visible]` | 面內左欄的顯示控制；`all` 全部、`group:guides` 獨立線群組、`group:grid:<id>` 網格群組、`guide:<id>`／`grid:<id>:<axis>:<index>` 個別線 | 原生 checkbox 的 `checked`／`indeterminate`、鍵盤 Space；不送出幾何指令、不增加 undo |
| `#faceReferenceVisibility details` | 「選擇個別參考線」收合清單，列出當前網格草稿或已套用座標 | 切換不重建右欄，保留草稿及欄位焦點；手機標籤高至少 44 px |
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
| `#faceInspectorTabs` / `[data-fi-tab]` | 面內檢視器分頁 屬性／形狀／構件／底圖；構件頁有 guide/timber/grid 三段 | `.active`、`.click()`、`[data-fi-pane]` 顯隱 |
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
| `#tbAnchor` `#tbSelector` `#tbA` `#tbB` `#tbDir` `#tbSide` `#tbRole` | 角材引用、截面、方向與角色；長度由引擎推導(GEO-195:`#tbAnchor` 選項排序/後綴見下、`#tbRole` 依主支軸 `disabled` 見下) | `value` 讀寫、`#tbRole [disabled]` |
| `#tbAnchorAllOccupied` | 角材放置表單:所有定位引用都已被占用時出現的 `.fi-note`(GEO-195) | 存在性、textContent |
| `#tbSelected` / `#tbEditForm` / `#tbEditA` / `#tbEditB` / `#tbEditDir` / `#tbEditSide` / `#tbEditRole` / `#tbEditPri` / `#tbEditAnchor` / `#tbEditSelector` / `#tbEditApply` / `#tbSelDelete` | 角材頁頂端「已選角材」可編輯表單(GEO-191 唯讀摘要 → GEO-194 可編輯;`fe.sel.kind==="timber"` 時才出現)。A/B/方向/側/角色可預填(橋接有回傳);`#tbEditAnchor`/`#tbEditSelector` 橋接不回傳現有值,固定不預填(第一個 `<option value="">` 佔位) | 存在性、`value`、`.click()` |
| `.face-layer-row[data-timber-id]` | 左欄角材列(GEO-191;`.sel` 同步畫布選取,hover/click 有掛鉤) | `dataset.timberId`、`.sel`、mouseenter/mouseleave/click |
| `#gridMainAlong`、`#gridUSource` `#gridVSource`、`#gridU` `#gridV`、`#gridUStart`/`Step`/`Count`、`#gridVStart`/`Step`/`Count`、`#gridUPanel`/`Gap`/`From`、`#gridVPanel`/`Gap`/`From`、`#gridPreviewStatus`、`#gridCreate` | 網格主支長度方向與來源編輯器；新網格必選方向，舊網格可顯示未設定；核心唯讀預覽與建立／重宣告 | `change`/`input`、預覽文字、`.click()`、游離面 disabled |
| `[data-face-tool="grid"]`、`[data-grid-id] .grid-layer-open` | 網格工具與清單直接編輯；G 快捷鍵 | 打開同一份草稿與方向圖卡 |
| `[data-grid-direction]`、`[data-grid-axis] [data-source]` | 方向及來源分段按鈕；原 select ID 留作表單狀態 | `aria-pressed`、`aria-invalid`；來源切換保留輸入 |
| `#gridDraftBadge`、`#gridReset`、`#gridUError`／`#gridVError` | 已套用／草稿／錯誤狀態，重設與欄位錯誤 | 重設不改世界，錯誤透過 `aria-describedby` 關聯 |
| `[data-grid-label]`、`[data-grid-ruler]`、`.grid-line-chip` | 拖曳座標、邊尺新增與逐線鍵盤編輯 | Esc／pointercancel 取消拖曳；非明寫新增先說明來源轉換 |
| `#gridShowCanvas`、`#gridReturnSettings` | 手機滿寬設定／畫布切換 | 保留輸入與捲動位置，全圖包含座標標籤 |
| `#gridTimberPopover` | 角材工具 hover 網格線顯示角色及截面，明確改選角色 | 使用既有 `fePlaceTimberFromForm`，不自行建立模型規則 |
| `.face-timber` / `.face-grid-line` / `.face-grid-hit` | 面內角材足跡、帶角色樣式的網格線與角材工具下可點的格線命中層(`k:<grid>:<axis>:<index>`) | `#faceEditorRoot` 內計數；`.role-primary`／`.role-secondary`／`.role-unset` |
| `.fe-anchor-hi` / `.fe-anchor-band` / `.fe-anchor-band-label` | 角材定位引用預示(GEO-195;角材工具啟用中或 `#tbAnchor` 焦點/hover/改值中才畫;`.fe-anchor-hi` 是定位引用本身的虛線、`.fe-anchor-band` 是**橫向定位示意**帶(G196-R05:由 `feAnchorCrossRange` 依錨法語意算——`at-line` 置中 `[c-⌊A/2⌋, c-⌊A/2⌋+A]`、`at-face` 貼材料側、`at-face t<id>` 不畫;帶套 `#face-material-clip` 扣孔裁到有效區域;**不看 `#tbSide`/`#tbDir`**——±n 是法線厚度方向,不影響 2D 帶)、`.fe-anchor-band-label` 固定文字「橫向定位示意」。GEO-196:`fe.timberHoverAnchor` 非 `null` 時(滑鼠指著某條可命中線)改畫那條線,優先於 `#tbAnchor` 表單值) | `#faceEditorRoot` 內計數、隨 `fe.tool`/`fe.anchorPreview`/`fe.timberHoverAnchor` 出現與消失(不吃事件) |
| `[data-face-hit]` | 面編輯器命中層(`v:<loop>:<i>`/`e:<loop>:<i>`/`g:<id>:<axis>`/`k:<grid>:<axis>:<index>`/`t:<id>`)。角材工具下點外輪廓邊、參考線或網格線可直接定位放置；格線帶主支 2／副支 3 預設，手動角色覆寫仍保留；孔邊快捷仍不支援。`#tbSide` 仍決定法線厚度方向。 | pointerdown 命中(非同步 bhit 已由它取代) |
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
| `mutate` | 多行 DSL 交易(失敗回滾+toast) | 空間成員重宣告/六面盒使用;GEO-195 起支援第二參數 `opts.friendlyError(rawError)=>string`(可選,不傳=既有行為) |
| `toast` | 錯誤提示(bridge error 原文) | `#toastRegion` 子元素 |
| `fe` | 面內工作區狀態 | `fe.tool`、`fe.panX/panY/zoom`、`fe.drag/work`、`fe.guides`、`fe.projViews`、`fe.sel/op/feats/selFeat`(GEO-188;`fe.sel={kind:"timber",id}` GEO-191)、`fe.hoverTimber`(GEO-191)、`fe.anchorPreview`(GEO-195)、`fe.timberHoverAnchor`(GEO-196:角材工具下滑鼠所指的可命中線,只記引用不記側,見下;G196-R02 移除 `fe.timberHoverSide`) |
| `feAnchorLineInfo` / `feAnchorOccupied` | 定位引用式 → `{constAxis,value}` / 占用判斷(GEO-195;依 `fe.timbers` 足跡,距離 ≤ 占用角材 `A`/`B`+1mm 算占) | 純函式(`feAnchorOccupied` 讀 `fe.timbers`/`oc.bmap`),測試可直接呼叫 |
| `referenceAnchorEntries` | 定位引用結構化清單 `[{value,label,occupied}]`(GEO-195;`referenceAnchorOptions` 據此排版) | 測試可直接呼叫比對排序/後綴 |
| `feTimberPrimaryAxis` / `feTimberRoleOptionsHTML` / `feTimberSyncRoleOptions` | 主支軸推導 / `#tbRole` 選項 HTML(依主支軸 `disabled`) / `#tbDir` 改值時重算並在原選項被 disable 時自動切換(GEO-195) | 測試讀 `#tbRole option[disabled]` |
| `feAnchorDirFromInfo` / `feAnchorSideForPoint` / `feTimberRoleForClick` | GEO-196:`info→"+u"/"+v"` / `(info,pt)→"+n"/"-n"` / `(bid,kind,dirAxis)→` 角色,點畫布上的線直接放置時算 dir/side/role 用的三個純函式 | 純函式,測試可直接呼叫 |
| `feTimberPlaceErrorMessage` | 角材放置失敗訊息人話化(GEO-195;`feDown` 的 timber 分支透過 `mutate` 的 `opts.friendlyError` 呼叫) | 純函式,測試可直接呼叫比對前綴文字 |
| `feTimberHintRefresh` | 角材工具下重算 `#faceCanvasHint`/狀態列文字(GEO-195 起;GEO-196 加點線放置;G196-R02 改字為「點外輪廓邊或參考線選定位直接放置;厚度方向依右欄「深度」設定。…」) | `fe.tool!=="timber"` 時 no-op |
| `fePrimaryAxisInfo` / `feTimberPrimaryAxis` | D17 主支軸推導(G196-R04):同面 primary 的軸一致→該軸;無 primary 由 boundary 的垂直方向推(src="boundary");皆無→未定義;矛盾→`conflict`(不自選、不挑第一支)。`feTimberPrimaryAxis` 是只回軸的薄包 | 回傳 `{axis,conflict,src}`;`fe.timbers` 為目前工作區那面 |
| `feAnchorCrossRange` / `fePointInLoop` | 預示帶橫向範圍(G196-R05,唯讀):`at-line` 置中、`at-face` 貼材料側(外邊=環內側、孔邊=孔外側,用邊中點±0.5mm 法向做點在環內測試,不靠畫布中心/L 形也對)、`at-face t<id>`→null 不畫 | 回傳 `{constAxis,lo,hi}` 或 null;不寫回狀態 |
| `feStartOp` / `feApplyOp` / `feCancelOp` / `feRectBool` | 形狀編輯(GEO-188):就地操作與正交矩形布林 | 測試直接呼叫 `feCancelOp()`;`feRectBool(loops,op,rect)` 純函式 |
| `feDeleteTimber` | 刪角材共用路徑(GEO-191;`delete timber <id>` + 清選取/重載) | 測試可直接呼叫 `feDeleteTimber(id)` |
| `feTimberEditApply` | 面內角材就地編輯(GEO-194;同一 id「刪掉重放」一筆 `mutate`:`delete timber <id>`→`timber <id> …`→`place <id> on …`,失敗 `mutate` 自己回滾+toast、成功後選取留在同一 id) | 測試可直接呼叫 `feTimberEditApply(id)`(需先填好 `#tbEditForm` 欄位) |
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
- 頂列三段:`.brand`(專案名)→ `.tool-group`(選取／平移／矩形／多邊形，含 `<kbd>` V/H/R/P)→ `.top-actions`(復原重做、視圖、檔案選單、保存狀態與主保存鈕)。
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
- GEO-203：顯示設定只作用於面內畫布，隱藏線、座標標籤及命中範圍，角材定位預示也遵循它；線的定義、引用選單及已放角材仍保留。每個面分別記住本次檢視設定，離開再進入、重繪及欄位更新不重設；換場景或重新整理恢復顯示。新產生的線預設顯示。三視圖投影及匯出不受影響。

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

- A3:`.quick-create-grid` 為 3 欄 × 1 列（空間、柱、樑）；六面盒移到兩張起點卡的第二張。
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
>
> **GEO-193**:`feDraftTryClose` 呼叫 `PolyDraft.tryClose` 成功後,把回傳的 `dropped`
> 陣列轉交 `feCommitDraft(pts, dropped)`;`emitBoundary` 成功、`dropped.length>0` 時
> `toast`+`setStatus` 提示「已閉合;補角時 (x,y)、(x,y) 併入直線——若要保留該轉折,
> Ctrl+Z 後把下一段畫完再閉合」(座標依 `dropped` 順序列出、用「、」隔開)。這是提示,
> 不是阻擋:自動補角把使用者剛畫的轉折併成直線,與「使用者故意少畫最後一段、想要矩形」
> 幾何上無法區分,不改變任何閉合結果、不彈對話框。對應斷言 `cdp_test.js` §P45。

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

> 原本僅限本次工作階段；2026-09-26 使用者核准 GEO-198：底圖、校準及來源紀錄可隨 `.gcanvas` 保存。
> `oc.underlays[bid]` 是目前場景作用中圖頁的投影；不寫 `.scene`/`localStorage`，`api("dump")` 不含底圖資訊。

- 右欄檢視器第 4 分頁 `[data-fi-tab="underlay"]`。沒載圖時有 `#refImport`、相容用隱藏 `#ulFile` 及保存說明；載入後才出現對位與校準欄位。檔案入口接受 PDF、PNG、JPEG、WebP、GIF。
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
- 角材頁(`fiShowTab("timber")`)頂端出現 `#tbSelected`:「已選角材 `<id>`」+ 可編輯表單
  `#tbEditForm`(GEO-194,見下節)+ `#tbSelDelete` 刪除鈕,走 `feDeleteTimber(id)` 共用路徑
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

## GEO-194 面內角材就地編輯(cdp_test §P46)

**先查明的事實**(實作前必讀,免得表單預填假資料):`fe.timbers` 來自 `references`
橋接指令(`geometry-web/reference_bridge.inc::cmd_references`,經 `web_bridge.c`
unity-build 進 `current_geometry.c`),對每支角材回傳 `{id, role, geometry:{surface,
centerline, length, u, v, dir, side, A, B, origin, axes}}`(`json_reference_geometry`)。
**沒有 anchor/selector(至-face/at-line 的具體引用式)、也沒有 priority**——這兩者
`place`/`timber` 的原始宣告參數,核心目前不回吐。`app.js::feLoadGuides()` 把
`geometry` 展開進每個 `fe.timbers[]` 元素(`{id,role,...t.geometry,L:t.geometry.length}`)。

- 角材頁 `#tbSelected` 區塊(GEO-191 唯讀摘要)改成可編輯表單 `#tbEditForm`(見上方
  「必須保留的 DOM id」表):A(`#tbEditA`)、B(`#tbEditB`)、方向(`#tbEditDir`,
  `+u/-u/+v/-v`)、側(`#tbEditSide`,`+n/-n`)、角色(`#tbEditRole`)+ priority
  (`#tbEditPri`,只在 `role==="custom"` 時顯示,同 `tbPlace` 表單的既有連動)——這五組
  橋接有回傳,`feTbSelectedHTML(bid)` 直接預填目前值。定位引用(`#tbEditAnchor`)+
  選段(`#tbEditSelector`)重用放置表單的選項來源 `referenceAnchorOptions(bid, surf)`,
  但**固定不預填**(下拉第一個選項是空字串佔位「橋接不回傳現有錨點,請重選」)——
  這是本票故意的行為,不是漏做,理由見上段「先查明的事實」。
- 按鈕 `#tbEditApply`「套用變更」→ `feTimberEditApply(id)`:驗證同 `tbPlace`(A/B 正整數、
  custom 要 priority ≥1、錨點必選,驗證失敗 `feMarkInvalid` 標紅對應欄位、不送指令),
  通過後組一筆 `mutate([...])` 批次、**同一個 id**:`delete timber <id>` →
  `timber <id> A B role …` → `place <id> on <sid> anchor selector dir side`。
  `mutate()` 的 `history-begin`/`history-end` 群組本身就是原子的(任一行失敗核心整組
  回滾、`abort` 冪等驗證回滾),**不需要**額外的 dump/undo 保底。成功後
  `feLoadGuides()` + 選取留在同一 id(`fe.sel={kind:"timber",id}`)+
  `renderFaceLayers()`/`drawFaceEditor()`/`renderFaceInspector()`;失敗
  `mutate()` 自己 `toast` 原文、不動狀態(`feTimberEditApply` 直接 return false)。
- 影響預覽:刪除唯一的 `role boundary` 角材或改動被引用的邊,`delete timber`/`place`
  這兩行任一觸發 I8a 時,`mutate()` 內部逐行呼叫的 `api()` 本來就會攔截 `result.preview`
  開 `confirmReferenceImpact` 對話框並等待使用者確認/取消,`feTimberEditApply` 不必
  另外處理,直接吃 `mutate()` 的回傳值即可(不繞)。
- `Ctrl+Z` 一次回到編輯前:因為 `mutate` 的三行是同一個 history 群組,單步 undo 涵蓋
  整批(delete+timber+place 一次復原)。
- 表單驗證與 `tbPlace`(放置表單)一致:A/B 正整數、custom 要 priority、錨點必選。
- 角材列/畫布高亮邏輯不變(GEO-191 既有 `.sel`/`hover` 機制,`feTimberEditApply`
  完全不碰)。

## GEO-195 面內「角材放置」表單 UX 止血(cdp_test §P47)

不改放置流程(點擊位置一律只是「確認」,不是落點輸入)、不改引擎、不改 `.scene`；
只讓人在點擊前就知道角材會落在哪、為什麼失敗、該怎麼改。

- **預設定位引用挑一條沒被占的線**:`feAnchorOccupied(bid, anchorValue)` 依
  `feAnchorLineInfo(bid, anchorValue)` 把定位引用式(`at-face e<i>`／`at-face h<h>e<i>`／
  `at-line guide <id>`／`at-line grid <id> u|v <idx>`)換算成 `{constAxis:"u"|"v", value}`
  (哪個座標軸固定、固定在哪個值;`at-face t<id>` 角材側面回 `null`,不判占用),
  再看 `fe.timbers` 有沒有哪支的 `feTimberRect` 足跡貼著這條線(只比對「深度軸」——
  角材沿 u 跑深度就在 v、反之亦然;定位引用的固定軸要等於該角材的深度軸才算數,不然
  一支貫穿全長的角材會讓所有垂直於它的線都被誤判成占用,見 GEO-195 修正紀錄——
  距離 ≤ 該角材 `A` 或 `B` + 1mm)。`referenceAnchorEntries(bid, surf)`(app.js)把每條定位引用連同
  `occupied`(佔用角材 id 或 `null`)包成結構化清單,`referenceAnchorOptions`
  (reference-ui.js)據此排版:未占用排前面、占用的排後面(兩組各自維持原順序),
  占用的文字後加 `(已有角材 N)`;瀏覽器 `<select>` 沒標 `selected` 時預設選第一個
  `<option>`,重排後第一個自然是第一條未占用,不需要另外設定。全部占用時不重排,
  `#tbAnchorAllOccupied`(`.fi-note`)出現,文字「所有定位引用都已有角材，先加參考線(L)」。
  `#tbEditAnchor`(GEO-194 編輯表單)沿用同一份 `referenceAnchorOptions`,但它前面自帶
  空字串佔位選項,不受這次重排影響(仍然固定不預填)。
- **畫布預示落點**:`fe.anchorPreview`(bool)——`#tbAnchor` 的 `focus`/`mouseenter` 設
  true,`blur` 設 false,`mouseleave` 依 `document.activeElement === tbAnchorSel` 判斷,
  `change` 觸發一次 true(見 `renderFaceInspector` 綁定段)。`drawFaceEditor()` 在
  `fe.tool==="timber" || fe.anchorPreview` 時畫 `.fe-anchor-hi`(定位引用本身,貫穿全圖
  虛線,用 `feAnchorLineInfo` 換算)+ `.fe-anchor-band`(依目前 `#tbSide`/`#tbA` 示意角材
  會占的半透明帶,寬 = A,沿定位引用的固定座標軸展開,文字標「示意」——真正長度由引擎依
  支撐推導,這裡只畫全圖範圍近似;不看 `#tbDir`,方向只決定角材沿哪軸「跑」,不影響帶要
  畫在哪)。`feSetTool` 切工具
  離開/進入 `"timber"` 都補一次 `drawFaceEditor()`;`fiShowTab` 切離「角材」頁清
  `fe.anchorPreview` 並重繪。`#tbA`/`#tbB`/`#tbDir`/`#tbSide` 改值都連動重畫(帶會跟著變)。
  角材工具下 `#faceCanvasHint`/狀態列改走 `feTimberHintRefresh()`:文字「角材將沿
  「〈定位引用名〉」放置，點面內任一處確認；點擊位置不影響位置 · A…×B… · Esc 取消」,
  `#tbAnchor` 改值時同步重算(`feTimberAnchorLabel` 讀 `referenceAnchorEntries` 找標籤)。
- **失敗訊息講人話**:`feTimberPlaceErrorMessage(err, bid, surf, anchorValue)`——
  `feDown` 的角材分支呼叫 `mutate([...], { friendlyError })`(`mutate()` 新增可選
  `opts.friendlyError(rawError)=>string`,不傳就是既有行為,不影響其他呼叫點)。依錯誤
  原文前置一句、原文接在後半(`\n` 分隔,同 `confirmReferenceImpact` 既有的 `\n` 慣例):
  含「中線上沒有任何合法跨距」→「〈定位引用名〉已被角材 N 占滿——請換定位引用
  (可用:〈未占用清單〉)」(全部占用時改「請先加參考線(L)」),並 `feMarkInvalid($("tbAnchor"))`;
  含 `V_PRIMARY_AXIS` →「主支軸是 〈u|v〉:沿它放只能選 primary;boundary/secondary
  要垂直於它」,`feMarkInvalid($("tbRole"))`;含 `V_CUT_PRIORITY` →「貼外輪廓邊的角材
  要選 boundary」,`feMarkInvalid($("tbRole"))`;其他錯誤原文不動。
- **角色選項依主支軸排除**:`feTimberPrimaryAxis(bid)`——`fe.timbers` 若有 `role==="primary"`
  的角材,主支軸 = 那支 `dir` 的軸(`"+u"/"-u"→"u"`,`"+v"/"-v"→"v"`);沒有就 `null`
  (角色不受限)。`feTimberRoleOptionsHTML(bid, dirValue, currentRole)` 依目前 `#tbDir`
  值算:方向與主支軸平行 → 只有 `primary` 可選,其餘 `disabled` 並在文字後加
  「（需垂直於主支軸）」;垂直 → `primary` `disabled`(加「（沿主支軸才能是主支）」),
  其餘可選。`#tbDir` 的 `change` 呼叫 `feTimberSyncRoleOptions(pane)` 重算 `#tbRole`
  的 `<option>`;原本選的角色若變成 `disabled`,自動跳到第一個可選項並 `toast` 一句
  說明(`type:"ok"`)。初次渲染時 `feTimberRoleOptionsHTML` 直接產生帶 `selected` 的
  HTML,不需要額外同步。
- 全部只動前端(`geometry-web/app.js`、`geometry-web/reference-ui.js`、`app.css`);
  `.scene`、`web_bridge.c`、`reference_bridge.inc`、`serve.py` 不動。

## GEO-196 角材工具下「點畫布上的線」直接放置(cdp_test §P48)

在 GEO-195 的基礎上加一條**新的**路徑,舊路徑(右欄表單 + 點面內空白)一字不改、
仍然是唯一的「表單驅動」放置方式。

- **命中判定**:`fe.tool==="timber"` 的 `pointerdown`(`feDown`)先看
  `ev.target.closest("[data-face-hit]")`(以**當次事件的實際 target** 為準,不由
  吸附後的座標反推線——G196-R03):
  - 命中外輪廓邊 `e:0:<i>` 或參考線 `g:<id>:<axis>` → 以那條線為定位引用,
    **定位/方向/角色**改由點擊決定並寫回 `#tbAnchor`/`#tbDir`/`#tbRole`
    (方便連放沿用這次帶入的值),**但 `#tbSide` 不寫**——`+n`/`-n` 是 B 厚度朝
    承載面法線哪側(G196-R02,對應 C 端 `depth_side`),不是面內左右;面內左右由
    定位引用本身決定(at-line 中線對齊、at-face 材料側貼齊,I13),兩者不能混用。
    命中的線其引用解析失敗(如參考線剛被刪)→ 報錯且不送,不靜默退回表單另一條
    引用(G196-R03)。之後走既有 `mutate([timber…, place…], {friendlyError})`
    放置路徑,一字不改。
  - 命中孔邊 `e:<h≠0>:<i>` → `toast("目前不支援直接點孔邊——請從右欄「定位引用」
    選孔邊(at-face h<i>e<j>)")`(G196-R02 改字:快捷點選目前不支援孔邊,但 I13
    的 `at-face h<i>e<j>` 表單路徑一直在——訊息只說明快捷限制,不宣稱公理禁止),
    不送指令、不動表單。
  - 命中面內空白(`ev.target.closest` 找不到 `[data-face-hit]`)或其他元素(頂點/角材,
    `.face-timber` 在角材工具下 `pointer-events:none`,見 app.css,本來就不會被命中)→
    **照舊**,用 `#tbAnchor`/`#tbDir`/`#tbSide`/`#tbRole` 表單目前值放置(含負向
    長度軸,點線邏輯不得重設表單值——G196-R02)。
  - GEO-202：格線以 `.face-grid-hit[data-face-hit="k:<id>:<axis>:<index>"]` 命中；
    hover 顯示角材放置帶及角色卡，直接點線沿用同一個定位／角色流程。
- **方向**:`feAnchorDirFromInfo(info)`——`info.constAxis==="v"`(線沿 u 跑)給 `"+u"`,
  `"u"`(線沿 v 跑)給 `"+v"`。固定取正向,不取負向;外輪廓邊的既有走向(逆時針/順時針)
  不採用,理由:與參考線統一同一條規則、不必分兩套。
- **側**(G196-R02,已修正):**不再由點擊位置決定**。舊實作的
  `feAnchorSideForPoint(info, pt)`(依點在線的哪一側覆寫 `+n`/`-n`)已移除——
  那會把面內左右位置誤當成法線厚度方向,導致點線任一側時 side 被點擊覆寫。
  修正後:快捷點線**不寫** `#tbSide`,一律沿用右欄表單值;hover 也一律只看表單值。
- **角色**:`feTimberRoleForClick(bid, kind, dirAxis)`——G196-R04 改用完整的
  D17 推導 `fePrimaryAxisInfo(bid)`(同面所有 primary 的長度軸一致→該軸;無
  primary 由 boundary 的垂直方向推;皆無→未定義;矛盾→`conflict` 不自動選、
  toast 診斷):主支軸已定義 → 方向平行給 `primary`,垂直給 `boundary`(邊)或
  `secondary`(參考線);未定義 → 外輪廓邊給 `boundary`、參考線給 `primary`
  (首支規則不變)。`feTimberRoleOptionsHTML` 與自動點選共用同一份推導;
  **custom 不因方向被停用**(D15:custom 的 priority 只參與 I19 比較,方向合法性
  交核心判)。
- **佔滿**:點到已占用的線**照舊送出**,前端不擋、不比對佔用——由引擎拒絕,GEO-195 的
  `feTimberPlaceErrorMessage` 人話訊息接手(前端佔用判定只是近似,見 GEO-195 節)。
- **hover 預示**:角材工具下 `pointermove`(`feMove`)只追蹤 `fe.timberHoverAnchor`
  (命中線的定位引用式字串,只認外輪廓邊與參考線,同 `feDown` 的判斷)——G196-R02 起
  **不再追蹤側向**(`fe.timberHoverSide` 移除);`drawFaceEditor()` 的
  `.fe-anchor-hi`/`.fe-anchor-band` 區塊在 `fe.timberHoverAnchor` 非 `null` 時改畫
  這條線(橫向範圍由 `feAnchorCrossRange` 算,與表單一致);離開線
  (`fe.timberHoverAnchor===null`)回到表單值,行為與 GEO-195 相同。
  離開畫布(`pointerleave`)、切工具(`feSetTool`)都清空 `fe.timberHoverAnchor`。
  hover 不送任何修改世界指令(G196-R03 §P50)。CSS:`.face-editor-viewport.tool-timber`
  下,外輪廓邊/參考線的命中線 `cursor: copy`,孔邊 `cursor: not-allowed`
  (格線無命中元素,不在此列)。
- **預示帶語意(G196-R05)**:`.fe-anchor-band` 的橫向範圍由 `feAnchorCrossRange(bid,
  anchor, A)` 唯讀算出——`at-line` 置中 `[c-⌊A/2⌋, c-⌊A/2⌋+A]`(多的 1mm 恆在
  +cross 側);`at-face` 外環邊貼外環內側、孔邊貼孔外側(I13 材料側);`at-face
  t<id>` 回 `null` 不畫帶(側由核心 R21(d) 判,前端無足夠資訊不亂畫)。帶套
  `#face-material-clip`(evenodd:外環扣孔)裁到有效區域;帶上文字固定
  「橫向定位示意」——只是位置示意,最終長度/跨距由核心決定。
- **提示文字**:`feTimberHintRefresh()` 改為「點外輪廓邊或參考線選定位直接放置;
  厚度方向依右欄「深度」設定。點面內空白則依右欄設定(目前「〈定位引用名〉」)放置
  · A…×B… · Esc 取消」(G196-R02:不再承諾「點在哪一側就放哪一側」)。
- 全部只動前端(`geometry-web/app.js`、`app.css`);`.scene`、引擎、放置流程本身
  (仍是同一段 `mutate`)不動。Esc、其他工具、選取邏輯不動。

流程層「點畫布上的邊直接放」已在本票做完;格線命中(若日後補上 `data-face-hit`)、
角材側面(`at-face t<id>`)當定位引用可否點選——留給下一票。

## GEO-197：連線、草稿與放材前置條件

- `#connectionNotice`：載入／錯誤狀態提示，位於工作區之外，`role="status"`。
  `#connectionRetry` 重新讀取場景；不重送失敗操作。載入與錯誤期間主工作區
  使用 `inert`，文件快捷鍵也停用。未讀到場景的計數顯示 `—`，不顯示建立第一物件的空狀態。
  已讀到過則保留最後完整快取，明示可能過期。HTTP 403 不放寬來源驗證。
- `#faceDraftNotice`：重畫外環時在畫布上方占獨立列，不能遮住落點。
  `#faceDraftTitle` 顯示草稿頂點數，`#faceDraftMessage` 說明原輪廓、面積與返回保留。
  `#faceDraftFinish` 走既有閉合驗證；`#faceDraftCancel` 只清草稿，不刪面。
  Esc 階梯保持原樣。原輪廓改用灰色虛線，草稿維持綠色。
- `#tbGoPlace`：游離面的角材頁提供「先放置這片面」，切屬性頁並聚焦其
  `#placeOX`。必須在 `#faceInspectorContent` 內找欄位，避免命中背景檢查器的同名欄位。
  未放置時角材工具停留選取模式，無材料預示。
- `#tbSuggestion`／`#tbUseSuggestion`：顯示及套用與點線入口相同的方向、角色建議。
  新表單及改定位引用時自動建議；手選角色後保留選擇，直到按套用建議或直接點線。
  `data-tb-role-manual` 記錄這項表單意圖，重繪時保留，不寫入 `.scene`。
  截面、深度、自訂優先序不因套用建議被改掉。核心仍可拒絕不合法的組合。

回歸：`cdp_test.js` P53–P56；可用 `GEOMETRY_FLOW_REPAIR_ONLY=1` 單跑。

## GEO-198 PDF、來源紀錄與專案保存（P57–P61）

- 檔案選單：`#btnImportReference`、`#btnOpenProject`、`#btnSaveProject`、`#btnProjectName`。檔案輸入為 `#referenceFile`、`#projectFile`；舊 `#file` 仍只載入 `.scene`。
- `#referenceDialog` 是原生 modal dialog。取消／Esc 不建立面；`#refApply` 成功後才關閉。讀取失敗時保持停用並由 `#refPreviewMessage` 說明。
  套用期間使用 `inert` 並保存已確認圖頁與取景，非同步建面完成前不能改頁；失敗後解除 `inert` 以便重試。
- 選頁／預覽：`#refPageNumber`、`#refPageCount`、`#refPrev`、`#refNext`、`#refZoom`、`#refThumbnails`。只算繪作用中頁及附近最多五張縮圖。
- 取景：`#refPagePreview` 上拖曳，`#refCropOverlay` 顯示範圍；`#refResetCrop` 恢復整頁。`#refTarget` 選既有面或 `new`，新面沿用預設矩形與草稿提示。
- 面內：`#refImport` 匯入，`#refMorePages` 重用完整來源檔，`#refActivePage` 切换已關聯頁；切頁不新增相同面的返回堆疊。
- `#refCalibrationStatus` 區分未校準／已校準；`#ulCalibUnit` 提供 mm／cm，核心距離仍為整數 mm。圖片保留 `#ulScale` mm/px；PDF 隱藏像素比例列，使用校準紀錄說明。
- 對位／比例或已校準面的輪廓改變時要求核對；`#refConfirmChecked` 只清除核對提示，不修改幾何。`#refFit` 對齊取景範圍。
- 來源紀錄：`#refRecordDetails`、`#refRecordLabel`、`#refRecordLocation`、`#refRecordValue`、`#refRecordUnit`、`#refRecordDatum`、`#refRecordAdd`。數值留空為 `null`；刪除按鈕使用 `data-ref-remove-record`。
- 來源／圖頁名稱一律作文字輸出；沒有幾何以外的命令執行通道。紀錄不自動建立 RC 或 3D 物件。
- 存檔測試入口：`ReferenceWorkspace.exportBytes()` / `importBytes(bytes)`；來源選頁入口 `sourceFromFile(file)` / `openSource(source,bid)`。正式 UI 與測試使用相同實作。
- 回歸保留 GEO-190 的 `feUnderlaySet/CalibStart/CalibPoint/ApplyScale/Remove`；`feUnderlaySet` 會把既有圖片納入目前場景的來源關聯。
- 儲存取消不改場景；写入失敗不清未保存狀態。已產生下載不等於檔案已寫入成功。
- 保存／開啟期間在文件捕捉階段阻擋點擊與輸入事件；只攔 `pointerdown` 不足以阻止按鈕的後續 `click`。
- `/api` 寫入回應遺失時，先依一次性請求識別查回結果，再更新來源歷史；重新連線不重送修改，尚未完成的群組確認後中止。
- 載入回應遺失時停止編輯，重試先比對核心 dump，確定使用載入前或載入後來源；無法判定時重試原載入並放棄無法證實的來源歷史，不按同號面猜接底圖。
- 完整格式、歷史與限制見 `REFERENCE-PROJECT.md`。核心、`.scene` 文法與公理未變。

## GEO-199 自訂游標（P62）

- `svg.cx-layer` 提供指標圖形、動作膠囊及吸附標記；`pointer-events:none`，不攔截原有畫布操作。
- `cx-on` 只在畫布顯示自訂指標時隱藏原生游標；按鈕、表單及離開畫布時恢復。
- 底圖捕捉指標拖出視窗時，`elementFromPoint()` 可為 `null`；空命中仍須安全處理。

## GEO-200 參考描面工作區（P63）

- `[data-project-action="save"]` 是畫布／工作區共用的同一個保存控制；工作區掛點為 `#workspaceProjectActions`。`#btnSaveProject` 選單入口是「另存新檔」。
- `[data-project-name]`／`[data-project-status]` 顯示目前來源上下文的名稱及狀態。成功關閉寫入才顯示「已保存」；下載顯示「已產生下載 · 請確認檔案」。
- `#btnExport` 保留原事件與識別，位於 `#fileMenuPop`；物件工作區移用同一個檔案選單。Esc 只關閉這個選單。
- `[data-project-action="import"]` 是物件庫及面內左欄的 PDF／圖片入口，仍使用 `#referenceFile`、`#referenceDialog`；取消不新增物件。
- `#faceReferenceSummary` 顯示實際來源、頁碼及校準狀態；點擊回到底圖頁。四個檢視器分頁的選取狀態使用 `aria-pressed`。
- 底圖分頁優先顯示 `#ulCalibStart`、`#ulCalibDist`、`#ulCalibUnit`、`#ulCalibApply`。`#refDrawOutline` 進入既有外環工具。
- `#refAlignmentDetails`、`#refSourceDetails`、`#refRecordDetails`、`#refPlacementDetails` 提供次要操作；原對位控制項位於展開區。`#refGoPlace` 回到原放置表單。
- 同一圖頁及同一組校準點的未套用距離保留；切換圖頁或重新取點不帶入舊值。
- ≤680px 開始取點時收起檢查器；`#calibrationCanvasPrompt` 保留進度與 `#cancelCalibration`。第二點後重開檢查器並聚焦距離；取消不改既有校準。
- `#refZoom` 預設 `page`（適合整頁）；其餘比例選項與取景來源座標不變。`#refResetCrop` 名稱改為「清除取景框」。
- 未套用外環或校準草稿會提示並阻止專案保存，避免將未套用的資料誤認為已保存；其餘核心驗證及幾何語意維持原樣。

## GEO-204 子網格（D19 / I25 / R23）

- 主網格編輯器的 `#subgridNew` 建立局部子網格；沒有已保存主格時停用。`SubgridEditor` 使用同一個 `[data-component-section="grid"]`，沒有第二套工作區。
- `#subgridCellChoice` 依主格座標與面外接 min/max 去重，列出有效面交集有正面積的格子；值為 `uLo|uHi|vLo|vHi` 四個來源參照，例如 `line:0|line:1|min|line:0`。已被其他子格占用的格子停用；正交裁切交點維持整數，面積判斷用 BigInt 避免大座標窄格被浮點誤判為空。
- `#subgridPickCell` 開啟畫布父格選擇；SVG `[data-subgrid-cell]` 以相同四邊值辨識，支援 click、Enter、Space。所有候選矩形與命中範圍均裁至有效面；手機選格時收起右欄，選定後重開並聚焦等分數。父格選單提供完整鍵盤替代路徑。
- `#subgridDivU` / `#subgridDivV` 為 1–65 整數等分數；雙軸 1、越界、小數與不能整除的跨度皆有欄位級 `aria-invalid`／錯誤說明。預設 2 / 2；座標只來自唯讀 `grid-preview subgrid …`，不在瀏覽器重做核心子線推導。
- `#subgridScopeSummary` 顯示父格範圍，`#subgridSpacingSummary` 顯示實際間距與條數；`[data-subgrid-axis] .grid-line-chip` 列出所有座標，點擊只定位，不直接拖動子線。畫布標籤改為聚焦等分數。
- 沿用 `#gridPreviewStatus` / `#gridDraftBadge` / `#gridCreate` / `#gridReset` / `#gridCommand` 的草稿生命週期；`#subgridCancel` 放棄草稿並返回父主格。編輯、重設、切面及非同步回應均核對編輯器身份與預覽序號。
- 子格清單列為 `.face-layer-row[data-grid-kind="subgrid"][data-grid-id]`，`.grid-layer-open` 進入編輯；主格與子格清楚標示父 ID。刪除時列出 `dependencies.children/guides/timbers` 實際引用，仍走核心交易守門。
- 每條 grid JSON `lines[].segments` 是已裁切的真實可見段；保存線、草稿線及 `[data-face-hit="k:id:axis:index"]` 皆逐段繪製。子線與放材預示限父格；孔內不留命中。顯示偏好沿用 `ReferenceVisibility` 的 `grid:id:axis:index`，父子控制互不影響，重開專案重置。
- 子線兩軸由核心預填 `secondary / 3`；`#tbSuggestion` 和 `#gridTimberPopover .subgrid-role-warning` 根據既有角材的實際主支軸顯示衝突。不能以副支放置時保留副支預設並要求明確改選，不自動改成主支；手動覆寫仍由核心驗證。
- `.reference-impact .impact-grids` 逐項列出主／子格父引用、新舊矩形、座標與實際可見段，即使沒有角材亦可確認或取消；原 guide 與 timber 影響仍列出。`[data-impact-grid]` 為逐格測試識別。
- `.subgrid-editor` 所有顯示中的 input、select、button 目標至少 44px，390px 右欄不水平溢出。回歸由 `cdp_test.js` P8v4 實際執行 `app.js`。

## GEO-209／GEO-212 畫布框選與角材多選

- `#ocSelectionSummary` / `#feSelectionSummary` 在選取工具下顯示框選提示與已選數量；`data-count` 為實際數量，`strong[role="status"]` 提供狀態通知。`[data-selection-clear="oc"]` / `[data-selection-clear="fe"]` 清除所屬畫布的選取。
- `.selection-marquee` 是 SVG 選取框，`pointer-events:none`。向右使用完整包含（藍色實線，`data-selection-mode="window"`）；向左使用含邊／角接觸的相交（綠色虛線，另有 `.crossing` 與 `data-selection-mode="crossing"`）。垂直方向不影響規則，水平位移為零沿用完整包含。拖過起點即時更新外觀及 summary `small` 說明；取消／放開指標後移除框並恢復方向提示，不寫入場景或專案。
- `oc.selection` 是 `{kind,id}` 集合；`fe.timberSelection` 是角材 ID 集合。多選時原本的單物件 `oc.sel` / `fe.sel` 為空，單選時維持既有檢視器契約。清單 `.multi-selection-list` 明示選中的物件，`.multi-selection-note` 說明第一版不批次編輯、移動或刪除。
- 左鍵從空白處拖曳框選；Shift 點選增減、Shift 框選加入，Ctrl／Cmd＋A 全選目前範圍。輸入欄位及對話框不攔全選。Space／H／中鍵保留平移。選取框不使用幾何格點吸附；縮放／平移後依實際畫面位置選取，手勢途中鏡頭改變則取消框選並保留原選取，避免混用座標基準。
- 邊與頂點沿用原本單選編輯；面內空白單擊的開口選點亦保留，已有多支角材選取時先清選，單支則維持原本選點流程。3D 預覽與三視圖不加入框選。
- 焦點導航與復原清除多選，但保留同專案且仍有效的單選：進入面須與目標卡一致，焦點空間僅保留其自身單卡，復原後角材由重載結果修剪。跨專案一律清除，不因 ID 相同沿用舊選取。
- 操作與驗收見 `CANVAS-SELECTION.md`；新增真瀏覽器回歸由 `cdp_test.js` P67 呼叫 `marquee_test.js`。

## GEO-210 建立空間的常用流程

- `#smInlineProjection` 提供尚未定義之水平來源的同視窗確認。`#smProjectionView` 明示俯視／仰視，`#smConfirmProjection` 點擊後才保存「空間邊界平面投影、室內淨空、牆外側」定義；一般面不因開啟建模而自動改用途。`#smSetProjection` 保留完整定義及 z 編輯入口。
- inline 確認於讀取前後核對專案身份、面實例 UID、完整場景、歷史 token、來源放置及 frame、原投影定義；關閉、切來源或方向取消等待中的提交。所有等待完成後才同步寫入投影 metadata。
- `#smCommonSettings` 集中高度、材料及角材；`#smBottomZero` 必須明示點擊才填 0。`#smSourceAdvanced` 收合其他建模方式／來源，`#smBoundaryAdvanced` 收合輪廓邊及底頂用途。`#smBoundarySummary` 與 `#smBoundaryWarning` 在進階區外，孔洞用途 `#smHolesWrap` 也保持外露；FREE 不預選，未指定孔用途則聚焦欄位並拒絕預覽。
- `#smCommitReview` 與建立按鈕同在 footer，包含 `#smCommitSummary`、`#smReviewJump`、既有 `#smConfirmFaces`。`#smReviewFaces` 是可展開的完整面清單；修改設定即撤銷舊預覽及核對，建立守門不變。footer 可捲動且保留設定區；窄且短的視窗省略非互動步驟列，操作目標仍至少 44px。
- 單一記憶體草稿只復用同專案、面 UID、放置、frame、投影、完整 dump 及未變歷史的控制值；不復用預覽或確認勾選。場景相同但經 undo/redo 也不可復用，不跨重整或分頁保存，已保存模型／修改牆高不覆蓋新建草稿。
- `#smSaveNotice` 區分加入目前專案、真正寫檔成功與下載待確認；`#smSave` 仍由使用者點擊直接呼叫保存，以維持原生選檔器的使用者手勢。
- `space_model_test.js` 的 GEO-210 分支驗證流程、草稿與延遲回覆；完整建模及角材回歸沿用相同按鈕、API 與核心。操作說明見 `SPACE-MODELING.md`。

## GEO-211 正式工程規格與缺口修补

- `#btnEngineeringSpecs` 與 `[data-engineering-open]` 開啟 `#ewWorkspace`；放置面／主格入口透過 `data-placement-id`／`data-grid-id` 對準本次物件。`#ewTitle` 與版號標示正式工作區身份。
- `.ew-nav [data-ew-section]` 切換套用、材料、做法與工程包；`#ewPreview` 建立核心候選，`#ewReviewed` 核對完整影響，`#ewConfirm` 確認单次交易。`#ewCancelPreview` 保留表單但取消候選。
- `#ewSave` 由原使用者手勢直接呼叫完整專案保存；未發布表單經 ReferenceWorkspace 草稿 API 保存，與原生 World 分開。單純表單輸入不造成核心 undo 步驟。
- 已有來源的網格用 `.engineering-grid-details` 顯示有效值；角材 `#tbSelected` 改由工程入口編輯來源，避免舊表單的刪除／重宣告把來源換成字面量。`references.engineeringSources` 為唯一綁定判準。
- `#guide-editor` 保留 LOCAL 引用式；DATUM 只能從共用基準管理器修改。`.reference-impact [data-impact-guide]` 顯示全部可見段前後端點；忙碌中的 I8a 確認／取消仍允許真指標操作。
- `engineering_workflow_test.js` 與 `project_audit_test.js` 使用正式畫布及 native bridge 驗證；模擬視窗不代替實體觸控驗證。
