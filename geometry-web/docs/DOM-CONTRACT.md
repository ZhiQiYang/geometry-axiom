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
| `#btnObj` | 三視圖總覽開關(D1:開/關覆層) | `.click()`、rect |
| `#btnUndo` / `#btnRedo` | 復原/重做 | `.click()` |
| `#btnZoom` | 縮放重置/fit-all | `.click()` |
| `#btnNewRect` | ＋面·矩形 | `.click()` |
| `#btnNewPoly` | ＋面·多邊形 | `.click()` |
| `#btnNewSpace` | ＋空間 | `.click()` |
| `#btnBox6` | 快速六面盒(Phase 4 才接對話框) | 存在性 |
| `#btnBack` / `#crumb` / `#btnHole2` | focusBar 內控制 | `.click()`、textContent |
| `#objectList` | 左欄物件清單容器 | 子列計數 |
| `#objectCountBadge` / `#faceCount` / `#spaceCount` | 數量徽標 | textContent |
| `#inspectorContent` / `#inspectorEmpty` | 右欄檢視器 | `hidden` 切換檢查 |
| `#emptyState` | 空狀態插圖 | `hidden` 切換檢查 |
| `#snapToggle` / `#gridToggle` | 吸附/格線開關 | `checked` |
| `#zoomInButton` / `#zoomOutButton` / `#zoomLevelButton` / `#homeButton` | 縮放控制 | `.click()` |
| `#searchInput` | 搜尋框(過濾卡片與清單) | `input` 事件驅動 `oc.search` |
| `#minimap` | 小地圖 canvas | `pointerdown` 導航;`oc.mmTf` 座標換算 |
| `#toastRegion` | toast 容器 | 存在性 |

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

## Phase 1 版面檢查點(cdp_test §1,五項)

1. `#app` 三列:topbar 58px / workspace 1fr / statusbar 28px
2. `.workspace` 三欄:左 242px / 中 1fr / 右 326px
3. `.topbar` 子層序:brand → tool-group → top-actions
4. `#ocv` 在 `#canvasViewport` 內且同大小(誤差 ≤2px)
5. `#status`、`#cmd` 都在 `.statusbar` 裡;另存 `phase1.png` 截圖

## 變更程序

1. 改 DOM id / class / 全域名 → 先改本表 → 同步改 cdp_test.js / canvas_test.js → 跑裁判。
2. 新增測試依賴 → 補進本表對應小節。
