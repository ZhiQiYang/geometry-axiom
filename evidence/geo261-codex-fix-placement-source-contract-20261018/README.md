# 05：承載面來源測試承接 canonical definition 契約

修正分支 `codex/geo261-fix-placement-source-contract-20261018`，基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，受測修正 `f7ce2d212be778b8ac8c66c9afea66bae2fca4e3`。只更新兩個測試檔；產品、SSOT、expected counts、skip 與 timeout 均未更改。修前與撤回精確重現八項失敗，修後三套 **43/43**；恢復旁錄亦 **43/43、零 skip**，並保存五個真產品負控的指定 ASSERT。這只完成本主題的定向驗證，不代表整合分支全量驗收。

## 原結果與三證據

下表秒數取 unittest 原 footer，順序為 `placement_sources`／`placement_definition`／`host_placement_definition`。

| 階段／測試 SHA | 方法結果 | unittest 秒 | 外層秒 | 原件 |
|---|---|---|---:|---|
| 修前 `e9c1509c` | 13/21、15/15、7/7；8 fail | 4.615／3.970／10.077 | 19.464624 | [receipt](before/receipt.json)、[八項失敗原文](before/suite-logs/py_test_geo261_placement_sources.unittest.log) |
| 修後 `f7ce2d21` | 21/21、15/15、7/7；43 pass | 4.673／3.735／8.769 | 17.990689 | [receipt](after/receipt.json)、[原 stdout](after/command.stdout) |
| 撤回 `4ac088db19bfa296bb1634c1c4e3ea1603720dd2` | 13/21、15/15、7/7；原8 fail | 5.511／4.218／9.276 | 19.824949 | [receipt](withdrawn/receipt.json)、[八項失敗原文](withdrawn/suite-logs/py_test_geo261_placement_sources.unittest.log) |
| 恢復 `f7ce2d21`＋旁錄 | 三個 module 同一 unittest suite，43/43 | **14.188** | 14.346140 | [receipt](restored/receipt.json)、[完整 unittest](protocol-restored/unittest.stderr)、[原 protocol](protocol-restored/protocol.jsonl) |

前三輪的命令皆為 `python3 -B -u tests/run_all.py --only py:test_geo261_placement_sources --only py:test_geo261_placement_definition --only py:test_geo261_host_placement_definition`，各 module 分程序執行。三套自行建立隔離 NativeBuild；本次沒有加 `--build`。恢復輪則透過已審旁錄入口，在同一 unittest suite 執行原三個 module，不能把它說成再次跑同一條 run_all 命令，也不能把其時間與前三輪當效能對照。旁錄自身時間 14.213734 秒，與 unittest／外層三層時間分列。

四輪外層 exit 依序 1／0／1／0，無 timeout、interruption 或 launch error，source／head／status-diff 皆穩定。修前與撤回的 placement_sources 完整 unittest log **只差 `Ran` 的時間**；八個失敗方法、traceback 與 ASSERT 原文均相同，沒有把新錯誤充當撤回證據。[撤回提交原文與 diff](withdrawn-commit.patch) 與固定 Git 物件逐 bytes 相同，`e9c1509c → 4ac088db` 的整棵 Git tree 無差異。

## 分類與每項預期遷移

