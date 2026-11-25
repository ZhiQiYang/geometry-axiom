# R09b D1 v2：無狀態來源比較與候選建構

規範來源是 `公理層.md` D59–D67、I70–I77、R56–R63。本文件是部分實作契約，
不修改條文，也不宣稱已提供一般 App 的重新關聯。它取代 issue #44
7169386952／7170683006 的 D1 Session、確認令牌、第二套 undo/redo 與獨立持久格式設計。
前一版 T/P 尚未採入；套用本版不得再疊加前版。

## 1. 本片的邊界與信任來源

`source_reassociation.py` 是 H 層計算 helper，沿用既有 `model_update.prepare_update`、
`space_modeling.replay_stored`、真原生 `source-inspect-file` 與隔離 `dump-deidentified`。
不另寫幾何 producer、不改既有模型更新入口，也不宣告交換執行器已完整支援
`source-reassociation/1`。H 是責任分工的推論：D65 是專案使用關係，D66 是宿主資料，
不屬 World 幾何定義。SSOT 分層索引尚未逐一列入新增條號，該文字缺口只回報。

本片只接受 1–16 列普通 faces、固定列數及順序、無障礙物、未選角材或拉伸件。
來源場景也須通過原 F1b 的 `_scene` 能力限制；含 `assembly-*` 的整份場景仍回
`UNSUPPORTED`，即使該組構未被明選也不例外。本片不放寬該既有守門。
合法 surface-set 可以是開放面；是否需要封閉與必要輸出完整性仍由原 producer 判定。

| 能驗證 | 不能由此 helper 證明 |
|---|---|
| 傳入完整場景可被真原生讀取，已啟用帳通過 I70 | 場景屬於哪個正在開啟的 `.gcanvas` 專案 |
| 舊完整模型與來源快照能重播；新模型由單一新來源完整重建 | 當前 App 的 context、歷史 frame、revision 或執行世代 |
| 傳入候選與固定輸入及執行器版本逐值一致 | 使用者已看過差異或同意正式發布 |
| 這次計算的逐列標籤唯一、選擇明示，原 bytes 不被改動 | D65 正式 carrierId 已配號、刪後不重用、完整歷史已落帳 |

回傳 `authority` 明列 project 為 caller-asserted、history 為 unverified、
confirmation 為 false、carrierIds 為 caller-provisional。即使 caller 填了相同字串，
也不把它升格為獨立驗證。兩次 source bytes 相同不能證明期間沒有 undo/redo 或改後改回。

## 2. API 與過渡候選

所有函式都不修改輸入、World、正式模型、history 或 dirty。

- `capabilities()`：回報 helper 的部分範圍、容量，以及 commit/save/history 均不支援。
- `judge_roots(identity, live, same_project=True)`：純 R57 判斷。前提是同一份已通過
  I70 的完整來源檢查圖；本身不是圖的正式驗證器。只處理普通 placement/boundary 根。
- `inspect(record_raw, source_scene, project_id=..., record_project_id=..., ...)`：
  以真原生驗證前提後比較。`record_raw` 是完整舊模型 UTF-8 bytes；不知道其歸屬時
  `record_project_id=None`，舊引用如實為 unknown。沒有自動提案收據，`proposals=[]`。
- `prepare_candidate(record_raw, source_scene, selection, project_id=..., carrier_ids=..., ...)`：
  產生完整但未生效的候選。每列 `selection` 必須明示 carrierId、placement_id、
  orientation、purpose；`carrier_ids` 是 caller 提供的暫態標籤，必須唯一且逐列對上。
  不自動拿 placement id、陣列索引或雜湊當正式 carrierId。
- `validate_candidate(candidate, record_raw, source_scene, ...)`：以完整外部輸入重新建構，
  比對整個候選，不只比雜湊或 `verified` 旗標。成功僅表示可重播，不能作為發布權限。

`geometry-reassociation-draft/2` 是計算輸出，不是 I77 完整專案保存格式，
`candidateNotSaveable:true`、`committed:false` 不可省略或改成有效收據。
它保存原始 `beforeRaw`、完整 source witness、當次 comparison、新模型、逐列 currentReferences、
真原生前後 frame，以及實際執行器版本。`requiredCapabilities` 只標示日後使用這些新資料
需要的能力，不能讓舊 `.gcanvas` writer 自動接受這個 draft。
JSON 複製後仍能完整重驗是序列化一致性；不等於 `.gcanvas` 冷開或正式收據防剝除已驗收。

## 3. 五態、內容及明選結果

依 R57 順序取第一個成立者；讀取、I70、容量及能力錯誤在分類前作操作失敗。

| 狀態 | 條件 | 本片能做的計算 |
|---|---|---|
| unknown | 歸屬未知或不同、舊引用無記號、目前帳未啟用 | 保留未知；同案或歷史歸屬未知可明選候選，已知跨專案匯入不支援 |
| conflict | 舊記號出現在另一 typed key | 保留衝突診斷；合法 World 上可以人工明選新候選，沒有自動改指 |
| absent | 原鍵目前不受身分帳涵蓋 | 明選可用目標；固定列數下沒有合法目標就整筆拒絕 |
| replaced | 原鍵受涵蓋但記號不同 | 即使幾何相等也維持 replaced；明選後另建新引用 |
| continuous | 專案、typed key、記號相符 | 可以比較內容、沿原目標完整更新；不把內容相等當身分證明 |

