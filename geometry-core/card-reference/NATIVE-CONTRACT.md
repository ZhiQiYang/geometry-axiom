# grid-card-reference/1：核心切片 A

依 #250 `f3f99a29` 採納內容與 #253 P-133。#193 是必要基底：最後刪除之後的明確重新宣告使用原有 I38 守門。
核心不依賴卡片名稱、領域範本、欄位順序或尺寸大小。正式條文與版本常數由任務 19 維護，本切片不改寫 SSOT。

## 一份來源及原生語法

`GridSystem.card_reference` 保存 set、parameter_id、fields[2]；沒有獨立 World id、swap bit 或 incarnation。
兩軸 card_length 是來源標記；既有 step/panel 欄位只是求值快取，序列化只輸出 `card`，不輸出有效長度或隱藏舊來源。
其他 phase/gap/anchor/stagger 的直接值與 ParameterRef 保留。

```text
requires parameters/1
requires grid-card-reference/1
# 來源卡片仍由原有 parameters begin/card/field/end 保存，位於網格之前
grid-system 4 name-hex 47 main-along none card-reference 10 3 8 u repeat -5 card v repeat 7 card
```

`card-reference P U V` 與兩個 `card` token 必須完整，兩軸只接受 repeat/repeat-panel。
例如 u 可為 `repeat-panel card gap param:10:9 from -5`；phase/gap/anchor 不從整卡推斷。
新語法即要求兩項能力；缺少其中宣告或未知版本，場景在替換 World 前拒絕。
舊 parameters/1 的既有能力補註例外保持；舊直接值、逐欄與有限網格不轉換。

## JSON 候選與讀回

沿用 `engineering-transaction/1`、expectedRevision、engineering-preview/confirm/cancel。
操作都只改候選；出口先檢 I38 最後刪除，再清除順序及捕捉 scratch，完整重算全部依賴，確認時再重驗，一次 history。

| op | 其餘欄位 |
| --- | --- |
| put-grid-system | value：`{id,name,mainAlong,u,v,cardReference?}`；mainAlong 為 none/u/v，u/v 是完整既有軸 DSL 字串，cardReference 是下列三欄物件 |
| set-grid-card-reference | id、value：`{parameterId,uFieldId,vFieldId}`；兩軸既有長度來源明示整組取代 |
| swap-grid-card-reference | id；只交換 fields[0]/fields[1]，重新驗 stagger 等全部限制 |
| unbind-grid-card-reference | id、mode：parameter 或 direct；一次轉兩槽，其他來源不變 |
| parameter-package | operations：僅 put-parameter/delete-parameter/import-parameters；整包讀完及求值，不接受包內插入解除 |

put-grid-system 是完整宣告，包含其他維持不變的軸設定；不補 phase、gap、anchor 等缺欄。
定義的缺欄、未知鍵與 mainAlong 型別／值錯誤使用 `D29 GRID_DEFINITION` 並指名網格；卡片映射缺欄才使用 `I74 COMPLETE_MAPPING`，保留兩種拒絕原因的區別。
已有整卡時，完整宣告若改成直接／逐欄而未先明示整組解除，亦拒絕同值 token，不能暗拆。
明確重新宣告整卡來源使用獨立的 PARAM_OWNER_GRID_CARD；只對調／改綁整卡不會替其他逐欄來源蓋章。
完整 put-grid-system 另對其實際宣告的逐欄來源記錄宣告。沿用 #193 的最後欄位刪除序列與每一引用者判斷，不更改匯入配號。
轉成逐欄也明確宣告兩個新 ParameterRef：ordinary grid-system owner 的 slot 0 表示完整軸宣告，slot `axis*6+field+1` 只表示指定槽（field 次序 phase/step/panel/gap/anchor/stagger）。刪卡重建後的整組轉逐欄因此合法；它不會順帶處理原有 phase/gap/anchor 等其他引用。

### 與面材試排共用 I38 使用處（P-142 B2）

