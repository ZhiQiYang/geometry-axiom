# Codex 全面接手交接文件(2026-10-21,Claude → Codex)

使用者在 2026-10-21 決定:接下來的工作全部交給 Codex。這份文件寫目前的狀態、待辦的優先順序與必守規則。本分支只放交接資料,**不要合併到任何分支**。

## 0. 先讀:必守規則

- 語言:除了 commit 訊息用英文,所有說明一律用繁體中文。
- **`公理層.md` 是 SSOT**,不得擅改;發現矛盾只回報。條文還沒定案的功能,不得實作。
- **公理層閱讀器只准有一份**:`geometry-guide/公理層-閱讀器.html`,只能由 `geometry-guide/sync_axiom_reader.py` 原位同步(有五道完整性 assert,細節見 `AGENTS.md`)。不准做「離線版」。
- `current_geometry.c` 是**統一 CRLF**,要掃它一律用二進位模式讀。root `.gitignore` 是**允許清單制**,新目錄要明列才收得進 repo,而且全域忽略 `*.svg`。
- 層級依賴只能單向:模板 W(`geometry-templates/`)→ 核心 K(`geometry-core/`)。H(`geometry-app/`、`geometry-web/`)可以組合兩者。K 不得 include W/H,W 不得 include H。
- **P-177**:不准為了效能改守門流量,也就是候選、驗證、seal、publish 的次數與時機。
- 不准 force push,也不准改寫已推出的歷史。`git add` 只加明確路徑。
- 任何改到 `tests/*.py`、或 `current_geometry.c` include 閉包的變更,都會讓突變帳本 `tests/mutants_results.json` 過期。帳本只能在最終 SHA 上整份重產:`python3 tests/mutate.py`,接著 `python3 tests/mutate.py --check`,約 1.5–2 小時。
- 改了 manifest 會碰到的檔案、或新增可執行檔時,要重產產品架構收據(manifest/scan/report/receipt 四檔)。重產工具見 `scripts/` 與第 5 節。
- **合併前必讀 PR 上最後一次 push 之後的全部留言**,特別是使用者貼的【ChatGPT 審查】。只要有未逐項回覆的阻擋或須改,就不准合併。把 PR 分支快轉併進整合分支,也算合併。這條 Claude 違反過兩次(#307、#321),不要再犯。
- GitHub Actions 被帳號計費擋住:每個 job 都 0 步驟失敗,不算任何證據。正式裁判是在 Linux 上跑等同 CI 的 7 項:native(`ulimit -s 16384; python3 tests/run_all.py --build`),以及 6 個 browser job(canvas、assembly、documents、grid、space、timber,定義見 `.github/workflows/integration-tests.yml`)。
- 你的環境連不到 GitHub API。所以開 PR、改 PR 正文、留言、合併,都由**使用者**做。你把要貼的內容寫成檔案,推到你的分支,並在回報裡寫清楚「請使用者在 PR #N 做什麼」。
- 宣告修好之前要做突變自證:把修正拿掉必須轉紅,失敗訊息要指得出病因。
- 使用者的待決事項(第 7 節)**不准代為決定**。

## 1. 目前狀態

### 1.1 GEO-261(PR #288)— 最優先

- 整合分支 `architecture/geo261-integration-20261016`。**最終 SHA `7dae5f21c7ca401e660450d437e60ba566218da8`**,已包含:
  - roots exact-set 修正:rootcat 分支 `2dad221e`,合入 Codex 的 `4e0def58`,另補 timber 面名 ↔ 局部側檢查;
  - #321 來源圖雜湊索引 `9f21280d`;
  - assembly killed 判準修正:`661d72bf`、`d3746972`、`390a5f33`;
  - 架構收據重產 `ec1238cd`;
  - #321 證據 `a8931316`;
  - 帳本整份重產 `7dae5f21`:killed 70、crashed 1(M20,main 上也一樣)、equivalent 4、retired 3,`--check` 為 0。
- **7dae5f21 上的 7 項**(WSL 收據 `canvas-7dae5f21/receipt-7jobs.json`):

  | job | 結果 |
  |---|---|
  | native | 綠,5175/5176(唯一 skip 是允許清單內的 GDI),`mutation:check` 與 `py:test_product_architecture` 都綠 |
  | assembly | 綠,150 |
  | documents | 綠,47 |
  | grid | 綠,350 |
  | space | 綠,242 |
  | timber | 綠,79 |
  | **canvas** | **紅,900/901**:P52-5 失敗,接著在 P68 FATAL `Audit timeout: !oc.busy && !document.querySelector('#datum-manager')?.dataset.busy`(log 在 `canvas-7dae5f21/canvas-run1-job.log`) |

- **P52-5 從沒失敗過**:之前 13 次 canvas 都是 PASS 或沒跑到這裡,這是第一次。測試在 `geometry-web/cdp_test.js` 約 6215–6236 行。流程是:點擊 (2000,1500) 放置 → `sleep(400)` → `apiRequest('references')` 找 id=3 的 timber。這次結果是 `g` 為 undefined,也就是 400 毫秒內 timber 3 還沒出現。
  - 可能的原因:
    1. 並行負載,當時同時跑兩個 job;
    2. 最終 SHA 新增的 roots/面身分驗證(Python `geometry-app/geometry_app/model_sources.py`、W `geometry_woodworking/model_sources.py`)讓放置後的模型更新變慢。
  - 單獨重跑 canvas(`canvas-7dae5f21/canvas-r2-job.log`)沒有得到有效結果:建置步驟 `npm run build` 卡了 18370 秒才結束,測試沒有真的跑(結束碼 124)。原因不明,可能是環境問題。
- 最終 SHA 上還沒跑的關卡:
  - Q38 gate:`tests/section_profile_mutation_check.py`,跑法見 `scripts/q38_gate.sh`;
  - §7 卡片參照突變:`geometry-core/card-reference/run_mutations.py` 與 `run_axiom_mutations.py`,跑法見 `scripts/card_ref_mutations.sh`;
  - P-189 效能複測:main `adbaebf9` / base `3e600772` / final,同法交錯量測,`scripts/fix_verify.sh` 與 `scale_compare2.py`。
  - 舊包 replay 已由 native 的 `py:test_geo261_model_base_replay` 涵蓋,已綠。
- ChatGPT 對 #288 的最新審查,是在 head `390a5f3` 上做的:4 阻擋、1 須改。前 4 項(roots、整合驗收、架構登記、P-189 整合)在 7dae5f21 都已處理或正在驗;第 5 項 PR 正文,Claude 已在 #288 正文最上方加了 10-20 現況段,head 寫的是 `96ade86b`,要改成最終 SHA 與最終證據。

### 1.2 其他在途 PR / 分支

| 項目 | 狀態 |
|---|---|
| **#323** `codex/geo261-load-residual-20261020`(你上一件工作) | opus 審查**不可合**:2 個 harness 編不過,`py:test_mutation_anchors`、`py:test_geo261_contact_sources` 轉紅,失效突變覆蓋不足。修正提示詞在 `prompts/PROMPT-C-load-residual-fix.md`。屬於 #300 的前置工作,**不進 #288 的最終 SHA**;#288 合進 main 之後,base 改成 main。 |
| `fix/framing-oracle-review-20261020`(Claude 子代理所做,**沒有 PR**) | 3 個 commit(`e9ca81e2`、`9b04a3c8`、`1126991c`),內容是回應 ChatGPT 對 #251 的審查(head `3d858c3`,3 阻擋 1 須改,這些已隨 #307 誤合進 main),以及 #318、#319。驗收與審查都沒完成。 |
| #322 | column/beam 的 snapshot 缺 `faces` 時,丟出未分類的 KeyError(既有問題,修法一行)。 |
| #300 | 容量 64→512。草稿在 `drafts/issue300/`(含 bench)。前置條件見 #300 的 10-20 留言:剩餘超線性熱點是 `contact_order` 的線性查找、擋面收集的 O(n²) 去重,以及 `geo_eval_depend`。 |

### 1.3 GEO-261 合入 main 之後的列車(草稿在 `drafts/`)

- **#299 + #316 只能用 combined 補丁**(`drafts/combined/rebased-546e2eb2/patch.diff`);兩個單獨補丁不能先後套用。接著是 **#314**(`drafts/issue314/rebased-546e2eb2/patch.diff`)。
- 以 546e2eb2 為基底,兩份都 `git apply --check` 通過,也可以疊加(#314 在 `current_geometry.c` 會 offset -34 行)。產生器在 `drafts/_gen`,設 `BASE_REV` 環境變數即可重產。
- 注意事項:
  - #314 的突變編號要從 **M99** 起,M89–M98 已被 #299 與 #316 用掉;
  - 套用後要重產架構收據、整份帳本,並執行 `sync_axiom_reader.py`;
  - `geometry-web/grid_inspector_rename_test.js` 的行號已變,#314 的 TESTS.md §6 過期;
  - P72B 在 `cdp_sections.golden.json` 釘了 50 個斷言,不可改變。
- #314 的設計稿有 3 處語意模糊,實作前要先審查,見 `drafts/issue314/`。

## 2. 優先順序(建議)

1. **把 #288 收尾**:
   - 查清 P52-5:在 main 與 7dae5f21 上量「點擊放置 → timber 出現在 `references`」的實際耗時;
     - 若是產品退化,修產品;
     - 若只是固定 `sleep(400)` 太短,改成有上限的輪詢等待,不能放寬斷言,並附修改理由;
   - 重跑 canvas 完整 job;
   - 跑 Q38、§7、P-189 複測;
   - 產出 #288 新正文檔案 → 使用者貼上並請 ChatGPT 複審 → 逐項處理 → 使用者合併。
   - 若修正改到產品碼或 `tests/*.py`,帳本要整份重產、7 項要全部重跑。
2. **#323**:依 `prompts/PROMPT-C-load-residual-fix.md` 修正。
3. **`fix/framing-oracle-review-20261020`**:審查、驗收,產出 PR 正文。
4. **#322**。
5. GEO-261 之後的列車:combined → #314。
6. #300(要先完成 #323,並處理剩餘熱點)。
7. 收尾總報告:草稿在 `report-parts/` 與 `drafts/closeout-report/`,要補上 10-20 以後的事件。

## 3. 代決紀錄

`notes/provisional-decisions-log.md` 的 P-001~P-190,是 Claude 依使用者 2026-10-09 授權 L 做的暫定決定,使用者可以推翻。和這次交接最相關的幾條:

- P-177:不改守門流量。
- P-186:native timeout 35;已被 P-189 部分推翻。
- **P-189**:#288 的載入效能門檻是 N=16/32/48/64 每一點 fix/main ≤ 2×,而且 dump 逐位元組相同。已達成:WSL 量得 0.90/1.18/1.56/1.94×。
- **P-190**:frame 旋轉可讓面名對到別的世界面,判為文件級殘餘風險,寫在 `geometry-app/native/MODEL-SOURCES.md`。

新的代決請照同一格式記錄:選項、採用、理由、如何推翻。

## 4. 執行紀錄

`notes/wsl-pending-after-game.md` 是 Claude 的流水帳,依時間順序記錄,含各收據的位置。收據多半在使用者電腦的 `D:/geometry-axiom-work/`,你讀不到;重要數字都已寫進本文件與各 PR 留言。

## 5. 腳本(`scripts/`,原本在使用者 WSL 上跑,路徑需自行調整)

- `fix_verify.sh` + `scale_compare2.py`:三方建 bridge,做 `loadfile`+`dump` 等價比對與交錯計時。
- `load_profile.sh`:gprof 剖析一次 loadfile。
- `t17_ledger.sh` / `stale_ledger.sh`:整份重產帳本 / 只刷新過期項。
- `q38_gate.sh` + `q38_controls.py`:Q38 斷面突變閘門。
- `card_ref_mutations.sh`:§7 卡片參照突變。
- 架構收據重產 driver 不在這裡:它在使用者電腦上,而且依賴 Windows 短 TEMP 路徑。最終 SHA 那一份已由 Claude 產生並提交(`ec1238cd`)。若之後新增可執行檔,請照 `geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md` 的規則手動登記並重產,三條驗證都要過:
  - `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`
  - `python -B tests/test_architecture_contract.py`
  - `python -B tests/test_product_architecture.py`

## 6. 場景產生器

`prompts/PROMPT-A-source-index.md` 末尾附有 `mini_gen.py`(single 家族,N 支角材)。它在 N=16/32/48/64 與 `drafts/issue300/bench/gen_scene.py` 的輸出逐字相同。

## 7. 使用者待決事項(不准代決,只能列出並附建議)

- 壁柱的處理:doubling(併料)或 retreat(退縮)。
- 柱跨牆階:物理上可施工,但核心 I19 不准邊界材端面頂非 boundary 的料;要能施工就得改 I19(路線 B)。這屬公理層變更。
- 搜尋索引是否排除 `D:\WSL`、`D:\geometry-axiom*`(系統設定,由使用者自己做)。
- 是否刪除 `D:\t`(`D:\t2` 不要刪,架構 driver 需要短 TEMP 路徑)。
- 是否刪除分支 `local/rule-lines-with-card-wait-20261008`。
- 是否把 WSL 搬到 SSD:USB HDD 飽和曾造成 canvas 假紅。
- GitHub Actions 計費。
- 是否推翻 P-186 / P-189 的效能門檻設定。
