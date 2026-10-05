# issue #123 設計驗收 — 七項實測證據（X6、B6、G3、G4、F1、F5、F6）

> 目的：為 #123 設計驗收中先前僅有靜態證據的七項，補上**實際操作與量測**結果，供 dot 接手判斷。
> 本文件只描述量測到的事實；原稿的問題描述與建議不在此引用（原稿屬私人檔案，不進 repo）。

## 版本與環境

| 項目 | 值 |
|---|---|
| 程式碼 commit | `d6b4b450d741fcbbfd75c51631915d3082926990`（= 當時 `origin/main`） |
| 取得方式 | `git archive` 匯出至獨立 TEMP 目錄，未修改任何產品檔案 |
| 服務 runtime | `GET /runtime` 回報 `version=e2f2ee7baaf7…`、`fresh:true`、root 指向匯出目錄 |
| 服務 | `serve.py 8851`，BelowNormal 優先權，獨立 feedback/TEMP 目錄 |
| 瀏覽器 | Playwright Python + Chromium（headless），每階段使用全新 profile |
| 原生元件 | 唯讀沿用已驗證二進位（bridge 內容雜湊 `c5955d469b13`、model-base `079eda49f0df`），未重編 |
| 視窗 | 1382×804、1161×804、900×804、390×844 CSS px |
| 主機狀態 | 量測期間 CPU 約 94%、可用記憶體最低約 266 MB——**等待時間可能受負載影響，不列為產品缺陷**（見 RUN-LOG） |

所有操作都走真實 UI（點擊、填表、雙擊卡片、Tab 鍵），未注入內部狀態。場景透過「檔案 ▸ 範例 ▸ 載入預設場景範例」建立（內容：1 面、3 支角材；G 階段另經完整工作區建立 1 個網格來源）。

## 結果總表

| 項 | 量測標的 | 結論 |
|---|---|---|
| X6 | 各工作區縮放列的位置、內容、尺寸 | 重現：四個畫布的縮放列位置與內容各異；390px 下網格工作區縮放列需捲動才可見 |
| B6 | 面內 `#feSelectionSummary` 與主畫布 `#ocSelectionSummary` 的顯示行為 | 部分重現：首次進入的小卡會遮到畫面左上標註；按「知道了」後 0 選時隱藏；兩畫布在 1 選時行為不一致 |
| G3 | 網格檢查器 `#gridObjectDelete` 的樣式與位置 | 重現：與鄰鈕僅 8 px（390px 為 6 px），透明低對比樣式；是否跳確認未驗 |
| G4 | 網格相關用語在三個位置的一致性 | 部分重現：工作區配置模式出現 `cell`／`對齊位置`，與面內 `主支/副支/子網格` 詞彙不連續；檢查器配置模式未渲染（受阻） |
| F1 | 3D 建模歡迎畫面在四個視窗的溢出與重疊 | 重現：`scrollHeight` 超過 `clientHeight`、歡迎內容與下方工具帶重疊；但 CTA 未被遮擋（hit-test 通過） |
| F5 | 3D 建模控制項的樣式一致性 | 重現：同一畫面兩種藍色主按鈕、teal 勾選框、圓角 5/6/8 px 混用、焦點框規格與其他工作區不同 |
| F6 | 3D 建模說明文字的字級與可讀性 | 重現：`.sm-help`／`.sm-guide`／`.sm-view-direction` 皆 11 px；單段 >100 字僅 `.sm-guide` 區塊整體成立 |

「重現」= 在 `d6b4b450` 實際量到所述現象；「部分重現」= 部分面向成立；「受阻」= 需要但未完成的互動，見各節。

---

## X6 — 縮放列

`measurements/stage_x1.json`、`stage_g.json`；截圖 `screenshots/X6-*.png`。

| 畫布 | 位置（1382×804 實測） | 內容 | 按鈕高 |
|---|---|---|---|
| 主畫布 `.canvas-controls` | 右下 x1042–1364, y714–758 | − 百分比 ＋｜全圖｜回原點｜吸附｜格點 | 32 px（390px: 44） |
| 面內 `.face-canvas-controls` | 左下 x274–614, y720–758；座標讀數在右下 | − 百分比 ＋｜全圖｜吸附｜格點｜格距選擇 | 30 px（390px: 44） |
| 三視圖 `#v3ZoomBar` | 左下 x214–365, y721–758 | − 百分比 ＋｜全圖 | 29 px（**390px 仍 29 px**） |
| 網格 `.ig-zoombar` | 畫布右下 x674–1006, y746–788 | − 「1 格 600×400 mm · 134 px」＋｜回到基準 | 34 px |
| 3D 建模 | 無縮放列 | 僅視角分段含「置中」（x232–280） | — |

