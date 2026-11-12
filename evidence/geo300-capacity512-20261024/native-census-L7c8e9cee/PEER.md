# #348 census 原件與範圍對抗核收

唯讀核收 `/tmp/pr348-census-L7c8e9cee-text-20261029`；沒有重跑測試、修改原件或採入 expected。

- execution L：`7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5`。21 個 manifest 列檔的 bytes／mode／SHA256 全符；兩個 tar 的 9＋329 成員逐份核 hash／size／mode，全符。
- PROCESS、RESULT、SUMMARY、LAUNCHER 一致：原 2100 秒守門，實際程序 -9、recorder exit 124、耗時 2100.075953891 秒，清理完成。此輪 census／native **未通過**。
- expected 前後逐 byte 相同，SHA256 `e88f97a2c13e4ab561c071855ebf68f58bef5cec5d05ba20f453d58a23cf4209`，沒有可採入更新。帳本前後 hash 相同是原收據觀察，未重跑 check。
- 102 份 fresh Python JSON 都與原 tar bytes／mtime／來源 suite 對上，重算 **1523 passed／0 failed／1 原 Windows GDI skip**。這是 Python 小計，未混四項非 Python 或未完成 H7，不能當全套總數。
- 最後只開始 [107/243] H7；原 log 恰七個點，無完整 JSON，不能標八項通過。後續 **136 套未開始**。
- 10.199 秒重疊由 SCHEDULING-NOTE 的父代理起訖時間重算一致；本封包沒有該 browser 的獨立原收據，故仍標**父代理回報**。H7 /proc 起始亦為當時記錄，不能冒稱本次獨立觀察。據該時間，H7 前已耗 1103.058453 秒、守門剩 996.941547 秒；本輪不是獨占效能樣本，不能把 timeout 全歸給這段重疊。

結論：可發布本輪失敗原件與限定範圍；未發現原件／小計／未跑項的誤標。不得宣告完整 native、expected census 或此輪八項 H7 綠。
