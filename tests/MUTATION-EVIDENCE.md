# 突變收據與可下載二進位證據

> **現行表（2026-11-12 依 `f3ee80cf` 實數更正）：138 筆／135 active／3 retired**；core 70（67 active＋3 retired）、bridge 68，七片依現行表動態分成 core 18／18／17／17 與 bridge 23／23／22（`.github/scripts/mutation_evidence.py::shards()`）。已採入的 `tests/mutants_results.json` 為 138 筆：killed 129、equivalent 5、crashed 1、retired 3（來源見最近一次採入 commit `77b04899`）。
>
> 歷史：main `8f82b207e87c086705a1d8b7a00e2f215c07cbcf` 納入 #338 時完整表為 123 筆／120 active／3 retired（core 70、bridge 53，分片 18／18／17／17 與 18／18／17）。`de9aea24113a522c6cd80d30b9281e1034b57c6c` 的 [run 41333327153](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41333327153) 及 78／75 收據保持原來源的歷史證據。

`tests/mutate.py --check` 不編譯、不執行突變。它嚴格核對來源、include 閉包、突變、裁判及執行收據。若同平台的暫存二進位存在，也會核對它的指紋與 SHA-256；不同二進位應判 `stale`。沒有暫存檔時通過，只能證明收據與目前來源／裁判一致，不能宣稱已核對原執行檔位元組或已重跑突變。

因此 #357 `212ee528` 的 [run 40939418733](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40939418733) 中 `mutation:check` exit 0，與另一工作區出現 75 筆暫存二進位不符可以同時成立。前者是乾淨環境的收據驗證；後者仍須保留拒絕結果，不能只稱為環境差後忽略。

## CI 的新證據

`Mutation evidence` 工作流程不改 `mutate.py`、`mutation_bridge.py` 或已提交歷史帳本：

1. 先在 GitHub 執行原 scanner CLI 與原兩支架構 unittest，保存新來源的 scan／receipt／說明與原始輸出；沒有在本機執行模組。歷史帳本的原 `--check` 守門仍保留在正式測試入口；來源改變時，歷史 stale 不能拿來阻止「生成新收據」，也不能被寫成已通過。
2. 從現行突變表自動分成 4 片 core 與 3 片 bridge，每筆恰好一片。新來源的全部 active（現行 135 筆）均需實際執行（含 equivalent 的完整 oracle），3 筆 retired 仍核對退役條件。bridge 還原裁判為 `tests/mutation_bridge.py::RESTORED` 的方法（現行 55 個），裁判閉包也包含 `tests/*.c` 與 `tests/fixtures/**/*.scene`，不能把舊 75 筆冒成 fresh。各片結果檔從空檔開始，不繼承歷史 killed。
3. 各片使用原 runner 執行基準與突變，保存新帳本、實際二進位／sidecar、執行輸出及雜湊 manifest。core 保存結構化 oracle 執行收據與 runner 輸出；bridge 另保存逐次建置及 oracle 的原始 stdout／stderr。省略 scratch checkout 與 OS core dump。
4. 每片要求全部指派 ID 存在、實際收據屬於當前 head，並用原工具 strict 檢查。刻意改壞一個該片二進位，必須被原二進位守門拒絕、strict exit 1；還原 bytes 後重驗通過。`blocked`、`stale`、未知／缺漏 ID、skip 或基礎設施失敗都不算 killed。
5. 聚合 job 必須等所有片成功；重新下載 artifact，逐筆要求二進位存在且 SHA-256 相符，再以原工具核對每片。最後要求完整表無重複／缺漏／額外 ID，對新完整帳本再跑原 strict 檢查。

`mutation-shard-*` 是原執行證據；`mutation-complete-evidence` 包含聚合帳本及 `summary.json`；`pr357-architecture-refresh` 保存原三命令的新架構衍生資料與 raw 輸出。已提交的 `tests/mutants_results.json` 在重產前保持 main 的歷史原件；只有真實新 CI 產物可採入為下一份帳本，不以改 hash 的方式洗綠。採入後仍須由新來源的原 `--check` 與正式測試取得結果。

## 從另一個乾淨環境重驗

需要 Git、GitHub CLI 與 Python 3.12 以上。使用該次 run 的完整 head SHA 簽出 repo，保持來源不改；下載 artifact 後，以下驗證只讀取二進位 bytes，不執行它們，也不重編：

```sh
gh run download <run-id> --repo ZhiQiYang/geometry-axiom --pattern 'mutation-shard-*' --dir <下載目錄>
python .github/scripts/mutation_evidence.py verify --artifacts <下載目錄> --out <新的驗證輸出目錄>
```

同平台保留原編譯指令／指紋的嚴格檢查；跨平台核對已下載的原執行檔 bytes 及原平台收據，不宣稱在接收平台執行了不相容的二進位。需要證明接收平台的行為時，須在該平台另跑原 runner，產生另一份執行收據。

artifact 保留 30 天；到期或來源／裁判／工具改變後，重新執行 `Mutation evidence`，不能沿用舊綠燈。工作流程可手動啟動；更動此工作流程、監督腳本或本文的 PR 也會自動產生當前 head 的完整證據。
