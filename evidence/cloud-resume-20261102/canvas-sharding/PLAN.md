# Canvas 拆片：單輪靜態前置方案

2026-11-02；固定讀取 `/tmp/geometry-pr366-20261102`，HEAD `502a64ff6214dd6060927b7f14643a533536f20d`，來源乾淨。這是待 root 審閱的實作方案，沒有改 cdp_test.js、workflow 或產品，沒有啟動瀏覽器／CI、重跑已綠測試或解封歷史證據。root 看過後才進入實作；不是要求使用者另行確認。

## 重複工作檢查

GitHub API 單輪只讀：28 個 open PR（完整一頁）與 237 個 live branches（100／100／37，三頁）。檢查 title／head／body 的 canvas＋shard／split／拆片／分片配對，及分支名稱 canvas／cdp／shard／split／browser／wait-trace，未識別既有 canvas sharding PR 或命名分支。命中的 `codex/native-shards-20261102` 是已知原生拆片；其餘為 2026-10-06／07 的 browser followup 和 #352 物件 canvas 功能。這是目前可見 metadata 的有界查重，不宣稱排除藏在無關名稱內、未發 PR 的私人工作。

#363 仍是活躍產品來源（本輪 API head `9367dbe9993cfeb6fed687fa55656d7d25eb5936`）；現在不在其來源上競寫。實作開工時由 root 指定乾淨基準，再重新核對本方案列出的四個 source hash 與原 golden；不能把本輪 502 的行號／計數直接移標到後續 head。

讀取 API：`GET /repos/ZhiQiYang/geometry-axiom/pulls?state=open&per_page=100`、`GET /repos/ZhiQiYang/geometry-axiom/branches?per_page=100&page=1..3`，urllib 保持 session proxy／TLS，exit 0。沒有 poll 舊 #366 run。

## 最小首版：兩個真正的執行分支

先保留 legacy 內部整條 stateful 流程；只把後方已具獨立 fixture 的外掛鏈分離。這是第一個低改動切點，不承諾耗時已平衡或一定縮短到某時間。898／1369 是現有 golden 的投影，不是新門檻或效能估計。

| 片 | 原執行範圍與順序 | 既有 golden 投影 |
|---|---|---|
| `legacy` | `cdp_test.js:403–7122` 內 Setup、1–10、P3–P66 既有本體及 BF 段，全留原順序 | 62 keys／898 assertions |
| `extensions` | `cdp_test.js:7123–7158` 外掛呼叫鏈，全留原順序；P83→P86 綁同片 | 23 keys／1369 assertions |
| 聚合 | 完整原 golden，section keys 精確不交且聯集全等 | 85 keys／2267 assertions |

**上表是責任範圍，不是可直接剪貼成函式的字串區間。** 現有外層 if 跨包部分外掛。最小實作應保留原 lexical scope，在現有三個本體 gate `cdp_test.js:401、3591、6308` 增加明確 `ownsLegacy` 路由，再把 `:7123–7158` 的外掛呼叫改由單一註冊表選擇。不要移動 P34/P35 的 const 或破壞後段閉包。full 舊入口仍走同一批原陳述式；新 shard 入口在進入 unit 前選擇，未擁有的測試 unit 根本不執行。

共用的只有 `:366–397` bootstrap：連線到本片新 Chrome、啟用 CDP、transport trace、固定 viewport、fetch／DOM settle instrumentation、等待 app ready，以及 `:1–332` 原 helpers。每片用自己 runner/server/bridge、profile、CDP port、feedback/temp/download/screenshot 目錄；先保留原 workflow 的 `npm run build`、runtime fresh probe、Chrome ownership、清理與 canvas wait-trace。原 browser job timeout 35 分鐘、既有所有 wait／poll／sleep timeout 不改，不增加數值地板，不以加大 timeout 掩蓋問題。CI 各 job 原本已有獨立機器；本地不得同時跑兩個 canvas/perf 重工作。

現有獨立 assembly／grid／documents／space／timber jobs 保留原責任；不能把已跑的 partial job 冒作本次 canvas 互斥片。只替換 canvas 那一支及新增其完整聚合 job。`extensions` 仍執行原 full 所包含的 assembly／grid，以保存原 85 段契約。

## 為何不直接拼現有 partial

`runConfiguration:11–28` 只允許單一 scope flag；`evaluateSections:333–362` 對 partial 明確不驗 golden。`REPAIR_ONLY`、`FLOW_REPAIR_ONLY`、`REFERENCE_ONLY`、`CDP_FROM_P31` 仍可能落入 P68／P69／P67（`:7123–7128`），所以它們不是互斥片。P83／P86 更只有 full 入口（`:7157–7158`）。不能把多個旗標疊起來、沿用 partial 綠燈或更改 receipt.mode 假裝完整。

