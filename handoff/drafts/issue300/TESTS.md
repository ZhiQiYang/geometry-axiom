# Issue #300 測試與突變草稿

> 與 `DESIGN.md` 配套。對 `09ab5f79` 寫成;**沒有編譯、沒有執行任何測試**。`patch.diff` 已含本檔說明的全部測試與控制組(除 §7 標明「不在 patch」的)。
> 規則沿用 repo 現有測試的誠實性約定:控制組必須先過基線、再讓「改過的版本」以**指名的斷言**失敗(`stderr` 逐字等於 `ASSERT:<標籤>\n`)、再還原過基線;編譯失敗、原生崩潰、逾時都不算偵測。唯一的例外是編譯期綁定(§5 的 C09–C13):它們的失敗模式本來就是編譯失敗,所以改成「基線必須先編得過,改過的版本必須編不過,且輸出必須含該檢查的名字(gcc)或 `C2118`(MSVC)」。

## 1. 情境矩陣:五個常數 × 「剛好 N」「第 N+1」

N = `WOOD_MEMBER_CAPACITY` = 512。「新增」= 本 patch 新寫;「更新」= 既有測試改成以巨集為準;「既有」= 沒動;「建議」= 不在 patch(§7)。

| # | 常數 | 守什麼 | 剛好 512 | 第 513 | 測試 |
|---|---|---|---|---|---|
| 1 | `WOOD_MEMBER_CAPACITY`(`members.h`,原 `document.h:20`) | 儲存 `timbers[]`/`anchors[]` | 512 支宣告後,DSL dump 恰有 512 行 `timber …` | **沒有第 513 槽**(結構上不可能);由 #2 的拒絕擋;編譯期 `app_timber_capacity_timbers/anchors_check` | T10(新增,`declared==512`);T12 C10(新增);T04 `capacity-pinned-512`(新增)、T09 C07(新增) |
| 2 | `WORLD_MAX_TIMBERS`(`current_geometry.c:2741`) | 宣告准入、工程還原、組構生成、PF-3 | 第 512 支宣告成功;滿容量時重宣告既有 id = 更新,成功 | 第 513 支新 id → `角材的數量超過上限`,**dump 逐字不變** | W 層 T05(新增);H 層 T10(新增);接線 T02(新增)、T11 C08(新增) |
| 3 | `WOOD_CONTACT_MEMBER_CAPACITY` | 接觸成員事實陣列;`axes[]`;`facts_valid` | `wood_contact_collect_stops` 以 512 個成員 → 144+1024=1168 面,尾端未被碰(既有 `regions` 案例,已更新);`wood_world_validate_members` 512 個成員通過(T06) | `member_count=513` → `I33 CAPACITY`,**一個 callback 都沒被呼叫**(T06,新守門) | T06;`contact_world_harness`(更新);`facts_valid`(`contact_sources.c:73`)的 N+1:建議(§7 O1) |
| 4 | `WOOD_CUT_LIST_MEMBER_CAPACITY` | 報告入口守門與 `groups[]`/`ids[]` | 512 支一群、512 支分兩群(偏移對)皆正確 | 513 → `false`,`out` 逐位元不變;`NULL` 輸入同 | `geo261_report_policy_harness.c` `limits`(更新 + 新斷言);T08(新增) |
| 5 | `WOOD_MEMBER_SPAN_MEMBER_CAPACITY`(+ `WOOD_MEMBER_SPAN_CUT_CAPACITY`) | span 暫存 `ca/cb`(2N)、`hit`(4N)、`cuts` | 純暫存上界,沒有執行期 N+1(候選數取決於參照命中的面,不是角材數) | —— | 編譯期 `app_timber_capacity_span_check`、既有 `app_span_scratch_bound_check`;T12 C13;T04 `capacity-span-*-derived`;功能面「512 支已放置時 `resolve_auto_span` 跑得完」只能靠探針(建議 O7) |
| 派生 | `WOOD_CONTACT_FACE_CAPACITY`(2432 → 3328)、`STOP_FACE_MAX` | 停止面陣列 | `contact_world_harness` `face-capacity-contract`(更新成公式);T04 `capacity-contact-faces-derived`、`capacity-face-bounds-agree` | —— | 編譯期 `app_timber_capacity_stop_face_check`(新增,原本沒有) |

