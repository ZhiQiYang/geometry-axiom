# #381 重複開間 111 支的耗時：選項 A 的量測與比對（2026-11-15，雲端容器）

使用者 2026-11-15 選 A（`決策佇列.md`「2026-11-15 #381 …採 A」）。這裡是改動前後的量測、結果比對與剩餘熱點。

## 環境與做法

- 雲端 Linux 容器；`npm run build`、`start_local.py` 18839 埠、headless Chromium 1400×900、真滑鼠鍵盤。
- 腳本是 `evidence/l4-cloud-20261114/scripts/walk_r04d2.js`（只用 UI），情境同該目錄 README 的「R04 d」：
  - **B**：`assembly-generation-v1.gcanvas` 面 1，網格 12×9，一次生成 111 支（世界 113 支）。
  - **C**：先墊 62 支（世界 64 支）再做 B（世界 175 支）。
  - **A**：先墊 62 支，網格 3×2，生成 7 支（世界 71 支）。
- **改動前**：main `7c04d0c2`（含 #394）乾淨工作樹，`runtime_version.py --probe` version `edf64995…dc72b`、`fresh:true`。
- **改動後**：同一 main 加本 PR 的 `assembly_sources.c`，version `3e091eea…5aee1`、`fresh:true`。
- 耗時是「按下按鈕到狀態列換字」與「選檔到『正在載入專案場景…』消失」，各情境的次數寫在表內。只在這台容器量過，Windows 本機沒有量。

## 耗時

| 情境 | 步驟 | 改動前 | 改動後 |
|---|---|---|---|
| B（111 支） | 預覽 | 8.10、7.98 秒 | 1.57、1.74 秒 |
| B | 確認 | 8.39、8.16 秒 | 1.72、1.85 秒 |
| B | 冷開 | 10.97、10.87 秒 | 4.66、4.16 秒 |
| B | 復原／重做 | 0.11／0.12 秒 | 0.12／0.12 秒 |
| C（64＋111 支） | 預覽／確認／冷開 | 11.6／11.8／17.9 秒（main `724d0370`，11-14 量，一次） | 2.38／2.28／7.47 秒（一次） |
| A（64＋7 支） | 預覽／確認 | 0.19／0.31 秒（main `724d0370`，11-14 量，一次） | 0.17／0.27 秒（一次） |

B 的改動前後各跑兩次，表內兩個數字就是那兩次。C、A 的「改動前」沿用 11-14 在 main `724d0370` 的量測（`evidence/l4-cloud-20261114/README.md`），不是同一個 main，只能粗比。

決策回報寫「約快 10 倍」，根據的是沒有重讀材料配置與規則的試作版（當時量到預覽 0.7 秒）。正式版每次重用前仍重讀這兩種定義，B 的預覽與確認約快 5 倍，冷開約快 2.4 倍。

## 結果有沒有變

- B 改動前後另存的專案檔，`world.scene` 逐位元組相同（37,308 bytes，SHA-256 前 16 碼 `c42c252a69e5c431`）。`manifest.json` 也逐位元組相同（340 bytes，`projectId` 都是 `assembly-generation-v1`）。兩個專案檔長度相同（37,870 bytes），整包只差 8 個位元組，都在兩個項目的 ZIP 時間欄位（00:36:48 與 00:45:36）：包裝的時間不同，所以整包的雜湊不同。檔案：`before/r04d-b.gcanvas`、`after/r04d-b.gcanvas`。
- 每個情境的格數、狀態、角材數、復原／重做、冷開後角材數，改動後都和改動前（或 11-14 的紀錄）相同：B 是 99 格 generated、新增身分 111、「驗證通過，確認後才會套用。」、2 → 113 → 2 → 113 → 冷開 113。
- 專案已有舊式單一開間實例時再加重複開間（R06 發現 6 的情境，`walk_r06_legacy.js`）：兩格 generated、確認鈕可按、冷開後兩個實例都在（`after/walk_r06_legacy.result.json`）。
- 原生測試 `tests/test_assembly_bay_repeat.py` 55 條全過，同一台容器的執行時間從 2 分多鐘（11-14 量到 131～165 秒）降到 69 秒。

## 改動後剩下的時間花在哪

預覽、確認、冷開期間對原生行程取樣 29 次（`after/native-stack-samples.txt`，gdb 每次取 14 層）。出現在堆疊裡的比例：

- `wood_assembly_instance_sources`（重用前重讀材料配置與規則）：8/29。
- `wood_assembly_bay_load_generated`（每個身分第一次的完整解碼）：4/29。
- `wood_assembly_load_rule`／`wood_assembly_load_binding` 合計出現在 10/29、9/29（含上面那 8 次）。

也就是說，剩下的時間約三成仍是重讀材料配置與規則。要再壓，得讓這兩種定義也「內容相同就不重新解析」，那會動到已有反向控制的 `wood_assembly_load_rule`／`wood_assembly_load_binding`，這次沒有做。

## 檔案

- `before/walk_r04d-b.run{1,2}.result.json`、`after/walk_r04d-b.run{1,2}.result.json`：B 的兩次量測。
- `after/walk_r04d-c.result.json`、`after/walk_r04d-a.result.json`、`after/walk_r06_legacy.result.json`。
- `before/r04d-b.gcanvas`、`after/r04d-b.gcanvas`：B 另存的專案檔。
- `after/native-stack-samples.txt`：取樣原文。

## 沒有量的

- Windows 本機的耗時。
- F1 客廳的實際平面（這裡是規則格 12×9）。
- 接近 512 支上限的情境。
