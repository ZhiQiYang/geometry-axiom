# 畫布參數操作契約（GEO-223）

依據：已核准 `公理層.md` D31 / I38 / I39 / R33。參數運算只由原生核心完成。

## 定義與上限

- `ParameterSet`：uint32 `id`、UTF-8 `name`、有序欄位與 `nextFieldId`。每世界最多 64 卡、256 欄；每卡 1–16 欄。
- `ParameterField`：卡片內 uint32 `id`、唯一 `name`、`dimension | count | ratio` 與結構化 `expression`。
- 名稱為 1–96 個 UTF-8 位元組，禁止控制字元；超長或空名以 `I38 NAME` 拒絕（條文約束，不歸入容量錯誤；Q24-a 🔒）。欄位刪除後其身分不可在原卡重用；完整專案保留最高使用記錄。
- 精確值回傳 `{num:"915",den:"2",unit:"mm"}`。整數絕對值不得超過 INT64_MAX；小數精確轉換，運算前約分與檢查溢位。
- 算式儲存最多 2047 bytes、128 節點、32 層；欄位依賴深度最多 64。容量不足以 `UNSUPPORTED/CAPACITY` 或 `UNSUPPORTED/PRECISION` 拒絕。

## 原生算式

`input` 是編輯入口，核心轉成 AST；持久化只保存 AST。

- 字面值 `915`、`457.5`、`1/3`：沿用欄位單位。
- 算式 `=(@1:2 + 2 mm) / 3`：`@卡片身分:欄位身分` 是來源選擇器產生的內部 token。介面以名稱顯示。
- 支援 `+ - − * × / ÷`、括號、一元正負號；`=` 或全形 `＝` 開頭。
- AST：`literal` 含 num/den 字串與 mm/1；`ref` 含 parameterId/fieldId；add/sub/mul/div 含 left/right；neg 含 left。拒絕未知欄位與未知運算。
- 裸數字在算式內無單位；乘法至少一邊無單位。mm/mm 得無單位。count 最終必須非負整數。
- 依欄位 DFS 求值；整張卡間的雙向依賴不等於循環。錯誤含卡片、欄位及引用路徑。

## 候選交易

沿用 `engineering-read / preview / confirm / cancel`；請求 schema 為 `engineering-transaction/1`，先帶目前 expectedRevision。

| operation | 內容 |
| --- | --- |
| put-parameter | value 卡片，每欄提供 input 或 expression，二者擇一 |
| delete-parameter | id；依 P-060／I38／R33，在整筆候選操作完成後檢查引用，最終仍被定義引用即拒絕並指名引用者；同候選刪除依賴卡或將引用欄改為直接值時，兩種刪除／修改順序皆合法。同一筆候選（一個 transaction，或一行 `engineering archive`）內已刪除的卡片身分不得再被 put-parameter 宣告，import-parameters 配新身分時也會略過（I38／I39）；名單屬於候選本身，取消、失敗的預覽與其他入口都不會殘留，之後另一筆交易可再使用 |
| import-parameters | value 完整參數包，由核心配新卡片身分與改寫引用 |
| set-source / set-override | 原有 grid/timber target，source/value 可為 `{kind:"parameter",parameterId,fieldId}` |
| unbind-source | target；存活的原始來源與覆寫依當前候選重算必要參數依賴；同候選已刪參數卡的來源值依 P-062 取刪除前有效值，含先前修改。明確解除後才把有效尺寸寫成直接值並移除來源及覆寫；原始來源、幾何限制與完整候選驗證仍適用 |

多個參數操作可含向前引用；全部放入候選後，依序驗參數、工程尺寸、網格、定位與角材。confirm 核對令牌、版本與完整定義，再重驗；成功一次 history 快照。卡片座標不影響令牌。

無限網格的 repeat phase/step 與 repeat-panel panel/gap/anchor 可寫 `param:卡片:欄位`；有限 SERIES/EXPLICIT 保持原義。有限 PANEL_LAYOUT 透過工程來源接入 panel/gap。定位引用式可用同一 param token；含參數整式精確求和，最終非整數拒絕，舊式維持取下界。

