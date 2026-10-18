【Codex】第 1 段：全量非瀏覽器驗證結果（留言草稿）

測試 SHA：`e64aa6359d600f43313ec9d7ba1112c465b6a40c`（`architecture/geo261-integration-20261016`）。實際執行 `ulimit -s 16384; python3 -u tests/run_all.py --build`（使用者原命令不含 `-u`；`-u` 僅關閉輸出緩衝），外層 exit `1`。214 個登錄 suite 與 214 個執行紀錄、214 個終端摘要逐一核對；這不代表逾時 suite 內的所有測試已跑完。

GitHub API（api.github.com）目前仍被代理拒絕，尚未取得 PR #288 正文最上方的目前狀態／驗證矩陣，本草稿尚未張貼；Git fetch 可用。後續證據分支的提交 SHA 不代表本輪測試來源 SHA。

驗證期間 fresh fetch 顯示遠端整合分支已前進 `1987af507c6f387d7986325da6c29b2ec6246944`，新增 memoized guide 的 resolved 回填修正。本輪 checkout 仍固定 e64aa635，結果不能歸到 1987；新提交尚未驗證。

臺北時間：2026-10-18T16:19:06+08:00 至 2026-10-18T18:56:35+08:00；包含建置的整段時間 9449 秒。runner 原始總耗時 9308.7 秒；表列各 suite 耗時四捨五入後相加 9308.6 秒（0.1 秒差異來自逐列四捨五入）。JSON 同時保留各 unittest runner 的獨立耗時。

環境：Debian GNU/Linux 13.6（trixie）、Linux 6.18.55 x86_64；GCC 14.2.0；Python 3.12.14；Node v24.19.0／npm 11.9.0；Google Chrome 155.0.8059.84、Chromium 154.0.8037.57；stack 16,384 KiB。Chrome 已安裝，這一段尚未執行 browser jobs。

| Suite 結果 | 數量 |
|---|---:|
| 通過 | 197 |
| 失敗 | 12 |
| 略過 | 1 |
| 逾時／未完整 | 3 |
| setUpClass 錯誤／未執行 | 1 |

以下分開列出計量單位；不把 C 檢查點、場景、node tests 與 canvas 斷言相加冒稱為同一種 test。Runner fail 欄保留原計數定義，可能包含 setUpClass 阻擋的未執行方法，詳見下方獨立說明。

| 有完整收據的單位 | Suites | 總數 | Pass | Runner fail | Skip |
|---|---:|---:|---:|---:|---:|
| C 檢查點 | 1 | 432 | 432 | 0 | 0 |
| 場景 | 1 | 157 | 157 | 0 | 0 |
| test | 176 | 2651 | 2611 | 39 | 1 |
| unittest | 1 | 11 | 11 | 0 | 0 |
| node test | 25 | 432 | 432 | 0 | 0 |
| 斷言 | 1 | 408 | 408 | 0 | 0 |

另外 6 個 suite 僅判定 exit code，不提供 test 級數量。`mutation:check` 的 63 stale／1 invalid／3 retired 是 ledger 狀態，不是單項 assertion 統計。

`py:test_model_update`：1200 秒期限後被終止，登錄 26 個 test，未取得完整 suite 結果。runner 的 synthetic failure 只作逾時標記；partial log 進度點不計入通過數。原始 note：`逾時（1200 秒）被終止，已終止整棵行程樹（killpg SIGKILL）（1200.1 秒後收完）；日誌 /tmp/geometry-tests/run_all-logs/py_test_model_update.log`。
`py:test_product_architecture`：實際執行 0 個方法、1 個 error 事件、18 個方法因 setUpClass 錯誤未執行。runner 把這些阻擋計入 fail；不能寫成 18 個實際 assertion failure。
`py:test_scenario_verify`：37 個方法已完成，36 pass／1 failed method；同一方法的 descriptor=1、2 各有 1 個 subTest error，合計 2 個 error 事件。這是內層 worker budget 錯誤，與外層 suite 1200 秒逾時分開記錄。
`py:test_space_modeling`：1200 秒期限後被終止，登錄 40 個 test，未取得完整 suite 結果。runner 的 synthetic failure 只作逾時標記；partial log 進度點不計入通過數。原始 note：`逾時（1200 秒）被終止，已終止整棵行程樹（killpg SIGKILL）（1200.1 秒後收完）；日誌 /tmp/geometry-tests/run_all-logs/py_test_space_modeling.log`。
`node:tests-js`：900 秒期限後被終止，登錄 730 個 node test，未取得完整 suite 結果。runner 的 synthetic failure 只作逾時標記；partial log 進度點不計入通過數。原始 note：`逾時（900 秒）被終止，已終止整棵行程樹（killpg SIGKILL）（900.1 秒後收完）；日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log`。
但 `node:tests-js` 的 partial 原文已直接觀測到 3 個具名 `✖` 失敗，不能寫成沒有 failure；沒有完整總摘要／失敗 traceback，實際執行總數及根因仍未知。這些原文在下方另列，不加入完整 suite 的計數總和。
完整 Python JSON 的實際失敗事件：{"error": 6, "failure": 17}；blocked_by_error 共 18 個方法，timeout 另列。

Windows GDI 的具名平台略過仍列未驗，不能視為 GDI 通過。

失敗清單與分類如下；分類依原始輸出、條文及已完成的歷史調查，除上游 1987 待驗提交外，其餘修正目前仍是外部提案。

| Suite | 分類 | 證據與提案 |
|---|---|---|
| `mutation:check` | 預期過時／執行收據失效 | 63 stale 收據不能證明本 SHA；另有 M11 舊錨點 invalid、3 retired。這是 exit-code-only 的 freshness gate，不是 64 個單項測試失敗。M11 對應 0b64623b 的精確孔中心判式；整合最終來源確定後仍需實跑刷新 mutation 收據。 提案：`README.md`。 |
| `py:test_assembly_candidate_impact` | 產品缺陷（e64 基準） | assembly 求值先快取 guide，後續 reference_rebuild 清除 resolved；快取命中未回填。最小實際回應顯示 guide 1/2/3 為 null，原幾何斷言正確。驗證期間上游 1987af507c6f387d7986325da6c29b2ec6246944 已新增 memoized guide resolved 修正，但尚未驗證；不另開重複修正分支。 提案：`03-assembly-guide-cache.md`。 |
| `py:test_geo261_member_reference` | 預期過時（靜態函式形狀） | 6ea2d3b5 的薄 delegate 靜態形狀未承接後續 H 尺寸來源組裝。提案分離既有 H 組裝 helper，保留禁迴圈斷言與全部行為；沒有證據顯示 W 幾何算法回流 H。 提案：`README.md`。 |
| `py:test_geo261_mutation_migration` | 預期過時 | 0b64623b 以精確孔中心判式取代 inside == 4；6bddee15 遷移檔案後保留不存在的 M11 old 錨點。舊錨點在整合 SHA 出現 0 次，不能將 M11 退役或改判 equivalent。 提案：`README.md`。 |
| `py:test_geo261_native_grid_rules` | 產品缺陷（main 既有） | H/W tokenizer 在第 8 欄截掉額外尾欄，既有拒絕條件看不到 :extra。main 的 68ac8a21 已有同一缺陷，整合分支新 native 驗收揭露。main 真 bridge 重現仍未驗。 提案：`04-gridrule-reference-tail.md`。 |
| `py:test_geo261_placement_sources` | 預期過時／負控錨點過時 | 138595e0 加入 canonical DEFINITION、真實消費及候選持有 decoded records，舊 suite 未同步：5 個舊預期、2 個 binding-value 錨點錯誤、1 個被舊 baseline 阻擋的負控。提案逐條對照既有契約，沒有要求產品回退。 提案：`05-placement-sources-definition-contract.md`。 |
| `py:test_geo261_wood_engineering_operations` | 測試寫錯 | 1906eae1 的負控自建立時就把移除 D28 guard 推論成整個 bridge 必須接受，但 I9 未放材終態守門早已存在。實際回應仍以 I9 拒絕，接受斷言應留在合法正控制。 提案：`06-engineering-unplaced-oracle.md`。 |
| `py:test_geo261_wood_finish` | 預期過時（分層負控） | 138595e0 typed version 來源讓單點 mutant 穿過第一道 I52 後仍由 I35 整數要求拒絕；原版 I52 正確。舊負控期待相同診斷並整體接受，未承接第二道守門。 提案：`07-finish-fractional-source-guard.md`。 |
| `py:test_geo261_wood_grid_application` | 測試寫錯（夾具） | child 夾具使用 line:0 指向最小邊界，違反 D19/I25 的 MIN 標準參照。產品依既有條文正確拒絕，兩個案例都在 baseline child:134 先失敗。 提案：`08-wood-grid-child-fixture.md`。 |
| `py:test_guide_panels` | 產品缺陷（導讀文件） | GEO-261 抽取後 locator／說明未同步真正 K/W 來源及組合 World。39 個面板中 14 個受影響，共 29 unresolved（5 個整面板、24 個 callout）；原測試正確。 提案：`09-guide-panel-sources.md`。 |
| `py:test_product_architecture` | 預期過時（固定來源雜湊） | 244 個 exclusion LF pins 中 3 個測試 JS pins 過時，第一筆失配導致 1 次 setUpClass error，18 個方法全未執行。已逐份審查來源歷史與差異；提案只更新 3 個精確 SHA，守門不變。 提案：`10-architecture-exclusion-pins.md`。 |
| `py:test_scenario_verify` | 產品缺陷（整合重構回歸） | c9e84b62 將 native 傳輸搬到 H model_native，但正式 worker 仍重新綁定舊 facade.subprocess，真正 run globals 不受覆寫，容量守門未接上。1 個方法的 descriptor 1/2 產生 2 個 worker budget error；不是外層 suite timeout，也不是應放寬限制的慢測試。 提案：`11-scenario-bounded-transport.md`。 |
| `py:test_section_profile_mutation_check` | 預期過時（ModelError 真定義模組） | 10cbda74 將同一 ModelError 搬到 geometry_app.model_common；舊 facade 是同一 class 的別名，collector 正確保存真 owner。測試 literal 及 SPM38/SPM40 的精確單元素 error_types 未同步；提案不接受雙 owner、不改 collector 或產品 __module__。 提案：`12-modelerror-owner.md`。 |
| `node:tests-js` | 待根因調查 | partial 已觀測 3 個具名失敗，但整組未完成、沒有完整失敗 traceback，不能從登錄或部分 TAP 推算已執行總數；根因另查。 |

