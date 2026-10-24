本 PR 接替 #337，整合 #299+#316、#314 題3比較器、已核可的 #318 閱讀 A 與 #323 memo 修正。**仍不可合併：P-189 完整比較、#323 跨版本比較、#323 N64/main 效能門檻與 required CI 仍紅。** 不以獨立 timing 或歷史收據改判。

| SHA 欄位 | 精確來源 |
|---|---|
| 唯一驗收來源 L | `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db` |
| 產品沿自 F／測試沿自 S | `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`／`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0` |
| evidence head E | `b621a4fbc3cdea359b3676fb22dc8ef566968b8a`；純證據提交，不是實跑 SHA |

### 唯一 current-state 矩陣

未另列來源者均在 L 執行。CLI 退出碼、個別 stage 執行與數值門檻分欄判讀；peer 核對數不是產品測試。完整包是否公開另見下方界線。 同L清單依各原OUT逐項合成；單一#323 driver的`all_required_stages_completed=false`、`full_acceptance_passed=null`保原值，不能冒成該driver完整驗收通過。

| Gate | 原結果 | 範圍與限制 |
|---|---|---|
| 全123帳本／tracked check | tracked、完整CLI、core-map、external-check皆0 | 114 killed／5 equivalent／M20原允許crashed／3 retired；120 execution heads皆L。tracked JSON保自然生成頭b6，不回寫成L |
| 完整native | r2 CLI／workflow／CI35／outer全0 | 230列恰各一次；5309=5308pass+0fail+1允許GDI skip；Node737/737，1819.561s<35min。r1四ENOENT原1保歷史 |
| canvas | 0 | 2267 assert、85 golden相符、零skip；P88=143、P73=69，1718.884882s<35min。唯一例外為P38故意fb-auto-probe，原EXPECTED檢查綠，無UNEXPECTED |
| assembly／documents／grid | 各0 | 150／47／356 assert；documents八截圖。assembly與grid原partial模式不比golden，沒有改成完整canvas |
| space／timber | 各0 | 原242／79 assert、八／五組完整；timber job不替代P52耗時量測 |
| P52呈現耗時 | formal／verifier／driver／outer全0 | main/fix/fix/main，每側16筆；main中位218.2650215ms、fix176.218242ms，ratio0.807359。原fix≤main成立，無+5寬限；五控制normal/delay 0、revert-delay/wrong/missing 1均符合原判準 |
| Q38 | 原CLI／driver／兩outer全0 | 42=41 killed＋SPM24 equivalent；native27／model20 baseline零skip；既定registry排除不變，原600／900秒子時限不改 |
| §7 card-reference／axiom | 0／0 | compiled baseline43、53刀assert1各restore0；axiom baseline44、V01–V05各assert1各restore44綠，原table不縮 |
| P-189完整比較 | **CLI／driver／outer1** | base `3e600772`對L。126組相同後第127組首差異中止，175未完成；原full內timing未啟動。精確assert見下文 |
| P-189獨立timing | CLI／driver／outer0；四數值門檻綠 | main `adbaebf9`／base `3e600772`／L，36samples；N16/32/48/64原receipt fix/main約1.101333／0.958790／1.277641／1.371567，皆≤2。dump_count=0、overall_P189_passed=false |
| #323 fixed-three／required-eight | 原0／0 | fixed-three原13/22/15由native完整module覆蓋；R8八列676是Python tests、C檢查點與core場景混合單位，零skip。619份複製logs含歷史，只計當次八列 |
| #323 PF3 | 原CLI／stage／driver／outer全0 | baseline20／19刀指定AssertionError 1／restored20；21次build invocation產42binary，不虛構42份獨立compiler OS退出碼 |
| #323 prepare／build／compare | **0／0／1** | base `b74f9a2`對L；175 scenes／350 runs，三個具名stdout差，前後同L clean。原compare中斷後ABC_result未設定，不冒後續完整audit通過 |
| #323 timing | stage execution0；**原outer CLI1、N64目標false** | N16/32/48 fix/base約0.998983／0.811880／0.806587均≤1；**N64 fix/main=1.4282954375>1.3**。CLI1含累積compare紅與數值紅，不改分母或門檻 |
| #323 profile | stage execution0；原outer CLI1；呼叫比門檻綠 | N32 geo_eval_source=82668、N64=364369；64/32=4.4076184255≤4.5。outer1仍帶累積compare／性能紅 |
| #323 whole-memo撤回／恢復 | 原driver／outer0；withdrawn1／restored0／隔離ABC0 | calls比撤回6.0538332063>4.5、恢復4.4076184255≤4.5；三phase execution_complete true，隔離175/350原audit tuple一致。不解除formal compare1或N64載入性能紅 |
| reader三條 | 0／0／0 | 原sync生成、--check、reader unit51；各原CLI退出碼0 |
| RC-run builder／checker撤回 | 各0/1/0 | 各以原單一方法、六assert；未拿native或全帳本的其他控制替代 |
| #314六suite／Node inspector | Python103全pass；Node aggregate737原0 | Python未另存per-child OS碼，依原裁判契約支持0；Node13為parent1+nested12通過事件，沒有獨立Node13 process exit |
| 閱讀A native／oracle | 7／14原module全pass | 依native原裁判契約支持child0；typed facts不證明#335真CLI初放已可用 |
| 閱讀A mutants-only／完整quick | 0／0；outer0 | 9402矩形逐毫米、14208二維、凹角579×8、step410×8／mirror820×8、odd1872、t10 mirror392、528／1056正例全保。原t4族六筆C11_MAIN_NOT_BUTTED另案，未改判或宣稱修復 |
| 架構三原裁判 | 0／0／0 | architecture_contract、test_architecture_contract205、test_product_architecture18，零skip；604輸入與HEAD/index前後一致；Linux manifest／scan／report／receipt四檔按原schema採用 |
| required CI | **run40043471807七job failure** | 實際head f05e7cf；原annotation為帳戶付款失敗或支出上限，runner空／steps=[]。未取得真啟動終態或正式替代接受，B3未解除 |

