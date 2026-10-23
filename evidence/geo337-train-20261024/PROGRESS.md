# 新列車進度：draft #338（取代 #337）

## 唯一 current-state（2026-10-23 19:38 UTC）

- 分支：`codex/train-337-continue-20261024`；產品 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`；架構裁判來源 P=`17b3576434ffd0833056668898e1fd1a8cc2d560`；四檔採用與上游合流 head=`4f4a24d76e816274bfae06868b4dbf31f0860299` 已推。最新 evidence head 以本檔所在提交為準，正式全清單的最終 SHA 尚未固定。
- 已普通 merge Claude `f7026c110b4800ee87f9ecc1eff0cc14d535841a` 與 main `425c092eaf16f90256d76433243baebde45163ac`。Claude 是同一 exclusion hash 更新；main 新增 #333 FIELD-RULES 與證據。相對 F，產品 C／JS 與測試內容不變。
- #314 指定 `3b0b634f` 的17個產品／裁判 blobs及M99–M121定義已存在列車；沒有假移植。F 的六 suite **103項 exit0**、Node inspector **13項 exit0**、M121 原CLI0與build0/0/0、斷言0/1/0。獨立541checks／0。Node不是browser；六suite不是完整native。完整原件收於 `geo314-f64-originals-and-peer.tar.gz`。
- #323 來源已全包含列車，只在此線修。F 的原13/22/15三suite **50/0/0**、19組control獨立346checks／0；四新增與兩漂移修復為具名ASSERT 0/1/0。placement-key-single原等價0/0/0仍照實記錄。
- #323 正式一次36timings及4profiles已執行，原execution各0：N16/32/48-base=.70152535/.81183549/.70936489；N64/main=1.26480058≤1.3；source calls64/32=364369/82668=4.40761843≤4.5。分母與原門檻未改；獨立原件358checks／0已完成，原wrapper1因下列ABC紅燈，不能標整組全綠。
- #323 原175場景／350組 exact比較 **exit1**：僅3場景因既有#299 V_EXTENSION新增邊與區間診斷不同；dump、有序來源圖、5guards及允許／拒絕相同。原紅不改，詳 `QUESTIONS.md`；同列車僅撤回memo的175／350嚴格全輸出ABC與完整memo性能反證已完成：0/1/0、4.407618→6.053833→4.407618；獨立6655checks／0。五原件壓縮包47,120,357B目前僅雲端，尚未推送，保存在原路徑。I11補充單場景exact綠、原scene runner **166/0/0**，不冒充完整native。
- 閱讀A F：reader三條 **0/0/0（51項）**，native **7項／12組0/1/0**、oracle **14項 exit0**；獨立629checks／0已完成，完整原件收於`reading-a-f64-originals/`（895members、5597339bytes壓縮包）。native41筆子SHA欄原為null，父c387、前後Git身份與70C/H實際輸入逐份比對另附間接綁定，原件不改；原ELF已由測試清除，只保原hash，不冒fresh rehash。原三組沒有額外outer/reaper，不虛構。RC-run builder/checker兩精準撤回已各0/1/0，actual377checks／0、封包382checks／0，原件已封`reading-a-rc-f64-originals/`；正式quick仍待跑，未冒稱最終全專項通過。
- 架構 P 原三條 **0/0/0**（generic205、product18）、過期manifest反證 **0/1/0**；Linux manifest/scan/report/receipt四檔已重產採用，獨立686checks／0，604輸入closure=`6e1a994abaddec0ee851b96184a173548ac81b54ea37f7f7725e3066c7a6f338`。原F架構1/0/5與Ran0失敗完整保留。封存 `architecture-p17-and-recovery.tar.gz`。
- 全123筆突變帳本已於19:33 UTC由root在4f4來源啟動，仍執行中、尚無最終exit；原3417探測1（107 stale、3 retired、13 unrun）保留。完整native、六browser、P52、Q38、§7、P-189與閱讀A矩形／579專項仍未完成。**沒有允許的新skip，不標READY-TO-MERGE。**
- 雲端Chrome156.0.8078.47／Nodev24.19.0／NotoCJK可用。只清已核可重建cache，保留收據、fixtures與Gitobjects；5批實際allocation回收998256640bytes，觀察free差996368384bytes，差值受共享磁碟並行活動影響。
- 18:25認證故障原件保留；18:55普通Git重試恢復，原未推提交ae25／17b已補推。交接分支在自動同步造成一次非快轉拒絕後，用普通merge補入，`8c60c977e772126f120fd6f2d3ca95208ba8fd44` 已推，含NEXT與#324 PR請求。沒有force push。

## 並行工作與下一步

1. #323 memo完整反證已完成。root全帳本執行中、獨占R3；完成後固定final SHA跑完整native、6browser與專項。canvas與性能獨占，其餘最多兩重測。
2. #324已接替為draft #339：S=`57b680140da2c6b77ab0d362a72029d8d7c9334b`已普通merge列車；獨立靜審254checks／0；16正式項未跑。owner接續封存新證據，不把靜審當動態綠。
3. noWood已開draft #340：S=`bfbab207a92a809fca50fefcefb3fa4b2af05ea9`、body=`63613255e8052004ee5c447cd729d4dde9d156c1`已推，獨立靜審116checks／0；13正式項／7phase未跑。列車未入main也繼續疊線。
4. #300前置剖析照常準備；#325/#331/#333不寫其分支。#333已由他人合入main。

每個歷史結果保留原SHA，不把證據提交冒充受測SHA；失敗原件不覆寫。最新審查來源是已fetch handoff的337/338及各工作線留言；338目前沒有新增審查。工作持續中。

## 歷史紀錄：2026-10-23 19:17 UTC

Reading A 的3條reader、7 native、14 oracle完整指令/環境/streams及629checks peer已封存推進；preparation hash失敗及peer自身兩次讀取錯誤亦保原件。這是F64既有實跑的封存，不另宣稱在evidence SHA實跑。

#323完整memo反證已回報fixed0→withdrawn1→restored0，sourcecalls比率4.407618→6.053833→4.407618；同列車175場景/350組完整stdout、stderr、orderedgraph與5guards全等。正交獨立actualpeer並封原件，歷史base三診斷紅仍原樣保留。

全帳本即將由root在可解析4f4 source啟動；先以原--check保留stale結果，再原123筆CLI全部重產。外部旁錄器只保存原完整stream，子程序600/900/300時限保持；原child與外層exit分列。323已明確釋放原checkout，不再有兩個owner移動同一HEAD。

## 2026-10-23 19:38 UTC 帳本啟動與反證封存

19:27 v3環境前置exit1，發現原scene CLI預設產生的ignored `current_geometry.svg`；原fullCLI從未開始、seed未移動。保留v3指令／原完整stdout與stderr／環境／exit及driver，收於`ledger-start-and-memo-summary/ledger-preflight-v3-original-failure.tar.gz`。v4只核Git untracked/ignored、regular XML與原main預設路徑後，將該SVG完整移入證據；其它ignored仍拒。獨立16checks／0，無產品／測試／斷言／時限修改。

19:33原123筆全CLI已真正啟動於4f4；原source與seed獨立Git、HEAD/索引/refs/所有原件hash守門通過。輸出`/tmp/train337-ledger-4f4a24d7-r2`、cache `/workspace/train337-ledger-cache-4f4a24d7`。此提交只保存開始事實，尚無全帳本結果。後續正式清單仍待ledger採用後固定final SHA。

已fetch handoff4ee272be；338尚無新審查，服務已開draft340。持續#300根因與browser低磁碟配置靜審，不空等帳本。#323完整47MB原包仍僅雲端，這次只推小交接與原件peer；不得把小摘要冒充全部原始輸出。
