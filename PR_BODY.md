# GEO-261：main 整合後的雲端驗收，P88 待修

一般 merge main 後的產品 F 已完成 native、其餘五 browser、P52、帳本及架構重驗；**canvas 的 P88 焦點逾時仍阻擋合併**。runtime 同 F 反證已取得 0／1／0；P73、Chromium154 與 oracle 反證仍待執行。下表是唯一 current-state 矩陣；沒有把歷史綠燈冒稱新執行。

- 受驗產品 F：`13d02c1db7022145a52ee063286a558e595eb212`。
- 本文證據快照 E：`1999cbc43e842c8bfe7db40e4494fca455722a38`；F→E 只新增 `evidence/geo261-final-13d02c1d/`。
- 繼承結果原執行 F2：`8f76f2b7d6f669670e5834310bfc26495b4a4aa6`；原證據 E2：`4b665fae21ab63aaffb7d84f6a32d5a469ba1675`。
- 帳本：F 上 `mutate.py --check` 原0；原件 SHA-256 `1b0adc12ed73c28075f56eb8bacf45fddffda6defae72809ee25109c1c5e4e2a`，fresh，未重產。
- 架構重產來源 S：`f79aa057521929597a9af4b204b709110414ac03`；保留真 `sourceBaseHead`，Linux 四檔安裝形成 F，三裁判另在 F 實跑0/0/0。
- 合入 main：`4ccced59315d0bcf01084ad89c760bb43d8b363b`；一般 merge `c1320a7ad41530252a6f335aaab372154a0e2bf2`。決策佇列只合入原文；公理層未改。

