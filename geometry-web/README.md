# geometry-web — 幾何模型 Web 介面

## 工程規格：材料、做法與正式網格

工程規格已接入正式畫布及原生核心。自己的面從工具列「網格 → 面材＋縫 → 選擇材料規格」進入，可選已發布面材、直接新增面材或重用做法，明設方向、縫寬及起算點後，一次預覽並確認建立網格。選面材時會明示一起建立的排格做法；既有角材不自動改綁。管理材料、做法及批次套用仍從「檔案 → 工程規格 · 面材與角材」進入；已綁定物件會顯示來源、生效尺寸與覆寫入口。

材料／做法改版不自動改動既有引用；選面升級時會預覽所有連帶影響。保存完整來源與未發布草稿用 `.gcanvas`，攜帶材料及做法用正式做法包。操作見 [工程規格操作說明](docs/ENGINEERING-SPEC-USE.md)，格式見 [正式工程做法包](docs/ENGINEERING-PACKAGE.md)，檢查紀錄見 [專案缺口補齊](docs/PROJECT-AUDIT-20260928.md)。

## 從面建立 3D 空間（第一版）

目前「工程規格版 2026.09.28」整合了空間與角材建模：可在面物件上指定空間邊界平面投影、俯視／仰視及室內淨輪廓，並將所選放置面上已放好的角材一併建模。從面工作區按「建立空間」；用途尚未定義時，可在同一視窗選擇俯視／仰視，按「確認用途與觀看方向」後繼續。原「平面投影」入口仍可編輯完整定義與圖面 z；詳見 [面投影定義](docs/FACE-PROJECTION.md) 與 [角材納入規則](docs/TIMBER-IN-SPACE.md)。

左欄「從面建立 3D 空間」提供矩形、L 形現成範例與介面內三步引導；自己的面可從面工作區「建立空間」進入。牆高預設 **3000 mm**，明確指定牆底與邊界後預覽，再核對建立；圖面 z 不代替牆高。材料牆預設 100 mm 向外加厚，可修改或不建立。

模型保存於 `.gcanvas` 專案的「已建立空間」，可透過「修改牆高 → 更新預覽 → 更新空間」調整已建平面模型，更新同一模型，支援重開及復原／重做。舊模型保留原高度；組合既有面的模式沒有單一牆高編輯。來源日後修改不會自動更新已建立模型。操作、格式及限制見 [第一版操作說明](docs/SPACE-MODELING.md)。

Windows 已安裝 WSL／GCC／Python 時，可用 `powershell -File .\geometry-web\start-space-model.ps1 -Port 18841` 從 repo 根啟動；入口為 `http://127.0.0.1:18841/#engineering-spec-v1`。選用空閒連接埠；啟動器不停止其他服務，會核對新服務工程能力及 z=2500～2533 骨架幾何。左欄空間建模仍提供 7 支角材的現成範例。

## 框選與多選（GEO-209／GEO-212）

物件畫布與面內角材可用「選取 V」從空白處拖曳框選：**向右完整框住才選取（藍色實線）；向左相交即選取，碰到邊或角也算（綠色虛線）**，往上或往下都適用。Shift＋點選加入／取消，Shift＋框選加入，Ctrl／Cmd＋A 全選目前範圍，空白鍵＋拖曳或 H 平移。畫面顯示已選數量及目前方向規則；多選可核對清單，編輯／移動／刪除仍先單選個別物件。3D 預覽與三視圖維持原操作。規則與驗收見 [畫布選取](docs/CANVAS-SELECTION.md)。

## 跨面共用基準

「檔案 → 共用基準」依序可建立具名尺寸、世界 X／Y／Z 基準，再讓各承載面引用。
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
只輸入截面 A/B，不再輸入長度。具名規格與參考線引用式可在面內「構件」頁的參考線區建立；工具列「參考線」也可直達。
會影響已放角材時，畫面列出新舊中線、長度與違規；按「確認套用」才改場景。
有違規或取消都保留原狀。詳見 [語法與驗收紀錄](../geometry-core/README.md)。

