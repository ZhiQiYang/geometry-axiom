# Q38：原生截面、延伸與簡易定位契約

本文件只記錄 D35–D40／I43–I51／R36–R40 已採納規格的有界實作接口，不新增公理。
原生核心提供完整 World 定義、1A 截面驗證、1B 兩種簡易定位宿主及互轉、typed 來源圖、scene 保存與原子 history。
本文件的原生測試不替代建模執行器、D24/R39 renderer、UI 或 .gcanvas 的跨層驗收；這些由各產品 gate 核對。
對語法合法的候選，驗證遍歷每個 member／run 及同 profile 的全部構件配對；不因第一個違規停止。
回應 diagnosticsComplete:true；包含未通過的可求值矩形、每項出界與重疊，以及來源無法求值的構件。
上游 parameters／engineering 先失敗時，也在隔離 trial 中逐一求值截面來源閉包，不沿用舊參數快取。
解析或操作形狀非法時拒絕輸入，提供該輸入錯誤；不臆造尚未建立的構件幾何。
輪廓擴大時，按原有接觸線段提示 `PROFILE_CONTACT_LOST`；仍貼其他邊不會掩蓋原接觸的消失（AC18）。

## World 與容量

`SectionProfileState` 是 World 的獨立 POD；沿用既有候選副本、整筆 history、definition equality 與 dump hash。
profile、member、run 各自使用完整 uint32 id 域（含 0），名稱不是身分，可以重複。沒有新增 canvas-pos 種類。

| 項目 | 限制 |
| --- | --- |
| profiles | 16 |
| members（所有斷面合計） | 128 |
| runs | 32 |
| 每斷面頂點 | 4–32，最後一點回接第一點，不重複末頂點 |
| profile／member canonical JSON record | 最多 2047 UTF-8 bytes |
| run canonical JSON record | 最多 8191 UTF-8 bytes |
| copied host range | 4–32 個外輪廓頂點，最多 8 孔，每孔 4–32 頂點 |
| 一筆交易 | 1–256 operations、1 MiB，沿用既有交易限制 |

Linux C11 實測 `sizeof(World)=2,904,880` bytes，截面狀態 `875,800` bytes。
固定容量為原生實作的工程選擇，超限拒絕，不截斷。
最大容量 fixture 同時保存 16 profiles／128 members／32 runs，fresh load 逐字等於完整 dump；這不是一般使用效能或手機記憶體驗收。

面材固定具名規格 `calcium-silicate-6`（`section-profile-read.panelSpecs`）：厚度 6、寬度嚴格小於 915、板長 1830。
板長不限制 run length，也不產生分段、接縫或料單。

## Native bridge 交易

`section-profile-read` 回傳 revision、定義、求值矩形、run 的局部／世界範圍，以及能力與限制。
`section-profile-preview <file>` 讀取完整 UTF-8 JSON：

```json
{
  "schema": "section-profile-transaction/1",
  "expectedRevision": 0,
  "operations": [
    {"op":"put-profile","value":{"id":1,"name":"L 斷面","outline":[[0,0],[400,0],[400,60],[60,60],[60,250],[0,250]]}},
    {"op":"put-member","value":{"id":1,"profileId":1,"kind":"timber","A":{"kind":"literal","value":27},"B":{"kind":"literal","value":33},"orientation":"A-u","u0":0,"v0":0}},
    {"op":"put-member","value":{"id":2,"profileId":1,"kind":"panel","panelSpec":"calcium-silicate-6","width":100,"orientation":"thickness-v","u0":27,"v0":0}},
    {"op":"put-run","value":{"id":1,"profileId":1,"length":{"kind":"literal","value":2400},"placement":null}}
  ]
}
```

revision 必須取自當次 native read，不能假定為 0。preview 不改 World／revision／undo；合法候選才可 `section-profile-confirm <token>`，一次確認只記一筆 history。
`section-profile-cancel <token>` 取消候選。來源修改、undo、redo 或另一筆候選會使舊 token 過期；engineering／assembly／普通 confirm 不得借用 section-profile token。
`line undo`／`line redo` 沿用完整 World 交易。解析拒絕、非法候選、取消及過期確認不清掉 redo。

`put-*` 是明示的同型別同 id 重宣告。刪除使用 `delete-profile`／`delete-member`／`delete-run` 和 `id`。
所有操作先修改候選，再重驗全 World；可同筆刪除 profile 與依賴者，不能留下孤兒，也不自動刪除依賴者。

