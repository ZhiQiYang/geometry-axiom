# 2026-10-26 專案現況唯讀盤點

API 快照共 46 個 open issues，無 PR 混入、無重複；指定 8 張 PR 全部仍 OPEN。這是分流與後續核對清單，不是完成報告，也沒有關閉任何 issue。

目前 main：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。主代理候選 F：`cbf0fb621888596aa14ad5f2349b503e23b1b72d`（只作銜接資訊；遠端 #338 的 head 仍是下表 a6）。

API 原件、完整 argv、exit、UTC、stdout/stderr hash 在每個查詢目錄的 RESULT.json；輸出原件為 stdout.bin / stderr.bin。總查詢分三頁，每頁上限 20；只取指定 PR 的最後一則留言。首次 historical 查詢誤把 issue #230 當 PR，exit 1 原件保留；修正查詢 exit 0。

## 可候選關閉與決定邊界

- **#198 是唯一已找到可供負責人核對的關閉候選**：#202 head 已是 main 祖先、#291 已 merged。這僅證明來源入 main，尚需對照原始反例與現有回歸後由負責人處理。
- 「待核實使用者決定」表示舊提案需對照後續原始批准；不能解讀成使用者一定尚未決定。本輪沒有木工規則推理，也沒有新語意決策。
- 其餘標為驗收缺口，含尚未取得整單完成證據的歷史總工單；不是宣告每一項目前都存在產品 bug。

## 指定 PR 目前狀態

