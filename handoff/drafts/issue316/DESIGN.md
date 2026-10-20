# #316 設計：死碼 `world_footprint_collides` 與 I11 的另外兩個同承載面過濾

> 草稿，基底 `09ab5f79`（GEO-261 整合分支 head）。**只讀程式、只寫文字檔；沒有建置、沒有跑任何測試。**
> 補丁：`patch.diff`（對 `09ab5f79` 通過 `git apply --check`，驗證方式見 `TESTS.md` §A）。`../combined/patch.diff` 是 #299 + #316 合併版。
> `公理層.md` 不動。引用的條文是 I11（W：「同一承載面上，任兩支已放角材的 footprint 正面積不得相交……明寫與 auto 放置都過這關，world_revalidate 也兩兩重驗」；K：呼叫契約必須明列參與者集合及比較配對）。

## 1. 結論

1. **死碼：推薦方案 (a)（刪除），而且範圍要比 issue 寫的大一點。** 測試 `test_five_real_main_consumers_delegate…` 列的五個「真實呼叫者」裡，**三個**沒有任何呼叫點：`world_footprint_collides`（issue 已指出）、`boundary_edge_interval`、`stop_in_owner_extension`。只刪第一個，這個測試仍在替另外兩個作偽證。補丁三個一起刪，並把測試改成「宣稱的宿主必須真的有呼叫者」。W API 只有 `wood_contact_footprint_collides` 一起刪（它唯一的產品呼叫者就是那個死函式）。
2. **I11 另外兩個過濾目前沒有任何突變覆蓋**（`mutate.py` 的條目逐一對過，見 §4.1），而且**單一承載面的場景原理上殺不了它們**——現有 171 個根目錄場景沒有任何一個讓兩支角材分屬不同承載面。補丁新增一個兩片承載面各一支 boundary 的接受場景 `_i11_two_surfaces_same_uv_accept.scene`，加兩個突變 M97（`references.inc`）、M98（`world_validation.c`），並在 W 單元層補兩個控制項。

## 2. 死碼

### 2.1 事實（逐一 `git grep -w`，排除 evidence／release-evidence）

| 函式 | 位置 | 呼叫點 |
|---|---|---|
| `world_footprint_collides`（H） | `current_geometry.c:5794–5800` | 0（issue 已知） |
| `boundary_edge_interval`（H） | `current_geometry.c:5950–5952` | **0**（自己轉呼叫 W `wood_contact_boundary_interval`；產品裡直接呼叫 W 的是 `contact_world.c` 內部） |
| `stop_in_owner_extension`（H） | `current_geometry.c:5992–5994` | **0**（W 內部 `wood_contact_end_faces_with_sources` 自己呼叫 `wood_contact_owner_extension`） |
| W `wood_contact_footprint_collides` | `contact_world.c:15–24`、`contact_world.h:26` | 只有上面那個死函式、`tests/geo261_contact_world_harness.c` 的 `collisions` 案、`test_geo261_wood_contact_world.py` 的 3 個控制項 |
| `collect_stop_faces`（H） | `current_geometry.c:5857` | 4（`resolve_auto_span`、`references.inc:639`、`world_validation.inc:56`、`timber_support_projection.inc:151`） |
| `timber_end_face_check`（H） | `current_geometry.c:6011` | 1（`reference_sources.inc:668`，「沒有 ctx／用目前值」分支）——真實但很窄 |

我另外寫了一段純文字的可達性檢查（和補丁裡新測試用的是同一組函式：去掉註解與字串後，數不是定義／宣告的 `name(`），對基底 `09ab5f79` 的 include 閉包（184 個檔）跑過：三個死宿主 calls=0，`collect_stop_faces` calls=4、`timber_end_face_check` calls=1；補丁後三個死宿主連提及都是 0。也就是說**新測試放到基底上會對舊的五個配對紅**，不是只在補丁後才綠。

