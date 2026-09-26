# geometry-web UI 重構規劃(SSOT)

> 立案 2026-09-13。本檔是實作 agent 的**唯一事實來源**:任何與本檔衝突的推測,以本檔為準;本檔沒寫的設計取捨,不得自行決定,寫進 §9 決策佇列停手等使用者。
> 參考原型:`docs/prototype-構形Canvas-v2.html`(自 Downloads 複製入庫的純前端設計原型,4269 行)。
> 現況主體:`index.html`(1186 行)、`serve.py`、`web_bridge.c`;幾何核心 `../current_geometry.c`(**本規劃全程不改 C 端**)。
> 修訂:v1.1 2026-09-13 — 經 verifier read-back 與對抗審查後修正:canvas-pos 驗證描述、`layout.views` 行號、新增 §4.1 既有控制項去留、§5.5.3a 放置表單(D2 路徑補洞)、`mutate` 互斥、dump 解析正則、`#nodeLayer` 取捨定案、Phase 1 可機判版面檢查點。

---

## 0. 給實作 agent 的工作守則(先讀)

1. **真相在 bridge,不在瀏覽器。** 前端沒有自己的資料模型,所有幾何都從 `objects / surfaces / boundary / render` 拉;所有修改都發 `line <DSL>`。瀏覽器只允許持有「快照 + 相機 + 選取狀態 + 進行中的拖曳暫存」。
2. **C 端零改動**(`current_geometry.c`、`web_bridge.c`)。遇到需要 C 端新指令才能做的功能,不做,寫進 §9。
3. **每個階段都有裁判**(§7)。沒過裁判的階段不算完成,不得進下一階段。
4. **原型是殼與元件庫,不是主幹。** 主幹是 `index.html` 既有的 bridge 邏輯層(`api()`、三視圖工具、`emitNewSurface / emitBoundary / applyVertexEdit / applyEdgeEdit`)。原型的資料層(§5.3 的 (c) 類函式)整段不搬。
5. **原型與核心衝突時,核心贏。** 例:原型允許任意多邊形,核心只接受正交多邊形;原型有 cm,核心是整數 mm;原型「建空間即生六面」,核心「面可游離、空間收成員」。
6. 讀檔守則:`index.html` 與原型都是大檔,用 `sed -n` / `grep -n` 分段讀,不整檔讀。附錄 A/B/C 已把合約抽出來,先讀附錄再讀原始碼。
7. 回報格式:每階段結束回報 ≤60 行,列「改了哪些檔 + 裁判輸出摘要(pass/fail 數)+ 未做/卡住的項目」。不貼大段原始碼。

---

## 1. 背景與目標

- 現況 `index.html` 已有兩層畫布:三視圖(`#cv`,建面/挖孔/編輯邊界/拖參考線)與物件畫布第一期(`#ocv`,卡片 + canvas-pos)。功能可用,但 UI 是工程原型,使用者不滿意。
- 原型 `prototype-構形Canvas-v2.html` 是使用者認可的視覺與互動方向:三欄殼(左物件庫 / 中無限畫布 / 右檢視器)、卡片式物件、面內工作區、空間工作區、對話框、toast、minimap。
- 目標:**把原型的殼與互動搬到 index.html 上,底下全部接 bridge**,並沿用既有測試當回歸裁判。

## 2. 🔒 已拍板決定(使用者 2026-09-13 拍板,不得改)

| # | 決定 | 含義 |
|---|---|---|
| D1 | **物件畫布為主,三視圖按需開啟,且只開對該面有意義的視圖** | 主畫面是原型的無限畫布。三視圖不常駐;在面內工作區提供「投影」面板,預設只顯示與該面法向對應的那一個視圖(§5.5.4),其餘視圖可手動勾開。空間工作區可開完整三視圖。 |
| D2 | **空間建立兩者並存:先有面再收成員 + 快速六面盒** | 面可游離。建空間 = 建空容器後勾選成員面重宣告 `space`;另提供「快速六面盒」對話框,前端組 6 行 `surface` + 1 行 `space` 送 bridge。C 端不動。 |
| D3 | **語意關係只留 contains / boundedBy,由 space 成員推導** | 畫布上的連線直接由 `objects` 回傳的 `spaces[].members` 畫;沒有獨立的關係資料、沒有「連接」工具、沒有關係對話框。 |
| D4 | **面內元素:opening = 挖孔,referenceLine = guide** | opening 走既有 `emitBoundary` 加內孔環(等同三視圖的挖孔工具);referenceLine 走 `guide id 面id u|v offset`。都是既有指令。 |

### 2026-09-26 補充：增量擴充與既有功能優化

使用者明示：有效的建議採增量更新，保留無限畫布、構件物件流程的既有能力與使用者資料；
原有功能若發現問題，允許改善介面、操作步驟與實作。「保留」不要求凍結現有按鈕、步驟或程式碼，
也不要求延續已確認的錯誤行為。
此約束適用於後續 PDF／參考圖重建；需求與回歸條件記於 `BACKLOG.md` GEO-198。

- 無限物件畫布仍為主工作區；保留物件卡片、面內編輯、空間組成與既有構件操作。
- 參考資料重建是可選入口；使用者可以不匯入資料，直接沿用現有手動建立流程。
- 匯入、校準、描繪、補充高度是可分次完成的工作，不得變成進入畫布或編輯既有物件的強制步驟。
- 經確認且符合公理的重建成果接入既有物件與編輯機制；來源資料及待補資訊不構成另一份幾何真相。
- 每次優化先說明具體問題、預期改善與影響範圍，分批實作並驗證；驗收同時確認問題已改善、既有任務仍能完成、既有資料仍可使用。
- 修正錯誤時同步更新對應預期並保留缺陷回歸案例；其他既有驗收條件維持有效。幾何行為仍以公理為準。
- 本補充原先只記錄設計約束。2026-09-26 使用者進一步核准 GEO-198 第一批：PDF 描面、來源紀錄及 `.gcanvas` 專案保存；詳見 `REFERENCE-PROJECT.md`。幾何仍以核心及 `.scene` 為準，公理未變更。
- GEO-198 允許前端持有可保存的來源、校準、紀錄及來源關聯歷史；不保存另一份權威幾何。§0／§4 的舊限制不排除此項已核准的中繼資料擴充。

## 3. 常規決定(我定的,屬工程慣例;若使用者反對可改)

