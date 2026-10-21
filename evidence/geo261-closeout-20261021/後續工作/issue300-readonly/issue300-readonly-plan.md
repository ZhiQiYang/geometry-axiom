# #300 容量 64 → 512：後續只讀盤點與驗收計畫

本次只做盤點。尚未套用草稿、修改產品、執行生成器、benchmark、測試、突變或編譯；沒有新增產品分支或提交。#300 不進 PR #288，必須先完成 #288 與 #323，再處理剩餘熱點。現有資料不足以宣告容量 512 已可採納，也不足以宣告不可行。

交接標籤沿用使用者的 20261021；本次整理時 runner UTC 為 2026-10-20。歷史原件的 2026-10-20 時戳保持原樣。本文件及伴隨索引是新產生的只讀盤點，不是補造舊驗收原件。

## 來源與閱讀範圍

| 名稱 | 固定來源 | 本次用途 |
|---|---|---|
| 交接分支 | `handoff/codex-takeover-20261021`，`59796b1af9259eb23d30134c2ce5a56317a06091` | 規則、尚未採用的草稿、舊 bench 原件。禁止合併交接分支。 |
| 草稿設計基底 | `09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1` | DESIGN.md:3–6 明示尚未編譯或測試；不是本輪產品來源。 |
| 舊 bench 基底 | `603e4195cf4336321f8c6aa2b90d7ee8969e0572` | 舊 results/env.txt；先於 #321/#323，不能當 A 或未定最終 L 的成績。 |
| main | `adbaebf9c73ea6801d7b4d5214e4b846b132923b` | 靜態對照舊接觸實作及容量 64。 |
| #288 候選產品／架構 A | `7159530c0e494d3211e6ab1764eb691137211707` | 靜態對照，沒有在本任務重新驗收。不是 #300 實作來源。 |
| #323 審閱來源 | `f3ea9c5232c043b3dca57b953577f5d22e9030e7`，`codex/geo261-load-residual-20261020` | 已有讀取共用與接觸來源變更的碼面範圍；不宣稱通過合併驗收。 |

`handoff/drafts/issue300/` 全部 14 個檔案已讀：DESIGN.md 307 行、TESTS.md 137 行、patch.diff 663 行、bench/README.md 156 行、bench.sh 287 行、drive.py 864 行、fit.py 594 行、gen_scene.py 375 行、calib/f3-00.scene 212 行，以及 results 的 STATUS、bench.tsv、env.txt、兩份各 443 行的建置 log。兩份建置 log 以完整 bytes 比較，讀完共同 424 行及全部 19 處差異。四支 bench 腳本由另一代理完整只讀審閱，詳細發現在 [issue300-bench-static-notes.md](issue300-bench-static-notes.md)。

亦已完整讀取 HANDOFF.md、PROMPT-A-source-index.md、PROMPT-B-load-residual.md、PROMPT-C-load-residual-fix.md；核對 provisional-decisions-log.md 的 P-175/P-176/P-177 與 P-189/P-190、wsl-pending-after-game.md:100–157 的相關紀錄。下文產品行號依上表固定 Git blob，並非目前工作樹的浮動 HEAD。`current_geometry.c` 均以 `git show` 的 bytes 或二進位讀取後解碼；沒有 text-mode 讀寫。

**缺少 #300 在 10-20 的原留言。** HANDOFF.md:64、91 只有前置條件摘要，相關 notes 只有轉述；本輪無 GitHub API，也沒有完整原留言可核。不能自行補出它的接受門檻、實作範圍、採納決定或後續留言。開始實作前須取得該留言及之後的完整討論，重新對照本計畫；現階段可先列已知缺口，不能把摘要冒稱原文。

## 已知順序與不可越過的界線

