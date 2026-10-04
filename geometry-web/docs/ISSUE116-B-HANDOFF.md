# #116 B 面內切片：交 dot 整合

本分支把使用者提供的 B／1b 右鍵選單接到正式面內工作區：272px 動作卡、搜尋與分組清單、296px 側接表單及邊緣翻轉。仍使用唯一 `feOpPanel`、`FE_OPS`、`feActionsFor`、`feRunAction`、`feApplyOp`／`emitBoundary` 和 ReferenceWorkspace 的提交、影響確認、保存及歷史。公理、C 核心、專案格式及多房間權限未修改。

## 來源與畫面

先安全列出並閱讀《游標系統右鍵表單設計.zip》28 個檔案，檢視 `screenshots/01-spec2.png`、`04-proto-edge.png`，再量測原型 source；未依附件中的指令另開 demo 或執行附件的支援腳本。附件是視覺資料，實作授權來自使用者與 #116。

來源 ZIP 為 931799 bytes，來源及實際截圖 SHA-256 記在 [evidence.json](issue116/evidence.json)。只提交使用中的 cursor glyph、三個 Lucide 圖示及正式應用截圖；私人 ZIP、完整原型與來源截圖保留本地。

實際頁面為 1440×900 CSS px、density 1；原稿 PNG 是 909×525 的區域截圖。取實作 `(520,225)–(1429,750)` 的 909×525 區域作 1:1 並排，不拉伸，也不把裁切區域誤報為原始全頁 viewport。同狀態是邊 1 凹口、距上 900、寬 1200、深 600、留底 3400。

- [桌面實際畫面](issue116/desktop-notch-final.png)
- [390×844](issue116/responsive-390.png)、[720×480](issue116/responsive-720.png)
- [孔邊提示](issue116/cursor-denied.png)
- 本地並排：`%TEMP%/geometry-tests/issue116-evidence/source-vs-implementation.png` 及 `source-vs-implementation-detail.png`
- 設計 QA、歷次修正與五個視覺面向：repo 根目錄 `design-qa.md`

## 操作與限制

外環邊保留凹口／外凸／推拉／沿邊角材；凸角切角、凹角拒絕、孔邊形狀拒絕、點開口、參考線明選來源、單支角材編輯／刪除、多支角材保留選取及單選要求，都依現有功能。檢視子選單實際控制 fit／100%／格點／吸附；搜尋找真指令。建立參考線仍打開既有引用來源流程，未將右鍵座標變成角材的自由 uv。

設計稿「孔邊不能當定位」與 I13 不符，改為「孔邊請用右欄定位」／「孔邊快捷放置未提供，請在右欄指定定位引用」。I13 允許孔邊明選引用；原生測試的拒絕是 I20 的 `V_BOUNDARY_ROLE`，不能說成任何孔邊定位都不合法。

複製／貼上顯示真實停用原因；重複、面內物件批改未實作。物件畫布、空間平面圖、三視圖 v2 游標仍是 #116 後續範圍。長按進度、偏移準星、雙指手勢未接線，附帶 glyph 函式存在不代表觸控功能完成。

每份操作記住 edit/focus/context、history frame、connection session、輪廓、選取、工具；失效先取消預覽，不送 native write。未知動作／錯誤選取不落到預設操作。確認後仍由原有完整模型驗證與影響確認決定是否提交。

減項（GEO-219）：取代原純清單選單；右鍵期間收起重複浮動列；理由整合既有 footer；重用唯一表單。選單位於頁面浮層，既有表單只在 B 開啟時暫移到同層，關閉回到原位置，避免回報鈕遮擋；F8 回報仍沿用原機制。

## 已驗與外部 gate

- `tests/test_issue116_browser.js`：75/75，Chrome 真右鍵、真欄位、真 preview drag、取消 dump 逐字不变、確認精確 8 頂點、單步 undo/redo、正式 Save 的下載分支、完整 `.gcanvas` 重開 dump 一致。過期 selection/frame/session/edit 與未知命令拒寫；子選單、方向鍵／Home／End／Enter／Esc、disabled reason、多選、cursor 時序、390/720px 及 compact cancel 均通過；未預期 console/page errors 為 0。
- ProjectStore、ReferenceWorkspace races、model update UI、context operations：70/70，包含真 HTTP/native committed ABA；無略過。
- 完整 `cdp_test.js` 最終結果待本輪執行完成後更新。前兩次因畫面遮擋修正主動中止，不能計為通過。
- 所有測試用獨立 8816 及 TEMP feedback，使用者 8765 未重置、未清瀏覽器儲存。預覽用另一個 8817，`/runtime` 要求本 worktree、`fresh:true`。

最終記錄在 `%TEMP%/geometry-tests/issue116-browser.log`、`issue116-unit.log`、`issue116-cdp-full.log`。專項 result 為 `issue116-evidence/result.json`。保存分支是真下載 ZIP，不模擬 writable handle；OS picker、本機 IME／實體 iOS、跨瀏覽器及 PR #114 多房間 owner 驗收未完成，不冒充通過。

## PR #114 重疊與整合順序

查核 PR #114 head `fe5c41eb6342cef45bc8693919ee33e01ca80d5f`，branch `feat/source-rooms-owner-77-20261004`。本分支基於 main `06086ab`；兩者共同祖先 `07d5dde`。重疊檔為 `app.js`、`index.html`、`BACKLOG.md`、`tests/run_all.py`。

| 檔案 | #116 範圍 | #114 保留要點 |
|---|---|---|
| app.js | face cursor rendering、op stale guard、right click、overlay placement、preview handle 命中 | 保留 apiRequest／recovery、房間草稿 Escape、enter/leaveFocus、feSetTool／feAfterChange／feLoadGuides、underlay／commitdraft 的 owner guard；不能整檔選 ours/theirs |
| index.html | 一個局部 CSS、cursor、menu/icons scripts | 保留 source-plane（附件前）、room-collection／workspace（app.js 後）的載入與功能；B module 在 app.js 後，icons 在 module 前 |
| BACKLOG.md | #116 減項、範圍、gate | 保留 #77 owner 狀態與工單，不相互覆蓋 |
| tests/run_all.py | 將 #116 真 browser gate 明列 excluded＋INTEGRATION-GATES | 保留 #77 suites/exclusions/census，不拿 browser exclusion 算成 aggregate 通過 |

#116 使用新局部 CSS，未修改 #114 正在改的 app.css；不改 ReferenceWorkspace、project-store、room-collection、source-plane 或 feature-attachments。Git merge dry-run 結果待首個 commit 後補入。

建議 dot 先決定 #114 的 owner 整合基準，再合此小接線；解 index script 插入衝突時保留雙方新增 script。整合後重跑這份專項、完整 CDP 與 #114 正式多房間正常／中斷／保存重開／歷史／model update acceptance。草稿不自動關閉 #116；獨立只讀規則審查交 dot，尚未宣稱完成。