其他量測：
- 三視圖開啟時主畫布 `.canvas-controls` `display:none`（不疊放）。
- 390×844 下網格工作區 dialog 內 `.ig-canvas` 位於 y=1604–1944，縮放列在 y=1876–1928，**初始視口內不可見，需在 dialog 內捲動**；`.ig-hint` 在 ≤760px 隱藏（hidden=true 實測）。
- 面內 390px 下 `#faceCoordinateReadout` 隱藏（0 尺寸）。
- 面內頂部列 `.object-workspace-topbar` 在四個視窗皆為 116 px（390px 為 122 px）。

## B6 — 選取摘要

`measurements/stage_x1.json`、`stage_h.json`；截圖 `X6-B6-face-*-firstvisit.png`、`B6-face-*.png`。

面內 `#feSelectionSummary`（data-guidance-key `face:select`）：

| 狀態 | 1382×804 實測 | 備註 |
|---|---|---|
| 首次進入、0 選 | 可見，296×62 @ (272,128)，佔視窗 3.5% | 文字「從空白處拖曳，框選角材…」，**遮住面左上角的 4000 標註與外環上緣**（截圖可見） |
| 按「知道了」後、0 選 | `hidden=true`，不渲染 | 「平常常駐」只在首次成立；localStorage 記住已讀 |
| 選 1 支角材 | 233×62 @ (272,128)，「已選 1 支角材｜可在屬性欄查看或編輯。」 | 資料集 `count=1, dynamic=true` |
| 選 3 支角材（Shift 點選列表） | 288×62 @ (272,128)，「已選 3 支角材｜編輯或刪除時，請先點選單一物件。」 | 右欄同時顯示多選清單 |
| 390×844 首次 | 280×60 @ (8,130)，佔視窗 6.3% | — |
| 框選拖曳中 | **未測** | — |

主畫布 `#ocSelectionSummary` 對照（同場景）：0 選 `hidden`；1 選 `hidden=false` 但 `rendered=false`（被樣式隱藏）——與面內 1 選仍可見的**行為不一致**（實測，非推論）。

## G3 — 檢查器刪除鈕

`measurements/stage_g.json`；截圖 `G3-inspector-*.png`。

`#gridObjectDelete` 實測（選取網格系統卡後的 `#gridInlineInspector`）：

| 視窗 | `.gi-actions` 內順序 | 刪除鈕與前鈕間距 | 刪除鈕樣式 |
|---|---|---|---|
| 1382×804 | 完整工作區(82×30) → 建立配置(70×30) → **刪除(46×30)** | 8 px | color `rgb(120,134,154)`、透明底、透明邊、12 px、字重 650 |
| 1161×804 | 同 | 8 px | 同上 |
| 900×804 | 同 | 8 px | 同上 |
| 390×844 | 同（36 px 高） | 6 px | 同上 |

- Hover（真實滑鼠移入）：`rgb(189,75,80)` + 淡紅底 `rgb(255,241,241)`。
- 文字色對白底對比約 **3.7:1**（依 sRGB 公式自算，非工具量測）。
- **未驗**：點擊刪除後是否出現確認（未點擊，避免改動場景）。

## G4 — 網格用語

`measurements/stage_g.json`（`*_text` 欄位）、`stage_h.json`（`g4_face_grid_pane`）；截圖 `G4-*.png`。

三個位置的**實際渲染文字**（不是搜字串）：

- **檢查器（來源模式）**：「網格來源」「主支方向：未設定；排法與基準可在完整工作區調整。」
- **完整工作區（配置模式，`#gridObjectNewBinding` 進入）**：「建立網格配置」「對齊邊界與 cell」「2 · 點選右側邊界的實際頂點。」「cell i」「cell j」「4 · 格子裡的對齊位置」「cell (0, 0)」——`cell` 出現 4 次、`對齊位置`、未見「格內位置」。
- **面內構件頁（網格工具）**：「主支橫向／主支直向」「副支 3」「主網格」「子網格」「建立子網格」——`主支` 7 次、`副支` 2 次。
- **受阻**：檢查器的**配置模式**（已建立綁定後的顯示）未渲染——本次未走到完成綁定那步；其文案僅有 `grid-inspector.js` 靜態字串（`配置設定／對齊頂點／格內位置／對齊格子`），不能視為實際畫面證據。

