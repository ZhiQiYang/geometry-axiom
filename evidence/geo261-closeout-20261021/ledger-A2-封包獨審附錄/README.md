# A2 帳本封包最後有限獨審附錄

本附錄只收 architecture_receipt 最後有限封包審查的實存五份原件；不改 ledger-A2-cc 凍結子包或其 SHA256SUMS。定版接受器真 exit 0，工具 chunk44d811；它核 2253 原件、2258 檔、32,239,179 bytes、根與巢狀 SUMS exact set/hash，以及 UTF8／0644／無可執行檔。亦核方法補充中的 M36 歷史語料、本輪 165 題及核心 raw 缺口界線。

首次接受器把啟動時的 initial null observation 誤當最終工具回覆，並以扁平 exit_code 欄位存取，得到 KeyError。真工具 chunk42a589、exit 1、錯誤摘要與完整首版接受器仍保留；沒有修改帳本或重跑產品。

首次執行沒有另外保存 stdout/stderr，完整工具輸出也未另存。現存 observation 只有真碼、工具 chunk 及錯誤摘要，不能稱為完整 stderr、完整合併輸出或 raw transport；亦不從摘要補造 traceback。定版工具 observation 保完整實際回覆的事後轉錄，仍明示不是 raw transport，也沒有重新 wait。

未複製 .py 可執行副本，兩版方法以原 bytes 的 .txt 保存。根原件清單只列五份原件，SHA256SUMS 精確涵蓋除自己以外的全部檔案；整理方法與最終copy/hash收據另放總根，避免自含循環。
