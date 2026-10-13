# K1 — #47 F4b 一維裁切／餘料 + 料單去重：可實作契約提案（r1）

- 狀態：**r1，暫定（依 2026-10-09 授權 L）**。opus 對抗審查判定「須先改、無阻擋」，本版依主迴圈裁決修訂。
  審查要點照錄於 `review-findings.md`；r1 再審通過前，不寫 SSOT、不開工。
- 基底：`a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e`（`公理層.md` 與 main `5cc1ffa` 完全相同）。
- 配套文件：`AXIOM-DIFF.md`（逐條條文，條號用佔位符）、`decisions-provisional.md`（岔路與採用）。
- 新能力名 `cutting-plan/1`。專案格式號用佔位符 `geometry-canvas/⟨K1-F⟩`，因為另有 4 份提案可能同時占號。

## r1 變更摘要（對應審查 1–8 項與「僅記錄」項）

| 審查 | 本版修在哪 |
|---|---|
| 1 工程專案不能用 | 採 P14-B，首版併入 native 唯讀的具型別末端欄位（§3、§6、§9），並以 `engineering-spec-v1` 為夾具（E1／E2、N1–N5） |
| 2 原材種類溯及改變餘料 | 被餘料引用的原材種類鎖定截面與材料鍵，回 `STOCK_TYPE_IN_USE`（§4.1、T12b） |
| 3 材料鍵缺指紋 | 材料鍵改為 (id, version, fingerprint)，三者皆等才算相同（§4.1、§5、T26） |
| 4 容量矛盾 | §4.4 單一容量表，逐項寫明拒絕層；餘料上限改 128；T18 改寫 |
| 5 records 上限寫錯 | 以實際基底 a7bff8f 為準：4→5（main 為 3 種；寫入時以實際基底 +1）|
| 6 CSV 列序與負可用長度 | §4.5 定固定列序；無剩料時欄位留空；可用長度 = max(0, 剩料 − t)（T4、T25） |
| 7 derive 拋錯無對應狀態 | 範圍改用讀取到的已放置角材清單預檢，得 `SCOPE_STALE`；其餘 derive 失敗改由具型別失敗碼對應 INCOMPLETE（§5、§6） |
| 8 OVER_LENGTH 判準與求值順序 | 判準改為 `C > max(S−2e, max U)`；新增 `REMNANT_EXHAUSTED`；明定 0–5 階段的求值順序（§5、T23、T28） |
| 僅記錄 | T3b 改為「期望值紅」；`MATERIAL_MIXED` 改歸 INCOMPLETE；T7 改為 API 層拒絕；新增截面與指紋不符的診斷碼；Δ7 改用明確錨點；Δ2 補 I34／I36 一句 |

---

## 1. 問題

F4a 已交付「完成尺寸料單」：每支正式已放置角材的原生 A/B/L、來源、雙向定位與 CSV（PR56／65／70／96）。
現場備料卻還缺三段換算（#47 原文）：**模型完成尺寸 → 加工毛料／裁切尺寸 → 購入原材尺寸**。
現有料單答不出：要買幾支料、每支怎麼下刀、會剩多少、手上的餘料能不能先用。

#47 留下三個待決差異：鋸縫精度、末刀與既有端面是否計刀、首版保存範圍。
「跨表示實物計量／去重」也仍未解決。Q32 已定 durable incarnation ledger 屬於另一個大契約，未採納
（`CONTINUATION-DECISIONS-20261003.md:48`、`IMPLEMENTATION-QUEUE-20261004.md:11`）。

## 2. 物理機制（先模擬，再定規則）

1. **鋸切會吃掉材料**。鋸片有厚度，每下一刀就有一條鋸路的材料變成木屑。
   這只在「實際下刀」時發生，和切出幾件無關。
2. **誤差累到最後一段**。師傅每件都從新鋸面往下量，所以誤差一路累積到末段。
   低估鋸路的後果是末件太短而報廢（硬失效）；高估只是剩料少一點（軟失效）。
   因此鋸縫要宣告成「不小於實際值的整數」。
3. **末刀**。末件之後還有料，就必須再下一刀分開，這一刀也吃鋸縫。
   末件剛好用到原端面或修整線時，不必再下刀分離。計刀規則因此是「有下刀才算」，這是定義推論。
4. **原廠端面**。原廠端面可能不方正或有裂，使用者可以宣告每個原廠端要切掉多少（含該刀）。
   剩料的一端是新鋸面，另一端仍是原廠端。
5. **截面**。橫切不會改變截面，所以比對不分 A、B 順序。
   不同材料不可混用；「材料未設定」的件是否同材，系統無法知道，只能由使用者宣告。
