# AR06：原生角材生成

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

首版有限三構件，不支援反組法、ortho-split、多跨距展開、任意嵌套或相位格線。
端面接觸不是固定件、工序或載重合格聲明。實體手機鍵盤／系統選檔／下載、Windows GDI 手測仍待另外驗證。
