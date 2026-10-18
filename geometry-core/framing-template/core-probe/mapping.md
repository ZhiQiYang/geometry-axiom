# oracle 角材種類 → 核心角色

本表只服務探針場景。`place` 不改 oracle 矩形。對不上的列在文末，場景裡的暫用角色不是裁定。

條文依據是 `公理層.md`。`PROPOSAL.md` 是提案，不拿來拍板。

> 依 opus 審查更正（#297）：孔邊 `rc_parallel` 的預期、待裁第 2 項、座標寫法裡的延伸段說明共三處已改，各處標「依 opus 審查更正」。
> 測試以本檔「已對上」表為角色與優先級的依據（`test_gen_scenes.py` 的 `mapping_declarations()` 直接讀這張表）；
> 改表就要同時改產生器，兩邊不一致測試會紅。
>
> golden 版本：oracle `90d20ad8`（2936 支，64 個排法）。沿革，支數是我對各版 golden 逐種類數出來的，不是引用 oracle 分支的說明：
>
> - `60785906`（2957 支）相對最初的 3093 支淨少 136 支：副支 secondary:mark 少 108、secondary:seam 少 20、孔邊上的 boundary 料少 8，是短於 `min_piece` 的極短料；10 支主支改成貼住相鄰料、座標變了；頂沿牆料的副支種類加 `:custom4`（63 支）。
> - `5610d217`（2947 支）依使用者 2026-10-18 拍板「短格記號用同一治具 367」：36 個排法有變，secondary:mark 少 26（含 `:custom4` 的 mark 少 3）、新增 16 支 `secondary:fill`（撞掉的記號旁補的那一支，不算記號），共淨少 10 支。`:custom4` 共 60 支（F1 52、F2 8）。secondary:seam、主支、沿牆料、rc_parallel、孔邊 boundary 料的支數不變。
> - `90d20ad8`（2936 支）是 oracle 對 `5610d217` 的審查修正（補位副支必須真的需要而且只補一支、縫上副支的位置要守與鄰近記號的間距上限）：2947 → 2936，F1 右上板長沿 X 少 5 支 fill，F5 右上、右下板長沿 X 各少 3 支 fill，共 11 支縫上副支的位置從 3151 挪到 3156、從 1351 挪到 1356（拿掉 11 支、新增 11 支，支數不變）。`secondary:fill` 剩 5 支（F2 3、F5 2），`:custom4` 仍是 60 支。

## 已對上

