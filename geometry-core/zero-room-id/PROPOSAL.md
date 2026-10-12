# K2b 契約提案：#87 零房起步與跨次保存候選、非空專案匯入的 ID 碰撞

狀態：**r4.1，暫定（依 2026-10-09 授權 L）**。r4 已通過第 3 輪核對的 10 項，另補 3 處小補成 r4.1（見下「r4.1 補正」）。可直接實作的契約；opus 對抗審查兩輪（第 1 輪 S1–S10 已入 r2；第 2 輪須先改、無阻擋，F1–F12 已入 r3），第 3 輪 sonnet fresh-context 核對（F1、F3–F10、F12 通過，F6 附 2 條用詞附註；F2、F11 部分通過；另有新缺口 N1–N3；共 10 項處置已入 r4，原文見 `review-round3-findings.md`）。不是產品完成聲明。衝突時以較新者為準（r4.1 > r4 > r3 > r2）。

## r4 對照表（2026-10-10，依第 3 輪核對 `review-round3-findings.md` 的 10 項；全部暫定，依 2026-10-09 授權 L）

「接手狀態」＝修訂 agent 被限額中斷後，接手時三份檔的實況；「本輪補完」＝接手的 agent 補上。

| 核對項 | r3 問題 | r4 處置 | 改動位置 | 接手狀態 |
|---|---|---|---|---|
| 1 F2 缺1 | §3 稱「其餘檔案不重疊」，但 `tests/run_all.py` 兩個 PR 都登錄 | 改為兩 PR 在 `project-store.js`、`reference-workspace.js`、`tests/run_all.py` 三個檔重疊，由同一整合 owner 處理、#87 先合 | §3 第 2 點 | 未動 → 本輪補完 |
| 2 F2 缺2 | §1.7 稱 `app.js:555` 已涵蓋 line；實際 :555 的 regex 只有 `assembly-confirm`、`section-profile-confirm` 兩項 | 更正：#87 的房間 `line confirm` 靠 roomLease 走 :532，不靠 :555；匯入須把 `definition-import-confirm` 加進含 :555 在內的七處 | §1.7 `app.js` 列（前一輪已完成）；§3 第 2 點 app.js 條（殘句「既有 `line` 已涵蓋」本輪更正） | 半套 → 本輪補完 |
| 3 F2 缺3 | 「五處」與 §2.3 實列七處不一致 | 統一為七處並逐一列出：`app.js` :546、:532、:555、:608；`reference-workspace.js` :37、:418–420；`project-store.js` :836/:856 | §1.7 `app.js` 列（前一輪已完成）；§2.3 首項、§2.7 `app.js` 列補「共七處」（本輪） | 半套 → 本輪補完 |
| 4 F11 缺1 | §2.2(b)3 只寫 rename 新名「必須未被使用」，沒有避開本次閉包全部與其他新名稱（只在 AXIOM-DIFF I⟨K2b-4⟩(d) 有） | 規則 3 補齊四項條件，與 I⟨K2b-4⟩(d) 同文 | §2.2(b) 規則 3 | 未動 → 本輪補完 |
| 5 F11 缺2 | IM16 夾具的目標沒有「柱寬2」，改名不構成撞名、「兩個撞名」不成立；兩個 rename 到同一新名時契約沒說被接受、拒絕或忽略 | 夾具改成真撞名（目標預先有「柱寬」與「柱寬2」）；明定本次任兩個 rename 目標同名 → 整批拒絕，碼 `IMPORT_RENAME_COLLISION`，不忽略、不取先者；IM16 拆為 (a) 單一撞名改到目標已有名、(b) 兩個 rename 到同一新名，另保留通過案例 (c) 與閉包撞名案例 (d)；IM05 的撞名結果同步改用此碼 | §2.2(b) 規則 3、IM05、IM16；AXIOM-DIFF I⟨K2b-4⟩(d) | 未動 → 本輪補完 |
| 6 N1 | roomsPin 建快取沒有上限、分批與單筆失敗行為，可能產生永遠不能接受的 session；舊引用 rcw:440–441 應為 rcw:77 | 建快取每批 64 房、批間讓出事件圈；任一房讀取失敗 → 快取「不可用」，session 只可檢視、捨棄、重新分析，不得接受、不得暫停、不寫草稿並明示提示；群組內草稿的新 D3 nativePin 引用改為 rcw:77；新增 PC21 | §1.2(b) 三段、§1.3 兩列、PC06、PC21、§1.7 `room-collection-workspace.js` 列（本輪補一句） | 前一輪已完成；本輪逐處核對，補 D 條目 |
| 7 N2 | 沒有草稿、群組內不寫時，「草稿等於剛寫入的值」的比對對象未定；沒有 PC 驗接受後 session 續用與其餘列 pending | 補「群組內沒有寫草稿者須仍無草稿」；新增 PC20（甲乙丙三案） | §1.1 第 3 點、§1.3 兩列、PC20（前一輪已完成）；AXIOM-DIFF R⟨K2b-2⟩（本輪） | 半套（PROPOSAL 完成、AXIOM-DIFF 未動）→ 本輪補完 |
| 8 N3 | §2.3「依上一列記歷史」的「上一列」現指取消／失敗那一列 | 改用項名「一筆 native 候選交易」指涉；§2.7 `project-ui.js` 列同類的「與上一列同一擁有者」一併改指 `app.js` 列 | §2.3 回覆未知項、§2.7 `project-ui.js` 列 | 未動 → 本輪補完 |
| 9 F6 附註 a | AXIOM-DIFF 條文仍有「執行期世代」「執行期修訂號」，無 D 編號 | 改為「本層不以任何執行期狀態判定新鮮度」，條文不再出現實作名詞 | AXIOM-DIFF D⟨K2b-3⟩、I⟨K2b-3⟩、§6 自查表 | 未動 → 本輪補完 |
| 10 F6 附註 b | R⟨K2b-2⟩ 的「過期」與 R⟨K2b-1⟩ 草稿過期同詞不同物 | 加限定語「候選工作過期」，並寫明與草稿過期不同物 | AXIOM-DIFF R⟨K2b-2⟩ | 未動 → 本輪補完 |

本輪自行補充（核對清單之外）：AXIOM-DIFF I⟨K2b-4⟩(d) 補「相撞則整個匯入拒絕」一句（IM16 的條文依據）；IM16 加 (c)(d) 兩案；§1.7 `room-collection-workspace.js` 列補快取一詞；§2.7 `project-ui.js` 列的「上一列」；§1.7 測試列的「上列四個既有檔」改為逐檔列名；§4.2 新增 #13（`names` 對目標無同名者的行為尚未定）。

## r4.1 補正（2026-10-10，r4 通過 10 項核對後的 3 處小補；全部暫定，依 2026-10-09 授權 L）

| 項 | r4 的問題 | r4.1 處置 | 改動位置 |
|---|---|---|---|
| 1 §4.2 #13 | `names` 鍵指到目標無同名、閉包外或根本不存在的規格時，行為留作「尚未裁決」 | 已裁決（decisions R4-11）：整批拒絕，碼 `IMPORT_RENAME_UNNEEDED`；呈現同 `IMPORT_RENAME_COLLISION`（預覽 `valid:false`、不發令牌、碼放進 `conflicts`、零變化）；不忽略該鍵、不視為預先改名。#13 改為已裁決；新增 IM16e（目標無同名）、IM16f（閉包外或不存在） | PROPOSAL §2.2(b) 規則 3 第 (v) 項、§2.6 IM16e／IM16f、§4.2 #13；AXIOM-DIFF I⟨K2b-4⟩(d)、§6 自查表；decisions R4-11 |
| 2 project-ui.js 歸屬 | §2.7 把 `project-ui.js` 寫成檔案選單入口；它其實是專案資訊面板（`projectInfoButton` 等）。檔案選單 `btnOpenProject` 的標記在 `geometry-web/index.html:65`，點擊接線在 `reference-workspace.js:1873–1887`（@ a7bff8f） | §2.7 以 `index.html` 列取代 `project-ui.js` 列，註明 #87 不碰 `index.html`；§3 重疊結論不變（`index.html` 只由匯入 PR 改）。§1.7 檔案表本無 `project-ui.js` 列，不需改 | §2.7 檔案表 |
| 3 app.js:549–554 | §1.7 `app.js` 列只說 `:555` 不涵蓋 `line confirm`，沒說明 `:549–554` 是什麼，讀者可能誤以為 #87 的房間 token 要登記到那裡 | 補一句：`:549–554` 是網格草稿專用的確認租約，`featureConfirmations` 只由 `grid-system-workspace.js:907` 經 `prepareFeatureConfirmation` 登記；#87 的房間 token 來自 `line preview` 的 `++g_preview_serial`，經 roomLease 走 `:532`，不會登記進去 | §1.7 `app.js` 列 |

r4.1 取代 r4 的下列殘句：r4 對照表「本輪自行補充」所稱 §4.2 #13「尚未裁決」；r4 對照表第 8 項與 decisions R4-8 所稱 §2.7 的 `project-ui.js` 列（該列已由 `index.html` 列取代）。

## r3 對照表（2026-10-10，依第 2 輪審查 F1–F12；全部暫定，依 2026-10-09 授權 L）

