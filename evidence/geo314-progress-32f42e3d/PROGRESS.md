# #314 進度：隔離 W 診斷

產品／測試 SHA：`32f42e3d991c7d2d916d21bfe8ac5d3dd0f9b131`，建立於整合 `4b665fae21ab63aaffb7d84f6a32d5a469ba1675`；未帶 #323 修改。

本收據只涵蓋 `tests/test_geo261_wood_grid_application.py`，不是完整驗收。

- 官方 runner：23／23 passed，failed／skipped／error 均 0，outer exit 0。
- 新 W 負控制 11 項均為 baseline 0／撤回 1／恢復 0；每項固定正常具名 ASSERT，包含缺 store 的安全拒絕，沒有 crash、compile error 或 timeout 充當 kill。原始 argv、完整 stdout／stderr 與 code 見 `W-DIAGNOSTIC/stdout.raw` 的 `GEO314_W_CONTROL_JSON`。
- 全新外部 TMPDIR，沒有使用共用 `/tmp/geometry-tests`；實際 NativeBuild 的 233 份 inputs／binaries、完整 build-log 已在 atexit 清除前封存。產品來源與 before／after HEAD、status、patch 同封；前後乾淨且 SHA 一致。
- 此 shell 未將 `google-chrome` 放入 PATH，原版本採集 exit 127 照實保留。補採 `/workspace/geo261-environment/bin/google-chrome --version` 為 exit 0／Chrome 156.0.8078.47（含原 stderr）；Node v24.19.0。沒有執行或宣稱 browser job 通過。

待辦：七份未修改 bridge 產生的凍結舊場景、H 有序證據／真 bridge／靜態 inventory／舊幾何與更名回歸、正式 mutation ledger 全份、架構四檔與三裁判、完整驗收及 PR 正文。這些項目目前未跑，不列通過。M110 單獨為 preview 遮蔽的 equivalent，MP1＋MP3 配對的真正常 ASSERT 證據亦待執行。

下一步依主代理排程，避免與 #323 正式效能量測互相干擾。
