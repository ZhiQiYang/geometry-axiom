# Issue #300 設計草稿:角材容量 64 → 512,五個容量常數收斂為單一來源

> **狀態:草稿。** 對 `09ab5f79`(GEO-261 整合分支 head)寫成。沒有建置、沒有跑任何測試、沒有改 repo 任何檔案、沒有建 worktree、沒有用 WSL。
> 產出三份:本檔、`TESTS.md`、`patch.diff`。
> **只驗證了兩件事**:(1) `patch.diff` 對 `09ab5f79` 的樹 `git apply --check` 通過;(2) 套用後 15 個檔案的 blob 與我編輯的檔案逐位元相同。
> 其餘全部是**未編譯、未執行**:C、Python、`sizeof(World)` 的數字(用純文字版結構排版計算器算,見 §6.1)、效能與堆疊的估算,都只是讀碼推出來的。每一個數字我都標了來源:`讀碼`、`計算`、`推論`、`未量測`。

## 0. 一頁結論

| # | 決定 | 理由(細節在後面各節) |
|---|---|---|
| 1 | 單一來源 = **`WOOD_MEMBER_CAPACITY`,放在 W 的 `members.h`**,值 512(巨集,不再是 `document.h` 的 enum 常數) | 儲存陣列需要編譯期大小,且依賴只能「模板 → 核心」:H 讀得到 W,W 讀不到 H,K 不認識角材(§3) |
| 2 | 其餘四個名字(`WORLD_MAX_TIMBERS`、`WOOD_CONTACT_MEMBER_CAPACITY`、`WOOD_CUT_LIST_MEMBER_CAPACITY`、`WOOD_MEMBER_SPAN_MEMBER_CAPACITY`)改成它的**別名**,名字全保留 | 所有使用處、突變錨點、測試引用都不用動;別名鏈無法再分叉(§4) |
| 3 | 編譯期綁定用 repo 慣用的 `typedef char x[cond?1:-1]`,**不是字面的 `_Static_assert`**,共 7 條,放在現有 `app_span_*_check` 旁 | `current_geometry.c:6044-6045` 的註解明說 MSVC 預設 C 模式不收 `_Static_assert`;全 repo 目前 0 處使用(§4.1)。**這與 issue 字面不同,請協調者確認** |
| 4 | `print_cut_list` 的平方陣列根因在 W 的 `WoodCutList`;改成**全部 group 共用一個 `ids[]`**,每 group 存 `first` 偏移 | 512 時 1,069,080 B → 26,648 B;CLI 輸出逐字相同(§5) |
| 5 | `sizeof(World)` **4,759,448 → 5,605,272**(+845,824 B,+17.77%,計算值);靜態 68 份合計 +54.85 MiB | §6 |
| 6 | GEO-261 效能:候選/快照全是整份 POD 複製與比對,**與 S 成正比 → 該部分 +17.77%**(不是 0,也不是被 N 放大) | §7;若仍拿「放大前的 main」當 2× 基準,R 要 ≤ 約 1.7~1.84 才不破線 |
| 7 | 順手加一個守門:`wood_world_validate_members` 在 `member_count > 容量` 時回 `I33 CAPACITY` | 原本 `axes[]` 無界寫入(world_validation.c:72);沒有它,N+1 在 W 層無法測(§4.3) |
| 8 | **新發現(原調查沒有)**:(a) `contact_order` 是線性掃描,放進排序與去重迴圈 → 每次停止面收集 O(P·M),每次重驗至少兩次/每支已放角材 → 每條指令約 O(N³);原報告 22~27 s / 53~70 s 的外推很可能偏低(§9.1)。(b) 3 份 World 在 512 時是 16.04 MiB,**剛好超過 16 MiB 堆疊**;目前靠「同鏈最多 2 份」撐住(§8) | 都不改,但都要在驗收時量 |

## 1. 與 P-175 的對照

| P-175 要求 | 本草稿 |
|---|---|
| 放大到 512 | `members.h`:`#define WOOD_MEMBER_CAPACITY 512` |
| 只在 GEO-261 合入後的 main 做 | patch 基底是整合 head;合入後要重新 apply(§10.5) |
| 五個常數收斂單一來源 + 靜態斷言 | §3、§4 |
| 修 `print_cut_list` 平方陣列 | §5 |
| 補 N / N+1 邊界測試與突變 | `TESTS.md`;patch 內含 12 個新測試、13 個控制組(突變) |
| 放大後重跑探針 | §10.4;注意探針時間(§9.1) |
| 參考線 16、空間 4、載入時間逼近 30 s 另開單 | 不在範圍;§9 只記錄「我讀碼時看到、會影響驗收」的幾點 |
| 公理層 I33 只規定回 CAPACITY,沒有規定數字 | 不碰 `公理層.md`;守門訊息沿用 I33 的 `CAPACITY` 類別 |

## 2. 五個常數現在在哪裡(`09ab5f79`)

先確認:整合 head 上**恰好五處**寫死的 64,互相沒有綁定(`讀碼`,與調查報告 §1.2 一致,行號已更新到這個 head)。

