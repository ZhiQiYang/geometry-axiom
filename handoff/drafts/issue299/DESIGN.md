# #299 設計：V_EXTENSION 診斷要指名定位邊與超出的區間（I22 W 段）

> 草稿，基底 `09ab5f79`（GEO-261 整合分支 head）。**只讀程式、只寫文字檔；沒有建置、沒有跑任何測試。**
> 補丁：`patch.diff`（對 `09ab5f79` 通過 `git apply --check`，驗證方式見 `TESTS.md` §A）。
> 公理層 `公理層.md` 不動：I22 W 段（`公理層.md` 約 1339–1351 行）早已寫「違反本條 → 拒絕（V_EXTENSION），訊息指名料件、定位邊與超出的區間」，本案是把實作補齊，不是新增條文。

## 1. 結論

- V_EXTENSION 的決定與訊息在 **W**：`geometry-templates/woodworking/native/contacts.c` 的 `wood_member_span_extension_check`（4–20 行）。issue 寫的 `current_geometry.c` 約 7770 行 `timber_end_face_check` 在 GEO-261 後已是 5 行 H 轉接器（`current_geometry.c:6011–6018`），**本補丁不碰 `current_geometry.c`**，所以 issue 擔心的「整合時還要再移植一次」不成立。
- 缺的資訊只有一項：定位邊的編號。區間（`edge_lo`/`edge_hi`）、超出量（`span_lo`/`span_hi`）呼叫端早已算好；編號 `edge` 在 `wood_contact_boundary_interval`（`contact_world.c:86–96`）內部有，但只回傳區間。
- 做法：新增 W 函式 `wood_contact_boundary_edge`（多回報編號），`wood_contact_boundary_interval` 變成它的薄包裝；`wood_member_span_extension_check` 多收一個 `edge_index`；訊息**以舊訊息為完整前綴**，後面接定位邊與超出區間。

## 2. 訊息格式

```
V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e3 [3000,4800] mm，低端超出 [27,3000] mm
V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e1 [0,1800] mm，高端超出 [1800,4773] mm
V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e2 [5,10] mm，低端超出 [0,5] mm，高端超出 [10,12] mm   （兩端都超出時的示意）
```

| 欄位 | 內容 | 來源 | 為何這樣寫 |
|---|---|---|---|
| 料件 | `角材（3）` | 既有，`self->id` | 沿用，不動 |
| 定位邊 | `e3` | 新：outline 邊索引 | 與 I20 的 `V_BOUNDARY_ROLE：…外輪廓邊 e%d`（`member_reference.c:319`、`334–336`）同一寫法，也是場景語法 `at-face e3` 的寫法 |
| 定位邊區間 | `[3000,4800] mm` | 既有 `edge_lo,edge_hi` | 沿長度軸的座標；括號寫法同 `member_reference.c:138` 的 `span[%lld,%lld]` |
| 超出區間（低端） | `低端超出 [span_lo,edge_lo] mm` | 既有 | 足跡低座標端伸出定位邊低端的那一段 |
| 超出區間（高端） | `高端超出 [edge_hi,span_hi] mm` | 既有 | 同上，高端；兩端都超出就兩段都印，沒超出的那端不印 |

- 全形標點（`：`、`——`、`，`）、`mm` 單位、`e%d` 沿用現有診斷風格；用「低端／高端」是因為 issue 與場景檔名（`_hi`）就是這麼稱呼。
- 為何用「保留舊訊息為前綴」：`_role_priority_mutant.scene` 只釘 `V_EXTENSION：非 boundary 角材（1）` 的前綴，不必動；測試裡的凍結裁判（§5）可以改成「舊字面是新字面的前綴」而不是整句重寫。
- **不印軸字母**。長度軸座標是 u 或 v 由定位邊 `e<i>` 決定（垂直邊的區間就是 v），加軸字母要再多帶一個參數、也沒有 u 向場景能釘它。
- **位元組預算**：UTF-8 下典型 135 B（p8 136 B、p8b 135 B）。放置路徑在單一候選時最終顯示的是 `first_check`（`member_reference.c:126,133` → `set_revalidate_error`，緩衝 256 B），完整保留；多候選時顯示 `reference_issue` 格式化的 `last`（`"%.190s"` 只限制訊息本身，前綴在限制之外）。**重驗路徑**（`reference_check_all`：`references.inc:648` → `reference_issue`）同樣把訊息截成 190 B，極端值（id 4294967295、座標 ±1e8、兩端都超出）約 212 B 時會截掉最後一段。典型情況安全；需要更保險時可把「高端」排在「低端」前面或縮短前綴，我沒動（避免改動舊前綴）。

