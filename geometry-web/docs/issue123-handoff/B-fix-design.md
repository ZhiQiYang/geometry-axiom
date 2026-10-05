# #123 修復設計(Agent B)——最小改動方案

基準:main `d6b4b450`。本文只描述方案,未改任何產品檔。行號皆為 `geometry-web/` 下該 commit 的行號。
實測證據:`geometry-axiom-123ev/.../issue123-evidence/`(下稱「證據」)。

通用說明:
- 「安全」= 該檔不在 #134/#137 的改動清單內(2026-10-06 以 `gh pr diff --name-only` 再核過 #134;#136 無 UI;#137 清單以派工為準)。
- 「等 dot」= 該檔在 #134 清單內(`app.js`、`app.css`、`grid-system-workspace.css/js`、`index.html`、`docs/DOM-CONTRACT.md`、`cdp_*`、`BACKLOG.md`、`tests/run_all.*`)。
- 全部方案不新增、不刪除、不改名任何既有 DOM ID;不碰 C 核心與公理;不碰保存/undo/redo 的交易路徑。
- 以下 CSS 方案優先放進 **不在兩 PR 清單內** 的檔(`space-workspace.css`、`workspace-guidance.css`、`workspace-shell.css`、`project-ui.css`),載入順序見 `index.html:9-24`(後載者在同特異度下勝出)。

---

## 1. 選取摘要遮住尺寸標註(B6)

### 根因
- 摘要卡 `#feSelectionSummary` 是浮在 `#faceEditorViewport` 內的 `position:absolute`(`app.css:2131`,top/left 12px;HTML 在 `index.html:427`)。
- 為了讓圖不被卡片壓到,`feViewportInsets()`(`app.js:2957-2962`)會把卡片底緣 +40px 當作上緣保留區;但它用 `!summary.hidden` 判斷。
- `openFaceWorkspace()`(`app.js:2998`)的順序是:`fe.timberSelection.clear()` → **`feFit(loopsBBox(...))`(`app.js:3026`)** → `feSetTool("select")`(`app.js:3028`,其中才呼叫 `renderSelectionSummary()` 把卡片從 hidden 解開,`app.js:8852-8865`)。
  進入前卡片因不具資格已被 `WorkspaceGuidance.paint()` 設成 `hidden`(`workspace-guidance.js` 的 `host.hidden = !state.active || ...`),所以 fit 當下量到的是 hidden 卡片,上緣保留只有下限 40px。
- 卡片之後才出現;`feResizeViewport()`(`app.js:3000` 附近)只比較寬、高與 `bottom` 不比 `top`(註解明說浮層出現不得移動鏡頭),因此不會補救。
- 算術佐證:證據截圖視口頂 y=116、卡片 128–190,若有算入卡片,圖頂應 ≥ 116+(190-116)+40=230;實際外環上緣約 y=157(≈ 116+40),吻合「fit 時卡片被當作不存在」。
- 範圍:只在「首次進入且 `工具說明` 開啟」或其他使卡片初始 hidden 的情況成立;按「知道了」後 0 選即隱藏(證據 B6 表)。

### 最小改動
- `app.js` `openFaceWorkspace()`:在 `feFit(...)`(3026 行)**之前**呼叫一次 `renderSelectionSummary()`(此時 `oc.focus`、`fe.tool="select"` 已就緒,`oc.focus` 於 `app.js:2531` 設定),讓卡片先解 hidden,`feViewportInsets` 即能量到真實高度。一行改動,不改函式簽章。
- 保底(可選,同檔):`renderSelectionSummary()` 的 `apply` 之後,若卡片由 hidden 轉為可見且 `fe.fittedBounds` 仍為「未被使用者改動的 fit」才重新 `feFit`。不建議做,理由:會在框選拖曳中移鏡頭,違反 `marquee_test.js` 約 213-230 行以 ResizeObserver 監看的「浮層出現不得移動鏡頭」契約。**只做第一項。**
- 不建議以 CSS 縮小卡片解決:卡片 62px 高,即使縮成單列(約 44px)圖頂 157 仍低於卡片底 172,CSS 無法保證不重疊。
- 兩畫布 1 選行為不一致(證據 B6 末段)是 GEO-216 刻意設計(`DOM-CONTRACT.md:56` 明載 `#ocSelectionSummary` 0/1 選視覺隱藏,`#feSelectionSummary` 不變),**不要動**,只需在 S6 文件註明。

