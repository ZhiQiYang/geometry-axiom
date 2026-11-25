# 根因診斷：R03 確認骨架後，角材在物件畫布與面內看不到（2026-11-26）

任務：issue #455 留言 7169923545（T6）。範圍是診斷，**不修產品、不改測試**。
基底：main `b3c4b981bb96b118c1c05b7a1bd98062d710c8b2`（乾淨工作樹 `git worktree add --detach`，跑完 `git status --short` 0 行）。

## 結論（先看這裡）

#449 列的六個症狀**不是同一個根因**。共有三個根因，另有兩項跟派生宿主無關，是一般畫面本來就沒有的呈現功能：

| 症狀 | 錯誤值 | 根因 | 取不到的確切位置 |
|---|---|---|---|
| S1 宿主卡尺寸 | `1×1 mm`（副標「自帶矩形 · 無邊界」） | **A** | `geometry-web/web_bridge.c:847-860`：`cmd_objects` 對 `boundary_id==0` 的 placement 一律輸出 `p->rect`；派生宿主的 `rect` 是全 0（`geometry-core/derived_placements.inc:15` 寫入時 `PlacementSurface p={0}`，幾何只放在 `components[]`）→ `objects.faces` 的 bbox `[0,0,0,0]` → `geometry-web/app.js:2352` `Math.max(1, …)` → `app.js:2379` 顯示 1×1；副標寫死在 `app.js:2322` |
| S2 檢查器外框尺寸 | `0 × 0 mm` | **A**（與 S1 同一筆資料） | 同上的 bbox；`app.js:10025` 直接相減，沒有 `Math.max`，所以是 0 |
| S3 面 1 面內看不到角材（及主格） | 「尚無角材」、0 個命中點 | **B** | `app.js:3318` `feSurf(1)` 只找 `surfaces[].boundary===1` 的 placement → 1；`app.js:4733`／`4737` 用這個 sid 過濾 `references` 的角材與網格。53 支角材與 from-fill 主格都在 placement **2**；`surfaces` 回 placement 2 的 `boundary:0`（`web_bridge.c:669`），沒有任何欄位把它連回面 1 |
| S6 宿主卡無法進入面內 | 「進入面內工作區」停用 | **B** | `app.js:10089`（kind 為 placement 一律停用，title「placement 面沒有邊界可編輯」）；清單雙擊 `app.js:9887`、`openCanvasObject` `app.js:10243` 同樣拒絕 |
| S5 X 參數卡 | `0 處使用` | **C** | `parameters.js:53-58` `usage()` 只看參數卡互引、網格系統 parameterRefs 與 `oc.parameterUses`（`app.js:2537` ← `objects.parameterUses` ← `web_bridge.c:930` `json_parameter_uses`）。`geometry-web/parameter_bridge.inc:6-48` 沒有列舉 panel-fill 的 gap／stagger／threshold。核心的 `parameter_uses`（`geometry-core/parameters.inc:550-557`）**有**列 panel-fill，所以是橋接層另寫的第二份清單漏列 |
| S4 物件畫布看不到角材 | 0 個角材元素 | **D（非派生宿主問題）** | 物件畫布三個繪製函式 `faceCard`（`app.js:2308-2380`）、`renderObjects`（`app.js:2515-2571`）、`drawObjects`（`app.js:2574-2685`）完全不引用 timber。**一般承載面上的角材在物件畫布也看不到**（對照組實跑：`demo-two-timbers.scene` 面 1 有 5 支角材，物件畫布 0 個角材元素） |
| S7 三視圖選取只寫「角材 N」 | `角材 3` | **D（非派生宿主問題）** | `app.js:1105` 選取說明只用 owner 種類與 id，任何角材都一樣；`references.timbers[].geometry` 已有 length／A／B，但這裡沒用 |

- **A 與 B 是不同根因**：修好 bbox（A）不會讓面 1 看到角材，也不會打開進入鈕；修好 B 也不會改卡片尺寸。
- **A、B、C 的原生資料都完整**：`panel-fill-read` 有派生宿主的有效區域（外接 `[266,244,4006,3545]`）；`references`／`objects.timbers` 有 53 支角材、真 surface 2；`panel-fill-read` 的鋪排 1 有 `threshold {parameterId 1, fieldId 1}`。缺的是**橋接層輸出**（A、C）與**前端導覽**（B），不是生成或保存。
- 載入同一份場景的全新 bridge 行程（等同原生冷開）得到相同錯誤值，所以這些錯誤值不是 session 暫存狀態造成的。
- B 也解釋 R02 PF-4A L4 的「發現 2」（主格建立後面內看不到）：from-fill 主格同樣掛在派生宿主（`grid 1 on 2 from-fill 1`），被 `app.js:4737` 濾掉。本次只在原生資料與 R03 場景確認，沒有另走 PF-4A 的 UI。

