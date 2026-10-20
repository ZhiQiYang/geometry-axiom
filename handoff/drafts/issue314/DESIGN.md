# #314 設計稿：一軸相位差的原生提交檢查（D10b / I24）

- 對象：`D:/geometry-axiom-work/geo261-integration`，head `09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1`（GEO-261 整合枝，#288 的 head）。
- 狀態：草稿。只讀了程式、寫了文字檔，**沒有建置、沒有跑任何測試**。`patch.diff` 只驗過 `git apply --check`（見 §9）。
- 條文來源：`公理層.md` 的 D10b、I24、D29、R22、R60，決策佇列「2026-10-16 #240 S6」與「2026-10-18 #260 最終文字確認…」第 2 題。本稿不改任何條文；`公理層.md` 在 `09ab5f79` 與目前 main 逐位元相同。
- 對應工單：issue #314；BACKLOG 的 GEO-267。
- 行號一律是 `09ab5f79` 的行號。`current_geometry.c` 是 CRLF，行號以 CRLF 切行計。

## 0. 摘要

1. 規則只有一個窄口：所有提交路徑最後都走 `world_revalidate_candidate`（`current_geometry.c:6247`）。在它裡面、`grid_systems_rebuild` 之後加**一次**「前後比較」，就涵蓋 DSL、`engineering archive` 單行、橋接器批次、R60 整卡操作、參數改值。不是每條路徑各補一份。
2. 三層分工：
   - K（`geometry-core/kernel/`）**一個字都不改**：K 沒有「提交」的概念，也不該替別的模板決定「一軸」。
   - W（`geometry-templates/woodworking/native/grid_application.c/.h`）新增 `wood_grid_stagger_commit_valid(after, before, …)`：只拿兩個 K store，純函式，不讀任何全域。規則本體與錯誤訊息在這裡。
   - H（`geometry-core/subgrid_world.inc` 新增 `grid_stagger_commit_valid`，`current_geometry.c` 加 3 行呼叫）：決定「這次重驗是不是提交」，供應基線。
3. 提交 vs 整體取代的區分：`g_subgrid_before != NULL`（有基線）且 `!g_parsing_scene_file`（不是場景檔重放）。這是 I23 早就在用的基線機制，不新增旗標，不動候選結構、不動 `AppWorldOperation`。
4. 改 4 個檔、淨增約 45 行。不新增檔案、不新增 include、不新增 source-graph 節點。
5. 會讓既有測試轉紅的地方（用雙軸相位差的互動提交當夾具）已列在 `TESTS.md` §6。
6. 這份稿裡有三件語意不確定的事，列在 §10。

## 1. 規則，逐句對照條文

| 編號 | 條文原句（`公理層.md`） | 實作位置 | 結果 |
|---|---|---|---|
| S1 | D10b：「同一份網格系統至多一軸有相位差」（W 區塊） | W `wood_grid_stagger_commit_valid` | 見 S2、S3 |
| S2 | I24：「由不足兩軸變為兩軸（含新建時兩軸都填、一軸已有再加另一軸）→ 拒絕，訊息說明同一份網格只能有一軸錯開」 | W：提交後兩軸都有 `stagger_set`，且提交前（沒有這個系統，或不足兩軸）→ 拒絕 | 訊息 M1 |
| S3 | I24：「提交後仍為兩軸而任一軸的相位差值有變 → 拒絕，訊息說明要先在同一筆編輯裡移除一軸」 | W：提交前後都是兩軸，且任一軸 `stagger_value_changed` → 拒絕 | 訊息 M2 |
| S4 | I24：「要改成錯開另一個方向，請在同一筆編輯裡移除這一軸的相位差、再設另一軸」 | 提交後只剩一軸 → 放行（不比較值） | 通過 |
| S5 | I24：「提交後仍為兩軸而相位差值不變（改名稱、改間距等）、以及移除一軸，照常」 | 值不變 → 放行；提交後不足兩軸 → 放行 | 通過 |
| S6 | I24 / D10b：「整體取代、隔離重放及復原／重做不是提交，不做此比較」 | H 閘：`!g_subgrid_before \|\| g_parsing_scene_file` → 不呼叫 W | 見 §4 |
| S7 | I24：「相位差值以該系統自己的相位差欄位求出的值為準；相位差若引用參數欄位，改那張參數卡的值不算改相位差值」 | W `stagger_value_changed`：同一個 ParameterRef 視為值沒變 | 見 §5、§10-1 |
| S8 | R60：「對調後須按新長度重新驗 D10b 等全部目標限制；相位差不對調，不代表原本合法的相位差仍合法」 | 不新增：K 的 `geo_grid_axis_stagger_valid`（`grid_store.c:237`）已在 `grid_systems_rebuild` 內逐軸驗 0／整倍數／溢位。I24 比較在它之後，只看相位差值有沒有變 | 對調不改相位差值 → 不觸發 S3 |

