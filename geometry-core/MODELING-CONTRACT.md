# GEO-129 正交 3D 建模交換契約

規範來源：`公理層.md` 的 D20–D25、I26–I33、R24–R30。本檔定義其資料介面、確定性編碼及驗收。
Q38 的 D35–D40／I43–I51／R36–R40 另以可宣告的 `section-profile/1` 延伸；完整欄位與座標語意見 [斷面模型介面](SECTION-PROFILE-MODELING.md)。
版本：`orthogonal-model/1`。GEO-130 已提供 **C 舊場景驗證＋Python 精確參考執行器、CLI、HTTP 與 OBJ 輸出**。
本節 GEO-129 的 extensions 型別不放入舊 C World／DSL；Q38 斷面三型別則由原生 World／DSL 求值。使用方式與實測界線見 `MODELING-RUNTIME.md`、`MODELING-VALIDATION.md`。
不能把 JSON 範例可解析、閱讀器同步或文字審查說成 3D 幾何驗收通過。

## 1. 與既有資料的邊界

保留 D1 整數 mm、有號正交框架及 D3/D4 分離。第一期只處理軸平行平面、多邊形與有界正交體積。
所有新增引用用 `{kind,id}`，不得只傳數字。id 仍在 uint32 範圍內，各 kind 自有命名空間。
引用目標必先存在；跨新舊型別比較不得合併 id。新型別無 UI 或 DSL 簡写的隱式默认值。

舊 `Space` 是 `slot-space/1`，不改 parser、不遷移既有檔案。它的 closed 欄位不可轉成 shell 的水密旗標。
新型別序列化為 extensions JSON，**不是已被 C parser 接受的新 `.scene` 指令**。
完整執行器須同時理解 base_scene 及下列新增定義；現行 C 不能用忽略 extensions 的方式假裝成功載入。

## 2. 定義資料

`definitions` 必含 `base_scene` 與 `extensions`。base_scene 是由同版 C 規格 R4 dump 產生的正典 DSL：
LF 換行、末尾一個 LF、不含註解或 canvas-pos；保留具名規格、局部輪廓與孔、frame、柱樑和角材引用。
画布位置與名稱等純展示資訊放到獨立 `presentation`，不影響幾何求值。例題輸入可以尚未正典化，交換包不能。

extensions 是按照依賴順序排列的非空或空陣列。就緒節點有多個時按 `(kind 的 Unicode 碼點序,id 數值)` 取最小者；
不得把有序 KEEP 成員清單重排。未知欄位拒絕，避免拼字錯誤被當成沒有設定。型別必備欄位如下：

| kind | 必備欄位 | 引用及限制 |
|---|---|---|
| extrusion | id, placement_id, lo_spec, hi_spec | carrier 必存在；兩規格名不得被內插成無名值 |
| shell | id, uses | 非空；每項僅 placement_id, orientation, purpose；同 carrier 不重複；orientation 整數 ±1；purpose 必明寫 boundary 或 calculation-cap |
| composite_space | id, shell_id, obstacles | 一個 shell；obstacles 可空，型別引用不得重複 |
| composition / KEEP | id, op, inputs | op=`KEEP`；非空有序、不重複引用 |
| composition / UNION | id, op, inputs | op=`UNION`；至少兩個互異引用，正典化按 kind/id 排序 |
| composition / DIFFERENCE | id, op, base, tools | op=`DIFFERENCE`；工具非空、無重複；tools 按 kind/id 排序 |

表中 composition 仍是一個 kind，三個 op 互斥，禁止混用 `inputs` 與 `base/tools`。
工具可引用同一既存 base，`A \ A = EMPTY`；這不等於組合自我引用成環，後者仍拒絕。
shell uses 正典順序按 placement_id 數值；obstacles 正典順序按 kind/id；不以排序翻轉 orientation。
uses[].purpose 區分一般邊界使用與 R26 顯式計算封口，兩者都不宣稱存在 RC 材料；
缺值／未知值 INVALID，無預設；不改幾何、orientation 或 I27/I28，封口仍須有明示 placement。
來源 operation_path 必經該 shell 的 uses 索引，讓接收端從 definitions 還原用途，不把用途混入 cut 角色。
所有必備欄位不得為 null。零障礙是 `[]`，未知障礙不是空集合；要宣告障礙必提供可求值定義。

布林和 obstacles 接受 column、beam、已合法放置的 timber、extrusion，以及返回 solid-set 的 composition。
EMPTY composition 也是已解算 solid-set，遵循 D23 空集合代數。KEEP 可接受 placement、上述實體、shell、KEEP／布林 composition；
不收 composite_space，避免 geometry / enclosure / clearance 在巢狀成員中產生角色歧義。
不提供材料／房間實體之間的隱式型別轉換。若希望對淨空結果再做新的運算，需另立型別契約，不能偷用 composite_space id。

