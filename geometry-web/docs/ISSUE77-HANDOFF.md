# #77 人工多房間切片：模組與 owner 接線交接

範圍依使用者接受的第 8 項明文建議及 PR100（`0230e436870ec3ba06fcb0735ffabc3b7427979d`，已隨 main `b3c210791d128dc84c3222078df2472b70cc0e60` 合併）。PR 分支已整合實際遠端 main `067cbdc08340536eaf1a2ec96cf923e7682a9afe`；下方記錄 exact-base 驗證。只有人工連續描房；沒有批准整包 Q37 舊 proposal、原生房間樹、3D parent、自動 transform 或 #54/#87 自動辨識。原生 geometry 唯一來源仍為 native boundary。此 PR 沒有修改共享 app、index、project-store、reference-workspace、ContextHistory 或格式號，不能單獨宣稱 #77 已在產品啟用。

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

共享底圖不顯示舊版「移除目前底圖」；`feUnderlayRemove` 與公共 `ReferenceWorkspace.remove` 均拒共享房間，使用房間列表 unlink。全域匯入 modal 排除共享房間作舊參考頁 target，applySource/addPage/selectPage 提交前也守門；其他普通面仍可匯入／顯示新來源。第三步直接開人工 new-room draft，沒有走 RoomOutline 自動辨識。Back／Esc／離開描繪工具完整取消房間 intent；未知 native 結果則保持 lease 和可恢復入口，禁止離開。receipt settlement 先清整份 room UI draft/候選、切回 select、重繪，再解鎖，避免 New B points 被下一次 Finish 當成 A 的 ordinary replacement。

## 驗證與未完成項

`node --test tests/test_room_collection.js tests/test_issue77_attachment.js tests/test_issue77_workspace.js` 最新 review 修正：41 pass、0 fail、5 **明示 skip**（46 tests），log `/tmp/issue77-review-final-test.log`。原 ce72adb 的 40 pass/5 skip 保留不覆寫。31 native/controller cases 真編譯執行 bridge；包含 new/cancel/replace、holes/fixity/kind、basis review、新 basis、rename/unlink/native delete、undo/redo、fresh native context、未知／錯 payload、各 late-context 時點與 owned preview。6 workspace tests 直接 VM 載現行 adapter，涵蓋 known fail、metadata rollback、lost rollback lease、UI 退休先於解鎖的順序、configure 和禁止 private Map/history 存取；改回舊 cleanup 的 mutation 被抓到。

5 skip 等 `GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER` 映射 owner 的正式 registry/store/history：真 ZIP、未知 envelope/kind/schema/capability、原圖／native閉包、完整歷史、context/native commit 原子守門。不能將這五項當已通過。`tests/test_issue77_browser.js` 需明設隔離 URL 與 TEMP feedback；optional browser adapter 只映射測試接線，須報 provenance。實體 iOS／使用者本地未測、未啟動。

### 五項 skip 逐項查核（不是 native setup 缺失）

原始 exact-head `ce72adb` 結果留在 `/tmp/issue77-final-test.log`：45 tests＝40 pass、0 fail、5 skip，不覆寫。再次唯讀核對遠端 main `b3c2107`、owner docs branch `f04c758e`、PR102 `ce72adb`，三者的正式 project-store/reference-workspace 均無 featureAttachments registry、source-rooms registration 或 read/setFeatureAttachment；所有遠端 heads 未見正式附件產品實作分支。Node v24.19.0、WebCrypto、vendor fflate zip/unzip 均可用；31 native cases 的 before hook 真 GCC 編譯並執行 bridge，沒有 native skip。四項純 payload/refs/pins tests 無條件執行。

以下全部屬完整 #77 **必須完成**的跨 owner 整合驗收，沒有從批准範圍排除。不能補一個自行序列化的假 owner adapter，或使用退役 dedicated prototype，把它們變成正式 pass。