| # | 名稱 | 定義位置 | 它守什麼 / 誰用它 |
|---|---|---|---|
| 1 | `WORLD_MAX_TIMBERS` | `current_geometry.c:2741`(`#define … 64`) | H 的容量參數:`apply_timber_line` 傳給宣告准入(`current_geometry.c:7068`)、`geometry-core/assembly.inc:28`(`c.member_capacity`)、`geometry-core/engineering_commands.inc:31`(`o.member_capacity`)、PF-3 的 footprint 上限與 `malloc`(`geometry-core/panel_fill_support.inc:37,39,61`);還有它推導的陣列:`AppContactFacts.members[]`(`:5768`)、`STOP_FACE_MAX`(`:5817`)、`SPAN_CUT_MAX`(`:6041`)、`obstacles[]`(`:6093`)、`facts[]`(`:6133`)、`REFERENCE_MAX_ISSUES`(`references.inc:8`)、`ReferenceEval.wanted[]`(`references.inc:120`)、`reference_dump` 的 `placed[]`(`:865`)、`SNAP_MAX`(`:921`)、`model_base.c:188` |
| 2 | `WOOD_MEMBER_CAPACITY` | `geometry-templates/woodworking/native/document.h:20`(**enum 常數** `= 64`) | 真正的儲存:`WoodDocument.timbers[]`、`anchors[]`(`document.h:29-30`) |
| 3 | `WOOD_CONTACT_MEMBER_CAPACITY` | `…/contact_world.h:7` | 成員事實陣列 `contact_sources.h:19`;`facts_valid` 的上界 `contact_sources.c:73`;`world_validation.c:72` 的 `axes[]`(**無守門**);面容量 `WOOD_CONTACT_FACE_CAPACITY`(`contact_world.h:8`)= 8×32×9+2×此值,用在 `contact_world.c:120-124`、`world_validation.c:48-49` 的堆疊陣列 |
| 4 | `WOOD_CUT_LIST_MEMBER_CAPACITY` | `…/cut_list.h:6` | `WoodCutList` 的 `groups[]`、每個 group 的 `ids[]`(`cut_list.h:11,14`);`cut_list.c:6` 的入口守門 |
| 5 | `WOOD_MEMBER_SPAN_MEMBER_CAPACITY` | `…/member_reference.h:100` | 跨距解析的暫存:`cuts[]`/`intervals[]`/`touching[]`(經 `WOOD_MEMBER_SPAN_CUT_CAPACITY`,`:101`)、`ca[]`/`cb[]`(2×)、`hit[]`(4×)(`member_reference.c:388-519`) |

現有的唯一綁定:`current_geometry.c:6047` `SPAN_CUT_MAX==WOOD_MEMBER_SPAN_CUT_CAPACITY`。`STOP_FACE_MAX`(`:5817`)與 `WOOD_CONTACT_FACE_CAPACITY` **沒有**對應的檢查。

**後果(讀碼可證)**:只改 #1 → `world->wood.timbers[]` 越界寫入;只改 #2 → #1 的容量參數大於儲存;只改 #3 → `axes[]` 越界;而這些全都照樣編得過。

**刻意不動的第六個 64**:`tests/test_geo261_panel_native.py:82` 內嵌 C stub 的 `#define WORLD_MAX_TIMBERS 64`,和 `tests/geo261_panel_harness.c` 的字面 `64`。前者是「凍結的舊演算法 oracle」自帶的常數、後者是傳給 `wood_panel_support_evaluate` 的顯式上限參數;兩邊在同一個 64 比對等價性,改成 512 沒有任何好處,也不屬於產品常數。`geo261_member_declaration_harness.c` 同理(參數化容量,自備 66 格陣列)。

## 3. 單一來源放哪一層、為什麼

**放 W(模板層)的 `members.h`。**

依賴規則(`tests/ARCHITECTURE-CONTRACT.md` 的層級表):K 只能到 K;W 到 K、W、vendor;H 到 K、W、H、vendor。

- 角材是模板概念。K 完全沒有角材(`product-architecture.json` 的 `forbiddenIdentifiers` 明列了 `WOOD_MEMBER_CAPACITY` 與另外三個 W 容量名,放進 K 會被掃描器擋下;`WORLD_MAX_TIMBERS` 是 H 的名字,不在清單內)。
- 儲存陣列(`WoodDocument.timbers[]`)和暫存陣列(`WoodCutList`、`WoodContactSourceFacts`、span 暫存)都在 W,需要**編譯期**大小。若讓 H 擁有數字,W 的標頭就得 include H(`LAYER_DIRECTION` 違規),或把每個陣列都改成執行期參數——後者正是 P-175 已排除的動態配置。
- `members.h` 是 W 裡最底層的成員儲存標頭,四個消費者已經(間接)include 它:`document.h:9`、`contacts.h:5`(→ `contact_world.h`)、`cut_list.h:5`、`member_reference.h:6`。**零個新 include 邊、零個新檔案**。

被否決的做法:

