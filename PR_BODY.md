# #338：新 F 閱讀器驗收完成，完整驗收仍未閉合

本文件是唯一 current-state 矩陣；舊正文與矩陣只作歷史。候選仍未 READY-TO-MERGE，沒有合併 PR/main、改寫歷史或部署。

| 身分 | 完整 SHA／分支 |
|---|---|
| 原 #338 產品 head | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，`codex/train-337-continue-20261024` |
| 候選產品 F | `cbf0fb621888596aa14ad5f2349b503e23b1b72d`，`codex/train337-recovered-evidence-20261026` |
| 本輪證據 E | `df84890966a600d3ba7e39c5b8ba882b18d1a9b2`；同分支，只增 evidence，產品與 F 相同 |
| 全帳本執行 S10 | `82c922a3941525d3a094ac0158bdc7dea57ea360`；120 執行 head 保持原值 |
| 架構四檔生成 A | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`；F 已再跑三條原裁判 |
| 歷史 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| 歷史 F8／R8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad` |

F 尚未採入原 #338 產品 ref。原列車與 Claude session f46787ac 的寫入範圍尚待釐清，因此 root 獨占 recovery 分支；既有交接 request 只讓 recovery prbody 更新 #338 正文，不改其 head/base/title，也不新增替代產品 PR。

| Gate | 真實結果與執行來源 | 目前界線 |
|---|---|---|
| 全 123 突變帳本 | S10 exit 0：114 killed／5 equivalent／M20 crashed／3 retired；原 stale exit 1 保留 | 原件已逐 byte 採入 F，沒有重產已有效帳本或改 execution head |
| `mutate.py --check` | F exit 0，123/123；stale/survived/invalid/blocked 皆 0 | 同 F 的既有有效驗證；不是本輪新跑 |
| 架構三條 | F 0/0/0；798 edges、零 diagnostics；generic 205／product 18、零 skip | A 四檔組裝 exit 0；604 raw/LF/Git closure、manifest/scan bytes 不變；不是本輪新跑 |
| reader generate／check／unit | **本輪 F 0/0/0，inner 與 outer 全 0**；207 clauses／1261 blocks／31 witnesses；51 tests、0 skip | inner 分別 4.566017／1.664875／163.323779 秒；173 則 ResourceWarning 完整保留，未稱零警告 |
| native | F9 exit 1：5327 pass／1 fail／1 原允許 GDI skip | 新 F **UNRUN**；清理後仍未達 `/tmp` 原 128 MiB 准入；#314 原修正反證保留 |
| canvas | F9 exit 0：2267 assertions／85 golden | 新 F **UNRUN** |
| assembly | F9 r2 exit 0：150 assertions；r1 環境 exit 1 保留 | 新 F **UNRUN** |
| documents | F9 exit 0：47 assertions／8 screens | 新 F **UNRUN** |
| grid | F9 exit 0：356 assertions | 新 F **UNRUN** |
| space | F9 exit 0：242 assertions | 新 F **UNRUN**；原 2 個分組 skip 保持 |
| timber | F9 exit 0：79 assertions | 新 F **UNRUN**；原 5 個分組 skip 保持 |
| Q38 | F9 完整 44 項 exit 0：43 killed＋SPM24 equivalent | 保留 F9 執行身分，不冒充新 F |
| §7 axiom／card | F9 axiom 歷史 exit 0；新 F 兩項尚未正式執行 | standalone axiom 資源診斷準備中；card 原 448 MiB 規劃仍不足 |
| #323 R8 效能 | 原 36 樣本：N16/base `0.9834192453688345`≤1；N32/base `0.9007932884873169`≤1；N48/base `0.7392862448969592`≤1；N64/main `1.2846970752586067`≤1.3；calls64/32 `4.407618425509266`≤4.5 | 原 outer exit 1 與全部差異保留，不重抽最好樣本 |
| #323 exact | F9 175 場景／350 列，outer/stage/audit 0 | 保留原三差限定，批准來源界線見下；不擴及 P-189 |
| P52／P-189／required-eight／PF3／whole-memo／RC／#314／Reading A 其他專項 | 尚未閉合；原 P-189 exact 紅燈保留 | 不把 reader、工具或封包核對代替正式產品結果 |
| 完整雲端替代 CI | **尚不成立** | native、六 browser、閱讀 A oracle 與適用專項未收齊 |

