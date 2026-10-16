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