### 檔案與重疊
| 檔 | 內容 | 重疊 |
|---|---|---|
| `app.js` | `openFaceWorkspace` 加一行呼叫 | #134 改 `app.js` → **需等 dot / 交接** |

### 影響評估
- 保存/undo/redo:無(只改視圖 fit 的時序,不入交易)。
- 鍵盤/焦點:`renderSelectionSummary` 本就在 `feSetTool` 內會被呼叫,提前一次為冪等;`WorkspaceGuidance.apply` 只有在 `eligible` 由假轉真時才 `remember(key)`,重複呼叫不會把首次教學提早標為已讀(`workspace-guidance.js` apply 前段)。
- DOM ID:不變。

### 回歸步驟
1. `node geometry-web/marquee_test.js`(現有;其中 S10 在 390px 檢查 `#feSelectionSummary` 不溢出,約 351 行)全綠。
2. 新增(或擴充 `marquee_test.js`)一個檢查:清空 localStorage 的 `geometry-tool-lessons-v1` 後,1382×804 進入面 1,取 `#feSelectionSummary.getBoundingClientRect().bottom` 與 `#faceEditorRoot` 內外環最上緣 `getBoundingClientRect().top`(含 `.face-dimension-label`)。**通過條件**:外環最上緣 top ≥ 卡片 bottom + 8px;390×844 同條件亦成立。
3. 突變測試(依專案慣例):把新加的那行拿掉,上一步必須變紅,且訊息指出 inset。
4. 按「知道了」後重測:不得觸發鏡頭移動(`fe.panX/panY` 前後相等)。

### 相依
- 依 #134 合併後在其 `app.js` 上改,或由 dot 在 #134 內順手帶入。

---

## 2. 手機 390px 三視圖按鈕過小

### 實測狀況
- **已實測**:`#v3ZoomBar` 內 `#v3ZoomOut/#v3ZoomIn/#v3ZoomFit/#v3ZoomLevel` 在 390px 仍為 **29px**(證據 X6 表;其他畫布 390px 為 44px)。
- **未實測、需先量**:三視圖工具分段 `.v3-seg-btn`(`index.html:240-243`:檢視/矩形/挖孔/編輯)、`#v3ToolbarSurf` 下拉與 `#newZ`(`app.css:2042-2043` 固定 `height:30px`)在 390px 的實際高度。由 CSS 推算 `.v3-seg-btn` 為 `padding:5px 10px;font-size:12px`(`app.css:1448-1449`),高度約 28–30px,**推論未驗**。
- 另一個「三視圖」入口——空間工作區的 `data-ss-tab="proj"` 頁籤——在 ≤680px 已被 `app.css:2492` 的 `.object-workspace .ss-tab{min-height:44px}` 涵蓋,不在本問題範圍。

### 根因
- 手機 44px 規則(`app.css:2506-2507`)掛在 `body.canvas-composition .canvas-controls ...` 之下;但 `syncCompositionLayout()`(`app.js:9136`)令 `canvas-composition` 在 `view3` 為真時 **關閉**(`active = oc.on && !oc.focus && !view3`)。三視圖模式 `body.v3-mode`(`app.js:10227`)因此退回基礎尺寸 `.canvas-controls .icon-button{29px}`(`app.css:333`)。
- `.v3-seg-btn`、`.v3-plane-controls select/#newZ` 全檔沒有任何 `@media (max-width:680px)`/`pointer:coarse` 觸控尺寸規則。