整卡引用者（`grid-system N card-reference u|v field F`）與 #193 P-141 的面材試排 gap／stagger／threshold 引用者，
都在 `parameters.inc` 的同一個 `parameter_uses()` 列舉，並由同一個 `parameter_retirements_valid()` 在所有候選出口（engineering、assembly、section-profile、panel-fill 共用 `batch_preview`，及互動 archive）做 I38 刪除拒絕；沒有第二套列舉或拒絕。
面材試排沒有混合候選改綁入口，仍是「另成一筆後再刪」的原生擁有者；同一欄位若同時有整卡引用者，拒絕訊息在 `(other references: N: …)` 內一併指名可在本候選處理的引用者，符合 I74「指名未處理者」。
本 PR 對 #193 的 I38 拒絕訊息共三處改動，指引文字本身不變：B2 在原生擁有者領頭的訊息內指名同欄可改綁的引用者（#193 原本只計數）；B2 審查後兩種訊息的名單都受 255 bytes 上限約束（見下段）；S1 把 grid-system 逐欄引用由原生擁有者改列為可同候選改綁（見下節）。
`test_P142_B2_CARD_AND_PANEL_FILL_{GAP,STAGGER,THRESHOLD}_SHARE_I38_REJECTION` 驗三種面材引用：兩種擁有者同則指名；本候選解除整卡後只剩面材擁有者；面材在自己的交易改指後只剩整卡擁有者且改用同候選指引，最後解除＋刪卡可提交。
I38 訊息經 `g_engineering_error`（256 bytes）回報。原生與非原生訊息的每份名單都只放剩餘長度容得下的**完整**名稱，其餘寫成 ` and N more`；連一個名稱都放不下時只留計數。整則保證不超過 255 bytes，不會把 `field 12` 截成 `field 1`。
`test_P142_B2_LONG_OWNER_LIST_KEEPS_COMPLETE_NAMES` 以 10 位數欄位／網格 id、三個整卡引用者加面材 stagger（未截斷全文超過 255 bytes）驗證：列出的每個名稱完整且欄位 id 與實際相符，`and N more` 補足精確數量。M84（拿掉剩餘長度檢查）已登錄 `tests/mutate.py`，待原生帳本重產。
M78（不指名同欄引用者）、M79（整卡引用者漏列）以這三個方法為裁判；兩筆已登錄 `tests/mutate.py`，待原生帳本重產，目前帳本尚無其紀錄。

### 網格系統逐欄引用可同候選改綁（P-142 S1）

#193 合併時網格系統沒有候選宣告入口，所以它的逐欄引用歸在「另成一筆後再刪」的原生擁有者。
本 PR 的 `put-grid-system` 以 slot 0 宣告整個網格系統，`unbind-grid-card-reference` 的 parameter 模式宣告 `axis*6+field+1`；
因此 `parameter_uses()` 把網格系統逐欄引用改列為可在同候選解除或改指的引用者，拒絕訊息改為 `unbind or repoint … in the same complete candidate`。
guide、datum、direct grid 與面材試排仍是原生擁有者，沿用 #193 的「另成一筆後再刪」指引（名單格式依上節 B2）。
`test_P142_S1_GRID_SYSTEM_FIELD_REBIND_IN_SAME_CANDIDATE` 以原生 DSL 建立逐欄網格系統：只刪卡、刪卡＋同鍵重建都以 I38 拒絕並指名 `grid-system 4 u step`；
同候選 `put-grid-system` 改指到另一張卡可提交；刪卡＋同鍵重建＋`put-grid-system` 明示重宣告可提交，預覽 `redeclaredReferences` 列出 slot 0 的兩個欄位。
反例 `test_P142_S1_REDECLARATION_WITHOUT_REBUILD_REJECTS`：`[delete-parameter 10, put-grid-system 仍指向 10]` 沒有重建來源；刪後宣告滿足刪除守門的順序，所以由網格求值的缺來源以 I38 MISSING 拒絕並指名 grid-system 4、parameter 10、field 3，World 不變。M85（指向已刪卡片時沿用快取長度）已登錄 `tests/mutate.py`，待原生帳本重產。
`test_parameters_core` 的原生擁有者對照同步把 grid-system 改為非原生。M80（網格系統仍歸原生）、M81（put-grid-system 漏宣告逐欄來源）已登錄 `tests/mutate.py`，待原生帳本重產。

