# PR217 B2：新帳本與必要 Linux 驗證入口（部分交付）

產品來源為遠端head 7dc0c7524e7c42c031e513cbc161493077dd294a。本輪沒有產品變更；新增正式Linux gate、來源/二進位/命令收據、必要入口文件，並重新產生變異帳本。

測試副本只包含所需core/bridge閉包及裁判，不是完整clone。第一輪執行48個變異，45筆非退役紀錄因execution.head空而stale，exit1；不採為有效帳本。其stdout/stderr保留。之後建立真實本地測試快照d487dd50b6a6338e2a6bbe0fab91532bfa78662c，核心blob8e11f75de7c4db97a2b7f430825711df08b431ca與遠端7dc0c75一致；重新實跑裁判，沒有事後改寫任何record的HEAD。原片段閉包SHA009c3bcd3e549a7d66f8461961b9cba5414a384d78e3a14d3a053be4420840f7；oracle/來源/執行器/二進位雜湊都由原裁判產生。新帳本採JSON緊湊排版，不變更紀錄內容或record指紋。本地快照不是遠端PR commit，不能冒充最終head七項；兩種身分與42檔來源雜湊另列source-link.json。

命令：ulimit -s 16384；MUTATE_RESULTS=/tmp/geometry217-mutants-identified.json python -u tests/mutate.py。全48：40killed、1crashed、4equivalent、3retired；survived/invalid/stale/blocked=0，exit0。M20在_test_lshape.scene三次同一SIGSEGV，由裁判列crashed，不能寫killed。基準線139場景全過；全部執行資訊在正式tests/mutants_results.json。後續同MUTATE_RESULTS的--check也exit0；--selftest為113checks、exit0。原命令輸出及分類保留，沿用的是來源/編譯指紋相符的exe cache，所有測試都重新執行，沒有沿用舊判決。

必要Linux gate：python tests/diagnostics/run_fragment_heap_gate.py --output <checkout外新空目錄>。本次final實跑exit0：core-build、bridge-build、fault-build、stack-regression、oom-regression皆exit0。receipt.json包含各次monotonic耗時、原始命令/退出碼、42個完整quoted-include來源SHA、4個裁判/場景SHA、3個新二進位SHA及環境；來源/裁判前後一致。raw stdout/stderr逐命令保留；hook只替換該函式分配點，故障副本原始碼留在執行目錄。既有非空輸出目錄拒絕exit2。Linux hard16/core16/bridge8；OOM只驗guide第1/2次片段分配、完整dump/definition，不外推timber或Undo/Redo。此必要入口已寫入INTEGRATION-GATES.md，是既有run_all範圍外的額外gate，不改任何原suite期望數。

未完成：完整native、與最新main整合、最終head正式七項仍缺。B2仍阻擋，PR保持draft，不合併。此gate與48變異不是完整native或正式WSL收據；#211其他8MiB問題仍保留。
