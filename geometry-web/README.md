# geometry-web — 幾何模型 Web 介面

以 `web_bridge`（C 核心）為唯一真相來源的物件畫布 UI。所有幾何變更都走 DSL → bridge；
畫布上的 `canvas-pos` 只是展示中繼資料，不記入歷史——undo/redo 還原快照時保留使用者當下的擺位（L1）。

## 啟動

```bat
cd /d/knowledgebase/geometry-web
build.bat                  :: 編譯 web_bridge.exe（首次或 C 端變更後）
python serve.py 8765       :: 啟動靜態檔 + /api 橋接服務
```

瀏覽器開 `http://localhost:8765/`。

`serve.py` 行為：

- `GET /` → `index.html`；`GET /app.css`、`/app.js` → 同名靜態檔。
- `GET /scenes` → 上層目錄 `*.scene` 清單。
- `POST /api`（JSON `{"cmd": "..."}`）→ 轉送給長駐 `web_bridge.exe` 的 stdin，回傳其 stdout 一行 JSON。
- `POST /upload` → 把 scene 內容寫成系統暫存目錄（`tempfile.gettempdir()`，Windows 為 `%TEMP%`）下的暫存檔並 `loadfile`；回應帶 `path` 欄位，前端 `curScene` 指到它，「重新載入場景」才會載回剛上傳的內容。
- POST 跨站防護（L3）：`Origin` 存在且非 `http://127.0.0.1:<port>` / `http://localhost:<port>` → 403；`Host` 非本機 → 403；無 `Origin` 的 curl/測試腳本放行。`cmd` 含 `\r`/`\n` 或超過 4094 bytes → 直接回 `{"ok":false}` 不送 bridge。

## 測試

兩套裁判都必須全綠才算過閘：

```bat
:: 1) 直接 DOM/幾何測試（不需要瀏覽器）
node canvas_test.js direct

:: 2) headless Chrome CDP 實機測試（需 server 在 8765、Chrome 於預設路徑、除錯埠 9333）
node cdp_test.js
```

`cdp_test.js` 依印出的 ✓/✗ 計數決定 exit code（有 ✗ → exit 1）。
測試依賴的 DOM id / class / 全域列在 `docs/DOM-CONTRACT.md`——改 DOM 必同步更新它與 `cdp_test.js`。

## 檔案配置

| 檔案 | 角色 |
|---|---|
| `index.html` | DOM 骨架（三欄殼 + objectWorkspace 覆層 + 對話框） |
| `app.css` | 原型 CSS + 專案補丁段（檔尾「geometry-web 專用補丁」起） |
| `app.js` | 全部前端邏輯（classic script，無模組） |
| `serve.py` | 靜態檔 + `/api` + `/scenes` + `/upload` |
| `web_bridge.c` | C 橋接層（編成 `web_bridge.exe`，**公理層真相**） |
| `canvas_test.js` | 直接裁判 |
| `cdp_test.js` | CDP 實機裁判 |
| `docs/UI-REDESIGN-PLAN.md` | UI 重構唯一事實來源（SSOT） |
| `docs/DOM-CONTRACT.md` | 測試依賴合約 |
| `docs/prototype-構形Canvas-v2.html` | 視覺/互動原型參考 |

## 鍵盤（§5.8）

- 主畫布：`Ctrl+Z`/`Ctrl+Y`/`Ctrl+Shift+Z` 復原重做、`Esc`、`v` 選取、`h` 平移、`r` 矩形、`p` 多邊形、`f` 全部顯示、`1` 縮放 100%、`空白`暫時平移、`/` 聚焦搜尋。
- 面內工作區：`Esc`、`v`/`l`/`r`/`h`/`i` 凹口/`t` 角材/`e` 重畫外環、`f` fit、`1` 縮放 100%、`空白`暫時平移。
- `Esc` 實際階梯（單次按）：輸入框聚焦中 → 留給原生（不關工作區）；開著的選單 → 收；開著的對話框 → 關；面內鍵入長度暫存 → 清；面內方向小選單 → 收；進行中草稿 → 清並提示「再按 Esc 返回」；以上皆非 → 返回上一層焦點/世界。

## 架構約定

- C 端（`../current_geometry.c`、`web_bridge.c`）改動須重跑 `build.bat` 並過兩套測試。
- 多行變更走 `mutate(lines)`：包成 `history-begin`/`history-end` 群組 = 一步 undo（L2）；群組內任一行失敗核心自動整組回滾不留半套，前端再送 `history-abort` 驗證，回滾失敗 toast「回滾失敗，狀態可能不一致」。
- 參考線：bridge 無列舉指令，由 `dump` 文本以正則 `^guide (\d+) (\d+) (u|v) (-?\d+)$` 解析；`sid` 是承載面 id。

## RC 柱樑與投影套用（RC-POLYGON-PLAN）

- **柱/樑是一等物件**：物件庫「＋柱」「＋樑」→ 對話框建立 → 卡片可拖、檢視器改尺寸（重宣告）、`objects` 回傳 `columns[]`/`beams[]`。DSL：`column`/`beam`（語法見 `docs/RC-POLYGON-PLAN.md` 附錄 A）。
- **障礙物鬼影**：面內工作區呼叫 `obstacles <bid>`，把同空間柱樑投影成分類矩形（孔/凹口/角凹/條帶/拆分/頂凹/頂降），半透明顯示不改 boundary。
- **套用投影**：圖層列勾選鬼影 + 「套用 N 項投影」→ `apply-proj <bid> <item>… [cut-strip]`，單一交易：孔入環、凹口改外環、拆分產新面（原 id 留最大片、孔隨片走、拆片退出空間成員）。快照式，與柱樑無連結。
- **空間工作區**：平面示意圖點放柱、拖放樑、構件收/出清單；空間→柱樑畫「障礙」連線。
