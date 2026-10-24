本 PR 接替 #337，保留 #299+#316、#314 題3比較器、已核可的 #318 閱讀 A 與 #323 memo 修正。本輪在 L 之上加入 K edge probe、#339 faces／#340 noWood 與 #343（含 #341／#342 祖先）；**U 不含 #346、#347、#348**。**仍不可合併：P-189 完整比較、#323 跨版本比較、#323 N64/main 效能門檻與 required CI 仍紅。** 不以獨立 timing 或歷史收據改判。

| SHA 欄位 | 精確來源 |
|---|---|
| 目前合流產品／測試來源 U | `ca7838e0f4950452b9befcf40899d606db9b81fa`；本輪已普通 merge 並 push 固定 |
| 目前證據 head E_U | `4d0ef8dee14873256efae1ee646c01d8dcfe947f`；含 U 五stage終態小原件；U完整raw封包尚未公開，不能借用L全包 |
| 上一輪完整驗收來源 L | `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`；以下既有正式實績均保原 execution SHA |
| L 完整證據 head E_L | `1952b0ae604291a2ec447a5cc684d6ab91306779`；已公開五份性能全包 |
| 原17方法 probe 來源 S_probe | `a543eef67b81f8d8800f32d5dc4a5641840d2943`；已普通 merge 進 caf6，不能冒 U 全套驗收 |

### 唯一 current-state 矩陣

**目前合流來源 U 的完整帳本、四檔架構收據、native、六 browser 與受影響專項尚待重產／重跑。** 三個架構原裁判已有同產品closure的新原終態，精確execution見下列；四檔尚未重產。 U原#323五stage已各跑一次並真終態；下表同時列出U當輪結果、其餘待驗狀態與最近L的原終態；L 的綠燈沒有移標成 U 綠燈。CLI、stage 與數值門檻分開，peer 核對數不是產品測試。L與本輪U的單一#323 driver均保 `all_required_stages_completed=false`、`full_acceptance_passed=null`；U原`ABC_result` key不存在，compare後段audit因assert未達；原八stage中的required-eight／PF3／native三項尚未跑，不冒完整通過。