## 1. UI 重現（只經 UI）

- 服務：`scripts/serve-wt.sh /tmp/wt 18891 $TMPDIR/fb`（沿用 `evidence/l4-cloud-20261122r03a/scripts/serve-wt.sh`：非 root、`ulimit -s 16384`、`LANG=C.UTF-8`、Node v24.22.3、回報目錄在 `$TMPDIR`）；`start_local.py --build-only` 建出 core／bridge／model-base 後 `start_local.py --port 18891`。
- `runtime_version.py --probe 18891`：`version b4814c2e…1f5c`、`fresh:true`、root `/tmp/wt`、pid 3238、session `69c337ca…`（`ui-run/runtime-probe.json`）。
- 瀏覽器：Google Chrome 158.0.8127.36（`/usr/bin/google-chrome`，headless、`--no-sandbox`），playwright-core 驅動，視窗 1400×900，新 profile。
- 腳本 `scripts/walk_repro.js`（由 #449 的 `walk_r03a.js` 第一階段刪減而成；`lib.js` 只改預設 port、`ui.js` 原樣複製）。輸入只有滑鼠與鍵盤；`page.evaluate` 只讀畫面、送唯讀查詢、讀前端變數。
- 和 #449 腳本的差異：基底版面左側多了工具列，原本的拖曳起點 (400,250) 落在工具列上，改為 (700,300)。另外只走主路徑，不走取消、可讀性與拒絕例。

操作路徑：檔案 → 新專案 → 工具列「矩形面」拖出 → 右欄「外環邊 · 尺寸確認」打 3740／3301 → 放置原點 0／0／2500、u +x、v +y → 雙擊面卡進面 → 屬性 → 面設定… → 完成面／骨架… → 面內工作切「平釘天花骨架（政策 A 固定治具）」（`modePath finish → framing → framing-fixed`）→「準備板材來源」在工程規格建 915×1830×6 面材 → 「獨立建立 8 mm 門檻 X」→ 保存 v2 配方（915／1830／2／27／33／367、左上、板長沿 v）→ 明選框架「放置面 1」、板材、X、勾 RC →「預覽整組骨架」→「確認骨架（一筆歷史）」→ 關閉 → 一般畫面（物件畫布、選宿主「承載面 2」、清單雙擊宿主、面 1「進入面內工作區」、三視圖點角材 3）→ 檔案 → 另存新檔…（`ui-run/r03-fixed.gcanvas`）→ 檔案 → 匯出場景檔…（`ui-run/r03-fixed.export.scene`）。

原始輸出（`ui-run/walk_repro.log`，全文）：

```
STEP 1-rect {"lines":["boundary 1 outline 266,244 4006,244 4006,3545 266,3545","placement 1 on boundary 1 origin 0 0 2500 u +x v +y"]}
STEP 6-preview {"head":"候選 53 支 · 確認前未寫入"}
PASS PREVIEW_53 
STEP 7-confirm {"status":"骨架已整筆確認為一般正式物件；配方不擁有物件，冷開不重新搜尋。","undoDelta":1,"kinds":{"spec":8,"requires":1,"finish-surface":1,"panel-fill":1,"derived-placement":1,"grid":1,"timber":53,"guide":8,"place":53,"#":53,"canvas-pos":1}}
PASS CONFIRM_ONE_HISTORY_53_TIMBERS 
PASS VIEW_ZERO_WRITE 
PASS SOURCES_READ_ZERO_WRITE 
PASS SAVE_EXPORT_ZERO_WRITE 
STEP 9-save {"gcanvas":[12182,"a10f6fa81c3dc5dfe8923c0542f74f62465f824bdbe1b0eade0c9e97840df461"],"exportScene":[10323,"44268b235b12201b874dd78bf784909af847de210273e57d4bede4dd8c967597"],"dumpScene":"44268b235b12201b874dd78bf784909af847de210273e57d4bede4dd8c967597"}
SUMMARY 5 / 5 ALL PASS
```

