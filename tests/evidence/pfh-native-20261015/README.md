# PF-H 雲端原生證據（2026-10-15，Asia/Taipei）

本目錄保留真宿主、來源鍵、D7、保存／全新程序重開、撤除控制及官方 mutation 原件。
產品來源為 `ae42774a41da403243e8603664fe0b415858e3a1`；`source-audit.json` 列個別檔案雜湊。
完整 native 尚待本檢查點後固定 head 執行；正式 WSL 七項未驗，沒有排程。

- 原四題入口紅：`diagnostics/contract-red.*`，不是移除功能突變。原 Undo/Redo 測試的 transport spelling 已改為既有 line 命令。
- 有理數邊鍵：新增具名案例先實際 exit 1，再修解析器；最後完整正／還原基準均含此題。
- `controls/summary.json`：父程序實際捕捉 29 綠 → 六個單點故障各 exit 1／具名斷言 → 還原 29 綠。
  零 skip、零 error；每份 command、測試輸出、source／binary 指紋及變異前後文字均保留。
- `witness/`：E1／E2／E3 真衍生 D4、兩支 boundary 加一支 primary 的實際 D7 足跡、保存源定義、全新 bridge 重開。
  原生輸出餵給獨立 R43 測試消費者：五段／三段／三段；原單一足跡 oracle 三段／一段／一段保留。
  PF-3 產品 support/effectiveSeams 仍是 null，不把測試消費者稱作 PF-3 產品完成。
- `official/`：三組互斥 ID 完整重編並執行 50 筆，合併後由正式 `mutate.py --check --killers` 驗證。
  請分別讀 killed／crashed／equivalent／retired；crashed 不冒稱斷言殺死。
- 首次 CLI 核心基準有 8/143 SIGSEGV：新增有界快取讓區域 World 撐破 16 MiB stack。
  CLI 與 model adapter 改用程序持有、每次清零的 World 後，同 16 MiB 核心 143/143 通過。
  `diagnostics/core-*` 保留前後差異；後續 mutation 的三個未改基準也各 143/143 通過。
- D28 application／D38 live host 的候選均拒絕，confirm 拒絕，World／revision 不變；見 capability-probe 原件。

本片沒有新增可見 UI，沒有 SSOT／白話／正典／🔒 作者差異。main 更新經一般 merge 承接；未合併 PR、force push、關閉 issue 或改 repository 設定。
