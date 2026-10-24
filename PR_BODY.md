Workbench HTTP fixture 每次關閉伺服器時，預設0.5秒輪詢造成等待。本變更只把測試fixture的 `serve_forever` 設為 `poll_interval=0.05`；原19項正確性斷言及1200秒時限保留。兩次正式原runner與四次獨立components觀測已全部完成，資料支持時間主要省在server.shutdown等待。

唯一 current-state 矩陣：

| 身份／gate | 目前結果與實際 execution SHA |
|---|---|
| Product／test source S | `2199cda8896b47c7ad2b6c10479e5e0cbdb67c83` |
| 原比較 BASE | `3c6633575ec0f9dccf35898380202aad8d0ffddf` |
| Evidence head | `99646d418bc5e886a92bfdabe33e68780e88fe3b` |
| 原正式19項 | PASS；BASE；原 `run_all.py --build --only test_rule_case_workbench_http`；19/19、0skip、exit0、unittest27.35s；外層wall27.700240s |
| 修正正式19項 | PASS；S；相同原指令／斷言／1200秒；19/19、0skip、exit0、unittest19.65s；外層wall19.923094s |
| 原components19項 | PASS；BASE；原exit0、26.47s；19個shutdown inclusive wall總和7.046116s |
| 修正components19項 | PASS；S；原exit0、19.48s；19個shutdown總和0.604546s |
| 撤回components19項 | PASS；實體S、明列記憶體測試variant逐byte等BASE；原exit0、26.13s；19個shutdown總和7.646091s |
| 恢復components19項 | PASS；S、執行測試bytes等修正版；原exit0、19.08s；19個shutdown總和0.726671s |
| source／cache／共享log | PASS；各原source前後clean／index不變，最終還原S；bridge與sidecar前後hash／inode／mtime相同，三舊rowlogs逐bytes還原 |
| 突變帳本／架構 | 本S未重產；由root最終union按完整來源一次處理，不冒舊SHA收據 |
| 完整native／六browser／required CI | 本收據未證明通過；非這兩次selected19或四次觀測可替代 |
| 允許skip／合併狀態 | 本六階段不允許skip，實際全0；尚無本PR的【ChatGPT 審查】，NOT READY-TO-MERGE |

正式runner關閉觀測；components另跑原測試並保留原watchdog。六次正確性皆0：撤回輪詢修正只增加等待，這是時間上的撤回／恢復自證，不能宣稱殺死正確性突變。沒有新增數值門檻、挑綠重跑或多樣本統計保證。正式單次27.35→19.65s之外，四組shutdown process CPU各約0.001s，符合等待而非運算時間；全部component原事件均保留。

component時間是inclusive span，tearDown、server_close與adapter.close存在巢狀呼叫，不能相加成不重疊總時間。process CPU不含native child CPU；watchdog的RUSAGE_CHILDREN差值是所有已等待子程序合計，不能冒稱獨立native-only時間。

完整原件在 `evidence/geo345-final-2199cda8/`。六phase actual＋分析獨審2493／0，核147原命令的完整輸出與hash。原run_process只暴露解碼後合併文字，已完整保存其暴露內容，未補造不存在的兩條inner raw pipe；外層與其餘原工具的stdout/stderr仍分開封存。原global ELF不另複製，保前後hash與sidecar原件，不聲稱包內有ELF payload。

僅測試fixture輪詢設定變更；沒有產品、公理、golden、斷言或時限改動。不force push、不合併PR。舊準備文件只作歷史，以上矩陣是唯一目前狀態。