位置只收直接整数 `u0,v0`；timber 的方位是 `A-u`／`A-v`，panel 是 `thickness-v`／`thickness-u`。
JSON 原生解析器拒絕浮點數；分數字串、布林、越界也不能當座標。構件是否在輪廓內以精確整數面積判定：矩形與輪廓外部的正面積差集（`sp_outside_regions` 的水平帶分割，即回報的 `outsideRegions`）為空才合法；貼邊或貼點合法，正面積交集拒絕。不用「四角在內加沒有輪廓邊穿過內部」的近似，那會接受剛好填滿凹槽、整個落在輪廓外的矩形（見下方 I44 修正）。

尺寸來源沿用既有具型別物件：

| 來源 | JSON |
| --- | --- |
| 直接整數 | `{"kind":"literal","value":27}` |
| D6b | `{"kind":"spec","name":"A"}` |
| D31 | `{"kind":"parameter","parameterId":0,"fieldId":0}` |
| D26 timber（只供 member A/B） | `{"kind":"material","id":"pine","version":1,"field":"A"}` |

material 欄位必須與 A/B 身分相符，旋轉不交换來源；run 不收 material/application 來源。
同一 batch 可用既有 engineering operations 修改參數／發布固定材料版本；另提供 `{"op":"put-spec","name":"A","value":27}`、`{"op":"delete-spec","name":"A"}`。
spec／parameter 改動須重新驗證既有斷面依賴；改來源造成出界或碰撞時完整 World 回滾。
既有 engineering-preview 及普通 DSL spec preview 也回傳 section-profile before/after，不私自凍結舊值。
native preview 的頂層 `before`／`after` 重用完整 engineering 候選狀態，包含具名 `specs`、材料／做法／套用、參數來源與既有幾何；原有 `sectionProfiles` 影響與提示仍保留。
同一來源也被既有 guide／角材使用時，預覽列出其新舊座標、姿態與長度，不能只顯示斷面影響；沒有斷面使用者的來源操作同樣須揭露來源變更。

run `placement:null` 合法且只回傳局部範圍，沒有世界位置。
進階定位保存 `{"kind":"advanced","origin":[1000,2000,2700],"N":"+Y","V":"-Z"}`；軸只收 `±X/±Y/±Z`，U 由 V×N 求得，不作另一份可編輯來源。
驗證輪廓拉伸的所有頂點均在 D1 範圍；同斷面可被多個 run 引用。
未識別欄位、截面孔、任意角度、逐 member 板厚、角色或裁切設定明確拒絕。

## 簡易定位與互轉

~~~json
{"kind":"simple","host":{"kind":"placement","placementId":9},"dir":"+v","p":1000,"q":2000,"up":"+Z"}
~~~

host 為有效 World D4 承載面時保存 live 引用；宿主 frame／range 變更重新求值。
另一種 host 複製已保存空間牆面的 frame／有效範圍，原空間或模型更新不聯動：

~~~json
{"kind":"space-wall-values","sourceDescription":"依某空間牆取值，不隨空間變動",
 "frame":{"origin":[0,0,2700],"U":"+X","V":"+Y","N":"+Z"},
 "region":{"outline":[[0,0],[5000,0],[5000,5000],[0,5000]],"holes":[]}}
~~~

原生只接受明確的 dir、p、q、up；UI 的預設值必須作為明示輸入。
dir 只收 ±u／±v，up 是與 N 垂直的 cardinal 軸。p,q 必須在閉合有效範圍內，孔邊界合法、孔內部拒絕。
O=host.origin+p·host.U+q·host.V，N=dir，V=−up，U=V×N。
不查 run 與其他 World 物件碰撞；也不要求延伸全長留在宿主範圍，宿主只定位起點。

- {"op":"convert-run-to-advanced","id":1}：保存求值後 O/N/V，解除宿主聯動，preview 提示 RUN_HOST_DETACHED。
- {"op":"convert-run-to-simple","id":1,"host":...}：原生反求 dir,p,q,up；起點不共面、方向非宿主平面軸、起點越界等條件逐項列在拒絕原因中，原 run 不變。
- {"op":"delete-placement","id":9}：在同筆 transaction 中明示刪宿主；仍有依賴時整筆拒絕，可同筆先把 run 改成 advanced 或刪除，不能自動解除依賴。

