本 PR 接手並取代 #337，整合 #299+#316、#314 題3鎖定比較器、#318 已核可閱讀 A 及 #323 memo 修正。唯一最終驗收來源 **L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`** 已一般推送；目前仍是 draft，**B1 同 L 完整驗收未完成，B2 原跨版本 exact 比較及新 B3 required CI 失敗仍阻擋合併**。

L 的 C/JS 產品沿自 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`，正式測試沿自 S=`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0`；相對帳本生成來源 b6，L 只採用原 `tests/mutants_results.json` 及 evidence，沒有修改產品、測試、裁判或判決欄位。架構 manifest 修正與 Linux 四檔已先按原 schema 採用。目前 evidence head E 為 **`30d80ddab38ec14bd6cf2033da93c3e6f1256908`**；往後純 evidence 提交另記 E，不移動 L，不把 E 當受測 SHA。

### 唯一 current-state 矩陣

下表 UNRUN 皆尚無本 SHA 的正式執行結果；歷史 F/S/b6 結果不填入 L 的通過欄。L 的 tracked check、完整123及三架構裁判已有正式終態；完整123於2026-10-23 22:25:15 UTC啟動、23:00:25 UTC完成，四原phase均0。L閱讀A兩個原CLI亦已0；reader三條及RC兩組精準反證亦已完成，原件已於E的final-L-readers-RC公開。

| Gate／事項 | 實際來源 | 原 exit／目前結果 | 範圍與限制 |
|---|---|---|---|
| 最終完整 123 帳本 CLI＋tracked check | L | **0／0／0／0；root 0** | tracked check／完整123 CLI／core-map／external-new-check全0；114 killed／5 equivalent／M20原允許crashed／3 retired，120 execution heads均L。終態原包及獨立核對已公開於E/final-L-ledger-complete |
| 完整 native | L | **RUNNING，無終態exit** | `ulimit -s 16384; python3 tests/run_all.py --build`；原 expected、斷言與子時限不變 |
| canvas | L | **UNRUN** | 原 workflow 完整 job；獨占，獨立埠／暫存 |
| assembly | L | **0；原件已公開** | 原150 assert／0skip／191.692s<原15分鐘；原job既定partial模式不比golden，非完整canvas |
| documents | L | **0；原件已公開** | 原47 assert／64.316s<原10分鐘；原exit0／outer0／前後sourceguard0，8截圖 |
| grid | L | **RUNNING，無終態exit** | 原 workflow 完整 job；獨立埠／暫存 |
| space | L | **UNRUN** | 原 workflow 完整 job；獨立埠／暫存 |
| timber | L | **UNRUN** | 原 workflow 完整 job；獨立埠／暫存 |
| P52 放置後 timber 出現耗時 | L | **UNRUN** | 原放置／呈現判準及耗時收據 |
| Q38 | L | **UNRUN** | 原 `tests/section_profile_mutation_check.py` |
| §7 card-reference／axiom mutations | L | **UNRUN／UNRUN** | 原 `run_mutations.py` 與 `run_axiom_mutations.py`，不縮項 |
| P-189 | L；main adbaebf9／base 3e600772 | **UNRUN** | N=16/32/48/64 三方交錯；每點 fix/main≤2×；固定base的171原scene＋4生成案，共175組完整load回覆／dump逐bytes相同（原拒絕案保拒絕，4生成案須載入成功） |
| #323 fixed-three／required-eight／PF3 | L | **完整native執行中／UNRUN／UNRUN** | fixed-three原load_residual13／host_facts_authority22／contact_sources15由完整native精確module覆蓋，不另重複C；required-eight原676、PF3原20/19/20仍各依原專項 |
| #323 原 timing／profile／完整 memo 反證 | L；原 base b74f9a2／main adbaebf9 | **UNRUN** | 原 36 timing、4 profile、N32/base≤1、N64/main≤1.3、calls64/32≤4.5；memo 撤回／還原保原斷言與分母 |
| #323 跨版本 175 場景／350 組 exact | L | **UNRUN** | 原 comparator 保留；下列歷史 exit1 仍是 B2，未獲裁決前不能宣稱解除 |
| reader 三條 | L | **0／0／0** | 原 sync 生成、`--check`、`tests/test_axiom_reader.py`（51）三 CLI 各自原退出碼0；終態原件已於E的final-L-readers-RC公開 |
| #314 六 suite 103＋Node inspector 13 | L | **UNRUN** | 由完整 native 的精確六個 module／Node 檔 argv 覆蓋；保各原 row/subtest，不另重複 C；Node 非 browser |
| 閱讀 A native 7／oracle 14 | L | **UNRUN／UNRUN** | 由完整 native 的兩個精確 module 覆蓋；typed facts 不代表 #335 真 CLI 初放支持 |
| RC-run 精準 builder／checker 源撤回 | L | **0/1/0／0/1/0** | 各以原單一方法、6 個原 assert 做 0/1/0；這兩刀未被完整 native／全帳本／quick 的其他控制取代 |
| 閱讀 A `--mutants-only`／完整 `--quick` | L | **0／0；outer 0** | r2同L環境閉包修復後正式完成；9402矩形逐毫米、14208二維、凹角579×8、step410×8／mirror820×8、odd1872、額外t10 mirror392、正例528／1056全保。原t4族6筆已知C11_MAIN_NOT_BUTTED另案保留，未改原判決；不宣稱此6缺陷已修 |
| 架構三原裁判 | L | **0／0／0** | architecture_contract、test_architecture_contract（205）、test_product_architecture（18），零skip；604輸入、HEAD/index前後一致，原流在 E/final-L-architecture |
| 帳本生成歷史（不是 L 驗收） | b6e1e45425f055cd825b259f46ef2c454f3ff13a | **1／0／0／0** | 生成前舊 tracked check1、完整123 CLI0、core-map0、external-new-check0；114 killed／5 equivalent／M20 原允許 crashed／3 retired，120 execution head 自然 b6；原 root0 |
| B2 歷史跨版本 exact | F 對原 base b74f9a2 | **1，仍阻擋** | 三個 #299 V_EXTENSION 診斷差異；同列車 memo-only 對照不取代此門檻 |
| 舊 B3 原始證據入庫 | 已公開 evidence | **已處理；非產品 gate** | 五原包、inventory、hash、指令與完整 streams 已入庫且可獨立重算 |
| 新 B3 required CI | Actions run40034196788；實際head c6c0b0d | **7項 failure；環境阻擋未解除** | 七check-run各有付款失敗或支出上限annotation；runner_id=0、steps=[]。原API真0；不是L測試結果，不能列pass或skip |
| M1 Q-314-SSOT 現況更正 | 已公開 QUESTIONS／正文 | **已處理；非產品 gate** | 現行提交例外已採納；後續精確有序補句的寫入差額另列，沒有重新要求決策 |

**允許 skip：沒有新增。** 只保原工具既有具名允許清單（包括平台適用的 Windows GDI 項）；各尚未執行項不預報實際數量。Chrome156.0.8078.47、Nodev24.19.0、NotoCJK 已在雲端可用；browser 未跑不可改標成通過或環境 skip。

### B2 仍須解除

原 #323 比較的三個差異場景為 `_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。#299 為現行 I22 補上 `V_EXTENSION` 定位邊與超出區間，因此原完整 stdout/stderr exact 比較 exit1。dump、完整有序來源圖、五 guards 與允許／拒絕相同，不會把原 exit 改成 0。