| 審查項 | r2 問題 | r3 處置 | 改動位置 |
|---|---|---|---|
| F1 | 接受時草稿與新 D3、房間同一筆交易，「唯一變更」永不成立；與 R⟨K2b-2⟩、rcw:432–447 衝突 | S5 只適用暫停、保存前同步、捨棄。接受改以 R⟨K2b-2⟩ 或現行回執證明，並要求草稿等於同一群組剛寫入的值 | §1.1 第 3 點、§1.3、R⟨K2b-2⟩ |
| F2 | `/api` 白名單漏列 requestId、nativePending、確認租約、可編輯性、定義變更事件 | §2.3、§2.7 補列各處。`app.js` 改為必改；兩 PR 重疊照實寫 | §1.7、§2.3、§2.7、§3 |
| F3 | I⟨K2b-5⟩ 把回覆未知寫成不改目標 World，與 IM17 矛盾 | 改為回覆未知時不重送、不推定結果，以回執為準 | I⟨K2b-5⟩、§2.3、IM17 |
| F4 | `save` 在 :1516 同步後，:1524 設 busy，:1530 經 :1258 再同步；:483 的 busy 丟錯先於 :486 的同值早退 | 同步前以快取自比，或 busy 時跳過。第二次是無操作、不報錯、不出提示 | §1.3、PC17、AXIOM-DIFF §6 |
| F5 | 沒有寫入也會被讀成必須退休 | 補「沒有寫入就不重新蓋章，工作階段維持不變」 | §1.3、PC16 |
| F6 | 公理把新鮮度只寫成領域指紋，契約卻用 candidateStamp；「工作階段」「重新蓋章」沒有 D 編號 | 草稿新鮮度留在公理；本分頁工作階段有效性只留契約。兩詞移出公理。失效而不寫入有狀態列提示與 PC18 | I⟨K2b-3⟩、§1.3、§4.2 #1、PC18 |
| F7 | :1258 也被背景本機恢復（:198）與 `readScenarioProject`（:1274）叫到 | 點名並排除這兩條的候選寫入；PC19 | §1.3、§1.7、PC19 |
| F8 | `unknownHistory` 把全部房間標為需重新關聯（`source-plane.js:222–224`） | 條文改為身分無法確認時，全部房間轉為需重新關聯 | I⟨K2b-1⟩、ZR12、§4.2 #11 |
| F9 | R⟨K2b-1⟩「缺值寫 null」與 canonical「undefined 一律拒」不一致 | 兩邊改為：undefined 一律拒絕；只有 schema 明文可缺的位置寫 null | §1.2(b)、R⟨K2b-1⟩ |
| F10 | 每次接受的 roomsPin 最多逐房讀 boundary 10,000 次 | 寫明風險。上限：接受時不逐房現讀；新 D3 重用回執，其餘用快取；缺快取則本步失敗回滾 | §1.2(b)、PC06 |
| F11 | IM16 沒有「兩個撞名改成同一個新名稱」；PC16 負例靠非正式注入 | IM16 補該案例。PC16 負例標明測試接縫 | IM16、PC16 |
| F12 | §1.3 寫「共五處」，實際只列四處；D⟨K2b-4⟩(a) 把 D40 寫成「本層內建」 | 改為四個直接呼叫點，並分清 :1258 的呼叫端。D40 改為「依 D40 規格」 | §1.3、§1.7、D⟨K2b-4⟩(a) |

## r2 對照表（2026-10-10，依 opus 審查 S1–S10 與使用者「照裁決繼續修」）

| 審查項 | r1 問題 | r2 處置（全部暫定，依授權 L） | 改動位置 |
|---|---|---|---|
| S1 | `roomId` 須在集合內，與「過期仍可保存」矛盾（featureProposal 每次驗整份 envelope） | `roomId` 只驗格式；存在與否交給 roomsPin 判過期 | §1.2(a)、I⟨K2b-3⟩、PC13 |
| S2 | 規格新名稱只避開「已使用」，會撞同批匯入名稱 | 新名稱須避開目標既有、本次閉包全部與本次其他新名稱 | §2.2(b)3、I⟨K2b-4⟩(d)、IM16 |
| S3 | 保存前同步失敗時保存行為未定；暫停先釋放再寫，失敗回不去 | 保存照常、本次不寫草稿並明示；暫停先驗容量再釋放 | §1.3、I⟨K2b-3⟩、PC05、PC14 |
| S4 | 新分析靜默覆蓋已保存草稿（含其他錨點） | 有草稿時開始新分析須明選「捨棄已保存候選」（一步） | §1.3、I⟨K2b-3⟩、PC15 |
| S5 | 暫停／同步寫入使自己的 session 立即過期（stamp 含 revision 與 undo 頂端） | 寫入成功後受控重新蓋章續用；不能證明唯一變更則退休、由草稿恢復 | §1.3、I⟨K2b-3⟩、PC16 |
| S6 | 指紋要非同步算，保存前同步是同步呼叫；漏列三條保存路徑 | 指紋在分析與接受時算好快取；同步只在 session 新鮮時用快取；列出全部呼叫點 | §1.2(b)、§1.3、§1.7、PC17 |
| S7 | 匯入確認走 REST，回執與 history.observe 只走 `/api`；§3 檔案不重疊不成立 | confirm／cancel 改走 `/api` 橋接指令；補列 `reference-workspace.js`；改寫 §3 | §2.2(b)、§2.3、§2.7、§3、IM17 |
| S8 | 「唯一共同基準」與保留舊圖頁 P 衝突 | 明寫舊式參考圖頁不是共享基準、不受 SourcePlane 約束 | D⟨K2b-2⟩、I⟨K2b-1⟩、ZR11 |
| S9 | 狀態轉換與現行程式不一致 | 改為「需複核，或身分無法確認時需重新關聯」 | I⟨K2b-1⟩、ZR12、§4.2 #11 |
| S10 | 漏 D28 面套用字串 id；R⟨K2b-3⟩ 未處理 `surface` 同號 | D28 歸 (b)、由目標重新產生；§四改「其他型別配號另案」 | D⟨K2b-4⟩(b)、I⟨K2b-4⟩(b)、R⟨K2b-3⟩、§四 |
| 小錯 | dimensions 項結構；「過期仍可保存」出處 | 項目為 `{edge,length,kind:"user-confirmed-mm"}`（`room-outline-workspace.js:183`），沒有既有 validator；出處改 D⟨K2a-2⟩ | §1.2(a)、AXIOM-DIFF 依據、§4.1 |

基準：`a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e`（PR #169 head；`公理層.md` 與 main `5cc1ffa` 位元組相同）。
條文：`AXIOM-DIFF.md`（佔位條號 D⟨K2b-1⟩…）。岔路裁決：`decisions-provisional.md`（Z／P／C／G 編號）。

讀過並據以設計的現況（路徑 @ a7bff8f）：
- #87 首切片已在 #169：`geometry-web/room-collection-workspace.js:151–227`（session、stamp、park）、`:411–451`（接受後受控延續）、`:530–547`（回執恢復使 session 失效）。
- 零房現況：無 collection 的面只顯示「以此底圖連續新增房間」（`room-collection-workspace.js:247`），它把**目前面**轉成第一個房間（`reference-workspace.js:513–558`）——正是 PR157 §10 要避免的「把匯入預設矩形默認為房間」。
- `Controller.beginNew` 要求 collection 已存在（`room-collection.js:62–74`）；`addPlane` 是另一筆 metadata 交易（`:160–165`），不能和 native 新建合成一步。
- 匯入現況：開啟 `.gcanvas` 是整份替換（`reference-workspace.js:1577–1703`；一步復原來自 `adoptLoadedContext` 的 `history.replace`，`:1802–1811`）。跨專案只有兩條既有路徑：參數包（I39；native `import-parameters`）與工程做法包（I34；同 id／版本異內容拒絕）。組構規則 id 是 World 局部 uint32（`web_bridge.c:493–495`），專案內「複製規則」給新 id、版本重設為 1（`geometry-core/assembly.inc:207–212`）。

---

## 1. #87 零房起步與跨次保存候選

### 1.1 首版範圍（一個 PR）

一句話：**在尚無共享來源的已校準圖頁上，第一次接受候選（或人工描繪）時，一筆交易同時建立共享來源平面、房間集合、第一個房間與它的 D3；候選列表可隨 `.gcanvas` 保存、重開後恢復（一律重新核對）。**

包含：
1. 零房入口：宿主面 F 不是任何房間記錄的邊界、其作用中圖頁 P 已校準、專案沒有 `(P.sourceId, P.page)` 的 SourcePlane。面內「新增方式」選單沿用同一個控制項，三個選項：
   - 「把目前面設為第一個房間」（現行 adopt，行為不變）
   - 「人工描繪第一個房間」（新：staged 交易）
   - 「取得同頁候選」（新：staged 交易）
2. Staged 新建交易（I⟨K2b-2⟩／R⟨K2b-2⟩）：一個 history 群組內 native confirm 新 D3 ＋ 寫入 `source-rooms` 附件新增 plane＋collection＋room（＋候選草稿更新）。F、P、P 的來源紀錄與核對收據一律不動。
3. 首次接受成功後的延續：不使用 S5 的「唯一變更」。回執證明「只新增一 plane、一 collection、一 room、一 D3」，且 `room-candidates` 等於同一群組剛寫入的值（寫入的是移除則為無草稿；群組內沒有寫草稿者須仍無草稿，N2）→ session 錨點由圖頁改為新集合，host 改為新房間 R，其餘列清 reviewed（R⟨K2b-2⟩，F1）。
4. 候選草稿持久化：專案附件 kind `room-candidates`、schema `room-candidate-drafts/1`；寫入時機、容量、能力、過期判準依 I⟨K2b-3⟩／R⟨K2b-1⟩。
5. 重開／本機恢復後的恢復：開啟錨點所在面（集合錨點＝該集合任一房間；圖頁錨點＝宿主 F），面板顯示「已保存的候選（N 列）」；選列＝恢復（先驗新鮮度，新 generation，reviewed 全清）。

不在首版：見 §1.8。

**範圍變更聲明**：持久化候選推翻了實作邊界文件 MR04（`geometry-guide/ROOM-MULTI-CANDIDATE-IMPLEMENTATION-BOUNDARY.md:30,36`：不新增 manifest／IndexedDB／localStorage 欄位）與 PR157 §12(2) 的 session-only 邊界；兩處都明說跨次保存須「另訂持久 schema／容量／能力／失效」，本案即是該另訂（依授權 L，暫定，見 decisions P1）。

### 1.2 資料模型

#### (a) `room-candidates` 附件（`room-candidate-drafts/1`）

每專案 0–1 份。整份標準 JSON ≤ 1 MiB（UTF-8）。未知欄位、缺欄位、型別錯誤一律拒。

```text
RoomCandidateDraft {
  schema: "room-candidate-drafts/1",
  draftId: string /^[\w-]{1,100}$/        // 編輯身分，不是房間或 D3 id
  anchor:
    | {kind:"collection", collectionId, planeId, planePin:hex64, roomsPin:hex64}
    | {kind:"page", boundaryId:uint32>0, pageId:string, pagePin:hex64}
  analysis: {
    sourceId:hex64, page:int>=1, coordinateSpace:"pdf-page-viewport/1"|"image-pixel/1", pageSize:[w,h],
    crop:[x,y,w,h]                         // 分析當時取景，落在 pageSize 內
    options:{mode:"auto"|"vector"|"image", minWidth:finite>0, minLength:finite>0}   // 不收 "manual"
    barriers:[[x0,y0,x1,y1]] (≤64, 有限數)
    analyzerRevision:string ≤100            // 新常數 RoomOutline.ANALYZER_REVISION，首版 "room-outline-batch/1"
    total:int>=0, complete:bool, ignoredNested:int>=0
  }
  rows: [ (≤12) {
    rowKey: string ≤20000                   // 既有 component canonical key；不是 id
    ordinal: int 1..12 (唯一), method:"pdf-vector"|"image-lines",
    sourcePoints:[[x,y]] (4..256, 有限數),
    warnings:[string≤1000] (≤100),
    deviation: finite>=0,
    pointsMm:[[int,int]] (4..256, |v|≤1e8, 每邊正交),
    dimensions:[{edge:int>=0, length:int>0, kind:"user-confirmed-mm"}] (≤256; 現行 room-outline-candidate 沒有 validator，項目結構取自 `room-outline-workspace.js:183`，本 schema 自行驗),
    rawInputs:{refRoomVertices, refRoomLength, refRoomEdge} (各為原字串 ≤20000 UTF-16，不 trim、不轉數),
    draftRevision:int>=0,
    status:"pending"|"excluded"|"accepted"|"existing",
    roomId?: string /^[\w-]{1,100}$/          // 僅 status=accepted 時必有；只驗格式，存在與否由 roomsPin 判過期（S1）
  } ]
}
```

