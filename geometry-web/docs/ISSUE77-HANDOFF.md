# #77 人工多房間切片：模組與 owner 接線交接

範圍依使用者接受的第 8 項明文建議及 PR100（`0230e436870ec3ba06fcb0735ffabc3b7427979d`，已隨 main `b3c210791d128dc84c3222078df2472b70cc0e60` 合併）。程式驗證基底 `1075058be37d37b98a2a910f4f67b87583be85b3` 與 b3c2107 的相關程式 blob 相同；PR 分支已 fast-forward b3c2107。只有人工連續描房；沒有批准整包 Q37 舊 proposal、原生房間樹、3D parent、自動 transform 或 #54/#87 自動辨識。原生 geometry 唯一來源仍為 native boundary。此 PR 沒有修改共享 app、index、project-store、reference-workspace、ContextHistory 或格式號，不能單獨宣稱 #77 已在產品啟用。

共用單 writer：thread `01a100b5-800b-75f2-9a02-71ee53e550ba`；#77 worker：`01a104fc-a75a-728a-8d74-2e323f84d08c`。共享附件框架依 PR100，不能將 TEMP 專用 prototype 的 `roomSources` 格式接入產品。

## 最小附件契約

kind `source-rooms`；payload schema `source-rooms/1`；frontend capability `source-room-collection/1`。capability 及 project format 分配由共用 owner 決定，這不是 native 生成能力。`source-plane.js` 導出 strict validator，拒未知欄位／schema、重複 source/page basis、缺 asset、錯 membership 及容量超限（256 planes/collections、10000 rooms；工程上限，不是新增公理）。

```text
{schema, planes, collections, rooms}
plane: {id, sourceId:sha256, page, coordinateSpace, pageSize,
        calibration, alignment:{x,y,mmPerPx,rotation}, basisRevision}
collection: {id, planeId, roomIds}
room: {id,name,boundaryRef:{kind:"boundary",id,associationPin:sha256},
       acceptedBasisRevision,reviewState:confirmed|needs-review|needs-reassociation}
```

每 source/page 僅一份 calibration/alignment。rooms 沒有 polygon、geometry 或 basis 副本，也沒有 placement／parent 引用。`associationPin` 使用完整 native `boundary` 回覆的 `geometryFingerprint`，包括 native 分類；不能在產品以 loops-only 自算 hash 取代。`references(value)` 返回 `{sourceIds, boundaries:[{kind,id,associationPin,reviewState}]}`，供原圖閉包和 typed refs 檢查；`validateNativeRefs(value, candidate.final_objects)` 只驗 ID 存在，**不能單獨作身份驗證**。`validateNativePins(value, Map<boundaryId, fullNativeResponse>)` 檢查所有有效引用有 native 指紋，confirmed 必須完全相符。needs-review 保留明示複核，編輯仍拒舊 pin；未知沿革必須由 owner 呼叫 `unknownHistory`／`retireBoundary`，不能按同號重接。沒有擴建 durable incarnation ledger。

目前 `scene-import-bridge.inc` 的 `load-prepare.final_objects` 只有 boundary IDs，沒有 candidate 指紋；live `boundary id` 查詢也不能冒充未發佈 candidate。因此 owner 需協調 native writer 增加最小 candidate 摘要（例如 `boundaryFingerprints:[{id,geometryFingerprint}]`）或提供等價隔離 candidate 核對，再於 publication 前驗 pins。只加 hash/id 摘要，不增加 metadata polygon，也不能先 confirm 換案才驗而失去失敗不改原案的保證。

basis 變更只改共享 plane、增加 revision，舊房變 needs-review；不改 native geometry。新房接受目前 revision。刪 native boundary 時 owner 同一步標 needs-reassociation；同號重建不解除。undo/redo 恢復整份附件。解除列表關聯只移除 metadata；native delete 仍由既有明示刪除動作處理。

## 與 PR100 草案的相容性與缺口

一般 metadata 只用 `ReferenceWorkspace.readFeatureAttachment("source-rooms", contextToken)` 和 `setFeatureAttachment("source-rooms", value, contextToken)`。draft 不寫附件、不建立 placeholder native boundary。讀值必須 deep copy，context token 過期拒寫，no-op 不加 history；原圖來源在保存閉包裡只存一份。

草案的三參數 setter 固定「one local history step」，**還不足以同一步 native confirm + metadata**。現 adapter 提供 owner 待定的第四參數：`{recordHistory:false, roomLease, reason}`，只能在本 lease 的開啟 native history group 內寫，不另 push；一般改名／basis／unlink 為 `{recordHistory:true, reason}`。owner 若採其他同交易接口，應只改薄 adapter 的此呼叫，不能讓 setter 忽略 options 而產生第二步歷史。此接口未落實前不要啟用 patch。