## 3. 現況與改動點（09ab5f79）

三條進入路徑，最後都走同一個 W 函式：

| 路徑 | 呼叫鏈 |
|---|---|
| 放置 | `member_reference.c:125 w->end_faces` → H `app_member_reference_end`（`references.inc:555`）→ H `app_reference_end_faces`（`reference_sources.inc:663`）→ W `wood_contact_end_faces_with_sources`（`contact_world.c:113`）→ **W `wood_member_span_extension_check`** |
| I8a 全量重驗 | `reference_check_all`（`references.inc:648`）→ 同上 |
| 最終世界重驗 | `world_validation.c:56 context->end_faces` → H `app_validation_end_faces`（`world_validation.inc:58`）→ 同上 |

另有「沒有 ctx / 用目前值」的分支走 H `timber_end_face_check`（`reference_sources.inc:668`），它轉呼叫同一個 W 函式。**所以只要改 W 一處，三條路徑的訊息一起變。**

改動檔案（`patch.diff`，13 檔）：

| 檔案 | 改什麼 |
|---|---|
| `geometry-templates/woodworking/native/contacts.h` / `.c` | `wood_member_span_extension_check` 多一個 `int edge_index`；訊息組裝（`low_note`/`high_note` 兩個局部緩衝 + 一次 `snprintf`）。函式內**不能有註解**（`test_geo261_wood_contacts.py::mutant()` 要求「去註解的定義」逐字出現在原始檔裡），說明寫在函式外 |
| `geometry-templates/woodworking/native/contact_world.h` / `.c` | 新 `wood_contact_boundary_edge(...,int *out_edge)`（原函式本體搬過來，成功時才寫 `*out_edge`，`out_edge` 可為 NULL）；`wood_contact_boundary_interval` 變成呼叫它的一行包裝；`wood_contact_end_faces_with_sources` 改呼叫新函式並把 `edge_index` 傳給檢查 |
| `tests/geo261_contacts_harness.c` | 新簽名；`SPAN_ERROR`/`full-id-text` 改新全文；新增高端／兩端／舊前綴三個斷言；`equivalence` 對凍結裁判的比較由「逐位元相同」改成「裁決相同、截斷處相同、完整長度時舊文是新文的嚴格前綴」 |
| `tests/geo261_contact_world_harness.c` | `intervals` 加 4 個編號斷言（水平 e2、垂直 e3、失敗不寫輸出、NULL 可接受）；`ends` 的 `strstr(error,"V_EXTENSION")` 改成整句相等 |
| `tests/geo261_host_facts_authority_harness.c` | 291 行一個整句相等的期望字串換成新訊息（elbow 場景：`e2 [50,100]`、`低端超出 [0,50]`） |
| `tests/test_geo261_wood_contacts.py` | 原始碼保真測試：整函式 token 相等 → 「守衛 token 相等 + 舊字面逐一出現」；新增 6 個欄位控制項 |
| `tests/test_geo261_wood_contact_world.py` | 新增 `edge-index-output` 控制項；方法名去掉已不實的 `twenty` |
| `tests/run_tests.py` | `error` 可寫清單（同一行診斷逐項全含）、新增 `error_not`；p8、p8b 改釘完整欄位 |
| `tests/mutate.py` | 新增 M89–M96（§6） |
| `tests/test_geo261_mutation_migration.py` | 登記 M89–M96 的目標檔，計數 28→36 |
| `geometry-core/domain-decoupling/product-architecture.json` | `policy.forbiddenIdentifiers` 補 `wood_contact_boundary_edge`（目前清單對 W 標頭宣告的 324 個 `wood_*` 函式是完整的，我維持完整；沒有測試強制） |

## 4. 為何 p8、p8b 能各自驗完整欄位

位置：#295 釘的 S1 場景在 `tests/run_tests.py:247–252`（`TESTS` 清單尾段），場景檔 `_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`；對應的帳本突變是 `tests/mutate.py:359–366` 的 M87（整個拒絕拿掉）與 M88（只驗起點那半）。要改的斷言（現狀只有 `'error': 'V_EXTENSION：非 boundary 角材（3）'` 一個前綴）：

