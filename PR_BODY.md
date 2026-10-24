本 PR 接替 #337，整合 #299+#316、#314 題 3 比較器、已核可的 #318 閱讀 A、#323、K source/edge 索引修正、#339/#340 與 #343（含 #341/#342）。本輪再修正 provider hint 的跨家族碰撞；完整 key 身分比對、graph 順序、失效與 fallback 保持原契約。容量仍為 64，未合入 #344/#345/#346/#347/#348。**目前不可合併，維持 draft。**

| 身分 | SHA |
|---|---|
| 固定產品／測試／架構產物 F | `6df0264f75e84f03adb70746b6ac3db07a9910fc` |
| 證據 head E | `bd5df6b7fb3c563fa10d0e4cfd37e2ee3ca2b99e`；與 F 的非 evidence tree 相同 |
| 架構真正執行 M | `e321026fb9bc9bc19c54b8034af6e6eaec2857f9`；F 只採用 M 的衍生 report／receipt |
| K 定向執行 S | `1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`；四個產品／測試葉一般合入 M |

以下是唯一 current-state 矩陣。UNRUN／UNREAD 不是通過；獨立審查的核對數不是產品測試數。原門檻、golden、斷言及時限均未放寬。

| Gate | 當前結果與真正執行 SHA | 仍待完成的範圍 |
|---|---|---|
| 全 123 突變帳本 | 原 tracked `python3 tests/mutate.py --check` 在 E51e36b94 真 exit1：120 stale／3 retired／0 invalid；E51 與 F 的非 evidence tree 完全相同 | 全量重產 UNRUN；外層收件 0 不等於 check 0，不移標成 F 實跑 |
| 完整 native | UNRUN at F | 完整原 aggregate，16 MiB stack、原 strict registry |
| canvas | UNRUN at F | 完整 golden、P73/P88；獨占執行 |
| assembly／documents／grid／space／timber | 各 UNRUN at F | 原 workflow，各自埠與暫存目錄 |
| P52 | UNRUN at F | 原 fix median ≤ main，原控制全保 |
| Q38 | UNRUN at F | 納入 AC23 後完整 44 案例；不能借歷史 42 案例 |
| §7 card-reference／axiom | 兩項 UNRUN at F | 完整原突變與恢復反證 |
| P-189 full exact／timing | 兩項 UNRUN at F | 歷史 full exit1 未解除，timing 綠不能代完整 bytes 比對 |
| #323 R7 prepare／build／compare／perf／profile | F 真終態 outer1；execution=0/0/1/0/0、CLI=0/0/1/1/1。N64/main=1.2292230778583162≤1.3 綠；N16/base=1.05190582882169>1 紅；原三個 stdout 差仍使 compare1 | 原36交錯樣本全保；N32/base=.8290229168845338、N48/base=.7499983665267913、calls64/32=4.407618425509266≤4.5 綠；ABC_result 缺席／all-required=false／full-acceptance=null，不外推未到的 audit |
| #323 required-eight／PF3／完整 native 後段 | UNRUN at F | 五 stage 不等於原完整八 stage |
| #323 whole-memo／恢復／隔離 ABC | UNRUN at F | 同列車反證不能代跨版本 exact |
| reader 三條／RC builder、checker 反證 | UNRUN at F | 原 SSOT 流程與兩刀 |
| #314 六 suite／Node inspector | UNRUN at F | 已核可有序比較器不變 |
| 閱讀 A native／oracle／mutants-only／完整 quick | UNRUN at F | #335 未核可 CLI 初放能力仍另案，不冒已解決 |
| 架構三原裁判＋四檔 | M 真 exit0/0/0，F 已採用；generic205／product18，零 skip | 604 inputs／334 owned／270 excluded／798 edges／0 diagnostics；唯一 input delta 為 K source.c。manifest937／55、scan bytes不變；九 guard 各 0/1/0、neutral2 綠，withdrawn 明用歷史 928 |
| K provider hint 定向與反證 | S 原 18＋24 方法全綠、零 skip；完整原件已普通合入 E51 | 整刀 warm lookup calls 0→16→0、正常 exit0/1/0；原十控制、full-provider／middle-byte／unaligned／allocation fallback 見原件。定向綠不替代正式 wall 或完整 native |
| required CI | F run40070571951／E597bce63 run40070806058，18原API讀0；各七job failure、runner_id0／steps0，failure annotation 為付款失敗或支出上限未啟動；Ubuntu notice 另列。當前 Ebd5 的 CI 未讀，不能移標 E597 的 run | 歷史 CI 付款失敗或支出上限未啟動，不能推定新 head 的 CI；沒有自行宣布正式替代已獲接受 |

