# M1：收據語意與精確筆數的審查修正

依 [ChatGPT 審查 M1](https://github.com/ZhiQiYang/geometry-axiom/pull/235#issuecomment-6164435921) 及 [Claude P-107](https://github.com/ZhiQiYang/geometry-axiom/pull/235#issuecomment-6164666788)，完成分析器補強、原 archive 重分析、反例與完整 native。沒有修改產品、expected、突變帳本，也沒有重跑七組瀏覽器量測或 WSL 全量。

## 收據與計數

- 原封存 archive SHA-256 仍為 `85169cee90b3feed67fd7291ea0be35b8b3ce8dc8819cd16d7e85eca25376c08`，未重打包或改寫。由此解出七組，更新後分析器 exit 0；新增的 `receipt_evidence` 見 [analysis.json](analysis.json)。
- runtime18：business requestId `75965015-9977-404e-b070-4f5825054a4b`，原 fetch-6／同 receipt fetch-7，同 call-5；原修改 stdin 0、非空 native reply 0，收據先完成取消，最終 ready、回「操作未送達，場景未變更；請重新操作。」。
- receipt18：business requestId `631ca45f-4aa7-4321-bf17-f42a549d3f7e`，原 fetch-6／同 receipt fetch-7，同 call-5；原修改 write/flush/queue 各一次、非空 native reply 一次，收據不執行修改並成功回收原結果，最終 ready、P7 五個 oracle 通過。
- 同時核對 client/server requestId、receipt body hash 與 API 結果；原修改只發一次，收據在 timeout 後查詢。七組 timeout/blocked 精確計數及合計六筆 timeout 均有守門。

## 12 個反例

[工具 stdout](counterexamples.stdout)／[完整子程序記錄](counterexamples.json)。未改的七組：修前及修後皆 exit 0。下列是**僅修改暫存副本的合成錯誤紀錄**：全部修前 exit 0（錯收）、修後 exit 1（正確拒絕），且 stderr 含對應具名原因。反例工具本身 exit 0；移除 M1、改用舊 head `940d25f1` 分析器便重新錯收。

| 反例 | 修後拒絕原因 |
|---|---|
| runtime 晚到原修改實際進入 native | cancelled-before-native |
| runtime client receipt 不同 ID | same-receipt-id |
| runtime server receipt 不同 ID | server-receipt-identity |
| runtime 最終 error | receipt-ready |
| runtime 未取得取消結果 | receipt-result-body |
| receipt 原修改寫入兩次 | exactly-once-native |
| receipt 原修改收到兩個非空 native reply | exactly-once-native |
| receipt 查詢不同 ID | same-receipt-id |
| receipt 最終 error | receipt-ready |
| bridge 少一筆真正 timeout | exact-timeout-blocked-counts |
| native 少一筆原 P7 fetch 前 guard | exact-timeout-blocked-counts |
| baseline 多一筆真正 timeout | exact-timeout-blocked-counts |

## 完整 native：首紅與修正環境後的完整重跑均保留

Debian/Linux x86_64、GCC 14.2.0、Python 3.12.14、Node 24.19.0、stack 16 MiB；原命令皆 `python3 -u tests/run_all.py --build`。

| 輪次 | 受測 head | suites／有計數者 | 整體退出碼 | 程序 wall 秒 |
|---|---|---|---:|---:|
| 共用預設快取 | `644f187fbca3ac085a48eb1310b0a150625479e3` | 88／2775 pass、0 fail、1 平台 skip | **1** | 745.483 |
| 獨立 MUTATE_CACHE | `a3ce4a84d29d7b26bac1d97b0f092e5e53a487a4` | 88／2775 pass、0 fail、1 平台 skip | **0** | 803.123 |

首輪不是全綠：`mutation:check` 是無 test 級計數的 suite，額外報 45 stale、0 blocked。`/tmp/geometry-tests/mutants` 的舊 binary/sidecar 是不同來源閉包；目前來源閉包與已提交帳本相符。[逐一快取對照](cache-diagnosis.json) 保留 45 筆 binary/hash/closure；[首輪 stdout](native-first.stdout)、[metadata](native-first.json)、[首輪所有原日誌](native-first.tar.gz) 均保留。

原工具明確支援乾淨 checkout 的可攜執行收據（`tests/mutate.py:723–735`，既有 `test_portable_receipt_accepts_clean_checkout_without_temp_binary`）。保留共用快取和帳本，使用 `/tmp/geometry-wake30-235/isolated-mutants` 作該分支的 `MUTATE_CACHE`。先行 check 為 stale 0／blocked 0／exit 0，再跑**完整** native，不將局部 check 與首輪拼接成綠燈。獨立快取在完整重跑前後均空，沒有重編或重跑既有 45 個 mutant；只驗證帳本與來源／oracle／既存執行收據。

另在第三個隔離快取放入舊 M01 binary/sidecar，原 check 立即報 M01 stale／exit 1，證明校驗仍有效；負向結果在 raw 的 `cache-negative.*`。第二輪 mutation:check 為 40 killed／1 crashed／4 equivalent／3 retired、0 stale／0 blocked；這是既存收據的完整性檢查，**不是本輪新突變裁判**。

[第二輪 stdout](native.stdout)／[第二輪 metadata](native.json) 顯示所有 suites 執行、數量與 expected 相符、無 fail／環境問題，唯一略過是允許清單中的 Windows GDI。兩輪產品與測試程式 SHA-256 完全相同，執行前後 head 固定、工作區乾淨；`644f187f→a3ce4a84` 只增加本目錄進度證據。最終其後也只附文件與證據，不改受測程式。這是雲端 native，**不是 WSL 收據**，亦不涵蓋完整 browser／owner gate。

## 原始輸出

- [raw.tar.gz](raw.tar.gz)：560 檔，包含兩輪 native 全日誌、PID／argv／exit／來源與 binary metadata、13 組修前修後分析子程序、所有合成變更輸入及執行腳本。
- [raw-manifest.json](raw-manifest.json)：每檔 bytes 與 SHA-256；封存後已重讀全部成員核對。
- [raw.tar.gz.sha256](raw.tar.gz.sha256)：`933d191c6123aa9d28154e879eb7abe3b2451608992776c11e810257104adb5e`。
- [analysis.stdout](analysis.stdout)、[counterexamples.stdout](counterexamples.stdout)、[native.stdout](native.stdout) 是可直接閱讀的原輸出；raw 另含 stderr 與退出碼。

M1 工具提交：`644f187f`；完整重跑提交：`a3ce4a84`。原首次交付、失效 pilot、首輪 native exit 1 都保留，不以後續綠燈改寫歷史結果。