| oracle 種類 | 幾何位置 | 核心角色 | 依據 |
|---|---|---|---|
| `boundary` | 外輪廓，長度蓋住整條邊或是其延伸 | `boundary` | D15 優先級 1。I20：boundary 的固定段必須蓋住整條外輪廓 FIXED 邊，且該邊垂直主支軸。D16／I22：只有 boundary 可以有延伸段。R19(b)(e)。 |
| `main` | 室內，沿主支軸 | `primary` | D15 優先級 2。D17／I21：primary 的長度軸就是主支軸。R19(d) 端面頂層級 1 的側面。 |
| `rc_parallel` | 外輪廓上、與主支軸平行（含被兩端 boundary 裁短的邊界主支） | `primary` | I21：與主支軸平行的外輪廓邊料是 primary，不是 boundary。R19(c) 把它裁短。R18：primary 的 coversEdge 恆假。 |
| `rc_parallel` | 孔邊上、與主支軸平行，長度可能伸出孔邊 | `primary` | I21 前句：boundary／secondary 不得與主支軸平行，否則 V_PRIMARY_AXIS。孔邊上的 secondary 因此不能用。探針維持 at-face，不縮短。**依 opus 審查更正：** 原先預期長度伸出孔邊會被 I22（V_EXTENSION）拒絕，實跑 32 支全部接受。核心的延伸段只看外輪廓邊，D16 也一樣（延伸段 = 超出外輪廓 FIXED 邊端點的部分），孔邊沒有延伸段的判式。 |
| `rc_parallel:custom` | 端面頂在凹角延伸段。這份 golden 有 20 支貼外輪廓；另外 4 支（F1 的四種排法各一支）與凹角牆線共線，但和該邊沒有正長度交集，整段落在另一肢 | `custom priority 3` | oracle 的種類標籤就是這個核心角色。D15：custom 必須明寫 `priority N`（N≥1），且沒有 I20、D16、I22 的專屬權利。I22：延伸段側面以優先級 2 計，主支（2）不能頂；能頂的是平行主支軸、優先級大於 2 的 custom。既有探針 p9 用 3。沒有正長度交集的那 4 支不能 at-face（R6(c) 要求與引用邊重疊），場景改 at-line，矩形不變。 |
| `secondary:mark` | 室內，垂直主支軸，端面沒有頂到 `custom` | `secondary` | D15 優先級 3。D17：secondary 必須垂直主支軸，且在主支軸出現之後。R19(f)：長度是相鄰主支側面的距離。R18：secondary 的 onBoundary 必為 false（只看外輪廓）。 |
| `secondary:seam` | 室內，垂直主支軸，端面沒有頂到 `custom` | `secondary` | 同上。mark 與 seam 是 oracle 的副支原因，不是另一個核心 role。 |
| `secondary:fill` | 室內，垂直主支軸，端面沒有頂到 `custom`。撞掉的記號旁補的那一支（oracle `5610d217` 新增，oracle `90d20ad8` 之後剩 5 支：F2 3、F5 2；`5610d217` 時是 16 支），不算記號 | `secondary` | D15 優先級 3：它是副支，只是 oracle 用來補位的副支，與 mark、seam 一樣不是另一個核心 role（oracle README 的標籤對照表同列 secondary / 3）。其餘依據同 `secondary:mark`。現行 golden 的 5 支都沒有頂到 `custom`；若有，依下一列的規則升格。 |
| `secondary:mark:custom4` | 室內，垂直主支軸，**端面頂到 `custom`**（沿牆料 `rc_parallel:custom`，或 F1 與凹角牆線共線的併料） | `custom priority 4` | 使用者 2026-10-18 拍板（🔒，main 的 `決策佇列.md`「2026-10-18 凹角沿牆料的排序」，#301）：條文不改，沿牆料本身維持 custom 3，端面頂它的副支改宣告 custom 4。I19：擋面擁有者優先級須嚴格小於自己，3 < 4 成立（副支 3 頂 custom 3 則不成立）。D15：custom 沒有 I20、D16、I22 的專屬權利，只參與 I19 的數值比較，所以改宣告不帶來新義務。角色讀 golden 的 `:custom4` 標籤（oracle `60785906`）；產生器另依實際擋面（`timber_stops`：端面座標相接、擋面角材在寬向蓋住整段，只拿 custom 3 當擋面）獨立判定，兩者不一致就不產生場景，測試也會紅。 |
| `secondary:seam:custom4` | 室內，垂直主支軸，**端面頂到 `custom`** | `custom priority 4` | 同上。 |

升格規則對所有副支種類一視同仁：端面頂到 custom 3 的副支，不論是 mark、seam、**fill**，或孔邊上暫寫 secondary 的 `boundary` 料，都改宣告 custom 4。golden 以 `:custom4` 標籤標出（`secondary:fill:custom4`、`boundary:custom4` 這兩種現行 golden 沒有實例，所以表裡沒有列；若出現，產生器與測試照同一規則處理，以標籤為準並與實際擋面交叉核對）。`:custom4` 只能加在副支上，加在別的角色上產生器直接報錯。

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

場景暫寫 `secondary`，`# probe-member` 的 `pending` 為 `hole-perpendicular`。這只是讓場景有一個合法的 role 欄位可以送進核心，不是裁定。因此這批探針量不到 custom 方案。這批料的端面若頂到 `custom`，同樣依上面的拍板改寫 custom 4（現行 golden 沒有這種情形；golden 的種類會寫成 `boundary:custom4`）。

### 2. `custom` 的 priority 取多少（依 opus 審查更正；已於 2026-10-18 拍板，見「已對上」表最後兩列）

**拍板結果：** 沿牆料本身維持 `custom priority 3`；端面頂到它的副支改宣告 `custom priority 4`，條文不改（使用者 2026-10-18，🔒，`決策佇列.md`「凹角沿牆料的排序」，#301）。下面是這個決定的前因，保留作為理由。

角色是 custom，這一點上面已對上。場景裡沿牆料寫 `priority 3`，與 oracle 標籤和既有探針 p9 相同。

先前這一項問成「priority 是不是只能是 3」，問錯了問題。**對頂它側面的副支（優先級 3）來說，取 3、4、5 都一樣被拒**：