結束碼 0。匯出的 `.scene` 與確認後的 `dump` 逐 byte 相同（SHA-256 同為 `44268b23…7597`，也存為 `ui-run/r03-fixed.dump.scene`）。

UI 上讀到的錯誤值（`ui-run/walk_repro.result.json` 的 `view`，截圖在 `ui-run/screens/`）：

| 畫面 | 讀到的值 |
|---|---|
| 宿主卡（`R-V-2-host-selected.jpg`） | `承載面 2 · 自帶矩形 · 無邊界 · 無邊界 · 1×1 mm · 4 頂點` |
| 宿主檢查器 | `外框尺寸 0 × 0 mm`；`#inspEnter` `disabled:true`、title `placement 面沒有邊界可編輯` |
| 左欄參數列／卡 | `鋪排承接門檻 · 1 個欄位 · 0 處使用`；`ParameterUI.usage(1)` = `[]` |
| 面 1 面內（`R-V-3-face1.jpg`） | `feSid(1)=1`、`fe.timbers.length=0`、0 個 `t:` 命中點，左欄「角材 · 尚無角材 · 設定並放置」 |
| 物件畫布（`R-V-1-object-canvas.jpg`） | 0 個角材元素 |
| 三視圖（`R-V-4-three-view.jpg`） | 53 個 timber owner；點角材 3，`#v3PickInfo` = `角材 3` |

同一時間的唯讀查詢（`sources`）：`objects.faces` placement 2 `bbox [0,0,0,0]`；`surfaces` placement 2 `boundary 0`；`references` 角材 `{2: 53}`、網格 `{2: 1}`；`objects.parameterUses` `[]`；`panel-fill-read` 派生宿主 2 的 `components[0].outline` 是 `(266,244)–(4006,3545)`，鋪排 1 `threshold {parameterId 1, fieldId 1}`，派生宿主 `h` 是字面值 33。

### 對照組（一般承載面，只經 UI）

`scripts/walk_control.js`：檔案 → 開啟場景檔…（repo 根目錄 `demo-two-timbers.scene`）→ 面 1「進入面內工作區」。原始輸出（`ui-control/walk_control.log`）：

```
{"objectCanvasTimberElements":0,"face1Sid":1,"face1FeTimbers":5,"face1TimberHits":5,"readOnly":true}
```

結束碼 0。一般宿主的角材在面內看得到（5 支），但物件畫布同樣是 0 → S4 不是派生宿主造成的。

## 2. 不經 UI 的只讀診斷

- `minimal-derived-host.scene`（19 行、1792 B、SHA-256 `c1bcbbc2031ea7e7af2641e47f667aa8aecff1bbf4a79e0848d5459aac6b69e2`）：由 `scripts/make_minimal.py` 從 UI 匯出的場景**只刪行**得到（刪角材 2–53 與其 place、R18 註解、記號用 spec／guide），不新增也不改寫任何一行。保留角材 1（邊界材，`place 1 on 2 at-face key-hex… between …`）。
- `scripts/diag_derived_host.py`：每個場景各起一支新的 bridge 子行程，`loadfile` 後只送 `dump`、`objects`、`surfaces`、`references`、`panel-fill-read`、`dump`，並要求前後 dump 逐字相同；用與 app.js／parameters.js 相同的運算式重算 UI 值；程式位置以原文片段搜尋得出（找不到就標 MISSING）；`--ui-result` 時與真 Chromium 讀到的值逐項比對。

命令（在 repo 根目錄執行；bridge 是 `start_local.py --build-only` 建出的那支）：

```sh
python3 -I evidence/diag-derived-host-20261126/scripts/make_minimal.py \
  evidence/diag-derived-host-20261126/ui-run/r03-fixed.export.scene evidence/diag-derived-host-20261126/minimal-derived-host.scene
python3 -I evidence/diag-derived-host-20261126/scripts/diag_derived_host.py --bridge <bridge> --repo /tmp/wt \
  --ui-result evidence/diag-derived-host-20261126/ui-run/walk_repro.result.json \
  --ui-scene evidence/diag-derived-host-20261126/ui-run/r03-fixed.export.scene \
  evidence/diag-derived-host-20261126/ui-run/r03-fixed.export.scene \
  evidence/diag-derived-host-20261126/minimal-derived-host.scene demo-two-timbers.scene > evidence/diag-derived-host-20261126/diag-output.json
```

