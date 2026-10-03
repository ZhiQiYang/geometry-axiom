# 可接續工作包：2026-10-03

基底：`0f3c1a6fdd88bbcce4484a256d45900bd1d92313`，唯一 repo ZhiQiYang/geometry-axiom。使用者 19:47 授權本輪**規格、依賴、repo 文件及工單整理，交付 draft 文件 PR**；不是產品實作、公理採納、合併或部署授權。本文第一批先交付總表、WP45 與 WP24，其餘工作包在同一文件 PR 接續補齊。

`公理層.md` 是 SSOT；[產品願景](PRODUCT-VISION.md) 仍為草案。[集中決策包](CONTINUATION-DECISIONS-20261003.md) 的建議全部待採納，不能由本文件標題或 issue 指令自行變成正式契約。#47 雙向定位已取消，**不加入本佇列，也不以共用身分工作偷渡重啟**。

## Readiness 與執行順序

「規格 ready」表示可準備精確契約、正反例與驗收稿；「既有契約可接續」表示不需要新增幾何語意，仍須另取得產品實作指令；「需決策」只能準備 proposal。這輪產品碼全部不開工。下表未填結果不是 pass；本輪未重跑任何產品驗收。

| 工作包 | 下一個最小切片 | 門檻／相依 | 規格狀態 |
|---|---|---|---|
|[WP45](#wp45) / #45|既有無限來源＋邊界的情境入口；草稿保存另切|Q31 草稿附件；既有 D29/D30/I37；避開 PR73/74 app 整合|既有契約可接續；附件需決策|
|[WP44](#wp44) / #44|F1a 缺少來源入口的型別清單；F1b 明選重建契約|Q32 來源沿革／更新方式；不含 #47 双向定位|唯讀規格 ready；重建需決策|
|[WP46](#wp46) / #46|A/B 完整固定快照保存＋新上下文讀回|Q33 方案閉包／採用／能力契約；不依賴 F1b 全完成|需決策|
|[WP48](#wp48) / #48|人工 EvidenceLink：原頁範圍＋參數欄位，保存讀回|Q34 證據附件／沿革；PDF snap 另一 owner|需決策；座標規格可先準備|
|[WP49](#wp49) / #49|固定 authoring 正反案例的隔離真核心結果|Q35 案例斷言／結果版本／保存契約；不等 #25 任意生成|需決策；fixture 規格 ready|
|[WP57](#wp57) / #57|來源子規則總路線與驗收閉環|#58 採納後才能啟動 #59–61|規格協調 ready，產品需決策|
|[WP58](#wp58) / #58|逐條公理差異＋身份／引用／保存提案|Q36 來源子規則；不分配正式條號／格式|proposal ready|
|[WP59](#wp59) / #59|單格按需原生查詢，再引用／全依賴交易|#58 明確採納；#60 同一原生整合 owner|產品阻擋，正反例規格 ready|
|[WP60](#wp60) / #60|來源規則與未提交草稿的完整保存讀回|#58 採納＋#59 interface；不沿用 /8、/9 偷塞新義|產品阻擋，能力矩陣 ready|
|[WP61](#wp61) / #61|既有來源工作區新增／預覽／確認一條規則|#58–60 固定；GEO-219 減項與實體手機拆開|產品阻擋，流程規格 ready|
|[WP62](#wp62) / #62|SR01–24 對照與獨立預期、最後整合真 UI|#58–61；SR24 必須實機|驗收準備 ready，產品驗收未跑|
|[WP24](#wp24) / #24|A01–23 證據索引＋A24 真 iOS 人工工作包|既有 #51/52/53/55 交付；PR73 独立 owner|索引準備 ready，A24 等實機|

同一 repo 文件分支只有一個寫入 owner；PR73 undo/redo 與 PR74 PDF snap 已有執行者，不修改其 app.js、reference-workspace.js、room-outline.js 或驗收檔。BACKLOG 的本條目僅追加文件佇列，合併時保留其他 owner 新增內容。

<a id="wp45"></a>
## WP45 — #45 情境入口的下一個有限切片

**已存在**：PR69 的 published-rule→材料配置入口；`context-operations.js`、原生固定規則指紋、角色／尺寸来源及 create/edit 寫入守門。#25 的 D34/I42/R35 三構件生成也已合併，不能再以「生成器尚未實作」當前置。未交付的是另一條 grid-source＋boundary 情境入口、未提交 grid 草稿持久保存及超出既有生成契約的擴充。

**最小切片 WP45-A**：明選一個既有無限 GridSystem 和一個合法 boundary → 顯示既有配置操作／未填欄位 → 開既有配置表單，帶入兩個 typed ID 和固定來源 → 用現有 preview/confirm 完成配置。選取順序／同名／卡片位置不猜來源、角色或角度；缺能力、未讀取、缺欄位、非法來源分開呈現。先不新增保存格式，也不新增可永久存在的規則或子規則。

**依賴與落點**：`geometry-web/context-operations.js`、`app.js` 的既有選取 disclosure、`grid-system-workspace.js` 與既有 binding bridge；D29/D30、I37 與 [無限網格提案](../geometry-core/INFINITE-GRID-PROPOSAL.md)。共用 app.js 等 PR73/74 owner 完成交付再指定單一接線者，操作描述／typed fixture 規格可獨立並行。WP45-B 的來源草稿保存依 Q31，不隱含使用 assemblyDrafts 存 grid 值。F2b 只接現有三構件生成端點；任意拓樸另 proposal，不列成 ready。

**驗收稿**：兩個同名 system、合法零號與不同 kind 同號不混淆；選取次序反轉結果同義；已用／MAX／草稿 ID 不撞號；來源刪除、讀取過期、切專案、晚回覆、取消均不建物件；成功 preview/confirm 和 undo/redo 由真核心走原交易；desktop/390px 真入口完成一次配置並確認無未捕捉例外；390px 不算 iOS。最終產品 PR 才要求同 head 原生／Node／完整 CDP、必要 space 與版本閉包，這輪全部未執行。

**減項與 readiness**：沿用單選 disclosure，合併原「來源→配置」重複操作說明；不加常駐工具列／第二配置管理器，每畫面常駐說明 ≤3。A 為既有契約可接續的規格工作；B 需 Q31 採納。

<a id="wp24"></a>
## WP24 — #24 證據收尾與 A24 實體 iOS

**已存在**：A01–A23 的 authoring 整合／#51 草稿與防撞／#52 native create/edit／#53+55 有限生成證據。A10 只覆蓋首版 schema 對不支援巢狀的拒絕，不能宣稱執行不存在的遞迴求值器。既有完整回歸數字屬原 head，不能複製成新 main 實跑結果。

**最小切片 WP24-A**：把原 A01–A23 每列接到既有 test file/name、原命令／exit、精確 commit、artifact 與適用能力，標出失效／未知版本／平台 skip。索引文件完成不代表新增產品功能。WP24-B 是真 iOS 使用者工作包：在可核對 fresh runtime 的正式版本建立／編輯規則、未選齊材料保存草稿、鍵盤中文／數字輸入、返回／焦點、檔案選擇器開啟、保存／下載位置與再開，逐步記錄 iPhone/iPad、iOS/Safari 版本、操作、結果與檔案位置；私人專案不上傳。

**依賴與落點**：[ASSEMBLY-CLOSEOUT-20261003.md](../geometry-web/docs/ASSEMBLY-CLOSEOUT-20261003.md)、`geometry-web/docs/assembly-validation/`、#24 原矩陣；`assembly-workspace.js`、`project-store.js` 與 `reference-workspace.js` 只是未來產品故障的落點。本輪不改。PR73 busy lock/undo repaint 由別人負責；索引可準備，A19 最新異步回歸待該 owner 同 head 證據。

**驗收稿與保留**：A24 必須逐項實機記錄，桌面390px、CDP chooser 替身、綠 CI、Linux 均不能代替。Windows GDI／原生手測另列平台，不混在 iOS pass。拒絕／取消保持 World、dirty、history、草稿；原生版本／fresh mismatch 先停止該操作並保全專案。只有有關產品變動才在自有 cloud 再跑必要回歸；不因 A24 待實機而阻擋其餘文件包。總工單仍 open，PR 使用 Refs，不用 Closes。

## 交付與稽核

工作包固定後，各產品 slice 必須另立 isolated branch/owner，先核對最新 main/進行中 PR；建立完整契約與可重現驗收，再寫產品碼。保存未知能力應在替換 World 前拒絕；.scene 不能冒充完整 .gcanvas；現在正式可讀 /1–/9，新增附件不能佔用既有 /8（生成）或 /9（輪廓收據）。不用私人圖紙、付費、變更安全、重置用戶服務或自動合併。

本輪驗證只包括文件路徑／錨點／issue 連結、差異範圍、規格與採納狀態一致性；沒有宣稱產品測試完成。