決策表（`n` = 該系統 `stagger_set` 為真的軸數；比較對象是同一個系統 id 的提交前、提交後）：

| 提交前 n | 提交後 n | 提交後兩軸相位差值 | 判定 |
|---|---|---|---|
| 任意（含系統不存在） | 0 或 1 | — | 通過 |
| 0 或 1，或系統不存在 | 2 | — | 拒絕 M1 |
| 2 | 2 | 兩軸皆不變 | 通過 |
| 2 | 2 | 任一軸有變 | 拒絕 M2 |

「值有沒有變」（`wood_grid_stagger_value_changed`）：

| 提交前來源 | 提交後來源 | 判定 |
|---|---|---|
| 直接整數 | 直接整數 | 比整數 |
| ParameterRef (卡, 欄) | 同一個 (卡, 欄) | **沒變**（不管那張卡的值變不變，S7） |
| 直接整數 ↔ ParameterRef，或 ParameterRef → 另一個 (卡, 欄) | | 比兩邊各自求出的值（K 的求值快取 `stagger`） |

最後一列是我補的細節，條文沒有明寫，見 §10-1。

## 2. 提交路徑普查

### 2.1 結論

所有「會改世界」的互動入口都收斂成兩個漏斗，兩個漏斗都經過 `world_revalidate_candidate`：

- 漏斗 A：`apply_scene_line` → `apply_scene_line_candidate`（`transactions.inc:567`）。互動輸入、`line` 指令、歷史群組內每一行、拖曳（`drag` 轉成 `move` 行）都在這裡。`current_geometry.c:3047` `apply_interactive_tokens` 是它的前門（undo/redo/history 控制行先攔掉，其餘都進 `apply_scene_line`）。
- 漏斗 B：橋接器批次 `batch_preview` / `batch_confirm`（`engineering_bridge.inc:164/194`）。

兩者都在重驗期間設 `g_subgrid_before`：漏斗 A 是 `transactions.inc:563`（`call->before` = 指令開始時的活世界），漏斗 B 是 `engineering_bridge.inc:158`；預覽確認時兩者都改走 `app_world_candidate_revalidate`（`current_geometry.c:6364-6374`，基線 `&candidate->before`）。

### 2.2 提交路徑（要檢查）

| # | 路徑 | 入口（檔:行） | 怎麼改到相位差 | 基線 |
|---|---|---|---|---|
| C1 | DSL `grid-system`，新 id | `grid_systems.inc:186` `apply_grid_system_line`；`:222-232` 暫存後 `app_world_revalidate_staged`；`:79-91` `grid_system_read_stagger`（唯一會解析 `stagger` 的地方） | 直接寫 `stagger N` 或 `stagger param:卡:欄` | `transactions.inc:563` |
| C2 | DSL `grid-system`，既有 id（重宣告 = 編輯） | 同 C1；`transactions.inc:610` `system_edit` 強制 I8a 預覽；`line confirm <token>`：`transactions.inc:577-596` → `current_geometry.c:6364` | 同 C1 | 預覽：`transactions.inc:563`；確認：`current_geometry.c:6368` |
| C3 | `engineering archive <base64>` 單行 | `engineering_commands.inc:77` `apply_engineering_line`，`:90-103` archive 分支；`:36` `eng_operation`；`:39` → `card_reference.inc:58` `grid_card_operation`；完成驗證 `:100` `reference_checked`（`references.inc:712`） | `put-grid-system`（`card_reference.inc:33-57`，內含 `u`/`v` 軸字串，走同一個 `grid_system_read_axis`） | `transactions.inc:563` |
| C4 | 橋接器 `engineering-preview` / `engineering-confirm`（`engineering-transaction/1`） | `web_bridge.c:1094`；`engineering_bridge.inc:220/228`；`:164` `batch_preview`、`:137` `app_batch_candidate_apply`（`:157-159` 設基線並 `world_revalidate`）、`:194` `batch_confirm`（`:200` 確認重驗、`:205` 發佈） | 同 C3 的 op | 預覽：`engineering_bridge.inc:158`；確認：`current_geometry.c:6368` |
| C5 | **R60 整卡提交**（#253 / #298 / #312） | 不是獨立入口：就是 C3、C4 裡的四個 op：`put-grid-system`（帶 `cardReference`，`card_reference.inc:33`）、`set-grid-card-reference`（`:66`）、`swap-grid-card-reference`（`:71`）、`unbind-grid-card-reference`（`:73-93`），寫回走 `grid_card_store`（`:31`）→ `app_grid_system_put`（`grid_adapter.inc:20`） | `put-grid-system` 可以直接帶雙軸 `stagger`；set／swap／unbind 只改間距與映射，**不動相位差欄位**，只可能讓既有相位差變成 0 或間距整倍數（由 K 的逐軸驗擋下，S8） | 同 C3、C4 |
| C6 | 參數改值 | C3、C4 的 `put-parameter`（`engineering_commands.inc:52`，`parameters.inc:405`）、`import-parameters`（`:49`，`parameters.inc:754`）、`delete-parameter`（`:55`，`parameters.inc:725`）、`parameter-package`（`:40`）。系統重新求值在重驗內：`reference_parameters_rebuild`（`current_geometry.c:6255`，`references.inc:681`）、`grid_systems_rebuild`（`:6270`） | 引用 `param:卡:欄` 的軸，快取值跟著卡變 | 同 C3、C4 |
| C7 | 其他 DSL 指令：`grid-binding`、`grid-source-rule`、`boundary-keyed`、`grid … from-system/from-binding`、`subgrid`、`delete`、`boundary`／`placement`／`surface`／`move`／`guide`／`spec` 等 | 全部經 `apply_scene_line_unchecked`（`current_geometry.c:9939`）；staged 重驗點 `grid_bindings.inc:68/82`、`grid_subdivision.inc:107`、`boundary_vertex_keys.inc:180/270`、`grid_systems.inc:256` | **不改相位差欄位**；只是同一個重驗也跑到新檢查（舊兩軸系統沒動就通過） | `transactions.inc:563` |
| C8 | 歷史群組內每一行 | `current_geometry.c:3047` → `apply_scene_line`；R56：「歷史群組內的每一行」各是一次提交，群組結束不是 | 同 C1…C7 | 每行各自的 `call->before` |
| C9 | 拖曳 | `web_bridge.c:297` `cmd_drag` → `feed_line("drag","move …")` | 不改系統 | 同 C7 |

