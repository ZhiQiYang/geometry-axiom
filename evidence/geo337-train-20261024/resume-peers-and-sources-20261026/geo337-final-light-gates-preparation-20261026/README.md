# 固定 F 後最小輕量驗收

F 固定為 `cbf0fb621888596aa14ad5f2349b503e23b1b72d`，候選分支 `codex/train337-recovered-evidence-20261026`；原三葉採入真正執行由 root 完成，本稿沒有採入、FF、測試或清理。這份工具只在 root 已錄製的一般 FF **之後**跑四條原裁判；沒有新的 source materializer、Git clone 或 mutation framework。

## 身分與依賴

- 私有 source：`/dev/shm/geometry-axiom-geo337-20261025/a6-architecture-source-20261026`。原 preparation 是 A=`a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，全部 3763 selected leaves、604 架構輸入、五 fixture 保留。
- 原 source RESULT SHA256：`2c8542df06b79b21a2a94ef5ce382d07a697a562e035ea86613dfb4a135274c4`；SOURCE_MANIFEST SHA256：`fbd0ded63cf26fab983e9befe1c957b5ade9e1e18a1f390f19a1fe4ebb8ff385`。
- 原 A 三 gate RESULT `1dd78c0ef53d715316da892886bdb20d475a2a03e3dccf8a84c3f060e26b6f25`、四檔 RESULT `a532b83a67e19b37e2cf724fb4d9ec86753b3a090de554093646b2e2c3d1b2df` 均 exit0；保留 A 標示，不改為 F、不重跑 A。
- 原 S10 full123 exit0、自然 execution heads 留 S10；本稿不執行重產。
- 此 checkout **不是 native 的 6997 葉來源，也不是 browser 的 3759 葉來源**。native source 與 browser thin seed 的正式準備各有原守門。
- 僅用 Python stdlib、Git、來源內原四裁判，沿用固定 c387 recorder。沒有 C 編譯或 Chrome/Node 依賴；tracked check 不是 full123。

## Root 執行順序

1. 對三葉採入 `RESULT.json` 真終態做獨立 peer，綁完整原件 hash。fresh capacity 與原雙鎖准入。保留 publisher 的 HEAD/index/refs 與 source 原 index，確認 source 為 A、clean、3763 實檔及五 fixture 未變；A→F 全非 evidence diff 必須只有 ledger/report/receipt 三葉。不得把跳過檢查或不完整 source 當作 FF 成功。
2. 使用 c387 recorder 在該 source 執行原生命令 `git -c gc.auto=0 -c maintenance.auto=false merge --ff-only cbf0fb621888596aa14ad5f2349b503e23b1b72d`，保留原 exit/stdout/stderr 與前後 HEAD/index。只移此私有 checkout HEAD/index；publisher 的 historical HEAD/index/train ref 不移。原 A Git objects 已透過既有單一 publisher alternate 可解析 F，不 fetch、不新增 provider、不碰舊 native source。失敗就保留 partial state，不 reset/clean/重寫。
3. Root 填 `REQUEST.UNBOUND.json`：source_result/source_actual_peer 仍綁原 A；adoption_result 綁真正 F 採入原件；三個 root lease 從 false 改 true。這不是許可模板自行推定批准，只有 root 可做。固定 request bytes hash。
4. 保原 16 MiB stack，以正式 require_escalated 執行：

   ```text
   python3 -B /tmp/geo337-final-light-gates-preparation-20261026/run_after_ff_four_gates.py --execute-root-approved --request <root-bound.json> --request-sha256 <sha256>
   ```

   runner 不移任何 source/ref；驗當下 HEAD=F、全部 3763 raw Git bytes、五 fixture、604 closure、原3leaf差分與原件 hash 後，實跑：

   ```text
   python3 -B tests/mutate.py --check
   python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
   python3 -B tests/test_architecture_contract.py
   python3 -B tests/test_product_architecture.py
   ```

   `MUTATE_*`、`GEOMETRY_*`、外來 Git/Python injection 清除，原 tracked ledger 真正讀取；無改時限、斷言或裁判。所有四項都收齊，任何非零使 wrapper 1。輸出在 OWN/F-final-light-gates-original-20261026，完整 c387 子命令、stdout、stderr、環境、F、raw input inventories、terminal RESULT。私有 source 原 index 透過獨立 out/private-index 保全；publisher 與原 `/workspace/geometry-axiom` 的 HEAD/index/refs/config/alternates 均只讀前後對照。
5. 另一 peer 核四項真 exit 與 c387 原流完整性，再原件封包/一般 push/完整 remote bytes 核驗。未完成前不得標 F 全綠。source_result 仍 A；新 gate receipt F；ledger 仍 S10。這是刻意保留三種不同意義的 SHA。

## 實際空間與守門

2026-10-26 此次唯讀快照：兩 OWN 全 inode 去重 U=`1741426688` B，2 GiB 餘裕 `406056960` B；SHM actual free `16130453504` B；/tmp free `24371200` B；/workspace free `4386816` B。這是瞬時取樣，執行前必重算。

輕量四 gate 保留既有 `64 MiB` reserve 與 `U+64 MiB≤2 GiB`；實際 TMPDIR/TMP/TEMP 一律新 out/tmp，故不消耗 native hardcoded /tmp/geometry-tests。複製原 index、兩份3763 inventory、604 inventory、約 0.2 MiB 三架構原 stdout/stderr 都納入 reserve；test_product_architecture 的可重建604 snapshot 在此 TMPDIR。此處未降低 native 的128 MiB或 browser416 MiB 門檻。若64 MiB不夠，拒絕並保留原件，不借用其他守門數字。

同一快照下，單 browser 原 `U+416 MiB≤2 GiB` 尚缺 `30150656` B，且尚未計 final thinseed 增量 D。此共同阻擋只能由 root 解決已授權安全空間或具體報缺；本稿不刪任何 cache，尤其不碰已拒絕的3156範圍。完整六項保守計畫仍是 `U+D+1600 MiB≤2 GiB`，不足不能稱已准入；每項真終態後保留並發布完整原件，按實際保留量重新算下一項，不刪 raw、不放大2GiB。

## 小稿驗證範圍

`prepare_runner.py` 只讀既有工具並產生一份最小副本，原件不變；曾在產稿 AST parse 發現缺少分號，已只修產稿再通過 AST parse 與預設 PLAN_ONLY。這不是正式 gate 或反證結果。`MINIMAL_DIFF.txt` 為完整差分；新 runner 尚待獨立靜審與 root 真執行。沒有執行 F gate、沒有重新 full123、沒有清理或額外 clone。
