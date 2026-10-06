> ⚠ **讀碼地圖,非規格。** 由驗收前的唯讀讀碼產出,只當線索;與實測或正式文件不符時以實測/正式文件為準。

# geometry-web 產品地圖(main d6b4b450,唯讀讀碼,未實測;由產品地圖員產出)

路徑前綴:`W/`=geometry-web/,`公`=公理層.md,`BL`=BACKLOG.md。「無規格」=僅實作行為。此地圖是線索,不是規格;實測與它不符時要記錄。

## 0. 先決條件
- 新啟動服務不是空世界:`W/web_bridge.c:878` 啟動載入 reference_default_world(面1 4000×3000 z=2500、3 支角材、參考線1、具名規格「主支中線」)。要空白專案:檔案選單→「新專案…」`#btnNewProject`(會跳 window.confirm)。
- 世界幾何在服務端 bridge 行程;PDF 底圖、校準等附件在瀏覽器端。
- 「全新瀏覽器環境」:新 profile(sessionStorage `geometry-canvas-recovery-tab-v1`、IndexedDB `geometry-canvas-recovery` 皆空)+ 重啟服務(新 X-Geometry-Session、回預設世界)。只換分頁不重啟服務會看到舊幾何但無底圖。
- 連線完成前 `#app` inert,`#connectionNotice`「正在讀取場景」。
- 不要帶 hash `#space-model-v1`/`#timber-space-v1`(會自動開範例)。

## 1. 匯入 PDF
- 入口:檔案選單 `#fileMenuBtn` →「匯入參考資料… PDF／圖片」`#btnImportReference`(index.html:69);面內左欄 `.reference-entry[data-project-action="import"]`「從 PDF／圖片描面」(:412);面內右欄底圖分頁 `[data-fi-tab="underlay"]` 的 `#refChoosePage`、`#refImport`、`#refMorePages`。DOM-CONTRACT:83 說匯入在「建立」選單,但 index.html:317-340 沒有(文件不一致)。
- 步驟:選檔(隱藏 `#referenceFile`)→ `#referenceDialog` 選頁(`#refPageNumber` `#refPrev` `#refNext` `#refThumbnails` `#refZoom`)→ 可拖取景框 `#refCropOverlay` / `#refResetCrop` → `#refTarget`「建立描繪用面（預設矩形）」或「套用至面 N」→ `#refApply`「加入參考頁」。
- 支援 PDF/PNG/JPEG/WebP/GIF,1B~128MB;加密/損毀 PDF 顯示「無法讀取 PDF；請確認檔案完整且未加密。」
- 方向:PDF 以 getViewport({scale:1}) 含原頁旋轉/CropBox;匯入對話框無旋轉;匯入後 `#refAlignmentDetails` 的 `#ulRot` 0/90/180/270。
- 尺寸:對話框只顯示「/ N 頁」;未找到頁面實體尺寸顯示。
- 底圖:成功後進面內工作區,右欄切底圖分頁,狀態列「已加入參考頁；請用圖上已知尺寸完成兩點校準。」底圖 SVG `#feUnderlay`,不透明度 0.5(`#ulOpacity`)、`#ulLock`、`#ulX`/`#ulY`。初始比例=面外接框寬÷取景寬,不算校準。只在面內工作區顯示。
- 預期:取消/Esc 不新增面;失敗後可重試。
- 實作:reference-workspace.js:605 sourceFromFile、:964 chooseFile、:968 openSource、:998 previewPage、:1044 applySource。規格:docs/REFERENCE-PROJECT.md:7-18、DOM-CONTRACT.md:862-875、BL:3465-3519(GEO-198)。