Codex 修正分支與 SHA：尚未建立。本段沒有套用任何提案，不存在修後通過或撤回轉紅證據；不得把提案寫成已修。assembly guide 題已有上游 `1987af507c6f387d7986325da6c29b2ec6246944` 待驗，不另開重複修正分支。

<details>
<summary>全部 214 個 suite 結果（每批一行）</summary>

| # | Suite | 狀態 | 單位 | Pass / Fail / Skip | 秒 |
|---:|---|---|---|---|---:|
| 1 | [c:integrity](suite-logs/c_integrity.log) | 通過 | C 檢查點 | 432 / 0 / 0 | 18.7 |
| 2 | [core:run_tests](suite-logs/core_run_tests.log) | 通過 | 場景 | 157 / 0 / 0 | 124.1 |
| 3 | [mutation:check](suite-logs/mutation_check.log) | 失敗 | exit code | 僅 exit code | 1.0 |
| 4 | [py:test_architecture_contract](suite-logs/py_test_architecture_contract.unittest.log) | 通過 | test | 205 / 0 / 0 | 0.9 |
| 5 | [py:test_assembly_candidate_impact](suite-logs/py_test_assembly_candidate_impact.unittest.log) | 失敗 | test | 1 / 3 / 0 | 21.6 |
| 6 | [py:test_assembly_capacity](suite-logs/py_test_assembly_capacity.unittest.log) | 通過 | test | 5 / 0 / 0 | 26.3 |
| 7 | [py:test_assembly_generation](suite-logs/py_test_assembly_generation.unittest.log) | 通過 | test | 22 / 0 / 0 | 84.4 |
| 8 | [py:test_assembly_native_diagnostics](suite-logs/py_test_assembly_native_diagnostics.unittest.log) | 通過 | test | 8 / 0 / 0 | 11.8 |
| 9 | [py:test_assembly_parameter_refs](suite-logs/py_test_assembly_parameter_refs.unittest.log) | 通過 | test | 3 / 0 / 0 | 17.0 |
| 10 | [py:test_assembly_rules](suite-logs/py_test_assembly_rules.unittest.log) | 通過 | test | 36 / 0 / 0 | 65.3 |
| 11 | [py:test_axiom_reader](suite-logs/py_test_axiom_reader.unittest.log) | 通過 | test | 51 / 0 / 0 | 234.1 |
| 12 | [py:test_binaries](suite-logs/py_test_binaries.unittest.log) | 通過 | test | 33 / 0 / 0 | 0.6 |
| 13 | [py:test_bridge_integrity](suite-logs/py_test_bridge_integrity.unittest.log) | 通過 | test | 24 / 0 / 0 | 485.7 |
| 14 | [py:test_cli_args](suite-logs/py_test_cli_args.unittest.log) | 通過 | test | 6 / 0 / 0 | 4.1 |
| 15 | [py:test_datum_contract](suite-logs/py_test_datum_contract.unittest.log) | 通過 | test | 9 / 0 / 0 | 53.7 |
| 16 | [py:test_domain_decoupling_adoption](suite-logs/py_test_domain_decoupling_adoption.unittest.log) | 通過 | test | 15 / 0 / 0 | 0.7 |
| 17 | [py:test_domain_decoupling_compatibility](suite-logs/py_test_domain_decoupling_compatibility.unittest.log) | 通過 | test | 14 / 0 / 0 | 17.7 |
| 18 | [py:test_domain_decoupling_proposal](suite-logs/py_test_domain_decoupling_proposal.unittest.log) | 通過 | test | 29 / 0 / 0 | 0.9 |
| 19 | [py:test_domain_source_pins](suite-logs/py_test_domain_source_pins.unittest.log) | 通過 | test | 16 / 0 / 0 | 1.3 |
| 20 | [py:test_engineering_core](suite-logs/py_test_engineering_core.unittest.log) | 通過 | test | 18 / 0 / 0 | 43.9 |
| 21 | [py:test_engineering_json](suite-logs/py_test_engineering_json.unittest.log) | 通過 | test | 7 / 0 / 0 | 0.7 |
| 22 | [py:test_engineering_model_compatibility](suite-logs/py_test_engineering_model_compatibility.unittest.log) | 通過 | test | 31 / 0 / 0 | 120.4 |
| 23 | [py:test_engineering_model_sources](suite-logs/py_test_engineering_model_sources.unittest.log) | 通過 | test | 4 / 0 / 0 | 54.0 |
| 24 | [py:test_engineering_transport](suite-logs/py_test_engineering_transport.unittest.log) | 通過 | test | 7 / 0 / 0 | 0.4 |
| 25 | [py:test_evidence_link_native](suite-logs/py_test_evidence_link_native.unittest.log) | 通過 | test | 6 / 0 / 0 | 8.8 |
| 26 | [py:test_feedback_store](suite-logs/py_test_feedback_store.unittest.log) | 通過 | test | 11 / 0 / 0 | 0.7 |
| 27 | [py:test_gdi_contract](suite-logs/py_test_gdi_contract.unittest.log) | 略過 | test | 0 / 0 / 1 | 0.4 |
| 28 | [py:test_geo261_application_closure](suite-logs/py_test_geo261_application_closure.unittest.log) | 通過 | test | 14 / 0 / 0 | 35.2 |
| 29 | [py:test_geo261_assembly_definition_authority](suite-logs/py_test_geo261_assembly_definition_authority.unittest.log) | 通過 | test | 15 / 0 / 0 | 8.6 |
| 30 | [py:test_geo261_assembly_graph_product](suite-logs/py_test_geo261_assembly_graph_product.unittest.log) | 通過 | test | 4 / 0 / 0 | 95.5 |
| 31 | [py:test_geo261_assembly_sources](suite-logs/py_test_geo261_assembly_sources.unittest.log) | 通過 | test | 8 / 0 / 0 | 5.2 |
| 32 | [py:test_geo261_candidate_cache](suite-logs/py_test_geo261_candidate_cache.unittest.log) | 通過 | test | 18 / 0 / 0 | 4.5 |
| 33 | [py:test_geo261_candidate_product](suite-logs/py_test_geo261_candidate_product.unittest.log) | 通過 | test | 11 / 0 / 0 | 63.9 |
| 34 | [py:test_geo261_contact_sources](suite-logs/py_test_geo261_contact_sources.unittest.log) | 通過 | test | 12 / 0 / 0 | 6.9 |
| 35 | [py:test_geo261_default_native](suite-logs/py_test_geo261_default_native.unittest.log) | 通過 | test | 8 / 0 / 0 | 55.3 |
| 36 | [py:test_geo261_definition_graph_product](suite-logs/py_test_geo261_definition_graph_product.unittest.log) | 通過 | test | 5 / 0 / 0 | 22.1 |
| 37 | [py:test_geo261_definition_sources](suite-logs/py_test_geo261_definition_sources.unittest.log) | 通過 | test | 7 / 0 / 0 | 4.5 |
| 38 | [py:test_geo261_derived_policy_graph_product](suite-logs/py_test_geo261_derived_policy_graph_product.unittest.log) | 通過 | test | 4 / 0 / 0 | 85.2 |
| 39 | [py:test_geo261_derived_policy_sources](suite-logs/py_test_geo261_derived_policy_sources.unittest.log) | 通過 | test | 14 / 0 / 0 | 6.2 |
| 40 | [py:test_geo261_domain_product](suite-logs/py_test_geo261_domain_product.unittest.log) | 通過 | test | 9 / 0 / 0 | 61.2 |
| 41 | [py:test_geo261_draw_annotation](suite-logs/py_test_geo261_draw_annotation.unittest.log) | 通過 | test | 4 / 0 / 0 | 19.1 |
| 42 | [py:test_geo261_enclosure_definition_authority](suite-logs/py_test_geo261_enclosure_definition_authority.unittest.log) | 通過 | test | 14 / 0 / 0 | 4.3 |
| 43 | [py:test_geo261_enclosure_product](suite-logs/py_test_geo261_enclosure_product.unittest.log) | 通過 | test | 5 / 0 / 0 | 21.0 |
| 44 | [py:test_geo261_enclosure_sources](suite-logs/py_test_geo261_enclosure_sources.unittest.log) | 通過 | test | 13 / 0 / 0 | 5.8 |
| 45 | [py:test_geo261_engineering_parameter_authority](suite-logs/py_test_geo261_engineering_parameter_authority.unittest.log) | 通過 | test | 17 / 0 / 0 | 52.3 |
| 46 | [py:test_geo261_engineering_sources](suite-logs/py_test_geo261_engineering_sources.unittest.log) | 通過 | test | 18 / 0 / 0 | 22.2 |
| 47 | [py:test_geo261_finish_definition_authority](suite-logs/py_test_geo261_finish_definition_authority.unittest.log) | 通過 | test | 14 / 0 / 0 | 7.4 |
| 48 | [py:test_geo261_finish_sources](suite-logs/py_test_geo261_finish_sources.unittest.log) | 通過 | test | 8 / 0 / 0 | 4.9 |
| 49 | [py:test_geo261_graph_product](suite-logs/py_test_geo261_graph_product.unittest.log) | 通過 | test | 5 / 0 / 0 | 34.9 |
| 50 | [py:test_geo261_grid_definition_authority](suite-logs/py_test_geo261_grid_definition_authority.unittest.log) | 通過 | test | 13 / 0 / 0 | 4.8 |
| 51 | [py:test_geo261_grid_definition_codec](suite-logs/py_test_geo261_grid_definition_codec.unittest.log) | 通過 | test | 13 / 0 / 0 | 5.7 |
| 52 | [py:test_geo261_grid_definitions_product](suite-logs/py_test_geo261_grid_definitions_product.unittest.log) | 通過 | test | 4 / 0 / 0 | 30.0 |
| 53 | [py:test_geo261_grid_sources](suite-logs/py_test_geo261_grid_sources.unittest.log) | 通過 | test | 11 / 0 / 0 | 6.4 |
| 54 | [py:test_geo261_guides_product](suite-logs/py_test_geo261_guides_product.unittest.log) | 通過 | test | 2 / 0 / 0 | 27.5 |
| 55 | [py:test_geo261_host_authority](suite-logs/py_test_geo261_host_authority.unittest.log) | 通過 | test | 18 / 0 / 0 | 55.6 |
| 56 | [py:test_geo261_host_candidate](suite-logs/py_test_geo261_host_candidate.unittest.log) | 通過 | test | 17 / 0 / 0 | 4.6 |
| 57 | [py:test_geo261_host_facts_authority](suite-logs/py_test_geo261_host_facts_authority.unittest.log) | 通過 | test | 17 / 0 / 0 | 28.0 |
| 58 | [py:test_geo261_host_history](suite-logs/py_test_geo261_host_history.unittest.log) | 通過 | test | 13 / 0 / 0 | 32.5 |
| 59 | [py:test_geo261_host_placement_definition](suite-logs/py_test_geo261_host_placement_definition.unittest.log) | 通過 | test | 7 / 0 / 0 | 11.4 |
| 60 | [py:test_geo261_linear_definition_graph_product](suite-logs/py_test_geo261_linear_definition_graph_product.unittest.log) | 通過 | test | 8 / 0 / 0 | 66.3 |
| 61 | [py:test_geo261_linear_definition_sources](suite-logs/py_test_geo261_linear_definition_sources.unittest.log) | 通過 | test | 15 / 0 / 0 | 3.9 |
| 62 | [py:test_geo261_member_reference](suite-logs/py_test_geo261_member_reference.unittest.log) | 失敗 | test | 10 / 1 / 0 | 22.8 |
| 63 | [py:test_geo261_model_semantics_authority](suite-logs/py_test_geo261_model_semantics_authority.unittest.log) | 通過 | test | 12 / 0 / 0 | 25.0 |
| 64 | [py:test_geo261_model_sources](suite-logs/py_test_geo261_model_sources.unittest.log) | 通過 | test | 12 / 0 / 0 | 58.6 |
| 65 | [py:test_geo261_model_vertex_ledger](suite-logs/py_test_geo261_model_vertex_ledger.unittest.log) | 通過 | test | 7 / 0 / 0 | 46.8 |
| 66 | [py:test_geo261_mutation_migration](suite-logs/py_test_geo261_mutation_migration.unittest.log) | 失敗 | test | 14 / 1 / 0 | 3.5 |
| 67 | [py:test_geo261_native_candidate](suite-logs/py_test_geo261_native_candidate.unittest.log) | 通過 | test | 17 / 0 / 0 | 4.5 |
| 68 | [py:test_geo261_native_datums](suite-logs/py_test_geo261_native_datums.unittest.log) | 通過 | test | 7 / 0 / 0 | 26.0 |
| 69 | [py:test_geo261_native_document](suite-logs/py_test_geo261_native_document.unittest.log) | 通過 | test | 10 / 0 / 0 | 4.2 |
| 70 | [py:test_geo261_native_enclosures](suite-logs/py_test_geo261_native_enclosures.unittest.log) | 通過 | test | 19 / 0 / 0 | 4.8 |
| 71 | [py:test_geo261_native_entrypoints](suite-logs/py_test_geo261_native_entrypoints.unittest.log) | 通過 | test | 3 / 0 / 0 | 21.7 |
| 72 | [py:test_geo261_native_geometry](suite-logs/py_test_geo261_native_geometry.unittest.log) | 通過 | test | 7 / 0 / 0 | 22.9 |
| 73 | [py:test_geo261_native_grid](suite-logs/py_test_geo261_native_grid.unittest.log) | 通過 | test | 8 / 0 / 0 | 23.7 |
| 74 | [py:test_geo261_native_grid_product](suite-logs/py_test_geo261_native_grid_product.unittest.log) | 通過 | test | 5 / 0 / 0 | 45.1 |
| 75 | [py:test_geo261_native_grid_rules](suite-logs/py_test_geo261_native_grid_rules.unittest.log) | 失敗 | test | 8 / 1 / 0 | 4.9 |
| 76 | [py:test_geo261_native_grid_store](suite-logs/py_test_geo261_native_grid_store.unittest.log) | 通過 | test | 18 / 0 / 0 | 6.2 |
| 77 | [py:test_geo261_native_guides](suite-logs/py_test_geo261_native_guides.unittest.log) | 通過 | test | 13 / 0 / 0 | 5.2 |
| 78 | [py:test_geo261_native_kernel](suite-logs/py_test_geo261_native_kernel.unittest.log) | 通過 | test | 13 / 0 / 0 | 31.1 |
| 79 | [py:test_geo261_native_linear](suite-logs/py_test_geo261_native_linear.unittest.log) | 通過 | test | 6 / 0 / 0 | 36.8 |
| 80 | [py:test_geo261_native_parameters](suite-logs/py_test_geo261_native_parameters.unittest.log) | 通過 | test | 9 / 0 / 0 | 25.5 |
| 81 | [py:test_geo261_native_placements](suite-logs/py_test_geo261_native_placements.unittest.log) | 通過 | test | 12 / 0 / 0 | 7.7 |
| 82 | [py:test_geo261_native_regions](suite-logs/py_test_geo261_native_regions.unittest.log) | 通過 | test | 13 / 0 / 0 | 5.2 |
| 83 | [py:test_geo261_native_sources](suite-logs/py_test_geo261_native_sources.unittest.log) | 通過 | test | 9 / 0 / 0 | 23.0 |
| 84 | [py:test_geo261_native_versions](suite-logs/py_test_geo261_native_versions.unittest.log) | 通過 | test | 14 / 0 / 0 | 4.7 |
| 85 | [py:test_geo261_panel_native](suite-logs/py_test_geo261_panel_native.unittest.log) | 通過 | test | 10 / 0 / 0 | 5.1 |
| 86 | [py:test_geo261_parameter_definition_sources](suite-logs/py_test_geo261_parameter_definition_sources.unittest.log) | 通過 | test | 20 / 0 / 0 | 3.6 |
| 87 | [py:test_geo261_parameter_sources](suite-logs/py_test_geo261_parameter_sources.unittest.log) | 通過 | test | 12 / 0 / 0 | 50.5 |
| 88 | [py:test_geo261_placement_definition](suite-logs/py_test_geo261_placement_definition.unittest.log) | 通過 | test | 15 / 0 / 0 | 4.2 |
| 89 | [py:test_geo261_placement_sources](suite-logs/py_test_geo261_placement_sources.unittest.log) | 失敗 | test | 13 / 8 / 0 | 5.1 |
| 90 | [py:test_geo261_region_edges](suite-logs/py_test_geo261_region_edges.unittest.log) | 通過 | test | 8 / 0 / 0 | 42.2 |
| 91 | [py:test_geo261_region_key_sources](suite-logs/py_test_geo261_region_key_sources.unittest.log) | 通過 | test | 15 / 0 / 0 | 3.1 |
| 92 | [py:test_geo261_regions_product](suite-logs/py_test_geo261_regions_product.unittest.log) | 通過 | test | 2 / 0 / 0 | 19.2 |
| 93 | [py:test_geo261_section_profile_authority](suite-logs/py_test_geo261_section_profile_authority.unittest.log) | 通過 | test | 15 / 0 / 0 | 8.0 |
| 94 | [py:test_geo261_section_profile_sources](suite-logs/py_test_geo261_section_profile_sources.unittest.log) | 通過 | test | 9 / 0 / 0 | 6.5 |
| 95 | [py:test_geo261_source_context](suite-logs/py_test_geo261_source_context.unittest.log) | 通過 | test | 8 / 0 / 0 | 4.8 |
| 96 | [py:test_geo261_source_describe](suite-logs/py_test_geo261_source_describe.unittest.log) | 通過 | test | 7 / 0 / 0 | 4.3 |
| 97 | [py:test_geo261_staged_candidate_graph](suite-logs/py_test_geo261_staged_candidate_graph.unittest.log) | 通過 | test | 7 / 0 / 0 | 42.0 |
| 98 | [py:test_geo261_version_activation](suite-logs/py_test_geo261_version_activation.unittest.log) | 通過 | test | 10 / 0 / 0 | 50.6 |
| 99 | [py:test_geo261_version_field_sources](suite-logs/py_test_geo261_version_field_sources.unittest.log) | 通過 | test | 19 / 0 / 0 | 34.9 |
| 100 | [py:test_geo261_wood_assembly](suite-logs/py_test_geo261_wood_assembly.unittest.log) | 通過 | test | 13 / 0 / 0 | 20.1 |
| 101 | [py:test_geo261_wood_contact_world](suite-logs/py_test_geo261_wood_contact_world.unittest.log) | 通過 | test | 10 / 0 / 0 | 30.2 |
| 102 | [py:test_geo261_wood_contacts](suite-logs/py_test_geo261_wood_contacts.unittest.log) | 通過 | test | 10 / 0 / 0 | 6.8 |
| 103 | [py:test_geo261_wood_contacts_product](suite-logs/py_test_geo261_wood_contacts_product.unittest.log) | 通過 | test | 1 / 0 / 0 | 29.4 |
| 104 | [py:test_geo261_wood_derived_placement](suite-logs/py_test_geo261_wood_derived_placement.unittest.log) | 通過 | test | 14 / 0 / 0 | 26.1 |
| 105 | [py:test_geo261_wood_engineering](suite-logs/py_test_geo261_wood_engineering.unittest.log) | 通過 | test | 12 / 0 / 0 | 25.1 |
| 106 | [py:test_geo261_wood_engineering_operations](suite-logs/py_test_geo261_wood_engineering_operations.unittest.log) | 失敗 | test | 14 / 1 / 0 | 16.1 |
| 107 | [py:test_geo261_wood_finish](suite-logs/py_test_geo261_wood_finish.unittest.log) | 失敗 | test | 11 / 1 / 0 | 21.6 |
| 108 | [py:test_geo261_wood_grid_application](suite-logs/py_test_geo261_wood_grid_application.unittest.log) | 失敗 | test | 9 / 2 / 0 | 23.6 |
| 109 | [py:test_geo261_wood_grid_cells](suite-logs/py_test_geo261_wood_grid_cells.unittest.log) | 通過 | test | 13 / 0 / 0 | 20.7 |
| 110 | [py:test_geo261_wood_grid_engineering](suite-logs/py_test_geo261_wood_grid_engineering.unittest.log) | 通過 | test | 14 / 0 / 0 | 21.2 |
| 111 | [py:test_geo261_wood_member_declaration](suite-logs/py_test_geo261_wood_member_declaration.unittest.log) | 通過 | test | 9 / 0 / 0 | 17.3 |
| 112 | [py:test_geo261_wood_members](suite-logs/py_test_geo261_wood_members.unittest.log) | 通過 | test | 10 / 0 / 0 | 4.6 |
| 113 | [py:test_geo261_wood_product](suite-logs/py_test_geo261_wood_product.unittest.log) | 通過 | test | 2 / 0 / 0 | 24.9 |
| 114 | [py:test_geo261_wood_report_policy](suite-logs/py_test_geo261_wood_report_policy.unittest.log) | 通過 | test | 8 / 0 / 0 | 17.6 |
| 115 | [py:test_geo261_wood_section_profile](suite-logs/py_test_geo261_wood_section_profile.unittest.log) | 通過 | test | 12 / 0 / 0 | 21.1 |
| 116 | [py:test_geo261_wood_supports](suite-logs/py_test_geo261_wood_supports.unittest.log) | 通過 | test | 13 / 0 / 0 | 7.5 |
| 117 | [py:test_geo261_wood_supports_product](suite-logs/py_test_geo261_wood_supports_product.unittest.log) | 通過 | test | 2 / 0 / 0 | 49.4 |
| 118 | [py:test_geo261_wood_world_validation](suite-logs/py_test_geo261_wood_world_validation.unittest.log) | 通過 | test | 14 / 0 / 0 | 26.3 |
| 119 | [py:test_geometry_host_native](suite-logs/py_test_geometry_host_native.unittest.log) | 通過 | test | 22 / 0 / 0 | 2.6 |
| 120 | [py:test_geometry_host_sources](suite-logs/py_test_geometry_host_sources.unittest.log) | 通過 | test | 29 / 0 / 0 | 3.3 |
| 121 | [py:test_geometry_host_world](suite-logs/py_test_geometry_host_world.unittest.log) | 通過 | test | 8 / 0 / 0 | 0.5 |
| 122 | [py:test_geometry_kernel_compatibility](suite-logs/py_test_geometry_kernel_compatibility.unittest.log) | 通過 | test | 1 / 0 / 0 | 0.6 |
| 123 | [py:test_geometry_kernel_geometry](suite-logs/py_test_geometry_kernel_geometry.unittest.log) | 通過 | test | 20 / 0 / 0 | 0.7 |
| 124 | [py:test_geometry_kernel_graph](suite-logs/py_test_geometry_kernel_graph.unittest.log) | 通過 | test | 30 / 0 / 0 | 0.5 |
| 125 | [py:test_geometry_kernel_isolation](suite-logs/py_test_geometry_kernel_isolation.unittest.log) | 通過 | test | 2 / 0 / 0 | 3.8 |
| 126 | [py:test_geometry_kernel_runtime](suite-logs/py_test_geometry_kernel_runtime.unittest.log) | 通過 | test | 8 / 0 / 0 | 3.4 |
| 127 | [py:test_geometry_kernel_session](suite-logs/py_test_geometry_kernel_session.unittest.log) | 通過 | test | 5 / 0 / 0 | 0.8 |
| 128 | [py:test_geometry_kernel_transactions](suite-logs/py_test_geometry_kernel_transactions.unittest.log) | 通過 | test | 31 / 0 / 0 | 0.5 |
| 129 | [py:test_geometry_source_runtime](suite-logs/py_test_geometry_source_runtime.unittest.log) | 通過 | test | 10 / 0 / 0 | 3.6 |
| 130 | [py:test_grid_inspector_contract](suite-logs/py_test_grid_inspector_contract.unittest.log) | 通過 | test | 3 / 0 / 0 | 19.6 |
| 131 | [py:test_grid_subdivision_oracle](suite-logs/py_test_grid_subdivision_oracle.unittest.log) | 通過 | test | 41 / 0 / 0 | 112.6 |
| 132 | [py:test_grid_system_contract](suite-logs/py_test_grid_system_contract.unittest.log) | 通過 | test | 15 / 0 / 0 | 40.0 |
| 133 | [py:test_grid_trial_contract](suite-logs/py_test_grid_trial_contract.unittest.log) | 通過 | test | 5 / 0 / 0 | 7.2 |
| 134 | [py:test_guide_panels](suite-logs/py_test_guide_panels.unittest.log) | 失敗 | test | 0 / 1 / 0 | 0.5 |
| 135 | [py:test_infinite_grid_contract](suite-logs/py_test_infinite_grid_contract.unittest.log) | 通過 | test | 25 / 0 / 0 | 79.6 |
| 136 | [py:test_local_launcher](suite-logs/py_test_local_launcher.unittest.log) | 通過 | test | 17 / 0 / 0 | 5.2 |
| 137 | [py:test_model_update](suite-logs/py_test_model_update.unittest.log) | 逾時／未完整 | test | 無完整結果 | 1200.1 |
| 138 | [py:test_modeling_degenerate](suite-logs/py_test_modeling_degenerate.unittest.log) | 通過 | test | 24 / 0 / 0 | 15.4 |
| 139 | [py:test_modeling_runtime](suite-logs/py_test_modeling_runtime.unittest.log) | 通過 | test | 46 / 0 / 0 | 62.4 |
| 140 | [py:test_modeling_transport](suite-logs/py_test_modeling_transport.unittest.log) | 通過 | test | 3 / 0 / 0 | 12.2 |
| 141 | [py:test_mutation_freshness](suite-logs/py_test_mutation_freshness.unittest.log) | 通過 | test | 32 / 0 / 0 | 1.0 |
| 142 | [py:test_panel_fill_finish_surface](suite-logs/py_test_panel_fill_finish_surface.unittest.log) | 通過 | test | 22 / 0 / 0 | 114.1 |
| 143 | [py:test_panel_fill_host](suite-logs/py_test_panel_fill_host.unittest.log) | 通過 | test | 32 / 0 / 0 | 121.9 |
| 144 | [py:test_panel_fill_layout](suite-logs/py_test_panel_fill_layout.unittest.log) | 通過 | test | 18 / 0 / 0 | 66.2 |
| 145 | [py:test_panel_fill_support](suite-logs/py_test_panel_fill_support.unittest.log) | 通過 | test | 20 / 0 / 0 | 114.0 |
| 146 | [py:test_parameter_netzero](suite-logs/py_test_parameter_netzero.unittest.log) | 通過 | test | 4 / 0 / 0 | 8.3 |
| 147 | [py:test_parameter_retirement_scope](suite-logs/py_test_parameter_retirement_scope.unittest.log) | 通過 | test | 6 / 0 / 0 | 11.0 |
| 148 | [py:test_parameters_candidate_value_history](suite-logs/py_test_parameters_candidate_value_history.unittest.log) | 通過 | test | 12 / 0 / 0 | 22.9 |
| 149 | [py:test_parameters_core](suite-logs/py_test_parameters_core.unittest.log) | 通過 | test | 40 / 0 / 0 | 95.0 |
| 150 | [py:test_parameters_deleted_unbind](suite-logs/py_test_parameters_deleted_unbind.unittest.log) | 通過 | test | 14 / 0 / 0 | 23.5 |
| 151 | [py:test_parameters_final_candidate](suite-logs/py_test_parameters_final_candidate.unittest.log) | 通過 | test | 4 / 0 / 0 | 7.3 |
| 152 | [py:test_parameters_unbind_scope](suite-logs/py_test_parameters_unbind_scope.unittest.log) | 通過 | test | 8 / 0 / 0 | 14.2 |
| 153 | [py:test_parameters_upstream_unbind](suite-logs/py_test_parameters_upstream_unbind.unittest.log) | 通過 | test | 12 / 0 / 0 | 21.8 |
| 154 | [py:test_product_architecture](suite-logs/py_test_product_architecture.unittest.log) | setUpClass 錯誤／未執行 | test | 0 / 18 / 0 | 0.6 |
| 155 | [py:test_recorded_api_receipts](suite-logs/py_test_recorded_api_receipts.unittest.log) | 通過 | test | 12 / 0 / 0 | 0.6 |
| 156 | [py:test_rectangular_bridge](suite-logs/py_test_rectangular_bridge.unittest.log) | 通過 | test | 2 / 0 / 0 | 1.8 |
| 157 | [py:test_rectangular_python](suite-logs/py_test_rectangular_python.unittest.log) | 通過 | test | 8 / 0 / 0 | 3.2 |
| 158 | [py:test_rectangular_template](suite-logs/py_test_rectangular_template.unittest.log) | 通過 | unittest | 11 / 0 / 0 | 0.8 |
| 159 | [py:test_reference_contract](suite-logs/py_test_reference_contract.unittest.log) | 通過 | test | 51 / 0 / 0 | 167.7 |
| 160 | [py:test_release_gate](suite-logs/py_test_release_gate.unittest.log) | 通過 | test | 21 / 0 / 0 | 0.8 |
| 161 | [py:test_rule_case_catalog](suite-logs/py_test_rule_case_catalog.unittest.log) | 通過 | test | 14 / 0 / 0 | 10.0 |
| 162 | [py:test_rule_case_definition](suite-logs/py_test_rule_case_definition.unittest.log) | 通過 | test | 27 / 0 / 0 | 0.6 |
| 163 | [py:test_rule_case_executor](suite-logs/py_test_rule_case_executor.unittest.log) | 通過 | test | 40 / 0 / 0 | 22.4 |
| 164 | [py:test_rule_case_host](suite-logs/py_test_rule_case_host.unittest.log) | 通過 | test | 13 / 0 / 0 | 3.5 |
| 165 | [py:test_rule_case_request](suite-logs/py_test_rule_case_request.unittest.log) | 通過 | test | 5 / 0 / 0 | 5.8 |
| 166 | [py:test_rule_case_workbench_http](suite-logs/py_test_rule_case_workbench_http.unittest.log) | 通過 | test | 19 / 0 / 0 | 101.6 |
| 167 | [py:test_runtime_version](suite-logs/py_test_runtime_version.unittest.log) | 通過 | test | 31 / 0 / 0 | 1.0 |
| 168 | [py:test_scenario_verify](suite-logs/py_test_scenario_verify.unittest.log) | 失敗 | test | 36 / 1 / 0 | 462.7 |
| 169 | [py:test_scene_import](suite-logs/py_test_scene_import.unittest.log) | 通過 | test | 10 / 0 / 0 | 46.8 |
| 170 | [py:test_section_profile_modeling](suite-logs/py_test_section_profile_modeling.unittest.log) | 通過 | test | 20 / 0 / 0 | 147.1 |
| 171 | [py:test_section_profile_mutation_check](suite-logs/py_test_section_profile_mutation_check.unittest.log) | 失敗 | test | 28 / 1 / 0 | 1.7 |
| 172 | [py:test_section_profile_native](suite-logs/py_test_section_profile_native.unittest.log) | 通過 | test | 28 / 0 / 0 | 131.6 |
| 173 | [py:test_serve](suite-logs/py_test_serve.unittest.log) | 通過 | test | 51 / 0 / 0 | 78.7 |
| 174 | [py:test_source_inspector](suite-logs/py_test_source_inspector.unittest.log) | 通過 | test | 18 / 0 / 0 | 40.1 |
| 175 | [py:test_source_inspector_transport](suite-logs/py_test_source_inspector_transport.unittest.log) | 通過 | test | 2 / 0 / 0 | 0.5 |
| 176 | [py:test_space_modeling](suite-logs/py_test_space_modeling.unittest.log) | 逾時／未完整 | test | 無完整結果 | 1200.1 |
| 177 | [py:test_subgrid_contract](suite-logs/py_test_subgrid_contract.unittest.log) | 通過 | test | 31 / 0 / 0 | 79.8 |
| 178 | [py:test_timber_support_projection](suite-logs/py_test_timber_support_projection.unittest.log) | 通過 | test | 13 / 0 / 0 | 56.1 |
| 179 | [py:test_unittest_runner](suite-logs/py_test_unittest_runner.unittest.log) | 通過 | test | 1 / 0 / 0 | 4.3 |
| 180 | [py:test_wait_trace](suite-logs/py_test_wait_trace.unittest.log) | 通過 | test | 20 / 0 / 0 | 5.6 |
| 181 | [py:test_witness_diagnostics](suite-logs/py_test_witness_diagnostics.unittest.log) | 通過 | test | 2 / 0 / 0 | 0.4 |
| 182 | [py:test_witness_marks](suite-logs/py_test_witness_marks.unittest.log) | 通過 | test | 6 / 0 / 0 | 0.5 |
| 183 | [node:tests-js](suite-logs/node_tests-js.log) | 逾時／未完整 | node test | 無完整結果；partial 已見 3 具名失敗 | 900.1 |
| 184 | [node:model_viewer](suite-logs/node_model_viewer.log) | 通過 | exit code | 僅 exit code | 0.2 |
| 185 | [node:polydraft](suite-logs/node_polydraft.log) | 通過 | node test | 75 / 0 / 0 | 123.3 |
| 186 | [node:canvas_direct](suite-logs/node_canvas_direct.log) | 通過 | 斷言 | 408 / 0 / 0 | 50.6 |
| 187 | [node:document_format](suite-logs/node_document_format.log) | 通過 | exit code | 僅 exit code | 0.1 |
| 188 | [node:document_cases](suite-logs/node_document_cases.log) | 通過 | exit code | 僅 exit code | 1.2 |
| 189 | [node:cdp_navigation](suite-logs/node_cdp_navigation.log) | 通過 | exit code | 僅 exit code | 0.1 |
| 190 | [node:cdp_confirmation_gate](suite-logs/node_cdp_confirmation_gate.log) | 通過 | exit code | 僅 exit code | 0.1 |
| 191 | [node:draw_annotation](suite-logs/node_draw_annotation.log) | 通過 | node test | 7 / 0 / 0 | 0.2 |
| 192 | [node:woodworking_frontend](suite-logs/node_woodworking_frontend.log) | 通過 | node test | 17 / 0 / 0 | 0.2 |
| 193 | [node:grid_inspector_command](suite-logs/node_grid_inspector_command.log) | 通過 | node test | 9 / 0 / 0 | 0.1 |
| 194 | [node:grid_lesson_control_ownership](suite-logs/node_grid_lesson_control_ownership.log) | 通過 | node test | 13 / 0 / 0 | 0.2 |
| 195 | [node:parameter_confirmation_settlement](suite-logs/node_parameter_confirmation_settlement.log) | 通過 | node test | 16 / 0 / 0 | 0.2 |
| 196 | [node:face_reference_settlement](suite-logs/node_face_reference_settlement.log) | 通過 | node test | 18 / 0 / 0 | 0.2 |
| 197 | [node:face_projection_lifecycle](suite-logs/node_face_projection_lifecycle.log) | 通過 | node test | 14 / 0 / 0 | 0.2 |
| 198 | [node:workspace_shell_history](suite-logs/node_workspace_shell_history.log) | 通過 | node test | 28 / 0 / 0 | 0.2 |
| 199 | [node:feedback_events](suite-logs/node_feedback_events.log) | 通過 | node test | 41 / 0 / 0 | 0.2 |
| 200 | [node:space_test_floor](suite-logs/node_space_test_floor.log) | 通過 | node test | 10 / 0 / 0 | 0.2 |
| 201 | [node:history_operation](suite-logs/node_history_operation.log) | 通過 | node test | 4 / 0 / 0 | 0.1 |
| 202 | [node:context_operations](suite-logs/node_context_operations.log) | 通過 | node test | 12 / 0 / 0 | 0.1 |
| 203 | [node:cdp_evaluation](suite-logs/node_cdp_evaluation.log) | 通過 | node test | 9 / 0 / 0 | 0.1 |
| 204 | [node:cdp_settle](suite-logs/node_cdp_settle.log) | 通過 | node test | 10 / 0 / 0 | 0.1 |
| 205 | [node:cdp_card_position](suite-logs/node_cdp_card_position.log) | 通過 | node test | 21 / 0 / 0 | 0.3 |
| 206 | [node:background_grid_viewport](suite-logs/node_background_grid_viewport.log) | 通過 | node test | 9 / 0 / 0 | 0.2 |
| 207 | [node:anchor_band_clip](suite-logs/node_anchor_band_clip.log) | 通過 | node test | 14 / 0 / 0 | 0.2 |
| 208 | [node:hover_pick_scheduler](suite-logs/node_hover_pick_scheduler.log) | 通過 | node test | 19 / 0 / 0 | 0.2 |
| 209 | [node:face_paint_scheduler](suite-logs/node_face_paint_scheduler.log) | 通過 | node test | 7 / 0 / 0 | 0.1 |
| 210 | [node:room_outline_worker](suite-logs/node_room_outline_worker.log) | 通過 | node test | 6 / 0 / 0 | 0.2 |
| 211 | [node:room_outline_closeout](suite-logs/node_room_outline_closeout.log) | 通過 | node test | 24 / 0 / 0 | 0.3 |
| 212 | [node:evidence_links](suite-logs/node_evidence_links.log) | 通過 | node test | 29 / 0 / 0 | 0.2 |
| 213 | [node:evidence_project_store](suite-logs/node_evidence_project_store.log) | 通過 | node test | 7 / 0 / 0 | 0.3 |
| 214 | [node:grid_definition_diagram](suite-logs/node_grid_definition_diagram.log) | 通過 | node test | 13 / 0 / 0 | 0.2 |

