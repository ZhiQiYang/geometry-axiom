# 根因與責任邊界分析(R1)

- 被測版本 main `d6b4b450d741fcbbfd75c51631915d3082926990`,碼在 `D:/geometry-axiom-qa`(detached HEAD,唯讀)。下文路徑除另註,皆相對 `geometry-web/`。
- 全程只讀碼與 git/gh 查詢,未改檔、未留言、未起服務。
- 標記:「已確認」= 讀到該行程式碼可直接證明;「推論」= 由碼與現象合理推出但無直接證明;「未查」= 沒讀。
- 「已有工單」欄:給 BACKLOG/issue/文件條號;「新」= 現有 BACKLOG.md、決策佇列.md、open issue(24 個)、known-issues.md 均無對應。

## 0. 先講三件對全局有影響的事

1. **open PR 比 known-issues.md 多**:現有 5 個 open PR = #129、#134、#135(win GDI 文件)、#136(win 二進位身分,只動 tests/binaries.py、tests/test_binaries.py、tests/run_all.expected.json)、#137(#46 A/B 採用,草稿)。known-issues 只列了 #129、#134。會碰產品檔的只有 **#134 與 #137**(下表)。
2. **「toast 原文」有一半是規格**:UI-REDESIGN-PLAN.md:196(§5.7)與 :168 明文「toast:所有 bridge ok:false 的 error 原文」;:197「狀態列文案沿用既有(cdp_test 比對中文),改文案必須同步改測試」。所以 **G2 要分兩半**:成功回顯原始指令(沒有規格,是缺陷)與失敗訊息原文(有規格,改動需使用者拍板;已有 opt-in 的 `friendlyError` 先例,app.js:9764/9782)。
3. **新增 CDP 斷言會撞 golden 計數**:#134 同時改 `cdp_test.js`、`cdp_sections.golden.json`、`tests/run_all.expected.json`、`tests/run_all.py`。任何修正 PR 若把回歸測試加進 cdp_test.js 或登記進 run_all,會與 #134 在這幾個檔案衝突。建議回歸測試寫成獨立檔(沿用 room_outline_test.js 那種由 cdp_test.js 呼叫的做法)並排在 #134 合併之後再登記。

## 1. 各 open PR / 分支改動檔(與本次修正有關者)

