# GEO-261 原生階段接續點（2026-10-16）

使用者於本次對話明示「階段性完成後停止」。本文件保存已完成的原始碼整理與實跑的有限檢查；**不是 GEO-261 完成、功能等價或可合併聲明**。

原始碼凍結：`6bddee15ad12b8a2dc0d4c6024988ffab0569d2d`；tree：`308254bc69d459a24c65b3c7a507bdd00d16b850`。父版本：`2ba81689dc78005d5347644186049d10e7f56fb3`。發布入口為 draft PR #279，前期失敗與診斷收據由 #286 保留，Python 分層及 definition-source 相容修改在 #285。發布使用一般 merge，不改寫歷史。

## 本階段保存內容

- `World` 實際分成三個內嵌值：K `GeoDocument`、W `WoodDocument`、H `AppDocument`。K 的九個 store、候選快照 offset、canvas-only 比較範圍與 scene/bridge 接線已同步；不是巨集欄位別名。
- 封閉空間的成員、平面／區間一致性與有序診斷搬入 K enclosure。H 保留原命令格式、錯誤文案、交易回滾與重驗時點。K ID 0 使用明確 REGION_REF 身份；H 既有 boundary 0 禁令不變。
- 組立的規則、綁定、slot、instance、mapping、generated 定義與尺寸來源接入同一候選圖，實際 owned-member pose 與最後 I42 footprint 讀取 typed 值。未擴充 model root 白名單。
- `NativeBuild(kernel_only=True)` 不複製、編譯或連結 H/W，新增文件與 enclosure 見證；這條路徑的原生執行仍未驗。
- 47 個有效／等價突變錨點遷至真正的 K/W/H 實作；全部 50 個身份、3 個退役項及歷史等價說明原樣保留。注入器沿唯一 include 路徑展開，產出的程式碼雜湊納入二進位快取。
- 原生來源新位置已納入 binary/runtime freshness（先前 commit `b9667341`）；沒有重啟使用者服務或清除瀏覽器儲存。

## 實際驗證及數量

本次收尾選定的純 Python／靜態檢查為 **53/53，0 failures、0 errors、0 skips，exit 0**：mutation migration 15、既有 mutation freshness 24、enclosure 3、document 3、assembly sources 2、既有 assembly/contact/grid 邊界檢查 6。完整測試 ID、輸出與執行選擇見 [portable-tests.log](evidence/native-stage-20261016/portable-tests.log)、[portable-tests.json](evidence/native-stage-20261016/portable-tests.json)。另 `python tests/mutate.py --selftest` 實跑 **113 checks、exit 0**；`git diff --check` 與 registry 檢查通過。這些檢查沒有編譯或執行 C。

`unittest` import-only discovery 共 **62 個 GEO-261 suites／627 個方法**，不是通過數。相對父版本新增 5 suites／56 方法：assembly sources 8、assembly graph product 4、document 10、enclosure 19、mutation migration 15；其中 33 個新增 native 方法未執行。`run_all.py` 補登記 29 個之前缺列的 suites，expected 補齊 37 個缺項，並依 discovery 修正 model sources 10→12、binaries 32→33、runtime version 24→25。[完整數量表](evidence/native-stage-20261016/discovery-counts.json)保留原值／新值。

前一輪原生執行仍是 `14ab395d56ce1dcabe43e65b5311776a8d3e6221` 的 **101＝98 pass、1 failure、2 timeout errors、0 skips**。單獨 120 秒診斷下兩個同二進位案例分別成功於 18.850039 秒及 43.040446 秒；原 20/30 秒驗收結果仍為失敗。新來源包含裁判修正與 candidate 快取改善，但尚未重跑，不宣稱已修復。

`2ba81689` 的 33 suites／372 方法僅排定前置準備。使用者要求停止時尚未編譯或執行任何方法；其 native、PF3 50／support 20＋19 mutants＋restore 20、原有 section 27 均標為 **UNRUN**。Windows archive 的兩次環境錯誤保留在獨立前置紀錄，不冒充產品失敗或測試結果。完整解壓位元組核對與 runtime discovery 未完成；第三次前置程序等候逾 10 分鐘後，核對自有 PID／命令列才停止，exit 1。372 是靜態清點數。[精簡前置收據](evidence/native-stage-20261016/preflight-2ba81689/PREFLIGHT-RECEIPT.md)保留這些限制。

## 接續時仍須處理

1. 先對最新凍結來源建置與驗證，不把 `14ab` 或 `2ba` 的收據套到此版本。先確認共有 NativeBuild／unity 接線可編，再跑本片新見證與原有回歸。
2. 來源圖 `coverage.complete` 仍是 `false`。尚需完成並逐項核對 enclosure、RC obstacle 的定義／space 關聯、member anchor／role／priority／order／between 定義、boundary fixity、衍生 key／segment／fixity 與 grid vertex key 帳本，以及未使用的定義枚舉。engineering binding source key 的穩定身份與 contact feature 身份也需複核。
3. 完成整份 `ulimit -s 16384; python3 tests/run_all.py --build`、全部 mutation ledger 重產及 `--check`、舊 `.scene`／存檔／夾具重開、正式 native＋六個 browser jobs。當前 ledger 未重產，不能視為新來源通過。
4. 依已核准提案與同一對話授權紀律處理 SSOT／白話／revision 相容與唯一正典閱讀器同步；D64／I74／R60 的追加範圍仍待使用者明示。這一階段沒有修改 SSOT，也沒有產生第二份閱讀器。
5. Python 預設載入器尚未切換到完整原生來源圖；完成涵蓋與同源 C→Python 驗證後才可採用。最後仍須 Claude 品質審查無阻擋，方可依使用者定義宣告交付。

本次停止後沒有排定新的編譯、瀏覽器或自動續跑。草稿 PR 保持 draft；接續需以本接續點與實際 Git head 為準。