Linux native 允許 skip 僅為缺 compiled Windows GDI harness。browser 保留原分組範圍，沒有新增 skip、放寬斷言、golden、時限或效能門檻。

本輪 reader 原件 RESULT SHA256 `c4f253756cdb03d0f753c60b8a33b824104caa9cbd383f8e93f057a67a2fd94c`；actual peer `805e8a051614c2d9d47a2852998fe54f283f9b46515c0c4451fba1ec7763a6f9`，1955 項核對 exit 0。212 必要來源、五份 fixture、HEAD/index 保全。canonical 被原生成器替換 inode，但 bytes/hash 不變。原 runner 的實際 timeout=None 如實保留，沒有把未使用的 300/1200 變數當已執行時限。首次 peer 的兩個換行測試名稱解析失敗保留；修正解析後核收，沒有重跑裁判。

F 相對 A 的非 evidence 差異僅帳本、架構 report、架構 receipt；產品／測試／SSOT 其他 bytes 不變。本輪只新增證據。既有 3763 葉來源不冒充 native 所需 6997 葉。

批准來源：GitHub `GET /user` 與 [2026-10-25 10:39:52Z 的 #338 留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)刊載帳戶均核實為 ZhiQiYang／59477728。留言中的「對本 PR 的意思」自述「本機 Claude 整理，非原話」；帳戶核實不等於本對話直接原話。既有 #323 exact 原三差範圍維持；本輪沒有新增例外。新的 P-189／跨 SHA 沿用文字仍只有轉錄與審查引用，未核實對應新原始批准，原比較器與原紅燈保持。

使用者於 2026-10-26 17:59:47 UTC 新批准固定 E9 清單後，原清理本體實際執行一次，18:30:29.532759–18:30:39.271074 **exit 0**：3156 檔與 108 空目錄完成，跳過 0。原拒絕保留為歷史，**這一批已完成，不再待批准**。先前額外 maps 檢查 exit 1 保留；以本機 Docker endpoint／零工作負載、原可讀 proc 與 root no-reuse 檢查建立有限 consumer 證據，沒有聲稱讀到兩個不可讀平台程序的 maps。Fresh 遠端 30 路徑核對 0；原排除 73 項、F9 ELF、fixtures、Git objects 及未知修改均保全。

清理實測 `/tmp` 可用量 10,326,016→117,559,296 bytes，**淨回收 107,233,280 bytes**；`/workspace` 不變，SHM 因新收據減少 6,791,168 bytes。18:30 當時 native 原 134,217,728 bytes 准入仍差 16,658,432 bytes；後續寫入會改變缺額，執行前須 fresh 檢查。新增候選為 3 個舊私有 index＋165 個 GPU cache，僅唯讀盤點／備份規劃，**未取得新增刪除批准、未刪除**。不把它們納入已批准舊批。

單 browser 原 416 MiB＋thin seed、card 原 448 MiB、native 原 128 MiB 與兩 OWN 合計 2 GiB 規劃守門均保持；實體 SHM 可用量不替代規劃守門。工具允許順序執行，不要求先建立六份。只設定 TMPDIR 無法解除 native 的 `/tmp/geometry-tests` 需求。

本包收入 1635 個原件；fresh remote 的 24 個 API stdout 以固定 E9 已有完整 raw bytes 索引，全部 30 個 path aliases、命令、時間、hash／OID 保留。新 tar 不含這 24 個 gzip 容器，本地原件未刪。新 reader／清理的完整原始輸出均在包內。

既有工作管理 CLI 已核實，現行 private ledger 仍 unknown；未另建空佇列，import-snapshot/reconcile/list-ready/list-alerts 均 UNRUN。接續補 native 最小容量、standalone axiom 資源實證與其他正式驗收；#54 僅單房，不擴 #87。

[最新 PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/df84890966a600d3ba7e39c5b8ba882b18d1a9b2/evidence/geo337-train-20261024/resume-20261026/PROGRESS.md) · [本輪原件索引](https://github.com/ZhiQiYang/geometry-axiom/blob/df84890966a600d3ba7e39c5b8ba882b18d1a9b2/evidence/geo337-train-20261024/resume-175947-20261026/INDEX.json) · [完整原件封包](https://github.com/ZhiQiYang/geometry-axiom/blob/df84890966a600d3ba7e39c5b8ba882b18d1a9b2/evidence/geo337-train-20261024/resume-175947-20261026/ORIGINALS.tar.gz)