Windows 如被 Smart App Control 擋住未簽章程式，使用已安裝的 WSL：

```powershell
powershell -File .\start.ps1 -Port 8765
```

此啟動器重新編譯目前原始碼，在 WSL 跑核心、Windows 跑網頁服務；不更動系統安全設定。
需現有 Ubuntu-24.04、gcc、Windows Python。可用 `-Distro` 指定其他已安裝的發行版。

## 啟動

從 repository 根目錄執行下列原生 Windows 開發流程；角材結構建模的現成範例與能力檢查請使用本頁開頭的 `start-space-model.ps1`。

```bat
cd geometry-web
build.bat                  :: 編譯 web_bridge.exe（首次或 C 端變更後）
python serve.py 8765       :: 啟動靜態檔 + /api 橋接服務
```

瀏覽器開 `http://localhost:8765/`。

`serve.py` 行為：

- `GET /` → `index.html`；`GET /app.css`、`/app.js`、`/reference-ui.js` → 同名靜態檔。
- `GET /scenes` → 上層目錄 `*.scene` 清單。
- `POST /api`（JSON `{"cmd": "..."}`）→ 轉送給長駐 `web_bridge.exe` 的 stdin，回傳其 stdout 一行 JSON。
- `POST /upload` → 把 scene 內容寫成系統暫存目錄（`tempfile.gettempdir()`，Windows 為 `%TEMP%`）下的暫存檔並 `loadfile`；回應帶 `path` 欄位，前端 `curScene` 指到它，「重新載入場景」才會載回剛上傳的內容。
- `POST /feedback` → 回報收件匣（GEO-183，見下節），寫進 repo 的 `feedback/<id>/`；`GEOMETRY_FEEDBACK_DIR` 可改落點（測試用）。
- POST 跨站防護（L3）：`Origin` 存在且非 `http://127.0.0.1:<port>` / `http://localhost:<port>` → 403；`Host` 非本機 → 403；無 `Origin` 的 curl/測試腳本放行。`cmd` 含 `\r`/`\n` 或超過 4094 bytes → 直接回 `{"ok":false}` 不送 bridge。

## 回報收件匣（GEO-183）

操作當下就把「哪裡怪」連同現場一起存下來，不必事後回憶，agent 也不必從口述猜是哪個功能。

- **F8** 或右下「回報」鈕開面板：選分類（問題／不符預期／建議／好用）、寫一句話（可留空）、
  「指出位置」點畫面上的元素、在說明欄 **Ctrl+V 貼截圖**（Win+Shift+S 截的圖可直接貼）。**Ctrl+Enter** 送出、Esc 取消。
- **Shift+F8**：不開面板，直接存一筆「快速標記」——手上正忙、只想先釘住「剛剛那下不對」。
- **自動擷取**：未捕捉的 JS 例外、Promise 拒絕、橋接器／伺服器斷線會自動存一筆（20 秒內最多一筆、同一原因 5 分鐘一次）；
  條文拒絕（`ok:false`）是正常行為，不自動存。伺服器寫不進去時暫存在瀏覽器，下次成功送出時補送。
- 每筆帶走：回報前最多 1000 筆操作（api 指令與回應、點擊與指到的元素、按鍵、改值、toast／狀態列、錯誤）、
  當下世界 `world.scene`（bridge dump）、畫面快照 `page.html`（內嵌 CSS、無 JS，紅框＝指到的元素）、
  應用程式狀態（`oc`／`fe`／三視圖工具）、視窗大小、git 版本。
- 落點 `feedback/<F-YYYYMMDD-NNN>/`（`.gitignore` 允許清單制，不進 git），索引 `feedback/INBOX.md` 自動重產。

agent 端：

