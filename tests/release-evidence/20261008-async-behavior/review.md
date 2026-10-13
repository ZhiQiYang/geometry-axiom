# 非同步行為審查（唯讀）

> 協調註記：審查讀取 `e176681f34c634d0fdd2dca364a8d7d44cc51808`。其後 `ce0958ca700753172338fe291a17e781da89465a` 只改證據用詞，沒有改 `app.js`。下面兩條缺陷已對照來源複讀因果鏈，瀏覽器尚未重現。發布用的 app.js 內容雜湊是 LF 正規化後的 `0eb8373cd7fdda7fd328312f8690d87ffc7804fbaa5b3c1d6b15d8263a1193c9`。


- 讀取根：`D:\geometry-axiom-focus390`
- HEAD：`e176681f34c634d0fdd2dca364a8d7d44cc51808`（相符，未 fetch）
- `geometry-web/app.js` git blob：`f4e2cd0f7e07c948ebe10495e0850f79325cc2aa`，與 `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72` 相同。`3574b47..HEAD` 沒有再改 `app.js`。
- 宣稱 SHA-256 `0eb8373cd7fdda7fd328312f8690d87ffc7804fbaa5b3c1d6b15d8263a1193c9`：工作樹是 CRLF（621924 bytes），磁碟 SHA-256 為 `91d91097739fb9bf1fa8ebc5962dadcd2a458111a34a0ce01338246a077839a2`。把 `\r\n` 換成 `\n` 後（611436 bytes）與宣稱值全等。內容相符，差異只在簽出行尾。
- 未開瀏覽器、未起服務、未編譯、未跑 CDP／GRID／P88。未改任何 repo 檔。

判準：只有完整因果鏈才列缺陷。缺測試只進覆蓋缺口。

## 共用實作

沒有單一非同步閘門。各畫面各自釘「這次回覆還是不是現任主人」，再決定要不要寫 DOM 或焦點。常見零件：

| 零件 | 位置 | 作用 |
|---|---|---|
| 導航序號 `oc.navigationSequence` | `app.js:1856`、`2548`、`2594`、`3124`、`3150`、`3551`、`10360` | 進面、離面、開空間、空間三視圖、切三視圖時遞增。面／空間的 `isCurrent()` 比對這個序號、焦點物件與專案。 |
| 物件刷新序號 `ocSeq` | `app.js:2149-2202` `renderObjects` | 每次刷新遞增；`objects`／`surfaces`／每個 `boundary` 回來都比序號，不符就放棄，避免舊邊界快取蓋掉新的。 |
| 面參考載入序號 `fe.guidesLoadSeq` | `app.js:2656`、`4263-4296` `feLoadGuides` | 同時釘 edit、focus、`ReferenceWorkspace.context()`、history frame、session。不符不寫 `fe.guides`。 |
| 面參考操作釘 | `app.js:4722-4739` `faceReferenceOperation` | context、edit、focus、history frame、session、model-operation 標記、原始輸入快照、native revision／fingerprint。`newid` 與放置交易每段 await 都重查。 |
| 檢查器焦點快照 | `app.js:337-389` `inspectorState`／`restoreInspectorState`／`reapplyInspectorFocus` | 重建當下才記焦點。隱藏欄位在可見後才補焦；同一 pane 裡已有別的焦點就不搶。 |
| Hover 序號 | `app.js:860-902` `createHoverPickScheduler` | 新點或 `cancel()` 使舊 hover 不能 `apply`。三視圖與面投影共用。 |
| API receipt | `app.js:419-472`、`541` | 恢復時用 requestId；組構確認另有 stamp，過期結果不 `observe`。 |

`renderFaceInspector`（`app.js:8242`）本身是同步重建。晚回覆會不會搶焦點，取決於「誰在 await 之後還呼叫它」以及呼叫當下的焦點／可見性，不是重建函式裡另藏一份舊焦點。

## 各畫面保護差異

### 主畫布

- 物件畫布刷新走 `ocSeq`（`app.js:2149`）。選取 `selectObject`（`app.js:8969`）與 `renderInspector`（`app.js:9304`）是同步的，沒有晚回覆可寫入的選取快照。
- 進／離面：`enterFocus`（`app.js:2545`）、`leaveFocus`（`app.js:2590`）在每次 await 後查 `isCurrent()`。`openFaceWorkspace`（`app.js:3052`）在 `feLoadGuides` 之後還查 `oc.edit` 物件同一性與 context id（`3076`），不符不畫檢查器。
- 換場景 `resetSceneFocus`（`app.js:1695`）先遞增導航序號並清空面檢查器子節點。

