# H-116-TIMBER/1 — R11 第二片 A 的原生操作契約

依據 issue #116 決策 6436163515、設計 6436046251 第 4–6 節與第 8 節；
基底為 `5c5700b5c151390f8f5c22a74655ee446ecfd2f0`。本 adapter 屬 H，
呼叫既有 K candidate/source 與 W 角材、工程來源、參照放置、支承及全域驗證。
它不新增 K/W 幾何規則，也不增加儲存檔能力或持久配方格式。

## 範圍與守門

同一原生專案 context、同一 boundary 面，單支普通已放置 D7 的複製／貼上／重複，
以及最多 64 支同面普通已放置角材的欄位批改。合法 timber id 與 placement id 包含 0。
更新只准明選 A、B、role、priority、direction；省略的定義保持各自原值。
批改不允許修改錨點、側向、存在身份或放置順序。

原生從目前 World 檢查存在、普通 D7、已放置、同面、assembly ownership 與已支援
placement discriminator；任一不適用，整筆拒絕。客戶端不能用 eligible、owner 或
groups 旗標覆寫判定。這個固定基底沒有 #335 群組資料模型，因此 `groups:[]`、
`groupsKnown:true` 表示原生已知本版 World schema 無此類群組記錄，不表示支援群組
複製。未知請求欄位、未支援物件及未知定義必須拒絕；加入群組模型時須升級此守門，
不能把 group 當 owner，也不能據本契約允許任意子圖、跨面、跨專案。

基底未提供 D60 incarnation ledger；本片保留既有 timber/anchor record slot、id、
放置 order，使用完整 revision 與同一 sealed candidate 守護，不宣稱新增 incarnation。

## 傳輸與容量

`POST /timber-edit/read` 與 `POST /timber-edit/preview` 接完整 UTF-8 JSON，
最多 1 MiB。拒重複 key、未知欄位、NUL、字串控制字元、重複目標及超額操作。
Python transport 建立服務擁有的暫存檔，送 `timber-edit-read <path>` 或
`timber-edit-preview <path>`，在 finally 移除；外部 JSON 不接受檔案路徑。
原生再次做完整 schema 與語意檢查，Python 不計算來源值或幾何。

`expectedRevision` 與回覆 revision 都是 canonical uint64 十進位字串，
不是 JavaScript Number。0 與 18446744073709551615 都可解析；數字型、正負號、
前導零、溢位皆拒絕。若原生 revision 已達上限，拒絕會遞增的提交，不回繞。

## 唯讀取得

```json
{"schema":"timber-edit-read/1","boundaryId":1,"timberIds":[0]}
```

回覆 `schema:"timber-edit-read-result/1"`、`revision`、`contextKey`、
`boundaryId`、`maxOperations:64`、`eligible`、`reason`、`timbers`、`recipeKey`。
`contextKey` 是每個 bridge 啟動時產生的隨機 64 hex 識別；只有一支適用角材才取得
獨立隨機 recipeKey。配方最多保留 64 份；最舊可被逐出，失效必須重新讀取。
亂數失敗直接拒絕，不退回時間或可預測計數器。

每個 row 含 id、eligible/reason、typed owner、groups/groupsKnown、placed、
以字串表示的 placementOrder、definition、effective 與唯讀 geometry。
definition.A/B 各為下列一種，兩者不是等價定義：

```json
{"mode":"direct","value":27}
```

```json
{"mode":"source","source":{"kind":"parameter","parameterId":10,"fieldId":5},"override":null}
```

source 沿用既有 literal/spec/material/application/parameter 型別，完整保存 material
id/version/field 或 parameterId/fieldId；override 必須明示 null 或既有合法來源。
effective.A/B 只供顯示，不可用來反推 source。definition 另含 role、priority 與
placement `{on,anchor,selector,direction,side}`；錨點文字直接序列化已存參照，
不從幾何重建。衍生長度、頂點與軸向不屬於可重用定義。

`definition.priorityText` 永遠提供 canonical 正 int64 十進位字串，是 UI 顯示、比較
與編輯優先級的權威值。既有 `priority` JSON 整數保留作相容投影，瀏覽器不得拿它
還原大整數。fields.priority 接受既有正 int64 JSON 整數或 canonical 正 int64 字串；
UI 一律送字串，範圍 1..9223372036854775807。priority 是 D15 的比較序，不能套用
尺寸的座標上限。舊資料若缺 priorityText，只能接受安全正整數；超出安全範圍須守門，
不可悄悄四捨五入。opaque 原生 recipe 保留完整 int64，與顯示投影無關。

