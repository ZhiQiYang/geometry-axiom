# oracle 角材種類 → 核心角色

本表只服務探針場景。`place` 不改 oracle 矩形。對不上的列在文末，場景裡的暫用角色不是裁定。

條文依據是 `公理層.md`。`PROPOSAL.md` 是提案，不拿來拍板。

## 已對上

| oracle 種類 | 幾何位置 | 核心角色 | 依據 |
|---|---|---|---|
| `boundary` | 外輪廓，長度蓋住整條邊或是其延伸 | `boundary` | D15 優先級 1。I20：boundary 的固定段必須蓋住整條外輪廓 FIXED 邊，且該邊垂直主支軸。D16／I22：只有 boundary 可以有延伸段。R19(b)(e)。 |
| `main` | 室內，沿主支軸 | `primary` | D15 優先級 2。D17／I21：primary 的長度軸就是主支軸。R19(d) 端面頂層級 1 的側面。 |
| `rc_parallel` | 外輪廓上、與主支軸平行（含被兩端 boundary 裁短的邊界主支） | `primary` | I21：與主支軸平行的外輪廓邊料是 primary，不是 boundary。R19(c) 把它裁短。R18：primary 的 coversEdge 恆假。 |
| `rc_parallel` | 孔邊上、與主支軸平行，長度可能伸出孔邊 | `primary` | I21 前句：boundary／secondary 不得與主支軸平行，否則 V_PRIMARY_AXIS。孔邊上的 secondary 因此不能用。custom 沒有 I22 豁免，伸出定位邊仍是 V_EXTENSION，不能靠改角色躲過。探針維持 at-face，不縮短。 |
| `rc_parallel:custom` | 端面頂在凹角延伸段。這份 golden 有 20 支貼外輪廓；另外 4 支（F1 的四種排法各一支）與凹角牆線共線，但和該邊沒有正長度交集，整段落在另一肢 | `custom priority 3` | oracle 的種類標籤就是這個核心角色。D15：custom 必須明寫 `priority N`（N≥1），且沒有 I20、D16、I22 的專屬權利。I22：延伸段側面以優先級 2 計，主支（2）不能頂；能頂的是平行主支軸、優先級大於 2 的 custom。既有探針 p9 用 3。沒有正長度交集的那 4 支不能 at-face（R6(c) 要求與引用邊重疊），場景改 at-line，矩形不變。 |
| `secondary:mark` | 室內，垂直主支軸 | `secondary` | D15 優先級 3。D17：secondary 必須垂直主支軸，且在主支軸出現之後。R19(f)：長度是相鄰主支側面的距離。R18：secondary 的 onBoundary 必為 false（只看外輪廓）。 |
| `secondary:seam` | 室內，垂直主支軸 | `secondary` | 同上。mark 與 seam 是 oracle 的副支原因，不是另一個核心 role。 |

截面 A 取 golden 的 `w`（這份是 27）。B=33、承載面 `origin 0 0 2500` 不在 golden，沿用既有天花場景（`_demo_ceiling.scene`、s1 p9）。golden 是平面矩形，不另造高度。

孔與柱：oracle 房間只有 `holes`，沒有獨立柱物件。場景用 `surface ... hole`。不寫 `column`，也不替柱發明 z。孔邊優先級是 0（D15、I19），任何角色都可以依數值規則頂它。

## 待 Claude 裁定

### 1. 孔邊上、golden 種類仍是 `boundary` 的料

這些料垂直主支軸，貼孔邊。有的蓋住整條孔邊，有的被主支截成短段。oracle 建構註解寫「柱面料是 secondary」（`framing_oracle.py` 約 366 行），但 golden 的種類標籤仍是 `boundary`，不是 `secondary:*`。

不能用的：

- `boundary`：I20 明寫孔邊不算，boundary 只覆蓋外輪廓 FIXED 邊。短段也蓋不住整條孔邊。
- `primary`：會成為第二條主支軸，I21 拒絕（V_PRIMARY_AXIS）。

兩種還說得通的可能：