### 面檢查器與規則線

- 規則線主人：`grid-rule-lines.js:56-88`。`initial` 釘 context、`oc.edit`、`oc.focus`、evidence／history／頁面 stamp；`current` 再加 viewport key；`query` 再加 `request`，精確查詢還加當時的 cell 輸入字串。
- `paintQuery`（`grid-rule-lines.js:80-85`）只在檢查器裡還看得到 `.grid-rule-details`、`#tbAnchor` 或 `#refGuideSource` 時才呼叫 `renderFaceInspector`。參數編輯器換掉這些節點後，晚回覆只 `drawFaceEditor()`，不重建檢查器。這是已記錄的產品行為，不是新缺陷。
- 精確定位按鈕（`grid-rule-lines.js:154-177`）只在「當初焦點就在該鈕、期間沒有 focusin／pointerdown／keydown、request 與輸入沒變、焦點落在 body、按鈕仍可見」時才把焦點補回 `#gridRuleExact`。
- 抽屜：`app.css:1631` 在沒有 `drawer-right-open` 時，`.face-inspector-panel` 不是 `display:block`。`reapplyInspectorFocus` 要求 `getClientRects().length`（`app.js:386`），關掉的 390 右抽屜不會把焦點補回。
- 投影小圖 `feRenderProjection`（`app.js:8748`）沒有面／專案／`fe.projOpen` 代號。見未升格。

### 網格工作區

- `grid-system-workspace.js:20` `current`：state 物件、對話框仍開、`ReferenceWorkspace.context()`、`contextToken`。
- 邊界：`loadBoundary`（`746-765`）用 `boundarySerial`，回來才填頂點選單。
- 配置結果：`drawResult`（`776-797`）用 `resultRequest`，規則線再交給 `GridRuleLines.readNative` 的 `owns`。
- 來源規則抽樣：`drawConfirmedRules`（`799-814`）用 `ruleDisplay` 物件同一性；舊 timer 不能 `drawGrid`。`syncRuleEditor`（`266`）不重寫規則輸入、不搶焦點。
- `close`（`1013`）遞增 `serial` 並把 `state` 設成 null，所以上述 `current` 一起失效。

### 空間

- 讀來源／預覽／建立：`startSource`（`space-workspace.js:349`）abort 並遞增 `sequence`。`openCurrentFace`（`427`）、`preview`（`593`）、`create`（`625`）在每次 await 後比 `sequence`、context id；預覽另比 `revision` 與來源 dump／history。改 `#smSettings` 會 `stale()`（`333`、`747`）使舊預覽不能寫入 `state.result`。
- 投影確認有 `projectionSequence`（`484-489`），但完成時仍會搶焦點。見缺陷 1。
- 空間裡的三視圖 `renderSpaceProjection`（`app.js:3550`）有 `isCurrent()`，含 focus、context、navigation。內部 `repaint`（`3581`）await 前後都查。這和全域三視圖不是同一條路徑。

### 全域三視圖

- `setView3`（`app.js:10359`）會遞增 `oc.navigationSequence`、關掉抽屜、清焦點，然後 `await render()`／`refreshSurfaces()` 或 `renderObjects()`。
- `render`（`app.js:835`）await `api("render")` 之後不看 `view3`、不看導航序號，直接寫 `#world` 與 `layout`。`#world` 在 `#cv` 裡，和物件畫布 `#oroot` 分開。見未升格。
- 編輯工具的晚回覆沒有工具代號。見缺陷 2。

### 模型庫（含空間模型庫與斷面庫）

- 斷面庫刷新：`section-profile-workspace.js:103` `refreshLibrary` 釘 `context()` 與 `librarySerial`，不符不改 `cachedRuns`、不發 `section-profile-library-changed`。
- 空間模型庫收到該事件只走 `sectionProfileLibraryList`（`space-workspace.js:651-668`）：只移除 `[data-sp-open-run]` 卡片再附加上斷面拉伸件。已存空間卡與卡上已開啟的來源檢查器不動。
- 斷面工作區本身另有 `generation`／`serial`／`live`（預覽 `78`、3D `98`、宿主面 `75`）。模型更新對話框 `model-update-app.js:13-50` 用 session、`sequence`、`AbortController`，預覽回來還查對話框仍開與選取簽章（`268-276`）。

