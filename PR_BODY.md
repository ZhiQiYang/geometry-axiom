本 PR 接替 #337，整合 #299+#316、#314 題3比較器、已核可的 #318 閱讀 A、#323、K source/edge索引修正、#339/#340及#343（含#341/#342）。本輪修正 `reference_rebuild` 在持續快取路徑上仍清零未使用區域結構的額外成本；fallback、配置失敗與有序圖語意保持原契約。容量仍64，未合#344/#345/#346/#347/#348。**維持 draft，目前不可合併。**

| 身分 | 完整 SHA |
|---|---|
| 固定產品／測試／架構產物 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad` |
| 證據 head E | `219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6`；非 evidence tree 與 F8 相同 |
| 架構真正執行 M | `6e50aef65513b7b38f93228919272c6d40d6c196`；F8採用其report／receipt |
| H 定向執行 S | `2c4635577a8fcb11e88b346547f7bb1c7b739fb7` |

以下是唯一 current-state 矩陣。UNRUN／UNREAD 不代表通過；原門檻、golden、斷言與時限不變，歷史來源結果不移標 F8。

| Gate | 結果與實際來源 | 尚待完成 |
|---|---|---|
| 全123突變帳本／tracked check | F8 tracked check真exit1，120stale／3retired／0invalid；全量重產UNRUN，正配置獨立cache與seed | 穩定來源整份重產，由root採用；不重寫帳本內真正execution SHA |
| 完整native | UNRUN at F8 | 原aggregate、16MiB stack、strict registry |
| canvas | UNRUN at F8 | 完整golden、P73/P88，獨占執行 |
| assembly、documents、grid、space、timber | 各UNRUN at F8 | 原workflow，各獨立埠／TMP |
| P52 | UNRUN at F8 | 原fix median≤main |
| Q38 | UNRUN at F8 | 全44案例，既定排除不擴張 |
| §7 card-reference／axiom | 兩項UNRUN at F8 | 完整原突變 |
| P-189 full exact／timing | 兩項UNRUN at F8 | 歷史full紅仍在，timing不能代exact |
| #323 R8 prepare/build/compare/perf/profile | F8原終態outer1；execution0/0/1/0/0、CLI0/0/1/1/1。N16/base0.9834192453688345、N32/base0.9007932884873169、N48/base0.7392862448969592均≤1；N64/main1.2846970752586067≤1.3；calls64/32=4.407618425509266≤4.5，全量化門檻綠。exact仍三差；ABC_result缺席、full_acceptance=null | 五stage不等於完整八stage；全部36樣本保留 |
| #323 required-eight／PF3／native後段 | UNRUN at F8 | 原入口與原時限 |
| #323 whole-memo／恢復／隔離ABC | UNRUN at F8 | 同列車反證不能代跨版本exact |
| reader三條／RC builder、checker反證 | UNRUN at F8 | 原SSOT流程與兩刀 |
| #314六suite／Node inspector | UNRUN at F8 | 已核可有序比較器 |
| 閱讀A native／oracle／mutants-only／完整quick | UNRUN at F8 | #335未核可CLI初放能力另案 |
| 架構三原judge＋四檔 | M exit0/0/0，205＋18、零skip；F8已採用 | 604inputs唯一references.inc變動；937／55政策與scan不變；九guard各0/1/0、neutral2綠。最終驗收的三gate另跑 |
| H局部修正與反證 | S 原14/14、exit0、零skip；舊13方法不變；三phase work exit0/1/0 | O0 focused，不代O2 wall；Windows未驗 |
| required CI | F8 run40170221039／E815cd2e3 run40170692505，各七job failure、runner_id0／steps0，原18 API讀0。當前E219bf5d4尚未讀CI，不移標較早run | 歷史annotation為付款失敗或支出上限，未修改帳戶；沒有正式替代接受紀錄 |

允許skip只限原Linux `py:test_gdi_contract` 缺compiled Windows GDI harness；F8尚未跑native，不預先計入skip。未刪測試或放寬數值門檻。

H的撤回反證精確失敗為 `ASSERT:persistent-reference-local-zero-work line=166 expr=local_zero_calls==0&&local_zero_bytes==0`；fixed／withdrawn／restored清零calls=0/2/0、bytes=0/255168/0。三phase的persistent、fallback、allocation-failure與ordered-graph語意皆exit0，fallback校準各實際攔截一次127584-byte清零。原ELF為hash-only，未宣稱保留payload。

跨版本exact仍依原 `verify_linux.py:156 assert not failures,failures` 判定，不正規化輸出。歷史三差為role_priority與P8低／高凹角；P-189歷史 `p189_verify.py:195 assert raw['base'] == raw['fix']` 亦首差於role-priority。引入提交為 `6366304eb787b2a50282e4132f45e51eb7d21290`；固定b74與F8的I22整條逐byte相同，舊base原訊息缺少它自己要求的定位邊／超出區間。現行I22必要定位診斷與固定舊base有版本差異；Q-323-ABC／Q-P189-EXACT已記QUESTIONS，尚無comparator／版本界線裁決。不刪必要診斷，不將待決項改成通過。

公開證據：

- `evidence/geo337-train-20261024/architecture-6e50-complete/`：380原件、4,630,676 bytes，三judge、九組反證、合流原流與獨審；實跑M與採用F8分列。
- `evidence/geo323-reference-local-init-2c463557/`：完整H原件2546members，tar SHA256 `7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388`；原14項與撤回／恢復全流、封包與獨審。
- `evidence/geo337-train-20261024/full-R8-five-stage-raw/`：9057members／31,362,296B，SHA256 `4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0`；完整原36樣本／四profiles／350比較原流與inventory在包內，七ELF保hash且原payload仍保留。小終態、CI、F8 check及五CLI／outer在 `current-R8-terminal/`。
- R5／R6／R7完整原件已公開，保留各自原SHA、原outer1與歷史紅；R7全包9128members，SHA256 `8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e`。R7的N64/main1.229223、N16/base1.051906僅為F7歷史，不移標F8。

其他工作線：#344新來源cbb318d的strict aggregate9已通過並公開於E a5ec136b／正文b169e27e，完整canvas三phase仍未跑；#348兩個512四指令批次的原600秒逾時仍紅。兩線均未合入本列車。

最新已讀審查為2026-10-24T06:38:46Z、head597bce6，來自handoff分支原文。B1完整最終驗收尚未完成；B2依R8原結果逐項記錄；B3未解除。本正文更新唯一current-state，不宣稱READY-TO-MERGE。

三差的[逐項原輸出與Git歸因](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/REPORT.md)及[具體選項](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/QUESTIONS.md)已公開並通過424/0獨審。維持A保紅；B′僅補診斷的比較基準或C具名三pair政策均需明確裁決，尚未採用。B′會改exact基準版本，C會改允許差異政策；任何方案皆不改性能分母或重抽有效R8。P-189適用範圍另需明示。

native ROOT已普通detach至F8，五fixture／sparse／原refs完整保留並經actual獨審；完整轉移原流在雲端保全待另行公開。全帳本仍未啟動，不把資源／來源準備冒正式測試。
