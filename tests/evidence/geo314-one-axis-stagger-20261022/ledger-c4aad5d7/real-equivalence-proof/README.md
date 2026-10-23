# #314 bridge equivalent 真實突變自證封存

產品／裁判修正實跑來源：`c4aad5d7bb98ea864639f9e6d85c99bb2613c24b`。內層 proof 與外層 reaper 原退出碼均 0，來源 HEAD 與乾淨狀態前後相同。
原 `python3 -B tests/test_mutation_freshness.py` 完整 74 方法，退出 0；既有 honesty suite bytes 未因這份封存而改動。

| phase | 原 M110 subset CLI | 原判決 | 原 baseline／mutant／restored |
|---|---:|---|---|
| fixed-baseline | 0 | equivalent | 0／0／0 |
| withdrawn（只撤裁判修正的本地已提交 `160e9dc9759aea2cd6b6f7c9eb717590924d1a24`） | 1 | invalid | 沒有 M110 execution receipt；不宣稱 mutant 或 restored 執行 |
| fixed-restored | 0 | equivalent | 0／0／0 |

固定版與恢復版使用獨立 cache／scratch；各自真編譯、真 bridge、原具名 unittest 與原 `execution_problems()` 單筆驗證均保留。沒有 mock build／oracle。
撤回版的 invalid 是 runner 對第一個 bridge equivalent 定義不相容，沒有 execution；這是裁判修正的 0/1/0 控制，**不是產品斷言 killed 或 crash detection**。

這份 proof 只主張 M110 原 subset CLI、原單筆 execution validator 與完整既有 honesty suite；**沒有主張全表 strict --check 通過，也沒有取代新來源的整份帳本與最終正式七項驗收**。

archive 保存完成當時 inner／outer 的全部 top-level、subcommands、tools、三 phase identity／ledger／validation、所有非 ELF cache stdout／stderr／sidecars，以及原 CONTROL_COMMIT／WITHDRAWAL.diff。每個成員的 path／bytes／SHA-256 已解包核同，原命令所有 stdin／stdout／stderr 也依原收據 hash 核同。`MEMBER_INVENTORY.json` 是逐檔清單，`EXCLUDED.json` 明列排除項。

四個 private scratch／control Git source clone 的 payload 與 7 個可重建 ELF 沒有封入；ELF 原 bytes／SHA-256 逐檔保留，clone 的 path／source SHA／存在與 file count／bytes 也保留。**排除僅指這份發布封包，不代表原 source 不存在；原 raw、source/control clone 與 ELF 都仍在雲端，未修改或刪除。**

原 proof/tools 中的 PREPARER 快照 SHA-256 是 `e14e75825102060aaa3c0361b7a6ffcbf892bc3150f1df39fa06cbe413391f17`；proof 結束後同路徑工具另有版本命令更新，這裡只封當次舊快照，不以現在 bytes 取代。所有當次工具快照與原收據 hash 綁定見 `TOOL_SNAPSHOTS.json`。

本 collector 只在 repository 外產生封存，不執行測試、compiler、retry、commit 或 push，不動目前正在重產帳本的新 source SHA。
