# R16 v2：網格標籤、鍵盤焦點與頁尾完整顯示

基底：`b3c4b981bb96b118c1c05b7a1bd98062d710c8b2`。承接 #461 R5／#454 F，取代 #123 的 R16 v1 候選（設計 7169732896 的 R16 部分、T 7169936499、P 7169937327）。v1 未採納，v2 為完整替代 T／P，不疊在 v1 上。

## 範圍及取捨

本片讓簡式網格 label 使用既有 root `--muted`，為簡式／完整表單及複合欄位補共用 accent 鍵盤焦點，並將手機完整工作區的固定頁尾收進實際 scrollport。沒有新入口、說明塊、色票 stylesheet 或保存欄位。沿用現有 `#giName/#giUStep/#giPreview/#gridObjectOpen`、`#igName/#igUStep/#igSaveSource/#igSaveBinding/#igDiscardDraft/#igDiscardConfirm`。

G1、G2 是 P2；v1 把容易隔離的候選稱為影響最大，理由不足。43 項的新盤點應優先排 P1 B2／X1。本次只修已交候選的缺陷；G2 全工作區密度統一與 X1 六區文字色仍未完成，不再用這片代表完整統一。

| 待定選擇 | 選項與影響 | 建議與本片狀態 |
|---|---|---|
| 桌面密度 | A 保留原桌面高度／字級；B 一般輸入與主要動作全寬度最小 44 px，提高觸控容錯但減少可見內容 | 推薦 A 先保留；B 應先以六工作區同場景核對資訊密度。本片沒有採用 v1 的桌面 44 px／14 px 提案。 |
| 完整工作區 label | A 保留繼承深色 ink 與原 12 px；B 改為 muted 及 13 px，字較大但對比降低 | 推薦 A；本片保留現況。若選 B，須實機比較閱讀性後另片。 |

`grid-system-workspace.css` 原本已有 scoped `--muted:#526579`。v1 新增的是 alias 並把此 scope 改指 alias，並非首次引入該 hex／scope；它仍不符合直接共用 root 的設計說法。v2 撤回新 alias 檔與載入修改，簡式 label 直接引用 root；完整工作區原有 scope 不動，避免連帶改非本片的輔助文字。完整 label 仍繼承原 ink，沒有改淡。

原 desktop min-height 34／35／38／42 px、字級／半徑及 mobile 規則逐條保留。390 px 簡式一般控件由 main 的 `workspace-height.css` 保持 44 px；680 px 簡式仍沿既有 40 px，沒有暗中全數加高。完整複合框仍為 desktop 38／mobile 44 px，內部 input 扣除兩條邊框為 36／42 px；v2 不把外框與內部命中面冒稱同一高度。完整 input 的 keyboard outline 之外，在 `.ig-pf-box:has(input:focus-visible)` 畫外框，避開原 `overflow:hidden`。

## 定義、歷史及保存相容

D56／D57 將未確認網格原字串放在 World 外的編輯資料；I68 也要求局部歷史不可抹掉來源曾缺失旗標。因此 World 零寫入不能推成所有專案歷史零步。現行 `ReferenceWorkspace.setFeatureAttachment()` 只在資料不同時記一個 local entry；`setGridDraft()` 沿用它。`InfiniteGridWorkspace.flush()` 對乾淨已提交目標不 capture，單純開啟／讀取／焦點不增草稿。

本片完全不改上述實作。P4541 先釘住乾淨完整入口前的歷史，開啟後即核零變化；讀取／焦點階段再次核零變化。真輸入一次並明示捨棄後，要求恰好兩個 local entry、既有 prefix entry 身分及 frame 保持、World dump 逐字相同。新增 Node 特徵測試還用實際 ReferenceWorkspace 實作驗兩次 undo／redo 還原原字串與捨棄狀態，所有 native 呼叫為零。原測試把這段要求成全歷史不變是裁判錯誤；沒有為轉綠改產品歷史。

沒有改 World 指令、bridge、幾何函式、確認資格、草稿格式、`.scene`／`.gcanvas` 編碼器或 I68 校驗。舊檔相容由檔案範圍及上述實作未變支持；本環境不把它誇稱為新版本真冷開實跑。

