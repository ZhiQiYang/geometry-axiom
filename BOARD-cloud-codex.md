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
- 不改任何等待、逾時、斷言或期望數。
- **2026-10-13 17:00 更新**:#201 也改 `grid_rule_editor_test.js`,但沒有改 `ux_refinement_test.js`。所以**現在先做 `ux_refinement_test.js` 那一半**,開 draft PR。`grid_rule_editor_test.js` 那一半等 #201 合進 main 之後,在同一支分支補上。不要因為 #201 就整項停住。
- 驗證:兩個檔都要過 `node --check`;有 Chrome 就跑對應的子集。開 draft PR,註明這是測試類,依規則只需 native + canvas + grid。

**指定任務 6:#211 native 測試的堆疊用量超過 8 MiB**
- 領取分支:`fix/211-native-stack-20261013`。先讀 #211。
- 8 MiB 和 16 MiB 各跑一次 native,找出只在 8 MiB 下崩潰的案例,定位 `current_geometry.c` 的最深遞迴鏈,並量出實際堆疊深度。報告貼到 #211。
- `current_geometry.c` 是統一 CRLF,用二進位模式讀寫。
- 只有能用對照證明行為不變時才修;修了就開 draft PR,註明這是產品程式,要走合併列車跑 7 項。

**指定任務 8:「下角材模式(平釘天花,木工模板)」提案(issue #205;只寫提案,不實作)**
- 領取分支:`proposal/framing-template-20261013`,base = main。
- 產出:`geometry-core/framing-template/PROPOSAL.md` 與 draft PR。**不改 `公理層.md`、白話、正典閱讀器、決策佇列,也不動任何 🔒 行。** 這是文件類 PR,只需 native。
- 先讀:#205、#204、#203 的正文和 2026-10-13 的留言(使用者定案在留言裡)、`公理層.md` 相關條文(D6/D6a/D6b、D10a、D15、D19、I19、I21、R19,以及 PF-0 的 D41–D45、R45)。
- 行為參考:本分支 `tasks/reference/framing-mode-demo.html`。**例外:副支記號的算法以使用者 2026-10-13 的定案為準,不照 demo 的 366/367 交錯。**
- 提案必須包含:
  1. **規則清單**,每條附使用者原話與物理理由:
     - 從起鋪牆整片鋪,裁切只在對牆,不置中;縫中心 c_k = k·T + P + ⌊gap/2⌋,T = P + gap。
     - 收邊太窄就挪縫:c > D − 1.5·角材寬 時,移到 ⌊D − 1.5·角材寬⌋。
     - 主支壓長邊縫(間距 917),整支連續、不可斷開;主支線碰到獨立柱或柱邊料 = 排板衝突,並列出不衝突的起鋪角與板長方向。
     - **副支記號(2026-10-13 定案)**:取整數模數 m,從縫中心線每 m 一個記號,一格 n − 1 個;餘數全部歸最後一格(例:1832 → 366×4 + 368;1831 → 366×4 + 367);唯一的檢查是每格 ≤ 間距上限(預設 450)。n 和 m 怎麼由上限推出,要寫成公式。
     - **端面固定(2026-10-13 定案)**:端面要頂的面若是 RC(牆或柱),先沿那個邊界固定一支角材,端面去頂它;牆和柱一體適用。
     - 板端縫兩側承接都要 ≥ 8 mm。
     - 樑:骨架高度帶碰到樑時報衝突,並給出完成面要降到多少。
  2. **核心與模板的切分**:依 🔒 產品方向「核心是領域無關的幾何公理,木工是第一個模板,依賴只能單向(模板 → 核心)」。
     - 450、每片 4 支、角材 27×33、承接 8 mm 這些數字屬模板。
     - 核心需要新增的只有通用原語;若現行 D6b + D6a 已經表達得出來,要寫明「核心不需新增」,並示範怎麼表達。
  3. **條文差異草案**(只寫在提案裡,不改 SSOT):
     - I19 與 D15 移除「端面不提供固定」這句木工理由。
     - PF-0 R45(3) 改為「孔環上會被端面頂到的邊產生沿邊料候選」。使用者已於 2026-10-13 同意,原話見 #204。
     - 其他你發現的矛盾,一律列出,不自行決定。
  4. **用詞**:每個名詞都要對得到 `公理層.md` 的 D 編號定義;沒有定義的新名詞,要在提案裡先定義。
  5. **驗收案例**(具體數字):
     - demo 平面圖的 5 個房間。
     - 房深 3700 的縫 [916, 1833, 2750, 3659]。
     - 廚房改右上起鋪的主支碰柱衝突,以及不衝突的選項。
     - 一個完整格與起鋪格的副支記號位置(照新算法)。
     - 收邊挪縫的例子。
     - 「關掉柱邊料 → 端面頂 RC 被擋」的反例。
     - 每條規則各一個突變:拿掉它,對應的驗收必須失敗,而且失敗訊息指得出是哪條規則。
- 完成後留【Codex】,寫「請 Claude 對抗審查」。流程(使用者 2026-10-13 定):先經 Claude 對抗審查,通過後才實作;本任務不含實作。
- 不排 WSL;不要提 SketchUp 插件(已移到另一個專案)。

**指定任務 9:依 P-087 把 main 合進 #201(2026-10-13 17:25 Claude 指定)**
- 領取分支:`ops/claim-201-p087-20261013`,只當鎖用。實際工作推到 #201 自己的分支 `feat/k2a-drafts-collection`。
- 照 #201 上的【Claude 裁決】P-087(https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6141924062):
  - 一般 `git merge origin/main`,不 rebase、不 force push。
  - `tests/run_all.expected.json` 照三方增量相加,`node:tests-js` = 700。
  - `geometry-core/drafts-topology/PROPOSAL.md` 取 main 的版本。
- 跑 native(`ulimit -s 16384`),確認數量與 expected 相符。推送後留言,附新的完整 head 和原始輸出。
- 完成後,它就能上下一班列車。

**指定任務 10:依 P-089 修 #212 的 test_binaries 間歇失敗(2026-10-13 18:30 Claude 指定;優先)**
- 領取分支:`fix/212-binaries-ctime-test-20261013`,base = main。
- 照 #212 上的【Claude 裁決】P-089(https://github.com/ZhiQiYang/geometry-axiom/issues/212#issuecomment-6143528242)。採 A,只修測試:
  - 改寫前先等 ctime 刻度前進一格,等待有上限。
  - `_identity_signature` 只補限制說明,不改行為。
  - 原斷言與期望數都不改。
- 突變:把 ctime 從簽章拿掉,修好的測試必須每次都失敗。
- 雲端可以先跑 200 次加突變。WSL/ext4 的 200 次驗收由本機工人排;開 draft PR 時寫明「待本機 WSL/ext4 200 次」。
- 屬測試類,只需 native。

**指定任務 11:GEO-255 PF-2～PF-6 面材鋪滿的核心切片(2026-10-13 21:30 Claude 指定;一次一片,依序)**
- **2026-10-15 04:10 PF-H 解除暫停**:#227 上的 P-116(https://github.com/ZhiQiYang/geometry-axiom/pull/227#issuecomment-6177092438)更正 P-103:E1-legal 的 V 向料是 **primary**(D17 的定義推論)。請 PF-H 負責人立刻依 P-098 與 P-116 實作:真宿主建立、保存、重開、復原與讀回;移除接入後具名轉紅;#221 原生見證。實跑結果要與 P-116 列的推導逐段比對。
- 依據:BACKLOG GEO-255、issue #128、`公理層.md` 的 D41–D45、I52–I57、R41–R46(PF-0 已採納)。木工模板 #221 依賴這五片(P-094),所以這是模板的前置。
- **一片一個 PR,照順序做**(2026-10-13 23:30 依 P-098 更新):PF-2 鋪滿與顯示(#225,**2026-10-14 已合進 main `0eb447e0`**)→ **PF-H 衍生宿主最小接入**(#227;PF-2 已進 main,請把 main 合進 PF-H 分支,並把 #227 的 base 改成 main;E1 依 #227 上的 P-103 分成純演算法 oracle 與合法場景 E1-legal)→ PF-3 承接比對(#226)→ PF-6 建議角材 → PF-4 網格對齊鋪排 → PF-5 空間完成面(只剩高度、方向與樑)。領取分支是 `feat/pf2-panel-fill-20261013` 這種形式;前一片的 PR 開出後,才領下一片。
- **本輪只做原生核心與 bridge API,不新增可見的 UI 入口**:新增入口時依 GEO-219 要寫明減項,而這件事目前還沒定。UI 等之後另議。
- **必守**(GEO-255):
  - 鋪排與 PANEL_LAYOUT/D10b 共用同一套排板與縫位計算,不另寫第二套。
  - 試排是推導結果,不進角材料單,也不影響既有角材的求值。
  - 既有場景的行為不變。
- **PF-6 另有一項必要能力**(P-094 第 3 點):R45 的確認要能放在外層交易裡,不各自提交,讓模板能把多個步驟一次提交;核心若做不到,要在 PR 裡說明。
- 驗收:PF-0 §6 的 PF01～PF24 中屬於該片的項目,逐項實跑,不准拿提案表當收據。每片都要附突變:拿掉實作必須轉紅,而且失敗訊息指得出病因。
- 這些是產品 PR,要走合併列車跑完整 7 項;雲端先跑 native(`ulimit -s 16384`)。不改 `公理層.md`;發現條文矛盾,停手回報。

**指定任務 12:「服務未在 15 秒內回應」分段量測(#209,依 ChatGPT 研究 R1;2026-10-14 15:40 Claude 指定)**
- 領取分支:`diag/209-request-wait-segments-20261014`,base = main。
- 先讀 #209 上的 R1 研究:https://github.com/ZhiQiYang/geometry-axiom/issues/209#issuecomment-6161512975 。
- **先量測,不要先修**:在 CPU 節流或人為加負載下,重現 P7 或 P52 的「服務未在 15 秒內回應」。對每一個逾時的請求,分段記錄時間:
  - 全域 RuntimeSnapshot 來源檢查鎖的等待。
  - receipt_lock 的等待。
  - bridge_lock.acquire 的等待。
  - stdin.write/flush。
  - bridge_responses.get 的等待。
  - 回覆寫回前端的時間。
  - 同時記錄前端在 `connection.phase` 變成 error 之後,有哪些請求是在 fetch 之前就被擋下的。
- 量測用的插樁只放在診斷工具或測試端,不改產品行為;原始輸出附在 PR。
- 依結果寫出「是哪一段造成逾時」,並提出修正方向:測試端有界等待、產品端縮短持鎖時間,或調整逾時。**本任務不實作修正**;修正等 Claude 依量測結果裁決。
- 開 draft PR,連到 #209。不排 WSL 全量。

**指定任務 13:serve.py 預設關閉的等待追蹤(#209,依 #235 上的 P-107;2026-10-14 17:00 Claude 指定)**
- 領取分支:`feat/209-wait-trace-20261014`,base = main。先讀 #235 的 P-107 與 #209 上的 R1 研究。
- 在 `geometry-web/serve.py` 加一個**預設關閉**、由環境變數 `GEOMETRY_WAIT_TRACE=1` 開啟的等待追蹤:
  - 每個請求記錄:全域來源檢查鎖、receipt_lock、bridge_lock 的等待時間,stdin write/flush,response queue 等待,HTTP 寫回。
  - 同時記錄當下的持鎖者是哪個命令、已經持有多久。
  - 輸出寫到測試的 feedback 目錄,一行一筆 JSON。
- 環境變數沒設時,行為與輸出必須完全不變。用測試證明這一點,並附突變:讓追蹤在沒設變數時也輸出,測試必須轉紅。
- 測試端(採納 #235 的建議):canvas harness 遇到 transport failure 時,保留**第一個**失敗的請求與時間,不讓後續的次級錯誤掩蓋先因。不改任何等待、逾時或斷言。
- 只在 WSL 列車的 canvas job 開啟這個環境變數;寫明要改哪裡(runner 或 harness),但 runner 屬共享檔案,改動要在 PR 裡單獨列出。
- 這是產品檔案的改動,要走列車跑 7 項;雲端先跑 native 與相關單元測試。開 draft PR,連到 #209。

**指定任務 14:白話文件對齊 SSOT(依 #240 的 S2～S5、S8;2026-10-15 00:00 Claude 指定)**
- **狀態(2026-10-15 04:00 Claude)**:已完成。#241 經 Claude 逐段審查(P-114),合併進 main `ea034fac`。更正:上面「依決策 M 屬文件類,只需 native」是 Claude 派工時分類錯誤;改到白話或正典閱讀器應走完整 7 項。補驗由本機第 16 班負責,雲端不需再動。
- 領取分支:`docs/plain-align-ssot-20261015`,base = main。先讀 issue #240(ChatGPT 研究 R9)的 S2、S3、S4、S5、S8。
- **只改 `geometry-guide/公理層-白話.md` 裡被點名的那幾段,讓白話照正式條文的意思寫**。`公理層.md` 是 SSOT,一個字都不改;白話不得新增條文沒有的語意,也不得刪減條文的限定。
  - S2:白話 D1 容許等分分配餘數,與 I25/I25a 的禁止相反。照 I25/I25a 改正。
  - S3:白話 I10 漏掉無限主格的明文例外。補上。
  - S4:白話 R45 把所有凹角面說成整批不能建立。改成正式規則「按明選集合驗證」的意思。
  - S5:白話 I53 推論到「板可以直接釘在樑底」,超出條文。刪掉超出的推論。
  - S8:白話檔頭的 Q38 狀態與正式檔頭不一致。照實更新。
- 任何含 🔒 的**人寫內容**(決策佇列的 🔒 行、條文與白話裡帶 🔒 的條文文字)都不得改動。正典閱讀器這種生成檔的整包 JSON 行例外:只要含 🔒 的條文物件逐字不變、而且只用同步腳本產生,整行改變沒關係(P-112)。
- 改完用 `python3 geometry-guide/sync_axiom_reader.py` 原位重產正典閱讀器,接著跑 `--check` 與原 41 題。
- PR 正文逐段列出「改前、改後、對應的正式條文與行號」。這是受保護文件的修正,由 Claude 審查後才能合併。依決策 M 屬文件類,只需 native。
- S1、S6、S7、S9 牽涉條文本身或語意解讀,**不在本任務範圍**,不要動。

**指定任務 15:PF-2 的兩個確定錯誤(依 #128 上的 ChatGPT 研究 R10;2026-10-15 01:00 Claude 指定)**
- **狀態(2026-10-15 04:00 Claude)**:已交付 #242,Claude 對抗審查通過(P-115)。合併 main 與正式 7 項由本機第 16 班負責;除非列車回報 #242 獨有的紅燈,雲端不需再動這一題,可以去領下一個任務。
- 領取分支:`fix/pf2-r10-e1-e2-20261015`,base = main。先讀 R10:https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6172907846 。
- **E1(中)**:合法的整數厚度,因為字串緩衝區大小不一致,被誤報成 INVALID/I52。
  - 先寫一個會紅的測試,重現 R10 指出的那組輸入。
  - 再修:讓兩處用同一個上限,或依 I52 的「正整數 mm」直接判斷,不要讓較小緩衝區的限制被當成幾何非法。
  - 突變:拿掉修正,測試必須轉紅,而且失敗訊息指得出是 I52 誤報。
- **E2(低)**:兩處過時的 transport/診斷說明,照目前的切片更新。
- R10 的 P1～P5 是風險,不在本任務範圍;在 PR 正文列出,之後另議。
- 這是產品程式的改動,要走列車跑 7 項;雲端先跑 native。開 draft PR,連到 #128。

**指定任務 16:已撤回(2026-10-15 03:15)**。使用者要求由 Claude 直接熱修並插隊處理,分支 `fix/start-ps1-runtime-dir-20261015` 由 Claude 使用,**請勿領取**。

**指定任務 18:網格系統直接引用整張參數卡,寫公理差異提案(#249,GEO-262;2026-10-15 05:35 Claude 指定)**
- 領取分支:`proposal/card-level-reference-20261015`,base = main。**只寫提案,不改 `公理層.md`、白話、正典閱讀器或任何產品程式。**
- 依據:issue #249 全文。使用者 2026-10-15 選擇「整張卡當引用單位」(🔒),這要改 D29、D31 等公理,所以先交提案。
- 產出:`geometry-core/card-reference/PROPOSAL.md`。格式比照 `geometry-core/PANEL-FILL-AXIOM-DIFF.md`。
  - **逐條公理差異**:新增或修改的 D、I、R 原文對照,以及白話對應段落的草稿。條號先用暫定編號,寫明以採納時的空號為準。
  - **回答 #249「提案必須回答的問題」第 1～8 點**。每點先看 SSOT 既有定義能不能推出答案,推得出就寫成定義推論。推不出的,列出選項、理由與建議,並標「待使用者決定」。
  - **領域無關**:機制只能用幾何語意(一組長度對應到網格的軸),不得出現木工語意(對齊 #248)。
  - 驗收案例表:正例、反例、邊界,每例附預期結果;另附突變計畫。
  - 與既有逐欄引用並存:舊場景檔、逐欄引用照舊可用,寫明相容規則。
- 依決策 M,只改 `*.md` 屬文件類,只需 native。開 draft PR,連到 #249,留【Codex】請 Claude 對抗審查。審查通過後交使用者拍板;拍板前不得實作。

**指定任務 17:BACKLOG 帳本對齊(2026-10-05 以後;2026-10-15 05:00 Claude 指定)**
- 領取分支:`docs/backlog-align-20261015`,base = main。**只改 `BACKLOG.md`**。`決策佇列.md` 由 Claude 的 #246 處理;`公理層.md`、白話、正典閱讀器一律不動。
- 背景:10-05 以後的真實進度都寫在 PR 正文與裁決留言,BACKLOG 沒有跟上。
- 做法:
  - 用 `gh pr list --state merged --search "merged:>=2026-10-05" --limit 200 --json number,title,mergedAt,mergeCommit,body`,逐張對照 BACKLOG 的 GEO 工單狀態。
  - 帳實不符的,把狀態改成事實,並附 PR 編號、merge commit 前 8 碼與日期。只寫 PR 正文或裁決明寫的事;PR 寫「未驗」的項目照寫未驗,不得因為已合併就寫成完成。
  - 列車 PR(train/…)要展開成車上的各個 PR,分別記到對應工單。
- 今天的裁決要一併記上:
  - GEO-253:K3-L 的必要驗收新增兩項,依 P-117(https://github.com/ZhiQiYang/geometry-axiom/pull/193#issuecomment-6177187407)。一是同鍵重建配新記號;二是沿用舊記號的突變必須轉紅。
  - GEO-258:
    - 第一個反例 `[delete 0, import P]` 仍是缺陷,#193 的阻擋 B1 待修(P-117)。
    - 第二個反例 `[delete 2, put{id:2}]` 依 P-111/D60 改為合法。
  - GEO-255:
    - PF-2 已隨第 10 班合併(`0eb447e0`)。
    - PF-2 的 E1/E2 修正 #242 已審過,待第 16 班。
    - PF-H(#227)依 P-116 解除暫停。
  - GEO-257:已隨第 14 班 #243 合併(`5cf7efd1`)。
  - #240 的 S1、S6、S7、S9 待使用者決定;S2–S5、S8 已由 #241 對齊(`ea034fac`)。
- **🔒 行一個字都不能改**:含 🔒 的行只能在它下面加註記。交付前用 diff 證明 🔒 行零刪改。
- 驗收:
  - 依決策 M,只改 `*.md` 屬文件類,只需 native。
  - 但同步腳本會讀 BACKLOG 的 GEO-120(🔒),所以**另外**要跑 `python3 geometry-guide/sync_axiom_reader.py --check` 與 `python3 tests/test_axiom_reader.py`(原 41 題)。
  - 開 draft PR,逐張列出改了哪張工單、依據哪個 PR 或留言,由 Claude 審查後合併。

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

## ★ 平行工作窗口(2026-10-15 晚,使用者電腦關機期間)

**背景**:使用者電腦關機,本機 WSL 裁判與本機派工代理人都停了。Codex 額度約在 15:40(台北)重置。重置後由 dot 開多個雲端任務**並行**,每個任務只做下面一項「指定任務」。使用者明示:不計 token 消耗,以效率為先。

**這段期間大家都要守的規則**(加在 AGENTS.md 與本看板既有規則之上):
- 只開 draft PR、只推自己的分支。不 ready、不 merge、不 close,不 force push,不改 repo 設定,不刪分支。
- 雲端跑的 native 只是參考,PR 留言寫明「雲端 native,非正式 WSL 收據」。正式 7 項等使用者開機後,由本機列車跑。
- **只改自己任務的檔案範圍**。動到別的任務範圍的檔案,先停手並在 PR 留言說明。`tests/run_all.expected.json`、`tests/mutants_results.json` 允許衝突,列車整合時逐 suite 合成,不要為了避免衝突而少更新。
- `公理層.md`、白話、正典閱讀器、`決策佇列.md` **只有任務 19 可以改**。其他任務發現條文矛盾,停手回報,不改條文。
- 不得降低 expected、不得放寬斷言、不得新增 skip。每個新規則都要有「拿掉實作就轉紅、訊息指得出病因」的突變。
- `current_geometry.c` 是 CRLF,用二進位方式讀寫;root `.gitignore` 是允許清單。
- 留言開頭用【Codex】;commit 訊息用英文,不加 AI 署名。做完留「【Codex】請 Claude 核對」,不要自己宣告驗收通過。

**指定任務 19:GEO-262 卡片級引用寫入公理層(使用者 🔒 採納)**
- 依據:#250 的 P-131(https://github.com/ZhiQiYang/geometry-axiom/pull/250#issuecomment-6185047490),逐項照做。
- 分支 `axiom/adopt-card-reference-20261015`,base main。
- 範圍:`公理層.md`、`geometry-guide/公理層-白話.md`、正典閱讀器(只用同步腳本)、`決策佇列.md`,以及 AXIOM 版本常數與其測試。
- 必附機械證明:寫入文字除條號(D64/I74/R60)外,與 #250 `f3f99a29` 的 PROPOSAL 逐字相同;其他條文與 🔒 行零改動。

**指定任務 19b:#256 的提交 B——AXIOM 版本常數與舊版相容(2026-10-15 22:45 Claude 指定)**
- 分支 `axiom/adopt-card-reference-claude-20261015`(#256)。在 Claude 的提交 A `b3c79615` **之後**加提交,不改提交 A 的任何檔案。
- 公理層的雜湊變了,要比照 Q38j 採納提交 `57996428`,以及既有夾具 `tests/fixtures/model-package-main-d1db88ae-profile.json` 和它的 provenance:
  1. `geometry-core/modeling/__init__.py`:`AXIOM_SHA256` 改成新 `公理層.md` 的 LF 雜湊。`AXIOM_REVISION` 依前例處理,並寫明理由。新增 `PRE_CARD_REFERENCE_AXIOM_VERSIONS = {("651c661b2c4c224c58bb4a2ed0a42ed929a16aa6", "ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004")}`,加入 `verify_package` 的 7 處相容判斷,並附註解。
  2. 用目前 main(`839063b9`)未修改的 `build_package` 產生一份凍結的舊版交換包夾具,附 provenance:產生者 head、axiom 版本、夾具 SHA。不得改寫 manifest 或幾何。
  3. 在 `tests/test_engineering_model_compatibility.py` 新增測試,比照 `test_released_k3_profile_package_reopens_and_rebuilds_geometry`:舊包可重開;重建結果只有兩個版本欄位改變;未知版本與混搭版本都拒絕。
  4. 突變:拿掉新的相容表,該測試轉紅,錯誤碼為 `AXIOM_VERSION`。
  5. 更新 `tests/run_all.expected.json`(只改該 suite 的數量)。
- 驗收:雲端完整 native,留言寫明「雲端 native,非正式 WSL 收據」;`--check` 與原 41 題維持綠。正式 7 項由本機列車跑。
- 只改上面列的檔案;`公理層.md`、白話、正典、決策佇列一個字都不准動。

**指定任務 20:GEO-262 核心實作(切片 A:核心+存檔+bridge,不含介面)**
- 依據:#250 `f3f99a29` 的 `geometry-core/card-reference/PROPOSAL.md`(使用者已採納),以及 #193 上的 P-121、P-122、P-129。
- 分支 `feat/card-reference-core-20261015`,**疊在 #193 的分支最新 head 上**。卡片級引用的刪除保護要沿用 #193 的守門,PR 的 base 設成 #193 的分支,並在正文寫明相依。
- 內容:
  - 網格卡片引用的資料、交易(建立、換卡、對調、解除成逐欄、解除成直接值)、求值順序、I74 驗證。
  - I38 的使用處列舉:卡片引用要被 #193 的守門看見。
  - I8a 預覽、存檔與讀檔、能力宣告 `grid-card-reference/1`、D25 交換包閉包、bridge JSON API。
- 驗收:
  - PROPOSAL §6 的 CR 案例逐一寫成具名測試並實跑。
  - §7 的突變逐一真的執行:拿掉對應實作就轉紅,而且訊息指得出病因。
  - 官方突變帳本重產並跑 `--check`;雲端完整 native。
- 若 CR29 的前提不成立(D25 匯出時角材的依賴閉包沒有含到 D29、D30),停手回報,不自行擴大閉包。

**指定任務 21:#227 PF-H 收尾(C2 繼續)**
- 照 P-126 已重產正典;補完整雲端 native 與證據,回覆所有審查項。不擴大範圍。

**指定任務 22:PF-3 有效板縫與承接比對(#226)**
- 分支沿用 #226;**改疊在 #227 的最新 head 上**(PF-H 已接近完成)。PR base 設成 #227 的分支。
- 依據:PF-0 已採納條文 R42、R43,BACKLOG GEO-255,#226 既有基準與 P-098。研究工人在 #226 的 R17、#227 的 R15 只當參考,不當規格。
- 必須重用 PF-2/PF-H 已有的排板與縫位計算,不另寫一套(GEO-255)。
- 驗收:PF-0 §6 中屬於 PF-3 的 PF 案例,以及 PF23/PF24 的分段結果,全部逐項實跑;附突變。

**指定任務 23:把下角材幾何 oracle 接進 native 測試(#251)**
- 分支 `test/framing-oracle-suite-20261015`,**疊在 #251 的分支上**。
- 只把 `geometry-core/framing-template/oracle/selftest.py` 接成 `tests/run_all.py` 裡一個具名的 native suite,並更新 expected。**不改 oracle 的任何計算邏輯**:那是 Claude 的推演,有疑問就留言回報。
- 驗收:新 suite 綠;把 oracle 的任一檢查改壞,這個 suite 必須轉紅。

**指定任務 24:審查 #237 的新 head `879ceee4`(只讀)**
- 照 #237 上的審查 B1(6178679029:缺少計數欄位時不得預設成功),以及 P-119、P-128,做對抗審查。
- 留言用【Codex 審查】,分「阻擋/須改/記錄」三節,每項附「檔案:行號」與反例。不改程式。

**加開任務(2026-10-15 22:10 Claude;使用者要求多用 Codex 額度加速)**:
瓶頸是本機 WSL 一次只能跑一班列車,以及 Claude 的核對。所以下面四件,一類用來減輕這兩個瓶頸,另一類與現有任務檔案不重疊。規則同本節開頭。

**指定任務 25:雲端預跑 7 項(advisory),讓列車少紅**
- 先確認雲端環境能不能跑瀏覽器 job:安裝 Chrome/Chromium 與 Node,照 `.github/workflows/integration-tests.yml` 的步驟跑一個 job。**跑不起來就停手**,在 #252 回報卡在哪一步,不要硬湊。
- 跑得起來時,對下列 head 依序跑完整 7 項,結果貼在各自的 PR,標明「雲端預跑,非正式 WSL 收據」:
  - #227 `303fec02` 與 #237 `879ceee4` 的合併樹(第 17 班候選)。
  - #242 `10a7fae4` 合到當下 main 的樹。
  - #256 最新 head(19b 完成後)。
- 每個 job 寫明 exit、通過/失敗/略過數、耗時、失敗斷言原文。只讀,不改任何程式。

**指定任務 26:把下角材 oracle 的結果交給核心驗收(只做探針,不改核心)**
- 依據:#251 最新 head 的 `geometry-core/framing-template/oracle/`,以及 `oracle-golden.json`。
- 把 F1–F5 每個「可施工」排法的角材,轉成核心的場景 DSL:承載面、網格或參考線,以及 D7 角材的 place,角色依 oracle 的種類對應。用原生核心逐支載入。
- 產出一張表:每支角材核心接受或拒絕;被拒的寫條號與訊息。目的是在下角材模板實作前,先找出「物理上合理、但核心規則不接受」的地方,例如柱邊角材的角色與 I19/I21。
- 只新增 `geometry-core/framing-template/core-probe/` 下的檔案。發現核心規則與 oracle 衝突,只回報,不改條文,也不改 oracle。

**指定任務 27:PF-6 建議角材(R45)可放在外層交易內(GEO-255)**
- 分支疊在 #227 最新 head 上,與 PF-3(#226)平行。
- 依據:PF-0 已採納的 R45、BACKLOG GEO-255、P-094 第 3 點:R45 的確認要能放在外層交易裡,不各自提交,讓模板能把多個步驟一次提交。
- 盡量只改 R45 相關檔案;與 PF-3 重疊的檔案,在 PR 列出,列車整合時處理。
- 驗收:PF-0 §6 中屬於 PF-6 的 PF 案例逐項實跑;附突變。

**指定任務 28:GEO-262 介面切片(等 #253 的 bridge API 出來才開工)**
- 開工條件:#253 已交付卡片引用的 bridge API,並寫明 JSON 介面。dot 看到 #253 的交付留言提到 bridge 完成,才派這件。
- 範圍:網格編輯器的「引用整張參數卡」入口、u/v 對調、整組解除(轉逐欄、轉直接值)、預覽顯示新舊來源。照 PROPOSAL §5.2 與 R60。
- 依 GEO-219,新入口要寫明減項;不得改核心。

**做完之後**:在自己的 PR 留言,寫明交付 head、做了什麼、雲端驗證結果、還沒驗的部分,然後停止。dot 會依序派下一件工作。

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