各路徑的 N+1 現況(誠實清單):
- **宣告**(`apply_timber_line` → `wood_member_declaration_capacity`):W 與 H 兩層都有 N/N+1(T05、T10)。
- **工程還原**(`engineering_commands.inc:31` → `engineering_operations.c:63` `*member_count==member_capacity`,訊息 `I10: timber ID exists or capacity exceeded`):W 層由既有參數化 harness 覆蓋小容量;**H 的接線只有純文字釘住**(T02)。產品層 512/513 筆還原:建議(§7 O4)。
- **組構生成**(`assembly.c:380` `member_count+3>member_capacity`):同上,接線釘住(T02);產品層「509 支 + 一個實例 = 512 接受、510 支 + 實例 = 拒絕」:建議(§7 O4)。
- **PF-3**(`panel_fill_support.inc:37,39,61`):footprint 數 ≤ 已放置角材數 ≤ N,所以 **N+1 不可達**,只有 N 有意義;接線釘住(T02)。512 個 footprint 的 PF-3 耗時沒有數據:建議(§7 O6)。

## 2. 新增測試(`tests/test_geo261_timber_capacity.py`,12 個)與其 C harness

`tests/geo261_timber_capacity_harness.c` 的案例:`values`、`declaration`、`validation`。數字 512 只在 `values` 的 `capacity-pinned-512` 釘一次;其餘全用巨集。Python 側的 `CAPACITY` 從 `members.h` 讀。

| ID | 類別 / 方法 | 內容 | 失敗標籤 / 訊息 |
|---|---|---|---|
| T01 | `TimberCapacitySource.test_one_definition_and_every_other_name_is_derived_from_it` | 純文字(不編譯):在 `current_geometry.c`、`geometry-core/*`、`geometry-app/native/*`、`geometry-templates/woodworking/native/*`、`geometry-web/*` 內,`WOOD_MEMBER_CAPACITY` 恰一個 `#define`(在 `members.h`,值是數字)、其餘四個名字各恰一個 `#define` 且值恰為 `WOOD_MEMBER_CAPACITY`;`WOOD_MEMBER_CAPACITY = …` enum 形式不得回來 | 指名檔案與名字 |
| T02 | 同上 `…hands_the_single_constant_to_every_capacity_consumer` | 純文字:宣告准入、`assembly.inc`、`engineering_commands.inc`、PF-3(兩處)都傳 `WORLD_MAX_TIMBERS`;host 內有 7 條 `app_timber_capacity_*_check` | 指名子字串 |
| T03 | 同上 `…cut_list_ids_are_one_flat_array_not_one_array_per_group` | 純文字:`ids[` 不得出現在 `WoodCutGroup` 內,只出現一次且在 `WoodCutList` 內 | |
| T04 | `NativeTimberCapacity.test_value_is_pinned_once_and_every_derived_bound_follows_it` | harness `values`:值 = 512;三個暫存別名 = 容量;`WOOD_CONTACT_FACE_CAPACITY`、`WOOD_MEMBER_SPAN_CUT_CAPACITY` 等於公式 `組件×32×9+2N`;兩者相等 | `capacity-pinned-512`、`capacity-contact-members-derived`、`capacity-cut-list-members-derived`、`capacity-span-members-derived`、`capacity-contact-faces-derived`、`capacity-span-cuts-derived`、`capacity-face-bounds-agree` |
| T05 | `…test_declaration_walks_the_real_capacity_slot_n_accepted_and_slot_n_plus_one_refused` | harness `declaration`:以真容量走 512 筆(`wood_member_declaration_capacity` 放行、`wood_member_declare` 附加);第 513 個新 id 與「不帶 id」都被拒且訊息逐字 `角材的數量超過上限`;既有 id(第一筆與最後一筆)仍放行;拒絕不寫入(78 KB 陣列逐位元不變) | `declare-slot-accepted`、`declare-slot-appended`、`declare-exact-capacity-reached`、`declare-over-capacity-refused`、`declare-over-capacity-without-id-refused`、`declare-existing-at-capacity-allowed`、`declare-refusal-writes-nothing` |
| T06 | `…test_world_validation_refuses_more_members_than_the_contact_capacity_before_reading_any` | harness `validation`:`wood_world_validate_members` 以 512 個未放置成員 → `true` 且 `error` 不動;513 → `false`、訊息以 `I33 CAPACITY` 開頭、`member_at` 被呼叫 0 次 | `validation-exact-capacity-accepted`、`validation-over-capacity-fails-closed-before-reading` |
| T07 | `…test_boundary_guards_fail_their_named_assertions_and_restore` | 控制組 C01–C04(§5),`subTest` | 各自標籤 |
| T08 | `…test_cut_list_guard_accepts_exactly_capacity_and_the_report_stays_linear` | 控制組 C05、C06 | `report-capacity`、`report-linear-size` |
| T09 | `…test_changing_the_value_fails_only_the_pin_because_every_other_bound_derives_from_it` | 控制組 C07 | `capacity-pinned-512` |
| T10 | `ProductTimberCapacity.test_bridge_accepts_exactly_capacity_timbers_refuses_the_next_and_keeps_the_world` | 真 bridge:`reset` 後逐行送 `line timber <id> 27 33 role primary`,id 從 1000 起;第 512 行 `ok`,第 513 行 `ok:false` 且 `error` 含 `角材的數量超過上限`;第 513 行前後的 `dump` 逐字相同;dump 恰有 512 行 `timber `;再送 `timber 1000 40 50 role secondary`(既有 id)為 `ok` | 以 `assertEqual(512, 首次拒絕的索引)` 等 |
| T11 | `…test_host_wiring_control_moves_the_actual_bridge_boundary_by_one` | 控制組 C08 | 首次拒絕索引 511 ≠ 512 |
| T12 | `…test_static_bindings_fail_the_build_naming_the_drifted_constant` | 控制組 C09–C13,`subTest` | gcc:輸出含 `app_timber_capacity_*_check`;MSVC:`C2118` |

