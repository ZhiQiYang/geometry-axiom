# R22 復原與重做後的輪廓提示

在修正提交 `2cb36f5ae9174830b5c032f7160379e3edbde8c4` 上重走 #440 的三條路徑。每次確認後先復原一次，再重做一次。確認與重做時，右欄均顯示「已確認來源輪廓。」復原時，同一處顯示「尚未核對來源輪廓」，來源卡也標出「幾何待核對」。九次比對均核對當前面的正式外環頂點、可見提示及其下方的核對狀態。[各步頂點、可見文字與截圖 SHA-256](result.json)

| 在 App 中的操作 | 確認 | 復原 | 重做 |
|---|---|---|---|
| PDF 匯入面 1、兩點校準為 2000 mm，點房間後拖框重取內緣 | [1960 × 1160 mm 四點外環](pdf-box-confirm.jpg) | [原 4000 × 3000 mm 矩形](pdf-box-undo.jpg) | [恢復內緣四點](pdf-box-redo.jpg) |
| PDF 重新框選，在局部修正輸入凹口頂點，調整凹口位置並把第一邊設為 2000 mm | [人工修正的八點外環](pdf-correction-confirm.jpg) | [原矩形](pdf-correction-undo.jpg) | [恢復八點凹口及邊長](pdf-correction-redo.jpg) |
| PNG 匯入新描繪面 2、校準後點選連通兩房，在門洞畫垂直分隔，再點同一主房 | [只含主房的八點外環](png-separation-confirm.jpg) | [描繪面的原矩形](png-separation-undo.jpg) | [恢復分隔後的八點](png-separation-redo.jpg) |

進入各條路徑後，在候選區勾選「已逐邊核對室內淨範圍、連通關係、尺寸及上述修整／警告」，再按「確認替換外環」。有連動預覽時須按「確認套用」。復原與重做均從面內按鈕操作。復原後出現的「已逐邊核對室內淨輪廓與尺寸」是另一個手動記錄核對的按鈕，本次走查未按它。

## 比對方法

在 Windows 隔離桌面以 Chrome、Playwright 和 Node 24 操作專用 App，視窗為 1400 × 900。匯入時點開瀏覽器的原生選檔框並用鍵盤選檔。每階段都讀回正式面外環及畫布 SVG 多邊形的全部頂點，分別與事先固定的座標比對，再核對畫面上實際可見的提示、核對標籤與來源卡。正式走查僅從畫面與前端讀值。執行前以 `runtime_version.py --probe 18855` 核對版本。[服務探針](probe.json)

修正前的對照取自 #440 的原始紀錄。在相同三個復原點，正式外環已還原，核對狀態是 `unreviewed`，右欄仍保留成功提示。新舊九組畫面各以檔案原始位元組核對 SHA-256。[修正前的 PDF 與 PNG 操作及原件](https://github.com/ZhiQiYang/geometry-axiom/blob/f0f40d6b68e9885ef6f648e65adf6b833941d66b/evidence/l4-cloud-20261121d/main-2562aee6/R22/README.md)

## 重放

以下 PowerShell 從修正版專案根目錄執行，將 #440 的原始驅動與選檔工具解壓到新暫存目錄。套用 [本次驅動差異](replay.patch) 並加入[九個畫面的驗證條件](history-oracle.cjs)後，`walk.cjs` 的原始位元組應符合收據中的 `driverSha256`。

```powershell
$evidence = (Resolve-Path 'evidence/r22-history-hint-20261121').Path
$replay = Join-Path $env:TEMP ("r22-ui-" + [guid]::NewGuid())
$archive = "$replay.zip"
git fetch origin refs/pull/440/head
git archive --format=zip "--output=$archive" 'f0f40d6b68e9885ef6f648e65adf6b833941d66b:evidence/l4-cloud-20261121d/main-2562aee6/R22' walk.cjs connected.png tools
Expand-Archive -LiteralPath $archive -DestinationPath $replay
git -C $replay -c core.autocrlf=false apply --no-index --unidiff-zero "$evidence/replay.patch"
Copy-Item -LiteralPath "$evidence/history-oracle.cjs" -Destination $replay
Get-FileHash -LiteralPath "$replay/walk.cjs" -Algorithm SHA256
```

依 #440 的「重放」準備獨立服務、Node 24、Playwright 與瀏覽器防護，將該段的 `$driver` 設為 `$replay`，`R22_URL` 指向本次受測服務。執行 PDF 與 PNG 新描繪面兩組，PDF 一組內依序涵蓋框選與人工修正。PDF 共 51 步、74 個斷言，PNG 共 29 步、36 個斷言。
