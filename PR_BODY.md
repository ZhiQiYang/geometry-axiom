本列車整合 #299＋#316、#314 的鎖定比較器、#318 閱讀 A 與 #323 載入修正。**維持 draft，尚未 READY-TO-MERGE。** 以下是唯一 current-state；舊正文及撤回來源的矩陣只留作歷史。

正式候選回到 **F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`**，位於 `codex/train337-recovered-evidence-20261026`。原 #338 列車 head 現為 **`e1efab34d970a052a8082fa62e478ad13a0625ae`**，base main=`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`；撤回提交把 tree 恢復為 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77` 的內容，尚未採入 recovery F。

[撤回提交](https://github.com/ZhiQiYang/geometry-axiom/commit/e1efab34d970a052a8082fa62e478ad13a0625ae) 及 [固定 handoff 的 01:48 更正](https://github.com/ZhiQiYang/geometry-axiom/blob/8992388515172d068ee1e28526e1103ff18aa4f2/handoff/pr-reviews/338.md#L270) 明確撤回先前 F′=`a4bd77e8090f5a82f0c8934c30c5335782293922`、不採帳本與「閉包改四檔」指示；其本機參考 evidence `2d7a635ec6408f7fda80db13992d08feb4727e4b` 亦已從列車撤回。不是要求丟棄已完成的 S10 或將 F′ 結果移標 F。

已公開且完整遠端核對的 recovery 證據 checkpoint **E=`047d93f01ba1bd349ebc256c4e8d19209bfd0f49`**；其包含 documents E=`45dd4d662eac9297eda8473742c9943a1cb336cb` 與較早 axiom E=`2d576269ab85ef64a921bc4b15d013ca2ef5b4fb`。本批 card 原件 **55,775,729 bytes 已成功發布並核對遠端 bytes**；F assembly 已在本地正式核收0，尚待公開原件。原已套用正文 D=`2cce6afaeac87521924bde28660a71e43ad306e5` 是舊版；本次新正文與其證據界線分開。

| Gate | 固定 F 的真實結果／目前狀態 | 原件與限制 |
|---|---|---|
| 全 123 突變帳本 | S10 `82c922a3941525d3a094ac0158bdc7dea57ea360` **exit0**：114 killed／5 equivalent／M20 crashed／3 retired | 已逐 byte 採入 F，120 execution heads原值保留；已有效成果不重產，也不使用撤回的「不採帳本」指示。 |
| `mutate.py --check` | **F exit0，123/123**；stale／survived／invalid／blocked皆0 | 同 F 已有有效收據，不重跑。F′ check1／53 stale是撤回來源的真實歷史，不是 F 的紅燈。 |
| 架構三裁判／四檔 | **F 0/0/0**；798 edges、205 generic、18 product、0 skip | F 採自己的架構收據；manifest/scan既有逐 byte保全。不採已撤回的 a4bd 架構兩檔，亦不以其本機 ALL PASS 摘要替換 F 原件。 |
| reader generate／check／unit | **F inner/outer 0/0/0**，51 tests／0 skip | 已交付原件，173 ResourceWarning保留；有效結果不重跑。 |
| §7 axiom | **F primary/reaper/outer0**；44 baseline，五組 red1／restored0，全部 killed | 11 subprocess／269 tests／0 skip，254.585306秒。完整原件已公開於 E2d576269 的 `axiom-F-cbf0fb62-20261027/EVIDENCE.tar.gz`；262葉／7fixtures／index／refs及目標恢復核對0。 |
| §7 card | **F primary/reaper/outer0**；43 baseline、53組依原序 red1／restored0，116 ELF全留 | 107 test processes／149 test invocations，431.763707秒；2409項原件核對0，262葉／15目標／7fixtures／index／refs恢復。完整封包 **55,775,729 bytes 已公開於 E047d93f0**，遠端 byte核對0；此前 HTTP422與一般Git傳輸失敗原件均保留，沒有重跑card取新樣本。 |
| native | **待外部正式終態；本任務未啟動 F native** | 既有外部任務已接手固定 F，尚無本次可核收final exit。F9 原1（5327 pass／1 fail／1 原 GDI skip）仍保留；#314修正0/1/0不等於完整 native通過。 |
| canvas | **F UNRUN** | F9 歷史0，不自動沿用。撤回來源本機a6參考1亦保留，README曾列P52-3兩斷言／段落下限失敗與transport failure，不全歸成速度問題。 |
| assembly | **F primary/reaper/wrappers0（本地已核收，尚待公開原件）**；150 assertions、0 skip、9 screenshots | 192.930640466秒＜原900秒；9151項核對0，3759葉／private index／golden bytes保全。原assembly partial模式不宣稱完整canvas golden比較；a4bd150／0及F9 r1環境1、r2正式0分開留歷史。 |
| documents | **F inner/outer0**；47 assertions，0 fail/skip，8 screenshots | 70.97391320997849秒，原10分鐘時限保持；完整原件已公開於 E45dd4d66 的 `documents-F-cbf0fb62-20261027/EVIDENCE.tar.gz`。另一次a4bd 47／0分開留作撤回來源歷史。 |
| grid | **F RUNNING，尚無final exit** | root session36920已正式啟動，保持原完整workflow；不得把啟動算通過，F9歷史0不移標。 |
| space | **F UNRUN** | F9歷史0及原2個分組skip保留，沒有新增skip。 |
| timber | **F UNRUN** | F9歷史0及原5個分組skip保留，沒有新增skip。 |
| 閱讀 A oracle／矩形逐毫米／凹角579 | **F 尚未閉合** | 最新ChatGPT審查明列 final來源必跑；撤回來源或本機a6參考0不關閉本列。 |
| Q38 | **F UNRUN** | F9原44 exit0／43 killed＋SPM24 equivalent保留；F9→F的#314測試變更進入副本digest，不能省略。 |
| #323 R8效能／exact | **尚未閉合到 F** | R8固定源 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`：N16/base0.9834192453688345≤1、N32/base0.9007932884873169≤1、N48/base0.7392862448969592≤1、N64/main1.2846970752586067≤1.3、calls64/32=4.407618425509266≤4.5；原36樣本及outer1保留、不重抽。F9 exact175場景／350組outer/stage/audit0維持原精確三差界線。 |
| P52／P-189／required-eight／PF3／whole-memo／replay／#314／RC其他 | **尚未閉合** | P-189 strict exact原紅與原取樣保留；逐項完整輸入／裁判閉包或必要重跑未完成，不以card或局部相同bytes推論。 |
| 完整雲端替代CI | **尚未成立** | final F仍缺完整native、canvas／grid／space／timber、閱讀A及適用專項／原件；assembly已本地0，公開封包尚待完成。a4bd歷史CI run40431992777七jobs failure但runner0、steps=[]，不是產品紅綠，也不是e1ef或F的新CI結果。 |

F9=`4f8a794f4167c3562eb182045102e86e9e37cca9`。Linux native既有允許skip僅缺 compiled Windows GDI harness；browser保留表內原分組skip，沒有放寬golden、斷言、時限或刪測試。已公開的指令、退出碼、完整stdout/stderr、環境、execution SHA與逐檔hash見 [E047d93f0 原件與進度](https://github.com/ZhiQiYang/geometry-axiom/tree/047d93f01ba1bd349ebc256c4e8d19209bfd0f49/evidence/geo337-train-20261024)。F documents環境為Chrome156.0.8078.47／Node24.19.0／Python3.12.14／GCC14.2／Noto CJK已安裝；不把工具或封包審查當產品通過。

撤回來源a4bd的assembly150／0、documents47／0與帳本check1都保留原實際SHA。該check真跑123列：killed62／crashed1／equivalent4／stale53／retired3，survived0／invalid0／blocked0；712葉來源／裁判依賴與完整Git tree核對，不是a6轉述。它證明該次check有效，沒有自動豁免或取代 F 的有效帳本。

[10-25裁決留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849) 的作者帳戶已與 `gh api user` 核對為ZhiQiYang／59477728；使用者選項原文與留言中明標「本機Claude整理，非原話」的技術解釋仍分開。#323精確三差與效能門檻保留；**P-189擴大白名單的原始批准尚未核實，保持strict裁判**，不自行延伸。01:48更正已撤回F′／不採帳本／四檔閉包方案；不能將作廢方案當新豁免。本任務仍不合併PR或main。

card一般Git傳輸曾意外產生約2.42 GB pack，使兩OWN當時實測約**5.303 GB，超過當時4 GiB工作規劃**；該次傳輸未成功push，原始失敗與原件保留，沒有修改產品。協調者其後將自訂工作規劃調為**兩OWN合計最多8 GiB**；這不是使用者數值門檻、平台配額或安全設定變更，也未降低64MiB發布保留與正式斷言／時限。須以fresh實體容量、完整執行及留證成本實證准入後串行續跑；前次SHM free約12.568 GB只是歷史觀測。固定新增168檔已獲批准，本輪實際結果：**exit0，刪除168檔／跳過0／刪目錄0；02:45:54–02:46:00 UTC 完成，`/tmp`實測回收22,892,544 bytes、終態free120,623,104 bytes，workspace／SHM回收量0；33目錄及HEAD/config/refs保全核收0；已備份的3個私有index依批准刪除，不等於native通過**。原3156檔清理早已完成，不重做。native由外部既有任務獨立接手，不能用此處SHM free抵算本環境真正 `/tmp` 准入。

下一步核收正在執行的固定F grid、公開F assembly原件，並依序完成其餘驗收；已公開card不重跑。按 [最新ChatGPT審查](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6409950139) 完成固定F的native、其餘browser、閱讀A與專項；產品／測試bytes相同不自動授權移標。完整收據與最新審查通過之前維持draft。
