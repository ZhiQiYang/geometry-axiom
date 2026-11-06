Python r2 唯讀核對完成：三階段原 COMMAND_RESULT、stdout／stderr、TEST_RESULT 與來源雜湊一致，每階段32項工具檢查，結果為 **0 → 1 → 0**。withdrawn 僅撤除實際 stdin 行長檢查，唯一紅項為 `reject-wrong-command-line-length`；fixed／restored 的三份 Python 來源逐 byte 等於現行版本。

本次只讀原件並保存本審查，沒有重跑自證、編譯 C、啟動產品或更改既有 REVIEW、Python、C。完整來源、proof driver、r2 RESULT、三份 COMMAND_RESULT／stdout／stderr／TEST_RESULT 及各階段來源 pin 均列於 PYTHON_R2_REVIEW.json。

已核修正：close 的 OSError 不替換原 TimeoutExpired，並標 observation invalid；fixture 固定為 `760a7169…`／45,154 bytes；parser 拒絕不合法 flush-enter rc 與負 flags；非零 CompletedProcess 保留原結果，僅接受其已記錄的邊界前綴。

這32項使用注入的假 runner 與合成事件，驗證 Python 工具規則及原結果／原串流留存。它們沒有驗證 C wrapper、真實 pipe 的分段到達或大量 stderr 壓力，也沒有實測 subprocess kill/reap。C 尚未編譯、link 或校準；N512 尚未執行，不能宣稱正式 gate、產品撤回反證或根因已通過。

README 的低度文字建議已由作者收斂：明列真實 pipe／kill-reap 未驗、PLAN 第5項尚未完整完成，並保留 full123 後由 root 排程獨占時槽。最終 README SHA256：`0b6e49e83028d762f1da198acb4a2d74637971edea9ec42363593ecd0a6e035b`；沒有未解文字問題。

r2 RESULT SHA256：`242deb4a1d1c59cb7f4f4a2d34a94b4dabb311bc10944deb5840aa49abdc068d`。本結論只適用 JSON 明列的原件 pin；peer 沒有獨立執行這些測試。