1. HANDOFF.md:61、77–91：#288 收尾先行；#323 不進 #288，#288 合入 main 後 #323 才改 base；#300 要先完成 #323 並處理剩餘熱點。
2. P-175（provisional-decisions-log.md:754–756）曾暫定容量 512、單一常數、編譯期一致性檢查、扁平 cut list、N/N+1 測試與探針，並限定在 GEO-261 合入後的 main 做。這是交接決策紀錄，並不代表這份未測補丁已採納。後續 typedef 寫法的同意見 wsl-pending-after-game.md:109；不必把已同意的例行寫法另當待決，但也不能藉此擴張功能。
3. A 的公理層.md:1468–1473（I33）要求能力／容量不足明確拒絕，不能截斷、刪面或把合法輸入的資源不足誤報成幾何 INVALID；條文沒有硬釘 64 或 512。容量變更仍須精確守住拒絕分類與原子性，不能自行改 SSOT。
4. **P-177 以 HANDOFF.md:12 的最新硬限制為準：候選、驗證、seal、publish 的次數與時機都不能為效能改動。** 舊 notes:771 曾列過較寬的方案，不得拿它恢復已被交接規則禁止的路線。也不能刪重驗、延後錯誤或只驗新增角材來加速。
5. P-189 的已定門檻仍是 N=16/32/48/64 每一點 final/main ≤ 2，且 dump 逐 bytes 相同（HANDOFF.md:100；P-189:889）。#323 提示詞另有 N64 ≤ 1.3 倍及來源呼叫倍率目標，這不是自動替換 P-189。README 建議的五房約 N300 ≤ 30 秒、16 MiB 保留 2 MiB、採用 256 等都不能由代理當成已批准的新門檻。
6. HANDOFF.md §7 的待決事項照原文保留：doubling／retreat、為柱跨牆階改 I19 路線 B、Windows 搜尋排除、刪 D:/t（不得刪 D:/t2）、刪指定 local 分支、WSL 搬 SSD、Actions 計費、推翻 P-186/P-189。此盤點不替使用者決定任何一項。

## A 與 #323 實際仍是容量 64

A 與 #323 的 `current_geometry.c:2741` 仍是 `WORLD_MAX_TIMBERS 64`；`document.h:20` 的 WOOD_MEMBER_CAPACITY、`contact_world.h:7`、`cut_list.h:6`、`member_reference.h:100` 亦為 64。後五個 W 檔在 A 與 #323 的 bytes 相同。main 的單檔常數在 `current_geometry.c:3730`，尚無這些抽離 W 檔。

草稿提案在 DESIGN.md:12–19、54–91：W 的 members.h 只定一次容量，H 的 World 與四種用途常數衍生自它，以七項 typedef 檢查綁定實際儲存與 scratch 下限；不令 K include W/H，不允許每個編譯單元自行覆寫容量而形成不同 ABI。這些是合理的待驗方向，尚未在目前來源實作。

cut list 提案（DESIGN.md:106–134；patch.diff:63–127）把各組 ids[N] 的平方儲存改成單一 ids[N] 與組的 first/count，需維持原本排序、組鍵與同組宣告順序。兩個直接 consumer 是 CLI 與 report harness；後續要重新枚舉實際來源的所有 consumer，不能只因舊草稿列兩處就當封閉。

## 剩餘熱點：能從程式確定什麼

### contact_order 與擋面排序／去重

A 與 #323 的 `geometry-templates/woodworking/native/contact_world.c` 完全同 bytes，SHA-256：

`fb961338710375da2c4eeb4b8af56f67bd1cf581067f91a48b356722646c30f8`

- :25–28 的 contact_order 每次掃 member_count，命中亦沒有 break。
- :63–70 的插入排序在 :65、67 重複呼叫 contact_order。
- :72–83 的去重有 i/j 成對候選；幾何篩選後 :77–78 還會掃成員決定先放者，:82 用 memmove 刪除。
- main 的對應實作在 `current_geometry.c:7219` collect_stop_faces，:7319–7330 排序、:7322/:7326 線性查順序，:7332–7346 去重、:7336/:7340–7341 再掃成員。因此這類成本在 main 已存在，僅看迴圈不能斷言它造成 A/main 退化。

令 M 是成員數、S 是收集到的面數，「O(n²) 去重」只描述成對候選。部分比較又掃 M，排序亦有比較次數乘 M 的成本。固定容量、幾何篩除、提早 duplicate、排列、每指令重驗次數都影響實際工作量；本次沒有 profile，不能把整個 loadfile 宣稱成已證 O(N³) 或 O(N⁴)。

