# 優先缺陷與驗證收斂佇列：2026-10-04

使用者20:23要求把 PROJECT-REVIEW-20261004.md 的具體問題排入工作排程，優先於一般新功能。原報告已從 Library 完整讀取（137行、12246bytes），查核基線 `9ebf52a1b6519356e9ff677e55b9cf167c47b70d`。本文件是可接續修復規格，**不是缺陷已由此worker重現、修復或驗收**；原作者的測試結果僅作來源證據，不合併成此文件head的回歸結果。

本輪只改文件／工單，依現行[公理](../公理層.md)、既有契約與[工作包](CONTINUATION-WORK-PACKAGES-20261003.md)界線。#78–80已由parent品質執行者在9ebf52a真native／Chromium獨立重現；root已分配三位隔離產品owner：assembly-quality、import、navigation，均以draft供root審查，本worker不另派重做或競寫。既有#47雙向料單—模型定位已取消，QR3修復現行live來源locator，兩者範圍分開。PR76已由root合併a274cae，PDFsnap產品不接管。

## 20:54 品質證據更新

已完整讀取品質獨立報告INDEPENDENT-REVIEW-THREE-9ebf52a.md（79行），報告與可重跑公開合成artifact均已留Library供root/修復owner使用。前三項狀態為**reproduced／修復中**，不是待重現，也不是fixed。使用新編bridge、真HTTP/Chrome圖片解碼/正式UI，非原作者VM或舊binary：P1正式預覽漏92、confirm1973→1960及x514→520；P2縮排誤拒、delete後附件接受且下一包sources0；P2來源真定位進10未選7，工程adapter對照進20選7。調查exit0表示成功重現，require-contract gate exit1表示缺陷仍在，不能算修復pass。

獨立重現head只到9ebf52a；**新main a274cae尚未重跑這三個反例**。root另回報a274cae的full CDP1900/native1551為PR76合併驗證，屬root執行證據，不能代替前三反例修復验收或冒稱本worker產品測試。每個產品owner須在自己的最新main＋patch記新的exacthead/closure與oracle，再交root；不merge／部署，不操作用戶正在描圖的本地服務。

## 實際可執行順序

