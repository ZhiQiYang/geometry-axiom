# #48 可讀取驗收證據

此目錄只保存已完成的合成驗收產物，不修改產品、測試或驗收契約。
實測產品 head：`34a62225aefc9986c12b3f2582fa558cf523bedf`；tree：`fb87229fbdd94163718406be6a59467c90174da6`。
證據 commit 的新 head 可由 PR #132 取得；沒有宣稱 full suite 在證據 commit 重跑。

## 直接檢閱

- [精確總收據](receipts/summary.json)、[110 項正式 app 收據](receipts/formal.json)、[runtime 收據](receipts/runtime.json)。所有原收據逐位元保存，絕對 TEMP 路徑是當時的執行 metadata，實際產物在此目錄的相對路徑。
- [1280 正常覆核](screens/1280-evidence.png)、[390 正常覆核](screens/390-evidence.png)：圖面原文 `915/2`、現場量測 `460.125`、native `915/2` 分開顯示；HTML 字串僅作文字。
- [1280 新 context 重開](screens/1280-reopened.png)、[390 新 context 重開](screens/390-reopened.png)、[390 shared-source 人工重綁與覆核補圖](screens/390-shared-evidence.png)。補圖上方保留重開時的短暫 toast，沒有修改圖片；表單反映測試後期 native 值 `459`。
- [1280 實際下載 ZIP](archives/1280-full.gcanvas)、[390 實際下載 ZIP](archives/390-full.gcanvas)；`archives/` 另有 evidence-only、core-only fallback undo/redo、shared-source 與缺失 target 的真下載。`reject-*` 是刻意非法的拒絕夾具，不是正常可開啟的專案。
- [原缺口說明](before/README.md)、[source/Git blob 等同性](source-equivalence.json)、[ZIP 內 PDF 與原日誌 provenance](artifact-provenance.json)、[檔案 SHA-256](MANIFEST.sha256)。

## 實際結果與界線

| Gate | 結果 | 收據 |
| --- | --- | --- |
| strict aggregate | 68 suites；2144 pass / 0 fail / 1 具名 Windows GDI on Linux exemption；exit 0 | [壓縮原日誌](logs/aggregate.log.gz) |
| 正式 evidence app / native / PDF / ZIP / history | 110/110；1280 和 390 CSS px、DPR 2 | [formal.json](receipts/formal.json)、[日誌](logs/formal.log.gz) |
| 無 scope full CDP | 1994 assertions，82 golden 段 matched，0 fail / 0 skipped groups；P70=113，P78=23 | [summary.json](receipts/summary.json)、[日誌](logs/cdp.log.gz) |
| full-space-suite | 202/202；0 unexpected errors/exceptions | [space.json](receipts/space.json)、[日誌](logs/space.log.gz) |
| 正式 owner adapter | 5/5 | [owner.json](receipts/owner.json)、[日誌](logs/owner.log.gz) |
| independent evidence adapter | 67/67，injected-memory backend，不能用來宣稱真 ZIP | [日誌](logs/adapter.log.gz) |
| grid portable 真 app / ZIP | 91/91 | [grid.json](receipts/grid.json)、[日誌](logs/grid.log.gz) |
| scenario / grid actual-owner compatibility | 1/1，無缺注入 skip | [日誌](logs/scenario.log.gz) |
| #77 main / exit / recovery / remove | 37 / 61 / 111 / 46 全通過 | `logs/issue77_*.log.gz` |

正式 gate 包含手動框選與欄位選擇、覆核、重新綁定、受防護雙向定位、真下載與 chooser、新空白 context 重開、history，以及取消/延遲/換頁/換 context/native/history/navigation race、target 刪除與 ID 重建、PDF 更換、未知格式/容量等拒絕。正常 native 更新透過原事件自動刷新同一 host，沒有測試強制 UI.refresh。
PDF Worker 每個 viewport 的真 gate 都是 created 4 / terminated 4，原 live reader 與 recovery 可用；VM 另驗成功/拒絕/取消/load failure 清理。

CDP 的 exception counter 1 是原 P38 刻意注入 `fb-auto-probe`；unexpected exception 為 0。full-space-suite 明確不包含 `timber-material` 與 `timber-source-guards`，不宣稱驗過這兩組。Mutation 日誌是既有結果 freshness check，不是新執行 mutation。Linux 平台豁免與實體 Windows/iOS/OS chooser/IME 未驗界線保留；390 Chromium 不冒充實體手機。

## 遠端 CI 阻擋

[Actions run 37274967780](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37274967780) 七個 jobs 皆 failure；native steps 空白，authorized connector 取日誌回 `404 BlobNotFound`，原因未定位。[ci.json](receipts/ci.json) 保留原結果。本地通過不等於遠端 CI 綠燈；PR 仍 draft，未 ready/merge。

## provenance、安全範圍與再核對

所有 PDF bytes 都來自實測 head 的 `geometry-web/evidence_links_integration_test.js` 裡 `fixture()`，唯一內嵌 PDF SHA-256 為 `a6f4a233d5c7b9a2483068313c45f049e2fea4166856305563798fbb52fd7b43`（1713 bytes）。ZIP 內的 native 場景與標註都是 synthetic；沒有私人 PDF、原始設計、credentials、feedback 目錄、瀏覽器 profile/storage、二進位 executable 或 DOM dump。
原日誌 gzip 解壓後與 TEMP 產物逐位元相同，hash 記於 `artifact-provenance.json`；圖片未編輯。`MANIFEST.sha256` 涵蓋除此 manifest 自身以外的所有證據檔案。

在此目錄執行 `sha256sum -c MANIFEST.sha256` 可驗內容；`gzip -dc logs/cdp.log.gz` 可讀原日誌。父任務可用 `git diff --name-status 34a62225aefc9986c12b3f2582fa558cf523bedf HEAD` 確認只新增本目錄。384 個 runtime source 的目前 bytes 已逐一等於實测 Git blob；fingerprint 仍是 `ac7297450636f6f2836eb171faf3c54628e4f7235db9c40ff03ccab50bfdbb25`，此 docs 目錄不納入 runtime 或公開 static routes。

重跑命令與必要環境沿用 `tests/INTEGRATION-GATES.md`。本次只驗證證據內容、Git blob 與 fingerprint，不重跑相同 full suite；工作區保留，未開始 #61。
