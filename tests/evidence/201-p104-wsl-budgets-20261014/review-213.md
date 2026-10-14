【ChatGPT 審查】PR #201 head 2135324
已讀 AGENTS、SSOT D56/D57/I68/R54、base caf4985、全部55 commits／1449檔差異、最新正文與645則留言；1413個既有變更blob與a09相同，另核2檔改動、34個新增證據檔與main整合。未執行作者程式。

## 阻擋
- 無新增確證產品阻擋；一般merge及P-104具名時限處置已實際完成，不能再把前版「未合main／未改時限」照搬為本版缺陷。

## 須改
- M1｜`tests/test_reference_workspace_races.js:123–150`、`tests/evidence/201-p104-wsl-budgets-20261014/README.md:16,27–31`：仍缺修正後整合來源的正式驗收。第9班90659e6原native2751／3／1、兩次Rule2不豁免；本輪4案子集與16次節流控制不能證明完整703題／整班已綠，最新正文亦明說213的完整native仍在執行。
  最小收尾：依[P-104](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6153429711)將本修正交下一班固定來源的既定正式驗收，附實測完整SHA、原始結果與退出碼並更新正文；完整native須涵蓋原Rule2另紅的preflight／legacy live-ref，保留第9班紅燈，不借舊ade6或四案子集抵銷。canvas依裁決歸#209，不另算本PR產品缺陷。

## 記錄
- R1｜`tests/test_reference_workspace_races.js:123–150`、`tests/evidence/201-p104-wsl-budgets-20261014/budget-basis.json:1–58`：四案完整WSL觀測最大值5851.711680／8789.908087／12359.045071／8105.571139ms，以ceil(2.5×max/1000)×1000得15000／22000／31000／21000ms，全在2–3倍內；已納入第9班三輪較慢值，未用新五次較快樣本取代。保留此具名預算；取消時的duration仍非完成成本上界，最終以M1驗證。
- R2｜`tests/test_reference_workspace_races.js:4,123–150`、`tests/evidence/201-p104-wsl-budgets-20261014/registration-proof.json:1–45`：自製靜態核對確認78個註冊的名稱／順序／callback未變，只改四項timeout；普通捨棄UndoRedo、三次真ZIP往返、raw／refs／orphan／容量及零API斷言保留，一般5000ms未放寬。不是只驗「沒報錯」，也不把註冊比較說成78案實跑。
- R3｜`tests/evidence/201-p104-wsl-budgets-20261014/controls-run.stdout:1–16`、`controls-summary.json:1–210`：812542-byte壓縮原件的67個member逐件bytes/hash核符；四案修前→修後→撤修→還原各1→0→1→0，8紅為timeout cancellation、8綠各1 pass／0 fail／0 cancelled，wrapper內嵌來源對回a09／本版。保留這個時限負控制，勿稱語義assertion killed；它不能取代M1的正式負載。
- R4｜`tests/run_all.expected.json:99–103,142–146,217–221,252–256`：共同基底2004c6c三方增量逐suite核算全符：Node659＋44＋0＝703、ownership9＋4＋0＝13、grid13＋2＋0＝15、compatibility24＋0＋4＝28，其他不變；87 suites合計2759個計數項。861雙親為9e4＋caf，213僅新增17個證據檔。整合／期望數缺口已解除，勿再調低門檻。
- R5｜`current_geometry.c:1–13067`、`tests/mutants_results.json:1`、`tests/evidence/201-p104-wsl-budgets-20261014/main-mutation-receipts.stdout:1–4`：C實際468109 bytes／13067 CRLF／零裸LF及NUL；C、整個core、mutate、run_tests與其139個場景blob全等main。保留main帳本合理，本次未重跑核心變異；`mutation-freshness.stdout:2–48`的舊cache造成45 stale原件仍在，另核原main收據才得40 killed／1 crashed／4 equivalent／3 retired／0 stale，兩者不得混寫。
- R6｜`geometry-web/engineering_bridge.inc:102–115`、`公理層.md:759–785,1353–1364,1811–1829`：preview刪除token與PF-1分派均保留，K2a產品blob未被本輪測試修正改動；SSOT、整個guide／唯一閱讀器、BACKLOG及決策佇列精確等main，無新增UI或K3越界實作。維持存量捨棄可保存、真內容變更仍須容量接納的區別。
- R7｜`tests/evidence/201-p104-wsl-budgets-20261014/README.md:18–24`、`train9-first.log:1`：第9班完整公開ZIP已獨立重組，外14件／內3782路徑逐件bytes/hash核符，原Node三輪700／0／3、700／0／3、701／0／2仍紅；未另宣稱1531來源與23 binary的全部執行關聯已獨核。新20次WSL完整TAP改由[本機交付](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6160470969)，本輪僅核公開摘錄，不要求新增base64鏡像。
- R8｜`tests/run_all.expected.json:1`、`geometry-web/engineering_bridge.inc:102–115`：與#192/#193/#194/#196/#202/#206/#225/#231有18個PR–路徑交集、5個唯一共用路徑，blob均不同；未以路徑交集冒稱實際衝突。後續列車按各suite增量與雙方分派核合流，不整檔擇一。

改完 1 項可合併