6. **太長的件**。比所有可用料都長的件只能接料，屬 §四「料長續接」，因此拒絕，不縮短模型，也不假裝料比較長。
7. **一件實物只算一次**。同一次世界讀取中，一支 typed 角材就是一件實物。
   跨表示之間沒有可證明的對應：合併可能多算，錯誤去重可能少算，所以不合併、直接拒絕。
8. **被引用的原材種類不能改形狀**。宣告餘料是手上那段真實的料。
   它的截面與材料是實物事實，改原材種類的定義不會改變那段料。
   若允許溯及修改，27×33 的料會被當成 30×40 拿去配，是硬失效（審查 2）。

領域事實查證（`flat-nailed-ceiling`）：

- skill 記載料長「8 尺約 2440、12 尺約 3636」，但 8 台尺換算是 2424，兩者不一致。
- 主骨能整支就整支，超過料長才搭接；末格現裁用來吸收累積誤差；刀誤差 ±0.5mm，裁切往安全側偏。
- **skill 沒有記載鋸路寬度與原廠端修整慣例**，所以本提案不設任何預設值。
- 測試只借 3636 當夾具。E2 的 4200 是純夾具值，不代表市售料長。

## 3. 首版範圍（兩個循序 PR）

**一句話**：需求是**現行 World** 內一或多個明選範圍（承載面全部或明選角材，可以跨面），以 **typed timber id 聯集去重**。
依專案保存的原材種類、宣告餘料、鋸縫、原廠端修整、加工餘量、留用下限，用**確定性 FFD** 算出每支原材的下刀、剩料與購料支數，並匯出 CSV。
材料歸屬讀**核心求出的具型別末端來源**，所以面套用（application）的工程專案也能用。

| PR | 內容 | 依賴 |
|---|---|---|
| **K1-a（native，唯讀、只增欄位）** | `references` 的 `engineeringSources[]` 每筆、`assembly.bindings[].effective[].A/B` 每筆，各加一個 `terminal` 欄位（§6.1）。由 `eng_resolve` 走完 D28 鏈時順手記下末端；不新增路由、不改既有欄位值、不改 World。 | — |
| **K1-b（前端）** | `cutting-plan.js` 純求值器；`timber-schedule.js` 拋錯加具型別 `code`（訊息與行為不變）；`cutting-settings` 附件；料單面板入口；對話框；匯出守門。 | K1-a |

**不含**（見 §10）：加工確認與庫存異動、採購、接料、以保存模型快照為計量世界、同一組多種料長、逐件餘量、最佳化保證、二維排板、D36 斷面構件。

## 4. 資料模型

### 4.1 保存：`featureAttachments.records[]` 新種類

```json
{
  "kind": "cutting-settings",
  "schema": "cutting-settings/1",
  "value": {
    "kerf": 3,
    "allowance": 0,
    "minRemnant": 300,
    "stockTypes": [
      {"key": 1, "name": "角材 27×33 試用料", "section": [27, 33],
       "material": {"id": "example-timber-27x33", "version": 1,
                    "fingerprint": "f58363d2c040ecdaeaf38e314bb20357f251ba7d955ecb23262f3d7bc4f6db66"},
       "length": 3636, "endTrim": 5}
    ],
    "remnants": [{"key": 1, "stockType": 1, "length": 1859, "headTrim": 0, "tailTrim": 5}],
    "nextStockKey": 2,
    "nextRemnantKey": 2
  }
}
```

- `kerf`、`allowance`、`minRemnant` 可以是 `null`（未設定）。原材種類與餘料的每個欄位都必填。
- `material` 是 `null`（材料未設定），或 `{id, version, fingerprint}`；fingerprint 為 64 個小寫 hex，比對時三者皆須相等。
- **鎖定**：原材種類只要被任一餘料引用，`section` 與 `material` 就不能修改，否則回 `STOCK_TYPE_IN_USE`，要改就新建一種。
  `name`、`length`、`endTrim` 可以改，因為餘料自帶 R、h、t，不會被溯及。
- key 為非零 uint32。兩份清單各自一個高水位，只增不減；值為 `0` 表示耗盡。

### 4.2 不保存：需求請求（session）

`{world: {kind: "live"}, scopes: [{surface, ids: null | uint32[]}]}`。
切換專案 context 就清空，比照 `fe.scheduleView`。
求方案時，所有範圍都由**同一次** `references` 讀取求值。

### 4.3 不保存：方案（衍生）

