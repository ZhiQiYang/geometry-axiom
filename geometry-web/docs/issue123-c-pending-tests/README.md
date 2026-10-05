# #123 C-review 第三節「尚未確認」五項實測

> 實測員:Claude(Sonnet 5.5),2026-10-06。只量測,不改產品程式、不 commit。
> 全程 fresh Chromium/Chrome profile、真 UI 操作(Playwright 鍵盤/滑鼠;cdp_test、space_model_test 為專案既有測試)。

## 環境

| 項目 | 值 |
|---|---|
| 被測 SHA | `d6b4b450d741fcbbfd75c51631915d3082926990`(`git archive d6b4b45` → `%TEMP%\geo123c\export`);補丁只在匯出副本 `export-s`(測項 4)、`export-p3`(測項 3),無任何 git worktree 被改 |
| 服務 | `serve.py 8861`,獨立 TEMP(`geo123c\tmp`)與 `GEOMETRY_FEEDBACK_DIR`(`geo123c\fb`);每個測項/補丁狀態各用新服務 |
| bridge / model-base | 沿用 `%TEMP%\geometry-qa\bin\bridge-c5955d469b13.exe`(檔名即前次 RUN-LOG 的內容雜湊 c5955d469b13)、`model-base-079eda49f0df.exe`;**未重編**。SHA-256:bridge `133E11F2…E70897`、model-base `494A9686…D3B0`。註:前次 RUN-LOG 的「內容雜湊」演算法未載明,本次以 SHA-256 前 12 碼比對不上檔名,故僅憑檔名沿用,未能獨立核對 |
| 瀏覽器 | Playwright(`geo2a-venv`,唯讀沿用)+ Chrome 本機安裝;cdp_test/space_model_test 自行起 headless Chrome(CDP port 9361/9362) |
| 資源取樣 | 可用記憶體 MB:1502(起)、1294、1656、3007、2077、2438、1631(止),全程 ≥800 MB,無等待/受阻;CPU 抽樣僅有收尾一筆 ≈100%(cdp 長跑期間機器忙碌,耗時 1055–1089 s 含此因素) |
| 其他 | 視窗 1382×804(測項 5、1、2);cdp_test 固定 1400×900(其內建) |

## 結果總表

