# #323 PF3 原完整執行的證據封存準備

此工具只整理既有原始資料，不執行 Git、產品、編譯、測試或 publisher，也不持 heavy lock。正式來源 P 固定為 `e9fffc1cb036b6e4538a23f4dd12a9e10c5136f9`。

來源為 `/tmp/g261-next323-pf3-full-01` 與原外層 `/workspace/geo323-work/pf3-full-01`。只有原外層完整退出 0、原 summary baseline 20／19 killed／restored 20 且原 source unchanged 時，才凍結 archive。尚在執行時只回報 pending，不覆寫任何原資料；原紅燈則保存失敗 metadata，不改原 verdict、不填成功。

```text
python3 -B /workspace/geo323-work/pf3-archive-preparation/prepare.py
```

成功後唯一原始 archive 在 `frozen/pf3-full-original.raw.tar.gz`，配對 `pf3-full-original.inventory.json`、`SELECTION.json`、`SHA256SUMS` 與四份 metadata。這不是新的產品執行或裁判。

封存完整原 sources.json／summary、21 次原 baseline／case／restore 的 build/tests execution、stdout/stderr、result、所有 binaries 目錄內的 JSON fingerprint／tests counts、完整 outer、原工具及其裁判／建置腳本、共用 runner／test-entry／reaper。對每個原 CASES 的實際修改目標保存原 bytes，與 P 的原 source hash、實際 mutant hash、精確原字串變更是否吻合分列；沒有擴張或縮減原 CASES。

不收 ELF、object 或每案的可重建全 source 副本。每個實際 binary／object 仍記錄原 bytes／SHA256；每案 source 只讀明列的修改目標，baseline source 另讀原目標及工具／裁判腳本，全部核對原 sources.json。其餘原來源由可解析 P 與原 204 項 sources.json 重建。排除範圍不冒稱新跑。archive 完成後再逐 member 重驗 bytes／SHA，量得實際壓縮大小必須低於 90 MB，不能截斷 raw。

`test_entry.py` 是這次原外層 `python3 -B /workspace/geo323-work/test_entry.py /tmp/g261-next323/tests/pf3_mutation_check.py --out /tmp/g261-next323-pf3-full-01 --jobs 1` 的 runpy launcher；各案真正執行 unittest 的則是原 PF3 自己的 `--child` 子命令。archive 已保存實際入口 `tools/test_entry.py` 的完整 1,227 bytes，SHA256 `eafca4c791303a2cf4692aefe972531ceac33693e6fa0956be43382fbe1f2e16`，與原入口檔及原 selection 核同。原封存衍生 `metadata/SCOPE.json` 把它寫成「not present in the PF3 command」並不精確；以原 outer command 與本段更正為準，archive／raw 原樣保留。

工具準備時沒有執行上述封存命令。最終結果只以完成後的原收據與實際 frozen 產物為準。

## 已完成的原結果與封存

原外層已完整退出 0；受驗 SHA 前後均為 P `e9fffc1cb036b6e4538a23f4dd12a9e10c5136f9`，前後工作樹與 patch 皆空。原完整 PF3：baseline 20／0 failure／0 error／0 skip，19 個 mutation 全 `killed`、各正常退出 1／具名 marker，restored 20／0 failure／0 error／0 skip；`originalSourcesUnchanged=true`。

本封存命令已在外層終態後真正執行，退出 0。唯一 archive 為 **402,683 bytes／297 members**，SHA256 `ca73356c0e33a5417cd370a411f3088c7735b528103542b3603210ba6b1990b4`。全部 member 已逐項重讀並核 bytes／SHA，原資料沒有更動。實際保存 20 份 mutant 目標原檔（host-identity 同時改 H 與 host 兩檔）；其相對 P 的 hash 及原 CASES 的完整重建驗證都在 metadata。42 份實際 executable 的 bytes／SHA 全列排除 inventory，沒有把可重建 binary 或整棵 source 副本放入 archive。

這份封存只證明上述原 PF3 完整執行，不是另一次測試、完整 native 或效能驗收。此子任務未執行 Git、publisher 或產品，也沒有取得 heavy lock。