「DSL 的 `grid` 指令」不會寫相位差：直接 `grid` 的軸是有限排法，`wood_grid_begin_direct`（`grid_application.c:41`，拒絕訊息在 `:44`）拒絕改 `from_system`／`from_binding` 的軸；`stagger` 只在 `grid_system_read_axis` 解析。所以不需要為 `grid` 指令另補。

`reference_snap`（`references.inc:970`）和 `cmd_grid_preview`（`reference_bridge.inc:317`）會對複本跑重驗或解析，但不改系統，也不發佈；同樣跑到新檢查，結果等於「沒變 = 通過」。

### 2.3 不是提交（不檢查）

| # | 路徑 | 入口 | 為什麼不會檢查 |
|---|---|---|---|
| D1 | 復原／重做 | `current_geometry.c:3029/3035` `history_undo/redo` → `history_restore_world`（`:2994`） | 只還原快照，不呼叫重驗 |
| D2 | 載入場景檔 `loadfile` | `web_bridge.c:423` `cmd_loadfile`；`:409-421` `app_scene_load_evaluate`（把 `g_subgrid_before` 設 NULL）→ `transactions.inc:713` `app_scene_replay_file` → `current_geometry.c:9984` `parse_scene_file`（`g_parsing_scene_file` 在 `:9994` 設真、`:10113` 清除；收尾重驗在 `:10105`，旗標仍為真） | 基線 NULL，旗標為真，兩道都擋 |
| D3 | 場景匯入 `load-prepare` / `load-confirm` | `scene-import-bridge.inc:23/56`；確認只發佈（`:64`），不重驗 | 準備階段同 D2；確認階段不重驗 |
| D4 | 開新、恢復內建場景 | `web_bridge.c:396` `cmd_replace_world` → `:213` `app_replace_world` | 開新是 `memset`；內建場景見下方注意 |
| D5 | GDI 載入、CLI 載入 | `current_geometry.c:3822`（`gdi_load_scene_file`）、`:10235` | 都是 `parse_scene_file` |
| D6 | 隔離重放（R46 重開、I31 交換包重建）與唯讀驗證 | `model_base.c:434-458`（基線 NULL，`app_scene_replay_file`）；`source-inspector-bridge.inc:209-211`（基線 NULL，`parse_scene_file`）；`engineering_bridge.inc:236-248` `cmd_engineering_validate`（驗證後丟棄） | 同 D2 |
| D7 | 前端「恢復資料」「載入方案快照」「開 .gcanvas」 | 前端走 `loadfile` / `load-prepare`（`geometry-web/serve.py:130,286`；`app.js:1870`） | 同 D2。這條是讀程式得到的，沒有實際執行驗證 |

