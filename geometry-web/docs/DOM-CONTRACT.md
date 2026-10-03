# DOM 合約(測試依賴清單)

## 參數確認期間輸入保全（GEO-233）

`#parameterEditor[aria-busy="true"]` 代表正式確認尚未完成；其 input/select/textarea/button 同步 disabled，不能先接受新輸入再被舊回覆清掉。成功或原生拒絕後恢復這次捕捉的控制，拒絕時 `#paramConfirm` 仍停用、草稿保留，編輯後可重新試算。`parameter_confirmation_test.js` 由完整 P76 呼叫，以真鍵盤、延遲成功回覆與真過期 token 驗證六項。

## 原生角材料單（#47 F4a）

`#faceLayerList` 的既有 `[data-timber-id]` 列直接提供料單，不另建清單工作區。
`[data-schedule-timber]` 是可鍵盤操作的定位按鈕，`aria-pressed` 與畫布角材選取同步。
`#timberScheduleScope` 明選承載面全部或當次選取的 ID 集合；`#timberScheduleUnit` 只格式化 mm/cm；
`#timberScheduleOrder` 按身分或完成長度排序。`#timberScheduleCSV` 導出同一集合的精確 mm，
`#timberScheduleStatus` 顯示正式件數／失效原因。來源細節在 `.timber-schedule-source` 展開。
數據契約與剩餘追溯限制見 [TIMBER-SCHEDULE.md](TIMBER-SCHEDULE.md)。

## 2026-10-03 Issue #54 房間輪廓候選

- 保留 `#refDrawOutline` 原步驟，在既有底圖 pane 啟動房間選點／框選；`#refOutlineDetails` 集中候選、人工修正與來源核對，移除重複 `.reference-intro`／`.calibration-instruction`。
- `#refRoomMethod` 選向量優先／本地影像／人工描繪；`#refRoomMinWidth`、`#refRoomMinLength` 使用固定來源單位，`#refRoomPick` 啟動選房間。未校準停用。
- `#refRoomHorizontal`／`#refRoomVertical` 與 `#refRoomClearBarriers` 是展開後的搜尋分隔控制，不寫正式牆。`#refRoomStatus` 明示取得失敗與過期。
- `#roomCandidateOverlay` 疊在既有 `#feDraftLayer`；點仍是 `fe.draft.pts`。`#refRoomEdge`／`#refRoomLength`／`#refRoomSetLength` 核對入值，`#refRoomVertices`／`#refRoomApplyVertices` 局部補點，`#refRoomReviewed` 每次修正後清除。
- `#refRoomConfirm`／`#refRoomCancel` 與既有 `#faceDraftFinish`／`#faceDraftCancel` 操作同一草稿。確認走核心 `emitBoundary`，依賴沿用 `.reference-impact`；取消／拒絕保留原面。H／空白鍵平移不清候選。
- `[data-reconstruction-state]` 依實際來源頁、校準／變換、核心輪廓顯示 `unreviewed|candidate|confirmed|recheck`。`#refConfirmChecked` 在此區記錄人工流程核對；任意頂點不算完成。
- `window.RoomOutlineWorkspace` 接合狀態與生命週期；`room_outline_test.js` 由完整 `cdp_test.js` 呼叫 P79，`GEOMETRY_ROOM_OUTLINE_ONLY=1` 僅是部分驗證。

> 立案 2026-09-13(Phase 0 產出);Phase 1 改版更新。本檔列出自動測試依賴的 DOM id / class / 全域名稱;
> 之後每階段改 DOM 都要對照本表,新增或改名需同步更新測試。

## 2026-09-29 GEO-218 第二輪介面與專案生命週期

- `#projectBar` 是同一個 DOM 節點，內含專案名稱、`#projectInfoButton`、狀態及 `[data-project-action="save"]`。主畫布、面工作區及大型模態視窗共用；`WorkspaceShell` 將它移入 `.workspace-project-header`，關閉後還原。`#ewSave`、`#igSaveProject`、`#smSave` 已移除。保留原生 `showModal()` 隔離背景。
- `#projectInfoPanel` 使用原生 popover；`#projectInfoDetails` 顯示可信來源、保存／下載與復原資訊。`#projectRecoveryRetry` 只在唯讀恢復狀態顯示；關閉原編輯分頁後，可重新競取編輯權限並刷新視圖。
- `ReferenceWorkspace.getProjectInfo()`、`restoreSession()`、`retryRecovery()`、`persistSession()`、`assertEditable()` 管理來源與恢復；詳見 `REFERENCE-PROJECT.md` GEO-218。`connection.session` 須先握手確認；唯讀讀取不寫入自動畫布位置。
- `#fileMenuPop [data-file-section]` 分 project、transfer、resources；`#exampleMenuBtn` 展開 `#exampleMenuPop`。`#btnNewProject` 建新身份，`#btnClear` 清空完整內容但保留身份。建立選單只放建立功能，`#btnSpaceModels` 位於 `.project-library-entry`，亦可由 `#btnModelLibraryMenu` 進入。
- `canvas-labels.css` 對畫布 SVG text 使用白色描邊與固定螢幕粗細；`.fe-edge-dimension` 的延伸線、尺寸線及端點刻度依真實邊生成。三視圖 `data-label-full`、title 及標註清單保留完整面代號，常態文字只顯示角材編號。
- `WorkspaceGuidance.apply()` 只保存工具教學的已讀偏好；`[data-guidance-dismiss]` 關閉，工具列的 `.guidance-help` 重新開啟。即時選取／定位不因關閉教學消失。原生按鈕及 summary 的 Enter／Space 不可誤提交外環草稿。
- 面內即時選取摘要是浮動覆層：顯示／隱藏本身不能觸發自動適配或取消框選；尺寸觀察器只監看畫布容器及底部控制列。明確按全圖時仍避讓當下提示，真正容器縮放仍重新適配。
- `#faceTechnicalDetails`、`#mainFaceTechnicalDetails` 收合面編號、原點與軸向；`#tbTechnicalDetails`、`#tbNewSegmentDetails` 收合精確選段及代碼，首層保留中文角色與常用尺寸。
- `ux_refinement_test.js` 由正式 CDP harness P74 執行；涵蓋桌面／390px、保存守門、真實重新整理及同瀏覽器雙分頁。