簡易↔進階互轉保存每個生成頂點；一次 confirm 只記一次 Undo/Redo。
live 宿主非法縮小時，普通 DSL 影響預覽也列出所有受影響 run。

## 完整診斷與來源圖

preview.sectionProfiles.violations 與 preview.violations 提供：

- member 的 memberId、profileId、rectangle、originalRectangle、條號及 expected/actual。
- V_PROFILE_OUTSIDE 的 outsideRegions：整數水平帶矩形分割，正面積聯集恰好等於構件矩形超出斷面的區域。貼邊沒有正面積，不報錯。
- V_PROFILE_OVERLAP 的 otherMemberId、另一構件原／新矩形與精確 intersection。
- 每個失效尺寸來源；每個失效 run 的長度、宿主或全部 D1 越界頂點。

區域分割至多 (32+1)×(32/2+1)=561 個矩形／構件，不截斷。
128 個構件的 8128 個違規配對全部輸出；幾何完整度由固定 World 容量保證。
拒絕的 trial 不寫 live World、revision 或 history。

typed source-inspector 新節點：section-profile:<id>、profile-member:<id>、profile-run:<id>、panel-spec:calcium-silicate-6。
member 引用 profile 及具型別的 spec／parameter-field／material-version 或 panel-spec；run 引用 profile、其構件及長度來源。
live simple run 額外引用 placement；copied host 沒有 space／model 假依賴。
名稱與 sourceDescription 不計入定義／值 fingerprint；實際 frame、range、尺寸、方位與來源計入適當 fingerprint。
來源圖達既有全局 nodes／edges 容量才回 complete:false；不因有截面資料而省略新型別。
scenario 原生驗證使用相同 typed inventory，三個物件域與 panel-spec 字串身分完整保留。

## Scene、能力與舊消費端

完整 native dump 先保存既有來源，再寫：

```text
requires section-profile/1
section-profile profile BASE64_CANONICAL_JSON
section-profile member BASE64_CANONICAL_JSON
section-profile run BASE64_CANONICAL_JSON
```

payload 就是各 `put-*` 的 `value`。三種類型依序保存；含零構件 profile、未定位 run 與全部尺寸引用。
records 只允許 atomic native `loadfile`／scene parser，不允許 `line` 逐筆注入。
每次 parse 重新檢查 required marker；移除 marker、未知版本、重複 id、損壞／截短 record 或非法依賴均拒絕，live World 不變。

含新資料的 scene／native required_capabilities 必須列 section-profile/1。
section-profile-native/1 是原生工程接口標記，read 明示 simplePlacementSupported:true、diagnosticsComplete:true。
全產品 capabilities 的 section-profile/1 由整合分支在 decoder、建模器與 UI 保存 gate 均接線後統一啟用；
原生 read 不用 rendererSupported 欄位推測其他程序的能力。
未支援新能力的消費端仍須拒絕 required marker，且不得藉剝除 marker 默默丟失 records。

## 可重現驗證

專屬 build（每次來源變更後重建；sidecar 由既有 binary registry 產生）：

```sh
ulimit -s 16384
python -c 'from pathlib import Path; from tests import binaries as b; b.OUT_DIR=Path("/tmp/geometry-q38-complete-native"); raise SystemExit(b.main(["build","bridge","core"]))'
GEOMETRY_TEST_BRIDGE=/tmp/geometry-q38-complete-native/bridge python tests/test_section_profile_native.py -v
```

永久測試核對固定數字、真核心負例、完整 dump／fresh-process roundtrip、零 id、固定來源、不同 token、取消與過期、undo/redo、容量、全項診斷、兩種宿主、96 個合法宿主／方向組合、互轉與來源圖。
外部 oracle、aggregate／變異及最終 commit／binary 指紋另外記錄。
早期 dirty tree 結果保留原 head／狀態；可用完整受驗來源雜湊等值綁定後續 commit，但不得把原收據改標成當時已在最終 clean commit 上執行。

### I44 修正：剛好填滿凹槽的構件（2026-10-09）

