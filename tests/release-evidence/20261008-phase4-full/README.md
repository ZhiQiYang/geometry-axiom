# 完整主 UI 回歸

這一輪在第四階段跑 `geometry-web/cdp_test.js`，沒有設任何 `GEOMETRY_*_ONLY`。模式是 full。它在 P73 中止，所以 golden 沒有比對。不要把 1623 和其他輪的通過數相加。

產品檔沒有再改。當時 HEAD 是證據提交 `457eade180add835e6b9fc854835844c7515281e`，產品提交仍是 `d44ad7fea531a94f67401d5b403565cd891770ae`。runtime `f2804c8068805409ccc06cddea3fac6219f768706f9276e981948f1142a286b2`，fresh，服務 pid 31516，session `ba75fc92a0794359b9126079015c9949`，port 8916。CDP 9518，browser pid 43880。bridge 與 model-base 都沒有重編。

`NODE_EXIT 1`。包住它的 PowerShell 管線結束碼是 0，因為 `Tee-Object` 吃掉了 node 的結束碼。以日誌裡的 `NODE_EXIT 1` 為準。

## 兩筆失敗

- 第 5 段拖卡片。預期卡片位置從 `[[1,60,60],[2,-20,10]]` 變成 `[[1,60,60],[2,100,80]]`。實際等待 4005 ms 後仍是 boundary 1 的 60,60，原因 `timeout`。這段 golden 是 1，本輪是 0。`app.js` 這次的 diff 只碰到外環邊長的擷取與還原，沒有碰到拖卡片。
- P73 `選已知邊一半產生引用式，位置與走向用語一致` 回傳 false，接著 fatal，整輪 `completed:false`。操作是把軸向改成 v、來源改成 `edge:e1:u`、比例改成 `1/2`，再按建立引用線。失敗當下的狀態列仍是上一筆成功提示 `guide 3 1 u param:1:1`。快照裡的 `connection.error` 是「無法確認載入結果，已暫停編輯。請確認服務後重試。」斷言把找不到指定引用、偏移不是 2000、或檢查器文字沒有「沿 v」與「u = 2000」都折成同一個 false，這輪沒有拆開。同一句 fatal 已記在 `geometry-web/docs/ISSUE116-B-HANDOFF.md`，那次也沒有改 guide 行為。這輪沒有為它改產品或測試。

P33 九條都通過，和 golden 的 9 相同。P88 在中止前已有 137 條通過。golden 仍是 107，檔案最後一次修改停在 `459478e`，早於後來加進格線測試的斷言。部分模式的舊格線輪本來就不比對 golden。這不是把 137 寫回 golden 的理由。本輪有失敗，沒有設 `GEOMETRY_CDP_UPDATE_GOLDEN`。

已跑完的段落裡，和 golden 不同的只有第 5 段、P88、以及中止中的 P73（本輪 36，golden 69；多出來的差是還沒跑到，不是 33 條各自失敗）。

## 未驗

golden 逐段相符、P73 之後的段落、實體滑鼠、IME、真實裝置、託管 CI、原生作業系統儲存對話框。沒有新編未簽章 exe，也沒有碰到 Smart App Control。C 與 Python 測試沒有跑：這次產品 diff 沒有 C 檔，也沒有對應的 Python 測試。
