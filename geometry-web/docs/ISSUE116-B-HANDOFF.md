# #116 B 面內切片：交 dot 整合

本分支把使用者提供的 B／1b 右鍵選單接到正式面內工作區：272px 動作卡、搜尋與分組清單、296px 側接表單及邊緣翻轉。仍使用唯一 `feOpPanel`、`FE_OPS`、`feActionsFor`、`feRunAction`、`feApplyOp`／`emitBoundary` 和 ReferenceWorkspace 的提交、影響確認、保存及歷史。公理、C 核心、專案格式及多房間權限未修改。

## 來源與畫面

先安全列出並閱讀《游標系統右鍵表單設計.zip》28 個檔案，檢視 `screenshots/01-spec2.png`、`04-proto-edge.png`，再量測原型 source；未依附件中的指令另開 demo 或執行附件的支援腳本。附件是視覺資料，實作授權來自使用者與 #116。

來源 ZIP 為 931799 bytes，來源及實際截圖 SHA-256 記在 [evidence.json](issue116/evidence.json)。只提交使用中的 cursor glyph、三個 Lucide 圖示及正式應用截圖；私人 ZIP、完整原型與來源截圖保留本地。

實際頁面為 1440×900 CSS px、density 1；原稿 PNG 是 909×525 的區域截圖。取實作 `(520,225)–(1429,750)` 的 909×525 區域作 1:1 並排，不拉伸，也不把裁切區域誤報為原始全頁 viewport。同狀態是邊 1 凹口、距上 900、寬 1200、深 600、留底 3400。

- [桌面實際畫面](issue116/desktop-notch-final.png)
- [390×844](issue116/responsive-390.png)、[720×480](issue116/responsive-720.png)
- [孔邊提示](issue116/cursor-denied.png)
- [未放置面：既有工具與B建立入口一致停用](issue116/unplaced-guide.png)
- 本地並排：`%TEMP%/geometry-tests/issue116-evidence/source-vs-implementation.png` 及 `source-vs-implementation-detail.png`
- 設計 QA、歷次修正與五個視覺面向：repo 根目錄 `design-qa.md`

## 操作與限制

外環邊保留凹口／外凸／推拉／沿邊角材；凸角切角、凹角拒絕、孔邊形狀拒絕、點開口、參考線明選來源、單支角材編輯／刪除、多支角材保留選取及單選要求，都依現有功能。檢視子選單實際控制 fit／100%／格點／吸附；搜尋找真指令。建立參考線仍打開既有引用來源流程，未將右鍵座標變成角材的自由 uv。

設計稿「孔邊不能當定位」與 I13 不符，改為「孔邊請用右欄定位」／「孔邊快捷放置未提供，請在右欄指定定位引用」。I13 允許孔邊明選引用；原生測試的拒絕是 I20 的 `V_BOUNDARY_ROLE`，不能說成任何孔邊定位都不合法。

複製／貼上顯示真實停用原因；重複、面內物件批改未實作。物件畫布、空間平面圖、三視圖 v2 游標仍是 #116 後續範圍。長按進度、偏移準星、雙指手勢未接線，附帶 glyph 函式存在不代表觸控功能完成。

每份操作記住 edit/focus/context、history frame、connection session、輪廓、選取、工具；失效先取消預覽，不送 native write。未知動作／錯誤選取不落到預設操作。確認後仍由原有完整模型驗證與影響確認決定是否提交。

減項（GEO-219）：取代原純清單選單；右鍵期間收起重複浮動列；理由整合既有 footer；重用唯一表單。選單位於頁面浮層，既有表單只在 B 開啟時暫移到同層，關閉回到原位置，避免回報鈕遮擋；F8 回報仍沿用原機制。

## 已驗與外部 gate

