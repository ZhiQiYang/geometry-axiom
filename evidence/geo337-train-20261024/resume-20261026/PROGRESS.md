# #338 current-state：固定 F cbf0fb62 接續驗收與證據交付

2026-10-27 UTC。此份唯一 current-state 的 final 執行來源恢復為 F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`。本證據提交父 E=`45dd4d662eac9297eda8473742c9943a1cb336cb`，屬 `codex/train337-recovered-evidence-20261026`，不覆寫原 train。**a4bd77e8 已撤回；兩來源結果互不移標。#338 仍 draft，尚未 READY-TO-MERGE。**

card 封包中的 `CURRENT_PROGRESS.md` 保留凍結當時的歷史快照；assembly 新終態僅更新本 repository `PROGRESS.md` 與發布 manifest，不重包或重跑，現況以本文件為準。

## 唯一 current-state 矩陣

目前 final 執行來源恢復為 F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`；a4bd77e8090f5a82f0c8934c30c5335782293922 已撤回，該來源收據僅列歷史，不能計入 F 的正式項目。

| Gate／來源 | 真實狀態與 exit | 證據與限制 |
|---|---|---|
| F native | 本環境 **UNRUN**；另一獨立環境已接手執行 | 不把別的執行者接手當終態；本線不改 native 路徑／准入 |
| F assembly | **driver／primary／reaper／所有wrapper／control exit0**；150pass（P77=134／P82=16）、0fail／skip、9screens，192.930640466秒<900 | root55236／1e4a3c；獨立9151checks0、3759closure／private index／golden0，原件待一次封存，不移標撤回來源 |
| F canvas／grid／space／timber | **UNRUN** | 以F的獨立來源／埠／暫存接續；撤回來源的browser不移標 |
| F documents | 原 inner／outer **0**；47 pass／0 fail／0 skip、8 screenshots，70.97391320997849 秒 | 已交付 E45dd4d662eac9297eda8473742c9943a1cb336cb；原10分鐘保持 |
| F Reading A oracle／Q38及其他待驗專項 | **UNRUN／未閉合** | 原來源／closure規則保持，不用封包或靜審替代 |
| F 全123帳本／mutation check | S10全帳本0，F check0／123 | S10=82c922a3941525d3a094ac0158bdc7dea57ea360；114 killed、5 equivalent、M20 crashed、3 retired；120 execution heads保留，不重跑 |
| F 架構三條／reader | 架構0/0/0；reader inner／outer0/0/0 | 已有效，不重跑；架構798 edges／205 generic／18 product／0skip；reader51tests／0skip、173 ResourceWarning保留 |
| F §7 axiom | primary／reaper／outer **0**；44baseline、5red1/restored0全killed、11subprocess／269tests | 已交付 E2d576269ab85ef64a921bc4b15d013ca2ef5b4fb |
| F §7 card | primary／reaper／outer **0**；43baseline／0skip，53actual mutants全red1/restored0，116ELF完整 | 原件已一次封存；API422與後續Git metadata取件失敗原件全留，目前尚未交付，改成完全無fetch的傳輸設計 |
| #323 R8／exact、P-189及其他歷史 | R8固定源75a1e93811a52b69385cbdaf6a09d773ed9052ad比例綠但outer1；F9 exact0；P-189 strict原紅保留 | 不重抽、不移標，不默認擴大白名單 |
| 已撤回 a4bd…的 assembly／documents／check | assembly150pass／190.771s、documents47pass／64.691s；check exit1 stale53、survived0 invalid0 blocked0 | 只是各原execution SHA的歷史原件，不能算F通過；後續獨立封存不刪原件 |

F9=`4f8a794f4167c3562eb182045102e86e9e37cca9`。F9 native 歷史 exit 1：5327 pass／1 fail／1 原 GDI skip；F9 六 browser 歷史 0，assembly r1 環境失敗保留；space 原 2、timber 原 5 分組 skip 保留。沒有新增 skip。舊矩陣只留 Git 歷史，不能拿封包或工具測試充當產品驗收。

## 本次 card 正式原件

原指令 `python3 -B -u geometry-core/card-reference/run_mutations.py --output <OUT>/subject`，不加 `--only`，完整 argv、環境、來源、命令與 stdout/stderr/exit/hash 在 `card-F-cbf0fb62-20261027/EVIDENCE.tar.gz`。OUT=`/dev/shm/geometry-axiom-geo337-20261025/card-F-cbf0fb62-formal-20261027`。01:42:42.718771Z 開始、01:49:54.482478Z 結束，wrapper 431.763707 秒；原 reaper 429.6554579734802 秒。root session34127／chunk aeb1c7 的 outer 0 為主代理終態觀測，核收代理沒有再 poll 或重跑。

