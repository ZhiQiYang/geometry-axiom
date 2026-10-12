# Q38j — 已定位拉伸件明選納入空間模型：快照語意與可實作契約（r2）

- 狀態：**r2，暫定（依 2026-10-09 授權 L）**。opus 對抗審查結論「改完 12 項可寫入、不必再審」；本版依主迴圈裁決逐項修訂，對照見文末「r2 修訂對照表」。
- 對應工單：BACKLOG GEO-256 剩餘切片 ①「Q38j 併入空間模型」（`BACKLOG.md:169-174`）；決策佇列 🔒Q38j（`決策佇列.md:117`：「比照 GEO-208 明選納入」）；
  提案 `geometry-core/SECTION-PROFILE-EXTRUSION-PROPOSAL.md` §4 Q38j（:204-206）、§7（:319）。
- 基底：`origin/main` = `6a8c2fac3f220ea4e76139da7c232a658dfebf16`。其 `公理層.md` blob `b2c4aee6…`，LF 1182 行，
  LF SHA-256 `29ad0c65…1eaf2`，與 Q38 採納版 `3ad8012` 及 K1 基底 `a7bff8f` 內容相同。行號一律以 LF 計。
- 配套：`AXIOM-DIFF.md`（逐條 Δ，條號佔位 D⟨Q38j-n⟩／I⟨Q38j-n⟩／R⟨Q38j-n⟩）、`decisions-provisional.md`（岔路與暫定採用）。
- 新格式號用佔位符：專案 `geometry-canvas/⟨Q38j-F⟩`；空間預覽 `geometry-space-preview/3`。PF-0（PR #184）、K1、K2a、K2b、K3 可能同時占號，寫入時統一配發。

## 0. 結論

**需要公理差異，但很小。** 快照與即時定義的衝突不是新問題：D7 角材在 World 裡同樣是即時重算（R2、R6(e)），
GEO-208 早已用「建立當下取來源快照、之後不改寫」把它們併入空間模型；#44 F1b（2026-10-04 CONT-8 第 3 項）
又提供「採用現行來源」：明選目前 World 的來源、預覽新舊差異、**整筆**取代同一模型紀錄、一步復原。
Q38j 兩條路都沿用：建立模型時明選納入，以及在既有模型上以 F1b 明選納入（選項 A＋F1b）。

需要改條文只因三件事：
(1) 第四節（`公理層.md:1179-1182`）明文把「併入空間 3D 模型」列為斷面拉伸第一版不做，必須解除；
(2)「保存的空間模型」在公理層沒有定義。「一個模型只有一份來源版本」「模型不隨 World 改寫、只能整筆換來源」只寫在產品文件，
這兩句也不能由現有條文推出（D25 只約束單一交換包），所以要由本差異**規定**；不規定，選項 B（即時連結）在條文上就不被排除；
(3) R40「重算全部依賴的拉伸件，不凍結舊幾何」字面上可被讀成「已保存模型也要重算」。
因此新增 D⟨Q38j-1⟩／I⟨Q38j-1⟩／R⟨Q38j-1⟩，修訂 R40 一句與第四節一項，採納橫幅一併更正已過期的 Q38 橫幅，共 6 個 Δ。

**native 不需改**：模型產生器已接受 `profile-run` 根（`geometry-core/modeling/engine.py:23,319,430-441`），
model base 已輸出每條 run 的 `coordinate_space`（`geometry-core/model_base.c:326-334`）。
但公理寫入會換掉 `AXIOM_REVISION`，必須同時為 Q38 版本（`3ad8012`）下產生的含斷面套件加豁免，見 §6 Q38j-0。

## 1. 問題：快照與即時定義，具體會在哪裡打架

空間模型（`.gcanvas` 的 `manifest.models[]`）在建立當下保存一份來源場景當 `input.base_scene`：
從目前面建立時是當下的 World dump，試用內建範例時是範例場景（`source.kind` 為 `scene` 或 `example`，
`geometry-web/project-store.js:440`、`geometry-web/space-workspace.js:432,661`、`geometry-web/scenario_verify.py:408`）。
再由它推導空間、體積、淨空、材料牆與角材交換包（`geometry-web/space_modeling.py:430-493`）。
「修改模型」只改設定、沿用保存的 `base_scene`（`space-workspace.js:703`「輪廓沿用保存的定義，不會自動讀取畫布的新變更」）；
F1b「採用現行來源」則以目前 World 重新推導整筆紀錄（`geometry-web/model_update.py:367-413`）。
拉伸件是 World 物件，宿主、L、斷面一改就依 R40 重算。兩者合併時會遇到（以下模型命名為 SA、SB，構件命名為 M1–M3）：

| # | 情境 | 若模型「即時」顯示拉伸件會怎樣 |
|---|---|---|
| S1 | t0 由房間平面建模型 SA（西牆內面 x=0、牆厚 100 向外）。燈槽 PR1 以承載面引用貼在代表西牆的立面承載面 H（x=0）。t1 使用者把房間西緣與 H 一起外推到 x=−200。 | World 中 PR1 依 R40 移到 x=−200；SA 的西牆仍在 x=0、牆體占 x∈[−100,0]。即時顯示會讓燈槽埋進牆外 100 mm。t0（兩者都在 0）與 t1（以現行來源重算後兩者都在 −200）都不是這個配置：**拼出了從未存在的設計**。 |
| S2 | 建模後刪掉 PR1，日後又以同 id 1 建一條不同斷面的拉伸件。 | 模型會把另一條燈槽當成「當初納入的那條」顯示。現在沒有任何身分依據（K3 身分帳首版不涵蓋 profile-run），內容相同也只證明同內容。 |
| S3 | PR3 以「空間牆取值」從 SA 的頂面取值（z=2700）。之後在 SA 上把牆高 2700 改 3000。 | 不論哪個選項，PR3 都不該跟著上移：D38 明文取值後不連動（`公理層.md:528-530`）。若實作順手「貼回頂面」就是猜測設計意圖（R3）。 |
| S4 | SA 先建好，燈槽才以 SA 的牆取值定位，使用者想在 SA 裡看到燈槽。 | SA 的來源快照裡根本沒有這條拉伸件。要看到它，只能從含有它的 World 版本**整筆**重新推導：以 F1b 採用現行來源並明選它，或另建模型。 |
| S5 | 重開專案或匯入時依 I31 重算核對保存的模型（`space_modeling.py:394-427` `replay_stored`）。 | 即時部分沒有保存的定義可重放，核對做不到；I31 要求「匯入必重驗 definitions…不符拒絕快照」。 |

