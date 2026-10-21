# R2 完整 native 重跑收據

本次 R2 判定：**通過**；本收據不是後續 P73 產品修正的最終驗收。固定來源 366ef501b78105d1f7242dc1f4f4752cac9086b5，detached 工作樹 /workspace/geo261-native；開始與結束皆為同一 SHA、乾淨工作樹，四個指定測試／裁判來源雜湊前後一致。本代理未新增 commit 或 push。前一輪中斷與環境失敗原件另見 ../native-first，沒有把首輪改算通過。

## 命令、環境與結束碼

內層完整命令，cwd 為 /workspace/geo261-native：

    timeout 2100 python3 tests/run_all.py --build

環境為 PYTHONDONTWRITEBYTECODE=1、LANG=C.UTF-8、LC_ALL=C.UTF-8，stack 為 16 MiB。外層實際 python3 -B -c argv 與 wrapper 全文原樣封存在 command.json；只在本程序設定 Linux PR_SET_CHILD_SUBREAPER，回收自己子樹的孤兒。沒有修改測試、忽略 zombie 或更動公理。主 timeout 子程序的結束碼獨立保存，外層原樣回傳，不被孤兒的 SIGKILL 狀態覆蓋。

- 開始：2026-10-20T20:44:15.032677+00:00
- 結束：2026-10-20T21:14:23.086690+00:00
- 主 child／外層 exit：0
- 外層總耗時：1808.054 秒；timeout 仍為 2100 秒。
- 完成表列：224/224；expected 數量不符：0。
- 表列合計：{"total": 5176, "passed": 5175, "failed": 0, "skipped": 1, "suiteSeconds": 1807.6}。
- 具名 skip：1 項；不允許 skip：0。
- 原始 suite .log/.json：600 份、295316 bytes。

此輪與其他 canvas 驗證並行，耗時只記實際執行資料，不作 P-189／P52 效能驗收。本次開始後的原始 suite logs 逐 byte 保存；本輪開始前的舊檔會另列排除，不混算。本次沒有複製 shim source、二進位或新增可執行工具。

verification.json 保存逐 suite 表列、expected 核對、具名 skip 比對、Python failures、獨立 owner／browser 門檻提示、回收與 cleanup 事件。suite-log-source-index.json 保存原始路徑、mtime、byte 數與 SHA-256；source-reference 保存 expected 原件及來源雜湊。主 timeout 若結束，wrapper 才會清理仍由自己直接收養的活子程序；這些事件另記 cleanup，不能延長驗收的 2100 秒上限。

## 環境自證與突變證據

首輪程序回收測試因 PID 1 為 tail、孤兒 sleep 保留為 Z 而失敗。固定來源與相同單測的 plain 控制為 exit 1，外層 subreaper 控制為 exit 0；原件在 ../native-first/環境診斷。兩案未改任何測試來源，也沒有把 zombie 排除於 group_members 判準。本輪完整 suite 仍要求 afterKill 為空；實際回收 PID、原始 wait status 與主 child exit 見 reaped.jsonl／reaped.json。

mutation:check 是既有突變 inventory freshness 檢查，不等同重跑全部突變。固定來源 7dae5f21c7ca401e660450d437e60ba566218da8 的 Q38、§7 實際突變與裁判控制另見 ../gates；不改標成 R2。該證據保留 killed、crashed、blocked、equivalent、survived／unlabelled 的原始分類，不混算 pass。

## 未驗項目與最大不確定性

run_all.py 只涵蓋其登錄的非瀏覽器 aggregate。正式 owner／browser 整合、geometry-web/cdp_test.js、geometry-web/space_model_test.js 及其他獨立必驗項須看各自收據；完整名單保存在 run.log 與 verification.json 的 separateGatesNotice。

Linux 唯一允許 skip 為 py:test_gdi_contract 的 test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources，理由 requires compiled Windows GDI contract harness；這不代表 Windows GDI 測試通過。本次沒有在 GitHub CI、Windows 或 WSL 執行。

最大不確定性是其他 runner 的 init／subreaper 是否提供相同孤兒回收條件。結論只對上述固定 SHA 與記錄環境成立；不把本收據改標成後續產品修正的 SHA。若 receipt 為 timeout 或未完成，acceptedNative 必為 false，保留完整失敗／未完成事實，不以單測控制替代整套驗收。

## 封存路徑

實際執行輸出目錄原為 /workspace/geo261-evidence/native-final；完成後依主代理要求封存為 /workspace/geo261-evidence/native-r2，bundle 對應 final-bundle/native-r2。command.json、receipt.json、run.log 與原始 suite logs 的 bytes 不因改名而重寫；其中歷史絕對路徑維持實際執行值。完整 mapping 見 path-mapping.json。
