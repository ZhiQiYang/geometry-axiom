# 持續工作恢復點（2026-10-24，L全項終態已公開，產品合流進行中）

這是執行中的恢復點，不是階段停止或完成報告。使用者不在，不提問、不等答覆；未核可的公理／鎖定決策差額寫 QUESTIONS，繼續其他工作。繁體中文、英文 commit；不 force push、不合併 PR、不推 claude/* 或 grok/*。主列車只由 root 寫入，子代理分支各一位 owner，產出須獨立對抗審查。

## 先讀的公開來源

- #338：`codex/train-337-continue-20261024`。上一輪固定受測 L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`；L完整證據 E_L=`1952b0ae604291a2ec447a5cc684d6ab91306779`（五性能全包亦已正常push）。目前合流來源 U=`ca7838e0f4950452b9befcf40899d606db9b81fa`，本輪產品scope只加K edge、#339/#340與#343（祖先#341/#342），不含#346/#347/#348。最新證據E_U=4d0ef8dee14873256efae1ee646c01d8dcfe947f，含U五stage真終態小原件；U完整native／六browser／帳本與其餘專項尚未跑；#323原五stage真終態1，execution0/0/1/0/0、CLI0/0/1/1/1；三原架構裁判已在同closure physical E=b09真0/0/0，四生成檔尚未重產。L執行不移標。
- 唯一現況矩陣正文 D=`939c1d9382d68bb78df6e3a952d586008c3768a6`，分支 `codex/train-337-continue-20261024-prbody`。新正文已普通 push，原發布結果 `/workspace/geo337-U-terminal-body-publication-20261024/RESULT.json`；等 bot 更新 PR 不阻斷其他工作。
- 最新已讀 handoff=`d36861ff65e941ed941bc8d86231b7cb5e16a1aa`；#338 最後審查仍 2026-10-24 00:39:37 UTC／head f05e7cf，#339 00:39:36／e9ee6d0，兩者均未判可合併。新#340/#341審查為02:38:33/34 UTC，詳見下文；#342–348當次無審查留言。每輪先 explicit fetch 再讀 `handoff/pr-reviews/*.md` 與 `pr-status.md`，不要依本快照猜有沒有新審查。
- main=`425c092eaf16f90256d76433243baebde45163ac`、Claude=`8f9301fc1b78712d930ffc68074437e44d068aab`。#323 已包含列車；舊 #323／#314／#318／combined 不再各自修。

## L既有正式結果：保原execution，依新union影響決定重跑

| 項目 | 原終態與限制 |
|---|---|
| 全帳本123 | tracked、完整CLI、core-map、external-check皆0；114 killed／5 equivalent／M20原允許crashed／3 retired；120 execution heads為L。tracked資料保原自然生成頭b6 |
| native r2 | CLI／workflow／CI35／outer全0；230列、5309=5308pass+0fail+1原WindowsGDI skip；Node737/737、1819.561秒<35min。r1缺三fixture造成四ENOENT的exit1保歷史 |
| 六browser | canvas／assembly／documents／grid／space／timber各0；2267／150／47／356／242／79原assert。canvas85段golden一致、P88=143、P73=69、1718.885秒<35min；唯一例外是P38故意fb-auto-probe，非未預期錯誤。原partial模式保留 |
| Q38／§7 | Q38原42=41 killed+SPM24 equivalent，兩baseline27/20零skip；§7 compiled53刀及axiom V01–V05皆原assert1/restored0，原CLI皆0 |
| reader／RC／Reading A／架構 | reader三條0/0/0；RC兩刀各0/1/0；Reading A mutants-only/quick0/0，保原t4六筆已知C11另案；架構三條0/0/0、205/18零skip、604inputs |
| required-eight／PF3 | R8八列676混合登記單位全0；PF3 baseline20／19指定AssertionError1／restored20，原外層皆0；完整包已於Ec22公開 |
| P52 | formal／verifier／driver／outer0；每側16筆，main中位218.2650215ms、fix176.218242ms，原fix≤main成立。五原控制0/0/1/1/1符合原判準 |
| P189原完整比較 | **exit1**；base3e600772，126組相同後第127個repo-_role_priority_mutant.scene首差中止，175未完成，full內timing未啟動。原比較包括load回覆；幾何dump相同、I22定位診斷不同 |
| P189獨立timing | **exit0但不改full1**；原36樣本、N16/32/48/64 fix/main=1.101333/0.958790/1.277641/1.371567皆≤2；dump_count0、overall_P189_passed=false |
| #323跨版本exact | prepare0/build0/compare1；base b74f9a2，175場景/350組完成後三個I22診斷差；正式ABC_result未設 |
| #323 timing | stage execution0，原outer CLI1；small-N fix/base皆≤1，**N64 fix/main=1.4282954375137715>1.3紅**，保原36樣本及分母，不重抽樣取綠 |
| #323 profile | stage execution0、原outer CLI1；source calls N32=82668、N64=364369，比4.407618425509266≤4.5綠。CLI1仍含先前compare與性能紅 |
| memo完整反證 | driver/outer0，withdrawn1/restored0/隔離ABC0，全complete；calls比6.053833206336931→4.407618425509266；隔離175/350完整有序圖與原audit tuple一致。不能代正式跨版本exact或N64性能 |

原driver共有八stage。L的單一#323 receipt只記前五stage，`all_required_stages_completed=false`、`full_acceptance_passed=null`保原值；L的R8/PF3/native在其他原OUT完成。本輪U也只跑前五stage，後三在U尚未跑，不能移用L實績。全清單須逐項引用，不回寫裁判欄位。原v4外層role掃`--base`誤標base的歷史亦保留，以真inner／明確L／前後Git guard另綁來源。

U帳本還未重產；前一caf6原`mutate.py --check` exit1，120 stale／3 retired全流已公開在E_U的`probe-evidence-and-ledger-freshness/original-caf6-ledger-check/`，不能以L綠帳本代替。U因含#342，Q38應跑44；#342歷史S eb846c345881cc6fc73a53c457a291175365b88c的44=43killed+SPM24保持原execution，L的42也不移標U。新U #323原五stage工具已靜審65/0；薄source準備真0，447檔／4,290,370B、U clean、nlink1唯讀與獨立index；REQUEST SHA256=`5e2a4b75e948ca1cea2d37fa676419c8a08486fae878a51ae69cb2159376c8ee`。新U五stage已真終態1，execution prepare/build/compare/perf/profile=0/0/1/0/0、CLI0/0/1/1/1。原compare完成175/350後三stdout差；N16/32/48 fix/base=0.9999532917535622/0.8129671517479105/0.806276034902179全綠，N64 fix/main=1.429347781620555>1.3仍紅；source calls82668/364369、ratio4.407618425509266≤4.5綠。原ABC_result key不存在、all_required_stages_completed=false/full_acceptance_passed=null，compare後段audit因assert未達，原八stage中required-eight/pf3/native三項未跑；最終L2須待後續完整帳本／架構重產才固定。

四個阻擋仍是 **P189 exact、#323 exact、N64性能、required CI**，沒有 READY-TO-MERGE。前兩者的I22資訊為現行SSOT所需，不可為舊基準exact刪回；裁決選項已寫列車QUESTIONS及正文。N64是可自主修正的效能缺陷，沒有要求新門檻。本輪真CI已另讀U ca7838的run40058889738及physical E b09的run40059064935，各七required jobs failure、steps0、runner空；十四failure annotation為付款失敗或支出上限，另保Ubuntu遷移notice。本次未抓signed logs。f05/e9與Forbidden／兩signature遮罩只保歷史，不能代新run。原件已由E_U76ba公開，B3仍未解除；補跑不自動代表正式替代流程已接受。

## 新U架構前檢（已公開，非四檔重產）

原physical execution=`b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5`，U=`ca7838e0f4950452b9befcf40899d606db9b81fa`；原Git diff證全非evidence路徑相同、source未改。三原裁判真0/0/0、205/18，334sources／6trusted／798edges／diagnostics0。四生成檔尚未重產，不能冒成U直接執行或新manifest/scan/report/receipt已出。與兩新CI run的124份351354B原件在E_U76ba的`evidence/geo337-train-20261024/current-U-architecture-and-ci/`。

## 原件位置與下一輪直接入口

所有L原執行均已終態且完整原包已公開；新union尚無完整驗收。#348整批終態1已釋secondary；root新U #323五stage已真終態1並釋雙鎖；#345原六phase已真終態0並釋獨占，OUT `/workspace/geo345-six-original-requests-20261024`；六次原19/零skip及描述性分析已獨審2493/0，完整包尚未公開，未納U gate。性能／完整canvas不得與其他重測重疊；靜態小檔工作可繼續。原命令表 `/workspace/final-L-performance-exact-argv-20261024.json`，launcher `/workspace/launch_geo337_L_performance.py`；不要重新執行同OUT。

- P52 `/tmp/g337p52L`；P189 `/workspace/g337p189L`、獨立tail `/workspace/g337p189L-timing`；#323 `/workspace/g337323L`；memo `/workspace/g337323memoL`。各outer為 `/workspace/train337-L-<gate>-original-launch-20261024`，原RESULT保真CLI退出碼。
- 已公開全包：native r2、六browser、Q38、§7、全帳本、reader/RC、Reading A、三架構、R8及PF3。完整路徑見新D唯一矩陣。
- 五份完整性能原包已於E_L1952的`evidence/geo337-train-20261024/final-L-performance-complete/{p52,p189,p189-timing,geo323,memo}/`公開，共74,496,801B、3150／3455／261／7485／5501 members。原PACKAGE內published:false保封存時原值，以publisher RESULT真push0證明公開；沒有改原P189full1、#323compare1／N64false。原status-only歷史不刪。
- root已將K edge probe、#339/#340及#343等祖先普通merge固定Uca783；E_Ub09a又普通merge probe完整原件及caf6 check收據。原17方法0／整刀0-1-0。新U原#323五stage已真終態1，N64目標仍紅；原小件在新E的`evidence/geo337-train-20261024/current-U-323-terminal-status`，完整U原流封包尚未公開，不能把L全包改標U。原v4 outer的source_role/source_sha依argv中的--base啟發式可能標base，原欄不改；產品綁定以明確U acceptance_sha、inner原receipt及前後Git guards為準。後續修正性能、完整帳本／架構／受影響正式驗收；#346/347/348留獨立線。五包publisher結果在`/workspace/geo337-complete-performance-publication-20261024/RESULT.json`；不要重跑成功publisher。

## 分支與 owner

| 工作線 | 已知公開來源／下一步 |
|---|---|
| #339 faces；specials | `codex/geo324-faces-20261024`，F616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4；新E8f39025be6708bd9d58e576ed5b349b7ef628624／D283d1e245f724e13644a1379cba5cd34f3dae9d9真推，獨立四head actual99/0。原142與三刀保execution F38da，493+5 Git entries逐byte相同且whole非evidence僅ledger，root准沿用有效局部實績；新F完整正式11仍UNRUN，不因純ledger重跑局部 |
| #340 noWood；specials | `codex/kernel-without-woodworking-20261023`，S175cee44c56c89871803d955c0c525236727ba65；新E04959e04c334ceaf03f865514f76b1cac8ee91f2／Ddb8bf2289f8ad931c00924193e238e621f970e05真推。S175原selected aggregate13/13、strict0、零skip；35native命令31×0與4預期1。原bfb七phase仍保舊execution／精確closure；完整native/browser／帳本／架構仍待union |
| #341／#343前置 | `codex/geo300-prerequisites-20261024` S aa0e3938f17dc996ef5e7410db4844b31856d2a6；`codex/geo300-contact-index-20261024` S ccfaf057088a80c7aad4049f1c67e5eedfc2fdec。原32/46及34/64方法/控制已證；不能預報新N64性能 |
| #342 AC23 | `codex/geo260-ac23-proof-20261024` S eb846c345881cc6fc73a53c457a291175365b88c／Edf230da57619e437c30527dbede8c67fd0ec6b50／Dbe1f69dc5ca7f9cdc2f00d22a1940d877f6002bb。44案例43killed+SPM24，不能以L42替代 |
| #344連線恢復 | `codex/issue320-connection-recovery-20261024` S7b45013da647b791acda8f5977475e4123d5f8c4／E42790be40eee56efada08de84ab2acb1681df981／Da066115bb7062bbacd8ec005e7e0bc6a286ead3b。NodeVM0/1/0已證；完整canvas三phase仍未跑，原PLAN在/workspace/issue320-20261024/full-canvas-three-phase-preparation/ |
| #345 HTTP fixture；specials | `codex/issue214-http-fixture-20261024` S2199cda8896b47c7ad2b6c10479e5e0cbdb67c83／E9896410a84b31fb742b5e92bc5601715bf242267／Dac478611e683c3b5684104e811804acaa23a1558。原19方法/1200秒與六請求各真0、零skip，specials的排程wrapper24d148已靜審48/0，原ready/helper/判準不變，原base3c663→fixed2199及記憶體withdraw/restore來源已核，actual2493/0；新完整原件仍待封包公開，四控制為等價0不是functional kill。已審請求/tmp/issue214-http-fixture-preparation-20261024/RUNTIME_REQUESTS_READY.json |
| #346 cut-list；combined | `codex/geo300-cut-list-storage-20261024` S39273bc0229fbbb16565134e1f8fad3a0d598c31／Eeaf15e239324a6464a04740647afccce3a3c17c7／D4e6a42e908f66ef4475704e0ce97a068e65a8ff6。原11/九組反證/83compile0；O(N)儲存但排序仍O(N²)，完整驗收未跑 |
| #347 P2；backlog | `codex/issue128-empty-panel-rows-20261024` S324034812bb6effca68e0413bc0468595337b317／E2e8a6ed20325aa4842dcd0f89eacd598662be598／D0109cab1a638cd5baa52673e83b136265c10f722。13方法、原十刀及新四組已證。raw seam後續只有外部三檔草稿與靜審，未建分支/未C |
| #348容量512；combined | `codex/geo300-capacity512-20261024`，產品S400a6d0ca50f3aca104fb569c77c8ef753c93355／測試F0f695866c0ba12d2c70dfd7d40628d0fda0f905f；新E41481f280495e14f5a6905d29784cea3a218df10／D9cca9a4d7ea5992366c8ef5df7ef639a455544c7已推、actual2361/0。formal整批終態1，OUT `/workspace/geo348-F0f695866-formal`；W7真7/7零skip exit0，H7為2PASS/5RED（三sentinel測試缺陷與兩512load原Timeout600）；三helper各fixed/withdrawn/restored全1/1/1，無完整有效三態，不能寫全綠。局部75其餘與完整gate仍未跑 |

backlog的K edge probe已公開source Sa543eef67b81f8d8800f32d5dc4a5641840d2943，branch `codex/train337-edge-probe-20261024`，E9b41d395fb2c5d6c971de4b13d4d2ac6701ff22c／D853a7a294b9201236da01d3a34ba397e62e29ecd；root已普通merge source成caf6。原17方法/零skip、56compile/link0、43native、整刀成本21→31→21且0/1/0，actual1427/0；R1目錄/執行檔同名linker紅保留，不能算mutation kill。完整原件在該E的`evidence/geo323-edge-probe-a543eef6/`，root caf6存binding與actualpeer。**該probe定向原實績不含N64**；U當輪fix/main=1.429347781620555仍紅，見上方本輪終態，四個原阻擋仍在。

本輪root實際U只納K edge、#339/#340與#343（祖先#341/#342）；#346/#347/#348不在此final，保持各自分支後續推進。#344/#345也依其實際受驗範圍另收尾，未宣稱已合U。可省重複祖先merge，不能省新組合驗收。root在固定U一次全帳本/架構與七jobs；子代理不各自重產。所有既有定向證據保原execution SHA，不移標。#325/#331/#333仍Grok所有；#335初放原子操作未核可，只保設計/待決。

#340/#339兩個正常merge的原RESULT在`/workspace/geo340-339-L-normal-merges-20261024-r2/RESULT.json`，原退出0、兩remote精確核對、兩checkout clean；L帳本blob保真，230列保留13/39與13/45。首輪環境1及完整3MB輸出保留，沒有reset或刪檔；兩E與兩D新出版已真0且獨立99/0。publisher原R1因KGIT缺origin在第一個readonly ls-remote128，尚無寫入；R2只用command-local遠端URL＋新OUT，原14件失敗完整封包，不改永久config、產品或test。

新審查追加：#340 head4d3要求在final closure真正跑原run_all的rectangular registry row（13、strict count及原時限），直接13方法不能替代；CI run40019345512七failure另須正式處理。specials已真補S175的原selected aggregate13/strict0與精確closure；仍未取得完整正式清單／CI接受，不能標READY。#341 head823729b要求完整優化撤回，對無重複／少量重複／密集／超capacity fallback逐項保存work、CPU、wall原樣本，不能由46組語意控制推論改善；另需原aggregate expected9→10、最終native／受影響timber與CI。combined已接手此要求，原run40022843722環境紅未解除。兩者都要更新base／唯一current-state與受影響bytes證明；這些新要求不允許放寬門檻或宣稱準備即通過。

## 磁碟與排程

磁碟快照：root五包出版前420,945,920B／後341,942,272B可用（/workspace，僅當時快照），不能沿用舊30MiB結論，也不能將配置節省當df淨回收。每次重測前fresh df；最多兩個重測，性能與完整canvas獨占。不能刪收據、fixtures或Gitobjects。#348與新U #323五stage皆已終態釋鎖；#345真啟前fresh WS344,915,968B/TMP23,261,184B（僅啟動快照），其原六phase現已真終態0並釋鎖。

保全lease分四類，各自計數、任何alias寫入／復用前必須**全部delink**，原path/bytes全保：

1. 三個cold checkout共423組（原295＋新128；新128保384 paths）。
2. cardref 2組受控ELF（58＋5＝63 alias paths；另53唯一ELF仍留，共116原paths）。
3. GEO339 1組六alias（原tar＋五份c387 stdin/stdout，6 paths）。
4. 大型歷史archive原3組（7＋4＋2＝13 paths），另新增4組×7＝28 paths真保全link完成；新增原件仍只雲端，待封包／推送。兩批各自列scope；F2兩個receipt截斷候選已排除，未動。

原295＋cardref2早已公開；cold128完整包2,774,412B／15922members、SHA4949b46b…以及新四群完整包248,731B／840members、SHAfc852b7d…均已於E2787ee3167deec7588bde26265152bcf6dc4a939公開。其原actual peers分別63835/0、3421/0，不冒本輪重驗原423或2。新四群19paths的gross配置節省476,540,928B，不等同df淨回收。先前三次環境失敗與成功原件皆保。最新storage量到WS313,602,048B／TMP23,265,280B是歷史快照，fresh df才可排新重測。

storage優先核終態原archive/捕獲stdin/stdout的保路徑去重；新版原包大多已直接hash-object/skip-worktree，root checkout沒有第二份tar，不能憑假設計算節省。/dev/shm為唯讀tmpfs，不能借symlink繞sandbox。環境瞬斷已恢復；若後續再失效，先保本地未推狀態，繼續不依賴它的工作，不詢問使用者。

## 本輪外部工具／待定稿欄位

H collector固定 `/workspace/geo300-capacity512-h-pipe-capture-20261024/TOOL_PINS.json` SHA0d7cdc2ef7bcce382f5a02bc38effcec695326358d40c2f2c156be09b702c033，獨審120/0；20假child/run/unit與4合成原入口1/0/1/2保真、stdin/stdout兩份獨立副本0/1/0。不改原Popen、buffer、timeout；compiler原text僅保decodedtext，不能稱predecode。formal外層須核兩observercomplete與真正OSexit，complete不是產品PASS。工具不得在formal執行中改寫。 新v2另存 `/workspace/geo300-capacity512-h-pipe-capture-v2-20261024`，TOOL_PINS SHA c922d920d196103a4a308f4636c3df59da8954b6fd8777431262d4d181417b76；新增loadfile實體bytes在原呼叫前捕捉，非child已讀的證明。新26＋原20＋entry4自驗皆外層0，內容保全撤回0/1/0，specials獨審59/0；無C或正式新重跑，舊v1與事後scene supplement身份不變。

本稿尚未發布；U與E_U已固定，正文先經root真推後填唯一D placeholder，再推handoff。這是continuation，不是stop或完成報告。#348整批終態仍紅；U五stage真終態1、N64與跨版本exact未解除，#345 已真終態0且完整原件已公開於獨立 E99646d418bc5e886a92bfdabe33e68780e88fe3b，不自行延伸驗收範圍；原出錯也不抹掉。下一輪先讀最新NEXT與各PROGRESS，不重啟既有OUT。證據代理只備外部稿，不寫root或handoff分支。

H原場景補件：collector的input.bin載loadfile路徑，未自動捕獲scene內容；combined在原NativeBuild temp尚活著時唯讀保4個scene／75,875B，`/workspace/geo348-F0f695866-formal-input-supplement-20261024/pass-001`有原path/hash/前後stat與時點。這是v1原執行的事後保全限制，不冒事前capture；v1原工具保持凍結。另版v2已補原run前loadfile bytes snapshot並完成59/0獨審，正式新重跑仍待，不能追認成v1已事前捕捉。


本輪原件發布補記：新增四組 archive 儲存保全已於 E_U 的 `evidence/geo337-train-20261024/maintenance-additional-four-archive-groups/` 公開，原包359949B／1597 members；不是產品gate。#345已普通推送完整六phase原件 E=`99646d418bc5e886a92bfdabe33e68780e88fe3b` 與正文 D=`c5515c14ac9cb59d147563f3dd75dbde5b75ca4e`，沒有移作U驗收或標READY。