完整 baseline 43 tests／0 skip；53 項依原順序各實體突變 red exit1（具名 assertion、無 error／skip／compiler／infrastructure failure），還原並重編後 exit0。107 test processes／149 test invocations，116 compile commands、116 ELF 全保留；沒有用 crash、編譯失敗或逾時冒充 killed。

原 compile/child 180 秒、confirmation compile60／run30、model adapter60／scene20、stack16MiB 保持，outer=None 不另虛構外層時限。原 capture/reaper、Node24 與 GCC pin 均有原件。獨立核收 exit0／2409 checks，39 外層 streams 與 446 內層 compiler/test stdout/stderr 原檔全留；原內層記錄未自帶 stream hash，因此核收於 SELECTION 為每份完整原件補 SHA256，未聲稱舊記錄已有。

完整封包選取 OUT **987 regular files、126 directories（含空 tmp）、152,414,354 logical bytes、154,218,496 allocated bytes**，包括 **116 ELF**，無刪除／排除。另納入工具、靜審與實際核收、固定 SELECTION，以及 documents 的已完成實際發布核收。全部原件仍留本機；不把封包放進原 OUT 造成遞迴。

262 closure 檔、15 個被突變目標、7 fixtures（含五份受保護 fixture）、HEAD/index/refs 恢復核對通過，15 原始備份全部精確。目標 mtime/ctime 因原突變／恢復合法改變，沒有偽稱時間戳不變。原程序消費者檢查零命中，但兩個 OS PID 共六個 permission-denied 欄位未可見，限制如實保留，不把未知當已檢查。

67 次非原子取樣 combined OWN 最大 2,445,164,544 bytes、實體 SHM free 最小 15,425,445,888 bytes；不是精確 peak，也沒有 gate 獨占 OOM 量測。此批非效能收據不外推 R8／P-189 性能。

## 已撤回 F′ 的歷史來源與批准範圍

目前來源以主代理已核的 handoff `8992388515172d068ee1e28526e1103ff18aa4f2`、#338 01:48Z更正為準：a4bd已撤回，改回Fcbf0；原API與完整留言在 `/tmp/geo338-source-withdrawal-20261027/`。原train目前evidence head=`e1efab34d970a052a8082fa62e478ad13a0625ae`、tree=`1fee37a0dc6c3f28fce09dd813f5c9865962962e`，仍與formal execution F分列。

以下只是歷史：先前handoff `913d6c429dbd0c6fbfcb3cf700133881c3149ee6` 的 #338 01:30:50Z Claude交接曾稱新 F′ 與本機 evidence head=`2d7a635ec6408f7fda80db13992d08feb4727e4b`，後續七項與 oracle 應以該來源執行。原 #338 分支由別的執行者管理，recovery 不覆寫。F′ 的 CI run40431992777 七 jobs failure 卻 runner_id0／steps=[]，沒有實際 runner，不能當產品紅綠。

F→F′ 非 evidence 差異恰三檔：`geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md`、`product-architecture-receipt.json`、`tests/mutants_results.json`；`tests/test_geo314_commit_paths.py` 同 byte。card 工具的 `Fprime-impact.md/json` 與原 diff 輸出已納入：三檔不在已查 card258／wrapper262 葉內容閉包，不改已知 card 產品／裁判輸入；這不等於自動批准跨 SHA 沿用，也不把新架構 receipt 視為已核收。

