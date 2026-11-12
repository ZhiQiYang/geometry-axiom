# 非瀏覽器CI確定性分片（2026-11-02）

目前正式安排為四個native矩陣job，每個`timeout-minutes: 35`保持，各片收據仍須嚴格小於1200秒。2026-11-02依P-186授權建立的三片為歷史安排；R348在2026-11-12的慢runner收據超時後，改為下方的完整三輪／四片規劃。原始main `405f8c5e1a637a16cbe47470faf5ae1fa02b8676` 的[GitHub native job](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40185639126/job/124015759512)量測繼續保留；不延長期限、不豁免失敗。

`native_shard_timings.json`保留完整來源SHA／run／job／原log SHA256及原main的224個suite實測毫秒；這224筆是上述main來源的量測，不改造為其他分支的套件數。初版按耗時遞減、名稱破同分，指派至目前累計最小的片（再以片號破同分）；此規則仍供明確傳入`weights`的呼叫使用。正式預設沿用R348情境分配器，輸入完整三輪量測。片內保留原完整runner的順序；未量測新suite仍用1000ms且必分到某片，但當前預算測試要求量測集合完整覆蓋registry，新增套件須同步補齊量測。配置不依本機cache、即時耗時、亂數或Python hash seed。

```sh
python3 tests/run_all.py --build --shard 1/4 --report /tmp/native/shard-1.json
python3 tests/run_all.py --build --shard 2/4 --report /tmp/native/shard-2.json
python3 tests/run_all.py --build --shard 3/4 --report /tmp/native/shard-3.json
python3 tests/run_all.py --build --shard 4/4 --report /tmp/native/shard-4.json
python3 tests/native_shard_receipts.py --input /tmp/native --parts 4 --output /tmp/native-complete.json
```

上述四個runner命令由不同GitHub job執行。單一片只代表該片，不能獨自宣稱完整驗收。`native complete coverage`下載四份原始收據，核對同一完整checkout SHA、耗時表／expected雜湊、計畫與實跑套件清單；每列必實跑、無fail／crash／環境問題、數量等於原expected、計數守恆。各片suite聯集必須等於原完整registry，且彼此不重疊。四份收據缺一、重複、漏列、來源不同、片內耗時達20分鐘均拒絕。GitHub各job由setup至complete的時間另外直接由Actions API核對，不把suite時間冒稱全部job時間。

分片本身保留各checkout拆分前的完整suite清單，不增減suite。224個suite及「只有runner案例1改12」是原main基底的實測範例；其他PR以各自完整registry／expected及全部分片實跑聯集為準，不能固定宣稱224個。11個分片守門測試併入原`py:test_unittest_runner`；各分支另有自身功能與驗證案例的expected變動，仍須逐項通過原嚴格數量核對。`check_registry`仍在每片執行；selected suite逐列嚴格比數量，另以完整universe檢查expected中已不存在的suite。`mutation:check`保留原套件、原指令、原退出碼及嚴格度，恰在某一片執行；不因分片跳過它。

每列另保留真實子程序`process_exit_code`，彙總必須收到整數0；缺失、布林、非0、未啟動或逾時的空值均拒絕。帳本inventory沿用原本的零斷言計數，不能偽造為一個通過斷言；其餘僅退出碼腳本保留原通過計數1。負控制同時驗證原runner記錄真實退出碼與彙總拒收偽綠列。這項修正來自首輪真CI彙總誤拒inventory的實際紅燈；不是放寬原mutation檢查。

```sh
python3 tests/native_sharding_mutation_check.py --output /tmp/native-sharding-proof
```

此GitHub CI反證使用同一支真實`test_partition_covers_actual_suite_registry_once`：基準exit0；只從其中一片拿掉一個suite，必須以該測試的正常AssertionError紅exit1（非error／skip／timeout）；恢復後exit0。原始0／1／0、移除的suite與stderr均上傳artifact。

`--shard`拒絕與`--only`／`--extra-py`／`--simulate-missing`混用，也不能更新expected。原`--allow-skip`的人工用途及具名允許清單不變；CI不設它，彙總只接受原允許skip。

本機只編輯與靜態檢視，所有執行、反證及效能量測以GitHub Actions原收據為準。bridge突變裁判另涵蓋`tests/*.py`、`tests/*.c`、`tests/fixtures/**/*.scene`與根目錄場景；這些來源改變會使舊收據過期，必須由GitHub真重產完整帳本並保留原strict check，不手改hash或當成環境豁免。

