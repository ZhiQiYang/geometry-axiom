# 交付候選與反覆驗收（2026-10-08）

現行整合草稿為 [#176](https://github.com/ZhiQiYang/geometry-axiom/pull/176)，
分支 `codex/integration-closeout-20261008-r2`，產品驗證候選
`5174a8dafd8c48329d7166abbd3d104e3c28c0c4`。完整版本、命令、原件、
已完成部分與內部／外部未完成项見[本次交付報告](../../tests/release-evidence/20261008-cloud-closeout/README.md)。
候選保持 draft；未合併 main。本頁下方 #169 的數字與環境敘述保留為歷史，不改標本輪。

本輪以已批准功能在同一版本正常運作為目標，不增加未定案幾何語義。公理仍以
`公理層.md` 為準；正式交付狀態取決於下列實際收據，不取決於 PR 數量或單一 CI 綠燈。

## 候選範圍

#169 歷史整合分支為 `codex/final-release-closeout-20261008`，包含 main `5cc1ffa`、
下列原 PR162 候選及新一輪收尾。以下先保留 `codex/release-readiness-20261007`
由 main `6562fa5` 整合的歷史來源，不把舊收據改標成新版執行：

| 功能／修正 | 保留的 PR 與精確來源 |
| --- | --- |
| A/B 完整專案、來源顯示保存、有限規則案例、字級／對比 | #137 `3897577` → #143 `6ae8e11` → #146 `d0c5671` → #147 `fb321eb` → #148 `aa91cd2` |
| 來源子規則、空交集、完整定位焦點 | #134 `b88545e`、#160 `2228da1` |
| 模型庫歷史、跨專案復原、有效草稿保護 | #159 `e3ddd74`、#161 `92ded63` |
| 單房平移及尺寸 Enter | #153 `349e2a5`、#155 `f1e020c` |
| PDF 資源釋放、非同步 guide 所有權 | #154 `83769b9`、#156 `2a7d9cb` |
| 瀏覽器通知分類、Windows binary 身分核對 | #144 `7cfa1a8`、#136 `cc3c1c4` |

#141 的七份實作／測試檔已逐 blob 包含在 #146，另兩份文件分開核對，
不能稱九個可執行元件。#169 當輪另整合：

| 功能／修正 | 保留的精確來源 |
| --- | --- |
| PR162 保存／歷史 oracle 的 A/B/C 補強與負控制 | `8b9b6f8` |
| work-manager 真瀏覽器收尾與鍵盤焦點修正 | #152 `43bf056` |
| 文件與方向同步 | #165 `794569e` |
| Q38 原生完整診斷、typed 來源圖、兩種簡易宿主與轉換 | `fb82d0a`，包含使用者 #167 `fb6ef45` 的跨物件影響揭露 |
| Q38 真模型產生器與完整來源保存 | `4346a50` |
| Q38 2D／3D、共用模型庫、完整 `/16`、late response／history 保護 | `fb619cc` |
| #87 已校準同頁的有界多房 session 與逐房交易 | `87af8b4` |
| 原 Windows／舊分支驗收原件 | #158 `06343d8`；保留原 head、成功及失敗範圍 |

#128 完成面／鋪板的 [PF-0 逐條差異](../../geometry-core/PANEL-FILL-AXIOM-DIFF.md)
仍待使用者採納新精確語意，未提前寫入 SSOT 或實作。#87 未接受候選不進 ZIP，
zero-room first collection 與跨 reload 未接受草稿不屬於本 session slice。
此表是來源紀錄；實際通過與未驗項必須各自附原始收據。

## 每輪的停止條件

1. 凍結產品來源，建立 fresh native receipts，記錄 Git head/tree、runtime 指紋及隔離目錄。
2. 執行完整功能與實際使用流程；保留失敗、超時、部分執行和測試夾具錯誤的原紀錄。
3. 缺陷先重現再修復，獨立複審修正；測試夾具錯誤須說明原因，不能放寬產品條件補綠。
4. 產品改動後重跑受影響流程；最終來源凍結後通過必要完整閘門。
5. 以不同角度再檢查完整使用流程與中斷／恢復，連續兩輪未發現新交付阻塞才評為候選穩定。

「未發現問題」只適用於記載的平台、資料與操作範圍，不表示所有可能情境均無缺陷。

## 驗收矩陣

| 層次 | 必要證據 |
| --- | --- |
| 核心及契約 | 嚴格 `tests/run_all.py`，既有 floors／具名平台 skip；不可用 update-expected 消除失敗 |
| 全產品回歸 | 無 scope flag 的 `cdp_test.js`、完整 `space_model_test.js`、獨立 timber；記錄 completed、scope、golden/floor、exit |
| A/B 及來源顯示 | native 300 次生命週期、scenario workflow/lifecycle、shared-room display；B 不改 A、整體採用、Undo/Redo、完整 ZIP |
| 保存與來源 | #77 正式 owner 五項及四個 browser gates、#116、#48 evidence、#61 reader；原圖 bytes／身份／raw 草稿完整保留 |
| 單房 | acceptance、pan、worker、keyboard 四個完整 gates；PDF／圖片、校準、尺寸、確認、取消及真保存重開 |
| 多房 session | 固定 34 項正式 gate，並保留 #77／shared-room display／#54 受影響回歸；命名取消與回覆遺失不得殘留 owner |
| 斷面拉伸 | 原生 26／模型 19、UI 68、fresh-browser 完整保存 18 各自記錄；兩種宿主、精確模型、來源圖、所有影響與取消／歷史 |
| 規則案例 | formal app 及 races；六有限案例、retention 單步 history、歷史未核信、來源變更過期、B 退休隔離 |
| 回報 | 真瀏覽器 ResizeObserver／真錯誤／人工回報 gate；非預期 exception 不忽略 |
| 使用者操作 | 桌面、390px、短高度，真滑鼠與鍵盤；建立→編輯→確認→復原→重做→下載→新專案→選檔重開 |
| 交付與恢復 | 全新 checkout／TEMP／profile、同服務 reload、唯讀／接管、損壞檔零提交、自有服務重啟後重開完整 `.gcanvas` |

具體命令及每個 gate 的語義見 [INTEGRATION-GATES.md](../../tests/INTEGRATION-GATES.md)。
測試只使用專屬服務、native process、feedback/profile 和合成來源；不使用使用者正在編輯的服務。
所有原始日誌、畫面、下載檔與前後 runtime 收據保存於本次 TEMP evidence 目錄。

## #169 歷史實測結果與可核查證據

原整合產品／完整測試凍結為 `459478e9f68fe8ee9252a5f6b4a1ffb2213a5207`。
驗收保留各次實跑版本；後續文件與證據提交另核對差異，不將舊收據改標為新版執行。

- `07bca299`：完整非瀏覽器登錄 82 suites，2571 pass、0 fail、1 具名 Windows GDI skip；
  其中 6 個 suites 僅核對 exit，不加入斷言數。完整 mutation 實跑於 `9357d0b9`：
  baseline 139，48 筆為 40 killed、1 crashed、4 equivalent、3 retired。
  最新原生／模型編譯閉包與 mutation 裁判、工具、結果未變，唯讀 freshness check 通過。
- `3c65ced`：多房、A/B、來源及其他較早獨立 gates 照原版本保留；
  本輪重新驗收的範圍以最新收據為準。`5c3d36c` 的獨立 timber 79、服務重啟重開 13 仍保留原 head。
- `459478e`：模型庫歷史 35、一般保存重開 33、Q38 全新瀏覽器保存 18、Q38 UI 68、
  完整 Space 228、P80／P81／P85 共 68、canonical room 120 各自通過；
  另有 P83／P86 診斷載入 36，範圍與 canonical 完整 CDP 分開。
  直接依賴空間工作區的模型保存／歷史 Node 單元測試另補跑 48/48（mock DOM，不取代瀏覽器）。
  **完整 CDP：2177/2177，84 段逐段符合 golden；full 無 scope filters／modifiers，0 fail／skip，0 非預期例外（P38 具名預期探針 1 次）。**

本輪三次完整 CDP 紅燈均保留。`5c3d36c` 僅修正 P69 測試的完整期望值，
恰好包含測試刻意新增的 `specs`；`f23a65a` 修正工程差異畫面遇到無效候選 `null`
幾何時崩潰，保留未求值資料與原生診斷並拒絕確認不完整候選，其工程 P69 160、
實際函式 17 與相鄰流程 8 項檢查照原範圍保留。`459478e` 再修正 Q38 來源晚回時
重建整個模型庫、移除已展開來源檢視器的競態，改為只更新 Q38 卡片。
原 P85 的 29 項全保留，新增 2 項真原生回覆延遲回歸；P85 為 31、完整 CDP golden 為 2177。

`3c→5c` 的測試檔同一性不能延伸成後續產品同值。各檢查數不相加為不重複使用情境；
command wrapper 的執行證明與各 harness 的完整結果數分開核收。
[驗收矩陣、版本與收據](../../tests/release-evidence/20261008/final-validation-matrix.json)、
[主要／完整 CDP 兩份證據包的逐檔清單](../../tests/release-evidence/20261008/integration-evidence-manifest.json)、
[23 個 open PR 的來源覆蓋](../../tests/release-evidence/20261008/final-pr-source-coverage.json)及
[PR162 原始 oracle 包核收](../../tests/release-evidence/20261008/pr162-oracle-inventory.json)
提供追查入口；open PR 數量不等於尚未整合的功能數。

既有 Hosted CI run [37751080937](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37751080937)
的七個 jobs 因帳務／支出限制在 step 前失敗；發布時 CI 狀態另記於候選 PR。
Linux Chromium 不涵蓋 Windows P70／P88、GDI／SAC、實體手機／IME、OS 原生 Save picker
或私人實圖。PR161 原十項腳本與舊 155 的完整重現來源仍缺件，現存歷史通過收據照原版本保留。
#128 PF-0 的新精確語意仍待採納，SSOT 與唯一閱讀器未變；以上未宣稱合入 main 或部署。

## 追加 PR168：等待卡片位置確實保存

原整合證據封存後新增的 [PR168](https://github.com/ZhiQiYang/geometry-axiom/pull/168)
已以普通 merge 保留 `a1b2f785` 來源，再於 `b822a9ff7c0deb74f7d6f05e70aa43d6f00dd8d5`
補強共用測試 helper。卡片拖曳須等到原生位置改變且頁面副本一致；原生或本地物件不存在、
API 失敗、未保存位置、非有限座標或逾時均不能判為成功，未回覆的讀取也受 deadline 限制。
首次拖曳尚未保存時則繼續等待，不會提早判成功或失敗；舊 helper 的過早拒絕已有真瀏覽器重現。
這一輪僅改測試與其登錄，產品、原生核心、SSOT 及唯一閱讀器保持原內容。

此 clean head 的追加驗收：canonical GRID 316、ASSEMBLY 150、COMPOSITION 52；
focused Node 30（新 helper 21、既有 CDP evaluator 9）；四種卡片實際拖曳 20、
首次保存等待 5，以及獨立 VM 對照 14，各自附收據且不相加為不重複使用情境。
四種卡片 probe 不冒充早段 P5／P11 整段 canonical 執行。
各範圍完整結果及實跑身分見
[追加矩陣](../../tests/release-evidence/20261008-card-wait/followup-validation-matrix.json)、
[來源同一性與新增 PR 覆蓋](../../tests/release-evidence/20261008-card-wait/source-equivalence.json)、
[封包清單](../../tests/release-evidence/20261008-card-wait/manifest.json)及
[獨立核對](../../tests/release-evidence/20261008-card-wait/independent-review.json)。

原 full 2177 保留 `459478e` 的原 harness 與執行身分；此次沒有把 partial scopes 改稱新版 full 重跑。
新增 Node suite 已登記獨立 21 項 floor，所有原有 suites 的 floors 未降低；原 82 suites／2571 pass
仍是 `07bca299` 的實跑紀錄，未宣稱新版 aggregate 已重跑。
PR168 原 Windows 205 項使用較舊 bridge 與 main 基底，只保留原有限範圍，
不替代最新 Windows P70／P88 或完整平台驗收。

#169 當輪最後遠端核對的 24 個來源 PR 中，只有 PR165 自原覆蓋快照前進到 `354bad2`。
該提交僅為 [AUX 審查文件](AUX-REVIEW-20261008.md) 新增 26 行，已另行保留來源；
其中「未驗」與未完成紀錄均屬文中指定的舊候選／Windows 執行，不改標成本輪結果。
實際文件合併與發布差異見
[發布清單](../../tests/release-evidence/20261008-card-wait/publication-manifest.json)。

## 仍須明列的交付限制

- Linux Chromium 的窄 viewport 不能證明實體手機、IME、Windows GDI/SAC 或 OS 原生 Save picker。
- Windows 一般入口仍為 `geometry-web/start.ps1`；啟動前後須核對 `/runtime`，不能以首頁 HTTP 200 代替。
- A/B active B 中斷目前保全 ticket/native B 並拒絕不安全續接；明確捨棄與已完成 Finish 的恢復須實測，不能宣稱任意中斷均可續編。
  #176 已另核 Finish／捨棄及生命週期；完整 Resume 仍需修改前持久化資格、metadata／World／ticket
  的同一工作歸屬，見[獨立審查](../../tests/release-evidence/20261008-cloud-closeout/report-support/resume-independent-review.md)。
  `tests/INTEGRATION-GATES.md` 中 AF_UNIX／未啟動 browser 段落只描述舊輪；
  現行實跑以[閘門矩陣](../../tests/release-evidence/20261008-cloud-closeout/gates/matrix.md)為準。
  該命令檔仍由 #175 owner 維護，精確過期段落已列交接，未競寫或把舊結果改綁。
- 遠端 CI 若在任何 step 前失敗，記錄為基礎設施阻塞；本地實測結果與遠端結果分開。
- `.scene` 僅是原生幾何，不是包含來源、模型、草稿和方案的完整專案备份；交付及搬移使用 `.gcanvas`。

現行 #176 的逐輪結果、精確受測版本、原始收據及未解除阻塞以本頁頂端交付報告為準。
此文件定義範圍與停止條件，本身不是正式發佈聲明。