注意:`objects` 指令只列**已放置**的角材,所以 T10 用 dump 計數;一條條宣告而不放置是可行的,因為 I9「收尾時仍有沒 place 的角材」只在**整份檔案載入結束**檢查(`_ax_i9_orphan_timber.scene`),互動式 `line` 不檢查。

## 3. 既有測試的調整(patch 內)

| 檔 | 改動 | 為什麼必須改 |
|---|---|---|
| `tests/geo261_report_policy_harness.c` | `grouping`:`groups[0].ids[0..1]` → `ids[groups[0].first+…]`;`ordering`:同;`limits`:開頭加 `report-linear-size`(`sizeof(WoodCutList) ≤ N·(sizeof(群)+4)+4·sizeof(size_t)`),以 `cap=WOOD_CUT_LIST_MEMBER_CAPACITY` 取代字面 64,新增「512 支分兩群」`report-capacity-two-groups-offsets`,`+1` 改 `cap+1` | `WoodCutGroup.ids` 消失;字面 64 失效 |
| `tests/geo261_contact_world_harness.c` | `regions` 案例:`face-capacity-contract` 改成公式 + `==WOOD_MEMBER_CAPACITY`;64 個成員 → `MEMBERS`(=容量);期望 `n==144+2×MEMBERS`,第一筆成員面 `timber_id==100+MEMBERS-1`,尾端 `timber_id==100`;斷言標籤改名 `…full-member-capacity` | 原本寫死 `2432`/`64`/`272`/`163` |
| `tests/run_all.py` | `PY_NEEDS` 加 `'test_geo261_timber_capacity': []` | 未登記的測試檔會讓 `run_all` 失敗並點名 |
| `tests/run_all.expected.json` | 加一個 suite(§6) | 完整跑時逐 suite 嚴格相等 |