```sh
python geometry-web/feedback_cli.py list              # 未處理
python geometry-web/feedback_cli.py show <id>         # 摘要 + 最後 40 筆操作
python geometry-web/feedback_cli.py events <id> -n 300
python geometry-web/feedback_cli.py replay <id>       # 列出改世界的指令,並用 core.exe 載回當下世界
python geometry-web/feedback_cli.py close <id> "已修 <commit>"   # 或 --status wontfix / cannot-reproduce
```

## 測試

測試分別驗證核心、前端整合與實際輸入；通過斷言數不等於獨立的端到端情境數。必須記錄實際執行範圍，略過或環境阻擋不算通過。

```bat
:: 1) 橋接器／幾何測試（不執行畫布 DOM）
node canvas_test.js direct

:: 2) headless Chrome 混合整合測試（先用相同 feedback 目錄啟動獨立測試服務）
set GEOMETRY_TEST_URL=http://127.0.0.1:8799/
set GEOMETRY_FEEDBACK_DIR=%TEMP%\geometry-tests\fb-cdp
node cdp_test.js

:: 新公理表單、確認/取消、非法預覽、扣孔命中的快速實機驗證
node reference_smoke.js

:: 3) 伺服器輸入與故障處理（不需要真實 bridge 或瀏覽器）
python -B -m unittest discover -s ../tests -p test_serve.py -v
```

`canvas_test.js` 的 HTTP 模式可用 `GEOMETRY_TEST_URL` 指定獨立測試服務。`cdp_test.js` 與 `space_model_test.js` 必須明設測試 URL 與 TEMP 下獨立回報目錄；未設時在開啟瀏覽器／重置場景前拒絕。服務與測試應指向同一實際目錄；Windows／WSL 使用各自對應路徑。

`cdp_test.js` 只計受控斷言，頁面日誌及狀態文字中的勾號不計數。執行例外與協定錯誤必須失敗；`CDP_SCOPE`／`CDP_RESULT` 明列全套或部分執行，不能把專項結果說成全套。完整回歸不得設定 `*_ONLY`／`GEOMETRY_CDP_FROM_P31`。工程子範圍必須搭配工程專項旗標，且互斥。

`space_model_test.js` 的結果也列出 included／omitted 群組；一般空間、角材、流程等專項分開，不合併冒充單次完整執行。保存下載流程不代表原生另存視窗，390px 版面不代表真手機觸控。原型目錄內的測試只證明原型，不作正式畫布整合證據。
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
GEOMETRY_BRIDGE=/opt/geometry/web_bridge GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/fb-cdp python3 serve.py 8799 &

GEOMETRY_CHROME=google-chrome \
GEOMETRY_CHROME_PROFILE=/tmp/cdp-profile \
GEOMETRY_CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage" \
GEOMETRY_TEST_SCREENSHOT=/tmp/phase1-shell.png \
GEOMETRY_TEST_URL=http://127.0.0.1:8799/ \
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/fb-cdp \
  node cdp_test.js
