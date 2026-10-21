本包保存 L2 `249571fe2477845d5330f6190dad965bf327f43b` 的一次完整 canvas 原件與完成後核對。它是後續 native 突變錨點修正前的歷史結果，不能代替 S3／L3 的全帳本及七項驗收；本輪另外五個 browser 沒有啟動。

原 full 結果為 2261 通過／0 失敗／0 跳過，85 段 golden 完全相同；P52 43、P68 36、P72B 50、P73 69。原 Node、wrapper 的父 wait、launcher 的父 wait、工具 session 真退出均 0。原 2100 秒上限包括 build／啟動／測試／清理，實際 2054.50496491 秒。詳見 [原結果報告](run/報告.md)、[只讀驗證](run/final-verification.json) 與 [獨立覆核](run/independent-review.json)。

`run/` 保存全部本輪 raw、原收據、135 張 PNG、8 個 gcanvas、6 個 CSV、5 份同下載目錄原測試 JSON；JSON 不冒稱 raw 直接宣告的下載。兩張 assembly 硬路徑原圖已原 bytes 捕捉，全部圖與補封檔 mtime 在執行窗內，沒有重生成。`launch/` 保存父命令、永久真碼、原 wrapper／launcher bytes、工具回傳轉錄、初始程序採樣與後補 PPID 樹。第一次採樣空陣列不代表程序已退，後補件明確列出當時程序。

`preparation/` 保存原規劃與實際 L2 來源綁定、native 初建放行小收據、產物與 binary 核對程式。早期規劃的 L2 未知狀態保留原貌；真正 L2 依 `L2-static-ready.json` 及 run 原收據。native 初建小收據只證明放行條件，不證明 native 全驗收。browser 使用主 repo 私有 runtime，三 binary 當輪全 built；沒有預置 native binary 或指向 native global。第一次額外 binary／194 來源採樣在 Node 已開始後，不能稱為 Node 之前；原 runtime-before／after fresh 收據仍在。

保留 P38 一個 expected exception、P53 firstTransportFailure 與 P57–P61 firstNetworkFailure；不能說零例外／零網路失敗。wait trace 未開啟，0 records 不代表 0 次等待。首次服務 readiness probe 1、後續 fresh 0，以及清理 SIGINT -2 都保留。原 releaseNote 的五項續跑計畫後來由 root 撤回，原件不回改。Chromium／Noto 與 native 並行的環境限制照錄，耗時不當 P189 性能證據。

`source-index.json` 逐件列來源絕對路徑、封包相對路徑、長度、SHA-256 與原 mtime。所有原件 bytes 不變，檔案 mode 統一 0644。外部程式以 `.txt` 保存原 bytes；未收 `.py/.js/.cjs` 可執行副本、binary、Chrome profile 或 cache。`SHA256SUMS` 包含全部檔案但排除它自身；包外驗證另存，不回寫凍結子包。