### 連帶更正（E1）

先前核對表記「原稿引用的步驟 2 文案在 main 已改」——**不正確**。完整工作區配置模式的初始步驟文字實際顯示「2 · 點選右側邊界的實際頂點。」；`grid-system-workspace.js:765` 的「2 · 點選圖中的實際頂點，包括孔洞。」是選取頂點後才更新的分支。E1 所指文案在 `d6b4b450` 可見。

## F1 — 3D 歡迎畫面溢出

`measurements/stage_f.json`、`stage_f2_explore2.json`；截圖 `F-3d-welcome-*.png`。

1382×804 版面堆疊（實測 y 座標）：專案列 0–64 → `.sm-header` 64–129 → `.sm-source-actions` 129–191 → `.sm-steps` 191–263 → `.sm-stage` 263–804。預覽區 `.sm-canvas-wrap` 高 **176.5 px**，其中 `#smWelcome`：

- `scrollHeight 237 > clientHeight 177`（溢出 60 px）；900px 時 `scrollHeight 211 / clientHeight 130`；390px 時 `177 / 130`。
- `.sm-wire-cube` 與 `.sm-stage-head` 重疊；`#smWelcomeTry`（y503–547）與 `.sm-view-tools`（y518–590）重疊；900px 下說明小字還與 `.sm-view-direction` 重疊。
- **CTA 未被遮擋**：在 `#smWelcomeTry` 高度 25/50/75/95% 處取 `elementFromPoint`，全部回 `smWelcomeTry`；且水平方向按鈕（x404–592）與視角分段按鈕（x28–280）不交會。
- Tab 巡覽 22 站全部在視口內，焦點框 `3px solid rgb(139,157,236)`。

## F5 — 3D 控制項樣式

`measurements/stage_f.json`（`styles`、`tab` 欄位）。

1382×804 computed style 實測：

- 全部按鈕與表單控制項高 **44 px**；圓角：一般按鈕 8 px、視角分段 5 px、表單欄位 6 px。
- 主色混用：頂部「保存」`rgb(54,91,245)`；`#smCreate`、`#smWelcomeTry` `rgb(56,85,188)`——同一畫面兩種藍。
- 勾選框 `accent-color: rgb(8,127,131)`（teal），與藍色系不同族。
- 焦點框 `outline 3px solid rgb(139,157,236)`、offset 3 px；面內工具列焦點為 2 px——規格不一致。
- 鍵盤可達性：Tab 序列涵蓋專案控制、範例鈕、畫布、CTA、視角分段、勾選、表單、dialog 控制項。

## F6 — 3D 說明文字

`measurements/stage_f.json`（`texts` 欄位）。

- `.sm-help` 11 px / 行高 19.8 px / `rgb(75,93,124)`；`.sm-guide` 11 px / 18.7 px / `rgb(88,105,135)`；`.sm-view-direction` 11 px / 17.6 px。
- 長度：`.sm-guide` 區塊合計 220 字／4 行（單段最長 80 字）；`.sm-help` 最長 86 字／3 行。「單段超過 100 字」僅整區塊合計成立。
- 對比：兩組文字色對白底分別約 5.9:1、5.3:1（自算）。

## 仍受阻（需再一段互動）

1. G4 檢查器**配置模式**渲染文字（需完成一次綁定）。
2. B6 框選拖曳中的摘要狀態。
3. G3 刪除鈕按下後是否有確認。

## 附檔

- `measurements/`：各階段原始 JSON 與 `css-evidence.out`（壓縮 CSS 的唯讀解析結果）。
- `repro/`：實際執行的腳本（Playwright Python + 兩個 Node CSS 解析器）與 `start-service.ps1` 啟動範本（路徑已參數化；記錄用，不宣稱可移植）。
- `screenshots/`：19 張對應量測的截圖。
- `RUN-LOG.md`：執行順序，含**未完成與受阻的第一次嘗試**及其歸因。