| 做法 | 否決理由 |
|---|---|
| 新檔 `member_capacity.h` | 必須同步改 `NativeBuild` 的複製檔名清單(`tests/test_geo261_native_kernel.py` 內寫死)、`product-architecture.json` 的 `sources`、收據;零收益 |
| 放 H(`current_geometry.c`) | 見上:W 讀不到 H |
| `#ifndef WOOD_MEMBER_CAPACITY … -D` 可覆寫 | 能讓小容量建置快速測 N/N+1,但結構大小隨巨集變;現有 harness 都是「client 與 W 物件分開編譯再連結」,不同巨集值的目的檔混連會變成 ODR 違規,錯誤會靜默。我選擇用真 512 走(代價:bridge 走 513 行,見 TESTS.md) |
| 保留 enum 常數 | 無法 `#if`;而且其他 W 容量(`WOOD_CONTACT_*`)全是巨集,別名鏈一致比較好 |
| 動態配置 | P-175 排除;`geometry-core/kernel/README.md` 明說 World 內不放淺層指標 |

## 4. 逐常數改法

| # | 名稱 | 改成 | 綁定 |
|---|---|---|---|
| 2 | `WOOD_MEMBER_CAPACITY` | `members.h`:`#define WOOD_MEMBER_CAPACITY 512`;`document.h` 的 enum 刪掉該項,留一行註解指向 `members.h` | 唯一定義 |
| 1 | `WORLD_MAX_TIMBERS` | `current_geometry.c:2741`:`#define WORLD_MAX_TIMBERS     WOOD_MEMBER_CAPACITY`(行內註解) | `app_timber_capacity_world_check`:`==`;`…_timbers_check`/`…_anchors_check`:`sizeof(World.wood.timbers)/sizeof(元素)==WORLD_MAX_TIMBERS`(捕捉「`document.h` 的陣列又被寫回字面」) |
| 3 | `WOOD_CONTACT_MEMBER_CAPACITY` | `contact_world.h:7` 別名 | `app_timber_capacity_contact_check`:`>=WORLD_MAX_TIMBERS` |
| 4 | `WOOD_CUT_LIST_MEMBER_CAPACITY` | `cut_list.h:6` 別名 | `app_timber_capacity_cut_list_check`:`>=` |
| 5 | `WOOD_MEMBER_SPAN_MEMBER_CAPACITY` | `member_reference.h:100` 別名 | `app_timber_capacity_span_check`:`>=` |
| 派生 | `STOP_FACE_MAX` ↔ `WOOD_CONTACT_FACE_CAPACITY` | 不改定義 | 新增 `app_timber_capacity_stop_face_check`:`==`(原本只有 span 那一對) |

**為什麼存取用 `==`,暫存用 `>=`**:儲存與容量參數必須一樣大(小了浪費,大了越界);暫存只要不小於儲存就安全。「有人把別名寫回 `64`」的失敗模式正是「暫存 < 儲存」,`>=` 抓得到。

**這 7 條檢查放在 host 而不是每個 W 標頭裡**:別名是文字替換,在 W 標頭裡檢查會是恆真式;真正有資訊量的比對(`sizeof` 儲存、`World` 型別、跨標頭的面容量)只在 H 看得到全部。W 層的保護由 `TESTS.md` 的純文字測試(整個產品原始碼只准各有一個 `#define`,且值必須是 `WOOD_MEMBER_CAPACITY`)與 C harness 的 `values` 案例負責。

### 4.1 為什麼不是 `_Static_assert`

`current_geometry.c:6044-6045`(原文):「Compile-time checks … written without C11 `_Static_assert`: the Windows MSVC builds compile in its default C mode.」`git grep _Static_assert` 在整個 `09ab5f79` 的 `.c/.h/.inc` 為 0 處;現有兩條檢查都是 `typedef char name[cond?1:-1];`。測試用的 gcc 是 `-std=c11`、cl 是預設模式(`tests/binaries.py:112-115`),所以 `_Static_assert` 在 Windows 這一側會直接編不過。

代價:失敗訊息比較差。gcc 會印出 `size of array 'app_timber_capacity_cut_list_check' is negative`(含名字),MSVC 只有 `C2118: negative subscript` 加行號。測試因此兩種形式都接受(`TESTS.md` §5 的 C09–C13)。名字取得夠描述性,補一點可讀性。

### 4.2 沒有動的地方(但值得知道)

- `ASM_INSTANCE_MAX*3 <= 容量`:`assembly.h:56,72` 的 `owners[48]` 與生成路徑的 `member_count+3>member_capacity`(`assembly.c:380`)。512 遠大於 48,沒有風險;若將來有人要縮到 <48 才需要。沒有加檢查,避免擴大範圍。
- `member_reference.c:519`:`hit_count < CAP*4` 超過就**靜默丟棄**(違反 I33「不截斷」的精神)。既有行為,與本單無關,且 `ca/cb` 的候選數取決於參照命中的面數,不是角材數,實務打不到。不改,只記錄。

### 4.3 順手加的守門

`world_validation.c:72` `WoodMemberAxisFact axes[WOOD_CONTACT_MEMBER_CAPACITY]`,第三個迴圈以 `i<context->member_count` 寫入,沒有上界(調查報告 §1.2 已點出)。目前靠「呼叫端的 member_count 不超過 64」這個隱性約定。收斂成單一來源後約定仍成立,但 W 的定位是「可獨立對 K 公開 API 編譯」,API 不該靠隱性約定。