</details>

<details>
<summary>mutation:check：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/mutation_check.log)

```text
結果檔 /workspace/geometry-axiom/tests/mutants_results.json
變異表 67 筆,紀錄 67 筆
殺死 killed 0 / 崩潰 crashed 0 / 存活 survived 0 / 等價 equivalent 0 / 無效 invalid 1 / 過期 stale 63 / 受阻 blocked 0 / 退役 retired 3
  INVALID M11  I5：孔罩住矩形判定:inside==4 改 inside==0(罩住反而放行)  <- 錨點在 geometry-core/kernel/geometry.c 出現 0 次(需要 1)
```

</details>

<details>
<summary>py:test_assembly_candidate_impact：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_assembly_candidate_impact.unittest.log)

```text
ERROR: test_first_hop_external_and_unchanged_geometry_are_shown_before_confirm (test_assembly_candidate_impact.CandidateImpact.test_first_hop_external_and_unchanged_geometry_are_shown_before_confirm)
TypeError: 'NoneType' object is not subscriptable
ERROR: test_generation_creation_and_removal_have_explicit_null_geometry (test_assembly_candidate_impact.CandidateImpact.test_generation_creation_and_removal_have_explicit_null_geometry)
TypeError: 'NoneType' object is not subscriptable
ERROR: test_multi_hop_external_timber_guide_timber_closure_matches_candidate (test_assembly_candidate_impact.CandidateImpact.test_multi_hop_external_timber_guide_timber_closure_matches_candidate)
TypeError: 'NoneType' object is not subscriptable
Ran 4 tests in 20.738s
FAILED (errors=3)
```