| 完整測試名稱 | 現在未跑的實際依賴 | 何時可跑 |
|---|---|---|
| `registered attachment roundtrips true ZIP and original PDF exactly once` | 正式 source-rooms registry、owner envelope 格式及 pack/unpack dispatch 未實作；ZIP 函式庫本身可用。 | owner 註冊本 payload validator/capability/references 並接正式 pack/unpack 後，用 test-only shim 映射 `register/manifest/attachment/pack/unpack`。 |
| `owner registry rejects unknown envelope version, kind, schema and capability without dropping data` | 正式 envelope／有限 kind whitelist／payload schema／frontend capability 守門未實作，不能只測 payload validator 冒充整份包守門。 | 上項可 roundtrip 且 owner 可拒 unknown/missing/duplicate 六種 manifest 反例後，以 `corrupt` 只改真格式欄位來驗。 |
| `generic owner source closure and native final-object hooks validate room payload` | owner 未把 SourceRooms asset refs 和 native final-object validator 接 pack/import；獨立模組相同正反例已跑。 | registry 的 references 用於來源閉包、正式 `validateProjectObjectRefs` 等 dispatch 可接 source-rooms validator 後，映射 `validateNativeRefs`；candidate pins 原子守門另外仍要前述 native 摘要。 |
| `owner attachment snapshots survive rename unlink native delete same-ID undo redo and unknown history` | 真 ContextHistory 尚無此附件 snapshot/restore/native-delete/unknown-history hooks；本模組控制器的真 native + 模擬 metadata timeline 已跑，不能代替實際 history。 | owner 接 immutable attachment snapshots、local/native 單步歷史與 lifecycle hooks 後，`verifyHistory` 必須執行真 ContextHistory、檢查完整附件復原。 |
| `owner workspace guards exclude late-context writes and pair room metadata with native transaction` | 正式 read/setFeatureAttachment context token/busy/lease 與同 native history 寫入未實作；VM 薄 adapter 的 unknown rollback 回歸已跑。 | owner 公布正式 read/set、configure callbacks 和 native 同交易 metadata 語義後，`verifyWorkspaceGuards` 執行真 ReferenceWorkspace，而非替身 store。 |

正式 owner code 到位後，worker 可在隔離 checkout 合入 owner exact commit，再提供 **只轉呼叫真 owner code** 的 test-only adapter，執行 `GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER=/absolute/path/adapter.cjs node --test tests/test_issue77_attachment.js`。環境變數現在缺省只是這五 gate 的可見開關，補變數不能補不存在的產品 API。已配置 adapter 若不存在／缺方法／方法失敗，測試直接 fail，不會 skip；註冊資料現在也明寫 `kind:"source-rooms"`，減少未来 mapping setup 歧義。

最新 TEMP Chromium 測試：37 assertions pass，1440×1000／390×844，實際 pointer 描房、零點取消、pending save 拒絕、new 保留 A、明選 edit、rename/undo、basis review、明選逐房複核、新 basis 房、真 ZIP 別的 browser context 重開、unlink/undo，console/pageerror 為空。整份 prototype manifest 無所選來源舊 basis shadow、PDF asset 只有一份。當時 `/runtime` fresh=true，root `/tmp/issue77-integrated`，版本 `30b7edfcdf7d3eecfbd4caebc7f72c960e90c0ec513dfd6ddfa4c740c9f2f269`；test-only shim `/tmp/issue77-browser-owner-adapter.js` 映射已退役 dedicated prototype store 加 configure callbacks。這些結果只證明目前模組與 UI 接線可運作，不證明 PR100 generic store 支援或有 records 的舊頁遷移。截圖 `/tmp/issue77-browser-evidence/desktop-two-rooms.png`、`mobile-room-list.png`；含自製夾具，無私人圖資。

程式與文案 diff whitespace 檢查通過；PDF xref 的標準 20-byte records 必含行末空白，unified patch 的空 context 行也必含一個前綴空白，這兩個 artifact 不以移除空白修飾。PDF deterministic byte check 與 main patch apply-check 另驗。

新增 review 回歸：`tests/test_issue77_remove_browser.js` 真 UI 21 assertions pass，adopt 時保留兩張不相關自製 legacy PDF 與兩份 records，實際 stale 舊移除按鈕及 public remove 都不刪資料；真 ZIP 保留 records／無所選 source 的 basis shadow；全域 file chooser/import modal 排除 shared target，強塞舊 target 拒寫，普通面仍正常匯入。禁用 shared-room guard 的記憶體 mutant 在 stale-button 後精確因 legacy-0/record 消失而 fail，log `/tmp/issue77-remove-mutant.log`；不是將錯誤輸出改成 expected。