## 2. 物理機制與規定的理由（先模擬，再定規則）

1. **一個模型是某一刻的設計**。燈槽是貼著那一刻的牆或頂施作的，牆與燈槽的相對位置只在同一個 World 版本內有意義。
   拿 t0 的牆配 t1 的燈槽，不是「比較新」，而是錯（S1）。只有在模型其餘來源都沒變時，即時顯示才碰巧正確，而那時整筆重算會得到同樣結果。
   → 因此**規定**單一來源版本。這不是由現有條文推出的：D25「定義版本必與快照所由產生的版本一致」只約束單一交換包，一個模型由多個交換包組成，
   公理層並沒有「模型」這個單位。本差異的 D⟨Q38j-1⟩ 才建立它。推論：換來源只能**整筆**換（F1b 正是如此），不能只把某條拉伸件換成目前定義。
2. **沒有世界位置的東西放不進空間**。未定位拉伸件只有局部 (u,v,w)（D39：「不出現在任何空間的 3D 結果或世界座標輸出中」）。→ 定義推論，不是選項。
3. **明選，不猜歸屬**。依據是 🔒Q38j「比照 GEO-208 明選納入」（`決策佇列.md:117`）。另外，拉伸件和空間之間也沒有像角材 `placement_id` 那樣的精確從屬關係：
   承載面引用的宿主可能是任何面，空間牆取值的來源說明依 D38「只供顯示，不是身分或引用」；依位置遠近、宿主或說明文字自動納入就是猜（R3）。
4. **重疊沒檢查，總量就要明標**。I50 規定拉伸件之間、拉伸件與空間、柱樑、角材之間都不做碰撞檢查（🔒Q38i：轉角重疊不檢查並標示）。
   兩條燈槽在牆角交會時，轉角那一段的體積會被兩條各算一次；實物上兩支實心料不可能占同一空間。
   → 規定：逐構件列出材料量（每個構件體積是精確的 A·B·L 或 t·w·L，R37）；所選拉伸件的總量可以列，但必須明標「未扣拉伸件間重疊」；
   拉伸件材料量**不與**角材、牆、空間體積合計。這是規定，不是定義推論。
5. **燈槽占用房間空氣，但淨空只扣明示障礙**。真實淨空會被燈槽吃掉一些；可是 D22／R26 規定「未列障礙不自動扣除」，
   而燈槽該以構件還是包絡扣除也沒有唯一答案（包絡含構件之間的空隙）。→ 首版不把拉伸件當障礙；畫面不得暗示淨空已扣燈槽。
6. **取值不連動是使用者明選的語意**（S3）。需要跟著牆走，應改用承載面引用（D38、提案 R9）。改牆高後燈槽不再貼頂，模型如實顯示高度，不搬、不裁、不宣稱「已貼合」（I50）。
7. **保存的模型不會自己變**。GEO-208 T09 已驗收「建立後修改／刪除來源…不改寫已保存模型」；F1b 也是使用者明選、預覽後整筆取代。
   角材本來就是即時定義（R6(e)），所以 Q38j 不是新衝突，是同一先例的延伸。

## 3. 選項

| 選項 | 內容 | 物理／使用理由 | 與條文、先例的一致性 | 成本 |
|---|---|---|---|---|
| A 納入即凍結（只在建立時） | 建立模型時明選已定位拉伸件；與空間、角材同一份 `base_scene` 推導一包拉伸件套件；World 之後怎麼改都不改寫它。 | 牆與燈槽永遠同一時刻，配置必曾存在（§2-1）；可重放核對（S5）；與角材一致。缺點：S4 只能另建模型，舊模型留在庫裡。 | 與 D9、D25、I31、R28 末句、D38、D39、I50、GEO-208 T08／T09、MODEL-SNAPSHOT-SCHEDULE 的「快照列不連到同 ID 現行角材」一致；只與第四節的明文排除衝突。 | 低：native 零改動；後端仿 `_timbers`；前端仿角材納入；一個新格式號。 |
| **A＋F1b（建議）** | A，再把既有 F1b「採用現行來源」的明選內容擴及拉伸件：以目前 World 整筆重算、預覽新舊差異、確認後整筆取代同一模型、一步復原。 | 解 S4：燈槽以 SA 的牆取值定位後，對 SA 採用現行來源並勾選它，SA 就含燈槽，且牆與燈槽仍同一版本。 | 與 A 相同，再加 CONT-8 第 3 項已採納的 F1b 語意（整筆取代、身分 `unknown`）；不新增入口。 | 中：多一個切片改 `model_update.py`、`model-update-app.js`。 |
| B 保留即時連結 | 模型只存拉伸件 id；開啟或更新時從目前 World 求值拉伸件，空間部分仍是快照。 | 模型永遠看到最新燈槽。但 S1 會拼出不存在的配置；S2 會把別的物件當成原物件；改牆高時燈槽會跟著目前 World 變。 | 與 GEO-208 T09、I31 重放核對相反；R40「不凍結」管的是 World 內的拉伸件，不是衍生輸出。現行條文沒有排除它，所以才需要 D⟨Q38j-1⟩。 | 中高，且仍無法證明身分。 |
| C1 整個模型改即時 | 模型只保存設定與明選，每次從目前 World 重算全部（含牆）。 | 不會拼版本；但已建模型會因任何畫布編輯而改變，「保存的模型」失去意義。 | 推翻 GEO-208 T08／T09、GEO-210 G06、F1b 的「明選後才更新」與 README「來源日後修改不會自動更新已建立模型」；屬產品層大翻轉，超出 Q38j。 | 高。 |
| C3 A＋檢視疊加目前拉伸件（不保存） | 開啟舊模型時，另疊上目前 World 的拉伸件作參考。 | 疊加本身就是 S1 的混版顯示；只有來源未變時才正確。 | 與 D9「來源已變而尚未重算的快照不得冒充現況」緊張；需加開關（GEO-219）。 | 中。不採。 |

## 4. 建議：採 A＋F1b，語意契約如下

1. **建立時納入**：只在「由平面輪廓建立空間」時（plan 模式，比照 GEO-208）提供；明選清單，介面預設不勾（偏離 GEO-208 T05 的預設勾選，理由見 J7）。
   候選是與 `base_scene` 同一 World 版本中**全部已定位**拉伸件；未定位者不可勾，只顯示數量與原因（D39）。
