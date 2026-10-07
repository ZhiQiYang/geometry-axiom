# 2026-10-08 輔助核對

本檔記錄當次開工時的 SHA、之後 main 被合併推進的事實、證據缺口與 390px 窄畫面補驗。它不宣告產品驗收完成，也不取代 `公理層.md`。

## 能力與協作

- 終端：PowerShell 7.6.6，已執行。
- Git：2.55.0；GitHub CLI 2.96.0，已執行 `fetch` 與 `gh pr view`。
- 瀏覽器：沒有瀏覽器 MCP。Chrome 安裝於 `C:\Program Files\Google\Chrome\Application\chrome.exe`。390px 追查用專案 `cdp_test.js` 的 `--headless=new`，不是已連線的互動瀏覽器。
- 多 agent：文件審查與證據整理各一名子代理並行。瀏覽器 QA 只有本回合一位 owner。沒有第二個瀏覽器行程。

## 綁定

| 項目 | SHA / 狀態 |
|---|---|
| 開工時 main = origin/main | `6562fa53d90de22b3e5492f2083199b26377a8c2`，工作樹乾淨 |
| 收尾時 main = origin/main | `7fb9ac1df7f4508f3c12e7c7cef6b0886bae4ea5`（Merge pull request #163）。本分支由此切出 |
| PR #163 開工 head | `b761ea43abde8b715ce8f102d78607c88822a0c0` |
| PR #163 合併前 head | `e63cef513fb9c804b3ecec0c6d27b8e8a829ea4b`（已併入 main） |
| PR #162 head | `c0e58e2f78b4412a2ff4ef48700cd41ab3cc79ea`，draft，未合併 |
| #162 受測產品來源 | `66a4c89d985e5e7a34f602ff1d085c7a9943c883` |
| #162 證據 commit | `60bf007947c263dc380d7124c37955808fec7e2c` |
| #162 runtime（證據包所記） | `503bdfe8b4762ed26720f6b81eb4b7a667bdef94cf41adfc3ef427080098c480` |

開工時沒有 8700–9900 監聽。Python pid 37636 的命令列是 `python.exe -`，沒有停止它。若干 worktree 在收尾時被 Git 標成 prunable；那些目錄不是本回合刪的，也沒有執行 `worktree prune`。

## 一、產品核心說明（PR #163）

開工審查的是 `b761ea43` 的 `geometry-web/README.md`。合併前又有 `c6cd572`、`e63cef5`，已改正：任意概念自由組合、單數定位線、綁定會生成角材、把參考網格標成施工面材。那些句子不再重改。

併入 `7fb9ac1` 之後仍與公理或生成契約不一致的句子，已在本分支的 README 改掉。對照來源：

- 公理 D32:471–480、D33:482–488、D34:490–496、D10a:180–184、D29、D30:427–432
- `geometry-core/assembly.inc:71` 接受 `ortho-split`
- `geometry-core/assembly_generation.inc:16–39,67–74`：三個 member、各一條 guide、primary `+v`、secondary `+u`、depth `+n`、接觸面 A、截面方向 A；重複 guide 拒絕；主支兩端必須是同面既有邊界材
- `geometry-core/ASSEMBLY-GENERATION-PROPOSAL.md:10–16,36–45`

未改公理，未改程式。D34 正文只寫「同向／端接」與接觸面 A、截面 A／B；`+v／+u` 是已採納生成契約與程式的現行限制，README 現在同時寫出，避免把「同向」讀成任意軸向都能生成。網格快捷位置對照 `geometry-web/grid-system-workspace.js` 的九個按鈕（左上到右下）與「其他精確比例」；D30:427–433 保存的是格內有理比例，不是只准那九點。

## 二、驗收證據缺口（PR #162）

未重跑已完成的整套測試。未找到不等於功能失敗。

### 模型庫十項中途操作保護：未找到

PR #161 正文把通過證據放在 `/tmp/geometry-159/guard-qa/candidate-final/`。#162 證據包內文沒有 `guard-qa`、`10-case` 或逐例 log。本機檔名搜尋 0 筆。WSL `\\wsl$\Ubuntu-24.04\tmp` 存在，其下沒有名稱含 geometry 的目錄。

仍缺：原腳本、十筆逐例結果、命令、退出碼、受測 head／runtime 前後收據。已點名類別只有 pending native Undo、重入拒絕、Save 拒絕、remove 拒絕、close／reopen／context／session 遲到回覆、真 readonly lease。回收文字沒有第 10 個案例 id。Space 228 與 Create／grid 138 不能代替。

