# R12／Q38j：斷面拉伸併入空間的 App 契約

日期：2026-11-15。固定基底：`11eddfdb4d7b1f76aedfe001e084a3840790bedc`。

2026-11-17 的 #430 修補基底為 `d1738db971b05311efa4289443c73942273c8a37`（已普通 merge main `0c796e308da770041dfb41111562d594a389671a`）。以下單一來源契約已更正 raw dump 與原生 canonical 場景混用的錯誤；本次修補不提高層級，正式瀏覽器與 ME 收據另核。

本文描述相對該基底的實作候選，承接 [issue #43 設計](https://github.com/ZhiQiYang/geometry-axiom/issues/43#issuecomment-6436056651)與[接線缺口巡檢](https://github.com/ZhiQiYang/geometry-axiom/issues/43#issuecomment-6877835952)。驗收以 [公理層.md](../../公理層.md) D63、I73、R59、R40 及既有 D35–D40／I43–I51／R36–R39 為準，不修改條文。

此處的來源契約、測試清單與 source census 不代表已取得瀏覽器完成收據。最終真瀏覽器、完整整合 census、正式 mutation evidence 及 L4 實機核對仍須分別記錄；不得以舊 a／b／c 補丁的結果改綁本候選。

## 1. 這一片接通什麼

使用者從原有「建立物件 → 斷面與拉伸」建立或選擇斷面及已定位拉伸件，再由水平面屬性中的「以此面建立空間」明選納入。預覽只產生候選；確認才在目前專案加入一個保存模型。之後可一步復原／重做、保存完整 `.gcanvas`、重開，以及透過原模型的「採用現行來源…」整筆更新。

原生斷面工作區與獨立拉伸建模在固定基底已存在；Q38j 的缺口是宿主組合及保存接線。**不新增原生幾何指令，也不在前端另算幾何。** 既有 `section-profile-read/preview/confirm/cancel`、R39 `profile-run` 根及建模執行器繼續負責幾何與交易。

| 切片／接點 | 固定基底的缺口 | 本候選的接線 |
|---|---|---|
| a：原生與 producer | `space_modeling.py::_plan` 只接受選用 `timbers`；`_preview` 沒有拉伸件包 | `_profile_runs` 核對同源、已定位、無重複根並發一次 R39 請求；`_plan/_preview` 加入 `profile_runs` 與 `/3` 摘要 |
| a：bridge／HTTP | `serve.py::Handler.do_GET` 的 `/model/capabilities` 只宣告 preview `/1`、`/2` | 能力表另宣告 `/3`；沿用 `do_POST` 的 `/model/space-preview`、`/model/verify`、`/model/space-replay`，沒有新增 native mutation 路由 |
| b：建立與呈現 | `space-workspace.js::openCurrentFace/makeInput/preview/create` 沒有 run 明選；`model-viewer.js::spacePreviewObjects` 沒有 profile geometry | `sourceProfileRuns/renderProfileCandidates/checkProfileSource` 提供同版候選與守門；原入口、核對、建立及 viewer 納入獨立材料包 |
| b：保存 | `project-store.js::validateSpaceModel/validateModelPackage` 的封閉欄位拒絕 profile；各格式／hash 路徑未接 | `validateProfileRunModel/validateProfileRunHashes` 驗來源、根、metadata、數量、材料量與包完整性；含本類模型使用 `/20` |
| b：重開與方案 | `space_modeling.py::replay_stored`、`scenario_verify.py::_model`、`reference-workspace.js::verifyStoredModel` 缺 profile 獨立重驗 | 三條路徑都核對明選的 `profile_runs`；`timbers` 是否驗證依 input 存在與否判定，不因 `/3` 跳過角材 |
| c：整筆更新 | `model_update.py::_selection/_record/_protected/PACKAGES/_diff/prepare_update` 缺 profile 明選、包與來源閉包 | plan selection 必填 `profile_runs`；全部包重算並產生完整差異，保留固定材料及來源關聯守門 |
| c：App 與原子提交 | `model-update-app.js::open/readPinnedSource/renderChoices/selection/renderReview/createController` 與 `model-update.js::selectionValid/checkedCandidate` 缺 run 清單與比對 | 原「採用現行來源…」入口明選、預覽、取消、重驗、整筆替換；由 `ReferenceWorkspace.updateSpaceModel` 保持同一 model id 與一筆歷史 |

## 2. 一般入口、預覽與確認

### 建立或選擇拉伸件

由 `#btnNewSectionProfile` 開啟原 `#sectionProfileWorkspace`。`#spProfileSelect` 選既有斷面；`#spNewProfile/#spNewMember/#spNewRun` 建立未提交表單。長度與定位仍在原工作區指定，`#spPlacement` 可選進階或簡易定位。`#spPreview/#spConfirm/#spCancel` 保持原生兩段交易；取消不改 World，確認以原生單筆歷史提交。

`#spBuildModel` 是獨立拉伸檢視，不是納入空間的確認鈕。空間牆面取值保留其已保存框架與範圍，不反向建立對某個保存空間模型的即時依賴。

### 由面建立空間

1. 開啟已放置的水平面，在屬性欄按 `[data-fp-build][data-fp-placement]`，進入唯一 `#smWorkspace`。需要時在原投影欄確認用途與俯視／仰視；明填牆底並核對牆高、外環邊、孔洞及封口用途。
2. 展開唯一 `#smTimberSettings` 的「一併納入」。`#smIncludeTimbers` 沿用原本此面角材選擇；`#smProfileCandidates [data-sm-profile-run]` 逐條列出同一來源快照的全部已定位 runs，**初始全部不勾選**。候選顯示 run id、斷面名、長度、構件數及定位來源摘要。
3. `#smProfileUnavailable` 列出已定位與未定位數量。未定位件沒有世界位置，不能選；不依空間範圍、宿主或名稱自動縮小候選，也不自動補入來源中未選的 run。
4. `#smPreview` 核對能力及來源後取得候選。`#smProfileReview/#smProfileReviewList/#smProfileVolume` 分別呈現 run／構件數、逐構件材料量、獨立總量及來源快照語意。合法已定位 run 即使有零個構件，仍是已納入的 run，構件數與材料量為零，不顯示成未納入。
5. 關閉或取消建模候選，World、保存模型紀錄與歷史保持不變。勾 `#smConfirmFaces` 核對既有面清單後，`#smCreate` 才可建立；只增加一個完整模型及一筆 local history，不把衍生網格寫回 World。

來源準備本身若須修改斷面、放置或投影，仍走各自既有確認與歷史。上述「取消零寫入」的比較起點是該次空間候選開始前，不撤銷先前已明確確認的來源準備。

### 顯示、保存模型與移除

`#smShowTimbers` 保留原 ID，文案為「角材與拉伸件」，共同控制兩類真正的 geometry mesh；包絡 reference 不畫入此模型，也不計材料量。`#smShowSpace/#smShowWalls` 及只作用於空間殼的 `#smShowRoof` 保持原義。顯示開關不改明選清單、不重算、不寫歷史。

角材與拉伸件的材料量分開呈現；不與空間體積、淨空或材料牆相加。拉伸件總量明示未扣拉伸件之間的重疊，並且沒有做碰撞、貼合或包含判定。原 `#smExportKind` 的 `timbers` 匯出仍只匯出角材包；完整 profile 包透過 `.gcanvas` 保存，本片沒有新增匯出選項。

`#smLibraryList` 保留原模型庫。`[data-sm-open-model]` 重開保存快照；`[data-sm-remove-model]` 移除整筆模型且可復原，不刪除 World 的斷面／run。`#smEditHeight` 修改牆高時使用原快照重算，不讀 live run，不搬移或裁短所納入的物件。

## 3. 精確輸入、結果及單一來源

建立 plan 的新增選用欄位：

```json
{"profile_runs":[{"kind":"profile-run","id":0}]}
```

未納入時省略欄位；明寫空陣列、重複、錯 kind、不存在或未定位的根均拒絕。run／member／placement 的 id 0 合法；這不使保留的 boundary id 0 成為可宣告具名邊界。faces 搭配 profile 明確拒絕，不能默默略過。

producer 以 run id 升冪發一次 `role=geometry,target=solid-set,allow_partial=false` 的 R39 請求。任何所選 run 不完整，整個模型建立或更新失敗；不得保留半套結果。

有 profile 時回應 `geometry-space-preview/3`，新增獨立 `result.profile_runs`、下述 `source_snapshot` 收據與以下 summary 欄位：

| 欄位 | 語意 |
|---|---|
| `profile_run_count` | 精確所選 run 數 |
| `profile_member_count` | geometry 構件數；不含 reference 包絡 |
| `profile_material_volume_mm3` | 各構件精確尺寸乘積的總和，十進位字串 |
| `profile_overlap_checked` | 固定 `false`；不宣稱扣除重疊或完成碰撞核對 |

同一 `/3` 可以同時有 `timbers` 與 `profile_runs`，兩個選用包獨立驗證。沒有 profile 而有 timbers 仍為 `/2`；兩者都沒有仍為 `/1`。舊五類包及其摘要語意不改。

`input.base_scene` 保留當次明選的去身分來源原文，包括註解與畫布展示位置。producer 僅透過原 `load_base` 取得 canonical 場景，並在 `/3` 的 `result.source_snapshot` 保存封閉欄位 `{schema:"geometry-space-source/1",input_sha256,canonical_scene}`。`input_sha256` 是原文 UTF-8 的 SHA-256；`result.source_sha256` 與 `source.scene_hash` 仍是原生 canonical 場景的 SHA-256。這兩個雜湊分別識別原文與幾何來源，不能互換。

`profile_runs.definitions.base_scene` 及同模型角材包須與 `canonical_scene` 完全相等，profile 的 `extensions` 須為空。空間殼、體積、淨空及材料牆會增添設定宣告，且原生會重新排序；同步守門要求原生 canonical 的每個非空完整行在各包恰出現一次，沒有在 JavaScript 刪除原始輸入的註解或 `canvas-pos`。此行檢查只證包間結構一致；I31 原生重播仍須從保存原文重建收據、完整 definitions/request/derived 及摘要，排除自填雜湊或額外定義造成的偽造。

一般建立與修改牆高在寫歷史前呼叫 `validateSpaceModelHashes`，驗原文、canonical 及 profile 包雜湊；非同步驗證後重新核對原 owner、設定、來源版本與歷史。整筆更新另核對候選的原文等於此次 `current_scene`，且收據的 input hash 等於候選已驗證的 `current_scene_sha256`。pack/unpack 與方案葉也重驗，不能把錯接來源留到保存時才拒絕。既有 `/1`、`/2` 不增添此 `/3` 欄位。

每個 run 恰有一個 reference 包絡，`member_id:null`、空 member path、材料量為 `"0"`。每個 geometry 成員保留 `(run_id,member_id)`、world 座標、方位、三個正整數尺寸、範圍、精確材料量與原生 face provenance。run id 或 member id 相同不表示與目前 World 物件延續。

## 4. 同版讀取、能力與 K3

建立候選以 `section-profile-read` revision 夾住去身分 dump／surfaces／references，並核對第二次 dump、context 與 history。預覽前後及建立前再驗同一來源；選擇、來源、專案或歷史改變後，舊候選失效。晚到回覆不能恢復已取消的候選。

I73 的能力宣告與 native `section-profile/1` 分開。`/model/capabilities.space_preview_schemas` 必須包含 `geometry-space-preview/3`；只有原生斷面能力不足。建立與含 profile 的 F1b 更新都拒絕能力不足，不能降級成不含 run 的模型。

模型來源快照使用去身分 dump，不帶 `requires identity-ledger/1` 或 identity 行。完整專案自己的 World 身分帳另依既有保存規則保留。

`source-inspector.js::modelRoots` 包含 profile-run 作內容新鮮度根；`untrackedModelRoots` 與 `[data-source-untracked]` 顯示其內容一致／已改／缺失／未確認及延續未知。`IdentityLedger.expectedRoots` 的 covered 白名單不變；不得把 profile-run 加成 pin 或新的 uncovered reason。已有合法 `sourceIdentity` 的 placement／boundary／角材／障礙等根，仍依原 K3 判 continuous／absent／replaced／conflict／unknown。

存在 run 時，`#muIdentity/#muName` 與來源檢查的文字須把已追蹤根的證明和 run 未知分清。勾選 run 當下即更新文字，不等送出候選；切換對話框清除舊 profile 選取，不能借用另一模型的選擇。

## 5. F1b：明選現行來源後整筆取代

一般入口保持「3D 模型庫 → 修改模型 → `#smCurrentSourceUpdate` 採用現行來源…」。`#muDialog` 沿原來源選擇、差異、確認與取消；沒有新增全域入口。

plan 的 `selection` 封閉欄位為：

```text
{placement_id,boundary_id,edges,obstacles,timbers,profile_runs,projection}
```

全部必填。`profile_runs:[]` 表示本次移除原模型所有 run；缺鍵不能當成繼承。`#muProfiles [data-mu-profile-run]` 全部需明選，`#muProfileCount/#muProfileUnavailable` 列選取數與未定位數。新 run 不會被 K3 的其他根預選規則帶入。

既有 faces 選擇仍為 `{mode:"faces",uses:[{placement_id}],obstacles}`，保留原 use 數、順序、orientation 及 purpose；本片不加入 faces＋timbers/profile。plan 的牆底、牆高、用途及厚度沿用舊模型，只有本次明選的來源、邊及內容更換。

`#muPreview` 產生隔離候選，`#muDiff` 顯示完整 source/input/summary、六類包 manifest 摘要，以及原角材與新增 profile 的實際幾何差異。preview 及 `#muClose` 取消都零寫入；`#muConfirmed` 核對後才啟用 `#muApply`。確認前重讀來源、重跑真 producer、核完整收據及 runtime，再同步原子替換同一模型；一步 undo/redo 必須完整回到前後紀錄。

producer 的 candidate/1 幾何收據與既有 K3 candidate/2 身分收據保留各自責任，不將暫時收據寫入保存模型。固定 material/method/rule 版本閉包及逐根關聯守門原樣適用：加入或移除帶固定材料來源的 run 若改變受保護集合，仍可回 `UPDATE_FIXED_VERSION`／`UPDATE_FIXED_ASSOCIATION`；本片不另開豁免。

## 6. 完整專案 `/20` 與重開

只有專案本身或方案葉含 profile 空間模型時，使用 `geometry-canvas/20` 並要求 `section-profile/1`。`project-store.js` 仍接受 `/1`–`/19`，不把既有 `/19` 當未知格式，也不因單有原生斷面而強制升 `/20`。空的 `/20`、降版藏入 profile、缺能力或未知欄位均拒絕。

新 envelope 保留 `/19` 的 room-candidate drafts、assembly bay-repeat 與 panel-fill 各自資料、能力及守門。重複開間專案的有限 native profile 憑證仍需完整提供；不能以單獨 PF reader credential 冒充。模型 adapter 既有來源能力限制保持，接受同一專案共存不等於允許每類 World 能力進入每一個模型包。

profile 保存核對來源 snapshot hash、package definitions hash、geometry hash、typed roots、schema、摘要及幾何 metadata。三條獨立重放是：

1. `space_modeling.replay_stored`：按保存輸入重新推導並比對完整結果。
2. `scenario_verify._model`：核對方案葉中的模型、原文／canonical 收據及同源選用包，保留合法 K3 sourceIdentity。
3. `ReferenceWorkspace.verifyStoredModel`：完整專案匯入時逐包 native verify，核返回 definitions/request/derived，再呼完整 space replay；全部通過後才替換目前專案。

任一驗證失敗都保留目前 World、非空專案、來源附件及歷史。source.boundary_id 的新 profile 規則為具名正整數或真正內含矩形的 `null`，不能用 `0` 或 `null` 冒充具名邊界。

## 7. 範圍與減項

本片只做 Q38j(a)(b)(c) 的 plan 第一片與原本已存在的來源能力。不做 faces＋profile、World 即時跟隨、依位置自動歸屬、拉伸件碰撞／貼合／包含、扣交會重疊、施工或力學判定、折線路徑、斜接、料長續接、新材料／斷面內孔、R13 的 reconstruction-data／C／D 接線。

GEO-219 的具體減項：原角材獨立「核對角材尺寸與世界高度」disclosure 改為同一「一併納入」內的普通清單，與新增 run 共用一個 disclosure；保留角材清單 ID。原 `#smShowTimbers` 合併承接角材與拉伸件，沒有第二個 visibility 開關。F1b 原角材 disclosure 改為兩類材料共用的「一併納入」，保留原 preview／confirm／cancel 和單一模型修改入口。

## 8. 驗收與證據狀態

下表是 2026-11-15 原始候選的歷史交付記錄，不改綁為 2026-11-17 的 #430 修補收據。#430 的修補另以該 PR 留言所附的固定來源、逐案原件與完整補丁身分核對；原始及修補後的測試數有增加。雲端啟動前的 `socket() EPERM` 不屬於產品紅，也不能作為瀏覽器通過；本修補仍須在正式 runner 補齊 space／timber 及六個 browser 撤回。

| 層次 | 必須取得的證據 | 本文件狀態 |
|---|---|---|
| 原生／Node | Q38j 正負例、精確 oracle、來源與包 tamper、K3／舊格式、三條 replay、固定材料守門 | 新 Python 33；前端整合單次 130；UI／faces／K3 另一輪 68；保存／重開／方案 35；舊格式與 K3 65，均零失敗、零 skip。這些執行範圍有重疊，不相加成完整 runner |
| 先紅後綠／具名撤回 | 同一 judge 對固定基底紅、候選綠；撤關鍵接線為 0／1／0，具名 assertion 失敗，不接受 import、timeout 或 skip 冒充 | a／b／c 有指定斷言紅綠；c 只替換基底更新模組，兩側共用完成的 a prerequisite。原生 26、工作區 26、更新前端 11、保存專項 7 個具名變體全為 0／1／0；原始收據與 hash 隨 issue 交付 |
| 真瀏覽器 | 一般入口、選取、取消、單步歷史、F1b、完整下載／冷開、來源 race、能力不足與 1400／690／390px | **阻擋**：凍結副本完成 fresh native build，但 Chromium 在 CDP／產品頁之前因 `socket() EPERM` 中止。產品斷言未執行，六個 browser 撤回全為 unrun；source census 不能當通過 |
| 完整整合 census | 原 finite groups／canvas golden／分片守門及所需 native registry 全量核對 | **待最終完整核對**；局部綠不相加成 full |
| 正式 mutation evidence／衍生檔 | 依原 `tests/mutate.py --check`、架構與閱讀器工具，綁最終來源／裁判／夾具 | 原正式帳本 138 筆中 68 stale，待採用分支真 CI 原件；沒有改帳本或三份架構產物。本地 scanner 零診斷、產品架構 18 綠；閱讀器原工具重建／check 五 assert 通過、53 tests 綠，HTML bytes 與基底相同 |
| L4 | 由實際 App 一般入口走完聲稱範圍並保留讀回／操作證據 | **未由本文宣稱通過** |

新瀏覽器 group 為 `profile-space`，`profile_space_test.js::CASES` 與 `space_test_floor.js` 明訂 **60 個具名斷言**，完整 Space 及 `GEOMETRY_SPACE_PROFILE_ONLY=1` 都呼叫同一 group。專項模式另有原 setup 2、browser-health 2；必須逐 group 恰合、`completed:true`、程序成功且無例外，不能只看總數。

原 `space-height-library/projection-lifecycle/projection-placement/projection-close/font-layout/space-flow/timber-material/timber-source-guards/timber-history-guard` 的預期數保持 `112/18/36/14/19/39/48/8/5`。原 canvas golden 與分片檔是 `geometry-web/cdp_sections.golden.json`、`geometry-web/canvas_shards.json`，本片不更動；profile-space 屬 Space census，不新增 canvas P 段。`tests/test_profile_space_browser_contract.js` 只驗 source census／接線／語法，不能替代瀏覽器。

F1 數值 oracle 使用三個 27×33 構件、PR1 長 2400、世界原點 `(1000,2000,2700)`、N=+Y、V=−Z。每件材料量為 `2,138,400 mm³`，合計 `6,415,200 mm³`；幾何逐值另核 M1 x[1000,1027]、M2 x[1373,1400]、兩者 y[2000,4400]／z[2667,2700]，M3 x[1000,1033]／z[2450,2477]。再選 PR4 的材料合計為 `9,088,200 mm³`，保持未扣重疊。

## 9. 層級與 L4 操作路徑

固定基底的 [需求帳 R12](../../需求帳.md) 記規格 L1、原斷面工作區 L3。本次 issue 補丁本身沒有實作 PR，不能把 Q38j 升為 L2；實作 PR/head 出現後記該切片 L2，合進 main 並有 merge SHA 才 L3，實際 App 核對後才可記 L4。本文不改需求帳的層級，也不把原 F1b 的 L4 收據移作 Q38j 收據。

L4 應由 `geometry-web/start.ps1` 一般入口啟動並依 GEO-231 核對版本，依序操作：

1. 建立或開啟專案；由「建立物件 → 斷面與拉伸」建立／選斷面、構件、拉伸長度與世界定位，走原預覽、取消及確認。
2. 回到面，從屬性「以此面建立空間」選合法水平來源，確認投影用途與觀看方向，明填牆底及牆高。
3. 在唯一「一併納入」明選 run，核預設不選、未定位不可納入，與既有角材同時選取；按預覽逐值核材料量、兩種材料顯示及來源快照標示。
4. 取消並比對 World、模型紀錄與歷史零變更；重新預覽、核對、建立，再一步復原／重做。
5. 從模型庫改牆高，核所選 run 的位置與幾何不變；取消保留舊紀錄。再走「採用現行來源…」明選 run、預覽、取消、確認及一步歷史；明示空清單可移除 profile 包。
6. 由原檔案操作另存完整 `.gcanvas`，新空專案及新頁面後冷開，核原生斷面／runs、同一模型的 input/source/全部包與方案葉均保持。保存 run 是來源快照，live 來源修改或刪除不改舊模型。
7. 核對讀取中來源改變、預覽後改設定、能力不足、舊候選取消及錯包拒絕；在 1400、690、390px 走同一可見路徑，記錄所需 pointer／鍵盤可達性。

瀏覽器自動化的頁面重開與真下載檔案，不等於作業系統原生選檔視窗、另一次服務啟動、實體手機多點觸控、IME 或使用者驗收；這些若未操作，必須分別列為未驗。