## 3. 根、角色與目標

request 精確欄位為 `roots`（非空不重複型別引用陣列）、`role`、`target`、`allow_partial`（布林，預設 false）。
同一請求的 role/target 適用全部 roots；不同角色使用不同請求，輸出可並列保存但不能混成同一物件。

| 根型別 | role | surface-set | solid-set |
|---|---|---|---|
| placement | geometry | 有位置、含孔的面 | INVALID：未定義實體構造 |
| column / beam / timber / extrusion | geometry | 材料邊界面 | 材料體積 |
| shell | geometry | 有向開放／閉合殼，保留使用者方向 | INVALID：零厚度殼不是材料體積 |
| composition: KEEP | geometry | 遞迴各成員，保留身分 | 每項須能輸出 solid-set；任一型別不合則整根 INVALID |
| composition: UNION / DIFFERENCE | geometry | 結果外表面與內腔面 | 全部體積分量或 EMPTY |
| composite_space | enclosure | 已定的殼面，可開放；不宣稱已有 V | 殼水密且方向正確才输出 V；開放則 INCOMPLETE |
| composite_space | clearance | 已定淨空的全部邊界面 | 已定淨空的全部體積分量 |
| profile-run（section-profile/1） | geometry | INVALID：本能力只接受 solid-set | 各構件完整實體＋明標 reference 的凹形包絡；未定位時保留 local 座標 |

未列出的根／角色配對 INVALID；boundary、未放置角材或 slot Space 不能被猜成 3D 建模根。
open shell 作 geometry/surface-set 可以 COMPLETE，表示面本身已定，並仍記 `closure:"open"`。
CompositeSpace 的 clearance 無論目標為何都需要已定 V；開放殼為 INCOMPLETE。closed shell 朝內若僅作
geometry/surface-set 可保留朝內方向；作 CompositeSpace 時違反 I28，必拒絕定義，不能用 INCOMPLETE 掩蓋。
缺 spec、找不到 carrier、非法 frame、非流形殼等是 INVALID 定義；不提供可保存這些非法定義的草稿模式。

partial 以 request root 為原子，診斷可深入子路徑。例：KEEP 內有未封閉 clearance 在本版因型別不合先拒絕，
而多根 CompositeSpace 中只有一間開放時，allow_partial=true 可輸出另一間閉合房間，整包仍是 INCOMPLETE。
任何已知 INVALID > UNSUPPORTED > INCOMPLETE；實作沒有能力判定的部分只報 UNSUPPORTED，不臆測有效性。
每根 COMPLETE/EMPTY 均為成功求值；全部無幾何時整包 EMPTY，其餘全部已定時 COMPLETE。

## 4. 交換包與幾何記錄

頂層必含 `manifest`, `definitions`, `request`, `derived`, `diagnostics`；可另含 `presentation`。
manifest 欄位：`schema:"geometry-model-package/1"`、`profile:"orthogonal-model/1"`、`axiom_revision`
（來源 Git full SHA）、`axiom_sha256`（條文 UTF-8 bytes，**先把 CRLF 正規化成 LF** 再雜湊——行尾是簽出方式、不是條文內容；不正規化的話同一份條文在 Windows 與 Linux 會算出不同值，套件就不可重現。見 GEO-153）、`generator:{name,version}`、`capabilities`、
`units:"mm"`、`coordinate_system:{handedness:"right",up:"+Z"}`、`source_sha256`、`geometry_sha256`。
capabilities 為有序能力字串集合：`extrusion/1`, `shell/1`, `composite-space/1`, `solid-composition/1`, `model-export/1`；
集合與實際版本必符合 I32。只实现 extrusion 的程式可以自稱该子能力，不能自稱完整 orthogonal-model/1。

來源另可要求 `engineering-spec/1` 與 `parameters/1`。含參數來源的套件保留所有卡片（含未使用欄位）、AST、固定身分與引用，原生重放後才建模；畫布位置仍移入 presentation。缺少能力或宣告舊公理版本時明確拒絕，不能將引用改寫成有效數字。參數版公理來源為 `802f9bda1b1b8ab046f059e115dbf05a44da10df`，LF 正規化 SHA-256 為 `b19009682ba5b3e7150341ae1b5190629cb03985d500d382aa918438fb548c0b`。舊版無參數套件沿用對應版本驗證。細節見 [參數操作契約](PARAMETERS-CONTRACT.md)。

