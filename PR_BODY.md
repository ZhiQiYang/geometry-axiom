本 PR 接替 #337，整合 #299+#316、#314 題3比較器、已核可的 #318 閱讀 A、#323、K edge probe、#339/#340、#343（含 #341/#342 祖先），以及 contact faces 線性排序檢查與平面群範圍快取。容量仍為64，沒有合入 #344/#345/#346/#347/#348 的獨立變更。**目前 NOT READY-TO-MERGE。**

| 身分 | 固定 SHA |
|---|---|
| 當前產品／測試與架構產物 F | `2bbe54f19b2d19e8a816530f0c4edca950629a34` |
| 證據 head E | `3df56ff38b450ad228da04b2c1dcb6511582af42`；純證據提交不改 F |
| 架構真正執行／產品合流 M | `8d2a69421560b83c0b69f3e82db8f5e97ccc037b`；F 只採用 M 的衍生 report／receipt |
| 平面群快取定向實跑 W | `df66452e7a514032453bea93b8b18ab74d7b1457`；五個產品／測試葉已普通 merge 至 M |
| 前輪 R5 執行 R | `a22df116c7e9f6b7d074451f1c8052d59e7e4f3e`；以下歷史欄保原判，不能移標 F |

以下是唯一 current-state 矩陣。`UNRUN`／`UNREAD` 不是通過；peer 核對數不是產品測試數。R6 沿用 v5 PIPE／延期序列化，原六件工具、175 scenes、36個交錯樣本、四個 profile 點、分母、門檻及時限都沒有改。

| Gate | 當前 F／實際執行來源與判定 | 歷史結果及界線 |
|---|---|---|
| 全123突變帳本 | F 的 `python3 tests/mutate.py --check` 真 **1**：120 stale／3 retired／0 invalid；全量重產 **UNRUN** | 前後 HEAD=F且clean；外層完成0不等於check0。只由主代理在最終來源整份重產 |
| 完整 native | **UNRUN at F** | 不沿用 L 的完整 native 綠 |
| canvas | **UNRUN at F** | 原完整 canvas、golden及P73/P88；正式時獨占 |
| assembly／documents／grid／space／timber | **五項各 UNRUN at F** | 各自使用原 workflow、獨立埠與暫存目錄 |
| P52 | **UNRUN at F** | 原 fix median ≤ main，沒有+5寬限；原控制亦待跑 |
| Q38 | **UNRUN at F** | 含#342後為44案例，不能借L的42案例 |
| §7 card-reference／axiom | **兩項 UNRUN at F** | 完整原突變表及恢復反證待跑 |
| P-189 full exact／獨立 timing | **兩項 UNRUN at F** | 歷史full1未解除；timing綠不能代完整loadfile+dump bytes比較 |
| #323 R6 prepare／build／compare／perf／profile | **F 真終態outer1**；stage=0/0/1/0/0、累積CLI=0/0/1/1/1。**N16/base=1.0434575834374764>1、N64/main=1.3731562025736295>1.3，兩點紅**；同三個stdout exact差 | R6原36樣本全保，N32/base=.8823227658668896、N48/base=.7581122695004152與sourcecalls比4.407618425509266綠。R5是另一輪歷史，不能混樣本或挑綠重抽 |
| #323 fixed-three／required-eight／PF3／native後段 | **UNRUN at F** | 五階段不等於完整八階段；compare斷言後未到的audit不可計通過 |
| #323 whole-memo／恢復／隔離ABC | **UNRUN at F** | L的1/0/0完整證據僅歷史；R5 `ABC_result` key缺席、all-required=false、full-acceptance=null保原 |
| reader三條／RC-run builder、checker反證 | **UNRUN at F** | 原SSOT流程及兩刀待跑 |
| #314六suite／Node inspector | **UNRUN at F** | 原比較器與🔒決定不變 |
| 閱讀A native／oracle／mutants-only／完整quick | **UNRUN at F** | t4族六筆C11_MAIN_NOT_BUTTED另案保留；不宣稱#335未核可CLI初放能力已解決 |
| 架構三原裁判＋四檔 | **實跑M：0/0/0；F已公開採用四檔** | generic205／product18、零skip；604 inputs、334 owned、270 excluded、798 edges、0 diagnostics。manifest937→937與55 strings、scan bytes不變；既有九guard各0/1/0、兩neutral0，withdrawn明用歷史928；不把F冒作實跑M |
| W平面群快取定向與反證 | **實跑W：14+15+7=36/36、零skip、三suite0；已合流M** | 354compile/link0；完整撤回39語意例仍綠，insert比較次數0/84/0對應正常exit0/1/0；五細控制及四行見證撤回均0/1/0。不能代正式N64 wall或F全驗收 |
| required CI | **F run40066383912／E12f36515 run40066703178，各七 job failure** | 本輪18次API原讀均0，14 jobs皆runner_id0／steps0；failure annotation為付款失敗**或**支出上限，Ubuntu migration notice另列。這是未啟動的環境阻擋，B3未解除，沒有自認替代驗收已接受；後續新E不得沿用此CI run |

