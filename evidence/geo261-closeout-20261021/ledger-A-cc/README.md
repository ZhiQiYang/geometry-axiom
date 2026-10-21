# A 來源完整突變帳本：預設 cc 正式輪

分支：`codex/geo261-closeout-20261021`。正式全量執行來源 A 為 `7159530c0e494d3211e6ab1764eb691137211707`，產品父 commit S 為 `ab6869b86a4ad82345359b72397fc055280d8308`；原始結果由主代理存入 L `43f85313c32410ac01406ab585846bbacafea278`。A 至 L 僅 `tests/mutants_results.json` 改變，75 筆 execution.head 仍保留實際 A，不用帳本自己的 commit SHA 製造循環來源。

完整 `python3 -B -u tests/mutate.py`、`python3 -B tests/mutate.py --check`、`python3 -B tests/mutate.py --check --killers` 的實際結束碼依序為 **0、0、0**。全量耗時 2871.5200704439994 秒，開始於 2026-10-20 22:12:10.978253 UTC，結束於 23:00:02.498312 UTC。兩項檢查分別耗時 4.586378269999841 與 4.644660317000671 秒；檢查沒有改寫 JSON bytes。原始命令、時戳與 wait 結束碼在 `phase-receipts.json`、各 `.exit-code`、`run-receipt.json`。

78 個定義全量處理，結果為 70 killed、1 crashed、4 equivalent、3 retired；survived、invalid、stale、blocked、unrun 皆為 0。75 個非 retired execution 全為 A。M20 以新編 binary 實跑三次，均在 `_test_lshape.scene` 以 -11 崩潰，依官方判準記 crashed。四個 equivalent 本輪均有重編與完整 165 案 oracle；其中 M36 的 why 文字引用歷史 7143 案差分，該 7143 案不是本輪另外執行。三個 retired 依既有定義保留，未捏造 execution。

本輪使用全新 detached worktree、cache、TMPDIR 與外部 MUTATE_RESULTS；環境移除 CC 及 PYTHONOPTIMIZE，依官方預設取得 `cc`，不是設定 CC=cc。57 個核心收據的 compile_command 均為 `["cc","-std=c11","-O2","<source>","-o","<output>","-lm"]`；18 個 bridge 的 baseline/mutant/restored sidecar command 均以 cc 開頭。stack soft/hard 皆 16 MiB，core dump 關閉。結束時來源 worktree tracked clean、零殘留 `_mutant_*.c`，橋接 scratch 也還原乾淨。

核心 57 筆 execution 共用一份成功 165/165 基準收據；官方工具在 mutant 迴圈前跑 baseline，但 blocked 可以重試且只保存最後收據，沒有基準逐次 raw 可獨立數出啟動次數。橋接流程則為一次共用 baseline 27/27，加 18 案各自 mutant 測試與還原後 27/27；全部還原的來源 bytes 及 binary hash 已核。相關原碼為 A 的 tests/mutate.py:1303–1336、1338、1393 及 tests/mutation_bridge.py:455–457、460、474–478、490、494–495。

包內保存 148 份橋接原始 stdout/stderr、95 份 binary identity sidecar、頂層完整 stdout/stderr、兩項 check 收據、啟動／環境／來源核對與原始帳本。`raw-source-index.json` 對照原 cache 檔案；`publication-index.json` 對照每份封裝原件。原 binaries、完整 repo 快照、cache 和外部整理器不放進提交包。9 份來源備份已對 A git blob 驗證，位置與 hash 在 prepare-receipt；可由公開 A 還原。`sourcecode.txt` 是依交辦保存的持久 supervisor 原 bytes，SHA256 為 `308e37f71422f96543d68be4b51a42397c9d734750e0388278bb65941b60606e`。

持久 supervisor 忽略 SIGHUP、stdout/stderr 直接寫檔，不依賴互動工具 session；各階段先保存 actual wait code 再輸出狀態。`launcher-selftest/` 保存預先控制：子程序故意 exit 7，收據如實記 7，輸出完整，supervisor 收到 SIGHUP 仍完成，自測判定 exit 0。正式 supervisor exit 0。

外部整理器第一次 AST 核對誤把 `dict(...)` 定義當 dict literal，實際 exit 1；在產生核對收據／publish 前失敗，未碰官方原件。只修外部 parser 接受實際 AST 後，第二次 exit 0，完整 78 ID 與來源核對通過。`validation-attempt1.*`、`validation-attempts*.json` 與第二次 `validation.*` 保留這個事件，兩版外部 `.py` 原碼路徑及 hash 均有紀錄；這不是重跑官方突變。第一輪 CC=gcc 的原件另存 `../ledger-A-gcc/`，雖同 gcc 環境檢查 0，預設 cc 檢查正確判 57 core stale，因此未採用；本輪沒有修改舊原件或放寬門檻。

未驗及限制：Linux/GCC 14 實跑；未在 Windows、WSL 或遠端 CI 重跑。官方核心工具僅保存完整結構化 oracle result 與子 stdout/stderr hash，沒有另存每個核心子程序的原始 stdout/stderr；頂層 mutate.stdout 不能代替缺失原輸出，這是最主要證據限制。本包不含最終 L 的七項整合、Q38、§7 或 P-189 結果；它們由主代理分開排程。

驗包指令：在此目錄執行 `sha256sum -c SHA256SUMS`。封裝外的 publication-check 與 final-bundle-copy receipt 記錄此命令實際結束碼與逐位元組來源比對，避免檢包收據自我雜湊循環。
