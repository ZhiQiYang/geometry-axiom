# #123 七項實測證據索引（Agent A）

> 性質：只整理**既有**證據，未重跑任何測試、未開瀏覽器、未啟動服務。
> 被測 main SHA：`d6b4b450d741fcbbfd75c51631915d3082926990`（README:10）。
> 證據位置：PR #138（草稿）分支 `docs/issue123-seven-evidence-20261005`，HEAD `b32cdb5`。
> 下表所有路徑都相對於該分支的 `geometry-web/docs/issue123-evidence/`（簡稱 `EV/`）。尚未合入 main，worktree 為 `D:/geometry-axiom-123ev`。
> 私人設計 ZIP 只以項目 ID 引用，本文件無其原文、截圖。

## 一、逐項表

JSON 鍵路徑格式：`檔案 : 鍵/鍵/…`。視窗鍵 `1382x804`、`390x844` 等為字面鍵名。

### X6 縮放列位置與內容各畫布不同——結論：重現

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | 主畫布縮放列右下 (1042,714) 322×44，按鈕 32px：`stage_x1.json : main/1382x804/.canvas-controls`、`…/#zoomOutButton/h`；390px 時按鈕 44×44：`main/390x844/#zoomOutButton`。面內縮放列左下 (274,720) 340×38，按鈕 30px：`face/1382x804/.face-canvas-controls`、`…/#feZoomOut`。三視圖縮放列左下 (214,721)，按鈕 29×29，**390px 仍 29×29**：`v3/1382x804/#v3ZoomOut`、`v3/390x844/#v3ZoomOut`。網格縮放列右下 (674,746)，按鈕 34px：`stage_g.json : ig_zoom/1382x804/.ig-zoombar`、`…/#igZoomOut`；讀數 `ig_zoom/1382x804/zoomText`=「1 格 600×400 mm · 134 px」。三視圖開啟時主畫布控制列 `display:none`：`stage_x1.json : v3/1382x804/mainControlsDisplay`。 |
| 390px 網格縮放列 | 縮放列 y=1876–1928，`.ig-canvas` y=1604–1944（初始視口 844 之外，需 dialog 內捲動）：`stage_g.json : ig_zoom/390x844/.ig-zoombar`、`…/.ig-canvas`；`.ig-hint` hidden：`ig_zoom/390x844/.ig-hint/hidden`。 |
| 截圖（PR #138 分支） | `EV/screenshots/X6-main-1382x804.png`、`X6-v3-1382x804.png`、`X6-grid-1382x804.png`、`X6-grid-390x844.png`、`X6-B6-face-390x844-firstvisit.png` |
| 重現腳本 | `EV/repro/stage_x1.py`（主畫布／面內／三視圖）、`EV/repro/stage_g.py`（網格）；`EV/repro/css-evidence.mjs` |
| 文字結論 | `EV/README.md:25`（總表）、`:37-53`（細節） |
| 未驗／受阻 | 3D 建模「無縮放列」只是未發現（README:46 表列）；未做觸控與實機。面內座標讀數 390px 隱藏：`stage_x1.json : face/390x844/#faceCoordinateReadout/hidden`。 |
| 證據強度 | **數值**（getBoundingClientRect 座標、computed 尺寸）。 |

