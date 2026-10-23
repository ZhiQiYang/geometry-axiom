# GEO-261：P88 點擊定位修正與新 SHA 驗收

P88 測試現在等版面穩定並核對點擊位置上的目標後才送出點擊；原焦點斷言、golden與時限保留。修正已提交，**新 F 的帳本及三條架構裁判通過，三次完整 canvas 正在執行；其餘受影響項與反證尚未結案，目前不宣告可合併。** 下表是唯一 current-state 矩陣；歷史結果各自保留實際執行 SHA。

- 受驗產品 F：`3d681636902371ecc528b20f51eea33e272581c9`；只讀證據快照 E：`6c5c7e599963cbb472a173a7e8766192cadca26e`。F→E僅新增`evidence/geo261-final-3d681636/`。
- P88來源提交：`8bce9239c014f070740455556c8ee1176c500af3`；一般merge後真架構重產來源 S：`4b588fb63c9cc8fe5ba7570618f353c0d00d3816`，四檔安裝形成F。
- 帳本SHA-256：`1b0adc12ed73c28075f56eb8bacf45fddffda6defae72809ee25109c1c5e4e2a`；F原`mutate.py --check`=0／fresh，未重產。
- 原完整輪 F13：`13d02c1db7022145a52ee063286a558e595eb212`，其證據E13：`66dd2437153cf95482ebc9ba1fe839c47cfea0d9`；更早繼承項 F2：`8f76f2b7d6f669670e5834310bfc26495b4a4aa6`，E2：`4b665fae21ab63aaffb7d84f6a32d5a469ba1675`。
- 已一般merge main `4ccced59315d0bcf01084ad89c760bb43d8b363b`（merge `c1320a7ad41530252a6f335aaab372154a0e2bf2`）。本次P88修正沒有改公理層、決策佇列或產品app.js。

