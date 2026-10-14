# 兩個獨立容量邊界各自的5秒預算

13476677完整native原件：2751 pass／1 fail／1 GDI skip，actual exit1、1136.422秒。唯一失敗為原集合雙邊界測試5318.230ms，test timed out after 5000ms；新live-ref B1回歸1220.438ms通過，其他suite無fail。首紅保存，不移算為新head綠。

定位：非節流原分組兩案約1906.668／2281.317ms，各自建新VM fixture且各自保存→標孤兒→保存→捨棄other→保存冷讀，全部原斷言均保留。這是兩個獨立off-by-one容量案例，不是彼此有先後依賴的競態。改成兩個具名Node tests，各自仍用原timeout5000；不加sleep、不改產品或縮減斷言。內層body逐byte相同，timer字面未改，證明在unchanged-assertions.json。Node count701→702只因一個雙參數test改為兩個，不漏任何輸入。

實際新source子集：新增live-ref B1與兩個邊界各通過，3/3、exit0，邊界2239.453／2049.842ms。此子集與下述第三批第一個grouped試驗有短暫本人測試重疊，所以不把該第一組當等條件控制。

定向controller只對本人新session/PGID的Node及其子程序STOP/CONT，period100ms；每次PID、monotonic、signals、實際exit及source/wrapper SHA完整記錄，不碰外來程序。測試副本只插每案起訖量測，原assertions/產品照常跑；不是正式WSL/native收據，也不是產品變異。全部測量資料保留：第一批70%為1/0/1/1，末個split仍可能超時；85%批為1/0/0/0，撤分組在較快負載下也可綠。未把這些不穩定控制藏掉或宣稱任意CPU負載都保證5秒。

第三批70%後三組沒有本人其他測試並行：split exit0（2429.371／2411.296ms）→撤分組 exit1（2835.282＋2950.199ms，具名5000ms timeout）→還原split exit0（2812.067／3376.513ms）。這是同一名義節流條件的分組反證，signal事件可核實際暫停比例；主機當時負載仍可波動，不宣稱排他/完全相同CPU供給。native首紅與實際拆分後整輪結果各自報告，不拼接部分綠。

source副本由原測試文字加量測/換分組形成，wrapper以原測試file path作CommonJS相依解析。controller原工具在orphan-timing.py，可重現其生成方式；historical receipts為實際執行時工具版本（後來加了保留批次suffix），不是重新標記執行head。所有原件含未成功的控制組。
