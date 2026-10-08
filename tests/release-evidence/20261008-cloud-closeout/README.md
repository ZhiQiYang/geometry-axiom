# 整合候選：已完成部分與精確未完成項

**本候選仍是 draft，尚不可整體合併；本階段没有收尾完成。** #171 ownership 拒因與資料不變 oracle 已補齊，#174 過期 projection 清理原情境已過；#173 新交付已接回，但原探針在整合候選仍有 4 個失敗。held-bhit、安全完整Resume、#123既定介面差距、#54完整修正路徑的降成本目標也是產品工作，不改稱只剩 CI／裝置驗收。

- main：`5cc1ffa1ee85120eca14258b86b715151cad274f`；[發布後快照](report-support/post-pr176-remote-summary.json)在 `2026-10-08T18:59:48.201950+00:00` 核得32 PR／27 issues。新增本草稿#176；先前唯一來源head變動是#173的純文件181fc。19:23發布前核對全部32個PR head與main均未變；當時只有本次已發布的#137摘要更正；#153/#155正文後於19:36更正，head未變，另有GET收據。最後補測後再核對（2026-10-08T20:16:21.859988+00:00）：main與全部PR heads未變，32 open PR／27 issues；[原時點摘要](report-support/remote-after-contract-gaps-summary.json)。來源核對窗口非原子GitHub快照。見[發布前核對](report-support/pre-publication-final-summary.json)。
- 乾淨產品候選：`5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，分支 `codex/integration-closeout-20261008-r2`；已推送，於 `2026-10-08T18:38:35.231195+00:00` 核遠端同 SHA：[命令](report-support/verify-product-push.json)、[ls-remote 原輸出](report-support/verify-product-push.stdout)。這不是最終證據／文件提交或 PR 發布證明。
- 原43筆 gate 終態以[凍結閘門矩陣](gates/matrix.md)及[matrix.json](gates/matrix.json)為準；最後條文核對的新限定補測另見[補測附錄](contract-gap-probes/verification-addendum.md)：每列連 canonical結果、命令、before/after clean、runtime／bridge、腳本／raw hash、退出碼。[報告整理時索引](report-support/receipt-index.json)只保留歷史458 full CDP及最早11筆5174 gate快照，不是另一份最終matrix。本次43筆閘門紀錄已完成核收；失敗與退出碼unknown的環境中斷仍獨立保留，不將assertions或輪數當成果。
- 已建立唯一整合草稿 [#176](https://github.com/ZhiQiYang/geometry-axiom/pull/176)，base 為 #169 的 `codex/final-release-closeout-20261008`。本報告隨文件／證據提交交付；[来源同一性](report-support/publication-source-equivalence.json)及[最後提交前逐blob核對](report-support/final-source-equivalence-precommit.json)確認5174之後只有指定文件／證據路徑。包含本報告的最終完整commit、遠端與新head CI／私有queue觀測，記於#176正文的發布收據，避免將未來自身SHA倒填受測結果。未合併 main、部署或改公理／權限／安全／付費設定。#168 取消、#169 未批准的 review comments 維持暫停。

## 版本、範圍與責任

初次盤點31 open PR、27 issues；28個原PR head已含候選，發布#176後為32 open PR。#141全部9檔在#146均逐blob相同：7份實作／測試＋2份文件；候選後來只改其中2份文件，不重套舊實作。#129／#157 提案不當已採納功能。[全部 issues／PR 的具體下一步](report-support/intake-next-steps.md)、[原包含性](ci-source-audit/audit.json)、[依賴](ci-source-audit/lineage.json) 均保留核對時點；包含性不等於批准合併。

| PR | 已接回完整 head | 判定 |
|---|---|---|
| #169 | `a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e` | 既有整合來源；review comment 暫停。 |
| #170 | `ce0958ca700753172338fe291a17e781da89465a` | 原乾淨版本 GRID 346／0、P88 中 137 限定證據有效；文案／hash 更正不要求同版重跑，也不是完整產品驗收。 |
| #171 | `fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d` | fresh-process 明確核 I42、拒絕後 dump／assembly-read 不變；正式規則線保存重開已接回。 |
| #172 | `f8225f767d969e30683a7de99270bbaff4535b5e` | 來源審查報告，不是 #174 產品修正或 browser pass。 |
| #173 | `181fc76049b2b2d001957d2ee0008448bbf5b024` | ce74產品由7467ebd接回；181純文件由`d8642b2e684038cbb8e24aba057c44e7aac1b231`接回。原16探針在clean5174為12 pass／4 fail。 |
| #174 | `5083a456b1caff33fbc56c5fa10927582432a283` | expired projection 清理已過；held-bhit 晚回覆仍有真 browser 失敗。 |
| #175 | `1127531f3aab472e01a4a99c03ef7b739b1b8ae5` | 命令、文件與限定證據索引，不是新產品功能或完整驗收。 |

root 持 Git／整合／推送責任；browser 與大型測試串行，證據及獨審唯讀並行。#175 來源記載 #174 owner 已結束且乾淨；#173 對 `app.js`／`space-workspace.js` 的停止／交接仍未確認，不因「草稿留給整合」推定已釋放。雲端不假裝看到本機程序，不競寫這兩檔。root 的 5174 只修 #123 C2 既有梁色 token、C4 空槽 action 可見性，沒有新增 DOM／handler／入口；desktop梁色／空槽、390梁色及既有inspector入口的390空槽已有有界通過證據；390雙擊入口缺陷另列。

最新 #173 `181fc76049b2b2d001957d2ee0008448bbf5b024` 是 ce74 的直接子提交，只新增四份 full-ui 收據文件，產品／可執行測試同值；**在5174主回歸完成後以d8642b2接回文件；最後條文缺口補測另直接綁定clean d864**。作者新 Windows `1692/2` 中止輪只交原 full log 的本機 hash，原 534908 bytes log 仍 unknown，不當獨立通過證明，也不因 docs-only 更新重跑同版範圍。[遠端核對](report-support/latest-remote-summary.md)。

## 已有有界合併依據的成果

| 成果／實跑版本 | 行為與證據 | 限制 |
|---|---|---|
| #152 adapter，`bdd1bf7812ba6126aab9ddffced43cd200ac977e` | 重複 PR observation 不再丟 task 事件／造錯來源新版；修前 2 fail，修後 suite 144 pass，獨審來源／repository／SHA 邊界。[摘要](work-manager-summary.md)、[審查](inventory/adapter-review.json)。 | 不覆寫別源、批准、scope；非 Geometry 驗收。 |
| 工具 UI，`3a48cf5bacb9a295e15046e5ca0cb021e50c54db` | W19、鍵盤、狀態、匯出後新 store 恢復、beforeprint／PDF。原 75 排除 2 空泛判定，保留 73 有效；另 16 最小 future 篩選分開。 | 不改綁 5174；非 OS print／真手機。 |
| 新私有 ledger v1→v5 | v5依實際來源冪等匯入完整32 PR／27 issues，含#176 clean5174；重複新增0、source_updated false、DB bytes不變，reconcile／list-ready／list-alerts同hash，59 read-only／write0。[摘要](work-manager-summary.md)、[私存hash](work-manager-private-receipt-hashes.json)、[獨審](report-support/queue-v5-independent-review.json)。 | v4與既有owner／批准／審查保全；30個不變head保留原CI核對時間。非舊DB恢復、非派工；v5觀測截止18:59:48，之後純證據提交的精確head另追加私人觀測，不倒填v5。 |
| ownership／規則線 probes，3a＋dirty diff；腳本最終 `9a4136da264249f76ba08258a7f14be926f96a95` | fresh load、I42、拒絕前後 dump／assembly-read 相等；合法 grid／face／正式角材修改、Undo／Redo、保存、reset 真空、load 完整引用；no-op 負控制失敗。[binding](contracts/closure-contract-binding.json)、[獨審](contracts/independent-probe-review-final-followup.json)。 | 不改稱 clean 9a／5174 實跑；canonical #171 由 full native 另驗。 |
| 真 Save／New／Open，clean `458779f003e1f57fdc0f4420564a0b295227843e` | grid／assembly ×1400／390 ×scene／gcanvas 共 8 閉環，先完整清空再真選檔，比完整 World／引用／assembly／封包；12 次重開後 member 拒刪均 I42，資料及 revision 不變，exit 0。[摘要](contracts/browser/browser-save-reopen-execution-summary.md)、[獨審](contracts/browser-run-02-independent-review.json)。 | fixture、拒刪用 API；非 UI authoring。無非空 models／typed drafts 綜合 fixture；非 OS dialog。 |
| held-proj，clean 458 | 扣 A 真 proj→B 畫好→釋放 A，兩寬 B 保持 5 handles／1 group、選取／World 不變，exit 0。[原件](async-new-head/README.md)。 | 只解除已修 projection 情境；bhit 仍失敗。 |
| full native，clean 458 | `python3 tests/run_all.py`、process-local 16 MiB stack：83 suites、2594／0／1 Windows GDI skip，exit 0。[receipt](native/full-run-all-new-owners.json)、[raw](native/full-run-all-new-owners.stdout)、[suite logs](native/new-owner-native-suite-raw-logs.tar.gz)。 | [458→5174 來源審查](report-support/native-source-impact-458-to-5174.json) 核 native/core、83 登錄與實讀 slices 未變；不稱 5174 重跑。9a 2593／0／1及初次 8 MiB 失敗均保留。 |
| full CDP，clean 458 | 無 filters／modifiers，completed true，2207／0／0 skip、84 段 golden 全符，exit 0；1 次具名預期 P38 探針例外、0 非預期。[receipt](gates/full-cdp-r2/receipt.json)、[raw](gates/full-cdp-r2/command.log)、[獨審](report-support/full-cdp-r2-independent-review.json)。 | 不是 5174 full CDP；9a 紅燈原輪保留。批次 controller 137 不改已完成 child gate 的 0，也不證後續已跑。 |

#162 ABC `8b9b6f80078c17238286e43da54b751e8d3b5b23` 已交付且原證據曾獨立核對，歷史 10／155 缺件另列。458 的 P5 只修同一目標可命中座標前置，單次 drag／等待／oracle 未改；P88 107→137 是新增 30 項，原 107 未刪，總數 2177→2207；grid native 40→41 有新增 case 依據。不把失敗輪轉綠，不把 assertions 相加成使用情境數。

## clean 5174 的閘門與剩餘範圍

[閘門矩陣](gates/matrix.md)已凍結已完成原件，不在本頁複製會過期的總數。已收 Space／timber、限定 async／synthetic grid reopen、save-roundtrip／model-history、scenario lifecycle/workflow、single-room及 #116／#77／reader 等範圍；每項只能沿該列原件判定。command-only wrapper 的 exit 0另以實際結果檔／raw census核對；完整Space不包含timber／專用async，既有async不含新held-bhit，scenario保全／Finish不等於完整Resume。

keyboard 原輪因環境斷線未完成：373筆觀察、1 unexpected／browserDisconnected／fatal，無release receipt，退出碼unknown；新版 room-keyboard-r2有完整396／0原件。兩輪分開保留，不把環境中斷當原版產品通過，也不刪失敗輪。

原始command中的暫存路徑保留為執行身分；[可重現命令](commands.md)明列隔離checkout、fresh native、sandbox、原名依賴與合法fixture，不要求新環境假裝繼承私人Temp。[#137摘要更正](report-support/pr137-summary-correction.json)已發布並GET核對：舊9a紀錄完整保留為歷史，現在head3897與Resume未完成明示。[#153／#155更正](report-support/pr153-pr155-summary-corrections.json)也已發布且逐字GET核對：原正文完整保留，只新增5174整合證據，不改綁PR原head；#54效率未證成明示。均未送review comment。

原服務 runtime `82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200`、session `86b719350c9d4e3b90536403b05f9dcc`。環境返回後原服務消失，原因未定；既有 raw hash 已重核，不宣稱其 final in-memory World 恢復。新隔離服務同 runtime、session `ca31be77efb542b89d45d5a88c3b1b45`，已再證 HTTP／sandboxed 真 browser：[入口](report-support/environment-return-browser-run.json)、[live bridge](report-support/environment-return-live-service.json)。入口成功不算產品驗收。最後產品測試全部結束後環境再次返回，18971已拒絕連線；[實際命令與exit1](report-support/final-environment-return-identity-r2.json)、[stdout](report-support/final-environment-return-identity-r2.stdout)保留。此時HEAD仍d864且乾淨、raw與待交付檔仍在；不宣稱ca31服務仍活著或in-memory World已恢復，也不因此重跑已完成範圍。

| 後續工作 | 本快照狀態及下一步 |
|---|---|
| full-cdp-r3 | **PASS，已獨審**：clean5174完整CDP，2207／0、completed true、84段golden相符，無filters／modifiers／skip，command／gate／controller皆exit0。唯一P38刻意注入例外，0非預期例外。[原件及獨審](gates/full-cdp-r3/independent-review.json)。新async與390缺陷不因full綠燈解除。 |
| 其餘既有 gates | **已執行並獨審**：rule-cases、rule-case-races、multiroom、section-profile-ui、q38-save-roundtrip、shared-room-display、evidence-formal、grid-raw-provenance、feedback-resize-observer逐列均exit0；語義／排除項及各原件見matrix。 |
| 6 owner/module gates | **已執行並獨審**：六個command/gate均exit0，結果見matrix獨立分區。scenario-grid-owner、scenario-module-browser、evidence-component-browser、rule-case standalone controller／browser、create-feedback-ui，與formal app gates分開，不以元件結果替代保存流程。 |
| native-context-300 | **已執行並獨審**：真HTTP/native 300個唯一session、修改及退休；9個具名判定通過，原World/revision及原子程序保持，command/gate exit0。 |
| 綜合非空專案與 Q38 服務重啟重開 | **已執行並獨審，原件在matrix逐項列出**：compound兩寬真正清空／fresh-profile Open，非空模型、未發布草稿、完整World／引用／實例與重開後I42不變；scene只恢復正式World。Q38同版18-check producer後，自有服務停止／重啟，原13個oracle通過。兩個command/gate皆exit0。 |
| CSS C2/C4 | desktop梁色與空槽pass，390梁色pass；390空槽以既有可見inspector入口通過click／Tab／Enter及資料不變。第一下選空間後重排、第二下命中縮放按鈕的雙擊失敗仍保留。各原輪、observer修正與替代入場路徑分列於[CSS證據](css-c2-c4/README.md)，不將雙擊輪改綠。 |

## 仍阻塞合併的產品工作

| 項目 | 已成立觀察 | 唯一 writer／QA 的解除步驟 |
|---|---|---|
| #173 replacement 拒絕殘值 | clean 5174 原 16：**12 pass／4 fail，exit 1**；main／face ×1400／390 replacement-rejected-value 留 `2000`，模型／default `4000`，完整 World 不變。同 input 新值、replacement 新值 `5151`、成功時未送 sibling `4242` 已保全。[原件](async-edge-ce74/README.md)、[獨審](report-support/pr173-ce74-replay-review.json)。 | 修輸入／提交世代，只消該拒絕提交殘值、不清新稿；重播原 16，不調 oracle；三視圖另收新 8 獨審。作者新 26／0 已取得並[審查](report-support/pr173-ce74-source-evidence-review.json)，有限值穩定等待不替代原探針 callback terminal；更早 13／1／1 缺件分開。 |
| #173 成功套用／三視圖晚回覆 | [新8情境與獨審](async-transition-ce74/README.md)：4個普通4200成功套用pass；4個扣A成功回覆→真進B三視圖Edit→釋放A，只有B editToken `2→3`，手把仍5→5、形狀／edit model／完整World皆不變。依原ownership oracle仍fail、exit1；不是丟手把或污染資料。 | 唯一writer審共同emitter／refresh歸屬；保留token失敗與舊raw。來源可重設B瞬態編輯，但此輪B靜止，live drag／draft實際影響尚未觀察，不擴大宣稱；不只為取綠重播不變stationary案例。 |
| #174 held-bhit | clean 458 真 pointer：A pointer-down 扣 bhit、pointer-up 已結束，view→B edit 畫好 5 handles，再釋放 A；兩寬 B 5→0、stale editDrag 復活，World 不變。[原件／獨審](async-new-head/README.md)。5174 對應 canvasDown 未變，不稱 5174 重跑。 | await 後同時核 edit 世代／工作面與存活 pointer gesture；修後重播 bhit、保留 proj pass；若宣稱 gesture lifetime 修復，補 same-edit early-pointer-up。相鄰 await 來源疑點不虚增為已重現。 |
| 完整安全 Resume／#137 | checkpoint、exact ticket、B namespace／lock、捨棄／Finish 已接回。同步 metadata 改後 IDB 尚未 durable、World 指紋可相同，不能恢復舊 metadata。[範圍獨審](report-support/resume-independent-review.md)。 | root 協調 app/space 唯一 writer，先定 epoch 狀態機及修改前 durable 資格；同一交付完成 exact resolve、完整 snapshot／ticket、metadata-only attach，涵蓋同步 setter、local Undo／Redo、底圖／draft。保留安全阻擋；單加 status endpoint 不算 Resume。 |
| #123 既定介面 | [43 列矩陣](inventory/123-current-matrix.md) 非43個現行確定失敗，也非全缺附件。C2梁色／C4空槽CSS已入5174，四個限定範圍已有browser證據，390空槽使用既有inspector入口；其他token／header／料單位置／構件分段／網格控制／S4 240px面板仍有既定差距。 | 逐項核現版來源、正常click／Tab／Enter，修有依據共同原因；不競寫app/space。附件只阻原稿比較；既定差距不移新提案。 |
| 390px 空間卡片雙擊入口 | clean5174 slots fixture：第一下正確選space:1，重排後同座標第二下被#btnZoom接住，focus保持null；真正等待30s失敗，無pageerror。這與同輪已通過的梁色CSS無關。 | app/layout writer保全兩下之間的可操作目標，修後重播原同座標雙擊；不能把縮放按鈕加入允許區或以強制點擊跳過。替代inspector入口只能補空槽驗收，不解除本缺陷。 |
| #54 單房完整流程成本 | [逐條來源及兩套實測](report-support/final-contract-mapping/room54/README.md)：完整修正／逐邊核對協定，候選21／27／33動作，手繪16／20／24；較輕P79單邊核對為7對12／14／16，門洞備援14對12。協定不同，不能只挑較低數或由功能pass推整體效率。 | 單房產品writer依同起終點與同核對範圍分解多出的操作，做有界減重後再量；不新增多房／新公理。比較要求已存在，不能改列等待新判準；最低幅度與真人樣本未定，不自行捏門檻。 |
| 其餘既定操作 | 2a #130／#133、#116 的 #125 已在 main；#54 單房，#87 已授權切片獨立。 | 本次必要cloud gates已收終態。逐issue條文映射與未完成產品步驟见清單，不能以suite數量關父單。 |

## 最後條文核對與限定補測

[#62／#24／#54條文映射](report-support/final-contract-mapping/README.md)保留補測前所見範圍；[新補測附錄](contract-gap-probes/verification-addendum.md)另記後續結果，沒有將缺證寫成已失敗產品。補測實跑head為clean `d8642b2e684038cbb8e24aba057c44e7aac1b231`，只比5174多#173四份收據文件。已獨審核收：SR18在合法正對照後鎖定D17/I21角色拒因與完整資料不變；SR15原生參數／anchor修改、兩面guide/direct引用、cancel／Undo／Redo及精確非法拒因；SR16／SR23桌面與390的真UI先第一面引用再第二binding，非法第二面整筆拒絕、合法更新、Save／New真空／fresh-profile產品Open，以及重開後Undo／Redo完整閉環。API只建立明列的boundary／placement／support前置。SR16實際拒因為R6/I5/I6，兩輪封包實際為format/11，不冒稱另一型別／版本。SR15 r1錯誤預期只列改動binding的失敗保留，r2改按來源核完整before/after與固定幾何值，未弱化產品契約。另在隔離instrumented bridge完成ASan／UBSan基線54個原測試（45個native程序），以及#62既定五類故障注入；五項都由原始語義assertion擋下，逐次同路徑還原後原測試恢復通過，未見sanitizer異常。原執行器因M1/M3只釘直接拒絕第187行、漏列現有preview拒絕第189行，保留整輪exit1及兩筆OTHER分類；獨審用精確非法整除／跨來源操作和還原正對照補述語義，不把任意error/crash算有效攔截，也不改測試或重跑取綠。這不復原歷史152原件、不宣稱非法preview已被確認寫入World。SR06遞迴及SR14重排不據舊矩陣新增v1排除／未提供的操作。A24與SR24實機仍待裝置QA。

## 外部驗收、缺件與排除項

| 條件 | 由誰、做哪一步解除 | 邊界 |
|---|---|---|
| CI 未啟動 | Repo帳務管理者處理既有付款／spending-limit；維護者重跑最終精確head，查runner／steps。 | 歷史31 runs／217 jobs、後續新heads均按原時點記未執行。[#176精確5174 run37828361927](report-support/pr176-5174-ci-summary.json)七jobs也是runner0／空steps、帳務未啟動，非產品pass/fail。未改帳務；最終文件head另查。 |
| Windows full CDP／GDI | Windows QA 對最終候選交完整 raw／exit／native 來源。 | Linux full 不替 Windows P70／P88。舊 #173 `1623/2, completed:false`（P5＋P73 fatal）及新181文件記1692／2中止輪都非平台通過；完整raw缺，仅有本機loghash不替內容。GDI為Linux native唯一具名skip。 |
| 真手機／IME／OS chooser、print | 裝置 QA 用確定候選及 fixture 真操作，留裝置版本及結果。 | 390px、synthetic composition、download fallback、beforeprint／PDF 不替代。 |
| #123 原附件 | 持有者交可讀 ZIP／附件及 hash，QA 比指定原稿。 | 不解除既定 UI 差距，不阻已有來源的修復／操作。 |
| 本機交接／歷史原件 | owner 交 full SHA、dirty diff、修改檔案、停止／責任；持有者補歷史 10／155、早期 #173 13／1／1、#152 舊 DB／66 raw。 | 新 #171／#174／#173 ce74 probe 已取得，不再全列 unknown。新 ledger 不冒稱舊 DB 恢復；edge／bhit／Resume 本身仍是產品未完成。 |

未定案／下一階段只含非空跨專案 ID 碰撞、引用重寫及歸屬政策，PF-0／#129／#157 未採納提案，F4b 裁切餘料等未定範圍；不能由願景改公理。既定保存／清空／同包重開不受阻。**完整 Resume、#123 既定差距仍屬本階段；#87 是獨立已授權工作。**

公開包只放合成原件、程式、摘要及版本索引，保留失敗輪。公開包不含私人queue／owner thread、完整traces／profiles或native binary。已取得的本輪私有證據位於 `/workspace/closure-evidence`，native binary／sidecar在 `/tmp/geometry-tests` 並有私有備份；#123原附件及歷史缺件仍未取得。有hash不等於已同步或公開可恢復。本輪雲端私有交付尚未同步回本機owner，不假設環境長期保留；接手者須在環境可取得時按原路徑與hash領回。[舊矛盾修訂狀態](report-support/stale-doc-corrections.md)：RELEASE-CANDIDATE現況及#137／#153／#155正文已更正；#175-owned INTEGRATION-GATES兩處仍交owner，不競寫。

交付依賴順序為 **#169 → #176**；已含來源heads不重複合入。最終發布只新增本證據包並修訂RELEASE-CANDIDATE；受測產品維持5174，不將舊收據改綁文件head。提交後的完整SHA、遠端一致性、clean status及精確head CI／私有queue更新由#176正文與私人發布收據記錄。公開證據可從该提交取回；私有資料及歷史缺件保留上述界線。已驗切片可供有界合併審查，但整體候選仍受列出的產品與交接阻塞，**不能稱只剩外部驗收或收尾完成**。
