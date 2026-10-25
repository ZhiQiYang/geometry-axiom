# H 區域初始化修正進度

受測產品／測試來源為 `2c4635577a8fcb11e88b346547f7bb1c7b739fb7`，父來源為 `6df0264f75e84f03adb70746b6ac3db07a9910fc`。證據提交只新增本目錄，不把受測 SHA 移標為後續證據提交。

- 原 `tests/test_geo261_load_residual.py` 完整 14 項於該來源 exit 0，14/14 通過、零 skip；原 13 項保留，新增 1 項初始化分支／工作量案例。
- 固定／完整撤回／恢復三階段的語意案例都通過。Linux 連結器包裝實際 `memset` 的 persistent 工作量為 0／2／0 calls，0／255168／0 bytes，工作門檻 exit 0／1／0；撤回精確 assertion 為 `persistent-reference-local-zero-work`。
- 原始命令、環境、stdin/stdout/stderr、來源與編譯輸入、退出碼與 SHA 一次封存。ELF 只保留原執行時雜湊，不能聲稱原 ELF payload 已封存。
- 此為 O0 focused 反證。未另外執行準備好的 O2 disassembly 工具，也未重抽正式效能樣本。R7 的 N16/base=1.05190582882169 與三項跨版本 exact mismatch 仍是紅燈。
- 主代理接續正常 merge、架構收據重產、固定新 final SHA 跑 R8 與整列車正式驗收；本支線沒有重產全帳本，未執行完整 native、六項 browser 或其餘正式專項。

本切片不是 READY-TO-MERGE；完整列車狀態以 #338 的唯一 current-state 矩陣為準。