改法:函式第一行,`member_count > WOOD_CONTACT_MEMBER_CAPACITY` 就用既有的 `validation_refuse` 回 `I33 CAPACITY: member count exceeds the contact capacity`,**在呼叫任何 callback、寫任何東西之前**。產品路徑不可達(同一來源),行為零變化;價值是讓 N+1 可以被測(`TESTS.md` 的 `validation` 案例與 C03/C04)。已核對:`world_validation.c` 現有的測試/突變錨點(`test_geo261_wood_world_validation.py` 的 10 條控制、`mutate.py` 的 M36/M37/M56)沒有一條落在函式開頭,每一條在修改後仍然恰好出現一次。

## 5. `print_cut_list` 的平方陣列

**成因**:不在 `print_cut_list` 本身,而在 W 的 `WoodCutList`(`cut_list.h`):`WoodCutGroup groups[N]`,每個 group 又含 `uint32_t ids[N]`。`print_cut_list` 把整個 `WoodCutList report;` 放在堆疊上(`current_geometry.c:10133`)。

| N | 舊 `sizeof(WoodCutList)` | 新 |
|---|---|---|
| 64 | 18,968 B | 3,352 B |
| 512 | **1,069,080 B**(約 1 MiB) | **26,648 B** |
| 1024 | 4.2 MB | 約 53 KB |

(`計算`:舊 = N×(40+4N)+24;新 = N×48+N×4+24。)

**修法**:改成 CSR 式佈局。

```c
typedef struct { GeoCoord length,size_a,size_b; WoodMemberRole role; size_t count,first; } WoodCutGroup;
typedef struct { WoodCutGroup groups[N]; uint32_t ids[N]; size_t group_count,placed; GeoCoord total_length; } WoodCutList;
/* group g 的 id = ids[groups[g].first .. first+count-1],宣告順序 */
```

`wood_cut_list_collect` 變兩段:第一段與原本一模一樣地找群、數 `count`,同時記下每個成員的「發現序」(暫存陣列 `discovered[]`),並暫時把發現序放在 `first`;排序**原封不動**(同一個交換式);排序後算出每個 group 的新位置(`landed[]`)、配置 `first` 偏移,第二段依成員順序把 id 填進去。

**行為等價的理由**(`讀碼`):
- 群的 key 是 `(length,size_a,size_b,role)` 四欄全比,key 在群之間唯一 → 排序比較器是全序,結果與穩定性無關;`first`/`count` 不參與比較。
- 群內 id 順序 = 成員宣告順序(第二段按 `i` 遞增填入),與舊版 `ids[count++]` 相同。
- 入口守門 `count>CAP` 仍在任何寫入之前,「超量時 `out` 逐位元不變」的原子性保留。
- 兩個暫存陣列各 `N×8 B`(512 時 4 KiB 各),在 `wood_cut_list_collect` 的框架內,不在 `WoodCutList` 裡。

**現有控制組的錨點全部保留且仍唯一**(已逐一計數):`if(!member->placed)continue;`、`&&group->role==member->role`、`right->length>left->length`。第二段刻意寫成 `members[i].placed`(不是 `member->placed`),就是為了不讓第一個錨點變成兩處。

**API 變更**:`WoodCutGroup.ids[]` 消失,改讀 `list.ids[group.first+k]`。全 repo 只有兩個消費者:`current_geometry.c:10152-10153`(已改)和 `tests/geo261_report_policy_harness.c`(已改)。CLI 輸出的位元組不變(`room_a.scene` 預期的 `=== 下料清單 ===` 區塊逐字相同,是 `test_geo261_wood_report_policy.py` 現有的斷言)。

## 6. 記憶體估算

### 6.1 方法與可信度

`sizeof(World)` 沒有原生量測值。我用調查階段留下的純文字結構排版計算器(`clayout.py`,LP64、x86-64 gcc 規則,只解析 typedef/struct/enum/`#define`,不呼叫編譯器)對 `09ab5f79` 的樹算:

- 基線(N=64)= **4,759,448**(調查報告在 `20cafb1f` 算的是 4,759,192;差 256 B,在 `GeoDocument` 裡,與 `20cafb1f..09ab5f79` 之間 K 的變動方向一致,**我沒有逐項追**)。
- 該計算器在兩個舊提交上與實測的 2,904,880 逐位元相同(調查報告 §0),但**在這個 head 沒有對照值**。
- 第一個原生量測點:`tests/test_core_integrity.c:543` 會印 `World=%zu bytes`。實作者跑到 `c:integrity` 時,日誌必須是**改前 `World=4759448`、改後 `World=5605272`**;若不是,以下所有數字都要重算。

### 6.2 單一槽與 World

