這是 codec 快速解碼候選的歷史定向驗證資料，14／14 通過，failure／error／skip 皆 0，88 次編譯與連結紀錄皆為 0。原件沒有產品重跑或補造。

實跑於 detached `43f85313c32410ac01406ab585846bbacafea278` 加唯一 `definition_sources.c` 補丁；之後同 bytes 提交至分支 `codex/geo261-p189-codec-trial-20261021`、SHA `7ad3216ac3ea00bec0adac7b38c3a3daf0a39d09`。這不是在 7ad 提交後重跑。`提交後來源綁定.json` 另保存本次 git show 真命令、退出碼及與實跑候選相同的 SHA-256。

原方法入口為 `env -u CC -u PYTHONOPTIMIZE python3 -B /workspace/geo261-evidence/wd-read-candidate/run_targeted.py`；實際 wait 的子命令是 `timeout 900 python3 -B /workspace/geo261-evidence/wd-read-candidate/targeted_tests.py`。cwd、環境及 16 MiB stack 以 `原件/targeted/command.json` 為準；`receipt.json` 保存 rawWaitStatus=0、exitCode=0、來源前後相同及 9.15574672299772 秒。開始 2026-10-21T01:02:05.425033+00:00，結束 01:02:14.581042+00:00。

完整測試層 stdout／stderr 原 bytes、14 個具名 test id、unit 結果、88 筆建置命令與各自 stdout／stderr／exit 均保留。build-log 是既有 NativeBuild 的文字紀錄；沒有另存各測試內每個執行子程序完整原始 wire stream，也沒有獨立工具傳輸 raw 日誌，不能把 unittest 的 OK 擴寫成這些不存在的原件。

沿用五個 definition 具名負控制、四個 H 返回值控制及 quantity 變異案例，未新增 decoder 專屬負控制。快速路徑撤回舊 loop 應維持功能綠，效能裁判另見既有性能包；本包不證明性能門檻或最終來源的七項完整驗收。完整 prefix 截斷、尾隨 byte、sticky failure／bounds 的最小專屬補測不在這 14 案範圍。

`原件/README.md` 和靜態審查保留當時狀態，其中「未推送／未跑性能」是歷史說明，不是當前主分支狀態。所有 18 個既有檔案原 bytes 都列於來源索引；三個 .py 只改副本路徑為 .py.txt、以 0644 保存為資料快照，未新增執行入口。沒有 binary、archive、pycache。SHA256SUMS 覆蓋本包其他每一檔；舊凍結包未改。
