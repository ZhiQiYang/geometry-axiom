# 持續工作恢復點（2026-10-24，native／Q38／required-eight／PF3 終態後）

使用者已撤銷階段性停止指示，要求持續推進；使用者不在，不在對話提問或等答覆。遇到未核可公理或🔒決策缺口，寫 QUESTIONS 與正文，保守保留原裁判並繼續其他工作。全程繁體中文、英文 commit；不 force push、不合併 PR、不推 claude/* 或 grok/*。

## 列車目前狀態

- PR #338：`codex/train-337-continue-20261024`，只有 root 寫入。
- 固定驗收來源 L：`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`。evidence-only 提交不能冒作實跑來源。
- 最新完整 R8／PF3 證據 E：`c22ab27787322ae9fc07d410d1a17397f4809c1d`。已由 `/workspace/geo337-required8-pf3-publication/RESULT.json` 確認正常push 0；原已推 E732=`732ac159043ab311fd66e338c21d33f322f6e968` 已有 native／Q38 完整包，以及 R8／PF3 status-only 原 RESULT。
- 已推正文 D：`a26b2a18dbb0b7746726716046f9a1039365e81a`，分支 `codex/train-337-continue-20261024-prbody`；唯一矩陣綁 E732。正文中的 R8／PF3「完整包待封」是該版出版時狀態，後續用新 E 更新。
- main 已讀為 `425c092eaf16f90256d76433243baebde45163ac`，Claude 來源為 `8f9301fc1b78712d930ffc68074437e44d068aab`。#323 已包含列車，舊 #323／#314／#318／combined 分支不各自修。
- 最新 handoff 已推 `6213cb56eaa695bc137c06f6d67aa4e11f961f76`（含容量512 draft PR 請求）；該輪沒有 #338／#339 新審查。#338 最新仍 2026-10-24 00:39:37 UTC／head f05e7cf，#339 為 00:39:36／head e9ee6d0。兩者沒有可合併裁決。

| L 正式項 | 原始結果／範圍 |
|---|---|
| 全帳本123 | tracked／完整CLI／core-map／external新check皆0；114 killed、5 equivalent、M20原允許crashed、3 retired，完整原件已公開 |
| 六browser | canvas／assembly／documents／grid／space／timber全0，各原範圍2267／150／47／356／242／79；沒有新增skip |
| canvas | 1718.8848816149984秒 < 原35分鐘，85段golden相符，P88=143、P73=69；唯一uncaught為P38故意fb-auto-probe，原EXPECTED檢查綠 |
| native r1 | 原exit1保歷史；230列，5309=5304pass+4fail+1skip。四ENOENT為薄checkout缺三個L既有fixture，不回寫舊判 |
| native r2 | 原CLI／workflow／CI35／outer全0；230列恰各一次，5309=5308pass+0fail+1原允許WindowsGDI skip，Node737/737；1819.561秒 < 原35分鐘。1366-member完整包f9c5ca6b…已公開 |
| Q38 | 原CLI／driver／兩outer全0；42原案例=41killed+SPM24 equivalent，native27／model20 baseline全綠且零skip。449-member完整包acbf826d…已公開；原registry排除未變 |
| required-eight | 原CLI／nested wrapper／stage／driver／outer全0；原八列676混合Python tests、C檢查點與core場景，零fail／skip，非676個unittest方法。841-member完整包81937992… |
| PF3 | 原baseline20全綠、19刀各指定正常AssertionError exit1、restored20全綠；原21次build invocation全0，42binary，沒有42份獨立compiler OS退出碼。4759-member完整包fb3fc268… |
| §7 | cardref／axiom原0／0；compiled原53刀各assert1／restore0，axiom V01–V05各assert1／restore完整44綠；完整原件已公開 |
| reader三條／RC兩組 | 0/0/0；原builder／checker各0/1/0，完整原件已公開 |
| Reading A | 原mutants-only0／quick0；矩形逐毫米、579×8、528/1056正例完整；原t4族六個已知C11_MAIN_NOT_BUTTED保原判決，另案 |
| 架構三條 | 0/0/0、205/18零skip，604輸入前後同L |
| P52／P-189／#323 timing、profile、memo | 本稿尚無原終態收據；下一批以原固定argv獨占執行，不能由前述通過項代替 |
| #323跨版本175／350 exact | L尚無原正式結果；歷史F原exit1的三個I22診斷差異仍B2，未獲comparator／版本裁決，不忽略或正規化 |

原v4 Recorder.role掃整串argv，兩項R8／PF3 orchestration外層因`--base`設定而將source_role/source_sha誤標base b74f9a2；原metadata及streams保留。acceptance_sha、明確`--sha L`、真正subject inner及前後Git guards才獨立綁定L，不概稱所有source欄皆L。原role重現診斷已備並隨完整包公開，不修改固定裁判。

R8原runner拷貝619份global suite-log，含歷史未選項，只按當次`--only`八項argv與八列stdout計。PF3省略包內42個ELF payload、原42,641,000B皆留原址，hash／側車／recipe保留。獨審2768／19603只核原件，不算產品測試。完整R8／PF3 collector原件在 `/workspace/train337-final-required8-pf3-collection/`，兩包及兩collection-launch完整保留。

#314精確映射：native r2六個完整Python module共103通過；原per-child OS欄沒有另外保存，以原裁判契約支持0。Node inspector13是parent1+nested12通過事件，不是獨立Node13 process exit；r2 enclosing Node737原0，r1 enclosing原1保歷史。舊52／122映射已於E935公開，不拿peer計數當產品gate。

最新B3：#338 f05的Actions40043471807、#339 e9的Actions40040764499各七required failure；十四原annotation是付款失敗**或**支出上限，API不區分。安全原件包40567a58…已公開；65原讀取63 exit0＋2 log Forbidden exit1，Forbidden不能證明log不存在。兩signed-log signature按manifest精確遮罩，未遮罩原件只留雲端。舊c6／47fd分類只保歷史。來源tree相等和雲端補跑不自動解除正式CI或替代流程要求，仍無READY-TO-MERGE。

## 排程與來源租約

native r2與Q38均已真終態、完整收包及actual peer完畢，不再RUNNING，也不能重新啟動。native ROOT/globalcache在7386原件核對完成後已交還root；R8與PF3亦已真終態並封包。root已進入P52→P189→#323性能的獨占排程，下一個恢復者先讀原outer RESULT判斷已到哪一項；不同時跑C／Chrome重測、壓縮或大規模hash。

- 原ROOT：`/tmp/train337-323-f64d638f-source`；共用cache：`/tmp/geometry-tests`。不得因舊session不存在重啟已完成項，也不得把新cache側車冒作舊原件。
- native r2 OUT：`/tmp/train337-full-native-L-7af8c5d8-r2`，outer：`/workspace/train337-native-L-7af8c5d8-r2-launch`。封存：`/workspace/train337-native-r2-terminal-collection/completed/`。
- Q38私有ROOT：`/workspace/train337-L-reading-a-source`，同L565原檔；正式包：`/workspace/train337-q38-terminal-collection/`。原jobs1／600、900秒子時限未改。
- 原R8／PF3 OUT：`/workspace/train337-final-L-{required-eight,pf3}-7af8c5d8`，各自`-launch`；兩原outer RESULT已有E732 status-only副本，不能以小RESULT冒完整raw包。
- 最多兩個重測；完整canvas與任何性能測試須獨占。開測前fresh df，只清自己的可重建暫存，不能刪收據、fixtures、Git objects。

## 各分支與下一步

| PR／工作線 | 分支與已推完整SHA | 已證範圍／下一步 |
|---|---|---|
| #339（接替#324） | `codex/geo324-faces-20261024`；F38da31bcac91db631e6325e40b228f8604810e82／E1d94ab77ab29952d5b73ec5b262dfd239819fe25／D71113ce739f6fe7c327b162e47e6fd7dba349824 | 同F原142／三組0/1/0與1469-member原包已公開、actual6636/0；CI安全包亦公開。正式11項仍3PASS／1RED／7UNRUN，帳本過期、aggregate等未完，非READY |
| #340 noWood | `codex/kernel-without-woodworking-20261023`；S4d3a17c306cad42057589c5cfd964f1c32b755c4／Ed45dbbc3e96c85e6d1caa629f6abafdfd62c5974／D77a007711f48b47daa10fbe1cb594d25937e295a | 原13項7phase為0/1/0/1/0/1/0；未納L，L仍原11項。specials為唯一owner；已授權性能結束後一般merge L進#340、再將#340一般merge進#339，不等main |
| #341前置 | `codex/geo300-prerequisites-20261024`；Saa0e3938f17dc996ef5e7410db4844b31856d2a6／E823729be5f4f025aebbf02c2dc85e09907c28812／Dea1a153b2da2203c3c0aac7a1f631d9caa1bf67b | 原32方法46控制282build0；不移標L或512 |
| #342 GEO260 | `codex/geo260-ac23-proof-20261024`；Seb846c345881cc6fc73a53c457a291175365b88c／Edf230da57619e437c30527dbede8c67fd0ec6b50／Dbe1f69dc5ca7f9cdc2f00d22a1940d877f6002bb | 原44案例0、43killed／SPM24 equivalent，不能冒L原42 |
| #343 contact index | `codex/geo300-contact-index-20261024`；Sccfaf057088a80c7aad4049f1c67e5eedfc2fdec／Ea934a554ae58f16f124f1b264523947f170b3f0b／D56ed8d0090449e09938e9c63c54aec7fda789380 | 34方法64控制318build0；全列車及512性能未跑 |
| #344 connection recovery | `codex/issue320-connection-recovery-20261024`；S7b45013da647b791acda8f5977475e4123d5f8c4／E42790be40eee56efada08de84ab2acb1681df981／Da066115bb7062bbacd8ec005e7e0bc6a286ead3b | 原NodeVM9/6/9為0/1/0；完整CDP三phase未跑，V082feb0662fea32131f3f7fb8ca451679ab6421d已公開；每次完整canvas要獨占 |
| #345 HTTP fixture | `codex/issue214-http-fixture-20261024`；S2199cda8896b47c7ad2b6c10479e5e0cbdb67c83／E9896410a84b31fb742b5e92bc5601715bf242267／Dac478611e683c3b5684104e811804acaa23a1558 | 目前已核紀錄仍原19方法／1200秒與四等價控制UNRUN；不得挪用其他分支結果 |
| #346 cut-list storage | `codex/geo300-cut-list-storage-20261024`；S39273bc0229fbbb16565134e1f8fad3a0d598c31／Eeaf15e239324a6464a04740647afccce3a3c17c7／D4e6a42e908f66ef4475704e0ce97a068e65a8ff6 | 原11方法零skip、九組0/1/0、83compile0已公開，actual2279/0；完整native/browser/帳本/架構未跑，NOT READY；儲存O(N)，分組排序仍O(N²)、容量64 |
| #347 P2 | `codex/issue128-empty-panel-rows-20261024`；S324034812bb6effca68e0413bc0468595337b317／E2e8a6ed20325aa4842dcd0f89eacd598662be598／D0109cab1a638cd5baa52673e83b136265c10f722 | 原panel13方法零skip、93compile/link0；原十刀正常ASSERT1只配整體baseline0，不假稱逐刀restore；新增四組真0/1/0。phasecalls撤回5000/50000000、固定及恢復2/2；PF整合/fullnative/browser/最終ledger/架構UNRUN，NOT READY。347.md目前無留言，bot正文仍舊7b105260待0109同步 |
| #300 capacity512（已送draft請求） | `codex/geo300-capacity512-20261024`；S400a6d0ca50f3aca104fb569c77c8ef753c93355／E391f44da1c3e37e50c7a25a8a855b93c2865062c／Dfd206036052bfb4f8c7ea0025c31b1b2a21cc4b8 | base為#347分支；只有靜態計畫／套用／公開件檢查。全部C／bridge／runtime／反證／ledger／架構／完整native／browser／效能UNRUN，NOT READY；AST W7/H5不是pass，512正例目前是unplaced測試設計，不代表512個placed世界已證 |

#325／#331／#333由Grok負責，不能改其分支。#337舊Claude分支不推；其新來源只用一般merge。後續順序#343→#346→#347 P2→512；共用tests／ledger／architecture由root統一安排，子代理不各自重產全帳本。draft PR建立或正文同步未完成時照做其他工作，不能把請求檔當PR已開。

## 空間保全

- 原212＋既有24＝236 cold archive aliases已公開維護收據。這輪另59組cold immutable receipts已實際0去重，原plan配置節省量286,375,936B，背景寫入不同，不能當成df淨回收；共295組cold aliases，所有原路徑／bytes保留。三個cold roots p-source／a-source／l-source在全部aliases脫鉤前禁寫、禁復用。
- 另有兩組cardref受控突變ELF alias groups，與cold archive groups分開；63／116 payload的保全link已真0，回收約79MB。各原受控ELF路徑仍在，寫任一alias前須全部delink；不能以inode／mtime冒原樣。
- 新59＋cardref維護包已在雲端真封：`/workspace/cold59-and-cardref-links-originals-20261024/`，7487members、4,160,382B，tar SHA256 `0c9cb4ef4f425d7cb7ab7542c0b183ac55f09d6ada7350ea7e4e36bf7c95fcdb`，actual30026/0。尚待root下一批公開，不是新增產品gate；collection outer與包外root sequential原件也須附，不重封或刪fixtures／收據／git objects。
- 最新root回報空間309MiB是59去重後的當時值，不代替開重測前fresh df。

## 下一步入口

1. root-only R8／PF3完整包publisher已真完成：`/workspace/publish_geo337_required8_pf3.py`；E732→Ec22正常push0，完整capture在 `/workspace/geo337-required8-pf3-publication/`。不要重新執行publisher或重新收包；新性能與維護證據另批。
2. 性能原argv：`/workspace/final-L-performance-exact-argv-20261024.json`，SHA256 `627438965715077a6fea35eb839ef0ecc2ffb62e4aa0f5bdcef75bc27ef4b86c`。P52必須`/tmp/g337p52L`；P189可`/workspace/g337p189L`；#323五stage共`/workspace/g337323L`。原交錯順序、分母、閾值與全失敗保留。P52原門檻為fix median≤main，沒有+5寬限。
3. 原outer `/workspace/launch_geo337_L_performance.py` SHA256 `0145049f3d9e0121c4ec2e06efcd61ff0c713479fbe7f431ddfb88cc5b18fe02`；只擷取原CLI，不改judge。P189若dump紅，原整項仍紅；獨立timing後補不改原判。#323 compare若紅保原差異，其他性能/profile繼續；原後續CLI會累計先前stage紅，須分列CLI exit、自身stage exit及數值，不冒全局0。
4. 持續explicit fetch main／handoff／Claude refspec；預設fetch只有main。讀hand-off最新PR審查，真正可合併才標READY，合併留本機。容量512請求結果在 `/workspace/geo300-capacity512-handoff-request-publication-20261024/RESULT.json`，到`handoff/pr-status.md`找實際新PR號，不重送請求。
5. 若性能正在獨占，其他代理只做小檔靜態工作；等終態後才做壓縮／大hash或其他C／Chrome。若認證失敗仍本地提交、明記未推，30分鐘後重試，不問使用者。
