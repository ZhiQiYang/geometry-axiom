GEO-261 在每行候選驗證中反覆解析同一支角材的 footprint、放置定義與姿態。本修正保留所有候選、驗證、收據與 seal，重用同次驗證的成功讀取，並為不同 consumer 補記原本的依賴。

**效能目標部分達成**：`geo_eval_source` N64／N32 為 **4.470× ≤ 4.5×**；N16／32／48 均快於基底。此雲端 N64 fix／main 為 **1.78×，未達 ≤1.3×**。未更改守門流量來降低成本。

基底分支必須設為 **`architecture/geo261-integration-20261016`**，基底 `546e2eb2142ebf19859489c5391b57cbb8413d10`；修正分支 `codex/geo261-load-residual-20261020`。產品碼與測試提交 `221156c280404f75bf3fb5a42fd4c9cf119f7064`，之後只附證據。此正文獨立放在 `codex/geo261-load-residual-20261020-prbody`，該分支整棵 tree 只有 `PR_BODY.md`，未放入修正分支。請維護者在本機建立 **draft PR**；本環境不呼叫 GitHub API、不合併。

修正分支最終 head：`f3ea9c5232c043b3dca57b953577f5d22e9030e7`；其產品碼與測試內容和受驗提交相同，後續提交只含證據。

## 改動與不變量

1. `reference_check_all` 與 `app_validation_footprint` 使用各自單次驗證的固定容量快取；鍵包含材索引與 placement。只在第一次真正需要時求值，失敗不快取。W 驗證的 host 讀取也僅在同次呼叫重用，仍依各 footprint 選擇邊界。
2. `ReferenceEval` 保存成功解碼的材定義、放置定義、姿態與擋面所用的投影。命中仍依原呼叫順序執行 `geo_eval_depend`，使用同一 source key 與 dependency kind；不將某個 consumer 的已讀紀錄當成其他 consumer 的已讀紀錄。失敗仍走原本求值與診斷分支；sealed 的定義／姿態讀取走原入口。
3. W contact feature 重用自己 query 已成功持有、不可變的 collection bytes；使用節點索引提示前先核對完整來源鍵、VALID 狀態與值，reset／重新註冊或提示失配時仍走原求值。仍記錄 feature → collection 的依賴，再執行原本的格式與範圍檢查。尚未成功的 collection 保留原求值路徑。
4. 沒有改 `contact_order`、擋面排序／去重、參與者或 D11 先放者順序。

逐條對應硬性不變量：

- **A，輸出**：基底與修正以指定 C11／O2 指令建置，175 份輸入逐位元組相同，包含拒絕場景的 stdout；檢測建置也必須與各自未檢測的 bridge stdout／stderr 相同。原始輸出完整保存。
- **B，來源圖**：暫時在每次 `geo_eval_seal` 入口，透過 `geo_eval_node_at`／`geo_eval_edge_at` 序列化全部欄位、key bytes、descriptor、狀態、值內容與邊。175 份輸入的完整二進位序列與順序皆相同，未只比最終 dump 或雜湊。首次讀取保留原求值順序；同 consumer 的重讀不增加新邊；不同 consumer 命中快取仍登記依賴。
- **C，守門流量**：五個函式入口的計數逐份完全一致。未跳過任何驗證、候選、發布或 seal。`wood_contact_collect_stops` 的呼叫數也與基底一致，詳見下表。
- **D，失效**：兩個迴圈快取在每次驗證開始 `begin` 清空，生命期止於該函式返回。來源解碼快取隨 `ReferenceEval` 生命期；候選每次重驗先銷毀原求值狀態並 reset 來源圖，再建立新的零初始化 `ReferenceEval`。dispose 亦清空快取。query 的 collection 只屬於該 query 與該求值圖，不跨重建。測試在同一 `AppWorldCandidate.after` 放材後移動／刪除、修改真正的參數欄位、拒絕改動後核對整份 World 回滾，並重用快取儲存驗證 begin 的失效規則。
- **E，API 與分層**：未修改任何公開 header，使用 C11 與固定容量資料，沒有平台加速或新增 `_Static_assert`；新增型別及函式皆私有。K kernel 沒有改動；W 只修改自身 contact provider，沒有 include H。`geometry-core/references.inc` 是原有 H 相容轉接，沿用既有分層。此環境只有 GCC，未實跑 MSVC。

未修改禁止項目：突變帳本、domain-decoupling 架構清單／收據、公理與閱讀器、BACKLOG／決策佇列。Actions 的計費失敗不列為驗收，也未為此改配置。

