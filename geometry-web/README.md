# geometry-web — 幾何模型 Web 介面

## 跨面共用基準

工具列「共用基準」依序可建立具名尺寸、世界 X／Y／Z 基準，再讓各承載面引用。
修改被已放角材引用的基準或尺寸時顯示全場影響，取消保持原狀，確認後原子提交。
每面只畫有效範圍內的線段；面外仍有定義。共用線請從基準管理器修改，不能拖曳成局部線。
「檔案 → 公理閱讀器」開啟同一份正典 HTML。

```text
spec 櫃頂高度 1200
datum 1 z spec:櫃頂高度
guide 1 1 datum 1
guide 2 2 datum 1
```

上例承載面 1、2 必須事先存在，且各自與基準面有唯一交線；平行或重合皆拒絕。

## Linux 雲端開發基線

需要 gcc、Python 3；managed preview 的啟動器另需 npm，不需下載套件。
`npm run build` 編譯當前 core 與 bridge 到忽略的 `.build/`。
本機可直接執行 `GEOMETRY_BRIDGE=.build/web_bridge python3 geometry-web/serve.py 8765`。
受管開發環境從 repo 根執行 `sites-preview start "$PWD"`；它使用 `npm run dev`。
受管模式只在環境變數 `GEOMETRY_MANAGED_PREVIEW=1` 且埠為 4173 時
額外接受 `terminal.local` 並綁定開發環境入口。預設仍只接受 localhost，沒有公開部署。
測試限制與可重現步驟見 [`DATUM-VALIDATION.md`](../geometry-core/DATUM-VALIDATION.md)。

以 `web_bridge`（C 核心）為唯一真相來源的物件畫布 UI。所有幾何變更都走 DSL → bridge；
畫布上的 `canvas-pos` 只是展示中繼資料，不記入歷史——undo/redo 還原快照時保留使用者當下的擺位（L1）。

## 新公理版本

已依 2026-09-18 更新的公理改為引用定位與自動跨距。角材表單先選定位引用，
只輸入截面 A/B，不再輸入長度。具名規格與參考線引用式可在面內屬性頁建立。
會影響已放角材時，畫面列出新舊中線、長度與違規；按「確認套用」才改場景。
有違規或取消都保留原狀。詳見 [語法與驗收紀錄](../geometry-core/README.md)。

Windows 如被 Smart App Control 擋住未簽章程式，使用已安裝的 WSL：

```powershell
powershell -File .\start.ps1 -Port 8765
```

此啟動器重新編譯目前原始碼，在 WSL 跑核心、Windows 跑網頁服務；不更動系統安全設定。
需現有 Ubuntu-24.04、gcc、Windows Python。可用 `-Distro` 指定其他已安裝的發行版。

## 啟動

```bat
cd /d D:\knowledgebase\geometry\geometry-web
build.bat                  :: 編譯 web_bridge.exe（首次或 C 端變更後）
python serve.py 8765       :: 啟動靜態檔 + /api 橋接服務
```

瀏覽器開 `http://localhost:8765/`。

`serve.py` 行為：

- `GET /` → `index.html`；`GET /app.css`、`/app.js`、`/reference-ui.js` → 同名靜態檔。
- `GET /scenes` → 上層目錄 `*.scene` 清單。
- `POST /api`（JSON `{"cmd": "..."}`）→ 轉送給長駐 `web_bridge.exe` 的 stdin，回傳其 stdout 一行 JSON。
- `POST /upload` → 把 scene 內容寫成系統暫存目錄（`tempfile.gettempdir()`，Windows 為 `%TEMP%`）下的暫存檔並 `loadfile`；回應帶 `path` 欄位，前端 `curScene` 指到它，「重新載入場景」才會載回剛上傳的內容。
- POST 跨站防護（L3）：`Origin` 存在且非 `http://127.0.0.1:<port>` / `http://localhost:<port>` → 403；`Host` 非本機 → 403；無 `Origin` 的 curl/測試腳本放行。`cmd` 含 `\r`/`\n` 或超過 4094 bytes → 直接回 `{"ok":false}` 不送 bridge。

## 測試

下列裁判都必須全綠才算過閘：

```bat
:: 1) 直接 DOM/幾何測試（不需要瀏覽器）
node canvas_test.js direct

:: 2) headless Chrome CDP 實機測試（需 server 在 8765、Chrome 於預設路徑、除錯埠 9333）
node cdp_test.js

:: 新公理表單、確認/取消、非法預覽、扣孔命中的快速實機驗證
node reference_smoke.js

:: 3) 伺服器輸入與故障處理（不需要真實 bridge 或瀏覽器）
python -B -m unittest discover -s ../tests -p test_serve.py -v
```