## R06 分支的同一基礎設施

R06 以 `bf178770a0e10e996014ec0b6487e186db561c7f` 的純 CI 差異三向套用，保留 R06 新增的兩個 Python suite，第一次以 5ed 交付時為 226 套。完整 [Actions run 41335411500](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41335411500) 的三份原始收據為 75／76／75 套，聯集精確等於 226、全部 ran、無重疊；記錄的 suite 時間為 727.680／730.221／427.026 秒。這次仍有真實回歸與舊 mutation ledger stale，不能當作驗收綠燈。

依該完整 census，只補上新 suite 的實際發現數 48／7，以及 Node aggregate 737→753；其餘原數量不變。Node 22 的 `node:test` 非隔離 run 沒有套用本 adapter 所需的名稱篩選，嚴格控制正確回報完整性錯誤；native CI 與 R06 專項一致明確選 Node 24，保留同一篩選、精確 test stream 與負控制，不把全部測試的錯誤當成指定案例的 kill。

## 合入已批准主線後的 R06 來源（2026-11-02）

使用者續授權正常合入主線 `8f82b207e87c086705a1d8b7a00e2f215c07cbcf`，保留原 R06 與主線歷史。核心、產品 JS 與測試 Python 凍結來源為 `0c56690b46747fbc6e460b677b92acb401cfa4de`；主線新增六個 suite，R06 的兩套仍保留。

[同來源完整 census run 41361134169](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41361134169) 的三份原始收據為 77／78／77 套，聯集精確 232，無重疊、漏列或多列，全部實跑；三份 registry／expected 問題均空。套件時間依序為 790.129615／817.702027／584.680204 秒，Actions 完整 job 時間為 876／899／649 秒，兩種時間分開記錄，皆低於20分鐘。沿用原耗時表與新套件1000ms預設權重，沒有延長35分鐘期限。

原生 R06 48／48、裁判 7／7、分片守門 12／12、Node 753／753 全部通過，四套均無 skip。全量 counted 為 5411＝5410 pass＋原具名 Windows GDI 允許 skip 1；不能宣稱全量無 skip。該次唯一紅列是舊帳本 `mutation:check` 真退出碼1：123筆中120 stale、3 retired，其他231列真子程序退出碼均整數0。原分片刪除 `c:integrity` 的正常 AssertionError 反證仍為0／1／0，彙總也正確拒收紅列。這是來源合併後的完整 census，不能當成最後驗收綠燈；新來源帳本與最後完整 CI 另依 PR 收據核對。

## R348歷史：兩輪315套／三片規劃（2026-11-12，已被慢runner反證）

本節保留原方案、來源與當時模型；正式安排由下一節四片方案取代，不將歷史回放視為最終通過。

基底`6c41bd14f4cab19ace45ae4d55bbf86256455cb7`的420000ms補充權重，只把H7與reader分開；兩片真收據仍超時。新`measured_runs`從六份原始`native-shard-*`收據生成，保留每一輪獨立的315套成本；每筆為`round(row.seconds * 1000)`，630筆逐項符合PR留言6816253268。頂層224筆歷史資料、來源欄位及原`supplemental`原樣保留，沒有把420000冒稱H7實測。兩輪來源如下（job依片1／2／3）：

| Run | PR head | 實際checkout | Source jobs |
|---|---|---|---|
| [43162989157](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/43162989157) | `6c41bd14f4cab19ace45ae4d55bbf86256455cb7` | `66aad332b3833db916fd0717f52e045450d1f0a5` | 130998274222／130998274260／130998273909 |
| [43150038015](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/43150038015) | `8239dbf195a09506e6429f38229e134bbd846909` | `4ec020d8236385b617d98463473523c22a5cde10` | 130956793594／130956793236／130956793618 |

每片資料另外帶完整job／artifact連結、原ZIP與JSON SHA-256、原收據`seconds`及`exit_code`。43162989157片2原`exit_code=1`（mutation freshness）照錄；耗時可用於規劃，不表示該次驗收通過。`profile_digest()`仍雜湊同一份完整JSON，涵蓋新增來源與成本，不另開未被收據綁定的配置檔。

