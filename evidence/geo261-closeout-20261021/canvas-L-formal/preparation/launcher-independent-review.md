# Canvas 父啟動器唯讀審查

定版 `launch_canvas_job.py` SHA-256 `4f7935f1c516d118c06272a5ed96c4c5909cdbe124a4e746870b0001ce490181`，唯讀審查無阻擋。stdout/stderr 從 Popen 開始直寫 orchestrator 檔案；父程序對自己建立的直接子 wrapper `wait()`，第一個收尾動作即寫 `.exit-code`，後續來源雜湊或 JSON 收尾失敗也不會遺失已寫出的原碼。

子程序使用 DEVNULL stdin、獨立 session；父程序忽略 SIGHUP，INT/TERM 僅轉交尚未回收的直接子 wrapper。沒有對其他程序名稱或 PID 集合發訊號。launcher 與 wrapper 的原 bytes 都有另存，完整 SHA、明示執行、放行說明及不得覆寫守門保留。

已讀 `launcher-controls/results.json` 與程式：假子程序 0、7、TERM 三例原碼分別是 0／7／-15，與落盤收據一致；這些控制沒有跑 build、服務或 browser。TERM 例因 Python `sys.exit(-15)`，父 launcher 的實際外層碼為 241；這與觀察到的子 wrapper -15 是不同層級，已由控制分列，不能混稱產品斷言失敗。

本次只讀審查，未重啟在跑的 A preflight，也未啟動 L。若父啟動器遭 SIGKILL 或環境中斷而沒有 `.exit-code`，仍須回報未知；不能依任一產品 `passed` JSON 推造已觀察到的 outer 0。