## 2. 比例尺(兩點校準)
- 入口:面內右欄底圖分頁「校準尺寸」:`#ulCalibStart`「在底圖上選取兩點」或 `#refCalibrateStep`「2 校準」;進行中 `#calibrationCanvasPrompt`、`#cancelCalibration`。
- 步驟:點兩點 → `#ulCalibDist` 實際距離、`#ulCalibUnit` mm/cm → `#ulCalibApply`「套用比例尺」。
- 預期:`#refCalibrationStatus`「已校準 · {值} {單位}」(前為「未校準 · 請使用圖上已知尺寸」);`#refOutlineDetails` 展開、`#refDrawOutline`「選房間／描外環」可用。
- 拒絕:距離須換算為 1~1e8 整數 mm(12.5cm 可、12.55cm 拒)「實際距離須能換算成正整數 mm，且不超過 100 km。」;點須在頁內;兩點相同拒;`#ulLock` 勾選時停用。≤680 寬取點時右欄自動收起。
- 效果:ul.mmPerPx = distMm/兩點像素距,x/y 不變;不縮放既有外環(設計如此);頁面標 reviewRequired;校準隨 .gcanvas 保存;校準不是 undo 步驟。
- 量測:無獨立量尺;用 `#faceCoordinateReadout`(u v mm)、`.fe-edge-dimension` 邊長標註、右欄 `#edgeLength${i}`。
- 實作:app.js:4759/4777/4790、:6799-6890;reference-workspace.js:823。

## 3. 描繪房間輪廓
- 核心限制:正交、4~32 頂點、無零長邊、不自交、±1e8 mm;邊界面上限 16、放置 16、空間 4。
- 矩形(主畫布):`#btnNewRect`/R/`#btnCreateRect`/`#btnQuickRect`,拖曳;無格點吸附(`#snapToggle` 只吸卡片);0 寬高 toast「矩形：請拖出範圍」;建游離面。app.js:9533。
- 多邊形:`#btnNewPoly`/P/`#btnCreatePoly`/`#btnQuickPoly`:建 4000×3000 預設面→進面內→啟用重畫外環工具;面內 `[data-face-tool="redraw"]`/E。
- PDF 半自動:`#refDrawOutline` → `#refRoomPick` 點房內或拖框;`#refRoomMethod`、`#refRoomHorizontal/Vertical`、`#refRoomEdge/Length/SetLength`、`#refRoomVertices`、`#refRoomReviewed`、`#refRoomConfirm`、`#refRoomCancel`。docs/ROOM-OUTLINE.md。
- 描繪(polydraft.js):逐點點擊;吸附 `#faceSnapToggle` 格點(格距依 zoom 10~1000mm)、既有頂點 ±8px 對齊虛線、已校準 PDF 線端點/交點 8px 優先;正交。鍵入長度:數字→`#feLenInput`+方向鍵;Backspace 退點;Enter。
- 閉合:點回起點(≤12px)、Enter、雙擊、`#faceDraftFinish`「完成外環」;末點與起點不同軸自動補直角;`#faceDraftCancel`「放棄草稿」。錯誤碼 CROSS/BACKTRACK/TOO_FEW/TOO_MANY/NO_CORNER。
- L 形:鍵入 `e`、`4000 →`、`1500 ↓`、`2500 ←`、`1500 ↓`、Enter(README:293);或 `#faceShapeButton` 形狀庫 `#shapeDialog`(`#shapeW #shapeD #shapeA #shapeB #shapeSubmit`);或 `#feActionBar` 凹口/外凸/推拉/切角/開口。
- 編輯:拖頂點(鄰邊保持正交)、拖邊、`#edgeLength${i}`、`#edgeFixed${i}`/`#edgeFree${i}`、Alt+拖凸角、右鍵 `#feCtxMenu`、雙擊邊=凹口/雙擊凸角=切角。刪單一頂點:未找到。刪面:主畫布選取 Delete 或 `#inspDelete`。
- 預期:成功 toast「✓ 面 N 已建立 · M 頂點 · W×H mm · Ctrl+Z 復原」;核心拒絕 toast 原文且不改世界;動到被角材引用邊彈 I8a `.reference-impact`/`#impact-confirm`。
- 規格:公 D3、I2、I3、I8/I8a:520-546;DOM-CONTRACT.md:487-560。