原先 `V_PROFILE_OUTSIDE` 呼叫 `poly_contains_rect`（四角在輪廓內或邊上，且沒有輪廓邊穿過矩形內部）。
凹槽的兩條平行邊本身就落在矩形邊界線上時，四角都在邊上、也沒有邊穿過內部，整個落在 F 外的矩形被判成「在內」，
例如輪廓 `[[0,0],[100,0],[100,100],[60,100],[60,40],[40,40],[40,100],[0,100]]` 上的 R = [40,60]×[50,70]（寬度剛好等於槽寬）。
這與 D35「構件剖面必在 F 內」的面積條件矛盾。現在改用同一份診斷用的整數水平帶分割：差集非空即 `V_PROFILE_OUTSIDE`，
`outsideRegions` 也與判定同源（`section_profile_validation.inc` 的 `sp_rebuild`）。永久測試涵蓋兩種繞向、三個填槽尺寸（含精確 `outsideRegions`）、
槽開口向右的凹形，以及貼著槽緣、仍在材料側的構件仍合法。

共用函式 `poly_contains_rect`（`current_geometry.c`，D7 角材的 I5 路徑經 `boundary_contains_rect` 使用）本身沒有改；
同一弱點在那條路徑上的實測：承載面輪廓 `0,0 1000,0 1000,1000 510,1000 510,300 490,300 490,1000 0,1000`（槽寬 20）上，
沿 u=500 的 20×20 主支角材在兩側邊界材到位後，R6 回報「跨距歧義： [20,280] [300,1000]」，第二段完全落在槽內；槽寬改成 22 時只有一段。
那屬於 D7／I5，不在 Q38 範圍內，需另案處理。

### AC16 故障注入閘門（`tests/section_profile_mutation_check.py`）

提案 AC16 要求移除指定守門後，其列出的驗收案例（AC04–AC06、AC12、AC21、AC24；AC07、AC23；AC21）分別轉紅，且失敗訊息指得出是哪一條。本閘門目前證明的是較弱的事實：每個守門至少有一個指名殺手測試會轉紅，失敗訊息含該守門的條號或病因；這不是提案 AC16 逐條（AC04–AC06、AC12…全部轉紅）的對應；逐案例實際轉紅的測試與其對應的提案 AC 見下方「--explore 實測」。
`tests/mutate.py` 的既有清單只以 `current_geometry.c` 的場景裁判審核心，
沒有對 Q38 的檢查注入過故障，所以另有此腳本（Linux/WSL；比照 `tests/assembly_mutation_check.py`，不編入 `run_all.py`，因為每個案例要編一支 bridge）：

~~~sh
ulimit -s 16384
python3 tests/binaries.py build
mkdir -p tests/release-evidence/<日期>-q38-i44
python3 tests/section_profile_mutation_check.py --receipt tests/release-evidence/<日期>-q38-i44/q38-mutations.json --logs tests/release-evidence/<日期>-q38-i44/mutation-logs
~~~

在拋棄式複本中一次只改一處，共 42 個案例。native 37 個案例改 C 來源（拿掉 I43／I44／I45／I48／I49／I51 的守門、R36 的嚴格不等號、
面材 w < 915 與 6 mm 板厚、R38 的符號與軸、D38 互轉條件、I47 的終端頂點與 D1、PROFILE_CONTACT_LOST、「板長 1830 當成 L 上限」等），
重編 bridge 後跑 `tests/test_section_profile_native.py`；model 5 個案例改 Python 製模器（R37 的 L 形包絡、R39 包絡不計材料量、
面材不依 1830 切段、構件矩形軸向、局部 run 不被世界網格切分），在複本上對未變異的原生轉接器跑 `tests/test_section_profile_modeling.py`。
判為殺死須同時成立：指名的測試以斷言失敗轉紅（或錯誤訊息含該案例的 cause 字串）；失敗訊息含每一個 cause 字串（條號或病因）；
native 組另須重編 binary 與基準線不同；model 組只變異 Python 製模器，使用同一支 fresh、未變異原生 adapter，沒有變異 adapter 雜湊比較。編譯失敗、無說明的錯誤、逾時與 skip 都不算偵測，基準線必須先零 skip 全過。
2026-10-10 在 WSL 乾淨 clone（`~/ga-q38c`，受驗提交 `f0c4c71291af5cab699f54de8ac852aa35fa378e`，基底 `c254e1f`，rebase 無衝突）實測。
收據在 `tests/release-evidence/20261010-q38-i44/`（`README.md` 有指令、環境與檔案清單、`SHA256SUMS.txt` 有雜湊）：