預設規劃以每套的兩輪成本向量工作：依最大觀測值遞減、名稱打破平手；逐套選加入後「該片各輪累計的最大值」最小的片，平手依各輪累計總和及片號。接著只做一次有界交換掃描：片對依`i < j`、名稱依字典序，交換必須讓全部片／情境的累計值降冪tuple嚴格下降；每個左側套件找到第一個改善交換即繼續下一套。不用亂數、不反覆搜尋至收斂，不平均掉不同runner的成本差異。最後按原registry順序輸出，完整聯集與不重疊守門不變。

對本次315套產生99／108／108套；以下是**以原JSON浮點成本回放同一配置**，不是新head的實際CI收據：

| Run | 片1套件秒數 | 片2套件秒數 | 片3套件秒數 | 加100秒後最大值 |
|---|---:|---:|---:|---:|
| 43162989157 | 854.940 | 1068.132 | 1068.127 | 1168.132 |
| 43150038015 | 1066.979 | 968.505 | 1041.845 | 1166.979 |

原六片最大「收據秒數－套件秒數」為92.194565秒（向上顯示）；規劃另預留100秒，再要求至少30秒餘裕。因此預算測試逐輪驗`max(suite_ms) + 100000 + 30000 < 1200000`，本次最大1198.131秒（整數毫秒表）通過。100／30是規劃預留，不能寫成實測。收據計時包含建置及runner成本；GitHub整個job的checkout／setup／upload則另計，35分鐘上限未改。

原`<600000`歷史profile與`<650000`補充相對權重assertion保留，後者明確回放原224筆加420000的配置；正式預設另由上面的兩輪真成本預算驗收，仍驗H7與reader分離。新增assertion併入原method，`py:test_unittest_runner`仍12項、expected未改。

`native_sharding_mutation_check.py`除原刪一套件反證外，新增兩組正常AssertionError的0／1／0，全部由現有coverage job執行並保留原始log：

- `R348_REVERT_MEASURED_PROFILE`：只撤回預設路由為歷史224筆加420000，完整量測與裁判不動，預算回到1384.929秒而紅。
- `R348_REMOVE_SCENARIO_SWAP`：只拿掉交換掃描，完整兩輪及greedy保留，預算回到1213.442秒而紅；還原為1198.131秒綠。不能用KeyError、timeout或skip代替kill。

限制：本方案涵蓋兩個完整觀測情境，**不保證任意逐套最慢值混搭**。逐套取兩輪最大值的總套件成本3463.371118秒，加三片各100秒等於3763.371118秒，已超過三片3600秒總預算。把舊輪H7單點改成713秒的敏感度為片1加100後1191.536秒；把同樣713秒混入新輪則片1為1319.874秒，不通過。整批成本再乘1.7亦不通過，不能據此宣稱任意慢CPU已獲保證。

上述三片當時仍須由exact head原收據各`seconds < 1200`裁決，後來的d7515daf正式收據未通過；不能以模型或ME採入解除超時。

## R348現行：保留完整來源，四片驗收（基底f10c4791）

固定基底`f10c4791ee5adfa5d645caea784410b1afa3b060`。原兩輪`measured_runs`的全部630筆、來源與失敗狀態原樣保留，另追加[43177620127](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/43177620127)完整315筆；不是退回20套樣本。最新PR head為`d7515dafd8933ca2d0d071184d1884031038333f`，真checkout為`ec80875d0723768b90166691d3119ed7b25984de`，三個source jobs依序為131045589092／131045588729／131045589006。原ZIP／JSON SHA-256、artifact／job URL、receipt seconds／exit均寫入同一profile，毫秒仍為`round(row.seconds * 1000)`。完整profile由既有`profile_digest()`綁定。

最新原收據為1406.750756／1132.062105／944.636343秒；片1的99套合計1291.186713秒，開銷115.564043秒。H7為755.187043秒、10/10通過，原mutation freshness的exit=1照錄。採入ME不能改變這份超時收據。f10c4791相對d7515daf只改原樣ME及兩份架構產物，分片來源相同；歷史執行不重標為f10c4791。

`native_shards.py`不需修改：原情境規劃器已接受任意有效片數及至少兩輪完整資料。以完整三輪規劃四片為51／87／89／88套，聯集315、零重疊，片內維持原registry順序。下表均為逐套整數毫秒模型的回放，不是四片新head的正式執行：

| 原始Run | 片1套件秒數 | 片2套件秒數 | 片3套件秒數 | 片4套件秒數 |
|---|---:|---:|---:|---:|
| 43162989157 | 455.303 | 845.592 | 845.150 | 845.149 |
| 43150038015 | 787.753 | 751.737 | 798.970 | 738.864 |
| 43177620127（d7515daf） | 845.583 | 809.795 | 819.060 | 775.768 |

