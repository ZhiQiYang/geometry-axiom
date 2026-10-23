# GEO-261／PR #288 雲端交接（2026-10-22）

使用者決定把後續驗收交給雲端 Codex，釋放本機。本次只完成帳本、架構與交接推送；**最新候選的完整七項、P52、Q38、§7、P-189 尚未執行**，不得宣稱 PR 已可合。

## 來源與交付版本

- 分支：`architecture/geo261-integration-20261016`。
- 產品與裁判凍結來源：`52b951940f570011b257cd207741ba0a7f6d7ce9`。
- 完整帳本執行來源：同上52；帳本產物提交／本輪架構執行來源：`0548c05cccbb7b35def6bbc3d6b285004be676e5`。
- 帳本與架構都提交後的候選完整 SHA：`60425b629aee9f74f4e62ea88af9882bc8968881`。
- 本交接檔、`.txt` 附件、`.gitignore` 放行及只針對附件的 `.gitattributes -text` 另為交接提交，只有證據資料，沒有改產品或裁判。附件保留原始bytes以便跨平台核對hash。**交接包的最終推送 SHA 請以 `git rev-parse HEAD` 讀取，並與 `git ls-remote origin refs/heads/architecture/geo261-integration-20261016` 相符**；本檔無法在自身提交內硬寫該提交的雜湊。雲端七項及專項應固定在實際接收的交接包完整 SHA，不把來源52或產物提交冒充最終驗收 SHA。
- 本機工作 clone：`D:\geometry-axiom-work\geo261-integration`；本機 `D:\geometry-axiom` 的 main 未 checkout 或修改。
- PR：<https://github.com/ZhiQiYang/geometry-axiom/pull/288>。不代貼正文、留言或合併；使用者負責最後審查及合併。

## 已完成且有收據

### 完整突變帳本

`python3 -B -u tests/mutate.py` 與 `python3 -B tests/mutate.py --check` 都在私有乾淨52 checkout 執行，**兩條退出碼都是0**；不是只刷過期或剩餘項。

| 指令 | 實際退出碼 | 秒數 |
|---|---:|---:|
| `python3 -B -u tests/mutate.py` | 0 | 6325.178997 |
| `python3 -B tests/mutate.py --check` | 0 | 21.102286 |

完整帳本JSON SHA256：`bd9c88f598b8bd1a82cd2f561b1953ba034837cc44e66d49556dd246c8bc4c73`。
原帳本收據 SHA256：`f4cd4832ee50cb14a356463d8208a9d31d8c492a2653e11bb4856596eeccfccb`。

- 78筆：70 killed／1 crashed（M20）／4 equivalent／3 retired；invalid、stale、blocked、survived 全0。
- 75 active 的 `execution.head` 全為完整52，57筆核心執行 schema＋18筆橋接執行 schema。
- M20基準線通過後，同一夾具連續3次 SIGSEGV（-11），列 crashed，沒有冒充具名斷言 killed。
- `verify_order_ledger_completion.py` 獨立比對原log78個唯一判決、完整JSON、全部命令退出碼與來源／hash，退出0；背景host及監督退出0、cleanup.remaining=[]。
- 提交內 `tests/mutants_results.json` 與原輪JSON逐byte相同。附件的原收據、log、check及verified可獨立讀回；JSON本體在上述版本化路徑。

### 架構原三關與四檔

從 `0548c05cccbb7b35def6bbc3d6b285004be676e5` 封存完整五roots及六必要檔，沿原driver及原裁判重產；來源與包含產物的提交分開記。

