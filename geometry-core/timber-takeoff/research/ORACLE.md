# 工作包 U：有限研究 oracle、獨立 checker 與歷史模型

固定套用基底：`19c00180228f6dfdff65684b47160736d2fae7e9`（PR #472）。
此切片延續 [#47 完整已核契約](https://github.com/ZhiQiYang/geometry-axiom/issues/47#issuecomment-6435627794)、[完整核可紀錄](https://github.com/ZhiQiYang/geometry-axiom/issues/47#issuecomment-6794611621) 與 [L 的 S1／後續切片設計](https://github.com/ZhiQiYang/geometry-axiom/issues/47#issuecomment-7175636777)。

## 範圍與可信邊界

這是研究目錄，沒有註冊新 App 能力，也不是正式 `timber-takeoff-sets/1` 附件或 `cutting-plan/2`。固定基底的公理層仍只有 `/1` 的單世界規則；已核完整新稿尚待 SSOT 維護者正式落檔。研究結果的 `COMPLETE` 只表示有限研究輸入通過計量規則，不授權產品匯出、不證明現場物件存在或已施工，也不繞過 `/1` 的 `WORLD_KIND` 拒絕。

`U476-facts/1` 的來源事實是此研究的顯式前提。`native.complete`、模型兩端的 outcome、owner、scenario 及 pins 在合成測例中都是人工控制的觀察值。即使輸入加上 `verified:true`，也不能覆蓋已有失敗。研究程式本身不能驗明 caller 所稱的 native 成功；正式產品仍須由可信 owner 綁定同次 native 讀取、模型原始 bytes、雙端原生驗證與完整專案／方案範圍，且在使用結果前再核時效。

真 native 重播另產出 source graph、模型 producer／replay、雙 candidate、料單與 K1 原件，再投影成研究 facts。那個投影明列離線研究的 owner／scenario，不能補造產品缺少的歷史所有權或將研究 context 誤稱正式持久證明。

## 程式分工

| 檔案 | 角色 |
|---|---|
| `candidate.cjs` | 另外實作的 JavaScript 候選：宣告解析、純計量求值與研究文件歷史。 |
| `check.py` | 只讀 facts 與 proposed result，以逐對來源、逐項覆蓋及獨立算術核驗；不 import／呼叫候選，也不共用 eligibility、grouping 或 trace helper。 |
| `fixtures.py` | 61 個具名合成觀察；不宣稱是 native producer 證據。 |
| `scan.py` | 固定 11,036 格集合宇宙、第三個封閉算術預期、順序／撤銷／換代表檢查與八種惡意結果。 |
| `history_scan.py` | 獨立文件、undo／redo 及單調 allocator 模型；259 條窮舉序列及 9 條具名序列。 |
| `probe.py`、`mutations.py` | 三項 checker 實體來源撤回；每階段新程序，精確斷言與 bytes 還原。 |

研究構想及部分初始測例承接 L 的外部研究包；本輪的新程式、雜湊與執行收據另計。L 的包原件為 `429892 bytes`、SHA-256 `0d8b15ca544526b0e3cf3d61483637af5152a0d8476d9a32de73d7326b4afb6c`。不能把 L 的舊成功收據算成本輪執行結果。

## 正確的件數與長度帳

每個明示 `itemKey` 表示一件計量需求。相同完整來源尚未宣告歸併，或分列在不同 itemKey，必須保持 `INCOMPLETE / DUPLICATE_SOURCE_NEEDS_REVIEW`；不能自動合併或重算成兩件。不同來源即使幾何、尺寸、名字相同也不能合併；硬合後依已核契約回 `INCOMPLETE`。只有結構性錯誤，例如重複 itemKey、同一表示被重複納入／排除，才屬研究中的 `INVALID`。

每個被納入的表示都須核對。代表列只決定代表位置，不能用其正常值遮蔽其他 alias 的錯誤。來源根、存在期、定義與有效值兩軸、材料末端、方向、定位、精確端部支承、typed closure 內容任一不符都不能產生部分完成需求。

守恆式為：

```text
rawRepresentedLengthMm
  = excludedLengthMm + physicalItemLengthMm + removedAliasLengthMm
```

兩份表示同一支 4,000 mm 角材的資料，明示歸併後是 4,000 mm 需求加 4,000 mm 移除別名；不能要求去重後仍保留 8,000 mm 需求。同源分組撤銷後原始表示及原始長度表恢復，但又分列的同源表示仍是 `INCOMPLETE`，不是兩支完成需求。

## 根與讀取的核對

每個研究來源都有必填 `native.rootNodes`：

```json
{
  "timber": {"key":"timber:0","kind":"timber","id":0,"placed":true,"surface":0},
  "placement": {"key":"placement:0","kind":"placement","id":0}
}
```

checker 分別核對 key、kind、數值 id、placed 與承載面，不從 key 字串猜 kind。缺根、錯 kind／id、未放置或承載面錯誤均缺證。current 的 readPin 必須等於 context 的 liveReadPin，包括只有保存模型被納入、live 表示已排除的情境。定義／有效值 pins 的一般合成測例及 native 投影都使用 timber／placement 兩根；沒有把空 map 或只提供一根當成完整證據。

模型的存在期記號取自原保存 sourceIdentity，不能從去身分 replay 新配出的記號補造連續性。這個 checker 比對 referenced closure 的內容，不擴張 K3 對 closure 節點存在期的定義。

## 固定的小宇宙

表示數為 0 至 4；實體來源標籤為 0／1；每個來源長度為 1／2 mm。第一個表示是 live，其餘是不同普通 plan 模型。這些是數量問題的合成研究值，並非全部情境經 native 產生器驗明合法。

每列各自可排除、未宣告，或進入任一集合；用 restricted-growth 編碼移除純 itemKey 更名的對稱，沒有省略分組。來源映射、兩個來源的長度、全部集合分割全部枚舉。

| 表示數 | 格數 |
|---|---:|
| 0 | 4 |
| 1 | 24 |
| 2 | 160 |
| 3 | 1,184 |
| 4 | 9,664 |
| 合計 | 11,036 |

每格經 JavaScript 候選、獨立 Python checker 及封閉算術預期核對。額外檢查每個完成格的順序置換，以及所有具 alias 的完成格之撤銷／換代表。具名例另涵蓋來源變更但值相同、重建同 id、缺原記號、兩端驗證失敗、未知／空支承、typed root 錯型別、混入另一 current 讀取、非法 partition 及 caller 成功旗標無法豁免等。

八種獨立負例是偽造 COMPLETE、未宣告自動歸併、改原生 L、漏 alias、改件數、改需求總長，以及把 1 mm 長度／1 件數量改成布林 true。checker 的 JSON 比對同時驗型別，避免 Python 的 `True == 1` 吞掉錯誤；每個負例必須在指定具名斷言拒絕，不能用任意 exception 代替。

## 歷史模型的獨立宇宙

歷史計數與 11,036 格分開。動作為 add、clear、undo、redo、cancel、reopen；長度 0 至 3 的全部序列共 259 條。另有 9 條具名序列，涵蓋已發 key 不再用、刪除／撤銷／重開後高水位不回退、無變更與取消不配 key、重複或退休 key 原子拒絕、uint32 最後一個 key 與耗盡狀態。

核對每一步的完整研究文件、revision、undo／redo 深度、dirty、needsVerification 與分配 key。這是 `StudyHistory` 研究服務的序列驗證，沒有宣稱完成專案歷史 owner、完整專案 cold open、方案快照、UI lease、World 修改原子性或 App L4。

## 有界重跑

Python 3 與 Node.js，皆僅標準程式庫。從本目錄執行，指定輸出到工作目錄以外的暫存路徑：

```sh
python3 -B fixtures.py
python3 -B scan.py --candidate "$PWD/candidate.cjs" --out /tmp/u476-oracle-scan --bounded
python3 -B mutations.py --candidate "$PWD/candidate.cjs" --out /tmp/u476-checker-withdrawals --bounded
```

集合掃描每批最多 128 個輸入、每個 child 最長 30 秒；歷史每批 64 條序列、每個 child 30 秒。這是新研究工具自己的固定界限，沒有更動任何既有測試的 timeout。原始案例用 gzip 保存，摘要包含未壓縮 bytes／SHA-256。

checker 可使用兩個檔案參數，或從 stdin 讀一個 `{input,output}` envelope：

```sh
python3 -B check.py facts.json proposed-result.json
python3 -B check.py < proposed-envelope.json
```

有效結果 exit 0；具名 `Rejected` exit 1；JSON／輸入／執行錯誤 exit 2 並帶 `U476_CHECKER_INPUT_OR_RUNTIME_ERROR`。後者不是反例命中。

三項 checker 撤回是件數守門、需求總長守門與原生長度守門。runner 實際改隔離目錄的來源 bytes，baseline／withdrawn／restored 各啟新程序，只有精確 `0/1/0`、指定 stderr 斷言、來源逐 bytes 還原才算成功。timeout、import、setup、crash 或不相干失敗一律不計 killed。constructor 的來源撤回另由整合測試交付，不重複混算。

## 尚未由本套件證明

未證明任意不可信 facts JSON 的完整語法安全、正式 native proof acquisition、真專案／方案 owner、正式附件存取與歷史交易、全部大型容量組合、CSV `/2`、UI late-response 與重複下載、正式 Actions／ME 採入、瀏覽器／App L4，或裁切最優性。研究文件 parser 的限額與 bytes 行為由候選整合測試另驗；本套件的有限枚舉不代替那些邊界。
