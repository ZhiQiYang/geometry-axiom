# #323：修復驗證 harness 與失效控制，保存完整固定 SHA 驗收

同一次候選驗證可重用已解析的角材 footprint，仍依每個 consumer 登記正確 dependency kind 與順序。本輪修復新介面下失效的既有 harness／錨點，新增真 `ReferenceEval.member_reads` 身分、失效及跨 consumer 控制，並補上 sealed footprint 命中路徑的守衛。

完整 native、必要八套、完整 PF3、175 場景 A/B/C 與三條架構裁判均在同一受驗 F 完成。**N64 fix/main 為 1.7457212386，未達原 1.3 目標；placement guard 單刪仍為等價 0/0/0。這兩項保留給審查，不宣稱完整驗收全綠。** 沒有改門檻、減守門流量、放寬斷言或刪測試。

## 來源與產物分欄

| 角色 | 完整 SHA |
|---|---|
| 原變更前 base | `546e2eb2142ebf19859489c5391b57cbb8413d10` |
| 固定 main 比較組 | `adbaebf9c73ea6801d7b4d5214e4b846b132923b` |
| 產品／測試 P | `e9fffc1cb036b6e4538a23f4dd12a9e10c5136f9` |
| 帳本實跑來源 S | `b823903e44aea091b70fd2f45b74dff6229776dc` |
| 帳本產物提交 L | `b7ca7843532098c4d3433035cde8dc2c43654978` |
| Linux 架構收據實跑來源 | `b7ca7843532098c4d3433035cde8dc2c43654978` |
| 架構四檔提交 A＝唯一正式受驗 F | `f43e8d8b876f587c11778fa74a80b205b51396b6` |
| 正式證據提交 E（只增證據，不替換 F） | `239040fdc8f0b73b75640378669a1ede6a975890` |
| 修正分支 | `codex/geo261-load-residual-20261020` |
| 正文分支 | `codex/geo261-load-residual-20261020-prbody`，僅 `PR_BODY.md` |

原 PROMPT-B／C 將帳本與架構收據留給維護者。本輪依使用者後續明確授權，由雲端維護者先跑原 `--check`、確認過期後整份重產，再由 Linux 重產 manifest／scan／report／receipt。未改公理層、閱讀器、BACKLOG 或決策佇列，也未放寬架構 policy／exclusion。每項保留真 execution SHA，不把帳本 S、產物 L 或證據 E 手改成 F。

