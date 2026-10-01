# 組構規則第一階段驗收（GEO-226／PR #26）

起點：PR 草稿 `1ac155e`，整合既有主線 `17bd432`。條文定案與正典同步：`8207401`。
正式功能與驗證腳本在本文件同一提交；PR 使用 Refs #19，不自動關閉尚待實機驗收的總工單。

## 範圍

第一階段是自訂規則與固定版本材料配置。沒有施工角材生成器，也沒有放寬 D15/I19。
只有一個正式入口：「建立物件 → 組構規則」。草稿、發布版本、材料配置共用工作區與專案保存列。

## 驗收矩陣

原生案例位於 `tests/test_assembly_rules.py::AssemblyRules`；UI 案例為
`geometry-web/assembly_workflow_test.js`（完整 CDP 入口的 P77）。

| ID | 證據與觀察 |
|---|---|
| A01–A02 | `test_publish_without_geometry_and_native_identity`；P77 由空專案建立槽位、構件、接合，保存未發布草稿，不生成面或角材。 |
| A03–A05 | `test_orthogonal_split_and_geometric_loop`；P77 真正點選局部交換、端點與側面；旋轉縮放後定義逐字相同。 |
| A06 | `test_duplicate_scope_and_endpoint_rejected`；P77 預覽指出兩個接合，World 不變。 |
| A07–A08 | `test_immutable_version_rename_reorder_and_fixed_binding`、`test_missing_duplicate_and_unknown_fields_rejected`；P77 改名重排不改身分，使用中槽位不得直接刪除。 |
| A09 | `test_orthogonal_split_and_geometric_loop` 接受四邊鄰接環。 |
| A10 | 首版無巢狀規則、規則求值引用；未知引用欄位在 schema 層拒絕。未宣稱有不存在的循環求值器。 |
| A11–A13 | `test_material_source_and_parameter_recomputation`、`test_unselected_binding_is_saved_as_incomplete`、`test_bad_dimension_sources_rejected_not_incomplete`；同材、不同來源、未選齊、錯型與失效來源分別驗證。 |
| A14 | `test_canvas_move_preserves_preview_and_history`；P77 真拖卡片、旋轉縮放後指紋不變。 |
| A15–A17 | `test_copy_and_idempotent_publication`、`test_immutable_version_rename_reorder_and_fixed_binding`、`test_cancel_and_protocol_tokens_do_not_commit`；P77 真複製、發布下一版、明選對應後取消。 |
| A18–A19 | `test_scene_roundtrip_in_fresh_process`、`test_referenced_rule_delete_and_atomic_rebind`、`test_canvas_move_preserves_preview_and_history`；Node `test_assembly_project_store.js`；P77 保存重開、草稿復原及發布復原重做。 |
| A20–A21 | Node assembly/project/parameter 格式測試，原生 `test_truncated_corrupt_and_duplicate_records_are_atomic`；能力遭移除、未知格式、殘缺記錄均拒絕，既有格式保留。 |
| A22 | `test_authoring_capability_does_not_enable_model_generation`；既有 138 個 scene 案例持續驗證 D15/I19。 |
| A23 | P77 桌面與 390px 真實輸入、點選、返回、保存重開；無水平溢出、表單按鈕至少 44px。 |
| A24 | **待實體手機驗收**：手機鍵盤、OS 原生檔案選擇器與下載目的地。窄版 Chrome 不等於實機。保留 open 追蹤。 |

## 可重現命令

在 WSL／Linux，所有二進位都放 `/tmp/geometry-tests`：

```sh
ulimit -s 16384
python3 tests/run_all.py --build
python3 tests/assembly_mutation_check.py
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/build_assembly_example.py --check
python3 geometry-guide/sync_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
python3 tests/test_axiom_reader.py
```

啟動隔離服務，`GEOMETRY_FEEDBACK_DIR` 指向專用暫存資料夾；測試不可連到使用者正在工作的服務：

```sh
GEOMETRY_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/fb-assembly python3 geometry-web/serve.py 8836
```

另一終端給相同 `GEOMETRY_TEST_URL=http://localhost:8836/` 與 `GEOMETRY_FEEDBACK_DIR`：
執行 `node geometry-web/cdp_test.js`（不帶 ONLY）、`node geometry-web/space_model_test.js`。
Windows Chrome 連 WSL 服務時加 `GEOMETRY_TEST_SERVER_PATH_STYLE=wsl`，feedback 路徑的兩種表示必須指向同一資料夾。

## 故障注入

`tests/assembly_mutation_check.py` 在暫存來源副本編譯三種故障，先跑正常基準。
略過衝突檢查、略過尺寸來源解析、允許已取消預覽確認，均須由指定案例的 AssertionError 偵測。
編譯失敗、崩潰、skip 不算抓到缺陷；不修改工作區，也不覆寫既有全庫 mutation 結果。

## 環境限制與計數紀律

Windows SAC 仍阻擋部分 core／model adapter／GDI 執行檔；未停用安全設定。
WSL 的 Windows GDI 案例會 skip，不能說成全數通過。既有全庫 mutation 結果因核心改動會 stale；
本次只宣稱上述三項新功能故障注入結果，不冒用舊結果。
新增 suite 的 19 個 test 與 Node 的 4 個 test，依完整執行實際 census 更新 expected；
自動更新因 GDI skip 拒絕，故本次明確只調整這兩個數量，保留 skip 守門及非零退出碼。
斷言、單元案例、scene 案例與 C 檢查點分列，不相加宣稱端到端流程數。

最終執行摘要與可供審查的日誌見本目錄 `assembly-validation/`。