## 4. 從輪廓建空間
A. 空間模型(主流程):
- 前置:輪廓面須已放置且水平:屬性分頁 `#placeOX/#placeOY/#placeOZ`、`#placeU/#placeV`、`#placeSubmit`「放置這片面」(app.js:8501-8600)。
- 入口:屬性分頁 `[data-fp-build]`「以此面建立空間」/「依此平面建立空間」→ `#smWorkspace`。
- 步驟:`#smProjectionView` 俯/仰視 + `#smConfirmProjection`;`#smBottom` 牆底必填(`#smBottomZero`);`#smHeight` 預設 3000;`#smThickness` 100、`#smWallsEnabled`;`#smIncludeTimbers`;「調整輪廓邊…」`[data-sm-edge]`、`#smHoles`;`#smPreview`「更新預覽」;勾 `#smConfirmFaces`;`#smCreate`「建立空間」。
- 生成:矩形 4 側+底+頂=6 面;L 形 6 側+底+頂=8 面;`#smVolume`/`#smClearance`/`#smWallVolume`。俯視 +Y 向上;編輯圖局部 u→ v↓(GEO-244)。結果只進空間模型庫(`#btnSpaceModels`、`#spaceModelCount`),不改核心世界;只存在 .gcanvas 的 models。
- 改高:模型庫 `[data-sm-edit-height]`「修改牆高」→ `#smEditHeight` → 預覽 → `#smCreate`(顯示「更新空間」)。
- 規格:公 D21/D22:296-305、D24/D25;3000 預設依 BL:3664-3675(GEO-206)、docs/SPACE-MODELING.md:29,34。
B. 原生空間卡片:`#btnNewSpace`、`#spaceAddMembers`、`#btnBox6`「知道尺寸 → 六面盒」`#box6Dialog`(`#box6W/D/H` 預設 4000/3000/2500、`#box6Floor`、`#box6Submit`)。2500 vs 3000 為刻意差異。公 D5、I4、I15-I17。