| Gate | 目前 U | 最近原結果（execution L，另列者除外） | 範圍與限制 |
|---|---|---|---|
| 全123帳本／tracked check | U尚未重產；前一caf6原check1 | tracked、完整CLI、core-map、external-check皆0 | L為114 killed／5 equivalent／M20原允許crashed／3 retired；120 execution heads皆L，tracked JSON保原b6。caf6新增產品／測試後原check1：120 stale／3 retired，原紅與完整輸出保留；未冒U有效帳本 |
| 完整native | UNRUN at U | r2 CLI／workflow／CI35／outer全0 | 230列恰各一次；5309=5308pass+0fail+1允許GDI skip；Node737/737，1819.561s<35min。r1四ENOENT原1保歷史 |
| canvas | UNRUN at U | 0 | 2267 assert、85 golden相符、零skip；P88=143、P73=69，1718.884882s<35min。唯一例外為P38故意fb-auto-probe，原EXPECTED檢查綠，無UNEXPECTED |
| assembly／documents／grid | UNRUN at U | 各0 | 150／47／356 assert；documents八截圖。assembly與grid原partial模式不比golden，沒有改成完整canvas |
| space／timber | UNRUN at U | 各0 | 原242／79 assert、八／五組完整；timber job不替代P52耗時量測 |
| P52呈現耗時 | UNRUN at U | formal／verifier／driver／outer全0 | main/fix/fix/main，每側16筆；main中位218.2650215ms、fix176.218242ms，ratio0.807359。原fix≤main成立，無+5寬限；五控制normal/delay 0、revert-delay/wrong/missing 1均符合原判準 |
| Q38 | UNRUN at U；本輪應44案例 | 原CLI／driver／兩outer全0 | L為42=41 killed＋SPM24 equivalent、native27／model20 baseline零skip；不能移標U。U納入#342，應44；#342歷史S=eb846c345881cc6fc73a53c457a291175365b88c曾44=43 killed＋SPM24，U須另跑。原600／900秒與既定排除不改 |
| §7 card-reference／axiom | UNRUN at U | 0／0 | compiled baseline43、53刀assert1各restore0；axiom baseline44、V01–V05各assert1各restore44綠，原table不縮 |
| P-189完整比較 | UNRUN at U | **CLI／driver／outer1** | base `3e600772`對L。126組相同後第127組首差異中止，175未完成；原full內timing未啟動。精確assert見下文 |
| P-189獨立timing | UNRUN at U | CLI／driver／outer0；四數值門檻綠 | main `adbaebf9`／base `3e600772`／L，36samples；N16/32/48/64原receipt fix/main約1.101333／0.958790／1.277641／1.371567，皆≤2。dump_count=0、overall_P189_passed=false |
| #323 fixed-three／required-eight | UNRUN at U | 原0／0 | fixed-three原13/22/15由native完整module覆蓋；R8八列676是Python tests、C檢查點與core場景混合單位，零skip。619份複製logs含歷史，只計當次八列 |
| #323 PF3 | UNRUN at U | 原CLI／stage／driver／outer全0 | baseline20／19刀指定AssertionError 1／restored20；21次build invocation產42binary，不虛構42份獨立compiler OS退出碼 |
| #323 prepare／build／compare | **execution／CLI 0／0／1**；175 scenes／350 runs後三stdout差 | **0／0／1** | base `b74f9a2`對L；175 scenes／350 runs，三個具名stdout差，前後同L clean。原compare中斷後ABC_result未設定，不冒後續完整audit通過 |
| #323 timing | execution0／**CLI1；N64 fix/main=1.429347781620555>1.3**；N16/32/48 fix/base=0.9999532918／0.8129671517／0.8062760349皆綠 | stage execution0；**原outer CLI1、N64目標false** | N16/32/48 fix/base約0.998983／0.811880／0.806587均≤1；**N64 fix/main=1.4282954375>1.3**。CLI1含累積compare紅與數值紅，不改分母或門檻 |
| #323 profile | execution0／CLI1；N32=82668／N64=364369，ratio4.4076184255≤4.5綠 | stage execution0；原outer CLI1；呼叫比門檻綠 | N32 geo_eval_source=82668、N64=364369；64/32=4.4076184255≤4.5。outer1仍帶累積compare／性能紅 |
| #323 whole-memo撤回／恢復 | UNRUN at U | 原driver／outer0；withdrawn1／restored0／隔離ABC0 | calls比撤回6.0538332063>4.5、恢復4.4076184255≤4.5；三phase execution_complete true，隔離175/350原audit tuple一致。不解除formal compare1或N64載入性能紅 |
| reader三條 | UNRUN at U | 0／0／0 | 原sync生成、--check、reader unit51；各原CLI退出碼0 |
| RC-run builder／checker撤回 | UNRUN at U | 各0/1/0 | 各以原單一方法、六assert；未拿native或全帳本的其他控制替代 |
| #314六suite／Node inspector | UNRUN at U | Python103全pass；Node aggregate737原0 | Python未另存per-child OS碼，依原裁判契約支持0；Node13為parent1+nested12通過事件，沒有獨立Node13 process exit |
| 閱讀A native／oracle | UNRUN at U | 7／14原module全pass | 依native原裁判契約支持child0；typed facts不證明#335真CLI初放已可用 |
| 閱讀A mutants-only／完整quick | UNRUN at U | 0／0；outer0 | 9402矩形逐毫米、14208二維、凹角579×8、step410×8／mirror820×8、odd1872、t10 mirror392、528／1056正例全保。原t4族六筆C11_MAIN_NOT_BUTTED另案，未改判或宣稱修復 |
| 架構三原裁判 | 同產品closure三裁判PASS；四檔待重產 | physical execution `b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5`，原0／0／0 | 原205／18；334sources、6trusted、798edges、diagnostics0。原Git diff證execution E與U全非evidence相同；未冒U直接執行，也未宣稱manifest／scan／report／receipt四檔已新生成 |
| required CI | **U及當時E各七job failure，B3未解除** | U run`40058889738`／physical E=b09 run`40059064935`，各原failure | 兩個實際head原steps0、runner空；各job原failure annotation為付款失敗或支出上限，另保Ubuntu遷移notice。沒有假定雲端gate已獲正式替代接受；本輪沒抓signed logs |
| K edge probe 定向與整刀 | 未在 U 重跑，待最終 closure 核對 | S_probe 原17方法／0 skip，suite0；whole 0/1/0 | 原56 compile/link全0、43 native；成本21→31→21。只證定向契約，不證新N64載入門檻；R1目錄與exe撞名原紅保留 |
**允許skip沒有新增。** native唯一為`py:test_gdi_contract`，Linux缺compiled Windows GDI harness；Q38的既定registry排除不是新增skip。Chrome156.0.8078.47、Node24.19.0與NotoCJK可用；原斷言、golden、時限與16MiB stack不放寬。