## 2026-09-29 GEO-219 介面減重（面工具列入口與單選覆層）

- 面工作區工具列的 `#btnFaceProjection`／`#btnFaceSpaceModel` **已移除**；對應能力集中在屬性欄：`[data-fp-edit]` 開啟投影定義，`[data-fp-build]` 建立空間。面內工作區對**已放置的面一律提供 `[data-fp-build]`**——未定義的水平面由建模視窗內的 `#smInlineProjection`/`#smProjectionCallout` 接手確認，非水平面可於視窗內切 `#smMode` 組合面模式；主畫布檢視器的 `[data-fp-build]` 仍限已定義且水平的放置。`SpaceModelWorkspace.openCurrentFace(placementId)` 介面不變。
- `#ocSelectionSummary` 恢復 GEO-216 契約：0／1 選取時視覺隱藏，僅多選或框選中顯示；`data-count` 與 `aria-live` 節點保留於 DOM。`[data-guidance-dynamic]` 顯示規則明確排除 `data-count="1"`；「工具說明」（`.guidance-help`）的明確重開不受此限。`#feSelectionSummary` 不變。
- `space_model_test.js` 的建模／投影入口全部改走屬性欄真實點擊（`facePropEntry` helper）；390px 下先開右側抽屜。

## 2026-09-28 Canvas 審查修正（面工作區及保存回饋）

本節取代舊節的一列面工作區頂列、隱藏窄螢幕保存狀態及復原按鈕位置要求。其餘幾何／預覽守門維持原契約；驗收範圍見 `UIUX-FIXES-2026-09-28.md`。

- `.workspace-tools-row` 是面／空間頂列第二列，包含既有工具與 `.workspace-history-tools` 的復原／重做／全圖；原 ID 不變。第一列是返回、物件名稱、放置摘要、抽屜與檔案／保存操作。第二列可水平捲動，焦點控制保持可達。
- `#objectWorkspace:not([hidden])` 使根節點與 body 同步頂列高度；桌面為 116px，手機斷點為 122px。`--topbar-h` 同步畫布、抽屜、提示的位置。主物件畫布維持自己的響應式頂列，不能將工作區高度套到主畫布。
- `[data-project-status]` 保留完整狀態文字、`title` 與可及名稱；`data-status-short` 供窄螢幕顯示「未保存／已保存／讀取中／驗證中」等短字。檔案入口保留文字。
- 開啟專案及試用工程期間，`#busyIndicator` 立即顯示真實讀取／驗證／載入階段，`ReferenceWorkspace.busy` 阻擋 UI 及重複開啟。`ReferenceWorkspace.historyActionLabel('undo'|'redo')` 提供待復原的專案開啟操作名稱。
- 面視野由 `ResizeObserver` 跟隨畫布容器尺寸：全圖模式重新適配，手動視角保留倍率與中心。三視圖切換重新同步 `#ocSelectionSummary`，三視圖不顯示框選提示。
- `#v3LabelDetails` 位於左側 `#v3Panel`，未選物件時亦可展開全部標註；窄螢幕由左側抽屜開啟與捲讀。圖上收合的密集標註仍保留於清單。
- 零成員空間的 `.space-plan-empty` 顯示空容器說明及加入成員入口，不渲染有尺寸的房間矩形。
- 無限網格的 `#igSaveSource`／`#igSaveBinding` 保留原 ID 並固定於 footer；保存專案與預覽建立是分開的動作，有未套用草稿時不允許以保存專案關窗丟棄內容。
- `#box6HeightNote` 說明整盒高度與空間建模牆高預設的差別；既有 2500／3000 值不變。

P73 `uiux_review_test.js` 透過 `cdp_test.js` 驗證本節，也可用 `GEOMETRY_UIUX_FIX_ONLY=1` 單跑；仍須使用明確隔離的服務及 TEMP 回報資料夾。

## 2026-09-28 來源／配置組合畫布（目前主畫布合約）

本節實作使用者選定的第 3 張介面：左側物件清單、主畫布組合關係、底部就地編輯。主畫布的 DOM 位置與操作入口以本節為準，優先於下方 2026-09-27 及更早的佈局紀錄；面內、空間與三視圖工作區仍各遵循原有契約。D29／D30 的物件語意、預覽確認與保存格式未變。