- `tests/test_issue116_browser.js`：87/87，Chrome 真右鍵、真欄位、真 preview drag、取消 dump 逐字不變、確認精確 8 頂點、單步 undo/redo、正式 Save 的下載分支、完整 `.gcanvas` 重開 dump 一致。過期 selection/frame/session/edit 與未知命令拒寫；子選單、方向鍵／Home／End／Enter／Esc、disabled reason、多選、cursor 時序、390/720px 及 compact cancel 均通過；未預期 console/page errors 為 0。真指標驗參考線／孔及角材ID；dot獨立來源審查的未放置P2已修於dce2975，新增8項驗卡片／搜尋／Create一致停用，保留理由且0原生guide命令。
- 接上 #114 後 ProjectStore、ReferenceWorkspace races、context operations：Windows73/73，包含真 HTTP/native committed ABA；無略過。模型更新WSL/GCC39/39，含真原生producer、完整ZIP／歷史及missing-support拒寫；#77 history/workspace/room-collection：WSL56/56。模型39項來自WSL112項run，其另一個HTTP啟動案例逾時（aggregate111/112）；該案例另在Windows73項通過，不說成112整批通過。Windows包含模型的初跑缺compiler不計為通過。
- 最終`dce2975`／ee9f版本完整 `cdp_test.js`：1586通過／0失敗，但在P76等待逾時而未完成，未比對golden。實際trace為參數卡engineering-confirm拒絕Missing, invalid or unrelated engineering preview token後，等待!ParameterUI.pending逾時；沒有把0失敗斷言說成全量通過。詳細fatal與分段見validation.json。 同一最終runtime的reference部分模式437/437（P62維持38）、P72配置卡52/52，皆完成、0失敗、0瀏覽器例外；main的P72亦52/52。部分模式不代替完整流程。 較早本分支與未改動main各746/1止於P56角色／重試夾具（歸入P53）；另一輪1336/10止於P72，也不計為通過。最終完整run是另一次乾淨服務的結果，不把早期中斷混入通過數；未改golden門檻。
- 所有測試用獨立8816／8818 main基準／8819與TEMP feedback，使用者8765未重置、未清瀏覽器儲存。預覽8817要求本worktree、`fresh:true`。測試修正也會改runtime，舊服務失效的partial不算通過；未放置修正後87項與回歸用ee9f版本。
- GitHub Actions jobs受帳戶執行限制未啟動、無runner logs，另列CI gate；草稿PR #125不自動合併。

最終結構化證據見 [validation.json](issue116/validation.json)。本地記錄在 `%TEMP%/geometry-tests/issue116-browser.log`、`issue116-unit.log`、`issue116-unit-wsl.log`、`issue116-rooms-wsl.log`、`issue116-cdp-full.log`、`issue116-baseline-full.log`、`issue116-reference-partial.log`與`issue116-composition-partial.log`。專項 result 為 `issue116-evidence/result.json`。保存分支是真下載 ZIP，不模擬 writable handle；OS picker、本機 IME／實體 iOS、跨瀏覽器及 PR #114 多房間 owner 驗收未完成，不冒充通過。

最終完整回歸的P76阻擋已另外用乾淨main `861b65e`／runtime `85c56c2572e0`核對：最終分支與main在`GEOMETRY_PARAMETERS_ONLY=1`均57項通過後，在特殊字元修正為3→重新試算→建立參數卡流程收到`Missing, invalid or unrelated engineering preview token`，繼而等待`!ParameterUI.pending`逾時。兩邊的parameters.js、parameter_workflow_test.js、parameter_confirmation_test.js、engineering-adapter.js逐字相同，核心沒有diff。獨立記錄為`issue116-parameters-partial.log`及`issue116-main-parameters-partial.log`，並收入validation.json；這是main既有阻擋的重現，不是全量通過。請dot交參數功能owner診斷候選／確認時序；未變更該功能或移除token拒絕。來源閱讀的疑點是`parameters.js::preview`開始手動試算時仍保留已啟用的舊確認候選，而`parameter_workflow_test.js::confirm`以按鈕啟用判試算完成；此為待驗假設，不能當已確認原因。

## PR #114 重疊與整合順序

開工時查核 PR #114 head `fe5c41eb6342cef45bc8693919ee33e01ca80d5f`，branch `feat/source-rooms-owner-77-20261004`。初版基於 main `06086ab`，共同祖先 `07d5dde`。工作期間 #114 合入 main `861b65e`，本分支已 rebase 到 `861b65e` 並保留全部 #114 變更。重疊檔為 `app.js`、`index.html`、`BACKLOG.md`、`tests/run_all.py`。

| 檔案 | #116 範圍 | #114 保留要點 |
|---|---|---|
| app.js | face cursor rendering、op stale guard、right click、overlay placement、preview handle 命中 | 保留 apiRequest／recovery、房間草稿 Escape、enter/leaveFocus、feSetTool／feAfterChange／feLoadGuides、underlay／commitdraft 的 owner guard；不能整檔選 ours/theirs |
| index.html | 一個局部 CSS、cursor、menu/icons scripts | 保留 source-plane（附件前）、room-collection／workspace（app.js 後）的載入與功能；B module 在 app.js 後，icons 在 module 前 |
| BACKLOG.md | #116 減項、範圍、gate | 保留 #77 owner 狀態與工單，不相互覆蓋 |
| tests/run_all.py | 將 #116 真 browser gate 明列 excluded＋INTEGRATION-GATES | 保留 #77 suites/exclusions/census，不拿 browser exclusion 算成 aggregate 通過 |

