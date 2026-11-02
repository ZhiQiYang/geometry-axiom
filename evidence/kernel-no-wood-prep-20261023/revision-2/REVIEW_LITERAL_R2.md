# 無木工候選 R2：literal include 補強覆核

只做小型文字／AST結構靜態審查，未編譯、未跑測試、未改候選或 collector。

讀取葉檔 `/workspace/kernel-no-wood-work/tests/test_rectangular_template.py`（負責人提供 SHA256 `e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e`）與 collector `/workspace/kernel-no-wood-prep/run_proof.py`（SHA256 `48e0badb3e09cb16603af11ad04fe8d79a75055009868beabd02acf64b2ce6bc`）。此檔是針對初審 `REVIEW_NO_WOOD_PREP.md` angle include 缺口的獨立補充，不改寫初審原件。

新版解析 quoted／angle literal，quoted 搜尋含來源目錄與已安裝 include roots，angle 搜尋 include roots；有 project 匹配的 angle header 一樣進 K 邊界檢查，沒有 project 候選的 system header 保留。原 K 邊界 assert 保留，沒有放寬。

同一新增方法中 quoted 與 angle 各有 baseline→真 header compile/link/exact-cells→來源 gate拒絕→還原來源 gate→原 exact-cells。正常版 collector 嚴核兩組 gate exits `[0,1,0,0,1,0]` 與兩個 mutant binary 的 exact-cells exit0；新增獨立撤回 literal parser 至舊 quoted parser 的正常 assertion 1、恢復0。撤全部 K guard 會由兩個 subTest 正常 failures 揭露，collector 因此嚴核 failures2，不把錯誤／缺標頭當反證。七個 outer phases 目標為0/1/0/1/0/1/0，但這仍只是準備，尚非實際結果。

初審所指的 `<rectangular_grid.h>` literal 繞路已在候選中補上控制，本輪沒有確立的新靜態阻擋。此判斷只涵蓋候選既定 literal include 範圍；不把 regex 視為完整 C preprocessor dependency closure。最終接受仍要同 committed source SHA 的真編譯／原 gate原始 streams、正常 assertions與來源恢復身份。
