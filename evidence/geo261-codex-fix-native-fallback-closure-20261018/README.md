# GEO-261／17：修復未設定 adapter 時的來源閉包掃描

`model_native` 的預設建置在 compiler 啟動前，會把 K 所有的 `geometry.h` 誤找成引用檔旁的不存在路徑。分類為 **產品回歸**：`c9e84b629231c96177712e6504859ada703a8399` 抽入 H 的保守 quoted-include 掃描只用了引用目錄。修正先找引用檔目錄，再找明確 K 根；仍找不到就拒絕，不加假標頭或借既有 binary。此題四輪證據已完成；本資料包目前是待發布候選，不表示 PR 全量通過。

基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`；自有分支 `codex/geo261-fix-native-fallback-closure-20261018`。只加測試的提交為 `8d0bf4258341dff5176f4035eda98145f0506e0a`，產品修正為 `13e0fe8f4c32c4d97f3a35111a4a2cc46bfb30c2`。本地撤回控制 `b9bad6792d426d28d66b875ec0d4cac45dbf57d2` 只撤產品，測試 bytes 全留；最後恢復到同一 `13e0fe8f…`。

## 實際結果

| 輪次／原始 stderr | 測試 SHA | 實跑結果 | unittest 秒 | 外層命令秒 | exit |
| --- | --- | --- | ---: | ---: | ---: |
| [修前](before-tests-support/command.stderr) | 8d0bf425 | 1 方法／1 failure；具名 closure 守門轉紅 | 0.002 | 0.320977230 | 1 |
| [修後完整 suite](after-full/command.stderr) | 13e0fe8f | 30／30，零 skip | 26.293 | 26.611272507 | 0 |
| [只撤產品](withdraw-product-only/command.stderr) | b9bad679 | 同 1 方法／1 failure、同 marker | 0.003 | 0.314639027 | 1 |
| [恢復完整 suite](restored-full/command.stderr) | 13e0fe8f | 30／30，零 skip | 25.046 | 25.354827789 | 0 |

四輪均無 timeout／interrupt／launch error，receipt 的 source／HEAD／status-diff stable 均真；父命令 stdout 都空，原 unittest 原文在 stderr。直接 unittest 沒有 run_all suite logs，`run_all_logs_complete:null` 不被寫成 true；兩個完整輪次並非 runner 全量。

修前與撤回都實際執行 `NativeUnityClosureTests.test_guarded_standalone_header_uses_its_actual_kernel_owner`，在方法內捕捉 `FileNotFoundError` 後產生：

```text
AssertionError: UNITY_CLOSURE_MUST_RESOLVE_OWNED_K_HEADER: [Errno 2] No such file or directory: '/tmp/geo261-native-cache-…/geometry.h'
Ran 1 test …
FAILED (failures=1)
```

完整含隨機目錄及 traceback 的原文以上述 raw stderr 為準。這是測試方法內的具名失敗，不是 setup/import/compile error。先前 `scenario-bounds/before` 在 `b9195094…` 得到的 `Ran 0 tests`／setUpClass `BASE_COMPILER` 只屬原症狀線索，不拿來冒充本題有效負控。

## 修正與保留的守門

[source-fix.patch](source-fix.patch) 是固定 e9→13e0 的原 Git diff，僅改 `geometry-app/geometry_app/model_native.py` 與 `tests/test_geometry_host_native.py`。產品新增私有 `_project_include_dirs`，只改原 `_project_source_closure`；其他原產品函式 AST 全等。解析仍以本地檔優先，再用 `geometry-core/kernel`。沒有新增 compiler `-I`、任意搜尋根、多 object 路徑，沒有移除 freshness／cache／source／binary identity 判準。

原三測試類的 AST 全等：12 個 build 方法、9 個 runtime 方法、1 個 guard-control 方法仍在；新增 7 個 closure 方法及 1 個真 fallback 方法，合計 30。guard-control 方法仍固定原 21 方法 baseline／restored 與 5 個單點守門控制，外層方法兩輪均為 `ok`；不把 21 說成 mutant 數，也不宣稱另有逐子程序的完整公開串流。原 compile 60 秒與 scene 20 秒上限不變。

兩輪完整輸出都明列 `test_unconfigured_fallback_builds_and_executes_a_fresh_real_adapter ... ok`。其固定來源會移除 `GEOMETRY_MODEL_BASE`／`GEOMETRY_MODEL_BASE_WSL_DISTRO`，隔離空 cache 和新 temporary directory，真編譯 adapter，再經公開 `load_base("")` 執行；驗 schema、精確 `base_scene == "\n"`、空 solids 及 cache 重用。沒有 mock compiler／subprocess 或修改真產品來源。

各輪 receipt 可直接證明 `CC=cc`、`GEOMETRY_MODEL_BASE`／`PYTHONOPTIMIZE` 未設。recorder 的環境白名單不含 WSL override，故不以 receipt 缺 key 推論外層也 unset；真 fallback 方法本身移除兩 override 的固定 source 是該項證據。真 adapter 在測後清除，本包未獨立封存每一支短命 adapter／mutant binary 的 bytes、hash 或子程序串流；公開一般 binary sidecar 不冒充它們。

來源責任依固定 e9 的 SSOT 分層段落（`公理層.md:63–79`）與 I32（1455–1457）的能力須有實際證據要求。本題只恢復既有 H 組裝／建置路徑，不改 K/W 規則或公理，不需要自行決定新條文。保守掃描含未啟用的 conditional include；未主張原 compiler 已實際需要新增 `-I`。

## 環境與未驗範圍

Linux 6.18.55 x86_64／glibc 2.41；gcc 14.2.0、Python 3.12.14、Node v24.19.0、Google Chrome 155.0.8059.84。實際 stack 為 16 MiB；本題未跑 browser，Chrome 版本只作環境記錄。

`tests/run_all.expected.json` 與 `tests/mutants_results.json` 被原 recorder 列為來源輸入且前後不變；本題沒有預寫 census 22→30。新增 8 方法仍須在最終固定合流來源以真正完整 `--update-expected` 產生、人工審核，再跑 strict full。Windows/MSVC/WSL override、任意 compiler 搜尋旗標、多 object 建置、六 browser jobs 與全量整合均不是本題驗收結果。

公開集合由既有 common collector 整理，人工判讀保留於 [results.json](results.json)，逐檔原件身份見 [inventory.json](inventory.json)。大型 before/after source maps 與 recorder Python 原碼不複製，省略項的原 SHA／bytes 由 receipt 轉錄而未在封裝時重算；不把完整性觀測升格成額外測試。原始命令、退出／時間、環境版本、binary sidecars 與具名紅燈原文全部保留。撤回的 [patch](withdraw-product-only.patch) 與 [commit 原文](withdraw-product-only-commit.txt) 保留供審查。
