# H死工／K查找候選與原有序圖

固定候選 `8b128aa7bf53b41b493dd3a0bee49f0d53391254` 已推 codex/geo300-consumer-scope-20261028，正式PR348仍F2/C，未採入。

H只把來源成功路徑不讀的raw footprint建置延後到fallback；端面仍先span-extension再原resolver，不改callback、幾何與錯誤優先順序。K以完整hash選原256槽hint，miss重用同hash；完整identity、原有序陣列、失敗fallback均保留。

| 實跑來源 | 原結果 |
|---|---|
| 887c3fab4b53e9acf4792b033979bf8992a49204 | 51項50過1敗：新fallback fixture預期4但raw fixed0側面被outline完整遮蓋，實際3；其他原42項與兩個H撤回均過，原紅保留 |
| 9ac98f162db44a37c12eb3a95065e9632e6d24fc | 120項119過1敗：新hash撤回的短anchor撞兩處，未啟動mutant，不能算killed；H9、原K29/slot6/scope17與其餘原回歸通過 |
| 8b128aa7bf53b41b493dd3a0bee49f0d53391254 | 只修測試anchor為node_index_capacity完整行；新hint7項exit0，三個不同具名撤回0/1/0。相對9ac產品與其他tests bytes不變 |

沒有刪或放寬原斷言；H fixture僅訂正原生遮蔽後的具體數量，逐面與原eager版本比較保留。各命令、原stdout/stderr、build與退出碼皆在RAW REQUEST/RESULT。

8b同源172場景plain/trace共344新子程序全過，00:09:06Z開始build，build8.690099秒/exit0，comparison47.002993秒/exit0；沿固定E18原B9a收據逐檔closure核對，不重跑B、不移標。完整ordered graph、五guards、allseals與stdout/stderr全等。這是原O0單翻譯單元圖裁判，正式H7仍分離K/W/H建置。

一次N128診斷：3949原ELF 5.134406秒、8b候選4.933180秒，兩份原流全等；只約3.9%改善，不當正式512或H7證據。上一輪3949的真512 load261.840563秒保留在獨立scope-load-3949deb9，不能改標8b。

完整H7 1200秒/每batch600、全census/expected、ledger、architecture、native/browser與上游鏈尚未完成；維持draft。下一步只在此固定source跑原H7，不縮短案例或放寬時限。
