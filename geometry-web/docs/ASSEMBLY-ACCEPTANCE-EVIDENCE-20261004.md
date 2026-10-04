# #24 組構驗收逐條證據索引（2026-10-04）

判準為已採納 D32/D33/I40/I41/R34 與 [#24 原驗收矩陣](https://github.com/ZhiQiYang/geometry-axiom/issues/24)。查核基底為 main `1c83b5e76cb0226bfd9c6c92289c8ab0760413e4`。本輪只補 A11/A12 的既有 native 案例；沒有產品、公理或共用測試基準變更。A24 仍未驗，#19/#24 不據此關閉。

第一階段文件與 2026-10-02/03 日誌是各自當時的紀錄。#25 的有限生成器已由 PR #53/#55 合併；能力為 D34/I42/R35 的 `assembly-timber-generation/1`，不代表任意自訂接合均能生成。歷史文件中的「沒有生成器／待實作」不能當作目前狀態。

## 證據來源與執行範圍

| 代號 | 來源、實際 head 與 scope |
|---|---|
| N | [native authoring 驗收](../../tests/test_assembly_rules.py)：35 個方法。本輪在原 `test_material_source_and_parameter_recomputation`、`test_unselected_binding_is_saved_as_incomplete` 補 subTest；方法數未變。補丁提交 `37ee1c25474c099eab3bfe932482983b96e14dd7`。 |
| C | [容量與材料型別](../../tests/test_assembly_capacity.py)：5 個方法，合法上界與下一筆原子拒絕。 |
| J | [專案封包](../../tests/test_assembly_project_store.js)、[工作區](../../tests/test_assembly_workspace.js)、[確認時序](../../tests/test_assembly_transport_context.js)：真 ZIP 與正式模組；部分工作區案例用替身環境，不冒稱全部為實際瀏覽器。 |
| U | 真 Chromium／native 的 [workflow](../assembly_workflow_test.js)、[review](../assembly_review_test.js)、[identity/mobile](../assembly_id_test.js)，由完整 CDP 的 P77 執行。實跑 head `6f935788de656883a59723f04817a15a34f4e398`，full 1970 pass／0 fail／0 skip、82 段 golden matched、completed=true；P77=134 個斷言。這不是 134 條獨立端到端流程。 |
| B | 整合 head `bb2c73914284eb503520710febc5d661e928e41a` 的既有非瀏覽器完整執行：54 suites、1645 pass／0 fail／1 具名 Windows GDI 平台略過。main `1c83b5e` 全 tree 與它相同。U 的產品與 P77 來源 blob 也與 main 相同；reader 更新另有自己的檢查。 |

U 是已有實跑證據的保留，沒有宣稱本輪重跑 full CDP。全局 raw browser exception 為 1，出自明示的 `fb-auto-probe` 預期注入；P77 新增未處理例外為 0。A24 不由此推導。

本輪新增驗證：N+C+ParameterRef+有限生成器四個已登記 native suites **64/64、0 fail、0 skip**，各方法數 35/5/3/21 與凍結基準相符；相關 Node 六檔 **103/103、0 skip**，另 space-model store **17/17、0 skip**。其中工程專案案例以隔離真服務重開。全部是聚焦執行，不能冒稱本輪完整 54 suites 驗收。

## A01–A24 索引

U 日誌行號指既有 `final-6f93578/full-cdp.log`；N/J 方法名可在上方連結直接定位。各列只宣告下述可觀察範圍。

| ID | 契約情境與可引用證據 | 實際觀察／邊界 |
|---|---|---|
| A01 | N `test_publish_without_geometry_and_native_identity`；U workflow 空白建立與草稿 ZIP 重開，log 1670–1679。 | 無房間／材料／網格仍可建規則、保存草稿；native 面／角材皆空。 |
| A02 | 同一 N 完整規則 value 比對；U workflow 真新增槽位／構件／接合；identity/mobile 從空白建規則，log 1779–1783。 | 自訂完整定義；N fixture 的 member1/2 同屬 slot1 而局部目標不同，沒有依名稱合併 member。 |
| A03 | N `test_orthogonal_split_and_geometric_loop`；U workflow 真 `asmSwap1`，log 1674、1682–1683。 | 局部交換改 native 定義與關係圖；非僅改文字。 |
| A04 | U workflow 單次交換第一 joint，完整 draft equality、native v2 equality、真 ZIP 重開 equality，log 1682–1683、1698。 | 第二 joint 與其餘欄位不變；局部關係独立。既有覆蓋已補齊，不重列舊缺口。 |
| A05 | N `test_missing_duplicate_and_unknown_fields_rejected`；U review 型別控制與 native joint 讀回，log 1729–1732。 | endpoint／side／dir 固定值，未知 kind、游標式 side 拒絕；視圖不代替定義。 |
| A06 | N `test_duplicate_scope_and_endpoint_rejected`；U 衝突 preview，log 1677。 | 診斷同時指出 joints1/2，確認拒絕、原 dump/revision 不變。 |
| A07 | N `test_immutable_version_rename_reorder_and_fixed_binding`；U v2 改名重排，log 1684。 | id/引用穩定，舊 binding 固定 v1；不以陣列位置配對。 |
| A08 | N `test_missing_duplicate_and_unknown_fields_rejected`、`test_binding_slot_and_face_contract`、`test_referenced_rule_delete_and_atomic_rebind`；U 刪槽負例，log 1676。 | 不留 dangling member/slot 或 rule 引用；合法明確改綁可與刪除同交易。 |
| A09 | N `test_orthogonal_split_and_geometric_loop`。 | 接受四邊幾何鄰接環，不把它當定義求值循環。 |
| A10 | N `test_missing_duplicate_and_unknown_fields_rejected` 的 `nested-rule` 等未知定義負例。 | 此版沒有巢狀規則求值引用；只宣告 schema 原子拒絕，不宣稱跑過不存在的遞迴循環求值器。 |
| A11 | N `test_material_source_and_parameter_recomputation` **本輪補驗**。 | 三配置分別同材同版、同材不同版、不同材料；反序 slots，完整 typed value＋逐 slot 不等尺寸/path 比對；發布更新材料後不升版，fresh native reload 保留完整 state/dump。既有參數重算仍驗。 |
| A12 | N `test_unselected_binding_is_saved_as_incomplete` **本輪補驗**；J draft-only ZIP。 | 保留全空正例；另四配置每次僅一 slot 的 contactFace 或 orientation=null，A/B 已選齊且來源/value/path 保留、complete=false；fresh reload 全等，沒有生成面／角材／instance。非法 enum 仍原子拒絕。 |
| A13 | N `test_bad_dimension_sources_rejected_not_incomplete`、`test_wrong_typed_fractional_sources_and_legacy_delete_reject`；C `test_material_kind_field_and_fixed_version_are_not_incomplete_values`。 | 不存在材料／版本、錯 kind／axis、錯型 ParameterRef、非正尺寸拒絕，不當未完成或補預設。C 另驗 8 slots／12 members／16 joints、32 versions／64 bindings、UTF-8 上界及超界拒絕。 |
| A14 | N `test_canvas_move_preserves_preview_and_history`；U 真 rotate/zoom 完整 draft 不變、真 card drag 位置變而 rule fingerprint 不變，log 1675、1693、1729。 | 不宣稱同一次 drag 同時全量比較每份 binding；既有角色與材料來源另由 N/J 保存驗證。 |
| A15 | N `test_copy_and_idempotent_publication`、`test_newid_wraps_past_max_in_independent_assembly_namespaces`；J workspace 配號；U copy/new/edit/碰撞，log 1689、1766–1778。 | 同名 native copy 新身分；UI 真新增／複製與 MAX 回繞不覆寫既有資料。 |
| A16 | N immutable-version 及 identity replacement 負例；U 編輯 v1→v2，log 1684。 | 新版本不覆寫舊版，舊 binding 固定 v1。 |
| A17 | N `test_atomic_new_version_rebind_delete_cancels_and_commits`；J mapping cancel/local undo-redo；U 明選新版→preview→cancel，log 1686–1688。 | U 核 binding 仍 v1；N 取消後完整 state/revision/dump 全等且 token 不可確認。取消預覽保留已明選的合法草稿；不等於撤銷草稿編輯。完整 World 與共用 history 的跨層證據合讀。 |
| A18 | N `test_scene_roundtrip_in_fresh_process`；本輪 A11/A12 fresh reload；J ZIP exact drafts/intent；U 保存重開與真正式 example 匯入，log 1679、1697–1702、1752。 | 真 export/import 保留規則版本、binding、位置存在及草稿。example 的完整配置固定 v1，未完成配置固定 v2，逐槽來源/值/null、版本順序與未發布 draft 分別驗。雙版本各自配置已覆蓋；不把「位置存在」寫成所有座標全等。 |
| A19 | N atomic new-version/rebind/delete 的 native undo-redo；J shared ContextHistory/無變更不加歷史；U review 真提交＋held reply，log 1709–1712、1751–1752。 | 一筆共用歷史、dirty=true、只清提交草稿；單步 native／草稿 undo-redo 協調，未提交另一草稿保留並真 ZIP 重開。不是每種 UI 刪除／改綁均在同一案例逐步比較 dirty。 |
| A20 | N `test_truncated_corrupt_and_duplicate_records_are_atomic`；J capability stripping/unknown schema/held-confirm context guard；project/parameter 能力負例。 | 殘缺／重複／未知格式與能力拒絕；原 dump/revision 或原 project context/history 保留。 |
| A21 | [face-projection store](../../tests/test_face_projection_store.js) `old projects stay v1/v2...` 與 v3 roundtrip；[space-model store](../../tests/test_space_model_store.js) `timber records round trip as v4...`；[engineering store](../../tests/test_engineering_project_store.js) v5；[parameter store](../../tests/test_parameters_project_store.js) v6。 | 各版真 ZIP accepted/roundtrip、format 與原 source/records 保留；舊版不強制升為組構格式。不是只引用降版拒絕負例。 |
| A22 | N `test_authoring_capability_does_not_enable_model_generation`；[有限生成器 native](../../tests/test_assembly_generation.py) 21 個既有案例；B 既有 scene 回歸。 | authoring 本身不生成；有限生成需其能力與完整輸入，仍拒碰撞／無承載面／缺 primary／失效來源等。D15/I19 未放寬，不代表任意拓撲已支援。 |
| A23 | U identity/mobile 390×844、空白專案真輸入建槽/構件/接合，未發布 ZIP 重開→native 發布→再重開完整定義全等，log 1779–1783；workflow/review 控件與返回，log 1694–1696、1720、1730–1732。 | 無水平溢出，可見 form controls 高度至少44px，圖 face controls 寬高至少44px；trusted 輸入與控制可用。ZIP 用正式 API；insertText 不是手機 IME、390px 不是實機。 |
| A24 | [既有 M1–M5 人工交接](ASSEMBLY-RULES-VALIDATION.md#a24-實機驗收交接未執行)。 | **未驗**：實體 iOS/Android 鍵盤、OS chooser、下載目的地、取消。必要裝置記錄未完成，不關閉 #19/#24。 |

A17 的單一 UI 全 World/history/dirty equality、A18 的同一雙 binding＋draft＋精確位置 archive equality 可加強現有組合 oracle；目前没有產品缺陷證據或新增必要需求，不能据此重開已補齊的 A04/A18/A23 缺口。

## 重現與原始證據

使用來源／binary SHA-256 freshness 守門。Native 四 suite 可由 `tests/run_all.py --only test_assembly_rules --only test_assembly_capacity --only test_assembly_parameter_refs --only test_assembly_generation` 聚焦執行；runner 清除繼承的 `GEOMETRY_*`，由 `binaries` 目錄重設子行程變數。需按其 binary 目錄準備 fresh 產物，不以檔名或外殼覆寫推定目前版本。Node 以下命令則直接使用列出的環境變數。

Node 命令：

```sh
node --test tests/test_assembly_project_store.js tests/test_assembly_transport_context.js tests/test_assembly_workspace.js tests/test_face_projection_store.js tests/test_engineering_project_store.js tests/test_parameters_project_store.js
node --test tests/test_space_model_store.js
```

設定 `GEOMETRY_TEST_BRIDGE`、`GEOMETRY_ENGINEERING_BRIDGE`（舊工程真服務案例仍需此名稱）與 `GEOMETRY_MODEL_BASE` 為同来源的 fresh 產物；未設齊只能得到明示 skip。初跑 103 案例為102 pass／1 skip，补足後為103/103；space store 初跑16 pass／1 skip，補足後17/17。保留兩次結果，不用後次結果冒稱前次無略過。

原始本輪 logs／來源與 head 證明在 cloud TEMP `/tmp/geometry-tests/geometry24-acceptance-20261004/`，交接附 SHA-256；生成檔沒有提交 repo。既有完整證據目錄 `/tmp/geometry-tests/geometry47-navigation-20261004/`：

- `final-6f93578/final-evidence.json` SHA-256 `cb3b3c68eb862b283cafa2d6021753cfe86137160d856db7992895d039117e80`。
- `integrated-bb2c739/final-evidence.json` SHA-256 `511beb0bdc6e029857a435593be54f6f13580b01408dd68e47efc5c9d341cdea`。
- `postmerge-1c83b5e/final-evidence.json` SHA-256 `af2dea7f9c18fe2285028ca611ade700990742d0d12fc67ce3ca1c0022b145e5`。

TEMP 路徑供同 cloud 的審查者讀取；其他環境以 source/test 名、命令及 PR 交接 head 重現，不把無法存取的 TEMP 當公開 CI artifact。歷史 raw logs、失敗與凍結基準皆保留。
