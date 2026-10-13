# 新交付唯讀契約審查

核對時間及 Git 原始命令／stdout／stderr／exit code 見 `report.json`、`read-command-receipts.json`。此次只讀 Git objects、AST 與收據；沒有執行 native／browser，沒有改 repository 或已凍結 private browser probe。核對時整合 HEAD `9a4136da264249f76ba08258a7f14be926f96a95`，工作樹乾淨。

來源：

- #171 舊 `821618fdf96cd54b9452806bc3ab94f4da29854d` → 新 `fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d`。
- #174 合成重開交付 `b0ef9bcfb6133e6463c859952270231f8e740363`；最新 `5083a456b1caff33fbc56c5fa10927582432a283` 仍包含同一份合成腳本及 harness。後者 app.js 已另有修正，舊實跑不改標到新 head。
- #175 `1127531f3aab472e01a4a99c03ef7b739b1b8ae5` 是交付索引；合成 probe 實作屬 #174、native test 屬 #171。

## #171 可接回的修正

`tests/test_assembly_generation.py:214` 現要求拒絕的 error／preview violation actual/message 含 `I42: delete the owning assembly instance`，拒絕後 dump text 及完整 assembly-read 相等。它排除了僅靠 ok:false 而被其他引用守門拒絕的假陽性。它仍只刪第一個 member；整合中獨立 `assembly_ownership_probe.py` 另有三 member、完整命令與讀取收據，不必把該工作重新實作到 canonical owner 檔案。

`tests/test_grid_subdivision_oracle.py:640` 新增 `NativeSubdivisionOracle.test_formal_rule_line_timber_undo_redo_survives_reset_load`，重用正式 rule 線＋兩支合法支撐 fixture。放置 undo/redo 比完整 snapshot；reset 後 objects 的 faces/spaces/gridSystems 及 references 的 guides/grids/timbers/specs/datums 為空，dump 不含 timber10/at-line rule，再 loadfile 並比原 dump/objects/references。這是有意義的清空後載入，接受為 canonical 回歸。它和本輪獨立 grid probe 有重疊；獨立 probe 額外涵蓋 source pitch 修改、source history、完整初始空 snapshot 與略過 load 的負控制。兩者不是同版重複派工理由。

AST 方法清單獨立點算：assembly 22→22，無方法增減；grid 40→41，只有上述新方法。fd5b8c8 的 expected 仍 assembly21/grid40。整合 9a 已修 assembly22，接新交付時只需 grid 精確 40→41；不使用 `--update-expected` 批量推導。完整方法清單及來源 blob SHA256 在 `report.json`。

## #171 收據邊界

`native-contract-run.log` 保留 fresh bridge 指紋、exe SHA256/size、編譯命令／時間、兩測試完整 unittest stdout/stderr、exit0；可以核對「作者交付的兩測試實跑結果」。它沒有執行當時 HEAD、dirty diff、test script hash、實際 unittest 命令、Python 版本、完整 native command/response 或 sidecar 原檔；不能獨立綁定成新整合候選驗收。#175 提供可重現命令，但不能回填原 log 未記欄位。

contract-review 如實保留首次使用無 sidecar 舊 bridge 時雖 exit0 但 skipped=2，且原 log 被覆寫。該首次 raw log 屬 missing，不造新原始檔。文件仍明示 no-op roundtrip 舊呼叫點、草稿/.scene 對照、跨專案未決政策等缺口，沒有把兩測試提升為完整產品通過。

## #174 已交付的合成 browser probe

`geometry-web/save_reopen_synthetic_test.js` 的 #174 receipt 記 1400/390、24/0、exit0。`synthetic-source-binding.json` 已逐一確認 receipt 六個 LF SHA256 與 b0ef9bc Git blobs 全符；script/space_model_test/space-workspace/test_space_floor 在5083仍相同，app.js 及 floor 已改，故24/0維持舊實跑範圍。這是已交付可接回工作，不應再開同等作者功能。

| 項目 | 已覆蓋 | 精確界線 |
| --- | --- | --- |
| grid/face/正式 rule timber | 合法600×400面、300×300未放置面；UI建系統/規則/binding/角材，成功改u pitch；完整 dump 保存／重開同 hash，若干完整引用 tuple及 id | 沒有 Undo/Redo；身份快照中的 objects/references 是選定欄位，不是整份 API response |
| 真產品開檔 | UI Save downloadfallback；New；Open button；CDP filechooser 的 #projectFile 選檔；實際產品 upload | 僅 .gcanvas，沒有 .scene #btnOpen/#file；downloadfallback 不等於OS Save dialog |
| 先清空 | New後等 busy=false、oc.faces/gridSystems 為空 | 只讀前端 cache；沒有 native dump/完整 objects/references/assembly-read 的空狀態 oracle |
| 完整封包 | ZIP world.scene 和保存 dump 全等；規則能力字串、next-key、from-binding、無translation；重開 projectId相同 | 沒有独立 manifest.requiredCapabilities 包含 dump required_capabilities 的斷言；沒有完整 project manifest/models/drafts/assets 比較 |
| assembly | 無 | cannot-test 明確 not-executed；label「owned 角材引用」其實是普通 grid timbers，不能寫成 I42 ownership 通過 |
| 雙寬度 | 1400與390 | 不是實體手機或IME驗收 |

需獨立指定 `GEOMETRY_SAVE_REOPEN_ONLY=1` 才跑這組；無 filter 的 full-space-suite 未包含它（space_model_test.js:84/1234）。不要把 full-space 成功視為 synthetic grid 已跑。有限檔案下載輪詢有 100ms sleep；既有交付應如實記錄，新增 probe 保持實際事件等待。新版 point() 會有限次滾動避開 sticky footer，仍要求 hit-test/可用，不 force click。

## 僅剩必要補驗

1. 接回 #171 強化與 #174 既有 synthetic；整合回歸按新候選 source變更安排，既有24/0不搬成新head。
2. 在 browser slot 對新整合候選先跑交付的 save-reopen filter，保留完整 raw receipt，避免重造 UI fixture/authoring。
3. 既有 private probe 可補 .scene grid 真產品開檔、assembly 兩格式真產品保存／開檔、三 member I42拒刪且 dump/read不變、native確空及完整 references/API比對。其 grid .gcanvas 部分與已交付項目重疊，但額外 oracle 有 nativeempty及完整reference/manifest；若 root 要減少重複，先決定有界格式篩選或只加 oracle，不能不跑便宣稱已驗。
4. private probe 已 source-approved 尚未執行，API seeding/API非法刪除、不含非空models/assets/drafts 的限制維持。不要把它將來的 World-only 流程推成完整 .scene/.gcanvas 格式契約或 UI authoring/delete 驗收。

本審查未发现 #171 source 接回阻塞；精確 expected grid登錄及新整合候選必要測試尚待 root 收斂。沒有批准合併 main 或跨專案身分政策。