| # | 項目 | 被測 SHA | 步驟 | 量測值 | 通過條件 | 結果 | 證據檔 |
|---|---|---|---|---|---|---|---|
| 1a | 3D 建模首個 Tab 停點 | d6b4b45 | 檔案▸3D 建模(進建置頁)→ `activeElement.blur()` 使焦點在 body → 連按 Tab | 第 1 次 Tab 後 `activeElement` 仍是 BODY(焦點離開頁面元素,`focusVisible:false`、`outline:3px none`;重跑 2 次相同);第 2 次起 `#projectInfoButton`(在 dialog 內)`:focus-visible` 命中,`outline: 3px solid rgb(139,157,236)`,第 3 停 `保存` 亦同,`smClose` 第 4 停 | 首個**實際元素**停點 outline-style≠none | **PASS**(註:第 1 次 Tab 無元素可量,見不確定點 1) | `measurements/t1_focus.json` 鍵 `sm_tab_seq[0..5]`;`t1b_toolbar.json` 鍵 `sm_repeat`;`screenshots/t1-sm-first-tab.png` |
| 1b | 面內首個 Tab 停點 | d6b4b45 | 載入範例▸雙擊面卡進面內▸按「知道了」▸blur▸Tab | 首停 `#faceUndoButton`,`focusVisible:true`,`outline: 2px solid rgba(78,103,232,0.55)`,offset 2px | style≠none | **PASS** | `t1_focus.json` 鍵 `face_tab_seq[0]` |
| 1c | **F5 補量:面內工具列按鈕焦點框** | d6b4b45 | 面內鍵盤 Tab 流中取 `[data-face-tool]` 各鈕 | select / redraw / shape(`#shapeToolButton`) / guide / hole / timber / grid / pan 皆 `2px solid rgba(78,103,232,0.55)`,offset 2px,`focusVisible:true`;`#feSelectionSummaryHelp` 為 `2px solid rgb(56,89,199)` | style≠none(並補上 F5「面內 2px」缺的實測) | **PASS**(面內工具列 2px 現已實測) | `t1b_toolbar.json` 鍵 `toolbar_walk[0..9]`;`screenshots/t1b-face-toolbar-focus.png` |
| 2 | B6 已讀後重進面 1 選 1 支角材 | d6b4b45 | 進面 1▸按「知道了」▸`#workspaceBackButton` 離開▸重進▸(A)點右欄角材列 / (B)點畫布上角材矩形選 1 支 | (B,鏡頭未動)卡片 272,128–505,190(233×62);最上 `.fe-edge-dim`「4000」x909.5–936.1(A)/ x647.6–674.2,y117.9–132.9(B);**所有 `.fe-edge-dim` 與卡片交集面積皆 0**。外環頂(由 `fe` 計算)B=156,A=182。重進後 0 選時卡片 hidden,`fe.viewportSize.top=40` → 卡片是在初次 fit **之後**才顯示 | 交集=0 | **PASS**(字面條件);另見下「附帶觀察」 | `t2_b6.json` 鍵 `verdict`、`reenter3_1sel_canvas`、`reenter_1sel`、`reenter_0sel`;`screenshots/t2-b6-reenter-1sel-*.png` |
| 3 | B 修法(`renderSelectionSummary()` 置於 `feFit` 前)× cdp_test `:3976` 等待條件 | d6b4b45 + 暫時補丁(僅 `export-p3`) | `GEOMETRY_CDP_FROM_P31=1 node cdp_test.js`(略過 P1–P30,涵蓋 P35 的 `waitForFaceViewport` 之 `v.top===i.top`),20 分鐘上限;補丁前 2 次、補丁後 1 次 | P35 共 14 行斷言:補丁前 run1 14/14 ✓、run2 14/14 ✓;補丁後 14/14 ✓,無逾時。整檔(P31–結尾):run2 與補丁後皆 `completed:true`、761 通過/0 失敗、EXIT=0,耗時 1055 s / 1089 s(<1200 s)。**補丁前 run1** 在 P56-6 失敗並 FATAL(`connection.phase` 錯誤「橋接器連線中斷」),620 s 結束;同碼 run2 通過 → 判為偶發,與補丁無關(補丁前就發生) | 不逾時、該段 pass | **PASS** | `t3_cdp_b6_patch.json`;三份 `t3_cdp_*.log`;`patches/b6-render-summary-before-fit.patch` |
| 4 | F6 改 12px × GEO210 @690×668、390×844 | d6b4b45 + 暫時補丁(僅 `export-s`) | `GEOMETRY_SPACE_FLOW_ONLY=1 node space_model_test.js`(43 斷言),補丁前/後各 1 次(另加僅 `console.log` 的量測儀器補丁,前後皆有) | 690×668:`confirmBottom` 509.8→511.6,`bottom` 570.3(餘裕 60.5→58.7);390×844:677.6→681.2,`bottom` 746.3(餘裕 68.7→65.1);兩者 overflow=0;補丁後 `.sm-help`/`.sm-view-direction` 皆 12px(`.sm-guide` 在此兩寬度基線就是 12px,因 ≤720px 媒體查詢);43/43 通過 | `confirmBottom<=bottom` | **PASS** | `t4_f6.json`;`t4_space-flow_*.log`;`patches/f6-font12.patch`、`instrument-space-log.patch` |
| 5 | G3 刪除確認(有/無配置來源) | d6b4b45 | 載入範例▸`#btnNewGridSystem` 建來源▸「＋ 選邊界建立配置」建 1 配置▸再建第 2 來源;選列表列→按 `#gridObjectDelete` | **有配置**:出現 `.reference-impact`,但為「變更無法套用…I8…I37: grid-system is still referenced by a grid-binding」,取消鈕為「返回修改」,`#impact-confirm` **disabled**;返回後來源仍在;無法走到確認/Ctrl+Z。**無配置**:**不出現**對話框,直接刪除,toast「網格系統 2 已刪除,可 Ctrl+Z 復原」(class `toast error`);Ctrl+Z 後來源 2 回來(`exists:true`) | 「依預期出現/不出現」 | **PASS(觀察結果,見解讀)** | `t5_g3_delete.json` 鍵 `with_binding`、`without_binding`;`screenshots/t5-*.png` |