**注意（D4 內建場景）**：`reference_default_world`（`transactions.inc:833-856`，逐行迴圈在 `:841-851`）用逐行 `apply_scene_line("default", …)` 重建內建場景，而且**沒有設 `g_parsing_scene_file`**。它在「恢復內建場景」時，每行都是 H 眼中的提交。目前內建場景（room_a）沒有任何 `grid-system`，所以不受影響。這是目前唯一一個「整體取代卻用提交路徑」的例外；`TESTS.md` 的普查測試會固定「內建場景文字不含 `stagger`」，將來有人把雙軸相位差放進內建場景就會紅。

## 3. 檢查放在哪一層

### 3.1 結論

| 層 | 放什麼 | 檔 |
|---|---|---|
| K | 不放。`geo_grid_axis_stagger_valid` 已有的逐軸規則（0、整倍數、溢位、兩軸須皆無限）維持不動 | `geometry-core/kernel/grid_store.c` 不在補丁內 |
| W | 規則本體、訊息、條號：`wood_grid_stagger_commit_valid` | `geometry-templates/woodworking/native/grid_application.c/.h` |
| H | 「這是不是提交」的判斷、基線供應、呼叫點 | `geometry-core/subgrid_world.inc`、`current_geometry.c` |

### 3.2 為什麼

1. **條文本身把規則放在 W。** D10b 與 I24 都分「核心契約（K）」與「固定木工模板契約（W）」兩塊。K 塊只說「指定無限軸在另一軸的 band 上採兩種平移」「δ 為非零且不得為節距整倍數」，沒有一個字提兩軸或提交；「同一份網格系統至多一軸」「相容例外」「每一筆提交（R56）比較提交前後」都在 W 塊。
2. **K 不能知道什麼是提交。** K 的 `GeoGridStore` 是沒有歷史的 store；「舊的兩軸檔要照樣能開」代表 K 在載入時必須接受兩軸。若把規則放進 K 的 `geo_grid_system_evaluate`，載入舊檔就會失敗；若放進 K 的 put/redeclare，每個呼叫者（載入、模型重放、測試 harness）都會被卡。
3. **K 要保持對別的模板中立。** `geometry-templates/rectangular-grid` 是第二個模板見證（`PRODUCT-ARCHITECTURE.md`）。一軸限制的理由是「同一種矩形板鋪滿一個面，板縫只能在一個方向錯開」（決策佇列 2026-10-16 協調 agent 推論，只在板子同方向平行鋪時成立）；這是木工模板的事。`tests/geo261_grid_store_harness.c:268` 目前就把兩軸相位差放進 K store 驗 K 的行為，K 不改則這支 harness 不受影響。
4. **H 才知道提交與整體取代的差別。** 這是宿主的交易概念（R56 / D61），W 的既有測試也明文要求 W 不讀 `g_subgrid_before`、`g_parsing_scene_file`（`tests/test_geo261_wood_grid_application.py` 的 `test_policy_has_no_host_world_or_ambient_candidate_dependency`）。所以 W 只收兩個 store，H 決定要不要呼叫它。`grid_application.c` 的 W 慣例也是這樣：`wood_grid_rule_edit_begin` 的 `loading` 旗標是 H 傳進去的。
5. **依賴方向。** H → W → K 單向。新增的 W 函式只 `#include "grid_application.h"`（它已包含 K 的 `grid_store.h`），用 K 的公開唯讀 API `geo_grid_systems_count/at/find`；K 沒有任何對 W 的引用；W 沒有任何對 H 的引用。`tests/architecture_contract.py` 的方向規則不會被觸動。
6. **為什麼是一個 store 級函式，不是 `WoodGridContext` 的新旗標。** 試過的替代：在 `WoodGridContext` 加 `bool commit`，讓 `wood_grid_world_valid_direct` 內部比較。這要在三處接線才不會靜默失效：`grid_sources.c:434`、`:440` 兩個 hook 的 `evaluated.before=…` 要連 `commit` 一起複製，`:457` 的 `wood_grid_sources_bind` 比較表要加欄位。漏一處就「檢查靜默不跑」。兩個 `const GeoGridStore *` 沒有這個問題。

### 3.3 呼叫點為什麼是 `world_revalidate_candidate` 而不是各路徑

