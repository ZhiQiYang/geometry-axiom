這份補丁為核心 K 與矩形格網模板加入隔離編譯及功能見證。新增控制要求 `geometry_woodworking` 與 `geometry_app` 即使確實可匯入也被拒絕，並檢查 K 引入已安裝模板的 quoted／angle header 時都會被原層界守門攔下。

本輪 current-state 唯一矩陣：

| 項目 | 目前身份或結果 |
| --- | --- |
| Product SHA | `bfbab207a92a809fca50fefcefb3fa4b2af05ea9`，已一般 push 並 ls-remote 核同 |
| 普通合流 | parents `3e7502e470bfdde3b40ca4cc82f7a68af158b144`、公開整合 `504933473d7b9bdfc5964f73402a710f1222fc96` |
| 產品差異 | 對整合 SHA 僅 `tests/test_rectangular_template.py` 與 expected 方法數 11→13；無公理、決策或產品實作更改 |
| 來源檢查 | clean，原 leaf SHA256 `e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e` 未變；兩產品檔 diff-check exit 0 |
| 歷史原件空白檢查 | 全 diff-check exit 2，僅舊 evidence/CANDIDATE.patch 六行 patch-context 空白；原輸出與原檔保留，不作產品或正式測試結果 |
| 新合流對抗審查 | 待獨立 peer；舊 9b201164 純靜審只涵蓋原 leaf，不冒稱新身份已審 |
| 正式 13 方法 | **UNRUN**，尚未獲 heavy 時槽 |
| 原 7 階段反證 | **UNRUN**；預期原退出為 `0/1/0/1/0/1/0`，尚無真實結果 |
| 本輪收據 evidence head | source publication 收據目前仍 local，由 root 統一推交接證據；既有舊 evidence／正文不充作本輪正式驗收 |
| 全突變帳本 | 由 root 在最終列車 SHA 唯一重產；此分支未自行重產 |
| 允許 skip | 無 |

正式入口已在 `NO_WOOD_REQUEST_bfbab207.json` 固定完整 SHA、原 driver/capture/test hash 與輸出位置。原 driver 自行取得 `/tmp/g261r3/heavy.lock` 的 EX|NB；忙鎖沿原錯誤分支為 exit 2，不能套用維護工具的 75，也不能移除鎖或故意忙時啟動。當前只準備，不冒稱正式通過。

合入主分支仍由使用者控制；未 merge PR、未 rebase、未 force push。