2. **求值**：同一份 `base_scene` 對所選拉伸件發一次 R39 請求，根依 id 遞增，`allow_partial=false`；任一條不完整，整個預覽／建立失敗（I31）。
3. **快照**：模型保存拉伸件套件；World 之後的重算、刪除、同 id 重建都不改寫它；模型內的拉伸件不得僅憑同 id 或同內容連到目前 World 的拉伸件。
4. **修改模型（牆高）**：沿用保存的 `base_scene` 與清單重算；拉伸件不動，包括取值自本模型牆面的拉伸件（D38）。這條路不能改納入清單。
5. **F1b 採用現行來源**：明選內容加拉伸件清單（可為空＝本次不納入）；候選與角材相同，取自同一份 `current_scene`；
   產生的整筆紀錄只有新來源一個版本。舊紀錄有、新選擇沒有的拉伸件就是本次移除，新舊差異必須列出。不提供「只更新某條拉伸件」。
6. **身分與量**：構件身分（run id, member id）保留；包絡只作參考、空間模型檢視中不畫、不計材料量。
   材料量逐構件列出；所選拉伸件的總量明標「未扣拉伸件間重疊」；不與空間體積、淨空、材料牆、角材相加。
   拉伸件不是殼成員、不是淨空障礙；不宣稱任何碰撞或貼合已檢查。
7. **新鮮度**：沿用模型卡片既有的「來源狀態」（`geometry-web/source-inspector.js:157-183` `freshness`），
   只把所納入的拉伸件加入 `modelRoots`（`:89-92`）；訊息沿用「相關來源已變更，需核對；模型保持原快照」。不新增徽章。

## 5. 資料契約

### 5.1 建立請求（`/model/space-preview`，plan 模式）

- 新增選用欄位 `input.profile_runs`：非空、無重複的 `[{kind:"profile-run", id:uint32}]`，id 可為 0。不納入時**省略**；明寫空清單為 INVALID（訊息：不納入請省略此欄）。
- faces 模式帶此欄 → `UNSUPPORTED`，碼 `SPACE_PROFILE_RUNS_MODE`，訊息「第一版只在由平面輪廓建立空間時納入拉伸件」。
- 後端 `_profile_runs(value, base, options)`（仿 `space_modeling.py:200-246` 的 `_timbers`）依序檢查：
  型別與重複 → 存在於 `base["profile_runs"]`（`load_base` 在含 section-profile 時必提供，`geometry-core/modeling/base.py:148-149`）→
  `coordinate_space == "world"`，否則 INVALID、碼 `SPACE_PROFILE_RUNS`、條號 D39 → 建包並 `verify_package` →
  套件不變式：`definitions == {base_scene: base["base_scene"], extensions: []}`、request 與根相符、`derived.status == COMPLETE`、
  每條 run 恰一個 `role=reference` 包絡（材料體積 `"0"`）、其餘物件 `role=geometry`、`coordinate_space=world`、`member_path=[member_id]`、
  體積等於 `dimensions_mm` 乘積且 > 0。任何 `ModelError` 以「拉伸件 #…」前綴重拋，路徑 `["profile_runs", …]`，不回 partial。

### 5.2 回應

- 有 `profile_runs` 時：`schema = "geometry-space-preview/3"`，加 `profile_runs` 套件；`timbers` 仍依原規則可有可無。
- 逐構件材料量就是套件每個 geometry 物件的 `section_profile.material_volume_mm3`（`SECTION-PROFILE-MODELING.md` 欄位表），介面與核對清單逐列顯示。
- `summary` 加 `profile_run_count`、`profile_member_count`、`profile_material_volume_mm3`（十進位字串，所選拉伸件全部 geometry 物件的和），
  以及 `profile_overlap_checked: false`（固定值，明標未扣拉伸件間重疊；介面據此顯示註記，驗證端拒絕其他值）。
- 既有 `space`／`volume`／`clearance`／`walls`／`timbers` 與 `summary` 既有欄位，與不帶 `profile_runs` 的同一請求**逐位元相同**；不新增任何跨類合計欄。
- 無 `profile_runs` 的請求維持 `/1`／`/2` 原樣，不偷加欄位。

### 5.3 F1b 採用現行來源（`/model/update-preview`）

- `selection` 加必填 `profile_runs`：typed 清單，可為空（F1b 既有慣例：明選清單含空清單，`MODEL-UPDATE-INTEGRATION.md`「Producer boundary」）。
  非空時才寫入新紀錄的 `input.profile_runs`（比照 `model_update.py:399-400` 的角材）。
- `record.input` 的允許鍵（`model_update.py:124`）加 `profile_runs`；`PACKAGES`（`:28`）與 `diff.packages` 加 `profile_runs`；
  固定版本守門的根（`:276` 一帶）加入所選拉伸件，使其 D26／D28 來源閉包同樣受 `UPDATE_FIXED_VERSION` 保護。
- 回執 `identity` 維持 `unknown`；不以同 id 宣稱新舊拉伸件是同一物件。

### 5.4 保存與重放

- 模型紀錄沿用 `{id,name,created_at,source,input,result}`；`input.profile_runs`、`result.profile_runs` 隨紀錄保存。
- 任何模型含 `profile_runs`（或 `result.schema == /3`）時，專案保存為 `geometry-canvas/⟨Q38j-F⟩`，`requiredCapabilities` 含 `section-profile/1`。
  其餘專案不強制升級。舊程式依格式表（`geometry-web/project-store.js:23-31`）明確拒絕新格式，不會丟失拉伸件。
- `validateProfileRunModel(record)`（仿 `project-store.js:401-430` `validateTimberModel`）：清單合法、`input.mode == "plan"`、
  套件根與清單一致、無 local 物件、每 run 一個包絡、`summary` 四欄與套件一致、`result.source_sha256` 與既有核對一致。
- **三處重放鍵清單都要加 `profile_runs`**：`space_modeling.py:413`（`replay_stored`）；`geometry-web/scenario_verify.py:453`（方案快照的獨立重放，現只在 `inputs` 含 `timbers` 時加 `timbers`）；
  `geometry-web/reference-workspace.js:1643`（`verifyStoredModel` 的 `packageKeys`）。後者現以 `schema === "geometry-space-preview/2"` 判斷是否驗 `timbers`，
  `/3` 也可能含角材，須改為依 `input` 是否有 `timbers`／`profile_runs` 決定，否則 `/3` 模型的角材包會漏驗。