新 `shard` scope 應和 legacy partial/full 分開：固定已知 shard ID／plan digest，拒絕未知／空 ID、所有舊 SCOPE_FLAGS、engineering modifiers、`GEOMETRY_CDP_UPDATE_GOLDEN`。原 full 和 partial 使用方式保持；shard 每片直接與**同一個原 golden 的擁有 section 投影**比對，聚合再用原 `cdp_floor.compare` 對完整 golden 嚴格比較。不得把原 exact count 改成 min，不重產 golden。

section key 必須由原 `cdp_floor.sectionOf:18–25` 判定，不能用 P 數字範圍推論：P22 bucket 包含沒有新標頭的 P23–P31；P53 包含 P54–P56；P57 包含 P58–P61；P73B 歸 P73，只有 P72B 特別獨立。Setup／8／10 的零 assertion keys 也要有真 section 進入事件，不能只以總數通過。

## 已識別的 state／fixture 邊界

| 範圍 | 原依賴與處理 |
|---|---|
| `cdp_test.js:403–768` | 初始 reset／boundary:1／卡片位置／拖曳／focus／undo/redo 是連續場景；首版不在內部切。 |
| `:3591–6306` | 保留原 block；P35 的 `feOrigin/clickFacePoint/enterFaceRedraw` 被 P36 使用（`:4039–4050,4197`）；P40 用 P34 `emptyWorld/ocOrigin`（`:3953–3960,4472`）。 |
| P48–P52 | `setupLinesG196` 在 `:5404`、`F_SUPPORT` 在 `:5485`，後段在 `:5645,5934,6076` 重用；若第二輪才細切，須抽真正 fixture 定義，不能重跑前段測試當暖身。 |
| P53／P57–P61 | `:6308–6482` 含 reload／fetch 故障與還原；`:6483–6695` 共用 PDF、g198Saved/g198Dump、回執及歷史。首版整組保留。 |
| P38 例外 | `:4399–4417` 刻意 `fb-auto-probe`；保留原 expected 例外與各組相對 counter 語義，不能新要求所有片 counter=0。 |
| P83→P86 | `model_snapshot_schedule_test.js:58–65` 產生真模型與 `__p83.archive/ids/originalApi/line`；`model_snapshot_navigation_test.js:1,11–15` 直接使用。首版同片同順序，不重跑 P83、吞其 16 assertions 為 P86 暖身。 |

下列 partial 可作為「既有獨立 fixture」的來源依據，但新 `extensions` 初版仍保留整條原順序；沒有斷言它們已動態驗成新 shard：

| 既有群入口 | 不能拆散的群與 source anchor |
|---|---|
| PROJECT_AUDIT_ONLY | P68；`project_audit_test.js:34–35,54` 自有 reset，先建自己的兩面。 |
| ENGINEERING_WORKFLOW_ONLY | P69 完整流程與 grid-material 子鏈；`:133–164` 三個 modifier 提早 return，不能代替完整群。 |
| MARQUEE_ONLY | P67；`marquee_test.js:31–32,68` 自有 reset。 |
| GRID_SYSTEM_ONLY | P70→P71→P78→P87→P88；`grid_system_test.js:66–68,335–336` 自有 reset 及巢狀載入。 |
| COMPOSITION_ONLY | P72→P72B；`composition_canvas_test.js:41,47` 自有 fixture，保持更名鏈。 |
| UIUX_FIX_ONLY | P73 含 P73B；`uiux_review_test.js:242` 巢狀 grid workspace draft。 |
| UX_REFINEMENT_ONLY | P74；含真 IndexedDB／reload，保留整組。 |
| SELECTION_CURSOR_ONLY | P75；`selection_cursor_test.js:32–35` 自有 fixture。 |
| PARAMETERS_ONLY | P76；`parameter_workflow_test.js:359–360` confirmation／preview ownership。 |
| ASSEMBLY_ONLY | P77→P82；`assembly_workflow_test.js:80–83` review／ID／generation／candidate-impact 不省。 |
| TIMBER_SCHEDULE_ONLY | P80→P81→P85；保留 default／原件 import fixtures；`source_navigation_test.js:18,54` 原 archive setup。 |
| ROOM_OUTLINE_ONLY | P79→P84；`room_outline_test.js:251` 將 setup／校準／來源 helpers 傳給 P84，保持同群。 |
| 無現成 flag | P83→P86；保持 producer 與 consumer 同片。 |

## 每片真執行收據與聚合裁判

新增小型純註冊／核驗模組，不把 shard 變成 per-assert filter。註冊原 units、source anchors、ownership sections 與原 golden hash；展開後斷言每個 full unit／85 個 keys 恰有一個 owner。`legacy` 中三個原 block 可記子 unit begin/end，但全歸同片；外掛使用原順序／巢狀呼叫，P83+P86 為不可拆 dependency group。