定義與有效值差異各列 `definitionChanged`、`valueChanged`，不混入身分結論。
R57 的 typed key 不允許用同號 boundary 代替 placement；一般 oracle 另含 column/beam、
parameter-field 與 owned timber，不把模型 roots helper 冒稱全部型別的執行器。

本片新增功能只建候選，沒有正式「確認」。其工程選擇固定如下：

1. 檢視、未修改保存、全 continuous 且目標與完整模型未變，不升版、不新增資料。
   相等幾何的 unknown/replaced 人工新選擇仍需保留未知或重建足跡，候選可有資料變更；
   真正遷移要等宿主的首次明示確認新功能（I77(b)）。舊 F1b 不因狀態名稱自動升版。
2. 新 helper 的 continuous 列改指另一面回 `UNSUPPORTED`，留到 carrier-edit 片；
   這是新 API 的窄範圍，不禁止現行 F1b 已有的明選改面。
3. 新模型的 sourceIdentity 與其當前 input.uses 逐列相符；舊完整紀錄與舊判定存在
   beforeRaw/comparison。兩者不是兩份可獨立修改的現行綁定。不能在改指後讓新模型
   的 current roots 繼續指向舊 typed key；現有讀取器會拒絕。
4. 若日後已確認新引用，舊足跡在原 World 回來後變 continuous 也只供審查；
   current 仍是新引用。可以再明選回原目標，不能自動改回。

完整宿主規格另判斷「相同未知引用已有同一來源的有效人工決定」時，再次原樣確認是
no-op。D1 不讀持久收據，不能由這次的 unknown 候選推斷是否已有該決定；
其 `changed` 不是正式 history 計數，交接時不可直接當成提交開關。

同一模型的每一列都要有合法選擇，不能略過 conflict 或失敗列更新其餘列。
允許不同模型各自使用同一面；同模型不重複 placement 依現行 F1b 守門，
不錯引只適用 model-carrier-edit/1 的 I76(a) 來宣稱本片已有可變載體。

orientation/purpose 必須明示且保持原值，這是 F1b producer 的切片範圍。
預覽 frame 的 origin/u/v/n 都來自真 model-base；新 frame 改變時呈現實值，
不偷翻 orientation。若需求必須更換相對朝向或用途，本片明確拒絕，不能偷偷猜。

## 4. 容量、原 bytes 與失敗原子性

| 項目 | 本片上限 |
|---|---:|
| 普通固定 faces | 1–16 列 |
| 舊模型原 bytes | 8 MiB，沿原 producer MAX_INPUT_BYTES |
| 單份來源場景 | 1 MiB，沿原 producer MAX_SCENE_BYTES |
| 完整 draft | 16 MiB |
| 單一暫態列標籤 | 128 UTF-8 bytes，非空且唯一 |
| caller 專案識別 | 256 UTF-8 bytes，非空 |

超限整筆拒絕；不截斷足跡、端點或來源，不改時限。D1 沒有持久 receipts 串，
前版「8 receipts」不再是有效契約。D2 須把正式容量與既有 manifest 8 MiB、64 模型、
方案及持久歷史合併預算，並讓使用者知道拒絕原因，不能靠丟掉舊證據續寫。
原 producer 仍對整份更新請求（舊模型、來源及明選清單的合計）施加 8 MiB 上限；
上表是各項必要上限，不保證每項都達上限時其組合仍可接受。

函式只接收值與 bytes，不開寫使用者檔案；native 使用暫存檔與隔離子程序。
舊 JSON 的縮排、鍵順序、尾端換行保留在 beforeRaw。既有 `.gcanvas` reader/writer
在此片完全不改，因此不把「函式零寫入」描述成已完成 `.gcanvas` 另存／冷開／復原驗收。
壞 JSON、I70 損壞或能力不足是 ModelError，合法的 unknown/absent/replaced 是比較結果。
原生 SNAPSHOT_UNCHECKED 沒有細分每種讀檔錯誤，不影響這個操作失敗與身分狀態的邊界。

## 5. 與現行 K3-44 流程的對接

現行一般入口為「檔案 → 3D 模型庫 → 修改模型 → 採用現行來源…」。
它已提供 absent/replaced/conflict 的人工改指，以及選用根的明確移除；必要 use 列不能移除。
`model-update-app.js` 顯示決定，`identity-ledger.js::previewAllowed` 接受 retarget/remove。
確認時 `confirmIdentity` 重建新根，`model-update.js` 寫回 sourceIdentity，
`reference-workspace.js::updateSpaceModel` 經既有唯一 history.changeModels 寫入。
這條現況沒有保存 R09b 要求的完整舊引用足跡，不能宣稱 D1 已修復它。

