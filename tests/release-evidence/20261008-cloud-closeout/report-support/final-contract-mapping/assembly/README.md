# #24 A01–A24 逐條來源／封存證據映射

只讀審查；沒有啟動 native、瀏覽器、測試或服務，沒有修改 repo、public-candidate、queue 或外部資料。原矩陣來自封存 GitHub #24 body；完整原文與來源雜湊保存在 `issue-24-body.md` / `issue-24-source.json`。不是依公理編號猜測 A 編號。

目前審查 HEAD `d8642b2e684038cbb8e24aba057c44e7aac1b231`；原始 native 命令實際受測 clean `458779f003e1f57fdc0f4420564a0b295227843e`，full-CDP-r3 實際受測 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`。後續 docs-only 提交不重新標成產品實跑版本。所有本表使用的產品／測試檔在三個 SHA bytes 相同，見 `source-identities.json`；完整 native 閉包與 app VM slices另見既有 [report-support/native-source-impact-458-to-5174.json](../../../report-support/native-source-impact-458-to-5174.json)。

native 檔案方法由 AST 定位，逐檔 census 精確等於完整執行收據 run=passed、failed=skipped=0，並已閱讀相關 oracle。原始 unittest log 只有點號；本表不冒稱原始 log 逐方法列名。Node/raw P77 則有具名通過行。沒有以 suite 或斷言總數替代條目內容。

可用原件：[native/full-run-all-new-owners.json](../../../native/full-run-all-new-owners.json)（命令、clean SHA、exit 0）、`raw-native/`（封存 tar member 原bytes）、[gates/full-cdp-r3/receipt.json](../../../gates/full-cdp-r3/receipt.json) / [gates/full-cdp-r3/command.log](../../../gates/full-cdp-r3/command.log)（命令、clean SHA、runtime/bridge、exit 0、completed=true、具名 P77）、[gates/compound-project/](../../../gates/compound-project/)（產品保存/清空/fresh browser重開）。完整命令/環境/時間/來源腳本雜湊/退出碼/載入bridge獨立觀察整理於 `execution-bindings.json`；native全套為 `ulimit -s 16384` 後 `python3 tests/run_all.py`，browser為 `node geometry-web/cdp_test.js`，不可把裸命令當有相同環境。full-CDP raw exception 1 為既有 P38 預期注入；P77 自身具名例外檢查通過，不稱全局 zero exception。

判定：A01–A23 都能找到對應已執行 oracle 或 A10 的原文允許能力邊界。A14/A17/A19 保留既有組合證據的直接觀察限制；這份唯讀映射沒有發現新的必須改產品的 assembly 缺陷，亦不能把這些限制改寫成一個未曾執行的全量 UI oracle。A24 是確定尚未執行的實體裝置條件。整張 #19/#24 保持 open；其他 #173/#174/Resume 的已知產品失敗仍由各自 gate 管理，本表不代替整體候選批准。

## A01 — 無房間／材料／網格時建立

原矩陣原文：**能建立並保存合法草稿，不暗建面／角材**（`issue-24-body.md:114`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:57` `async function prepareDraft`；`geometry-web/reference-workspace.js:568` `function setAssemblyDraft`；`geometry-core/assembly.inc:86` `static bool asm_publish`。

判定：**bounded automated evidence**。空白正式 UI 建草稿，ZIP 保存未發布值；native 規則可獨立於面、角材存在。

- native `test_publish_without_geometry_and_native_identity` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:87 / raw-native/py_test_assembly_rules.json`。
- browser `空世界草稿從零開始` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1939](../../../gates/full-cdp-r3/command.log#L1939)。
- browser `開啟中的草稿保存最新值` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1947](../../../gates/full-cdp-r3/command.log#L1947)。
- browser `發布後原生卡片可找到且不生成角材` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1948](../../../gates/full-cdp-r3/command.log#L1948)。
- node `draft-only projects require assembly capability and format 7, preserving incomplete values` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:1`。

限制：P77 草稿 ZIP 使用 exportBytes/importBytes；不是 OS chooser。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A02 — 空白規則新增角色及接合