不存：`reviewed`、preview token、lease、generation、runId、Worker 狀態、DOM 焦點、選中列。

#### (b) 指紋（R⟨K2b-1⟩，新增純函式於 `geometry-web/source-plane.js`）

```text
canonical(v) = JSON.stringify(v)            // 陣列固定順序；ECMAScript 數字最短往返
                                            // undefined 一律拒絕，不得省略（F9）
                                            // 只有下方 schema 明文可缺的位置寫 null：校準為 null、被引用 D3 不存在時原生指紋為 null
planePin(plane) = sha256(canonical([id,sourceId,page,coordinateSpace,pageSize,
                    calibration?[points,distanceMm,inputValue,inputUnit]:null,
                    [alignment.x,alignment.y,alignment.mmPerPx,alignment.rotation], basisRevision]))
roomsPin(state, collectionId, nativePin(bid)) = sha256(canonical(collection.roomIds.map(id =>
                    [id, room.boundaryRef.id, nativePin(room.boundaryRef.id)??null, room.acceptedBasisRevision, room.reviewState])))
pagePin(page) = sha256(canonical([page.id,page.sourceId,page.page,page.imgW,page.imgH,page.mmPerPx,page.x,page.y,page.rot,
                    page.calibration?[points,distanceMm,inputValue,inputUnit]:null]))
```

`nativePin` 用既有 `GeometryRoomCollection.boundaryPin(native "boundary <id>")`。取景、透明度、鎖定、房名不入指紋（呈現資料）。

**指紋計算時機（S6、N1）**：roomsPin 需非同步讀原生 D3 再算 SHA-256，所以 session 在三個非同步時點算好並快取 `anchorPins`：分析結果被接受進 session 時（`receiveCandidates`）、每次接受成功的群組內（只把本筆新 D3 寫進快取，見下段）、從附件恢復時（驗新鮮度那一次）。其中分析時與從附件恢復時要逐房讀取，批次與失敗規則見下下段（N1）。所有寫入（暫停、保存前同步、接受）只用快取；保存前同步是同步呼叫，不做任何 await。

**接受時的讀取上限（F10、N1）**：集合最多 10,000 房（`source-plane.js` 的 `MAX_ROOMS`）。若每次接受對每一房各送一次 `boundary <id>`，最多 10,000 次往返；`/api` 單筆逾時 15 秒（`app.js:567`），總時間沒有上限。因此接受路徑不逐房現讀：其餘房間只用既有快取的 nativePin；群組內寫草稿所需的本筆新 D3 nativePin，只取 `commitWithMetadata` 在 `line confirm` 之後讀回的那一次（rcw:77 的 `boundary <id>`），不再另送。rcw:440–441 是群組結束後、續用核對時另讀一次新房（現行行為），不屬群組內的草稿寫入，也不是上述重用的對象。接受入口先檢查快取可用且涵蓋集合全部房間，否則在 prepare 之前拒絕（零 native mutation）；若群組內才發現快取缺任一房，本步失敗，依 I⟨K2b-2⟩ 整筆回滾，不得改為現場逐房補讀。

**快取建立的批次與失敗行為（N1）**：分析與恢復兩個時點要為集合內每一房各讀一次 `boundary <id>`（圖頁錨點沒有 roomsPin，不建此快取，不受本段影響）。
- 分批：每批最多 64 房，批與批之間必須 `await` 讓出事件圈，不得在同一同步回合把整個集合的讀取連續送出；批內順序與併發不限。10,000 房最多 157 批。每筆讀取仍受 `/api` 15 秒逾時；整體耗時沒有硬上限，但每批結束後核對 stamp，捨棄、切面、重新分析或 stamp 已變即中止並丟棄已讀結果。建立完成前，候選列可檢視、不可接受。
- 單筆失敗：任一房的讀取失敗（逾時、transport 錯、回覆缺失或算不出 nativePin）→ 立即停止後續批次，快取標「不可用」；不重試、不以部分快取續行、不寫入任何附件。
- 不可用時，session 只可檢視、捨棄、重新分析。**不得接受**（接受入口在 prepare 之前拒絕，零 native mutation）；**不得暫停**（拒絕，編輯器與輸入保持原狀，同 S3）；**不寫草稿**（沒有可信的 roomsPin 可寫）：保存照常，狀態列明示「候選未寫入檔案：房間指紋無法建立，檔案內仍是上次保留的候選（或沒有候選）」。面板明示「房間指紋無法建立（讀取第 N 房失敗），本次候選不能接受；可檢視、捨棄或重新分析」。
- 從附件恢復時失敗同樣處理：草稿無法驗新鮮度，列不可選，只可檢視、捨棄、以相同設定重新分析；附件原封不動。
- 重新分析並建完快取後才恢復可接受。這避免出現「永遠無法接受卻看似可用」的 session。

#### (c) Staged 新建意圖（`geometry-web/room-collection.js`）

```text
Controller.beginNewStaged({plane, collectionId, display, host:{boundaryId, pageId, pagePin}})
  前置：requireIdle；plane = S.fromPage(P, type, uuid) 且 basisRevision=1；plane.calibration 非 null；
       state 中無 sourceId:page 相同的 plane；planes<256、collections<256、rooms<10000
  intent = {..., staged:{plane, collectionId, display, host}, collectionId, roomId:null, room:null}
assertCurrent(intent) 另驗：integration.readHostPage(host.boundaryId, pageId) 存在且 pagePin 相同；仍無同頁 plane
attachmentForPin(pin)（staged）：next = S.upgradeDisplay(intent.state || S.empty())；
  push plane；push {id:collectionId, planeId:plane.id, roomIds:[roomId]}；push room(display = staged.display)；S.validate(next)
```

`display` = `{crop:P.crop, opacity:P.opacity, locked:P.locked}`（同 `adoptRoomSource` 的作法）。新房的 mm 外環由 P 的基準換算，與 `S.materialize(plane, …)` 用同一組 x／y／mmPerPx／rot，所以接受前後座標一致。

### 1.3 交易與 undo 邊界

| 動作 | 交易／歷史 | 失敗 |
|---|---|---|
| 零房接受（候選或人工） | 一個 history 群組：`line history-begin` → `line confirm <token>` → 讀回 D3 指紋＝預覽指紋 → `setFeatureAttachment('source-rooms', …, {recordHistory:false, roomLease})`（＋必要時 `room-candidates`）→ `line history-end`。**一步復原**同時移除 D3、room、collection、plane；重做全回。延續不走 S5：依 R⟨K2b-2⟩，回執證明只新增一平面、一集合、一房、一 D3，且草稿等於同一群組剛寫入的值（F1）；群組內沒有寫草稿（原本就沒有草稿）者須仍無草稿（N2） | 全回滾；回覆未知沿既有 receipt recovery，不重送，session 標失效。延續不能證明時，剩餘列候選工作過期（不是 R⟨K2b-1⟩ 的草稿過期；已寫入的草稿仍依指紋判新鮮度），不把已成功的接受改判失敗 |
| 既有集合的新建接受 | 前置：roomsPin 快取可用且涵蓋集合全部房間，否則在 prepare 之前拒絕（N1，§1.2(b)）。同上（現行 #77 交易），若有候選草稿則同群組更新該列為 accepted（新 D3 的 nativePin 取自 rcw:77 的讀回）；沒有候選草稿則群組內不寫。延續不走 S5：用現行回執（rcw:432–447：只多一房、既有房間與平面與取景保留、新 D3 指紋相符、核對期間 stamp 沒再變），並加上草稿等於同一群組剛寫入的值（F1）；群組內沒有寫草稿者須仍無草稿（N2） | 同上；不能證明則剩餘列候選工作過期（不是 R⟨K2b-1⟩ 的草稿過期），不把已成功的接受改判失敗 |
| 暫停（park） | **先**把作用中列快照到記憶副本並以 `featureProposal` 驗整份 envelope 與專案清單容量（不寫入）；通過才釋放編輯器（`releaseCandidateEditor`）並寫 `room-candidates`：一筆 local history「暫停並保留房間候選」 | 容量或驗證不過：拒絕暫停，編輯器、intent 與輸入完全保持原狀（S3） |
| 保存前同步（flush） | 同步函式，直接呼叫點是四個，不是五個（F12）：`save`（:1516，在 :1524 設 busy 之前）、`freezeScenarioProject`（:1440）、`finishScenarioEditor`（:1464）、`exportSnapshot` 無 owner 時（:1258）。`createScenarioEditorTicket`（:1381）帶 owner，不進入 :1258，不寫。:1258 的呼叫端另有 `exportBytes`（:1272，寫一次）、`save` 的第二次（:1530，此時已 busy）、背景本機恢復 `persistSession`（:198）與 `readScenarioProject`（:1274）。後兩條即使 session 新鮮也排除候選寫入：不呼叫 `setFeatureAttachment`、不報錯、不出提示，快照沿用上次已寫入的草稿（F7）。其餘呼叫點的寫入條件：session 存在且新鮮、`assertCandidates` 通過、`active===null`、未 committing。呼叫 `setFeatureAttachment` 之前先用快取與現行附件比對，相同則不呼叫；`busy` 時直接返回，不走到 :483 的丟錯（F4） | 容量或驗證不過：**保存照常**，本次不寫草稿，狀態列明示「候選未寫入檔案：檔案內是上次保留的候選（或沒有候選）」（S3）。工作階段已失效：**保存照常**、本次不寫，狀態列明示「候選未寫入檔案：本分頁工作階段已失效，檔案內仍是上次保留的候選（或沒有候選）」（F6）；不把這句說成容量錯誤。有 active 編輯器時仍由 `hasWork` 擋保存（MR05 不變）。`save` 的第二次是無操作、不報錯、不出提示、不新增步驟 |
| 寫入後續用（S5，F1，F5） | 只適用暫停、保存前同步、捨棄，不適用接受。這三者寫入成功後才比對：`source-rooms` 與其他附件、World 修訂之外的房間與幾何指紋都不變，`room-candidates` 等於剛寫的值，history 頂端是剛推入的那一步 → 以新狀態重新蓋章（`s.stamp=candidateStamp(...)`、新 generation）。沒有寫入就不重新蓋章，工作階段維持不變 | 比對有任一不符：工作階段退休，原因「無法確認草稿寫入是唯一變更」，改由附件恢復。正式操作插不進寫入與蓋章之間；負例標明測試接縫（PC16，F11） |
| 房間指紋快取不可用（N1，§1.2(b)） | 分析或恢復時分批（每批 64 房、批間讓出事件圈）讀 boundary 建快取，任一房讀取失敗即標「不可用」。此時 session 只可檢視、捨棄、重新分析：接受在 prepare 之前拒絕（零 native mutation）；暫停拒絕；暫停與保存前同步都不寫草稿；附件原封不動 | 保存照常，狀態列「候選未寫入檔案：房間指紋無法建立，檔案內仍是上次保留的候選（或沒有候選）」；面板「房間指紋無法建立（讀取第 N 房失敗），本次候選不能接受；可檢視、捨棄或重新分析」。重新分析並建完快取後才恢復可接受（PC21） |
| 開始新分析（S4） | 專案已有 `room-candidates`（不論錨點是否相同）：確認框改為「捨棄已保存的 N 列候選並重新分析」；確認＝先寫 null（一步「捨棄房間候選」）再分析 | 取消＝什麼都不改 |
| 捨棄剩餘候選 | 有附件：寫 null＝一筆 local history「捨棄房間候選」；無附件：只清記憶體 | — |
| 排除／恢復列、切列、修正 | 不寫附件、不進 history（同現行） | — |
| undo/redo 任一步 | 記憶體 session 照現行規則失效；附件隨 context snapshot 回到該步狀態，可再從附件恢復 | — |
| core-only undo 回退（`project-store.js:862–888`） | 附件保留（現行即保留 featureAttachments），房間被標 needs-reassociation → roomsPin 不符 → 草稿過期 | — |

