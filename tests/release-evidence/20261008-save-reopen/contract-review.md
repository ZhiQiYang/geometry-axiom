# 保存與重開契約審查（唯讀）

> 協調註記：審查讀取 `e176681f34c634d0fdd2dca364a8d7d44cc51808`。其後 `ce0958ca700753172338fe291a17e781da89465a` 只改焦點證據用詞，不屬於本契約。歷史 10／155 缺失收據仍缺。本文件不是驗收通過。


- 基底：`D:\geometry-axiom-focus390`
- HEAD：`e176681f34c634d0fdd2dca364a8d7d44cc51808`（`fix/rule-guide-focus-20261008`，工作樹無未提交變更）
- 本頁不執行測試、不編譯、不起服務。測試欄只記名稱與斷言範圍。
- 行為判準以 `公理層.md` 為準。條文未寫的檔案狀態不從 C／UI 升格成公理。
- 此 HEAD 的焦點修正不是本契約的一部分，下文不把它算進保存語意。

## 0. 三條流程共用、但層級不同的狀態

公理有「目前 World／專案」與「保存狀態」這幾個已定案句子，沒有「乾淨／髒／未命名／已命名」四個檔案旗標。

| 項目 | 已定案 | 出處 | 未定案 |
| --- | --- | --- | --- |
| 場景 SSOT | dump＝定義＋放置＋canvas-pos；重放逐字相同；輸出引用，不輸出凍結長度／uv | `公理層.md:891–902` | — |
| 失敗不換專案 | 匯入失敗保留當前 World 與專案；未知能力不得降成直接數 | `公理層.md:783–785`、`1080` | — |
| 復原單位 | 撤銷／重做以整筆交易為單位 | `公理層.md:589`、`597` | 專案檔是否攜帶復原堆疊：公理未寫 |
| 工程保存狀態 | 未發布草稿與發布目錄分開，介面明示保存狀態 | `公理層.md:781–782` | 「乾淨／髒」這兩個詞未入公理 |
| 參數專案身分 | 完整專案重開保留原卡片身分；參數包匯入改寫新身分，與來源專案獨立 | `公理層.md:817–823` | — |
| 組構草稿 | 未發布草稿在完整專案的獨立編輯區，不冒充 World | `公理層.md:834–841`、`908–910` | — |
| 檔名級未命名／已命名 | — | — | 公理未定案。產品文件把專案寫成 `projectId`／`name`／`sceneHash`（`geometry-web/docs/REFERENCE-PROJECT.md:25`、`92–97`）。實作初值名稱是「未命名專案」，並另有 `dirty`／`saved`／`downloaded`（`geometry-web/reference-workspace.js:6`、`153–155`）。這只是產品現況，不是公理。 |
| `.scene` 與 `.gcanvas` | 場景定義與 `.gcanvas` 都要帶工程來源閉包（`公理層.md:781–785`） | 產品補充：`.scene` 只存取幾何，不含完整專案（`REFERENCE-PROJECT.md:15`、`92`）；不能代替模型與投影（`geometry-web/docs/SPACE-MODELING.md:61`） | 底圖、未發布草稿、已建空間模型被 `.scene` 省略，是既定邊界，不是本頁新發現，也尚未被公理逐欄命名 |

重開後應比較的是身分與引用，不是畫面：定義位元組、id、指紋、vertexKey／ruleKey、owned mapping、`projectId`。推導出的線段、中線、長度、平移、體積可以重算後核對，但不得寫回成第二份來源（`公理層.md:135–145`）。

產品復原堆疊不進專案包（`REFERENCE-PROJECT.md:63`、`SPACE-MODELING.md:63`）。因此「關閉再打開」公理承諾的是目前定義可重放，不承諾上一工作階段的 undo 堆疊還在。

`REFERENCE-PROJECT.md:23` 的格式清單停在 `geometry-canvas/9`。封裝常數已寫到 `/16`（`geometry-web/project-store.js:8–19`）。不得把該舊清單當成現行上限，也不得把常數清單升格成公理。公理只要求該能力出現時必須宣告，缺能力就拒絕（`公理層.md:760–767`、`837–840`、`1079–1080`）。

## 1. 網格＋面

### 步驟與應保持的關係