M13 的歷史也印證了這件事：突變原本打在 `world_footprint_collides`，GEO-261 `51e9045b` 之後那行不再被執行，M13 在帳本重產時存活（`9c467933` 已把它移到 `resolve_auto_span` 的實際過濾行）。對死碼的突變保證存活，等於白跑一次約兩小時的帳本。

### 2.2 方案比較

| | (a) 刪除並改測試 | (b) 保留、只改正測試宣稱 |
|---|---|---|
| 程式風險 | 刪的是無呼叫點的 `static`／無產品呼叫者的 W 函式；MSVC 與 GCC 都不需要它 | 無 |
| 測試 | 刪 1 個 harness 案 + 1 個測試方法 + 3 個控制項；新增「宿主必須有呼叫者」斷言 | 要加「已知死碼」例外名單，測試變成在文件化一個不該存在的東西 |
| 假保證 | 消除。W 單元層不再有一組「保證 I11 同面碰撞」但產品不走的斷言 | 保留。harness 的 `collision-*` 九個斷言會繼續全綠，讀的人以為 I11 的參與者過濾被守住了，其實守的是死函式 |
| 重複的政策 | 同承載面過濾只剩三個活的檢查點（§3），都有突變 | 第四份副本（W 的）會慢慢和三個活的脫節 |
| 代價 | 讀者追溯燈號不變，但「原始碼」連結清單變動（§2.4）；帳本本來就要重產 | 無 |
| 退路 | 補丁的刪除各自獨立成 hunk，可只留 `world_footprint_collides` | — |

**推薦 (a)。** 還有一條 (c)：讓 `resolve_auto_span` 向 W 要「同承載面障礙物」清單，把 W 的參與者過濾救活，同時把三份同承載面過濾收斂成一份。這符合 K 契約「呼叫契約必須明列參與者集合」，但它是行為保持的重構，不是修死碼，我建議另開單，不放進這個補丁。

### 2.3 補丁怎麼處理

- `current_geometry.c`（CRLF，補丁保留 CRLF）：刪三個函式與它們的說明註解；刪 5758–5760 那三行已經沒有函式可說明的 I11 孤兒註解；在 `resolve_auto_span` 收障礙物之前加一段註解，指出 I11 的三個活檢查點與對應突變（M13／M97／M98，K 判式 M12）。
- 被刪的 D16／R18「純幾何、不看宣告與錨法」與 I22「延伸段側面以優先級 2 計」兩段說明沒有丟：搬到 `contact_world.h` 對應宣告上方（英文改寫，實質相同）。
- W：刪 `wood_contact_footprint_collides`（`contact_world.c`／`.h`）。保留 `wood_contact_boundary_interval`、`wood_contact_owner_extension`——它們在 W 內部仍有呼叫者。
- 測試：
  - `tests/geo261_contact_world_harness.c`：刪 `collisions()` 與分派。
  - `tests/test_geo261_wood_contact_world.py`：刪 `test_collision_…` 方法、`COLLISION_FILTER`、3 個控制項；`test_five_real_main_consumers_…` 改名 `test_main_consumers_have_callers_delegate_…`，只留兩個真宿主（`collect_stop_faces`、`timber_end_face_check`），對每個多斷言「`call_sites >= 1`」（新增 `product_sources()`／`call_sites()`／`mentions()` 三個輔助函式：從 `current_geometry.c` 與 `geometry-web/web_bridge.c` 沿引號 include 走完閉包），並對 `RETIRED_DEAD_HOSTS` 三個名字斷言「完全不再出現」，避免有人無聲復活。控制項測試方法名去掉已不實的 `twenty`。
  - `tests/run_all.expected.json`：`py:test_geo261_wood_contact_world` 10→9（刪一個方法）。
- `product-architecture.json`：`policy.forbiddenIdentifiers` 拿掉 `wood_contact_footprint_collides`。這份清單是「K 檔案禁止出現的 W 識別字」（`architecture_contract.py:933`），沒有任何檢查要求條目必須仍存在，所以不拿掉也不會壞；拿掉是為了讓 W 公開面的清單維持真實（目前它對 W 標頭宣告的 324 個 `wood_*` 函式是完整的）。另兩個被刪的是 H 的 `static`，本來就不在清單裡。

