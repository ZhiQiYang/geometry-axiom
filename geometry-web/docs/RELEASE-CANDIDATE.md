# 交付候選與反覆驗收（2026-10-07）

本輪以已批准功能在同一版本正常運作為目標，不增加未定案幾何語義。公理仍以
`公理層.md` 為準；正式交付狀態取決於下列實際收據，不取決於 PR 數量或單一 CI 綠燈。

## 候選範圍

獨立分支 `codex/release-readiness-20261007`，由 main `6562fa5` 的已批准工作整合：

| 功能／修正 | 保留的 PR 與精確來源 |
| --- | --- |
| A/B 完整專案、來源顯示保存、有限規則案例、字級／對比 | #137 `3897577` → #143 `6ae8e11` → #146 `d0c5671` → #147 `fb321eb` → #148 `aa91cd2` |
| 來源子規則、空交集、完整定位焦點 | #134 `b88545e`、#160 `2228da1` |
| 模型庫歷史、跨專案復原、有效草稿保護 | #159 `e3ddd74`、#161 `92ded63` |
| 單房平移及尺寸 Enter | #153 `349e2a5`、#155 `f1e020c` |
| PDF 資源釋放、非同步 guide 所有權 | #154 `83769b9`、#156 `2a7d9cb` |
| 瀏覽器通知分類、Windows binary 身分核對 | #144 `7cfa1a8`、#136 `cc3c1c4` |

#141 的九個元件檔已逐 blob 包含在 #146。獨立 work-manager、未定案多房自動辨識
及施工反向推演不加入這次候選。此表是來源紀錄，並非借用上述各分支的驗收結果。

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
| 規則案例 | formal app 及 races；六有限案例、retention 單步 history、歷史未核信、來源變更過期、B 退休隔離 |
| 回報 | 真瀏覽器 ResizeObserver／真錯誤／人工回報 gate；非預期 exception 不忽略 |
| 使用者操作 | 桌面、390px、短高度，真滑鼠與鍵盤；建立→編輯→確認→復原→重做→下載→新專案→選檔重開 |
| 交付與恢復 | 全新 checkout／TEMP／profile、同服務 reload、唯讀／接管、損壞檔零提交、自有服務重啟後重開完整 `.gcanvas` |

具體命令及每個 gate 的語義見 [INTEGRATION-GATES.md](../../tests/INTEGRATION-GATES.md)。
測試只使用專屬服務、native process、feedback/profile 和合成來源；不使用使用者正在編輯的服務。
所有原始日誌、畫面、下載檔與前後 runtime 收據保存於本次 TEMP evidence 目錄。

## 仍須明列的交付限制

- Linux Chromium 的窄 viewport 不能證明實體手機、IME、Windows GDI/SAC 或 OS 原生 Save picker。
- Windows 一般入口仍為 `geometry-web/start.ps1`；啟動前後須核對 `/runtime`，不能以首頁 HTTP 200 代替。
- A/B active B 中斷目前保全 ticket/native B 並拒絕不安全續接；明確捨棄與已完成 Finish 的恢復須實測，不能宣稱任意中斷均可續編。
- 遠端 CI 若在任何 step 前失敗，記錄為基礎設施阻塞；本地實測結果與遠端結果分開。
- `.scene` 僅是原生幾何，不是包含來源、模型、草稿和方案的完整專案备份；交付及搬移使用 `.gcanvas`。

本輪逐輪結果、精確受測版本、原始收據位置及未解除阻塞記錄於候選 PR 的驗收說明。
此文件定義範圍與停止條件，本身不是正式發佈聲明。
