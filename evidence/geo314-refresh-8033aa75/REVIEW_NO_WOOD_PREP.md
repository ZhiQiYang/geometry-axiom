# 無木工候選：獨立靜態對抗審

本次只讀候選與 collector；未編譯、未執行測試，也未修改負責人的檔案。

候選 `test_rectangular_template.py.patch` SHA256：`2b14c750746c3c7912bc6fa8b3119ea4672e003a206f9a4eb71ffba0639aaaaa`。
collector `run_proof.py` SHA256：`dc7444f5a00e9005d3e0dce533db5fb00087dcae2c00b4980299dae88be4dedd`。

## 待補的控制

`test_source_installation_is_closed_and_contains_only_core_recipe_and_tests` 的既有 include regex 只收集 `#include "..."`；新增 K 層檢查仍只檢查該集合。隔離編譯器同時有 rectangular-grid 的 `-I` 搜尋路徑。因此 literal `#include <rectangular_grid.h>` 可指向已安裝 W header，卻不進該 K 層檢查。這是靜態可見的檢查缺口，尚未動態確證；不能將其記為真測試失敗或已取得反證。

建議補辨識 quoted 與 angle literal include：可解析到隔離 project header 的 angle include 仍需守 K 邊界，系統標頭照原編譯搜尋行為處理。quoted 與 angle 控制各自確認真 header 可編譯、連結、exact-cells 成功，再取得原來源 gate 的 0/1/0；不要用缺 header 或編譯失敗代替層拒絕。

## 暫無具體反對的部分

import blocker 增補 `geometry_woodworking`，測試建立實際可匯入的 sentinel 套件；withdraw 時應由正常 assertion 揭露。quoted K→W 控制使用已安裝的真 W header，先編譯/連結/exact-cells，再核來源 gate 正常 assertion；原功能及語意 mutant 測試保留。collector 分開保存各 phase 真 returncode、stdout/stderr，未用 wrapper 成功代替原裁判。上述均只完成靜態審查；動態 0/1/0、同 SHA、完整輸出與資源時槽尚待負責人補齊。
