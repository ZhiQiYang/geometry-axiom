# 新公理實作與驗收紀錄

GEO-130 新建模執行器：見 [使用方式](MODELING-RUNTIME.md) 與 [實測紀錄](MODELING-VALIDATION.md)。
可輸出確定性 3D JSON／OBJ；使用 C 舊場景驗證與 Python 精確運算。GEO-130 當時未改舊 C DSL 或畫布 UI；後續 GEO-205～210 已由正式 Canvas 接入從面建立空間、角材結構、模型保存與牆高編輯，見 [空間建模操作說明](../geometry-web/docs/SPACE-MODELING.md)。新型別仍未併入舊 C World，模型採獨立交換包保存。

驗收基準：`公理層.md`，包含 2026-09-18 的 GEO-123、GEO-124。
本次只修改實作、示例、測試與實作文件；沒有修改公理層或閱讀器。
GEO-124 是執行期間另一個工作已提交的條文同步修正，本次跟隨該版本核對。
基準 SHA-256：`c60e0f709d5f29041a8c3d84775245b66ffffd2c9cc2330f82d45391c6c53700`。

## 修正對照

| 條文 | 實作結果 | 驗證 |
|---|---|---|
| D6/D6a/D6b、I7/I9 | 具名規格、五類引用、有理係數精確加總後取下界；拒絕裸 mm、缺引用、異面異軸、循環及運算溢位 | reference contract |
| D7、I12/I13、R6 | 只宣告 A/B；at-line guide/grid 或 at-face 外邊/孔邊/角材；跨距自動求唯一解；奇數寬多 1 mm 在正側 | 場景、contract、bridge |
| D9、I23、R4/R6/R21 | 保存引用與放置順序，改線、規格、網格、截面、邊界、框架或擋面時重算 | contract、全接受場景 dump/幾何往返 |
| I8/I8a、R20 | 候選世界預覽，列出新舊幾何和違規；確認 token 綁定舊世界，套用前重驗；錯誤、取消、過期確認均不提交 | contract、core、canvas、Chrome 對話框 |
| D10a、I10 | 3/5 mm 奇數縫合法，縫中線取下界；面材起算點仍按條文固定 | 場景、contract |
| D11、R6(d) | 同面擋面與重複邊檢查，全世界重新檢查端面支撐 | 場景、core |
| D4、I2、R18 | 自带矩形適用同一邊界角色規則；不再額外要求輪廓頂點數為偶數 | 場景、contract |
| I5/I6/I11、D15–D17、I18–I22 | 保留足跡、孔洞、FREE 邊、不重疊、角色、優先級與主支軸驗證 | 場景、core、bridge |
| D12/I14、D13/D14、I15–I17、R8–R17 | 保留畫布、空間、RC 柱樑、投影拆分與交易流程 | 場景、core、canvas、Chrome |
| R1/R5 | 拾取依繪製順序；拖線吸附至可驗證引用，無合法引用就拒絕；單擊不消耗復原步驟 | contract、Chrome |
| D6/D10 | 面內參考線、格線與命中範圍按有效多邊形扣孔裁切 | Chrome、既有 C 截線流程 |

## 新語法

空間編號必須大於 0(GEO-164):`space_id=0` 是柱樑游離的標記。
`space 0` 與柱樑明寫 `in 0` 均拒絕;游離柱樑請省略 `in`,並明寫 `z` 或 `top`。
柱樑本身的編號 0 仍合法。舊場景若宣告空間 0,須先改為未使用的正整數,
並同步修改其空間引用;載入器不會自行猜測歸屬或改寫存檔。

參考線方向 `u` 表示沿 U 走、位置是 V 座標；`v` 表示沿 V 走、位置是 U 座標。
引用式允許 `+`、`-`、整數或分數係數乘引用量。負值的取整也向下，不是向零。

```text
spec 主支中線 500
guide 1 1 v spec:主支中線
guide 2 1 v 1/2*edge:e1:u+spec:主支中線
timber 3 27 33 role primary
place 3 on 1 at-line guide 1 +v +n
```