| id / class | 契約 |
|---|---|
| `body.canvas-composition` | 僅主物件畫布啟用；進入面／空間或三視圖即移除，不改其他工作區的欄位佈局 |
| `body.canvas-has-inspector` / `body.canvas-grid-inspector` | 前者在主畫布有選取或建立草稿時展開底部檢視器；後者限單選無限網格來源或網格配置，套用就地網格編輯版面 |
| `#btnCreateObject` / `#mobileCreateObject` / `#createObjectPop` | 桌面物件庫與窄螢幕「建立」共用同一選單，`aria-expanded` 對應開啟狀態；原空間、柱、樑、六面盒、匯入與空間建模入口保留原識別，收在此選單 |
| `#createObjectPop` / `#quickBoundaryPop` 鍵盤操作 | trigger 的原生 Enter／Space 開啟並聚焦首個可用項目，ArrowDown／ArrowUp 開啟並聚焦首／末項；選單內 ArrowDown／ArrowUp 循環、Home／End 到首／末項。Escape 關閉選單、焦點回 trigger，保留手機物件庫抽屜的開啟狀態 |
| `#btnNewGridSystem` / `#emptyNewGridSystem` | 常駐物件庫入口與空畫布入口都建立無限來源，開啟 `#infiniteGridWorkspace`；不是舊有限編輯器的建立入口 |
| `#btnQuickBoundary` / `#quickBoundaryPop` / `#btnQuickRect` / `#btnQuickPoly` | 「邊界」快捷入口明選矩形或多邊形，沿用既有建面操作；建立選單中的 `#btnCreateRect`／`#btnCreatePoly` 也走相同操作 |
| `#canvasDrawToolbar` | 選取、平移、`#btnNewRect` 與 `#btnNewPoly` 浮於畫布，保留原工具識別與快捷鍵；不再位於主頂列 |
| `#ocSelectionSummary` | 主畫布通常為 0／1 選取時視覺隱藏，僅多選或正在框選時顯示；保留 DOM 的實際 `data-count` 與 `aria-live` 狀態節點 |
| `#btnCollapseLibrary` / `body.canvas-library-collapsed` | 桌面收合／展開左側物件庫並更新 `aria-expanded`；窄螢幕關閉左抽屜 |
| `#filterDisclosure` | 物件庫底部的原生 `details`，內含 `[data-filter-group]` 與 `#filterAll`；收合篩選選單不改目前篩選值 |
| `.object-group[data-object-group]` | `sources` 為來源（面、網格系統、參數、組構規則），`bindings` 為配置（網格配置、材料配置），`structures` 為空間與構件；空組不顯示。組內保留 `.object-row[data-kind][data-id]`、選取及鍵盤操作 |
| `.grid-relation[data-binding-id][data-source-kind][data-source-id]` | 從來源卡連到配置卡；`data-source-kind` 為 `grid-system` 或 `boundary`，曲線為子節點 `path.grid-relation-path`。只有兩端卡片皆顯示時才繪製，拖移卡片會更新連線 |
| `.grid-relation-label[data-binding-id][data-source-kind][data-source-id]` | 與對應曲線使用同一組身分，分別標「使用此網格」／「使用此邊界」。選取任一端時連線與標籤 `.active`；關係顯示不攔截畫布操作、不新增模型引用 |
| `.ocard[data-kind="grid-system"] .ocard-body` | 無限來源縮圖每軸最多繪製 64 條線，以縮圖座標 8px 為最小取樣間距；僅控制顯示密度，不改幾何、格距或無限索引 |
| `#gridInlineInspector[data-gi-kind]` | 底部就地編輯根節點，值為 `source` 或 `binding`；切換專案、物件或工作區時清除失效編輯上下文 |
| `#giName` / `#giUStep` / `#giVStep` | 無限來源的名稱與 `repeat` 間距；只有對應軸為 `repeat` 才有間距欄位。基準、主支方向及 `repeat-panel`／`none` 排法在完整工作區修改，底部預覽保留其既有值 |
| `#giSystem` / `#giBoundary` / `#giVertex` | 配置選擇無限來源、獨立邊界與實際頂點；缺少任一軸的來源不可用於 cell 配置。更換邊界須重新選點，不按陣列位置猜測既有頂點身分 |
| `#giBoundaryView [data-gi-vertex]` | 真實外環／孔環縮圖上的頂點，值為 `outer:N` 或 `hole:H:N`；與 `#giVertex` 同步，`data-vertex-key` 保留已有穩定身分，支援點擊及 Enter／Space |
| `#giAnchorView [data-gi-anchor]` | cell 內九個對齊位置；屬性使用半格單位 `0,0` 至 `2,2`，`1,1` 代表中心 `(1/2,1/2)`。`aria-pressed` 表示選取；未更動時保留已有精確比例 |
| `#giCellI` / `#giCellJ` | `type="text"` 的正負整數索引，使用 BigInt 驗證及傳輸十進位字串，不經 Number 截斷 |
| `#giPreview` / `#giStatus` | 「預覽變更」先取得核心完整候選，再由 `.reference-impact`／`#impact-confirm` 確認；輸入草稿、取消或失效回應不直接修改世界。狀態使用 `role="status"` |
| `#gridObjectOpen` / `#gridObjectNewBinding` / `#gridObjectDelete` | 開啟同一個完整網格工作區、從所選來源建立配置、刪除所選物件。建立配置只在無限雙軸來源且沒有未保存的底部來源草稿時可用；刪除仍受原生依賴守門 |

`grid-inspector.js` 擴充既有 `InfiniteGridWorkspace.renderInspector/disposeInspector`，不另存一份來源或配置。來源／邊界／專案已變更、選取被切換或較舊的讀取回應返回時，不能提交舊草稿。來源與配置卡片的畫布位置仍只是顯示資料；移動卡片不改幾何對齊。

回歸入口為 `cdp_test.js` P72 的 `composition_canvas_test.js`，可用 `GEOMETRY_COMPOSITION_ONLY=1` 單跑，也納入完整 CDP。它以實際指標／鍵盤操作檢查入口、分組、連線、就地編輯與窄螢幕；此處列測試契約，通過狀態以實際執行紀錄為準。

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

- `#btnSpaceModelTrial` 開矩形範例，`#btnSpaceModels`／`#spaceModelCount` 開模型庫；它們位於獨立 `.space-model-entry`，原 `.start-options` 仍保留兩個入口。面內「使用目前面」的入口自 GEO-219 起由屬性欄 `[data-fp-build]` 提供，原 `#btnFaceSpaceModel` 工具列鈕已移除。
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

## 2026-09-27 UI/UX 審查更新（主畫布佈局已由 2026-09-28 節更新）

以下保留當日決策；主畫布入口、工具列、物件清單與檢視器位置若與上方 2026-09-28 節不同，以新節為準。

