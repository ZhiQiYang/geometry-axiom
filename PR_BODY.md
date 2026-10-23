# #299＋#316：補齊 I22 定位邊診斷，退役無 caller 的碰撞轉接器

非 boundary 角材超出定位邊時，保留原 `V_EXTENSION` 前綴與裁決，補上定位邊 `e<i>`、定位邊區間，以及實際超出的低／高區間。沒有超出的端點不印假區間，原 NULL error、容量與截斷判準保留。

移除三個沒有產品 caller 的 H wrappers，及唯一 caller 是死 wrapper 的 W footprint API。活 I11 放置、H 重驗與 W 最終重驗路徑保留；新增雙承載面局部 UV 重疊但各自合法的接受場景，分別由 M97／M98 保護 H／W 的同承載面過濾。

本分支獨立基於 #288 的已驗收程式，不帶 #323／#314；使用完整 combined patch，沒有先後疊兩份 individual patch。公理層、決策佇列及 BACKLOG 均未改。尚未合併。

#316的具名退休範圍包含只直接呼叫死API的9個collision checks、一個Python method及3個controls；活I11的M12／M13、H／W重驗、邊接觸、跨承載面、未放置與contact-stop／owner pointer identity保護均保留，另新增同UV雙承載面場景與M97／M98。這個既定API退休範圍與修紅燈時保留全部活斷言分開核對。

| 身分 | SHA |
|---|---|
| 精確 base／#288 公開證據提交 | `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` |
| 權威 handoff | `804afbb4c5fa38b6023087d6dcb150f40c5978e6` |
| 修復後產品／tests／manifest P3 | `e4557b3f5fab70d70ebb44cd5489cd8841bb3670` |
| 帳本真正實跑來源 S | `e40762e99b078335d78c65a3a2682a0c9ab875d0` |
| 帳本保存提交 L | `3a165ef581976914cbf1acc27561a35452e21a44` |
| Linux 架構真正實跑來源 | L；新 receipt `sourceBaseHead` 保留 L |
| 架構產物 A＝正式驗收 F | `5bfadf187e615ba0fb8466753b63ce3044ef7d1c` |
| 正式 native 證據 E_native（已一般推送） | `66f6da5e2ea191746cfd0531288bb38fb3d50905`；受驗來源仍是 F |
| 最終證據 E_final（已一般推送） | `139ab64ca5f88e89bb4e95921675b998457026aa`；F後僅保存同F證據，不冒E已受驗 |

上述 source branch 已一般 push 並以 `ls-remote` 核同；未 force push、未合併。帳本 execution 不改成保存帳本的 L，也不改成 F。

同一 F 的原指定 native、六個 browser jobs及三條正式架構裁判均已完成，原退出碼全為 **0**。其中 native 的224 suites全部執行；有計數者合計 **5,185項：5,184 pass、0 fail、1具名 Windows GDI skip**。該 GDI harness 在 Linux 無法執行，原 workflow 已明列允許，保留 skip，不列為通過。原 job 1,812.307秒／30.205分，未超過原35分CI時限；沒有放寬時限或自動重抽。同 F 獨立三條架構裁判也已原 **0／0／0**，來源前後乾淨一致。

`ulimit -s 16384; python3 tests/run_all.py --build` 的原 stdout／stderr、環境、版本、SHA、完整suite日誌及退出碼已封在 `evidence/geo299-316-final-5bfadf18/raw/native-01.tar.gz`，原收據見 `receipts/native.json`。`mutation:check` 原退出0，88筆帳本仍有效；此項驗 freshness，沒有假稱重新執行85個 mutants。canvas、assembly、documents、grid、space、timber六項原workflow job已在同F逐項完成，於2026-10-23 03:28:09 UTC留下整輪終態0。各項原test／child／publisher退出均0，沒有超過各自原CI時限；服務埠19081–19086及暫存目錄各自獨立。

| 正式 native 中的重要回歸（已含在上述總數內） | 原結果 |
|---|---|
| core場景 | 166／166；新增 `_i11_two_surfaces_same_uv_accept.scene` 實際 PASS |
| W contact world／contacts／world validation | 9／9、10／10、14／14，均0 fail／0 skip |
| H host facts authority／contact sources | 19／19、13／13，均0 fail／0 skip |
| 上述六個直接受影響 suites 小計 | 231／231；包含新I11場景，沒有將全suite數量冒稱全是新增案例 |
| candidate product／唯一canonical reader／mutation anchors | 26／26、51／51、3／3，均0 fail／0 skip |
| Node單元登錄 | 737／737，0 fail／0 skip；實際Chrome jobs另列下表 |

原版本命令均0：`Google Chrome 156.0.8078.47`、`node v24.19.0`、Python3.12.14、Debian cc14.2.0；`fonts-noto-cjk` 狀態為 `install ok installed 1:20240730+repack1-1`。正式 native 執行前／後皆為乾淨 F。