後續 profiling 應分每次 collect 與每個真實指令記錄 contact_order 呼叫／總掃描、sort compare/move、去重 i/j/t 次數、幾何篩除率、memmove bytes。直接 id 索引或預先順序表是待審方向，不先採用；須保留 id 域、缺失 id、同序、來源順序與首次錯誤的既有語意。

### #323 已做的共用與尚未消除的工作

在 #323 固定來源：

- `geometry-app/native/reference_sources.inc:489–509` 的 definition_read／anchor_read 即使命中，也在 :495/:509 保留 geo_eval_depend。
- :596 的 reference_contact_facts 在 :618–622 共用同 placement footprint，:619 仍登記 member pose 依賴；:832–842 共用 relation 的 pose 並保留 depend。
- `geometry-core/references.inc:121` 起新增 member_reads，:168 清除；:640、669 為 reference_check_all 加 AppFootprintMemo。
- `geometry-app/native/world_validation.inc:11–27、47–60、107–110` 是單次驗證的成功 footprint／host memo，每次驗證重置。
- `world_validation.c:61–70` 成員碰撞的兩兩迴圈未移除；接觸收集本身亦未消除。

這是讀取／解碼共用的範圍核對，不能冒稱 #323 已完成效能或語意驗收。既有 #323 預審與第二次夾具審查仍須處理（外部 final-bundle/後續工作/ 已另存），尤其 fixture 可編譯不等於突變可抵達預期守門。

### geo_eval_depend 已有索引，仍有登記成本

A 與 #323 的 `geometry-core/kernel/source.c` 完全同 bytes，SHA-256：

`ab8d09bbf4d211f8019d52c8b12eb8d0e4ffde6df45e788cd6ce883225ec0acb`

:247–252 的 depend 經 :170 geo_source_node／:55 find_node，再經 :189 geo_source_edge／:68 find_edge；查找已有雜湊索引。:64/:76 才是無索引線性備援，:81–103 包含增長／配置失敗備援。不能拿 PROMPT-A 的舊問題描述說目前全部還在全陣列線性查找。

未 sealed 的 geo_eval_source（:263–268）也先登記 node/edge。#323 的 `contact_sources.c:120–140` 為 feature 新增 collection_node_hint，核對完整 provider/key/VALID 後 :134 用 depend，失配 :136 回 source；:167–189 每次 collect 仍配置 query、求 collection 並逐面求 feature，:90–107 的新集合仍取 facts 並在 :102 收集擋面。

所以只看 geo_eval_source 次數下降會漏掉移往 depend 的工作。後續應合併計 source+depend 總請求、hash probes/key bytes、重複邊率、新增 node/edge 與 fallback 次數，再逐筆比對完整有序圖。不得省略 dependency kind、改 node/edge 插入順序或取消失效依賴。

需留意的重複路徑包括 `world_validation.c:49` → `world_validation.inc:87` → `current_geometry.c:5786–5792` 的接觸來源／直接收集，以及 `world_validation.c:56` → `reference_sources.inc:702` → `contact_world.c:113` → `reference_sources.inc:692–700` 的端面來源。先量同一指令的重複 facts／collection，不從函式名稱推定可以刪除。

## 舊草稿及 bench 不能提供的證明