決策、本回合不新造測試：沒有第 10 個 id 就不寫新的十項腳本，避免把新設計誤當成遺失的原紀錄。

### 模型庫 155 項 UI：部分找到

包內 `historical/model-a49d/ui-settled-v2/ui/receipt.json`：命令 `python3 /tmp/geometry-rc-space-final/ui-settled-v2/browser_ui.py`，exitCode 0，head `a49d2a5470abf6e9db4e14573535476d05647c21`，runtime `2dd5d975ce57e2d4cd8728915a4dd31a25bda7c998cedc84a61344dda0d290c9`。`gate.log` 有 155 行 `pass:true`，結尾 `COMPLETE 155`。這是舊 head 的通過收據，不是 `66a4c89` 重跑。

仍缺：`browser_ui.py`、`ui/artifacts/results.json`、初始場景失敗到 fixture 修正的原檔（`actual-initial-world.scene`、`final-world.scene`、diff、diagnostic）。`reviews/model-ui-gates-review.md` 只敘述：原 ui/ 在 52 項後失敗，差一行 `canvas-pos boundary 1 60 60`；修正是等 native hasPos/cx/cy 與畫面一致。敘述不能代替那些檔。本回合沒有重跑 155。

### 若日後只補缺件

十項：找回原腳本就用它的原命令，在隔離 port、專用 TEMP、`fresh:true` 的 `/runtime` 上重跑，逐例記命令與退出碼。腳本確定遺失且第 10 個 id 已由原作者補上之後，才為已點名類別各寫一筆：pending 期間只有一筆 Undo；重入、Save、remove 被拒絕；遲到回覆不續租、不改世界；readonly lease 拒絕庫寫入。判定用 DOM、歷史長度、native dump、page error 與 download 為 0。

155：不重跑 155 條。只重現「畫面 hasPos 已真、native 尚未寫完就抓初始 World」（預期差那一行 canvas-pos），以及 fence 第三次才 true 才抓 World。保存場景 diff、命令與退出碼。

## 三、文件與實際狀態

`c0e58e2f` 已把過早完成改成驗收尚未完成。該句不必再改。main `6562fa53` 沒有把 #162 寫成已合併或已完整驗收。收尾時的 main `7fb9ac1` 只多了 #163 的說明合併。

建議改 #162 分支、本 PR 沒有改那裡。下列是 `c0e58e2f78b4412a2ff4ef48700cd41ab3cc79ea` 上的原句與最小替換。

1. 未驗。`BACKLOG.md` 驗收夾具那一則的後半現在是：「TEMP 模型庫流程的初始 World 改在原生卡片位置與畫面一致後取樣，仍逐字核對全部 World，不忽略位置差異。原紅、因果反例與修正後收據均保留。」前半 Space dump／228 floor 不動。後半改為：「TEMP 模型庫流程的初始 World 取樣修正，目前只有 `reviews/model-ui-gates-review.md` 的敘述：原 ui/ 在第 52 項後失敗，差一行 `canvas-pos boundary 1 60 60`，修正是等 native hasPos/cx/cy 與畫面一致。`browser_ui.py`、`results.json`、場景 diff 與 diagnostic 原檔沒有收進證據包，不能稱為已保留的收據。」
2. 未驗。`tests/release-evidence/20261007/README.md` 現在寫：「每個 scope 的原始 head、runtime、結果、限制與失敗前序均保留，沒有把舊結果重標為新 head。」改為：「已收錄的 scope 保留原始 head、runtime、結果與限制，沒有把舊結果重標為新 head。模型庫十項中途操作保護，以及 155 項從初始場景失敗到 fixture 修正的前序，尚未收錄。」
3. 未驗。同 README 在「收集時作者記錄」那句之後補：「`manifest.json` 的 `pending: []` 與 `finalCandidate.state` = `local-candidate-acceptance-complete` 是 `generatedAt` `2026-10-07T14:19:14.052552+00:00` 的收集快照；`releaseApproval` 仍是 `not-evaluated`。`pending` 長度 0 不表示上述兩項缺口已關閉。`c0e58e2f` 只否定了完成這個用詞，沒有改 manifest 原 bytes。」不要改 manifest 或 tar。
4. 環境受阻。PR #162 正文目前只引 run `37636065503`（commit `60bf007`）。補：head `c0e58e2f` 的 run `37650122454` 同樣 7 jobs、steps 長度 0。annotation（job `112890959152`）：「The job was not started because recent account payments have failed or your spending limit needs to be increased.」run `37636065503` 的 attempt 1 與目前 attempt 2 也是 7 jobs、steps 0。這不是產品失敗，本機收據也不能當成遠端 CI 通過。不調整付費設定。

