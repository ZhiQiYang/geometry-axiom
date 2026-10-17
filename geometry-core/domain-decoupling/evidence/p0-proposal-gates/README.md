# P0 提案守門的可重跑負控制

這份證據只驗提案完整性守門，不代表幾何核心已解耦，也不是使用者批准或 Claude 最終審查。

凍結輸入對應 P0 source commit `17a25e92c75e8c89063e36ca329729980d8ea6a9`；各輸入的原始及 LF 正規化 SHA-256 記在 `mutation-results.json`。收據於 2026-10-15 18:53:57 UTC 開始，使用 Windows `C:\Python314\python.exe`。來源 SSOT 的 CRLF／LF 差異只作行尾正規化，不改條文。

| 執行 | 測試數 | exit | assertion failures | errors |
|---|---:|---:|---:|---:|
| 未修改的正式測試 | 29 | 0 | 0 | 0 |
| 移除 SOURCE_HASH guard | 29 | 1 | 3 | 0 |
| 移除 CLAUSE_BEFORE guard | 29 | 1 | 1 | 0 |
| 移除 MIXED_LEGACY guards | 29 | 1 | 1 | 0 |
| 移除 PREAMBLE_SCOPES guard | 29 | 1 | 3（同一測試的三個 subtest） | 0 |

runner exit 0；四組 mutant 均在暫存副本移除實際 validator guard，且失敗測試名稱必須精確符合預期。不是讓 mutant 編譯失敗，也不是只驗錯誤字串。五份 `.log` 是原始 stdout＋stderr；收據逐份記其 SHA-256。正式測試、map、逐條提案、SSOT 與 expected counts 在整輪前後逐位元組不變，暫存副本已清除。

從 repository 根目錄重跑（輸出目錄須是新的，不可覆蓋本收據）：

```sh
python geometry-core/domain-decoupling/evidence/p0-proposal-gates/mutate_proposal_gate.py.txt --root . --out /path/to/new-receipts
```

可用 `--python /path/to/python3` 指定子測試的 Python，預設沿用 runner 的解譯器。保留 `.py.txt` 是為了將歷史重現工具與產品 Python 模組分清；它仍可由 Python 直接執行。runner 不修改 repository；原始輸入漂移、guard 命中數錯誤、非預期測試失敗均令 runner 非零退出，環境受阻另記 exit 2。

此證據不是 `tests/mutate.py` 的原生 C 突變帳本。該帳本仍須在完成實作後全量重產；P0 沒有以這四項負控制冒稱已完成該要求。
