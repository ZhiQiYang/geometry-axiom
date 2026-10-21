本包保存分支 `codex/geo261-closeout-20261021`、完整 SHA `6589248c9a94bdf0460d8f84dd1610e51048188b` 的一次正式完整 canvas。2261 通過／0 失敗／0 跳過，85 段與該 SHA 的 golden 完全一致；P52 43、P68 36、P72B 50、P73 69。原 Node、wrapper 父 wait、launcher 父 wait、工具真退出均為 0。原 2100 秒整個 job 上限不變，實際 2062.211495709 秒，包含 build／啟動／測試／清理，剩餘 37.788504291 秒。

| 核對項目 | 原件直接連結 |
| --- | --- |
| 原 CLI `node geometry-web/cdp_test.js`，full、filters=[]、modifiers=[] | [父命令](launch/canvas-L3-formal-6589248c-parent-command-code.txt)、[原 receipt（含 Node 步驟 argv／退出 0）](run/receipt.json) |
| 完整 stdout 與原結果 | [canvas.log](run/canvas.log)、[result.json](run/result.json)、[原 golden 驗證](run/result-validation.json)、[Git golden 原 bytes](run/golden-snapshot.json) |
| wrapper 父 wait 真碼 0 | [永久 .exit-code](launch/canvas-L3-formal-6589248c.exit-code)、[父 wait 收據](launch/canvas-L3-formal-6589248c-launcher-exit.json) |
| launcher 父 wait 真碼 0／工具 session 真碼 0 | [永久 launcher-process.exit-code](launch/canvas-L3-formal-6589248c-launcher-process.exit-code)、[工具回傳轉錄](launch/canvas-L3-formal-6589248c-exec-observation.json) |
| 來源與 runtime 前後 | [source-before](run/source-before.json)、[source-after](run/source-after.json)、[runtime-before](run/runtime-before.json)、[runtime-after](run/runtime-after.json) |
| 自有程序與 port 清理 | [cleanup.json](run/cleanup.json) |
| 驗收與獨立覆核 | [報告](run/報告.md)、[主接受器](run/final-verification-code.txt)、[主核對真 0](run/final-verification.json)、[peer 真 0](peer/peer.json)、[peer 實際執行碼](peer/execution-v2.json) |
| 135 張原圖與 21 件補封產物 | [screens](run/screens/)、[原產物 capture](run/declared-artifact-capture.json)、[下載原件](run/declared-artifacts/) |

主來源前後為 L3 clean，runtime 版本／程序／session 相同且 fresh。三支 private runtime binary 本輪均為 **reused**，原建置時間仍 04:19／04:20；沒有預置或複製 native global binary。194 份 binary dependency 與 160 份 browser 來源逐項綁 Git；額外首次 binary 採樣在 Node 已開始後，不能稱為 Node 之前。當輪 [build.log](run/build.log)、[during-start](run/native-identity-during-start.json)、[after](run/native-identity-after.json) 與原 sidecars 都保留。native 初建六 binary／12 件小收據只證明本輪放行條件，不證明 native 全驗收。

P38 保留 **1 個預期 uncaught exception** `fb-auto-probe`，非預期例外為 0；P53 firstTransportFailure 與 P57–P61 firstNetworkFailure 是原受控路徑，不能寫成零 transport／network failure。wait trace 為 disabled，0 records 不代表零等待。首次 readiness probe 1、後續 fresh 0、服務清理 SIGINT -2 亦保留。本輪沒有新增撤回突變執行；原受控路徑與既有專項撤回證據分開陳述。

135 PNG 包含兩張硬路徑 assembly 原圖；補封 21 件為該兩張圖、8 gcanvas、6 CSV、5 同下載目錄原測試 JSON，共 262484 bytes，缺失 0。JSON 另標收據，不冒稱 raw 直接宣告的下載。所有圖與補封檔 mtime 在本輪窗內，沒有重生成。peer 檢 PNG CRC／hash，未逐張目視。

`peer/` 全收獨審原件：首版因 parentEnvironment 新增欄位而誤判 1，修正為核實三個欄位後真 0；保留首版 code、完整 stdout／stderr、真 wait、最小差分。這是只讀接受器的 schema 誤判，不是產品失敗，沒有重跑 canvas。`preparation/` 保存 160 來源靜態準備、兩個 capture helper 原 bytes／來源實例化對照與 native 初建小收據；`launch/` 保存實際原碼、argv、父環境、永久真碼與原始工具回傳轉錄。工具觀察是實際回傳逐欄轉錄，不冒稱 transport 自動原始日誌。

封包器首次沿舊輪的 native 初建 index 檔名而在建立封包前退出 1；原件實際存在，僅修正外部封包路徑後成功。首版程式與完整工具觀察保留於 preparation/，沒有產品重跑。

其他五 browser 另包 `browser-five-L3-formal`；native 與 gates 依各自同 L3 當輪原件，不由本包推論全七項已完成。本機 Chromium／Noto 與 CI Google Chrome、同機 native 並行的差異保留；耗時不作 P189 性能證據。

`source-index.json` 精確列原件來源／封包路徑／長度／SHA-256／mtime。原件逐 bytes 保留，封包檔案 mode 0644；外部程式以 `.txt` 保存，未收 `.py/.js/.cjs` 可執行副本、binary、Chrome profile 或 cache。`SHA256SUMS` 含全部檔但排除自身；包外驗證另存，不回寫凍結子包。
