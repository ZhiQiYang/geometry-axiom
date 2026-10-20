# #299 測試與驗證計畫

> 基底 `09ab5f79`。本輪**沒有建置、沒有跑任何測試**；下面 §A 只列我實際做過的靜態檢查，§C 起的「預期」都是推導值，等 WSL 空閒再實跑驗證。

## A. 這一輪實際做過的靜態驗證（可重做）

| 檢查 | 做法 | 結果 |
|---|---|---|
| 補丁能套 | 暫時索引 `git read-tree 09ab5f79` + `git apply --check --cached patch.diff`；`GIT_OBJECT_DIRECTORY` 指到暫存目錄、`GIT_ALTERNATE_OBJECT_DIRECTORIES` 指到 repo，所以沒有寫進 repo 的物件庫、沒有動工作樹 | 通過 |
| 套完逐位元相同 | 真套進暫時索引，再把 13 個結果 blob 與我手上的目標檔逐位元比 | 13/13 相同 |
| 工作樹式套用 | 在 repo 外的暫存目錄放基底檔案副本，`git apply --check` 與真套 | 通過（本機 `core.autocrlf=true`，所以寫出的檔案是 CRLF，去掉 CR 後與目標檔相同） |
| Python 語法 | 對補丁後的 `.py` 做 `ast.parse` | 通過 |
| C 括號平衡 | 去註解與字串後數 `{}`、`()`、`[]` | 通過（**不是編譯**） |
| 突變錨點 | 解析補丁後 `mutate.py`，對 86 個編號突變逐一確認 `old` 在目標檔（LF 正規化後）恰好出現 1 次；M87、M88 的錨點文字沒動 | 全部為 1 |
| 單元控制項錨點 | `test_geo261_wood_contacts.py` 23 個、`test_geo261_wood_contact_world.py` 21 個控制項的 `before` 在各自函式／檔案中恰好 1 次；`wood_member_span_extension_check` 函式內沒有註解（`mutant()` 的前提） | 通過 |
| 凍結裁判保真 | 照新測試的邏輯，用 `git show 09ab5f79:tests/geo261_contacts_legacy_fixture.txt` 抽出舊守衛與舊字面，對補丁後 `contacts.c` 比 token | 守衛 token 相同、兩段舊字面都在 |
| 訊息模擬 | 從補丁後 `contacts.c` 抽出三段格式字串，用 Python 重現 `snprintf`，對照 harness 與 `run_tests.py` 的每個期望字串 | 全部逐字相同 |
| 計數 | `TESTS` 長度與 `run_all.expected.json` 一致（165）；`test_geo261_wood_contact_world.py` 測試方法數一致（10） | 一致 |
| 讀者追溯影響 | 用 `axiom_matrix` 的 `code_sites`／`scene_hits`／`mutant_hits` 對補丁後檔案重算 | 無燈號變化；I22 的變異清單 +M89–M96 |

**沒做**：任何編譯（含 MSVC `cl`、WSL `gcc`）、任何 `run_tests`／unittest／`mutate.py`／`sync_axiom_reader.py`、任何瀏覽器驗收。

## B. 預期的診斷全文（實跑第一步：先對照這四行）

套補丁、建好 core 後先手動跑（命令列形式取自 `run_tests.py:269`）：

```
<core.exe> --scene _s1_p8_l_room_primary_through_reflex_extension.scene --no-window
<core.exe> --scene _s1_p8b_l_room_primary_through_reflex_extension_hi.scene --no-window
```

預期結束碼 1，stderr 該行 `<路徑>:<行號>: ` 之後逐字為：

| 場景 | 預期訊息 |
|---|---|
| p8 | `V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e3 [3000,4800] mm，低端超出 [27,3000] mm` |
| p8b | `V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e1 [0,1800] mm，高端超出 [1800,4773] mm` |
| `_role_priority_mutant.scene`（只釘前綴，不用動） | 以 `V_EXTENSION：非 boundary 角材（1）的 footprint 超出定位邊範圍——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm` 開頭（此行是我推導的，非釘住） |

若數字和上表不同：**先確認是不是我的推導錯**（`wood_member_boundary_props` 選哪條邊、`start/end` 實際值），再改 `run_tests.py` 的釘住值，不要改程式去湊。

## C. 斷言清單

### C1. 場景級（`tests/run_tests.py`）

| 場景 | `error`（同一行診斷須逐項全含） | `error_not`（該行不得含） |
|---|---|---|
| p8 | 前綴 `V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍`、`定位邊 e3 [3000,4800] mm`、`低端超出 [27,3000] mm` | `高端超出` |
| p8b | 前綴（同上）、`定位邊 e1 [0,1800] mm`、`高端超出 [1800,4773] mm` | `低端超出` |

runner 本身的改動（`run_one`）：`error` 接受字串或清單；`error_not` 只能用在 reject（否則回 `INFRA`）；單一字串時失敗訊息格式與舊版完全相同（`FAIL 錯誤不符: 期望含「…」實得「…」`）。

### C2. W 單元（`tests/geo261_contacts_harness.c`，`span` 案）

`span-no-edge`、`span-accept-output-unchanged`、`span-boundary-extension`、`span-touch-equality`、`span-contained`、`span-low-refusal`、`span-error-exact`（低端整句）、`span-legacy-prefix`（舊整句是前綴）、`span-high-refusal`（`err==NULL`）、`span-high-refusal-message`、`span-high-error-exact`（高端整句）、`span-both-refusal`、`span-both-error-exact`（兩端整句）、`span-unknown-role-not-boundary`。
`buffer` 案：容量 0／1／8／21／512 的截斷、結尾 NUL、尾巴不動，全部沿用，只換成新句；`full-id-text` 用 `UINT32_MAX` 驗整句。
`equivalence` 案：3000 組隨機輸入對凍結裁判，裁決一律相同；截斷容量（0／1／19）逐位元相同；完整容量時舊句是新句的嚴格前綴。