- 主頂列 `.tool-group` 顯示選取／平移與 `#btnNewRect`／`#btnNewPoly` 四種工具；左欄 `.start-options` 是描面、六面盒兩張起點卡，`.quick-create-grid` 只有 `#btnNewSpace`、`#btnNewColumn`、`#btnNewBeam` 一列。`#sceneList` 位於 `#fileMenuPop` 內，主頂列顯示 `[data-project-name]`／`[data-project-status]`。保存控制 `[data-project-action="save"]` 會在進出工作區時移動同一個 DOM 節點，工作區掛點為 `#workspaceProjectActions`；`#btnSaveProject` 是「另存新檔」選單入口。
- `#objectWorkspace` 只有 `.object-workspace-topbar` 和 `.object-workspace-statusbar`；已移除 `.workspace-project-bar`／`.workspace-file-menu`。工作區頂列借用主頂列的 `#fileMenu`，Esc 關閉 `#fileMenuPop` 而不離開工作區。`#shapeToolButton` 開啟 `#shapeToolPop [data-shape-action]`；選操作後以 `fe.queuedShapeAction` 等待邊／角，開口轉入既有開口工具。外環邊的浮動列和右鍵選單含 `[data-fe-act="timber"]`，沿選邊預填並放置角材。
- `#faceInspectorTabs [data-fi-tab]` 順序是 `prop,shape,components,underlay`，右欄對應 `[data-fi-pane]`。原 `guide,timber,grid` 仍可傳給 `fiShowTab()`，會打開構件頁並捲到 `[data-component-section]`。形狀庫 `#faceShapeButton` 由程式移入形狀頁；角材表單 `#tbPlace` 直接提交同一筆宣告與放置交易。`#faceReferenceSummary` 顯示來源，`[data-reference-step]` 表示選頁／校準／描外環。未放置面標示「未放置」。
- 空間左欄 `#spaceAddMembers` 在成員面標題旁；`#spaceSizeTools` 依平面圖放柱／樑工具移到頂列，三視圖不顯示放置工具。三視圖矩形工具使用 `#v3PlaneControls`、`#v3ToolbarSurf`、`#v3ExistingZ`、`#newZ` 顯示並修改工作面與高度。
- 審查項目與驗收流程見 `UIUX-REVIEW-2026-09-27.md`；下列舊節保留各階段的歷史決策。除 2026-09-28 更新的主畫布範圍外，若其 DOM 位置或頁數不同，以本節為準。
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
| `#objectCountBadge` / `#sourceCount` / `#bindingCount` / `#structureCount` | 數量徽標。三個組合計不隨搜尋縮小：來源＝面＋網格系統＋參數＋組構規則，配置＝網格配置＋材料配置，空間與構件＝空間＋柱＋樑 | textContent |
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
| `[data-filter-group]` | 顯示組篩選 chips(button,`aria-pressed`)：`sources` 來源、`bindings` 配置、`structures` 空間與構件 | `aria-pressed`、`.click()` |
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
| `[data-filter-group]` | 顯示組篩選(sources/bindings/structures) | `aria-pressed` |
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
| `oc` | 物件畫布狀態物件 | `oc.on`、`oc.faces`、`oc.spaces`、`oc.focus`、`oc.sel`、`oc.tool`、`oc.panX/panY/zoom`、`oc.drawTool`、`oc.rect/card/pan`、`oc.groupOn`（sources/bindings/structures）、`oc.search`、`oc.surfs`、`oc.busy`、`oc.mmTf` |
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
- 柱與樑納入物件庫。篩選已於 GEO-228 收成 `[data-filter-group="structures"]`，數量併入 `#structureCount`。
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

- `#ocSelectionSummary` / `#feSelectionSummary` 在選取工具下提供框選提示與已選數量；主畫布的視覺顯示條件依上方 2026-09-28 節。`data-count` 為實際數量，`strong[role="status"]` 提供狀態通知。`[data-selection-clear="oc"]` / `[data-selection-clear="fe"]` 清除所屬畫布的選取。
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
- `#smSaveNotice` 區分加入目前專案、真正寫檔成功與下載待確認；GEO-218 統一使用 `#projectBar [data-project-action="save"]`，使用者點擊直接呼叫保存以維持原生選檔器手勢。
- `space_model_test.js` 的 GEO-210 分支驗證流程、草稿與延遲回覆；完整建模及角材回歸沿用相同按鈕、API 與核心。操作說明見 `SPACE-MODELING.md`。

## GEO-211 正式工程規格與缺口修补

- `#btnEngineeringSpecs` 與 `[data-engineering-open]` 開啟 `#ewWorkspace`；放置面／主格入口透過 `data-placement-id`／`data-grid-id` 對準本次物件。`#ewTitle` 與版號標示正式工作區身份。
- `.ew-nav [data-ew-section]` 切換套用、材料、做法與工程包；`#ewPreview` 建立核心候選，`#ewReviewed` 核對完整影響，`#ewConfirm` 確認单次交易。`#ewCancelPreview` 保留表單但取消候選。
- GEO-218 統一由 `#projectBar [data-project-action="save"]` 的原使用者手勢直接呼叫完整專案保存；未發布表單經 ReferenceWorkspace 草稿 API 保存，與原生 World 分開。單純表單輸入不造成核心 undo 步驟。
- 已有來源的網格用 `.engineering-grid-details` 顯示有效值；角材 `#tbSelected` 改由工程入口編輯來源，避免舊表單的刪除／重宣告把來源換成字面量。`references.engineeringSources` 為唯一綁定判準。
- `#guide-editor` 保留 LOCAL 引用式；DATUM 只能從共用基準管理器修改。`.reference-impact [data-impact-guide]` 顯示全部可見段前後端點；忙碌中的 I8a 確認／取消仍允許真指標操作。
- `engineering_workflow_test.js` 與 `project_audit_test.js` 使用正式畫布及 native bridge 驗證；模擬視窗不代替實體觸控驗證。

## GEO-213 普通網格入口直接選材

- `[data-engineering-grid]` 出現在網格表單頂端及每軸「面材＋縫」內，携帶 `data-placement-id` 與已有網格的 `data-grid-id`。`GridEditor.engineeringContext()` 僅提供目前有效編輯面的原始縫寬、起點與主支方向；拒絕失效或錯面上下文。
- 入口使用同一個 `#ewWorkspace[data-mode="grid"]`，`#ewTitle` 為材料規格排格；不復用一般批次工作區的選面清單。`#ewField-gridFlow-route` 選既有面材、新面材或既有做法；其他設定沿用 `#ewField-gridFlow-…`。
- `[data-ew-grid-origin]` 明選面下界；`[data-ew-grid-method-defaults]` 明選做法設定。既有網格主支方向唯讀，包含 `none`；新網格須明選方向。未填縫寬及起點不暗中補值。
- 沿用 `#ewPreview`、`#ewReviewed`、`#ewConfirm` 與 `#ewCancelPreview`，整包候選包含必要的材料／做法發布、面套用及同 ID 網格綁定，不加入角材綁定。關閉、失效上下文或過期候選不得提交。
- `grid_material_entry_test.js` 從真實工具列及選材按鈕測試，由 `engineering_workflow_test.js` 納入完整 P69；原本僅填數字的格線測試不能代替此材料流程。