### B6 選取摘要——結論：部分重現（面內首次進入遮擋成立；與主畫布不一致的面向 JSON 不支持）

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | 面內 `#feSelectionSummary`：首次進入 0 選，可見 296×62 @ (272,128)，佔視窗 3.5%：`stage_x1.json : face/b6_first_visit_1382/{hidden,x,y,w,h,coversPctOfViewport,text}`（另在 `stage_h.json : first_visit`）。按「知道了」後 0 選 `hidden=true`：`stage_x1.json : face/b6_after_dismiss_0sel/hidden`、`stage_h.json : after_dismiss`。1 選：`face/b6_1sel/{w,h,text}`。3 選 288×62：`stage_h.json : multi_sel/{count,w,h,text}`。390px 首次 280×60 @ (8,130)，6.3%：`stage_x1.json : face/390x844/summary`。主畫布 `#ocSelectionSummary` 對照：**README:70 的數字與 JSON 對不上**。README 稱 0 選 `hidden`、1 選 `rendered=false`；`stage_g.json : oc_0sel` 實為 `hidden:false, rendered:true, count:0`，`oc_1sel` 實為 `hidden:false, rendered:true, count:1`（文字含「清除選取」「知道了」）。因此「兩畫布 1 選行為不一致」這一面向，以 JSON 看**不成立**（兩者 1 選皆可見），README:26、:70 該句不可採信，需重測。 |
| 「遮住尺寸標註」 | README:63 稱遮住面左上 4000 標註與外環上緣。**JSON 只有摘要卡自己的矩形，沒有量測標註（4000）的矩形或兩者交集**；此結論僅憑截圖目視：`EV/screenshots/X6-B6-face-1382x804-firstvisit.png`。 |
| 截圖（PR #138 分支） | `EV/screenshots/X6-B6-face-1382x804-firstvisit.png`、`X6-B6-face-390x844-firstvisit.png`、`B6-face-1sel-1382.png`、`B6-face-multisel-1382.png`、`B6-face-after-dismiss-1382.png` |
| 重現腳本 | `EV/repro/stage_x1.py`、`EV/repro/stage_h.py`；CSS 規則解析 `EV/measurements/css-evidence.out`（段名 `### B6 selection-summary visibility rules`，約 :217） |
| 文字結論 | `EV/README.md:26`、`:55-70` |
| 未驗／受阻 | 框選拖曳中的摘要狀態未測（README:68、:138）。390px 下是否遮住標註未判斷（無標註矩形）。 |
| 證據強度 | 摘要卡大小、位置、顯示規則＝**數值**；「遮住標註」＝**僅截圖目測**。 |

### G3 檢查器刪除鈕——結論：重現（樣式與間距）；點擊後確認未驗

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | `#gridObjectDelete` 46×30，色 `rgb(120,134,154)`、透明底、透明邊、12px、字重 650：`stage_g.json : gi/1382x804/deleteStyle/{color,bg,border,fs,fw}`。與鄰鈕間距 8px：`gi/1382x804/deleteStyle/parentGap`（390px 為 6px、高 36：`gi/390x844/deleteStyle/parentGap`、`gi/390x844/#gridObjectDelete`）。三鈕座標：`gi/1382x804/#gridObjectOpen`、`#gridObjectNewBinding`、`#gridObjectDelete`。Hover：`gi_delete_hover` = `rgb(189,75,80)` / `rgb(255,241,241)`。 |
| 對比 3.7:1 | README:86 註明為**自算**（sRGB 公式），非工具量測；JSON 中無此值。 |
| 截圖（PR #138 分支） | `EV/screenshots/G3-inspector-1382x804.png`、`G3-inspector-390x844.png` |
| 重現腳本 | `EV/repro/stage_g.py`；`EV/measurements/css-evidence.out` 段 `### G3 gi-delete / gi-actions`（約 :202） |
| 文字結論 | `EV/README.md:27`、`:72-87` |
| 未驗／受阻 | 按下刪除後是否跳確認：**未點擊**（README:87、:139）。`gi_delete_keyboard` 為 null，鍵盤焦點樣式未取得。 |
| 證據強度 | 位置、間距、computed color＝**數值**；對比比值＝**自算**。 |

### G4 網格用語三處不一——結論：部分重現

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | 完整工作區配置模式：`cell` 4 次、`對齊位置` 1、`對齊頂點` 1：`stage_g.json : g4_workspace_binding_text/counts`（`/lines` 為實際文字）。檢查器來源模式：`g4_inspector_source_text/{counts,lines}`（`主支` 1、`網格來源` 1）。面內構件頁：`stage_h.json : g4_face_grid_pane/{counts,lines,activeTab}`（`主支` 7、`副支` 2、`主網格` 1、`子網格` 2）。 |
| 截圖（PR #138 分支） | `EV/screenshots/G4-binding-workspace-1382.png`、`G4-face-grid-pane-1382.png`、`G-impact-dialog-1382.png` |
| 重現腳本 | `EV/repro/stage_g.py`、`EV/repro/stage_h.py` |
| 文字結論 | `EV/README.md:28`、`:89-98`；E1 更正 `:100-102` |
| 未驗／受阻 | **檢查器配置模式（已建綁定後）未渲染**（README:98、:137），其字串只有 `grid-inspector.js` 靜態原始碼，不算畫面證據。`stage_g.json : exception` 記錄第 3 次執行末段「雙擊面卡進面內」逾時，面內文字改由 stage_h 取得。 |
| 證據強度 | 渲染文字計數＝**文字量測**（非搜原始碼）；「三處不一致」的判斷是人讀文字比較。 |

