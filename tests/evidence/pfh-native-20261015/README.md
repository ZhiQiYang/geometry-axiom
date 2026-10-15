# 新審查 6183160730：消費端已補，最終裁判待重跑

第二分量的子格正面積與場景輪廓已修正。新增三題覆蓋第二分量 grid/subgrid、重開與 I23 原子回滾、缺口／孔零面積、實際 DrawTarget render 與 guide pick；32 題在規定 16 MiB stack 全過。
補測前在未改產品的 63ed444 原生 binary 重現：三題中 2 紅／1 綠，分別是 I25 第二分量誤拒及缺少第二塊 polygon。第一份外部補測曾誤寫不支援的 explicit 字詞，另存 invalid-dsl，不當作領域紅；第一份正向執行未設 16 MiB，另存 default8m 診斷，不冒稱規定環境回歸。
完整 native、控制、正式突變和見證將隨目前產品重新執行；下方 63ed444 數字是歷史 head。正典同步與正式 WSL 七項仍阻擋，不宣稱可合併。

---

# PF-H 原生交付：正典同步仍阻擋

固定 head `63ed4448546638b9515eb63574e308abf5c697f2` 的完整 native 已跑完，6 題因 R41 追溯同步而紅；數字與限制見 [NATIVE-RESULTS.md](NATIVE-RESULTS.md)。

同 head 的 controls-review-63ed：29 綠 → 六個領域斷言紅及一個子格堆疊撤回紅 → 還原 29 綠，無 skip／error。程序退出碼與領域斷言分列。
原同步器記憶體內生成的 14 行差異使原 reader 41 題全綠；正典本體沒有改動。依看板交唯一 owner #207／Claude 在包含本片來源的整合候選處理，不宣稱可合併。
正式 WSL 七項仍未驗。以下是 `24ba8332` 檢查點的原說明；prefull-manifest 僅描述該歷史檢查點。

---

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