`tests/test_issue77_exit_browser.js` 真 UI 61 assertions pass：Back／Esc／V 各零點與四點，pending 跨面拒絕，退出 intent/lease/points 全退、真 ZIP 可保存、再開其他面沒有沿用草稿。TEMP viewport 1440×1000，截圖 `/tmp/issue77-exit-browser-evidence/`。這些測試仍使用明示 prototype adapter，不能代替前述正式 owner 五 gate 或所選頁已有 records 的遷移驗收。

`tests/test_issue77_recovery_browser.js` 真 UI 71 assertions pass：history-begin／confirm／history-end／cancel-preview **確實 native 執行**後丟失 reply，第一次自動 receipt 也不可用，再按真 connectionRetry 從既有同 requestId receipt 核實，沒有重送 mutation。unfinished group rollback；successful history-end 保留独立 B。所有恢復先清 points/preview/drag/typed/panHold/newOutline、關自己 dialog、切 select、重繪，再釋放 lease。恢復後真 Finish／Enter／feDraftTryClose 不修改 A 或 B，fresh new/cancel 仍可用且 known cancel 回 select。桌面 1440×1000／390×844，無 page/console errors；截圖 `/tmp/issue77-recovery-evidence/`。舊 async continuation 使用捕獲的 operation/dialog，instance/generation/context token 變更後不清新草稿或搶另一案焦點。

最後將固定新版 module 複製至隔離 `/tmp/issue77-integrated`，port8819 `/runtime` fresh=true，版本 `402e4dd04820e4ffa614be20f281997ffe0f87a666d006b349ba27b83e2c8dab`；原流程／多legacy刪除／退出另依序復跑，結果存 `/tmp/issue77-review-browser.log`、`issue77-review-remove.log`、`issue77-review-exit.log`。這仍是 TEMP owner adapter 的接線證據，不把任何正式保存 gate 的 skip 算 pass。

自製 PDF `tests/fixtures/issue77-two-rooms.pdf`，生成器 `tests/build_issue77_fixture.py`，600×400 viewport，A/B 分離矩形；200pt 校準為4000mm。SHA256 `7e63ee59ffafe7baed86847f849131f35baab4c9802679686351a8549cfd6e44`。沒有私人原圖。保存證據不得附帶使用者資產。

## main 067cbdc 的模組合併交付

root 已獨立 review `18ba1f859f8866ad43bbe520140f7efec24a1c71`，清除移除底圖、退出草稿與 receipt recovery 三項阻塞，並授權先合併獨立模組，由 root 執行 merge。`git ls-remote` 後 fetch 的實際 main 是 `067cbdc08340536eaf1a2ec96cf923e7682a9afe`，不是以訊息中的簡碼猜測。b3c2107→067cbdc 僅新增 14 個 rule_cases 模組／文件／測試檔，與 #77 的新增檔完全不交集；共享 web 入口、正式 store/history、native bridge 與核心來源沒有變動。

合入 main 後重新執行 focused suite：46 tests＝41 pass、0 fail、5 owner-interface skip，log `/tmp/issue77-main067-focused.log`。上述五項 production owner gates 仍明文未完成，實際正式 registry/read/set/history/lease 接口仍不存在；不是測試環境阻擋。另驗自製 PDF deterministic bytes、JavaScript syntax、patch 對當前 main apply-check 與所有既有檔案 blob 相等；證據 `/tmp/issue77-main067-evidence.json`。

這次 base 整合沒有改動三個房間模組、接線 patch、browser test harness 或 native/web 依賴 blob；現有 37＋21＋61＋71 TEMP browser assertions 的 provenance 保留在各原始 log，沒有將它們重標為新 head 的重新執行結果。未啟用 production UI，因此不為不相干 rule_cases 新增檔重跑 full CDP。若 owner 接線改動上述依賴，須在其整合 exact head 重跑正式 UI／保存驗收。

此獨立模組 PR 可交 root 合併；Refs #77，不關 issue，也不開 production 入口。完整 #77 驗收仍需 owner 正式附件分支、adoptLegacySource records 保全／無 basis shadow、同交易 metadata、未知能力拒絕、actual ContextHistory 與 fresh-context browser 全部通過，再交 root review 確認產品啟用。
