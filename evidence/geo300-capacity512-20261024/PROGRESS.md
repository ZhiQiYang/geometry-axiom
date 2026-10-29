# #348 current state：8b候選各批600內；完整H7原1200逾時

正式產品仍F2 `b595e55952d5d66de95024432e1b29bec7525e9b`／測試C `75481194f3b85a6b07e11896403633d7d0fa0d6f`。獨立候選 `8b128aa7bf53b41b493dd3a0bee49f0d53391254` 尚未採入。

- 00:12:43–00:32:43Z原8方法H7實跑，1200.016299009秒超時，outer1；7方法印ok，最後canonical方法未完，**不是READY-TO-MERGE**。
- 新512load256.109964／251.966908秒、sequential＋I8a確認/history273.936417秒、第一canonical285.428571秒皆0且原斷言過；第二canonical被aggregate期限中止，不能算通過。
- 完整原件 `h7-timeout-8b128aa7/`，含待完008與原ELF，原600失敗/F2/C/前候選歷史不移標。172有序圖等價和先前具名撤回保持原execution。
- 一次N128插裝診斷exit0：24548個exclude不同但其餘key完整相同；只證明可命中，不是新效能收據。生命週期靜態審查排除刪必要World重驗。下一步單次真512profile找剩餘產品成本。
- 上游#347目前 `8bb0359331365c6f3a96872620427cf7847fcb50`，343→346→347未閉合。原review相對base behind2、目前ref比較behind3；新evidence提交只改ahead。全ledger/census/architecture/native/browser未完成，不合PR/main、不放寬守門。

## 真512 profile完成；hash-tag候選不採入

8b原ELF的512-pg診斷371.171277秒exit0，stdout/stderr與正式512全等。2ac7126205f0079feda8a282663996a75ea12d87的62控制與172有序圖綠，但一次N256 34.701295→34.902487秒未證收益，故不帶入下一候選。原件profile-and-tag-2ac71262。下一步從8b的獨立ordered-runs分支省去W已排序區段的重複比較；H7原紅與上游狀態維持。

## W有序run候選已完成有界核對

cff51164fe0293c8046aa66d86016cd0be333a08原53與172圖過；只加新tests/catalog的b05288e2be691dd5229937ab6c9a1f555b3f64e2新8與三具名0/1/0過，產品未再變。N256新執行34.299473對沿用8b34.701295秒、原流等，僅約1.2%差，不稱正式512或H7綠。未採入正式產品；原件face-runs-b05288e2。接續只讀評估低命中率hint容量；原守門與來源鏈不變。

## 歷史檢查點（以下current-state字樣均為原當時紀錄）

# #348 current state：512三路徑各批已綠；整套時限與上游鏈仍阻擋

execution C `75481194f3b85a6b07e11896403633d7d0fa0d6f`，產品仍F2 `b595e55952d5d66de95024432e1b29bec7525e9b`；以下舊段落只保留歷史。

- **C 第二H7完整exit0，1test／0fail/error/skip**，966.209439335995秒。512 load468.402913秒／RSS251368KiB；sequential＋實際token確認＋history491.646998秒／RSS456208KiB，兩批exit0且各低於原600秒。所有原capacity rollback、delete、Undo／Redo、幾何與精確保存斷言保留並通過。
- F2第一H7原方法exit0，512 load482.595614秒、canonical500.587198／529.473389秒；按history-complete-75481194/closure逐項同源證明沿用，execution不改標C。C小7支0/1/0、32項F2控制與K29／root172原件均保留；無未跑冒通過。
- 原F2 I8a紅、原B600秒timeout、各環境失敗完整保留。C首輪工具session中止SIGKILL／無完整結果，獨立背景重跑才有本次正式終態，不冒成最佳樣本重抽。
- **未達合併條件**：完整H7原1200秒預算仍不符、native35分鐘／全census expected／全帳本／架構／browser未完成；上游#343→346→347未閉合。當前直接#347 8bb0359331365c6f3a96872620427cf7847fcb50，原review behind2、C fresh behind3/ahead22，來源鏈修復後才一般merge精確head及受影響重驗。
- 本次原件在history-complete-75481194/RAW.tar.gz與manifest／STATUS／ENVIRONMENT；正文以實際新evidence head更新。下一輪純計算memo仍僅私有候選，未採入、未證實加速。

## 最新獨立候選（尚未採入 PR348 產品）

2026-10-28 23:13Z：隔離分支 codex/geo300-hotpath-candidate-20261028 固定 f5806c60c6067a64776f979f77981e4aba087df3 已推。K空槽/W有序快路徑/memo 的原控制與新反證已實跑，原編譯前置紅和duplicate控制存活均保留並補正。詳細逐execution在 hotpath-candidate-f5806c60/README.md。單次N128 6.691758→6.037951秒，stdout/stderr相同；只~9.8%，不足解除full1200。新有序圖比對尚未完成。原F2/C 512正式收據不變、不重跑、不移標。

