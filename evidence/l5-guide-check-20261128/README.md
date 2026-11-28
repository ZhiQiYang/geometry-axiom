# L5 導覽抽驗：9 張卡，兩種寬度

2026-11-28（台北）｜[導覽原文](../../docs/L5-acceptance.md)｜#455 留言 7229909948。這次驗的是「交給使用者這張卡，能不能照著走」，不是使用者本人接受了功能。

**原九卡抽驗的兩處不符：**卡 01 已看見 53 支，但第 5 步少了一個離開面內的動作；卡 05 可以建立、復原及重做主格，但第 3 步的表題與畫面不符。以下把操作能否走通、畫面是否相符分開記。原文未改。

## 怎麼試的

- 產品基底 `48d5f3887e8cb8d222307db62dbdea287fda8442`。Linux 本機 Python 服務＋實際編譯的原生 bridge，`runtime_version.py --probe`：`fresh: true`，版本 `b4814c2e8615c27db57cd73005e0020192a0ea64c6f2c01989f3c6bd984a1f5c`。使用者 `apiworker`，UID 1002，Node 24.22.3，Playwright 1.56.1 驅動系統 Google Chrome 157.0.8103.78（headless）。
- 每張、每寬各開新瀏覽器；卡片開始前量 `innerWidth × innerHeight`，分別為 **1400×900** 及 **390×844** CSS px。兩寬使用獨立測試服務，沒有在桌面跑完才縮圖。390 仍用滑鼠、鍵盤，不代表實體觸控。
- 點可見控制項、捲動表單、實際選檔／下載（瀏覽器 file input／下載備援）、在畫布點擊與拖曳。讀畫面文字、表格與 SVG；另以唯讀場景／房間集合讀回區別草稿與正式結果。底圖點位用現行顯示座標轉換，再用滑鼠點；這不是手眼描圖精度測試。沒有用指令寫入幾何或造候選。
- 下表的「走通」只表示此起點與此寬度。各格截圖均為**本次操作**所攝，點連結可看原尺寸。後面的輸出節錄自[走查程式](walk.cjs)及既有測試。

## 原九卡逐卡結果