| # | 決定 | 理由 |
|---|---|---|
| C1 | 單位一律 **mm 整數**,UI 顯示 mm | 核心是整數 mm,無浮點。原型的 cm 與小數不搬。 |
| C2 | 檔案拆成 `index.html`(骨架)+ `app.css` + `app.js`,`serve.py` 加靜態檔路由 | 合併後估計超過 5000 行,單檔對 agent 編輯極不友善。classic script 的頂層 `const/let` 仍是全域,測試靠全域讀狀態不受影響。 |
| C3 | 面內編輯器座標映射沿用 index.html 現況:u→x、v→y(y 朝下),原點可平移 | 與仰視圖(X 右、Y 下)一致;原型也是 y 朝下。不引入翻轉。 |
| C4 | 卡片維持 SVG 實作(`#ocv > #oroot`,`.ocard` class),套原型視覺 | cdp_test 靠 `.ocard` 與 SVG 座標;改 div 會讓整套測試重寫。 |
| C5 | 保留 DSL 指令列 `#cmd`(進階入口),放在狀態列右側 | 角材/網格等尚無 UI 的功能靠它。 |
| C6 | 不做深色模式 | 原型宣告 `color-scheme: light`;不在範圍。 |
| C7 | 物件命名 = id(例「面 3」「空間 1」) | 核心沒有名稱欄位;原型的 rename 功能不搬。 |

## 4. 非目標(明確不做)

- localStorage 真相、JSON 匯入匯出、demo state、專案名稱/儲存狀態。
- 六種語意關係、連接工具、關係對話框、關係標籤。
- 原型的「建空間自動生六面」語意(改為 D2 的快速六面盒)。
- 任意多邊形、頂點插入(`insertFaceVertex`)、頂點刪除:核心只接受正交多邊形,現有邏輯沒有「保持正交的插入/刪除」,列入 §9。
- 刪除物件、刪除參考線:**DSL 沒有 delete 指令**(只有 reset / undo),UI 不提供刪除;列入 §9 為 C 端工單候選。
- 角材(timber / place / grid)的圖形化操作:維持指令列;三視圖面板仍會畫出來並可 hover/pick。
- 原型死碼(`openEditObject` 的編輯分支)與其表單編輯流程。

### 4.1 index.html 既有控制項去留(逐一交代)

| 既有 | 去留 |
|---|---|
| `#tool`(view/rect/poly/hole/edit)、`#workSurf`、`#newZ` | **保留**,搬進「三視圖總覽」面板的工具列(§5.4 `#btnObj` 開啟的那個面板),換皮不換邏輯 |
| `#btnObj` | 保留 id,語意改為「開/關三視圖總覽」 |
| `#btnNewRect / #btnNewPoly / #btnNewSpace` | 保留 id,搬到左欄物件庫 |
| `#btnHole2` | 面內工作區的「開口」工具取代,id 可保留在工具列內 |
| `#btnBack`、`#crumb` | 由原型 `#workspaceBackButton / #workspaceBackLabel` 取代;`leaveFocus` 全域保留 |
| `#btnOpen #file #sceneList #btnScene #btnEx #btnExport #btnZoom #btnClear` | 保留,搬到 topbar 右側與狀態列 |
| `#cmd #status #hovertxt` | 保留,狀態列 |
| `#cv #world #overlay` | 保留,放在三視圖總覽面板內 |
| `#ocv #oroot` | 保留,即主畫布 |

## 5. 目標架構與 UI 規格

### 5.1 分層

```
bridge API 層   api(cmd) → POST /api → web_bridge.exe        (既有,不動)
快照層          snap = { faces, spaces, surfaces, bmap }     (每次 mutate 後重新拉 objects/surfaces;boundary 逐面快取)
畫面層          原型的 render* 函式改成「吃 snap + ui」的純函式,輸出 HTML/SVG
事件層          pointer/keyboard → 組 DSL → api("line …") → 重拉快照 → 重畫
歷史            只有 api("line undo") / api("line redo");前端無 history stack
```

- 快照層資料形狀直接採用 bridge 回傳(附錄 A),不另造欄位名。
- 所有 mutate 走同一個 helper:`mutate(lines: string[])`,逐行送 `line`,第 k 行失敗時送 `line undo` k−1 次回滾前面已成功的行,然後 toast 錯誤(`error` 欄位原文)。canvas-pos 不記 history(核心行為),所以卡片拖曳不用走 `mutate`,且 `mutate` 的 lines 裡**不得混入 canvas-pos**(否則 undo 次數會算錯)。
- **互斥**:`mutate` 執行期間設 `ui.busy = true`,畫布 pointer 事件、所有會發指令的按鈕與 `#cmd` 一律忽略輸入(視覺上 disable);完成或回滾後解鎖。同一時間只允許一個 `mutate` 在飛。

### 5.2 檔案配置

```
geometry-web/
  index.html      骨架(DOM),不含 CSS/JS
  app.css         自原型 8-735 行搬入並改名/裁剪
  app.js          既有 index.html 的 JS + 原型 (a)(b) 類函式改寫
  serve.py        GET /app.css, /app.js 靜態路由(其餘不動)
  docs/           本檔、原型、DOM 合約
  cdp_test.js     更新座標與文案(§7)
  canvas_test.js  不動
```

### 5.3 原型函式取捨(對照附錄 C)

- **(a) 純畫面/純函式:直接搬**,但改吃 mm 整數並拿掉 cm 換算(`formatLength/Area/Volume` 改 mm / m² / m³ 計算基準)。`previewFaceSvg` 改吃 `boundary` 回傳的 loops(loops[0] 外環、其餘為孔)。
- **(b) 綁 state 的畫面函式:搬骨架、改參數**。所有 `state.objects/nodes/relations` 讀取改為讀 `snap.faces/snap.spaces`;`state.camera` 改為前端本地 `oc.panX/panY/zoom`(既有)。
- **(c) 資料/持久化/歷史:整段丟棄。** 名單見附錄 C。

### 5.4 主畫面(物件畫布)

**頂列(topbar)**:brand |(中)工具群:選取/移動、平移、＋面·矩形、＋面·多邊形 |(右)開啟場景檔、載入範例(select)、匯出 .scene、undo、redo、縮放重置(fit)。
- 拿掉:搜尋框可留(過濾卡片)、`importButton`(改為開啟 .scene)、`createButton`(改為左欄物件庫)。