最新審查明確要求恢復原 exact，或先取得並登記診斷版本界線及相應 comparator 的裁決。現行 I22 與既有測試要求這些診斷欄位，不能刪回短訊息、忽略文字、正規化輸出或自行放寬比較器。同列車只撤 memo 的175／350 exact 與原性能0/1/0已在 F 完成，但只是新增因果證據，不能解除跨版本 B2。本輪保留原 comparator、功能與紅燈，其餘 L 驗收繼續。

### 原件、歷史及執行界線

L 原tracked check的完整指令/環境/streams、39條已完成preflight與起始request在已公開 `evidence/geo337-train-20261024/final-L-start/`。本次完整123已真終態；原完整CLI／外層／原raw／工具的1354-member封包與三份peer已由root一般推送至Effa6e438的`evidence/geo337-train-20261024/final-L-ledger-complete/`。L架構三條與前後來源身份在 `final-L-architecture/`；原命令全0、generic205/product18、零skip。899/646獨立核對只驗證收據與來源，不替代任何其他gate。

b6 於22:08:38 UTC真完成123項，原JSON逐byte採用成L，沒有改head/date/verdict或補造row。原完整指令、環境、所有 streams、失敗沿革與清單在 `evidence/geo337-train-20261024/ledger-b6-complete/`；生成前check1完整保留。先前4f4的磁碟不足 CLI2／root1／108項、15未跑仍是歷史環境失敗，不混入新帳本，也不在本表當成 L 結果。L 的新完整123外部JSON只封進後續 E，不再次改 tracked ledger，避免自我引用。

