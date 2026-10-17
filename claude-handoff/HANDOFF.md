# 雲端 Claude → 本機 Claude 交回(2026-10-17 18:00 台北)

本檔原是本機 Claude 13:20 交給雲端的交接。雲端 Claude 在 13:49–18:00 依使用者指示接手，使用者要求「階段性完成後停止」,所以這一段做完列車就收工。**新增的第 0 節是雲端這一段的交回**;第 1–6 節保留原交接，其中第 3 節表格已改成收工時的狀態。

本機回來時：一律以遠端分支的實際 head 為準(`git ls-remote`),本檔只是收工當下的快照。

## 0. 雲端這一段(13:49–18:00)

所有雲端結果都是「**雲端預跑，非正式 WSL 收據**」。環境:Ubuntu 24.04.5、gcc 13.3.0、Python 3.13.16、Node 22.22.0、Chromium 153.0.8010.0(P-162)、`ulimit -s 16384`。

### 0.1 收工時的分支 head

| 項目 | 分支 | 交接時 | 收工時 | 誰改的 |
|---|---|---|---|---|
| main | `main` | `c144c013` | `02baea2c` | #296(S6 🔒 決定落 main,交接後由他人合併) |
| 列車(新) | `train/geo262-honesty-20261017` | — | `eeb9d239` | 雲端 Claude |
| #253 | `feat/card-reference-core-20261015` | `33e655d6` | `e180a268` | 雲端:run_mutations.py 不再寫死 36(P-163) |
| #293 | `fix/receipt-tombstone-capacity-20261017` | `6d5bb03c` | `baa81f61` | 本機(交接前一刻) |
| #294 | `fix/mutation-bridge-crash-honesty-20261017` | `3adc84ff` | `f5981035` | 本機 `157166f1`(交接後)+ 雲端審查修正(P-165) |
| #295 | `test/s1-s7-core-scenes-20261017` | `ba94f0a7` | `a03c2dab` | 雲端審查修正(P-164) |
| #260 | `proposal/stagger-one-axis-wording-20261016` | `3a524bd5` | `f796c5c9`(本機)| 雲端改稿在 `claude/wip-pr260-revise-20261017` `4e7bdf5c`,**未複審、未推到 #260**(P-168) |
| #279 | `architecture/geo261-native-source-graph-20261016` | `96e06218` | `1fc45f73` | 雲端修正 `1fc45f73`(P-166) |
| #288 | `architecture/geo261-integration-20261016` | `43305271` | `43305271` | 雲端整合在 `claude/wip-geo261-288-integrate-20261017` `f62ebb8b`,**未審查、未推到 #288**(P-167) |
| 下角材班 | `train/framing-20261017` | `f1fd146f` | `f1fd146f` | 沒動 |

### 0.2 做完的