證據入口：[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/tree/239040fdc8f0b73b75640378669a1ede6a975890/tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/PROGRESS.md)、[QUESTIONS.md](https://github.com/ZhiQiYang/geometry-axiom/tree/239040fdc8f0b73b75640378669a1ede6a975890/tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/QUESTIONS.md)、[FORMAL_RECEIPT.json](https://github.com/ZhiQiYang/geometry-axiom/tree/239040fdc8f0b73b75640378669a1ede6a975890/tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/FORMAL_RECEIPT.json)、[FORMAL_METRICS.json](https://github.com/ZhiQiYang/geometry-axiom/tree/239040fdc8f0b73b75640378669a1ede6a975890/tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/FORMAL_METRICS.json)、[PUBLICATION.json](https://github.com/ZhiQiYang/geometry-axiom/tree/239040fdc8f0b73b75640378669a1ede6a975890/tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/PUBLICATION.json)。

## 逐項回覆 PROMPT-C 第 1–5 項

| 要求 | 處理與實跑結果 |
|---|---|
| 1. 兩個既有 harness 編不過 | 既有修正 `221156c280404f75bf3fb5a42fd4c9cf119f7064` 以正確的 `AppValidationInputs` 與雙參數 context 適配，保留原斷言及驗證目的。本輪 F 完整 native：world-validation **14/14**、host-facts **20/20**，原退出均 0；不將繼承修復重報成本輪新產品變更。 |
| 2. PF3 host-identity 錨點 | 同一 `221156c2…` 依 PF3 規則重新對準 `reference_member_anchor_read` 所在的 host-identity 守門。F 上完整跑原工具，非只選 host-identity：baseline **20/20**、19 mutants **全 killed**、restored **20/20**，工具退出 0，errors／skip 0，原來源恢復相同。`test_mutation_anchors` **3/3**。 |
| 3. W feature→collection 與 kind | `221156c2…` 重錨既有 feature-edge；`0af3b7dd1db0a12011ae52c92b442c58e9180218` 補第二 feature 省略依賴、錯 kind 與求值順序控制，逐筆比較完整有序邊。F 上 contact-sources **14/14**；每項真 0/1/0 與原失敗訊息列於下表。 |
| 4. 真 member_reads 失效／跨 consumer | `e9fffc1c…` 補 id 比對、anchor miss 清 footprint、H definition／anchor／footprint／pose 各命中依賴與 kind／order 控制；保留原 7 個方法並新增 5 個，F 上 load-residual **12/12**。placement 單刪在合法生命期內為 **equivalent 0/0/0**；配對控制僅證第二防線，不能稱本要求的每個單刪皆紅，詳 QUESTIONS。 |
| 5. sealed footprint 守衛 | `0af3b7dd…` 加入 `!geo_eval_is_sealed(ctx->sources)`，使已封存且已 VALID 的內部 H 來源讀取走原只讀入口；撤回修正後真 `ASSERT:sealed-contact-facts-remain-readable`，原 0/1/0。未改 K/W sealed 新 query 拒絕政策。 |

PF3 host-identity 正常編譯退出 0，具名測試退出 1、failure 1／error 0／skip 0；原失敗末行為：

```text
+ [[0, 27, 100, 900, True], [27, 273, 10, 20, True], [273, 300, 100, 900, True]] : PF3_HOST_FILTER: a different derived host must remain empty
```

完整 traceback 與前後對照保存在封包成員 `acceptance-r1/evidence/pf3/host-identity/tests/stderr`；完整 19 個結果、build/test 輸出與來源指紋在 `acceptance-r1/evidence/pf3/`。沒有將編譯失敗、crash 或 timeout 算成 killed。

## 固定 F 的正式驗收

全部原 stage 的 source before／after 都是同一 F 且 clean；正式執行時未移動 HEAD。環境為 Linux x86_64、Python **3.12.14**、GCC **14.2.0**、Node **24.19.0**，stack limit **16 MiB**。完整環境與工具指紋逐命令保留；原 native 225/225 suites 全部執行。

| 關卡 | 原退出與結果 |
|---|---|
| `ulimit -s 16384; python3 tests/run_all.py --build` | **0**；225 suites；5193 計數＝5192 pass／0 fail／1 允許 skip |
| 原必要八套 `run_all.py --build --only …` | **0**；674/674，0 fail／skip；suite 明細見下 |
| `python3 tests/pf3_mutation_check.py` 完整工具 | **0**；baseline20／restored20，19 killed |
| A/B/C 原裁判 | **0**；175 場景、350 base/fix 版本組，全部相同 |
| 三方交錯性能原子程序 | 36 筆均 **0**；原 N64 ≤1.3 量化目標未達 |
| base／fix 的 N32／64 四次原 profile | 均 **0**；fix source64/source32＝4.4704196928 ≤4.5 |
| `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | **0**，0 diagnostics |
| `python -B tests/test_architecture_contract.py` | **0**；205/205 |
| `python -B tests/test_product_architecture.py` | **0**；18/18 |
| all 封裝總退出 | **1**，`full_acceptance_passed=false`，原因是 N64 量化目標未達；不是 native 失敗 |

完整 native 原合計列：

```text
合計(已執行、有計數者)                            5193  5192     0     1  1938.1
exit 0：完整非瀏覽器登錄測試：全部 suite 都跑了、數量與 expected 相符、沒有 fail、沒有環境問題、沒有可避免的 skip（具名允許清單不算）；必要正式 owner／瀏覽器整合另驗
```

唯一 skip 是允許清單中的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`，原理由 `requires compiled Windows GDI contract harness`。本環境未做 Windows GDI／MSVC 動態驗證。這份 #323 的 C 驗收範圍是完整 native、PF3、A/B/C 與效能；沒有在此來源跑六個瀏覽器 job，亦不以 #288 的另一來源收據替代。

必要八套原計數：

| suite | pass/total |
|---|---:|
| `c:integrity` | 432/432 |
| `core:run_tests` | 165/165 |
| `py:test_bridge_integrity` | 24/24 |
| `py:test_geo261_assembly_graph_product` | 4/4 |
| `py:test_geo261_candidate_cache` | 18/18 |
| `py:test_geo261_graph_product` | 5/5 |
| `py:test_geo261_load_residual` | 12/12 |
| `py:test_geo261_source_index` | 14/14 |

C 的完整 native 原 stdout 是封包成員 `acceptance-r1/invocations/2026-10-22T234941.1559690000/commands/000971/stdout.bin`，完整 stderr、argv、退出及環境為同目錄原件；逐 suite JSON／unittest log 在 `acceptance-r1/evidence/native-suite-logs/`。`FORMAL_METRICS.json` 是只讀索引，不是替代裁判。

## 新突變與原失敗全文

下列載入控制與 W collection 控制均在 F 的原完整 suite 內重跑。除明列等價的 placement 單刪外，表列控制皆為原 baseline **0** → 突變 **1** → 恢復 **0**；失敗來自正常具名 ASSERT，未以 crash／編譯失敗／timeout 充數。`ordered_cache_edges` 比對原 prefix 與新增依賴的 consumer、來源、kind 及順序，並非只查邊存在。

| 控制 | 原退出 | 原失敗訊息全文 |
|---|---|---|
| H definition 省第二 consumer 依賴（`definition-edge`） | 0/1/0 | `ASSERT:definition-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H definition 錯 kind（`definition-kind`） | 0/1/0 | `ASSERT:definition-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H anchor 省第二 consumer 依賴（`anchor-edge`） | 0/1/0 | `ASSERT:anchor-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H anchor 錯 kind（`anchor-kind`） | 0/1/0 | `ASSERT:anchor-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H footprint 省第二 consumer 依賴（`footprint-edge`） | 0/1/0 | `ASSERT:footprint-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H footprint 錯 kind（`footprint-kind`） | 0/1/0 | `ASSERT:footprint-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H footprint 錯求值順序（`footprint-order`） | 0/1/0 | `ASSERT:footprint-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H pose 省第二 consumer 依賴（`pose-edge`） | 0/1/0 | `ASSERT:pose-cache-second-consumer-edge-and-order line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| H pose kind 寫死（`pose-kind`） | 0/1/0 | `ASSERT:pose-cache-preserves-requested-dependency-kind line=245 expr=ordered_cache_edges(ctx->sources,prefix_count,prefix,consumers,sources,kinds,count)` |
| 同 slot 不同 id，刪 id 比對（`anchor-id-key`） | 0/1/0 | `ASSERT:member-anchor-cache-id-must-match line=75 expr=reference_member_anchor_read(&f->ctx,0,42,&second)&& second.placement_id==8&&second.order==2&&second.uv.v==40&&f->ctx.member_reads[0].id==42` |
| 刪 anchor miss footprint 失效（`anchor-miss-invalidation`） | 0/1/0 | `ASSERT:member-anchor-miss-invalidates-footprint line=94 expr=reference_contact_facts(&f->ctx,f->ctx.sources,&request,after)&& after->member_count==2&&after->members[0].member->id==42&&after->members[0].order==2&&after->members[0].footprint_valid&& after->members[0].footprint.min_v==40&&after->members[0].footprint.max_v==50&& after->members[1].member->id==41&&after->members[1].order==1&&after->members[1].footprint_valid&& after->members[1].footprint.min_v==0&&after->members[1].footprint.max_v==10` |
| placement 單刪（`placement-key-single`） | 0/0/0 | 無失敗；equivalent，不能算 killed |
| placement 配對：先撤 anchor invalidator（`placement-key-paired`） | 0/1/0 | `ASSERT:contact-footprint-cache-placement-must-match line=122 expr=reference_contact_facts(&f->ctx,f->ctx.sources,&request8,after)&& after->member_count==2&&after->members[0].member->id==42&&after->members[0].placement_id==8&&after->members[0].footprint_valid&& after->members[0].footprint.min_v==40&&after->members[0].footprint.max_v==50&&!after->members[1].footprint_valid` |
| W feature→collection 原語意重錨（`feature-edge`） | 0/1/0 | `ASSERT:contact-feature-requires-collection-value` |
| W 第二 feature 省依賴（`second-feature-edge`） | 0/1/0 | `ASSERT:collection-cache-second-feature-edge-and-order` |
| W 第二 feature 錯 dependency kind（`second-feature-kind`） | 0/1/0 | `ASSERT:collection-cache-second-feature-edge-and-order` |
| W feature 求值順序改變（`feature-evaluation-order`） | 0/1/0 | `ASSERT:collection-cache-second-feature-edge-and-order` |
| 撤回 sealed footprint 守衛 | 0/1/0 | `ASSERT:sealed-contact-facts-remain-readable` |

三份原 execution JSONL 分別為封包成員 `acceptance-r1/evidence/native-executions/load-residual.jsonl`、`contact-sources.jsonl`、`host-facts.jsonl`；保存各原 argv、退出與完整 stdout／stderr。host-facts 原記錄 schema 沒有逐行環境／SHA，來源綁定由外層原命令收據及 clean F 保證，沒有事後補造欄位。另有 required-eight 內的 load-residual JSONL；該選集本來沒有執行 host-facts／contact-sources，這兩個檔案不存在不代表 skip 或通過，正式完整 native 的三份原件均存在。

placement 的單故障在合法 immutable canonical graph 生命期內，被 anchor miss 失效覆蓋；不偽填 memo、不擴大生命期製造紅燈。配對 0/1/0 的三個程序都以先撤 anchor invalidator 為前置，只證 placement 的第二防線，**不能證單刪在原產品中非等價**。C 第4項要求「每個單刪皆紅」尚不能如此宣告，已列 QUESTIONS。

既有 `AppFootprintMemo` 的手動失效負控制仍保留，不能冒充真產品 `member_reads` 失效證據。sealed 的 0/1/0 僅證內部 H 對已 VALID 幾何的只讀相容性，不能外推某個公開端面操作曾經失敗；未知 pose 在 sealed 圖中仍拒絕且不新增求值或邊。

## A–F 不變量與快取生命期

- **A：輸出。** 原171個根目錄 scene＋N16/32/48/64＝175；base／fix 各175，**每版75接受、100拒絕**。完整 `loadfile`＋`dump` stdout 逐 bytes 相同，包含錯誤訊息及拒絕場景，不只成功 dump。
- **B：來源圖。** 同批每次 seal 的完整有序 nodes／edges／key bytes／descriptor／state／value 逐筆相同。跨 consumer 命中仍依原 relation 登記依賴及插入位置；同 consumer 重讀不新增重複邊。
- **C：P-177。** 每個 scene／process 的 create、seal、publish、revalidate、`reference_check_all` 五個總呼叫數與 base 相同，**不是每 seal 五計數**。沒有減候選、驗證或 seal。
- **D：失效。** world-validation memo 僅屬同次驗證；ReferenceEval canonical 讀取屬同一求值圖，候選重驗／reset／dispose 重新建立狀態。anchor 命中比對真 id，miss 清 footprint 有效位；footprint 鍵比對 placement；依原 consumer 與 kind 登記邊。保留同候選放置後移動／刪除、參數變更、拒絕回滾與跨 consumer 測試；真 id／miss 失效正常負控及 placement 等價範圍如上。
- **E：API／分層。** 保持公開 API、C11 與固定容量私有資料；K 不 include W/H，W 不 include H。Linux 原架構裁判通過；MSVC 未在此環境動態驗證，不能稱已實跑。
- **F：禁止項。** 本輪不改公理層、閱讀器、BACKLOG、決策佇列。帳本與架構四檔依使用者後續維護者授權重產，policy／roots／route／信任界線未放寬。

A/B/C 的逐場景結果、原 normal／trace stdout／stderr、完整 ordered graphs 與 guards 保存在 `acceptance-r1/evidence/`；原 `equivalence.json` 退出 0，原 audit tuple 相同，trace 未改原輸出。沒有 main A/B/C 比較，不把性能 main 比較混入175組結果。

## 三方交錯性能與原目標

同一 F，N16／32／48／64，每輪原順序 **base→fix→main**，共3輪、36筆；只量 loadfile，不 dump，保留原600秒 timeout，未挑樣本或重抽。量測期間沒有其他編譯、重型封存或測試爭用；每筆原程序退出0。

| N | base median 秒 | fix median 秒 | main median 秒 | fix/main | fix/base |
|---:|---:|---:|---:|---:|---:|
| 16 | 0.200029317 | 0.197496643 | 0.150066502 | 1.316060815 | 0.987338486 |
| 32 | 0.361281229 | 0.301003989 | 0.251693104 | 1.195916711 | 0.833157011 |
| 48 | 0.757308848 | 0.555059024 | 0.399997606 | 1.387655865 | 0.732936140 |
| 64 | 1.555082622 | 1.062526359 | 0.608646063 | 1.745721239 | 0.683260390 |
| 原目標 | 實測 |
|---|---|
| N64 fix/main ≤1.3 | **1.7457212386，未達** |
| fix `geo_eval_source` N64/N32 ≤4.5 | **4.4704196928，達到** |
| N16/32/48 相對 base 不變慢 | 三點 fix/base＝0.987338486／0.833157011／0.732936140，均達到 |
| 封裝總判決 | 退出 **1**，未全達標；各原執行 stage 退出均0 |

PROMPT-B 明列「量化目標(以維護者的 WSL 重測為準，你那邊的機器只作參考)」，並要求「沒做到的目標要照實寫」。本輪 C 要求同法重跑，已完整交付雲端實數；不把未達寫成通過、不將 #288 的2×移作本題門檻，也不請使用者電腦替跑。handoff 將剩餘效能熱點留給後續 #300，這裡保留原目標及未達項供複審。

## 原 gprof 呼叫數

原 `-O1 -fno-inline -pg`，base／fix 各跑 N32／N64 一次，四次程序退出0；不是 O2 性能樣本，也沒有 main profile。

| 函式 | base32 | base64 | fix32 | fix64 |
|---|---:|---:|---:|---:|
| `geo_eval_source` | 450,098 | 2,980,967 | 80,273 | 358,854 |
| `geo_eval_depend` | 無 flat 呼叫記錄 | 無 flat 呼叫記錄 | 276,844 | 1,968,612 |
| `wd_read` | 5,922,136 | 43,503,376 | 99,024 | 370,680 |
| `contact_order` | 354,308 | 2,729,508 | 354,308 | 2,729,508 |
| `wood_contact_collect_stops` | 3,438 | 12,942 | 3,438 | 12,942 |
| `app_reference_member_footprint` | 19,029 | 141,429 | 1,146 | 4,314 |

base 的 `geo_eval_depend` 原 flat profile 沒有對應呼叫行；工具按原規則記0，這裡明標無記錄，不能據此宣稱實際沒有呼叫。六個符號、原 gprof matched lines、缺行清單、gmon 與完整 profile 輸出均封存。fix64 尚有 `contact_order` 2,729,508、`geo_eval_depend` 1,968,612 次；這些是保留的殘餘熱點，未藉省守門流量處理。

## 完整帳本及 Linux 架構四檔

原 S 上 `python3 tests/mutate.py --check` 退出 **1**（75 stale＋3 retired），故整份執行 `python3 tests/mutate.py`，退出 **0**，隨後原 `--check` 退出 **0**，外層收據退出0；S 前後 clean。78 records＝**70 killed＋M20 crashed＋4 equivalent＋3 retired**，75筆新 execution.head 全為 S，stale／survived／invalid／blocked 皆0。歷史 M20 的三次 SIGSEGV 如實為 crashed，不改稱 killed。安裝 ledger 之後，正式 F native 的 `mutation:check` 原綠。

Linux 在 L 實跑三條原架構裁判並重產 manifest／scan／report／receipt，產物提交 A＝F；manifest bytes 不變。原結果：601 executable、333 owned、268 excluded、796 edges、0 diagnostics，918 forbidden identifiers／55 strings；F 又獨立重跑原三條 0/0/0。未以新 exclusion 躲過來源。

先前完整帳本 primary 收據與架構重產 raw 分別在同證據根目錄的 `ledger-b823903e/`、`architecture-b7ca7843/`；本次完整帳本補充稽核位於正式目錄 `ledger-audit/`。帳本原工具未落盤 core 內層各 attempt／compiler 的完整 streams；完整 top-level 原命令 stdout／stderr、structured cases 與原 stream hashes 均保存。75份 mutant C 為**重建後逐一吻合原編譯指紋**，不是原捕獲，不能說每個內層原 stdout 都已封存。

## 證據封存及未執行範圍

正式兩個封包共 **11,089 members／106,672,856 raw bytes**，每個 member 均解包核對 path／bytes／SHA-256；另有帳本補充稽核743 members。`PUBLICATION.json`、各 `inventories/*.members.json` 與 `SHA256SUMS` 可定位原件。Git archive stdout tar 原樣保留；可重建 checkout、ELF 等排除項另存 metadata／hash，未將其冒充原輸出。封存只整理已有結果，沒有重跑或改寫裁判。

本輪未執行 Windows GDI、MSVC，亦未把 #288 在 F2 的六個 browser job 算成本 #323 的證據。既有 GitHub Actions 計費失敗不算測試；GitHub API不可用，因此沒有宣稱已更新線上 PR 正文。

## 最不確定的地方

1. **性能尚未達原 N64 1.3×目標。** 雲端固定 F 原量測為1.7457212386；三方樣本完整保留。它可證本環境結果，不能冒作維護者 WSL 數字或保證容量512可接受。
2. **placement 單刪為等價。** 配對控制只證第二防線，尚不能滿足 C 原文「每個單刪皆紅」的字面要求；請審查是否接受此等價分類。若要改產品生命期或公理語意製造可達故障，須另決定，本輪不代決。
3. **sealed 保證範圍。** 只涵蓋內部 H 對已 VALID 來源的只讀行為；不外推公開操作或改動 sealed 新 query 政策。
4. **跨平台與原工具捕獲限制。** Linux 原裁判已跑，MSVC／Windows GDI 未動態驗證；core ledger 內層未落盤的 streams 不能由事後重建補稱原捕獲。

請使用者將此檔貼至 **PR #323 正文**並請複審，連同 QUESTIONS 的兩個未滿足項一併判讀。修正及 prbody 分支都以一般 push 保存；不 force push、不合併，也不把本分支合入 #288。#288 進 main 後再依既定流程處理 base。