| 現況 | D1 v2 | 後續對接 |
|---|---|---|
| 已有明選改指／移除 | 保留原入口與所有 bytes | D4 保留操作可達性與原能力限制，將新功能批次接到新版完整候選 |
| 合法 World 的 conflict 可人工改指 | 新 helper 也能人工建候選；不自動提案 | 明列衝突與舊事實後一次確認，不能為本片方便把 App 入口禁止 |
| 確認覆寫 sourceIdentity | 不改既有確認路徑 | D2＋D3＋D4 在同一步保存新清單、new roots、不可改 old trail 與能力 |
| 正式 undo/redo 在宿主 | 不建立 Python Session | 使用同一條完整專案歷史；復原還原整份紀錄，不重新執行授權 |

正式 carrierId 要在第一次成功新功能提交與正式清單同一步建立；使用隨機有界列鍵，
維持該消費者存續分支的已用鍵集合、刪除 tombstone 及歷史前後像，檢查碰撞後才發布。
不能用 D1 的 caller 標籤作永久配號證明，也不能從陣列 index 追認過去列身分。
新格式必須有模型內結構性版本／anchor，讀取端與外層能力推導共同拒絕缺足跡或剝除能力；
只把旁側 receipt 刪掉後仍可冒充舊格式的設計不能交付為正式保存功能。

需求帳的既有 F1b L4 核對是 plan 路徑；faces、柱樑與角材的改指／移除仍待實機核對。
D1 不沿用那份 plan L4 為新 faces API 背書，也不改需求帳 R09b 列（由 PR #458 同步）。

## 6. Oracle、三方域與後續規格

`tests/oracles/r09b_source_reassociation.py` 不 import 產品，含狀態建構、獨立檢查與
小域事件序列掃描。通用規格包含建立、刪除、同鍵新存在期、異型別撞號、改名再回來、
啟用、整體取代、互動 clear、同專案分支、復原及重做。正式確認、世代過期、
原子歷史與列鍵分配是後片的可執行規格，不冒稱 D1 已具備這些能力。

三方逐值測試比較 oracle、新 Python judge_roots、現行 IdentityLedger.judgeRoots，
共同域限同專案的普通 placement/boundary 根、完整合法 active/inactive 圖。
比較完整回傳列與輸入零修改，不只比較五態字串。JS 自身不接 projectId，liveKey
也不處理 parameter-field 複合鍵；跨專案與其他型別另測 oracle/新 API，不偷改 JS 輸入造綠。

已知 main 範圍外差異：ordinary timber 刪除後，同數字 id 變成 assembly-owned/null，
原 pin 依 R57(3) 應 absent；現行 judgeRoots 對 node/null 回 unknown。
本輪以真原生場景重現並在交付附原件；不為三方一致而讓通用 oracle 跟著錯，亦不順手改 JS。

## 7. 切片次序、交集與 F4b

| 片 | 交付責任 | 層級／驗收界線 |
|---|---|---|
| D1 v2 | 真原生支援的無狀態比較、完整候選、重播驗證 | 作者補丁候選，沒有 PR，不是 L2/L3/L4 |
| D2 | 正式模型版本、carrier 清單、不可改足跡、能力及 .gcanvas／方案相容 | 必須真跑舊檔不升版、新檔完整冷開、剝除拒絕 |
| D3 | 宿主 owner/context/epoch/token、正式列鍵與單一歷史 | ABA、啟用後過期、取消零寫入、同候選不重送 |
| D4 | 接回既有 K3-44 App、全部差異、人工 conflict、保留移除路徑 | 真 Chrome、390/1400、undo/redo、另存冷開及 L4 操作 |
| D5 | 有正式驗證器的有限操作對照、其他消費者及證據改綁 | 不傳遞舊同意；依 R63 重置新目標核對狀態 |
| D6 | model-carrier-edit/1 增減重排及完整用途/方向編輯 | 列鍵穩定、非空、全模型原子、幾何完整性 |

D1 只有新增獨立模組、文件與測試／來源片段；後片的 model_update、space_modeling、
project-store、reference-workspace、model-update-app、serve 與其他包有交集，要在當時
main 重新核對，不先出待套用的連續後片。

R09b 的新引用不等於同一現場實物。F4b 仍需既定來源證明、使用者明示同件及撤回、
計量附件／完整性拒絕條件與 CSV／裁切／App 接線；I59 的單一計量 World 不改。
D1–D6 沒有 plan 模型角材根的產品片，F4b 該部分來源證明依 R09a 既有引用，
不能把普通 faces 候選說成已交付跨表示去重。

## 8. 正式量測與未驗項

新 suite 走 tests/suites.d 獨立片段，由 Native suite measurement 真量測後原樣採入。
pending-ci-census 或缺成本時，正式六片與 complete 的拒絕仍有效；不得手填計數或成本。
本片沒有 canvas 段；沒有 Chromium、一般 App、Windows 或 .gcanvas 冷開實跑宣稱。
ME/AE 依原工具重跑及採入，固定歷史帳本、架構衍生檔、閱讀器與既有 golden 都不改。
