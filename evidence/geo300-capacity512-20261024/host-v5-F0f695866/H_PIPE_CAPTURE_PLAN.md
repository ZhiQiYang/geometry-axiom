# H 原管線收據補強設計（未實作／未執行）

原 `tests/_bridge.py::BridgeSession` 用 Popen(text=True,encoding='utf-8')，原 command 直接 write/flush／stdout.readline→json.loads；stderr 是 TemporaryFile，在 stop finally 關閉。故只 wrap subprocess.run 不會留下原 H 方法的每筆命令、回覆與 stderr。新 placed 方法已用 run_once(text=False)，其原 bytes 可由 run observer 留存。

正式 H driver 須在不改產品／原 assertion／timeout 的前提下加**被動原位捕獲**，另交對抗審：

- BridgeSession 建立 Popen 後、任何 command 讀寫之前，紀錄實際 child argv、cwd、來源 F、已釘 binary、環境 allowlist、pid、時間與原 stop_timeout。不能只紀錄外層 unittest argv。
- 原 stdout 的 TextIOWrapper 會正規化換行，禁止把已解析 JSON 重新 dumps 冒原回覆。若使用原 buffer 層 tee，必在任何 read 前 detach，完整保留原 UTF-8／newline／error／buffering 語意；被動 tee 存真 bytes 後原樣交給 decoder。stdin 同理存實際送出的 bytes；部分寫入、BrokenPipe、EOF、decoder 錯誤不可改成成功。
- stderr 必在原 TemporaryFile 關閉前保全所有原 bytes；不能只保存錯誤字串的最後一段。保留原 wait/kill 行為及真 returncode；timeout 記 timeout，不把 wrapper 的例外碼當 C child 正常 assert exit。
- 不攔截／改寫產品 C 的輸出，也不在資料管線插入 JSON。避免全域替換 subprocess.Popen 影響 compiler；捕獲只綁這個 driver 裡真正的 tests._bridge 與同一 alias，原方法仍跑原 child。
- 所有 session（包含正常、三個測試修正撤回、原 safe guard mutant／restored）都要 terminal record；cleanup 之後仍有完整 bytes、SHA、byte-count。configured 路徑未產生不得聲稱已保。

啟用前先以小型 Python 假子程序測 capture 原樣性（只在 root 結束性能獨占後）：原 LF/CRLF、UTF-8 分段、stdout 多行預讀、stderr、非零 child、提前 EOF、父端 BrokenPipe。原與 instrumented wrapper 的送回值／例外類別／真 child code 要一致，capture 的原 bytes 必逐字相等；這是 collector 自驗，不能冒作 H 產品驗收。

設計選項：若 raw buffer tee 無法不影響原 TextIOWrapper 語意，可使用 OS 層被動追蹤並核完整性；在另行審查前不得拿 JSON object 重建原 stream。本輪只記必要契約，沒有聲稱 capture 工具已完成或測過。