## 候選圖比較真終態

f5806c60c6067a64776f979f77981e4aba087df3 的172場景×2新程序全過，23:24:53Z–23:25:39Z、exit0。沿用原B9a的固定E18原件並逐檔核closure；全ordered graph/stdout/stderr/5guards/allseals相同，沒有重跑B。原件 graph-candidate-f5806c60/。此候選尚未採PR348；更新中的consumer scope是另個來源，仍需自己的受影響驗收。

正文同步：GH API本輪可用，23:25:37Z已PATCH並GET逐byte核對，實際正文已從舊2de/ac1更新為dbdf/F2/C；新evidence head發布後再同步。REST PR物件base.sha仍2e8a6ed20325aa4842dcd0f89eacd598662be598，但同一API git/ref及Git ls-remote均8bb0359331365c6f3a96872620427cf7847fcb50，應分開記snapshot與目前分支，不誤稱新上游修鏈。#347最新審查仍B1/B2未閉合。

## 作用域索引候選檢查點（未採入）

3949deb9e565a9e5aeca5bc475ec646e77cc6546 已推獨立候選。原 allocation 紅保留並修復；K48、W/bridge52及補充scope17均實跑綠，逐execution見 scope-candidate-3949deb9。一次N128僅12.5%改善，不冒H7全綠；下一步真正512與剩餘查找成本。實際PR正文已於23:35:26Z同步E e4d00c43ed204aa3f07606a86cd625c59dce2184並GET逐byte核對，舊2de/ac1/ENOSPC正文已解除。來源鏈仍阻擋。

## 512候選載入真終態

3949deb9e565a9e5aeca5bc475ec646e77cc6546 的單一真512 load於23:59:33Z完成：261.840563秒、exit0、原placed_geometry過、RSS222088KiB，stdout與舊F2/C相同。原件scope-load-3949deb9。沒有聲稱canonical/history或H7已過；目前繼續H兩處未使用raw facts與K hint省工，待新來源完整驗證。

## H/K最小省工候選（待原H7）

8b128aa7bf53b41b493dd3a0bee49f0d53391254：172完整圖全過；9ac120項中的119項已綠，唯一新增withdrawal定位前置修復後8b新7全過，產品未變。H新fixture紅、hashanchor紅均封存 hk-candidate-8b128aa7。下一步原H7整套1200秒與各batch600，未稱全綠；原F2/C與上游鏈狀態不變。

## 歷史檢查點（不取代上方current state）

# #348 current state：512各批已在600秒內完成；I8a history與整套時限仍紅

產品／execution F2：`b595e55952d5d66de95024432e1b29bec7525e9b`。本節為唯一 current state，以下舊段落只保留歷史。維持 Draft，未達合併條件。

- I8a測試修復已採入：真token確認；原delete成功／無preview及全部history斷言保留。7支真橋接0/1/0已跑，撤回命中placed-delete-confirm-must-commit。512修後尚待執行；詳history-protocol-20261028。產品四leaf未再變動。
- 原兩個 H7 慢方法已真正結束：exit **1**，2 tests／1 failure／0 error／0 skip，2511.530170054秒。第一個方法通過；第二個不是通過。
- **512 placed load 482.595614208秒、canonical replay 500.587198156秒與529.473388700秒**，三批真exit0，原幾何／ID／definition／fresh協定逐byte斷言通過。wait4 RSS依序251460／256668／256564KiB。
- 第二方法的load492.981413560秒與sequential/history子程序496.086327713秒均exit0、未timeout；但test_geo261_timber_capacity_host.py:279期待delete直接ok:true，實際回I8a valid:true預覽、零violations。只刪除512，另511支幾何未變；未確認World逐byte不變，後續Undo因此不是撤銷刪除。**這是既有I8a流程的測試缺漏，將補真正token確認，不能繞過產品I8a或放寬原斷言。**
- 另外32項受影響控制（H6、W14、W容量7、H7其餘5）已在同F2實跑exit0，118.664619289秒、0fail/error/skip。K source29與172根scene的688次有序圖／stdout／stderr／guards逐byte等價已核，不重跑同版。
- **完整H7/native尚未通過**：run_all.py:530的Python suite時限是1200秒（先前900說法更正），native job35分鐘；第一方法六批本身1516.046849611秒，不含編譯／assertion／收件，已超整套預算。每batch600秒保持不變，不能以各批完成冒稱整套綠。
- 帳本check已實跑exit1：107 stale／13 unrun／3 retired；需最終穩定來源完整重產。架構原三裁判與四檔、完整native／browser與其餘專項未完成。
- 單次static-pg N128診斷10.439190712秒exit0，與既有N128 stdout/stderr逐byte相同；揭露memset0.58秒、memmove0.56秒及mcount2.07秒開銷。不能外推正式512性能；完整ELF、建置、原輸出與profile均保存。
- 新原件位於 `formal-f2-b595e559/RAW.tar.gz`、逐檔MANIFEST及STATUS；固定execution不隨evidence提交移標。原600秒timeout、F1環境紅與F2第一輪outer130中止完整保留。
- 取件更正：GIT_NO_LAZY_FETCH本身未阻止所有隱式歷史取件。改用獨立非promisor發布object store、只保留原parent tree並更新新葉；一般push，無刪objects、無force。原生tmpfile仍查真/tmp，未以SHM抵算。
- 上游阻擋1仍存在：審查相對base **behind2**；已知目前#347 `8bb0359331365c6f3a96872620427cf7847fcb50`新增evidence提交後原B為behind3/ahead8。#343→#346→#347未閉合；鏈修復後才一般merge精確head、逐leaf重審與受影響重驗。未merge上游，不合併PR/main。

