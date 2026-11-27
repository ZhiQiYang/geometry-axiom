# D06：吸附來源與游標標籤

工作包 F／R5 的獨立 D06 v2 片。輸入基底為 `b3c4b981bb96b118c1c05b7a1bd98062d710c8b2`。
本文件是呈現與測試契約，不改 `公理層.md`，也不新增幾何定義或引用自由度。

## 使用者看見的差別與原因

外環工具現在從當次 `feDraftSample()`／`PolyDraft.previewMove()` 的實際結果取來源。
來源端點與格點恰好同座標時，仍按來源身分分辨：PDF 命中顯示「PDF 端點」，沒有 PDF 命中的同座標才顯示「格點」。
以前 `cxResolveFace()` 只看草稿是否已有點與 `guides`，首點一律稱格點；有 guides 一律稱端點。
後者也不精確：PolyDraft 的 x、y 可分別對齊不同頂點，組合點未必是任何既有端點。
現在稱「草稿對齊」。例如已有 `(0,0)`、`(100,0)`、`(100,100)`，新點 `(3,103)` 可由第一點取 x、第三點取 y，落在從未存在的 `(0,100)`。
「端點」會把兩個獨立軸向來源誤述成單一端點；「草稿對齊」由這個來源型別直接推得。
即使某次剛好回到同一端點或起點，來源仍是相同的逐軸對齊算法；不以座標巧合另造端點身分。
這個取捨不增改吸附候選、不改優先序、門檻、取整、落點或曲線排除。

v2 另修預審找到的同類誤報：非重畫手勢不能一概用 `feSnap()` 猜最後採用點。
Alt 捏角與形狀把手先經固定選單格距，再由各自函式以 `feGridStep()` 二次取整，還有鄰邊裁限、單軸更新或 no-op。
因此 v2 只對已核明的手勢畫固定格點標記；捏角、把手與未分類手勢不畫沒有可信來源的標記，保留原來的真矩形、尺寸預覽及操作游標。
這不是取消吸附，幾何函式與事件路徑逐字不動；只撤掉前一層點冒稱最終結果的錯誤呈現。

## 來源完整表

