# #299＋#316 固定 F2 的純文字 closure 覆核

唯一基準為 Git 可解析的 `4b665fae21ab63aaffb7d84f6a32d5a469ba1675`。本檔只記固定 Git blob 的讀取／詞法盤點；**沒有編譯、測試、產品執行、架構掃描、效能量測、Git 寫入或動態綠燈**。目前 working tree 不作基準。

權威語意仍是該 SHA 的 `公理層.md:1253`：I11 只比較同承載面已放角材，正面積交集才拒絕，邊／端點接觸合法，正式建立、重宣告與全量重驗須一致。沒有修改條文或另定門檻。

## 真 caller 與退役範圍

從 `current_geometry.c` 與 `geometry-web/web_bridge.c` 沿 quoted includes 保守讀取，分別得到 168／184 檔，union 184 檔；每個原 blob、raw SHA256、include edge 及每個 occurrence 的原行，均在 `closure-review.json`。註解／字串／字元常值遮罩後，函式定義、宣告、call 與非 call reference 分列；這是文字證據，不假裝是 C preprocess 或 link-time reachability proof。

| 符號 | 原定義／宣告 | 原真 calls | 結論 |
|---|---:|---:|---|
| H `world_footprint_collides` | 1／0 | 0 | `current_geometry.c:5825`，無 address／非call reference |
| H `boundary_edge_interval` | 1／0 | 0 | `current_geometry.c:5981`，無 address／非call reference |
| H `stop_in_owner_extension` | 1／0 | 0 | `current_geometry.c:6023`，無 address／非call reference |
| W `wood_contact_footprint_collides` | 1／1 | 1 | 唯一產品 call 是上述死 H wrapper 的 `current_geometry.c:5830`；W 定義 `contact_world.c:15`、宣告 `.h:26` |
| H `collect_stop_faces` | 1／0 | 4 | `current_geometry.c:6130`、`references.inc:639`、`geometry-app/native/world_validation.inc:56`、`timber_support_projection.inc:151`，必須保留 |
| H `timber_end_face_check` | 1／0 | 1 | `reference_sources.inc:678` 的無 ctx／current-values 路徑，窄但是真 caller |

另外從同一 F2 manifest 的 190 個 C sources 補讀兩入口 union 外的六檔：`geometry-app/native/kernel_storage.h`、`geometry-app/native/model_sources.inc`、`geometry-core/engineering_json.inc`、`geometry-core/model_base.c`、`geometry-templates/rectangular-grid/rectangular_grid.c`／`.h`。六檔對上述六名及下面兩個活 W API 全部零 identifier mentions，原 bytes hash 亦在 JSON。故現在沒有被兩入口閉包漏掉的真 caller。

**不能連帶退役其他 W API。** `wood_contact_boundary_interval` 原有三 calls；刪死 H wrapper 後，`contact_world.c:137`／`:150` 仍用於 owner extension／end faces。`wood_contact_owner_extension` 原有兩 calls；刪死 H wrapper 後，`contact_world.c:164` 的真 end-face evaluator 仍用它。

## 刪掉的測試只守退役 API

原 `tests/geo261_contact_world_harness.c:20` 的 `collisions()` 全部九個 `collision-*` CHECK 都直接呼叫唯一被退役的 `wood_contact_footprint_collides`，不經任一活 I11 產品檢查點。對應原 Python `test_collision_positive_area_pointer_identity_candidate_placement_and_eligibility`（`:118`）與三 controls：`positive-area`／`collision-identity`／`collision-placement`，也只連結這個 API。因此 combined 移除該 method 與這三 controls，是 API 退役範圍；不是降低活 I11 的斷言或為紅燈減 expected。

原方法數 10→9 可由「刪一個方法，其餘方法保留」說明，但最後仍須 AST census 與原 strict 執行實證。原20 controls 去三加 #299 的 `edge-index-output`，combined 為18；不要沿 individual #316 的17或舊整表88數字作全案宣稱。

## 仍活的 I11／identity／接觸保護

| 產品路徑／性質 | F2 原來源 | 保留或新增的原 oracle |
|---|---|---|
| 放置時只收同面已放者為障礙物 | `current_geometry.c:6124`–`:6128` → K `geometry.c:666` | 原 M13 錨點不改；保留原核心 `_test_collide.scene` 與其他全部165場景 |
| K 正面積判式，邊接觸合法 | `geometry-core/kernel/geometry.c:604` | 原 M12；`geo261_geometry_harness.c:93`–`:94` 的 touching／overlap；`test_geo261_native_geometry.py` 原 `boxes` case |
| H 全量重驗的同面配對 | `geometry-core/references.inc:650`–`:659` | 新兩面同UV接受場景；M97 單獨移除 `other_anchor.placement_id!=a->placement_id` |
| W 最終重驗的同面／placed配對 | `world_validation.c:61`–`:69` | 原 `geo261_world_validation_harness.c:78`–`:81` 保留 `validation-touch-is-legal`、`validation-positive-collision`、`validation-separate-hosts`、`validation-unplaced-no-collision`；原 Python collision method與原正面積 control保留，新增同面／placed兩control |
| 真 contact-stop candidate pointer identity | `contact_world.c` 的 `member==exclude`、`fact->member!=owner` | 原 `geo261_contact_world_harness.c:53` 的 same-id copy vs exact pointer；原 `stop-identity` → `ASSERT:stop-exclusion-keeps-candidate-identity`、`owner-identity` → `ASSERT:owner-pointer-not-id` 均保留 |

