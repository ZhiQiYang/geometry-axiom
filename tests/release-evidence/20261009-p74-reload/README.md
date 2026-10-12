# P74 部分模式（fresh model-base）

這一輪只設 `GEOMETRY_UX_REFINEMENT_ONLY=1`，沒有重跑完整主介面。模式是 partial。golden 沒有比對。通過 52、失敗 0。不要把 52 和 1692、26、316、328、346、1623 或第三階段的 32 相加。

產品檔沒有改。HEAD 是證據提交 `181fc76049b2b2d001957d2ee0008448bbf5b024`，app.js 仍是 `a0545004a061402b645f785bbc883d60137b417399f9c46c5d0323dc7f2297d2`。`cdp_test.js` SHA-256 `31fdf17c0a0e0c3f534504fe4cdfd9f30dfa16bdd4a91f1cda30ce85a7387687`。runtime `9db2394ed4b390e6a99b125fff34fda2fcf6e5cf534daeef6a6b600abbdce490`，fresh，服務 pid 40864，session `73fbc5923f38438e8fea44435b61a2ba`，port 8941。CDP 9541，browser pid 33368。

`NODE_EXIT 0` 來自 `node` 之後的 `$LASTEXITCODE`。`completed:true`。`sections` 只有 P74:52。`uncaughtBrowserExceptions` 是 0。

先前完整主介面停在「重新整理核對同服務同場景後完整恢復身份、附件、模型、草稿及保存記錄」，因為當時的 model-base 沒有 sidecar。這輪用 `binaries.py build model-base` 在私有暫存目錄建出 fresh 的 model-base，SHA-256 `2c0258cdf75f141a1eea5fd5355d7e3347e2a9e9e47512d7ad1ccf408a57e56c`，建於 2026-10-09T18:53:44+08:00。沒有覆蓋共用的舊 model-base，沒有手寫 sidecar，沒有重編 bridge。bridge 仍是 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`。port 8915 沒有停。

同一條重新整理斷言這次通過。下載後備「下載另記時間，保留上次真實保存時間且不清除待保存修改」也通過。那是拿掉 `showSaveFilePicker` 之後的下載，不是作業系統的儲存對話框。清空專案的確認是頁面對話框，由 harness 接受或取消，也不是系統視窗。

## 未驗

P75 之後的外掛、golden 逐段相符、實體手機、人工 IME、真實裝置、託管 CI、原生作業系統儲存對話框。390 格網工作區焦點、空間投影晚回覆、刪除後晚回覆、模型更新標題、面內格網預覽、三視圖投影晚回覆。模擬寬度裡的手機步驟不是實體手機。
