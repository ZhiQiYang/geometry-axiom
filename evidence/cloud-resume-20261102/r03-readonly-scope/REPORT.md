# R03 下角材模式：唯讀需求、owner 與前置盤點

本輪只讀 metadata／固定單檔及本地既有 Git blob，未實作、未改 source／branch／SSOT、未開 PR／留言、未跑測試。所有新執行與效能 UNRUN。盤點一次完成，沒有輪詢。固定比較 main `e02057b4c725d6f03ae52c3bc30776bf9442b0cf`，不是將歷史 native／oracle 結果移標此來源。

R03 真正工單是 [#205](https://github.com/ZhiQiYang/geometry-axiom/issues/205)，不是另猜號碼；#221 是已合併提案，#251／#307／#327 是 oracle／相關整合歷史，#213 是另案 SketchUp。需求帳 [R03 第63行](https://github.com/ZhiQiYang/geometry-axiom/blob/78dfb1129ce72719fbdb71ce5e71800eefcb3a68/%E9%9C%80%E6%B1%82%E5%B8%B3.md#L63) 明列產品 L1、oracle L3，不能由幾何參考推成 App 已交付。11/2 的 [派工第160行](https://github.com/ZhiQiYang/geometry-axiom/blob/78dfb1129ce72719fbdb71ce5e71800eefcb3a68/%E9%9C%80%E6%B1%82%E5%B8%B3.md#L160) 指派雲端 Codex、排 R02 後；[handoff 第3行](https://github.com/ZhiQiYang/geometry-axiom/blob/0919c4c6e00c496d0941b12047b281ec6c90348a/handoff/NEXT.md#L3) 同樣把 R03 放在既有鏈、UI15、小件／canvas 後。它們是排程來源，不是本輪新建產品 owner。

## Owner 與來源界線

一次讀取 codex **148**、grok **11**、feat **13** 個 remote ref metadata，以及 **27** 張 open PR（無下一頁）；沒有 checkout／fetch。未見 R03 專用產品實作 branch／open PR。`feat/framing-oracle-20261015`=`3d858c31e84e025d34c62b0c6be6a9b73ce55a8d`、`feat/framing-core-probe-20261017`=`bc3fb622131a55c6f3e5135caab6d4c39e4b2b4c` 是已存在參考／探針，不能據名稱認定現在有產品 writer。相關 PR API assignees 均空，API author 只是帳號，不據此推 agent owner；未推送工作及其他 ref prefix 真正未知。完整查過清單在 OWNER_AND_DEPENDENCIES.json。

最新 open #355 是 `b5a61bbc0cb33a1f188112cc5c7982bffbec93ff`，draft；UI15 仍標 UNRUN／未達合併條件。以下只核 source 和 author 所報支持範圍，未重審其 browser 收據。#333 API metadata 為已 merged（merge `425c092eaf16f90256d76433243baebde45163ac`），舊 body「沒有合併」是歷史；本輪 main 的 FIELD-RULES blob `5a5e7e4c712d1628a56d30528bb75553d4c41a94` 等於 #333 final 檔 blob，38 條 `>` 引文皆可在 fixed main 決策佇列逐字找到。

## 已讀原文與不能另造的規則

先讀 main 的決策佇列 10/12～15、10/22、10/23、10/24，以及 [FIELD-RULES](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-templates/woodworking/FIELD-RULES.md#L1)；後者自己明寫「本頁不是 `公理層.md`」。FIELD-RULES 源引文截止舊 main，10/23／24 另從決策佇列讀，不能只靠該頁漏掉後續採納。

- [需求原話](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L238)：「我跟一個木工師傅 討論某個圖面或者是指定封閉面 上  我要 "下角材" 怎麼下 這個介面我可以方便的操作去下角材示意給他看」。同節「通過審查就直接實作」沿用，沒有新增重問使用者流程。
- [端面／RC 原話](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L198)：「因為角材的端面 頂到角材材能固定 不能直接頂到RC」。10/22 [補充](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L762)：「主要是你這個角材端面只能固定在角材上 你是不是聽不懂?」。不另造懸空 mm 上限，不把斜釘／側釘工法加成 App 規則。
- [10/15](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L436)：「對,只在對牆、不置中」。[主支](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L217)：「??? 主支為什麼要斷開 ?」「不能斷開阿」。如何套用仍沿已採條文及 W 策略，不能以角色字串免核心檢查。
- [10/22 原位偏好](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L715)：「用這個」。它回應 B1；先原縫、原位不成立才由近到遠，完整建構／完整檢查。[累積退距決策](https://github.com/ZhiQiYang/geometry-axiom/issues/205#issuecomment-6336484777) 已採不另設固定總量上限，不能把 oracle README 的舊「待決」重新變成問題。
- [10/23](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L811)：「同意 #318 照閱讀 A」。[10/24](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E6%B1%BA%E7%AD%96%E4%BD%87%E5%88%97.md#L850)：「量還沒貼料的那段 (建議)」；其後條文補句與 #335 放置路徑分案界線仍在。main [I53](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E5%85%AC%E7%90%86%E5%B1%A4.md#L1667)、[I55/I56](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E5%85%AC%E7%90%86%E5%B1%A4.md#L1683)、[R41](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E5%85%AC%E7%90%86%E5%B1%A4.md#L2351)、[R43](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E5%85%AC%E7%90%86%E5%B1%A4.md#L2393)、[R44/R45](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/%E5%85%AC%E7%90%86%E5%B1%A4.md#L2410) 已另讀。
- #205 原始 body 仍帶已撤回 450 說法；不得採用。間距／短料／偏好引用已決現場來源，不發明新門檻。

[FT-S1 採 A](https://github.com/ZhiQiYang/geometry-axiom/issues/205#issuecomment-6436162610) 已決：保存可重用生成意圖；確認後是一般 D7／D6／D42 正式定義，無模板排他 owner；再次生成明選，一般物件仍依自身來源重算。這不代表所有呈閱中的公理差異已寫入；見 QUESTIONS.md。不能沿 PROPOSAL 舊第176行把配方 ownership 又稱未決。

## PF2–6 接點矩陣

共用現有 native 入口：`panel-fill-read`、`panel-fill-preview <JSON>`、`panel-fill-confirm/cancel <token>`，schema `panel-fill-transaction/1`，expectedRevision＋operations；[bridge dispatch](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-web/web_bridge.c#L1061)，HTTP `POST /panel-fill/preview` 及 generic `/api` 路由在 [serve.py](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-web/serve.py#L650)。這些不是 FT generator API。

| PF | main native／API 實有 | main UI／保存重開 | #355 UI-1 實有及仍無 |
|---|---|---|---|
| PF-2 鋪滿 | `put/delete-panel-fill`；真裁片／whole/cut／raw seamLines；共用 panel_layout_math；[PF2:9/37/52](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/panel-fill/PF2-NATIVE.md#L9)。`seamLines` 本身不是有效縫或承接。 | 原生 scene 只存定義／來源並重推 [PF2:66](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/panel-fill/PF2-NATIVE.md#L66)；main App 無此入口，project-store reader 不接受 panel-fill capability（[267](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-web/project-store.js#L267)），不能把 native load 當完整 .gcanvas 交付。 | 真面→屬性→面設定→完成面與鋪排，建立／編輯／preview／confirm/cancel；[app:31/189](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/app.js#L31)、[adapter:214](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/panel-fill-adapter.js#L214)。正式 reader 新增 geometry-canvas/19＋panel-fill/1，[store:13](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/project-store.js#L13)。 |
| PF-3 承接 | `effectiveSeams/nonSeams/support`；真 D4 宿主 D7 足跡、兩側實寬與 D31 X ParameterRef；不足仍能保存。[PF3:12–45](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/panel-fill/PF3-NATIVE.md#L12)。 | 每次讀取、preview、undo/reopen 重推；不存顏色／段 cache；main 無可見入口。 | [workspace:170/186](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/panel-fill-workspace.js#L170)呈現 native 每一子段及精確值，紅色結果不是拒絕合法試排的理由。PR UI11 報真下載＋fresh BrowserContext 重開，共用同一原生程序；本輪未再驗，不稱 fresh native／OS picker。 |
| PF-4 from-fill 網格 | D10／R44 規格已列；PF3 native scope 明寫未提供 PF4，既有一般 grid 不是 from-fill 交付證明。[PF3:44](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/panel-fill/PF3-NATIVE.md#L44) | 未見本片 native/API 操作、可見入口或完整 save/reopen 關閉證據。 | UI 明寫尚未提供 PF4，supportedActions 沒有對齊／網格建立；未增加其保存契約。 |
| PF-5 空間完成面 | 有 D41 明設 frame(origin/U/V/N)、structureSide、typed RC 障礙，以及 PF-H 真 D4 衍生宿主／h、角材層 `(t,t+h)` 原語；[PFH:8/24/40](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/panel-fill/PFH-NATIVE.md#L8)。這些是實有接點，不能說全部不存在。 | 它們只存 D41／fill／host 定義並重建；完整空間工作流仍未交付。bridge layerJudgement 明示 pending，[main bridge:15](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-web/panel_fill_bridge.inc#L15)。 | 可明設現有 frame／host，沒有補 PF5 空間與分層流程；不能把 PF-H 或手設frame改標 PF5完成。 |
| PF-6 R45 建議 | 有一般 D7 及 R45 SSOT，未有本片 R45 外層候選 builder API。native operation whitelist [finish.c:218](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-templates/woodworking/native/finish.c#L218)只接 finish/fill/host 及受限既有工程變更，不是任意 D7／骨架生成。 | 一般 D7 可保存並非「由板縫建議→確認→同筆建立」已可用；無 PF6 UI/save/reopen 閉環。 | 明示沒有 PF6 可執行動作。必須先提供只修改外層候選、不自行 confirm 的 builder；不得用逐行提交或 history 包裝充當原子生成。 |

PF-H 是 PF2→PF3 的重要真接點，不是可跳過 PF4/5/6 的替代物。[原生見證前置](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-core/framing-template/PROPOSAL.md#L157)要求 PF2–6全部落地後，先證真 D42→D4 衍生宿主→柱邊→逐跨副支，再開始模板實作。

main `panel-fill-read` 明示 `complete:false`、supportedRecords只有finish/fill/derived-placement（[bridge:122](https://github.com/ZhiQiYang/geometry-axiom/blob/e02057b4c725d6f03ae52c3bc30776bf9442b0cf/geometry-web/panel_fill_bridge.inc#L122)）。#355 的 [uiContract](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/panel_fill_bridge.inc#L124)只准 `read / edit-definitions / read-layout / read-support`；`completeForScope` 是這個有限 view 的完整性，不能升格整套 PF 或 R03完整。UI [第203行](https://github.com/ZhiQiYang/geometry-axiom/blob/b5a61bbc0cb33a1f188112cc5c7982bffbec93ff/geometry-web/panel-fill-workspace.js#L203)逐字明示 PF6/4/5未提供與全域complete:false。提案中的 `/framing-template/capabilities`、`preview`、confirm/cancel 仍是 [待實作設計](https://github.com/ZhiQiYang/geometry-axiom/issues/205#issuecomment-6435623938)，本輪未在讀過的main entrypoints找到產品接線，不登錄假capability。

## #343→#346→#347／R04 的實際界線

| PR | 本輪 metadata 固定 head | 對 R03 的意義 |
|---|---|---|
| #343 | `a934a554ae58f16f124f1b264523947f170b3f0b` | unique-ID contact index／stable排序；原branch仍draft。來源祖先已納入其他main鏈不等於其正式缺gate與效能已關閉，不能當512或完整骨架證明。 |
| #346 | `eaf15e239324a6464a04740647afccce3a3c17c7` | cut-list單一ID池，仍draft；不是PF建議或UI功能。 |
| #347 | `8bb0359331365c6f3a96872620427cf7847fcb50` | PF2空列舉優化，current base #346；body明示正式S324來自舊parent，B1/B2／最終整合未關閉。不能把S324局部數字當#355 UI15。 |
| R04／#348 | `86c8f0bbe68275e2948d3b1959207aba4225e0c7` | 64→512仍draft；R03 F1完整房間108–116支需要它。main目前64不能以丟料、只建一半或提高時限掩蓋，容量不足仍CAPACITY。 |
| #355 UI15 | `b5a61bbc0cb33a1f188112cc5c7982bffbec93ff` | UI1局部可用範圍與歷史實跑保留；等343→346→347同源整合，且PF6→PF4→PF5仍需另交。 |

上述 bodies 只是來源自述，本輪未重跑／重新核收各PR；實際 API base/head/draft/assignees 全保於 OWNER_AND_DEPENDENCIES.json。

## 前置未閉時可準備的保守 slice／測試設計

1. **需求與接口追溯表**：維持本報告的read-only capability矩陣、來源型別／版本、原生command與保存格式對應，標實有／設計／缺口；不新增產品registry或按鈕，不重做R02 UI1。
2. **前置能力反例設計**：完整PF前置缺一、未知schema／policy、view incomplete、API沒有該supportedAction時不得產生可確認R03候選；scope完整與complete:false分開驗。只出測試計畫，不以mock成功宣稱產品能力。
3. **沿原fixture的數值／交易見證清單**：F1容量、F5真衍生宿主及逐跨副支、PF23/24 R43子段、閱讀A RC連續裸露段、反向／結構側／真引用鍵；引用原答案與拒絕原因，不從候選輸出生oracle。成功後才設計撤接線0/1/0；compile錯／timeout不當功能紅。
4. **FT-S1-A保存測試稿**：配方不擁有生成物、刪配方不刪料、一般定義仍依來源重算、再生成明選；`.scene`只存正式定義；`.gcanvas`配方沿已採A契約，相關呈閱中的SSOT差異仍需正式寫入、reader仍待實作。未知schema拒整案、版本不可用只讀等按採納稿界線，不提前註冊新格式。
5. **後續真App驗收設計**：PF2–6與原生見證關閉後，由既有面內入口走全流程；最後一支非法整筆零寫入，取消／過期／歷史往返／重建同id／掉回覆有界守門；實際下載→fresh browser與native重開核source/dump/引用及逐片/逐支，不以console或API旁路取代可見旅程。保原gates與時限，沒有新數值門檻。

本輪真正未知與未批准的語意證據缺口列 QUESTIONS.md，不向使用者索取已決答案。來源完整SHA／檔案hash／API快照在 SOURCE_MANIFEST.json。沒有任何新產品或執行通過聲明。