舊 B3 五包47,120,357 bytes已公開於 E `bea6f30995da1425ebe375a37d871e4f19c54a2d` 的 `evidence/geo337-train-20261024/geo323-full-originals/`，包含完整 inventory、hash 與5272原stdout/stderr。F 的 #314、閱讀A、RC-run、架構、#323固定套件／timing／profile／memo原件也保留實際 SHA；歷史通過只作 provenance，不取代本輪 L。獨立 peer 核對數只證明收據／來源保全，不計成產品測試結果。

reader 生成會寫 canonical 閱讀器的暫存再替換原檔，RC兩刀僅產生 ROOT 外精確variant。L全帳本已終態且root已交還clean ROOT；已於23:06:44～23:09:25 UTC在完整native前獨占ROOT完成reader三條及RC兩組，原初末HEAD=L且status/cached空，正常釋鎖後交還root；保原前後SHA／clean／bytes，與§7等暫改source項互斥。完整 native 的 oracle 預設 CI 抽樣不代替另列的完整 quick；所有專項沿原driver／argv／斷言／時限，第一紅仍保存並繼續獨立項，不刪測試或降低門檻。


閱讀A原件已由root一般推送至E3c663。r1兩CLI原exit1是薄checkout缺`make_golden`的環境失敗，完整原流／guard與同L補齊22檔閉包過程保留；未算突變擊殺。r2於22:39:03～22:45:53 UTC執行，原mutants0、quick0、outer0，初末L／22檔bytes／完整index stage相同。quick原印39850是原顯示計數，不能冒稱涵蓋全部內部build、odd及額外t10對照；兩組528／1056正例皆missing0、nonbuildable0。原t4族6筆`C11_MAIN_NOT_BUTTED`依原判官另案保留；沒有刪案、改golden、放寬斷言或新增skip。此oracle證據不表示#335真CLI初放可達。

新B3與上述舊原件B3分開：[Actions run40034196788](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40034196788)在head c6c0b0d的七個required job仍為failure。七份check-run annotation逐項明示「recent account payments have failed **or** your spending limit needs to be increased」，因此屬排程前帳戶付款／支出上限環境阻擋；API未區分是哪一項，不作進一步猜測。七job均runner_id0／steps空；原14條API／Git命令及完整流已取得並獨立核對，分類報告及完整原流已於E的actions-40034196788-environment入庫。這次沒有重跑CI、改帳戶設定或修復限制；B3不能自動解除，同L雲端補跑也不冒稱CI綠燈。gh不支持`attempt`欄位的原讀取1及刪欄位重讀0皆保留，並非API403。

M1 已更正為現行 D10b 提交相容例外、I24 參數卡改值例外、D29 按當下有效值解除引用均已採納。10/23另核可的精確有序補句尚未逐字寫入／同步的差額留在 QUESTIONS；不把既有條文寫成暫緩，不重問題3／4。#335 的13mm薄牆階兩種初放路徑仍另追蹤，oracle可施工不代表 CLI 已支持；本輪不新增放置公理或豁免。

後續 #339／#340、GEO260、#300新索引與#320各自分支的定向驗收保原SHA，不轉標成L、也不充本PR gate。無 force push、無合併 PR；儲存維護不列產品驗收。B1 全部正式項、B2 與新 B3 未解除前，不標 READY-TO-MERGE。

最新已讀審查：handoff `48e82e72` 的 `handoff/pr-reviews/338.md`，最後評論2026-10-23 22:39:41 UTC、head c6c0b0d。舊B3原件入庫與M1已處理；新B3是七required CI未啟動的環境阻擋。本文只保一個current-state矩陣，依真執行SHA／原exit列示；peer核對數不當產品gate結果。

documents及assembly皆真完成並獨立核對，670／672-member完整原包已分別公開於E的`final-L-browser-documents/`與`final-L-browser-assembly/`，保完整原指令、退出碼、環境、SHA、streams、runtime fingerprints與8／9截圖。peer3420／3431核對不算產品assert；原cache/ELF排除清單明列且未刪。完整native session80260續跑、grid session85457占第二槽；canvas、space、timber尚未執行，canvas仍須獨占。原native230列／35分鐘與各browser原CI時限不變，未終態者不標綠。

browser外部執行工具只新增允許輸出於/workspace且repository外的路徑，解決/tmp容量限制；native仍只用/tmp，原workflow／golden／斷言／時限不變。舊storage工具實際也限制/tmp，先前交接的可直接使用workspace描述已更正。七批已終態儲存維護的完整原件及collector最外原流已封`terminal-maintenance-seven-originals/`，保所有收據、fixtures、Gitobjects、受控source；快取退休／相同archive hardlink去重與原raw保真搬移不是產品驗收。
