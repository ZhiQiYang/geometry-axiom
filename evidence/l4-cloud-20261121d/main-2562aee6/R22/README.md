# R22 單房輪廓桌面實跑

2026-11-21，在 main `2562aee65c9f21a9ffdfd684100102d764bc2eb4` 的獨立 Windows 測試服務（18851，`fresh:true`）操作 Chrome 157.0.8103.79，內容區 1400 × 900。本次桌面 L4 切片涵蓋 PDF 框選重取、局部頂點與逐邊尺寸修正，以及 PNG 影像來源與門洞分隔重取。另發現復原後一處狀態文字仍顯示已確認。未實跑 390 px、觸控、保存後冷開或 GEO-250 的其他實機項目。[服務探針](../environment/probe-18851.json) · [功能操作與契約](../../../../geometry-web/docs/ROOM-OUTLINE.md)

三組均從「檔案 → 範例 → 載入範例 → 面 1 → 進入面內 → 底圖 → 匯入 PDF／圖片」開始，在原生 Windows 選檔視窗鍵入檔案路徑並按 Enter。選頁加入後，以來源座標 (30,30)、(230,30) 校準為 2000 mm，再按「顯示取景範圍」。校準前選房間按鈕停用。下文標為 px 的距離屬 PNG 原圖，模型頂點與長度以 mm 表示。[操作腳本](walk.cjs) · [原生選檔工具](tools/native_picker.py)

## PDF 框選與人工修正

在既有面 1 匯入公開 PDF 的第 1 頁。原面為 4000 × 3000 mm，已有角材 90、91、1。下列兩條路徑在同一輪操作完成。51 張逐步畫面、20 項斷言全數通過。[PDF 原件](../../../../geometry-web/docs/fixtures/issue54-public-rooms.pdf) · [操作與讀回紀錄](pdf/result.json)

| 操作 | 預期 | 實際 |
| --- | --- | --- |
| 在圖上點 (70,70)，再按「在圖上選房間／框選重取」，從 (20,20) 拖至 (250,165) | 拖框縮小搜尋範圍，正式外環維持原狀，候選沿房間內緣 | 兩次均為 `pdf-vector`。取景從 280 × 190 縮為約 230 × 145，來源四點同為 (32,32)、(228,32)、(228,148)、(32,148)，即 1960 × 1160 mm。[框選候選](pdf/19-box-candidate.jpg) |
| 按「已逐邊核對室內淨輪廓與尺寸」 → 確認替換外環 → 在連動預覽確認套用 → 復原 → 重做 | 確認前場景維持原樣，套用後正式外環等於候選，復原與重做可來回切換 | 四個頂點逐一相符，復原回 4000 × 3000 mm，重做回 1960 × 1160 mm。[連動預覽](pdf/22-impact.jpg) · [重做](pdf/28-redo-result.jpg) |
| 再復原、重新框選，先按逐邊核對按鈕，再到「局部補點／凹口與頂點修正」輸入八點凹口，套用後將第一邊從 1960 改為 2000 mm | 修改後要重新按逐邊核對按鈕。若既有角材失去合法擋面，應列出原因並保留原面 | 八點與人工入值均顯示在候選中。右側凹口使角材 1 頂到未鋪邊界材的 RC，連動預覽顯示 I19/I22、`V_CUT_PRIORITY`，無法確認套用。按「返回修改」可繼續編輯，原面仍是四點。[人工尺寸](pdf/35-edit-edge.jpg) · [拒絕原因](pdf/38-impact.jpg) |
| 將凹口移至 x=390–440、y=1300–1480，再輸入第一邊 2000，再次核對並確認套用 | 合法八點輪廓可寫入，復原及重做應分別得到原外環及修正外環 | 正式八點為 (320,320)、(2320,320)、(2320,1480)、(440,1480)、(440,1300)、(390,1300)、(390,1480)、(320,1480)。狀態 `confirmed`，兩次歷史操作的幾何逐點相符。[正式外環](pdf/47-confirmed.jpg) · [復原](pdf/49-undo-result.jpg) · [重做](pdf/51-redo-result.jpg) |

## PNG 影像與門洞分隔

使用同一張 280 × 190 px 的雙房圖。房間透過右側門洞連通。原生匯入後在「加入位置」選「建立描繪用面（預設矩形）」得到面 2。29 張逐步畫面、10 項斷言全數通過。[PNG 原件](connected.png) · [操作與讀回紀錄](png/result.json)

