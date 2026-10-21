# L 完整 native 驗收收據

本輪通過。固定產品來源為 `43f85313c32410ac01406ab585846bbacafea278`，工作樹為 `/workspace/geo261-native-l`（detached）。開始與結束均為同一 SHA、乾淨工作樹；四個指定測試／裁判來源的雜湊前後一致。本代理沒有修改產品或測試，沒有 commit／push。

## 實際命令與結果

cwd 為 `/workspace/geo261-native-l`，正式內層 argv 完整為：

    timeout 2100 python3 tests/run_all.py --build

父環境以 `env -u CC -u PYTHONOPTIMIZE` 啟動。wrapper 設定 `PYTHONDONTWRITEBYTECODE=1`、`LANG=C.UTF-8`、`LC_ALL=C.UTF-8`、`TMPDIR=/tmp/geo261-native-l-43f85313` 與 16 MiB stack。正式日誌確認 `CC=未設定`。`TMPDIR` 只隔離 tempfile；`tests/binaries.py` 的 POSIX 輸出仍固定為 `/tmp/geometry-tests`，suite 原日誌為 `/tmp/geometry-tests/run_all-logs`。

- 開始：2026-10-20T23:39:12.072242Z。
- 結束：2026-10-21T00:10:47.374057Z。
- 主 timeout、subreaper wrapper、父 launcher、tool session 的真實 exit 均為 0。
- 含 build 總耗時：1895.301800551 秒；原定 2100 秒上限沒有延長。
- 完成 224／224 suites；表列與 expected 逐項相符，缺失日誌 0。
- 計數合計 5176；pass 5175、fail 0、skip 1。另有 7 個 exit-code-only suites，沒有冒充斷言數。
- 唯一允許 skip：`py:test_gdi_contract` 的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`，原因為 `requires compiled Windows GDI contract harness`；不允許 skip 為 0。
- 原始 suite `.log`／`.json` 共 600 份、296101 bytes，逐 byte 複製並保存 SHA-256、來源路徑與 mtime；沒有本輪開始前的舊檔。

`verification.json` 保存完整 224 項表列、expected 核對、Python failures、具名 skip 比對與原收據雜湊。`named-required-suites.json` 額外具名保存 `py:test_architecture_contract` 205／205、`py:test_product_architecture` 18／18、`py:test_geo261_model_base_replay` 6／6，以及 `mutation:check` 的 exit-only 結果；兩個架構 suite 的六份 JSON／log／unittest.log 都連回本輪 `suite-log-source-index.json`。`all224Passed` 表示完整 aggregate 判準成立，仍保留上述 skip 與 exit-only 分類。

## 來源、程序回收與 binary 保存

啟動前已將既有 `/tmp/geometry-tests` 全目錄原樣移至 `/tmp/geometry-tests-before-native-l-43f85313-20261020T233737Z`，825 個檔案／links、12119670 file bytes，移動前後雜湊逐一核對。詳細清單在 `launcher/prior-global-artifacts.json`。本輪從空的 global 輸出目錄實際重建六個 native binary；Windows GDI 在此平台為 n/a。

初始與最後 binary／fingerprint 原件留在外部 `/workspace/geo261-evidence/native-l-binary-preservation/initial-build` 與 `final`；本證據包保存兩組 fingerprint 原文與索引，不混入 binary。12 個 artifacts 的 bytes 與 mtime 前後均不變。最後 bridge SHA-256 為 `1dde99f08755c785223bceb3a733ad999311749d8eb5e0be16e1fc7daeb5ed0b`；sidecar SHA-256 為 `91a510bf879ff7e3c57e44c44f830a3fd947cfca80faddf07a3d0801bea772d5`。這是後續 Q38 使用全域 bridge 前的同 L 原件，不宣稱 Q38 不依賴全域 binary。

外層只在自己的子樹設定 Linux `PR_SET_CHILD_SUBREAPER`，以真實 `waitpid` 回收孤兒；沒有修改測試或忽略 zombie。主 timeout 子程序的結果獨立保存，不被收養子程序的 signal exit 覆蓋。主程序結束後才清理由此 wrapper 收養的直接子程序，不延長測試的 35 分鐘驗收期限。本輪沒有額外 cleanup kill；13 個本輪已知 PID 在結束後均不存在。原始 wait status 與事件見 `reaped.jsonl`／`reaped.json`，清理核對見 `cleanup-verification.json`。

完整實際 argv、wrapper 全文與原碼雜湊見 `command.json` 及 `launcher/launcher-command.json`、`launcher/wrapper-code.txt`、`launcher/launcher-code.txt`。父 launcher 將 stdout／stderr 直接寫入獨立 `orchestrator.log`，真 `wait` 後保存 `.exit-code`、`.launcher-exit-code` 及 `launcher-receipt.json`；不只依賴 tool transport 的最終碼。一次唯讀 `/proc/*/environ` 採樣被權限拒絕，已記入 `launcher/actual-process-preflight.json`；沒有聲稱成功讀取。環境 absence 以實際啟動 argv、同環境 preflight 與 run_all 自報為證。

## 突變自證與外部封裝修正

`mutation:check` 本輪正式 exit 0，帳本 78 筆／紀錄 78 筆，killed 70、crashed 1、equivalent 4、retired 3、survived／invalid／stale／blocked 均 0。M20 的 crashed 保留原分類，沒有計作斷言 killed。這個入口驗證 inventory freshness，不等同在本輪重跑全部突變。Q38、裁判 controls、整卡 53 案與版本 V01–V05 的同 L 實跑須另行取得收據，本 native 收據不代替它們。

歷史原環境 plain 控制 exit 1、subreaper 控制 exit 0 的診斷原件在 `../native-first/環境診斷`，仍標其真實歷史來源；本輪 L 的 `py:test_assembly_mutation_check` 12／12 實際通過，不以歷史單測替代本輪完整驗收。

正式 native 只執行一次。第一次外部收據解析器用 `\s` 匹配欄位空白，跨換行吞掉交錯列，誤解析為 116 列並 exit 1。原碼、原衍生結果與失敗收據保留在 `packaging-attempt1`；第一次 stdout 只有 tool 回傳且可見輸出曾截斷，沒有冒稱完整 stdout 已落盤。改用水平空白後，對同一原始 run.log 與已保存 raw 重新核對，得到 224 列、expected mismatch 0，封裝檢查 exit 0。第二次完整 stdout 在 `packaging-final.log`；沒有重跑正式 native、改 raw 或放寬驗收條件。

## 未驗項目與最大不確定性

本收據只涵蓋 run_all 登錄的非瀏覽器 aggregate；正式 owner／browser 獨立門檻名單保存在 `run.log` 與 `verification.json` 的 `separateGatesNotice`。六個正式瀏覽器入口、Q38／整卡／版本突變及 P-189 應查各自同 L 的實跑收據。本輪前段與五個依序 browser 驗收並行、後段獨占，耗時不當作 P-189 或 P52 效能證據。

未在 GitHub CI、Windows 或 WSL 重跑；Windows GDI 的允許 skip 不代表其通過。最大不確定性是其他 runner 的 init／subreaper 回收條件與此環境是否一致。本輪的結論限於固定 L、所列環境與完整原始證據。
