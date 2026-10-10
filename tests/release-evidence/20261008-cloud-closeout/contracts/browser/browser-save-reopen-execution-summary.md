# 保存重開 browser 補驗結果

已完成四組案例（grid／assembly ×1400／390），各組都執行 `.scene` 與 `.gcanvas` 真產品保存／選檔重開，共八次重開閉環。唯一 browser 已關閉並於 2026-10-08 16:52:46 UTC 釋放；沒有改產品碼或 canonical owner 檔案。

- 整合候選：`458779f003e1f57fdc0f4420564a0b295227843e`，執行前後 HEAD/tree/source hash 相同、dirty status 為空。
- main：`5cc1ffa1ee85120eca14258b86b715151cad274f`；#171：`fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d`。原始 git 命令 stdout/stderr/exit 在 before/after-identity.json。
- runtime：`5f7efb63220523dd481660f8dc092ca9f40f35e896cbe172d7694e61f308eb66`，pid138518，session `73f0ea92dd884bdb93c88379161ca93b`，loopback18971，fresh=true。前後 identity 不變。
- 唯一 service 子程序 bridge pid138519；`/proc/138519/exe` 指向 `/tmp/geometry-tests/bridge`，live binary SHA256 `b76a6da590512722d6eda64cfc946392ccc2636f82ab187ef822c1e1606d68b5`，registry fresh，sidecar 原檔隨收據保存。
- Python3.12.14、Playwright1.62.0、Chromium151.0.7922.173；chromium_sandbox=True，沒有額外 launch args。
- 腳本 SHA256：`6f340ae4ee6b79dc721837649d813cb465f6c730dd176de8ebf09a1ab50b69a5`。run-02/script.py 凍結執行版本。
- 原始命令／stdout／stderr／exit：`browser-run-02-command.json`，exit0，stderr空；receipt.json SHA256 `3f69a6d5acd62f3c0a6b60330d8ddd87c2847422e4ca5f4c01c0b7e9f9e41f90`。

每個 fixture 先透過 API loadfile 建立已驗合法 scene，再 await renderObjects；這是 API fixture 建立，不能稱 UI authoring。從產品選單點 `.scene` 匯出，Playwright download 保存原 bytes；New 之後比完整 native empty snapshot，再透過 #btnOpen/#file 實際 filechooser 上傳，等待 HTTP／busy／draw／fileinput／cardkey 完成。重開比全部 dump／objects／references／assembly-read（只排除成功載入允許遞增的頂層 revision，raw revisions全保存）。

接著產品 Save 走明示的 download fallback，檢查 ZIP world.scene、projectId／name、requiredCapabilities；New 後完整空狀態及新projectId，從 #btnOpenProject/#projectFile 真選檔重開。原生資料完整比對，project manifest/source bytes／identity 亦比對。

assembly 每次 `.scene` 或 `.gcanvas` 重開後，對三個 member timberId 分別執行原生 API delete，必須含 I42 具體 ownership 拒因；每次拒絕前後完整 dump 和 assembly-read 包括 revision 都不變。共12次拒刪，完整 commands/responses及每個member收據保留。

四組 case 都沒有 pageerror、network-capture error、context/trace cleanup error；trace 與 screenshot、匯出 .scene/.gcanvas、archive manifest、空／前／後 snapshot 均在各 case 子目錄。檔案 SHA256/bytes清單為 `browser-run-02/SHA256SUMS.json`。完整 raw合計約25 MB，屬合成 fixture 沒有私人圖紙。

第一輪 `browser-run-01` exit1，於啟動 browser 之前失敗：此 kernel 沒有 `/proc/<pid>/task/<pid>/children`。保留原腳本 `9a744684...` 和原始 traceback；第二輪唯一修正是前置 process graph 改用已保存的 `ps -eo pid=,ppid=`，仍要求 runtime 存活、唯一所屬 bridge 及 live binary hash。產品流程／判定沒有改。delta receipt `browser-preflight-fix-01.json`；此輪不是產品失敗，也不是 sandbox policy 拒絕。

範圍限制：此 probe 只驗正式 World/reference/assembly閉環。API seeding與API拒刪，不宣稱UI幾何建立或UI刪除；downloadfallback/filechooser不是OS Save dialog；390只是desktop viewport，不是實體手機／IME。fixture沒有非空models/assets/PDF/未發布drafts，故不能當完整 `.scene`／`.gcanvas` 所有格式欄位對照或模型庫驗收。既有 native probe 的 UndoRedo/source修改／no-op負控制證據維持原版本，不冒稱本browsercase做過。#174 delivered synthetic UI authoring與改pitch gate由root另行接回實跑。