### F1 3D 歡迎畫面溢出／重疊——結論：重現（但 CTA 未被遮擋）

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | 1382×804：`#smWelcome` scrollH 237 > clientH 177：`stage_f.json : 1382x804/measure/welcomeScroll`；預覽區高 176.5：`…/measure/els/.sm-canvas-wrap/h`。堆疊 .sm-header y64 h65、.sm-source-actions h62、.sm-steps h72.2、.sm-stage 起於 y263.2：`…/measure/els/{.sm-header,.sm-source-actions,.sm-steps,.sm-stage}`。重疊清單：`…/measure/overlaps`（`#smWelcomeTry × .sm-view-tools`、`#smWelcome .sm-wire-cube × .sm-stage-head` 等）。900×804：scrollH 211 / clientH 130、重疊 4 筆：`stage_f.json : 900x804/measure/{welcomeScroll,overlaps}`。390×844：177/130：`390x844/measure/welcomeScroll`。CTA hit-test（四點皆回 `smWelcomeTry`、與視角分段水平不交會）：`stage_f2_explore2.json : f1_hit/{probes,overlaps,segmentRects,tryRect}`。 |
| 截圖（PR #138 分支） | `EV/screenshots/F-3d-welcome-1382x804.png`、`F-3d-welcome-1161x804.png`、`F-3d-welcome-900x804.png`、`F-3d-welcome-390x844.png` |
| 重現腳本 | `EV/repro/stage_f.py`、`EV/repro/stage_f2_explore2.py`、`EV/repro/explore1.py` |
| 文字結論 | `EV/README.md:29`、`:104-113` |
| 未驗／受阻 | 1161×804 的數值在 `stage_f.json : 1161x804/measure`，README 未逐項列。`mediaCompact` 全為 false（未觸發 900px 精簡斷點）。headless Chromium，未做真機／觸控。 |
| 證據強度 | **數值**（DOM 矩形、scroll 尺寸、`elementFromPoint`）。 |

### F5 3D 控制項樣式不一致——結論：重現

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | 1382×804 控制項清單 `stage_f.json : 1382x804/controls[]`（欄位 `id,h,br,bg,accent,fs`）：頂部保存按鈕 `controls[1].bg`=`rgb(54,91,245)`；`smWelcomeTry`、`smCreate` `bg`=`rgb(56,85,188)`（兩種藍）；`smShowSpace/smShowWalls/smShowTimbers/smShowRoof/smWallsEnabled/smIncludeTimbers` `accent`=`rgb(8,127,131)`（teal）；圓角 8（按鈕）／5（視角分段）／6（表單欄位）；按鈕高皆 44。焦點框：`stage_f.json : focusOutlineWelcomeTry`（3px solid rgb(139,157,236)、offset 3px）。Tab 巡覽：`tabOrder1382[]`。 |
| 註記 | README:117 寫的鍵名 `styles`、`tab` 與 JSON 實際鍵名不符；實際為 `controls`、`tabOrder1382`。README:124 稱面內工具列焦點框為 2px，本批 JSON 中**沒有**面內焦點框的量測值，該句無檔案內證據。 |
| 截圖（PR #138 分支） | 無專屬截圖；可參 `EV/screenshots/F-3d-welcome-1382x804.png` |
| 重現腳本 | `EV/repro/stage_f.py`；`EV/measurements/css-evidence.out` 段 `### F5 .sm-button / primary / checkbox / focus`（約 :105） |
| 文字結論 | `EV/README.md:30`、`:115-125` |
| 未驗／受阻 | 與「其他工作區」的對照值（面內／主畫布主色與焦點框）未在本批 JSON 內，需另查。 |
| 證據強度 | **數值**（computed style）。 |

