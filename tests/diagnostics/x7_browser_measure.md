# X7：真 App 大場景延遲量測

這支診斷程式提供真 Chromium 的可重跑量測入口，**本次作者環境沒有執行 Chromium，瀏覽器數值、流程可達性及預算是否通過均未驗**。它不屬於 canvas 登錄段，不產生 CI 成本或突變收據，也不把 `acceptance:false` 改為驗收通過。原生預算與其先紅後綠證據由 X7 的原生測試另行處理。

編寫及靜態核對基底為 `4c4028f8f80f09963f14a46062cbfcf8db76637b`。執行時會另外記錄實際 Git HEAD、診斷程式 SHA-256、bundle SHA-256、原生執行檔的官方 freshness 檢查、App `/runtime` 的來源版本，以及 Chromium／Node 版本。工作樹若包含待測 P，不能只拿 HEAD 當作 P 的來源證明；請連同套用的補丁雜湊保存。

## 可重跑命令

以下為 Linux worker 的完整命令範例。在已套用待測補丁的 repo 根目錄、一般使用者帳號下執行；`--chrome` 要填 worker 已安裝的真 Chromium 路徑。腳本需要有原生 `fetch`、`WebSocket` 的 Node 環境（與現行 CDP 工具相同），並使用 repo 內已有的 ZIP 函式庫。

```sh
python3 -B tests/binaries.py build bridge
python3 -B tests/binaries.py status bridge
python3 -B tests/diagnostics/x7_scenarios.py --bridge /tmp/geometry-tests/bridge --out /tmp/x7-scenes-base
node tests/diagnostics/x7_browser_measure.cjs --bundle /tmp/x7-scenes-base/browser-bundle.json --bridge /tmp/geometry-tests/bridge --chrome /usr/bin/chromium --out /tmp/x7-browser-base --samples 3
```

每次重跑使用新的 `--out`，例如把兩個 `base` 分別改為 `patched`。`--bundle` 指向 generator 真實產生的檔案；不可自填 `.scene`、數量、bytes、SHA-256 或收據。需要指定 Python 時加 `--python /絕對路徑/python3`。Windows 的 bridge／Chromium 路徑要使用該 worker 的實際安裝位置；Windows 及 OS 對話框操作本片未驗。

腳本自己啟動獨立 port 的原生服務、全新 Chrome 行程及全新 profile，結束時只停止它啟動的兩棵行程。Linux 服務沿用正式 `start_local.py` 的 16 MiB stack 前提，沒有改產品時限或放寬 stack 守門。腳本不接管已有 App、不清使用者的瀏覽器資料，也不加停用 Chrome sandbox 的旗標。輸出與 profile 路徑會留在報告中供查核；不會刪掉失敗證據。

## 三個場景與量測範圍

| case | 世界角材數 | 房間 | 批次操作 | 明示限制 |
| --- | ---: | ---: | --- | --- |
| `room53` | 53 | 1 | 正式面設定入口，`flat-ceiling/2` 預覽 53 支並一次確認 | 矩形 3740 × 3301 mm、無孔、明設 RC；量目前政策 A 固定治具的實際入口 |
| `f1_111` | 111 | 1 | 經「開啟場景檔…」載入既有 oracle 產生的真 F1 場景 | F1 為凹形且有孔；目前 main 的 R03 模板拒絕此範圍，沒有宣稱一鍵生成 F1。歷史約 116 支不是這次現行 oracle 的數字 |
| `house500` | 500 | 5 | 先載入 416 支，再由第 5 房正式 R03 入口預覽／確認 84 支 | 三個 111 支 F1 加上 83、84 支矩形房；不是同一面一次生成 500 支，也不是多面整批生成入口 |

三者共用 `x7_scenarios.py` 的 bundle。每份 before／completed／geometry 原件先核 bytes 與 SHA-256。矩形房的 UI 配方另核固定模板版本、政策指紋、六個參數及起鋪角／板長方向，不接受 App 預設悄悄改變後仍只對支數。

每個 case 在 1400 × 900 與 390 × 844 各跑 3 次（`--samples` 可明設 1–10）。`first-observed` 表示該寬度第一圈，`repeat` 表示其餘圈；這不是每次重啟行程的冷啟動比較。390 px 是桌面 Chromium 的窄視窗與行動裝置 viewport 模擬，不代表實體手機。

確認後的骨架在 main 面內呈現仍有已知缺口。報告分開記錄目前焦點、`faceTimbers`、面內料單列數及三視圖的全世界角材 ID 數；不能把世界有 500 支寫成當前單面或同一張預覽圖顯示 500 支。三視圖重繪另斷言 53／111／500 個不同角材 ID 都有繪圖節點；這只證明 DOM 幾何呈現，不證明每支在窄視窗可讀或未互相遮蔽。

## 計時邊界及狀態核對

所有 UI 計時都先安裝觀察器，再用 CDP Input 點真正控制。開始點取頁面捕捉到的**本次可信輸入事件**，不是 Node 發指令前的時間。完成條件必須同時包含本次輸入之後的新請求、該操作的新狀態、相關 DOM 穩定後的兩次新 `requestAnimationFrame`；不以舊成功狀態或固定等待代替。

