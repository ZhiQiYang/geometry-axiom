GEO-261 已在固定來源 **F2 `8f76f2b7d6f669670e5834310bfc26495b4a4aa6`** 完成雲端最終驗收：正式17項及其publisher均原退出0，seven／specials兩段outer均0；九個額外phase亦已完成。首次Cperf因ENOSPC原退出1保留，復原環境後只重跑該項並通過。請依已鎖定的Actions billing替代裁判複審；本PR未合併、未force push。

## 受驗來源與產物

| 角色 | 完整SHA／用途 |
|---|---|
| 產品／tests基線 P；整份ledger真執行來源 | `b6646d10751a0d85a2f03f5d24fbe1073cb78980` |
| ledger產物 L | `aa02a65e9d3923cc14c13340f05ed16c8b7d4fce` |
| canonical reader trace修復 P2 | `8a80abc1402b0c4c394969025c93a6019b4bb91d` |
| 最新產品修正 P3；最新架構真執行來源 | `55b9fb6479485361d9e2283a95e4355f5fca76db` |
| Linux架構四檔產物 A3 | `8f76f2b7d6f669670e5834310bfc26495b4a4aa6` |
| 唯一正式驗收來源 F2 | `8f76f2b7d6f669670e5834310bfc26495b4a4aa6`；與A3同提交 |
| 最終證據快照 E | `4b665fae21ab63aaffb7d84f6a32d5a469ba1675`；後續證據提交不替換受驗F2 |
| 本文提交 | `codex/geo261-final-prbody-20261022` 的 `PR_BODY.md`；以該分支實際HEAD解析，不自我引用 |

帳本在P整份重產，precheck／full／checkafter原退出1／0／0；78＝70 killed＋1 crashed（M20）＋4 equivalent＋3 retired，75筆真execution綁P。L是產物提交，沒有冒稱帳本在F2重產。後續來源依原closure／oracle／tool hashes核對，P3與F2原 `mutate.py --check` 均0；F2的stale／invalid／survived／blocked皆0。

最新架構在P3的雲端Linux依原schema重產四檔，原scanner0、generic205／0、product18／0；601＝333 owned＋268 excluded、796 edges、0 diagnostics。manifest／scan bytes未變，report／receipt更新，closure `303ee650…`；A3為產物提交。F2再獨立跑原三條正式命令，均0，沒有要求回使用者電腦重產。

產品修正包括：P73以SVG的hidden attribute守門；canonical header即時窄讀仍完整驗證原格式、原full API／decoder不變，沒有跨consumer cache；raw snapshot只省去成功typed BOX必覆寫的純計算，保留來源求值順序及錯誤partial bytes。P3只在完整新盤點精確等於原immutable snapshot keys時重用Path／既有排序；逐檔完整讀取、檔型／排除規則、集合比對及最後再盤點都保留，沒有內容／stat／TTL快取或減少freshness守門。P2由原同步器修正唯一canonical HTML的I11 trace，SSOT／生成器／原測試不變。

## 同F2正式17項