「沒有 pending／excluded 列」時任何寫入改為寫 null（移除）——全部接受完的 session 不留附件、不強迫新格式。

### 1.4 能力宣告與格式

- 零房起步：**不新增能力**，沿用 `source-room-collection/1`、`source-room-display/1`（新房一律 `source-rooms/3`，因 `upgradeDisplay`）。
- 候選草稿：editor/reader 能力 `room-candidate-drafts/1`（同 `grid-editor-draft/1` 的層級：只進 `readerCapabilities` 與專案 `requiredCapabilities`；`sceneCapabilities`、native required capabilities 與原生能力 validator 一律拒它）。
- 格式：新增 `geometry-canvas/⟨K2b-F⟩`（與 K2a 依合併順序配號：先合者取 /17）。只有存在 `room-candidates` 附件才用新版；保留 /16 以下全部能力。降版、移除能力、未知 schema `room-candidate-drafts/2`、附件數 >5 均在替換專案前拒。
- `feature-attachments.js`：`assertKind` 白名單加 `room-candidates`；envelope `records.length` 上限 4→5；`capabilities()` 回 `room-candidate-drafts/1`；此 kind 單筆上限 1 MiB（envelope 現行一律以 8 MiB 驗，`feature-attachments.js:205,224`；128 KiB 只用於 grid-draft 單筆，`:173,210,230`）。**必改**：現行 `boundedJSON` 對每個字串限 `MAX_STRING=4096`（`:16,124`，只有 legacyGeometry 路徑放寬到 100000），而本 kind 的 `rawInputs` 與 `rowKey` 允許 20,000（256 頂點的 refRoomVertices 就可能超過 4096）——須比照 legacyGeometry 加一條只對 `room-candidates` 的 rows 原字串／列鍵路徑放寬到 20,000 的規則，否則 PC05 的 20,000 邊界不成立。`room-candidates` 不計入 source-rooms 的 lifecycle reserve。

### 1.5 使用流程

**零房（候選）**：匯入 PDF →「建立描繪用面（預設矩形）」得 F＋P → 兩點校準 → 面內「新增方式＝取得同頁候選」→「分析來源取景」→ 列表 → 選列、核對、修正 →「接受為新房間」→ 命名 → 預覽對話框文字：「建立共享來源（第 N 頁目前基準）與第一個房間；目前描繪用面 F 保留、不關聯」→ 確認 → 焦點到新房 R，列表在 R 的面板繼續（集合錨點）。

**零房（人工）**：同上但選「人工描繪第一個房間」→ 逐點描繪 → 同一 staged 交易。

**跨次保存**：任一時刻「暫停並保留候選」或直接「保存專案」（無 active 編輯器且 session 新鮮時自動 flush；flush 超限或工作階段已失效時保存照常並明示未寫入）→ 下載／寫入 `.gcanvas` → 新分頁開啟 → 進錨點面 → 「已保存的候選」→ 選列（驗新鮮度；過期則只顯示原因與「捨棄」「以相同設定重新分析」）。

**提示文字更動**：`beforeunload`／`mayLeave` 的候選提示只在「記憶體 session 與附件不同」時出現（`hasUnpersistedCandidates`），不再對已保存的候選誤報會遺失。

### 1.6 驗收測試清單（具體例）

純函式／VM（Node）夾具：圖頁 `P = {id:"pg1", sourceId:<fixture sha>, page:1, imgW:300, imgH:250, crop:[0,0,300,250], x:0, y:0, mmPerPx:10, rot:0, opacity:0.5, locked:false, records:[], calibration:{points:[[0,0],[100,0]], distanceMm:1000, inputValue:100, inputUnit:"cm"}}`（opacity／locked 取 `applySource` 預設，`reference-workspace.js:1160–1162`）；障礙沿用 `tests/test_room_multi_candidate.js` 的三環（期望來源外環第一列 `[[22,22],[118,22],[118,98],[22,98]]` → mm `[[220,220],[1180,220],[1180,980],[220,980]]`）。

