# GEO-261 F1：固定木工前端配方與角色策略

這片把新建材料／斷面構件／角材表單／試擺的木工規格，以及主支方向推導、點線角色建議、角色選項及子格警告移到 `geometry-templates/woodworking/frontend.js`。宿主 `geometry-app/application.js` 固定選取深層不可變的 `woodworking/1`，缺模板時拒絕組裝。既有公開入口、DOM ID、選項次序、文字及保存格式維持。

一般新建面材保持 915×1830×6；網格交接保留空白尺寸；新角材材料也保留空白。開啟或編輯既存資料不重套新建配方。格線的 `data-role` 直接取語意值；更換顯示詞不會改角色身分。前端資產僅有兩條明列路由，啟動快照以同一次捕捉的 bytes 提供內容及計算指紋；木工／宿主來源改動會使舊服務過期。

**拿掉／合併（GEO-219）：** 合併散落在數個工作區的材料預設與角色推導到唯一固定 provider；零新增可見入口、按鈕或常駐教學區塊。

## 本片實際證據

- Windows Node：木工 provider／真宿主消費端 15 tests，15 pass；格線 renderer 13 tests，13 pass。
- Windows Python：runtime 30 tests，28 pass，2 真 symlink 測試因 WinError 1314 略過，exit 0。沒有把略過計入已執行。
- 同三個 suite 透過正式 `run_all.py --only` registry 執行：58 tests／56 pass／0 fail／2 skip，子行程 exit 3，依 runner 規則明確不是全綠。完整命令及 raw log 指紋在 `evidence/frontend-f1/aggregate.json`。
- 五個隔離原始碼突變全部以具名斷言失敗偵測：繞過新建 provider、繞過角色策略、重新解析顯示詞、遺漏移動來源的 runtime 指紋、錯誤正規化公開模板 bytes。各次 0 errors；正式來源前後 bytes 未變，暫存樹已刪除。
- 重現：`python tests/geo261_frontend_mutations.py --out <不存在的輸出目錄>`。收據及原始日誌見 `evidence/frontend-f1/`；最初兩次因隔離副本漏複製既有 JS 依賴而未完成基準線，未算成負控制或產品失敗。最終副本包含完整必要閉包。
- 獨立靜態審查未見阻擋，並另跑 15 tests 及實際工作樹 RuntimeSnapshot bytes／freshness／載入順序檢查。
- registry 計數增量：新 suite `node:woodworking_frontend` 15；`node:grid_definition_diagram` 12→13；`py:test_runtime_version` 24→30，合計 +22 個發現到的測試。

## 尚未宣稱完成

這是 F1 切片，尚非整個核心解耦。draw label 的具型別註記、組構生成的木工配方、其他宿主／模板接點與正式全來源 manifest 仍在後續切片。尚未跑本 head 的完整非瀏覽器套件、七項列車或真瀏覽器操作；F1 的 Node VM 不構成瀏覽器驗收。使用者服務未作測試重置。

## GEO-261 之後的錨點（2026-10-20）

`tests/geo261_frontend_mutations.py`（F1 有 5 個負控制，F2 增到 8 個，現在 9 個）在整合分支 `7e36543b` 上有兩處過期：

1. `runtime-omits-moved-source` 的錨點已不存在。`geometry-web/runtime_version.py` 的 `source_files` 迴圈在 `b9667341`（「include extracted layers in source freshness」）加入 `geometry-kernel`，根目錄由四個變五個。
2. 基準線在 `runtime` suite 就停：`discovered 31, expected 30`。同一個提交新增了 `test_extracted_kernel_host_and_template_sources_require_restart`。預期數改成 31，其餘 suite（17、52、7、13）不變。

| 案例 | main `adbaebf9` 原本打的位置 | 整合分支改打的位置 | 層數 | 為什麼是同一條規則、同一種錯誤 |
|---|---|---|---|---|
| runtime-omits-moved-source | 沒有對應：工具與案例都新於 GEO-261。變異後的文字就是 main `geometry-web/runtime_version.py` 的寫法 `for directory in ('geometry-web', 'geometry-core'):` | `runtime_version.py:88` 現行的五個根目錄 `('geometry-web', 'geometry-core', 'geometry-kernel', 'geometry-app', 'geometry-templates')` 換回 main 的兩個。`after` 沒改，只有錨點（`before`）跟著現況 | 1 層，單層即被殺 | 規則是「runtime 指紋涵蓋所有原始碼根目錄，搬出 `geometry-core` 的來源一改，舊服務就要過期」。變異等於退回 main 的掃描範圍。指名的 `test_template_native_and_host_source_changes_require_restart` 失敗，同時新增的 `test_extracted_kernel_host_and_template_sources_require_restart` 也失敗（共 6 個 failure、0 error）。 |

變異同時拿掉 `geometry-kernel`，所以 kernel 那條測試也會失敗。`after` 沿用 main 的原樣（兩個根），沒有另外設計只拿掉 `geometry-app`、`geometry-templates` 的版本。

### WSL 實跑收據（2026-10-20）

受驗提交是 `bda11f1430a19c88e0b0474dfe5034d3cf35b9f5`，`git status` 乾淨。環境：WSL Ubuntu-24.04（Linux，所以 runtime suite 的兩個 symlink 測試不跳過，`skipped` 為 0）、`/opt/node`，ext4 clone `/var/tmp/anchor-drift-geo261/repo`，經 WSL 鎖。指令 `python3 tests/geo261_frontend_mutations.py --out …`，結束碼 0，14 秒。

- 五個基準 suite 發現數 17、52、7、13、31，全部 exit 0、0 failure、0 error、0 skip。
- 9 個負控制全部 `detected`：每個都 exit 1、failure 大於 0、error 為 0，且失敗名稱含指名的測試。`runtime-omits-moved-source` 為 6 個 failure。
- 來源逐 byte 未變（`sourceUnchanged: true`），暫存樹已移除（`tempRemoved: true`）。
- 改錨前對照（`7e36543b`，工具未改）：4 秒內在 `baseline-runtime` 停下，`discovered 31, expected 30`，結束碼 1。

收據在 `D:/geometry-axiom-work/anchor-drift-20261020/`，沒有提交進 repo：`final-tools/out/frontend/receipt.json` sha256 `431dd0f24415bc72f6cae68a9baff1d459ffda2e8b00747e562af7254dc6a576`；`before-tools/frontend.out` sha256 `0d311e84de11355a11b87b0179dd89910289004b28d8b19d4a1a120a01b0d706`。