| `operation` | 新請求／新狀態 | 計時之外的內容核對 |
| --- | --- | --- |
| `load_before_scene`、`load_complete_scene` | 真檔案選擇入口的 `change` → 新 `/upload` → 新專案 context、已載入訊息、輸入清空、重繪後的物件卡 | 載入後世界角材數；fixture bytes／SHA-256；不包含使用者停留在選檔器的時間 |
| `load_confirm_f1_scene` | 同上，從空場景載入 111 支 F1 | 0 → 111；後續復原回空場景、重做回完整 F1；明列 R03 模板未支援 |
| `preview_batch` | 新 `/framing-template/preview` → `confirmable` 且確認控制可用 → 兩次新 rAF | 精確 53／84 列候選；原生 dump 及歷史項身份完全不變。`confirmable` 本來屬 pending，不能錯等 `pending=false` |
| `confirm_batch` | 新 `framing-template-confirm` → `committed`、pending 解除、新 undo 項 → 兩次新 rAF | 世界數與新增數精確相符；沿用 `makeHistoryOracle` 核一筆歷史，含 32 格已滿時的 retained entry 身份 |
| `undo`、`redo` | 新 `line undo`／`line redo` → 新 history frame、App busy 解除 → 兩次新 rAF | native dump 逐字回到操作前／後；不靠堆疊長度或數量相同冒充 |
| `save_as_download` | 新 `dump` → `saveOutcome.seq` 本次增加且成功、busy 解除 → 兩次新 rAF | 另找本次唯一完整 `.gcanvas`，解 ZIP 核 `world.scene` 等於重做後 dump 及 manifest 的 scene hash |
| `three_view_redraw` | 真「三視圖」控制 → 新 `/view/read`／`render` → 新 world 繪圖節點 → 兩次新 rAF | 全世界不同角材 ID 數精確為 53／111／500 |
| `timber_select` | 真畫面角材的 `pointerdown` → 新 `/view/pick` → 新選取的精確角材 ID、選取呈現、busy 解除 → 兩次新 rAF | 顯示與選取前後 native dump 完全相同 |

選取的點先從真繪圖幾何取候選，再用最多 32 次、8 秒內的原生只讀拾取確認有可選角材。這個找點準備不算進使用者點選延遲；正式計時仍要求新的真指標事件和新的拾取回應。沒有在計時前直接設定 `selected` 或呼叫點選 handler。

請求觀察器回傳原來的 fetch promise，不替換回應、不等 clone／JSON 解碼，也不呼叫產品重繪函式。raw 裡的請求 `end` 是 fetch promise 回傳 response 的時間，**不是回應 body 解析完畢或整體操作完成時間**；整體仍由操作專屬狀態與兩次 rAF 決定。兩次 rAF 是瀏覽器的繪製機會，沒有宣稱量到螢幕實際掃描輸出。

保存會固定走產品既有的下載後備路徑（新 profile 內把 `showSaveFilePicker` 設為不可用，做法沿既有 archive harness）。`saved_archive_evidence.browserBytesVerifiedMsUpperBound` 是另一個上界，額外包含主機檔案輪詢、CDP 往返、ZIP 解碼及 hash 核對；它不是純前端重繪時間，也不是 OS 持久寫入時間。OS 原生保存／選檔對話框、檔案系統 durability、完整專案重新開啟及附件復原不在本片量測範圍；載入量的是 `.scene` 正式入口。

## 輸出與失敗處理

- `samples.jsonl`：每個操作的原始樣本、自己的新請求與頁面時間、long task、viewport、可見範圍；失敗樣本照樣保留。
- `report.json`：schema `x7-browser-measurement/1`，整體 `measured` 或 `failed`，固定 `acceptance:false`，含來源、實際版本、所有樣本、例外與對話框記錄。
- `server.stdout`／`server.stderr`、`chrome.stdout`／`chrome.stderr`、`bridge-inspection.stdout`／`bridge-inspection.stderr`：原樣輸出。
- `downloads/`：實際產生的 `.gcanvas`；下載原件的 bytes、SHA-256 與內容核對結果寫入樣本。
- `feedback/`：這個隔離測試 App 的自動錯誤回報，不混進使用者的回報目錄。

操作截止為 30 秒，服務／瀏覽器啟動截止為 20 秒。這只是診斷程式的有限等待界線，不能把「30 秒內結束」當成 X7 效能預算通過；本片沒有變更任何既有測試的斷言或時限。只要錯誤、逾時、支數不符、dump 不同、歷史步不符、下載內容不符、瀏覽器例外或來源版本改變，就保留 raw 並以非零結束。不要刪除首跑失敗後只交隔離重跑。

worker 回報須附完整命令、結束碼與原始輸出位置，說明每個 case、寬度及 repetition 是否走完。尚未取得這些原件前，本片只能列「量測工具已交，真瀏覽器未驗」；不提高 R03／R04／R05 的 L0–L5 層級，也不稱 L4 或 L5 已完成。
