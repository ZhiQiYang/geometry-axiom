# 回收分支固定候選 F 的最小方案（僅準備）

本文件沒有修改產品、分支、裁判或比較器，沒有重跑驗收，也沒有取得新的批准。root 可以在自己獨占的 `codex/train337-recovered-evidence-20261026` 接續，既有 train 與私人 publisher 的 HEAD/index 不必移動。

已唯讀核對 `refs/remotes/resume-20261026/train`=`a6f4013364e21bcb7239b5dcc25caac0f6d61f77`（下稱 A）、handoff=`6e0d142fe1afa8f325d927ac3c5afb1ac3e2902c`。S10=`82c922a3941525d3a094ac0158bdc7dea57ea360` → A 的非 evidence 差異只有 `決策佇列.md` 新增22行；不是新的產品或測試修改。

## 可以直接保留的原件

- S10 完整123帳本及實跑收據：生成 ledger SHA256 `a4b5f1957e4bde6d30e4c05328e8a8dc1282fa811c52260eb01670cd560d56e7`。所有120個實跑 `execution.head` 保持 S10，不改為 A/F。不能因新 Git head 或新決策文字再重產一整輪。
- 根據 `tests/mutate.py:889–904,1305–1347`，有效性取決於來源/include closure、變異定義、oracle、原執行收據與 checksum；`tests/mutation_bridge.py:102–113` 的 bridge oracle 輸入是 tests/*.py、tests/*.c、tests/fixtures/**/*.scene 和根 *.scene，不包含決策文件。A 與 S10 的上述檔案皆無差異。因此先逐byte採用已生成ledger，之後以真正 F checkout 跑 tracked `python3 tests/mutate.py --check` 決定有效性；不要先預設該檢查已綠。
- 四檔中 manifest 與 scan 的既有bytes可以保留，仍須由新來源原三裁判再次證明。S10 report/receipt 只能保作 S10 歷史；A 的決策hash已是 `e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740`，不能把舊快照移標。
- 原 c387 recorder、recursive `ls-tree`/`mktree` 核心、Git OID/bytes/SHA核對、原 native wrapper/driver 與新 SHA request 綁定可沿用。不要重做工具全集或另一份完整 native clone。

## 建議順序

1. 先正常發布已完成原件；在開始產品工件採用前記錄回收分支當下完整 parent E。E 相對 A 除 evidence 外必須零差。
2. 在既有 publisher object store 上建立一份**僅架構用的私有 sparse checkout**，HEAD=A，不 fetch、不複製整份 Git objects，也不改既有 native ROOT/F10-pool。物化原 manifest 所列604個執行輸入，外加三個 judge、四份舊工件、兩份 SSOT 與實際 import 所需的 package metadata；逐Git/tree核完整選集，不能只憑604這個數字判準。這不是新完整 native checkout。sources 可從既有 immutable pool 讀取；若使用 readonly hardlink，需事先核所有 alias 不會被寫，不能原地改共享 inode。
3. 在 A 跑三條原架構命令，原參數、205/18、零新增skip保持；完整錄下 source/env/argv/stdout/stderr/exit。這是 A 尚未跑過的命令，不能把 S10 三條收據改 SHA。依舊schema組出四檔：manifest/scan若相同保原bytes；report/receipt更新當次實際來源 A、兩SSOT快照與原三gate。歷史 M6e50 九組反證保持歷史來源。
4. 更新小型 adopter 的**身份綁定**，一次將 S10 ledger 與 A 的 report/receipt 三個現存葉採到回收分支 E 之上。manifest/scan必仍等於 A；其餘所有產品/測試/SSOT保持 E。用 commit-tree產生單parent F，對回收 ref 做預期舊值 CAS 後普通 push，再核遠端 commit/tree/三個完整blob。全程凍結原 publisher HEAD/index/train ref。
5. F 可遠端解析後，完成既有 native v2 focused proof尚缺的真runtime；綁 F、原 native F9完整index/sparse與五fixture、精確五葉 delta、候選分支的完整 remote observation。只將既有 `/tmp/train337-323-f64d638f-source` 普通 FF 到 F。先有真容量守門、source/provider leases與對抗稽核，不能只填true視為完成。
6. 在 F 跑 tracked ledger check、完整 native、六組 browser、Reading A oracle，以及最新規格明列必跑項。完整canvas獨占；其他重測最多兩組。原時限、golden、斷言、唯一Linux GDI skip保持。六browser用既有準備的隔離來源/埠/TMP，先完成其尚未做的來源與工具准入，不能把F9六個0移標。
7. F 上的三架構原命令也留正式收據；可再於來源外產製綁F的四檔，**放入 evidence 作當次權威收據，不為內嵌 F 再無限製造新 F**。canonical 工件的生成來源 A、採用來源 F、F 當次gate/evidence head要分列。四個衍生工件明確排除於自身604 inputClosure，receipt不hash自己；此界線有原schema依據。若後續再改產品/測試，依實際closure變動另處理，不能只改標籤。
8. 把回收分支的新F、所有真終態與未跑/待核項交 train 以一般 merge 收斂。這不等於本代理有權合併PR或寫main。若train在另一環境有新產品改動，先做完整差異與受影響gate分析，不強行推同一分支。

## 三葉 adopter 必改的身份守門；其餘不要放寬

