# #316 測試與驗證計畫

> 基底 `09ab5f79`。本輪**沒有建置、沒有跑任何測試**；§A 只列實際做過的靜態檢查，§C 起的「預期」都是推導值，等 WSL 空閒再實跑。

## A. 這一輪實際做過的靜態驗證（可重做）

| 檢查 | 做法 | 結果 |
|---|---|---|
| 補丁能套 | 暫時索引 `git read-tree 09ab5f79` + `git apply --check --cached patch.diff`（`GIT_OBJECT_DIRECTORY` 指到暫存、`GIT_ALTERNATE_OBJECT_DIRECTORIES` 指到 repo：沒寫進 repo 物件庫、沒動工作樹） | 通過 |
| 套完逐位元相同 | 真套進暫時索引，12 個結果 blob 與目標檔逐位元比 | 12/12 相同 |
| CRLF 保真 | `current_geometry.c` 是統一 CRLF（`.gitattributes` 標 `-text`）。補丁後 10462 行、LF 數 = CRLF 數、沒有孤立 CR | 通過 |
| 工作樹式套用 | 在 repo 外暫存目錄放基底副本，`git apply --check` 與真套 | 通過（本機 `core.autocrlf=true`，去掉 CR 後與目標檔相同） |
| Python 語法 | 補丁後 `.py` 做 `ast.parse` | 通過 |
| C 括號平衡 | 去註解與字串後數 `{}`、`()`、`[]`（含 `current_geometry.c`） | 通過（**不是編譯**） |
| 突變錨點 | 對補丁後 `mutate.py` 的 80 個編號突變逐一確認 `old` 在目標檔恰好 1 次；M13 的錨點文字沒動；M97 在 `references.inc`、M98 在 `world_validation.c` 各恰好 1 次 | 全部為 1 |
| 單元控制項錨點 | `test_geo261_wood_contact_world.py` 17 個、`test_geo261_wood_world_validation.py` 12 個（原 10 + 新 2）的 `before` 各恰好 1 次 | 通過 |
| 可達性輔助函式 | 把新測試用的 `without_comments_and_strings`／`call_sites`／`mentions` 抽出來，對基底與補丁後的 include 閉包（184 檔）實際計數 | 基底：三個死宿主 calls=0；`collect_stop_faces` 4、`timber_end_face_check` 1。補丁後：三個死宿主 mentions=0 |
| 根目錄場景掃描 | 171 個 `.scene` 逐檔取 `place N on P`：104 個有 `place`、30 個宣告 ≥2 個承載面、**每個場景最多 1 個承載面帶角材** | 支持 §3.2 的前提 |
| 計數 | `TESTS` 長度 166 = `run_all.expected.json` 的 `core:run_tests`；`test_geo261_wood_contact_world.py` 測試方法 9 = 期望值 | 一致 |
| 讀者追溯影響 | `axiom_matrix` 函式對補丁後檔案重算 | 無燈號變化；清單變動見 DESIGN §2.4 |
| 兩補丁相容 | `patch.diff` 單獨、`../combined/patch.diff` 都通過；#299 → #316 先後套用有 4 個檔案互擋 | 見 DESIGN §4 |

**沒做**：編譯（MSVC／WSL gcc）、`run_tests`、任何 unittest、`mutate.py`、`sync_axiom_reader.py`、瀏覽器驗收。

## B. 實跑第一步：新場景要先在「未套補丁的基底」接受

M97／M98 的牙齒完全依賴 `_i11_two_surfaces_same_uv_accept.scene` 在正常程式下被接受。所以請先：

1. 只放入新場景檔（不套其餘補丁），用基底的 core 手跑：`<core.exe> --scene _i11_two_surfaces_same_uv_accept.scene --no-window`。
2. 預期結束碼 0，stdout 的 `尺寸:L=` 依序是 4000、3000。若被拒，錯誤訊息會指出是哪一道規則；這時**不要改程式**，改場景（例如加 `space 1 boundary 1 3`、調整牆的輪廓）直到基底接受，再往下。
3. 順便再看 `lengths` 的順序與 `TESTS` 的 `'lengths': [4000, 3000]` 是否一致。

## C. 斷言清單

### C1. 核心場景（`tests/run_tests.py`）

| 場景 | 預期 | 備註 |
|---|---|---|
| `_i11_two_surfaces_same_uv_accept.scene` | `accept`，`lengths [4000, 3000]` | 放在 `TESTS` 最後；`core:run_tests` 計數 165→166 |

### C2. 可達性斷言（`tests/test_geo261_wood_contact_world.py`）

`test_main_consumers_have_callers_delegate_and_keep_original_member_identity`：

- `collect_stop_faces`→`app_contact_resolve_stops`、`timber_end_face_check`→`wood_contact_end_faces_with_sources`：本體含該 W 呼叫、本體沒有 `for`／`while`、**`call_sites >= 1`**。
- `RETIRED_DEAD_HOSTS`（`world_footprint_collides`、`boundary_edge_interval`、`stop_in_owner_extension`）：在產品閉包裡**一次都不得出現**（去註解與字串後）。
- `app_contact_facts` 轉接器與 `app_contact_resolve_stops` 的既有斷言原樣保留。

**負向確認**（證明這個斷言有牙齒；不需要編譯，純 Python）：把補丁還原到基底的 `current_geometry.c`，只把舊的五個配對放回 `pairs`，`call_sites` 對 `world_footprint_collides`／`boundary_edge_interval`／`stop_in_owner_extension` 都得 0 → 斷言失敗。我已用同一組輔助函式在基底上算出這三個 0。

