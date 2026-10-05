# 產品驗收報告:main `d6b4b45`(2026-10-05~06)

> 本目錄是一輪**黑箱產品驗收**的完整交接包,讀者是沒看過驗收對話、要接手修正的人(dot)。
> 所有路徑都相對於本目錄。**本輪未修改任何產品程式、測試或規格文件**;本分支只新增本目錄。

## 0. 標頭

| 項目 | 內容 |
|---|---|
| 被測 repo | geometry-axiom(GitHub 上的本 repo) |
| 被測版本 | main 完整 SHA `d6b4b450d741fcbbfd75c51631915d3082926990`(= PR #133 merge commit,2026-10-05 18:01 +0800) |
| 驗收日期 | 2026-10-05 夜間 ~ 2026-10-06 |
| 被測工作樹 | 獨立 detached worktree,驗收期間未改任何檔;每次起服務都以 `runtime_version.py --probe` 確認 `fresh:true`、版本指紋 `e2f2ee7b…`(見 `probes/`) |
| 環境 | Windows 11;MSVC 自編 bridge / core / model-base(放隔離 TEMP,檔名帶來源雜湊);`serve.py` 測試埠 8831–8837(每位驗收員一埠);無頭 Chrome 154、每輪全新 profile;桌面 1440x900 + 390x844 行動模擬(觸控 + Android UA) |
| 方法 | 只走正式 UI:CDP 送滑鼠/鍵盤/觸控事件、點正式按鈕後才經 file chooser 給檔、confirm 對話框照使用者按確定/取消。**未注入狀態、未呼叫 app 私有函式、未直接打 /api 改世界、未對隱藏 input 設檔**。讀 DOM 只做唯讀量測;對下載的 `.gcanvas` 只做唯讀解壓核對 |
| 分工 | T1 匯入+比例尺(8831)、T2 描輪廓+建空間(8832)、T3 多房間+網格/參數(8833)、T4 保存/重開(8834)、V1 複驗 T2-05(8836)、V2 複驗 T4-01(8837)、R1 讀碼根因(不起服務) |
| 限制 | ① 測試圖**全部為人工合成**(`fixtures/`),非真實案場;② 390 模擬 ≠ 實機 iPhone(輸入法、系統選檔、下載未驗);③ 保存只測**下載備援分支**(`fsAccess:'none'`),File System Access 原生對話框分支**未測**;④ 未測 Edge |

## 1. 結論

- **沒有阻斷主要流程的問題。** 8 個主幹流程在合成圖上都走得通,數值逐項核對吻合:
  - 校準 5000 mm 後 ROOM_A 四角讀數 5000×4000、**0 mm 誤差**(讀數為整數 mm);A3 底圖寬換算 21000 mm(理論 21000,重新校準差 0.019%)。
  - 建空間:矩形 **60 m³**(5000×4000×3000,6 面,牆 5.52 m³)、L 形 **78 m³**(26 m²×3000,8 面,牆 6.72 m³);改牆高 2700 → 54 / 70.2 m³,更新同一模型不新增;第二輪 L 邊改 6500 → 82.5 m³。
  - 保存 → 全新 profile + 重啟服務 → 開檔:**22 項逐項對照,除 T4-01 的兩項外全一致**(`findings/T4-roundtrip-table.md`);PDF 原檔 sha256 隨檔、校準數值逐位相同。
- **1 項資料遺失(次要)**:T4-01 — 走「以此底圖連續新增房間」(#77 共享來源)路徑後,底圖**不透明度/鎖定/取景**不保存,而且不必保存就會被重置、修改時也不標髒(V2 複驗擴大範圍)。
- **1 項幾何方向議題待拍板**:T2-05 — 照預設放置後俯視為南北鏡像;V1 確認鏡像成立但屬 GEO-244 明文設計(只提示、不自動改),77.647 m³「不只翻轉」的說法已駁回。
- 其餘皆**次要體驗**(假警報 toast、內部指令外露、返回鍵要按兩次、卡片疊住、拒絕無文字等),已依共用根因分 G1–G7。

## 2. 四段結果

### 2.1 已實際通過(合成圖)

| 流程 | 通過內容(摘要) | 證據 |
|---|---|---|
| 1 匯入 PDF | A3 橫向/A4 直 2 頁/`/Rotate 90`/issue54 5 頁:選頁、上下頁、縮圖、取景框;取消與 Esc 不留面;套用至既有面成為第 2 張參考頁;非 PDF/截斷/PNG 改名皆顯示明確錯誤且狀態乾淨 | `findings/T1-report.md`、`screens/T1/02-a3-dialog.png`、`screens/T1/03-a3-esc.png`、`screens/T1/05-a3-applied.png`、`screens/T1/104-rot90-applied-b.png`、`screens/T1/118-issue54-applied-to-face1.png`、`screens/T1/126-err-notpdf.png` |
| 2 比例尺 | 校準 5000 mm(與 500 cm 結果相同);12.55 cm/0/負數/文字拒絕、12.5 cm 接受;頁外點拒絕;取消各路徑不留殘點;讀數 0 誤差;A4 第 2 頁 T 形 1:100 校準 6000 吻合 | `findings/T1-report.md`、`screens/T1/18-calib-12.55cm-rejected.png`、`screens/T1/23-recalibrated-5000mm.png`、`screens/T1/25-measure-roomA.png`、`screens/T1/156-T-measure.png` |
| 3 描輪廓 | PDF 端點吸附描 ROOM_A/ROOM_L(缺口右上、無鏡像);鍵入長度 4000/2000/2000/3000/6000/5000;半自動候選改邊仍正交閉合;拖頂點/拖邊/Alt+拖切角正交一致;閉合:點起點、Enter、「完成外環」 | `findings/T2-report.md`、`screens/T2/020-A-closed-by-startclick.png`、`screens/T2/031-A-closed-by-enter.png`、`screens/T2/092-L-closed.png`、`screens/T2/128-typed-L-result.png`、`screens/T2/145-L-candidate-confirmed.png`、`screens/T2/137-alt-drag.png` |
| 4 建空間 | 60 m³ / 78 m³(對齊後俯視缺口右上)、改牆高 54 / 70.2 m³、六面盒 6 面封閉、取消不留半成品 | `findings/T2-report.md`、`screens/T2/075-after-create.png`、`screens/T2/079-height-updated.png`、`screens/T2/096-L-preview-top.png`、`screens/T2/101-box6-created.png`、`screens/V1/V29-aligned-top.png` |
| 5 多房間 | `#roomSourceCreate` → `#roomNew` 建 ROOM_L(26.00 m²、凹角正確);選取(單擊/Shift/左右框選/Ctrl+A/Esc);改房間 2 邊長不影響房間 1;刪除/Ctrl+Z;改名、解除列表關聯、基準變更標「需複核」 | `findings/T3-report.md`、`screens/T3/s08-L-applied.png`、`screens/T3/s53-selection.png`、`screens/T3/s51-f2-edge5-4500.png`、`screens/T3/s55-roomlist-after-delete.png`、`screens/T3/s13-unlinked.png`、`screens/T3/s18-list-after-ulX.png` |
| 6 網格/子網格/參數 | 無限網格 700x500 綁面 1(DOM 量 700.0/500.0)、相位差 350;子網格 u7×v4 / u5×v2、不可整除拒絕;面內有限網格依 L 裁切;參數卡 PANEL 寬 915→1000 連動網格與子網格;容量上限拒絕不改世界 | `findings/T3-report.md`、`screens/T3/s70-face1-with-grid.png`、`screens/T3/s76-face1-stagger.png`、`screens/T3/s83-subgrid-created.png`、`screens/T3/s96-finite-grid-draft.png`、`screens/T3/s108-after-param-confirm.png`、`screens/T3/s43-box3-result.png` |
| 7 取消/撤銷/重做 | 匯入=1 步(撤銷面消失、重做全回);面內三步編輯逐步退回;空間建立 Ctrl+Z/Y;子網格 31↔22↔27;參數 Ctrl+Z×2/Y×2;「開啟專案」可撤銷並在 2.5 s 內重做回來 | `screens/T1/32-undo2.png`、`screens/T1/36-reopen-after-redo.png`、`screens/T2/139-undo3.png`、`screens/T2/140-redo3.png`、`screens/T2/103-box6-undo-redo.png`、`screens/T3/s91-redo.png`、`screens/T3/s110-param-undo-redo.png`、`screens/T4/post1-undo-open.png`、`screens/T4/post1-redo-open.png` |
| 8 保存/重開 | format `geometry-canvas/10`、PDF sha256 隨檔;全新環境開檔 22 項對照中,除 T4-01 不透明度與鎖定 2 項遺失外一致;第二輪改邊 + 新模型再存再開仍完整;「保存」與「另存」world.scene/manifest 位元組相同;守門:外環草稿/未套用校準拒存、dirty 開檔 confirm、4 種損毀檔拒絕且世界不變;十邊樓梯形(容量拒絕 → 取消牆 12 面 42 m³)存開一致 | `findings/T4-report.md`、`findings/T4-roundtrip-table.md`、`screens/T4/pre-cap-canvas.png`、`screens/T4/post1-cap-canvas.png`、`screens/T4/pre-cap-library.png`、`screens/T4/post1-cap-library.png`、`screens/T4/post2-cap-library.png`、`screens/T4/guard-1-draft-save.png`、`screens/T4/guard-2-calib-save.png`、`screens/T4/corrupt-corrupt-notzip.png`、`screens/T4/ten-10-reopened-lib.png` |
| 窄螢幕 390x844 | 匯入→校準(抽屜自動收/開)→量測;多邊形面→改邊→放置→建空間 60 m³;雙房間 + 網格綁定;開同檔、保存鈕 44×44 下載成功;全程 scrollWidth=390 無橫向溢出 | `screens/T1/210-M-calibrated.png`、`screens/T1/212-M-measure.png`、`screens/T2/m12-preview-done.png`、`screens/T2/m14-created.png`、`screens/T3/m21-roomL-applied.png`、`screens/T3/m35-face1-grid-mobile.png`、`screens/T4/m-03-opened-canvas.png`、`screens/T4/m-08-face1-underlay.png`、`screens/T4/m-09-save.png` |

console:全程除 PDF.js「Indexing all PDF objects」warning 與 ResizeObserver 良性訊息(見 G1)外,無 pageerror。

### 2.2 失敗

影響程度:阻斷 = 阻斷主要流程;資料 = 資料錯誤或遺失;次要 = 次要體驗。「修正在被測版本?」全部為「否」——被測版本內沒有修正,本輪也未修。

| ID | 標題 | 影響 | 根因組 | 已知對照 | 修正在被測版本? | 證據 |
|---|---|---|---|---|---|---|
| **T4-01**(+V2) | 共享房間來源路徑:底圖不透明度/鎖定/取景不保存、adopt 與基準變更即重置、修改不標髒 | **資料**(次要;非幾何) | T4-01 專組 | 新;與 #77 相鄰,不在其五道 gate 內 | 否(#137 草稿亦未修) | `findings/V2-verdict.md`、`findings/T4-report.md`、`screens/V2/s05-after-adopt.png`、`screens/T4/ul-reopened-face1.png`、`downloads/v2-shared-save1.gcanvas` |
| **T2-05**(+V1) | 預設放置「天花 u+x v+y」→ 俯視南北鏡像 | **待拍板**(現判:設計如此 + 次要體驗) | G7 | GEO-244、#117(closed)、PR #121 | 設計如此(只提示不自動改) | `findings/V1-verdict.md`、`screens/V1/C09-control-unaligned-top.png`、`screens/T2/149-unaligned-top.png` |
| T1-01 / T2-01 / T3-02 | 開匯入對話框即 toast「已自動記錄程式錯誤 F-…」(實為 ResizeObserver 良性訊息) | 次要 | G1 | 新(僅測試註解承認) | 否 | `screens/T1/144-G-imp1-back.png`、`screens/T2/050-restart-calib-mode.png` |
| T1-04 / T2-02 / T3-04 / T4-05 | 成功 toast/狀態列/對話框顯示核心原始指令 `boundary 1 outline …` | 次要 | G2a | 新 | 否 | `screens/T1/30-after-shape-L.png`、`screens/T2/145-L-candidate-confirmed.png`、`screens/T3/s86-dialog-state.png`、`screens/T4/s016-roomA-confirmed.png` |
| T3-03 | 六面盒/空容器超容量時顯示「line 56: 邊界面的數量超過上限」原文 | 次要 | G2b | WEB-003 部分;#124 範圍外 | 否 | `screens/T3/s45-box3-reject-toast.png`、`screens/T3/s49-now.png` |
| T4-04 | 截斷 .gcanvas 顯示英文「invalid zip data」 | 次要 | G2c | 新 | 否 | `screens/T4/corrupt-corrupt-truncated.png` |
| T3-01 / T4-02 | 從房間清單/新增房間進面 2 後,「← 物件畫布」第一下回面 1 | 次要 | G3 | 新 | 否 | `screens/T3/s09-back1.png`、`screens/T3/s10-back-after-dblclick.png`、`screens/T3/m22-canvas.png`、`screens/T4/r2-c03-back.png` |
| T1-08 / T3-05 | 兩次匯入同檔/再匯入同頁,新面卡片與舊卡片同座標疊住 | 次要 | G4 | 新(GEO-187 同函式前題) | 否 | `screens/T1/124-dup-after-back2.png`、`screens/T3/s71-canvas-after-apply.png` |
| T2-03 | 外環點擊被拒(2 點 Enter、自交、折返)無文字說明 | 次要 | G5 | 新(RC-POLYGON-PLAN §5.A.1.8 有寫) | 否 | `screens/T2/117-toofew.png`、`screens/T2/120-cross-draft.png` |
| T1-02 | 選頁輸入超範圍頁碼無提示,輸入框與預覽不一致 | 次要 | G5 | 新 | 否 | `screens/T1/42-p2-typed5.png`、`screens/T1/153-RERUN-typed5-applied.png` |
| T1-05 | 校準同一點點兩次仍提示「已選好兩點」,套用才拒絕 | 次要 | G5 | 新 | 否 | `screens/T1/11-calib-same-point-apply.png` |
| T2-04 | 面內雙擊不閉合外環 | 文件漂移(非缺陷) | G5 / 文件 | 文件債 | — | `screens/T2/115-dblclick.png` |
| T1-03 | 校準隨「較早的幾何步驟」被復原而無聲消失 | 次要 | G6 | 文件化設計(REFERENCE-PROJECT.md:61),缺提示 | 否 | `screens/T1/138-C-after-B.png`、`screens/T1/139-C-undo1.png`、`screens/T1/140-C-undo2.png`、`screens/T1/142-C-redo2.png` |
| T3-06 | 空間模型「移除」無確認;對話框內 Ctrl+Z 無作用 | 次要 | 其他 | 新 | 否 | `screens/T3/s33-removed-model1.png`、`screens/T3/s34b.png`、`screens/T3/s35-canvas-after-undo.png` |
| T2-06 | 雜項:同面建兩次同名模型;形狀選單開著 Esc 直接離開面內;390 空白提示卡被工具列蓋;半自動候選取內緣(小一個線寬) | 次要 | 其他 | 新 | 否 | `screens/T2/084-duplicate-create.png`、`screens/T2/130-after-esc.png`、`screens/T2/m03-newproject.png`、`screens/T2/143-L-candidate.png` |
| T1-06 | 錯誤檔對話框仍顯示「/ 1 頁」;0 byte toast 約 2.5 秒偏短 | 次要 | 其他 | 新 | 否 | `screens/T1/126-err-notpdf.png`、`screens/T1/128-err-empty.png` |
| T1-09(+T2) | 撤銷/重做/閉合 2–4 秒才到位,無忙碌提示;連按被「操作進行中」吞 | 次要 | 其他 | 部分(BACKLOG PR70 follow-up) | 否 | `screens/T1/150-G-redo-both.png`、`screens/T1/151-G-redo-both-settled.png`、`screens/T1/34-redo2.png` |
| T1-07 | 390 觸控 300–400 ms 內連點兩個校準點,第二點把狀態重置 | 次要(**未確認**,可能是 CDP 合成觸控) | — | 未見已知 | — | `screens/T1/207-M-two-points.png` |
| T4-03 | 「顯示全部參考線」計數 21/21 vs 20/20(重新整理恢復/重做開檔) | 次要(信心中低,未查) | — | 新 | — | `findings/T4-report.md` |
| T4-06 | 面內 DOM 重複 id(`placeOX` 等) | **非新缺陷**(DOM-CONTRACT.md:270、:853 容許);潛在小雷 app.js:5834 | 其他 | — | — | `findings/rootcause.md` |

### 2.3 尚未測(原因)

- **File System Access 原生保存對話框**:無頭 Chrome 無對話框會卡住,工具刻意移除該 API 改走下載備援。
- **真實案場 PDF**、`asymmetric-ten.pdf` 實檔:本輪只用合成圖(十邊只測了合成樓梯形)。
- **實機 iOS/Android**(輸入法、系統選檔、下載、觸控長按、雙指):只有 390 模擬;T1-07 因此未定。
- **Edge**:未裝測試設定。
- **#77 五道 gate** 未逐項測(T4/V2 只覆蓋了共享路徑的保存重開);**GEO-242 空白鍵平移**未測。
- 多頁/加頁 PDF 與非預設取景(crop)的保存重開;右鍵選單、雙擊邊/凸角面板、凹角 Alt+拖;390 下的鍵入長度/半自動/六面盒/參數卡/子網格/相位差/`#igRuleAdd`;建立無限網格與配置的 Ctrl+Z;`#btnNewAssembly`、材料規格排格 `#btnEngineeringSpecs`;邊長引用參數(找不到入口)。
- 連按 Ctrl+Z/Y 間隔 < 1 s 的丟棄行為(中斷前疑似,未重跑,不列發現)。
- 詳見各報告「尚未測」段:`findings/T1-report.md`、`findings/T2-report.md`、`findings/T3-report.md`、`findings/T4-report.md`。

### 2.4 被環境阻擋

1. **22:25(2026-10-05)四埠 bridge 同時消失,原因未確認。** 8831–8834 的 `serve.py` 仍在、但 bridge 子行程消失,`/api` 回「橋接器連線中斷」。依使用者 🔒 指示,各驗收員**只結束自己核對過 PID 與命令列的程序後重起**(禁止按程序名稱一次關掉),重起後 probe 皆 `fresh:true`(`probes/T1-probe_8831_after_interrupt.txt`、`probes/T2-probe_8832_after_interruption.txt`、`probes/T3-probe_8833_after_interrupt.txt`、`probes/T4-probe-8834-after-interruption.txt`)。重跑範圍:
   - T1:只有「A4 輸入頁碼 5 後加入」受影響,已重跑(`screens/T1/153-RERUN-typed5-applied.png`);其餘中斷前案例當時橋接正常。
   - T2:校準、ROOM_A 描點/三種閉合/雙擊、面內復原重做、輸入邊長、放置與建空間全部重跑;ROOM_A 半自動候選改以 ROOM_L 候選重跑。
   - T3:22:11–22:25 第一輪(房間 A/L、選取、改邊、刪面/Ctrl+Z、返回鈕)全部重跑,結果一致。
   - T4:中斷前專案整個作廢,22:27 起以正式 UI 重建(`r2-*` 截圖),保存重開全在重跑之後。
   - V1、V2 在事件之後才開始,不受影響。
2. **SAC(Smart App Control)擋新編 exe**:model-base 第一次編譯後 5 次重試全被擋(WinError 4551),重編同來源後即過。屬環境阻擋,非產品失敗(`tools/ENV-README.md` §6)。
3. **T4-07:高 CPU 下開 3 模型檔偶發 30 s 逾時**(CPU 94–100%,他人負載):「未能完成開啟專案:signal timed out」,8 次中 3 次,重試成功、世界不變;`reference-workspace.js:1212` 等為固定 30 s 逾時。**原因未確認**,不列為確認缺陷(`screens/T4/s-fresh2-04-retry.png`)。
4. **工具問題(非產品)**:T3 的 CDP daemon 自身卡死兩次,改 attach 版重啟;`tools/stop_server.sh` 對同埠第二次停止時 rename `*.stopped.json` 失敗(服務其實已停);T2/T3/T4 的報告檔寫入曾被 harness 擋,報告由主迴圈依其最終回覆存檔(內容未改)。

## 3. 失敗項詳細

共通環境:main `d6b4b45`、Windows 11、無頭 Chrome 154 全新 profile、桌面 1440x900(另註 390x844)、合成圖 `fixtures/synthetic_floorplan_A3_landscape.pdf`(除另註)。

### 3.1 T4-01 共享房間來源:底圖顯示設定遺失(資料遺失,次要)

- **環境/入口**:T4 埠 8834、V2 埠 8837(每次重起 probe `fresh:true`,`probes/V2-probe_8837.txt`);入口:面內底圖分頁「同來源房間」→ `#roomSourceCreate`(以此底圖連續新增房間)→ `#roomNew`。
- **最短重現**(V2,正式 UI):
  1. 檔案 → 新專案 → 匯入參考資料 → 選 A3 合成 PDF → 加入參考頁。
  2. 底圖分頁兩點校準 5000 mm;確認 ROOM_A 外環;不透明度設 0.70(`screens/V2/s04-pre-adopt-op070.png`)。
  3. 按 `#roomSourceCreate`(ROOM_A)→ **不透明度立刻變 0.5**(`screens/V2/s05-after-adopt.png`,此刻 SVG 仍顯示 0.7,控制項與畫面不一致)。
  4. `#roomNew` 建 ROOM_L(6000x5000 L);L 設 0.30 + 鎖定(`screens/V2/s08-L-op030-locked.png`)。
  5. 面 1 設 0.75(`screens/V2/s09-A-op075.png`)→ 旋轉 90 → **不透明度回 0.5**(`screens/V2/s10-A-after-rot90.png`);同時 **ROOM_L 的 0.30+鎖定也被重置**為 0.5/未鎖(`screens/V2/s13-L-after-A-basis-change.png`)。
  6. 再設 0.75 + 鎖定 → 保存(`screens/V2/s14-A-before-save.png`、`screens/V2/s15-saved.png`)→ 停服務重起 → 全新 profile 開檔 → **0.5、未鎖定**(`screens/V2/r02-A-reopened.png`、`screens/V2/r03-L-reopened.png`)。
  7. 開檔後(狀態「已保存」)改 0.8 + 鎖定 → **狀態仍「已保存」,不標髒**(`screens/V2/r04-L-op080-lock-dirty-check.png`)。
  - 對照組(不按 `#roomSourceCreate`,同樣設定):重開保留 0.75/鎖定,改不透明度會變「有未保存的變更」(`screens/V2/c04-final-set.png`、`screens/V2/cr02-A-reopened.png`、`screens/V2/c05-op-only-dirty.png`)。
- **完整範圍**:(a) 不保存就丟 — adopt 當下即重置;(b) 任何共享基準變更(旋轉/X 位移)連帶把**所有同來源房間**的不透明度/鎖定重置;(c) 只改不透明度/鎖定不標髒、不入 history;(d) 保存後 opacity/locked/crop 不入檔(旋轉/X/Y、mmPerPx、校準點、頁碼、房間↔邊界對應**有**保留)。
- **檔案證據(本輪報告整合員再次唯讀解壓確認)**:

  | 檔 | format | manifest.faces | opacity/locked/crop 欄 |
  |---|---|---|---|
  | `downloads/v2-shared-save1.gcanvas`(共享路徑) | `geometry-canvas/10` | 0 | 無 |
  | `downloads/t4-ulset-save4.gcanvas`(T4 共享路徑) | `geometry-canvas/10` | 0 | 無 |
  | `downloads/v2-ctrl-save1.gcanvas`(對照) | `geometry-canvas/9` | 1 | 有 |
  | `downloads/ctrl-plain-import-op-lock.gcanvas`(T4 對照) | `geometry-canvas/1` | 1 | 有(0.84 / true / crop) |

  T4 的重開截圖:`screens/T4/ul-state.png`(保存前)、`screens/T4/ul-reopened-face1.png`(重開後)、`screens/T4/ctrl-ulset.png`(對照)。
- **預期依據**:`geometry-web/docs/REFERENCE-PROJECT.md:17`(對位、旋轉、透明度與鎖定同屬「對位與顯示」)、`:27-28`(每 face 的 pages 保存 crop/opacity/locked)。Q37 已採納範圍只共用比例尺／對位,見 `geometry-guide/IMPLEMENTATION-QUEUE-20261004.md:16`;`docs/ISSUE77-HANDOFF.md:43` 的 adopt 只移除所選頁舊獨立 basis 的保存影子,其餘原來源／證據保留。依此保留各 room/page 既有顯示 metadata 是最小變動的保存契約修復推論,不必等本報告所稱新授權的原話才修復已確認遺失。這是既有產品契約的核對,**不是新增 SSOT 條文或使用者逐字授權證據**。
- **根因(V2 讀碼,已確認)**:
  - `geometry-web/source-plane.js:25`:plane 白名單只有 id/sourceId/page/coordinateSpace/pageSize/calibration/alignment/basisRevision;`:164-168` `fromPage` 丟掉 crop/opacity/locked;`:170-177` `materialize` 硬寫 crop=整頁、opacity 0.5、locked false、records []。
  - `geometry-web/reference-workspace.js:440-480` `adoptRoomSource` 把原頁自 `g.pages` 移除(:480);`:1093-1098` `manifestData` 只序列化 `g.pages` → `faces=[]`(這是現象點,根因是 plane 契約沒有顯示欄位)。
  - `geometry-web/room-collection-workspace.js:115-127`:顯示值只存在 per-context/per-bid 快取 `oc.underlays[bid]`;基準真的改變時 `:123` 以 `materialize` 覆寫 → (b)。
  - `geometry-web/app.js:4717-4726` `feChangeUnderlay` 對 opacity/locked 只 `Object.assign` 到快取,再經 `reference-workspace.js:833-835` → `RoomCollectionWorkspace.changeBasis`(值未變);`geometry-web/room-collection.js:154-157` `change()` 遇 no-op 不寫 metadata → 不標髒、不入 history → (c)。
- **影響**:實測確認底圖不透明度／鎖定偏好遺失;非整頁 crop 保存未經本輪 UI 驗證,其欄位遺失與 materialize 回整頁屬讀碼／保存檔核對,不能算已重現的取景 UI 遺失。幾何、校準、對位、房間關聯不受影響。鎖定遺失會讓重開後的對位可被誤拖,間接改到共享基準並把所有同來源房間標「需複核」。
- **已知對照**:issue #77 五道 gate(registry 往返/未知 envelope/source closure/attachment undo-redo/late-context)都不談顯示設定 → **新發現,建議掛 #77**。PR #134 未修本項,但修正涉及 `app.js`,與 #134 **同檔**;PR #137(草稿)改 `reference-workspace.js` 的 `manifestData`(加 scenarioCatalog)與 `project-store.js` format/keys 驗證,**未修 T4-01**,但與修正點同函式/同驗證器。共檔需 ownership 協調,不代表必然同 hunk 衝突。
- **作者回報的拍板**:顯示設定**每間房各自一份(per-room)**,原回報與授權證據界線見 §5;不以作者宣稱代替使用者原話。

### 3.2 T2-05 預設放置 → 俯視南北鏡像(待拍板)

- **環境/入口**:T2 埠 8832、V1 埠 8836(`probes/V1-probe_8836.txt`);面內屬性分頁「放置這片面」→ 物件「以此面建立空間」→ 空間建模視窗。
- **最短重現(不用 PDF 的對照組,V1-B)**:
  1. 新專案 → 工具列「多邊形面」(P)→ 點一下 → 鍵入 4000→ 2000↓ 2000→ 3000↓ 6000← Enter(L 形,缺口在編輯圖右上)。
  2. 放置全部照預設(原點 0/0/0、u +x、v +y,表單只寫「法向 +Z(天花)」)→ 放置(`screens/V1/C06-place-form-default.png`)。
  3. 以此面建立空間 → 俯視 → 確認用途與觀看方向 → 牆底 0 → 更新預覽 → **缺口在右下**,78 m³ / 淨空 78 / 牆 6.72(`screens/V1/C09-control-unaligned-top.png`)。
  - PDF 組結果完全相同(`screens/V1/V16-place-form-default.png`、`screens/V1/V21-unaligned-top-78.png`);按「依原圖對齊放置方向」後缺口回右上、體積不變(`screens/V1/V29-aligned-top.png`)。
- **預期 vs 實際**:依產品常識,描一張俯視平面圖後的俯視模型應與原圖同手性;實際照預設會南北翻轉(Y 軸),而且**第一次確認前沒有任何方向警告**(`screens/V1/V20-projection-confirmed.png` 是第一次確認後才出現說明)、不對齊也能預覽並建立,模型連同「俯視(沿 −Z)」定義存進模型庫(`screens/V1/V25-library-unaligned.png`、`screens/V1/V26-library-model-top.png`)。**規格**:`docs/FACE-PROJECTION.md:25`、`:33`、`docs/SPACE-MODELING.md:32`、`BACKLOG.md:4186-4190`(GEO-244)明定「只提示、提供按鈕,不自動改放置」;公理層無「預設要對齊原圖」條文 → **現行規格下屬設計如此 + 體驗缺口**。
- **77.647 m³ 已駁回**:T2 截圖 148/149 用的是半自動候選面(邊 4000/2002/1988/2985/5988/4987),面積 25.88218 m² × 3 m = 77.6465 m³、牆 6.705 m³ 正好吻合;鏡像本身不改體積(`screens/T2/147-placement-ui.png`、`screens/T2/148-unaligned-sm.png`、`screens/T2/149-unaligned-top.png`)。
- **根因(已確認)**:`geometry-web/app.js:8426-8433` PLACE_PRESETS「天花」= u +x、v +y;`app.js:8516-8517` 新面預設 `"+x"/"+y"`;`geometry-web/model-viewer.js:52-63` `drawingAlignment`(:59 法向 +Z 配俯視必 changed);`geometry-web/space-workspace.js:219-224` 須先有投影定義才算 alignment(故首次無警告)、`:433-451` 只有第二次按才 mutate 放置。
- **影響**:單房間體積/牆量正確;多房間相對方位或對真實方位時手性錯。若產品意圖是「照預設就得到同手性」,即升級為資料錯誤 — **需使用者拍板**(§6 (a))。
- **已知對照**:GEO-244、#117(closed)、PR #121(修的是「提供對齊」,不是「預設對齊」)。
- **旁支觀察(未追查)**:V1-O1 在 5% 縮放、「PDF 端點讀取中」時描點沒吸到 PDF 端點,整個外環比 PDF 線高 850 mm(`screens/V1/V13-state.png`);V1-O2 對齊後回到面內,右欄仍顯示舊放置「天花 z=0」,離開到畫布才更新(`screens/V1/V30-after-align-canvas.png`、`screens/V1/V32-object-canvas.png`)。

### 3.3 G1 假警報 toast(T1-01 / T2-01 / T3-02,次要)

- 入口:檔案 → 匯入參考資料。重現:新專案 → 匯入任一合成 PDF → 選頁對話框開啟/換頁/套用。
- 預期(產品常識):正常匯入不出現「程式錯誤」。實際:toast「已自動記錄程式錯誤 F-20261005-00x」,紀錄內容皆為 `ResizeObserver loop completed with undelivered notifications.`(T1 ≥5 次、T2 2/2、T3 5/5)。`screens/T1/144-G-imp1-back.png`、`screens/T2/050-restart-calib-mode.png`。
- 根因(已確認):`geometry-web/feedback.js:112-116` 全域 error 監聽只擋空訊息,未過濾 ResizeObserver;觸發源最可能是 `reference-workspace.js:1536` 的 RO 回呼改了被觀察元素尺寸(推論)。`room_outline_test.js:12-17` 註解早已承認並以等 15 秒繞過。
- 註:驗收員引用的 `fb-<port>/F-…/report.md` 回報副本**未放入本包**(含本機路徑,屬回報收件匣);上述摘錄即其內容。

### 3.4 G2 內部指令/核心原文外露(次要)

- **G2a 成功回顯原始指令**(T1-04 / T2-02 / T3-04 / T4-05):形狀庫取代外環、閉合外環、確認候選、放置後,toast 與狀態列顯示 `boundary 1 outline 0,0 4000,0 …`、`placement 1 on boundary …`;I8a 確認對話框以 `<code>` 顯示指令;刪網格後狀態列殘留 `✓ delete grid 2`。`screens/T1/30-after-shape-L.png`、`screens/T2/020-A-closed-by-startclick.png`、`screens/T3/s86-dialog-state.png`、`screens/T3/s86-now.png`、`screens/T3/m20b-confirm-dialog.png`、`screens/T4/s016-roomA-confirmed.png`、`screens/T4/ten-02.png`。根因:`app.js:1140-1144` `emitLine` 預設 successText = 原始指令,18 個呼叫點只有 :7339 傳了 successText。對話框 `<code>` 是被測試鎖住的設計(不建議同修)。預期:使用者語言(產品常識,無規格)。
- **G2b 容量拒絕訊息原文**(T3-03):六面盒建到 14 面/2 空間後第 3 個、空容器第 5 個 → 「line 56: 邊界面的數量超過上限」「✗ line 62: 空間的數量超過上限」(無數字、帶核心行號,六面盒對話框內不顯示)。`screens/T3/s45-box3-reject-toast.png`、`screens/T3/s49-now.png`。**拒絕行為正確**。根因:`app.js:3612-3646` `submitBox6`、`:10265-10272` `btnNewSpace` 不經預檢;#124 的 preflight 只在空間建模路徑(範圍不同,不是 #124 失效)。**注意**:UI-REDESIGN-PLAN.md §5.7(:196、:168)現行規定失敗 toast 顯示原文 → 要不要轉友善文案需拍板(§6 (b))。
- **G2c 截斷檔英文例外**(T4-04):開截斷 .gcanvas → 「未能完成開啟專案:invalid zip data」。`screens/T4/corrupt-corrupt-truncated.png`。根因:`geometry-web/project-store.js:628`、`:641-644` 把 fflate 例外原樣丟出。

### 3.5 G3 返回鍵要按兩次(T3-01 / T4-02,次要)

- 重現:兩房間專案 → 在面 1 工作區底圖分頁「同來源房間」清單按「查看」開房間 2(或新增房間確認後)→ 按「← 物件畫布」。實際:第一下回到面 1、第二下才回畫布(T3 3/3 含 390、T4 2/2);畫布雙擊進入則一次回畫布。`screens/T3/s09-back1.png`、`screens/T3/s10-back-after-dblclick.png`、`screens/T3/m22-canvas.png`、`screens/T4/r2-c03-back.png`。
- 預期:按鈕名稱即「物件畫布」,應一次回畫布(產品常識;同類「切圖頁累積返回堆疊」已被 cdp_test P61-3 當缺陷修過)。
- 根因(已確認):`app.js:2529` 已在面工作區再 `enterFocus("face", 其他面)` 會把舊面推入返回堆疊;呼叫端 `room-collection-workspace.js:278`、`:332`。

### 3.6 G4 新面卡片疊住(T1-08 / T3-05,次要)

- 重現:新專案 → 匯入 A3 → 加入 → 返回畫布 → 再匯入同檔「建立描繪用面」→ 返回。實際:面 2 卡片與面 1 同座標,蓋住面 1 標頭。`screens/T1/124-dup-after-back2.png`、`screens/T3/s71-canvas-after-apply.png`。
- 根因(已確認):`app.js:8759-8764` `objNewPolyFace` 以視野中心直接寫卡片座標,繞過 `nextCardPosition` 的碰撞偵測;返回畫布會重置 pan/zoom,故兩次中心相同(座標逐像素相同屬推論)。

### 3.7 G5 拒絕無文字/輸入不一致(T2-03、T1-02、T1-05;T2-04 文件)

- T2-03:面內重畫外環 2 點按 Enter 無反應;第 5 點自交只有紅色虛線;背向折返點擊被忽略,均無文字。`screens/T2/117-toofew.png`、`screens/T2/120-cross-draft.png`。依據 `docs/RC-POLYGON-PLAN.md:224-229`(§5.A.1.8 應有警示文字)→ 規格寫了、面內漏了。根因 `app.js:5376-5385`(`r.error.msg` 被丟)、`:5796-5801`。
- T1-02:A4 2 頁輸入 5/0/1.5/空白 → 輸入框保持 5、預覽仍第 2 頁、無訊息,加入的是第 2 頁。`screens/T1/42-p2-typed5.png`、`screens/T1/153-RERUN-typed5-applied.png`。根因 `reference-workspace.js:999`。
- T1-05:同一點點兩次顯示「已選好兩點」且「套用比例尺」可按,按下才拒絕。`screens/T1/11-calib-same-point-apply.png`。根因 `app.js:4782`、`:4796`、`:6886`。
- T2-04:面內雙擊不閉合(`screens/T2/115-dblclick.png`)。`docs/RC-POLYGON-PLAN.md:204`、`:322` 仍寫「雙擊」為三種閉合之一,但同 commit 的 `cdp_test.js:4077` 已註明面內無雙擊,GEO-186(b) 移除主畫布 poly 機器 → **文件漂移,非缺陷**(§6 (c))。

### 3.8 G6 校準隨較早步驟復原而無聲消失(T1-03,次要)

- 重現:面已匯入底圖 → 形狀庫取代外環(A)→ 校準 5000 → 再取代外環(B)→ Ctrl+Z(校準仍在)→ 再 Ctrl+Z(復原 A)→ 校準變「未校準」、底圖縮回,toast 只有「已復原」;Ctrl+Y×2 校準回來。`screens/T1/138-C-after-B.png`、`screens/T1/139-C-undo1.png`、`screens/T1/140-C-undo2.png`、`screens/T1/142-C-redo2.png`。
- 依據:`docs/REFERENCE-PROJECT.md:61`「復原/重做可恢復原實例的來源」→ 行為符合文件,缺的是提示。根因 `reference-workspace.js:827-833` `calibrated()` 不 push history,`project-store.js:673-681` 快照含 calibration。

### 3.9 其他次要

- T3-06 空間模型移除:「已建立空間」清單的「移除」無確認;對話框內 Ctrl+Z 無效(原生 modal 擁有鍵盤,`app.js:1462`),畫布 `#btnUndo` 可還原。`screens/T3/s33-removed-model1.png`、`screens/T3/s34b.png`、`screens/T3/s35-canvas-after-undo.png`。根因 `space-workspace.js:663`(另無 try/catch)。
- T2-06 雜項:同面建兩次得兩筆同名「面 1空間」(`screens/T2/084-duplicate-create.png`,`space-workspace.js:326` 無唯一性檢查);形狀選單開著按一次 Esc 直接離開面內(`screens/T2/130-after-esc.png`,1 次);390 空白專案提示卡被工具列蓋(`screens/T2/m03-newproject.png`);半自動候選取內緣,比圖面中心線小一個線寬(`screens/T2/143-L-candidate.png`)。
- T1-06 / T1-09 / T1-07 / T4-03 / T4-06:見 §2.2 表與 `findings/T1-findings.md`、`findings/T4-report.md`、`findings/rootcause.md` §3。

## 4. 共用根因與責任邊界(依 `findings/rootcause.md`)

> **本輪未修改產品程式。** 下列是建議修正範圍與排序,未動手。行號以 `d6b4b45` 為準(`geometry-web/` 下)。

| 組 | 涵蓋 | 責任邊界 / 最小修正點 | 與 PR/分支的衝突 | 建議順序 |
|---|---|---|---|---|
| G1 | T1-01、T2-01、T3-02 | `feedback.js:112-116` 對 `/^ResizeObserver loop/` 不 autoReport(仍記黑盒子);治本可在 `reference-workspace.js:1536` 回呼外包 rAF | 無 | **先做**,可並行;做完可拿掉 `room_outline_test.js:12-17` 的 15 秒等待 |
| G2a | T1-04、T2-02、T3-04、T4-05 | `app.js:1140-1144` `emitLine` 預設成功文案改通用(勿改簽名);對話框 `<code>` 不同修 | #134 在 `emitLine` 內 :1141 後加 1 行 | **排在 #134 之後**(或同作者) |
| G2b | T3-03 | `app.js:3612-3646`、`:10265-10272` 送出前以 16/16/4 預檢,`friendlyError` opt-in 轉人話;核心 `line %d:` 不動 | 無 | 可並行,但**先等 §6 (b) 拍板** |
| G2c | T4-04 | `project-store.js:628`、`:641-644` 包 fflate 例外為中文 | #137 改同檔(hunk 不含這幾行) | **排在 #137 之後** |
| G3 | T3-01、T4-02 | 只改 `app.js:2529` enterFocus 側(面→面取代不 push);或窄改 `room-collection-workspace.js:278`、`:332` | #134 重構 leaveFocus(:2565-2600)→ **只改 enterFocus 側** | 可並行;通知 #123(返回/麵包屑) |
| G4 | T1-08、T3-05 | `app.js:8759-8764` 視野中心碰撞時改用 `nextCardPosition`,保留「在視野內」(GEO-187、cdp_test.js:3942) | 無 | 可並行 |
| G5 | T2-03、T1-02、T1-05(T2-04 文件) | `app.js:5376-5385`、`:5796-5801` 補 `setStatus("✗ "+msg)`+toast;`reference-workspace.js:999` 無效頁碼還原;`app.js:4782` 同點即提示 | 無 | 可並行 |
| G6 | T1-03 | 最小案 `app.js:9633-9668` `doUndoRedo` 比對校準變化附提示;治本案讓 `reference-workspace.js:827` 校準自成一步(碰 `project-store.js:673-699`) | 治本案撞 #137(project-store.js 672-695) | 最小案可並行;**治本案排在 #137 之後** |
| G7 | T2-05 | 由小到大:① `space-workspace.js:219` 提早警示;② 未對齊時閘門;③ `app.js:8516-8517` 改預設放置 | 無 PR;②③與 GEO-244 規格衝突 | **等 §6 (a) 拍板** |
| T4-01 | T4-01(+V2 a/b/c) | 依 §5 既有保存契約推論保留各 room/page 的 opacity/locked/crop(非整頁 crop UI 未驗);作者建議 `source-rooms` 附件或房間 metadata 保存顯示欄,`feChangeUnderlay`(app.js:4717-4726)走 metadata change(標髒、可 undo),`materialize`(source-plane.js:170-177)與 adopt(reference-workspace.js:440-480)沿用原頁值。schema／capability 方案必要性由整合 owner 審查,不是新授權已驗證的結論 | `app.js` 同 #134;#137 佔用 `manifestData`(reference-workspace.js:1101-1107)與 project-store format /14、keys 驗證 | **排在 #137 之後**;另與 #134 app.js owner 協調,格式版本號由整合 owner 核對 |
| 其他 | T3-06、T2-06 | `space-workspace.js:663` 移除前 confirm/提示 + try/catch;`:326` 同名加序號 | 無 | 可並行 |

**測試檔共通規則**:回歸測試請寫**獨立檔**(沿用 `room_outline_test.js` 由 cdp_test.js 呼叫的模式),**不要**直接加進 `cdp_test.js`、`cdp_sections.golden.json`、`tests/run_all.expected.json`、`tests/run_all.py` — 這幾個檔與 #134(以及 #136 的 run_all.expected.json)衝突;待 #134 合併後再統一登記。每個修正都要做突變測試:拿掉修正必須紅、失敗訊息指得出病因。
**相鄰工作**:issue #123(UI 整合 S0–S6,尚無 PR)與 G2a(狀態列/toast 文案)、G3(返回)概念重疊,動手前對一次。停滯分支 `origin/feat/assembly-generation-minimal-20261002` 若重啟會碰 project-store.js / reference-workspace.js(低風險)。

## 5. 作者回報的拍板紀錄(原始授權待核)

**本交接保留作者回報,整合前需核對原始授權。** 本包未附該次使用者原話,下列歷史日期與 per-room 回報不構成獨立授權證據;本次不採納也不否定作者回報,不轉寫 SSOT 或 `決策佇列.md`。

| 日期 | 決定 | 狀態 |
|---|---|---|
| 2026-10-06 | 作者原回報:🔒 **T4-01:底圖顯示設定(不透明度/鎖定/取景)每間房各自一份(per-room),非同一 plane 共用。** | 作者稱已拍板及待 dot 轉寫;本包未附原話,**原始授權待核,不得據此直接轉寫 `決策佇列.md`**。本分支保留不改該檔 |

**來源與推論分開**:既有 `REFERENCE-PROJECT.md:17,27-28` 明列每 face 的 ReferencePage 保存 crop/opacity/locked;Q37(`IMPLEMENTATION-QUEUE-20261004.md:16`)共用校準／對位,`ISSUE77-HANDOFF.md:43` adopt 只去舊 basis shadow。因此保留各 room/page 顯示 metadata 是最小變動的既有保存契約修復推論,不需因作者所稱新授權欠原話而卡住不透明度／鎖定遺失修復;這不等於核實上列逐字拍板或批准額外 schema 設計。回歸應核兩房各自的值在 adopt、基準變更、保存→全新環境開檔後保持。**目前僅實測確認既有 opacity/lock 遺失;非整頁 crop 尚未 UI 驗證**,讀碼顯示其遺失風險另列待驗。

## 6. 待拍板(紅燈;只列選項與建議,不替使用者決定)

**(a) T2-05 俯視鏡像要不要升級?**
- 選項 0:維持現狀(GEO-244 設計,只提示)。
- 選項 1(低):只把方向警示提前到第一次確認前(`space-workspace.js:219`),不改行為。
- 選項 2(中):未對齊時停用「更新預覽/建立空間」,直到按對齊或明示忽略 — 與 `docs/FACE-PROJECTION.md:25`、`:33`、`docs/SPACE-MODELING.md:32`「不自動改動放置」精神衝突,需改文件。
- 選項 3(高):有底圖/描繪來源的面預設改 u +x、v −y 並自動補原點 — 改變每個新面預設,影響 P79/P84、space_model_test、保存重開夾具與 GEO-244 的 8 種放置×俯仰視契約(BACKLOG.md:4193);公理層無此條文,屬新行為。
- 建議:先做選項 1(無爭議、成本低);是否走 2/3 取決於產品意圖「描底圖照預設就要同手性」是否成立 — 若成立,本項應改判為資料錯誤。理由:V1 已證明幾何忠於放置座標、體積正確,問題在可發現性與預設語意。

**(b) 失敗訊息要不要從核心原文轉友善文案?**
- 現行規格 `UI-REDESIGN-PLAN.md` §5.7(:196、:168)規定 toast 顯示 bridge `ok:false` 原文;`:197` 改狀態列文案須同步改 cdp_test。
- 選項:① 維持原文;② 只對容量拒絕(G2b)與損毀 ZIP(G2c)用既有 `friendlyError` opt-in 轉人話,不改規格;③ 全面改規格。
- 建議:②。理由:有 GEO-195 先例、不動 SSOT 與核心、影響面小;③ 牽動所有 cdp 文案斷言,宜併入 #123。

**(c) 文件漂移怎麼處理?**(每項:改文件以符實作,或改實作以符文件)

| 位置 | 漂移 | 建議 |
|---|---|---|
| `docs/RC-POLYGON-PLAN.md:204`(及 :322) | 寫「雙擊」為三種閉合之一,面內實作與測試皆無 | 改文件標「已移除」 |
| `docs/REFERENCE-PROJECT.md:23` | format 清單只到 `/9`;實測共享來源存成 `/10`,repo 另有 `/13` 規則保存 | 補 `/10`–`/13` |
| `geometry-web/README.md:300-305` vs `docs/DOM-CONTRACT.md:585` | README 說底圖「只存在本次工作階段、重新整理就沒了」;DOM-CONTRACT 記 GEO-198 已核准隨 .gcanvas 保存(T4 實測也保存) | 改 README |
| `docs/DOM-CONTRACT.md:83` | 說匯入入口收在「建立」選單;實際在檔案選單 `#btnImportReference` | 改文件(或決定補入口) |
| `docs/SPACE-MODELING.md:48` | 寫「修改牆高」按鈕;實際按鈕叫「修改模型」(space-workspace.js:588) | 改文件 |
| `公理層.md:10-12` | 稱 D20–D25/I26–I33(`orthogonal-model/1`)「尚未實作於現行 C 核心或物件畫布」;本輪實測空間建模(封閉殼、I33 SPACE_CAPACITY 拒絕)已在產品中運作 | **SSOT,只回報不改**;是否更新狀態句由使用者決定(本項報告整合員未逐條核對 D20–D25 實作範圍,信心中) |

## 7. 已知問題對照

| 已知項 | 本輪觀察 |
|---|---|
| #54 / PR #63(已合入 d6b4b45) | 校準 → 選房間/描外環 → 候選核對 → 確認 → 保存重開,合成圖全通過;私人實圖 REAL-PDF 仍未驗 |
| #77(OPEN;#102、#114 已合入,五道 gate 未做) | 正式入口 `#roomSourceCreate`/`#roomNew`/改名/解除關聯/需複核**已可用**;registry 往返在 d6b4b45 實際可用;**新發現 T4-01** 掛 #77 相鄰;五道 gate 未逐項測 |
| #87(同頁多候選,未實作) | 找不到入口,與已知一致 |
| #61 / PR #134(子線顯示、RuleLineRef 草稿) | 找不到子線顯示/選線;`#igRuleAdd`(slice1)可見未測 |
| #119 / PR #124 | 十邊樓梯形(合成)容量拒絕 I33 SPACE_CAPACITY(21/16)→ 取消牆 12 面 42 m³ → 保存重開一致(format /3),**此合成案例通過**;`asymmetric-ten.pdf` 實檔未測 |
| #124 範圍 | preflight 只在空間建模路徑;T3-03 的六面盒/空容器是手動路徑,**不在 #124 範圍**,不是 #124 失效 |
| GEO-242 空白鍵平移被攔截 | 未測 |
| GEO-244 / #117(closed)/ PR #121 | T2-05 即此設計;見 §3.2、§6 (a) |
| #123 UI 整合 | G2a、G3、T2-06(390 提示卡被蓋)與其範圍相鄰 |
| 已知清單全文 | `findings/known-issues.md`(驗收前 2026-10-05 的索引;open PR 另有 #135、#136、#137,見 `findings/rootcause.md` §0) |

## 8. 給 dot 的接手清單

建議一組一張工單,優先序:

1. **T4-01 底圖顯示設定保存**(不透明度／鎖定遺失已確認;非整頁 crop UI 未驗)— 依 §5 既有契約做最小修復,不把作者拍板宣稱當新授權原話或先轉写 `決策佇列.md`;**等 #137 合併後**再動 `manifestData`/project-store 格式,並與 #134 的 app.js owner 協調。
2. **G1 假警報過濾**(最便宜、可立即並行;順手移除 15 秒等待)。
3. **G3 返回鍵**(只改 enterFocus 側;通知 #123)。
4. **G5 拒絕文字 + 頁碼/同點提示**、**G4 卡片碰撞**、**G6 最小案提示**、**其他(T3-06、T2-06)**— 皆可並行。
5. **G2a 成功文案**— 等 #134 合併後。**G2c 中文 ZIP 錯誤**— 等 #137 合併後。
6. **等拍板**:G7/T2-05(§6 a)、G2b(§6 b)、文件漂移(§6 c)。
7. **待查**(不開修正單,先調查):T4-03 參考線計數、T1-07 實機觸控、T4-07 30 s 逾時與負載關係、V1-O1 5% 縮放吸附、T1-09 延遲來源。

**如何重跑**:見 `tools/ENV-README.md`。流程:`python tools/build_qa.py`(雜湊快取,沒改就不重編;SAC 擋屬環境)→ `bash tools/start_server.sh <埠>`(自動 probe,須 `fresh:true`)→ 以 `tools/qa_cdp.js`(零相依,Node ≥22)寫腳本或用 `tools/example_script.json` 格式跑 → `bash tools/stop_server.sh <埠>`(只停自己記錄的 PID)。合成圖以 `python fixtures/gen_synthetic_pdfs.py` 重生,座標與真實尺寸見 `fixtures/fixtures.md`。工具中的 `<QA>`/`<TEMP>` 為清洗後的佔位字,使用前換成本機路徑。驗收守則原文:`findings/BRIEF.md`。

## 9. 本目錄內容

| 路徑 | 內容 |
|---|---|
| `README.md` | 本主報告 |
| `findings/` | 各驗收員原文:`findings/T1-findings.md`、`findings/T1-report.md`、`findings/T2-report.md`、`findings/T3-report.md`、`findings/T4-report.md`、`findings/T4-roundtrip-table.md`、`findings/V1-verdict.md`、`findings/V2-verdict.md`;讀碼根因 `findings/rootcause.md`;已知問題索引 `findings/known-issues.md`;`findings/product-map.md`(**讀碼地圖,非規格**);`findings/BLOCKERS.md`;`findings/BRIEF.md` |
| `fixtures/` | 3 份合成 PDF、`fixtures/fixtures.md`、`fixtures/gen_synthetic_pdfs.py` — **全部為人工合成,非真實案場** |
| `tools/` | `tools/qa_cdp.js`、`tools/qa_server.py`、`tools/start_server.sh`、`tools/stop_server.sh`(已知瑕疵:同埠第二次停止 rename 失敗)、`tools/build_qa.py`、`tools/ENV-README.md`、`tools/example_script.json` |
| screens/(代號)/ | 只挑報告引用的截圖(155 張;桌面 1440x900 與 390x844),檔名保留驗收原名 |
| `downloads/` | 4 個 `.gcanvas`(內含 PDF 已以 sha256 核對為 `fixtures/synthetic_floorplan_A3_landscape.pdf`) |
| `probes/` | 各埠 `runtime_version.py --probe` 輸出(session 值已遮為 `<session>`) |

**證據檔名對照註記**:原始報告中的引用與本包檔名有幾處不同 — T1-03 的「C-after-B / C-undo1…」= `screens/T1/138-C-after-B.png` 等帶序號檔;T3 報告的 `s21` 無對應檔(房間 L 證據以 `screens/T3/s08-L-applied.png` 為準);BLOCKERS 提到的 `evidence/T4/findings.md` 不存在,T4-01 內容在 `findings/T4-report.md` 與 `findings/V2-verdict.md`;`fb-*` 回報副本、瀏覽器 profile、daemon/node 日誌、console 原始 dump、repo 夾具 PDF 副本**刻意未收**(摘錄已寫入本報告)。原始報告中的 `evidence/<代號>/…` 路徑指驗收當時的暫存目錄,本包對應位置為 `screens/<代號>/`、`downloads/`、`probes/`。
**補充截圖索引**(上文未逐一點名、但各驗收員報告有引用的佐證):
- 流程 1/2:`screens/T1/s01-home-default.png`(預設世界 1 張面)、`screens/T1/01-new-project.png`(新專案 0 物件)、`screens/T1/40-p2-dialog-page2.png`(A4 第 2 頁預覽)。
- 流程 3/4:`screens/T2/057-A-closed.png`、`screens/T2/061-edit-edge1.png`、`screens/T2/094-L-edited.png`、`screens/T2/133-shapelib-L.png`(形狀庫 L 缺口在右下、兩臂同寬,做不出 PDF 的 L,屬 T2-06 觀察)、`screens/T2/m06-closed.png`、`screens/T2/m15-library.png`;V1 `screens/V1/V18-after-place.png`(放置後「投影視圖(仰視)」)、`screens/V1/V22-faces-list.png`(8 面皆 +1 實際邊界)。
- 流程 5/6:`screens/T3/s11-renamed.png`、`screens/T3/s32-sm-library.png`(兩筆空間模型 60 / 77.985 m³)、`screens/T3/s81-subgrid-invalid-click.png`(700 不可 3 等分拒絕)、`screens/T3/s99-state.png`(再匯入同頁得獨立面,T3-05)。
- 流程 8:`screens/T4/pre-cap-face1.png` vs `screens/T4/post1-cap-face1.png`(面內底圖/校準保存前後)、`screens/T4/post1-space3-created.png`(第二輪 82.5 m³)、`screens/T4/r2-d03-preview-top-before-align.png` vs `screens/T4/r2-d05-preview-top-after-align.png`(對齊前後俯視)、`screens/T4/r2-o01-saved.png`、`screens/T4/r2-p03-reload-final.png`(同分頁重新整理自動恢復)、`screens/T4/guard-5-after-cancel.png`(dirty 開檔按取消世界不變)、`screens/T4/example-opened.png`(examples/space-model-v1.gcanvas 可開)、`screens/T4/ten-05-preview.png`(十邊含牆被 I33 拒絕)。

**隱私清洗**:所有文字檔中的本機使用者路徑換成 `<QA>`/`<TEMP>`/`<HOME>`、session 值換成 `<session>`;截圖為無頭 Chrome 的 app 畫面。
