# O467 / O1 v3：原生突變盤點

基底 `48d5f3887e8cb8d222307db62dbdea287fda8442`。本文件是來源盤點，不是正式執行收據。
`MUTANTS` 原表 152 筆（core 74、bridge 78）原內容與順序保持，追加16片後168筆。
原 bridge `RESTORED` 67方法保持，片段的具名方法去重追加；檔案、計數及pin由測試驗證。

| 功能 | main 實際狀況 | 本片與仍未覆蓋的邊界 |
|---|---|---|
| #438 / flat-ceiling/1 | `framing_template_mutation_check.py:56`起5個native專用撤回；host另2個；沒有直接R03正式ID | 5個來源錨點原樣登錄；MAIN改用有正確主支拒絕marker的新8組裁判。原生輸入拒絕、owner、防重入等普通測試不等於逐條突變覆蓋。 |
| #445 / flat-ceiling/2 | `framing_template_policy_a_mutation_check.py:28`起4個專用撤回；host另1個 | 原4錨點與判準，外加兩版本共用的活guide來源突變。尚不代表凹室、孔柱樑或退縫片已實作。 |
| #447 / PF-6 | 下表10個ID已有正式ref與原record，不能說未登錄 | 追加6個不同退化；原10個不重編號、不重複登錄、不新增equivalent。任意外層operation組合與每種輸入拒絕仍非全覆蓋。 |
| R03 grid mark 活來源 | `geometry-web/framing_template_bridge.inc:203`識別grid anchor並以D6a式保存；原N14只看main且gap 2→3 | 新裁判按D6/D6a、I8/I8a、R2檢查gap 2→4時guide與secondary ±1mm、ID、Undo/Redo、冷開；預期由輸入差值獨立計算，不調產品generator。 |

## 已存在的正式 PF-6 原件

以下只證明基底ref指向的原record為killed並有該execution head；不冒稱本輪重跑或對O1工具／裁判仍fresh。

