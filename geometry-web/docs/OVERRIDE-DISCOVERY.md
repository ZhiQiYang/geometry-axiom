# D09：已套用覆寫的首屏摘要（issue #454 工作包 F；#461 R5 v2）

基底：`b3c4b981bb96b118c1c05b7a1bd98062d710c8b2`。本片只改工程規格宿主展示；公理層、核心定義、保存格式、交易與候選驗證不變。

## 從條文推出的通則

D28 的覆寫附屬於明確的物件／面／欄位，查找順序是物件覆寫、本面覆寫、固定做法、固定材料版本。R31 要求預設保留既有覆寫；I36 保存完整來源。由這些條文可推出：重開後不能僅因目前數字等於預設，就把明示覆寫當成沿用；介面也不能只讓使用者看到沿用來源的外觀而藏起已保存的定義。

條文沒有指定 badge、摘要位置或自動展開。最保守的宿主取捨是：在第一個可編輯欄位前，以一個既有 disclosure 的摘要告知目前目標的覆寫數；第一項同時列欄位與來源，展開看全部。只有使用者按檢視才移動焦點與捲軸。開啟表單不展開、不自動捲動、不建立草稿、不改 World／歷史。這保留開啟位置與鍵盤焦點，不把資料存在 DOM 裡當作可見。

摘要用「**已套用**」表示目前核心 World；不寫「已保存」，因為確認後可能尚未另存檔案。未確認草稿仍在原欄位，不混入數量。新瀏覽器讀回 `.gcanvas` 後則從新讀取的核心定義產生相同摘要，不另存一份摘要狀態。

計數規則：一個明示覆寫欄位算一項。literal 0、與做法數值相等的 literal、具名尺寸及固定材料版本引用都算；軸向及主支方向的明示面設定也各算一項。物件覆寫限目前放置面的主格／角材，按實際 target 身分取；只有 source、沒有 override 的普通綁定不算。缺少核心讀取時保留原讀取錯誤畫面，不顯示假造的零項。

起算點與覆寫必須分開命名與計數，這是定義推論：D28 明列面／物件可覆寫欄位，並把具體起算點定為依 D10a 保存的獨立明示設定；套用起點選項只供新建，已建 anchor 在主格。R31 也分別要求保留覆寫與具體起算點。因此不能把「所有明示配置」冒稱「D28 覆寫數」，也不能因排除覆寫計數就忽略起算點。現行工程表單的起算點 fieldset 在「套用目標」details 關閉標籤之後，並未藏在那個 details 內；更新主格時仍顯示保留目前起點／明選變更的控制。

條文沒有指定起算點是否共用首屏摘要。可選：A，獨立的具體起算點配置列（建議，清楚區分來源覆寫與幾何 anchor）；B，在同一 disclosure 裡新增獨立配置分區並分列兩個數量。兩者都不得把起點混算成覆寫、也不得以 anchorOptions 猜已建主格的有效值。這項呈現取捨尚未拍板，v2 不新增起算點摘要，不宣稱已解決所有明示配置的首屏可發現性。

## 哪些表單適用