1. 建立面。邊界面可未放置（`公理層.md:63`、`431–450`）。輪廓是定義；端點以外的裁切不是來源。
2. 建立 D29 系統。World 獨立物件：id、名稱、兩軸（未定義／REPEAT／REPEAT_PANEL）、可選 `main_along`、可選 D10b 相位差、每欄恰好一個直接整數或 ParameterRef。不依附面，不擁有角材（`公理層.md:393–411`）。名稱可重名，不是身分。
3. 建立 D30 配置。保存 id、邊界 id、系統 id、vertexKey、帶符號 cell、cell 內已約分比例。平移只推導，不另存（`公理層.md:431–449`）。首次選點的 key 表與配置同一交易；刪點不降低 next-key；重開不得重用已刪 key（`公理層.md:444–449`、`798`）。未配置的舊邊界不因此多一份 key 表。配置不暗建 placement 或角材。
4. 套到面上。`grid G on P from-binding B`。承載面必須引用同一邊界；每面最多一個主格（`公理層.md:179–182`、`794`）。不得改寫成可見座標陣列，不得用工程綁定覆蓋來源式主格（`公理層.md:800–801`）。
5. 可選 D19a。規則由系統擁有，不依附面、不存每面覆寫、不展開成每格一份 D19（`公理層.md:272–278`）。正式線引用是整組 `(appliedGridId, systemId, ruleKey, signed cellI/J, axis, innerIndex)`。同座標或同 ruleKey 換來源不得暗接。
6. 可選手動子格、guide、角材。子格只存父格與等分（`公理層.md:261`、`R23` 在 `1022–1024`）。角材存 `at-line`／`at-face` 引用；長度不凍結（`公理層.md:895–897`）。格線不擁有角材（`公理層.md:176–177`）。
7. 修改。來源、邊界、相位、參數進同一候選，重算全部配置、主格、子格、guide、角材（`公理層.md:795–803`）。參數改值不改 signed 索引、vertexKey、比例、band。失敗整筆留在舊 World。
8. 復原／重做。保留同一 key、cell、比例、引用（`公理層.md:1078`）。D19a 連規則與高水位一起回到該 World 快照；不承諾被丟掉的 undo 分支，也不新增跨專案永久身分（`公理層.md:279`）。
9. 保存。順序含 boundary 與 keymap、system、binding、placement 主格、子格、後續引用；含未使用來源與未放置配置與 canvas-pos；不輸出平移、裁切陣列、顯示取樣（`公理層.md:1076–1080`）。有規則就必須宣告 `grid-subdivision-rules/1`。
10. 關閉重開。定義與推導結果相同；legacy-finite 不因重開改成無限排法（`公理層.md:410–411`、`1099`）。載入失敗不得替換目前 World（`公理層.md:1080`）。
11. 專案旗標。公理未定義此流程的未命名／已命名／髒／乾淨。產品層另規定未套用的網格草稿擋住保存專案（`REFERENCE-PROJECT.md:95`）；那不是幾何來源本身。

應同時成立的關係：`binding → boundary`、`binding → system`、套用主格的承載面與 binding 同一邊界、規則屬於系統而非面、角材／guide 指向完整線引用而不是毫米座標、canvas-pos 不參與幾何（`公理層.md:59–62`、`403`）。

### 既有測試

原生 `.scene`，比的是 dump＋references＋objects，不是畫面。