現稿 `/tmp/geo337-S10-three-leaf-adoption-preparation-20261025/adopt_three_leaves.py` SHA256 `9e53c8275ba8861679bca6cebe16d7a9f8b3436ee5feb13d30d501139e04797b`，**不能直接執行在 A 或回收分支**。目前固定 BRANCH=train，要求S10→parent非evidence零差，並要求ledger與架構都源S10；它正確地會拒絕目前輸入。

| 原守門 | 最小適配，保留拒絕未知變更 |
|---|---|
| 一個 SOURCE=S10 同時驗ledger/architecture | 拆成固定 `ledger_execution_sha=S10` 與 `architecture_execution_sha=A`。ledger terminal/INDEX/120execution heads/3retired仍逐項驗S10；architecture RESULT/receipt/sourceBeforeAfter/三gate/604/四bytes改驗真A。每類peer分開綁實際source，不以request自行宣稱成功。 |
| S10→parent排evidence零差 | 改驗 A→parent排evidence零差；另外保存 S10→A 的精確單葉 `決策佇列.md` old/new mode、Git OID、bytes、SHA和22行新增證據。任何其他葉拒絕。這不是把決策新內容當成已核批准。 |
| `clean(parent)` 要求現有publisher HEAD=parent/BRANCH=train | 保留publisher當下歷史 HEAD/index/status/train ref 快照；改核**目標回收分支 local+remote ref=parent**。原 HEAD 不必等於目標分支parent。 |
| `merge --ff-only F` 更新現有checkout | 保留單parent commit-tree，使用 `update-ref refs/heads/<固定候選分支> F <expected-parent>` 原子CAS；普通push同名ref。不得checkout/reset原train，不得force push。前後原HEAD/index/trainref完全相同。 |
| final相對S10僅三葉 | final相對A必恰三葉；回收parent→F也必恰同三葉；manifest/scan等於A，其他產品/測試/SSOT bytes不變。 |
| 遠端查固定train ref | 精確換成固定候選分支；原remote commit/tree/唯一parent、三完整blob、最後ref再核都保留。 |

`build_tree()` 的固定三葉allowlist、只允現存100644、拒多葉/缺葉、原件不能在publisher內、完整原始peer binding、64MiB reserve、普通push、遠端全bytes校驗、原WS provider保全等都維持。只針對上述身份適配做小型撤回/恢復與獨審，不需要重跑完整帳本來驗工具。

分支常數必拆成 `CANDIDATE_BRANCH` 與 `HISTORICAL_PROVIDER_BRANCH=train`。舊WS `before['branch']` 仍驗原train，不能因候選分支而移除或改掉它；publisher HEAD的原train身份也須維持。

## 架構 assembler 必改範圍

`assemble_architecture_v2.py` SHA256 `b51110ff9756326a2b47d2ae4a6aded2a7995d92e2a882ddf9ec4065fae87d17` 現在固定S10/F10-pool與S10原六gate batch；不能單改 SOURCE 常數就宣稱新來源通過。

保留 `snapshot()`、604精確輸入、Git/raw/LF/closure、protected兩SSOT、工具hash、manifest/scan原bytes、前後乾淨來源與四schema寫法。新綁A、架構用checkout、A原三gate原件／peer／完整source manifest；`validate_gate()` 的 exact argv、source/cwd、exit、完整流hash及205/18/零skip不變。改用三個新gate的明確索引，不能把原S10六gate退出碼1/0/0/0/0/0改成新全綠。新決策hash只來自A Git bytes；不編輯決策內容，不推定新的批准。

## Native v2 真實就緒程度

`transition_native_final.py` SHA256 `6e93e96f732df9b15f869327422de1aecd424b708f36e2f3d5eb3d738af86845`；獨立 `REVIEW.v2.json` SHA256 `00061250c282cbe43130793ed368f8179db87e794bd1422d3f65d08e154ade0a` 是**static exit0、runtime UNRUN**。不能拿舊eba3版本七例當此版通過。

- 五個候選delta路徑已包含 #314測試、決策、ledger、report、receipt；A新決策不用擴大allowlist。request仍需真F所有非evidence差分逐葉old/new完全匹配。
- `production_policy()['branch']` 固定train，需在副本精確換回收分支；remote完整原命令和ref regex一起由同一policy導出。這是身份適配，不接受任意remote/任意分支。root先取得原c387五檔，工具內仍不發網路。
- provider HEAD不要求=F；只要求F在provider objects可解析、F9為F祖先、F為已發布ref祖先，且provider metadata/objects保持。因此原publisher HEAD/index可一直不動。
- 既有focused runner可沿用：新policy binding後做新v2八例及四個單guard 0/1/0；root准入後新fixtures/capture/TMP一律落新OWN child，不加/tmp大型fixture。
- 原transition64MiB與native128MiB是不同守門，數值不變；目前/tmp不足由root處理。此方案沒有執行或授權任何cache退役。

## 仍未核實／不應假定

- 新決策的P-189白名單與沿用規則目前只有repository轉錄與新審查引用；原始批准尚待root核實。不要改比較器，不要把原先UNRUN項目當成已有F9結果。
- R8原36樣本不重抽；其原outer1與實際性能值維持原來源。Q38/F9、reader/F9、axiom/F9等已完成證據可先保留和附closure，不能在批准未核前自行宣告同final全綠。
- §7 card、P52、P-189 full、required-eight/PF3/whole-memo/RC等真正未跑項仍未跑；資料封存成功不是產品驗收成功。
- 本計畫只核了既有工具與Git文字，不建立checkout、不修改ref、不跑任何judges/proof/native/browser/oracle。下一份工具的runtime與真正F尚未存在。
