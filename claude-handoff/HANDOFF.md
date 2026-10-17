# 本機 Claude → 雲端 Claude 交接(2026-10-17 13:20 台北)

本檔記錄交接當下的狀態。在途的子代理之後可能又推了新 commit,**一律以遠端分支的實際 head 為準**:先 `git ls-remote` 或 `gh pr view` 核對，再動手。

## 1. 角色與分工

- 2026-10-17 起，全部實作都由 Claude 做，決策記錄在 `決策佇列.md`(#292)。
- GEO-261(核心與木工模板解耦，#248)已由 ChatGPT Astra 全權交給 Claude。Astra 的交接全文在分支 `handoff/geo261-astra-wip-20261017` 的 `evidence/geo261-astra-handoff-20261017/README.md`。
- 雲端 Codex 只負責在指定分支上跑測試並回報，不改程式。請求列在本分支 `BOARD-cloud-codex.md` 的「雲端測試請求」,目前 R-002 待領，還在等使用者確認。
- 品質流程:
  - 實作交給子代理。
  - 每個 PR 交給獨立的 opus 對抗審查，不自審。
  - 審查意見退回作者修，再合併。

## 2. 合併規則

- 只用 merge commit,不 rebase、不 squash、不 force push。
- GEO-261 的 `AXIOM_REVISION e744f531` 必須保持可從 main 追溯。
- 正式裁判是**使用者電腦上的 WSL 七項**(native + canvas/assembly/documents/grid/space/timber),結果全綠才能合併。
  - GitHub Actions 自 2026-10-03 起被帳號計費擋住，所有 job 都在 3 秒內失敗。這是計費問題，不是程式失敗。
  - 雲端自己跑出的結果一律標「雲端預跑，非正式 WSL 收據」,不能當合併依據，除非使用者在對話中明確同意以雲端結果代替。
- 列車流程:
  1. merge main。
  2. 用 `tools/synth_expected.py` 逐 suite 三方合成 `tests/run_all.expected.json`。
  3. 正典閱讀器只能用 `python3 geometry-guide/sync_axiom_reader.py` 重產，接著跑 `--check` 與 `tests/test_axiom_reader.py`。
  4. 跑 `python3 tests/mutate.py --check`:有 STALE 就重跑那幾筆;tool 或 oracle 雜湊變了就整份重產。
  5. 最後跑七項。
- 對 `tests/*.py` 的任何改動，都會讓 bridge 突變 M61–M70 過期。
- 只改不被建置或測試讀取的文件(BACKLOG、決策佇列)時，不必重跑。

## 3. 在途工作(交接當下)

| 項目 | 分支 / head | 狀態 | 下一步 |
|---|---|---|---|
| 下角材班 = #251 oracle + #254 native suite | `train/framing-20261017` / `f1fd146f` | WSL 七項:native、assembly、documents 綠;**canvas exit=1**:2177 斷言全過、0 失敗，但 P83 的 CSV 下載逾時(fatal: No completed actual CSV download)。判定為環境逾時:本班沒改前端，跑的時候 Windows 上有子代理在跑測試。grid/space/timber 交接時還在跑 | canvas 排他重跑;七項全綠就開列車 PR → 合併 → 關 #251/#254 |
| #253 GEO-262 B1/B2 整卡引用 | `feat/card-reference-core-20261015` / `33e655d6` | 已合 main c76737ec;卡片年代分三段:現行版本與 b3c79615 可帶整卡，更早的 19 組拒絕 | 與 #294、#295 同一班。突變帳本要整份重產，要跑到新的 M78–M87;另跑 `run_axiom_mutations.py`(V01–V05)、`run_mutations.py`(53 個自訂突變)、七項 |
| #293 回執封存項容量(Fixes #264) | `fix/receipt-tombstone-capacity-20261017` / `6d5bb03c` | opus 審查無阻擋;作者正在補 2 個測試、修契約第 11、20 行與 PR body | 補完後確認新測試讓審查員的突變 M8b/M7b 轉紅，再上列車 |
| #294 突變判決誠實性(看板任務 32) | `fix/mutation-bridge-crash-honesty-20261017` / `3adc84ff` | opus 審查中;合併後 tool 雜湊變更，64 筆全 stale | 審查意見處理完，併進 #253 那班 |
| #295 S1/S7 核心場景(看板任務 29) | `test/s1-s7-core-scenes-20261017` / `ba94f0a7`(突變已改號為 M86/M87;與 #253 都改 `tests/mutate.py` 尾端與 `core:run_tests` 計數，後進者要解衝突並合計) | opus 審查中;預期值是讀程式推的，**沒有原生實跑** | 原生實跑核對 7 個場景;併進 #253 那班 |
| #260 條文稿(給使用者看) | `proposal/stagger-one-axis-wording-20261016` / `3a524bd5`(作者還在加 commit) | A 區:「只准一軸」🔒,放 K 段，見 P-160。B 區:I5、R18 措辭。C 區:I23、R13 標題。D 區:Q-E 用詞。`evidence/check_quotes.py` 逐字驗引文 | 待最新 commit:K 段不得引用 W 段;白話版同步;D 區。之後派 opus 審查，**交使用者看稿**,不得自行採納 |
| GEO-261 #279 原生來源圖 | `architecture/geo261-native-source-graph-20261016` / `96e06218` | 修了 `tests/geo261_model_vertex_ledger_harness.c:86` 改傳指標，這是讓 145 項沒跑的編譯錯誤 | 22 個模組 276 項重跑。WSL 已排隊，交接時還沒輪到;模組清單見 `tools/focused-modules.txt` |
| GEO-261 #288 整合 | `architecture/geo261-integration-20261016` / `43305271` | 子代理正在把 main c144c013(第 18 班 #193 參數重宣告、#266 終版)合進來，是最高風險的移植，必讀 `tools/incoming-train18-overlap.md`;也會一併合進 96e06218 | 檢查遠端是否已推新 head;沒推就自己重做 |
| GEO-261 其餘 | 見 Astra 交接 §3 | coverage-activation 補丁待套用;#289 Python 預設尚未合入;要整份重產突變帳本;`run_all.py --build` 全量;產品架構稽核刷新;舊夾具重開;瀏覽器 gates | 照 `tools/geo261-queue.md` |

看板上的其他任務:
- 26:oracle → 核心探針。#251 合入後才能做。
- 27(PF-6 外層交易)、33(參數暫存移出 World)、34(參數卡使用次數):都會和 GEO-261 撞檔，**等 GEO-261 合入後再做**。
- 28:GEO-262 介面，等 #253 合入。

## 4. 使用者拍板過的決定(🔒,不得改動)

- 全文在 main 的 `決策佇列.md`。重要的幾條:
  - 2026-10-09 收尾拍板 A–L;
  - 2026-10-13 合併列車;
  - 2026-10-17 全部實作改由 Claude 接手;
  - Q-A「只准一軸(建議)」:新編輯拒絕第二軸相位差，已存的雙軸檔照舊可讀。
- 下角材現場規則，使用者多次糾正過，不得再犯:
  - 支撐可以移動：每個板邊承接要 ≥ X,副支間距要 ≤ 上限。只有找不到任何調整位置時才報衝突，並附物理理由。
  - 記號：起點相同、間距相同，整間每一排板一組。主支兩側位置相同是這兩點的自然結果，**不是另一條規則**,不准說成「必須對齊」或「必要錯位」。
  - 主支遇到 RC(壁柱邊界材或柱面)分段停住，算「連續到 RC」,不是衝突。
  - 板端縫靠近 RC 時，縫上的副支移到貼住 RC 角材。
- 使用者說過的每條規則，都要對應一個自動檢查和一個突變。

## 5. 硬規則(repo 的 `AGENTS.md` 是權威，先讀)

- 一律用繁體中文。
- `公理層.md` 是 SSOT,不得擅改。發現矛盾只回報;條文改動要先經使用者批准。
- 公理層閱讀器只准有一份，就是 `geometry-guide/公理層-閱讀器.html`,不准做離線版。
- `current_geometry.c` 統一 CRLF,只能用 Python 二進位模式讀寫。
- root `.gitignore` 是允許清單制，並全域忽略 `*.svg`。
- `git add` 寫明路徑。commit 結尾加 `Co-Authored-By: <實際模型> <noreply@anthropic.com>`;PR body 結尾加 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`。
- 不動 `.codex/`、`codex/*` 分支、`feedback/`。#213(SketchUp)與 #194 不處理。
- 不改任何安全設定，也不改使用者電腦設定。
- 定義推得出的事不問使用者，寫成定義推論;推不出的批次彙整後再問。安全批准一律交給使用者。
- 幾何推演寫成可執行的 oracle:建構 + 獨立檢查(突變、掃描)。
- 宣告修好前先做突變：把修正拿掉必須轉紅，失敗訊息要指得出病因。

## 6. 本資料夾的工具

| 檔案 | 用途 |
|---|---|
| `tools/synth_expected.py` | `python synth_expected.py <worktree> <ours> <theirs>`:逐 suite 三方合成 expected.json |
| `tools/ci_run.py`、`tools/ci_job.py`、`tools/wsl_ci.sh` | WSL 七項 runner(路徑寫死 WSL,在雲端用時要改路徑;照每個 SHA 自己的 `.github/workflows/integration-tests.yml` 跑) |
| `tools/stale_ledger.sh` | 只重跑 STALE 的突變再 `--check` |
| `tools/t17_ledger.sh` | 整份重產突變帳本 |
| `tools/focused_unittest.sh`、`tools/focused-modules.txt` | GEO-261 的 22 個模組 276 項 |
| `tools/geo261-queue.md` | GEO-261 切片順序 |
| `tools/incoming-train18-overlap.md` | 第 18 班 × GEO-261 重疊風險，含必須保留的行為 |
| `decisions/provisional-decisions-log.md` | Claude 代決紀錄(P-xxx);最終報告「照建議處理的部分」從這裡取 |
| `decisions/user-decisions-batch.md` | 待使用者決定的題目(Q-A…Q-E) |