下一步：修正I8a history測試及具名撤回；依profile繼續產品效能修復以符合原整套時限。I33仍必須CAPACITY且不截斷；公理層、決策與既有閾值不變。

## 歷史檢查點（不取代上方 current state）

# #348 current state：F2 索引修補及172場景等價已過；正式512待跑

產品 F2 `b595e55952d5d66de95024432e1b29bec7525e9b` 已一般推送，遠端ref核對一致。本次可選索引只壓縮ordinal儲存；權威count／ID／ordered node/edge仍為size_t，超出UINT32_MAX或配置失敗會放棄索引回原線性搜尋，不截斷、不新增CAPACITY拒絕。公理與原600秒未改。

- **索引29項 exit0**：原21項保留，新增4正例及4具名撤回；所有原、新控制均具名偵測，0failure/error/skip。
- **172根場景圖等價 exit0**：B `9a8584f57be7935604c3bad4c2481945a6ec3d9f` 對F2，每場景四支診斷程序，共688次；stdout/stderr、所有seal完整有序node/edge/value/status、五守門計數與seal次數逐byte相同，無差異白名單。這是O0單編譯單元診斷，不冒正式分離K/W/H建置。
- F2 N128原分離O0加pg診斷10.398194秒exit0，stdout與B逐byte相同；不外推512通過。profile的累積child_maxrss仍含compiler，不能冒產品RSS。
- F1原H7第二輪：512 load546.118481秒／canonical第一輪590.554897秒均真exit0；第二fresh replay收據寫入ENOSPC，完整方法未過；sequential在原64MiB發布reserve前置失敗，沒有開始。原outer1、全部已取得raw保留；未將F1移標F2。
- 已修正取件工具使用：GIT_NO_LAZY_FETCH=1防止隱式補抓；新失敗未索引pack完整搬存SHM並保留原路徑/hash/mode，無刪原件或indexed Git objects。正式新OUT使用SHM，逐batch完整raw壓縮後持久存/workspace；小型64場景留證smoke1/0 exit0（非完整H7），實際含binaryhash與原指令/退出碼。1MiB是留證規劃而非產品門檻，原64MiB發布reserve及600秒不變。
- 原件固定於 `packed-index-b595e559/RAW.tar.gz`，逐檔manifest與STATUS另列。**F2正式兩方法、帳本重產、架構、完整整合未完成**；不是READY-TO-MERGE。
- 上游仍阻擋：review時相對base behind2；當前#347 `8bb0359331365c6f3a96872620427cf7847fcb50` behind3/ahead8。#343→#346→#347未閉合；鏈修復後才一般merge精確head、逐leaf審查及受影響重驗。

## 歷史檢查點（下列執行中描述均為當時狀態，不取代上方current state）

# #348 最新檢查點：512 placed load 已過；replay/history 未收終態

候選 F `ac1d8017038ee9563f0cbd8596ea61c8b2577b19` 的原 H7 512 load/dump/objects/references 真 exit0，546.118秒、wait4 RSS293292KiB，低於原每batch600秒；原512幾何、ID順序與dump/reference斷言已過，程序已接著進 canonical replay。完整兩個方法、第二次replay及sequential history仍未收終態，**阻擋2尚未全解除**。原件見 `placed-load-partial-ac1d8017/`；這是部分收件，不能冒完整H7通過。