`RoomCollectionWorkspace.configure(adapter)` 需以下 opaque callbacks；模組不直接持有／改 `ReferenceWorkspace.context()` Maps 或 history：

| callback | owner 責任 |
|---|---|
| `readSource(sourceId, contextToken)` | 唯讀原圖 bytes/runtime；驗目前 context。 |
| `readIncarnation(boundaryId, contextToken)` | 現有 history frame 的身份；delete/recreate 失效，undo 恢復。 |
| `beginTransaction(contextToken)` | 在 native preview 前鎖目前 context/history，返回至少含 contextToken 的 opaque lease。 |
| `assertTransaction(lease)` | 驗 lease、context/frame、編輯權與目前服務 session。 |
| `endTransaction(lease)` | 只有已知終局或已完成 receipt recovery 才解鎖。 |
| `groupOpen(lease)` | 此 lease 的 native history group 是否開啟。 |
| `labelTransaction(lease,label)` | confirm 完成後標目前單一步驟，不新增 history。 |
| `adoptLegacySource({plane,collectionId,boundaryId,page,roomId,name,associationPin,contextToken})` | 明選初始舊底圖→共享來源與第一房，單一步 metadata；驗 context/frame/page/native 身份、保留原 source records／證據，只移除所选頁舊獨立 basis 的保存影子，其餘頁保持。失敗不改資料。 |

最後一項是必要缺口：不能只 associate 後仍保存 legacy `faces[].pages[].calibration/alignment`，也不能為去重而刪使用者來源紀錄。owner 若尚無保留 records 的遷移路徑，先拒絕這種舊頁的轉入；不要抹資料。TEMP browser shim 僅處理自製、無 records 夾具，不能當此遷移已完成。

原生 create/edit 仍使用既有 preview/confirm/history begin/end/abort。new 配到未用 ID 並二次核對；edit 明選 ID、保留分類/holes/未變邊 fixity。known failure 清候選可取消；confirm 或 rollback 回覆未知則保留 lease，由既有 receipt recovery 核實／回滾後才解鎖。owner 必須在所有 app native mutation、換案、保存、undo 和來源更換入口擋此 lease。

## 小 UI patch

`issue77-ui-integration.patch` 可在上述 main 執行 `git apply --check`。只供共享 owner 採用；沒有競寫實際入口。owner 安裝附件 validator/history hooks、configure callbacks 與 native metadata 同交易接口之後，才接此 patch。

patch 載入三個模組、路由逐點外環至 new/edit、保存阻擋草稿與未知交易、共用比例／對位、房間列表、明選改名／複核／unlink。進共享房間時收起原本自動辨識與舊來源列表，仍保留原校準／對位 controls。草稿提示依 new/edit 改寫，取消包括零點草稿，避免仍顯示「取代目前面」的舊引導。全房間 unlink 或 native delete 後的來源概覽／重新關聯入口需 owner 既有 project/source 概覽接線；不要為此建立另一套原生樹。

## 驗證與未完成項

`node --test tests/test_room_collection.js tests/test_issue77_attachment.js tests/test_issue77_workspace.js`：40 pass、0 fail、5 **明示 skip**。31 native/controller cases 真編譯執行 bridge；包含 new/cancel/replace、holes/fixity/kind、basis review、新 basis、rename/unlink/native delete、undo/redo、fresh native context、未知／錯 payload、各 late-context 時點與 owned preview。5 workspace tests 直接 VM 載現行 adapter，涵蓋 known fail、metadata rollback、lost rollback lease、configure 和禁止 private Map/history 存取；改回舊 cleanup 的 mutation 被抓到。

5 skip 等 `GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER` 映射 owner 的正式 registry/store/history：真 ZIP、未知 envelope/kind/schema/capability、原圖／native閉包、完整歷史、context/native commit 原子守門。不能將這五項當已通過。`tests/test_issue77_browser.js` 需明設隔離 URL 與 TEMP feedback；optional browser adapter 只映射測試接線，須報 provenance。實體 iOS／使用者本地未測、未啟動。

自製 PDF `tests/fixtures/issue77-two-rooms.pdf`，生成器 `tests/build_issue77_fixture.py`，600×400 viewport，A/B 分離矩形；200pt 校準為4000mm。SHA256 `7e63ee59ffafe7baed86847f849131f35baab4c9802679686351a8549cfd6e44`。沒有私人原圖。保存證據不得附帶使用者資產。

完整 #77 驗收仍需 owner 正式附件分支、adoptLegacySource records 保全／無 basis shadow、同交易 metadata、未知能力拒絕、actual ContextHistory 與 fresh-context browser 全部通過，再交 root review 決定合併。此獨立模組 PR 是可審小 slice；Refs #77，不關 issue。