`2ba81689dc78005d5347644186049d10e7f56fb3` 同時新增來源 provider 與舊測試；[`138595e04282266c2fe860ddbf9b6a9fa4f49070`](https://github.com/ZhiQiYang/geometry-axiom/commit/138595e04282266c2fe860ddbf9b6a9fa4f49070) 引入 canonical DEFINITION、實際定義消費及候選持有的 decoded records，舊 suite 未同步更新。因此分類為 **五項預期過時、兩項測試寫錯（過時負控錨點）、一項負控被過時 baseline 阻擋**，沒有產品回退。

固定基底 [SSOT 分層契約 L69](https://github.com/ZhiQiYang/geometry-axiom/blob/e9c1509cf89e6f35d298743ec5e3368370316cf7/%E5%85%AC%E7%90%86%E5%B1%A4.md#L69) 要求依實際引用建立完整候選閉包；[D4 L113](https://github.com/ZhiQiYang/geometry-axiom/blob/e9c1509cf89e6f35d298743ec5e3368370316cf7/%E5%85%AC%E7%90%86%E5%B1%A4.md#L113) 要求具型別來源鍵與輸入引用；[D9 L253](https://github.com/ZhiQiYang/geometry-axiom/blob/e9c1509cf89e6f35d298743ec5e3368370316cf7/%E5%85%AC%E7%90%86%E5%B1%A4.md#L253) 區分定義與衍生值並要求完整依賴閉包。**enum 值、精確節點／邊數、callback 次數及借用地址規則來自 138595 的 API／實作與既有 definition suite，不冒稱是條文逐字指定的數字。**

| 原失敗／分類 | 逐項理由與精確修正 |
|---|---|
| `explicit-leaves-have-no-upstream-edges`；預期過時 | 本地 FRAME／REGIONS 現在都消費同 id 的 canonical DEF；3 nodes／0 edges 改為精確 **4／2**。新增兩條各自指向同 DEF 的 DEFINITION_REQUIRED，驗 DEF typed key、metadata、schema；原 geometry 值保留。 |
| `declined-binding-never-reads-upstream`；預期過時 | geometry binding 拒絕後仍須探詢 definition binding，callback 總數2→**4**；新增 FRAME=1／REGIONS=1／DEF=2、精確5 nodes／3 edges。原 frame_calls=0／region_calls=0 與既有 VALUE_REQUIRED 保留。 |
| `inline-set-borrows-its-own-store`；預期過時 | 新 canonical 定義由候選持有的 decoded record 提供，API 承諾同候選生命週期，並未承諾等址原始 input components。改驗借用 view／outline／hole pointers 與 literal 幾何在 sibling reads 後、同 placement FRAME 後、seal 後重讀10次仍穩定；不以 `!= raw_store` 作新預期。原順序／孔資料檢查提前到安全解參照前，並在每段再驗。 |
| `unknown-key-kind-rejected`；預期過時 | tag 3 已明定為 DEFINITION，不能再當非法值。改用255作原拒絕例，另逐一驗4..254與既有0，共涵蓋253個非法 tag；保留失敗時 kind／id 不變，新增3的精確 BE bytes／完整 uint32 decode。 |
| `region-reference-has-two-nodes-one-value-edge`；預期過時 | 原 region VALUE_REQUIRED 之外新增 placement→DEF 邊，2／1 改為精確 **3／2**；原 value-edge 斷言仍在前，不掩蓋負控。region node 由 source key 定位，不固定取已變成 DEF 的 node1；原無 placement-context 斷言保留。 |
| binding-value 負控 `Negative control must hit one real expression`；測試寫錯 | 產品現在按 kind 選 DEFINITION_REQUIRED／VALUE_REQUIRED，舊 literal 命中0。同步 before／after literal 的三元式，仍只丟棄回傳值、保留求值與 typed edge；唯一命中、精確 exit1／ASSERT 與前後正控制不變。 |
| boundary binding-value subtest `1 != 0`；測試寫錯 | 與上一項同一過時 literal；更新錨點後五個控制各恰命中一次，沒有繞過或刪除 boundary 檢查。 |
| region-edge 負控先遇相同 `region-reference-has-two-nodes-one-value-edge`；baseline 阻擋 | 負控本體、marker、判準均不改。只修 baseline 拓撲與 node lookup 後，才能真正執行並要求缺邊時命中 `placement-region-reference-edge`。 |

[實際採用 diff](source-fix.patch) 僅修改 `tests/geo261_placement_sources_harness.c` 與 `tests/test_geo261_placement_sources.py`，兩檔 bytes 與原已審05提案相同。21個方法名稱保留、11個 Python assertion AST 全等；具名 C CHECK 由116增至126。三個過時 marker（explicit 無邊、inline 等址原始 store、region 2／1）以表內精確新契約取代，不能籠統說所有 C 斷言原文未變。`edge()` 仍只驗 VALUE_REQUIRED，另以 `typed_edge()`／`definition_edge()` 精確驗定義邊，不接受任意邊。候選隔離、失敗輸出原子性、memoized failure、雙向 destroy order 及 provider batch 原子性保留。

## 五個真產品負控，與測試撤回分列

恢復旁錄共有 **29 個 native-client 事件＝24 個 exit0＋5 個 exit1**。每個負控都由原方法執行「正控制0 → 突變1 → 恢復正控制0」；前後正控制執行檔 SHA 相同、突變執行檔 SHA 不同。下表五個 exit1 的 stdout 都是精確空字串，stderr 都是單行 `ASSERT:<marker>\n`。

| case | 精確 marker |
|---|---|
| binding-values | `placement-binding-consumes-upstream-frame` |
| batch-duplicate | `batch-duplicate-second-rejected` |
| batch-invalid | `batch-invalid-second-rejected` |
| region-edge | `placement-region-reference-edge` |
| batch-closed | `batch-used-or-sealed-graph-rejected` |

原測試仍以精確 exit1／marker／空 stdout 判定，編譯失敗、timeout 或 crash 不算負控通過。完整事件、命令與 executable hash 在 [protocol](protocol-restored/protocol.jsonl)，逐組核對在 [protocol-review.json](protocol-review.json)。這五個是隔離產品 guard／資料使用的突變；`4ac088db` 則是**撤回測試修正的紅色對照**，不能冒稱撤掉產品修正。

## 環境與證據邊界

Linux 6.18.55 x86_64／glibc2.41、GCC Debian14.2.0-19、Python3.12.14、Nodev24.19.0、Google Chrome155.0.8059.84（另有 Chromium154.0.8037.57）。本題不啟動瀏覽器；版本 stdout 在各 stage 封存。

恢復旁錄只包 `NativePlacementSources.run_case`，原方法只呼叫一次並回傳原 CompletedProcess；原20秒 timeout、原斷言與測試輸入均未改。definition／host module 的 native 程序未逐個旁錄。stdout／stderr 是原 `text=True` 解碼結果；binary 只記當時仍存在時的 SHA，未封存 transient ELF。正常回傳 exit0／1 有完整 decoded streams；若原方法因 crash assertion 或 TimeoutExpired 先拋出，旁錄只有例外資訊，不宣稱所有異常均有完整結構串流。

公開資料含原命令／receipt／suite logs、registry sidecars、版本及 protocol；registry sidecars 是外層環境快照，**不是本套隔離 NativeBuild／mutant 的 binary 身分**。隔離 binary 以 protocol 當時 hash 為準。大型 source maps 與 Python recorder 不複製到 repo，公開 receipt 只保留其原 identity；因此不能靠本 payload 重新逐檔驗算完整來源掃描。135份非大型 source-map 原 evidence 已重核 hash；27份 suite logs 由各輪 manifest 宣告且 copied=true。恢復輪不是 run_all，`run_all_logs_complete=null` 與空 suite-log manifest 原樣保留，不借用前輪 logs。

尚未驗：最新整合分支的完整非瀏覽器／六瀏覽器、Windows GDI，以及跨主題合流後驗收。本報告不更動 SSOT，也不處理 #213／#194。發布狀態以主代理另存的 push／PR留言收據為準。