### C3. W 單元

- `tests/geo261_contact_world_harness.c`：刪 `collisions` 案（9 個 `collision-*` 斷言隨死 API 一起走）。
- `tests/test_geo261_wood_contact_world.py`：控制項 20→17（刪 `positive-area`、`collision-identity`、`collision-placement`）；方法名 `test_twenty_…`→`test_actual_guard_controls_…`；刪 `test_collision_…` 方法（10→9）。
- `tests/test_geo261_wood_world_validation.py::test_removed_rules_fail_exact_named_assertions` 新增兩個控制項：

| 控制項 | 替換 | 應轉紅的斷言 |
|---|---|---|
| validation-same-host | 拿掉 `\|\|a.placement_id!=b.placement_id` | `validation-separate-hosts` |
| validation-pair-placed | `if(!b.member->placed\|\|`→`if(` | `validation-unplaced-no-collision` |

### C4. 其他計數與清單

- `tests/run_all.expected.json`：`core:run_tests` 165→166；`py:test_geo261_wood_contact_world` 10→9。
- `tests/test_geo261_mutation_migration.py`：`added` 登記 M97／M98，長度斷言 28→30。
- `product-architecture.json`：`policy.forbiddenIdentifiers` 移除 `wood_contact_footprint_collides`。

## D. 帳本突變預期（`tests/mutate.py`）

| 編號 | 預期結果 | 預期 `killed_by` | 機制 |
|---|---|---|---|
| M13（既有，僅改註解） | killed | 與舊帳本同（`subgrid-local` 等前 5 個） | 不變 |
| M97 | killed | `_i11_two_surfaces_same_uv_accept.scene`（只有它） | 過濾拿掉 → 跨面配對被比 → `reference_member_footprint` 回 false → `reference_check_all` 回 false → 場景被拒（`FAIL 應接受但拒絕`） |
| M98 | killed | 同上 | 過濾拿掉 → `context->footprint(…,j,a.placement_id,…)` 回 false → `world_validate_derived` 回 false → 場景被拒 |

**判讀陷阱**

- 若新場景在基底就被拒（§B），M97／M98 會因為「基線不過」被帳本判為 blocked／invalid，不是 survived；先修場景。
- 若兩個突變都 **survived**：代表場景被接受卻沒觸發跨面比較。可能是 `reference_check_all` 或最終重驗根本沒走到（例如場景是否在 `loadfile` 時沒有全量重驗），或 `lengths` 之外的某個條件讓兩支角材其實落在同一面——請先看 stdout 的承載面標示。
- 若只有 M98 survived：代表最終重驗的兩兩檢查被 `reference_check_all` 蓋住（M36 同型）；那表示 §3.3 的機制 1 在檢查點 3 不成立，需要另找殺手或標等價並附差分證據。

## E. 實跑步驟（WSL 空閒、遊戲未開時）

1. §B（基底上手跑新場景）。
2. `git apply --check patch.diff && git apply patch.diff`（基底 `09ab5f79` 或其後續的 GEO-261 整合分支；若同時要 #299，改套 `../combined/patch.diff`）。
3. 建 core／bridge：照既有流程（`tests/binaries.py`、`tests/run_all.py`）。
4. `python tests/run_tests.py <core exe>`：預期 166/166。
5. 純 Python（不需編譯器）：`python tests/test_geo261_mutation_migration.py`、`python -B tests/test_product_architecture.py`、`python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`；可達性斷言在 `ContactWorldBoundary` 類，不需編譯：`python -m unittest tests.test_geo261_wood_contact_world.ContactWorldBoundary`（同檔的 `WoodContactWorld` 類需要 C 編譯器）。
6. W 單元（需 C 編譯器，走 WSL）：`python tests/test_geo261_wood_contact_world.py`、`python tests/test_geo261_wood_world_validation.py`。
7. 針對性突變（不覆蓋正式帳本）：`MUTATE_RESULTS=<暫存路徑>.json python tests/mutate.py M13 M37 M97 M98`；M13、M37 應與舊帳本一致，M97、M98 對照 §D。
8. `tests/test_bridge_integrity.py`：會對新場景做 dump／重載往返（accept 場景都會跑）。
9. 與 #299 合併後一次重產整份帳本：`python tests/mutate.py`（約 2 小時）→ `python tests/mutate.py --check`；再 `python3 geometry-guide/sync_axiom_reader.py`、`--check`、`python3 tests/test_axiom_reader.py`；`tests/run_all.py` 完整閘。

## F. 已知會因本補丁改變的既有東西

| 位置 | 原本 | 現在 |
|---|---|---|
| `current_geometry.c` | `world_footprint_collides`、`boundary_edge_interval`、`stop_in_owner_extension` 與其註解；5758–5760 I11 孤兒註解 | 刪除；`resolve_auto_span` 前多一段 I11 三檢查點註解 |
| `contact_world.c`／`.h` | `wood_contact_footprint_collides` | 刪除；`.h` 兩個宣告上方多兩段說明 |
| 測試方法 | `test_collision_…`、`test_five_real_main_consumers_…`、`test_twenty_…` | 刪除／改名（見 C2、C3） |
| 讀者追溯清單 | 見 DESIGN §2.4 | 需重跑 `sync_axiom_reader.py` |
