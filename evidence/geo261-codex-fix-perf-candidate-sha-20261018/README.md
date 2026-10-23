【Codex】候選 SHA 效能修正：`57d916fb1d2c980769c3438172849bb3a3f03c00` 已完成新增測試 **73/73**、修前／撤回負控、正常量測、gprof 與相同微測試比較。修正分支為 `codex/geo261-fix-perf-candidate-sha-20261018`；本檔是待發布的證據報告，不代表已留言或合併。**bridge_integrity 兩側皆 24/24 功能通過，但 A/D 仍為 main 的 3.222 倍，未達 ≤2 倍效能門檻；完整驗收尚未重跑。**

A 保留完整快照，在完整 bytes 相等時延後 SHA；不同時仍雜湊保存原件與目前 bytes，不把篡改值當預期，不修改 const 封印。eager constructor、optional cache OOM 後備 SHA、必要配置失敗拒絕，以及 metadata／revision／狀態／完整 H snapshot 守門均保留。D 移除 World publish 中一次完整、重複的 `app_candidate_check`；正常成功路徑因此少做 before／after 兩次 H 快照檢查、一次 K 檢查及一次 live／before 相等比較。World 的 null／operation seal、泛用 H publish、K mark-published 仍保留。direct World 成本測試要求 H check=1、K check=2、provider metadata malloc/SHA 各=2；20 個判定情境、兩個 metadata OOM 點與持續 OOM 保留拒絕及重試契約。

| 測試來源／階段 | 實際結果 | 原始輸出 |
|---|---|---|
| `1492606c` A 初版 | 67 methods：64 過、3 新測試預期錯誤 | [stderr](tests/after-a-initial/command.stderr) |
| `dfb130e8` 修正測試預期 | 只重跑 product 4/4；未宣稱當時一次 67 全過 | [stderr](tests/product-after-oracle-correction/command.stderr) |
| `dfb130e8` 原回歸 | 5 suites、70/70 通過 | [stdout](tests/original-candidate-regressions/command.stdout) |
| `c00c9fc0` A00 撤回兩 policy | 1 method 的 create/bind 2 子測試真紅；exit 1 | [stderr](tests/withdraw-both-policies/command.stderr) |
| `dfb130e8` 恢復 A | 同一 method 通過；exit 0 | [stderr](tests/restored-cost-guards/command.stderr) |
| `169f1849` 只有 D 測試 | `ASSERT:publish-single-host-check` 真紅；exit 1 | [stderr](tests/before-d/command.stderr) |
| `57d916fb` A+D | 同次新增三套 73/73；unittest 29.261 s、外層 29.483 s | [stderr](tests/after-ad/command.stderr)、[三筆 D 子負控](tests/after-ad/command.stdout) |

初版三個失敗分類為**測試寫錯**：native 正控制已 exit 0，但 Python 誤要求合法 I8a preview stderr 為空。修正為固定 fixture 完整 **372 bytes** 的逐 byte 相等，負控仍要求同一前綴與精確 ASSERT，沒有刪除斷言或放寬任意 stderr。D 三筆 `D_CONTROL_JSON` 分別撤回 D、移除 operation guard、移除 H publish guard，實際子程序均 exit 1，精確斷言為 `publish-single-host-check`、`publish-operation-tamper-rejected`、`publish-host-after-tamper-rejected`，各方法隨後恢復正控制。這些是外層 73/73 期待的真負控，不是三個外層失敗。 A00 撤回提交 `c00c9fc0` 僅在本地、未推送；已附真實 [dfb→c00 差異](tests/A-withdrawal.patch) 與 [commit 原件](tests/A-withdrawal-commit.txt)，可依已公開的 dfb 來源重建同一撤回變更。七輪均無 timeout／interrupt；完整 SHA、argv、起迄與 raw hash 見 [results.json](results.json) 及 [歷史七輪清單](tests/A-D-evidence-list.json)。後者保留產生當時的草稿狀態；現況以本報告與新收據為準。