- 一個角材槽 = `WoodMember` 152 B + `WoodMemberPlacement` 1,736 B = **1,888 B**(計算器輸出;與調查報告手算一致)。其中 1,568 B 是三個 `ref_derived_key`/`between` 文字緩衝,不是角材本身的資料。
- `S(N) = 4,638,616 + 1,888·N`(`計算`)。容量相關部分占 S 的比例:N=64 為 2.54%,**N=512 為 17.24%**。
- 沒有別的陣列隨 `WORLD_MAX_TIMBERS` 長在 `World` 裡:`ΔS` 剛好等於 `448×1,888 = 845,824`,可驗證。

| N | `sizeof(World)` | 較 N=64 | 68 份靜態合計 | Δ(68 份) | 1 個候選堆積(4S) | 同鏈 2 份 | 同鏈 3 份 |
|---|---|---|---|---|---|---|---|
| 64 | 4,759,448(4.539 MiB) | — | 308.6 MiB | — | 18.2 MiB | 9.08 MiB | 13.6 MiB |
| 128 | 4,880,280 | +2.54% | 316.5 | +7.8 | 18.6 | 9.31 | 14.0 |
| 256 | 5,121,944 | +7.62% | 332.2 | +23.5 | 19.5 | 9.77 | 14.7 |
| **512** | **5,605,272(5.346 MiB)** | **+17.77%** | **363.5** | **+54.9** | **21.4** | **10.69** | **16.04(> 16 MiB)** |
| 1024 | 6,571,928 | +38.08% | 426.2 | +117.5 | 25.1 | 12.53 | 18.8 |

### 6.3 World 的份數(`讀碼`,`09ab5f79`)

- 靜態 **68** 份:`g_hist_undo[32]`+`g_hist_redo[32]`+`g_hist_evicted`+`g_hist_group_base`(`current_geometry.c:2953-2955`)= 66;`g_reference_trial`(`references.inc:11`);活的世界 1(bridge `g_world`、CLI `static World world`)。**注意**:調查報告寫的 `g_preview` 內含 `World before, after` 是舊結構;現在 `ReferencePreview` 只持有 `AppWorldCandidate *transaction` 指標(`transactions.inc:8`)。
- 每個候選 = `AppWorldCandidate`(`before`+`after` 兩份,`world_candidate.inc`)+ 候選自己擁有的 `before_bytes`、`after_bytes` 各一份(`app_candidate.c`)= **4 份堆積**。候選池 `APP_WORLD_CANDIDATE_POOL_MAX 4`(只有 model-base 開)最多多留 4 個區塊 = +6.77 MB(約 6.5 MiB)。
- 只在「歷史用到的程度」才常駐:`.bss` 的頁面碰到才算。Windows 以整段未初始化資料計**提交量**(推論),多個測試行程並行時要乘上行程數:每行程 +54.9 MiB。

### 6.4 其他隨 N 成長的東西

| 項目 | N=64 | N=512 | 備註 |
|---|---|---|---|
| `g_reference_issues[]`+`g_preview.issues[]`(`REFERENCE_MAX_ISSUES=8N+24`,每筆 452 B,兩個靜態陣列) | 0.46 MiB | 3.55 MiB(**+3.09 MiB**) | `ReferencePreview` 在 `loadfile`/source-inspector 會整份複製+清零(`web_bridge.c:412-419`、`source-inspector-bridge.inc:208-211`):約 0.26 → 1.88 MB,每次呼叫約 3 次遍歷,量級 1 ms |
| `reference_snap` 的 `candidates[SNAP_MAX][1536]`(`references.inc:921`,**單一堆疊框**) | 2,334,720 B | 3,710,976 B(+1.31 MiB) | 同框還有一份 `World candidate=*w`(S)→ 框架 ≈ 9.3 MiB |
| 停止面陣列 `StopFace faces[STOP_FACE_MAX]`(3 處:`resolve_auto_span`、`world_validation.c:48`、`contact_world.c:120`),每個 | 116,736 B | 159,744 B | 巢狀時 2~3 個同時存活 |
| span 暫存(`wood_member_resolve_span`) | 約 64.5 KB | 約 128 KB | |
| `AppContactFacts`(`world_footprint_collides` 每次呼叫都 `memset`) | 4 KB+ | 32 KB+ | 每次呼叫多 28 KB 清零,量級 1~2 µs |
| `print_cut_list` | 18,968 B | 26,648 B(+8 KiB 暫存) | §5 |

## 7. 對 GEO-261 效能的影響(重點)

### 7.1 為什麼是「S 的線性函數」

候選與歷史機制都以**整個 `sizeof(World)`** 為單位,不管 `timber_count` 是多少:`snapshot_size=sizeof(World)`(`world_candidate.inc:49`、`current_geometry.c:2957`),`memcpy`/`memcmp` 都是整份。所以 N 的放大**即使 0 支角材也要付**。

一次互動式 `line`(bridge 的 `line …`、CLI 視窗)的 S 級操作(`讀碼`:`app_candidate.c`、`transactions.inc:544-640`、`world_candidate.inc`):