每片保存原 stdout/stderr、實際 process exit、唯一且 completed 的 CDP_RESULT、unit begin/end／section begin／**受控 assertion** journal、section counts、unexpected/expected 例外資料、runtime probe 原輸出、checkout SHA／tree、runner+helper+plugin/include fixture source closure、golden/plan SHA-256、run ID／attempt、shard ID 與實際 scope。journal 在原受控 verdict 路徑 `recordLog:137–149` 產生，不能從摘要反推；用 unit/section/ordinal 識別實際 assertion occurrence，保留 raw label 和 site 資訊便於查核，不把任意 diagnostics 的 ✓ 當 assertion。

聚合只下載**本 run/attempt** 的兩片官方原件，逐一驗 API artifact digest／manifest raw hash，拒絕重複鍵、缺片／重片／未知片。要求相同預期 source/runner closure、真正 checkout execution SHA（PR synthetic merge 另記 head/tree 對應，不能改字串）、run/attempt、plan/golden 原件；本次只接受完整成功 jobs、process exit 0、completed=true、無 fatal、原 skip 契約不變。從 raw/journal 重算 section 與 assertion occurrence，不只信總數：owned unit 完整 begin/end、沒有 unowned unit/section/assertion、沒有重複 occurrence、每個零數 key 也實際進入。兩片 section keys 必須不交且聯集逐 key 等於原 golden；逐 section 套原 exact count，然後完整原 `floor.compare`，總數等於原各段之和。summary 只能在這些檢查全過後產生。

這個模型依賴可追溯官方 source/job/raw；本地 manifest 自洽不能認證自行偽造整份輸出的人。沿用 #366 的教訓：run/attempt/probe 等核驗必須在 verifier 明確實作，不留成只寫在 manifest 的欄位。

## 具名負控制（實作後驗；本輪未跑）

| ID | 具體破壞與必須拒絕的理由 |
|---|---|
| CANVAS_MISSING_SHARD | 移除 extensions 原件：明確缺片／缺 23 keys，exit 非 0。 |
| CANVAS_DUPLICATE_SHARD | 提供兩份 legacy：重 shard ID／重 unit／重 sections，不能用總數湊綠。 |
| CANVAS_WRONG_HEAD | 換 receipt 的 execution SHA 或 source closure：與預期 checkout/tree/job 原件不符。 |
| CANVAS_WRONG_RUN_ATTEMPT | 同 head 另一 run/attempt 片混入：明確 provenance 拒絕。 |
| CANVAS_GOLDEN_CHANGED | 改 golden bytes、少／多一個 key，或把 exact 改 min：原 hash／原契約拒絕。 |
| CANVAS_ZERO_SECTION_DROPPED | 移除 Setup／8／10 任一真 section 事件但保留相同總數：missing key/event 拒絕。 |
| CANVAS_COUNT_DRIFT | 對 owned 段少一個或多一個受控 assertion：原 floor 的 changed 拒絕。 |
| CANVAS_FAKE_SCOPE | shard 同開 *_ONLY/FROM_P31/modifier 或冒稱 full/partial、未知片：preflight／receipt scope 拒絕。 |
| CANVAS_FAKE_SUMMARY | exit 0 或假 totals，但缺 completed/journal/raw、或 raw verdict 與 summary 不同：拒絕。 |
| CANVAS_UNOWNED_EXECUTION | 故意讓 legacy 片也執行 extension unit，再藏其摘要／assert：原 unit/section/raw journal 指出 unowned execution；不能計成拆片。 |
| CANVAS_ASSERTION_NOT_MASKED | 在 owned unit 把一個既有 check 故意判 false：真正 assertion failure＋process exit 1，恢復後 0；不能是 timeout/error/skip 充當 killed。 |
| CANVAS_P86_WITHOUT_PRODUCER | 拿掉 P83 group 但讓 P86開始：具名 fixture 缺失／完整依賴 group 拒絕；不得私下執行 P83再藏數。 |

實作驗收還需確認無 shard 時原 full routing／原 golden 語義不變；純 verifier 負控制先跑，真正新兩片再依 root 排程跑一次，下載官方原件核精確聯集。這些未完成前只能稱 plan，不稱 canvas 拆片已完成或效能改善已證明。

## 本輪邊界與交付

只新增本 PLAN 與 `plan.json`，總量小於 30KB；沒有改動任何 source。git／rg／必要區間讀取及 golden 純資料加總均 exit 0；未做大掃描、archive 重封、產品動態執行或 CI。四個 source 原件 SHA-256、分片 section 清單及未驗項保存在 JSON。下一步由 root 審閱此最小切點，再決定開工來源；不因 #340/#363 正在變動而追著改 SHA。
