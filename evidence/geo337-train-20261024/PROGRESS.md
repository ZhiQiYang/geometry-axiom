# 新列車進度：draft #338（取代 #337）

## 唯一 current-state（2026-10-25；F8 的 R8 性能全綠，exact 仍紅）

固定產品／測試／架構產物 F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`。R8在獨立乾淨checkout完成原prepare/build/compare/perf/profile，execution=0/0/1/0/0，累積CLI=0/0/1/1/1，outer=1。完整36個交錯樣本一次保留，沒有重抽或選樣；四份真工具回覆包含terminal chunk2aff4e／exit1。

**原性能門檻全部通過：N16/base=0.9834192453688345≤1、N32/base=0.9007932884873169≤1、N48/base=0.7392862448969592≤1、N64/main=1.2846970752586067≤1.3。** source calls82668→364369，64/32=4.407618425509266≤4.5。N16 median fix0.1123812579899095s、base0.11427604098571464s；不剔除第二輪較慢樣本，不以O0工作反證或O1/pg時間代O2 wall。

原compare仍exit1：175scenes／350runs的程序與trace皆0，但role_priority、P8低／高凹角三個stdout差觸發 verify_linux.py:156 的 assert not failures,failures。ABC_result仍缺席、all_required=false／full_acceptance=null；前段graph／guards相同不能代後段未到audit。Q-323-ABC／Q-P189-EXACT維持待明確版本界線裁決，不刪必要I22診斷、不正規化輸出。 三差已逐expected／actual與Git來源核對，診斷補齊引入6366304eb787b2a50282e4132f45e51eb7d21290；b74固定base與F8的I22整條逐byte相同且早已要求定位邊／超出區間。已批准規格內未找到同時保舊bytes與必要診斷的產品修法。current-R8-exact-three/公開150檔原件與424/0獨審；QUESTIONS列A保留紅、B′診斷一致基準、C具名三pair政策，B′／C均未核可、未採用，性能分母與有效R8不變。

F8真正tracked `python3 tests/mutate.py --check` 已真exit1，120stale／3retired／0invalid，前後同F8 clean，所有MUTATE_*清除。外層完成0不等check0。產品暫定穩定，root接續整份123重產；完整native、六browser、P52、Q38(44)、§7、P189 full/timing、required-eight/PF3、memo、readers／RC／#314／Reading A在F8仍UNRUN。只允許原Linux Windows-GDI skip，不新增skip。

架構真正執行M=`6e50aef65513b7b38f93228919272c6d40d6c196`：三gate0/0/0、205＋18零skip、604inputs唯一references.inc變動、九guard各0/1/0／neutral2綠。F8只採用有差的report／receipt，政策937／55與scan不變。380原件／4,630,676B在architecture-6e50-complete/，本批附採用actualpeer，不把M實跑改標F8。

H定向來源S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`原14/14、零skip、work0/1/0；真memset calls0/2/0、bytes0/255168/0。完整2546members包SHA7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388已公開child E74a0，再普通合入root E815cd2e3；本批附其公開blobs獨審與合流原流，產品不變。這些focused結果不代完整native。

F8 required CI run40170221039與證據E815cd2e3 run40170692505，18原API讀皆0，各七job failure、runner_id0／steps0；annotation明示付款失敗或支出上限，Ubuntu migration notice另列。沒有變更帳戶或自行核可替代流程。本提交以後的新E未讀CI，不把E815結果移標。

本批current-R8-terminal/公開原六bindings、全部36樣本／profiles摘要、五CLI／outer完整流、真工具poll、帳本check、CI與採用／H公開原件。完整R8 inner/source preparation原件本提交已公開於full-R8-five-stage-raw/：9057members／31,362,296B，SHA2564503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0。完整inventory在tar內且PACKAGE另釘hash，111,407,792B原件逐member/hash/source roundtrip經獨審；七ELF僅hash inventory，原payload仍保留。原正式outer1／compare1不因收包0而變綠，歷史published:false/PENDING字樣保原不回填；R5／R6／R7公開原件保留原source／紅燈。native ROOT已在保留原refs／五fixtures／sparse與全部原件的條件下，普通detach切至F8並獨審通過；本批只公開轉移小RESULT／request／actualpeer，完整轉移原流仍在雲端保存待另行出版；全帳本仍未啟動，正在按實際檔案系統配置新cache／seed與資源預算。root接續全帳本、其餘正式驗收。**目前不是READY-TO-MERGE。**

### 歷史 H 合流與架構採用（正式 R8 前）

