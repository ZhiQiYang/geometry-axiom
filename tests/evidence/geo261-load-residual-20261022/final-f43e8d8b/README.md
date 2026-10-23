# #323 固定最終來源的完整雲端收據

正式受驗來源 F：`f43e8d8b876f587c11778fa74a80b205b51396b6`。
`FORMAL_RECEIPT.json` 保留各原 stage 退出、來源前後、量測目標與封裝退出碼；`FORMAL_METRICS.json` 只整理原資料，不代替裁判。
N64 fix/main **1.7457212386，未達原 1.3 目標**；source calls 64/32 **4.4704196928，達到原 ≤4.5**，三個小 N/base 亦達原不變慢目標。沒有放寬門檻或重抽。完整測試結果以原收據與 metrics 為準，不能將性能未達標寫成全驗收通過。

封包含原 175 場景 A/B/C、完整 ordered graphs、逐場景五 guard 總數、36 原計時、四原 profile/gprof/gmon、required-eight／完整 PF3／完整 native 的 argv、退出碼、環境、SHA 與完整 stdout/stderr；另有同 F 的三條原架構裁判。每個封包成員已解包核對 path／bytes／SHA-256。
原 Git archive stdout tar 原樣保留。可重建 checkout 與 ELF 未當作原始收據複製，排除項另列 metadata/hash。

`ledger-audit/` 是前一輪真 S=b823903e 的整份帳本稽核，與本輪 F 的正式驗收分欄。原工具未保存 core 內層各 attempt/compiler streams；完整 top-level 命令輸出、結構化結果與原 stream hashes 仍保留。75 mutant C 明標重建且逐一符合原編譯指紋，不能冒稱原捕獲。

本目錄只封存原結果，未重跑產品或改寫判準。產品／測試 P、帳本實跑 S／產物 L、架構實跑 L／產物 A=F、後續證據保存 E 的完整角色，見 PR 正文。
