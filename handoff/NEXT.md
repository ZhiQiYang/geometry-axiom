# 持續工作恢復點（2026-10-24，L 全項取得終態）

這是執行中的恢復點，不是階段停止或完成報告。使用者不在，不提問、不等答覆；未核可的公理／鎖定決策差額寫 QUESTIONS，繼續其他工作。繁體中文、英文 commit；不 force push、不合併 PR、不推 claude/* 或 grok/*。主列車只由 root 寫入，子代理分支各一位 owner，產出須獨立對抗審查。

## 先讀的公開來源

- #338：`codex/train-337-continue-20261024`。固定受測 L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`；最新終態證據 E=`b621a4fbc3cdea359b3676fb22dc8ef566968b8a`，正常 push 已確認。
- 唯一現況矩陣正文 D=`733360596e6febaf66a27dd9e61a8991406be0e4`，分支 `codex/train-337-continue-20261024-prbody`。原發布結果 `/workspace/geo337-all-terminal-compact-prbody-publication-20261024/RESULT.json`，真 push0；等 bot 更新 PR 不阻斷其他工作。
- 最新已讀 handoff=`d2ed8e6e`；#338 最後審查仍 2026-10-24 00:39:37 UTC／head f05e7cf，#339 00:39:36／e9ee6d0，兩者均未判可合併。新#340/#341審查為02:38:33/34 UTC，詳見下文；#342–348當次無審查留言。每輪先 explicit fetch 再讀 `handoff/pr-reviews/*.md` 與 `pr-status.md`，不要依本快照猜有沒有新審查。
- main=`425c092eaf16f90256d76433243baebde45163ac`、Claude=`8f9301fc1b78712d930ffc68074437e44d068aab`。#323 已包含列車；舊 #323／#314／#318／combined 不再各自修。

## L 正式結果：不要重啟已完成項

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

單一#323 receipt的`all_required_stages_completed=false`、`full_acceptance_passed=null`保原值：它只有五stage，R8/PF3/native在其他原OUT完成。全清單須逐項引用，不回寫裁判欄位。原v4外層role掃`--base`誤標base的歷史亦保留，以真inner／明確L／前後Git guard另綁來源。

四個阻擋仍是 **P189 exact、#323 exact、N64性能、required CI**，沒有 READY-TO-MERGE。前兩者的I22資訊為現行SSOT所需，不可為舊基準exact刪回；裁決選項已寫列車QUESTIONS及正文。N64是可自主修正的效能缺陷，沒有要求新門檻。CI已查 f05/e9 兩run共14個job為付款失敗或支出上限、runner空／steps=[]；Forbidden不能證明log不存在，兩個signed-log signature只在公開副本遮罩。補跑不自動代表正式替代流程已接受。

## 原件位置與下一輪直接入口

所有L原執行均已終態，性能獨占已釋放。原命令表 `/workspace/final-L-performance-exact-argv-20261024.json`，launcher `/workspace/launch_geo337_L_performance.py`；不要重新執行同OUT。

- P52 `/tmp/g337p52L`；P189 `/workspace/g337p189L`、獨立tail `/workspace/g337p189L-timing`；#323 `/workspace/g337323L`；memo `/workspace/g337323memoL`。各outer為 `/workspace/train337-L-<gate>-original-launch-20261024`，原RESULT保真CLI退出碼。
- 已公開全包：native r2、六browser、Q38、§7、全帳本、reader/RC、Reading A、三架構、R8及PF3。完整路徑見新D唯一矩陣。
- P52／P189full／timing完整包已在 `/workspace/train337-final-performance-collection-preparation/{p52-v3,p189-v2,p189-timing-v2}/` 封存並獨審，**尚未公開tar**。#323/memo正在準備原件封包。Eb621只新公開28小原件2,936,868B，包括完整memo driver receipt及原性能/profile JSON；不是全raw已推。
- 下一步先回收可保原路徑的重複immutable原件空間，發布尚未推送完整包；再讓定向修正與後續分支合流。最新小publisher與結果：`/workspace/publish_geo337_all_terminal_status.py`、`/workspace/geo337-all-terminal-status-publication/RESULT.json`。不要重跑已成功publisher。

## 分支與 owner

| 工作線 | 已知公開來源／下一步 |
|---|---|
| #339 faces；specials | `codex/geo324-faces-20261024`，最新source F616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4已正常push；舊純evidence E1d94ab77ab29952d5b73ec5b262dfd239819fe25／D71113ce739f6fe7c327b162e47e6fd7dba349824待更新。原142及三刀證據仍綁舊F38da31bcac91db631e6325e40b228f8604810e82；新F只合更新#340與L帳本，正式項未重跑，不移標 |
| #340 noWood；specials | `codex/kernel-without-woodworking-20261023`，最新source S175cee44c56c89871803d955c0c525236727ba65已正常push；舊純evidence Ed45dbbc3e96c85e6d1caa629f6abafdfd62c5974／D77a007711f48b47daa10fbe1cb594d25937e295a待更新。由S4d3a17c306cad42057589c5cfd964f1c32b755c4正常merge L，原13方法/七phase證據保舊實跑頭。新thin checkout首輪無index環境1保留，r2用read-tree初始化後merge0；新S正式項未跑 |
| #341／#343前置 | `codex/geo300-prerequisites-20261024` S aa0e3938f17dc996ef5e7410db4844b31856d2a6；`codex/geo300-contact-index-20261024` S ccfaf057088a80c7aad4049f1c67e5eedfc2fdec。原32/46及34/64方法/控制已證；不能預報新N64性能 |
| #342 AC23 | `codex/geo260-ac23-proof-20261024` S eb846c345881cc6fc73a53c457a291175365b88c／Edf230da57619e437c30527dbede8c67fd0ec6b50／Dbe1f69dc5ca7f9cdc2f00d22a1940d877f6002bb。44案例43killed+SPM24，不能以L42替代 |
| #344連線恢復 | `codex/issue320-connection-recovery-20261024` S7b45013da647b791acda8f5977475e4123d5f8c4／E42790be40eee56efada08de84ab2acb1681df981／Da066115bb7062bbacd8ec005e7e0bc6a286ead3b。NodeVM0/1/0已證；完整canvas三phase仍未跑，原PLAN在/workspace/issue320-20261024/full-canvas-three-phase-preparation/ |
| #345 HTTP fixture | `codex/issue214-http-fixture-20261024` S2199cda8896b47c7ad2b6c10479e5e0cbdb67c83／E9896410a84b31fb742b5e92bc5601715bf242267／Dac478611e683c3b5684104e811804acaa23a1558。原19方法/1200秒與六請求仍未跑；四控制為等價0不是functional kill。已審請求/tmp/issue214-http-fixture-preparation-20261024/RUNTIME_REQUESTS_READY.json |
| #346 cut-list；combined | `codex/geo300-cut-list-storage-20261024` S39273bc0229fbbb16565134e1f8fad3a0d598c31／Eeaf15e239324a6464a04740647afccce3a3c17c7／D4e6a42e908f66ef4475704e0ce97a068e65a8ff6。原11/九組反證/83compile0；O(N)儲存但排序仍O(N²)，完整驗收未跑 |
| #347 P2；backlog | `codex/issue128-empty-panel-rows-20261024` S324034812bb6effca68e0413bc0468595337b317／E2e8a6ed20325aa4842dcd0f89eacd598662be598／D0109cab1a638cd5baa52673e83b136265c10f722。13方法、原十刀及新四組已證。raw seam後續只有外部三檔草稿與靜審，未建分支/未C |
| #348容量512；combined | `codex/geo300-capacity512-20261024`，產品S400a6d0ca50f3aca104fb569c77c8ef753c93355；最新測試F0f695866c0ba12d2c70dfd7d40628d0fda0f905f，最後純evidence E391f44da1c3e37e50c7a25a8a855b93c2865062c，正文Dfd206036052bfb4f8c7ea0025c31b1b2a21cc4b8待新稿。修H計數/I9與真正placed64/512、W7/H7局部75皆仍UNRUN；evidence代理正備完整Popen原流collector，不冒靜審為C通過 |

backlog另正準備#323 K edge miss重用probe的外部最小補丁，`/workspace/geo323-runtime-static-analysis-20261024/edge-probe-draft/`；root已靜讀，未合分支/未C/未性能。必保完整圖順序、五guards、rehash碰撞與allocation fallback，撤回/恢復後才合主列車，不另在舊#323重修。

root最終依來源祖先收斂 #340→#339→#343/#346/#347/#348，再#342/#344/#345；可省重複祖先merge，不能省新組合驗收。產品/測試union固定後root統一一次全帳本/架構與七jobs；子代理不各自重產。所有既有定向證據保原execution SHA，不移標。#325/#331/#333仍Grok所有；#335初放原子操作未核可，只保設計/待決。

#340/#339兩個正常merge的原RESULT在`/workspace/geo340-339-L-normal-merges-20261024-r2/RESULT.json`，原退出0、兩remote精確核對、兩checkout clean；L帳本blob保真，230列保留13/39與13/45。首輪環境1及完整3MB輸出保留，沒有reset或刪檔；新source的獨立actual審查與各分支evidence/body出版仍由owner接續。

新審查追加：#340 head4d3要求在final closure真正跑原run_all的rectangular registry row（13、strict count及原時限），直接13方法不能替代；CI run40019345512七failure另須正式處理。specials已被指派優先準備新S175的原aggregate與來源閉包，未跑前不能標READY。#341 head823729b要求完整優化撤回，對無重複／少量重複／密集／超capacity fallback逐項保存work、CPU、wall原樣本，不能由46組語意控制推論改善；另需原aggregate expected9→10、最終native／受影響timber與CI。combined已接手此要求，原run40022843722環境紅未解除。兩者都要更新base／唯一current-state與受影響bytes證明；這些新要求不允許放寬門檻或宣稱準備即通過。

## 磁碟與排程

兩個merge後最後df約/workspace30MiB、/tmp29MiB，只是快照。每次重測前fresh df；最多兩個重測，性能與完整canvas獨占。不能刪收據、fixtures或Gitobjects，也不可在資料不完整時把環境錯誤算mutation kill。

128組保存式去重已全部真0；連原295共423個cold immutable alias群全部禁寫，原path/bytes保留，全部aliases脫鉤前不得復用p/a/l checkout。另2個cardref受控ELF群分開計。cold59/cardref完整包已公開Ef16；cold128新包在`/workspace/cold128-originals-20261024/`，15922members、2,774,412B，SHA4949b46b18d9b8b8bbaaec0fd65dc212ded056757b13589422f56fe702aeb2cd，獨審63835/0，尚未推。gross配置量不能當df淨回收。

另有#339一組六個archive／捕獲stdin/stdout aliases已於02:52:59真0保存式去重，全部原path/bytes保留；這一組不併入423cold或2cardref，全部aliases脫鉤前亦禁寫。固定PLAN在`/workspace/geo339-six-original-aliases-preparation-20261024/`，完整原RESULT／journal在`/workspace/geo339-six-terminal-originals-preserving-links-execution-20261024/`及其`-launch`；原失敗1/1/1與末成功0保留。配置節省23,592,960B，原free前後29,868,032→53,329,920，差額包含新收據，不能等同配置量。

storage優先核終態原archive/捕獲stdin/stdout的保路徑去重；新版原包大多已直接hash-object/skip-worktree，root checkout沒有第二份tar，不能憑假設計算節省。/dev/shm為唯讀tmpfs，不能借symlink繞sandbox。環境瞬斷已恢復；若後續再失效，先保本地未推狀態，繼續不依賴它的工作，不詢問使用者。
