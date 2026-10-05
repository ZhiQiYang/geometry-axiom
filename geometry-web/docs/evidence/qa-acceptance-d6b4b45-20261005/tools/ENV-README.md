> **QA 報告附註(2026-10-06)**:本目錄為驗收當時的工具原樣(僅路徑清洗:`<QA>`=驗收暫存根、`<TEMP>`=Windows %TEMP%)。
> 已知瑕疵:`stop_server.sh` 對**同一埠第二次**停止時,把 `run/<port>.json` rename 成 `<port>.stopped.json` 會因目標已存在而失敗;服務其實已停,只是該步報錯(見 T2 報告第四段)。`example_script.json` 內的路徑已清洗成 `<TEMP>`/`<QA>`,實際使用須換成本機路徑。

# QA 環境 README(驗收版本 d6b4b450d741fcbbfd75c51631915d3082926990,worktree `D:/geometry-axiom-qa`)

ENV = `<QA>/env`
QA 暫存根 = `%TEMP%\geometry-qa\`(= `<TEMP>\geometry-qa\`):`bin\`(exe)、`fb-<port>\`(回報)、`tmp-<port>\`(服務 TEMP)、`run\<port>.json/.log`。

## 1. 建置(只需一次;其他 agent 再跑只會命中快取)
```
python ENV/build_qa.py [--core]          # 預設編 bridge + model-base;--core 加編 core.exe
```
- exe 放 `%TEMP%\geometry-qa\bin\`,檔名帶來源雜湊:`bridge-c5955d469b13.exe`、`model-base-079eda49f0df.exe`、`core-5131c76e7d5c.exe`;`bin\paths.json` 記路徑。
- 雜湊 = include 閉包(bridge:`web_bridge.c` + `current_geometry.c` + 9 個 `.inc`)逐檔位元組 + cl 指令。沒變就不重編;不覆寫舊檔,所以不需要殺任何行程。
- 重編後驗證:新檔時間戳、exe 內含 ≥3 個來源字串字面量、行為驗(bridge 回 dump JSON、model-base 吃最小 scene)。被 SAC 擋時間隔 12 秒重試 5 次,仍擋則退出碼 3 =「環境阻擋」。
- 退出碼:0 成功 / 2 編譯或驗證失敗 / 3 環境阻擋 / 4 其他。服務所需 exe 只有 bridge(同時當 model-update bridge)與 model-base;core 僅 feedback_cli replay 才用。

## 2. 起服務、probe、停服務(埠只准 8800–8899 且未被占用)
```
bash ENV/start_server.sh 8831        # 起服務 + 自動 probe;輸出 http://localhost:8831/
python ENV/qa_server.py probe 8831   # 單獨 probe(= runtime_version.py --probe)
python ENV/qa_server.py status 8831
bash ENV/stop_server.sh 8831         # 只停 run\8831.json 記的 PID 樹(serve.py+bridge),先核對命令列
```
環境變數(qa_server 已設):GEOMETRY_BRIDGE=bridge-*.exe、GEOMETRY_MODEL_BASE=model-base-*.exe、GEOMETRY_MODEL_UPDATE_BRIDGE=同 bridge、GEOMETRY_FEEDBACK_DIR=`%TEMP%\geometry-qa\fb-<port>`、TEMP/TMP=`tmp-<port>`。**不用 start.ps1**(它走 WSL gcc,且埠預設 8765 可能撞使用者服務)。
probe 成功的原始輸出:`ENV/probe_8831.txt`(`fresh:true`、`root:"D:\\geometry-axiom-qa"`、version e2f2ee7b…,指紋與 QA worktree 相符)。多 agent 同時用:各自挑不同埠(如 8831/8832/8833/8834)與不同 Chrome 偵錯埠、不同 profileDir。

## 3. qa_cdp.js(零相依,Node ≥22;Chrome 預設 `C:/Program Files/Google/Chrome/Application/chrome.exe`)
庫:`const qa=require('ENV/qa_cdp.js'); const b=await qa.launch({port:9411, profileDir, width:1440, height:900, mobile:false, downloadDir, fsAccess:'none'})`
- 導覽/讀:`goto(url)`、`reload()`、`centerOf(sel)`(只讀座標/可見/被誰蓋住)、`exists`、`readText(sel)`、`readValue`、`readAttr`、`pageText()`、`waitFor(expr)`、`waitSelector`、`evalReadOnly(expr)`(**只准讀 DOM;不得呼叫 app 私有函式、不得改狀態**)。
- 滑鼠(`Input.dispatchMouseEvent`,target 可為 selector 或 `[x,y]`;selector 會先檢查可見/未停用/中心點未被蓋住):`click`、`rightClick`、`doubleClick`、`hover`、`drag(from,to,{steps})`、`wheel(target,deltaY,{modifiers:2=ctrl})`、`tap`(觸控)。
- 鍵盤:`press('Escape'|'Enter'|'Delete'|'ctrl+z'|'ctrl+y'|'ctrl+shift+z'|…)`、`typeText`(逐字 char 事件)、`insertText`(`Input.insertText`)、`fill(sel,value,{enter})`(點→Ctrl+A→insertText)。
- 選檔:`await b.chooseFileOnNext([路徑]); await b.click('#btnImportReference'); await b.waitForChooser()`。用 `Page.setInterceptFileChooserDialog`,app 自己開 chooser 後才 `DOM.setFileInputFiles(backendNodeId)`;不碰隱藏 input。
- 下載:`launch({downloadDir})`(`Browser.setDownloadBehavior`),`waitForDownload(dir,'.gcanvas',timeout)` → `{file,size}`;`b.downloads()` 看事件。
- 其他:`screenshot(path,{fullPage})`、`consoleLog({onlyErrors})`(console + pageerror + Log 項 + dialog)、`setDialogPolicy('accept'|'dismiss')`、`resize(w,h,mobile)`、`close()`(只殺自己那棵 Chrome 樹)。
- 螢幕:`mobile:true` + 390x844 會設 touch 與 Android UA;截圖 1x(`deviceScaleFactor` 可傳)。
CLI:`node ENV/qa_cdp.js script.json`,格式見 `example_script.json`(`launch`/`url`/`outDir`/`steps[]`;step.do ∈ goto click rightClick doubleClick hover drag wheel tap press type insert fill sleep waitFor waitSelector chooseFile waitChooser waitDownload screenshot resize dialog read assertText assertExists assertNotExists consoleErrors;任一步加 `"shot":"x.png"` 即截圖;失敗自動 `-FAILED.png`,結果寫 `outDir/script-result.json`,exit 1)。

## 4. 已驗證(2026-10-05)
- 煙霧:`node ENV/smoke.js 8831` → `ENV/smoke/smoke-desktop.png`(1440x900)、`smoke-mobile390.png`(390x844);兩者皆為 app 畫面(「構形 Canvas」),console/pageerror 皆 0。輸出 `smoke/smoke-output.txt`。
- 選檔真實驗證:檔案選單 → `#btnImportReference`(正式「匯入參考資料…」)→ file chooser 被攔截 → 塞 `synthetic_floorplan_A3_landscape.pdf` → app 開出「選取參考圖頁」對話框並渲染 PDF(`verify/02-after-import.png`)。`verify_chooser_download.js`。
- 下載真實驗證:檔案選單 → `#btnSaveProject`(另存新檔…)→ 下載 `未命名專案.gcanvas`(955 B,ZIP「PK」開頭,含 `world.scene`)到 downloadDir。`verify_download.js`。
- CLI 腳本 `example_script.json` 14 步全過(含 wheel/drag/ctrl+z/Escape)。

