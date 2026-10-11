# #116 K4 交接：其餘畫布的游標、右鍵選單、觸控

來源提案：K4 提案 r3（2026-10-10；DP-11、DP-32 的就地動作解讀為使用者確認 🔒，其餘依授權 L 暫定）。
本檔每個 PR 各加一節：head SHA、runtime 指紋、通過數、log 路徑。87 項與新 gate 都是 `run_all.py` 的 excluded 手動 gate，
CI 又受帳號計費阻擋，所以兩者的結果只在這裡與 PR 正文留底。

## PR-a：共用選單殼（2026-10-11，純重構）

**無新可見入口**（GEO-219 減項說明：無新增、無移除；只把已有的面內右鍵選單的實作換成共用殼）。

### 範圍

| 檔案 | 變更 |
|---|---|
| `geometry-web/context-menu-shell.js`（新） | `window.ContextMenuShell.create(adapter)`：開關、單一實例（DP-24）、頭／tiles／搜尋／清單／footer 原因、子選單、鍵盤（↑↓ Home End Enter ←→ Esc、IME 組字不搶鍵）、邊緣夾限與翻轉、焦點離開關閉、選用的外部 pointerdown 關閉、兩級守門（DP-33）、執行前 `current()` 再核 |
| `geometry-web/face-context-menu.js` | 改為 adapter：`model()`、`stamp()`／`current()`、寫入守門 `writable()`、各項目效果 `execute()`、側接表單 `#feOpPanel`（`decoratePanel`／`layout`）。`window.FaceContextMenu` 對外面不變 |
| `geometry-web/index.html` | 新增 `<script src="context-menu-shell.js">`（在 `face-menu-icons.js` 之後、`face-context-menu.js` 之前） |
| `geometry-web/docs/DOM-CONTRACT.md` | GEO-192 C 節與全域表各補一段 |
| `tests/test_issue116_canvases_browser.js`（新） | K4 新 gate 的殼段（A 特徵測試＋B 殼契約）；`tests/run_all.py`、`tests/INTEGRATION-GATES.md` 登錄為 excluded |

`app.js`、`face-context-menu.css`、`current_geometry.c`、`公理層.md` 未動。`#feCtxMenu`、`data-fe-act`、`.fcm-*`、`.fcm-anchor`、
所有文字與尺寸逐字不變。

### 殼介面（一句話）

`ContextMenuShell.create({menu, viewport, actAttr, escape, icon, model, stamp, current, guards:{nav,world}, begin, execute, …選用鉤子})`
回傳 `{open, hide, sync, position, render, reason, destroy, isOpen, state}`；模型項目的 `level` 為 `'view'`（不受寫入守門）、`'nav'`
或預設的 `'world'`（各自走 adapter 的 `guards`），每個項目執行前殼先用 adapter 的 `current(stamp)` 再核一次，過期就關閉、不執行。

### 驗證

- 基準：`origin/main` = `6a8c2fac3f220ea4e76139da7c232a658dfebf16`。
- 執行環境：WSL Ubuntu-24.04、Google Chrome 153.0.8010.47、Node v24.21.0；Playwright 取自 Codex runtime 現成安裝（`NODE_PATH`，未下載）；
  每次都是乾淨 clone＋原生建置＋隔離服務（`/runtime` fresh 且屬該 clone）＋TEMP feedback。
- 程式碼 runtime 指紋（`/runtime` version，來源檔雜湊）：PR 程式碼 `1db30734b40d9b5c32a2c8193c8c40620664bc7255cb3b8e29834c14a996629f`；
  main 基線 `290ebaee1760b3983e98fc4da27bc9154d3a151e2723e24265c4c129aaa2f070`。
- 87 項 `tests/test_issue116_browser.js`：PR 87/87、main 基線 87/87（期望值未改；失敗集合皆為空，故相同）。
- 特徵測試對照：新 gate 的 A 段可對抽出前的程式跑。對 main 基線與 PR 各跑一次，16 組目標（邊／孔邊／凸角／凹角／面內點／面外空白／參考線／
  未放置／單選角材／多選角材／390px，含子選單、搜尋、表單開啟）的選單 DOM（`outerHTML`）與幾何（四捨五入到 0.01px）快照合併後 SHA-256 **相同**：
  `fd673e6801f2084985b1993baccaa96153925f24c34449a564bb08261520ff4d`。
- 新 gate（`4ec7279`，與 PR 程式碼相同）：A 段 19 項、完整 gate 56 項，全綠；特徵快照雜湊與 main 基線相同。
- 突變（`4ec7279`，每個都在乾淨 clone 上改一處文字、斷言恰好命中一處、重建後跑完整 gate；log 在 `scratchpad/k4a/runs/s4-mut-*`）：

  | 突變 | 變紅的檢查 |
  |---|---|
  | face adapter 的 `current()` 恆回 true（§10 PR-a (i)）＋外環邊→另一邊後點舊 Fixity 列 | a1「STALE MENU NODE SENT A WORLD COMMAND」（實際送出 `line boundary 1 … fixity F F F X`）、a1 dump 被改 |
  | 殼執行前不再呼叫 `current()`（§10 PR-a (ii)） | 同 a1 兩項、b3「STALE NODE RAN」 |
  | 檢視類項目放到寫入守門後 | a2「VIEW ITEM WAS BLOCKED」、b2「VIEW ITEM WAS GUARDED」 |
  | 拿掉守門分級 | a2「WORLD ITEM RAN UNDER oc.busy」 |
  | 拿掉單一實例 | b1 三項 |
  | 拿掉 IME 組字守門 | a3 兩項、b4 |
  | 拿掉焦點離開關閉 | a4 |
  | 拿掉邊緣夾限 | b5 四個角（另牽連 a1c 對照組） |

