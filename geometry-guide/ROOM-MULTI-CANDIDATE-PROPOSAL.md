# #87 同頁多房間候選：有限第一版提案

狀態：**proposal-only，待逐項採納；不是產品開工、規格採納或功能完成聲明。**

基準：`main 6562fa53d90de22b3e5492f2083199b26377a8c2`；議題與 PR 狀態查核於 2026-10-06 08:51–08:54 UTC。本文只新增此文件，不改公理、產品碼、既有規格或測試基準。文件或 proposal-only 草稿 PR 的發布只供審閱，不代表方案採納、產品開工、合併或部署授權。

## 1. 結論與授權邊界

建議第一版：在**已建立且已校準的 #77 共享來源頁**，一次本地搜尋提出最多 12 個暫時候選；在現有底圖工作區逐個選取、疊圖、修正、核對，再由 #77 原生交易建立獨立 Boundary。候選不預配原生 ID、不自動批量建房、不覆蓋目前房間。

**不需要新增幾何公理。** 候選是來源分析草稿，正式輸出仍滿足 D1 整數 mm、D3 純 2D Boundary、I2 正交／閉合／非自交與 I8／I8a 交易和影響確認。來源集合不是 D5 Space、D22 CompositeSpace 或 3D 父物件；共享 basis 不自動變形已確認幾何。

本文的範圍、資料欄位、容量、排序、失效、互動與驗收門檻是**具體建議**，尚未因「先做方案」獲採納。沒有公理 diff 要求使用者追認；若日後要求斜／弧牆、原生父子、basis 自動移動舊房或自動批量確認，須另案逐條提出差異，不能用本案開工。

### 第一版刻意收窄的入口

- 必須已有合法 `source-rooms` plane／collection，至少有一個有效關聯房間可進現有面內工作區。沒有時停在既有 #54／#77 流程，不將匯入時的預設矩形默認為已核對房間
- 從該來源同頁找下一批候選；原先房 A 的 native geometry、名稱、孔與 fixity 全部保留
- 不支援第一次匯入後「零正式房間 → 一鍵取得並連續接受全部房間」的全新入口。第 10 節有唯一替代方案，這是需決定的實質範圍差異
- 支援 PDF 向量優先及本地影像輔助；只分析一頁、一個使用者可見的來源 crop，不跨頁、不做整屋語意還原

## 2. 已有什麼，這次才新增什麼

