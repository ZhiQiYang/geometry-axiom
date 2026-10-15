# #201 承接 PF-2 main：完整雲端 native

依[第11班預檢6160847493](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6160847493)，一般合入新 main `0eb447e00605f6df117711b03e6c98ccabbcd026`。本輪受測乾淨 head `aa6d82c84f69a9ded91371e6ed11faf2e2ac213a`，只有 expected 發生衝突；無 rebase、force push 或 PR merge。

三方共同基底 caf49852，按各 suite 保留獨立增量：Node659＋44＋0＝703、ownership9＋4＋0＝13、grid13＋2＋0＝15、PF2 layout0＋0＋17＝17；main compatibility28保留。88登錄suite、82個有count的suite、2776計數項。三份原expected及完整解法見 `merge-proof.json`，不是放寬期望數。`engineering_bridge.inc` 保留preview刪除token和finish_batch分派；`run_all.py`承接main的PF2 suite。

核心C、整個geometry-core、mutate/run_tests與P105帳本精確等main（`main-core-diff.txt`為空）；P104測試檔精確等前輪fd66（`p104-diff.txt`為空）。沒有重寫ledger hash，沒有再編譯／執行核心mutants或重做16次期限對照。Native內的mutation check只核main既有執行收據／來源新鮮度，並使用獨立空cache避免其他來源的歷史執行檔干擾；不宣稱已重新核驗缺席的mutant binary bytes。上一輪213在caf組合的2758/0/1原件留原目錄，不移作本輪證據。

## 實測結果

`ulimit -s 16384; python3 -u tests/run_all.py --build`：**88/88 suites、2775 pass／0 fail／1允許的Windows GDI skip，actual OS exit0，child wall 821.886秒**（suite表加總776.2秒，另含建置及runner前後處理）。Node703/703、reader41/41、PF2 layout17/17。所有tracked檔案執行前後hash相同、結束git status空。child status先寫 `native-actual-exit.json` 再做任何複製或後處理。

`cloud-native-originals.tar.gz` 保存本輪stdout/stderr、actual exit、逐suite原件及5支實際binary/fingerprint。共用日誌目錄中早於本輪開始時間的檔案分開排除，見 `native-log-selection.json`。`executed-sources.tar.gz` 保存來源及fixture，包含fingerprint完整來源引用（即使C檔位於歷史evidence目錄）及實際materialized engineering JSON HARNESS。一般未驗的UI圖片未打包；全tracked執行前後raw hash另存。fingerprint依工具規則CRLF→LF，archive inventory則保留原始bytes hash。

## 驗收界線

作者重開交付封包核驗：native219件、來源／fixture1347件逐件bytes／SHA全符，5支binary及各自fingerprint的全部50／51個來源引用亦核符，結果與原執行器見 `delivery-verification.json`。`native-six-cases.json` 單列本輪完整Node中四容量案、preflight及legacy六案，全部通過；這些仍是本輪雲端耗時。三份 `*-expected.raw.json` 是固定Git refs的逐byte原件；不帶raw的快照為同值格式化JSON。審查對二進位封包的獨立讀取能力另按其原留言界線，不假稱外審已重新解包。

這是雲端完整非瀏覽器登錄測試，**不是正式WSL收據或7項全綠**。修正交回既定第11班固定來源驗收，不另排WSL全量。第9班首紅／Rule2未豁免及P104本機20次量測原件照留；不追加base64鏡像，不宣稱雲端取得20份WSL完整TAP。舊caf旗標記錄保留為歷史，本輪一般合流預檢exit0；GitHub已解除衝突，但不代表正式M1解除或已ready。
