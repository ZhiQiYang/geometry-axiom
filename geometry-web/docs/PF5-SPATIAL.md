# PF-5 V1：明設完成面的雙層與交界

本片對應 issue #476 工作包 V，產品基底為 main `48d5f3887e8cb8d222307db62dbdea287fda8442`。候選補丁交於 issue #128；未推送、未開 PR、未合併，不提升需求帳 R02 的 L 等級。設計推導見 [PF5-GEOMETRY-DESIGN.md](PF5-GEOMETRY-DESIGN.md)。

## 使用路徑與這片的範圍

沿既有「物件面 → 屬性 → 面設定… → 完成面／鋪排」輸入明示框架、結構側、固定面材版本、障礙集合及角材層厚來源。按原有預覽，結果區新增專案中已明設各鋪排的雙層與交界；原確認／取消列繼續承接交易。沒有新的全域入口、第二個 PF 工作區或另一個確認交易。

結果包括：

- 每個 fill 的完成面身分、框架、結構側、t、h、原生板背宿主、全部層分量／孔及完整宿主邊鍵。
- 每個明選樑／柱的世界 AABB、局部投影、沿結構方向的區間，以及面材層／角材層各自裁切、接觸或通過。
- 每對 fill 的可見共同邊、接觸維度、最小 L1 間隙及面材／角材四組包絡的交界體積與接觸維度。
- 俯視 X/Y、正視 X/Z、側視 Y/Z；每層近／遠面及連線均取 native 投影，保留孔與全部分量。三視圖是 PF 結果內的唯讀投影，沒有新增全域 WorkspaceView owner 或選取規則。

角材層是可用包絡，並非已放入的 D7 角材；它不證明支撐足夠、互不碰撞或結構安全。圖表可顯示交疊與間隙，接法仍為 `unselected`。沒有自動補側封、退讓、斜接或跨面共用角材。

## 物理量與權威

依 D41、I53、R41，`n=sN`，面材占 `[0,t]`，貼板角材可用層占 `[t,t+h]`。完成面的 `w=0` 是可見面；板背宿主是另一個身分，框架為 `(O+t·n,U,sV,n)`，座標為 `(u,sv)`。h 必須是明示來源，不能用完成面到 RC 樓板的距離補值；room／樑高也不能反推出唯一設計高度。

樑下、板下及側封各自有明示面與來源。兩層裁切沿用原生 `wood_pf_values`／`wood_pf_clip` 和既有 rebuilt host。包絡先依整個 F 求值，不能把排板 tiles 的面積相加代替它，因為板縫不等於整層可用包絡的洞。純接觸不裁，無 epsilon。

面對診斷只對上述已求得的有效區域作精確正交分解與世界座標交集，不重新求障礙裁切，也不生成新的施工規則。獨立 Python constructor／checker 不被產品 import，不共用裁切或 parser。產品測試只轉譯協定欄位，再逐值比 oracle 與獨立 checker；測例中的 section A 是顯式 oracle metadata，不冒稱 native 包絡求值器新建了 A 的產品欄位。

## 新增唯讀 wire：panel-fill-spatial/1

既有 `panel-fill-read` 回覆增加 `spatial`；既有 preview 增加 `spatial.before`／`spatial.after`。正式 `uiContract` 的既有定義、交易 revision、valid 與 completeForScope 守門繼續存在；spatial 不取代它們。

| 欄位 | 契約 |
|---|---|
| `schema`／`scope` | `panel-fill-spatial/1`／`diagnostic-envelope-only`。 |
| `complete`、`finishes`、`junctions`、`errors` | 完整性與有界診斷。每個 fill 一筆；同一完成面的多個 fill 仍保持各自身分。 |
| `finishes[].id`／`finishId`／`hostId` | id 是 fill id，finishId 是正式完成面 id，hostId 是正式派生 placement id。不可混同。 |
| `frame`／`side`／`panelVersion`／`thickness`／`h` | 來源框架、結構側、固定材料版本及有效尺寸；不從名稱、世界 Z、畫布位置或其他面猜值。 |
| `panel`／`timber` | 完整層 interval、area、components。各 component 保留 outer、holes、world near／far 及三視 projections。 |
| `host` | 原生正式宿主定義、frame、h、完整 region 與 edges。邊鍵沿原 R41，不生成近似替代鍵。 |
| `obstacles` | 僅明選 typed refs；各自 projectedRect、normalInterval、footprintRelation、panel／timber 判定、world AABB 與三視投影。 |
| `junctions[].finishes` | 依 fill id 排序的所有兩兩配對，不依名稱合併或去重。 |
| `sharedEdges`／`visibleContactDimension`／`minimumL1Gap` | 可見面幾何。dimension -1 表示分離；空有效域無距離時 gap 為 null，不能填 0。 |
| `layers` | `panel-panel`、`panel-timber`、`timber-panel`、`timber-timber`，各有 volume、contactDimension、relation。 |
| `joinPolicy` | 固定 `unselected`；不是選了某一種收邊後隱藏選項。 |