| 表單 | 判定與本片範圍 |
|---|---|
| 工程規格「套用至面」與由主格進入的同一套用表單：`engineering-workspace.js::renderApply/renderTarget` | 適用；本片完成頂部本面／物件摘要。未勾選的核對面仍可唯讀查看；只有原本可編輯目標提供檢視欄位按鈕。多面作用域見下一節。 |
| 「材料規格排格」新建／更新網格：`engineering-workspace.js::renderGridFlow` | 適用；本片共用同一摘要。此流程保留既有覆寫，摘要唯讀，不增另一套覆寫編輯／提交按鈕。 |
| 工程規格內物件尺寸來源／覆寫編輯：`engineering-workspace.js::renderObjectSources/sourceEditor` | 適用；本片把同面實際物件覆寫納入摘要，仍沿既有來源欄位預覽，custom 角材不因此改角色。 |
| 三角色 A／B「截面覆寫」巢狀收合：`engineering-workspace.js::renderTarget` | 適用且在本片；具名欄位納入同面摘要，明示檢視會展開外層與目標控制的全部祖先 details。Node 回歸包含只有 primary.A、沒有 gap 的已套用覆寫。 |
| 預覽的「保留的覆寫 · N」：`engineering-workspace.js::renderPreview` | 同一可發現性原則適用，但其作用域是整次候選與受影響下游，不是目前核對面；現有 summary 已顯示保留數，詳列 before/after 中相同定義。本片維持原 I8／I8a 預覽、核對勾選與確認門檻，不把編輯頁的本面數量帶過去冒充全候選數。 |
| 可編輯角材定義／批改：`timber-edit.js::dimensionInput/batchHTML/dimensionHTML` | 適用但不在本產品片。A／B 的物件覆寫模式、來源與值是可編輯欄位；「所選角材的原定義與來源」能列出覆寫，但收合時沒有逐件狀態。本片未替它加頂部摘要。後續應按所選角材與 A／B 槽位列數、保留混合值和未勾欄位；不能依新草稿或批改輸入的初始「沒有覆寫」判定所有原物件無覆寫。 |
| 完成面鋪排「明示縫中心」：`panel-fill-workspace.js::fieldNames/nativeFields/readableTable` 的 `seamOverrides` | 適用同一原則，但有限中心覆寫屬 panel-fill 自己的定義與作用域；本片未新增這類編輯表單，不與 D28 面／物件覆寫混算。 |
| 材料／做法版本編輯、具名尺寸與參數卡、一般幾何座標 | 不直接套用「覆寫」標籤。它們是自己的來源定義或新版本／草稿，不能由數值不同推定局部覆寫；沿現有版本與草稿狀態。 |
| 面內唯讀檢查器：`app.js::engineeringSourceSummary`、角材詳細資料／工程來源主格檢查器 | 原則適用，這裡不是覆寫編輯表單。現有有效值旁有「物件覆寫」，來源路徑在詳細資料內，角材技術區本身也可能收合。本片不改檢查器，不宣稱其所有選取狀態已首屏可見；需要時另驗頂層摘要，避免重複下方完整來源。 |
| 唯讀角材料單與 CSV：`timber-schedule.js::sourceText` | 原則適用，這裡不是覆寫編輯表單。現行來源文字指名物件覆寫、CSV 保留來源定義；本片維持，不另加重複編輯入口或覆寫數。 |

## 多面套用的作用域

摘要只代表「核對這個面」目前選到的 `activePlacement`（排格入口則是 `gridFlow.placementId`）。可見 summary 一開始就寫面名／放置 id；`data-ew-owner` 也固定為同一 id。它不是「套用目標 · 已選 N 個放置面」的聯集數，不因另勾一面就混入其他面的覆寫，也不把未勾的目前面冒稱待套用目標。

其他已勾面的查看路徑是：展開「套用目標」核對已勾清單 → 在「核對這個面」逐一切換 → 讀取同位置、已換成該面名稱與數量的摘要；需要編輯時才按該面的檢視按鈕。這次採保守的單面核對契約，沒有新增所有已選面的合計或自動跳頁。真正預覽仍列本次全部明選目標和引用鏈的連帶影響，確認前仍要勾已核對；單面摘要不能替代整次預覽。Node 同時勾兩面、切換 activePlacement，檢查面名與各自數量，不將其中一面的 0 項推成全部已選面 0 項。

## DOM 與操作契約

`#ewOverrideOverview` 位於 `.ew-editor .ew-form` 的標題之後、第一個欄位之前。兩個入口共用 `renderOverrideOverview(placementId)`，資料只從已成功讀取的 `state.snapshot` 推得。`data-ew-face-count`、`data-ew-object-count` 分列已套用定義；摘要的總數是兩者和。首項保留來源種類與身分，不以推算有效數字取代具名尺寸／材料版本。

展開列出所有已套用欄位、物件來源及核心提供的有效值；目前面核心定義沿用原 `renderData()`。`[data-ew-reveal-overrides="face"]` 展開既有 `[data-ew-face-overrides]`，聚焦已有 value 欄（無 value 時來源模式），再將同一控制捲進可見處。object 動作定位原 `[data-ew-source-details]` 的覆寫模式。這些動作不呼叫 `changed()`、`saveDraft()`、核心指令或候選建立。

