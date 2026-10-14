# P064兩個獨立普通捨棄邊界

17731486完整native：2752/1/1、actual exit1、917.190秒。唯一超時為舊P064普通捨棄一題同跑130956與131072兩個新fixture，耗時5783.968ms、test timed out after5000ms。新的live-ref B1（2108.663ms）與拆分後孤兒邊界兩題（3155.719／4238.064ms）通過；其他suite無fail。

P064依同一原則拆成兩個具名用例；每份仍完整跑新接納拒絕、先存other再存大份、捨棄other、raw/shape、真ZIP冷讀、局部UndoRedo。內層body逐byte相同，timeout5000字面未改，沒有增加sleep、改產品或刪斷言；Node702→703只因原1題拆2題。原收據保留，不拼接前兩輪部分綠；最終固定source需完整native再驗。
