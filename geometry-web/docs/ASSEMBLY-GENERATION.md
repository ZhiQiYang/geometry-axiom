# AR06 原生角材生成與 R06 重複開間

## R06：有限重複開間（D58／I69／R55）

本節依 main `405f8c5e1a637a16cbe47470faf5ae1fa02b8676` 已採納的 D58、I69、R55 與 BACKLOG GEO-252(b)。下方 AR06 記錄是 2026-10-03 的單一開間歷史，不能代替本次 R06 驗證回執。

在既有組構工作區選一份完整材料配置，按「依來源生成角材」，將「配置方式」選為「重複開間」。規則仍是同槽位兩個 primary、一個 secondary 的固定版本；A 面接觸、A 向面內橫向、B 向 +n。加入主支及副支線，逐筆選同面參考線／主格線；主支也可選與主支平行的外輪廓邊。每支主支明選兩支支撐角材。主格線範圍捷徑只展開為有限來源列，沒有保存中的隱含展開指令。

預覽由原生依每條副支線的完整寬度帶推導相鄰開間，顯示每格結果。正面積的局部覆蓋會拒絕整筆候選；零格或全略過仍保留副支線。可在同一預覽明勾略過，重新預覽後確認。取消保留未提交草稿；共用保存保留已提交來源、映射及未完成草稿，重開前核對服務能力與完整世界。

| 契約 | 原生與交換資料 |
|---|---|
| 明列有限來源 | `source.layout="bay-repeat"`；`primaries[{key,at,ends}]`、`secondaryLines[{key,at}]`、`omit[{line,left,right}]`。兩類 key 分別在實例內唯一且為正 uint32。 |
| 定位來源 | `guide`、同面主格的 `grid-line`，及主支的 `outline-edge`；主支是 u 座標線，副支線是 v 座標線。格線 `index` 保存為精確十進位字串。 |
| 所屬身分 | `mapping[{primary,timberId}]` 或 `mapping[{secondary:{line,left,right},timberId}]`；不用顯示序號／座標／名稱配對。開間、完成長度、空間排序均不保存。 |
| 鍵比對更新 | 保留身分保留原 ID 與 World 次序；新增依主支鍵、再副支 tuple 排序追加。待刪舊 owned ID 不得在同一候選重用。外部引用先阻擋刪除，舊段移除後才正式求值。 |
| 原子驗證 | 主支先以兩支指定支撐唯一相向面的固定座標預規劃；正式 R6 解必須相同。顯式依賴與實際選定端面不得回到本實例 owned；失敗回報路徑／目標，整個候選回滾。 |
| 能力與保存 | 重複來源或未完成草稿使用 `geometry-canvas/19`，同時要求 `assembly-timber-generation/1` 與 `assembly-bay-repeat/1`。缺宣告、未知形式、懸空來源或映射不符均拒絕；重開在隔離世界重算比對，不扁平化成普通角材。情境快照內的重複來源亦受同一雙能力守門。 |
| 有限容量 | `assembly-read.state.limits` 明列 16 實例、全體 48 支 owned、World 64 支角材、每筆 canonical source＋mapping 8191 bytes；每實例最多 12 主支、24 副支線、24 個 omit。 |

反組法、巢狀、任意拓樸、相位／子格／規則子線、鋪排來源主格線（from-fill）、孔邊仍不在 D58 的能力內。這裡排除的是引用種類，不是整個衍生承載面：同面的 D6 參考線與普通有限主格仍可用於重複開間，角材照 I53 驗證 B＝h 及 +N。不存在來源、錯面／錯軸／非主格是來源驗證拒絕，不以猜測替代。一般角材編輯／刪除不能獨立改動所屬角材。

外輪廓定位以 `{"kind":"outline-edge","edge":3}` 引用一般面的邊；衍生面改存 `{"kind":"outline-edge","edgeKey":[["e3",0,1]]}` 的完整 R41 來源鍵。兩種欄位互斥；衍生面不接受數字索引，一般面不接受衍生鍵，孔鍵或不再完全相等的段號／總段數亦拒絕。草稿與完整專案原樣保存來源鍵，重開時仍由原生重新求值。