## 5. 合成測試資料(`ENV/fixtures/`,**全部為人工合成**,詳見 `fixtures.md`;重生 `python gen_synthetic_pdfs.py`)
- `synthetic_floorplan_A3_landscape.pdf`:A3 橫、1:50;ROOM_A 5000x4000、ROOM_L L 形(6000x5000 缺右上 2000x2000)、尺寸線「5000」(端點 (283.4646,368.5039)→(566.9291,368.5039) pt)、左下 `SYNTHETIC TEST 1:50`。
- `synthetic_portrait_2page.pdf`:A4 直 2 頁;p1 矩形 4000x3000(1:50)、p2 T 形(1:100,含尺寸線 6000)。
- `synthetic_rotated90_A4.pdf`:加分,頁面 /Rotate 90。
- repo 既有可用 PDF:`geometry-web/docs/fixtures/issue54-public-rooms.pdf`、`tests/fixtures/issue77-two-rooms.pdf`、`geometry-web/docs/evidence/issue119-20261004/asymmetric-ten.pdf`;範例專案 `geometry-web/examples/*.gcanvas`。

## 6. 已知環境坑
1. **File System Access API**:app 的「保存/另存」優先用 `showSaveFilePicker`,無頭 Chrome 無對話框會卡住(無任何反應、無下載)。qa_cdp 預設 `fsAccess:'none'` 在新文件前移除該 API,app 走正式備援(產生 .gcanvas 下載,狀態列「已產生專案下載」、`downloaded` 而非 `saved`)。**驗收報告須註明保存測的是下載備援分支**;`fsAccess:'native'` 保留原 API(無頭會卡)。
2. **SAC(WinError 4551)**:新編 exe 第一次執行可能被擋(本次 model-base 第一次 5 次重試全擋,重編後同來源即過)。症狀:build_qa 退出碼 3、serve.py「橋接器連線中斷」、Permission denied。先當環境阻擋、等 10–15 秒重試,不當成程式失敗;勿動安全設定。`%TEMP%\geometry-tests\bridge.exe`(別人的)本次也 Permission denied,別用。
3. **core.exe 會把 `current_geometry.svg` 寫在原始碼旁**(QA worktree 根,被 .gitignore 忽略,`git status` 不顯示)。本環境一次驗證誤寫了一個(22:00:27,5280 B;刪除被權限分類器拒絕,留給使用者處理);build_qa 現已改用 `--out` 暫存。驗收 agent 若自跑 core.exe 請加 `--out`。
4. Bash heredoc 會吃反斜線:含 `\` 的腳本用 Write 工具寫檔。Git Bash 的 `/tmp` ≠ Windows TEMP,路徑傳給 Node/Chrome 請用 `C:/…` 形式。
5. serve.py 以 `127.0.0.1` 綁定,Origin 只收 `localhost:<port>`/`127.0.0.1:<port>`;請用 `http://localhost:<port>/`。
6. 重編前不要殺任何 bridge(使用者可能有服務在跑);本環境以雜湊檔名避鎖。
7. 啟動時 serve.py 會凍結來源快照;QA worktree 在驗收期間不可改檔,否則 `/runtime` 變 `fresh:false`。