## GEO-215 無限網格與配置

- `#infiniteGridWorkspace` 為完整編輯工作區；建立新來源或配置時使用它，主畫布已選物件的常用修改另見上方 2026-09-28 就地編輯契約。`#igGridView` 可平移、縮放與拾取 cell；攝影機不寫入模型。`#igDensity` 明示抽樣。
- `#igName`、`#igMainAlong`（GEO-222 起為 `role=radiogroup` 的分段選擇，內含 `input[name=igMainAlong][value=none|u|v]`，元素本身仍可讀寫 `.value`）與 `#igUSource`／`#igVSource` 定義來源；`#igSaveSource` 預覽後確認。只新增 repeat／repeat-panel／none，沒有條數。
- GEO-229：`#igUStagger`／`#igVStagger` 是「相鄰格子相位差 mm」。空白或 0 不寫入 stagger。非零時工作區把該軸畫成停在另一軸格子邊界的段，段帶 `data-ig-segment-band`。底部檢查器不加輸入欄；非零時既有「第 0 線座標」那一行帶出數字。不新增工作區或常駐說明。有相位差的主格上 `#subgridNew` 停用。
- `#igNewBinding` 選邊界建立配置。`#igBoundaryView` 與 `#igVertex` 選實際外環或孔環頂點；`#igCellI`／`#igCellJ` 使用十進位字串及 BigInt，`[data-ig-anchor]` 選 cell 內九宮位置。`#igSaveBinding` 保存明確引用。
- `#igResultView` 只繪核心 query 回傳的裁切線段。`#igApplyBinding` 明確套用到同邊界承載面；未套用配置不暗建面。
- `#igKeyedVertices`、四側 `#igGrowLeft/Right/Top/Bottom` 和 `#igSaveBoundary` 保留穩定頂點身分，預覽確認後提交。
- `grid-binding` 為獨立物件種類；卡片、選取、清單、位置、刪除與保存均使用其獨立 ID。`#gridBindingOpen` 從面內開啟配置。
- 面內 `gridLineEntries()` 將抽樣位置轉為真正的 signed 索引；命中區、角材選項、隱藏偏好均沿用此索引。子線仍為 ordinal。`feRefreshLatticeViewport()` 隨平移／縮放查詢目前範圍，`#feLatticeDensity` 明示稀疏顯示；過期回應核對專案、面、網格實例與範圍後捨棄。未抽到的合法線仍由 lattice 定義精確求值，點選新出現的格線會先補入角材選項。
- lattice 子格使用 `[data-subgrid-cell="lattice:i:j"]` 真 cell；`#subgridCellI`／`#subgridCellJ`／`#subgridUseLatticeCell` 可直接指定密集格的索引。不以外接框或抽樣間距假造 cell。
- `grid_system_test.js` 和 `infinite_grid_face_test.js` 由正式 CDP harness 執行，包含實際 SVG 拾取、signed 引用、保存重開及窄螢幕。
- GEO-221：`#igGridView` 的 viewBox 等於元素實際像素，u、v 共用比例。`data-ig-camera="u0 v0 u1 v1"` 是目前（已貼合繪圖區）的模型矩形（mm，相對局部索引基準）；`[data-ig-plot]` 是繪圖區矩形，點擊只在其內選 cell。`[data-ig-ruler="u|v"][data-ig-ruler-index]` 為尺規索引（純數字、置中於格線），`[data-ig-origin]`／`[data-ig-origin-label]` 為基準點，`#igZoom` 顯示「1 格 U×V mm · N px」。
- GEO-222：版面為單列 56px 標題（`.ig-header` 的 `#igClose`＋麵包屑 `.ig-crumb`，與共用 `#projectBar` 同列）、左側 `.ig-main`（`.ig-canvas` 內含 `#igGridView`、`#igViewNote` 浮動提示、`.ig-zoombar` 內的 `#igZoomOut`／`#igZoom`／`#igZoomIn`／`#igFit`）、右側 `.ig-inspector`（`.ig-settings` 捲動區＋底部 `.ig-footer`，`#igSaveSource`／`#igSaveBinding`／`#igStatus`／`#igDraftNote` 在 footer）。`#igCellPreview` 為格子縮圖；`#igInfo`（`#igInfoTitle`、`#igInfoCell`、`#igInfoRows`）顯示游標與已選取格。SVG 內 `[data-ig-hover="i,j"]`、`[data-ig-selected="i,j"]`（僅來源模式）與 `[data-ig-band=u|v]`（尺規高亮）。`#igDensity` 只在稀疏或大索引時顯示。麵包屑的專案名稱為 `.ig-crumb-project[data-project-name]`（390px 時為標題上方小字）；`[data-ig-origin-label]` 在第 0 線不在 0 mm 時附上 mm 位置。軸線查詢請用 `fieldset[data-ig-axis]`，`line[data-ig-axis]` 也帶同名屬性。
- GEO-227：`#paramGridLesson` 是「參數套到網格間距」的同一張圖。無限網格來源表單開啟時，它以靜態排版放進 `#igSourceForm` 裡、`#igName` 之後的 `#paramGridLessonSlot`，不蓋 `#igGridView`。`#paramGridLessonFrame1`／`#paramGridLessonFrame2` 切換兩張；`#paramGridLessonClose`（知道了）把目前這組事實寫進 `localStorage` 鍵 `geometry-param-grid-lesson`（值是事實 token）。舊鍵 `geometry-param-grid-lesson-v1` 的 `'1'` 只對應最初那組事實。之後只留 `#paramGridLessonOpen`（圖解）。配置模式隱藏 `#igSourceForm` 時不顯示。

