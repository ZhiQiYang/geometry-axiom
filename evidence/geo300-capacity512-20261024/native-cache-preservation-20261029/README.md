# 原生快取可逆保全，未執行 native

原 /tmp/geometry-tests 28直接檔與run_all-logs9檔，共5,785,357 bytes，copy2後逐檔核mode／size／SHA與來源前後一致。原資料沒有刪除或覆寫；沒有遞迴收集mutants或其他快取。保留工具與完整manifest／consumer觀測。可讀程序未見consumer，兩原鎖以唯讀非阻塞方式取得後釋放；PID125/176無權讀取欄位仍unknown，不能宣稱全系統可見。這不是native驗收，也未將任何ELF命名為F9；後續正常build前仍須fresh核使用狀態。
