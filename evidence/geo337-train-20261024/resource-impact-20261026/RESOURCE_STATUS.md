# 剩餘驗收的整體容量與解除條件

本次只做一次完整依賴核算與靜態影響審查，不宣稱新的產品測試通過。產品候選固定 `cbf0fb621888596aa14ad5f2349b503e23b1b72d`（F）；已交付證據 `9bd32131e1657ea3a35c41707ae3e1f42df5fdb8`。原列車 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77` 未由本輪改動。所有原件、未知修改、fixtures、Git objects 保留；沒有刪除新增 168 檔。

## 唯一容量觀測與範圍

`OBSERVATION.json` 是 2026-10-26 20:35:17.964141 UTC 的觀測，不是之後任何指令的准入憑證。兩個既有 OWN 目錄以 `(device,inode)` 去重計 allocated blocks：

- `/dev/shm/geometry-axiom-geo337-20261025`：1,691,840,512 bytes。
- `/dev/shm/geo337-F9-browsers-20261025`：386,994,176 bytes。
- 合計 2,078,834,688 bytes；距原 2,147,483,648-byte 規劃上限餘 68,648,960 bytes。
- 實際掛載 free：`/workspace` 4,378,624、`/tmp` 111,140,864、`/dev/shm` 15,793,045,504 bytes。不同掛載的 free 不能相加抵帳。

## 2 GiB 的具體來源

最早在本輪直接核實的原件是 `/workspace/geo337-five-browser-capacity-plan-20261025/PLAN.json`，建立於 2026-10-25 12:52:38.641401 UTC，來源 F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`；24,035 bytes，SHA256 `1a55a0d7f21adb1eb30db406498a93f955d5186d1c36dc90516b0376d13f445d`。欄位 `recommended_SHM.root_planning_ceiling_bytes=2147483648`；原文同時明列 `budget_is_not_proven_maximum=true`、`runtime_peak_is_measured=false`、`no_new_CI_or_assertion_threshold=true`。

修訂 `PLAN.v2.json`（26,832 bytes，SHA256 `cae41bfdbe8571d98f137f6542e2ea9af29d468af822aece2c5ceca9c7fc5d75`）把五組 browser、獨立 Git/來源、保留原流、封包、Git objects、完整遠端讀回、暫存及原 64 MiB reserve 合計估為 1,778,384,896 bytes，另留 369,098,752 bytes。這是五組舊 F9 的規劃，不能當成本輪尚可用空間。

13:01:56.490623 UTC 的 `SHM_NAMESPACE_AND_TWO_ROOTS_ADDENDUM.json`（2,201 bytes，SHA256 `770fc7aa446e99a3f5095755807bfe80a76aacac90ce596f54531bd5dba9ed4d`）明列兩 OWN 共用 `shared_combined_budget_bytes=2147483648`，`combined_admission_proven=false`，要求每次於同一核准 namespace fresh 核對。沒有證據顯示這是平台硬配額、公理或產品門檻；它是本任務原資源計畫，後續管理指示明確要求保持。不得因實體 SHM free 很多就自行放寬。

現行 `/tmp/geo337-recovery-evidence-append-preparation-20261026/publish_append.py`（SHA256 `988a3b851db4417d41c073d02e8d3e440ea7dd22c10c53421490da79174cb720`）第 25–32 行實際強制：已占用兩 OWN + `3P + 65536L + 8M + 67108864 <= 2147483648`，其中 P 是新提交 payload 總 bytes、L 為葉數、M 為原 manifest bytes。另檢查真正掛載 free。這個規劃守門、64 MiB reserve 與正式測試斷言／時限全部保持。

## 完整剩餘流程：已知必要量與未知上界

順序執行只能減少同時執行的暫存，不能消除已保留原件。每一步須計入先前所有保留增量 R、當步來源／編譯／執行峰值 G、當步完整原流 A，以及最後一次封包與上述發布公式；不可只看下一個命令。各掛載分開核算。下表的缺額是所列入場量的下界，**不是整輪足量保證**。

Q38 320 MiB 與 card 448 MiB 的原來源為 `/workspace/geo337-F9-nonperf-SHM-placement-preparation-20261025/RESOURCE_ESTIMATE.json`（5,285 bytes，SHA256 `b5872fabefeb3ae2c56cc4df928835ab98665a1d0381e11e1a171d995e9b410d`）的 `suggested_incremental_scheduling_allowance_bytes`。browser 416 MiB 與 native 128 MiB 的路徑及原准入來自 `/workspace/geo337-next-round-common-resource-route-20261025/PLAN.json`（13,788 bytes，SHA256 `203901f7ec6fd53f82a7fd377b23bbd1b2a99e419bde409dbfccb51f8eff14e2`）。browser/Q38/card 缺額均相對兩 OWN **規劃**餘額；不是說實體 SHM 少了同樣的 bytes。

