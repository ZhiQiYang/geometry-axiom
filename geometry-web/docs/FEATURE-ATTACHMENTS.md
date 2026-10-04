# 有界功能附件與單一網格草稿（#45，第一保存切片）

`feature-attachments.js` 是有限種類的 plain JSON 驗證器；`project-store.js` 保存附件，`ReferenceWorkspace` 協調專案上下文及既有歷史。附件不宣告 World，不執行程式、不保存 preview token、DOM、快取 URL 或另一份 geometry。

這一切片完成 adapter → 完整 `.gcanvas` ZIP → 重開 → undo/redo 的資料路徑。**尚未接入網格表單自動捕獲、save 前 flush、重開表單、來源失效提示、既有來源→邊界入口與 native confirm 清草稿同一步；#45 尚未完成。** 邊界頂點、四側擴大及承載面套用草稿也尚未纳入本 schema，現有工作區仍照原 save gate 阻擋，沒有假稱全部原始工作已可保存。

## 保存格式與能力

非空附件使用 `geometry-canvas/10`，清單包含：

```json
{
  "featureAttachments": {
    "schema": "geometry-feature-attachments/1",
    "records": [{
      "kind": "grid-draft",
      "schema": "grid-editor-draft/1",
      "value": {
        "schema": "grid-editor-draft/1",
        "draftId": "editor-uuid",
        "kind": "binding",
        "intent": "create",
        "baseRef": null,
        "inputRefs": [],
        "rawForm": {
          "igSystem": "0", "igBoundary": "", "igVertex": "",
          "igCellI": "-", "igCellJ": " 001 ",
          "igAnchorUN": "1", "igAnchorUD": "0",
          "igAnchorVN": "", "igAnchorVD": ""
        }
      }
    }]
  },
  "requiredCapabilities": ["grid-editor-draft/1"]
}
```

目前只支持 `grid-draft`，每專案零或一份；未知種類／任一 schema／額外欄位／重複／超限拒。非空附件被降至 `/1`…`/9`、移除附件但保留能力、移除所需能力，都拒。合法空 envelope 保存時移除，沿資料選擇既有格式。第 10 版仍保留組構生成、參數、工程來源、完整模型、圖頁原始 bytes 與第 9 版輪廓核對收據，沒有降級或剝除既有能力。

`grid-editor-draft/1` 是本 reader 的編輯能力。`readerCapabilities(nativeCapabilities)` 加入它用於專案能力檢查；`sceneCapabilities`、原生候選 `required_capabilities` 及原生能力 validator 都仍拒它。它與尚待 native owner 實作的 `grid-subdivision-rules/1` 沒有互相代替。

## 精確原始輸入與引用

`rawForm` 必須保留有限完整欄位，每值都是原樣字串，最多 4096 UTF-16 units；不 trim、parseInt、Number、歸零或填預設值。空白、`-`、`1e`、signed-64 越界、分母 `0`、未啟用軸內輸入均可保存，不能因此成為正式來源／配置。

- `source`：`igName`、`igMainAlong`，以及 U/V 各軸的 `Source`、`Step`、`Phase`、`Panel`、`Gap`、`Anchor`、`Stagger`；後六欄每欄另有 `...Source` 參數選擇字串。兩種模式及未啟用軸欄位全部保留。
- `binding`：上例九欄。`igSystem` 記選擇的來源，`igVertex` 記原選擇器字串。後續 UI 恢復必須使用已保存 boundary 幾何與 key mapping pin 核對選擇，不能拿重排後 index 或新同號物件自動替代。

`create` 的 `baseRef` 必須 null。`edit` 必須為相應的 `grid-system` 或 `grid-binding` 已發布內容 pin；`draftId` 只是編輯身分，沒有預先分配正式 ID。`inputRefs` 最多 20 個，不得重複或引用另一份草稿：

- `{kind:"grid-system"|"grid-binding", id, fingerprint}`，ID 0 合法。
- `{kind:"boundary", id, fingerprint, vertexKeysFingerprint}`，boundary ID 必須正；幾何與穩定頂點 key map 分別 pin。
- `{kind:"parameter-field", parameterId, fieldId, fingerprint}`，兩個 ID 各可為 0…uint32 max。

所有 pin 是 64 位小寫 hex。它們是編輯來源證據，不是正式宣告或可認證的身份沿革；raw 中缺失／錯誤引用仍須可保存，故匯入不要求它們在 World 出現。後續表單／預覽 owner 必須將缺失或內容改變視為 stale、要求明選並拒舊候選，不能匯入時自動關聯或提交。正式圖頁／投影引用仍經現有真 native 最終物件閉包驗證，沒有放寬。

整個 envelope 最多 128 KiB；遍歷限制深度 12、4096 值，拒 NaN/Infinity/undefined/函式/class instance/accessor/symbol/稀疏或帶額外欄位的陣列。先驗再 clone，避免 JSON.stringify 靜默丟值。

## 共用 owner API

```text
readFeatureAttachment("grid-draft") -> deep copy | null
setFeatureAttachment("grid-draft", validValue | null, expectedContextToken)
```

寫入必須提供目前 `getProjectState().contextToken`；token 綁目前 history frame，undo 回同一 context 也產生新 token，舊非同步 owner 不會復活。過期 token、專案／核心 busy、history group、prepare/load 未完成、只讀或另一分頁衝突都先拒，沒有 dirty/history 變更。成功新增、替換或捨棄是一筆既有 local history；值相同或不存在時刪除是 no-op。呼叫者與回傳值的修改不改 saved record。完整 snapshots、切專案、清空／新專案、恢復資料及 browser history window 以外的 core undo 都保留相應附件資料；不建立第二條歷史。

其他已批准種類（#77 `source-rooms`、#49 `rule-cases`）待各自正式 validator 與閉包接入再加入白名單，現在明確拒。#49 匯入的歷史 receipt 不能只靠自洽指紋冒稱可信新 pass；須明示歷史／待重跑，或由目前受控 executor 重跑。

## 驗證方法

現有 `test_project_store.js` 的可攜、版本拒絕、核對收據共存與 history 案例擴充來源／配置完整 raw 往返、能力分離、降版／剝除／未知 kind/schema/超限負例。`test_reference_workspace_races.js` 擴充真 adapter 的 clone/no-op/token/busy/group、ZIP、匯入與切案 undo、新案／清空及跨分頁拒寫；VM DOM/PDF 是 fakes，不能冒稱實際瀏覽器 UI。既有測試方法數不變。root另授權共用owner註冊已合 PR101 的四個 #49 Python suite，三個需真 bridge、一個純 validator；完整跑後新增四個 expected 計數，全部原凍結計數（scene139、integrity88等）、mutation/golden維持，不覆寫 #85 證據。

原生 native/ZIP 能力與瀏覽器載入需在交付 exact head 執行；本文件不把舊 head 的 CI 或實體手機當作本切片證據。A24 實機仍未驗。