正常量測使用同一腳本 `46b806df…`、同一 room_a.scene `c3c0ba58…`、GCC 14.2.0／`-O2`、16 MiB stack；cold/model 各 7 次、resident 15 輪。A-only `dfb130e8` 與 A/D 各自正常 run，以及 A/D gprof run，都有完整 **305 samples、288 筆 bridge 成功回應、21 筆 model 有效輸出**；原始回應、樣本與 summary 已核對。A-only／A/D 各有同輪 main `e980cb0d` 對照。下表為 wall 中位數（ms）；全部分段見 [results.json](results.json)。

| 分段 | e64 | A-only | A/D | e64 ÷ A/D | A/D ÷ 同輪 main |
|---|---:|---:|---:|---:|---:|
| cold_start_dump | 1091.693 | 194.082 | 184.419 | 5.92× | 3.65× |
| load_scene | 831.183 | 97.292 | 92.893 | 8.95× | 3.42× |
| unused_spec_create | 86.643 | 11.550 | 10.884 | 7.96× | 2.36× |
| preview_spec | 81.040 | 6.652 | 7.213 | 11.24× | 2.17× |
| model legacy | 878.460 | 183.580 | 170.292 | 5.16× | 3.64× |

[A-only 正常 run](performance/artifacts-a-dfb130e8/runs/20261018T202803818534-normal/summary.json)、[A/D 正常 run](performance/artifacts-ad-57d916fb/runs/20261018T203438052503-normal/summary.json) 與相鄰原始收據均完整保留。**仍未回到 main 成本**；分段減少不代表 214 suites 或瀏覽器已全部通過。e64→A/D 還包含上游 `1987af507c6f387d7986325da6c29b2ec6246944` guide 修正，不能把全部差額單獨歸因 A/D；A-only→A/D 也只有一輪，preview 中位數並未再改善，不能包裝成所有分段單調變快。

[gprof 原始 run](performance/artifacts-ad-57d916fb/runs/20261018T203445910138-gprof/summary.json) 保留 **37 個 gmon.out**，七組 workload 各有完整 flat profile、callgraph 與 self／inclusive／calls 前 20。integration resident 的 `geo_sha_block` calls **53,019,413→12,842**，model legacy（7 程序合計）**15,304,688→3,731**。修前 SHA 是主要熱點，修後剩餘 self 取樣很稀疏；例如 resident 總歸屬已只有少量 0.01 s 級樣本。不能把 gprof 的 0.00 說成零成本，不能用其插樁 elapsed 算退化倍率；libc 的 memcpy／memcmp 等成本也不能靠此歸屬排除。

相同微測試工具、wrapper、compiler binary、合成 fixtures 與 room_a.scene 已逐 hash 核對；每側有 2 次 warmup、World／version_store 各 11 筆 SHA，9 個真候選。每次 SHA 結果均核對獨立 hashlib digest；原始 JSONL 與摘要相符。World 大小 4,759,192 bytes，version_store 535,560 bytes。World SHA wall 吞吐 **214.260→213.661 MB/s**，version_store **218.299→201.917 MB/s**；因此觀測到的是減少重複工作，不是 SHA 核心本身變快。

| 候選分段，wall 中位數 ms | e64 | A/D | e64 ÷ A/D |
|---|---:|---:|---:|
| create_and_9_bind | 37.367 | 1.645 | 22.71× |
| noop_evaluate | 36.186 | 1.113 | 32.51× |
| seal | 1.191 | 1.155 | 1.03× |
| publish | 3.810 | 2.092 | 1.82× |
| lifecycle_including_harness_checks | 80.111 | 7.321 | 10.94× |

[修前 microbenchmark](performance/sha-candidate-bench/results-e64-r1/summary.json)、[修後 microbenchmark](performance/sha-candidate-bench/results-ad-r1/summary.json) 保留 bench.c／measure.py、命令、compiler closure、hashlib fixture 收據與 stdout/stderr。noop 保證 **0 provider、0 node**，仍含空 metadata、配置／複製／比較，不能代表幾何來源圖成本。分段含讀時鐘開銷，lifecycle 另含 harness 檢查且不含輸出；`CLOCK_PROCESS_CPUTIME_ID` 是 CPU 時間，**不是硬體 cycles**。合成 `.bin` 不重複發布；inventory 保留大小、SHA 與逐 byte 可重建公式 `(131*i + 17) % 256`。