- 副支（secondary，核心優先級 3）的端面頂到這支 custom 的側面時，I19 要求擋面擁有者優先級嚴格小於自己。N = 3 時 3 < 3 不成立，N = 4、5 更不成立。
- 反方向也走不通：這支 custom 自己的端面要頂延伸段，I22 把延伸段側面按優先級 2 計，所以要 2 < N，即 N ≥ 3。
- 「N < 3」與「N > 2」之間沒有整數，所以整數無解。**這個結論的前提是副支必須是 secondary（優先級 3）。** 頂它側面的料若可以是優先級更大的 custom，或副支的優先級另有定義，就有解。要裁的是角色對應或條文，不是 N 取幾。

實跑（`c2d218c2`，WSL 排他，副支仍寫 secondary）看到的 I19 拒絕有 24 支，全是副支端面頂 `rc_parallel:custom` 的側面。同型的副支另有約 40 支被容量上限遮住，那是推算不是實測，見 `HANDBACK.md` 的「實跑結果摘要」。拍板後這類副支改寫 custom 4，預期這 24 支 I19 拒絕消失；要實跑才算數。現行 golden（oracle `60785906`，2957 支）標 `:custom4` 的共 63 支（F1 53、F2 10）；舊 golden（3093 支）是 64 支，少的 1 支是被去掉的極短料。

## 放置順序

不是「全部邊界材，然後全部主支，然後全部副支」。延伸中的 boundary 若排在它所停靠的料之前，核心會把順序問題和幾何問題混在一起。

| 階 | 誰 | 為什麼先／後 |
|---|---|---|
| 0 | 不延伸的外輪廓 `boundary` | D15 優先級 1。別人的端面要頂它的側面（I19、R19(d)）。 |
| 1 | `primary`（`main` 與未標 custom 的 `rc_parallel`） | R19(d) 端面頂 boundary 側面。第一支 primary 定義主支軸（D17、I21）。 |
| 2 | 有延伸的外輪廓 `boundary` | R19(e)、I22：延伸端要先有被頂的料。 |
| 3 | `custom priority 3`（沿牆料） | I22：延伸段側面按優先級 2，primary 不能頂。必須在那段 boundary 之後。 |
| 4 | `secondary`，含上面暫寫的孔邊料；以及端面頂到 custom、改宣告 `custom priority 4` 的副支 | D17：副支在主支軸之後。R19(f)。改宣告的副支仍在這一階，擋面（custom 3）已在前一階放好。 |

同一階用 golden 原序打破平手。端面若恰有一個全寬角材擋面，該擋面先放。同階兩支 `boundary` 的轉角互頂不建這條依賴（I19 允許互頂，避免環）。真的有環就強制取出階數最小的一支，場景標 `# probe-cycle`，不刪料。

## 座標怎麼寫

D7：長度不宣告，錨點是引用，不存凍結 uv。所以 `place` 裡沒有矩形，矩形在 `# probe-member`。

- 唯一貼邊（外輪廓 `eN` 或孔邊 `hIeJ`）用 `at-face`。材料側由核心依 I13 決定：外輪廓與孔在這份 JSON 都是 CCW，料落在房間內側／孔外側。深度 `+n`。長度方向跟著邊的頂點走向。
- 貼邊而且長度伸出該邊（外輪廓 boundary 的延伸、或孔邊沿牆料伸出孔邊）仍用 `at-face`，不改成 `at-line`，也不把 `through` 縮進固定段。外輪廓 boundary 的延伸段由 D16／I22 管。孔邊沿牆料原先預期被 I22 拒絕；**依 opus 審查更正：實跑 32 支全部接受**（核心的延伸段只看外輪廓邊）。
- 沒有貼邊用 `at-line`。寬向中線 = 矩形寬向 lo + ⌊w/2⌋。w=27 時核心足跡是 [c−13, c+14]（I13，多的 1 mm 在 +cross），還原成 [lo, lo+27]。格線只放用到的中線，嚴格遞增，不寫 `main-along`。
- 一支料同時貼到兩條邊會直接失敗，不猜第一條。
- 跨距：兩端都恰有一個全寬擋面才用 `between`（R6(d)、R21）。角材側面優先於輪廓或孔邊，因為 I19 要頂 boundary 的側面，不是外牆。擋面要在寬向上蓋住整段，點接觸不算。引用的角材必須已經放置。否則 `through`，取長度開區間內的點 lo+(hi−lo)//2。長度只有 1 mm 時沒有整數內點，`through` 退回 lo，並在場景註明。這份 golden 的 2957 支全部是 `between`，沒有任何 `through`。

I5：整個足跡要在有效範圍內、不跨孔。I6：端面若貼在輪廓邊上，該邊必須是 FIXED。本探針的輪廓邊沒有改成 FREE。
