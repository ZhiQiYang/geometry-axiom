# 任務 20：切片 A 實測證據

雲端 native,非正式 WSL 收據。最終交付 head 的完整 native 結果另留在 PR #253 交付留言；本包不把第一輪失敗控制當成交付綠燈。

依 #250 `f3f99a29` PROPOSAL 及 #253 P-133；base 為 #193 的 `6236f5733052a19362132738a4eb79cac7924e0b`。
產品及測試來源 epoch 為 `277050b7316e979e75153b141dd4d0c446cfcae0`，後續提交僅補證據、官方帳本與 expected。

`raw-evidence.zip` 保存 994 份原始命令、編譯輸出、測試 stdout/stderr、逐筆結果及雜湊，沒有執行檔；`MANIFEST.json` 列每檔 SHA-256，外層另附 ZIP SHA-256。

| 路徑 | 實測意義 |
| --- | --- |
| `mutations-closeout/report.json` 及各子目錄 | 31 方法基準全綠；44 筆真正修改 native 來源、重編、對應具名 CR 轉紅，再還原重編同案回綠。無編譯失敗、error 或 skip 冒算 killed。含來源、測試、裁判及二進位指紋。 |
| `archive-mutations-final/report.json` 及各子目錄 | 7 方法基準全綠；6 筆保存格式／manifest／來源宣告／reader／錯誤版號／快照根能力突變各轉紅，還原同套回綠。 |
| `official-closeout/` | 官方工具依 AGENTS 規則分 ID、隔離結果與 cache 執行，合併 50 筆後官方 `--check` exit 0：42 killed、1 crashed、4 equivalent、3 retired，零 survived/stale/blocked/invalid。crashed 為官方 M20 三次同夾具 SIGSEGV，沒有改列 killed。 |
| `preimplementation-193/all-tests.*` | 固定 #193 原實作編譯後跑新增 31 方法，31 failures、0 errors、0 skips、0 compile_failures，exit 1；不是只以預期字串描述會紅。 |
| `corrected-directed.log` | 修正後 99 個原生方法通過、0 skips：整卡 31、modeling transport 3、scenario verify 37、section profile native 28。 |
| `unbind-{before,after}.log`、`nested-card-{before,after}.log` 與 probe | 真實前後反例：刪重建後轉逐欄被錯誤 I38 擋住；只有方案快照有整卡時根保存漏能力。修正後各恢復合法行為，另有逐槽宣告與根能力真突變。 |
| `native-full/` | 較早候選第一輪完整 native 的失敗控制：96 suites，2940 count、2896 pass、43 fail、1 既有平台 skip，exit 1。暴露舊能力白名單及格式／能力數斷言需隨新增協定更新；修正及定向重跑後，最終 head 重新跑完整 aggregate。 |
| `node-full-census.log` | 隔離執行全部 Node suite：711 tests、711 pass、0 fail、0 skip；exit 1 僅因 expected 尚為 710，且有 `--only`，不可冒充完整 native。 |

`expected-changes.json` 列唯一三個數量變更：新增整卡 31；#193 實際已有的 parameters core 25→35；Node 704→711。第一輪完整執行以 `--update-expected` 取得前兩者及 Node 710，補快照根案例後再實測 Node 711，無降低或移除 suite。

CR19 使用真正 ZIP 及新 native context；CR29 保存完整 canonical base_scene、整卡映射、來源卡及傳遞依賴，檢查能力、verify_package 幾何重算與缺件拒絕，沒有修改 model_base.c 的幾何依賴折疊。
CR16 使用實際 rule→guide→timber 下游重新求值；CR17 以測試 TU 的真 bridge confirm 路徑注入失效下游，檢查拒絕時 World／revision／dirty／undo redo 不變；產品沒有測試後門。

未驗：CR18 啟用身分帳／外部 pin 與對應 M12（基底未宣告 native identity-ledger/1）；CR24／M23 UI 屬切片 B；正式 WSL 七項由本機列車執行。CR18 僅驗未啟用身分帳對照。PROPOSAL 原文沒有 CR23／M15，不補號、不加假 skip。官方帳本 M12/M23 和 GEO-262 提案的同號不是同一套突變，不可混稱已覆蓋。

請 Claude 依原始證據核對，這份記錄不自行宣告驗收通過。
