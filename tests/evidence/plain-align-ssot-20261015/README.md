# 指定任務 14：早期白話候選與逐行限制原件

以下保留 P-112 前的停手狀態；P-112 已明確解釋生成資料的例外。
新的正典與完整雲端驗證見 [p112/README.md](p112/README.md)，不回寫早期收據。

基底 main：79412a858f712981fa0ba15a6b293c3e0bf06f21。
只修 S2／D1、S3／I10、S4／R45、S5／I53，以及 S8／Q38 檔頭。
scope-proof 核对四個白話條目及全部 204 條正式 body 不變；
含 🔒 的 D15、R6、R8、R12 clause 物件逐字全等，白話本身沒有 🔒 行變動。

同步器曾對候選正典原位 sync、--check，兩次 actual exit0，五道 assert、
independent SSOT、204 clauses／851 blocks 通過。這些日誌屬於候選，
**不能當目前提交正典的通過收據**：同步會替換兩行含 🔒 的整包序列化資料，
因此依看板「任何含 🔒 的行都不得改動；改到 🔒 行就停手回報」還原正典。
生成的候選 diff 留在 /tmp/plain-align-reader-proposed.diff，未存第二份閱讀器。

已向使用者請求兩行生成資料的明確例外，前提是全部鎖定條文逐字不變。
在收到回答前，不提交候選正典，不繼續依賴其更新的原41題／native，保持draft。
這些檢查均未驗，不把局部同步日誌當完整功能交付。

SSOT、BACKLOG、決策、C、run_all／expected、突變帳本與基底逐字相同。
S1／S6／S7／S9 不在本任務，未動；沒有新增可執行測試。
GEO-219：無新入口。mutate 無新覆蓋。未跑WSL。
