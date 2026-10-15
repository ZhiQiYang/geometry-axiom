# PR217 審查 B1/M1 的修正證據

基底 head b2be09a575d172498e43e450488268ab4eb4af85。B1成立；先前將malloc失敗與不合法候選共用false會在保留片OOM時提交另一片。改為三態結果：-1 allocation failure、0 invalid、1 valid；guide/timber呼叫端遇任一-1整筆拒絕，沿用既有交易回滾。C主檔只改6行，13047個CRLF，0裸LF；其他成功路徑不變。

單次OOM測試從既有R13場景將guide改成v，先載入尚未apply-proj的完整場景並記dump；再載入apply-proj版本，注入僅reference_fragment_candidate第1或第2次配置失敗。兩個暫存副本只在該函式的分配點加故障包裝，原版副本回到b2be控制流，修後副本保留三態守門。16MiB下old build exit0、new build exit0；原版test exit1（OOM仍ok:true），修後兩次fault test exit0（ok:false且完整dump、definition_sha256不變）。測試全文為tests/diagnostics/fragment_oom.py；各次commands/stdout/stderr見oom*.out/err。不是全域malloc失敗，也不是實際耗盡主機記憶體。測試的World不變僅涵蓋dump與definition指紋，不冒稱Undo/Redo全狀態已驗。

M1：讀取及保留hard，只變更soft。hard不足16MiB在exec前明示ENVIRONMENT BLOCKED、exit2。繼承soft=hard=16MiB：舊入口exit1（preexec無權提高hard）；新入口exit0。繼承hard8MiB：新入口exit2。最後產品core/bridge＋hard16回歸exit0。所有輸出保留，不把舊入口環境錯誤算作產品突變killed。

最終core的16MiB CLI139場景139pass/0fail/0infra、exit0，stdout與前報原版全文逐byte相同；不是完整native。新core/bridge建置exit0，原始編譯輸出保留。B1回退副本就是修正拿掉的對照，有限hard的M1另分環境錯誤。

B2未完成：尚未重產45筆變異帳本，不能沿用；回歸仍為diagnostic手動入口、未登記正式run_all；完整native與最終head七項尚缺。看板禁止雲端排本機WSL全量，所以沒有偽造七項收據。PR維持draft/阻擋，不稱可合併。原始基底未整合新main；之前的heap有限對照、CLI8MiB其餘缺口保留。