`make_minimal.py` 輸出：`ui-run/r03-fixed.export.scene: 192 lines -> minimal-derived-host.scene: 19 lines`。
`diag_derived_host.py` 結束碼 0，`"ok": true`；完整輸出是 `diag-output.json`。摘錄（每個場景的原生欄位）：

```
ui-run/r03-fixed.export.scene  readOnly true
  objects.faces  [{"kind":"boundary","id":1,"bbox":[266,244,4006,3545]},{"kind":"placement","id":2,"bbox":[0,0,0,0]}]
  surfaces       [{"id":1,"boundary":1},{"id":2,"boundary":0}]
  references     timbers {2: 53}  grids {2: 1}
  objects.parameterUses []   panelFillRefs [{"id":1,"threshold":{"fieldId":1,"parameterId":1}}]
  derivedPlacements [{"id":2,"definition":{"fillId":1,"h":33,"id":2},"componentBboxes":[[266,244,4006,3545]]}]
minimal-derived-host.scene     readOnly true
  objects.faces  [{"kind":"boundary","id":1,"bbox":[266,244,4006,3545]},{"kind":"placement","id":2,"bbox":[0,0,0,0]}]
  surfaces       [{"id":1,"boundary":1},{"id":2,"boundary":0}]
  references     timbers {2: 1}  grids {2: 1}
  objects.parameterUses []   panelFillRefs [{"id":1,"threshold":{"fieldId":1,"parameterId":1}}]
  derivedPlacements [{"id":2,"definition":{"fillId":1,"h":33,"id":2},"componentBboxes":[[266,244,4006,3545]]}]
demo-two-timbers.scene（對照）  readOnly true
  objects.faces  [{"kind":"boundary","id":1,"bbox":[0,0,4000,3000]}]
  surfaces       [{"id":1,"boundary":1}]   references timbers {1: 5}
```

重算的 UI 值（兩份 R03 場景相同；最小場景角材數為 1）：S1 `1×1 mm`（真外接 `[266,244,4006,3545]`）、S2 `0 × 0 mm`、S3 `feSid 1`、面內角材 0、網格 0（別處：surface 2）、S5 `0`（真引用：鋪排 1 threshold）、S4 0、S6 停用、S7 `角材 <id>`。對照組 S3 面內角材 5。

與 UI 實讀逐項比對（`diag-output.json` 的 `uiComparison`，全部 true）：S1 卡片文字含 `1×1 mm` 與副標、S2 檢查器含 `外框尺寸\n0 × 0 mm`、S3 feSid 1＝1、角材 0＝0 且左欄「尚無角材」、S4 0、S5 `0 處使用`＝`usage(1).length`、S6 停用、S7 `角材 3`。

`sourceLocations`（片段搜尋結果，皆唯一命中）：`current_geometry.c:332`（rect 只在 boundary_id==0 時有效的註解）、`:341`（`derived_fill_id`）、`derived_placements.inc:15`、`web_bridge.c:847`／`860`／`669`／`930`、`parameter_bridge.inc:6`、`parameters.inc:556`、`app.js:2537`／`2308`／`2322`／`2352`／`2379`／`10025`／`10089`／`3318`／`4733`／`4737`／`1105`／`9857`、`parameters.js:53`／`57`／`69`。

## 3. 各畫面的取值路徑

