# scenario worker 容量守門修正

分類：產品缺陷／GEO-261 重構回歸。基底為開題時最新整合提交 `1987af507c6f387d7986325da6c29b2ec6246944`；自有分支 `codex/geo261-fix-scenario-bounds-20261018`，測試入口提交 `b9195094225982dc712c4d7711b65663395f0315`，產品修正提交 `7575ad303aaf02190dc4043e36100adf724b0873`。

`c9e84b62` 把 native 傳輸移到 H 的 `geometry_app.model_native`，正式 worker 卻仍重新綁定舊 facade 的 `subprocess`。真正函式因此沒有使用容量受限的 adapter。現在正式入口直接暫時綁定 H owner，並在 `finally` 還原；私有故障 helper 改經真 `main --model-worker`，避免測試自行安裝 adapter 而掩蓋產品漏接。

原 37 個測試方法及其斷言不變。stdout 16 MiB、stderr 64 KiB、stdin 9 MiB、原 timeout、`<3s` 與 0.5 秒子程序清理判準全部保留；未截斷輸出或放寬錯誤。I31／I32／I33 支持整包拒絕、能力與容量分類；上述數字仍是原工程契約，不宣稱來自條文。

| 階段 | 被測 SHA | 定向結果 | unittest 秒／外層秒 |
| --- | --- | --- | ---: |
| 修前，保留加強 helper | `b9195094` | 2 方法；容量方法兩個 descriptor 均 ERROR，清理方法通過 | 46.857／47.165 |
| 修後 | `7575ad30` | 2/2 通過 | 11.845／12.113 |
| 只撤產品接線，保留 helper | `3e229a2f` | 同一容量方法、同兩個 timeout ERROR；清理方法通過 | 20.339／20.650 |
| 恢復產品修正 | `7575ad30` | 2/2 通過 | 11.741／12.034 |

修前與撤回的原文為 `geometry_app.model_common.ModelError: Isolated verification exceeded its execution budget.`，堆疊抵達 `SCENARIO_NATIVE_TIMEOUT`。修後容量方法要求兩個 descriptor 均為 `SCENARIO_NATIVE_CAPACITY` 且小於 3 秒；另一方法驗證逾時子程序不能稍後完成。逐行原始 stdout／stderr、真正 argv／退出碼／耗時與完整 recorder receipt 隨各階段附上。

四輪皆使用同一命令與經 registry 驗證 fresh 的 bridge／model-base：

```sh
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge \
python3 -B -m unittest -v \
  tests.test_scenario_verify.ScenarioNativeAcceptance.test_model_base_stdout_and_stderr_are_bounded_inside_worker \
  tests.test_scenario_verify.ScenarioNativeAcceptance.test_model_timeout_stops_its_base_child_before_it_can_finish_late
```

recorder 為 child 設定 16 MiB stack；來源、HEAD、status/diff 前後均相同。撤回提交 `3e229a2fa6280abcce6dca561aaf947ae1ad694f` 僅為本地負控，不推送；附 `withdrawal.patch` 與原 commit 文字供重建該差異。修正分支的證據提交與被測產品 SHA 分列，沒有將未執行的證據提交改稱被測 SHA。

另保留第一次未設 `GEOMETRY_MODEL_BASE` 的 `before` 輸出：0 方法、setUpClass 錯誤、exit 5，因 fallback closure 誤找 `geometry-templates/woodworking/native/geometry.h`，報 `BASE_COMPILER`。它不算本題容量紅燈，另列自動建置問題處理；不能隱藏或冒充上述三證據。

環境：Debian 13.6、Linux 6.18.55 x86_64、GCC 14.2.0、Python 3.12.14、Node 24.19.0、Google Chrome 155.0.8059.84。各工具原版本輸出及 native binary／sidecar 身分另附。

未驗：此修正的完整 scenario 37 方法、modeling runtime／transport、合流後全量與瀏覽器仍待最終候選驗收；本報告只宣稱上述兩方法與撤回證據，不把修前 e64 的 37 方法收據當成修後結果。原始 e64 全量已有 37 方法中 1 方法失敗、2 個 subTest errors，見 PR #288 第一階段報告。