取消、確認、復原／重做、保存仍走原流程。改欄位仍先預覽；核對後確認才一筆歷史；零變更預覽仍須沿原有行為處理。摘要不清空覆寫、不自動還原沿用，也不把草稿讀成已套用。來源更新、undo/redo 或重開後，以新的核心讀取重畫。

GEO-219 減項：移走一般套用頁底部的「目前本面套用與覆寫」，以及排格頁底部的「本面已有做法與覆寫，核對保留內容」，合為同一個頂部 disclosure；不增頂層入口、常駐教學或第二組預覽／確認列。原本用來編輯的本面／物件來源區仍保留。

## 測試與收據界線

`test_d09_override_discovery.js` 的原 8 個產品 tests 執行真正工作區 renderer、輸入／點擊處理和 command builder，在基底先紅；P 後檢查頂部順序、零與同值計數、來源身分、多面選取下的單面範圍、草稿隔離、兩入口、逃脫文字與明示檢視零寫入。v2 增加 3 個 cold driver 原生讀取契約 tests，總共 11 個；它們在無 Chrome 的 VM 執行實際 `coldLanding()`，不以模擬繪製結果宣稱瀏覽器通過。既有 D09 display 7 tests 不修改。

`d09_override_discovery_mutations.py` 保留 4 個產品具名撤回：移除頂部摘要、漏算 literal 0、混入他面覆寫、拿掉明示展開。v2 加 3 個裁判自身撤回：誤把 ownership 從 engineering-read 取、漏查 revision、把其他 target kind 的相同 id 當角材。每項隔離副本執行；須通過語法、命中指定 assertion，基線／突變／還原為 0／1／0 才記 killed。設定錯誤、逾時或 anchor 不唯一不算 kill；不寫入正式突變帳本。

v1 cold driver 的第 78 行確實會失敗，但缺的是 `snapshot.grids`，不是預審所寫的 `sources/bindings`。`engineering_bridge.inc::cmd_engineering_read()` 以 geometry=false 回傳 `state.sources`，不含 grids/timbers；`engineering-adapter.js::read()` 才合併 references 的 ownership。v2 driver 改為 engineering-read → references → engineering-read，兩次 revision 必須相同，四個必要清單缺任何一個便拒絕，不以空陣列猜零。每次 cold 開啟另記 `cold-native-390.json`／`cold-native-1400.json` 原始三回覆。新增 tests 對保存的 v1 driver 真正執行出具名 assertion 紅，對 v2 driver 綠；這是裁判修正證據，與產品 T→P 的 8 個紅綠分開報告。

P4549 是獨立 module。390×844／1400×900 檢完整裁切祖先與五個命中點，走正式例子、改 4 mm、取消、核對確認、undo/redo、未編輯預覽；佈局矩陣明示用了實際 wheel 回頁頂，**不把它叫冷開證據**。真正冷開由 `tests/integration/d09_override_discovery_browser.cjs` 另跑：正式 Save 實檔、新建空工程、每尺寸一個 fresh profile、正式 chooser Open，第一次觀察前不點、不滾、不展開；保存 raw metrics、第一屏截圖、native dump 與每個階段的身分。確認視覺不得只查 DOM 值。

預審 7171574960 在外部暫存複本真 Chrome 跑到 v1 P4549 先紅後綠（7 pass／1 fail → 22 pass），v1 cold 390 首屏繪製兩項通過後才因 ownership 缺欄中斷；1400 cold 未達到。v2 的產品 JS/CSS 與 P4549 原 bytes 保留，但修後完整 cold driver 在本交付環境未開 Chrome，仍須雲端重跑。Node/VM 結果不代表 Chromium 通過；外部暫存單段結果也不是正式成本或 L4。新段與套件維持工具產生的 pending 宣告，未填入虛構 count／cost／golden。所有既有段落 count、golden、時限與 byte pin 保持。

## 雲端接手

