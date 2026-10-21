此包為未採用的 CC=gcc 歷史重產輪，不是最終帳本。其來源 A=`7159530c0e494d3211e6ab1764eb691137211707`，同一 CC=gcc 環境內 full/--check/--check --killers 均0；但主代理在 L1=`cd4ac98f44174729fb3a2f1c291c6c258c9a239a` 執行 CI 預設（CC 未設定）的 --check 得到 exit1，57個核心案例因 compile command changed 成為stale。L1未作為最終產品來源，後續需以全新CC未設定重產帳本取代，不能改寫原收據或放寬檢查。

工具把字面argv與其JSON hash納入身分：gcc與cc雖在本機指向同一實際GCC二進位，仍是不同命令。既有CI workflow不覆寫CC，mutate.py及binaries.py的預設皆cc，因此第二輪已在同一公開A以全新worktree/cache/results/TMPDIR、移除CC及PYTHONOPTIMIZE完整78重產。

原 ledger-A 目錄只更名為 ledger-A-gcc，內部全部檔案bytes/hash未變，兩份manifest檢查均0。包內複製收據記錄舊目錄位置與原README中對L的未來式均為歷史原件，請以此外層狀態說明識別。L1的P-189僅建立準備資料，沒有執行任何自測、build、equivalence或timing，後續須使用真正最終L的新目錄。

共用 baseline 精確補正：凍結包 ledger-A-gcc/README.md 第 5 行的「每案 baseline 與 restored 皆完整跑 27」不表示 baseline 跑了 18 次。bridge 在 mutant 迴圈前實跑一次 27/27 baseline，18 案各引用同一份成功收據，再各跑自己的 mutant 與 restored 27/27。core 則在 mutant 迴圈前建立共用成功 baseline 165/165 收據，57 案引用該份收據，並非每案重跑 baseline；官方工具允許 blocked 時最多三次重試且只留最後收據，原件不足以獨立數出 core baseline 子程序的實際啟動次數。此補正不修改凍結原件，也不增加任何測試成果。來源 A 的 tests/mutate.py:1303–1338、1393；tests/mutation_bridge.py:455–471、474–478、490–495。
