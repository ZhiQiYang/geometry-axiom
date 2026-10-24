# 待複審釐清的驗收界線

本檔供後續審查判讀，不等待使用者回覆才做其他工作。未採用新的公理、數值門檻或忽略差異的規則。

## Q-323-ABC：跨功能版本的診斷文字差異

原 #323 固定歷史 base `b74f9a2ae7ade1555b9be45283adecc097fb76e3` 對列車 F `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9` 的原 175 場景／350 組比較真 exit 1。只有以下三個完整 stdout 不同：

- `_role_priority_mutant.scene`
- `_s1_p8_l_room_primary_through_reflex_extension.scene`
- `_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`

差異是列車既已採用的 #299 診斷文字：`V_EXTENSION` 增加定位邊與超出區間。來源 `6366304eb787b2a50282e4132f45e51eb7d21290`；產品的允許／拒絕、dump、完整有序來源圖及五 guards 保持一致。原 #299 的低側／高側／兩側精確文字與錯側排除均有既定正反例，不能為了舊跨版本比較轉綠而撤銷這項功能。

建議的處理是保留原跨版本 exact 紅燈與全部差異，另外使用同一列車、只撤回本次 memo 的對照版本，逐 byte 比較原175全部輸出／有序圖／guards，並做完整 memo 的性能撤回／恢復。這是新增的隔離修正證據，不把歷史紅燈重新標成綠，也不過濾 error 文字或刪除場景。N32/base、N64/main、source-call 比率的原性能分母與門檻完全不換。

首輪 #338 審查（handoff a47d625c，2026-10-23 20:44 UTC，head b6）明確指出：同列車 memo-only 反證不能取代原跨版本 exact 門檻。此項仍是阻擋，原 compare exit 1；須恢復 exact，或取得並登記可接受 #299 診斷差異及相應 comparator 的明確裁決後才重跑。現行 I22 明定訊息指出定位邊與超出區間，既有正反例亦驗證這些欄位，因此直接刪回舊訊息會違反現行 SSOT，不能作為保守修正。可選方案是保留現行功能與原紅燈、將診斷版本邊界另行明確裁決；不自行過濾、正規化、放寬 comparator 或改數值門檻。本輪採此保守處理，精確根因與原差異繼續封存，其他驗收照跑，仍不標 READY-TO-MERGE。

後續2026-10-24 00:39:37 UTC／head f05e7cf的#338審查重申B2仍未解除：須先取得並登記診斷版本界線／comparator裁決或恢復exact，再以L跑原comparator；memo-only不能取代。本補記只更正審查沿革，沒有採納新裁決、變更比較器或改寫原exit1。

已封根因（`review-b6-response/b2-diagnostic-originals-and-peer.tar.gz`）：歷史 b74 的 I22 已要求定位邊與超出區間，舊二進位欠缺此資訊。待裁決的最窄選項為僅承認以下三個具名場景的三對完整 error／stderr 差異，其餘 bytes、返回碼、有序圖、五 guards 與175／350數量仍完全相等；或將歷史基準補齊同一診斷後另立明確版本。建議前者較容易精確審核，但目前未採納、未改 comparator；兩者都不能冒稱原 b74 二進位未改的 exact已通過。

- `_role_priority_mutant.scene`：新增 `——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm`。
- `_s1_p8_l_room_primary_through_reflex_extension.scene`：新增 `——定位邊 e3 [3000,4800] mm，低端超出 [27,3000] mm`。
- `_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`：新增 `——定位邊 e1 [0,1800] mm，高端超出 [1800,4773] mm`。

歷史E537僅比較完成時的快照（後續性能／memo終態見Q-323-N64）：同L #323原prepare0／build0／compare1已真完成；equivalence.json記175 scenes／350 runs，差異僅列`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`三個stdout。原`verify_linux.py:156`的`assert not failures,failures`拋出；ABC_result尚未設定、quantitative_targets為空，不能冒完整後續audit四元組或性能已通過。前後來源同L且clean；perf／profile／memo仍UNRUN，原比較器未改，B2未解除。

## Q-P189-EXACT：同族I22診斷差異，保原正式紅燈

