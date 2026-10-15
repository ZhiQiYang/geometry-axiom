# PR237／R12 最終雲端原件

受測固定head：c8250a2c4b94016951f8818a2111283f6c7ac9a7；base main79412a85。
原完整native --build／stack16384：89 suites、2804 pass／0 fail／1具名允許Windows GDI skip，
Node711/711、expected吻合；actual exit0／615.452秒。
前後head與1061選定tracked檔案SHA一致；不是連續監看。
本輪Python19／Node7過，十四個新具名變異各actual1→還原0。
最終native原件包204成員、先前正向e5d4包204、controlled-stop部分包121，逐件核bytes/SHA。
五binary只有最終hash／sidecar，不交付exe bytes或前後binary身分聲明。

B1／R12 M2：256筆Queue.put_nowait交接、writer獨占File I/O；queue/stat與metadata鎖不包IO。
holder先快照、native實際unlock邊界取樣、metadata釋放後發布；重入保留外層身分。
slow sink覆蓋acquire／call／release及外receipt／內bridge；waiter timeout仍有界。
metadata年齡用觀察時點，不用方法入口；發布順序可不同，按實際時間字段分析。
state mutex協調admission／closed／empty檢查，close不吞已accepted事件。
完成marker交代accepted、written、drop/error、sink時間及closedMonotonic；截止後請求不在覆蓋聲明內。
trace模式SIGTERM只有界drain後直接退出，維持terminating SIGTERM不進業務cleanup的路徑。
default-off不設該handler，不換原locks，也不讀診斷clock/UUID/Path；不宣稱零import成本。

B2：只有enabled canvas在啟服前unlink那一個trace並配新run ID；兩跑／預置舊record與其他feedback保留過。
collector拒mixed run、missing/empty/unfinished/loss，同時保留raw；只有預期run ID與完整marker才archived。
最終真bridge／SIGTERM／collector均actual0，28筆、14601bytes，
真實Linux kernel6.18.44、run ID與有效env保留，不是WSL或完整canvas。
R12 M1：server旗標關閉與P-107獨立常開browser observer分開；Node off-flag證明observer仍讀一次clock、
回傳原Promise，正常CDP_RESULT新增兩欄位仍存在，不把server-off測試擴稱全部browser輸出不變。
B3：正式WSL canvas部署／artifact發布與固定最終整合head的native＋六browser未驗，由本機列車完成。

歷史：c9f4 native因補有界關機而自停，actual-15／363.902秒，來源前後同，121部分原件不當全量綠。
e5d4完整actual0／628.527秒、2802/0/1的204原件包保留pre-admission-race/，不是最終c825收據。
舊兩次Linux smoke各有原head，pre-bounded-shutdown/及pre-admission-race/smoke/保留。
第一個before-initial慢sink替身重用了closed StringIO，部分red沒有達目標stage；修替身後before.log
五方法七個具名失敗actual1（2.048秒）才是有效baseline，原初錯誤未抹除。
shutdown-before及race-before都保留actual1；不把已知中斷／舊head改成最終結果。

相對合入main，C／SSOT／白話／正典／BACKLOG／決策／帳本無作者差異；沒有新可執行test檔，既有suite19及Node711。
mutate無新覆蓋（本輪負控制不算C ledger新增killed）；GEO-219無新入口。
CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。
未跑WSL、不合併PR、不force push、不關PR或issue，維持draft。