### F6 3D 說明文字——結論：重現（字級）；「單段超過 100 字」僅區塊合計成立

| 欄 | 內容 |
|---|---|
| 被測 SHA | d6b4b450 |
| 關鍵量測值 | `stage_f.json : 1382x804/help[]`（欄位 `sel,fs,lh,color,chars,lines`）。`.sm-help` 共 8 筆，皆 11px（例 `help[0]`、`help[1]`：86 字／3 行）；`.sm-guide` 區塊 `help[8]`：220 字／4 行；`.sm-guide p` `help[9]`：80 字；`.sm-view-direction` `help[13]`：11px。整個 `help[]` 另含 `.sm-section p`、`.sm-metrics small`、`.sm-steps small` 等也是 11px；`.sm-source-summary` 為 12px（`help[14]`）。 |
| 註記 | README:131 引用的顏色（`.sm-help` `rgb(75,93,124)`、`.sm-guide` `rgb(88,105,135)`）與 JSON 值不符：JSON 為 `.sm-help` `rgb(82,101,121)`、`.sm-guide` `rgb(82,106,133)`；README:133 的對比 5.9:1／5.3:1 為自算，依 README 顏色得出，可能需重算。 |
| 截圖（PR #138 分支） | 無專屬截圖 |
| 重現腳本 | `EV/repro/stage_f.py`；`EV/measurements/css-evidence.out` 段 `### F6 .sm-help / .sm-guide font-size & line-height`（約 :125） |
| 文字結論 | `EV/README.md:31`、`:127-133` |
| 未驗／受阻 | 讀者實際可讀性（非字級）未評；對比比值為自算。 |
| 證據強度 | 字級、行高、字數＝**數值**；對比＝**自算且與 JSON 顏色對不上**。 |

## 二、證據強度總覽

| 項 | 數值（JSON） | 僅截圖目測 | 自算／文字推導 |
|---|---|---|---|
| X6 | 位置、尺寸、顯示狀態 | — | — |
| B6 | 摘要卡位置／大小／顯隱／文字 | 「遮住 4000 標註」 | — |
| G3 | 間距、computed color／尺寸、hover 色 | — | 對比 3.7:1 |
| G4 | 渲染文字與詞頻 | — | 「三處不一」的判斷屬人讀 |
| F1 | scroll 尺寸、矩形、重疊清單、hit-test | — | — |
| F5 | computed 高、圓角、顏色、accent、焦點框 | — | — |
| F6 | 字級、行高、字數 | — | 對比比值 |

## 三、與 #123 相關的其他既有證據（只摘相關部分）

- **PR #131（已合併）建立回饋浮層**：`D:/geometry-axiom/geometry-web/docs/issue123-feedback-overlay/README.md`（結果表約 :17-27）、`before-results.json`／`after-results.json`。範圍僅「390px Create → 網格系統」被回饋啟動鈕遮擋，README 自述「不證明整個 #123」。**不對應 43 項中的任何 ID**（issue 正文把它當子項）。修前 4 例失敗、修後 138/0 通過。
- **PR #139 QA 報告**：`D:/geometry-axiom-qa-report/geometry-web/docs/evidence/qa-acceptance-d6b4b45-20261005/README.md`。與 #123 相關者：`T2-06` 的「390 空白專案提示卡被工具列蓋」（README:67、:188）與 #123 相鄰（:257），但不是 43 項 ID。`findings/known-issues.md:57` 稱 #123「43 項需對現行逐項複核，非確證缺陷」。其 390px 模擬非真機（README:17）。

## 四、整理者最不確定的地方

1. B6「遮住尺寸」只有截圖目視，JSON 沒有標註矩形。
2. B6 主畫布對照（README:70）與 `stage_g.json : oc_0sel/oc_1sel` 矛盾；F6／F5 兩處 README 與 JSON 不一致（F6 顏色值、F5 鍵名、F5 面內焦點框 2px 無檔案依據）。
3. 這批全在 headless Chromium＋主機 CPU 約 94% 下取得（README:17、RUN-LOG:3-6），尺寸屬版面事實不受影響，但「等待逾時」類現象不能當產品缺陷。
