# 雲端實機核對：R03 下角材模式第二片（固定治具矩形，2026-11-22）

雲端 Claude（scheduled routine）在 main `7d426259fe5c002ccefe07998be34ce2ec5bfd03`（[#445](https://github.com/ZhiQiYang/geometry-axiom/pull/445) 合併提交，2026-11-22 06:32 UTC）用真 Chrome、只用滑鼠與鍵盤，照 #205 ChatGPT 設計 [7065012645](https://github.com/ZhiQiYang/geometry-axiom/issues/205#issuecomment-7065012645)「L4 一般入口操作路徑」走 R03 第二片：矩形、無孔、無柱樑、明選固定治具版本 `flat-ceiling/2`（policyFingerprint `3641dec4…6b58`）。範圍依同一設計與 #445 終審 [7074957297](https://github.com/ZhiQiYang/geometry-axiom/pull/445#issuecomment-7074957297)。做法沿用第一片 `evidence/l4-cloud-20261121r03/`。

## 結論（分項，不以預覽表概括整片）

| 範圍 | 結果 |
|---|---|
| 七步主路徑：3740×3301 → v2 配方 → 明選來源 → 預覽 53 支 → 取消零寫入 → 再預覽 → 確認一筆歷史 → 復原／重做 → 另存 → 新服務＋新 profile 冷開 | **通過**（第一階段 23/23、第二階段冷開 8 項全過） |
| 預覽表與 oracle 逐支 | **通過**：53／53 支 kind、矩形、長度全部相同；八個記號 = 設計 = oracle |
| 拒絕例 3700／3709（POLICY_RULE_CONFLICT）、3720（NATIVE_INVALID） | **通過**：代碼正確、確認鈕停用、無候選表、無 confirm 請求、預覽與取消都零寫入 |
| 既有 v1 配方原行為與 pin、不自動升級 | **通過**（第三階段 8/8） |
| 第 4 點「確認後一般畫面」 | **部分通過、部分未通過**，逐項見下表；未通過項獨立列為缺口 |

三階段合計 46 項自動核對全過（23＋15＋8）。這是雲端實機操作（L4 範圍），不是使用者驗收（L5）。

## 環境與方法

- 乾淨 main `7d426259` 工作樹（sparse-checkout 排除 `evidence/`、`tests/evidence/`）；建置與三階段跑完，工作樹 `git status --short` 為 0 行、HEAD 仍是 `7d426259…`。
- 服務：`scripts/serve-wt.sh`，以**非 root 使用者**（`claude`，uid 999）執行，腳本拒絕 root；`ulimit -s 16384`、`LANG=C.UTF-8`／`LC_ALL=C.UTF-8`、Node v24.22.3（腳本檢查 `v24.`）、`GEOMETRY_FEEDBACK_DIR` 必須在 `$TMPDIR`（`/tmp/r03a-l4/tmp`）底下；`start_local.py --build-only` 後 `start_local.py --port 18871`。
- `runtime_version.py --probe 18871`：三階段都是 version `2493abf0db05dabdc6de488b3f73cc0fd6b4766d2076f273ce1919fe8961137b`、`fresh:true`、root 為該工作樹（`main-7d426259/runtime-probe.phase{1,2,3}.json`）。每階段前重啟服務：pid 5275／6098／6832，session `e18401c9…`／`02ec9559…`／`0e44cfcd…`。
- 瀏覽器：Google Chrome for Testing 153.0.8010.12（headless、`--no-sandbox`），Playwright 驅動；每階段新瀏覽器、新 profile；視窗 1400×900（可讀性一步改 390×844 再改回）。
- 輸入只有滑鼠與鍵盤（同第一片 `ui.js`）：按鈕與核取方塊用滑鼠點；下拉先點一下再用方向鍵；數字與文字欄三擊後鍵盤輸入、Tab 離開；畫布拖曳用滑鼠。面內工作下拉是收合 select，每按一次方向鍵就觸發 change 並重繪，所以從「完成面與鋪排」到「平釘天花骨架（政策 A 固定治具）」會先經過 v1 模式一次（`modePath: finish → framing → framing-fixed`，只讀不寫，之後才記錄起始檢查點）。
- **場景變更只經 UI**。`page.evaluate` 只用來讀畫面文字、表格、SVG 與元素位置；唯讀查詢（`dump`、`engineering-read`、`identity-read`、`panel-fill-read`、`newid`）；讀 `ReferenceWorkspace.history`、`getProjectState()`、`readFeatureAttachment('framing-template-recipes')`、`oc.focus`；讀 `/runtime`；以及唯讀 `POST /framing-template/read` 取 `generatorInvocations`。沒有用 bridge 指令或 JS 改場景、配方或歷史。網路請求由 Playwright `request` 事件旁觀記錄。
- 唯一改瀏覽器屬性的地方同第一片：`lib.js` 的 `noPickers`（另存走下載、開檔走 `<input type=file>`），不碰場景。
- SHA-256 一律對檔案原始位元組（`ui.js` 的 `sha()` 直接吃 Buffer；`scripts/test_ui_sha.js` 回歸 `L4_GCANVAS_RAW_SHA256`）。

### 重現

```sh
git worktree add --no-checkout <wt> 7d426259fe5c002ccefe07998be34ce2ec5bfd03
(cd <wt> && git sparse-checkout set --no-cone '/*' '!/evidence/' '!/tests/evidence/' && git checkout 7d426259fe5c002ccefe07998be34ce2ec5bfd03)
# 以非 root 使用者、TMPDIR 設好後執行；輸出目錄先清空
TMPDIR=<tmp> bash evidence/l4-cloud-20261122r03a/scripts/run_walk.sh <wt> 18871 <輸出目錄> <tmp>/fb <repo 根目錄>
python3 -I evidence/l4-cloud-20261122r03a/scripts/oracle_compare.py . <輸出目錄>/walk_r03a.phase1.result.json <輸出目錄>/oracle-compare.json
python3 -I evidence/l4-cloud-20261122r03a/scripts/verify_sha256.py --repo . evidence/l4-cloud-20261122r03a
node evidence/l4-cloud-20261122r03a/scripts/test_ui_sha.js
```

畫布上拖出的矩形位置取決於當下平移，重跑時外環座標可能不同；oracle 對照用實際外環。

## 逐步操作與結果（`scripts/walk_r03a.js`）

### 第一階段（`walk_r03a.phase1.result.json`，23/23）

1. **建立 3740×3301 面**：檔案 → 新專案 → 工具列「矩形面」拖出 → 右欄「外環邊 · 尺寸確認」邊 0 打 3740、邊 1 打 3301 → 放置原點 0／0／2500、u +x、v +y。場景 `boundary 1 outline 122,194 3862,194 3862,3495 122,3495`、`placement 1 on boundary 1 origin 0 0 2500 u +x v +y`，無柱、樑、孔（`RECT_3740x3301_PLACED`）。
2. **雙擊進面 → 屬性 → 面設定… → 完成面／骨架… → 面內工作「平釘天花骨架（政策 A 固定治具）」**：只有一個 `[data-ft-workspace]`；配方說明「固定模板 flat-ceiling/2」（`ENTRY_V2_EXPLICIT`）；範圍說明含「政策 A 固定治具：矩形、無孔、無柱樑」「裁切只在對牆」「需退縫或貼邊移主支的排法仍明確拒絕」（`SCOPE_TEXT_V2`）；三個來源「請明選」、RC 未勾、預覽／確認停用（`SOURCES_BLANK`）。
3. **板材**：「準備板材來源／返回骨架」→ 工程規格「＋ 面材」→ L4 R03A 面材 915×1830、6 mm → 預覽 → 勾核對 → 確認 → 返回原面骨架，仍在 v2 模式，板材下拉出現 `… v1 · 915 × 1830 × 6 mm`（`MATERIAL_SOURCE_RETURN_V2`）。
4. **X**：「獨立建立 8 mm 門檻 X」→ 參數卡預覽 → 確認 → 返回，X 下拉出現「鋪排承接門檻／X · 8/1 mm」，三個來源仍空白（`THRESHOLD_SOURCE_RETURN_V2`）。第 3、4 步各一筆歷史（工程修訂號 15→17）。
5. **保存 v2 配方**：名稱「L4 R03A 3740×3301 固定治具」，六個預設明打 915／1830／2／27／33／367（第六欄標題「固定治具步距 M」），起鋪角「預覽圖左上」（min-min），板長欄位沿「面 v 軸」→「保存配方」。場景與修訂號不變、歷史 +1 且末筆 `kind:'local'`；配方 `template = {id:'flat-ceiling', version:2, policyFingerprint:'3641dec4…6b58'}`，七個欄位（`SAVE_RECIPE_V2_INTENT_ONLY`）。
6. **明選來源並預覽**：框架「放置面 1」、板材 v1、X、勾 RC →「預覽整組骨架」。請求恰一筆 `/framing-template/preview`（schema `framing-template-generate/1`、template v2／該指紋）。標題「候選 53 支 · 確認前未寫入」、狀態「整組候選已通過原生驗證；確認才寫入一筆歷史。」（`PREVIEW_53_MEMBERS`）；記號（記號副支相對起鋪牆的位置）`363,730,1097,1464,2198,2565,2932,3117`（`PREVIEW_MARKS_FIXED_JIG`）；表 53 列與 SVG 53 個矩形逐一相同（`PREVIEW_TABLE_MATCHES_DIAGRAM`）；場景、修訂號、身分帳、歷史、配方附件、id 高水位都不變（`PREVIEW_ZERO_WRITE`）。
   - 6b. 可讀性：視窗改 390×844 → 右欄收起，按「右欄」切換鈕打開 → 量表格；再改回 1400×900。前後零寫入、候選仍可確認（`RESIZE_ZERO_WRITE`）。結果見第 4 點表。
7. **取消**：「取消本次生成」→「本次生成已取消，配方與場景保持取消前原狀。」，各值不變（`CANCEL_ZERO_WRITE`）；恰一次 `framing-template-cancel`、沒有 confirm（`CANCEL_SENT_NO_CONFIRM`）；配方、板材、X 都還在（`CANCEL_KEEPS_RECIPE_MATERIAL_X`）。
8. **再預覽並確認**：重新明選 → 預覽（53 列逐值與第一次相同、零寫入，`PREVIEW2_SAME_AS_PREVIEW1`、`PREVIEW2_ZERO_WRITE`）→「確認骨架（一筆歷史）」→「骨架已整筆確認為一般正式物件；配方不擁有物件，冷開不重新搜尋。」歷史 +1、redo 0、修訂號 17→18、這一輪恰一次 preview＋一次 confirm、配方不變（`CONFIRM_ONE_HISTORY`）。場景新增 181 行：8 行 `spec r03_mark_*`、`requires panel-fill/1`、`finish-surface 1`、`panel-fill 1`、`derived-placement 2`、`grid 1 on 2 from-fill 1 main-along v`、記號 `guide`、53 行 `timber`、53 行 `place … on 2`；場景沒有 `framing-template`／`flat-ceiling` 字樣（`CONFIRM_LIVE_DEFINITIONS`）。
9. **關閉候選工作區 → 一般畫面**（第 4 點，見下表；前後零寫入 `VIEW_AFTER_COMMIT_ZERO_WRITE`）。
10. **復原／重做**：物件畫布左欄點「面 1」→ 右欄「進入面內工作區」→ 面內「復原」：場景與身分帳回到預覽前、歷史回到預覽前深度、redo 1、配方仍在（`UNDO_ONE_STEP_KEEPS_RECIPE`；工程修訂號是遞增計數，復原時 18→19、重做 19→20，不拿來比對）；「重做」：場景與確認後逐字相同、沒有 preview 請求（`REDO_SAME_COMMIT_NO_SEARCH`）。重做後再看一次一般畫面。
11. **另存**：檔案 → 另存新檔…（下載 `未命名專案.gcanvas`，存為 `main-7d426259/r03a.gcanvas`，12197 B，SHA-256 `ff42721bae1364d0c7136db44ee83eb1b37ed9076daa6871047bee60556e3960`）；存檔場景＝確認後場景（`SAVE_IS_COMMITTED_STATE`）。舊程序 `generatorInvocations` 2（兩次預覽）。

### 第二階段（`walk_r03a.phase2.result.json`，15/15）

新服務程序（pid 6098、新 session）＋新瀏覽器 profile；開機時是內建示範場景、無配方（`FRESH_CONTEXT`）。

12. **冷開**：檔案 → 開啟專案…（`r03a.gcanvas`，開檔前重算 SHA-256 與另存值相同，`COLD_FILE_IS_SAVED_FILE`）。場景逐字相同（`COLD_SCENE_EXACT`）；配方附件深相等且仍是 v2／該指紋（`COLD_RECIPE_V2_EXACT`）；開檔過程沒有任何 `/framing-template/*` 請求、新程序 `generatorInvocations` 0（`COLD_NO_SEARCH`）。一般畫面檢查前後零寫入（`COLD_VIEW_ZERO_WRITE`）。再經同一入口開骨架：專案配方「L4 R03A 3740×3301 固定治具 · flat-ceiling/2」、左上／v、三個來源空白、零寫入（`COLD_FORM_SHOWS_V2_RECIPE_SOURCES_BLANK`），沒有 preview 或 confirm（`COLD_FORM_NO_GENERATION`）。
13. **拒絕例**（同一冷開專案，各在物件畫布空白處新拉矩形，原點 0／0／2500、u +x、v +y，經同一入口切 v2 模式、沿用 v2 配方、明選來源 → 預覽 → 取消）：

| 尺寸 | 面／放置 | App 狀態 | 確認鈕 | 候選表 | 零寫入（預覽、取消） |
|---|---|---|---|---|---|
| 3700×2000 | 面 2／放置 3 | `POLICY_RULE_CONFLICT：此起鋪需要退最後板縫，會裁切不在對牆的板；未套用舊 oracle 退縫` | 停用 | 無 | ✓ |
| 3709×2000 | 面 3／放置 4 | `POLICY_RULE_CONFLICT：此縫在舊 R-butt 會移主支中心；目前共同域不接受不同位置` | 停用 | 無 | ✓ |
| 3720×2000 | 面 4／放置 5 | `NATIVE_INVALID：R43: v k=0 segment [4115,4127] has left/right 0/0 mm, X=8/1 mm; complete candidate refused` | 停用 | 無 | ✓ |

每例只發一筆 `/framing-template/preview`、沒有 confirm（`REJECT_*_POLICY_RULE_CONFLICT`／`_NATIVE_INVALID`、`REJECT_*_ZERO_WRITE`）。三例後配方與面 1 的骨架定義都還在（`REJECTS_KEEP_RECIPE_AND_FACE1`）。同一 oracle 對三個實際外環都給 28 支、check 0 失敗（見 `oracle-compare.json` 的 `rejects`）——與設計表「oracle 綠燈不能蓋掉本片邊界與 R43」一致。

### 第三階段（`walk_r03a.phase3.result.json`，8/8）

新服務程序（pid 6832）＋新 profile。輸入是第一片 L4 在 main `3ef07683` 另存的 `evidence/l4-cloud-20261121r03/main-3ef07683/r03.gcanvas`，原樣複製為 `main-7d426259/v1-input.gcanvas`（SHA-256 `697bd7c7…1b28`，與第一片記錄相同）。

14. **開檔**：場景與第一片冷開前逐字相同，配方附件與第一片深相等、template 仍是 `flat-ceiling/1`／`21d364e9…bd83`（`V1_OPEN_RECIPE_UNCHANGED`）；開檔沒有 `/framing-template/*` 請求（`V1_OPEN_NO_SEARCH`）。
15. **v1 原行為**：空白處新拉 3740×2000 → 面內工作「平釘天花骨架（矩形第一片）」：自動選回「L4 R03 3740×2000 平釘天花 · flat-ceiling/1」、說明「固定模板 flat-ceiling/1」、範圍說明是第一片（`V1_RECIPE_SELECTED_IN_V1_MODE`）。明選來源 → 預覽 33 支，平移 (298, −74) 後與第一片 `preview1` 逐列（角色、矩形、長度、寬×厚）相同（`V1_PREVIEW_ORIGINAL_BEHAVIOR`）；預覽、取消零寫入。
16. **不自動升級**：同一面切到「政策 A 固定治具」：配方下拉只有「請明選」與「… · flat-ceiling/1」，沒有出現 /2，說明「固定模板 flat-ceiling/2」（只是 v2 草稿），配方附件與開檔時相同、零寫入（`V1_NOT_AUTO_UPGRADED_IN_V2_MODE`）。在 v2 模式明選那份 v1 配方 → 工作區回到 v1（說明「flat-ceiling/1」、下拉「矩形第一片」），附件與 pin 不變、零寫入（`V1_PICK_KEEPS_PIN`）。

## oracle 逐支對照（`main-7d426259/oracle-compare.json`）

`scripts/oracle_compare.py` 只拿 App 預覽表的列與同列 SVG 的 `data-ft-kind`；oracle 是 `geometry-core/framing-template/oracle/framing_oracle.py` 的 `build()`（SHA-256 `7aa56990aa36abab695aee816c64710ffa60974cf1880879634885259406b359`，與 main 相同；即設計所說的「原 oracle」），參數 P915、L1830、gap 2、w 27、M 367、X 8、min_piece 27，版面由保存的配方偏好換算（v → A=x，min-min），房間是實際外環 `(122,194)–(3862,3495)`。

結果：App 53 支、oracle 53 支，**逐支 kind、矩形、長度全部相同**，寬×厚都是 27 × 33；oracle `check` 0 失敗、0 conflicts、0 core_limits。

| App 列 | 角色（kind） | 位置矩形 x0, y0, x1, y1 | 長度 | oracle |
|---:|---|---|---:|---|
| 0–1 | 邊界材（boundary） | 122, 194／3468, 3862, 221／3495 | 3740 ×2 | 相同 |
| 2–5 | 主支（main） | 1025／1942／2859／3776, 221, +27, 3468 | 3247 ×4 | 相同 |
| 6–7 | 平行邊界材（rc_parallel） | 122／3835, 221, +27, 3468 | 3247 ×2 | 相同 |
| 8–15 | 記號副支 | 149, y, 1025, y+27（y = 544／911／1278／1645／2379／2746／3113／3298） | 876 ×8 | 相同 |
| 16–39 | 記號副支 | 1052–1942、1969–2859、2886–3776 三格，同上 8 個 y | 890 ×24 | 相同 |
| 40–47 | 記號副支 | 3803, y, 3835, y+27（同上 8 個 y） | 32 ×8 | 相同 |
| 48 | 板縫副支 | 149, 2012, 1025, 2039 | 876 | 相同 |
| 49–51 | 板縫副支 | 1052–1942、1969–2859、2886–3776, 2012, …, 2039 | 890 ×3 | 相同 |
| 52 | 板縫副支 | 3803, 2012, 3835, 2039 | 32 | 相同 |

- **固定治具記號**：記號副支下緣＋13 − 194 = `363,730,1097,1464,2198,2565,2932,3117`，與設計表、oracle 三者相同。由記號推得：起鋪牆到第一個記號 363、之後每步 367；板端縫在 2025（相對 1831），縫後從縫起算 367、367、367，最後兩步 185＋184 到對牆 3301，即設計所說尾格 1470 拆成 367+367+367+185+184。
- **主支整支連續**：4 支都從 y 221 連到 3468（長 3247 = 3301 − 2×27），同一 u 只有一支。
- **只在對牆裁切**：板寬縫 1038／1955／2872／3789，板片 915×4＋**72**；板長縫 2025，板片 1830＋**1469**。只有最後一片小於整板。
- **RC 邊界有邊界材**：四邊各一支、貼齊外環。

## 第 4 點：確認後的一般畫面（逐項）

檢查時機：確認後（關閉候選工作區）、重做後、新程序冷開後；三次結果相同。

| 項目 | 結果 | 證據 |
|---|---|---|
| 邊材、主支、記號副支、板縫副支在一般入口**看得見** | **部分通過**。頂列「三視圖」的仰視圖（及前、側視圖）畫出全部 53 支（`data-owner-kind="timber"` 53 個 id），三次都在。物件畫布與面 1 面內**看不到**：面 1 左欄「角材 · 尚無角材 · 設定並放置」，面內畫布 0 個角材命中點。 | `screens/R03A-V{1,2,3}-*-5-three-view.jpg`、`-3-face1.jpg`；結果 JSON `viewAfterCommit`／`viewAfterRedo`／`viewAfterCold` |
| 四類各能**選取** | **部分通過**。三視圖點仰視圖內各類第一支：角材 1（邊界材）、角材 3（主支）、角材 9（記號副支）、角材 49（板縫副支），右欄「選取結果」各顯示「角材 N」。面 1 面內無可選角材。 | `-6-three-view-pick-*.jpg`、`threeViewPicks` |
| 卡片與檢查器**尺寸**正確 | **未通過**。三視圖選取結果只有「角材 N」，沒有長度、寬×厚、宿主或角色；放骨架的宿主「承載面 2」卡片寫「無邊界 1×1 mm · 4 頂點」，選取後右欄「外框尺寸 0 × 0 mm」、「進入面內工作區」停用。沒有找到能顯示這 53 支尺寸的一般畫面卡片或檢查器。 | `-2-host-selected.jpg`、`hostCard`、`hostInspector`、`hostEnterDisabled` |
| 正式 id 與 host id 可見 | **部分通過**：三視圖顯示正式 timber id（角材 1／3／9／49）；host id 只在物件畫布「承載面 2」看得到，與角材之間在一般畫面沒有關聯呈現。 | 同上 |
| Undo／Redo 後仍可見可選 | **部分通過**（同上兩列的部分通過，重做後三視圖 53 支、四類可選；尺寸仍未通過）。復原後（未確認狀態）沒有另看一般畫面。 | `R03A-V2-redo-*` |
| 新程序冷開後仍可見可選、不重搜 | **部分通過**（三視圖 53 支、四類可選；冷開沒有任何 `/framing-template/*` 請求、`generatorInvocations` 0）；尺寸仍未通過。 | `R03A-V3-cold-*` |
| X 參數卡的**引用次數** | **未通過**。物件畫布左欄與卡片寫「鋪排承接門檻 · 1 個欄位 · 0 處使用」；確認後 `panel-fill-read` 的鋪排 #1 `threshold: {parameterId 1, fieldId 1}`（`committedPanelFill`）。三次都是 0。 | `-1-object-canvas.jpg`、`parameterRows` |
| 390 px 預覽表數值完整可讀 | **通過**。右欄需先按切換鈕打開；212 格 0 格折行、0 格截斷、0 個數字被折斷，頁面無橫向捲動（scrollWidth 390），確認／取消鈕 316×44 可見。 | `R03A-15r-390-*.jpg`、`readability[0]` |
| 1400 px 預覽表數值完整可讀 | **未通過**。右欄寬 319 px，「長度」欄把 **3247 折成「324／7」兩行**（6 列：4 支主支＋2 支平行邊界材），64 格折行（其餘是「27 × 33」在空白處換行與「平行邊界材」換行，數值未斷）；無截斷。第一片已記同類現象（3740 折成 374／0）。 | `R03A-15r-1400-table.jpg`、`readability[1].brokenSamples` |
| 390 px 下確認後一般畫面的數值 | **未核對**（一般畫面本身沒有角材尺寸可讀）。 | — |

## 發現（只記錄，不修產品碼）

編號自成一組。

1. **確認後骨架只在三視圖看得到，物件畫布與面內看不到，也沒有尺寸。**（第一片 #444 發現 1 的延續，第二片未修。）
   - 重現：照上面第 1～8 步確認 → 返回面設定 → 看面 1 左欄「角材」與面內畫布；回物件畫布點「承載面 2」；切「三視圖」點任一角材。
   - 預期（設計 7065012645「第二片 L4 另須驗」）：關閉候選工作區後，從一般入口看見並選取正式宿主上的四類角材，卡片／檢查器尺寸、框架、有效範圍、正式 id 與 host id 正確。
   - 實際：三視圖可見可選但只顯示「角材 N」；面 1 面內「尚無角材」；宿主卡 1×1 mm、檢查器 0×0 mm、進入面內停用。53 行 `place` 都是 `on 2`（`derived-placement 2`）。設計文已從源碼定位到 `cmd_objects`／`faceCard`／`feLoadGuides`，並寫要與 #128 PF-5 協調；本次沒有做等價對照，**原因未確認**。
2. **X 參數卡顯示「0 處使用」。**（#444 發現 2 的延續，第二片未修。）
   - 重現：同上確認後看物件畫布左欄「鋪排承接門檻」。
   - 預期：使用次數反映鋪排對 X 的引用，或明示統計範圍。
   - 實際：0；鋪排 #1 的 threshold 是 parameterId 1／fieldId 1。設計文指向 `json_parameter_uses` 未枚舉鋪排 threshold；本次未做等價對照，**原因未確認**。
3. **1400 px 下預覽表「長度」欄把四位數長度折成兩行**（3247 → 324／7）。390 px 時反而不折（右欄覆蓋畫布、表格較寬）。
   - 重現：第 6 步預覽後，以 1400×900 視窗捲到表格。
   - 預期：數值完整可讀。
   - 實際：如上（6 列）。只影響顯示，不影響幾何、歷史或保存。

另外只記錄、不算發現：
- 面內工作下拉是收合 select，用鍵盤從「完成面與鋪排」往下切到 v2 時，每一步都觸發重繪，會先經過 v1 模式（只讀）。
- 第二階段三個拒絕例後 `generatorInvocations` 是 1（三次預覽請求都送出、都被拒）。計數規則未查，不據此判斷。

## 未核對範圍

- 第二片範圍外（設計明列、App 未試）：退縫 FT02／R-butt（3700、3709 只驗拒絕）、凹室／L 形、孔、柱、樑（含「World 有任何柱樑就拒絕」的守門）、多面整批、既有輸出重排。
- 第二片範圍內未走：其餘三個起鋪角、板長沿 u、2500×3000、F3／F4 凍結房、3740×2000 在 v2 的相容、M 改值。
- 未知可讀版本唯讀、已知版本錯 pin 整份開檔拒絕（需要改檔，未做）；配方新增／複製／刪除。
- 復原後的一般畫面（只核了場景回到預覽前）。
- Windows、實體手機與觸控、輸入法、輔助科技、系統選檔視窗（另存走下載後備路徑）。
- 使用者驗收（L5）。

## SHA-256 逐檔核對

`python3 -I scripts/verify_sha256.py --repo . evidence/l4-cloud-20261122r03a`：**PASS（相符 13、非檔案 370、失敗 0）**，exit 0。

- 相符：`savedSha256`、`savedSha256AtOpen`（＝`r03a.gcanvas` 原始位元組）、`v1InputSha256`（＝`v1-input.gcanvas`）、各處引述同值、`oracle-compare.json` 的輸入檔雜湊、`repoFileSha256`（對 repo `framing_oracle.py` 重算）、`sceneSha`（對同物件 `scene` 字串重算）。
- 非檔案：零寫入比對用的回覆字串雜湊、runtime version、兩個模板 policyFingerprint（腳本常數另列為已知值）等，每類附理由；歸不了類就算失敗。
- 負控：把副本 `savedSha256` 改一位，腳本列 3 筆 FAIL（`savedSha256` 與檔案不符、兩處引述無法歸類），exit 1。
- `node scripts/test_ui_sha.js`：`PASS L4_GCANVAS_RAW_SHA256`。

## 檔案

- `main-7d426259/runtime-probe.phase{1,2,3}.json`：三階段服務的 probe。
- `main-7d426259/walk_r03a.phase{1,2,3}.result.json`、`.log`：每步、每項核對、檢查點、網路旁觀、預覽表逐列值（`preview1`）、確認新增場景行、一般畫面檢查（`viewAfter*`）、可讀性量測、拒絕例、v1 對照。
- `main-7d426259/r03a.gcanvas`：另存的專案（冷開原檔）；`v1-input.gcanvas`：第三階段輸入（第一片原檔）。
- `main-7d426259/oracle-compare.json`：oracle 逐支、記號、三項抽查與拒絕例 oracle 結果。
- `main-7d426259/screens/`：每步截圖（jpg）。
- `scripts/`：`walk_r03a.js`、`run_walk.sh`、`serve-wt.sh`（新增非 root／TMPDIR／Node 24 檢查）、`oracle_compare.py`、`verify_sha256.py`（改為指名 .gcanvas）、`lib.js`（只改預設 port）、`ui.js`、`test_ui_sha.js`（與第一片相同）。