| 階段 | 複製(memcpy) | 比對(memcmp) |
|---|---|---|
| `history_record` | 1S | |
| 候選建立 | 3S(`before`、`after`、`before_bytes`)+ `calloc`/`malloc` 首次觸碰頁面約 4S | |
| `g_reference_trial=*candidate`(`transactions.inc:562`) | 1S | |
| evaluate 開頭驗 `before` | | 1S |
| evaluate 成功後存 `after_bytes` | 1S | |
| seal | | 2S |
| publish 的 check(`before`、`after`、`world_definitions_equal`) | | 約 3S |
| publish 寫回 | 1S | |
| **合計** | **約 7S 複製 + 約 4S 頁面首次觸碰** | **約 6~7S 比對** |

- SHA:09ab5f79 已含「延遲 SHA」(`app_candidate.c` 的 `deferred_snapshot_sha`):`memcmp` 相等就不算 SHA。所以 P-177 說的「14 MB SHA」在命中路徑上已經消失;若 `memcmp` 不等才補算。
- 檔案重放(`loadfile`/CLI `--scene`)每行:`memcpy(frame->before,world)` 1S + `g_reference_trial` 1S(失敗時回滾再 1S),加上整個檔案一次外層生命週期(`transactions.inc:675-700`,整檔重放框架另見 `:758-845`);P-177 的 B(外層候選內不逐行建候選)在這個 head 已經是這個形狀。

### 7.2 估算

- **比例**:S 相關部分 ×1.1777。這個數字與 N 無關,只與「容量槽占 S 的比例變多」有關。
- **絕對值**(假設 memcpy 6~10 GB/s、memcmp 8~12 GB/s、首次觸碰頁面 0.25~0.7 µs/頁;**未量測**):互動式 `line` 每條 ≈ 基線 7~13 ms → **多 1.2~2.3 ms**。513 行的 bridge 走訪(TESTS.md 的產品測試)約多 0.6~1.2 s。
- **與 2× 閘門的關係**:設「放大前、GEO-261 修完效能之後」對 main@64 的倍率為 R,S 相關占 GEO-261 牆鐘的比例為 f。放大後(若基準仍是 main@64)倍率 ≈ R·(1+0.1777·f)。

| R \ f | 0.5 | 0.8 | 1.0 |
|---|---|---|---|
| 1.6 | 1.74 | 1.83 | 1.88 |
| 1.8 | 1.96 | 2.06 | 2.12 |
| 2.0 | 2.18 | 2.28 | 2.35 |
| 要守 ≤2.0 所需的最大 R | 1.84 | 1.75 | 1.70 |

`bridge_integrity` 這類短場景幾乎全是候選開銷,**f 很可能在 0.8~1.0**(推論,未量測)。所以:

1. **若 2× 的基準是「放大前的 main」**,GEO-261 修完後 R 必須 ≤ 約 1.7~1.75 才能在加上本單後仍守住。這是我最想請協調者知道的一點。
2. **若基準改成「同一棵樹、同一個 N」**(合入後 main@N 對 main@N,A/B 兩個建置),本單不改變倍率,只讓絕對時間多 17.77%(S 相關部分)。實作者只要在合入後的樹上量一次 N=64(暫時把 `members.h` 改回 64 建一份)與 N=512,就能把這個爭議量化。
3. 任何想「把候選成本降下來」的後續(例如只複製 `timber_count` 以內的前綴)都會因本單而更值得做,但會破壞「POD 整份 memcpy 即快照」的語意,不在這張單。

## 8. 堆疊(16 MiB 合約)

