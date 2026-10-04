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


## 2026-10-05 納入 #127 後的最終同步與完整回歸

隨後 main 合入 #127，已再普通 merge 納入 `417f4c0`，無衝突；來源 merge `b38c417`。保留參數 owner 的 preview ownership 修正與原有 token 拒絕，沒有修改共用參數功能、C 核心、公理或 golden 門檻。D:\geometry-axiom 的乾淨 main 與 origin/main 已對齊 `417f4c0`。

此来源 B 真 Chrome/native **87/87**；另跑預設完整空間套件 **202/202、completed:true、0例外／console error**（預設模式不含 timber-material／timber-source-guards）。完整 CDP **1407通過／1失敗、completed:false**，止於P73「選已知邊一半產生引用式，位置與走向用語一致」，未比對golden。log中native `line guide 4 1 v 1/2*edge:e1:u` 回ok:true並顯示成功toast；斷言仍false，原因未定案。未將之判為產品已修或擅改guide行為／測試。此輪尚未抵達P76，不能宣稱已越過歷史P76 gate。繼承main的total1987、P76=86、P79=87全部未改。預期fb-auto-probe仍在log，沒有UNEXPECTED EXCEPTION；未完成的terminal receipt沒有exception counter，不自行補成0或1。舊失敗收據完整保留。

最新空間202收據来自 Windows Chrome／相同 Linux 本地 TEMP 後端副本／8814。Windows Python＋WSL橋接的另一次87/2未完成收據保留：完整4模型ZIP重開驗算時15秒signal逾時，無page／console error，不算該Windows後端的空間通過。原a1aa來源曾在Windows完成202項，不能據此代替新版Windows後端gate。Linux Chrome另兩輪完整／空間在原生角色／用途select後卡住，分別746/1和8/2未完成，亦完整保留，不算綠燈；相同後端／相同source改用Windows Chrome重跑，沒有改harness或選擇DOM值。原生select事件相容性是依trace推論，未單獨定案。未更改匯入驗證／逾時或模型核心；Windows後端多模型重開時序與Linux瀏覽器相容性仍交dot／owner評估。

完整 CDP 初次从 WSL 的 Windows 掛載路徑執行時，版本 fresh 檢查單次4.151秒、早段 UI/native 逾時，19/7且未完成，不計通過。另建 1043 檔逐位元相同的 Linux 本地 TEMP 副本（解壓後每檔SHA256讀回相等），fresh 約0.173秒；Windows Chrome／Node 配 Linux 本地後端、完全相同 source／harness／golden／native core 重跑取得上述1407/1未完成收據。feedback在Windows TEMP，服務的/mnt/c路徑指向同一目錄；fixtures以現有wsl path-style傳入，沒有加延遲或降低門檻。Linux來源指紋 `6b910a40e4b5cdb109ba508cc9faae738a8e5fb5c3238806aa7672380abd9d12`；Windows／8817 `d6d3df43d69c82e9b4250368807df84c2325624b2663b36d117f5d700e1ba8aa`，在各自驗證當時fresh；8817最終已停止。

先前 a1aa 來源的共用73／模型39及桌面手機旋轉證據保留原時間與來源；未把它們冒稱為 #127 後重跑。#127 僅加入獨立參數修正；本次完整回歸、87項專項與202項空間套件提供最新來源驗收。8817 再重啟後，原完整保存檔的核心 world.scene 逐字核對通過、當時d6d來源fresh:true；之後最終檢查時8817已停止服務，保留關閉狀況，不將先前fresh收據冒稱為目前仍在服務。完整原檔、1208-byte 原 dump 與再次重啟前 dump 均未覆蓋。使用者全部關閉視窗，未重開 Edge、未宣稱 PDF／草稿 UI 恢復，8765 未動。

最新結構化證據為 `geometry-web/docs/issue116/validation.json` 的 `latest_main_update_20261005`。PR #125 維持草稿交 dot；Hosted CI、最終 head／owner、實體 iOS／IME／OS picker 及跨瀏覽器 gate 保留。


## 2026-10-05 最後同步 #126／正式保存機制

main 在回歸執行中合入 #126，最新為 `8d134fc`；普通 merge `1a21b5d` 沒有衝突。已逐字核對 project-store.js、reference-workspace.js、scene-import-bridge.inc 與繼承 golden，完整保留 main owner 的實作。C 幾何核心、公理及本次3D viewer程式沒有追加修改。依最新 scene-import include 重編隔離 bridge，binary SHA256 `29e735f32cbf857d398da5243c2a16916256ff04e700e4075ada270f137965a4`，已驗包含 final_scene；model-base 核心閉包不變而沿用已驗編譯物。

最新合併來源 B 真 Windows Chrome/native **87/87**，完整 Save／reopen／取消零寫入／確認精確頂點／undo-redo／過期拒写與390／720px均完成，page／console errors為0。共用context／ProjectStore／ReferenceWorkspace races加正式subdivision store：**106/106、0fail、0skip**，含真native import、same-ID／來源閉包及formal archive往返。Linux本地來源副本1099檔解壓後逐檔SHA256相等；Windows B 用分支本身的隔離服務，指紋 `24ed41ec44020f6b729a0d0af672c15adeabe04645be758b71a16dcc16806cf1`、fresh:true，未繞過來源核對。

完整／SPACE的b38／417f凍結checkpoint保留在 `checkpoint_after_pr127_20261005`，不能冒稱為最新#126合併head的完整回歸。最新來源的106與87收據在 `latest_main_update_20261005`；最新combined full／SPACE、Hosted CI與final head／owner審查交dot整合，golden未下修。B的原稿與實作對照、3D同角度／手機圖及0e555ed的真canvas／native dump／體積驗證不變。原sourceguard拒絕Linux不同root與Windows暫存PTY服務在導航前結束的紀錄均保留；最終以hidden獨立服務完成87項，沒有改harness或放寬任何源身分條件。

本地乾淨main與origin/main已在8d134fc；本次修正仍在草稿PR #125。8817先前更新／保存場景逐字載回的成功收據保留，但最終查驗服務已關閉，維持關閉，不重開使用者視窗；完整私人檔與各份核心備份仍在本機，8765未重置。