**左欄(sidebar-left)**:
- 物件庫:＋面·矩形、＋面·多邊形(設 `oc.drawTool`,在畫布上拉/點,沿用 `objDrawDown / drawRectPreview / drawPolyPreview / objEmitFace`)、＋空間(空容器,`space <newid>`)、＋快速六面盒(開 §5.6 對話框)。
- 篩選:面 / 空間 兩個 checkbox + 計數(自 `snap`)。
- 物件清單:每列 = kind 圖示 + 名稱(「面 3」)+ 副標(boundary: `placed ? 已放置 : 游離`、`placement` 類:「自帶矩形」;space: `closed ? 封閉 : 開放` + 成員數)。點列 = 選取並定位卡片。
- 畫布選項:吸附開關、格線開關(只影響前端畫布,不進核心)。

**中央(canvasViewport)**:
- 卡片:每個 `snap.faces[]` 與 `snap.spaces[]` 一張;位置 = `cx,cy`(核心給的 canvas-pos 或預設);拖曳結束送 `line canvas-pos <kind> <id> <x> <y>`(既有 index.html:1077)。
- 卡片內容:面卡 = `previewFaceSvg(loops)` + 標題 + 副標;空間卡 = 成員數、closed 標記、`previewSpaceSvg` 可改為簡化的六槽示意(±X/±Y/±Z 哪些被佔)。
- 連線:對每個 space,對每個 member 畫 space→face 的邊(原型 `renderEdges / relationGeometry / nodeAnchor`),標籤 contains;無其他關係。
- 雙擊面卡 → 面內工作區;雙擊空間卡 → 空間工作區(既有 `enterFocus`)。
- 縮放控制(zoomIn/Out/level/home)、minimap(`drawMinimap` 改讀卡片與 space 邊)、空狀態。
- **`placement` 類面卡(自帶 rect、無 boundary)不能進面內工作區**(沒有 boundary 可編),卡片標示「無邊界」,雙擊只顯示檢視器。

**右欄(inspector)**:選取物件的屬性:kind、id、bbox、placed/closed、所屬空間(由 spaces.members 反查,即 boundedBy)、成員列表;按鈕:進入工作區、(space)編輯成員、定位。

**狀態列(statusbar)**:`#status`(既有,測試依賴)+ hover 文字 + `#cmd` 指令列 + `#btnClear`。

### 5.5 面內工作區(objectWorkspace,face 模式)

沿用原型 `faceWorkspaceShell / renderFaceWorkspace` 的三欄殼(左內容清單 / 中編輯器 / 右檢視器),邏輯全接既有。

**5.5.1 左欄「面內物件」**:
- 邊界:外環頂點數、每邊 fixity(F/X)。
- 孔:loops[1..] 每個一列(頂點數、bbox)。
- 參考線:此面的 guides。**bridge 沒有列 guide 的指令**,做法:呼叫 `dump`,對 `text` 逐行套正則 `^guide (\d+) (\d+) (u|v) (-?\d+)\s*$`,第 2 群等於此面的 placement id 的行就是本面的參考線;第 1 群是 guide 自己的 id,第 3、4 群是軸向與 offset(dump 輸出格式見 current_geometry.c:8316-8319)。

**5.5.2 中央編輯器**:SVG,座標映射 C3。工具:
| 工具 | 快捷鍵 | 行為 | 送出指令 |
|---|---|---|---|
| 選取/拖曳 | v | 拖頂點 → `applyVertexEdit`;拖邊 → `applyEdgeEdit`(既有,保持正交);放開後 `emitBoundary` | `boundary <id> outline … [hole …] [fixity …]`(整段重宣告) |
| 參考線 | l | 在面內點一下:水平拖 → `v` 方向線、垂直拖 → `u` 方向線(依拖曳主軸);offset = 吸附後座標 | `guide <newid.guide> <sid> u|v <offset>`;拖既有線 → `move <id> <offset>` |
| 開口 | r | 拉矩形 → 加一個孔環 | `boundary …`(既有挖孔邏輯 `oc.drawTool="hole"`) |
| 平移 | h / 空白鍵 | 平移相機 | 無 |
| fit | f | `fitFaceEditor` | 無 |

- 頂點/邊命中:沿用既有 `bhit`(bridge)或原型的 `data-face-hit` 屬性法二擇一,**選 `data-face-hit`**(純前端、無往返),但拖曳套用仍用既有 `applyVertexEdit/applyEdgeEdit`。
- 吸附:`snapFacePoint`(原型)改成整數 mm,格距預設 50 mm。
- guide 的 `sid` 是**承載面 id**(placement id),不是 boundary id;`surface` 合體時兩者同 id,`placement … on boundary` 時不同,要從 `surfaces` 回傳的 `{id, boundary}` 對照取得。游離 boundary(無 placement)**不能放參考線**,工具停用並提示。
- 錯誤:核心拒絕(非正交、孔越界、重複 id)→ toast 原文,畫面回到快照。

**5.5.3 右欄檢視器**:面資料(id、承載面 id、origin/u/v 軸、bbox、面積由外環減孔算)、所屬空間、fixity 編輯(每邊 F/X 切換 → 重宣告 boundary)。

**5.5.3a 「放置」區(必做,D2 的「先有面再收成員」靠它)**:
- 物件庫的「＋面·矩形/多邊形」只建**游離 boundary**(既有 `objEmitFace` 只送 `boundary … outline …`,index.html:1004-1013)。游離面沒有位置與法向,不能算 closed、不能放參考線、不會出現在三視圖。
- 因此面的檢視器(主畫布右欄與面內工作區右欄都要有)提供「放置」表單:origin x/y/z(mm 整數)+ u 軸、v 軸(各為 ±x/±y/±z 下拉,u⊥v 才可送出)+ 六個常用預設(天花 `u+x v+y`、地板 `u+y v+x`、y=0 牆 `u+x v+z`、y=D 牆 `u+z v+x`、x=0 牆 `u+z v+y`、x=W 牆 `u+y v+z`,填入軸向後 origin 由使用者填)。
- 送出:`placement <同 boundary id> on boundary <id> origin x y z u ±a v ±b`(附錄 A.2);已放置的面再送同 id 即交易式重綁。成功後該面 `placed:true`。
- 若 placement id 已被「自帶 rect 的 placement」占用(`newid.placement` 與 boundary id 衝突),改用 `newid.placement` 給的 id;`surfaces` 回傳的 `{id, boundary}` 是兩者的對照表。

