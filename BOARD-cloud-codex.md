# 雲端 Codex 任務看板(由 Claude 維護;你只讀,不要修改本分支)

你是 geometry-axiom(repo ZhiQiYang/geometry-axiom)的實作 agent。每次被叫醒,照下列順序**一件接一件做下去**:做完一件就回到步驟 A 重新判斷,直到步驟 A 沒有待處理意見、步驟 B 也沒有可領的任務,或你的單次工作時間用完為止。全程繁體中文;commit 訊息英文;不要加 Claude 署名。

## ★ 目前階段:先讓 PR 落地(2026-10-11 23:10 起,優先於下方步驟)
- **步驟 B 暫停:不要領任何新任務。**
- 手上已經開始的任務,做到開出 draft PR 為止,不要往下一段延伸(例如 PF 做完目前這一段就停,不接著做下一段)。
- 只做步驟 A:處理 PR 上的審查意見,讓它們達到可合併。範圍見下方「本線的 PR」(2026-10-12 04:50 起擴大到沒人在顧的 PR)。

## ★ 指定任務(2026-10-12 22:40 Claude 指定;不受「步驟 B 暫停」限制,先到先做,只要一個人做)
**定位並修 tests/test_reference_workspace_races.js「caller mutation during real hashes…」的 5 秒超時**(2026-10-13 00:30 改:P-066 已撤回,原先「bridge 冷啟動編譯」的根因是錯的)
- 分支照舊:`test/warm-bridge-before-races-20261012`(已有人領就由原領取者繼續);base = main。
- 已知:通過時 4057 ms、失敗時 5547 ms,單項時限 5000 ms。Node 子程序帶 GEOMETRY_TEST_BRIDGE,find_bridge 只檢查不編譯;log 裡的 gcc 輸出屬於下一個檔 test_room_collection.js 的 before()。詳見 #189 的 dot 留言與【Claude 裁決】撤回 P-066。
- 第一步(先做,不要先改):對同一份程式分段量測,每個 python 子程序與 bridge 呼叫各記 monotonic 時間、PID、exit、stdout、stderr,找出 4–5.5 秒花在哪裡。原始輸出附在 PR。
- 第二步:依定位結果修。可能是縮短子程序成本,或把真正的前置成本移到 before() 並放寬它的時限;不要只是把單項時限調大。只改測試,不改產品。
- 證明:同條件(可用 CPU 節流重現)修前超時、修後通過;突變(拿掉修正)要回到超時。
- 開 draft PR,留【Codex】說明。不排 WSL 全量。

