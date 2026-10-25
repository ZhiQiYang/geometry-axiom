# 目前接續狀態 — F9 完整 native 執行中

這是持續工作的 checkpoint，不是階段停止或完成報告。下面舊區塊全屬歷史；以本段身分與真原件為準。全程繁中／英文commit；不合併PR、不forcepush、不碰claude/grok分支、不改未核可公理或決策佇列；使用者不在，不提問空等。

## 已公開身分

- 主列車／#338：codex/train-337-continue-20261024，固定正式驗收F9=`4f8a794f4167c3562eb182045102e86e9e37cca9`。
- 原完整帳本生成／R8真正執行F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`；F8→F9只有tests/mutants_results.json及evidence，所有產品／裁判相同。不要移標原execution。
- 最新證據E=`cd19c63a9fe625c039a421c52d3c6d335e2009c4`，相對F9只evidence；追加9葉/739736B native起跑收據。上一E782bc80b0a13ecd19670f5285a8edb1824349686的226葉/25,493,554B初始gates已actual2354/0。
- 最新正文D=`37555b9e24ccd58d13afe4b3e20d86fc9ca1f206`，分支codex/train-337-continue-20261024-prbody；唯一current-state矩陣已標native RUNNING，末稿b13c36…／新E與起跑事實peer153/0、真push0。上一D4e6bc0edbeca54d166d823a8cb6017732c2ad710已actual78/0。pr-status仍舊47ace3da，尚不能稱bot已套用正文。既有請求會自動讀body_ref，不新增重複請求。
- main=`425c092eaf16f90256d76433243baebde45163ac`，Claude head仍`8f9301fc1b78712d930ffc68074437e44d068aab`。最新fetch的handoff=`4b4d72287975a952558eb9f256be158631becb23`，評論/狀態與前次無新增；#338最新審查仍2026-10-24T06:38:46Z/head597bce6。所有PR仍未READY。

## 正在跑：不可重啟／不可碰來源

完整native root原exec session **41942**，F9，原workflow開始 **2026-10-25T09:53:11.697952+00:00**。
- 外層：`/tmp/geo337-F9-native-launch-20261025`；內層：`/tmp/geo337-F9-native-4f8a794f-20261025`。
- 真原指令：`ulimit -s 16384; python3 tests/run_all.py --build`，全部230登記項、原35分鐘CI gate不變，watchdog不是放寬門檻。
- 原ROOT：`/tmp/train337-323-f64d638f-source`，HEAD真F9，前置clean；driver入場TMP135462912B。native外層釘原128MiB啟動headroom，後續不可把開跑後下降當另一產品門檻。
- secondary由外層持、heavy由原driver持；舊/tmp/geometry-tests原638檔/5,455,046B已同device整目錄rename保存在內層preserved-global-geometry-tests，不刪任何原件。
- 原工具`/tmp/native-final-executable-preparation/run_full_native_workflow_v2.py` pin763a6e8064be212a020522a43a80bdb6cd353d329997c83479f469c2359f4d21；root外層`/tmp/launch_geo337_F9_native_20261025.py` pinface7315bc0a6dc65ab67928f0b195571559d04aede94cdef263c3f579401c82，靜審d5443d5f…已0。
- 真終態前不freeze/hash活動完整payload、不改ROOT／seed、不啟heavy或性能/canvas。只可讀小metadata/末尾狀態。拿到exec真正exit後立刻保存完整tool FINAL，不把receipt存在或部分綠當終態。
- 目前只知執行中，正式native出口尚未有；任何紅照規則收齊、分類，不放寬斷言/時限。

## 已完成：不要重跑

1. **F8完整123**：原session58101真0，07:38:36–09:00:48；原四phase舊tracked1/full0/map0/新外置check0。123＝114killed/5equivalent/M20原允許crashed/3retired，120自然F8 head。原JSON SHA2560123548b29bf8adbaf3cf896bfffb212134452f2574eaf8ae1d1b663104ead1b。原件peer7625/0、封包11165/0。
   公開於E f0f7888213a8cc5b54f0a4303fb0577fe812cefd 的 evidence/geo337-train-20261024/ledger-F8-complete/；1486regular/49,703,520原bytes，gzip8,584,878B，archive806ab05886963c6dd2673096e04272c734f09c602f830ded9561a79729e13be8，INDEX c4ab625602baffd3e073f4dec765e586793a337963d1c4aec221277d4bfbcaa4。兩次v2/proc讀權失敗完整保留；v3正式獲准環境封存0，不改安全設定，外部UID0系統cwd仍明列unknown。
2. **F9採入**：/tmp/geo337-F9-byte-adoption-20261025/RESULT.json，普通push0、清MUTATE_*原trackedcheck0/stale0/blocked0。原F8頭／日期／分類逐byte保持。採入/公開actual924/0，evidence F9-initial-gates/ 已全收。
3. **F9三架構原judge**：/tmp/geo337-F9-architecture-original-20261025，0/0/0；205契約＋18產品測試全ok、334sources/6trusted/798edges/0diagnostics。actual144/0。四artifact與F8同blob，原receipt仍M6e50aef65513b7b38f93228919272c6d40d6c196，不冒F9重產。
4. **F8→F9雙來源轉移**：09:47:42–57真0，/tmp/geo337-F8-F9-dual-source-apply-20261025；原exec34408 final在/tmp/geo337-F8-F9-dual-source-EXEC_FINAL-20261025.json。native6997／seed2738原物理葉保全、兩邊五fixtures、refs/sparse/完整index gzip/忽略原件保留，只有新帳本葉改。actual12224/0在/tmp/geo337-F8-F9-dual-source-actual-peer-20261025/REVIEW.v2.json，pine4a85545e379708190885effbcff8ba56d950e824520015c7d1b44eac42d5c25。**不可再跑F8-bound轉移入口**。seed路徑仍包含F8，但其HEAD已F9：/workspace/geo337-full123-F8-cache-20261025/_bridge-work/75a1e93811a52b69385cbdaf6a09d773ed9052ad/repo。
5. **R8**：全部原36樣本與calls門檻已達，outer仍1因三stdout差；不重抽有效R8。B/C仍未核可、P189也未另核可。I22原必要診斷不得刪，不更新golden/正規化。具體三差/選項已公開、QUESTIONS保紅。CI原付款/額度阻擋不自行改帳戶或安全設定；新F9/E CI未讀。
6. **F8 #341 fallback-only成本**：原session33499真0，/tmp/geo341-F8-fallback-cost-run-20261025；546CLI/14cases/378samples（42diag/42warmup/294scored）/9ELF。actual4416/0、包24831/0，全包公開在F9-initial-gates/。N64 none wall23846/22334ns約+6.77%、dense7601/10816約−29.72%；保存全點，performance_acceptance_decided=false，不自訂門檻。原B1要求「完整優化撤回」但沒指定Sc493唯一基準；新的fallback實測未覆蓋unique-ID全撤回。cost_tool_adversarial正準備最小完整withdrawal草稿、保H/#343，未編譯/量測/改產品。勿把前輪結果改成全面性能改善。

## 接續工作與擁有者

- 主代理唯一寫train。native真終態收原tool/receipt/logs、peer、發布PROGRESS；其他原正式gate照37命令計畫。Q38全44、required-eight681、§7、PF3、P52、P189、reader/RC/閱讀A/#314各UNRUN，不得冒正式已跑。
- Browser來源：resource_and_transition_review正修1025 docs/prototype唯讀alias工具，architecture_actual_review對抗審。只有外部小草稿/合成，不曾新增alias。**native結束才可實執**。轉移/alias純準備64MiB＋真峰值，native另128MiB，browser原64MiB/各job重新入場；不是產品數值門檻。
- 已審split單job preparer：/tmp/geo337-browser-single-job-split-preparation-20261025/browser_readonly_pool_preparer_split_single_job.py，pin5e9b3fc3daeaf95ca4349e934dafb90eb915dc3dca17f6d1c418fe1d2ab85787。h_init_actual_review已備F9外層v2（見下），保原workflow/driver2a425…/Chrome156/Node24/六埠/TMP；尚未啟任何browser。
- 小磁碟：native開始前TMP約141MB，後續只按fresh真值。不要刪收據/fixtures/Gitobjects/原ELF，不碰永久/tmp/geo337-published-archive-git-objects-20261024與其alternates。七對raw去重與36Chrome cache已真完成且actual741/0，**勿重做**；新immutable registry pinec140cfd…在/tmp/geo337-terminal-narrow-maintenance-actual-peer-20261025。WS375與舊四/六冷群也早已做完。另剩6冷TMP群gross23,388,160B只是候選，未新plan/執行，不能預算成已可用。
- #348：r8_terminal_peer備F73重建/真小fixture校準/原512四指令整批600s的明確診斷；不與native/canvas爭資源。F0f兩timeout保原身份；9個F73舊TMP ELF已不存在，不可宣稱復用，現可復用乾淨204檔F73 source與已審wrapper。tinyC協議已過，不重跑它代正式512。
- #344仍S7 cbb318d76d7d242ae0db760ae15d57ef1cad4aa0 strict9/9原0，完整canvas三phase與整合UNRUN；VM010仍S540。#345/#346/#347/#348未合入train。#325/#331/#333歸Grok不碰。

最新已備browser外層v2：/tmp/geo337-F9-browser-launch-preparation-v2-20261025/launch_F9_browser.py pin1af311d824c2dfcfd946d44d677501ac1356549cdabaf33690d1c34d82a04281，PINS9e690a03df64762ffbeac2534d876fbc9d10dc1499a41e774af89739cae14fdf；peer55/0在/tmp/geo337-F9-browser-launch-static-peer-20261025/V2_REVIEW.json（75daac0ab5e53815e7429b8a9ae275c45b1ffc07b5bbe0ac9d4ec892f57fa6f7）。六requests仍UNBOUND，必須native真終態＋alias與完整sourceprep真0、原c387/PREPARER/MATERIALIZER/PLAN/FREEZE/GUARD pins才排，各項目前UNRUN。不要直接跑舊L launcher。

1025alias最新v3：/tmp/geo337-missing-readonly-alias-preparation-20261025/add_missing_readonly_browser_aliases_v3.py，pin7b65de06c6488d06e535135333e12bfeb631ace546fec02939ae8f87b20883ed；REQUEST.v3.F9.pending.json lease/review都false，待architecture最後審查，不曾實執。#341完整withdrawal OWN已有peer86/0（f5bc2bd7…），cost代理正接插樁/runner，C與新成本仍未跑。

一次試喚醒舊acceptance代理遇agent thread limit；沒有重試、換模型或另開任務。現有代理繼續分工，這不是產品紅燈或usage limit宣告。

以下舊內容完整保留作歷史；其中RUNNING、E/D、F8來源等不得覆蓋上述新狀態。

---

# 持續工作 checkpoint：F8 的 R8 量化門檻全綠，exact 三差保紅，接續完整帳本與正式驗收

這是接續點，不是停工或完成報告。使用者不在，不提問、不空等；繁體中文、英文 commit。不 force push、不合併 PR、不推 claude/*／grok/*。主代理唯一寫 #338 主列車；每條來源由一人維護、另一人對抗審查。不得放寬斷言／golden／時限，不改決策佇列；公理只依已核可 SSOT 流程。主列車保持 draft，尚無 READY-TO-MERGE 裁決。

本稿以 handoff 基底 `7a31dc436c78f16979b8f4cb97550118355f6d3a` 的既有 NEXT 保留其他工作線，更新本輪可核對的 F8／R8 終態。來源 SHA、實際執行 SHA、證據提交與正文提交分列，不隨 evidence 提交移標。

## 唯一 current-state

| 項目 | 身份／實際結果 | 下一步與界線 |
|---|---|---|
| #338 主列車 | `codex/train-337-continue-20261024`；固定產品／測試／架構 F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`；證據 E=`80fc475cef8cbb6dd01700a79ff9536f116d3015` | E 的非 evidence tree 與 F8 相同；只有 root 可續寫此分支。 |
| 正文 | 分支 `codex/train-337-continue-20261024-prbody`，D=`927db8e1670420139b7ad5802c9d62c989bf737b`，真普通 push 成功 | `/tmp/geo337-R8-prepared-prbody-publication-20261025/RESULT.json` 為原結果。此草稿所讀 pr-status 還列舊正文47ace3da；不能把分支已推送說成 bot 已套用，不重複排請求或空等。 |
| R8 原五 stage | F8，prepare/build/compare/perf/profile execution=`0/0/1/0/0`；累積 CLI=`0/0/1/1/1`；outer真exit1 | 全36樣本／4 profiles／175 scenes、350比較已收。五stage不等於八stage；all_required=false、full_acceptance=null，ABC_result原欄缺席。 |
| R8 性能 | N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`，皆≤1；N64/main=`1.2846970752586067`≤1.3 | 原量化門檻全綠，沒有放寬、不重抽有效R8。後續帳本採用不能把這輪改稱其他 execution SHA。 |
| R8 source calls／exact | N32=82668、N64=364369，比例=`4.407618425509266`≤4.5。exact仍同三個stdout mismatch，compare exit1 | role_priority、P8低／高凹角；原assert與版本基準保留。B′／C未核可，見公開逐項報告與QUESTIONS。 |
| F8 tracked帳本 | 原 `python3 tests/mutate.py --check` execution_head與product_source均為F8，exit1；120 stale／3 retired／0 invalid | 完整123已於2026-10-25T07:38:36.624220+00:00在F8正式啟動，RUNNING、尚無終態；生成完成與採用均不得預宣告。只由root在穩定來源整份重產，保留120個真execution.head；採用JSON後固定FINAL，再清除所有MUTATE_*跑原tracked check。 |
| 完整正式清單 | F8 full native、6 browser、P52、Q38全44、§7兩項、P-189 full與timing、required-eight／PF3／native後段、memo、reader／RC／#314／閱讀A專項皆仍UNRUN | H focused或R8量化通過不代替這些正式gate。native原16MiB stack、strict registry；性能與完整canvas獨占，其餘重工作最多兩個。 |
| H局部修正 | 原定向來源 S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`，14/14、exit0、零skip；原13方法不變，修正已入列車 | 固定／撤回／恢復actual memset工作量exit0/1/0、calls0/2/0、bytes0/255168/0；不是Windows或完整native驗收。 |
| 架構三裁判／四檔 | 真執行 M=`6e50aef65513b7b38f93228919272c6d40d6c196`，三judge exit0/0/0，205＋18、零skip；F8採用其report／receipt | 604inputs僅references.inc變動；scan與937／55政策不變；九guard各0/1/0、neutral2通過。最終正式三gate仍另跑，不把M移標為F8執行。 |
| required CI | F8 run40170221039／較早E815cd2e3 run40170692505各7 failure，runner_id0／steps0；原18 API讀0 | 當前E80fc475c的CI未讀，不能移標舊run。原annotation是付款失敗或支出上限；未改帳戶，亦無正式替代接受紀錄。 |
| native ROOT | `/tmp/train337-323-f64d638f-source` 已普通detach到F8，checkout真0，actual獨審通過 | 來源轉移不是全帳本或產品gate；full123獨立source/cache/seed與每filesystem入場已完成，observer正在執行，結果未定。 |