```text
Plan {status, diagnostics[{status, code, detail}], worldFingerprint, settingsFingerprint, label:"本次找到的方案",
  groups:[{stockTypeKey, newStockCount, stocks:[{label, length, headTrim, tailTrim,
     pieces:[{seq, timberId, surface, L, allowance, C, start, end}],
     tail:{kind:"trim"|"none"|"separate", consumed, cuts},
     leftover:null | {length, usable, class:"reusable"|"waste"}}],
   unusedRemnants:[key...], kerfLoss, trimLoss}]}
```

`usable = max(0, length − tailTrim)`；`length = 0` 時 `leftover = null`。

### 4.4 容量（**唯一定義處**；公理只寫「由執行器宣告」與拒絕層）

| 項目 | 上限 | 拒絕層 | 回應 | 依據 |
|---|---|---|---|---|
| 原材種類數 | 32 | 設定保存驗證（I⟨K1-1⟩） | 拒絕該次編輯，設定與歷史不變 | 工程值 |
| 宣告餘料數 | **128** | 設定保存驗證（I⟨K1-1⟩） | 同上 | 對齊既有 `boundedJSON` 非房間附件的陣列上限 128（`feature-attachments.js:96`，main） |
| 名稱 | 96 bytes | 設定保存驗證 | 同上 | 同 D29 名稱上限 |
| 附件整體 | 128 KiB、4096 個節點 | 既有 `boundedJSON` | 同上 | 32 種原材加 128 段餘料約 1,200 個節點，在範圍內 |
| 需求範圍數 | 64 | 求方案（R⟨K1-1⟩ 第 0 步） | `UNSUPPORTED/CAPACITY` | 工程值 |
| 需求件數 | 4096 | 求方案（R⟨K1-1⟩ 第 2 步） | `UNSUPPORTED/CAPACITY`，不截斷 | 工程值 |

### 4.5 CSV（列序固定，和畫面排序無關）

- 列序：原材種類 key 遞增 → 該種類被使用的料，依 R⟨K1-2⟩(2) 的候選順序（餘料按 U 遞增、再按 key 遞增，然後是新料，依開啟順序）→ 每支料內依件序列出 `piece` 列，最後接一列 `end`。
- 未使用的餘料不列在 CSV，只在畫面的彙總中顯示。
- 欄位：`row_kind(piece|end), plan_status, plan_label, world_fingerprint, settings_fingerprint, stock_type_key, stock_type_name, section_mm, material_id, material_version, material_fingerprint, stock_label, stock_length_mm, head_trim_mm, tail_trim_mm, kerf_mm, seq, timber_id, surface_id, finished_length_mm, allowance_mm, cut_length_mm, start_mm, end_mm, tail_kind, tail_consumed_mm, cuts, leftover_mm, leftover_usable_mm, leftover_class`。
- `piece` 列中只屬於 `end` 列的欄位留空；`end` 列中只屬於件的欄位留空。
- **無剩料時，`leftover_*` 三欄留空**，不填 0 或負數；材料未設定時，三個 `material_*` 欄留空。
- 格式沿用 `TimberSchedule.csvCell`：引號、公式字串前綴、BOM、CRLF。數值一律以 mm 匯出。

## 5. 求值順序與規則（對應 R⟨K1-1⟩–R⟨K1-3⟩）

| 步 | 內容 | 失敗時 | 是否繼續 |
|---|---|---|---|
| 0 | 請求：沒有任何範圍 → EMPTY；（請求格式只帶一個計量世界，跨世界無法表達，不設分支）世界種類非 live → `UNSUPPORTED/WORLD_KIND`；範圍數超限 → CAPACITY | 依左 | 停 |
| 1 | 對計量世界做一次 `references` 讀取並取定指紋；讀取不 ok 時 → `INCOMPLETE/WORLD_UNREADABLE`。用其 `timbers[]`（只含已放置）**自行**核對每個明選 id 存在、且 `geometry.surface` 等於該範圍的面 → 否則 `INVALID/SCOPE_STALE` | 依左 | 停 |
| 2 | 逐範圍呼叫 `derive`；失敗以 `error.code` 對應 `INCOMPLETE/ROW_NOT_READY:<code>`（不比對錯誤文字）。以 timber id 聯集；件數超限 → CAPACITY（停）；範圍沒有任何件且 derive 未拋錯 → `INCOMPLETE/SCOPE_EMPTY`（derive 拋錯的範圍只報 ROW_NOT_READY，不同時報 SCOPE_EMPTY）。材料鍵：回覆缺 `terminal` 欄位 → `UNSUPPORTED/NATIVE_CAPABILITY`；`terminal` 為 null → `INCOMPLETE/MATERIAL_UNRESOLVED`；A、B 末端不一致 → `INCOMPLETE/MATERIAL_MIXED`。配料依序判斷 `MATERIAL_FINGERPRINT_MISMATCH` → `STOCK_SECTION_MISMATCH` → `NO_STOCK`（皆為 INCOMPLETE） | 收集 | 逐件評估 |
| 3 | OVER_LENGTH（不需 k、r_min）：`C > max(S − 2e, 該種類各餘料 U)` → INVALID；a 未設定時以 L 判斷 | 收集 | 逐件評估 |
| 4 | k、a、r_min 有任一未設定 → `INCOMPLETE/MISSING_SETTING` | 收集 | — |
| 5 | 第 2–4 步都沒有診斷時才排料：FFD；新料放不下而餘料已被占用時 → `INCOMPLETE/REMNANT_EXHAUSTED`；收尾並做守恆自檢 | 依左 | — |

