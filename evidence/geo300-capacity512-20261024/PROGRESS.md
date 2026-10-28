# #348 阻擋 2：修復中，未達合併條件

本輪基底 B `9a8584f57be7935604c3bad4c2481945a6ec3d9f`。最新修補來源 C `3420931a4a512f08e3f4d7584958cc8630e190c3`；原逾時、環境錯誤與每版診斷均收在 timeout-diagnosis-20261028/RAW.tar.gz，MANIFEST.json 逐檔 hash／byte 回讀相符。

- **原 B 真實 placed load：600.013933527 秒，exit -9、timeout=true**；wait4 RSS 279492 KiB，stdout/stderr 均空。原 600 秒未變。兩份歷史 timeout 都停在 initial load，canonical replay／sequential history 尚未到達，不能冒稱已各自測出逾時。
- B N128 原 O0 分離 K/W/H 的 gprof：14.914535 秒，exit 0。anchor memo 版 `42e573f59f19693d03f2f4a64bc76a5575b45690` 同 N128 14.166502 秒、N256 127.336561 秒，exit 0；N128 stdout 與 B 逐 byte 相同。這些是診斷，**不是正式 512 通過**。profile 的 child_maxrss 欄包含 compiler 累積，不能當產品峰值；詳 DIAGNOSTIC_LIMITS.json。
- C 新的 scope-local anchor 與借用 host 測試：6 項、0 fail/error/skip，exit 0；六個獨立撤回各有具名 0/1/0。借用 host 的性能尚未測量；K source index／W contact 重複工作繼續修復。
- 正式兩個 H7 placed/replay/history 方法、最終 ordered graph 比較、完整 native/browser、帳本與架構：**尚未完成**。I33 CAPACITY 拒絕與原 timeout 均不放寬。
- 上游仍阻擋：審查時相對 base behind 2；目前 #347 `8bb0359331365c6f3a96872620427cf7847fcb50` 為 behind 3/ahead 8（新增一個 evidence-only 提交）。#343→#346→#347 尚未閉合；未以 evidence-only 差異冒稱上游驗收已閉合。鏈修復後才一般 merge 精確 head，逐 leaf 重審及重跑受影響項。

下一步：修復大量重複資料複製、接觸面順序與 source 索引工作，固定新 SHA，原方法 600 秒內驗證 placed load／canonical replay／sequential history，保留所有紅燈。原 F0f/F73 歷史證據未移標或刪除。