**5.5.4 「投影」面板(D1)**:
- 檢視器底部一個可摺疊面板「投影視圖」,預設關閉;打開時呼叫 `render`,只取對應視圖的 ops 段(ops 依 begin/end 分三段,索引 0/1/2 = FRONT/SIDE/BOTTOM)。
- 預設視圖由承載面法向 N = U×V 決定:N 為 ±Z → BOTTOM(2);±Y → FRONT(0);±X → SIDE(1)。另兩個視圖用 checkbox 手動加開。
- ops 座標是視圖局部 mm,**不含 tx/ty**;單視圖顯示時直接用 `bounds` 當 viewBox,不加 tx/ty。
- 面板內沿用既有 hover/pick(`pick <v> …`)與參考線拖曳(`drag <guide_idx> <v> …`)。
- 既有註解把索引 2 叫「俯視圖」,核心定義是「仰視圖」(X 右、Y 下,從房間內往上看);UI 文案用「仰視」。

### 5.6 空間工作區(space 模式)

- 沿用原型 `renderSpaceWorkspace` 殼:左成員清單、中成員面卡片格、右檢視器。
- 成員編輯:「編輯成員」開勾選清單(所有 boundary 面,已屬其他空間的標示),確認 → `space <id> boundary <ids…>` 重宣告(交易式,失敗 toast)。移除成員同法。
- closed 狀態與六個方向槽位(±X/±Y/±Z)顯示哪些已被佔(需自行由 `surfaces` 的 u/v 算法向與位置;若算不出來只顯示 closed 布林)。
- 「投影」面板:三視圖全開(整個 `render` 結果),沿用既有三視圖互動。
- **快速六面盒對話框**:輸入 W、D、H(mm 整數,預設 4000/3000/2500)與是否含地板;按確認 → 用 `newid` 取起始 id,照 `../room_full.scene` 的 6 行 `surface` 模板(origin/u/v/outline 逐行對應)+ 1 行 `space`,經 `mutate()` 送出;成功後為 7 個物件各送 canvas-pos 排成一排。

### 5.7 對話框與回饋

- 對話框只留:快速六面盒、編輯空間成員、載入範例(可用 select 取代)。原型的 objectDialog/viewDialog/relationDialog 三者的殼可重用,內容全換。
- toast:所有 bridge `ok:false` 的 `error` 原文;~~成功操作不 toast~~(**作廢**:UIUX-FIX-PLAN.md Q2 改為成功訊息同時發 `.toast.ok` 2000ms,錯誤 toast 3600ms)。
- 狀態列 `#status` 文案沿用既有(cdp_test 比對中文),改文案必須同步改測試。

### 5.8 鍵盤

主畫布:Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z(undo/redo 走 bridge)、Esc(取消繪製 / 退出工作區,沿用既有 615-644)、v/h、f、1、空白鍵平移、`/` 聚焦搜尋。
面內工作區:Esc、v/l/r/h、f、1、空白鍵。
不做:Ctrl+S、Ctrl+D、Delete。

## 6. 階段計畫

每階段:改動範圍 → 裁判 → 完成定義(DoD)。**過閘才留**。

### Phase 0 地基(不改任何 UI)
- 拆檔(C2):`index.html` → `index.html + app.css + app.js`;`serve.py` 加 `/app.css`、`/app.js` 路由。
- `cdp_test.js`:改成依 ✓/✗ 計數決定 exit code(現況固定 exit 0,附錄 B §9)。
- 新增 `docs/DOM-CONTRACT.md`:列出測試依賴的 id / class / 全域(附錄 B §7),之後每階段改 DOM 都要對照。
- 裁判:`node canvas_test.js direct` 全 pass;`node cdp_test.js` 全 ✓(exit 0)。
- DoD:兩個裁判過,`git diff` 只含拆檔與測試 exit code 修改,行為零變化。

### Phase 1 殼
- `app.css` 引入原型 CSS(附錄 C §2 的群組),改為三欄殼;`index.html` 改為原型 DOM 骨架(附錄 C §1),把既有 `#cv`、`#ocv`、`#status`、`#cmd` 等測試依賴的元素放進新骨架對應位置(`#ocv` 進 canvasViewport;`#cv` 暫放同一區,`hidden` 切換)。
- 頂列/左欄按鈕接既有 handler(btnOpen/file/sceneList/btnExport/btnZoom/btnNewRect/btnNewPoly/btnNewSpace/btnBack)。
- 物件清單、右欄檢視器、狀態列接 `snap`。
- 裁判:cdp_test 更新硬編座標與 elementFromPoint 後全 ✓;canvas_test 不動全 pass;headless Chrome 截圖存 `docs/screens/phase1-*.png`,並在 cdp_test 新增可機判的版面檢查點(全部要 ✓):
  1. `#app` 是 grid,三列高度 = topbar / 1fr / statusbar(`getComputedStyle` 的 `gridTemplateRows` 含 3 個值)。
  2. `.workspace` 三欄:左欄寬 ≈ 242px、右欄寬 ≈ 326px(±2px),中央 `#canvasViewport` 佔剩餘寬。
  3. topbar 內元素順序:brand → tool-group → actions(以 `children` 順序斷言)。
  4. `#ocv` 在 `#canvasViewport` 內且與其等大(rect 差 ≤ 2px)。
  5. `#status` 與 `#cmd` 在 statusbar 內(`closest('.statusbar')` 非 null)。
- DoD:上述 5 點 + 兩套測試全過;既有功能(建面、建空間、拖卡片、進面編輯、undo)全部照舊可用。

### Phase 2 卡片與連線
- 面卡/空間卡套原型 node 視覺(C4:SVG 內實作),`previewFaceSvg` 吃 loops;space→member 連線(D3);minimap;空狀態;搜尋過濾;縮放控制。
- 裁判:cdp_test 既有卡片測試 ✓ + 新增:建 2 面 + 1 空間(用 `#cmd` 送 `space 1 boundary 1 2`)後 `#edgeGroup` 有 2 條邊;搜尋「面 1」只剩 1 張卡。
- DoD:附錄 B §7 全部 id/class/全域仍存在。