- 整體狀態取最嚴重者：INVALID > UNSUPPORTED > INCOMPLETE；逐件診斷全部保留。只有 COMPLETE 可以匯出。
- **材料鍵**：A、B 各取原生 `terminal`；該軸沒有工程來源時，視為非材料末端。
  - 兩軸末端都不是材料 → 材料鍵為「未設定」。
  - 兩軸是同一個 (id, version, fingerprint) → 材料鍵為該版本。
  - 其他情況 → `MATERIAL_MIXED`。
  - 前端不重做 D28 查找，也不解析 `path`。
- **排料**：
  - 件序：C 遞減，同長依 id 遞增。
  - 候選料：先用餘料（U 遞增，同長依 key 遞增），再用已開啟的新料。
  - 起點：料上還沒有件時 x = h，否則 x = 前件終點 + k。`x + C ≤ 長度 − t` 就放入。
  - 沒有料放得下時開一支新料（h = t = e）。
- **收尾**：設末件終點為 y。
  - `y = 長度 − t`：做修整（t = 0 則不下刀）。
  - 否則下末刀，耗損 `min(k, 長度 − y)`，剩料 = `長度 − y − 耗損`，可用長度 = `max(0, 剩料 − t)`。
  - 剩料 > 0 且可用長度 ≥ r_min 才可留用；剩料 > 0 但不足留用是廢料；剩料 = 0 為無剩料。

## 6. 介面

### 6.1 K1-a 原生欄位（唯讀、只增欄位）

- `engineeringSources[]` 每筆、`assembly.bindings[].effective[].A/B` 每個非 null 物件，各加 `"terminal"`：
  - `{"kind":"material","id":"…","version":N,"fingerprint":"<64hex>"}`
  - 或 `{"kind":"literal"}`、`{"kind":"spec"}`、`{"kind":"parameter"}`
  - 有效值無法求值時為 `null`。
- 實作方式：把 `eng_resolve` 改名為帶可選 `EngTerminal *` 輸出參數的內部函式，原 `eng_resolve` 保留為傳 NULL 的薄包裝。
  - 葉節點（literal、spec、parameter、material）寫入 terminal；material 的 fingerprint 取自 `EngMaterialVersion.fingerprint`。
  - application 分支遞迴到 nested 時自然帶回末端（含面覆寫）。
  - `eng_effective` 同樣加一個帶 terminal 的變體。只有兩個 serializer 會傳非 NULL。
- 既有呼叫者（`assembly.inc`、`assembly_generation.inc`、`section_profile_validation.inc`、交易求值）一律不改。
- `json_engineering_sources` 同時供 `references`、`engineering` 讀取與工程預覽的 before／after 使用（`engineering_bridge.inc:50`），三處都會帶出新欄位，影響範圍都是只增欄位。
- 回覆中既有欄位的值與順序都不變。新欄位排在各物件的最後；`sourceFingerprint`（`eng_definition_hash` 只雜湊 World dump）不受影響。

### 6.2 前端介面

