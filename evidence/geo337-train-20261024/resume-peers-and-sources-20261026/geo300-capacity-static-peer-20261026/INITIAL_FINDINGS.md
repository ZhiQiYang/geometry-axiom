# #300／#348 靜態報告初稿對抗審查

此初稿紀錄保持不變，後續修訂以 FINAL REVIEW 為準。沒有執行 Git、API、原 generator、編譯或產品測試；只有 local capture 的 hash、AST literal 與記憶體 byte 比對。

受審原稿：`REPORT.md` SHA256 `023edfe7880a4d4efc86d5c349c11ed4801cce3f9a87e9ff22601efaf7cd40d1`；`ANALYSIS.json` SHA256 `78cebe39dbe33146a6b8e99893b02bb5c45ab03d98239b9581a3f4b2443c80de`。

已獨立確認：112 份 manifest 原件與 33 組完整 capture streams 相符；候選 F `cbf0fb621888596aa14ad5f2349b503e23b1b72d` 的兩個 C 檔，使用同 F 測試內四組 literal 撤回片段後，逐 bytes 等於 #348 head `9a8584f57be7935604c3bad4c2481945a6ec3d9f` 的固定 raw API 原件。略去任一組撤回即不相等。這只證明兩檔差分，不證明整個分支、產品行為或效能。

兩處需精確澄清：

1. 原觀測器已有例外 `stdout`／`stderr` 經 `retain` 保存的路徑；`captured:false` 對應當時傳入 `None`。原件沒有可用 partial bytes，可據此說無法分辨四命令的最後完成位置；不能推成觀測器根本沒有實作 partial capture，也沒有依據再造同樣工具。
2. 1048 命令是當前 #348 head 的 sequential AST 建構值，其 suffix 21 項。封存 F0f 的 suffix 是19項（同1026 DSL假設下為1046），不得把1048移標成當時真正執行。兩份 H7 79／83 實際輸入都僅是140 bytes 的同一四命令 preload。

主代理已請作者保留初稿並定點澄清。原紅燈仍保留；不歸因 `loadfile`，不宣告 512 可施工、效能通過、history 已執行或 READY-TO-MERGE。