| 卡／走法 | 1400 px | 390 px | 畫面與卡片比對 |
|---|---|---|---|
| [01 下角材](../../docs/L5-acceptance.md#card-01)：明選放置、板材、門檻與 RC／角材，預覽 → 取消 → 再預覽確認 | **卡在 5**；[候選](screens/01-1400-preview.jpg)・[卡住處](screens/01-1400-step5.jpg)・[補步後](screens/01-1400-pick.jpg) | **卡在 5**；[候選](screens/01-390-preview.jpg)・[卡住處](screens/01-390-step5.jpg)・[補步後](screens/01-390-pick.jpg) | 候選圖、53 列、取消提示都在；取消前後正式場景相同。確認返回面設定後，頂列不是物件畫布的頂列，不能直接切三視圖。先按「← 物件畫布」，才看得到並能點選仰視圖中的角材。390 px 的「補步後」圖停在點料，沒有展開檢查器。 |
| [03 開已存骨架](../../docs/L5-acceptance.md#card-03)：開已確認檔 → 三視圖 → 回面查看配方 → 關閉 | 走通；[點料](screens/03-1400-pick.jpg)・[配方](screens/03-1400-recipe.jpg) | 走通；[點料](screens/03-390-pick.jpg)・[配方](screens/03-390-recipe.jpg) | 三視圖有 53 個不同角材編號；點料後程式讀回「角材 N」。卡 03 第 2 步要求的是能選到角材，不要求打開結果欄。保存的是固定治具配方、左上、面 v 軸；三種來源都顯示「請明選」。只開表單再關閉沒有多一組料。 |
| [04 面材鋪排](../../docs/L5-acceptance.md#card-04)：框架＋固定外環 → 勾鋪排、填原點及來源 → 預覽、取消 → 重填、確認、重開 | 走通；[候選排板](screens/04-1400-preview.jpg)・[重開](screens/04-1400-saved.jpg) | 走通；[候選排板](screens/04-390-preview.jpg)・[重開](screens/04-390-saved.jpg) | 15 片、確認前／候選後兩欄、支撐不足可保存都看得到。取消未留下完成面；確認重開仍是原完成面和 15 片。前置交接順序要說清楚，見下。 |
| [05 建立跟隨板縫的主格](../../docs/L5-acceptance.md#card-05)：勾主格、沿 u → 取消 → 再確認 → 復原／重做 | 走到底；**第 3 步畫面不符**。[比較](screens/05-1400-preview.jpg)・[重做](screens/05-1400-redo.jpg) | 走到底；**同一差異**。[比較](screens/05-390-preview.jpg)・[重做](screens/05-390-redo.jpg) | 有「主支偏好　不存在 → 沿 u」；取消重開沒有主格，確認及重做都是來源主格 #1。但四張可讀比較表不是卡上列的四類，沒有「完成面」變更表。 |
| [06 排板移 10 mm](../../docs/L5-acceptance.md#card-06)：原點 0→10 預覽、取消；再確認、重開，暫改 3146 | 走通；[四位數列](screens/06-1400-3247.jpg) | 走通；[四位數列](screens/06-390-3247.jpg) | 主格比較列 101→111；取消回原點 0；確認後仍是 #1。在同一份 #1 的下一次預覽看到 111→3247，四位數完整單行；最後取消。 |
| [10 同底圖描兩房](../../docs/L5-acceptance.md#card-10)：開始 → 左房四角 → 客廳 → 新增房間 → 臥室 → 查看 → 復原／重做 | 走通；[第一房](screens/10-1400-first.jpg)・[第二房](screens/10-1400-second.jpg) | 走通；[第一房](screens/10-390-first.jpg)・[第二房](screens/10-390-second.jpg) | 兩房都在同來源列表。客廳 1600×1200、臥室 1400×1200 mm；「查看」能切到客廳，沒有另問比例。復原只撤第二間，重做恢復；原面 1 保留。需移開右欄或縮小才能點全四角時，不應將點不到當作缺房。 |
| [15 用長度畫 L 形](../../docs/L5-acceptance.md#card-15)：鍵入四段＋方向鍵 → 放棄 → 重畫完成 → 復原／重做 | 走通；[正式 L 形](screens/15-1400-outline.jpg) | 走通；[正式 L 形](screens/15-390-outline.jpg) | 草稿有 5 個頂點，放棄不改原矩形；確認補成寬 4000、高 3000 的六頂點 L 形。復原是矩形，重做是同一個 L。 |
| [21 超過 64 支的房間](../../docs/L5-acceptance.md#card-21)：開 110 支檔 → 雙擊面 1 → 構件／角材 → 點料單 | 走通；[支數](screens/21-1400-count.jpg)・[定位](screens/21-1400-locate.jpg) | 走通；[支數](screens/21-390-count.jpg)・[定位](screens/21-390-locate.jpg) | 範圍是承載面 1（`surface`），狀態明寫 **110 支正式角材**，確有 110 個可點料單列；點第一列選中角材 1。只驗載入與選取，不推論大量建料速度。 |
| [26 不相接互頂組](../../docs/L5-acceptance.md#card-26)：開矩形場景 → e0/e2 兩支各 27×20、+u/+n → 預覽、取消 | 走通；[拒絕](screens/26-1400-reject.jpg) | 走通；[拒絕](screens/26-390-reject.jpg) | D16a 的預期條件是中文；「確認套用」停用，**拒絕才是此卡要看的結果**。按「返回修改」離開預覽；正式角材仍是 0。 |

**卡 01／03 的窄版證據界線：**390 px 已點選、選取結果字串已讀回；原走查未展開檢查器，結果文字的可見性未驗。[走查程式](walk.cjs)預設的 `three()` 讀取 `#v3PickInfo.innerText`，不是檢查畫面可見性；兩張原 390 px 點料圖都沒有顯示右欄「選取結果」。[後續補驗](#t56)才核對展開後的畫面。

### 建議修正（不回寫導覽原文）

1. **卡 01 第 5 步**：「返回面設定 → 左上『← 物件畫布』→ 頂列『三視圖』→ 點仰視圖的一支料 → 窄版再展開頂列『檢查器』，查看『選取結果』」。[檢查器按鈕](../../geometry-web/index.html#L55)是 `#toggleRight`。
2. **卡 04 前置／第 2 步**：未勾「設定鋪排（PF-2／3）」時，鋪排原點欄尚未出現。可由套用端先填完成面名稱、框架；由操作者勾鋪排後填 u/v＝0，再選來源。若已代填原點，交接應寫「鋪排已勾，不必重勾」。門檻選單寫「鋪排承接門檻 / X（1:1）」，不是顯示 8 mm 的選項；用準備時確認過的尺寸欄位。
3. **卡 05 第 3 步**：請找「鋪排 #1 · 原生派生結果變動」、「派生宿主 #1 · 原生派生結果變動」、「來源主格 #1 · 新增」及「主格 #1」，不要要求使用者找未變更的完成面比較表。來源主格的定義與主格有效值是兩張表。
4. **卡 10 第 3 步、各卡窄版**：第一房確認後視角可能框住第一房。要描第二房時，先讓四角全在可點的底圖區域，再逐點；390 px 需要面內控制項時先展開右欄，點畫布時別讓右欄遮在圖上。卡 26 第 4 步的取消，在拒絕視窗中標作「返回修改」。
5. **[卡 35 第 5 步](../../docs/L5-acceptance.md#card-35)**：原文的「來源／影響與參數交換」不是現行區段名稱。請展開「使用關係與交換」→「預覽刪除卡片」；仍被引用時應拒絕刪除，取消返回。這是對 `227fb8c` [參數編輯器文字](../../geometry-web/parameters.js#L696-L699)的靜態核對，舊基底 `48d5f38` 也是同名；卡 35 尚未重新實跑，不計入上表。

## 起點（可直接複查）

以下四份都是這次在基底 App 用一般 UI 建立、**在該卡操作前另存、再用「檔案 → 開啟專案…」重開**的 `.gcanvas`。不是從已確認檔移除資料，也沒有手編封裝。這裡是抽驗副本，不代表導覽附錄其餘起點已備妥。

| 卡 | 進入處與已備好的內容 | 尚未做的確認 |
|---|---|---|
| [01.gcanvas](inputs/01.gcanvas) | 面 1，外環 (122,194)–(3862,3495)，放置原點 (0,0,2500)，u+x／v+y。915×1830×6 板材、8 mm 門檻及固定治具配方已各自保存；左上、板長沿 v。 | 沒有角材；本次放置、板材、門檻與 RC／角材語意仍須明選。 |
| [04.gcanvas](inputs/04.gcanvas) | 面 1，外環 (172,194)–(572,494)，100×200×6 面材與 8 mm 門檻已備。 | 沒有完成面或鋪排。開表單後另填名稱、O=(0,0,0)、U/V/N=+X/+Y/+Z、結構側 +N、鋪排原點 (0,0)、長邊 v、正排、縫 3。 |
| [05.gcanvas](inputs/05.gcanvas) | 從 04 副本用 UI 確認完成面、鋪排、高 30 mm 宿主，回到面 1。 | 尚無主格。 |
| [10.gcanvas](inputs/10.gcanvas) | 預設範例面 1，匯入 [two-rooms.pdf](../l4-cloud-20261115/d13/two-rooms.pdf)，左房上緣兩點校準 1600 mm。 | 附圖及比例在；尚無房間集合成果。進底圖頁後關吸附再描。 |

其餘用 repo 原件：[03 已確認 53 支](../l4-cloud-20261122r03a/main-7d426259/r03a.gcanvas)、[06 已有主格 #1](../l4-cloud-20261123/main-ea16e3f5/pf4a.gcanvas)、[21 已有 110 支](../l4-cloud-20261113/r04a-110.gcanvas)、[26 無角材矩形](../l4-cloud-20261123/scripts/r17-rect.scene)（用「開啟場景檔…」）；15 從新專案開始。

## 重走方法

在 repo 根目錄，用非 root 帳號開**專用、可丟棄**的服務（走查會開新專案，勿指向使用中的 App）。先建置一次，避免同時啟動時競用 build 鎖。範例用一個服務依序走兩寬；本次並行的兩個寬度分別用 18747、18749，既有測試另用 18748。

```bash
ulimit -s 16384
npm run build
GEOMETRY_FEEDBACK_DIR=/home/apiworker/tmp/t47-fb-18747 python3 geometry-web/start_local.py --port 18747
```

另一終端（`OUT` 是新證據目錄，不覆寫本次截圖）：

```bash
python3 geometry-web/runtime_version.py --probe 18747
npm install --prefix /tmp/t47 --ignore-scripts --no-audit --no-fund playwright@1.56.1
export APP_URL=http://127.0.0.1:18747/ NODE_PATH=/tmp/t47/node_modules
export OUT="$(mktemp -d)"
for size in 1400 390; do
  for card in 01 03 04 05 06 10 15 21 26; do
    node evidence/l5-guide-check-20261128/walk.cjs "$card" "$size"
    echo "卡 $card / $size px：結束碼 $?"
  done
done
```

預設讀本目錄的 `inputs/`。若要從頭備檔，依序將卡號換成 `prep01`、`prep04`、`prep05`、`prep10`、寬 1400；將輸出留在同一個新的 `OUT`，再走功能卡，即會重開新生成的副本。隨機配號不要求相同。卡 01 補步及卡 05 功能路徑都走完後，程式仍就**原卡**的不符回傳 1，不以繞過當通過。

## 卡片操作輸出（節錄）

每欄都是單獨一次 `node evidence/l5-guide-check-20261128/walk.cjs 卡號 寬度` 的結束碼；不是把 1400 的結果套到 390。實跑的環境前綴為 `NODE_PATH=/tmp/t47/node_modules APP_URL=http://127.0.0.1:18747/ OUT=/tmp/t47/final-1400`，390 則用 `18749` 與 `/tmp/t47/final-390`。右欄取 390 的關鍵輸出原文，各行以換行分隔。

| 卡 | 1400 結束碼 | 390 結束碼 | 390 輸出原文（截取；省略重複行） |
|---|---:|---:|---|
| 01 | 1 | 1 | `候選 53 支 · 確認前未寫入 53 列`<br>`本次生成已取消，配方與場景保持取消前原狀。`<br>`原步驟 5 卡住： TimeoutError: locator.click: Timeout 5500ms exceeded.`<br>`補一步：返回物件畫布，再點三視圖`<br>`角材 16` |
| 03 | 0 | 0 | `角材 16`<br>`'L4 R03A 3740×3301 固定治具 · flat-ceiling/2',`<br>`'預覽圖左上',`<br>`'面 v 軸',`<br>`'請明選',`<br>`'請明選'` |
| 04 | 0 | 0 | `勾鋪排前有鋪排原點欄？ false`<br>`比較表 [ '完成面 #1 · 新增', '鋪排 #1 · 新增' ]`<br>`重開，正式完成面 false`<br>`重開正式結果 正式來源結果 片數 15 · 裁片數 15 · 整片 3 · 厚 6 mm` |
| 05 | 1 | 1 | `主支偏好	不存在	沿 u`<br>`原生列出 3 筆變更：鋪排 #1・原生派生結果變動、派生宿主 #1・原生派生結果變動、來源主格 #1・新增。`<br>`復原後主格提示存在 false`<br>`停在 5 復原與重做、重查表單 Error: 第 3 步表題與原卡不符：沒有完成面比較表；建立與歷史已走至第 5 步。` |
| 06 | 0 | 0 | `[ '101', '111' ]`<br>`取消重開原點 0`<br>`[ '111', '3247' ]`<br>`3247 顯示行數 1` |
| 10 | 0 | 0 | `點四角前縮小次數 0`<br>`'boundary 2 outline 400,400 2000,400 2000,1600 400,1600'`<br>`點四角前縮小次數 5`<br>`'boundary 2 outline 400,400 2000,400 2000,1600 400,1600',`<br>`'boundary 3 outline 2400,400 3800,400 3800,1600 2400,1600'`<br>`查看面與比例 [ 2, 10.000000944816748 ]` |
| 15 | 0 | 0 | `外環草稿 · 5 個頂點 · 尚未套用`<br>`'boundary 1 outline 0,0 4000,0 4000,1500 1500,1500 1500,3000 0,3000'`<br>`復原 [ 'boundary 1 outline 0,0 4000,0 4000,3000 0,3000' ]` |
| 21 | 0 | 0 | `範圍 surface 承載面 1 · 110 支正式角材 · 材料／加工未設定者保持未知`<br>`畫面料單列數 110`<br>`定位 角材 1`<br>`完成 L 6438 × A 27 × B 33 mm · +u+n true` |
| 26 | 0 | 0 | `角材 1 · D16a`<br>`預期：兩個真實端面須法向相反、位於同一平面，且有正長度接觸。`<br>`實際：timber 1 [0,1000] 與 timber 2 [0,1000] 沒有恰一組相向端點同座標且寬向正長度接觸（寬向交集 0 mm）；P1-A：不互頂即整筆拒絕 確認停用 true`<br>`取消後正式角材 0` |

## 既有測試（不是卡片證據）

本次在獨立服務使用的命令（同一 shell，依序執行）：

```bash
ulimit -s 16384
export GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox
export GEOMETRY_TEST_URL=http://127.0.0.1:18748/ GEOMETRY_FEEDBACK_DIR=/home/apiworker/tmp/t47-fb-18748
export GEOMETRY_TEST_BRIDGE=/home/apiworker/tmp/geometry-runtime/9c791b72e46d5b16ec3b/bridge
GEOMETRY_FRAMING_JIG_ONLY=1 node geometry-web/cdp_test.js
GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js
GEOMETRY_BOUNDARY_PAIR_ONLY=1 node geometry-web/cdp_test.js
node tests/test_room_collection.js
```

| 範圍 | 結束碼 | 輸出原文（節錄） |
|---|---:|---|
| 固定治具 | 0 | `=== 結果:28 通過斷言 / 0 失敗斷言 / 0 略過群組 (partial) ===` |
| 面材／主格 | 0 | `=== 結果:417 通過斷言 / 0 失敗斷言 / 0 略過群組 (partial) ===` |
| 互頂 | 0 | `=== 結果:192 通過斷言 / 0 失敗斷言 / 0 略過群組 (partial) ===` |
| 房間集合 | 0 | `ℹ tests 36`、`ℹ pass 36`、`ℹ fail 0`、`ℹ skipped 0` |

首次同時啟兩個 `start_local.py` 時，18748 服務未啟動：`啟動失敗：另一個「build」正在執行`（節錄）。上述三個 CDP 命令首輪各為 1，導覽請求回 `net::ERR_CONNECTION_REFUSED`，`FATAL: UI condition timed out at connecting to isolated test browser: typeof api==='function' && typeof oc==='object' && connection.phase==='ready'`。這是進場失敗，不是產品紅燈。單獨啟動並用 `--probe 18748` 驗到 `fresh: true` 後，原命令重跑得到上表，未改測試。房間集合測試兩輪均為 0。沒有跑整個 CI、golden 或具名撤回。

**未驗：**其餘卡、其他確認前範例、R22 的復原提示、卡 01 的一般畫布可視性與表格折行缺口、Windows、實體手機觸控／輸入法、作業系統選檔視窗與一分鐘目標。卡 04 實際順序是先勾鋪排才填原點；卡 10 兩寬這次都是第一房不用縮小、第二房開描後縮小五次。不把這些準備動作當成使用者可以省略。未取得使用者的接受意見，沒有任何一項因此升為 L5。

<a id="t56"></a>

## T56 補驗：點到哪支角材，檢查器就顯示哪支

依 [PR #482 審查](https://github.com/ZhiQiYang/geometry-axiom/pull/482#issuecomment-7234834276)另跑卡 01、03。產品基底 `227fb8cd98bf30b70e180888c06ee9fc7da03637`；專用 Linux App 的 `--probe 18756` 回 `fresh: true`，Playwright 1.56.1 驅動系統 Chrome 158.0.8127.36，UID 1002。卡 01 從未生成副本起步，卡 03 重開已保存的 53 支。下表是**新截圖與新輸出**，不取代原九卡紀錄。

| 卡 | 390×844：點料 → 展開頂列「檢查器」 | 1400×900 對照：點料，不切換右欄 | 整卡結束碼（390／1400） |
|---|---|---|---|
| 01 | [補步後顯示角材 16](screens/01-390-inspector.jpg) | [右欄顯示角材 2](screens/01-1400-inspector.jpg) | **1／1**：原第 5 步切不到三視圖，須先回物件畫布。 |
| 03 | [展開後顯示角材 16](screens/03-390-inspector.jpg) | [右欄顯示角材 2](screens/03-1400-inspector.jpg) | **0／0**：點料後仍能回面查配方；窄版讀完以同一頂列按鈕收欄。 |

補驗用滑鼠點仰視圖的一支料，以點擊座標實際命中的角材編號與 `#v3PickInfo` 文字比對。390 px 點完時結果欄不可見；展開後才驗文字與編號相符、文字範圍在視窗內且中心未被遮擋，再截圖。1400 px 結果欄原已顯示。兩寬點到的料不同，不要求編號相同。

輸出原文（兩卡各自實跑，以下節錄相同的兩行）：

```text
點料命中角材 16 讀回 角材 16 展開前欄位可見 false
選取結果 角材 16 文字在視窗內且中心未遮擋 true
```

```text
點料命中角材 2 讀回 角材 2 展開前欄位可見 true
選取結果 角材 2 文字在視窗內且中心未遮擋 true
```

卡 01 兩寬仍報 `原步驟 5 卡住： TimeoutError: locator.click: Timeout 5500ms exceeded.`，補走後仍報 `停在 5 返回面設定 → 三視圖 Error: 原步驟 5 少了返回物件畫布；補步後已核對三視圖。` 卡 03 收尾各為 `走至最後一步 03 390`、`走至最後一步 03 1400`。初次補驗卡 03／390 已看到結果，但點抽屜內「關閉 ×」時 `TimeoutError: locator.click: Timeout 5500ms exceeded.`（`#fbButton` 攔到點擊），結束碼 1；改以頂列「檢查器」收欄後重跑才是表中的 0。

重走時照上方「重走方法」先開專用服務、備妥 Playwright 與新的 `OUT`。下列是本次補驗的參數；不加 `--check-inspector` 仍走原步驟。

```bash
export NODE_PATH=/tmp/t56/node_modules APP_URL=http://127.0.0.1:18756/ OUT=/tmp/t56/check
node evidence/l5-guide-check-20261128/walk.cjs 03 390 --check-inspector
node evidence/l5-guide-check-20261128/walk.cjs 01 390 --check-inspector
node evidence/l5-guide-check-20261128/walk.cjs 01 1400 --check-inspector
node evidence/l5-guide-check-20261128/walk.cjs 03 1400 --check-inspector
```

另於專用服務跑既有 CDP 固定治具（P2052：28 個通過斷言）與參數流程（P76：89 個通過斷言），兩者各為 0 失敗、0 略過群組、結束碼 0，均為部分模式。參數流程不是卡 35 的逐步實跑；以上不是使用者 L5 驗收。