## 驗收 A／B／C

先設 `ulimit -s 16384`。基底及修正分別：

```sh
gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm
printf 'loadfile %s\ndump\n' X.scene | ./bridge
```

批次重現（`verify.py.txt` 複製成 `/tmp/geo261-residual-tools.py`；所有 subprocess 設 stack 16 MiB）：

```sh
git worktree add --detach /tmp/geo261-residual-base 546e2eb2142ebf19859489c5391b57cbb8413d10
git worktree add --detach /tmp/geo261-source-main adbaebf9c73ea6801d7b4d5214e4b846b132923b
python3 /tmp/geo261-residual-tools.py build /tmp/geo261-residual-base /tmp/geo261-residual/base
python3 /tmp/geo261-residual-tools.py build "$PWD" /tmp/geo261-residual/fix
python3 /tmp/geo261-residual-tools.py build /tmp/geo261-source-main /tmp/geo261-residual/main
python3 /tmp/geo261-residual-tools.py build /tmp/geo261-residual-base /tmp/geo261-residual/base-trace --trace
python3 /tmp/geo261-residual-tools.py build "$PWD" /tmp/geo261-residual/fix-trace --trace
python3 /tmp/geo261-residual-tools.py compare "$PWD" /tmp/geo261-residual --evidence "$PWD/tests/evidence/geo261-load-residual-20261020"
```

全部建置及比對結束碼 **0**。最後輸出：

```text
PASS A/B/C: 175 scenes; byte-identical stdout, full ordered graphs at every seal, all five guard counts
```

175 = 根目錄 171 份 `.scene` + 產生器四份。每份的指令、結束碼、stdout bytes／SHA-256、完整圖 bytes／SHA-256 及五個計數都在 `equivalence.json`；對應原始資料在 `stdout/` 與 `graphs/`。

四份量測場景的 base／fix 五個計數如下（相同）：

| N | create | seal | publish | revalidate | reference_check_all |
|---|---:|---:|---:|---:|---:|
| 16 | 4 | 4 | 4 | 0 | 26 |
| 32 | 4 | 4 | 4 | 0 | 42 |
| 48 | 4 | 4 | 4 | 0 | 58 |
| 64 | 4 | 4 | 4 | 0 | 74 |


## 效能與 gprof

同一雲端 Linux／GCC 14.2、16 MiB stack，以 `time.perf_counter()` 計整個 bridge 行程的 `loadfile`，不含 dump。每個 N 依 base → fix → main 交錯三輪，全部載入 exit 0 且 `ok:true`；原始 36 筆數值與 stdout／stderr 完整保留。此環境資料供參考，WSL 結果由維護者重測。

```sh
python3 /tmp/geo261-residual-tools.py perf "$PWD" /tmp/geo261-residual --evidence "$PWD/tests/evidence/geo261-load-residual-20261020"
```

結束碼 **0**，中位數：

| N | base（秒） | fix（秒） | main（秒） | fix／main | fix／base |
|---|---:|---:|---:|---:|---:|
| 16 | 0.2026 | 0.1854 | 0.1752 | 1.06× | 0.91× |
| 32 | 0.4513 | 0.3537 | 0.2846 | 1.24× | 0.78× |
| 48 | 0.9770 | 0.7407 | 0.4433 | 1.67× | 0.76× |
| 64 | 1.9530 | 1.2944 | 0.7292 | 1.78× | 0.66× |


N64 未達 1.3×。以下 gprof 呼叫數亦說明依賴登記仍有成本：成功值命中改用 `geo_eval_depend`，所以來源求值減少不等於所有圖操作都變成二次成長，不能據此宣稱已解決 512 支容量問題。

```sh
gcc -std=c11 -O1 -fno-inline -pg geometry-web/web_bridge.c -o /tmp/geo261-residual/fix-pg/bridge -lm
ulimit -s 16384
cd /tmp
printf 'loadfile /tmp/s32.scene\n' | /tmp/geo261-residual/fix-pg/bridge
gprof /tmp/geo261-residual/fix-pg/bridge gmon.out
printf 'loadfile /tmp/s64.scene\n' | /tmp/geo261-residual/fix-pg/bridge
gprof /tmp/geo261-residual/fix-pg/bridge gmon.out
```

基底同樣以 `base-pg/bridge` 執行。編譯、載入、gprof 結束碼均 **0**，載入 `ok:true`。

