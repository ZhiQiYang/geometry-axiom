# 正式 L 完整 canvas 證據包

來源分支 `codex/geo261-closeout-20261021`，完整 SHA `43f85313c32410ac01406ab585846bbacafea278`。這是正式 L 單輪完整 canvas；A 預檢另包保留，不混稱本輪重跑。

完整 2,261 項斷言通過、0 失敗、0 略過，85 段逐段符合原 Git L golden。P52=43、P68=36、P72B=50、P73=69，直至最後 P86 全部完成。Node 真退出 0、launcher 對 wrapper 的 wait 回傳 0、外層 shell 記錄 launcher 自己退出 0，三層證據分列。wrapper 1971.433 秒，launcher 1971.488 秒，35 分鐘上限餘 128.512 秒；期限自 build 前起算且沒有延長。

source 前後 L/clean、七個來源 hash、fresh runtime 完整身分均一致；自有服務與 browser 全部退出、兩 port ECONNREFUSED。服務預期 SIGINT 回傳 -2；啟動第一個 runtime probe 尚未 ready 回傳 1，後續 probe 全 0，原碼沒有隱去。

`npm run build` 原碼 0，三支 native binary 均 reused，原 built_at 與來源／compile command／binary hash 在 `run/native-identity.json` 及 sidecars；不宣稱本輪重新編譯。父環境 CC 與 PYTHONOPTIMIZE 均 absent。fresh 指來源相符且本輪新建服務，不等於冷編譯。

本輪 `uncaughtBrowserExceptions=1`，恰對應 P38 唯一 `[EXPECTED EXCEPTION] Error: fb-auto-probe`；沒有 `[UNEXPECTED EXCEPTION]`，不能簡寫為「0 個例外」。原 firstTransportFailure/P53 與 firstNetworkFailure/P57–P61 仍完整保留，屬原具名連線／回執控制，不是任意忽略網路異常。wait trace 在本 Linux runner 明確 disabled，archive 0 不代表 trace 行為已驗。

135 張原 PNG 已保存，包括兩張硬路徑 assembly 圖：本輪 mtime 均在執行窗內且晚於啟動前 A 舊圖 baseline。P73 本輪空態圖已目視，但沒有逐張檢查全部圖，也沒有補稱為原 R2 失敗畫面。raw 明列的 14 份 `.gcanvas`／CSV 共 41,960 bytes 一併保存，沒有複製 profile/cache。

獨立複核第一次讀 assembly 原硬路徑時，因路徑不存在而資料比對 exit 1；這不是產品紅，原紀錄保留。後續 native 的 preflight 原件證明整個共用目錄已保全移至 `/tmp/geometry-tests-before-native-l-43f85313-20261020T233737Z`。移存兩圖的 bytes/hash/mtime 與 canvas 原 capture 及封存圖完全一致，另做只讀補核，沒有還原或重測。`cross-job/` 只收移存鏈原件，不把後續 native 的啟動記錄當成 native 驗收結果，也不讀新建同名暫存檔混作本輪原圖。

本輪沒有突變注入；P52/P72B/P73 精確撤回控制在各自包，這裡不冒稱重新執行。P72B 本輪只使用新 JS context，未指定第二 native 服務。斷言混合 trusted input、DOM/programmatic integration 與 native API 檢查，斷言數不等同全端情境數。完整報告及未驗項目見 `run/報告.md`。

`run/` 是該輪 raw、原收據、圖片、原產物及完成後資料核對；`launch/` 保留原父層收據／退出碼／stdout／preflight／兩份程式原 bytes；`preparation/` 是外部調度器設計與控制歷史。後者 `static-check.json` 的 a9ea… hash 屬修正字型條件前版本，定版採 327e… 並有來源與補充審查，沒有將舊 CLI 控制改標為定版重新執行。launcher 的假子程序 0／7／-15 控制是工具驗證，並非產品突變；-15 對應 launcher 外層 241，層級明確分開。

所有原件逐 bytes 複製，來源、長度、SHA-256 列於 `原件清單.json`。可執行副本 `.py/.js/.cjs` 不收；本輪 wrapper/launcher 與假子程序原 bytes 已有 command-code.txt 對照，外部調度程式沒有成為另一產品工具。封存是 job 結束後的純檔案工作，不延長原 job 耗時。

本包只完成正式七項中的 canvas，不宣稱其他六項或 Q38、§7、P-189 全通。最新 PR #288 審查已取得，新候選仍需使用者複審；本包不表示可以合併。其他瀏覽器／平台及未啟用 trace 是剩餘證據限制。

封裝核對指令：`sha256sum -c SHA256SUMS`。原件逐 bytes 與 checksum 核對結果另由封裝操作收據保存。