L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`的原P-189 full已在2026-10-24 02:01:49～02:02:52 UTC真exit1。這次base是`3e600772076465fc65a26ac09055028301c0fb0b`，不是Q-323-ABC的b74。原`p189_verify.py:195`以`assert raw['base'] == raw['fix']`比較完整stdout，126組相同後在第127個`repo-_role_priority_mutant.scene`中止；175組未全完成，原full timing未啟動。

兩版load均reject、第二行完整dump相同；L的第一行error及stderr多了現行I22要求的`——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm`。它與既有B2同族，但不是同一基準或同一執行證據。原assert訊息稱dump不同，不代表幾何dump真的不同。

本輪保守採取：保留原full exit1與原始完整輸出，不刪診斷、不過濾error、不放寬comparator；已審獨立timing原0且四個數值門檻均通過，其他不受影響驗收繼續。待裁決選項仍是明確登記診斷版本界線／具名完整差異的處理，或建立核可的新診斷基準後另跑；兩者目前都未採納，不能冒原基準exact已綠。獨立timing成功只解答數值門檻，不能解除這個完整比較紅燈。
## Q-314-SSOT：現行規範已採納；有序補句另列寫入差額

本項不再列為等待使用者決定。現行 `公理層.md` D10b 已含只在提交比較、整體取代／隔離重放／復原重做豁免的相容例外；I24 已含參數卡改值例外，D29 已含按當下有效整數解除引用。對應 2026-10-18 的逐字稿核可已記於決策佇列；不能再把這些既有條文寫成「暫緩採納」。

#314 題3／4的行為已決定，2026-10-23 15:35:22 UTC 的 #314 決策回報又核可 I24／D29／D10b 的精確有序補句（原操作順序、換來源當下有效值、將來明示刪除的身分邊界）；這份補句不是上段既有文字，在本受審來源尚未逐字寫入 SSOT。#337 19:44 交接稱使用者選擇暫緩寫入，僅作這份後續補句的交接沿革，不能反推既有提交相容例外尚未採納，也不把已核可稿重新列成待看稿。

目前程式／測試的有序判定與原實跑來源照各 gate 記載；它們不是新條文已完成寫入／閱讀器同步／採納雜湊更新的證明。本輪先更正現況文件，保留現行 SSOT／決策原文；具體剩餘為上述有序補句的寫入及既定 SSOT 流程核對，不新增政策或數值門檻，也不重問題3／4。

## Q-335-CLI：Reading A 正例的初放入口缺口（另案設計，未解決）

已核可 Reading A 的接觸政策，不等於真 CLI 已能初放兩支互頂壁邊材。原 core 收據（issue 標 074a004a、後補 README 標 3cbeb759，兩者 C/H/inc 相同）是 order12/order21/only2 退出 1/1/0：先放 e0 時第一支端面無支撐；先放 e2 時 e2 先延伸成長1000，再使 e0 無合法跨距。完整 scene/stdout/stderr/core hash 已保留；本輪只有 L 靜態來源核對，沒有將舊負例重標為 L 實測，oracle/Reading A 綠燈也不補此能力。

依決策佇列 2026-10-24 Q318-1「政策先合，另開工單」與 issue335，放置路徑及逐條條文差異定案前不實作。較窄待審方向為明示 Reading A boundary 固定段原子放置契約，須釐清組內已放/完成狀態、初始跨度、無環來源與 dump/重建；未採用，不把未 placed 料當已放、不硬裁 auto 跨距，不放寬 I22、I20/R18、I5/I11，不新增數值門檻。根因與限制經獨立 peer84/0；這是準備證據，不是產品修正或 #335 驗收通過。

完整唯讀原件與設計比較收於 `issue335-readonly-cause/`；本項維持待決策，不在對話提問或阻斷其他驗收。

## Q-323-N64：既定性能門檻紅，無新增門檻決策

同L原36樣本timing的stage execution0，但N64 fix/main=1.4282954375137715>1.3，target_met=false；outer CLI1另包含累積compare1。N16/32/48 fix/base原三門檻皆true，原四profile的source calls64/32=4.407618425509266≤4.5亦true。memo撤回6.053833206336931>4.5真1、恢復4.407618425509266真0，隔離175/350 ABC0，不代表N64載入時間或跨版本診斷exact已綠。

本項不要求使用者定新數值。原1.3門檻與分母保留，性能病因待依原profile剖析，不逕歸環境、不挑樣本、不改比較器。可自主進行不改公理／鎖定決策的效能修正，須做撤回／恢復並按影響更新驗收。原B2與P189診斷版本界線另保待裁決，不以這次memo因果證據解除。


## Q-CI-CURRENT-U：新合流來源的 required jobs 仍受帳戶環境阻擋

U=`ca7838e0f4950452b9befcf40899d606db9b81fa` 的 run40058889738，及證據頭 b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5 的 run40059064935，七個 required jobs 都是 failure／steps=[]，原 annotation 明載 recent account payments failed 或 spending limit。原 API 讀取全退出0；沒有把未啟動的 job 算作產品測試紅燈或成功。完整原件已封 current-U-architecture-and-ci/ci。

保守處理是保留 required checks 阻擋，繼續同產品來源的雲端原門檻與修正；本代理不改付款設定、支出上限、required checks 或原 workflow。可由帳戶環境修復後取得同 head 真 CI 終態，或由既有正式替代流程明確接受同來源補跑收據；目前兩者都尚未成立，不能自行解除 B3 或標 READY-TO-MERGE。這不阻斷其他工作線，也不在對話要求使用者回覆。

### U 五stage新終態補記（不改既有裁決）

在U=`ca7838e0f4950452b9befcf40899d606db9b81fa`，原#323 compare再現同三個stdout差，verify_linux.py:156原assert1；I22版本界線仍待既有裁決，不刪診斷或放寬exact。新N64fix/main=1.429347781620555>1.3，屬可自主修正的性能缺陷，不要求新門檻；small-N與calls比雖綠，不解除它。

原ABC_result key不存在、all_required_stages_completed=false/full_acceptance_passed=null，compare後段audit因assert未達；原八stage中required-eight/pf3/native三項尚未執行。小原件見`evidence/geo337-train-20261024/current-U-323-terminal-status`；完整U原流封包仍未公開。原L結果及待決選項保持歷史身份，不移標。
