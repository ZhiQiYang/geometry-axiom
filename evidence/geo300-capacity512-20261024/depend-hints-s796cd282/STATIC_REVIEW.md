# S796封包工具靜態審核

這是準備階段，沒有執行封包、產品測試、編譯、Git、checkout修改或遠端發布。`package_s796.py` AST可解析，模組沒有subprocess／動態import／Git入口；只在主代理指定的全新本準備目錄子目錄寫封包。

已逐項對實際原件檢查K15/H18/legacy98/H7/profile/binding/preflight/merge/N256 schema。原98 exit1、S H7 exit:null/timed_out:true、1200.106348秒與008未生成RESULT均保留；不把歷史execution改標S、不把預檢當正式ledger。N128 input/stdout/stderr直接逐bytes相同，只保同法診斷結果，不冒正式性能。

選集是固定required，不用glob將其他候選／622 graph混入；舊H28完整包／原B graph archive不重封。原命令入口、observer、graph driver/reuse wrapper/trace文本均選入；未另存的binding/preflight collector缺口已明列，不後造executor冒原工具。

tar以普通檔保存，每member核path、bytes、mode、SHA及沒有遺漏，讀回採串流、不另外解壓整份。先留預估封包成本，再保原64MiB reserve；逐檔與完成後也檢查reserve。所有原件保留，失敗部分包也不自刪。官方HEAD是主代理另驗的宣告值，工具不冒自行Git核過；PROGRESS current與發布仍由主代理處理。

最終追加required：S796 H7時間audit、舊smoke實際OBSERVER87fdcecc…、新版417eca…工具與精確checkpoint函式fsync/readback控制（含持久archives）。舊smoke1test/0以舊工具身份保留，不冒新版完整H7；新增控制的test_suite_rerun=false。時間audit不將311.857秒未歸屬成本全歸給收件，也不斷言Git/API是唯一timeout原因。

本文件是靜態核對說明，不是執行通過收據；實際封包後的STATUS/MANIFEST/SHA256SUMS才提供逐member核驗與壓縮成本。最終script SHA由主代理收件訊息及準備目錄SHA256SUMS綁定。

最終獨立同行已核`4ede1396cc00d4853a434e20b16cb640d6c454da5208e9a894b98d5e803f2311`（16584 bytes）：新增required路徑／原schema／87fd與417eca工具hash均同，沒有optional跳過、沒有622 graph、未見阻擋。同行未執行封包、測試、編譯或Git。

另直接核graph BUILD原兩命令均為`gcc -std=c11 -O0 <web_bridge.c> -o <plain/trace> -lm`，BUILD.kind明列monolithic diagnostic；README之用語有原命令依據，沒有以正式separated H7冒稱。