```

測試環境變數（URL 與回報目錄必填，其餘依需覆寫）：

| 變數 | 用途 |
|---|---|
| `GEOMETRY_BRIDGE` | `serve.py` 要啟動的橋接器**指令**（可帶參數；預設同目錄 `web_bridge.exe`） |
| `GEOMETRY_BRIDGE_WSL` | 設為 `1` 時，把送進橋接器的場景路徑由 `D:\…` 翻成 `/mnt/d/…` |
| `GEOMETRY_CHROME` | chrome 執行檔（預設 Windows 的 `chrome.exe`） |
| `GEOMETRY_CHROME_PROFILE` | `--user-data-dir` 位置 |
| `GEOMETRY_CHROME_FLAGS` | 追加旗標，空白分隔；WSL 內以 root 跑需要 `--no-sandbox` |
| `GEOMETRY_TEST_URL` | 必填，明確指定獨立測試服務網址 |
| `GEOMETRY_TEST_SERVER_PATH_STYLE` | Windows 上執行 CDP 測試、服務位於 WSL 時設為 `wsl`，將測試建立的暫存場景轉成服務可讀的 `/mnt/<磁碟>/…` 路徑；同系統執行時留空 |
| `GEOMETRY_FEEDBACK_DIR` | 必填，TEMP 下的專用回報目錄；serve.py 與測試必須指向同一實際位置 |
| | **Chromium 141+ 在 Linux 容器內請用 `http://127.0.0.1:<port>/`**，並在 `GEOMETRY_CHROME_FLAGS` 加 `--disable-features=HappyEyeballsV3`：新版 HttpStreamPool 對 `localhost` 每次先試 `::1` 失敗再退 `127.0.0.1`，約 600 次請求後 socket pool 會卡死（P5b 永遠等不到 `pick` 回應）。2026-09-25 以 netlog 確認，與應用程式碼無關。 |
| `GEOMETRY_TEST_SCREENSHOT` | 截圖輸出路徑；未設時使用系統暫存，不覆寫已提交的文件截圖 |

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
| `serve.py` | 靜態檔 + `/api` + `/scenes` + `/upload` + `/feedback` |
| `feedback.js` | 回報收件匣前端（黑盒子錄製、F8 面板、自動擷取；在 `app.js` 之前載入） |
| `feedback_store.py` / `feedback_cli.py` | 回報的寫入／INBOX 產生，與 agent 端 list/show/replay/close |
| `web_bridge.c` | C 橋接層（編成 `web_bridge.exe`，**公理層真相**） |
| `canvas_test.js` | 直接裁判 |
| `cdp_test.js` | CDP 實機裁判 |
| `docs/UI-REDESIGN-PLAN.md` | UI 重構唯一事實來源（SSOT） |
| `docs/DOM-CONTRACT.md` | 測試依賴合約 |
| `docs/prototype-構形Canvas-v2.html` | 視覺/互動原型參考 |

## 鍵盤（§5.8）

- 主畫布：`Ctrl+Z`/`Ctrl+Y`/`Ctrl+Shift+Z` 復原重做、`Esc`、`v` 選取、`h` 平移、`r` 矩形、`p` 建面卡並進面內畫外環（GEO-186 b：非持續工具）、`f` 全部顯示、`1` 縮放 100%、`空白`暫時平移、`/` 聚焦搜尋、`Delete`/`Backspace` 刪除選取的卡片（同右欄刪除鈕，可 Ctrl+Z；輸入框內與繪圖工具進行中不作用）。
- 面·多邊形外環在**面內工作區**畫（`e`／「重畫外環」，實際 mm）：點頂點或數字鍵鍵入長度、`Enter` 定長／閉合、`Backspace` 退一點、`Esc` 依序清數字→清草稿→離開工作區。
- 面內工作區：`Esc`、`v`/`l`/`r`/`h`/`t` 角材/`e` 重畫外環、`f` fit、`1` 縮放 100%、`空白`暫時平移。
- 面內工作區形狀編輯（GEO-188）：select 下單擊邊/凸角/面內 → 浮動列選「凹口／外凸／推拉／切角／開口／F⇄X」；面板內 `Enter` 套用、`Esc` 關面板。
- 重畫外環（GEO-189）：`e` 後直接打數字＋方向鍵 `← → ↑ ↓` 逐段畫（沒點第一點就從原點起）；`Enter` 閉合（末點與起點不同軸時自動補角）並回到選取；`Backspace` 沒有數字時退一點。
- 重畫外環補角提示（GEO-193）：自動補角如果把剛畫的一個轉折併回直線（例如少畫最後一段、或補角吃掉了刻意留的缺口），閉合成功後仍會落地（不擋），但狀態列與提示會列出被併掉的座標，例如「已閉合；補角時 (3000,1000) 併入直線——若要保留該轉折，`Ctrl+Z` 後把下一段畫完再閉合」；直接同軸閉合（沒有補角）不會有這則提示。
- `Esc` 實際階梯（單次按）：輸入框聚焦中 → 留給原生（不關工作區）；開著的選單 → 收；開著的對話框 → 關；面內鍵入長度暫存 → 清；面內方向小選單 → 收；**面內右鍵選單 → 收（GEO-192）**；面內量比例尺進行中 → 取消（不離開工作區）；面內就地操作面板 → 關；面內有選取的邊/角/點/角材 → 清；進行中草稿 → 清並提示「再按 Esc 返回」；以上皆非 → 返回上一層焦點/世界。
- 面內游標互動（GEO-192，select 工具）：`Alt` + 拖外環凸角 = 捏出一塊缺口（不按 `Alt` 照舊拉角）；就地操作面板開著時可直接拖畫布上預覽矩形的四條邊改尺寸（放開不套用，仍要 `Enter`/套用鈕）；右鍵點邊/角/面內空白/角材 = 先做與左鍵單擊相同的選取，再彈出選單（內容與浮動列相同），右鍵面外空白只清選取；雙擊邊 = 直接開「凹口」面板、雙擊凸角 = 開「切角」、雙擊面內空白 = 選點並開「開口」、雙擊角材 = 開角材頁並選取該角材。