| 項目 | 原退出 | 真結果 | 秒／正式CI時限 |
|---|---:|---|---:|
| native：`ulimit -s 16384; python3 tests/run_all.py --build` | 0 | 224 suites；5185＝5184 pass＋允許的Windows GDI 1 skip | 1749.343／35分 |
| canvas | 0 | full2267／0；completed=true、85段golden matched、P73=69 | 1720.939／35分 |
| assembly | 0 | 150／0；原workflow指定partial子組 | 191.268／15分 |
| documents | 0 | 47／0；原RESULT沒有completed欄 | 61.913／10分 |
| grid | 0 | 356／0；原workflow指定partial子組 | 455.097／15分 |
| space | 0 | 242／0；full-space-suite各group完整 | 213.333／15分 |
| timber | 0 | 79／0；原timber子組各group完整 | 127.109／20分 |
| `python3 tests/mutate.py --check` | 0 | 78筆有效；70 killed＋1 crashed＋4 equivalent＋3 retired | 1.873／專項 |
| P52 main準備 | 0 | 原clone／checkout／build皆0；準備與量測分列 | 31.231／專項 |
| P52放置後timber可見時間 | 0 | main243.980630／fix179.233603ms；ratio0.73462226489；各16筆，原≤1.0 | 377.196／專項 |
| P52 verifier | 0 | 9節點真退出／driver／無timeout-crash核對通過 | 0.123／專項 |
| Q38完整gate | 0 | 42＝41 killed＋SPM24 equivalent；native27／model20基準全綠 | 292.236／專項 |
| §7兩原runner | 0 | 各exit0；53＝50產品＋3裁判，全killed／恢復0；V01–V05 red1／恢復44綠 | 649.413／專項 |
| P-189三方量測及逐bytes比對 | 0 | 36次timing全原0／load_ok；175組dump相同＝75接受＋100拒絕 | 177.100／專項 |
| 原架構scanner | 0 | 同F2獨立執行；333 owned／796 edges／0 diagnostics | 5.123／專項 |
| 原架構generic | 0 | 205／205、0skip | 0.599／專項 |
| 原架構product | 0 | 18／18、0skip | 12.775／專項 |

七個產品job都在原CI時限內；外層watchdog不代替正式時限。assembly／grid保留原partial filter，不稱full golden；documents未杜撰completed。canvas原例外總數1＝P38預期探針1，非預期0；原firstTransportFailure／firstNetworkFailure trace照存，不稱全程無傳輸錯誤。native內原replay同F2為6／6，與P-189的175組逐bytes比較分列。

Q38的41 killed含SPM38／40兩個具因果的ModelError，未全改稱AssertionError。§7卡片原基準43、53筆恢復皆0；公理原基準44，V01–V05各具名正常紅1、恢復44綠。沒有將compile error／timeout當killed。原架構命令：

```text
python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python -B tests/test_architecture_contract.py
python -B tests/test_product_architecture.py
```

