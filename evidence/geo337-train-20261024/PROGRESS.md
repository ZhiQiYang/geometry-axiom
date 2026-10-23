# 新列車進度：draft #338（取代 #337）

## 唯一 current-state（2026-10-23 20:54 UTC）

- 分支：`codex/train-337-continue-20261024`；產品 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`；架構裁判來源 P=`17b3576434ffd0833056668898e1fd1a8cc2d560`；四檔採用與上游合流 head=`4f4a24d76e816274bfae06868b4dbf31f0860299` 已推。新測試來源 S=`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0` 已推；C/JS產品仍同F，最新 evidence head 以本檔所在提交為準，正式全清單的最終 SHA 尚未固定。
- 已普通 merge Claude 最後交接 `8f9301fc1b78712d930ffc68074437e44d068aab`（merge `586e6e8f`）與 main `425c092eaf16f90256d76433243baebde45163ac`。main 新增 #333 FIELD-RULES 與證據。相對F產品C/JS不變；兩個tests葉改為M151登記與free-end唯一錨點，保留所有斷言。
- #314 指定 `3b0b634f` 的17個產品／裁判 blobs及M99–M121定義已存在列車；沒有假移植。F 的六 suite **103項 exit0**、Node inspector **13項 exit0**、M121 原CLI0與build0/0/0、斷言0/1/0。獨立541checks／0。Node不是browser；六suite不是完整native。完整原件收於 `geo314-f64-originals-and-peer.tar.gz`。
- #323 來源已全包含列車，只在此線修。F 的原13/22/15三suite **50/0/0**、19組control獨立346checks／0；四新增與兩漂移修復為具名ASSERT 0/1/0。placement-key-single原等價0/0/0仍照實記錄。
- #323 正式一次36timings及4profiles已執行，原execution各0：N16/32/48-base=.70152535/.81183549/.70936489；N64/main=1.26480058≤1.3；source calls64/32=364369/82668=4.40761843≤4.5。分母與原門檻未改；獨立原件358checks／0已完成，原wrapper1因下列ABC紅燈，不能標整組全綠。
- #323 原175場景／350組 exact比較 **exit1**：僅3場景因既有#299 V_EXTENSION新增邊與區間診斷不同；dump、有序來源圖、5guards及允許／拒絕相同。原紅不改，詳 `QUESTIONS.md`；同列車僅撤回memo的175／350嚴格全輸出ABC與完整memo性能反證已完成：0/1/0、4.407618→6.053833→4.407618；獨立6655checks／0。五原件壓縮包47,120,357B目前僅雲端，尚未推送，保存在原路徑。I11補充單場景exact綠、原scene runner **166/0/0**，不冒充完整native。
- 閱讀A F：reader三條 **0/0/0（51項）**，native **7項／12組0/1/0**、oracle **14項 exit0**；獨立629checks／0已完成，完整原件收於`reading-a-f64-originals/`（895members、5597339bytes壓縮包）。native41筆子SHA欄原為null，父c387、前後Git身份與70C/H實際輸入逐份比對另附間接綁定，原件不改；原ELF已由測試清除，只保原hash，不冒fresh rehash。原三組沒有額外outer/reaper，不虛構。RC-run builder/checker兩精準撤回已各0/1/0，actual377checks／0、封包382checks／0，原件已封`reading-a-rc-f64-originals/`；正式quick仍待跑，未冒稱最終全專項通過。
- 架構 P 原三條 **0/0/0**（generic205、product18）、過期manifest反證 **0/1/0**；Linux manifest/scan/report/receipt四檔已重產採用，獨立686checks／0，604輸入closure=`6e1a994abaddec0ee851b96184a173548ac81b54ea37f7f7725e3066c7a6f338`。原F架構1/0/5與Ran0失敗完整保留。封存 `architecture-p17-and-recovery.tar.gz`。
- 4f4原完整CLI於20:44:44環境失敗終止：CLI2／root1／原new--check2，108/123（98killed／5equivalent／1crashed／3retired／1blocked），15未跑。M118還原build建立smoke時Errno28，M119建立目錄再Errno28而原程式早退；不是完整帳本綠。2031checks獨立審查原失敗保真，49.6MB原流封於`ledger-4f4-terminal/`；M118缺restore仍缺，不補假row。下一來源b6e1e454（C/tests同ec8）由root原完整123重新執行，尚未啟動。完整native、六browser、P52、Q38、§7、P-189與閱讀A矩形／579專項仍未完成。**沒有允許的新skip，不標READY-TO-MERGE。**
- 雲端Chrome156.0.8078.47／Nodev24.19.0／NotoCJK可用。只清已核可重建cache，保留收據、fixtures與Gitobjects；5批實際allocation回收998256640bytes，觀察free差996368384bytes，差值受共享磁碟並行活動影響。
- 18:25認證故障原件保留；18:55普通Git重試恢復，原未推提交ae25／17b已補推。交接分支在自動同步造成一次非快轉拒絕後，用普通merge補入，`8c60c977e772126f120fd6f2d3ca95208ba8fd44` 已推，含NEXT與#324 PR請求。沒有force push。

## 並行工作與下一步

1. #323 memo完整反證已完成。root正在封舊4f4環境失敗並準備新來源完整帳本；新ledger完成採用後固定final SHA跑完整native、6browser與專項。canvas與性能獨占，其餘最多兩重測。
2. #339接替324：原S57的指定9個importer模組142/142與3組predicate反證真綠；普通merge #340後source1f0，原registry-list0只表示清點，11正式列仍未跑。最新E dcdf2265／D2aac已推，base=#340；不把S57實跑轉標新source。
3. noWood draft #340：原Sbfb的13項及7phase真0/1/0/1/0/1/0，actual530/publication949/新merge343 checks獨審0。新source4d3、body77a已推；11輸入同但不冒4d3重測。列車未入main也繼續疊線。
4. #300原c493的三套32方法／46controls真0/1/0、282compile/link全0，actual1020checks／0；普通merge #339後只expected9→10，已推sourceaa0，效能與512尚未完成。GEO260接aa0後sourceeb846，保noWood13/faces45/woodcontact10並只native28→30，原全44準備執行；af4 focused兩控制仍保原SHA。#325/#331/#333不寫其分支，#333已進main。

每個歷史結果保留原SHA，不把證據提交冒充受測SHA；失敗原件不覆寫。最新審查來源是已fetch handoff的337/338及各工作線留言；338目前沒有新增審查。工作持續中。

S ec8的Linux架構四檔已於9a05採用，三原裁判0/0/0、205/18及781checks獨審0，604-input closure不變。冷checkout原碼副本全封後精確回收216,199,168B已推；free-end與舊323收據只搬儲存位置並保原path symlink、原bytes/mode/mtime，沒有刪收據。下一輪重測先守資源預算，保留所有原失敗。

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