- `section_profile_mutation_check.py`：native 與 model 基準線皆 exit 0、零 skip；42 例 41 killed、1 equivalent、0 survived，exit 0（`q38-mutations.json`、`mutation-logs/`）。唯一等價的是 SPM24（D38 進階轉簡易的「V 對應合法的 up」）：進階框架只可能由 `surface_frame_is_valid` 放行（單位座標軸、V ⟂ N），U = V × N，up = −V 恆合法、`legal_up` 恆真，這個拒絕項在實作上不可能不成立，所以沒有任何測試能演示它。
- 歷史 SPM41（f0c4c71）把精確面積改回 `poly_contains_rect` 後，`test_concave_not_four_corners_and_winding` 轉紅，訊息是 expected rejection 'V_PROFILE_OUTSIDE' but the candidate was accepted（`mutation-logs/SPM41.log`）。
- `python3 tests/run_all.py --build`：83 個 suite、2611 測試，2610 pass、0 fail、1 skip（Linux 上的 Windows GDI，具名允許清單），exit 0（`run_all.log`）；`test_section_profile_native` 26／26、`test_section_profile_modeling` 19／19。總數比開發樹量到的 2592 多，是因為基底前進到 `c254e1f` 後主線新增了測試。
- `python3 tests/mutate.py --check`：killed 40、crashed 1（M20，基底即有）、survived 0、equivalent 4、invalid 0、stale 0、blocked 0、retired 3，exit 0（`mutate-check.log`）；rebase 後帳本沒有過期，沒有重跑任何條目、沒有改動 `tests/mutants_results.json`。
- 託管 CI 受帳號計費阻擋（Actions job 秒失敗，不是程式失敗），以上 WSL 收據代替；需要 Chrome 的瀏覽器層閘門沒有跑。

歷史 42 例的 killed 不是全為斷言 FAIL：39 例由 AssertionError 偵測，SPM38／SPM40 兩個 model 案例由含指定 cause 的 ModelError（ERROR）偵測；原始日誌保留。

2026-10-11 審查後，SPM41 改為在 `sp_outside_regions` 的計數回傳丟掉恰一片正面積差集（`return n>1?n:0;`），保留 I44 具名反例及精確 outsideRegions 斷言。此單點故障不依賴 `poly_contains_rect` 是否已修正；新收據與來源閉包見 [雲端複核導讀](../tests/release-evidence/20261011-pr182-cloud-review/README.md)。舊 42 例收據不當成修改後全表已重跑。

#### 歷史 --explore 實測：逐案例紅燈與提案 AC16 的差異

`--explore` 對每個案例跑整個測試類別，收據是 `q38-mutations-explore.json`（日誌 `mutation-explore-logs.tgz`），逐案例的紅燈測試與失敗訊息在 `ac16-per-case-red-tests.md`。測試方法本身不帶提案 AC 編號，下表的 AC 欄是人工讀測試內容對應的結果，而且是方法層級：一個方法含多個 AC 場景，「含」不等於「該場景是導致轉紅的那一行」，失敗訊息才是實際斷言。

提案 AC16 三組要求的實測：

| 提案要求的突變 | 對應案例 | 提案列出的 AC | 實測轉紅 | 未被打紅 |
|---|---|---|---|---|
| 移除 P-I2（R ⊆ F） | SPM01 | AC04、AC05、AC12 | AC12 同場景（390 縮邊）；AC04、AC05 以相似場景轉紅（`all_violations`、`profile_geometry`、`concave`） | 無（AC04／AC05 非原始數字） |
| 移除 P-I3（互不重疊） | SPM02 | AC06、AC24 | 相似場景：`touch_edges…`（u=26 重疊 1 mm、面材 w=30 於 u=20）、`maximum_pair…` | 無（AC06／AC24 非原始數字） |
| 面材寬度 `w < 915` → `w <= 915` | SPM05 | AC21 | AC21 同場景（w=915 拒絕 `V_PANEL_WIDTH`） | 無 |
| P-R1 `<` → `<=`（u 向、v 向） | SPM03、SPM04 | AC07、AC23 | AC07 同場景（u=27 貼齊必須接受）；SPM03 另使 `named_sources…` 轉紅 | **AC23** |

與提案 AC16 逐條要求的差異：

