# #209 分段量測證據（指定任務 12）

完整方法、六筆逐階段表格、限制與修正方向見 [診斷報告](../../diagnostics/request_wait_segments/README.md)。本次只做量測，未修產品，未跑 WSL 全量。

| 檔案 | 內容 |
|---|---|
| [raw.tar.gz](raw.tar.gz) | 228 個原始／衍生檔；正式與失效 pilot 均保留 |
| [raw.tar.gz.sha256](raw.tar.gz.sha256) | 壓縮包 SHA-256 |
| [raw-manifest.json](raw-manifest.json) | archive 每個檔案的 bytes / SHA-256；打包後已逐一重讀核對 |
| [analysis.json](analysis.json) | 七組、每筆真正 fetch 的所有階段、真逾時與 fetch 前 guard |
| [timeouts.csv](timeouts.csv) | 六筆真正 fetch 逾時的完整小數時間；空值是未進入該階段 |
| [analysis.stdout](analysis.stdout) | 分析器原輸出（exit 0） |
| [cohorts.stdout](cohorts.stdout) | 七組 runner 原輸出（exit 0；故障組 oracle 未完成仍如實記錄） |
| [metadata.json](metadata.json) | 13 項命令 stdout/stderr/exit、版本、16 MiB stack、產品來源 hashes、binary 來源閉包與指紋 |
| [baseline.png](baseline.png) / [bridge18.png](bridge18.png) | 原 P7 完成與 15 秒連線 error 畫面（1400×900） |

解開 archive 後：

- **`cohorts-drained/` 是唯一正式七組**。每組有 `server-events.jsonl`、`browser-events.json`、`result.json`、`ready.json`、server stdout/stderr、console、network-failures、DOM、截圖及 `browser.cjs.executed` / `server.py.executed`。`cohorts-drained.exit=0`；`analysis-drained.exit=0`；`metadata.exit=0`。
- `cohorts/` 是清理時機不正確的失效 pilot；`analysis.stdout` / `analysis.exit` 亦為該初版分析，**不採作原生回覆結論**。其工具及假 EOF 證據沒有刪除或改寫。
- `baseline-run/` 是先行基準；其 shell 記錄 `baseline.exit=0`。正式表格只用重跑後的七組。
- 研究／看板快照：`research-r1.md`、`issue209.md`、`BOARD-cloud-codex.read.md`。看板 branch SHA：`c3730132fc4a9b334d2c7998c671d7c70029ba8a`。
- `analyze.executed.py` 是強化後實際分析器；`collect_metadata.py`、`package_evidence.py` 記錄環境與打包方式。pilot 與正式輸出沒有互相覆蓋。

所有時間差只在各自程序時計內計算，跨程序只以 request ID 關聯。HTTP BrokenPipeError 是瀏覽器已 abort 後寫回失敗，不能當成新的傳輸耗時；清理時的原生空回覆不能當成清理前故障。原生程序清理前存活且 bridge_failure=null，由各組 `native_before_cleanup` 記錄。

資料只來自本次隔離測試場景；產品來源沒有改動。這是雲端 Linux 的受控 P7 表達式實驗，不是歷史 Windows/WSL 故障的根因定案，也不是完整 canvas/WSL 收據。