已重新fetch並讀[handoff最新審查全文](https://github.com/ZhiQiYang/geometry-axiom/blob/7bd61a43210bbad0abf95709e1a0205cd8760cac/handoff/pr-reviews/288.md)：同步SHA `7bd61a43210bbad0abf95709e1a0205cd8760cac`，最新審查2026-10-23T10:40:30Z／head `1999cbc`。它要求P88新F確定性驗證與撤回／恢復反證，以及同F的P73、Chromium154、oracle。此前runtime反證在F13已關閉；因本次改動影響RuntimeSnapshot輸入，仍安排F重驗。本檔推prbody分支供套用，沒有宣稱live PR正文已更新。

| Gate | 實際執行SHA／exit | 允許skip、範圍與限制 | 證據 |
| --- | --- | --- | --- |
| 01 native | F13 完整0；F 四組 partial **待跑** | 224 suites、5184 pass／0 fail／1 原允許 Windows GDI skip，1684.13s≤35min；原 replay 6/6。新F將用原runner重跑4組真RuntimeSnapshot消費路徑，不能宣稱完整native在F重跑。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/native.json) |
| 02 canvas | F **三次執行中**；F13 原三次1/0/0 | F原35min、完整golden、斷言不變；三次所有結果保留。F13後兩次2267/0且golden matched不等於修正後F已過。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| 03 assembly | F13 原0，受影響範圍分析後沿用 | partial150/0，完整golden未比較，184.69s≤15min；不執行變動的P88模組。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/assembly.json) |
| 04 documents | F13 原0，受影響範圍分析後沿用 | 47/0，原RESULT沒有completed/schema/scope欄；63.94s≤10min；不補造欄位。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/documents.json) |
| 05 grid | F **待跑**；F13 原0 | 直接執行P88變動模組，須F重跑。歷史partial356/0、golden未比較，442.97s≤15min，不拿來充新F綠。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/grid.json) |
| 06 space | F13 原0，受影響範圍分析後沿用 | full-space-suite242/0、6groups；原省略timber-material/source-guards，207.73s≤15min。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/space.json) |
| 07 timber | F13 原0，受影響範圍分析後沿用 | partial79/0，含material/source-guards/font-layout；原省略height-library/projection-lifecycle/placement/flow/close，128s≤20min。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/timber.json) |
| 08 mutation-check-final | F 原0 | 78筆仍fresh；帳本未過期所以未重產；M20歷史crashed不改稱killed。 | [新F收據／raw索引](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/receipts/p88-final-prerequisites.json) |
| 09 P52 main準備 | adbaebf9 原build0；F綁定待跑 | 沿用固定比較源adbaebf9c73ea6801d7b4d5214e4b846b132923b；準備不是timing gate。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-formal.json) |
| 10 P52 | F **待跑**；F13 gate0／driver0 | F13 main252.7797935ms、fix189.6910945ms、ratio0.7504203238；新F仍依原4blocks×8／每側16筆與fix≤main，五controls0/0/1/1/1。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-formal.json) |
| 11 P52 verifier | F **待跑**；F13 verifier0／adapter0 | 原9assertions；新F正式P52輸出才能作新F驗證。保留DERIVED launch projection身分。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/postmerge-p52-verifier.json) |
| 12 Q38 | F2 原0，判定closure沿用 | 42＝41killed＋SPM24 equivalent；native/model baseline0/0；不是F新執行。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/q38.json) |
| 13 §7 card-reference兩runner | F2 原0，判定closure沿用 | 53killed／53restore0；axiom V01–V05 red1／restore0；沿原正式清單合計一項。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/card-reference.json) |
| 14 P-189 | F2 原0，判定closure沿用 | N16/32/48/64 ratios0.967938/1.177801/1.699450/1.823251≤2；36timing原0；175dumps逐bytes相同（75接受＋100拒絕）。新F無新增樣本，整份source archive並非bytes相同。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/p189.json) |
| 15 architecture_contract.py | F 原0 | Linux四檔重產後F實跑；601inputs／333owned／268excluded／796edges／0diagnostics。 | [新F收據／raw索引](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/receipts/p88-final-prerequisites.json) |
| 16 test_architecture_contract.py | F 原0 | 原205tests，沒有改裁判或計數門檻。 | [新F收據／raw索引](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/receipts/p88-final-prerequisites.json) |
| 17 test_product_architecture.py | F 原0 | 原18tests；獨立peer核對原streams／hash及真sourceBaseHead。 | [新F收據／raw索引](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/receipts/p88-final-prerequisites.json) |
| 新F native四組partial | F **待跑** | 原run_all --build加四個--only：test_local_launcher、test_modeling_transport、test_serve、node:tests-js；原17/3/51/737，不能冒完整native。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| P88撤回／恢復反證 | F **待跑**；F13基底、記憶體v5/original/v5的query診斷1/1/1、driver2 | 舊診斷沒有產生要求的錯位，屬工具前提不成立，無效反證；不列為原焦點assertion紅。依真renderer／原scroll-restore rAF trace準備新定序實驗，禁止人工scroll或改response。 | [新F收據／raw索引](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/receipts/p88-final-prerequisites.json) |
| 額外P73 controlled | F **待跑** | 原fixed/withdrawn/restored；受控callback不取代自然canvas。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| 額外P52 runtime | F **待跑**；F13 0/1/0、driver0 | F13 ratio0.750420/1.202992/0.815971，非crash/timeout假紅；新F須重做原protocol，保五freshness控制。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/receipts/postmerge-runtime-complete-raw.json) |
| 額外reader | F2 原0/1/0，判定closure沿用 | 具名方法反證，不冒全51reader tests。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-reader.json) |
| 額外W checker | F2 原0/1/0，判定closure沿用 | 原三行撤回、具名Regex AssertionError；不是重跑舊20controls。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-checker.json) |
| 額外parser-prepare | F2 outer0／inner0，判定closure沿用 | compiled=false、testsRun=false，只準備14inputs，不冒動態通過。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-prepare.json) |
| 額外parser-O2 | F2 compile0／run0，判定closure沿用 | 199810comparisons、stderr空。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-o2.json) |
| 額外parser-sanitized | F2 compile0／run0，判定closure沿用 | ASan/UBSan199810comparisons、stderr空。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-parser-sanitized.json) |
| 額外Cperf | F2 首次1（ENOSPC）／retry0，判定closure沿用 | 原各組3筆；withdrawn/main2.564916＞2，restored/main1.970798≤2；不刪首次失敗、不重抽。 | [原收據](https://github.com/ZhiQiYang/geometry-axiom/blob/4b665fae21ab63aaffb7d84f6a32d5a469ba1675/evidence/geo261-final-8f76f2b7/receipts/F2-Cperf-retry1.json) |
| 額外Chromium154 P73 | F **待跑** | 固定版本69項P73子集；須proof_expectation_matches=true；不取代Chrome156正式job，不冒舊產品曾綠。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| oracle/probe 1 selftest --quick | F **待跑** | 保原golden，不write-expected。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| oracle/probe 2 test_gen_scenes | F **待跑** | 原完整unittest，實際Ran/OK待原輸出。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| oracle/probe 3 C4 | F **待跑** | 原0/1/0及具名C4NEG bad8/0/8；不是歷史159mutants重跑。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |
| oracle/probe 4 core_limits | F **待跑** | 原具名方法0/1/0；撤回須正常AssertionError，非setup/crash。 | [新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md) |

P88 原失敗predicate是`document.activeElement===document.querySelector("#refGuideMode")`（原`grid_rule_lines_test.js:27`，390px呼叫點原121行）。實際active是`refGuideRatio`，最後click落在來源比例label/div，座標(293.75,627.5)。F13獨占三次原樣重跑**1／0／0**，確認間歇紅；後兩次完整2267/0、golden matched，1754.826s／1739.477s，均在原35min內。三份原streams與分類已封存於[歷史F13進度](https://github.com/ZhiQiYang/geometry-axiom/blob/66dd2437153cf95482ebc9ba1fe839c47cfea0d9/evidence/geo261-final-13d02c1d/PROGRESS.md)。原第一輪沒有將NODE_OPTIONS列入環境白名單，不把後驗shell狀態倒填成啟動觀測；後兩輪及新F三輪明確env -u NODE_OPTIONS -u PYTHONOPTIMIZE。

本次採用的修復假說是**測試量測座標與真正點擊之間的版面時序競態**；自然紅燈的精確因果尚未證實。真query診斷觀察到renderer換掉節點、父容器scroll 25→0→25，原rAF恢復scroll；但那次實驗沒有重現原錯點，fixed/withdrawn/restored都在工具前提檢查失敗（1/1/1，driver2），不能拿來證明自然失敗必然是這個事件順序。該實驗完整raw與原錯誤摘要都保留，v2只更正parsed_json_unchanged欄位，不宣稱wire bytes相同。新反證將只控制真量測相對原scroll-restore rAF callback的順序，保原callback與原焦點裁判，尚未執行。

修正僅在`grid_rule_lines_test.js`局部點擊工具加入穩定／命中檢查；共用`cdp_helpers`、原check行、原key後續流程與12次嘗試保留，準備與焦點判定共用原25秒上限，沒有增加時間預算。canvas與grid會執行該檔，必須F重跑。這個檔也是RuntimeSnapshot輸入，所以四組native partial及P52／runtime反證重驗；assembly/documents/space/timber不執行它，保留F13原結果並明列這項版本指紋變化，沒有說整份runtime identity相同。

F13→F的非封存差異是P88單檔＋三個架構衍生檔。Linux manifest/scan/report/receipt四檔均重產，scan bytes恰好相同，只有manifest/report/receipt進Git差異。原metadata collector誤以為四檔都必須改動而exit1，已保留；修正版要求精確三個derived差異，另硬性核scan mode/blob相同，identity exit0，未修改產品裁判。三條原架構裁判另在F實跑0/0/0，205／18原tests，獨立peer核對來源與原streams。

表中九個F2繼承項依原5108輸入／110公開證據的閉包紀錄，加本次實際Git差異與18461fixture/evidence三方同一性判定。P-189工具的整份source archive包含變更JS，故**不主張整份archive bytes相同**；其C判定／夾具不執行該JS，原36timings與175dumps仍是F2執行，不產生新F效能樣本。詳細input-delta及peer在[新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md)的prerequisites與independent-reviews封包。

雲端環境是Linux6.18.55、Google Chrome156.0.8078.47、Nodev24.19.0、fonts-noto-cjk；原版本命令、環境、SHA、exit及完整stdout/stderr均隨raw保存。六個browser均可在雲端跑，沒有把安裝失敗略過當通過，也沒有使用使用者電腦。新F獨立乾淨checkout沿用原稀疏規則（不實體展開evidence與tests/evidence），Git來源完整且HEAD/tree/index核對保留；三輪各自獨立埠／TEMP／Chrome profile，canvas期間其他重測試暫停。

保留的歷史失敗包含main原文空白檢查2、架構舊收據1/0/5、原canvas1、Cperf ENOSPC1、runtime首次封存socket錯誤與P88無效query反證。runtime完整補包有1633列冊檔（713實際入包、920可重建cache排除），272份原命令streams/log引用全覆蓋；第一不完整包沒有刪掉。原始資料可由[新F進度與封包](https://github.com/ZhiQiYang/geometry-axiom/blob/6c5c7e599963cbb472a173a7e8766192cadca26e/evidence/geo261-final-3d681636/PROGRESS.md)及其raw inventory追溯。

尚未結案項目已在唯一矩陣逐項標示。最大不確定處仍是P88自然間歇紅的精確事件順序與修復有效性，需新F連續canvas及有效反證共同回答；Cperf繼承值1.970798接近2×且僅原三筆，保留此限制，不另抽樣或改門檻。全部普通push；不force push、不合併PR。