| 範圍 | 主線／待整合事實 | #87 不得混稱的邊界 |
| --- | --- | --- |
| [#54 單房候選](https://github.com/ZhiQiYang/geometry-axiom/issues/54) | 主線已有向量／影像障礙解析、單種子連通區、分隔線、整數化偏差、逐邊核對與修正、Worker、單房替換／取消／保存路徑 | 已有單房功能不等於每項效率目標、私人實圖或手機驗收完成，也不是同頁自動多候選 |
| [PR153](https://github.com/ZhiQiYang/geometry-axiom/pull/153) | open draft，head `bef28643153194fe592534d088325b0e0ef68d52`；平移 pointer routing 修復及單房 closeout 證據待整合 | 本文未重跑其證據；原六組完整修正腳本沒有證明操作／時間減少，遠端 CI 問題仍應按該 PR 原報告處理 |
| [PR155](https://github.com/ZhiQiYang/geometry-axiom/pull/155) | open draft，head `9c96a49772f47b4036c487260d4b8ff123f4d1b8`；base 是 PR153，尺寸欄受控 Enter 待整合 | Enter 只套用尺寸，不自動核對、跳下一房或確認；實體 IME／手機仍未驗 |
| [#77 人工連續建房](https://github.com/ZhiQiYang/geometry-axiom/issues/77) | 本基準已有 `source-plane.js`、`room-collection.js`、`room-collection-workspace.js`，並有正式 `ReferenceWorkspace` 附件／lease／history／保存接線 | 舊 issue 與 `ISSUE77-HANDOFF.md` 的 foundation 未接線、prototype／skip 敘述是歷史，不能覆蓋目前碼；也不能反過來把目前碼存在說成本文已跑完整驗收 |
| [#87 本案](https://github.com/ZhiQiYang/geometry-axiom/issues/87) | 同一頁一次取得有界、多個獨立來源區域，維持暫時列表，逐個人工核對並接 #77 新建 | 沒有新 persistent candidate schema，沒有第二套 PDF app／辨識引擎，也沒有產品實作 |

現行 #54 的 `stamp/current` 綁定 host boundary、incarnation、原外環指紋；其 Confirm 意圖是**替換該面的外環**。現行 `app.js` 對共享房間顯示 #77 面板並隱藏 #54 面板，`feCommitDraft` 又優先路由 room intent。因此不能單純在 #54 加一個陣列，或同時令兩個 owner 認為自己持有 `fe.draft`，便宣稱安全完成 B→C。

## 3. 優先方案的完整使用流程

1. 在已校準共享底圖的「同來源房間」區，把現有「新增房間」改成同一個新增控制：選「人工描繪」或「取得同頁候選」。既有明選編輯與人工入口保留
2. 「取得同頁候選」預設使用整個來源頁；可先明確框選較小的來源範圍。畫面標出實際分析 crop，禁止拿目前螢幕可視區或既有房 A 外環當隱藏裁切
3. 本地取得後顯示「找到 N 個可核對區域」，每列有暫時編號、方法與警告。未選任何列前不能確認。畫布只顯示選中候選的完整外環及其他候選的淡色編號輪廓
4. 明選一列後，載入唯一 `fe.draft` 及既有尺寸／頂點編輯器。其他列保存自己的 session 修正資料；切列前先將目前草稿回存到該列，禁止借用另一列的 reviewed 或邊號
5. 核對凹口、門洞、內緣、連通、每邊尺寸和整數化偏差；任何修正清除該候選 reviewed，保留人工入值與來源推估的區別
6. 「接受為新房間」只處理所選列：明填名稱 → #77 native preview → 原有影響確認 → 確認同一 token → 原子 native＋metadata commit。沒有「全選接受」
7. 成功後該列標「已建立」，既有 A 與其餘已接受房間保持原樣；回到同一來源列表，**不自動選下一列、不自動重跑辨識**。尚未接受的列表按第 6 節重新核對來源；若核對失敗則全部過期
8. 排除一列只改 session 狀態，可按該列「恢復候選」；它不是專案 undo，也不删除任何房間。中途保存可明選「暫停候選並保存已接受房間」，保留本分頁 session 的修正，之後明選恢復；「放棄剩餘候選」是另一個獨立選擇。兩者都不把未接受候選寫入檔案，安全轉換見第 8 節

### UI 減項（供獲准開工後寫入 BACKLOG）

- 合併既有「新增房間」入口為單一方式控制，不另加常駐工具列、精靈或第二個來源工作區
- 多候選模式只顯示一份尺寸／頂點／核對表單與一組確認／取消；列表內不複製每房編輯器
- 以新建意圖與列表狀態取代該模式的「替換目前外環」及重複取得說明；普通單房替換流程的 DOM 和語意保留
- 警告按需展開；常駐操作說明不超過三塊。不在本次文件工作改 BACKLOG 或 DOM 契約

## 4. 最小分析方法：共用一次障礙解析與連通分量

### 4.1 輸入與座標

- 原始 asset 只讀，依現行 `sourceId = SHA-256(original bytes)` 引用；不複製 PDF bytes 至每個候選，不用檔名、URL、縮圖或螢幕 pixels 當來源身份
- PDF 沿本版 PDF.js `getViewport({scale:1})`，包括原頁旋轉／CropBox；圖片用原始像素座標。分析影像的縮放只用於障礙擷取，結果換回同一來源座標
- 輸入包含頁码、coordinateSpace、pageSize、明確 source crop、目前共享 calibration／alignment／basisRevision、線寬／最短線門檻、分析模式及人工分隔
- 人工分隔仍只是搜尋條件，沿既有水平／垂直明畫規則，不推斷牆體。更動分隔或門檻必須重新取得；不在既有結果偷偷閉合門洞
- 來源座標的浮點推估與正式整數 mm 分開。每列保留來源點、轉換後估值、整數候選及最大偏差；不先取整 source 點來合併房間

### 4.2 一次枚舉，不以密集 seed 重複解析

把 `room-outline.js:region()` 現有的座標壓縮網格／障礙 coverage 與外環走訪拆成共用內部 helper：單房仍從 seed 走同一 helper，多候選在**同一份** blocked grid 上逐一走訪所有未訪問 free component。每個 cell 最多訪問一次。原單房 API、門檻與失敗語意保持回歸，不複製第二個 region 實作。

1. PDF 模式重用 `pdfObstacles`；影像重用 `imageObstacles` 及既有渲染頁，不為每房重渲 PDF
2. 對每個 component 追蹤是否連到 crop 邊界、完整有序邊與全部 loop 關係；連到邊界者只計入排除原因，不產生可接受矩形
3. 完全封閉且合法的 component 提出外環；保留 L 形與每個凹入轉角。斜邊、角點分岔、無法閉合、整數化退化、過多頂點均明列拒絕，不回傳 bbox 當候選
4. 完整列舉後做來源座標的 loop 包含／相交檢查。嚴格位於另一候選內環中的封閉區域標「巢狀／障礙內部」，不列為另一房。這會保守排除疑似柱空腔、家具框等，也可能排除真正嵌套房間；可改用既有單房／人工流程明確處理
5. 有內部孤立障礙的外環保留「只取外環；未建立孔／柱」警告和內環位置疊圖。不自動建立或抹除 D3 孔；若使用者確認它是真正須扣除的孔，第一版轉回既有人工孔編輯流程，不能把只有外環的結果稱為完整淨面積
6. 門洞使相鄰兩房連通時，只得到一個連通候選且維持警告；不凭瓶頸、面積或門弧自動切成兩房。使用者加明確分隔後整批重取
7. 向量路徑無可用候選或不支援時，可整批 fallback 至影像並列出原因。已取消／失效不可觸發 fallback；向量成功但有不足時不混補 raster 候選，需明選影像重取，避免兩套結果互相疊加

全部仍是**可核對區域**，不是可靠的房間分類。文字、尺寸線或家具若恰好形成封閉輪廓仍可能成為候選；明示方法與限制，不顯示未校準的「準確率」。

### 4.3 排序、去重與相互衝突

- 同一 run 不用面積取最大房；先列可編輯候選，再列阻擋／歧義摘要。可編輯列按来源座標 `minY → minX → 完整輪廓 canonical key` 固定排序，不隨 pan／zoom／修改尺寸跳號
- exact 去重使用完整有序輪廓：去除重複終點、只移除共線中間點，將起點循環位移和順／逆向做 canonical 比較；key 含 source fingerprint、人工分隔、完整 loop 結構。不排序所有頂點，不用 bbox／area／IoU 當同一房
- 近似輪廓只標「可能重複」，不自動刪除；不同凹口、薄牆相鄰房、同 bbox／area 都必須保留差異
- 候選互相穿越、含混包含，或人工修正後有正面積重疊，標成衝突組。不能同時當獨立房接受；要求修正／排除，或離開此候選流程用既有明確建模。接觸同一邊不當作面積重疊
- 對同來源、同 basis 且有效的既有 room，以原生 ordered loops 投回來源座標作 exact 比對；確定完全相同者標「已存在」，不再新建。基準需複核、身份未知或無法 exact 比對時只警告，不按 ID／名稱猜同一房
- 每次接受前重新檢查與**此刻**已接受房間的關係；禁止繞過剛建立的 A 再接受同一區域。此防重是候選 UX 範圍，沒有新增全 World 的房間不得重疊公理

## 5. 暫時資料契約，不新建保存格式

以下名稱是實作草案，不是已註冊 schema 或 capability：

```text
Session:
  sessionId, generation, projectId, contextToken, serviceSession
  planeId, collectionId, sourceFingerprint, requestFingerprint
  runId, status, complete, coverage, diagnostics, selectedCandidateId
  candidates[]

sourceFingerprint = SHA256(canonical[
  sourceId, page, coordinateSpace, pageSize,
  calibration, alignment, basisRevision, sourceCrop
])
requestFingerprint = SHA256(canonical[
  sourceFingerprint, method, thresholds, orderedBarriers, analyzerRevision
])

Candidate:
  candidateId = runId + componentKey
  componentKey, ordinal, method, sourcePoints, innerLoopDiagnostics
  estimatedMm, draftPointsMm, roundingDeviation, warnings, conflicts
  dimensions[], reviewed, status(pending|excluded|accepted|blocked)
  acceptedRef? = {roomId, boundaryId, associationPin}  // session evidence only
```

- `canonical` 固定欄位順序、拒非有限數值；來源 bytes 已有 hash，這裡只 hash 有界純資料。`analyzerRevision` 是分析方法版本，不是 native 能力
- `complete` 只表示在容量內完成指定 crop 的本方法走訪與列表輸出，不表示全頁房間已辨識；`coverage` 記錄 crop、方法、找到／排除／阻擋／列出數及降採樣。零候選表示「本方法未取得候選」，不能表示圖上沒有房間
- session 的 row ID 不預測 `roomId` 或 Boundary ID；正式 `roomId` 與 native `newid` 仍由既有 #77 接受時分配
- `fe.draft` 只有目前被選中的一列；其餘候選 session 記錄不是另一套可引用 geometry，也不可被 native、模型或附件引用
- `reviewed` 與 dimensions 只屬同一 candidateId＋draft revision；修正、換列舊 DOM 事件或重取不得把舊核對挪到新列
- SourcePlane 是唯一持久 basis。候選只保留只讀快照用於新鮮度核對；接受後 `RoomRecord` 仍只有 name／typed boundaryRef／acceptedBasisRevision／reviewState，沒有再存 polygon 或 calibration 副本
- 不把 method／warnings 硬塞進現行 strict `source-rooms` payload，也不偽造不適用的 legacy `reconstructionReviews`。第一版來源追溯沿現有 room＋plane 關係；若要求多候選辨識方法／警告跨次保存，另提附件差異，不在本案默加欄位

## 6. Worker、取消與失效：拒晚到是必要條件

### 6.1 只擁有自己的工作

每頁同時最多一個分析 Worker；新 run 先退休自己舊 job，再啟動新 job。request 和 response 攜 sessionId／generation／runId／兩種 fingerprint。主執行緒在 PDF operator list 回來、image decode 後、postMessage 前、收到結果、切入編輯和接受前各自核對，不只相信 Worker 回傳的值。

取消時先增加 generation、移除消費者／timer，再 terminate 自己 Worker；晚到 message／error／finally 不得清掉新 run、新選取或新草稿。不能 destroy 共用 PDF document、清來源 cache、關別人的 preview、重啟服務或重置專案來完成取消。背景中的 PDF 讀取若無可用取消接口，允許只讀工作自行結束，但其結果永不再消費。

### 6.2 失效矩陣

| 變更 | 候選行為 | 已接受房間 |
| --- | --- | --- |
| 換案／New／Open／清空、undo／redo、外部 context 或 service session 變化 | 退休整個 session 與 Worker；同號新案／同號 Boundary 不復活舊列 | 依原有專案交易／history 還原 |
| 換 source bytes／頁／crop／basis、重新校準／對位／旋轉、collection 移除或來源身份不明 | 全部失效，回到重新取得 | basis 變更只標 needs-review，native 不變 |
| 更改方法／門檻／人工分隔、明確重取 | 新 run；若有修正或已核對未接受列，先確認允許以新結果取代。舊資料保留至新結果可原子換入，來源條件已變則舊列停用 | 保留全部正式房間 |
| 切其他幾何工具／離開來源工作区 | 按既有退出保護先取消或明確放棄，再退休 session；拒絕離開則原狀 | 保留 |
| pan／zoom／fit／透明度／顯示鎖定、列表切列 | 不失效、不重算、不清修正 | 保留 |
| 明選暫停→保存→恢復同一 session | 依第 8 節保留有界修正快照；退休 active job／editor 所有權，恢復時重新驗來源與上下文並清 reviewed，不復活舊 token | 只保存已接受內容，不新增 native mutation／history |
| 任何非本 session 的模型／房間／附件修改 | 保守使 session 失效，不繼承舊確認 | 按既有交易處理 |
| 本 session 已知成功的一個新建交易 | 只允許下述受控延續；舊 Worker 不復活 | 新增該一房 |

**連續接受的唯一延續例外：**接線 owner 必須以本 session 的 operation identity 配對已知成功的 room transaction，核對同 project／service、sourceFingerprint 和 plane 完全不變、原 rooms／其他附件沒有非預期變化，新增的 room／boundary 與 preview pin 完全一致。只由成功回執換成新的 context stamp，剩餘每列 `reviewed=false`；使用新 #77 intent，不沿用舊 controller 或 native preview token。失敗、未知回覆、無法證明只發生這筆變更時全部失效。不能用「目前 context 看起來一樣」解鎖或整批略過守門。

## 7. 接受、容量與失敗保全

### 7.1 接受只能走新建路徑

新增一個薄的、明確命名的候選→#77 adapter：將所選且已核對的整數點交給 fresh `beginNew(collectionId)`／`prepare`／`confirm`，重用現行 native-ID 分配、candidate pin、preflightAttachment、lease、history-begin／confirm／history-end 和 receipt recovery。

- 接受新候選沒有 edit target，不能回落到 `emitBoundary(hostBid, ...)`；明選編輯既有房間仍走原 #77 入口，先離開候選 session
- adapter 在入口及 native preview／confirm 前確認 reviewed 與來源仍新鮮。不要只先開 room intent 便讓現行 `feCommitDraft` 的 room 分支繞過候選核對
- native 不接受的輪廓保留該候選作修正，reviewed 清除；影響確認取消只取消自己的 preview，原 A／B、dirty、history 留在操作前
- 每次正式接受是一筆 native＋room metadata 歷史；不預先新增空 room，不在 native 已提交後另用第二筆 metadata history「補記」
- unknown transport 保留既有 lease 和暫停編輯，沿原 requestId 查同一回執，不重送 create／confirm。恢復後先清自己的 editor／preview／drag，再解鎖；若不能證明 session 延續條件，清候選且保留已核實的正式結果

### 7.2 建議的有界上限

以下為第一版工程預算，均待採納及基準量測，不是新公理：

| 項目 | 第一版建議與超限結果 |
| --- | --- |
| 並行與时间 | 1 個 Worker；一次取得總期限 30 秒，包含準備階段的消費者 deadline。逾時取消，不在主執行緒改跑同步分析 |
| 來源擷取 | 沿用既有 PDF 200,000 ops／單 path 600,000 entries／12,000 boxes；image 4,000,000 pixels 與目前最大邊 1800 的來源降採樣提示 |
| 網格 | 沿用 150,000 compressed cells、2,000 fills、fill 頂點乘 cells 5,000,000 的上限；實際建置前算安全乘積，拒 overflow |
| 分量與輪廓 | 最多檢查 64 個封閉分量；總輪廓頂點 16,384；单候選最多 256 頂點，與目前候選修正界線一致 |
| 顯示列表 | 最多 12 個待核對候選，所有已接受／排除列也在同一 run 的有界數量內，不累加多批成無限列表 |
| 正式容量 | 仍由現有 room/attachment/manifest/native admission 決定；不得以「12 個候選」繞過 SourcePlane 的 256 planes/collections、10,000 rooms 或既有 bytes／lifecycle reserve |

若完整掃描後有 13–64 個候選，固定排序只交付前 12，顯示實際找到數及「本次只列 12，範圍未完整呈現，請縮小範圍」；不是「全頁完成」。候選上限只限制顯示，不能先取 12 就跳過全批包含／衝突檢查。超過分量／網格／總頂點／時間上限，整批失敗，不接收拓撲尚未檢查完的部分結果。

每次重取在暫存結果完成驗證後才替換舊列表。未改來源而新分析失敗，可保留原列表和修正並明示新嘗試失敗；來源已變的舊列表只可看過期說明、不能再接受。任何失敗不改 World、持久附件、dirty、history。已接受房間不因後續辨識失敗回滾。

## 8. 完整保存、重開與 undo 的精確承諾

本版的「完整保存」涵蓋**已接受房間與所有原有專案資料**，不包含未接受的 session 候選。

### 8.1 安全暫停可保留本 session 修正

**session-only 不等於保存正式成果前必須丟草稿。** 優先方案提供明確的 `active → parked → active` 轉換：暫停只是本分頁記憶體保全；關閉／重載／新 context 後續編則是另一個未採納的持久化要求。

1. active 候選仍讓既有 [assertSaveReady](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/reference-workspace.js#L1129) 拒絕直接保存。使用者明選「暫停候選並保存已接受房間」，不是程式收到 Save 就自動接受或丟棄候選
2. owner 先把選中列的 draftPointsMm、dimensions、未套用的尺寸／頂點輸入原字串、選列及排除狀態回存到同一份有界 session 快照；捕捉 generation、project/context、service、source/request fingerprints 與當前正式資料 stamp。快照先驗容量，超限或複製失敗就拒絕暫停並保留 active 輸入，不截斷、不清稿。最多保留這一份列表，沒有 IndexedDB／localStorage／manifest 寫入，也不新增正式 history／dirty
3. 若正在 native prepare／preview／confirm、room intent、history group、lease 或未知回覆，**不得暫停或保存**。要求先完成、明確取消自己的 preview／intent，或經原回執恢復至已知終態；不把 lease／token 搬入 parked、不代為確認、不為通過 gate 清掉旗標。取消步驟若失敗，保留 active 草稿並沿既有 recovery 阻擋
4. 只在無上述交易後退休自己 Worker／PDF 結果消費者、增加 generation，原子將 session 標 parked，清除自己的 `fe.draft`、preview、drag 和選中編輯器，釋放 active editor owner。此轉換必須按當前 stamp 重新核對；失敗時不進保存，保留可檢視的完整修正快照。其他校準／參數／工具草稿一律不清除
5. parked 沒有可提交幾何、active room intent、Worker 或 native token。另保留可見的 `hasParkedSession`／未存候選提示，與「正在操作」的 `hasWork` 分開；不能只在呼叫 Save 前把 `hasWork=false` 再立刻改回。只有完成真實生命週期轉換，才呼叫原保存入口，照常經過 `assertSaveReady`、`assertEditable`、history／lease／snapshot guards。其他 blocker 仍照常拒絕
6. 保存成功、使用者取消檔案選擇器或寫入失敗，都保留 parked 修正，不自動恢復編輯／重算。提示分開顯示「已接受成果的保存結果」與「另有未接受候選只留本分頁」；不能把暫停草稿標成已存入檔案
7. 「恢復候選」在保存已結束且所有編輯守門通過後，重新核對同 project/context/service、正式資料 stamp、來源與 basis。保存本身的 saved／downloaded／dirty 狀態切換不是幾何或來源變更，不作錯誤失效；其餘非預期 revision、history frame 或幾何／附件改動仍按第 6 節失效。成功以新 generation 重新取得單一 editor owner，恢復同列修正／輸入／排除狀態，清 reviewed 並要求重新核對，不恢復舊 Worker／preview token
8. parked 期間換案、undo／redo、改來源／basis 或其他非本 session 的實質修改仍使它不可恢復；過期快照可顯示原因，但不得當有效候選接受。使用者明確放棄才清快照。關閉／重載分頁或換案的離開提示須包含 parked 未存修正，即使正式專案剛保存、dirty=false；不能靠 dirty 單一旗標隱藏遺失風險。瀏覽器／OS 強制終止仍可能丟失本 session，這不是可攜保存保證

這是需實作與驗收的薄 owner 生命週期接線，不是現行產品已具備的暫停功能。若實作不能建立上述安全狀態，第一版只能另作明確取捨：保存前接受或放棄，會損失未接受修正，須重新取得使用者對該降級的同意；不能以 session-only 為理由默認降級。

### 8.2 檔案與 history 的承諾

- 安全暫停或明確放棄剩餘候選後，保存真 `.gcanvas`；同一原始 PDF／圖片依 source hash 保存一次，共用一份 plane basis，房 A/B 各有獨立 room ID 與 typed Boundary pin。暫停路徑不以丟掉未接受修正來換取保存成功
- 尊重現行 `project-store` 選格式，主線最高已有 `/13`；本案不分配新版、不回退 `/9` 或 `/10`、不剝既有 grid／evidence／model／source history 能力。無歷史的 `source-rooms/1` 與有歷史 `/2` 均原樣保存
- 重新開啟先驗原始 bytes/hash、頁／尺寸、來源閉包、native 最終 typed refs／pins 和共享 basis，成功才替換現案。未知 capability／schema、缺來源、壞 pin 仍拒絕且保留舊案
- 新瀏覽器 context 重開後，A/B 原生 ordered loops／holes／fixity／kind、room ID／名稱／refs／reviewState、唯一 basis、舊來源 records／歷史收據及其他附件相同；沒有待選候選或舊 Worker 復活
- 接受 B 後一次 undo 同時移除 B 的 native 及 room metadata，A、原圖與先前 basis 不變；redo 同時還原 B。同 session 剩餘候選在 undo／redo 時失效，不能依舊 ordinal 自動補建
- 排除／恢復／修正候選不新增專案 undo。保存包沿既有契約不攜帶跨次 undo 堆疊；不得宣稱重開後仍有關閉前的候選或完整復原歷史
- 真檔案寫入完成與「已產生下載」沿現有文案區分；`.scene` 仍只含 geometry，不能拿它代替完整來源保存

## 9. 落點、writer 重疊與实施順序

下表是**獲批准後**才可分配的改碼範圍；本次沒有改任何一項。

| 落點 | 最小變更 | 重疊／依賴 |
| --- | --- | --- |
| `geometry-web/room-outline.js`、`room-outline-worker.js` | 共用 grid／loops helper；保留單房 API，新增 batch request/result、容量與診斷 | 與 #54 演算法 owner 協調；不另寫第二辨識引擎 |
| `geometry-web/room-outline-workspace.js` | session 列表、選中唯一 draft、指紋／取消守門、安全 parked 快照／恢復；抽出可重用的尺寸核對 UI | PR155 的 guarded Enter 直接同檔；須以已整合最新 head 留住舊 DOM／IME／repeat 防護 |
| `geometry-web/room-collection-workspace.js` | 明確候選新建 adapter、成功延續回執、UI single-owner 交接 | #77 controller／lease owner 決定接口；不能自行繞 setFeatureAttachment 或 private context Maps |
| `geometry-web/app.js`、`reference-ui.js`、`reference-workspace.js` | 僅必需的面板、草稿路由、退出／save gate／導航接線 | PR153 pointer routing、已合 [PR151](https://github.com/ZhiQiYang/geometry-axiom/pull/151) 導航取消、[PR156](https://github.com/ZhiQiYang/geometry-axiom/pull/156) source ownership、[PR134](https://github.com/ZhiQiYang/geometry-axiom/pull/134) 規則 UI 有重疊；必須由共享入口單 writer 接線，本 worker 暫不碰 |
| `source-plane.js`、`room-collection.js`、`feature-attachments.js`、`project-store.js` | 優先方案預期不改保存 schema；使用現行 public adapter／validator | 原圖／basis 唯一性、capacity reserve、typed pins 及 ContextHistory 都重用；若發現必需新增接口由 owner 審查，不能暗擴保存契約 |
| `tests/test_room_outline*.js`、新多候選 Node／browser gate、合成夾具 | 加 batch 分量／取消／列表接受／ZIP／undo 反例；保留單房 oracle | PR153/155 測試與 `tests/run_all.py`／INTEGRATION-GATES 共用登錄；現有 floor／golden 不降、不以 skip 充 pass |
| BACKLOG／DOM-CONTRACT／ROOM-OUTLINE 操作說明 | 採納後記 UI 減項、batch session 邊界與新入口 | 與上述 PR 的文件 writer 排序；本 proposal 不預改既有規格 |

實施順序（未授權）：

1. 先由共享 owner 完成 PR153→PR155 整合安排並核對最新主線／file ownership；不要在舊 base 競寫其修復。已有單房 baseline 不必另重做一張 #54
2. 單獨落地 pure batch helper／Worker protocol 與合成拓撲、容量、cancel 測試，**不暴露產品入口**
3. 唯一 UI／history owner 接 session、來源 guard 和新建 adapter；先證明不替換 host A、無雙 owner、取消／未知回執保全，再開入口
4. 同一 frozen exact head 跑第 11 節；若改 `app.js`，依 AGENTS 跑完整 `cdp_test.js`，涉空間工作區才另跑 `space_model_test.js`。純 Node／VM 不能代替真 UI
5. 交 root review；PR、merge、部署與新範圍由另外授權決定。本次有限文件到此交付後即停止，不因未回覆無限重排

## 10. 唯一替代方案：首候選才建立共享來源

若第一版必須覆蓋「剛匯入校準，尚無 #77 collection」，可保留上述分析方法，在**首個人工接受**時，一筆交易同時建立 SourcePlane／collection／新 RoomRecord／新 native Boundary；沒有預先占位房間，也不綁定或覆蓋原預設矩形。

具體代價：

- 現行 `Controller.beginNew` 要求 collection 已存在，需增加 staged source-collection intent 及 admission，而非多加一顆按鈕
- 首交易須驗 source closure、legacy records／receipt 保全與是否採用已存在的唯一 source/page basis；同 source/page 已有不同 basis 必須明確選用或拒絕，不能建立第二 plane
- UI 必須清楚交代原描繪用面保留、首候選是另一 Boundary；若要刪原面，另外明選，不列自動清理
- 多出「首次來源 metadata＋native 同步失敗／未知回執／undo／重開」、「已有 source/page 碰撞」及有 records 舊頁的負例。会增加 source/history owner 的改動面，不能與共享入口修復平行競寫

此替代方案仍不需新幾何公理或 persistent candidate schema，但需要額外採納入口和首次交易行為。建議先選第 1 節的已有共享頁版本，將此擴充留後；不估算未经實作量測的工期。

## 11. 可測的驗收與證據表

**以下全部是未執行的產品驗收計畫，不是 pass。** 只用 repo 公開／可公開自製夾具；本文不取用私人 PDF、不猜設計稿、不把歷史合成結果當真圖結果。

| Gate | 輸入／操作 | 必須觀察到的結果 |
| --- | --- | --- |
| A1 向量與影像多房 | 同頁兩矩形；三房含 L 與局部凹口，另有文字、尺寸線、門弧 | 每個期望輪廓與完整 cyclic edge adjacency 符合獨立 oracle；內緣／凹口完整，不只比 area、bbox、頂點數；向量與 raster 各自報告 |
| A2 語意保守性 | 房內空心柱／家具框、內障礙、開門洞相鄰房、邊界外部 | 巢狀內部不成另一房；孔不自動建；連通者不自動拆；不閉合不產生 crop 矩形；人工分隔後才改分離結果 |
| A3 排序與去重 | 同輪廓不同起點／方向、同 bbox 同 area 不同凹口、重取／改尺寸、近似薄牆 | exact 重複只一列；非等價輪廓不丟；順序不被相機與編輯重排；近似／重疊須明示 |
| A4 座標 | PDF 原頁 90°、四種共享對位旋轉、裁切、pan／zoom／fit；raster 降採樣 | 獨立預期來源坐標與 native mm 對位；每個 deviation 可見；斜邊／退化不偷修；相機不讓結果失效 |
| A5 Worker races | 真 Worker 結果受控延遲；取得／decode／結果／接受各階段取消、重取、换頁／換案／basis 變更 | 舊結果和 finally 不動新 session／焦點／draft；零新增 native mutation、dirty、history；新 run 正常完成。合成晚投遞標 fault injection，不說成真 terminate 後必然晚投 |
| A6 接受與所有權 | 已有 A，選候選 B 修正核對，取消預覽／native 拒絕／正常確認／連按／再選 C | A 的完整 native 定義與來源不變；每次至多一個新 boundary；不能繞 reviewed；取消／拒絕仍可修正；不自動選或建立 C；舊 input 不能改新列 |
| A7 回執與失效 | 確认 native 真執行後丟 reply；第一次 recovery 不可用，再查原回執；其他 context 同號資料 | 不重送 mutation、不先解鎖；已知結果恢復一致；舊資料不能串新案。成功延續只在配對本交易且完整驗證時發生 |
| A8 容量 | 12／13／64／65 封閉分量；256／257 頂點；pixels／grid／fills／bytes 邊界；逾時 | 明示完整／不完整或整批拒絕，絕無假全頁完成；舊有效列表與修正可保全；持久原案不變，native admission 失敗不留半房 |
| A9 真保存與重開 | 接受 B/C，剩一已修正未接受列且有未套用輸入；直接 Save、明選暫停後 Save；另測 picker 取消／寫入失敗、同 session 恢復、preview／lease／history／未知結果時拒暫停；下載真 ZIP 後確認離開提示，再 dispose context，UI New→Open | 直接 gate 及其他 blocker 不被繞過；暫停／保存／恢復保留候選 points、原字串、dimensions、選列／排除狀態而清 reviewed，零額外 native／history；保存失敗不丟修正；原始 source bytes 只一份，A/B/C 的全部 native＋room＋basis 及舊附件 exact roundtrip；未接受候選不在 ZIP，不跨次復活；坏 bytes／pin／能力保全拒絕 |
| A10 undo／redo | 接受 B→一次 undo→redo；再改 basis、rename、unlink、native delete／同號重建；包含 parked session | native＋metadata 同步一步；其他房不被覆蓋；basis 只 needs-review；未知身份 needs-reassociation；active／parked 舊候選失效且明示，保存不靠丟持久資料成功；仍新鮮的未接受修正按 A9 暫停保全 |
| A11 桌面／窄屏 | 桌面及 390px：选列、疊圖、pan、局部修正、尺寸 Enter／click、核對、接受／排除、Save | 主要操作可見可達、触控目標至少 44px、無橫向溢出；右欄收合不清選取；焦點／鍵盤不跨列；沿 PR153/155 保留 pan／IME／repeat 行為 |
| A12 實體手機 | 真 iOS：雙指取景與選列衝突、螢幕鍵盤／組字、方向切換、返回取消、OS chooser、download／reopen | 獨立記裝置／OS／結果；未做即未驗。390px、DevTools 或合成 composition 不得替代 |
| A13 成本是否改善 | 人工／單房逐取／多候選三組，全部從同一公開圖、同一已校準共享來源＋已核對正式房 A、相同名稱／關聯／basis／視野／工具狀態開始；終點是同一組新增房間全部修正核對完成且正式獨立保存。另做首次匯入成本比較時使用下一段的共同起點 | 真實計數選取、修正、尺寸、排除、核對、新房命名／關聯、確認及同一保存終點的成本，報操作數與實測時間；暫停／恢復本身及恢復後 reviewed 清空造成的再次核對操作與時間都須計入，保留修正不等於完全無重工；單房路徑若需額外來源／新房接線，必須計入；失敗列入，不憑減少 seed 點擊即宣稱全流程變快 |

公開起點可用現有 `tests/fixtures/issue77-two-rooms.pdf`（600×400 source viewport，200 頁面單位校準為 4000 mm）、`tests/room_outline_fixture.js`、`geometry-web/docs/fixtures/issue54-public-rooms.pdf`。補三房、門洞與巢狀夾具用獨立生成器和人工寫定的 ordered-vertex oracle；不能從被測輸出生成預期值，不能硬編碼 fixture 座標進演算法。

A13 的主要比較只回答「已有共享來源與房 A 之後」的增量成本。若另宣稱首次匯入就省操作，三組必須從相同空專案開始，完整計入匯入／選頁／校準、完成並核對首房 A、[建立共享來源時的命名與明確關聯](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-collection-workspace.js#L239)、其後全部新增房間及同一保存終點；不能只報進入多候選按鈕後的成本，或將先建立 A／collection 當成免費 setup。第 10 節零房起步若未實作，就標該路徑未驗，不以估算扣掉前置成本。

證據需記 exact commit／runtime fingerprint／root、命令與 exit、pass/fail/skip、原始 JSON、無私圖截圖；每項標「pure／VM／真 native／真 browser／physical」。先跑基線再跑修改版本，修改最後一行後需重核 relevant gates，不挪用 PR153/155 原 SHA 的收據。

## 12. 真正需要決定的事項

1. **是否採納優先方案的第一版範圍？** 限已有 #77 共享來源頁，最多 12 個 session 候選，逐一人工接受；首次匯入無 collection 的流程留後。若必須首批支持零房起步，改選第 10 節並接受其首次交易／保存驗收增量
2. **是否接受 session-only 的保存邊界？** 已接受房間完整保存；未接受修正可按第 8 節安全暫停、保留在同一分頁 session，保存正式成果後再明選恢復，不必為保存而丟棄。關閉／重載後不能續編候選；若要求跨次保存，再另訂持久 schema／容量／能力與失效差異，本方案不能先做再補採納

排序細節與工程上限已有本提案的預設建議，可連同方案審閱；數值調校由非機密基準證據支持，不能暗中改成更強的房間正確性／完成性承諾。writer 順序由整合 owner 安排，無須把內部檔案衝突轉成使用者的設計工作。

## 13. 來源與本次實際核對

- [main 基準](https://github.com/ZhiQiYang/geometry-axiom/commit/6562fa53d90de22b3e5492f2083199b26377a8c2)
- [AGENTS](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/AGENTS.md)、[產品願景（非授權）](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-guide/PRODUCT-VISION.md)、[公理層](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/公理層.md)
- [單房演算法](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-outline.js)、[Worker](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-outline-worker.js)、[單房 workspace](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-outline-workspace.js)、[單房操作契約](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/docs/ROOM-OUTLINE.md)
- [共享 plane／strict schema](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/source-plane.js)、[room controller](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-collection.js)、[room workspace](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/room-collection-workspace.js)
- [正式來源／history adapter](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/reference-workspace.js)、[正式 store／格式](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/project-store.js)、[feature attachment validators](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/feature-attachments.js)、[app 路由](https://github.com/ZhiQiYang/geometry-axiom/blob/6562fa53d90de22b3e5492f2083199b26377a8c2/geometry-web/app.js)

本次已讀 #87／#54／#77 issue 與可用 comments、PR153/155 metadata 與改檔清單、適用根 AGENTS、願景、公理相關條文、BACKLOG、現行候選與共享來源程式、REFERENCE-PROJECT／REFERENCE-RECONSTRUCTION-PLAN／DOM-CONTRACT／FEATURE-ATTACHMENTS 及 #77 handoff。基準 tree 內未見另層適用 AGENTS。主要程式以 Git blob identity 核對本基準，沒有把其他 recovery candidate 的改動當 main。

`feedback_cli.py list` 在隔離的主線資料副本回「沒有未處理的回報」；此副本不含使用者本機 feedback，不能據此宣稱使用者沒有回報。本次只做文件、連結／範圍及來源核對，未啟動產品、未跑 Node／native／browser／手機驗收，也未讀取私人 PDF。
