# 正式 L3 P-189：通過

本輪固定來源 `6589248c9a94bdf0460d8f84dd1610e51048188b`，唯一 parent S3 `19401ca5448e162ee6140fed37b64b83b31ddec8`；S3→L3 僅 tests/mutants_results.json。這是 L3 新 archive／新建置／新量測的正式結果，不沿用 L2 或候選成績。

generator selftest、16 controls、三方 build、175 equivalence、36 timing、check、supervisor 均真 0。prepare 的頂層工具觀察是 session 75565/chunk 7de041；supervisor 是 session 1850/chunk 900b3a。prepare 觀察由準備代理依工具結果轉錄，supervisor 觀察由 root 轉錄；並非原 transport，也不是封裝階段重新 wait。

| N | main median 秒 | base median 秒 | L3 median 秒 | L3/main |
|---|---:|---:|---:|---:|
| 16 | 0.1188524570025038 | 0.17758666799636558 | 0.12788341000123182 | 1.0759845713457803 |
| 32 | 0.22071910399972694 | 1.1681115940009477 | 0.23993698300182587 | 1.0870693956882078 |
| 48 | 0.32143088100565365 | 4.823500583996065 | 0.5177576200003386 | 1.6107899103547298 |
| 64 | 0.6566931790002855 | 17.318912367001758 | 0.9734185269990121 | 1.4823033924014444 |

原 ≤2x 門檻未改；N16/32/48/64 各三輪正反交錯共 36 有效樣本。t0 仍在 Popen 回傳後、communicate 前；沒有挑樣或重抽。main adbaebf9c73ea6801d7b4d5214e4b846b132923b、base 3e600772076465fc65a26ac09055028301c0fb0b，gcc -std=c11 -O2，16MiB stack、900 秒 timeout、PYTHONOPTIMIZE 移除且無 Python -O。

16 項裁判控制是本輪 selftest 實跑（2 正／14 負）。等價原判準為 4 生成場景三方有效載入且 stdout 同、171 固定場景 base/final 同；本輪額外觀測全部 175 列三方 stdout 同。175 中只有 75 成功 load，另 100 是歷史受控拒絕，不稱全部成功載入。

只讀核對將三方 archive、source-index、實際來源檔及各 commit 的 Git blob 逐 bytes 綁定，495/673/673 檔全部相符；171 固定場景另綁 base Git blob。runner/gen/calibration 原 bytes、三個 binary hash、六階段 argv／原流 hash、全部 phase 的 repository_head=L3、前檢排程與樣本順序均核同。1122 份完整 stdout/stderr 全部保存。

raw/prepare-receipt.json 中「尚未執行」等欄位描述準備當時，實際階段完成以 phase-receipts、receipt 及 readonly-source-review 為準。method 保留當時尚待真 SHA 的準備文件，沒有事後改寫成執行收據。

本包只完成正式 P-189；其他正式關卡由各自 L3 收據驗收，不據此宣稱全部通過或 PR 可合併。此輪沒有另做產品性能撤回；先前 6c/4bd 的精確撤回證據仍以自己的來源與原件保存。最不確定的是單輪量測對不同環境的代表性，而非本輪門檻或來源判定。

場景輸入依固定 runner 的選取規則：生成場景使用原名，171 固定場景使用 repo- 前綴；每份輸入皆先核 scene_sha256 與固定 base Git blob 後才複製。method/inherited-L2 是方法來源歷史，未冒稱本輪執行那些 L2 工具；本輪實際方法及最小差異分別保存。

ELF、archive、來源整樹及 pycache 不進包；其 hash／重建依據保留。source-snapshots/*.py.txt 是原 bytes 的 0644 純文字資料，非新增正式部署工具。artifact-mapping 逐檔綁原件；SHA256SUMS 涵蓋除自身外全部檔案。
