本目錄是 **protocol-only 真實合成 C／pipe 校準**。首輪編譯並執行最小 stub 與原 wrapper 副本；沒有編譯或執行任何 geometry 產品源碼／ELF，沒有 N512、perf、browser 或 heavy lock。

首輪 `RESULT.json` 的61項檢查全過，共26筆內層原命令，另保存外層 driver 命令。每筆 full argv、exit／例外與 raw stdout／stderr 都在各自 `runs/` 目錄，原失敗控制保留。`MANIFEST.json` 逐檔固定 bytes／SHA256；約1.2 MiB，低於8 MiB限制。

已取得的實際證據：

- `cc -std=c11 -O0 -Wall -Wextra -Werror` 編譯 unwrapped、fixed、withdrawn、restored 四個 stub；wrapped 額外使用 `--wrap=fgets`／`--wrap=fflush`。`nm -a` 原流包含兩個 wrapper 與 libc fgets／fflush 符號；正常實際執行留下4個 stdin-return、4個 flush-enter、4個 flush-return及EOF，共13事件。
- normal、stress、stdin_error、stdout_error 的 unwrapped／wrapped stdout及stderr逐 byte 相等。正常 stderr 的控制數據也驗非stdin FILE、tmpfile fflush、fflush(NULL)、非匹配FILE讀錯以及 errno sentinel；stdin EBADF 被記為 stdin_error，stdout EBADF 被記為 flush-return -1。
- 真實 subprocess.run 壓力案例寫256 KiB stderr及分段stdout。額外 Popen／selectors 收據顯示 stdout 實際分5次讀到，前4片段不以LF結束，串接bytes等於原run輸出；child均已回收。
- `031-real-timeout-0.25s` 使用 **合成專用0.25秒**，真 TimeoutExpired 保留cmd1完整JSON與cmd2部分stdout、stderr；returncode仍null，原例外身份保持。PID檔對應 `waitpid` 回ECHILD，`kill(pid,0)` 回process absent，證明原subprocess.run已kill／reap。這沒有修改或執行產品600秒門檻。
- `030-event-write-failure` 在首個read事件後關閉child的event FD，原輸出與errno控制資料不變，status為attempts13／successes1／faults12，診斷拒絕判定。
- C負控制只在臨時copy撤掉flush-return事件；三個真guard CLI exit **0→1→0**，withdrawn報input-command-identity。該控制的raw stdout／stderr仍等於unwrapped；`C_WITHDRAWAL_PROOF.json`保存原guard結果。

界線與未做事項：

- 只校準本目錄的合成stub ELF。產品ELF的實際callsite／fortify／ABI／符號命中、原產品四指令及N512仍 **UNRUN**。沒有產品gate或timeout根因結論，也沒有新效能資料。
- 真pipe驗證使用本目錄的校準driver（timeout案例為原subprocess.run，額外分段觀測為Popen／selectors），沒有宣稱已把真pipe案例整合到原 `launch_diagnostic.py`。校準driver的finally尚非一般I/O／close故障保護器；本輪未發生該類recorder故障。原正式launcher的close保護另有Python工具反例。
- 本輪有實際event FD寫錯控制，尚未逐一注入C clock、format、partial-write、mmap或每一初始化錯誤。不能將61項寫成所有C故障分支已驗。
- 首輪未在執行前另存PYTHONOPTIMIZE／sys.flags及磁碟free／空間估算收據；此為紀錄限制，不能用事後資訊補成歷史。`r2/`只建立草稿與其preflight，收到父代理停止指示後 **未執行、未編譯**；沒有第二輪或第三輪，r2/preflight不是首輪執行前證據。
- 原 `trace_wrap.c`、`sidecar.py`及其餘既有工具保持不變。`REPAIRED_GUARDS_READONLY_REVIEW.json`另唯讀核對父代理fixture／close／flush_entry／flags共12個Python假runner原命令，四組各0→1→0；沒有重跑它們。

首輪RESULT SHA256：`58310d85b42628c2fc55bb790cd51bb23d803def2454bde225e56b0bdf8afa11`。任何產品來源、正式資料或N512執行仍由root另排獨占時槽。