- **列車** `train/geo262-honesty-20261017`(PR #298,draft,**未合併**):main `02baea2c` + #253 + #293 + #294 + #295(P-161),全部 merge commit。
  - 每次合併都用 `synth_expected.py` 三方合成,結果都等於 git 自動合併。
  - 正典閱讀器只用 `sync_axiom_reader.py` 重同步(只動追溯資料),`--check` 與 `test_axiom_reader.py` 51/51。
  - 突變帳本整份重產:78 筆,killed 70 / crashed 1(M20,同以往)/ survived 0 / equivalent 4 / stale 0 / blocked 0 / invalid 0 / retired 3,`--check` exit 0。M78–M88 全數 killed。
  - `run_axiom_mutations.py`:V01–V05 全數 killed。`run_mutations.py`:53 筆全數 killed,每個還原控制組重新編譯皆綠。
  - 最終 head 七項(P-169):

  | job | exit | pass | fail | skip | 秒 | CI 時限(分) |
  |---|---:|---:|---:|---:|---:|---:|
  | native | 0 | 3525 | 0 | 1(GDI,具名允許) | 1089 | 15(超出，在 3 倍內) |
  | assembly | 0 | 150 | 0 | — | 217 | 15 |
  | documents | 0 | 47 | 0 | — | 48 | 10 |
  | grid | 0 | 350 | 0 | — | 507 | 15 |
  | canvas | 0 | 2211 | 0 | — | 2103 | 35(超出 3 秒，在 3 倍內;84 段與 golden 相符) |
  | space | 0 | 242 | 0 | — | 258 | 15 |
  | timber | 0 | 79 | 0 | — | 117 | 20 |

  兩個 job 並行，同時有審查子代理在編譯，不是排他執行。
- **#293**:審查員的 M8b、M7b 各以兩種寫法重建,新測試都轉紅、訊息指得出病因;還原後 17/17。契約第 11、20 行已更正。
- **#295**:7 個場景原生實跑，輸出與讀程式推出的預期逐字一致。opus 審查後補 p8b/M88、p9 改 u=2750(對齊 #251 golden)、新場景移到 TESTS 最後(舊突變的 killed_by 不被擠掉)。
- **#294**:opus 審查(5 須改)→ 子代理修 → 原審查員複審無阻擋。兩項後續見 P-165(都是現行測試沒有的構造情境)。
- **#253**:ChatGPT 審查要的「最終 head 完整驗證」由本列車提供(雲端預跑);正文與 `review-p154-20261016/summary.json` 仍描述舊 head `300cb953`,PR 正文已在最前面加「目前狀態」段，原文保留為歷史。
- **GEO-261 #279**:22 模組在雲端跑出 276 項 21 敗;追到 5 個根因(1 產品 + 4 夾具)修好，276/276(P-166)。opus 獨立審查：修正本身無阻擋;run_all 對照(96e06218 vs 1fc45f73)少掉的正好是那 21 項，沒有新增失敗。已快轉推到 #279,PR 留言寫明孔頂點修正改變 main 行為。須改未做:孔頂點回歸測試(突變「h 後非數字」存活)、參數圖 oracle 改比邊集合、vertex ledger 場景補「分量 id = 有帳 boundary id」陷阱。#279 本身另有既有阻擋:`tests/binaries.py` 的 unity 建置在 gcc 編不過(#288 WIP 的 `169ecf4c` 有修法，未審查);22 模組以外的 GEO-261 suite 在 base 與 fix 同樣失敗:placement_sources 8、timber_support_projection 13、domain_decoupling_proposal 23、candidate_cache 2、wood_grid_application 2、assembly_candidate_impact 4、axiom_reader 6、binaries 5 等，名單在審查報告。
- **GEO-261 #288**:雲端重做 main + #279 合併(P-167),22 模組 276/276、第 18 班七套參數測試 60/60;完整 run_all 只跑到 13/213。**未審查**。
- **#260**:三件事查核 + opus 審查(1 阻擋 6 須改)+ 改稿(P-168)。改稿未複審。

### 0.3 沒做完／卡住

- 列車:正式 WSL 七項沒跑(雲端碰不到 WSL)。合併需要使用者同意以雲端結果代替，或本機用 WSL 收。
- #288:要 opus 對抗審查、完整 `run_all.py --build`、瀏覽器 gates、整份重產帳本。三項既有失敗沒修(M11 錨點、`test_assembly_candidate_impact` 0/4、W ops unplaced negative control),都在 `ab609924` 就失敗。
- #260 改稿:要再一輪 opus 複審，通過後快轉推到 #260。
- #294 後續兩項(P-165)、#295 記錄項(1mm 容差、I19 嚴格小於等一階突變補 M89 起、核心 V_EXTENSION 訊息未指名定位邊與區間)、#253 記錄項(報告加 expected 數與登記 sha、錯誤訊息印預期/實得;7 個 P142 測試沒有對應突變)。
- 下角材班 `train/framing-20261017` `f1fd146f`:雲端沒動。canvas 在本機 WSL 為 P83 的 CSV 下載逾時(2177 斷言全過、0 失敗),判定環境問題，需要**排他重跑**;grid/space/timber 結果請以本機紀錄為準。

### 0.4 待使用者決定(集中一批)

1. 列車要不要以雲端結果代替 WSL 收據合併(或等本機 WSL)。
2. #260「什麼算舊檔」三選一(建議選項一：只守提交，不守整體取代)。全文在 `claude/wip-pr260-revise-20261017` 的 PROPOSAL.md 第 43–177 行。
3. #279 孔頂點引用修正會改變 main 的現行行為(由「一律拒絕」變「可引用」,依 D6a(a)),是隨 #279 進還是另開單修 main。
4. #288 兩個設計點：候選順序 ledger 放 H 還是 K;unity 建置的修法。

### 0.5 雲端工具(本次新增，見 `tools/`)

- `tools/cloud_ci.sh <sha> <job> <port>`:照該 SHA 的 workflow 跑一個 job(native 或六個瀏覽器之一),每個 job 自己的乾淨 worktree 與**短 TMPDIR**(長路徑會讓 Chrome 崩潰)。瀏覽器用 `CLOUD_CHROME` 指定(雲端內建 141 跑不了 pdf.js,見 P-162)。
- `tools/cloud_ledger.sh <worktree> <out> <stack>`:整份重產帳本，核心兩組 + bridge 一組各自 worktree 平行跑，用 `mutate.save_records` 合併後 `--check`。

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

## 3. 在途工作(2026-10-17 18:00 雲端收工時;原 13:20 版本見 git 歷史)

| 項目 | 分支 / head | 狀態 | 下一步 |
|---|---|---|---|
| 列車 #253+#293+#294+#295 | `train/geo262-honesty-20261017` / `eeb9d239`,PR #298(draft) | 雲端七項全綠、帳本 78 筆 `--check` 0、53+5 筆 GEO-262 自訂突變全 killed(雲端預跑) | 使用者同意以雲端代替就合併;否則本機 WSL 七項(`tools/wsl_ci.sh eeb9d239 all`),綠就合併、關 #253/#293/#294/#295 |
| 下角材班 = #251 + #254 | `train/framing-20261017` / `f1fd146f` | 雲端沒動。WSL:native、assembly、documents 綠;canvas P83 CSV 下載逾時(2177 斷言全過、0 失敗),判定環境 | canvas 排他重跑;grid/space/timber 以本機紀錄為準;七項綠就開列車 PR。注意列車 #298 先進 main 的話要 merge main 並重產帳本 |
| #260 條文稿 | PR 分支 `f796c5c9`;改稿 `claude/wip-pr260-revise-20261017` / `4e7bdf5c` | 審查 1 阻擋 6 須改都已改稿;「什麼算舊檔」三選項待使用者(P-168);改稿**未複審** | opus 複審改稿 → 快轉推到 #260 → 交使用者看稿與選選項 |
| GEO-261 #279 | `architecture/geo261-native-source-graph-20261016` / `1fc45f73` | 22 模組 276/276(雲端);修正無阻擋;PR 層級既有阻擋(unity 建置) | 補孔頂點回歸測試等 3 項須改;unity 建置修法隨 #288 審查 |
| GEO-261 #288 | PR 分支 `43305271`;整合 `claude/wip-geo261-288-integrate-20261017` / `f62ebb8b` | main 02baea2c + #279 修正已合入(15 衝突檔、第 18 班移植);22 模組 276/276;run_all 只跑 13/213;**未審查** | opus 對抗審查 → 完整 run_all → 推到 #288;設計兩點待使用者(P-167) |
| GEO-261 其餘 | 見 Astra 交接 §3 | 同交接時 | 照 `tools/geo261-queue.md` |

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
| `tools/cloud_ci.sh`、`tools/cloud_ledger.sh` | 雲端預跑七項的單一 job、整份重產帳本(見 §0.5) |
| `decisions/provisional-decisions-log.md` | Claude 代決紀錄(P-xxx);最終報告「照建議處理的部分」從這裡取 |
| `decisions/user-decisions-batch.md` | 待使用者決定的題目(Q-A…Q-E) |

## 7. 14:30 更新(本機子代理全部因每週額度停在 20:00 前)

- 下角材班 f1fd146f:native/assembly/documents/grid/timber/space 綠(space 重跑 474 s 綠)。canvas 重跑:completed=true、2211 斷言過、0 失敗、golden matched,但 `uncaughtBrowserExceptions: 1` → exit 1。第一次跑是 P83 CSV 下載逾時。還沒查出是哪個例外(log 裡各段「no uncaught browser exceptions」都打勾);下一步：拿同一 job 在 main 上跑基線比對，或從 CDP 收據找例外原文。本班沒改前端。
- GEO-261 #279 `96e06218` 完整 22 模組 276 項：255 過、21 列失敗(約 12 個測試，見 `D:/geometry-axiom-work/focused-geo261-276-96e06218/failures.txt`;雲端看不到就自己重跑)。修復子代理剛開工就被額度打斷，未推任何 commit。
- #288 整合 merge 子代理被打斷，工作區 `D:/geometry-axiom-work/geo261-integration` 可能有未提交的半成品;遠端仍是 43305271。
- #260:opus 審查 f796c5c9 有 2 阻擋 11 須改;裁定見 `decisions/provisional-decisions-log.md` 的 P-162(只准一軸改放 W、撤 K 補句;舊雙軸檔改值交使用者;C 補括號;D2/D3 移出)。改稿子代理被打斷,遠端仍是 f796c5c9。
- #293 `baa81f61` 審查意見已全處理，可上列車。
- #294 `157166f1` 已依審查改成「連三次存取違規才 crashed」;增量複審被打斷。
- #295 `ba94f0a7`:審查有阻擋(閱讀器沒同步,`test_axiom_reader` 會紅)與須改(M86 被 M05/M06 涵蓋);改修子代理被打斷。
- #296 已合併(main 02baea2c):把 S6 🔒 紀錄補進 main。
- Grok 在 `D:/geometry-axiom-work/grok-core-probe` 做看板任務 26(core-probe),分支 `feat/framing-core-probe-20261017`。
