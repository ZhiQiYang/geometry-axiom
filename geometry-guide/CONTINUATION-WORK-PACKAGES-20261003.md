# 可接續工作包：2026-10-03

初始產品查核：`0f3c1a6fdd88bbcce4484a256d45900bd1d92313`；本後續文件基底：`9ebf52a1b6519356e9ff677e55b9cf167c47b70d`。唯一 repo ZhiQiYang/geometry-axiom。使用者 19:47 授權本輪**規格、依賴、repo 文件及工單整理，交付 draft 文件 PR**；不是產品實作、公理採納、合併或部署授權。PR75 first head `f742463d76e2e55605e07f6328cc2ae7b93e6f46` 只交總表/WP45/WP24，於20:01:23 UTC外部合併；本後續draft補齊原12包與Q31–Q36選項，另納20:19追加的WP77/Q37多房間，共13包。文件被合併不等於新產品契約已採納。

`公理層.md` 是 SSOT；[產品願景](PRODUCT-VISION.md) 仍為草案。[集中決策包](CONTINUATION-DECISIONS-20261003.md) 的建議全部待採納，不能由本文件標題或 issue 指令自行變成正式契約。#47 雙向定位已取消，**不加入本佇列，也不以共用身分工作偷渡重啟**。

## Readiness 與執行順序

20:23追加的[九項優先缺陷／驗證收斂工作包](PROJECT-REVIEW-QUEUE-20261004.md)已去重建#78–86，排在下表一般新功能之前；前三項已由parent品質owner在9ebf52a真native/Chromium獨立重現，root已分配assembly-quality/import/navigation三owner修復中，非待重現或fixed。新maina274反例未重跑，本worker只文件不競寫。20:22自動辨識順序已納入[同頁A→B→C](PROJECT-REVIEW-QUEUE-20261004.md#auto-rooms)：#54先修單房間失敗→#87同頁多候選→#77共享基準的獨立Boundary。原13項工作包保留；PRIVATE案例只公開[REAL-PDF-01/02歷史結果／新版本未驗索引](PROJECT-REVIEW-QUEUE-20261004.md#private-cases)，原檔留Library。

「規格 ready」表示可準備精確契約、正反例與驗收稿；「既有契約可接續」表示不需要新增幾何語意，仍須另取得產品實作指令；「需決策」只能準備 proposal。這輪產品碼全部不開工。下表未填結果不是 pass；本輪未重跑任何產品驗收。