### 原比較紅燈與待決界線

P-189原`p189_verify.py:195`是`assert raw['base'] == raw['fix']`，訊息為`AssertionError: dump 不同：repo-_role_priority_mutant.scene`。它比較完整load回覆＋dump的stdout；兩版均reject、第二行完整dump相同，L的第一行error與stderr多了`——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm`。不能把訊息的「dump不同」誤寫成幾何dump不同，也不能把126組通過寫成175組完成。

#323原`verify_linux.py:156`的`assert not failures,failures`列三個stdout差：`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。它完成175／350後才判紅，與P-189的base及中止範圍不同。

K edge probe 的17方法與整刀已通過；本輪U五stage真終態1，原順序execution為0／0／1／0／0、CLI為0／0／1／1／1。新U的N64 fix/main=1.429347781620555仍大於原1.3；小N與calls比通過沒有解除它。原36樣本全部保留，不重抽樣取綠。U compare也保同三個具名stdout差與`verify_linux.py:156`原assert1；`ABC_result`尚未建立，compare後段audit因assert未達；其餘required-eight／PF3／native三stage尚未跑，不宣稱完整graph／audit通過。

現行I22及既有正反例要求定位邊／超出區間；未取得診斷版本界線或comparator裁決前，保留完整原差異與exit1，不刪診斷、過濾、正規化或放寬exact。歷史F的同列車memo-only因果證據不能取代跨版本門檻。待決選項及原版本來源在`evidence/geo337-train-20261024/QUESTIONS.md`的Q-323-ABC／Q-P189-EXACT。

### CI與原件公開界線

最新已讀#338審查仍為2026-10-24 00:39:37 UTC／head f05e7cf；它是審查歷史，不代替本輪CI。新讀 U=`ca7838e0f4950452b9befcf40899d606db9b81fa` 的run40058889738與當時 E=`b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5` 的run40059064935，各七required jobs均failure、runner空、steps0。十四個failure-level annotation皆為付款失敗**或**支出上限，另有Ubuntu遷移notice；API不分兩種帳戶原因。本輪未抓signed logs，沒有把舊Forbidden或signature遮罩套到新run，沒有環境已修或替代驗收已接受的主張。

本輪U五stage的原命令、CLI／execution、receipt、36樣本表與比較小原件，於E_U的 `evidence/geo337-train-20261024/current-U-323-terminal-status` 公開；這是終態小件，不是完整graph／profile原流封包，完整raw仍在雲端。原TERMINAL_SUMMARY的published:false保收件當時原值，公開事實由新E與publisher原RESULT證明。原v4 outer的source_role/source_sha依argv中的--base啟發式可能標base，原欄不改；產品綁定以明確U acceptance_sha、inner原receipt及前後Git guards為準。

新三裁判與兩run共124份原件／351,354B已於先前E76ba的 `evidence/geo337-train-20261024/current-U-architecture-and-ci/` 公開。舊f05/e9完整原讀65次（63 exit0與兩log Forbidden1）、兩signed-log signature遮罩和原review仍留歷史原件；Forbidden不證明log不存在。

以下 L 相對路徑均以 E_L=`1952b0ae604291a2ec447a5cc684d6ab91306779` 的 `evidence/geo337-train-20261024/` 為準；不冒 U 新執行：

