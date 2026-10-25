# F9 六個 browser 已全綠；native 仍紅，專項尚未閉合

以下唯一矩陣是目前狀態；最末完整舊文只留歷史。六個browser均在F9原正式流程取得exit0。assembly完整原件已於E3447遠端驗證；本批提交其餘四browser、§7 axiom及PUBLIC comparison完整正式原流。本批出版與遠端逐blob驗證均exit0，190個unique blob完整核對；封存0不代產品0。

本 PR 接替 #337，整合 #299+#316、#314 題3、#318 閱讀 A、#323、K 索引及 #339/#340/#343（含 #341/#342）。容量仍64，未合 #344–#348。**維持 draft；native 尚紅，完整驗收未完成。**

以下是唯一 current-state 矩陣；原門檻、golden、時限不變，歷史結果不移標。

| 身分 | 完整 SHA |
|---|---|
| 最終來源 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| 帳本生成／R8／成本執行 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad`；F8→F9僅帳本／evidence |
| 已驗遠端 checkpoint E／assembly 完整 package head | `3447ab384c4c777f9d2685128044b9b9d043e17d`（其前一checkpoint為`60909ad5062c6bc6f072442f5c2957b08b15f443`） |
| 目前證據 E／四browser、PUBLIC、axiom完整package head | `249a05ed4c8a085bdf3353ac781638f2a9b3d460`；publication exit0、remote verification exit0，190個unique blob全bytes／SHA256／Git OID核對通過 |
| 架構四檔原執行 M／H 定向執行 S | M=`6e50aef65513b7b38f93228919272c6d40d6c196`；S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7` |

