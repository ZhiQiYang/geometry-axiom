# 無限網格與邊界錨點配置（GEO-215）

2026-09-28。使用者明確要求「無限條格線、每條無限延伸」，並授權「規劃後開始修正」。GEO-214 的有限排法物件未滿足這個概念；本文件修正物件定義與驗收，依本次授權先採納條文，再實作。舊 `GRID-SYSTEM-PROPOSAL.md` 僅說明上一版及其相容語意。

## 使用流程

1. 在畫布建立獨立網格：名稱、兩軸間距或面材＋縫、相位、可選主支方向；不填總條數。
2. 進入網格工作區，平移、縮放，直接選任意正／負索引 cell。展示視窗不保存成幾何範圍。
3. 選一個已存在的邊界（未放置也合法），點選實際外環或孔環頂點，選 cell 內位置，再預覽確認。
4. 產生獨立的「網格配置」卡片，保存來源及錨點關係。邊界內的格線是推導結果。
5. 要沿格線放角材時，明確將配置套給引用同一邊界的承載面；不暗建面或角材。
6. 修改格距、被引用頂點或對齊位置時，預覽所有依賴，再整筆確認／取消／復原。來源、配置、頂點身分皆保存重開。

## 條文逐條差異

### D29：無限規則與有限舊檔分開

```diff
- 新網格由 EXPLICIT／SERIES count／PANEL_LAYOUT 的有限來源構成。
+ 新網格保存 REPEAT(phase,step) 或 REPEAT_PANEL(panel,gap,anchor)，每線兩端無限延伸，k∈Z。
+ REPEAT 的 c(k)=phase+k·step；REPEAT_PANEL 的 pitch=panel+gap，phase=anchor+panel+floor(gap/2)。
+ 不保存總條數、第一條／最後一條、視窗或裁切線段；一軸可未定義，至少一軸存在。
+ cell(i,j)由 i/i+1、j/j+1 圍成；選 cell 須兩軸存在，不使用邊界或視窗邊作假格線。
+ 舊 explicit／series／panel 與 from-system origin 保持原义，標為 legacy-finite；新舊軸不得混用。
```

### 新增 D30：配置與穩定頂點

```diff
+ GridBinding 是 World 獨立物件：id、boundary、system、vertexKey、signed cell(i,j)、cell內有理比例(α,β)。
+ 不要求 boundary 已放置；同一來源或邊界可有多個配置。u/v 同名軸對應，第一版不旋轉、鏡射或縮放。
+ cell內點=(phase_u+(i+α)step_u, phase_v+(j+β)step_v)，translation=邊界頂點−cell內點。
+ 平移是衍生值，不和錨點並列保存為第二份來源；修改格距或頂點仍保持同一對齊關係。
+ 介面沿用局部 u向右、v向下；左上(0,0)、中心(1/2,1/2)、右下(1,1)，相機不改錨點。
+ 頂點key在boundary內唯一，首次配置或显式keyed編輯才初始化；舊未配置邊界的dump不增加身份資料。
+ 顯式boundary-keyed更新保存頂點身份；普通重宣告只容許舊key在新輪廓唯一同座標匹配。
+ 刪掉被配置引用的key、重複key、模糊配對或沒有明示身份的移點均拒絕，不按同一陣列位置猜角點。
```

### D9／D10／D12／D19／I10／I23／I25：來源與索引

```diff
+ D9 保存配置、穩定頂點key、帶符號格線／cell身份；不保存推導平移或取樣格線。
+ D10 主格可 from-binding B，承載面必引用同一boundary；線引用使用signed lattice k，不使用可見陣列序號。
+ D12 新增 grid-binding 卡片位置，仍不參與幾何。
+ D19 無限主格的子格使用 lattice-cell i j，四邊固定是 i/i+1、j/j+1；其後按C∩F裁切。
+ I23 對無限主格不套用「可見條數改變即鎖住子格」；不可見格線仍存在，角材另驗有效範圍。
+ I10/I25 的64條是具體查詢／子格陣列容量，不是無限來源或配置的條數；超限明報，不截斷當完整結果。
```

### I37：合法性及原子性

```diff
- 每個系統的有限座標／條數上限64。
+ 最多16個系統、32個配置；來源不因未指定範圍、範圍內線多或沒有可見線而非法。
+ 輸入與實際求值遵守D1；整數溢位、無法精確表示的半毫米對齊明確拒絕，不能暗取整。
+ source、binding、keyed boundary修改皆重算完整依賴，I8a預覽確認且原子提交。
+ 首次key初始化與配置建立是一筆交易；失敗不得留下key資料、隱藏surface或半份配置。
+ 不能刪仍被引用的來源／配置／頂點；from-binding的主格不能普通軸編輯或工程綁定覆蓋。
+ legacy ordinal 與 lattice 身分不可藉同ID重宣告偷偷互轉；已保存有限檔不自動變無限。
```

### R32：求值、查詢、保存

```diff
- 按有限來源加origin後展開全部座標。
+ 單線由帶符號k以O(1)求值，實際範圍用ceil/floor算需要的k，再按真實外環與孔裁切。
+ 查詢 exact 過限只拒絕該查詢；sample 明示stride與非完整結果，以全域k=0為取樣基準，不重編號。
+ 視窗太密時可抽樣顯示並明示；cell命中仍用真實格距，不把大格當原始cell。
+ dump順序含boundary/keymap、system、binding、placement主格與後續引用；保存來源，不保存取樣結果。
+ 重開、復原、重做保留同一頂點key、signed索引與精確對齊比例。
```