1. 在共同基底依序套 T、P；跑 Node suite 與具名撤回。瀏覽器執行使用隔離 loopback 服務、獨立 TEMP feedback、專屬 Chrome profile。
2. `Native suite measurement`：suite=`node:d09_override_discovery`。取得官方 ZIP 原件，沿 `FRAGMENTED-REGISTRIES.md` 的 `--import-suite` 產生 stage，原樣採入。
3. `Canvas section measurement`：section=`P4549`。下載官方原 ZIP 後執行 `python3 tests/diagnostics/d09_discovery_registry.py import-canvas --artifact-id ID --artifact ORIGINAL.zip`。這只轉呼叫正式 `canvas_registry.js import-cost`；真 count/cost 由原件決定，沒有自訂 golden 寫入器。
4. 真冷開：設定 `GEOMETRY_TEST_URL`、`GEOMETRY_FEEDBACK_DIR`、`GEOMETRY_D09_DISCOVERY_EVIDENCE`、`GEOMETRY_CHROME` 及專屬 `GEOMETRY_CDP_PORT`，執行 `node tests/integration/d09_override_discovery_browser.cjs`。driver 要求非預設 loopback port、checkout 外新證據目錄，拒絕污染現有證據。保留完整 `results.json`、stdout、所有首屏 PNG／JSON 和 `.gcanvas`。
5. 導入後跑 registry contract、原生六片、canvas 兩片與 complete coverage。P4549 固定原新 module 尾 slot；本片不申請 auto balance，不改兩片分界。新增 architecture exclusion 只指名這支測試 module；產品來源原本的 H 登錄不變。

L4 操作路徑：檔案 → 試用工程規格現成專案 → 本面縫寬 literal 4 → 預覽／取消（World 與歷史不變）→ 再預覽／核對／確認 → 復原／重做 → 保存 → 關閉瀏覽器 → 390 實機／桌面各開檔 → 檔案／工程規格。先不滾動，核對頂部已套用覆寫摘要與 4 mm；展開摘要，按檢視後確認欄位可讀、焦點及全控制未被 footer 擋。未編輯預覽是 0 項變更，取消無寫入。手機真觸控與作業系統原生 picker 不由 headless CDP 代證。

本片交付只增加 D09 的可驗證實作與驗收碼，目前是未採入的候選補丁。待真 Chromium／正式 CI 通過並正式採入 main，才可把這一片記為 L3；L4 仍須上述實機路徑。它不將 R16 全 43 項一併升級或宣稱全數完成。

## v3：公開失敗的修正與重新交付

本次完整 T／P 基底為 `48d5f3887e8cb8d222307db62dbdea287fda8442`。這是依公開原件重新建出的 v3，取代中斷索引
7175906485 的 D09 補丁宣告；不沿用該則未交原件的 bytes、雜湊或實跑數字。
上文 v1／v2 的數字是歷史紀錄；本次原始輸出與新指紋在交付索引。

7174254721 的冷開失敗成立：欄位下緣 751.8125 超過有效裁切下緣 751.640625，
差 0.171875 px。`nearest` 加上整數 scrollTop 可能原地不動；五點命中不等於整個欄位完整顯示。
只在使用者明示檢視時，把同一欄位的 block 位置改為 center；inline nearest、preventScroll 焦點、
既有展開與零寫入保持。不是在冷開自動捲動，也不改任何裁切容差。

新增一項 test 執行真正 handler，在報告座標及 128 個 1/128 px 分數位移上獨立計算整數捲動後的完整裁切。
v3 T 配 v2 P 時，`D09_DISCOVERY_REVEAL_STRICT_CLIP` 具名紅；v3 P 時 Node 12 項全綠。
第八項撤回 `D09_DISCOVERY_RESTORE_NEAREST` 必須回到這個指定 assertion；裁判從同一失敗子測試的
error 與 ERR_ASSERTION 判讀，不從整份輸出搜尋字串。P4549 與真正冷開 driver 保留 v2 原 bytes，
嚴格完整裁切、五點 hit、固定預算與既有 golden 都不改。本機幾何模型不是 Chromium 的完成證據；
390／1400 冷開及正式成本仍待雲端實跑。