已讀最新 [handoff 審查全文](https://github.com/ZhiQiYang/geometry-axiom/blob/f6a174df42d5ff1ce670b6f8277da60c667b8965/handoff/pr-reviews/288.md)，同步 SHA `f6a174df42d5ff1ce670b6f8277da60c667b8965`；最新【ChatGPT 審查】為 2026-10-23T06:41:42Z、head `22ad28f`。該審查關閉 main 衝突、P52、帳本與架構阻擋，仍要求 P88、四組反證及本文更新。本檔推至 prbody 分支供套用；不宣稱 live PR 正文已更新。

| Gate | 實際執行 SHA | 原 exit／判決 | 允許 skip／範圍與限制 | 證據 |
| --- | --- | --- | --- | --- |
| 01 native | F | 0 | 224 suites；5184 pass／0 fail／1 原允許 Windows GDI skip；mutation check 0、replay 6/6；1684.13s ≤35min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/native.json) |
| 02 canvas | F | **原1；原樣重跑1／0；第3次執行中** | 原1502後fatal；第1次同predicate紅1071.91s；第2次完整2267/0、completed=true、golden matched，1754.83s≤35min。確認間歇紅，修正及新F連續驗證仍待 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/canvas.json) |
| 03 assembly | F | 0 | partial 150/0；完整 golden 未比較；184.69s ≤15min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/assembly.json) |
| 04 documents | F | 0 | 47/0；原 RESULT 沒有 completed/schema/scope 欄，不補造；63.94s ≤10min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/documents.json) |
| 05 grid | F | 0 | partial 356/0；完整 golden 未比較；442.97s ≤15min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/grid.json) |
| 06 space | F | 0 | full-space-suite 242/0、6 groups；原省略 timber-material、timber-source-guards；207.73s ≤15min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/space.json) |
| 07 timber | F | 0 | partial 79/0；含 timber-material/source-guards/font-layout，原省略 space-height-library/projection-lifecycle/projection-placement/space-flow/projection-close；128.00s ≤20min | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/timber.json) |
| 08 mutation-check-final | F | 0 | 帳本 fresh；只 check，未重產、未將歷史 M20 crashed 改稱 killed | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/post-main-prerequisites.json) |
| 09 P52 main 準備 | adbaebf9（main build）；驗收綁定F | 準備0、原 main build 0 | 原比較源 466 runtime inputs；不是 timing gate | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-formal.json) |
| 10 P52 | F | gate0／driver0 | main 252.7797935ms、fix 189.6910945ms，ratio 0.7504203238；4 blocks×8、每側16筆；五 controls 0/0/1/1/1 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-formal.json) |
| 11 P52 verifier | F | 原 verifier0／adapter0 | 原9 assertions未改；DERIVED launch projection明列，逐一核9個Node原exit/streams/hash/timeout | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-verifier.json) |
| 12 Q38 | F2，closure相同繼承 | 原0 | 42＝41 killed＋SPM24 equivalent；native/model baseline 0/0；非新 F 重跑 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/q38.json) |
| 13 §7 card-reference（兩 runner） | F2，closure相同繼承 | 原0 | 53 killed／53 restore0；axiom V01–V05 red1／restore0；不拆成新增正式項 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/card-reference.json) |
| 14 P-189 | F2，closure相同繼承 | 原0 | N16/32/48/64 ratios 0.967938/1.177801/1.699450/1.823251 ≤2；36 timing原0；175 dumps逐bytes相同（75接受＋100拒絕） | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/p189.json) |
| 15 architecture_contract.py | F | 0 | 三條原裁判各自執行；601 inputs／333 owned／796 edges／0 diagnostics | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/post-main-prerequisites.json) |
| 16 test_architecture_contract.py | F | 0 | 三條原裁判各自執行；601 inputs／333 owned／796 edges／0 diagnostics | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/post-main-prerequisites.json) |
| 17 test_product_architecture.py | F | 0 | 三條原裁判各自執行；601 inputs／333 owned／796 edges／0 diagnostics | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/post-main-prerequisites.json) |
| 額外 P73 controlled | F 尚未執行 | **未跑** | 待原 fixed/withdrawn/restored 0/1/0；受控callback不代替自然canvas | 尚無本輪終態收據 |
| 額外 P52 runtime | F | baseline0／withdrawn1／restored0；driver0 | 同原P52 protocol；ratio 0.750420/1.202992/0.815971；無 crash/timeout假紅；完整補包取 postmerge-runtime-complete-raw | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/postmerge-runtime-complete-raw.json) |
| 額外 reader | F2，closure相同繼承 | 原0/1/0 | 具名方法，不冒全51 reader tests | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-reader.json) |
| 額外 W checker | F2，closure相同繼承 | 原0/1/0 | 原三行撤回，具名 Regex AssertionError；不是重跑舊20 controls | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-checker.json) |
| 額外 parser-prepare | F2，closure相同繼承 | 原outer0／inner0 | compiled=false、testsRun=false；只準備14 inputs，不冒動態測試 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-prepare.json) |
| 額外 parser-O2 | F2，closure相同繼承 | compile0／run0 | 199810 comparisons、stderr空 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-o2.json) |
| 額外 parser-sanitized | F2，closure相同繼承 | compile0／run0 | ASan/UBSan 199810 comparisons、stderr空 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-sanitized.json) |
| 額外 Cperf | F2，closure相同繼承 | 首次1（ENOSPC）；retry0 | 原各組3筆；withdrawn/main2.564916＞2、restored/main1.970798≤2；保留原失敗，不重抽 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-Cperf-retry1.json) |
| 額外 Chromium154 P73 | F 尚未執行 | **未跑** | 固定版P73子集；不取代Chrome156正式job，不冒舊產品曾綠 | 尚無本輪終態收據 |
| oracle/probe 1 selftest --quick | F 尚未執行 | **未跑** | 保原golden，不write-expected | 尚無本輪終態收據 |
| oracle/probe 2 test_gen_scenes | F 尚未執行 | **未跑** | 原完整unittest；實際Ran/OK待原輸出 | 尚無本輪終態收據 |
| oracle/probe 3 C4 | F 尚未執行 | **未跑** | 待原0/1/0與具名C4NEG bad8/0/8；非歷史159 mutants重跑 | 尚無本輪終態收據 |
| oracle/probe 4 core_limits | F 尚未執行 | **未跑** | 待原具名方法0/1/0；撤回必須正常AssertionError，非setup/crash | 尚無本輪終態收據 |

