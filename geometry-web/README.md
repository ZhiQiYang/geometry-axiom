# geometry-web — 幾何模型 Web 介面

以 `web_bridge`（C 核心）為唯一真相來源的物件畫布 UI。所有幾何變更都走 DSL → bridge；
畫布上的 `canvas-pos` 只是展示中繼資料，不參與幾何歷史。

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
- `POST /upload` → 把 scene 內容存成上層暫存檔並 `loadfile`。

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

- 主畫布：`Ctrl+Z`/`Ctrl+Y`/`Ctrl+Shift+Z` 復原重做、`Esc`、`v` 選取、`h` 平移、`f` 全部顯示、`1` 縮放 100%、`空白`暫時平移、`/` 聚焦搜尋。
- 面內工作區：`Esc`（取消拖曳→退出工具→返回）、`v`/`l`/`r`/`h` 工具、`f` fit、`1` 縮放 100%、`空白`暫時平移。

## 架構約定

- C 端（`../current_geometry.c`、`web_bridge.c`）不在本目錄職責範圍，重構期間零改動。
- 多行變更走 `mutate(lines)`：逐行送、失敗 undo 回滾 + toast（error 原文）。
- 參考線：bridge 無列舉指令，由 `dump` 文本以正則 `^guide (\d+) (\d+) (u|v) (-?\d+)$` 解析；`sid` 是承載面 id。

## RC 柱樑與投影套用（RC-POLYGON-PLAN）

- **柱/樑是一等物件**：物件庫「＋柱」「＋樑」→ 對話框建立 → 卡片可拖、檢視器改尺寸（重宣告）、`objects` 回傳 `columns[]`/`beams[]`。DSL：`column`/`beam`（語法見 `docs/RC-POLYGON-PLAN.md` 附錄 A）。
- **障礙物鬼影**：面內工作區呼叫 `obstacles <bid>`，把同空間柱樑投影成分類矩形（孔/凹口/角凹/條帶/拆分/頂凹/頂降），半透明顯示不改 boundary。
- **套用投影**：圖層列勾選鬼影 + 「套用 N 項投影」→ `apply-proj <bid> <item>… [cut-strip]`，單一交易：孔入環、凹口改外環、拆分產新面（原 id 留最大片、孔隨片走、拆片退出空間成員）。快照式，與柱樑無連結。
- **空間工作區**：平面示意圖點放柱、拖放樑、構件收/出清單；空間→柱樑畫「障礙」連線。
