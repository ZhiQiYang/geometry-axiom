# #348 S796 候選：新原件一次收件

這份包保留不同來源的真 execution，不把閉包引用改寫為 S796 的新執行。候選 S=`796cd282693736af61c1b0d6c8ff91f03437a175`，官方產品仍由主代理另行確認；預期發布前官方 evidence HEAD 為 `cfbde095…`。本封存工具沒有讀寫官方 checkout、執行 Git 或 push，也不改 PROGRESS current／PR 正文。

| 原範圍 | 真 execution | 原結果與界線 |
|---|---|---|
| 新 K depend hint | edc57cd4a8f7e4eb5813d51435c4732b7d75b793 | 15 tests、exit0、無fail/error/skip，4.729628793s；到S非evidence無差異。不是在S重跑。 |
| H hint＋load residual | 057884a4388e72312067385b9cf738431d8d69e3 | 18 tests、exit0、無fail/error/skip，74.965864160s；後續新增K測試等不在該direct測試閉包。 |
| legacy regression原紅 | 4b17edac67648fb5f6048b05114a66e99eb1846a | **98 run／1 failure／exit1**，114.330930626s。唯一FAIL是never-invalidate建置前錨點唯一性assert；不是產品被具名斷言殺死。獨立85個K63＋H22方法原綠可依binding引用，不能將98整輪改綠。 |
| 172完整有序圖診斷 | fix4b17edac…／base9a8584f5… | 172/172、exit0、無failure，原plain/trace/stdout/stderr/五guard核同。185個實際build葉及172凍結場景的mode/OID到S均同；依REPORT引用，**execution仍4b17**。monolithic O0診斷不是separated正式H7。 |
| N256單次可行性 | 057884a4388e72312067385b9cf738431d8d69e3 | 27.764076694s、exit0、原placed-geometry斷言綠；對舊8b原34.701295152s input／輸出同。不是正式512、未設新時限，也沒有重抽baseline。 |
| S來源合流 | 796cd282693736af61c1b0d6c8ff91f03437a175 | 相對edc57非evidence diff0，合入既有私有M347祖先；保初次merge128與原失敗index／其後成功的原收據，不宣稱上游原PR已全綠或已合併main。 |
| 123 anchor preflight | S796cd282… | 120個有效／等價錨點唯一、3退役舊錨點0，123項可依原路徑在記憶體套用；43 RESTORED方法與166 core scene存在。**沒有編譯或執行正式ledger**，不能當123 killed／crashed帳本綠。 |
| 完整H7原紅 | S796cd282… | **1200.106348276s timeout**，原RESULT保`exit:null`、`timed_out:true`，killpg SIGKILL。前7方法報ok；第8方法開始後batch-008未完、沒有RESULT／完整suite合計。不能補造exit124、把未完batch當斷言失敗、或稱H7全綠。原每batch600s、suite1200s與16MiB stack皆未改。 |
| N128 gprof診斷 | S796cd282… | actual_exit0／gprof_exit0，6.484310795s；原B9a8584f57be7935604c3bad4c2481945a6ec3d9f的14.914534721s只作舊同法診斷對照，不重抽、不當正式效能判決。 |

N128 的 input.scene（11199 bytes）、stdout.bin（146252 bytes）、stderr.bin（0 bytes）已對原B逐bytes核等；完整比較另存`PROFILE_BYTE_COMPARISON.json`。原stdin為不同本地loadfile路徑（候選78／B82 bytes），沒有宣稱stdin相同。這個N128等價不代表完整H7在時限內。

收件目錄含新K15/H18/legacy98當時已落盤的命令與輸出、graph原SOURCE/BUILD/trace與逐場景原件、N256原件、binding/123preflight、Smerge原失敗與成功原流、H7原件＋未完成temp、profile原ELF/gmon/gprof及現有executors。原環境／路徑／SHA皆沿各收據，不改舊收據。針對graph的原wrapper execution-time hash未獨存等已知限制，仍依binding REPORT保留，不補造歷史欄位。

185-leaf binding與123-anchor preflight兩個目錄沒有另存獨立collector程式，僅保實際REPORT/PREFLIGHT/說明與原Git讀取紀錄；不能宣稱每份收據都有可直接重播的executor，也不以後來重建程式冒當時原工具。

H7 batch-008因原timeout未生成完整結果或原stdout收件，封包只能保存當時實際落盤的stdin／fixture／binary與其他原件；不補造未生成的RESULT或未落盤stream。`exit:null`也保持原工具觀測，不換成推測的程序退出碼。

## H7時間核對與observer工具修復的獨立證據

S796只讀時間核對：已完成000–007產品呼叫848.801342776s；81次編譯／連結18.804766921s；被計時捕捉的9次checkpoint同步Git/API共20.641384512s。剩餘311.857574779s包含未完008、互動產品工作與未分別計時的Python檢查／本地壓縮／fsync等，不能全說成收件，也不能斷言Git/API是唯一超時原因。最初request checkpoint在計時攔截安裝前，沒有逐命令計時，保null。完整REPORT.md/json收錄，不用診斷結果取消原timeout。

本地observer單方法smoke的**實際執行工具**為封存在`local-observer-old-smoke/OBSERVER.py`的舊`87fdcecc5f4db5c15f55e66debece1dee5633220c97bbd24c2cbf61572d76cb6`：1test、exit0、0fail/error/skip，wrapper6.761294205s（內層suite6.592473267s）。它不是完整H7，也不改標為之後的工具版本。

舊smoke後補了checkpoint metadata檔fsync；目前工具為`417eca03461d3189ac0b786fd8fe0e3839dc2a777256cea501bc0820b240499d`。新版本僅對**實際checkpoint函式＋binary fixture**做真archive/metadata/directory fsync、重開archive逐bytes readback，exit0；該RESULT明列test_suite_rerun=false、remote_published=false。包內同時保這個新控制的SHM原件與`/tmp/pr348-local-fsync-control`持久原archive/manifest，不將它稱新完整suite綠。

新工具保原600／1200秒、原測試／measurement主體；只將計時內同步Git/API發布改為先本地fsynced archive，待原計時流程終態後另發布。後續新候選／622 graph不在這個S796包，也不以後續執行回填此原timeout。

舊H28 facts-zero完整原件、舊B graph完整archive與其他已封歷史不重封；binding中的歷史H28欄位只作引用，不宣告S已重跑H6。舊N128/N256 baseline只選本次比較必要的小原件，保舊來源身份。這個包不是全帳本、census、架構四檔、正式native35分鐘或browser通過聲明；候選仍未READY。

封包以RAW.tar.gz及MANIFEST.json保每member路徑、原bytes、原mode及SHA-256，逐member重讀核驗。STATUS保所有原紅燈與execution。所有原檔保留，本工具不刪資料、不改產品、斷言、公理或任何時限；發布與current摘要由主代理審後另做。