## 保存與交換

- 能力 `parameters/1`；完整專案使用 `geometry-canvas/6`，舊 /1–5 仍讀取。執行器、模型套件及專案清單必須保留並驗能力。
- 原生 `.scene`：`requires parameters/1`，再以 `parameters begin`、base64 JSON card/field records、`parameters end` 組成完整區塊。缺 `requires parameters/1` 但區塊完整時照常載入並於輸出補回宣告（與 engineering-spec 既有慣例相同，屬升級不是降級）；明確拒絕的是未知版本（`parameters/2`、`geometry-canvas/7`）與專案清單 `requiredCapabilities` 被刪或不足（Q24-b 🔒）。每欄一行避免超過既有行長上限。區塊只可在原子場景載入中使用，不允許互動逐行留下未完成參數。
- 卡片位置：`canvas-pos parameter id x y`；有效值不進定義，重開重算。
- `geometry-parameters/1` 為 `{schema,cards}`；cards 使用完整定義，不含有效值或使用物件。匯出以整卡取得全部遞移來源。匯入必須自足，重配卡片身分、保留欄位身分並改寫 AST，候選全部有效才確認。同名不覆寫。
- UI 草稿阻擋完整專案匯出與保存；離開可取消以繼續編輯，或明確捨棄。非同步試算核對編輯序號、草稿版本與專案 context。

## 正式介面與驗收

建立選單 → 參數；選取卡片在既有檢視器編輯。單值、寬×長、W×H 範本與快速輸入只建立草稿。引用連線只在相關物件選取時顯示。舊具名規格透過共用入口編輯原 spec。

核心驗收：`tests/test_parameters_core.py`。專案與能力：`tests/test_parameters_project_store.js`。正式瀏覽器：`parameter_workflow_test.js` 已接入 `cdp_test.js`；局部開發可用 `GEOMETRY_PARAMETERS_ONLY=1`，完成仍須完整回歸。

向量、座標轉換、組件嵌套、跨專案共用庫、拖線建立引用與板邊／縫中心切換不在本期。完整驗收見 [參數驗收紀錄](../geometry-web/docs/PARAMETERS-VALIDATION.md)。

### 互動 archive 入口的完整重驗（PR #193 跟進）

`engineering archive <base64 operation>` 每行是獨立候選。成功解析／執行 op 後，先查該行最終候選是否仍引用已刪身分，再清除退役清單，並依 I8／I38 重算參數及完整幾何依賴，才可預覽有效或確認提交；不得把新欄位尚未求值的 0 當正式結果。缺失引用、除零或幾何使用處不接受分數時，候選無效，正式 World 與 revision 保留。場景檔載入仍在讀完全部紀錄後完整重驗，不把互動入口的時點套用到半份場景。

P-060 已裁決引用合法性依完整最終候選判斷。卡片 delete/delete 與 delete/put-literal 的雙順序、最終懸空拒絕及身分不重用已完成；解除獨立來源時只重算該綁定所需的當前參數依賴，因此無關卡片的 delete → unbind → delete 與其餘兩種排列均可完成。原始來源即使有覆寫仍須有效；目標缺失、循環、單位與幾何整數限制，以及完整候選出口的全圖驗證維持。P-062 已裁決：同候選先刪被綁參數卡再明確 `unbind-source`，使用刪除前最後有效值，包含候選內先前修改；仍存活的來源／覆寫重新計算當下依賴。暫存只在候選內供明確 unbind 使用，候選出口清空整個暫存陣列及計數，不能進入 World 比較、序列化或 history；最終殘留引用仍整筆拒絕。

多來源邊界待裁決：D=27、S=@D、目標綁S，先delete D再delete S再unbind目前因S刪除時已缺D而拒絕；若先把D改29亦相同。先unbind再刪兩張卡則能求得27／29。四組preview與cancel診斷已交 https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6124416895；是否保留上游刪除前S的最後有效值仍等候Claude裁決，未自行加入一般失效引用fallback。