原 API 帳戶／批准全文已在 documents E45dd4d 封存：`gh api user` 與 [#338 10:39:52Z 留言](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849) 作者 id 同為59477728。留言的使用者選項引述與「本機 Claude 整理，非原話」已明確分開；核實帳戶及引述不等於任意擴張解釋。保持 #323 精確三差、性能門檻、P-189、mutation stale／survived／invalid／blocked 的原邊界；不自動採新例外、不自行合併。

## 容量、其他工作與下一步

兩 OWN 規劃已由父端在本次本地重包意外後明確更新為最多 8 GiB，是可逆任務規劃，不是產品／使用者門檻或平台配額。原64MiB發布保留、`3P+L*65536+M*8+67108864` 完整公式、真掛載 free 與 native TMP 原門檻不變。card 封包和發布原件在新 SHM delivery sibling，完整規劃不假定壓縮率；不改 mount/quota/權限、不增付費資源。

原3156檔＋108空目錄清理已完成，TMP實測回收107,233,280 bytes，不重做。新增固定168檔經原批准與fresh備份／consumer／dirty／hash核對後已真exit0：168 removed、0 skipped、0 directories；60commands／336journal，TMP實測+22,892,544 bytes，終態free120,623,104 bytes。原件在/tmp/geo-extra168-approved-20261027/execution/RESULT.json，SHA256 b7f6e997e0cdf4a0bb2b78be71c10cc7a13ee54bb3f419ff58a7bd727a690bc4；既有備份不重複複製。所有原始失敗／fixtures／Git objects／使用者修改保全。native128MiB工具規劃與產品門檻由另一owner診斷，本線不改native路徑或/tmp/geometry-tests，既有launcher准入維持；TMP不能用SHM抵算。

#347 C1 文件已普通快進 E=`8bb0359331365c6f3a96872620427cf7847fcb50`、正文 D=`066bc6606503f29b57b6ff54d07e1a0d13f1617a`；產品／execution S324、source parent a5f、current base eaf 已分開，B1/B2仍未解。#343/#348 的已交付文案與原紅燈維持，不重發同版。

下一步在 F 的獨立來源完成仍必跑的 browser／oracle 與原件核收；native由另一獨立環境執行，本線不更改其路徑或門檻，已有效的F收據不無依據重跑。每個結果保留真正 execution SHA，不以停止等待或空輪詢代替可執行工作。未合併PR/main、部署、付費、改安全設定或新增公理。

## Card 發布傳輸修復

首次發布 root session30780／chunk02a67e exit1，停在第4條 POST git/blobs；完整 stdout240B／stderr152B 為 GitHub HTTP422「input too large … Consider creating the blob in a local clone … pushing it to GitHub」。`published:false`、`publish_attempted:false`，未建新commit／未嘗試更新ref；不是權限或安全拒絕。完整原始請求（含約74MB base64 stdin）、回覆與失敗收據保留，沒有重試同一API。

替代流程在另一個新的私有SHM metadata Gitdir，用publisher-source object provider唯讀alternates，僅抓固定E45dd的blobless父提交／tree，建立精確兩個evidence葉的單parentcommit，再一般git push（無force）。既有55,775,729B封包SHA256 `475678a2227d503ba0781eb578ee86d27fa13716fb146ba510f62f0144097be9` 不重壓、不拆分、不刪原件。只有完整遠端ref與兩blob逐byte／GitOID／SHA256核對後才算交付；本文件是發布前current-state，實際新E及傳輸結果由原始發布收據補充，不預先宣稱成功。

## 第二次傳輸失敗與修復設計

Git替代傳輸 root session75914／chunke286ac exit1，未嘗試push。第4條`git fetch --filter=blob:none --depth=1`先取得15,945B commit/tree pack，Git2.52 `index-pack --promisor` 的 `repack_local_links()` 隨即把唯讀alternates中已有的27,738個物件本地重包為2,422,150,411B，含21,779blobs。全部OID已在fetch前provider中，沒有證據支持將此稱為2.4GB網路下載；原始未開trace2，不虛構內層程序紀錄。原filter有效，`GIT_NO_LAZY_FETCH`不會禁止這種本地promisor重包。此工具設計遺漏已承認：只做事後pack檢查太晚，原64MiB metadata估算不足。

新工具完全移除fetch／clone／index-pack／repack路徑，僅將這次已存在的完整E45物件資料庫當唯讀alternates。新私有Gitdir不設promisor remote；缺物件即失敗，不補抓。完整新物件集合在push前必須精確等於兩blob、必要tree與單parentcommit；新blob／可能outgoing pack／完整readback／指令原件及metadata逐項估算，再取不低於原3P公式的預算並保留64MiB。fresh實體SHM與cgroup壓力觀測後才准入。原2.4GB物件、API失敗stdin、全部正式收據均保留，不刪、不搬、不重壓封包。小合成本機反證與新工具peer另記，不將其算成產品驗收。

本機合成修復反證已真完成：oldblob_not_copied固定／撤回／恢復exit為0/1/0，incoming pack僅354B。撤回no-ingest修復會在無網路、GIT_NO_LAZY_FETCH=1下重現local repack；固定／恢復的privateODB只有兩新blob、一新tree、一新commit。原始31外層指令與2內層verify-pack、全部原流保留，獨立核對172checks exit0；這是傳輸工具反證，不算產品驗收。