新守門同時驗每個完整觀測情境，及每套取三輪最大值的更保守組合。開銷預留由100增為120秒（已觀測最大115.564秒上取整），原30秒規劃餘裕保留，總限制仍是嚴格小於1200秒；這使守門更嚴，不是增加時限。

| 每套取三輪最大值 | 片1 | 片2 | 片3 | 片4 |
|---|---:|---:|---:|---:|
| 套件秒數 | 862.898 | 912.666 | 898.140 | 907.489 |
| 加120秒開銷＋30秒餘裕 | 1012.898 | 1062.666 | 1048.140 | 1057.489 |

全部套件再乘1.7的敏感度如下，公式為`套件合計 * 1.7 + 120`；若120秒也乘1.7，每格再加84秒。這個壓力情境不通過，不能宣稱四片保證任意慢CPU：

| 原始Run | 片1預估秒數 | 片2預估秒數 | 片3預估秒數 | 片4預估秒數 |
|---|---:|---:|---:|---:|
| 43162989157 | 894.0151 | 1557.5064 | 1556.7550 | 1556.7533 |
| 43150038015 | 1459.1801 | 1397.9529 | 1478.2490 | 1376.0688 |
| 43177620127（d7515daf） | 1557.4911 | 1496.6515 | 1512.4020 | 1438.8056 |

這不是再調權重就能保證的情境：最新總成本3250.206秒，`3250.206 * 1.7 / 4 + 120 = 1501.33755`已是四片最大值的理論下界；H7單套755.187043秒乘1.7亦已1283.817973秒。後續n²依賴記帳效能另案設計，不在本補丁改K來源圖。四片仍須正式收據通過才可收尾，不能以分片取代產品測試。

### 回歸與具名反證

新增assertion併入原method，`py:test_unittest_runner`仍12項，expected與golden不變。先只採T（完整量測＋測試），保留原三片workflow：覆蓋接線及預算兩個正常AssertionError紅；再採P四片workflow後應全綠。原`<600000`／`<650000`、兩輪三片`+100000+30000 <1200000`保持；舊兩輪內容及新輪內容另固定canonical SHA-256，防止來源被重標或時間被降低。

原`R348_REVERT_MEASURED_PROFILE`與`R348_REMOVE_SCENARIO_SWAP`繼續以原兩輪／三片歷史回放殺死。新四片移除swap的模型仍可低於1200，因此不把歷史kill冒稱四片性能證據。新增具名撤回驗三片回退、native job名稱、runner分母、漏第四matrix項、coverage parts、35分鐘放寬、來源刪改及只在四片漏一套。每組均要求真0／1／0、指定assertion、0 error／0 skip，不以異常或逾時算kill。全由既有native coverage job執行及上傳，不手改mutation ledger。

### Repo端required checks

一般CI改為13個job，不代表repo目前已設定13個required contexts；GitHub是按名稱設定，沒有「12改13」數字欄位。2026-11-12讀取rulesets為空清單；classic branch protection因連接器403未讀得，現行required清單未確認。補丁不修改repo管理設定。

等grokbot FF推送後正式PR CI成功產生新名稱，再由具管理規則權限的人操作：