- 能力宣告：`serve.py:406` 的 `space_preview_schemas` 加入 `geometry-space-preview/3`。執行器早已宣告 `section-profile/1`（`modeling/__init__.py:56-57`），
  那只表示能求值拉伸件，不表示能產出含拉伸件的空間模型；前端送出前以 `/3` 是否被宣告為準（仿 `requireTimberCapability`，Q16）。

## 6. 實作切分

| 切片 | 內容 | 層 | 依賴 |
|---|---|---|---|
| **前置驗證（Q17）** | 在 Q38j-0 之前先跑：World 含斷面定義、不帶 `profile_runs` 的空間建模能照常產生 `/1` 結果（現有測試未涵蓋）。不綠就先停下回報。驗收：Q17。 | 測試 | — |
| **Q38j-0 公理寫入** | 依 `AXIOM-DIFF.md` Δ1–Δ6 寫入 `公理層.md`、`geometry-guide/公理層-白話.md`；`sync_axiom_reader.py` 同步正典並跑三條驗證。更新 `geometry-core/modeling/__init__.py` 的 AXIOM_* 常數，**並新增豁免集合**（下段）。驗收：Q23，加正典三條驗證。 | SSOT＋模型版本守門 | 前置驗證綠；與 PF-0／K1／K2a／K2b／K3 依序配號 |
| **native** | **不改**。engine 已收 `profile-run` 根並輸出世界／局部座標；model base 已輸出 `coordinate_space`；候選由既有 `section-profile-read` 提供；模型是專案層，不進 World。 | — | — |
| **Q38j-a 後端** | `geometry-web/space_modeling.py`：`_profile_runs`、plan 模式 `_keys` 加選用鍵、faces 模式明確拒絕、`/3` 與 summary、`replay_stored` 鍵清單。`geometry-web/scenario_verify.py:453` 鍵清單加 `profile_runs`。`geometry-web/serve.py:406` 宣告 `/3`。`geometry-web/model_update.py`：**暫時守門**——`record.input` 含 `profile_runs` 時回 `UNSUPPORTED`、碼 `UPDATE_PROFILE_RUNS`（現在會被 `:124` 的嚴格鍵以泛用的 `UPDATE_SHAPE` 擋下，訊息誤導）。驗收：Q01、Q01b、Q02–Q05、Q07 後端段、Q08(a)–(e) 的重放部分、Q08(f)、Q15、Q16 的服務宣告部分、Q19 後端部分、Q21(b)；測試檔 `tests/test_space_modeling.py`、方案快照路徑的竄改測試、`tests/test_model_update.py`。 | bridge／Python | Q38j-0 |
| **Q38j-b 前端與保存** | `geometry-web/project-store.js`（新格式、`validateProfileRunModel`、格式允許清單 `:310-341` 每處加新格式）；`geometry-web/reference-workspace.js:1643`（`packageKeys` 改依 `input` 判斷並加 `profile_runs`）；`geometry-web/space-workspace.js`（候選讀取與同版守門、納入清單、預覽失效、摘要、模型卡片 `:687`、模型檢視 `:703` 文字、能力檢查、開關文字）；`geometry-web/model-viewer.js:77-86`（拉伸件構件歸同一開關、網格標籤「斷面拉伸件」、不畫包絡）；`geometry-web/source-inspector.js:89-92`（`modelRoots` 加 profile-run）；文件 `docs/SPACE-MODELING.md`、`docs/DOM-CONTRACT.md`、`docs/REFERENCE-PROJECT.md`、`docs/TIMBER-IN-SPACE.md`、新增 `docs/PROFILE-RUN-IN-SPACE.md`。驗收：Q06、Q07 介面段、Q08(a)–(e) 的保存驗證部分、Q09–Q14、Q16 的前端部分、Q18、Q19；測試檔 `tests/test_space_model_store.js`、`tests/test_model_viewer.cjs`、`tests/test_source_inspector.js`、`geometry-web/space_model_test.js`、`geometry-web/source_inspector_browser_check.js`。 | 前端／保存格式 | Q38j-a |
| **Q38j-c F1b 擴及拉伸件** | `geometry-web/model_update.py`（`selection.profile_runs`、允許鍵、`PACKAGES`、固定版本守門根；移除 Q38j-a 的暫時守門）；`geometry-web/model-update-app.js`（候選讀取、勾選清單、`packages`／`packageNames` 加 `profile_runs`、disclosure 文字）；`geometry-web/model-update.js`。驗收：Q20、Q21(a)、Q22；測試檔 `tests/test_model_update.py`、`tests/test_model_update.js`、`geometry-web/model_update_browser_check.js`。 | bridge＋前端 | Q38j-b |

**Q38j-0 的模型版本豁免**：照 Q38 的 `263235f` 只換 `AXIOM_REVISION`／`AXIOM_SHA256` 的話，在 `3ad8012` 下產生、含斷面的套件會被
`geometry-core/modeling/__init__.py:180-182` 以「Section profiles require the adopted Q38 axiom revision」拒成 `UNSUPPORTED`，既有含斷面的專案全部打不開。
做法比照 PF-0 分支的 `PRE_PANEL_FILL_AXIOM_VERSIONS`（PF-0 分支 `origin/axiom/adopt-panel-fill-pf0-20261010` @ `444a871` 的 `geometry-core/modeling/__init__.py:24-28,179-182,188-191`）：
新增一個「本差異之前已採納、且支援 section-profile/1」的版本集合，內含 `3ad8012`（`29ad0c65…1eaf2`）以及寫入時已合併的 PF-0、K1 等版本的 (revision, LF SHA-256)；
加入允許集合（origin/main `6a8c2fa` 第 171–174 行；PF-0 分支 `444a871` 第 179–182 行），並在斷面拒絕（origin/main 第 180–182 行；PF-0 分支第 188–191 行）與其後各版本守門中比照 PF-0 豁免它。行號以寫入當下的基底為準。驗收 Q23。

- 三個實作 PR 依序提交：後端可用夾具獨立驗；前端牽涉格式與真瀏覽器；F1b 有自己的守門與瀏覽器檢查。突變與收據各自分開。
- 動空間工作區 → 必跑 `space_model_test.js`；若碰 `app.js` → 加跑完整 `cdp_test.js`（AGENTS.md）。WSL 經排隊鎖。
- 🔒A「不碰 Codex 正在改的檔」（`決策佇列.md:45`，含 `space-workspace.js`、`reference-workspace.js`）的前提已不成立，見 J30；開工時再核一次。

