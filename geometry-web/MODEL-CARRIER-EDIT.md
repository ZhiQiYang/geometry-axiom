# R09b D2／S1：可變普通載體的原生候選

本文件對應 issue #476 工作包 S。驗收依 `公理層.md` D59–D67、I70–I77、R57、R61–R63；
本文件是有限實作契約，不是新條文，也不修改 SSOT。工作包 S 把舊切片表中的可變載體
提前成 S1，再依序接正式保存、宿主交易與 App；不要把本包的 D2 名稱誤讀成舊表的保存片已實作。

固定補丁基底：PR #466 head `1121fb97ce0973958196227b0dcf3a2cf057df11`。
開工 main：`48d5f3887e8cb8d222307db62dbdea287fda8442`。
1121fb97 只採入證據；D1 產品仍是 463f0b53 的 v2。#44 的 v3 增量修正
（留言 7229472931、7229478779）已交付但不在此基底，不能稱 oracle 問題已在 PR 修好。

## 1. 先處理預審的四題

預審 #455／7171399755 §2 的四題含「收據容量滿」；該報告結尾摘要換成了
「舊足跡再 continuous」，後者另列於下，不能漏答容量題。

| 題目 | 判定與處理 |
|---|---|
| 哪種確認算使用新資料 | I77(b) 已定讀取、未修改保存、取消不遷移；但既有 F1b 的 unknown 明選確認何時改走新版協定，仍有兩種相容路由。列 Q1 選項；S1 沒有正式確認或保存，不依賴選擇。 |
| continuous 可否改指 | **定義推論**：D63 附加段、D65、I76(b)、R62 已允許載體明選改指，沒有只限非延續狀態。保留 carrierId，重新明選新目標的 orientation/purpose，顯示真 frame／法向。D1 的拒絕是其 API 範圍；S1 可計算此候選，不動舊 API。 |
| 收據達容量後怎麼辦 | **定義推論**：I77(e)、I76(d) 要求整筆拒絕；不能截斷端點、丟必要足跡或寫入半套。容量數字及無損編碼屬工程選擇。S1 無持久 receipts，只有下述固定輸入／候選上限；正式保存片須先驗整份專案預算。 |
| sourceIdentity 與旁側新引用何者為準 | **語意可推導、編碼未唯一**：D65 的正式清單是唯一現行權威，新引用對現行清單，舊事實不可改。持久欄位布局列 Q4 選項；S1 只給不可保存的幾何投影與分開的新引用，不採持久布局。 |

### 需使用者拍板的路由／保存選項

這兩題只約束後續正式保存及 App 片。S1 能獨立驗證，無須先選。

- **Q1-A（建議）**：保留既有 F1b 路由；只有明示使用載體編輯或「建立新來源關聯」的
  實際變更才走新協定。unknown 不會自行觸發升版，舊功能保持原義。代價是入口須清楚
  區分這次是更新既有快照，還是建立有完整足跡的新關聯。
- **Q1-B**：新版所有普通 faces 的實際確認都走新協定，一次建立完整列鍵與足跡；
  開檔、取消與真正無變更仍不遷移。路由較一致，但原 F1b 使用者的修改也會首次升版。
- **Q4-A（建議）**：新版 `sourceIdentity` 表示現行引用；完整舊紀錄、舊引用與比較時點
  放在版本化且必需的歷史區。模型內版本／anchor 與外層能力共同阻止刪足跡後冒充舊格式。
- **Q4-B**：凍結舊 `sourceIdentity` 為明確標示的歷史資料，新版 `currentReferences`
  表示現行引用；所有 reader、來源顯示、更新與驗證一次改讀新版權威。代價是讀取器遷移較廣。

兩個 Q4 選項都不能有兩份可獨立修改的現行綁定。若需要修改條文，須另附候選全文核可；
本片不修改條文，也不把上述工程提案寫成已採納事實。

補充可推導項：改綁後舊足跡再被判 continuous，仍只供審查；current 不會自動改回。
只有另一次明示選回才能換 current（D62 附加段、D67、R61）。這不是配號器重用舊記號。

## 2. S1 可用範圍與信任邊界

`model_carrier_edit.py` 是 H 層無狀態計算 helper，依真原生來源檢查、隔離去身分 dump、
完整舊模型重播與 `space_modeling.preview` 產生候選，不另寫幾何引擎。

本片可計算 1–16 列普通 faces 的新增、移除、重排與人工改指。新增明選目標、
orientation、purpose；同目標保留列的設定隨列鍵保持，這片不另提供同目標設定編輯。
改指時可以明選新的相對朝向與用途，甚至原目標 continuous；世界法向以真原生 frame
乘明選 orientation 顯示，不能只以相同符號宣稱方向相同。