合入 #193 的 P-142 S2 修正後，逐欄 `unbind-source` 與整卡 direct 解除在同一有序候選讀同一個當步來源：
`test_P142_S2_INTEGRATED_FIELD_AND_CARD_REBUILD_READS_99` 對同一張卡執行 `[delete P, put P(a=99, b=47, f9=99), 整卡轉直接值, unbind-source(timber A)]`，
整卡捕捉與正式長度為 (99, 47)、角材讀 99（不是刪除前快取 27），一次 history。M82（已重建欄位仍走刪除快取）、M83（整卡因曾刪除一律拒絕）已登錄 `tests/mutate.py`，待原生帳本重產。

direct 解除只在該有序步驟依原生參數 evaluator 重算必要欄位並驗整卡。
該步來源存在時取當下有效值，包括刪除後已重建的同鍵來源；例如 `[delete P, put P(a=99), 轉直接值]` 取得 99。
該步來源不存在（刪除未重建）或來源不合法時拒絕，不因同候選曾刪除而一律拒絕。
不讀畫面鏡像、正式舊 World、刪除值快取或後續卡片修改。
預覽 `cardCaptures` 明列 gridSystemId、parameterId、兩個 fieldId、values[2]、timing=ordered-candidate-step 及候選事件 order。
捕捉紀錄只在預覽序列化副本內，確認後不進 World、dump、定義指紋或 history。

### 捕捉 scratch 的固定記憶體成本

`measure_capture_memory.py` 用真核心型別及同一份 ParameterState 宣告移除捕捉成員的對照量測。
雲端 Linux x86-64／gcc 14.2 ABI 下，GridCardCapture 為 40 bytes，256 格陣列為 10,240 bytes，count 為 8 bytes；每份 World 固定增加 10,248 bytes。
P-146 量測來源 `417ea06d` 的 World 共 3,178,472 bytes、ParameterState 為 813,632 bytes；這些是該來源與 ABI 的實測大小，不是後續合入 main 或跨平台 ABI 的大小保證。
`HISTORY_MAX=32`，Undo 與 Redo 兩個固定陣列共 64 槽，捕捉成員合計增加 655,872 bytes；正式 World、預覽及其他快照的額外空間另計，不能把這個數字當成整個程序的增加量。
上限 256 對齊 `ENG_OPERATION_MAX=256`：每個有序操作最多產生一筆整組 direct capture；parameter-package 不允許插入解除。
`parameters_clear_candidate_scratch` 會在 staging／比較／history 前清零陣列及 count；歷史不保留捕捉內容，但 World 內的固定配置空間仍隨每份快照存在，沒有宣稱記憶體成本為零。

**GEO-261 整合後**（本段以上描述 main 單層版本，量測工具 `measure_capture_memory.py` 也只適用那個版本）：
GEO-261 已移除 `World.parameters`／`ParameterState`。捕捉紀錄改放在 H 的 `ParameterCandidateLedger`（`parameters.inc`，與宣告、欄位退場同一份候選 scratch），
只在一個受追蹤候選的生命期內以 `calloc` 配置，`parameters_end_candidate` 時釋放；World、K 儲存、候選封印、history 與交換格式都不含它，
所以每份 World／history 快照不再固定增加上述 10,248 bytes。上限 `PARAM_CARD_CAPTURE_MAX=256` 與預覽 `cardCaptures` 的內容、順序不變。
分層位置：`GridSystem.card_reference` 與各軸 `card_length` 是 K 格網儲存（`kernel/grid_store.h` 的 `GeoGridCardReference`）的定義欄位；
兩個受控長度由 K `geo_grid_system_evaluate`（同一 resolver，在逐欄 ParameterRef 之前）求值，`geo_grid_system_resolve_card` 供 R60 direct 解除在該有序步驟重算；
I74 診斷文字由 W `wood_grid_card_error` 產生；W 的格網定義編碼（`grid_definition_codec.c`、`grid_sources.c`）帶整卡映射與 `card_length`，受控槽在 authored 線上與 ParameterRef 槽同樣遮蔽；
JSON 操作、場景語法、bridge 與 I38 引用者列舉留在 H（`card_reference.inc`、`grid_systems.inc`、`parameters.inc`、各 bridge）。

