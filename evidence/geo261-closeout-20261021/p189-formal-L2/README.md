# 正式 L2 P-189：通過

本輪固定來源 `249571fe2477845d5330f6190dad965bf327f43b`，唯一 parent A2 `cbefb39b47fb0edcfaf003d2c1101929fea244c8`；A2→L2 僅 tests/mutants_results.json。這是 L2 新 archive／新建置／新量測的正式結果，不沿用 6c 或 75f 候選成績。

generator selftest、16 controls、三方 build、175 equivalence、36 timing、check、supervisor 均真 0。prepare 的頂層工具觀察是 session 7647/chunk 9d39ed；supervisor 是 session 96721/chunk a58d5d；兩者明示為 root 回報後轉錄，並非原 transport 或封裝代理重新 wait。

| N | main median 秒 | base median 秒 | L2 median 秒 | L2/main |
|---|---:|---:|---:|---:|
| 16 | 0.11301125299723935 | 0.1766907569981413 | 0.11745617599808611 | 1.0393316849690653 |
| 32 | 0.20045346400002018 | 1.116580896999949 | 0.2733078469973407 | 1.363447862379236 |
| 48 | 0.3395307739992859 | 4.798283307001839 | 0.4967130780023581 | 1.4629397864342122 |
| 64 | 0.5384727830023621 | 17.163470482002595 | 0.9393659159977688 | 1.7445002712303253 |

原 ≤2x 門檻未改；N16/32/48/64 各三輪正反交錯共 36 有效樣本。t0 仍在 Popen 回傳後、communicate 前；沒有挑樣或重抽。main adbaebf9c73ea6801d7b4d5214e4b846b132923b、base 3e600772076465fc65a26ac09055028301c0fb0b，gcc -std=c11 -O2，16MiB stack、900 秒 timeout、PYTHONOPTIMIZE 移除且無 Python -O。

16 項裁判控制是本輪 selftest 實跑（2 正／14 負）。等價原判準為 4 生成場景三方有效載入且 stdout 同、171 固定場景 base/final 同；本輪額外觀測全部 175 列三方 stdout 同。175 中只有 75 成功 load，另 100 是歷史受控拒絕，不稱全部成功載入。

獨立只讀核對將三方 archive、source-index、實際來源檔及各 commit 的 Git blob 逐 bytes 綁定，495/673/673 檔全部相符；171 固定場景另綁 base Git blob。runner/gen/calibration 原 bytes、三個 binary hash、六階段 argv／原流 hash、全部 phase 的 repository_head=L2、前檢排程與樣本順序均核同。1122 份完整 stdout/stderr 全部保存。

raw/prepare-receipt.json 中「尚未執行」等欄位描述準備當時，實際階段完成以 phase-receipts、receipt 及 readonly-source-review 為準。method 保留當時尚待真 SHA 的準備文件，沒有事後改寫成執行收據。

本包只完成正式 P-189；其他正式關卡由各自 L2 收據驗收，不據此宣稱全部通過或 PR 可合併。此輪沒有另做產品性能撤回；先前 6c/4bd 的精確撤回證據仍以自己的來源與原件保存。最不確定的是單輪量測對不同環境的代表性，而非本輪門檻或來源判定。

首封裝方法錯將固定場景當成無 repo- 前綴的實體檔名，於建立 bundle 前真 1；其方法、命令、原流與結束碼保存在 packaging-history。v2 僅依固定 runner 的選取規則補正封裝映射並保存失敗，未重跑產品或效能量測；正式驗收仍為原輪真 0。

ELF、archive、來源整樹及 pycache 不進包；其 hash／重建依據保留。source-snapshots/*.py.txt 是原 bytes 的 0644 純文字資料，非新增正式部署工具。artifact-mapping 逐檔綁原件；SHA256SUMS 涵蓋除自身外全部檔案。