## 7. 介面與 GEO-219 減項（請主迴圈寫入 BACKLOG GEO-256）

- **新可見項**：(1) 建立空間時的拉伸件勾選清單；(2) F1b「採用現行來源」對話框的拉伸件勾選清單；(3) 3D 中的拉伸件構件；(4) 預覽摘要、逐構件材料量與模型卡片的拉伸件數量文字。
- **拿掉／合併**：
  1. 建立空間不新增區塊：既有區塊 `#smTimberSettings`（`space-workspace.js:52`）目前是**單一核取框**「一併納入此面角材（N 支）」加一段說明與候選核對 disclosure。
     角材維持單一核取框（全納入或不納入，行為不變）；同一區塊改標題為「一併納入」，在其下加拉伸件的逐條核取清單，與角材共用**同一段**說明（改寫原說明句，常駐說明數不增）。
  2. F1b 對話框不新增 disclosure：既有「本次明選內容」中的「角材」disclosure（`model-update-app.js` `#muTimbers` 所在處）改為「角材與拉伸件」，內含兩組勾選。
  3. 不新增顯示開關：既有「角材結構」開關（`#smShowTimbers`，`space-workspace.js:45`）的文字改為「角材與拉伸件」，同時控制角材與拉伸件構件；包絡在空間模型中不畫。
     不用「構件」一詞：D36 的「構件」專指斷面構件（`公理層.md:508-515`，「構件不是 D7 角材」），用來同時指角材會混淆。
  4. 沿用既有「3D 模型庫」入口與模型卡片；只改卡片摘要文字（加「拉伸件 N 條 · 來源快照」）。不新增匯出選項、範例、工具列、工作區或徽章。
- **網格標籤不改**：角材網格的標籤維持「角材結構」，拉伸件網格另用「斷面拉伸件」。所以只有開關與 disclosure 文字是規格變更。
  受影響斷言：`tests/test_model_viewer.cjs:82`、`geometry-web/space_model_test.js:1127`（斷言網格標籤「角材結構」，標籤不改則**不需改**）；
  `geometry-web/docs/DOM-CONTRACT.md:194`（「`#smShowTimbers` 只控制真實角材 mesh」，**須改**為同時控制拉伸件構件）；
  `geometry-web/docs/TIMBER-IN-SPACE.md:16`（三個開關名稱，**須改**開關文字）；F1b 對話框文字若有斷言，以實作時 grep 為準。
- 拉伸件清單每列：`#id · 斷面名稱 · L mm · N 個構件 · 定位方式`（承載面 #H／「依…取值」原來源說明／進階）。來源說明只顯示，不據以篩選或預選。
- 摘要寫法：「拉伸件 N 條（M 個構件）· 材料量合計 X（未扣拉伸件間重疊；不含角材、牆）」，核對清單逐構件列體積。不出現「貼合」「無衝突」等宣稱。

## 8. 驗收清單（夾具 F1；數字已手算）

**F1**：平面 `boundary 1` 外輪廓 (0,0)–(4000,0)–(4000,5000)–(0,5000)，`placement 1` 原點 (0,0,0)、u=+x、v=+y；
設定：牆底 0、牆高 2700、四邊皆邊界、底與頂為邊界、無孔、牆厚 100。
斷面 SP1 = Q38 提案的 L 形 (0,0)→(400,0)→(400,60)→(60,60)→(60,250)→(0,250)，構件 M1 27×33 A 沿 u (0,0)、M2 27×33 A 沿 u (373,0)、M3 27×33 A 沿 v (0,223)。
PR1：SP1、L=2400、進階定位 O=(1000,2000,2700)、N=+Y、V=−Z（U=+X，Q38 AC09）。PR2：SP1、L=1000、未定位。PR0：id 0、已定位。
模型一律以 SA、SB 命名，與構件 M1–M3 區分；夾具拉伸件為 PR0–PR4、斷面為 SP1，與公理的 R 條號及情境 S1–S5 區分。