## 架構約定

- C 端（`../current_geometry.c`、`web_bridge.c`）改動須重跑 `build.bat` 並過兩套測試。
- 多行變更走 `mutate(lines)`：包成 `history-begin`/`history-end` 群組 = 一步 undo（L2）；群組內任一行失敗核心自動整組回滾不留半套，前端再送 `history-abort` 驗證，回滾失敗 toast「回滾失敗，狀態可能不一致」。
- 參考線：使用 bridge `references` 的來源、世界位置／方向與裁切段；不得從顯示數值反推引用定義。

## 形狀編輯（GEO-188，`docs/uiux-review/形狀編輯提案.dc.html` 方案 A + B）

- **邊優先（A）**：select 工具單擊外環邊 → 邊亮起、浮動列「凹口／外凸／推拉／F⇄X」；單擊凸角 → 「切角」；單擊面內空白 → 「開口」（填寬、高、距左／右、距上／下）。
  切角面板同時有「切掉 a、b」與「留下」欄，兩邊連動；凹口面板多一格「留底」。
  選操作後就地面板填「定位（從左／置中／從右）＋距離、寬、深」（推拉：往內／往外＋距離；切角：a、b），
  畫布即時畫紅（減）／綠（加）預覽矩形，`Enter` 套用、`Esc` 取消。拖邊仍是推拉。
- **幾何**：`feRectBool(loops, "sub"|"add", rect)` 純函式做正交多邊形對矩形的布林（頂點座標切格 → 取邊界環），
  結果一律走 `boundary` 重宣告交易，核心 I2 守門；面消失或拆成兩片在前端就擋下（toast）。
  新邊 fixity：與舊邊共線重疊者繼承，其餘 FIXED（對齊公理層 R7「套用產生的新邊 fixity 一律 FIXED」）；
  新環的走向與起點盡量沿用舊環，沒被動到的邊保住 `e<i>` 編號。
  會動到被角材引用的邊時，核心照 I8a 回 `preview`，`api()` 照舊開影響預覽對話框，確認才落地。
- **形狀頁（B）**：檢視器「形狀」分頁列出本次工作階段套用的特徵（寬、高、距左／右、距上／下，可改起算邊），
  改數字即落地（反向布林還原再正向套用）、可左右／上下鏡射、可刪除（反向布林）。
  **特徵堆疊只存在記憶體，不寫進 .scene**——核心只認最終輪廓；每次邊界變更後逐筆驗活，對不上的自動剔除。