- 所有路徑（C1–C9）都會經過它；預覽與確認各跑一次，所以預覽階段就會顯示無效，不會等到確認才失敗（I8a）。
- 呼叫點放在 `grid_systems_rebuild` 之後：K 的逐軸驗（0、整倍數）先報，I24 的跨軸比較後報；此時候選 store 的相位差快取已由 `wood_grid_publish_system_cache`（`grid_sources.c:254`）寫回。放在 `grid_bindings_rebuild` 之前，讓錯誤訊息先指出系統而不是被下游的綁定錯誤蓋掉。
- 失敗時沿用同一段收尾：`set_revalidate_error(...)`、`reference_capture_trial(candidate)`、`return false`，與前後兩個兄弟分支一致。呼叫端（`apply_grid_system_line:232`、`app_batch_candidate_apply:159`、`reference_stage`）已經會把這段訊息帶到 `error` 或 `preview.violations[].message`。

## 4. 怎麼區分「整體取代」與「編輯」

H 的判斷只有兩個條件（`subgrid_world.inc` 新增的 `grid_stagger_commit_valid`）：

```
if (!g_subgrid_before || g_parsing_scene_file) return true;   // 不比較
return wood_grid_stagger_commit_valid(candidate 的 grid_store, g_subgrid_before 的 grid_store, …);
```

- `g_parsing_scene_file`：`parse_scene_file` 期間為真（`current_geometry.c:9994/10113`）。載入場景檔、場景匯入準備、隔離重放、`source-inspect-file`、CLI／GDI 載入全部走它。檔案重放時每行的基線 `frame->before` 只是「載到這一行為止」的半成品世界（`transactions.inc:675-700`），拿來比較一定誤判，所以一律不比。
- `g_subgrid_before == NULL`：沒有基線就沒有東西可比。`app_scene_load_evaluate`（`web_bridge.c:409-421`）、`model_base.c:447`、`source-inspector-bridge.inc:209` 都主動設 NULL。
- 復原／重做根本不呼叫重驗（D1）。

這與 I23 的基線是同一個機制（`subgrid_world_valid`、`grid_rules_world_valid` 都用 `g_subgrid_before`），不引入第二套「提交種類」。

### 4.1 這個做法的弱點

1. 它依賴兩個全域，不是候選自己帶的屬性。如果將來有人用「逐行 `apply_scene_line`」實作整體取代，而不經 `parse_scene_file`（`reference_default_world` 就是現成例子，§2.3），那條路徑會被當成提交。
2. 如果將來有新的提交入口沒設基線，檢查會**靜默略過**，而不是失敗。

緩解：W 函式對缺基線 fail closed（這只保護 W 的其他呼叫者；H 端「沒基線就略過」靠下一句的普查測試擋）；`TESTS.md` §5 的普查測試固定「所有 `app_world_candidate_publish` / `world_revalidate` / `app_world_revalidate_staged` 呼叫點」的分類，新增一個就紅；每條路徑各有突變（拿掉該路徑的基線就紅）。

### 4.2 沒採用的方案

- 把「提交／整體取代」寫進 `AppWorldOperation`（`world_candidate.inc:5`，會被簽進 `operation_seal`）：最乾淨，但動候選結構，`tests/test_geo261_deferred_product.py` 釘了 `app_world_candidate_publish` 的簽名與流程，改動面比這個 issue 大。列為之後的加固選項。
- 只在 `app_world_candidate_publish` 檢查：太晚（預覽已經說有效），而且 5 個呼叫端要各自說明種類。
- 各 parser 自己比對：參數改值、R60 的 set／swap／unbind、`put-grid-system` 內的軸字串各是不同路徑，容易漏，而且要重複 5 份基線取得邏輯。

## 5. 參數間接改到相位差

`GeoGridAxisDef` 對相位差有兩個欄位：`parameters[5]`（ParameterRef，`set` 為真表示引用）與 `stagger`（數值；有引用時是 K 求出來的快取，沒引用時是作者寫的整數）。GEO-261 的 `wood_grid_def_axis`（`grid_sources.c:82-98`）已把「有引用時 `stagger` 是快取、不屬於定義」寫進正式定義編碼，所以這裡採同一個語意：

1. 軸的 `stagger_set` 是否為真，只由 token 在不在決定。參數卡的值怎麼改都不會讓 `stagger_set` 變化（值求成 0 或節距整倍數會先被 K 逐軸驗擋下）。所以**參數改值不可能讓系統從不足兩軸變成兩軸**。
2. 在兩軸舊網格上，兩軸都引用同一個 (卡, 欄)、只改那張卡的值：`stagger_value_changed` 回「沒變」→ 通過（S7）。
3. 來源本身換了（直接整數 ↔ ParameterRef，或改指別的 (卡, 欄)）：比兩邊的求值。這讓「明示解除參數引用、轉成當下有效整數」（D29，經 I8a 預覽）在兩軸舊網格上可行：值不變就通過，值不同就拒絕。