### 2.4 讀者追溯連鎖

用 `axiom_matrix` 對補丁後檔案重算：**沒有任何條文的燈號改變**（`test_axiom_reader.py` 比的是燈號），但清單內容變：

| 條文 | 變化 |
|---|---|
| I11 | 原始碼：`app_contact_facts`→`resolve_auto_span`（原本孤兒註解掛到下一個函式上，是誤歸屬）；夾具 +新場景；變異 +M97、M98 |
| D2 | 夾具 +新場景（場景註解提到 D2） |
| D16、I20、I21、R4、R18 | 原始碼少 `boundary_edge_interval` |
| I22 | 原始碼少 `stop_in_owner_extension` |

這些條文原本指向死函式，現在少一個指向；依 `AGENTS.md` 仍須重跑 `sync_axiom_reader.py`、`--check`、`tests/test_axiom_reader.py`。若不想動 D16／I20／I21／R4／R18／I22 的清單，就改用退路（只刪 `world_footprint_collides`）。

### 2.5 縮小到只刪 `world_footprint_collides` 的做法

從 `current_geometry.c` 的補丁段落去掉第 3、4 個刪除 hunk；`contact_world.h` 不加兩段說明；`RETIRED_DEAD_HOSTS` 只留第一個名字；§2.4 只剩 I11 一列。測試仍可保留「宿主必須有呼叫者」，只是剩下的兩個死宿主不在清單裡。

## 3. I11 的四個檢查點與突變覆蓋

I11 在基底裡實際有三個「執行中的」兩兩比較，各有自己的同承載面過濾（第四個是上一節的死碼）：

| # | 位置（09ab5f79） | 過濾 | 比較判式 | 現有突變 |
|---|---|---|---|---|
| 1 | H `current_geometry.c:6093–6097` `resolve_auto_span` 收障礙物 → K `geometry-core/kernel/geometry.c:666` | `:6096` `a->placement_id!=placement->id` | K `geo_rect_overlap_positive`（`geometry.c:604`） | M13（過濾）、M12（判式，共用） |
| 2 | H `geometry-core/references.inc:650–660` `reference_check_all`（I8a 全量重驗） | `:654` `other_anchor.placement_id!=a->placement_id` | `:656` `uv_rects_overlap`（`current_geometry.c:5749`→K） | **無** |
| 3 | W `world_validation.c:61–71`（最終世界重驗） | `:65` `!b.member->placed\|\|a.placement_id!=b.placement_id` | `:69` `geo_rect_overlap_positive` | M37（`:63` 迴圈 `j=i+1`→`j=i`，只改迴圈起點） |

issue 寫的 `references.inc:656`、`world_validation.c:66` 是比較判式那一帶；過濾本身分別在 `:654`、`:65`。

重驗的順序（`current_geometry.c`）：`reference_rebuild`（6288，逐支重新放置、障礙物含已放者）→ `reference_check_all`（6290，檢查點 2）→ `world_validate_derived`（6307 → `wood_world_validate_members`，6223，檢查點 3）。

### 3.1 逐一確認：沒有突變打得到這兩個過濾

- `tests/mutate.py` 裡 `geometry-core/references.inc` 這個字串只出現在 M36 的說明文字，**沒有任何突變以它為目標檔**。
- 以 `world_validation.c` 為目標的只有 M36（等價）、M37（`j=i+1`）、M56（等價）；沒有一個動到 `:62` 的 `placed` 或 `:65` 的過濾。
- 帳本（`tests/mutants_results.json`）佐證：M37 的殺手是 `subgrid-local.scene` 等，原因是「自己和自己比」讓每個有角材的場景都被拒，和同承載面過濾無關。

### 3.2 為什麼單一承載面的場景殺不了

