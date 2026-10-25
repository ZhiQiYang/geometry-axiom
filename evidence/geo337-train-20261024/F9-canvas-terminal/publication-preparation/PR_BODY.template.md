本 PR 接替 #337，整合 #299+#316、#314 題3、#318 閱讀 A、#323、K 索引及 #339/#340/#343（含 #341/#342）。容量仍64，未合 #344–#348。**維持 draft；native 尚紅，完整驗收未完成。**

以下是唯一 current-state 矩陣；原門檻、golden、時限不變，歷史結果不移標。

| 身分 | 完整 SHA |
|---|---|
| 最終來源 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| 帳本生成／R8／成本執行 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad`；F8→F9僅帳本／evidence |
| 證據 E | `{{EVIDENCE_HEAD}}` |
| 架構四檔原執行 M／H 定向執行 S | M=`6e50aef65513b7b38f93228919272c6d40d6c196`；S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7` |

| Gate | 實際結果／未完成項 |
|---|---|
| 全123帳本／tracked check | F8完整重產0：114 killed／5 equivalent／M20 crashed／3 retired。逐byte採入F9，tracked check0、stale0／blocked0 |
| 完整 native | F9 exit1；35分鐘裁判0（1846.506872秒）。230登記列；5327 pass／1 fail／1 skip。唯一紅為下述 #314 assertion |
| canvas | F9 原workflow／wrapper exit0，35分鐘裁判0；1723.223173秒。完整2267 assertions、零fail／skip；85段golden相符，P73=69、P88=143；原件peer170/0 |
| assembly、documents、grid、space、timber | 五項各UNRUN at F9；原workflow，各獨立埠／TMP |
| P52／Q38／§7兩項 | 各 UNRUN at F9；保留P52原median門檻、Q38全44及兩套完整突變 |
| P-189 full exact／timing | 兩項 UNRUN at F9；歷史exact紅保留，三差裁決未明示延伸本項 |
| #323 R8五stage | F8原outer1；execution=0/0/1/0/0、CLI=0/0/1/1/1。量化門檻綠但exact三差仍1；ABC_result缺席、full_acceptance=null |
| #323 新comparison單項 | F9 outer／stage exit0（12:12:46–12:14:21 UTC）；原件逐列與175／350完整性peer待完成，本批未公開完整原流；不移標F8 R8結果 |
| #323 required-eight／PF3／native後段 | 各 UNRUN at F9；R8五stage不能代完整八stage |
| #323 whole-memo／恢復／隔離ABC | 各 UNRUN at F8（原R8正式來源） |
| reader三原條 | F9 exit0/0/0，207 clauses／1261 blocks，unit51/51、零skip；獨立可寫269葉F9來源逐byte核對且前後clean，nativeROOT不變；actual peer1972/0 |
| RC builder、checker反證／#314六suite及Node inspector／閱讀A native、oracle、mutants-only、完整quick | 各獨立專項UNRUN at F9；native總表不代完整專項 |
| 架構三原judge／四檔 | F9 exit0/0/0、205＋18全ok；334 sources／6 trusted／798 edges／0 diagnostics。四檔為M原收據經F8採用，F9逐blob相同 |
| #341四類成本 | F8 fallback-only exit0；14 cases全樣本。N64 none wall +6.77%、dense −29.72%；未判性能接受，未解除完整優化撤回B1；新F9完整撤回尚未實跑 |
| H局部修正／反證 | S：14/14 exit0、零skip；work反證0/1/0，清零calls=0/2/0、bytes=0/255168/0。O0定向不代O2性能 |
| required CI／替代驗收 | 母證據E c32的原API查詢exit0、total_count0／runs[]，僅代表當時沒有run；本次新E的Actions未讀。OWNER批准同一final SHA七項＋專項全綠替代；目前native1、五browser未跑，替代條件尚未達成 |

native精確失敗：`test_geo314_commit_paths.Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，assertion `I24 submission policy must not change K files`，原額外stdout為 `geometry-core/kernel/source.c`。已定位固定歷史基底的測試範圍問題；嚴格修正草案待主代理批次採入與撤回／恢復反證，尚未修改F9或免除斷言。唯一允許skip是Linux缺compiled Windows GDI harness的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`，實際1項。native原件獨審2208/0、包6191/0只證收件正確，不改正式exit1。