允許skip僅原Linux `py:test_gdi_contract` 缺compiled Windows GDI harness；新完整native未跑，不預先計入。不得新增skip、刪測試或放寬門檻。

## 本輪公開原件與不可混淆的結論

- [R8完整五stage原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/full-R8-five-stage-raw/)：9057 members／31,362,296B，tar SHA256 `4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0`。完整36樣本、四profiles、350比較原流及inventory在包內；七ELF是hash-only封包，原payload仍留雲端，不宣稱封包包含ELF。原OUT `/tmp/g337323R8`、tools `/tmp/geo323-final-r8-stage-tools-20261024`，不得覆寫或重抽樣。
- [R8小終態／CI／F8帳本check／原CLI與outer](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-terminal/)；小摘要 `/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json` SHA256 `23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd`。小摘要actual51/0只核原件投影，不是產品測試數。
- [三項exact的完整原輸出與Git歸因](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/REPORT.md)及[具體選項](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/QUESTIONS.md)已公開，獨審424/0。
- exact保留原 `verify_linux.py:156 assert not failures,failures`。引入提交 `6366304eb787b2a50282e4132f45e51eb7d21290`；固定b74與F8的I22整條逐byte相同，舊base訊息欠缺其自身條文要求的定位邊／超出區間。不能為追求綠燈刪必要診斷。
- 維持A：如實保紅、繼續其他工作。B′補診斷的比較基準會改exact版本邊界；C具名三pair政策會改允許差異規則，均需明確裁決，尚未採用。兩者均不改性能分母或重抽有效R8；P-189適用範圍仍須另外明示。Q-323-ABC／Q-P189-EXACT未解決，無隔離ABC接受結果。歷史P-189 `p189_verify.py:195 assert raw['base'] == raw['fix']` 亦首先在role-priority失敗，不把獨立timing當full exact。
- [H完整定向原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo323-reference-local-init-2c463557/)：2546 members，tar SHA256 `7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388`。支線 `codex/train337-reference-local-init-20261024`，S如表，E=`74a0a289b48f21f0211c4906808c79138b22b741`，D=`11a93b5b82a5c630b307da0d49bf79349149f58e`，均真普通push且已合入主列車。
- H把持續狀態分支不使用的127584-byte local零初始化延後到fallback。三phase persistent／fallback／allocation-failure／ordered-graph皆exit0；fallback實際校準各清零一次。完整撤回精確紅燈是 `ASSERT:persistent-reference-local-zero-work line=166 expr=local_zero_calls==0&&local_zero_bytes==0`。focused為O0，ELF hash-only；新O2 wall結果只以R8原樣本為準。未採rank-bound外稿不混入本修正。
- [架構完整原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/architecture-6e50-complete/)：380原件／4,630,676B，M真執行與F8採用分列。K provider-hint前一切片 S=`1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`、E=`4d3ac4bf42f431c23833c8841e4a7a597d275dbd`、D=`ae5e9431bfb8feb3b8b8aa9ecce523af3135a5ea` 保歷史來源及完整反證，已合列車，不冒F8 focused重跑。
- R5／R6／R7原件均已公開，歷史outer1與當時紅燈原樣保留。R7全包9128 members、SHA256 `8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e`；F7=`6df0264f75e84f03adb70746b6ac3db07a9910fc` 的N16/base1.05190582882169只屬歷史，不能繼續稱為F8當前性能紅燈。