1. **物件畫布卡片／檢查器尺寸**：`renderObjects`（`app.js:2515`）→ `api("objects")` → `oc.faces`。bridge `cmd_objects` 在 placement 迴圈（`web_bridge.c:847-860`）只略過 `boundary_id!=0`，然後用 `p->rect` 當 bbox。派生宿主（`derived_fill_id!=0`）的 `rect` 在 `app_dp_write`（`derived_placements.inc:15`）寫入時就是 0；它的有效區域在 `components[]`。同一個函式後半段算角材屬性時用了 `placement_effective_boundary`（`current_geometry.c:413-425`），那個函式會處理派生宿主，但 faces 這段沒有用它。`cmd_surfaces` 也一樣，只輸出 `boundary`（0），沒有派生標記或來源。
2. **面內角材／網格**：`enterFocus('face', 1)` → `feLoadGuides`（`app.js:4719`）→ `feSid(1)`（`app.js:3315-3319`：只認 `boundary===bid` 的 placement）→ `references` 依 `geometry.surface===sid` 過濾（`app.js:4733`）、網格依 `surface===sid` 過濾（`4737`）。派生宿主和來源面在前端沒有關聯資料，派生宿主本身又不能當面開啟（`app.js:10089`、`9887`、`10243`；`enterFocus` 的 face 分支也要求 `boundary <id>` 成功，`app.js:2936-2943`）。
3. **參數「N 處使用」**：`parameters.js:69` 卡片與 `app.js:9857` 左欄都用 `ParameterUI.usage(id).length`。`usage()`（`parameters.js:53-58`）＝參數卡互引＋`oc.gridSystems` 的 parameterRefs＋`oc.parameterUses`。`oc.parameterUses` 只來自 `json_parameter_uses`（`parameter_bridge.inc:6-48`），它列：工程綁定（角材／網格 A、B）、組構配置槽位、參考線／基準面運算式、網格系統卡片引用。核心 `parameter_uses`（`parameters.inc:503-566`）另外還列：網格系統軸參數（前端用 gridSystems 補了）、非系統網格應用的軸參數（`parameters.inc:547`）、**panel-fill gap／stagger／threshold（`550-557`）**、斷面輪廓成員與跑段（`558-565`）。後三類在 UI 端都沒有來源。這段只依程式碼閱讀，本次只實測了 panel-fill threshold。
4. **物件畫布上的角材**：沒有取值路徑。三個繪製函式都不引用 timber，`renderObjects` 也沒有讀 `objects.timbers`（`objects.timbers` 只有 id／surface／role 等屬性，沒有幾何）。
5. **三視圖選取說明**：`pickAt`（`app.js:1097-1105`）只用 `target.root.kind/id` 組字串。

## 4. 對照 ChatGPT 工作包 A 設計（issue #205 留言 7169635026）

逐列核對它在「各畫面的資料路徑」表的根因說法：

| 它的說法 | 核對 |
|---|---|
| 宿主卡 1×1、檢查器 0×0：`cmd_objects` 把 `boundary_id==0` 一律當自帶 rect，讀到零 rect；卡片 `Math.max(1,…)`、檢查器直接相減；同一漏讀 | **正確**。補充：零 rect 的來源是 `derived_placements.inc:15`；同一函式的 timbers 段已用 `placement_effective_boundary`，faces 段沒有 |
| 物件畫布沒有骨架：卡片沒有繪製宿主上角材的路徑，不能靠修 bbox 補出 | **正確**。補充：一般承載面也一樣（對照組實跑 0 個元素），所以這是一般畫面本來就沒有的功能，不是派生宿主的缺陷；要不要做是需求與設計問題（它放在 A2，合理） |
| 來源面面內沒有骨架／PF-4A 主格：`feSurf` 只找 `boundary==bid` 的普通 placement，再按 sid 過濾 | **正確**（`app.js:3318`、`4733`、`4737`；R03 場景實測網格也被濾掉） |
| 派生卡無面內入口：雙擊／清單／檢查器對 placement 一律拒絕 | **正確**（`app.js:10089`、`9887`、`10243`）。UI 實測只確認檢查器按鈕停用；清單雙擊的狀態訊息本次沒讀到（腳本只讀 `role=status` 元素），以原始碼為據 |
| X「0 處使用」：`json_parameter_uses` 沒列 panel-fill；核心 `parameter_uses` 已有 gap／stagger／threshold；派生宿主 h 的 `ENG_PARAMETER` 不在 engineering.bindings，同樣漏列 | **前兩點正確**（`parameters.inc:550-557`）。h 那點依程式碼成立（`derived_placement.c:17-18` 允許 h 是參數來源；`json_parameter_uses` 沒有掃 `finish_surfaces.hosts`），但 R03 的 h 是字面值 33，**本次沒有實測**。另外，核心 `parameter_uses` 也沒有掃派生宿主 h；刪除參數欄位時有沒有別的守門會擋，本次未查 |
| 選角材只有「角材 N」：選取描述沒有共用的角材尺寸摘要 | **正確**（`app.js:1105`），而且所有角材都一樣，不限派生宿主 |
| R03 預覽表 3247 折行：獨立元件 CSS | 不在本次範圍，未核對 |

