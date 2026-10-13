# 完整主介面回歸（ce74dc9）

這一輪在凍結提交 `ce74dc949168b597e33ec00110ce57f26ae51ff8` 上跑 `geometry-web/cdp_test.js`，沒有設任何 `GEOMETRY_*_ONLY`。模式是 full。工作樹在啟動時是乾淨的。golden 沒有比對，因為整輪沒有跑完。不要把 1692 和 26、316、328、346、1623 或第三階段的 32 相加。

產品檔沒有再改。app.js SHA-256 `a0545004a061402b645f785bbc883d60137b417399f9c46c5d0323dc7f2297d2`。`cdp_test.js` SHA-256 `31fdf17c0a0e0c3f534504fe4cdfd9f30dfa16bdd4a91f1cda30ce85a7387687`。runtime `9db2394ed4b390e6a99b125fff34fda2fcf6e5cf534daeef6a6b600abbdce490`，fresh，服務 pid 40308，session `b5a3a1594afb475aafcdfd008dd82f10`，port 8931。CDP 9532，browser pid 6288，node pid 37188。bridge 與 model-base 都沒有重編。port 8915 沒有停。

`NODE_EXIT 1` 是 PowerShell 在 `node` 之後讀到的 `$LASTEXITCODE`。`completed:false`。通過 1692、失敗 2。`currentSection` 是 P74。`sectionsFailed` 是第 5 段 1、P74 1。golden 比較結果是 `not compared (run did not complete)`。

## 兩筆失敗

- 第 5 段拖卡片。預期從 `[[1,60,60],[2,-20,10]]` 變成 `[[1,60,60],[2,100,80]]`。實際等待 4007 ms 後 boundary 1 仍是 60,60，原因 `timeout`。這次產品 diff 只碰到外環邊長的擷取、還原與重繪時的 change，沒有碰到拖卡片。沒有加長等待，也沒有改這段斷言。
- P74「重新整理核對同服務同場景後完整恢復身份、附件、模型、草稿及保存記錄」。重新整理前的專案是 `engineering-spec-example-v1`／「工程規格試用・平面與7支角材」，格式 `geometry-canvas/5`，含附件、面、模型、工程草稿與面投影。重新整理後變成新的 `356f16cf-1b20-46b6-acee-7dc32d96dcba`／「未命名專案」，格式 `geometry-canvas/1`，上述內容都不在。`recovery.state` 是 `unavailable`，訊息是「未恢復本機專案：Native executable lacks a matching current source and binary build receipt.目前場景未被覆寫，請開啟 .gcanvas 檔案。」

恢復路徑以 `verifyOnly=true` 讀回本機專案，接著呼叫 `/scenarios/verify-native`。這份範例含已保存模型，所以驗證會檢查 model-base。當時的 bridge `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d` 經 `binaries.inspect_one` 是 fresh，建於 2026-10-08T20:13:41+08:00。model-base `03a487c77ee20adcc73624adc947027019c071cff9025d1c7ba8cc5a81c8476f`（536064 bytes）是 stale：沒有 sidecar，來源是否相符無從證明。沒有手寫 sidecar，也沒有為了這條斷言放寬收據檢查。

同一輪裡，P73 整段通過，包含「選已知邊一半產生引用式，位置與走向用語一致」。P33 九條通過：成功改成 500、拒絕 0、負數與非數字，面內與主畫布清單一致。P88 段沒有出現在 `sectionsFailed`。這些都不改寫先前中止輪的 1623／2。

## 這輪已經做到、不要重跑的 Windows 操作

鍵盤、焦點、對話框與下載後備在中止前已經走過，包含 P5 鍵盤表、P74 的 Enter 不誤送外環草稿、共用保存的時間紀錄，以及把 `showSaveFilePicker` 拿掉後的下載。那個下載是後備路徑，不是作業系統的儲存對話框。headless Chrome 沒有可操作的系統儲存對話框。

## 未驗

P74 該斷言之後的段落（含清空、新專案復原、服務世界不吻合、雙分頁）與 P75 之後的外掛。golden 逐段相符。實體手機、人工 IME、真實裝置、託管 CI、原生作業系統儲存對話框。390 格網工作區焦點、空間投影晚回覆、刪除後晚回覆、模型更新標題、面內格網預覽、三視圖投影晚回覆。模擬寬度裡的「手機」步驟不是實體手機。

要再跑 P74 重新整理這條，需要這份工作樹上看來 fresh 的 model-base（由 `binaries.py` 建置並帶相符 sidecar）。沒有新編未簽章 exe，也沒有改 Smart App Control。C 與 Python 測試沒有跑。
