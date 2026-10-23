新增平釘下角材的現場規則引文頁，供後續推理先核對使用者原話。38 行引文保留指定決策快照的原字、tab 與行尾空白；非引文只負責編排。這份頁面不取代公理層，也不宣告產品已實作新規則。

最新 ChatGPT 審查為 handoff `b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6` 所收錄的 2026-10-23 14:41:33Z、head `3d9bd947`，結論「可合併」。其後 `02cb11b9` 僅撤回 `.gitignore` 對整個 `geometry-templates/` 的放行；已追蹤的 FIELD-RULES 保持逐位元組相同。這是對較早審查的範圍收斂，沒有把已撤回的須改誤列為最新阻擋，也沒有聲稱新 SHA 已獲 ChatGPT 複審。

| Current-state 項目 | 身分／結果 |
|---|---|
| 文件／政策來源 S | `02cb11b9762da429a3dbb0eed9151f45a65ed620` |
| 完整證據快照 E | `a0043acbb4876cac09e3d31c0b960bf86811a89e` |
| 引文頁 | 38 行引文；FIELD-RULES SHA-256 `3305d8000af9814b91c2646cfcbbc841e1ead813fe3390e482f8bfc2a71c0ab2`；本次修正未改 bytes |
| Allowlist 自證 | 原 `git check-ignore --no-index -v geometry-templates/woodworking/notes.txt`：修正 0／撤回 1／恢復 0；每階段 FIELD-RULES 仍為已追蹤原檔 |
| 精確紅燈 | 撤回時原 Git exit 1，代表同層未追蹤 notes.txt 不被忽略；外部政策訊息為 `ASSERT_FIELD_RULES_ALLOWLIST`，不冒充產品 unittest assertion |
| 錄製與還原 | 外層 exit 0；所有原指令、環境、streams、exit、S 與前後 clean 身分均已封存 |
| 獨立對抗審查 | 176 checks，0 findings；核對原 23 個 Git 指令及 launcher、來源 diff、遠端 SHA、完整原 streams |
| 產品／瀏覽器／施工驗收 | 本次未跑；此變更只限文件與 ignore 範圍，沒有修改產品、測試、golden、閾值、公理、決策佇列或閱讀器 |

證據與進度：[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/a0043acbb4876cac09e3d31c0b960bf86811a89e/evidence/geo333-final-02cb11b9/PROGRESS.md)；[原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/a0043acbb4876cac09e3d31c0b960bf86811a89e/evidence/geo333-final-02cb11b9/receipts/ignore-scope-reviewed.json)。完整原件與對抗報告收在同目錄的 raw 封包。

原始私人對話與現場圖片未由本次驗收直接核對；引文真實性只以宣告的 Git 決策快照為界。較晚的 #318 閱讀 A 核可另見 main 的 2026-10-23 決策，沒有偷偷補寫成本頁的舊來源。

所有推送均為一般 push；本工作沒有合併 PR。
