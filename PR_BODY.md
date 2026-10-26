# #338：候選 F 已採入有效帳本與架構，完整驗收仍未完成

本文件是本輪唯一 current-state 矩陣；舊矩陣只作歷史。沒有合併 PR、改寫歷史或部署。

| 身分 | 完整 SHA／分支 |
|---|---|
| 已讀 #338 head | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，`codex/train-337-continue-20261024` |
| 新候選產品 F | `cbf0fb621888596aa14ad5f2349b503e23b1b72d`，`codex/train337-recovered-evidence-20261026`；普通 push、完整遠端三檔核對 exit 0 |
| 本輪證據 E | `d803910822803a020a57a7568c62325a076239f0`；只變更 evidence，產品與 F 相同 |
| 全帳本執行 S10 | `82c922a3941525d3a094ac0158bdc7dea57ea360`；120 執行 head 保持原值 |
| 架構四檔生成 A | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`；F 再跑三條原裁判 |
| 歷史 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| 歷史 F8／R8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad` |

候選 F 尚未同步進原 #338 head。原列車與 Claude session f46787ac 的即時寫入範圍未被原始執行紀錄確認，因此產品與證據保存在 root 獨占分支，不改原列車 ref。本正文由對應 prbody 與既有交接 request 更新原 #338，沒有新增替代產品 PR，也沒有改 PR head。

| Gate | 真實結果與執行來源 | 目前界線 |
|---|---|---|
| 全 123 突變帳本 | S10 exit 0；114 killed／5 equivalent／M20 crashed／3 retired，原 stale exit 1 也保留 | 完整生成原件已逐 byte 採入 F；沒有重抽或改 execution head |
| `mutate.py --check` | **F exit 0**；123/123，stale/survived/invalid/blocked 皆 0 | 證明 S10 帳本於 F 仍有效；M20 原 crashed 分類未改 |
| 架構三條 | **F 0/0/0**；798 edges、零 diagnostics；generic 205／product 18、零 skip | A 的四檔組裝 exit 0；604 raw/LF/Git closure 不變，manifest/scan byte 不變 |
| native | F9 exit 1：5327 pass／1 fail／1 原允許 GDI skip | 新 F **UNRUN**，未達原 `/tmp` 128 MiB 准入；#314 修正原反證保留 |
| canvas | F9 exit 0：2267 assertions／85 golden | 新 F **UNRUN** |
| assembly | F9 r2 exit 0：150 assertions；r1 環境 exit 1 保留 | 新 F **UNRUN** |
| documents | F9 exit 0：47 assertions／8 screens | 新 F **UNRUN** |
| grid | F9 exit 0：356 assertions | 新 F **UNRUN** |
| space | F9 exit 0：242 assertions | 新 F **UNRUN** |
| timber | F9 exit 0：79 assertions | 新 F **UNRUN** |
| Q38 | F9 完整 44 項 exit 0，43 killed＋SPM24 equivalent，完整封包已交付 | 保留 F9 執行身分 |
| §7 axiom／reader | F9 axiom exit 0、reader 0/0/0 | 保留歷史來源；card 等未完成項不冒通過 |
| #323 R8 效能 | 原 36 樣本：N16/base `0.9834192453688345`≤1；N32 `0.9007932884873169`≤1；N48 `0.7392862448969592`≤1；N64/main `1.2846970752586067`≤1.3；calls64/32 `4.407618425509266`≤4.5 | 原 outer exit 1 與原始差異保留，不重取最好樣本 |
| #323 exact | F9 175 場景／350 列，outer/stage/audit 0 | 只依已核實使用者三差白名單，不擴及 P-189 |
| P52／P-189／card／required-eight／PF3／whole-memo／RC／#314／Reading A | 仍有未跑或未閉合項；原 P-189 exact 紅燈保留 | 不以工具合成測試或封包核對代替正式產品結果 |
| 完整雲端替代 CI | **尚不成立** | native、六 browser、Reading A oracle 與適用專項未收齊；未標 READY-TO-MERGE |

原 Linux native 允許 skip 僅為缺 compiled Windows GDI harness。browser 仍依原工作流程分組範圍，沒有新增 skip 或放寬斷言、golden、時限、效能門檻。

F 相對 a6 的非 evidence 差異僅為帳本、架構 report、架構 receipt 三葉；其他產品／測試／SSOT 不變。一般 FF 與四裁判完整 argv、原始 stdout/stderr、退出碼、環境、F 均封存；五份 fixture、3763 selected leaves、604 架構來源及原 publisher／old workspace metadata 保全。此 3763 葉來源不能冒充 native 的 6997 葉來源。

批准來源界線：GitHub `GET /user` 與 [2026-10-25 10:39:52Z 的 #338 留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)（內容為 Q-323-ABC 與 B3 裁決）刊載帳戶均核實為 ZhiQiYang／59477728。該留言引述使用者所選選項，但其「對本 PR 的意思」明標「本機 Claude 整理，非原話」；帳戶核實與本對話直接原話是兩種證據。既有 #323 收據按其原三差限定保留，本輪未新增比較例外。a6 的 P-189／跨 SHA 沿用新文字仍僅查到轉錄與審查引用，沒有對應新的原始批准，因此保留原比較器與原紅燈。

共同空間阻擋：單 browser 的原 416 MiB 准入目前不足，且需計入 thin seed；原 2 GiB 規劃上限不變。工具允許逐組準備、執行、持久化後再進下一組；沒有把「先建六份」加成新條件。native 的 `/tmp/geometry-tests` 仍需原 128 MiB；只設定 TMPDIR 無法解除。

自動審核拒絕的清理仍未執行：3156 葉（2439 來源副本、691 Chrome cache、2 私有 index、24 ELF）及原工具附帶的 108 個空目錄。命令未啟動，刪除 0，原 true 請求撤銷；不拆批、不換路徑重試。完整 scope、保全與遠端 hash、ownership 的限制及排除項另附 approval packet。另 165 個 GPU cache 不在本次範圍，也未執行。

後續依序：解決已具體列出的空間／來源准入，原 native 與六 browser、剩餘專項逐項保留終態；確認新裁決原件後才處理其依賴。等待期間持續做 #300 等不占重測試資源的工作。已核對的兩個 C 檔中，#348 head 尚缺 F 的四組優化；歷史兩次 600 秒都是各自四命令 preload 整批逾時，未能判定最後完成哪個命令，不能推定成單獨 loadfile 病因。

[最新 PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/d803910822803a020a57a7568c62325a076239f0/evidence/geo337-train-20261024/resume-20261026/PROGRESS.md) · [接續與未完成項](https://github.com/ZhiQiYang/geometry-axiom/blob/d803910822803a020a57a7568c62325a076239f0/evidence/geo337-train-20261024/current-status-clarified-20261026/NEXT.md) · [批准與空間依賴](https://github.com/ZhiQiYang/geometry-axiom/blob/d803910822803a020a57a7568c62325a076239f0/evidence/geo337-train-20261024/current-status-clarified-20261026/QUESTIONS.md)