| ID | 原 verdict | 原 execution head | repo ref |
|---|---|---|---|
| PF6_OMIT_DEPENDENT_REVALIDATION | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OMIT_DEPENDENT_REVALIDATION.json` |
| PF6_OWNER_FRAMING_TEMPLATE_REJECTS_ENGINEERING_CONFIRM | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_FRAMING_TEMPLATE_REJECTS_ENGINEERING_CONFIRM.json` |
| PF6_OWNER_FRAMING_TEMPLATE_REJECTS_LINE_CANCEL | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_FRAMING_TEMPLATE_REJECTS_LINE_CANCEL.json` |
| PF6_OWNER_LOAD_CAPACITY_RETAINS_CANDIDATE | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_LOAD_CAPACITY_RETAINS_CANDIDATE.json` |
| PF6_OWNER_LOAD_COUNTER_CAPACITY | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_LOAD_COUNTER_CAPACITY.json` |
| PF6_OWNER_PF6_REJECTS_ENGINEERING_CONFIRM | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_PF6_REJECTS_ENGINEERING_CONFIRM.json` |
| PF6_OWNER_PREVIEW_COUNTER_CAPACITY | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_PREVIEW_COUNTER_CAPACITY.json` |
| PF6_OWNER_SHARED_LOAD_TOKEN | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_OWNER_SHARED_LOAD_TOKEN.json` |
| PF6_PARTIAL_SUCCESS_WRITES | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_PARTIAL_SUCCESS_WRITES.json` |
| PF6_UNSELECTED_CREATES | killed | `5853d7d4579cfff5e4e50a029d1f8c5fea32ddc4` | `.github/evidence/mutations/refs/PF6_UNSELECTED_CREATES.json` |

## 追加原生定義（每個皆執行真 bridge）

| ID | 基底目標行 | 預期具名斷言 | 為何是實際退化 |
|---|---|---|---|
| PF6_O_FINAL_POST_GEOMETRY | `geometry-web/panel_fill_builder_bridge.inc:245` | `PF6_PLAN_MUST_SHOW_FINAL_POST_GEOMETRY` | 確認前須揭露 outer post 已作用後的每支最終幾何；撤回最後 footprint 重算必須被具名裁判拒絕。 |
| PF6_O_LIVE_DIMENSION_BINDING | `geometry-app/native/panel_fill_builder.inc:166` | `PF6_SAVE_LIVE_A_SOURCE` | A 活來源須保留為 definition source，不得凍結為數值；形狀先驗證避免 TypeError 被誤當 assertion kill。 |
| PF6_O_NUMERIC_EDGE_ORDER | `geometry-templates/woodworking/native/r45_builder.h:115` | `PF6_R41_SOURCE_KEY_NUMERIC_ORDER` | 邊來源數字鍵排序跨過 9 後仍須按數值；字典序不可變更候選的確定性次序。 |
| PF6_O_RECEIPT_FINAL_HASH | `geometry-web/panel_fill_builder_bridge.inc:467` | `PF6_O_RECEIPT_FINAL_HASH` | 確認回執的 definition_sha256 必須等於實際提交後 canonical dump 的獨立 SHA-256，不能回報提交前雜湊。 |
| PF6_O_REUSED_ID | `geometry-web/panel_fill_builder_bridge.inc:311` | `PF6_O_REUSED_ID` | 既有零號 host 是合法明示來源；預覽與確認的 reusedDefinitions 必須都回報同一精確 ID。 |
| PF6_O_SELECTED_SET_ONLY | `geometry-app/native/panel_fill_builder.inc:226` | `PF6_SELECTED_PREFIX_RECOMPUTES_SPAN` | 重算只能使用明示 selected 集合；未選支不得偷渡為縮短次支跨距的支承。 |
| R03A_CONFIRM_DIFFERENT_CANDIDATE | `geometry-web/framing_template_bridge.inc:347` | `R03A_CONFIRM_DIFFERENT_CANDIDATE` | Publish an unpreviewed ordinary definition during confirm; the preview/committed canonical fingerprints must differ. |
| R03A_FIXED_JIG | `geometry-templates/woodworking/native/flat_ceiling_jig.h:65` | `R03A_FIXED_JIG` | Replace the ratified fixed jig with the old per-cell ceil split. |
| R03A_LAST_TWO_STEPS_SPLIT | `geometry-templates/woodworking/native/flat_ceiling_jig.h:62` | `R03A_FIXED_JIG` | Omit the existing oracle merge/split when the last jig mark intersects the end member. |
| R03A_REJECT_WRITES | `geometry-web/framing_template_bridge.inc:312` | `R03A_REJECT_WRITES` | Write an ordinary spec and a history frame after the full native candidate has been rejected. |
| R03_CANCEL_ZERO_WRITE | `geometry-web/framing_template_bridge.inc:333` | `R03_CANCEL_ZERO_WRITE` | complete native bridge: cancel publishes the candidate and records history |
| R03_CEIL_MARKS | `geometry-templates/woodworking/native/flat_ceiling.h:88` | `R03_CEIL_MARKS` | production C generation: floor cell count changes/removes required marks |
| R03_MAIN_CONTINUOUS | `geometry-templates/woodworking/native/flat_ceiling.h:126` | `R03_MAIN_CONTINUOUS` | production C generation: a main ends midway instead of reaching the opposite boundary member |
| R03_MARK_GUIDE_FREEZES_GRID_SOURCE | `geometry-web/framing_template_bridge.inc:203` | `R03_MARK_GUIDE_LIVE_SOURCE` | Persist an accepted grid-backed mark as a fixed spec coordinate. |
| R03_NOT_CENTERED | `geometry-templates/woodworking/native/flat_ceiling.h:70` | `R03_NOT_CENTERED` | production C generation: translate the starting edge by half the panel remainder |
| R03_ONLY_OPPOSITE_WALL_TRIM | `geometry-templates/woodworking/native/flat_ceiling.h:75` | `R03_ONLY_OPPOSITE_WALL_TRIM` | production C generation: adopt historical last-seam retreat, cutting the penultimate panel |

各片的 `tests` 是正式ME指定方法；`expected_assertion`是metadata，定向diagnostic另驗marker。
原正式ME分類、七片分配、120/900秒與job時限、crashed規則、來源／裁判閉包均不減。
所有新執行收據由原Mutation evidence產生並原樣採入不可變store；本補丁不更新歷史seed或收據。
