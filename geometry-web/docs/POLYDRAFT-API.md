# POLYDRAFT-API.md — polydraft.js 模組合約

> 本檔是 `geometry-web/polydraft.js` 的介面 SSOT,供主畫布「面·多邊形」(P)與面內工作區
> 「重畫外環」(e)兩處呼叫端共同遵守。行為規格(何時觸發、畫面長怎樣)在
> `RC-POLYGON-PLAN.md` §5.A.1(🔒 Q13–Q16);本檔只定「純函式簽名與資料形狀」。
> `polydraft.js` 規則:純邏輯,不碰 DOM、不送 bridge(不呼叫 `api`/`emitLine`/
> `emitBoundary`,不 `import`/`require` 任何 DOM API),所有輸入輸出都是 plain
> object/array,可在 Node 直接呼叫測試。
> 載入方式:`geometry-web/index.html:527-528` 目前依序 `<script src="reference-ui.js">`
> → `<script src="app.js">`(classic script,無 `type="module"`)。`polydraft.js` 依同
> 慣例掛 `window.PolyDraft`,`<script src="polydraft.js">` 需插在 `app.js` 之前——這是
> HTML 改動,**不在本次四份文件的交付範圍內**,留給下一個實作 agent 去加。

## 0. 閉合驗證的設計原則(GEO-178,🔴 改 `polydraft.js` 前必讀)

連續三輪對抗審查(F1/F2、G1、G3/G4)找到的是**同一個根源**的四個出口:「有些新邊沒走
檢查」與「拿化簡後的形狀去判合法」。以下三條是原則,不是補丁——任何新的落點/收尾管道
都要照這三條接上去,**不要再對個別案例加 gate**。實作在 `polydraft.js` 檔頭同名段落。

1. **草稿折線不變式(增量維持)**。任何時刻 `pts` 構成的折線都滿足:每邊軸平行且非零長、
   相鄰兩邊互相垂直(共線同向在落點當下就併成一條邊、共線反向一律 `BACKTRACK`)、
   非相鄰邊完全不接觸(端點觸碰也算)、且不接觸 `existingEdges`。
   **所有**會動到 `pts` 的管道都必須走同一道 `evaluateNextPoint` 才准改 `pts`:
   `place`、`applyTypedLength`。(G4 根因:`applyTypedLength` 曾經完全不檢查,是唯一
   能把自交頂點塞進草稿的管道;`place` 序列本身走不到 G3 那個點。)
2. **閉合 = 對 raw 環做一次總驗證**。`tryClose` 把閉合段接上去後,對**還沒去共線的**
   原始點列做總驗證,規則逐條對齊 `current_geometry.c::poly_loop_is_valid`,另加一條
   相鄰邊規則(相鄰兩邊只准共享那一個端點,共線同側非法)。這道總驗證涵蓋「每一段新邊
   都要被檢查」:直接閉合的 `L→F`、補角的 `L→C` 與 `C→F`,都對草稿自身所有已定邊 +
   `existingEdges` 檢查;閉合段的相鄰邊是末段與首段(照 `poly_loop_is_valid` 的相鄰排除)。
   **絕不可以拿去共線後的點列判合法**——G3 就是這樣被放行的:raw 5 點 core.exe 拒絕、
   deduped 4 點 core.exe 接受,模組拿後者當通行證,送出使用者沒畫的矩形。
3. **去共線只是輸出前的化簡,不承擔任何判合法責任**。`dedupeLoop`(內部函式,對應既有
   `feDedupe`)只在原則 2 通過後才跑,用途是拿掉共線贅點(收尾段與首段/末段共線時,
   `F` 或 `L` 會變成沒有轉彎的贅點)。它對相鄰重合點與重複座標要穩健(先合併重合、
   再去共線、迭代到穩定),但因為原則 2 已保證環是簡單多邊形,它不再需要、也不准用來
   判斷任何合法性。由此得到可測的**形狀守恆不變式**(見 §3 `tryClose`)。
   唯一排在原則 2 之前的檢查是「化簡後湊不齊 4 個頂點」→ `TOO_FEW`(形狀根本還沒成形,
   比自交更前置,否則三點共線的草稿會收到答非所問的 `CROSS`)。
