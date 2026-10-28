此整合列車承接 #299／#316、#314 與 #318 閱讀 A。這次僅補驗收閉包與精確 P-189 原件、採入已完成的 P52，沒有改產品或新增豁免；B1 whole-memo 因原始 ELF 缺件仍未達合併條件。

# #338 唯一 current-state：B1／B2／B3 與正式驗收

更新日：2026-10-29（台北）。本輪依[最新審查 6435441274](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6435441274)處理；先前進度以[更新前固定版本](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/PROGRESS.md)保留作歷史，不再作現況。

- 已採入的 merge 基底 **M=`0ae1728c2309e1d670369289a6b8da059fa63a50`**；固定產品／正式七項 execution **F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`**。F→M 非 evidence 差異為零；本輪僅新增證據與狀態文件，不改產品、公理、測試或門檻。
- **完整 PR head／本次 evidence E：`f817f208fccc833c4a09735e904ad7e4a44dea35`**。B3 真正執行於 M；七項原正式執行於 F。各原件保留真實 execution SHA；本次 head 與 M 的非 evidence 差異為零。
- **維持 draft／未達合併條件：B1 原 ELF 缺件；B2 閉包及 B3 實跑結果如下。** 沒有合併 PR/main、force push、部署或新增豁免。

## 本輪合併阻擋

| 項目 | 狀態 | 實際來源、原件與界線 |
|---|---|---|
| B1 whole-memo | **未完成：原 R8 ELF 尚缺** | 要求 F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad` 的 base-pg／fix／fix-trace 原 bytes、完整 mode0100700；[固定 STATUS](https://github.com/ZhiQiYang/geometry-axiom/blob/cbf8df4facf87b40db0fe46581c0b20131afada2/evidence/geo337-followup-scope-20261027/whole-memo/STATUS.json)。雲端原三路徑缺失；本機 Claude 正在搜尋（使用者本輪指示）。沒有重編替代，metadata-only0/1/0不是正式反證。見 [本輪觀測](https://github.com/ZhiQiYang/geometry-axiom/blob/f817f208fccc833c4a09735e904ad7e4a44dea35/evidence/geo337-train-20261024/review-unblock-20261029/B1_STATUS.json) |
| B2.1 R8 perf／profile | **沿用原 perf／profile exit 0，附完整閉包**；原 compare／overall 1 保留 | 原36樣本、4 profiles、固定base／main、原F8 execution不移標；R8 stdout比較原紅；該次 R8 在中止點之後的嚴審計未完成。F9 另一次 compare／audit 已為 0，見下一列，不能回填成 R8 ABC 通過。完整工具／場景／建置／輸入閉包見 [B2 三項閉包報告](https://github.com/ZhiQiYang/geometry-axiom/blob/f817f208fccc833c4a09735e904ad7e4a44dea35/evidence/pr338-b2-closure-20261029/B2.md) |
| B2.2 F9 175／350 ABC | **沿用原 compare／audit exit 0，附完整閉包** | 原F9=`4f8a794f4167c3562eb182045102e86e9e37cca9`，175場景／350組、700 O2/trace命令；使用R8四個binary literal symlink，不稱F9新建置。六處stdout/stderr插入、其餘bytes、return codes、有序來源圖與五guards各列原結果 |
| B2.3 與目前產品閉包 | **本輪閉包稽核 exit 0**；原工具／輸入／來源分列，未移標 execution | 逐項列出是否讀 tests/test_geo314_commit_paths.py／決策佇列.md，及其他實際差異的非執行收據性質；閉包證明不代表改寫舊execution |
| B3 P-189精確比較／效能 | **已實跑 M，精確比較與計時各 exit 0**；175 場景、525 次呼叫；36 原序樣本，N16/32/48/64 比值 0.892801／1.118817／1.071056／1.428946；3 baseline0／27 negative1／3 restored0 | main固定adbaebf9c73ea6801d7b4d5214e4b846b132923b；僅決策887–891三場景的指定位置與逐byte文字，其餘bytes／returncode不變；N16／32／48／64 fix/main≤2不變。原strict紅與timing-only非全過保留。[B3 正式收據](https://github.com/ZhiQiYang/geometry-axiom/blob/f817f208fccc833c4a09735e904ad7e4a44dea35/evidence/geo337-b3-p189-20261029/B3.md)。歷史 L 的三個實際 C 輸入改變，故未沿用 L timing；本輪重跑 P-189，沒有重抽 R8。 |

## 正式驗收矩陣

以下已存在的綠項依其真實來源採入，沒有重跑製造新樣本。F原件可沿用到M及本輪證據提交的理由是完整非evidence內容相同，不是把執行SHA改寫。

| Gate | execution／實際結果 | 固定證據 |
|---|---|---|
| native | **F exit0**；230 suites，5328 pass／0 fail／1原Windows GDI skip；1886.996秒<2100，16MiB stack | [732ef20e](https://github.com/ZhiQiYang/geometry-axiom/tree/732ef20e34876379a37eb69693a481becebea43e/evidence/geo337-native-validation-20261027/F-complete)。不是本機約7361秒的空間量測 |
| canvas | **F exit0**；2267斷言、85goldens相符、0skip；1749.408秒<2100 | [M 固定原件](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/final-browser-delivery-20261027/F-canvas.tar.gz) |
| assembly | **F exit0**；150／0／0；192.931秒<900 | [M 固定原件](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/recovery-bundle-20261027/F-assembly.tar.gz) |
| documents | **F exit0**；47／0／0；70.974秒<600 | [45dd4d66](https://github.com/ZhiQiYang/geometry-axiom/tree/45dd4d662eac9297eda8473742c9943a1cb336cb/evidence/geo337-train-20261024/documents-F-cbf0fb62-20261027) |
| grid | **F exit0**；356／0／0；464.330秒<900；partial不冒稱full golden | [M 固定原件](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/recovery-bundle-20261027/F-grid.tar.gz) |
| space | **F exit0**；242／0，0 individual skip；原2組omission；213.725秒<900 | [M 固定原件](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/final-browser-delivery-20261027/F-space.tar.gz)；原省略timber-material、timber-source-guards |
| timber | **F exit0**；79／0，0 individual skip；原5組omission；123.626秒<1200 | [M 固定原件](https://github.com/ZhiQiYang/geometry-axiom/blob/0ae1728c2309e1d670369289a6b8da059fa63a50/evidence/geo337-train-20261024/final-browser-delivery-20261027/F-timber.tar.gz)；原省略space-height-library、projection-lifecycle、projection-placement、space-flow、projection-close |
| Reading A／oracle／RC／reader | **F正式0**；quick391.726秒，528＋1056可施工；golden／RC builder／checker各0/1/0；reader51、required-eight681原native覆蓋 | [7886f2ea](https://github.com/ZhiQiYang/geometry-axiom/tree/7886f2eaa3da7f9f4855104ca4b028d2d06ce6da)。保留6個C11_MAIN_NOT_BUTTED known-defect觀察，不說全專案零缺陷 |
| PF3 | **F正式0**；745.697秒；baseline20、19指定原assertion killed、restored20；0error/skip | [1d9b980d](https://github.com/ZhiQiYang/geometry-axiom/tree/1d9b980defec2659d7b08ee0a3ac782e00354780/evidence/geo337-pf3-20261027) |
| Q38 | **F正式0**；820.152秒；full44＝41原assertion kill＋2原ModelError＋SPM24 equivalent；baseline29／model20 | [dd2cbf6a](https://github.com/ZhiQiYang/geometry-axiom/tree/dd2cbf6a558b4af240ab4702cc8402621380881b/evidence/geo337-q38-20261027)。SPM38／40不改稱assertion kill |
| P52放置後timber耗時 | **已採入F formal／verifier／outer＝0／0／0**；369.462秒；main16／fix16，median216.281467／183.6549265ms，ratio0.849147775≤1 | [a08a036d正式原件](https://github.com/ZhiQiYang/geometry-axiom/tree/a08a036db335e88608ead761539d3e60b75e8e5d/evidence/geo337-p52-20261027)。main固定adbaebf9；normal/delay/revert-delay/wrong/missing exits0/0/1/1/1。見[本輪 P52 採入核對](https://github.com/ZhiQiYang/geometry-axiom/blob/f817f208fccc833c4a09735e904ad7e4a44dea35/evidence/geo337-train-20261024/review-unblock-20261029/P52_ADOPTION.json)；不重抽樣 |
| 全123帳本／check | S10=`82c922a3941525d3a094ac0158bdc7dea57ea360`全帳本0；**F check0／123**；114killed／5equivalent／M20crashed／3retired | 原120execution heads與失敗保留；stale／survived／invalid／blocked0；不把crashed算killed |
| 架構三裁判 | **F 0／0／0**；798edges、205generic／18product／0skip | a6生成的產品architecture receipt與F正式judge來源分開，不改標產生SHA |
| §7 axiom／card | **F兩原正式0**；axiom44baseline＋5red1/restored0；card43baseline＋53red1/restored0，116ELF保留 | [axiom E2d576269](https://github.com/ZhiQiYang/geometry-axiom/tree/2d576269ab85ef64a921bc4b15d013ca2ef5b4fb)；[card E047d93f0](https://github.com/ZhiQiYang/geometry-axiom/tree/047d93f01ba1bd349ebc256c4e8d19209bfd0f49) |

P52與其他外部證據的E，是原件提交位置；其產品execution均按原收據列F。外部總交接：[2ef90622](https://github.com/ZhiQiYang/geometry-axiom/blob/2ef9062284849ec9a46517f1137abd3e4d0a03c8/evidence/geo337-executor-handoff-20261027/README.md)。本輪未重新解包全部舊browser／special payload，沒有把原件採入稱為重新執行。各正式完整命令、原流、退出碼、環境及SHA沿固定原件查閱。

## 已決政策與未完成界線

使用者本輪直接指示按決策900–914採三場景精確白名單，不再列為待批准。#323與P-189保留各自base/main，不混用分母；原R8效能不重抽。10/26允許的是逐項完整閉包證明後沿用，不能只有「產品碼沒變」一句。

CI計費停用時依已核可流程採同源完整七項＋適用專項；runner_id0／steps=[]的Actions failure不是產品紅綠。B1尚未閉合時不宣告整條替代CI或列車可合併，也不藉「僅stale可後補」豁免它。

#335 CLI-order diagnostic exit0只代表診斷完成；兩順序都沒有觀察到兩材皆成功，不改說建構已通過。其既有分流維持，本輪不新增公理或擴成新的#338阻擋。