| 來源 | 產品檔 | 與本次相關的 hunk(舊檔行號,`gh pr diff` 讀到) |
|---|---|---|
| PR #134(draft,#61 slice2,head 5e4ae3e) | app.js、app.css、index.html、reference-ui.js、source-inspector-app.js、grid-system-workspace.js/.css、grid-rule-lines.js(新)、cdp_test.js、cdp_helpers.js、cdp_sections.golden.json、docs/DOM-CONTRACT.md、BACKLOG.md、tests/run_all.* | app.js **1139-1144(emitLine 多一行 operation 守門)**、**2565-2600(leaveFocus 拆成 finishFocusExit/finishObjectCanvasExit)**、9765-9794(mutate 加 operation 守門)、另有 340-360、2697-2837、4197-4738、4919、5095、5425、5594、7405、7605、8123、8307、8369、9765 等 |
| PR #137(draft,#46 A/B,head 見 gh) | project-store.js、reference-workspace.js、index.html、serve.py、native-transport.js、native_context.py、scenario-*.js/.css、scenario_verify.py、tests/test_project_store.js 等 | project-store.js **672-695(ContextHistory.snapshot/restore)**、593、658、686;reference-workspace.js 4、1101-1111、1142-1162、1274、1314、1555;index.html 22、100、647、686 |
| PR #136 / #135 / #129 | tests/binaries.py、tests/test_binaries.py、tests/run_all.expected.json / 純文件 / 決策佇列.md | 不碰產品檔 |
| 本機 worktree(7 個)與 `git status` | 全部乾淨;canvas-performance、history-operation-gate、issue116-context-menu-b、grid-2a 分支相對 main 皆 **ahead 0**(已合入或落後) | 無競寫 |
| 遠端分支(近 2 天) | origin/codex/issue48-evidence-integration、origin/fix/issue123-create-feedback-overlay、origin/codex/issue61-rule-editor-slice1、origin/review/pr130-*、feat/wp60-a-* 皆 ahead 0(已合入) | 無競寫 |
| origin/feat/assembly-generation-minimal-20261002 | ahead 2、最後更新 10-03;改 current_geometry.c、geometry-core/*、project-store.js、reference-workspace.js、assembly-workspace.js | 停滯分支、無 open PR;若重啟會碰 G2(project-store.js)/G6,低風險,需先確認作者是否還活著 |
| issue #123(UI 整合 S0–S6,尚無 PR) | 預計大範圍動 app.css、index.html、標頭/返回/麵包屑 | 非現有競寫,但 G3(返回行為)、G2(狀態列/toast 文案)與其 S1 標頭有概念重疊,動手前要對一次 |

## 2. 分組分析

### G1 匯入對話框 ResizeObserver 良性訊息被當程式錯誤自動回報(T1-01、T2-01、T3-02)

- **責任邊界**:兩層。(a) `feedback.js` 的全域自動擷取不分良性/真錯誤;(b) `reference-workspace.js` 的預覽版面 RO 回呼會觸發該良性訊息。
- **根因**:
  - 已確認:`feedback.js:112-116` 的 `window.addEventListener("error")` 只擋 `!e.message`,其餘一律 `autoReport("JS 例外:"+e.message)`,**沒有任何對 "ResizeObserver loop" 的過濾**。`autoReport`(:230-247)通過節流(20 秒全域、同文 300 秒)後 `notify(已自動記錄程式錯誤 …)` 即 :243 的 toast。
  - 已確認:`reference-workspace.js:1536` `new ResizeObserver(layoutPreview).observe(.ref-preview-scroll)`;`layoutPreview`(:1030-1035)在回呼內改 `#refPagePreview` 的 `style.width`,而 `.ref-preview-scroll` 是 `overflow:auto`(app.css:1823),被觀察元素的內容盒會因捲軸出現/消失而變。
  - 推論:這正是 Chrome 回報 "ResizeObserver loop completed with undelivered notifications" 的典型成因(回呼內改了被觀察元素尺寸);沒有跑瀏覽器逐一證明是這一支 RO 而非 app.js:10302-10307 的兩支。T1~T3 都只在開匯入對話框時出現,與 :1536 最吻合。
  - 已確認:團隊早知道。`room_outline_test.js:12-17` 註解寫著 "A transient baseline ResizeObserver notification can display a feedback toast during layout. Wait for its normal expiry; do not suppress errors.",每次截圖前 `waitForUI` 最多等 15 秒讓 toast 消失(也是 #118 的「等待成本」)。BACKLOG 全文無此條。
- **建議修正範圍(最小改動點)**:`feedback.js:112-116` 的 error 處理器對 `/^ResizeObserver loop/` 開頭的訊息不呼叫 `autoReport`(可仍 `push` 進黑盒子事件)。這是一處、幾行。治本可另做:在 `reference-workspace.js:1536` 的回呼外包 `requestAnimationFrame`。**只做 feedback 過濾,就不會碰到 #134/#137 的任何檔案。**
- **回歸測試想法**:在 CDP 開匯入對話框(沿用 room_outline_test.js 夾具)後斷言:(1) `#toastRegion` 無含「程式錯誤」的 toast;(2) 測試用 `GEOMETRY_FEEDBACK_DIR` 下沒有新增 kind=auto 的 F-* 目錄;(3) 同時再丟一個真的 `setTimeout(()=>{throw new Error("x")})` 仍然會被記錄(防止過濾過寬)。通過後可移除 room_outline_test.js:12-17 的 15 秒等待。突變:拿掉過濾必須讓 (1)(2) 紅。
- **競寫**:可並行;不碰 PR 檔案。
- **工單**:新(僅測試註解承認)。

### G2 內部指令/核心原文外露(T1-04、T2-02、T3-04、T4-05;T3-03;T4-04)

拆成三個獨立根因,責任邊界不同。

**G2a 成功回顯原始指令(T1-04、T2-02、T3-04 狀態列/toast、T4-05)**
- **責任邊界**:app.js 的 `emitLine`(通用 DSL 送出 helper)。
- **根因(已確認)**:`app.js:1140-1144` `emitLine(text, options)` 成功時 `setStatus("✓ " + (options.successText || text))`,**預設文案就是送給核心的原始指令**;`setStatus`(:613-619)對 "✓" 開頭自動再發 `.toast.ok`,所以 toast 與狀態列同時顯示 `boundary 1 outline …`。`emitBoundary`(:1175-1183)組出 `boundary N outline …`;放置走 `emitLine(line)`(:8585,`placement N on boundary …`);子網格用 `successText`(:7339,所以那條是好的);刪除走 `delete grid N`(:7063)。18 個 `emitLine` 呼叫點只有 :7339 傳了 `successText`。空容器空間(:10270)更特殊:`emitLine("space N")` 先 toast `space 3`,隨後 :10272 又 `setStatus` 一次,同一動作兩則 toast。
- 已確認:T3-04「刪面後狀態列仍留舊指令」是因為 `✓ delete grid 2` 寫進 `#status` 後,沒有後續 `setStatus` 清掉。
- 對話框那一半:`reference-ui.js:12` 與 `room-collection-workspace.js:302` 把 `preview.command` 塞進 `<code>`(I8a 確認對話框)。這是**被測試鎖死的設計**:`assembly_generation_test.js:26`、`parameter_workflow_test.js:157`、`grid-system-workspace.js:874` 都讀這個 `<code>` 的文字。要動屬於另一個決定,不建議跟 G2a 同做。
- **建議修正範圍**:`emitLine` 預設 `successText` 改為由呼叫端提供或用「已更新」類通用文案(讓 18 處呼叫點逐步補),或最小版:無 `successText` 時不 `setStatus("✓ …")`、改設通用「✓ 已套用」。依 UI-REDESIGN-PLAN.md:197,**改狀態列文案要同步改 cdp_test 比對**(事先 grep `#status` 斷言:cdp_test.js:3789、3917、4149、4910、4933、5072、6938 讀 status 文字,需逐一確認不依賴指令回顯)。
- **回歸測試想法**:對 `emitBoundary` 成功、放置成功、刪網格成功各一次,斷言 toast 與 `#status` 文字不含 `boundary `、`placement `、`outline`、`delete `(以正則 `/\b(boundary|placement|outline|delete|subgrid)\s+\d/`)。突變:還原預設文案必須紅。
- **競寫**:#134 在 `emitLine` 加 1 行(app.js:1141 後插入 operation 守門),與 :1144 隔 3 行 → 3-way merge 多半乾淨,但同一函式,**排在 #134 之後或由同一人處理較穩**;若改 `emitLine` 簽名則必衝。
- **工單**:新。

**G2b 失敗訊息帶核心原文「line 56: …」與 PR #124 preflight 為何沒出現(T3-03)**
- **責任邊界**:核心 `current_geometry.c` 的 `scene_error`(:6443-6449)把 `"line %d: %s"` 寫進 `g_scene_last_error`——`line` 是核心重播指令流的行號,對使用者無意義;app.js 對失敗一律原文轉出(`mutate` :9783 `toast(msg)`;`emitLine` :1149-1150 `setStatus("✗ "+r.error)`+toast)。
- **根因(已確認)**:
  - 六面盒 `submitBox6`(app.js:3612-3646)與「新增空容器空間」`btnNewSpace`(app.js:10265-10272)直接以 `mutate`/`emitLine` 送 `surface …`/`space …`,**不經任何容量預檢**,撞到核心上限(`current_geometry.c:3609-3614`:邊界面 16、承載面 16、空間 4;錯誤字串 :9337/:9341/:11931)才被拒,原文冒出。
  - PR #124 的 preflight(`space_modeling.py:102-122 check_plan_capacity`、:134-136 `face()`、:153)只在 **空間建模(從面建立空間、材料牆)** 路徑,錯誤碼 `SPACE_CAPACITY`/I33、文案「邊界面需 22/16…」。契約文件 `docs/ISSUE119-WALL-REQUEST-CONTRACT-20261004.md` 的範圍也只寫「新 preview／create／height update／source replacement」。**T3 測的是六面盒與空容器兩條手動路徑,本來就不在 #124 範圍,所以「宣稱的 preflight 訊息沒出現」不是 #124 失效,是範圍不同**(已確認)。
  - 失敗訊息原文本身有規格(UI-REDESIGN-PLAN.md:196、:168),且 `mutate` 已有 `friendlyError` 先例(app.js:9764、:9782,GEO-195)。
  - 「toast 疊在遮罩後、六面盒對話框不顯示錯誤」:推論,`submitBox6` 失敗時 `mutate` 只 `toast` 且對話框保持開啟;toast 層級與 `<dialog>` top layer 的關係未查。
- **建議修正範圍**:`submitBox6` 與 `btnNewSpace` 兩處在送出前以 `oc.faces`/`oc.spaces` 計數預檢(16/16/4;現成 `space_modeling.py` 文案可借鏡),並對 `mutate` 傳 `friendlyError` 把 `line N: …數量超過上限` 轉成帶數字的人話。**是否改動「原文」規格需使用者拍板**(僅轉換這兩條容量訊息屬 opt-in,不動規格)。核心的 `line %d:` 前綴不建議動(公理層/核心,AGENTS 規定 SSOT 不擅改)。
- **回歸測試想法**:先建 14 面+2 空間,再按六面盒 → 斷言對話框內或 toast 出現含「16」「邊界面」的人話、不含 `line \d+:`;空容器到第 5 個同理。突變:拿掉預檢必須紅。
- **競寫**:app.js 3612-3646、10265-10272 與 #134 的 hunk 不重疊 → 可並行。
- **工單**:部分。容量本體 BACKLOG WEB-003(🔶,「動態化/再加大仍開放」);#119 只涵蓋空間建模路徑;**訊息可讀性本身:新**。

**G2c 損毀 ZIP 顯示英文 "invalid zip data"(T4-04)**
- **責任邊界**:`project-store.js` 的 `unpack`。
- **根因(已確認)**:`project-store.js:641-644` 對 `unzip.push` 的例外 `catch (e) { die(e); }`,:628 `if (err) return die(err)`,fflate 原生 `Error("invalid zip data")` 原樣丟出,最後由 `reference-workspace.js:1249-1250` `setStatus("未能完成開啟專案："+error.message)` 顯示。其他驗證失敗(:621、:633、:646、:655-657)都有中文訊息,唯獨 fflate 例外沒包。
- **建議修正範圍**:`unpack` 內把 fflate 例外包成「專案檔案不是有效的 .gcanvas(ZIP)或已截斷」,一處。
- **回歸測試想法**:餵截斷位元組、非 ZIP、空檔,斷言 `error.message` 為中文且不含 `invalid zip`(可在 tests/test_project_store.js 純 Node 測)。
- **競寫**:#137 改 project-store.js 但 hunk(593、658-663、672、686)不含 :628-644 → 理論上可並行,檔案同一支,**建議排在 #137 之後**避免被迫 rebase。
- **工單**:新。

### G3 「← 物件畫布」第一下回到面 1(T3-01、T4-02)

- **責任邊界**:`app.js` 焦點堆疊(`enterFocus`/`leaveFocus`)+ `room-collection-workspace.js` 的呼叫端。
- **根因(已確認)**:`app.js:2529` `if (oc.focus) oc.stack.push(oc.focus)`:只要目前已在面工作區再 `enterFocus("face", other)`,就把舊面推進返回堆疊。`room-collection-workspace.js:278`(`openRoom`,即清單「查看」)與 :332(新增房間確認後進新面)都是在面 1 裡呼叫 `enterFocus("face", 新面)`;`leaveFocus`(app.js:2563-2597)`oc.stack.pop()` 得到面 1,走 :2581-2588「上層仍是面工作區(巢狀):重開」,所以第一下回面 1、第二下才回畫布。畫布雙擊進入時 `oc.focus` 為 null,堆疊為空,所以正常——與 T3 觀察完全一致(桌面 2+窄 1 次、「畫布雙擊進入則正常」)。
- 已確認有先例:同一類問題在「切圖頁」已被當缺陷處理——`reference-workspace.js:1065` 與 `app.js:156` 先判斷「已在該面就不再 enterFocus」,`cdp_test.js:6467` P61-3「切圖頁不累積同一面的返回堆疊」。面→面巢狀沒有任何規格(DOM-CONTRACT.md:229、:257、:359 只談返回/enterFocus,沒說面對面要巢狀)。
- **建議修正範圍**:最小——`enterFocus` 在 `oc.focus?.t==="face" && t==="face"` 時取代 focus 而不 push(app.js:2529 一行);或只在 `openRoom`/`commitDraft` 兩個呼叫端前 `oc.stack` 清理。前者影響面最廣(任何面→面),後者最窄;請依 #123「返回來源」語意選。
- **回歸測試想法**:建兩面 → 面 1 內從房間清單開面 2 → 按 `#workspaceBackButton` 一次 → 斷言 `oc.focus===null` 且 `#objectWorkspace` hidden;再測新增房間確認後同樣一次回畫布;對照:畫布雙擊進面 2 再返回仍一次回畫布。突變:還原 :2529 必須紅(目前 P61-3 只覆蓋「同一面」)。
- **競寫**:app.js :2522-2530 不在 #134 任何 hunk 內(其 hunk 為 2565-2600 的 leaveFocus 重構)→ 檔案層可並行;**語意上 #134 把 leaveFocus 拆成 `finishFocusExit(next)`,若選「改 leaveFocus」就會直接撞,所以請只改 enterFocus 側**。與 #123(標頭「左返回/麵包屑」)概念相鄰,需讓 #123 知道。
- **工單**:新。

### G4 新面卡片與既有卡片同座標疊住(T1-08、T3-05)

- **責任邊界**:`app.js` 的 `objNewPolyFace`(「匯入→建立描繪用面」與 P/多邊形面按鈕共用)。
- **根因(已確認)**:`app.js:8759-8764`:建面後**直接**以「目前視野中心」算 `cx,cy` 並 `api("line canvas-pos boundary …")`,繞過 `renderObjects` 的「跳過已佔用格位」自動排格(:2156-2170 → `nextCardPosition` :2325-2331 有碰撞偵測,但只對沒有座標的物件執行,而這裡已先寫了座標)。每次 `leaveFocus` 回畫布會重置 `panX=0,panY=0,zoom=1`(app.js:2593),所以第二次建面算出的視野中心與第一次完全相同 → 卡片逐像素重疊(推論:座標相同是由此推出;T1/T3 實測重疊吻合,未逐數字核對)。`reference-workspace.js:1057`(匯入「建立描繪用面」)呼叫同一函式。另一路徑 `app.js:8789-8790`(bbox 左上落點)未查是否同樣可能疊住。
- 來源:BACKLOG GEO-187(:2952,✅)「縮到很小後卡片找不回來」是視野中心落點的起因;cdp_test.js:3942 斷言「落點是建立當下的視野中心」。所以**不能簡單改成純自動排格**,要保留「在視野內」。
- **建議修正範圍**:`objNewPolyFace` 的視野中心座標若與 `ocAllObjects()` 現有卡片(`cardBox`)碰撞,就沿用 `nextCardPosition` 找可用位置(只改 :8759-8764)。
- **回歸測試想法**:連續兩次 `objNewPolyFace`(中間 `leaveFocus`),斷言兩卡 bbox 不相交且新卡仍在視野內(沿 cdp_test.js:3942 的視野內斷言);匯入同一 PDF 兩次同理。突變:還原必須紅。
- **競寫**::8751-8770 不在 #134/#137 hunk → 可並行。
- **工單**:新(GEO-187 是同函式的前一個問題,非同題)。

### G5 拒絕無文字說明(T2-03、T1-05、T1-02);雙擊不閉合(T2-04)

- **責任邊界**:`app.js` 面內「重畫外環」草稿(PolyDraft 驅動);`reference-workspace.js` 選頁輸入;`app.js` 校準取點。
- **根因(已確認)**:
  - T2-03-a「2 點按 Enter 無反應」:`app.js:5796-5801` `feDraftTryClose` 在 `fe.draft.pts.length < 3` 時直接 `return`,沒有 toast/狀態。`polydraft.js:467`、:497 已備好「外環至少要 4 個非共線頂點」。
  - T2-03-b 第 5 點自交/背向折返:`app.js:5376-5385` `PolyDraft.place` 回 `r.error`(CROSS「這段會與既有邊交叉」polydraft.js:269、BACKTRACK「不能沿原邊回頭」:251)時只 `feDraftPreviewMove(pt); return;`——橡皮筋轉紅(:5266 `.draft-rubber.error`),**`r.error.msg` 被丟掉**。
  - 規格對照:`docs/RC-POLYGON-PLAN.md:224-229`(§5.A.1.8)寫「橡皮筋線轉紅、浮標 `.hint-context` 改警示文字、點擊該位置不落點」;面內沒有 `.hint-context`,實作改用狀態列+紅(app.js:5870-5882 `feDraftApplyLen` 的註解自己這樣說),**鍵入長度失敗與 `tryClose` 失敗(:5804-5805)有補狀態列+toast,點擊拒絕沒補** → 這是「規格寫了、面內實作漏了」,不是無規格。
  - T1-02:`reference-workspace.js:999` `previewPage` 對超範圍/非整數頁碼直接 `return`;:1004 才寫回 `#refPageNumber`,所以輸入框停在 5、預覽仍是第 2 頁(`#refPageNumber` onchange 在 :1532)。
  - T1-05:`app.js:4782` 校準點直接附加、不檢查兩點是否相同;:4771 文案「已選好兩點」;:4796 `pxDist>0` 才放行並回 false,:6886 才 toast「請先在圖上點兩個不同的點」。拒絕行為正確,缺的是第二點時就擋或提示;註:這句 toast 也被其他 false 原因共用(非整數距離、不可編輯),文案不夠準。
- **T2-04 雙擊不閉合——結論:現行規格已不含它,屬文件漂移**:
  - `docs/RC-POLYGON-PLAN.md:204`(§5.A.1.7)與 :322 寫「三種閉合:點回起點/Enter/雙擊」,但**同一個 commit 3ab5ab3(2026-09-22)**的 `cdp_test.js:4077` 註解就寫「面內沒有雙擊閉合」;雙擊閉合只實作過在主畫布 P 工具,2026-09-24 GEO-186(b)(BACKLOG.md:2936-2945)移除整套主畫布 poly 機器,明列移除「poly 鍵盤/雙擊/三段 Esc」。`app.js:9987-10005` 的面內雙擊只掛在 `fe.tool==="select"`(`feHandleDblClick` :10177)。README 面內說明也沒列雙擊閉合。
  - 因此:不是缺陷;建議把 RC-POLYGON-PLAN §5.A.1.7/§5.A.1.12 的「③雙擊」改成「僅歷史/已移除」(文件修正,公理層無涉),或由使用者決定是否要補。
- **建議修正範圍**:(1)`feDown` 的 `r.error` 分支與 `feDraftTryClose` 的 `<3` 分支,各補一行 `setStatus("✗ "+msg)`+toast(同 :5880-5881 手法);(2)`previewPage` 對無效頁碼把 `refPageNumber` 還原為 `modal.page` 並顯示 `refPreviewMessage`;(3)校準第 2 點若與第 1 點像素距離為 0,在 :4782 就提示/不計入。
- **回歸測試想法**:(1)畫 2 點按 Enter → 斷言 toast/狀態出現「至少要 4 個」;畫成 4 點矩形後點會自交的位置 → 斷言文字出現且頂點數不變(P35-5b 已驗頂點數,cdp_test.js:4070-4074,可就地加文字斷言);(2)輸入 5/0/1.5/空白 → 輸入框回到有效頁碼且有訊息;(3)同點點兩次 → 有提示。突變:拿掉補的那行必須紅。
- **競寫**:app.js 5376-5385、5796-5801、4771-4796、reference-workspace.js:999 皆不在 #134/#137 hunk → 可並行。cdp_test.js 的斷言若加入既有檔會撞 #134(見第 0 節)。
- **工單**:新(T1-02、T1-05、T2-03);T2-04 屬文件,新(文件債)。

### G6 校準隨較早步驟被復原而無提示(T1-03)

- **責任邊界**:`reference-workspace.js` 的 `calibrated()` + `project-store.js` 的 `ContextHistory`(來源歷史),UI 提示在 `app.js` `doUndoRedo`。
- **根因(已確認)**:`reference-workspace.js:827-833` `calibrated()` 直接改 `p.calibration`、`p.reviewRequired` 後 `dirty()`,**不呼叫 `history.push`**(對照同檔 :415、:483、:502、:930 的來源編輯都會 push "local" 步驟)。`project-store.js:673-681` `snapshot()` 與 :695-699 `copyGroups` 會把 `calibration` 一併複製;`push()`(:700)存的是「該步之前」的快照。時序 A(取代外環)→校準→B:撤銷 B 還原到「B 之前」的快照(含校準)→校準仍在;再撤銷 A 還原到「A 之前」的快照(校準=null)→校準悄悄消失,底圖縮回。完全吻合 T1-03。
- 這是**文件化設計**:`docs/REFERENCE-PROJECT.md:61`「同一面實例的來源修改不新增幾何復原步驟。復原／重做可恢復原實例的來源」、:59「中繼資料歷史對應核心的成功命令」;`qa/product-map.md:27`「校準不是 undo 步驟」。所以是**體驗缺口(無提示)而非規格違反**。
- **建議修正範圍(兩案,請擇一)**:
  - 最小案:`doUndoRedo`(app.js:9633-9668)在復原前後比對作用面 `calibration` 有無變化,有變就把「底圖校準已一併還原/重做」附在 `successText`(:9640 附近)。只動 app.js、不動歷史。
  - 治本案:讓 `calibrated()` 像 :930 那樣 `history.push(history.snapshot(),"local","套用比例尺")`,使校準自成一步。但會改變所有撤銷步數的測試期望、與 REFERENCE-PROJECT.md:61 措辭,且碰 ContextHistory。
- **回歸測試想法**:T1-03 序列(取代外環→校準→再取代外環→Ctrl+Z×2),斷言第二次復原的 toast/狀態提到校準,Ctrl+Y×2 後 `calibration.distanceMm` 回復。治本案則斷言第一次撤銷就撤校準。
- **競寫**:最小案 app.js:9633-9668 不在 #134 hunk(其 9765+ 是 mutate)→ 可並行。**治本案碰 project-store.js:673-699,與 #137 的 672-695 hunk 正面衝突 → 必須排在 #137 之後或與其作者協調。**
- **工單**:新(product-map 只是記錄)。

### G7 俯視預覽鏡像(T2-05/V1)

V1 已有結論(鏡像成立、與 PDF 無關、GEO-244 設計為「偵測、提示、提供按鈕,不自動改」;77.647 m³ 是不同輪廓的算術,已駁回)。我重新讀過相關行,V1 的行號全部屬實,補「最小改動點與衝突風險」:

- 已確認行號:`app.js:8425-8433`(`PLACE_PRESETS`)、`app.js:8516-8517`(新面無 surf/slot 時 u/v 預設 `"+x"`/`"+y"` = 天花)、`model-viewer.js:52-63`(`drawingAlignment`,:59 `changed = normalZ !== (view==='top' ? -1 : 1)`)、`space-workspace.js:219-224`(`alignment` 要先 `validProjection(def)` 才算,故第一次確認前無警告)、:433-451(只有第二次按且觀看方向相同才 `mutate` 放置)、:454(第一次只寫投影定義)。
- **最小改動點(由小到大)**:
  1. 可發現性:`space-workspace.js:219` 的 `alignment` 判斷不再要求 `validProjection(def)`(用預設 top 判斷),讓「方向相反」說明在第一次確認前就出現。只動警示,不動行為。**風險低**,但仍是 GEO-244 區塊的 UI。
  2. 閘門:`updateActions` 在 `alignment` 為真時停用「更新預覽/建立空間」直到對齊或明示忽略。**與 GEO-244/docs/FACE-PROJECTION.md:25、:33、docs/SPACE-MODELING.md:32 的「僅設定觀看方向仍只保存用途資訊,不會自動改動放置」「不自動搬移既有場景」精神衝突,需使用者拍板。**
  3. 預設值:`app.js:8516-8517` 對「有底圖/描繪來源」的面預設改成 u +x、v −y 並自動補原點(= `drawingAlignment` 的結果)。**最大衝突**:改變每個新面的預設放置,影響 P79/P84、space_model_test、保存重開夾具與 BACKLOG GEO-244 的 8 種放置×俯仰視契約(BACKLOG.md:4193);且公理層沒有「預設要對齊原圖」的條文,是新行為,須使用者決定。
- 與 PR 的競寫:`space-workspace.js`、`model-viewer.js` 無 PR 觸及;`app.js:8516-8517` 不在 #134 hunk。**檔案層可並行,語意層需使用者決策**(尤其 2、3)。
- **工單**:GEO-244(BACKLOG.md:4186-4190)、#117(closed)、PR #121。V1 判定「設計如此+體驗缺口」我同意;若產品意圖是「照預設得到同手性模型」才升級為資料錯誤。

## 3. 其他項目

| ID | 結論 | 根因/定位 | 工單 | 競寫 |
|---|---|---|---|---|
| T4-06 面內重複 id | **已被文件容許;非新缺陷**。已確認 `placeFormHTML`(app.js:8501)被面內檢視器(:8192-8193)與主畫布檢視器(:9241-9242)各呼叫一次,id 固定(`placeOX` 等 :8513、`placeSubmit` :8520)→ 兩份並存於 DOM(T4 `_q/A/0058.out`:一份 vis=1、一份 vis=0)。`docs/DOM-CONTRACT.md:270`「放置表單欄位(檢視器內,兩處共用)」、:853「必須在 #faceInspectorContent 內找欄位,避免命中背景檢查器的同名欄位」,程式也這樣寫(app.js:160-162、8528、8560 以 `pane.querySelector`)。邊長清單則刻意加前綴避免撞號(app.js:1308-1311;`edge` vs `mainEdge`,DOM-CONTRACT.md:528)。**T4 說的 `edgeLength0` 兩份與碼不符(推論:可能把 `mainEdgeLength0` 當同名)**。**潛在小雷(推論)**:`app.js:5834` 用全域 `$("placeOX")?.focus()`,若主畫布檢視器曾渲染過,會命中 DOM 順序在前的隱藏副本而聚焦失敗(index.html:308 在 :472 之前);未實測 | 新(雷點);重複 id 本身 DOM-CONTRACT 已容許 | 可並行(5834 不在 #134 hunk) |
| T3-06 空間模型移除無確認、該頁 Ctrl+Z 無效 | 已確認:`space-workspace.js:663` 刪除鈕直接 `ReferenceWorkspace.removeSpaceModel(...)`(reference-workspace.js:579-584 → `history.changeModels`,project-store.js:706-710 push "local" 步驟,所以**可復原**)且沒有 try/catch(`removeSpaceModel` 找不到時 throw → 未捕捉例外 → 觸發 feedback 自動回報,推論)。Ctrl+Z 無效:`space-workspace.js:33,182` 是 `<dialog>.showModal()`,`app.js:1462` 的全域 keydown `document.querySelector("dialog[open]")` 一律 return(註解寫明「原生 modal 擁有鍵盤」)→ 對話框內 Ctrl+Z 設計上就不作用。最小修正:移除前 `confirm` 或移除後 toast 提示「可關閉視窗後用畫布復原」,並包 try/catch | 新 | 可並行(space-workspace.js 無 PR) |
| T2-06 同面建兩次同名模型 | 已確認:名稱由 `space-workspace.js:326` 取 `source.name+"空間"`,記錄 id 為 `crypto.randomUUID()`(:581),`reference-workspace.js:566` 只檢查 id 重複,**沒有名稱唯一性檢查**,規格也沒要求唯一(docs/SPACE-MODELING.md 無「同名」)。另:按鈕文案是「修改模型」(space-workspace.js:588),docs/SPACE-MODELING.md:48 寫「修改牆高」→ 文件漂移。建議:同名時自動加序號或提示(一處) | 新 | 可並行 |
| T1-09/T2 撤銷、閉合延遲無忙碌提示 | 只定位:`doUndoRedo`(app.js:9633-9640)設 `oc.busy` 與 `body.oc-busy`(按鈕/輸入 pointer-events:none,app.css:1085-1091)但**不顯示 `#busyIndicator`**(index.html:349「套用中…」只有 `mutate` 在 400 ms 後顯示,app.js:9773);`emitLine`(:1140)根本不設 busy。連按第二次得 toast「操作進行中,請稍候」(:9634、:1478)是現行設計。BACKLOG.md:38-44(PR70 follow-up)明寫「不新增可見入口…沿用既有忙碌樣式」,所以「不加指示」是當時的決定。延遲本身(2–4 秒)來源**未查**(`renderObjects` 對每個面串行 `boundary N`、app.js:2137-2141,僅為可疑點,非結論) | 部分(BACKLOG.md:38-44 管忙碌閘,未管提示;延遲:新) | 若加指示改 app.js:9633+,不在 #134 hunk;可並行 |
| T4-03 參考線計數 21 vs 20 | **未查**。T4 自評信心中低;未讀 `feLoadGuides`/「顯示全部參考線」計數碼 | 新 | — |

## 4. 一覽:共用根因 × 競寫 × 工單

| 組 | 修正會碰的檔案(行) | 與 PR/分支重疊 | 建議順序 | 工單 |
|---|---|---|---|---|
| G1 | feedback.js:112-116(主);reference-workspace.js:1030-1035、1536(選) | 無 | 可並行,先做(最便宜、消除每次匯入的假警報與測試 15 秒等待) | 新 |
| G2a | app.js:1140-1144(+ 18 個呼叫點) | #134 在 :1141 後加 1 行(同函式) | 排在 #134 之後或同作者;勿改簽名 | 新 |
| G2b | app.js:3612-3646、10265-10272 | 無 | 可並行;**先問使用者**是否轉換原文 | 部分(WEB-003、#119 另一路徑) |
| G2c | project-store.js:628、641-644 | #137 改同檔(hunk 不含這幾行) | 排在 #137 之後 | 新 |
| G3 | app.js:2529;或 room-collection-workspace.js:278、332 | #134 重構 leaveFocus(:2565-2600) | 可並行(只改 enterFocus 側);告知 #123 | 新 |
| G4 | app.js:8759-8764 | 無 | 可並行 | 新 |
| G5 | app.js:5376-5385、5796-5801、4782/4796/6886;reference-workspace.js:999 | 無(測試檔見下) | 可並行 | 新;T2-04 文件債 |
| G6 | 最小案 app.js:9633-9668;治本案 + project-store.js:673-699、reference-workspace.js:827 | 治本案撞 #137(project-store.js 672-695) | 最小案可並行;治本案排在 #137 之後 | 新 |
| G7 | space-workspace.js:219-224(低風險);app.js:8516-8517(高衝突) | 無 PR;與 GEO-244 規格衝突 | 需使用者決策,先不動 | GEO-244 |
| 其他 | space-workspace.js:663、326;reference-workspace.js:566 | 無 | 可並行 | 新 |

測試檔共通提醒:凡把斷言加進 `cdp_test.js`/`cdp_sections.golden.json`/`tests/run_all.expected.json`/`tests/run_all.py`,都會與 #134(及 #136 的 run_all.expected.json)衝突;建議回歸測試放獨立檔,待 #134 合併後再統一登記。

## 5. 我最不確定的地方

1. G1 的 RO 觸發點是 :1536 這一支只是最吻合,沒在瀏覽器逐支驗證;但**過濾 feedback.js 這個最小修正不依賴它**。
2. G4 的「座標逐像素相同」由 `leaveFocus` 重置 pan/zoom(app.js:2593)推出,未對照實測座標;重疊現象本身有 T1/T3 截圖證據。
3. T3-03 的「toast 疊在遮罩後」與 T3-06 的「未捕捉例外會觸發自動回報」是推論。
4. T4-03、T1-09 延遲來源:未查。
5. 我沒執行 `git fetch`,遠端分支資訊是本機 refs 當下的值(origin/main = d6b4b45);PR 清單來自 `gh pr list`(即時)。