4. **容量上限鏡射核心,且在落點當下就擋**(GEO-179)。核心 `current_geometry.c` 的上限是
   `POLY_MAX_VERTICES = 32`(`:198`),兩處各自擋:`poly_loop_is_valid`(`:229-232`)拒絕
   `count > 32`;場景 DSL 的 `parse_loop_vertices`(`:8487-8489`)讀到第 33 個 `u,v` 直接
   `return -1`,呼叫端(`:8568-8574`)報「outline 後面要接至少四個 u,v 頂點」——**同一句話
   兼管太少與太多**,核心的拒絕訊息分不出這兩者,所以前端必須自己把話講清楚。
   `polydraft.js` 以常數鏡射這個上限(不是猜的:`polydraft_test.js` 的「跨層裁判
   (GEO-179)」實跑 `core.exe` 對 32/33/34 點 outline 各驗一次,核心換上限該測試會紅),
   `place`/`applyTypedLength` 在新點會讓草稿超過 32 時回 `TOO_MANY`(共線延長不新增頂點,
   不受限),`tryClose` 比對**化簡後**的輸出長度(拿 raw 比會誤殺「32 點草稿 + 補角 =
   raw 33 → 化簡回 32」這種合法收尾)。
   > 正交簡單環的頂點數恆為偶數(邊必須橫直交錯),所以合法輸出只會是 4,6,…,32;
   > 經 `place` 畫出來的草稿(≤32 點)加補角後,raw 33 必定化簡回 32 或根本不合法——
   > `tryClose` 的 `TOO_MANY` 因此只會被「沒走 `place`」的呼叫端(或直接塞 state 的測試)
   > 觸發,屬防禦性路徑,但它是**送核心前**最後一道,不能省。
5. **座標範圍同樣鏡射核心,且在落點當下就擋**(GEO-180,對抗審查 H1)。核心
   `current_geometry.c:43` `#define COORD_LIMIT INT64_C(100000000)`(±100 km,單位 mm),
   `:44-47` `coord_in_range` **兩端都含等號**(±1e8 本身合法,超過一單位才非法);
   `poly_loop_is_valid`(`:239`)對環上**每一個頂點**的 u/v 各驗一次;場景 DSL 另有一道
   (`:12026`)報「座標或尺寸超出支援範圍(-100000000 至 100000000 mm)」。
   `place`(含首點分支)/`previewMove`/`applyTypedLength` 對落點超界回 `OUT_OF_RANGE`,
   `tryClose` 對整個 raw 環逐點驗(補角點的座標都抄自既有頂點,自己不會新超界;要擋的是
   沒走 `place` 的呼叫端塞進來的超界草稿)。邊界一樣不是背常數:`polydraft_test.js` 的
   「跨層裁判(GEO-180)」用 `core.exe` 實測 ±1e8 → ACCEPT、±(1e8+1) → REJECT。
   > **吸附在驗證之前**(§1 的既有管線順序):落在既有頂點 ±8px/`zoom` 內的超界點會先被
   > 吸附回那個合法頂點,再依**吸附後**的點判定,因此不會回 `OUT_OF_RANGE`——真正要送出去
   > 的本來就是吸附後的座標。這點有專屬測試釘住,不是漏檢。

## 1. 座標系與單位

- 所有 `pt`/`pts` 一律是 **scene 座標**(整數 mm):主畫布呼叫端傳入 `oc.*` 世界座標,
  面內呼叫端傳入面 uv 座標。`polydraft.js` 不知道兩者差異,呼叫端負責換算(主畫布用
  `oc.panX/panY/zoom`、既有 `ocToCanvas`;面內用 `fe.panX/panY/zoom`)。
