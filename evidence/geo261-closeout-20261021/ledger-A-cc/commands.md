# 本輪實際命令與重現條件

以下是本輪已執行的命令，完整 argv、cwd、環境及 actual wait code 在 prepare-receipt.json、launch-receipt.json、environment.json 與 phase-receipts.json；重現時須換全新 cache、TMPDIR 與 MUTATE_RESULTS，不能覆寫本包原件。

```sh
git -c core.autocrlf=false -C /workspace/geometry-axiom worktree add --detach /workspace/geo261-ledger-cc-run.nu12fpy7/repo 7159530c0e494d3211e6ab1764eb691137211707
```

正式唯一 writer 的 cwd 是 `/workspace/geo261-ledger-cc-run.nu12fpy7/repo`。從 env 刪除 CC、PYTHONOPTIMIZE；設定 TMPDIR=`/workspace/geo261-ledger-cc-run.nu12fpy7/tmp`、MUTATE_CACHE=`/workspace/geo261-ledger-cc-run.nu12fpy7/cache`、MUTATE_RESULTS=`/workspace/geo261-evidence/ledger-cc-7159530c0e49.wzi0t97l/mutants_results.json`、PYTHONIOENCODING=utf-8、PYTHONDONTWRITEBYTECODE=1。設定 RLIMIT_STACK soft/hard=16777216、RLIMIT_CORE soft/hard=0。未傳任何 ID 篩選，未使用只更新 stale。

```sh
python3 -B -u tests/mutate.py
python3 -B tests/mutate.py --check
python3 -B tests/mutate.py --check --killers
```

三者依序執行，結束碼依序 0、0、0。啟動器實際 argv：

```sh
python3 -B /workspace/geo261-evidence/ledger-cc-supervisor.py /workspace/geo261-evidence/ledger-cc-7159530c0e49.wzi0t97l/prepare-receipt.json
```

呼叫端以 start_new_session 啟動，stdout/stderr 直接導向外部 orchestrator.log；無互動 session 依賴。啟動器 sourcecode.txt 是原 bytes。編譯設定預檢 argv 在 prepare-receipt.json，官方方法實際回 CC_present=false、compile_command argv0=cc，exit 0。

外部靜態封裝核對（不編譯、不測產品）：

```sh
python3 -B /workspace/geo261-evidence/ledger-cc-validate-and-package.py
```

第一次 exit 1 為新增 AST 核對的 parser 錯誤，完整原 stdout/stderr 另存 validation-attempt1.*。只修外部 parser，第二次 exit 0。正式三階段未重跑，工具／門檻未改。驗收工具兩版路徑與 SHA 在 validation-attempts.json；SHA256SUMS 僅驗包完整性，不能替代官方測試的判定。