## GEO-223 畫布參數卡

- `#btnNewParameter` 加入建立選單；卡片為 `.parameter-card[data-kind=parameter][data-id]`，沿用選取、移動、搜尋、框選和小地圖。只對目前選取卡片／物件畫引用連線；幾何使用處連到所屬面。
- 共用編輯器 `#parameterEditor` 位於既有檢視器；`#paramName`、`#paramQuick`／`#paramParse` 及 `[data-param-field]` 支援自訂欄位、種類、算式、排序與移除。插入引用含固定身分的可讀 token；前端只格式化核心值。（`#paramTemplate`、`[data-insert]` 已於 GEO-224 移除，見下節。）
- `#paramPreview`／`#paramResult`／`#paramConfirm` 使用原生候選交易；`#paramDiscard` 明確還原草稿。回應核對草稿序號及專案 context；dirty 草稿阻擋保存與離開。所有參數表單控制最小 44px。composition 版面下沒有右側抽屜：≤900px（含 390px）沿用畫布下方的檢視器面板（GEO-224 起 >900px 參數編輯時改為畫布右側固定欄）。
- 尺寸控制的 `…Source` 下拉與 `[data-param-jump-for]` 共用「直接輸入／引用來源」。無限來源的 phase、step、panel、gap、anchor 均保留 ParameterRef；工程物件來源模式 `parameter` 分別綁定每一欄。`[data-ew-parameter]` 從既有綁定跳至來源卡。
- `#paramExport` 與 `#parameterSelectionExport` 匯出所選及完整引用卡；`#paramImport`／`#paramFile` 先預覽整包新增，確認才提交。同名保持獨立。
- UI 減項：面內 `#refSpecName`／`#refSpecValue`／`#refSpecSave` 獨立表單移除；`#refParameterOpen` 進共用入口，`#paramSpec`／`#paramSpecValue`／`#paramSpecSave` 編輯既有 spec 原物件。參數編輯器僅一塊常駐操作說明，試算狀態及使用關係按需呈現。
- 位置引用參數（共用基準與參考線）：共用空間基準管理器的 `#datum-parameter` 下拉選尺寸欄位，寫入 `#datum-expression` 的 `param:卡:欄`；面內參考線建立表單在選到參數來源時，於 `#refGuideParameterLinks` 掛 `[data-reference-parameter="卡ID"]` 按鈕（基準列 `#datum-list` 與參考線編輯器 `#guide-editor-source` 同樣掛此按鈕），點擊經 `ParameterUI.jump` 跳回參數卡。即使沒有下游構件，綁定仍先走 `.reference-impact` 預覽（`#impact-confirm`／取消鈕）；基準的前後值列在 `.impact-datums` 的 `[data-impact-datum="基準ID"]`，參考線一律在 `<code>` 顯示 preview.command，`.impact-guides` 的 `[data-impact-guide]` 列僅在核心 preview.guides 有前後差異時出現，測試不依賴該列。
- `parameter_workflow_test.js` 經完整 `cdp_test.js` 執行，含尺寸組、跨卡算式、真網格引用、連動／復原、/6 保存重開、手機、過期回應、獨立參數包匯入，以及共用基準與參考線的參數綁定（先預覽、取消保持原狀、確認保留來源、跳回參數卡）。

## GEO-224 參數編輯面板重做

設計稿存於 `docs/uiux-review/建議-建立參數 4a.dc.html`；使用者定案 `決策佇列.md` Q25。純前端：核心、橋接器、`PARAMETERS-CONTRACT.md` 與專案檔案格式不變，前端仍不做算式求值。