1. **容量與記憶體。** DESIGN.md:140–150 的 World 4,759,448 → 5,605,272 bytes、+17.77%，原來是舊布局推算；舊 bench.tsv:2–3 的二進位回報支持那一版數字，不能直接套到 A/#323 或未來 main。扁平 cut list 的估算同理。需在實際採用來源重新 sizeof，保存 binary、flags、ABI、實際輸出與 source/closure 指紋。
2. **堆疊。** DESIGN.md:221–226 的 3×World 約 16.04 MiB 是超過 16 MiB 約 38,600 bytes，不是已驗「尚餘 38 KB」。wsl notes:109 的「只剩」措辭不能當量測。靜態找兩個 World 也未涵蓋所有函式指標、live frame、遞迴與完整工作負載；固定容量不能證明 N64 代表全部 N。
3. **舊結果。** results/STATUS 是 SANITY-FAILED rc=3。bench.tsv 只有 World 大小與 sanity，沒有正式 load/edit/new/batch/delete、fit 或 stack 結果。house N128/cap512 在 300.002229 秒 timeout；single N65/cap512 接受。cap64/N65 的 rc0 代表「預期容量拒絕」成立，並不是錯放第 65 支。notes:130 說 queue32 成功，但交接此目錄沒有相應原始封包，不能補成已驗證成果。
4. **工具停止條件。** drive.py:330–350 的 sanity 固定 300 秒，不受 BENCH_RUN_TIMEOUT／--retry-timeouts 控制；bench.sh:265–270 的 run/stack/all 都先重跑全部 sanity。README 的含 build ≤29 分鐘沒有全域 deadline 保證。drive.py:383–385 把 timeout 說成生成句型不合法，舊 house128 只能說未完成，不能作此歸因。
5. **工具假綠。** run 的完成狀態主要看 load；reject/timeout/crash 亦可被列為已處理，後續 line 失敗可留下完成單元。fit 即使 FAIL／資料不足仍 exit0；stack 未強制四種負載全部齊備、16 MiB 真跑、輸出一致或失敗屬真正堆疊溢位。不得以外層 0 宣稱產品驗收綠。
6. **混來源續跑。** TSV 沒有 source/tool/patch/compiler 指紋；換來源重建但沿用 BENCH_ROOT 可能跳過舊列，env.txt 卻覆寫新來源。未來須使用全新隔離輸出，或讓每列與整份 receipt 綁唯一來源。舊 bench 預設 gcc，不能當 CI/default cc 的同一字面編譯契約。
7. **模型與門檻。** 「single 為 house 嚴格上界」、由少數點確證立方、5 房估 50–110 秒或 512 估 7–13 分鐘，都是假說／外插。README:131 的兩 MiB 餘裕對應 14 MiB，:142 卻寫 14.4 MiB；即使修正算式，也不能代決接受門檻。既有服務 30 秒不能自行放寬。

完整工具行號及十份 bench 原件 hash 見伴隨 notes；它的 SHA-256 為 `d565c902f54bdc8ca19e68ca30636ad0d41fbc67fd619669289e43b35e7a2b33`。

## 後續實作前與驗收計畫（全部尚未執行）