1. 按「在圖上選房間／框選重取」並點主房 (70,70)。預期門洞讓搜尋進入鄰房。實際 `image-lines` 候選有 12 個頂點，包含主房 (70,70) 和鄰房 (250,100)。[初次候選](png/18-pick-candidate.jpg)
2. 選「垂直分隔」，從 (230,70) 拖至 (230,150)，再點同一主房。預期此次搜尋排除鄰房並提示人工分隔，原面保留。實際候選縮為八點，包含主房測點、排除鄰房測點，並顯示核對門洞的警告。門洞處沿分隔 x=230 px，兩側牆內緣 x=228 px，校準後留有 20 mm 凸段。[分隔](png/20-barrier.jpg) · [重取候選](png/22-pick-candidate.jpg)
3. 逐邊核對後確認替換外環。預期接受人工核對的輪廓。正式八點為 (2280,900)、(2300,900)、(2300,1100)、(2280,1100)、(2280,1480)、(320,1480)、(320,320)、(2280,320)，與候選逐點相符。復原回初始矩形，重做回八點。[確認](png/25-confirmed.jpg) · [重做](png/29-redo-result.jpg)

### 同圖加入既有面時的拒絕

保留預設加入位置「面 1」，使用相同 PNG、校準點與分隔重取步驟。預期候選須通過既有角材的完整驗證。實際得到同一八點候選，預覽列出角材 1 的三個可能跨距 [320,900]、[920,1080]、[1100,1480]（R6/I5/I6），停用「確認套用」，正式外環仍為原矩形。原始腳本等待點擊停用按鈕而逾時，原始收據如實標記 `failed-or-blocked`，前七項斷言通過。本分支未提交候選。上節面 2 的成功案例由 App 重新建立描繪用面。[既有面拒絕畫面](png-existing-face/24-impact.jpg) · [25 張逐步紀錄](png-existing-face/result.json)

## 發現：復原後仍顯示「已確認來源輪廓」

可在上述任一成功案例，於確認後按面內的「復原」重現。正式外環恢復為原矩形，讀回的 `reviewState` 為 `unreviewed`，來源卡顯示「幾何待核對」。預期房間輪廓區的提示也反映待核對。實際同一畫面仍寫「已確認來源輪廓，可復原／重做及保存專案。」PDF 的兩個確認案例及 PNG 新面都出現。重做後幾何與 `confirmed` 狀態一致。[PDF 框選復原](pdf/26-undo-result.jpg) · [PDF 修正復原](pdf/49-undo-result.jpg) · [PNG 復原，左右欄可對照](png/27-undo-result.jpg)

## 重放

在固定 main、獨立測試服務與 Windows 原生 Chrome 下操作。專案根目錄執行以下 PowerShell。腳本需要 Node 24、可經 Node 解析的 `playwright-core`（此機 1.62.1）、Python、已安裝的瀏覽器防護腳本。Chrome 啟動器檢查 Windows 帳戶失敗計數，在產生專用設定檔後套用防護，再在隔離桌面啟動有視窗的 Chrome。驅動程式使用實際滑鼠與鍵盤；App 內讀值用於找畫布座標與比對操作結果。將 `R22_URL` 指向專用服務，三組重放各使用自己的分頁環境與輸出資料夾。

```powershell
$driver = 'evidence/l4-cloud-20261121d/main-2562aee6/R22'
$env:NODE_PATH = "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
$env:R22_URL = 'http://127.0.0.1:18851'
python geometry-web/runtime_version.py --probe 18851
if ($LASTEXITCODE -ne 0) { throw 'R22 測試服務版本探針失敗' }
$browser = node "$driver/tools/launch_browser.mjs" | ConvertFrom-Json
$env:R22_CDP = $browser.endpoint
$env:R22_BROWSER_PID = [string]$browser.browserPid
$outputRoot = Join-Path $env:TEMP ("r22-replay-" + [guid]::NewGuid())
Remove-Item Env:R22_USE_EXISTING_FACE -ErrorAction SilentlyContinue
$env:R22_OUTPUT = Join-Path $outputRoot pdf
node "$driver/walk.cjs" pdf
$env:R22_OUTPUT = Join-Path $outputRoot png
node "$driver/walk.cjs" png
$env:R22_OUTPUT = Join-Path $outputRoot png-existing-face
$env:R22_USE_EXISTING_FACE = '1'
node "$driver/walk.cjs" png
```

最後一組遇預期的核心拒絕，原驅動會以非零結束。每份 `result.json` 記錄操作、來源檔 SHA-256、該步截圖 SHA-256、正式外環、可見文字及候選狀態。三份收據的輸入雜湊與共 105 張 JPG 逐一驗過。PDF 與 PNG 新面的通過結果限於斷言列出的項目。