| 函式 | base N32 | base N64 | base 倍數 | fix N32 | fix N64 | fix 倍數 |
|---|---:|---:|---:|---:|---:|---:|
| `geo_eval_source` | 450,098 | 2,980,967 | 6.62× | 80,273 | 358,854 | 4.47× |
| `geo_eval_depend` | 0 | 0 | — | 276,844 | 1,968,612 | 7.11× |
| `wd_read` | 5,922,136 | 43,503,376 | 7.35× | 99,024 | 370,680 | 3.74× |
| `contact_order` | 354,308 | 2,729,508 | 7.70× | 354,308 | 2,729,508 | 7.70× |
| `wood_contact_collect_stops` | 3,438 | 12,942 | 3.76× | 3,438 | 12,942 | 3.76× |
| `app_reference_member_footprint` | 19,029 | 141,429 | 7.43× | 1,146 | 4,314 | 3.76× |


修正 N64 flat profile 原始前段如下；0.01 秒取樣比例只作線索，四份完整 gprof stdout 與逐項結束碼另存於證據目錄。base 的 `geo_eval_depend` 無呼叫紀錄，以 0 呈現。

```text
Flat profile:

Each sample counts as 0.01 seconds.
  %   cumulative   self              self     total           
 time   seconds   seconds    calls  ms/call  ms/call  name    
 14.29      0.05     0.05    12942     0.00     0.01  wood_contact_collect_stops
 11.43      0.09     0.04  2729508     0.00     0.00  contact_order
  7.14      0.12     0.03  5253317     0.00     0.00  geo_source_edge_hash
  5.71      0.14     0.02  2327466     0.00     0.00  geo_source_edge
  5.71      0.16     0.02  1638811     0.00     0.00  geo_source_find_edge
  5.71      0.18     0.02   118130     0.00     0.00  app_member_reference_at
  5.71      0.20     0.02    19413     0.00     0.00  reference_contact_facts
  2.86      0.21     0.01 21540561     0.00     0.00  geo_source_hash_size
  2.86      0.22     0.01  2327466     0.00     0.00  geo_source_find_node
  2.86      0.23     0.01  1769857     0.00     0.00  geo_source_index_append
  2.86      0.24     0.01  1281504     0.00     0.00  wood_contact_source_read_u32
```

## 測試、突變與架構

```sh
ulimit -s 16384
python3 tests/run_all.py --build --only py:test_geo261_source_index --only py:test_geo261_candidate_cache --only py:test_geo261_graph_product --only py:test_geo261_assembly_graph_product --only py:test_bridge_integrity --only c:integrity --only core:run_tests --only py:test_geo261_load_residual
```

結束碼 **0**；8 suites，669 個登錄測試／檢查點全部通過（含 C integrity 432、core 165、bridge integrity 24、assembly graph 4、candidate cache 18、graph product 5、source index 14、新增 7）。名稱由 `run_all.py --list` 核對，與要求相同。新 suite 已登記，expected 計數為 7。部分執行不冒充完整驗收。

```sh
python3 tests/test_geo261_load_residual.py
```

結束碼 **0**，7 tests 通過。兩種要求的突變與集合節點有效性的第三種突變分開編譯；必須先有未突變成功對照，突變以正常結束碼 1 及具名斷言失敗，再確認原版通過；崩潰、編譯錯誤或逾時均不算偵測。實際 stderr 摘要：

```text
ASSERT:stale-footprint-after-move ...
ASSERT:stale-footprint-after-parameter ...
ASSERT:cross-consumer-placement-edge-missing ...
ASSERT:reset-collection-must-be-evaluated ...
```

永不失效突變移除 `app_footprint_memo_begin` 的 valid 清除，測試重用同一儲存使過期值可確定性重現；跨 consumer 突變保留快取值但省略命中的依賴登記，第二個 consumer 的邊檢查轉紅。另以真實 W API 測 query 物件跨 reset／重新註冊：節點位置改變與已 describe 但尚未求值均保持原順序；第三種突變省略節點有效性驗證，該測試轉紅。完整斷言與行號見 `checks/native.stdout`，未改突變帳本。

```sh
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer tests/geo261_load_residual_harness.c -o /tmp/geo261-residual-sanitizer -lm
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/geo261-residual-sanitizer move-delete
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/geo261-residual-sanitizer parameter
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/geo261-residual-sanitizer consumers
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 /tmp/geo261-residual-sanitizer collection-reset
```

編譯及四個案例結束碼均 **0**，各有 `PASS ...`，沒有 sanitizer 診斷。拒絕案例的原有 DSL 錯誤訊息另保留在 stderr。