**允許skip沒有新增。** native唯一為`py:test_gdi_contract`，Linux缺compiled Windows GDI harness；Q38的既定registry排除不是新增skip。Chrome156.0.8078.47、Node24.19.0與NotoCJK可用；原斷言、golden、時限與16MiB stack不放寬。

### 原比較紅燈與待決界線

P-189原`p189_verify.py:195`是`assert raw['base'] == raw['fix']`，訊息為`AssertionError: dump 不同：repo-_role_priority_mutant.scene`。它比較完整load回覆＋dump的stdout；兩版均reject、第二行完整dump相同，L的第一行error與stderr多了`——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm`。不能把訊息的「dump不同」誤寫成幾何dump不同，也不能把126組通過寫成175組完成。

#323原`verify_linux.py:156`的`assert not failures,failures`列三個stdout差：`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。它完成175／350後才判紅，與P-189的base及中止範圍不同。

現行I22及既有正反例要求定位邊／超出區間；未取得診斷版本界線或comparator裁決前，保留完整原差異與exit1，不刪診斷、過濾、正規化或放寬exact。歷史F的同列車memo-only因果證據不能取代跨版本門檻。待決選項及原版本來源在`evidence/geo337-train-20261024/QUESTIONS.md`的Q-323-ABC／Q-P189-EXACT。

### CI與原件公開界線

所據最新#338審查為2026-10-24 00:39:37 UTC／head f05e7cf；原文在`review-f05-e9-originals-and-preparation/338-all-original.md`。新run40043471807及#339的40040764499共十四annotation皆為付款失敗**或**支出上限，API不區分；65原讀取為63 exit0＋兩次log Forbidden 1，Forbidden不能證明log不存在。`actions-f05-e9-environment-public-v2/PUBLIC_REDACTIONS.json`明列兩個signed-log signature遮罩；其餘原bytes保留。舊c6分類與source-tree相等均不解除新head CI，也不代表正式替代流程已接受。

以下相對路徑均在E的`evidence/geo337-train-20261024/`：

- 已公開完整原件：`final-L-ledger-complete/`、`final-L-native-r2-complete/`、`final-L-browser-canvas/`、`final-L-browser-assembly/`、`final-L-browser-documents/`、`final-L-browser-grid/`、`final-L-browser-space/`、`final-L-browser-timber/`、`final-L-Q38/`、`final-L-section7-cardref/`與`final-L-section7-axiom/`、`final-L-required-eight-complete/`、`final-L-pf3-complete/`、`final-L-readers-RC/`、`final-L-reading-a-complete/`與`final-L-architecture/`。
- P52已公開`final-L-p52-terminal-status-only/`；P-189兩項與#323 compare小原收據在`final-L-performance-terminal-status-only/`，包含原assert輸出、首次差異streams、36樣本表、原receipt／scope及175／350 equivalence。**P52／P189full／timing三份完整包雲端已封核，尚未推送**；13496／14330／1457是原件peer核對數，不是產品gate。新`final-L-all-terminal-status-only/`另保formal performance／profile原JSON、完整memo driver receipt與三outer；#323/memo完整原流尚未公開，這些小收據也不代完整封包。完整archive未公開的限制不因附PACKAGE或peer JSON而解除。
- P52 collector先因Chrome IPC、再因原ledger附加欄位各exit1；v3封包保兩次失敗、45個IPC metadata、65 annotations，六ELF只省包內payload，未重跑產品。R8／PF3原v4外層因argv含`--base`誤標source_role/source_sha，原欄位不改；acceptance_sha、--sha L、真inner與Git guards另綁L，診斷在`final-L-required-eight-pf3-tools-and-peer/`。
- 歷史失敗與沿革不重寫：`final-L-native-r1-environment-failure/`、`ledger-b6-complete/`、`review-b6-response/b2-diagnostic-originals-and-peer.tar.gz`。#314既有SSOT例外已採納，後續精確有序補句的寫入差額仍列QUESTIONS；Reading A不冒#335初放能力。儲存維護及其他PR的獨立SHA不列本PR產品通過項。
