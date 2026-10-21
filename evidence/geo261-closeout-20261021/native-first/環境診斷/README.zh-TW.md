# Native 程序回收失敗：環境對照證據

來源固定為 `366ef501b78105d1f7242dc1f4f4752cac9086b5`，工作樹 `/workspace/geo261-native`。原始完整 native 執行仍依自己的結束碼判定；下列單測對照不能把原本的 fail 改算通過，也不能取代完整 native 重跑。

## 觀察與判定

完整 native 的 `py:test_assembly_mutation_check` 在 12 題中有 1 題失敗：`test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left` 期待 `afterKill == []`，實際殘留兩個 `sleep`，狀態均為 `Z`（PID 76947、76948；程序群組／session 76946）。原始 trace、suite JSON 與空白 stdout 原件均保存在本目錄，檔名以 `original-` 開頭。

只讀 `/proc` 採樣確認 PID 1 為 `tail`；上述兩個 sleep 的 `PPid` 均為 1 且仍為 `Z`。`pid-1-status.log`、`pid-76947-status.log`、`pid-76948-status.log` 保存採樣時的原始 bytes；`original-environment-observation.json` 記錄每個檔案的採樣時戳、來源路徑、byte 數與 SHA-256。這些是失敗之後的採樣，不冒稱執行前狀態。

原環境與外層 subreaper 對照吻合事前假說：這次指定單測的紅燈來自孤兒程序沒有被回收的環境條件。證據不支持把它解讀為幾何斷言失敗；正式 suite 的失敗仍須保留。

## 原始機制

- `tests/test_assembly_mutation_check.py` 檔頭明示這批單測不需要編譯器。指定方法以 `sh -c 'sleep 30 & sleep 30; wait'` 建立 shell 與後代，給 `run_logged` 2 秒期限，要求逾時後整個程序群組完全消失。
- `tests/assembly_mutation_check.py:495` 的 `run_logged` 使用 `start_new_session=True`。逾時後對程序群組送 `SIGKILL`，再以 `process.wait()` 回收直接子 shell。
- `wait_group_gone` 在最多 5 秒內每 0.05 秒掃一次 `/proc`。`group_members` 明確把程序群組或 session 相符的 zombie 也列入；這是既有判準，本次未改成忽略 `Z`。
- `SIGKILL` 使 sleep 結束，但不代替父程序的 wait。shell 同時被殺後，sleep 需要由最近的 subreaper 或 PID 1 收養並回收，程序表條目才會消失。`process.wait()` 只回收直接子 shell，不會憑空取得已由 PID 1 收養的 sleep。

因此成立條件是**祖先中的回收程序能在期限內 wait 孤兒**，不限定一定由 PID 1 完成。一般 CI VM 的 init／systemd 可以提供這項條件；以 `tail` 當 PID 1 的容器不能直接假設有同樣行為。本次沒有實跑 GitHub CI，不能據一般環境慣例宣稱 CI 已通過。

## 已執行的兩案

同一來源、同一單測、同一 16 MiB stack，事前預期 plain 為 exit 1、subreaper 為 exit 0：

| 案例 | 實際 exit | 耗時 | 觀察 |
|---|---:|---:|---|
| plain | 1 | 7.169 秒 | 1 題 failure；`afterKill` 殘留兩個 `Z` |
| 外層 Linux subreaper | 0 | 2.138 秒 | 1 題成功；外層回收 2 個 SIGKILL 孤兒與測試子程序 |

plain 的實際 argv：

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -m unittest tests.test_assembly_mutation_check.AssemblyMutationCheck.test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left
```

subreaper 的完整 `python -c` 實際 argv 原樣封存在 `subreaper-command.json`，不是另存一份 repo 工具。它只在自己的程序呼叫 `prctl(PR_SET_CHILD_SUBREAPER=36, 1)`，用 `PR_GET_CHILD_SUBREAPER=37` 核對，fork／exec 同一個單測，然後以 `waitpid(-1, 0)` 回收自己收養的子程序；最後原樣回傳測試子 exit。沒有修改測試、包裝 unittest 結果、偽造斷言、忽略 zombie 或操作原 native 的程序。

`subreaper-reaped.json` 記錄實際回收：孤兒 83864、83865 的原始 wait status 均為 9（SIGKILL，exit code -9）；測試子 83861 的 wait status 0、exit 0。這些 PID 與原 native 的 76947／76948 不同。外層直到自己的子程序都已回收才結束。

`environment-control-summary.json` 保存前後完整 SHA、乾淨狀態，以及 `tests/test_assembly_mutation_check.py`、`tests/assembly_mutation_check.py`、`tests/run_all.py`、`tests/run_all.expected.json` 的前後雜湊。四檔 bytes 未變，前後 SHA 相同、工作樹皆乾淨。兩案的命令、環境、實際結束碼與時間分別保存在 `plain-*`、`subreaper-*` 收據。

## 後續驗收建議與限制

先讓原完整 native 結束或到達既定 35 分鐘上限，保留其真實結論。若其他關卡沒有更早的阻擋，可在具備正確孤兒回收的 runner 中，以相同 SHA、相同完整 `tests/run_all.py --build` 命令重跑，另留完整新收據；不可拿本次單測對照補寫原完整跑的通過結果。

可選擇既有具 init 的 CI／Linux runner，或以只監督該次測試子樹的外層 subreaper 提供環境條件。若使用 Docker 的 `--init`，仍須實際核對 init 與回收行為；此處沒有啟動 Docker 或驗證 daemon，也沒有改系統設定。

這份對照只驗指定程序回收單測。未重跑其他 suite、沒有執行突變器的完整編譯工作，也沒有把完整 native 宣告為綠燈。最大不確定性是完整 native 其餘 suite 的結果與另一 runner 的實際環境條件，須以各自完整收據判定。
