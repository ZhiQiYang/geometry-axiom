# R13 N1：人工 RC 補資料與研究轉接

本版依 #43 7175773779 的 N1 封閉契約，承接已發布的 v3 原件（索引 7230545802），重新對齊 PR #468 的完整 head `366365b89528809e0a33e9cc7f7e76691e72990a`。開工 main 是 `48d5f3887e8cb8d222307db62dbdea287fda8442`；N1 必須疊在上述 E1 head，不能直接套 main。v3 仍綁舊 E1 `470062e1806954ad87f2d94d302017c65f5e25f3`，其原始輸出不冒充本次實跑。本次另附 v4 T／P 與獨立重驗。SSOT 是 D13/D14/D51a–c、I63a–c、R58a–b/D63，本片不改公理。

## 範圍與使用路徑

面內「底圖」→「來源與補資料」→「補資料紀錄」，選房間高度／RC 柱／RC 樑並新增。沿同一人工編輯器逐欄保存原文、明選單位及位置基準、確認觀察或唯一推導。RC 沒有正式採用、圖面拖拉、D07 障礙或 World 寫入；資料全域列出，沒有因入口面自建關聯。

人工來源恰為 `{kind:"manual"}`，不冒稱量測或 PDF 證據。後續 N2 活 R10 引用、N3 原子 RC 採用、N4 D07 多筆範圍／R19 同源，仍須依各片契約另作；這份交付沒有重建舊 N2 研究原件，亦不宣稱它已產品化。

## 封閉紀錄與有限關係

沿 `reconstruction-data/1`，紀錄共用 id/kind/name/revision/fields；房間的鍵與舊 bytes 政策不變。RC 另有 nullable `spaceId`，樑另有 nullable `axis`。其餘鍵、來源種類與偽造確認拒絕。

| kind | fields（順序固定） | 關係 |
|---|---|---|
| room-height | bottom, top, height, wallThickness | bottom + height = top |
| rc-column | x, y, width, depth, bottom, top, height | bottom + height = top |
| rc-beam | start, end, center, width, depth, bottom, top | bottom + depth = top |

每欄恰 raw/unit/basis/source/revision/confirmation，初值 raw 空字串、unit null、confirmation null；沒有尺寸、軸向、D5、完成面或標高預設。位置基準 unknown，距離 distance。原文字最多 64 Unicode scalar，原樣保存，確認才要求 `^[-+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$`、mm/cm、精確整數 mm、絕對值≤100000000；正尺寸須>0。允許 `+001`、`.1 cm`，拒空白、全形、尾點、指數、算式、千分位、分數及分數 mm。

x/y 須 world-x/y；底頂須 world-z；樑 start/end 沿明選水平軸、center 沿另一軸。unknown 位置可核對原觀察，不能供研究幾何。基準說明最多 256 scalar，可空，文字不建立轉換。spaceId 僅 null 或整數 1…4294967295；只記意圖，尚未核存在／身分／合法歸屬。

直接確認重驗全部原字串、單位、基準、manual source、修訂與精確值。推導只接唯一空 raw 第三欄，另兩欄須目前有效直接確認、同世界 Z、目標單位明選；結果另按確認，不接連鎖推導，不覆寫第三欄原文。三值有矛盾保留全部原文，阻擋相關研究幾何。

真改欄位或 axis/spaceId 配紀錄新修訂；受改欄位與相依推導清確認。改軸僅清 start/end/center，保留其原文與基準。spaceId 不改尺寸確認。純改名／no-op／失敗不耗修訂。原宿主歷史一次提交；undo/redo 還原內容但同 context 高水位不倒退，冷開從保存水位起始。刪資料不刪 World 或模型，原房間 review 缺失語意保留。三模板合計 256 筆、每筆 16 KiB，整附件 1 MiB；既有 64 review、每筆 64 KiB 與其他 owner 限制不變。

共用編輯器保留目前 E1 的原文修正：尺寸使用 textarea；CR／CRLF 經控制項顯示正規化時，未改的顯示仍讀回專案原文，不因保存改字或清確認。真正修改顯示才成為新原文。切換專案時保留舊 context 的未送出輸入草稿，解除舊面板的保存綁定；相同 rd-id 不得跨案回寫，切回舊 context 再顯示原草稿。這些規則同樣涵蓋柱／樑的動態欄位。

## 版本與保存

未使用 R13 的舊案不新增附件；僅房間、或使用後刪至空的附件為 /21。主案或任一方案有 RC，整案選 /22 並要求 reconstruction-data/1 與 reconstruction-rc-data/1；RC 後綴能力不進 native scene。/22 空宣告、降 /21、能力剝除、未知 /23 在發布目前專案前拒絕。完整 `.gcanvas`、方案、恢復與既有核心歷史保留附件；`.scene`/去身分 dump 不攜帶宿主資料。