```sh
python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
```

基底／修正結束碼均 **0**，JSON `diagnostics: []`。這份新基底已沒有上一輪未登記 `gen_scenes.py` 的診斷；本次未改 manifest。兩份完整 JSON 在 `checks/architecture-*.stdout`。

完整 `python3 -u tests/run_all.py --build` 結束碼 **1**。原始 stdout／stderr 與起訖時間均在 `checks/full.*`。摘要：

```text
[3/225] mutation:check …
[164/225] py:test_product_architecture …
mutation:check                                       -     -  FAIL     -     0.7  mutation inventory freshness (not test assertions); exit 1；日誌 /tmp/geometry-tests/run_all-logs/mutation_check.log
py:test_product_architecture                        18    18     0     0    12.2
合計(已執行、有計數者)                            5183  5181     1     1  2187.7
  mutation:check
exit 1：有 fail／逾時／預期數不符／未登記檔
```

225 個 suite 全部執行完畢，只有兩個 suite 未過：`mutation:check` 是既有突變帳本因 include 閉包變更而過期，依要求留給維護者重產；`py:test_assembly_mutation_check` 是下述可在基底重現的 zombie 清理問題。其餘 suite 沒有失敗，包含已補正的四組測試與 18 個 product architecture tests。Windows GDI 的 1 項 skip 在既有具名允許清單內；獨立 browser／owner 整合仍未執行。


另外，`py:test_assembly_mutation_check` 的程序群清理案例在此容器失敗：被 SIGKILL 的 `sleep` 留在 `/proc`，狀態為 Z（zombie）。在基底與修正版各直接執行 `python3 tests/test_assembly_mutation_check.py`，均 exit 1、12 tests 中同一項失敗；兩支相關測試／工具檔與基底無差異。原始輸出與結束碼保存於 `checks/assembly-process-base.*`、`checks/assembly-process-fix.*`。這項環境清理失敗保持紅燈，未修改測試或程序管理規則來排除它。

完整跑曾找出四組測試適配：兩支 harness 需接收新的私有 `AppValidationInputs`，contact feature 與 PF3 host-identity 的負控制需重設到實際執行的錨點。保留原斷言與錯誤類別後，四個 suite 複跑 **46 tests 全過**；指令／exit 0 見 `checks/test-adapters.*`。重設後的 PF3 host-identity 另以原工具執行完整基準 20 tests、單一突變指定 `PF3_HOST_FILTER` 失敗（exit 1、1 failure、無 error／skip）、完整恢復 20 tests 通過；整體工具 exit 0，來源未變。這份收據是在此 Linux 執行，未冒充 WSL 收據，保存於 `pf3-host-identity/`。

```sh
python3 tests/run_all.py --only py:test_geo261_host_facts_authority --only py:test_geo261_wood_world_validation --only py:test_geo261_contact_sources --only py:test_mutation_anchors
python3 tests/evidence/geo261-load-residual-20261020/pf3_control.py.txt
```

適配前那次完整結果（5183、5160 pass／22 fail／1 skip，exit 1）完整保留在 `checks/full-before-test-adapters.*`；最終完整重跑另列於上方，不混用通過數。

第一次完整測試因複查補上 reset 邊界回歸而主動中止（exit -15），保留於 `checks/full-interrupted.*`，不列作最終驗收；後續完整測試重新由頭執行。

## 證據與未驗項目

全部證據位於 [tests/evidence/geo261-load-residual-20261020/](https://github.com/ZhiQiYang/geometry-axiom/tree/codex/geo261-load-residual-20261020/tests/evidence/geo261-load-residual-20261020)，包含 README、可重跑的 `.py.txt` 腳本、受驗 SHA、環境、原始輸出、指令與結束碼。新增測試本身依既有 registry 使用 `.py`，證據腳本均以 `.py.txt` 存放。

未實跑 Windows／MSVC、維護者 WSL 及 run_all.py 明列獨立執行的 browser／owner 整合。沒有以 Actions 計費失敗作紅燈或綠燈。

## 最不確定的地方

- N64 fix／main 仍為 1.78×；此修正只降低同次驗證的重複讀取，依賴邊登記與既有擋面成本仍在，不能承諾 512 支的成長率。
- 同 consumer 的重用依賴目前驗證函式期間不修改 World 的契約；若將來在驗證中加入修改或將快取延長生命期，必須重設失效邊界並重跑完整圖比對。
- 本機只驗 GCC／ASan／UBSan；MSVC 與 WSL 效能仍待維護者確認。
