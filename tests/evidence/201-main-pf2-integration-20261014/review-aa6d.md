【ChatGPT 審查】PR #201 head aa6d82c
已讀 AGENTS、SSOT D56/D57/I68/R54、base 0eb447e、全部57 commits、1480檔差異、正文及648則留言；以既審blob同一性及新增diff／子樹核對追到本次合流。未執行作者程式。

## 阻擋
- 無新增確證產品阻擋；`tests/evidence/201-main-pf2-integration-20261014/merge-proof.json:1–120`：aa6雙親為fd66＋當前main 0eb，已完成一般merge；舊fd66預檢的expected衝突不能照搬成目前缺陷。保留雙方增量，正式收尾見M1。

## 須改
- M1（範圍縮小）｜`tests/evidence/201-p104-wsl-budgets-20261014/README.md:56–60`、`tests/evidence/201-main-pf2-integration-20261014/merge-proof.json:94–119`：舊caf組合的完整雲端native已補齊；但aa6新合流只有整合證據，尚無固定新來源的正式列車驗收。2776是期望數，不能由213的2758／0／1或main的P-105結果拼成aa6通過。
  最小收尾：交既定下一班固定整合來源完成[P-104](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6153429711)正式驗收，附完整受測SHA、原始結果、actual exit，涵蓋四案及原Rule2的preflight／legacy，並同步正文交付SHA與驗證狀態。第9班native2751／3／1、兩次Rule2仍不豁免；canvas依裁決歸#209，不另算本PR產品缺陷。

## 記錄
- R1｜`tests/run_all.expected.json:99–103,142–146,217–221,252–256,427–431`：獨立讀caf／0eb／aa6後逐suite核算，ownership9＋4＝13、Node659＋44＝703、grid13＋2＝15、main新增PF2＝17、compat28保留；88登錄suite／82計數suite／2776項正確。保留此合流結果，不調低期望數。
- R2｜`geometry-web/engineering_bridge.inc:40–65,105–137`、`tests/run_all.py:55–60`：PF2的panelFill序列化與runner依賴承接main，K2a的刪除receipt／preview token和finish_batch分派仍在；其餘K2a產品及四案測試blob未被合流改動。維持雙方路徑，不整檔擇一。
- R3｜`tests/evidence/201-p104-wsl-budgets-20261014/native.stdout:113–201`、`native-actual-exit.json:1–6`、`run_native.py:13–18`：完整雲端213的87個suite逐項對expected相符，2758通過／0失敗／1允許GDI略過、Node703、reader41，child actual exit0先落檔，wall822.379秒與suite合計792.3秒分開。舊M1「只有四案子集」已解除；保留受測213／caf與非WSL界線。
- R4｜`tests/test_reference_workspace_races.js:4,123–150`、`tests/evidence/201-p104-wsl-budgets-20261014/README.md:7–16,37–48`：15／22／31／21秒仍由全部已報WSL最大值取2.5倍向上整秒，78個callback／原斷言／一般5000ms不變；前輪獨核67件控制原件、四案修前→修後→撤修→還原各1→0→1→0。保留負控制，8次紅為timeout cancellation，不冒稱語義mutant killed。
- R5｜`current_geometry.c:1–13069`、`tests/mutants_results.json:1`：本版C精確等main，468323 bytes／13069 CRLF／零裸LF、裸CR、NUL；整個core、mutate、run_tests及帳本0818df5均承接P-105 main。沒有本PR新核心變異重跑，不能把舊caf帳本當本版帳本；核心來源／裁判相同可沿用main結果，勿手改hash。
- R6｜`tests/evidence/201-p104-wsl-budgets-20261014/README.md:50–62`、`native-summary.json:2–13`：22份公開文字／空檔／source快照hash核符，前後source blob相同，198份納入與21份排除log清單互核；兩份新gzip因連接器不支援二進位未能獨立解包，216／1342 members及五binary閉包僅核文字清單相容。保留作者驗證與審查可驗範圍，不另增base64鏡像或格式門檻；20份WSL TAP仍按既定本機交付。
- R7｜`公理層.md:759–785,1353–1364,1811–1829`、`geometry-web/engineering_bridge.inc:105–137`：SSOT、整個guide／唯一閱讀器、決策及BACKLOG精確同main；本次PF2是上游合流，無自加K3或UI入口。維持合法存量捨棄可保存、真內容變更仍須容量接納的區別。
- R8｜`tests/run_all.expected.json:1`、`geometry-web/engineering_bridge.inc:105–137`：與仍open的#192/#193/#194/#196/#202/#206有10個PR–路徑交集；未以交集冒稱真衝突。已合併的#225/#231不再列open衝突，後續列車保留各suite增量與雙方分派。

改完 1 項可合併