- 涉及螢幕像素的閾值(±8px 對齊、12px 閉合半徑)一律由**呼叫端先換算成 scene 距離**再
  傳入(除以各自的 `zoom`),`polydraft.js` 內部只用 scene 單位比較,不吃 `zoom`/
  `panX`/`panY`。**此條僅適用於底層純函式**(`axisLock`/`snapToGrid`/`snapToVertices`,
  它們的 `thresholdScene` 參數就是已換算好的 scene 距離)。`place`/`previewMove` 這兩個
  組合函式為了讓呼叫端少算一步,改成直接吃 `vertexSnapPx`(像素常數)+`zoom`,由函式本體
  內部除以 `zoom` 得到 scene 閾值(見 §3 `place` 的③);`previewMove` 的 12px 閉合半徑
  比照辦理,同樣是**模組內建常數**(不開放呼叫端調整),用呼叫端傳入的 `zoom` 換算成
  `12/zoom` 再比較(對應 RC-POLYGON-PLAN §5.A.1.7「既有 12px 半徑不變」)——這是實作時
  發現的一處必要微調:§1 原文「不吃 zoom」只對底層純函式成立,對這兩個組合函式而言若不吃
  `zoom` 就無法算出 scene 閾值,徒增呼叫端負擔且與 §3 對 `vertexSnapPx` 的既有描述矛盾。

## 2. State 形狀

```js
{
  pts: [[x, y], ...],   // 已定頂點,scene mm 整數,含起點(index 0)
  cur: [x, y] | null,   // 目前軸鎖後的游標預覽點(未定);null = 尚未落第一點或尚未移動
  typed: "",             // 鍵入長度緩衝(數字字元字串);"" = 未在輸入
  closeReady: false,     // pts.length>=3 且 cur 落在(已換算 scene 的)12px 閉合半徑內
  error: null | { code, msg },  // 目前這一刻(cur 位置)是否會導致錯誤;不影響 pts,只影響預覽呈現
}
```

`polydraft.js` **不持有**策略參數(`gridMm`/`snapOn`/`vertexSnapPx`/`closeRadiusPx`
/`zoom`);呼叫端每次呼叫時當引數傳入(見 §3),讓主畫布/面內用同一份函式、不同參數,不必
分叉 state 形狀,也不必讓 `polydraft.js` 知道自己被誰呼叫。

## 3. 純函式

### `PolyDraft.createState()`

→ 回傳 §2 空狀態:`{ pts: [], cur: null, typed: "", closeReady: false, error: null }`。

### `PolyDraft.axisLock(pts, freePt)`

輸入:`pts`(已定頂點,至少 1 個)、`freePt`(未吸附的自由座標 `[x,y]`)。
輸出:軸鎖後的 `[x,y]`——與 `pts` 最後一點比較 `|dx|`/`|dy|`,較大者的軸取自由座標值,
較小軸鎖定為上一點的座標(與現行 `objDrawDown`/`feDown` 的軸鎖比較邏輯等價)。

### `PolyDraft.snapToGrid(pt, gridMm)`

→ `[Math.round(x / gridMm) * gridMm, Math.round(y / gridMm) * gridMm]`;
`gridMm <= 0` 時原樣回傳(視同不吸附)。

### `PolyDraft.snapToVertices(pt, pts, thresholdScene)`

輸入:候選點、已定頂點列、已換算成 scene 的像素閾值。
輸出:`{ pt: [x,y], guides: [{ axis: "x"|"y", value: number }] }`——x/y 各自獨立判斷是否
有頂點的該軸座標落在閾值內,命中則該軸吸附到該頂點座標、`guides` 加一筆;都沒命中則
`pt` 原樣回傳、`guides: []`。

### `PolyDraft.place(state, freePt, opts)`

`opts = { gridMm, snapOn, vertexSnapPx, zoom, existingEdges }`
(`existingEdges`:呼叫端已知的既有邊列表,每筆 `[[x0,y0],[x1,y0]]` 或等效表示;主畫布
是空陣列(新面沒有既有邊,只跟自己草稿已定的邊比較);面內是同一 loop 內、除了最後一段
以外的所有邊,供交叉/回頭判定用)

流程:①`axisLock` ②(若 `snapOn`)`snapToGrid` ③`snapToVertices`
(`thresholdScene = vertexSnapPx / zoom`)④用 `existingEdges` + 草稿自身已定邊判斷是否
`CROSS`/`BACKTRACK`/共線。

