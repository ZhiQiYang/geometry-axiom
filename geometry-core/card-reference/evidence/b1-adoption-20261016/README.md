# P-142 B1：採納後版本與舊版能力防線

受測完整 head：`9ba754762304648345c7eb3acace3f79a827465a`。一般合入 main `a898ad6e12707104568679591fe1b21804bfc3df`，合併提交 `23f6e243cb76bddf5545575e44494ae959691bf9`。
本資料夾後續提交只保存文件、expected、帳本與證據；產品與測試逐 byte 對照受測 head。雲端 native，非正式 WSL 收據。

**完整 native exit 1：99 suites，3031 計數／3024 pass／6 fail／1 既有 GDI skip。六個 failure 全在受保護的正典閱讀器 suite（35/41），涉及 I74 追溯狀態及 112／113 統計的重建差異；此輪停止並回報 owner，沒有修改正典、放寬斷言或再跑以掩蓋失敗。B1 相容性 36/36、整卡 34/34、Node 718/718。**

- B1 測試先行：五個具名方法，三條拒絕路徑 × 19 組舊版本 = 57 個修正前失敗斷言，0 errors／skips；修正後完整相容性 suite 36/36。
- 四個一般邏輯突變：整道防線撤除、漏查 manifest、漏查來源、豁免最後一組採納前版本。逐筆具名轉紅，逐 byte 還原後完整 36 題回綠。
- 整卡 49 筆新來源反證：48 筆原生產品碼與 1 筆測試 helper 負對照；沒有借用舊來源收據。保存／格式另六筆 JavaScript 突變。
- 官方 50 筆帳本完整重產與 check；原始 crashed／equivalent／retired 分開保留，不冒稱 killed。
- 完整 native 的 exit、數量、耗時、執行前後狀態與每個 suite 原始輸出見 `summary.json` 與 ZIP 的 native/。
- expected 合併保留兩方 suite，Node 704 + 7 整卡 + 7 transport = 718；完整跑之後唯一新增數量為相容性 31→36，沒有降低門檻或新增 skip。
- 正典直接採用 main 原件。四份受保護文件與 main 逐 byte 相同；參數守門檔案與本輪開始的 d42d21fb 相同，B2／S1 尚未接入。

`raw-evidence.zip` 內含 1071 份原件與逐檔 SHA-256 的 MANIFEST.json；未收執行檔／編譯快取。首份測試夾具錯誤與官方 runner 過早啟動的失敗原件有保留，均排除於有效反證之外。
正式 WSL 七項、B2／S1 與既有身分帳／UI 邊界仍未驗，不宣稱任務 20 最終整合驗收完成。