</details>

<details>
<summary>py:test_geo261_member_reference：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_member_reference.unittest.log)

```text
FAIL: test_actual_reference_and_main_consumers_delegate_the_policy (test_geo261_member_reference.MemberReferenceBoundary.test_actual_reference_and_main_consumers_delegate_the_policy)
AssertionError: Regex matched: 'for(' matches '\\b(?:for|while)\\s*\\(' in '\n    if(!ctx->use_current_values&&!app_assembly_saved_dimensions(ctx->world,ctx->world->wood.timbers[i].id)&&ctx->wanted[i]){\n        Timber *member=&ctx->world->wood.timbers[i];bool owned;\n        if(!reference_member_owned(ctx,member->id,&owned))return false;\n        if(owned){\n            GeoCoord width,depth;\n            if(!wood_assembly_sources_owned_dimensions(ctx->assembly_sources,member->id,&width,&depth))return false;\n            member->size_a=width;member->size_b=depth;\n        }else{\n            WoodEngineeringContext engineering=app_eng_context(ctx->world);\n            wood_engineering_sources_bind(ctx->engineering_sources,&engineering);\n            for(int field=0;field<2;++field){EngTarget target={1,member->id,0,field};\n                const EngBinding *binding=wood_eng_binding(&engineering,&target);GeoCoord dimension;\n                if(binding){if(!wood_eng_effective(&engineering,binding,&dimension,NULL,0))return false;}\n                else if(!wood_definition_sources_dimension(ctx->definition_sources,member->id,field!=0,&dimension))return false;\n                if(field)member->size_b=dimension;else member->size_a=dimension;\n            }\n        }\n    }\n    AppMemberReferenceContext c={0};c.evaluation=ctx;c.world=ctx->world;WoodMemberReferenceContext context=app_member_reference_context(&c);bool place=false;if(!wood_member_reference_compute(&context,i,&place))return false;return !place||reference_place_geometry(ctx,ctx->world,i);\n'
Ran 11 tests in 22.254s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_geo261_mutation_migration：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_mutation_migration.unittest.log)

```text
FAIL: test_all_fifty_definitions_keep_live_or_retired_targets (test_geo261_mutation_migration.LiveMutationAnchorMigration.test_all_fifty_definitions_keep_live_or_retired_targets) (mid='M11')
AssertionError: 'run' != 'invalid'
- run
+ invalid
Ran 15 tests in 3.038s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_geo261_native_grid_rules：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_native_grid_rules.unittest.log)

