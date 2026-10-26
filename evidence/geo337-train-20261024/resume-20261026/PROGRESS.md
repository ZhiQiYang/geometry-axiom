# #338 current-state：本輪清理與新 F reader 已完成

2026-10-26 UTC。產品候選仍是 `cbf0fb621888596aa14ad5f2349b503e23b1b72d`（F），分支 `codex/train337-recovered-evidence-20261026`。本輪只增證據；上一輪證據 `dea5d12a88c0a2ed93141014524dce5d104f8b1f` 是基線，不當成本輪新成果。尚未 READY-TO-MERGE。

原 #338 head 仍是 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，F 尚未採入其產品 ref。本輪 fetch 的 main 為 `405f8c5e1a637a16cbe47470faf5ae1fa02b8676`，handoff 為 `628507bceec091241ee3c83fc1003ff2ac31ac74`；沒有競寫原列車或 Grok 分支。

## 唯一 current-state 矩陣

| 項目 | 真實結果／來源 | 本輪狀態與限制 |
|---|---|---|
| 全123突變帳本 | S10 `82c922a3941525d3a094ac0158bdc7dea57ea360` 真 exit0 | 既有原件已採入F，不重產已有效帳本；114 killed／5 equivalent／M20 crashed／3 retired保持 |
| mutate.py --check | F exit0，123/123 | 上一輪同F有效驗證，不計為本輪新跑 |
| 架構三條 | F 0/0/0，798 edges／205 generic／18 product | 上一輪有效驗證；本輪產品/測試bytes未改，不重跑製造進度 |
| reader generate | **本輪 F exit0**，207 clauses／1261 blocks／31 witnesses | 原命令與reaper；inner 4.566017秒 |
| reader check | **本輪 F exit0** | inner 1.664875秒，正典bytes仍與F一致 |
| reader unit | **本輪 F exit0**，51 tests／0 skip | inner 163.323779秒；173個ResourceWarning完整保留，不能稱零警告 |
| native | 新F UNRUN；F9歷史exit1：5327 pass／1 fail／1原允許GDI skip | 本輪清理後仍未通過原/tmp 128MiB准入，不把未啟動算通過 |
| 六browser | 新F canvas／assembly／documents／grid／space／timber均UNRUN | F9歷史六組0仍保留歷史身分；原單job416MiB＋thin seed及兩OWN合計2GiB規劃不變 |
| Q38 | F9完整44項exit0，43 killed＋SPM24 equivalent | 歷史來源，未冒充新F |
| §7 axiom／card | 新F尚未執行；F9 axiom歷史0 | 正準備獨立axiom資源核對；card原448MiB規劃仍不足，兩者分列 |
| #323 R8／exact | R8原36效能樣本達門檻但outer1保留；F9 exact outer/stage/audit0 | 不重抽樣；三差例外不外推P-189 |
| P52／P-189／required-eight／PF3／whole-memo／RC／#314／Reading A其他專項 | 尚未閉合；P-189原exact紅燈保留 | 沒有新增skip、修改golden、放寬斷言／時限或擴張批准 |

Reader三正式項的inner/outer真退出碼均0。RESULT SHA256：`c4f253756cdb03d0f753c60b8a33b824104caa9cbd383f8e93f057a67a2fd94c`；actual peer `805e8a051614c2d9d47a2852998fe54f283f9b46515c0c4451fba1ec7763a6f9`。212個必要來源、五份fixture、index/HEAD及publisher保全；canonical inode因原生成器替換而改變，bytes/hash相同。51 tests的兩個docstring換行案例造成首次peer解析失敗，原1保留，窄幅修正後1955項核對0；沒有重跑裁判。原runner實際outer timeout=None的事實保持，不將未使用的300/1200變數當已執行限時。

## 本輪新批准清理的真實終態

使用者於2026-10-26 17:59:47 UTC針對固定E9清單給予新批准；原拒絕紀錄保留，不能繼續把這一批列為待批准。範圍只限E9 `9a57aea2128a7bc3985064932c24e2229fd8fcb8` 的0000 retained_rows、0010、0009、0008。

先完整重驗3156葉/108目錄；額外maps檢查因兩個平台程序不可讀退出1，沒有刪除。後續以本機Docker endpoint、零容器/volume/plugin、原可讀proc與root no-reuse規則核實有限的無已知任務consumer，保留不可讀界線；沒有修改安全設定。Fresh遠端4份manifest＋26份raw共30路徑真0，24個唯一API完整讀回與E9逐byte相同。

原未修改清理本體只執行一次，18:30:29.532759至18:30:39.271074，**exit0；3156檔、108空目錄實際完成，跳過0**。原排除73項、F9六ELF、fixtures與Git保全成立，沒有擴刪新cache。RESULT SHA256 `075534e2c72f827b30fbe3d5d7da65398a371183fa263df12180ae5d8949aa4e`；最終actual peer R2 `839c02c12613bd46b101a0ba2155a006c66c9af10f09fb65cf6d81008232639c`，17192項核對0。首輪peer程式的欄位/刪index先後解析錯誤與原1亦保留。

| 實際掛載 | 清理前可用bytes | 清理後可用bytes | 實測淨變化 |
|---|---:|---:|---:|
| /tmp | 10,326,016 | 117,559,296 | **+107,233,280** |
| /workspace | 4,378,624 | 4,378,624 | 0 |
| /dev/shm | 15,815,753,728 | 15,808,962,560 | -6,791,168（新原始收據） |

這是18:30的實測；native當時距134,217,728 bytes原准入尚差16,658,432 bytes。後續新收據會消耗空間，真正啟動前仍須fresh原准入。清理成功不等於native/browser可執行。額外暫存正在依新指示唯讀盤點並準備具體範圍，**沒有額外刪除批准或執行**；原2GiB／native128MiB／browser416MiB守門不變。

## 原件交付、管理入口與下一步

本包保留本輪獨有的完整argv、退出碼、stdout/stderr、環境、SHA、journal、原失敗與修正後審查。只有freshremote的24個API stdout改以固定E9已有完整raw bytes逐項索引；全部30個path aliases、Git OID、bytes/hash及fresh時間/命令都保留。新tar不含這24個gzip容器，不能宣稱容器在包內；本地原件未刪。本次ls-tree輸出及所有新reader/清理原流仍完整收入tar。

既有工作管理CLI入口已核實：geometry-web/work-manager/cli.py。現行私有ledger仍unknown；預設.local不存在，有限搜尋不等於證明全機無DB。為避免另建空佇列，import-snapshot/reconcile/list-ready/list-alerts均UNRUN；舊資料保持，不另造替代任務或佇列。

接續工作是補native最小容量解除範圍、實證standalone axiom編譯暫存需求，繼續可負擔的正式項目。完整card與六browser仍按原資源守門處理。#54若另行核收只限單房候選，不擴#87；沒有合併PR/main、部署、付費或新增公理。