讀取不改 World、history、dirty、revision 或既有 pending。配方只保留 A/B 的
typed 定義與 override、role/priority，以及 context/revision/面綁定；不存原物件 id、
owner、incarnation、長度或幾何。Undo/Redo 即使回到相同 dump，revision 仍不同，
舊 recipe 必須失效；另一次 process 啟動也不接受舊 key。

## 預覽

```json
{"schema":"timber-edit-transaction/1","expectedRevision":"15","boundaryId":1,"operations":[{"op":"update-timber-fields","id":0,"fields":{"A":{"mode":"direct","value":29}}}]}
```

create transaction 只容許一個 `create-from-recipe`，不得混入更新：

```json
{"op":"create-from-recipe","recipeKey":"<原生 64 hex key>","placement":{"on":0,"anchor":"at-face e2","selector":"","direction":"+u","side":"+n"}}
```

使用者必須明選合法落點；不複製原位置、不自動偏移。anchor 恰為一條既有 at-line
或 at-face 子句，selector 為空、through 或 between 子句。拒絕控制字元、尾隨指令
與跨面 placement。使用既有完整 placement parser 與幾何驗證。

批改先解析所有 patch、檢查所有目標，在同一 AppWorldCandidate 中依次寫入全部
明選定義，最後才呼叫一次 world_revalidate；不走逐支 delete/recreate 或逐支提交。
明選 direct 只移除該欄位自己的工程綁定；其他欄位來源不動。明選 custom role
須同時提供正整數 priority；離開 custom 恢復該普通 role 的既有優先級。

回覆 `ok:true, preview`，包含 schema、token、valid、revision、noOp、before/after、
changes、dependencies.timbers/guides 及 violations。有效且完整定義相同時
`noOp:true,token:null`，不建立新 pending、不提交、不增 history/revision。
相同有效值但不同 source identity 是真正變更。

新物件預覽使用 `handle:"new:0"`。候選內只用私有數值索引進行原生計算；正式 World
與配號不變，after/changes/diagnostics 不對外露出此數值作為新正式 timber id。
既有依賴維持自己的正式 typed id。真正成功發布時才回傳新增正式 id 映射。
uint32 配號回繞必須跳過所有已存在 id，包括 0。

語法/適用性/stale 錯誤回 ok:false，完全不建立新 pending；幾何錯誤回
ok:true、valid:false 及自己的 token，保留完整候選違規供檢閱與取消。
共用 preview slot 仍由現有候選系統持有，前端必須持有全域 workspace lease，
不讓其他寫入/預覽穿越不確定結果；read/no-op 不取消他人的 pending。

## 確認、取消與 requestId

`timber-edit-confirm <token>` 只接受 timber family 的當前有效 token，重新檢查
revision、target eligibility、candidate seal，重驗原候選後記一次 history、發布一次、
revision 加一。失敗原 World 不動。成功回 history_changed、revision、before_revision、
transaction_id、changedIds，以及 created 的 `{handle,kind:"timber",id}` 映射。
再次確認同 token 不會重做。成功後若要 Repeat，先讀取成功新增 id 取得新 baseline 的
recipeKey；不得把一次批改當作上次新增動作。

`timber-edit-cancel <token>` 只取消自己同 token 的 pending。engineering、assembly、
section-profile、panel-fill 與一般 line confirm 都不能借用 timber token；反向亦同。
一般無 token 的 line cancel-preview 不能取消 timber pending。

確認使用既有 `/api` requestId/receipt transport。app.js 必須把 timber-edit-confirm
列入既有寫入與 requestId 流程；ReferenceWorkspace 持有確認 lease，ContextHistory
觀察同一成功提交。掉回覆時只用原 requestId 查 receipt，不能重送確認或以畫面猜成功。
配方、剪貼簿、未確認候選及 repeat 記錄皆不寫入 .gcanvas。

## 驗證界線

`tests/test_timber_edit.py` 是真 bridge 具名測試，包含私有預覽資料與 uint32 回繞。
`tests/mutate_timber_edit.py` 在隔離 source copy
逐案編譯 -O0 ELF，僅把對應具名斷言失敗列為 kill，並還原 bytes、重編、重跑綠。
編譯失敗、崩潰、無關失敗、error、skip 都不是 kill；收據包含 source/ELF/判準雜湊。
正常產品另以 -O2 編譯並執行全部具名案例。真 UI/CDP、WSL、本機完整 canvas golden
應依實際各自收據報告，這份契約本身不代表任何測試已通過。
