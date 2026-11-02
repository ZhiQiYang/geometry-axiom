# #366 integration 原件獨立核收

範圍：既有 integration run `41376852060` 已完成的六組 browser、三片 native、native complete coverage；終態 job snapshot 為 `api/20261102T025323Z/integration-jobs.json`。只讀 `/tmp/geometry-resume-20261102/pr366/` 已下載 API snapshot、job log 及官方 ZIP 解出原件；沒有打 API、執行產品測試或下載二進位、修改 source、另啟 CI、push 或留言。官方 ZIP digest 由主核收代理先驗，本輪獨立逐項核讀內容並保留各輸入 SHA-256。

結果：本輪未見異常假綠。原執行 checkout 是 PR 合成 merge `7d2a1927e15d3c0d59b20fa6618005f19c4a6c56`，log 明示將新 head `502a64ff6214dd6060927b7f14643a533536f20d` 合入 base `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`。這不是 mutation workflow 專用的 PR head checkout，也沒有沿用舊 `df347` 綠燈。

## 六個 browser job

| 組別 | Job ID | 原逐條通過數 = result marker | 失敗 | 略過／範圍 |
|---|---:|---:|---:|---|
| assembly | 125058860539 | 150 | 0 | `skipped=[]`；P77=134、P82=16；partial，未比 golden |
| grid | 125058860586 | 356 | 0 | `skipped=[]`；P70=121、P71=9、P78=23、P87=60、P88=143；partial，未比 golden |
| documents | 125058860505 | 47 | 0 | documents 專用完整 runner；marker 沒有獨立 skipped/completed 欄 |
| space | 125058860545 | 242 | 0 | `full-space-suite`；略去 timber 兩組，由 timber job 覆蓋 |
| timber | 125058860472 | 79 | 0 | `GEOMETRY_TIMBER_ONLY` partial；timber-material=48、source-guards=8，另 setup/font/browser-health |
| canvas | 125058860626 | 2267 | 0 | full；85 段逐段精確比對 golden；`skipped=[]` |

逐條原 log 的 `PASS` 或受控 `✓` 判定計數均精確等於唯一結果 marker；每個 actual browser regression step 的 API 終態為 success，workflow 原封不動傳出 runner status，沒有 GitHub error 行。六組皆確認 runtime `fresh:true`；space/timber 每個 group 都 `expected=passed`、failed=0、completed=true，completenessProblems、exceptions、consoleErrors 都空；assembly/grid completed=true、uncaughtBrowserExceptions=0。documents 最後兩條實際斷言為無 uncaught exception、無 asset request failure，47 條全部通過才印成功 marker；原 runner catch 路徑會設 process.exitCode=1。

canvas 原 log `3191–3195` 明示 `CDP_SECTIONS 85 段,合計 2267 通過斷言`、`[CDP FLOOR] 與 golden 逐段相符(85 段)`、2267/0/0 full，以及唯一 `CDP_RESULT` completed=true、scope.mode=full、filters=[]、modifiers=[]、goldenCompare=matched。獨立 checker 再將原逐條受控 verdict 依段重數，精確等於 85 段 marker 與已提交 `geometry-web/cdp_sections.golden.json`，總和 2267；沒有更新 golden。full legacy log 同一行可含多個判定，且診斷 JSON、`status:` 顯示文字、undo 尾端狀態也可能帶勾號；這些顯示文字依原 `assertionVerdicts` 語義排除，沒有用所有可見勾號粗算斷言數。

canvas 的 `uncaughtBrowserExceptions=1` 必須原樣保留：原 log `950` 唯一 `[EXPECTED EXCEPTION] Error: fb-auto-probe`，接著 `952–953` 為 P38 自動回報及預期單次例外已抵達的通過斷言；原 `cdp_test.js` 明示設定 expectedException 再丟出此 probe。沒有 `[UNEXPECTED EXCEPTION]`。其 firstTransportFailure 的 surfaces/P53 來自原測試注入 partial/malformed/403 回應，後續重試／快取保全斷言全通過；firstNetworkFailure 保留 P61 的 `line spec receipt_probe 10`、`net::ERR_ABORTED`、canceled=true，該段原碼注入 lost-reply，原回執恢復／世界回滾斷言通過。本核收不把這些非空原始欄位改寫為零錯誤。

assembly 的 `firstTransportFailure` 非空，但確切錯誤為 `Injected lost success response`。原 `geometry-web/assembly_review_test.js:21` 明示在真實伺服器完成提交後注入此錯誤，原 log 亦完成回執恢復／未知結果保稿的後續斷言；這是測試故障注入，不應抹去原欄位，也不應誤報為未通過的實際網路故障。Chrome startup 的 D-Bus stderr 及 Actions Node 20 棄用 warning 有保留；它們沒有伴隨產品 console／uncaught error 或失敗斷言。

六個 job 的 assertion 通過數合計 3141（含 full canvas 與獨立 partial job 的重複覆蓋），屬混合真實瀏覽器輸入、DOM/API 整合斷言，不稱作 3141 個不重複或完整 E2E 情境。canvas full golden 本輪已有自己的終態完整證據。

## 230 個 native suite