| ID | 操作 | 必須觀察到 |
|---|---|---|
| ZR01 | 無 source-rooms 附件；F=boundary 1（4000×3000）、P 如上；取得候選→第 1 列命名「房 A」接受 | boundary 1 的 dump 行逐字不變；新 boundary id＝接受前 `newid` 的 boundary 值；附件 schema `source-rooms/3`，planes＝[fromPage(P)]（basisRevision 1）、collections＝[{planeId, roomIds:[A]}]、rooms＝[A：boundaryRef.id＝新 id、reviewState confirmed、acceptedBasisRevision 1、display {crop:[0,0,300,250],opacity:P.opacity,locked:P.locked}]；F 仍掛 P（records、reconstructionReviews 不變）；history 恰多一步 |
| ZR02 | ZR01 後一次 undo、再 redo | undo：新 D3 不在 objects、附件回到「無 source-rooms」、F/P 不變、session 失效；redo：與 ZR01 結果逐欄相同 |
| ZR03 | ZR01 後不重新分析，選第 2 列接受「房 B」 | 走既有集合新建；同一 plane、collection.roomIds＝[A,B]；第 3 列仍 pending、reviewed=false |
| ZR04 | 另一面 G 已 adopt 同 sourceId:page 成 plane；在 F 上零房接受 | 在 prepare 前拒絕，訊息指向既有共享來源；World、附件、history、dirty 不變；無殘留 native preview token |
| ZR05 | 預覽後、確認前改 P 校準（mmPerPx 10→12） | 確認拒絕（過期）；零 native mutation；不改用新基準 |
| ZR06 | 附件已有 256 planes | admission 拒（prepare 前）；同上不變 |
| ZR07 | native confirm 成功但回覆丟失 | 不重送；receipt recovery 後狀態＝回執；session 失效；F/P 不變 |
| ZR08 | 命名對話框取消 | staged intent 退休；不建 plane；`hasWork=false` |
| ZR09 | 候選外環與 F 外環完全相同 | 列上警告「與目前描繪用面外環相同」；仍可接受；接受後 F 與新 D3 並存 |
| ZR11（S8） | ZR01 後改 F 上舊圖頁 P 的校準 | 平面 basisRevision 仍 1、房 A 仍已核對；P 自己的校準照改；兩者並存不被視為違反同頁唯一平面 |
| ZR12（S9、F8） | ZR03 之後房 A、房 B 都已核對；送一筆未配對到已記錄預覽的 `line confirm` | 房 A 與房 B 都轉需重新關聯，沒有房間維持已核對或需複核；房間記錄不刪 |
| ZR10 | ZR03 後真 `.gcanvas` 保存→新 profile 開啟 | plane／collection／A、B／F＋P 逐欄 roundtrip；格式依資料（無草稿附件時不升到新版） |
| PC01 | 接 ZR01 狀態（集合錨點、第 2、3 列 pending）：第 2 列改頂點並在 refRoomLength 留 `"1e"`、refRoomEdge `" 003 "`，排除第 3 列 → 暫停 → 保存 → 新 profile 開啟 → 進房 A 面板 | 附件逐欄 roundtrip（原字串逐字、status、ordinal、dimensions）；`requiredCapabilities` 含 `room-candidate-drafts/1`；格式＝新版；選第 2 列後所有列 reviewed=false，編輯器顯示原字串 |
| PC02 | PC01 的檔案先改共同基準（basisRevision 2）再保存、重開 | 草稿過期，原因「共同基準已變更」；列不可選；「捨棄」後附件消失、一步可復原 |
| PC03 | 暫停後解除房 A 關聯 → 保存 → 重開 | roomsPin 不符→過期 |
| PC04 | 把 PC01 檔 manifest 改 format `/16`；另一份刪 `room-candidate-drafts/1`；另一份 schema 改 `/2` | 三者皆拒開，目前專案不變 |
| PC05 | 第 2 列 refRoomVertices 長 20,000（合法，須能存取；驗 MAX_STRING 放寬確實生效）；再改成 20,001 | 前者暫停成功、重開逐字相同；後者在釋放編輯器之前就拒絕暫停（S3：先驗容量），訊息指出超限；編輯器、intent（hasWork 仍為 true）與輸入保持原狀，附件不變 |
| PC06（F10、N1） | 恢復後核對第 2 列並接受。另設兩案：(甲) 接受前拿掉既有房的 nativePin 快取（視同快取不可用）；(乙) 測試接縫：接受入口檢查通過後、群組內才移除某既有房的快取 | 主案：native D3＋room＋草稿（該列 accepted＋roomId，roomsPin 重算）同一步；undo 後該列回 pending、房間消失。接受過程不為既有房間另送 `boundary <id>`；群組內草稿用的新 D3 nativePin 只重用 rcw:77 讀回的那一次（不是 rcw:440–441 群組結束後的續用核對讀取）。(甲) 在 prepare 之前拒絕，零 native mutation、零 history、零 `boundary` 讀取。(乙) 本步失敗並整筆回滾，不得改為逐房補讀（F10） |
| PC07 | 無 active 編輯器時直接保存（未按暫停） | flush 寫入最新列表；有 active 編輯器時保存被既有 gate 擋 |
| PC08 | 暫停兩次（中間改第 1 列）後 undo 一次 | 附件回到第一次暫停的內容；記憶 session 失效；從附件恢復得到第一次的列 |
| PC09 | 零房 session 暫停→保存→重開→接受第 1 列 | 圖頁錨點新鮮；接受建立 plane（ZR01 同結果）；附件錨點改為 collection |
| PC10 | 把附件 analyzerRevision 改成 `"room-outline-batch/0"` | 不過期；每列加註「分析器版本不同」 |
| PC11 | 所有列 accepted/existing 後 flush | 附件被移除（寫 null），格式不因草稿升版 |
| PC12 | 舊 `/16` 專案（無草稿）開啟→不碰候選→保存 | 仍為 `/16`，位元組語意不變 |
| PC13（S1） | PC06 後解除房 A 關聯（草稿中該列 accepted、roomId=A） → 保存 → 重開 | 保存與開啟都成功（roomId 只驗格式）；草稿判過期（roomsPin 不符）；可捨棄 |
| PC14（S3） | 草稿已有一份；把列原字串加長使整份 >1 MiB → 直接保存 | 保存成功；檔案內 `room-candidates` 是先前那份；狀態列有「候選未寫入檔案」明示；記憶 session 不變 |
| PC15（S4） | 已保存集合 X 的草稿；到另一來源頁 Y 開始新分析 | 確認框文字含「捨棄已保存的 N 列候選」；取消→附件與 session 不變；確認→history 多一步「捨棄房間候選」後才分析；undo 一步→草稿回來、新分析 session 退休 |
| PC16（S5、F1、F5、F11） | 暫停後立刻選第 1 列；再對已與附件同值的 session 做一次保存前同步 | 暫停後不出現「舊候選已失效」，可直接核對，且已重新蓋章。值相同的那次同步沒有寫入、不重新蓋章、工作階段維持不變、不出現退休。負例標明測試接縫：寫入回傳後、重新蓋章前，由測試替身再寫一筆其他附件 → 工作階段退休，從附件恢復得到剛寫的列。正式環境沒有使用者動作能插在這兩步之間 |
| PC17（S6、F4） | 分別經 `save()`、`exportBytes()`、`freezeScenarioProject`、`finishScenarioEditor`；另經 `createScenarioEditorTicket` | `save()` 在 :1516 寫入一次；:1524 設 busy 之後，:1530 經 :1258 的第二次是無操作、不報錯、不出提示、不新增第二步。`exportBytes`、`freezeScenarioProject`、`finishScenarioEditor` 各寫入一次（值同則不加步）。`createScenarioEditorTicket` 不寫。同步函式內沒有 await |
| PC18（F6） | 領域指紋不變，但 candidateStamp 的 revision 或 undo 頂端已變，且沒有 active 編輯器；直接保存 | 保存成功；`room-candidates` 仍是上一份；狀態列為「候選未寫入檔案：本分頁工作階段已失效，檔案內仍是上次保留的候選（或沒有候選）」；沒有重新蓋章。重開後草稿依領域指紋仍新鮮，可恢復 |
| PC19（F7） | 記憶體列比附件新且 session 新鮮。分別讓 `persistSession`（:198）與 `readScenarioProject`（:1274）走到 `exportSnapshot` | 兩條都不寫 `room-candidates`、不新增 history、不報錯、不出「候選未寫入」提示；快照內是上次寫入的草稿。對照 PC17 的 `exportBytes` 會寫入最新列 |
| PC20（N2） | 既有集合 X（房 A），第 2、3 列 pending。三案：(甲) 已暫停保存過（附件有草稿），恢復後核對第 2 列並接受；(乙) 從未暫停也未保存（附件無 `room-candidates`），核對第 2 列並接受；(丙) 零房、圖頁錨點、附件有草稿（PC09 狀態），接受第 1 列 | (甲) 群組內草稿更新為第 2 列 accepted＋roomId；回執核對通過；session 續用，不出現「候選已失效」；第 3 列仍 pending、reviewed=false，可繼續核對，附件內第 3 列仍 pending。負例（測試接縫）：群組結束後、續用核對前由替身改寫附件草稿 → 續用失敗，剩餘列候選工作過期，已接受的房間不改判失敗。(乙) 群組內不寫草稿；接受後附件仍無 `room-candidates`、格式不升版；session 續用，第 3 列 pending、reviewed=false。(丙) 錨點改為新集合，附件錨點同步改為 collection；session 續用，第 2、3 列 pending、reviewed=false。三案各只多一步 history |
| PC21（N1） | 集合 130 房（測試替身提供 `boundary <id>` 讀取，可逐筆延遲或失敗）。(甲) 分析一次；(乙) 第 70 房的讀取逾時；(丙) 附件有草稿，恢復時第 130 房讀取失敗 | (甲) 讀取分為 64、64、2 三批，批與批之間各讓出至少一次事件圈（測試斷言每批結束到下一批開始之間經過至少一個 macrotask）；建完前接受鈕停用、列可檢視；建完後可接受。(乙) 第 70 房在第 2 批；失敗後不再送第 3 批的讀取；快取「不可用」；面板顯示「房間指紋無法建立（讀取第 70 房失敗）…」；接受被拒且零 native mutation、零 history；選列檢視後暫停被拒，編輯器與輸入保持原狀；未選列（無 active 編輯器）時直接保存成功並顯示「候選未寫入檔案：房間指紋無法建立…」，附件不變；捨棄與重新分析可用，重新分析建完快取後可接受。(丙) 草稿列不可選，顯示「無法確認新鮮度」，只可檢視、捨棄、以相同設定重新分析；附件位元組不變 |

既有回歸：`tests/test_room_collection.js`、`tests/test_room_multi_candidate.js`、`tests/test_project_store.js`、`tests/room_multi_candidate_browser.js`、原 #54 單房與 #77 人工新建流程、完整 `cdp_test.js`（若動到 `app.js`）。

### 1.7 受影響檔案

| 檔案 | 變更 |
|---|---|
| `geometry-web/room-collection.js` | `beginNewStaged`、staged `assertCurrent`、`attachmentForPin` staged 分支 |
| `geometry-web/source-plane.js` | `planeForSourcePage`、`planePin`、`roomsPin`、`pagePin`（純函式） |
| `geometry-web/feature-attachments.js` | `room-candidates` kind／`room-candidate-drafts/1` validator、能力、上限 |
| `geometry-web/project-store.js` | 新格式常數與 `formatPolicy`、manifest keys、能力守門 |
| `geometry-web/reference-workspace.js` | `setFeatureAttachment` 的 grouped 寫入允許 `room-candidates`（同 room lease）；`featureProposal` 同時驗兩種附件；候選 flush 的四個直接呼叫點（:1516、:1440、:1464、:1258）。:1258 對 `persistSession`（:198）與 `readScenarioProject`（:1274）排除候選寫入；:1381 不加。`mayLeave` 改 `hasUnpersistedCandidates`；`roomIntegration.readHostPage`。匯入 PR 另改 :37 與 :418–420，見 §3 |
| `geometry-web/room-collection-workspace.js` | 零房面板（方式選單）、錨點抽象（collection／page）、staged 接受、延續改錨、park 寫入、flush、discard、從附件恢復、房間指紋快取（分批建立、不可用狀態，N1）、接受時同群組更新草稿 |
| `geometry-web/room-outline-workspace.js` | `collect` 不再要求 collection（改用錨點 stamp）；訊息文字 |
| `geometry-web/room-outline.js` | `ANALYZER_REVISION` 常數 |
| 文件 | `geometry-web/docs/ROOM-OUTLINE.md`、`FEATURE-ATTACHMENTS.md`、`REFERENCE-PROJECT.md`、`BACKLOG.md`（GEO-219 減項紀錄） |
| 測試 | `tests/test_room_collection.js`、`tests/test_room_multi_candidate.js`、`tests/test_project_store.js`、`tests/room_multi_candidate_browser.js` 四個既有檔擴充；`tests/run_all.py` 登錄 |
| `geometry-web/app.js` | 必改檔，但白名單改動在匯入 PR，不在本 PR。#87 的確認指令是既有 `line confirm`：`:532`、`:546`、`:608` 的 regex 與 rw:37 都含 `line `，所以這幾處 #87 不必改；房間路徑帶 roomLease，在 `:532` 走 `assertTransaction(roomLease)`。**`:555` 的確認租約 regex 目前只有 `assembly-confirm\|section-profile-confirm`，不含 `line confirm`，#87 也不依賴它**（房間路徑靠 roomLease 走 `:532`，不是靠 `:555`）。`:549–554` 是網格草稿專用的確認租約（`featureConfirmations` 只由 `grid-system-workspace.js:907` 經 `prepareFeatureConfirmation` 登記，`reference-workspace.js:93`）；#87 的房間 token 來自 `line preview` 的 `++g_preview_serial`（`geometry-core/transactions.inc:485`），經 roomLease 走 `:532`，不會登記進 `featureConfirmations`，也就不會走 `:549–554`（均 @ a7bff8f）。匯入 PR 須把 `definition-import-confirm` 加進包含 `:555` regex 在內的七處，逐一見 §2.3、§2.7。兩 PR 不平行寫此檔；排序見 §3 |

### 1.8 不做的事

- 同頁已有 SourcePlane 時「明選改用該平面並重新分析」（首版直接拒，Z3）。
- 自動批量接受、多份並存的候選草稿、跨頁或整屋分析、斜／弧牆候選。
- 自動把描繪用面 F 刪除、關聯或改形；自動遷移 legacy 圖頁 P 進平面。
- 保存「已核對」、預覽令牌、Worker 進度；過期草稿的修正移植到新 run。
- IndexedDB／localStorage 另存一份候選（本機恢復沿用既有整包暫存，不另立通道）。
- 私人 PDF、實體 iOS 驗收（另列人工清單，未做即標未驗）。

---

## 2. 非空專案匯入時的 ID 碰撞

### 2.1 首版範圍（一個 PR）

一句話：**新增「從其他專案匯入定義」：從另一份 `.gcanvas` 選組構規則版本／組構綁定，連同其參數卡、具名規格、timber 材料版本閉包，以獨立副本加入目前（可非空）專案；World 局部 id 一律重配、子身分保留、材料版本同穩定身分／版本且同指紋才共用、同身分／版本異指紋整批拒、規格撞名須明選；一筆候選、一次預覽、一步復原。**