bridge_integrity 使用相同 `tests/test_bridge_integrity.py` 與 `tests/_bridge.py`（兩個提交的逐 byte SHA 相同）、同命令 `python3 -B -u tests/run_all.py --build --only py:test_bridge_integrity`。兩側都 24/24、exit 0，且 source/head/status 穩定。

| 來源 | unittest 真時間 | runner 顯示時間 | 含建置外層時間 | 原件 |
|---|---:|---:|---:|---|
| main `e980cb0d` | 33.819 s | 34.0 s | 51.229 s | [stdout](performance/bridge-integrity-main/command.stdout)、[unittest](performance/bridge-integrity-main/suite-logs/py_test_bridge_integrity.unittest.log) |
| A/D `57d916fb` | 108.959 s | 109.2 s | 135.845 s | [stdout](performance/bridge-integrity-ad/command.stdout)、[unittest](performance/bridge-integrity-ad/suite-logs/py_test_bridge_integrity.unittest.log) |

以同輪、同一 Linux 環境兩側的 unittest 時間相除，A/D 為 main 的 **3.222×**，**未達 ≤2× 門檻**；不能與其他環境先前約 10 倍的數字拼成改善倍率。功能斷言通過與效能驗收分開：本修正顯著改善成本，但不能稱效能全過；此處未用含建置外層時間算 suite 退化倍率。

A/D [build 原收據](performance/after-ad-build-invocation.json) 的 `prepare_argv` 因記錄器共用 list，後續 stage=build 誤改了原欄；[獨立 correction](performance/after-ad-build-invocation.correction.json) 保留實際 prepare/build argv 與原檔 hash，原檔未改，[stdout](performance/after-ad-build.stdout) 前兩行亦有來源 prepare 證據。此瑕疵不隱藏、不以重寫原始收據修飾。

修前 e64 正式資料已公開於報告提交 [`d5423381`](https://github.com/ZhiQiYang/geometry-axiom/commit/d5423381bcdfa7c67366bedca92eb47a06209879)，本 payload 不重複複製：[基準報告](https://github.com/ZhiQiYang/geometry-axiom/blob/d5423381bcdfa7c67366bedca92eb47a06209879/evidence/geo261-codex-validation-20261018/performance/phase3-performance-report.md)、[完整 408 檔精確清單](https://github.com/ZhiQiYang/geometry-axiom/blob/d5423381bcdfa7c67366bedca92eb47a06209879/evidence/geo261-codex-validation-20261018/performance/phase3-publication-inventory.json)、[正常 summary](https://github.com/ZhiQiYang/geometry-axiom/blob/d5423381bcdfa7c67366bedca92eb47a06209879/evidence/geo261-codex-validation-20261018/performance/artifacts/runs/20261018T200850689427-normal/summary.json)。完整 SHA 永久連結與檔案 hash 另見 [results.json](results.json)。來源封存只公開 manifest，產品來源以原提交永久連結查閱；不發布 ELF 或整包工作區。

環境：Debian 13、Linux 6.18.55 x86_64、GCC 14.2.0、Python 3.12.14、Node 24.19.0、Google Chrome 155.0.8059.84；本階段沒有跑瀏覽器。尚未完成：bridge_integrity ≤2× 效能門檻、修後全量非瀏覽器、六 browser jobs、Windows/MSVC/GDI、完整舊包 UI/native 驗收。既有 baseline 失敗／逾時仍需各自重驗，這份效能結果不能取代它們。

新增 **73 methods／3 suites 尚未更新 expected**；本分支不能當作 CI 全綠。最終全部修正完成後，仍須實跑完整 `python3 tests/run_all.py --build --update-expected`，再以普通 strict 全量 `python3 tests/run_all.py --build` 驗證；兩輪均保留 16 MiB stack 與完整原始收據，不能只改 expected 省略實跑。

文字勘誤：本次只釐清上文 D 的完整重複檢查範圍與同輪 3.222 倍的比較口徑；[原始報告 `875235e2`](https://github.com/ZhiQiYang/geometry-axiom/blob/875235e2227d93336b798d9b4548e2c2fa67c3fe/evidence/geo261-codex-fix-perf-candidate-sha-20261018/README.md) 保留可追溯原文。原始測試、效能、stderr 收據及其 hash 不變，本勘誤不增加任何已通過項目。