### Phase 3 面內工作區
- 原型 objectWorkspace 殼 + 既有編輯邏輯;工具表 §5.5.2;參考線(guide/move);開口(hole);fixity 切換;投影面板(D1)。
- 裁判:cdp_test 既有「進入面編輯 / 拖頂點 / Esc / undo redo」✓ + 新增:
  - 在面 1 拉一條參考線 → `dump` 文本含 `guide <n> 1 v <offset>`;拖它 → offset 改變。
  - 拉開口 → `boundary 1` 回傳 loops 長度 2。
  - 開投影面板,天花板面(N=+Z)只出現一個 `<g data-view="2">`。
  - 送非法編輯(讓頂點跑出正交)→ toast 出現且 `boundary 1` 未變。
  - 建一個游離矩形面 → 檢視器「放置」表單選「天花」預設、origin 0 0 2500 → 送出後 `objects` 該面 `placed:true`、`surfaces` 出現對應 id;再在該面拉參考線成功(游離時參考線工具應為 disabled)。
- DoD:上述全 ✓;canvas_test 全 pass。

### Phase 4 空間工作區
- 成員編輯、closed 顯示、三視圖面板、快速六面盒(D2)。
- 裁判:新增 cdp 測試:快速六面盒 4000/3000/2500 → `objects` 回 6 faces + 1 space 且 `closed:true`;移除一個成員 → `closed:false`;第 4 行故意送錯(測試注入)→ `objects` 回到執行前狀態(mutate 回滾)。
- DoD:全 ✓。

### Phase 5 收尾
- 鍵盤表 §5.8、toast 一致化、README(`geometry-web/README.md`:啟動、測試、檔案配置)、`../BACKLOG.md` 新增本次衍生的 C 端工單候選(§9 內容)。
- 裁判:兩套測試全過;verifier agent 對本檔 §5 逐條 read-back 核對。

## 7. 測試合約

**必須保留**(cdp_test.js 依賴,附錄 B §7):
- DOM id:`#cv #world #overlay #ocv #oroot #topbar #status #btnObj #btnNewRect #btnNewSpace #btnNewPoly`(`#btnObj` 在 D1 下語意改為「顯示三視圖總覽」,仍要存在且可 click 切換 `#cv/#ocv` hidden)。
- class:`.ocard`,並保留 `dataset`(kind/id)。
- 全域(classic script 頂層):`oc`(含 `on faces spaces focus edit bmap panX panY zoom rect card pan drawTool`)、`api`、`layout`、`leaveFocus`。
- `#status` 文案:改動需同步改 cdp_test。

**必然要改**:硬編座標(640,350 等)與 `elementFromPoint` 落點、卡片 `getBoundingClientRect` 假設。改法:測試改為先讀 `.ocard` 的實際 rect 再算座標,不硬編。

**新增測試**放進 cdp_test.js 同一支(K、L、M… 段),不另開檔;每段印 ✓/✗ 並計數。

**跑法**:
```bash
cd /d/knowledgebase/geometry-web && python serve.py 8765
```
```bash
cd /d/knowledgebase/geometry-web && node canvas_test.js direct
```
```bash
cd /d/knowledgebase/geometry-web && node cdp_test.js
```
(cdp_test 需 `C:\Program Files\Google\Chrome\Application\chrome.exe`,port 9333,serve.py 已在 8765。)

## 8. 已知陷阱(實作前必讀)

1. 視圖索引(current_geometry.c:1959-1975):0=FRONT(X 右、Z 上,看向 −Y)、1=SIDE(Y 右、Z 上)、2=BOTTOM(X 右、Y 下,仰視)。index.html:352/363 註解寫「俯視」是錯的。
2. `render` 的 ops 座標**未含** `tx/ty`;三視圖總覽要自己 translate,單視圖不要加。
3. `guide` / `timber` 重宣告同 id 會被**拒絕**(7252 / 7346);參考線位置改用 `move`,不能重發 guide。
4. ~~DSL **沒有 delete**;`undo` 是唯一反悔手段~~(**作廢**:§9 Q1 已做 `delete <kind> <id>` 交易重驗,commit `551e416`)。
5. 核心只收正交多邊形;頂點拖曳要用既有 `applyVertexEdit`(連動相鄰邊),不能自由移點。
6. `surface N` 合體 = boundary N + placement N 兩個物件同 id;`placement … on boundary M` 時 id 可不同。guide 的面 id 是 placement id。
7. `objects` 的 `kind:"placement"` 面沒有 boundary,不能進面內編輯。
8. `canvas-pos` 不進 history,undo 不會還原卡片位置。
9. `line` 失敗回 `{ok:false,error}`;`drag/uv/proj/bhit` 失敗只回 `{ok:false}` 無 error。
10. 交易語意:boundary/placement/space/surface 重宣告失敗時 World 整份回滾,前端只要重拉快照即可。
11. `space` 的 `closed` 要六個方向槽位各恰一片成員面;成員面法向由 U×V 決定,六面盒模板的軸向不能亂改(照 room_full.scene)。
12. bridge 沒有「列 guide」指令;面內參考線清單從 `dump` 文本解析。
13. cdp_test 目前 exit code 不反映結果(Phase 0 修)。
14. `serve.py` 對 `/api` 收到非 JSON body 會拋例外(見 `_serve.log`);前端送 body 前務必 `JSON.stringify({cmd})`。

## 9. 決策佇列(2026-09-13 使用者拍板 🔒)

| # | 問題 | 決定 | 落點 |
|---|---|---|---|
| Q1 | 刪除物件 / 刪除參考線 | **做**:C 端 `delete <kind> <id>` 走交易重驗 | ✅ 已完成 commit `551e416`(cdp P6) |
| Q2 | 正交多邊形的頂點插入(加凹口 = 一次插兩點) | **做**;實作定案:矩形凹口(4 頂點),前端走 `boundary` 重宣告,不需 C 端原語 | ✅ 已完成 commit `69f59fe`(cdp P7) |
| Q3 | 角材 / 網格的圖形化操作 | **做**:本期 | ✅ 已完成 commit `820195f`(cdp P8):面內角材工具(t)+網格表單+足跡預覽+圖層刪除 |
| Q4 | 面內編輯器 v 軸方向(C3 目前 y 朝下) | **維持** | 不動 |
| Q5 | 檔案拆分(C2) | 拆(已落實) | Phase 0 |

## 10. 交辦 prompt(直接貼給實作 agent)