這個語意的後果（要讓使用者知道）：在兩軸舊網格上，用「改參數卡的值」可以任意改兩軸相位差，I24 不會攔。這是 I24 最後一句的字面結果，不是實作漏洞。

## 6. 錯誤訊息與條號

K 的逐軸訊息（零、整倍數、溢位、兩軸須皆無限）不動，仍是 `I24: …`（`grid_application.c:202-220` 的 `wood_grid_system_error`）。

新增兩則，都由 W 產生，前綴 `I24:`，括號內指向定義條 `D10b`：

| 代號 | 情形 | 訊息（`%u` = 系統 id） |
|---|---|---|
| M1 | 提交後兩軸都有相位差，提交前不是兩軸（含新建、含從一軸加第二軸） | `I24: 網格系統 %u 的 u、v 兩軸都設了相位差。同一份網格只能有一軸錯開（D10b）；請只保留一軸的 stagger` |
| M2 | 提交前後都是兩軸，任一軸相位差值有變 | `I24: 網格系統 %u 提交前後都是兩軸錯開，但 %c 軸相位差由 %lld 改成 %lld。要改請先在同一筆編輯裡移除一軸，再改剩下那軸（D10b）` |
| M0 | 內部：W 被呼叫時缺基線或候選 store（H 的錯） | `I24: 相位差提交缺少前後世界，不能比較，一律拒絕` |

- 測試固定的子字串直接取自條文：M1 的「同一份網格只能有一軸錯開」、M2 的「先在同一筆編輯裡移除一軸」。
- 長度（UTF-8 位元組，已算過）：M0 68、M1 最長 144、M2 最壞 211（id 取 uint32 最大、兩個 `%lld` 取 int64 最小；實際相位差受 D1 範圍限制，更短），都小於 H 端 `grid_error[256]`，不會在多位元組字元中間被截斷。
- 訊息怎麼到使用者手上：DSL 走 `scene_error`（`grid_systems.inc:233`）；橋接器批次走 `eng_fail(g_revalidate_error)` → `preview.violations[].message`（`engineering_bridge.inc:159`、`:128`）；預覽階段的無效候選走 `reference_stage` 的 `actual` 欄。三處都不需改。

## 7. 對 GEO-261 的影響

### 7.1 結構

- 補丁只動 H 與 W 的 4 個檔，不動 K、不動 `AppWorldCandidate` / `AppWorldOperation`、不動 source graph（沒有新的 provider、節點、依賴邊），不新增 include，不新增檔案。
- 檢查直接讀 `candidate->geo.grid_store` 與 `g_subgrid_before->geo.grid_store`。`grid_store` 已是候選綁定的核心之一（`world_candidate.inc:61` `APP_BIND_CORE(grid_store)`），不需要新綁定。
- 檢查結果不 memoize、不進圖：它依賴基線，而基線不是來源。確認階段由 `app_world_candidate_revalidate` 重新跑一次，不信任預覽時的結果。

### 7.2 效能

- 每次 `world_revalidate_candidate` 多一個迴圈：最多 16 個系統 × 在基線 store 線性找 id（最多 16）→ 最壞約 256 次比較，沒有配置、沒有 World 複製、沒有 SHA。
- 一次提交通常重驗 1 次（直接）或 2 次（預覽 + 確認）；`reference_snap` 會對多個候選位置各重驗一次，也只是各加這幾百次比較。
- 對照 GEO-261 目前的成本（World 約 4.76 MB，候選建立、封存、SHA 才是大頭；`evidence/geo261-codex-fix-perf-candidate-sha-20261018/README.md`）：這個增量在量測雜訊以下，也不會改變 `geo_sha_block` 呼叫數。
- **不宣稱已量測。** GEO-261 在 bridge_integrity 上還有未達的 ≤2× 門檻（該 README：3.222×），本補丁不處理也不加重它。實作後的驗證方式：同輪 A/B 跑 `py:test_bridge_integrity`，沒有可辨識的差異；`geo_sha_block` 呼叫數不變。

### 7.3 帳本與盤點

動到這 4 個檔會讓下列既有帳本過期，需要實作後重刷（不在補丁內，也不要手改）：

1. `tests/mutants_results.json`：逐檔 SHA 釘（`grid_application.c/.h`、`subgrid_world.inc`、`current_geometry.c` 都在其中），`run_all` 的 `mutation:check` 會紅。要在 WSL 重跑（#312 正文：由主迴圈排他執行）。
2. `geometry-core/domain-decoupling/product-architecture-scan.json` 與其收據（`854660a7` 剛刷過）：新增了 W 的公開函式與 H 的靜態函式。
3. `geometry-core/domain-decoupling/product-architecture.json` 的 `policy.forbiddenIdentifiers`：目前列了所有 W 識別字（含 static，例如 `wood_grid_error`）。新函式 `wood_grid_stagger_commit_valid`、`wood_grid_stagger_value_changed` 不在內，意思是將來 K 檔誤用它們不會被掃到。這份清單有收據釘住，要隨掃描重產，不要手改。
4. `tests/run_all.expected.json`：新增測試後的測試數。