| 既有 | K1 如何使用 | 不變的部分 |
|---|---|---|
| `TimberSchedule.derive` 的列（id／surface／A／B／L／sources／assembly／sourceFingerprint） | 唯一的需求列來源，直接讀 L | 回傳值除 `sources[].terminal` 新欄位外不變，訊息不變；**新增**：每個 `throw` 的 Error 帶 `code`，依 a7bff8f 的 `timber-schedule.js` 行號：:11 `ASSEMBLY_OWNER_AMBIGUOUS`、:18 `ASSEMBLY_SOURCE_UNVERIFIED`、:26 `REFERENCES_UNVERIFIED`、:28 `SCOPE_ID_INVALID`、:30 `TIMBER_ID_INVALID`、:35 `NOT_EVALUATED`、:39 `ENDPOINT_RANGE`、:44 `SELECTION_STALE`（第 1 步預檢通過後，:44 理應不會觸發，若觸發仍歸 INCOMPLETE） |
| `row.sources[]`（engineeringSources 子集，或 owned 的 slot 來源） | owned 列的來源要從 `assembly.bindings[].effective` 帶入 `terminal`，所以 `assemblySource()` 一併複製 `effective[field].terminal` | F4a CSV 逐位元組不變：`timber-schedule.js:57` 序列化 `dimension_source_definitions` 時以 replacer 剔除 `terminal`（快照料單共用同一 serializer，一併不變）|
| `references.sourceFingerprint` | 計量世界的釘選值，匯出前重新核對 | 定義不變 |
| `feExportTimberSchedule` 的守門 | 照樣用於裁切匯出，另加設定指紋與範圍鍵 | F4a 匯出逐位元組不變（見上列 CSV 剔除 terminal）|
| `featureAttachments` 的 records 上限 | 依主迴圈裁決，以 main `5cc1ffa` 為準：`records.length > 3`（`feature-attachments.js:215`，3 種 kind）改為 4。**註**：即將合入的 a7bff8f 已是 `> 4`（同檔第 225 行，含 rule-case 共 4 種），屆時應改為 5。寫入時以實際基底加 1，並與同時新增 kind 的提案統一配號 | 其他 kind 的驗證不變 |
| MODEL-SNAPSHOT-SCHEDULE | 首版不接，回 `WORLD_KIND` | 不變 |

## 7. 去重契約

- 計量世界**恰有一個**，實例鍵是 `(世界, timber:id)`（含 0）。範圍重疊時，同一 id 只計一件。
- 不同 id 即使同截面、同長、同範本、同組構規則，仍算兩件。
- 跨世界：請求格式只帶一個計量世界，跨世界在格式上無法表達（不另設 CROSS_WORLD 分支）；不建 ledger，也不以 UUID、名稱、尺寸或指紋配對。這與 Q32 原案 A 一致。
- 同一 session 內「同 id 刪除後重建」時，以當下世界為準。這不構成 durable 身分宣稱，因為需求範圍本來就不保存。

## 8. 驗收測試清單（數字皆由參考實作 `k1-work/ffd_ref_r1.py` 逐支核對守恆）

共同設定（另註除外）：截面 27×33、材料未設定、S = 3636、e = 5、k = 3、a = 0、r_min = 300。

