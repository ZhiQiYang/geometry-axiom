# #314 v2 準備工具獨立窄靜審

接受目前凍結 v2 作為待執行工具；未發現可確立的準備阻擋。v1 的「原 mutation CLI 0 可能包含 crashed」假綠缺口已以獨立 proofAccepted 修正，保留原 CLI 真碼。現在要求精確 M99–M121、原 S3b、逐位元組還原、build 0、22 個正常具名斷言 0/1/0；M110 明確等價 0/0/0，不冒突變擊殺。M121 正反兩方法與唯一負例一致。

原六 native suites 合 103 僅為 partial；OUT_DIR 綁定先於 run_all import，故 LOG_DIR import-time cache 及呼叫時計算的 binary/sidecar 路徑均指專有目錄。Node inspector 使用真 bridge 加 VM，不能替代 P72B 真 HTTP/Chrome；後者明列未跑，原可用入口是 COMPOSITION_ONLY 的 P72 52＋P72B 50，保 partial/golden 不比較。

僅讀取、AST 與小檔 hash，未 import 或執行任何 driver、產品、測試、編譯或 Chrome。固定產品來源 3b0b634feb54266700cc61f26c34d7aeac4c0314，未驗新 forward stack。動態時仍須原 streams、binary freshness、終態 SHA、真 counts/退出與完整還原收據。精確六檔 hash 及界線見 FINAL_V2_CHECKS.json。