mm、mm²、mm³ 及座標使用十進位整數字串，避免 JS 讀取面積／體積時先失去精度；有界身分、軸向與維度保持 JSON number。畫面保留原字串，圖形只投影／縮放，不重算裁切或判定交界。

沒有明示 h 時面材層仍可求，角材層／宿主／相關層配對明列 pending，不以 0 或預設截面代替。診斷達容量或整數表示界線時明列 unsupported／原因及 `complete:false`，不偽裝為空區域。這些是唯讀診斷的可表示性限制，不新增合法 World 的拒絕條件。malformed wire 或來源閉包不符時 UI 顯示診斷不可呈現；正式 preview／confirm 仍沿原交易裁判，不能以「空間診斷不完整」覆蓋 I55 的既有條件。

`capacity` 明列本片診斷上限，不把它們寫成施工規格：

| 欄位／界線 | 上限與失敗行為 |
|---|---|
| `rectanglesPerLayer` | 4096；只限制面對診斷的正交分解，不截短原生層輪廓。 |
| `sharedSegmentsPerPair` | 4096；不能只保留前幾段共邊。 |
| `geometryComparisonsPerPair` | 1000000；包含可見區域、共邊交集／合併及四組層交集，不只計最後體積迴圈。 |
| `pairLoopVertices`／`pairHolesPerComponent` | 32／8，沿既有 K 區域分解器；超界整個 pair 為 `SPATIAL_REGION_CAPACITY`，保留可求出的單面完整輪廓。 |
| `volumeMax` | 9223372036854775807；每次乘法與累加先檢查，超界整個 pair 為 `SPATIAL_VOLUME_CAPACITY`，不輸出部分四層結果。 |
| D1 世界座標 | 所有近面／遠面頂點逐點驗原 D1 界線；超界整面為 `SPATIAL_COORD_CAPACITY`，不 clamp。 |

完整邊鍵先依原生 R41 求值與快取，確定成功才標完整；無法取得時整面為 `SPATIAL_EDGE_KEY_UNAVAILABLE`，不以 null 代替。若任一來源面 invalid／unsupported，相關 pair 為 `SPATIAL_SOURCE_UNAVAILABLE`，沒有假造的空共邊、分離維度或零距離。尚缺 h 的 pending 與上述來源不可用不同：仍能輸出已確定的面材及可見交界，僅缺角材相關量。

## 三面與缺側封的精確見證

這些數值是測試輸入，沒有加入產品預設。room／樑底 2500、樑頂 3000、t=9、A=27、B=h=30 的顯式測例：

| 明設完成面 | 面材層面積 mm² | 角材層面積 mm² | 原因 |
|---|---:|---:|---|
| z=2600 | 8800 | 8800 | 兩層均與明選樑有正內部交集。 |
| z=2400 | 10000 | 10000 | 兩層均在樑下，沒有交集。 |
| z=2480 | 10000 | 8800 | 只有角材層進入樑；兩層不能合成同一個厚度區間。 |

另明選高面 z=2600、低面 z=2461 與側封 x=31：側封面材／角材層面積是 13900／3900 mm²；上下共同可見邊各 100 mm；低面與側封的面材包絡交疊 8100 mm³。拿掉側封後只有兩面，最小 L1 間隙是 139 mm，不能自動產生第三面。交疊本身不替使用者選擇施工接法。

## 保存、歷史與相容性

spatial 不進 World、dump、scene 或 gcanvas，也不新增 capability 寫入標記。read 零寫入；preview 的 before／after 各自從同一原生候選重算。取消、拒絕、過期不得修改正式定義或歷史；確認仍是一筆既有交易；undo／redo 與冷載入後由定義重算。舊檔沒有 fill 時回空集合，不暗建完成面，不改版本，不保存派生快取。

本機產品裁判會核對 read 的 dump／revision 不變、取消／拒絕／過期、確認／復原／重做、原生 dump 冷重播。原生冷重播不等於 Chromium 的正式 gcanvas 冷開；後者列為套用端未驗項。

## 與工作包 A、PF-6、PF-4B 的分工

A1 的真 bbox／empty／名稱／h 使用處及 I38，A2 的一般卡片縮圖／typed 唯讀導覽／來源面相關物件／選取尺寸都不在這片。這片不改 `app.js`、`workspace-view.js`、一般 owner 或物件卡，沒有依賴 A 的未合併檔案。一般畫布、面內與宿主卡的呈現列未驗，不因 PF 結果內可畫就宣稱已完成 A。

PF-6 App #469 與這片的 `panel_fill_bridge.inc`、`panel-fill-adapter.js`、`panel-fill-workspace.js`、`index.html`、BACKLOG 有檔案交集；若先合，須以其採用 head 合流 supportedActions 與結果區，保留 builder 的候選 owner／確認路徑，再重跑兩片測試。V 不取 PF-6 的未合併能力作前置。PF-4B 快照 operation、來源凍結與相關測試不納入。

## 六檔來源及沿用判定