只有一個承載面時，每一對角材都通過過濾，拿掉過濾 = 沒有任何行為差異。我掃了根目錄 171 個 `.scene`：104 個有 `place` 行、30 個宣告 ≥2 個承載面，但**沒有任何一個的角材分屬 ≥2 個承載面**（每個場景最多 1 個承載面帶角材）。所以現有 TESTS 的 165 個場景不可能殺它們。bridge 類測試裡有多面案例（如 `test_datum_contract.py`、`test_section_profile_native.py`），但那些不是核心帳本的裁判。

### 3.3 殺手場景 `_i11_two_surfaces_same_uv_accept.scene`

```
surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000     # 天花板
surface 3 origin 0 0 0 u +x v +z outline 0,0 3000,0 3000,2500 0,2500        # 牆（y=0）
timber 1 20 20 role boundary        timber 2 20 20 role boundary
place 1 on 1 at-face e0 +u +n       place 2 on 3 at-face e0 +u +n
```

- 預期接受，`lengths: [4000, 3000]`。兩個承載面的框架（`origin`/`u`/`v`）都是現有場景用過的（`_test_fixed.scene`、`_wit_d2_wall_frame.scene`）；兩支都貼各自的 e0，和 `_test_fixed.scene` 同型。
- 局部座標下兩支的足跡正面積重疊（u∈[0,3000]、v∈[0,20]），房間座標下一個在 z=2500、一個在 y=0 不相碰。I11 說同承載面才比，所以接受。
- 拿掉過濾為什麼轉紅，有**兩條獨立機制**：
  1. 有候選／ctx 時（`reference_check_all`、最終重驗都在這條）：`reference_member_footprint`（`reference_sources.inc:489–505`）在 `anchor.placement_id != placement_id` 時直接回 false；`references.inc:655` 於是 `ok=false`，`world_validation.c:68` 於是 `return false`，整個世界被拒。
  2. 沒有 ctx 時：`timber_a0_footprint_uv` 會用另一個承載面的框架硬算出足跡，因為我讓局部足跡重疊，所以會得到假碰撞而被拒。
  第 2 條是保險：如果日後有人把第 1 條的行為改掉，這個場景仍然殺得到。
- 場景是 `accept`，所以 `tests/test_bridge_integrity.py::test_all_accepted_scenes_keep_geometry_and_canonical_dump` 會順便把它跑一遍 dump／重載往返。

### 3.4 突變

| 編號 | 檔案 | 替換 | 預期殺手 |
|---|---|---|---|
| M97 | `geometry-core/references.inc` | `if(other_anchor.placement_id!=a->placement_id)continue;`→`if(0&&…)continue;` | 新場景（場景被拒：`reference_check_all` 回 false） |
| M98 | `geometry-templates/woodworking/native/world_validation.c` | `if(!b.member->placed\|\|a.placement_id!=b.placement_id)continue;`→`if(!b.member->placed)continue;` | 新場景（最終重驗 `return false`） |

新場景放在 `TESTS` 最後（理由同 #295 的註解：`killed_by` 只存前 5 個失敗夾具，放前面會擠掉舊突變的殺手），所以 M97／M98 的 `killed_by` 就只有它。`mutate.py` 的目標檔機制接受 `.inc`（現有 bridge 突變已用）；`references.inc` 在閉包裡只被 `current_geometry.c:7521` 引用一次，展開鏈唯一。

### 3.5 W 單元層（不用等帳本）

`geo261_world_validation_harness.c` 的 `collision` 案早就有 `validation-separate-hosts`（placement 11 vs 10 → 接受）與 `validation-unplaced-no-collision`，但 `test_removed_rules_fail_exact_named_assertions` 的控制項**沒有任何一個**把產品原始碼綁到這兩個斷言。補丁加兩個控制項：

| 控制項 | 替換 | 應轉紅的斷言 |
|---|---|---|
| validation-same-host | 拿掉 `\|\|a.placement_id!=b.placement_id` | `validation-separate-hosts` |
| validation-pair-placed | `if(!b.member->placed\|\|`→`if(` | `validation-unplaced-no-collision` |