| 片 | suites | 計數測試 | 通過 | 失敗 | allowed skip |
|---|---:|---:|---:|---:|---:|
| 1 | 77 | 1726 | 1725 | 0 | 1 |
| 2 | 76 | 1747 | 1747 | 0 | 0 |
| 3 | 77 | 1867 | 1867 | 0 | 0 |
| 聯集 | 230 | 5340 | 5339 | 0 | 1 |

三份 shard receipt 的 universe 相同，selected 與實際 rows 精確相等，跨片 230 個 suite 恰好各一次，無重複、缺漏或額外 ID；所有 rows 都 ran=true、process_exit_code=0、failed=0，沒有 env_problem、crashed、expected_problem，registry_errors／expected_problems 空。原三個 job log 的最後合計列分別與 1726/1725/0/1、1747/1747/0/0、1867/1867/0/0 精確相符；aggregate job 原 log 的完整 JSON 亦等於官方 artifact JSON。

- 194 份 Python receipt：每份 JSON.total/run 與原 `*.unittest.log` 唯一 `Ran N tests` 一致且非零；每份 row 的 total/passed/failed/skipped 與 JSON 一致，原 unittest 結尾 OK。沒有 unrun_skipped、blocked_by_error、expected_failed、import_error、extra_errors 或失敗項。
- 唯一 skip 為 `py:test_gdi_contract`，1 個測試在 Linux 因 `requires compiled Windows GDI contract harness` 明確 skip。原 raw 為 `s`、`Ran 1 test`、`OK (skipped=1)`，receipt 也保存同一理由；不將這一個測試計入通過。
- 32 份 Node suite 原 log：有計數者的 tests/pass/fail/skipped 精確等於 receipt；direct canvas 為 408 pass / 0 fail。明示 exit-only 的 helper suites 不捏造測試數。
- `c:integrity` 原 log 第一行為 `432/432 integrity checks passed`，core 原完整結構化結果為 166/166、fail=0、infrastructure=0，166 個 cases 皆 pass；framing 原 log 完成 8137 次 CI 抽樣建構且零檢查失敗。
- native `mutation:check` 原 log 為既有帳本的 strict 只讀核驗：123 records，114 killed／1 crashed／5 equivalent／3 retired，stale=blocked=0。它不能替代另一 mutation run 對新 head 的 120 active 真實執行證據。

## 移除 c:integrity 的真實紅燈

官方 `native-complete-coverage/native-sharding-proof/` 原件保存 baseline／removed／restored 各自 JSON 與 raw log。三次實際退出碼為 0／1／0；各跑指定原覆蓋測試一次、errors=skips=0。

`removed.log` 的唯一失敗為 `test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once`，有實際 traceback 及 `AssertionError: Counter(...) != Counter(...)`，訊息「分片必須完整涵蓋原套件清單，且每個suite恰好一次」，最末 `FAILED (failures=1)`。removed receipt 明確 `removed=["c:integrity"]`；baseline／restored 原 log 都是同一測試 `... ok` 及 `OK`。這證明原覆蓋測試能殺掉實際少一個 suite 的分片，而非把 error／skip 冒充 mutation killed。

## 可重核指令、退出碼與 hash

本輪獨立 checker 只解析既有 JSON/text、計數與計算 SHA-256，不 import repository 程式、不編譯或執行任何產品測試／artifact binary：

```sh
python -B /tmp/geometry-resume-20261102/pr366/check_downloaded_native_browser.py
```

退出碼 0；`passed=true`，1403 個 evidence assertions；194 Python receipts、32 Node logs。`independent-native-browser-check.json` 保存完整 marker、來源 SHA、逐檔 hash 與核對結果。此 checker 本身及 JSON 的最終 hash 可用 `sha256sum` 重核；所有 642 個已讀原件／來源工具檔的 hash 在 JSON 的 `input_sha256`。

重要原件 SHA-256：

| 原件 | SHA-256 |
|---|---|
| `check_downloaded_native_browser.py` | `da961cd5d4d6d0dd4d06224633eabcbc1c2b0460817b9c4e2305d34d80863852` |
| `independent-native-browser-check.json` | `a8984334f26a430ca51fe3df8870570ebead607566cbb3ca8c6609dfe38ed2b4` |
| `job-logs/125058860626.txt`（canvas 原 log） | `d3c3cb3ba7cf70f2c44dc1cdb5bfd37192a2f3631af34dc611d689b6a89b6abc` |
| `native-sharding-proof/removed.log` | `1fd69c999a848613e2aa1065f7bc39192f3107c8c2ddd38d11322eb4ec56050f` |
| `native-sharding-proof/receipt.json` | `107efd037037fd00ca23ea06efc659cfefffe8f116acd257893ac094335d5410` |
| `native-complete.json` | `eaa4792b38f80d7b6927d4883e4a784e9577ed586e8cdcb226d903aabf3b38c3` |

未驗範圍：本輪沒有視覺檢視截圖，也沒有替主核收代理重下載或重驗官方 ZIP digest。這份獨立核收涵蓋 integration 十個 success job；另一個新 mutation run 的完整執行與 aggregate 由主核收代理另驗。
