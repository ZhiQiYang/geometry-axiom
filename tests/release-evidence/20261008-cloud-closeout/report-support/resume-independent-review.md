# 完整安全 Resume 的獨立範圍審查

結論：既有授權足以繼續同服務 session 的安全續接工程，不需要使用者另定幾何公理。但目前不能把完整閉環限定為 `serve.py`、`reference-workspace.js`、`scenario-workspace.js` 三檔並排除 app/space owner。提案第 2 步的「每次修改前 durable 失效」尚缺與既有同步寫入介面相容的實作；這是具體產品工程依賴，不是手機、CI 或附件等外部驗收阻塞。單獨增加 status endpoint 只完成前置，不列作 Resume 成果。

本審查唯讀，沒有修改 repo、啟動 browser/native 或執行產品測試。2026-10-08T17:35:21Z 觀測本機 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`。上述三檔相對提案基底 `458779f003e1f57fdc0f4420564a0b295227843e` 無差異。完整命令、stdout/stderr、退出碼、檔案 hash 與行號摘錄在 `resume-independent-raw/receipt.json`。

## 已採納範圍與已交付部分

- 本輪使用者明列 #137 及後續恢復工作；`geometry-guide/IMPLEMENTATION-QUEUE-20261004.md:12` 已採納 A/B 完整獨立快照、B 不改 A、整體採用且可回復；:18 讓工程 owner 決定模組及測試方法。可決定内部 status 回應和有版本 epoch 協定；不可擴為任意跨專案合併或搬運舊 Undo。
- `geometry-web/docs/REFERENCE-PROJECT.md:96–99` 規定同服務 session、場景指紋、完整包核對後只恢復 metadata，不上傳 native；不承諾未套用工具草稿或較早 Undo、跨 profile/origin/服務重啟。`tests/INTEGRATION-GATES.md:373–402` 的現況「Resume 不可用」是現有保全 gate，不是永久禁止後續實作；unsafe 分支必須繼續拒絕。
- #137 已交付的 checkpoint、exact ticket、B namespace/lock、明確捨棄、Finish 收據屬既有基礎，不能重列為未接手。現有 `scenario-workspace.js:135–158` 保留非 retiring ticket，`reference-workspace.js:266–272` 明確保留 B 並阻擋未證明恢復；保留它們直到新協定可驗，不直接刪 guard。

## 無法由三檔 async 改動自行封閉的入口

1. `app.js:573–610` 的 `apiRequest` 同步呼叫 `assertEditable`、`tryLocalHistory`、`beginNativeOperation`，隨後送 fetch。`reference-workspace.js:36–40` 回傳同步 release callback，:658–670 的 local history 也在返回前完成修改。把 hook 改為 Promise 並不會讓現有呼叫者等待；甚至会破壞 release callback 型別。必須在 local Undo/Redo **之前**和任何 mutating request 發送前取得已提交的寫入資格，並於 await 後重核 context/session/操作歸屬。
2. `app.js:4858–4873` 底圖操作已先呼叫同步 `assertEditable`，才 `Object.assign(ul, changes)`，再呼叫 `changed`；:4938–4952 同樣先 guard，再直接改共用 `ul.mmPerPx`，再 `calibrated`。:10283–10299 的真 pointermove 使用此同步契約。這些不是當前 guard 旁路；但在 `changed()` 事後才排程 IDB 失效已太晚。需要在該共享物件首次修改之前完成 durable barrier；不能靠回滾、晚通知或每次要求使用者再點一次補順序。
3. `space-workspace.js:641/652/755` 同步 update/add/remove setter 返回後立即成功通知、清 draft 或 refresh。`evidence-links.js:115–131` 更明文要求同步原子 setter，拒絕 AsyncFunction 與 Promise，並要求最後 guard 到本地 history 修改之間不 await。不能僅將 reference 公共 setter 改 async；如增加 async 準備階段，須在它之前取得 durable permit，再保留原同步 commit 和最後 guard，並審其真正 caller。必要協調範圍至少 app/space owner 及該同步附件介面，不能預先宣稱只改三檔。

具體反例時序：B0 的完整包已存；使用者成功改模型名稱、底圖透明度或已記錄草稿，World 不變；600ms debounce 前 reload。舊 native 指紋仍相同，但旧 metadata 不再代表最新已確認 B。`reference-workspace.js:181–207` 只排程快照，且 IDB put 之後才判 stamp 是否變動；不能作新 Resume 的最新資格。現有安全 guard 正是在避免這種未證明狀態。

本次讀到的契約和三模組沒有既定同步 durable latch：`sessionStorage` 只保存 root recovery namespace key（reference:245–253）；嚴格持久 ticket 用 IDB `durability:'strict'` 並等 transaction complete（:1350–1374）。因此不自行引入 localStorage epoch 作為等價證明。只在 bootstrap 先永久標 unsafe 可以保全資料，卻不能證明後續完整 Resume；在 checkpoint 後立即 disarm 再開放編輯也不能宣稱普通中斷已有恢復資格。

## 可審查的最小完整工程切片

先由 root 與目前 app/space owner 確認不競寫，指定同一 writer 協調接口；提交前先寫明 epoch 狀態機與每個「可修改/已確認」線性化點，再做下列同一交付的相依步驟。

1. root-only exact tuple 的唯讀 resolve。讀既有 `editor_creations` 與 `scenario_contexts`、session、highwater 和 bridge 存活資訊，不能 create、close、ask native、改 highwater。`serve.py:525–540` close 已刪 UUID 記錄，只保留 scalar highwater；因此 unknown tuple 且 sequence ≤ highwater 只能誠實表示 absent/fenced，不能假稱有該 UUID 的歷史退休收據。此端點不能授予 metadata 恢復資格。
2. 有版本且有界的 B durable 資格/完整快照協定。舊 `scenario-editor-ticket/1` 的 `eligible:false`（reference:1302–1336）不得誤解為可恢復；舊包保留並拒絕。持同一 B 的 WebLock；成功寫入前先完成資格失效，失效失敗則 native 請求/metadata/history 都未發生。新 snapshot 與 exact ticket/context/epoch 必須一致提交；任何晚寫入或新修改不得讓舊 snapshot 重新 eligible。準備、提交、回覆不確定期都 fail closed，保留既有包與 native B。
3. 同 session/tuple/epoch、完整包、native 指紋與 owner 全部核對後做 metadata-only attach，重核 native 與 await 後歸屬，再由 scenario handshake 解除 inert/Finish。creating/initializing 沒有足夠一次初始化/完整 B 資格時繼續保留，不猜測、不重匯舊 catalog、不新配 B；active 也不可只看 World 相同。保留現有 retiring/Finish immutable receipt、較新 A 優先與 exact close 行為。

## 必要 oracle 與驗收邊界

- 服務 resolve 正反例：同 UUID/sequence/session 活 B；錯 session/錯 sequence/未知 UUID；closed/死亡 bridge；lost-create exact tuple。每次查前後 root/B dump、context 數、editor_creations、highwater、收據、子程序數全不變。不存在就不分配，不用 POST create 探查。
- 真 IDB transaction completion 被扣住、拒絕、quota/abort 或 reload 時，barrier 未提交前零 native 發送、零 metadata/history 修改、零成功 UI；提交之後仍要相同 context/selection/操作 owner 才可繼續。測 local Undo/Redo、底圖 opacity/位置/校準、模型 rename/add/remove、已記錄 assembly/engineering draft、feature attachment 等「World 相同但 metadata 不同」代表路徑。
- eligible B0 → metadata-only B1 → 在新 checkpoint 前 reload 的反例不得還原 B0。持舊 snapshot 寫入再允許較新修改，晚完成不能重新 eligible。若選擇拒絕，必須保留完整原包/B/ticket 並明示尚不能恢復；不把拒絕當 Resume 成功。
- 成功 Resume 從真 iframe/reload 和正常入口進行；對完整包（來源 bytes、模型、草稿、catalog、引用、dirty/saved）及 native dump 比對，HTTP 證明沒有 upload/reset/loadfile/create；新瀏覽器 token/較早 Undo 不作相等要求。錯 session、較新 B、另一 tab 持鎖、服務重啟、缺/corrupt package 必須拒絕且資料不變。
- Cancel/Finish 競態、lost replies、retiring 重入、A 較新 metadata 不被舊 Finish receipt 回滾；每 await 後核 owner。最後在实际整合候選以既有 lifecycle/workflow 真 IDB/WebLocks/browser gates 驗證，保留先前 guard 測試的 unsafe 分支與失敗輪。

目前 writer 釋放不能由歷史 queue 表或 PR headline 推定；#173 最近正文仍只是「草稿留給 dot 整合」，不是停止寫入/clean/檔案交接證明。root 正等 owner 回覆。本審查不以此擴大自己寫入權。解除本項產品依賴的明確下一步是 owner 交接上述同步入口並完成可審狀態機/接口 patch；status 可隨該 patch 做前置，不能單獨算完整收尾。