1. 開[Branches設定](https://github.com/ZhiQiYang/geometry-axiom/settings/branches)，找到適用main的Branch protection rule，按Edit。
2. 在Require status checks to pass before merging中，同次編輯移除`native (1/3)`、`native (2/3)`、`native (3/3)`，加入`native (1/4)`、`native (2/4)`、`native (3/4)`、`native (4/4)`。
3. 保留`native complete coverage`、`browser (canvas) complete coverage`、`browser (canvas 1/2)`、`browser (canvas 2/2)`、`browser (timber)`、`browser (space)`、`browser (grid)`、`browser (assembly)`、`browser (documents)`及其他既有要求；若原12項全required，替換後就是13項。保留原來源App及分支更新等設定，按Save changes。
4. 如果實際使用[Rulesets](https://github.com/ZhiQiYang/geometry-axiom/settings/rules)，到Settings的Rules／Rulesets，編輯適用main的啟用規則，在required status checks清單做相同替換並Save changes；若兩種保護同時存在，所有適用規則都要核對。
5. 回PR最新head／GitHub test merge commit檢查13項結果與四份原收據，確認沒有舊`/3`名稱繼續等待。不刪coverage或停用保護以繞過等待。

## R380 新套件的獨立登錄與有界規劃（2026-11-12）

本次新增兩套測試，原三份 `measured_runs` 各自仍是 315 套，原檔及 canonical SHA-256 不變。`native_shard_added_evidence.json` 獨立保存新增套件的來源與規劃上界；讀取時才合併成目前的 317 套 registry，不把新增成本寫成歷史實測。`profile_digest()` 同時涵蓋原 profile 與此追加證據的 LF bytes。

來源是 [run 43231596387](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/43231596387) 的 [native 2/4 job 131228034964](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/43231596387/job/131228034964)，source head `a4ea8327bd4a7c0b4089a89ea6d0f270a8f01659`、實際 checkout `2b9d0eea17155c2d857447466aa4a9abce649036`。該 job 整體因 expected 登錄缺漏而失敗；下列兩個 suite 自身全部通過。秒數來自原日誌的一位小數摘要，不能冒充更精確的量測。先前 run `43212366533`／job `131162945568` 的 35.5 秒原日誌保留在補丁證據包，規劃改採最新 61.9 秒來源，沒有降低任何已知實測。

| suite | 原收據 passed / discovered | 原摘要秒數 | 本次規劃上界 ms |
| --- | ---: | ---: | ---: |
| `py:test_panel_fill_grid_source` | 13 / 13 | 61.9 | 65000 |
| `node:panel_fill_grid_read_compat` | 11 / 11 | 0.1 | 2000 |

追加證據必須提供 source run／head／checkout、每套 source job、完整通過計數及高於日誌摘要秒數的整數規劃上界；缺來源、重複名稱、失敗測試、低估成本或與原實測 registry 重疊均拒收。這兩套的 expected 計數按完整實跑精確補入；`py:test_geo314_commit_paths`、`py:test_unittest_runner`、`node:room_candidate_cold_contract` 分別以新增的實際 method／case 更新為 12、13、9。

原單輪兩套交換在完整 317 套的三片重播超過預算；最新 65000／2000 ms 上界也使單一起點的兩輪 pair swap 加四輪 two-for-one 改善不足。本次保留原 greedy 起點，另外最多八個固定起點，將成本最高的套件依序與接下來八套同片，再填入其他套件。每個起點先執行兩輪原 pair swap，以原完整跨情境字典序評分選唯一最佳，再執行四輪「一次最佳 two-for-one exchange，加一輪原 pair swap」。每個 shard 只選成本最高的 16 套作 two-for-one 候選，同成本以名稱穩定排序；四片每輪最多 `4 * 3 * C(16,2) * 16 = 23040` 個候選。起點數、候選數、搜尋輪數皆有固定上限，只有嚴格改善才交換，不依套件名稱、PR 或預算門檻特判。

三片歷史重播仍包含全部 317 套，原 `+100000+30000 <1200000` 不變。正式四片仍驗全部 registry 恰好一次、三份來源成本及 per-suite 最大包絡的 `+120000+30000 <1200000`。新增具名撤回 `R380_REVERT_SINGLE_PAIR_SWEEP`、`R380_REMOVE_MULTISTART_SCREENING`、`R380_DROP_ADDED_SUITE_EVIDENCE`，連同原具名突變全部要求正常 AssertionError 的 0／1／0；不以 crash、timeout 或 skip 算 kill。正式四份 wall-clock 收據與完整 CI 仍須另外驗收。

官方說明：[required checks與最近七日成功條件](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)、[classic設定](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)、[rulesets設定](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository)、[多規則聚合](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)。最終合併判斷仍需最新來源全部正式CI、四份`seconds <1200`原收據、完整coverage及mutation freshness通過。

## R379 新套件加入後的有界情境規劃（基底57d55edc）

R14 三個新增 suite 的獨立來源保留在 `native_shard_added_evidence.json`，其規劃上界合計為 11000ms。三份歷史 `measured_runs`、224 筆原權重及 supplemental 權重全部不變。新增套件仍與原 315 套一起參與既有三片回放及正式四片規劃；沒有把它們排除在預算之外。

只用原本「最大成本遞減」的單一起點加一次交換，在 318 套時落到另一個局部結果：前兩輪三片最大值加原 130000ms 預留為 1204609／1205166ms，原嚴格 `<1200000` 正常拒收。一換一保留各片套數，而一換一／二換一也未必能一次移走多個小套件，讓情境互補的大套件進到同片。修正保留原 greedy 起點及完整成本向量，再增加至多八個固定起點：依最大成本／名稱排序，將最大套件分別與接續八套之一預放同片，再執行原 greedy。每個起點只先做兩輪原一換一掃描，以全部片／情境負載的降冪 tuple 選出唯一最佳者；只有勝者再做固定四輪「二換一最佳交換＋原一換一掃描」。二換一只搜尋各片依同一排序的前 16 套，每次只採 tuple 嚴格改善，同分保留第一個選擇。這使套數可在片間改變，仍保留每套恰好一次，名稱及片號固定打破平手，片內維持原 registry 順序。不改權重、不依亂數、即時耗時或機器 cache，不迭代到收斂，亦沒有套件名稱或預算特例。#379 與 #380 使用同一份通用規劃器。候選起點最多九個，但昂貴的二換一只執行一組；本機篩選加改善的三片／四片規劃約 0.81／1.34 秒，完整 13 項 runner 為 13.193 秒。

本機整數毫秒模型回放如下，這不是新 head 的正式 CI 收據：

| 模型 | 片1 | 片2 | 片3 | 片4 | 最大值含原預留 |
|---|---:|---:|---:|---:|---:|
| 原兩輪／三片：43162989157 | 894057 | 1054068 | 1054069 | — | 1184069 |
| 原兩輪／三片：43150038015 | 1054366 | 993471 | 1040487 | — | 1184366 |
| 三輪／四片：43162989157 | 467713 | 844827 | 844827 | 844827 | 994827 |
| 三輪／四片：43150038015 | 760657 | 743842 | 767339 | 816486 | 966486 |
| 三輪／四片：43177620127 | 844830 | 831849 | 748161 | 836366 | 994830 |
| 四片逐套三輪最大值 | 874865 | 902000 | 899430 | 915898 | 1065898 |

三片為 91／113／114 套，四片為 6／104／105／103 套；兩者皆精確涵蓋全部 318 套一次。套數不同反映各套成本及跨輪情境不同，規劃不追求套數相等。三片保留 100000＋30000ms 預留，四片保留 120000＋30000ms 預留，所有既有測試斷言、workflow 35 分鐘及收據 1200 秒限制不動。`test_unittest_runner.py` 本輪未改；前一片已新增的來源反證 method 實跑共 13 項，因此只精確補 expected 的 12→13。

新增 `R379_REVERT_SINGLE_START_ONE_SWEEP`，只在子行程中恢復原規劃器，不改測量、suite 或裁判，必須以原 `R348_MEASURED_RECEIPT_BUDGET` 正常 AssertionError 產生 0／1／0。原刪一套件、撤回真實量測、移除交換及全部四片具名反證仍執行；正式四份原收據及 ME freshness 仍須採入補丁後另驗。

## #379 × #380 合併：新增套件證據改為每來源一檔（候選，待 ChatGPT 審）

#379 與 #380 各自新增了 `native_shard_added_evidence.json`，而原 schema 只允許單一 `source_run`，兩份無法聯集。候選解法：改為目錄 `tests/native_shard_added_evidence/`，每個來源一檔（`pr379-r14.json`、`pr380-c0-from-fill.json`，兩檔內容與兩邊原檔位元相同）。`added_suite_costs()` 依檔名排序讀取每一檔，逐檔沿用原 `native-shard-added-suite-evidence/1` 全部驗證（來源 run／head／checkout、每列 source job 屬於該檔 run、完整通過、上界高於摘要秒數且 <1200000），另拒收空目錄、缺目錄及跨檔重複套件（`R380_NEW_SUITE_UNIQUE_ACROSS_SOURCES`）。`profile_digest()` 改為雜湊原 profile 加上每檔「檔名＋LF bytes」。之後新增 suite 的 PR 只需新增自己的檔，不再 add/add 衝突。

`R379_REVERT_SINGLE_START_ONE_SWEEP` 移除：它重寫的 `_scenario_owners`（原 greedy＋一輪 pair swap）與 main 上 `R380_REVERT_SINGLE_PAIR_SWEEP`（`_improve_scenarios = _swap_scenarios`）在三片／四片、兩輪／三輪 profile 下產生逐套相同的 owners，是同一個撤回的重複；R380 三個具名突變保留。