| 原裁判指令 | 實際退出碼 | 秒數 |
|---|---:|---:|
| `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | 0 | 24.608000 |
| `python -B tests/test_architecture_contract.py` | 0 | 26.054000 |
| `python -B tests/test_product_architecture.py` | 0 | 124.249000 |

| 四檔 | SHA256（原始bytes） |
|---|---|
| `product-architecture.json` | `472550e33b541ed302c112a98d7608282f74b5e8c1c285e6664eb45bbc06a452` |
| `product-architecture-scan.json` | `a107ce7ceff08edede8b0c3c963837f19518d8d9d66ab6014212025fa212d3a6` |
| `product-architecture-receipt.json` | `61f7bf95555624059690eb50a7f3907a797d406ee1cad71c0e6493d7035ff259` |
| `PRODUCT-ARCHITECTURE.md` | `c591715fd8b590ad0e752b9b2ce1842f1f418e5ebe2869ddeafa9b52e0dff0ba` |

來源封存SHA256：`37d7d3c2ce826b58532fff88596d9278a4971ca4ae1d8c01b6cfe0986961401f`；原driver SHA256：`c786be4a0cd7288163c4004aeb06485997594d63a835f4e33a0dee6840b169c5`。

- scanner：601 executable／333 owned／268逐檔排除／796 edges／0 diagnostics；K69、W67、H191、vendor6。
- 本輪產品執行碼未變，`changedPreviouslySealedInputs=[]`；沒有 stale excluded/vendor/embed digest。原driver `allRawAndLfInputsUnchanged=true`。
- 通用架構205項＝204通過＋1 Windows符號連結權限skip（WinError1314）；產品架構18／18、0skip。三條命令退出0不等於該Windows skip已驗到；雲端Linux應再由native涵蓋。
- 四檔都重產並獨立讀回hash，manifest／scan內容維持，實際git差異只report與receipt；明列四路徑提交。

### 已累積的產品修正與歷史反證

相關P52原量測、45fc timing、P88／P72B及order-index診斷收據也以同目錄.txt附上並列入hash清單；它們各自保留原來源，不能當最新交接SHA通過。

- `45fc3092b55cd296424eb49c0d3ea69990484a46`：P52先實測出產品退化，原main／7dae各8次中位數637.285／828.490ms（1.30003倍），因此修正freshness inventory掃描成本，仍讀完整路徑及內容，沒有TTL或省略P-177守門；同時把sleep400改成有上限等待，保留足跡斷言。當時修正後各16次中位數653.110／522.622ms；撤回產品修正同裁判轉紅。這些是歷史來源證據，新交接SHA的P52仍待跑。
- `76df2d816abfee02d3bb9eb545d7fb5c12150801`：P88在版面穩定後恢復guide inspector捲動，保留後續使用者捲動。當時原P88=143／0、只撤回產品修正即原點擊／world斷言紅；不能因此省略新完整canvas。
- `0369579ef93b9046130d756e072f59c394654b09`：P72B等待唯一新文件marker、complete及ready。當時正常與延遲導頁50／0，撤回等待同裁判紅；P72B golden維持50。
- `2f695e7817d3e1920c8bd1c55f8a7aa1f8f3c9da`：W接觸查詢建立每次呼叫的堆疊索引，排序取最後一筆同id事實、去重取所有事實的minimum order（含未放置／不同host），保留穩定同序、先判pair再去重及排除指標。完整u32 id（含0／MAX）安全，128槽對應容量64，超64沿原線性fallback；沒有heap／持久快取／容量增加／ABI變動。原diagnostic 60樣本與byte相同載回／dump不等於最終P-189。後來第4輪發現的舊負控制錨點與漏登記，由52另修，詳下。

### 第4輪 native 為何紅、怎麼修

第4輪來源 `ac39346e74ca2ab6fc5bb0053024bd26f8af06b2`，標籤 `codex-final-r4-20261022`，parallel1。七套都實際結束：canvas2267、assembly150、documents47、grid356、space242、timber79各exit0；native exit1，5177＝5175通過／1失敗／1允許的Linux GDI skip。總結果保留 `red: native`，兩次失敗套件獨跑也都是exit1，沒有flaky豁免。

1. `tests/test_geo261_wood_contact_world.py` 的 equal-order-dedup 控制仍找已消失的 `world->members[t].order<order`，命中0處，於「必須改到一處」斷言失敗，當時尚未執行產品突變，不能算killed。修成實際索引路徑 `index->minimum[slot]<order`，仍只改 `<` 為 `<=`，仍用原ordering夾具及原 `ASSERT:equal-order-not-deduplicated`。
2. `tests/run_all.expected.json` 的 `py:test_geo261_contact_sources` 漏登新增項：登記12、實跑13且13／13通過。只把該一筆12改13，沒有批量更新expected、刪測試、改斷言或放寬數量守衛。

英文提交：`52b951940f570011b257cd207741ba0a7f6d7ce9`，恰上述兩檔各一行。產品C、容量64、SSOT及P-177守門流量都沒有改。

原生複驗來源如實為「乾淨ac＋精確兩檔overlay」：

```sh
python3 -B -m unittest -v tests.test_geo261_wood_contact_world tests.test_geo261_contact_sources tests.test_mutation_anchors
```

26項（10＋13＋3）全部通過、0skip、exit0；20＋8個具名負控制全部基準綠→原正常ASSERT紅→恢復綠。equal-order新位點確實執行產品突變。兩提交blob經LF規範後與所驗候選逐字相同；原收據SHA256 `f834a4deabcc6de9d9d070643efeffb24570acd00e22359ecc26a7e005e07ea9`。附件包含原receipt／verified／commit讀回與原單元log。

R4 canvas2777.5秒、native4771.2秒都超正式35分鐘，功能退出碼與正式時限分開揭露，未改timeout。09:56第3輪中斷是**使用者關機**；原輪無完整退出收據，不算產品／環境失敗或通過，不再調查原因。

## 尚未跑，雲端依序接手

1. 實際接收的完整交接SHA之七項：native、canvas、assembly、documents、grid、space、timber；parallel1。保持原完整golden與嚴格expected，不能挑綠拼湊。
2. 同一SHA的P52真實點擊放置耗時及等待負控制。
3. 同一SHA的Q38完整閘門。
4. 同一SHA的§7卡片參照及公理突變兩套。
5. 同一SHA的P-189三方交錯量測與載回／dump逐byte比較。
6. 全部通過後獨立讀回原始退出碼、raw log與hash，才重寫#288正文檔／收尾報告給使用者貼及請複審。不得擅自合併或展開其他列車。

目前沒有最新SHA的七項或專項綠燈。82e歷史P-189曾在N64=2.003174832239倍失敗；後續2f的60樣本診斷N64=1.75835286倍、只撤回索引為2.09896217倍紅，**這只是診斷，不能替代待跑的正式P-189**。

## 腳本附件、還原與環境

所有附件都在本檔同目錄，檔名 `geo261-cloud-*.txt`。`geo261-cloud-attachments.json.txt` 列每檔原始SHA256與byte數；原腳本逐byte附上。`kind=reference` 是本機流程／完整舊讀回判準參考，含D槽路徑，不能直接當雲端入口。

雲端需完整Git歷史（至少main `adbaebf9c73ea6801d7b4d5214e4b846b132923b`、base `3e600772076465fc65a26ac09055028301c0fb0b`及交接HEAD）、Python3.12以上、gcc、Node/npm、PyYAML、Google Chrome（`/usr/bin/google-chrome`）、CJK字型及fontconfig。缺套件屬環境受阻，不算killed或通過。先依根目錄AGENTS.md／公理層與workflow閱讀；本機專屬WSL鎖規則仍只用於本機，雲端直接跑Linux工具並串行鎖住自己的工作。

以下命令是雲端待執行說明；本機只驗過附件hash、還原及Python語法，**沒有在本機執行新雲端七項／專項**。使用無空白路徑，新的scratch必須不存在、位於repo外，不覆蓋舊收據：

```sh
set -euo pipefail
export REPO="$(pwd)"
export SHA="$(git rev-parse HEAD)"
export MAIN=adbaebf9c73ea6801d7b4d5214e4b846b132923b
export SCRATCH="/tmp/geo261-cloud-${SHA:0:8}-$(date -u +%Y%m%dT%H%M%SZ)"
python3 -B evidence/geo261-cloud-prepare.py.txt --repo "$REPO" --scratch "$SCRATCH"
export TOOLS="$SCRATCH/tools"
mkdir -p "$SCRATCH/tmp"
export TMPDIR="$SCRATCH/tmp"
```

還原器只改暫存副本的來源repo／輸出／generator路徑，原判準、取樣數及逾時不變；`preparation.json` 列逐項替換與執行版hash。保持原件與執行版hash分開，不把新還原版冒充原本已跑過的位元組。所有重型命令共用 `flock "$SCRATCH/heavy.lock"`，同時只跑一個；不要清別人的鎖、刪使用者資料或停止外來程序。

### 七項

```sh
export WSL_CI_REPO="$REPO" WSL_CI_PARALLEL=1
export WSL_CI_OUT="$SCRATCH/seven" WSL_CI_LABEL=cloud-r1
flock "$SCRATCH/heavy.lock" python3 -B -u "$TOOLS/ci_run.py" "$SHA" all 2>&1 | tee "$SCRATCH/seven-launch.log"
```

原runner讀取該SHA自己的 `.github/workflows/integration-tests.yml`，保留各job命令／golden／實際退出。必要套件必須先裝妥（缺套件會BLOCKED）；`receipt.json` 必須7／7 green、每套exit0、0failed、無flaky-rerun-pass、exclusive全程成立。原WSL runner有3倍看門狗及 `over_ci_timeout` 註記；雲端仍須逐套揭露正式workflow時限（native/canvas35、assembly/grid/space15、documents10、timber20分鐘），不得把超正式時限隱藏為正式CI通過。新native期望5177＝5176通過＋1允許GDI skip，並明確核對contact_sources13、wood_contact_world10、mutation_anchors3；full canvas2267、P88=143／P72B=50、golden matched，唯一刻意的fb-auto-probe與unexpected exceptions分開。

### P52

先準備固定main供交錯比較；不用重跑舊main/7dae診斷。這只在新私有scratch clone操作：

```sh
mkdir -p "$SCRATCH/work/p52-main/tmp"
git clone -q --no-checkout "$REPO" "$SCRATCH/work/p52-main/main"
git -C "$SCRATCH/work/p52-main/main" -c core.autocrlf=false checkout -q --detach "$MAIN"
(cd "$SCRATCH/work/p52-main/main" && flock "$SCRATCH/heavy.lock" npm run build) 2>&1 | tee "$SCRATCH/p52-main-build.log"
flock "$SCRATCH/heavy.lock" python3 -B -u "$TOOLS/postfix_validate.py" "$SHA" 2>&1 | tee "$TOOLS/postfix-${SHA:0:8}-launch.log"
python3 -B "$TOOLS/verify_postfix_receipt.py" "$SHA"
```

`postfix_validate.py` 使用main/fix/fix/main，每塊8次，合計各16次；量「真實點擊→references出現timber3」，保留1987..2014足跡斷言，要求fix中位數≤main。五個等待控制：normal／900ms delay各Node0、5／5；revert-delay／wrong各Node1、原足跡斷言4綠1紅；missing必須在有上限5000ms的具名等待失敗，Node1。真實Node退出碼須與原JSON日誌相符，timeout／crash／缺結果都不能當killed；`verify_postfix_receipt.py` 應退出0。完整七項不能由這個擷取的P52專項取代。

### Q38

```sh
flock "$SCRATCH/heavy.lock" bash "$TOOLS/q38_gate.sh" "$SHA" cloud-r1 - gate 2>&1 | tee "$SCRATCH/q38-launch.log"
```

完整gate、無patch、不選子集；原native27及model20基準線都0、0skip。42筆＝41 killed＋SPM24 equivalent；39個正常AssertionError紅，加SPM38／SPM40兩個因果ModelError紅，不能把所有ERROR當一般斷言或吞掉不相干環境錯誤。逐筆檢查正常基準、突變紅及恢復綠、來源SHA、裁判／突變表／編譯hash與gate退出0；不要一律要求所有紅都是AssertionError而誤殺那兩個合約拒絕。

### §7

```sh
flock "$SCRATCH/heavy.lock" bash "$TOOLS/card_ref_mutations.sh" "$SHA" cloud-r1 2>&1 | tee "$SCRATCH/cardref-launch.log"
```

不得設 `AXIOM_ONLY`。原卡片基準43／0；53個killed中50個是產品二進位突變，3個是裁判控制 `P146-error-fields`／`P154-identity-boundary`／`P154-identity-one-message`，不能統稱53個產品突變。每筆具名ASSERT紅exit1，errors/skips/編譯與infra失敗0；恢復exit0、原binary hash相同。公理基準44／0，V01–V05五個killed，紅1／恢復44綠0；保留 `raw.tgz` 的兩份原report、二進位／來源／裁判hash及兩個runner實際退出0。

### P-189

```sh
flock "$SCRATCH/heavy.lock" python3 -B -u "$TOOLS/p189_verify.py" "$SHA" 2>&1 | tee "$SCRATCH/p189-launch.log"
```

main固定adbaebf9、base固定3e600772、fix固定接收完整SHA，三方gcc `-std=c11 -O2 ... -lm`，stack16384；沿原scale_compare2交錯順序、N16/32/48/64各三輪，36樣本全部status=ok／ok=True。**四個點各自fix/main≤2，不可只看平均或N64挑綠重跑。** 原base與fix每個load回覆＋dump逐byte相同，四個生成效能場景必須load_ok=True；repo-root刻意拒絕的場景分列拒絕，不冒稱全部載入成功。保留編譯器／generator／timing-driver／bridge hash、raw stdout/stderr、dump-equivalence.json及samples.tsv，從原TSV獨立重算中位數；exit0與receipt.pass=true都要成立。

## 不可越界與限制

`公理層.md` 是SSOT，不擅改；P-177候選／驗證／seal／publish次數與時機不變，容量仍64。若再改 `tests/*.py` 或C include閉包，必須全量重產帳本及check，再依影響重產架構／最終驗收，不沿用本包綠燈。新本機交接附件只是文字，沒有新增產品執行入口。

實體手機／iOS、使用者Windows正式服務、P72B optional真雙服務fresh URL往返未另驗。既有MODEL-SOURCES文件殘餘及P-190未改，其他列車、#323／#300不在本次授權。GitHub Actions先前因計費0步驟失敗不能當證據；雲端若不能持續到完整驗收，留下真實部分收據，不宣稱完成。

本機交接完成後停止排程、確認鎖無持有者，再依使用者指示 `wsl --shutdown`；關閉結果及實際最後推送SHA另記在本機 `codex-closeout-20261021/cloud-handoff-final.json` 與最後回報。本文件不冒稱在寫入時已先驗到未來的關機結果。