objects 的 gridSystems、原生預覽及 engineering 候選 after.geometry.gridSystems 均回一份 cardReference。
受控槽回 stepSource/panelSource=card，另回唯讀 effectiveStep/effectivePanel；該槽沒有 step/panel 直接值或 ParameterRef。
parameterUses 回一個 kind=grid-card-reference 的使用單位，內有兩條 fieldId/axis/slot 路徑，不用兩份逐欄使用處冒充。
唯讀 source-inspect 亦保存卡片單位與兩條實際欄位路徑。其定義指紋含映射而不含有效長度；同值對調改定義指紋，改來源值只改有效值指紋。這是原生 bridge 索引，不新增 UI 或變更幾何根走訪。

## 保存、格式與 P-133

完整專案分配 `geometry-canvas/18`，沿用 /17 的全部附件政策，只在整卡資料需要時提升；/1–17 原義保持。
world.scene 與 manifest.requiredCapabilities 兩處都須保留 grid-card-reference/1、parameters/1。
只存在於方案快照的整卡來源亦向根專案傳遞兩項能力並使用 /18；既有隔離驗證器的有限能力白名單同步識別此能力，仍拒絕未知版本。
JSON 模型包仍使用 geometry-model-package/1，新增明示能力；完整 canonical base_scene 保存來源、映射及卡片傳遞依賴。
依 P-133，幾何走訪不必列網格；model_base.c 只新增能力序列化，沒有修改幾何依賴折疊。
verify_package 仍從來源重算幾何及摘要；不得輸出兩個常數或兩份 ParameterRef 代替 CardReference。
geometry-parameters/1 的匯出／匯入仍只有卡片閉包，不包含網格，不新增 D55 根種類。

### 採納前模型包的版本防線（P-142 B1）

D64／I74／R60 於 #256 的提交 A `b3c79615` 採納；#266（GEO-261）之後執行器版本改指 `e744f531`（LF 雜湊 `18a9a75b…`），`b3c79615` 成為 `PRE_DECOUPLING_AXIOM_VERSIONS`。
整卡語意的年代因此分成三段：現行版本，以及 `CARD_REFERENCE_AXIOM_VERSIONS` 內已含 D64／I74／R60 的執行器版本（採納提交 `b3c79615`，與 #260 採納前最後一個發佈到 main 的 `e744f531`），可帶整卡；
`_pre_card_reference_versions()` = 允收集合 − 現行 − `CARD_REFERENCE_AXIOM_VERSIONS` 的 19 組版本早於 D64，只有在未宣告且未使用整卡能力時才相容。
這 19 組恰等於 a898ad6e（當時現行即 `b3c79615`）凍結的 `historical-versions.json` 全部家族，可獨立核對。日後若再有採納讓現行版本退為舊版，須把它加入 `CARD_REFERENCE_AXIOM_VERSIONS`，否則其整卡包會 fail closed。
#260 的採納（現行改指 `a00ba9e9`，LF 雜湊 `7794a778…`）即是這種情形：它退役了 `e744f531`（`PRE_ONE_AXIS_STAGGER_AXIOM_VERSIONS`）。
`b3c79615`、`e744f531`、`a00ba9e9` 三版的 D64／I74／R60 區塊逐位元組相同，三版之間改的字（A/B 一軸錯縫、I5/R18、I23/R13 標題括號、D31/R33 cardId→parameterId）都不在整卡條文內，
所以 `CARD_REFERENCE_AXIOM_VERSIONS` = `b3c79615`、`e744f531` 兩組。#318 閱讀 A（現行改指 `0fd8cacf`，LF 雜湊 `c66c48e5…`）只改 D11、I19、R6，不動整卡條文，所以再把退役的 `a00ba9e9` 加入（`PRE_READING_A_AXIOM_VERSIONS`），成為三組。`tests/test_engineering_model_compatibility.py` 的 `CARD_CLAUSE_SHA256` 記錄 D64／I74／R60 區塊的 SHA-256：
測試只實算現行 `公理層.md`，現行條文的這三條一動即轉紅，清單內多一組而沒有記錄雜湊也轉紅；三個歷史版本的雜湊是整合時以 `git show` 逐版核對後記錄的（三版相同），測試不重算。
這道雜湊只是絆線，不是完整的整卡語意守門：它只涵蓋三條的條頭區塊，其他條文行中帶整卡語意的句子（例如 D29、D25、I38、R33 內提到 D64／I74 的行）改了不會轉紅。日後升版、要把版本加進 `CARD_REFERENCE_AXIOM_VERSIONS` 時，仍須人工審過全部提到 D64／I74／R60 的行。
#309 提交的執行器版本 `0d9015bc`（LF 雜湊 `f10ef7ca…`）不在其中，也不在允收集合：#309 只以 merge commit 第二親代進 main，main 的 first-parent 狀態從來沒有宣告過它（P-181），依「過渡版本不列入」的先例刻意不收，帶它的包回 `UNSUPPORTED/AXIOM_VERSION`。
`verify_package` 在重建之前檢查 manifest.capabilities 與 base_scene 的能力宣告／整卡語法；任一出現 `grid-card-reference/1` 語意即回 `UNSUPPORTED/AXIOM_VERSION`。
兩處能力宣告都被移除但仍有 card-reference／card 語法，也不能藉此套用舊版公理。
現行版本的完整整卡包仍可原樣重建；未知或混搭版本仍由原有精確版本配對拒絕。