衍生宿主隨實際 R06 定義或已驗草稿保存於 `/19`，保留 I56 的 `panel-fill/1`、`engineering-spec/1`、`parameters/1` 宣告；不改舊 `/1–6` 或啟用獨立 PF 專案。H reader 在同一服務的原生隔離候選已重放、提供 canonical scene 後，另以既有 `panel-fill-read` 的 `panel-fill-native/1`／`complete:false`／恰三種 `supportedRecords` 核對有限宿主重放範圍；不將該 read 的舊 World 幾何當成候選結果，不改全域 PF 能力。這承接 [#128 已採有限保存設計 §5.0、§8](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)，未提供 PF-4／5／6 入口或語法。

W 固定模板在 `geometry-templates/woodworking/` 實作重複政策，H 只提供同候選幾何事實、交易及傳輸；K 不引用 W。新增 H adapter `geometry-web/assembly-provenance.js` 已登記 `product-architecture.json`，只核對原生完整身分與固定槽位，供材料表、支撐與來源檢視共用，不推導開間。

測試入口：`tests/test_assembly_bay_repeat.py`（真 C bridge）、`tests/test_assembly_bay_projection.js`（正式唯讀 JS 消費端）、既有 ProjectStore 測試的新 R06 保存案例，以及正式 `cdp_test.js` 的 R06 真入口流程與具名突變。實際執行結果、未能執行的環境限制及 P／T 分離補丁，以 issue #25 的 R06 交付回執為準；本文件不將未跑過的瀏覽器／平台測試寫成通過。

## AR06 單一開間歷史

使用者於 2026-10-03 核准 [有限生成契約](../../geometry-core/ASSEMBLY-GENERATION-PROPOSAL.md)。
D34/I42/R35 已採納；公理版本來源為 `cc6adff4c9c783ce78bcbd849754b69254690cab`。
本功能依賴 #52 的生成前修復；合併時先處理 #52，再處理本功能。

## 操作

1. 開啟 `examples/assembly-generation-v1.gcanvas`，或準備同面兩支邊界角材與三條定位線。
2. 在組構工作區選已發布的材料配置。首版須 A 面接觸、A 沿構件面內橫向、B 沿 +n；三構件規則含兩個向內端接。
3. 按「依來源生成角材」，明選承載面、各構件定位線，以及兩支主支各自的兩支邊界支撐（無序 R21 between；實際起末端由走向與原生幾何決定）。
4. 預覽核對 source、構件→原生角材身分、位置、方向、截面與完成長度。確認才整筆寫入；取消保留草稿。
5. 「編輯來源」保留原生角材身分。選另一份固定版本材料配置後再確認，才明確换版；發布新版不自動升級。
6. 共用「保存專案」保留實例、映射與未完成草稿；刪除實例連同三支角材一起處理，外部引用仍會阻止刪除。

來源尺寸、參數與定位線改變由原生完整候選重算。碰撞、缺支撐或不合法來源會整筆拒絕。
生成所屬角材不能透過一般 place／重宣告／刪除／尺寸綁定獨立改動。

## API 與交換

- `POST /assembly/generate-preview`：原樣轉交 `assembly-generation-transaction/1`；1 MiB 上限、完整 JSON、expectedRevision。
- 原生 `assembly-generation-preview <server-owned-path>`；操作 `create-instance`、`edit-instance`、`delete-instance`。
- 建立／更新必須帶目前 binding 來源指紋；更新／刪除另帶實例指紋。
- 原生 `assembly-read` 回傳 instances 的完整 source、穩定 mapping、來源指紋、原生 geometry／definition。
- 沿用 `assembly-confirm`／`assembly-cancel`、共用歷史與回執；確認綁定同一世界版本與候選，服務故障時不重送確認。
- `geometry-canvas/8` 必須含 `assembly-timber-generation/1`。匯入前先核對服務能力，即使只有未完成實例草稿也不省略；能力不足時不載入場景、不替換專案或草稿。沒有實例或實例草稿的既有專案仍保存原格式；/1–7 相容。
- scene 有能力宣告、`owned <instance> <member> timber|place ...` 與 assembly instance source/mapping 記錄。
  owned 僅允許完整原子場景載入；载入核對存量角材來源與映射，拒絕缺能力或壞資料，不能默默修復。
- 早期 #50 的實驗第 8 版不符合此契約，不併入本功能。
- Python orthogonal-model 執行器尚未實作生成能力，因此對含生成來源的模型包明確拒絕；原有有效模型包仍可重開。

## 驗收證據

2026-10-03 本機完整重新建置測試：1,311 項通過、0 失敗、1 項既有 Windows GDI 平台略過。
新 native 生成 suite 在 PR #53 head `618da535` 為 17 項，使用真实 C bridge；archive／transport／舊模型版本相容回歸亦通過。
独立審查追加第 18 項：交換主支的兩個支撐選擇器時，原生幾何與 owned mapping 不變；
UI 明示無序 R21 支撐，不能將保存欄位鍵當成物理起末端。副支的有序 joint 語意維持。
`tests/build_assembly_generation_example.py --check` 由全新 native 流程重建並比對完整範例 bytes。
實際 Chrome 工作區測試與完整七組 CI 的最終結果將附在 PR；尚未完成前不宣稱 G09/G10 通過。

| 契約驗收 | 實作驗證位置 |
|---|---|
| G01 三支真正角材 | native exact-three 測試；Chrome 從生成表單選來源、預覽、取消、確認 |
| G02 截面與穩定身分 | 27×33／40×50、定位改動、排序改名與 mapping 精確比對 |
| G03 拒絕、容量與原子性 | 缺／錯來源、指紋、拓撲、17 實例超容量、碰撞回滾；既有引用／幾何回歸 |
| G04 來源更新 | parameter、guide、binding 重算、世界回滾、來源预览 |
| G05 所有權與引用 | 一般入口防覆寫、自依赖／角色拒絕、外部 guide 阻止刪除 |
| G06 真交換 | 新 bridge 精確重開；來源竄改、owned 映射、缺能力、假 /8 拒絕；/1–7 回歸 |
| G07 歷史與草稿 | native undo/redo；Chrome 共用歷史、未完成草稿保存重開 |
| G08 token 與回覆 | native stale/cancel；Chrome 在真实生成確認後遺失回覆，核對鎖定與單次回執恢復；共用確認延遲／跨專案回歸 |
| G09 桌面／390px | 真 Chrome pointer/keyboard、來源讀回、溢出、44px 操作、console；實體手機未驗 |
| G10 完整回歸 | native、assembly、canvas、grid、documents、space、timber 七組 CI |

2026-10-03 的 AR06 首版有限三構件，不支援反組法、ortho-split、多跨距展開、任意嵌套或相位格線；本次有限重複開間的新增範圍見上方 R06，既有單一開間記錄不改形。
端面接觸不是固定件、工序或載重合格聲明。實體手機鍵盤／系統選檔／下載、Windows GDI 手測仍待另外驗證。