R8原36樣本不重抽：N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`（各≤1）；N64/main=`1.2846970752586067`（≤1.3）；source calls64/32=`4.407618425509266`（≤4.5）。原outer1與350比較原流保留。

批准來源已直接經GitHub API核實：[2026-10-25 10:39:52Z原留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)。`GET /user`與comments API均HTTP200/exit0，已連接帳戶與作者皆`ZhiQiYang`，id`59477728`、node ID完全相同，留言OWNER。原文明列【使用者裁決】與「A 接受這 3 筆」、「延伸到所有 PR」等選項，適用說明由Claude整理。API證明帳戶，不能證明真人手動輸入；也不是本任務B′問題的直接回覆。依管理代理明示的帳戶核實條件，按此當次批准接續。

Q-323-ABC只准三個指定場景各自逐字的新增定位邊文字，其他bytes／返回碼／完整有序圖／五guards與效能門檻不變；第四差、錯字、位置或次數不符仍紅。依核可白名單執行的新F9 comparison單項已於12:14:21 UTC取得outer／stage exit0；逐列與175／350完整性獨審尚在進行，完整原件本批尚未公開。原R8 outer1與全36樣本保留，不換base、不重抽，不擴及P-189，也不把此單項0當作required-eight或整份驗收通過。範圍文字見main [`405f8c5e…`](https://github.com/ZhiQiYang/geometry-axiom/blob/405f8c5e1a637a16cbe47470faf5ae1fa02b8676/決策佇列.md#L841)。CI替代須每張PR同一可解析final SHA七項與專項全綠及完整證據；stale-only帳本例外不含survived／invalid／blocked。本輪帳本check仍0，不需援用，也不自行合併。

最新已讀[審查原文](https://github.com/ZhiQiYang/geometry-axiom/blob/e34e6d784ad9b0ffd2a68be7db92584f953594b0/handoff/pr-reviews/338.md#L151)：2026-10-25T10:40:50Z、head cd19c63。B1的native已終態1，其餘未跑項保留；B2／B3的當次OWNER批准已經原API核實；新comparison單項0的完整原流／獨審待下一批公開，完整替代驗收條件仍未達成；不標READY-TO-MERGE。

原件索引：[F9 native完整原流與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/F9-native-terminal/)（1374 members、13,895,527原bytes，gzip SHA256 `42217b1827d010e8eac017b95799a24910835c202aa1e32a0137cfee32e95d5c`）；[F9帳本採用／架構／F8成本](https://github.com/ZhiQiYang/geometry-axiom/tree/782bc80b0a13ecd19670f5285a8edb1824349686/evidence/geo337-train-20261024/F9-initial-gates/)；[R8完整五stage](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/full-R8-five-stage-raw/)與[全部歷史進度／證據連結](https://github.com/ZhiQiYang/geometry-axiom/blob/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/PROGRESS.md)。


[Reader完整原件與API批准核實](https://github.com/ZhiQiYang/geometry-axiom/tree/c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc/evidence/geo337-train-20261024/F9-readers-and-verified-decision/)：582原件／11,063,364B分為兩個封包，逐member回讀及獨審7041/0。原reader首輪三個reaper環境變數缺漏的啟動前exit1全部保留；只補GEO261_REAPER_LOG後以原argv完成三項。原實際外層timeout=None與警告保留，不冒稱另有已執行的timeout守門。API完整comments原流公開，無關私人帳戶profile留雲端，以身份欄位與完整原回應hash綁定；獨審106/0。


[F9完整canvas原件與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/{{EVIDENCE_HEAD}}/evidence/geo337-train-20261024/F9-canvas-terminal/)：原workflow在11:22:04.734796–11:50:47.957901 UTC執行，原35分鐘界線2100秒未放寬。P38故意注入fb-auto-probe，原uncaughtBrowserExceptions=1且標EXPECTED、unexpected=0；P53 API故障與被取消的網路請求亦完整保留，不能改寫成診斷總數0。原件裁判170/0與封包5396/0分列，封包peer不代產品gate。四包保留656個regular檔45,780,854B＋4個symlink，全部ELF／cache／profile／診斷均收；只將5個SOURCEPLAN Git metadata／mutable latest葉作精確hash-only及1個Unix socket作metadata-only，原payload保留，私有index完整封存另案。這是一輪F9完整canvas通過，不外推其他browser或重複穩定性已驗。