- 已公開完整原件：`final-L-ledger-complete/`、`final-L-native-r2-complete/`、`final-L-browser-canvas/`、`final-L-browser-assembly/`、`final-L-browser-documents/`、`final-L-browser-grid/`、`final-L-browser-space/`、`final-L-browser-timber/`、`final-L-Q38/`、`final-L-section7-cardref/`與`final-L-section7-axiom/`、`final-L-required-eight-complete/`、`final-L-pf3-complete/`、`final-L-readers-RC/`、`final-L-reading-a-complete/`與`final-L-architecture/`。
- 五份完整性能原件已於`final-L-performance-complete/{p52,p189,p189-timing,geo323,memo}/`公開，tar共74,496,801B，3150／3455／261／7485／5501 members；各附原PACKAGE、SUMMARY、完整collector outer及actual peer。完整RAW_INVENTORY在各tar內，發布manifest另保其hash與locator，不以小摘要取代原流。原status-only資料保歷史；原PACKAGE的published:false是封存時原值，不回寫，發布事實由此E及publisher RESULT證明。ELF僅省包內payload而留原址/hash；五包產品結果仍為P520、P189full1/timing0、#323 compare1/N64目標false、memo0，沒有改判。
- P52 collector先因Chrome IPC、再因原ledger附加欄位各exit1；v3封包保兩次失敗、45個IPC metadata、65 annotations，六ELF只省包內payload，未重跑產品。R8／PF3原v4外層因argv含`--base`誤標source_role/source_sha，原欄位不改；acceptance_sha、--sha L、真inner與Git guards另綁L，診斷在`final-L-required-eight-pf3-tools-and-peer/`。
- 歷史失敗與沿革不重寫：`final-L-native-r1-environment-failure/`、`ledger-b6-complete/`、`review-b6-response/b2-diagnostic-originals-and-peer.tar.gz`。#314既有SSOT例外已採納，後續精確有序補句的寫入差額仍列QUESTIONS；Reading A不冒#335初放能力。儲存維護及其他PR的獨立SHA不列本PR產品通過項。

### 合流與獨立工作線

#339 source F616 已公開 E=`8f39025be6708bd9d58e576ed5b349b7ef628624`、body D=`283d1e245f724e13644a1379cba5cd34f3dae9d9`；#340 source S175 已公開 E=`04959e04c334ceaf03f865514f76b1cac8ee91f2`、D=`db8bf2289f8ad931c00924193e238e621f970e05`。#340 的原 selected aggregate 13／13 strict0 屬 S175；#339 的142與三刀沿用原 F38da execution，493＋5個原來源 Git entries完全相同、非evidence僅ledger改變，沒有虛構 F616 新執行。兩線完整正式驗收、帳本與CI仍不齊；不列 U 的產品通過項。

K probe 完整原件已透過一般 merge 納入 E_U 的 `evidence/geo323-edge-probe-a543eef6/`；execution 仍為 S_probe，root另保 source binding 與原 actual peer。caf6原帳本check1全流在 `evidence/geo337-train-20261024/probe-evidence-and-ledger-freshness/original-caf6-ledger-check/`。維護兩個完整包也已於歷史 E=`2787ee3167deec7588bde26265152bcf6dc4a939` 公開，僅為保全與儲存收據，不是產品 gate。

#348 F0f695866 留在獨立分支繼續，不納本輪U。其原整批終態1，W7真7／7、零skip、exit0；H7為2PASS／5RED（三個 sentinel 測試缺陷與兩個512 load原600秒Timeout），三helper各 fixed／withdrawn／restored皆1／1／1，沒有完整有效三態，也沒有放寬時限或標綠。secondary已釋；新U的#323原五stage也已真終態並釋雙鎖。#345原六phase已真終態0、各19／零skip，獨審2493／0；完整包已於獨立 E99646d418bc5e886a92bfdabe33e68780e88fe3b 公開，結果歸其獨立線OUT，不列本列車通過項。五stage工具已靜審65／0；薄source準備真0（447檔／4,290,370B、U clean、nlink1唯讀與獨立index）。新U五stage原終態1與兩個產品紅已列唯一矩陣；其餘新U正式項目仍未跑。後續帳本／架構整份重產後才固定L2。這些進度不解除四個原阻擋，也不是 READY-TO-MERGE。


本輪原件發布補記：新增四組 archive 儲存保全已於 E_U 的 `evidence/geo337-train-20261024/maintenance-additional-four-archive-groups/` 公開，原包359949B／1597 members；不是產品gate。#345已普通推送完整六phase原件 E=`99646d418bc5e886a92bfdabe33e68780e88fe3b` 與正文 D=`c5515c14ac9cb59d147563f3dd75dbde5b75ca4e`，沒有移作U驗收或標READY。
