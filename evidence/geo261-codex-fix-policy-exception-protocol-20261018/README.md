# PolicyIssue 標準例外協定修正與三證據

本分支修正產品例外 `PolicyIssue` 不相容 Python 標準 traceback 處理的缺陷。新增真實產品 cause-chain 回歸後，修前與只撤回產品修正時皆在同一具名斷言失敗；修後及恢復後完整模組各為 **9／9、零 skip**。正式 SPM38 在先前 `c4a04e0` 仍為 **blocked**；它在合流來源上的新 gate 結果尚未驗證，不能以這份報告宣稱 killed 或 full42 通過。

分支：`codex/geo261-fix-policy-exception-protocol-20261018`。基底 `a25d975bdcc809bc63593d5b434663083395444b`；測試支援提交 `82dd8dcc075b6b7a989ca16eeb67b04e8141f77e`；產品修正／兩輪綠燈來源 `a55b87d1a1f1a98bc5606148454961325b563478`；僅產品撤回控制 `a68eecbd24fadac295b1ea64dbc04aab8cb2b8c6`。

## 四輪真結果

| 階段 | 測試來源 SHA | 範圍 | 結果 | unittest 秒 | 外層命令秒 |
|---|---|---|---|---:|---:|
| [修前](before/command.stderr) | `82dd8dcc` | 新增單一 cause-chain 方法 | 1 run／1 FAIL | 0.026 | 0.314717 |
| [修後](after/command.stderr) | `a55b87d1` | runtime 完整模組 | 9／9 | 2.822 | 3.180047 |
| [僅撤回產品](withdraw/command.stderr) | `a68eecbd` | 同一 cause-chain 方法 | 1 run／1 FAIL | 0.024 | 0.315831 |
| [恢復](restored/command.stderr) | `a55b87d1` | runtime 完整模組 | 9／9 | 2.224 | 2.521518 |

四輪皆零 error、零 skip，無 timeout／interrupt／launch error；recorder 的 source、HEAD、status/diff 穩定欄位全為 true。兩個紅燈不是 import／setup／編譯錯誤，精確原文為：

```text
AssertionError: ('dataclasses.FrozenInstanceError', "cannot assign to field '__traceback__'") is not None : POLICY_EXCEPTION_STANDARD_PROTOCOL: ('dataclasses.FrozenInstanceError', "cannot assign to field '__traceback__'")
```

修前／撤回真命令：

```text
python3 -B -m unittest -v tests.test_geometry_kernel_runtime.KernelRuntimeTests.test_policy_error_cause_supports_standard_unittest_reporting
```

修後／恢復真命令：

```text
python3 -B -m unittest -v tests.test_geometry_kernel_runtime
```

這些時間只記錄功能驗證耗時，不作效能比較。[人工台帳](stage-review.json) 與各階段 `receipt.json`、`command.process.json`、stdout／stderr 保存完整 argv 和原判決。沒有新增或放寬測試 timeout。

## 根因與最小變更

`PolicyIssue(ValueError)` 自 `10cbda745bf9692e1108d6da3351d69ddf3a4306` 起以 `@dataclass(frozen=True)` 定義。frozen 生成的 `__setattr__` 不只禁止資料欄更新，也擋下標準例外的 `__traceback__`。Python 3.12 標準 unittest 在整理 chained cause traceback 時依法寫入此屬性，因而再次拋出 FrozenInstanceError，遮蔽原本已形成的產品拒絕及正式 mutation 收據。

[產品 patch](product.patch) 僅把該 decorator 改成 `@dataclass`；[撤回 patch](product-withdraw.patch) 精確反向還原此一行。保留原類別／ValueError 繼承、六個資料欄、建構子順序與 defaults、所有幾何／來源拒絕、H 的 `raise ... from error` 及原 cause；沒有改 mutation collector、放寬判決或移除第二層守門。

移除 frozen 同時使資料欄可寫、取消自動生成的 hash，不能說成只讓 traceback 可寫。固定來源的所有 PolicyIssue 產品引用已核：W 的 root admission、source binding、profile mesh／volume 拒絕，及 H 的欄位轉譯、cause chaining、診斷聚合；未找到以它作 set／dict key、依賴 hash 或要求該 exception instance 不可變的消費點。H ModelError、K EvaluationError 本來就是普通可寫例外。其他不可變 DTO、模型 wire、K／W 幾何演算法皆不變。

