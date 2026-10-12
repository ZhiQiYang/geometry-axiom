# #209：P70 隱藏表單、P88 視窗／hit 與可操作恢復

本次取得兩條受控重現路徑，**原 WSL 首紅根因仍是 unknown**。沒有產品修正、全量 runner、golden 比對或合併；P78 已核收資料原樣保留。本資料不能解除 #195／#189 歷史首紅，也不能作為唯一環境根因的證明。

在固定 390×844 下，P70 的 3 秒等待重現 `#igBoundary` 零尺寸；同一次 `open()` 完成後，原選單操作可選到 301。18 秒等待觸發原 15 秒 API 期限；真實「返回畫布 → 重新連接」恢復 connection ready，但接著原卡片入口 hit=false，**沒有完成手機重新進入配置**。在固定 1280×900 的歷史 P88 局部中，DOM 重建後按鈕在視窗外；兩次真實滾輪及 hit-tested 點擊可以繼續完成局部三個斷言。

## 授權、owner 與來源

- [Claude 擴大裁決](https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6132043463)、[本線領取與檔案範圍](https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6132102824)。僅 `test/p78-trial-abort-timeline-20261013`／draft #210；新增 `tests/diagnostics/ui209_*` 與本目錄。
- 開工重讀 `AGENTS.md`、`ops/agent-board:BOARD-cloud-codex.md`，board commit `05383d5c2594c3e7ef24d4ef27a2af17fe9584ef`；分支原 head `c93cfca9bb1af0d82d32878e2a4a1eb1399148f8`，main `1bf661028d55b3ebbd48a02f010116ac9185b81f`。只有本線擁有這個工作分支，工作樹開工時乾淨。
- #186 P74 beforeunload 四情境／K4 屬 [原 owner](https://github.com/ZhiQiYang/geometry-axiom/pull/186#issuecomment-6131182883)；#190 P7 四情境屬 [原 owner](https://github.com/ZhiQiYang/geometry-axiom/pull/190#issuecomment-6131847800)。沒有重跑這兩線，也沒有重跑 P78 或 #195 正式七項。
- P70 雲端產品來源為上述 `c93cfca9...`。435 個 runtime 來源的實際 bytes 對 #195 `0c437b7d1a404643fd9e00b3c07718e943a6d757` 全符，包含 runner／產品來源；兩者 `geometry-web/`、`geometry-core/`、`current_geometry.c` 的 Git diff 為零。
- P88 在 TEMP 用 `git archive` materialize 歷史 `b40620cd433ae36c6a3905c4293313dfd6e7f745`，434 個 runtime 來源 bytes 全符；使用該版原 helper／P88，沒有改用 main 的新版等待 helper。沒有 checkout、寫入其他 owner 分支。

## 原件獨立重建

[raw.tar.xz](raw.tar.xz) 內含兩份原公開 ZIP、取件留言 URL／更新時間／body hash、#195 manifest，以及本次全部 8 次局部執行。每個 raw member 的 bytes／SHA-256 見 [manifest.json](manifest.json)；archive 身分與 source 對照見 [verification.json](verification.json)。