輸出:`{ state: newState, error: null | { code: "CROSS"|"BACKTRACK"|"TOO_MANY"|"OUT_OF_RANGE", msg } }`。

- 錯誤:`error` 非 null 時 `newState === state`(不落點),呼叫端據此讓橡皮筋轉紅、不
  push 新頂點。
- 共線往前延伸(同軸且方向與最後一段相同):`newState.pts` 的最後一個元素被新點**取代**
  (不是新增)。
- 一般落點:`newState.pts` 追加一個元素,`newState.cur = null`,`newState.typed = ""`。

### `PolyDraft.previewMove(state, freePt, opts)`

供 pointermove 用,**不落點**,只算下一幀要畫什麼。`opts` 同 `place`。

`closeReady` 判定用**未經軸鎖/吸附的原始 `freePt`**(不是預覽用的 `cur`)到 `pts[0]`
的歐氏距離,與既有 `objDrawDown`/`feDown` 現況(用滑鼠原始位置比對,不是橡皮筋預覽線的
落點)一致;半徑 = `12 / zoom`(12px 為模組內建常數,見 §1)。

輸出:
```js
{
  cur: [x, y],                 // 軸鎖+吸附後的預覽點
  guides: [{ axis, value }],   // 對齊參考線
  closeReady: boolean,
  error: null | { code, msg }, // CROSS / BACKTRACK / TOO_MANY / OUT_OF_RANGE,供橡皮筋轉紅
  cornerPreview: null | [x, y] // 見下
}
```

`cornerPreview`:若 `closeReady` 且末點與起點不同軸,回傳補直角候選點(供畫空心方塊
預覽);候選選擇邏輯同 `tryClose` 的 `computeCornerCandidates`(見下),但這裡**不做
交叉檢查**(只是預覽,真正驗證在 `tryClose`)。

### `PolyDraft.backspace(state)`

→ 移除 `pts` 最後一個元素(若只剩 1 個則清空整個 `pts`),回傳新 state
(`cur`/`typed`/`error` 一併清空)。

### `PolyDraft.typeDigit(state, ch)` / `PolyDraft.typeBackspace(state)` / `PolyDraft.clearTyped(state)`

→ 操作 `state.typed` 字串(數字字元/退格/清空),回傳新 state,不動 `pts`。

### `PolyDraft.applyTypedLength(state, opts)`

`opts = { existingEdges }`(同 `place`;方向由 `state.cur` 相對 `state.pts` 最後一點
決定,同現行 `feRedrawApplyLen` 邏輯。呼叫端要自己把 `previewMove` 回傳的 `cur` 併回
state,否則永遠是 `NO_DIRECTION`——見 `app.js::objPolyPreviewMove`)。

→ `{ state: newState, error: null | { code: "NO_DIRECTION"|"CROSS"|"BACKTRACK"|"TOO_MANY"|"OUT_OF_RANGE", msg } }`。

- `state.cur` 為 `null`(從未移動過滑鼠就按數字鍵)或 `pts` 為空 → `NO_DIRECTION`,
  `newState === state`。
- **鍵入長度產生的新段與滑鼠落點的新段走完全同一道檢查**(§0 原則 1,GEO-178):
  與草稿自身已定邊/`existingEdges` 相交 → `CROSS`;沿最後一段同軸反向 → `BACKTRACK`。
  兩者都 `newState === state`(不落點),呼叫端照 `place` 的錯誤處理顯示 toast 即可。
  > GEO-178 之前這個函式直接 `pts.concat([newPt])`、不做任何檢查,是唯一能繞過
  > `place` 全套前置檢查把自交頂點塞進草稿的管道(對抗審查 G3 的打穿點、G4 的根因)。
- 共線續走(方向與最後一段相同)→ **延長合併**:取代末頂點,不新增(與 `place` 同規則,
  維持「相鄰兩邊必互相垂直」的折線不變式)。
- `typed` 算出的長度 ≤0(新點與末點重合)→ 靜默忽略:`newState === state`、`error: null`
  (比照 `place` 的重合規則),**不得**產生零長邊。
