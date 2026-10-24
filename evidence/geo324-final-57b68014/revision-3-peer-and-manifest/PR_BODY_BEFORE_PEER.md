柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑應回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免洩出未分類例外。這是 #324 的 Codex 替代線；產品已疊新列車，正式雲端驗收仍未執行。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 原 PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok 原 head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 已普通merge main | `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` |
| 已普通merge train | `504933473d7b9bdfc5964f73402a710f1222fc96` |
| 目前公開產品 S | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| 目前 evidence E | `792d086eb046263384888b3b0a064ae96f0cdc27` |
| 前批公開 evidence | `07615668c110684826390990cd2d6134eb6025fd` |
| Fresh審查handoff | `4aeabc8ec05b358e22fe2375f97dce64324fbc22` |
| 替代head／正文分支 | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |
| PR預定base | `codex/train-337-continue-20261024`（列車draft #338） |

對指定train，非evidence產品差異恰原三檔121+/2-。兩leaf保原Grok blobs；expected只聯集 `py:test_geometry_host_sources`39→45，其它registry metadata精確等train。SSOT／決策佇列blob精確等train，不改字。普通merge／push來源S／ls-remote及diffcheck均0，沒有rebase或force push，沒有合併PR。

目前45只是expected契約，非本輪實跑數。五支公開行為方法涵蓋柱／樑missing、null/object、非dict、int/list feature，並保三predicate controls。原作者Windows/Python3.14的45 tests exit0是歷史結果；Actions39721803849七job零步驟failure仍屬環境，兩者都不能代本輪S。

唯一 current-state 驗收矩陣如下。`null`表示沒有本輪原exit／execution SHA，不是允許skip；沒有新增skip豁免。正式final SHA尚待root排合流／架構刷新順序。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
| registry-list | 未執行 | `null` | `null` |
| native-and-full-expected | 未執行 | `null` | `null` |
| canvas | 未執行 | `null` | `null` |
| assembly | 未執行 | `null` | `null` |
| documents | 未執行 | `null` | `null` |
| grid | 未執行 | `null` | `null` |
| space | 未執行 | `null` | `null` |
| timber | 未執行 | `null` | `null` |
| affected-importers | 未執行 | `null` | `null` |
| predicate-list | 未執行 | `null` | `null` |
| predicate-dict | 未執行 | `null` | `null` |
| predicate-feature | 未執行 | `null` | `null` |
| mutation-check | 未執行 | `null` | `null` |
| architecture-contract | 未執行 | `null` | `null` |
| architecture-tests | 未執行 | `null` | `null` |
| product-architecture-tests | 未執行 | `null` | `null` |

三predicate補充driver v2 SHA `4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d` 只AST0。它先pin原c387 helper，從精確Git tracked blobs構建獨立四packages／三fixtures，逐案原method baseline／withdraw／restored各封完整streams及正常0/1/0。mutant另核原helper具名unclassified診斷，不能用setup/import/syntax/error或timeout冒正常紅。原test/assertions/60秒不改。原內建helper最後只跑第一個restored，不捏造其餘兩案輸出；feature=int會被後段集合擋住，同method的list feature才有牙齒。

p88_priority只對先前S f1217b0f／當時普通merge原件／v2完成純靜審118 checks、0 findings，完整原checker錯判1與窄更正報告保留；不把它外推本次S。新merge的獨立靜審待補，正式動態仍未執行。原frozen準備不覆寫，只追加current計畫的v2精確檔名。產品／正式裁判／Chrome都尚未執行。

原件位於 `evidence/geo324-final-57b68014/`（本輪一般push及ls-remote已核同）：本次merge原命令、完整stdout/stderr/env/SHA與前批publication原流；先前fresh review／v1/v2／manifest／peer保於原evidence/geo324-final-f1217b0f/。Git認證18:25Z曾lookup失敗，原本地commit／故障狀態皆保留。18:55Z root探針恢復後，原Ede5142a0／D2fc63aef兩ref均一般push0、ls-remote核同；本輪新E也已一般push0核同。10條恢復原命令與完整streams封於原evidence/geo324-final-f1217b0f/revision-2-network；正式16gate仍未跑。正文由同名-prbody分支一般推送，實際D與原exit另記於出版收據。

下一步：root統一推handoff替代draft PR request；排正式同SHA native＋expected／六browser／importers／三predicate0/1/0／mutation check與架構三原裁判／四檔刷新。帳本過期如實交root統排，不在準備階段重產全ledger。後續動態依root時槽執行，本owner不搶槽。不宣稱可合併。

本次另普通merge root已公開50493347完整列車，原架構四檔保 incoming train 的 sourceBaseHead；#324 owned W leaf／excluded test 的原裁判與四檔刷新仍未跑。mutation bridge oracle hash 包含 tests/*.py，因此不能把列車既有帳本或架構收據直接當作本S有效。