## 已修項目

| 項目 | 檔案與函式 | commit |
|---|---|---|
| 規則線重繪後，焦點只回到仍可見、且 pane 裡沒有別的焦點的 `#refGuideExpr` | `app.js:383` `reapplyInspectorFocus`；呼叫點 `app.js:8529`、`8558` | `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72`。其後 `9b97a39`、`163c575`、`8982605`、`e176681` 沒有改 `app.js`。 |
| 離開檢查器、打開參數對話框、關閉 390 抽屜、切換選取並離開面之後，晚查詢不搶 `#refGuideExpr` | 同上，加上 `grid-rule-lines.js:59-88` 的主人檢查與 `80-85` 的 DOM 閘門 | 產品行為在 `3574b47`；測試在 `9b97a39`、`163c575`、`8982605`。 |
| 參數編輯器換掉規則明細後，`paintQuery` 不再呼叫 `renderFaceInspector` | `grid-rule-lines.js:80-85` | 已記錄的測試／產品落差（`163c575` 的 25 秒是測試還在等第二次重建）。不是新缺陷。`verify-3` 因探針送 Escape 被排除，不重開。 |
| Q38 來源晚回只更新自身卡片，不換掉已存空間卡與開啟中的來源檢查器 | `section-profile-workspace.js:103` `refreshLibrary`；`space-workspace.js:651` `sectionProfileLibraryList` | `459478e9f68fe8ee9252a5f6b4a1ffb2213a5207`（PR #169 的 `a7bff8f4` 是其後的文件提交，這次 HEAD 已包含）。 |

`8982605` 的 GRID 346／0 與 P88 137 未重跑。

## 仍成立的缺陷

### 1. 空間投影確認的晚回覆搶走仍可編輯欄位的焦點

- 檔案與函式：`geometry-web/space-workspace.js` `confirmProjection`（`484-524`），搭配 `renderProjection`（`285-289`）與 `#smSettings` 的 `input`（`747`）。
- 觸發順序：
  1. 對話框開著、牆底 `#smBottom` 仍是空的，使用者按「確認用途與觀看方向」。
  2. `projectionPending` 只停用 `#smProjectionView`、`#smConfirmProjection`、`#smSetProjection`。`#smSettings` 裡的牆高、牆厚、邊、孔洞沒有停用。
  3. 等待 `dump`／`surfaces` 時，使用者改 `#smHeight`（或牆厚、邊勾選）。`input` 只呼叫 `stale()`，遞增 `revision`，不遞增 `projectionSequence`。
  4. `active()`（`489`）仍為真：它不看 `revision`、不看 `document.activeElement`。
  5. 成功路徑 `522` 把 `next` 設成 `#smBottom`，然後 `scrollIntoView` 與 `focus()`。
- 為何舊回覆會贏：這次回覆是最後一個會動焦點的人。使用者的新焦點沒有被記進任何代號。`#smBottom` 當時是啟用的，所以 `focus()` 生效，牆高上的鍵盤輸入被拉走。投影定義仍會照原觀看方向寫入；這不是數值被蓋掉，是焦點被蓋掉。
- 牆底已經有字時，`next` 是當時仍停用的 `#smPreview`，`focus()` 通常不會生效；同一行的 `scrollIntoView` 仍會捲動設定區。那一部分不算搶焦點。

### 2. 三視圖離開「編輯」後，舊邊界讀取仍畫回編輯手把

- 檔案與函式：`geometry-web/app.js` `enterEdit`（`1237-1248`）、`drawEditHandles`（`1251-1262`）、`v3SetTool`（`1425-1436`）。按鈕在 `geometry-web/index.html:243-246`。
- 觸發順序：
  1. 三視圖開著，使用者按「編輯」。`v3SetTool("edit")` 把 `tool` 設成 `edit` 後 `await enterEdit()`。
  2. `enterEdit` 先 `previewClear()`，再 `await api("boundary ...")`。`drawEditHandles` 裡每個視圖還 `await uvMap(v)`。
  3. 這些 await 期間，使用者按「檢視」（或「矩形」「挖孔」）。`v3SetTool` 立刻把 `tool` 改掉並再次 `previewClear()`，而且不會再發一次邊界讀取。
  4. 舊的 `enterEdit` 回來。它不看 `tool`、不看 `view3`、不看導航序號，仍寫 `editLoops` 並 `drawEditHandles()`。`previewIn`（`1138-1142`）把手把加回 `#world`。