身分處理限 D54 已列舉的類別，首版匯入型別限 D55；本列舉未涵蓋的身分（例如 D41／D42 id、D47／D48 key）須先補入公理，不能只加能力與驗收。後續幾何併入、網格來源、空間模型、專案附件須另核型別、身分與閉包契約，不由本首版預先承諾。

首版明確支援：根＝D32 規則版本、D33 綁定；閉包＝D32 規則版本（作為綁定閉包依賴，P-056 A 已定、D55／白話仍待同批同步）、D31 卡片（含遞移）、D6b 規格、D26 timber 材料版本。其餘一律 UNSUPPORTED（整包不執行）。

「開啟專案」維持整份替換，不改。

### 2.2 資料模型與協定

不新增保存格式：匯入後的物件就是普通 World 定義（既有 `/6` 參數、`/7` 組構、`/5` 工程格式依資料選擇）。不保存來源追溯。

#### (a) Native 唯讀讀取（隔離 World）

```text
bridge: definition-import-read <server-owned scene file>
service: POST /definition-import/read   body = 來源 world.scene 文字（≤16 MiB）
回 {ok, scene_sha256, required_capabilities, definitions:{
      rules:[{id,version,name,fingerprint,content}],
      bindings:[{id,name,rule:{id,version},fingerprint,slots:[...]}],
      parameters:[{id,name,fields:[...]}], specs:[{name,value}],
      materials:[{id,version,kind,fingerprint,content}] }}
```
隔離 World：與 `engineering-validate` 同性質，不碰 live World、不佔 `/upload` 候選槽、不消耗任何 token。

前端：用 `ProjectStore.unpack` 驗 ZIP／manifest／`sceneHash`／能力（讀取端不支援的能力→拒），**不**建 context、不驗或渲染 PDF、不載入模型。

#### (b) Native 預覽／確認

```text
POST /definition-import/preview
{schema:"definition-import/1", expectedRevision, sourceScene:<text>, sourceSceneSha256,
 roots:{rules:[{id,version}], bindings:[id]},
 names:{ "<specName>": {mode:"rename", name:"<new>"} | {mode:"map-existing"} } }
→ {ok, preview:{valid, token, map:{
      rules:[{from:{id,version}, to:{id,version}, class:"world-local"}], bindings:[{from,to,class:"world-local"}],
      parameters:[{from,to,class:"world-local"}],
      specs:[{from:name, to:name, class:"name", action:"create"|"rename"|"map-existing", value, targetValue?}],
      materials:[{id,version,class:"content-global",action:"share"|"create"}] },   // class＝D⟨K2b-4⟩ 類別，I⟨K2b-5⟩ 要求列出
    bindings:[{to, slots:[{slotId, A:{effective, path}, B:{effective, path}}]}],
    conflicts:[...], diagnostics:[...] }}
/api  definition-import-confirm <token>   → {ok, revision, history_changed:true}   // 經 /api 才有回執與 history.observe（S7）
/api  definition-import-cancel <token>
// 先例：assembly 的 preview 走 REST file_request（serve.py:559–562），confirm 走 /api（assembly-workspace.js:286、serve.py:176–203）
```

規則（全在 native 候選 World 內，R⟨K2b-3⟩）：
1. 閉包：binding → 其 `rule {id,version}`；slot 來源 `parameter` → 卡片（I39 遞移閉包）；`spec` → 規格；`material` → D26 版本。選 rule version 為根時只帶該版本。
2. 材料 (a 類)：目標有同 id／version：fingerprint 同→`share`；不同→整包拒（列 `id@version`）。無→`create`。`archived` 是專案狀態：新建者未封存，共用者沿用目標狀態。
3. 規格 (d 類)：目標無同名→同名同值建立；有同名→`names` 必須給該名的明選，否則 `valid:false`，診斷列出未決名稱。`rename` 的新名須同時滿足四項（F11）：(i) 不同於目標既有的任何規格名稱；(ii) 不同於本次閉包內的全部規格名稱（以來源名稱計，含目標無同名、將以原名建立者）；(iii) 不同於本次其他任何 `rename` 的新名稱；(iv) 符合現行 `spec` 宣告文法。(i)–(iii) 任一不符 → 整批拒絕：預覽 `valid:false`、不發令牌、`conflicts` 列碼 `IMPORT_RENAME_COLLISION` 與撞到的對象，零 World、附件、dirty、history 變化；本次任兩個 `rename` 的目標同名時，不忽略其一、不取先者、不讓第二個靜默通過。(iv) 不符 → `valid:false`，診斷列出該名稱。`map-existing` 不改目標規格，預覽列 `value→targetValue`。第 (v) 項（r4.1；作用於 `names` 的鍵，不是 `rename` 的新名，所以上述「四項」仍專指新名）：`names` 的每個鍵都必須是本次閉包內、目標有同名而須明選的規格名稱。鍵若指到 (a) 目標無同名、因此不需改名的規格（它將以原名建立），或 (b) 不在本次閉包內、或根本不存在的規格名稱，不論 `mode` 是 `rename` 或 `map-existing` → 整批拒絕：預覽 `valid:false`、不發令牌、`conflicts` 列碼 `IMPORT_RENAME_UNNEEDED` 與該鍵（註明屬 (a) 或 (b)），零 World、附件、dirty、history 變化；呈現方式同 `IMPORT_RENAME_COLLISION`。不忽略該鍵、不視為預先改名、不因其他鍵合法而放行。
4. 配號 (b 類)：卡片→規則→綁定；同型別先把閉包內來源 id 升冪排序，再用**該型別的既有匯入／配號規則**對「目標＋已配」取號：
   - D31 卡片：沿用 I39 參數包匯入的現行規則（`parameters.inc:310–315`：計數器自 0 起、跳過已用號、只增不減，依包內順序逐張取號）；本操作把閉包卡片依來源 id 升冪排成包內順序。
   - D32 規則、D33 綁定：沿用 `newid` 的 `WORLD_NEXT_ID`（`web_bridge.c:391–407,493–494`：目前最大號＋1、uint32 回繞、跳 0、找第一個空號）。
5. 版本：每條來源規則的被匯入版本依來源版本升冪重編 1…k（單一版本→1，與 `copy-rule` 一致）。
6. 改寫：binding.rule→新 {id,version}；slot `parameter.parameterId`→新卡片 id（fieldId 不變）；slot `spec.name`→依明選；卡片 AST 內卡片 id→新 id（沿用 `parameters.inc` 的 `parameter_remap_ast`）。
7. 指紋：規則與綁定以新內容重算；不採信來源指紋。
8. 建立順序：參數 → 規格 → 材料 → 規則 → 綁定；之後依 I38、I40、I34、容量（如規則版本總數 32）全量驗證。
9. 令牌綁定候選內容＋`expectedRevision`＋`sourceSceneSha256`；目標任何定義變更使之過期（canvas-pos 除外）。

#### (c) 畫布位置

匯入物件在候選中沒有 `canvas-pos`；確認後由既有自動排位（`nextCardPosition`）配置，`canvas-pos` 不新增 history（I14、REFERENCE-PROJECT「canvas-pos…不新增歷史」）。

### 2.3 交易與 undo 邊界

- 一筆 native 候選交易；confirm 經 `/api` 送 `definition-import-confirm <token>`，成功 = native 一個 history 步驟。下列共七處白名單（`app.js` 四處、`reference-workspace.js` 兩處、`project-store.js` 一處）都加入此指令；少一處則 IM17 或確認期間的保存守門不成立（F2）：
  - `app.js:546`：有 requestId 才有回執。沒有 requestId 則 IM17 無法查回執。
  - `app.js:532`：可編輯性守門（`assertEditable`）。
  - `app.js:555`：確認租約。未知回覆期間保留租約，只由同一 requestId 的回執解除，不重送。
  - `app.js:608`：成功且 history 有變時發出 `geometry-definition-changed`。既有監聽不改檔：`parameters.js:921`、`assembly-workspace.js:326`、`grid-system-workspace.js:1019`。
  - `reference-workspace.js:37`：`beginNativeOperation` 計入 `nativePending`，使 `assertSaveReady`（:1239）在確認進行中擋住保存。:1239 已有此條件，不另寫。
  - `reference-workspace.js:418–420`：`dirty()` 與 `notifySceneChange` 的指令清單。
  - `project-store.js:836,856`：history.observe。
- 一次 undo 移除全部匯入結果（含新建材料版本；共用材料不受影響）；redo 全回。
- 取消／預覽失敗／過期：零 World、附件、dirty、history 變化。
- 回覆未知時不重送、不推定結果，以回執為準（F3）。回執為成功則依「一筆 native 候選交易」那一項（成功＝native 一個 history 步驟）記歷史並標 dirty；回執為失敗則 World 不變。
- 讀取與預覽期間，前端 context／revision 變了即丟棄晚到結果（沿用現行 contextToken 守門）。

### 2.4 能力宣告

- 執行器操作能力 `definition-import/1`：native capabilities 清單回報；不寫入專案 `requiredCapabilities`，`validateProjectCapabilities` 不收它（避免任何專案「需要」它）。
- 來源閉包所需能力（`parameters/1`、`engineering-spec/1`、`assembly-rule-authoring/1`）目標執行器必須全有，否則 UNSUPPORTED。
- 根或閉包出現首版外型別→UNSUPPORTED，診斷列出型別與來源 id（例如「組構實例 7：首版不支援」）。

### 2.5 使用流程

「檔案 → 從其他專案匯入定義…」（GEO-219：放進既有檔案選單，不加工具列）→ 選 `.gcanvas` → 清單：規則（id／版本／名稱）、綁定（id／名稱／規則）勾選 → 自動展開閉包（唯讀列出參數卡、規格、材料）→ 撞名區塊每列一個二選一（新名稱輸入框／改用目前專案同名規格）→「預覽匯入」→ 對應表＋各槽位有效值 →「確認匯入」→ 新卡片自動排位，狀態列「已匯入 N 項，可復原」。

### 2.6 驗收測試清單（具體例）

夾具（native＋Node，數值固定）：
- 目標 T：規則 1@1「目標框架」；綁定 2（規則 1@1，全 literal）；參數卡 id {0, 3}；規格 `柱寬=30`；材料 `t-uuid-A@1` timber 27×33（指紋 fA）。
- 來源 S：規則 1@1「S框架」、1@2「S框架改」、5@1「其他」；卡片 1「S卡」欄 1 W=27 mm；卡片 2「S衍生」欄 1 `= 卡1.欄1 + 6 mm`；規格 `柱寬=27`、`梁深=120`；材料 `t-uuid-A@1`（同內容 fA）、`t-uuid-B@1` timber 45×90；綁定 1：規則 1@2；槽 1 A＝param(2,1)、B＝spec 柱寬；槽 2 A＝material A@1.A、B＝material B@1.B。

