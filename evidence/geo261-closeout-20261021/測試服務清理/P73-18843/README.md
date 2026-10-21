# P73 測試服務 18843 清理證據

這是正式 P73 驗收後保留 idle 的自有測試服務清理，與已凍結的 P73 驗收包分開保存。本包不宣稱正式 L canvas 或其他產品驗收完成。

- 清理時分支 codex/geo261-closeout-20261021，HEAD cd4ac98f44174729fb3a2f1c291c6c258c9a239a；此為未採用帳本 L1，不能冒稱最終 L。服務則是產品 A 7159530c0e494d3211e6ab1764eb691137211707 的原正式 P73 服務。
- 原服務 PID 138215、startTime 617363、完整命令 python3 -u /workspace/geometry-axiom/geometry-web/serve.py 18843；原 runtime session 7d1ecfaadb2440858d9a51c788c27b12、root、version 與正式 P73 原收據完全相符。唯一 bridge 子程序 PID 138222、startTime 617430、PPID 138215。
- 清理前無既有 TCP 連線，世界為 P73 最後測試場景（revision 66，含 space 990）；dump、objects、references、場景文字及原 server log 均先備份。
- 只透過 pidfd 向已核對 PID/startTime 的 138215 發一次 SIGINT。原 finally 結束自有 bridge；沒有發 TERM／KILL，沒有使用 killall，沒有清理其他服務。兩程序的 /proc 均消失、survivors 為空、18843 connect_ex=111（ECONNREFUSED）、ss 無 listener。
- **清理操作實際 exit 0；服務的 serviceWaitReturncode 保持 null。** 原服務不是清理程序的直接子程序，因此未取得其 wait() 回傳碼；不能把操作 0 或 passed 推成服務退出碼。操作退出觀察.json 是工具真 exit 0 的事後轉錄，明示原回覆 chunk，不冒充原生 exit-code 檔。
- 初讀 /proc/PID/cwd 受沙箱限制回 PermissionError／exit 1；沒有升權，後續以可讀程序資料、原隨機 runtime session 與測試世界交叉核實。這項限制沒有隱去。
- 沒有刪除 feedback、profile、cache、使用者檔案或原驗收證據；沒有修改產品、測試、wrapper、launcher、CI 或主樹。

原清理命令 bytes 保存在 command-code.txt，作為歷史操作記錄，不是新增產品工具，也不是可以在新程序上盲目重跑的通用清理器。原 stdout/stderr 在 operation-raw.log；receipt 另保留實際前後程序及 port 狀態。每個原件逐 bytes 複製並列於來源清單.json，封裝可用 sha256sum -c SHA256SUMS 驗證。

本次沒有產品測試或突變自證；未能觀察的項目是原服務的 wait 回傳碼，而不是其是否仍存活。正式 L 仍等待正確來源 SHA 與父代理放行。
