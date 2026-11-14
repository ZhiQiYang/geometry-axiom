# 雲端實機核對（2026-11-14）

雲端 Claude（session `c161fbcc`）做的兩件事：

- **R14 host／App 第一片**（[#379](https://github.com/ZhiQiYang/geometry-axiom/pull/379)，台北 11-14 16:29 合併）：L4 實機核對。
- **R06 發現 6**（[11-13 核對紀錄](../l4-cloud-20261113/README.md)第 6 點）：修正前後的實機紀錄。修正在 [#405](https://github.com/ZhiQiYang/geometry-axiom/pull/405)。

方法沿用 [11-07 核對紀錄](../l4-cloud-20261107/README.md)「環境與方法」：
- `npm run build` → `geometry-web/start_local.py`，`runtime_version.py --probe` 回 `fresh:true`。
- Playwright headless Chromium，視窗 1400×900，每項先「檔案 → 新專案」。
- 存檔時把 `showSaveFilePicker`／`showOpenFilePicker` 設成 `undefined`，走下載與檔案欄位的後備路徑。

`page.evaluate`／`$eval` 只用來讀畫面文字、讀格線元素的位置後再用滑鼠點，以及唯讀查詢 `objects`。這是雲端實機操作，不是使用者驗收（L5）。

## R14 面材分份 host／App 第一片（main `724d0370`）

**操作路徑**（`scripts/walk_r14.js`）：
1. 檔案 → 新專案 → 畫布中央「建立網格系統」。
2. 名稱「R14 面材七等分」。u 軸點選「面材＋縫」，填面材 915、縫寬 2、面材起點 0；v 軸間距 400、第 0 線 0。
3. 預覽並建立 → 確認套用。
4. 「新增子規則」：名稱「面材七等分」、u 7、v 2 → 預覽 → 取消；再預覽 → 確認套用。
5. 點選格子 (0, 0) → 返回畫布 → 復原 → 重做 → 另存新檔。
6. 全新瀏覽器 → 開啟專案 → 點網格來源卡 → 開啟 → 再點格子 (0, 0)。

**結果：通過。**
- 建立來源的預覽寫著「u 無限面材 915＋縫 2 mm，起點 0 mm，間距 917 mm」。
- 子規則預覽寫著「每一主格為 14 個 131×200 mm 小格」，確認鈕可按。917÷7＝131、400÷2＝200。
- 取消後規則數 0；確認後規則 `ruleKey 1`、等分 7／2、`nextRuleKey 2`。
- 格子 (0, 0) 顯示 7 條子線：u 方向 6 條、v 方向 1 條，見 `screens/R14-3-sublines.jpg`。
- 復原後規則數 0，重做後 1。
- 另存後冷開，規則仍在，格子 (0, 0) 仍顯示 7 條子線。

證據：`walk_r14.result.json`、`r14.gcanvas`、`screens/R14-*`。

**未核對**：
- 390 px 手機寬度：#379 的瀏覽器測試有跑，這次沒跑。
- 子規則的編輯與「917 不能六等分」的拒絕。
- 未確認原始輸入的保存。
- Windows 原生對話框、觸控、中文輸入法。

## R06 發現 6：專案已有舊式單一開間實例時的重複開間

**操作路徑**（`scripts/walk_r06_legacy.js`，以 11-07 的 `walk_r06.js` 為底，只用 UI）：
1. 開啟 `geometry-web/examples/assembly-generation-v1.gcanvas`，**不刪**舊式實例 #1（角材 1–3）。
2. 雙擊面 1 → 網格 → 主支直向 → u 明寫 `3000 3500`、v 明寫 `1000 2000` → 建立網格。這個位置不和舊實例碰撞。
3. 組構規則 → 配置 1 → 依來源生成角材 → 重複開間 → 承載面 #1 → 移除預設列。
4. 加入索引範圍：主支 u 0–1、端點 90／91；副支線 v 0–1。
5. 預覽變更 → 確認套用 → 另存 → 全新瀏覽器開檔。

| | 修正前（main `724d0370`） | 修正後（#405 commit `1c5f54145`） |
|---|---|---|
| 狀態列 `#asmStatus` | 「原生服務的所屬角材身分不完整；草稿仍保留。」 | 「驗證通過，確認後才會套用。」 |
| 開間 | 無預覽 | 2 格，全部 generated |
| 確認鈕 | 停用 | 可按，確認成功 |
| 冷開後組構實例 | 只有舊實例 | 舊實例（角材 1–3）＋重複開間實例（角材 4–7） |

證據：
- 修正前：`r06-before/walk_r06_legacy.result.json`、`r06-before/R06L-3-bay-preview.jpg`。
- 修正後：`r06-after/walk_r06_legacy.result.json`、`r06-after/r06l.gcanvas`、`r06-after/R06L-*.jpg`。
- 修正前那次跑的腳本，比 `scripts/walk_r06_legacy.js` 少了冷開後讀 `#asmStatus` 的一行，其餘相同。
