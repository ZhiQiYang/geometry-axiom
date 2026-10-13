# 驗收證據索引（2026-10-08）

讀取根：`D:\geometry-axiom-focus390` @ `ce0958ca700753172338fe291a17e781da89465a`。main 是 `5cc1ffa1ee85120eca14258b86b715151cad274f`。沒有重跑測試，沒有重造歷史 10/155，沒有再複製 repo 裡的 tar.gz，沒有刪 Temp。

索引文字裡的使用者家目錄寫成 `<local-user>`。複製進 `evidence-stage` 的兩份 JSON 保持原檔，它們沒有家目錄路徑。含家目錄或 `feedback/` 的原始檔不複製，標「含私人內容，未收」。

種類：真瀏覽器、VM／純函式、原生、作者自述、未驗。

## 可查詢表

| 案例 | 腳本 | 受測提交 | runtime／bridge | 原始路徑 | 退出碼 | 結論 |
| --- | --- | --- | --- | --- | --- | --- |
| 焦點丟失再現 | 當時探針；位元組已被後來的 `probe/focus390-verify.js` 蓋過。以該輪 `probe.log` 為準 | 補丁前。binding 不把這輪算產品通過 | 服務埠 8907。bridge 指紋 `0c1e19603546dab1c18a887debbc25298eb4c57b0e694525fb1777c14658baed`，exe SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`，783872 bytes | repo `tests/release-evidence/20261008-focus390/runs/focus390-repro/`。`status.json` SHA-256 前綴 `3f95c327cb0b1e77` | 0 | 真瀏覽器。exit 0 是再現 focus-lost，不是產品通過 |
| verify-3 含 Escape | `probe/focus390-verify.js` 再加一次 Escape | head 記錄 `a7bff8f`，`appJsDirty` | runtime `38021bc54308…`，fresh，pid 17304，session `53426f92…`，埠 8907 | `…/runs/focus390-verify-3/`。status SHA 前綴 `f8023d63a9bb0aef` | 1 | 真瀏覽器。排除輪，保留。390 `tab-missed` |
| verify-4 | `probe/focus390-verify.js` | `a7bff8f` 加未提交 app.js，該 diff 後來成為 `3574b47` | 同上 runtime 字串，fresh，pid 5684，session `b36e19b4…` | `…/runs/focus390-verify-4/`。status SHA 前綴 `98157f51f07321f6` | 0 | 真瀏覽器。限定通過。不是乾淨 `3574b47` 的 GRID 輪 |
| GRID 316／0、P88 107 | `cdp_test.js`＋`grid_system_test.js`，`GEOMETRY_GRID_SYSTEM_ONLY` | 乾淨 `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72` | runtime `38021bc54308a464a56785a2e3106af3f2d10f11caac79a541a0b716ce2c3f7f`，埠 8911 | `…/runs/grid-system-170/receipt.json` SHA 前綴 `c78425fe9df4f330` | nodeExit 0 | 真瀏覽器。316/0。不是完整主 UI。截圖目錄當時是空的 |
| 回歸一 | 同上，加焦點回歸 | 仍是 `3574b47` | runtime `dcc5ee0b…`，fresh，pid 10968，埠 8912 | `…/runs/grid-system-170-regress-1/` SHA 前綴 `b9b1ae5f6094df6b` | 1 | 真瀏覽器。325 通過、0 失敗後，fatal `#btnNewProject`。不得改標成通過 |
| 回歸二 328／0、P88 119 | 同上 | HEAD 仍是 `3574b47`，測試檔未提交。不是乾淨 `9b97a39` | runtime `09fb8f1c…`，fresh，pid 40080，埠 8912 | `…/runs/grid-system-170-regress-2/` SHA 前綴 `91a015060e176e5c` | 0 | 真瀏覽器。328/0。不是 316 那輪 |
| 乾淨 163c 逾時 | 同上 | `163c575756dedf31efff7842cdeb2f9de9726ba2` | runtime `1d1fc493…`，fresh，pid 36160，埠 8913 | `…/runs/grid-system-163c/` SHA 前綴 `d6e5120dd49702f2` | 1 | 真瀏覽器。266 通過、0 失敗、未完成。25 秒等第二次重建 |
| 乾淨 8982605 | 同上。腳本 blob 與後來的 `e176681`／`ce0958c` 測試腳本相同（`ce0958c` 只改證據文案） | `8982605c83d0f27cec27790c0b407d946b0093fe` | runtime `168bfaecbe12bf0adbf8def1ca67834fc1177305c76a72cd75045b36794388a6`，fresh，pid 24988，session `bad0b27f…`，bridge pid 38552，埠 8913，CDP 9513 | `…/runs/grid-system-8982605/receipt.json` SHA 前綴 `8fed3e920424d729` | 0 | 真瀏覽器。346/0，P88 137。限定格線。服務 `processExit` 1 是驗完主動停 |
| #169 非瀏覽器 82 套 | `tests/run_all.py` 彙總 | executionHead `07bca2991ec7984b18b11792bbdbd2e7616dc0c1`。不是 #169 head `a7bff8f` | 見 `final-native-aggregate.json` 的 binary closure。具名 skip：`py:test_gdi_contract` | repo `tests/release-evidence/20261008/final-native-aggregate.json` | 0 | 原生。2571 pass、0 fail、skipped 1。先前失敗輪 `bb93953` exit 1、2563/8/1 仍留在同一 JSON |
| #169 完整 CDP | `cdp_test.js` 完整模式 | `459478e9f68fe8ee9252a5f6b4a1ffb2213a5207` | 矩陣列 `full-cdp`。大檔在 tar.gz，本索引未解壓 | `tests/release-evidence/20261008/geometry-full-cdp-evidence-459478e9.tar.gz`（15356034 bytes）與 `final-validation-matrix.json` | 矩陣 status `verified` | 真瀏覽器。2177/0。不得說成 `a7bff8f` 或 `ce0958c` 已重跑。同矩陣保留較早失敗輪：`f23a65a` 2006、`5c3d36c` 1059 且 failed 1 |
| #169 卡片等待追加 | followup matrix 點名的部分 GRID／組立／卡片 | `b822a9f` 這段。followup 寫明沒有新的 full2177 | 見 `20261008-card-wait/` | `geometry-card-wait-evidence-b822a9ff.tar.gz`（7859803 bytes）已在 repo | 矩陣 `verified-and-sealed`，`releaseApproved` false | 真瀏覽器的部分範圍。不是新 head 的全套 |
| #173 邊長草稿 | PR 內截圖與 `binding.json`。本索引沒有重跑 | `d44ad7fea531a94f67401d5b403565cd891770ae` | 較早 Temp identity 含家目錄，未收 | 已進該 PR：`tests/release-evidence/20261008-edge-draft/` | 未把截圖當退出碼 | 真瀏覽器截圖在 PR。較早 Temp 的 phase3 自記 21／2，含家目錄，未收，也不升成這包的數字 |
| #173 第三階段保存重開 | `harness/phase3-formal.js` 與 `harness/phase3-undo.js`。本索引沒有重跑 | 產品 `d44ad7f`。證據提交 `457eade180add835e6b9fc854835844c7515281e` | `identity.json`：runtime `f2804c8068805409ccc06cddea3fac6219f768706f9276e981948f1142a286b2`，fresh true，pid 30184。bridge 沒有重編。model-base 路徑不抄出 | 已在該提交：`tests/release-evidence/20261008-phase3-formal/`。`results.json` SHA-256 `ea8f77d877458b53826ea4eedfece27e2e6d794704b9da9a0429ddbc3dce4025` | 最終輪 `NODE_EXIT 1`（32 通過、1 失敗）。追蹤輪 `NODE_EXIT 0`。CI run `37802875624` 是 7 jobs、0 steps | 來源核對已提交檔，不是本輪實際執行。失敗項保持失敗。log 含本機路徑，不複製 |
| #174 before | `async_reply_ui_test.js` 範圍 `GEOMETRY_ASYNC_REPLY_ONLY` | 修補前。PR 內 `before/` | 埠 8921。Temp 收據含家目錄，未收 | PR：`tests/release-evidence/20261008-async-repro/before/`。Temp 同名輪不複製 | Temp `completed` false；async-reply-ui 1 通過／1 失敗；整份 passed 3、failed 3 | 真瀏覽器。失敗輪應以 PR 內已去敏檔為準。Temp 未收 |
| #174 after | 同上 | `4e6ab4421e0e634ff4fd06356dadb7d8eaf4feb3` | 同上 | PR：`…/after/` | Temp `completed` true；該組 6/0；整份 passed 10、failed 0 | 真瀏覽器。通過輪在 PR。CI 沒有跑 |
| #174 合成格網重開 | `geometry-web/save_reopen_synthetic_test.js`，`GEOMETRY_SAVE_REOPEN_ONLY=1`。本索引沒有重跑 | 產品 `4e6ab44`。紀錄提交 `b0ef9bcfb6133e6463c859952270231f8e740363` | runtime `f0c9f4c72d601dde34476ee0b763f29fceeb0a5dd70488b04fd1fa59abef92c4`，fresh true，pid 34272，埠 8921，CDP 9521。bridge SHA-256 `aa2cc6ae…`，沒有重編 | `tests/release-evidence/20261008-async-repro/save-reopen/record.json` | 0。通過 24、失敗 0 | 來源核對已提交收據。下載備援。沒有 undo／redo。不是作業系統存檔對話框，也不是完整 CDP。CI run `37805163066` 是 7 jobs、0 steps |
| #174 negative | 同上腳本的負控制 | Temp only，不在 `4e6ab44` 樹 | 埠 8921 | `<local-user>\AppData\Local\Temp\geometry-async-qa-20261008\run-negative\result.json` | `completed` false；該組 2 通過／4 失敗；整份 passed 6、failed 5 | 真瀏覽器。含私人路徑，未收。不把這 4 失敗升成產品缺陷，也不當成已進 PR 的收據 |
| 卡片提交探針 | Temp `card-commit-postfix.json` | 不在任何 open PR 樹。合成夾具 | 無 runtime 欄 | 已複製 `evidence-stage/card-commit-postfix.json`，3125 bytes，SHA-256 `884552b4b401eebaf7c53e11e3eedcbc289688b22b0efa7b5deadf19a867565f` | 無單一 exit | 真瀏覽器探針 JSON。不是 #168 通過證明 |
| 卡片拖曳探針 | Temp `card-drag-probe.json` | 同上。頁面 `127.0.0.1:8893`，Chrome/155.0.8059.39 | 無 | `evidence-stage/card-drag-probe.json`，34106 bytes，SHA-256 `84acb2be78dd4b78ca7b7e00ea4ee92314501292ae8d58bca38287de1bcc1961` | 無單一 exit | 真瀏覽器探針。合成邊界，不是私人圖紙 |
| 歷史模型庫十項與 155 | 未收錄。`browser_ui.py` 與修正前序不在包內 | `20261007/README.md` 寫受測 head `66a4c89` 等舊值 | 不適用 | `tests/release-evidence/20261007/README.md` 第 41–42 行。tar.gz 3381155 bytes，SHA-256 `e06116c9c536e083256cb869c811c8bfbfa849841d4ed52177f52a57befc695e` | 不適用 | 未驗。不要重造。155 通過紀錄只保留原版本，oracle 仍缺 |
| owned 刪除原因與規則線清空後載入 | 兩支 unittest。實際執行 | #171 `fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d` | fresh bridge 指紋 `0c1e19603546dab1c18a887debbc25298eb4c57b0e694525fb1777c14658baed`，exe SHA-256 `507ae331edea9f530b3b22af5f8d46eee8d6d26a95f947f742ed96144ebada1b`，783872 bytes，建於 `2026-10-08T23:20:38+08:00`。沒有重編 | #171 `tests/release-evidence/20261008-save-reopen/native-contract-run.log` | 0。`Ran 2 tests in 1.087s`、`OK` | 原生。不是完整 `run_all`。同命令對無 sidecar 的 exe（SHA-256 `453d689db7bb6f90b1ee10948c02dc179c3e23aefd3b586eba9615a223fce2a5`，729088 bytes）是 `skipped=2`，那個 0 不算 |
| 遠端 CI | `Geometry integration`，7 jobs | 上列舊 run 仍是 0 steps。新增：#171 `fd5b8c8` run `37804408304`；#173 `457eade18` run `37802875624` | 無 runner，steps 0 | GitHub Actions。沒有測試 log | 結論欄是 failure | 未執行。不是測試失敗，不要刪測試或改門檻。沒有為了這兩筆重跑 |

