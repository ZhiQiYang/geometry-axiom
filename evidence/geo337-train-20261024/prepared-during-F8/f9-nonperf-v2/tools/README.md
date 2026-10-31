# F9 原 nonperf 工具外稿（尚未正式執行）

僅 root 在 F8 全123原終態完成並獨審、採用帳本固定新 F9 後可啟動。F9 現在未綁；不得用 F8 或目前 evidence head 冒新 F9。工具要求 F8 為祖先、差異含 tests/mutants_results.json 且除此僅 evidence/；產品、測試、原裁判 bytes 必與 F8 相同。採用前後若有其他差異，直接拒絕並另審影響。

沿原 strict wrapper：Q38 完整 SPM01–44、cardref 完整 registry、axiom 完整44基線/恢復與5突變、required-eight 原8 selector共681（source_index18/load_residual14）、PF3原20/19/20。所有原斷言、編譯/測試時限、重試與finally保全不改。Q38 AST 僅metadata守門，不import/執行裁判；完整命令仍無only/group/explore。原Linux唯一允許skip政策不變。

required-eight/PF3沿既有已審v5收件器，保全部原stdout/stderr/argv/exit，不跑prepare/build/compare/perf/profile。F8 R8已有效，不重跑、不改標F9。memo不在此工具內：原memo formal.source_sha必等--sha；只能另審F8錨點漂移後在真F8 proof，不能把R8配F9繞過guard。

原native driver763a6e可重用，不在此重寫。此五gate執行需root checkout lease與重工作排程；required-eight獨占/tmp/geometry-tests，不與native並寫。cardref/axiom暫改真來源，必獨立可寫inode，不得用readonly browser pool。性能與fullcanvas獨占，不與此工具並跑。

原metadata自驗固定new/obsolete/new為0/1/0，不啟任何產品gate。正式每項 fresh OUT；失敗保真，all模式繼續收完其餘項；不得覆寫前次輸出。完整原c387/reaper、原stage內部收件器保留。

啟動樣式（F9/OUT須真綁，現在不可執行）：
python3 -B /tmp/geo337-F9-nonperf-original-tools-v2-20261025/run_original_specials.py --repo /tmp/train337-323-f64d638f-source --sha <F9_FULL40> --out <FRESH_OUT> --heavy-lock /tmp/g261r3/heavy.lock --preparation-sha256 <PREPARATION_SHA256> --gate q38
其餘gate依REQUESTS.json：cardref、axiom、required-eight、pf3；--gate all原序跑五項，非完整native。

V2只將F8→F9的Git差異守門明確設--no-renames，保留產品原葉移到evidence時的刪除路徑，禁止將rename目的地白名單誤當完整closure。metadata自驗沿v1真0/1/0（helper與原裁判相同，不重跑）；其argv保原v1路徑，不冒v2新執行。