```
你要執行 D:\knowledgebase\geometry\geometry-web\docs\UI-REDESIGN-PLAN.md 的 Phase <N>。
先讀該檔 §0、§2、§3、§5、§6 的 Phase <N>、§7、§8,再讀附錄 A/B/C;原始碼用 sed -n 分段讀。
規則:C 端零改動;真相在 bridge;沒寫的設計取捨不做、寫進 §9 停手;每階段裁判沒過不得宣告完成。
完成後回報 ≤60 行:改了哪些檔(檔名:行號範圍)、裁判輸出摘要(pass/fail 數與失敗項)、未做/卡住的項目與原因。
不要貼大段原始碼。
```

---

## 附錄 A:bridge 指令與 DSL 合約(自 web_bridge.c / current_geometry.c 抽出,2026-09-13)

### A.1 bridge 指令(stdin 一行 → stdout 一行 JSON)

| 指令 | 回傳 | 出處 |
|---|---|---|
| `render` | `{ok,layout:{w,h,views:[{tx,ty,bounds:[minx,miny,maxx,maxy]}×3]},ops:[…]}`;無面時 `{ok:false,error}`。ops 依 FRONT/SIDE/BOTTOM 順序,各段 `begin{tx,ty}` … `end{}`。op:`rect{x0,y0,x1,y1,s}` `poly{p:[x,y,…],s}` `line{x0,y0,x1,y1,s}` `text{x,y,s,rot,t}`。`s` 見 STYLE(附錄 B)。 | web_bridge.c:179-209 |
| `pick <v> <x> <y> <r>` | `{ok,none,desc,guide,timber,face,hover:[ops]}` | 211-240 |
| `drag <guide_idx> <v> <x> <y>` | `{ok:true,offset}` / `{ok:false}` | 242-275 |
| `line <text>` | `{ok:true}` / `{ok:false,error:"line N: …"}` | 277-286 |
| `loadfile <path>` | 同上;失敗 World 還原 | 288-302 |
| `uv <v> <x> <y> <sid>` | `{ok,u,v}` / `{ok:false}` | 307-320 |
| `proj <v> <u> <v> <sid>` | `{ok,x,y}` / `{ok:false}` | 323-335 |
| `newid` | `{ok,boundary,placement,guide,grid,timber,space}`(各命名空間 max+1) | 338-358 |
| `surfaces` | `{ok,surfaces:[{id,boundary,origin:[x,y,z],u:[…],v:[…]}]}` | 361-379 |
| `boundary <id>` | `{ok,loops:[{verts:[[u,v]…],fixity:[1/0…]}]}`,loops[0]=外環;不存在 `{ok:false,error}` | 382-409 |
| `bhit <id> <u> <v> <r>` | `{ok,kind:"vertex"|"edge",loop,index}` / `{ok:false}` | 412-424 |
| `objects` | `{ok,faces:[{kind:"boundary",id,placed,bbox:[lo_u,lo_v,hi_u,hi_v],cx,cy,hasPos} | {kind:"placement",id,placed:true,bbox,cx,cy,hasPos}],spaces:[{id,members:[…],closed,cx,cy,hasPos}]}` | 450-526 |
| `dump` | `{ok,text}`(可重放 DSL 全文) | 529-558 |
| `default` / `reset` | `{ok:true}` | 578-585 |
| 未知 | `{ok:false,error:"不認得的橋接指令"}` | 636 |

### A.2 DSL(`line <…>` 的內容)

| 指令 | 語法 | 出處(current_geometry.c) |
|---|---|---|
| `boundary` | `boundary id outline u,v u,v … [kind room_plan\|wall_elevation\|unspecified] [fixity F/X …] [hole u,v … [fixity …]]…`;fixity 修飾最近一個環;預設全 F | 6677-6824 |
| `placement` | `placement id [on boundary B] origin x y z u ±x\|±y\|±z v ±x\|±y\|±z [rect u0 v0 u1 v1]`;無 boundary 時 rect 必填 | 6834-7003 |
| `surface` | ① `surface id on boundary B origin … u … v …`;② `surface id origin … u … v … rect …`;③ `surface id origin x y z u … v … outline u,v … [fixity][hole …]`(同時建 boundary+placement,同 id) | 7015-7224 |
| `space` | `space id [boundary id id …]`;無成員 = 空容器 | 8121-8191;closed 判定 5744-5776 |
| `guide` | `guide id <placement_id> u\|v <offset>`(恰 5 token;同 id 重宣告拒絕) | 7227-7293 |
| `grid` | `grid id on <placement_id> u c1 [c2…] [v c1 …]` | 7464-7621 |
| `timber` | `timber id 長 A B` 或 `timber id A B`(auto) | 7302-7359 |
| `place` | `place 角材 on 面 (at u v \| at-guides g1 g2 \| at-grid G u\|v i \| at-edge e<i>\|h<i>e<j>) [through …] ±u\|±v ±n` | 7641-8071 |
| `move` | `move guide_id new_offset` | 8072-8117 |
| `reset` | `reset` | 8194-8208 |
| `canvas-pos` | `canvas-pos boundary\|placement\|space id x y`;會驗 kind 合法、id/x/y 為整數、被指物件存在(否則 `error`),但不做幾何驗證、**不記 history** | 8402-8442 |
| `undo` / `redo` | 只能經 `line undo` / `line redo`(互動層攔截,不在 .scene 格式) | 3348-3374 |

ID 命名空間:boundary / placement / guide / grid / timber / space 各自獨立。重宣告:boundary/placement/space/surface 交易式重綁(`world_replace_object` 6375-6393,失敗整份回滾);guide/timber 拒絕;grid 同 id 可補另一軸。

### A.3 六面盒模板(自 `../room_full.scene`,W=4000 D=3000 H=2500)

```
surface 1 origin 0 0 H  u +x v +y outline 0,0 W,0 W,D 0,D      # 天花 N=+Z
surface 2 origin 0 0 0  u +y v +x outline 0,0 D,0 D,W 0,W      # 地板 N=−Z
surface 3 origin 0 0 0  u +x v +z outline 0,0 W,0 W,H 0,H      # y=0 牆 N=−Y
surface 4 origin 0 D 0  u +z v +x outline 0,0 H,0 H,W 0,W      # y=D 牆 N=+Y
surface 5 origin 0 0 0  u +z v +y outline 0,0 H,0 H,D 0,D      # x=0 牆 N=−X
surface 6 origin W 0 0  u +y v +z outline 0,0 D,0 D,H 0,H      # x=W 牆 N=+X
space 1 boundary 1 2 3 4 5 6
```
id 以 `newid` 的 boundary/placement/space 起算(surface 合體需 boundary 與 placement 兩邊都空,取兩者 max)。