- **描繪指定尺寸的多邊形**：最直接的路是「外環」工具純鍵盤：`e` → `4000 →` `1500 ↓` `2500 ←` `1500 ↓` `Enter`，就是一個 L；之後再用上面的操作修。
- 「開口」拖矩形工具保留，但改走同一套布林並記進特徵（全在面內 = 孔、碰到邊 = 凹口、蓋到角 = 切角，矩形裁到外接框）；圖層列的孔可直接刪除。
- 特徵的距左／右、距上／下以**現況**外環外接框起算（推拉／外凸後數字跟著現況走，才是真距離）；起算邊在建立時取較近一側並固定，之後不會左右翻轉。
- 舊的「凹口」工具（點邊開對話框、`i` 快捷鍵、`#notchDialog`）已移除，凹口只走上面的流程；「外環」重畫與形狀庫保留。

## 面內底圖臨摹（GEO-190）

檢視器右欄第 6 分頁「底圖」：放一張掃描/照片平面圖在面內底下，照著描外環。**只存在本次瀏覽器工作階段的記憶體**（`oc.underlays[bid]`）——不寫進 `.scene`、不寫 `localStorage`；離開這片面再進來仍在，重新整理瀏覽器就沒了。核心（`web_bridge.c`、`.scene` 格式）不動，純前端功能。

- **選圖**：分頁按「選圖片」讀本機圖檔；預設比例尺 = 面外接框寬 ÷ 圖片寬（px），對位原點取外接框左上、不透明度 0.5、不旋轉。
- **對位**：拖曳畫布上的底圖改 X/Y，或直接在分頁填 X/Y（mm，圖片未旋轉時左上角的面座標）；旋轉限 0°/90°/180°/270°；「鎖定」後底圖不可拖，也不吃畫布事件。拖曳只在「底圖」分頁作用中、`select` 工具、未鎖定時生效，不會擋到點邊/點角/點面/畫外環等既有互動。
- **量比例尺**：按「量比例尺」→ 在圖上點兩點（畫布會畫出兩點與連線）→ 填這兩點的實際距離（mm）→「套用」，程式算出 mm/px；套用時對位 X/Y 不變。進行中按 `Esc` 只取消量比例尺，不離開工作區。
- **移除**：分頁「移除底圖」清掉這片面的底圖狀態。

## 面內角材可選取（GEO-191）

select 工具下點角材矩形可選取（之前點角材沒反應、會被當成點面內空白）。GEO-191 只做選取、高亮、刪除；就地編輯見下一節 GEO-194。

- 畫布：點角材矩形 → 矩形高亮（`.sel`）、左欄該列同步高亮，浮出 `#feActionBar` 只有一顆「刪除」。其餘工具（重畫外環、開口、放角材……）下矩形不吃事件，不擋既有互動。
- 左欄角材列：hover → 對應矩形高亮（`.hover`）；點列（非 ✕ 鈕）＝與畫布點選相同效果。
- 檢視器「角材」分頁頂端顯示「已選角材 `<id>`」的編輯表單（GEO-194 後取代原本的唯讀摘要）與刪除鈕；刪除走既有「刪除角材」（`delete timber`）路徑，可 `Ctrl+Z`。
- 點面內空白（非角材）／點外環邊或角／`Esc`，行為與既有（GEO-188/189）一致；邊界變更或角材被刪後，若選取的角材已不存在會自動清選取。

## 面內角材就地編輯（GEO-194）

選取角材後，「角材」分頁頂端的 `#tbEditForm` 可直接改截面 A/B、角色（custom 要填 priority）、方向（+u/−u/+v/−v）、側（+n/−n）與錨點（定位邊／參考線／格線＋選擇器）。截面、角色、方向、側會預填現況；**錨點不預填、要重選一次**（橋接的 `references` 指令目前不回傳錨點，後續票）。

- 「套用變更」＝同一個 id 刪掉重放，一筆交易：`delete timber <id>` → `timber <id> A B role …` → `place <id> on <面> <錨點> <選擇器> <方向> <側>`；核心拒絕（例如非 boundary 角材頂到 RC 邊）就 toast 原文、什麼都不變。
- 影響預覽照舊：刪唯一的邊界材或動到被引用的邊，會彈既有的 I8a 影響預覽對話框，確認才落地。
- `Ctrl+Z` 一次回到編輯前；套用後選取仍留在該角材。
- 表單驗證與放置表單相同：A/B 為正整數 mm、custom 角色必填 priority、錨點必選。