## 8. 補丁內容導讀（`patch.diff`）

| 檔 | 改動 |
|---|---|
| `geometry-templates/woodworking/native/grid_application.h` | 在 `wood_grid_systems_rebuild` 宣告後新增 `wood_grid_stagger_commit_valid` 宣告與契約註解 |
| `geometry-templates/woodworking/native/grid_application.c` | 在 `wood_grid_systems_rebuild` 之後、`wood_grid_system_evaluate_direct` 之前新增 `wood_grid_stagger_value_changed`（static）與 `wood_grid_stagger_commit_valid`。位置在 `wood_grid_bind_engineering` 之前，不影響 `test_geo261_wood_grid_engineering.py` 對該函式之後原始碼的禁字掃描 |
| `geometry-core/subgrid_world.inc` | 在 `subgrid_world_valid` 之後新增 H 的 `grid_stagger_commit_valid` |
| `current_geometry.c`（CRLF） | `world_revalidate_candidate` 內、`grid_systems_rebuild` 失敗分支之後加 3 行呼叫 |

W 程式（全部）：

```c
static bool wood_grid_stagger_value_changed(const GeoGridAxisDef *old,const GeoGridAxisDef *now)
{
    const GeoParameterRef *prior=&old->parameters[5],*current=&now->parameters[5];
    if(prior->set&&current->set&&prior->parameter_id==current->parameter_id&&prior->field_id==current->field_id)return false;
    return old->stagger!=now->stagger;
}
bool wood_grid_stagger_commit_valid(const GeoGridStore *after,const GeoGridStore *before,char *error,size_t cap)
{
    if(!after||!before)return wood_grid_error(error,cap,"I24: …缺少前後世界…");
    for(size_t i=0;i<geo_grid_systems_count(after);++i){
        const GeoGridSystem *now=geo_grid_systems_at(after,i),*old=geo_grid_systems_find(before,now->id);
        if(!(now->axis[0].stagger_set&&now->axis[1].stagger_set))continue;
        if(!old||!(old->axis[0].stagger_set&&old->axis[1].stagger_set))return …M1…;
        for(int axis=0;axis<2;++axis)if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis]))return …M2…;
    }
    return true;
}
```

與既有架構測試的相容性（讀碼確認，未執行）：

- `test_geo261_wood_grid_application.py` 的 W 純度掃描禁用 `World`、`Coord`、`scene_error`、`world_find_placement`、`g_subgrid_before`、`g_parsing_scene_file`。新碼用 `GeoCoord`（`\bCoord\b` 不會誤中），訊息文字不含這些字。
- `tests/test_geo261_wood_grid_cells.py` 只掃 `grid_cells.c`，不受影響。
- 沒有新增 include，`architecture_contract.py` 的 include 邊不變。

### 8.1 重新套用

`#288` 合入 main 後，行號可能位移，但四個錨點都是唯一字串，可以重新套：

1. `grid_application.h`：`bool wood_grid_systems_rebuild(WoodGridContext *,char *,size_t);` 之後。
2. `grid_application.c`：`bool wood_grid_system_evaluate_direct(WoodGridContext *c,uint32_t id,char *error,size_t cap)` 之前。
3. `subgrid_world.inc`：`subgrid_world_valid` 整個函式之後。
4. `current_geometry.c`：`world_revalidate_candidate` 內 `if (!grid_systems_rebuild(candidate,grid_error,sizeof grid_error)) {…}` 之後。

## 9. 驗證（只做了文字層面）

- `git apply --check`：
  1. 對 `D:/geometry-axiom-work/geo261-integration` 直接 `--check`：通過，工作樹仍乾淨、HEAD 仍是 `09ab5f79`。
  2. 對從 `git show 09ab5f79:<path>` 取出的 blob 副本（暫存目錄，不在任何 repo 內，`core.autocrlf=false`）：`--check` 通過；實際套用後四個檔與預期結果逐位元組相同。
  3. 對 CRLF 工作樹樣式的副本（`core.autocrlf=true`）：三個 LF 檔通過。`current_geometry.c` 在 repo 內是 `-text` 的 CRLF，補丁在該檔用 CRLF 上下文，已由 (1)(2) 覆蓋。