`tests/test_engineering_model_compatibility.py` 的五個具名方法涵蓋三條拒絕路徑、現行完整包與全部舊版無整卡對照；
GEO-261 合併後另加三個：年代分割等於凍結允收集合（純 Python）、以 a898ad6e 原件加整卡宣告在重建前驗證 19 組舊版全拒且 `b3c79615` 放行（純 Python，以 mock 截在重建前）、`b3c79615` 版整卡包原生重建只更新版本欄位（需原生）。
#260 列車再把後兩者擴為逐一檢查採納提交與被退役的 `e744f531`（`b3c79615`、`e744f531`；清單寫死在測試裡，不從 `modeling` 讀回），並加三個：純 Python 的版本閘測試、`0d9015bc` 必須以 `AXIOM_VERSION`（通用訊息，不是整卡閘的訊息）被拒的測試、D64／I74／R60 區塊雜湊釘住的測試；失敗訊息都指名版本配對。
`run_axiom_mutations.py --output <新目錄>` 實際撤除整道防線、漏查 manifest、漏查來源、豁免最後一個採納前版本家族，或把整個採納後集合（V05）當成採納前；每筆要求具名斷言轉紅、沒有 error／skip，逐 byte 還原後完整相容性 suite（44 題）回綠。
每個變異的目標字串必須在原始檔中恰好出現一次，否則該工具以「目標字串遺失或不唯一」的訊息停下，不會拿未變異的原始碼冒充變異。
該工具以 `\n` 比對多行目標，需在 LF 行尾的檔案上執行（Windows 簽出為 CRLF 時，先用 `core.autocrlf=false` 另行簽出）。

## §7 整卡突變在 GEO-261 之後的錨點

`run_mutations.py` 執行 `mutations.py` 的 53 筆突變（現為 67 個 patch）。開跑前，它會逐一確認每個 `old` 字串在原始檔中恰好出現一次，有一個不符就停。

GEO-261 把整卡規則搬到 K／W／H 之後，main `4b975a3d` 這張表有 26 筆突變（29 個 patch）在整合分支上找不到錨點，runner 在 M01 就停了。下表列出這 26 筆的改錨位置，條件是每一筆都打同一個 CR 案例、同一條規則、同一種錯誤。

- 行號是改錨當時的位置，只用來定位。runner 只做字串的精確比對，不讀行號。
- 判定 killed 的準則（`run_mutations.py`）沒有改。
- 其餘 27 筆的錨點沒有改。其中 4 筆的注入程式碼改用新 API，見下方「錨點仍在、注入碼編不過的 4 筆」。