**刻意沒動、且仍會通過的**(已逐一查過):
- `tests/geo261_member_declaration_harness.c`:參數化容量(`init(&f,64)`、66 格陣列),不讀產品常數。
- `tests/test_geo261_panel_native.py:82`、`tests/geo261_panel_harness.c` 的字面 64:凍結舊演算法 oracle 自帶的常數 / 傳給函式的顯式上限(DESIGN §2)。
- `tests/geo261_host_authority_harness.c:152-154`、`tests/pf3_algorithm.c:28,31`:已用巨集;堆疊上的 `anchors[N]` 從 111 KB 變 889 KB,遠低於 8 MiB。
- 全部既有控制組的錨點:`cut_list.c` 的 `if(!member->placed)continue;`、`&&group->role==member->role`、`right->length>left->length`;`world_validation.c` 的所有錨點;`contact_world.c`、`member_declaration.c` 的錨點。**我用腳本逐一數過,改後仍各恰好一次。** `tests/mutate.py` 的 M36/M37/M56(錨在 `world_validation.c`)同樣不受影響。

## 4. 為什麼不用 `mutate.py` 的情境 oracle 當主要防線

`tests/mutate.py` 的變異是針對 `run_tests.py` 的 165 個 `.scene` 場景(`core:run_tests`)。要用它殺掉容量守門,需要新增場景夾具,而:
1. 512 筆**只宣告**的場景會在檔尾因 I9 被拒;要通過就得放置 512 支,耗時見 DESIGN §9.1(未量測但量級是分鐘)。
2. 只有「第 513 筆被拒」的場景無法分辨「拒絕第 513 支」與「誤拒第 512 支」,因為 `run_tests.py` 比對診斷時把行號剝掉了(`re.findall(r"^<path>:(?:\d+:)?\s*(.*)$")`)。
3. 每個 `.scene` 都在 `oracle_sha256` 內,新增場景會讓所有判決再次過期(反正本單已讓全部過期,§6.2)。
先例是 `_edge_grid_overflow.scene`(GRID_MAX_LINES 的第 65 條)。若協調者仍想要,建議只加「513 筆 reject」一個場景當第二道網,N 精確度仍靠 T10。

## 5. 控制組(突變)清單:13 個

「紅在哪」= 該控制組啟用時失敗的測試與標籤。

| ID | 改什麼(檔 / 原文 → 新文) | 紅在 | 為什麼這個控制組有意義 |
|---|---|---|---|
| C01 | `member_declaration.c`:`if(*context->count==context->capacity){` → `if(*context->count+1==context->capacity){` | T07 / harness `declaration` / `declare-slot-accepted` | 少一槽(最後一槽被拒)。既有控制組 `capacity-first` 只在滿容量時測,抓不到 off-by-one |
| C02 | 同一處 → `if(*context->count>context->capacity){` | T07 / `declaration` / `declare-over-capacity-refused` | 多一槽(第 N+1 支被放行) |
| C03 | `world_validation.c`:整個守門(兩行)刪除 | T07 / `validation` / `validation-over-capacity-fails-closed-before-reading` | 守門被拿掉:`member_at` 被呼叫(`calls≠0`)且沒有 `I33` 訊息。夾具的 `member_at` 在 `i≥容量` 時回 `false`,所以突變版不會真的寫出界,不會崩潰 |
| C04 | 同守門:`>` → `>=` | T07 / `validation` / `validation-exact-capacity-accepted` | 剛好 N 被誤拒 |
| C05 | `cut_list.c`:`count>WOOD_CUT_LIST_MEMBER_CAPACITY)return false;` → `count>=…` | T08 / report harness `limits` / `report-capacity` | 剛好 N 被誤拒。**不做** `>` → `>+1` 這類「放行超量」的突變:會真的寫出界,變成崩潰,不是名字斷言 |
| C06 | 在**複製的** `cut_list.h` 的 `WoodCutGroup` 內加 `unsigned char reserved[WOOD_CUT_LIST_MEMBER_CAPACITY*4];` | T08 / `limits` / `report-linear-size` | 平方陣列回來了:仍可編譯(所以只有大小斷言能發現),三個目的檔與 client 都用同一份被改的標頭編譯 |
| C07 | 在**複製的** `members.h`:`#define WOOD_MEMBER_CAPACITY 512` → `1024` | T09 / `values` / `capacity-pinned-512` | **只有釘子會紅**:其餘別名全隨之變,證明「值」是唯一的自由度。只跑 `values`(不呼叫任何 W 函式),所以與原本編好的物件混連不會出 ABI 事故 |
| C08 | 複製的 host:`apply_timber_line` 的 `WORLD_MAX_TIMBERS,` → `WORLD_MAX_TIMBERS-1,` | T11:首次拒絕索引由 512 變 511 | 接線錯誤(編譯期綁定抓不到這種錯)。要重編一份被改過的 `web_bridge.c` 閉包 |
| C09 | 複製的 host:`#define WORLD_MAX_TIMBERS     WOOD_MEMBER_CAPACITY` → `…64` | T12:編譯失敗,含 `app_timber_capacity_world_check`(gcc)/ `C2118` | 五個常數之一又寫回字面 |
| C10 | 複製的 `document.h`:`WoodMember timbers[WOOD_MEMBER_CAPACITY];` → `timbers[64];` | T12:`app_timber_capacity_timbers_check` | 儲存與容量參數分叉(最危險的那種:編得過、會越界) |
| C11 | 複製的 `contact_world.h`:別名 → `64` | T12:`app_timber_capacity_contact_check`(同時 `…stop_face_check`) | |
| C12 | 複製的 `cut_list.h`:別名 → `64` | T12:`app_timber_capacity_cut_list_check` | |
| C13 | 複製的 `member_reference.h`:別名 → `64` | T12:`app_timber_capacity_span_check`(同時既有 `app_span_scratch_bound_check`) | |