| ID | 操作 | 必須觀察到 |
|---|---|---|
| IM01 | 根只選綁定 1（不另選其規則版本）；柱寬選「新名稱 `柱寬-匯入`」；確認 | 規則 1@1 指紋不變；新規則 2@1（內容＝S 1@2，id 2、version 1，指紋＝新內容 SHA-256）；綁定 2 不變；新綁定 3（rule {2,1}；槽 1 A＝param(2,1)、B＝spec 柱寬-匯入；槽 2 A＝A@1、B＝B@1）；卡片 1＝S卡（欄 id 1）、卡片 2＝S衍生（AST 指向 (1,1)）——卡片依 I39 規則自 0 起取第一個空號（目標 {0,3} → 1、2）；規格 `柱寬=30` 不變、新 `柱寬-匯入=27`；材料 A@1 僅一份、新 B@1；來源規則 5@1、1@1 與規格 梁深 不在閉包、不匯入；綁定 3 有效值：槽 1 A=33、B=27，槽 2 A=27、B=90；history 恰一步 |
| IM02 | 同 IM01 但柱寬選「改用目前專案」 | 不建新規格；綁定 3 槽 1 B＝spec 柱寬，有效值 30；預覽列 27→30 |
| IM03 | 未對柱寬作明選就預覽 | `valid:false`，診斷列「柱寬」；不可確認；零變化 |
| IM04 | 目標已有 `t-uuid-B@1` 但為 45×95 | 整包拒，列 `t-uuid-B@1`；零變化 |
| IM04a | 同 IM01；S 與 T 的 `t-uuid-A@1` 穩定身分／版本相同，均為 timber 27×33、指紋 fA | A@1 共用，仍恰一份；新綁定槽 2 A 引用既有 A@1；不得另建 A@1 或改其資料；其餘結果同 IM01 |
| IM04b | 同 IM01，但 S 的 `t-uuid-B@1` 改為 timber 27×33；除穩定 id 外材料資料與 T 的 A@1 全同；T 尚無 B@1 | A@1 與 B@1 保留兩個不同穩定身分，各恰一份；新綁定槽 2 A 引用 A@1、B 引用 B@1，有效值 A=27、B=33；不得因資料相同把 B 引用改為 A |
| IM04c | 同 IM01，但 S 的 `t-uuid-A@1` 改為 timber 27×34，依法重算指紋且不等於 T 的 fA；穩定身分／版本仍相同 | 整包拒，診斷指名 `t-uuid-A@1`；完整 T、全部附件及 history／redo 逐字不變；不新增任何閉包物件、不覆寫材料、不另立版本 |
| IM05 | IM01 後再匯入同一綁定；閉包內規格「柱寬」再次撞名，明選新名稱時「柱寬-匯入」已被使用而必須另取（例如「柱寬-匯入2」） | 新規則 3@1、綁定 4、卡片 4、5（目標 {0,1,2,3} → 4、5）；與第一次副本互不引用；材料仍各一份；以「柱寬-匯入」為新名稱時整批拒絕，`conflicts` 碼 `IMPORT_RENAME_COLLISION`（與目標既有規格同名） |
| IM06 | 目標規則 id {1, 4294967295} | 新規則 id＝2（回繞跳 0、1 已用） |
| IM07 | 預覽後在目標改 `柱寬` 為 31 | 確認拒（過期），需重預覽；零變化 |
| IM08 | IM01 確認後 undo／redo | undo：規則 2、綁定 3、卡片 1、2、規格 柱寬-匯入、材料 B@1 全消失，T 原物件逐欄不變；redo 全回、id 相同 |
| IM09 | 根＝規則 1@1 與 1@2 | 新規則 2@1、2@2（依來源版本升冪） |
| IM10 | 來源綁定槽 2 為 null（未完成） | 匯入為未完成綁定（合法） |
| IM11 | 來源含組構實例且使用者嘗試選它；或來源場景需 `section-profile/1` 而 native 不支援 | 前者 UI 不提供勾選、API 直接送也回 UNSUPPORTED；後者讀取即拒 |
| IM12 | 執行器未宣告 `definition-import/1` | 入口停用並說明；API 回 UNSUPPORTED |
| IM13 | IM01 後保存→重開 | 匯入物件 id、版本、指紋與引用不變（I41 重開保留） |
| IM14 | 目標是空專案，根只選綁定 1（不另選其規則版本） | 新規則 1@1、綁定 1（`WORLD_NEXT_ID` 空 World 從 1 起）、卡片 0、1（I39 規則自 0 起）；同一套流程 |
| IM15 | 取消預覽、來源讀取中切換專案 | 零變化；晚到結果被丟棄 |
| IM16a（S2、F11） | 另一來源 S2：規格 `柱寬=27`、`柱寬2=40`，綁定 9 的槽 1 B＝spec 柱寬、槽 2 B＝spec 柱寬2；目標 T2：規格 `柱寬=30`、`柱寬2=35`（兩個都撞名）；根＝綁定 9。把「柱寬」改名為「柱寬2」，「柱寬2」選改用目前專案 | 整批拒絕：預覽 `valid:false`、無令牌、`conflicts` 含 `IMPORT_RENAME_COLLISION`，診斷指出新名「柱寬2」與目標既有規格同名；零 World、附件、dirty、history 變化 |
| IM16b（F11） | 同 IM16a 的 S2 與 T2。把「柱寬」與「柱寬2」都改名為「柱寬-新」 | 整批拒絕，碼同上；診斷指出來源名稱「柱寬」「柱寬2」的新名相同；不忽略其一、不取先者、不建立任何一條 `柱寬-新`；零變化 |
| IM16c | 同 IM16a 的 S2 與 T2。分別改為「柱寬-S2」與「柱寬2-S2」 | 通過；兩槽有效值各為 27、40；T2 既有的 柱寬=30、柱寬2=35 不變 |
| IM16d（S2） | 同 S2，但目標用 T（沒有 `柱寬2`）。把「柱寬」改名為「柱寬2」（`柱寬2` 在目標無同名，將以原名建立） | 整批拒絕，碼同上；診斷指出新名與本次閉包內的「柱寬2」相同 |
| IM16e（r4.1，§2.2(b) 規則 3 (v)） | 同 IM16d 的 S2 與目標 T（T 沒有 `柱寬2`）。`names`：「柱寬」＝`{mode:"map-existing"}`（合法），另送「柱寬2」＝`{mode:"rename", name:"柱寬2-新"}`（`柱寬2` 在目標無同名，將以原名建立，不需改名）；另測「柱寬2」的 `mode` 為 `map-existing` 的同案 | 兩案都整批拒絕：預覽 `valid:false`、無令牌、`conflicts` 含 `IMPORT_RENAME_UNNEEDED`，診斷指出鍵「柱寬2」目標無同名；不忽略該鍵、不當作預先改名（不會建立 `柱寬2-新`）；「柱寬」的合法選擇不使整批放行；零 World、附件、dirty、history 變化。去掉「柱寬2」這個鍵後同一請求通過 |
| IM16f（r4.1，§2.2(b) 規則 3 (v)） | 夾具同 IM01（S 另有規格 `梁深`，但不在根＝綁定 1 的閉包內）。`names`：「柱寬」＝`{mode:"rename", name:"柱寬-匯入"}`（合法），另送 (甲)「梁深」＝`{mode:"rename", name:"梁深-匯入"}`（來源有、不在閉包內）；(乙)「不存在的規格」＝`{mode:"map-existing"}`（來源與目標都沒有這個名稱） | 甲、乙兩案都整批拒絕：預覽 `valid:false`、無令牌、`conflicts` 含 `IMPORT_RENAME_UNNEEDED`，診斷各指出鍵「梁深」「不存在的規格」，並分別註明不在閉包內、不存在；零變化；各去掉該鍵後同一請求（即 IM01）照常通過 |
| IM17（S7、F3） | IM01 的 confirm 經 `/api` 送出後丟失回覆 | 以同一 requestId 查回執得到結果；不重送、不推定結果。回執為成功則 history.observe 恰記一步，`notifySceneChange` 與 `dirty()` 各觸發一次，且 :532、:546、:555、:608、rw:37 都曾套用此指令；回執為失敗則 World 不變。回執回來前不得把結果當成未提交或已提交 |

### 2.7 受影響檔案

| 檔案 | 變更 |
|---|---|
| `geometry-core/definition_import.inc`（新） | 隔離讀取、閉包、分類、配號、改寫、候選建立、預覽 JSON |
| `geometry-core/assembly.inc`、`parameters.inc`、`engineering.inc` | 抽出可重用的 publish／put-binding／parameter remap／material publish 入口（不改既有語意） |
| `current_geometry.c` | include；能力清單加 `definition-import/1`；history 一步 |
| `geometry-web/web_bridge.c`、`geometry-web/definition_import_bridge.inc`（新） | 四個 bridge 指令 |
| `geometry-web/serve.py` | `/definition-import/{read,preview}`（REST file_request，server-owned 暫存檔、大小上限）；confirm／cancel 不開 REST，走既有 `/api` |
| `geometry-web/reference-workspace.js` | `:37` 的 `nativePending` 白名單，以及 `:418–420` 的 `dirty()`／`notifySceneChange` 白名單，加入 `definition-import-confirm` |
| `geometry-web/app.js` | 必改。`:532` 可編輯性、`:546` requestId、`:555` 確認租約、`:608` `geometry-definition-changed` 加入 `definition-import-confirm`（共七處中的四處；另兩處在 `reference-workspace.js` 列、一處在 `project-store.js` 列）。監聽端 `parameters.js:921`、`assembly-workspace.js:326`、`grid-system-workspace.js:1019` 不改 |
| `geometry-web/definition-import.js`（新） | 選檔、`unpack`、選根、撞名明選、預覽、確認、自動排位 |
| `geometry-web/project-store.js` | 匯出唯讀 `readForImport(bytes)`；history observe 加 `definition-import-confirm` |
| `geometry-web/index.html` | 檔案選單入口一項的標記（r4.1 更正：現行同類入口 `btnOpenProject` 的標記在 `index.html:65`，點擊接線在 `reference-workspace.js:1873–1887`，均 @ a7bff8f）。`project-ui.js` 是專案資訊面板（`projectInfoButton` 等），與檔案選單入口無關，不在改動清單。#87 PR 不碰 `index.html`，只由匯入 PR 改，所以不構成 §3 的重疊；入口接線若寫進 `reference-workspace.js:1873–1887` 的分派，屬 §3 已列的 `reference-workspace.js` 重疊，結論不變 |
| 文件 | `geometry-core/DEFINITION-IMPORT-CONTRACT.md`（新）、`ASSEMBLY-RULES-CONTRACT.md` 指路 |
| 測試 | `tests/test_definition_import.py`（native bridge）、`tests/test_definition_import.js`（前端純函式）、`geometry-web/definition_import_browser_test.js`（CDP，接入 `cdp_test.js`）、`tests/run_all.py` 登錄 |

