# SR18：來源規則線的角色拒絕（待執行探針）

本目錄僅準備探針，作者沒有執行 native／瀏覽器／產品測試。不得將本文件當 pass 收據。唯一 native owner 應串行執行，保留首輪所有失敗。

契約不是「來源子線只准 secondary」。`公理層.md:233–235`（D15）允許明確覆寫預填角色；D17 `248–252` 定義由既有 primary 推出的主支軸；I21 `674–677` 明定 secondary 不可與主支軸平行，診斷 `V_PRIMARY_AXIS`。I13 `645` 要求 direct rule 完整 footprint ⊆ 父 cell，且仍有真擋面／碰撞／角色檢查。R20 `998–999` 要求重宣告連坐重驗失敗整筆回滾。角色負例鎖的是 I21，不發明來源規則線専屬 role guard。

現有 `tests/test_grid_subdivision_oracle.py:611–638` 的 direct primary 拒絕帶有 400mm cell／1560mm 全跨度不合的前置條件；它不能單獨證明角色拒絕。P88 `grid_rule_lines_test.js:101–107` 的 `t9999` 則只驗缺失支撐 selector。既有 manual-subgrid 的 `tests/test_subgrid_contract.py:313–321` 已示範 full-height cell＋真支撐排除 R6 前置失敗後，才鎖 `V_PRIMARY_AXIS`；本探針把同樣隔離方式套到正式來源規則線。

最小 fixture：

1. 重用 `NativeSubdivisionOracle.source/rule/boundary/binding/apply_grid`（`tests/test_grid_subdivision_oracle.py:196–222`）及 `real_supports`（597–606）；只將 source v 改為合法 `repeat 0 1600`。boundary仍 `(100,200)–(2100,1800)`，binding錨到 cell `(-2,1)`，該 cell 精確為 `[100,200,700,1800]`。
2. 真 boundary t81/t82 分別貼 e0/e2；t1/t2 為已成功放置的 primary +v，中心 x120/x680、長1560，建立明確主支軸。
3. 正對照 t9 明寫 primary、20×20，`place 9 on 1 at-line rule 10 0 1 -2 1 u 0 between t81 t82 +v +n` 必須真正成功。字面預期 centerline300、length1560；從回傳 origin/axes/尺寸獨立算 footprint `[290,220,310,1780]`，全在 cell內。這也證明 primary 覆寫預填角色本身合法。
4. 只送 `timber 9 20 20 role secondary`，同 id/截面/定位/完整規則線 tuple/selector/真支撐均未換。鎖 `V_PRIMARY_AXIS`、明確指 t9/secondary，拒絕不能靠 `I13/R6` 或缺失支撐過關；如有候選，再確認不能提交。前後完整 dump、references、definition revision/hash 必須全等，原完整 t9 讀回亦全等。

本探針不混入 selector 負例或 SR15 source-parameter／binding-anchor 修改。參數／錨點修改是 R32 現有操作；目前既有 literal-pitch＋兩既存錨點證據不能改稱那些修改已驗。

由 root 串行執行（HEAD 填執行前實際完整 SHA；out 必須不存在）：

```sh
ulimit -s 16384
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -B /workspace/closure-evidence/inventory/final-contract-mapping/sr18-probe/sr18_role_probe.py --repo /workspace/geometry-axiom --head ACTUAL_FULL_SHA --out /workspace/closure-evidence/inventory/final-contract-mapping/sr18-probe/run-01
```

入口強制明設 `GEOMETRY_TEST_BRIDGE`，透過既有 `binaries.inspect_one` 核對 sidecar＋來源閉包＋binary hash；不自動編譯，不借用現有HTTP/native服務。使用獨立新 bridge child，Linux另記 `/proc/PID/exe` 實際載入hash。腳本不要求整個工作樹標成clean：文件／交付整理的 dirty 狀態及完整diff都保存；所有native來源閉包及探針依賴必須逐bytes等於執行HEAD，前後再比。

交付 raw `bridge.stdin`／`bridge.stdout`／`bridge.stderr`、逐命令 JSONL、正對照、原始拒絕、前後完整快照、Git/腳本/依賴/bridge身份、退出碼與artifact hashes。90秒watchdog僅終止本探針自有child；清理或身份核對失敗仍非零退出。若正對照不成立，先記前置條件失敗，不把後續角色結論改成pass，不迎合native輸出修改判定。