```text
FAIL: test_signed_cell_expression_references_and_active_timber_facts (test_geo261_native_grid_rules.NativeGridRules.test_signed_cell_expression_references_and_active_timber_facts)
AssertionError: 0 != 1 : references: ASSERT:references:63
Ran 9 tests in 4.479s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_geo261_placement_sources：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_placement_sources.unittest.log)

```text
FAIL: test_actual_frame_rectangle_and_region_leaves_have_exact_typed_metadata (test_geo261_placement_sources.NativePlacementSources.test_actual_frame_rectangle_and_region_leaves_have_exact_typed_metadata)
AssertionError: 0 != 1 : ASSERT:explicit-leaves-have-no-upstream-edges
FAIL: test_binding_value_discard_control_fails_named_consumption_assertion (test_geo261_placement_sources.NativePlacementSources.test_binding_value_discard_control_fails_named_consumption_assertion)
AssertionError: 1 != 0 : Negative control must hit one real expression
FAIL: test_declined_binding_uses_explicit_values_and_region_reference_edge (test_geo261_placement_sources.NativePlacementSources.test_declined_binding_uses_explicit_values_and_region_reference_edge)
AssertionError: 0 != 1 : ASSERT:declined-binding-never-reads-upstream
FAIL: test_empty_region_set_ordered_components_and_borrowed_holes_remain_stable (test_geo261_placement_sources.NativePlacementSources.test_empty_region_set_ordered_components_and_borrowed_holes_remain_stable)
AssertionError: 0 != 1 : ASSERT:inline-set-borrows-its-own-store
FAIL: test_exact_binary_keys_decode_full_uint32_and_preserve_failed_outputs (test_geo261_placement_sources.NativePlacementSources.test_exact_binary_keys_decode_full_uint32_and_preserve_failed_outputs)
AssertionError: 0 != 1 : ASSERT:unknown-key-kind-rejected
FAIL: test_region_reference_consumes_core_region_and_records_required_value_edge (test_geo261_placement_sources.NativePlacementSources.test_region_reference_consumes_core_region_and_records_required_value_edge)
AssertionError: 0 != 1 : ASSERT:region-reference-has-two-nodes-one-value-edge
FAIL: test_same_geometry_without_region_edge_control_fails_named_edge_assertion (test_geo261_placement_sources.NativePlacementSources.test_same_geometry_without_region_edge_control_fails_named_edge_assertion)
AssertionError: 0 != 1 : ASSERT:region-reference-has-two-nodes-one-value-edge
FAIL: test_every_negative_control_hits_exactly_one_live_expression (test_geo261_placement_sources.PlacementSourcesBoundary.test_every_negative_control_hits_exactly_one_live_expression) (control='binding-value')
AssertionError: 1 != 0
Ran 21 tests in 4.694s
FAILED (failures=8)
```

</details>

<details>
<summary>py:test_geo261_wood_engineering_operations：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_wood_engineering_operations.unittest.log)

```text
FAIL: test_removed_unplaced_guard_fails_named_client_and_actual_bridge (test_geo261_wood_engineering_operations.WoodEngineeringOperations.test_removed_unplaced_guard_fails_named_client_and_actual_bridge)
AssertionError: False is not true : {'ok': True, 'preview': {'token': 1, 'valid': False, 'revision': 12, 'before': {'capabilities': ['engineering-spec/1', 'parameters/1', 'assembly-rule-authoring/1', 'assembly-timber-generation/1', 'grid-subdivision-rules/1', 'section-profile/1'], 'required_capabilities': [], 'native_capabilities': ['section-profile-native/1', 'panel-fill-native/1'], 'specs': [], 'materials': [], 'methods': [], 'applications': [], 'sources': [], 'parameters': [], 'assembly': {'capabilities': ['assembly-rule-authoring/1', 'assembly-timber-generation/1'], 'rules': [], 'bindings': [], 'instances': []}, 'sectionProfiles': {'profiles': [], 'members': [], 'runs': []}, 'geometry': {'grids': [], 'gridSystems': [], 'datums': [], 'guides': [], 'timbers': [{'id': 1, 'role': 'primary', 'geometry': None}]}}, 'after': {'capabilities': ['engineering-spec/1', 'parameters/1', 'assembly-rule-authoring/1', 'assembly-timber-generation/1', 'grid-subdivision-rules/1', 'section-profile/1'], 'required_capabilities': ['engineering-spec/1'], 'native_capabilities': ['section-profile-native/1', 'panel-fill-native/1'], 'specs': [], 'materials': [], 'methods': [], 'applications': [], 'sources': [{'target': {'field': 'A', 'id': 1, 'kind': 'timber'}, 'source': {'kind': 'literal', 'value': 55}, 'override': None, 'effective': 55, 'path': 'explicit integer mm'}], 'parameters': [], 'assembly': {'capabilities': ['assembly-rule-authoring/1', 'assembly-timber-generation/1'], 'rules': [], 'bindings': [], 'instances': []}, 'sectionProfiles': {'profiles': [], 'members': [], 'runs': []}, 'geometry': {'grids': [], 'gridSystems': [], 'datums': [], 'guides': [], 'timbers': [{'id': 1, 'role': 'primary', 'geometry': None}]}}, 'redeclaredReferences': [], 'sectionProfiles': {'before': {'profiles': [], 'members': [], 'runs': []}, 'after': {'profiles': [], 'members': [], 'runs': []}, 'warnings': [], 'diagnosticsComplete': True, 'violations': [{'code': 'SECTION_PROFILE_INVALID', 'clause': 'I43-I49', 'message': 'I9: candidate still contains an unplaced timber', 'expected': 'valid atomic transaction', 'actual': 'rejected input or upstream dependency'}]}, 'violations': [{'code': 'ENGINEERING_INVALID', 'clause': 'I8/I35', 'message': 'I9: candidate still contains an unplaced timber'}, {'timber': 0, 'clause': 'I8', 'expected': 'all world invariants pass', 'message': 'candidate rejected'}]}}
Ran 15 tests in 15.656s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_geo261_wood_finish：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_wood_finish.unittest.log)