- **§10 PR-a (i) 的「87 項必紅」預期不成立**：face adapter 的 `current()` 恆回 true 時，87 項仍是 87/87 全綠
  （`s4-mut-face-current-true/b87.log`）。87 項的過期情境（selection／frame／session／context）在 `current()` 失效後仍被
  其他層擋住，原因我沒有深究；所以「`current()` 被拿掉」的牙齒只在新 gate 的 a1，不在 87 項。87 項的期望值依規則未動。
- WSL CI 等價收據（`148e85c`，程式碼同上）：canvas 2207 通過／completed:true／golden 吻合 84 段（與 main 基線同）；
  native 2609／2611 通過、1 失敗（`py:test_binaries … same_size_rewrite_restoring_mtime_is_not_published`，與本 PR 無關，隔離重跑通過，
  但不在基線失敗清單所以 runner 判紅）。

### 審查後的調整（`48d9be0`，只改測試）與證據界線

PR #186 的審查（dot）指出新 gate 的四個缺口，`48d9be0` 已處理：

1. 身分／隔離前置（`runtime.fresh`、`runtime.root` 屬本 worktree、頁面 meta 版本＝`/runtime` 版本）在任何模式下都是 fail-fast，先於任何 fixture 或命令；
   `GEOMETRY_K4_KEEP_GOING=1` 只作用於行為斷言。`GEOMETRY_K4_SELFTEST=stale-runtime` 以錯的 root 驗證：必須非零結束、沒有 `PASS a0`、`commandsSent=0`。
2. characterize 與完整兩個 phase 共用同一個結算 `settle()`，任何已記錄的失敗都非零結束。`GEOMETRY_K4_SELFTEST=fail-check` 在兩個 phase、`KEEP_GOING=1` 下注入刻意失敗，必須非零結束。
3. `b7` 改為以 add／removeEventListener 記帳驗證 `destroy()`（新增 4 個、洩漏 0 個；不是只看 `state=null`），並新增突變 `no-destroy-cleanup`。
4. 新增 `b8`：adapter 效果的延後 resolve／reject 發生在選單 close→reopen 之後，不得動到新選單（突變 `hide-after-execute`）。

**證據界線（請照字面讀）**：
- `4ec7279` 之前的 87 項／新 gate／突變／`148e85c` 的 canvas 2207 與 native 的收據，都不是 `48d9be0` 之後的最終 head 的證據。`/runtime` 指紋不含 `tests/`，
  所以程式碼同版只能說明「產品程式沒變」，不能取代最終 head 的重跑。最終 head 的重跑已排進 WSL v3 佇列（`seq3.sh`），收據會綁：完整 head、測試檔雜湊、runtime 版本、
  原生 binary 雜湊、每個指令與其 exit；在它出來之前，最終 head 沒有自己的收據。
- 完整 7 job 的裁判由主迴圈跑；本 PR 不宣稱 CI 等價全綠。
- native 首次（`148e85c`，環境互斥）是 2609 通過／1 失敗／1 skip，**維持紅**；失敗項是無關的 `py:test_binaries …same_size_rewrite_restoring_mtime_is_not_published`（隔離重跑通過）。
  第二次 native（`4ec7279`，收據 `4ec7279e-k4a-native2`）有外來重度程序（`exclusivity.during_run` 為否）、另外兩個無關的逾時型失敗
  （`py:test_rule_case_workbench_http … test_timeout_output_unknown_runtime_and_capability_are_nonpass`、`node:tests-js` 的 formal-cases 計時項），**不可當裁判**，只留作診斷。
- **過期節點的保證範圍**：a1／b3 只證明「同一次開啟內，情境改變後殼拒絕執行已保存的節點」。更早一次開啟遺留的節點，其監聽器會對「當下」的狀態驗證（承襲自抽出前的行為；
  節點已被 `hide()` 拔掉，沒有使用者路徑可達）。這一點沒有被測試覆蓋、也沒有改變，**不得宣稱完整的過期節點保證**。若要補，是在殼加「開啟世代」並讓各節點綁世代，屬行為變更，不在 PR-a（純重構）。

### PR #186 M1：保留失敗結算收據（2026-10-11）

新 gate 在 `settle()` 寫出完整 `failed` 收據並擲錯後，最外層 catch 原本會再寫入縮減的
`aborted`，遺失 phase、records、errors、snapshotHash 與 runtime。現在成功、失敗與真正中止共用
完整格式；已結算的失敗不重寫，真正中止保留已取得的 runtime／快照，尚未取得者明列 null。
若檢查通過後瀏覽器清理失敗，最後仍寫 aborted 並非零退出，不留下假 passed 收據。

