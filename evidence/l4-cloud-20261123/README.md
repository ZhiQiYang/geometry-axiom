# 雲端實機核對：#443 五項顯示修正與 #433 R11 物件畫布觸控（main ea16e3f5，2026-11-23）

雲端 Claude（排程）在 main `ea16e3f570c22fbc73625e8fadfbfc9bd1968780` 用真 Chrome 走需求帳上 L3、還沒有 L4 的六項：

- [#443](https://github.com/ZhiQiYang/geometry-axiom/pull/443) 的五組顯示修正：D06、D09、D02、PF-4A 表格與 R17 訊息。
- [#433](https://github.com/ZhiQiYang/geometry-axiom/pull/433) 的 R11 物件畫布觸控第一片。

兩個 PR 都由合併列車 [#450](https://github.com/ZhiQiYang/geometry-axiom/pull/450) 帶進 main：merge `39798a2cb385b08b51bdf71487ae02b5f4983a4d`，台北 2026-11-22 23:32。核對前先用 `git merge-base --is-ancestor` 確認兩個 PR 的最終 head（`154f4556`、`19f06b77`）都在 #450 裡。`39798a2c..ea16e3f5` 之間 `geometry-web/` 只改了原生 bridge（#447 PF-6），沒有動到這六項的前端檔案。

做法與證據格式沿用 [#449](https://github.com/ZhiQiYang/geometry-axiom/pull/449)（`evidence/l4-cloud-20261122r03a/`）。這次只改紀錄：本目錄與 `需求帳.md` 的對應列。產品碼、`公理層.md`、時限與斷言都沒有改。

## 結論

| 項目 | 層級 | 核對 | 結果 |
|---|---|---:|---|
| D02 鍵入長度欄避開教學卡（21c-1） | **L4** | 16/16 | 1400、390 px 都通過 |
| D06 PDF `h` 閉合後的接續線段 | **L4** | 11/11 | 通過，有無 PDF 端點的對照點 |
| D09 表單顯示既有本面覆寫（21c-4） | **L4** | 14/14 | 通過，含 390 px 冷開 |
| R02 PF-4A 預覽與主格表的可讀性 | **L4** | 16/16 | 1400、390 px 都通過，含冷開 |
| R17 D16a／P1-A 中文診斷 | **L4** | 10/10 | 1400、390 px 都通過 |
| R11 物件畫布觸控第一片 | **L4**（CDP 觸控） | 30/30 | 1400、390 px 都通過；實體觸控未驗 |

六項合計 97 項自動核對全部通過。這是雲端實機操作，屬 L4 範圍，不是使用者驗收（L5）。

## 環境與方法

- **工作樹**：乾淨的 main `ea16e3f5` 工作樹，sparse-checkout 排除 `evidence/`、`tests/evidence/`。跑完後 HEAD 仍是 `ea16e3f5…`，`git status --short` 是 0 行（`main-ea16e3f5/worktree-state.txt`）。
- **服務**：`scripts/serve-wt.sh`，原樣沿用 #449。以非 root 使用者 `claude`（uid 999）執行，`ulimit -s 16384`，`LANG=C.UTF-8`／`LC_ALL=C.UTF-8`，Node v24。`GEOMETRY_FEEDBACK_DIR` 放在 `$TMPDIR`（`/tmp/l4w/tmp`）底下。先跑 `start_local.py --build-only`，再跑 `start_local.py --port 18881`。
- **Probe**：`runtime_version.py --probe 18881` 在跑前與跑後都回報 version `9cd9b61c5866b3d25401714377287023a81716cf3a168665fb8db48f58f0a683`、**`fresh:true`**，root 是該工作樹，pid 8784。檔案是 `main-ea16e3f5/runtime-probe.json` 與 `runtime-probe.after.json`。
- **瀏覽器**：Google Chrome for Testing 153.0.8010.12（headless、`--no-sandbox`），由 Playwright 啟動。每項都開新的瀏覽器與 profile，冷開步驟另開一個。
- **輸入全部經 CDP**（`scripts/lib.js`）：
  - 點擊、拖曳、滾輪：`Input.dispatchMouseEvent`。
  - 鍵盤：`Input.dispatchKeyEvent`；中文欄位用 `Input.insertText`。
  - 觸控：`Input.dispatchTouchEvent`，搭配 `Emulation.setTouchEmulationEnabled`（maxTouchPoints 2）。
  - 下拉選單：點一下，按 Escape，再用方向鍵選。
  - 元素不在可點位置時，用 CDP 滾輪捲動，並以命中測試確認點得到；不呼叫 `scrollIntoView`。
- **`page.evaluate` 只做唯讀的事**：
  - 讀 DOM 文字與元素位置，以及 `oc.panX/panY/zoom`、`fe.draft.pts`、`ReferenceWorkspace.history` 的長度等狀態。
  - 換算座標（`feMmToPx`、`feUlImgToMm`）。
  - 唯讀查詢：`dump`、`engineering-read`、`panel-fill-read`、`/runtime`。
  - R11 另掛一個只記錄不攔截的 capture 監聽器（passive），記下觸控落點。
- **只改瀏覽器屬性的兩處**（都不碰場景）：
  - `noPickers()`，同 #449：讓另存走下載、開檔走 `<input type=file>`。
  - PF-4A 用 `setViewportSize` 改視窗寬度。
- **零寫入的判定**：場景 dump 的 SHA-256、面內歷史 undo／redo 深度都與動作前相同。
- **雜湊**：一律對檔案的原始位元組計算。

### 重現

```sh
git worktree add --no-checkout <wt> ea16e3f570c22fbc73625e8fadfbfc9bd1968780
(cd <wt> && git sparse-checkout set --no-cone '/*' '!/evidence/' '!/tests/evidence/' && git checkout ea16e3f570c22fbc73625e8fadfbfc9bd1968780)
# 以非 root 使用者、設好 TMPDIR 後執行；輸出目錄先清空
TMPDIR=<tmp> bash evidence/l4-cloud-20261123/scripts/run_all.sh <wt> 18881 <輸出目錄>
python3 -I evidence/l4-cloud-20261123/scripts/verify_evidence.py <輸出目錄>
```

`run_all.sh` 會重啟服務一次並存下 probe（不是 `fresh:true` 就停）。接著用 repo 的 `tests/diagnostics/pdf_snap_close_fixtures.py` 產生 PDF 夾具，再依序跑六支 `walk_*.js`。

## 逐項操作路徑與結果

### D02：鍵入長度欄避開首次教學卡（`walk_d02.result.json`，16/16）

1400×900 與 390×844 各走一次：

1. 檔案 → 新專案。物件畫布的教學卡按「知道了」。
2. 工具列「多邊形 P」。進入面內重畫外環，**面內首次教學卡保持開著**（`LESSON_OPEN_IN_REDRAW`）。
3. 在教學卡下方 48 px、視口 25% 與 60% 寬處點兩點。390 px 時再把游標移到卡下緣 12 px（舊的 −30 px 定位會撞卡）。
4. 鍵入 `12`。`#feLenInput` 顯示 12、在視口內（`TYPED_VALUE_VISIBLE`），不疊 `#faceCanvasHint`、`.cx-cur`、縮放控制與座標讀數（`TYPED_CLEAR_OF_BLOCKERS`，overlaps 為空）。截圖見 `screens/D02-*-1-typed-12*.png`。
5. 游標移到視口右下角，量測結果同上（`BOTTOM_RIGHT_CLEAR`）。
6. 按 ↓。最後一段為 (0, 12)，鍵入欄隱藏（`ARROW_APPLIES_12`）。
7. 再鍵入 12，按 Esc。只清掉鍵入，草稿點數不變，教學卡仍開著（`ESC_CLEARS_TYPED_ONLY`）。
8. 全程零寫入（`TYPED_ZERO_WRITE`、`ALL_ZERO_WRITE`）。

### D06：PDF `h` 閉合後接續的線段（`walk_d06.result.json`，11/11）

夾具是 `pdf/h-then-line.pdf`，由 repo 的 `pdf_snap_close_fixtures.py` 產生，SHA-256 `72692ee7…0a06`，與 `pdf/manifest.json` 相符。第 2 頁路徑為 `60 40 m 300 40 l 300 140 l 220 140 l 220 200 l 60 200 l h 40 40 l S`：`h` 之後的 `40 40 l` 從子路徑起點 (60,40) 接續。

1. 新專案 → 範例 → 點面 1 卡 → 進入。
2. 右欄「底圖」→「匯入 PDF／圖片」→ 點第 2 頁縮圖 →「加入位置」選「建立描繪用面」→「加入參考頁」。得到面 2，頁碼 2（`PAGE2_NEW_TRACE_FACE`）。
3. 校準：點比例線兩端 (60,200)、(260,200)，輸入 2000 → 套用。結果為 10 mm／單位（`CALIBRATED_10MM_PER_UNIT`）。
4. 「外環 E」，吸附開著。
   - **修正點**：在 `h` 後那條線的端點（頁面 (40,180)）偏右 6 px、偏上 1 px 處點一下。自由落點是 (429, 1795) mm，草稿起點吸到 **(400, 1800)**（`SNAP_TO_ENDPOINT_AFTER_H`）。修正前 `h` 後的線段沒有被收進吸附特徵。
   - **對照**：同樣偏移點在 (40,160)，附近沒有 PDF 端點。草稿起點被格點吸到 (500, 1500)，不是 400（`CONTROL_NOT_SNAPPED_TO_400`）。這證明 (400,1800) 來自 PDF 端點，不是格點。
   - 按 Esc 放棄草稿，零寫入（`PROBE_ZERO_WRITE`）。
5. 照描 L 形六角，每點偏 3／−2 px。草稿階段零寫入（`TRACE_DRAFT_ZERO_WRITE`）。
6. 按 Enter。外環六邊為 2400／1000／800／600／1600／1600，記一筆歷史（`TRACED_EDGES`）。
7. 面內「復原」、「重做」（`UNDO`、`REDO`）。
8. 另存（`d06.gcanvas`）。新瀏覽器、新專案 → 開啟專案：外環逐點相同；面 2 的底圖是第 2 頁，比例 10 mm／單位（`COLD_OUTLINE`、`COLD_UNDERLAY_AND_SCALE`）。

### D09：工程規格表單顯示既有本面覆寫（`walk_d09.result.json`，14/14）

1. 新專案 → 檔案 → 範例 ▸ →「試用工程規格現成專案…」。工作區讀取完成（`EXAMPLE_WORKSPACE_READY`）。
2. 展開「本面覆寫與恢復沿用」，縫寬一開始是「沿用來源」（`INITIAL_INHERIT`）。
3. 縫寬改為「改成本面數值」，輸入 4 →「預覽套用」，零寫入 → 勾核對 →「確認套用」。記一筆歷史；場景的 application overrides 為 `gap: literal 4`（`CONFIRM_ONE_HISTORY`）。
4. **修正點**：同一次開啟中，表單顯示「改成本面數值」4（`SAME_OPEN_SHOWS_4`）。關閉後從「檔案 → 工程規格 · 面材與角材」重開，仍顯示 4（`REOPEN_SHOWS_LITERAL_4`）。21c-4 當時這裡顯示「沿用來源」。
5. 不改任何欄位，直接預覽：顯示「核對 0 項版本或定義變更」並列出「保留的覆寫 · gap literal 4」，零寫入（`UNEDITED_PREVIEW_ZERO_CHANGE`）。按「返回修改」，零寫入（`CANCEL_ZERO_WRITE`）。
6. 關閉，按工具列「復原」。場景回到確認前，表單回到「沿用來源」（`UNDO_RESTORES_SCENE`、`UNDO_FORM_INHERIT`）。
7. 按「重做」。場景與確認後相同，表單回到 4（`REDO_*`）。
8. 另存（`d09.gcanvas`）。用新瀏覽器、**390×844** 開新專案 → 開啟專案：場景與確認後逐字相同，表單顯示 4，欄位在視窗內（`COLD_SCENE_EQUAL`、`COLD_390_SHOWS_4`）。

### R02 PF-4A：預覽與主格表改為可讀表（`walk_pf4a.result.json`，16/16）

前置步驟沿用 `evidence/l4-cloud-20261121a/scripts/walk_pf4a.js` 的一般入口：

1. 新專案 → 檔案 → 工程規格 →「建立面材規格」100×200 → 預覽 → 核對 → 確認 → 關閉。
2. 工具列「矩形」拖出面 → 雙擊進入 → 屬性 →「面設定…」→「完成面與鋪排…」。
3. 勾鋪排 →「準備新的 8 mm 門檻欄位…」（參數卡預覽、確認、返回）→ 填完成面、正排鋪排、縫 3，勾宿主並填 h 30 → 預覽。

量表的方法：只看可見的 `table.pf-readable-table`。表頭要逐字等於指定的欄名，每格表頭用 Range 量測要恰好一行，且 `writing-mode` 是 horizontal-tb。表格不得寬過卡片或視窗。數字要以完整 token 判定，前後不得接英數或連字號，且不得跨行；材料 UUID 不算數字。

- **前置預覽**：完成面、鋪排、派生宿主三張「欄位／確認前／候選後」表都可讀（`PREP_DEFINITION_TABLES_READABLE_1400`）→ 確認。
- **主格預覽**：再開表單 → 勾「建立跟隨此鋪排的主格」→ 主支「沿 u」→ 預覽，出現四張表（`GRID_PREVIEW_TABLES_READABLE_1400`）。「主格 #1」表的「主支偏好」列為「不存在 → 沿 u」，並保有 `lattice.u.baseCoordinate` 等原生欄位路徑（`GRID_PREVIEW_LABELS`）。
- **改視窗 390×844**：按右欄切換鈕，四張表仍可讀（`GRID_PREVIEW_TABLES_READABLE_390`，`screens/PF4A-2-grid-preview-390.png`）。改回 1400，零寫入（`RESIZE_ZERO_WRITE`）。
- **取消與確認**：取消，零寫入且沒有主格（`GRID_CANCEL_ZERO_WRITE`）。再預覽 → 確認，記一筆歷史，主格 #1 `main-along u`（`GRID_CONFIRM_ONE_HISTORY`）。
- **來源主格原生值表**：再開表單，展開「來源主格 #1」。表頭為「欄位／原生值」，可讀（`GRID_RESULT_TABLE_READABLE_1400`）。
- **改鋪排原點 u 0→10**：預覽四張表可讀（`SOURCE_EDIT_TABLES_READABLE_1400`）。主格表的「週期基準 · u 軸 · 基準座標（mm）」是 **101 → 111**（`SOURCE_EDIT_SHOWS_BASIS_BEFORE_AFTER`）→ 取消，零寫入（`SOURCE_EDIT_CANCEL_ZERO_WRITE`）。
- **冷開**：另存（`pf4a.gcanvas`）。新瀏覽器 390×844 → 開啟專案，場景相同（`COLD_SCENE_EQUAL`）→ 進入面 → 同一表單的「來源主格 #1」表可讀（`COLD_GRID_RESULT_READABLE_390`）。

### R17：D16a／P1-A 中文診斷（`walk_r17.result.json`，10/10）

1400×900 與 390×844 各走一次：

1. 新專案 → 檔案 → 開啟場景檔 `scripts/r17-rect.scene`（1000×1000 矩形面，沿用 21a）。
2. 點面卡 →「進入」。390 px 時先按面內「檢查器」切換鈕。
3. 構件 → 角材 → 放置方式「兩支互頂壁邊材」。第 1 支選 e0、第 2 支選 e2，都設 A 27、B 20、+u、+n → 預覽。
4. 影響視窗出現 `角材 1 · D16a`（`D16A_DIALOG`）。「預期」列為「**兩個真實端面須法向相反、位於同一平面，且有正長度接觸。**」，不含英文原句（`EXPECTED_ZH`）。確認鈕停用（`CONFIRM_DISABLED`）。
5. 該段文字沒有被裁切，也沒有橫向溢出（`EXPECTED_NOT_CLIPPED`；390 px 時寬 305 px）。
6. 取消：零寫入，沒有任何 `timber` 行（`PREVIEW_CANCEL_ZERO_WRITE`）。

依 #443 的設計，「實際」列仍是原生原文（`timber 1 [0,1000] 與 timber 2 [0,1000] 沒有恰一組相向端點…；P1-A：不互頂即整筆拒絕`），只有「預期」轉成中文。

### R11：物件畫布觸控第一片（`walk_r11_touch.result.json`，30/30）

先開新專案 → 範例 → 物件畫布 →「顯示全部」（滑鼠）。觸控全部用 `Input.dispatchTouchEvent`。

1. **長按面卡**（1400 與 390）：
   - 約 250 ms 出現進度環，選單未開。約 400 ms 時選單仍未開。約 700 ms 開出 sheet（`LONG_PRESS_RING_THEN_MENU`）。
   - sheet 標題「面 1」，項目為開啟／定位／刪除／在右欄查看（`LONG_PRESS_CARD_ITEMS`）。
   - 放開後選單仍在，沒有補發 trusted click，也沒有進入面（`RELEASE_KEEPS_MENU_NO_OPEN`）。
   - sheet 在視窗內（`SHEET_INSIDE_VIEWPORT`），零寫入（`LONG_PRESS_ZERO_WRITE`）。
   - 用手指點「定位」，執行後選單關閉，零寫入（`TAP_MENU_ITEM_RUNS_CLOSES`）。
2. **長按空白**（1400 與 390）：
   - 選點條件：命中元素是 `#ocv`，且離卡片與控制項至少 40 px。觀測到的 touchstart 落點不是卡片（`BLANK_POINT_IS_CANVAS`）。
   - 開出「物件畫布」sheet：回到原點／顯示全部／建立物件／格點吸附／顯示背景格點，沒有「刪除」（`LONG_PRESS_BLANK_VIEW_MENU`）。
   - sheet 在視窗內。按 Esc 關閉，零寫入（`BLANK_*`、`ESC_CLOSES_BLANK_MENU`）。
3. **短按卡片**（1400）：只選取（`oc.sel` 為 boundary 1），不開選單、不進入面、零寫入（`SHORT_TAP_SELECTS`）。
4. **手指在卡上移動 12 px 再到 60 px**（1400）：
   - 不開選單，也沒有進度環（`MOVE_OVER_8_CANCELS_LONG_PRESS`）。
   - 卡片照原單指拖曳移動 77.7 px，場景只多一行 `canvas-pos boundary 1 100 60`（`DRAG_MOVES_CARD`）。
   - 再用滑鼠把同一張卡拖回 −60 px，場景回到拖曳前（`DRAG_SAME_AS_MOUSE_PATH`）。兩條路徑都不經面內歷史（undo 深度不變），與滑鼠原行為一致。
5. **雙指**（1400，在空白處）：張開後縮放比為 **1.500**；兩指平移後 panX +**60**、panY 0（`PINCH_ZOOM_1_5`、`TWO_FINGER_PAN_60`）。不開選單，場景不變（`TWO_FINGERS_NO_MENU_NO_WRITE`）。
6. **雙擊卡片**（1400）：照原雙擊語意進入面 1，不開選單（`DOUBLE_TAP_ENTERS_FACE`）→ 返回。

截圖：`screens/R11-*-1-card-sheet.png`、`-2-blank-sheet.png`、`R11-1400-3-after-pinch-pan.png`。

## 發現（只記錄，不修）

**23-1　D02 面內首次教學卡蓋住畫布上方一塊可畫區域。** 21c-1 的原點位是面內 mm (2000, 0)，在 1400 與 390 px 下，這一點都落在 `#faceCanvasHint` 內（`walk_d02.result.json` 的 `originalSecondPointHit`）。#443 內文所說原 driver 在 1400×900 的第二點 (670,209) 落在教學卡，也是同一件事。

- 重現：新專案 →「多邊形 P」→ 不關教學卡 → 在 (0,0) 點一下 → 移到 (2000,0)。
- 結果：那一點點到的是卡，不是畫布。
- 鍵入長度欄本身已經不會被蓋住（本次 D02 通過）。
- 這是教學卡與畫布的版面取捨，條文沒有規定。這裡只記錄，不判定為缺陷。

## 未核對範圍

- **D02**：主畫布「矩形 R」、各吸附間距。
- **D06**：圖片底圖、390 px 照描、其他閉合變體（`re`、曲線、`double-h`、`h-then-move`）。
- **D09**：spec 名稱與材料版本覆寫的顯示、截面覆寫。
- **PF-4A**：交丁、結構側 −N、兩份鋪排、障礙、主支「沿 v／未設定」。
- **R17**：13 mm 牆階正例（11-21 已核）、有下游的整組刪除。
- **R11**：
  - 實體觸控與手機（iOS／Android），包括真實手指的接觸面積、OS 長按手勢、iOS callout。CDP 觸控不等於實機。
  - sheet 的鍵盤操作、短視窗（390×250）、忙碌時的停用原因、第二指加入時取消第一指。
  - 面內、空間、三視圖的觸控。
- **全部**：Windows 本機、`start.ps1`、原生檔案對話框、中文輸入法、使用者驗收（L5）。

## 證據核對

`python3 -I scripts/verify_evidence.py main-ea16e3f5` 的結果是 `{"ok": 36, "fail": 0}`。它核對四件事：

- 25 張截圖，雜湊對原始位元組。
- 三份另存的 `.gcanvas`，比對雜湊與大小。
- PDF 夾具與 manifest。
- 六份結果檔的 checks 都通過，且計數一致。

負控：在 `d09.gcanvas` 尾端多加一個位元組後重跑，回報 `FAIL walk_d09.result.json: saved d09.gcanvas mismatch`，exit 1。

## 檔案

- `scripts/`：
  - `lib.js`：CDP 輸入與唯讀觀測。
  - `walk_{d02,d06,d09,pf4a,r17,r11_touch}.js`。
  - `run_one.sh`、`run_all.sh`、`serve-wt.sh`（沿用 #449）、`verify_evidence.py`、`r17-rect.scene`（沿用 21a）。
- `main-ea16e3f5/`：
  - `walk_*.result.json`、`walk_*.log`。
  - `runtime-probe.json`、`runtime-probe.after.json`、`worktree-state.txt`。
  - `pdf/`（夾具與 manifest）、`screens/`（25 張 PNG）。
  - `d06.gcanvas`、`d09.gcanvas`、`pf4a.gcanvas`。
