# 待執行的 E2 交付驗證方法

本目錄只是新 L2 綁定後的方法副本，沒有建立 E2、執行 verifier／controls、產總索引或修改主樹。

`verify_E2.py` 為 18120 bytes，SHA-256 **`99e6cdbafec586a97c37382216ad14737a173f6e394af3bde2685464d59db9e1`**。對既有已審 `verify_E.py`（`ffe3d3fe08ba3c51534b51724ae984e9c3a3774b02230e6d0f344f1bc4d897e3`），只替換三個常數：

| 常數 | 新值 |
|---|---|
| `L` | `249571fe2477845d5330f6190dad965bf327f43b` |
| `SNAPSHOT_HASH` | `6f5840a1c9247617a67af1c03a7a63fb1dc7b61adf01e381f6322361f684e48b` |
| `LEDGER_HASH` | `6bda315331050bd3478ed65211a8263508cb1a1f6f67cee3f35df377506e7f0b` |

新快照在實際 L2 上以未改的工具新跑、真碼 0，沒有改舊快照 SHA 欄位。方法生成命令 `python3 -B /workspace/geo261-evidence/prepare-E2-from-L2.py` 真碼 **0**；AST／parser 核對通過，反向替換三行後逐 bytes 等於原 verifier，完整 diff 在 `constant-only.patch`。既有 exact diff、來源／ledger／closure、強制 source bytes 載入正式 hash 模組、檔案類型／magic、index／config／ignore／attributes 守門全部保持。舊 57 項純資料控制未在此重跑，不能當作本輪新執行。

待 E2 與最後 exact review 已建立後，命令為：

```text
env -u CC -u PYTHONOPTIMIZE python3 -B /workspace/geo261-evidence/source-binding-E2-preparation/verify_E2.py --root <E2工作樹> --expected-e <完整E2SHA> --snapshot-l /workspace/geo261-evidence/source-binding-L2-preparation/snapshot-L2.json --review-file <新exact-review.json> --review-sha256 <新review原bytesSHA256>
```

stdout／stderr與真 wait 碼由外部父程序另存。E2 收據留 repo 外，避免自含 SHA 循環。源值已固定，但 E2 SHA、全量驗收收據與最終總索引／review 尚未齊；本方法準備不是 E2 驗證成功。封包時 `.py` 原 bytes 改副檔名為 `.py.txt`，不新增產品執行工具。
