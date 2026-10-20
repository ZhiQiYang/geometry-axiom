修正 GEO-261 來源圖在場景載入時反覆線性搜尋的退化。產品碼僅修改 `geometry-core/kernel/source.c`；基底為 `3e600772076465fc65a26ac09055028301c0fb0b`，PR base 為 `architecture/geo261-integration-20261016`。

## 實作與語意

- 私有 context 增加 node／edge 開放定址索引，鍵分別為 `(provider, key_size, key bytes)` 與 `(consumer, source, kind)`。索引負載最多一半，碰撞後仍完整比對鍵；sealed 的 describe／source 共用 node 查找。
- `nodes`／`edges` 仍只在原本新增位置追加，索引只存原插入序號加一，擴表不排序或搬動節點本體。公開列舉、seal 及收據沿用相同陣列與順序；harness 以獨立的舊式線性去重模型逐筆核對。
- 保留原有輸入檢查、provider 缺失、dependency kind、ACTIVE 循環、成功值快取、失敗／重試、描述與求值邏輯，以及 sealed 的 INVALID 規則；沒有增加 provider 呼叫或跳過任何守門流程。新測試明確覆蓋 OK／MISSING／INVALID／MEMORY／CYCLE／FAILED。
- 兩陣列改用倍增容量。倍增配置失敗時重試舊實作的 `(count+1)` 大小；必要的 node／key／陣列配置失敗時仍回 MEMORY，既有內容、計數、節點與輸出不被覆寫。
- 索引配置是可選的：首次配置或擴表失敗即釋放不完整索引，退回原本線性搜尋；之後新增時可重建。理由是索引只加速查找，不應新增 MEMORY 條件。harness 同時驗證索引失敗時的順序、去重、sealed 讀取及恢復。
- `geo_eval_clear` 釋放索引並將指標、容量及旗標重置；reset／destroy 沿用它。reset 仍拒絕 sealed／active context。
- `source.h` 公開 API 未改；只使用 C11 的無號整數運算及標準函式庫，沒有新增編譯期斷言或平台加速，也沒有引入 W／H 依賴。未修改任務列出的禁止檔案或架構清單／收據。

## A／B：等價性與效能

環境、指令、結束碼、stdout 指紋及每次原始量測見 [驗收證據](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-source-index-20261020/tests/evidence/geo261-source-index-20261020/README.md) 與 [measurements.json](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-source-index-20261020/tests/evidence/geo261-source-index-20261020/measurements.json)。此為雲端 Linux x86_64（Intel Xeon Platinum 8573C）／GCC 14.2.0 的同機比較；維護者的 WSL 數據須另行重跑。

```sh
git worktree add --detach /tmp/geo261-source-base 3e600772076465fc65a26ac09055028301c0fb0b
git worktree add --detach /tmp/geo261-source-main adbaebf9c73ea6801d7b4d5214e4b846b132923b
python3 -u tests/evidence/geo261-source-index-20261020/measure.py \
  /tmp/geo261-source-base "$PWD" /tmp/geo261-source-main /tmp/geo261-source-measure
```

腳本設定 stack 16 MiB（等同先 `ulimit -s 16384`），三份工作樹各執行：

```sh
gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm
python3 mini_gen.py N > sN.scene
printf 'loadfile %s\ndump\n' sN.scene | ./bridge
```

A：三次編譯與八次 base／fix 的 loadfile＋dump 全部結束碼 0；四個 N 的 stdout 都逐位元組相同，loadfile／dump JSON 全部 `ok:true`，stderr 皆空。

| N | stdout bytes | base／fix SHA-256（相同） |
|---|---:|---|
| 16 | 3352 | `9700c998cffafad61604347e45d54e7fcc81e026e60a43a84cb799652ecdd41e` |
| 32 | 5827 | `fa8c6cd72bdeb4b8e86d3f035a860653035764e21681ba9b6834a5b5b5e9f761` |
| 48 | 8314 | `8b7a82faedf42c28d0b025e7fdfa12dde126086cb9304b7f6ac45b0a6d40563b` |
| 64 | 10791 | `999065d3fc69913fbc292ddaa6d90439678d303cb2c8e73d36d0d8de014ba2e5` |

B：僅輸入 `loadfile`，每個 N 使用 `base/fix/main`、`fix/main/base`、`main/base/fix` 三回合交錯順序；三版本各三次，36 次全部結束碼 0、`ok:true`、stderr 空。下表單位秒，取中位數。

| N | base | fix | main | fix／main | base／fix 加速 | 達成 ≤2× main |
|---|---:|---:|---:|---:|---:|---|
| 16 | 0.2326 | 0.1987 | 0.1677 | 1.19× | 1.17× | 是 |
| 32 | 1.2991 | 0.4609 | 0.2824 | 1.63× | 2.82× | 是 |
| 48 | 5.6311 | 0.9797 | 0.4412 | 2.22× | 5.75× | 否 |
| 64 | 19.4856 | 1.9231 | 0.6972 | 2.76× | 10.13× | 否 |

N=48、64 未達 2× main，照實保留全部樣本，未修改守門流量或略過檢查。補跑：

```sh
gcc -std=c11 -O1 -fno-inline -pg geometry-web/web_bridge.c -o /tmp/geo261-source-checks/bridge-profile -lm
cd /tmp/geo261-source-checks
ulimit -s 16384
printf 'loadfile /tmp/geo261-source-measure/s48.scene\n' | ./bridge-profile
gprof ./bridge-profile gmon.out
```

