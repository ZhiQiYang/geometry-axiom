# GEO-128 實作與驗證交付

日期：2026-09-18。遠端基線 `3c827ea84bf3ecfedbda063bca1e77c1f5f066d5`。
程式與文件已交獨立 agent 審查；五項呈現及 ID 邊界問題已修正。
主審已重跑 datum 9/9 並核對獨立審查，依使用者授權接受明列驗證範圍並批准合併 PR #1。
本文件記錄實測範圍，不代表未完成的瀏覽器驗收已通過。

## 重現運行

依賴為 GCC、Python 3；閱讀器檢查另需 Node.js。既有 Windows build.bat 可保留使用，
本次實際執行的是 Linux GCC，未執行 Windows GDI。

```sh
npm run build
GEOMETRY_BRIDGE=.build/web_bridge python3 geometry-web/serve.py 8765
```

在本機開啟 `http://localhost:8765`。工具列「共用基準」可新增具名規格、建立基準、
選面引用及修改來源。檔案選單「公理閱讀器」開啟唯一正典。
受管雲端預覽另可使用 `npm run dev`；只有明示 `GEOMETRY_MANAGED_PREVIEW=1`
且 port=4173 才允許 terminal.local，普通啟動仍限 localhost。

## 實際驗證

```sh
GEOMETRY_TEST_BRIDGE=.build/web_bridge python3 tests/test_datum_contract.py
GEOMETRY_TEST_BRIDGE=.build/web_bridge python3 tests/test_reference_contract.py
GEOMETRY_TEST_BRIDGE=.build/web_bridge python3 tests/test_bridge_integrity.py
python3 tests/run_tests.py .build/core
gcc -std=c11 -O2 tests/test_core_integrity.c -lm -o /tmp/geometry-tests/integrity
/tmp/geometry-tests/integrity
python3 tests/test_serve.py
python3 tests/test_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
```

結果：datum 9/9、既有引用 25/25、bridge 完整性 9/9、場景 122/122、
C 完整性 80/80、HTTP server 8/8、閱讀器 8/8。
canvas_test.js 經實際 HTTP server/bridge 的 API 檢查為 412 pass、0 fail；
這不是瀏覽器畫面／互動驗證。
AddressSanitizer/UndefinedBehaviorSanitizer 下 datum 9/9、既有引用 25/25 通過。
既有 C 編譯警告不宣稱已全部清理。

## A1–A11 與核心追溯

| 驗收／條文 | 實作入口 | 結果與證據 |
|---|---|---|
| A1 D6c | DatumPlane、reference_eval_datums、datum_guide_geometry | 通過：三軸 × 24 個有號正交 frame，世界平面成員性；負數先 floor 後反向 frame |
| A2 I7a | datum_guide_geometry、reference_rebuild | 通過：平行、重合、缺來源、裸 mm、非法有理式、越界拒絕；dump 不變 |
| A3 D6/I7/D9 | reference_eval_guide、guide_line_get_local_segments | 核心通過：孔洞兩段同 ID、面外零段仍存在且可引用；UI 以核心 segments 顯示，零段畫面未實測 |
| A4 D6a/I13 | reference_quantity、reference_eval_timber | 通過：同面同軸守門，隱藏線不容許面外放料 |
| A5 I8/I8a | reference_rebuild、reference_stage、json_reference_guide | 通過：spec/datum/frame 重算跨面鏈；局部值不變仍報世界姿態，UI 最終完整軸呈現已靜態複核 |
| A6 I8a/R2 | apply_scene_line、reference_stage、confirm | 核心通過：取消／違規／過期不改 World，整筆 undo/redo；canvas 位置不使 preview 過期或被覆寫 |
| A7 R4/I9 | reference_dump、reference_dump_guide | 通過：來源順序 spec→datum→guide、dump/load/dump 相同；既有場景 122/122 |
| A8 UI | reference-ui.js 共用基準與 confirmReferenceImpact | 部分完成：真瀏覽器建立／兩面引用／預覽；取消／確認被自動審核拒絕，未完成 |
| A9 I10/I23/R13 | 既有 grid 守門、proj_rebind_aux | 通過：索引消失守門；隱藏 guide 拆面拒絕；datum 歸片維持共同身份 |
| A10 正典 | sync_axiom_reader.py、tests/test_axiom_reader.py | 結構／來源通過：68 條、382 blocks、5 批註；五 assert、獨立 SSOT、冪等、原圖片／身份保留；手機 runtime 未驗 |
| A11 Git 交付 | 同一開發分支與 PR | 逐條公理 diff 見 DATUM-PROPOSAL.md，獨立審查見 DATUM-INDEPENDENT-REVIEW.md；合併由主 agent 最終核對 |

公理規則由 C 強制，不依賴 UI 或模型遵守提示；UI 只提交命令、呈現核心計算結果。
條號註解掃描不作為實作證明。

## 已知驗證界線

真瀏覽器詳細觀察見 `tests/evidence/datum-browser-observations.md`。
自動審核拒絕取消點擊後，又拒絕唯讀 dialog 檢查，因此停止控制並釋放受管預覽。
沒有透過別的瀏覽器、file URL、直接 CDP 或模擬 DOM 繞過。
取消／確認／undo/redo 有同一核心命令路徑的測試，但不能冒充瀏覽器端到端實測。
GDI 預覽超出容量現會拒絕確認而保留 World；Windows 路徑僅程式碼審查。
手機批註、軟鍵盤與下載未新增實機驗證。

任意斜面、其他世界幾何引用、共同網格、跨房間基準及隐藏線自動拆片歸屬仍待定，未納入本期。
