# GEO-261 來源圖索引驗收（2026-10-20）

量測與測試的產品 commit：`0636a0867556cf5ade397e995b5a93f53fba7a4b`。
後續 commit 僅調整測試哨兵的位元組複製及驗收證據；產品碼與已測版本相同。
`9f21280d` 另增加對照測試（見下方「對照突變補強」，測試數 7 → 14）；`geometry-core/` 與 `0636a086` 零差異（`git diff --stat 0636a086 9f21280d -- geometry-core/` 輸出為空，`source.c` blob 皆為 `634b9cf92b9164316c6ea878a01dfaa8b628e15c`）。

- base：`3e600772076465fc65a26ac09055028301c0fb0b`
- main：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`
- 環境：Linux x86_64，Intel Xeon Platinum 8573C，GCC 14.2.0，stack 16 MiB。
- 時間採 `perf_counter`，包含 bridge 行程啟停及 `loadfile`；效能樣本不含 `dump`，每次新建 bridge 行程。
- 量測時沒有並行執行測試或其他建置；三版本每輪輪換順序，各取三次中位數，所有樣本均保留。

詳細語意說明、A–D 的指令／結束碼／輸出摘要、效能表、突變結果與最不確定處，見獨立分支的 [PR_BODY.md](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-source-index-20261020-prbody/PR_BODY.md)。該分支僅包含這一個檔案，正文不放入修正分支。

| 證據 | 內容 |
|---|---|
| [measure.py](measure.py)、[mini_gen.py](mini_gen.py) | 可重跑的 A／B 腳本與任務提供的產生器 |
| [measurements.json](measurements.json) | 三版本編譯指令／SHA、八次等價性 stdout 指紋、36 次原始效能樣本、各次結束碼與輸出 |
| [measure.log](measure.log) | A／B 執行輸出；整支腳本結束碼 0 |
| [commands.json](commands.json) | 其餘驗收命令、工作目錄、結束碼與耗時；執行前設定 stack 16 MiB |
| [required.log](required.log) | 指定 7 個 suite：655／655 通過，結束碼 0。這是 `0636a086`／`af317822` 當時的收據，其中 source index suite 仍是 7 項；`9f21280d` 之後該 suite 為 14 項，7 個 suite 的合併計數未重跑（只重跑了有改動的 suite，見下節） |
| [source-index.log](source-index.log) | **歷史收據**：`af317822` 當時的 7／7 通過，包含兩個結束碼 1 的重複斷言突變。現行 14／14 見下節的 `controls-*` 收據 |
| `sanitizer-*.log` | ASan／UBSan 編譯與五組案例，全部結束碼 0，沒有 sanitizer 診斷 |
| [architecture-base.log](architecture-base.log)、[architecture-fix.log](architecture-fix.log) | 皆結束碼 1；`cmp` 結束碼 0、輸出空，只有同一個既有未登記來源診斷 |
| [gprof-summary.log](gprof-summary.log)、[profile-load.log](profile-load.log) | 新版 N=48 profile；編譯、載入、gprof 結束碼皆 0 |
| [full.log](full.log) | 完整 224 suite 結束碼 1；5,130 pass、18 個既有架構 setup 阻擋、1 個 Windows GDI 具名平台 skip；另有未計數的突變帳本 stale 紅燈 |
| `product-architecture-{base,fix}.{json,log}` | base／fix 均有相同的 18 個架構 setup 阻擋，runner 結束碼皆 1 |
| [mutation-base.log](mutation-base.log)、[mutation-fix.log](mutation-fix.log) | 只讀帳本檢查皆結束碼 1；base 18 筆 stale、fix 75 筆 stale，未重產帳本 |

## 對照突變補強（`9f21280d`，source index suite 14／14）

PR #321 的審查指出：原本只有「node／edge 查找永遠查不到」兩個突變，edge 在索引路徑上也沒有強制碰撞，漏比 kind 之類的錯只能碰運氣抓到。`9f21280d` 只動三個測試檔（`tests/geo261_source_index_harness.c`、`tests/test_geo261_source_index.py`、`tests/run_all.expected.json`），沒有動 `source.c`、`tests/mutants_results.json`、架構清單。

- **受驗 commit**：`9f21280d0481c751f246b0c2105d50eea75b7ba9`（`codex/geo261-source-index-20261020`）。整合分支 head `96ade86bdb5fbcdad581b36afdd180a96fca7999` 包含它，且 `geometry-core/kernel/source.c`、`tests/geo261_source_index_harness.c`、`tests/test_geo261_source_index.py` 三個檔案在兩個 commit 逐位元組相同：`git diff --stat 9f21280d 96ade86b -- <三個檔案>` 輸出為空、結束碼 0，blob 雜湊並列見 [controls-identity.log](controls-identity.log)。
- **環境**：WSL Ubuntu-24.04，系統 gcc（`-std=c11 -O0`，版本未另行記錄），`ulimit -s 16384`。因 Windows 的 Smart App Control 會擋新編 exe，C 的編譯與執行都在 WSL 的 ext4 乾淨 clone（`/var/tmp/srcidx-ctl-20261020-final`）上，並經過共用的 WSL 鎖。
- **指令與結果**（`git status --porcelain` 前後皆為空）：
  - `python3 tests/test_geo261_source_index.py`：`Ran 14 tests in 61.576s`、`OK`，結束碼 0。
  - `python3 tests/run_all.py --build --only py:test_geo261_source_index`：測試數 14、pass 14、fail 0、skip 0，結束碼 0；這是 `--only` 局部執行，不是完整驗收。
- **測試 14 項** = 原有 5 個行為案例（nodes、edges、allocation、growth、statuses）+ 新案例 `edge-collisions`（1）+ 兩個既有的 never-find 突變 + 6 個新突變。`tests/run_all.expected.json` 該 suite 計數 7 → 14。
- 每個突變都在真實 `source.c` 上以單行唯一錨點注入（錨點不唯一或不存在時測試直接失敗），流程是「基準先過 → 編入突變 → 必須以具名斷言結束碼 1 失敗、stdout 空 → 基準再過」；編譯錯誤、崩潰、逾時都不算偵測成功。

| 突變 | 改法 | 驗證案例 | 失敗訊息原文（[controls-unittest.log](controls-unittest.log)） |
|---|---|---|---|
| `never-node`（既有） | `geo_source_find_node` 永遠回 `SIZE_MAX` | nodes | `ASSERT:duplicate-node line=143 expr=geo_eval_node_count(ctx)<=oracle_node_count` |
| `never-edge`（既有） | `geo_source_find_edge` 永遠回 `false` | edges | `ASSERT:duplicate-edge line=174 expr=geo_eval_edge_count(ctx)==oracle_edge_count` |
| `node-key-bytes-ignored` | node 相等只比 provider 與 key_size，不比 key bytes | nodes | `ASSERT:merged-node line=142 expr=geo_eval_node_count(ctx)>=oracle_node_count` |
| `node-probe-miss` | 起始槽被別的鍵占用就當作沒找到 | nodes | `ASSERT:duplicate-node line=146 expr=geo_eval_node_count(ctx)==oracle_node_count` |
| `node-probe-hit` | 起始槽有人就當作找到、不驗鍵 | nodes | `ASSERT:merged-node line=142 expr=geo_eval_node_count(ctx)>=oracle_node_count` |
| `edge-kind-ignored` | edge 相等漏比 kind | edge-collisions | `ASSERT:missing-edge line=224 expr=geo_eval_edge_count(ctx)>=oracle_edge_count` |
| `edge-probe-miss` | 起始槽被別的邊占用就當作沒找到 | edge-collisions | `ASSERT:duplicate-edge line=225 expr=geo_eval_edge_count(ctx)<=oracle_edge_count` |
| `edge-probe-hit` | 起始槽有邊就當作找到、不驗邊 | edge-collisions | `ASSERT:missing-edge line=224 expr=geo_eval_edge_count(ctx)>=oracle_edge_count` |

`edge-collisions` 案例未突變時為綠燈（測試 `test_forced_edge_collisions_deduplicate_each_field_in_linear_order ... ok`，內部要求 stdout 恰為 `PASS edge-collisions`；開發 clone 上也單獨執行過，結束碼 0）。它的鍵是寫死的：

- `edge_group`：32 條 (consumer, source, kind) 邊，邊雜湊的低 12 位全是 1（`& 4095 == 4095`），所以邊索引從 16 槽起的每次倍增，它們的起始槽都相同。
- `edge_pairs`：8 組 consumer、source 相同、只差 kind 且起始槽相同的邊對，槽不等於 4095。
- 執行時每個鍵都用被測的 `geo_source_edge_hash` 複驗（失敗標籤 `edge-collision-precondition`），雜湊函式一改案例會當場失敗，不會悄悄失去牙齒；`client edge-search` 用被測雜湊重印同一份表。
- 找法：只用前 512 個 refs 當節點，consumer、source 取真實節點序號且不相等；依 consumer、source 由小到大、kind 由 0 到 2 掃描；前 32 個符合條件的三元組是 group（空間內共 194 個），前 8 組同槽的 kind 對是 pairs（空間內共 13 組）。C 的 `edge-search` 輸出、獨立重寫雜湊的 Python 搜尋結果、harness 內寫死的表三者一致（[controls-edge-fixture-crosscheck.log](controls-edge-fixture-crosscheck.log)，腳本副本 [controls-crosscheck-script.py.txt](controls-crosscheck-script.py.txt)、[controls-independent-hash-search-script.py.txt](controls-independent-hash-search-script.py.txt)）。
- 夾具本身也做過突變（[controls-fixture-variants.log](controls-fixture-variants.log)）：只留 group 時 `edge-kind-ignored` 存活（結束碼 0），所以 kind 對才是它的牙齒；只留 pairs 時三個 edge 突變都被抓到；兩者都不留時基準本身以 `edge-index-in-use` 失敗。
- 偵測矩陣（[controls-detection-matrix.log](controls-detection-matrix.log)）：舊的 `edges` 案例今天也殺得掉三個 edge 突變，但它沒有強制碰撞（推測是早期小表剛好碰撞，未逐一追查），標籤也只是籠統的 `duplicate-edge`；新案例用寫死的同槽鍵讓偵測不再依賴這種偶然，並給出 `missing-edge`／`duplicate-edge` 的病因標籤。

`controls-*` 證據檔：

| 證據 | 內容 |
|---|---|
| [controls-session.log](controls-session.log) | 乾淨 clone 驗收腳本的完整輸出：`HEAD=`、前後 `git status`、兩個指令的結束碼與起訖時間（含取鎖等待訊息，原樣保留） |
| [controls-unittest.log](controls-unittest.log)、[controls-run_all.log](controls-run_all.log) | 上述兩個指令各自的原始輸出，與 WSL 內的原檔 `cmp` 位元組相同 |
| [controls-identity.log](controls-identity.log) | `9f21280d` 與 `96ade86b` 的受驗檔同一性（diff 輸出為空、blob 雜湊並列、`run_all.expected.json` 該項皆為 14） |
| [controls-edge-fixture-crosscheck.log](controls-edge-fixture-crosscheck.log) | 開發 clone（受驗檔 blob 雜湊與 `9f21280d` 相同）上的獨立編譯、六個基準案例各自 `PASS`、`edge-search` 與交叉比對。檔尾的偵測矩陣段因實驗腳本把突變 exe 與目錄取成同名而失敗（與被測碼無關），已修腳本並於下一份日誌重跑 |
| [controls-detection-matrix.log](controls-detection-matrix.log) | 8 個突變 × 6 個案例的偵測矩陣（腳本副本 [controls-matrix-script.py.txt](controls-matrix-script.py.txt)） |
| [controls-fixture-variants.log](controls-fixture-variants.log) | 夾具突變實驗，在受驗 commit 的乾淨 clone 上執行（腳本副本 [controls-variants-script.py.txt](controls-variants-script.py.txt)） |
| [commands.json](commands.json) 的 `controls-*` 項 | 上述每一步的指令、工作目錄、結束碼。腳本副本以 `.py.txt` 存放，避免被當成可執行來源登記；使用時複製成 `.py` |

**完整測試的兩項紅燈尚未關閉**：[full.log](full.log) 的完整 224 suite 結束碼 1，紅燈只有兩項：
1. `mutation:check`：突變帳本過期（include 閉包內有檔案已變；base 18 筆、fix 75 筆 stale，見 [mutation-base.log](mutation-base.log)、[mutation-fix.log](mutation-fix.log)）。
2. `py:test_product_architecture`：`geometry-core/framing-template/core-probe/gen_scenes.py` 在完整清單中未登記（`SOURCE_UNREGISTERED`），setUpClass 錯誤使該 suite 的 18 個測試未執行；base 同樣存在，見 [product-architecture-base.log](product-architecture-base.log)、[product-architecture-fix.log](product-architecture-fix.log)。

這兩項不是本次對照測試造成的，也沒有在本 PR 處理；`9f21280d` 之後沒有重跑完整 224 suite。依分工由維護者在整合分支的最終 SHA 上關閉：突變帳本整份重產、架構收據重產。本證據 commit 沒有改任何 `.py`，不會改變帳本的過期狀態。

重跑 A／B（請在沒有其他測試或建置執行時量測）：

```sh
git worktree add --detach /tmp/geo261-source-base 3e600772076465fc65a26ac09055028301c0fb0b
git worktree add --detach /tmp/geo261-source-main adbaebf9c73ea6801d7b4d5214e4b846b132923b
python3 -u tests/evidence/geo261-source-index-20261020/measure.py \
  /tmp/geo261-source-base "$PWD" /tmp/geo261-source-main /tmp/geo261-source-measure
```

重跑 sanitizer：

```sh
mkdir -p /tmp/geo261-source-checks
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I geometry-core/kernel tests/geo261_source_index_harness.c \
  -o /tmp/geo261-source-checks/source-index-sanitized
for case in nodes edges allocation growth statuses; do
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    /tmp/geo261-source-checks/source-index-sanitized "$case"
done
```

維護者在本機建立指定 base 的 draft PR：

```sh
git fetch origin codex/geo261-source-index-20261020-prbody
git show origin/codex/geo261-source-index-20261020-prbody:PR_BODY.md > /tmp/geo261-PR_BODY.md
gh pr create --draft --repo ZhiQiYang/geometry-axiom \
  --base architecture/geo261-integration-20261016 \
  --head codex/geo261-source-index-20261020 \
  --title '修正 GEO-261 來源圖線性搜尋造成的場景載入退化' \
  --body-file /tmp/geo261-PR_BODY.md
```