[測試支援 patch](tests-support.patch) 只在既有模組新增一方法；[固定 Git／AST 核對](source-review.json) 證明原八個 test 方法 AST 全同、測試支援／修後／撤回 test bytes 完全一致，且歷史 c4a 的兩個相關檔案與本次基底逐 bytes 相同。

新方法沿用既有 native fixture seam，修改 local_profile 的 metadata dimensions 10→11；typed region 仍為 10×2、length 30，真 K 幾何體積 600 與真 W metadata 體積 660 不符，經產品 W `PROFILE_VOLUME` → H ModelError 的真 raise-from 路徑。它沒有宣稱執行 C native adapter。未修改的標準 `TextTestRunner`／`FunctionTestCase` 必須正確記錄內層一次預期 ERROR；外層檢查真 H／W 類別、原 cause 物件身份、診斷欄位、root tuple→dict、traceback 及完整格式化報告。內層 ERROR 是預期被正確報告的產品拒絕，不是外層 suite 額外錯誤。外層只把 runner 崩潰表達為具名斷言，沒有替換或抹除產品 cause。

## 原 SPM38 證據與待驗邊界

本包逐 bytes 保存歷史 `c4a04e0792a795603e6e227651c369732885633c` 的 [SPM38 原 log](historical-c4a-full42/mutation-logs/SPM38.log)、[缺失收據紀錄](historical-c4a-full42/mutation-logs/SPM38.exceptions.json)、[完整 gate](historical-c4a-full42/gate-receipt.json)、[recorder 收據](historical-c4a-full42/receipt.json) 及 command 原流；[映射](historical-c4a-mapping.json) 記其原路徑、bytes、SHA。

原 trace 先出現 W `PROFILE_VOLUME`，H 保留 cause 轉成 ModelError，接著標準 unittest `_clean_tracebacks` 寫入 cause traceback 時觸發 FrozenInstanceError；正式 exceptions receipt 未完成，因此原工具判 **blocked** 正確。不能因 trace 曾出現期望 ModelError 就把這次改算 killed。歷史全42仍為 33 killed、3 survived（02／03／04）、1 unlabelled（20）、1 equivalent（24）、3 invalid（28／29／33）、1 blocked（38）；它是根因資料，不是本分支修後驗收。

待驗項：具備 12／16 工具遷移的同一合流來源上，重跑 SPM38 的真20項 model baseline／具名 terminal receipt／精確 cause 判決及其產品撤回控制；其餘 native mutation 問題分題處理，最終 full42 仍須完整重跑。本分支沒有修改 `run_all.expected.json`、mutation ledger 或四份架構產物；runtime census 8→9 及既有 W 檔 bytes 變更須納入最終 census／架構身份重建。本次也不宣稱新增瀏覽器驗收。

## 環境與公開證據範圍

Linux x86_64，Debian **13.6**（[OS 原文](os-release.txt)）；kernel 6.18.55、glibc 2.41；gcc 14.2.0（Debian 14.2.0-19）；Python 3.12.14；Node v24.19.0；Google Chrome 155.0.8059.84，另裝 Chromium 154.0.8037.57。四輪 child stack 皆 **16 MiB**。工具版本 stdout 隨各階段公開，版本資訊不代表本題執行瀏覽器或 C 編譯。

共用嚴格 collector 只整理既有收據與人工 claim，未執行產品、不自行判定 kill。[results](results.json) 與 [inventory](inventory.json) 列公開原件精確 bytes／SHA；inventory 自身另列，避免自指。持久 binary/sidecar 是 recorder 環境觀測，不冒稱本題 pure-Python fixture 曾執行那些 binary；方法內的既有子程序控制只主張 unittest 方法已通過，不外推未分別保存的 transient 子程序 raw。

原 recorder `.py` 與各大型 `before/after.source.json` 仍保留外部，不改名混入 payload；公開 receipt 保留其身份值，公開包不能自行重算未公開的全來源清單。歷史全42同樣不公開工具源碼或大型 source 快照。所有新寫檔僅為證據文件，原測試 raw 保持不變。
