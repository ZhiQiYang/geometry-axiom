# 雲端實機核對：R03 下角材模式第一片（2026-11-21）

雲端 Claude（scheduled routine）在 main `3ef07683b76837fd08f8737ac5f515a3e46d6b6b`（[#438](https://github.com/ZhiQiYang/geometry-axiom/pull/438) 合併提交，2026-11-21 14:32 UTC）用真 Chrome、只用滑鼠與鍵盤，照 #205 ChatGPT 設計 [6933261603](https://github.com/ZhiQiYang/geometry-axiom/issues/205#issuecomment-6933261603)「驗收及證據界線」的 L4 路徑走完 R03 第一片。範圍依同一設計與 #438 終審 [7063991411](https://github.com/ZhiQiYang/geometry-axiom/pull/438#issuecomment-7063991411)：只限軸向矩形、無孔、World 無柱樑、水平且結構側 +N、RC 邊界。

結果：**走得通**。第一階段 16 項、第二階段 11 項核對全部通過；App 預覽表 33 支與 oracle 對同一尺寸的輸出逐支相同；三項抽查（主支整支連續、只在對牆裁切不置中、RC 邊界有邊界材）都成立。另記 2 項發現（見文末），都不影響幾何、歷史與保存，這張 PR 不修。

這是雲端實機操作（L4），不是使用者驗收（L5）。

## 環境與方法

- 乾淨的 main `3ef07683` 工作樹（sparse-checkout 只排除 `evidence/`；建置與兩階段跑完 `git status --short` 為 0 行）。
- 啟動：`scripts/serve-wt.sh <工作樹> 18861 <回報暫存目錄>`：`ulimit -s 16384`、`LANG=C.UTF-8`／`LC_ALL=C.UTF-8`、PATH 前置 Node 24，`start_local.py --build-only` 後 `start_local.py --port 18861`，`GEOMETRY_FEEDBACK_DIR` 指到暫存目錄（不寫進 repo 的 `feedback/`）。
- `runtime_version.py --probe 18861`：兩次都是 version `e29f1f48f44e7ba5dbac6773f80239257ce9cfab852537ecd204b72adca4b77f`、`fresh:true`、root 為該工作樹（`main-3ef07683/runtime-probe.phase1.json`、`runtime-probe.phase2.json`）。第二階段前重啟服務，pid 3431→3901、session `8628efdf…`→`1a30083e…`，所以冷開是**新服務程序＋新 session＋新瀏覽器 profile**。
- 瀏覽器：Google Chrome for Testing 153.0.8010.12（headless、`--no-sandbox`），Playwright 1.63.0 驅動，視窗 1400×900。Node v24.22.3。
- 輸入只有滑鼠與鍵盤：按鈕、核取方塊用滑鼠點；下拉選單先點一下取得焦點，再用方向鍵移到目標值（`scripts/ui.js` 的 `pick`）；數字與文字欄三擊選取後鍵盤輸入、Tab 離開；畫布拖曳與雙擊用滑鼠；復原／重做用面內按鈕。
- **場景變更只經 UI**。`page.evaluate` 只用來：讀畫面文字、表格與 SVG 屬性、元素位置；唯讀查詢（`dump`、`engineering-read`、`identity-read`、`panel-fill-read`、`newid`）；讀 `ReferenceWorkspace.history`、`getProjectState()` 與 `readFeatureAttachment('framing-template-recipes')`；讀 `/runtime`；以及兩次 `POST /framing-template/read`（唯讀，只取 `generatorInvocations`，分別在另存後與冷開核對之後）。沒有用 bridge 指令或 JS 改場景、配方或歷史。網路請求由 Playwright 的 `request` 事件旁觀記錄（不改請求）。
- 唯一改到瀏覽器屬性的地方同 11-13 以來各次核對：`lib.js` 的 `noPickers` 把 `showSaveFilePicker`／`showOpenFilePicker` 設成 `undefined`，讓另存走下載、開檔走 `<input type=file>`。這不碰場景。
- 所有記錄的 SHA-256：`.gcanvas` 等檔案一律對檔案原始位元組（`crypto.createHash('sha256').update(Buffer)`，`ui.js` 的 `sha()` 不先轉字串；`scripts/test_ui_sha.js` 是同一條具名回歸 `L4_GCANVAS_RAW_SHA256`）。`sceneSha` 等是唯讀回覆字串的雜湊，只做零寫入比對用，核對腳本逐一歸類。

### 重現

```sh
# 1. main 工作樹（可 sparse 排除 evidence/）
git worktree add <工作樹> 3ef07683b76837fd08f8737ac5f515a3e46d6b6b
# 2. 兩階段實跑（每階段前自動重啟私人測試服務並存 probe）；輸出目錄需先放不下任何舊檔
NODE=/opt/node24/bin/node NODE_PATH=<含 playwright 的 node_modules> \
  bash evidence/l4-cloud-20261121r03/scripts/run_walk.sh <工作樹> 18861 <輸出目錄> <暫存目錄>
# 3. 只看不改：確認後的骨架在一般畫面哪裡看得到（發現 1）
APP_URL=http://localhost:18861/ OUT=<輸出目錄> node evidence/l4-cloud-20261121r03/scripts/walk_view.js
# 4. oracle 逐支對照與三項抽查
python3 -I evidence/l4-cloud-20261121r03/scripts/oracle_compare.py . <輸出目錄>/walk_r03.phase1.result.json <輸出目錄>/oracle-compare.json
# 5. 證據目錄 SHA-256 逐檔核對（需要 repo 根目錄核對 oracle 原始檔）
python3 -I evidence/l4-cloud-20261121r03/scripts/verify_sha256.py --repo . evidence/l4-cloud-20261121r03
node evidence/l4-cloud-20261121r03/scripts/test_ui_sha.js
```

`CHROME=` 可改瀏覽器路徑。畫布上拖出的矩形位置取決於當下平移，所以重跑時外環座標可能不同；oracle 對照用的是實際外環，與座標無關。

## 操作路徑與結果（`scripts/walk_r03.js`）

### 第一階段（`main-3ef07683/walk_r03.phase1.result.json`，16/16）

1. **建立矩形封閉面**：檔案 → 新專案 → 工具列「矩形面」在物件畫布拖出 → 右欄「外環邊 · 尺寸確認」邊 0 打 3740、邊 1 打 2000（Tab 送出）→ 「放置這片面」原點 0／0／2500、u +x、v +y →「放置這片面」。場景：`boundary 1 outline 122,194 3862,194 3862,2194 122,2194`、`placement 1 on boundary 1 origin 0 0 2500 u +x v +y`（`RECT_3740x2000_PLACED`）。
2. **物件畫布雙擊進面 → 屬性 → 面設定… → 完成面／骨架…**：面設定選單是「設定平面投影／完成面／骨架…」；面內工作下拉有「完成面與鋪排」「平釘天花骨架（矩形第一片）」兩項，切到後者。只有一個 `[data-ft-workspace="1"]`，沒有另開頁籤（`ENTRY_SINGLE_WORKSPACE`）；範圍說明持續可見，含「矩形第一片」「裁切只在對牆」「主支整支連續」「3700 mm…回報規則衝突」（`SCOPE_TEXT`）；框架、板材、X 三個下拉都是「請明選」，RC／角材語意未勾，預覽與確認鈕停用（`SOURCES_BLANK`）。
3. **準備板材來源**：「準備板材來源／返回骨架」→ 既有工程規格「材料規格」→「＋ 面材」→ 名稱、寬 915、長 1830、厚 6 →「預覽發布材料」→ 勾影響核對 → 確認 →「返回原面骨架（重新讀取）」。回到骨架、狀態「已返回骨架並重讀來源；配方輸入保留，請重新明選本次框架、板材與 X。」，板材下拉出現「L4 R03 面材 915×1830 · v1 · 915 × 1830 × 6 mm」（`MATERIAL_SOURCE_RETURN`）。
4. **建立 X**：「獨立建立 8 mm 門檻 X」→ 參數卡預覽 → 確認 →「返回原面骨架（重新讀取）」。X 下拉出現「鋪排承接門檻／X · 8/1 mm」，三個來源仍是「請明選」（`THRESHOLD_SOURCE_RETURN`）。第 3、4 步各是一筆獨立歷史（歷史 5→7，工程修訂號 15→17）。
5. **保存配方**：名稱「L4 R03 3740×2000 平釘天花」，六個預設明打 915／1830／2／27／33／367，起鋪角「預覽圖左上」（min-min），板長欄位沿「面 v 軸」→「保存配方」。場景與修訂號不變、歷史 +1 且末筆 `kind:'local'`，配方只有 `defaults,id,name,preference,sourceHints,sourceSlots,template` 七個欄位，模板 `flat-ceiling/1`、政策指紋 `21d364e9…bd83`（`SAVE_RECIPE_INTENT_ONLY`）。
6. **明選來源並預覽**：框架「放置面 1 · 原點 0, 0, 2500 · u +x／v +y」、板材 v1、X、勾 RC／角材語意 →「預覽整組骨架」。標題「候選 33 支 · 確認前未寫入」，狀態「整組候選已通過原生驗證；確認才寫入一筆歷史。」。表 33 列與 SVG 33 個矩形逐一相同（`PREVIEW_TABLE_MATCHES_DIAGRAM`）。預覽前後場景、修訂號、身分帳、歷史深度與末筆、配方附件、`newid` 高水位都相同（`PREVIEW_ZERO_WRITE`）。
7. **取消**：「取消本次生成」→ 狀態「本次生成已取消，配方與場景保持取消前原狀。」；同上各值不變（`CANCEL_ZERO_WRITE`）；網路上恰一次 `framing-template-cancel`、沒有 confirm（`CANCEL_SENT_NO_CONFIRM`）。
8. **再預覽並確認**：重新明選 → 預覽（33 列逐值與第一次相同，`PREVIEW2_SAME_AS_PREVIEW1`）→「確認骨架（一筆歷史）」。狀態「骨架已整筆確認為一般正式物件；配方不擁有物件，冷開不重新搜尋。」；歷史 8→9、redo 0、修訂號 17→18、恰一次 confirm 請求、配方附件不變（`CONFIRM_ONE_HISTORY`）。場景多 113 行：`requires panel-fill/1`、`finish-surface 1`、`panel-fill 1`、`derived-placement 2`、`grid 1 on 2 from-fill 1 main-along v`、4 支 `spec`／`guide`（記號）、33 支 `timber`＋33 行 `place … on 2`；場景裡沒有 `framing-template` 或 `flat-ceiling` 字樣（`CONFIRM_LIVE_DEFINITIONS`）。
9. **復原／重做**：「返回面設定」→ 面內「復原」：場景回到預覽前、歷史回到 8、配方仍在（`UNDO_ONE_STEP_KEEPS_RECIPE`）；「重做」：場景與確認後逐字相同（`REDO_SAME_COMMIT`）。
10. **另存**：「← 物件畫布」→ 檔案 → 另存新檔…（下載 `未命名專案.gcanvas`，存為 `main-3ef07683/r03.gcanvas`，8942 B，SHA-256 `697bd7c76c4f84235229434224ff857deafe1b431a934f9268acf5d936d91b28`，原始位元組）。下載後備路徑的狀態列寫「已產生下載，請確認…」，專案 dirty 仍為 true（下載無法回報完成，同既有行為）。

### 第二階段（`main-3ef07683/walk_r03.phase2.result.json`，11/11）

重啟服務（新 pid／session）後開全新瀏覽器（新 profile）。新服務開機時載入內建示範場景（4000×3000 面＋3 支角材），沒有配方、沒有完成面／鋪排定義（`FRESH_CONTEXT`）。

11. **冷開**：檔案 → 開啟專案…（`r03.gcanvas`）。場景與另存前**逐字相同**（124 行，`COLD_SCENE_EXACT`）；配方附件與另存前深相等（`COLD_RECIPE_EXACT`）；開檔過程沒有任何 `/framing-template/*` 請求，新程序的 `generatorInvocations` 為 0（另存前舊程序是 2，即兩次預覽）（`COLD_NO_SEARCH`）。再經同一入口進面 1 → 平釘天花骨架：專案配方顯示「L4 R03 3740×2000 平釘天花 · flat-ceiling/1」、左上／v，三個來源仍是「請明選」，場景等值不變（`COLD_FORM_SHOWS_RECIPE_SOURCES_BLANK`），沒有發出預覽（`COLD_FORM_NO_GENERATION`）。
12. **3700×2000 拒絕案例**：回物件畫布，在空白處再拖一個矩形 → 邊 0 打 3700、邊 1 打 2000 → 放置原點 0／0／2500、u +x、v +y（`boundary 2 outline 420,120 4120,120 4120,2120 420,2120`、`placement 3 on boundary 2 …`；放置 id 是 3，因為 2 已是派生宿主）（`RECT_3700x2000_PLACED`）→ 雙擊面 2 → 屬性 → 面設定 → 完成面／骨架… → 平釘天花骨架。配方沿用冷開的那張（左上、v、gap 2），框架下拉只有「放置面 3」（`ON_OPTIONS_ONLY_FACE2_PLACEMENT`）。明選來源 → 預覽：狀態 `POLICY_RULE_CONFLICT：此起鋪需要退最後板縫，會裁切不在對牆的板；未套用舊 oracle 退縫`，`data-ft-status="rejected"`，確認鈕停用、沒有候選表、沒有 confirm 請求（`CONFLICT_3700_POLICY_RULE_CONFLICT`）；預覽前後各值不變（`CONFLICT_3700_ZERO_WRITE`）；再按取消仍不變（`CONFLICT_3700_CANCEL_ZERO_WRITE`）。

## oracle 逐支對照（`main-3ef07683/oracle-compare.json`）

`scripts/oracle_compare.py` 只拿 App 預覽表的列（角色、位置矩形、長度、寬×厚）與同列 SVG 的 `data-ft-kind`，不讀 native 回覆物件；oracle 是 `geometry-core/framing-template/oracle/framing_oracle.py`（SHA-256 `7aa56990…`，與 main 相同），參數與 `tests/test_framing_template.py::assert_oracle` 相同（P915、L1830、gap 2、w 27、M 367、X 8、min_piece 27），版面由保存的配方偏好換算（v → A=x，min-min → a_start=min、b_start=min），房間是 App 實際外環 `(122,194)–(3862,2194)`。

結果：App 33 支、oracle 33 支，**逐支 kind、矩形、長度全部相同**，寬×厚都是 27 × 33；oracle 自身 `check` 0 失敗、0 conflicts、0 core_limits。

| App 列 | 角色（kind） | 位置矩形 x0, y0, x1, y1 | 長度 | oracle |
|---:|---|---|---:|---|
| 0 | 邊界材（boundary） | 122, 194, 3862, 221 | 3740 | 相同 |
| 1 | 邊界材（boundary） | 122, 2167, 3862, 2194 | 3740 | 相同 |
| 2–5 | 主支（main） | 1025／1942／2859／3776, 221, +27, 2167 | 1946 ×4 | 相同 |
| 6 | 平行邊界材（rc_parallel） | 122, 221, 149, 2167 | 1946 | 相同 |
| 7 | 平行邊界材（rc_parallel） | 3835, 221, 3862, 2167 | 1946 | 相同 |
| 8–11 | 記號副支（secondary:mark） | 149, y, 1025, y+27（y = 544／911／1278／1645） | 876 ×4 | 相同 |
| 12–23 | 記號副支 | 1052–1942、1969–2859、2886–3776 三格，同上 4 個 y | 890 ×12 | 相同 |
| 24–27 | 記號副支 | 3803, y, 3835, y+27（同上 4 個 y） | 32 ×4 | 相同 |
| 28 | 板縫副支（secondary:seam） | 149, 2012, 1025, 2039 | 876 | 相同 |
| 29–31 | 板縫副支 | 1052–1942、1969–2859、2886–3776, 2012, …, 2039 | 890 ×3 | 相同 |
| 32 | 板縫副支 | 3803, 2012, 3835, 2039 | 32 | 相同 |

逐列原值見 `oracle-compare.json` 的 `members`（33 筆，每筆有 appRect／appLength／oracleRect／oracleLength／match）。

三項抽查（同檔 `mainContinuity`、`trim`、`rcBoundary`，全部只用表上的值推回）：

- **主支整支連續**：4 支主支每支都從 y 221 連到 2167（兩側邊界材內緣，長 1946 = 2000 − 2×27），同一 u 位置只有一支，數量與 oracle 相同。
- **封板只在對牆裁切、不置中**：由主支中心推回板寬縫 1038／1955／2872／3789（= oracle seams_a），板片寬 915／915／915／915／**72**；由板縫副支推回板長縫 2025（= oracle seams_b），板片長 1830／**168**。只有最後一片（對牆，max 側）小於整板；置中會讓兩端都是裁片。
- **RC 邊界有邊界材**：v 向兩邊各一支全長 3740 的邊界材，u 向兩邊各一支 1946 的平行邊界材，四支都貼齊外環。

3700×2000 對照：同一 oracle 在面 2 的外環給 28 支、check 0 失敗，最後一道板寬縫是 4079（從 420+3667=4087 退到 4079，即設計文所說的退縫）；App 依第一片規則回報 `POLICY_RULE_CONFLICT` 並停用確認，與 #438 的 `test_N08` 和設計文「3700 mm 舊案例保留為拒絕對照」一致。

## SHA-256 逐檔核對

`python3 -I scripts/verify_sha256.py --repo . evidence/l4-cloud-20261121r03`：56 個檔案、163 處 64 位十六進位值，**相符 7、非檔案 156、失敗 0**，exit 0（含本 README 引述的 `.gcanvas` 指紋與 runtime version 兩處）。

- 相符：`savedSha256`（＝`r03.gcanvas` 原始位元組）、結果 JSON 第 10 步、日誌與本 README 引述的同值、`oracle-compare.json` 的輸入檔雜湊、`oracle/repoFileSha256`（對 repo 的 `framing_oracle.py` 原始位元組重算）、`beforeCold/sceneSha`（對同物件 `scene` 字串重算）。
- 非檔案：`sceneSha`／`identitySha`／`lastUndoSha`／`recipeSha`／`idsSha`（唯讀回覆字串的零寫入比對雜湊）、`version`（runtime 來源指紋）、`policyFingerprint`（模板政策指紋），以及核對細節裡引述這些值的 `before`／`cold` 等欄位；每類都附理由，歸不了類就算失敗。
- 負控：把副本 `savedSha256` 改一位，腳本列出 `FAIL … r03.gcanvas 原始位元組為 697bd7c7…` 與輸入檔雜湊不符，exit 1。
- `node scripts/test_ui_sha.js`：`PASS L4_GCANVAS_RAW_SHA256`。

## 發現

編號自成一組。兩項都是顯示面，不影響幾何、歷史與保存；這張 PR 只記錄、不修。

1. **確認後的 33 支骨架在一般畫面看不到。** 確認後回到面 1 面內，左欄「角材」仍寫「尚無角材 · 設定並放置」，面內畫布只有外環；回物件畫布，左欄多一列「承載面 2 · 自帶矩形」，卡片寫「無邊界 1×1 mm · 4 頂點」，選取後右欄「外框尺寸 0 × 0 mm」、「進入面內工作區」停用（`screens/R03-20-redo.jpg`、`VIEW-02-face1.jpg`、`VIEW-03-host2-selected.jpg`，`walk_view.result.json`，該腳本前後場景不變）。骨架只在確認前的預覽圖與表裡看得到。
   - 重現：照上面第 1～9 步確認後關閉表單看面 1；或冷開 `r03.gcanvas` 後看物件畫布左欄與「承載面 2」。
   - 預期：至少能在某個一般畫面看到已確認骨架的位置。
   - 實際：如上。場景裡 33 行 `place` 都是 `on 2`（派生宿主 `derived-placement 2`），不是面 1 的放置 1；這與 [l4-cloud-20261121a 發現 2](https://github.com/ZhiQiYang/geometry-axiom/blob/claude/l4-cloud-20261121-b/evidence/l4-cloud-20261121a/README.md)（PF-4A 主格與派生宿主看不到）現象相同，#128 §7 把派生宿主的一般畫布呈現與工具路由排在 PF-5。兩者是否同一原因、R03 是否應在本片內呈現，**未確認**，不在這張 PR 判定。
2. **X 參數卡顯示「0 處使用」，名稱是「鋪排承接門檻」。** 從骨架的「獨立建立 8 mm 門檻 X」建立的參數卡，物件畫布左欄與卡片寫「鋪排承接門檻 · 1 個欄位 · 0 處使用」（`screens/R03-22-saved.jpg`、`VIEW-01-object-canvas.jpg`）；確認後 `panel-fill-read` 的鋪排 #1 引用了它（`threshold: {parameterId 1, fieldId 1}`，見 `walk_r03.phase1.result.json` 的 `committedPanelFill`）。
   - 預期：使用次數反映鋪排對 X 的引用（或明示只計某些引用）。
   - 實際：0。使用次數的計算範圍是否本來就不含鋪排門檻，**未確認**；名稱沿用鋪排的預設名，是否該依骨架入口改名也未確認。

另外只記錄、不算發現：預覽表「長度」欄很窄，3740 會折成「374／0」兩行（`screens/R03-15b-preview-diagram.jpg`）。

## 未核對範圍

- 第一片範圍外：凹室／非矩形、孔、柱樑（設計文明定本片不提供，未在 App 試）。
- 其餘起鋪角與板長沿 u；F3／F4 的 8 個既有 golden 正例；3700 的 u 向與 gap 3 變體；3720×2000、X=14 的 `NATIVE_INVALID`。
- 配方的新增／複製／刪除、未知 schema／能力／錯政策指紋／未知 generator 的開檔拒絕；`.scene` 匯出只重建物件。
- 預覽中途改來源、服務世代改變、回執未明的恢復；Enter 不提交。
- 窄畫面（390 px）、Windows、實體手機與觸控、輸入法、輔助科技、系統選檔視窗。
- 使用者驗收（L5）。

## 檔案

- `main-3ef07683/runtime-probe.phase1.json`、`runtime-probe.phase2.json`：兩階段服務的 probe。
- `main-3ef07683/walk_r03.phase1.result.json`、`walk_r03.phase2.result.json`：每步、每項核對、檢查點（不含整段場景的摘要）、網路旁觀紀錄、預覽表逐列值（`preview1`）、確認新增的場景行與冷開前後場景全文；`.log` 是同次主控台輸出。
- `main-3ef07683/r03.gcanvas`：另存的專案（冷開用的原檔）。
- `main-3ef07683/oracle-compare.json`：oracle 逐支對照與三項抽查。
- `main-3ef07683/walk_view.result.json`：發現 1 的只看不改補充。
- `main-3ef07683/screens/`：`R03-*.jpg` 每步截圖、`VIEW-*.jpg` 發現 1 的截圖。
- `scripts/`：`walk_r03.js`（兩階段操作）、`walk_view.js`、`run_walk.sh`、`serve-wt.sh`、`oracle_compare.py`、`verify_sha256.py`、`test_ui_sha.js`、`lib.js`（改自 `l4-cloud-20261121a/scripts/lib.js`，只改預設 port）、`ui.js`（與 `l4-cloud-20261121a` 現行版相同）。