- 兩面、來源身分、衍生座標不得寫回、同行程 reset 後重載：`tests/test_grid_system_contract.py:212–225`，`roundtrip` 在 `123–132`。
- 失敗載入留住全部套用：`204–210`。
- 取消、過期確認、兩面一起改、undo／redo、roundtrip：`247–274`。
- 子格＋guide＋角材任一失敗整筆回滾後 roundtrip：`300–319`。
- 刪除被引用系統拒絕；刪光後 undo 恢復：`321–336`。
- 工程綁定不能取代 grid-system 來源：`338–363`。
- 未放置邊界只存 key／比例，dump 無 translation：`tests/test_infinite_grid_contract.py:175–195`。
- 改 pitch 後兩份錨點、取消、undo／redo、roundtrip：`197–221`。
- key 與配置同一交易，undo 一起消：`223–240`。
- 刪除最高 key 後重載仍不得重用：`323–337`。高水位耗盡重載仍耗盡：`339–348`。
- 舊有限排法重開不暗轉：`522` 起 `test_legacy_finite_replay_keeps_ordinal_indices_and_cannot_silently_convert`。
- 規則 key 取消不消耗、刪除不降低高水位、undo／redo、roundtrip：`tests/test_grid_subdivision_oracle.py:311–336`。
- 改來源後兩配置錨點與 ruleKey 都在，undo／redo：`351–370`。
- 缺能力／缺高水位載入失敗且不傷既有歷史：`873–904`。
- 缺規則、換系統、錯 innerIndex 的 guide 引用整筆拒絕：`931` 起。
- uint32 高水位耗盡經刪除、undo／redo、roundtrip 仍耗盡：`1010–1034`。
- 角材 `at-line rule …` 寫在 dump，roundtrip：`611–638`。第二面越界則整份來源拒絕：`640–663`。
- 手動子格父先於子、再先於 guide，undo／redo 後 roundtrip：`tests/test_subgrid_contract.py:635–646`；整組 history：`656` 起。

`test_grid_system_contract.py` 是 legacy `from-system origin`，不能拿來證明 D30。`test_infinite_grid_contract.py:1–6` 已寫明兩者分開。

### 最小缺口

1. 沒有一條案例串起：一面 D30 錨點、該面一條 D19a 正式線上的角材、該角材這一步的 undo／redo、然後像 `test_grid_system_contract.py:123–132` 先清空再載入。`611–638` 有引用與 roundtrip，但沒有這支角材的 undo。`1036–1090` 有角材引用指紋，沒有 roundtrip。
2. 來源規則成功路徑的 `roundtrip()`（`test_grid_subdivision_oracle.py:303–309`）載入前不 `reset`。載入若被做成 no-op 仍會相等。它弱於網格系統那個先清空的重載。
3. 同 ruleKey 不得暗接，已由同一檔的 `wrong-source`（`931` 起）拒絕。定案的是換成另一來源也不得暗接（`公理層.md:277`）。`279` 寫明此邊界不新增跨專案永久身分；兩個專案如何交換、匯入後 id 必須留或必須改，條文未定，不得寫成規格，也不補那個測試。
4. 沒有斷言網格編輯之後的 `projectId`、名稱、`dirty`／`saved`／`downloaded`。這些旗標公理未定案，所以缺口是「產品旗標未被此流程斷言」，不是缺一條公理。
5. 沒有「只匯出 `.scene` 再打開，底圖與未發布草稿仍不在」與這條網格鏈放在同一次斷言。省略本身是已知邊界。

### 可用合成資料

新建，不要讀私人檔。

- 面 A：`(0,0) (600,0) (600,400) (0,400)`，放置原點 `(0,0,0)`，`u=+x`，`v=+y`。
- 面 B：`(0,0) (300,0) (300,300) (0,300)`，先不放置，用來證明配置不必有承載面。
- 系統：u `repeat 0 200`，v `repeat 0 100`，無 stagger，名稱「假格網」。
- 配置：面 A 左上頂點，cell `(0,0)`，比例 `0/1,0/1`。
- 規則：`all-cells`，`2×2`，名稱「假規則」。預期正式 key＝1，next＝2。
- 角材不要用「左右邊界材跨接副支」這組合成。面寬 600、u 間距 200 會切成三格，左右外輪廓不在同一格；副支若 `between` 這兩支，footprint 超出單一 cell。直接引用 D19a 線時，完整 footprint 必須留在該線所屬 cell（`公理層.md:645`），格邊不是擋面。
- 角材改指向既有合法夾具，不另造：`tests/test_grid_subdivision_oracle.py` 的 `test_direct_line_needs_real_support_and_complete_cell_scope_while_guide_is_coordinate_only`。`real_supports` 用上下邊界材承接格內兩支主支；副支是格內 `between t1 t2`（約 `631`），已斷言長度 540、中線 400。
- 專案顯示名只作產品層夾具：「假專案甲」。幾何斷言不得依賴這個名字。

手算檢查只核格線與索引，不是角材夾具：u 線 `…,-200,0,200,400,600,…`；規則內線在 cell 寬 200 的一半處。改 step 為 300 後，cell 索引與 vertexKey 必須仍是原值，只有推導座標變。跨出該格的副支不在這組建議裡。