## 角材放置表單 UX 止血（GEO-195）

不改放置流程——點面內永遠只是「確認」，不是輸入位置；只是讓人在點擊前就知道角材會落在哪、失敗了該怎麼改。

- **定位引用下拉**：已被別支角材占滿的邊/參考線/格線，選項文字後加「(已有角材 N)」並排到清單後面；預設自動選第一條未占用的。全部占滿時表單多一行提示「所有定位引用都已有角材，先加參考線(L)」。
- **畫布預示**：角材工具啟用中，或滑鼠移到／點進「定位引用」下拉時，畫布上會畫出那條線的虛線標示，並依目前深度(+n/−n)/A 畫一條半透明帶示意角材會占的位置（標「示意」——真正長度仍由引擎依支撐推導；帶固定沿定位引用展開，跟「方向」欄無關）；切工具或切開別的檢視器分頁就消失。角材工具下狀態列與畫布角落浮標會寫「角材將沿「〈定位引用名〉」放置，點面內任一處確認；點擊位置不影響位置」。
- **失敗訊息**：放置失敗時，前面會多一句白話說明：定位引用已被占滿會講「已被角材 N 占滿——請換定位引用（列出可用清單）」或「請先加參考線」；違反主支軸規則會講「主支軸是 u/v，沿它放只能選 primary」；違反 RC 優先權會講「貼外輪廓邊的角材要選 boundary」。原始規則代號還是接在後面。
- **角色選單**：已有一支「主支」角材時，方向與主支軸平行只能選 primary，垂直則 primary 停用（改選項時若原本選的角色不能用，會自動換成可用的並提示一句）。

## 角材工具下「點畫布上的線」直接放置（GEO-196）

GEO-195 的「表單先選定位引用、再點面內確認」路徑**完全保留、一字不改**；這裡加一條新路徑，直接點想放的那條線：

- **點外輪廓邊或參考線**：以那條線為定位引用，右欄「定位引用」下拉自動同步選到它；**方向**沿該線的軸，固定取正向（+u 或 +v）；**角色**依主支軸規則（D17）自動帶入——主支軸已推導出來時，方向平行給 primary、垂直給 boundary（外邊）／secondary（參考線）；還推導不出來時，外輪廓邊給 boundary、參考線給 primary。**厚度方向（深度 +n/−n）一律看右欄表單，不由點擊點的左右決定**（G196-R02 修正：±n 是朝承載面法線哪側伸出，點在線的左邊右邊只是畫面位置）。右欄的 A/B、選段、custom priority 仍照表單目前值。算完立即走既有的放置流程（同一段交易），成功後表單保留這次帶入的值，方便連續放下一支。
- **點已被占滿的線**：照舊送出，由引擎拒絕，GEO-195 的人話錯誤訊息接手——前端不做占用判斷，只是近似提示。
- **點孔邊**：跳出提示「目前不支援直接點孔邊——請從右欄『定位引用』選孔邊」，不送指令；孔邊本身公理允許當定位（`at-face h<i>e<j>`），是這條快捷點選路徑還沒做，走右欄下拉一樣可以選到。
- **點面內空白**：照舊——用右欄表單目前的設定放置（含負向長度軸），這條路徑完全沒變。
- **格線目前不能點**：格線（虛線點狀網格）還沒有可命中的元素，只做了外輪廓邊與參考線；這是已知限制，留給下一票。
- **滑鼠預示**：角材工具下滑過一條可以當定位引用的線，畫布上的虛線+半透明帶預示會改成跟著滑鼠指的那條線走，游標也變成「可點」的樣式；移開滑鼠、離開線，預示會回到右欄目前選的那條線（跟 GEO-195 原本的行為一樣）。半透明帶是「橫向定位示意」：`at-line` 以線為中線置中展開、`at-face` 貼材料側、自動扣除孔位；±n 只影響出畫面方向的厚度，不影響這條帶。
- 提示文字：「點外輪廓邊或參考線選定位直接放置；厚度方向依右欄『深度』設定。點面內空白則依右欄設定放置」。

