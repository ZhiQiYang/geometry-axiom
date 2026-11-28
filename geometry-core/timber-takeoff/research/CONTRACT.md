# U476 S2 研究候選 API

固定基底為 PR #472 `19c00180228f6dfdff65684b47160736d2fae7e9`。指定條文已核可、S0 尚未落檔，因此本模組只供獨立研究執行，未登錄 `timber-takeoff-sets/1` 或 `cutting-plan/2`，不得被正式 App、project-store、capabilities 或切割入口 import。沒有修改公理層。

## 研究求值

`evaluate(data)` 接收 `U476-facts/1`，格式沿 L467 研究 facts：`context/endContext/current/representations/declarations`。`representations` 是明示研究來源宇宙，每列 `ref` 只是研究資料的索引；同件證據由 project scope、scenario、typed timber/placement 與 marks、雙內容 pin、完整 native content 提供。資料不是可由 UI 提交的正式核對證明。

新增必需欄位 `native.rootNodes`：

```json
{"timber":{"key":"timber:0","kind":"timber","id":0,"placed":true,"surface":0},"placement":{"key":"placement:0","kind":"placement","id":0}}
```

從真 native 投影時，必須先逐值驗 raw node 自己的 key/kind/id，再轉成上列數值 ID；不能只用 Map key 找到就當證明。所有納入表示和 current 根都驗。未知或缺失根回 `INCOMPLETE`。`definitionPin/effectivePin` 為非空 scalar string（有限 synthetic facts）或 `{timber,placement}` 兩個非空字串（真 native）；文件化保存只接受後者的 64 位小寫 SHA-256。

輸出 `U476-result/1`、`researchOnly:true`，欄位與 L467 相同。`MANUAL_GROUP_SOURCE_MISMATCH` 改列 `INCOMPLETE`，schema／partition／key 問題才是 `INVALID`。所有 member 都核對，不以代表遮蔽失敗；同源分列兩件維持 `DUPLICATE_SOURCE_NEEDS_REVIEW`。current 來源的 `native.readPin` 必須等於固定的 `context.liveReadPin`，即使本次只納入 model，仍不能混進另次 current read。非 COMPLETE/EMPTY 不產生部分 items。`raw = excluded + physical + removedAlias`。

CLI：`node candidate.cjs batch` 讀 stdin JSON array，輸出相同順序 result array。`evaluate` 模式讀單份 facts。

## 宣告的研究保存形狀

`document = {schema:'U476-study-document/1',projectScope,scenario,nextItemKey,items,excluded}`。`items` 每項 `{itemKey,members,representative}`；`members/excluded` 保存 descriptor：

```json
{"kind":"live","projectScope":"p","scenario":"s","timber":{"kind":"timber","id":0,"mark":"t0"},"placement":{"kind":"placement","id":0,"mark":"p0"},"definitionPin":{"timber":"64 lowercase hex","placement":"64 lowercase hex"},"effectivePin":{"timber":"64 lowercase hex","placement":"64 lowercase hex"}}
```

model descriptor 另加 `recordId,recordSha256`；live 不准有這兩欄。`representative` 是 `tupleOf(member)`：`[kind,recordId或null,'timber',id,'placement',id]`，無另一套 member id。`memberOf(row)` 由研究 facts 擷取 descriptor，沒有建立新來源證明。

`validateDocument(doc)` 回排序後的 canonical plain object；`serializeDocument(doc)` 回 UTF-8 Buffer，固定欄序、item key 數值序、live 在前，再依 model ID/typed root 數值序；末尾一個 LF。`parseDocument(bytes)` 接 Buffer 或 string，拒絕 duplicate JSON keys（含 escaped key）、非法 UTF-8、未知欄位/schema、非法 scalar、非 plain JSON、稀疏陣列及循環；容量是 64 item、128 表示（含排除）、8 model、128 KiB、4096 nodes、12 層。先驗有限 JSON，再驗 schema；壞輸入可先被較早容量守門拒絕。

保存只有宣告與 pins；沒有 A/B/L、COMPLETE、verified、authorization、token、採購或幾何副本。`evaluateDocument(doc,facts)` 重新對每個納入 descriptor 的完整 pins 與當輪 facts。document 明列本次範圍，未選 facts 不會自動成為待宣告表示。選定 tuple 有兩筆 facts 時回 `INVALID/DUPLICATE_REPRESENTATION_FACT`，不取最後一筆。納入表示缺資料時回 `INCOMPLETE/DECLARATION_SOURCE_MISSING` 且零需求；排除表示缺來源仍保留宣告，不重列成必需需求。excluded 不要求它的來源內容仍相同，但整份研究 `context/endContext` 仍須相同。

文件求值另回 `observation`：`scope:'available-declared-representations'`、declaredCount、observedCount、missingIncluded、missingExcluded、ambiguousSelected。其中 raw/excluded 長度只計當輪有原生數值的明選表示；來源缺失不捏造零長，清單仍列明。若納入來源缺失，physical/removedAlias 維持 null；不能把 raw 觀測小計冒稱整份定案料單。context 中的 attachmentPin/owner 等是研究輸入前提，沒有正式宿主發出的授權；保存文件本身及內容核對不代替產品 owner acquisition。

## 研究歷史

`new StudyHistory(doc)`、`StudyHistory.reopen(bytes)`；`view()` 回 `{document,revision,undoDepth,redoDepth,dirty,needsVerification:true}`。`begin()` 回 `{revision,document}` 暫存 draft，必須是同一 history 發出的物件；修改其 document 後 `commit(draft)`，或 `cancel(draft)`。commit 以 revision CAS 拒 stale draft。

新增 item 在 draft 用 `itemKey:null`，只在成功提交時配 key。既有正 key 必須仍在目前文件中；不能指定已退休 key 或自行配號。commit 原子驗整份，返回 `{changed,allocatedKeys,document,revision}`；失敗、取消、no-op 均零歷史變動與零配號。成功為一步 undo；新分支清除 redo。

`undo()/redo()` 回 boolean，每步復原內容但保留全程 allocator 高水位。`nextItemKey:0` 是永久耗盡。清空 items/excluded 表示刪除宣告，研究文件仍保留 allocator tombstone；不是正式 D51 附件刪除的產品接線。`save()` 只回保存 Buffer；`reopen()` 新歷史、無 COMPLETE cache。`evaluate(facts)` 純讀，不改 revision/dirty/history。

CLI `history` 讀 `{document,operations:[{op:'commit'|'cancel',document},{op:'undo'|'redo'|'reopen'}]}`，回 `{initial,steps,final}`。step 包含 op、ok、result 或 error code、view；拒絕不終止後續步驟。`history-batch` 對上述輸入陣列回結果陣列。

## T scaffold

baseline.cjs 有實體 module 與 evaluate API，對完整正例明確回 `INCOMPLETE/S2_NOT_IMPLEMENTED`。T 的 CT01 應在 `U476_CT01_EXPLICIT_ONE_ITEM` 斷言紅；不把 require/setup 失敗算成紅。其餘 API 只有同名尚未實作 scaffold。P 才替換為候選實作。研究來源、schema 和能力沒有在正式產品中啟用。