- 一般情況:依方向把 `typed` 數值長度的新點加入 `pts`,清空 `typed`/`cur`。

### `PolyDraft.computeCornerCandidates(pts)`

輸入:`pts`(至少 3 點,`pts[0]` = 起點 F,`pts[pts.length-1]` = 末點 L)。

輸出:`{ candidates: [[x,y],[x,y]], preferred: 0 | 1 | -1 }`——
`candidates[0] = [L.x, F.y]`,`candidates[1] = [F.x, L.y]`;`preferred` 指出與最後一段
軸向交錯的那個索引(RC-POLYGON-PLAN §5.A.1.7 規則 2)。若 `L` 與 `F` 已同軸(不需要補
角),回傳 `{ candidates: [], preferred: -1 }`。

### `PolyDraft.tryClose(state, opts)`

`opts = { existingEdges }`(不含最後一段,即除頭尾外的所有邊,供補角候選的交叉檢查用;
定義同 `place` 的 `existingEdges`)。

流程(GEO-178 起是「組 raw 環 → 對 raw 環總驗證 → 才化簡」,不再是「化簡 → 判合法」):
1. `pts.length < 3` → `TOO_FEW`(防禦)。
2. 若末點 `L` 與起點 `F` 同軸(免補角):收尾段是 `L→F`,raw 環 = `pts` 本身,
   直接進步驟 4。
3. 否則用 `computeCornerCandidates` 取候選,依 `preferred` 優先順序逐一試;
   每個候選的 raw 環 = `pts + [候選]`,收尾段是 `L→C` 與 `C→F`,拿去跑步驟 4;
   **任一**判決碼(不分 `TOO_FEW`/`CROSS`/`DEGENERATE`)都代表「這個候選不可行」→
   試下一個;兩個都不可行 → `NO_CORNER`。
4. 對這個 raw 環下判決(§0 原則 2/3,順序有意義):
   1. 去共線後頂點數 `< 4` → `TOO_FEW`(形狀還沒成形,比自交更前置);
      `> 32` → `TOO_MANY`(容量問題,與形狀無關,同樣前置;§0 原則 4);
      環上任一頂點座標超出 ±100000000 → `OUT_OF_RANGE`(§0 原則 5)。
   2. 收尾段與 `existingEdges` 相交/共線重疊 → `CROSS`。
   3. **raw 環本身**不合法 → `CROSS`。規則逐條對齊
      `current_geometry.c::poly_loop_is_valid`(每邊軸平行非零長、非相鄰邊不得相交或
      共線重疊、含「首邊與末邊相鄰」的排除),外加一條相鄰邊規則:相鄰兩邊只准共享
      那一個端點,共線同側(兩段疊在一起)一律非法。收尾段的相鄰邊就是末段與首段。
   4. 去共線後 shoelace 面積 `=== 0` → `DEGENERATE`(防禦;非自交的正交簡單環面積恆不為 0)。
5. 通過 → 去共線(等同既有 `feDedupe`)後的點列就是輸出。

輸出:`{ ok: true, pts: number[][] } | { ok: false, error: { code, msg } }`。**不修改
傳入的 state**,呼叫端在 `ok: true` 後才自行決定何時真的送出核心(`objEmitFace`/
`feRedrawClose`)並清空自己持有的 state。

**形狀守恆保證**(GEO-178,`polydraft_test.js::assertShapePreserved` 對所有手寫與隨機
案例逐一驗):`ok: true` 時回傳的 `pts` 與「raw 草稿 + 閉合段」是同一個幾何——shoelace
有向面積相等、raw 每個頂點都落在輸出多邊形的邊上、輸出每個頂點都是 raw 頂點。換句話說
去共線只會拿掉「落在輸出邊上的共線贅點」,**不會**把使用者畫過的段落悄悄丟掉。
> 這條保證取代了 GEO-177 版的行為:當時 `L→C` 或 `C→F` 壓在草稿自己的邊上時,去共線
> 會把突出段整段吃掉、湊出一個核心會接受的漂亮矩形(core.exe 對 raw 點列 REJECT、對
> deduped 點列 ACCEPT),送出的不是使用者畫的形狀。現在這種候選一律判為不可行 →
> `NO_CORNER`(補角)或 `CROSS`(直接閉合)。