| Gate | 實際結果／未完成項 |
|---|---|
| 全123帳本／tracked check | F8完整重產0：114 killed／5 equivalent／M20 crashed／3 retired。逐byte採入F9，tracked check0、stale0／blocked0 |
| 完整 native | F9 exit1；35分鐘裁判0（1846.506872秒）。230登記列；5327 pass／1 fail／1 skip。唯一紅為下述 #314 assertion |
| canvas | F9 原workflow／wrapper exit0，35分鐘裁判0；1723.223173秒。完整2267 assertions、零fail／skip；85段golden相符，P73=69、P88=143；原件peer170/0 |
| assembly | F9第二次原workflow／launcher／sampler／host exit0；150 assertions（P77 134＋P82 16）、0 fail／skip，188.8433秒≤原15分鐘。actual peer237/0。首次環境exit1完整保留，詳下文；[兩次完整封包](https://github.com/ZhiQiYang/geometry-axiom/tree/249a05ed4c8a085bdf3353ac781638f2a9b3d460/evidence/geo337-train-20261024/F9-assembly-terminal/)已於E3447公開並完成遠端驗證，封包actual peer6741/0 |
| documents | F9原workflow／launcher／sampler／host exit0；47 assertions、0 fail，8張截圖hash全對；63.197160秒≤原10分鐘，actual237/0；本批完整原件見[F9-four-browser-terminal](https://github.com/ZhiQiYang/geometry-axiom/tree/249a05ed4c8a085bdf3353ac781638f2a9b3d460/evidence/geo337-train-20261024/F9-four-browser-terminal/) |
| grid | F9原workflow／launcher／sampler／host exit0；356 assertions、0 fail／skip，P88=143；464.984065秒≤原15分鐘，actual228/0；本批四job完整包 |
| space | F9原workflow／launcher／sampler／host exit0；242 assertions、0 fail，原scope不含timber兩組；209.339秒≤原15分鐘，actual226/0；本批四job完整包 |
| timber | F9原workflow／launcher／sampler／host exit0；79 assertions、0 fail（timber48＋guards8＋font19＋setup2＋health2）；124.531604秒≤原20分鐘，actual223/0；本批四job完整包 |
| Q38 | F9 原完整44項及launcher exit0（14:45:38–14:59:28 UTC），原argv／timeout不變；host終態已保存，完整原件獨審及封包出版尚待完成 |
| P52／§7 card mutations | 各 UNRUN at F9；保留P52原median門檻及完整card mutations |
| §7 axiom mutations | F9原CLI／outer exit0；baseline與五次restored各44 tests、零skip，V01–V05全killed。原件peer428/0，本批206檔完整封包與actual1475/0見[F9-axiom-original-complete](https://github.com/ZhiQiYang/geometry-axiom/tree/249a05ed4c8a085bdf3353ac781638f2a9b3d460/evidence/geo337-train-20261024/F9-axiom-original-complete/) |
| P-189 full exact／timing | 兩項 UNRUN at F9；歷史exact紅保留，三差裁決未明示延伸本項 |
| #323 R8五stage | F8原outer1；execution=0/0/1/0/0、CLI=0/0/1/1/1。量化門檻綠但exact三差仍1；ABC_result缺席、full_acceptance=null |
| #323 新comparison單項 | F9 outer／stage／audit exit0；175場景／350 base-fix列、700 ordinary＋trace原CLI完整保留。actual17231/0、對抗10144/0；本批PUBLIC五包僅排除一份無關GET /user完整profile，範圍與限制見下。不移標F8 R8結果 |
| #323 required-eight／PF3／native後段 | 各 UNRUN at F9；R8五stage不能代完整八stage |
| #323 whole-memo／恢復／隔離ABC | 各 UNRUN at F8（原R8正式來源） |
| reader三原條 | F9 exit0/0/0，207 clauses／1261 blocks，unit51/51、零skip；獨立可寫269葉F9來源逐byte核對且前後clean，nativeROOT不變；actual peer1972/0 |
| RC builder、checker反證／#314六suite及Node inspector／閱讀A native、oracle、mutants-only、完整quick | 各獨立專項UNRUN at F9；native總表不代完整專項 |
| 架構三原judge／四檔 | F9 exit0/0/0、205＋18全ok；334 sources／6 trusted／798 edges／0 diagnostics。四檔為M原收據經F8採用，F9逐blob相同 |
| #341四類成本 | F8 fallback-only exit0；14 cases全樣本。N64 none wall +6.77%、dense −29.72%；未判性能接受，未解除完整優化撤回B1；新F9完整撤回尚未實跑 |
| H局部修正／反證 | S：14/14 exit0、零skip；work反證0/1/0，清零calls=0/2/0、bytes=0/255168/0。O0定向不代O2性能 |
| required CI／替代驗收 | OWNER核可同一final SHA七項＋專項全綠替代；目前六browser均0，但native仍1且多項專項UNRUN，替代條件未成立。未宣稱新證據head的Actions已啟動；不自行合併 |

native精確失敗：`test_geo314_commit_paths.Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，assertion `I24 submission policy must not change K files`，原額外stdout為 `geometry-core/kernel/source.c`。已定位固定歷史基底的測試範圍問題；嚴格修正草案尚未採進F9；v2外層real-index守門失敗保留，v3改用完整私有index後，full11 fixed／withdrawn／restored 0/1/0與四種K負例全通過，外層exit0、restore errors空，獨立actual349/0。未修改F9或免除斷言。唯一允許skip是Linux缺compiled Windows GDI harness的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`，實際1項。native原件獨審2208/0、包6191/0只證收件正確，不改正式exit1。

R8原36樣本不重抽：N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`（各≤1）；N64/main=`1.2846970752586067`（≤1.3）；source calls64/32=`4.407618425509266`（≤4.5）。原outer1與350比較原流保留。

批准來源已直接經GitHub API核實：[2026-10-25 10:39:52Z原留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)。`GET /user`與comments API均HTTP200/exit0，已連接帳戶與作者皆`ZhiQiYang`，id`59477728`、node ID完全相同，留言OWNER。原文明列【使用者裁決】與「A 接受這 3 筆」、「延伸到所有 PR」等選項，適用說明由Claude整理。API證明帳戶，不能證明真人手動輸入；也不是本任務B′問題的直接回覆。依管理代理明示的帳戶核實條件，按此當次批准接續。

Q-323-ABC只准三個指定場景各自逐字的新增定位邊文字，其他bytes／返回碼／完整有序圖／五guards與效能門檻不變；第四差、錯字、位置或次數不符仍紅。依核可白名單執行的新F9 comparison單項已於12:14:21 UTC取得outer／stage／audit exit0；175場景／350 base-fix列／700原CLI完整性actual17231/0、對抗peer10144/0已完成。三指定場景各stdout／stderr的六次精確插入保留，strict tuple without exceptions仍false；有序graph逐byte及五guards依原scope核對，不能改稱完全沒有字串差。本批提交PUBLIC正式比較封包（輔助完整profile留雲端），遠端交付以原出版收據為準。原R8 outer1與全36樣本保留，不換base、不重抽，不擴及P-189，也不把此單項0當作required-eight或整份驗收通過。範圍文字見main [`405f8c5e…`](https://github.com/ZhiQiYang/geometry-axiom/blob/405f8c5e1a637a16cbe47470faf5ae1fa02b8676/決策佇列.md#L841)。CI替代須每張PR同一可解析final SHA七項與專項全綠及完整證據；stale-only帳本例外不含survived／invalid／blocked。本輪帳本check仍0，不需援用，也不自行合併。

最新已讀[審查原文](https://github.com/ZhiQiYang/geometry-axiom/blob/fd35d1415/handoff/pr-reviews/338.md)：2026-10-25T14:35:15Z、head3447ab3。仍保留B1 native測試範圍紅燈、B2其餘正式清單未閉合、B3與main衝突；新增C1要求區分checkpoint E609與assembly完整package E3447，本表已明列兩者，本批新package head在推送驗證後同步寫進正文。12:47衝突說明與唯讀分析一致：main405f8只新增決策文件28行；將正常merge，完整保留列車10/24與main10/25原文（含列車前六行條文寫入綁定），不改既有鎖定內容。目前尚未merge、不移標F9收據；採納測試直接讀此文件，整合後須跑受影響項。維持draft，未標READY-TO-MERGE。

原件索引：[F9 native完整原流與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/F9-native-terminal/)（1374 members、13,895,527原bytes，gzip SHA256 `42217b1827d010e8eac017b95799a24910835c202aa1e32a0137cfee32e95d5c`）；[F9帳本採用／架構／F8成本](https://github.com/ZhiQiYang/geometry-axiom/tree/782bc80b0a13ecd19670f5285a8edb1824349686/evidence/geo337-train-20261024/F9-initial-gates/)；[R8完整五stage](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/full-R8-five-stage-raw/)與[全部歷史進度／證據連結](https://github.com/ZhiQiYang/geometry-axiom/blob/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/PROGRESS.md)。


[Reader完整原件與API批准核實](https://github.com/ZhiQiYang/geometry-axiom/tree/c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc/evidence/geo337-train-20261024/F9-readers-and-verified-decision/)：582原件／11,063,364B分為兩個封包，逐member回讀及獨審7041/0。原reader首輪三個reaper環境變數缺漏的啟動前exit1全部保留；只補GEO261_REAPER_LOG後以原argv完成三項。原實際外層timeout=None與警告保留，不冒稱另有已執行的timeout守門。API完整comments原流公開，無關私人帳戶profile留雲端，以身份欄位與完整原回應hash綁定；獨審106/0。


[F9完整canvas原件與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/aea7456bc8d48e3a9a8038eb598b4e0d018f8fdb/evidence/geo337-train-20261024/F9-canvas-terminal/)：原workflow在11:22:04.734796–11:50:47.957901 UTC執行，原35分鐘界線2100秒未放寬。P38故意注入fb-auto-probe，原uncaughtBrowserExceptions=1且標EXPECTED、unexpected=0；P53 API故障與被取消的網路請求亦完整保留，不能改寫成診斷總數0。原件裁判170/0與封包5396/0分列，封包peer不代產品gate。四包保留656個regular檔45,780,854B＋4個symlink，全部ELF／cache／profile／診斷均收；只將5個SOURCEPLAN Git metadata／mutable latest葉作精確hash-only及1個Unix socket作metadata-only，原payload保留，私有index完整封存另案。這是一輪F9完整canvas通過，不外推其他browser或重複穩定性已驗。




本輪雲端共同容量配置已實際執行：既有`/dev/shm`為tmpfs，沒有增加掛載、配額、付費或安全設定。各job獨立source/gitdir/index/port/TMP/profile；共用經逐byte核對的唯讀seed。原WS與TMP接近滿載，故新出版repo改在獨立SHM私有Gitdir，單向唯讀借用舊objects；bootstrap31條CLI真0、actual465/0，舊WS metadata/status/PROGRESS前後相同，零既有Git objects複製。後續train只由主代理於此私有repo正常push；所有SHM原件與新objects受保護，揮發性副本不算已交付。每份完整封包必須正常push後，由GitHub API下載完整raw並核bytes/SHA256/Git OID；assembly完整封包已在E3447逐blob遠端驗證通過；本批其餘封包是否已完成遠端逐blob驗證只依實際出版收據，不能以本段或原collection0代替。

assembly第一次原workflow在13:30:01.714515–13:31:27.087503 UTC exit1（85.372989秒）：Chrome明確`FATAL: Socket path too long`→`no CDP`；完整socket literal113B（含NUL114）超過Unix socket108B容量，0產品assertions、golden未比較。建置與前後來源guard均0。第二次只更換fresh out/storage，縮短socket為104B（含NUL105），原sampler/launcher/driver/argv/15分鐘時限與判定未改，結果150 assertions全部綠。原partial assembly scope不冒完整canvas golden。P77故意注入`Injected lost success response`負例仍完整保留，不能把預期transport紀錄刪掉。

第一次90個資源樣本、最大間隔1.000906秒；第二次193個、最大間隔1.013863秒。共享SHM取樣used最大分別209,575,936B、229,765,120B，OOM／oom_kill均0；第二次同期間有出版準備增量，故這是共享掛載取樣峰值，不是連續真峰值或單job獨占峰值，也不能外推R8性能。後四job完整socket bytes已逐literal核對含NUL≤108。

#344另線已正常推送來源`9aec9a32630fc65f94c53d49e99969e546574d6e`、證據`df39d1933402c76b2f8b35ca013412daf16ed4c9`、正文`cbb1aa30b83d1b368ce1cb27885a39003bc58fed`，修正CDP exclusion LF hash並保留三原架構judge／反證原件。該線仍未合入本列車，strict9的歷史綠不替代其完整canvas/native/其餘未跑清單。



[F9 assembly兩次完整原件與封包獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/249a05ed4c8a085bdf3353ac781638f2a9b3d460/evidence/geo337-train-20261024/F9-assembly-terminal/README.md)：三包保留828個regular檔35,366,094B＋5個symlink，gzip合計8,121,472B。首次環境exit1／第二次正式exit0與兩次原15分鐘gate0分列；兩次launch、runtime／build ELF、profile、screens、sampler、原commands／環境／mounts全收。只將5個sourceplan Git metadata／mutable latest葉作hash-only、1個Unix socket作metadata-only，seed/source payload原地保留。collector原0、封包actual6741/0不代產品gate；原828葉只在三包中，不另逐葉重複入Git。



本批四browser完整原件共2411 regular／125,944,310B＋8 literal links，9 gzip共31,278,535B；原24個scope全葉、原各10／15／15／20分鐘時限與前後來源守門均保。獨立封包actual17156/0不代產品判官。20個SOURCEPLAN Git metadata／mutable latest葉明列hash-only、2個Unix socket metadata-only；所有regular runtime／ELF／profile／診斷原流都收錄，未刪測試或省略失敗紀錄。共享SHM取樣used最大：documents262,922,240B、grid320,098,304B、space383,094,784B、timber416,649,216B，OOM均0；這是含其他出版I/O的共享掛載觀測，不是單job連續真峰值，也不外推R8。

§7 axiom完整原189份產物加17份具名工具／host／peer，共206 regular／12,652,356B，單gzip 2,548,379B，SHA256 `b7d6aea19c5bcc81770c06ee8982d4687d80bd7e6f7a7dabd71b0ac6badbd3b2`。collector0與獨審1475/0只驗原件，原正式44＋5 mutants沒有重跑。

PUBLIC comparison保留700個正式CLI、另12個Git查核的全部1424 stdout／stderr、350份有序圖與全部比較輸出；只排除無關輔助`GET /user`完整profile一葉（2795B，SHA256 `b8939b00b88600ac7c4e96dcb45f38d75ffa5b5eddf7a3fa3f24d8109f6d9f29`）。原私有五包留雲端、不改原bytes；公開版只重封part4，另外四part引用原完整bytes。API原argv／exit／hash與安全身份witness保留，但公開版不聲稱含該完整私人guard輸入、不能冒稱全部authority輸入可獨立原地重播。scope1463/0、collector26/0、actual159/0及獨立actual審查無阻擋。新唯讀reader v1因host JSON層級誤讀KeyError exit1原件保留；v2修正後0，這不是產品撤回／恢復反證，collector與正式比較沒有重跑。原R8 outer1及36性能樣本完整保留，不擴白名單至P-189。

#314暫態反證（F9＋明列暫態測試修正，沒有產生產品commit）：full11 fixed0／withdrawn1／restored0，source.c、candidate.c、staged新K與untracked新K四種違規各1、恢復各0。外層仍exit1：`original ROOT index bytes/inode/metadata untouched`；index由SHA256 `3916c388a49d66327ebb120d2ddb10f40e043bc8932e86f386764743a2868228` 變為 `ad03de61dae2e621503443050fb230baf80e2192bd84662140c9e73d597163c2`，大小同為6,575,523B、inode改變。完整after副本與原流保留，未以reset回寫。時間落於restored-existing-K-1、早於private staged add；現有證據不能完全確定歷史寫入者，不能假稱已重現病因。v3工具從首個Git指令起採完整私有index／objects，逐command嚴格保護real index；正式原執行exit0，full11為11 pass／10 pass加精確source.c FAIL／11 pass，四類K負例各1→0、無新skip／ERROR，source恢復一致且restoration errors空。獨立actual349/0完整核對38條命令與76份輸出流，不是35條；仍不宣稱已找出v2歷史index寫入者。本批先公開終態與獨立審查，兩次完整原件另行完整封包出版。這不把native1改綠，也不代最終修正SHA的完整native、mutation check或架構驗收。

下一步採入已經反證與獨審通過的#314嚴格測試修正、封存已exit0的Q38完整原件並完成P52／card／P-189／required-eight／PF3／memo／RC／閱讀A等未跑項，依已核界線正常merge main並逐字保留兩側新增決策段，再固定新final跑受影響驗收。未force push、未合併PR、未宣稱全專案完成。


完整歷史矩陣僅保留於 [PROGRESS.md 的歷史區塊](https://github.com/ZhiQiYang/geometry-axiom/blob/249a05ed4c8a085bdf3353ac781638f2a9b3d460/evidence/geo337-train-20261024/PROGRESS.md)，不與上表並列為 current state。
