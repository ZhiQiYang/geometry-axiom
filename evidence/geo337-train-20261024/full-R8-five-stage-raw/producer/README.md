# R8 終態摘要與完整原件 collector

小摘要已於獨立靜審 35/0 後真執行，producer／outer exit 0；`/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json` 為 31716 bytes，SHA256 `23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd`。這是投影工具成功，原產品五階段 outer exit 仍 1。完整 membership freeze 與 collector 尚未執行，須等 root 確認容量後另啟動。

來源固定 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`；原始 OUT `/tmp/g337323R8`，stage tools `/tmp/geo323-final-r8-stage-tools-20261024`，執行工具 session62076。只由已審 R7 producer 做必要參數調整，不執行產品、不讀取仍活動的 raw OUT、不重抽樣本。

原 175 scenes／350 runs／36 交錯樣本／4 profiles、五個 own-stage exit 與五個累積 CLI exit、outer exit 分開保存。三項既有 exact 差只依本輪原結果記錄，不預寫其數目或修正裁判；ABC_result 若缺席就保持缺席，full_acceptance/null 與 all_required/false 原樣保存，不補造通過。

collector 沿原單一 archive36MiB／metadata4MiB／native reserve128MiB；168MiB 入場門檻沒有放寬。七個原 ELF 只保存 SHA，原 payload 留在既有路徑。original stdin/stdout/stderr/request/environment/source 及 byte roundtrip 守門不改。

R8 API 物件取原 `EXEC_TOOL_INITIAL.json` 及已提供 `EXEC_TOOL_*.json`，所有 running 物件綁 session62076，且必須有唯一原 terminal object 並與 outer exit 相符。沒有硬寫未來 chunk_id 或重建工具輸出，也不宣稱中間 API 回應序列完整。

舊 R7/F7 的 ledger 收據不混入本輪 current scope。尚無本輪 ledger 或 source preparation 獨審附件，因此只收入已存在的 R8 工具靜審；其他正式結果另由主代理追蹤。歷史 R7 collector 原工具作 provenance 保留原標籤。

執行順序（第 1 步已完成；後兩步須由 root 在 peer 審過且核實容量後啟動）：

1. `python3 -B summarize_terminal.py`：全部原五階段、outer 真終態才產小摘要 `/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json`。
2. `python3 -B freeze_terminal_plan.py`：固定當下原始 membership、terminal pins、API 原物件；缺件就明確失敗，不造替代。
3. `python3 -B launch.py`：原兩個非阻塞 heavy slot 擇一，一次收包到 `/tmp/geo323-r8-full-package-20261025/`，保留所有原始檔。

本目錄保留外稿、差異與小摘要執行原流。沒有 PLAN.json、collect.py、launch.py、PACKAGE 或自行創造的正式判決，也沒有自行推分支。`PROVENANCE.json` 的 executed=false 是準備當時記錄，實際後續以 `summary-launch/RESULT.json` 為準。
