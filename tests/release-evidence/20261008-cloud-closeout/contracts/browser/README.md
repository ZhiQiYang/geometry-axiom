# Browser 保存重開補驗原件

整合候選 `458779f003e1f57fdc0f4420564a0b295227843e`，乾淨工作樹；run-02 exit0。grid/assembly ×1400/390，每組依序從產品 `.scene` Export/New/Open 及 `.gcanvas` Save/New/Open，完成8次清空後重開。完整World/reference/assembly比較；assembly每次重開對3個member鎖I42拒刪且完整dump/read含revision不變。

- `browser-run-02/script.py` 是執行當輪exact probe，SHA256 `6f340ae4ee6b79dc721837649d813cb465f6c730dd176de8ebf09a1ab50b69a5`。
- `browser-run-02-command.json` 是完整命令/stdout/stderr/exit。`receipt.json`、before/after identity/runtime/bridge sidecar 綁定來源、工具與服務。四個case目錄保留完整native commands/responses、HTTP原始请求/回覆、empty/before/after全資料、synthetic下載scene/gcanvas及每組最終截图。
- `browser-run-01` 是未啟browser的前置失敗：kernel缺task/children。原脚本與原traceback保留。`browser-preflight-fix-01.json` 記唯一修正為可用ps PID/PPID後代查詢；唯一runtime→bridge與/proc/exe hash要求維持，產品oracle未改。
- `PUBLICATION-MANIFEST.json` 記所有逐bytes複製原件及未公開trace/額外截图的原路徑、size、SHA256。沒有複製browserprofile/session資料夾。runtime session是服務身分欄位，不是登入憑證。

再現須先啟動同候選的獨立loopback產品服務、fresh bridge及sandbox允許的Chromium。使用實際clone及此證據目錄，明示fixture路徑，避免依賴歷史Temp：

```sh
python3 <evidence>/contracts/browser/browser-run-02/script.py \
  --root <clone> --url http://127.0.0.1:<isolated-port>/ \
  --bridge <fresh-bridge> --out <new-empty-evidence-dir> \
  --grid-scene <evidence>/contracts/browser/browser-run-02/grid-fixture.scene \
  --assembly-scene <evidence>/contracts/browser/browser-run-02/assembly-fixture.scene
```

入口 fixture 與拒絕刪除使用API；幾何authoring與刪除按鈕不在此驗收。保存/下載/開檔/New使用實際產品UI與filechooser；showSaveFilePicker明示停用以選產品downloadfallback，不當OS Save對話框。390為桌面viewport，不是實體手機或IME。fixture沒有非空models/assets/PDF/未發布draft；不當整個格式、模型庫或跨專案合併政策驗收。既有delivered synthetic提供UI建立及來源pitch修改，另有獨立gate收據。本包不重跑也不代替那些項目。

完整native/HTTP、逐狀態snapshot與sidecar原件收在 `raw-evidence.tar.gz`，member 路徑和原始SHA256列於PUBLICATION-MANIFEST；每个member已重新解包讀取核hash。可執行 `tar -xzf raw-evidence.tar.gz` 還原同層目錄。tar不含trace或browserprofile。私人原件完整保留。