產品／測試合流來源 M=`6e50aef65513b7b38f93228919272c6d40d6c196`，子來源 S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`。四個產品／測試葉與公開 S 相同；本提交採用 M 的架構 report／receipt。採用 commit 將固定為 R8 的 F8，再獨立 checkout 執行；M 與 S 的實跑不得改標 F8。

H 修正把原每次 reference_rebuild 都做的 127,584-byte 區域清零移入 fallback，持續快取路徑不再做這段無用工作。S 原 LoadResidual 14/14、零 skip、exit0；舊13方法未改。固定／撤回／恢復 actual memset calls=0/2/0、bytes=0/255168/0，work exit0/1/0；各 phase 的 persistent、fallback、allocation-failure、ordered-graph 語意均0。精確撤回 assertion 是 persistent-reference-local-zero-work。這是 O0 focused 反證，尚不代表 O2/N16 wall 通過；子分支原件正在另行出版，不能把未出版件稱為已入庫。

M 架構三原 judge exit0/0/0，generic205／product18、零 skip；604 inputs、798 edges／0 diagnostics，唯一 input delta 是 references.inc。九既有 guard 各0/1/0、neutral2綠；937／55政策與 scan bytes 不變。完整原件、51原命令、合流原流及獨審在 architecture-6e50-complete/。本提交只採用 report／receipt 兩個實際改動的衍生檔，未改公理、裁判或架構政策。

R8 原五 stage／36交錯樣本／4 profiles 尚未執行；全123帳本、完整native、六browser、P52、Q38(44)、§7、P189、required-eight/PF3、memo、readers／RC／#314／Reading A在新來源均UNRUN。只允許原Linux Windows-GDI skip。原R7 N16/base=1.05190582882169>1與三個stdout exact差保留為歷史紅；N64/main=1.2292230778583162是舊F7綠，不移標新F8。

Q-323-ABC／Q-P189-EXACT 的診斷版本界線尚無裁決，維持原exact紅，不刪I22診斷、不正規化比較。required CI既有付款失敗或支出上限分類仍在；新M／採用commit的CI未讀，沒有正式替代接受紀錄，不變更付費或安全設定。

下一步：固定採用SHA，以原工具和門檻跑R8；性能與完整canvas獨占，其他重測最多兩個。**目前不是READY-TO-MERGE。**

### 歷史 R7 終態（F6df；不可移標 H 修正來源）

固定產品／測試／架構產物 **F=`6df0264f75e84f03adb70746b6ac3db07a9910fc`**。R7 在獨立乾淨 F checkout 於 06:36:52–06:40:10 UTC 一次完成原 prepare/build/compare/perf/profile；stage execution=0/0/1/0/0、累積 CLI=0/0/1/1/1、outer=1。完整36交錯樣本保留，沒有重抽或混入 R6；原雙鎖正常釋放。三份真正工具 poll JSON 亦保留，終態 chunk87c3e8 明確 exit1。

**N64 fix/main=1.2292230778583162≤1.3，已綠；N16 fix/base=1.05190582882169>1，仍紅。** N16 median fix0.12007854899275117s、base0.1141533259942662s，差5.925ms。N32/base0.8290229168845338、N48/base0.7499983665267913與source calls82668→364369、64/32=4.407618425509266≤4.5綠。不把 perf/profile stage exit0 冒作量化門檻全過，也不以 O1/pg 時間代 O2 wall。

原 compare 完成175 scenes／350 runs，程序／trace皆0，但 verify_linux.py:156 的 assert not failures,failures 仍真1：role_priority、P8低／高凹角三個 stdout 差。完整 graph／guards 前段相同不能代未到的後段 audit；ABC_result缺席、all_required=false、full_acceptance=null保原。Q-323-ABC／Q-P189-EXACT仍待診斷版本界線裁決，不刪I22必要診斷、不過濾或正規化 exact。

原 tracked `python3 tests/mutate.py --check` 在實際 E51e36b94 真1，120 stale／3 retired／0 invalid；E51前後clean、非evidence tree與F相同，不移標成F實跑。全123帳本尚未重產。完整native、六browser、P52、Q38(44)、§7、P189 full/timing、required-eight/PF3、memo/隔離ABC、readers/RC/#314/ReadingA在F仍UNRUN。只允許原Linux Windows-GDI skip，不新增skip、不放寬golden／斷言／時限。

F 的 required CI run40070571951 與證據 E597bce63 的 run40070806058，原18次API讀皆0；兩組各七job failure，runner_id0／steps0，原annotation為付款失敗或支出上限而未啟動。Ubuntu migration notice另列。這是環境阻擋，沒有修改付款設定或宣稱正式替代已接受；本提交以後的新E之CI未讀，不以E597的run移標。

架構實跑 M=e321026fb9bc9bc19c54b8034af6e6eaec2857f9 的三原judge0/0/0、205/18零skip、604inputs/798edges/0diagnostics，九guard各0/1/0＋neutral2。F已採四檔，只有report/receipt兩個實際差異；manifest937／55與scan bytes不變。299原件在 architecture-e321-complete/，本批附674/0採用獨審，不把M結果改標F。

K定向真實來源 S1449d430 的18＋24方法全綠、整刀calls0→16→0／正常exit0/1/0及原鄰接控制，完整3201member原包已公開child E4d3ac4bf，再一般合入root E51e36b94。這些定向結果不代本輪N16 wall或全native。

R5／R6兩輪完整原件已在 E597bce63 普通推送至 full-R5-five-stage-raw/ 與 full-R6-five-stage-raw/，附全部inventory/hash與獨審。原outer1、各自性能紅與三exact差均保原執行SHA；每輪七ELF為hash inventory，原payload仍在雲端。archive-object-store/ 同批公開永久TMP Gitobjects的原接線／讀者收據，禁止清理此store。維護原件不算產品gate。

本批 current-R7-terminal/ 公開六原binding、完整外層／五CLI流、真API poll、當前CI／帳本check、stage工具與672/0獨審。完整 R7 inner／source preparation 原件本提交已公開於 full-R7-five-stage-raw/：9128 members／31,359,550B，SHA256 8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e，獨立原件 roundtrip 50504/0。完整 RAW_INVENTORY.json 已在 tar 內，外部 PACKAGE.json 另釘其 hash；七個 ELF 為 hash inventory，原 payload 全保留。原環境、source、每個指令／退出碼／全輸出、175 scenes、36樣本、四profiles與三份真工具poll均保；完整 producer 初次準備失敗、自驗反證及後續 true0 原件另附。封包0不解除原outer1、N16紅與三exact差。收件時 published:false／peer PENDING 等歷史字樣原封不回寫，當前發布事實由本提交與實際 peer 分欄證明。永久TMP Gitstore中的原已驗blob以普通提交／push公開，沒有移動或刪除原objects。

下一步：依已收齊結果修N16額外成本；原單次N16 pg診斷只用作因果分析，不當新正式樣本。後續在新來源重跑受影響原門檻，穩定後由root整份重產帳本及完整驗收。其他獨立工作線繼續。**目前不是READY-TO-MERGE。**

### 歷史 K 合流與架構採用（正式 R7 前的狀態）

固定 R7 產品／測試／架構產物來源 **F=`6df0264f75e84f03adb70746b6ac3db07a9910fc`**。其產品／測試合流來源 **M=`e321026fb9bc9bc19c54b8034af6e6eaec2857f9`**，已一般 merge 並 push 子來源 **S=`1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`**。四個產品／測試葉與 S 完全相同；本次採用 M 實跑的衍生架構 report／receipt，採用後的可解析 SHA 才作為 R7 來源，不能把 M 或 S 的結果改標。

修正沿既有 256-entry hint 對 provider token 做乘法混合，保留完整 key／provider equality、graph 有序內容、失效／清除／fallback 與 allocation 行為。外部同場景 shadow 先確認跨 provider 碰撞；單樣本的計數不宣稱 wall 改善。原 18 方法與相關 24 方法在 S 全綠、零 skip。整刀反證 warm lookup calls 為 0→16→0、正常 exit 0/1/0；十組既有鄰接控制及 full-provider／middle-byte 對照保留。完整 child 原件已於 E4d3ac4bf 公開，並一般合入目前列車；實跑來源仍是 S144。

架構三原裁判於 M exit 0/0/0，generic205／product18、604 inputs、334 owned／270 excluded、798 edges／0 diagnostics。九組原 guard 重新 0/1/0、neutral2 綠；manifest 937／55 與 scan bytes 不變，對前份 receipt 的 input delta 僅 K source.c。四檔原件、51 原命令流與 1755/0 獨審在 architecture-e321-complete/。本次只採用兩個實際有差的衍生檔，沒有改架構裁判或公理。

R7 原五 stage／36 交錯樣本／四 profile 尚未執行。全帳本重產、完整 native、六 browser、P52、Q38(44)、§7、P189、required-eight/PF3、readers／RC／#314／Reading A 在此新來源均 UNRUN。R6 的 N64/main1.373156>1.3、N16/base1.043458>1 與三個跨版本 stdout 差仍是歷史紅燈，必須以原門檻確認是否解除；不重抽同源樣本挑綠、不刪診斷、不改 comparator。

required CI 的既有原 failure annotation 明確是付款失敗或支出上限而未啟動，沒有正式替代接受紀錄；不以較早 run 代新 head。除了原 Linux Windows-GDI skip 外，零新增允許 skip。**目前不是 READY-TO-MERGE。**

R5（原執行來源 a22df116）與 R6（原執行來源 2bbe54f1）的完整原件已於本提交公開：full-R5-five-stage-raw/ 9055 members、31,186,327B，SHA256 caaf311a748c2ce1dc4ebd754fbebc9c4d70f59a5d0938fb2e9e34e57f2dd794；full-R6-five-stage-raw/ 9062 members、31,317,807B，SHA256 a9113e5e8e3474da70ee21970a29d451a46e148a3abdde1cecded4c36631d3f1。每包附完整 inventory／summary／原命令、環境、SHA、原 stdout/stderr、36 樣本與四 profiles；各七個 ELF 只附 hash inventory，原 payload 仍保存在雲端。原 outer exit1、compare 三差、量化紅燈與 full_acceptance=null 均保留，沒有把封包成功冒作產品通過。各自獨審 50132/0、50171/0。收件時的 published:false 保原文，公開事實由本次普通證據提交另證。

archive-object-store/ 同時公開永久 TMP Git object store 的原命令／完整讀者驗證／646/0 peer；此儲存區已成 Git objects，禁止當快取刪除。兩大包以既有已驗 Git blob 納入普通提交，沒有再複製進工作目錄；其餘 maintenance 包保留硬連結前後的全部路徑、bytes、hash 與原收據，沒有刪 fixtures 或 Git objects。

下一步：在固定 F 的獨立 checkout 執行 R7；維持唯一 current-state，以下歷史矩陣不作目前通過證明。

### 歷史 R6 終態（來源 F2bbe；不可移標新 K 來源）

固定產品／測試／架構產物來源 **F=`2bbe54f19b2d19e8a816530f0c4edca950629a34`**。後續普通 evidence 合流不改來源；獨立乾淨F checkout已一次跑完R6原prepare/build/compare/perf/profile，stage execution=0/0/1/0/0、累積CLI=0/0/1/1/1、outer1，原雙鎖正常釋放。全36交錯樣本保留，未重抽、未放寬門檻。

原性能判定兩紅：**N64 fix/main=1.3731562025736295>1.3**（median fix0.6787833540s、main0.4943234810s）；**N16 fix/base=1.0434575834374764>1**。N32/base0.8823227658668896與N48/base0.7581122695004152綠；source calls82668→364369、64/32=4.407618425509266≤4.5綠。不能把stage本身exit0冒作量化門檻全綠，或以gprof秒數代原O2 wall。

原compare完成175scenes/350base-fix runs，仍在verify_linux.py:156的assert not failures,failures真1：role_priority、P8低／高凹角三個stdout差。完整有序圖／guards前段相同不能代後段audit，原ABC_result缺席、all_required_stages_completed=false、full_acceptance_passed=null保留。QUESTIONS既有診斷版本界線仍待決；不刪I22必要定位、不過濾或正規化exact。

F自身原tracked `python3 tests/mutate.py --check` 真1：123筆、120stale/3retired/0invalid，前後HEAD=F且clean；全量帳本尚未重產。完整native、六browser、P52、Q38(44)、§7兩項、P189full/timing、required-eight/PF3/native後段、memo/隔離ABC、三reader/RC兩刀/#314/ReadingA專項在F仍UNRUN。既有Linux Windows-GDI skip以外零新增允許skip，原斷言/golden/時限均保。

F required CI run40066383912與當時E12f36515 run40066703178各七job failure，runner_id0、steps0；18API原讀均0，原failure annotation為付款失敗或支出上限，Ubuntu migration notice另列。這是未啟動的環境阻擋，沒有修付款／required checks，沒有自認正式替代被接受；新純證據E不能冒用上述E12f的CI run。B3未解除。

架構三原裁判實跑M=`8d2a69421560b83c0b69f3e82db8f5e97ccc037b`真0/0/0，generic205/product18零skip；F已採四檔，937→937、604inputs/798edges/0diagnostics，九fresh guard0/1/0。實跑SHA不移標。W來源df664的36方法與整刀0/84/0、五細控制及四行反例0/1/0全包已普通合入E12f的evidence/geo343-plane-ranges-df66452e/；定向綠不能解除本輪wall雙紅。

本次current-R6-terminal公開原終態投影/六原bindings/五CLI與outer全流、當前CI/帳本原件、671/0實績/3353來源準備/704架構採用與check等獨審。完整R6 inner graph/所有命令/gprof原流及source準備原件仍在雲端待完整封包；小摘要不冒全包。R5完整9055member/31,186,327B原包已在TMP封成，尚待公開；U9091member全包已公開E586。

下一步依新profile分工：W剩餘查詢成本只準備可撤回證明，K做外部shadow觀察以量測短key衝突；不先猜新策略、不並改產品、不以同源重抽樣本取得綠。**目前非READY-TO-MERGE。**

### 歷史 W 合流與架構採用（正式 R6 前的狀態）

最新產品／測試合流來源 M=`8d2a69421560b83c0b69f3e82db8f5e97ccc037b` 已普通 push。它將 child F=`df66452e7a514032453bea93b8b18ab74d7b1457` 的5個產品／測試葉一般 merge 到前輪列車；產品與測試 bytes 完全相同，其餘差異只有 evidence。沒有改公理、決策、原門檻或容量64。既有 scratch 在排序後記錄各完整64-bit平面區間，移除重複二分搜尋，不增加堆疊或改遮擋判定。

child F 三原 suite 真0/0/0，14+15+7=36方法、零skip，354次 compile/link 均0；整刀正常0/1/0對應 plane comparisons 0→84→0，五細控制亦0/1/0。原 full-coordinate 反證曾在R1存活；原斷言保留，補第三個同平面成員後重新全綠。這四行反例另做固定／撤回／恢復真0/1/0，撤回精確 `Guard survived: indexed-plane-coordinate`。R1紅與兩項環境未跑仍保留；不能以定向綠外推正式 N64 wall。

本提交採用 M 真執行的架構四檔：三原 exit0/0/0、generic205/product18零skip、604inputs/334owned/270excluded/798edges/0diagnostics。manifest 937→937、55 strings 與 scan bytes 完全不變；相較前份b9收據，完整架構closure僅 contact_world.c 改變。九個既有guard在M重新0/1/0，withdrawn明確使用歷史U的928版manifest，不冒稱上一份937版。完整原件與獨審在 architecture-8d2a-complete/。

新的正式效能來源將固定於本次衍生report／receipt採用提交後，以可解析SHA啟動R6；目前 R6、全123帳本、完整native、六browser及P52/Q38/§7/P189/required-eight/PF3/readers/閱讀A均為新來源UNRUN。前輪R5 N64/main=1.3369644933292553>1.3、三項exact差及required CI付款／支出上限阻擋沒有被此專項解除；以下僅保留歷史實跑SHA。沒有新增skip，沒有READY-TO-MERGE。

K觀察證據已普通合入 b4639b4d；沒有改K策略。R5小終態/v5工具原件和U完整9091member原包已於586f01d公開；R5完整原流正在封存。下一步在新固定來源獨占跑原五stage，完整保存36樣本與退出碼，不挑綠重抽。

### 歷史 R5 終態（執行來源 a22df116；不移標新來源）

當前產品／架構產物來源 **R=`a22df116c7e9f6b7d074451f1c8052d59e7e4f3e`**。它已一般合入排序修正與9個Reading A架構guard；後續純證據提交不改受測來源。R5在獨立乾淨R checkout以v5收件工具執行原prepare/build/compare/perf/profile各一次，execution=0/0/1/0/0、CLI=0/0/1/1/1，outer1，雙鎖已正常釋放。**N64 fix/main=1.3369644933292553>1.3仍紅**；small-N fix/base16/32/48=0.9903333938/0.8627250817/0.7692726791均綠；source calls82668/364369比4.4076184255≤4.5綠。原36樣本全保、不重抽、不放寬門檻。

compare完成175 scenes/350 runs，仍於原verify_linux.py:156正常assert1，三個stdout差為role_priority與P8低／高凹角。原ABC_result缺席、all_required_stages_completed=false、full_acceptance_passed=null；不能把比較前段graph／guards相同冒作後段audit或完整八stage通過。新R完整native、六browser、P52/Q38/§7/P189、required-eight/PF3、reader/ReadingA與全帳本尚未跑。

R的tracked帳本check已在同非evidence tree的physical E39a執行1：123筆、120stale／3retired／0invalid，原件在current-R5-status/ledger-freshness。源碼仍需修性能，root待穩定來源整份生成，不讓子代理各自重產。架構三原裁判及四檔生成真執行於b9c9fb818f031828530994a4d66f1976da0d8138：0/0/0、205/18零skip、604inputs與九組guard反證0/1/0；R只採非執行性report／receipt。原件已公開architecture-b9-complete，不移標執行SHA。

最新CI原讀：R的run40063478544與當時E39a的run40063689734，各7個job均failure／steps=[]，annotation明載付款失敗或支出上限未啟動；另有Ubuntu label notice。沒有修改付款／required checks或取得正式替代接受，B3仍未解除；這不是產品程式執行失敗或成功。新純證據head的CI不以這兩run冒充。

v5只恢復原subprocess.run PIPE並把性能收據落盤延至原perf返回後，原judge、36樣本、timer、timeout、門檻都未改；48合成契約及兩組0/1/0、87/0peer完整公開於current-R5-status/recorder-v5-originals。R5終態／CI／check原件及671/0獨審已同批公開，但R5完整graph／gprof／所有command原件仍在雲端待完整封包。上一輪U五stage完整9091member原包（31,361,891B，SHAa276bd4f…）本次已公開於full-U-five-stage-raw，50331/0獨審；包內原published:false保收件時間，發布事實由本提交另證。沒有用U包代R5原流。

排序修正Saa16的35方法、332compile/link與整刀128→896→128／四細控制真0/1/0已完整合入evidence/geo343-monotonic-aa16e73d；實跑來源仍Saa16。下一刀由W owner針對17,741,288次plane_compare尋因，K僅做觀察儀表、不並改產品策略。原三診斷版本界線與CI限制照QUESTIONS保留。**尚未READY-TO-MERGE；所有原skip、斷言、golden、時限均未放寬。**

### 前輪 U 終態與歷史矩陣（不代表上述新來源）

目前合流產品來源固定為 **U=`ca7838e0f4950452b9befcf40899d606db9b81fa`**，供下一輪原 #323 五段驗收；之後純證據提交不改 U 產品／測試。已一般 merge 核心 edge probe 修正來源 `a543eef67b81f8d8800f32d5dc4a5641840d2943`；此提交的 HEAD 是新整合來源，但最後 union 尚未固定。子分支原 17 方法零 skip、56 次 compile/link 全 0、43 次 native 已實跑；十組語意控制及完整撤回／恢復（hash calls 21／31／21、exit 0／1／0）已通過，獨立原流審查 1427／0。第一輪 Linux 測試目錄／執行檔撞名的失敗完整保留，修測試路徑後重跑，未更動斷言或時限。詳見 `edge-probe-integration/`；完整子分支原包與 1503 members inventory 已公開於 `evidence/geo323-edge-probe-a543eef6/`（E9b41d395），本次一般 merge 合入；CAF6 原帳本 check1／120 stale／3 retired 的完整四指令與原流也封存於 `probe-evidence-and-ledger-freshness/`。

已再一般 merge #339 證據頭 `8f39025be6708bd9d58e576ed5b349b7ef628624`（含 #340）。#340 原 strict aggregate 13／13、exit0 已公開；#339 舊 F38 的 142 方法／三組反證保原 execution SHA，與新 F616 的 498 項 executable closure 全等收據已公開。合流保留核心新 17 方法、host 45、rectangle 13；這些定向結果不冒作合流後完整驗收。詳見 `faces-kernel-integration/`。

本輪再一般 merge #343 `a934a554ae58f16f124f1b264523947f170b3f0b`，只納入同 load 路徑的 contact index／穩定排序及其祖先 #341、#342；容量 512、cut-list storage 與 panel empty-row 仍留後續分支。#343 原 34 方法／64 控制、318 compile 的實跑頭為 `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`，#342 原 44 案也保原 SHA；組合後效能及 #341 整段成本審查仍待，不以既有單元結果宣稱達標。tracked 帳本保 root 原 L 版本，檢查曾因新 source.c／測試閉包得到 120 stale／3 retired，最後固定來源後由 root 整份重產。詳見 `contact-index-integration/`。

**新來源尚未通過最終帳本、架構四檔重產或整套驗收。U 原五 stage 已終態 1：compare 的三個 stdout 差異與 N64 fix/main=1.429347781620555>1.3 仍紅；完整結果見本文末新增 U 終態段落。** 架構三原裁判已於實際 HEAD `b09a34c53ccac652cf0efa3f3e9b4b18ca74d6c5` 執行 0／0／0（205／18 方法、334 sources／6 trusted／798 edges／零 diagnostics）；原 Git diff 證明該 HEAD 除 evidence 外與 U 完全相同，但不把實際 execution SHA 改寫為 U。完整指令／原流封存於 `current-U-architecture-and-ci/architecture/`。

新 required CI 原件已讀並封存：U 的 Actions run **40058889738**、證據頭 b09 的 run **40059064935**，各七個 job 為 failure，steps 都是空；原 annotation 明載付款失敗或支出上限導致工作未啟動。Ubuntu 26 runner label 遷移 notice 另外保留，不冒充失敗原因。尚未修復帳戶環境，也沒有正式替代已獲接受的證據，B3 仍未解除；f05 舊 run 只留歷史。完整原 API 指令與退出碼在 `current-U-architecture-and-ci/ci/`。 下表是上一輪固定 L 的真終態，不能移標為目前 HEAD；四個既有阻擋仍保留。其餘工作線先完成定向驗收再合流，之後由 root 一次重產帳本／架構並執行受影響正式項。


上一輪完整驗收來源 **L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`** 已一般推送。C/JS 產品沿自 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`，測試沿自 S=`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0`；L 相對生成來源 b6 只採原帳本與 evidence。後續 evidence head E 是本檔所在提交，不能冒作受測 SHA。同L正式清單的原終態已收齊；P189／#323 exact、N64性能與required CI仍紅，沒有READY-TO-MERGE。

| 正式項 | 真來源 | 原 exit／狀態 | 範圍 |
|---|---|---|---|
| tracked `mutate.py --check` | L | 0 | 22:25:16–22 UTC 原命令，完整流在 final-L-start |
| 原完整123帳本 | L | tracked／fullCLI／core-map／external-check 全0；outer0 | 23:00:25 UTC真終態；123筆／120自然execution heads皆L，114killed／5equivalent／1原允許crashed／3retired；完整原流封final-L-ledger-complete |
| 架構三原裁判 | L | 0／0／0 | generic205／product18、零skip，604輸入及index前後一致；final-L-architecture |
| 完整 native | L | r2原CLI／workflow／CI35／outer全0；r1環境1保歷史 | r2全230列，5309=5308pass+0fail+1原允許WindowsGDI skip；1819.561s<35min，Node737/737；完整原件封final-L-native-r2-complete；r1四ENOENT不改舊判 |
| canvas／assembly／documents／grid／space／timber | L | canvas0；assembly0；documents0；grid0；space0；timber0 | canvas2267原assert全0／1718.885s<35min，85 golden一致、零skip；P88=143；其餘五job各原收據已封，獨立checkout／埠／暫存、canvas獨占、原CI時限保留 |
| P52／Q38／§7兩項 | L | §7 compiled0／axiom0；Q38原0／outer0，完整原件已公開；P52 formal／verifier／driver／outer0（完整原件封final-L-performance-complete/p52） | P52 main中位218.2650215ms、fix176.218242ms，原fix≤main成立，無+5寬限；首次收件工具exit1不改產品0 |
| P-189原完整比較 | L／base3e600772；main adbaebf9 | 原CLI／driver／outer1；已跑，仍紅 | 原p189_verify.py:195的assert raw[base]==raw[fix]；126組完整stdout逐bytes相同後，第127個repo-_role_priority_mutant.scene首次不同而中止，未完成175。兩版皆reject、完整dump相同，差在I22載入診斷與stderr；原full內timing未啟動，完整原件封final-L-performance-complete/p189 |
| P-189獨立timing tail | L／main adbaebf9／base3e600772 | 原CLI／driver／outer0，完整原件封final-L-performance-complete/p189-timing | 原36samples，N16/32/48/64四receipt ratio約1.101333／0.958790／1.277641／1.371567皆≤2；此tail的dump_count=0、overall_P189_passed=false，不能將原full exit1改成綠 |
| #323 required-eight／PF3 | L | 原exit0／0，完整原件包已封 | 原676混合單位／20-19-20，未移標舊F |
| #323原timing | L；baseb74／mainadba | stage execution0／outer CLI1；N64目標false | 原36samples；N16/32/48 fix/base 0.998983／0.811880／0.806587皆≤1，N64 fix/main=1.4282954375>1.3。原CLI1含累積compare紅與數值紅 |
| #323原profile | L | stage execution0／outer CLI1；calls比門檻綠 | 原四profiles；N32 82668／N64 364369，ratio4.4076184255≤4.5。累積compare／性能紅未解除 |
| #323 whole-memo反證 | L及明示withdrawn/restored變體 | driver／outer0；withdrawn1／restored0／隔離ABC0 | 三phase execution_complete true；calls比撤回6.0538332063>4.5、恢復4.4076184255≤4.5；隔離175/350與原audit tuple相同，不代跨版本compare1或N64性能紅 |
| reader三條／RC-run兩精準刀／ReadingA mutants-only及完整quick | L | reader0／0／0；RC各0／1／0；mutants-only0／quick0 | reader unit51、原RC單方法各6assert；原quick列39850 builds／failures0、既有C11六案限制仍保；兩批outer0、r1環境1仍保 |
| #323跨版本175／350 exact | L對原b74 | prepare0／build0／compare1；同L已跑仍紅 | 原175 scenes／350 runs，三個具名stdout差；verify_linux.py:156原assert not failures,failures；來源前後L clean。原ABC_result尚未設定，未冒後續audit或性能已通過 |
| 最新B3：Actions 40043471807 required jobs | head f05e7cf | 七項failure；新run原annotation已分類帳戶／支出環境阻擋 | 同批封新run原件及source binding；未取得CI真啟動終態或正式替代接受，B3仍未解除；舊c6／40034196788只作歷史 |

允許skip沒有新增；Chrome156.0.8078.47／Node24.19.0／NotoCJK在雲端可用。RUNNING不等於通過，peer計數不計產品測試。最終L原trackedJSON保自然b6 heads；L新external帳本完成後只封E，不反覆修改trackedJSON。

b6 原全123已22:08:38 UTC真完成，生成前check1／完整CLI0／coremap0／externalcheck0，114killed／5equivalent／M20原允許crashed／3retired；1239原件與原JSON已封L的ledger-b6-complete。原4f4 ENOSPC、108筆／15未跑與CLI2原失敗保歷史。前次B3五原包47,120,357B及13865member公開於bea6f309，已獨立逐byte核對；M1現有D10b/I24/D29已採納，僅後續精確順序補文尚未literal寫入，QUESTIONS已改正。B2保守待裁決方案仍在QUESTIONS，不能自行放寬exact。

L帳本已真終態並核對ROOT/SEED初末HEAD、tree、stage、refs、clean與1362歷史raw、175保全sidecars；ROOT `/tmp/train337-323-f64d638f-source` 的reader／RC已真終態釋放，native r1、§7及canvas均已終態；同L補齊三fixture後，r2於00:38～01:09 UTC完成原完整重跑且原件／sidecar已封，獨審確認後ROOT與共用cache交還root排程。SEED `/workspace/train337-ledger-cache-L-7af8c5d8/_bridge-work/7af8c5d80d34cb4f49d01ba67deb78a3a6d725db/repo` 已由root建立六browser獨立checkout的只讀pool；SEED禁止回借mutator，原ROOT inode與它獨立。175對ELF及sidecar搬移歷史完整保留，builder自行判fingerprint，沒有搬判決。終態actual35760、身份/raw8220與package6776獨立核對只驗來源與原件，不是額外產品gate。


本輪完整原件：`final-L-performance-complete/` 的 p52／p189／p189-timing／geo323／memo 五個子目錄，保存完整原公開輸出、指令、退出碼、環境、來源及封存清單。五份 tar 共74,496,801B，分別3150／3455／261／7485／5501 members；包內原判及PACKAGE的封存時published:false不回寫，發布事實另以同提交與publisher RESULT判定。當次collector outer及獨立actual報告亦封存；peer計數不計產品測試，原ELF只省包內payload並留原址/hash，P52 IPC只存原metadata。原收件失敗仍保留。

#323的完整包含五stage；它的all_required_stages_completed=false及full_acceptance_passed=null保真，R8/PF3/native另有各原OUT。memo隔離175/350/audit全等不改跨版本compare1，P189 timing0亦不改full1。N64原1.3門檻及當次1.428295紅燈仍保留；後續源碼優化另固定可解析來源並按影響驗收，不能重抽樣改判。

後續線已取得#340新S175cee44的原selected aggregate13/13、strict count、零skip結果；#339新F616ce753及probe子分支S9430bae5來源皆另列，不移標為本L測試。各線新審查、owner與完整SHA以handoff/NEXT.md及其後PROGRESS為準；此提交只公開L原件，不合產品。

## 並行工作歷史摘要（最新來源見 handoff/NEXT.md）

- #339 歷史快照Ee9ee6d08／De1b5b171：三架構0、mutate check1（107stale／13unrun）；舊S57結果不移標。後續同F38da的142及三組反證已公開於E1d94ab77ab29952d5b73ec5b262dfd239819fe25／D71113ce739f6fe7c327b162e47e6fd7dba349824；正式11項仍3PASS／1RED／7UNRUN。最新各線來源與owner見handoff 2e7963d3的handoff/NEXT.md，不把本歷史段落當current矩陣。
- #340 noWood：13項／7phase原實跑0/1/0/1/0/1/0；source4d3a、Ed45d、D77a已推，列車完整正式項仍待。
- #341前置與#342 GEO260：各原定向驗收已封自己的SHA；#342全44為43killed／SPM24equivalent、539inputs相同，不能替代aggregate/native/browser。
- #343 contact index＋穩定排序：Scc2ea1b3原三套已收齊0／1／0（318build全0）；唯一紅是placement-order負控制仍改舊後備路徑，新快路未受損而正常PASS ordering。新Sccfaf057只修原tuple錨點；三套34methods／64controls／318build全0，tuple原單方法8controls撤回／恢復0／1／0。Ea934a554與D56ed8d00正常推，完整1499members包及獨立actual1222／693、public6181均0；whole-opt、性能／512仍未跑。舊S1ee4e830的33／56／302build全0只作歷史，容量512／性能仍未跑。
- #344連線復原：S7b45013d／V082feb06／E42790be4／Da066115b已推；原CDP三既有檢查增加非空error seed與命中確認，golden/斷言/時限不變。原VM9／6／9、0／1／0，actual365與public1585獨審0；真完整canvas三態、native/ledger/architecture仍未跑。
- #345（#214）HTTP fixture：S2199cda8／E9896410a／Dac478611已推；只將fixture serve_forever既有poll interval明設0.05，原19項及1200時限不改。source/helper靜審14／20皆0；所有正式實測與效能仍UNRUN，不占live native共用cache。

最新已讀handoff e3934fbdee70c4dbd226eb19137fb4a5ecf885d6 的#338審查為2026-10-24 00:39:37 UTC/head f05e7cf；#339為00:39:36/head e9ee6d0。#338 B1確認帳本、五browser、reader/RC、Reading A、§7已有終態；評論當時canvas與native r2尚未終態，現在canvas真0已封、native r2真0與完整原件已同批封存。B2原exact及版本／comparator裁決仍未解除。B3須對新run40043471807保存原件，不以舊c6分類代替。依最新C1，canvas／native終態後已更新正文Da26b2a18（完整SHA a26b2a18dbb0b7746726716046f9a1039365e81a），唯一矩陣綁E732；本次再公開R8/PF3完整包，該正文中的status-only是當時狀態，後續由root更新；沒有可合併結論，不等審查而繼續獨立工作。

## 本次封存

原39條已終態preflight指令、完整streams、來源/環境/175搬移/launch request封於final-L-start，排除未完成command40及live observer/RESULTS；不把初始預設exit1誤稱終態。架構原3條CLI及前後Git／604inputs完整收據封於final-L-architecture。完整舊進度在各Git歷史提交保留，以下為歷史事件，不能當現行矩陣。

## 歷史紀錄：2026-10-23 19:17 UTC

Reading A 的3條reader、7 native、14 oracle完整指令/環境/streams及629checks peer已封存推進；preparation hash失敗及peer自身兩次讀取錯誤亦保原件。這是F64既有實跑的封存，不另宣稱在evidence SHA實跑。

#323完整memo反證已回報fixed0→withdrawn1→restored0，sourcecalls比率4.407618→6.053833→4.407618；同列車175場景/350組完整stdout、stderr、orderedgraph與5guards全等。正交獨立actualpeer並封原件，歷史base三診斷紅仍原樣保留。

全帳本即將由root在可解析4f4 source啟動；先以原--check保留stale結果，再原123筆CLI全部重產。外部旁錄器只保存原完整stream，子程序600/900/300時限保持；原child與外層exit分列。323已明確釋放原checkout，不再有兩個owner移動同一HEAD。

## 2026-10-23 19:38 UTC 帳本啟動與反證封存

19:27 v3環境前置exit1，發現原scene CLI預設產生的ignored `current_geometry.svg`；原fullCLI從未開始、seed未移動。保留v3指令／原完整stdout與stderr／環境／exit及driver，收於`ledger-start-and-memo-summary/ledger-preflight-v3-original-failure.tar.gz`。v4只核Git untracked/ignored、regular XML與原main預設路徑後，將該SVG完整移入證據；其它ignored仍拒。獨立16checks／0，無產品／測試／斷言／時限修改。

19:33原123筆全CLI已真正啟動於4f4；原source與seed獨立Git、HEAD/索引/refs/所有原件hash守門通過。輸出`/tmp/train337-ledger-4f4a24d7-r2`、cache `/workspace/train337-ledger-cache-4f4a24d7`。此提交只保存開始事實，尚無全帳本結果。後續正式清單仍待ledger採用後固定final SHA。

已fetch handoff4ee272be；338尚無新審查，服務已開draft340。持續#300根因與browser低磁碟配置靜審，不空等帳本。#323完整47MB原包仍僅雲端，這次只推小交接與原件peer；不得把小摘要冒充全部原始輸出。

## 2026-10-23 20:07 UTC：終態快取回收與新交接

只回收已終止任務的2000個可重建副本（1931份原Git source、49份完整新封ELF、20份既有封ELF）。執行前逐份bytes/hash/inode/hardlink與7包full-bytes核實；原命令exit0，獨立scope78checks／0、實際結果15checks／0。原961份舊Git checkout、所有receipts、fixtures、Gitobjects、gmon、mutant/trace/withdrawn source與正在執行的ledger全部保留。磁碟可用/tmp由132059136升202870784B，workspace由138784768升169799680B；全命令、原完整streams、前置相對路徑失敗、manifest與peer封存於`terminal-cache-retirement/`。7份原bytes封包仍僅雲端，沒有宣稱已推送。

已fetch handoff d65d464f，讀到337的19:44 UTC Claude最後交接：新head8f9301fc含M151 owner-map修正及原收據，將普通merge；不改寫歷史。#314指定程式已符合題3，條文暫緩寫入決定保留；#335 CLI已知缺口另列，不自行改公理。free-end錨點的原9方法四輪已實跑1/0/1/0，18原控制及斷言保持，獨立actual peer中；只會採用這一葉測試定位修正，不摻#300優化。完整123筆ledger仍固定4f4執行，未出最終exit，不冒稱完成。

## 2026-10-23 20:10 UTC：兩個測試缺陷修正與原反證已封存

S=`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0` 已普通推送。來源一是Claude f1f2e8d0的M151 owner-map，完整15方法0/1/0，撤回只讓原完整registry字典相等斷言紅，獨立241checks／0；來源二是free-end單葉patch（SHA256 `10e30443932f047fc5bdcd9c4926c00df26f2a5d4935fb64090b16366ed91afe`），原9方法1/0/1/0，原紅唯一`AssertionError: 1 != 3`。新錨點保留跨寬判定，只撤原free-end guard；fixed/restored各18控制0/1/0，獨立1328checks／0。全原件與工具封於`test-anchor-recovery-ec8e0d7e/`，不把受控variant冒成新SHA全native。

S的原`mutate.py --check` exit1；三條原架構裁判exit0/0/0。Chrome/Node版本、全指令/原streams/環境與前後clean SHA已封。架構manifest/scan/report/receipt正按原Linux schema重產。當前4f4帳本仍執行，70個core已完成且原裁判無阻擋，53個bridge繼續；沒有最終exit。新tests會使bridge oracle hash過期，本輪舊SHA原件保為歷史，後續由root於新穩定來源完整重產，不改帳本定義或只補選定ID。

## 2026-10-23 20:19 UTC：新測試來源的Linux架構收據採用

S ec8的三原裁判0/0/0與205/18原計數已按同schema封存；604個physical/Git/raw/LF輸入及原scanner/generic/product裁判均與P17相同，closure仍`6e1a994abaddec0ee851b96184a173548ac81b54ea37f7f7725e3066c7a6f338`。新manifest/scan bytes不變，新report/receipt已採用；獨立781checks／0，完整原件封`architecture-ec8-originals/`。真受測S與封存a607分列；兩個tests葉不在604架構scope，不能以此代替測試/ledger。P17 manifest反證只保原SHA，不轉標本輪。上一段出版時間標籤修正為原20:10，受測指令收據原時間未改。

noWood原13項/7phase已真完成0/1/0/1/0/1/0，owner交獨立peer與自己分支封存；#324接第2槽跑30+13 C importers。root原4f4 fullledger仍執行中，不標最終完成。PR338新正文`c6a66707db7fac932d3b8ceb91572b7552091730`已一般推送，唯一矩陣區分F/P/S/E與所有紅/未跑項；handoff NEXT已推5461a7bb，後續持續更新。

## 2026-10-23 20:39 UTC：退休checkout副本封存、回收與後續線結果

已完整封存10個root自有退休checkout的9510個immutable原碼副本；966個不同payload共20,235,083B，6,204,042B原封包逐byte roundtrip。固定scope9533、封包10504、actual9554個獨立checks均0。精確unlink exit0，回收216,199,168配置bytes；Git/objects/index/refs、收據、fixtures、gmon、所有mutant/trace/withdrawn來源不動。完整原指令/環境/streams/退出碼/原來源SHA及可逐檔還原封包在`cold-checkout-retirement/`。這不是產品驗收。

#340原13項與7phase反證真0/1/0/1/0/1/0已推；普通merge本列車後source4d3a17c3，原實測bfbab207不轉標。#339原9模組142/142均原exit0且3組predicate0/1/0已推，普通merge#340後source1f0ebd3e、原實測57b68014分列。GEO260新focused SPM43/44於af4fd36c真baseline29 pass、各具名assert1、restore0，1252checks獨審0；原c926 KeyError仍保留。這些不冒整體native/browser。

root4f4完整帳本仍跑，20:40已100/123（92killed/4equivalent/1crashed/3retired），無最終exit；S ec8仍需完整重產。第2重槽已交#300三原suite，所有大暫存改用獨立workspace目錄；/tmp仍緊，繼續只盤點已終態可重建cache，保留全部收據。新架構四檔已在9a05採用，原0/0/0與781checks peer全封。完整native/6browser/專項尚未完成，不標READY。

## 2026-10-23 20:48 UTC：全帳本M118環境紅燈，原件保留且其餘繼續

舊4f4原full CLI尚在執行，M118於20:44:37的restored-build原exit1：`編得出來但無法啟動：[Errno 28] No space left on device: .../M118/bridge-restored/smoke`。這是儲存環境阻擋，原verdict=`blocked`，restored phase未完成；不能列killed或產品assertion反證。原row及M118全部既有streams、full-launch環境／SHA封於`ledger-4f4-m118-interim/`，沒有覆寫live ledger。其他ID繼續收齊；修好空間後新S的完整123重產自然重驗M118，原失敗不改標。

root PR338正文已一般推D e51c7abc984a9a09c2ff27cad5e6d44c42254fbf（其20:38進度早於此紅），下版將納此環境紅與真正終exit。handoff NEXT／#300 draft請求與#339 base=#340已一般推2d409187；沒有合併任何PR。#300原32項/46controls已取得原0，獨立actual審查中；其後正常merge#339並只把expected9→10，S aa0e3938已交GEO260下一棒。

## 2026-10-23 20:54 UTC：全帳本原失敗終態與完整原流出版

原108/123結果、CLI2/root1/check2、143observer commands、67core mapping與452bridge＋M118孤立兩流完整封存1272members（49,634,273B原件／8,876,183B壓縮）；original ELF與source/Git仍雲端保留，未冒封在包中。獨立2031checks只證明失敗收據完整，不把產品gate判綠。

更正上一筆interim的「其餘繼續／尚無最終exit」：當時root只讀遞增JSON、未讀已結束的outer session，原CLI實已20:44:44因下一M119的Errno28提前終止。原interim檔保留且本段明確更正；沒有自行終止工具、沒有略過15項後報通過。接著在公開b6來源重新跑全123；舊非零仍保原SHA，不能補入新帳本。

## 2026-10-23 21:04 UTC：新公開來源原完整123帳本已啟動

source=`b6e1e45425f055cd825b259f46ef2c454f3ff13a`，21:00:13 UTC，exec session72136；原完整CLI不傳ID，70core（含3retired）＋53bridge全部重新判。只同filesystem移68個core編譯cache與seed以免重複占147MB；原CLI自行判fingerprint，沒有跳測或強迫cached。68個舊sidecar另保原bytes，全部舊bridge raw與Gitobjects留原位，source/refs/index原守門已0。原16MiB／子時限／verdict與三個原裁判未改，v5獨立30checks0；準備與實際起始證據封於`ledger-b6e1e454-start/`，不把啟動當通過。

JOB `/workspace/train337-ledger-b6e1e454-v5`、CACHE `/workspace/train337-ledger-cache-b6e1e454`、TMP同job加`-tmp`、SEED在CACHE的`_bridge-work/b6e1e45425f055cd825b259f46ef2c454f3ff13a/repo`；ROOT仍`/tmp/train337-323-f64d638f-source`。其他agent禁止動這兩個HEAD/cache。另一重槽由GEO260原全44使用，固定eb846、原起始20:53:16 UTC；不以其af4舊focused結果冒全44。沒有canvas或perf同跑。

## 2026-10-23 21:21 UTC：回應最新 b6 審查與新工作線

已讀 #338 B1–B3/M1，按現行 SSOT 改正 QUESTIONS 與當前狀態，沒有修改公理、決策、產品、測試或裁判。B2 的三個 V_EXTENSION 差異來自 I22 要求的新診斷，不能直接撤回欄位或放寬 exact；保留阻擋並繼續不受影響驗收。五原包出版工具已準備，磁碟餘裕不足時先清已終態可重建 Chrome cache，不刪原件。新完整 b6 帳本仍在原程序執行；不將部分列數當最終成功。

GEO260 的完整44及獨立審查原件已推 E df230da5；request 已在 handoff b537a4e7 提交，base=#341。#341 request改base=#339。新 #320 連線成功後殘留 error 由獨立子代理從2d157069開始處理，不動live帳本來源，定向正反例先行。

## 2026-10-23 21:30 UTC：B3五包原件已推、B2根因與快取維護已封

B3原五包47,120,357B及MANIFEST已普通推送 E bea6f30995da1425ebe375a37d871e4f19c54a2d，路徑 `geo323-full-originals/`。13865members／172515281原bytes，所有5272原stdout/stderr均在包內；原F64 source不轉標，新舊失敗均保留。出版全部Git原argv/exit/streams／環境封 `review-b6-response/geo323-full-raw-publication.json`（完整commands locator仍可讀）；沒有在工作樹再複製47MB，原雲端檔不刪。

B2根因84項獨立核對已封 `b2-diagnostic-originals-and-peer.tar.gz`：三案原stdout/stderr完整差異、graph/5guards與source傳遞鏈保真；I22連歷史b74本身就要求定位邊/超出區間，舊短訊息原本欠缺，不能撤#299欄位來冒exact。QUESTIONS保留最窄待裁決方案，未實作新版comparator、未忽略或正規化字串，原ABC exit1不變。

為保帳本與出版空間，root只清19份已終態job的426個精確Chrome可重建cache葉：5678 regular/singlelink files、106860544配置bytes；71個profile父、storage/cookies、原收據/outputs/fixtures/Git/ELF/源均不在刪除範圍。原scope7449checks／0，實際39checks／0；root原exit0，21:25:03–09 UTC，workspace204382208→263221248B、tmp16064512→64204800B。觀察free差受並行寫入影響，不冒等於allocation；38個不可讀proc欄位限制保留，不冒完全掃遍所有OS程序。plan、fresh identity/hash/membership/proc、完整原命令/streams、結果與工具封 `terminal-chrome-cache-originals.tar.gz`，actual peer另列。

最新B1原碼契約已獨審14/0：check@L可驗closure但不等於fullCLI@L，因此採上一段明列的嚴格同L實跑方案。現b6仍先收齊，不中斷、不重抽；沒有任何gates被靜態peer或metadata出版取代。

B3公開核對完成：Git五blob直接stream核、13865個member逐bytes/hash全符；五包47,120,357B、172,515,281原bytes、5272原stdout/stderr，33個出版Git原命令皆0且remote=bea6。獨立27834checks／0封 `review-b6-response/geo323-public-raw-peer.json`，沒有另extract副本或改原測試退出碼。

## 2026-10-23 21:55 UTC：已終態快取回收與後續請求

精確移除四個已終態checkout的1229份普通code副本，保留Git原blob/index/HEAD、fixtures與全部收據；原exit0、actual1500checks/0。另精確移除13個原瀏覽器profile中全零BrowserMetrics-spare.pma，原exit0、actual45checks/0，profile與19份原終態receipt保留。兩批原指令/完整streams/環境/工具/scope/peer共259原件（archive另加inventory共260members）已封 `terminal-maintenance-2151/`，package777checks/0。配置回收58,408,960B與54,525,952B不等於workspace實增；第一批workspace實際少7,606,272B（新raw與並行寫入），第二批/tmp實增54,525,952B，數據照原收據。這不是產品驗收。

主帳本仍固定b6原完整123執行，未出最終exit。#300新prefix-index S1ee4e830/E2a0772da/Dc89d516b已一般推送，原33methods/56controls開始排入/tmp獨立環境，不改100MiB資源預算或產品門檻；以真正outer終態判定結果。#320 Sc1113f6f/Ed2c58317/D8233916d已推，Node原9→撤回3assert紅→恢復9綠，實際browser/native/ledger/architecture仍未跑。兩新draft請求已推handoff54d76d41，服務已開GEO260 #342；沒有合併PR。

## 2026-10-23 22:05 UTC：編譯快取回收與正式項持續

已精確退休舊4f終態的76個可重建bridge ELF cache（85,291,008配置bytes、actual318checks/0），及18個歷史browser job的54個baseline runtime ELF（53,035,008配置bytes、actual143checks/0）。兩原命令exit0；所有sidecar、source、compile原流、fixture、Gitobjects、目錄及原測試收據保留。舊4f的原CLI2/root1/108筆/15未跑仍是歷史紅，不改判；這76個binary的舊「雲端保留」描述僅代表當時狀態，此次是有重建依據的快取退休，沒有宣稱ELF bytes已封包。新47原件656,653B與完整工具／範圍／原streams封於 `terminal-elf-maintenance-2200/`（archive含inventory共48members，獨立200checks/0）。與live b6原件守門1395精確路徑無交集，活source/cache未動。

#300 新S1ee4e830三原套件已真完成33methods/56controls（皆原具名ASSERT 0/1/0、零skip）與302build exit0，獨立actual1140checks/0；完整快路撤回七正例、性能及512仍未跑。#339真M1f0ebd3e原三架構裁判0/0/0（205/18）、mutate --check1（過期），完整native與六browser仍未跑；原帳本紅交root最後整份重產，不局部填帳本。主b6全123仍執行，最終退出碼尚待真終態。

## 2026-10-23 22:18 UTC：完整123原帳本採用，固定下一輪L

b6原完整CLI與外層真exit0，123 ID完整／120個execution head自然b6；114killed、5equivalent、M20原允許crashed、3retired。M118原restore build0與43方法0，舊ENOSPC失敗仍保歷史。原四階段是生成前trackedcheck1／fullCLI0／core-map0／external-new-check0，沒有隱去1。獨立actual35,756checks/0與完整封包4,529checks/0；1239members/45,345,757B原件封於 `ledger-b6-complete/`，原core文字與bridge bytes依原schema保存，不冒不存在的OS predecode pipes。

`tests/mutants_results.json` 與b6原外部JSON逐byte相同，未改head/date/verdict或補造row。本次採用提交用作唯一下一輪驗收L；精確公開SHA由後續啟動收據與正文記錄。L的原trackedcheck、完整123CLI、完整native、六browser及專項尚待真正執行；新L外部帳本只封evidence，不反覆改L tracked ledger。產品／測試與b6相同，沒有新增skip或降低門檻。B1尚未完成、B2跨版本診斷exact仍紅，維持draft。

## 2026-10-23 22:47 UTC：閱讀A環境失敗封存與同L首項通過

r1兩原CLI都在selftest.py:1386匯入make_golden時ModuleNotFoundError，原exit1／outer1，沒有AssertionError；薄checkout漏檔是環境準備缺陷。兩完整streams/環境/初末HEAD/11inputs/索引、原準備與同L修復全收 `final-L-reading-a-environment/`（419members、20,469,890原bytes），獨立1164checks/0只證收據保真，不把環境紅當產品反證。修復只物化同L oracle全20檔＋PROPOSAL與決策共22檔，沒有改產品／golden／測試／時限；原r1閉包與失敗原件保留。

r2原 `selftest.py --mutants-only` 已22:39:25 UTC真終態0，9條原stage命令與前後clean/L/fullstreams、22input binding封 `final-L-reading-a-mutants/`；actual46checks/0。這個模式原本不做完整掃描，不能替代quick。其後原 `--quick` 仍session19147背景執行，最外兩stage總exit尚無；封包排除livequick、外層RESULT及aggregatecommands，不能宣稱兩項已綠。root全123仍session56927，沒有最終exit。

## 2026-10-23 22:59 UTC：閱讀A兩原命令完成與進度更正

r2兩stage已於22:45:53.451047 UTC真正結束，原`--mutants-only` 0、完整`--quick` 0、outer0；原22檔、HEAD、fullstage與index初末一致。原quick列39850 builds／failures0，包含矩形逐毫米9402、二維14208、579凹角×8、step410×8／mirror820×8、odd1872及額外t10mirror392；正例528／1056 missing與nonbuildable皆0。39850是原工具印出的counter，不冒所有內部build總和。原工具另列的t4六個C11_MAIN_NOT_BUTTED既有限制保持，不宣稱這六案已修復或新增豁免。

更正上一提交9083bca1於22:47仍寫quick RUNNING：該次出版依較早的狀態通知，實際命令已在22:45:53結束；此次依完整terminal receipt及exec session19147實際exit0改正。上一快照保歷史，不能將當時資訊錯置成已知結果。兩stage與outer完整流、原工具／環境／22輸入與守門共169原件、8,955,138B封入`final-L-reading-a-complete/`（含inventory170members、archive1,751,713B）。actual46／119及package349獨立核對不是額外產品gate；reviewer第一次誤讀SCOPE.md的metadata失敗亦保留。r1缺make_golden原1／1仍完整保在環境包。

最新審查新增的Actions B3另列；無runner/steps尚不足直接認定原因，已交獨立調查並繼續雲端完整驗收。root L全123尚無最終exit，reader三條／RC兩刀與其他UNRUN不借閱讀A通過補綠。

## 2026-10-23 23:07 UTC：最終L原完整123帳本完成並公開

原程序22:25:15.110046～23:00:25.504176 UTC，session56927真outer0；tracked check／原完整CLI／原core mapping／external新帳本check四phase全部0。123定義與原AST IDs精確一致，120個execution head自然為L；114killed、5equivalent、M20原允許crashed、3retired，沒有新增skip或缺項。M118原restore build與43方法皆0；舊4f磁碟紅仍保原SHA。新external JSON SHA256 `66895ec4be133bdfca13cd38733dd024d5005a39ec9fa3bd157122610a5916a6`；沒有再次覆寫L tracked JSON或移動驗收來源。

原完整指令、環境、全部原streams、636bridge rows、67core映射、ROOT/SEED身份與歷史raw守門、工具及175 sidecar搬移沿革共1354members／48,375,681原bytes封於 `final-L-ledger-complete/`；archive8,111,145B、SHA256 `351d84a2a3eb9724ffc1216c5cc5cc2a664006238f63109bd2446ac3fef18af5`。原core文字仍照原裁判UTF-8表示保存，不冒不存在的predecode OS pipes；ELF/源Git/fixtures不在原流包中。actual35760／identity8220／package6776均獨立核對0，沒有拿核對數充產品測試。

ROOT與SEED已在完整原件核對後正式釋放到下個用途，原source仍固定L。reader三條與RC兩刀正在按原工具準備／執行；尚無其終態者維持UNRUN。完整native、六browser與其他專項仍未通過，B1未解除。Actions40034196788的七個原annotation已查得GitHub帳戶付款或支出上限造成派runner前阻擋；CI仍failure，完整環境分類原件另封，不能把這件事當雲端補跑已綠。B2原exact紅仍保留。

## 2026-10-23 23:19 UTC：reader／RC終態、CI分類與下一正式項

23:06:44～23:09:25 UTC，原reader生成／check／51方法unit三CLI全0，RC builder與checker兩精準撤回各0／1／0，撤回皆原AssertionError而非環境錯。原45個c387完整指令／環境／streams、初末L/clean/index與兩實際variant封於 `final-L-readers-RC/`（253members／484,814B壓縮），actual與package755獨立核對0。六assert是原一個方法的六個斷言位置，撤回失敗在第一個命中即停止，不冒該紅phase執行完六個。最外session84069的exit0為工具API觀測，沒有捏造額外OS pipes。

Actions40034196788原14個Git／gh唯讀命令、七個job annotation與完整原流封於 `actions-40034196788-environment/`。GitHub明列付款失敗或支出上限導致job未開始，故判排程前帳戶環境阻擋，無法再細分兩者；13命令0，第一次本地gh不支援attempt欄位的1也保留。required jobs仍7/7 failure，144項獨立核對只確認分類與原件；不能將這個B3標通過。

已用原完整native工具啟session80260；六browser pool真建立且來源／Git／inode守門0，documents啟session70767占第二槽。修正先前NEXT的環境描述：原browser storage driver亦只允許/tmp；新外部driver只容browser輸出在/workspace且repository外，native仍限/tmp。所有workflow執行函式、golden、斷言、CI時限與watchdog不變；原pathguard差分35項與launcher43項獨審0。這是儲存位置的環境修正，不改L產品／測試。未終態job不標綠。

#335獨立根因與原命令／失敗／authority原件已封 `issue335-readonly-cause/`，兩種順序都無法建立互頂pair，但e2先放本身成功且先延伸成1000；不能誤稱兩順序的第一支都立即失敗。依現有核可只準備未決設計，不實作未placed支撐／硬裁auto跨距；QUESTIONS已改成精確現況。

## 2026-10-23 23:31 UTC：documents 正式通過與七批環境維護原件入庫

documents 在同L原workflow真exit0、wrapper0、47個原斷言全通過，64.316秒低於原CI10分鐘，沒有新增skip。完整原步驟／Chrome與Node版本／前後Git守門／8截圖、runtime fingerprint與輸入綁定封 `final-L-browser-documents/`，670members、5,357,450B壓縮；三ELF與82個Chrome可重建cache有排除清單，沒有刪除或冒稱封入。producer694與獨立3420個原件核對均0，checker初次CRLF及newline比法錯誤的原失敗亦保留；產品未重跑或修改。assembly亦真完成0（150assert，原P77=134/P82=16，191.692秒），完整原件正獨審；其原workflow既定partial與golden不比較不能冒完整canvas。grid已在第二槽執行，native仍原完整230列執行，無最終判決。

七批維護的原工具／範圍／指令／完整stdout與stderr／環境／退出碼／peer，1,677members與獨立8446核對0，封 `terminal-maintenance-seven-originals/`，collector最外原流另外逐檔入庫。包括三組相同原封包的hardlink去重、四及八個已終態獨立index快取、L完整帳本終態後175個可重建ELF快取退休，以及一組82,776,064配置bytes的歷史原流跨filesystem保全搬移。前六類合計439,607,296配置bytes，不能冒實際free差；搬移只是將/tmp原流完整移到/workspace，原路徑改symlink，並非整體空間釋放。所有原收據、fixtures、Gitobjects、原source/controlled variants、sidecars都保留；ELF僅保重建依據，沒有捏造binary完整封存。

三個cold checkout `p-source/a-source/l-source` 的三組既有原tar現共用inode；在三組都解除hardlink之前禁止寫入、checkout或跑測試。原bytes與路徑不變，原inode/mtime差異及限制列於原PLAN；不是crash-durability承諾。第二組raw `/tmp/g288-final-native-3d681636/subcommands` 未動。另23:30完成95個歷史seal ELF快取退休、exit0，原件正交獨審，尚未冒已封入本七批包。

## 2026-10-23 23:32 UTC：assembly 完整原job原件公開

assembly同L原workflow、outer與reaper皆0；原150斷言（P77 134＋P82 16）全通過、0skip、uncaught0，191.692秒低於原CI15分鐘。9截圖、全部原commands/streams/environment/SHA與兩個已關閉Git守門封於 `final-L-browser-assembly/`，672members／5,226,869B壓縮，producer695與獨立3431核對0。原workflow指定GEOMETRY_ASSEMBLY_ONLY，既定partial模式不比golden，不能冒完整canvas；原Injected lost success response是P77預期故障注入，不另當產品紅。80個可重建Chrome cache與3個ELF按清單排除且未刪；runtime sidecars與原compile完整保存。

## 2026-10-23 23:40 UTC：grid 原正式項通過

grid同L原workflow／outer／reaper皆0，356個原斷言全通過、0skip／uncaught0；P70=121、P71=9、P78=23、P87=60、P88=143，482.279秒低於原CI15分鐘。原4截圖、source初末L/clean、全部commands/streams/environment與runtime sidecars收於 `final-L-browser-grid/`，675members／8,569,103B壓縮；producer690、獨立3438核對均0。原grid-only partial模式不比golden，不能冒完整canvas。CDP_RESULT後339行server trace全部保留，沒有裁成錯誤或截去；80個可重建cache及3個ELF排除清單明列且未刪。space已啟session66090占第二槽，native session80260仍執行原230項，兩項尚無最終退出碼。

## 2026-10-23 23:50 UTC：完整native的環境紅燈與原件公開

原完整native已於23:42:38 UTC結束，workflow／driver／reaper／outer皆1，原CI35分鐘gate為0（1873.241秒，沒有逾時）。完整230列符合原expected names/count；5309=5304pass＋4fail＋1skip。唯一失敗suite是node:tests-js（737／733／4／0），四個原測例都在readFileSync發生ENOENT，雲端精簡checkout漏物化同L的三個既有fixture：`tests/evidence/k2a-collection-capacity-20261012/legacy6a.gcanvas`、同目錄`legacy6a-with-scene.gcanvas`及`tests/evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas`（最後一件被兩案引用）。沒有產品assertion紅的證據；唯一skip是原Windows GDI具名允許項，沒有新增skip。

四個精確失敗名稱為「B1 previous collection writer ZIP retains a full-size orphan draft on cold read and re-save」、「B1 legacy near-limit ZIP reads and re-saves without reserving new admission bytes」、「K2a B1 previous collection ZIP original import and save preserves raw refs orphan and full draft size」、「K2a B1 legacy missing-source scan preserves raw and unchanged flush; one byte edits still need admission」。完整原命令／環境／SHA／原stdout-stderr／原230逐列logs及runtime sidecars，1366members／11,241,774B原件／2,229,053B壓縮，已封 `final-L-native-r1-environment-failure/`，獨立4005核對0。原big old-cache只精確排payload且保before/preserved manifest；普通ELF僅按registry/sidecar排payload，未刪，未知與受控變體保。原工具內部未公開的pipes不捏造。collector初prune修正與peer自身兩個row-name假設錯誤原件皆保，與產品紅分開。

原r1失敗保持不變，已在修復前保三fixture真不存在、同L Git mode/blob/size與完整讀取流。接著只補同L原檔，原產品／測試／golden／斷言／時限不改，再用原完整native正式項取得新的退出碼，不把單獨四案補跑或靜態審核回填成本次native0。space及timber亦真exit0、完整原件正收及獨審；目前root原§7 compiled占ROOT，待其原finally還原後才物化fixture，避免改到活躍來源。

本次出版首次diff --check exit2只指出原`tests/binaries.py` Git stdout逐bytes副本的既有EOF空白行；完整首次8命令原流保在publication-initial-originals。原raw已再次與L真Gitblob核等，不裁空白；其它新增metadata照原diff檢查，沒有修改產品／測試斷言。

## 2026-10-24 00:06 UTC：space／timber 原正式項通過，canvas 獨占開始

space原SPACE_RESULT 242/0、八組完整，229.754秒低於原15分鐘；timber原SPACE_RESULT 79/0、五組2/48/8/19/2完整，124.236秒低於原20分鐘。原模式既定省略的互補組別沒有改動，不新增skip；timber job不冒P52呈現耗時。原workflow／outer／reaper及前後獨立pool守門皆0，完整685／660 members、各指令、退出碼、完整streams、環境、SHA與輸入／ELF排除hash明列，包及獨立3479／3383核對封於final-L-browser-space、final-L-browser-timber。peer數不是產品斷言。

完整canvas同L已於2026-10-24 00:04 UTC獨占啟動，session18785，原35分鐘與golden／斷言不改；目前無終態exit。native r1全230列原exit1環境失敗已公開，三fixture補齊後源SHA及完整index tree不變，尚未重跑，不能標綠。§7兩原CLI已真0，原件待獨審收齊另封。ROOT、SEED與六個browser source持續隔離。

## 2026-10-24 00:07 UTC：§7 兩個原完整突變 CLI 通過

同L原card-reference run_mutations.py／run_axiom_mutations.py及其driver／outer皆真0。compiled baseline43全通過，原53刀逐一正常assert1、各restore0，116compile全0；axiom baseline44全通過，原V01～V05各精準CARD_AXIOM_* AssertionError真1、各restore完整44全綠。未縮原table、斷言、golden或時限，初末HEAD／tree／index／refs／clean守門一致。完整commands／streams／環境／SHA封於final-L-section7-cardref（932members）及final-L-section7-axiom（188members），獨立6360／937收據核對0不算產品測試。compiled116個ELF的真hash與保留位置明列，150,289,288B payload留雲端原地；axiom僅所選OUT/OUTER無ELF，不宣稱其他cache無ELF或內部compiler輸出已被捕捉。原工具未暴露的內部pipe不捏造。

## 2026-10-24 00:08 UTC：native r1 四個環境失敗的原件與同L修復

原230項完整執行的唯一紅列node:tests-js為737/733/4/0，四個readFileSync ENOENT對應L原有legacy6a.gcanvas、legacy6a-with-scene.gcanvas、legacy/base49-capacity.gcanvas三個fixture（其中一個用於兩案）；薄checkout的skip-worktree使三檔未物化。原r1完整exit1、完整Node stdout、3個原Gitblob、初始掃描器誤配及修正後literal閉包掃描全保。用原git sparse-checkout add --stdin精確補397,952B，HEAD／完整index tree保持L；只改物化及index stat/skip旗標，無產品／測試／expected修改。修復tool/outer0、actual104及獨立包333核對0、107原件封於final-L-native-fixture-environment-repair。literal掃描不保證計算型路徑皆完備，仍須原完整230項r2判官；目前r2未啟動，不以補檔0代替native綠。

## 2026-10-24 00:44 UTC：完整 canvas 通過，六項 browser 同 L 收齊

canvas 原完整 CDP_RESULT 為2267通過／0失敗、skipped=[]，85個golden section完全相符；P88=143、P73=69，原workflow與outer皆0。原elapsed1718.8848816149984秒，低於原35分鐘，沒有改斷言、golden或時限。原紀錄的1個uncaughtBrowserExceptions是P38故意注入fb-auto-probe，原EXPECTED標記及兩個P38檢查均通過，沒有UNEXPECTED EXCEPTION標記；transport/network故障注入診斷亦逐字保留，沒有宣稱例外欄位為0。

完整742members／51,393,525原bytes封於final-L-browser-canvas，tar為10,485,838B、SHA256 4153cafa4e1a24b75368a31c4fe8c71ab7b8bb5dde056c55880820bb41b78dbc。包含原指令、結束碼、完整streams、環境、L來源、4張workflow截圖及5個本地artifact；本地保存不冒GitHub上傳。三個可重建ELF僅省略payload而保真hash與sidecar；82個Chrome cache葉列明省略且未刪除。前後checkout／pool守門、reaper均原0，獨立3712核對0只驗收據，不增加產品測試數。六項browser現已同L全0。

native第二輪已在三個原fixture補齊後，依原完整230列入口重新啟動；final-L-native-r2-start只保存不變的啟動argv、原環境、來源SHA與launcher靜審，沒有封未完成streams，也不宣稱native通過。第一輪環境exit1保留。P52、Q38、P-189、#323 required-eight／PF3／timing／profile／memo仍UNRUN；B2原跨版本exact紅與B3待同L完整補驗仍未解除，沒有READY-TO-MERGE。

## 2026-10-24 00:53 UTC：終態維護完整原件、native切片映射與issue盤點封存

原27項終態維護完整3101-member包、collector最外argv／環境／完整streams及退出碼，封於terminal-maintenance-round2-originals；原source SHA逐項保留，不把維護capture綁定的L當成所有歷史工作來源。包括95＋37普通終態ELF退休、receipt保真去重、4個外部index退休、第二組raw保真跨filesystem搬移、12＋15普通ELF退休。原失敗、修正、工具、原PLAN、側車與既有對抗審查皆保。12側車使用退休時已核原hash的凍結副本，沒有把native R2重建後的cache冒成原收據。跨filesystem搬移只轉移占用，不能算全機節省。維護不是產品gate。

新增212組三份相同archive保真hardlink去重與seven-final舊15個普通ELF退休的原命令／退出碼／完整streams／原來源／PLAN／peer，封於terminal-maintenance-212-plus-15-originals。新212加既有24，共236組archive aliases；/workspace/geo261-cold/g261seal/{p-source,a-source,l-source}三個cold checkout一律禁寫，所有alias完全脫鉤前不可啟動測試或修改來源。收據、fixtures、Git objects與受控mutant／trace／withdrawn來源均保留；普通可重建ELF退休不算測試成功，未移標原歷史判決。

final-L-native-r1-special-coverage保存原52項映射核對、三份L原Git來源、extractor及獨立122核對：#314六完整Python module共103、閱讀A兩module21、#323三module50原row與完整unittest log皆pass。Python child0僅原裁判契約支持，per-child OS欄位原本未保存而明列null；Node inspector13是失敗Node737中的13個通過事件，沒有獨立Node13 exit0。完整native r1／workflow／outer仍1，四個ENOENT未改判；此映射不替代完整native、專項或性能。

open-issue-triage-originals封原90-member／1,482,357原bytes的534,257B小包及producer完整原流、初始outer未mkdir的準備1、286獨審與初helper錯誤。38個issue全文是既有歷史capture，不冒最新完整GitHub清單。r1把#340誤說已在L的finding1及r2修正均保：#340原獨立13項不在L原11項中；#214與#300仍是部分切片，不能宣稱母issue結案。沒有寫issue狀態或碰Grok分支。

draft #346已由本機橋接開出，沒有重複請求。native R2及Q38仍待原正式終態；Q38環境物化0不算產品通過，啟動紀錄目前僅雲端。P52、P-189與#323其餘專項繼續排程；B1／B2／B3仍未解除，沒有READY-TO-MERGE。

## 最新審查對照補正（2026-10-24 00:39 UTC評論）

#338 head f05e7cf最新B3對應Actions40043471807；#339 head e9ee6d0最新B2對應Actions40040764499。這兩個run的14份原annotation已逐項取得：付款失敗或支出上限，API不區分兩者。新run原件與source binding已同批封存，未以舊run40034196788／40032957675移標，也未宣稱新CI有runner、已啟動或已通過。新審查原全文及來源commit保留；最新評論仍判不可合併。

#339原11列仍3PASS／1RED／7UNRUN，新F38da的142 importer原0與三個predicate各0/1/0已完成且actual peer6636/0；aggregate native仍未跑，這批不替其餘正式項移標或解除阻擋；準備／source pin不算通過。C1要求可見PR狀態正式接替#324；C2仍取決於draft#340接受與最終組合驗收，不因文件更新解除。這次僅修審查來源和Actions對照，不發布另一份中間PR正文，也不改產品、測試、公理或任何判準。

## 2026-10-24 01:30 UTC：同L原完整Q38終態0與最新f05／e9審查對照

native R2原230列全部依expected完整執行，5309=5308pass＋0fail＋1原允許Windows GDI skip；Node737/737全通過，r1四個ENOENT已在同L補fixture後消除。原native CLI／workflow／CI35／outer皆0，00:38:48.178258～01:09:07.739721 UTC約1819.561秒，小於原35分鐘；沒有新增skip或放寬判準。final-L-native-r2-complete封1366-member／2,230,143B完整原包，SHA256 f9c5ca6b5d6b368a52657aff6ac73b4b7b31195973d840e1f99180eae4e0efde；原globalcache側車、完整已暴露streams、命令／環境／SHA與registry原Git bytes都在包內。6個普通ELF只省略payload，真hash與側車完整，原物件未刪；舊cache payload依原collector排除並保原保全manifest，不冒本輪輸出。collector不重跑subject，原7386獨審0只驗原件與來源；初peer誤讀producer schema的工具失敗亦保。

Q38原42案例完整執行，41 killed＋SPM24原equivalent，native27／model20兩baseline原exit0、零skip；原CLI、環境driver、兩層outer均真0，00:44:33～00:57:50 UTC。原registry排除test_source_index_typed_closure_and_display_identity保持，不把原排除改稱新增skip或補成已跑；SPM38／40的原允許ModelError沿原判決，不把它冒FAIL或新增擊殺。沒有縮table、改斷言／golden／600或900秒子時限。

final-L-Q38封449-member完整原包（4,717,550B，SHA256 acbf826d08488d4d678c68004d0c5e9e5979d0ba05951f5926dc73a6a28a1690），保原privatebridge／model-base環境driver、同L 22→565物化、原來源前後守門、兩outer、所有已暴露commands／退出碼／完整streams／環境／SHA，另保collector最外原流。兩個private ELF僅省略payload並保真hash、sidecar及原路徑；原TemporaryDirectory自行清理的突變payload未虛構仍在。此環境隔離不改產品／測試，不共用native R2 global cache。

原handoff e393的#338 f05／#339 e9最新審查全文、精確摘錄、四條Git原流與最小文件補正封於review-f05-e9-originals-and-preparation；初excerpt guard把正文小標誤認下一留言造成準備1的原件亦保，僅修辨識日期comment界線後復用同四capture，沒有改審查原文。新Actions40043471807／40040764499的365-member安全公開包封於actions-f05-e9-environment-public-v2；65條原讀取為63 exit0＋2次log Forbidden exit1，14原annotation都明示付款失敗或支出上限，不能猜是哪一項。兩次signed-log回應僅遮罩signature查詢值，PUBLIC_REDACTIONS明列位置與原hash，未遮罩的完整原件留雲端；其他公開bytes保持原件，不冒所有原流完全未遮罩。只發布已審v2指定三檔及安全peer附件，未遍歷私有原件目錄。

原四份完整Git tree與rawdiff顯示L7af→E935的260個變動路徑、F38→Ee9的20個變動路徑均為evidence/，所有非evidence path/blob相同；這是來源一致性證據，不把受測L／F換成CI evidence head，也不宣稱任何正式替代流程已接受。舊c6／47fd run分類只作歷史；最新兩run CI仍failure，B3不因分類或tree比對自行解除。

依最新C1，canvas與native已全終態，原件／唯一GDI skip已核對；正文仍暫維持D5bc，接著由root一次更新唯一矩陣，不把舊中間正文冒成此批結果。root已在native收包與7386原件核對後交還cache，接續同L原required-eight及PF3；本批保存兩份真正終態outer RESULT：required-eight原exit0、PF3原exit0，都保原command／環境／來源／stdout與stderr hash。這只是小原RESULT，完整原流／側車及專項包仍待另封，沒有冒稱已入庫。P52、P-189與#323性能／profile／memo仍UNRUN，B1／B2／B3未全解除，沒有READY-TO-MERGE。

## 2026-10-24 01:50 UTC：required-eight／PF3完整原件公開

同L兩項原CLI／nested wrapper／stage／driver／outer均0。required-eight原八列676個登記單位全部通過且零skip；676混合Python tests、C檢查點與core場景，不是676個unittest方法。原runner複製619份global suite-log，包含歷史未選項；只按當次--only八項argv與八列原stdout計數。841-member完整包2,063,262B／SHA256 81937992087ce136bdc34ece9d9da468e05beba5c931add719c9fb2501e661e4封於final-L-required-eight-complete。

PF3原baseline20全部通過，19刀各命中指定方法與marker的正常AssertionError exit1，restored20全部通過；原21次build invocation皆0，產生42個binary，不虛構42份獨立compiler OS退出碼。4759-member完整包14,686,234B／SHA256 fb3fc268318ec6844433fb35ef6a0c2dc1f72715f11f52d1417e633e068bd127封於final-L-pf3-complete；42個ELF共42,641,000B留原地，只省略包內payload，保hash／側車／recipe。

原v4 Recorder.role掃整串argv，遇--base設定而將兩項orchestration外層source_role/source_sha誤標base b74f9a2；原欄位與streams不回寫。acceptance_sha、顯式--sha L、真正subject inner與執行前後Git guards獨立綁定L，不能概稱所有source_sha欄皆L，也不能把base標籤當成實跑base。V4_OUTER_SOURCE_ROLE_DIAGNOSTIC與純role重現工具保此病因；未改原裁判或重跑subject。

兩份collector外層完整命令／stdout／stderr／環境／exit及原工具均公開；R8初peer schema誤判與v1保歷史。獨立2768／19603核對0只驗原件，不算產品測試。舊status-only小RESULT保原樣；本批不移標其他性能、exact、CI或整體驗收，不新增skip、放寬斷言或時限。P52／P-189／#323 timing、profile、memo及L跨版本exact仍待原正式結果，B1/B2/B3尚未全解除，沒有READY-TO-MERGE。

## 2026-10-24 01:57 UTC：59組cold receipts與cardref受控突變ELF保全原件公開

本批僅維護證據，不執行或移標產品gate。59組新增cold aliases的177原路徑與bytes全保，連同既有236組共295組cold aliases；三個cold checkouts在全部aliases脫鉤前禁寫、禁復用。原plan配置節省量286,375,936B，不能當成有背景寫入時的df淨回收。

cardref另有兩組受控突變ELF aliases，原116路徑與bytes全留，63個重複payload以保全link共享；原plan配置節省量79,196,160B，不是df淨回收。這兩組與295組cold aliases分開，任一alias寫入或復用前須全部delink。原inode與per-path mtime不保原樣，原metadata在PLAN；沒有刪受控ELF、收據、fixture或git object。

固定原件包7487members、4,160,382B、SHA256 0c9cb4ef4f425d7cb7ab7542c0b183ac55f09d6ada7350ea7e4e36bf7c95fcdb已公開於terminal-maintenance-cold59-cardref-originals。它保存原小metadata與完整命令流，不另複製cold receipt本體或ELF payload；cardref原931份非ELF原件由既有§7完整包／inventory覆蓋，沒有聲稱新包二次包含。collector完整外層與包外root sequential原件另外公開，未回寫固定tar；原收包0、獨審30026/0及collector靜審19/0均保。這些核對數不計產品gate，不更新其他效能終態，也不宣稱整體READY。

## 2026-10-24 02:01 UTC：P52原正式量測與五控制真終態0

同L原main/fix/fix/main交錯四區塊、每側16筆全部保留，main中位218.2650215ms、fix176.218242ms，ratio0.8073590573008969；原門檻fix<=main成立，沒有+5ms容忍。normal/delay原0，revert-delay/wrong/missing原1且各符合原控制判準；formal/verifier/driver/outer全0。四份原終態收據先封於final-L-p52-terminal-status-only，完整streams仍在原OUT，尚待完整原件包與獨立核對，沒有冒稱已全封。第一次collector遇Chrome SingletonCookie symlink退出1，屬收件工具假設錯誤，完整失敗保留；沒有重跑產品、改斷言或改時限。P-189與#323性能接續，B2及B3仍未解除。

## P-189首個exact差異：正式full原exit1，獨立timing另列

原正式full於2026-10-24 02:01:49～02:02:52 UTC執行，真正退出碼1，不再列UNRUN。原stderr精確為`p189_verify.py:195`的`assert raw['base'] == raw['fix']`，訊息`AssertionError: dump 不同：repo-_role_priority_mutant.scene`。訊息寫dump不同，但該assert比較完整load回覆加dump的stdout；兩版拒絕相同、第二行完整dump逐byte相同，第一行load error及stderr在L多`——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm`。

原stdout先有126組逐bytes相同（含四個生成場景），第127組首個mismatch即終止，未完成175組，也未啟動full原程式內後續timing。這是既有I22診斷功能版本與原跨版本exact的界線衝突，屬待裁決的驗收紅，不是環境或dump幾何差異；P189 base3e600772與#323 baseb74不同，不能把兩門檻當成同一實跑。保全部原判與差異，不過濾／正規化或放寬比較。

已依預先審過的獨立p189-timing tail完成三方量測，原CLI／driver／outer全0，36samples四receipt ratio皆≤2；該tail明列dump_count=0及overall_P189_passed=false，不把full紅燈改綠。P52已正式0、status-only於E58a75f4公開；collector先因Chrome IPC、再因原ledger附加欄位各退出1，兩次工具失敗均保留；v3已封完整包並核對13496/0，原產品沒有重跑。45個IPC只存metadata，65項原annotation保留，六個ELF只省包內payload；完整包待推送。

## 歷史快照：E537僅完成#323 compare時的小收據出版

同L #323原prepare0／build0／compare1已真完成；equivalence.json記175 scenes／350 runs，差異僅列`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`三個stdout。原`verify_linux.py:156`的`assert not failures,failures`拋出；ABC_result尚未設定、quantitative_targets為空，不能冒完整後續audit四元組或性能已通過。前後來源同L且clean；perf／profile／memo仍UNRUN，原比較器未改，B2未解除。

本批final-L-performance-terminal-status-only只公開P189兩原終態／assertion與首次差異streams、timing原36表／receipt／scope，以及#323比較後receipt／equivalence與outer；三份已完成完整包仍在雲端，沒有壓縮或入Git。P52／P189full／timing的actual核對為13496／14330／1457各0，不當產品測試；產品結果仍為0／1／0。

## 全部L專項終態已收齊：仍有原比較、性能與CI紅燈

同L完整清單是各原OUT逐項合成；單一#323 receipt只執行五stage，all_required_stages_completed=false及full_acceptance_passed=null原值保留，不改成整體driver通過。原#323 prepare/build/compare/perf/profile stage execution為0/0/1/0/0；perf與profile的outer CLI皆1，不能與stage execution0或個別數值目標綠混用。N64fix/main=1.4282954375137715>1.3是真性能門檻紅；N16/32/48對原base皆不變慢，source calls64/32=4.407618425509266≤4.5通過。原36timing與四profile未重取樣，分母與門檻未改。

memo於02:35:07.864974 UTC真完成，原driver/outer0；撤回1的calls比6.053833206336931>4.5，恢復0的比4.407618425509266，兩phase execution_complete true。memo隔離175/350 ABC原0、原audit tuple一致，仍不解除formal跨版本compare1、P189full1或N64載入性能紅。

本批final-L-all-terminal-status-only保原13KB formal receipt、performance/profile原JSON、三outer完整小流與原2,877,262B memo driver receipt；沒有摘欄冒原件。完整#323/memo原流與P52/P189三完整封包尚未推送，本小收據不代完整封包。下一步先查N64熱點與做受影響修正／撤回恢復，保原比較紅與QUESTIONS的版本裁決界線，繼續其他已授權工作，不放寬門檻。


## 2026-10-24 03:33 UTC：cold128 與四組保存式去重原件封存

本提交只補歷史維護證據，不執行產品測試、不改任何正式 exit、PR 正文或目前產品驗收狀態。兩份固定 tar 直接寫入 Git blob 並設 skip-worktree，工作樹不另物化副本；原 PACKAGE 欄位不回寫。

cold128 原包 15,922 members、2,774,412B、SHA256 4949b46b18d9b8b8bbaaec0fd65dc212ded056757b13589422f56fe702aeb2cd；128 組的 384 個來源路徑與 bytes 全保，原配置節省量 150,953,984B，不是 df 淨回收。完整原準備、執行、root 序列、命令與 stdout/stderr 已在包內；當次 collector 外層、靜審 24/0、完整包獨審 63,835/0 另附。先前 12.3MB Git-tree 原件沿包內固定 prior PACKAGE 連到既已公開的 cold59/cardref 包，未聲稱再次收錄；selector 的直接 exec／無獨立 c387 outer 限制照原披露。

四組原包 840 members、248,731B、SHA256 fc852b7d53c9c0c41feb2ce6256e61723cf2903fcdff4142e1076bb237ce73e7，保全部 19 個原 archive/stream 路徑及 bytes。來源配置節省量 476,540,928B，不替代含其他寫入的 df 差額；原 6alias publication 的 1/1/1/0 與 54 列歷史終態含紅結果原樣保留。原方案、精確原工具、完整 Git/consumer/journal/outer、獨審皆入包；當次 collector 外層、靜審 22/0 與完整包獨審 3,421/0 另附。F2 counterfactual 因原收據截斷無可信終態而排除，兩個候選原檔未動。

寫入禁令分開記錄：既有三個 seal cold checkout 的 423 組、cardref 的 2 組 ELF、GEO339 的 1 組六 alias、另 3 組大型歷史 archive。任一受保護 alias 寫入或復用前必須完整 delink。原 inode／nlink 與非 canonical 時間戳會按原方案改變，未宣稱保留 inode 身份；沒有刪收據、fixture、Git object 或受控 ELF。兩包完整 inventory 已在各 tar 內，未額外複製大 JSON。這些維護核對不計入產品 gate，也不把舊 L 收據移標成其他來源 SHA。

### U 原五stage終態（本段由root新證據提交附入）

產品來源固定 `ca7838e0f4950452b9befcf40899d606db9b81fa`，原prepare/build/compare/perf/profile各一次；execution=0/0/1/0/0，CLI=0/0/1/1/1，整輪launcher1。五階段前後均同U clean，兩重測鎖已釋。原命令、退出碼、環境、SHA及小終態原件在 `evidence/geo337-train-20261024/current-U-323-terminal-status`；完整U原流封包仍待保全／出版，不借L全包移標。

compare真175 scenes/350 runs後於verify_linux.py:156 `assert not failures,failures`判三stdout差：_role_priority_mutant、_s1_p8_l_room_primary_through_reflex_extension、_s1_p8b_l_room_primary_through_reflex_extension_hi。原ABC_result key不存在，all_required_stages_completed=false/full_acceptance_passed=null；compare後段audit因assert未達，required-eight/pf3/native三stage未跑，不冒完整audit通過。

原36樣本：N16/32/48 fix/base=0.9999532917535622/0.8129671517479105/0.806276034902179全綠；N64fix/main=1.429347781620555>1.3仍紅。profile execution0，原N32/N64 source calls=82668/364369，ratio4.407618425509266≤4.5綠；CLI1仍帶累積比較與性能紅。沒有改閾值、選樣或丟棄慢樣本。

下一步修性能病因並撤回／恢復自證；其餘新U原gate仍按最終來源重產／重跑。#345原六phase已真終態0、各19／零skip，獨審2493／0；完整包仍待公開，結果由獨立線原OUT `/workspace/geo345-six-original-requests-20261024` 保存，不列本列車gate。不是READY-TO-MERGE。

原v4 outer的source_role/source_sha依argv中的--base啟發式可能標base，原欄不改；產品綁定以明確U acceptance_sha、inner原receipt及前後Git guards為準。

### 新增四組儲存收據公開

本次另公開 maintenance-additional-four-archive-groups/：28 個原 archive 路徑與內容保留，四組 hardlink 維護原 exit0；原件包 359949B／1597 members，SHA256 e85764f616d5801a9fa13e23ea56cbfdaf32d8ccc203b1b0f48012c423bd31b6。完整收件原流與獨審 6417／0、alias registry 及其 77／0 另列；這是磁碟保全，不是 U 產品 gate。後續若要寫入任一共享副本，必須先解除該組全部 hardlink。

### b9 架構四檔採用

三原裁判0/0/0、九組原scanner具名assert反證0/1/0已在同一可解析b9完成，完整48條原命令、604Git/blob/raw/LF與兩SSOT初末保全。manifest／scan bytes不變，衍生diff只有report／receipt；前份928產物與本次937執行來源分開保存，沒有把較早native/browser/ledger移標。下一次性能使用已獨審的PIPE計時收件工具，原v4／U紅燈完整保留；測試門檻與樣本不變。
