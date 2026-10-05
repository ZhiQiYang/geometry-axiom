# C 獨立核對:A 證據與 B 方案

> 作者:Agent C(對抗審查員,opus,唯讀)。C 無寫檔工具,本檔由協調者**逐字轉存**其回報,未改判定。
> 審查基準 `d6b4b450`;審查期間 main 前進至 `6ee719d`(#135 合併,僅文件),下列行號仍有效。
> 協調者抽查 4 條並確認成立:app.css:11 / 2172-2176(accent 僅 composition 下為 #365bf5)、workspace-guidance.js:41(dynamic 狀態已讀後仍顯示)、app.js:3020/3023(feFit/feSetTool 行號)、app.js:609-611(刪除走 confirmReferenceImpact)。
> 標 PLAUSIBLE 者為算術推導,未實測。
> 2026-10-05 UTC 文件勘誤:下文只更正 fit 適用範圍與 F5 焦點證據的元件歸屬;原 C 轉存歷史、A/B 原檔與原始量測保留,未重跑實測。

## 一、確定缺陷(依嚴重度)

1. **B 的 B6 修法仍須核對卡片出現時序**(B-fix-design.md:23)。按「知道了」後,選取角材卡片仍可由 dynamic 狀態顯示(workspace-guidance.js:41;`stage_x1 face/b6_1sel` open:false、233×62 @272,128)。風險限於卡片在初次 fit 後才出現,且 `feResizeViewport()` 不因只有 top inset 變化就補 fit(app.js:2978-2989);此情境的遮蔽仍待實測。**明確呼叫 `feFit()` 會重算 inset**:summary 未 hidden 時,top 為 `max(40, summary.bottom - viewport.top + 40)`,再限於視口高度的 30%(app.js:2957-2961),不能稱此後每次 fit 都只留 40px。issue S3 要的是「框選提示僅相關狀態顯示」,B 的方向是縮小圖。
2. **B 回歸步驟 1 跑錯對象**:直接 `node marquee_test.js` 只跑框選規則單元契約(marquee_test.js:442-446);S10 與 ResizeObserver 段只經 cdp_test.js:7007 執行。
3. **B 回歸步驟 2 選擇器不存在,通過條件會自敗**:`.face-dimension-label` 只在 app.css:755 與原型;app.js 實際產生 `.fe-dim.fe-edge-dim`(app.js:4877)。標註距外環約 29px 加半字高(app.js:4850-4852),套 B 修法後標註頂只比卡片底低約 5px,達不到 B 自訂的 +8px。(PLAUSIBLE)
4. **問題 3 的 B 案(sticky)無效**:`.ig-canvas` 父層 `.ig-main` 只包畫布(grid-system-workspace.js:307),sticky 範圍受父層限制,畫布不會進初始視口。
5. **問題 3 的 Tab 順序推論方向相反**:DOM 中 `.ig-main` 在 `.ig-inspector` 之前(js:307),現行手機 `order:1/2`(css:198-199)**已經**讓視覺與 Tab 順序分家;A 案反而讓兩者恢復一致。
6. **F5「全站 --accent:#365bf5」錯誤**:該值只在 `body.canvas-composition` 下(app.css:2172-2176),根層為 #4e67e8(app.css:11);進面內時 composition 關閉(app.js:9136),改 `var(--accent)` 會讓 3D 主色隨入口不同,無法達成「四處主要按鈕一致」。
7. **A 判 B6「1 選不一致不成立」判錯**:`oc_1sel` 文字含「知道了」,即 state.open 為真(workspace-guidance.js:44),guidance-open 強制顯示(workspace-guidance.css:6);面內 1 選則在已讀後量(open:false),狀態不對等。已讀狀態下主畫布 1 選是隱藏的(app.css:2256、workspace-guidance.css:11、marquee_test.js:117)。結論:#138 README 數值錯,但「不一致」本身成立,且屬 GEO-216 刻意設計。
8. **F5 的 2px 證據須區分元件**:`stage_f.json tabOrder1382[6]` 量到的是 3D `smCanvas` 的 `2px solid rgba(78,103,232,0.55)`(對應全域規則 app.css:66-67)。此值只支持 smCanvas 已量到 2px;**面內工具列 2px 仍無對應實測**,不能以不同元件的焦點值替代。歡迎 CTA 的 3px／offset 3px 另由 `focusOutlineWelcomeTry` 支持。
9. **A 把 G3 判「實證重現」過度**:實測時刪除鈕旁是「建立配置」而非「完整工作區」;只有配置模式或非無限來源才緊鄰(grid-inspector.js:48),該情境未量。應改為「部分重現+程式推導」。
10. **B 說刪除前「未見 confirm」不實**:`api()` 收到 preview 走 `confirmReferenceImpact`(app.js:609-611);grid_rule_editor_test.js:133 按 `#gridObjectDelete` 後處理 `.reference-impact[open]`;刪除後另有可 Ctrl+Z 的 toast。再加一層會變雙重確認。
11. **F1 a 案會改到既有測試主視窗**:`max-height:900` 含 900,space_model_test.js 主視窗 1400×900(約 :391、:404)會換成緊湊版面,截圖基準跟著變,B 未提。
12. **B 引用行號/數值有誤**:feFit 在 3020(非 3026);feSetTool 在 3023(非 3028);feResizeViewport 在 2978;`.sm-view-direction` 在 space-workspace.css:36(非 :2);`#v3ZoomLevel` 高 28;390px 網格縮放鈕為 34×44(非 44)。

## 二、設計改善(取捨,需 dot/使用者決定)

- B 的「安全」只看檔案清單,未顧 issue 協調要求:3D space-workspace 須與 #119(OPEN)協調;project UI 須與 #116、#77 協調,而 B:10 把 project-ui.css 列為可放規則處。issue 要求先做 S0/S1 tokens,B:169 一面說 F5「可安全開始」一面說色值等 S1,前後矛盾。
- 問題 2 用 `(pointer:coarse)`,但主畫布 44px 規則只看 `max-width:680`(app.css:2463/2506),造出新的不一致;觸控筆電 1382 寬時 B 的「桌面維持 29px」條件也會失敗。workspace-shell.css 是 S1 共用標頭檔,放三視圖規則日後會與 S1 衝突。
- 面內左上三個浮層搶同一位置:`#feLatticeDensity`(app.js:2741,top:8)、#134 新增 `#feRuleDensity`(top:42,掛在 faceEditorViewport 內)、選取卡片(app.css:2131),都沒算進 `feViewportInsets`。#134 合併後 B6 修法仍不完整。
- B 說 `.sm-workspace` 高度在 801–900 會一併變貼邊版,很可能不會發生:後載的 workspace-shell.css:2 `dialog.workspace-shell` 特異度較高會蓋過。(PLAUSIBLE)

## 三、尚未確認(需實測)

| 項目 | 量什麼 | 通過條件 |
|---|---|---|
| 首個 Tab 停點焦點框 | `stage_f tabOrder1382[0]`(smClose)為「3px none」,`stage_x1 face/tab1382[0]` 為「none 3px」;從 body 按 Tab | `:focus-visible` 命中且 outline-style ≠ none |
| B6 已讀後情境 | 已讀後重進面 1、選 1 支角材 | 卡片矩形與最上方 `.fe-edge-dim` 交集 = 0 |
| B 修法 × cdp_test.js:3976 | 等待條件 `v.top===i.top`;卡片進入時可見、之後 dismiss | 不逾時 |
| F6 改 12px | space_model_test GEO210 @ 690×668、390×844 | `confirmBottom<=bottom` 仍成立 |
| G3 刪除確認 | 對有/無配置的來源各按刪除 | `.reference-impact` 對話框依預期出現/不出現 |

## A 結論勘誤表

| 項目 | 判定 | 證據 |
|---|---|---|
| B6 主畫布 1 選可見 → 不一致不成立 | 不成立 | `stage_g oc_1sel.text` 含「知道了」;workspace-guidance.css:6、:11;marquee_test.js:117 |
| B6 README 與 JSON 數值矛盾 | 成立 | `stage_g oc_0sel` / `oc_1sel` |
| F6 顏色 README 與 JSON 不符 | 成立 | `stage_f 1382x804/help[0]`、`help[8]` |
| F5 鍵名不符 | 成立 | `stage_f` 頂層鍵為 controls、tabOrder1382 |
| F5 面內工具列 2px 的實測證據 | 未量;3D smCanvas 2px 已量 | `stage_f tabOrder1382[6]` 的 id 為 smCanvas;app.css:66 是規則,不等於面內工具列實測 |
| G3 實證重現 | 存疑 | grid-inspector.js:48;`stage_g gi/1382x804` 三鈕順序 |
| B6 遮標註僅截圖目視 | 存疑 | `face/1382x804/#faceEditorViewport`(y116、h656)配合 app.js:2958-2971 可算出外環頂 156 < 卡片底 190 |
| X6、F1、G4 數值、43 項計數與 P1/P2/P3 分級 | 成立 | 已逐鍵核對 JSON |

## B 方案風險表

| 項目 | 判定 | 證據 |
|---|---|---|
| B6 根因(fit 時卡片被當 hidden) | 成立 | app.js:2957-2962、3020/3023;截圖 zoom 0.1747 與畫面 17% 吻合 |
| B6 範圍只在首次進入 | 不成立 | workspace-guidance.js:41;`face/b6_1sel` |
| 問題 2 根因(三視圖時 canvas-composition 關閉) | 成立 | app.js:9136;app.css:333、2506;index.html:285 |
| 問題 3 根因(手機版設定排在畫布前) | 成立 | grid-system-workspace.css:189、196-201 |
| 問題 3 的 B 案與 Tab 推論 | 不成立 | 見缺陷 4、5 |
| F1 斷點差 4px | 成立 | space-workspace.css:12;`stage_f mediaCompact` 全為 false |
| F5 accent 說法 | 不成立 | app.css:11、2172 |
| G3「無確認」 | 存疑 | app.js:609-611;grid_rule_editor_test.js:133 |
| 三個 CSS 檔不與開啟中 PR 重疊 | 成立(僅就檔案) | 逐一核 `gh pr diff` #134、#136、#137、#129、#138、#139、#140 |

## C 核定:能安全開始實作的檔案範圍

- **可開始**:`grid-inspector.css`,只限 G3 文字對比(≥4.5:1)與間距。
- **可開始**:擴充 `marquee_test.js` / `space_model_test.js`(marquee_test 瀏覽器段經 cdp_test.js 執行;只跑,不改 cdp_test.js)。
- **有條件**:`space-workspace.css` 只做 F1 a/b 兩案,前提是 #119 負責人同意,且接受 1400×900 測試基準變動。F5、F6 等 S1 定案。
- **待 dot 決定**:三視圖手機規則放哪個檔(不建議 workspace-shell.css)。

**整體**:A 的數值索引大多正確,但 B6「不一致不成立」需區分已讀／開啟狀態;F5 則須分清已量的 3D smCanvas 2px 與未量的面內工具列。B 的根因大致成立,但 B6 時序範圍、問題 3 sticky 與 Tab 推論、F5 accent、兩條回歸步驟有實錯;B6 明確 fit 會重算 inset,初次 fit 後卡片出現的風險仍待情境驗證。**以 C 的修正為準**,否則實作者會做錯。