所有「複製的」都在 `NativeBuild` 的暫存目錄內改,**不碰 repo**。基線先編譯過(`build.bridge()`、`build.cli()`),所以不是「環境壞了所以編不過」。

### 手動補充(不自動化)

- 把 `cut_list.c` 第二段迴圈裡的 `landed[discovered[i]]` 改成 `discovered[i]`:群被排序後 id 會落到錯的群 → 紅在 `report-capacity-two-groups-offsets`(單群案例分不出來,所以才加雙群案例)。
- 把排序迴圈整段刪掉:紅在既有的 `report-length-order`/`report-section-order`。

## 6. `run_all.expected.json` 會變動的計數

唯一的結構變動(patch 已含):

```json
"py:test_geo261_timber_capacity": { "mode": "count", "count": 12, "unit": "test" }
```
位置:`py:test_geo261_staged_candidate_graph` 與 `py:test_geo261_version_activation` 之間。這 12 = 檔案內 `def test_` 的數目(我用腳本數過)。

**不變的計數**(列出來是因為它們的檔案內容受影響,但 `count` 只算測試方法):
`py:test_geo261_wood_report_policy` 8、`py:test_geo261_wood_contact_world` 10、`py:test_geo261_wood_member_declaration` 9、`py:test_geo261_wood_world_validation` 14、`py:test_geo261_contact_sources` 12、`py:test_geo261_member_reference` 11、`py:test_geo261_native_document` 10、`py:test_geo261_panel_native` 10、`py:test_geo261_host_authority` 18、`py:test_architecture_contract` 205、`py:test_product_architecture` 18、`py:test_mutation_anchors` 3、`c:integrity` 432、`core:run_tests` 165。

**但這幾項的「內容」會變**:
- `c:integrity` 的日誌行 `World=…`:改前 4759448,改後 5605272(計算值;不是則 DESIGN §6 全部重算)。計數 432 不變。
- `mutation:check`(`exit-code-only`):**會紅**,直到整本突變帳本重跑(DESIGN §10.1)。這不是計數問題,是 `closure_sha256` 過期。
- `py:test_product_architecture`:應仍全綠(沒有新增產品檔案、沒有新增 `#include`、新增文字沒有 `??`);它掃的是即時樹,不比對 `product-architecture-receipt.json`。

**條件式**(只有協調者選了 §7 的對應項才會變):

