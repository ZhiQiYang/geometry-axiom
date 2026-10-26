# #338 current-state：閱讀器通過；新增容量候選已備份，尚未清理

2026-10-26 UTC。產品 F 仍為 `cbf0fb621888596aa14ad5f2349b503e23b1b72d`。本提交只增加證據；父證據為 `df84890966a600d3ba7e39c5b8ba882b18d1a9b2`。原 #338 head 仍為 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，未改寫原列車。尚未 READY-TO-MERGE。

## 唯一 current-state 矩陣

| Gate | 執行來源與真實結果 | 目前限制 |
|---|---|---|
| 全 123 突變帳本 | S10 `82c922a3941525d3a094ac0158bdc7dea57ea360` exit 0；114 killed／5 equivalent／M20 crashed／3 retired | 原件已採入 F；120 execution heads 不改標，未重跑已有效結果 |
| mutation check | F exit 0，123/123 | 既有同 F 驗證 |
| 架構三條 | F 0/0/0；798 edges、205 generic、18 product | 既有同 F 驗證，非本次新跑 |
| reader generate／check／unit | F 0/0/0，inner／outer 均 0；51 tests／0 skip | 173 則 ResourceWarning 原樣保留；原件已在父證據交付 |
| native | 新 F UNRUN；F9 歷史 exit 1：5327 pass／1 fail／1 原允許 GDI skip | 原 `/tmp` 128 MiB 准入未達；先準備完整來源轉移 |
| canvas／assembly／documents／grid／space／timber | 新 F 六項 UNRUN；F9 歷史六項 0 | assembly 原 r1 環境失敗保留；space 原 2、timber 原 5 個分組 skip 保持；未新增 skip |
| Q38 | F9 完整 44 項 exit 0，43 killed＋SPM24 equivalent | 不改標新 F |
| §7 axiom／card | 新 F 正式項目均 UNRUN；F9 axiom 歷史 0 | 本次四個 `cc -###` 資源診斷 0，不是編譯或突變驗證；card 原 448 MiB 規劃保持 |
| #323 R8／exact | R8 原 36 效能樣本達原門檻，outer 1 保留；F9 exact outer／stage／audit 0 | 不重抽樣；既有三差範圍不擴及 P-189 |
| P52／P-189／required-eight／PF3／whole-memo／RC／#314／Reading A 其餘項目 | 尚未閉合；P-189 原 exact 紅燈保留 | 不接受新語意例外、不放寬斷言／golden／時限 |

F9 為 `4f8a794f4167c3562eb182045102e86e9e37cca9`。原結果、失敗及執行 SHA 都保留；封包或發布核對不代替產品驗收。

## 已完成並交付的工作

使用者 17:59:47 UTC 新批准的固定舊清單已於 18:30 完成：3156 檔、108 空目錄、跳過 0、exit 0；`/tmp` 實測回收 107,233,280 bytes。這一批不再待批准。原排除 73 項、fixtures、Git objects、F9 ELF 與未知修改保全。

新 F 閱讀器三項原件與完整清理原件已推送父證據 `df84890966a600d3ba7e39c5b8ba882b18d1a9b2`，六份遠端 payload 全文讀回一致。封包實際核收 12837 項、發布實際核收 1062 項，均 exit 0。

正文分支已推至 `a51af370fcfe4bc5022250d2b393db233e9951b6`，交接分支至 `2d18b25b56ae47308a56c478497fd10193cf6e26`。正文／交接實際核收分別 336／363 項、exit 0；原 NEXT 全文與 request 保留，原 publisher HEAD/index 不變。PR 是否已自動套用該正文另待 handoff/pr-status 核實，不能用分支推送代稱已套用。

## 新增 168 葉容量方案

新增範圍只有三個已退役 checkout 的私有 index 與十一個舊 profile 的 165 個 GPU cache 葉。完整固定清單見 `extra168-preservation-candidate-20261026/SNAPSHOT.tar.xz` 內的 `BYTE_MAP.json`，原始 allocated 合計 **23,707,648 bytes**。33 個 cache 目錄僅保存 metadata，沒有列入新增刪除範圍。

備份於 19:30:34–19:30:42 UTC 實際完成，exit 0；完整 tar.xz 723,012 bytes，SHA256 `f9770ca505999057c23c898d559836f74594bc66e90bf5c83479e3d76f0385f6`。168 葉的完整身份與內容前後一致，42 條 Git 原命令及完整輸出已保存；前三根 HEAD／refs／dirty 狀態精確符合原退役紀錄，沒有新的 staged 或未知修改。這是新增備份，**沒有新增刪除批准，也沒有刪除任何新增候選**。

備份 INDEX 保存的是備份前測量，內含 `new_backup_written=false`；真正落盤終態在新 backup AUDIT/RESULT，不能混為同一時點。可恢復完整 bytes／權限／mtime；inode／ctime 不能重建。不可讀的平台程序界線如實保留，任何後續刪除仍須另有批准並重新核對 consumer、身份與遠端可恢復性。

19:27:33 UTC 的 native 來源觀測因保留完整原始資料占用了 `/tmp` 4,640,768 bytes；當時可用 111,865,856 bytes。即使日後批准並實際回收整批 23,707,648 bytes，純加總僅比原 134,217,728-byte 准入多 1,355,776 bytes。來源轉移另外預估永久增加約 507,904 bytes，加少量 refs/logs 與可能的 index extension；所以不能再沿用先前「另有 4 MiB 餘裕」的舊估計。這些是估算，真正 native 准入必須在轉移／清理後重新實測。備份成功不等於 native 或 browser 已可啟動。

## 接續與未解依賴

§7 的四個 driver 診斷已真實完成，receipt SHA256 `f087dfcd582114bc8ae26afc5ffe2ea9996a2d448069c0b3e89406a9083d9905`，來源保持，未產生編譯暫存；下一步是有完整收件預算的編譯資源診斷，再決定原正式 axiom 五組突變是否可執行。診斷資源上限不帶入正式裁判，原 60／180 秒不變。

native 會重用原完整 checkout，沿原 sparse 規則核實新 F 的 6997 個實際選取葉，保全五份 fixture、ignored 原件及 Git metadata；尚未執行轉移。原 `/tmp` 128 MiB、browser 416 MiB＋thin seed、card 448 MiB、兩 OWN 合計 2 GiB 規劃都保持。

現有工作管理 CLI 入口已核實，但私有 ledger 仍 unknown；import-snapshot／reconcile／list-ready／list-alerts 都未執行，沒有新建空佇列。#54 僅單房候選，不擴 #87。未合併 PR/main、部署、付費、改安全設定或新增公理。
