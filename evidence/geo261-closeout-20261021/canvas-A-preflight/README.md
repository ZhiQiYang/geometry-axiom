# A 完整 canvas 預檢證據包

來源分支 codex/geo261-closeout-20261021，完整產品 SHA 7159530c0e494d3211e6ab1764eb691137211707。

這是 A 預檢。最新 PR #288 審查已取得；新候選仍待複審，正式七項、Q38、§7、P-189 將另在同一最終 L 產品 SHA 執行。本包不宣稱 L 正式驗收完成或可以合併。

- 首輪字型工具阻擋：npm build exit 0、中文字型已安裝；外部調度器錯把預設 sans 首選必須是 Noto 當必要條件，於啟服務/browser 前停止。工具 session 實際 exit 1 的事後轉錄有明列來源及限制；0 產品斷言，不算產品紅。原調度器 bytes/hash、raw、cleanup、trace-disabled 全保留。
- 第二輪完整預檢：原 node 真 exit 0，2261 通過、0 失敗、0 略過；85 段與 Git A golden 精確相同。P52=43、P68=36、P72B=50、強化 P73=69，至最後 P86 全部完成。完整 job 2058.016 秒，距 35 分鐘上限餘 41.984 秒；node 2051.649 秒。正式 L 完整 canvas 宜獨占重負載。
- 第二輪前後來源 A/clean、來源 hash、fresh runtime 身分均一致；自有服務與 browser 全部退出，兩 port ECONNREFUSED。服務預期 SIGINT 退出 -2，啟動第一次 probe exit 1 後第二次及正式前後 probe 均 0，沒有隱去這些原始退出碼。
- 第二輪 exec session 18751 遺失，外層 shell exit 無法再觀察；原 stdout 直寫檔案而持續。node 的 0 來自原 wrapper Popen.poll。外層碼保持 null，沒有由 receipt passed 推造 0。
- 本 Linux runner wait trace 未啟用；archive exit 0、trace-disabled 並非等待行為已驗證。P38 預期例外 1 個，沒有未預期例外；原受控 API/network 失敗診斷完整保留。
- 共 135 張本輪 PNG，含事後唯讀封存的兩張 assembly 硬路徑圖；baseline 不存在，原 mtime 及 hash 另錄。P73 本輪空態圖已目視，沒有零尺寸資訊且加入成員入口保留。原 R2 失敗畫面的缺口沒有被本輪新圖補稱為原圖。
- 原 raw 明列的 14 份 saved .gcanvas／P83 下載檔（41960 bytes）亦已唯讀封存。沒有複製 browser profile/cache。
- 本輪沒有突變注入。P52/P72B/P73 的精確撤回自證各在相應包；P72B 這輪只用新 JS context，未指定第二服務，不冒稱雙服務驗收。
- 最後資料核對及另一代理獨立複核各 exit 0。獨立審查沒有逐張目視，也沒有重跑產品測試。

所有原件逐 bytes 複製；來源清單記錄原路徑、長度、SHA-256 與封存時間。可用 sha256sum -c SHA256SUMS 核對封裝。外部調度器保留為 command-code.txt，沒有新增第二份 .py/.js/.cjs 產品工具。本包包含 job 完成後的純證據封裝，這不延長已記錄的 job 耗時。
