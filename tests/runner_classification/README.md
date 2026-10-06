# #118：parent test 結果分類

現有 reporter 以 failure/error/skip **事件數**當作 parent test 數：同方法兩個 failing
subtest 得到 `failed=2/total=1`，body failure 加 tearDown error 也被計兩次。
`expectedFailures` 未分類，反而得到 `passed=1`；`run_all.py` 直接採信這四個總數。
這是結果分類錯誤，不代表幾何 oracle 或整個產品流程無效。

基準來源：main `11dc339152e05ea811972b8c0c15ff29520207cd`。
基準位置：`tests/_unittest_runner.py:224–262`、`tests/run_all.py:513`。
修正候選的實際 bytes 指紋與基準指紋在 `evidence-manifest.json`；PR head 保存相同被測程式。

## 最小修正與契約

`_ParentResult` 按每次 `startTest` 分類一次，保留 unittest 原始事件與文字 log。
failure/error/unexpected-success 優先於 skip；同 ID 或同 instance 的重複執行仍各算一次。
class/module setup error 依 scope 去重，優先於同 scope skip；setup 未跑項目仍屬 blocked，
tearDownClass/module error 保留既有 extra_errors 契約，不扣已成功 parent 的 passed。

expected failure 明示於 `expected_failed`／`expected_failures`，並投影到既有 `skipped`
欄位，以免未改的 consumer 將它當 pass。其 scope 是 `expected-failure`，不會拿到
platform allowlist credit。純 expected failure 的 reporter exit 仍為 0（unittest 契約）；
aggregate 的預設 strict 判斷因此是 skip／exit 3，不能宣稱全過。
既有 `--allow-skip` 仍是顯式放行 skip 的模式，會放行此類結果且聲明非全部跑過。
若未來要讓 expected failure 在該模式也必紅，應由 consumer owner 明定政策，不能靜默更改。

每筆 subtest failure／skip 明細均保留。對已失敗 parent 或重複 skip 的明細使用
`count=0, scope=test-detail`；既有 allowlist 只讀 scope=test，因此零 count 明細不會取得豁免。
文字 trace 仍在原始 unittest log。此處沒有改 freshness、skip 豁免、timeout、golden 或產品。

## 紅綠證據

同一組固定合成 fixture 使用真 unittest 與 subprocess，不執行產品 suite，也不建置 native binary。
原始 fixture、JSON、文字 log、實際 argv／exit／wall time、獨立 reviewer probe 收在 `evidence.zip`，
由 `evidence-manifest.json` 逐檔記錄 SHA-256。收據與程式路徑均為這輪隔離 TEMP。

| 驗證 | 結果 | command exit | wall time |
|---|---|---:|---:|
| 精確 main reporter，29 個固定情境 | 15 符合／14 不符；consumer 偵測 xfail 誤充 pass 與 failed parent skip 誤拿 allowlist credit | 1 | 2.832 s |
| 修正 reporter，同 29 個情境＋真 consumer parser／allowlist probes | 29/29 符合，consumer probes 通過 | 0 | 2.933 s |
| canonical reporter 跑新專項回歸入口 | total/run/pass=1，fail/skip=0 | 0 | 2.616 s |
| 獨立 reviewer 另寫的 24 個情境 | 24/24 符合，無阻擋項 | 0 | 未記錄整體 wall time |

14 個不符包括新增 metadata 在舊版不存在，不能解讀成 14 個獨立產品 bug。
情境包括 normal、兩 fail subtest、failure＋error、fail＋skip 的兩個順序、兩 skip、
expected failure／unexpected success、class/module/import skip、setup error、tearDown error、
同 ID／instance 重複執行、setup＋cleanup 多事件、45 筆 failure／205 筆 skip 明細及 0 tests。

實際命令（cwd 為隔離 repo；清除繼承的 GEOMETRY_*，PYTHONDONTWRITEBYTECODE=1）：

```sh
python3 tests/runner_classification/verify.py --runner /tmp/issue118-reporter-20261006/baseline/tests/_unittest_runner.py --out /tmp/issue118-reporter-20261006/red-v3
python3 tests/runner_classification/verify.py --out /tmp/issue118-reporter-20261006/green-v3
python3 tests/_unittest_runner.py tests/test_unittest_runner.py --json-out /tmp/issue118-reporter-20261006/registered-gate.json --log /tmp/issue118-reporter-20261006/registered-gate.unittest.log
```

日後重跑 `verify.py --out <新的TEMP目錄>`；已有目錄會拒絕覆寫。
正式 aggregate 新增 `py:test_unittest_runner`，僅 **1 parent test** 呼叫此矩陣。
`PY_NEEDS` 只追加 `[]`，expected 只追加 count=1。此次依授權不跑全庫或
`--update-expected`；該 count 由實際 canonical reporter 收據與 loader 確認。
全部既有 expected entries 逐筆完全相同，registry check 無錯誤。

## census、效益與未驗

獨立 AST census 在精確 main 找到 46 registered Python suites：800 靜態方法＋18 動態
modeling vectors＝818 parent tests；各 suite 均符合既有 expected。34 suites 有 207 個
subTest call sites，屬於 187 個 parent methods，expectedFailure 使用數為 0。
修正不改這 818 個發現數；追加 reporter gate 後為 819。目的在消除虛假通過與重複失敗計數，
不是增加產品覆蓋宣稱。

本次未跑全庫、browser、geometry main flow、Windows CPython/GDI、WSL 或 hosted CI。
沒有量測 aggregate 加速；2.6 秒是新增隔離分類 gate 的成本，不能當產品或 CI wall time。
沒有更動舊 #142/#134/#137/#143 held packages，也沒有重跑舊 #136 head。