| 工作包 | 下一個最小切片 | 門檻／相依 | 規格狀態 |
|---|---|---|---|
|[WP45](#wp45) / #45|單選來源→既有邊界picker的守門；pair入口另選，草稿保存另切|Q31 草稿附件；既有 D29/D30/I37；PR73/74已合併，共用app另指單一接線者|既有契約可接續；附件需決策|
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
|[WP24](#wp24) / #24|既有A01–23索引核對＋A24真iOS工作包|既有#51/52/53/55及A24handoff；PR73已合併|索引核對ready，A24等實機|
|[WP77](#wp77) / #77|同PDF一次校準、連續新增獨立房間與來源總覽|Q37共享來源附件/更新政策，非現有Space父子|規格ready；產品需決策|

同一 repo 文件分支只有一個寫入 owner；PR73 undo/redo 與 PR74 PDF snap 已由原執行者交付並外部合併。本文件分支不修改 app.js、reference-workspace.js、room-outline.js 或產品驗收檔；後續實作核對其新接口再指定接線owner。BACKLOG 的本條目僅追加文件佇列，合併時保留其他 owner 新增內容。

<a id="wp45"></a>
## WP45 — #45 情境入口的下一個有限切片

**已存在**：PR69 的 published-rule→材料配置入口；`context-operations.js`、原生固定規則指紋、角色／尺寸来源及 create/edit 寫入守門。#25 的 D34/I42/R35 三構件生成也已合併，不能再以「生成器尚未實作」當前置。未交付的是另一條 grid-source＋boundary 情境入口、未提交 grid 草稿持久保存及超出既有生成契約的擴充。

**最小切片 WP45-A（較小規格建議，尚未選定產品入口）**：單選一個既有兩軸無限 GridSystem → 原「選邊界建立配置」動作 → 在既有boundary picker明選第二個輸入 → 顯示未填vertex/cell/rationalanchor → 沿現有preview/confirm完成配置。補context adapter與來源/邊界pin守門，來源card/action與createBinding(id)目前只預選system，不能宣稱已支持同時帶入boundary。GridSystem/GridBinding 0合法，boundary0非法；同名／卡片位置不猜來源、角色或角度，缺軸／finite不能叫ready。grid沒有已採納独立grid-authoring/1 capability，不拿assembly能力誤守門；驗現行nativegridread/preview支援與fresh版本，指紋領域標明，不比較SI hash與sourceKey。先不新增保存格式／幾何語意。

**另一入口方案 WP45-A2（待UI減項選定）**：exact pair {grid-system,boundary}多選，在現有多選檢查器一對一合併泛用「所選物件」提示與情境操作，不稱沿用单選disclosure，不動Q19主畫布選單。A2較貼原雙物件選取需求，但不是A1已存在/已完成；首版先選一個presentation，resolver/typed輸入共用。

**依賴與落點**：`geometry-web/context-operations.js`、`app.js` 的既有選取 disclosure、`grid-system-workspace.js` 與既有 binding bridge；D29/D30、I37 與 [無限網格提案](../geometry-core/INFINITE-GRID-PROPOSAL.md)。PR73/74已合併，核對最新 app.js 後指定單一接線者，操作描述／typed fixture 規格可獨立並行。WP45-B 的來源草稿保存依 Q31，不隱含使用 assemblyDrafts 存 grid 值。F2b 只接現有三構件生成端點；任意拓樸另 proposal，不列成 ready。

**驗收稿**：兩個同名 system、合法零號與不同 kind 同號不混淆；選取次序反轉結果同義；已用／MAX／草稿 ID 不撞號；來源刪除、讀取過期、切專案、晚回覆、取消均不建物件；成功 preview/confirm 和 undo/redo 由真核心走原交易；desktop/390px 真入口完成一次配置並確認無未捕捉例外；390px 不算 iOS。最終產品 PR 才要求同 head 原生／Node／完整 CDP、必要 space 與版本閉包，這輪全部未執行。

**減項與 readiness**：A1沿原單選系統action一對一合併「來源→配置」重複說明；若選A2則只合併現有exact pair多選泛提示；不加常駐工具列／第二配置管理器，每畫面常駐說明 ≤3。A 為既有契約可接續的規格工作；B 需 Q31 採納。

<a id="wp24"></a>
## WP24 — #24 證據收尾與 A24 實體 iOS

**已存在**：A01–A23 的 authoring 整合／#51 草稿與防撞／#52 native create/edit／#53+55 有限生成證據。A10 只覆蓋首版 schema 對不支援巢狀的拒絕，不能宣稱執行不存在的遞迴求值器。既有完整回歸數字屬原 head，不能複製成新 main 實跑結果。

**最小切片 WP24-A**：現有[ASSEMBLY-RULES-VALIDATION.md](../geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md)已含A01–23分組索引與A24實機handoff；本包核對每列test file/name、原命令／exit、精確commit、artifact及能力，補版本過期／未知／平台skip，不重造矩陣。#52closeout等原head的「生成器未實作」舊段只作歷史，最新有限生成已有#53/55。索引文件完成不代表新增產品功能。WP24-B 是真 iOS 使用者工作包：在可核對 fresh runtime 的正式版本建立／編輯規則、未選齊材料保存草稿、鍵盤中文／數字輸入、返回／焦點、檔案選擇器開啟、保存／下載位置與再開，逐步記錄 iPhone/iPad、iOS/Safari 版本、操作、結果與檔案位置；私人專案不上傳。

**依賴與落點**：[ASSEMBLY-CLOSEOUT-20261003.md](../geometry-web/docs/ASSEMBLY-CLOSEOUT-20261003.md)、`geometry-web/docs/assembly-validation/`、#24 原矩陣；`assembly-workspace.js`、`project-store.js` 與 `reference-workspace.js` 只是未來產品故障的落點。本輪不改。PR73 busy lock/undo repaint已由原owner交付並合併；索引納其實際head證據，不能拿舊UI時序結果冒充新main。本文只整理，不重跑或改其測試。

**驗收稿與保留**：A24 必須逐項實機記錄，桌面390px、CDP chooser 替身、綠 CI、Linux 均不能代替。Windows GDI／原生手測另列平台，不混在 iOS pass。拒絕／取消保持 World、dirty、history、草稿；原生版本／fresh mismatch 先停止該操作並保全專案。只有有關產品變動才在自有 cloud 再跑必要回歸；不因 A24 待實機而阻擋其餘文件包。總工單仍 open，PR 使用 Refs，不用 Closes。

<a id="wp44"></a>
## WP44 — #44 F1a 缺口清單與 F1b 明選重建

**已存在**：[F1a 契約](../geometry-web/docs/SOURCE-INSPECTOR-CONTRACT.md)的有界原生 read index、保存來源 candidate World、逐來源定義／有效值指紋、來源缺失／變更與延續性未知。PR67/70 有限切片已合併；内容指紋相同不證明 incarnation，source-inspector 自訂 definitionFingerprint 不可與另一 JSON/sourceKey 雜湊領域直接比較。

**最小切片**：WP44-A 只整理缺少導航入口的 material/method/spec/datum/old-rule typed nodes、哪些已有現行 locator、哪些缺資料須保持未知，形成原生→adapter→既有檢查器驗收矩陣。現有 live context 內可證明的來源定位才可提接線規格；保存模型的歷史 ID 不自動跳到 live 同號。WP44-B 只提一個普通 plan 模型的明選重建：使用者選原模型及**明確重新選定**現行承載面／所需根物件 → 保留原 settings → 真 producer 候選 → 列明舊／新 input/source/result 差異 → 採用或取消。更新原 model record 還是保留舊模型另存新副本由 Q32 決定；第一版不接無法生成的 assembly-owned／faces+timbers producer。**不包含已取消 #47 料單—模型雙向定位。**

**依賴／落點／並行**：Q32、`source-inspector.js`/`source-inspector-app.js`、`reference-workspace.js` 現有 model preview/add、`project-store.js` 的 model驗證及 ContextHistory；native `source-inspector-bridge.inc` 與 model transport。read-only locator 清單及差異 fixtures 可獨立；重建 UI/歷史只由一位整合者接入，以已合併PR73/74的新main接口為基底再開產品分支，不與 #46 同寫保存／歷史。

**驗收稿**：同值换 ParameterRef／固定材料版本仍列來源差異；改名／卡片位置／不相關定義不把所有模型誤判過期；刪除重建同號仍未知；選錯 kind／來源缺失／能力不足拒絕；真正候選零 live修改、取消零 model變更；切案／移除model／替換同IDrecord／遲到回覆不覆寫；確認原子更新全部 record 或建立完整新副本、dirty/history一筆、保存新上下文重開可再核對。既有內容一致是 content-equal/identity-unknown，不改成 green identity。

**減項／readiness**：唯讀在原「來源／影響」展開，不增一個檢查器；重建動作若採納，合併模型現有零散來源狀態與差異提示，不增加常駐說明。A 的規格 ready；B 等 Q32 和最小更新契約採納，這輪不開工。

<a id="wp46"></a>
## WP46 — #46 A/B：先完整快照保存讀回，再比較與採用

**現有與缺口**：模型庫是建立時的 input/source/result 記錄，undo/redo 是操作歷史，固定rule版本是定義身分；三者均不是獨立 scenario。現在 /9 manifest 嚴格欄位沒有 scenarios，不能把 A/B JSON 塞進舊清單讓舊 reader 丟掉。

**最小切片**：WP46-A「保存目前為 A → 明確以 A 為基準建立 B → 兩份固定來源閉包保存 → 新上下文讀回」先不允許採用。Q33 固定 scene／草稿／models／投影／圖源各歸哪一個 scenario、namespace及來源資產內容去重。WP46-B 才在隔離World修改 B並比較 typed定義／固定來源／接合；WP46-C 另做整体採用／取消／undo。幾何結果只有真 producer 支援才顯示，不拿畫面／外接盒代替同外形不同組法。

**依賴／落點／並行**：Q33 必先採納；typed diff 可共用 F1a，只用可證明對應、不要求 F1b 完成。`project-store.js`/`reference-workspace.js` 的完整保存及 ContextHistory、既有 model viewer/工作區、server-owned候選World。schema/closure正反例可與 #48/#49文件並行；持久化／World替換由同一整合owner排串行，沒有跨 scenario 單一 preview token 污染。

**驗收稿**：A/B同數字id與同名不錯配；B改參數／接合不改A；same-value/new-ref與same-outline/new-joint列差異；兩個未匹配物件不依名字硬配；真正 ZIP保存及freshcontext讀回scene／draft／models／資產與基準指紋一致；未知schema／缺閉包／超量拒絕且保留原案；採用遺失回應查receipt不重送、取消／晚回覆不部分替換，原A保持可恢復；快照並不攜帶舊undo堆疊。

**減項／readiness**：在既有model/來源比較區按需展開，合併重複「当前／快照」比較說明，不增常駐分支工具列。Q33未採納，A/B/C都只是proposal-ready；不等待全部 #44 或 #25。

<a id="wp48"></a>
## WP48 — #48 人工圖源證據：一個原頁區域連一個參數欄位

**現有與缺口**：[參考專案契約](../geometry-web/docs/REFERENCE-PROJECT.md)已有圖源原始bytes/hash、頁碼、crop/rotation/calibration、人工 records 與 /9輪廓核對收據；不是跨物件 EvidenceLink。來源記錄值不修改幾何。

**最小切片**：WP48-A人工選原頁範圍 → 明選一個 ParameterCard/fieldId → 保存一筆圖紙標示／現場量測 observation、原文字／原單位／人工核對狀態 → 從證據清單重新定位同頁範圍 → 完整專案保存新上下文讀回。首版不接材、模型、跨方案或自動數值採用；其物件沿革未知就「待重新關聯」，不因ID重用延續舊核對。WP48-B再做多份互相矛盾證據與圖源換版提示；採用尺寸沿既有 native preview/confirm另明選，不屬新增證據的副作用。

**依賴／落點／並行**：Q34、`reference-workspace.js`/`reference-ui.js` 原頁轉換、`project-store.js`新附件能力、`parameters.js`既有欄位檢查器、F1a typed locator。PDF/image座標差異與矩陣fixture可先寫規格；PR74 PDFsnap已合併；後續產品接線從最新來源碼進行單owner整合，不回復其snap變更，也不複製另一PDF app／閱讀器。目標沿革若沒有可證明資料就保留未關聯，不要求先寫全部F1b。

**驗收稿**：PDF以套用原頁旋轉後scale1座標、image以原像素，保存crop/rotation基準；zoom/viewport/390px變化仍同區；換同名異hash文件／重排頁／crop換版需複核；舊observation及衝突值保留；值精度不符D1仍可作原始觀察但不能套幾何；刪除重建field／切案／晚讀頁不串資料；未知附件／錯頁／壞rect／超容量在World替換前拒絕；ZIP只攜使用者明選圖源，沒有私人圖紙自動外傳。

**減項／readiness**：沿既有來源紀錄和參數「來源／影響」disclosure合併證據清單，不加一個常駐證據管理器。Q34未採納，新附件產品blocked；座標與負例規格ready。真iOS框選／鍵盤／OS檔案操作另列。

<a id="wp49"></a>
## WP49 — #49 有限 authoring 案例與隔離真核心

**現有與缺口**：repo有 assemblyfixtures、tests/build_assembly_example.py 和固定規則原生 read/preview；應用內尚無可攜 case library。原生 `assembly-preview` 目前不保證所有失敗都有 typed fieldPath/ref；`ASSEMBLY_INVALID`＋clause/message 與部分 timber issue 是既有回覆。不能反解析message就宣稱精確欄位诊斷已實作。

**最小切片**：WP49-A先固定3個非機密case定義：同角色不同member不混配；修改authoring draft／發布新version時只換一個joint、另一joint保持，不覆寫既有固定published rule；錯型來源依精確指定檢查拒絕。輸入包含固定rule/draft內容、typed closure、expected接受/拒絕、有限typed predicates；獨立process/World真載入并驗證，結果記casegeneration/input hash/validator fingerprint。WP49-B補至Q35首個可交付集合共6case，再做既有assemblyworkspace按需「案例」列表及完整專案保存讀回；A的3case不是宣稱六例全部完成。若現有diagnostic不足，API擴充須先把型別契約定清楚，負例不能任意error都算pass。

**依賴／落點／並行**：Q35、`assembly.inc`/`assembly_bridge.inc`、現有 batch preview、`tests/build_assembly_example.py`、`assembly-workspace.js`、`project-store.js`新case附件。shared候選/read方法可與 #46共規格，但自己的隔離World，不用live reset或消耗用戶唯一token。fixture和獨立expected可先並行；native diagnostic一個owner、保存一個owner、正式app接線一個owner。第一版不依賴 #25 任意拓樸／SGR產品。

**驗收稿**：accepted与指定rejected由真native決定；語法錯誤／missing能力／timeout／崩潰／transportblocked不能當幾何反例pass；原World/dump/history/dirty/token/feedback前後不變；同role不同member、改joint不影響另一joint有實際typed對照；來源/輸入/validator/斷言schema變則stale，unknownruntime為unchecked；latecase切案/取消不回填；保存重開可重現；在隔離build破壞member對應／略過指定拒絕，使行為斷言紅，編譯失敗不算mutation抓到。

**減項／readiness**：案例區合併原assembly內零散正反例說明，非新增永久試驗工作區；不執行上傳JS/Python/shell，不開公共分享。Q35未採納，產品blocked；typedcase格式／oracle稿ready。

<a id="wp57"></a>
## WP57 — #57 來源子規則整合總工作包

**現有與缺口**：D19/I25/R23手動單格子網格與D29/D30獨立來源／配置已採納；來源層可重用SubgridRule未採納，SSOT「全格批次、巢狀待定」限制仍有效。不得把GEO204/215舊數字當新功能完成。

**最小切片／依賴**：Q36/ WP58採納記錄 → WP59單格按需查詢／typed引用／全依賴原子交易 → WP60正式保存與草稿 → WP61來源編輯／配置跨面 → WP62同一app真流程與SR01–24。三層接口先固定，核心與保存共用同一Worldsource owner；功能不是只畫小格。

**落點／並行／验收**：原 `grid_systems.inc`、`grid_bindings.inc`、`grid_lattice.inc`、`subgrids.inc`、既有web工作區／專案；獨立proposal/fixture/容量壓測規格可並行，產品等採納。完整flow含無房間來源→U3/V2→第一面→第二面→引用→pitch更新取消/確認→保存freshcontext→undo/redo；step須真正UI，不先API做好再截圖。大signedcell／L形孔／zero-visible／one-surface-invalid rollback都在整合gate。

**readiness**：總路線與拆包ready，產品blocked；原issues保持open/Refs，不因文檔PR完成將#57關閉。SR24真iOS與Windows限制單獨保留，不拖住規格工作。

<a id="wp58"></a>
## WP58 — #58 逐條語意差異與共用契約

**最小交付**：Q36完整proposal列來源所有權／一層rule family、stablekey生命週期、selector/整除、manual衝突、RuleLineRef、guide/at-line差異、全依賴preview/confirm、exact/sample資源、完整保存／新能力相容；提供獨立正反例和接口候選。正式公理條號與下一檔案version在整合採納時協調，本文不占用。

**依賴／落點**：[公理層](../公理層.md) D6a/D9/D19/D29、I13/I23/I25/I37/R6/R32和本包Q36；未採納只改proposal文件／工單。若使用者採納逐條diff，另一產品PR才更新SSOT、白話、唯一正典與見證，再核對model parser/能力/hash；不能只改AXIOM_SHA256字串。

**驗收／並行／ready**：source無boundary合法规则、manual正面積守門原義不變、已有引用的rule更新策略選項與I23手動子格分開、兩來源samekey不串、跨undo分支key政策寫清；600×400U3/V2、917/7、600/7、signed>2^53、holes/zero-visible都有獨立預期。proposal/向量ready，正式契約需Q36採納；其schema与API不能由#59–61各自補義。

<a id="wp59"></a>
## WP59 — #59 C 按需細分、typed引用及依賴交易

**最小切片**：WP59-A來源保存一條合法已採納rule並讀取一個真signedcell，不逐格加World.grids；WP59-B配置/面查询裁C∩F、typedRuleLineRef解析、guide取座標與直接at-line完整footprint；WP59-C source/rule更新檢查所有binding、面、manual子格、guide和timber，任一違規整筆拒絕。有限集合只列真已保存下游，不能展開無限所有cell。

**依賴／落點／並行**：#58/Q36採納才寫產品；`current_geometry.c`的World與dispatch、`grid_systems.inc`/`grid_bindings.inc`/`grid_lattice.inc`/`subgrid_world.inc`/`subgrid_rebind.inc`、typedreference資料與web bridge。C主檔CRLF不normalize；與#60共用一位World/sceneserializerowner，helper純query可分責，產品commands/保存不能競寫。#62oracle不與implementation共用計算公式。

**验收稿**：U200/400、V200及pitch917/U7內距131；拒600/7、0/66/1×1、缺軸/stagger/legacyfinite；2^53以上cell以decimalstring/relativeanchor无Number溢位；manual/source雙向衝突；guide外越與at-linefootprint/真实端面分開；第二面下游非法時World/dump/geometry/history不變，readonly query/validate保留原pending，explicit impact preview依既有交易以新候選／invalid token替換舊preview；capacityerror不是sourceinvalid。ASan/UBSan與略過clipping/等分/第二面依赖mutants須由行為断言抓到。

**readiness**：現在只能準備fixture／oracle規格；產品blocked by #58，不能從讀到issue diff視作採納。

<a id="wp60"></a>
## WP60 — #60 完整来源／草稿保存與相容

**最小切片**：WP60-A未套用来源+rule、高水位/key、兩binding／面、typedlineRef完整dump/正式.gcanvas保存→freshcontext原生重建；WP60-B未提交／未填／非法rawsource/rule草稿獨立附件保存恢復，不改liveWorld；WP60-C未知format/capability/closure、舊版本介面省略rules、遺失載入回覆與undo/redo負例。worldsource与展示/sample線段不能有兩份可獨立改的真相。

**依賴／落點／並行**：Q36原生來源保存及Q31草稿契約，#59固定typedinterfaces；`project-store.js`、`reference-workspace.js`、gridworkspace flush hooks、native dump/load、model-base/model驗證與能力預驗。現在/1–/9可讀，/8生成與/9來源核對不重用；formal新format/capability由單一保存owner在各功能採納後協調，不能四個工作包各自搶/10。schema負例矩陣和旧reader refusal fixture規格可先並行；World/scene寫入與59串行整合。

**验收稿**：未套用來源不丟、decimalcell不取Number、samekey不同system不串；rawinvalid draft重開仍raw不自動确认；刪cap/偽舊version/未知欄/壞source/hash/超量都在World替換前拒絕且原檔可保留；新context恢復完整source+draft+assets，不保存或恢復舊undo/redo stacks；本頁native/metadata交易history原子undo/redo，成功開檔按既有ContextHistory記一步、失敗保持原狀；reopen後新producer真能力支持，不只JSON自洽；模型adapter unsupported保持明示，不换hash假支援。

**readiness**：proposal/相容table ready；產品blocked by58/59/Q31，草稿schema及正式version未採納。

<a id="wp61"></a>
## WP61 — #61 正式来源工作區與手機流程

**最小切片**：WP61-A空白sourceworkspace建立一條rule→預覽／確認，不需房間；WP61-B從真邊界vertex／signedcell配置到兩面，查／選真子線並走既有guide或明寫角色角材流程；WP61-C改sourcepitch看兩面及有限下游差異、取消／確認、保存重開與草稿。不是把existingmanualsubgrid換名字，不造平行manager。

**依賴／落點／並行**：#58採納、#59真core与#60草稿／完整保存；`grid-system-workspace.js`、`grid-inspector.js`、`app.js`既有singleowner整合、`WorkspaceShell`、nativequery/hittest。流程文案、typedDOM_contract与keyboard/触控规格可独立并行；不把mock/shots當成已接core。PR73/74已合併，以其新接口再核對執行當下open PR並指定app接線owner。

**验收稿**：错误与未填保留草稿；两面共享一source，pitch改完整重算；真cell命中不用sample序号、hugeindex显示保持字串；遲到query／取消／换source／切案无oldstate回填；desktop與390px真实关键步骤所有DOM能操作/焦點正確，控件触控面积≥44px，無水平overflow；實體iOSkeyboard/OSfilechooser/download另SR24未驗。

**减项／readiness**：来源細分編輯收在既有sourceworkspace；合併現有分散「主格／手動子格／來源規則」說明為一段範圍摘要，舊manual入口必要功能仍保留，不加永久一排buttons／說明≤3。未確認具體UI減項時不標產品ready。目前流程spec ready，產品blocked by58–60。

<a id="wp62"></a>
## WP62 — #62 SR01–24 獨立驗收與同head交付

**最小切片**：WP62-A在採納前就把[原SR01–24](https://github.com/ZhiQiYang/geometry-axiom/issues/62)逐行轉成fixture輸入、獨立expected、test層／檔候選、artifact及人工欄；不執行不存在的產品commands。WP62-B接同一正式app+真core，完整flow與新保存重開；WP62-C同head完整回歸、sanitizer、mutation/還原，以及經採納唯一正典驗證。所有新SR列目前未驗，不引用GEO204/215舊pass替代。

**分層索引**：SR01–08 source/整除/軸/identity/signedindex；SR09–13clipping/zero-visible/有界query/manual衝突；SR14–18生命週期/crossbinding/全筆rollback/guidevs材；SR19–22draft/完整保存/capability/receipt/token/undo/latecontext；SR23desktop/390px真流程；SR24真iOS/OS。SR11/12必有工作量有界断言，SR18先建合法支撐再驗角色拒絕，避免提早不相關錯誤。

**依賴／落點／並行**：#58–61、`tests/test_subgrid_contract.py`/`test_grid_system_contract.py`等既有層、新增test註冊`tests/run_all.py`、正式`geometry-web/cdp_test.js`載入新的workflow；若動space另跑`space_model_test.js`。檔名／新用例是候選，要產品owner先定interfaces；獨立expected與mutation選擇可先並行，但最終基底/binaries/runtime/goldens範圍不可混搭。

**验收與ready**：可攜非機密.gcanvas＋來源/草稿与trueUI截图/console、命令exit及sameheadhash；fullnative與unfilteredCDP完成標記/golden，局部不稱完整；環境blocked/skip/timeout分開、不改expected掩蓋；略過整除、丟rules、去systemId、錯cellclipping、漏第二面或過期gate應使行為assertred，編譯fail不算。公理採納後sync/check/reader tests三道與見證一起跑。A驗收準備ready；B/C產品驗收blocked by58–61；SR24維持人工未驗，總工單不自動關閉。

<a id="wp77"></a>
## WP77 — #77 同一PDF連續建立獨立房間

**授權與現況**：使用者20:19明確要求加入排程；本輪仍只準備規格／依賴／工單。已查全部open/closed工單，無同範圍既有單，建立[#77](https://github.com/ZhiQiYang/geometry-axiom/issues/77)。同PDFsourceId與bytes/hashdedup不是共享校準：目前newPage是calibration:null並重設x/y/scale。D3 Boundary單外環＋孔且無parent；D4 PlacementSurface引用boundary、自有worldframe；D5 Space六方向面成員組、D22 CompositeSpace殼均不是來源頁多房間樹。

**最小可行模型／決策**：Q37建議SourcePlane/RoomCollection為專案來源附件，一個sourceHash/page/原座標/calibration/對位basis；RoomRecord只有roomId/name/typed boundaryRef（可選placementRef），不另存polygon/頂點/frame/volume。父子表示來源/工作區歸屬，不改native幾何所有權。新房間在共同來源工作UV座標描繪，native D3保存唯一輪廓；placement若需要明選現有D4建構，不隱含建Space。更新共享校準只改描圖基準，新描房間用新basis，既有geometry不自動移動而標需複核。

**最小切片**：MR-A先固定Q37的來源平面/room metadata、原生引用及沿革、共享basis變更/刪除、schema/capability與舊獨立ReferencePage兼容。MR-B校準一次→描A真nativepreview/confirm→回同來源工作區→「新增房間」→描B真preview/confirm，A不被replace；編輯A必明選A再走舊外環replace。MR-C列表/命名/獨立編輯/來源總覽→完整ZIP保存freshcontext重開。新rooms引用真实native IDs，surface合體要newid.surfaces，不JSmax+1。

**依賴／程式落點／並行**：Q37/sharedsourceplan附件、project-store/ContextHistory、reference-workspace/reference-ui與既有boundary/outlinepreview、project資料sourcebytespool。Q34共享原頁座標術語可用，EvidenceLink產品不是前置；房間幾何建立不需SGR/A/B功能。boundaryD3與placementD4不共享數字驗證器，刪重建同號未知需重新關聯，不靠roomUUID證明nativeincarnation。schema/合成雙房PDFfixture與操作稿可並行；同app/reference/store接線一owner，保留已合併snap/undoRedo，未開新產品分支競寫。

**自動候選接續**：#54（A）先修現行單房間失敗、#87（B）同頁有界多候選逐一核對，再接本包（C）明選新增房間。MR-B的人工連續描繪規格不要求先完成B；自動C須B穩定並採納Q37，候選不批量變成geometry。REAL-PDF-01/CaseA本地0f3c1a6匯入/323.5cm校準成功、單房辨識edge-open/tooManySegments失敗已驗，geometry不變/0 exceptions；newhead snap/人工分區/整屋/新main重跑未驗，REAL-PDF-02/CaseB各階段未驗。合成双房fixture不能替代實圖，也不抹掉歷史失敗。

**驗收稿**：同一自製雙房PDF一次calibration，連續新建兩个nativeboundary，A的dump/来源/身份不變；有孔的A不是多間room；A/B独立name/roomUUID/nativeRef/edit；基準变/同名异hash/换page旧review失效；cancel/invalid/latepage/切案/delete-recreate/unknowncap/badclosure原project/history完整；confirmpaint/busy保持、一笔native＋metadataundo，无半建room孤兒；真ZIP重开原PDFbytes/共用basis/两个native轮廓与typedRef一致；旧无collection/page资料原義正常，strict旧reader拒新capability。.scene不能宣稱攜共享來源。desktop/390px完成两间与总览，真iOSkeyboard/OSchooser/download单列未驗。

**UI減項／readiness**：沿既有來源工作區將僅「替換目前外環」的工作模式提示整合為「新增房間／編輯所選房間」明選意圖，原replace功能保留，不另造PDFapp/永久父子管理器，常駐說明≤3。若無具體減項確認，UI仍待GEO-219門檻。規格ready；MR產品需Q37/附件採納，sharedcalibration/newparent未當已採納。

## 交付與稽核

工作包固定後，各產品 slice 必須另立 isolated branch/owner，先核對最新 main/進行中 PR；建立完整契約與可重現驗收，再寫產品碼。保存未知能力應在替換 World 前拒絕；.scene 不能冒充完整 .gcanvas；現在正式可讀 /1–/9，新增附件不能佔用既有 /8（生成）或 /9（輪廓收據）。不用私人圖紙、付費、變更安全、重置用戶服務或自動合併。

本輪驗證只包括文件路徑／錨點／issue 連結、差異範圍、規格與採納狀態一致性；沒有宣稱產品測試完成。