---

## 附錄 B:index.html 既有合約(2026-09-13 盤點)

### B.1 DOM id(index.html:34-70)
`topbar btnOpen file sceneList btnScene btnZoom btnObj tool workSurf newZ btnExport objtools btnNewRect btnNewPoly btnNewSpace btnHole2 btnBack crumb cv world overlay ocv oroot bar status hovertxt cmd btnEx btnClear`

### B.2 頂層狀態(全域)
- 98-103:`layout zoom panX panY selected panning dragging pickSeq`
- 311-319:`tool workSurfaces drawPts rectStart editLoops editBid editDrag affineCache previewGs`
- 685-699:`oc = {on, panX, panY, zoom, faces, spaces, stack, focus, bmap, card, pan, rect, poly, drawTool, edit}`、`ocSeq`
- undo/redo 無前端堆疊:615-627 送 `line undo/redo`

### B.3 事件綁定
`#cv` pointermove/down/up/cancel/wheel(228-286)→ canvasMove/Down/Up;`#tool` change 592;`#workSurf` change 600;`#btnExport` 604(dump→Blob);window keydown 615(Ctrl+Z/Y、Esc);`#cmd` keydown 647;`#btnClear` 654;`#btnEx`/`#btnScene` 658/665;`#btnOpen`/`#file` 666/667(POST /upload);`#btnZoom` 675;window resize 676;`#ocv` pointerdown/move/up/wheel(1026-1117);`#btnObj` 1130;`#btnBack` 1143;`#btnNewRect/Poly` 1144/1148;`#btnNewSpace` 1152;`#btnHole2` 1163。

### B.4 三視圖排版與 STYLE
`layout.views[v].{tx,ty,bounds}` 在 `screenToView`(133,實際讀取於 138)與 `previewIn`(379)使用;`fit()` 117 只用 `layout.w/h`;`replay()` 156 重放 ops 到 `#world`。
STYLE(82-95):0 FRAME、1 TITLE、2 SURFACE、3 EDGE、4 EDGE_FREE(虛線)、5 HOLE、6 LABEL、7 GUIDE(紅虛線)、8 GUIDE_LABEL、9 TIMBER_FACE、10 TIMBER_FACE_NEAR、11 TIMBER_LABEL、12 HOVER。

### B.5 物件畫布資料流
`renderObjects()` 774-798:`objects` → 無座標者送 `line canvas-pos …`(791)→ 面卡另呼叫 `boundary <id>`(793-796)。卡片放開:`line canvas-pos ${kind} ${id} ${x} ${y}`(1077)。`enterFocus` 807-822:`boundary` → `oc.bmap`;`oc.edit={bid,work,drag}`;拖動用 `bhit`(900);放開 `emitBoundary()`(411-419)。
既有可重用邏輯:`emitLine` 400、`emitNewSurface` 415、`emitBoundary` 428、`refreshSurfaces` 438、`enterEdit` 459、`applyVertexEdit` 487、`applyEdgeEdit` 496、`faceCard` 728、`spaceCard` 756、`enterFocus` 834、`leaveFocus` 869、`drawFaceEditor` 878、`faceEditDown/Move/Up` 899/920/941、`objDrawDown` 978、`objEmitFace` 1004、`drawPolyPreview` 1015、`drawRectPreview` 1110。

### B.6 測試
- `canvas_test.js`:純 bridge,不碰 DOM;`check()` 計數,exit code 反映結果(232-233);`node canvas_test.js direct` 直接 spawn bridge。
- `cdp_test.js`:Chrome 路徑寫死(3),port 9333(4,7),profile `C:\tmp\cdp-profile`(8),導向 `http://localhost:8765/`(60);**固定 exit 0**(277),只印 ✓/✗。

### B.7 cdp_test.js 依賴清單
- DOM:`#world` childElementCount、`#ocv/#cv` hidden(69-71, 273-275);`#btnObj` rect(75,79);`#topbar/#cv/#ocv` rect;`elementFromPoint(640,350)` 等硬編(80,128);`.ocard`(83,93,96-97,114,117-118,144,148,164);`getElementById("btnNewRect"/"btnNewSpace"/"btnNewPoly"/"btnObj").click()`(108,124,205,228,271);`#status.textContent` 中文比對(143,175,194,209,245,257,262)。
- 全域:`oc.*`、`api()`、`leaveFocus()`(63-65,210,224,258,261 等);測試自注入 `window.__pd`(124-126)。

---

## 附錄 C:原型(prototype-構形Canvas-v2.html)結構與取捨

### C.1 DOM 骨架(738-1020)
```
738  #app.app-shell
739   header.topbar(brand / tool-group / top-actions:#undoButton #redoButton #searchInput #fitButton #exportButton #importButton #importFileInput #createButton)
787   main.workspace
788    aside.sidebar-left
790     .create-section(#newObjectIconButton + .quick-create-grid)
804     .filter-section(#showAllTypesButton, [data-filter-type]×2, #faceCount, #spaceCount)
812     .object-tree-section(#objectCountBadge, #objectList)
820     .canvas-options-section(#snapToggle, #gridToggle, #loadDemoButton, #newProjectButton)
829    section#canvasViewport
830     #canvasWorld > svg#edgeLayer(defs>marker#arrowhead, g#edgeGroup) + div#nodeLayer
842     #emptyState + #emptyCreateButton
851     #connectionHint(丟)
857     .canvas-controls(#zoomOutButton #zoomLevelButton #zoomInButton #homeButton)
866     .minimap-shell > canvas#minimap
872    aside.sidebar-right(#inspectorEmpty / #inspectorContent)
883   footer.statusbar(#toolStatus #selectionStatus #saveStatus #summaryStatus)
896  section#objectWorkspace[hidden]
897   header.object-workspace-topbar(#workspaceBackButton #workspaceBackLabel #workspaceTypeIcon #workspaceEyebrow #workspaceTitle)
911   nav#faceWorkspaceTools + #faceUndoButton #faceRedoButton
923   #workspaceFitButton #workspaceDoneButton
927   main#objectWorkspaceContent(動態注入)
930   footer.object-workspace-statusbar(#workspaceToolStatus #workspaceSelectionStatus #workspaceCoordinateStatus #workspaceZoomStatus)
935  #modalBackdrop;936 #objectDialog;975 #viewDialog;986 #relationDialog(丟);1015 #toastRegion
```
取捨:`#connectionHint`、`#relationDialog`、`#saveStatus`、`#loadDemoButton`、`#newProjectButton`、`#importButton`(改成開啟 .scene)丟;**`#nodeLayer` 不建**:卡片與連線全部畫在既有 `#ocv > #oroot` SVG 內(C4),`#edgeLayer` 也不建(連線畫進同一個 SVG 的一個 `<g id="edgeGroup">`);HTML 覆蓋物(空狀態、縮放控制、minimap)用 absolute 定位直接放在 `#canvasViewport` 內。