1. QR1確認影響完整性優先；QR2候選物件驗證、QR3型別導航可獨立重現，產品共用app/reference接口由一位整合owner接線。
2. QR4先恢復helper保護，QR5逐條退休歷史UI遷移、QR6資料派生count；同reader/sync owner合併，維持唯一正典與五assert。
3. QR7固定binary內容身分，QR8盤點有效變異並重跑，之後接既有驗收入口；QR9驗收漏群組守門低優先。
4. [自動房間A→B→C](#auto-rooms)依序改善，與原新功能工作包同列；Q31–Q37仍未採納。實體iOS待驗只阻擋對應人工驗收，不把雲端規格／反例／修復全部停住。

| 包／工單 | 優先 | 下一個最小切片 | 本輪取得的證據／剩餘 |
|---|---|---|---|
|[QR1](#qr1)／[#78](https://github.com/ZhiQiYang/geometry-axiom/issues/78)|P1|組構確認預覽須包含外部角材依賴的完整幾何影響|已獨立重現9eb；assembly-quality修復中；新a274反例未跑、未fixed|
|[QR2](#qr2)／[#79](https://github.com/ZhiQiYang/geometry-axiom/issues/79)|P2|匯入附件引用須以原生候選最終物件核對，移除宣告掃描|已獨立重現9eb；root指定import owner修復中；新a274反例未跑、未fixed|
|[QR3](#qr3)／[#80](https://github.com/ZhiQiYang/geometry-axiom/issues/80)|P2|來源定位保留 placement 身分，避免同 boundary 多放置時進錯面|已獨立重現9eb；root指定navigation owner修復中；新a274反例未跑、未fixed|
|[QR4](#qr4)／[#81](https://github.com/ZhiQiYang/geometry-axiom/issues/81)|P2|閱讀器 force marker 分支返回前完成補丁登記|完整讀取報告＋工單；產品未改，本worker未獨立重現|
|[QR5](#qr5)／[#82](https://github.com/ZhiQiYang/geometry-axiom/issues/82)|P3|閱讀器去除重複見證 handler，逐項退出已完成 UI 遷移|完整讀取報告＋工單；產品未改，本worker未獨立重現|
|[QR6](#qr6)／[#83](https://github.com/ZhiQiYang/geometry-axiom/issues/83)|P3|閱讀器可見條文總數改由 clause-data 派生並納一致性檢查|完整讀取報告＋工單；產品未改，本worker未獨立重現|
|[QR7](#qr7)／[#84](https://github.com/ZhiQiYang/geometry-axiom/issues/84)|P2|native binary freshness 核對內容雜湊，收斂到既有版本機制|完整讀取報告＋工單；產品未改，本worker未獨立重現|
|[QR8](#qr8)／[#85](https://github.com/ZhiQiYang/geometry-axiom/issues/85)|P2|恢復現版 mutation inventory 與 freshness，接回既有驗收入口|完整讀取報告＋工單；產品未改，本worker未獨立重現|
|[QR9](#qr9)／[#86](https://github.com/ZhiQiYang/geometry-axiom/issues/86)|P3|獨立 space 瀏覽器驗收補逐群組數量基準，避免整段漏跑仍綠|完整讀取報告＋工單；產品未改，本worker未獨立重現|

## 共通交付契約

每個修復只沿已有求值／候選／identity／驗收機制收斂，明寫刪除了哪個錯誤假設或重複責任。只搬檔案、補特殊case、增加test數量不算完成。正反例在隔離World／服務／TEMP，公開夾具為非機密資料；PR要附exact head、命令、exit、oracle、未驗範圍，不能借舊綠CI。cancel/invalid/stale/contextswap守門與dirty/history必按真效果核對。無自動merge/部署、安全設定變更或付費。

<a id="qr1"></a>
## QR1 — P1 / #78 組構確認預覽須包含外部角材依賴的完整幾何影響

**報告反例**：27×33 三構件生成主支1/2，普通副支92以 between t1 t2 引用。binding A從27改40，預覽只列1/2/3，確認卻使92長1973→1960、origin.x514→520。

**最小切片／刪除責任**：從既有已全量重算的 candidateWorld 取得 I8a 遞移閉包、新舊幾何與 typed identity；接到既有確認呈現。移除組構serializer自行挑選下游幾何責任，不增加第二solver。

**落點與依賴**：[geometry-web/assembly_bridge.inc](../geometry-web/assembly_bridge.inc)、[geometry-web/assembly-workspace.js](../geometry-web/assembly-workspace.js)。parent品質執行者負責前三项隔離重現；本文件worker未重跑、不競寫。Refs #24 #25。

**完成oracle**：92在確認前可見且新舊值正確；取消、invalid、stale不改World/dirty/history；確認僅提交已審閱候選。

**Readiness／未驗**：reproduced（品質owner於9ebf52a真native＋Chromium獨立重現），修復已分工；不是fixed。本worker只讀取證據／整理規格，產品未改；最新a274cae尚未重跑此反例，修復head另驗，實體iOS未驗保留。

**Owner／ready分工範圍**：root指定assembly-quality owner修復中；由已重驗candidate輸出完整幾何影響，保留專用assembly輸入，原生表示盡量收斂既有reference/engineering serializer。import/navigation各有自己的owner；共用bridge/primitive若碰撞由root協調，不另造solver。

<a id="qr2"></a>
## QR2 — P2 / #79 匯入附件引用須以原生候選最終物件核對，移除宣告掃描

**報告反例**：合法縮排 boundary 1 被frontend拒絕；boundary 1後delete boundary 1，metadata仍指1卻被接受，下一次匯出sources=0。

**最小切片／刪除責任**：在context替換前對完整 native candidate final objects 核對source/projection/metadata typedrefs，移除獨立宣告scan。只加trim不足以解決delete/reset。

**落點與依賴**：[geometry-web/reference-workspace.js](../geometry-web/reference-workspace.js)、[geometry-web/project-store.js](../geometry-web/project-store.js)、[geometry-web/docs/REFERENCE-PROJECT.md](../geometry-web/docs/REFERENCE-PROJECT.md)。parent品質執行者重現；報告使用VM圖片/HTTP替身＋真native，不等於一般UI存檔必遺失。Refs #24。

**完成oracle**：縮排合法案可開啟；不存在目標拒於contextswap前，source bytes/關聯/World/history保全；真封裝→解包→候選→重開核對，不只hash。

**Readiness／未驗**：reproduced（品質owner於9ebf52a真native＋Chromium獨立重現），修復已分工；不是fixed。本worker只讀取證據／整理規格，產品未改；最新a274cae尚未重跑此反例，修復head另驗，實體iOS未驗保留。

**Owner／ready分工範圍**：root指定import owner修復中；最小範圍readProjectContext/importProjectData、現有 /engineering/validate-project 候選驗證回覆、必要project-store typed metadata核對及相應正式測試。來源faces、既有projection/reconstruction review都以同候選最後boundary/placement定義核對，涵蓋所有可接受格式，不把legacy檔繼續交另一regex。保留source bytes/hash、PDF頁/圖片解碼、能力/late/contextswap/history保全；失敗在upload/live/context替換前拒絕。只移除宣告掃描責任，不重寫scene parser、store或保存。可與P1/導航並行，reference/history只由import owner寫，共用native fileio回覆需root協調。

<a id="qr3"></a>
## QR3 — P2 / #80 來源定位保留 placement 身分，避免同 boundary 多放置時進錯面

**報告反例**：boundary1由placement10/20引用，timber7在20；source graph完整保留20，導航只傳boundary1而進10，從畫布與已開10皆錯。

**最小切片／刪除責任**：讓source path復用既有按typed boundary/placement身分定位的工程入口，核對目標、目前工作區與context；engineering-adapter已傳placementId並後驗，不重寫該正確邏輯。移除source path省略placement而落入first匹配的錯誤假設，顯式目標失效時拒絕fallback。不涉及已取消#47雙向料單—模型導航。

**落點與依賴**：[geometry-web/source-inspector-app.js](../geometry-web/source-inspector-app.js)、[geometry-web/engineering-adapter.js](../geometry-web/engineering-adapter.js)、[geometry-web/app.js](../geometry-web/app.js)。parent品質執行者重現；本輪未跑真browser。既有live locator修復，可獨立於F1b新身份契約。Refs #44。

**完成oracle**：兩種進入情境均進20、選7；不同kind同號、晚回覆/切案/缺目標不錯接；World/dirty/history不變；VM與真browser分別列證據。

**Readiness／未驗**：reproduced（品質owner於9ebf52a真native＋Chromium獨立重現），修復已分工；不是fixed。本worker只讀取證據／整理規格，產品未改；最新a274cae尚未重跑此反例，修復head另驗，實體iOS未驗保留。

**Owner／ready分工範圍**：root指定navigation owner修復中；主落點source-inspector-app.js的live guide/grid/timber導航，重用工程入口的typed placement primitive，必要時才在engineering-adapter抽共用helper；不重寫其已正確的導航。即使同boundary亦按placement切換，讀回後驗目標實際屬該placement才選取；保持原context/revision/selection/late守門與唯讀World/history。顯式目標缺失拒fallback。若需app.js共用helper或feSurf失效策略，由root單owner協調，不能與PDF/畫布owner競寫。先覆蓋已重現timber7兩入口，再覆蓋同一branch的guide/grid，不偷接保存模型/#47。

<a id="qr4"></a>
## QR4 — P2 / #81 閱讀器 force marker 分支返回前完成補丁登記

**報告反例**：force(...,marker=...)的兩個earlyreturn跳過PATCHES登記；單次得到new MARK但登記0，移除MARK後verify仍不報錯。

**最小切片／刪除責任**：所有成功分支共用登記責任，保留冪等/唯一性與template drift拒絕；不用總登記量99門檻代替每項保護。

**落點與依賴**：[geometry-guide/sync_axiom_reader.py](../geometry-guide/sync_axiom_reader.py)、[tests/test_axiom_reader.py](../tests/test_axiom_reader.py)。報告隔離反例，尚未由此worker重跑；未宣稱現行四個UI已故障。

**完成oracle**：未套用/已套用marker兩分支均有可核對登記，刪marker必拒；現有canonicalreader、批註、五道assert及重建冪等保留。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="qr5"></a>
## QR5 — P3 / #82 閱讀器去除重複見證 handler，逐項退出已完成 UI 遷移

**報告反例**：兩份renderWitness、兩次axiom:current註冊使一次事件複製SVG兩次；46次force無改動仍綁定歷史OLD/NEW，正常空白UI變更可能drift拒绝。

**最小切片／刪除責任**：先刪死renderWitness/重複handler；再逐條列保留/退役/遷移的force用途與兼容。不因46次no-op便整批刪除，不另造reader。

**落點與依賴**：[geometry-guide/公理層-閱讀器.html](../geometry-guide/公理層-閱讀器.html)、[geometry-guide/sync_axiom_reader.py](../geometry-guide/sync_axiom_reader.py)、[tests/test_axiom_reader.py](../tests/test_axiom_reader.py)。依賴QR4helper保護先修；未量測真browser可感知性能，不能稱性能加速已證。

**完成oracle**：一次事件一次見證更新；單檔離線/批註保全/Markdown身份/JSON-DOM一致/圖追溯嵌入/五assert不退步；逐項歷史輸入與normal UI修改反例。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="qr6"></a>
## QR6 — P3 / #83 閱讀器可見條文總數改由 clause-data 派生並納一致性檢查

**報告反例**：可見側欄寫89條中31有見證，而clause-data118條；--check及25reader tests仍通過。

**最小切片／刪除責任**：移除可見數字89的第二份計數真相，總數及見證數從當前資料派生；檢查可見欄位對資料，不追加過期數字blacklist。

**落點與依賴**：[geometry-guide/sync_axiom_reader.py](../geometry-guide/sync_axiom_reader.py)、[geometry-guide/公理層-閱讀器.html](../geometry-guide/公理層-閱讀器.html)、[tests/test_axiom_reader.py](../tests/test_axiom_reader.py)。可與QR4設計獨立，reader/sync產品接線同owner避免競寫；本輪產品未驗。

**完成oracle**：當前118及有見證數與資料一致；增/減合法條文fixture可見count同步、故意改count檢查必red；批註與正典唯一性保留。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="qr7"></a>
## QR7 — P2 / #84 native binary freshness 核對內容雜湊，收斂到既有版本機制

**報告反例**：fresh GDI binary與sidecar複製到TEMP，改一byte且保留size/mtime仍判fresh；未執行修改exe，不代表過去CI實用錯binary。

**最小切片／刪除責任**：沿既有mutate binary內容hash做法，讓binary registry的建置/重用/現有pending身分及freshness一致核對實際bytes；舊sidecar明確stale或已評估遷移，不另造版本工具/安全繞過。

**落點與依賴**：[tests/binaries.py](../tests/binaries.py)、[tests/mutate.py](../tests/mutate.py)。環境SAC不改設定，GDI按平台具名；產品runner/native evidence消費者皆需核對，先有限counterexample。

**完成oracle**：同size/mtime改byte必stale且拒測；真正fresh可重用；missing/badsidecar/sourcechange/SAC blocked保原狀。記錄source＋binaryhash及精確head，不執行破壞副本。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="qr8"></a>
## QR8 — P2 / #85 恢復現版 mutation inventory 與 freshness，接回既有驗收入口

**報告反例**：報告mutate --check48筆：44stale、1invalid(M56 anchor缺)、3retired，有效killed/crashed/equivalent=0；現有正常CI/run_all沒呈現此缺口。

**最小切片／刪除責任**：逐條核對當前公理/故障目的/anchor，明確更新或退役理由，重跑仍有效變異後由既有驗收入口檢查freshness。不能改結果分類湊green、借舊run、新增健康分数；與QR7共用binary identity。

**落點與依賴**：[tests/mutate.py](../tests/mutate.py)、[tests/run_all.py](../tests/run_all.py)。先盤點後整合，依QR7固定hash領域；是否equivalent需可審查證明。Refs #24、BACKLOG GEO-225（非同一專門工單）。

**完成oracle**：每項有現版source/binary/command/exit/oracle；assertion-red與compilefail/timeout/infra分開；invalid/stale不可算killed，無效變異透明退役；check對故意改source/binary/result必拒。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="qr9"></a>
## QR9 — P3 / #86 獨立 space 瀏覽器驗收補逐群組數量基準，避免整段漏跑仍綠

**報告缺口**：獨立空間browser腳本已有行為assert、exception/consoleErrors與失敗exit守門；尚缺完整CDP逐群組counts基準，可能整段漏跑仍綠。報告尚未據此重現產品錯誤。

**最小切片／刪除責任**：沿完整CDP已有frozen group expected/完成旗標，補逐群組census與漏跑拒絕；保留space_model_test.js既有行為assert及異常fail，移除群組驗收缺乏基準的猜測責任，保持平台skip具名。

**落點與依賴**：[geometry-web/space_model_test.js](../geometry-web/space_model_test.js)。低優先可獨立規格；實作前核實現行腳本，與產品缺陷聲明分開。

**完成oracle**：真全群組可數且completed:true；故意跳過一群/拋例外/提前返回必red，不能調golden掩蓋；counts取獨立census。

**Readiness／未驗**：可依既有公理準備隔離反例與修復；沒有需要新增幾何公理的已知門檻。原報告結果未由本文件worker重跑，產品未修；詳細位置隨實作head再校正。過去套件pass不代表已涵蓋此反例，也不能反推所有舊結果是假通過。

<a id="auto-rooms"></a>
## 自動房間辨識 A → B → C

使用者20:22明確指定順序；本輪為規格／依賴整理，沒有產品實作。現有#54、#77保留，另建去重後#87處理同頁多候選。

| 順序／工單 | 最小切片／依賴 | 完成oracle／狀態 |
|---|---|---|
|A／[#54](https://github.com/ZhiQiYang/geometry-axiom/issues/54)|先修現行單房間實際失敗；重用既有向量/本地影像候選、Worker、輪廓修正與receipt；保持PR74/76snap及GEO-242呈現性能修正|實圖單房間反例逐項定位；來源基準、淨輪廓、凹口、歧義、取消與late reply可核對；目前私人案例全未驗，不能先宣稱成功率|
|B／[#87](https://github.com/ZhiQiYang/geometry-axiom/issues/87)|A穩定後，同頁有界多候選列表；session-only candidateId、source/page/basis revision、輪廓/警告；逐個明選核對/修正/排除。重用現有引擎，不先批量建正式面|雙房/三房向量與影像、門洞/相鄰連通/L形/孔/文字干擾核對拓樸，capacity不完整明示；換頁/校準/案/session使草稿失效；候選World/dirty/history不變；本輪未執行|
|C／[#77](https://github.com/ZhiQiYang/geometry-axiom/issues/77)|B的明選候選接[WP77](CONTINUATION-WORK-PACKAGES-20261003.md#wp77)/[Q37](CONTINUATION-DECISIONS-20261003.md#q37)：同來源基準，原生配號新增獨立Boundary；新增/編輯意圖分開|先A再B不替換A；每room穩定metadata身分＋typed nativeRef；完整ZIP保存freshcontext重開；Q37新附件待採納，產品未開工|

B先只保有界session候選，不自行增加持久格式或正式能力。若改成持久候選，先另提確切schema/capability差異。C的RoomCollection是來源附件，不是D5 Space或新的native父子geometry；共享sourcebytes不代表已有共享calibration。既有獨立ReferencePage校準維持原義，Q37採納前不暗改。

**落點／並行與減項**：[room-outline.js](../geometry-web/room-outline.js)、[reference-workspace.js](../geometry-web/reference-workspace.js)、[reference-ui.js](../geometry-web/reference-ui.js)、既有PDF path與本地Worker、[project-store.js](../geometry-web/project-store.js)。A反例分類／非機密多房fixture／Q37schema規格可獨立並行；產品app/reference/history一owner，不與PR76競寫。沿原「取得候選→描外環」工作區合併單/多候選核對，不新增第二PDF app、常駐管理器或超過三段說明。真iOS/OSchooser/download單列人工，不以390px代替。

<a id="private-cases"></a>
## 私人 PDF 案例索引（只公開匿名狀態）

使用者20:25已提供兩份私人PDF，可供後續授權測試重用；不需再次索取。Library是原檔持續來源，本輪未下載或開啟PDF。受限的case→Library映射與原文件名只留cloud TEMP，不提交repo，亦不將privatehash、地址、名稱、原圖或截圖放GitHub/CI。

| 案例 | 匯入 | 校準/對位 | 單房辨識A | snap | 多候選B | 多房建立/保存C |
|---|---|---|---|---|---|---|
|REAL-PDF-01|未驗|未驗|未驗|未驗|未驗|未驗|
|REAL-PDF-02|未驗|未驗|未驗|未驗|未驗|未驗|

後續實圖結果只公開匿名失敗類別、步驟及非機密數值/狀態；需要共享反例時先合成非機密幾何。合成夾具pass不等於這兩份實圖pass，性能合成benchmark不等於日常圖紙倍率。