不納入 plan、障礙、角材、拉伸件、assembly-owned 或其他新附件。整份來源沿 D1／F1b
既有 `_scene` 能力限制，含 assembly-* 仍拒絕，沒有為 S1 新增例外。
合法開放 surface-set 依原 producer 求值；體積未定保持 null／原診斷，不改成零。
任何已請求的必要包失敗均拒絕，不保存成功的子集合。

| 可驗證 | S1 不能證明 |
|---|---|
| 完整原生來源與 I70、舊模型重播、新模型單一來源 | 傳入來源就是目前 App 正式 World；projectId 是 caller assertion |
| 完整明選清單、唯一標籤、唯一目標、逐列方向與用途 | 正式 carrierId 配號、跨提交刪後不重用或分支 tombstone |
| 全部候選欄位可依外部原輸入重算 | 人類同意、App context、epoch、ABA、一次性提交令牌 |
| 原 input／record bytes 不變，隔離程序不寫正式 World | .gcanvas 冷開、正式 history、dirty、有效收據與能力遷移 |

`authority` 明列 caller-asserted／caller-provisional／unverified／confirmation:false。
S1 不建立第二套 Python undo/redo，也不把 JSON 往返叫完整專案保存。

## 3. 載體計算與固定來源

舊模型仍是基底可讀的完整普通 faces record；`carrier_ids` 是呼叫者對舊列的當次暫態標籤。
`selection` 必須是完整新清單，每列只准四欄：

```json
{"carrierId":"draft-north","placement_id":0,"orientation":1,"purpose":"boundary"}
```

合法零號保留。相同標籤／相同目標為 retained；相同標籤／另一目標為 retargeted；
新標籤為 added；未出現在完整新清單的舊標籤為 removed。重排比較存續標籤次序，
不按 array index 轉交 orientation／purpose。省欄位、未知欄位、重複標籤／目標、非法
朝向／用途及空清單均明確拒絕。空清單可作未完成的 UI 編輯狀態，但不能產有效模型。

每個保留／改指列按其標籤獨立驗固定材料／規則版本及逐根欄位路徑，重用原
`model_update._protected`、`_fixed_versions`、`_fixed_associations`。單根正規化避免舊
`selected-use:index` 隨重排換人。新增／移除可明示帶入／移出自己的依賴，但不能掩蓋
另一存續列的固定版本或引用關係變更；不以全圖聯集相同代替逐列守門。

## 4. API 與候選格式

- `capabilities()`：只回報 partial draft 能力，commit/save/history/永久配號均 false。
- `judge_roots(...)`：沿 D1 R57 實作；只處理已驗完整 I70 圖中的 ordinary roots。
- `plan_selection(carrier_ids, old_uses, selection)`：純載體對應，回 rows／removed／orderChanged。
- `prepare_candidate(record_raw, source_scene, selection, *, project_id, carrier_ids, ...)`：
  真原生重播、完整新模型、原件、逐列比較、框架、新引用與影響摘要。
- `validate_candidate(candidate, record_raw, source_scene, selection, *, project_id, carrier_ids, ...)`：
  必須獨立提供原明選與舊標籤；不能從待驗候選自讀選擇。依全部外部值重建後逐值比較。

`geometry-model-carrier-draft/1` 明標 `candidateNotSaveable:true`、`committed:false`。
`beforeRaw` 保留舊 JSON 縮排與尾換行，`comparison` 保留全部舊列（包含移除列）的當次事實。
`geometryRecord` 僅是原生重播投影，無 sourceIdentity，不是新版正式紀錄；
其 input.uses 是 selection 去除 carrierId 後的幾何投影，結果全部來自同一去身分快照。
`currentReferences` 只描述當次明選的新目標；未啟用帳如實保留 null 與 ledger-inactive，
不補舊記號、不暗啟用帳。完整 identified 來源見證只存在專案層 draft，幾何輸入不帶記號。

impact 分開 carrierListChanged、geometryChanged、nonContinuousCarrierIds，沒有拿一個
changed boolean 冒充正式 history 或升版判斷。原生／公理／Python 版本由開始讀舊紀錄
之前到候選結束完整核對；驗證成功仍不是宿主權限或新世代確認。

| 容量 | 上限 |
|---|---:|
| 舊／新普通 faces | 各 1–16 |
| 單列標籤 | 128 UTF-8 bytes |
| 舊模型原件 | 8 MiB，沿 D1 |
| 單份來源場景 | 1 MiB，沿 F1b |
| 整個請求（原件＋完整來源、選擇與上下文編碼） | 8 MiB |
| 完整候選 | 16 MiB |

各項上限並不保證其最大值可同時使用；合計超限整筆拒絕，不截斷。已知跨專案的
關聯匯入不在此片，明確 UNSUPPORTED；歷史歸屬未確認時保留 unknown。

## 5. 與 K3-44 既有入口的接續設計

既有入口是「檔案 → 3D 模型庫 → 修改模型 → 採用現行來源…」。後續 S4 沿同一入口，
把固定列選擇區換成可編輯清單；不新增平行主選單或第二套確認表單。BACKLOG 的 UI
減重說明應記「以載體清單取代原固定逐面選擇區，合併來源核對與結果差異」。

