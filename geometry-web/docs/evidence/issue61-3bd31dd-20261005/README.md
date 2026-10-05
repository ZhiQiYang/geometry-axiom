# #61 第一正式規則 UI 切片驗收證據

實測產品 head：`3bd31dd4728dfac4b90d1ca96f17e47880018ac5`；tree：`f254ed11e07e6d5ab03d6ad00802fad5a1889958`。
Draft [PR133](https://github.com/ZhiQiYang/geometry-axiom/pull/133)，未 ready/merge。後續證據 commit 只更新 slice 狀態文件及此目錄；沒有宣稱 full 在證據 commit 重跑。runtime/source Git blob 等同性見下列收據。

可直接看 [精確總收據](receipts/summary.json)、[正式 /13 reader 34 項](receipts/reader.json)、[正式 #48 app 110 項](receipts/formal48.json)、[runtime](receipts/runtime.json)、[source 等同性](source-equivalence.json)、[ZIP／日誌 provenance](artifact-provenance.json) 及 [MANIFEST.sha256](MANIFEST.sha256)。原收據保留執行時 TEMP 路徑，實際交付產物以此目錄的相對連結取得。

- [桌面真候選摘要](screens/rule-editor-desktop-preview.png)、[桌面 raw 重開](screens/rule-editor-desktop-restored.png)、[390 raw](screens/rule-editor-390-raw.png)、[390 真重開](screens/rule-editor-390-reopened.png)。
- [edit orphan 恢復](screens/rule-editor-orphan-edit.png)、[delete orphan 恢復](screens/rule-editor-orphan-delete.png)：遺失來源明示，原 pin/raw 保留，發布與輸入唯讀，真保存／返回／明確捨棄可用。
- [桌面实际 Save ZIP](archives/rule-1280.gcanvas)、[390 实际 Save ZIP](archives/rule-390.gcanvas)、[edit orphan Save ZIP](archives/rule-orphan-edit.gcanvas)、[delete orphan Save ZIP](archives/rule-orphan-delete.gcanvas)。
- [合法 /13 共存 ZIP 的实际 Save](archives/reader-accepted-reader13.gcanvas)、[自製 /13 reader 夾具](archives/reader-authored-reader13.gcanvas)。只有 raw/native/evidence 和 repo-authored PDF；原 PDF bytes 閉包及模型集合都保留。
- [非空模型／投影原 Space UI Save](archives/model-original-space-ui.gcanvas)、[衍生 /13 fixture](archives/model-plus-rule13-fixture.gcanvas)、[实际 /13 重新 Save](archives/model-rule13-actual-ui-save.gcanvas)、[4 項逐值收據](receipts/model-collections.json)、[原 supplemental harness](supplement/model-collections.cjs)。實際含 1 個模型及 1 個投影，完整值相同；不只檢查空集合。
- [四種拒絕及合法讀取原收據](receipts/reader.json)、[缺 canonical](screens/reader-missing-canonical.png)、[能力不符](screens/reader-capability-mismatch.png)、[snapshot 不完整](screens/reader-incomplete-snapshot.png)、[pin 非法](screens/reader-invalid-pin.png)。都是正式 file chooser 和真 native prepare；負例只竄改 detached 回覆 metadata。
- [修前重現](before/README.md) 包含原 main 缺口與 `0844b58` 的兩個 review blockers。舊 head 的 full 不算修後通過。

| Gate | 實際結果 | 原始收據 |
| --- | --- | --- |
| strict aggregate | 68 suites；2157 pass／0 fail／1 具名 Windows GDI on Linux 豁免；Node510；exit0 | [日誌](logs/aggregate.log.gz) |
| 無 scope full CDP | 2054 assertions／83 段 golden matched；0 fail／0 skipped groups；P87=60、舊82段不變 | [總收據](receipts/summary.json)、[日誌](logs/cdp.log.gz) |
| 正式 /13 reader | 34/34，4 個非法候選零 confirm，各 cancel1，World/context/raw/history frame 不變；合法共存真 ZIP Save | [reader](receipts/reader.json)、[日誌](logs/reader.log.gz) |
| /13 非空模型／投影實際 Save 補驗 | 4/4，同 head Space 实际 ZIP → /13 真 chooser → Save，完整模型／投影逐值相同 | [收據](receipts/model-collections.json)、[日誌](logs/model-collections.log.gz) |
| 正式 #48 evidence app/native/PDF/ZIP/history | 110/110，1280/390、DPR2 | [formal48](receipts/formal48.json)、[日誌](logs/formal48.log.gz) |
| grid portable／first-pointer | 91／243，均零失敗或未捕捉例外 | [portable](receipts/grid.json)、[first-pointer](receipts/grid-interaction.json) |
| full-space-suite | 202/202，0 unexpected exceptions/console errors | [space](receipts/space.json)、[日誌](logs/space.log.gz) |
| 正式 #77 owner adapter／scenario actual owner | 5/5／1/1，無缺注入 skip | [owner](receipts/owner.json)、[owner 日誌](logs/owner.log.gz)、[scenario 日誌](logs/scenario.log.gz) |
| #77 main／exit／recovery／remove | 37／61／111／46 | `logs/issue77-*.log.gz` |
| independent evidence adapter | 67/67，injected-memory backend，不當作正式 ZIP | [日誌](logs/adapter48.log.gz) |

P87 是正式空白來源建立、all-cells／signed cell CRUD、真點主格及明選、native 取消/拒絕、改名/刪除/高水位、>2^53 原字串、undo/redo、native/history/context 延遲 race、未 blur 無效 raw、实际 Save/new empty context/open，包含正常來源卡片刪除後 orphan 續編；orphan 部分不使用 fixture API 或 renderObjects 補狀態。其他 P87 stale-source 案的 API 變更只是明確測試 fixture，不放寬產品拒絕。raw 不留正式 key/token；一次 native 確認與移除 raw 共用 ContextHistory 一步。

四個 reader 負例各以不同的真目前專案證明原狀保留，並非只回到空場景。finite formatPolicy 在共同 store 定義、正式 reader 三處使用，/11–13 的 canonical scene／native capability／evidence snapshot 和 pin 守門一致；合法歷史 pin 的 definition 差異仍沿既有 needs-reassociation 語意。非瀏覽器 runner 對新 reader 的「injected-backend」行是既有通用標籤；本 gate 是真 native/app reader，僅負例 detached metadata 由測試注入，具體以 reader 原收據為準。

數量都是 assertions，不是端到端 scenario 數。CDP exception counter1 是原 P38 故意注入 `fb-auto-probe`，unexpected exception0。Space full 明確省略 timber-material/timber-source-guards。SR24 實體手機、Windows/iOS、IME、OS chooser／下載位置仍人工未驗；390 Chromium 不冒充實體手機。

本切片支援雙無 stagger REPEAT 的 source rules；不含 REPEAT_PANEL/缺軸/finite/stagger 自動轉換、nested/override、自動生成、子線 display/pick、RuleLineRef、guide/direct、跨面完整正常流程或 durable identity ledger。未修改 SSOT/native C，不关闭 #61/#62/#57。完整 SR01–23 對照見上層 `ISSUE61-SLICE1-20261005.md`。

遠端 [Actions run37289563849](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37289563849) 七 jobs failure；native steps空、授權 log fetch回404 BlobNotFound。原因未定位，[原 CI 收據](receipts/ci.json) 保留。本地通過不等於 CI 綠燈，parent 獨立 review／合併仍未完成。

所有資料 synthetic/repo-authored，圖片未編輯，日誌 gzip 解壓後逐位元相同。沒有 private PDF、credential、feedback目錄、profile/storage、executable、DOM dump 或部署。執行 `sha256sum -c MANIFEST.sha256` 可核對全部檔；`gzip -dc logs/cdp.log.gz` 可讀完整原日誌。source-equivalence 記 runtime footprint 的逐檔 Git blob/bytes/hash，本證據目錄及 slice 狀態文件不屬 runtime/static route；後續 evidence head 保持同一產品 bytes。重跑環境和 gates 見 `tests/INTEGRATION-GATES.md`。