分類：程式已修與測試通過只引用各證據自己的 head，不把舊結果改標成 `66a4c89`。CI 兩次都是環境受阻。#162 未合併。

## 四、390px「Rule line control unreachable」

與負尺寸 SVG 色帶不是同一件事。2026-10-08 00:47 左右 `D:\geometry-axiom-bqa` 的 `main-negative*` 紀錄只屬於色帶，不能為本項結案。

### 先前證據（#134 head，不是本候選的新跑）

- head `77c3847f32b2ba0616bab6c8d0c8370082c4941c`，port 8874，`GEOMETRY_GRID_SYSTEM_ONLY=1`
- 4 次裡 2 次失敗，都在 P88、390 寬、同一控制項 `[data-rule-cell-i]`，通過斷言 289，尚未印出「390 單規則引用數」
- 失敗座標：一次 `y=1411.515625`，一次 `y=2021.515625`；`w=134`、`h=44`、`hit:false`、`disabled:false`
- 測試把視口設成 390×900（`grid_rule_lines_test.js`）。舊 README 寫 844，與測試碼不符
- `cdp_helpers.js` 的 `makeCtl` 只呼叫一次 `scrollIntoView`，然後最多量測 12 次。量測迴圈不會再捲。舊紀錄寫「12 次 scrollIntoView」與程式不符
- 失敗當下的 UI 黑盒子：構件分頁點在視口內，接著 Home／Enter 的目標是 `body`，不是規則 select。候選後來加了 `focusedCtl` 與 Tab／Enter 焦點保留；那兩筆失敗發生在這個改動之前

`cdp_helpers.js` 與 `app.css` 在 `77c3847` 與 `c0e58e2f` 之間沒有 diff。`grid-rule-lines.js` 與 `grid_rule_lines_test.js` 有 diff。所以舊的 2/4 不能直接改標成候選已重現或已消失。

### 本回合在候選上的兩次執行：未到達 390

- 候選 `c0e58e2f78b4412a2ff4ef48700cd41ab3cc79ea`，tree `15fc840ead0e7b7f115d123a76142b405e562403`
- 隔離 worktree 已移除。port 8891，CDP 9491，回報目錄 `C:\Users\Yang\AppData\Local\Temp\geometry-aux-20261008\fb-8891`
- bridge 沿用 `bridge-c5955d469b13.exe`。`77c3847` 與 `c0e58e2f` 的 bridge 閉包 diff 為空，source hash `c5955d469b13525589461873ff6c1b9df0058d0c2c4399cf1af46102be346033`
- `/runtime`：`fresh:true`，root `D:\geometry-axiom-aux390`，pid 17636，version `05a669d49262706118e414caa5c637604e0a04cbb8b31fca0c422198e4cf9348`
- 該 version 含一處失敗後才記錄捲動父層的診斷。兩次都在判定前就停住，診斷沒有執行，也沒有多一次捲動或加長等待
- 兩次都是 exit 1。P70 通過 52、失敗 1。致命句都是「配置卡片可拖動且不改錨定幾何」。拖曳前後 `cx=500`、`cy=328`、cell 與 translation 全相同。點擊落在同一卡片框 `x=1113.05`、`y=484.88`
- 因此沒有進入 P88，沒有執行 390 的規則線點擊或 Tab／Enter。本項在候選上的結論是未驗，不是通過，也不是規則線失敗
- `grid_system_test.js` 的這句斷言本身沒有在 `77c3847..c0e58e2f` 改動；同區間 `app.js` 有 97 行差異。本回合沒有把差異縮到某一行

重現到停住點：候選 tree、上述 bridge、`GEOMETRY_GRID_SYSTEM_ONLY=1`、headless Chrome、`http://127.0.0.1:8891/`。下一步要先讓這次拖曳真的改變卡片 `cx/cy` 且不改錨點，套件才能走到 390 的 `[data-rule-cell-i]`。走到之後只看一次 `scrollIntoView` 後的捲動父層、`getBoundingClientRect`、`elementFromPoint` 與焦點，不要用強制點擊、無限重試或只加長 delay 當作修好。

服務 pid 17636 與其 bridge 子行程已停止。沒有停止其他程序。