`canvas_test.js` 的 HTTP 模式與 `cdp_test.js` 都可用 `GEOMETRY_TEST_URL` 指定獨立測試伺服器，避免修改正在使用的場景。

`cdp_test.js` 依印出的 ✓/✗ 計數決定 exit code（有 ✗ → exit 1）。
測試依賴的 DOM id / class / 全域列在 `docs/DOM-CONTRACT.md`——改 DOM 必同步更新它與 `cdp_test.js`。

### 在 WSL 內執行（Windows 端被應用程式控制原則擋住時）

Smart App Control 強制模式會封鎖新編譯的未簽章執行檔，`web_bridge.exe` 因此起不來
（`cg_new.exe` 不受影響，C 核心測試照跑）。此時整條鏈可以搬進 WSL：

```bash
# 一次性：gcc、Node 22+（cdp_test.js 用全域 WebSocket）、Chrome
sudo apt-get install -y gcc
# Node 官方 tarball 解到 /opt/node；Chrome 用 dl.google.com 的 .deb

# 每次：建置 Linux 版 bridge，起 server，跑測試
gcc -O2 -o /opt/geometry/web_bridge web_bridge.c -lm
GEOMETRY_BRIDGE=/opt/geometry/web_bridge python3 serve.py 8765 &

GEOMETRY_CHROME=google-chrome \
GEOMETRY_CHROME_PROFILE=/tmp/cdp-profile \
GEOMETRY_CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage" \
GEOMETRY_TEST_SCREENSHOT=/tmp/phase1-shell.png \
  node cdp_test.js
```

可覆寫的環境變數（不設時行為與先前完全相同）：

| 變數 | 用途 |
|---|---|
| `GEOMETRY_BRIDGE` | `serve.py` 要啟動的橋接器**指令**（可帶參數；預設同目錄 `web_bridge.exe`） |
| `GEOMETRY_BRIDGE_WSL` | 設為 `1` 時，把送進橋接器的場景路徑由 `D:\…` 翻成 `/mnt/d/…` |
| `GEOMETRY_CHROME` | chrome 執行檔（預設 Windows 的 `chrome.exe`） |
| `GEOMETRY_CHROME_PROFILE` | `--user-data-dir` 位置 |
| `GEOMETRY_CHROME_FLAGS` | 追加旗標，空白分隔；WSL 內以 root 跑需要 `--no-sandbox` |
| `GEOMETRY_TEST_URL` | 測試頁面網址（預設 `http://localhost:8765/`） |
| | **Chromium 141+ 在 Linux 容器內請用 `http://127.0.0.1:<port>/`**，並在 `GEOMETRY_CHROME_FLAGS` 加 `--disable-features=HappyEyeballsV3`：新版 HttpStreamPool 對 `localhost` 每次先試 `::1` 失敗再退 `127.0.0.1`，約 600 次請求後 socket pool 會卡死（P5b 永遠等不到 `pick` 回應）。2026-09-25 以 netlog 確認，與應用程式碼無關。 |
| `GEOMETRY_TEST_SCREENSHOT` | 截圖輸出路徑；**在 WSL 內跑時建議指到 `/tmp`**，否則會用
  Linux 字型渲染覆寫掉 `docs/screens/phase1-shell.png` 這張文件用參考圖 |

注意：WSL 預設 NAT 網路下 Windows 連不到 WSL 內的 `127.0.0.1`；改用鏡像模式
（`.wslconfig` 的 `networkingMode=mirrored`）仍會被 Hyper-V 防火牆的預設輸入
封鎖策略擋住。上面的做法是讓 server、Chrome、測試腳本全在 WSL 這一側，
不跨越邊界，因此不需要動任何防火牆設定。

### Windows + WSL 混合模式（要用瀏覽器手動操作 UI 時）

上面那套全在 WSL 內跑，適合自動化測試，但 Windows 的瀏覽器連不到它。
要**人工操作畫面**時改用混合模式：`serve.py` 跑在 Windows（瀏覽器連得到
`localhost`），只把橋接器交給 `wsl.exe` 執行 Linux 版。`wsl.exe` 本身有簽章、
不受 Smart App Control 封鎖，所以用到的是**當前核心**而非舊二進位。

