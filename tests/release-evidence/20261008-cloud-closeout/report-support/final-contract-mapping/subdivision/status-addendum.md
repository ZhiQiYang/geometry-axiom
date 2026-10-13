# 凍結映射後的精確接續

本檔不更改已封存通過結果，不把來源推導寫成產品失敗。2026-10-08 本次來源映射發現仍可執行的有界證據工作，root 已接手安排；不是外部阻塞。

| 條目 | 已定範圍／精確來源 | 接續責任 |
|---|---|---|
| SR16 | `tests/test_grid_subdivision_oracle.py:680` 的兩面、t3/t23、U300只使第二面違規；原生全量拒絕已驗。真 UI 需沿既有 source/rule/binding/direct入口，核相同 typed違規、disabled confirm、cancel後 dump/refs/history不變。 | `/root/gate_evidence` 唯一 private browser probe writer；root 唯一 browser runner，後由獨立 reviewer核原件。 |
| SR18 | `test_grid_subdivision_oracle.py:597/611` 的真支持可用；`test_subgrid_contract.py:313` 已有合法完整cell＋角色負例。D15允角色覆寫，錯誤角色必須違反 D17/I21，不能用 UI 預設 secondary 當新公理。 | `/root/report_finalize/assembly_mapping` private native probe writer；root/唯一 native runner串行執行。正對照合法 primary；只改角色後須 V_PRIMARY_AXIS與dump/references/revision不變。 |
| SR23 | `grid_rule_lines_test.js:40–51` 建兩面，`:86–90`改pitch，`:98–107`才建立refs。須補原issue順序的「第一面→guide/direct→第二面→來源更新有限下游→取消/確認/Undo/Redo→真Save/清空/Open」，1280/390。 | 同一 SR16 browser writer/runner；重用 P88 helpers `:6–39`，不改原oracle，不重跑全suite充數。 |
| SR06 recursive | D19a `公理層.md:273`只允一層；native contract `:13–22`無遞迴欄位。既有 Node `native source closure preflight rejects unknown rule syntax atomically` 已有執行。 | 原表的「recursive payload未具名」是觀察限制；先以既有拒絕語法映射，不新增 nested API/UI 或因未採納操作無限擴測。 |
| SR14 reorder | 現行正式DSL `公理層.md:1093–1095`只有create/keyed-edit/delete；UI `grid-system-workspace.js:239/253–257`以ruleKey取row與綁定事件，沒有使用者reorder操作。rename/delete/recreate/highwater已驗。 | 不新增reorder UI。stable-key承諾與既有具名oracle已保留；未實跑任意排列交換只作來源觀察限制。 |
| SR15 parameter/anchor | `公理層.md:1070–1087`明定 param token、binding anchor，屬既定能力。source-rule native `:351`只有literal pitch更新＋兩種既存anchors；`test_parameters_core.py:149` 與 `test_infinite_grid_contract.py:197/299`為一般網格參數/anchor證據。 | 不從組合推「同rule參數/anchor更新已實跑」。root可在同一有界native接續增加參數值600→900、binding anchor只改一項的完整refs比對；不另發明參數或錨點功能。 |

探針生成與執行是後續新材料；結果必須另綁受測head、腳本hash、命令/退出碼和原始log。未執行前不提前改寫本映射為通過。