`tests/fixtures/r13_n1_e1_reader.json` 是由固定 Git blob 產生的 gzip/base64 原件，仍保留其歷史 base 470062e 與全部 bytes/hash；該 reader 來源在目前 E1 head 未改。測試真的載入 E1 reader，驗 /21 正例、/22 拒絕與全部 21 個舊政策逐值相同。保留另一個 pre-E1 reader 的原 byte pin。既有精確格式／reader 能力清單追加 /22 與 RC 能力，未知負控改 /23；E1 oracle 中的「目前讀取器」兩個欄位同步遷移，沒有增加歷史例外。

## 公開研究 API

`geometry-web/reconstruction-rc-adapter.js::toGInput(records,context)` 回 `{input,provenance}`。`input` 恰含外部明選 outer/layout/params/ceiling_z 加 obstacles；context 不含預設，也不從房間 top 或樑底推完成面。這個 Node 可用的純函式不載入 App；不新增伺服路由或正式採用按鈕。

| 紀錄 | obstacle（恰 id/type/rect/bottom_z/top_z） |
|---|---|
| 柱 | `[x,y,x+width,y+depth]`，type column |
| X 樑 | `[start,center-floor(width/2),end,center+ceil(width/2)]`，type beam |
| Y 樑 | `[center-floor(width/2),start,center+ceil(width/2),end]`，type beam |

位置、端點、區間長度均受 D1；樑寬奇數多 1 mm 在正側。record id 是研究 id，provenance 另列 revision/spaceId、status=research-candidate、worldIdentity=unproven。單批≤64，不重複 id；任一明選資料未確認／不支援即整批拒絕，不篩除、不截斷、不按幾何去重。完整原資料及 context 不改寫。G 自己驗正交外環、自交與柱重疊；轉換成功、G 接受與 World 合法是三個不同判準。

## 可執行裁判、撤回與界線

`tests/oracles/r13_rc_oracle.py` 是獨立 Python/Fraction 建構器；反向區間 checker 不呼叫建構器或產品碼，驗起點、區間差、中心偏置與上下關係。完整 1 mm Cartesian：729 柱（x/y=-1…1、寬/深=1…3、底=-1…1、高=1…3），270 樑（兩軸、中線=-1…1、寬=1…5、起點=-1…1、長=1…3）。999 項逐值驗產品；每項損壞 rect 再由 checker 拒絕，另驗 bottom_z=false／top_z=true 兩個不得以 Python bool 冒充整數的錯誤輸出；這 1001 項是邏輯負控，不冒稱 OS 撤回。

四套新 Node 測試以真正資料 owner、共用 UI 與既有 VM/ZIP 宿主驗資料、歷史、格式與冷 unpack。新具名來源撤回另用實際 bytes 副本與真 Node 子程序，錯誤 reporter 只比對 AssertionError 的 message，不拿 stack 出現的標籤算 killed。原 E1 23/8/13 撤回保留；原 K1/R06 anchor 僅遷移新格式清單。

`r13_n1_g_compat.py` 要求另行取出 #205 7173437704 釘選 G 原件，實際將本產品 API 的九案輸出送 G CLI/checker：六案可行、一案低 1 mm 衝突、兩案輸入拒絕且不跑 checker。無新開孔／吊掛政策進 App。原包 bytes/hash、逐案 command/stdout/stderr 隨作者證據交付。

這份補丁沒有 N1 PR；不稱產品 L2/L3/L4。新 suites 均 pending-ci-census，P4314 未真 Chrome／未量測，P4313／P4635 亦須套用端在最終套用結果回歸。Native 全集、官方 ME/AE、Windows、實體 IME、觸控與檔案對話框待原流程驗收。現行 E1 已包含 P4313 undo/redo 等待完整操作結束的修正；本片保留其 bytes，並將同樣的 ready／busy／owner 條件加在 P4314 三處歷史等待，未增加時限。P4314 原生 select 每次鍵盤選取後重新取得可能被 render 替換的控制項；合成 DOM／原函式測試只驗此時序，仍不冒稱真 Chrome 結果。

PR #468 再變時：schema／修訂／review 會連動 N1 資料 owner 與撤回；store／feature envelope 會連動 /22、方案、高水位及舊 reader 負控；UI 原文、IME、context 或歷史修正會連動共用動態 editor、N1 UI 測試及 P4314；canvas 模組或來源閉包改變後須重新做正式量測。不能只替換基底 SHA 沿用舊結果。
