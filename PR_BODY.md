# #314：保留有序操作歸因的單軸相位差提交規則

舊雙軸場景可以保值換來源、改卡與移除一軸；仍為雙軸時，非保值來源切換依原規則拒絕。本次補上「最終引用相同」遮掉有序操作的缺口：舊 u=A400，先解除成400、再改卡A500、最後綁回A500，最後一步400→500不是保值，應拒絕；先改卡A500、解除500、再綁回A500則放行。兩個例子的最終 stores／source 相同，必須使用原步驟事實判斷。

本次採用使用者明示的實作授權與 `決策佇列.md` 2026-10-22 題3B／題4鎖定決策；舊草稿 §10-4 的「待核可」及舊 agent 推論不當作公理文字已修改或默認逐條核可。公理、決策文字與 K 未改。新 guard 只在舊／新 stagger 值不同且該軸有 ordered facts 時先查有序歸因；原同參數引用改卡例外與最終軸數判斷保留，未為中間變動最後回同值另增拒絕。

## 唯一 current-state 矩陣

產品／測試來源 **S=`3b0b634feb54266700cc61f26c34d7aeac4c0314`**；證據 head **E=`ed1ab195aa5cd6a7d03de708ff63724404fcbbf6`**。E 相對 S 只新增本輪 evidence。來源分支 `codex/geo314-one-axis-stagger-20261022`，正文分支 `codex/geo314-one-axis-stagger-20261022-prbody`。

| 項目 | 原 execution／適用來源 | 原 exit／當前狀態 | scope、skip 與限制 |
|---|---|---|---|
| 新 guard 與同終態正反例 | leaf `f61413ba785b67d2f455e4977e8b8da06050d654`，已納入 S | 尚未動態執行；exit=null | 新增2方法；未放寬斷言 |
| 既有 legacy-value unit source-control anchor維護 | S 的單leaf `3b0b634feb54266700cc61f26c34d7aeac4c0314`，來源 `1cd2fc216299041a557654a874509a33884af819` | 單字串靜態維護完成；動態未跑，exit=null | 2參數pattern改真6參數呼叫；replacement仍if(0)，23方法／11個控制與全部斷言不變 |
| #323 普通合併 | `c939d4f35ec6083e7c661f50a0e90fe3ded9f440`，前棒 `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6` | merge完成、一般push | 保留load residual與AppValidationInputs；不是驗收裁判 |
| 小型 AST／anchor／shared metadata | S 前工作樹、對應內容已提交 S | 靜態收集exit0；diff-check0 | 101唯一ID；M102/M103/M105/M121各1 anchor；count15/22/13/47；不代替產品驗收 |
| 原 canonical reader 機械生成 | c939的未提交source工作樹；原input hashes與實況完整記錄，內容已納入 S | 原 `python3 -B geometry-guide/sync_axiom_reader.py` exit0 | 僅機械生成；不是在乾淨S執行reader裁判 |
| 新 M121 修正撤回／恢復 | S 的專項待執行 | 未跑；exit=null | 需真0／1／0原streams；未宣稱killed |
| #314 stagger47／ordered facts／route／migration | S | 未跑；exit=null | 等root資源時槽，skip=null |
| reader原裁判 | S或最終合流來源 | 未跑；exit=null | 原sync `--check`、reader測試與相關原追溯檢查待跑 |
| native與6個browser job | S | 未跑；exit=null | 舊cc67結果不改標為S通過；本輪允許skip尚無結果，記null |
| 完整ASM | S | 未跑；exit=null | 舊cc67完整ASM保原來源角色 |
| 原 `mutate.py --check`／整份帳本 | 新source與tests使舊帳本stale | 未跑；exit=null | root最後統一重產一次，不沿用舊execution冒新source |
| 原架構三裁判／四檔重產 | S或最終合流來源 | 未跑；exit=null | 暫保#314原四檔全套舊bundle；明確stale，非新來源收據；root最後Linux統一重產 |

S 已交棒 combined，後續共用檔順序是 #314→combined→#318→無木工。原三裁判、編譯、Chrome、benchmark與scan目前受root重工作時槽安排，沒有把等待排程寫成通過或允許skip。

## 本次單檔維護與來源界線

在#318 owner確認停止編輯並暫交單檔後，以正常no-commit cherry-pick保留已審的唯一leaf：舊source-control的2參數pattern在真產品已是6參數呼叫後不再命中。現改成與M102相同的完整6參數pattern，保原方法、stagger-w06、具名marker、replacement和全部assert；沒有帶入#318其他產品／tests／expected修改。source commit只改 `tests/test_geo261_wood_grid_application.py` 一行，已普通push並核ls-remote同SHA。