整體判斷：它把六個症狀分成「bbox 漏讀」「面內導覽」「參數清單」與「本來沒有的呈現功能」，與本次實跑一致，沒有發現說錯的根因。要補的只有：S4、S7 在一般宿主上也成立；`json_parameter_uses` 和核心清單之間還差非系統網格應用與斷面輪廓兩類（依程式碼閱讀，未實測）。

## 建議（最小修正方向，給工作包 A 參考）

1. **A（S1、S2）**：只改 bridge 輸出。`cmd_objects` 的 placement 迴圈遇到 `derived_fill_id!=0` 時，bbox 改由 `components[].outline` 的聯集求得（與 `panel-fill-read` 的 derived components 同一份資料），並另外輸出派生標記（例如 `derivedFillId`）；`components` 為空時明確輸出空範圍，不要給 `[0,0,0,0]`。前端卡片副標（`app.js:2322`）、清單（`app.js:9821`）、三視圖標籤（`app.js:1015`、`1105`）依這個標記改用「派生宿主」字樣。這一項不需要動核心資料或場景格式。
2. **C（S5）**：`json_parameter_uses` 補一段 panel-fill 迴圈（照 `parameters.inc:550-557` 的三個欄位），canvasTargets 指向來源面（fill → finish-surface → boundary）或派生宿主；h 為參數來源時也算一處。長期較好的做法是讓 JSON 由核心的同一份列舉產生，避免兩份清單再分歧（非系統網格應用、斷面輪廓目前也只在核心那份）。
3. **B（S3、S6）**：這不是一行修得好的 bug。前端需要知道「面 1 的鋪排 1 產生了派生宿主 2」：`surfaces`（或 `objects`）帶出派生宿主的 `derivedFillId` 與來源 boundary id；面 1 面內至少要能列出／切換到派生宿主上的角材與主格，或提供以 placement id 開的唯讀派生宿主工作區。不可以把角材搬回 placement 1、不可以把 placement 2 改成普通 rect、不可以讓 `feSurf` 把兩個 id 當同一個（D4／R41 的 typed 宿主語意要保留）。這需要畫面設計，適合放在 A2。
4. **D（S4、S7）**：不屬於派生宿主修正。若需求要求「物件畫布看得到角材」，那是新的呈現功能；三視圖說明可以直接用 `references.timbers[].geometry` 的 length／A／B。建議在需求帳把這兩項和派生宿主缺口分開記，以免修了 A 之後仍被當成同一缺口未修。

## 未驗項

- 復原／重做後、新程序＋新 profile 冷開後的一般畫面，本次沒有在 UI 重走。原生端的「冷開」只用全新 bridge 載入同一份場景（`diag_derived_host.py`）；#449 已記錄三次結果相同。
- 派生宿主 h 為參數來源、負座標、多分量、孔、空集合的派生宿主，都沒有場景，未實測。
- R02 PF-4A 的 UI 路徑（主格在面內看不到）只以同一根因推論，未走 UI。
- `json_parameter_uses` 缺非系統網格應用、斷面輪廓兩類引用，只依程式碼閱讀。
- 清單雙擊派生宿主的拒絕訊息文字未讀到（見第 4 節）。
- 1400 px 預覽表 3247 折行不在本次範圍。
- 只在 Linux headless Chrome 158 跑；Windows、實體手機未跑。

## 檔案

- `scripts/walk_repro.js`、`scripts/walk_control.js`：UI 重現與對照（Playwright API；本次以 `playwright-core` 加一個 `require('playwright')` 轉接殼執行，`NODE_PATH` 指到暫存目錄，未放進 repo）。
- `scripts/lib.js`（改自 #449，只改預設 port）、`scripts/ui.js`（原樣）、`scripts/serve-wt.sh`（原樣）。
- `scripts/make_minimal.py`、`scripts/diag_derived_host.py`：最小場景產生器與只讀診斷。
- `minimal-derived-host.scene`：最小場景。`diag-output.json`：診斷完整輸出。
- `ui-run/`：`runtime-probe.json`、`walk_repro.log`、`walk_repro.result.json`、`r03-fixed.gcanvas`（另存，12182 B，SHA-256 `a10f6fa8…f461`）、`r03-fixed.export.scene`（匯出，10323 B，SHA-256 `44268b23…7597`）、`r03-fixed.dump.scene`（確認後 dump，與匯出檔逐 byte 相同）、`screens/`。
- `ui-control/`：對照組 `walk_control.log`、`walk_control.result.json`、`screens/`。