## 2. 組構規則＋角材

### 步驟與應保持的關係

1. 發布 D32。穩定規則 id、版本、槽位 id、接合 id。不以名稱、陣列順序、卡片位置配對（`公理層.md:475–484`）。發布版本不可覆寫；草稿不是可引用版本。規則可以完全不綁房間、網格、邊界、承載面。
2. 建立 D33。固定規則版本，加上槽位到材料來源、接觸面、截面方向（`公理層.md:486–492`）。缺材料可存成未完成；懸空引用要拒絕，不是未完成。綁定不生成、不擁有角材。新規則版本不自動改綁定。
3. 畫布位置依 D12 進 World（類別含 `assembly-rule`／`assembly-binding`，`公理層.md:59`）。拖卡片不改規則指紋。
4. 建立 D34 才生成角材。保存規則版本與指紋、明選 binding、有限 member、承載面、兩端支撐、member→原生角材所有權（`公理層.md:494–500`、`843–848`）。首版只允許兩支同向 primary 加一支端接 secondary；超出能力回 `UNSUPPORTED`，不改規則。
5. 修改。候選整包重驗。owned 角材拒絕獨立改截面、移動、刪除（`公理層.md:845`）。解除仍被引用的來源必須同一交易完成，否則拒絕（`公理層.md:830`）。
6. 復原／重做。還原全部規則、綁定、實例、引用（`公理層.md:841`）。取消與過期確認不改 World（`公理層.md:846`）。
7. 保存。正式 dump 含未使用規則與合法未完成綁定，順序是規則／材料先於綁定（`公理層.md:908–910`）。不得用展開尺寸或已生成幾何取代。未發布草稿只進完整專案的獨立區（`公理層.md:836`）。
8. 關閉重開。完整專案保留原身分；重開重算並核對 owned mapping 與來源閉包（`公理層.md:841`、`847–848`）。舊能力不足必須拒絕，不能把組構展平成普通角材。
9. 專案旗標。公理未定案。產品層組構草稿可隨 `.gcanvas` 重開（`REFERENCE-PROJECT.md:66`、`95`）。`.scene` 沒有這塊草稿區。

應同時成立的關係：binding 指向固定 `(ruleId, version)` 而不是名稱；instance 指向該 binding 的指紋；memberId 對 timberId 是所有權，不是「畫面上有三支料」；外部 guide 可以引用 owned 角材，因此刪實例前要先處理外部引用（I9／I42）；authoring 能力不等於生成能力（`公理層.md:839–840`）。

跨專案：公理只明確寫「完整專案重開保留原身分」。參數包匯入會改寫新 id（`公理層.md:821`）。組構匯入沒有同等句子。不得把參數規則或 UI 抄成組構跨專案契約。此點標未定案。

### 既有測試

- 未完成綁定可保存，選了尺寸仍不偷偷補面：`tests/test_assembly_rules.py:342–345`。
- 新版本重綁與刪除的 undo／redo 連 dump 一起比：`320–340`。
- canvas-pos 不弄丟預覽，undo 後 redo 仍有該列：`469–475`。
- 新 bridge 行程 `.scene` 往返，dump 與 `assembly-read` 全等：`477–484`。
- 截斷、重複紀錄載入失敗且 dump 不變：`486–493`。
- authoring 不因此能生成：`538` 起。
- 三支 owned 角材、預覽不改 World：`tests/test_assembly_generation.py:43–47`。
- 改名改序不改 member→timber：`125` 起 `test_reorder_rename_keeps_member_to_timber_mapping`。
- owned 拒絕獨立 place／delete／改尺寸：`169–173`。這是保存前。
- 新行程 roundtrip 保留來源、mapping、幾何 dump：`174–177`。這條沒有重寫，載入後仍不刪。
- 重開後 owned 仍拒絕直接 `delete timber`：`214` 起 `test_reopened_owned_member_refuses_direct_delete`。沿用同一組生成夾具的主支承接與端接副支，fresh process 只做 `loadfile` 後拒絕刪除且 dump 不變。不是 4000×3000 空間模型 oracle，也沒有另測 undo／redo／reset。
- 拿掉能力或改 owned 尺寸的檔拒絕，且不修好：`178–181`。
- 外部 guide 擋住刪除；清掉 guide 後 undo／redo：`182–184`。
- 參數改值重算長度但不重新配置 timber id：`187–193`。
- 升版不自動發生：`194` 起。
- 瀏覽器封包重開保留草稿 id 與已發布 id，不互相覆寫：`geometry-web/assembly_id_test.js:33–40`、`65–70`。這是產品包，不是公理裡的跨專案匯入。
- `tests/test_rule_case_workbench_http.py:388–393` 只鎖 HTTP `projectId`／generation，不斷言角材所有權。