- **版面**：參數編輯（建立新卡或編輯既有卡）時 `body` 加 `parameter-editing`（僅在 `canvas-composition` 且 `#inspectorContent` 內有 `#parameterEditor[data-editor="card"]` 時；離開編輯即移除）。視窗 >900px 且有此 class：`.sidebar-right` 變畫布右側固定欄，寬 `clamp(380px, 30vw, 480px)`、高度佔滿畫布列、內部捲動，畫布取其餘寬度。其他檢視器（面、網格、參考線…）沿用畫布下方面板，語意不變。≤900px 不做右側欄，沿用畫布下方面板；只在 `body.parameter-editing` 時把它的高度上限放寬為 `min(62dvh, 560px)`（兩個斷點都套，其他檢視器維持原本的 280px／680px 以下 min(310px,40dvh)），欄位區才看得到兩三欄。剛進入參數編輯（畫布因右側欄變窄）時，選中的卡會被平移到可視區內（`keepSelectedCardVisible`），離開編輯不平移回去。
- **面板結構**（`#parameterEditor.parameter-editor[data-editor="card"]`，由上而下）：標頭（`.param-title`、`.param-badge` 狀態徽章：草稿 · 未套用／已套用／有未套用修改、`#paramName`）；只在建立新卡：`[data-param-template="single|panel|section"]` 三顆範本鈕（`aria-pressed`）與 `#paramQuick`／`#paramParse`（文字「建立欄位」，內容可解析才 enabled；Enter 等同按鈕）、`#paramQuickHint` 即時預告；`#paramFields`（每欄一列 `[data-param-field="欄ID"]`，不再是 fieldset）含 `input[data-name]`、`select[data-type]`（三個值 dimension／count／ratio）、`[data-result]`（`data-state="ok|pending|error"`）、`input[data-input]`；`#paramAdd`（滿 16 欄 disabled）與 `[data-field-count]`；`.param-help` 說明；`#paramResult`；`details#paramUsage`（只在編輯既有卡；內含 `[data-param-use]`、`#paramExport`、`#paramDelete`）；`details#paramExchange`（`#paramImport`、`#paramFile`、`#paramLegacy`）；`.param-footer` 固定頁尾（`position: sticky`）含 `#paramStatus`（`role="status"`，`data-tone="ok|wait|error"`）、`#paramDiscard`、`#paramPreview`（次要「重新試算」）、`#paramConfirm`（主按鈕；enabled 條件不變＝最新一次預覽 valid）。
- **無障礙語意**：每個欄位列 `[data-param-field]` 是 `role="group"`，`aria-label="欄位 <名稱>"`，改欄位名時同步更新；選中列的 `[data-up]`／`[data-remove]` 的 `aria-label` 帶欄位名（`上移欄位 <名稱>`、`移除欄位 <名稱>`）；`[data-error]` 帶 `role="alert"`；`#paramQuickHint` 是 `aria-live="polite"`，`#paramParse` 以 `aria-describedby="paramQuickHint"` 說明為何 disabled。`#paramQuick` 的 Enter 在輸入法組字中（`isComposing` 或 `keyCode 229`）不處理。
- **選中列**：列內任一控制取得焦點即加 `.is-active`，該列才展開 `[data-tools]`：`.param-chips` 內的引用晶片 `button[data-insert-ref="卡ID:欄ID"]`（文字「卡名.欄名 值」）、`[data-up]`、`[data-remove]`。來源排除自己這一欄與會造成循環的來源（以 catalog 的 AST 加上草稿輸入內的引用 token 求傳遞閉包）；超過 8 個來源時出現 `input[data-ref-filter]`，晶片區限高可捲動。點晶片在 `[data-input]` 游標處插入 token（原值不是算式時改為 `=` 加 token，比照舊 `[data-insert]`）。加欄、移除、上移、套範本只重繪 `#paramFields`，焦點落在新欄名稱、相鄰列或被移動列的上移鈕。
- **試算與錯誤**：沿用 450ms 防抖與 `/engineering/preview`。valid：每欄 `[data-result]` 顯示核心回傳的精確值（如 `= 27 mm`）；invalid：以 `violations[].message` 的路徑前綴 `[pid:fid 卡.欄]` 取最後一個屬於本卡者為出錯欄，該列加 `.is-error`、`input[data-input]` 設 `aria-invalid="true"`，並出現 `[data-error]`（中文短句＋`<details>` 內的核心原文），其餘欄顯示「待試算」；解析不到欄位時錯誤顯示於 `#paramResult`。歸屬只認分節開頭（訊息開頭或緊接在 ` -> ` 之後）的 `[pid:fid `；分節被名稱裡的 ` -> ` 切歪時寧可不歸屬也不標錯欄；錯誤碼只取根因段（最後一個 ` -> ` 之後）。核心回多筆違規時，歸屬到本卡欄位的那筆顯示在該欄，其餘每一筆仍逐筆列在 `#paramResult`（中文短句加核心原文）；純函式 `ParameterUI.explainFailure(diagnostics, card)`、`ParameterUI.failureMarkup(failure)` 供測試呼叫。錯誤碼對照為 `ParameterUI.errorText(message)`（`I38 DIV_ZERO`＝除以零、`CYCLE`＝循環引用、`UNIT`＝單位不合、`MISSING`／`REFERENCE`＝找不到引用、`SYNTAX`／`AST`／`OP`＝算式寫法有誤、`NUMBER`＝數值格式有誤、`GEOMETRY`＝不是整數 mm、`NAME`＝名稱不合規定、`DUPLICATE`＝名稱或身分重複、`COUNT`／`UNSUPPORTED/CAPACITY`＝超過容量上限、`UNSUPPORTED/PRECISION`＝超過可表示的精度；其餘顯示原文）。
- **移除**：`#paramTemplate`（併入三顆範本鈕）、`select[data-insert]`（併入引用晶片）、每欄 `fieldset`／`legend`。`#paramParse` 保留但文字改「建立欄位」。
- **保留**：`#parameterEditor`、`#paramName`、`#paramQuick`、`#paramParse`、`[data-param-field]`、`[data-name]`、`[data-type]`、`[data-input]`、`[data-up]`、`[data-remove]`、`#paramAdd`、`#paramPreview`、`#paramResult`、`#paramStatus`、`#paramConfirm`、`#paramDiscard`、`#paramExport`、`#paramDelete`、`#paramImport`、`#paramFile`（仍為 `input[type=file]`）、`#paramLegacy`、`[data-param-use]`。測試改以 `#paramUsage`／`#paramExchange` 取兩個摺疊區（舊寫法 `details:first-of-type`／`details:last-child` 作廢）。
- **一致性**：常駐操作說明維持 3 塊（`.param-help`、`#paramResult`、`#paramStatus`）；`#paramQuickHint` 是輸入時才出現的即時預告，不計入。所有可點控制（含晶片、上移、移除、範本鈕、種類下拉、`summary`）最小 44px，390px 無水平溢出。樣式只用 `app.css :root` 既有 token，不載入外部字型。
- **畫布草稿卡**（GEO-224 最後一步）：建立新卡期間畫布顯示 `.parameter-card.is-draft`（虛線外框、右上角「草稿」標），內容跟著草稿欄位與試算結果更新；位置取 `nextCardPosition`（在右側欄版面定案之後才排，並平移視圖使草稿完整落在未被欄遮住的畫布內），確認時以同一組座標寫入真卡的 canvas-pos，所以真卡落在草稿卡的位置；不寫 canvas-pos、不進 `oc.parameters`、不影響保存內容與歷史，不可選取、不畫關係線；捨棄或確認後消失。
- **測試**：`parameter_workflow_test.js`（P76）新增斷言（第二輪追加：多層循環與草稿 token 建邊、草稿位置＝真卡位置、選中卡不被右欄遮住、離開路徑清 class、特殊字元、過期回應、可及名稱、多筆違規與訊息解析、窄畫面面板高度、輸入法 Enter）：範本鈕與 `aria-pressed`、快速輸入預告與 Enter、每欄核心值、`=1/0` 只標該欄且不可套用、循環來源不出現於晶片、點晶片後試算成功、1280px 右側固定欄與頁尾可見（含離開後其他檢視器仍在下方）、390px 控制項 ≥44px 且無水平溢出、草稿卡出現／消失且不進保存內容。
- GEO-227：參數編輯時同一張 `#paramGridLesson` 放在 `#canvasViewport`（不進 `#parameterEditor`，避免把 `#paramFields` 擠出窄畫面可視區），並避開上方繪圖工具。寬度 ≤900px 且展開時改為貼在視窗下方。知道了之後只留 `#paramGridLessonOpen`，窄螢幕時這顆鈕留在畫布內。圖解不是第四塊常駐說明。圖上的欄名、預設值、第二張的寬（預設寬 × 4/3）與來源控制的無障礙名稱，畫的時候向 `ParameterUI.panelTemplate`、`sourceControl` 標記與 `InfiniteGridWorkspace.lessonSurface` 讀；卡片標題向 `#btnNewParameter strong` 讀。`FeatureLessons.check()` 對不上時以教學 id `param-grid` 失敗。

