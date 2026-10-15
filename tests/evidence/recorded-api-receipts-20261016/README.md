# #240 S9：任務 30 回執三層與正式函式測試

基底 main：`1c80751150d0767ba52509537caf8d5542769ccb`。
依據：#240 R14／P-143；看板 blob `efd73b543a16f37022547b33400778d6501d7f85`。
新增 `geometry-web/NATIVE-CONTRACT.md`，因指定路徑在固定 main 與開工時 main 都回 404。
沒有以另一份既有契約被覆寫作為前提。

## 改動與驗證界線

- T1 六組正式測試選取當前 `serve.py` 原 AST 的 `recorded_api`、`err_json`、
  `MAX_RECEIPTS`、`BRIDGE_TIMEOUT`，只替換 context 與 bridge；不複製實作邏輯。
- T2 按 `batch_confirm` 索引回覆欄位及可選 hash；T3 明列各功能接線尚未逐一核對。
- 必要範圍外登記：`tests/run_all.py` 的 PY_NEEDS 新增一行空二進位需求；
  `tests/run_all.expected.json` 只新增一個 suite/count=6，既有項目不改。
  不登記會使原 runner 拒絕新增測試，因此依看板 ≤20 行小例外一併處理。
  expected 的 6 來自新 suite 實測，不宣稱完整 census 已重跑。
- 不改產品、SSOT、白話、正典、決策佇列、官方 C 突變定義／帳本或其他工人檔案。

## 實跑

Linux 6.18.44 x86_64、glibc 2.39、Python 3.12.14。函式測試不需原生二進位。

| 執行 | 實際結果 | actual exit |
|---|---|---:|
| 六組正式函式測試 | 6 pass／0 fail／0 error／0 skip | 0 |
| 透過 `run_all.run_suite` 執行新登記 suite | 6 pass／0 fail／0 skip，expected 相符 | 0 |
| 隔離 baseline | 6 pass／0 fail／0 error／0 skip | 0 |
| 拿掉快取讀取：`cached = native.api_receipts.get(request_id)` → `cached = None` | 2 pass／4 assertion failures／0 error／0 skip | 1 |
| 隔離還原 | 6 pass／0 fail／0 error／0 skip | 0 |
| 突變驅動器（驗上述條件及測試不變） | PASS | 0 |
| 新測試、兩支證據工具與 runner 的 py_compile | 通過 | 0 |

最終原件：[`raw/exact-source-final/receipt.json`](raw/exact-source-final/receipt.json)，
含各子程序 exit、時間、source/test SHA256 與 runner JSON；stdout、stderr 與
unittest log 均在同目錄。`T1_LOST_RESPONSE_RECOVERED`、
`T1_EARLY_LOOKUP_SEALS_ID`、`T1_COMMAND_BINDING` 具名轉紅。
測試檔三輪 SHA 相同；產品原件在前後完全不變，只改臨時副本。

重現：

```sh
python tests/test_recorded_api_receipts.py -v
python tests/evidence/recorded-api-receipts-20261016/mutate_receipt.py --out /tmp/receipt-mutation-new
python tests/evidence/recorded-api-receipts-20261016/verify_registration.py
```

`--out` 必須是尚不存在的目錄，避免覆寫先前原件。
`registration.stdout` 是真 `run_all.run_suite` 的結果；此工具刻意不略過後假稱完整
registry 檢查，也不將一個 suite 的執行說成完整 native。

## 先前嘗試保留

- `raw/attempt1-missing-helper/`：隔離副本漏帶 runner 的 binaries.py 依賴，三輪均 import error，
  驅動器 actual exit 1。這不是有效 baseline 或 killed。
- `raw/attempt2-missing-log/`：子程序已 6綠／4紅／6綠，但驅動器錯從空 stderr 找 assertion，
  actual exit 1；改為保存並驗 unittest log 後才完成。
- `raw/final/`：第一次完成驅動器，但下載檔案寫入時多一個檔尾空行；
  後續將產品來源恢復成連接器固定 Git blob 的精確 bytes，重跑為 `exact-source-final`。
  前者不冒充最終精確來源證據。

## 未驗／交付限制

**雲端定向測試，非正式 WSL 收據；完整 native 未執行。**
GitHub 與 git.chatgpt-team.site 的 clone 都因缺少非互動憑證 exit 128；
本輪透過已連接 GitHub 讀取必要的固定版本檔案，沒有完整 checkout，
不能執行完整 native 或宣稱全部登記／owner／browser gates 通過。
沒有改用空白替身檔湊出完整 registry。

PR 維持 draft。完整 native、正式七項（改到共享 runner）、HTTP、真 bridge、
瀏覽器及 T3 接線仍待驗；正式數量與衝突由既有列車逐 suite 整合。
本任務沒有新增可見 UI，也沒有宣稱 R52 端到端成立。