### 最小改動(僅 CSS)
- 放入 `workspace-shell.css` 或 `space-workspace.css` 尾端(兩者皆不在 #134/#137 清單),使用 `@media (max-width:680px), (pointer:coarse)`:
  - `body.v3-mode #v3ZoomBar :is(.icon-button,.zoom-level)`:`min-width:44px;min-height:44px`(含 `width/height`,因基礎規則寫死 29px);`#v3ZoomBar` 加 `flex-wrap:wrap`、`max-width:calc(100% - 20px)`,避免 390px 溢出。
  - `body.v3-mode .v3-seg-btn`:`min-height:44px`;`body.v3-mode .v3-plane-controls :is(select,#newZ)`:`min-height:44px`。
  - 選擇器需帶 `body.v3-mode` 前綴以勝過 `app.css:333`、`app.css:1579`。
- 先量再改:實作前先在 390×844 量上述四類元素的 `getBoundingClientRect().height`,量完才決定是否需改 `.v3-seg-btn`(上述為推論)。
- 版面風險:`.view-toolbar`(`app.css:1577`)是 `min-height:48px` 的橫列,按鈕變 44px 後可能折行,需在 390px 看溢出。

### 檔案與重疊
| 檔 | 重疊 |
|---|---|
| `workspace-shell.css`(或 `space-workspace.css`)尾端新增規則 | 不在 #134/#137 清單 → **可安全開始** |
| 不要改 `app.css`(#134 清單) | — |

### 影響評估
- 保存/undo/redo/鍵盤/焦點/DOM ID:無影響(純樣式)。`cdp_test.js:6959`(P64)檢查 `#v3ZoomBar .v3-zoom` 結構,不受影響。

### 回歸步驟
1. 390×844 開三視圖,量 `#v3ZoomOut,#v3ZoomIn,#v3ZoomFit,#v3ZoomLevel,[data-v3-tool]`:**每一項 width≥44 且 height≥44**;`#v3ZoomBar` 與 `.view-toolbar` 的 `scrollWidth ≤ clientWidth`(無水平溢出)。
2. 1382×804 同量:縮放列維持 29px(桌面不得放大),避免桌面版面被牽動。
3. 既有:`node geometry-web/cdp_test.js` 的 P64。

### 相依
- 無。與 #123 S4(三視圖右欄 240px)無檔案衝突,但 S4 會再動 `app.css`,屆時等 dot。

---

## 3. 網格縮放工具離畫面太遠/390px 落在摺頁下(X6)

### 實測狀況
- 1382×804:`.ig-zoombar` 位於畫布右下 x674–1006、y746–788,**仍在視口內**,距離不算「太遠」;各畫布縮放列位置/內容/高度不一致(主畫布右下 32px、面內左下 30px、三視圖左下 29px、網格右下 34px)是 S1 tokens 議題,不在本最小方案。
- 390×844:`.ig-canvas` 在 dialog 內 y=1604–1944,縮放列 y=1876–1928,**初始視口外**,需捲動(證據 X6)。

### 根因
- ≤760px 時 `.ig-layout` 改成直向 flex(`grid-system-workspace.css:196`),`.ig-settings` 的 `order:1` 排在畫布之前(`:198`),`.ig-main`(含 `.ig-canvas`)`order:2`(`:199`),畫布固定 340px(`:201`)。設定區很長,畫布被推到第二屏以後。縮放列 `.ig-zoombar` 是畫布內 `position:absolute; bottom:16px`(`:147`),跟著畫布一起在摺頁下。

### 最小改動
- 純 CSS,在 `grid-system-workspace.css` 的 `@media (max-width:760px)` 區:讓畫布在手機尾端有可達性。兩案擇一(建議 A):
  - A:`.ig-main` 改 `order:0`(排在設定之前),`.ig-canvas` 維持 340px。取捨:畫布佔去首屏約 40%,設定區往下;與 S2「對齊頂點圖移右欄 step2」方向相容但需 dot 確認手機步驟順序。
  - B:`.ig-canvas` 改 `position:sticky; top:0; z-index:2`(畫布釘在捲動區頂端),設定區在其下捲動。缺點:持續佔 340px。
- 不要移動 `.ig-zoombar` 的 DOM(`#igZoomOut/#igZoom/#igZoomIn/#igFit` 在 `grid-system-workspace.js:307` 模板內,另有測試引用 `grid_system_test.js`、`grid_trial_test.js`)。

### 檔案與重疊
| 檔 | 重疊 |
|---|---|
| `grid-system-workspace.css` | #134 改此檔 → **需等 dot / 交接** |

### 影響評估
- 保存/undo/redo:無。鍵盤:Tab 順序依 DOM 不變(`order` 只改視覺順序,**注意**:視覺與 Tab 順序分離,A 案會使 Tab 先到設定欄、視覺上畫布在上,這是無障礙取捨,需 dot 決定,或改 B 案避免此問題)。
- 焦點:無。DOM ID:不變。

### 回歸步驟
1. 390×844 開網格工作區,量 `#igZoom` 所在 `.ig-zoombar` 的 `getBoundingClientRect()`:**在初始(未捲動)視口內**,即 `top ≥ 0` 且 `bottom ≤ 844`。
2. 1382×804 不變:`.ig-zoombar` 在原位(x674–1006)。
3. 既有:`grid_system_test.js`、`grid_trial_test.js`、`grid_portable_browser_test.py`;footer 的 sticky 儲存鍵(`:200`)不被畫布蓋住(量 footer 與 `.ig-canvas` 不重疊)。

### 相依
- #134(同檔)。S2 的手機步驟排序若由 dot 重做,本項併入該處理。

---

## 4. 3D 建模預覽被標頭擠壓(F1)

### 根因(兩個,疊加)
1. **緊湊斷點差 4px**:為了讓模型在筆電上放大,`space-workspace.css:12-24` 的緊湊版面只在 `@media(min-width:721px) and (max-height:800px)` 生效;證據環境是 **1382×804**,剛好落在 800 之外,吃到寬鬆版(header padding 20/16、source-actions、steps padding 16、stage-head padding 28/32 等,`space-workspace.css:2`)。證據實測堆疊:專案列 0–64、`.sm-header` 64–129、`.sm-source-actions` 129–191、`.sm-steps` 191–263,`.sm-stage` 只剩 541px,其中預覽 `.sm-canvas-wrap` 僅 **176.5px**。(issue S5 也寫「短高度斷點900px」。)
2. **歡迎區是絕對定位填滿**:`.sm-welcome{position:absolute;inset:0;...padding:20px}`(`space-workspace.css:2`)放在 `flex:1;min-height:130px` 的 `.sm-canvas-wrap`(`:2`);≤720px 又被 `:5`/`:40` 設為 `min-height:90px`/`flex:1 0 130px`。歡迎內容(`.sm-wire-cube` 80px + 標題 + 說明 + CTA + padding,證據量到內容高 237)大於容器 177 → `scrollHeight>clientHeight`,與下方 `.sm-stage-head`、`.sm-view-tools` 視覺重疊。390px:177>130。
   `.sm-stage` 預設 `overflow:hidden`(`:2`),所以超出被裁或疊住而不捲動。
- 證據同時指出 CTA 未被遮擋(hit-test 通過),本問題是視覺重疊與預覽過矮,不是不可操作。

### 最小改動(皆在 `space-workspace.css`)
- a. 把 `:12` 的 `max-height:800px` 改為 `max-height:900px`(對齊 issue S5)。注意該媒體區同時改 `.sm-workspace` 高寬(`height:calc(100dvh - 16px)`),801–900 高度會一併變為貼邊版,需肉眼確認。
- b. 歡迎區顯示期間保證預覽有足夠高度、且 stage 可捲:新增
  `.sm-stage:has(#smWelcome:not([hidden]))` → `overflow-y:auto`,其直接子元素 `flex-shrink:0`;
  `.sm-canvas-wrap:has(#smWelcome:not([hidden]))` → `flex:1 0 260px; min-height:260px`(≥ 237 內容高;390px 內容 177 亦涵蓋)。
  只在歡迎區顯示時生效,有模型後(`space-workspace.js:289` 把 `smWelcome` 設 hidden)恢復原行為,不會壓縮真正預覽。`:has()` 已被本專案 CSS 使用(如 `app.css:2256`)。
- c. (可選)`@media (max-height:900px)` 下 `.sm-wire-cube{font-size:48px;margin-bottom:10px}`,以減少 b 案撐出的捲動。

### 檔案與重疊
| 檔 | 重疊 |
|---|---|
| `space-workspace.css` | 不在 #134/#137 清單 → **可安全開始** |
| `space-workspace.js` | 不需改 |

### 影響評估
- 保存/undo/redo/鍵盤:無。焦點:歡迎區 CTA `#smWelcomeTry` 的 Tab 序不變;stage 變成可捲容器時,焦點進入下方控制項會自動捲動,可接受。
- DOM ID:不變。與 #119 完整性診斷區塊無檔案衝突,但 b 案改變 stage 捲動行為,需確認診斷區在 721–900px 高度不被裁。
- 協調風險:其他未列出的 PR 若改 `space-workspace.css`,應在動工前再 `gh pr list` 核一次。

### 回歸步驟
1. 視口 1382×804、1161×804、900×804、390×844,無模型狀態,量 `#smWelcome`:**`scrollHeight ≤ clientHeight`**。
2. 同視口量 `.sm-wire-cube` 與 `.sm-stage-head`、`#smWelcomeTry` 與 `.sm-view-tools` 的矩形:**交集面積 = 0**。
3. 1382×804 量 `.sm-canvas-wrap` 高:**≥ 260px**(基準 176.5)。
4. 載入範例模型後(`smWelcome` hidden)量預覽高度:**不小於修改前**(桌面)。
5. 既有:`node geometry-web/space_model_test.js`。

### 相依
- 無(與 #123 S5 共用標頭整合另案,等 S1)。

---

## 5. 其餘已重現項(簡列)

| 項 | 根因(檔:行) | 最小改動 | 檔案 | 可否先做 |
|---|---|---|---|---|
| G3 刪除鈕低對比/貼近 | `grid-inspector.css:10` `.gi-delete` 透明邊底、色 `#78869a`(約 3.7:1);`.gi-actions{gap:8px}`(`:8`),≤760px `gap:6px`(`:61`) | 加深文字色至對比≥4.5:1、加與鄰鈕間距或分隔(不移 DOM)。**點擊後有無確認未驗**:`deleteObject`(`app.js:9363`)前段未見 confirm,需實測再決定是否加確認 | `grid-inspector.css`(不在清單);若要加確認則動 `app.js` | CSS 部分可先做;確認對話需等 dot |
| G4 用語不連續 | `grid-system-workspace.js:307` 模板與 `:617,:661,:714,:844` 的 `cell i/j`、`對齊位置` vs 面內 `主支/副支/子網格` | 統一用語字串;**先決定詞彙(含 DOM-CONTRACT 與測試中的文案斷言)**,屬產品決策 | `grid-system-workspace.js`、`grid-inspector.js`、`docs/DOM-CONTRACT.md` | 等 dot(#134 同檔) |
| F5 3D 控制項樣式 | `space-workspace.css:1` `--sm-primary:#3855bc`、`--sm-teal:#087f83`(勾選 `accent-color`,`:2`)vs 全站 `--accent:#365bf5`(`app.css:2176`) | 把 `--sm-primary` 對齊全站 accent、勾選 `accent-color` 改 `var(--accent)`;焦點框統一 | `space-workspace.css` | 可安全開始(視覺基準等 S1 tokens 定案後再定色值) |
| F6 說明字 11px | `space-workspace.css:2` `.sm-guide`、`.sm-help`、`.sm-view-direction{font-size:11px}`(`:2`)及 `:5` 手機覆寫 | 本體字級提升至 12px;不必刪減文案 | `space-workspace.css` | 可安全開始 |

---

## 總表

| 問題 | 檔案 | 重疊 PR | 可否先做 |
|---|---|---|---|
| 1 選取摘要遮標註(B6) | `app.js`(`openFaceWorkspace` 加一行) | #134 | 否,等 dot |
| 2 手機三視圖按鈕(實測僅縮放列 29px;分段鈕未量) | `workspace-shell.css` 或 `space-workspace.css` 新增規則 | 無 | 可(先量 `.v3-seg-btn`) |
| 3 網格縮放 390px 摺頁下(X6) | `grid-system-workspace.css` | #134 | 否,等 dot |
| 4 3D 預覽被擠(F1) | `space-workspace.css` | 無 | 可 |
| G3 | `grid-inspector.css`(+`app.js` 若加確認) | 無 / #134 | CSS 可,確認等 dot |
| G4 | `grid-system-workspace.js`、`grid-inspector.js`、`DOM-CONTRACT.md` | #134 | 否 |
| F5 | `space-workspace.css` | 無 | 可 |
| F6 | `space-workspace.css` | 無 | 可 |

### 能安全開始實作的檔案範圍
- `geometry-web/space-workspace.css`(問題 4、F5、F6)
- `geometry-web/workspace-shell.css`(問題 2,二擇一亦可放 `space-workspace.css`)
- `geometry-web/grid-inspector.css`(G3 的樣式部分)
- 新增測試時,放獨立的新測試檔或 `marquee_test.js`/`space_model_test.js`;**不要**動 `cdp_test.js`、`cdp_helpers.js`、`cdp_sections.golden.json`、`tests/run_all.*`(#134/#137 清單)。

### 必須等待 dot 的檔案
- `app.js`(問題 1 的一行;G3 若加確認)
- `app.css`(S1/S4 tokens、本方案刻意避開)
- `grid-system-workspace.css`、`grid-system-workspace.js`(問題 3、G4)
- `grid-inspector.js`(G4,雖不在 #134 清單,但與 #134 的網格文案同域,建議同批)
- `index.html`、`docs/DOM-CONTRACT.md`、`cdp_*`、`BACKLOG.md`、`tests/run_all.*`(#134/#137 清單)
- #54 範圍不接管。

### 實作順序建議
1. 先做不衝突的 CSS 三件(問題 4、問題 2、F5/F6/G3 樣式)並各自附回歸量測。
2. 待 #134 合併後,由 dot 或交接者在新基準上補 `app.js` 一行(問題 1)與 `grid-system-workspace.css`(問題 3)。
3. 文件(DOM-CONTRACT)隨 #134 後的 S6 補。

### 我最不確定的三點
1. 問題 1 的根因是由程式碼順序與像素算術推得(fit 當下卡片為 hidden),**未實際執行驗證**;實作者應先印出 `feViewportInsets` 回傳的 `top`(預期 40)確認,再套修。
2. 問題 2 的 `.v3-seg-btn`/`#newZ` 高度是由 CSS 推算,證據只量了縮放列;手機斷點是否也有 `pointer:coarse` 專屬情境未驗。
3. 問題 4 的 b 案以 `:has()` 令 stage 在歡迎區顯示時可捲動,是否與 #119 診斷區、`.sm-stage>*` 既有 flex 行為互相干擾(`space-workspace.css:40`)未在瀏覽器驗證。另 G3 刪除是否有確認尚未實測。