1. **AC23 沒有被任何突變打紅。** 面材 w=346 貼在 M1、M2 之間並被接受的場景，不在被計入的任何測試裡：唯一把 `panel()`（u=27、w=346）貼在角材旁的 `test_source_index_typed_closure_and_display_identity` 被本閘門排除（它要求帶來源與建置收據的 registry binary，拋棄式變異 binary 沒有），modeling 測試也沒有 w=346。所以 P-R1 的 `<` → `<=` 只由角材貼齊（AC07）打紅，面材貼齊沒有獨立的紅燈證據。
2. **AC04、AC05、AC06、AC24 是相似場景轉紅，不是提案列的原始數字。** 提案用 (380,0)、27×27 於 (50,50)、(20,0)、w=346 於 (20,0)；測試用 u=26 的 1 mm 重疊、面材 w=30 於 u=20、凹槽輪廓上的 60×60 與填槽矩形。條文子句與診斷碼相同，但不是同一列的逐字場景。
3. **沒有「整個移除面材寬度上限」的獨立案例。** SPM05 是上限比較的差一（`<` → `<=`）；整個移除推論上由同一個 w=915 斷言抓到，但沒有實測。
4. 不在提案 AC16 列舉範圍、但本閘門另外證明有殺手測試的守門（I43、I46、I47／D1、I48、I49、I51、D36、D37、D38、D40、R37、R38、R39）見下表；其中 SPM11、SPM12、SPM28、SPM29 的紅燈測試沒有對應到任何提案 AC（它們守的是依賴交易與材料來源，提案 AC 表沒有列）。

42 例逐案例（`紅燈測試數` 是 `--explore` 下整個測試類別中失敗的方法數）：

| 案例 | 組 | 條號 | 突變 | 判定 | 紅燈測試數 | 紅燈測試所含的提案 AC（人工對應、方法層級、偏寬） |
|---|---|---|---|---|---|---|
| SPM01 | native | I44 | drop the member-in-profile containment check | killed | 4 | AC03, AC04~, AC05~, AC06~, AC12, AC13~, AC18, AC19~ |
| SPM02 | native | I45 | drop the member-overlap check | killed | 3 | AC06~, AC07, AC24~ |
| SPM03 | native | R36 | u overlap uses <= : edge-sharing members become overlapping | killed | 2 | AC06~, AC07, AC24~ |
| SPM04 | native | R36 | v overlap uses <= : members touching along v become overlapping | killed | 1 | AC06~, AC07, AC24~ |
| SPM05 | native | I46/D40 | panel width w < 915 becomes w <= 915 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM06 | native | I46 | panel width lower bound 1 becomes 0 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM07 | native | D40 | panel spec identity is no longer checked | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM08 | native | D40 | spec thickness 6 becomes 7 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM09 | native | D40 | spec w_max 915 becomes 914 | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM10 | native | I43 | drop the outline validity check | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM11 | native | D37 | run length accepts a D26 material source | killed | 1 | （無對應提案 AC） |
| SPM12 | native | D36 | material A/B field identity is no longer enforced | killed | 1 | （無對應提案 AC） |
| SPM13 | native | I51 | scene records no longer need the section-profile/1 declaration | killed | 1 | AC14 |
| SPM14 | native | I46 | timber orientation is not validated | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM15 | native | I46 | panel orientation is not validated | killed | 1 | AC03, AC04~, AC13~, AC19~ |
| SPM16 | native | R38 | V = +up instead of -up | killed | 3 | AC10=/~, AC14~ |
| SPM17 | native | R38 | negative directions (-u,-v) lose their sign | killed | 1 | AC10~ |
| SPM18 | native | R38 | dir +u/-u and +v/-v pick the wrong host axis | killed | 4 | AC10=/~, AC13~, AC14~ |
| SPM19 | native | I48 | p,q may lie outside the host range | killed | 2 | AC13~ |
| SPM20 | native | I48 | up need not be perpendicular to the run direction | killed | 1 | AC13~ |
| SPM21 | native | I48/D1 | simple-placement origin is not range-checked | killed | 1 | AC13~ |
| SPM22 | native | R38 | origin x component swaps p and q | killed | 3 | AC10=/~, AC14~ |
| SPM23 | native | D38 | advanced->simple conversion ignores the host plane | killed | 1 | AC11 |
| SPM24 | native | D38 | advanced->simple conversion accepts any V as up | equivalent | 0 | — |
| SPM25 | native | D38 | advanced->simple conversion takes the last host direction regardless of N | killed | 3 | AC10~, AC11 |
| SPM26 | native | I49 | PROFILE_CONTACT_LOST is never reported | killed | 1 | AC12, AC18 |
| SPM27 | native | I44 | outside-region split drops the right-hand remainder | killed | 4 | AC03, AC04~, AC05~, AC06~, AC12, AC13~, AC18, AC19~ |
| SPM28 | native | I49 | a member may reference a deleted profile | killed | 1 | （無對應提案 AC） |
| SPM29 | native | I49 | a run may reference a deleted profile | killed | 1 | （無對應提案 AC） |
| SPM30 | native | I47/D1 | generated run vertices are not range-checked | killed | 1 | AC09, AC13~ |
| SPM31 | native | R36 | A-v / thickness-u swap width and height the wrong way round | killed | 15 | （廣：15 個測試，幾乎涵蓋整個類別；見 ac16-per-case-red-tests.md） |
| SPM32 | native | D36 | panel orientation thickness-u is read as thickness-v | killed | 1 | AC20, AC21, AC22, AC25~, AC26 |
| SPM33 | native | D40/R37 | the 1830 mm sheet length is misused as an upper bound for the run length | killed | 15 | （廣：15 個測試，幾乎涵蓋整個類別；見 ac16-per-case-red-tests.md） |
| SPM34 | native | I51 | scene load accepts a duplicate profile id | killed | 1 | AC14 |
| SPM35 | native | I49 | section-profile records may be injected line by line outside an atomic load | killed | 1 | AC14 |
| SPM41 | native | I44 | back to poly_contains_rect: a rectangle exactly filling a notch counts as contained | killed | 1 | AC05~ |
| SPM42 | native | I47/D1 | only the start vertex of a run is range-checked, not the far end | killed | 1 | AC09, AC13~ |
| SPM36 | model | R37 | the reference envelope becomes the bounding rectangle of the outline (L shape lost) | killed | 2 | AC08~, AC14~ |
| SPM37 | model | R39 | the reference envelope is counted as material volume | killed | 3 | AC08~, AC14~ |
| SPM38 | model | R37/D40 | a panel is cut at the 1830 mm sheet length | killed | 1 | AC26 |
| SPM39 | model | R36/R37 | member rectangles are read with u and v swapped | killed | 6 | AC08~, AC09, AC10~, AC26 |
| SPM40 | model | D39 | an unplaced (local) run is cut by the world grid | killed | 11 | AC08~, AC14~, AC26 |