| 選項 | 計數變動 |
|---|---|
| O1 contact_sources 成員 N/N+1 案例 | `py:test_geo261_contact_sources` 12 → 13 |
| O2 堆疊預算回歸網 | 新 suite 或併入 `py:test_geo261_timber_capacity` 12 → 13(併入較省) |
| 核心場景夾具(§4) | `core:run_tests` 165 → 166,且 `oracle_sha256` 變 |

## 7. 建議但**不在 patch** 的測試

| ID | 內容 | 為什麼不在 patch |
|---|---|---|
| O1 | `geo261_contact_sources_harness.c` 加 `member-capacity` 案例:facts callback 設 `member_count = 容量`(每個 `member` 指向夾具的某個成員、屬於別的 placement 以免被收集)→ `wood_contact_sources_collect` 成功;設 `容量+1` 且不填元素 → 回 `false`,`out`/`count` 不動,`facts_calls==1`。控制組:`contact_sources.c:73` 的 `>` → `>=` | 需要動既有 harness 的夾具與 `test_geo261_contact_sources.py` 的方法表,風險/效益比我判斷不如先保持 patch 小 |
| O2 | **堆疊預算回歸網**(DESIGN §8):POSIX 上以 `RLIMIT_STACK = 3·S − 2 MiB` 啟動 bridge(`S` 取自 `section-profile` 能力 JSON 的 `nativeBytes.world`,`section_profile_bridge.inc:99`,不寫死),`loadfile` #211 的三個場景(`_ax_r13_anchor_follows.scene`、`_ax_r10_hole_follows_piece.scene`、`_ax_r17_wall_column_face.scene`),全部要 `ok:true`。2 份鏈通過、3 份鏈必崩 | 需要在 WSL 實跑確認門檻(`2 MiB` 餘裕是我估的),先量再定 |
| O3 | **`contact_order` 微基準**(DESIGN §9.1):只量 `wood_contact_collect_stops`,P=M ∈ {64,128,256,512},依放置順序與反向各一次;回報對 P 的斜率(2 或 3) | 是量測,不是測試;結果決定 #297 探針能不能照原計畫跑 |
| O4 | 工程還原與組構生成的**產品層** N/N+1:還原 512/513 筆角材的專案(預期 `I10: timber ID exists or capacity exceeded`);509 支 + 一個實例 = 512 接受、510 支 + 實例 → `CAPACITY: …`(`assembly.c:380`) | 需要準備 JSON 專案/規則/綁定夾具;接線已由 T02 釘住 |
| O5 | 512 支**已放置**角材的功能面(`resolve_auto_span`、`reference_check_all`、`reference_snap` 在 512 時的堆疊框) | 就是「放大後重跑 #297 探針」本身 |
| O6 | PF-3 在 512 個 footprint 的耗時與正確性 | 沒有數據;先量 |

## 8. 預期值與執行順序

- 先決:WSL 空閒(無瀏覽器驗收、無其他列車),見 P-176 教訓。
- 順序:`test_geo261_wood_report_policy` → `test_geo261_wood_contact_world` → `test_geo261_timber_capacity` → `c:integrity`(讀 `World=`) → 其餘 W suite → 全量 `run_all`。
- 預期:全部綠;`mutation:check` 紅(待帳本重跑)。
- 新 suite 的耗時我**沒有數據**。組成:一次 `NativeBuild` 建置(每個 suite 行程都要付,和另外 80 個 `test_geo261_*` 一樣)+ 2 個 harness 編譯連結 + 約 6 個 W 突變目的檔 + 5 次宿主 `current_geometry.c` 編譯(最重,每次 400 KB 單一翻譯單元)+ 1 次被改過的 bridge 編譯(同樣含整份宿主);全部約 17 次編譯 + 3 趟 513 行的 bridge 走訪(每行一個完整互動式候選,DESIGN §7.1:約 7~13 ms/行,未量測)。粗估 3~6 分鐘;native job 逾時剛由 15 調到 35 分鐘(`e32994bf`),若吃緊,先把 `HOST_CONTROLS` 砍成 C09/C10/C12 三條。