```bat
set GEOMETRY_BRIDGE=wsl.exe -d Ubuntu-24.04 --user root -- /opt/geometry/web_bridge
set GEOMETRY_BRIDGE_WSL=1
python serve.py 8765
```

`GEOMETRY_BRIDGE_WSL=1` 會把 `loadfile` 的 Windows 路徑翻成 `/mnt/…`，
否則 `/scenes` 與 `/upload` 給的路徑 Linux 端的橋接器開不了。

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
- 面內工作區形狀編輯（GEO-169）：select 下單擊邊/凸角 → 浮動列選「凹口／外凸／推拉／切角／F⇄X」；面板內 `Enter` 套用、`Esc` 關面板。
- `Esc` 實際階梯（單次按）：輸入框聚焦中 → 留給原生（不關工作區）；開著的選單 → 收；開著的對話框 → 關；面內鍵入長度暫存 → 清；面內方向小選單 → 收；面內就地操作面板 → 關；面內有選取的邊/角 → 清；進行中草稿 → 清並提示「再按 Esc 返回」；以上皆非 → 返回上一層焦點/世界。

## 架構約定

- C 端（`../current_geometry.c`、`web_bridge.c`）改動須重跑 `build.bat` 並過兩套測試。
- 多行變更走 `mutate(lines)`：包成 `history-begin`/`history-end` 群組 = 一步 undo（L2）；群組內任一行失敗核心自動整組回滾不留半套，前端再送 `history-abort` 驗證，回滾失敗 toast「回滾失敗，狀態可能不一致」。
- 參考線：使用 bridge `references` 的來源、世界位置／方向與裁切段；不得從顯示數值反推引用定義。

## 形狀編輯（GEO-169，`docs/uiux-review/形狀編輯提案.dc.html` 方案 A + B）

- **邊優先（A）**：select 工具單擊外環邊 → 邊亮起、浮動列「凹口／外凸／推拉／F⇄X」；單擊凸角 → 「切角」。
  選操作後就地面板填「定位（從左／置中／從右）＋距離、寬、深」（推拉：往內／往外＋距離；切角：a、b），
  畫布即時畫紅（減）／綠（加）預覽矩形，`Enter` 套用、`Esc` 取消。拖邊仍是推拉。
- **幾何**：`feRectBool(loops, "sub"|"add", rect)` 純函式做正交多邊形對矩形的布林（頂點座標切格 → 取邊界環），
  結果一律走 `boundary` 重宣告交易，核心 I2 守門；面消失或拆成兩片在前端就擋下（toast）。
  新邊 fixity：與舊邊共線重疊者繼承，其餘 FIXED（對齊公理層 R7「套用產生的新邊 fixity 一律 FIXED」）；
  新環的走向與起點盡量沿用舊環，沒被動到的邊保住 `e<i>` 編號。
  會動到被角材引用的邊時，核心照 I8a 回 `preview`，`api()` 照舊開影響預覽對話框，確認才落地。
- **形狀頁（B）**：檢視器「形狀」分頁列出本次工作階段套用的特徵（寬、高、距左／右、距上／下，可改起算邊），
  改數字即落地（反向布林還原再正向套用）、可鏡射、可刪除（反向布林）。
  **特徵堆疊只存在記憶體，不寫進 .scene**——核心只認最終輪廓；每次邊界變更後逐筆驗活，對不上的自動剔除。
- 舊的「凹口」工具（點邊開對話框）、「開口」拖矩形、「外環」重畫與形狀庫都保留。

## RC 柱樑與投影套用（RC-POLYGON-PLAN）

- **柱/樑是一等物件**：物件庫「＋柱」「＋樑」→ 對話框建立 → 卡片可拖、檢視器改尺寸（重宣告）、`objects` 回傳 `columns[]`/`beams[]`。DSL：`column`/`beam`（語法見 `docs/RC-POLYGON-PLAN.md` 附錄 A）。
- **障礙物鬼影**：面內工作區呼叫 `obstacles <bid>`，把同空間柱樑投影成分類矩形（孔/凹口/角凹/條帶/拆分/頂凹/頂降），半透明顯示不改 boundary。
- **套用投影**：圖層列勾選鬼影 + 「套用 N 項投影」→ `apply-proj <bid> <item>… [cut-strip]`，單一交易：孔入環、凹口改外環、拆分產新面（原 id 留最大片、孔隨片走、拆片退出空間成員）。快照式，與柱樑無連結。
- **空間工作區**：平面示意圖點放柱、拖放樑、構件收/出清單；空間→柱樑畫「障礙」連線。
