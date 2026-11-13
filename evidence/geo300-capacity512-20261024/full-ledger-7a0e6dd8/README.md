# #348 原全帳本終態核收

固定原執行來源：`7a0e6dd81c54066995981393925fa46a815de2f8`。

原程序於 **2026-10-29 03:00:41.343947–04:31:23.469447 UTC** 執行；約 5442.126 秒。本輪只回收既有原件，沒有重跑測試、改動產品／帳本原件、寫 Git 或發布。

| 原命令 | 實際 exit | 原結果 |
|---|---:|---|
| `python3 tests/mutate.py --check`（重產前） | 1 | 107 stale、13 unrun、3 retired；原紅保留 |
| `python3 tests/mutate.py`（完整 scope） | 0 | 123 筆全覆蓋：114 killed、1 crashed、5 equivalent、3 retired |
| `python3 tests/mutate.py --check`（重產後） | 0 | 0 stale／blocked／survived／invalid／unrun |

wrapper exit 0、reaper primary exit 0；原 source_before／source_after 都是同一 M、status 空白。完整 123 筆由原表的 core 70 與 bridge 53 組成；退役 3 筆不算真執行。

原 `ledger.json` SHA256：`812956bf480e74eda9e838e29f40f83a9cdd1f317e16e0432aaf539f33fcc569`。採入後仍必須保留其中原 execution SHA；不得移標成後續 ledger／evidence commit。

M20 是唯一 crashed：原基準全過後，三次在同一 `_test_lshape.scene` 以 `-11` 存取違規結束，依原規則單列，**不是斷言 killed**。五個 equivalent 為 M09／M23／M36／M56／M110；三個 retired 為 M35／M51／M55。未新增豁免。

已保全 `originals/` 697 份原文字檔、14,330,005 bytes。內容包括原完整帳本、receipt、85 份頂層 capture 檔、wrapper／reaper、原工具及所有可用 bridge build／test raw streams、binary sidecars；使用 copy2 並核 bytes／mode／mtime／SHA256 相符。逐項對照 `ORIGINAL_MANIFEST.json`。原 full-ledger stderr 的 333-byte Git alternate 警告也原樣保留。

`EXECUTION_LINKS.json` 另核 120 個非退役 execution 與原 ELF／sidecar：67 core＋53 bridge；636 個 bridge build／test stream 引用對應 428 份獨立 raw 檔，SHA256 全相符；baseline／restored ELF hash相同，三組 build exit 0。原175支 ELF 共182,733,328 bytes仍在原 SHM cache，已核 SHA256 與 sidecar身份；為遵守本次30MiB暫存預算，**沒有複製或打包 ELF**。精確清單在 `ORIGINAL_ELF_MANIFEST.json`，不得把這份文字保全說成完整二進位已遠端交付。

原 core mutator 將每次 oracle 的結構化結果及 stdout／stderr hash寫入帳本，但不另存每次的 raw stream；本輪沒有重建或偽造這些不存在的原流。頂層 full-ledger原 stdout／stderr則完整保全。完整 ledger0/checkafter0不能冒充尚未完成的 native35分鐘或六browser。

核收工具第一輪把原 relative `baseline.stdout` 誤當絕對路徑而 exit1，原錯誤在 `RECOVERY_FAILURE_1.txt`；依原cache位置解析後工具exit0，沒有改原件，也沒有重跑產品。可重現的只讀核收腳本為 `recover.py` 與 `verify_execution_links.py`。

下一步由 root 在官方分支採入整份帳本、以原命令驗採入後有效性並發布證據；本子任務未操作官方分支。規則獨審見 `rules-review.md`。