### 最小缺口

1. 既有 fresh-process roundtrip（`174–177`）仍只比來源、mapping 與 dump，沒有重寫。載入後「owned 角材仍拒絕直接刪除」由 `test_reopened_owned_member_refuses_direct_delete`（`214` 起）補上；undo、redo、reset 之後的同一拒絕沒有加進這條。
2. 沒有一條案例同時含：未發布草稿、已發布版本、未完成綁定、已生成 instance，然後只拿 `.scene` 打開時草稿消失、拿 `.gcanvas` 打開時草稿還在且不變成可引用版本。A15／A23 蓋住封包重開，沒有對照 `.scene` 省略。
3. 跨專案組構身分未定案，因此也沒有合法測試可寫「匯入後 id 必須改或必須留」。缺的是條文，不是再補一個 UI 案例。在條文出現前，不得用 A15 的同包重開代替。
4. 沒有把組構確認之後的產品 `dirty`／名稱／`projectId` 和原生 dump 分欄斷言。`assembly-confirm` 在實作裡會標髒（`reference-workspace.js:420`），這不是公理，也尚未被這組原生測試看見。

### 可用合成資料

- 面：`(0,0) (800,0) (800,500) (0,500)`，原點 `(0,0,0)`，`u=+x`，`v=+y`。
- 具名規格：`位置甲=100`、`位置乙=700`、`位置丙=250`（毫米）。兩條豎向 guide、一條橫向 guide 只引用這些名字。
- 邊界材：id 90、91，截面 `20×20`，分別貼左右外輪廓。
- 規則版本 1：槽位 1「主支」、槽位 2「副支」；member 1 與 2 用槽位 1，member 3 用槽位 2；兩處 `end-to-side`。
- 綁定：槽位 1 直接整數 `A=30,B=40`；槽位 2 `A=20,B=40`；接觸面 A，方位 A。另存一份兩槽都未選的未完成綁定。
- 實例只引用完成綁定。預期三個新 timber id，與 90／91 不同；長度由 R6 推出，不斷言把長度寫進 dump。
- 草稿：名稱「假草稿」，不得出現在 `assembly-read` 的已發布清單。
- 第二專案只放顯示名「假專案乙」與另一個 `projectId`。在公理補上匯入身分前，這個專案只能當負例：不得自動改到甲的規則版本。

## 3. 模型庫跨專案操作

### 公理邊界（先於步驟）

公理沒有「模型庫」這個型別。相關已定案只有：

- D5 槽位空間不是水密外殼，也不是 D21／D22（`公理層.md:51–57`）。
- D24／D25 是正交建模交換包：definitions 與 derived 分開，另一專案要能依交換包重建形狀（`公理層.md:324–352`、`1060`）。快照不能回寫成來源。
- 外部專案變更不自動改本專案（`公理層.md:777`）。
- 參數包跨專案匯入改新 id（`公理層.md:1107`、`821`）。
- 網格 ruleKey 沒有跨專案永久身分（`公理層.md:279`）。

「3D 模型庫裡的已建立空間」是產品物件：複合空間記錄與畫布上的六面槽位卡片分開（`SPACE-MODELING.md:57–63`）。模型記住建立當下的輸入與來源場景，後來改原面不更新模型。這段不是公理；與公理衝突時仍以公理為準。本流程不得把兩者寫成同一個所有權。

### 步驟與應保持的關係（產品契約；公理未定義的標出）

