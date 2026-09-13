# geometry-web UI/UX 審查 → 規格摘要（可貼進 UI-REDESIGN-PLAN.md §5 之後）

> 2026-09-14 審查產出。完整問題清單與畫面對照見 `UI-UX 審查報告.dc.html`；修正稿 `建議-主畫布 v2.dc.html`、`建議-面內工作區 v2.dc.html`。
> 原則：保留 DOM-CONTRACT 既有 id/class，只改層級與樣式；新增元素用新 id 並補進 DOM-CONTRACT.md。C 端零改動。

## S1 全域 token（app.css :root）

| 項目 | 現況 | 規格 |
|---|---|---|
| 內文字級 | 14px body，元件 8–11px | body 13px；元件最小 **11px**；標題 12.5–15px |
| 次要字色 | `--muted #6b7485`、`--faint #98a1b2` | 文字只用 muted（4.9:1）；faint 僅裝飾線、停用態 |
| 互動熱區 | 17–26px | 最小 **28×28px**（圖示鈕 30–34、列高 ≥38） |
| 列高 | topbar 58 / statusbar 28 | topbar 56 / **statusbar 32** / workspace topbar 56 |
| 欄寬 | 左 242 / 右 326；面內 236 / 314 | 左 **260** / 右 **320**；面內 240 / 320 |
| 圖示 | 主畫布 SVG、工作區 Unicode | 一律 `ICON_PATHS` SVG；補 `guide/hole/notch/timber/redraw/column/beam` |
| 卡片字級 | 11.5 / 9 / 8.5 / 8 | 12.5 / 10.5 / 11 / 10.5；zoom < 0.75 切 compact（只留標題列） |

## S2 主畫布（§5.4 修訂）

**頂列**（修 A1）
- 左：brand ＋ 場景下拉（`#sceneList` 改為按鈕觸發的選單，含「開啟…」「載入範例」）。
- 中：工具群 4 顆，每顆 icon＋文字＋`<kbd>`（V / H / R / P）。
- 右固定 5 件：`#btnUndo` `#btnRedo` ｜ segmented「物件畫布｜三視圖」（`#btnObj` 保留 id 於三視圖鍵） ｜ 「檔案 ▾」（`#btnOpen` `#btnScene` `#btnEx` 收進選單） ｜ `#btnExport` 主鈕。`#btnZoom` 移到畫布縮放列。
- 右群寬度上限 ≈ 420px；1160px 以下工具群收成 icon-only，但**任何寬度不得覆蓋**中群。

**左欄**（修 A2 A3 F2）
1. `#searchInput` 移到最上（34px，placeholder「搜尋物件（名稱或 id）」）。
2. 物件庫：3×2 icon 鈕 56px 高，單行標籤；**六面盒放第一格**。保留 `#btnNewRect #btnNewPoly #btnNewSpace #btnBox6 #btnNewColumn #btnNewBeam`。
3. 篩選：單列 chips `[data-filter-type]`（`aria-pressed`），含計數 `#faceCount` 等；右側「全部顯示」。
4. 清單 `#objectList` `flex:1`；列 = `.row-icon.{face|space|column|beam}` ＋ `.row-copy > strong(12.5/600) + small(11 muted)` ＋ 游離徽章。**app.js:3016 改為 `.row-copy`**。
5. 「格線吸附／顯示格線」移到畫布縮放列（`#snapToggle` `#gridToggle` 保留 id，改 `aria-pressed` 按鈕）。

**畫布**（修 A4 A5 A6 A8 A10）
- 卡片：OC 200×156、SP 240×196；標題列 40px（型別點＋名稱 12.5＋副標 10.5＋狀態膠囊 10.5 可點）；footer 11px。
- 面卡副標：已放置 → 「已放置 · 天花 z=2500」（由 surfaces u×v 推法向）；游離 → 「尚未放置」＋膠囊「游離」（點擊＝選取並捲到檢視器放置區）。
- 空間卡六槽：天花／地板／前牆／後牆／左牆／右牆（副標 ±Z…）；footer「開放 · 缺 天花、左牆」。
- 連線：包含＝實線 `#929bad`；障礙＝虛線 `6 4` `#b1894f`；標籤 11px 膠囊，文字「包含」「障礙」。保留 `.edge-path .edge-label .edge-group-item`。
- 左下縮放列：− 100% ＋ ｜ fit 原點 ｜ 吸附 格線。右下小地圖 150×96，可收合。

**右欄檢視器**（修 A7 F1）
- 頂部：型別圖示＋「面 2」＋副標（邊界面 · 尺寸 · 頂點）＋狀態膠囊。
- 流程條（boundary 面才顯示）：`1 建面 ✓ → 2 放置 → 3 收進空間`，依 `placed` 與是否為 space 成員決定進度；游離時顯示一段限制說明。
- 放置區：6 預設 3×2 radio 卡（`[data-place-preset]`）→ 填 `#placeU #placeV`；origin 三欄；**u⊥v 即時驗證**，通過時顯示「u ⊥ v · 法向 +Z（天花）」，不通過禁用主鈕；主鈕 `#placeSubmit` 文案「放置這片面」／已放置「重綁」。
- 屬性 dl：id、範圍（u,v）、外環、孔、所屬空間；bbox 用「0–4000 × 0–3000」格式。
- 底部動作：`#inspEnter` `#inspLocate` 並排，`#inspDelete` 全寬危險樣式，文案含「可 Ctrl+Z 復原」。空間另有 `#inspMembers` 主鈕「＋收成員」。