| 真實來源／情境 | 來源欄位或函式 | 游標標籤 | 邊界 |
| --- | --- | --- | --- |
| 已校準 PDF 的原始直線端點 | `RoomOutline.nearestSnap()` 的 `target.kind === endpoint`，由 `feDraftSample()` 採用 | PDF 端點 | 不以整格座標或青色描線推定；仍保留頁碼、原線段與取整 mm 的既有詳細提示 |
| PDF 兩條有限閉合路徑線段的交點 | 同上，`target.kind === intersection` | PDF 閉合路徑交點 | 開放尺寸線交叉不因此升為候選；未增加中點、任意投影點或曲線能力 |
| 畫外環的草稿 x／y 對齊 | `PolyDraft.previewMove().guides` 非空，且當次沒有 PDF target | 草稿對齊 | 表示最後一層軸向來源，不聲稱組合點是同一既有端點；沿用關閉格點時仍會執行的原草稿對齊 |
| 畫外環的格點回退 | 當次沒有 PDF target／guides，`sample.opts.snapOn` 為真 | 格點 | 使用既有 zoom 對應格距；PDF 非整格首點後的固定軸保留／自由軸取整不變 |
| 拖邊對齊其他外環／孔環頂點的同軸座標 | `feMove()` 已決定的 `d.snapTo` | 頂點對齊 | 不新增端點候選；原本獨立於格點開關的拖邊吸附仍獨立，標籤也據實呈現 |
| 新參考線 `guideNew`、拖參考線 `guide`、矩形開口 `holeRect`、拉頂點 `vertex`、未對齊的拖邊 `edge` | 非 redraw 的 pointer 入口先用固定選單格距 `feSnap()`，再進原 `feMove()` | 格點；拖邊若已有 `d.snapTo` 改為頂點對齊 | 顯式手勢白名單，不把任意 `fe.drag` 都算作這一類。是座標預覽，不冒充 R5 已接受的合法引用式；最終原生命令與拒絕邏輯不動 |
| 參考線／矩形開口工具尚未按下的座標預示 | `feSnap()`，`fe.tool` 為 `guide/hole` 且無拖曳 | 格點 | 保留既有工具的固定格距預示；自由點不冒稱格點 |
| Alt 拖外環凸角，`d.kind === pinch` | pointer 入口 `feSnap()` → `feMove()` → `fePinchRect()` 的 `feGridStep()` → 鄰邊長與內向象限裁限 | 不畫吸附標記；保留捏角游標與真矩形寬高 | 固定格距與 zoom 格距可能不同，裁限後的角也可能不在任何格點；不能只把標記改成第二種格距 |
| 形狀預覽四邊把手，`d.kind === opHandle` | `feSnap()` → `feMove()` → `feApplyGhostDrag()` 的 `feGridStep()`；依 point/corner/edge 只改一軸、保留對側、裁限或母邊 no-op | 不畫吸附標記；保留縮放游標、原參數與矩形預覽 | 沒有可代表所有把手結果的單一二維吸附點；不以原游標另一軸補造一個點 |
| 子網格尺規新增線 | `GridEditor` 尺規 click 的 `feSnap(fePoint(e))`，取對應軸整數 mm | 既有格線／尺規呈現；無 `.cx-marks` 吸附標記 | 工具為 grid；這是獨立事件路徑，不能漏列成「無吸附」 |
| 子網格拖線 | `GridEditor` 的 pointermove：原線座標＋手勢位移 → `feSnap()` → `s.gesture.mm`／`moveLine()` | 既有 `.grid-drag-ghost`；無游標吸附標記 | 不建立 `fe.drag`，也不走 `feMove()`；保留自己的拖曳鬼影 |
| 物件主畫布拖卡片 | `ocPointerUp()` 依 `#snapToggle.on` 將 `c.nx/c.ny` 取到 20 的倍數，再寫 `canvas-pos` | 卡片本身移位；主畫布游標沒有吸附標記 | 20 是畫布座標單位，zoom=1 時對應 20 px，並非 20 mm。D12 的純顯示中繼資料仍屬 World／dump／保存；不抹成「零寫入」 |
| 其他未分類的面內 drag | 沒有經此白名單證明的單一採用點 | 不畫吸附標記 | 日後新增手勢必須先核對其真實採用來源，不可繼承固定格點猜測 |
| 未校準、沒有 PDF、影像底圖、PDF loading／manual／unavailable | 原回退分支，沒有採用 `target` | 依實際回退顯示格點／草稿對齊，或不顯示標記 | 既有座標讀數的讀取中／人工描繪原因保留；不捏造 PDF 來源 |
| 關閉格點、沒有草稿對齊的自由落點 | 當次來源為 `null` | 不顯示吸附標籤 | 整數 mm 取整本身不叫格點吸附 |
| 頁面／校準／對位、格點開關或草稿已變，而尚無新取樣 | 取樣的頁物件、basis、snapOn、草稿點陣列身分已不符 | 不顯示過期標籤 | 不在游標渲染時重選候選或把過期 PDF 改稱格點；下一次原取樣才重建 |
| 平移、Space 暫時平移、busy | 原游標狀態 | 不顯示吸附標籤 | 不把之前的描繪預覽宣稱為當前平移吸附 |

`CursorV2.snap()` 的既有一般碼 `vertex/mid/edge/grid/cross/guide` 仍分別顯示
端點／中點／邊上／格點／交點／參考線，供原呼叫端相容；這六個圖示能力不是六個新接上的吸附來源。
面內的新 `source` 只覆蓋已採用結果的文字；明確 `opts.label` 與 `label:false` 語意不變。
角材工具沿邊／沿線的命中是既有型別引用選擇，點邊／點角是選取；兩者不是本片新加的數值吸附來源。
主畫布、空間／三視圖的其他定位與投影保留原路徑；本表把已存在的 20 單位卡片吸附明列，不宣稱它已接面內游標標記。

### 兩種格距的獨立數值核對

| zoom／固定選單 | 原游標 mm | pointer 入口 `feSnap()` | `feGridStep()` | 真捏角矩形／真右把手結果 |
| --- | --- | --- | --- | --- |
| 0.1／50 | `(140,160)` | `(150,150)` | 250 | 起角 `(0,0)`、鄰邊上限 800 得 `[0,0,250,250]`；point 右把手 `[0,0,600,600]` 得 `[0,0,250,600]` |
| 0.06／100 | `(370,360)` | `(400,400)` | 500 | 相同起角與上限得 `[0,0,500,500]`；右把手得 `[0,0,500,600]` |
| 上兩列，各將鄰邊上限改為 170／190 | 同上 | 同上 | 同上 | 真捏角都裁為 `[0,0,170,190]`，其角不是上述兩種格點 |

