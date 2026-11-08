# 後四個 browser 的單批終態收件準備

固定 F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`，只收 documents、grid、space、timber。目前只是外部草稿；不得把初期 SCOPE snapshot 的 observed 欄當作最終結果。

原 assembly 收件工具已真 exit0 且獨審6741/0。此稿透過 `ASSEMBLY_TO_FOUR_JOB.diff`、`FOUR_JOB_V1_TO_V2.diff` 展示範圍差分；tar 分包、source hash/stat、完整 leaf set、所有 member roundtrip 與 64MiB fresh reserve 算法相同。四個獨立目錄各沿用2MiB metadata allowance，合計8MiB，沒有更改產品門檻。原 CI 時限逐 job 保持10／15／15／20分鐘、watchdog3；不重新執行裁判或新增 timeout。

採用 `collect_four_browser_terminal_v2.py`。它分開保留 host／sampler／launcher exit、workflow exit、CI gate、checkout 與 source guards 的真結果，允許原紅燈資料封存而不改判；收件0不代表產品0。四個原 workflow receipt、launcher和sampler真終態均須存在；若啟動早期失敗而沒有 workflow receipt，就保留失敗與現場，須另明列那次收件範圍，不能略過。若發現額外 `<job>...json` request（例如環境重跑），也會拒絕不完整範圍，不默默只挑綠的一次。

每個 job 完整 launch／storage／sampler、各自 sourceplan、host plan/materialize 全流／工具／原host FINAL 具名入包；所有 ELF／cache／profile／screens／diagnostic 均保。原四個產品 actual peer 請在 publication manifest 另附小檔。sourceplan Gitdir／mutable latest 只作hash-only，Unix socket metadata-only，不複製seed/source payload、不刪原件。

四個原 host FINAL 全部確定後，由 root 建立 terminal-pins JSON：頂層恰為四個 job，每項恰含 `final_sha256`、`plan_final_sha256`、`materialize_final_sha256`，分別綁固定 `/workspace/geo337-F9-<job>-SHM[-plan|-materialize]-EXEC_FINAL-20261025.json`。不能用預估 exit／未完成日誌代替。

獨立靜審需頂層 `exit_code:0`、collector和launcher的精確SHA256。root 再以正式 `require_escalated` 執行 `launch_four_job_collection.py --peer <REVIEW> --peer-sha256 <pin> --terminal-pins <JSON> --terminal-pins-sha256 <pin> --execute-root-approved`。預設只列PLAN；旗標不取代OS批准。輸出兩個fresh OWN SHM目錄，原c387記全部argv／exit／完整流／環境／SHA。root須保證四job及source guards已結束；不碰活動原件。

工具不操作Git/API。SHM中raw／fixtures／Git objects全部受保護。正常push及GitHub原始blob逐bytes/hash/OID驗證完成前，`delivered` 固定false。所有未執行與未核項仍明列，不以assembly或舊F8結果代替。
