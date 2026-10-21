本次實際 cwd：`/workspace/geo261-ledger-run.ra2_k2z2/repo`，HEAD=A `7159530c0e494d3211e6ab1764eb691137211707`。以 `git -c core.autocrlf=false worktree add --detach /workspace/geo261-ledger-run.ra2_k2z2/repo 7159530c0e494d3211e6ab1764eb691137211707` 建立，exit0；執行前新 cache 為空且 results 不存在。

```bash
cd /workspace/geo261-ledger-run.ra2_k2z2/repo
ulimit -s 16384
ulimit -c 0
unset PYTHONOPTIMIZE
export TMPDIR=/workspace/geo261-ledger-run.ra2_k2z2/tmp
export MUTATE_CACHE=/workspace/geo261-ledger-run.ra2_k2z2/cache
export MUTATE_RESULTS=/workspace/geo261-evidence/ledger-7159530c0e49.y0lrsfpu/mutants_results.json
export PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE=1
export CC=gcc
python3 -B -u tests/mutate.py
python3 -B tests/mutate.py --check
python3 -B tests/mutate.py --check --killers
```

三個程序的實際結束碼依序是 0、0、0。正式執行由 Python supervisor 設定 RLIMIT_STACK soft/hard=16777216 bytes、RLIMIT_CORE=0，並以獨立 session 啟動程序，stdout/stderr 直接寫檔；上列 shell 片段表達相同環境與實際 argv，不能聲稱三條原本在同一 shell 自動連續完成。兩條 check 是監看事件後另外補跑，見 recovery-check-receipts.json。原工具 `tests/mutate.py` raw SHA256=`8fc573fba9596ca8c6570a99c7de284584643a3560cee6cf5f0ac27416d26451`；其餘工具、source、版本、原命令詳見 environment.json、prepare-receipt.json、phase-receipts.json。

只驗收封裝原件，不重跑產品：

```bash
sha256sum -c SHA256SUMS
```

不要對本輪已使用的 cache/results 再執行全量命令來宣稱是同一輪；重現應另建新 worktree/cache/results，並保留新一輪收據。