**指定任務 2:issue #209 的 canvas P78 時間線定位**(2026-10-13 03:00 Claude 指定;只要一個人做)
- 領取:先確認遠端沒有分支 `test/p78-trial-abort-timeline-20261013`;沒有就建立並 push 佔位提交,base = main。
- 先定位,不要先改:在 CPU 節流下跑 canvas 的 P78「建立前矩形與角材試擺」,記錄完整時間線:grid-trial-query 請求的起迄、前端 abort 的時間點與原因、igTrial.dataset.trialState 的每次變化、server 與 bridge 的起迄。原始輸出附在 #209。
- 回答 #209 的第 1 題:請求被中止後,UI 會重試、回報錯誤,還是永遠停在非 ready?
- 依結果修:產品端(中止後可恢復)或測試端(有界等待,比照 #197)。要附修前紅、修後綠、移除修正變紅。修正開 draft PR,連到 #209。不排 WSL 全量。

**指定任務 3:SketchUp 插件「下角材」**(2026-10-13 使用者指定;只要一個人做;不受「步驟 B 暫停」限制)
- 完整規格:本分支 `tasks/SKP.md`。行為參考:`tasks/reference/framing-mode-demo.html`。
- 領取:先確認遠端沒有分支 `feat/sketchup-framing-plugin-20261013`;沒有就建立並 push 佔位提交,再照 SKP.md 做。
- 驗收照 SKP.md:插件測試、突變、SketchUp 內驗收腳本。不跑 geometry-axiom 的 7 項(P-074)。

### 指定任務 4～7(2026-10-13 13:55 Claude 指定;每項只要一個人做;不受「步驟 B 暫停」限制)
共同規則:
- 領取方式同上:先確認遠端沒有該項的「領取分支」;沒有就從 origin/main 建立,`git commit --allow-empty -m "chore: claim <任務代號>"`,push 成功才算領到,被拒就換下一項。
- 不使用本機 WSL;測試在你自己的雲端環境跑。native 一律先 `ulimit -s 16384`。
- 每 20 分鐘推送一次進度。證據是原始輸出加 exit code,不貼整包 base64。
- 不改 `公理層.md`、白話、正典閱讀器、🔒 行和 `sketchup-plugin/`。

**指定任務 4:#215 的 Linux 實測(issue #212)**
- 領取分支:`ops/claim-t1-215-linux-20261013`,只當鎖用。實際工作推到 PR #215 的分支 `fix/212-binaries-ctime-flake-20261013`。
- 照 #215 正文的工具與說明,在 Linux 跑 200 次 control 加 200 次 observed。結果和原始數據貼到 #212,寫明 ctime 刻度推測成立或不成立。
- 推測成立時,另做兩個修法草案,各附突變測試:A 只修測試;B 修 `tests/binaries.py`。PR 標題寫明「待 Claude 裁決用哪個方案」。

**指定任務 5:#209 UI 控制項失敗時的現場診斷**
- 領取分支:`test/209-control-diagnostics-20261013`。先讀 #209,以及 #208 上的 P-077 和它的補充。
- 只改失敗路徑:在 `ux_refinement_test.js` 第二分頁的 `control()`(約 :218)和 `grid_rule_editor_test.js` 的 `ctl`,失敗當下把以下資料寫進錯誤訊息:
  - 按鈕的 rect、`disabled`
  - `elementFromPoint` 命中節點 `outerHTML` 的前 200 字
  - 選單容器的 display/visibility、`#fileMenuBtn` 的展開狀態
  - 現有 `diagnostics()` 的輸出
- 不改任何等待、逾時、斷言或期望數。開工前確認沒有其他 open PR 正在改這兩個檔。
- 驗證:兩個檔都要過 `node --check`;有 Chrome 就跑對應的子集。開 draft PR,註明這是測試類,依規則只需 native + canvas + grid。

**指定任務 6:#211 native 測試的堆疊用量超過 8 MiB**
- 領取分支:`fix/211-native-stack-20261013`。先讀 #211。
- 8 MiB 和 16 MiB 各跑一次 native,找出只在 8 MiB 下崩潰的案例,定位 `current_geometry.c` 的最深遞迴鏈,並量出實際堆疊深度。報告貼到 #211。
- `current_geometry.c` 是統一 CRLF,用二進位模式讀寫。
- 只有能用對照證明行為不變時才修;修了就開 draft PR,註明這是產品程式,要走合併列車跑 7 項。

**指定任務 7:落地前的雲端預驗(advisory)**
- 領取分支:`ops/claim-t5-preverify-20261013`,只當鎖用,不開 PR。
- 依序處理 open PR:#187、#191、#199、#201、#200、#206、#192、#193、#196、#202、#207、#190、#186,已合併或已關閉的跳過。
- 每個 PR 的最新 head:先用 `git merge-tree --write-tree origin/main <head>` 檢查衝突,再跑 native。
- 結果以「【Codex】雲端預驗(advisory)」留言到該 PR,內容包含:
  - 完整 head SHA
  - 衝突有無
  - pass/fail/skip 數、失敗測試名稱、exit code、耗時
  - 環境說明(OS、gcc、python、ulimit)
- 註明「這不是正式 WSL 收據」。不寫「等 Claude 裁決」,除非 PR 獨有的失敗需要裁決。

## 步驟 A:先處理自己 PR 上的審查意見(優先)
看下表「本線的 PR」。若某個 PR 上最新的「【dot】」、「【ChatGPT 審查】」或「【Claude 裁決】」留言,晚於該 PR 上最新的「【Codex】」留言,而且其中有「阻擋」或「須改」項目,或是一則要求實作的裁決:就處理那個 PR(成立就修,測試先行+突變;不成立就附條號與證據回覆),在該 PR 留「【Codex】」逐項回覆後結束。一次只處理一個 PR。

## 步驟 B:沒有待處理意見時,領一個新任務
依「任務表」由上而下,找第一個「領取分支」**在遠端還不存在**的任務(用 `git ls-remote --heads origin <分支>` 檢查)。分支已存在 = 已有人在做,跳過。
找到後:立刻建立該分支並 push 一個提交佔位,再照該任務檔(本分支 `tasks/` 底下)完整執行,開 draft PR,在 PR 留「【Codex】」說明你領的是看板上的哪一項。
全部任務的領取分支都已存在 → 回報「看板沒有可領的任務」後結束。

## 本線的 PR(步驟 A 用)
#196(GEO-246)、任務表中各領取分支所開出的 PR,**以及沒人在顧的 PR**(2026-10-12 04:50 Claude 補充)。

「沒人在顧的 PR」指同時符合以下三條的 open PR:
1. 最新的【dot】或【ChatGPT 審查】有「阻擋」或「須改」項目。
2. 那則審查之後,已超過 2 小時沒有任何【Codex】留言,也沒有新推送。
3. 待辦的不只是「WSL 七 job」,也不是在等【Claude 裁決】。這兩種你處理不了,跳過。

接手方式:
- 挑符合條件、審查最舊的一個,先在該 PR 留「【Codex】接手處理(雲端)」,避免和別人重工,再照步驟 A 處理。
- 修改推到該 PR 的原分支;不 force push,不改寫歷史。
- 不要排 WSL 全量,七 job 由本機在落地順序裡跑。
- 目前符合的(依審查時間):#182、#187、#191、#185(要先確認 #199 的 P-058 已交付)、#186。
- 這份名單只是起點,每次都照上面三條重新判定。

## 任務表
| 項 | 任務檔 | 領取分支 | 前提 |
|---|---|---|---|
| C1 | tasks/K1.md | feat/k1a-cutting-native-20261011 | 無 |
| C2 | tasks/198.md | fix/classify-rect-outline-20261011 | 無(疊在 #196 上) |
| C3 | tasks/K2b.md | feat/k2b-zero-room-impl | 無 |
| C4 | tasks/K4.md | feat/k4-pr-b-cursor | 無(疊在 #186 上) |
| C5 | tasks/K2a.md | feat/k2a-drafts-collection | 無 |
| C6 | tasks/PF.md | feat/pf2-obstacles-20261011 | 無(疊在 #190 上;PF-2 以後依序從上一段分支切出) |

## 免裁決的小例外(2026-10-12 起)
- 為了正確性,必須超出任務檔原定的檔案或區段範圍時:改動 **≤20 行**、附理由、附測試與突變,就**直接做,不必停下來等裁決**;在 PR 正文列「範圍外改動」一節(檔案:行、理由、測試)。Claude 事後複核。
- 超過 20 行、改變既有行為、碰到公理層/閱讀器/🔒,或屬於政策選擇的,才停下標「需 Claude 裁決」。

## 共同規則
不合併、不 force push、不關 PR/issue、不改 repo 設定。PR 留言開頭「【Codex】」;「【WSL 裁判】」是 Claude 的驗證,「【dot】」與「【ChatGPT 審查】」是審查意見。不得假稱跑過 WSL。
