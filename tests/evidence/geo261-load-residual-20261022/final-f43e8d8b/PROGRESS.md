# #323 固定來源驗收完成（2026-10-23）

受驗 F：`f43e8d8b876f587c11778fa74a80b205b51396b6`；本目錄的後續證據提交 E 不替代 F。

| 完成項目 | 原結果 |
|---|---|
| 完整 native | 225 suites；5193 = 5192 pass / 0 fail / 1 允許的 Windows GDI skip；原退出0 |
| 原必要八套 | 674/674，退出0；原部分執行聲明保留 |
| 完整 PF3 | baseline20 / restored20 / 19 killed，退出0 |
| A/B/C | 175場景、350 base/fix版本組；75接受＋100拒絕各版本；stdout逐bytes、每seal完整有序圖、每scene五guard總數均相同，退出0 |
| 36筆三方交錯性能 | 各原程序0；N64 fix/main **1.7457212386，未達1.3**，未重抽；N16/32/48相對base均不變慢 |
| 四次原profile | 全0；source N64/N32 **4.4704196928 ≤4.5** |
| 三條原架構裁判 | 同F，0/0/0 |
| 帳本整份重產 | 真S=b823903e；precheck1 / full0 / checkafter0；78=70 killed+M20 crashed+4 equivalent+3 retired，75筆execution全S |
| 總封裝退出 | **1**：原量化目標未全達；不是native失敗，不能聲稱完整驗收全綠 |

各項 argv、真退出、完整原stdout/stderr、環境、來源SHA與工具指紋已封存。正式原資料11089 members/106672856 bytes，兩封包逐member path/bytes/SHA核同；另列完整ledger稽核與其原工具限制。

C第4項placement guard單刪為合法生命期下的等價0/0/0；配對撤anchor invalidator才0/1/0，僅證第二防線。不能稱單項非等價或C每個單刪皆紅。詳QUESTIONS.md及新正文。

下一步：將新正文推至既有prbody分支供使用者貼到#323；繼續#314與#299+#316。PROMPT-B明文允許如實交付未達性能目標，剩餘熱點留既有#300後續，不改門檻、公理語意或守門流量。