編譯、載入與 gprof 結束碼皆 0；載入 `ok:true`。新版 flat profile 前幾名：`_init` 20.00%、`wood_contact_collect_stops` 11.43%、`contact_order` 8.57%、`geo_vector_dot` 7.14%、`geo_source_find_edge` 5.71%、`wd_read` 4.29%。`geo_source_node`／`geo_source_edge`／`geo_eval_source` 各 1,329,948 次，`app_reference_member_footprint` 61,157 次，與問題提供的呼叫數相同。0.01 秒取樣的百分比只作熱點線索；[原始 flat 摘錄](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-source-index-20261020/tests/evidence/geo261-source-index-20261020/gprof-summary.log) 保留實際輸出。

## C：測試與突變自證

suite 名稱由 `python3 tests/run_all.py --list` 確認，與任務指定相同。新增 `tests/geo261_source_index_harness.c` 與 `py:test_geo261_source_index`，依既有 Python native-build 方式登錄；expected 計數增加 7。

```sh
ulimit -s 16384
python3 tests/run_all.py --build \
  --only py:test_geo261_candidate_cache \
  --only py:test_geo261_graph_product \
  --only py:test_geo261_assembly_graph_product \
  --only py:test_bridge_integrity --only c:integrity --only core:run_tests \
  --only py:test_geo261_source_index
python3 tests/test_geo261_source_index.py
```

新 harness 涵蓋 1,536 個不同 binary key（前 32 個刻意落在最終 4,096 槽表的同一槽）、不同長度、相同 key 不同 provider、空 key、edge 三欄去重、線性模型插入順序、sealed、reset 重建及必要／可選配置失敗。

突變自證由同一支 Python 測試將真實 `geo_source_find_node`／`geo_source_find_edge` 的函式開頭分別插入 `return SIZE_MAX;`／`return false;`，其餘產品碼與 harness 保持原樣；先確認基準通過，再編譯突變並執行相同案例，最後重驗基準。編譯錯誤、崩潰或逾時不算偵測成功。

`python3 tests/test_geo261_source_index.py` 結束碼 0，7 tests 全過；兩支突變執行檔都正常編譯，執行結束碼為 1，原始 stderr：

```text
ASSERT:duplicate-node line=143 expr=geo_eval_node_count(ctx)==oracle_node_count
ASSERT:duplicate-edge line=171 expr=geo_eval_edge_count(ctx)==oracle_edge_count
```

失敗直接指出重複。同一套測試在未突變的真實實作恢復通過；沒有修改 `tests/mutants_results.json`。

```sh
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I geometry-core/kernel tests/geo261_source_index_harness.c \
  -o /tmp/geo261-source-checks/source-index-sanitized
# 各執行 nodes / edges / allocation / growth / statuses
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  /tmp/geo261-source-checks/source-index-sanitized nodes
ulimit -s 16384; python3 tests/run_all.py --build
```

指定 7 個 suite 全部通過，結束碼 0：`c:integrity` 432、`core:run_tests` 165、bridge integrity 24、assembly graph product 4、candidate cache 18、graph product 5、新 source index 7，合計 655／655，無失敗／skip。獨立新測試結束碼 0，7／7 通過；sanitizer 編譯及 `nodes`／`edges`／`allocation`／`growth`／`statuses` 五組案例全部結束碼 0，輸出各為 `PASS <case>`，沒有 ASan／UBSan 診斷。

完整 `python3 tests/run_all.py --build`（224 suite）仍在執行中，尚未宣稱通過。已知 `mutation:check` 因來源閉包變動回傳 1：base 已有 18 筆 stale，fix 有 75 筆 stale；依任務限制不重產 `tests/mutants_results.json`。本段及完整輸出將於執行結束後更新。

## D：架構掃描

base 與 fix 各執行：

```sh
python -B tests/architecture_contract.py --root . \
  --manifest geometry-core/domain-decoupling/product-architecture.json
```

base／fix 結束碼皆 1，兩份 stdout 逐位元組相同（`cmp architecture-base.log architecture-fix.log` 結束碼 0、輸出空），唯一診斷：

```text
geometry-core/framing-template/core-probe/gen_scenes.py:1
SOURCE_UNREGISTERED: executable source omitted from the complete manifest
```

沒有新增診斷；既有 manifest 完整性錯誤仍阻擋掃描繼續，不能將它描述成完整架構綠燈。本次沒有修該檔或重產架構清單／收據。

依任務已知資訊，GitHub Actions 受帳號計費阻擋的零步驟失敗不作為產品通過／失敗證據；本次沒有為它修改程式或 workflow。PR 保持 draft，不合併。

## 最不確定的地方

- N=48／64 仍未達 2× main；共享雲端機器與維護者的 WSL／GCC 13.3 有差異，須在維護者環境重跑全部交錯樣本。
- 未實際執行 MSVC 編譯；本次僅有 GCC 14.2.0 及 ASan／UBSan 的實測。
- 配置失敗以測試端代理注入驗證，沒有進行整機記憶體耗盡實驗。
- 架構掃描仍受既有 manifest 完整性錯誤阻擋；完整非瀏覽器 suite 尚在執行，正式瀏覽器整合未執行。