## 4. 錯誤碼總表

| code | 觸發時機 | 由誰回 | 建議中文訊息 |
|---|---|---|---|
| `CROSS` | 新段(滑鼠落點/鍵入長度/直接閉合的收尾段)與既有邊、草稿自身非相鄰邊相交或共線重疊 | `place`／`previewMove`／`applyTypedLength`／`tryClose` | 「這段會與既有邊交叉」 |
| `BACKTRACK` | 新點落在最後一段同軸且方向與該段相反(回頭/重疊) | `place`／`previewMove`／`applyTypedLength` | 「不能沿原邊回頭」 |
| `TOO_FEW` | 閉合時去共線後頂點數 <4(含 `pts.length < 3` 的防禦) | `tryClose` | 「外環至少要 4 個非共線頂點」(沿用面內既有 `feRedrawClose` 原文) |
| `DEGENERATE` | 閉合時 shoelace 面積為 0(防禦性路徑) | `tryClose` | 「這個形狀面積是 0,無法閉合」 |
| `NO_CORNER` | 補直角兩個候選都不可行(撞既有邊/撞草稿自身邊/與既有頂點重合/會讓化簡改掉形狀) | `tryClose` | 「末段接不回起點——兩個轉折都會撞到既有邊」 |
| `NO_DIRECTION` | 未移動過滑鼠就按數字鍵鍵入長度(`state.cur` 為 null) | `applyTypedLength` | 「先移動游標決定方向再輸入長度」 |
| `TOO_MANY` | 頂點數會超過核心上限 32(`POLY_MAX_VERTICES`,見 §0 原則 4) | `place`／`previewMove`／`applyTypedLength`／`tryClose` | 「外環最多 32 個頂點」 |
| `OUT_OF_RANGE` | 座標超出核心支援範圍 ±100000000 mm(`COORD_LIMIT`,見 §0 原則 5) | `place`／`previewMove`／`applyTypedLength`／`tryClose` | 「座標超出支援範圍(±100000000 mm)」 |

> 補角分支不會回 `TOO_FEW`/`DEGENERATE`(但**會**回 `TOO_MANY`/`OUT_OF_RANGE`——容量與座標
> 範圍問題換另一個轉折也救不了,照實回報):其餘候選不可行的理由一律收斂成 `NO_CORNER`
> (「兩個轉折都不行」才是使用者需要知道的事;GEO-177 的 G1 就是誤把候選不可行報成
> `TOO_FEW`)。`TOO_FEW`/`DEGENERATE` 只可能來自直接閉合分支。

## 5. 主畫布 P 怎麼接

- 座標:`oc.poly`(或其後繼 `oc.polyDraft.pts`)是世界 mm 座標,螢幕↔scene 換算用
  `oc.zoom`/`oc.panX`/`oc.panY`(既有 `ocToCanvas`)。
- `existingEdges`:新面沒有外部既有邊,永遠是 `[]`(`CROSS`/`BACKTRACK`/補角交叉檢查
  在主畫布情境下只會跟**同一份草稿自己已定的邊**比較)。
- `gridMm` = `oc.gridMm`(預設 250,DOM `#polyGridSize`);`snapOn` =
  `$("snapToggle").classList.contains("on")`。
- `vertexSnapPx` = 8(固定常數,不開放調整)。
- `zoom` = `oc.zoom`。
- 草稿層:`#polyDraftLayer`;鍵入長度框:`#ocLenInput`;浮標:`#canvasModeHint`
  (三段,RC-POLYGON-PLAN §5.A.1.2)。
- 送出:`tryClose` 回傳 `ok: true` 後呼叫既有 `objEmitFace(result.pts)`
  (§5.A.1.9 改寫版,bbox 落點,不再用 `centerOnNode`/homeless 自動排格)。