| # | 輸入 | 預期 | 要打掉的變異 |
|---|---|---|---|
| Q01 基本納入 | F1，`profile_runs=[PR1]` | `/3`；套件根 [PR1]；3 個 geometry：M1 x[1000,1027] y[2000,4400] z[2667,2700]、M2 x[1373,1400] 同 y、z[2667,2700]、M3 x[1000,1033] 同 y、z[2450,2477]；每個構件 `material_volume_mm3="2138400"`（27×33×2400）；1 個 reference 包絡（材料 `"0"`）；summary `profile_run_count=1`、`profile_member_count=3`、`profile_material_volume_mm3="6415200"`、`profile_overlap_checked=false` | 包絡計入材料（會得 91,375,200＝6,415,200＋包絡 35,400×2400＝84,960,000）→ 紅 |
| Q01b 重疊明標 | F1 另加 PR4：SP1、L=1000、O=(1000,2027,2700)、N=+X、V=−Z（U=−Y；與 PR1 在牆角交會）；`profile_runs=[PR1,PR4]` | 照常建立；總量＝6,415,200＋3×27×33×1000＝9,088,200，`profile_overlap_checked=false`，介面顯示「未扣拉伸件間重疊」；不報碰撞 | 移除註記或把 `profile_overlap_checked` 寫成 true |
| Q02 量不混 | 同 Q01，對照不帶 `profile_runs` | `space`／`volume`／`clearance`／`walls` 套件與既有 summary 欄逐位元相同；無任何跨類合計欄 | 把拉伸件體積加進 `volume_mm3`、牆體積或角材體積 |
| Q03 未定位 | `profile_runs=[PR2]` | INVALID `SPACE_PROFILE_RUNS`，條號 D39，無模型 | 拿掉 `coordinate_space` 檢查 → 局部物件被塞進模型 → 紅 |
| Q04 清單守門 | 不存在 id、重複、`[]`、kind 錯、id −1／1.5、PR0（id 0） | 前五者拒絕（`[]` 訊息指示省略）；PR0 接受，不被當空值 | 用真值判斷 id |
| Q05 全有或全無 | 以壓低 `max_cells` 或故障注入讓拉伸件套件 `UNSUPPORTED/CAPACITY` | 整個預覽失敗，無 `space` 結果、無模型紀錄 | 改成略過失敗的 run 仍回成功 |
| Q06 快照不隨 World | 建立含 PR1 的模型 SA 後，分別：(a) PR1 的 L 改 2000 (b) M1 移到 (0,10) (c) 刪 PR1 (d) 刪後以 id 1 重建內容不同的拉伸件 (e) 刪後以 id 1 重建內容完全相同的拉伸件 | SA 紀錄逐位元不變；`replay_stored` 通過；來源狀態：(a)(b)(d) `changed`，(c) `missing`，(e) `unknown`（「可追溯來源內容一致；物件延續性未知」，`source-inspector.js:182`）。`identity-unknown` 只在呼叫端傳入同一工作階段觀察到的刪除集合時才出現（`:157,167`），現行呼叫端（`:147,233`）未傳，故本表不期望它。SA 內構件不連到目前 PR1 | 開模型時改從目前 World 求值 → 紅 |
| Q07 改牆高與取值 | 建模型 SA（牆高 2700，不納入）→ 以 SA 頂面「空間牆取值」建 PR3（SP1、L=2400、沿水平軸、up=+Z）→ 建模型 SB（同面同設定，納入 PR3）→ SB 牆高改 3000 | SB 中 PR3 的構件 z：M1、M2 為 [2667,2700]、M3 為 [2450,2477]（z = 2700 − v）；改高後 summary 頂＝3000，PR3 範圍逐位元不變；不出現「已貼頂」字樣 | 改牆高時重新取值或依新頂面平移 PR3 |
| Q08 版本一致與竄改 | (a) 把 `result.profile_runs` 換成 L=2000 版 `base_scene` 產生並重算雜湊的套件 (b) 清單含 PR2 (c) summary 材料量含包絡 (d) 套件含 local 物件 (e) 根與清單不符 (f) 把 (a) 的竄改模型放進方案快照，走 `scenario_verify.py` 獨立重放 | (a)–(e) 在替換目前專案前拒絕，目前專案不變；(f) `SCENARIO_MODEL_REPLAY` 拒絕 | 只驗套件自洽、不比對 `input.base_scene`；或重放鍵清單漏 `profile_runs` → (f) 通過 → 紅 |
| Q09 保存重開 | 含 Q01 模型的專案保存 → 新工作階段重開 | 格式 `⟨Q38j-F⟩`、含 `section-profile/1`；重開後幾何、數量、材料量逐位元相同；`verifyStoredModel` 對 `/3` 模型同時驗 `timbers`（若有）與 `profile_runs` | `packageKeys` 仍以 `schema === /2` 判斷角材 → `/3` 含角材時漏驗 → 紅 |
| Q10 舊程式與舊專案 | 以合入前的 `project-store.js` 開新格式；以新程式開 /1–/16 專案與僅角材模型 | 前者明確「專案版本不支援」；後者照舊可開、可改牆高，不升級格式、不自動補入拉伸件 | 新格式偵測過寬，讓僅角材專案也升級 |
| Q11 過期來源 | 「使用目前面」後只改 PR1 的 L，再按更新預覽與建立 | 兩者都拒絕（`dump` 比對涵蓋 section-profile 行），訊息要求重新使用目前面 | 候選清單快取跨版本使用 |
| Q12 候選與同版守門 | 候選讀取期間 World 改變（前後 `section-profile-read` revision 不同或 dump 不同） | 丟棄候選並重讀，不顯示舊清單 | 只讀一次不核對 |
| Q13 建立介面 | plan 模式真瀏覽器：清單只列 PR1、PR0，PR2 以「另有 1 條未定位，不能納入」一行說明；拉伸件預設不勾、角材核取框行為不變；勾選使預覽失效；「角材與拉伸件」開關同時隱藏兩者；包絡不畫；1400／690／390 px 可操作、目標 ≥ 44 px、無水平溢出；該畫面常駐說明 ≤ 3 塊 | 依左 | 拉伸件預設全勾 |
| Q14 模型庫 | 建立後開「3D 模型庫」 | 模型卡片有「拉伸件 1 條 · 來源快照」；既有已定位拉伸件卡片（`[data-sp-open-run]`）照舊、標目前定義；兩者不互相導航 | 從模型卡片連到同 id 目前拉伸件 |
| Q15 faces 模式 | faces 請求帶 `profile_runs` | `UNSUPPORTED/SPACE_PROFILE_RUNS_MODE` | 靜默忽略該欄 |
| Q16 服務能力 | 服務宣告 `section-profile/1` 但 `space_preview_schemas` 不含 `/3` | 前端不送出，顯示能力不足；不降級成不含拉伸件的模型 | 以 `section-profile/1` 當作可納入 |
| Q17 前置：含斷面的來源、不納入 | F1 World 含 SP1、PR1、PR2，但不帶 `profile_runs` | 照常建模，`/1`；與「World 無斷面」的同設定空間幾何相同（套件 manifest 依現行規則宣告能力）。**在 Q38j-0 之前先跑** | —（現有測試未涵蓋此情形） |
| Q18 快照料單不變 | 對 Q01 模型跑既有保存快照料單 | 只列明選角材，不含拉伸件構件（Q38a、K1 皆排除 D36） | 把構件混入料單 |
| Q19 GEO-208 回歸 | 既有 T01–T15 的自動化部分 | 全綠，角材仍 z=2500～2533 | — |
| Q20 F1b 納入（S4） | 建模型 SA（不納入）→ 以 SA 頂面取值建 PR3 → 對 SA「採用現行來源」，`selection.profile_runs=[PR3]`，其餘選擇同原模型 | 預覽差異列出 `profile_runs` before=null、after=新包；確認後同一模型 id、單一新來源；PR3 構件 z 同 Q07；一步復原回到原紀錄逐位元相同 | 只把拉伸件包接到舊紀錄、不換 `base_scene` → Q08(a) 型拒絕 |
| Q21 F1b 移除與守門 | (a) 對含 PR1 的模型採用現行來源、`profile_runs=[]` (b) Q38j-c 之前：對含 PR1 的模型呼叫 F1b | (a) 差異列出移除，新紀錄無 `profile_runs`、格式依其餘模型決定 (b) `UNSUPPORTED/UPDATE_PROFILE_RUNS`，不產生候選 | (b) 拿掉守門 → 回 `UPDATE_SHAPE` 或靜默丟失拉伸件 → 紅 |
| Q22 F1b 固定版本 | PR1 的 A 來源引用材料版本 M@1；目前 World 把同 id 版本內容換掉 | `UPDATE_FIXED_VERSION`，不產生候選 | 守門根未含拉伸件 |
| Q23 舊版含斷面套件 | 夾具：在 `3ad8012`（`29ad0c65…1eaf2`）下產生、含 section-profile 的 R39 套件與含 PR1 的空間模型專案；公理寫入後以新程式 `verify_package` 與開專案 | 通過，不回 `UNSUPPORTED/AXIOM_VERSION`；任意其他舊版本＋斷面仍拒絕 | 拿掉豁免集合 → `__init__.py:180-182` 拒絕 → 紅 |