上例需先建立承載面與合法端面支撐，完整可執行示例見 `room_a.scene`、
`demo-two-timbers.scene`。網格與構造尺寸仍依 D1/D10 等原條文接受整數定義。

| 引用量 | 寫法範例 |
|---|---|
| 具名規格 | `spec:主支中線` |
| 外邊／孔邊座標 | `edge:e1:u`、`edge:h0e1:u` |
| 外框／孔頂點座標 | `vertex:v2:u`、`vertex:h0v1:v` |
| 參考線 | `guide:1` |
| 格線 | `grid:1:u:0` |
| 面材／縫寬 | `panel:1:u`、`gap:1:u` |
| 角材截面 | `timber:3:A`、`timber:3:B` |
| 已放角材側面 | `timber:3:u:lo`、`timber:3:u:hi` |

```text
place 4 on 1 at-line grid 1 u 0 +v +n
place 5 on 1 at-face e0 +u +n
place 6 on 1 at-face h0e2 +u +n
place 7 on 1 at-face t3 through 1500 +v +n
place 8 on 1 at-line guide 2 between t3 t4 +u +n
```

`through` 只是選跨距，`between` 只是選擋面，都不能跳過幾何／角色守門員。
參照角材側面有兩個合法解時拒絕並列出候選，不自選一側。

## 影響預覽

網頁與 GDI 在會改變已放角材的操作前顯示預覽。CLI/bridge 可使用：

```text
preview spec 主支中線 900
confirm <本次回傳的 token>
cancel-preview
```

預覽不寫 World、不佔復原步驟；表格保守地列出所有已放角材，包括依賴链受影響者。
bridge 的 `references` 回傳求值後幾何，`preview` 回傳 `timbers` 的 before/after、
`violations` 的角材、條文、預期與實際。無法推導的幾何明列為 unavailable，絕不假造尺寸。
任何有違規的預覽不可確認。批准前幾何變更使 token 過期；純畫布位置不影響幾何批准。

舊固定座標存檔不能可靠還原引用來源，因此明確拒絕，不默默轉換。
禁止的舊語法包含明寫 L、`at`、`at-guides`、`at-grid`、`at-edge`、`grid-ref`、`span-auto`。

## 驗證方法與範圍

建置與重現命令見 `tests/README.md`、`geometry-web/README.md`。
檢查順序為：條文對照 → 實作／示例修正 → 核心與保存測試 → Chrome 實際操作 → 第二輪回歸。
第二輪另找到並修正預覽後群組回滾、單擊誤記歷史、矩形承載面角色驗證、畫面扣孔裁切。

Windows 原生 C 與 bridge 可以編譯；本機 Smart App Control 阻擋未簽章程式執行，
執行與瀏覽器驗證使用已有 WSL 的同一份 C 原始碼。GDI 視窗互動在此環境無法實測。
`geometry-web/start.ps1` 會重新編譯 WSL 核心並啟動本機網頁，不調整系統安全設定。

此驗收只涵蓋公理已定義的模型；完成面、面材厚度等「未來的層」未自行實作。

### 最後驗證結果（2026-09-18）

| 檢查 | 結果 |
|---|---|
| 場景接受／拒絕與尺寸 | 121 / 121 |
| C 完整性、支撐去重、歷史與交易 | 80 / 80 |
| 新公理引用合約（含 R13 分片與角材 ID 0） | 25 / 25 |
| bridge 保存、所有接受場景重載 | 9 / 9 |
| HTTP 服務輸入與故障處理 | 8 / 8 |
| 畫布/API 整合檢查 | 412 / 412 |
| 完整 Chrome 操作檢查 | 273 / 273，0 未捕捉例外 |
| 最終 Chrome 引用流程、表單寬度及扣孔命中 | 12 / 12 |

核心、場景與 bridge/引用合約另以 AddressSanitizer + UndefinedBehaviorSanitizer 通過。
完整 Chrome 測試後，新增的部分共線擋面回歸再跑核心全套；最終啟動器重編譯後，
再驗證畫布與引用對話框。Windows MSVC 的原生核心及 bridge 建置通過。
