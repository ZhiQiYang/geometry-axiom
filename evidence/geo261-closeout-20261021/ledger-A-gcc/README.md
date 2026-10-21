本次在來源 A `7159530c0e494d3211e6ab1764eb691137211707` 完整重產 78 案，官方重產、帳本檢查與 killer 列表檢查均結束碼 0。A 的 parent 產品 S 是 `ab6869b86a4ad82345359b72397fc055280d8308`，來源樹為 `502024d69976c98f309a3964df1bfb5e5cbcfcc0`。來源所屬工作分支為 `codex/geo261-closeout-20261021`；執行使用獨立 detached A worktree，未修改主工作樹、測試、公理、timeout 或判準，未 commit/push。

全量命令於 2026-10-20 21:15:43.821081 UTC 啟動，22:03:06.037090 UTC 結束，耗時 2842.216033580001 秒。結果是 70 killed、1 crashed、4 equivalent、3 retired；survived、invalid、stale、blocked、unrun 都是 0。75 筆實際執行的 execution.head 全部精確等於 A，3 筆 retired 依既有定義保留，沒有假造執行收據。

核心基準 165／165 通過。57 個非退役核心案例本輪均實際重跑；4 個等價案例亦重新編譯並跑完整 oracle。M20 的基準成功，突變後連續三次皆在 `_test_lshape.scene` 發生存取違規 -11，每次其餘 164 案通過，因此依既有規則記 crashed，沒有改寫成 assertion killed。18 個橋接案例全部 killed；每案 baseline 與 restored 皆完整跑 27 個具名方法，byte_restored=true，還原二進位與基準 SHA256 相同。

原始帳本 `mutants_results.json` 是 5,170,404 bytes，SHA256 `1b8fc87eb83ac5fd5af0589aa48795aa868380d9d5ae35b4c1a8bf7af2175c7d`。`original-ledger.json` 是執行前來源 A 內的歷史帳本，僅作保留對照；其歷史 execution.head 不作本輪驗收證據。重產結果由後續 L commit 收納，execution.head 保留真實執行來源 A，不為了指向帳本本身而改寫成 L；L 的正式關卡另行執行。

原監看工具於中途斷線，原 writer 持續執行且沒有重啟。全量程序退出碼 0 已由原 supervisor 寫入 `mutate.exit-code` 及 `phase-receipts.json`。原 session 後來無法續接，supervisor 未自動執行 checks，且無法取回其自身退出碼或確切退出原因；未把猜測的 BrokenPipe 當成已證實事件。確認 writer/supervisor 都已停止、78 案完整且 full exit0 後，才使用同 A、同環境與唯一 results 補跑兩條只讀檢查，實際各 0，兩次前後帳本 SHA256 完全不變。原 `phase-receipts.json`、`running.json`、原 stdout/stderr 都未改寫；`running.json` 是原啟動紀錄，不是當下存活程序清單。補檢查獨立保存於 `recovery-check-receipts.json` 及 `recovery-check*`。

完整性核對另外結束碼 0：78 個定義 ID 完全齊、75 筆來源相符、8 份 source/rawtool 備份與 A 的 git blob bytes 相同、原帳本保持、隔離 worktree 及橋接 scratch clone 都 tracked clean、沒有 `_mutant_*.c` 殘留、所有已執行二進位 hash 與收據相符。橋接 baseline 共用原輸出 4 檔，加 18 案各 8 檔，共 148 份原 stdout/stderr 全部保存並與帳本逐一 hash 比對；另保存核心 58 份及橋接 37 份 identity sidecar，共 95 份。索引見 `raw-source-index.json`，可提交包的每份原件來源及雜湊見 `publication-index.json`，整包驗證用 `sha256sum -c SHA256SUMS`。

限制與最不確定：既有核心工具僅把子 oracle 的完整結構化 result 與 stdout/stderr SHA256 寫入帳本，沒有另存每個子程序原 stdout/stderr；頂層 mutate.stdout 不能替代這些缺少的原始子輸出。沒有變更工具來補記或另跑第二輪。原 supervisor 終止原因未能直接取證。此次只驗 Linux/GCC，沒有驗 Windows/WSL。此包不宣稱 L 的七項、Q38、§7 或 P-189 已完成；7dae 的歷史 P-189 紅亦未變更。未提交二進位、1.1GB 來源 archive 或 scratch clone；source archive 位置與 hash 保留在 prepare-receipt.json，可用已公開的 A 取得原來源。