| 突變（CR） | main `4b975a3d` 原本打的位置 | 整合分支改打的位置 | 為什麼是同一條規則 |
|---|---|---|---|
| M01（CR01） | `card_reference.inc:50` `*old=s;` 存入後改成兩個 ParameterRef | `card_reference.inc:50` `GeoGridStoreError detail;` 之前，對要存入的 `s` 做同樣的轉換 | 同樣是 put-grid-system 把整卡存成兩個獨立的 ParameterRef，幾何結果相同。GEO-261 改成先編輯複本，再經 `app_grid_system_redeclare` 寫回 K。 |
| M02-order／name／value（CR25） | `card_reference.inc:41` `grid_card_system` 找既有系統之前，依欄位順序、名稱或數值重排映射 | `card_reference.inc:47` `world_find_grid_system` 之前，做同樣的重排；名稱改由 `geo_parameters_fields` 讀取 | 同一個函式的同一個時點，同樣把使用者明確指定的 (8,3) 映射改掉。 |
| M03-distinct（CR07） | `grid_systems.inc:73` `grid_card_resolve` 的 DISTINCT_FIELDS 判斷 | `kernel/grid_store.c:278` `geo_grid_card_resolve` 回傳 `GEO_GRID_STORE_CARD_FIELDS` | 同一個兩欄必須不同的判斷，已搬到 K resolver。I74 文字改由 W `wood_grid_card_error` 產生。 |
| M03-complete（CR11）、M03-same-card（CR07） | `card_reference.inc:10/11/13` 的 JSON 讀取 | `card_reference.inc:13/14/16` 同樣的判斷 | 只是 `eng_json_*` 改名為 `geo_json_*`，邏輯沒變。 |
| M04-source（CR11） | `grid_systems.inc:76` SOURCE_EXCLUSIVITY | `kernel/grid_store.c:284` `GEO_GRID_STORE_CARD_EXCLUSIVE` | 同一個單一來源守門，已搬到 K resolver。 |
| M04-token（CR31） | `grid_systems.inc:333` 場景重宣告拿掉整卡時的 CONTROLLED_TOKEN_REJECT | `grid_systems.inc:230` 同一個函式，改成比對候選複本與正式的 `previous` | 同一個場景 DSL 守門。 |
| M05-dimension（CR08） | `parameters.inc:71` `parameter_value` 的 dimension 檢查 | `kernel/parameters.c:36` `geo_parameters_dimension_value` | evaluator 已搬到 K。H 仍把 `GEO_PARAMETER_NOT_DIMENSION` 格式化成 `not a dimension`。 |
| M05-positive（CR09） | `grid_systems.inc:79` POSITIVE；`:21`／`:22` 兩個軸驗證器 | `kernel/grid_store.c:288` `value <= 0`；`:203`／`:204` `geo_grid_axis_valid`（panel 改名為 body） | resolver 與軸驗證器都已搬到 K，三處要一起放寬，才會讓 ≤0 的卡長通過。 |
| M05-integer、M05-range（CR09） | `parameters.inc:78` `parameter_coord`；range 另打 `grid_systems.inc:21` | `kernel/parameters.c:42` `geo_parameters_coordinate`；range 另打 `kernel/grid_store.c:203` | 同一個整數 mm／D1 判斷，已搬到 K。 |
| M05-precision（CR10） | `parameters.inc:17` `parameter_mul` 的溢位檢查 | `kernel/exact.c:21` `geo_integer_multiply` | H 的 `parameter_mul` 與 K evaluator 都委派給它。 |
| M06-extra-field（CR06） | `parameters.inc:208` AST `ref` 缺欄位時回 MISSING | `kernel/parameters.c:88` `geo_parameter_eval_ast` 同一分支 | AST evaluator 已搬到 K。突變同樣把缺欄位當成 7 mm。 |
| M07（CR12） | `engineering_bridge.inc:159` `batch_preview` 重驗之後、檢查未放置角材之前，把失敗的候選寫回 `g_world` | `engineering_bridge.inc:160` `app_batch_candidate_apply` 的同一點 | 這段順序已移進 candidate evaluate callback。破壞的仍是同一個原子性。 |
| M10（CR15） | `grid_bindings.inc:74` 第一迴圈只跑第一筆 | `grid_application.c:138` W `wood_grid_bindings_rebuild` 的同一個迴圈 | H 的 `grid_bindings_rebuild` 已改為委派給 W。 |
| M11-expiry（CR17） | `engineering_bridge.inc:174` confirm 的過期判斷 | `engineering_bridge.inc:198`、`kernel/candidate.c:207`（base_revision）、`app_candidate.c:128`（`equal(live,before)`） | 見下方「M11 的三層」。 |
| M11-revalidation（CR17） | `engineering_bridge.inc:176` `world_revalidate(&g_preview.after)` | `engineering_bridge.inc:200`（`app_world_candidate_revalidate`）、`app_candidate.c:127`（after 雜湊）、`kernel/candidate.c:118`（current 摘要） | 見下方「M11 的三層」。 |
| M11-undo（CR17） | `current_geometry.c:4089` `history_undo` 的 restore | `current_geometry.c:3031` `history_undo` 呼叫 `app_history_undo` 的前後 | 同樣讓 undo 只還原 u 欄、v 欄留在對調後。 |
| M13-unused（CR19） | `grid_systems.inc:391` dump 迴圈 | `grid_systems.inc:267` 同一個迴圈，改走 K store | 同樣讓沒有被綁定的網格系統不寫入 dump。 |
| M14-legacy（CR21） | `grid_systems.inc:90` 重建迴圈裡、解析整卡之前，就地把同卡的兩個 ParameterRef 併成整卡 | `grid_systems.inc:30` H `grid_systems_rebuild` 進入 W 之前，對 K store 做同樣的合併 | GEO-261 的 K／W 求值只在候選自有的解碼複本上進行，只把快取槽寫回，碰不到 authored 定義。所以「重驗時靜默改寫舊定義」唯一的位置，是 `world_revalidate` 每個候選都會呼叫的 H 重建入口。 |
| M18-closure（CR29） | `parameters.inc:746` `parameters_dump` 的卡片迴圈 | `parameters.inc:795` 同一個迴圈，改走 K parameter store | 同樣只輸出整卡直接引用的卡片，丟掉遞移閉包。 |
| M18-capability（CR29） | `model_base.c:401` required_capabilities | `model_base.c:360` `model_legacy_snapshot` 的同一行 | 函式已改名，參數改成 `const World *`。 |
| M20（CR30） | `grid_systems.inc:165` stagger 重驗 | `kernel/grid_store.c:241` `geo_grid_axis_stagger_valid` | 同樣讓整卡系統跳過 D10b 重驗。 |
| M22（CR32） | `parameters.inc:380`（不變）＋`:365` 的 `!parameter_field_generation` 重用判斷 | `parameters.inc:431`（不變）＋`:352` H 的 `parameter_rebuilt_key` callback | 重用判斷已改由 K `geo_parameters_accept_rebuilt_field` 執行，它向 H 詢問這個鍵是否在本候選刪過。突變讓 callback 在受追蹤的候選內一律回答「是」，等同 main 的 `!w->parameters.tracking`。 |

