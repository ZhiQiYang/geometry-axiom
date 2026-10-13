<!-- assembly-acceptance-20261004:start -->
## 2026-10-04 #24 有限收尾／新main整合

[Draft PR97](https://github.com/ZhiQiYang/geometry-axiom/pull/97) 最終head `377440fb0a319463aa1f0f6838b6bd5298c9cd3d`，已整合#85 main `1075058be37d37b98a2a910f4f67b87583be85b3`；未自行merge。
[逐條 A01–A24索引](https://github.com/ZhiQiYang/geometry-axiom/blob/377440fb0a319463aa1f0f6838b6bd5298c9cd3d/geometry-web/docs/ASSEMBLY-ACCEPTANCE-EVIDENCE-20261004.md)。A04/A18/A23已有真UI/native/ZIP覆盖，不重列舊gap；A11固定不同材料/版本/path與不暗升、A12四種只缺face/orientation的合法incomplete配置已補fresh native全state/dump。root要求的exact binding IDs{1,2,3}已加，防空loop。

**同377head實跑full56suites：1678pass/0fail/1具名Windows GDI skip、exit0，frozen匹配，5binary fresh。** 新scene139/integrity88與#85mutation gate保留並實跑；mutationcheck48/0stale/0invalid，crashedM20保留其分類。初次stack8MiB的ac92 full fail保留，採既定16MiB重跑後zero fail。相對新main只3授權files，產品/SSOT及#85全部基準blob不變；相對原20de053測試增量僅1assert。沒有新fullbrowser冒稱。

A10只有現schema拒絕、沒有巢狀求值器；**A24實體iOS/Android keyboard/OSchooser/下載仍未驗，#19/#24保持open**。#25有限D34/I42/R35早已PR53/55合併，不代表任意拓撲。八項本輪採納/各owner/shared接口另由[PR100](https://github.com/ZhiQiYang/geometry-axiom/pull/100)精確回填；#45繼續，不因人工項停止其他cloud工作。歷史段落保留其當時head與狀態。
<!-- assembly-acceptance-20261004:end -->

<!-- continuation-work-package:start -->
## 2026-10-03 後續規格與20:54品質狀態
[Draft PR88](https://github.com/ZhiQiYang/geometry-axiom/pull/88)，完整規格reviewhead `e01d0941fb7baf979cebdf73d8bf2c980d6b814e`；品質／實圖歷史follow-up最終文件head `0800d26d7061c7f602a887f42185b623d83881ee`，文件基底main `9ebf52a1b6519356e9ff677e55b9cf167c47b70d`。PR75 firstbatch已由外部合併，文件merge不等於Q31–Q37採納。

WP24既有A01–23與A24handoff索引核對；#25有限三構件已由PR53/55合併，不再描述為尚未實作。A24實體iOS/OS驗收仍未驗，desktop390px與CI不代替。

**最新優先缺陷狀態**：#78/P1、#79/P2匯入、#80/P2來源定位已由品質owner在9ebf52a真native/Chromium獨立reproduced；root已分派assembly-quality/import/navigation三位隔離產品owner修復中，不是僅排隊，勿另派重做。最新版a274cae尚未重跑這三反例；root另回報PR76合併fullCDP1900/native1551，不能替代缺陷修復驗收。調查exit0代表成功重現，require-contract gate exit1代表未修缺口；本文件worker沒有跑這些產品測試，也未改產品。

[13項工作包](https://github.com/ZhiQiYang/geometry-axiom/blob/0800d26d7061c7f602a887f42185b623d83881ee/geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md)／[Q31–Q37決策](https://github.com/ZhiQiYang/geometry-axiom/blob/0800d26d7061c7f602a887f42185b623d83881ee/geometry-guide/CONTINUATION-DECISIONS-20261003.md)／[#58逐條proposal](https://github.com/ZhiQiYang/geometry-axiom/blob/0800d26d7061c7f602a887f42185b623d83881ee/geometry-core/GRID-SUBDIVISION-RULES-PROPOSAL.md)／[優先缺陷、owner與A→B→C](https://github.com/ZhiQiYang/geometry-axiom/blob/0800d26d7061c7f602a887f42185b623d83881ee/geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md)。

本worker實際：6Markdown、87相對連結/錨點、13包/7未採納決策/9缺陷/2匿名實圖狀態校驗exit0，git diff --check exit0；公理/AGENTS/current_geometry.c/正典閱讀器bytes unchanged。完整規格e01由兩位read-only独立審查通過；follow-up增加品質狀態、已指定scope及CaseA舊版失敗歷史／新baseline待驗分界，產品不變。私人PDF留Library；REAL-PDF-01/CaseA本地0f3c1a6已匯入/323.5cm校準成功，預設vector/image edge-open及width0.1 tooManySegments失敗，geometry不變/0 exceptions，root核對原bytes一致；保留歷史。newhead snap/人工分區/整屋/新main重跑未驗，REAL-PDF-02/CaseB各階段未驗；#47雙向定位取消。本worker不自動關閉issue，Refs不用Closes；本worker無PR merge/部署。
<!-- continuation-work-package:end -->

## 2026-10-03 17:56 UTC 最新main與實際後驗

PR70已由root合併，reviewed `adf5ed4a150f09e8b1e104e16cf5265cb0247d52` → main `d5ea5311c69657376dbfb567f28fe8f5551daebe`；tree d67e80eb完全相同。Root獨立quality actual own-compile full1530/0/1GDI、無filter1855/0/79golden，之後才合併。Worker同main postmerge P8316／料單37／來源29／native18／Node63均0fail/exit0；HTTP292public/205vendor前後bytes/headers與runtime6bd936b25127/fresh/root核對成功，自有服務已停止。沒有hostedCI rerun、部署或用戶本機操作。

PR71 exactdad3e91e3e44c16baf13c24a12d28ddaf457a6e1仍draft，單檔測試器Promise保留修復；原space183/timber79/helper9/獨立10/真GC通過，main70＋71本地整合183＋16＋79也通過，現在由另一agent獨立檢驗最新基底，交root決定merge。PDF校準→房間偵測由另一hotfixthread01a102d4負責，避免競寫。

A24實體手機keyboard/OSchooser/下載與Windowsmanual/GDI仍未驗；完整#47雙向定位、實物去重、assembly-owned／faces+timbers保存模型、F1b durableidentity與F4b加工裁切餘料仍open。#45擴大入口／F2b與#57–62新增來源子規則仍須相應契約／公理採納；不因issue正文放寬。PR52已合併1805bb5，PR53有限D34/I42/R35已合併68c4ac13。較早狀態如下為歷史。

---

## 2026-10-03 16:56 UTC 已完成的雲端切片與精確剩餘

目前main `8993b03b91d27030d210d6478e08764af51385d7`；PR69 reviewed175b308d已合併、同tree且postmain入口16／binding16／料單37／HTTP291+205全驗。PR52早已合併1805bb5；PR53有限D34/I42/R35生成早已合併68c4ac13，不能仍記作未合併／未實作。

已交root審查的两個draft、未合併／未部署：

- [PR70](https://github.com/ZhiQiYang/geometry-axiom/pull/70) exact `adf5ed4a150f09e8b1e104e16cf5265cb0247d52`／base899：單一保存模型明選角材原生快照與核對CSV，一對一既有入口。完整47suites1530pass/0fail/1具名GDI；**無filterChromium1855/0/0skip/completedtrue/79golden**；prod+ASan各121/121、獨立APPROVE。真space183／timber79／binding16／來源29與HTTP292public/205vendor、前後fresh/runtime全驗，最終桌面與390px截圖已看。歷史27/33不被live29/35或missing偷換，模型/context/close/late失效零Blob、連點一次。實際producer目前拒絕assembly-owned savedmodel及faces+timbers，不製造正例。
- [PR71](https://github.com/ZhiQiYang/geometry-axiom/pull/71) exact `dad3e91e3e44c16baf13c24a12d28ddaf457a6e1`／base899：單檔空間testharness復用既有Promise保留工具，避免ChromeGC中途停止；空間183/0、timber79/0、helper9／獨立10、真GC及不重試mutation／cleanup證據通過、APPROVE。與PR70隔離。

兩PR的Actions run37137739059／37138428595七jobs都未執行、steps/logs null，不稱greenCI或產品assertionfail；既有免費quota耗盡記錄，沒有rerun unchanged／付費／改policy。自有測試服務已依root/PID停止，不碰用戶服務。

A24實體手機keyboard／OS chooser／下載及Windowsmanual/GDI仍未驗；整張#47的完整雙向定位、跨表示實物去重、F1b durableidentity、F4b加工裁切餘料、#45其餘grid-source＋boundary／附件／F2b仍open。#57–62的新來源子規則須先採納#58具體差異，現D19/I25/R23單父格及末節全格批次未定案限制保持，不因issue正文放寬。#54他人PR63/64交付保留，不競寫。這些缺口與已完成雲端切片分開。

以下是較早需求／歷史，最新節為目前事實。

---

## 2026-10-03 16:21 UTC 最新已合併 main 與雲端後驗

PR69 已由持有原始 exact 批准的 root 合併：reviewed `175b308d2a2523aa1da81d679d536c7bc5de7905` → main `8993b03b91d27030d210d6478e08764af51385d7`；tree438e1cc35072069f3699b35274d25acef8def153完全相同。合併前完整47suites1499pass/0fail/1具名GDI skip、無filterChromium1839/0/completedtrue/78golden及獨立review通過。合併後同main真P82入口16/0、既有binding16/0、P80/P81料單37/0、HTTP291public/205vendor逐bytes與headers相符；前後runtime68d9a81b76b4b0f571565ffad2c76da5bde83073fe293b8a43154669af7e6a1c/root/fresh正確，自有測試服務已停止。沒有部署或擴大公理。

PR52早已合併1805bb5，PR53有限生成器早已合併68c4ac13；本輪不是只修CI，後續資料正確性與已批准切片已有55/56/63/65/66/67/68/69交付（以各PR精確正文為準）。#25有限D34/I42/R35不代表任意生成語義完成。A24實體手機keyboard/OS chooser/download與Windowsmanual/GDI仍未驗，保留open。Actionsincludedquota耗盡時七jobs未執行，不能稱greenCI；沒有付費或改billing/policy。

下一實作 #47 的單一保存模型原生快照料單 draft [PR70](https://github.com/ZhiQiYang/geometry-axiom/pull/70) 已整合main899；完整非瀏覽器1530pass/0fail/1GDI，當前native production及ASan121/121。正在完成真下載/模型失效/390px及無filter full，尚未宣稱最終全部驗收或合併。

較早狀態／原始需求如下，僅最新節為現況。

---

## 2026-10-03 14:28 UTC 最新 main 與既有配置修復

PR68 經 parent exact-head 獨立審查 APPROVE 後已合併；reviewed `8dc8159ff9f5cee48954db00e6148ca157e14c4d` → main `f52ed1d5cab2486ee8e3ea620dfeeb123ca76c81`，tree `e4527e8febc0ccf928ea2171ecc03814d192a7f9` 全等。完整46套件1478/0/1具名GDI、無filterChromium1823/0/0skip/completedtrue/77golden、真配置UI16/0、space183/0與材質來源79/0已驗；postmerge 新World37/0、真binding16/0、HTTP289/205 bytes+headers/runtimefresh全部exit0，自有服務已停止。

目前 #45 F2a 首個 existing-contract 情境入口正在隔離分支實作，尚未當成功能完成／合併。PR52已合併1805bb5、PR53有限D34/I42/R35生成已合併68c4ac1；不是任意拓樸。A24實體手機／OS鍵盤、選檔與下載仍未驗，總工單保持open，與cloud可繼續項分開。Actions quota jobs未執行不能宣稱greenCI。下列較早main／draft紀錄作歷史保留。

---

## 2026-10-03 13:36 UTC cloud 整合完成／最新 main

唯一 repo ZhiQiYang/geometry-axiom。PR65→66→67 已依後續明確授權順序合併；目前 main `2af20c11203f43fb2ce51b8562958623c6942587`。PR67 reviewed head `e3d3ffc8ffde45e35d273924dcfd41c0bb47e7f5` 與合併 tree `a71f6354c789e43429b5ab48e6b8206ea4ed1a17` 全等：同版完整46套件1462/0/1具名 WindowsGDI skip、完整無filter Chromium1823/0/0skip/completedtrue/77段golden相符；獨立production81/81 + ASan/UBSan81/81、正式來源操作29/0、space183/0、材質來源79/0。新main另以fresh World實測P80/P81 37/0/exit0及288公開路由／205vendor bytes+headers全等；所有自有測試服務已核對停止，未部署。

[PR68](https://github.com/ZhiQiYang/geometry-axiom/pull/68) exact `8dc8159ff9f5cee48954db00e6148ca157e14c4d` 是基於新main的draft，尚未合併：修既有配置create/published-edit/late/repeat對同ID版本但來源內容已更換的守門。完整1478/0/1具名GDI、無filterChromium1823/0/77golden相符、真配置UI16/0、space183/0、材質來源79/0，獨立61/61與額外37/37、歷史對照assert-red。不是新F2a入口／registry完成，未新增公理／schema。

PR52已合併1805bb5；PR55修正已先整入PR53、PR53有限D34/I42/R35已合併68c4ac1，不能再把它記成未實作或draft待合併，也不等於任意拓樸生成。A24實體手機鍵盤／OS選檔下載與Windows現場仍未驗，保留open。最新67/68遠端CI七jobs均未執行（steps/logs null，included minutes2000/2000耗盡），不是綠CI或產品測試失敗。

以下保留歷史與原始需求；當時狀態不覆蓋本文最新事實。

---

## 2026-10-03 cloud 最新精確事實（保留歷史與未驗項）

PR52 已合併 `1805bb585a74f4a5759367aab7ef8de016d96d4d`；PR55 修正先整入 PR53，PR53 的有限 D34/I42/R35 生成已合併 `68c4ac13ec963dae4c9776fb67dac7eff003be06`。不是任意拓樸生成。

PR56 reviewed head `c1bc56675a329d81210265ade69e148cf8825ea3` 已合併 main `693a1c875584a8556b491d3534525a4624ca53c6`；reviewed/merge tree 全等。實測同 head 完整非瀏覽器1393 pass/0 fail/1具名 Windows GDI skip；完整無filter Chromium1809/0/0skip/completed:true、76段 golden matched，raw1僅P38預期注入、未預期0；獨立 space183/0、材質／來源79/0，獨立審查無剩餘P0/P1/P2。postmerge新World P80 23/0/exit0且runtime fresh/root/version核對通過；其他owner已合併PR63/#54與PR64均保留。

A24 **實體手機鍵盤、OS選檔／下载及Windows現場驗收仍未驗**，不能用Linux／390px／綠CI冒稱完成。GitHub Actions included minutes2000/2000已耗盡；run37118444759七jobs未執行（steps/logs null），不是七產品測試失敗或綠CI，未重跑相同CI、付費或改billing／policy。

本工單保持open，保留未完成的A24與原要求；不把有限生成／原生料單 slice 當所有跨場景功能完成。


以下原正文保留原始需求與當時紀錄；其中過去「未實作／待核准／draft未合併」不代表目前狀態，最新精確事實以本文頂端為準。

---
父工單：#19。前置：#20、#21、#22、#23。

本單由整合／驗收 agent 負責，但不能只審文件：發現缺口要在授權範圍內修正並重跑；只有所有相關工作接到同一個正式 app，才可交付第一階段。

## 完整使用流程

在正式畫布使用真 bridge：空白專案 → 空白組構規則 → 角色／member／joint → 局部交换連續方 → 保存未發布草稿 → 真正保存並重開 → 發布版本 → 主副支材料綁定 → 保留不完整綁定 → 保存重開 → 建立第二版本並明選升級／取消 → 復原重做。

不能只用工程 API 建好資料後截圖，宣稱使用者可以完成以上 UI 流程。測試初始化可用 API，但新功能的關鍵操作必須有真實 UI 驗證。

## 原提案 24 項驗收矩陣

全部初始為未執行。每列最終記錄：test file／test name、命令、結果、SHA、artifact、例外或人工狀態。斷言數不當作端到端流程數。

| ID | 情境 | 必須觀察到的結果 |
|---|---|---|
| A01 | 無房間／材料／網格時建立 | 能建立並保存合法草稿，不暗建面／角材 |
| A02 | 空白規則新增角色及接合 | 自訂可用，不只選固定範本 |
| A03 | 交換局部連續方 | 核心定義與示意都變，非只換名字 |
| A04 | 同角色在不同接合採不同配置 | 局部關係獨立保存，不受全域 priority 覆蓋 |
| A05 | 選端面與側面 | 保存型別／固定身份；視圖或游標位置不代替定義 |
| A06 | 同處矛盾接合 | 指出兩個衝突條件，不採最後輸入者勝出 |
| A07 | 角色改名／重排 | 原 slot/member/joint 引用不變 |
| A08 | 刪除被接合引用的角色 | 拒絕或在明確交易解除，不留孤兒 |
| A09 | 矩形框的幾何鄰接環 | 不誤判為求值依賴循環 |
| A10 | 非法定義依賴循環 | 契約可表達的真循環原子拒絕；不為測試擅增巢狀規則功能 |
| A11 | 主副支同材／不同材 | 各角色來源明確且獨立 |
| A12 | 材料或方向未選齊 | 可存合法未完成綁定，不宣稱已產生施工幾何 |
| A13 | 不存在或錯型材料引用 | 拒絕，不補預設或當空欄 |
| A14 | 拖卡片／縮放旋轉示意 | 定義／接合身份／材料對應不變 |
| A15 | 複製規則 | 新身份，不覆寫同名來源 |
| A16 | 修改發布規則 | 新版本，舊綁定仍指原版 |
| A17 | 明選升版後取消 | 原綁定／World／history 不變 |
| A18 | 完整專案保存重開 | 規則全部版本、綁定、草稿和位置保留 |
| A19 | 建立／刪除／改綁的復原重做 | native 和專案資料協調，dirty 一致 |
| A20 | 未知格式／移除必要能力 | 明確拒絕，原專案不變 |
| A21 | 舊 geometry-canvas/1–6 | 舊能力與來源正常，不暗遷移組法 |
| A22 | 自訂規則與舊 D15/I19 不相容 | authoring 不生成非法角材、不放寬底線 |
| A23 | 桌面、390px 建立／編輯／返回／保存 | 真操作可用、無遮擋／失焦，離開守門一致 |
| A24 | 實體手機鍵盤／OS 檔案對話框 | 人工記錄；窄版瀏覽器不得冒充實機 |

A10 若因首版完全不提供某類定義引用而只能在 schema 層拒絕，須明確記錄實際可驗範圍及原因，不能寫成跑過不存在的求值器。A24 未驗可交付待實機驗收版本，但不得宣稱全平台已完成；未驗項保留 open 追蹤。

## 不能漏掉的整合回歸

- 實際編譯目前 core、bridge、model adapter，記錄編譯版本和 binary hash，避免拿舊 binary 測新程式。
- 新核心規則／交易測試，完整專案與草稿測試，原生 `.scene` round-trip。
- 既有 scene cases、引用契約、橋接完整性、參數、工程材料、網格／子格、空間建模／保存測試。
- 完整 `geometry-web/cdp_test.js` 不帶 ONLY/filter；新 assembly workflow 已在完整入口內執行。局部測試可加速開發，但不能取代最後完整回歸。
- 正典同步、`--check` 和 `tests/test_axiom_reader.py`，及規定的追溯／見證檢查。
- 凍結預览→改動其他定義→舊 token 拒絕；切專案→延遲回覆不污染；保存當下有未提交草稿仍保存最新內容。
- 對關鍵守門做至少幾項故障注入／mutation：略過衝突檢查、丟失來源、跳過預覽、把 UI 交換只改文字，測試必須變紅；完成後還原注入版本並重跑。

## 環境與證據紀律

依目前 package.json／tests 文件重現，不僅照抄歷史命令。使用隔離暫存輸出及 `GEOMETRY_FEEDBACK_DIR`，避免污染使用者 feedback。現有 CDP 可能覆寫已提交截圖，測試前後核對並只還原本次測試造成的產物，不動他人的修改。

Windows Smart App Control／GDI、瀏覽器可用性等阻擋與產品失敗分開記；可用已授權 Linux／WSL 跑同原始碼路徑，但不得停用安全設定。沒有真正跑到的測試明列未驗／skip，不能記 pass。

## PR 與操作交付

- 提供開發分支、起始／最終 commit、PR 及變更清單；不直接合併 main、強推或部署。
- PR 不以 `Closes #19` 在未完成驗收時自動關單；先使用 `Refs #19`。
- 一個不含機密的可重開 `.gcanvas` 範例：規則草稿、兩個發布版本、角材組合；來源從正式模型生成，不能手刻假合法包。
- 實際啟動／編譯命令、已核對的連接埠與 UI 點擊路徑，版本可見；不是只有 localhost 字串卻没有啟動說明。
- 在既有文件体系記錄 `ASSEMBLY-RULES-USE` 與 `ASSEMBLY-RULES-VALIDATION`（或對應現有位置）、BACKLOG、DOM-CONTRACT，鏈接實際測試 artifact／CI log。不要把私人 `%TEMP%` 路徑當成唯一供審查證據。
- 每項驗收具有 code/test/record 對應，列出未實作與未驗證。第一階段只涵蓋 authoring＋binding，不是角材生成器。

## 關單條件

- [ ] #20–#23 的結果在同一個可重現整合版本。
- [ ] A01–A23 有逐項證據／經明確說明的能力边界；A24 狀態如實保留。
- [ ] 完整回歸、截圖、console、正式保存重開及故障注入證据可核對。
- [ ] 實際功能、範例、操作文件及審查 PR 交付給使用者；不能交一份未接入 app 的 patch 就說完成。
- [ ] 最終是否合併與標記總工單完成，由專案擁有者核對；沒有被自動關掉的剩餘工作。

## 2026-10-02 已合併證據與剩餘驗收

第一階段 authoring/binding 已由 [PR #26](https://github.com/ZhiQiYang/geometry-axiom/pull/26) 及 [PR #41](https://github.com/ZhiQiYang/geometry-axiom/pull/41) 接入正式 app。以下為已合併 `fd8f38b42bc0eb9eb8ea16595dfc76e83e7bdea2` 的證據回填，不是本輪未提交修改的測試結果。原始需求與未勾選驗收仍保留；本次不自動關單。

[合併後 CI run 36972304794](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/36972304794) 七個 job 全數通過：native 1267 pass/0 fail/1 明示 GDI skip；canvas 1660/0/0，74 golden；assembly 84；grid 138；space 183；timber 79；documents 47。本地同版原生 assembly+ParameterRefs 28/28、Node assembly 三檔 32/32、真 Chrome P77 84/84 的證據亦已保留。

當時待補列（下列缺口已由 #51 完成，最新狀態見本文頂端）：A04 局部交換的 UI/保存 oracle；A13 assembly 專屬錯型與容量負例；A15 MAX 配號與草稿保留碰撞；A18 正式範例逐版本 binding；A23 390px 空白建立完整規則；新 ASan/UBSan；本輪最新 head 的 mutation 注入與還原重跑；驗收文件中舊 PR26 計數改為實際新結果。A10 僅驗首版 schema 拒絕不支援巢狀引用，不聲稱有不存在的求值器。A24 保持 open/人工未驗，不能用桌面窄版冒充實機。#25 有限生成器已有 draft #53；第一階段 authoring 證據不等同生成器驗收，尚未合併。