## 面內工作區的四種游標互動（GEO-192）

在 GEO-188/189/191 既有的「單擊選取 → 浮動列 → 就地面板」流程上，補純游標也能做到的四種互動；**不改動核心引擎、`.scene`、`serve.py`、`index.html` 既有結構**（只加新元素）。

- **Alt + 拖外環凸角捏缺口**：`select` 工具下按住 `Alt` 拖外環（不是孔環）的凸角，畫布即時畫紅色預覽矩形（頂點到游標，吸附格線，裁到外環外接框且不超過鄰邊長）；放開後走**與切角面板套用完全相同的路徑**（`feRectBool("sub", rect)` → 交易 → 記進「形狀」頁，`type` 為 `corner`）。不按 `Alt` 完全是原本的拉角（`applyVertexEdit`）；矩形太小（<1mm）或拖曳中按 `Esc` 都直接取消，不送指令。
- **拖預覽矩形的邊改尺寸**：`#feOpPanel` 開著時，畫布上的紅/綠預覽矩形四邊各有一條可拖曳的粗描邊（`cursor: ew-resize`/`ns-resize`）。拖哪條邊就只有那條邊動、另一側固定：與母邊平行的邊界改「寬 w」（連動改定位讓另一端不動），與母邊垂直、不與母邊重合的邊界改「深 d」（或推拉的距離）；面內開口／切角比照對應欄位。面板欄位隨拖曳即時同步，放開不自動套用，仍要 `Enter` 或按套用鈕。
- **右鍵選單**：畫布上右鍵先做與左鍵單擊完全相同的選取（邊/角/面內空白/角材/面外空白皆同一套邏輯），再在游標處彈出選單；選單內容與浮動列 `#feActionBar` 是同一份資料來源（一定逐一相同），點選單項目效果與點浮動列相同。右鍵面外空白只清選取、不顯示選單。點選單外任一處、`Esc`、滾輪縮放都會關閉選單。
- **雙擊**：直接開該目標最常用的操作面板——雙擊外環邊開「凹口」、雙擊外環凸角開「切角」、雙擊面內空白選取該點並開「開口」（可填寬高與距邊）、雙擊角材切到「角材」分頁並選取它。雙擊不靠瀏覽器原生 `dblclick` 事件（單擊選取會整份重繪畫布，原生事件的節點參照常常來不及冒泡就被拔掉），改成 `pointerdown` 自己量時間與螢幕位移判斷。

## RC 柱樑與投影套用（RC-POLYGON-PLAN）

- **柱/樑是一等物件**：物件庫「＋柱」「＋樑」→ 對話框建立 → 卡片可拖、檢視器改尺寸（重宣告）、`objects` 回傳 `columns[]`/`beams[]`。DSL：`column`/`beam`（語法見 `docs/RC-POLYGON-PLAN.md` 附錄 A）。
- **障礙物鬼影**：面內工作區呼叫 `obstacles <bid>`，把同空間柱樑投影成分類矩形（孔/凹口/角凹/條帶/拆分/頂凹/頂降），半透明顯示不改 boundary。
- **套用投影**：圖層列勾選鬼影 + 「套用 N 項投影」→ `apply-proj <bid> <item>… [cut-strip]`，單一交易：孔入環、凹口改外環、拆分產新面（原 id 留最大片、孔隨片走、拆片退出空間成員）。快照式，與柱樑無連結。
- **空間工作區**：平面示意圖點放柱、拖放樑、構件收/出清單；空間→柱樑畫「障礙」連線。