| 可能 | 依據 |
|---|---|
| `secondary` | I21：孔邊料可以是 secondary。D17：本就該垂直主支軸。R18：孔邊不算外輪廓，onBoundary 仍是 false。oracle 建構註解把柱面料稱為 secondary。 |
| `custom priority N`（N≥1，若要頂延伸段則 N>2） | D15：custom 沒有軸向義務，也沒有「必須在邊界上」的推導。I19 只拿 priority 做數值比較。沒有條文說孔邊短料必須是 secondary。 |

場景暫寫 `secondary`，`# probe-member` 的 `pending` 為 `hole-perpendicular`。這只是讓場景有一個合法的 role 欄位可以送進核心，不是裁定。因此這批探針量不到 custom 方案。

### 2. `custom` 的 priority 是否只能是 3

角色是 custom，這一點上面已對上。N 的值沒有對上：

| 可能 | 依據 |
|---|---|
| 只能寫 3 | oracle 標籤 `rc_parallel:custom` 與既有接受探針 p9 都用 3。I22 的例子是「大於 2」。沒有條文寫「必須等於 3」。 |
| 任何大於 2 的 N 都可以 | D15 只要求 N≥1。I22 要求頂延伸段的 custom 優先級大於 2（延伸段側面按 2 計）。4 或 5 一樣通過這條數值比較。 |

場景全部寫 `priority 3`，與 oracle 標籤和 p9 相同。每一支不另標 pending。N 是否唯一，仍待裁定。

## 放置順序

不是「全部邊界材，然後全部主支，然後全部副支」。延伸中的 boundary 若排在它所停靠的料之前，核心會把順序問題和幾何問題混在一起。

| 階 | 誰 | 為什麼先／後 |
|---|---|---|
| 0 | 不延伸的外輪廓 `boundary` | D15 優先級 1。別人的端面要頂它的側面（I19、R19(d)）。 |
| 1 | `primary`（`main` 與未標 custom 的 `rc_parallel`） | R19(d) 端面頂 boundary 側面。第一支 primary 定義主支軸（D17、I21）。 |
| 2 | 有延伸的外輪廓 `boundary` | R19(e)、I22：延伸端要先有被頂的料。 |
| 3 | `custom priority 3` | I22：延伸段側面按優先級 2，primary 不能頂。必須在那段 boundary 之後。 |
| 4 | `secondary`，含上面暫寫的孔邊料 | D17：副支在主支軸之後。R19(f)。 |

同一階用 golden 原序打破平手。端面若恰有一個全寬角材擋面，該擋面先放。同階兩支 `boundary` 的轉角互頂不建這條依賴（I19 允許互頂，避免環）。真的有環就強制取出階數最小的一支，場景標 `# probe-cycle`，不刪料。

## 座標怎麼寫

D7：長度不宣告，錨點是引用，不存凍結 uv。所以 `place` 裡沒有矩形，矩形在 `# probe-member`。

- 唯一貼邊（外輪廓 `eN` 或孔邊 `hIeJ`）用 `at-face`。材料側由核心依 I13 決定：外輪廓與孔在這份 JSON 都是 CCW，料落在房間內側／孔外側。深度 `+n`。長度方向跟著邊的頂點走向。
- 貼邊而且長度伸出該邊（延伸、或孔邊沿牆料伸出孔邊）仍用 `at-face`，不改成 `at-line`，也不把 `through` 縮進固定段。伸出後被 I22 拒絕，就是這支探針要留下的結果。
- 沒有貼邊用 `at-line`。寬向中線 = 矩形寬向 lo + ⌊w/2⌋。w=27 時核心足跡是 [c−13, c+14]（I13，多的 1 mm 在 +cross），還原成 [lo, lo+27]。格線只放用到的中線，嚴格遞增，不寫 `main-along`。
- 一支料同時貼到兩條邊會直接失敗，不猜第一條。
- 跨距：兩端都恰有一個全寬擋面才用 `between`（R6(d)、R21）。角材側面優先於輪廓或孔邊，因為 I19 要頂 boundary 的側面，不是外牆。擋面要在寬向上蓋住整段，點接觸不算。引用的角材必須已經放置。否則 `through`，取長度開區間內的點 lo+(hi−lo)//2。長度只有 1 mm 時沒有整數內點，`through` 退回 lo，並在場景註明。

I5：整個足跡要在有效範圍內、不跨孔。I6：端面若貼在輪廓邊上，該邊必須是 FIXED。本探針的輪廓邊沒有改成 FREE。
