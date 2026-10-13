# PR217 67a1a19 審查 M1：逾時保留原始輸出

TimeoutExpired單獨處理：保留exception.stdout/stderr的bytes，例外字串另放error；命令紀錄timed_out=true、exit=2（gate的infrastructure分類，不冒稱被殺子程序的實際returncode）。正常返回timed_out=false，既有180秒預設不變。輸出檔不再被清空或以例外訊息取代子程序stderr。

回歸：`ulimit -s 16384; python tests/diagnostics/fragment_gate_timeout.py`，exit0。實際Python子程序先flush兩串stdout/stderr，再等待30秒；gate原run函式以0.5秒逾時。driver從AST取得正式bounded/run函式，並非另寫一個模擬handler。明驗兩個raw檔案內容、timed_out、infrastructure結果2、另存error及commands.json。stdout中保存實際觀察到的兩串partial輸出。

突變：暫存副本只移除TimeoutExpired專用except，保留廣義SubprocessError處理；同driver針對副本exit1，在raw stdout應保存的斷言轉紅。正式檔案不被改成突變。完整stdout/stderr保留。這是恢復先前丟輸出的失敗路徑，不是語法錯誤或沒跑到child。

修改後完整fragment必要gate重跑：`python tests/diagnostics/run_fragment_heap_gate.py --output /tmp/geometry217-gate-timeout-fixed`，exit0；core/bridge/fault編譯、stack/guide OOM驗證五命令exit0且timed_out=false。receipt含本次gate來源/裁判與二進位雜湊，raw各命令輸出保留。py_compile兩檔exit0。

本輪沒有產品改動，沒有改變native變異裁判或其oracle；既有48筆帳本的產品閉包仍一致。B2仍阻擋：尚未承接最新main、未跑精確最終head的完整native／正式七項。仍不是完整native或正式WSL收據。