| # | 輸入 | 預期 | 要打掉的變異 |
|---|---|---|---|
| T1 基本 FFD | id1、id2 各 2560；id3–5 各 890；id6 876 | 新料 3 支。N1：[5,2565] id1、[2568,3458] id3，末刀 3，剩 175、可用 170 → 廢料。N2 同理（id2、id4）。N3：[5,895] id5、[898,1774] id6，剩 1859、可用 1854 → 可留用。每支下刀 3 次 | 漏算件間鋸縫 |
| T2 用到原端面不計刀 | S=3000、e=0；1500、1497 | 1 支：[0,1500]、[1503,3000]；末端不下刀，下刀 1 次 | 若末刀一律計，需 3003 > 3000，變成 2 支 → 紅 |
| T3 末刀小於鋸縫 | 同 T2；1500、1496 | 末刀耗損 1，無剩料，下刀 2 次 | 耗損恆取 k → 剩料 −2，非負檢查紅 |
| T3b 末刀計入 | 同 T2；1500、1490 | 末刀耗損 3，剩 4（廢料） | 「從不計末刀」→ 剩料 7、耗損 0：**期望值紅**（守恆仍成立） |
| T4 末端修整恰滿 | 3626 | [5,3631]，修整耗損 5，下刀 2 次；CSV `leftover_*` 三欄**空** | 輸出 0 或 −5 |
| T5 先用餘料 | 餘料 R1（1000,0,5，U995）、R2（600,0,5，U595）；件 900、590 | 新料 0 支。R2 放 590（剩 7、可用 2，廢料）；R1 放 900（剩 97、可用 92，廢料）。CSV 先列 R2 再列 R1 | 先開新料 |
| T5b 餘料由小到大 | 同 T5 的餘料；只有件 500 | 用 R2；R1 未使用：不列入 CSV、不切、不計刀 | 餘料改由大到小 |
| T6 去重 | 面1全部（含 id1–3）+ 面1明選 {2} + 面2明選 {7} | 件為 {1,2,3,7} | 拿掉聯集 |
| T6b 同尺寸不同件 | id3、id4 都是 890 | 兩件都計入 | 依尺寸去重 |
| T7 世界種類（API 層） | 直接呼叫求值器，world.kind = model:<id> | `UNSUPPORTED/WORLD_KIND`，零方案（跨世界在請求格式上無法表達，不設測試）| — |
| T8 材料分流 | id10 為 M@1@fp1、27×33；id11 未設定、27×33；原材 S1{27×33, M@1@fp1}、S2{27×33, 未設定} | 兩件各配各的原材，從不同支 | 只比截面 |
| T8b 缺原材 | 同 T8，但只有 S2 | `INCOMPLETE/NO_STOCK`，列出「27×33、M@1@fp1」 | 退回未設定原材 |
| T9 截面轉向 | 件 33×27 對原材 27×33 | 配上 | 依順序比對 |
| T10 末端不可求 | 某綁定的 `terminal` 為 null | `INCOMPLETE/MATERIAL_UNRESOLVED` | 當作未設定 |
| T10b 混合 | A 末端是 M@1、B 末端是 literal | `INCOMPLETE/MATERIAL_MIXED` | 取 A 的材料 |
| T10c 舊 native | 回覆沒有 `terminal` 欄位 | `UNSUPPORTED/NATIVE_CAPABILITY` | 退回讀 source 或 path |
| T11 加工餘量 | a=10、L=890 | C=900，CSV 同時列出 L、a、C | — |
| T12 設定拒絕 | k=0、k="2.4"、a=−1、S=10 搭 e=5、餘料 R=10/h0/t10、原材 {27×33,未設定} 與 {33×27,未設定} 並存、fingerprint 非 64 hex | 全部拒絕；設定與歷史不變 | 取整、夾值、重複 |
| T12b 鎖定 | S1 被 R1 引用時，改 S1 截面為 30×40 或改其材料鍵 | 拒絕並回 `STOCK_TYPE_IN_USE`；改名稱、S、e 可以；新建 S2 可以 | 允許溯及修改 |
| T13 留用門檻 | 3323 → 剩 305、可用 300；3324 → 剩 304、可用 299 | 前者可留用，後者廢料 | 以實長比較 |
| T14 唯讀 | 求方案、切 cm、排序、匯出 | World dump／hash、dirty、history、設定 value 逐字不變 | — |
| T15 確定性 | T1 的件順序打亂、範圍順序反轉 | 方案與 CSV 逐 byte 相同 | 移除 id tie-break |
| T15b CSV 與畫面排序無關 | 畫面改為依長度或 id 排序後再匯出 | CSV 逐 byte 相同 | CSV 依畫面排序 |
| T16 匯出新鮮度 | 方案求出後改 World、改設定、切 context、遲到回覆；連點匯出 | 前四項零 Blob；連點只產生 1 個 Blob | 移除任一守門 |
| T17 保存與重開 | 建 R1、R2，刪 R2，再建 | 新 key 為 R3；重開後設定與高水位相同 | 重用 key |
| T17b 能力 | 舊格式讀到新附件、未知 schema、刪掉能力標記 | 全部拒絕，現有專案不變 | 靜默忽略 |
| T18 容量 | ① 需求件 4097 支 ② 範圍 65 個 ③ 新增第 33 種原材 ④ 新增第 129 段餘料 | ①② 求方案時回 `UNSUPPORTED/CAPACITY`，不截斷；③④ 保存驗證拒絕該次編輯 | 截斷，或拒絕層錯置 |
| T19 未設定 | kerf=null，其餘合法 | `INCOMPLETE/MISSING_SETTING` | 補預設 |
| T20 被引用原材不可刪 | 刪除 S1（被 R1 引用） | 拒絕；同一次編輯一併刪除 R1 則可 | — |
| T21 範圍失效 | 明選 {2} 後刪掉 timber 2，或把它移到別的面 | `INVALID/SCOPE_STALE`，由預檢得出、不經 derive 錯誤文字 | 比對錯誤字串，或靜默略過 |
| T22 空 | ① 沒有任何範圍 ② 某範圍沒有任何件 | ① EMPTY ② `INCOMPLETE/SCOPE_EMPTY` | 靜默丟棄範圍 |
| T23 餘料被占用 | S=3000、e=5（新料可用 2990）；餘料 R1（3300,0,5，U3295）；件 3200、3100 | 3200 進 R1；3100 新料放不下、R1 已占用 → `INCOMPLETE/REMNANT_EXHAUSTED` | 誤報 OVER_LENGTH |
| T23b 超長 | 同 T23；件 3296 | `INVALID/OVER_LENGTH`（3296 > max(2990, 3295)） | 判準只看 S − 2e |
| T25 可用長度下限 | S=3000、e=5；件 2989 | 末刀 3，剩 3，可用 max(0, 3−5) = **0** → 廢料 | 可用長度為負 |
| T26 指紋不符 | 原材 M@1@fpX，件末端為 M@1@fpY | `INCOMPLETE/MATERIAL_FINGERPRINT_MISMATCH` | 只比 id 與 version |
| T27 截面不符 | 原材 {30×36, M@1@fp1}，件 M@1@fp1、27×33 | `INCOMPLETE/STOCK_SECTION_MISMATCH`，不是靜默 NO_STOCK | — |
| T28 求值順序 | ① 件 L=3700 且 kerf=null ② a=null 且 L=3700 ③ a=null 且 L=1000 | ① INVALID OVER_LENGTH 加上 INCOMPLETE MISSING_SETTING，整體為 INVALID ② 以 L 判定為 OVER_LENGTH ③ 不判超長，只有 MISSING_SETTING | 先檢查設定導致狀態錯 |
| **E1 工程範例** | `geometry-web/examples/engineering-spec-v1.gcanvas`。7 支角材的 A/B 全是 application，經做法 `example-ceiling-method@1` 鏈到 `example-timber-27x33@1`（fp `f58363d2…db66`）。原材 {27×33, 該材料三鍵}，S=3636、e=5 | 14 個 `terminal` 全是該材料，0 件 UNSUPPORTED。L 依條文推導：t10、t11 = 4000；t12、t13、t20 = 2946；t30 = 1960；t31 = 1959（2946 與 u 1987..2014 已有 `cdp_test.js` P49 斷言佐證，其餘以原生讀值為 oracle 核對）。結果 `INVALID/OVER_LENGTH`：t10、t11 的 C=4000 > 3626 | 前端重做 D28，或判成 UNSUPPORTED |
| **E2 工程範例** | 同 E1，S=4200（夾具值） | COMPLETE，新料 6 支。N1、N2 各放一支 4000（剩 192、可用 187，廢料）；N3–N5 各放一支 2946（剩 1246、可用 1241，可留用）；N6：[5,1965] t30、[1968,3927] t31（剩 270、可用 265，廢料） | — |
| N1–N5（K1-a native） | ① literal／spec／parameter／material 直接來源 ② application 鏈到材料 ③ application 加面覆寫為 literal ④ owned slot 為材料 ⑤ 不可求值 | terminal 依序為 literal／spec／parameter／material(id,ver,fp)、material、literal、material、null；其他回覆欄位逐 byte 不變（剔除 terminal 後比較）；production 與 ASan/UBSan 都通過 | 把 terminal 寫成 binding 層的 source kind（② 變 application） |
| UI | 桌面與 390px 真操作：加入範圍、設定、方案、匯出 | 既有 P80／P81／P83 golden 不減 | — |