| 路徑 | 實際位置、現存規則與已知成本 | 20:35 依賴／狀態 |
|---|---|---|
| native 完整來源轉移＋35 分鐘原流程 | 真正 cache 固定 `/tmp/geometry-tests`；啟動 free 134,217,728 bytes，不能只換 TMPDIR。完整選取 6997 葉；舊 index 保全＋新 index.lock 的轉移暫存與五檔來源另計。估永久增加約 507,904 bytes，不含 refs/logs 與未知 index extension。 | 單啟動已差 **23,076,864 bytes**。完整來源轉移＋收據／發布現有模型也不成立；正式 native **BLOCKED/UNRUN**。 |
| 六 browser 順序執行 | 每組獨立 checkout/index/埠/tmp/profile，完整 canvas 獨占。原單組規劃 436,207,616 bytes，加新的 thin seed；原 64 MiB 物化 reserve 不減。每完成一組保留原流、封包、objects、讀回。 | 連單組也差 **367,558,656 bytes＋seed**；六組累積保留量尚無已驗上界，**BLOCKED/UNRUN**。不把六倍單組量冒充實際最壞峰值。 |
| Q38 全 44 | D4 測試變動進入模型副本 digest，必須補 F 原件。原規劃 43 個保留 ELF、來源副本與編譯 scratch 合為 335,544,320-byte 排程增量；此為估計非產品數字。 | 原排程量短 **266,895,360 bytes**，另有完整交付；**BLOCKED/UNRUN**。 |
| §7 card 全套 | 原 53 mutants／116 retained binaries，469,762,048-byte 規劃增量；實際每 ELF 與 scratch 上界未測。原 mutable source 獨占與還原維持。 | 原規劃短 **401,113,088 bytes**，另有交付；**BLOCKED/UNRUN**。 |
| §7 axiom | 原 11 個順序子程序，間接 H adapter 確實會編譯 C；不能沿用舊規劃「no C build」敘述。完整 codegen→as→link→11 程序→全部原件單次交付的模型見同包整鏈報告。 | assembly/object/ELF/scratch/異常殘件與完整正式 raw 上界未知，**無可證完整最壞成本，BLOCKED/UNRUN**。v3 真 exit 1 在 compiler 前；四個 driver 診斷 0 不代正式通過。 |
| required-eight／PF3／#314 完整專項 | required-eight 仍會寫 `/tmp/geometry-tests`；PF3 原 21 個 C variants；D4 裁判與原 index 保全反證不能省略。 | 既有裁判原件逐項保留；新 F 完整流程／容量未閉合，不把工具合成測試算正式通過。 |
| P52／P-189／whole-memo／replay／RC／Reading A 其他 | 需要原完整 native/CLI 或 browser 來源、編譯產物及各自完整輸出。效能獨占；R8 不重抽。P-189 strict exact 原紅保留，不能自行擴大 #323 三差範圍。 | 依賴未準備好的 F 正式執行路徑，且部分比較批准仍缺原始核實；**未閉合**，沒有以相同產品 bytes 直接豁免。 |

新 F 帳本 check、架構三條、reader 已有有效原件；不重做。影響分析 `IMPACT.md` 與 peer 特別區分選取 Git 集合、實體 checkout 完整性及實際執行，沒有把 6997 metadata 葉數當成完整實體驗證。

## 最小解除選項與明確限制

1. 新增固定 168 葉若獲明確批准，仍需重新核 consumer/identity/hash/dirty 與遠端可恢復性；有變動即跳過。23,707,648 bytes 是 allocated 候選額，非已回收。以此觀測零成本純加總，native 啟動僅多 630,784 bytes；扣上述來源永久估量後剩 122,880 bytes，尚未算 refs/logs、index extension、執行原流及最終發布。因此該批批准不能當整個 native 已可執行，亦不能解除 SHM 規劃。
2. 若不刪其他受保護資料，需明確核准並提供足以承擔整鏈的保留容量；實體 SHM 尚有空間，但原 2 GiB 任務規劃要另有有依據的資源決定，本輪不調整。這不是要求增加付費資源或修改安全／掛載設定。
3. 可核實相同 compiler／C closure 的既有完整峰值與產物紀錄，才可縮小未知量；目前 driver `-###` 沒有這種證據。不得反覆調小新診斷 minimum 或只夠下一 phase 就啟動。
4. 真正已授權且獨立完成的新工作是 gate 影響審查。其他同 SHA 已驗項不再重跑；未明確核實的跨 SHA 或 P-189 比較政策維持待決。既有工作管理入口的私有 ledger 仍 unknown，不能另建空佇列冒操作完成。

結論是上述正式路徑現階段受阻，**不是專案完成或全部產品全綠**。本次只合併報告、既有 v3 失敗原件與下一步，做一次證據與交接發布；不再更新 PR 正文、不為相同觀測新增輪次封包、不刪既存資料。
