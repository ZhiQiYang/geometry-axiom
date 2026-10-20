【任務】GEO-261 載入成本的剩餘超線性:降低每次驗證重複的角材 footprint 來源求值(#300 的前置工作)

除了 commit 訊息用英文以外,所有說明一律用繁體中文。

## Repo 與分支
- repo:ZhiQiYang/geometry-axiom
- 基底:分支 `architecture/geo261-integration-20261016`,commit `546e2eb2142ebf19859489c5391b57cbb8413d10`(PR #288 的產品碼已定稿)
- 你的分支:`codex/geo261-load-residual-20261020`
- 你的環境連不到 GitHub API,所以**不要開 PR**:
  - 把完整 PR 正文存成 `PR_BODY.md`,推到另一個分支 `codex/geo261-load-residual-20261020-prbody`(只放這一個檔)。
  - draft PR 由維護者在本機開。
- GitHub Actions 被帳號計費擋住,每個 job 都會 0 步驟失敗,不算任何證據。

## 背景(已量測)
上一輪(#321)把 `geometry-core/kernel/source.c` 的來源圖查找改成雜湊索引。WSL 實測 fix/main 在 N=16/32/48/64 是 0.90/1.18/1.56/1.94×,但比值仍隨 N 上升。#300 要把角材容量從 64 提高到 512,照這個趨勢會嚴重超標。

gprof 呼叫次數(`-O1 -fno-inline -pg`,single 家族場景,產生器附在最後):

| 函式 | N=32 | N=64 | N 加倍的倍數 | main N=64 |
|---|---:|---:|---:|---:|
| `geo_eval_source` | 450,098 | 2,980,967 | 6.6×(約 N^2.7) | 不存在 |
| `wd_read`(`geometry-templates/woodworking/native/definition_sources.c:17`) | 5,922,136 | 43,503,376 | 7.3× | 不存在 |
| `contact_order`(`contact_world.c:25`,線性找 id) | 354,308 | 2,729,508 | 7.7× | 內嵌 |
| `wood_contact_collect_stops` | 3,438 | 12,942 | 3.8× | `collect_stop_faces` 12,924 |
| `app_reference_member_footprint`(`geometry-app/native/reference_sources.inc:628`) | — | 141,429 | — | 不存在 |

解讀:
- 擋面收集的呼叫次數與 main 相同,是兩邊共有的成本。
- GEO-261 多出來的是:每次驗證(`reference_check_all`、`geometry-app/native/world_validation.inc:41` 的 `app_validation_footprint`)都為每支角材重新經來源圖解析 footprint。每個 footprint 又要讀約 20 個來源(`reference_contact_facts`、`wood_definition_sources_placement`、`wd_read`…)。

## 目標
1. 主要:在同一個候選、同一次驗證之內,不要為同一支角材重複解析 footprint 的來源。可以記憶化,也可以改成先批次解析一次再查表;方法自選。
2. 次要(可選):
   - `contact_order` 改成依 id 直接索引;
   - `wood_contact_collect_stops` 的插入排序與 O(n²) 去重改成 O(n log n)。
   兩者都必須保持輸出順序與結果逐筆相同,包括 D11「先放者」的穩定排序。
3. 量化目標(以維護者的 WSL 重測為準,你那邊的機器只作參考):
   - N=64 的 fix/main ≤ 1.3×;
   - `geo_eval_source` 的呼叫數從 N=32 到 N=64 的倍數 ≤ 4.5×;
   - 不得讓 N=16/32/48 變慢。

## 硬性不變量(違反任一條就不能合)
A. 輸出逐位元組相同:
   - 基底與你的 head 各編一支 `gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm`(先 `ulimit -s 16384`);
   - 對產生器 N=16/32/48/64,以及 repo 根目錄全部 `*.scene`,各跑 `printf 'loadfile %s\ndump\n' X.scene | ./bridge`;
   - stdout 必須逐位元組相同,含錯誤訊息與拒絕的場景。
B. 來源圖相同:
   - 每次 seal 時,`geo_eval_node_at` / `geo_eval_edge_at` 的完整序列(內容與順序)必須與基底相同。
   - 依賴邊有去重,所以同一個 consumer 重複讀同一個來源不會新增邊。但如果快取跨 consumer 共用,就會漏記邊。
   - 寫一支暫時的檢測建置(例如 `#ifdef` 的傾印,或 tests 裡的 harness),對 A 的同一批場景比對基底與你的 head,並把比對結果附在證據裡。
C. 守門流量不變(P-177 禁止改守門流量):
   - `app_world_candidate_create` / `app_world_candidate_seal` / `app_world_candidate_publish` / `app_world_candidate_revalidate` / `reference_check_all` 的呼叫次數,在同一批場景上必須與基底完全相同(用 gprof 呼叫數或計數器證明)。
   - 只准減少「同一次驗證之內的重複來源讀取」,不准跳過任何驗證、候選或 seal。
D. 快取必須正確失效:
   - 候選內每一行指令都可能改變 World。快取的生命期與鍵必須保證不會用到過期值。
   - 寫明你的失效規則。
   - 新增測試涵蓋:同一候選內先放角材再移動或刪除、參數改值、拒絕後回滾。測試要證明拿掉失效邏輯時會出錯。
E. 不改公開 API(`source.h`、`contact_world.h` 等);純 C11;MSVC 可編;K 層不 include W/H,W 不 include H。
F. 不准動:
   - `tests/mutants_results.json`(帳本由維護者重產);
   - `geometry-core/domain-decoupling/` 的架構清單與收據;
   - `公理層.md`、`geometry-guide/` 的閱讀器;
   - BACKLOG.md、決策佇列.md。

## 測試與自證
- 新增測試要照 `tests/run_all.py` 的既有方式註冊,並更新 `tests/run_all.expected.json` 計數。
- 突變自證:分別讓快取「永不失效」與「跨 consumer 共用」,新測試或不變量 B 的比對必須轉紅,失敗訊息要指出病因。
- 至少跑:
  `ulimit -s 16384; python3 tests/run_all.py --build --only py:test_geo261_source_index --only py:test_geo261_candidate_cache --only py:test_geo261_graph_product --only py:test_geo261_assembly_graph_product --only py:test_bridge_integrity --only c:integrity --only core:run_tests`,再加你的新測試。
- 時間夠就跑完整 `python3 tests/run_all.py --build`。
  - 已知完整跑會紅兩項:`mutation:check`(帳本過期,由維護者重產)、`py:test_product_architecture`(若 manifest 未變應為綠;若因你新增檔案而紅,照實寫明,不要改清單)。
  - 其他任何紅燈都要處理或照實報告。

## 證據
- 放在 `tests/evidence/geo261-load-residual-20261020/`:原始輸出逐位元組保存、指令、結束碼、受驗 SHA、環境。
- 腳本若要入 repo,用 `.py.txt` 存放,避免被當成可執行來源。
- 效能:base / fix / main(`adbaebf9c73ea6801d7b4d5214e4b846b132923b`)交錯 3 輪,取中位數;附修正後的 gprof 前幾名與呼叫數表。

## PR_BODY.md 要寫
- 改了什麼、為什麼不變量 A–E 都成立(逐條)
- 驗收指令、結束碼、輸出摘要
- 效能表、呼叫數前後對照
- 突變自證結果
- 沒做到的目標要照實寫(例如 N=64 只降到 1.5×),不要為了達標跳過任何驗證
- 最後列「最不確定的地方」

## 場景產生器(存成 mini_gen.py;`python3 mini_gen.py 48 > s48.scene`)
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

## 完成後
推兩個分支(修正分支與 prbody 分支)。不要合併。維護者會在 WSL 重跑 A/B/C、效能與完整驗收,再送審查。