1. 建立。從已放置面或組合面產生一筆模型：id、name、created_at、source（含當時 scene hash、boundary、placement、投影）、input、各角色 result。畫布上的 D5／面 id 仍是另一份物件。
2. 修改。平面模式只允許改已保存的牆高並重驗；取消或預覽失敗不改原紀錄（`REFERENCE-PROJECT.md:34`、`SPACE-MODELING.md:50–53`）。其他設定要另建模型，不是就地變成新所有權。
3. 復原／重做。模型增刪與核心幾何共用一條本機歷史，次序交錯；刪掉最後一個模型仍是未保存（`SPACE-MODELING.md:63`、`REFERENCE-PROJECT.md:62`）。專案檔不保存這條堆疊。
4. 保存。`.gcanvas` 的 `models` 與 `world.scene` 分開。含投影為 format `/3`，含角材結構模型為 `/4`（`SPACE-MODELING.md:61`）。更新的格式號見第 0 節，不在此把 `/16` 說成模型庫公理。
5. 關閉重開。先驗證套件，再依保存輸入重建並比對摘要與幾何，全部成功才替換目前場景與專案（`SPACE-MODELING.md:62`、`REFERENCE-PROJECT.md:49–50`）。失敗留在原專案。同一檔重開保留 `projectId`（產品，`REFERENCE-PROJECT.md:25`）。
6. 換專案。新專案是新身份與新名稱，清空場景、附件、模型、草稿，且可一步復原（`REFERENCE-PROJECT.md:94`）。清空內容則保留身份與名稱。開啟別的檔也是一步復原。
7. 跨專案拷貝模型。公理未定案。產品文件沒有寫「把甲的一筆模型併進乙的非空專案時，model id 與 source hash 要不要重發」。不得用「Undo 回到上一個專案」代替這件事。

應保持的區分：

- 模型 source 指向建立時的場景指紋，不是現在畫布的即時面。
- 畫布空間卡片的 id 空間 ≠ 模型 id。
- `projectId` 屬於專案，不屬於某一面或某一支角材。
- 下載產生 ≠ 已寫入成功（`geometry-web/docs/DOM-CONTRACT.md:900`）。`save_roundtrip_acceptance.cjs:74` 斷言下載後仍是 `downloaded && dirty`。
- 索引資料庫恢復不等於已保存檔案（`REFERENCE-PROJECT.md:96–97`）。

### 既有測試

- 模型 v2 往返、無模型維持 v1：`tests/test_space_model_store.js:29`。
- 核心與本機歷史交錯、分支擋住過期 redo：`80–96`。
- 刪最後一個模型仍警告離開：`129`。
- 驗證失敗不換專案：`137`、`233`。
- 角材模型 v4、高度更新不讀即時定義：`182`、`248`。
- 瀏覽器同一包重開、竄改幾何拒絕且 context 不變：`geometry-web/space_model_test.js:1426–1437`。
- 33 項真實下載／新設定檔重開／新專案 undo／損壞 ZIP：`tests/integration/save_roundtrip_acceptance.cjs:50–99`。幾何 oracle 是 `boundary 311` 的 4000×3000，牆高 3000→3200，體積字串 `36000000000`／`38400000000`（`61–66`）。重開用 `semantic()` 比對 world、id、name、manifest、模型與來源 bytes（`40`、`87`），不是截圖。名稱跟的是保存快照，不是另寫的預期字面。
- 模型庫 35 項：`tests/integration/model_library_history_browser.py:50–69`。MH00 建立模型（`245–247`）；MH01 暫停中的 Undo 不改模型，放開後 World 與 models 回到原值（`269–276`）；MH02 關閉再開後晚到回覆不得刪模型（`289–296`）；MH03 暫停中拒絕換檔（`303–309`）；MH03-cross-project 是庫內 Undo「新專案」一步回到原 context（`312–332`）；MH04 外來 context／session 不覆寫（`337–352`）。限制寫明不重建歷史 10／155（`63–64`）。
- 非瀏覽器 28 項只走 shell 函式：`tests/test_workspace_shell_history.js:223–228` 讓假 history 的 Undo 跟到另一個 context。檔頭契約說它沒有 `.gcanvas` 往返（`tests/INTEGRATION-GATES.md:30–34`）。
- Q38 斷面七個 mesh 的 `.gcanvas` 往返與 undo：`tests/integration/q38_save_roundtrip.py:202–250`。它證明的是斷面定義，不是模型庫跨專案合併。附圖與草稿被它自己標成範圍外（`183`）。

### 最小缺口