**沒有新增允許skip：僅原 `py:test_gdi_contract` 在Linux缺compiled Windows GDI harness的既定skip。** F native尚未跑，不預先計為一次skip；Q38既定registry排除依原契約。原golden、斷言、時限及16MiB stack不放寬。

待修與待決界線保持原判：

- R6全部36個原交錯樣本與中位數已核，N16/base與N64/main兩紅屬後續根因調查，門檻仍≤1與≤1.3；N32/N48及sourcecalls綠不能解除它們。R6的source calls仍82668→364369；compare assertion之後audit未達，`ABC_result` key缺席／all-required=false／full-acceptance=null。R5原樣本另保歷史，不混成R6，也不以gprof `-O1/-pg` self time代原`-O2` wall。
- R6與R5均在原 `verify_linux.py:156` 的 `assert not failures,failures` 保同三個stdout差：`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。175 scenes／350 runs與trace exits皆0不代表最後exact assertion通過。#323 base=`b74f9a2ae7ade1555b9be45283adecc097fb76e3`，main=`adbaebf9c73ea6801d7b4d5214e4b846b132923b`。
- 歷史P-189 `p189_verify.py:195` 原 `assert raw['base'] == raw['fix']` 在第127組 `repo-_role_priority_mutant.scene` 首差中止；126相同不是175全過。base=`3e600772`。兩版reject／幾何dump相同，但load回覆的I22定位邊／區間診斷不同。
- 現行I22正反例要求定位診斷。未有核可版本界線／comparator裁決前，不刪、不過濾、不正規化exact；**Q-323-ABC／Q-P189-EXACT仍待決**。Q-323-N64按原1.3繼續自主修復；CI B3按原收據與正式接受界線處理。#314 SSOT後續補句及#335未核可操作只準備、不改公理。

原件定位與公開限制：

- M架構302原件／4,999,779B已在F的 `evidence/geo337-train-20261024/architecture-8d2a-complete/` 公開，原1755/0 actual隨包公開；704/0 adoption/check獨審與F自身check原1已在E3df56的current-R6-terminal公開。非evidence只report／receipt變更。
- W的完整8529member原包與歷史R1紅、R2綠、四行見證反證已普通push至child E=`f7a389deafed64f0f3137c0086a7033841c709e3`，正文D=`37a2f117529c15c6525be79b17389d47b43a9acd`；主列車E12f36515已合入 `evidence/geo343-plane-ranges-df66452e/`。實跑來源仍W，不移標F。
- R5小終態、v5工具與自驗原件、原CI／ledger流已於E=`586f01d3e18f09145cc008816c47e1f45340f077` 的 `current-R5-status/` 公開。**R5完整原件已在雲端一次封包0，尚待完整獨審／出版；R6完整raw尚未封包，兩輪小摘要均不當全包。** 同E的 `full-U-five-stage-raw/` 已公開9091member原U全包與50331/0獨審；U source=`ca7838e0f4950452b9befcf40899d606db9b81fa`，不能改標F或R5。
- K node-hint觀察證據已普通merge於E=`b4639b4d856719023b61c6cc9317661779558763`，`evidence/geo323-node-hint-a22df116/`。只觀察，未改K策略或正式性能裁判。
- L只供[歷史PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/1952b0ae604291a2ec447a5cc684d6ab91306779/evidence/geo337-train-20261024/PROGRESS.md)追溯；原P189 full1、#323 exact／N64紅、CI／環境失敗保原SHA，不移標F。

獨立線#348的F73定向H3與四組反證已完成，首批末三項環境未跑／exit1保原，只補跑三項0/1/0；兩個512load原600秒timeout仍紅、容量變更未合本列車。#345原六次19方法／零skip真0，E99646d41／Dc5515c14已公開，未取得可合併裁決。新12群＋105保全退休與11root archive alias擴充均有獨立證據，完整維護出版另批；維護0不當產品gate，全部共享alias須完整de-link後才可寫。

本稿currentCI原件已在E3df56的 `evidence/geo337-train-20261024/current-R6-terminal/required-ci/` 公開，實讀對象仍F／E12f，當前E3df的CI未讀；原API讀取成功不代表required jobs通過。R6小終態 `/workspace/geo323-r6-terminal-summary-20261024/SUMMARY.json`（30,747B，SHA349c75785e5b08cf6623a1eba532ae5a39cdcd386c2e0a64431aa13c9bf2d9a1）完整投影原receipt／36樣本／profile；671/0獨審亦核五CLI／outer原流、當前18CI讀取與Fcheck。R6小件、兩原run的CI／Fcheck與peer已在E3df56公開（185檔／664097B），完整R6 raw與source準備原件另封；不作最終驗收通過聲明。
