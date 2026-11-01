# 突變收據與可下載二進位證據

`tests/mutate.py --check` 不編譯、不執行突變。它嚴格核對來源、include 閉包、突變、裁判及執行收據。若同平台的暫存二進位存在，也會核對它的指紋與 SHA-256；不同二進位應判 `stale`。沒有暫存檔時通過，只能證明收據與目前來源／裁判一致，不能宣稱已核對原執行檔位元組或已重跑突變。

因此 #357 `212ee528` 的 [run 40939418733](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40939418733) 中 `mutation:check` exit 0，與另一工作區出現 75 筆暫存二進位不符可以同時成立。前者是乾淨環境的收據驗證；後者仍須保留拒絕結果，不能只稱為環境差後忽略。

## CI 的新證據

`Mutation evidence` 工作流程不改 `mutate.py`、`mutation_bridge.py` 或已提交歷史帳本：

1. 在乾淨 checkout 與未編譯的隔離 cache 核對歷史收據，明確標示它不含二進位位元組驗證。
2. 從現行突變表自動分成 4 片 core 與 3 片 bridge，每筆恰好一片。目前為 78 筆：75 筆需實際執行（含 equivalent 的完整 oracle），3 筆 retired 仍核對退役條件。各片結果檔從空檔開始，不繼承歷史 killed。
3. 各片使用原 runner 執行基準與突變，保存新帳本、實際二進位／sidecar、執行輸出及雜湊 manifest。core 保存結構化 oracle 執行收據與 runner 輸出；bridge 另保存逐次建置及 oracle 的原始 stdout／stderr。省略 scratch checkout 與 OS core dump。
4. 每片要求全部指派 ID 存在、實際收據屬於當前 head，並用原工具 strict 檢查。刻意改壞一個該片二進位，必須被原二進位守門拒絕、strict exit 1；還原 bytes 後重驗通過。`blocked`、`stale`、未知／缺漏 ID、skip 或基礎設施失敗都不算 killed。
5. 聚合 job 必須等所有片成功；重新下載 artifact，逐筆要求二進位存在且 SHA-256 相符，再以原工具核對每片。最後要求完整表無重複／缺漏／額外 ID，對新完整帳本再跑原 strict 檢查。

`mutation-shard-*` 是原執行證據；`mutation-complete-evidence` 包含聚合帳本及 `summary.json`。已提交的 `tests/mutants_results.json` 保持歷史紀錄，新 CI 收據不以改 hash 的方式覆寫它。

## 從另一個乾淨環境重驗

需要 Git、GitHub CLI 與 Python 3.12 以上。使用該次 run 的完整 head SHA 簽出 repo，保持來源不改；下載 artifact 後，以下驗證只讀取二進位 bytes，不執行它們，也不重編：

```sh
gh run download <run-id> --repo ZhiQiYang/geometry-axiom --pattern 'mutation-shard-*' --dir <下載目錄>
python .github/scripts/mutation_evidence.py verify --artifacts <下載目錄> --out <新的驗證輸出目錄>
```

同平台保留原編譯指令／指紋的嚴格檢查；跨平台核對已下載的原執行檔 bytes 及原平台收據，不宣稱在接收平台執行了不相容的二進位。需要證明接收平台的行為時，須在該平台另跑原 runner，產生另一份執行收據。

artifact 保留 30 天；到期或來源／裁判／工具改變後，重新執行 `Mutation evidence`，不能沿用舊綠燈。工作流程可手動啟動；更動此工作流程、監督腳本或本文的 PR 也會自動產生當前 head 的完整證據。