第一輪 formal 的64三批皆0，但正文Git write-tree觸發歷史物件補抓吃滿/tmp，512收據寫入ENOSPC，原外層1且產品終態未回收，第二方法沒有真正啟動。失敗原件保留。只將本輪自建clean checkout完整搬到SHM、保留原路徑連結，無刪收據/fixtures/Git objects；恢復約324MB。正文發布已改用只修改既有parent的PR_BODY葉、保留遠端既有tree的write-tree --missing-ok，不重抓歷史blobs。20:21:15 UTC於同F的新OUT重跑兩原方法，預先保存每批fixture；不放寬斷言或600秒。

正文分支已推 `07789f8217677d4ac246aac6ad32b3b06fcbafd8`，尚待既有relay回讀。以下較早檢查點及各execution SHA留作歷史：

# #348 最新檢查點：正式 512 驗收執行中

固定候選 F：`ac1d8017038ee9563f0cbd8596ea61c8b2577b19`，已推送可解析。20:08:28 UTC 在獨立乾淨 `/dev/shm/pr348-formal` 啟動原兩個 H7 placed 方法，原分離 K/W/H -O0、16 MiB stack、每批600秒；收據寫 `/tmp/pr348-runs/formal-placed-ac1d8017`，執行完封存。64支load及兩次canonical replay exit0，512第一批仍執行中，**尚未宣告通過**。

- W contact suite：`a22d17c52f97115448160c4c13bfb72e62fd1686`，14 tests／0 failure／0 error／0 skip，exit0；保留41原控制，新增排序/plane具名撤回各0/1/0。
- K source-index suite：F，21 tests／0 failure／0 error／0 skip，exit0；原8控制保留，新增3個具名撤回0/1/0，涵蓋非單調/nested consumer及失敗append。
- F N128 O0-pg診斷11.654085秒、exit0；stdout與原B逐byte相同。profile不能替代原正式600秒；mcount外部成本不能歸作memcpy。完整原件見 `index-fix-20261028/RAW.tar.gz` 及逐檔manifest，靜審另列。
- 候選保留全部ordered edges，只省重複查找；W保留穩定完整uint64順序、單一覆蓋witness和CAPACITY。H局部scope不跨candidate/history。
- 有序source圖比較、正式512終態、帳本、架構、完整整合尚未完成；#343→#346→#347上游鏈仍阻擋。不是READY-TO-MERGE。

以下為本輪較早檢查點，execution SHA各自保留：

# #348 阻擋 2：修復中，未達合併條件

本輪基底 B `9a8584f57be7935604c3bad4c2481945a6ec3d9f`。最新修補來源 C `3420931a4a512f08e3f4d7584958cc8630e190c3`；原逾時、環境錯誤與每版診斷均收在 timeout-diagnosis-20261028/RAW.tar.gz，MANIFEST.json 逐檔 hash／byte 回讀相符。

- **原 B 真實 placed load：600.013933527 秒，exit -9、timeout=true**；wait4 RSS 279492 KiB，stdout/stderr 均空。原 600 秒未變。兩份歷史 timeout 都停在 initial load，canonical replay／sequential history 尚未到達，不能冒稱已各自測出逾時。
- B N128 原 O0 分離 K/W/H 的 gprof：14.914535 秒，exit 0。anchor memo 版 `42e573f59f19693d03f2f4a64bc76a5575b45690` 同 N128 14.166502 秒、N256 127.336561 秒，exit 0；N128 stdout 與 B 逐 byte 相同。這些是診斷，**不是正式 512 通過**。profile 的 child_maxrss 欄包含 compiler 累積，不能當產品峰值；詳 DIAGNOSTIC_LIMITS.json。
- C 新的 scope-local anchor 與借用 host 測試：6 項、0 fail/error/skip，exit 0；六個獨立撤回各有具名 0/1/0。借用 host 的性能尚未測量；K source index／W contact 重複工作繼續修復。
- 正式兩個 H7 placed/replay/history 方法、最終 ordered graph 比較、完整 native/browser、帳本與架構：**尚未完成**。I33 CAPACITY 拒絕與原 timeout 均不放寬。
- 上游仍阻擋：審查時相對 base behind 2；目前 #347 `8bb0359331365c6f3a96872620427cf7847fcb50` 為 behind 3/ahead 8（新增一個 evidence-only 提交）。#343→#346→#347 尚未閉合；未以 evidence-only 差異冒稱上游驗收已閉合。鏈修復後才一般 merge 精確 head，逐 leaf 重審及重跑受影響項。

下一步：修復大量重複資料複製、接觸面順序與 source 索引工作，固定新 SHA，原方法 600 秒內驗證 placed load／canonical replay／sequential history，保留所有紅燈。原 F0f/F73 歷史證據未移標或刪除。
