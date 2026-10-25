本 PR 接替 #337，整合 #299+#316、#314 題3、#318 閱讀 A、#323、K 索引及 #339/#340/#343（含 #341/#342）。容量仍64，未合 #344–#348。**維持 draft；native 尚紅，完整驗收未完成。**

以下是唯一 current-state 矩陣；原門檻、golden、時限不變，歷史結果不移標。

| 身分 | 完整 SHA |
|---|---|
| 最終來源 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| 帳本生成／R8／成本執行 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad`；F8→F9僅帳本／evidence |
| 證據 E | `59064fe0478f7ebe9126e6fe042c2054f336a42f` |
| 架構四檔原執行 M／H 定向執行 S | M=`6e50aef65513b7b38f93228919272c6d40d6c196`；S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7` |

| Gate | 實際結果／未完成項 |
|---|---|
| 全123帳本／tracked check | F8完整重產0：114 killed／5 equivalent／M20 crashed／3 retired。逐byte採入F9，tracked check0、stale0／blocked0 |
| 完整 native | F9 exit1；35分鐘裁判0（1846.506872秒）。230登記列；5327 pass／1 fail／1 skip。唯一紅為下述 #314 assertion |
| canvas、assembly、documents、grid、space、timber | 六項各 UNRUN at F9；canvas含P73/P88、獨占原workflow |
| P52／Q38／§7兩項 | 各 UNRUN at F9；保留P52原median門檻、Q38全44及兩套完整突變 |
| P-189 full exact／timing | 兩項 UNRUN at F9；歷史exact紅保留，三差裁決未明示延伸本項 |
| #323 R8五stage | F8原outer1；execution=0/0/1/0/0、CLI=0/0/1/1/1。量化門檻綠但exact三差仍1；ABC_result缺席、full_acceptance=null |
| #323 required-eight／PF3／native後段 | 各 UNRUN at F9；R8五stage不能代完整八stage |
| #323 whole-memo／恢復／隔離ABC | 各 UNRUN at F8（原R8正式來源） |
| reader三條／RC builder、checker反證／#314六suite及Node inspector／閱讀A native、oracle、mutants-only、完整quick | 各獨立專項 UNRUN at F9；native總表不代完整專項 |
| 架構三原judge／四檔 | F9 exit0/0/0、205＋18全ok；334 sources／6 trusted／798 edges／0 diagnostics。四檔為M原收據經F8採用，F9逐blob相同 |
| #341四類成本 | F8 fallback-only exit0；14 cases全樣本。N64 none wall +6.77%、dense −29.72%；未判性能接受，未解除完整優化撤回B1；新F9完整撤回尚未實跑 |
| H局部修正／反證 | S：14/14 exit0、零skip；work反證0/1/0，清零calls=0/2/0、bytes=0/255168/0。O0定向不代O2性能 |
| required CI／替代驗收 | 審查記cd19的run40183211769七job failure、steps0；新E的Actions未讀。repository記錄有替代裁決，原始批准身分待核實，未採用；目前native1、六browser未跑，正式接受狀態不變 |

native精確失敗：`test_geo314_commit_paths.Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，assertion `I24 submission policy must not change K files`，原額外stdout為 `geometry-core/kernel/source.c`。先核基底／來源再修，未免除斷言。唯一允許skip是Linux缺compiled Windows GDI harness的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`，實際1項。native原件獨審2208/0、包6191/0只證收件正確，不改正式exit1。

R8原36樣本不重抽：N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`（各≤1）；N64/main=`1.2846970752586067`（≤1.3）；source calls64/32=`4.407618425509266`（≤4.5）。原outer1與350比較原流保留。

2026-10-25的repository裁決記錄位於main [`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`](https://github.com/ZhiQiYang/geometry-axiom/blob/405f8c5e1a637a16cbe47470faf5ae1fa02b8676/決策佇列.md#L841)；main記錄四個選項為使用者原文，但題意／適用範圍及背景明示由Claude整理；handoff對適用解釋也標「本機 Claude 整理，非原話」。本任務尚未核實原始選答身分，這份紀錄不是本任務直接批准；目前無API核實留言是否由真使用者帳戶發出。Q-323-ABC記錄的範圍僅為 `_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene` 各自指定的新增定位邊文字。**精確白名單／CI替代：repository記錄有裁決，原始批准身分待核實；未採用，正式裁判與接受狀態不變。**白名單尚未實作／重驗；其餘bytes、返回碼、有序來源圖、五guards仍須相同，第四差或文字不同仍紅。不得正規化或刪I22診斷；性能門檻不變；P-189適用範圍仍未核可。記錄另述CI替代延伸所有PR、帳本僅stale可後補；兩者均不在本稿採用，也不援用來解除阻擋。本任務直接選答B′尚未收到。

最新已讀[審查原文](https://github.com/ZhiQiYang/geometry-axiom/blob/e34e6d784ad9b0ffd2a68be7db92584f953594b0/handoff/pr-reviews/338.md#L151)：2026-10-25T10:40:50Z、head cd19c63。B1的native已終態1，其餘未跑項保留；B2／B3僅有repository轉述記錄，原始批准身分待核實，未採用；不標READY-TO-MERGE。

原件索引：[F9 native完整原流與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/F9-native-terminal/)（1374 members、13,895,527原bytes，gzip SHA256 `42217b1827d010e8eac017b95799a24910835c202aa1e32a0137cfee32e95d5c`）；[F9帳本採用／架構／F8成本](https://github.com/ZhiQiYang/geometry-axiom/tree/782bc80b0a13ecd19670f5285a8edb1824349686/evidence/geo337-train-20261024/F9-initial-gates/)；[R8完整五stage](https://github.com/ZhiQiYang/geometry-axiom/tree/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/full-R8-five-stage-raw/)與[全部歷史進度／證據連結](https://github.com/ZhiQiYang/geometry-axiom/blob/59064fe0478f7ebe9126e6fe042c2054f336a42f/evidence/geo337-train-20261024/PROGRESS.md)。