測試用實際 `feSnap → feMove → fePinchRect/feApplyGhostDrag → feOpRect` 函式驗算。
另核兩種 zoom 下的 bottom 把手與貼母邊 no-op；呈現呼叫前後不重寫幾何。

## DOM 與資料界線

既有 `.cx-layer[data-cx-host="fe"] .cx-marks` 是唯一吸附標記位置，文字仍是帶
`data-label-halo="none"` 的 SVG text；不加操作入口、不增加隱藏模型欄位或保存欄位。
`fe.draftPreview.snapSource/snapOn/snapDraft` 只是同一次預覽的呈現記錄。
`snapDraft` 指向現有不可變草稿點陣列；鍵入長度／替換草稿後，不可把舊來源留作新操作提示。
`cxRender()` 只把來源交給 renderer；不呼叫核心、提交歷史或改寫 reference／draft。
取消、確認、復原／重做、保存與冷開的既有流程不修改。本片無須新公理，也未改 🔒 決定。

## T → P 與具名撤回

`node --test --test-reporter=spec tests/test_d06_snap_labels.js` 實際執行原檔抽出的
`feDraftSample/feDraftPreviewMove/cxResolveFace/cxRender`、原 `PolyDraft`、原 `RoomOutline` 與完整 `CursorV2`。
只替換最小 DOM 宿主；沒有測試副本的標籤表或吸附演算法。
只有 T 時，PDF 端點／交點誤標、草稿誤稱端點、假格點、過期來源、拖邊與平移等具名裁判應紅。
v2 保留原 14 個 Node test 的名字與每個斷言，另加 5 個具名 test，T＋P 共 19 個應全綠。
新增的捏角／裁限／把手／母邊 no-op／未知手勢測試在 v1 P 上也具名紅；沒有以新測試替換原裁判。
相同格點座標的 PDF／非 PDF 對照阻止以座標猜來源。
每個正例核獨立給定的座標；零寫入回歸核重複渲染前後 draft、preview、來源逐字相同。

```sh
node --test --test-reporter=spec tests/test_d06_snap_labels.js
python3 -B tests/diagnostics/d06_snap_labels_mutations.py --out /tmp/d06-withdrawals
```

撤回清單：W01 來源傳遞、W02 PDF 端點文字、W03 交點分類、W04 草稿分類、W05 自由點、
W06 過期 basis、W07 拖邊來源、W08 平移、W09 草稿替換（原九項原樣保留）；
v2 加 W10 把捏角錯列為固定格點、W11 把形狀把手錯列為固定格點、W12 對未知手勢取消來源白名單。
腳本每項保存 baseline／mutant／restored
stdout、stderr、exit，要求真正的具名 AssertionError 與 0／1／0，並精確還原原件。
這是有界 Node／VM 證據；不冒稱官方突變帳本或瀏覽器撤回。

## 真瀏覽器與 golden／成本交接

新獨立段 `P1236` 各在 390×844、1400×900 走：進面 → 底圖 → 匯入 PDF → 選第 2 頁 →
加入參考頁 → 兩點校準 2000 mm → 外環 → h 後端點偏 6／−1 px → 讀真 SVG 標籤 →
點下得 `(400,1800)` → 放棄 → 空白格點對照 → 關吸附對照 → 草稿軸對齊 → Space 平移 → 放棄。
v2 進場直接點 `.card-enter`，不先點卡片打開檢查器；原 ctl 的真 hit、16 次重試與 `throwOnFail:true` 一字不放寬。
各寬度再走正常 V → 性質分頁 → 顯示全部 → Alt 拖凸角 → 讀真矩形與「無標記」 → Esc →
點面內 → 浮動列「開口」→ 拖真右把手 → 讀原候選尺寸與「無標記」 → 取消。
每次只讀原生 dump 與歷史 entry 身分驗零寫入，不以 stack 長度單獨作證。
PDF bytes 由現有 `pdf_snap_close_fixtures.py` 的 `h-then-line` 產生，保存在 literal JSON 依賴，來源閉包可驗。
檔案選擇經真 `#refImport` 啟動，再將固定 FileList 交給既有 `#referenceFile` change handler；
這是測試檔案傳輸，**未驗 OS 選檔器**。幾何點選、表單輸入、工具與取消均用 CDP Input，未直接調用產品取樣或落點函式。
獨立 native 初始 fixture 只建立承載面，不注入 PDF、校準、預覽或來源結果。