`tests/test_k4_evidence.js` 直接執行 gate 的 check／settle／catch 原碼，只把 main 的瀏覽器工作
替換成受控結束路徑：characterize／full 各驗失敗及提前中止，再驗成功與成功後清理失敗，共 6 項。
修前 1 過／5 失敗；修後 6/6；移除 catch 的失敗保護後 4 過／2 失敗，兩個 phase 均指出
「outer catch must not overwrite a settled failure」；還原 6/6。這些是純 Node 收據測試，沒有啟動瀏覽器。
既有 87 項及 browser gate 的行為斷言未改，native 登記僅因新增 6 項而由 651 調成 657。

原始日誌及雜湊：本次 scratchpad `board-local-codex/pr186-before.log`、`pr186-baseline.log`、
`pr186-overwrite-mutant.log`、`pr186-restored.log`、`pr186-unit-results.json`。
修後 head 的 87 項、完整新 gate、瀏覽器突變及 7 job 收據仍待 WSL；上述純 Node 結果不替代 B1，
先前 native 首紅與外來程序污染紀錄維持原判定。

### 2026-10-12：缺少 runtime version 的中止收據（PR #186 M2）

`/runtime` 回覆 `{error:"Not Found"}` 時，原 main 會用 undefined 覆蓋初始 null，導致
JSON 序列化省略 runtime 欄。現在以 `runtime.version ?? null` 保留明確的 null；fatal 隔離
檢查仍在瀏覽器啟動及任何 fixture／reset 之前拒絕，不因 KEEP_GOING 放行。

`test_k4_evidence.js` 新增 characterize／full 各一項，直接執行未替換的 main 入口，
只模擬 fetch 回覆與外部依賴；斷言非零退出、零 launch、零命令、完整收據及 runtime:null。
修前為 6 過／2 紅；修後 8/8；移除 null 預設的突變再次 6 過／2 紅，還原 8/8。
純 Node 測試無 skip、不開埠、不啟動瀏覽器，aggregate 只因新增兩項由 657 調為 659。
原始資料在 scratchpad `board-local-codex/pr186-m2-{before,after,remove-null-mutant,restored}.log`
及 `pr186-m2-results.json`。舊 87 項及產品檔未改；新 head 的 B1 瀏覽器及七 job 驗收仍待完成。

### 暫定裁決（依授權 L，可逐列推翻）

| 題目 | 選項 | 採用 | 理由 | 如何推翻 |
|---|---|---|---|---|
| 殼的 `presentation` | 立刻支援 `card`＋`sheet`／只做 `card` | 只接受 `card`，要 `sheet` 就擲錯 | `sheet` 的 CSS、定位、不自動聚焦都在 PR-d，PR-a 沒有東西可驗；條文推不出的行為不實作 | PR-d 放寬該檢查並補 `.fcm-sheet` |
| `face-context-menu.css` | PR-a 就改成殼共用選擇器／維持 | 維持不動 | PR-a 要求外觀逐字不變，且還沒有第二個宿主；PR-c 加 `#canvasCtxMenu` 時再擴選擇器 | PR-c 改 CSS |
| 外部 pointerdown 關閉 | 殼內建／選用 | 殼提供、**預設關**；面內 adapter 不開 | 面內已由 `app.js` 的 pointerdown 處理（含拖曳 op 手把的例外），PR-a 不動 `app.js`；兩邊並存會對例外不一致 | PR-c 的 oc adapter 開啟 |
| 守門分級的表達 | adapter 自己判斷／項目帶 `level` | 項目帶 `level`（`view`／`nav`／預設 `world`） | 讓「檢視類不受寫入守門」成為殼的結構性保證，而不是各 adapter 的慣例；`nav` 殼已支援、面內未用 | 改回 adapter 內判斷 |
| 新 gate 的探針 | 用 `op:*` tile 驗寫入守門／用 Fixity 列 | Fixity 列 | `feStartOp` 在 `oc.busy` 時自己就拒絕，拿掉殼的守門 `op:*` 探針不會紅（突變 `guard-none` 實測通過了 A 段）；Fixity 執行時 adapter 會先關選單，所以「選單仍開著且 footer 有守門原因」只可能來自殼 | — |

### 已知差異與未驗項

- 唯一的程式面行為差異：`open()` 最後的搜尋欄聚焦寫成 `?.focus`（舊版直接 `.focus`）；只有 `render/position` 在開啟過程中被即時判成過期而關掉選單時才不同（舊版會丟 TypeError），正常路徑不會走到。
- 不含：游標、觸控、物件畫布選單、`#homeButton` 移除（PR-b／c／d）。
- 沒有視覺變更，因此沒有對稿截圖；視覺不變以上面的 DOM／幾何雜湊證明。
- 未驗：實機觸控與 iOS／Android（PR-d 才有）；Windows Chrome 上的 87 項（SAC 擋新 exe，原生部分只在 WSL 跑）；CI 受計費阻擋；除 native 與 canvas 外的 5 個 CI job 由主迴圈另跑。