| 原browser job | 原秒數 | 原CI時限（分） | 原footer／scope |
|---|---:|---:|---|
| canvas | 1665.084770 | 35 | 2267 assertions／0 fail，`full`，golden `matched` |
| assembly | 186.209069 | 15 | 150 assertions／0 fail，`partial`：`GEOMETRY_ASSEMBLY_ONLY` |
| documents | 60.458381 | 10 | 47 assertions／0 fail，原documents harness |
| grid | 439.853007 | 15 | 356 assertions／0 fail，`partial`：`GEOMETRY_GRID_SYSTEM_ONLY` |
| space | 207.312252 | 15 | 242 pass／0 fail，`completed:true`，`full-space-suite` |
| timber | 119.906185 | 20 | 79 pass／0 fail，`completed:true`，`partial`：`GEOMETRY_TIMBER_ONLY` |

各行保留原workflow選定的groups及原footer口徑；assertion數包含可信輸入、DOM／程式整合及native API檢查，不是互不重複的端到端情境數。assembly／grid原為partial，golden原文為`not compared (partial mode)`；完整canvas才做原golden比較並matched。

space原`full-space-suite`仍明列omitted：`timber-material`、`timber-source-guards`。timber原partial的included為`timber-material`、`timber-source-guards`、`font-layout`，omitted為`space-height-library`、`projection-lifecycle`、`projection-placement`、`space-flow`、`projection-close`；79／0只代表這個timber切片，沒有擴稱全部space groups。

原canvas stdout第1829行的`P73 空空間不畫假邊界，提供加入成員入口 ✓`及第1854行的`P73 整輪沒有未處理瀏覽器例外 ✓`均通過；後者僅指P73模組。canvas整個原footer的`uncaughtBrowserExceptions:1`保留，對應原`[EXPECTED EXCEPTION] Error: fb-auto-probe`及P38預期單次例外抵達／自動回報兩個具名成功斷言，沒有將它改寫成整個canvas零例外。

原canvas第772行`P52-5`的`SYNC_WAIT`為197ms，條件是角材3放置交易收尾且核心references回傳幾何。這是正常job同步等待紀錄，沒有冒作獨立main／fix效能比較。

首輪修復前完整 native 的原1／11fail保留（reader追溯6、fixture順序1、Node缺三個既有ZIP夾具4）。reader只走原同步器；fixture保全部斷言並做下述0／1／0；Node環境只由同一Git blob物化缺檔、原部分retry737／737。最後在固定F跑完整native0；除已授權死API退休範圍外，沒有因紅燈刪case或放寬斷言。

正式F隔離來源的首輪準備僅在產品測試前遇到收集器對 Git `skip-worktree` 自動清旗標的錯誤假設；r2明列三個既有夾具旗標變更，四夾具逐bytes同F Git blob、其餘index／產品bytes保留。首輪沒有執行產品測試，原前置紅燈及未用worktree安全釋放收據保在同F evidence；正式native只執行上述一輪。L首輪純出版也保 git add因sparse排除evidence退出1的原收據，僅對精確path改用Git原`--sparse`後一般推送。

| 已完成帳本／架構項目 | 原結果與範圍 |
|---|---|
| 原整份帳本命令 | 原 `python3 tests/mutate.py` 退出 **2**、外層 **1**：67 個 core execution 完成，fresh bridge checkout 因雲端 ENOSPC 受阻；原 checkafter／source_after 缺漏保留 |
| 純 collector 前置 | 第一次環境 retry 工具把同一組18 IDs的順序誤當不同，於任何 mutate 執行前退出 **1**；保原輸出，僅修 repo 外清單為原 registry 順序 |
| 同 S 環境 retry | 全新 cache／scratch，僅 sparse 排除三個已公開 evidence 目錄；原 C closure、完整 flat Python／scene oracle hashes、兩原工具 bytes 及完整原 RESTORED **27** 方法名單核同；原18 bridge subset **0**、其後原 strict `--check` **0**、外層／reaper **0** |
| 最終帳本 | 88筆，85個 execution 全綁 S：**80 killed、4 equivalent、M20 crashed、3 retired**；無 survived／invalid／stale／blocked／unrun。原67個 core 每段 JSON 原始 bytes 全同；新 M89–M98 全為正常斷言 killed |
| 安裝後追溯與帳本 | 原 canonical sync／原 `--check`／原完整51 reader tests／安裝後原 `mutate.py --check` 各 **0**；HTML bytes 未變。沒有因帳本日期重標來源或重造閱讀器 |
| Linux 架構 r1 | 原三裁判 **0／0／0**；額外退休普查 collector 直接保 CRLF，未沿原 scanner 的 LF 正規化，於 `lex` 假報 lexical error，整體 **1**，保完整原 raw |
| Linux 架構 r2 | 只修 repo 外 collector 兩處 `normalized(raw/body)` 後再原 `lex`，不改產品／tests／scanner／manifest。相同 L 重跑原三裁判與四檔，全部 **0**；generic原205 tests、product原18 tests。601 executable／333 owned／268 exclusions／796 edges／0 diagnostics；920 identifiers／55 strings |
| 唯一 API 退役證據 | 原完整190個 owned C seeds／include closure逐 token 普查：`wood_contact_footprint_collides` 現為零 identifier references；舊 sealed來源 Git blobs 找到 H caller＋W定義／prototype三處。僅退役這個 guard，其餘舊 identifiers／全部 strings 保留；此為 include graph／詞法證據，不冒 function call graph 或 native absence test |