- 依 memory「宣告修好前先做突變測試」：每個變異都必須真的變紅，失敗訊息要指得出病因。
- 守恆自檢不可被測試繞過。

## 9. 受影響檔案

- **K1-a（native）**
  - `geometry-core/engineering.inc`：帶 terminal 的 resolve／effective 變體與葉節點寫入。
  - `geometry-web/engineering_bridge.inc`：`json_engineering_sources` 輸出 terminal。
  - `geometry-web/assembly_bridge.inc`：effective 輸出 terminal。
  - 新增 `tests/test_engineering_terminal.py`（N1–N5，含 production 與 ASan/UBSan）。
  - 有逐 byte 比對 `references`、`engineering`、`assembly-read`、`source-inspect-file` 回覆的測試，依新欄位更新期望值（`tests/test_reference_contract.py`、`tests/test_source_inspector.py`、`tests/test_timber_support_projection.py` 等，以實際 grep 為準）。
  - `tests/run_all.py`、`tests/run_all.expected.json`。
- **K1-b（前端）**
  - 新增 `geometry-web/cutting-plan.js`、`geometry-web/docs/CUTTING-PLAN.md`。
  - 新增 `tests/test_cutting_plan.js`：T1–T11、T13、T15、T15b、T18①②、T19、T21–T28、E1／E2 以夾具回覆驗證。
  - 新增 `tests/test_cutting_project_store.js`：T12、T12b、T17、T17b、T18③④、T20。
  - 新增 `geometry-web/cutting_plan_test.js`：CDP P⟨K1⟩，含 T6、T14、T16、UI，以及 E1／E2 真 native。
  - 修改 `geometry-web/timber-schedule.js`：只加 `code`，以及 owned 列複製 terminal。
  - 修改 `geometry-web/feature-attachments.js`：新 kind、strict `boundedJSON`、records 上限、`capabilities()`。
  - 修改 `geometry-web/project-store.js`：`geometry-canvas/⟨K1-F⟩` 與能力清單。
  - 修改 `app.js`、`index.html`、`app.css`。
  - 修改文件 `docs/DOM-CONTRACT.md`、`docs/TIMBER-SCHEDULE.md`、`docs/REFERENCE-PROJECT.md`。
  - 修改 `cdp_test.js`、`cdp_sections.golden.json`、`tests/run_all.*`、`tests/test_timber_schedule.js`（加 code 斷言）、`BACKLOG.md`。