本環境不開 Chromium，P1236 的 assertions／elapsed cost 保持工具產生的未接受候選，沒有填估值。
由雲端 Claude 在已套用 head 執行 `Canvas section measurement`（section=P1236），下載原 ZIP 後：

```sh
python3 -B tests/diagnostics/d06_snap_labels_golden.py \
  --artifact /path/to/original.zip --artifact-id OFFICIAL_ARTIFACT_ID --out /tmp/d06-golden
```

產生器委由現有 `canvas_registry.js import-cost` 核官方 run／artifact／source，從原 stdout 導入真 assertion 數與成本，
另輸出確定性 golden 投影及雜湊；舊段 fragment bytes 必須全部不變。
新 native 套件 `node:d06_snap_labels` 也由 `Native suite measurement` 取得真 census／成本後導入。
缺這些原件時正式全套守門應繼續拒絕；不得以局部 Node 綠燈取代。
接著須跑合併全集的兩片 canvas／完整 coverage、原既有 browser 組、native 六片及架構／官方突變檢查。
三份架構衍生證據、正典閱讀器及官方突變收據由既有工具／CI 重產，本補丁不手寫。

## 層級、實機核對與未驗項

這份是設計與可套用補丁，尚未開 PR，依需求帳定義不能自行記 L2。
套用後有實作 PR 才可記此修正 L2，合 main 為 L3；D06 原先已核對範圍的 L4 不撤銷，也不因本片擴張。
此標籤修正的 L4 須在實際 App 於 390／1400 各走上述匯入、校準、偏移點選、取消，
核 PDF 端點／格點／草稿對齊／自由點的字樣與座標、無錯誤 console，並另存冷開後再核相同來源字樣。
圖片、其他 PDF 閉合變體、觸控、IME、OS 選檔與本次冷開皆未在本環境實跑；不聲稱 R16 的 43 項完成或使用者 L5 驗收。
PDF 交點、拖邊頂點對齊與子網格／主畫布來源尚未加入本片真 UI 驗收；交點與拖邊已有原 Node／VM 裁判，不能把兩種證據層級混稱。

## v3：把手命中修正與重新交付

本次完整 T／P 基底為 `48d5f3887e8cb8d222307db62dbdea287fda8442`，取代中斷索引 7175906485 的 D06 補丁宣告。
舊 v3 原件無法取回，本次從可取回的 v2 原件重建，新指紋與原始輸出另列；不把舊測試數字當作本次實跑。

7174254721 的真正問題在渲染寬度，不是垂直 SVG line 的零矩形寬度：報告的 zoom
`51.666656/600=0.08611109333333333` 下，`max(10,14/z)` 輸出 162.58067872633367，
但 CSS 已是 non-scaling-stroke，單位直接是螢幕 px，會遮到其他邊。
改成 `min(14,max(10,14/z))` 只封住低 zoom 超過 14 px 的部分；高 zoom 原 10–14 px 與選單開啟 14 px 保持。
不能直接把所有情境改成 14：高 zoom 的合法窄矩形會失去原本可分辨的長邊命中。

新增兩項 Node test 執行完整的原 `drawFaceEditor`，不是複製待修表達式：七種 zoom × 選單兩態 × 四邊，
及六種高 zoom 窄矩形（核原筆寬與可區分的兩條長邊）。獨立有限線段距離按實際繪製順序判 topmost 命中，
渲染前後 op／World 必須逐字不變。v3 T 配 v2 P 為 20 pass、1 個 `D06_HANDLE_SCREEN_HIT` 紅；
v3 P 為 21 pass。W13 撤回上限命中 SCREEN_HIT；W14 一律 14 命中 HIGH_ZOOM，連原 12 項共 14 組 0／1／0。

P1236 在原 `facePoint(3600,900)` 前增加具名 SCREEN_HIT 與 computed stroke／vectorEffect／elementFromPoint 診斷，
後面的 REAL_SOURCE 另核真正 drag.side 為 right。原座標、選取器、真 CDP 事件、hit helper、時限與舊斷言均保持；
沒有把進場 obscured 當成預期紅。每尺寸新增一個 assertion；候選 fragment 仍不手填計數與成本，
由原 golden 匯入器讀正式 measurement 原件。Chromium 390／1400 及正式全套仍未在本機執行。
