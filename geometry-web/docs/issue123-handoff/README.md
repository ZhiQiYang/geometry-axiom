# #123 UI 整合交接包(2026-10-06)

> 本包是**可審查、可接續實作的交付包**,不宣稱 #123 已修好。僅文件,未改任何產品程式。
> 交付後由 dot 核對 ownership,再放行不重疊的程式修改。

## 基準

| 項目 | 值 |
|---|---|
| 被測/被分析 main | `d6b4b450d741fcbbfd75c51631915d3082926990` |
| 七項實測來源 | 草稿 PR #138(`docs/issue123-seven-evidence-20261005` @ `b32cdb57e5f34f0bf493ce3b4c0bab99032fea9e`) |
| 設計原稿 | 《UI設計全面審查.zip》SHA-256 `940ffab7313f1df74eaef48f88e845a8a6533f2583530d2cbfe47cdacf98953d`(私人素材,**未收錄**;本包只引用項目 ID 與自寫摘要) |
| 設計方向 | 桌面 56px 單列 WorkspaceHeader 為已排程方向(不再請使用者選擇);仍須可讀、可達、不遮蔽 |

## 檔案與所有者(一檔一位寫手)

| 檔案 | 所有者 | 內容 |
|---|---|---|
| `README.md` | 協調者 | 本頁:基準、分工、結論、續接範圍 |
| `A-evidence-index.md` | Agent A | 七項實測逐項證據索引 |
| `A-43-map.md` | Agent A | 43 項對映表(狀態只依既有證據) |
| `B-fix-design.md` | Agent B | 四項優先問題的最小改動方案與回歸步驟 |
| `C-review.md` | Agent C | 獨立核對:確定缺陷/設計改善/尚未確認 |

## 本輪執行條件

- 主機 CPU 100%、可用記憶體約 3.5 GB → 本輪**未啟動任何瀏覽器、服務或測試**;所有結論來自既有證據與靜態閱讀。
- 不接管、不修改 dot 的 #134、#136、#137 分支與其檔案;#54 不接管。

## 閱讀順序與優先權

先讀 `C-review.md`。**A、B 與 C 衝突處一律以 C 為準**(C 已逐條附 檔:行;協調者抽查 4 條成立)。A、B 原檔保留原樣以利追溯,不回頭改寫。

## 四個指定問題的現況

| 問題 | ID | 證據 | 根因(C 核定) | 狀態 |
|---|---|---|---|---|
| 選取摘要遮住尺寸 | B6 | 部分重現;遮蔽可由 JSON+程式算出 | fit 時卡片 hidden 只留 40px;**已讀後 dynamic 狀態仍會重現** | 根因成立,B 修法範圍不足;另有 #134 `#feRuleDensity` 搶同位置 |
| 手機三視圖按鈕過小 | D4 / X6 | 僅縮放鈕量到 29×29;`.v3-seg-btn`、`#newZ` 未量 | 三視圖時 `canvas-composition` 關閉,44px 規則失效 | 根因成立;放哪個檔待 dot 決定 |
| 網格縮放工具太遠 | X6 / E6 | 390px 重現(縮放列 y≈1876);桌面不成立 | 手機版設定排在畫布前 | 根因成立;sticky 案無效,order 案反而修正 Tab 順序 |
| 建模預覽被標頭擠壓 | F2(F1) | 只量歡迎狀態(預覽區 176.5px) | 緊湊斷點 800 差 4px;歡迎區絕對定位溢出 | 根因成立;改 900 會改到 1400×900 測試基準,須 #119 協調 |

## 能安全開始實作的檔案範圍(以 C 核定為準)

- **可開始**:`geometry-web/grid-inspector.css`(僅 G3 對比與間距);擴充 `marquee_test.js`、`space_model_test.js` 的量測案例。
- **有條件**:`geometry-web/space-workspace.css`(僅 F1 斷點/歡迎區溢出)— 先取得 #119 負責人同意。F5/F6 等 S1 tokens 定案。
- **須等 dot**:`app.js`、`app.css`、`grid-system-workspace.css/.js`、`index.html`、`docs/DOM-CONTRACT.md`、`cdp_*`、`tests/run_all.*`(#134/#137 持有);`workspace-shell.css`(S1 共用標頭);`project-ui.css`(#116/#77)。

## 交接記錄(與 dot 活躍工作重疊)

- B6 修法需改 `app.js`(#134 持有),且 #134 新增 `#feRuleDensity`(top:42)與選取卡片同位置 → 建議 #134 合併後由同一 writer 一併處理浮層避讓。
- X6 需改 `grid-system-workspace.css`(#134 持有)→ 交 dot。
- #138 README 有三處數值與 JSON 不符(B6 主畫布、F6 顏色、F5 鍵名)→ 建議 #138 作者勘誤;本包不改 #138。

## 未完成/未驗

- 本輪未做任何實測。待測清單與通過條件見 `C-review.md` 第三節(焦點框、B6 已讀後、cdp_test 等待條件、F6 12px、G3 刪除確認)。
- 43 項中 30 項「未驗」;D4 三視圖勾選熱區、F2 建立後 3D canvas 未實測。