## 其他工作線：保留自己的S／E／D，不冒F8新驗收

#344：`codex/issue320-connection-recovery-20261024`，S=`cbb318d76d7d242ae0db760ae15d57ef1cad4aa0`（一般merge F7），E=`a5ec136baf3909453867b3eed50f1b93b229ca59`，D=`b169e27ebb4b5835af50a4f070af290c7622630c` 已普通push。該S原strict aggregate9真0；完整canvas fixed／withdrawn／restored三phase仍UNRUN，未合主列車。舊S540的VM9/row9仍是歷史，不移標。

#348：`codex/geo300-capacity512-20261024`，S=`73b21e64dce72f0d16ca29e18559c51815b9724d`，E=`9a8584f57be7935604c3bad4c2481945a6ec3d9f`，D=`1f0e9d8633c333114f2dce74315a9903e36a0dd7`。H3、三helper與sentinel定向反證完成；兩個原方法的第一個placed512四指令批次仍各600秒timeout紅，尚未到sequential-history／canonical replay。原收件未留partial stdout，不能只歸因loadfile；原NativeBuild ELF已清除，保hash而非payload，重建必標新的ELF／closure。容量仍未合列車；原失敗包與環境補跑分列，兩原archive Git blobs不得刪。

下表沿用舊NEXT的既有工作線身份與驗收界線；縮寫是歷史記錄，不補造未驗的新SHA：