#116 使用新局部 CSS，未修改 #114 正在改的 app.css；不改 ReferenceWorkspace、project-store、room-collection、source-plane 或 feature-attachments。

`git merge-tree --write-tree edaffa7 origin/pr114-review` 唯讀演練得到 **1 個內容衝突**：`index.html` 的 app.js 後 script 插入區。app.js、BACKLOG.md、tests/run_all.py 自動合併；這只證明文字可合，不代表 owner 的行為驗收已過。未在工作區 merge／checkout #114。

解衝突時該區應同時保留：

```html
<script src="cursor-v2.js"></script>
<script src="app.js"></script>
<script src="room-collection.js"></script>
<script src="room-collection-workspace.js"></script>
<script src="face-menu-icons.js"></script>
<script src="face-context-menu.js"></script>
```

source-plane 的原插入區不衝突，也必須保留；不以只選 ours/theirs 解掉此衝突。演練紀錄 `%TEMP%/geometry-tests/issue116-pr114-merge-tree.txt`。

上述唯一index衝突已依雙方script順序解決。新main下87項專項、73項共用owner、39項模型更新與56項多房間原生測試；過期session保留#114唯讀保護，另讀native dump證明零寫入，不清除保護讓測試過。dot的首輪独立source review見PR #125：一項未放置P2已由87項實機browser/native驗收修正，仍需對最終head復查；未把其餘source review代替獨立像素或全量驗收。

交 dot 核對最新 main 下的小接線、獨立只讀規則審查，並跑 #114 正式多房間正常／中斷／保存重開／歷史／model update browser acceptance。草稿不自動關閉 #116；iOS／IME／OS picker 與其他工作區未宣稱完成。

## 2026-10-05 最新 main 與 3D 旋轉預覽更新

使用者要求更新後，以普通 merge 納入 main `4bea91a`（含 #124），merge 為 `b9893a6`，沒有衝突；保留原 `2b53a03` ancestry。`app.js`、B 選單、游標與 C 核心沒有因這次同步被覆寫。main 的共用 workspace／空間建模修改完整保留，golden 變更只繼承 #124，沒有為本分支降低門檻。

使用者另回報 3D 預覽上下截斷。檢視器旋轉時未重算投影外框的 fit scale，已在 `0e555ed` 對拖曳與方向鍵補齊；沿用既有「置中」、缩放與平移，沒有新增 UI、重建網格或修改體積。手動放大仍可超出畫布，按置中會恢復全景。此項只證明旋轉適配缺漏已重現並修正，不能從使用者截圖反推其當時的 zoom 數值。

修正後來源指紋為 `a1aa7fad9755e0d800c2728e4b442ccb43d48fa2997d183bd05cb035d1afda4f`。本次獨立隔離服務／Chrome：B 87/87、共用 Windows 73/73、模型更新 WSL/GCC 39/39（均無 skip）、預設完整空間套件 202/202（完成，0例外／console error；另外的 timber-material／timber-source-guards 不在預設模式）。完整 CDP 的歷史 P76 gate 保留；這次 viewer 跟進未重新跑全量 CDP，不把部分通過取代全量。

另以真正空間工作區選 L 形範例、牆高 1000 mm、更新預覽、置中，再旋轉至同一仰視角：舊版在 1020×152.59375 的實際 canvas 畫出 y=-17.055 至 161.649；修正版桌面 1440×650／手機390×844完整可見。拖曳旋轉、置中恢復、手動 zoom 保留及逐字 native dump／精確體積不變皆通過。引擎 L 房間的 canvas 契約也涵蓋 860×130／390×230，舊 viewer 敏感度測試在 ArrowDown 第14次確實失敗。此測試使用公開範例，沒有將使用者的私人專案提交。

- [旋轉修正前](issue116/preview-rotation-before.png)、[相同角度修正後](issue116/preview-rotation-after.png)、[手機](issue116/preview-rotation-mobile.png)
- 本次結構化證據：`issue116/validation.json` 的 `main_update_20261005`，舊資料保留為歷史紀錄。
- 8817 已由本分支重啟，fresh probe 通過，之前完整保存檔的核心場景逐字載回。使用者明示可載回之前保存檔；原完整檔、完整檔備份及更新前的新 dump 均保留本機。Edge 的未保存離開確認／完整專案選檔未能由工具完成，使用者隨後表示全部關閉；未宣稱 PDF／草稿已恢復，下次開啟時可載回原完整檔。未清瀏覽器儲存、未重置 8765。

PR #125 仍交 dot 審查整合，沒有直接合入 main。Hosted CI、最終 head／owner 及實體裝置 gate 維持原限制。