## 解讀(只寫數值支持的)

- **測項 1**:C 擔心的「首停點無焦點框」未被數值支持:首個實際元素停點(3D=`#projectInfoButton`、面內=`#faceUndoButton`)與面內全部工具列鈕都有可見 outline。唯一的「none」是 3D 工作區第 1 次 Tab 後 `activeElement` 為 body(`3px none`)——那是**沒有元素獲焦**,不是元素缺焦點框。
- **測項 2**:字面交集為 0,但這是因為 `.fe-edge-dim` 的標註文字落在卡片水平範圍外(卡片 x272–505,「4000」x≥647)。**卡片與外環頂部仍有重疊**:外環頂 156 < 卡片底 190,且外環 x311–1010 與卡片 x272–505 重疊(外環左上角、含最上方角材被卡片蓋住 311–505 一段)。C 描述的「`feResizeViewport` 不補 fit」得到數值支持:重進時 `fe.viewportSize.top=40`,選 1 支角材卡片出現後相機不動。(列表選取 A 變體會平移相機——「定位角材」按鈕——故外環頂移到 182;與 B 變體不同,兩者都記錄。)
  - 補丁影響(`t3b_b6_with_patch.json`,同流程在補丁服務上):**首次進入**時 `viewportSize.top` 40→114,外環頂 156→230(高於卡片底 190,解掉遮蔽);但「已讀後重進再選 1 支」情境與未補丁完全相同(top=40、外環頂 156/182)——**B 的一行補丁不涵蓋此情境**,需另案(例如選取使卡片出現時重算 inset)。
- **測項 3**:補丁不會造成 `:3976` 等待逾時或失敗;整檔補丁前後結果等值。
- **測項 4**:12px 使 `confirmBottom` 下移 1.8–3.6 px,餘裕仍 ≥58 px。注意:該測試的 PASS 行不印數值,本次靠儀器補丁(只加一行 `console.log`)取得。
- **測項 5**:A 的「G3 無確認」與 B 的「未見 confirm」只對**無配置**來源成立(直接刪、有 Ctrl+Z toast);**有配置**來源會跳影響對話框,但在本場景(範例場景+該配置)是「無法套用」型,只能返回。C 缺陷 #10 的「走 confirmReferenceImpact、另有 Ctrl+Z toast」兩半各自對應上述兩種情境。「確認後可 Ctrl+Z」僅在無配置情境驗證;**有配置的『確認後』路徑本次因確認鈕 disabled 無法走到**(未先刪配置,超出範圍)。toast 用 `error` class 呈現成功刪除,是樣式觀察,不判缺陷。

## 已停 PID(皆為本次自行啟動)

serve.py:1948、25576、25040、28572、29200、7760、39616;其子 bridge:34148、17868、12000、33048、32232、32100、30640;conhost:38544、36716、26320、17296、26828、29072、34596(逐一記於 `%TEMP%\geo123c\pids.log`)。測試工具自起之 headless Chrome 由 cdp_test/space_model_test 於結束時 `kill`,收尾時以 `geo123c` 命令列掃描無殘留;8861 已無監聽。未碰 PID 19324(他人的 node)及任何以名稱匹配的程序。

## 限制 / 注意

- 以 headless Chrome + Playwright,未含真實鍵盤/螢幕閱讀器;測項 1a 第 1 次 Tab 行為在有頭瀏覽器可能是進入網址列,屬瀏覽器差異。
- cdp_test 使用 `GEOMETRY_CDP_FROM_P31=1`(略過 P1–P30,不影響 P35 區段);整檔 P1–P30 未跑。
- 測項 2/5 的場景為合成範例(「載入預設場景範例」+ 測試用網格來源),無私人圖紙。
- 本目錄 `repro/` 的 `common.py` 是 `issue123-evidence/repro/common.py` 的改版(port、fresh profile、記憶體守門);`svc.ps1` 只停自己記錄的 PID。
