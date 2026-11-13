# 08 子格測試夾具：邊界同座標使用標準 min 參照

四輪完整 suite 已完成：修前 9／2、修後 11／0、撤回一行夾具修正後 9／2、復原 11／0；另有原 parent-lock 方法的定向 1／1，保存真正 native baseline→mutant→restored 三筆原始結果。這不代表 PR #288 全量或 browser 驗收通過；本 publication 準備時尚未發布。

自有分支 `codex/geo261-fix-grid-child-fixture-20261018`；基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，修正 `5fc3369f283c63662c81a7f6229d555263822e38`。分類是 **測試夾具寫錯**，不是產品缺陷，也不是原先合法預期隨新條文過時。唯一變更是 `tests/geo261_grid_application_harness.c` 一行：兩軸低界 `0` 改成公開常數 `WOOD_GRID_CELL_MIN`，高界 `1` 不變。Python 測試逐 byte 不變，所有 C 正向、拒絕、狀態不變、父格鎖與 stagger 順序斷言整行保留；產品與 SSOT 未改。

## 根因與條文

夾具的有效面是 `[0,200] × [0,200]`，兩軸父線為 0、100、200。原夾具以 `line:0`／`line:1` 指第一格，但第 0 線恰與最小外接邊界同座標。D19 明定此情況用 `min`／`max` 作標準參照，I25 要求符合 D19 標準形式。因此第一格應為 `min`／`line:1`，實際範圍仍是 0–100；兩軸各二等分仍為 50 mm，沒有改指其他格子或放寬相鄰／整除守門。

真產品呼叫鏈為 `wood_grid_child_check` → `wood_grid_valid_in` → `wood_grid_axis_lines_in` → `wood_grid_cell_bounds`。邊界保留 MIN／MAX，只加入嚴格位於內部的父線，所以本例標準 refs 為 `[MIN,1,MAX]`；原 `[0,1]` 應拒絕。原 raw 只印 `ASSERT:child:134`；本報告不把由 source 推得的完整 I25 診斷冒充實際 stderr。

歷史依據：`494660068` 已有 D19／I25 標準參照；`eeb30d51` 抽出的 `grid_cells.c` 保留相同邏輯，並已有 `min-alias-rejects-line-at-min`；`57500f5c` 新增本夾具時低界即誤填 `0`；`98f651ca` 的 child admission 已呼叫完整 grid validator。後來 `d0b5a104` 只給父格鎖負控制具名斷言，沒有修這個前置夾具。此一行依既有明確條文修正，無新條文決策。

## 真實結果與撤回

| 輪次 | 測試 SHA | methods 通過／失敗 | unittest 秒 | 外層 child 秒 | exit |
|---|---|---:|---:|---:|---:|
| before | e9c1509cf89e6f35d298743ec5e3368370316cf7 | 9／2 | 10.209 | 10.364531676 | 1 |
| after | 5fc3369f283c63662c81a7f6229d555263822e38 | 11／0 | 7.567 | 7.717455930 | 0 |
| withdrawn：只撤回一行夾具 | 8cbf5c89bc7c4f5bc8e1e9bb58a50b88be6d0a91 | 9／2 | 7.823 | 7.997819071 | 1 |
| restored | 5fc3369f283c63662c81a7f6229d555263822e38 | 11／0 | 8.242 | 8.409403944 | 0 |
| parent-lock 定向旁錄 | 5fc3369f283c63662c81a7f6229d555263822e38 | 1／0 | 4.252 | 4.446818525 | 0 |

前四輪命令完全相同：`python3 -B -m unittest -v tests.test_geo261_wood_grid_application`；每輪完整 11 methods。第五輪只跑既有 `WoodGridApplication.test_removed_child_identity_guard_fails_parent_change_assertion`，不與全 suite 數相加冒充新增 coverage。五輪均來源穩定、零 error／skip、沒有 timeout；原命令、UTC、環境及原始退出收據見 [results.json](results.json)。外部 recorder 設 16 MiB stack 與 600 秒外層上限，case 原 10 秒限制不變。

修前與撤回的兩個同源失敗：

```text
test_child_parent_type_index_space_and_stagger_order
test_removed_child_identity_guard_fails_parent_change_assertion
AssertionError: 0 != 1 : child: ASSERT:child:134
```

第二個方法在 mutant 建置前的基準 child 呼叫就失敗，因此修前／撤回的紅 **不是 parent-lock mutation kill**。這兩個失敗共用錯誤夾具，不能報成兩個獨立產品缺陷。原文：[before](before/command.stderr)、[after](after/command.stderr)、[withdrawn](withdrawn/command.stderr)、[restored](restored/command.stderr)。[撤回提交 patch](withdrawn-commit.patch) 保留本地撤回差異；沒有移除產品修正。

## 真正 parent-lock 單點突變

定向入口只把該 suite 模組的 `subprocess` 參照換成透明 observer；原 `run` args／kwargs 呼叫一次，回原 CompletedProcess，finally 恢復。沒有覆寫全域 stdlib subprocess、NativeBuild、原 case 或任何斷言。原 case 仍回 int，原精確 marker 比對也保留。原負控制只改 `grid_application.c` 一個父身分守門，再替換一個實際 product object 連結，最後回到原 binary。

[原 protocol](protocol-parent-lock/protocol.jsonl) 三筆順序與 [逐欄核對](protocol-review.json)：

1. 原 `grid-application-client child`：exit 0、stdout／stderr 空。
2. 真 `grid-application-child-identity child`：exit 1、stdout 空、stderr **精確** `ASSERT:grid-child-parent-lock\n`。
3. 原 `grid-application-client child`：exit 0、stdout／stderr 空。

第 1／3 筆 binary SHA 相同：`4cac11254a1672e1101155f580ee5c9482cae616896f91797a6796194251c30d`；第 2 筆 mutant 為 `4a05f64c551d60468c8fdb1f97452777121c0c53ccd0d4325ca2ea3cb103b8ad`。三筆原 timeout 都是 10 秒。[定向 unittest](protocol-parent-lock/unittest.stderr) 真 1／1，[執行 metadata](protocol-parent-lock/result.json) 記 method、來源及 wrapper hash。這是已執行的產品 guard-removal 證據；另列的一行夾具撤回證據不能代替它。

## 環境、封存與未驗

Linux 6.18.55 x86_64／glibc 2.41、GCC 14.2.0、Python 3.12.14、Node 24.19.0、Google Chrome 155.0.8059.84、stack 16 MiB。列 Chrome 版本不是 browser 驗收。本題在 NativeBuild 隔離目錄編譯／執行；持久 registry sidecar 不冒充 transient client／mutant。protocol 的 stdout／stderr 是原 text=True 解碼結果，ELF 只記 hash 不公開；旁錄有額外 I/O 耗時，不當效能對照。

公開前綴 `evidence/geo261-codex-fix-grid-child-fixture-20261018/`。固定 collector 只核原件 bytes/hash 與 metadata，一切 pass／kill 分類先由人工讀原文判斷；inventory 不收 ELF、巨量 source inventories、秘密或整個工作區。

未驗：最終組合 strict 非瀏覽器全量、六 browser jobs、Windows／GDI、舊包真 UI、效能及其他架構驗收。既有 e64 結果仍綁原 SHA，本題完整 11 methods 和定向 1 method 不能取代 PR #288 全部驗收。
