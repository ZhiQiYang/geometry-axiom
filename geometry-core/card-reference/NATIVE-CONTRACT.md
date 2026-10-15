# grid-card-reference/1：核心切片 A

依 #250 `f3f99a29` 採納內容與 #253 P-133。#193 是必要基底：最後刪除之後的明確重新宣告使用原有 I38 守門。
核心不依賴卡片名稱、領域範本、欄位順序或尺寸大小。正式條文與版本常數由任務 19 維護，本切片不改寫 SSOT。

## 一份來源及原生語法

`GridSystem.card_reference` 保存 set、parameter_id、fields[2]；沒有獨立 World id、swap bit 或 incarnation。
兩軸 card_length 是來源標記；既有 step/panel 欄位只是求值快取，序列化只輸出 `card`，不輸出有效長度或隱藏舊來源。
其他 phase/gap/anchor/stagger 的直接值與 ParameterRef 保留。

```text
requires parameters/1
requires grid-card-reference/1
# 來源卡片仍由原有 parameters begin/card/field/end 保存，位於網格之前
grid-system 4 name-hex 47 main-along none card-reference 10 3 8 u repeat -5 card v repeat 7 card
```

`card-reference P U V` 與兩個 `card` token 必須完整，兩軸只接受 repeat/repeat-panel。
例如 u 可為 `repeat-panel card gap param:10:9 from -5`；phase/gap/anchor 不從整卡推斷。
新語法即要求兩項能力；缺少其中宣告或未知版本，場景在替換 World 前拒絕。
舊 parameters/1 的既有能力補註例外保持；舊直接值、逐欄與有限網格不轉換。

## JSON 候選與讀回

沿用 `engineering-transaction/1`、expectedRevision、engineering-preview/confirm/cancel。
操作都只改候選；出口先檢 I38 最後刪除，再清除順序及捕捉 scratch，完整重算全部依賴，確認時再重驗，一次 history。

| op | 其餘欄位 |
| --- | --- |
| put-grid-system | value：`{id,name,mainAlong,u,v,cardReference?}`；mainAlong 為 none/u/v，u/v 是完整既有軸 DSL 字串，cardReference 是下列三欄物件 |
| set-grid-card-reference | id、value：`{parameterId,uFieldId,vFieldId}`；兩軸既有長度來源明示整組取代 |
| swap-grid-card-reference | id；只交換 fields[0]/fields[1]，重新驗 stagger 等全部限制 |
| unbind-grid-card-reference | id、mode：parameter 或 direct；一次轉兩槽，其他來源不變 |
| parameter-package | operations：僅 put-parameter/delete-parameter/import-parameters；整包讀完及求值，不接受包內插入解除 |

put-grid-system 是完整宣告，包含其他維持不變的軸設定；不補 phase、gap、anchor 等缺欄。
已有整卡時，完整宣告若改成直接／逐欄而未先明示整組解除，亦拒絕同值 token，不能暗拆。
明確重新宣告整卡來源使用獨立的 PARAM_OWNER_GRID_CARD；只對調／改綁整卡不會替其他逐欄來源蓋章。
完整 put-grid-system 另對其實際宣告的逐欄來源記錄宣告。沿用 #193 的最後欄位刪除序列與每一引用者判斷，不更改匯入配號。

direct 解除只在該有序步驟依原生參數 evaluator 重算必要欄位並驗整卡；缺失／刪除／不合法來源拒絕。
不讀畫面鏡像、正式舊 World、刪除值快取或後續卡片修改。
預覽 `cardCaptures` 明列 gridSystemId、parameterId、兩個 fieldId、values[2]、timing=ordered-candidate-step 及候選事件 order。
捕捉紀錄只在預覽序列化副本內，確認後不進 World、dump、定義指紋或 history。

objects 的 gridSystems、原生預覽及 engineering 候選 after.geometry.gridSystems 均回一份 cardReference。
受控槽回 stepSource/panelSource=card，另回唯讀 effectiveStep/effectivePanel；該槽沒有 step/panel 直接值或 ParameterRef。
parameterUses 回一個 kind=grid-card-reference 的使用單位，內有兩條 fieldId/axis/slot 路徑，不用兩份逐欄使用處冒充。
唯讀 source-inspect 亦保存卡片單位與兩條實際欄位路徑。其定義指紋含映射而不含有效長度；同值對調改定義指紋，改來源值只改有效值指紋。這是原生 bridge 索引，不新增 UI 或變更幾何根走訪。

## 保存、格式與 P-133

完整專案分配 `geometry-canvas/18`，沿用 /17 的全部附件政策，只在整卡資料需要時提升；/1–17 原義保持。
world.scene 與 manifest.requiredCapabilities 兩處都須保留 grid-card-reference/1、parameters/1。
JSON 模型包仍使用 geometry-model-package/1，新增明示能力；完整 canonical base_scene 保存來源、映射及卡片傳遞依賴。
依 P-133，幾何走訪不必列網格；model_base.c 只新增能力序列化，沒有修改幾何依賴折疊。
verify_package 仍從來源重算幾何及摘要；不得輸出兩個常數或兩份 ParameterRef 代替 CardReference。
geometry-parameters/1 的匯出／匯入仍只有卡片閉包，不包含網格，不新增 D55 根種類。

## 驗收邊界

`tests/test_grid_card_reference.py` 登記 31 個具名 CR 核心方法；CR19 會用實際 ZIP writer/reader，開到新原生 context 並逐字核 dump。
`tests/test_card_reference_project_store.js` 檢查 /18 的保存、降版、能力、未知版本及舊逐欄相容。
原 PROPOSAL 沒有列 CR23 或 M15，沿用其原始編號，不自行補號。
CR24／M23 是 UI 切片，本次不宣稱桌面／390px 操作或草稿支援。
CR18 本次驗未啟用身分帳的對照；此基底未宣告原生 identity-ledger/1，啟用身分帳的新記號／外部 pin 與 M12 仍待其實作切片，不新增假 skip 或聲稱通過。
CR10 以原生 AST 表示 `(3/2 mm) × 2` 的精確尺寸；文字入口沿既有 parser 寫 `=3 mm/2*2`，不把既有 `3 / (2 mm)` 反向長度語意偷改成尺寸。
實際 pass/fail、突變結果與受測 head 以 PR 的最終交付收據為準，本文不把計畫當成執行結果。