```python
# p8（低端）
'error': ['V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍', '定位邊 e3 [3000,4800] mm', '低端超出 [27,3000] mm'],
'error_not': ['高端超出'],
# p8b（高端）
'error': ['V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍', '定位邊 e1 [0,1800] mm', '高端超出 [1800,4773] mm'],
'error_not': ['低端超出'],
```

- p8（`_s1_p8_…`）：凹角在定位邊 `e3`（v 3000..4800）的**低端**，足跡 v∈[27,4773]。只有低端超出：釘 `角材（3）…範圍`、`定位邊 e3 [3000,4800] mm`、`低端超出 [27,3000] mm`，並要求同一行**不得**出現 `高端超出`。
- p8b（`_s1_p8b_…_hi`）：凹角在定位邊 `e1`（v 0..1800）的**高端**。只有高端超出：釘 `定位邊 e1 [0,1800] mm`、`高端超出 [1800,4773] mm`，且**不得**出現 `低端超出`。
- 兩個場景各只有一端超出，所以「兩段 clause 的條件」各被一個場景單獨管：拿掉某一段，對應場景轉紅；把某一段改成無條件印（會印出 `[27,0]` 這種假區間），`error_not` 轉紅。沒有 `error_not`，「多印」這種錯誤用子字串比對看不出來。
- 兩端都超出、u 向、極端值等組合沒有場景級夾具，改由 W 單元 harness（`geo261_contacts_harness.c` 的 `span`/`buffer` 案）整句比對。

## 5. 被牽動的既有釘住（必須一起改，否則轉紅）

GEO-261 為證明「搬進 W 之後行為不變」立了幾道凍結裁判，V_EXTENSION 訊息這次是**刻意的行為變更**，所以：

1. `tests/geo261_contacts_legacy_fixture.txt`（雜湊釘死）**不動**。新訊息保留它的兩段字面片段，原句仍是新句的前綴。
2. `test_policy_blocks_preserve_frozen_product_decisions_and_error_text`：改為比對「守衛條件 token」與「舊字面片段」，不再要求整個函式 token 相同。`wood_member_end_contact_check` 的整函式比對維持不變。
3. `geo261_contacts_harness.c::equivalence`：同上，改成前綴關係。
4. 兩個整句相等的舊字串（`geo261_contacts_harness.c` 的 `full-id-text`、`geo261_host_facts_authority_harness.c:291`）換新句。

這是本案最需要審查者點頭的一處（見 §9 第 3 項）：它放寬了「凍結裁判」的嚴格度，但只放寬在訊息尾巴，決定（守衛）與舊前綴仍逐字保真。

## 6. 突變（`tests/mutate.py` 新條目）

全部是對**訊息**的單點替換，`old` 在目標檔中恰好出現一次（我用腳本對補丁後的檔案逐條驗過）。

| 編號 | 檔案 | 拿掉／改壞什麼 | 預期殺手 |
|---|---|---|---|
| M89 | contacts.c | 料件欄位（id 固定印 0） | `_role_priority_mutant`、p8、p8b |
| M90 | contacts.c | 定位邊編號 `e<i>`（格式與引數一併拿掉） | p8、p8b |
| M91 | contacts.c | 定位邊區間 `[edge_lo,edge_hi] mm` | p8、p8b |
| M92 | contacts.c | 「低端超出」整段（`if (edge_lo > span_lo)`→`if (0)`） | p8 |
| M93 | contacts.c | 「高端超出」整段 | p8b |
| M94 | contacts.c | 「低端超出」無條件印 | p8b（靠 `error_not`） |
| M95 | contacts.c | 「高端超出」無條件印 | p8（靠 `error_not`） |
| M96 | contact_world.c | W 不回報定位邊編號（`if(out_edge)*out_edge=edge;`→`(void)edge;`，訊息變 `e-1`） | p8、p8b |

既有 M87（整個拒絕拿掉）、M88（只驗起點那半）的錨點文字**一字未動**，仍唯一；它們的殺手集合不變。
同樣的欄位控制項在 W 單元層也各有一個（`test_geo261_wood_contacts.py` 6 個、`test_geo261_wood_contact_world.py` 1 個），所以 W 層不必等整份帳本重產就能看到牙齒。

`killed_by` 只存 TESTS 順序前 5 個失敗夾具：M92–M96 的殺手 p8/p8b 位置在清單中段，不會被擠掉。

## 7. 帳本／讀者連鎖（請和 #316 合成同一次重產）