### M11 的三層

main 的 confirm 只有一道判斷。GEO-261 把它拆成三層，三層都會擋：

1. bridge 的 `batch_confirm`。
2. H 的 `app_candidate_check`：比對 before／after 雜湊，以及 `equal(live,before)`。
3. K 的 `geo_candidate_check`：比對 base_revision 與 current 摘要。

`app_world_candidate_revalidate` 與 `app_world_candidate_publish` 都會再呼叫第 2、3 層。所以只拿掉其中一層的突變，仍會被其他層擋下。

- **M11-revalidation**：CR17 的探針在 seal 之後，竄改待確認 after 的 K binding。只拿掉 `app_world_candidate_revalidate`，publish 仍會因 after 雜湊不符而拒絕，世界不變。這是等價突變；Windows 實跑的結果見下方〈本機驗證〉。突變改成同時拿掉重新求值與 seal 完整性檢查：被竄改的 after 會被發布，與 main「confirm 不重驗」的錯誤相同。
- **M11-expiry**：只拿掉 bridge 那一道，過期的預覽仍會被第 2、3 層以 INVALID 擋下，只有錯誤碼與 STALE 不同。突變改成同時拿掉三層的過期判斷：過期的預覽會被確認成功，與 main 的錯誤相同。

這兩筆因此各從 1 個 patch 變成 3 個，總數由 63 變為 67，每個 patch 都恰好出現一次。