原矩陣原文：**自訂可用，不只選固定範本**（`issue-24-body.md:115`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:122` `function ruleForm`；`geometry-core/assembly.inc:47` `static bool asm_validate_rule`。

判定：**bounded automated evidence**。真新增槽位、member、joint；完整規則定義由 native 讀回相等。

- native `test_publish_without_geometry_and_native_identity` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:87 / raw-native/py_test_assembly_rules.json`。
- browser `A23 390px 空白建立完整規則的精確來源` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2047](../../../gates/full-cdp-r3/command.log#L2047)。
- browser `A23 手機發布資料由原生核心讀回完全一致` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2050](../../../gates/full-cdp-r3/command.log#L2050)。

限制：390px 為 Chromium emulation，非手機。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A03 — 交換局部連續方

原矩陣原文：**核心定義與示意都變，非只換名字**（`issue-24-body.md:116`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:122` `function ruleForm`；`geometry-web/assembly-workspace.js:141` `function diagram`；`geometry-core/assembly.inc:47` `static bool asm_validate_rule`。

判定：**bounded automated evidence**。連續方交換改 typed definition；SVG 端點/方向有具體幾何屬性 oracle。

- native `test_orthogonal_split_and_geometric_loop` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:231 / raw-native/py_test_assembly_rules.json`。
- browser `正交分段按局部交換連續構件` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1942](../../../gates/full-cdp-r3/command.log#L1942)。
- browser `A04 不同局部配置真正寫進原生發布版本` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1951](../../../gates/full-cdp-r3/command.log#L1951)。
- node `endpoint and direction choices change drawn SVG attributes, not only text` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:68`。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A04 — 同角色在不同接合採不同配置

原矩陣原文：**局部關係獨立保存，不受全域 priority 覆蓋**（`issue-24-body.md:117`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:122` `function ruleForm`；`geometry-core/assembly.inc:47` `static bool asm_validate_rule`。

判定：**bounded automated evidence**。局部 first joint 精確交換，第二 joint 和其餘欄位全等，发布及 ZIP 重開仍全等。

- browser `A04 單次局部交換精確改第一接合並保留第二接合` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1950](../../../gates/full-cdp-r3/command.log#L1950)。
- browser `A04 不同局部配置真正寫進原生發布版本` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1951](../../../gates/full-cdp-r3/command.log#L1951)。
- browser `A04 真正保存重開後兩處不同接合與完整定義不變` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1966](../../../gates/full-cdp-r3/command.log#L1966)。

限制：P77 ZIP 走正式 API；不是 chooser。A04 原已補齊，不重開舊待辦。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A05 — 選端面與側面

原矩陣原文：**保存型別／固定身份；視圖或游標位置不代替定義**（`issue-24-body.md:118`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:47` `static bool asm_validate_rule`；`geometry-web/assembly-workspace.js:141` `function diagram`。

判定：**bounded automated evidence**。end/side/dir 固定身份，游標式 side 與未知 kind 拒絕；UI 图/表單與 native 相符。

- native `test_missing_duplicate_and_unknown_fields_rejected` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:220 / raw-native/py_test_assembly_rules.json`。
- native `test_binding_slot_and_face_contract` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:495 / raw-native/py_test_assembly_rules.json`。
- browser `起終端控制改变接觸處實際圖形位置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1989](../../../gates/full-cdp-r3/command.log#L1989)。
- browser `局部 u/v 控制改变實際方向箭頭端點` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1990](../../../gates/full-cdp-r3/command.log#L1990)。
- browser `圖上點選與鍵盤選面同步表單` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1995](../../../gates/full-cdp-r3/command.log#L1995)。
- browser `新增方向及端點圖形旋轉縮放不改固定身分` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1997](../../../gates/full-cdp-r3/command.log#L1997)。
- browser `示意控制結果與真核心讀回一致且不生成角材` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2000](../../../gates/full-cdp-r3/command.log#L2000)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A06 — 同處矛盾接合

原矩陣原文：**指出兩個衝突條件，不採最後輸入者勝出**（`issue-24-body.md:119`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:47` `static bool asm_validate_rule`；`geometry-web/assembly_bridge.inc:32` `static void json_assembly_preview`。

判定：**bounded automated evidence**。重複 scope/endpoint 診斷含 joints 1 and 2；共用 reject oracle 核確認拒絕、dump/revision不變。

- native `test_duplicate_scope_and_endpoint_rejected` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:215 / raw-native/py_test_assembly_rules.json`。
- browser `衝突預覽拒絕且正式世界為空` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1945](../../../gates/full-cdp-r3/command.log#L1945)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A07 — 角色改名／重排

原矩陣原文：**原 slot/member/joint 引用不變**（`issue-24-body.md:120`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:47` `static bool asm_validate_rule`；`geometry-web/assembly-workspace.js:122` `function ruleForm`。

判定：**bounded automated evidence**。改名重排不變 joint/member 對應；native 新版可倒序而舊 binding 保持 v1。

- native `test_immutable_version_rename_reorder_and_fixed_binding` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:239 / raw-native/py_test_assembly_rules.json`。
- browser `改名排序不改接合身分` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1946](../../../gates/full-cdp-r3/command.log#L1946)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A08 — 刪除被接合引用的角色

原矩陣原文：**拒絕或在明確交易解除，不留孤兒**（`issue-24-body.md:121`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:47` `static bool asm_validate_rule`；`geometry-core/assembly.inc:144` `static bool assembly_rebuild`；`geometry-web/assembly-workspace.js:122` `function ruleForm`。

判定：**bounded automated evidence**。被引用 slot 的 UI 刪除拒絕；native dangling refs拒絕，合法改綁+刪除同交易可Undo/Redo。

- native `test_missing_duplicate_and_unknown_fields_rejected` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:220 / raw-native/py_test_assembly_rules.json`。
- native `test_binding_slot_and_face_contract` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:495 / raw-native/py_test_assembly_rules.json`。
- native `test_referenced_rule_delete_and_atomic_rebind` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:442 / raw-native/py_test_assembly_rules.json`。
- browser `刪除使用中槽位指出構件` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1944](../../../gates/full-cdp-r3/command.log#L1944)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A09 — 矩形框的幾何鄰接環

原矩陣原文：**不誤判為求值依賴循環**（`issue-24-body.md:122`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:47` `static bool asm_validate_rule`。

判定：**bounded automated evidence**。具四個 member 的四邊幾何鄰接環發布成功，規則數精確為2。

- native `test_orthogonal_split_and_geometric_loop` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:231 / raw-native/py_test_assembly_rules.json`。

限制：不是求值依賴循環求值器測試。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A10 — 非法定義依賴循環

原矩陣原文：**契約可表達的真循環原子拒絕；不為測試擅增巢狀規則功能**（`issue-24-body.md:123`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:77` `nested rules are unsupported`。

判定：**explicit accepted capability boundary**。kind=nested-rule、未知欄位、錯引用由 I40 schema 原子拒絕。

- native `test_missing_duplicate_and_unknown_fields_rejected` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:220 / raw-native/py_test_assembly_rules.json`。

限制：首版無巢狀規則引用/求值器；#24 A10 明文容許此能力邊界。

剩餘：None within adopted authoring schema. Do not add a recursive evaluator to satisfy an inexpressible case.

## A11 — 主副支同材／不同材

原矩陣原文：**各角色來源明確且獨立**（`issue-24-body.md:124`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:106` `static bool asm_binding_parse`；`geometry-web/assembly-workspace.js:159` `function sources`；`geometry-web/assembly-workspace.js:160` `function bindingForm`。

判定：**bounded automated evidence**。同材同版、同材不同版、不同材3配置；逆序slots，以固定identity比完整value/effective/path；新材料版不暗升；fresh native reload全state/dump。

- native `test_material_source_and_parameter_recomputation` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:380 / raw-native/py_test_assembly_rules.json`。
- browser `同值換來源 1 確認保留精確引用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2004](../../../gates/full-cdp-r3/command.log#L2004)。
- browser `同值換來源 2 確認保留精確引用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2006](../../../gates/full-cdp-r3/command.log#L2006)。
- browser `換來源重做保存重開保留固定版本與參數引用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2020](../../../gates/full-cdp-r3/command.log#L2020)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A12 — 材料或方向未選齊

原矩陣原文：**可存合法未完成綁定，不宣稱已產生施工幾何**（`issue-24-body.md:125`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:106` `static bool asm_binding_parse`；`geometry-web/assembly-workspace.js:160` `function bindingForm`；`geometry-web/project-store.js:210` `function validateAssemblyDraft`。

判定：**bounded automated evidence**。全空与4種僅一slot缺face/orientation合法incomplete；已選來源/value/path保留；fresh reload完整相等；面/角材/instance皆空。

- native `test_unselected_binding_is_saved_as_incomplete` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:342 / raw-native/py_test_assembly_rules.json`。
- browser `未選材料保存為未完成` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1949](../../../gates/full-cdp-r3/command.log#L1949)。
- node `draft-only projects require assembly capability and format 7, preserving incomplete values` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:1`。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A13 — 不存在或錯型材料引用

原矩陣原文：**拒絕，不補預設或當空欄**（`issue-24-body.md:126`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:106` `static bool asm_binding_parse`；`geometry-core/assembly.inc:47` `static bool asm_validate_rule`。

判定：**bounded automated evidence**。不存在材料/版、錯kind/axis/type、非正尺寸與非法ParameterRef原子拒絕；容量上界/下一筆拒絕另有capacity具名方法census。

- native `test_bad_dimension_sources_rejected_not_incomplete` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:435 / raw-native/py_test_assembly_rules.json`。
- native `test_wrong_typed_fractional_sources_and_legacy_delete_reject` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:520 / raw-native/py_test_assembly_rules.json`。
- native `test_material_kind_field_and_fixed_version_are_not_incomplete_values` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_capacity.py:18 / raw-native/py_test_assembly_capacity.json`。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A14 — 拖卡片／縮放旋轉示意

原矩陣原文：**定義／接合身份／材料對應不變**（`issue-24-body.md:127`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:141` `function diagram`；`geometry-core/assembly.inc:157` `static bool assembly_dimensions_changed`。

判定：**composed evidence with declared direct-oracle limit**。旋轉縮放完整draft不變；真drag位置變且native rule fingerprint不變；native canvas-pos在pending binding後保留confirm及Undo/Redo。

- native `test_canvas_move_preserves_preview_and_history` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:469 / raw-native/py_test_assembly_rules.json`。
- browser `旋轉縮放只改檢視` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1943](../../../gates/full-cdp-r3/command.log#L1943)。
- browser `拖曳原生卡片只改位置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1961](../../../gates/full-cdp-r3/command.log#L1961)。
- browser `新增方向及端點圖形旋轉縮放不改固定身分` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1997](../../../gates/full-cdp-r3/command.log#L1997)。

限制：真drag的直接oracle沒有同時全量比對每一份binding/material mapping；原20261004索引已明示此限制。

剩餘：Optional strengthening: capture full assembly-read before/after the same trusted drag and compare every binding; not evidence of a discovered product bug or a reopened accepted A04/A18/A23 gap.

## A15 — 複製規則

原矩陣原文：**新身份，不覆寫同名來源**（`issue-24-body.md:128`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:22` `function freeId`；`geometry-web/assembly-workspace.js:57` `async function prepareDraft`；`geometry-core/assembly.inc:172` `static bool assembly_operation`。

判定：**bounded automated evidence**。native同名copy新ID，UI複製/新增/MAX回繞，不覆寫既有native或草稿。

- native `test_copy_and_idempotent_publication` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:264 / raw-native/py_test_assembly_rules.json`。
- native `test_newid_wraps_past_max_in_independent_assembly_namespaces` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:248 / raw-native/py_test_assembly_rules.json`。
- browser `複製有新原生身分` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1957](../../../gates/full-cdp-r3/command.log#L1957)。
- browser `A15 真複製跳過原生及草稿取得規則3` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2044](../../../gates/full-cdp-r3/command.log#L2044)。
- browser `A15 複製發布保留原有2與MAX且未吞草稿1` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2045](../../../gates/full-cdp-r3/command.log#L2045)。
- node `new and copied rules/bindings skip interleaved native and draft IDs after uint32 wrap` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:37`。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A16 — 修改發布規則

原矩陣原文：**新版本，舊綁定仍指原版**（`issue-24-body.md:129`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:86` `static bool asm_publish`；`geometry-core/assembly.inc:98` `static bool assembly_versions_immutable`；`geometry-web/assembly-workspace.js:57` `async function prepareDraft`。

判定：**bounded automated evidence**。immutable舊版不可覆寫，包括delete/republish/copy繞過；發布v2不暗升binding。

- native `test_immutable_version_rename_reorder_and_fixed_binding` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:239 / raw-native/py_test_assembly_rules.json`。
- native `test_same_transaction_delete_republish_cannot_change_fixed_version` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:271 / raw-native/py_test_assembly_rules.json`。
- native `test_intermediate_identity_replacement_is_rejected_before_later_restore` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:300 / raw-native/py_test_assembly_rules.json`。
- browser `新版本不升級既有配置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1952](../../../gates/full-cdp-r3/command.log#L1952)。
- browser `A04 不同局部配置真正寫進原生發布版本` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1951](../../../gates/full-cdp-r3/command.log#L1951)。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A17 — 明選升版後取消

原矩陣原文：**原綁定／World／history 不變**（`issue-24-body.md:130`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:160` `function bindingForm`；`geometry-web/assembly-workspace.js:45` `function invalidate`；`geometry-web/assembly_bridge.inc:60` `static void cmd_assembly_cancel`。

判定：**composed evidence with declared direct-oracle limit**。UI明選新版/preview/cancel後binding仍v1；native cancel完整state+revision+dump相等且token不能確認；草稿選版可保留。

- native `test_atomic_new_version_rebind_delete_cancels_and_commits` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:320 / raw-native/py_test_assembly_rules.json`。
- native `test_cancel_and_protocol_tokens_do_not_commit` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:455 / raw-native/py_test_assembly_rules.json`。
- browser `預覽寫出換了哪一版` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1955](../../../gates/full-cdp-r3/command.log#L1955)。
- browser `取消換版不改正式配置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1956](../../../gates/full-cdp-r3/command.log#L1956)。
- browser `預覽與取消不改真核心且特殊名稱只作文字` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2002](../../../gates/full-cdp-r3/command.log#L2002)。
- node `explicit new-version mapping keeps typed sources and its fixed provenance through undo and redo` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:52`。

限制：沒有單一UI case同時全量比較World+history+dirty；正式preview取消不是撤銷先前已明選草稿，後者已有local history。

剩餘：Optional single-UI World/history/dirty snapshot strengthening; existing acceptance index explicitly treats this as composed coverage, not a newly necessary product change.

## A18 — 完整專案保存重開

原矩陣原文：**規則全部版本、綁定、草稿和位置保留**（`issue-24-body.md:131`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:225` `static void assembly_dump`；`geometry-core/assembly.inc:233` `static bool apply_assembly_line`；`geometry-web/project-store.js:247` `function validateAssemblyDrafts`；`geometry-web/reference-workspace.js:1626` `c.assemblyDrafts=JSON.parse`。

判定：**bounded automated evidence**。兩版本+各自binding精確來源/null，草稿獨立；fresh native scene全等。額外compound-project清空確認+fresh browser正式Save/New/Open覆蓋非空model+draft+assembly instance。

- native `test_scene_roundtrip_in_fresh_process` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:477 / raw-native/py_test_assembly_rules.json`。
- native `test_material_source_and_parameter_recomputation` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:380 / raw-native/py_test_assembly_rules.json`。
- native `test_unselected_binding_is_saved_as_incomplete` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:342 / raw-native/py_test_assembly_rules.json`。
- browser `保存重開保留所有版本配置與卡片位置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1965](../../../gates/full-cdp-r3/command.log#L1965)。
- browser `A18 範例配置一固定第1版且逐槽來源與有效值正確` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1968](../../../gates/full-cdp-r3/command.log#L1968)。
- browser `A18 範例配置二固定第2版且保留精確未完成槽位` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1969](../../../gates/full-cdp-r3/command.log#L1969)。
- browser `A18 範例版本槽位排序與未發布草稿不混為另一版` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1970](../../../gates/full-cdp-r3/command.log#L1970)。
- browser `回覆完成後共用保存重開仍保留 B 精確資料` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1980](../../../gates/full-cdp-r3/command.log#L1980)。
- node `binding create/update intent and exact original source survive formal archive reopen` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:8`。
- compound-project：1400/390 各自具名 `trusted New clears native World, model, drafts, instances and changes project identity`、`second browser process with fresh profile starts empty before Open`、`fresh-profile formal chooser restores complete World, references, instances, model and draft bytes` 均通過；完整11項/width來源與時刻見 mapping.json supplemental，原件 [gates/compound-project/artifacts/1400/result.json](../../../gates/compound-project/artifacts/1400/result.json) / [gates/compound-project/artifacts/390/result.json](../../../gates/compound-project/artifacts/390/result.json)；受測 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，命令/gate退出0。API seed明示，正式Save/New/Open是真產品控件及chooser事件，但不是OS picker。

限制：P77位置是hasPos，不是所有座標全等；compound另有完整payload equality，但fixture不等於P77所有兩版組合。

剩餘：No reopened A18 gap. Optional one-archive two-bindings+draft+all-position coordinates joint equality is additional strengthening, not a discovered missing implementation.

## A19 — 建立／刪除／改綁的復原重做

原矩陣原文：**native 和專案資料協調，dirty 一致**（`issue-24-body.md:132`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/reference-workspace.js:568` `function setAssemblyDraft`；`geometry-web/reference-workspace.js:79` `function beginAssemblyConfirmation`；`geometry-web/project-store.js:718` `class ContextHistory`；`geometry-web/assembly-workspace.js:279` `async function confirm`。

判定：**composed evidence with declared direct-oracle limit**。native建立/刪除/改綁交易完整Undo/Redo，Node共用history與no-op，UI發布dirty=true只一筆history、草稿協調；另真instance刪除Undo/Redo。

- native `test_atomic_new_version_rebind_delete_cancels_and_commits` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:320 / raw-native/py_test_assembly_rules.json`。
- native `test_referenced_rule_delete_and_atomic_rebind` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:442 / raw-native/py_test_assembly_rules.json`。
- native `test_identical_delete_republish_has_no_revision_or_history_change` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:308 / raw-native/py_test_assembly_rules.json`。
- browser `成功僅清理提交草稿且只新增一筆共用歷史` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1977](../../../gates/full-cdp-r3/command.log#L1977)。
- browser `單步復原原生發布同時恢復兩份草稿` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1978](../../../gates/full-cdp-r3/command.log#L1978)。
- browser `單步重做只清理原提交草稿` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1979](../../../gates/full-cdp-r3/command.log#L1979)。
- browser `換來源單步復原還原先前 B 引用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2019](../../../gates/full-cdp-r3/command.log#L2019)。
- browser `換來源重做保存重開保留固定版本與參數引用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2020](../../../gates/full-cdp-r3/command.log#L2020)。
- browser `G08 刪除整個實例與三支原生角材` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2068](../../../gates/full-cdp-r3/command.log#L2068)。
- browser `G08 單步復原映射與實例` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2069](../../../gates/full-cdp-r3/command.log#L2069)。
- browser `G08 單步重做刪除` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2070](../../../gates/full-cdp-r3/command.log#L2070)。
- node `assembly drafts and native confirmation share undo and redo without losing incomplete edits` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:4`。
- node `ordinary, rejected and no-op assembly results release the guard and preserve native history counts` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:19`。

限制：未聲稱每一種規則/綁定UI刪除/改綁均在同一案例逐步比較dirty。

剩餘：Optional UI delete-rule/delete-binding/rebind per-action dirty snapshot strengthening; native operations and shared-history mechanism have named evidence. No product defect discovered by this read-only mapping.

## A20 — 未知格式／移除必要能力

原矩陣原文：**明確拒絕，原專案不變**（`issue-24-body.md:133`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:233` `static bool apply_assembly_line`；`geometry-web/project-store.js:247` `function validateAssemblyDrafts`；`geometry-web/reference-workspace.js:65` `assertAssemblyIdle`。

判定：**bounded automated evidence**。殘缺/重複/未知schema/必要能力不足明確拒絕；原native dump 或project context/history保留。

- native `test_truncated_corrupt_and_duplicate_records_are_atomic` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:486 / raw-native/py_test_assembly_rules.json`。
- browser `G06 能力不足拒絕匯入且世界草稿歷史不變` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2072](../../../gates/full-cdp-r3/command.log#L2072)。
- node `draft capability stripping, old format, unknown schema and duplicate IDs reject` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:3`。
- node `a late successful assembly reply cannot dirty, append history or notify an externally replaced context` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:20`。
- node `matrix: unknown project versions and stripped or unknown capability markers are rejected` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:260`。

限制：仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A21 — 舊 geometry-canvas/1–6

原矩陣原文：**舊能力與來源正常，不暗遷移組法**（`issue-24-body.md:134`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/project-store.js:9` `const ASSEMBLY_FORMAT`；`geometry-web/project-store.js:718` `class ContextHistory`。

判定：**bounded automated evidence**。v1/v2/v3/v4/v5/v6實際ZIP accepted/roundtrip保留format與來源；沒有只用拒絕降版負例替代合法舊格式。

- node `old projects stay v1/v2 without defining existing faces; an empty definition list is not a forced upgrade` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:106`。
- node `a face with no PDF or model saves and reopens its definition as v3, independently for each placement` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:105`。
- node `timber records round trip as v4 with exact id zero, source snapshots and independent geometry packages` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:578`。
- node `engineering scene remains the sole source and selects v5 with a required capability` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:90`。
- node `parameter projects use /6, retain scene bytes and require native support` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:256`。
- node `legacy v1/v2/v3 archives and height-edit inputs do not gain empty timber fields or forced v4 upgrades` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:579`。

限制：Node存儲/服務測試，不宣称所有旧版都在真OS chooser跑一遍。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A22 — 自訂規則與舊 D15/I19 不相容

原矩陣原文：**authoring 不生成非法角材、不放寬底線**（`issue-24-body.md:135`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-core/assembly.inc:5` `Authoring validates sources and local topology`；`geometry-web/assembly-workspace.js:175` `async function newInstance`；`geometry-core/assembly_generation.inc:2` `static bool`。

判定：**bounded automated evidence**。authoring不生成；model load因CAPABILITY拒絕。不完整有限生成輸入禁止套用；有限生成具名負例驗錯承載/guide/support、inward接合、超出支持拓樸/方向與碰撞拒絕、World不變。

- native `test_authoring_capability_does_not_enable_model_generation` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_rules.py:538 / raw-native/py_test_assembly_rules.json`。
- native `test_missing_wrong_sources_and_inward_joint_geometry_are_atomic` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_generation.py:148 / raw-native/py_test_assembly_generation.json`。
- native `test_unsupported_section_orientation_and_joint_topology` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_generation.py:156 / raw-native/py_test_assembly_generation.json`。
- native `test_unselected_sources_report_i42_and_preserve_world_on_create_and_edit` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_generation.py:159 / raw-native/py_test_assembly_generation.json`。
- native `test_source_change_collision_rejects_entire_world` — pass via complete unfiltered file execution and AST census; dot log does not name individual methods；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`tests/test_assembly_generation.py:210 / raw-native/py_test_assembly_generation.json`。
- browser `發布後原生卡片可找到且不生成角材` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1948](../../../gates/full-cdp-r3/command.log#L1948)。
- browser `示意控制結果與真核心讀回一致且不生成角材` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2000](../../../gates/full-cdp-r3/command.log#L2000)。
- browser `G06 未選定位線不能套用` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2063](../../../gates/full-cdp-r3/command.log#L2063)。

限制：不把有限3member生成宣稱任意拓樸。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A23 — 桌面、390px 建立／編輯／返回／保存

原矩陣原文：**真操作可用、無遮擋／失焦，離開守門一致**（`issue-24-body.md:136`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/assembly-workspace.js:122` `function ruleForm`；`geometry-web/assembly-workspace.js:160` `function bindingForm`；`geometry-web/assembly-workspace.js:50` `function close`；`geometry-web/assembly-workspace.js:42` `function lockConfirm`；`geometry-web/assembly-workspace.css:8` `44px`。

判定：**bounded automated evidence**。桌面+390px真建/編輯/控制/返回與鍵盤恢復；草稿/發布兩次重開，完整定義native equality；尺寸44px和無overflow。

- browser `390px 完成 A/B 材料配置` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1962](../../../gates/full-cdp-r3/command.log#L1962)。
- browser `390px 無橫向溢出與小於44px操作` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1964](../../../gates/full-cdp-r3/command.log#L1964)。
- browser `390px 端點方向圖可操作且沒有橫向溢出` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1998](../../../gates/full-cdp-r3/command.log#L1998)。
- browser `390px 最大縮放旋轉後選面至少44px且不覆蓋接觸圖` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1999](../../../gates/full-cdp-r3/command.log#L1999)。
- browser `A23 390px 空白建立完整規則的精確來源` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2047](../../../gates/full-cdp-r3/command.log#L2047)。
- browser `A23 390px 從空白新增全流程無橫向溢出` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2048](../../../gates/full-cdp-r3/command.log#L2048)。
- browser `A23 未發布手機草稿真正保存重開仍可編輯` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2049](../../../gates/full-cdp-r3/command.log#L2049)。
- browser `A23 手機發布資料由原生核心讀回完全一致` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2050](../../../gates/full-cdp-r3/command.log#L2050)。
- browser `A23 手機已發布規則再重開仍保留身分接合與來源` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:2051](../../../gates/full-cdp-r3/command.log#L2051)。
- browser `確認期間明確鎖住改稿切稿關閉與連點` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1975](../../../gates/full-cdp-r3/command.log#L1975)。
- browser `未知结果只用鍵盤返回重連再開不盲送也不刪草稿` — pass；受測 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；[gates/full-cdp-r3/command.log:1988](../../../gates/full-cdp-r3/command.log#L1988)。
- node `declining the existing leave gate preserves the old draft owner and pending token` — pass；受測 `458779f003e1f57fdc0f4420564a0b295227843e`；`raw-native/node_tests-js.log:36`。
- compound-project：1400/390 各自具名 `trusted New clears native World, model, drafts, instances and changes project identity`、`second browser process with fresh profile starts empty before Open`、`fresh-profile formal chooser restores complete World, references, instances, model and draft bytes` 均通過；完整11項/width來源與時刻見 mapping.json supplemental，原件 [gates/compound-project/artifacts/1400/result.json](../../../gates/compound-project/artifacts/1400/result.json) / [gates/compound-project/artifacts/390/result.json](../../../gates/compound-project/artifacts/390/result.json)；受測 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，命令/gate退出0。API seed明示，正式Save/New/Open是真產品控件及chooser事件，但不是OS picker。

限制：合成輸入不是手機IME；P77保存重開是正式API；compound補產品Save/New/Open，仍不是OS dialog。

剩餘：No additional mandatory internal work established by these records; preserve the stated observation boundary.

## A24 — 實體手機鍵盤／OS 檔案對話框

原矩陣原文：**人工記錄；窄版瀏覽器不得冒充實機**（`issue-24-body.md:137`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。

實作：`geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md:49` `## A24 實機驗收交接`。

判定：**external manual acceptance not executed**。沒有實體iOS/Android驗收收據。既有M1–M5操作與裝置表仍未填。


限制：Linux Chromium/390px、Node、native、完整CDP均不能代替實體鍵盤/IME/OS chooser/下載目的地/取消。

剩餘：Physical-device QA owner (not assigned in accessible records) runs existing M1–M5 on actual iOS/Android, records tested full SHA/runtime, OS/browser/device/orientation/input method, real saved file/destination/reopen and cancel outcomes. Project owner signs off; #19/#24 remain open.

## A24 原有 M1–M5 解除步驟

依 `geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md:49` 原交接，不另設新驗收：M1 中文IME/鍵盤/直橫向/焦點與可達性；M2 真保存且在OS目的地找到非空gcanvas；M3 另一空白專案經OS選檔重開；M4 兩發布版/完整與未完整binding/草稿重開核對；M5 離開提示、OS選檔和可取消保存提示的取消。填日期、驗收者、裝置、OS、瀏覽器、runtime/完整SHA及原始結果。可取得紀錄沒有指名當前實體裝置驗收owner，保持 unknown，不虛構已派工。

## 可加強但不得偽稱已執行的組合觀察

A14：同一次真drag前後全量 assembly-read 對所有binding/material mapping。A17：明選v2並preview/cancel的同一UI案例一次核對World/history/dirty；取消的起點應是已選草稿，不能錯把撤銷草稿選版當契約。A19：規則/綁定各自UI刪除與改綁逐次dirty快照。A18：同一兩binding+draft archive的所有座標精確 equality。既有 20261004 acceptance index 已明示前三者/位置限制，且把 A17/A18 整合 oracle列為可加強、非新增必要要求；本次保留此區別，不把未做的單一大case說成已做，也不擴張工作範圍。