- 每個「要打掉的變異」都要實際做突變：拿掉修正須轉紅，失敗訊息指得出病因；驗完還原回綠（memory 規則）。
- 既有測試只因開關文字改為「角材與拉伸件」而改期望值，屬規格變更，PR 正文寫明；其他期望值不得改動。
- Q01b 的 PR4 構件 M1 占 x[1000,2000]×y[2000,2027]×z[2667,2700]，與 PR1 的 M1 在 x[1000,1027]×y[2000,2027]×z[2667,2700] 重疊 24,057 mm³（27×27×33），是刻意製造的未檢查重疊；總量 9,088,200 不扣這段，測試只驗總量與註記，不要求算出交集。

## 9. 明確不做（首版）

1. 模型與 World 拉伸件的即時連結（選項 B）、整個模型改即時（C1）、檢視疊加（C3）。
2. 只更新模型中部分物件或部分交換包（例如只把某條拉伸件換成目前定義）；「修改模型（牆高）」路徑上更改納入清單。
3. faces（組合已有面）模式的納入；F1b 本來就只支援普通單一平面模型（`model_update.py:123`）。
4. 未定位拉伸件進入任何空間模型（D39）。
5. 拉伸件作為淨空障礙、殼成員或布林輸入；拉伸件與牆、頂、角材、柱樑、其他拉伸件的碰撞、貼合或包含判定（I50）。
6. 拉伸件材料量與角材、牆、空間的合計；扣除拉伸件之間的重疊。
7. 模型內拉伸件的 3D 點選定位、匯出拉伸件套件的新選項、現成範例。
8. 拉伸件併入快照料單或 F4b 裁切（另案，K1 首版已排除 D36）。
9. 僅憑 id 或內容相同宣稱拉伸件是同一物件（K3 身分帳首版不涵蓋 profile-run，現在沒有身分依據）。

## 10. 剩餘風險與最不確定的地方

1. **最不確定：把「保存的空間模型」寫進公理（D⟨Q38j-1⟩）是否恰當。** 它同時約束 GEO-208 角材與 F1b 的既有行為。
   我核對過的實作都相符（`space_modeling.py:394-427` 重放；`space-workspace.js:656,703,711` 建立前比對 dump、修改模型沿用保存來源；
   `model_update.py:367-413` 整筆取代；`TIMBER-IN-SPACE.md` T08／T09；`MODEL-SNAPSHOT-SCHEDULE.md`）。
   改寫端已掃：`reference-workspace.js:639-660` 只有新增、整筆更新、移除三個入口，呼叫者為 `space-workspace.js:651,662` 與 `model-update-app.js:83`，都先過 `validateSpaceModel` 且整筆替換。
   審查補出的兩個重放點（`scenario_verify.py:453`、`reference-workspace.js:1643`）已列入切片；讀取端仍可能有我沒讀到的路徑。
   若要縮小範圍，退路是只保留 Δ1（橫幅，含過期的 Q38 橫幅更正）、Δ5（R40 一句）與 Δ6（第四節），其餘降為產品契約；代價是選項 B 在條文上不被排除。
2. **Q17 未驗**：在 origin/main 的 `tests/test_space_modeling.py`、`tests/test_space_model_store.js`、`geometry-web/space_model_test.js` 中找不到「`base_scene` 含 section-profile 定義」的空間建模案例；已列為 Q38j-0 之前的前置驗證。
3. Q23 的豁免集合要等寫入當下才知道要列哪些版本（PF-0、K1 等若先合併）；漏列任何一版，該版下產生的含斷面套件就會被拒。
4. 開關文字改為「角材與拉伸件」屬規格變更；若使用者要分開看燈槽與骨架，需另議並給減項。
5. 條號、格式號與 PF-0、K1、K2a、K2b、K3 同時占號；D⟨Q38j-1⟩ 與 K2b 的 D⟨K2b-1⟩、D⟨K2b-4⟩ 語意重疊，寫入時須去重（見 `AXIOM-DIFF.md` §3）。

## r2 修訂對照表

（行號為 r2 檔案的行號，已於本表寫成後逐一核對；`公理層.md` 行號以 origin/main LF 計。）