### 2.8 不做的事

- 整份專案併入、World 幾何（D3/D4/D6/D7/網格/空間/柱樑）併入、D29/D30 網格來源與配置、D34 實例、D35–D37 斷面、空間模型、專案附件（房間、證據、規則案例、草稿）匯入——政策已定，能力另案。
- 新的分享包格式（沿用 `.gcanvas`）；跨專案即時連結或共用庫；來源追溯紀錄。
- 自動改名、依名稱或內容自動合併 World 局部定義、同名卡片合併。
- 匯入 D27 做法、D28 面套用（首版閉包不經過它們）。

---

## 3. 交付順序與 writer 協調

1. Axiom PR（K2b 條文；在 PF-0r／K1／K2a 之後）→ WSL 裁判全綠 → 合併。
2. #87 PR（§1）與匯入 PR（§2）在 `project-store.js`、`reference-workspace.js`、`tests/run_all.py` 三個檔重疊，不平行改同一檔，由同一整合 owner 處理，#87 PR 先合（F2）：
   - `project-store.js`：#87 改格式與能力；匯入改 history.observe 的指令清單。
   - `reference-workspace.js`：#87 改 grouped 白名單、候選 flush、mayLeave、readHostPage；匯入改 :37 的 `nativePending` 白名單與 :418–420 的指令清單。
   - `tests/run_all.py`：#87（§1.7 測試列）與匯入（§2.7 測試列）各登錄自己的測試；由同一整合 owner 依合併順序接續登錄，不各自平行改。
   - `app.js` 不計入兩 PR 的重疊：只由匯入 PR 改 :532、:546、:555、:608，#87 不改此檔。#87 的 `line confirm` 在 :532、:546、:608 被既有 `line ` 前綴涵蓋；:555 的確認租約 regex 目前只有 `assembly-confirm`、`section-profile-confirm`，不含 `line confirm`，#87 的房間路徑靠 roomLease 走 :532，不依賴 :555。此檔只有一個瀏覽器擁有者，匯入 PR 排在該擁有者之後（協調索引在分支 `docs/runbook-index-20261008` 的 `1127531`，未進 a7bff8f，合併時須重核是否仍有效）。
   順序固定為 #87 PR 先合；匯入 PR 在其上 rebase 後才改上述三個重疊檔。其餘檔案不重疊，可並行開發。
3. 格式號 `⟨K2b-F⟩` 與 K2a 的格式號依合併先後配發；能力名寫入前對全 repo `git grep` 確認未用。

---

## 4. 自檢：與既有條文的介面核對、仍推不出唯一行為之處

### 4.1 介面核對

| 介面 | 核對結果 |
|---|---|
| I32 能力 | 兩個新能力各自宣告；`room-candidate-drafts/1` 是編輯器能力（同 `grid-editor-draft/1` 慣例，`FEATURE-ATTACHMENTS.md:40`），不進場景／原生；`definition-import/1` 是操作能力，不進專案必要能力。I32 附加句已明寫類別。✔ |
| D25 交換包 | D25 definitions 內 id 屬快照命名空間（D⟨K2b-4⟩ 末句）；R30「另一專案僅憑交換包重建」是隔離重建，不是併入；把 D25 併入非空 World 屬 D⟨K2b-5⟩ 首版外 → UNSUPPORTED。D25 manifest 能力不受影響（沒有新 World 型別）。✔ |
| I36／I39／I41／I51 保存 | 候選草稿在編輯資料區（I36／I41 慣例）；匯入結果是普通定義，沿用既有保存；I39、I41 附加句把重配寫成條文。✔ |
| I8／I8a／undo | 零房：native＋附件一群組一步（與現行 `commitWithMetadata` 同構）；匯入：native 一步；暫停／flush／捨棄：一筆 local step；接受＋草稿更新同一步。I8a 預覽：零房沿用 #77 新建預覽（新 D3 不移動被引用者）；匯入依 I⟨K2b-5⟩ 必出預覽。✔ |
| core-only undo 回退 | 現行保留附件並把房間標 needs-reassociation（`project-store.js:862–888`）→ roomsPin 必不符 → 草稿過期；與 D⟨K2a-1⟩「草稿不阻擋 World」一致。✔ |
| 房間集合（Q37／D⟨K2b-2⟩） | 零房新增唯一 plane；ZR04 驗同頁唯一；接受去重沿用現行「同集合同 basis exact 相同」。✔ |
| D12／I14 | 匯入不帶畫布位置；確認後自動排位不新增 history、不使令牌過期。✔ |
| I34／A13 | 附加句限定只對 (a) 類；IM04 驗同 id／版本異內容拒。✔ |
| D19a 第 279 行 | ruleKey 屬 (c) 保留、來源 id 屬 (b) 重配；仍不新增跨專案永久身分。✔ |
| K2a D⟨K2a-1⟩／D⟨K2a-2⟩ | 候選草稿是 D⟨K2a-1⟩ 的一種；「過期仍可保存、重開、捨棄，不得預覽提交」出自 D⟨K2a-2⟩，I⟨K2b-3⟩ 比照另寫、不靠繼承；K2a 未採納時用備援句。✔ |

### 4.2 仍推不出唯一行為之處（交對抗審查重點看）

1. **草稿新鮮度與本分頁工作階段是兩件事（F6）**：草稿新鮮度只看領域指紋，寫在 I⟨K2b-3⟩／R⟨K2b-1⟩。本分頁工作階段是否有效看 candidateStamp（含 revision 與 undo 頂端，rw:148–150、rcw:150–155），只寫在 §1.3，不進公理，也不使用「工作階段」「重新蓋章」這兩個沒有 D 編號的詞去寫條文。工作階段已失效而領域指紋仍新鮮時，保存不寫入並給 PC18 的狀態列提示；重開後仍可依指紋恢復。分頁內戳記維持 #169，不放寬。
2. **指紋數值序列化**：依 ECMAScript 數字最短往返。只有前端計算時唯一；若日後 native 或其他語言要計算同一指紋，需另定數值編碼（目前條文未涵蓋）。
3. **D6b 新名稱的合法字元**：公理層 D6b 只寫「名稱唯一」，字元集由 DSL 文法與 native 決定；I⟨K2b-4⟩(d)「符合該型別宣告文法」指向非公理來源。
4. **兩套配號規則並存**（已核對，r1 定案）：D31 卡片沿用 I39 參數包匯入的「自 0 起第一個空號」（`parameters.inc:310–315`），D32／D33 沿用 `newid` 的「最大號＋1、回繞」（`web_bridge.c:391–407`）。R⟨K2b-3⟩ 已逐型別指明，行為唯一；但同一專案內「新建卡片走 newid（max＋1）」與「匯入卡片走最小空號」兩種規則並存是既有現況，不是本案造成，審查可能要求統一。
5. **D⟨K2b-2⟩ 只寫語意**：`source-rooms/2` 的 legacyHistory、`/3` 的 display 與容量（256 planes、10,000 rooms）仍只在 app 契約，條文以「依 source-rooms 契約」指路，沒有 D 編號可追溯。
6. **圖頁錨點的身分證據**：圖頁錨點以 (boundaryId, pageId, pagePin) 判新鮮。pageId 是 uuid、pagePin 只證明內容相同；若 D3 刪除後同號重建且同 uuid 圖頁經 undo 回來，會判新鮮。這不是原生沿革證明（與 Q37「沿革未知需明選」有張力）；目前靠「恢復清 reviewed＋接受走原生預覽」兜底。
7. **D32 版本重編**：依 `copy-rule` 先例重編 1…k，代價是失去「來源 v2」的對照；預覽有對應表，但匯入後物件本身不記來源版本（首版不存來源追溯）。
8. **材料 `archived` 旗標**：新建者未封存、共用者沿用目標狀態——寫在提案 §2.2(b)2，未寫進條文（屬專案狀態，非內容）。
9. **分析器版本漂移**：只加註不過期；若新版改了列鍵正規化，「以相同設定重新分析」得到的新 run 與舊列不可對照——已規定不移植，行為唯一但使用者會看到兩套列鍵。
10. **格式號**：`⟨K2b-F⟩` 依合併順序配發，公理不含號碼；在兩個 PR 都合併前，兩份文件的號碼是暫定。
11. **I⟨K2b-1⟩ 狀態轉換的覆蓋面**（r3 依 F8：身分無法確認時，全部房間轉為需重新關聯。對齊未配對 confirm 的 `project-store.js:901–905`，以及 `unknownHistory` 的 `source-plane.js:222–224`）：配對到已記錄預覽的 `line confirm` 仍逐一標記（`:894–900`）；能對到單一 D3 的其他變更仍只把該房標為需複核。只有完全不經 confirm 直接重宣告房間 D3 的路徑（若存在）會讓已核對房間留著舊指紋，直到保存時 `validateNativePins` 拒絕。本提案未逐一核對所有 D3 修改入口；條文寫的是應然，實作 PR 須以測試證明所有入口都經 confirm（或補掛鉤）。
12. **零房「同頁已有平面」只拒絕**：PR157 §10 允許「明選選用」，首版不提供；這是範圍取捨，不是推不出，但使用者若有兩面各掛同頁不同基準的 legacy 圖頁，第二面只能先被拒、再從既有共享來源走。
13. **`names` 鍵指到目標無同名、閉包外或不存在的規格（r4 新增；r4.1 已裁決，暫定依 2026-10-09 授權 L）**：整批拒絕，碼 `IMPORT_RENAME_UNNEEDED`，呈現同 `IMPORT_RENAME_COLLISION`（預覽 `valid:false`、不發令牌、碼放進 `conflicts`、零變化）；不忽略該鍵、不視為預先改名。已寫入 §2.2(b) 規則 3 第 (v) 項、AXIOM-DIFF I⟨K2b-4⟩(d)、IM16e／IM16f、decisions R4-11。理由與規則 3 其他拒絕同一原則：使用者送出的明選不得靜默沒生效，也不替使用者猜意圖。若對抗審查認為忽略比拒絕對呼叫端友善，須同時改 IM16e／IM16f、AXIOM-DIFF I⟨K2b-4⟩(d) 與 R4-11。