| 現行行為 | 新路徑安排 |
|---|---|
| unknown／absent／replaced 人工明選 | 保留；顯示舊判定、新目標與未知原因，不自動猜 |
| 合法 World 的 conflict 人工改指 | 保留可達性；先明示矛盾，完整確認後另建關聯，不能修補記號 |
| continuous 可改選 | 保留，faces 的新載體編輯交 S1；D1 的窄 API 拒絕不覆蓋既有 App 操作 |
| 選用根可明確移除，required use 原不能移除 | plan 原能力保留；新 faces 清單可明示移除列，但零列不可確認 |
| 確認直接覆寫 sourceIdentity | 只在選定新版路由後替換：新清單／新引用／舊足跡／能力同一步發布 |
| history.changeModels | 沿唯一宿主歷史，含完整前後像；不建立 Python 第二歷史 |

S4 使用者路徑：開上述入口 → 檢視每列舊狀態 → 明選保留／新增／移除／改指及順序 →
檢查逐列朝向／用途與完整模型差異 → 取消零寫入或確認一次 → 復原／重做 → 另存冷開。
1400 與 390 px 都須真 Chromium 走過；冷開範例面一律由 `newid` 取得合法空位，
不拿既有 3 號面重宣告當進場。載體控制縮排為同一清單，手機以單欄逐列核對。

## 6. 後續切片、交集與基底變更

依 #454 規則12，本輪只交第一片 T/P；後片等套用結果再出。

| 片 | 範圍／接點 | 主要驗收 |
|---|---|---|
| S1（本片） | 新 helper、獨立 oracle／測試／診斷、獨立 suite 與架構來源片段 | 原生增減重排改指、完整重播、三方 R57、先紅後綠及具名撤回 |
| S2 | 新正式模型版本、carrierId 與足跡、project-store.js／scenario_verify.py；等 Q1/Q4 | 新／舊檔與方案往返、能力剝除拒絕、容量滿拒絕；舊檔無變更不升版 |
| S3 | reference-workspace.js／model-update.js／serve.py 的 owner、context、epoch、單一歷史 | ABA 不復活、啟用獨立歷史、取消零寫入、同候選不重送、完整 undo/redo |
| S4 | model-update-app.js／既有樣式與 App 接線、獨立 canvas 片段 | 上述完整路徑、1400／390、冷開與能力不足、faces 的實際 L4 |

S2/S3/S4 與 R13 模型核對附件、F4b 模型消費者、其他 project-store／history 工作可能
同檔；屆時按最新合併結果對齊。任何未支援附件先拒絕，不能丟掉後續更新模型。
S1 不改這些共用檔，不碰 SSOT、需求帳、既有 F1b 固定列數守門或 K3 JavaScript。

若 #466 再改：重新核對 source_reassociation 的 `_context` 回傳、`_record`／`_observe`
範圍、runtime 鍵、五態欄位與未知原因；重跑舊重播、所有新 tests／oracle／撤回。
S1 新 validate 自己接受外部 selection／carrier_ids，不依賴 D1 的弱版 validate。
已交 D1 v3 修改自己的 oracle／test harness／validate；不得將本片的新 oracle 改回舊版，
也不得因函式名稱未變就跳過重驗。新檔可套用不等於語意合流已通過。

## 7. 驗證與層級界線

三方逐值共同域是普通 placement／boundary roots、同專案、完整合法 active/inactive 圖；
圖可含 parameter-field 複合鍵。JS 不接受 projectId，跨專案另測新 API 拒絕，
不改 graph.active 造三方一致。Node 內回傳實際呼叫前後輸入，另用負控制驗改輸入會被擋。
通用 owned timber 差異不在本片，不把 ordinary 域說成全型別支持。

新 oracle 與獨立 checker 不 import 產品；先獨立判准駁，再驗 rows／removed／設定，
避免以 outcome 自述建立合法性。窮舉是有限宇宙，正式載體配號與 App 提交不在其產品宣稱內。
具名撤回 runner 的 timeout、import、一般錯誤、skip 都是 blocked，不能算 expected red。
實跑命令、退出碼、stdout/stderr、具名失敗與來源雜湊另附交付索引及作者證據包。

新 suite 由 native_registry --init-suite 產生；正式計數／成本由 Native suite measurement
採入，pending/缺成本仍阻擋正式六片與 complete。ME／AE 依既有 workflow 真重產，
不手寫收據、固定帳本、architecture scan／report、閱讀器或既有 golden。

本片交付時只有作者補丁及本地驗證，沒有自己的 PR，不能記 L2／L3／L4／L5。
D1 已有 #466 只代表該切片 L2。本片一般 App、正式保存、宿主世代、Windows、真 Chromium、
正式全部 CI 仍未驗；既有 F1b plan 的 L4 不作新 faces 的驗收證據。