| 項次 | 改了哪裡 | 檔案:行號 |
|---|---|---|
| 1 材料量自相矛盾（阻擋） | R⟨Q38j-1⟩ 改為逐構件列出、總量明標「未扣拉伸件間重疊」、不與角材牆空間合計，拿掉「定義推論」；Δ6 改為「不與角材、牆、空間合計，以及不扣拉伸件間重疊」；§2-4、§4-6 同步；§5.2 加 `profile_overlap_checked:false`；Q01 加逐構件值、新增 Q01b（PR4 與 PR1 重疊 24,057 mm³）；J14 改寫 | AXIOM-DIFF.md:22,123-124,170,197；PROPOSAL.md:56-58,85-87,109-110,182-183,218；decisions-provisional.md:23 |
| 2 單一來源版本不是推論（阻擋） | D⟨Q38j-1⟩ 拿掉「（定義推論）」並在說明寫明是規定；§0 表改「不能推出」；§2-1 改為「因此規定」；J4 改為選擇、推翻方式改「改 D⟨Q38j-1⟩」 | AXIOM-DIFF.md:23,77,88,185；PROPOSAL.md:20-22,49-52；decisions-provisional.md:13 |
| 3 AXIOM_* 換版會拒舊斷面套件（阻擋） | Q38j-0 加「模型版本豁免」：比照 PF-0 `PRE_PANEL_FILL_AXIOM_VERSIONS`，豁免 `3ad8012` 與寫入時已合併的 PF-0／K1 等版本；新增驗收 Q23（含拆除豁免的突變）；檔頭與 §3 PF-0 註記同步 | PROPOSAL.md:25-27,139,145-148,205；AXIOM-DIFF.md:8-10,208；decisions-provisional.md:40 |
| 4 「完整 World 定義」不符事實 | 改「來源場景（目前 World 或內建範例）」，附 `project-store.js:440`、`space-workspace.js:432,661`、`scenario_verify.py:410` | AXIOM-DIFF.md:74,89；PROPOSAL.md:31-34 |
| 5 能力守門 | I⟨Q38j-1⟩ 改為須另行宣告支援含拉伸件的空間模型輸出，只宣告 section-profile/1 不足；產品對應 `space_preview_schemas` 含 `/3`；Q16 改為「宣告 section-profile/1 但無 /3」；J21 補理由 | AXIOM-DIFF.md:105-106；PROPOSAL.md:131-132,198；decisions-provisional.md:30 |
| 6 重放核對漏列 | §5.4 列三處重放鍵清單（`space_modeling.py:413`、`scenario_verify.py:453`、`reference-workspace.js:1643`，後者改依 input 判斷以免 `/3` 漏驗角材）；Q38j-a／b 檔案清單加入；Q08 新增 (f) 方案快照路徑竄改；Q09 加 `packageKeys` 突變 | PROPOSAL.md:128-130,141-142,190-191 |
| 7 🔒A 不碰區 | 新增 J30：依前提推論不擋（#180 `c254e1f` 已合入、兩條 Codex 分支為 main 祖先、#177／#178 剩文件提交），註明計畫檔措辭依主迴圈裁決；§6 加指向 | decisions-provisional.md:39；PROPOSAL.md:153 |
| 8 與 K3 不相容 | D⟨Q38j-1⟩ 改「僅憑 id 相同或內容相同，不得…宣稱兩者是同一物件」；§3 K3 段改寫為相容說明（K3 可憑身分鍵＋記號宣稱）；§4-3、§9-9、Δ6 同步 | AXIOM-DIFF.md:80,93,171,187,204-206；PROPOSAL.md:81,221 |
| 9 「構件」與 D36 衝突 | 開關與 F1b disclosure 改「角材與拉伸件」；網格標籤不改；列出受影響斷言（`test_model_viewer.cjs:82`、`space_model_test.js:1127` 不需改；`DOM-CONTRACT.md:194`、`TIMBER-IN-SPACE.md:16` 須改）；J16 改寫；Q13 同步 | PROPOSAL.md:159-168,195；decisions-provisional.md:25 |
| 10 「整筆紀錄是衍生快照」 | 改為「各交換包是 D9 衍生快照；建模設定與明選清單是專案層的建模輸入」 | AXIOM-DIFF.md:76,183 |
| 11 Q06／Q07 | Q06 拆成 (a)–(e) 並寫明 `unknown` 與 `identity-unknown` 的出現條件（`source-inspector.js:157,167,182`）；模型改名 SA／SB 與構件 M1–M3 區分（§1、Q07、Q20 一併） | PROPOSAL.md:31-44,178,188-189,202 |
| 12 J6 不是推論；J14 | J6 依據改為 🔒Q38j（`決策佇列.md:117`），推翻方式改「須推翻 🔒Q38j」；§0 表與 §2-3 同步；J14 同第 1 項 | decisions-provisional.md:15,23；AXIOM-DIFF.md:21；PROPOSAL.md:54-55 |
| 記錄：條號 | 不用 D40a／I51a／R40a，維持佔位，接在 PF-0、K1、K2b、K2a、K3 之後順號配發；J26 改寫 | AXIOM-DIFF.md:5-6；decisions-provisional.md:35 |
| 記錄：`#smTimberSettings` | 更正為「單一核取框」區塊；角材核取框行為不變，拉伸件清單加在同一區塊；J17 同步 | PROPOSAL.md:159-160；decisions-provisional.md:26 |
| 記錄：J7 偏離 T05 | J7 寫明偏離 GEO-208 T05「預設勾選」及理由；§4-1 同步 | decisions-provisional.md:16；PROPOSAL.md:78 |
| 記錄：Q17 前置 | 列為 Q38j-0 之前的前置驗證（§6 表首列、Q17、§10-2）；新增 J33 | PROPOSAL.md:138,199,231；decisions-provisional.md:42 |
| 記錄：Q38 橫幅過期 | Δ1 改為「修改＋插入」，第 29 行改為「已隨 PR #167 / #169 合入，同源真瀏覽器驗收仍在進行」；新增 J32 | AXIOM-DIFF.md:46-67；decisions-provisional.md:41 |
| r2.1-a | `scenario_verify.py:410` 更正為 `:408`（`source["kind"] not in ("scene","example")` 所在行） | PROPOSAL.md:33；AXIOM-DIFF.md:89 |
| r2.1-b | 豁免段的行號標明分支：origin/main `6a8c2fa` 允許集合 171–174、斷面拒絕 180–182；PF-0 分支已前進到 `444a871`，其豁免集合 24–28、允許集合 179–182、斷面拒絕 188–191；註明以寫入當下的基底為準 | PROPOSAL.md:147,149 |
| r2.1-c | 縮小範圍的退路與 J2 統一為「保留 Δ1、Δ5、Δ6」 | PROPOSAL.md:230；decisions-provisional.md:11 |
| r2.1-d | §6 每個切片列出所屬驗收：前置 Q17；Q38j-0 Q23；Q38j-a Q01、Q01b、Q02–Q05、Q07 後端段、Q08 重放、Q08(f)、Q15、Q16 服務端、Q19、Q21(b)；Q38j-b Q06、Q07 介面段、Q08 保存驗證、Q09–Q14、Q16 前端、Q18、Q19；Q38j-c Q20、Q21(a)、Q22 | PROPOSAL.md:138-143 |
| r2.1-e | Δ1 新橫幅改引 BACKLOG〈Q38 斷面拉伸完整產品接線〉（`BACKLOG.md:253`「驗收中」），不再引 GEO-256 | AXIOM-DIFF.md:54,57 |
| r2.1-e 待入帳 | 交主迴圈：GEO-256 的「待 #169 合併」已過期（#169 已合入 main）——`BACKLOG.md:73` 索引列「待 #169 合併」、`:169` 標題「待 PR #169 合併」、`:171`「#169 合併後才進 main」，請更新為現況 | （本表此列；不改 repo） |
| r2.1-f | 夾具改名：拉伸件 R0–R4 → PR0–PR4、斷面 S1 → SP1；情境 S1–S5 與公理 R2／R3 不動；夾具說明加命名註記 | PROPOSAL.md:41-43,176-209,242 |