來源分支 `openaiworker/45816012843`；歷史提交 `291ee64e90dd566c6a3c005ed72ac0e71f10f9dc`。worker 報告記載沒有建立獨立純 PF5 保存分支，另產生 tree `df609d8b54c8fc189313685c1809827f0c832c7c`。可用 `git show <commit>:<path>` 取回，不把 tree 當 branch。

| 檔案 | 原 blob | 本片處理 |
|---|---|---|
| `geometry-web/docs/PF5-GEOMETRY-DESIGN.md` | `751fc4d388cc869eb5db05b8ec3db7db32b53d5f` | 更新產品切片及正確的實際 HEAD 重現方式。 |
| `tests/pf5_geometry_check.py` | `4413b0c7d974e6eac4542a6d7963cafceadf2b90` | 原 bytes 沿用。 |
| `tests/pf5_geometry_mutations.py` | `7d45d299b73b6338b3d460e8c38a5cefa3107019` | 有界執行與指定 test／具名 AssertionError 判定；一般錯誤不算 kill。 |
| `tests/pf5_geometry_oracle.py` | `8291329895ad1341050dcbbdbfd2d52911ccca73` | 原 bytes 沿用。 |
| `tests/suites.d/py__test_pf5_geometry_oracle.json` | `86c01413d6b7f054353947bcffb88c0486890185` | 原 bytes 沿用，仍為 pending CI census／cost。 |
| `tests/test_pf5_geometry_oracle.py` | `bb8b726d408fbfb4767d70e7400eb2f55dbda776` | 原 bytes 沿用，另加產品 suite。 |

## 驗收分工與未驗項

T／P 分離，T 包含完整原 oracle 工具，正常編譯及建場後產品測試才紅在具名 `PF5_SPATIAL_ENTRY`。P 後逐值對兩層、全部分量／孔、明選障礙、宿主及面對關係；來源撤回須原檔／突變／恢復三次取得 `0/1/0`，只認指定測試的指定斷言。診斷腳本自己的 timeout／錯誤分類另有反例。

新 suite 使用原 native `--init-suite`；新 canvas `P1285` 使用原 `stage-module`，正式計數／成本不手填。套用端需跑真 Chromium 的 1400×900 與 390×844，量測並用原 import 工具採入，之後跑完整兩片；正式原生六片、架構收據、其他既有守門照常要求。此文件不是量測收據，最新本機命令、結束碼與未驗項以 issue #128 最終交付索引為準。

### P1285 的兩個 viewport 預期

同一獨立段在 1400×900 與 390×844 各跑完整路徑。先正式 reload 等新 document ready，避免承繼舊段的單視圖／關閉圖層；建場只取 `newid` 的正式識別，受測輸入、預覽、取消、確認與導覽均由 CDP 真控制進入。T 的第一個產品紅點是進場成功後的 `PF5_BROWSER_NATIVE_SPATIAL_PRESENT <width>`。

| 情境 | 1400 與 390 都必須滿足的結果 |
|---|---|
| 新完成面 | frame／結構側及 h 尚未輸入時為空，不出現沒有來源的規格預設。 |
| z=2480／2491／2461／2600 | 面材／角材層面積分別 10000／8800、10000／8800、10000／10000、8800／8800；2491 的面材及 2461 的角材僅接觸樑，不裁。 |
| 明設高面／低面／側封 | 面積逐面為 3100／3100、3800／3800、13900／3900；低面與側封共邊 100、面材交疊 8100、gap 0，所有接法 `unselected`。 |
| 交易 | preview／cancel 的 dump、revision、project、history 不變；confirm 恰一筆既有歷史。 |
| PF 結果內三視圖 | 每張圖的所有 native path（全部分量／孔、近／遠面）逐值相符；寬與高各至少 180 px、整圖在裁切可見範圍內（量測容差 1 px）、中心可命中、文件不橫向溢位（容差 1 px）。記錄完整 `P1285_LAYOUT` 實測數字，不能只報成功。 |
| 既有全域三視圖 | 真入口顯示 front／side／bottom；全部 host polygon 的點多重集合逐圈相同，包含孔與重疊投影。step 樑 bounds 依序 `[40,-3000,60,-2500]`、`[0,-3000,100,-2500]`、`[40,0,60,100]`，畫布可命中。 |

不另寫 golden 產生器：沿現有 `Canvas section measurement` 與 `canvas_registry.js import-cost`，由真全綠 journal 產生本段精確計數／成本／來源 pin。候選 0／null 不是正式 golden；沒有手填例外或更動舊段 pin。新 native 四套件同樣經原 `Native suite measurement`／`native_registry.py --import-suite` 取得真計數／成本。詳細指令遵循 `tests/FRAGMENTED-REGISTRIES.md`，交付索引列出本片的確切名稱與套用步驟。

本環境不實跑 Chromium。三視圖在真 DOM 的可見性、hit target、手機捲動與正式 gcanvas 冷開仍待雲端實跑；不冒稱 L4。一般 A 呈現、空間直接選面、自動接法、骨架生成與結構安全不屬 V1 已驗範圍。
