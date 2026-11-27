# PR #456 API worker 本機重演證據（不屬於 PR，不併入 main）

這個孤兒分支只放 PR #456（`.github/workflows/api-worker.yml`）的本機重演原件，供審查方逐字核對與重跑。
它與 main 沒有共同歷史，不改動 repo 的任何檔案。

## 內容

| 路徑 | 說明 |
|---|---|
| `harness/replay.py`、`fake_api.py`、`fake_gh.py` | 重演程式的最新版，產生 `runs/red-r3`、`runs/green-r3` |
| `harness/replay.56db0239.py` | 前一版重演程式，產生 `runs/red-r2b`、`runs/green-r2` |
| `workflows/api-worker.<commit>.yml` | 受測的 workflow 原件：`8f0e5def`（F1–F7 修正前）、`6eac9e5c`（F1–F7 修正後）、`4c4438f3`（R2-1～R2-3 修正後）、`0f873dd8`（R3-1 與巢狀 公理層.md 修正後） |
| `mutants/*.yml` | 具名撤回檔。前 8 份（EXEC_PATH、CREATE_ONLY、PROTECTED_ROOT_MATCH、ROOT_MATCH_AND_TREE、INTERMEDIATE_TREE、MISSING_RECEIPT_UNKNOWN、PUSH_UNKNOWN_STATE、CLEANUP_ORDER）以 `6eac9e5c` 為基準；接著 3 份（SCAN_ERROR_CHECK、PGREP_RC_CHECK、PUSH_OUTCOME_SPLIT）以 `4c4438f3` 為基準；最後 3 份（SCAN_RC_EXACT、SCAN_CLASSIFIER_RC、NESTED_SSOT）以 `0f873dd8` 為基準 |
| `runs/red9/` | `REPLAY_WF=api-worker.8f0e5def.yml python3 replay.py <F1–F7 的 9 個情境>`（先紅） |
| `runs/green/` | `python3 replay.py all`，workflow＝`6eac9e5c`（25 情境） |
| `runs/red-r2/`、`runs/red-r2b/` | `REPLAY_WF=api-worker.6eac9e5c.yml python3 replay.py <R2 的 5 個情境>`（先紅；r2b 重跑兩個 push 情境，補上 post-receive 收據） |
| `runs/green-r2/` | `python3 replay.py all`，workflow＝`4c4438f3`（30 情境） |
| `runs/red-r3/` | `REPLAY_WF=api-worker.4c4438f3.yml python3 replay.py scan-killed scan-classifier-error nested-axiom-merge`（先紅） |
| `runs/green-r3/` | `python3 replay.py all`，workflow＝`0f873dd8`（33 情境） |
| `runs/withdrawals-0f873dd8.txt`、`runs/withdrawal-APIWORKER_{SCAN_RC_EXACT,SCAN_CLASSIFIER_RC,NESTED_SSOT}_REMOVED.*.log` | 最後 3 份撤回的完整 `diff -u`、重演節錄與全文 |
| `runs/withdrawals-6eac9e5c.txt`、`withdrawal-diffs-6eac9e5c.txt` | 前 8 份撤回的重演節錄與完整 `diff -u` |
| `runs/withdrawals-4c4438f3.txt`、`withdrawal-APIWORKER_SCAN_ERROR_CHECK_REMOVED.scan-fails.log` | 後 3 份撤回的完整 `diff -u` 與重演節錄／全文 |

每個 `runs/*/` 底下的 `<情境>.log` 是重演時逐 step 的原始紀錄，`<情境>.api.log` 是假 API 收到的請求。
`summary.out` 是該次命令的標準輸出（最後一行是 `replay exit=`）。

`<情境>.log` 每個 step 只列輸出的最後 60 行。從 `runs/red-r3`、`runs/green-r3` 起，每個 step 的完整輸出另存在 `<情境>.steps/<序號>-<job>.out`；較早幾輪沒有完整輸出，只能稱為節錄。
從 `runs/red-r3`、`runs/green-r3` 起，摘要裡的 `work` 結果也計入 always() 的 Stop／Package 兩步（與真 Actions 的 job 狀態一致）；較早幾輪的 `work` 欄位沒有計入這兩步，不能拿來代表 job 狀態。

## 注意

- 各 `runs/` 的 `replay.py` 版本不同。harness 在各輪之間有增修：新增情境、故障注入、每情境重置。
  只有 `runs/green-r2` 對應這裡的 `harness/replay.py`；較早幾輪的 harness 差異，見 PR #456 的留言 7173365615、7175299588 與本分支所在的留言。
- `replay exit=0` 只是重演程式的結束碼，不代表每個安全斷言都通過。斷言結果要看各情境的 `reasons`、遠端分支、sentinel、貼出的留言。
- 重演環境：Ubuntu 24.04.5 容器、sudo 1.9.15p5。以非 root 的 `runner` 使用者（有 NOPASSWD sudo）逐 step 執行 YAML 的 `run:` 原文。
  GitHub 換成本機 bare repo 加假 `gh`；Anthropic API 換成 `fake_api.py`，配合真 Claude Code CLI 2.1.330。
  每個情境開始前把 `/usr/local/bin`、`/opt` 設成 777，模擬 runner 映像。
  harness 需要 root；它會建立使用者並改動 `/etc/sudoers.d`、`/etc/gitconfig`、`/srv/replay`，只能在拋棄式容器裡跑。
- `replay.py` 裡出現的 `ghp_`、`sk-ant-api03-` 字樣，是執行時才組出的假憑證，用來測試拒絕條件，不是真的金鑰。

## 雜湊

見 `SHA256SUMS`（`sha256sum` 格式，涵蓋本分支所有檔案，README 與 SHA256SUMS 除外）。