這輪故障注入先後逼出多處測試缺口（面材規格身分、兩種方位字串、D37 不收 D26 材料、簡易定位原點的 D1、I47 終端頂點、
刪斷面時只剩成員或只剩 run 仍引用、已載入場景後的逐行注入）與上面的 I44 缺陷；這段 f0c4c71 I44 歷史切片以加強既有測試方法補缺口，當時沒有新增方法或改 expected。後續 f3c87c21 新增 `test_section_profile_mutation_check.py` 九項及一個 suite，aa4067b 清冊為 84 suites／2620 項；既有 83 suites 期望未放寬。`tests/mutants_results.json` 因核心來源變動依 `tests/mutate.py` 的規則整份重跑重生。

### 前一個有界切片的歷史驗證（非本版收據）

產品提交 `569b229` 的永久原生測試 13／13、獨立外部原生 oracle 18／18、
舊 JS／Python／C 消費端拒絕檢查 6／6 均通過。
完整非瀏覽器 aggregate 實跑 **70 suites：2174 pass、0 fail、1 個具名 Windows GDI skip，exit 0**。
以該次完整執行更新 expected：只新增原生 suite 13 項，Node 共用 suite 由 510 增至 513；既有 floor 不降低。
這不是 CDP、實體裝置、Windows 或上述未完成產品層的驗收。

核心來源變更後也實際重新編譯／執行 mutation inventory，未只改收據雜湊：
未變異 baseline 139／139；48 筆為 40 killed、1 crashed、4 equivalent、3 retired，
0 survived／invalid／stale／blocked，exit 0。等價項亦經原 runner 的實跑核對。
工具保留執行當時的 HEAD `5cc1ffa`（加凍結中的本切片修改）；
收據的 source／closure 指紋與 `569b229` 核心來源相符，不能解讀為未修改 main 的測試。
提交中的 `tests/mutants_results.json` 是實跑生成的收據；`mutate.py --check` 是其後的 freshness 核對。