### C.2 CSS 分群(8-735)
| 群 | 行 | 依賴子元素順序的 grid |
|---|---|---|
| root/reset | 9-53 | — |
| topbar | 55-97 | `.app-shell`(55) |
| sidebar / quick-create / filter / object-list | 99-152 | `.workspace`(99) `.filter-row`(119) `.object-row`(128) |
| canvas-viewport / node 卡片 | 154-225 | `.node-footer`(195) |
| inspector | 227-271 | `.property-row`(245) `.relation-row`(250) |
| dialog | 273-336 | `.type-choice`(285) `.relation-endpoints`(328) |
| toast | 337-341 | — |
| RWD | 343-372 | 1160/900/680px |
| object-workspace 殼 | 375-465 | `.object-workspace`(382) `.object-workspace-topbar`(389) |
| face-workspace-layout / inner-panel | 465-545 | `.face-workspace-layout`(469) |
| face-editor-viewport / svg | 547-629 | — |
| face-inspector / selection-card | 630-657 | — |
| space-workspace-layout | 659-699 | (663)(672) |
| RWD(workspace) | 701-735 | — |

### C.3 JS 三層分類
**(a) 純畫面/純函式 → 直接搬(改 mm)**:icon 1091, hydrateIcons 1096, uid 1200, escapeHtml 1217, safeNumber 1226, clamp 1231, round 1235, formatLength 1240, formatArea 1245, formatVolume 1249, shortId 1253, polygonBounds 1316, polygonArea 1331, polygonPerimeter 1342, signedPolygonArea 1353, isAxisAlignedRectangle 1364, previewFaceSvg 1810, previewSpaceSvg 1871, previewSvg 1920, objectMetrics 1928, objectProperties 1951, renderNodeBody 1984, edgeNodesForRelation 2032, nodeAnchor 2044, relationGeometry 2054, propertiesMarkup 2126, boundaryListMarkup 2147, viewportCenterWorld 2271, facePointerToWorld 2961, snapFacePoint 2972, renderFaceInspector 2777, renderSpaceWorkspace 2931, toast 3784。
(丟:nowIso, deepClone, createRectangleBoundary, defaultFaceEditorState, normalizeFacePoint/Element, ensureFaceData, updateFaceDerived, setFaceBoundaryRectangle, faceElementById, elementTypeLabel, typeMeta/relationMeta 改為 face/space 兩型, createDomainObject, createCanvasNode, boundaryDefinitions, dynamicFieldsMarkup/setTypeChoice/renderDynamicFields/selectedObjectTypeFromForm/formObjectData。)

**(b) 綁 state → 搬骨架、改吃 snap/oc**:selectNode 1770, selectObject 1784, clearSelection 1799, renderNodes 2000, renderEdges 2073, renderObjectList 2091, relationListMarkup 2131(只畫 contains/boundedBy), renderInspector 2158, renderStatus 2199, updateWorldTransform 2210, renderToolState 2227, renderEmptyState 2244, renderAll 2248, viewportToWorld 2263, setCameraScale 2276, centerOnNode 2291, fitAll 2300, snapValue 2326, findFreeNodePosition 2332, currentWorkspaceObject 2485, faceToolLabel 2489, faceToolHint 2499, setFaceTool 2509, renderObjectWorkspace 2570, faceWorkspaceShell 2591, renderFaceWorkspace 2639, renderFaceLayerList 2674, faceSelectionDescription 2703, renderFaceEditorSvg 2820, setFaceCameraScale 2978, fitFaceEditor 2998, drawMinimap 3714, openDialog/closeDialogs 3448-3470。

**(c) 資料/持久化/歷史 → 整段丟**:createBoundaryFaces 1501, syncBoundaryFaces 1541, createDemoState 1559, createEmptyState 1586, normalizeState 1599, loadState 1648, hasStoredState 1661, captureModel 1669, restoreModel 1679, pushHistory 1689, commit 1696, undo 1704, redo 1714, updateHistoryButtons 1724, markDirty 1729, saveNow 1735, addViewForObject 2365, removeView 2382, deleteObject 2398, duplicateObject 2423, pushFaceDragHistory 3015, beginFaceGeometryDrag 3022, insertFaceVertex 3038, deleteFaceSelection 3054, renameWorkspaceObject 3083, renameFaceSelection 3096, openCreateObject 3520, submitObjectForm 3564, submitRelationForm 3662, deleteRelation 3694, toggleNodeMode 3703, exportProject 3792, importProject 3808, loadDemo 3833, newProject 3846。

### C.4 事件層與快捷鍵(3150-4269)
- 主畫布 `handleKeyboard` 4038-4096;工作區 `handleWorkspaceKeyboard` 3410-3445(表見 §5.8,已裁剪)。
- 面內編輯器:hit 測試靠 `data-face-hit` 屬性 + `closest()`(3170),值域 `canvas/boundary/edge/vertex/line/line-endpoint/opening/opening-handle`;邊有加粗熱區 `.face-edge-hit`(2861-2862);手柄半徑隨 `camera.scale` 反向縮放(2840-2842);grid 用 SVG `<pattern>`(2911-2916);camera `{x,y,scale}` 預設 `{120,90,1}`,scale clamp 0.08-8(2988)。
- 原型 referenceLine `{x1,y1,x2,y2}` 無方向欄位、opening `{x,y,width,height}`:對映到核心時,referenceLine 改為 `{id, axis:u|v, offset}`,opening 改為孔環 4 點。
- 物件清單:`handleObjectListClick` 3986-4003;篩選 4133-4150;空狀態 2244(以卡片數判定)。