P88 的精確 fatal predicate 是 `document.activeElement===document.querySelector("#refGuideMode")`。原 active 為 `refGuideRatio`；最後 click 命中 `label < div#refGuideSourceFields` 的「來源比例」，座標(293.75,627.5)。分類是 **UI 焦點／點擊定位紅燈，產品版面時序或測試定位根因待確證**；原輸出沒有 pointer-down target／rect／scroll，不補造這些資訊。固定 F、原 workflow、原35分鐘時限與golden的三次canvas獨占重跑已交專責代理，已完成兩次：第1次同predicate紅1，第2次完整canvas綠0（2267/0、golden matched、1754.826s），第3次仍執行中。相同F已確認間歇紅；一次綠不取代修復。兩份[原樣重跑收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/p88-original-canvas-run-1.json)與[第2次收據](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/receipts/p88-original-canvas-run-2.json)均已封存。原第1次launcher未把NODE_OPTIONS列入環境白名單，後驗shell未設定不倒填成啟動時已觀測；第2、3次明確env -u NODE_OPTIONS -u PYTHONOPTIMIZE。舊F2 canvas綠只作歷史。

closure 繼承依據是 F2→F 的 5108 repository inputs mode/blob 相同、110 原公開證據相同，另補 18461 fixture/evidence 的三方同一性；只支持表中明列九個繼承項，不產生新效能樣本。§7兩runner沿原正式清單合計一項。原17正式項與9額外phase的歷史紀錄留在[舊證據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/PROGRESS.md)，不是第二個current-state矩陣。

雲端環境：Linux 6.18.55、Google Chrome 156.0.8078.47、Node v24.19.0、fonts-noto-cjk；各job原版本命令、退出碼、環境及完整stdout/stderr在raw包內。使用者電腦未執行本輪；六browser實際都能跑，沒有標為通過的環境略過。原七項按序、同一乾淨F執行；新三次canvas每次獨立埠與TEMP，canvas獨占重工作資源。原native唯一Windows GDI skip保留，其餘partial/omitted按各job原scope明列。

保存的失敗：main原文空白檢查exit2、最初architecture1/0/5後重產修復、原canvas1、歷史Cperf ENOSPC1均未刪改。runtime封存首次staging遇Chrome socket失敗，`c3fec08f`第一包不完整；`postmerge-runtime-complete-raw`補包逐hash列冊1633檔，其中713檔bytes入tar、920可重建cache明列排除。272份原收據引用的命令輸出／logs全數入包，沒有被cache規則排除。原0/1/0結果與第一包均保留。

目前未結案：P88，以及P73、Chromium154、oracle三組未跑反證。最大不確定處是P88間歇紅的自然事件順序：原輸出不足以判定舊座標先點錯或產品後續搶焦點。診斷與修正未完成；P52/Cperf對負載敏感，繼承Cperf restored/main1.970798接近2×門檻且僅原三筆，沒有重抽或改門檻。

下一輪影響審查已找出原native內四組真RuntimeSnapshot消費路徑；若最後只改P88 driver，將於新F用原run_all partial重跑test_local_launcher17、test_modeling_transport3、test_serve51與node:tests-js737，另跑canvas、grid、帳本、架構三裁判及四組反證。這是待執行計畫，不修改上表原F13/F2的實際執行身分。

完整原命令、exit、環境、SHA、streams/hash以[PROGRESS與raw inventory](https://github.com/ZhiQiYang/geometry-axiom/blob/1999cbc43e842c8bfe7db40e4494fca455722a38/evidence/geo261-final-13d02c1d/PROGRESS.md)為準。一般push；未force push、未合併PR。
