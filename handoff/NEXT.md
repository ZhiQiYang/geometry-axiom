# 持續工作 checkpoint：F8 的 R8 量化門檻全綠，exact 三差保紅，接續完整帳本與正式驗收

這是接續點，不是停工或完成報告。使用者不在，不提問、不空等；繁體中文、英文 commit。不 force push、不合併 PR、不推 claude/*／grok/*。主代理唯一寫 #338 主列車；每條來源由一人維護、另一人對抗審查。不得放寬斷言／golden／時限，不改決策佇列；公理只依已核可 SSOT 流程。主列車保持 draft，尚無 READY-TO-MERGE 裁決。

本稿以 handoff 基底 `7a31dc436c78f16979b8f4cb97550118355f6d3a` 的既有 NEXT 保留其他工作線，更新本輪可核對的 F8／R8 終態。來源 SHA、實際執行 SHA、證據提交與正文提交分列，不隨 evidence 提交移標。

## 唯一 current-state

| 項目 | 身份／實際結果 | 下一步與界線 |
|---|---|---|
| #338 主列車 | `codex/train-337-continue-20261024`；固定產品／測試／架構 F8=`75a1e93811a52b69385cbdaf6a09d773ed9052ad`；證據 E=`996aeded246090de87efc631a29cb7e4b5585d30` | E 的非 evidence tree 與 F8 相同；只有 root 可續寫此分支。 |
| 正文 | 分支 `codex/train-337-continue-20261024-prbody`，D=`aebadf14ae832053fca5c932900ba821dcb18f13`，真普通 push 成功 | `/tmp/geo337-R8-running-prbody-publication-20261025/RESULT.json` 為原結果。此草稿所讀 pr-status 還列舊正文47ace3da；不能把分支已推送說成 bot 已套用，不重複排請求或空等。 |
| R8 原五 stage | F8，prepare/build/compare/perf/profile execution=`0/0/1/0/0`；累積 CLI=`0/0/1/1/1`；outer真exit1 | 全36樣本／4 profiles／175 scenes、350比較已收。五stage不等於八stage；all_required=false、full_acceptance=null，ABC_result原欄缺席。 |
| R8 性能 | N16/base=`0.9834192453688345`、N32/base=`0.9007932884873169`、N48/base=`0.7392862448969592`，皆≤1；N64/main=`1.2846970752586067`≤1.3 | 原量化門檻全綠，沒有放寬、不重抽有效R8。後續帳本採用不能把這輪改稱其他 execution SHA。 |
| R8 source calls／exact | N32=82668、N64=364369，比例=`4.407618425509266`≤4.5。exact仍同三個stdout mismatch，compare exit1 | role_priority、P8低／高凹角；原assert與版本基準保留。B′／C未核可，見公開逐項報告與QUESTIONS。 |
| F8 tracked帳本 | 原 `python3 tests/mutate.py --check` execution_head與product_source均為F8，exit1；120 stale／3 retired／0 invalid | 完整123已於2026-10-25T07:38:36.624220+00:00在F8正式啟動，RUNNING、尚無終態；生成完成與採用均不得預宣告。只由root在穩定來源整份重產，保留120個真execution.head；採用JSON後固定FINAL，再清除所有MUTATE_*跑原tracked check。 |
| 完整正式清單 | F8 full native、6 browser、P52、Q38全44、§7兩項、P-189 full與timing、required-eight／PF3／native後段、memo、reader／RC／#314／閱讀A專項皆仍UNRUN | H focused或R8量化通過不代替這些正式gate。native原16MiB stack、strict registry；性能與完整canvas獨占，其餘重工作最多兩個。 |
| H局部修正 | 原定向來源 S=`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`，14/14、exit0、零skip；原13方法不變，修正已入列車 | 固定／撤回／恢復actual memset工作量exit0/1/0、calls0/2/0、bytes0/255168/0；不是Windows或完整native驗收。 |
| 架構三裁判／四檔 | 真執行 M=`6e50aef65513b7b38f93228919272c6d40d6c196`，三judge exit0/0/0，205＋18、零skip；F8採用其report／receipt | 604inputs僅references.inc變動；scan與937／55政策不變；九guard各0/1/0、neutral2通過。最終正式三gate仍另跑，不把M移標為F8執行。 |
| required CI | F8 run40170221039／較早E815cd2e3 run40170692505各7 failure，runner_id0／steps0；原18 API讀0 | 當前E996aeded的CI未讀，不能移標舊run。原annotation是付款失敗或支出上限；未改帳戶，亦無正式替代接受紀錄。 |
| native ROOT | `/tmp/train337-323-f64d638f-source` 已普通detach到F8，checkout真0，actual獨審通過 | 來源轉移不是全帳本或產品gate；full123獨立source/cache/seed與每filesystem入場已完成，observer正在執行，結果未定。 |

允許skip僅原Linux `py:test_gdi_contract` 缺compiled Windows GDI harness；新完整native未跑，不預先計入。不得新增skip、刪測試或放寬門檻。

## 本輪公開原件與不可混淆的結論

- [R8完整五stage原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/full-R8-five-stage-raw/)：9057 members／31,362,296B，tar SHA256 `4503955cefc6fb1a6491ad2a146c259e59a2185401d0fbebc09908a47e3bf9d0`。完整36樣本、四profiles、350比較原流及inventory在包內；七ELF是hash-only封包，原payload仍留雲端，不宣稱封包包含ELF。原OUT `/tmp/g337323R8`、tools `/tmp/geo323-final-r8-stage-tools-20261024`，不得覆寫或重抽樣。
- [R8小終態／CI／F8帳本check／原CLI與outer](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-terminal/)；小摘要 `/tmp/geo323-r8-terminal-summary-20261025/SUMMARY.json` SHA256 `23c0b08133a48285bb7fd75192a9b05a2fb190fa04ca5dc5cadfb28e28a4e5dd`。小摘要actual51/0只核原件投影，不是產品測試數。
- [三項exact的完整原輸出與Git歸因](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/REPORT.md)及[具體選項](https://github.com/ZhiQiYang/geometry-axiom/blob/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/current-R8-exact-three/originals/QUESTIONS.md)已公開，獨審424/0。
- exact保留原 `verify_linux.py:156 assert not failures,failures`。引入提交 `6366304eb787b2a50282e4132f45e51eb7d21290`；固定b74與F8的I22整條逐byte相同，舊base訊息欠缺其自身條文要求的定位邊／超出區間。不能為追求綠燈刪必要診斷。
- 維持A：如實保紅、繼續其他工作。B′補診斷的比較基準會改exact版本邊界；C具名三pair政策會改允許差異規則，均需明確裁決，尚未採用。兩者均不改性能分母或重抽有效R8；P-189適用範圍仍須另外明示。Q-323-ABC／Q-P189-EXACT未解決，無隔離ABC接受結果。歷史P-189 `p189_verify.py:195 assert raw['base'] == raw['fix']` 亦首先在role-priority失敗，不把獨立timing當full exact。
- [H完整定向原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo323-reference-local-init-2c463557/)：2546 members，tar SHA256 `7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388`。支線 `codex/train337-reference-local-init-20261024`，S如表，E=`74a0a289b48f21f0211c4906808c79138b22b741`，D=`11a93b5b82a5c630b307da0d49bf79349149f58e`，均真普通push且已合入主列車。
- H把持續狀態分支不使用的127584-byte local零初始化延後到fallback。三phase persistent／fallback／allocation-failure／ordered-graph皆exit0；fallback實際校準各清零一次。完整撤回精確紅燈是 `ASSERT:persistent-reference-local-zero-work line=166 expr=local_zero_calls==0&&local_zero_bytes==0`。focused為O0，ELF hash-only；新O2 wall結果只以R8原樣本為準。未採rank-bound外稿不混入本修正。
- [架構完整原件](https://github.com/ZhiQiYang/geometry-axiom/tree/219bf5d44a0c0f1c3a0d5e67b2782ed807e09af6/evidence/geo337-train-20261024/architecture-6e50-complete/)：380原件／4,630,676B，M真執行與F8採用分列。K provider-hint前一切片 S=`1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`、E=`4d3ac4bf42f431c23833c8841e4a7a597d275dbd`、D=`ae5e9431bfb8feb3b8b8aa9ecce523af3135a5ea` 保歷史來源及完整反證，已合列車，不冒F8 focused重跑。
- R5／R6／R7原件均已公開，歷史outer1與當時紅燈原樣保留。R7全包9128 members、SHA256 `8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e`；F7=`6df0264f75e84f03adb70746b6ac3db07a9910fc` 的N16/base1.05190582882169只屬歷史，不能繼續稱為F8當前性能紅燈。

## 其他工作線：保留自己的S／E／D，不冒F8新驗收

#344：`codex/issue320-connection-recovery-20261024`，S=`cbb318d76d7d242ae0db760ae15d57ef1cad4aa0`（一般merge F7），E=`a5ec136baf3909453867b3eed50f1b93b229ca59`，D=`b169e27ebb4b5835af50a4f070af290c7622630c` 已普通push。該S原strict aggregate9真0；完整canvas fixed／withdrawn／restored三phase仍UNRUN，未合主列車。舊S540的VM9/row9仍是歷史，不移標。

#348：`codex/geo300-capacity512-20261024`，S=`73b21e64dce72f0d16ca29e18559c51815b9724d`，E=`9a8584f57be7935604c3bad4c2481945a6ec3d9f`，D=`1f0e9d8633c333114f2dce74315a9903e36a0dd7`。H3、三helper與sentinel定向反證完成；兩個原方法的第一個placed512四指令批次仍各600秒timeout紅，尚未到sequential-history／canonical replay。原收件未留partial stdout，不能只歸因loadfile；原NativeBuild ELF已清除，保hash而非payload，重建必標新的ELF／closure。容量仍未合列車；原失敗包與環境補跑分列，兩原archive Git blobs不得刪。

下表沿用舊NEXT的既有工作線身份與驗收界線；縮寫是歷史記錄，不補造未驗的新SHA：

| 工作線 | 保留身份／owner | 狀態 |
|---|---|---|
| #339／#340 | specials；原 F38／S175 | 祖先已合；#340 最新審查已解除13 aggregate缺件，仍 required CI，不自行判已接受。 |
| #341／#343 | combined；W source=`df66452e7a514032453bea93b8b18ab74d7b1457`；E=`f7a389deafed64f0f3137c0086a7033841c709e3`，D=`37a2f117529c15c6525be79b17389d47b43a9acd` | 原定向36、plane整刀0/84/0與見證反證保來源；已入列車。#341 四類 work/CPU/wall不得冒已完整。未採 rank 外稿另保，不改已公開收據。 |
| #342 | backlog 準備，原 source=`eb846c34` | 祖先已合；新 strict native30尚未完整整合驗收，當前 Q38應44。最新審查的 native30／CI／base 阻擋保留。 |
| #345 | specials；原 S=`2199cda8`，E=`99646d418bc5e886a92bfdabe33e68780e88fe3b`，D=`c5515c14ac9cb59d147563f3dd75dbde5b75ca4e` | 六次19方法／零skip真0；四控制屬等價0，不冒 functional kill。尚未有可合併裁決，未合列車。 |
| #346／#347 | combined／backlog；原 S=`39273bc0` cut-list、S=`32403481` empty-row | 原公開定向／反證保原SHA；未合列車。各既有 E／D以歷史 NEXT／該 PR原收據為準，本輪未更新；raw-seam 外稿未C。 |
| #325／#331／#333 | Grok | 不碰分支。木工端頭／固定／RC 推理先讀核可決策及 #333 FIELD-RULES。 |

更早完整S／E／D及工具記錄保存在歷史 `handoff/NEXT.md`（`230113da9b919861862eccbeb2c339bda94044e7`）。#339既有最新審查接受F38→F1的498-path closure保留142 importer與三predicate，舊B3已解除；正式11／native／browser／ledger／架構、requiredCI及base接受仍待。#324舊入口仍需本機Claude可見重導向#339並凍結／關閉；雲端未代發留言或推Grok分支。#335未核可CLI初放能力仍僅準備／QUESTIONS，不擅自採入公理。

## ROOT轉移已完成，下一步是全123與同FINAL正式清單

原L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`已由普通 `git checkout --detach F8` 轉到F8。真readonly preflight為 `/tmp/geo337-native-root-transition-F8-preflight-20261025/`；真apply為 `/tmp/geo337-native-root-transition-F8-apply-20261025/`，07:06:28–07:06:38 UTC，exit0。未reset／clean／force，也未刪receipt、fixture或Git object。

apply保留原refs並另加 `refs/codex-preserved/native-root-L-before-75a1e938-20261025T070635Z` 指向L；6997個物化檔案／306,790,772B逐GitOID／SHA／nlink1通過，只有4個原定新C harness，無原路徑消失。Gitmetadata只index、HEAD、logs/HEAD為普通checkout預期變更；sparse與ignored `current_geometry.svg` 原bytes保留。actual peer `/tmp/geo337-native-root-transition-actual-peer-20261025/REVIEW.json` SHA256 `ab5b4e7fb1c9b991942f4ee05f5b15e8c08921693cbdbb98bd5b893ca45e04e5`。這批原流尚在雲端待另行正常出版，不宣稱已在E219。

五份fixture原bytes與Git身份都保全，禁止刪除：

- `tests/evidence/k2a-collection-capacity-20261012/legacy6a.gcanvas`
- `tests/evidence/k2a-collection-capacity-20261012/legacy6a-with-scene.gcanvas`
- `tests/evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas`
- `tests/release-evidence/20261008-cloud-closeout/contracts/grid-final/grid-rule-timber.scene`
- `geometry-web/docs/evidence/issue48-34a6222-20261005/archives/1280-full.gcanvas`

**全123已正式啟動，RUNNING，尚無終態收據。** 原 observer request 的 started_utc=`2026-10-25T07:38:36.624220+00:00`，source SHA為F8；原入口 `tests/mutate.py`，沒有只選子集。root session=`58101`（當次本機執行記號，接續時先查原進程／原件，不當作可跨工作階段重用的handle）；outer `/tmp/geo337-full123-F8-launch-20261025/`，job `/tmp/geo337-full123-F8-job-20261025/`，開始事實見 `observer/request.json`。原driver實際filesystem入場通過後才進observer；不能把啟動或部分列進度寫成完整通過。

來源配置 `/tmp/geo337-F8-full123-source-materialize-20261025/RESULT.json` 真exit0，SHA256 `c058ce31c147707643eeef027bbcd0e61d6c62450f56282c4251fd2ea9c0f229`；它只證原root／新seed／cache準備與closure，不是正式結果。先前root抄driver pin少了`a7`，原launcher在輸出目錄／鎖／admission／正式入口之前拒絕exit1；原失敗保 `/tmp/geo337-F8-full123-prelaunch-20261025/FAILED_PIN_TYPING.json`，formal_executed=false，修正CLI pin後只正式啟動一次，未改工具、門檻或產品。

由root單獨整份重產123（120自然項／3 retired），保每列真execution.head，完整原流封存；所有原終態完成並獨審後才採用帳本JSON、普通commit／push固定FINAL。正式tracked check必清除所有MUTATE_*，外置候選check不能替代tracked check。歷史正文D757發布時尚未開始full123；當前正文D aebadf14已同步真開始時間與RUNNING狀態，尚無終態，不把D757移標為已記錄啟動。

完整123的原prepare／observer／mapper保持。外部容量入場稿 `/tmp/geo337-full123-F7-admission-draft-20261024` 的名稱含F7只是工具來源歷史，真正request必綁F8；driver `7b6c57008921d7622ee6e47a987d7225a9318a7e53b582d3c1b9a1a5dd177eb1`、helper `bc93c7e37c29ed0ef3c93819e6e67ae0674f4b054ac7ab7df48a25ee718ba121`，原52/0 static peer。必同時計算TMP／workspace各filesystem的mutable seed、編譯池、全raw、Git出版與預留，不能用另一filesystem的free抵帳；來源轉移192MiB admission不替全123背書。完整操作順序保於 `/workspace/geo337-native-root-transition-and-final-chain-20261024/PLAN.v2.md`，其中R6舊紅／未轉移敘述是歷史，當前身份以本檔及F8原件為準。

採用帳本後的FINAL依原清單完成native、六browser、P52、Q38全44、§7、P-189 full+timing、required-eight／PF3／memo、reader／RC／#314／閱讀A及架構三裁判。原工具的source／OUT／cache request要精確新綁並獨審；不得拿歷史L/F7的綠改名。採用前後若只帳本／證據變，保存精確closure與真execution SHA，不篡改帳本head。

## 永久保全、排程及審查接續

**`/tmp/geo337-published-archive-git-objects-20261024` 是永久 Git object store，絕不可當cache清理、搬移或刪除。** 保留其lease、root alternates及所有已公開R5/R6/R7/R8/#348 blobs；原receipts、fixtures、raw與歷史失敗都不能刪。

歷史同bytes封包的共享inode只限已登記冷資料；所有alias保持immutable，禁止原地寫入，重新使用前須獨立解除每個alias。registry只追加，不回寫歷史nlink。四冷TMP群維護已真0且actual709/0，19原路徑全保，實際TMP淨增加137,879,552B；後續六群原RESULT真0（30paths、原net86,007,808B）與其獨立actual核對分開看，不推定全部storage已封包公開。WS375經獨立第二靜審後已原exit0，2622個原path全保，workspace free由57,393,152增至376,119,296B，實際回收318,726,144B；原件在 `/tmp/geo337-ws375-preserving-execution-20261025/` 與 `-launch`，獨立actual已完成19791項資料核對／0錯誤，收據 `/tmp/geo337-ws375-second-actual-peer-20261025/REVIEW.json` SHA256 `63a996840e8eb6f24ba881dd83adf6fa334ef3496f85cc1d75a04dad1b4e22a5`；同目錄IMMUTABLE_ALIAS_REGISTRY.json SHA256 `a919b549016076e75911ba7af42c0f2d27b40952009ec3deac0b718995f376f6`。完整維護收據仍待另公開，不冒已入E219。跨device容量因此可重新判定，full123原admission已真通過；磁碟維護不代產品gate。每次重工作前fresh df，不拿任何歷史free數字當當下容量。新工具／OUT／cache優先新私有TMP，永久objects與全raw除外。

本草稿所讀 handoff 為 `7a31dc436c78f16979b8f4cb97550118355f6d3a`；#338最後【ChatGPT 審查】仍是2026-10-24T06:38:46Z、head597bce6。B1完整final驗收尚未完成；B2性能部分已有F8/R8原量化綠，但跨版本exact與未核可B′／C仍紅；B3 requiredCI未解除。新正文已普通推D aebadf14，bot套用與新審查再讀pr-status／pr-reviews，不自行標READY。

每輪先fetch handoff分支，讀 `handoff/pr-reviews/*.md`、`handoff/pr-status.md`與`handoff/pr-requests/README.md`。新阻擋優先修；需要新PR／正文依既定5欄請求流程，已排請求不重複排，不等待bot空轉。等審查時照優先順序推進未合列車上的其他工作線；主線full123執行時可做靜審與小metadata，性能或完整canvas則獨占。任何紅燈保原assert／exit／輸出，先分類，未核可公理或數值政策寫QUESTIONS並繼續不受影響工作。全程無合併PR授權。

最新啟動證據已普通push：[F8 full123 RUNNING 收據](https://github.com/ZhiQiYang/geometry-axiom/tree/996aeded246090de87efc631a29cb7e4b5585d30/evidence/geo337-train-20261024/current-F8-full123-start/)；7葉349860 bytes，非evidence tree不變。此處只公開啟動、來源配置小收據與預啟動pin輸入錯誤，不宣稱整份重產已完成或所有維護raw已公開。
