# 8b128aa7 完整 H7 原1200秒逾時（未通過）

固定候選 `8b128aa7bf53b41b493dd3a0bee49f0d53391254`，正式PR產品仍F2/C，沒有採入。完整原八方法於2026-10-29 00:12:43Z開始，00:32:43Z由原run_all.run_process/kill_tree結束：1200.016299009秒、timed_out=true、child exit=null；外層腳本按原條件exit1。不是每batch600秒超時，不是全綠。

完整命令、stack16MiB、source、環境/資源、build-log、原ELF、全部已取得stdin/stdout/stderr/fixture、每批wait4時間/記憶體、原unittest與outerlog均在RAW。7個方法已印ok，第8個64/512 canonical方法未收結尾，沒有整套tests總結。最後batch008只有原始stdin/fixture/binary身分，因整套期限中止；沒有原stdout收回，不能冒成通過。所有原件不刪。

| batch | 真結果 |
|---|---|
| 000 | 小history0，0.152284秒 |
| 001 | 512 load0，256.109963763秒 |
| 002 | 512 sequential＋I8a實際token確認＋history＋513 CAPACITY等原斷言過，273.936417312秒 |
| 003/004/005 | 64 load與兩次fresh canonical皆0，0.947009／1.044994／1.015368秒 |
| 006 | 512 load0，251.966908094秒 |
| 007 | 第一次512 canonical0，285.428571146秒 |
| 008 | 第二次512 canonical未完成；不重抽樣洗掉原紅 |

逐批原件已在獨立receipts branch逐次一般push及GitHub實際blob讀回，末完成checkpoint `fde57aa157f4bc7ce9087bdeff19e71bedc01c6d`。本包一次收齊終態與未完008；先前每batch證據不改標。

一次N128 aggregate診斷：原版8b現成輸出不重抽樣，插裝執行exit0。50,382次查詢中16,796原memo命中；33,451次exclude不同，其中24,548次其餘完整facts/axis/placement/cap/id/placed相同。僅移除唯一具名前綴的診斷行後stdout/stderr逐byte等於既有8b原件，所有統計恆等式過。這只是快取候選可命中證明，不是效能樣本或新幾何判決。初輪工具未呼叫b.bridge()便link，沒有產品binary/execution；原工具及準備產物保留，前tool session失聯所以該次exit unknown，不捏造退出碼。

獨立生命週期靜態複核：407個clear含reset/destroy，完整world validation只有138次，不能刪除必要逐次World重驗。後續只依實際512 profile找純維護熱點；不改600/1200/35分鐘、I33、原斷言、SSOT。

完整native、ledger重產/census、architecture、browser與上游343→346→347鏈仍未完成，維持draft。