## 頁尾寬度與保守修正

預審原件在 680 px 報 `rect.right=672`、有效裁切右界 665，差 7 px。main 固定頁尾原本貼 viewport 右側；`.ig-layout` 在此寬度為 scrollport，傳統捲軸占一部分寬度。v2 由 `syncFooterLane()` 實測 `offsetWidth-clientWidth`，同時設定右 inset 與寬度扣量；頁尾左界保持 `viewport − 原 dock 寬`，不侵入畫布 lane。沒有把 7 或 15 px 寫死。

沿原 ResizeObserver 觀察 canvas、footer，另觀察 layout；頁尾仍以實際高度留捲動空間。Node 執行實際 helper，核 0／7／15 px 捲軸及不同 footer 高度。它不能取代 CSS layout 實跑；是否還有其他祖先／固定定位裁切，仍由 P4541 原嚴格 clip 與真五點 hit 在 Chromium 核收。

## 裁判修正與不變守門

- 進場的 `#btnZoom`／卡片／開啟控制使用 main 已有 `entryControlReady`：真可見、enabled、五點全命中。預審 390 的 0.28125 px 祖先裁切差不再被當成本片進場失敗。原 helper 完全未改。
- 表單量測、焦點、輸入與頁尾主動作仍使用原 `controlWithinClip`，完整矩形及五點一個也沒少。1400 的 0.875 px 只靠真 `scrollIntoView({block:'center'})` 重試解決，不加 epsilon、不改 clip 界線、不偽造命中。
- 同為 16×70 ms 有界重試；`throwOnFail:true`、真 CDP Input、requestAnimationFrame 與原 UI 等候預算保持。導航與表單是兩個明示契約，不是把所有完整裁切改為可點擊。
- v1 全桌面 44 px、共同字級／半徑／淡色 label 的候選斷言隨未採納提案一起撤回，改成保持 main 現況的具名斷言。沒有動任何 main 既有套件、canvas 段、golden、byte pin 或時限。
- P4541 三寬 390×844、680×900、1400×900；各走來源與配置簡式→完整路徑，核對比／label policy、原密度／半徑、真 hit／焦點、水平溢出、唯讀歷史與 edit/discard 的 local 兩步／World 不變。fixture 只用 native 建隔離場景，不冒稱使用者建立流程。

## T → P 與具名撤回

| 本機實跑 | base＋v2 T | 同一 T＋P |
|---|---|---|
| `python -B tests/test_r16_grid_form_contract.py` | 7 項，4 pass／3 具名 AssertionError：LABEL_ROOT_TOKEN、FOCUS、FOOTER_GUTTER | 7／7，exit 0 |
| `node --test tests/test_r16_grid_form_runtime.js` | 2 項，歷史特徵通過、FOOTER_LANE 的缺 helper assertion 紅；非 import／ReferenceError | 2／2，exit 0 |

`python -B tests/diagnostics/r16_grid_form_withdrawals.py --out OUTSIDE_CHECKOUT` 逐次複製真相依源碼到臨時目錄。七項：RESTORE_LOW_CONTRAST、REINTRODUCE_SCOPE_ALIAS、REMOVE_COMPACT_FOCUS、REMOVE_FULL_FOCUS、REMOVE_COMPOUND_FOCUS、DROP_FOOTER_INSET、IGNORE_REAL_SCROLLBAR，前綴均 `R16GF_`。每項 baseline／withdrawal／restored = 0／1／0；要求具名 AssertionError，語法、import、timeout 不算 killed。原始 stdout／stderr 與前後來源 hash 隨交付。

這是來源契約與 VM 執行證據。P4541 尚未啟 Chromium；預期 T 在 label policy／focus／footer 等產品斷言紅、P 全綠，必須由雲端原樣實跑確認。沒有冒稱 v2 瀏覽器已綠。既有 P72/P1231、完整 canvas 兩片、native 六片及其他 UI 回歸本輪未跑。

## 片段、成本、衍生物