（harness 的 `footprint` 回呼忽略 placement 參數，所以過濾一拿掉，重疊的矩形就被當成碰撞——這點是我讀 `geo261_world_validation_harness.c:26–27` 確認的。）檢查點 2 在 H，沒有現成的單元 harness 能放兩個承載面，所以它只靠新場景。

### 3.6 沒有補的突變，以及原因

- **兩兩比較判式本身**（`references.inc:656` 的 `uv_rects_overlap`、`world_validation.c:69`）：我判斷它們是冗餘防線——放置時 `resolve_auto_span` 已排除與已放者重疊（檢查點 1），`reference_rebuild` 對所有角材按順序重放，所以走到檢查點 2、3 時不會再有重疊。這和 M36（已標等價）同型。但這個結論只來自讀程式，沒有差分測試佐證，我不敢在 `mutate.py` 寫 `equivalent=` 的證詞。建議帳本重產時加 `M99/M100` 之類的探針，若存活再仿 M36 做差分實證；若有場景殺得到，那個場景才是真牙齒。
- **反向過濾**（`!=`→`==`）：也會被新場景殺（跨面配對被拿去比），不另立。

## 4. 帳本／讀者連鎖與合併建議

- `closure_sha256` 是 `current_geometry.c`（加 `web_bridge.c`）整個 include 閉包的雜湊（`mutate.py:638–670`），所有紀錄共用。本補丁動了 `current_geometry.c`、`contact_world.c/.h`；#299 動 `contacts.c/.h`、`contact_world.c/.h`。**任何一個都讓整份帳本過期**，不只是 `current_geometry.c` 與 `mutate.py`。
- `oracle_sha256` = `run_tests.py` + 被引用的所有 `.scene`（`mutate.py:675–690`）：新場景與 `run_tests.py` 都動了；bridge 類突變的裁判另含 `tests/*.py` 與根目錄場景。
- 兩個補丁都要重產帳本（約 2 小時）與重跑讀者同步，**請合成一次**。`../combined/patch.diff` 就是兩者合併、已驗過 `git apply --check`。
- 兩個單獨補丁**不能先後套用**：在 `contact_world.h`、`run_tests.py`、`test_geo261_mutation_migration.py`、`test_geo261_wood_contact_world.py` 四個檔案會互相擋（暫時索引實測 4 個檔案 `does not apply`）。單獨套任一個都可以；要兩個都要就套 combined。
- 其他草稿（#300、#314）和本補丁熱點檔重疊；用暫時索引試過它們先套再套本補丁都能 `--check` 通過，語意衝突沒看。
- 編號 M97、M98 暫定（#299 用 M89–M96）。

## 5. 我最不確定的三件事

1. **新場景在基底上是不是真的被接受，以及它是不是真的殺得到 M97／M98。** 全靠讀程式推導：多承載面、每面一支 boundary、沒有 `space`、`lengths [4000,3000]` 的順序與格式。前一個失敗模式是「基底就拒絕」（那 M97／M98 會被誤判成 survived 或 killed 於錯誤原因）；後一個是我對 `reference_member_footprint` 回 false 的讀法錯了，那就只剩第 2 條（局部足跡重疊）機制。第一步請先在基底（未套補丁）手跑這個場景，`exit 0` 且尺寸為 4000、3000，才繼續。
2. **刪除範圍比 issue 大。** issue 只提 `world_footprint_collides`；我連 `boundary_edge_interval`、`stop_in_owner_extension` 一起刪、還搬了兩段說明，連帶讀者追溯清單（D16／I20／I21／R4／R18／I22）少一個指向。理由是不這樣測試就仍在宣稱死碼是真實呼叫者；退路在 §2.5。你可能比我更清楚這兩個函式是否為日後保留的接點。
3. **兩兩判式（`references.inc:656`、`world_validation.c:69`）是冗餘防線的說法。** 我沒設計殺手也沒標等價，因為這個結論只是靜態推論。若帳本重產時它們存活，這代表 I11 的全量重驗其實從未被任何場景獨立證明；若被殺，代表有我沒想到的路徑。兩種結果都值得知道，所以建議補探針突變而不是現在就下結論。
