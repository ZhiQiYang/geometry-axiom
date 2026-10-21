# 固定寬度解碼候選：性能預檢仍失敗

分支 `codex/geo261-p189-codec-trial-20261021`，候選真 SHA `7ad3216ac3ea00bec0adac7b38c3a3daf0a39d09`，parent 為正式 L `43f85313c32410ac01406ab585846bbacafea278`。完整 patch、單一改檔與來源 closure 索引在 raw；只有 wd_read 固定 1／4／8 位元組解碼變更，未改 P177 次數／時機。

generator selftest、16 控制（2正／14負）、三方 build、175 equivalence、timing 均真0；**check、supervisor、頂層 exec session 真wait均1**。timing0只是收樣完成。175場景三方完整stdout全同，36有效樣本，來源判定通過。

| N | main median 秒 | 候選 median 秒 | 候選/main | ≤2 |
|---|---:|---:|---:|---|
| 16 | 0.11074152499713819 | 0.12093423400074244 | 1.092040533159243 | 通過 |
| 32 | 0.21071959099936066 | 0.3254812269988179 | 1.5446177806970278 | 通過 |
| 48 | 0.3120637430001807 | 0.7256599210013519 | 2.3253579990576854 | 失敗 |
| 64 | 0.527766454997618 | 1.3449583139990864 | 2.548396741140277 | 失敗 |

四個 N、三輪正反交錯、固定 main/base、三方新 archive／gcc -std=c11 -O2 建置、16MiB、900秒timeout、原工具hash與≤2門檻均沿用。t0仍在Popen返回後；無Python -O且移除PYTHONOPTIMIZE。原法實跑命令在raw/planned-commands.json，實際真碼與開始／結束時間在raw/phase-receipts.json。

可判此解碼候選單獨仍不足解除原門檻。未另跑同時段 L 對照，不能用跨輪數字宣稱精確改善幅度；未重抽或覆寫紅燈。正式 L 的原件與診斷包完整保留。

這是候選性能預檢，尚未整份重產其突變帳本／架構產物及重跑全部正式關卡，不能稱完整可合。最不確定的是後續哪個仍在#288範圍且不改P177的局部成本能解除門檻；#323 memo／排序與#300容量未混入。

1122個完整stdout/stderr保留；source-snapshots是外部調度／唯讀輔助的0644原bytes純文字資料，不是正式產品入口。ELF與來源tar留外部，hash/固定SHA/archive命令完整記錄。SHA256SUMS覆蓋除自身外全部檔案；外部copy-check保存真核對碼。