允許 skip 僅原 Linux 的 `py:test_gdi_contract` 缺 compiled Windows GDI harness；F 的完整 native 尚未跑，不預先計入一次 skip。Q38 原 registry 的既定排除不擴張。

仍紅／待決項：

- R7 的 N16 median fix=0.12007854899275117s、base=0.1141533259942662s，原門檻仍≤1；三個原配對樣本均較慢。N64已達原門檻，但不解除 N16 或 exact。後續只診斷／修根因，不以同源重抽挑綠。O1/pg 計數顯示 K 查找下降；另從原 O2 ELF 找到 persistent 路徑仍清零未用的127,584B local context，正準備可撤回單因修正，尚未合入或宣稱 wall 改善
- 原跨版本 comparator 在 `verify_linux.py:156` 的 `assert not failures,failures` 曾留下三個 stdout 差：`_role_priority_mutant.scene`、P8 低／高凹角；175 scenes／350 runs 的程序退出 0 不等於 exact assertion 通過。base 固定 `b74f9a2ae7ade1555b9be45283adecc097fb76e3`，main 固定 `adbaebf9c73ea6801d7b4d5214e4b846b132923b`。
- 歷史 P-189 `p189_verify.py:195` 的 `assert raw['base'] == raw['fix']` 在第 127 組 role-priority 首差中止；126 組相同不能當成全過。幾何 dump 與拒絕結果相同，但現行 I22 必要定位診斷改變。**Q-323-ABC／Q-P189-EXACT 仍待版本界線／comparator 明確裁決**；未獲核可不刪、不過濾、不正規化診斷。問題已記 QUESTIONS，繼續其他不受影響工作。

原件已公開：

- `evidence/geo337-train-20261024/architecture-e321-complete/`：299 原件／4,551,015B，四檔、51 原命令流、九組 guard 反證與獨立審查；實跑 M 不移標 F。
- `evidence/geo323-provider-hint-1449d430/`：3201 members 完整原包、原 shadow／18／24 方法、整刀與鄰接反證，以及第一次環境失敗；保原 source SHA。
- `evidence/geo337-train-20261024/full-R5-five-stage-raw/`：9055 members／31,186,327B，SHA256 `caaf311a748c2ce1dc4ebd754fbebc9c4d70f59a5d0938fb2e9e34e57f2dd794`。
- `evidence/geo337-train-20261024/full-R6-five-stage-raw/`：9062 members／31,317,807B，SHA256 `a9113e5e8e3474da70ee21970a29d451a46e148a3abdde1cecded4c36631d3f1`。
- R5／R6 的完整原件、inventory、環境、原指令／退出碼／全輸出、36 原樣本與四 profiles 已在 E597bce63 普通推送；每輪七個 ELF 只附 hash inventory，原 payload 仍保存在雲端。原 outer1／exact 三差／null 完整保留，封包成功不是產品通過。原件收件時的 published:false 保留，公開事實由後續普通提交另證。
- R7 六原binding、小終態、五CLI與outer完整流、三份真正工具poll JSON、當前CI／帳本check、stage工具與672/0獨審，已公開於 Ebd5 的 `evidence/geo337-train-20261024/current-R7-terminal/`（399檔／1,122,842B）。完整R7包已在雲端單次封存並經50504/0獨審：9128members／31,359,550B，SHA256 `8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e`；尚未公開，不把小摘要冒全包

歷史結果只供追溯：R6 來源 `2bbe54f1` 的 N64/main=1.3731562025736295>1.3、N16/base=1.0434575834374764>1；R5 來源 `a22df116` 的 N64/main=1.3369644933292553>1.3。全樣本與紅燈保留，不混成 R7、不重抽同源樣本挑綠、不以 gprof 時間代 O2 wall。更早 L 的完整 native／browser 綠僅為歷史，不能外推 F。

獨立工作線繼續：#344 已在 F7 上一般合流，原 S540 的 VM9 0/1/0 與 strict aggregate9=0 已公開，新來源與完整 canvas 三階段另列；#348 兩個 512 四指令批次的原 600 秒逾時仍紅，完整原件與後續定向反證已公開 E9a8584f5／D1f0e9d86，沒有合入本列車。Git objects、收據、fixtures 均保留；維護成功不算產品 gate。

最新已讀審查：handoff `ef7b3191` 所同步的 2026-10-24T06:38:46Z／head597bce6。B1尚未完成；B2的N64已由R7原門檻真綠，N16與exact仍紅；B3未解除。本稿更新C1的F/E/實跑來源與目前CI，不宣稱整項可合併。