- **SSOT**：`公理層.md` 依 AXIOM-DIFF，審查通過後才寫入。

## 10. 不做的事（首版）

1. 加工確認、庫存自動異動。可留用的剩料不會自動入庫，這需要另立加工狀態契約。
2. 採購、報價、供應商。
3. 接料或搭接。
4. 以保存模型快照為計量世界（回 WORLD_KIND）；跨世界合併則永遠拒絕。
5. 同一（截面, 材料）有多種料長、自動選料。
6. 逐件或依角色的加工餘量；設定值引用 D6b／D31。
7. 最佳化保證；容差分析。
8. 二維面材排板、D36／D37 構件、縱剖或刨削改截面。
9. 跨專案共享庫存。

## 11. 剩餘風險

1. **K1-a 會改變多個回覆的逐 byte 輸出**。凡是逐 byte 比對 live 回覆的既有測試，都要逐一更新。
   MODEL-SNAPSHOT-SCHEDULE 的「live references 回覆與換行保持不變」是當時那個切片的限制，這次是刻意新增欄位，要在契約文件中註明。
2. E1／E2 的 L 有一部分是依條文推導，尚未用原生實跑（只有 2946 與 u 範圍有既有斷言佐證）。實作時必須以原生讀值為 oracle。
3. records 上限：審查依 main 判為 3→4，但 a7bff8f 合入後實際應是 4→5。寫入時要以實際基底為準。
4. 「材料未設定」原材的 UI 文案、FFD 非最佳、無預設鋸縫與修整值，這三項仍屬使用者接受度問題。
5. 條號、格式號、kind 上限，都要與另外 4 份提案統一配號。


## r1.1 修正（第 2 輪審查後，主迴圈直接修，2026-10-10）
- F1：F4a 不變性改為「CSV 序列化時剔除 `terminal`」，F4a 匯出與快照料單逐位元組不變；derive 回傳值僅多 `sources[].terminal`。
- F2：REMNANT_EXHAUSTED 理由改為「本次找到的方案無法排入」，不宣稱料不足；診斷清單各原材種類組各自繼續、每組報第一件。
- F3：刪除 CROSS_WORLD 執行分支（請求格式只帶一個計量世界）；T7 改測 WORLD_KIND。
- R1：§9 受影響測試補 `tests/test_assembly_rules.py:350-351,365,418,427`（寫死 effective 為 {value,path}，加 terminal 必紅，須更新期望值）；`test_reference_contract.py`、`test_timber_support_projection.py:213`、`test_source_inspector.py:107` 為同源比較、不會紅。§6.1 影響範圍另補 `section_profile_bridge.inc:90-91` 的 preview 與 `json_assembly_state` 所在的 7 個輸出（含 `reference_bridge.inc:125` preview）。
- R2：做法 gap 末端（`engineering.inc:251`，`nested={0}` 即 ENG_LITERAL）會被標為 `{"kind":"literal"}`、與直接整數無法區分；K1 只用角材不受影響，`terminal` 欄位文件註明此限制。
- R3：STOCK_SECTION_MISMATCH 限定件的材料鍵已設定時才判。
- R4：derive 拋錯的範圍只報 ROW_NOT_READY，不同時報 SCOPE_EMPTY。
- R5：`settings_fingerprint` = SHA-256（小寫十六進位）of 設定的正規 JSON——物件鍵依 Unicode 碼位排序、無空白、整數無小數點、字串 UTF-8、原材種類與餘料陣列依 key 遞增排序。
- R6：N5（terminal 為 null）在 live World 可能構造不出（提交時 I35 重驗），改以 preview 的 before/after 候選或夾具構造。
- R7：records 上限主述改為 4→5（基底 a7bff8f）。