使用者提醒「改 `current_geometry.c` 或 `tests/mutate.py` 會讓帳本過期」。實際範圍更大，已逐項讀程式確認：

- `closure_sha256` 是 `current_geometry.c`（加 `geometry-web/web_bridge.c`）**整個 `#include` 閉包**的雜湊（`mutate.py:638–670`），所有紀錄共用同一個值。本補丁雖然沒改 `current_geometry.c`，但改了閉包內的 `contacts.c/.h`、`contact_world.c/.h` → **整份帳本仍然過期**。
- `oracle_sha256` = `run_tests.py` + 所有被 `TESTS` 引用的 `.scene`（`mutate.py:675–690`）；本補丁改了 `run_tests.py` → 所有 killed／survived 紀錄再失效一次。bridge 類突變的裁判還含 `tests/*.py` 與根目錄場景。
- 讀者（`geometry-guide/公理層-閱讀器.html`）的追溯區塊由 `axiom_matrix` 推導：本補丁只讓 I22 的「變異」清單多 M89–M96。我用 `axiom_matrix` 的函式對補丁後的檔案模擬過：**沒有任何條文的燈號改變**（`test_axiom_reader.py::test_traceability_lights…` 比的是燈號），但清單文字會過期，依 `AGENTS.md` 仍須重跑 `sync_axiom_reader.py`、`--check`、`tests/test_axiom_reader.py`。
- 編號 M89–M98 是暫定（#299 用 M89–M96，#316 用 M97–M98）；合入時若別的分支已佔用，整批改號即可（結果檔以編號為鍵，重產時才會寫入）。
- 其他草稿（#300、#314）和本補丁會碰同一批熱點檔（`contact_world.h`、`geo261_contact_world_harness.c`、`run_all.expected.json`…）；我用暫時索引試過 `#300`、`#314` 先套再套 #299 都能 `--check` 通過，但沒有看語意衝突。

## 8. 沒有做的事

- 沒有改 `current_geometry.c`（不需要）、沒有碰讀者 HTML、沒有重產帳本、沒有改 `BACKLOG.md`（GEO-264 狀態）。
- 沒有新增場景。u 向、兩端皆超出的場景級夾具可以另做，但訊息不含軸字母，目前沒有需要它的欄位。
- 衍生填充面（`derived_fill`）的 `e<i>` 語意見 §9。

## 9. 我最不確定的三件事

1. **整個補丁沒有編譯、沒有執行。** 最脆弱的是兩類字串：場景級的數字（p8 的 `e3 [3000,4800]`、span `[27,4773]`；p8b 的 `e1 [0,1800]`）來自場景檔頭註解加上對 `wood_member_boundary_props` 的人工推導，單元 harness 的 `e2`／`e3` 也是人工推導；任何一個數字和實跑不同，對應斷言就會誤紅。建議第一步：套補丁、建置後先手跑 p8、p8b 看 stderr 那一行是不是和 `TESTS.md` §B 的預期逐字相同，再信任 `run_tests`。C 語法我只做了括號平衡與模擬輸出比對。
2. **衍生填充面上的 `e<i>` 語意。** 傳進 W 的 `role_boundary` 只是該元件的外輪廓，`edge` 是元件內索引；但場景語法／R41 在衍生面上不允許 `e<i>` 別名，內部擋面編號是 `component*GEO_LOOP_MAX_VERTICES+i`（`contact_world.c:42–44`）。我沿用 I20 訊息（也是元件內索引）的作法，沒有加元件編碼。若要印得和擋面編號一致，需要在 `wood_contact_end_faces_with_sources` 找出 `role_boundary` 是 `regions[]` 的第幾個——但 `app_contact_facts` 把有效邊界複製進 `facts->effective`（`current_geometry.c:5774`），指標比對不可靠，可能得改比 `id`。這是設計決定，不是我能靜態判定的。
3. **放寬凍結裁判是否被接受。** §5 的三處測試改動是 GEO-261 當初為防止「搬移時偷改行為」而立的牢籠的鬆綁；我的理由是行為變更有明文依據（I22 W）、且舊前綴與守衛仍逐字保真，但這是審查者的判斷。替代做法：保留 `wood_member_span_extension_check` 原樣、把細節在 `wood_contact_end_faces_with_sources` 事後追加到 `error` 尾巴——不用動凍結裁判，代價是要處理緩衝已被截斷的情況、而且舊函式變成只為測試而存在的死碼（正是 #316 在處理的病）。我沒選它。