完整命令、真退出、原stdout／stderr、環境與版本、SHA、時間及hash見[逐項收據](https://github.com/ZhiQiYang/geometry-axiom/tree/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts)、[原始封存](https://github.com/ZhiQiYang/geometry-axiom/tree/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/raw)及[進度索引](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/PROGRESS.md)。正式凍結彙總已公開於 `78500160d918d992a2929bcf0027891121694a6e`，METRICS SHA256 `28688104…`；[最終完整性核驗](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/evidence-integrity.json)另核公開Git blobs與封存。

P52五個原等待控制normal／delay／revert-delay／wrong／missing真退出0／0／1／1／1，全部expected，verifier核完整9個Node。P-189依原main `adbaebf9…`／base `3e600772…`／F2三方交錯，每點3輪、共36樣本，原四點分別通過≤2×：

| N | main median秒 | base median秒 | F2 median秒 | F2/main |
|---:|---:|---:|---:|---:|
| 16 | 0.1154 | 0.1744 | 0.1117 | 0.9679376083 |
| 32 | 0.1946 | 1.0690 | 0.2292 | 1.1778006166 |
| 48 | 0.3091 | 4.8610 | 0.5253 | 1.6994500162 |
| 64 | 0.5273 | 16.6855 | 0.9614 | 1.8232505215 |

175組base/F2的loadfile回覆＋dump全逐bytes相同；100組是原本拒絕，沒有冒稱175組全載入成功。四個性能場景、36次timing均成功，未挑點重跑。

## 同F2九個額外phase

各撤回在隔離F2 clone上套明列patch，保存dirty variant／source／tool hashes，再還原F2；沒有把撤回工作樹冒充乾淨正式F2。表中「outer0」與預期的原紅退出分欄；Cperf首試環境失敗另列。 九phase彙總已凍結，METRICS SHA256 `ef04d730…`；完整原資料與彙總均由最終證據索引連回。

| Phase | 完成outer | 真結果與範圍 | 已公開證據 |
|---|---:|---|---|
| P73 controlled | 0 | fixed／withdrawn／restored **0／1／0**；三before皆true、after true／false／true；各明確原callback一次，例外0，最後source／clone clean | [0978a341](https://github.com/ZhiQiYang/geometry-axiom/commit/0978a3411e2cf969cc893bc920ef10426d410d90) |
| P52 runtime | 0 | 撤回原gate1、恢復0；各phase四timing Node全0、各side16，最後clean | [f2ea3457](https://github.com/ZhiQiYang/geometry-axiom/commit/f2ea34577fca848907c3b952085b4c559d2cbd06) |
| canonical reader | 0 | 原具名idempotence方法 **0／1／0**；I11 facts／facts_prepare trace具名AssertionError；SSOT／test／generator不變、最後clean | [3bba83cb](https://github.com/ZhiQiYang/geometry-axiom/commit/3bba83cb0a1625783f6cd600260e54606c463ff5) |
| contact checker | 0 | 原具名staticmethod **0／1／0**；只撤checker三行，產品三input不變；原Regex AssertionError，最後clean | [5118a5df](https://github.com/ZhiQiYang/geometry-axiom/commit/5118a5df13ed3fd901f13552aeee3a70112b9dce) |
| parser prepare | 0 | 14 input/context hashes前後同、F2 clean；compiled=false／testsRun=false，不冒稱已跑差分 | [915ed86d](https://github.com/ZhiQiYang/geometry-axiom/commit/915ed86df36b67b0efcca2c7a4729a3dec021922) |
| parser O2 | 0 | 原compile／run0，199810 comparisons／PASS，stderr空，來源hash不變 | [cfe132e9](https://github.com/ZhiQiYang/geometry-axiom/commit/cfe132e9) |
| parser ASan／UBSan | 0 | 原compile／run0，199810 comparisons／PASS，stderr空，counts／transcript同O2，F2 clean | [e60c7c0a](https://github.com/ZhiQiYang/geometry-axiom/commit/e60c7c0a19a2cf209734511b9d20c765bf5deb58) |
| 累積Cperf retry1 | 0 | N64三方各3筆；9timing全0／load_ok，三方dump同正式F2；withdrawn>2×紅、restored≤2×綠，最後F2 clean | [84c511fc](https://github.com/ZhiQiYang/geometry-axiom/commit/84c511fc404c2f5156ddd4ee6ea3f650a6331a2f) |
| Chromium154固定P73 subset | 0 | 154.0.8037.57／Node24.19.0，原P73 **69 pass／0 fail／0 skip／0 exceptions**、completed=true、source clean；partial golden原本未比較 | [6c7cc5a4](https://github.com/ZhiQiYang/geometry-axiom/commit/6c7cc5a4d0d2e2ebddc74740f04cdc78227d4f17) |

P73修正使用 `svg.hasAttribute('hidden')`：SVG沒有HTML的hidden反射屬性，本輪觀察為hidden property undefined、attribute true、computed display none而CTM非null，舊callback可插入假grid。controlled phase明確呼叫真app `syncSpacePlanAnnotations()`一次，使用同F2 `uiux_review_test.js:219`的原predicate／訊息，沒有改測試或造SVG。這只證明受控callback時點；**F1自然subset原撤回0／恢復0、工具outer1不足自證仍保留**，不宣稱已被本工具殺到。

舊版固定F2使用原 `GEOMETRY_UIUX_FIX_ONLY` 子集、同predicate，79.997秒內通過；不稱完整canvas／full golden，也不要求154撤回紅。先前Chromium154隔離dump-dom的30秒timeout124／真−9／stdout空與fixed未執行原件照存，根因未證。現在的fixed subset通過不證明154原版曾經綠。

P52 runtime只撤回P3一檔至old F（恰等P3 parent），再恢復；原main／fix／fix／main、每block8、原fix median≤main均不變：

| 額外phase | main median ms | fix median ms | fix/main | 原gate退出 |
|---|---:|---:|---:|---:|
| withdrawn runtime | 205.5316555 | 217.191353 | 1.0567294486663636 | 1 |
| restored F2 | 202.316803 | 172.937228 | 0.854784305780079 | 0 |

F1正式P52／verifier原1（ratio1.03825180997）保留歷史；F2正式及本次反證沒有修改原≤1.0、不挑樣本，也不據此推斷原約9.3ms差額的唯一原因。

累積Cperf只驗N64的整組六個C來源性能撤回，不是每個微優化個別必要，也不是又跑完整P-189：main／withdrawn／restored median **0.476／1.2209／0.9381秒**，withdrawn/main **2.564915966386555**、restored/main **1.9707983193277312**。9個timing程序仍全0，語意dump與門檻判決分列。第一次因/tmp ENOSPC在compile／semantic／perf前原outer1、截斷JSON原bytes已公開於[be90acec](https://github.com/ZhiQiYang/geometry-axiom/commit/be90acece0352d5fc971fb9802ebedfb5e5388c8)，沒有修補成有效JSON或算產品性能紅；恢復環境後僅本item新scratch重跑，正式17項原綠不變。

同F2 native32個既有控制／96筆baseline-mutant-restored原raw另補索引[375aee12](https://github.com/ZhiQiYang/geometry-axiom/commit/375aee120677cd9b8da972d159218ab972842750)。它是已執行native的補充，不是32個unittest方法、不新增第18個正式job或第10個extra phase。parser兩差分也只是額外等價證據，不冒稱mutation ledger。

## 審查回覆與驗證限制

唯一權威來源是使用者指定的[handoff保存全文](https://github.com/ZhiQiYang/geometry-axiom/blob/804afbb4c5fa38b6023087d6dcb150f40c5978e6/handoff/pr288-latest-review-20261022.md)。本次再次 `ls-remote` 原0，handoff head仍 `804afbb4…`；保存全文5838 bytes、SHA256 `ef18e0a9fbcffece2bf31dd0a667ebb70d87a48e75212ce363928fb01123e0bd`。GitHub API403，沒有宣稱讀過其後未提供的live留言；權威讀取的原命令、完整輸出與hash併入最終證據。

1. **最新阻擋1：同最終來源完整驗收已補齊。** 唯一目前矩陣為F2，正式17項、負控制／恢復與全部extra都保存原exit／log／環境／SHA／hash，沒有以audit-only或歷史產品結果外推。舊不可解析ledgerhead阻擋已由保存審查關閉，新P／L與F2 check仍分欄。
2. **須改2：本文更新為實際角色及結果。** 不再列96ade86、帳本進行中或架構待本機重跑。產品、ledger execution／artifact、架構execution／artifact、F2與E各自可追；本輪原紅與失敗嘗試保留歷史。
3. **正式workflow使用已鎖定的billing替代裁判。** run1020七job因付款／額度在0step失敗，不是產品結果。依決策B、2026-10-14計費決策與2026-10-22雲端試行，本次用同F2等同CI的七項雲端收據，原filter／時限／所有專項與數值gate不減；不宣稱GitHub Actions綠。

全程Codex雲端Linux，沒有使用使用者電腦執行。`google-chrome --version`＝Google Chrome156.0.8078.47、`node --version`＝v24.19.0，原命令皆0；Python3.12.14、cc14.2.0、fonts-noto-cjk已安裝。Chrome156六個browser job均真跑、各有獨立port／TEMP／profile，沒有browser列「本環境無法執行」。本輪指定suite中唯一Linux無法執行的是允許的Windows GDI 1 skip，未冒稱通過；另有舊Chromium154固定P73動態對照。

repo外subreaper處理PID1不回收孤兒程序的環境問題；Q38 wrapper只設soft stack16MiB、hard不降，原測試與斷言不動。ENOSPC只重跑受影響Cperf項，沒有為環境失敗重跑挑選正式樣本。

最不確定處仍明列：Cperf restored/main **1.9708接近2×**，只按原三樣本中位數、不重抽；P52對負載敏感，本輪正式／撤回／恢復結果不外推所有硬體；P73 controlled scope與舊版fixed子集不能證明舊自然時序或154原版曾綠。

未修改公理或鎖定決策，未合併或force push。後續 #323 → #314 → #299＋#316 combined依使用者指定順序另交分支，不混入本PR的F2驗收來源。