新增 Python 與 Node 各一個 `tests/suites.d` 片段，皆由 `native_registry.py --init-suite` 產生、仍為 pending-ci-census。P4541 fragment 由 `canvas_registry.js stage-module` 產生，`assertions:0/cost:null` 是候選未驗收標記，不是真 golden。沿 `tests/FRAGMENTED-REGISTRIES.md`，套用端在真 Chromium 全綠後取 Native／Canvas measurement 官方原件並匯入；正式 runner 在 count／cost 未完整前仍拒絕。

`tests/diagnostics/r16_grid_form_golden.py` 維持 v1 原 bytes：它委派現有驗真 importer，核其他段片段 bytes 不變，才在外部目錄產全量 golden。其他片仍 pending 時拒絕，不把本機計數、秒數填進成本。P4541 架構 exclusion 只釘本新測試模組的工具計算 LF hash；沒有手寫掃描、mutation 結果、官方收據或閱讀器 HTML。正式採入後依 CI 重產衍生證據。

## 層級、L4 與檔案交集

目前仍是未採入候選，不上調任何需求帳層級。採入且完整自動 gate／瀏覽器通過才可列本片 L3；L4 要實機走 390／680／1400：選網格來源→簡式欄位與 Tab→完整工作區→核原數值及深色 label→真改名稱→捨棄→復原／重做；再選配置→核 cell／來源→改 cell→捨棄；另走原預覽／確認、保存與重新開啟，留下真 hit、focus、World／草稿與操作原件。這片不結案全部 G2 或 43 項。

產品只改兩個網格 CSS、`grid-system-workspace.js` 的頁尾測量與 `workspace-height-dialogs.css` 的網格 footer；沿既有 #448 高度保留機制。D09 的 engineering-workspace、D06 的 app/cursor 實作不重疊；三片僅 BACKLOG／DOM-CONTRACT 的不同小節有共同檔。與之後 #448 控制 lane／網格完整工作區修改有實質同檔風險，須正常合流再驗；不可宣稱所有未來 PR 任意順序都安全。

GEO-219 減項：簡式 label 不再另維護硬寫色值，焦點沿原 control 與共用 accent；沒有新增提示區或重複主鈕。全工作區密度／色彩的更大取捨已移出這片，等待前述選擇。

## v3：root 色彩繼承修正與重新交付

本次完整 T／P 基底為 `48d5f3887e8cb8d222307db62dbdea287fda8442`，取代中斷索引 7175906485 的 R16 補丁宣告。
舊 v3 原件無法取回，這次從可取回的 v2 原件重建；不重用舊 bytes／hash 或舊驗證結果。
上文 v2 的直接 `var(--muted)` 說法與數字是修正前紀錄，不再代表 v3 的實作。

7174254721 報告的 LABEL_POLICY 失敗成立：root 的 `--muted` 是 #596679，body 已覆寫為 #566b85，
在 label 查找 var(--muted) 取到的是後者，不能稱為 root 顏色。
只在 app.css 的原 `:root` 加 `--form-label-color:var(--muted)`，簡式 label 改讀此 alias。
CSS 自訂變數在 root 計算後繼承，因此 body 的既有 muted 覆寫不再改變這個 label 值。
不新增色碼、不新增 scope、不改完整工作區的深色 label、桌面高度、半徑與字級，也不把 root 顏色搬到 body。

新增契約逐一讀 index.html 實際載入的 stylesheets，要求 alias 只在 app.css 的 :root 宣告一次。
v3 T 配 v2 P 時 LABEL_ROOT_TOKEN／ROOT_ALIAS_DECLARATION 兩項具名紅；v3 P 為 Python 8、Node 2 全綠。
新增 RESTORE_BODY_MUTED_LOOKUP 與 MOVE_ALIAS_TO_BODY，連原七項共九組具名 0／1／0。
P4541 保留對比 >=4.5、root 顏色相等、完整 label 深色 >=12、真完整裁切／五點命中與原 density 判定，
再同時核 root 與欄位繼承的 alias 都等於原 root muted；不把裁判改成「等於當下 body」而放寬。

新增產品交集為 app.css；D06 改 app.js 與 cursor-v2.js，D09 改 engineering-workspace，產品邏輯仍分片。
正式 Chromium 三寬、原 canvas 兩片及成本待套用端實跑，沒有用本機 source/VM 綠燈宣稱 L4。
