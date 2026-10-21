# A2 帳本方法、逐 ID 判定與證據限制

本補充與已凍結的 `ledger-A2-cc/README.md` 合讀；不修改該包、其原始帳本或 SHA256SUMS。

完整 ledger 的實際來源是 A2 `cbefb39b47fb0edcfaf003d2c1101929fea244c8`。L2 `249571fe2477845d5330f6190dad965bf327f43b` 的唯一父提交是 A2，唯一變更為 `tests/mutants_results.json`；75 筆 execution.head 保留 A2。這是同一產品／測試來源加上帳本的來源綁定，不是把 A2 執行改稱在 L2 重跑。

當輪在全新 detached A2 工作區與空 cache，移除 CC／PYTHONOPTIMIZE，使用預設 cc、stack 16 MiB、core dump 0，依序執行完整 `tests/mutate.py`、`--check`、`--check --killers`。三階段、supervisor finally、父 wait、互動工具最後回覆及必要 validator 皆真碼 0。沒有 ID 篩選或只更新 stale，也沒有重跑 ledger 來整理本包。

78 筆逐 ID 判定與 A2 原帳本完全一致：70 killed、1 crashed、4 equivalent、3 retired。外層另外要求 map 精確相同，不能只因 verdict 屬允許集合便接受新增 crashed 或其他變動。57 個核心 execution 的當輪基準是 165/165；18 個 bridge execution 的 baseline 與 restored 各為完整 27 方法，byte-restored 與 binary identity 由原 validator 核對。

- M20 是唯一 crashed；當輪三次都在 `_test_lshape.scene` 以 -11 存取違規結束。這代表偵測到崩潰，不是斷言殺死。
- 四個 equivalent 是 M09、M23、M36、M56；它們在當輪 A2 都實際有一次 165/165、exit 0 的 mutant attempt。分類的歷史論證保留在原 `why`，不因本輪執行日期而改標成新證據。
- M36 `why` 所述 2026-10-01 的 7,143 輸入差分，以及前一輪「同時拿掉兩處檢查 136/136」都是歷史敘述。本輪沒有重新執行該 7,143 語料、其 fuzz／擾動生成，或該 136 題探針；本輪直接證據僅為正式工具的 165 題 attempt 與來源／編譯指紋。
- retired 三筆不偽造 execution；完整執行數是 75，不是 78 個 mutant binary 都重新執行。

核心原始證據存在固定缺口：正式工具保存完整結構化 oracle result 及子 stdout/stderr 的 SHA256，沒有另外保存每個核心子程序的原 stdout/stderr。頂層 `mutate.stdout` 不能替代這些缺失原件，也不能從 hash 重建。bridge 保存的原 raw／identity／sidecar 則按原工具引用逐 bytes 收錄。

獨立審查定版接受器真碼 0。兩次先前接受器失敗原件也保留：一次把只保尾 3000 字的 `failure.detail` 當完整輸出，一次未處理 FAIL 標頭後的測試說明文字；它們不是 ledger 失敗。修正接受器後核完整 mutant stdout 的具名 FAIL／AssertionError，沒有重跑產品或改帳本。獨審沒有額外重新雜湊 75 個 cache binary；此項由既有正式 validator 完成，不將兩份核對說成同一範圍。

03:25 左右的短暫工具傳輸故障沒有中斷或重啟 writer；原 session 最後實際返回 exit 0。當時只有事後 `/proc` starttime tick，沒有啟動時保存的 tick，可對照 PID／argv／父子鏈與時間，不能宣稱完成歷史 tick 逐值比對。L2 importer 的最外層真碼收據是 root 對實際工具回覆的事後轉錄，已明示不是 raw transport 檔案，也不是再次 wait。

本包只能證明 A2 全量帳本及 A2→L2 發布鏈；其他 L2 正式驗收有各自原件與收據，不由本包推論它們已通過。
