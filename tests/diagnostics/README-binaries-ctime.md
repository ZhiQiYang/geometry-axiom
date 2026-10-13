# #212：保留原測試的 ctime 實測工具

這是 T1 的中間成果。它提供可重複的採樣與原始輸出，**本文件不代表已完成 Linux 200 次實測，也不判定 #212 的推測成立**。工具不編譯或執行原生二進位。

`binaries_ctime_probe.py` 直接載入並執行既有的
`BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published`，每次包含 unittest 的 setup、assertion 及 cleanup。它不複製測試本體、不調整等待、不放寬斷言、不修改 `tests/binaries.py`。

預設先執行 200 次 control，再執行 200 次 observed：

- control：不插入 utime/stat 採樣。
- observed：只包住該次 `neutral.bin` 的兩次 `os.utime`，在第一次設定 mtime 後取 before、第二次還原 mtime 前取 after_rewrite、還原後取 after_restore。每次保存三個 `st_ctime_ns` 及 dev、ino、size、mtime 等欄位。測試結束後、臨時檔清除前另讀回內容，確認失敗案例確實有改寫。採樣失敗另記，不能冒充完整證據。
- 最後在同一 temp root 建立校準檔，重複保留 atime/mtime 的 utime + stat。`--samples N`（N 至少為 2）產生 N 個 delta、N+1 筆原始讀值，記錄零值、負值及觀測到的最小正 delta。

額外的 stat 和 Python 包裝會改變時序，可能讓 flake 消失；所以同時保留 control 組。兩組依序執行，失敗率差異也可能來自執行時間不同。這不是無干擾的核心追蹤。

## Linux 執行方式

在 Linux 自有 checkout 執行。不要使用共用驗收槽、本機 WSL 或使用者正在操作的應用服務。輸出位置用 checkout 外的新目錄；工具拒絕覆寫非空目錄。

```sh
# Bash；先遵循 native 測試的 stack 與統一入口規則。
ulimit -s 16384 || exit $?
evidence_dir=$(mktemp -d /tmp/geometry-212.XXXXXX)
set +e
git rev-parse HEAD > "$evidence_dir/head.txt"
git status --porcelain=v1 > "$evidence_dir/worktree-status.txt"
python3 tests/run_all.py --build --only py:test_binaries > "$evidence_dir/baseline.log" 2>&1
baseline_exit=$?
printf '%s\n' "$baseline_exit" > "$evidence_dir/baseline.exit"

# 即使原測試失敗，也繼續收集 flake 證據；兩個 exit code 分開保存。
python3 tests/diagnostics/binaries_ctime_probe.py \
  --iterations 200 --samples 10000 --temp-root /tmp \
  --output "$evidence_dir/ctime" > "$evidence_dir/probe.log" 2>&1
probe_exit=$?
printf '%s\n' "$probe_exit" > "$evidence_dir/probe.exit"
printf 'evidence_dir=%s baseline_exit=%s probe_exit=%s\n' \
  "$evidence_dir" "$baseline_exit" "$probe_exit"
```

`run_all --only` 是部分驗證，不是全套 native 通過聲明。probe 的退出碼也不能替代 `run_all` 的退出碼。

若要研究 CI 的特定檔案系統，將 `--temp-root` 換成該掛載點上已存在的目錄，並在報告寫明差異。工具同時設定 unittest 的 temp root 與校準檔位置；不要拿 `/tmp` 的結果宣稱另一個檔案系統有相同解析度。

## 產物與退出碼

| 檔案 | 用途 |
| --- | --- |
| `report.json` | 全部 iteration、失敗 traceback、三次 stat、校準讀值、環境、完整 Git SHA、來源雜湊、限制與退出碼 |
| `iterations.csv` | 每次 pass/failure/error/skip、耗時、三時間點 metadata；control 的採樣欄位留空 |
| `unittest.log` | 每次原始 unittest 輸出及 probe 最終 exit code |
| `ctime-readings.csv` | 校準原始讀值與相鄰 delta；校準未完成時不產生 |

probe 退出碼：

- `0`：要求的兩組案例都通過，而且採樣完整。只表示本次未重現。
- `1`：原測試有 failure 或 error；保留原始輸出，不因為是診斷工具就吞掉失敗。
- `2`：環境／工具錯誤、來源變動、未跑完、skip 或採樣不完整；需要先處理證據缺口。

預設在非 Linux 上退出 `2`。`--allow-non-linux` 只供工具開發檢查；產物標示 `linux_evidence: false`，不能拿來推論 Linux ctime。

工具固定原方法的 LF 正規化 SHA-256。方法有變時拒絕執行，避免採樣假設過期後仍產生看似有效的數據。若要用於後續 A 方案，必須先審查新方法的兩次 utime 語意、再更新對應的 hash 與採樣假設，並保留修法前後各自的來源雜湊。

## 如何判讀與交付

先分組列出 pass/failure/error/skip 與失敗率，再閱讀失敗 iteration 的 traceback、完整 metadata 及內容改寫證據。不要把不同 iteration 的失敗與 ctime 碰撞拼成同一個因果鏈。

只有同一次 observed 測試出現 `OSError not raised`，且確認內容已改寫、dev/ino/size/mtime 還原一致、after_restore 的 ctime 與 before 相同，才有證據支持預期的時間戳記碰撞機制。三次 ctime 全相同會提供更強的佐證；最終 ctime 不同或其他錯誤要另案分析。

- 兩組皆無失敗：寫「未重現，無法定論」，不能寫推測不成立。
- 僅 control 失敗：可以報失敗率，但沒有該次的三時間點資料；揭露採樣可能抑制失敗，不能宣稱已完成逐次因果驗證。
- 校準有零 delta：單獨不足以解釋測試失敗。
- 校準最小正 delta：只稱「本次操作下觀測到的最小正值」，不是已證明的核心最小刻度。沒有正 delta 時為 null，不能寫解析度為零。
- 負 delta：保留原值，說明可能有時鐘倒退或其他環境因素，不把它排除後宣稱整體正常。

交付 #212 時附完整 SHA、環境／檔案系統、原始 CSV 與 unittest 輸出、兩個退出碼，以及上述限制。若數據支持推測，再做 A（只修測試）與 B（修產品）的獨立草案；各方案都要用同環境的修法前後迴圈和移除修法的突變測試支持，不能只靠一次綠燈。

## 工具本身的合成檢查

```sh
python3 tests/diagnostics/test_binaries_ctime_probe.py
```

這些是採樣與報告管線的合成測試，不是 Linux 重現、native 驗收或 A/B 修法驗證；不加入或變更正式 runner 的測試期望數。