| PR | Head／base 名稱 | API 狀態 | 最新留言時間 | 尚需核對／完成 |
|---|---|---|---|---|
| [#338](https://github.com/ZhiQiYang/geometry-axiom/pull/338) | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77` / `main` | OPEN；draft=true；MERGEABLE | [2026-10-26T06:43:48Z](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6409950139) | 最新審查以 a6 為 checkpoint，列 S10／架構／final F、完整 native、六 browser、閱讀 A oracle 缺口。主代理已另推進新候選 F；本快照不把兩者視為同一受測來源，也不覆蓋已回收的新收據。 |
| [#344](https://github.com/ZhiQiYang/geometry-axiom/pull/344) | `df39d1933402c76b2f8b35ca013412daf16ed4c9` / `codex/train-337-continue-20261024` | OPEN；draft=true；CONFLICTING | [2026-10-25T14:35:16Z](https://github.com/ZhiQiYang/geometry-axiom/pull/344#issuecomment-6398950277) | 完整實際 canvas 撤回／恢復與具名 P53-3/P61-10/P61-11、其他五 browser、native、帳本仍待；strict aggregate 九項不是整合通過。當前 API 顯示衝突。 |
| [#341](https://github.com/ZhiQiYang/geometry-axiom/pull/341) | `823729be5f4f025aebbf02c2dc85e09907c28812` / `codex/geo324-faces-20261024` | OPEN；draft=true；MERGEABLE | [2026-10-24T02:38:34Z](https://github.com/ZhiQiYang/geometry-axiom/pull/341#issuecomment-6378848374) | 最佳化整組撤回與 none/few/dense/overflow 成本／CPU／wall 證據、final native／受影響 timber browser 仍缺；語意反證不是效能驗收。 |
| [#346](https://github.com/ZhiQiYang/geometry-axiom/pull/346) | `eaf15e239324a6464a04740647afccce3a3c17c7` / `codex/geo300-contact-index-20261024` | OPEN；draft=true；MERGEABLE | [2026-10-25T16:38:47Z](https://github.com/ZhiQiYang/geometry-axiom/pull/346#issuecomment-6400283559) | 與上游 #343 來源鏈須收斂；完整 native、六 browser、效能、帳本與架構尚缺。歷史 11 methods／9 controls／83 builds 不移作新 final。 |
| [#347](https://github.com/ZhiQiYang/geometry-axiom/pull/347) | `2e8a6ed20325aa4842dcd0f89eacd598662be598` / `codex/geo300-cut-list-storage-20261024` | OPEN；draft=true；MERGEABLE | [2026-10-26T06:43:47Z](https://github.com/ZhiQiYang/geometry-axiom/pull/347#issuecomment-6409949843) | 先收斂 #346 來源鏈；PF1/PF2/PF3、native/browser、帳本與架構缺口。先前 empty-row 修補不代表整體面材完成。 |
| [#348](https://github.com/ZhiQiYang/geometry-axiom/pull/348) | `9a8584f57be7935604c3bad4c2481945a6ec3d9f` / `codex/issue128-empty-panel-rows-20261024` | OPEN；draft=true；MERGEABLE | [2026-10-26T08:55:17Z](https://github.com/ZhiQiYang/geometry-axiom/pull/348#issuecomment-6412053022) | 先收斂 #343→#346→#347→#348；兩次 N512 全 batch 600 s 原失敗保留，無 partial bytes 不能分派至四命令中的某一命令；完整七項、#297、帳本／架構仍缺。 |
| [#323](https://github.com/ZhiQiYang/geometry-axiom/pull/323) | `4ea6c50796711ed1e79bae89c93d07037d317837` / `main` | OPEN；draft=false；MERGEABLE | [2026-10-23T16:42:08Z](https://github.com/ZhiQiYang/geometry-axiom/pull/323#issuecomment-6369925233) | 2026-10-23 審查所列舊 head 的 N32/base、source calls 比例、負控制與帳本紅燈需與新列車 R8／exact 證據逐一銜接。API 現在 baseRefName=main，舊 retarget 要求不可再記為現況未做。 |
| [#324](https://github.com/ZhiQiYang/geometry-axiom/pull/324) | `4e176e830b691269cc72d021ce7e1bc0b167d621` / `main` | OPEN；draft=true；MERGEABLE | [2026-10-23T17:01:09Z](https://github.com/ZhiQiYang/geometry-axiom/pull/324#issuecomment-6370286270) | 最新留言是承接前一則 ChatGPT 審查的回覆；五 public paths／45 tests 是舊收據。正式 native、六 browser、importers／帳本整合缺口仍轉交 successor；不修改 grok 分支。 |

完整 baseRefOid 保存在 SNAPSHOT.json，並非保證該值就是 base 分支最新 tip。#323 的 base 名稱現在是 main；其舊審查中的 retarget 要求已不能當成目前未做。#338 的舊審查缺口與主代理新 F 收件分開，不重跑已有效證據，也不提前把 F 稱為全綠。

## Open issues 分流

| Issue | 分類 | 核對依據／下一步 |
|---|---|---|
| [#19 [組構規則][AR-00] 實作總工單：無限畫布規則編輯、角材組合、保存與完整驗收](https://github.com/ZhiQiYang/geometry-axiom/issues/19) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#24 [組構規則][AR-05] 完成整合、24 項驗收、完整回歸與可重現 PR 交付](https://github.com/ZhiQiYang/geometry-axiom/issues/24) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#25 [組構規則][AR-06][後續] 由規則＋角材＋配置生成構件實例：先補求值契約再實作](https://github.com/ZhiQiYang/geometry-axiom/issues/25) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#43 [功能提案][F0] 新增功能路線：來源追溯、方案比較、構件料單、圖面證據與規則試驗台](https://github.com/ZhiQiYang/geometry-axiom/issues/43) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#44 [功能提案][F1] 來源／影響檢查器與模型更新狀態：先唯讀追溯，再受控重建](https://github.com/ZhiQiYang/geometry-axiom/issues/44) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#45 [功能提案][F2] 情境式組合入口：顯示可用操作、缺少輸入，銜接 #25 有限構件生成](https://github.com/ZhiQiYang/geometry-axiom/issues/45) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#46 [功能提案][F3] 保存 A/B 候選方案並比較來源、接合與幾何差異](https://github.com/ZhiQiYang/geometry-axiom/issues/46) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#47 [功能提案][F4] 模型連動構件料單：完成尺寸、來源與雙向定位，後續銜接裁切／餘料](https://github.com/ZhiQiYang/geometry-axiom/issues/47) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#49 [功能提案][F6] 規則試驗台與案例庫：正反例、隔離驗證、結果過期與可重用範例](https://github.com/ZhiQiYang/geometry-axiom/issues/49) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#54 [功能提案] 從 PDF／圖片底圖快速取得房間輪廓，減少手動臨摹](https://github.com/ZhiQiYang/geometry-axiom/issues/54) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#57 [網格子規則][SGR-00] 實作總工單：在網格系統定義可重用子網格，跨配置／承載面繼承](https://github.com/ZhiQiYang/geometry-axiom/issues/57) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#61 [網格子規則][SGR-04] 正式來源工作區細分編輯、跨面繼承、選格／選線與手機操作](https://github.com/ZhiQiYang/geometry-axiom/issues/61) | 仍驗收缺口 | #133 已 merged，但 BACKLOG 明列只是第一片；跨面、手機及完整來源工作區範圍不能據此關閉。 |
| [#62 [網格子規則][SGR-05] 24項整合驗收、完整回歸、見證文件與可重現PR交付](https://github.com/ZhiQiYang/geometry-axiom/issues/62) | 仍驗收缺口 | #133 的第一片不能替代 SGR-05 全部 24 項與完整回歸。 |
| [#77 [多房間][MR] 同一 PDF 共享來源基準，連續建立獨立房間邊界與保存](https://github.com/ZhiQiYang/geometry-axiom/issues/77) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#87 [房間辨識][B] 同一底圖頁取得多個獨立房間候選並逐一核對](https://github.com/ZhiQiYang/geometry-axiom/issues/87) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#116 [互動設計][B] 依設計稿整合游標 v2 與情境右鍵選單](https://github.com/ZhiQiYang/geometry-axiom/issues/116) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#118 [工程品質] 盤點結構風險、測試有效性與等待成本，分段改善](https://github.com/ZhiQiYang/geometry-axiom/issues/118) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#123 [UI整合] 依10/04全面審查統一六工作區介面與操作流程](https://github.com/ZhiQiYang/geometry-axiom/issues/123) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#128 [完成面][面材鋪滿] 空間完成面→鋪面材（帶縫／交丁）→比對並反推貼板角材，可選網格對齊鋪排](https://github.com/ZhiQiYang/geometry-axiom/issues/128) | 仍驗收缺口 | #347 空列修補仍 open；這也不是整個面材鋪滿／R10／PF 專項的完成證明。 |
| [#142 [功能驗收][E2E] 全面功能審查與使用者完整操作旅程，缺陷修復後獨立複驗](https://github.com/ZhiQiYang/geometry-axiom/issues/142) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#166 [跨模型審查] 三方判斷都可能偏：只累積可對帳主張，不採信共識](https://github.com/ZhiQiYang/geometry-axiom/issues/166) | 仍驗收缺口 | 跨模型主張對帳是流程工單；未取得範圍完成／歸檔依據，不能把沒有新留言當完成。 |
| [#198 core: classify_rect_outline 以四角計數判定接觸,凹口與尖脊會誤判(GEO-257 同類)](https://github.com/ZhiQiYang/geometry-axiom/issues/198) | 已合入可候選關閉 | #202 head 137427563de2e94e41d067282266c232f176f0d8 已是目前 main 祖先（exit 0）；#291 已合入，BACKLOG 第 25、44 行也記載納入 #202。僅列候選：尚未逐項核對 issue 全部原始反例與最新回歸，不直接關閉。 |
| [#203 [公理][子網格] 平釘天花的板中間支撐：整除保護與 PF-0 排除讓標準 1830 板無法用子網格，需定案依間距上限放支撐](https://github.com/ZhiQiYang/geometry-axiom/issues/203) | 待核實使用者決定 | 舊 issue 要求決定間距上限、整除與 PF-0；2026-10-22～24 的鎖定決策可能已有回答。本輪未核對原始批准，不宣稱仍未拍板，也不自行採納舊提案。 |
| [#204 [公理][端面] 獨立柱：I19 允許端面直接頂柱面、理由「端面不提供固定」與現場不符；主支不可斷開需另行把關](https://github.com/ZhiQiYang/geometry-axiom/issues/204) | 待核實使用者決定 | 舊 issue 的 I19／端面固定提案須與後續已批准 Reading A、RC 面量法逐條對照；本輪只盤點，不新增木工語意。 |
| [#205 [功能提案][下角材模式] 平釘天花一鍵下角材：第一個木工模板需要、規格尚缺的規則](https://github.com/ZhiQiYang/geometry-axiom/issues/205) | 待核實使用者決定 | #333 FIELD-RULES 已合入 main，但完整下角材模式的提案與批准範圍仍須對照；文件落地不代表整個模板功能已驗收。 |
| [#209 [測試穩定性] canvas P78 在慢機器上可能卡住:grid-trial-query 被前端中止後 igTrial 一直不 ready](https://github.com/ZhiQiYang/geometry-axiom/issues/209) | 仍驗收缺口 | #237 等待追蹤已合入的歷史紀錄不等於 P78 慢機器根因已修；保留原 issue 所需重現與回歸缺口。 |
| [#211 [核心穩定性] 原生核心的堆疊用量超過 Linux 預設 8 MiB:subgrid 與 apply-proj 路徑在預設環境會 SIGSEGV](https://github.com/ZhiQiYang/geometry-axiom/issues/211) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#214 驗收耗時分析與不降斷言的加速方案](https://github.com/ZhiQiYang/geometry-axiom/issues/214) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#230 PF23/E1 oracle: distinguish R43 unit input from legal D7 fixture (P103)](https://github.com/ZhiQiYang/geometry-axiom/issues/230) | 待核實使用者決定 | 舊 E1／P103 的 R43 單元輸入與合法 D7 場景區別須對照最新 SSOT 與原始裁決；相關 PF-H 已合入不足以單獨判定此 issue 可關閉。 |
| [#232 ChatGPT 研究工人:工作佇列與進度記錄](https://github.com/ZhiQiYang/geometry-axiom/issues/232) | 仍驗收缺口 | 研究工作佇列屬進度紀錄；本輪未取得完整交付與歸檔依據，先保留。 |
| [#233 PF23/E1 驗收足跡在 SSOT 下無法建立成合法的 D7 場景](https://github.com/ZhiQiYang/geometry-axiom/issues/233) | 待核實使用者決定 | 舊 E1／PF23 場景與 SSOT 衝突屬語意邊界核對項；本輪未驗證後續批准是否已完整解除，不自行更新 golden。 |
| [#239 證據原件發布方式:取代 base64 留言鏡像](https://github.com/ZhiQiYang/geometry-axiom/issues/239) | 仍驗收缺口 | 證據發布流程需核對現有原件與交付制度；本輪沒有逐包審查，因此保留驗收缺口。 |
| [#240 公理層一致性總檢(2026-10-14 多批採納後)](https://github.com/ZhiQiYang/geometry-axiom/issues/240) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#248 [架構] 幾何核心與木工模板解耦(GEO-261)](https://github.com/ZhiQiYang/geometry-axiom/issues/248) | 仍驗收缺口 | #288 已合入 main（API + 祖先 exit 0），但 GEO-261 總工單不能僅憑其中一張 PR 關閉；仍須對照無木工模板建置、後續列車與總範圍。 |
| [#249 [功能][公理] 網格系統直接引用整張參數卡(GEO-262)](https://github.com/ZhiQiYang/geometry-axiom/issues/249) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#252 平行工作窗口 2026-10-15 晚:雲端 Codex 並行進度](https://github.com/ZhiQiYang/geometry-axiom/issues/252) | 仍驗收缺口 | 歷史平行工作窗口的部分列車已合入；尚未對照所有工作項，僅可日後提出行政歸檔候選，不能整單宣告完成。 |
| [#299 V_EXTENSION diagnostic does not name the locating edge and the exceeding interval (I22)](https://github.com/ZhiQiYang/geometry-axiom/issues/299) | 仍驗收缺口 | #338 列車仍 open；I22 診斷改動與跨版本 exact 的批准邊界須沿原始裁決核對，不能把舊 stdout 差異默認放行。 |
| [#300 Raise the timber capacity (64) so a real room's framing fits; unify the five GEO-261 capacity constants](https://github.com/ZhiQiYang/geometry-axiom/issues/300) | 仍驗收缺口 | #348 仍 open；原 N512 兩次全 batch 600 s 超時保留，不能定位為單一 loadfile 失敗；#341/#346/#347 鏈及正式整合缺口仍在。 |
| [#308 Framing oracle: shallow pilasters (29–53 mm) and mid-room wall steps reported unbuildable without a reason](https://github.com/ZhiQiYang/geometry-axiom/issues/308) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#314 Implement the one-axis grid stagger rule (D10b/I24) on every native commit path, including R60 card commits](https://github.com/ZhiQiYang/geometry-axiom/issues/314) | 仍驗收缺口 | #338 列車仍 open；題 3 比較器與禁止本功能修改 K 的反證需沿主代理既有修補來源核對。 |
| [#316 GEO-261 follow-up: dead world_footprint_collides and I11 mutation coverage at the other two same-surface filters](https://github.com/ZhiQiYang/geometry-axiom/issues/316) | 仍驗收缺口 | #338 列車仍 open；已實作的 I11 覆蓋不能代替該新來源的完整驗收。 |
| [#318 Framing oracle builder defects: columns across a wall step pass as buildable but fail checks; build crash when a hole edge midpoint hits another ring's vertex](https://github.com/ZhiQiYang/geometry-axiom/issues/318) | 仍驗收缺口 | #338 Reading A 列車仍 open；final native、六 browser、閱讀 A oracle 的正式缺口以最新審查與主代理新 F 收據逐項銜接。 |
| [#319 Framing oracle: C3 bearing band is clipped at region x-blocks when boards run along Y](https://github.com/ZhiQiYang/geometry-axiom/issues/319) | 仍驗收缺口 | 本輪只取得目前 open issue 原文及歷史 BACKLOG；沒有足以證明整個工單完成的最新固定來源驗收，不能因相關切片曾合入就關閉。 |
| [#320 Web app: recovering the connection leaves the old connection.error, which later blocked edits echo](https://github.com/ZhiQiYang/geometry-axiom/issues/320) | 仍驗收缺口 | #344 仍 open 且 API mergeable=CONFLICTING；strict aggregate 九項通過不等於完整 canvas／六 browser／native 通過。 |
| [#322 GEO-261 follow-up: column/beam snapshot without faces raises unclassified KeyError](https://github.com/ZhiQiYang/geometry-axiom/issues/322) | 仍驗收缺口 | #324 原 Grok 分支仍 open；主代理接手的 successor 需完成整合驗收，原分支不由本工作修改。 |
| [#335 Place two mutually-butting boundaries on a thin wall step (#318 reading A positive B)](https://github.com/ZhiQiYang/geometry-axiom/issues/335) | 待核實使用者決定 | issue 明列 13 mm 薄牆階的相互頂靠邊界為另案；Reading A 已批准部分不等於批次交易／共求值設計已批准。核實原始批准邊界後才可變更該依賴。 |

分類數：仍驗收缺口 39；待核實使用者決定 6；已合入可候選關閉 1。

## Grok 工作範圍

| PR | API 狀態 | 處理 |
|---|---|---|
| [#325](https://github.com/ZhiQiYang/geometry-axiom/pull/325) | OPEN；head `c16f9255383823fa3ce7610c69262905b64c1ff9` | 仍由 Grok 負責；本工作不改其分支或代為結案。 |
| [#331](https://github.com/ZhiQiYang/geometry-axiom/pull/331) | OPEN；head `02086a3689d27d41fbfac470f707e4d6b17b7e70` | 仍由 Grok 負責；本工作不改其分支或代為結案。 |
| [#333](https://github.com/ZhiQiYang/geometry-axiom/pull/333) | MERGED；head `7eaa359063b04a9f02aa72a05aeeca41ab17675a` | 已合入 main，祖先檢查 exit 0；FIELD-RULES 文件落地不等於 #205 完整功能已完成。 |

## BACKLOG 日期與可接續小步驟

目前 main 與候選 F 的 BACKLOG.md 是同一 blob `610cd00186e7a11e1401f8c39dd7ab187dd80870`，內容 SHA-256 `ecfa7d3e3fa9895792f26ad47c51cafb6e2a95425b041205bc69983f2d50de50`。頂端是 **2026-10-19 歷史快照**，當時 #288 尚未合入、#300 尚未開始的文字有日期上下文，不能直接抹除。第 9 行也明定該輪只新增、不改舊文。

可把本快照交給 #325 的負責人，新增「2026-10-26 現況核對」節，連結本 API 原件，記錄 #288/#333 已合入與 #338 等待完成的現況；保留 10-19 原節與歷史失敗。這是建議，尚未修改 BACKLOG。另可在不跑重測試的情況下，逐一對照 #198 原始凹口／尖脊案例與 main 既有測試，再提出帶來源的關閉候選說明。

## 邊界

- API 是 2026-10-26 10:53:57～11:00:35 UTC 的非原子快照；沒有逐 issue 下載全部留言，故不得宣稱完整語意／批准審核。
- latest-comment 只取各指定 PR 最後一則；#324 是回覆，並非本輪直接重新取得它引用的較舊完整審查。
- API mergeable 只代表機械可合併性，reviewDecision=null 不是批准，也不等同 READY-TO-MERGE。
- GitHub PR baseRefOid 原樣保存；它可落後於 baseRefName 現在的分支 head，不把舊 baseOid 誤稱當前 main。
- API 留言作者欄與同步文字不自動構成新的使用者批准；本快照不裁決 exact／P-189 白名單。
- main 祖先判定不是該 issue 全部驗收；只有 #198 列為供負責人複核的關閉候選。
- 未執行編譯、重測試、清理、fetch、push、PR 或 issue mutation；只讀 API 與既有 Git objects。
- 第一次 historical-and-grok-status 因把 issue #230 當 PR 查而 API exit 1；保留原失敗與修正後 exit 0，這是盤點查詢錯誤而非產品失敗。