### 錨點仍在、注入碼編不過的 4 筆

M14-import（CR22）、M17（CR13）、M19-axis-scope（CR13）、M19-partial-owner（CR27）的 `old` 錨點仍恰好出現一次，所以錨點檢查抓不到它們。但它們注入的 `new` 程式碼用到 GEO-261 已移除的 `World.parameters` 與 `eng_json_*`，突變原始碼編不過，runner 會在編譯階段停下。

修法只改 API 名稱，錨點與語意都不變：

- `w->parameters.cards`／`card_count` 改為 `geo_parameters_cards`／`geo_parameters_card_count`；
- `eng_json_*` 改為 `geo_json_*`；
- 候選宣告改從 H 的候選 ledger（`parameter_ledger(w)->declarations`）讀取。

### 本機驗證（Windows／MSVC，不是正式結果）

2026-10-19 以 `run_mutations.py` 的 Windows 移植版，在拋棄式複本上實跑。

- 移植版用同樣的預檢與 killed 判準。紅燈在突變原始碼還在時跑，CR17 探針與修改測試檔的突變都會讀到突變後的檔案。CR17 的 `cc` 只在子行程中改用 MSVC。
- 基準：43/43 綠。
- 53 筆中，52 筆在這個執行順序下 killed，每筆還原後的控制組都是綠的。
- M01-index 的新編執行檔連續被 SAC（WinError 4551）擋下。它的錨點與注入碼都沒有改。先前一輪已 killed：那一輪在還原原始碼之後才跑紅燈，但 CR04 只執行突變後的 bridge，結果不受影響。
- 單層對照：
  - 只拿掉 `app_world_candidate_revalidate`：CR17 仍然是綠的，是等價突變。
  - 只拿掉 bridge 的過期判斷：只因為錯誤碼 `INVALID` 不等於 `STALE` 而轉紅，過期的預覽並沒有被發布。
  - 三層版本：M11-revalidation 讓探針報告「World/metadata/history changed」；M11-expiry 讓過期預覽確認成功。

正式結果以 WSL 上 `run_mutations.py --output <新目錄>` 的收據為準。

## 驗收邊界

`tests/test_grid_card_reference.py` 登記 31 個具名 CR 核心方法、3 個 P-146 方法、2 個 P-154 方法、4 個 P-142 B2 方法、2 個 P-142 S1 方法及 1 個整合後 P-142 S2 方法；CR19 會用實際 ZIP writer/reader，開到新原生 context 並逐字核 dump。
拒絕測試逐則核對原因與完整 id token，要求同一則診斷同時具有原因及全部身分，不將 field 3 誤配到 field 30，也不拼接不同違規的身分。
模型包在網頁正式開啟、恢復及方案載入時的原生驗證路徑與實際服務探針，見 `MODEL-ADMISSION-AUDIT.md`；結構驗證／ZIP 解包本身不冒稱通過原生版本核對。
`tests/test_card_reference_project_store.js` 檢查 /18 的保存、降版、能力、未知版本及舊逐欄相容。
原 PROPOSAL 沒有列 CR23 或 M15，沿用其原始編號，不自行補號。
CR24／M23 是 UI 切片，本次不宣稱桌面／390px 操作或草稿支援。
CR18 本次驗未啟用身分帳的對照；此基底未宣告原生 identity-ledger/1，啟用身分帳的新記號／外部 pin 與 M12 仍待其實作切片，不新增假 skip 或聲稱通過。
CR10 以原生 AST 表示 `(3/2 mm) × 2` 的精確尺寸；文字入口沿既有 parser 寫 `=3 mm/2*2`，不把既有 `3 / (2 mm)` 反向長度語意偷改成尺寸。
實際 pass/fail、突變結果與受測 head 以 PR 的最終交付收據為準，本文不把計畫當成執行結果。