- 16 MiB 是全專案共同假設:`tests/binaries.py:107`(`/STACK:16777216`)、`.github/workflows/integration-tests.yml:30,77`(`ulimit -s 16384`)、`geometry-web/start_local.py:24`(`MIN_STACK`)。
- **已知的最深鏈**:`apply_*_line`(`World backup`,S)→ … → `proj_rebind_aux`(`World source`,S)。`reference_fragment_candidate` 現在是 `malloc`(`subgrid_rebind.inc:8`);**更早的 #211 證據顯示它曾經也是堆疊上的 S,三份 S 共 8.8 MB**(`tests/evidence/211-cloud-bridge-stack-20261013/README.md`,峰值 8,800,640 B / 當時 S=2,904,880 ≈ 3.03S)。
- 我重跑了調查階段的名稱比對呼叫圖(`callgraph.py`,在 `09ab5f79` 上):按值 `World` 的**最長鏈 = 2**(`apply_grid_line`、`apply_applyproj_line`、`apply_placement_line`、`apply_subgrid_line`、`apply_surface_combined_line`)。512 時 2S = 10.69 MiB,加上其餘框架(舊證據約 85 KB;本單讓 `faces[]` 等多約 0.2 MB)≈ 10.9 MiB,距 16 MiB 還有約 5 MiB(32%)。
- **盲點**:呼叫圖只認直接呼叫,指令是用表格和函式指標派發的。**3 份 = 16.04 MiB,比 16 MiB 只多 38,600 B**;只要未來(或我沒追到的)有一條鏈同時存活 3 份就會崩,而且是靜默崩潰(#211 的 8 MiB 對照:`stdout/stderr` 皆空、exit -11)。
- 建議的保險(**不在 patch**,見 TESTS.md §7):把 #211 的三個場景在 `RLIMIT_STACK = 3S − 2 MiB`(512 時約 14.0 MiB)下跑一次。2 份鏈通過、3 份鏈必崩,等於一個便宜的「深度 ≤ 2」回歸網。
- 另一個單框架大戶:`reference_snap`(§6.4)≈ 9.3 MiB;呼叫圖顯示它不在任何按值 `World` 函式之下,餘裕約 6.7 MiB。

## 9. 不在這張單,但驗收時會撞到

### 9.1 `contact_order` 的立方成本(原調查沒有)

`contact_world.c` 的 `contact_order(world,id)` 是對 `member_count` 的線性掃描。`wood_contact_collect_stops` 的「依放置順序插入排序」與「去重」兩段迴圈,**對每個成員側面各呼叫它一到兩次**。每次收集約 `4·P·M + 2·P·M + (2P+144)²` 次基本步驟(排序 + 去重;P=已放置成員數、M=成員總數):

| P=M | 步驟數 | 以 1~2 ns/步 |
|---|---|---|
| 64 | 約 10 萬 | 0.1~0.2 ms |
| 512 | 約 290 萬 | **3~6 ms** |

`world_validation.c:48-49` 對每支已放置角材收集一次(`context->stops`),`end_faces` 又經 `wood_contact_end_faces_with_sources` 再收集一次;`reference_check_all`/`resolve_auto_span` 另有。**每次重驗 ≥ 2·P 次收集 → 每條指令 O(P³)**。

粗估(把「每條指令重驗全部已放置角材、每支 2 次收集」當成立;T₅₁₂ = 上表 512 時每次收集的 3~6 ms):從空 World 一條條放到 n 支的總時間 ≈ 2·Σ k·T₅₁₂·(k/512)² ≈ T₅₁₂·n⁴/(2·512²):n=116 約 1~2 s、**n=310 約 50~110 s、n=512 約 7~13 分鐘**。這比調查報告的外推(22~27 s / 53~70 s)大約 6~12 倍——那個外推是用 n≤64 的二次式擬合;依上面的假設,立方項在 n≤64 時只占總時間約一成,擬合看不到它。

這是**推論**:我只讀了收集函式的複雜度,沒有追每條指令實際觸發幾次重驗、也沒有量任何一個步驟的耗時。**建議在放大後、跑探針之前,先做一次 n=64/128/256 的微基準(只量 `wood_contact_collect_stops`),確認斜率是 2 還是 3。** 若成立,「五房整套一次載入」不是靠改大容量、也不是靠 bridge 逾時調高能解決的,需要把 `contact_order` 改成預先建 `id→order` 表(O(M log M) 或 O(M))——另開單。

### 9.2 其他

- 參考線 16(最差排法剛好用滿)、空間 4、`serve.py` 的 30 s 逾時:P-175 已指示另開單。
- 與 `SP_MEMBER_MAX=128`、`ENG_BINDING_MAX=192`、`ENG_OPERATION_MAX=256` 這類「每個角材一筆」的上限是否會比 512 先撞牆,取決於還沒寫的模板怎麼用,我沒有檢查(`SP_MEMBER_MAX` 是斷面成員,不是角材,看起來無關)。

## 10. 流程成本、同步清單、實作順序

### 10.1 突變帳本全部過期(最大的流程成本)

`tests/mutants_results.json`(約 10.5 萬行)每筆帶 `closure_sha256`(整個 core+bridge 的 include 閉包)。本 patch 動了 `members.h`、`document.h`、`contact_world.h`、`cut_list.*`、`member_reference.h`、`world_validation.c`、`current_geometry.c`,**全部過期**,`mutation:check`(`exit-code-only`)會紅,直到整本重跑。上一次整本重跑是提交 `09ab5f79`(距前一個程式提交 `8394ef60` 約 6 小時,含等待與其他工作,實際機時未知)。這張單合入後必須排一次 WSL 整本重跑,而且不能與瀏覽器驗收並行(P-176 教訓)。

### 10.2 架構收據

`geometry-core/domain-decoupling/product-architecture-receipt.json` 等的 input closure hash 會過期。`py:test_product_architecture`(18 個)掃的是**即時樹**對 `product-architecture.json`,不比對收據,所以不會因此變紅;依 `854660a7` 先例另補一個 audit 提交。**沒有新增產品檔案**(這是把數字放進既有 `members.h` 的另一個好處),`product-architecture.json` 不用改;新增的兩個 `tests/` 檔不在掃描範圍(`sourceFiles` 只含 `tests/__init__.py`、`tests/binaries.py`)。已核對新增程式沒有 `??` 三字元序列(掃描器會拒絕),沒有新增 `#include`。

### 10.3 文件同步

| 檔 | 內容 | 在 patch 內? |
|---|---|---|
| `ARCHITECTURE.md:79` | `64 角材` → `512 角材` | 是 |
| `決策佇列.md:930`、`geometry-core/drafts-topology/decisions-provisional.md:54` | B-15 的「World 角材 64」 | 否(協調者維護的決策文件) |
| `geometry-core/drafts-topology/PROPOSAL.md:292,381-382`、`review.md:92,130` | 歷史提案文字 | 否(歷史文件,建議不追改,在 B-15 加註即可) |
| `BACKLOG.md:441-443` | #300 條目狀態 | 否 |

### 10.4 實作者的建議順序(全在 WSL 空閒時)

1. 把 `patch.diff` apply 到「GEO-261 合入後」的 main:`git apply --3way`;若 context 有位移就重做(§10.5)。
2. 只跑最便宜的三個 suite:`py:test_geo261_wood_report_policy`、`py:test_geo261_wood_contact_world`、`py:test_geo261_timber_capacity`(最後一個約 17 次編譯,其中 6 次是整份宿主 `current_geometry.c`,估 3~6 分鐘,**未量測**)。
3. `c:integrity` 看日誌 `World=5605272`。
4. 其餘 W 相關 suite(`wood_world_validation`、`wood_member_declaration`、`member_reference`、`native_document`、`host_authority`、`panel_native`、`wood_product`)。
5. 全量 `run_all`(`run_all.expected.json` 只多一個 suite,見 TESTS.md §6)。
6. 整本突變帳本重跑(§10.1)、架構收據補提交(§10.2)。
7. 重跑 #297 探針 F1–F5 的 64 個排法,**先做 §9.1 的微基準**;探針會是第一次大量實跑「第 65 支以後」的規則(原報告:已知 14 筆 I19 `V_CUT_PRIORITY` 非容量拒絕,放大後可能浮出更多)。

### 10.5 套用方式與驗證指令

`patch.diff` 是對 **`09ab5f79`** 的 unified diff(git 風格標頭;`current_geometry.c` 的片段保留 CRLF,其餘為 LF,與 blob 一致)。`D:/geometry-axiom` 的工作樹是 main,不是 `09ab5f79`,所以不能直接 `git apply --check`;我用暫存索引對 `09ab5f79` 的樹檢查(不碰工作樹、不建 worktree):

```
set GIT_INDEX_FILE=<任一暫存路徑>\tmp.idx
git -C D:/geometry-axiom read-tree 09ab5f79
git -C D:/geometry-axiom apply --cached --check D:/geometry-axiom-work/drafts/issue300/patch.diff
```

結果 exit 0。再 `git apply --cached` 之後,對 15 個檔案逐一比 `git ls-files -s` 與 `git hash-object --no-filters`,**全部相同**。合入 GEO-261 之後,若整合分支又動過這些檔,改用 `git apply --3way` 並重看 §2 的行號。

檔案清單(15):產品 9(`current_geometry.c`、`members.h`、`document.h`、`contact_world.h`、`cut_list.h`、`cut_list.c`、`member_reference.h`、`world_validation.c`、`ARCHITECTURE.md`)+ 測試 6(`geo261_report_policy_harness.c`、`geo261_contact_world_harness.c`、`run_all.py`、`run_all.expected.json`、新增 `geo261_timber_capacity_harness.c`、新增 `test_geo261_timber_capacity.py`)。

## 11. 風險

| 風險 | 嚴重度 | 說明 |
|---|---|---|
| 草稿 C/Python 沒編譯過 | 中 | 我逐行對過型別與簽名,並確認所有現有錨點仍唯一,但**沒有編譯器驗證**。最可能的錯誤點:`sizeof(((World *)0)->…)` 在 MSVC 的寫法、`WoodWorldValidationContext` 的欄位名、`copy_product_closure` 搭配被改過的標頭 |
| 3 份 `World` 堆疊鏈 | 高但低機率 | §8;靜默崩潰 |
| `contact_order` 立方成本讓 #297 探針與 5 房整套超時 | 高(對後續工作) | §9.1;不影響本單測試(測試只宣告未放置的角材) |
| 新測試套件拖慢 native job | 低~中 | 12 個測試含 6 次整份宿主編譯(5 次靜態綁定控制組 + 1 次接線控制組的 bridge);native job 逾時剛由 15 → 35 分鐘(`e32994bf`);若吃緊,先砍 `HOST_CONTROLS` 到 3 條 |
| 與 issue 字面的差異 | 低 | 沒有用 `_Static_assert`(§4.1);新增了一個 W 守門(§4.3) |

## 12. 我最不確定的三件事

1. **`contact_order` 立方成本的實際大小**(§9.1)。我讀出了複雜度,但每條指令實際重驗幾次、每步幾 ns 都是假設;若錯,可能是「根本不是問題」(實際 f 很小),也可能比我估的更糟。它決定「放大後探針與 5 房載入還能不能做」,而不是這張單能不能合。
2. **`sizeof(World)` 與「S 相關占 GEO-261 牆鐘的比例 f」都沒有量測**(§6.1、§7.2)。計算器在這個 head 沒有對照值;`f` 是從候選機制的程式結構推的。這兩個數字決定 7.2 表格裡的結論:放大後還守不守得住 2×。第一個驗證點是 `c:integrity` 的 `World=` 日誌行。
3. **堆疊鏈深度**(§8)。名稱比對呼叫圖在這個 head 給 2,但漏掉函式指標派發;3 份剛好超過 16 MiB 約 38 KB。我提了便宜的 `RLIMIT_STACK` 回歸網但沒放進 patch。