### C3. W 單元（`tests/geo261_contact_world_harness.c`）

- `intervals`：`boundary-edge-index-horizontal`（elbow，水平 → e2、[50,100]）、`boundary-edge-index-vertical`（垂直 → e3、[50,100]）、`boundary-edge-failure-leaves-outputs`、`boundary-edge-null-index-accepted`。
- `ends`：`extension-refusal-precedes-contact` 由 `strstr` 改整句，驗證編號確實從定位函式流到訊息。

### C4. H 單元（`tests/geo261_host_facts_authority_harness.c:291`）

`facts-span-error-precedes-source-failure` 的期望整句換新（elbow：`e2 [50,100]`，`低端超出 [0,50]`）。

### C5. Python 控制項（拿掉就轉紅，W 單元層）

`test_geo261_wood_contacts.py::test_guard_controls_fail_named_independent_assertions` 新增：

| 控制項 | 替換 | 應轉紅的斷言 |
|---|---|---|
| span-edge-id | `edge_index`→`0` | `span-error-exact` |
| span-edge-interval | `edge_lo` 印成 `span_lo` | `span-error-exact` |
| span-low-clause | `if (edge_lo > span_lo)`→`if (0)` | `span-error-exact` |
| span-high-clause | `if (edge_hi < span_hi)`→`if (0)` | `span-high-error-exact` |
| span-low-always | →`if (1)` | `span-high-error-exact` |
| span-high-always | →`if (1)` | `span-error-exact` |

`test_geo261_wood_contact_world.py`：`edge-index-output`（`if(out_edge)*out_edge=edge;`→`(void)edge;`）→ `boundary-edge-index-horizontal`。

## D. 帳本突變預期（`tests/mutate.py`）

| 編號 | 預期結果 | 預期 `killed_by`（TESTS 順序，最多 5 個） |
|---|---|---|
| M87（既有） | killed | `_role_priority_mutant`、p8、p8b（與舊帳本相同） |
| M88（既有） | killed | p8b |
| M89 | killed | `_role_priority_mutant`、p8、p8b |
| M90 | killed | p8、p8b |
| M91 | killed | p8、p8b |
| M92 | killed | p8 |
| M93 | killed | p8b |
| M94 | killed | p8b |
| M95 | killed | p8 |
| M96 | killed | p8、p8b |

**判讀陷阱**：M90、M91 同時改格式字串與引數，若寫錯會「編譯失敗」→ 帳本記 `invalid`／`blocked`，**不算 killed**。實跑時如果看到 `invalid`，先看編譯錯誤，不要當成牙齒。

## E. 實跑步驟（WSL 空閒、遊戲未開時）

1. `git apply --check patch.diff && git apply patch.diff`（基底 `09ab5f79` 或其後續的 GEO-261 整合分支）。
2. 建 core／bridge：照既有流程（`tests/binaries.py`、`tests/run_all.py`），不要自己拼指令。
3. §B 的兩個手動指令，對照訊息全文。
4. `python tests/run_tests.py <core exe>`：預期 165/165，p8、p8b 為 PASS。
   - **負向確認**（證明新機制有牙齒）：暫時把 p8 的 `'定位邊 e3 [3000,4800] mm'` 改成 `'定位邊 e4 [3000,4800] mm'` 應得 `FAIL 錯誤不符: 期望含「…」且含「…」…`；暫時在 p8 的 `error_not` 加 `'低端超出'` 應得 `…且不含「高端超出」「低端超出」實得…`。確認後還原。
5. W 單元：`python tests/test_geo261_wood_contacts.py`、`python tests/test_geo261_wood_contact_world.py`（需要 C 編譯器，Windows 本機沒有 gcc，走 WSL）。
6. 純 Python：`python tests/test_geo261_mutation_migration.py`（驗 36 個登記與錨點）、`python -B tests/test_product_architecture.py`、`python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`。
7. 針對性突變（不覆蓋正式帳本）：`MUTATE_RESULTS=<暫存路徑>.json python tests/mutate.py M87 M88 M89 M90 M91 M92 M93 M94 M95 M96`，對照 §D。
8. 與 #316 合併後一次重產整份帳本（`python tests/mutate.py`，約 2 小時）→ `python tests/mutate.py --check`；再 `python3 geometry-guide/sync_axiom_reader.py`、`--check`、`python3 tests/test_axiom_reader.py`；`tests/run_all.py` 的完整閘（計數表 `tests/run_all.expected.json` 在本補丁不變：沒有新場景、沒有增減測試方法）。

## F. 已知會因本補丁改變的既有斷言（審查時逐條看）

| 位置 | 原本 | 現在 |
|---|---|---|
| `geo261_contacts_harness.c` `span-error-exact` | 舊整句 | 低端整句 |
| `geo261_contacts_harness.c` `full-id-text` | 舊整句（id 4294967295） | 新整句 |
| `geo261_contacts_harness.c` `equivalence` | 與凍結裁判逐位元相同 | 裁決相同＋截斷相同＋完整時舊句為嚴格前綴 |
| `geo261_contact_world_harness.c` `extension-refusal-precedes-contact` | `strstr(…,"V_EXTENSION")` | 整句相等 |
| `geo261_host_facts_authority_harness.c:291` | 舊整句 | 新整句 |
| `test_geo261_wood_contacts.py` 保真測試 | 整個函式 token 相同 | 守衛 token 相同＋舊字面逐一出現 |
| `run_tests.py` p8、p8b | 只釘前綴 | 欄位逐項釘＋`error_not` |
