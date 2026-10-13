# PF-2 progress, cloud native only

Base `2004c6c8bebe1bbff2df142630b630e1ee5115b8`, claim `bea36ea4`.
No UI, SSOT, whitepaper, canonical reader or timber definitions are changed.

All commands: `ulimit -s 16384; python3 -m unittest ...`, actual exits below.
The first baseline imported the PF-1 test class directly, so unittest also discovered
its original 22 tests. Later the harness is imported as a module, avoiding accidental
duplicate registration in the standalone PF-2 suite. The baseline raw is retained.

| Run | Suites | Actual exit | Result |
|---|---|---:|---|
| baseline | new layout, with accidentally discovered PF-1 | 1 | 34 tests; 16 failing subcases, unsupported put-panel-fill |
| fixed-1 | layout | 1 | 12 tests; negative origin incorrectly rejected; test sent undo without line prefix |
| fixed-2 | layout + PF-1 | 1 | 34 tests; old unknown-command diagnostic changed because panel-fill is now a registered record |
| fixed-3 | layout + PF-1 | 1 | 36 tests; touching holes emitted a figure-eight |
| fixed-4 | layout + PF-1 | 0 | 36/36; right-branch traversal splits touching holes into simple rings |

The undo test was corrected to use the documented `line undo`/`line redo` bridge protocol;
the old invalid-record assertion now expects the registered command's arity error.
No original assertion or fixture was removed. Full native and mutation receipts follow.

第二份產品提交 `026a58a5`：縫 band 完整求值與 D1／容量檢查移入核心，
工程參數預覽包含新舊試排；新增參數下游重算驗收，layout suite 為 15 項。
`fixed-5` 的 37 題首跑 exit 1 是新 PF02 交叉比對測試讀錯 bridge 的 `objects`
欄位（KeyError），改為文件已有的 `references`；同一 mistake 造成首份突變 baseline
exit 1，保留在 `mutant-baseline-oracle-error/`，**没有把它算 killed**。
修改後實際有限 PANEL_LAYOUT 及 D29 REPEAT_PANEL 兩者都比對 101／204。

`run_pf2_mutants.py.txt` 是實際執行腳本。使用獨立 instrumented C bridge，明示透過
harness 的 binary selector 指向該執行檔，沒有宣稱 registry freshness。
base_source_head `026a58a58ad86c5a9e702a163a2fb4512a0d96e3`。
`mutants-receipts.json` 保存實際 compile/test exit，`mutants-audit.json` 補完整生成來源
及原件 SHA；每個變異有改動的原生來源、compiler stdout/stderr、具名 assertion 原文。
大份未改 core/bridge 原件留在雲端 `/tmp/geometry-wake20/pf2-mutants/`；
其內容由 pinned Git head 加腳本所列 include 替換可重建，audit 提供完整 SHA。

| 對照 | 結果 |
|---|---|
| 未變異 baseline | 15/15，exit 0 |
| 移除 PF-2 put/delete 接線 | PF02 unsupported-operation assertion，exit 1 |
| 整數縫半寬改為全縫寬 | PF02 101/204 座標 assertion，exit 1 |
| 交丁改為逐列累加 | PF03 第 2 列回 0 assertion，exit 1 |
| 不扣孔 | PF04 孔環 assertion，exit 1 |
| 層接觸當正體積相交 | PF08/PF09 接觸判定 assertion，exit 1 |
| 接觸孔環改回八字走訪 | PF04 simple hole loops assertion，exit 1 |
| 放寬門檻 X=0 | I55 parameter candidate assertion，exit 1 |
| 還原 baseline | 15/15，exit 0 |

ASan/UBSan：實際 `cc -std=c11 -O1 -g -fsanitize=address,undefined
-fno-omit-frame-pointer geometry-web/web_bridge.c -lm -o /tmp/geometry-wake20/bridge-sanitized`，
compile exit 0；37/37（15 PF-2 + 原 22 PF-1），test exit 0；原文與 binary SHA 見
`sanitize-receipt.json`。這是 instrumented 原生驗證，並非完整 native runner 收據。

既有核心突變實際全跑：`ulimit -s 16384; MUTATE_CACHE=/tmp/geometry-wake20/core-mutants
python3 -u tests/mutate.py`，actual exit 0；baseline 139/139。
48 筆：40 killed、1 crashed、4 equivalent、3 retired；0 survived/stale/blocked/invalid。
`tests/mutants_results.json` 由原工具重產，未手編。
M53 只把同一語意的變異靶點移到共用公式；由原 `_test_grid_panel.scene` 殺死。
本輪每支 binary 都在獨立 cache 實際重編並執行，沒有借用舊閉包的 killed。
極值空板列兩個診斷也都完整以 CAPACITY 拒絕，沒有先輸出截短列表；stdout 原文保留。

This is not a WSL or browser receipt. PF-3 effective seams/support, PF-5 derived placement
and timber layer, PF-4 grids, PF-6 timber suggestions and browser project reopening remain pending.