## 5. 多房間
- 主畫布可多面多空間(面 16、空間 4);單擊選、雙擊進;`#memberDialog`/`#memberSubmit` 收成員;框選、Shift、Ctrl+A;多選不能批次編輯/刪除。
- 同 PDF 多房(#77):`#roomSourceCreate`「以此底圖連續新增房間」(須已校準)→ `#roomNew`、`[data-room-open]` `[data-room-edit]` `[data-room-rename]` `[data-room-unlink]`;規格為提案(BL ISSUE-77 接線驗證中),公理層無條號。共享來源房間不得用一般「移除底圖」。
- 空間模型庫上限 64。同頁多候選 #87 未做。

## 6. 網格/子網格/參數
- 已上線:無限網格系統 D29 `#btnNewGridSystem`/`#btnQuickGrid`/`#emptyNewGridSystem`,工作區 `#infiniteGridWorkspace`(`#igName` `#igUSource` `#igVSource` `#igSaveSource`);網格配置 D30 `#igNewBinding` `#igCellI` `#igCellJ` `[data-ig-anchor]` `#igSaveBinding` `#igApplyBinding`;相位差 `#igUStagger/#igVStagger`;子網格 D19 面內 `#subgridNew` `#subgridCellChoice`/`#subgridPickCell` `#subgridDivU/#subgridDivV`(1~65);面內有限網格:工具列網格 G → `[data-engineering-grid]`;工程規格 `#btnEngineeringSpecs`;參數卡 D31 `#btnNewParameter`(GEO-223 待人工驗收)。
- 缺口/未完成:來源子網格規則 D19a UI(#61,子線 display/pick、RuleLineRef 未完成,#134 草稿);grid-trial(非正式);組構規則 `#btnNewAssembly` 僅最小角材;舊三視圖 `#btnObj`;公理層 :14 未定案項。

## 7. 取消/返回/撤銷/重做
- 按鈕:`#btnUndo` `#btnRedo`;面內 `#faceUndoButton` `#faceRedoButton`;返回 `#btnBack` `#workspaceBackButton`;`#faceDraftCancel` `#cancelCalibration` `#refRoomCancel` `#refClose`。
- 鍵:Ctrl+Z;Ctrl+Y/Ctrl+Shift+Z(輸入框內不攔截;busy 時 toast「操作進行中,請稍候」)。無全域 Ctrl+S。Esc 階梯(README:270、app.js:1483-1563)。
- 歷史:核心改世界指令=1 步;history-begin/end 群組=1 步;上限 32。本機步驟:空間模型增/改/刪、面投影定義、開專案、新專案、清空。不入歷史:校準、底圖調整、匯入頁。重新整理後歷史消失。開專案可復原。
- 讀碼疑點:undo 較早幾何步時,校準/新頁可能被 ContextHistory.snapshot 的 groups 一併還原(未實測)。

## 8. 保存與開檔
- 保存:`.project-save`「保存」(data-project-action="save");檔案選單 `#btnMenuSaveProject`、`#btnSaveProject`「另存新檔…」→ save()(reference-workspace.js:1163)。Chrome 用 showSaveFilePicker(原生對話框);無 API 則下載 `<專案名>.gcanvas`,狀態「已產生下載 · 請確認檔案」。
- 保存守門 assertSaveReady(:1129):未確認外環草稿/未套用校準/房間候選/房間草稿/參數草稿/忙碌 → 拒絕。
- 內容:ZIP(manifest.json、world.scene、sources/<sha256>):PDF 本體、每面頁(頁碼、crop、x/y/rot/opacity/locked、mmPerPx、校準點/距離/單位)、world.scene(面、放置、空間、柱樑、網格系統/配置、參數、畫布位置)、models、faceProjections、工程草稿、組構草稿、featureAttachments、reconstructionReviews;格式 geometry-canvas/1…/13。不存歷史、未套用草稿、fe.feats。
- 開檔:`#btnOpenProject`「開啟專案… .gcanvas」→ `#projectFile` → openProject(:1226);dirty 時 confirm;驗完整性、重建空間模型、/upload/prepare→/upload/confirm 原子替換;失敗不替換;開檔可復原。`#btnOpen` 只載 .scene。
- 自動恢復:IndexedDB `geometry-canvas-recovery`(600ms 內)、條件同分頁+同服務 session+同 sceneHash;資訊面板 `#projectInfoButton`、`#projectRecoveryRetry`。
- 規格:公 I36:735-739、I39:771-778、I41:788-795、D12:55-58;docs/REFERENCE-PROJECT.md:20-45,90-99。

## 9. 快捷鍵
主畫布 V/H/空白/R/P/F/1、/、Delete、Ctrl+Z/Y、:、Esc;Ctrl/Cmd+A、Shift。面內 V L R H T G E F 1 空白 Enter 數字+方向 Backspace。F8/Shift+F8 回報。

## 10. 窄螢幕(CSS 讀碼,未實測)
斷點 ≤1160/900/680/560/400/360。≤1160 工具鈕文字隱藏(用 id 選)。≤900 左庫抽屜 `#toggleLeft`、`#toggleRight` 隱藏、`#mobileCreateObject`「建立」。≤680「保存」只剩圖示、小地圖隱藏、檢視器變底部面板、頂列兩列。面內 ≤680 左右欄為抽屜 `#workspaceToggleLeft/#workspaceToggleRight`;取點時右欄自動收。`#smWorkspace` ≤720 用 `#smTabPreview/#smTabSetup`、`#smMobileNext`。

## 11. 文件衝突
README:300-305(GEO-190 底圖不入檔)vs DOM-CONTRACT:585(GEO-198 可存);DOM-CONTRACT:83 vs index.html;REFERENCE-PROJECT:23 只到 /9;公理層:12 說 D20–D25 未實作 vs BL GEO-130/205。

## 最不確定
1. 校準/底圖與 Ctrl+Z 互動。2. 全新瀏覽器環境判準。3. 窄螢幕隱藏項與 #77 實際可用範圍。