這是原整份重產的兩個環境 phase：原67 core＋同 S 環境 retry18 bridge＋原 strict check。**不宣稱單次原 full 命令退出0。** 雲端容量修復僅釋放三個已公開、乾淨且可由 Git 重建的舊 main 比較 clone；原 raw／payload 保留，完整 guard／命令／退出碼／每檔 hash／空間前後收據一併封存。

移植保留 F2 `ContactOrderIndex` 的 last／minimum／重複 ID／equal-order／容量 fallback 與 collect-stops；H prepare wrapper／實際 member 身分、minimum 的 equal-order 負控及 host-facts 原 callback snapshots／phase／partial-output 斷言均保留。

fixture 順序修正保留全部新舊斷言，只把新增 boundary failure-output 檢查移到原 I5 判準之後並重設 sentinels：原完整9方法 fixed／reverted／restored為 **0／1／0**，撤回的原失敗為 `ASSERT:i5-notched-footprint-deferred` 被新增 `ASSERT:boundary-edge-failure-leaves-outputs` 先遮蔽。唯一 canonical 的機械同步亦有原完整51 baseline **0**／僅換回舊 HTML 的具名 idempotence case正常 **1**／恢復完整51 **0**；SSOT／決策／BACKLOG bytes不動。

`tests/evidence/geo299-316-combined-20261022/ledger-e40762e9/` 保存 primary及完整大 raw。primary封包18,096,924 bytes／550members，包含容量修復與前置失敗；大 raw封包11,334,429 bytes／1,195members，保53,359,955原bytes、78個top-level streams、216個bridge stream references（148unique）、184 C closure 與397個原 flat Python／根scene inputs。全部封包逐 member path／bytes／SHA256解包核同。

原 core 內層 compile／attempt沒有全部 streams落盤，原完整 top-level stdout／stderr、structured results及原stream hashes已保，沒有以 hashes反推未捕獲輸出。85份 mutant C 是由原 pure helper重建並比對原 fingerprint／sidecar，明標 `reconstructed-not-captured`。clone子樹明列未遍歷／未hash，closure／judge inputs另保；其餘 ELF／objects逐檔hash。

`architecture-3a165ef5/` 的12,371,006-byte／317members封包保 r1失敗與r2成功、原完整 argv／退出碼／stdout／stderr／環境／SHA、兩行外部工具修正、四檔、舊 Git blobs與完整退休普查，也含 L 的正常 push／ls-remote原輸出。manifest bytes未變，新四檔保真 `sourceBaseHead=L`。

同 F 獨立三條正式架構原收據在 `evidence/geo299-316-final-5bfadf18/receipts/architecture-final.json`，完整原stdout／stderr、環境、SHA封在 `raw/architecture-final-01.tar.gz`；原CLI／generic205／product18各0。這些獨立架構執行另列，不重複加進native合計。

最終證據提交E只在`evidence/geo299-316-final-5bfadf18/`追加原收據、raw、終態wrapper、閱讀摘要與metrics；F之後沒有產品／tests變更。受驗來源始終是F，E僅保存證據。閱讀入口均固定在同一不可變E：

- [FORMAL_SUMMARY.md](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/FORMAL_SUMMARY.md)
- [FORMAL_METRICS.json](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/FORMAL_METRICS.json)
- [原收據目錄](https://github.com/ZhiQiYang/geometry-axiom/tree/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/receipts)及[完整raw／inventory](https://github.com/ZhiQiYang/geometry-axiom/tree/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/raw)
- [BROWSER_SCOPE_FACTS.json](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/BROWSER_SCOPE_FACTS.json)：已讀原stdout的選定scope欄位／原文／行號小索引；沒有重寫原footer，未錄得行號保null

metrics是純整理索引，`not_acceptance_gate=true`，不能把collector寫檔成功當裁判通過；上述結果以原judge、原workflow退出碼、原footer及收據為準。原formal completion封包與較早文件版本照留，最後metadata修正文句只收斂P73模組／P38預期注入與各job原scope，沒有重跑產品或修改原raw。

本輪實證範圍是Linux／GCC與Chrome156；Windows GDI harness原具名skip，沒有執行Windows／MSVC驗證。本分支也尚未與#323／#314疊合驗收，這是後續整合仍需留意的主要不確定處；原core內層streams缺捕、85份C明標`reconstructed-not-captured`的限制維持。

GitHub API存取受限，請依handoff從來源分支`codex/geo299-316-combined-20261022`建立此合併補丁的對應PR並套用本文，base設為`architecture/geo261-integration-20261016`；#288進main後再依handoff調整base及整合順序。#299／#316是本次合併處理的工項編號。此交付提供已推送分支與正文，GitHub上的PR建立／正文套用仍待使用者完成；本次未合併、未force push。