| 工作線 | 保留身份／owner | 狀態 |
|---|---|---|
| #339／#340 | specials；原 F38／S175 | 祖先已合；#340 最新審查已解除13 aggregate缺件，仍 required CI，不自行判已接受。 |
| #341／#343 | combined；W source=`df66452e7a514032453bea93b8b18ab74d7b1457`；E=`f7a389deafed64f0f3137c0086a7033841c709e3`，D=`37a2f117529c15c6525be79b17389d47b43a9acd` | 原定向36、plane整刀0/84/0與見證反證保來源；已入列車。#341 四類 work/CPU/wall不得冒已完整。未採 rank 外稿另保，不改已公開收據。 |
| #342 | backlog 準備，原 source=`eb846c34` | 祖先已合；新 strict native30尚未完整整合驗收，當前 Q38應44。最新審查的 native30／CI／base 阻擋保留。 |
| #345 | specials；原 S=`2199cda8`，E=`99646d418bc5e886a92bfdabe33e68780e88fe3b`，D=`c5515c14ac9cb59d147563f3dd75dbde5b75ca4e` | 六次19方法／零skip真0；四控制屬等價0，不冒 functional kill。尚未有可合併裁決，未合列車。 |
| #346／#347 | combined／backlog；原 S=`39273bc0` cut-list、S=`32403481` empty-row | 原公開定向／反證保原SHA；未合列車。各既有 E／D以歷史 NEXT／該 PR原收據為準，本輪未更新；raw-seam 外稿未C。 |
| #325／#331／#333 | Grok | 不碰分支。木工端頭／固定／RC 推理先讀核可決策及 #333 FIELD-RULES。 |