交替相位版採 `ccbec5fe9e4b056bcd5673fb9f69a54e888ea4e6`，LF 正規化 SHA-256 為 `264d8c5d2fa4e513418fbd611f2ef6f8d597def51d89805a75e9e21d0d24e8fe`。D10b / I24 的 stagger、參數引用與 band 交由同一個原生 C parser 求值並完整重放，不在 Python 另造座標；模型包保留來源身分。舊參數版（含 `82074011...`）可重建原本未錯開的來源，但不得夾帶 stagger 或 band 宣稱舊版已支援。精確版本配對與來源雜湊守門仍保留。

derived 必含 `status`, `objects`。objects 每項包含：

- `root`：輸入根型別引用；`member_path`：KEEP 成員 0-based 索引路徑（一般非 KEEP 為空陣列）。`section-profile/1` 的材料構件另用 `[member_id]`，包絡為 `[]`；不是 KEEP 陣列位置。
- `role`, `status`, `representation:"mesh"`, `closure:"open"|"closed"|"empty"`。
- `component`：體積分量編號；面物件不適用時為 null。獨立面、單一殼及每個實體體積分量分別成 object 記錄。
- `vertices_mm`：依 R29 排序的三維整數陣列；`triangles`：同向三個頂點索引的陣列，不含退化三角形。
- `face_sources`：與 triangles 等長的來源集合陣列；`boundary_shells`：每殼的三角形索引集合及 `outer|cavity|open` 角色。
- `volume_mm3` 必填：本 object 的已定材料／空腔／淨空體積為非負十進位整數字串，EMPTY 為 `"0"`；
  placement、僅作 geometry 的 shell 或開放 enclosure 為 null。實體即使選 surface-set 仍填其已定體積。
  多個體積分量各填自己的體積；不得省略欄位或用 JSON 浮點近似大整數。

closure=closed 的面集合仍須檢查 role/根型別，不能只靠 closure 升格為 material solid。
空結果保留 root/status=EMPTY 的 object 記錄，所有幾何陣列為空、component=null，diagnostics 記 EMPTY_RESULT。
INCOMPLETE 根沒有幾何 object；每個被省略根必须有 diagnostics。其他成功根依 partial 原子規則輸出。
diagnostics 每項精確記 `root`,`path`,`code`,`clause`,`message`；缺欄位／缺來源可另記 `missing`（型別引用或規格名）。
已知必要但缺少封閉面的開放殼，用 boundary edge 座標報缺口，不捏造未存在的面 id。

## 5. 唯一化、來源與摘要

切分網格按 R29 取自整個選定依賴閉包，含各實體完整求值邊界；別的未選畫布物件不參與。
每個 root／KEEP 成員先獨立求形狀，再套共同網格；只有明示布林能刪掉相交物件的內表面。
體積分量按其最小佔用 cell 的 `(x_lo,y_lo,z_lo)` 數值排序；分量間不共用頂點。
內部連通但含空腔的分量保留全部外殼／內腔殼，不把空腔當新材料分量。
同一 geometry object 的殼按最小有向三角形頂點序排序，再派本版本內編號；跨版本不保證 mesh 索引穩定。

對每一最終矩形片，以其相對內部被來源面完整覆蓋為條件選來源；邊／點接觸不算覆蓋。
來源由實際運算依賴路徑傳遞：擠出為 bottom_cap/top_cap/outer_side/hole_side；既有柱樑/角材為其六面特徵；
surface 為 placement 的有效面，另追溯 boundary（如有）。布林保留所有覆蓋該片、在依賴路徑上被使用的來源面，
並記沿 DIFFERENCE 工具路徑的 cut 角色；同平面不同來源不得只留一個。orientation 以輸出結果法向另記，不改來源。
每個 face_sources 記錄固定欄位為 `origin:{kind,id}`, `feature`, `placement_id`, `boundary_id`,
`loop_index`, `edge_index`, `operation_path`, `role`, `normal_sign`，不得自由增刪標準欄位。
基礎 origin.kind 只用 placement / column / beam / timber / extrusion；布林與 KEEP 由 operation_path 記路徑，不冒充原始面。`section-profile/1` 另用 profile-run，來源路徑與 reference 角色見其延伸契約。
feature 固定如下：placement 用 `surface`；extrusion 用 `bottom_cap`,`top_cap`,`outer_side`,`hole_side`；
column/beam 用 `-X`,`+X`,`-Y`,`+Y`,`-Z`,`+Z`；timber 用 D7 的 `A0`,`A1`,`B0`,`B1`,`START`,`END`。
placement_id 為該原始物件所引用的 carrier（placement 自指），沒有 carrier 的 column/beam 為 null；
boundary_id 為其 carrier 引用的 D3 id，自帶 rect 或無 carrier 為 null。外環 loop_index=0，第 i 個孔為 i+1（i 從 0 起）；
outer_side/hole_side 的 edge_index 沿来源環原始 0-based 邊索引；cap、surface 與盒體六面兩個索引均為 −1。
operation_path 是沿正典定義從 root 下行的欄位／陣列索引字串，例如 `["inputs","0","tools","1"]`；原始根為 `[]`。
路徑至少含一次 DIFFERENCE 的 tools 邊時 role=`cut`，其餘=`boundary`；這是来源用途，不用它推算法向。
normal_sign 是結果法向相對原始 feature 法向的 ±1；原始 placement 用 N、擠出／盒／角材用各原始材料面外法向。
來源鍵為 `(origin.kind,origin.id,feature,loop_index,edge_index,operation_path,role)`：
字串按 Unicode 碼點序、id/索引按數值，缺索引用 −1，operation_path 是從 root 起的引用欄位與索引字串陣列。
集合去完全重複後按该键排序；正規化可拆 source 邊，但不重編來源 loop/edge 索引。
若最終片找不到來源則拒絕，不能填 unknown 後冒充追溯完整。