1. 沒有「專案甲存一筆模型，專案乙已經有自己的面與另一筆模型，再把甲的模型併入乙」的案例。現有跨專案是本頁歷史裡 Undo 新專案（`model_library_history_browser.py:321–332`、`save_roundtrip_acceptance.cjs:81–83`），身分跟著整包回去，不是拷貝所有權。
2. 公理未寫這次合併要不要新 model id、要不要重算 source hash。缺口先是未定案，不能用測試補規格。
3. 33 項重開的 `semantic()` 已含 `name`（`save_roundtrip_acceptance.cjs:40`、`87`），會跟保存快照比名稱，不是完全沒測名稱保存。缺的是獨立預期名稱字面。`snap()` 讀了 undo／redo 長度（`36–39`），`semantic()` 比較時丟掉它們，所以沒有斷言重開後歷史堆疊為 0 或僅剩「開啟」一步。產品說堆疊不進檔（`REFERENCE-PROJECT.md:63`）。
4. 沒有斷言：同一幾何看起來一樣時，模型 source 仍是舊 scene hash，畫布 D5 卡片張數不變。`SPACE-MODELING.md:58` 寫了不跟隨原面，儲存測試蓋的是牆高更新不改 native dump（`save_roundtrip_acceptance.cjs:68–70`），沒有在重開後改面再證明模型 result 不動。
5. `.scene` 不得冒充含模型的專案：文件已寫（`SPACE-MODELING.md:61`），沒有與上述 4000×3000 模型鏈放在同一次「只存 scene → 模型清單為空」斷言。

### 可用合成資料

- 面：`(0,0) (600,0) (600,400) (0,400)`，放置 z＝0，`u=+x`，`v=+y`。不要用 4000×3000 的既有 oracle 充當新夾具。
- 平面模型：名稱「假模型一」，牆底 0，牆高 2400。淨體積應為 `576000000` mm³（600×400×2400）。材料牆若開啟，厚度 100，且必須整筆成功才算有牆。
- 專案甲：`projectId` 用測試自造的 UUID，顯示名「假專案甲」。
- 專案乙：另一 UUID，顯示名「假專案乙」，自帶一面 `(0,0) (200,0) (200,200) (0,200)`，模型清單空。
- 通過條件要分欄：乙的 `projectId`、乙的面 id、甲的 model id、甲的 `source.scene_hash`、甲的 result 頂點。任兩欄相同都不得推成「已合併」。
- `.scene` 對照檔只含面與放置。打開後 models 必須是空陣列。不要把這份 `.scene` 命名成 `.gcanvas`。

## 不可升格

以下任何一項都不能寫成「保存／關閉重開契約已通過」：

1. 畫面、截圖、3D 檢視看起來一樣。體積或外框相同也不等於 source hash、model id、`projectId` 相同。`save_roundtrip_acceptance.cjs:72` 的截圖不是斷言。
2. 歷史 10／155 缺失收據。仍缺 PR #161 原十項腳本、第十個 case id、舊 155 的 `browser_ui.py`、原 results、初始 World 到修正後的前序。找到的 155 通過收據留在原 head `a49d2a5`。出處：`geometry-guide/CLOSEOUT-EXTERNAL-DEPENDENCIES-20261008.md:7–14`、`geometry-web/docs/AUX-REVIEW-20261008.md:25`、`56`、`126–151`、`tests/release-evidence/20261007/README.md:42`、`geometry-web/docs/RELEASE-CANDIDATE.md:104`。本頁不把它們改標到 `e176681f`。
3. 新的 35／33 項與 16 項 oracle control 只覆蓋自己的 harness。`tests/INTEGRATION-GATES.md:64–67`、`107–113` 寫明不重建十項／155。不得把 35 或 33 加成 155。
4. `tests/test_workspace_shell_history.js` 的 28 項沒有真實版面、原生 bridge 或 `.gcanvas`（`tests/INTEGRATION-GATES.md:30–34`）。
5. 下載備援、picker stub、寫入失敗注入不是作業系統存檔對話框驗收（`save_roundtrip_acceptance.cjs:99` 的 limits；`CLOSEOUT-EXTERNAL-DEPENDENCIES-20261008.md:30`）。
6. `#170` 的焦點修正。它不建立、也不證明本頁任一欄位。
7. `REFERENCE-PROJECT.md:23` 的 `/1–/9` 清單，以及只比較可見線段、中線毫米、合併外形。
