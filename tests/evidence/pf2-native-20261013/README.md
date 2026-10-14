# PF-2 雲端原生驗收

base `2004c6c8bebe1bbff2df142630b630e1ee5115b8`，領取提交 `bea36ea4`。
未改 UI、SSOT、白話、正典或角材定義。

命令皆為 `ulimit -s 16384; python3 -m unittest ...`，下表保留實際 exit。
首次 baseline 直接匯入 PF-1 test class，因此額外發現原 22 題；後改為匯入 harness module，
避免 standalone PF-2 重複登錄。首次原文仍保留。

| Run | Suites | Actual exit | Result |
|---|---|---:|---|
| baseline | new layout, with accidentally discovered PF-1 | 1 | 34 tests; 16 failing subcases, unsupported put-panel-fill |
| fixed-1 | layout | 1 | 12 tests; negative origin incorrectly rejected; test sent undo without line prefix |
| fixed-2 | layout + PF-1 | 1 | 34 tests; old unknown-command diagnostic changed because panel-fill is now a registered record |
| fixed-3 | layout + PF-1 | 1 | 36 tests; touching holes emitted a figure-eight |
| fixed-4 | layout + PF-1 | 0 | 36/36; right-branch traversal splits touching holes into simple rings |

Undo 測試改用既有 `line undo`／`line redo` 協定；原非法 record 斷言改驗新增指令的 arity error。
原斷言或夾具未刪除。以下另列完整 native 與突變收據。

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

完整 native 受測 head `4ab052dbda9ab1f814954bb2124bfab0eb541c1e`：
`ulimit -s 16384; python3 -u tests/run_all.py --build`，88 suites，
**2719 pass／0 fail／1 allowed GDI skip，實際 exit 0**，897.933 秒。
台北時間 2026-10-13 21:55:04.994175～22:10:08.763643。
PF-2 15/15、PF-1 22/22、Node 659/659、reader 41/41、test_binaries 32/32。
before/after 全部 tracked bytes 相同；受測工作樹 clean。
原完整 stdout/stderr、各指定 suite JSON、source manifest SHA、實際 binary/sidecar SHA
见 `native-summary.json` 及 `native-binary-identities.json`。
完整逐檔 source manifests、全部 suite logs 與 binary 原件仍在
`/tmp/geometry-wake20/native/`；未將大型可執行檔貼成 base64。

PF13 補充原生命令驗收（不併入 runner 計數）：1024 片完整成功、1025 片 CAPACITY 拒絕且 World 不變；
t=0 在 D26 發布前被拒。`supplementary_acceptance.py.txt` 為原腳本，stdout／exit 原件保留。

這不是 WSL 或瀏覽器收據。PF-3 effective seams/support、PF-5 衍生宿主與角材層、
PF-4 網格、PF-6 建議及真瀏覽器完整專案重開仍 pending；正式產品七項由合併列車驗證。
最後只補證據的提交不改受測產品、測試、runner、expected 或核心帳本；不把新 delivery head 冒稱受測 head。
