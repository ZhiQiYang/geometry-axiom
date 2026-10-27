# #338 唯一 current-state：固定 F cbf0fb62

本文件是 `evidence/geo337-train-20261024/PROGRESS.md` 的唯一目前狀態；`resume-20261026/PROGRESS.md` 與各封包內快照均為歷史。更新日期 2026-10-27 UTC。產品／正式 execution **F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`**；本次證據父 **E=`047d93f01ba1bd349ebc256c4e8d19209bfd0f49`**，本提交只增加證據與更正進度入口，不改產品。發布後的完整新 E 以普通 Git 發布原始收據為準，不把預備文案當遠端成功。

`a4bd77e8090f5a82f0c8934c30c5335782293922` 已撤回，其結果不能移標 F。#338 仍 draft，**尚未 READY-TO-MERGE**。

| 正式項目／來源 | 真實終態與 exit | 原件、限制與尚缺工作 |
|---|---|---|
| F native | 外部固定F正式 **0**；230 suites／5328pass／0fail／1原GDI skip，1886.996秒 <2100，stack16MiB；ledger check0／stale0 | 外部原件 E=`732ef20e34876379a37eb69693a481becebea43e`，[NATIVE_HANDOFF](https://github.com/ZhiQiYang/geometry-axiom/blob/732ef20e34876379a37eb69693a481becebea43e/evidence/geo337-native-validation-20261027/audit/NATIVE_HANDOFF.md)；producer75files遠端hash0，root已讀回交接、完整接收核對中；來源／tests不變，不塞入本次六包 |
| F canvas | UNRUN | 必須在 F 獨占執行，舊 F9 綠不能移標 |
| F assembly | driver／primary／reaper／所有 wrapper／control **0**；150 pass、0 fail／skip、9 screenshots，192.930640466 秒 <900 | root session55236／chunk1e4a3c；獨立 9151 checks0，3759 closure、private index／golden bytes保全0。本次 `F-assembly.tar.gz` 收錄完整原件 |
| F documents | inner／outer **0**；47 pass／0 fail／skip、8 screenshots，70.97391320997849 秒 <600 | 已交付 E45dd4d662eac9297eda8473742c9943a1cb336cb；本次僅補原 namespace 排除漏掉的兩個 `.git` 共146B及1271目錄 metadata，無 ignored runtime 遺漏，不重包大原件 |
| F grid | driver／primary／reaper／所有 wrapper／control **0**；356 assertions、0 skip、4 screenshots，464.329781552 秒 <900 | root36920／c78dd1；獨立9137 checks0、3759 closure／private index／golden bytes保全0，本次 `F-grid.tar.gz` 收錄完整原件 |
| F space | 正式／control **0**；242 assertions、0 individual skip、原2組omission、33 runtime PNG，213.725140721秒 <900 | root session82112；獨立9164 checks0／完整3759 closure／index／golden bytes保全0。本地原件已核，待後一束交付，不納本次六包 |
| F timber | 主代理觀測正式外層 **0**；詳細原件核收／公開待完 | root session21730／chunkc5eb9d，F獨立來源；不納本次六包，不把尚待核收稱已交付 |
| F Reading A oracle／Q38及其他待驗專項 | Reading A 三項已委派同一外部native工作線，尚未收到終態；Q38等 UNRUN／未閉合 | 本環境不競跑oracle，產品／裁判 closure規則保持，不以委派／封包／工具測試替代 |
| F 全123帳本／mutation check | S10全帳本 **0**；F check **0／123** | S10=`82c922a3941525d3a094ac0158bdc7dea57ea360`；114 killed、5 equivalent、M20 crashed、3 retired；120 execution heads保留，既有有效原件不重跑 |
| F 架構三條／reader | 架構 **0／0／0**；reader inner／outer **0／0／0** | 架構798 edges／205 generic／18 product／0skip；reader51tests／0skip、173 ResourceWarning保留；已有效，不重跑；產品內架構receipt於a6生成，與F後跑正式三裁判分列 |
| F §7 axiom | primary／reaper／outer **0**；44 baseline、5 red1／restored0全killed，11subprocess／269tests | 已交付 E2d576269ab85ef64a921bc4b15d013ca2ef5b4fb |
| F §7 card | primary／reaper／outer **0**；43 baseline／0skip、53 actual mutants全部 red1／restored0，116ELF完整 | 已交付 E047d93f01ba1bd349ebc256c4e8d19209bfd0f49；普通push及兩blob完整遠端bytes／SHA核對0，本次僅補傳輸收據與兩次失敗 |
| #323 R8／exact、P-189等歷史 | R8固定源75a1e93811a52b69385cbdaf6a09d773ed9052ad的比例綠但outer1；F9 exact0；P-189 strict原紅保留 | 不重抽、不移標，不擴大白名單；這些不是本 F 尚缺正式項的通過替代 |
| 撤回來源 a4bd…歷史 | assembly150pass／190.7710495829815秒，documents47pass／64.691242696秒；check **1**，stale53／survived0／invalid0／blocked0 | 本次自然分包完整原件，只保留其實際 execution SHA，不計入 F 正式矩陣的綠燈 |

F9=`4f8a794f4167c3562eb182045102e86e9e37cca9` 的舊 native exit1（5327pass／1fail／1原GDI skip）、六browser0、assembly r1環境失敗均保留。舊space2／timber5分組skip是原來源原結果，未增加skip或放寬斷言／golden／時限。

## 本次一次交付的範圍

`recovery-bundle-20261027/` 依自然工作分成六包：固定F assembly、固定F grid、已撤回assembly、已撤回documents＋ledger、transport、cleanup＋小補件。每包逐檔列來源／mode／size／SHA256與目錄（含空目錄）；socket／symlink只留metadata、不跟隨。全部新封包以固定tar metadata及gzip mtime0產生，完整串流roundtrip核對；在生成前用未壓縮tar／PAX headers加gzip最壞上界檢查每blob<100MiB，不假設壓縮收益。

assembly／grid 的 partial mode 與 space 專用裁判未執行完整 canvas golden 比較；其「golden bytes保全0」只指原檔逐byte未變，不能充當 canvas 通過。

正式browser只排除各原審查列的**exact3759 tracked source葉**；`.git`、ignored runtime、private Git metadata／index、private golden、命令、環境、輸出、screenshots和所有其餘葉皆保留。原件未刪。已公開card包55,775,729B不拆、不重壓；成功publisher原始`000035/stdout.bin`與此包逐byte相同，Git blob=`e02a03a6dd2c3d53f650fce3c5f6dc219935d215`、SHA256=`475678a2227d503ba0781eb578ee86d27fa13716fb146ba510f62f0144097be9`。新tree中的stdout原件路徑直接指向同一已公開immutable blob，保留完整來源／path／size／hash mapping，引用E047既有完整readback核對，不再製造第二份55MB下載原流。全部**新**archive仍須完整遠端readback後才算交付。

本次工具反證僅驗封包工具：正常／撤回內容完整性／恢復 **0／1／0**，撤回樣本保持同size／mtime／inode但命中`audited hash mismatch`；包含長PAX路徑、空目錄與metadata-only symlink。正常／恢復gzip逐byte相同。此結果不是產品驗收。

## 傳輸失敗、修復與審查更正

第一次 root30780／02a67e exit1，POST git/blobs回422「input too large … Consider creating the blob in a local clone … pushing it to GitHub」；原stdout240B、stderr152B與約74MB base64 stdin全保留，沒有commit／ref嘗試，也沒有重試該API。這不是權限或安全拒絕。

第二次 root75914／e286ac exit1，沒有push。`git fetch --filter=blob:none --depth=1`取得15,945B metadata pack後，Git2.52 `index-pack --promisor`的`repack_local_links()`把alternates中原已存在的27,738個object本地重包為2,422,150,411B（21,779blobs）。全部OID有fetch前provider成員證據，不能稱為2.4GB網路下載；原未開trace2，不虛構內層process trace。`GIT_NO_LAZY_FETCH`不會禁止這種本地promisor重包；原工具的容量估計與事後檢查不夠，已保留根因與原失敗。

修復採完全**no-fetch**、無promisor的私有Gitdir，唯讀復用既有完整object provider；缺物件即失敗，不clone／index-pack／repack。hash-object以原檔argv讀取、stdin空，不再複製base64 payload。小型local-repack反證0／1／0，incoming pack354B，獨立172checks0；正式成功root8624／c234d0 exit0，普通fast-forward到E047、exact outgoing8objects（2blobs＋5trees＋1commit）、兩blob完整遠端核對0；provider與兩次失敗原件保全。

曾有核收代理誤把JSON顯示轉義當成實際regex雙跳脫；原`ACTUAL_PEER.json`保留，`CORRECTION.json`與`ACTUAL_PEER.corrected.json`**撤回**`PROMISOR_REGEX_DOUBLE_ESCAPE`判斷。frozen executor實際regex bytes為`5e72656d6f74655c2e2e2a5c2e70726f6d69736f7224`，本來正確，沒有修改它或重跑發布。另加的人工regex突變0／1／0不表示實際publisher有該缺陷；獨立審查已核12outer＋3inner、45完整streams。所有原錯判與更正一起交付。

大型production Git objects仍保留原地，不重複包進證據；排除metadata、完整verify-pack輸出／provider快照／所有命令原流均留存，不以省空間刪任何原件。

## 來源、批准及資源邊界

目前來源依主代理核實handoff `8992388515172d068ee1e28526e1103ff18aa4f2`、#338 01:48Z更正：撤回a4bd、回F。原train evidence head=`e1efab34d970a052a8082fa62e478ad13a0625ae`、tree=`1fee37a0dc6c3f28fce09dd813f5c9865962962e`。先前handoff913d…／01:30:50Z F′指示只是歷史；F′ CI七jobs runner_id0／steps=[]沒有執行，不能判產品紅綠。

原API帳戶與[#338 10:39:52Z留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)作者id同59477728；完整API早已隨documents交付，原使用者引述與「本機Claude整理，非原話」分開。帳戶／引述核實不等於擴張#323三差白名單至P-189、改數值門檻或豁免mutation stale／survived／invalid／blocked。新正文D=`e386f0063e50b1e96597671f9339a908fa2f66fe`的真發布原件本次一併收錄，不重發同版。

父端目前允許兩OWN合計最多**8GiB任務規劃**，不是產品門檻／平台quota／安全設定。原`3P+L*65536+M*8+67108864`、64MiB保留、實際掛載free、cgroup觀測保持；完整成本另算新archives／loose／outgoingpack／新payload readback／metadata，不以SHM free抵算TMP。缺失PSI明列unavailable，不當零壓力。無mount／quota／權限變更，無付費資源。

原3156檔＋108空目錄清理已回收107,233,280B，不重做。固定extra168已依明確批准與fresh核對完成exit0：168removed／0skip／0dirs，60commands／336journal，TMP實測+22,892,544B，終態free120,623,104B。本次包含完整原流／audit，舊備份不複製；fixtures、Git objects、使用者修改與原始失敗保全。

#347 C1 文案已普通快進E8bb0359331365c6f3a96872620427cf7847fcb50、正文D066bc6606503f29b57b6ff54d07e1a0d13f1617a；產品S324／source parent a5f／current base eaf分開，B1／B2仍未解。#343／#348舊紅燈與交付不變。

下一步交付space原件、接續F timber／canvas／oracle與其餘必跑專項，核收另一環境native完整原件與Reading A終態；有效既有gate不重跑。合併只在既有工作分支同步的批准範圍處理，**不合併PR或main、不部署、不新增公理、不改安全設定**。
