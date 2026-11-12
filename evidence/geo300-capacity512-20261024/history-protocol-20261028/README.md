# I8a history 協定修復

產品仍為 b595e55952d5d66de95024432e1b29bec7525e9b；執行時親提交 b872264006f400d600c801fe8c096d5679ad9013 加此提交同 bytes 的測試檔（SHA256 a6b503157d857ddcd517aecbad97c8b9a295900167372a250baaa135ab44d507）。未把 dirty 執行移標成新 clean SHA。

命令 `python3 -B /dev/shm/pr348-history-protocol-check-v2.py`，outer exit0。真7支場景 baseline0、撤回 confirm→dump 後1（placed-delete-confirm-must-commit）、restored0；各1 test，無error/skip。取消只證零變更／新token，不宣稱本小例額外獨立驗證舊token已撤銷。前一留證版本未複製loadfile原fixture，原資料保留於initial-receipt；修觀測器後complete-fixtures保存每輪實際原fixture及三流。沒有改產品或斷言取綠。

fake child控制只證新整批deadline／大量stderr不死鎖／非零退出與callback錯誤可回收，不能作產品綠。正式整批600秒保持不變，不是每條命令重算600。

原512 history紅保留在 b8722640 的formal-f2-b595e559；此修復後512長方法尚未跑。新的v4 observer另攔dynamic dialogue，將真token命令／原stdout／stderr／wait4 usage保存；不由JSON重序列化冒原流。

持久文字checkpoint計畫由1MiB改512KiB是本任務工具規劃，依前輪兩受影響批合計328591bytes＋建置/結尾約31KB估算並留餘裕；產品600秒、原64MiB發布reserve、實體/tmp檢查與512支fixture不變。每批仍在寫前驗實際剩餘bytes，失敗不標過。

全H7原1200秒／native35分鐘預算仍未閉合。帳本仍過期；完整census更新expected、架構與整合驗收待最終穩定來源，維持Draft。