## GEO-214 舊有限網格相容介面

以下控制只保留給舊有限來源；新來源使用上方 GEO-215 工作區。

- 選取既有舊有限來源時使用 `#gridSystemEditor`；不提供新建有限來源入口。`#btnNewGridSystem` 與空白畫布 `#emptyNewGridSystem` 建立的是 GEO-215 無限來源，開啟 `#infiniteGridWorkspace`。網格系統屬於來源組 `[data-filter-group="sources"]`，數量併入 `#sourceCount`；卡片、清單、搜尋、框選及小地圖均納入同一 `grid-system` 身分。
- `#gsName`、`#gsMainAlong` 編輯名稱及可選主支方向；`[data-gs-axis="u"]`／`[data-gs-axis="v"]` 各含排法和數值欄位。面材模式提示未套用時只有排法，不能把卡片示意當實際範圍。
- `#gsSave` 預覽新增／來源修改，`#gsReset` 重設未提交草稿，`#gsCancel` 取消建立；`#gsStatus[role="status"]` 呈現錯誤與結果。核心完整定義為唯一保存来源，名稱以 UTF-8 hex 安全傳輸。
- `#gsSurface`、`#gsOriginU`／`#gsOriginV` 選擇套用目標與原點；`#gsApply` 建立套用候選。需更換既有主格來源時，先明勾 `#gsReplaceExisting`；工程綁定主格不能隱含轉換。
- `#gsApplications [data-gs-application]` 列出主格與面；`[data-gs-edit-application]` 回填該次原點；`[data-gs-delete-application]` 預覽解除該次套用，依賴仍須通過核心守門，不連帶刪除來源。來源修改預覽使用既有 `.reference-impact`，包含主格、子格及後續依賴的新舊結果。
- 來源式面內主格顯示來源與原點，`#gridSourceSystemOpen` 開啟獨立系統；不提供普通軸編輯或工程綁定覆蓋。`#gsDelete` 在仍有引用時停用，核心也拒絕直接刪除。
- 操作見 `GRID-SYSTEM.md`；`grid_system_test.js` 經 `cdp_test.js` 執行真瀏覽器流程，原生守門另由 `tests/test_grid_system_contract.py` 驗證。

## 組構規則（GEO-226）

- 新增／複製在 uint32 回繞時仍避開 native 與所有同類草稿身分；下一版保留規則 ID，版本到上限則在既有 `#asmStatus` 拒絕，保留草稿。`#asmPreview` 提交前檢查新增配置 ID 未占用、明確編輯的原始配置內容未改，拒絕時不送 native 預覽；沒有新增 UI 入口。

- `#btnNewAssembly` 開啟唯一 `#assemblyWorkspace`。草稿、全部固定版本、材料配置同列於側欄；共用 WorkspaceShell 保存列。
- `[data-asm-draft]`、`[data-asm-rule="id:version"]`、`[data-asm-binding="id"]` 選來源。草稿 ID 作 HTML 屬性前必須 escape。
- `#asmNewRule`、`#asmName`、`#asmAddSlot`、`#asmAddMember`、`#asmAddJoint` 從空白定義開始；`#asmSwapN` 交換該接合的連續構件。
- `#asmKindN`、`#asmEndN`、`#asmSideN`、`#asmDirN` 與示意的 `[data-joint][data-face]` 寫入局部型別與固定身分。`#asmRotate`／`#asmZoomIn`／`#asmZoomOut` 只改檢視。
- `#asmSourceNA`／`#asmSourceNB`、`#asmValueNA`／`#asmValueNB`、`#asmContactN`、`#asmOrientationN` 編輯材料配置；空值可存草稿或合法未完成配置。
- `#asmBindingRule` 換版先開 `#asmMapping`；`#asmMapN` 及 `#asmApplyMapping` 明確對應槽位，`#asmCancelMapping` 撤回選擇。
- `#asmFooter` 只在有草稿或待確認預覽時出現。`#asmPreview` 在尚未取得預覽時顯示；預覽回來後改顯示 `#asmConfirm`（`.primary-button`，無效時 disabled）與 `#asmCancel`，兩者固定在對話框底部。沒有待確認變更時這三個鈕都隱藏。`#asmPreviewResult` 貼在底部按鈕上方、不跟表單一起捲動，先寫槽位名稱、截面前後值或規則版本，違反原因仍列在外面；完整 JSON 在「完整資料，給除錯對照」。`#asmStatus` 顯示拒絕原因。異步回應核對 context、編輯代次及序號。示意圖 `#asmDiagram` 的圖說使用槽位名稱與右側／左側／上側／下側，`[data-face]` 的值仍是 `+u`／`-u`／`+v`／`-v`。已發布配置用 `.asm-slot` 顯示槽位名稱與截面。
- `.assembly-card[data-kind="assembly-rule"|"assembly-binding"][data-id]` 沿用畫布身分、拖曳、搜尋、小地圖和選取。`#asmInspectorOpen` 返回工作區。
- `#asmClose` 返回畫布，草稿留在專案；需使用共用保存寫入檔案。新建／開啟專案會關閉舊工作區。
- 空間工作區在寬高皆 ≤720px 時收起 `.sm-source-actions` 的重複範例捷徑；設定區來源選擇、返回畫布與保存列仍保留，確認／建立按鈕須完整可見。
