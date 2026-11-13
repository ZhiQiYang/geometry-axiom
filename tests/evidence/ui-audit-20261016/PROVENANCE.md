# 來源說明(2026-10-24 補提交)

- 本目錄是 2026-10-16 對當時 main `1c80751150d0767ba52509537caf8d5542769ccb` 做的操作流程與 UI 審查,報告見 [REPORT.md](REPORT.md)、測試結果見 [TEST-RESULTS.md](TEST-RESULTS.md)。
- 原本產生在本機工作區 `geometry-web/docs/audit-20261016/`,一直沒有提交;2026-10-24 由本機 Claude 原樣搬到這裡提交,檔案內容一個 byte 都沒改,另外只新增本檔與 `.gitattributes`(`* -text`,保持 bytes 原樣)。
- 搬離 `geometry-web/` 的原因:GEO-261(#288)合入後,`geometry-web` 是產品架構清單的完整來源根目錄,其中的 `.py`/`.cjs` 都必須登記;本目錄的 `collect_results.py`、`reproduce_model_capability.py`、`diagnose_section.cjs` 只是審查用腳本,不是產品來源。`tests/` 底下不在產品根目錄內,也不在 `run_all.py` 的頂層測試清點範圍內。
- 報告、收據與 JSON 內寫的路徑(`geometry-web/docs/audit-20261016/...`)是當時的輸出位置,保留原樣,不改寫成新位置。
- 本次只補提交,沒有重跑任何審查或測試;報告中的結論只對 `1c807511` 成立,不代表目前 main 的狀態。
