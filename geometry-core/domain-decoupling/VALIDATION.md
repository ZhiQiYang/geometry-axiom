# GEO-261 P0 驗證紀錄

> P0 只有提案與提案完整性測試。正式規範、白話、正典閱讀器、modeling 版本及產品程式未改；尚未獲使用者批准。此文件不構成 GEO-261 完成交付。

- 基準 source：`1c80751150d0767ba52509537caf8d5542769ccb`。
- P0 source：`17a25e92c75e8c89063e36ca329729980d8ea6a9`。
- 後續收據提交只新增驗證材料，不冒稱重新驗過另一組產品程式。

## 提案與負控制

`python -B tests/test_domain_decoupling_proposal.py`：29／29、exit 0。測試獨立讀取 SSOT，核對固定基準雜湊、204 條順序與 before 全文、103 項 after、完整混合條文尾段、Markdown／JSON 對應及前言作用域。另有同步篡改 map／Markdown／SSOT 的負例，避免內部自洽掩蓋來源漂移。

[四組實際 guard-removal 收據](evidence/p0-proposal-gates/README.md)：runner exit 0；正式 baseline 29／29；四組 mutant 各跑 29 項、exit 1、具名 failures 3／1／1／3、errors 全為 0。正式檔前後不變。

內部對抗審查已關閉 D19 的單軸 `n=1` 與 R44 的普通值快照可編輯問題。獨立驗證員另核對來源全文、提案一致性、登錄計數與未改正式規範。這些是 P0 審查，不是 Claude 最終品質審查。

## 測試清冊

| 項目 | 基準 | P0 | 差異 |
|---|---:|---:|---:|
| suites | 88 | 89 | +1 提案 suite |
| counted checks | 2827 | 2856 | +29 Python tests |
| Python tests | 1044 | 1073 | +29 |
| Node checks | 1510 | 1510 | 0 |
| C checks | 130 | 130 | 0 |
| 原生場景 | 143 | 143 | 0 |
| 只檢查 exit 的 suites | 6 | 6 | 0 |

counted checks 混合測試、assertions 與場景，不能改稱 2856 個端到端情境。既有 88 項清冊不變；原 Windows-only GDI skip 單獨記錄，不計作 pass。

## WSL native

兩個全跑各使用獨立 Linux checkout、私有 mount／network namespace、私有 `/tmp` 與 loopback，不重置使用者服務。stack 16384；Python 3.12.3、GCC 13.3、Node 24.21。

| 執行 | source | 結果 |
|---|---|---|
| 第一輪完整基準，`tests/run_all.py --build` | 基準 | exit 1：發現 2821，pass 2731，fail 89，skip 1；node:tests-js 缺裸 `python`，該 suite 比預期少發現 6 項 |
| 補私有 `python → python3` PATH alias 後只跑 node:tests-js，`--build --only node:tests-js` | 同一基準，來源未改 | 704／704，exit 0 |
| 補 alias 後完整基準重跑，`tests/run_all.py --build` | 同一基準 | 執行中，尚無完整通過結論 |
| P0 完整候選，`tests/run_all.py --build --update-expected` | P0 | 執行中；產生的 expected JSON 必須逐項等於提交版，不能以更新清冊掩蓋測試增減 |

保留第一輪環境失敗紀錄，不以單一 suite 復測冒稱完整基準通過。候選 `--update-expected` 若只改 JSON 排版，須先證明解析後完全相同，再在隔離 checkout 回復原位元組並記錄；若資料不同即屬未解差異。

## 尚未完成的驗收

- 全量 native 最終結果與精簡原始收據尚待寫回。
- 六個瀏覽器 job 未在 P0 執行。P0 不改產品介面；後續實作仍須依改動跑真實 app 操作，正式七項列車由 Claude 核收。
- 基準 main 沒有 `geometry-core/framing-template/oracle/`，因此 oracle selftest 未跑，不算通過。
- 原生突變帳本 freshness check exit 0（42 killed／1 crashed／4 equivalent／3 retired，無 stale）；尚未全量重產。解耦實作後必須重產。
- 真正核心依賴方向、拿掉木工模板、第二模板、全部舊 fixture 前後差分與 Claude 無阻擋審查都尚未完成；提案測試不能替代它們。
