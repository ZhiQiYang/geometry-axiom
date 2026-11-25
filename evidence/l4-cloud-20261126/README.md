# 雲端實機核對：R16 U123-H:A 畫布高度（PR #448）與 R03 第二片未核對項（main b3c4b981，2026-11-26）

API worker 依 issue #455 任務 T7（留言 7169924221）在 main `b3c4b981bb96b118c1c05b7a1bd98062d710c8b2` 用真 Chrome 走兩件事：

- **A. R16 U123-H:A**：[PR #448](https://github.com/ZhiQiYang/geometry-axiom/pull/448) 的合併提交就是 `b3c4b981`（`git log`：parents `c432983b…`、`a2620da6…`，提交時間 2026-11-26 00:48:22 +0800）。依 [#123 決策 6436164902](https://github.com/ZhiQiYang/geometry-axiom/issues/123#issuecomment-6436164902) 的正常態畫布高度，在 1400×900、390×844、320×844 各走一次六個工作區，量畫布高度與工具列控制的中心點命中。
- **B. R03 第二片未核對項**（需求帳 R03 列「第二片未核對」）：其餘三個起鋪角、板長沿 u、2500×3000、配方新增／複製／刪除、復原後的一般畫面。每項都走「預覽 → 取消零寫入 → 再預覽 → 確認一筆歷史 → 復原／重做 → 另存 → 新服務程序＋新瀏覽器冷開」。

做法與證據格式沿用 `evidence/l4-cloud-20261123/`。這次只新增本目錄、改 `需求帳.md` 的 R16、R03 兩列與新增的核對小節。產品碼、`公理層.md`、時限、斷言都沒有改。

## 結論

| 項目 | 層級 | 核對 | 結果 |
|---|---|---:|---|
| A. R16 U123-H:A 正常態畫布高度 | **L4**（高度） | 三尺寸×七個繪圖節點全過 | 1400×900 每個節點可用高度 ≥812（主畫布、面內、空間平面圖、空間投影、三視圖都是 812，完整網格與 3D 是 844）；390×844、320×844 ≥716（前五個 716，完整網格與 3D 748）。都沒有非繪圖 UI 覆蓋、25 點取樣全中、沒有頁面橫向溢出；教學卡開著時也一樣 |
| A. R16 工具列控制中心點命中 | 1400：**L4**；390／320：**未通過，維持 L3** | 170/174 | 1400 全部控制中心點命中。390、320 只有完整網格的 `#igName`（設定區的網格名稱欄）點不到：它在視窗下方（top 912 > 844），滾輪與觸控都捲不到（發現 26-1）。其餘控制都命中，部分要先捲動 dock 或工具列 |
| B. R03 其餘三個起鋪角（3740×3301，沿 v） | **L4** | 3×（18＋8） | 右上、左下、右下各 53 支，與 oracle 逐支相同；七步全走通，冷開 generatorInvocations 0 |
| B. R03 板長沿 u（1680×3880） | **L4** | 18＋8 | 28 支，與 oracle 及凍結 F4 走道 golden（平移後）逐支相同 |
| B. R03 2500×3000（沿 v） | **L4** | 18＋8 | 30 支，與 oracle 逐支相同 |
| B. R03 配方新增／複製／刪除 | **L4** | 24＋8 | 新增與複製是零寫入草稿，保存與刪除各一筆歷史、場景不變；冷開後兩份配方原樣 |
| B. R03 復原後的一般畫面 | **L4** | 6 項各 1 | 6 個項目都核：復原後物件畫布清單與卡片、面 1 圖層與角材命中點、三視圖角材數，與預覽前基準逐項相同（沒有「承載面」、三視圖 0 支） |

B 合計 162/162（第一階段 114、第二階段 48）。A 是 170/174。

這是雲端實機操作，屬 L4 範圍，不是使用者驗收（L5）。各數字只代表結果檔 `checks` 逐項寫下的判準，不推廣到其他輸入、尺寸或裝置。

## 環境與方法

- **工作樹**：兩個乾淨的 main `b3c4b981` 工作樹（A 用 `/tmp/l4w/wt`、B 用 `/tmp/l4w/wt2`），都以 sparse-checkout 排除 `evidence/`、`tests/evidence/`。跑完後兩個 HEAD 仍是 `b3c4b981…`，`git status --short` 都是 0 行（`main-b3c4b981/worktree-state.txt`）。
- **服務**：`scripts/serve-wt.sh`。改自 `l4-cloud-20261123` 版，差異只有兩點：本機沒有 `/opt/node24`，改用 PATH 上的 node（仍檢查 `v24.`），並加 `pipefail`。以非 root 使用者 `apiworker`（uid 1002）執行，`ulimit -s 16384`，`LANG=C.UTF-8`，Node v24.22.3，`GEOMETRY_FEEDBACK_DIR` 在 `$TMPDIR`（`/tmp/l4w/tmp`）底下。先 `start_local.py --build-only`，再 `start_local.py --port <port>`。
  - A 用 port 18881，跑前重啟一次。
  - B 用 port 18871，**每個項目、每個階段前都重啟**，所以每個冷開都在新的服務程序（新 pid、新 session）。
- **Probe**：每次重啟後都跑 `runtime_version.py --probe`，不是 `fresh:true` 就停。全部 probe 都是 version `b4814c2e8615c27db57cd73005e0020192a0ea64c6f2c01989f3c6bd984a1f5c`、`fresh:true`（`r16/runtime-probe*.json`、`r03/runtime-probe.<項目>.phase{1,2}.json`）。
- **瀏覽器**：Google Chrome 157.0.8103.78（`/usr/bin/google-chrome`，headless、`--no-sandbox`），由 Playwright 1.65.1（`playwright-core`，暫存於 `/tmp/nodetools`，不進 repo）啟動。A 每個尺寸開新瀏覽器與 profile；B 每個項目、每個階段各開一個。
- **輸入全部經 CDP**（`scripts/lib.js`，原樣沿用 `l4-cloud-20261123`）：滑鼠 `Input.dispatchMouseEvent`、鍵盤 `Input.dispatchKeyEvent`。下拉選單：點一下、Esc、方向鍵。開檔由 Playwright filechooser 回填，觸發它的點擊仍是 CDP。
- **捲動**：一律用 CDP 滾輪，不呼叫 `scrollIntoView`。A 另寫 `revealCtl`：找出把控制裁掉的最近捲動容器，在容器內「不在繪圖節點上、且最近的同軸捲動祖先就是該容器」的點送滾輪（直向 deltaY、橫向 deltaX），每步捲動量是被裁掉的像素＋2（上限 120），直到 controlProbe 的五點都命中或 30 步。
- **`page.evaluate` 只做唯讀的事**：量測函式（下述）、DOM 文字與位置、`dump`、`engineering-read`、`identity-read`、`panel-fill-read`、`newid`、`ReferenceWorkspace` 歷史與附件、唯讀 `POST /framing-template/read`（`generatorInvocations`）、`/runtime`。唯一改瀏覽器屬性的是 `noPickers()`（同前，讓另存走下載、開檔走 `<input type=file>`）。
- **零寫入**：
  - A：場景 dump 的 SHA-256 與工程修訂號不變。
  - B：場景 SHA-256、工程修訂號、身分帳、歷史 undo／redo 深度與末筆、配方附件、鋪排修訂號、id 高水位全部不變（同 r03a 的 `cp`）。
- **雜湊**：一律對檔案原始位元組計算。

### A 的量測判準

- **高度**（DOM-CONTRACT.md「R16 U123-H:A 正常態畫布高度」）：寬 >560 時 V−88，≤560 時 V−128，V 是 `innerHeight`。1400×900 → 812；390×844、320×844 → 716。
- **量法**：`scripts/r16_surface_probe.js` 是 main `geometry-web/canvas_sections/P1231.js:112-182` 的 `surfaceProbe` 逐字複製（P1231.js SHA-256 記在結果檔 `probeSources`）。可用高度＝實際繪圖節點 bbox 與視窗、各層 overflow 裁切的交集，且沒有非繪圖 UI 覆蓋（`obstructions` 為空、25 點取樣都打到繪圖節點），沒有頁面橫向溢出。
- **控制可達**：控制清單與 P1231.js:36-65 相同；量法用 repo 的 `tests/diagnostics/r16_control_probe.cjs`（`controlProbe`，SHA-256 也記在 `probeSources`）。判定是任務指定的**中心點命中**：控制可見、在視窗內，且中心點的 `elementFromPoint` 落在控制或其子節點。controlProbe 另外四個內縮點沒命中的，記成 `edgeMisses`，不改判定。
- **狀態**：進入工作區時若有開著的首次教學卡，先量「教學開著」一次（`teaching-open`），再以 CDP 點「知道了」，量正常態（`normal`）。沒有教學卡的工作區只量 `normal`。
- **夾具**：新專案 → 檔案 →「開啟場景檔… .scene」選 repo 的 `room_box.scene`（面 1、面 2、空間 1）。
- **六個工作區的入口**（都經一般 UI）：
  - 主畫布 `#ocv`：開檔後的物件畫布。
  - 面內 `#faceEditorSvg`：「顯示全部」→ 面 1 卡片「進入 ›」。390／320 px「顯示全部」後卡片縮成 compact、「進入」隱藏，改用卡片雙擊（既有語意）。
  - 空間平面圖 `#spacePlanSvg`、空間投影 `#spaceProjSvg`：Esc 取消面 1 選取 → 「顯示全部」→ 空間 1 卡片（同上）→「平面圖」／「投影」分頁。
  - 三視圖 `#cv`：頂列「三視圖」。
  - 完整網格 `#igGridView`：物件庫「網格系統」（390／320 px 先開左側物件庫），量完「捨棄原始草稿」。
  - 3D 模型 `#smCanvas`：檔案 → 範例 ▸ →「從面建立 3D 空間 · 現成範例」，等到預覽。

### B 的項目

| 項目 | 尺寸 | 起鋪角 | 板長沿 | 預期支數（設計 7065012645） |
|---|---|---|---|---:|
| corner-max-min | 3740×3301 | 預覽圖右上 | v | 53 |
| corner-min-max | 3740×3301 | 預覽圖左下 | v | 53 |
| corner-max-max | 3740×3301 | 預覽圖右下 | v | 53 |
| along-u | 1680×3880（凍結 F4 走道的尺寸） | 左上 | u | 28 |
| size-2500x3000 | 2500×3000 | 左上 | v | 30 |
| recipes | 3740×3301 | 右下（「副本」配方） | v | 53 |

每個項目第一階段的操作（`scripts/walk_r03b.js`，改自 r03a 的 `walk_r03a.js`）：

1. 新專案 → 工具列「矩形 R」在 `#ocv` 內拖出 → 右欄「外環邊」打兩邊長 → 放置原點 0／0／2500、u +x、v +y。
2. 左欄點「面 1」→「進入面內工作區」→ 屬性 → 面設定… → 完成面／骨架… → 面內工作切「平釘天花骨架（政策 A 固定治具）」。
3. 「準備板材來源／返回骨架」→ 工程規格建面材 915×1830×6 → 預覽 → 勾核對 → 確認 → 返回。「獨立建立 8 mm 門檻 X」→ 預覽 → 確認 → 返回。
4. 配方：名稱、六個預設（915／1830／2／27／33／367）、起鋪角、板長沿 →「保存配方」（場景不變、歷史 +1、末筆 `local`）。recipes 項見下。
5. 關閉工作區 → **一般畫面基準**：物件畫布清單與卡片、面 1 面內圖層與角材命中點、三視圖角材 id 數。
6. 回到同一入口、選回配方 → 明選框架「放置面 1」、板材 v1、X、勾 RC →「預覽整組骨架」。
7. 「取消本次生成」→ 零寫入，恰一次 cancel、沒有 confirm。
8. 再明選 → 再預覽（與第一次逐列相同、零寫入）→「確認骨架（一筆歷史）」。
9. 關閉 → 面內「復原」→ **復原後的一般畫面**，與第 5 步基準逐項比對 → 面內「重做」（場景與確認後逐字相同、沒有 preview 請求）→ 三視圖角材數。
10. 檔案 → 另存新檔…（下載後備路徑）→ `<項目>.gcanvas`。

第二階段（每項都先重啟服務）：新瀏覽器 profile → 檔案 → 開啟專案… → 場景逐字相同、配方附件深相等、開檔沒有任何 `/framing-template/*` 請求、`generatorInvocations` 0 → 三視圖角材數與重做後相同 → 回到同一入口開骨架：配方在、三個來源空白、零寫入、沒有 preview／confirm。

**recipes 項的配方操作**：

1. 保存 A（左上／v）。
2. 「新增配方」：草稿、零寫入、預覽停用。名稱 B、起鋪角右下 → 保存，共 2 份，A 原樣。
3. 「複製為新配方」：草稿「… B 副本」、零寫入 → 保存，共 3 份，新 id，預設與偏好同 B。
4. 下拉選 A →「刪除所選配方」：場景不變、歷史 +1，剩 B 與「B 副本」，下拉不再有 A。
5. 選「B 副本」走完整流程。

**oracle 對照**：`scripts/oracle_compare_r03b.py`。App 預覽表逐支 (kind, 矩形, 長度) 與 `geometry-core/framing-template/oracle/framing_oracle.py` 對同一外環、同一偏好的輸出比對；參數與版面換算同 `tests/test_framing_template.py::assert_oracle`。along-u 另與 `oracle-golden.json` 的 F4 走道（同 layout）平移後逐支比較。

## 逐項結果

### A. R16（`r16/walk_r16_height.result.json`，170/174）

`python3 -I scripts/summarize.py main-b3c4b981` 的表（可用高度單位 px；「需捲動」是要先用滾輪捲動才命中的控制數）：

| 尺寸 | 工作區 | 狀態 | V | 下限 | 可用高度 | 遮蔽 | 控制數 | 中心未命中 | 邊點未命中 | 需捲動 |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| 1400×900 | main | teaching-open | 900 | 812 | 812 | 0 | 18 | — | — | 0 |
| 1400×900 | main | normal | 900 | 812 | 812 | 0 | 18 | — | — | 0 |
| 1400×900 | face | teaching-open | 900 | 812 | 812 | 0 | 23 | — | — | 2 |
| 1400×900 | face | normal | 900 | 812 | 812 | 0 | 23 | — | — | 3 |
| 1400×900 | space-plan | normal | 900 | 812 | 812 | 0 | 10 | — | — | 0 |
| 1400×900 | space-projection | normal | 900 | 812 | 812 | 0 | 8 | — | — | 0 |
| 1400×900 | three-view | normal | 900 | 812 | 812 | 0 | 15 | — | — | 0 |
| 1400×900 | full-grid | teaching-open | 900 | 812 | 844 | 0 | 9 | — | — | 0 |
| 1400×900 | full-grid | normal | 900 | 812 | 844 | 0 | 9 | — | — | 0 |
| 1400×900 | 3d | normal | 900 | 812 | 844 | 0 | 8 | — | — | 0 |
| 390×844 | main | teaching-open | 844 | 716 | 716 | 0 | 18 | — | — | 6 |
| 390×844 | main | normal | 844 | 716 | 716 | 0 | 18 | — | — | 5 |
| 390×844 | face | teaching-open | 844 | 716 | 716 | 0 | 23 | — | — | 12 |
| 390×844 | face | normal | 844 | 716 | 716 | 0 | 23 | — | — | 13 |
| 390×844 | space-plan | normal | 844 | 716 | 716 | 0 | 10 | — | — | 0 |
| 390×844 | space-projection | normal | 844 | 716 | 716 | 0 | 8 | — | — | 0 |
| 390×844 | three-view | normal | 844 | 716 | 716 | 0 | 15 | — | — | 2 |
| 390×844 | full-grid | teaching-open | 844 | 716 | 748 | 0 | 9 | #igName | — | 1 |
| 390×844 | full-grid | normal | 844 | 716 | 748 | 0 | 9 | #igName | — | 1 |
| 390×844 | 3d | normal | 844 | 716 | 748 | 0 | 8 | — | — | 0 |
| 320×844 | main | teaching-open | 844 | 716 | 716 | 0 | 18 | — | — | 11 |
| 320×844 | main | normal | 844 | 716 | 716 | 0 | 18 | — | — | 10 |
| 320×844 | face | teaching-open | 844 | 716 | 716 | 0 | 23 | — | — | 13 |
| 320×844 | face | normal | 844 | 716 | 716 | 0 | 23 | — | — | 14 |
| 320×844 | space-plan | normal | 844 | 716 | 716 | 0 | 10 | — | #workspaceBackButton | 0 |
| 320×844 | space-projection | normal | 844 | 716 | 716 | 0 | 8 | — | #workspaceBackButton | 0 |
| 320×844 | three-view | normal | 844 | 716 | 716 | 0 | 15 | — | — | 5 |
| 320×844 | full-grid | teaching-open | 844 | 716 | 748 | 0 | 9 | #igName | — | 1 |
| 320×844 | full-grid | normal | 844 | 716 | 748 | 0 | 9 | #igName | — | 1 |
| 320×844 | 3d | normal | 844 | 716 | 748 | 0 | 8 | — | — | 0 |

- 1400 px：面與空間卡片用「進入 ›」；完整網格入口在物件庫裡直接看得到。
- 390、320 px：「顯示全部」後卡片是 compact，用雙擊進入；完整網格要先開左側物件庫。
- 面內 1400 px 的「工具說明」（`#feSelectionSummaryHelp`）和「平移」在工具列右端被裁掉一部分，要先橫向捲動工具列（需捲動 2～3 個）。
- 390、320 px 主畫布的 dock 在頂列，只有一列高，要直向捲動才看得到矩形、多邊形與縮放鈕（需捲動 5～11 個）。這是 DOM-CONTRACT「可由既有入口及容器正常捲動」允許的情況，判定為命中。
- 320 px 的空間平面圖與投影：「物件畫布」返回鈕（`#workspaceBackButton`）中心點命中，但右緣內縮 5 px 那一點打到 `#workspaceToggleLeft`（記在 `edgeMisses`，不改判定）。
- 零寫入：主畫布、面、空間、三視圖走完後，場景 SHA-256、修訂號、undo／redo 都不變。開完整網格再捨棄草稿後，場景與修訂號不變，但歷史多了兩筆 `local`（undo 2→4）。3D 預覽後同樣不變。這兩筆只記錄，不判定。
- 截圖：`r16/screens/R16-<工作區>-<寬>-{1-teaching,2-normal}.jpg`，共 30 張。

### B. R03（`r03/walk_r03b.<項目>.phase{1,2}.result.json`）

| 項目 | 第一階段 | 第二階段 | 預覽 | 另存 bytes／SHA-256 前 12 碼 | 重做後／冷開三視圖 | 冷開 generatorInvocations |
|---|---:|---:|---|---|---|---:|
| corner-max-min | 18/18 | 8/8 | 候選 53 支 · 確認前未寫入 | 12191／`2be7b5b2247f` | 53／53 | 0 |
| corner-min-max | 18/18 | 8/8 | 候選 53 支 · 確認前未寫入 | 12200／`dcec7c58dd0c` | 53／53 | 0 |
| corner-max-max | 18/18 | 8/8 | 候選 53 支 · 確認前未寫入 | 12206／`5e38631eb63c` | 53／53 | 0 |
| along-u | 18/18 | 8/8 | 候選 28 支 · 確認前未寫入 | 8111／`d6d340d23259` | 28／28 | 0 |
| size-2500x3000 | 18/18 | 8/8 | 候選 30 支 · 確認前未寫入 | 8663／`4b9908ea0169` | 30／30 | 0 |
| recipes | 24/24 | 8/8 | 候選 53 支 · 確認前未寫入 | 12689／`f91cbdf0cd31` | 53／53 | 0 |

- 每項第一階段都有：`RECT_PLACED`、`SOURCES_READY_V2`、配方保存一筆 `local` 歷史、`PREVIEW_MEMBER_COUNT`、`PREVIEW_REQUEST_LAYOUT`（恰一筆 v2 preview）、`PREVIEW_TABLE_MATCHES_DIAGRAM`、`PREVIEW_ZERO_WRITE`、`CANCEL_ZERO_WRITE`、`CANCEL_SENT_NO_CONFIRM`、`PREVIEW2_SAME_AND_ZERO_WRITE`、`CONFIRM_ONE_HISTORY`、`CONFIRM_LIVE_DEFINITIONS`（timber／place 各 N 行，場景沒有 framing-template／flat-ceiling 字樣）、`UNDO_ONE_STEP`、`UNDO_GENERAL_VIEW_EQUALS_BEFORE_PREVIEW`、`UNDO_GENERAL_VIEW_ZERO_WRITE`、`REDO_SAME_COMMIT_NO_SEARCH`、`REDO_THREE_VIEW_SHOWS_ALL`、`SAVE_IS_COMMITTED_STATE`。recipes 項用 7 項 `CRUD_*` 取代單一配方保存。
- 每項第二階段都有：`FRESH_PROCESS_AND_PROFILE`（新 pid、新 session、內建場景、無配方）、`COLD_FILE_IS_SAVED_FILE`、`COLD_SCENE_EXACT`、`COLD_RECIPE_EXACT`、`COLD_NO_SEARCH`、`COLD_THREE_VIEW_SHOWS_ALL`、`COLD_FORM_RECIPE_SOURCES_BLANK_ZERO_WRITE`、`COLD_FORM_NO_GENERATION`。
- 舊程序 `generatorInvocations` 都是 2（兩次預覽）。
- oracle（`r03/oracle-compare.json`）：6 項 App 支數＝oracle 支數，逐支 (kind, 矩形, 長度) 多重集合相等，寬×厚全是 27 × 33，oracle check 0 失敗、0 conflicts。along-u 與 F4 走道凍結 golden 平移 (−3170, −2970) 後 28 支逐支相同。
- 截圖：`r03/screens/R03B-<項目>-*.jpg`，共 118 張（含復原前後一般畫面的 `V-before-*`、`V-after-undo-*`）。


## 發現（只記錄，不修產品）

**26-1　390／320 px 完整網格：設定區用滑鼠滾輪或觸控滑動都捲不到（R16 控制可達性）。**

- 重現：390×844（或 320×844）→ 新專案 → 左上物件庫 →「網格系統」→ 在畫面任一處用滾輪向下捲，或用手指上滑。
- 結果：設定區的網格名稱欄 `#igName` 一直停在 top 912（視窗高 844），中心點不在視窗內。
  - 捲動容器是 `.ig-layout`（可見高 748、內容高約 2479），但它的可見區被兩樣東西蓋滿：網格畫布 `#igGridView`（`touch-action: none`，滾輪用來縮放）與右側 `#igHeightDock`（`overscroll-behavior: contain`）。
  - CDP 滾輪 30 步都捲不動（結果檔 `wheelContainers: ["ig-layout"]`）。
  - 探索時另用 CDP 觸控在 dock 與畫布各上滑 3 次，`.ig-layout` 的 `scrollTop` 都是 0。這只是探索輸出，沒有存成原件。
- 只作觀測：正常態下按 Tab 把焦點移到 `#igName` 後，它會進入視窗、中心點命中（結果檔 `tabObservation`）。手機沒有 Tab 鍵。
- 契約對照：DOM-CONTRACT 寫「手機仍先預覽、向下捲到設定」「控制可由既有入口及容器正常捲動到可見位置」。P1231 用 `scrollIntoView` 捲動，所以 CI 會過；這次的一般捲動做不到。
- 影響：手機寬度改不到網格名稱等設定，只能用 footer 的「預覽並建立」。不影響畫布高度。

**只記錄、不算發現**

- 320 px 空間返回鈕的右緣被 `#workspaceToggleLeft` 疊住約 5 px，中心點仍可點。
- 1400 px 面內工具列右端的「平移」「工具說明」要先橫向捲動才完整可見。
- 開完整網格再捨棄草稿，World 不變，但歷史多兩筆 `local`。
- R03 未發現新缺陷。#449 記的確認後一般畫面缺口（物件畫布與面內看不到骨架、宿主卡 1×1 mm、X 卡 0 處使用、1400 px 長度折行）這次沒有重驗。復原後的一般畫面本來就不含骨架，與預覽前相同。

## 腳本結束碼

- 所有腳本都是 `set -eo pipefail`。
- walk 任一核對項 FAIL 時，node 以 exit 1 結束；`run_one.sh` 經 pipefail 回非 0；`run_all.sh` 記 `rc=1`，其餘 walk 照跑，最後以非 0 結束。
- 本次 `run_all.sh` 的原始輸出在 `main-b3c4b981/run_all.log`。結果是 `walk_r16_height FAILED`、`run_all rc=1`、`exit=1`：R16 有 4 項 FAIL，所以非 0。R03 的 12 支 walk 與 oracle 對照都以 0 結束（沒有 FAILED 行）。

## 重現

```sh
git worktree add --no-checkout <wtA> b3c4b981bb96b118c1c05b7a1bd98062d710c8b2
(cd <wtA> && git sparse-checkout set --no-cone '/*' '!/evidence/' '!/tests/evidence/' && git checkout b3c4b981bb96b118c1c05b7a1bd98062d710c8b2)
# <wtB> 同上
# 非 root、TMPDIR 設好；NODE_PATH 指向含 playwright 的 node_modules（預設 /tmp/nodetools/node_modules）
TMPDIR=<tmp> bash evidence/l4-cloud-20261126/scripts/run_all.sh <wtA> <wtB> <輸出目錄（絕對路徑）>
python3 -I evidence/l4-cloud-20261126/scripts/verify_evidence.py <輸出目錄>
python3 -I evidence/l4-cloud-20261126/scripts/summarize.py <輸出目錄>
```

畫布上拖出的矩形位置取決於當下平移，重跑時外環座標可能不同；oracle 對照用實際外環。

## 證據核對

`python3 -I scripts/verify_evidence.py main-b3c4b981` 的輸出（`main-b3c4b981/verify.txt`）：

```
CHECK-FAIL r16/walk_r16_height.result.json: R16_CONTROLS_CENTER_full-grid_teaching-open_390
CHECK-FAIL r16/walk_r16_height.result.json: R16_CONTROLS_CENTER_full-grid_normal_390
CHECK-FAIL r16/walk_r16_height.result.json: R16_CONTROLS_CENTER_full-grid_teaching-open_320
CHECK-FAIL r16/walk_r16_height.result.json: R16_CONTROLS_CENTER_full-grid_normal_320
{"integrityOk": 224, "integrityFail": 0, "checkFail": 4, "runtimeVersion": ["b4814c2e8615c27db57cd73005e0020192a0ea64c6f2c01989f3c6bd984a1f5c"]}
verify exit=2
```

- exit 2 的意思是：完整性全部相符（截圖、另存檔、冷開檔、計數、probe fresh 與 version 一致、oracle ok），但有核對項 FAIL。
- 這次沒有做負控（改一個 byte 看 verify 會不會報錯）。

## 未核對範圍

- **R16**：
  - 560／561 邊界與 768×1024（P1231 有，這次沒走）。
  - 軟鍵盤、對話框／抽屜、繪製任務帶等例外狀態。
  - Tab 可達的完整稽核（只在未命中的控制上觀測）。
  - 簡式網格檢查器（G）。
  - 43 項的其餘項目。
  - 真手機與 visualViewport 縮放。
- **R03**：
  - F3／F4 凍結房的完整房間座標（along-u 只用 F4 的尺寸）。
  - 未知可讀版本唯讀、已知版本錯 pin 開檔拒絕。
  - 3740×2000 在 v2 的相容、M 改值。
  - 390 px 下的這些項目，以及確認後一般畫面的 #449 缺口重驗。
  - 退縫 FT02／R-butt、凹室、孔、柱樑、多面。
- **全部**：Windows 本機、`start.ps1`、原生檔案對話框（另存走下載、開檔走 `<input type=file>`）、實體觸控、中文輸入法、使用者驗收（L5）。

## 檔案

- `scripts/`：`lib.js`（原樣沿用 20261123）、`serve-wt.sh`、`run_one.sh`、`run_all.sh`、`walk_r16_height.js`、`r16_surface_probe.js`、`walk_r03b.js`、`oracle_compare_r03b.py`、`verify_evidence.py`、`summarize.py`。
- `main-b3c4b981/r16/`：`walk_r16_height.result.json` 與 `.log`、`runtime-probe.json`、`runtime-probe.after.json`、`screens/`（JPEG）。
- `main-b3c4b981/r03/`：每項 `walk_r03b.<項目>.phase{1,2}.result.json` 與 `.log`、`runtime-probe.<項目>.phase{1,2}.json`、`<項目>.gcanvas`、`oracle-compare.json` 與 `.log`、`screens/`（JPEG）。
- `main-b3c4b981/run_all.log`、`worktree-state.txt`、`verify.txt`。