原cherry-pick夾帶的兩份318 evidence導致metadata衝突，原exit1與git restore拒絕unmerged的原exit1都保留；確認兩檔在本身原HEAD不存在後只移除此incoming metadata，完成單leaf正常commit／push／ls-remote皆exit0。這是Git維護記錄，不算產品測試或語義反證。動態仍全未跑，尤其原具名legacy-value方法的baseline／撤guard／restored 0／1／0尚待時槽。

舊feature／registry來源 `8033aa756c62f654333c24d1276d4b61beb31a45`、證據 `25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb` 與其reader生成原件保留原角色。以下舊靜態／reader連結沒有改標成新S實跑。新S只補test anchor，產品C/H/JS、registry、canonical、架構四檔及保護文字不因本維護改動；tests/*.py的oracle來源變更仍需root最後統一整份帳本，不沿用舊execution冒新鮮。

- [單leaf維護進度](https://github.com/ZhiQiYang/geometry-axiom/blob/ed1ab195aa5cd6a7d03de708ff63724404fcbbf6/evidence/geo314-anchor-maintenance-3b0b634f/PROGRESS.md)
- [原Git維護嘗試](https://github.com/ZhiQiYang/geometry-axiom/blob/ed1ab195aa5cd6a7d03de708ff63724404fcbbf6/evidence/geo314-anchor-maintenance-3b0b634f/original-attempt/receipt.json)、[完成及push原件](https://github.com/ZhiQiYang/geometry-axiom/blob/ed1ab195aa5cd6a7d03de708ff63724404fcbbf6/evidence/geo314-anchor-maintenance-3b0b634f/completion/receipt.json)
- [修正後純靜態anchor盤點](https://github.com/ZhiQiYang/geometry-axiom/blob/ed1ab195aa5cd6a7d03de708ff63724404fcbbf6/evidence/geo314-anchor-maintenance-3b0b634f/STATIC_AFTER.json)、[完整原件hash索引](https://github.com/ZhiQiYang/geometry-axiom/blob/ed1ab195aa5cd6a7d03de708ff63724404fcbbf6/evidence/geo314-anchor-maintenance-3b0b634f/INVENTORY.json)

## 來源與實際原件

- 權威審查讀自 handoff `ea2748248d47563f8559638ccb70ec0ed21910d9` 的 `handoff/pr-reviews/314.md`；本輪不把舊審查錯寫成針對 S 的新審查。
- [本輪進度與完整待跑項](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/PROGRESS.md)
- [靜態原件與保護文字blob](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/SOURCE_STATIC.json)、[shared count原值](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/SHARED_UNION.json)
- [原reader生成收據](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/reader-sync-source/receipt.json)、[完整stdout](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/reader-sync-source/stdout.txt)、[完整stderr](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/reader-sync-source/stderr.txt)
- [逐檔bytes／SHA256索引](https://github.com/ZhiQiYang/geometry-axiom/blob/25c15f7b81de07d3c9c66a5553bf9bb43aa8f3fb/evidence/geo314-refresh-8033aa75/INVENTORY.json)

M99–M120 保原號、原判決：21 killed＋M110 equivalent。M110原單撤baseline／mutant／restored是0／0／0，不能寫22 killed；原paired MP1+MP3深度反證與舊原件保留。新M121只撤本次新增guard；M102只重錨新實際呼叫，M103與M105原碼anchor仍唯一。原 H候選事實、seal、preview／confirm漏斗與 World／dump／history邊界不擴張。

歷史正式來源 **F_old=`cc67e2518f6ab331b5ab9fdbcd5bd6334134377f`** 的原七項、完整ASM與三架構保存在 **E_old=`1e9f4873e6563bb4b90595bb1965532ea98619b3`** 的 [原結果索引](https://github.com/ZhiQiYang/geometry-axiom/blob/1e9f4873e6563bb4b90595bb1965532ea98619b3/evidence/geo314-final-cc67e251/ORIGINAL_RESULT_INDEX.json)。原job測試皆0，但整輪wrapper／outer實際1（assembly出版label衝突），publication-only補修0；原失敗沒有改判。Linux原Windows GDI skip1、canvas預期例外1及各partial／omitted scope都仍依舊收據。這些只描述舊F，不列為S的當前綠燈。

最不確定的是本次新guard的真撤回負控尚未跑；parameter-package混合操作、facts realloc／OOM與完整P177全域動態計數也未從靜態接線推成已測過。完整新來源驗收與原始輸出待時槽，不宣稱本PR已全綠。

未force push、未合併PR；合併仍等待#288進main。GitHub API受限，本檔已交正文分支供套用，沒有宣稱線上正文已更新。