- 為何舊回覆會贏：新操作只做了同步清除，沒有留下一個較新的寫入者。橋接器就算照送出順序回覆，舊邊界讀取仍是最後一次畫手把的人。使用者已離開編輯工具，畫面又出現編輯手把。這不寫 World，只覆寫三視圖預覽。

## 覆蓋缺口

| 既有測試 | 已蓋到 | 沒蓋到 |
|---|---|---|
| `grid_rule_lines_test.js` 的 late sample／late exact／具名規格／`lateGuide`（約 `114-197` 行） | 晚抽樣保留 cell 輸入與焦點；晚精確查詢不覆寫新 cell；參數規格 `901` 與焦點；檢查器外、關 390 抽屜或開參數對話框、切到另一個面之後不搶 `#refGuideExpr`；離開面或延遲 source jump 不改新 view | 不重跑。沒有把「等待中改 `#refGuideExpr` 的文字、焦點仍留在該欄」單獨拆成一條；該情況由 `inspectorState` 在重建當下讀現值，程式上會保留。 |
| `space_model_test.js` `flowInlineGuardsRegression`（約 `475-498` 行） | 確認投影被握住時，關閉、換來源、換專案、改觀看方向之後，晚回覆不能寫入投影 | 握住期間改 `#smHeight`／牆厚／邊，釋放後焦點是否仍在該欄。缺陷 1 沒有測試。 |
| `source_navigation_test.js`（約 `68-77` 行） | 晚的 `section-profile-read` 保住兩張空間卡、開啟中的來源檢查器與焦點 | 未見「斷面庫刷新同時又換專案、又關模型庫」的組合。程式有 `librarySerial` 與 context 比較。 |
| `cdp_test.js` | 有 `setView3(true)` 與 `v3SetTool('rect')`（約 `7013` 行） | 沒有在 `enterEdit` 的 `boundary` 未返回時改按「檢視」。缺陷 2 沒有測試。 |
| `parameter_workflow_test.js` | 參數建立、試算、390 版面 | 沒有「試算未返回時換專案／換選取」的焦點斷言。程式有 `generation`／`serial`／`previewRequest`（`parameters.js:509-533`）。 |
| `assembly_workflow_test.js` | 組構流程與 390 版面；生成測試會握住 confirm 回應 | 不在這次六個畫面的晚回覆焦點矩陣裡。組構對話框自己有 `generation`（`assembly-workspace.js:45-53`、`274`）。 |

## 未升格

1. `render`（`app.js:835-844`）與 `setView3`（`10383-10390`）在 await 之後不回讀 `view3` 或 `oc.navigationSequence`。舊 `render` 會寫隱藏的 `#world` 和全域 `layout`。物件畫布是 `#oroot`，這次寫入不會改卡片。再次打開三視圖會再叫 `render()`；若回應照送出順序回來，較新的那次後寫。在新 render 完成前可能閃舊圖，沒有「舊回覆留到最後」的閉環。
2. `feRenderProjection`（`app.js:8748-8787`）await 之後不查 `fe.projOpen`、面焦點、專案或 `box.isConnected`。`renderFaceInspector` 若已換過 `innerHTML`，舊函式寫到的是脫離文件的節點。要讓同一顆 `#projViews` 上的舊圖蓋掉新圖，需要較早的 `render` 較晚回來。這次沒有證明橋接器會亂序，所以不升格。
3. `parameters.js:868-875` `create` 在 `leaveFocus`／`setView3` 之後沒有再比 context，仍可能把 `state` 設成呼叫開始時的 context，並把 `oc.parameterCreating` 設真。`current()`（`8`）隨後會失敗，`render`（`792`）在沒有 object 時直接 return，不會把舊草稿畫進新專案。沒有看到新專案欄位被寫壞的閉環。`project-info-changed`（`923`）只清「已經不是 current」的 state；若換專案事件發生在 `state=` 之前，旗標可能多留一會。
4. `model-update-app.js:277` 預覽成功後 `focus()` `#muReviewTitle`。等待中 `actions()`（`254-264`）已停用放置與預覽控制；這比較像該次預覽完成後的導向，不是舊回覆蓋掉使用者剛改的值。
5. `163c575`：參數對話框換掉規則明細後不再次重建檢查器。已記錄，不重寫成缺陷。