`server-lifecycle.json` 裡九段服務的 `processExit` 都是 1，角色寫明是主動停止或該輪結束，不是 bridge 崩潰。verify-4 與 8982605 的 fresh 為 true。

## 種類怎麼分

- 真瀏覽器：上表焦點輪、GRID only、完整 CDP 2177、#173 截圖、#174 before/after、兩份 stage 探針。
- 原生：#169 `final-native-aggregate.json`。GDI skip 是具名略過，不是通過。
- VM／純函式：followup 有一列 `pr168-independent-helper-vm`。本索引沒有把該列重跑，只指出它在 `20261008-card-wait/followup-validation-matrix.json`，且 `releaseApproved` 是 false。
- 作者自述：#175 提交說明寫沒有重跑。#172 的 review.md 是審查紀錄，不是收據。矩陣的 `verified` 字樣不能代替上表的 exit。
- 未驗：實體滑鼠、真機、IME、其他工作區查詢後重繪、完整主 UI 在 `ce0958c`、新 head 的 full2177、歷史 10/155、PR161 十項腳本、全部上列 CI。

## 缺件、重複、失效路徑、大小、雜湊、隱私

- `ce0958c` 相對 `e176681` 只改 `round-audit.md` 與 `SHA256SUMS.txt` 各一行。產品與套件 log 沒有變。改寫前的 89 筆對帳留在先前證據核對；現在的總表對的是改寫後的 round-audit，不要把舊 blob 說成 head 的雜湊。
- aux 目錄的五份 `grid-system-*.log` 與 repo `suite.log` 差 19 到 316 bytes，是去敏前的原檔（含家目錄）。repo 已有去敏版。原檔含私人路徑，未收。不算第二套數字。
- `/workspace/scratch/...` 若出現在舊 JSON，是當時執行目錄，不是 repo 路徑。
- `commands.md` 停在回歸二，沒有 163c 與 8982605 的命令區塊。命令在各輪 receipt 與 suite.log，沒有補造。
- 大檔已在 repo，不複製：`20261007/evidence.tar.gz` 3381155；`20261008/geometry-full-cdp-evidence-459478e9.tar.gz` 15356034；`geometry-main-evidence-459478e9.tar.gz` 39046314；`pr162-oracle-evidence.tar.gz` 3043564；`20261008-card-wait/geometry-card-wait-evidence-b822a9ff.tar.gz` 7859803。未解壓。
- #174 的負控制、async Temp 的 before/after、inspector `phase3-out` 的 identity／results、focus390 Temp 的 `feedback/`、`*.scene`、全部 `chrome-profile*`：含私人路徑或使用者回報目錄，未收。
- 兩份已收探針沒有 `Users\`、沒有憑證、沒有 `feedback/` 場景。

## 可清理清單（不要刪）

下面只是清單。埠 8915、8921、9521 與四個工作樹還在用，現在刪會打到活人。

1. `<local-user>\AppData\Local\Temp\geometry-cdp-*` 與各 `geometry-*-download-*`、`geometry-rule-editor-*`、`geometry-rule-lines-*`：大量同時間戳的瀏覽器設定與下載暫存。可能含 cookie，未收。
2. `geometry-focus390-20261008` 的 chrome-profile 與 feedback、`*.scene`。已收錄的是 repo 去敏包。
3. `geometry-aux-20261008` 的 `grid-system-*.log`：與 repo suite.log 近重複，且含家目錄。`serve-8891.err` 同樣不收。
4. `geometry-async-qa-20261008\run-*\chrome-profile` 與空的 `feedback/`。負控制 JSON 先留在原地，等 #174 負責人去敏後再決定要不要收。
5. `geometry-inspector-draft-20261008` 的 chrome 與 phase3 Chrome 日誌（多份 `000003.log`）。身份檔含家目錄。
6. 不要刪 repo 的 tar.gz、失敗輪、verify-3、回歸一、163c、#169 的 precedingFailedAttempt。

`evidence-stage` 現有兩檔：`card-commit-postfix.json`、`card-drag-probe.json`。沒有別的複本。