## DSL 與橋接契約

```text
grid-system S name-hex HEX main-along u|v|none u repeat PHASE STEP v repeat-panel PANEL gap GAP from ANCHOR
grid-binding B on-boundary D from-system S vertex-key K cell I J anchor NU DU NV DV
grid-binding B on-boundary D from-system S vertex outer INDEX geometry-hash HASH cell I J anchor NU DU NV DV
grid-binding B on-boundary D from-system S vertex hole H INDEX geometry-hash HASH cell I J anchor NU DU NV DV
boundary-vertex-keys D outer K0 K1 ... hole K... [hole ...] next-key N
boundary-keyed D geometry-hash HASH outline K:u,v K:u,v ... [kind ...] [fixity ...] [hole K:u,v ... [fixity ...]]
grid G on P from-binding B
subgrid SG parent G lattice-cell I J divisions u NU v NV
grid-query system|binding|grid ID rect U0 V0 U1 V1 mode exact|sample limit N
delete grid-binding B
canvas-pos grid-binding B X Y
```

`repeat`、`repeat-panel`、`none` 可用於新來源；不允許兩軸皆none或混入legacy有限軸。比例分母正、比例介於0與1，約分保存。首次 `vertex outer/hole` 建立keymap與配置於同一候選；正式保存一律 `vertex-key`。首次選點及 `boundary-keyed` 必核對核心回傳的最新 geometry-hash，不能僅靠前端檢查。雜湊描述 ordered loops、座標、kind/fixity，不含畫布位置或placement。`boundary-vertex-keys` 僅初始／重放，不能重綁已有key。`grid-query` 為唯讀橋接查詢，N=1…64每軸，不是場景指令；查詢失敗不改World。

無限的數學定義不受D1視窗或64條限制；機器可表達的索引是signed int64，超出時明確拒絕。配置內格線用等價式 `localLine(k)=vertex−α·pitch+(k−I)·pitch` 精確求值，避免先算巨大 `I·pitch` 再相減。D1限制實際幾何輸出，不要求整個無限網格都落在D1。衍生translation若無法以int64表達，API回null及明示狀態，不能因此拒絕仍可精確求值的配置或回寫近似數字。

頂點key表保存 `next-key` 高水位，0表示uint32耗盡；刪最高key後也不退回，重開不重用已刪除key。已有身份表不得改綁或降低高水位。

`objects.gridSystems` 增加 `mode: infinite|legacy-finite`；`objects.gridBindings` 包含 id/boundary/system/vertexKey、decimal-string cell索引、約分anchor、衍生translation、applications與canvas-pos。boundary讀取提供每頂點key/loop/index/u/v，未初始化時明示。references主格增加bindingId、indexSpace:lattice|ordinal；lattice線與cell索引用十進位字串傳輸，避免JavaScript精度損失。舊ordinal維持既有格式。

query回傳mode/exact/rect及兩軸firstIndex/lastIndex/total/stride/lines；每線含index、coordinate、segments。所有index/count/stride可用十進位字串；sample不得標為exact。preview包含來源、配置的錨點／平移／裁切變化及後續主格／子格／guide／角材。

## 驗收（不得以舊有限版測試替代）

- N01：來源不含count，k=-2/0/2均可求；線超出顯示窗仍有同一身份，平移縮放不改dump。
- N02：未放置boundary可與來源組合，沒有暗建placement或角材；兩個boundary可共用来源。
- N03：實際點頂點、負索引cell及左上／中心；保存vertexKey與cell/比例，不只translation。
- N04：pitch600/400、cell(-2,1)、vertex(100,200)：左上translation(1300,-200)，中心(1000,-400)。改800/500後分別為(1700,-300)、(1300,-550)，頂點保持不動。
- N05：顯式帶key向四側放大邊界，新增外側格線而原k不變；重排同座標仍是同一key，刪引用key拒絕。
- N06：601mm中心導致半毫米時拒絕且無殘留；精確比例、負除法、D1邊界與溢位均有反例。
- N07：密集來源與配置仍合法；exact超限明報，sample明示稀疏顯示且不變更線或cell身份，縮放後可恢復密度。
- N08：套到實際承載面後，guide／角材引用signed k；面外格線仍可引用，材料有效範圍另驗。無限子格使用真正lattice-cell，擴大範圍不重編父線。
- N09：來源與頂點變更預覽所有配置；取消、過期確認、依賴失敗全部回滾；支持整筆復原重做。
- N10：舊finite保存維持原線數與索引；新配置正式下載→清空→開檔，來源／key／cell／錨點／位置／推導完全相同。
- N11：真實桌機及390px操作；核心、模型相容性、完整cdp_test、唯一正典同步與見證圖驗證。

## 實作分工與順序

先提交採納後的SSOT，讓模型版本指向實際條文commit。核心處理無限來源、頂點key、配置、signed引用、查詢及模型適配；介面處理來源/配置卡片、獨立工作區、真正點選與既有面內signed引用；測試以固定數值oracle驗收。最後同步唯一閱讀器、保存舊版本相容白名單，完整驗證後更新同一試用服務。