更早完整S／E／D及工具記錄保存在歷史 `handoff/NEXT.md`（`230113da9b919861862eccbeb2c339bda94044e7`）。#339既有最新審查接受F38→F1的498-path closure保留142 importer與三predicate，舊B3已解除；正式11／native／browser／ledger／架構、requiredCI及base接受仍待。#324舊入口仍需本機Claude可見重導向#339並凍結／關閉；雲端未代發留言或推Grok分支。#335未核可CLI初放能力仍僅準備／QUESTIONS，不擅自採入公理。

## ROOT轉移已完成，下一步是全123與同FINAL正式清單

原L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`已由普通 `git checkout --detach F8` 轉到F8。真readonly preflight為 `/tmp/geo337-native-root-transition-F8-preflight-20261025/`；真apply為 `/tmp/geo337-native-root-transition-F8-apply-20261025/`，07:06:28–07:06:38 UTC，exit0。未reset／clean／force，也未刪receipt、fixture或Git object。

apply保留原refs並另加 `refs/codex-preserved/native-root-L-before-75a1e938-20261025T070635Z` 指向L；6997個物化檔案／306,790,772B逐GitOID／SHA／nlink1通過，只有4個原定新C harness，無原路徑消失。Gitmetadata只index、HEAD、logs/HEAD為普通checkout預期變更；sparse與ignored `current_geometry.svg` 原bytes保留。actual peer `/tmp/geo337-native-root-transition-actual-peer-20261025/REVIEW.json` SHA256 `ab5b4e7fb1c9b991942f4ee05f5b15e8c08921693cbdbb98bd5b893ca45e04e5`。這批原流尚在雲端待另行正常出版，不宣稱已在E219。

五份fixture原bytes與Git身份都保全，禁止刪除：

- `tests/evidence/k2a-collection-capacity-20261012/legacy6a.gcanvas`
- `tests/evidence/k2a-collection-capacity-20261012/legacy6a-with-scene.gcanvas`
- `tests/evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas`
- `tests/release-evidence/20261008-cloud-closeout/contracts/grid-final/grid-rule-timber.scene`
- `geometry-web/docs/evidence/issue48-34a6222-20261005/archives/1280-full.gcanvas`

**全123已正式啟動，RUNNING，尚無終態收據。** 原 observer request 的 started_utc=`2026-10-25T07:38:36.624220+00:00`，source SHA為F8；原入口 `tests/mutate.py`，沒有只選子集。root session=`58101`（當次本機執行記號，接續時先查原進程／原件，不當作可跨工作階段重用的handle）；outer `/tmp/geo337-full123-F8-launch-20261025/`，job `/tmp/geo337-full123-F8-job-20261025/`，開始事實見 `observer/request.json`。原driver實際filesystem入場通過後才進observer；不能把啟動或部分列進度寫成完整通過。

來源配置 `/tmp/geo337-F8-full123-source-materialize-20261025/RESULT.json` 真exit0，SHA256 `c058ce31c147707643eeef027bbcd0e61d6c62450f56282c4251fd2ea9c0f229`；它只證原root／新seed／cache準備與closure，不是正式結果。先前root抄driver pin少了`a7`，原launcher在輸出目錄／鎖／admission／正式入口之前拒絕exit1；原失敗保 `/tmp/geo337-F8-full123-prelaunch-20261025/FAILED_PIN_TYPING.json`，formal_executed=false，修正CLI pin後只正式啟動一次，未改工具、門檻或產品。

由root單獨整份重產123（120自然項／3 retired），保每列真execution.head，完整原流封存；所有原終態完成並獨審後才採用帳本JSON、普通commit／push固定FINAL。正式tracked check必清除所有MUTATE_*，外置候選check不能替代tracked check。歷史正文D757發布時尚未開始full123；當前正文D927db8e1已同步真開始時間與RUNNING狀態，尚無終態，不把D757移標為已記錄啟動。

完整123的原prepare／observer／mapper保持。外部容量入場稿 `/tmp/geo337-full123-F7-admission-draft-20261024` 的名稱含F7只是工具來源歷史，真正request必綁F8；driver `7b6c57008921d7622ee6e47a987d7225a9318a7e53b582d3c1b9a1a5dd177eb1`、helper `bc93c7e37c29ed0ef3c93819e6e67ae0674f4b054ac7ab7df48a25ee718ba121`，原52/0 static peer。必同時計算TMP／workspace各filesystem的mutable seed、編譯池、全raw、Git出版與預留，不能用另一filesystem的free抵帳；來源轉移192MiB admission不替全123背書。完整操作順序保於 `/workspace/geo337-native-root-transition-and-final-chain-20261024/PLAN.v2.md`，其中R6舊紅／未轉移敘述是歷史，當前身份以本檔及F8原件為準。

採用帳本後的FINAL依原清單完成native、六browser、P52、Q38全44、§7、P-189 full+timing、required-eight／PF3／memo、reader／RC／#314／閱讀A及架構三裁判。原工具的source／OUT／cache request要精確新綁並獨審；不得拿歷史L/F7的綠改名。採用前後若只帳本／證據變，保存精確closure與真execution SHA，不篡改帳本head。

## 永久保全、排程及審查接續

**`/tmp/geo337-published-archive-git-objects-20261024` 是永久 Git object store，絕不可當cache清理、搬移或刪除。** 保留其lease、root alternates及所有已公開R5/R6/R7/R8/#348 blobs；原receipts、fixtures、raw與歷史失敗都不能刪。

歷史同bytes封包的共享inode只限已登記冷資料；所有alias保持immutable，禁止原地寫入，重新使用前須獨立解除每個alias。registry只追加，不回寫歷史nlink。四冷TMP群維護已真0且actual709/0，19原路徑全保，實際TMP淨增加137,879,552B；後續六群原RESULT真0（30paths、原net86,007,808B）與其獨立actual核對分開看，不推定全部storage已封包公開。WS375經獨立第二靜審後已原exit0，2622個原path全保，workspace free由57,393,152增至376,119,296B，實際回收318,726,144B；原件在 `/tmp/geo337-ws375-preserving-execution-20261025/` 與 `-launch`，獨立actual已完成19791項資料核對／0錯誤，收據 `/tmp/geo337-ws375-second-actual-peer-20261025/REVIEW.json` SHA256 `63a996840e8eb6f24ba881dd83adf6fa334ef3496f85cc1d75a04dad1b4e22a5`；同目錄IMMUTABLE_ALIAS_REGISTRY.json SHA256 `a919b549016076e75911ba7af42c0f2d27b40952009ec3deac0b718995f376f6`。完整維護收據仍待另公開，不冒已入E219。跨device容量因此可重新判定，full123原admission已真通過；磁碟維護不代產品gate。每次重工作前fresh df，不拿任何歷史free數字當當下容量。新工具／OUT／cache優先新私有TMP，永久objects與全raw除外。

本草稿所讀 handoff 為 `7a31dc436c78f16979b8f4cb97550118355f6d3a`；#338最後【ChatGPT 審查】仍是2026-10-24T06:38:46Z、head597bce6。B1完整final驗收尚未完成；B2性能部分已有F8/R8原量化綠，但跨版本exact與未核可B′／C仍紅；B3 requiredCI未解除。新正文已普通推D927db8e1，bot套用與新審查再讀pr-status／pr-reviews，不自行標READY。

每輪先fetch handoff分支，讀 `handoff/pr-reviews/*.md`、`handoff/pr-status.md`與`handoff/pr-requests/README.md`。新阻擋優先修；需要新PR／正文依既定5欄請求流程，已排請求不重複排，不等待bot空轉。等審查時照優先順序推進未合列車上的其他工作線；主線full123執行時可做靜審與小metadata，性能或完整canvas則獨占。任何紅燈保原assert／exit／輸出，先分類，未核可公理或數值政策寫QUESTIONS並繼續不受影響工作。全程無合併PR授權。

最新啟動證據已普通push：[F8 full123 RUNNING 收據](https://github.com/ZhiQiYang/geometry-axiom/tree/996aeded246090de87efc631a29cb7e4b5585d30/evidence/geo337-train-20261024/current-F8-full123-start/)；7葉349860 bytes，非evidence tree不變。此處只公開啟動、來源配置小收據與預啟動pin輸入錯誤，不宣稱整份重產已完成或所有維護raw已公開。

## 08:55 UTC 接續更新：不要重新啟動全帳本

原 full123 仍是 session58101、F8、07:38:36 UTC開始；08:55增量117/123，尚無真終態，不當通過。先用write_stdin讀真session終態並保存原工具回應（exit_code整數，完成後無session_id），再核job/outer原RESULT。不要重新跑已完成R8。

E80fc475c已普通推準備包882葉／6,948,494B（prepared-during-F8目錄881葉，另PROGRESS），非evidence精確F8；actual peer `/tmp/geo337-prepared-during-F8-publication-actual-peer-20261025/REVIEW.json` SHA7ec28ab4cd0e6349e13073b1b16c2c4331e28a400497c28094cb888fec792879。正文D927db8e1普通push0，原結果`/tmp/geo337-R8-prepared-prbody-publication-20261025/RESULT.json`；bot套用仍未見新status。QUESTIONS已另在Eecdcc22c補current，R8數值紅解除、exact三差與CI未解除，B/C無批准，P189不自動擴及。

立即順序：
1. 真全123終態後釋鎖，先檢磁碟；需要時由root執行兩項已審窄維護（不得在full123持鎖時跑）：七對terminal stdout TMP48,807,936B與Chrome純cache WS7,098,368B候選；精確v2 launchers及pins在 `/tmp/geo337-resume-resource-review-20261025/NEXT.md`，共同peer7a6923f7。新actual與alias registry仍需收件，不能把gross當已回收。
2. 全123終態collector用 `/tmp/geo337-F8-full123-terminal-preparation-v2-20261025/`，PREPARATION45058091b308950ee18af616f6add2e4fe6535dc130cd5dc390f57f175d3369f、peer7bab5cae204f0b0d79c4ef2b4464fae8c681e4eb051b47ca4c490bb6ae463628。新BOUND request綁真job/outer/工具FINAL；先verify再collect，全raw與123/120 F8/3retired/四phase必真核。壞子JSON可保原紅封包，但不得採用。讀README精確CLI，保全原ELF/source/cache、不刪。
3. 成功且原每列／raw／封包經另一peer後，root逐byte採帳本，正常commit/push固定F9；原120 execution.head仍F8，不篡改。清所有MUTATE_*跑真正tracked --check。原R8仍F8，不重跑／不移標；須證F8→F9只有ledger＋evidence差異。ROOT/seed轉移F9須另綁實際終態與只ledger差，不能直接改舊L轉移工具常數。
4. native原763a6e工具可參數綁F9；37條命令計畫 `/tmp/geo337-F9-original-gate-command-plan-v2-20261025/`。nonperf僅採v2 `/tmp/geo337-F9-nonperf-original-tools-v2-20261025/`（PREP593ab353、wrapper993ee010），原681／Q38全44，tiny Git no-renames真0/1/0；v1審查已撤回啟動結論。正式仍UNRUN。
5. browser分device單job工具 `/tmp/geo337-browser-single-job-split-preparation-20261025/` 已peer144/0（59ae64748d2e17232d1e894299e95fa910380f0d7391591141de2440ee2f0cb9）；來源WS、Gitdir/raw/job輸出TMP，原門檻與64MiBreserve保留。完整F9seed缺1025readonly葉的新增alias工具仍由resource owner備，未執行；不能拿nativeROOT冒seed，不可把含alias seed再給mutator。先fresh雙device預算，再逐job完整跑，canvas獨占。
6. memo只用F8 copy-only v2 `/tmp/geo337-F8-memo-counterfactual-tools-v2-20261025/`，PREPcee50f54e8c28b059c17a223091a2780b7268406d14474c200869a5fd3ed53bd；peer98/0 b370a26a0cdf0352bd19a78826338b50d0b405e715d6c36703409ed15cb00b6b（完整原pin以該REVIEW檔為準）。四處撤回精確H＋local-init；原R8三ELF只私有copy，增加4,340,968B之外仍須全成本預算；原same-F8/4.5/175ABC不改。driver各phase持heavy，root只保secondary，避免同heavy自撞。
7. #341成本外稿root v2 `/tmp/geo341-cost-preparation-v2-20261025/`，PINS008b50d645074777e38c2d2b61074d510a28e7069319b9afc79d20e2966cbeab；peer188/0 16a003022be036836fd665f70edd0cf63b82014ba508b18b57c1dbe9c94c36fc。修FACE截斷收件缺陷、五組0/1/0，C/性能未跑。僅F8 fallback，不冒舊Sc493全刀B1。
8. #348診斷工具 `/tmp/geo348-command-boundary-diagnostic-tools-20261025/`，current FINAL_INVENTORY.R3 e8967ccccfab8ff0f2c559917fa0667ff3c67ae9f38f98a512129b1070dce8af；小C原件 `/tmp/geo348-synthetic-c-protocol-20261025/`（61checks/26CLI），actual peer355/0 cf629f40fafd55259ab3a61554b7de035ed55c855a32aafba4f931df9d5eb067。未實跑r2不補重跑；產品ELF/原512/性能仍UNRUN，先固定真正產品來源與ELF再校準，原四指令整批600不變。

本更新是持續工作checkpoint，沒有停止或完成宣告；全123、native、六browser與專項未完成前不能READY。其他工作線原S/E/D以上表保留。
