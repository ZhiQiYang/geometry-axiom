# geometry-axiom 已知問題索引(產品驗收用)

- 被測版本:main `d6b4b450d741fcbbfd75c51631915d3082926990`(= PR #133 的 merge commit)
- 產出時間:2026-10-05;資料來源:`gh`(repo ZhiQiYang/geometry-axiom)、`git -C D:/geometry-axiom`、BACKLOG.md / 決策佇列.md / RISKS.md、`feedback_cli.py list`
- 全程唯讀:未留言、未改標籤/分支、未建立任何東西。
- 「在被測版本」判定法:對每個 merged PR 的 mergeCommit 跑 `git merge-base --is-ancestor <sha> d6b4b45`。近 30 天(2026-09-05 起)共 88 個 merged PR,**88/88 皆為 d6b4b45 祖先(exit 0)**。open PR 的 head 皆不是祖先。
- 重要提醒:issue 的「OPEN」不等於「功能未合入」。多數 open issue 是總工單/分段工單,部分切片已合入 main;下表逐項標明。
- 本索引中「症狀關鍵字」用於之後比對新發現。判斷不了者寫「未判定」。

---

## 1. Open PR(2 個)

| PR | 分支 | 作者 | 最後更新 | 草稿 | 範圍(一句話) | 在 d6b4b45? |
|---|---|---|---|---|---|---|
| #134 | codex/issue61-rule-line-display-20261005 | ZhiQiYang | 2026-10-05 13:46Z | 是 | #61 切片 2:面內畫布/角材 anchor/guide 顯示並追溯 native 來源規則子線(RuleLineRef);含 anchor bounds、凹形/孔導航保留、390px 溢出修復 | 否(head 5e4ae3e 非祖先);已知:full CDP 在該分支尚未列 pass,CI 前次 head 七 jobs failure 且 log 空 |
| #129 | docs/panel-fill-decisions-20261005 | ZhiQiYang | 2026-10-04 19:12Z | 否 | 僅改 `決策佇列.md`:記錄 #128 PANEL-FILL(完成面/面材鋪滿)拍板決策 | 否(head 1269e6b 非祖先);純文件,不影響被測功能 |

近期已關閉未合併 PR:#50(組構身分跨草稿,2026-10-03,已由其他 PR 取代)。

## 2. 近 30 天 merged PR(88 個,全在 d6b4b45;下面只列與 9 類流程相關者,完整清單見 gh)

(mergeCommit 簡碼)

| 流程類 | PR | 簡述 | merge sha |
|---|---|---|---|
| 匯入/描輪廓 | #63 | #54 來源綁定房間輪廓候選與核對流程(向量優先、影像輔助;/9 保存格式) | c87be115 |
| 匯入/描輪廓 | #74 | PDF 人工描繪來源端點吸附、9% 縮放格距顯示 500mm 誤示 50mm | 92c1ce55 |
| 匯入/描輪廓 | #76 | PDF 吸附 phantom targets(annotation appearance、文字裁切 mode 4..7) | a274cae7 |
| 比例尺/描輪廓 | #72 | 校準後「選房間/描外環」入口、既有外環不隨校準縮放、取景範圍 | 0f3c1a6f |
| 建空間/方向 | #121 | 本機空間預覽啟動修復、描面圖方向(traced-plan orientation) | 07d5dde1 |
| 建空間 | #124 | #119:材料牆需求未滿足須拒絕 + native 容量 preflight(16/16/64) | 4bea91a3 |
| 建空間 | #120 | P79 旋轉 expected 改獨立 oracle | 7414cfd2 |
| 多房間 | #102 | #77 人工多房 foundation(source-plane/room-collection,**未接線**) | d1a161f6 |
| 多房間 | #114 | #77 共享房間所有權整合、來源歷史保全(WIP 標題,已 merge) | 861b65e9 |
| 網格/參數 | #27、#28、#31、#32、#5–#9、#14–#16 | 參數網格、交丁、子網格、無限網格、格線顯示 | (見下方 sha 對照) |
| 網格/參數 | #127 | 參數 re-preview 舊 token 仍可 confirm → TOKEN 錯誤卡 pending(P76 阻塞型態) | 417f4c0 |
| 網格/子網格 | #107、#126、#133、#130 | #58/#59/#60/#61:REPEAT 規則、native 規則保存、正式規則編輯器 slice1、2a 定義圖 | c0d3fbad/8d134fc/d6b4b450/ff279f2a |
| 取消/撤銷 | #73 | undo/redo 須持 busy 至 repaint 完成 | 257742b5 |
| 保存/重開 | #55、#66、#111、#104、#126、#133、#132 | format 8 驗證、runtime 靜態資產版本、raw 網格草稿保存、規則保存(/13)、PDF 參數證據入 ZIP | (見下方 sha 對照) |
| 窄螢幕 | #131 | 390px 下 feedback launcher 擋住「建立」選單 | b87f381e |
| 窄螢幕/UI | #125 | #116 B 右鍵選單 + 3D 旋轉裁切 | a4caf166 |
| 效能 | #64 | 網格/hover/runtime-check 效能 | d40dee0c |

(確切 sha 以 `gh pr view <n> --json mergeCommit` 為準;本表重點在「皆為 d6b4b45 祖先」已用 git 驗證。)

## 3. Open issues(24 個)與歸類

| # | 標題(縮) | 流程類 | 現況與「是否在被測版本」 | 症狀關鍵字 |
|---|---|---|---|---|
| **#54** | 從 PDF/圖片底圖取得房間輪廓 | 匯入/比例尺/描輪廓/保存 | **OPEN,但主體已合入**:PR #63 已於 2026-10-03 merge(c87be115,在 d6b4b45)。issue 保持開啟僅因驗收項未全勾、後續切片分流到 #87/#77。**目前無 open PR 掛 #54,無 GitHub 留言**(comments=0)。詳見第 4 節 | 校準後原矩形被當完成;房間落在外環/舊視野外;edge-open;tooManySegments;漏邊/凹口被吞;候選確認替換外環;/9 保存 |
| **#87** | [B] 同頁多個獨立房間候選逐一核對 | 描輪廓/多房間 | OPEN,**未實作**(規格+排程,無 PR);被測版本沒有「同頁多候選」功能 | 同頁多房間候選、批量候選、session-only 候選列表 |
| **#77** | 同 PDF 共享來源基準,連續建立獨立房間邊界 | 多房間/保存 | OPEN。PR #102(foundation)、#114(接線 WIP)已合入;**官方留言(2026-10-04 05:25)稱「五項必要正式 owner gates 未做」**:registry 往返、未知 envelope 拒絕、source closure/native final-object、attachment 與 undo/redo、late-context 守門。正式入口接線完成度:**未判定**(BACKLOG ISSUE-77「接線驗證中」) | 共享校準、新增不覆蓋舊房、basis 變更只標待複核、同 ID 重建、unlink 後不刪 geometry、room metadata+native 同步 undo |
| #119 | [正常流程] 材料牆容量不足時需求與結果不一致 | 建空間/保存 | OPEN。PR #124(在 d6b4b45)已做「拒絕未滿足牆需求+容量 preflight」;issue 另列「十邊案例 .gcanvas 保存重開未驗」,未宣稱通過 | I33/SPACE_CAPACITY;walls:null;預設勾牆+100mm 但結果無牆;十邊/2+10+2+7+1=22>16 |
| #117(closed) | 方向驗證 oracle/正常流程 | 建空間 | 已 closed 2026-10-04,修復在 d6b4b45(PR #120、#121) | 描面圖與 3D 俯視上下顛倒;凸角在左下變左上;空間預覽「預覽回應缺少空間或摘要」(GEO-243) |
| #118 | 結構風險/測試有效性/等待成本 | 全部(工程) | OPEN,分析類;不影響產品行為 | 循環 oracle;過度宣稱斷言;弱測試 |
| #123 | [UI整合] 六工作區統一(43 項) | 窄螢幕/UI | OPEN,S0–S6 未做(僅 PR #131 修一個子項)。**43 項需對現行逐項複核,非確證缺陷** | header 單列 56px、按鈕色不一致、welcome 與視角重疊、900/390px、左欄圖層、對齊頂點圖位置 |
| #116 | [B] 游標 v2 + 情境右鍵選單 | 描輪廓/窄螢幕 | OPEN。PR #125 已合入(僅「面內」完整切片);物件畫布/空間平面圖/三視圖、觸控長按、雙指、複製貼上仍未做;該 PR 的 full CDP 曾止於 P76 逾時 | 右鍵選單、側接表單、觸控長按、準星偏移未驗 |
| #61 | [SGR-04] 正式來源工作區細分編輯 | 網格/子網格 | OPEN。slice1(#133)已合入:兩軸無相位差 REPEAT 的 all-cells/單 cell CRUD、預覽/確認/取消、ZIP 保存。**未做**(#134 草稿中):子線顯示/選線、RuleLineRef、guide/direct、跨面繼承完整流程;SR24 實體手機未驗 | 子線不顯示;選格/選線;跨面繼承;面內手動子格 vs 來源規則;抽樣 |
| #57–#60、#62 | SGR 總單、00–03、05 驗收 | 網格/子網格 | OPEN。#58(固定契約/容量)、#59(REPEAT 核心 #107)、#60(保存 #126)部分切片已合入;整合驗收 #62 未做 | ruleKey、selector、複合 lineRef、容量、未知能力拒絕 |
| #43–#49 | F0–F6 新功能路線(來源追溯/A-B 候選/料單/證據/規則試驗台) | 非 9 類主流程 | OPEN。#44(#99/#113)、#45(#104/#111)、#46(#110)、#47(#96/#65)、#48(#106/#132)、#49(#101/#105)均部分合入;不屬本次驗收主軸 | EvidenceLink、A/B 快照、料單 |
| #85 | 恢復 mutation inventory/freshness | 工程 | OPEN,PR #98 已合入;issue 未關(收尾驗證) | mutation freshness |
| #24、#25、#19 | 組構規則 AR-05/06/00 | 非主流程 | OPEN。#24 僅剩 A24(實體 iOS/OS 檔案對話框)未驗 | A24 |
| **#128** | [完成面][面材鋪滿] | 新功能(未來) | OPEN,**僅決策文件(#129 open)+ issue;尚無產品碼**。被測版本沒有「完成面/面材鋪滿」 | 完成面、鋪面材、交丁、承接 8mm |

## 4. #54 的範圍與現況(只讀)

- 建立:2026-10-03,label=enhancement,狀態 OPEN,最後更新 2026-10-03T21:17Z;**無 GitHub 留言**;內容由使用者需求 + 「Agent 開發任務補充」+ 「後續規格與 20:54 品質狀態」區塊(由 doc worker 回填)組成。
- 範圍:校準底圖後「點選/框選房間 → 取得室內淨輪廓候選(PDF 向量優先,影像本地輔助)→ 修正/尺寸核對 → 確認走核心驗證與 I8a → 保存重開接續投影/空間建模」。不含:多房間(→#87/#77)、全屋還原、斜牆/弧牆、自動改公理。
- 完成狀態:A(完成狀態不再因任意頂點誤勾)/B(向量+影像候選)/C(修正、確認、保存 /9)已由 PR #63 合入 main(c87be115,在 d6b4b45)。PR 文件 CI:程式版 4bb30b9 七組全綠(含 CDP 1776);**最後文件 commit CI 因 GitHub 帳戶付款/支出上限未啟動**。
- 後續/追加修復也已合入:#72(校準後入口、「選房間/描外環」)、#74(人工描繪端點吸附)、#76(phantom targets)、GEO-242 效能(Worker 取消/重取)。
- **仍開放的已知缺口(測驗收時預期可能遇到,先對照勿當新發現)**:
  1. 私人實圖 REAL-PDF-01/CaseA:預設 vector/image edge-open、width0.1 tooManySegments 失敗(歷史,geometry 不變、0 exceptions);新 head 的 snap/人工分區/整屋重跑**未驗**;REAL-PDF-02/CaseB 各階段**未驗**。
  2. 同頁多房候選(#87)未實作;同 PDF 連續多房(#77)只有 foundation/WIP 接線。
  3. BACKLOG GEO-242 記:**空白鍵平移在房間取點/候選狀態被 `RoomOutlineWorkspace.move()/feMove()` 攔截**(尚未修,需補反例);辨識中空草稿的輸入互斥待驗。
  4. 驗收方向 checkbox 全部未勾(issue body)。
- 結論:#54 有人處理且主體已合入;我們不接管。驗收時對 #54 範圍內症狀,先比對本節與 #87/#77。

## 5. 9 類流程對照(PR/issue/條目,含症狀關鍵字)

### 5.1 匯入 PDF
- PR #63、#74、#76、#66(runtime 靜態資產)、#55;issue #54(部分)、#79(closed:匯入附件引用須以 native 候選最終物件核對)、#117(closed)。
- BACKLOG:GEO-198(來源保存/校準/人工描面)、GEO-242 吸附。
- 關鍵字:匯入失敗、頁面旋轉/裁切、官方 Library 檔案下載失敗、phantom target、annotation、錯位吸附、PDF.js 6.3.289、Worker、tooManySegments。
- 已知未驗:私人 PDF 實測(見第 4 節);實體 iOS 檔案選擇器(A24/SR24)。

### 5.2 比例尺(校準)
- PR #72(校準後入口/取景)、#74(格距顯示)、#63;issue #54。
- 關鍵字:兩點校準 323.5cm、校準只放大底圖不縮放既有外環、房間落在外環外/視野外、重新校準使舊候選失效/要求重新核對、9% 縮放顯示 50mm 實 500mm。
- 已知設計:重新校準不縮放正式面(by design,issue #54)。

### 5.3 描房間輪廓
- PR #63、#72、#74、#76、#120、#121、#125(#116 面內選單);issue #54、#87(未實作)、#116、#117(closed)。
- BACKLOG:GEO-244(方向修正)、GEO-242(性能、空白鍵平移待修)、#116 條。
- 關鍵字:edge-open、候選替換外環、逐邊核對、凹口、L 形、方向顛倒(左下→左上)、空白鍵平移失效、右鍵選單、cursor v2。
- 已知未驗:P79 旋轉 oracle 已獨立化(#120);PR #125 的 full CDP 曾止於 P76(其後 #127 修 token race)。

### 5.4 建空間
- PR #124(#119 牆容量)、#121(方向/啟動)、#127(參數 token)、#113/#99(模型更新)、#53(組構生成);issue #119(open)、#117(closed)、#78(closed:組構確認預覽漏外部角材依賴)。
- BACKLOG:GEO-243(預覽元件/WSL adapter)、GEO-244、GEO-205/206/207/208/210。
- 關鍵字:「預覽回應缺少空間或摘要」(UNSUPPORTED / BASE_COMPILER / I32)、I33/SPACE_CAPACITY、walls:null、牆厚 100、體積 37.285476 m³、俯視方向、牆高 3000、底高 0、十邊容量 16/16/64。
- 已知未驗:十邊案例 `.gcanvas` 保存重開(#119)、Windows 本機 SAC/ctime 阻擋 `run_all.py` 整體(GEO-243)。

### 5.5 多房間
- PR #102、#114;issue #77(open)、#87(open,未實作)。
- 關鍵字:共享校準、basisRevision、needs-reassociation、unlink 不刪 geometry、新增不覆蓋舊房、Q37、source-rooms/1,/2、`source-room-history/1`、同 ID 重建、room metadata 與 native 同步 undo。
- 已知:同 PDF 共用 sourceId 但**每頁仍 calibration:null**(issue #77 提到的「實際現況」為 9ebf52a 時;PR #114 合入後是否已共享,**以 #77 最新留言為準,正式入口接線未判定**)。

### 5.6 網格/子網格/參數
- PR #27、#28、#31、#32(試擺)、#107、#126、#127、#130、#133;issue #61(open)、#57–#62、#128(未來)。
- BACKLOG:GEO-204(局部子網格)、GEO-214–216(無限網格)、GEO-223/224/227/229(參數/交丁)、ISSUE-45(raw 草稿)、#61 slice1。
- 關鍵字:一面一格、stagger/交丁相位差、signed i/j、sub-line、ruleKey、REPEAT、60×40 U3/V2、RuleLineRef、「子線不顯示」(#134 未合)、參數 confirm TOKEN、raw form 草稿續編。
- 決策佇列未採納:Q31–Q37(整包 proposal 未採納,八項已拍板);#128 PANEL-FILL Q38–Q47 已拍板但無產品碼。

### 5.7 取消/撤銷/重做
- PR #73(busy)、#127(token)、#111、#104(單步 undo)、#133;issue #54 驗收項、#77 gate 4(snapshot 與 undo/redo)。
- 關鍵字:undo 在 repaint 前被判閒置、候選確認後 Ctrl+Z/Y、取消保留原 dump、單一 history group、遲到回覆。

### 5.8 保存 .gcanvas 與重開
- PR #55、#66、#111、#126、#132、#133、#63(/9)、#114(來源歷史);issue #119(十邊保存重開未驗)、#77(registry 往返 gate)、#60。
- 關鍵字:format /8 /9 /13、featureAttachments、`source-rooms/2`、舊讀取器拒絕、未知 envelope、raw draft 隨 ZIP、保存重開 PDF 底圖仍顯示(GEO-244 提醒需使用者手動載回)、capability 缺少。
- 已知未驗:Edge 擴充無本機檔案存取,GEO-244 的最後一次瀏覽器恢復使用者未回覆確認。

### 5.9 窄螢幕(390px 等)
- PR #131(feedback launcher 擋 Create 選單)、#134(draft:390px 溢出修復)、#125(桌面/手機旋轉)、#130;issue #123(open,S0–S6 未做,900/390px 待實測)、#116(觸控長按未驗)。
- 關鍵字:fbButton z-index 90 蓋 Create 選單、drawer left:12px、390px 溢出、44px 觸控熱區、真 iOS 鍵盤/IME/chooser/下載(A24/SR24 永遠標未驗)。
- 提醒:390px 通過不得替代實體 iOS。

## 6. BACKLOG.md / 決策佇列.md / RISKS.md 未完成/已知缺陷條目(僅與上述流程相關)

BACKLOG.md(條號 + 一句話):
- #77 saved-cloud owner 接續(2026-10-04 WIP):native candidate 指紋與 legacy records 無損遷移仍待 owner 協調;draft 不代表 #77 完成。
- ISSUE-77(接線驗證中):需真 owner/browser 明選、ZIP/fresh-context 全等、一步 undo/redo、basis-change、stale/cancel/未知回執;native 候選指紋待獨立 owner,同版 consumer 與 full gates 前保持 draft。
- GEO-242(底圖畫布性能):空白鍵平移被 `RoomOutlineWorkspace.move()/feMove()` 攔截,尚未修需補反例;辨識中空草稿輸入互斥待驗。
- GEO-242(PDF 人工描繪吸附):不宣稱牆角/內緣辨識;文字/曲線/虛線/裁切/影像不提供特徵(設計限制)。
- GEO-243(預覽元件):完整 `run_all.py --build --update-expected` 受 Windows `Path.stat()/os.fstat()` ctime 阻擋,census 更新待完成;測試組不含 timber-material/timber-source-guards。
- GEO-244(方向修正):`cdp_test.js` 全量跑至 P73 為 1407 通過/1 失敗(參考線「已知邊一半」斷言)且未完成、未比對 golden;隔離 FIX_ONLY 的 P73 65 項通過,**長流程時序原因未判定**。
- #116 條:full `cdp_test.js` 止於 P76(參數 engineering-confirm 拒絕 token),後 PR #127 修;再同步 main 417f4c0 後又止於 P73 引用線(原因待定),未宣稱越過 P76;實體裝置 gate 未驗。
- #61 第一正式來源規則 UI 切片(PR133 合入):未宣稱完成已確認子線 display/pick、RuleLineRef、guide/direct、跨面完整流程;SR24 實體手機待驗。
- ISSUE-45:真 desktop/390px、完整 ZIP 重開、未知結果 receipt recovery 證據須真瀏覽器;A24 IME/chooser/下載未驗。
- ISSUE-44:空間/投影/牆高專用瀏覽器回歸另外執行,A24 界線保持。
- CONT-20261003/CONT-20261004:Q31–Q37 整包 proposal 未採納;實體 iOS A24/SR24 未驗。
- GEO-225:GDI 在 Windows 受 SAC 阻擋,保留「進行中」。
- Issue #54 條(PR #63):最後文件 commit CI 因帳戶支出上限未啟動;真實使用者 PDF/截圖未測(官方 Library 下載失敗)。

決策佇列.md:
- 「待拍板」:Q31–Q37 整包 proposal 未採納(八項已於 2026-10-04 拍板);已拍板區另有 AR06、CONT-8。
- 2026-10-05 PANEL-FILL / STRUCT-FROM-FINISH(Q38–Q47)見 #128/#129:僅決策,**#129 尚未合入 main**(被測版本的 決策佇列.md 看不到)。

RISKS.md:
- 檔頭自述「已過時(2026-09-17 審查)」,為舊 C 核心風險清單(座標混用 D1–D6 等),**不是現行風險清單,不用於本次驗收**。

## 7. 使用者回報收件匣

`python D:/geometry-axiom/geometry-web/feedback_cli.py list` → 輸出:`(沒有未處理的回報)`。無相關未結回報(未改任何狀態)。

## 8. 驗收時的比對建議

1. 新發現若符合「第 5 節關鍵字」→ 先查是否為:#54 已列缺口(第 4 節)、GEO-242 空白鍵平移、#119 十邊/牆容量、#77 五個 gates、#123 UI 統整、#87 未實作功能(同頁多房候選)、#61 子線顯示(#134 未合)。
2. 以下屬「by design / 刻意限制」,別當缺陷:校準不縮放既有面;候選確認會替換目前外環;不自動正交化斜牆;影像路徑為半自動不保證任意圖面;PDF 吸附不辨識牆角;牆為預設勾選,取消勾選須重新預覽(PR #124 契約)。
3. 以下「功能被測版本不存在」:同頁多候選(#87)、同 PDF 正式入口連續多房(#77 完整接線未判定)、完成面/面材鋪滿(#128)、子線顯示與 RuleLineRef(#134)。
4. 單一失敗歸因:被測版本 PR #134、#129 的內容皆不在內。


## 附:其餘相關 PR 的 merge sha(皆已 is-ancestor 驗證)
#5=e60a83e3, #6=a9ad80f1, #7=ca5d82da, #8=75f66d99, #9=61597802, #14=42cde789, #15=5e6aa3ac, #16=9abef2f0, #27=b5d0812a, #28=e7e74242, #31=5b8a7d43, #32=24e73158, #53=68c4ac13, #55=ebdb6d88, #63=c87be115, #64=d40dee0c, #66=9e252ae3, #99=170f8f56, #104=b0031a0c, #107=c0d3fbad, #111=f1b9f9df, #113=b972dafb, #126=8d134fcb, #130=ff279f2a, #132=97f0b0e0