**狀態列**（修 A9）
- 32px / 11.5px。左：目前工具（icon＋名）｜context hint。右：物件摘要「16 物件 · 1 空間開放 · 2 游離」｜`#cmd`（mono、`›` 前綴、↑↓ 歷史、`:` 聚焦）。
- `#status` 保留（測試比對），但成功訊息同時發短暫 toast（成功色 `--face`），錯誤維持 toast.error。`#btnEx #btnClear` 收進「檔案 ▾」。

## S3 面內工作區（§5.5 修訂）

- **頂列**：返回鈕「← 物件畫布」；麵包屑「空間 1 / ● 面 3」＋放置膠囊（「天花 · z=2500」或「游離」）；工具群 icon＋文字＋kbd（V L R I T E ｜ H）；右：undo redo ｜ `#faceShapeButton`「形狀庫」｜ `#workspaceDoneButton`「完成」。移除 `#faceCanvasHint` 常駐浮條（只在多步工具出現）。
- **左欄** `#faceLayerList` 分組：邊界（外環、孔）／參考線／角材／網格／柱樑投影（尚未套用）。列 38px：圖示 26 ＋ strong 12 ＋ small 11 ＋ 刪除 icon 鈕 28px（hover 顯示）。投影群組底部灰底卡：`#feCutStrip` ＋ `#feApplyProj` 主鈕「套用 N 項投影」＋ 一句說明。移除 `.fe-ob-ctrl` 的 `#b48` 虛線與 `.mini-btn`。
- **畫布**：格距依 zoom 選（螢幕間距 ≥24px，序列 10/25/50/100/250/500/1000），主格線每 4 格；吸附格距 `#faceGridSizeSelect` 獨立於顯示格距。邊中點標長度（11.5px 白底）、參考線末端標 `u = 1500`、原點標 `0,0 · u→ v↓`。左下縮放列（− % ＋ fit ｜ 吸附 格線 格距）；右下讀數 `u 1850  v 600  mm` 11.5px。
- **右欄** tabs：屬性｜角材｜網格。
  - 屬性：dl（id、尺寸、面積（扣孔）、外環/孔、所屬空間）；「外環邊」表：索引徽章＋方向文字、長度欄（統一樣式＋mm）、F/X segmented（`[data-fix-edge]` `.fixity-btn` 保留）；「放置」摘要卡 3 欄＋「重綁…」；「投影視圖」摺疊列顯示預設視圖名。
  - 角材：`#tbLen #tbA #tbB #tbDir #tbSide`；網格：`#gridU #gridV #gridCreate`。游離面時兩頁顯示停用說明。
- **狀態列** 32px：左 工具＋hint；右 常用 kbd（L 參考線 R 開口 Esc 返回）。

## S4 空間工作區（§5.6 修訂）

- 中央改 Tab「平面示意｜三視圖」佔滿高度；移除 `#spaceFaceGrid` 卡片格（左欄成員列 hover 顯示縮圖，點擊 `enterFocus`）。
- 平面示意工具：柱／樑尺寸 chip 下拉；「點放柱 · 拖放樑」改 tooltip／首次浮條。`#planColSize #planBeamSize` 保留。
- 構件列：動作鈕 hover 顯示（移出／收進，28px）；刪除統一 toast＋Ctrl+Z，不用 `confirm()`。
- 右欄槽位：面名稱＋軸向副標；空槽顯示「＋放置一片面到這裡」（帶入對應預設開放置）。移除 `#spProjRefresh`，mutate 成功後自動 `renderSpaceProjection()`。

## S5 三視圖總覽（D1 修訂）

- 開啟時左欄改「視圖（正面／側面／仰視 勾選）＋圖層（面／參考線／角材／柱樑）」，右欄顯示 pick 結果與 hover 描述（`#hovertxt` 移入）。
- `#tool #workSurf #newZ` 改 segmented ＋ 下拉，樣式同工具群；加左下縮放列。
- TITLE／LABEL 文字改 HTML 疊字或依 zoom 反比縮放。

## S6 測試同步（DOM-CONTRACT）

- 新增：`#fileMenu`（檔案 ▾）、`#viewSwitch`（物件畫布｜三視圖 segmented，`#btnObj` 保留為其中一鍵）、`#placeFlow`（流程條）、`#placeValid`（u⊥v 驗證文字）、`#faceInspectorTabs [data-fi-tab]`、`#spaceStageTabs [data-ss-tab]`、`#feApplyCard`。
- 版面檢查點更新：topbar 56 / statusbar 32；左欄 260 / 右欄 320；`.top-actions` 右緣 ≤ viewport、左緣 > `.tool-group` 右緣（防溢出斷言）。
- `#status` 文案不變；成功 toast 加 `.toast.ok` 計數檢查。
