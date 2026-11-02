# #344 原完整 canvas 三相終態

固定產品 F `d794a7447b98a82fb35c1dccaedc3443e2230933`；只撤app清錯一行的local control V `acd623857f2cc117b548907c2b96b638d9e1b31a`，未push。三個乾淨獨立checkout、port、profile、TMPDIR，原Node24.22.1／Chrome156／完整canvas，原22個scope/modifier全清除、原golden與skip不變；每相原2100秒。

| 相 | 原Node命令時間UTC | 秒 | gate exit | 結果 |
|---|---|---:|---:|---|
| fixed-02 F | 06:35:03–07:03:05 |1681.676534|0|2267pass/0fail/0skip，85golden matched |
| withdrawn V |07:04:01–07:32:10|1689.603122|1|2264pass/5fail/0skip：3具名產品失敗＋2原golden後果 |
| restored F |07:41:42–08:09:57|1694.881392|0|2267pass/0fail/0skip，85golden matched |

三個具名紅是P53-3「重試只讀取，不重送修改」、P61-10「載入未送達時，重試連線保留原幾何與來源」、P61-11「載入已送達但回應遺失時，核對核心後恢復正確來源」。兩個golden後果為P53預期28實27／P57預期56實54，不冒稱五個獨立產品bug；恢復後全部原段精確相等。P38原預期fb-auto-probe例外每輪各1，未寫成整場零例外。

734個runtime來源在每相前後raw/mode/mtime完整相同；fixed/restored之間734hash全同，V唯一不同輸入是app.js。三個配置的native二進位檔與sidecar跨三相逐byte相同、原inspector fresh；這是配置檔案身份，沿原release_gate限制不冒充執行中native程序attestation。原golden全程未變、未timeout／中斷，原Node exit與外層gate exit一致。

最初fixed P76 ENOENT（private TMPDIR缺geometry-tests父目錄，1827pass/0assertfail但fatal exit1）及後續0.065秒gate葉已存在拒件均保留原件，不洗紅。完整48檔require/38個FS寫出callsite預檢、36parent真writeprobe後，fixed-02與V/R均用相同正確目錄配置。沒有改產品斷言、golden或timeout。原Node VM 9/6/9另存，不能代替本真browser三相。

原source／preflight／fixed-complete子代理peer PASS保留；新全部三相子peer因同模型capacity未完成，主代理有界核原件的結果為ORIGINAL_FULL_0_1_0_VERIFIED_PRIMARY_REVIEW，不冒稱新子peer PASS。請最新獨立審查讀本原件。原正式F兩run20jobs／原verifier另見../ci-F；full三相不改標成CI execution。