四點環以法向排序並從 XYZ 數值最小點開始；三角形仍保留 (0,1,2)/(0,2,3) 的朝向。
排序比較採有向世界頂點序及來源鍵，不採記憶體地址、哈希表遍歷順序或相機深度。
derived.objects 按 `(root.kind,root.id,member_path,component)` 排序，路徑與數值逐元素比較，null component 排在 0 前。
共享頂點只限同一 object 記錄，KEEP 中相同來源經不同巢狀路徑出现仍各自輸出，不折叠身分。

規範化 JSON 只收 object/array/string/boolean/null/整數，禁止浮點與 NaN；object keys 按 Unicode 碼點排序，
UTF-8 無 BOM、無縮排與多餘空白、不逃逸非 ASCII 字元、控制字元依 JSON 短逸出優先，其餘用小寫 `\u00xx`。
字串不做 Unicode NFC 或其他文字改寫；正負零均編碼為 0；摘要輸入不加末尾換行。
可用等價於 Python `json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)` 的整數域實作。
source_sha256 = SHA-256(規範化 definitions)；geometry_sha256 = SHA-256(規範化 derived)。
公理摘要與來源摘要分開；presentation、生成時間、相機與 manifest 不進這兩個摘要，避免自我引用。
同一來源定義、請求、算法版本的標準 derived 相同；更換根集合可改共同切分及摘要，但不得改實際幾何集合。
外部格式適配器另外聲明單位／軸轉換及精度，不把其二進位編碼差異稱為公理不同。

## 6. 交付驗收

可解析的輸入與預期結果見 `modeling-cases.json`；向量本身不是測試報告，實際執行結果另記 `MODELING-VALIDATION.md`。
每案都必須：解析→能力檢查→求值→拓撲驗證→輸出→獨立重建比較。僅檢查 JSON 不構成 pass。

| 驗收 | 必须成立 |
|---|---|
| M1 帶孔牆、反向擠出 | 貫穿孔不填、厚度及 XYZ 範圍正確、完整水密材料邊界 |
| M2 L 形八面空間 | 六段立面加頂底可閉合，面向重複合法，凹口不填成 AABB |
| M3 開放與非流形 | 缺頂可輸出面但不可報確定體積；點捏合／三面共邊拒絕 |
| M4 KEEP 與 UNION | 重疊 KEEP 不消面／不丟身分；UNION 去內部面且體積正確 |
| M5 DIFFERENCE | 內腔、多塊、全空及交換順序各自正確，空結果可再次參與運算 |
| M6 依賴與回滾 | 規格／frame 變更重算，非法候選與刪被引用來源完全回滾 |
| M7 部分輸出與能力 | root 原子、列全部缺件，未知版本／能力不能partial混過 |
| M8 重建與確定性 | 另一獨立實作從定義重建一致；同版標準陣列與摘要相同；改畫布不改摘要 |

## 7. 現況与後續工作

GEO-129 首次交付只有規格；GEO-130 接續實作的參考執行器已執行 18 組向量，並有獨立網格與交易檢查。
不能把這些測試等同於另一套完整幾何引擎已通過 M8 的跨實作符合性驗收。
新增型別的 C data model／DSL 與畫布 UI 仍待接入；目前可透過 Python API、CLI 或 HTTP 使用新能力。
OBJ 適配器已提供整數 mm 幾何，來源及語意仍由 JSON 交換包保存；GLB／SketchUp 專用適配器另行實作。
