# P73 證據封裝

正式結果先讀 `formal/報告.md`、`formal/summary.json` 及獨立審查 `formal/independent-review.json`。正式受測分支 `codex/geo261-closeout-20261021`，SHA `7159530c0e494d3211e6ab1764eb691137211707`。

正式六組皆 actualFixed:true，三組 none 不替換 app：完整 P73 69/69、完整 P73 加明示 callback 69/69、真非空→空→非空 6/6，皆 exit 0。撤 guard、撤 metrics、完整撤回分別 47/1、2/1、47/1，皆因預期條件 exit 1；各收據驗證 exit 0。強化後的同題 metrics 檢查確實由正式 69 題執行。所有專用瀏覽器均正常退出。

`診斷.md`、`獨立審查.md` 及根目錄九組是較早的 R2 候選預覽：SHA `366ef501b78105d1f7242dc1f4f4752cac9086b5`、actualFixed:false、app 候選以明示來源替換生效；當時完整 69 題仍用舊版測試。不要把預覽稱為正式來源重跑。原最小診斷 exit 0、0 個驗收斷言只代表診斷完成；原 P73 自然 69 題全過及單撤 guard 自然 6 題存活均原樣保留，不能算 killed。

`original-full-canvas/` 保留 R2 原完整 canvas：1689 pass、1 fail、exit 1、completed:false，P52/P68/P72B 已過，止於 P73。原頁 DOM／截圖沒有保存；後續截圖不冒充原失敗頁。自然診斷及明示手動 callback 支持根因，但不宣稱精確重演整段排程。隱藏 SVG 的裝飾不是可見假房間；真正可見的是錯誤的零範圍／前空間尺寸文字。

全部 raw、receipt、審查、SSOT 對照、原服務 World 快照及 109 張截圖均保留。`來源清單.json` 記錄逐檔原路徑、精確 bytes/hash；`server-formal.log` 是封裝時點 snapshot，服務保留 idle，來源之後可能追加。`SHA256SUMS` 覆蓋除自身外每個封裝檔。

正式唯一工具只引用 `正式工具來源.json` 的 Git blob，不另複製 .py/.js/.cjs。候選 v2 probe 與正式 blob 逐 bytes 相同。初版診斷 probe 及四個外部調度／patch 生成腳本完整保存為各自 `command-code.txt`，只作來源追溯與重現說明，不是另一套產品工具或正式入口。其原始檔名、處理理由與 hash 見 `程式來源處理.json`；每輪真正執行的 argv 在 raw/receipts，正式調度 argv 與來源 hash 另見 `formal/summary.json`。如需復現，將文字原件放回收據指定的外部路徑並先核 hash；不得直接覆寫既有 log。

正式工具語義：`P73_MODE=full|transition|minimal`；`P73_APP_VARIANT=none|candidate|withdraw-guard|withdraw-metrics|withdraw-all`；`P73_AFTER_EMPTY_SYNC=1` 明示手動較晚 callback。none 完全沿用服務來源；撤回在 app.js 回應階段先核 actual hash，再用精確源碼改寫，於 ResizeObserver 建立前生效。完整撤回有效 app hash 必須為 `362999f2ddd793c832f762f7fb882e7db647091dfde5b4ebb3ee5fd493a77b4b`。`P73_PARSE_ONLY=1` 只解析來源，不啟動 browser；不能冒稱驗收。

本封裝不宣稱最終完整 canvas 2261 題、七項整體驗收或 ledger 已完成。RC-only 真瀏覽器案例尚未新增；新 guard 不阻擋該路徑目前有靜態審查支持。正式與預覽的自然存活、受控紅、來源／清理限制均分開記錄。