- **沒有**編譯。新 C 碼靠逐行審視與對照既有程式的型別／慣例（`GeoGridAxisDef.parameters[5]`、`GeoParameterRef.{set,parameter_id,field_id}`、`geo_grid_systems_count/at/find` 的 const 簽名、`wood_grid_error` 的 printf 慣例）。第一次編譯可能還有小錯。
- 沒有跑 WSL，也沒有跑任何測試。

## 10. 我最不確定的三件事

### 10-1. 參數間接改到相位差，算不算「編輯」，以及「來源換了」怎麼比

條文只明寫一句：「改那張參數卡的值不算改相位差值」。我把它實作成「同一個 (卡, 欄) = 值沒變」。沒寫的有四種情形，我選了「比求值」，但它們都可以有別的合理讀法：

1. 直接整數 → 引用，求值相同（例如把 400 改成引用一張值為 400 的卡）。我放行（值沒變）。嚴格讀法是「來源 token 變了就算編輯」，會拒絕。
2. 引用 → 直接整數，求值相同（D29 的「解除參數引用」）。我放行。若拒絕，兩軸舊網格就永遠不能解除相位差的參數引用，除非先移除一軸。
3. 改指另一個 (卡, 欄)，兩邊求值相同。我放行。
4. 同一筆同時換引用又改卡值。我拿「前一個世界的快取」對「這次候選的快取」，所以結果取決於哪個值先被算出來。這個情形我沒有找到條文可以裁決。

另一個後果見 §5：在兩軸舊網格上，改參數卡的值可以任意移動兩軸相位差，I24 攔不到。若使用者的本意是「兩軸舊檔只能凍結或收斂到一軸」，那 S7 那句話就需要收窄。這屬於條文，不是實作；我不改。

### 10-2. 「提交」的邊界，特別是我用兩個全域來判定

我確定的：C1–C9 都會經過 `world_revalidate_candidate`，D1–D7 不會（或被旗標擋下）。不確定的有三處：

1. 判定靠 `g_subgrid_before` 與 `g_parsing_scene_file` 這兩個全域，不是候選的屬性。§2.3 的內建場景重建已經是一個「整體取代卻走提交路徑」的例子（現在無害）。
2. 沒有基線時我選擇「不檢查」（因為 I23 已經這樣）。我沒有找到今天會在沒基線下改網格系統的提交入口，但這是讀碼結論，不是測過。
3. 條文 R56 說「加入既有 World 的匯入確認」是提交。我只找到一條對應路徑（參數卡匯入 `import-parameters`，走 C3／C4）。如果還有別的「把外部資料併進現有世界」的入口，我漏看了。另外 D7（前端恢復資料、載入方案快照走 `loadfile`）是看 `serve.py` 與 `app.js` 推的，沒有實際跑過。

### 10-3. 「同一筆編輯」與「同一份網格」的單位

1. 「同一筆」我解成「一個 R56 提交」：一行指令，或一個橋接器批次；歷史群組內的兩行是兩筆。後果：舊網格 `u:400, v:300` 可以在**一行**內重宣告成只錯開 u（或只錯開 v），提交後只剩一軸，通過，數值也可以同時改。
   但「兩軸都保留、而且改任一軸的值」不論拆成幾筆都做不到：只要某一筆的結果仍是兩軸且值有變就是 M2，而先移除一軸、再把它加回來，加回來那筆是 M1。這是條文的設計（舊兩軸網格只能凍結或收斂到一軸），我只是把它列出來，因為使用者可能沒有意識到這一點。
2. 「同一份網格」我按系統 id 比。同一筆批次裡「刪掉系統 5 再用 id 5 新建」會被當成同一份（與 D60 的「刪除後同鍵重建 = 新存在期」是兩回事）；分成兩次提交做則第二次是「新建」，兩軸會被 M1 擋。這是更嚴格的方向，沒有漏洞，但跟身分帳的語意不一致。
3. R60 的 `swap-grid-card-reference` 或 `set-grid-card-reference` 作用在兩軸舊網格上：相位差值不動，所以 I24 放行（S5「改間距等照常」）。但兩軸的節距會一起變，物理上等於兩軸都換了一組新錯開位置。我照條文字面放行，沒有另設規則。

## 11. 前端與其他附帶事項（不在補丁內）

- 前端 `grid-system-workspace.js` 仍允許在兩軸各加 `stagger`（`data-ig-add-stagger`，`:449`）。補丁後原生會拒絕並回傳 M1，使用者看到的是 toast 與原生訊息。要不要在 UI 上直接停用第二軸，是另一個 UX 工單，#314 明寫只做原生。
- 會因此轉紅的既有測試，與要新增的測試，見 `TESTS.md`。
- 實作合入時建議同步：BACKLOG 的 GEO-267 狀態、`geometry-core/README.md` 若有 I24 實作說明。