| 原件 | 核對結果 |
|---|---|
| [#195 首報](https://github.com/ZhiQiYang/geometry-axiom/pull/195#issuecomment-6131905102) 與公開 21 段 ZIP | 743481 bytes；SHA-256 `a8dfa45bebb1aad075b585325df323ee80390ed2d9aa5f214947efc22e20ddfe`；283 路徑／214 unique payload 全符 |
| #195 公開三段 manifest JSON | 重建 JSON 並依原 2 空格＋LF 格式序列化；SHA-256 `5f5aff29f74bcb09a66a7059cb69f46c1baa4f16816b7feeca6403dc272cfebb` |
| [#189 歷史局部原件](https://github.com/ZhiQiYang/geometry-axiom/pull/189#issuecomment-6115997361) | 222289 bytes；SHA-256 `3b8be9cc3961f58c7324d9076944f08a63b5c88cd971864014a54b1677a44993`；32 payload 全符 |

#195 正式首輪仍為 grid 105/0、completed=false；canvas 1657/0、completed=false；wrapper exit 1。這些是中止前斷言數，並非兩個 job 通過。P70 手機 `手機 無限` 建立後的來源→配置轉場：`grid_system_test.js:236–237`；原 UI connection ready、network failures／pendingAssets 空、仍顯示來源表單。原 tail 顯示 click → objects 30ms → surfaces 102ms → references 10ms 成功，缺少後續 await／退出點；**本次首個 objects 注入不能當成原 WSL 的卡住位置**。

#189 既有 natural prefix exit 0、old/candidate/revert/restore 局部結果，及其[限縮聲明](https://github.com/ZhiQiYang/geometry-axiom/blob/03aa3a3d8c53b19d88ced4ae9de5dc220aaa82ae/tests/evidence/serve189-diagnostic-scope-20261012/README.md)保留。舊原件沒有直接量到 scrollTop 復位，也沒有證明完整 World/history 零寫入。本次不重做該四輪 helper 比較，僅補實際恢復與觀測。

## 受控條件與原始結果

P70 取原 helper／create() 及其兩個斷言，只建立 boundary 301＋一個「手機 無限」來源，再執行原 `ctl('#igNewBinding'); choose('#igBoundary',301)`。沒有前面 P70 全部物件／參數／草稿／profile。P88 取歷史 1280px 的前綴，包含兩個 binding/apply 與三個原斷言；在第二次舊 helper 捲動之後，**明示呼叫一次現有 `InfiniteGridWorkspace.openSystem()`** 製造新 DOM。這是注入，並非原 WSL 自然時序。

所有 API 15 秒、bridge 30 秒、原 P70/P88 wait 20/25 秒、ctl 12 次與 poll 80/70ms 均未放寬。受控 hold 在真 bridge lock 已取得後、native stdin.write **之前**，只針對已標記的第一個 binding `objects`；不是 native CPU 負載，也不是整機慢速模擬。P70 額外等待 open 結束的 22 秒只用於首紅後診斷，不改原判決。

| raw run 目錄 | browser／wrapper exit | 秒 | 實測與界線 |
|---|---:|---:|---|
| `ui209-p70-baseline-01` | 2 | 7.959 | 無注入已選到 301；工具錯把整段操作的 undo 要求全等。工具失敗原樣留存 |
| `ui209-p70-baseline-02` | 0 | 8.836 | 更正為分別觀測；兩個原建立來源斷言及局部選單步驟完成；390×844 |
| `ui209-p70-hold3-01` | 1 | 11.787 | 原零尺寸首紅；截圖後 viewport 被 Playwright 改為 1400×1000，恢復不算手機證據 |
| `ui209-p70-abort18-01` | 1 | 29.975 | 原零尺寸首紅＋TimeoutError；同上，重新進入成功僅限變更後 viewport |
| `ui209-p88-wheel-01` | 1 | 22.418 | 首紅保留；截圖後 viewport 變更，恢復不算 1280px 證據 |
| `ui209-p70-hold3-02` | 1 | 12.640 | 改為直接 CDP 截圖；固定 390×844，原首紅後可選到 301 |
| `ui209-p70-abort18-02` | 2 | 27.411 | 固定 390×844；原首紅保留；真返回／retry 後 ready，後續卡片 hit=false，中止擴展診斷 |
| `ui209-p88-wheel-02` | 1 | 12.216 | 固定 1280×900；原首紅保留；兩次滾輪後可點，繼續三個原局部斷言 |

表中秒數是 Node 受控命令 elapsed，非整個編譯／啟動程序，也非原 WSL job 時間。每一筆 commands.json 有原 argv、cwd、exit、elapsed；identity.json 有 source head、實際 server PID/root/port、環境覆寫及 executable SHA。失敗後 recovery 成功不會把首紅變成 exit 0；後续恢復控制再失敗另留 exit 2。所有執行已結束，沒有把啟動或 inProgress 當結果。

v1（undo 判準）、v2（Playwright 截圖）、v3（CDP 截圖）實際工具 bytes 依 hash 封存於 raw/tools，逐 run 的 executed-tool-index.json 可取回確切版本。只有上述具體工具問題導致補驗；沒有無限重排同一版本。

## 時間線與反證

詳細數字可由 [ui209_summarize.py](../../diagnostics/ui209_summarize.py) 從 raw 重算；[summary.json](summary.json) 提供逐 await／return／generation。

| 固定 viewport 案例 | request／open 代次 | server 前置／排隊 | 注入／native 回覆 | browser／UI |
|---|---|---|---|---|
| P70 baseline-02 | `ui209-50`／3 | 0.060／0.009ms | 無 hold／23.480ms | open 269.5ms；mode=binding |
| P70 hold3-02 | `ui209-49`／3 | 0.082／0.153ms | 3000.133／2.956ms | 首紅時 mode=source、bindingForm.hidden=true、display=none、零尺寸、connection ready；open 3281.9ms 後 mode=binding |
| P70 abort18-02 | `ui209-50`／3 | 0.076／0.011ms | 18000.208／0.745ms | fetch 後 14998.8ms signal abort，14999.5ms reject；TimeoutError；open 15028.8ms 後仍 source |

時間差只在各自時鐘內計算：browser performance、host monotonic、server monotonic 分別記錄；epoch 僅用來對齊，沒有跨時鐘硬相減。API timeout 建立 stack、signal reason、fetch rejection stack、server request／queue／lock／stdin／stdout／response／disconnect 全保留。hold 結束後 native 正常回覆，但 abort18 client 已斷線，server 記 BrokenPipe。這不是 native 執行了 18 秒。

open() 13 個 await 位點與所有 return 有觀測；每筆帶 options、serial、mode、busy／initializing／heldControls／projectControls／releasing、project busy。`ownsEntry` 記 ticket／serial、context／token／frame 同一性與結果。本輪沒有觀測到 ownsEntry=false；**不表示原 WSL 不可能走 early-return**。catalogPins 內部 SHA 工作只量外層 await，未細分 WebCrypto 每個工作。

hold3 固定手機案例的首紅只有 hidden 表單；不需要 abort 就能重現。await 完成後在同一次 open 選到 301，反證「零尺寸必定表示永久不可恢復」。abort18 後 mode 仍 source、connection error；真 `igClose`／`connectionRetry` click 的 `isTrusted=true`。retry 後 phase=ready（error 字串仍保留舊訊息），但原 canvas `.ocard[data-kind="grid-system"][data-id="1"]` 中心 hit=false；未試其他入口、Tab、再次關閉 drawer 或手機頁面 reload，未判定所有路徑都不可恢复。此案例沒到後置 dump/history 比較，不能借桌面案例宣称手機 World/history 相同。

P88 的替換前及後按鈕皆已在視窗外，node 身分改變；兩個新舊 inspector 的觀測 scrollTop 都為 0，**未量到「從非零重設為零」**。恢復時同一按鈕中心 y：1218.828 → 818.828 → 418.828；第一次 400px 後雖進 viewport，hit 仍是 `SPAN#igDraftNote`；第二次 400px 後才 hit=true，接著真點擊開始下一代 open。不能把「在 viewport 內」當成「可點」。

baseline-02、hold3-02 與 p88-wheel-02 的前後 dump 都驗 `ok===true` 且 `typeof text==='string'` 後逐字比較，全相同；redo entry 身分、frame、limit、context/token 全同。undo entry 全等為 **false**：P70 4→7，P88 19→20。產品 `setFeatureAttachment()` 會為網格草稿記 local history；本資料只報實測差異，不把原生 dump 相同擴張成完整 history 零寫入。沒做產品 red/green/revert 或全量回歸。

## #195 P74：原件分流與最小補證

#195 是 `ux_refinement_test.js:72` **第一次 reload 的 ready()** 超時，尚未進到後面的專案恢復斷言。`2160.1s` 是 canvas job 已執行總時長；ready() 原條件等待是 40 秒，不能說成 P74 等待 2160 秒。原 tail 只有兩次成功 dump、connection loading，沒有後續 objects；7 個 PDF worker pending 屬先前 P57–63。以上不證明 PDF worker 或慢機器根因，也不是 #186 的 beforeunload 事件。

`app.js:568–593` 中 recoverConnection 先 await recoverApiResults／recoverLoad／handshake，再 await restoreSession，之後才 renderObjects→ready。`reference-workspace.js:215` 的 restoreSession 包含 editor lock、recovery lock、IndexedDB open/read、checkpoint 等分支。原件缺這些 await 的起迄、busy／recovery、locks 與 IndexedDB 回呼；因此仍 unknown，本線不占用原 owner 的正式重跑。

原 owner 可在既有保留的同一 profile／同一服務、原 timeout catch **停止前** 用原 send/eval_ 收以下只讀快照，存原字串並保留當時 PID、port、Chrome／runner／step／bridge 身分。不要清 storage 或另起一輪完整 runner：

```js
const snapshot = await eval_(`(async()=>({
  at:performance.timeOrigin+performance.now(),mono:performance.now(),
  url:location.href,ready:document.readyState,
  connection:typeof connection==='undefined'?null:{...connection},
  project:typeof ReferenceWorkspace==='undefined'?null:{
    busy:ReferenceWorkspace.busy,info:ReferenceWorkspace.getProjectInfo()},
  locks:navigator.locks?await navigator.locks.query():null,
  databases:indexedDB.databases?await indexedDB.databases():null,
  focus:document.activeElement?.id,
  dialogs:[...document.querySelectorAll('dialog[open]')].map(n=>n.id)
}))()`);
fs.writeFileSync(output+'/p74-first-reload-state.json',JSON.stringify(snapshot,null,2));
```

這只能補「當下」狀態，不倒推出過去 await。若原頁已關閉，明記無法補回；由既有排程 owner 在下一次同 head 有界重現前，以 `Page.addScriptToEvaluateOnNewDocument` 加只讀記錄：locks.request 的 call／callback lock-null、IDB open 的 success/error/blocked/upgrade、transaction complete/error/abort，並在上述 recoverConnection/restoreSession 各 await 前後記相同 performance clock、busy／recovery 狀態。保留原 20 秒 document marker／40 秒 ready 期限及 beforeunload 判決。held lock 的 callback promise 刻意保持到頁面結束，不能因「request promise 未完成」就當卡死。這組原 profile instrumentation **本輪未執行**；不能冒稱已驗 P74 恢復。

P70 原 WSL 的最小補證是由 #195 原 owner 在已排定 grid job 重用本線 open observer，保留原完整前置狀態，記 #igNewBinding 點擊前後每個 await／ownsEntry／return、mode、bindingForm.hidden、祖先 display、實際 hit/focus 和 request ID。若只有原 tail，保持 unknown，不能用本輪單 source fixture 補寫歷史。

## 重現與檢查

在同一 cloud repo、已有 Chromium／Playwright 的環境執行；每個 `--out` 必須是新的 TEMP 路徑，各命令逐一執行。這四個命令只跑局部，首紅案例 exit 非零是保留的結果。

```sh
python3 tests/diagnostics/ui209_run.py --case p70-baseline --out /tmp/ui209-new-baseline
python3 tests/diagnostics/ui209_run.py --case p70-hold3 --out /tmp/ui209-new-hold3
python3 tests/diagnostics/ui209_run.py --case p70-abort18 --out /tmp/ui209-new-abort18
python3 tests/diagnostics/ui209_run.py --case p88-wheel --out /tmp/ui209-new-p88
```

P88 需本地已有 b40620c Git object；runner 不從網路更新分支。沿用 binary 時可加 `--bridge /tmp/.../bridge`，必須另核來源閉包。此次各自編譯 c93／b406 的命令皆是 `gcc -std=c11 -O2 geometry-web/web_bridge.c -o <TEMP>/bridge -lm`，編譯 exit 0；兩次產物 SHA-256 同為 `133f374ea6575febe2c474053b2507d280eed07cc4fe6e83bf14387870779924`。完整 42 項 compiler include 閉包已保存。Chromium 154.0.8037.57、Node 24.19.0、gcc 14.2、Python 3.12.14；wrapper 與 Chromium ELF 分開算 hash，版本原文在各 run。

重算封存摘要：解壓 raw.tar.xz 到新的 TEMP 目錄，再 `python3 tests/diagnostics/ui209_summarize.py <解壓目錄>`。驗證每個 raw member 的 length/hash 與 manifest.json；來源／binary 前後一致性、八次實際 exit、兩份歷史 ZIP／payload 都由該工具檢查。源碼定位 snapshot、完整工具版本、原 executed-prefix、served JS、server adaptation、request/bridge logs、截圖都在 raw。

工具觀測有額外 Promise、stack 與 snapshot 成本，未校準 instrumentation overhead；fresh cloud profile、單一 bridge、人工 hold 和歷史 WSL 不同。只收錄本線啟停的服務；結束 census 沒有仍活動的本線 server／bridge／browser，Chromium 的 PID1 zombie 另列，不冒充活動 runner 或全主機隔離證明。