| 階段 | 必須產出的具體證據 |
|---|---|
| 前置凍結 | 先完成 #288 與 #323；取得 #300 10-20 原留言及後續討論，記實際採用 main/full SHA、適用條文與範圍。不能直接套 09ab5f79/603e4195 的草稿，也不能將 #323 混入 #288 以求容量前置綠。 |
| 先修量測可信度 | 隔離 source/patch/compiler/tool 指紋；全流程有界 deadline；分類 accepted/rejected/timeout/crash/tool-invalid；完成集合包含所有必要操作；資料不足或工具失效不能作 PASS。為這些裁判規則做小型明確正負控制，才執行昂貴量測。修工具不等於擴產品 timeout。 |
| 先量現有容量 | 在同機、獨占條件依固定 N 與同一合法 scene 交錯 baseline/fix/main，保存三次原樣回應與中位數；profile 與正式計時分開。量上述每層迴圈及 source+depend，確認剩餘成本後才選資料結構。#323 預期守門計數與有序圖 oracle 同時保留。 |
| 選定最佳化 | 分別審順序索引、去重資料結構、來源重複登記方案；不改 P177 流量、錯誤先後、精確幾何及回滾。不同最佳化分開以精確撤回負控制定位。未能保留語意就不採用。 |
| 容量補丁重整 | 依實際 main 重整五常數／七 binding、W ownership、cut list 扁平化與所有 consumer；檢查所有受容量影響的配置、堆疊、保存／恢復與輸出。維持 CRLF；實際 git apply check 與編譯留待該階段。 |
| 邊界／原子性 | 現有 TESTS.md 的 T01–T12/C01–C13 是待跑設計：512 接受、513 明確 CAPACITY 拒絕、World 不變、滿額更新既有 id、validation 不讀越界 callback、cut list 順序／線性大小、真正 host wiring。補齊工程 restore、assembly 509+3／510+3、PF3/footprint 全容量路徑的實際適用案例；區分「只宣告未放置」與真 512 支放置，不互相代替。 |
| 突變自證 | 每個修正 baseline 綠 → 精確唯一撤回／壞 kind／壞失效或容量邊界 → 指名斷言紅 → 還原綠。編譯期 binding 控制只接受預定診斷；MSVC 的 C2118 必須確實定位到被改 binding，不能任意編譯失敗算 killed。保留完整控制集，不因猜測超時把 HOST_CONTROLS 由 5 減成 3。 |
| 大容量成本與堆疊 | 合法 single/house 分層逐步放大，固定容量 64/512 比較有明確拒絕 oracle；完整原回應與幾何等價、peak stack／工作負載涵蓋、World/ABI 實測。timeout 作下界及未完成，不用外插代替 N512。量測預算與可用性門檻分開，後者未定不代決。 |
| 最終來源驗收 | 新可執行檔／掃描變更依現行架構政策逐檔登記並重產 manifest/scan/report/receipt 四檔、三條架構驗收及相關負控制。產品 include 閉包或 tests/*.py 改動後，在最終來源整份重產帳本並以正式預設 compiler 執行 --check；不得只刷新選定 stale。依 HANDOFF §0/§2 實跑 native 與六 browser、相關 Q38/§7/replay/P189，逐項記 source、命令、exit、elapsed、未驗，不以舊收據外推。 |
| 送審 | 寫成可審的 PR 正文與逐項回覆檔；使用者在實際對應 PR 操作。合併前取得最後 push 後全部留言並處理阻擋／須改；此盤點沒有任何可合併宣告。 |

草稿 patch 引用的 `tests.test_geo261_native_kernel.native` 與 `test_geo261_wood_world_validation.PRODUCT_DEFINES/copy_product_closure` 在 A 仍存在（native_kernel.py:32、199、260；wood_world_validation.py:16、20）。這只排除「名稱已完全消失」的靜態問題，不證明 patch 可套、harness 可編、連結 ABI 一致或控制可達。tests/run_all.expected.json 的 12 亦只是草稿預期；須用新來源實際列舉／執行核對。

## 指紋、命令與未驗範圍

主要交接原件 SHA-256：

| 原件（相對 handoff/drafts/issue300/） | SHA-256 |
|---|---|
| DESIGN.md | `06f09369ece61f7f977a34cbfcaef28953da7e6b91f0e038a0b0f80c6f29dfdd` |
| TESTS.md | `c727cb26bbcc596650dc364ef3ea72e594929fd8864de45b940dbbf2fb11196c` |
| patch.diff | `8cfaa00217914ff77c3341a91f241de9847f89431d0eedca53d2ffe29e9aeb17` |
| bench/README.md | `8d83880aab16091e88272437b8985e08e7ec30987b39a30ab47d2646848acd72` |

全 14 原件、提示／notes 與本次參照的固定 Git blob 指紋另見 `issue300-readonly-sources.json`。建立索引與 read-only 核對的實際命令保留於 `issue300-readonly-source-check.code.txt`，本次輸出與結束碼保留於 `issue300-readonly-source-check.receipt.json`；這些只是檔案／來源核對，不是產品測試。舊收據沒保存的 argv、binary hash 或 raw JSON 不補造。

本輪執行的是二進位讀取、文字定位、`git show`／`git rev-parse` 與 hash 核對。沒有套補丁、import bench 腳本、執行任何生成器、自測、產品、突變、完整測試或效能量測。一次筆記讀取工具因索引超出 EOF 返回 1，改為實際檔尾後重新讀取返回 0；它不是產品紅燈，也沒有被計入驗收。

未驗項目包括：草稿在新來源是否可套、實際編譯／MSVC、十二項 suite 與十三控制、容量 512 真放置／保存／恢復／assembly/PF3、完整圖與 P177 等價性、任何新效能倍率、最終 L 的各項正式驗收，以及缺少的 #300 原留言。**突變自證本次未做，因沒有實作變更；未將純靜態核對標為 killed。**

最不確定的是目前真實負載中接觸收集、共用讀取與 source/depend 各占多少成本，以及 512 下的實際 live stack。舊 house128 timeout 沒有 profile／完整回應，無法分辨求值成本、環境競爭或其他阻塞；目前證據不能回答這些問題。