```text
FAIL: test_same_fractional_thickness_guard_controls_actual_preview_and_commit (test_geo261_wood_finish.WoodFinish.test_same_fractional_thickness_guard_controls_actual_preview_and_commit)
AssertionError: 'thickness must be explicitly set positive integer mm in D1; no rounding' not found in 'I35: effective dimension violates its positive/nonnegative integer mm range'
Ran 12 tests in 21.110s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_geo261_wood_grid_application：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_geo261_wood_grid_application.unittest.log)

```text
FAIL: test_child_parent_type_index_space_and_stagger_order (test_geo261_wood_grid_application.WoodGridApplication.test_child_parent_type_index_space_and_stagger_order)
AssertionError: 0 != 1 : child: ASSERT:child:134
FAIL: test_removed_child_identity_guard_fails_parent_change_assertion (test_geo261_wood_grid_application.WoodGridApplication.test_removed_child_identity_guard_fails_parent_change_assertion)
AssertionError: 0 != 1 : child: ASSERT:child:134
Ran 11 tests in 23.112s
FAILED (failures=2)
```

</details>

<details>
<summary>py:test_guide_panels：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_guide_panels.unittest.log)

```text
FAIL: test_every_panel_and_callout_resolves (test_guide_panels.GuidePanels.test_every_panel_and_callout_resolves)
AssertionError: 1 != 0 : panels: 39
unresolved: [('callout', '基礎幾何型別', 'lines 63-75', '\\} Point3;'), ('callout', '基礎幾何型別', 'lines 63-75', '\\} Vector3;'), ('callout', '基礎幾何型別', 'lines 63-75', '\\} Quad3;'), ('callout', '基礎幾何型別', 'lines 63-75', '\\} Plane3;'), ('callout', 'vector_cross', 'lines 86-89', '\\.x = a\\.y \\* b\\.z'), ('panel', 'SurfaceFrame'), ('callout', 'surface_point_to_room', 'lines 377-386', '\\.x = surface->frame\\.origin\\.x'), ('callout', 'surface_point_to_room', 'lines 377-386', 'w \\* surface->frame\\.normal\\.x'), ('callout', 'surface_frame_is_valid', 'lines 136-140', 'return vector_dot\\(frame->axis_u, frame->axis_u\\) '), ('callout', 'surface_frame_is_valid', 'lines 136-140', 'vector_dot\\(frame->axis_u, frame->axis_v\\) == 0 &&'), ('callout', 'surface_frame_is_valid', 'lines 136-140', 'vector_cross\\(frame->axis_u, frame->axis_v\\),'), ('panel', 'PolygonLoop2'), ('panel', 'SpaceBoundarySurface'), ('panel', 'GuideLine'), ('panel', 'Timber'), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', 'Vector3 axis_length = surface_direction_vector\\('), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', '\\? surface->frame\\.normal'), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', 'Vector3 axis_a = vector_cross\\(axis_b, axis_length'), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', 'SurfacePoint2 far_corner = \\{'), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', 'surface_contains_rect'), ('callout', 'timber_place_a0_on_surface', 'lines 1018-1065', 'timber->placed = true;'), ('callout', 'timber_local_to_room', 'lines 1067-1077', 'length_coordinate \\* timber->axis_length\\.x'), ('callout', 'timber_get_face_room', 'lines 1079-1087', 'const int k = TIMBER_FACE_SPEC\\[face\\]\\.axis;'), ('callout', 'timber_get_face_room', 'lines 1079-1087', 'local\\[u\\] = TIMBER_FACE_WALK\\[s\\]\\[i\\]\\[0\\]'), ('callout', 'timber_get_face_room', 'lines 1079-1087', 'out_face->vertices\\[i\\] = timber_local_to_room\\('), ('callout', 'World', 'lines 2786-2790', 'SpaceBoundarySurface boundaries\\[WORLD_MAX_BOUNDAR'), ('callout', 'World', 'lines 2786-2790', 'TimberAnchor anchors\\[WORLD_MAX_TIMBERS\\];'), ('callout', 'World', 'lines 2786-2790', 'Timber timbers\\[WORLD_MAX_TIMBERS\\];'), ('callout', 'parse_scene_file', 'lines 9978-10108', '!out_world->timbers\\[i\\]\\.placed')]
Ran 1 test in 0.087s
FAILED (failures=1)
```

</details>

<details>
<summary>py:test_product_architecture：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_product_architecture.unittest.log)

```text
ERROR: setUpClass (test_product_architecture.ProductArchitecture)
architecture_contract.ContractError: geometry-web/cdp_test.js:1: EXCLUSION_DIGEST: immutable lf digest is absent or mismatched
Ran 0 tests in 0.151s
FAILED (errors=1)
```

</details>

<details>
<summary>py:test_scenario_verify：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_scenario_verify.unittest.log)

```text
ERROR: test_model_base_stdout_and_stderr_are_bounded_inside_worker (test_scenario_verify.ScenarioNativeAcceptance.test_model_base_stdout_and_stderr_are_bounded_inside_worker) (descriptor=1)
geometry_app.model_common.ModelError: Isolated verification exceeded its execution budget.
ERROR: test_model_base_stdout_and_stderr_are_bounded_inside_worker (test_scenario_verify.ScenarioNativeAcceptance.test_model_base_stdout_and_stderr_are_bounded_inside_worker) (descriptor=2)
geometry_app.model_common.ModelError: Isolated verification exceeded its execution budget.
Ran 37 tests in 462.080s
FAILED (errors=2)
```

</details>

<details>
<summary>py:test_section_profile_mutation_check：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/py_test_section_profile_mutation_check.unittest.log)

```text
FAIL: test_collector_preserves_actual_module_qualified_modelerror (test_section_profile_mutation_check.ExceptionCollector.test_collector_preserves_actual_module_qualified_modelerror)
AssertionError: 'geometry_app.model_common.ModelError' != 'modeling.common.ModelError'
- geometry_app.model_common.ModelError
+ modeling.common.ModelError
Ran 29 tests in 1.324s
FAILED (failures=1)
```

</details>

<details>
<summary>node:tests-js：原始失敗訊息摘錄</summary>

[完整原始輸出與 traceback](suite-logs/node_tests-js.log)

```text
✖ delivered engineering project reopens through a private real service, retains seven bound sources and rejects tampering atomically (51060.389569ms)
✖ native old27/live29 receipt updates the same complete model once; source settings remain fixed (80398.102013ms)
✖ native complete record survives actual workspace save ZIP reopen, fresh verify, undo and redo (60115.598269ms)
```

</details>

完整原始日誌與機器可讀結果：

- [完整 runner 原文](run_all.log)
- [逐 suite 原始日誌](suite-logs/)
- [機器可讀 JSON](suite-results.json)
- [每 suite 一行 CSV](suite-results.csv)
- [214 suite 登錄快照](registered-suites.expected.json)

未驗項：六個 browser jobs（canvas、assembly、documents、grid、space、timber）、main／整合分支相同指令效能比較與前 20 熱點、Windows GDI、各修正三段證據、最終來源 mutation ledger 刷新、完整 ModelError／section-profile mutation gate（含 SPM38/SPM40 真正 mutation 收據），以及所有逾時 suite 的完整結果。run_all 額外列出的必要 owner／browser gates 亦未由本段代驗，不自動等同六個 CI jobs；詳見原始 runner log。