- Esc 階梯:主畫布專屬三段(§5.A.1.8),呼叫 `PolyDraft.clearTyped`/清空 state 兩級,
  第三級才離開工具,與面內既有七階梯無關。

## 6. 面內 e 怎麼接

- 座標:面 uv mm 座標,螢幕↔scene 換算用 `fe.zoom`/`fe.panX`/`fe.panY`。
- `existingEdges`:同一 boundary 的 `loops[0]` 目前**已定的邊**(草稿邊自己),**不含**
  孔環(重畫外環期間孔環隱藏不編,RC-POLYGON-PLAN P5 既有規則)。
- `gridMm`:既有 UIUX-FIX-PLAN B4「依 zoom 挑 10/25/50/100/250/500/1000」格距函式的
  回傳值,**不是**固定 250。
- `snapOn` = `fe.snapOn`(既有 `#faceSnapToggle`)。
- `vertexSnapPx` = 8(與主畫布相同常數)。
- `zoom` = `fe.zoom`。
- 草稿層:`#feDraftLayer`;鍵入長度框:`#feLenInput`(既有,不改 id/不改樣式)。
- 送出:`tryClose` 回傳 `ok: true` 後呼叫既有 `feRedrawClose` 的核心部分(整份重宣告
  `oc.bmap[bid].loops[0]`,`fixity` 全設 1)。
- Esc 階梯:**不變**,沿用 UIUX-FIX-PLAN「Esc 三段式決定 🔒」既有七階梯;只在其中
  「清鍵入長度」與「清草稿」兩級改呼叫 `PolyDraft.clearTyped`/清空 state,其餘五級
  (輸入框焦點、選單、對話框、參考線小選單、離開工作區)不受影響。

## 7. Node 單元測試方式

`polydraft.js` 結尾用 CommonJS/瀏覽器雙相容寫法:

```js
if (typeof module !== "undefined" && module.exports) module.exports = PolyDraft;
else window.PolyDraft = PolyDraft;
```

測試可用例如
`node -e "const PD=require('./geometry-web/polydraft.js'); console.log(PD.snapToGrid([113,240],250))"`
直接驗純函式,或寫成獨立 `.js`/`.py` 腳本呼叫並斷言,不需要 headless Chrome、不需要
bridge、不需要啟動 `serve.py`。`RC-POLYGON-PLAN.md` §5.A.1.14 的 `§P21-12` 起即為此類
模組層級測試的斷言編號。

## 8. 與現有函式的取代關係(供實作 agent 對照)

| 現行(`geometry-web/app.js`) | 被取代/改呼叫 |
|---|---|
| `objDrawDown` 內的軸鎖 + push 判斷(`app.js:3572-3598`) | 改呼叫 `PolyDraft.place`/`PolyDraft.axisLock` |
| `drawPolyPreview`(`app.js:3616-3624`) | 改讀 `PolyDraft.previewMove` 的回傳值畫 `#polyDraftLayer` |
| `objEmitFace`(`app.js:3600-3613`) | 送出前先跑 `PolyDraft.tryClose`;座標落點邏輯改依 RC-POLYGON-PLAN §5.A.1.9 |
| `feDown` 的 `fe.tool==="redraw"` 分支(`app.js:2572-2596`) | 改呼叫 `PolyDraft.place` |
| `feMove` 的 `d.kind==="redraw"` 分支(`app.js:2694-2701`) | 改呼叫 `PolyDraft.previewMove` |
| `feDedupe`(`app.js:2832-2842`) | 邏輯併入 `PolyDraft.tryClose` 內部的去共線步驟;`feDedupe` 是否保留為薄包裝或直接移除,由實作 agent 視重構範圍決定 |
| `feRedrawClose`(`app.js:2843-2854`) | 前半(驗證)改呼叫 `tryClose`;後半(送出 `emitBoundary`)不變 |
| `feRedrawApplyLen`(`app.js:2924-2938`) | 改呼叫 `PolyDraft.applyTypedLength` |

行號依目前工作區 `geometry-web/app.js`(2026-09-22,codex 未提交變更已套用的版本);若之後
行號位移,以函式名 `grep` 為準,不要死認行號。
