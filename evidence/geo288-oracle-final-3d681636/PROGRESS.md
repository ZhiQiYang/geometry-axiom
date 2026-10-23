固定產品 F `3d681636902371ecc528b20f51eea33e272581c9`，獨立乾淨 tiny checkout；本輪 oracle 原八階段真終態：**符合全部原八階段要求**。

原程序 exits：`0,0,0,1,0,0,1,0`；原 driver／outer／top：`0/0/0`。完整 probe 真跑 60 方法；C4 與 probe 撤回各保具名正常 failure 1，非 crash/import/skip。八階段沒有允許 skip；沒有重產 ledger。

原 cfea/c387/6825/7d84 工具未改；top 真 argv 明列 `env -u PYTHONOPTIMIZE`；原 R3 排他鎖覆蓋八階段與 source-after，16 MiB stack。85 原輸入 raw hash 初末完全一致；mode/blob 由 setup 逐筆核固定 F。

`original-raw.tar.gz` 收錄四個原始目錄的所有檔案（driver／outer／top-launch／checkout-setup），逐檔對照 `ORIGINAL_RAW_INDEX.json`；原 argv、完整 stdout/stderr、環境、退出碼、source SHA 與原撤回／還原 bytes 均保留。`SUMMARY.json` 是索引，不替代原始輸出。

下一步：#314 owner 對真終態 raw 與公開 Git package 作獨立對抗審，目前 pending。本子項不外推 native／六 browser、歷史159 source mutants 或真正 native run_probe.sh 全場；原 unittest 在記憶體捕捉而未持久化的內層 streams 未補造。
