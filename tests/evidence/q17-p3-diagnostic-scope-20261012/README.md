# #188 P3 診斷的推論界線

本文件回應 [dot 6116283738](https://github.com/ZhiQiYang/geometry-axiom/pull/188#issuecomment-6116283738)。產品與原裁判來源仍為 `d856b65e0d056b213df435d673a3e6515ba85298`；本次只有文件及唯讀原件核對，沒有重跑 Chrome、native、Q17 五測、mutant 或正式七 job。

[原 ZIP 首段](https://github.com/ZhiQiYang/geometry-axiom/pull/188#issuecomment-6116174776) 及兩段 base64 原文保留。ZIP 33653 bytes，SHA-256 `d60f390e02153049812dce492c1e432e72d7f1e9c759f1bd9e29e241ce1a4d94`；26 payload＋manifest 不改寫，其中 README 舊推論由本文件與更正後的作者回覆限縮。

- 第二次 pointerdown 的 raw target 是 `DIV#`，沒有 class、DOM 路徑或 `closest` 結果。撤回「第二擊落在新 inspector」的精確定位；目前只稱未具名 DIV。
- `eligible:true` 只記錄 `canvasCardClickEligible` 在觀測時的結果，不能等同排除捕捉 handler 的全部守門。current context、first viewport、inRegion、物件存續及執行時狀態並未完整記錄；同座標與已記錄選取也不能補成所有 guard 的完整證明。
- 原診斷加入事件觀測，觀測本身也有計時成本。42.9／2020.8／33.6ms 是 trace 的第二 pointerdown 觀測時間減產品 first.time，不宣稱就是未觀測產品 handler 的精確執行時間。CPU20 超過 450ms 的受控反例可採，但不足判定 WSL 歷史唯一根因，也不解除原 canvas 紅燈。
- CPU20 輪走到後續 trace，支持該正常流程完成 rate1 設定；driver 沒有 try/finally 故障復原保證。restored 輪使用另一個新 Chrome PID/profile，不能稱作同一 Chrome 故障恢復驗證。
- 原入口仍有 `if(card20)` 的可能漏測邊界；本次三輪確有 card20，並執行原 focus／workspace 兩個斷言，不能据此覆蓋缺卡片案例。沒有改這個入口或原斷言。
- 新 PID/profile 可核，但封包服務啟停、foreign census 與清理原件不足。當輪工作紀錄不等於封包交付，不能回填完整隔離、WSL 排他、flaky 或 main 同案豁免。

已核範圍仍為 original Setup→9f→P3-1 的局部診斷，保留四次逐一 await 的 CDP mouse events、1382×804 及原卡片座標。natural36/0 exit0→CPU20 34/2 exit1→另 fresh restored36/0 exit0，兩紅是原 focus face20 與 workspace 開啟斷言；沒有驗後續 P3、完整 canvas 或 golden。既有 450ms 判準未改，不把它放寬成通過。

`audit.py --zip <還原的原ZIP>` 只核全部 26 payload hash、三份既有退出碼、stdout／trace 同一性、已記錄 target／eligible 與間隔、新 PID/profile 差異。audit exit0 只證明原件和上述有限讀值核符，不是新的 browser guard 或產品驗收。stdout／stderr 與直接 subprocess.run receipt 附於本目錄。

首次唯讀 audit 把原件中的 `previous:null` 當成 dict，發生 AttributeError、actual exit1；已保留該腳本 bytes、stdout／stderr 與 receipt。修正只讓讀值處理這個合法 null，另行 audit exit0。這是原件讀取器的失敗與修復，不是產品紅燈、browser 重跑或 mutant。

原 `d856b65e` 六綠一紅、canvas completed=true／2202 pass＋6 fail／exit1 保留；五個流程斷言連鎖失敗與另一次 FLOOR 計數失敗不改判，不當成像素 golden 或六個獨立根因。最終同 SHA 正式驗收仍由既定 owner 承接，維持 draft，不與 #189 P88／#197 space 直接歸為同因。
