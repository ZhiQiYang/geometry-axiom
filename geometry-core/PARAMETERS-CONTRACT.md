# 畫布參數操作契約（GEO-223）

依據：已核准 `公理層.md` D31 / D60 / I38 / I39 / R33 / R56，以及 P-111／P-121／P-122。參數運算只由原生核心完成。

## 定義與上限

- `ParameterSet`：uint32 `id`、UTF-8 `name`、有序欄位與 `nextFieldId`。每世界最多 64 卡、256 欄；每卡 1–16 欄。
- `ParameterField`：卡片內 uint32 `id`、唯一 `name`、`dimension | count | ratio` 與結構化 `expression`。
- 名稱為 1–96 個 UTF-8 位元組，禁止控制字元；超長或空名以 `I38 NAME` 拒絕（條文約束，不歸入容量錯誤；Q24-a 🔒）。完整專案保留欄位最高使用記錄；一般新增欄位不回用已提交刪除的低號。同一候選明示刪除後重建欄位依 D60 是新存在期，適用下列 I38 引用保護，不能只用高水位讓引用反例提前失敗。
- 精確值回傳 `{num:"915",den:"2",unit:"mm"}`。整數絕對值不得超過 INT64_MAX；小數精確轉換，運算前約分與檢查溢位。
- 算式儲存最多 2047 bytes、128 節點、32 層；欄位依賴深度最多 64。容量不足以 `UNSUPPORTED/CAPACITY` 或 `UNSUPPORTED/PRECISION` 拒絕。

P-121／P-122 的引用保護涵蓋整卡刪除，以及完整卡片重宣告省略欄位造成的 `(parameterId, fieldId)` 刪除。引用者須在該欄位最後一次實際刪除後明確重宣告；刪除前的宣告、單純重建來源與重建後再次刪除，都不算處理了最後一次刪除。完整卡片、組構綁定、斷面構件／拉伸件的明示 put 與工程來源／覆寫的各別明示設定，分別記錄其引用者宣告；自動推導或格式轉換不代替明確改綁。未被刪除的欄位及從未存在過的前向引用不列入刪除事件。

P-129／P-141 明確解讀 I38：刪後的明確操作即為改綁，即使序列化引用內容相同；只處理該操作實際宣告的部分。網格的 u/v、panel/gap、來源/覆寫各自判斷，設定 u 軸不處理 v 軸。guide、datum、grid-system、無法經既有 `set-source` 改綁的 direct grid，以及面材試排的 gap／stagger／threshold 引用，共五類沒有混合候選改綁入口；刪除其來源一律拒絕並指名物件，要求先在原生 DSL 或該物件自己的交易裡改掉引用，另成一筆後再刪。本 PR 不新增這五類的 engineering op；面材試排擁有者不會被候選宣告。（GEO-262 / #253 P-142 S1 更新：#253 的 `put-grid-system` 在同候選內宣告網格系統的逐欄來源，因此 grid-system 自此移出上述清單，刪除其來源改給「同候選解除或改指」的拒絕，只剩 guide、datum、direct grid 與面材試排四類要求另成一筆；原生擁有者領頭的拒絕也在 `other references` 內指名同欄可改綁的引用者（P-142 B2）。）整包預覽的 `redeclaredReferences` 列出最後刪除後已明確重宣告的引用者、來源欄位與說明；這份操作順序只供預覽序列化，不進入正式 World、history 或交換格式。

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
| delete-parameter | id；依 P-060／I38／R33，在整筆候選操作完成後檢查引用，本候選中被刪除的欄位若仍有引用者在最後一次刪除後未明確重新宣告，即拒絕並指名引用者，不因來源鍵已被 put 或匯入重佔而略過；同候選刪除依賴卡或將引用欄改為直接值時，兩種刪除／修改順序皆合法。P-111 更新「不重用身分」為不延續已結束的存在期：無引用者時 put-parameter 同鍵重建依 D60 合法；仍有引用者時逐一適用 P-121。匯入依 R53 對候選 World 加本次已配號取自 0 起第一個未用號，依 P-122 撤回 P-117 的跳過剛刪鍵規則；確認收據仍保留中間刪除的 parameter-field。候選內欄位刪除事件與明確宣告順序只供 I38 診斷及明確解除來源，不參與配號，不是 K3 記號；出口清空所有陣列、計數及追蹤旗標，不進入正式 World／history |
| import-parameters | value 完整參數包，由核心配新卡片身分與改寫引用 |
| set-source / set-override | 原有 grid/timber target，source/value 可為 `{kind:"parameter",parameterId,fieldId}` |
| unbind-source | target；存活的原始來源與覆寫依當前候選重算必要參數依賴；同候選已刪參數卡的來源值依 P-062／P-065 取其自身或上游被覆寫或刪除到無法重算前的最後有效值，含先前修改。明確解除後才把有效尺寸寫成直接值並移除來源及覆寫；原始來源、幾何限制與完整候選驗證仍適用 |

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

P-060 的引用合法性仍依完整最終候選判斷。卡片 delete/delete 與 delete/put-literal 的雙順序、最終懸空拒絕維持；候選內禁止重建同鍵的舊限制已由 P-111／D60 更新。解除獨立來源時只重算該綁定所需的當前參數依賴，因此無關卡片的 delete → unbind → delete 與其餘兩種排列均可完成。原始來源即使有覆寫仍須有效；目標缺失、循環、單位與幾何整數限制，以及完整候選出口的全圖驗證維持。P-062 已裁決：同候選先刪被綁參數卡再明確 `unbind-source`，使用刪除前最後有效值，包含候選內先前修改；仍存活的來源／覆寫重新計算當下依賴。暫存只在候選內供明確 unbind 使用，候選出口清空整個暫存陣列及計數，不能進入 World 比較、序列化或 history；來源缺失或刪除後仍殘留未處理的引用均整筆拒絕。

P-111 的存在期語意不代表本 PR 已提供 K3 身分帳。依 [K3 正式契約](identity-trace/FORMAL-CONTRACT.md)，核心／宿主／保存的 `identity-ledger/1`、啟用及實際記號尚未實作；本次參數守門修正處理現有未啟用路徑與真實刪除收據，不在參數暫存內造記號或宣稱舊記號已換新。依 P-117，啟用後「同鍵重建配新記號」與「沿用舊記號突變轉紅」兩項必要驗收已移交 K3-L（GEO-253），本 PR 不等待或冒稱完成它們。

多來源邊界已由 P-065 採 A（https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6125213098）：D=27、S=@D、目標綁 S，delete D → delete S → unbind 與 unbind → delete D → delete S 都保存 27；同候選先把 D 改為 29 時兩序都保存 29，confirm 後完整 dump 逐 UTF-8 位元組相同。覆寫既有卡片或刪除前，只重算受影響的必要欄位依賴並更新候選內的最後有效值；先改成另一合法值、再暫時改壞與刪除時，保留該新合法值，不退回候選開始前的值。只有來源在解除那一步確實已刪除且明確 unbind 才能消費暫存；暫存依候選內來源代次分開保存。同鍵重建不讓存活舊引用自動改接；依 P-141 補充，明確 unbind 時若來源欄已重建，必須依當下定義求值，故 [delete P, put P(a=99), unbind-source] 保存99，不能讀刪除前快取。D 已刪但 S 仍存活時，unbind 仍依當下依賴拒絕並指出 S → D。存活覆寫同樣重算；一般求值器、最終懸空拒絕及候選暫存清空規則不變。
