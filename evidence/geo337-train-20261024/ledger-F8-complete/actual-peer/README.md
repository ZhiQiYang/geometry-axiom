# F8 全 123 筆帳本實績獨立審查

接受原件完整性與原裁判結果；正式原始碼固定 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。`REVIEW.json`：7,625 項檢查、0 錯誤。原指令、環境、退出碼及完整 stdout/stderr 路徑和 hash 在 `ORIGINAL_COMMANDS.json`、`RAW_FILES.json`；逐列結果在 `ROWS.json`。未執行任何產品測試、編譯或 mutator。

123 列由 F8 原 registry 靜態 AST 取得且逐筆相等：67 core、53 bridge（共 120 個 F8 execution），另 3 retired。114 killed、5 equivalent、1 crashed；M20 是同一場景三次存取違規，明確不是 assertion killed。原四階段 exits 為 **1 / 0 / 0 / 0**：舊追蹤帳本過期、新完整 CLI、core stream mapping、新外置帳本 check；outer 和原工具終態均 0。

核對 33 個原 c387 指令、143 個原 observer 指令、636 個 bridge phase/stream 綁定，所有 core 每次 attempt 都各自對回真 command number，結構結果由原完整 stdout 重新解讀且對回 ledger。Core 每次 166 個場景順序與 bridge baseline/restored 的 43 方法皆對照原 source registry。bridge mutant methods 不缺漏，只有 assertion failures 可認 killed，baseline/restored 皆真 0。所有 row record hash、原始 mapping、source before/after/final head/tree/index/clean 狀態一併核對。

限制：原 observer 四個 Git check_output 的 stderr 繼承父程序，沒有四個獨立捕獲檔；父完整 stderr 已核。原 `SystemExit(0)` 是正常入口結束。Core ELF hash 本次核原 mapper/ledger 綁定與原 mapper check 0，沒有再次讀 ELF；不將此說成二次二進位驗證。封包／採用 commit／其餘正式 gates 另審。

## F9 採入計畫

已讀 `/tmp/geo337-F9-byte-adoption-plan-20261025.md`：無實質阻擋。依計畫先完成封包 peer 與普通公開，再鎖定最新遠端 BEFORE，以原 JSON bytes 採入，只容 ledger 與 PROGRESS。務必以 `--no-renames -z` 核 closure，普通 push 後重新核完整 F9，再在 F9 清除 MUTATE_* 執行原 tracked check。不能以本次 F8 外置 check 取代，不改 execution.head/date/verdict，也不因帳本接受解除 exact/B/C/CI。

本審稿自身兩次 parser 假設與 SystemExit 假設修正另保留 `AUDIT_DEVELOPMENT_NOTES.md` 和初稿；沒有改動被審原件。
