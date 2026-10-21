# 首輪 native 原始證據（中斷，非完整驗收）

固定來源為 `366ef501b78105d1f7242dc1f4f4752cac9086b5`。原命令為 `timeout 2100 python3 tests/run_all.py --build`，16 MiB stack。首輪發現容器 PID 1 不回收孤兒造成 assembly 行程清理測試失敗；環境診斷與 plain/subreaper 單測原件位於「環境診斷」。主代理於第 43/224 項進行中發出 SIGINT，外層 exit 130，耗時 574.9473356559997 秒；此輪未完成，不產生完整 native 結論。

`suite-logs` 在第二輪啟動前逐 byte 複製當時所有 .log/.json 原件；來源時間與 SHA-256 位於 `suite-log-source-index.json`。未複製二進位或 shim source。新完整驗收使用同一來源及測試，由外層 subreaper 回收自己的孤兒子行程，不修改測試或忽略 zombie。
