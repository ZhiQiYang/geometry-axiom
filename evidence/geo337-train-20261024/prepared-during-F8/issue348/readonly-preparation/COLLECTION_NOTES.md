本次只讀來源與收據。初輪誤用主 repository 查 F0f 的 tests tree，Git 明確回「path ... does not exist」；該失敗保留在 git/001 與 collect_static.initial-root-lookup.py.txt。改由原正式來源自己的 /workspace/geo348-F0f695866-source Git repository 讀取，12 檔全與實體原來源逐 byte 相等；15 個成功 Git 原流保留在 git-r2。沒有 fetch、補造 tree、修改 Git objects 或原收據。

FACTS 的 F0f→F73/F8 差異僅限明列的12個選定路徑，並非整個 commit 全部 diff。靜態原始碼、fixture、stdout 等副本均保留原 bytes，未重跑產品或 generator。PLAN 的獨立審查指出兩項敘述精確度問題：EOF/error 要分清、contact collection 不涵蓋未放置或前置失敗成員；已收斂文字，FACTS 不變。
