【任務】修正 GEO-261 的場景載入效能退化:geometry-core/kernel/source.c 的來源圖線性搜尋

一律用繁體中文寫 commit 訊息以外的所有說明(PR 正文、留言)。commit 訊息用英文。

## Repo 與分支
- repo:ZhiQiYang/geometry-axiom
- 基底:分支 `architecture/geo261-integration-20261016`,commit `3e600772076465fc65a26ac09055028301c0fb0b`(PR #288 的 head)
- 你的分支:`codex/geo261-source-index-20261020`,開 **draft PR,base 設成 `architecture/geo261-integration-20261016`**(不是 main)
- GitHub Actions 被帳號計費擋住,每個 job 都會 0 步驟失敗。那不是產品紅燈或綠燈,不要為它改任何東西。

## 問題(已量測)
同一份場景用 `web_bridge` 的 `loadfile` 載入,N = 角材支數,中位數,3 次交錯取樣,WSL Ubuntu 24.04、gcc 13.3 -O2:

| N | main adbaebf9 | GEO-261 603e4195 | 倍數 |
|---|---|---|---|
| 16 | 0.49 s | 0.59 s | 1.2× |
| 32 | 0.87 s | 3.93 s | 4.5× |
| 48 | 1.10 s | 19.2 s | 17× |
| 64 | 2.18 s | 74.5 s | 34× |

(603e4195 與 3e600772 的差異只有測試與文件,產品碼相同。)

gprof(N=48,-O1 -fno-inline -pg)前兩名:
- `geo_source_edge` 82%,1,329,948 次呼叫
- `geo_source_node` 10.5%,1,329,948 次呼叫
- 兩者都由 `geo_eval_source` 呼叫;上游大宗是 `app_reference_member_footprint`(61,157 次,來自 `reference_check_all` 與 `app_validation_footprint`)

病因:`geometry-core/kernel/source.c`
- `geo_source_node` 每次都線性掃描全部 nodes 比對 (provider, key_size, key bytes)。
- `geo_source_edge` 每次都線性掃描全部 edges 去重 (consumer, source, kind)。
- 兩個陣列都用 `realloc(count+1)` 一次只長一格。
- `geo_eval_describe` 與 `geo_eval_source` 的 sealed 分支也是線性找 node。
呼叫次數 × 陣列長度 → 載入成本約 N⁴。

## 要做的
1. 在 `source.c` 的私有 `struct GeoEvalContext` 加雜湊索引(開放定址即可):
   - node 索引鍵 = (provider token, key_size, key bytes)
   - edge 索引鍵 = (consumer, source, kind)
   - 兩個陣列改成容量倍增
   - sealed 分支的查找也走索引
2. **語意必須完全不變**。這些都是觀察得到的行為:
   - `nodes` / `edges` 陣列的內容與插入順序要逐筆相同(`geo_eval_node_at`、`geo_eval_edge_at`、seal、收據都看得到順序)。
   - 每種狀態碼(OK / MISSING / INVALID / MEMORY / CYCLE)在相同輸入下要回相同值。
   - 配置失敗時不得破壞既有狀態;回 `GEO_SOURCE_MEMORY` 的條件不得變寬。如果索引配置失敗,可以退回線性掃描,也可以照原本規則回 MEMORY,選一種並寫明理由。
   - `geo_eval_clear` / `geo_eval_reset` / `geo_eval_destroy` 要釋放並重置索引。
   - 不改 `source.h` 的公開 API。
3. 限制:
   - 純 C11,不准用平台相依的加速。
   - 要能被 MSVC 編譯;編譯期檢查沿用 repo 既有的 typedef 寫法。
   - K 層檔案不得 include W(geometry-templates)或 H(geometry-app、geometry-web)的任何東西。架構掃描會擋。
4. **不准動**:
   - `geometry-app/geometry_app/model_sources.py`、`native_entrypoints` 相關檔(另一條分支正在改)
   - `公理層.md`、`geometry-guide/` 的閱讀器
   - `tests/mutants_results.json`(突變帳本由維護者重產)
   - `geometry-core/domain-decoupling/` 的架構清單與收據(維護者會在最終 SHA 重產)
   - BACKLOG.md、決策佇列.md
5. 新增一支 C 測試 harness,比照 `tests/geo261_*_harness.c` 的寫法,並照 `tests/run_all.py` 既有方式註冊;若有 `tests/run_all.expected.json` 計數,一併更新。至少涵蓋:
   - 大量不同 key 的 node,含刻意雜湊碰撞、不同 key_size、同 key 不同 provider、key_size=0
   - edge 依 (consumer, source, kind) 去重,三者任一不同都要新增
   - 插入順序與舊實作逐筆相同
   - sealed 後的查找
   - reset 後重建
   - 配置失敗路徑(若 repo 已有注入配置失敗的手法就沿用)
   - 有 ASan/UBSan 就跑一次
6. **突變自證**:把新索引的查找改成「永遠查不到」(會產生重複 node/edge),新測試必須轉紅,而且失敗訊息要指出是重複。把結果寫進 PR。

## 驗收(全部要附指令、結束碼、輸出)
A. 等價性:基底 3e600772 與你的 head 各編一支 bridge:
   `gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm`
   對下面產生器的 N=16、32、48、64 各跑:
   `printf 'loadfile %s\ndump\n' sN.scene | ./bridge`(先 `ulimit -s 16384`)
   兩支 bridge 的 stdout 必須逐位元組相同。
B. 效能:同一台機器,base / fix / main(`adbaebf9c73ea6801d7b4d5214e4b846b132923b`)三者交錯各跑 3 次 `loadfile`,報中位數表。
   - 目標:每個 N 都是 fix ≤ 2 × main。
   - 做不到就照實報,並附新的 gprof 前幾名。不要為了達標去改守門流量或跳過任何檢查(那是禁止的)。
C. 測試:至少跑
   `ulimit -s 16384; python3 tests/run_all.py --build --only py:test_geo261_candidate_cache --only py:test_geo261_graph_product --only py:test_geo261_assembly_graph_product --only py:test_bridge_integrity --only c:integrity --only core:run_tests`
   加上你的新測試;時間夠就跑完整 `python3 tests/run_all.py --build`。
   - suite 名稱以 `tests/run_all.py --list`(或該檔實際的列舉方式)為準。名稱若不同,用最接近的並寫明。
D. 架構掃描:`python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`
   - 已知它在基底就會因為 `geometry-core/framing-template/core-probe/gen_scenes.py` 未登記而失敗。這不是你的問題,不要修。
   - 只要確認除了這條以外,沒有因為你的改動新增診斷。

## 場景產生器(貼成 mini_gen.py;`python3 mini_gen.py 48 > s48.scene`)
```python
import math, sys
def scene(n):
    A, Z, best = 27, 2500, None
    for m in range(1, 61):
        if m > n - 5: break
        r = max(1, -(-(n - 4 - m) // (m + 1)))
        if r > 60: continue
        w = 916 + 918 * (m - 1) + 14 + 891 + A; h = 363 + 367 * (r - 1) + 14 + 295 + A
        s = abs(math.log(w / h / 1.04)) + 0.01 * (4 + m + (m + 1) * r - n) / n
        if best is None or s < best[0] - 1e-12: best = (s, m, r, w, h)
    _, m, r, w, h = best
    us = [916 + 918 * i for i in range(m)]; vs = [363 + 367 * j for j in range(r)]
    L = ["surface 1 origin 0 0 %d u +x v +y outline 0,0 %d,0 %d,%d 0,%d" % (Z, w, w, h, h),
         "grid 1 on 1 u %s v %s" % (" ".join(map(str, us)), " ".join(map(str, vs)))]
    def t(i, role, place): L.extend(["timber %d 27 33 role %s" % (i, role), "place %d on 1 %s" % (i, place)])
    t(1, "boundary", "at-face e0 between e3 e1 +u +n"); t(2, "boundary", "at-face e2 between e3 e1 -u +n")
    mains = [3 + i for i in range(m)]; wl, wr = 3 + m, 4 + m
    for i, k in enumerate(mains): t(k, "primary", "at-line grid 1 u %d between t1 t2 +v +n" % i)
    t(wl, "primary", "at-face e3 between t1 t2 -v +n"); t(wr, "primary", "at-face e1 between t1 t2 +v +n")
    k = 5 + m
    for bay in range(m + 1):
        left = wl if bay == 0 else mains[bay - 1]; right = wr if bay == m else mains[bay]
        for j in range(r):
            if k > n: break
            t(k, "secondary", "at-line grid 1 v %d between t%d t%d +u +n" % (j, left, right)); k += 1
    return "\n".join(L) + "\n"
sys.stdout.write(scene(int(sys.argv[1])))
```
(它與維護者的基準產生器在 N=16/32/48/64 逐字相同,已驗證。)

## PR 正文要寫
- 改了什麼、為什麼語意不變(逐條對應上面第 2 點)
- 驗收 A–D 的指令、結束碼、輸出摘要
- 效能表(base / fix / main 與倍數)
- 突變自證結果
- 沒跑或沒過的項目照實寫
- 最後列「最不確定的地方」

## 完成後
- 推分支、開 draft PR,不要合併。
- 維護者會在自己的 WSL 重跑等價性、效能與完整驗收,再送審查。
