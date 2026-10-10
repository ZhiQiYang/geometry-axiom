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
- 新 gate：A 段 18 項、完整 gate 55 項（head `148e85c`；後續只改測試探針，見 PR 正文的最終數字）。
- 突變與 WSL 收據：見 PR 正文與下方路徑。

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