最後一列是**活 contact-stop／owner identity**，不是把退役 collision API 的 identity 測試改稱仍在守 I11。三個活 I11 check points 也不受刪除死 API 影響。H `world_revalidate_candidate` 原先在 `current_geometry.c:6321` 做 `reference_check_all`，再於`:6338` 做 `world_validate_derived`；沒有改守門流量的必要。

新 `_i11_two_surfaces_same_uv_accept.scene` 仍只是待動態驗證的正例：兩承載面局部足跡重疊而實體 frame 不同，預期長度4000／3000。不能因草稿寫「必紅」就預填 M97／M98 killed；先在未改產品 F2 接受，再分別驗兩個單fault、再恢復。若某個被前關遮蔽而 equivalent，必須保留真輸出並分類，不能算 kill。

## 新 helper 的完整性邊界與最小強化建議

已純文字讀取 `/tmp/g261-next299316/tests/test_geo261_wood_contact_world.py` 的 `product_sources`／`call_sites`。原 combined helper 只從兩入口相對路徑走 include，會漏前述六個 manifest C source；缺檔 `continue` 也不是 fail-closed。建議保留兩入口，再以實際 manifest `sources` 中 `language == "c"` 全部路徑加 seed，源檔缺失須失敗；這不增加測試方法、不變更數值判準。

原 relative／ROOT-only 盤點有30個 unique kernel quoted includes（兩 root 重複後60紀錄）無 local target；例如 `members.h:7`→`geometry.h`、`derived_placement.h:7`→`placements.h`、`engineering.h:6/9/12/15/18`。**全部**可映射既有公開 `geometry-core/kernel/<name>`，而且全部已經在184檔 union，沒有新增／漏掉今日 source。JSON `public_kernel_fallbacks` 有完整30條來源／行號／name／target。relative→ROOT→public K fallback可以全解，不應用任意 basename 搜尋誤選 `internal/` 同名標頭。

抓 include 前應只遮 comments，保留真 string／char literal 和換行；不能套 `without_comments_and_strings`，它會把 `#include "name"` 的 name 抹掉。可用 comment|string|char lexer alternation，callback 將 comments換成等長空白（保留newlines）、字串／字元維持原文，再取行首 include。保留 ifdef 全部分支作保守閉包即可；不宣稱做 C preprocess。

## 解鎖重型執行後的真命令與0／1／0

下列是後續計畫，**本次未執行**；應由 parent 的原環境／SHA／streams recorder 及 heavy lock 執行，獨立 TMPDIR、MUTATE_RESULTS。

1. 在固定 F2 的原 core 先只加入新場景，執行 `<F2-core> --scene <new-scene> --no-window`，真0、長度4000／3000；不接受就先查fixture，不改產品放行。
2. 新產品 P 跑 `python3 tests/test_geo261_wood_contact_world.py`、`python3 tests/test_geo261_wood_world_validation.py`、`python3 tests/test_geo261_native_geometry.py`。原 controls 已按 baseline→mutant→baseline 執行，須保存 named ASSERT、正常1及恢復0，編譯失敗／crash不算 kill。
3. 純Python caller／退役名稱控制：`python3 -m unittest tests.test_geo261_wood_contact_world.ContactWorldBoundary`；基準0，隔離重加死 definition／只恢復舊五pairs的負例須在 call_sites／mentions 具名紅，恢復0。不要以編譯錯誤代替。
4. `MUTATE_RESULTS=<private>/ledger.json python3 tests/mutate.py M12 M13 M37 M97 M98`，不覆正式帳本。M97／M98 各自獨立；在前後都用未突變 core 真跑新場景0，保存 mutant 原 `FAIL 應接受但拒絕`／killed_by，確保沒有拿上一個突變的紅當下一個。
5. 原 `python3 tests/run_tests.py <P-core>`、`GEOMETRY_TEST_BRIDGE=<P-bridge> python3 tests/test_bridge_integrity.py`，保留原全部場景與新場景 dump／重載獨立 oracle，再由 final SHA 的整份帳本／架構／完整native／browser收尾。

最大的未確定點是新兩面場景對M97／M98的實際0／1／0；本次文字證據沒有把推論寫成結果。
