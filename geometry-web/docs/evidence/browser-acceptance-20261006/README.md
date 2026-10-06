# 瀏覽器驗收紀錄 2026-10-06(#152 / #134 / #156)

> 環境:**本機 Windows 11**(非雲端)。唯一 QA owner:Claude Sonnet 5.5。只量測,未改產品程式,未 commit/push/留言。
> 受測版本皆用隔離 detached worktree(`D:\geo-bqa-<n>`,結束後已移除,四個皆乾淨 `git status`=空)。

## 1. 環境

| 項目 | 值 |
|---|---|
| main | `6562fa53d90de22b3e5492f2083199b26377a8c2`(tree `00807ad44334e88f36313a3a8476ea7ae7d5e63d`),`origin/main` 全程不變 |
| 瀏覽器 | Playwright for Python 1.63.0(`geo2a-venv`,唯讀沿用)+ 其內建 Chromium 153.0.8010.12(`ms-playwright\chromium-1243`),headless,每個情境 fresh profile(`%TEMP%\geobqa\profile-*`) |
| 另有 | #134 的 P88 自動化由 `cdp_test.js` 自起本機已安裝的 Chrome(版本未記錄,自行結束,無殘留) |
| 原生 exe | **未新編譯**。沿用 `%TEMP%\geometry-qa\bin\bridge-c5955d469b13.exe`、`model-base-079eda49f0df.exe`。新鮮度:用 `qa-acceptance-d6b4b45-20261005/tools/build_qa.py` 的 `source_hash()`(只讀,不編譯)對 main、#134、#156 三個 checkout 算 C 閉包雜湊,bridge=`c5955d469b13`、model-base=`079eda49f0df`,與檔名相同;且 main→#134、main→#156 的 `*.c/*.h/*.inc` diff 為空。故既有 bridge 與三個 head 的 C 原始碼相符。(AGENTS 說的 SAC 阻擋未遇到。) |
| 服務 | 每 PR 獨立 port/TEMP/`GEOMETRY_FEEDBACK_DIR`(`%TEMP%\geobqa\{tmp,fb}-<port>`);同時最多一個服務+一個瀏覽器 |
| 資源取樣 | `env/resource.log`(41 筆):可用記憶體最低 965 MB(≥800),CPU 最高 100%(僅 #134 的 P88 長跑期間單點,從未連續 70% 達 15 分鐘)。**「連續 15 分鐘資源不足」規則全程未觸發。** |
| 觀測限制 | headless,無真實螢幕閱讀器/IME/OS 檔案選擇器;截圖皆合成資料 |

## 2. 階段 1:服務 ↔ 真瀏覽器互通(PASS)

- 啟動:`env/svc.ps1 start D:\geo-bqa-main 8870`(內容見檔;環境變數 `GEOMETRY_BRIDGE`/`GEOMETRY_MODEL_BASE`/`GEOMETRY_FEEDBACK_DIR`/TEMP 皆隔離)。輸出 `env/p1_start.txt`。
- `curl -sS -i /` → 200,`text/html`,50203 bytes(`env/p1_curl_root.txt`);`/runtime` → 200,`{"schema":"geometry-runtime/1","version":"2bbcd8fb…04eb6","fresh":true,"root":"D:\\geo-bqa-main"}`(`env/p1_curl_runtime.txt`);`runtime_version.py --probe 8870` exit 0(`env/p1_probe.txt`)。
- Chromium:`env/p1_browser.py`(Playwright 1.63.0 / Chromium 153.0.8010.12),exit 0(`p1_browser_chromium.exit`)。title「構形 Canvas · 工程規格與空間建模」、`#app` 存在且非 inert、`#fileMenuBtn` 存在、`apiRequest` 為 function、scrollWidth=innerWidth=1382、頁內 fetch `/runtime` fresh:true、console/pageerror 0。截圖 `env/p1_home_chromium.png`。
- 服務 stderr 0 bytes(`env/p1_serve_stderr.txt`),stdout 為啟動訊息。Chromium 一次就起得來,**未遇到 AF_UNIX EPERM**,故未做 msedge 對照(不需要;未改任何安全設定)。
- 結論:服務與真瀏覽器互通;PR #152 本文所稱「Chromium 無法建 AF_UNIX socket」在本機本次**未重現**(環境差異,不代表該 PR 的別處環境)。

## 3. #152 私人 work manager(PASS 19 / FAIL 0 / 未驗 1;依契約 W-01~W-20)

- main `6562fa53`;PR head `a15d73a35189b3396f1469090968759b66bb816d`(測前、測後 `gh pr view` 確認不變);受測 tree `68095311f1e11dcad38ae0c2ea5d6028a5eab3ec`。
- 服務:`python geometry-web/work-manager/cli.py --data-dir %TEMP%\geobqa\wm152 serve --port 8871`(非 serve.py,無 `/runtime`;`/api/state` 200、`X-Work-Manager-Code` 在)。fixture `synthetic-demo.json`,匯入於 2026-10-06T09:57:43Z(=本機 17:57),**早於 stale 時點 2026-10-07T01:00Z**;state_hash 前 10 碼 `79f7e18372` 與契約預期一致。
- 視口 1382×804、390×844,另補 1440×1000(只量 scrollWidth)。腳本 `pr152/w_test.py`、`w_test2.py`;結果 `results_part1.json`、`results_part2.json`、`w_test_part*.log`。

| 條目 | 結果 | 備註 |
|---|---|---|
| W-01 | PASS | 127.0.0.1 與 localhost 皆載入;title、h1、stateLoaded、64 hex hash |
| W-02 | PASS | UI = CLI = `/api/state` state_hash;payload_hash 相同 |
| W-03 | PASS | 3 工作/1 項動作/唯讀0 可寫入1 等待2/警示 5/顯示 3/3 |
| W-04 | PASS | 3 列;`w04_rows.json`。DEMO-REVIEW 顯示停止/受批准阻擋;**「無列顯示完成」為機器關鍵字判斷+人眼讀 json,非像素驗證** |
| W-05 | PASS | 展開 DEMO-REVIEW 見 demo-evidence-2 與 PR #2;example.com 連結 4 個。鍵盤開合/焦點還原未逐項驗 |
| W-06 | PASS | 搜尋 1/0/3;篩選各選項列數記於 log |
| W-07 | PASS | 可進行項點擊定位 DEMO-READY;模式鈕可篩 |
| W-08 | PASS | 訊息「已讀取 3 筆登記紀錄,5 項警示。」,hash 不變,generated-at 更新 |
| W-09 | PASS | 殺自己 serve 後重讀:`#fetch-error` 顯示「狀態讀取失敗…畫面保留上次成功讀取的資料與雜湊」,列與 hash 保留;重啟後恢復(`w09_fetch_error.png`) |
| W-10 | PASS(縮窄) | 只能注入 title(`<img onerror>`/`<script>`):純文字顯示,無 `__xss`、無 img、無 javascript: 連結。**`javascript:` URL 無法匯入**(CLI 驗證拒絕,`w10_url_import_rejected.txt`),故 safeURL 白名單的 UI 端未實測 |
| W-11 | PASS(縮窄) | **只用 HTTP GET `/api/export`**(200、`Content-Disposition: attachment; filename="geometry-work-backup.json"`、2425 bytes、sha256 `57ad9b1b…f1b82`);檔案存 `%TEMP%\geobqa\wm152-backup.json`,**不在證據目錄**。UI「匯出備份」按鈕下載未驗(下載須使用者許可) |
| W-12 | PASS | POST/PUT/PATCH/DELETE/OPTIONS=405 Allow:GET;偽 Host、跨 Origin=403;`/nope`=404;favicon=204;只聽 127.0.0.1 |
| W-13 | PASS | 初版腳本誤判 FAIL(`results_part1.json` 內仍寫 FAIL),複核(`w13_probe.json`):6 個無 data-label 的 td 為「標題欄」與空的 colspan 明細列,屬設計。兩視口 scrollWidth≤innerWidth(390 恰 390),390 為堆疊;alerts-list tabindex=0 role=region。截圖人眼檢視無截斷/重疊(非機器驗證) |
| W-14 | PASS | 首停「跳到工作佇列」(top 10px,3px #2f78c4 外框),Enter 捲到 y=492;12 次 Tab 皆有外框(`w14_tabseq.json`)。Enter 後 `activeElement.id` 為空(捲動成功,焦點落點未細查) |
| W-15 | PASS(縮窄) | 複製:「已複製完整狀態雜湊。」;**列印未驗**(window.print 不執行) |
| W-16 | PASS | 同 data-dir 重啟 hash 相同;匯出→`restore`→`reconcile` payload_hash 相同 |
| W-17 | PASS | 受測 worktree `git status --short` 空 |
| W-18 | PASS | 空 data-dir:0 工作、「尚無來源」、「尚未匯入 issue 清單…」(`w18_empty.png`) |
| W-19 | **未驗** | 需自造含 inventory/umbrella 的快照,本輪未做 |
| W-20 | PASS | 請求只有 `/`、`/api/state`、`/app.js`、`/style.css`;全 same-origin;0 console error |

已停 PID:serve 28880(單次長駐);W-09/16/10/18 由腳本自起 5 個(7784、39572、30240、30900、2572,皆 `Popen.kill`)。

## 4. #134 #61 切片 2(PASS 13 / PARTIAL 1 / FAIL 1 / 未驗 3;R-01~R-18)

- main `6562fa53`;PR head `77c3847f32b2ba0616bab6c8d0c8370082c4941c`(`pr134/head_check.txt`,測前測後不變);tree `5660d1ef8836095a96d62d7f3bdcb18a6718cf56`;port 8872;`/runtime` fresh:true、root=`D:\geo-bqa-134`、version `a7155144…582c4`、probe exit 0(`runtime.json`、`probe.txt`)。
- 初始世界:兩個 boundary/placement 以 `line` 原生指令作者(同 P88 夾具,契約允許);其餘全走真 UI(來源/規則/配置/套用、面內、檢查器、Save/Open)。腳本 `r_lib.py`、`r_run1~4.py`;結果 `r_run*_{1382,390}.json`。
- 重要細節:服務端 World 跨瀏覽器工作階段持續,每次必須先「新專案」(`h.fresh()`);第一次 390 失敗即因此(污染),非產品問題。

| 條目 | 1382 | 390 | 備註 |
|---|---|---|---|
| R-01 | PASS | PASS | 來源/配置規則視圖 `data-ig-rule-ref="none"` |
| R-02 | PASS | PASS | exact cell 線段 = native `grid-rule-query` 逐字;完整 tuple 含大索引;面1 3 段/面2 5 段 |
| R-03 | PASS | PASS | u/v anchor 預示 4 數 bounds、finite、材料裁切、不越界;點 `.face-rule-hit` 選取+標籤,零寫入 |
| R-04 | — | PASS | 5 個控件高 ≥44px、inspector/page 無水平溢出(319/319、390/390);**SR24 實機未驗** |
| R-05 | PASS | PASS | 隱藏共用參考線→hit=0、anchor 停用、dump 與 history 不變 |
| R-06 | PASS | PASS | source jump 到同 editor/ruleKey,零寫入,boundary 快取保留;**「延遲中途換 view 不被拉回」未驗** |
| R-07 | PASS | PASS | 預覽含 2 配置;取消零寫入;確認單步;undo/redo 各一步;ruleKey 不變 |
| R-08 | PARTIAL | PARTIAL | sample ≤96 且標「抽樣未完整」、零寫入、exact 仍可完整定位 PASS;**晚返回回應不覆寫 raw/焦點未驗** |
| R-09 | PASS | PASS | 真 gridrule guide(axis u、off 200);錯 source 被 native 拒絕(WRONG_SOURCE,confirm disabled)零寫入,取消後 history 不變 |
| R-10 | PASS | PASS | 未存在 selector→native 拒絕,同表單與角色截面保留、零寫入;只修 selector 重試成功,undo 1 步移除/redo 1 步恢復(timbers 5→4→5)。註:`history.undo.length` 在上限時不增,故改用 undo/redo 實效判單步 |
| R-11 | PASS | PASS | 有引用的規則改來源:`#impact-confirm` disabled、World 不變(`r11_impact_locked_390.png`) |
| R-12 | PASS | PASS | 無來源規則的面:進面+格線工具後 `grid-rule-query` 0 次。UI 減項(≤3 常駐說明)**未判** |
| R-13 | 未驗 | 未驗 | 手動子格草稿遇晚回應,未做 |
| R-14 | 未驗 | 未驗 | 刪最後一條規則後晚返 exact,未做 |
| R-15 | 未驗 | 未驗 | 我的 newid 延遲配方在角材表單**未攔到任何 newid(held=0)**,等於沒走到受測路徑,不計 PASS |
| R-16 | PASS | PASS | Save→ZIP(1564/1562 bytes,sha256 見 json,只在 TEMP)→新專案→Open:dump 逐字相同、面內 3 線重現。下載檔不在證據目錄 |
| R-17 | PASS(縮窄) | PASS(縮窄) | 鍵盤:cell 輸入→Tab 到 `[data-rule-exact]`、Enter 完成查詢「已核對」、焦點 2px 外框。**`.face-rule-hit` tabIndex=-1,不可鍵盤選線**(是否為缺陷依契約未定,只記錄) |
| R-18 | PASS | **FAIL** | 見下 |

**R-18 失敗(390 才有,可重現)**:在 390×844 面1(有來源規則),角材工具下於 `#tbAnchor` 先選 u 再選 `at-line … v 0` 的瞬間,console 連噴 3 次 `Error: <rect> attribute height: A negative value is not valid. ("-80.32…","-80.32…","-480.32…")`(出處 app.js:765 createElementNS,`probe_neg.out`;`r_run2_390.json` 的 `error_locations`)。1382 無。**未在 main 做對照**(main 沒有規則線可選,無等價操作),故不知是否為本 PR 引入;該行為相關程式(`feAnchorLineInfo`)本 PR 有改。另:`r_run4` 兩個寬度各有 1 筆 `404 http://127.0.0.1:8872/null`(角材流程中,來源未查);首頁載入(階段 1)沒有此 404。
**P88 自動化(補充,不取代上表)**:`GEOMETRY_GRID_SYSTEM_ONLY=1 node cdp_test.js`(`p88_cmd.sh`、`p88_cdp.log`、exit=1):P70/P87 全過,P88 於 390 的「單規則引用數」前 FATAL `Rule line control unreachable [data-rule-cell-i]`(y=1411,hit:false),此前已過 289 行 ✓、0 行 ✗;只跑一次,未重試,原因未定(我自己的 Playwright 同流程在 390 通過 R-10 摘要檢查)。故 P88 標 **incomplete/FAIL(單次)**,不得宣稱 105/105。

## 5. #156 #118 guide 所有權與取消檢查(PASS 6 / PARTIAL 3 / 未驗 3 / FAIL 0;G-01~G-12)

- main `6562fa53`;PR head `2a7d9cba8d199a33f703e721553034400c0c5764`(測前後不變);tree `71c0c7cc6f6cde1854ba7f70880bb31761f05e8b`;port 8873;`/runtime` fresh:true、root=`D:\geo-bqa-156`、version `32deb2a1…c30c1c`、probe exit 0(`runtime.json`、`probe.txt`)。基線:main 同 port 8870 同腳本(`g_results_main.json`、`g8_results_main.json`)。
- **延遲注入屬測試儀器**:`window.fetch` 暫時包裝,只攔 POST `/api` 且 `cmd` 以 `snap `或 `newid` 開頭的請求,手動放行(契約作者自擬配方,PR 未提供)。腳本 `g_run.py`、`g8_run.py`。

| 條目 | 156 | main 基線 | 判定 |
|---|---|---|---|
| G-01/02 一般建立(picker 與 drag,1382/390) | guide +1,undo→0、redo→1 | 相同 | PASS |
| G-03 snap 階段延遲→Back→放行(picker/drag × 2 視口) | guide 0、World 不變、離開面 | **guide 1、World 變**(缺陷重現) | **PASS(基線有重現)** |
| G-03 newid 階段延遲→Back | guide 0 | guide 0(**基線也 0**) | **基線無法重現,不判 PASS**,標 PARTIAL |
| G-04 同面重入(snap 階段) | 舊手勢零寫入 | guide 1(重現) | PASS(舊手勢);重入後新手勢可建一次**未驗** → PARTIAL |
| G-04 同面重入(newid 階段) | 0 | 0(基線無法重現) | 同 G-03 newid |
| G-05 換 context/history/session | — | — | 未驗 |
| G-06 移動既有 guide 延遲 | — | — | 未驗 |
| G-07 newid 被拒 | toast 顯示訊息、零寫入 | toast「I8: invalid definition/reference」 | PASS(縮窄:我注入的拒絕訊息為 `injected newid failure`,PR 預設字串「無法取得參考線識別…」未走到) |
| G-08 取消的卡片「檢查」(有未套用參數草稿,confirm 按取消) | 草稿/選取/抽屜與之前完全相同(兩視口) | 390:**右抽屜被錯開**(`g8_main_cancel_390.png`),1382 相同 | **PASS(基線在 390 有重現)** |
| G-09 接受 | 選取目標;390 開右抽屜、1382 不開 | 相同 | PASS |
| G-10 卡片鍵盤 Enter/Space | — | — | 未驗 |
| G-11 回歸 | 一般建立/undo/redo 同 main;Save→Open 後 guide 仍在**未驗** | | PARTIAL |
| G-12 console | 兩視口 0 錯誤 | | PASS |

計數:PASS 6(G-01、02、07、08、09、12)/PARTIAL 3(G-03、04、11)/未驗 3(G-05、06、10)。草稿類型:G-08 用「新增參數卡且未套用」(`DraftGate` 會跳 confirm「參數有未套用的草稿…」)。

## 6. 已停 PID(皆為本人啟動並記錄,`env/pids.log`)

serve.py:25980(main 階段 1)、41972(#134)、2092 與 37516(#156,兩次)、13248(main 基線);其子 bridge:11324、20996、20768、43240、34664;conhost:10684、28656、22336、19436、33308。#152:wm serve 28880 與腳本自起 7784、39572、30240、30900、2572。收尾 `netstat` 8870–8873 無 LISTEN;未碰任何其他 PID,未按名稱殺。

## 7. incomplete / 未驗清單

- #152:W-19(inventory/umbrella)、W-11 UI 匯出下載、W-15 列印、W-10 的 `javascript:` URL(無法匯入)。
- #134:R-13、R-14、R-15;R-06/R-08 的「晚返回」子條;P88 自動化 FATAL 未結案;R-18 的 390 console 錯誤與 `/null` 404 缺 main 對照。
- #156:G-03/G-04 的 newid 階段(基線無法重現)、G-05、G-06、G-10、G-11 的 Save→Open。
- 人工項目(一律未驗):SR24 實體手機觸控/鍵盤/IME、iOS、OS 檔案選擇器與下載位置。
- 未做:msedge 對照(Chromium 正常,不需要)。
- 結果檔小提醒:`pr152/results_part1.json` 的 W-13 為初版誤判 FAIL,以本 README 複核為準;`pr134/r_run3_*.json` 的 R-10/R-11 為舊配方(未備支撐)結果,已被 `r_run4_*.json` 取代,僅 R-12、R-17、R-09.options 取自 r_run3。
