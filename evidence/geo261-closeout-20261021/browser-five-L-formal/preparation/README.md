# 五項 browser 外部編排準備

`run_browser_five.py` 是外部編排，沒有加入正式 repo、架構清單或產品工具。`code.txt` 保存相同 bytes；`static-check.json` 保存 AST 檢查與兩個拒絕執行的負控制。準備當下 repo 為 `codex/geo261-closeout-20261021`／`7159530c0e494d3211e6ab1764eb691137211707`。實際驗收仍等待 root 提供完整 L SHA 及明確 browser 排程；已有 SHA 本身不代表可以啟動。

預計命令（占位字不可直接執行）：

```text
python3 /workspace/geo261-evidence/browser-five-preparation/launch_browser_five.py --sha <完整L_SHA> --execute --release-note <root明確放行訊息與時間> --run-id <唯一小寫標籤> --output /workspace/geo261-evidence/final-browser/<唯一小寫標籤>
```

命令依序跑 assembly、documents、grid、space、timber；任一項未通過立即停止。每項保留原 workflow 的 Node argv 與唯一 scope flag，分別用 15、10、15、15、20 分鐘總期限，開始時間早於 `npm run build`。前置查核、服務啟動、browser、來源核對、程序清理、截圖複製及產物雜湊都算在同一總期限；15 秒僅作清理保留，不外加時間。每項原 browser 結束碼、驗證碼與最終接受結果分開。

獨立服務使用 18851–18855，CDP 使用 workflow 的 9367／9366／9334／9347／9348。每輪專用 TEMP、feedback、cache、profile。`documents_browser_test.js` 自建 profile，仍受專用 TEMP 約束。build/server 保持 `/tmp` 的正式 `start_local.py` 快取，兩次 `require_fresh` 及 runtime-before/after 核對自有 PID/root/version；另逐 bytes 保存三份 sidecar 與 native 執行檔雜湊。字型記錄實際 sans-serif 匹配與已安裝 Noto CJK；沒有把西文首選字型當產品失敗。

清理先對自有 profile/CDP listener 發 Browser.close，再給 server SIGINT；所有強制訊號以 PID/startTime 核對後使用 pidfd。每個根建立獨立 session/PGID，subreaper 接回自己的孤兒。沒有 `pkill chromium`、名稱匹配或對其他 agent 的程序發訊號。結束需自有 live 程序為空，兩個 port 的 connect_ex 皆 ECONNREFUSED；TIME_WAIT 不冒充存活服務。

原始結果解析如下：

- assembly/grid：各一筆完整 `CDP_RESULT`，partial scope 唯一旗標、零失敗/例外、實際 sections 與當前 frozen golden 選定段完全相同。原 harness 的 partial 模式仍不比 full golden，外層選段查核另列。
- documents：原 harness 無 golden/completed 欄位。逐名逐序比對凍結來源的 47 個字面 `check` 與 raw PASS，實際計數一致且最後兩個健康檢查存在；沒有套用交接舊 WSL 52 題。
- space/timber：`SPACE_RESULT` 與原 `result.json` 相符，完整群組/既有固定 census/逐題明細皆通過，未引入新 golden。

原始 stdout、server/build/probe、結束收據、錯誤、screenshots 與 space 結果都保留。manifest 不自我雜湊，也排除仍會更新的最終 receipt；正式封裝時可再對整輪封存清單核對。缺圖或封存失敗另列外層證據失敗，不把它改寫成某一個產品斷言紅。

目前只完成語法與拒絕參數控制，沒有執行這五項 build/browser，也沒有新增產品突變。最不確定處是首次實際長流程的時間預算及 Linux Chromium 與 workflow Google Chrome 差異；後續以原始收據呈現，不能靠延長 deadline 或略過題目宣稱 CI 等同。

## 工具連線中斷時的真退出碼

正式入口改用外部父啟動器 `launch_browser_five.py`，SHA-256 `479cdcd9f1c1c03ab203aff6fc5f0f9fddb3c70d779507777c7c1d903762f124`；`launcher-code.txt` 保存相同 bytes。父啟動器先核對已審 wrapper `4ffefe74…`，將其原 bytes 保存為 `<output>-launch/wrapper-code.txt` 並直接執行該快照，避免事後修改原工具造成來源不明。快照不改任何測試或產品 bytes。

stdout/stderr 從開始便直接寫入 `<output>-launch/orchestrator.log`，子 wrapper 的 stdin 為 DEVNULL 且使用獨立 session。父啟動器忽略 SIGHUP；INT/TERM 只轉送自己尚未回收的直接子程序，內層再按既有自有程序清理。`wait()` 返回的第一個收尾動作，是以原始碼寫 `<output>-launch/.exit-code`，之後才完成 `launcher-receipt.json`。這個碼才是實際觀察到的外層 wrapper 退出；不能由產品 receipt 的 passed 值倒推 0。負碼保留訊號語意；父啟動器自身預計返回 `128 + signal`，該欄不冒充再上層已觀察碼。

若父啟動器本身遭 SIGKILL、環境停機或檔案寫入失敗，缺 `.exit-code` 的結果保持未知。原測試 log、內層收據與仍活程序可以保留，不能補造外層 0。

`launcher-controls/results.json` 是低負載假命令控制：原碼 0／7／-15 皆與 `.exit-code` 及 JSON 相同，AST 與驗證程序 exit 0。假命令刻意輸出 `passed:false` 但退出 0，以及 `passed:true` 但退出 7，證明觀察器沒有依 JSON 推造退出碼；這不表示產品接受結果。短 SHA／缺明示執行均 exit 2 且沒有建立工作或 launch 目錄。這些控制沒有啟動正式 wrapper、build、服務或 browser。
