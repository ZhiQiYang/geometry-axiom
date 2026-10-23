柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。這是 #324 的 Codex 替代線；已普通合入完整列車，三predicate補證已實跑，完整整合仍待驗收。

| 來源角色 | 完整SHA／分支 |
|---|---|
| 原PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok原head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 已普通merge train | `504933473d7b9bdfc5964f73402a710f1222fc96` |
| 公開產品S／本次execution SHA | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| 目前evidence E | `602b393298b7217347532c7f8b0faba118e02e45` |
| 替代head／正文分支 | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |
| PR預定base | `codex/train-337-continue-20261024`（列車draft #338） |

對指定train，非evidence差恰原三檔121+/2-；兩leaf等Grok原blobs，expected只host_sources39→45，其餘metadata精確等train；SSOT／決策blob原字等train。合流純靜審254 checks／0 findings，不代正式執行。沒有rebase、force push或合併PR。

唯一current-state矩陣：三predicate原命令序列是baseline／withdraw／restored；`null`是未跑，不是skip。45只是expected契約，本輪未跑完整45。

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
| predicate-list | 通過（原0/1/0） | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-dict | 通過（原0/1/0） | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| predicate-feature | 通過（原0/1/0） | `0/1/0` | `57b680140da2c6b77ab0d362a72029d8d7c9334b` |
| mutation-check | 未執行 | `null` | `null` |
| architecture-contract | 未執行 | `null` | `null` |
| architecture-tests | 未執行 | `null` | `null` |
| product-architecture-tests | 未執行 | `null` | `null` |

原v2 driver SHA `4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d` 未改。獨立薄checkout先逐Git原blob／工作bytes核37inputs，只複製精確tracked四packages／三fixtures；原三公開Python method各真0/1/0，撤回每組有column／beam兩個正常AssertionError及精確null／nested-list／feature-list TypeError／AttributeError診斷，無ERROR、import、crash、skip或timeout。每phase原60秒保留，來源前後clean、三份產品bytes還原。原helper mock native transport，這批不是native或browser驗收。

52內命令＋10外setup命令的argv／exit／環境／SHA／完整stdout/stderr、37inputs、三份還原樹與凍結工具全封於 `evidence/geo324-final-57b68014/raw/three-predicate-originals-57b68014.tar.gz`，逐member inventory無排除且producer roundtrip逐bytes同。原receipt SHA `58bf107cbe1207cf695c81b11001881e233075c4782dd6673ed08e4d878b85fb`；獨立actual peer551 checks／報告0且原helper process0，SHA `075f987fdc99fbedb52f9e9719946839886fe80ab6a5c9c8facb332c580e8e01`，同封revision-5。

先前metadata修正／原件完整保留：原出版collector1是對原patch whitespace跑check所得2，raw未改；manifest自索引排除自身；E495 generated PROGRESS合法追加6行，舊true只指寫新metadata前對E792 snapshot的驗證時點。原package peer1019有1finding（report exit_code1，helper實際process0），精確澄清另封，不把原報告回寫成綠。這些不是產品裁判結果。

架構原四檔屬incoming train的sourceBaseHead，#324 owned W leaf／excluded test需原三裁判與四檔刷新，尚未跑；mutation bridge oracle hash讀tests/*.py，不能把列車帳本直接當本S有效，完整帳本由root統排。其餘13列依root時槽繼續，下一步先完整45／affected importer，再同SHA full native＋expected、六browser、mutation check及架構。沒有新增skip或放寬斷言，不宣稱可合併。
