# BACKLOG — current_geometry.c 工單庫

## CONT-46-20261005 — 完整候選方案正式整合（進行中）

- 授權依 #46／Q33；完整 A/B、原圖內容定址去重、隔離試改、比較後整體採用可復原。沒有逐物件 merge、搬舊 undo 或新的物件沿革公理。
- UI 減項（GEO-219）：將原「專案與場景有何不同？」三段常駐說明合為既有專案資訊內的一段「完整專案與候選方案」，A/B 操作收在此 disclosure 及按需 dialog，不新增畫布常駐工具列。方案 dialog 一段用途說明；試改 dialog 一段狀態，均不超過三塊。
- 共用模型：正式 root catalog／能力 geometry-scenario-snapshots/1 與空出的 geometry-canvas/14。leaf project 不可含目錄；projectId 與 scenarioId 分離，#48 的 target projectScope 保留原 projectId。每份完整 manifest、scene、固定基準與 typed origins 都驗；原圖只按 hash 儲存一份。完整 root manifest 沿用 8 MiB、ZIP 256 MiB、展開 512 MiB 上限，最多 8 方案／256 資產。
- B 使用同一正式 app 的獨立 native context；共同 transport、receipt、upload 路徑綁 context，失效識別不回退至 live A。只讀驗證每次 disposable process；整體採用沿共用原子載入及一筆 ContextHistory，catalog／原圖／草稿／模型隨同一步 undo/redo。無部署或實體手機完成聲明。
- 尚在實作與驗收，不宣稱 #46 完成；#134 產品凍結及 16 檔證據發布 hold 分別保留。

## #134 — 完整定位查詢保留鍵盤焦點（2026-10-07，候選驗證完成）

- 在隔離 Chromium 的 390px 真 Enter 操作重現：`data-rule-exact` 按鈕被 disabled 時先失焦，原生只讀回應重建檢查器後焦點仍停在 BODY。單加 DOM id 不足以修復。
- 沿用既有完整定位入口，增加穩定 `gridRuleExact` id；查詢發起時保存焦點意圖，僅在 editor／request／raw tuple 仍新鮮且使用者未另行操作時還原，不搶回其他欄位或畫面的焦點。查詢保持只讀，不改核心、公理、保存格式或歷史。
- 本次拿掉／合併（GEO-219）：沒有新增可見入口或常駐說明；合併到原完整定位按鈕與其既有忙碌流程。
- P88 新增桌面與 390px 真 Tab／Enter 回歸，先確認舊 receipt 清空及實際焦點，再用含 Enter 字元事件的可信輸入觸發新原生查詢，避免預設值或舊結果掩蓋誤點。現有 reachability 與回歸門檻保留。
- 修正版完整 CDP：2161／0、零略過、84 段；golden 僅 P88 105→107、total 2159→2161。P38 有一筆預期 `fb-auto-probe`，非預期例外零。另跑網格 partial 312／0、P88 107／0、零瀏覽器例外；兩者分開記錄。runtime 前後 fresh，產品及 harness 來源 hash 不變。
- 嚴格完整非瀏覽器登錄回歸：70 suites，69 成功、1 Windows GDI 專用在 Linux 具名略過、零失敗、exit 0。`node:tests-js` 533／0／0，expected 僅 513→533；其中 production exact handler 23 tests 及 8 種 guard removal 反例通過。
- 獨立 Playwright：1280×900／390×900 六個原生 rule／面外 guide 預覽與下載 Save／選檔 Open 流程，188／188；World／history／非空 raw 保持不變，console／pageerror 零。另驗真 Enter 與延遲回應改欄位、點空白、離面不搶焦點。面外 guide 空交集未冒充舊普通 grid v0 精確 fixture，未驗實體手機或 OS Save picker。
- Windows #158 的偶發 `Rule line control unreachable` 本輪 Linux 尚未重現，未將焦點修補當作其根因已查明；仍保留待查。基底 `b88545e0` partial 310／0 及兩次未完成全量保留為診斷紀錄，不併入最終完整結果。

## CONT-20261004 — 八項採納與單writer整合

- 使用者已明示接受八項建議，並授權自行安排順序／並行／批次；[目前接口／owner／採納範圍](geometry-guide/IMPLEMENTATION-QUEUE-20261004.md)。舊準備階段的「全部待採納」保留為歷史，不擴大未明寫條文，也不拿來阻塞已批准工作。
- 第一波#85/#24收尾、#45單份rawdraft/來源→邊界、#44受控ordinary模型、#77人工多房與#49隔離案例準備；第二波#46/#48與案例保存；#58先六條精確差異/oracle後native→保存→UI。共用project-store/history/app及nativeWorld各單writer，root決定逐stage合併。

## #77 saved-cloud owner 接續 — 共享來源與明選重新關聯（2026-10-04，WIP）

- 沿 PR114 保存實作接線，不另造 PDF app／module／native parent。共享來源在既有專案資訊顯示；全房 unlink 或原生刪除後仍能明選 source collection／既有 boundary／房間、逐邊核對後重新關聯，不建 placeholder geometry。原圖 asset 與來源集合保留。
- **本次拿掉／合併（GEO-219）**：共享房間的舊獨立參考頁選單、移除底圖與自動辨識入口合併為同來源房間操作；來源概覽合入既有專案資訊，不新增工具列／常駐教學／工作區。普通面原功能保留。
- native candidate 指紋與 selected legacy records／receipt 無損遷移仍待 root／sole native owner 協調；拒絕保全不等於成功遷移，draft 不代表 #77 完成。同 head native、browser、ZIP／歷史及必要 full gates 結果回填交接文件與 PR114。
- #85 PR98已合併main1075058；#24 PR97待root審查，A24實機保留。具體測試／exact head另以各stage真實證據回填，不宣稱採納等於功能完成。

## F4a 保存模型雙向定位 — #47 恢復的有限切片（2026-10-04）

- 使用者明示恢復先前取消的工作；隔離分支 `feat/model-snapshot-schedule-navigation-20261004`，基底 main `4e5f5df`。只處理已驗證 ordinary plan 的明選 `input.timbers`，不接管 #54／PR92／PR93；交 draft PR，由 root 獨立驗收後決定合併。
- 同一保存 record 的既有 native 快照料單與唯一 typed timber root mesh 對照；料單列定位／高亮該模型構件，3D 點選回選該料單列。沒有 live World 同 ID 回退、尺寸猜測、F1b、新公理或保存格式。
- **本次拿掉／合併（GEO-219）**：readonly 3D 原有重複 ID／世界 z 列合併為既有快照料單的同一呈現；將既有列升為選取操作，沿用已有視角／置中及角材顯示開關，沒有新增工具列或工作區。未保存預覽的核對列保留。
- 必驗同尺寸 root 0／4 的分別選取、實際三角形命中與遮擋、拖曳／縮放不誤點、record／context／close／late 失效、幾何逐位元不變、保存重開及桌面／手機視口。A24 實體 iOS／OS 檔案對話框仍未驗；不宣稱整張 #47 完成。

## GEO-242 — 底圖畫布與選房間的操作性能（2026-10-04）

- 使用者回報縮放、平移、描輪廓與選房間卡頓，授權先從程式碼排查。只修現有流程的性能；不改公理、吸附座標、候選辨識門檻、正式幾何、保存格式或核對要求。
- 確認 wheel／框選每事件整份重建面內 SVG，人工描輪廓每事件廣播 ReferenceWorkspace.present，游標每事件重寫 DOM 並讀版面。合併呈現到下一幀，幾何與座標仍同步更新；pointerdown/up 呈現最後狀態，跨編輯工作階段丟棄舊待繪工作。同步重繪承接待呈現的 camera／座標，避免快速換工具時顯示落後。
- 保留已解碼的底圖 image／clip group，更新來源時才換 href；縮放／重繪不反覆移除底圖。PDF 影像輔助使用已渲染頁，去除每次取得候選重渲／編碼整頁的工作。
- 房間障礙矩形的重複填格改成壓縮座標上的精確差分聯集；保持內緣、凹口、錯誤、分隔與警告。向量／像素分析及搜尋移到本地 Worker；取消、重取、來源變更即終止舊 Worker，舊回覆不能清除或覆寫新工作，分析仍須來源驗證後才成為待核對草稿。
- **本次拿掉／合併（GEO-219）**：合併同幀的重繪、座標及草稿提示，移除每次 pointermove 的全域通知與未變游標 DOM 重寫，去除重複 PDF 渲染及重疊格掃描；沒有新增可見 UI 入口或常駐說明。
- 初步固定 120 事件批次：wheel 與房間框選從 120 次全畫布重繪降為 1 次，底圖節點保留，native dump 逐字相同。高重疊 11774 障礙的純 region 合成案例三次中位數 5531→9.9 ms，結果逐字相同；不得把它當作一般圖紙或日常操作的倍率。
- 已整合 main `0f3c1a6`，保留新校準／選房間入口、取消辨識及失敗清理。新增 13 項排程／Worker 故障與取消測試、登記全庫 runner，相關 84 項再次通過。完整非瀏覽器 49 suites：1543 通過、0 失敗、1 項具名 Windows GDI 略過；該 GDI 另以同版 Windows fresh harness 補驗 1/1。Linux 來源副本 887 檔逐位元核對相同（工單紀錄除外），expected 由完整 census 產生，只增加 7+6 項新測試。
- 初次交付時真 Chromium 完整回歸尚未完成；後續同版 native Linux Chrome／服務無 filter full 完成，79 段 frozen golden 相符、1867 通過斷言、0 失敗、0 略過群組。唯一 exception 是回報測試刻意注入的 `fb-auto-probe`。先前 Windows／WSL 混合測試遇到預設 stack、建模 adapter 設定及一次連線中斷；Windows 新編 bridge/core 被 SAC 阻擋，未改安全設定。
- 另定位到既有房間取點／候選狀態的空白鍵平移被 `RoomOutlineWorkspace.move()`／`feMove()` 前置守門攔截；這批尚未修改該手勢規則，後續需補實際移動量的反例並修復。辨識中的空草稿也需另驗輸入互斥，不能把背景分析的結果覆蓋成使用者的人工意圖。
- 修正在 managed worktree `canvas-performance`；目前使用者 8765 服務及完整專案恢復資料保持原狀。啟用仍须依 GEO-231 保全 `.gcanvas`（含底圖與草稿）及核心 dump 後切換並核對版本，不以 `.scene` 備份冒充。
- 2026-10-04 使用者明示要求提交全部現行修正並合併遠端／本地 main：整合 PR73 `b0f9e5a`、PR74 `3300db6` 與本工單性能修正。合併測試先以 P84 重現延後的通用座標讀數覆蓋 PDF 來源吸附讀數；`bf10b82` 讓來源讀數與草稿同幀呈現，通用讀數先排程。修後真 Chromium 房間／PDF partial P79=84、P84=27，共 111 通過、0 失敗、0 exception，相關 Node 32/32；889 檔 Linux 測試副本與提交來源逐位元相同（工單文字除外）。這份整合版尚未重跑無 filter full Chromium，不借用性能分支的 1867 當整合版結果。遠端 Actions 七個 jobs 均零 steps 而失敗，保留環境失敗，不宣稱 CI 綠燈。舊身分政策原型／備份不在本次已核准修正範圍內。

- 整合來源 `bf10b82` 另完成完整非瀏覽器 50 suites：1551 通過、0 失敗、1 具名 Windows GDI 略過，所有 frozen expected 相符。最後納入 PR74 可見性排除 `7263b83` 及 PR75 規格提案 `f742463`，Node 32/32 再次通過；沒有把提案採納或實作。這兩筆後沒有重跑 full Chromium／全庫，不宣稱最後 main 的全量 exact-head 驗收。

## PR70 補驗 follow-up — 復原／重做保持忙碌直到操作完成（2026-10-04）

- PR70 已由外部流程合併為 `d5ea531`；原切片、原生快照及保存契約不重做。此 follow-up 基底是包含 PR71／72 的 main `0f3c1a6`。
- 補驗在 P70／P72 發現復原／重做讀回先於操作完成：`doUndoRedo()` 原先未持有 `oc.busy`，同時閒置判斷及下一次操作可提早進入。沿用既有忙碌門，涵蓋原生／本地歷史及畫面刷新，成功、拒絕、例外都由 finally 釋放。
- 不新增可見入口或常駐說明；合併重疊的歷史操作，沿用既有忙碌樣式。公理、snapshot/native 邏輯、schema、durable identity 與 F4b 範圍均不變。
- 驗證結果以 follow-up PR 同 SHA 證據回填；既有 frozen expected／golden 不調整，只登記新增的 4 個歷史操作測試。原 PR70 補驗的所有失敗均保留，不以後續通過覆寫。

## CONT-20261003 — 可接續工作包與集中決策（規格準備，未開產品實作）

- 使用者 2026-10-03 19:47 指定 #45、#44、#46、#48、#49、#57–62、#24：整理最小切片、依賴、驗收、落點、並行與 readiness，加入佇列並提交 draft 文件 PR。初始基底 `0f3c1a6fdd88bbcce4484a256d45900bd1d92313`，後續文件基底 `9ebf52a1b6519356e9ff677e55b9cf167c47b70d`；不改公理或產品契約。
- 集中入口：[可接續工作包](geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md)；[決策包](geometry-guide/CONTINUATION-DECISIONS-20261003.md) 的 Q31–Q36 全部待採納。規格 ready 不代表產品已授權／已實作／已驗收。
- 20:23使用者專案檢視報告已完整讀取，去重建立#78–86：[九項優先缺陷／驗證收斂包](geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md)，排在一般新功能之前。20:54完整讀取品質獨立報告，前三項在9ebf52a真native/Chromium已reproduced，root分派assembly-quality/import/navigation三owner修復中，不再只是排隊；新a274尚未重跑這三反例、本worker未改產品。P2最小檔案/交易/typedlocator分工界線已備，禁止另派重做。
- 已取消的 #47 雙向定位不排入本佇列；PR73 undo/redo 與 PR74 PDF snap 已由原 owner 交付並外部合併，本文件分支不改其產品碼／驗收。保存與共用 app.js 接線另指定一個整合 owner，不競寫。
- **UI 減項（本輪）**：沒有新增產品 UI／常駐說明；未來 WP45 合併來源配置說明，WP61 沿用來源工作區合併手動／來源細分說明。各 slice 必須寫明具體移除／合併項，否則依 GEO-219 先進決策佇列。
- 文件規格與正反例可並行；子網格產品 #59–61 先等 #58 精確採納；#46/48/49 新附件契約未採納；A24／SR24 真 iOS／OS 選檔與下載另列，不以390px冒充。#24 與總工單維持 open，使用 Refs。
- 使用者20:19追加同PDF連續獨立房間，已查重建[#77](https://github.com/ZhiQiYang/geometry-axiom/issues/77)，加入[WP77](geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md#wp77)/[Q37](geometry-guide/CONTINUATION-DECISIONS-20261003.md#q37)。共享sourcebytes不是共享calibration，Space不是樓層房間樹；附件不存第二geometrytruth，新契約仍需採納。
- 20:22自動房間依[A→B→C](geometry-guide/PROJECT-REVIEW-QUEUE-20261004.md#auto-rooms)：#54先修單房間實際失敗→新#87同頁多候選→#77確認獨立Boundary/共享基準；不用同一issue混稱全部完成。私人PDF留Library；REAL-PDF-01/CaseA本地0f3c1a6已匯入及323.5cm校準成功，預設vector/image edge-open、width0.1 tooManySegments失敗，geometry不變/0 exceptions，root核對原bytes一致。保留該歷史；newhead snap/人工分區/整屋/新main重跑未驗，REAL-PDF-02/CaseB各階段未驗。private映射僅cloud TEMP，不提交原文件名/地址/LibraryID/hash/截圖。
- PR75 first head `f742463`（外部已合併）只含第一批總表／WP45／WP24；後續draft補齐原12＋#77共13工作包、Q31–Q37選項、[#58逐條proposal](geometry-core/GRID-SUBDIVISION-RULES-PROPOSAL.md)，另納九項優先缺陷與自動房間順序。全部規格準備，決策未採納；本輪僅文件驗證，未重跑產品測試，沒有worker merge／部署。

## GEO-240 — #45 F2a 單選已發布規則銜接既有材料配置（2026-10-03）

- 基底 main f52ed1d（已合併 PR68）；只適配既有 D32/D33/I40/I41/R34 authoring，不改公理、保存格式或生成範圍。規則卡片帶原生既有固定版本指紋；入口不能按同 id 的最新版本、名稱或卡片順序猜来源。
- **本次拿掉／合併（GEO-219）**：單選規則檢查器的泛用「開啟組構工作區」按鈕一對一替換成「建立材料配置」；完整編輯仍由既有卡片／清單／建立選單到達。材料配置物件的既有開啟操作保留；不改 Q19 已鎖的建立入口，不加常駐工具列或工作區，SourceInspector 不重做。既有發布規則內「建立材料配置」使用同一操作描述與來源守門。
- 一筆有型別 context operation registry 描述所需 authoring 能力、固定規則與輸出 binding。材料 A/B、接觸面與擺向可在既有表單補齊，合法 incomplete binding 不被禁；不宣稱生成幾何。
- 新入口先在隔離讀取狀態驗 capability／版本／指紋／選取與 context；過期、缺來源或缺能力在 flush、取消舊 token、配號及寫草稿前拒絕。延遲回覆、重複點擊、換選取／專案與舊 workspace 編輯不接入另一份來源。沿用 PR68 newDraft 的原生配號／draft保留／preview／confirm／保存與來源 guard。
- PR69 reviewed `175b308d2a2523aa1da81d679d536c7bc5de7905` 已合併 main `8993b03b91d27030d210d6478e08764af51385d7`，tree完全相同：完整47suites1499/0/1具名GDI、無filterChromium1839/0/78golden、native/ASan各35/35及獨立79/79＋10/10通過。合併後真P82入口16/0、既有binding16/0、P80/P81料單37/0、HTTP291public/205vendor bytes與headers及前後fresh/runtime核對成功。grid-source＋boundary、未提交 grid 草稿附件、F2b 範圍擴張與 A24 實機仍分開。

> 2026-10-03 cloud 事實校正：PR52 已合併 `1805bb5`；PR55 合併至 PR53，PR53 的有限 D34/I42/R35 生成已合併 `68c4ac1`。其他 owner 的 PR63/#54 已合併 `c87be11`、PR64 已合併 `d40dee0`。以下較早工單內「未實作／未合併」保留當時歷史，不能作目前事實。A24 實體手機未驗。

## GEO-241 — 單一保存模型的原生角材快照料單（2026-10-03，#47 bounded 切片，實作中）

- 隔離分支起於 main f52，已整合 main899（PR69）；只計一個合法保存模型明選 `input.timbers`。同尺寸不同 placement 保留各件；不加入未選根、現行 World 或另一模型，不以 UUID／範本／尺寸／World hash 捏造實物去重。
- 既有 snapshot 路由在同一 candidate World 追加既有原生 `timberReferences`，重用 pure serializer；尺寸、原點、typed 工程來源及精確支撐不借 live。live 輸出 bytes 保持不變，無新 command／route／保存 schema／公理。
- 派生使用既有 decorated 料單 adapter，canonical 模型 scene／definitions JSON／native World 的 hash 領域分開。現行 changed／missing 不替換歷史快照尺寸；內容一致也保留 incarnation unknown。
- 減項（GEO-219）：模型既有來源 disclosure 內，一對一將「重新檢查」升為「核對並匯出快照 CSV」；普通來源入口不變，無新工具列／工作區／永久說明或幾何附件。匯出前核對同模型 owner、context／history／revision、取消／遲到與連點。
- Draft PR70：整合 main899 後完整47suites1530pass／0fail／1具名GDI，production121／121及ASan/UBSan121／121；獨立review APPROVE。JS63／63＋21實際native／lifecycle反證，五個新native案例在 immutable f52 baseline都assertion-red，wrong-World mutant3／5 assertion-red，兩World九種live回覆byte-identical。真P83桌面／390px、gcanvas重開、逐bytes下載、changed／missing歷史尺寸、model／context／close／late／repeat守門16／0；只新增P83=16，原1839段計數保留，最後無filter full與exact-head結果以PR70最新正文為準，不宣稱整張#47完成。
- 既有 model engine 拒絕 assembly-owned snapshot（capability／definition whitelist）；不剝來源或製造保存正例。跨表示去重、模型內完整雙向定位、F4b加工／裁切、durable identity 與 A24實機仍分開。契約見 `geometry-web/docs/MODEL-SNAPSHOT-SCHEDULE.md`。

## GEO-239 — 現有材料配置的固定規則來源守門（2026-10-03，#45 既有流程修復）

- 已重現規則同 ID／版本／槽位、不同 joint 內容刪除重建後，旧 asmBind 與 published-binding edit 可合法提交不同規則語義；配置自身 value／fingerprint 不足以辨識 underlying rule 改變。
- 建立／編輯在 flush／配號前核對顯示來源與 fresh native rule fingerprint，沿用既有 base_ref 保存 fixed rule 身分；preview 再驗 native source、rule tuple 與 update intent。失敗不能藉第二次同一舊 UI 操作採用已刷新的快取，只有明確重開／換版對應才能更新來源。
- Legacy null 草稿保留原生驗證；明確 mapping 更新 base_ref 而保留 typed slot sources 與 create/edit 意圖，metadata-only pin 變更仍經原有 history 保存。
- 減項：合併進現有 asmBind／材料配置編輯／preview，沒有新 context 入口、操作 registry、工作區、保存格式、公理或原生生成能力；不得稱 #45 F2a 完成。
- 以真 native 同 tuple／不同語義反例、Node assert-red baseline、正式 Chromium 控制／保存重開／零 preview POST負例與完整整合測試驗證，精確結果另附 PR。A24、F2a 新入口／網格附件契約仍分開追蹤。

## GEO-237 — Runtime 公開靜態來源閉包與精確位元版本（2026-10-03）

- 獨立審查證實既有205個vendor中195個未參與版本，公開documents／正典reader／examples仍live讀；同version可提供不同bytes且fresh仍true。
- 同一allowlist決定公開路由、來源集合、啟動capture、版本與freshness；所有副檔名及無副檔名vendor、既有四documents／reader／三examples均固定提供capture bytes，不增加公開路由。
- 公開artifact逐位元識別，二進位／字體／archives不正規化CRLF；未提供的source及SSOT保留LF同一性。私有圖紙、專案、feedback、上傳及動態場景不納入部署版本。
- 啟動缺檔／競態拒絕，增刪檔及同尺寸同時間戳改動仍拒絕fresh；沿用現行保全dump與過期拒絕策略。
- 減項：合併server與runtime兩份vendor路由枚舉；不新增UI入口、常駐說明、公理、保存或安全設定。
- 隔離四檔修正44592ec由另一agent獨立審查，55/55 tests及兩個assertion-red故障注入；282static／205vendor路由集合不變。最終整合head完整驗證另附PR，未部署或觸碰用戶服務。

## GEO-236 — 原生角材支撐來源正式接線與 CSV 核對（2026-10-03，#47 F4a）

- 沿用 D11/R6/R21 原生擋面與唯一候選，正式 references 追加支撐來源、局部面、世界法向與 owned 版本；無唯一證據保持 unknown，不以座標、名稱或材料習慣補造關係。
- 獨立審查抓到 adapter 只驗欄位形狀：同 fingerprint 下偽造實例指紋、支撐 member／rule version／不存在 timber 仍可 CSV。正式 adapter 改核對同面實际放置及全部八欄 ownership，無 JS 接觸重算。
- 數量仍由原生計量與明選 scope 決定，未選支撐只提供核對，不加入料單。保存／重開仍沿用既有 gcanvas 定義。
- 減項：合併到既有可展開來源與 CSV；不新增可見入口、常駐說明或獨立保存格式。
- 正式接線、registry 與 P81 四個實際 CSV 負例納入同 head 完整驗證。雲端來源、真瀏覽器與獨立審查證據附 PR65；A24、model 快照適配與 F4b 仍未完成。

## GEO-233 — 確認期間參數輸入保全與異槽生成 oracle（2026-10-03，已合併 PR56）

- main `31ba2be` 的參數確認只設 busy，欄位仍可輸入；獨立審查及本 worker 真 Chromium 均重現 native 已確認27、回覆未到時輸入99、回覆後27覆蓋99且 pending=false。
- 確認期間同步鎖定當前編輯器控制並標 aria-busy，取消自動試算計時；事件不再捕捉確認途中輸入。只恢復這次捕捉的 DOM，不解鎖另一專案／新版編輯器；成功及過期拒絕都恢復正確操作狀態，不重送確認。
- 真鍵盤新驗證6/6：延遲真成功回覆與真 stale token 兩路均拒絕途中輸入99，成功保留正式27，拒絕保留27草稿／正式11；回覆後均可明確試算並提交99。
- 生成 production 目前正確；舊19項在「每個 member 讀第一材料槽」mutant仍全綠。新增獨立整數 oracle：主支27×33，副支40×50，逐 member 精確截面／料長／原點／軸；另驗槽位與 member 重排、稀疏ID、僅副支typed參數更新、穩定mapping與fresh replay。
- 正常生成21/21，ASan/UBSan21/21；first-slot mutant兩個新tests出現12個Assertion failure、exit1，無編譯失敗或skip。未改正常核心或公理。
- PR63已由其他owner合併main `c87be11`；本分支整合其format9、房間P79=72並保留料單P80=23。完整整合驗證與最終exact head待回填；GitHub Actions帳務阻塞不冒稱綠，未改billing。
- 整合候選 `a5e9d6e` 完整非瀏覽器1349/0/1具名GDI略過、真Chromium1805/0/0skip且76段golden matched，獨立space183/0、ASan/UBSan56/56。但獨立審查另抓到 `loadLegacy` 遲到插入三個enabled控制；真瀏覽器已反證確認途中可輸入99。因此不能因全量綠就停止修復。
- 補鎖遲到控制只增補既有Map，不重捕已disabled舊控制；成功／拒絕恢復新增控制的原狀，legacy handlers亦守busy。修正 b064646 已push且獨立review無P0/P1/P2；同head完整native1349/0/1具名GDI、P76focused72/0/raw0、space183/0、完整無filterChromium1809/0/0skip且76段golden全等（首次CDP中斷及重跑紀錄另保留）。PR56尚未合併；發現最新main d40又增PR64，因此整合新main并驗GEO235測試基礎設施修正後再合併。Actions included minutes已2000/2000、11月1日重置；七CI jobs未執行，不冒称綠，未重跑相同CI、改billing／policy或付費。

## GEO-234 — 原生角材完成尺寸料單（2026-10-03，#47 F4a，原 GEO-232 編號避重）

- 自 main `1805bb585a74f4a5759367aab7ef8de016d96d4d` 隔離實作。只導出目前明選承載面的正式已放置角材；不計未生成規則／材料配置，也不混入空間模型快照。
- 原生 references 提供來源定義指紋；每列保留 timber ID、surface ID、原生 A/B/L、dir/side、定位／跨距選擇器及工程尺寸來源。未提供的材料、加工與求值支撐身分明示未知，不自行猜定。
- 範圍可以是此承載面，或使用者明選的角材 ID 集合；排序／mm 或 cm 顯示不改身分或原生值。CSV 匯出同一列集合，防護公式樣式字串。
- **本次拿掉／合併（GEO-219）**：將既有左欄角材尺寸列直接升為料單，共用其選取、高亮與刪除；不另建料單對話框／第二份清單。座標與來源細節按需展開，沿用既有構件操作入口。
- 不改公理、專案格式、工程交易或私人圖源；F4b 裁切／餘料／採購不在本批。#54 已由其他 ChatGPT 執行者接手，本分支不寫底圖狀態／候選流程。
- 原 main 首版實測：Node 料單 7/7、原生 references 34/34；完整非瀏覽器 1297 pass／0 fail／1 Windows GDI 平台略過。真 Chromium P79 14/14、0 例外。完整回歸抓到 P75 仍假設點角材列不會平移畫布；以真實「適合」按鈕再看對側構件，保留全部命中／游標斷言，修後 P75 37/37。
- 已隔離整合 PR53 reviewed head `edb0fe68` 的 format8／生成來源；references 重用原生 assembly typed read，owned 角材保留 instance/member/binding/rule 與截面 source，核對有效值相等。新增原生唯讀不消耗待確認 token、Node typed source 與真生成範例料單測試。整合候選完整非瀏覽器 1323 pass／0 fail／1 GDI 平台略過，Node 料單8/8、generation19/19，真 Chromium P79 16/16、0 例外。完整無 filter CDP 預期 1720，exact-head CI 另回填；未跑完不得宣稱全綠。
- **再次獨立審查修正（P2）**：合法 placement0 原先被正號檢查誤拒，改按原生 uint32 含0，null／超界仍拒；追加 Node 與原生讀回。匯出預驗等待中若資料身分、載入序號、專案revision／context或範圍改變，或原生ok=false，均拒絕建立CSV。原生A長4000→B長4200的舊回覆問題已重現；修後真Chromium P79 23/23、0例外，其中六種延遲負例均零CSV Blob。Node9/9、references35/35通過（16MiB stack）。最新完整golden1727與完整非瀏覽器／CI待最終提交後回填。
- head `1fd5956` 實測完整非瀏覽器1333 pass/0 fail/1具名GDI平台略過；完整無filter Chromium1727/0/0skip，75段golden matched，raw1為既有P38刻意probe、未預期0；CI37111777904七jobs success。CSV移除兩個source guard的隔離mutation17pass/6fail、exit1，四種延遲反例實際產生Blob而被抓。後續料單改P80避開PR63的房間P79；以上數字仍精確屬於1fd5956，整合後重新驗证。
- 剩餘：自動跨距的確切支撐身分／局部面適配、空間模型快照導出及 F4b；保持 #47 open。不能以這個首批切片宣稱整張工單完成。

## GEO-235 — 全量 CDP 非同步求值的 Promise 保全（2026-10-03）

- b064 原全量首次在 P52 因 CDP `Promise was collected` 中断，687 個斷言通過、0斷言失敗但 completed:false；保留原log。無source改動的新World重跑完整1809/0/0skip、76段golden全等。整合其他執行者 PR64/main d40 的候選97be836又於P52同類中断，713/0且不完整，不能以重試碰運氣交付。
- test-only `cdp_evaluation.js` 在頁面以每次求值獨立Map項強持有原expression返回值，收到CDP回應後finally釋放。原expression僅執行一次，協定失敗不重送可能已提交的native mutation；原錯誤不被cleanup次要失敗覆蓋，成功後cleanup失敗則仍報错。
- 9個登記純Node回歸驗global lexical／statement、pending／並行持有、拒絕／syntax清理、協定失敗單次mutation、錯誤保存與更換document不污染。真Chromium強制GC正反例／独立review／最終同head完整CDP另回填PR，未完成不得宣稱。
- 不改產品功能、公理、正常native核心、保存格式或UI；不新增可見入口／常駐說明。GEO-234料單改號避免與另一執行者已合併的GEO-232效能工單重號，原歷史證據仍按exact head保留。

## Issue #54 — 來源房間輪廓候選（2026-10-03，PR #63 待審）

### 校準後輪廓入口熱修（2026-10-03）

- 合成 PDF 重現 4000×3000 mm 既有外環；兩點 323.5 cm 校準只放大底圖，房間落在外環與舊視野外。辨識本來依來源取景，不被原外環裁切；候選確認本來就替換目前外環。
- 精準改現有入口：「描外環」標成「選房間／描外環」，校準完成後明確展開輪廓區（不被 inspector 舊折疊狀態蓋回）。沿用原 `refFit`／fitReference，把「顯示取景範圍」從來源區移到輪廓區。
- GEO-219 減項：搬移同一顆 fit 按鈕，來源區不留第二顆；搜尋範圍與替換說明取代原 `refRoomStatus`，候選說明與確認鈕直接明示替換，不加工作區或常駐教學區。
- 辨識中沿用原取消入口與 generation 守門；正式面不變，遲到結果不恢復候選。審查指出且真 PDF 開口夾具重現的失敗狀態，先清 acquiring 再算繪失敗提示，避免失敗後殘留「取消辨識」。核心、I8a、保存格式、公理及 PR70／71 未改。
- P79 增 12 項：原生 dump 校準前後相同、展開與單一 fit、超出原外環的六角內緣 oracle、候選確認門檻、取消／遲到取消、失敗狀態清理、實際確認／復原／重做、保存及真 reload 重開。原 72 項保留，整合已合併 PR70／71 的 main `34c2ebe`，golden 只加 P79=84／total=1867，其他各段（含 P83）不變。
- 已驗：P79 84/0、0 瀏覽器例外；完整非瀏覽器 47 suites、1530/0、1 個具名 Linux GDI 略過；Playwright 真 Chromium 1440×1000／390×844 校準與確認、0 error／warning。全量結果與原始證據見[草稿 PR #72](https://github.com/ZhiQiYang/geometry-axiom/pull/72)，未合併／部署。
- 真實使用者 PDF／截圖未測：官方 Library 檔案下載失敗，依授權停止重試，所有回歸只用自製非私人圖面。

- 開工基準：main `1805bb585a74f4a5759367aab7ef8de016d96d4d`；隔離分支 `codex/issue-54-room-outline`。開發期间 #53 由其他工作合併至 main `68c4ac1`，本分支整合已合併版本，保留其公理／格式 /8 變更，不覆寫其他工作。
- 順序：A 完成狀態綁定實際來源頁、校準／變換、核心輪廓；B 點選目標的 PDF 原始向量優先、影像本地半自動候選；C 既有面工作區修正、整數入值核對、核心交易、歷史與保存重開。
- 候選契約 `room-outline-candidate/1`：只在當次面內編輯保存草稿；來源 hash、頁 id／頁碼、固定 viewport 頁面座標、取景與校準／變換依據、取得方式、頁面輪廓／局部推估座標、警告和人工修改。草稿阻擋保存；確認後只保存來源核對收據（含 ordered 核心輪廓指紋與來源依據），不另存權威幾何。
- 保存：/9 包住核對收據，舊 /1–/8 仍可讀，包含新 main 的組構生成能力；未知版本由舊讀取器拒絕。不挪用 /8。來源與輪廓引用驗證先於世界替換；重新校準只改底圖，要求重新核對，不縮放正式面。
- 方法評估：vendor PDF.js 為 6.3.289，`getOperatorList` 的 `constructPath` 使用 DrawOPS（非舊版座標格式）；重用 CTM＋原始頁旋轉後 viewport 的直線／填色障礙。向量不表示牆語意，需人工選線寬門檻及核對。影像取長正交暗線作障礙，再取點所在連通區；不閉合、觸及取景邊界、孔／多輪廓與忽略的斜／曲線均明示，不偷偷封門或轉矩形。
- UI 減項（GEO-219）：既有「描外環」步驟容納「選房間／人工描繪」；移除重複 reference-intro 與 calibration-instruction，合併底圖核對說明至單一輪廓區；原 `refConfirmChecked` 併入這裡的實際來源核對。候選頂點／邊尺寸使用同一面內草稿層，不新增工作區。常駐說明限三塊；狀態、錯誤及草稿才出現的核對內容另計。
- 開工基線：61 個來源／保存／投影 Node 測試通過；38 個服務／回報 Python 測試通過。完整瀏覽器與空間測試使用另編 `%TEMP%/geometry-tests/issue54/` 的橋接器與隔離服務；不終止使用者持有的 bridge.exe。後續結果與未驗項目見交付證據文件。
- 交付：[草稿 PR #63](https://github.com/ZhiQiYang/geometry-axiom/pull/63)；A／B／C 已實作，整合最新 main `31ba2be`。程式 `4bb30b9` 的七組 CI 全過：完整非瀏覽器 1,335 通過、0 失敗、1 個具名 GDI 平台略過；完整空間 183 通過；完整 CDP 1,776 通過、0 失敗、0 略過群組，75 段嚴格符合 golden；另角材 79、組構 128、網格 138、文件 47 通過。[驗收證據](geometry-web/docs/ISSUE54-VALIDATION.md) 含命令、CI 連結、公開夾具／畫面與實測比較，以及 Windows 受阻／WSL 失敗嘗試。後續只補報告，但文件提交 CI 因 GitHub 帳戶付款／支出上限未啟動，明確保留 draft；解除後須對最新 head 重跑。不更動帳務，不把未跑寫成通過；未合併本 PR、關閉 issue 或部署。

> 產生日期：2026-09-12，對象 `current_geometry.c` @ 4,567 行。
> 估時以「熟悉此 codebase 的工程師」為準（30 分鐘～3 小時）。
> 平行標記：⚡= 可與同標記工單同時進行（不摸同一段程式碼）。
> 相依標記：`←` 後面列出必須先完成的工單。

---

## 第 0 流：基礎設施（先做，後面所有工單的驗收都靠它）

### GEO-001 ⚡ 建立一鍵建置腳本
- **內容**：`build.bat`：`vcvars64` + `cl /nologo /W4 /O2 /utf-8 current_geometry.c /Fe:current_geometry.exe`；另出 `build_debug.bat`（`/Od /Zi /RTC1 /W4`）。
- **驗收**：乾淨 checkout 下跑 `build.bat` 產生 exe；警告數量印在結尾。
- **檔案**：新增 `build.bat`、`build_debug.bat`。
- **測試**：手動跑兩支腳本各一次；debug 版跑 `--no-window` 無 RTC 攔截。
- **相依**：無。**估時 1h**。

### GEO-002 ⚡ 建立最小回歸測試腳本
- **內容**：`run_tests.bat`（或 python）：逐一執行 `--scene X --no-window --out Y`，比對 exit code 與 stdout 關鍵字。初版收錄：room_a（exit 0）、room_box（0）、各錯誤案例（exit 1）。
- **驗收**：`run_tests` 全綠才准 commit；失敗時印出哪個 case、預期/實際。
- **檔案**：新增 `tests/run_tests.py` + `tests/cases/*.scene`。
- **測試**：故意弄壞一個 scene 確認測試會紅。
- **相依**：GEO-001。**估時 1.5h**。

### GEO-003 ⚡ 修復壞掉的範例檔
- **內容**：`ceiling-a.scene`、`demo-two-timbers.scene` 改新語法（`place … on <面id> …`）；或若決定廢棄就刪除並在文件註明。
- **驗收**：兩個檔 `cg --scene` 皆 exit 0；`demo-two-timbers` 產出含兩支角材的 SVG。
- **檔案**：`ceiling-a.scene`、`demo-two-timbers.scene`。
- **測試**：GEO-002 納入這兩個檔。
- **相依**：無（測試納入相依 GEO-002）。**估時 30min**。

### GEO-004 寫建置/使用說明 README
- **內容**：`README-geometry.md`：編譯需求（VS BuildTools）、build 指令、CLI 參數表、scene 格式入口。
- **驗收**：照文件從零能編出 exe 並產出 SVG。
- **檔案**：新增 `README-geometry.md`。
- **測試**：找不熟的人照做一次（或自己刪 exe 重走流程）。
- **相依**：GEO-001。**估時 1h**。⚡ 與代碼類工單全平行。

---

## 第 1 流：解析層與輸入面（RISKS B1/B4、F5、A5/A6）

### GEO-010 ⚡ Coord 輸入上限
- **內容**：`parse_i64` 之外加 `parse_coord`：限制 `|v| ≤ 100,000,000` mm（=100 km，遠大於任何房間）；所有場景檔數值欄位改用它。id 仍走 `parse_u32`。
- **驗收**：`surface … 0 0 99999999999999 3000` 被拒（exit 1）；現有合法 scene 全部仍通過。
- **檔案**：`current_geometry.c`（parse 層 ~L3258）。
- **測試**：tests/cases 加超大座標、負座標、INT64_MAX、剛好上限±1 的邊界 case。
- **相依**：GEO-002。**估時 1h**。

### GEO-011 溢位安全評估與中間值加寬 ← GEO-010
- **內容**：GEO-010 擋住外部輸入後，盤點內部乘法鏈（`view_quad_area2`、`view_dist2_to_segment`、`view_unproject_on_surface`、`timber_place_a0_on_surface` 的 far_corner、`surface_point_to_room`）：在 1e8 上限內最大乘積 ~1e16 < int64；寫一份「安全域證明」註解進檔頭。若要支援更大座標則關鍵路徑換 `__int128`/檢查乘。
- **驗收**：檔內有一節註解寫明安全域推導；debug 版加 `assert` 擋越界輸入。
- **檔案**：`current_geometry.c`。
- **測試**：以 1e8 上限的極端 scene 跑 debug 版，無 assert 觸發。
- **相依**：GEO-010。**估時 2h**。

### GEO-012 ⚡ 修「無結尾換行超長末行」靜默截斷
- **內容**：`parse_scene_file`：`fgets` 讀滿且無 `\n` 時，不論 `feof` 都再讀一個字元確認是否真的到檔尾；超長一律報錯。
- **驗收**：511+ 字元無換行的末行報「這一行太長」。
- **檔案**：~L4092。
- **測試**：tests/cases 加兩個檔：恰好 510 字元末行（過）、600 字元無換行末行（拒）。
- **相依**：GEO-002。**估時 45min**。

### GEO-013 ⚡ 修 511 字元合法行被誤殺
- **內容**：同上區段，或把 `SCENE_MAX_LINE` 定義為「含 \n\0」並把 buffer 加大 2。
- **驗收**：510 字元內容 + `\n` 的行可解析；511+ 字元才報錯，錯誤訊息寫明上限。
- **檔案**：~L2020、~L4092。
- **測試**：邊界行長 509/510/511 各一個 case。
- **相依**：GEO-002。**估時 45min**。與 GEO-012 摸同一區塊，**不平行**。

### GEO-014 ⚡ BOM 檢查改為長度感知
- **內容**：`if (line_no==1 && length>=3 && text[0]==0xEF && …)`；順便消 C28199。
- **驗收**：`cl /analyze` 不再有 C28199；1-byte 場景檔不誤判。
- **檔案**：~L4101。
- **測試**：tests/cases 加 1 字元檔、含 BOM 檔、偽 BOM（EF BB 41）檔。
- **相依**：GEO-002。**估時 30min**。

### GEO-015 ⚡ 未知 CLI 參數要報錯
- **內容**：argv 掃描迴圈加 else：`fprintf(stderr, "不認得的參數：%s\n")` + return 1；順便把 `--help` 印用法。
- **驗收**：`--scen` 打錯會 exit 1 並提示；`--help` 印全部參數 exit 0。
- **檔案**：main ~L4177。
- **測試**：run_tests 加 `--bogus` case。
- **相依**：GEO-002。**估時 30min**。

### GEO-016 ⚡ `--bench` 參數改用 strtol 並驗範圍
- **內容**：換掉 `atoi`：非數字/負數/0 報錯；上限 1e6 防呆。
- **驗收**：`--bench abc`、`--bench -5` exit 1；`--bench 10` 正常。
- **檔案**：main ~L4194。
- **測試**：手動三個 case。
- **相依**：無。**估時 30min**。

### GEO-017 錯誤訊息列出全部指令名
- **內容**：`apply_scene_line` 的「不認得的指令」改為從 `SCENE_COMMANDS` 表動態列出（現在漏寫 move/room/reset）。
- **驗收**：輸入 `foo` 時訊息含全部 8 個指令。
- **檔案**：~L4065。
- **測試**：互動輸入列打 `foo` 看狀態列。
- **相依**：無。**估時 30min**。⚡

### GEO-018 ⚡ scene 檔規格文件
- **內容**：`SCENE-FORMAT.md`：每指令欄位、單位、座標系圖、錯誤語義（哪行錯報哪行）、reset 的中途生效行為。
- **驗收**：文件與 `SCENE_COMMANDS` 逐列對得上；含 room 的六面盒完整範例。
- **檔案**：新增 `SCENE-FORMAT.md`。
- **測試**：文件內每個範例實際餵給程式驗 exit code。
- **相依**：無。**估時 1.5h**。

---

## 第 2 流：幾何核心正確性（RISKS C1/C2/C6、D1/D5）

### GEO-020 ⚡ 修 GDI 滑鼠反解的負值四捨五入
- **內容**：`gdi_screen_to_view`：`(Coord)(v + 0.5)` 改成 `(Coord)floor(v + 0.5)` 或 `(Coord)llround(v)`；pick_radius 同理（恆正但也要一致）。
- **驗收**：游標在版面左/上界外（mm 為負）時，unproject 回來的 UV 不偏 1mm；用 GDI 拖曳把 guide 拉到負值區域能對齊整數格。
- **檔案**：~L2642。
- **測試**：手動 GDI 驗 + 在程式加一行 debug 印 px→mm 對照表人工核對。
- **相依**：無（需 include math.h）。**估時 45min**。

### GEO-021 釐清並註解 unproject 的 det 恆 ±1
- **內容**：`view_unproject_on_surface` 的 `% det != 0` 在單位軸前提下永不觸發——把這個證明（det = N·into ∈ {-1,0,1}）寫進註解，或改成 `assert`；同時決定：若未來支援非軸向面，這裡要改成什麼。
- **驗收**：註解或 assert 就位；沒有「以為有用其實沒用」的防禦碼。
- **檔案**：~L1704–1733。
- **測試**：紙面證明 + 三視圖各拖一次 guide 確認行為不變。
- **相依**：無。**估時 1h**。⚡

### GEO-022 ⚡ 跨角材拾取改為取視線最近者
- **內容**：`scene_pick_at` 對多支角材同點命中時，比較 `distance4` 取最小（最近），而非「索引最後」。
- **驗收**：兩支角材在俯視圖重疊時，點到的是最靠近觀者那支的面。
- **檔案**：~L1750–1761。
- **測試**：scene：兩支角材同 UV 不同深度側（+n/-n），互動點選確認選中上層。
- **相依**：無。**估時 1h**。

### GEO-023 ⚡ move 之後錨點報告加「已過期」標記
- **內容**：`from_guides` 錨點在 guide move 後不再等於交點；`main` 報告與（未來）UI 狀態列在 guide 動過後加印「（錨點為放置當時的交點）」或重算交點並標 `(原 500,300 → 現 700,300)`。
- **驗收**：move 後的輸出不會把舊交點當現況印。
- **檔案**：~L3880、~L4436。
- **測試**：scene 檔寫 place → move → 看輸出文字。
- **相依**：無。**估時 1h**。

### GEO-024 place at-guides 的 guides 必須屬於同一面——補明確錯誤
- **內容**：現在靠 `guide_line_intersection` 的 surface_id 檢查間接拒絕；在 `apply_place_line` 先分別檢查 `guide_a->surface_id == surface_id` 給出「參考線不在指定面上」的明確訊息。
- **驗收**：跨面 guide 組合報新訊息；同面同方向仍報舊訊息。
- **檔案**：~L3828。
- **測試**：tests/cases 加跨面 guide case，比對錯誤文字。
- **相依**：GEO-002。**估時 45min**。⚡

### GEO-025 ⚡ 退化面（area2==0）策略文件化
- **內容**：`timber_project_faces` 跳過退化面是對的（輪廓在相鄰面邊上），但「skip 的面不可被點選」這個副作用要寫進註解；評估是否讓退化面以「線」形式可被拾取。
- **驗收**：註解寫明；若決定可拾取則拾取半徑內退化面以 segment 命中。
- **檔案**：~L1411、~L1739。
- **測試**：END 面在正視圖退化成線 → 確認能否被點（依決定驗收）。
- **相依**：無。**估時 1.5h**。

### GEO-026 ⚡ guide 與邊重合（offset=邊界值）行為定義
- **內容**：`guide_offset_in_range` 允許 offset == min/max，與邊重合；決定：允許（現狀，寫進文件）或警告。若允許，scene_draw_view 應避免 guide 虛線與 edge 實線完全重疊看不出來（例如稍微內縮 1px 或改色）。
- **驗收**：決定寫進 SCENE-FORMAT.md；重疊時圖上可辨識。
- **檔案**：~L448、~L1517。
- **測試**：scene：guide offset=0 與 offset=max_v 各一條，看 SVG。
- **相依**：GEO-018。**估時 1h**。

---

## 第 3 流：GDI / Win32 層（RISKS A2/A3、E1/E2/E4）

### GEO-030 ✅ 已做(2026-09-21) CreateFontW 失敗時不 SelectObject(NULL)
- **內容**：`gdi_text`：`font==NULL` 時改用 `GetStockObject(SYSTEM_FONT)` 或直接 return；消 C6387。
- **驗收**：`cl /analyze` 無 C6387；故意讓 CreateFontW 失敗（破壞字型名）時不當機、文字用預設字型。
- **檔案**：~L2400。
- **測試**：暫時把字型名改成不存在字串跑一次。
- **相依**：無。**估時 30min**。

### GEO-031 ⚡ gdi_color 加格式檢查
- **內容**：檢查 `hex[0]=='#'` 且長度 ≥7、其餘為 hex 字元；不合法回黑並可選 debug 印。
- **驗收**：`gdi_color(NULL)`/格式錯誤不再 UB；STYLE_SPEC 現值全部通過。
- **檔案**：~L2127。
- **測試**：單元測試或臨時 printf 驗三種壞輸入。
- **相依**：無。**估時 30min**。

### GEO-032 ⚡ bench_paint 早期 return 補資源釋放
- **內容**：`sink`/`sink_bmp` 任失敗時：釋放已建物件 + `ReleaseDC(NULL, screen)`；用 goto cleanup 或 helper。
- **驗收**：程式碼走查確認所有 exit path 釋放配對；無行為改變。
- **檔案**：~L3080–3087。
- **測試**：人工走查 + GDI 物件計數工具前後比較（可選）。
- **相依**：無。**估時 45min**。

### GEO-033 ⚡ 多視窗/多實例安全：`g_edit_orig_proc` 移進 GdiApp
- **內容**：全域 WNDPROC 改成每個 EDIT 用 `SetWindowSubclass`（comctl32）或把原 proc 存 `GWLP_USERDATA`，去掉全域。
- **驗收**：理論上開兩個視窗互不覆寫；單視窗行為不變（Enter 仍送 WM_APP_APPLY_INPUT）。
- **檔案**：~L2653、WM_CREATE ~L2732。
- **測試**：編譯後開視窗按 Enter 驗證指令仍生效。
- **相依**：無。**估時 1h**。

### GEO-034 ⚡ style 快取與 owned 路徑走查 + 註解
- **內容**：`gdi_select_style`/`gdi_release_style`/`gdi_cache_release` 三處的「誰刪誰」規則整理成一張所有權表放註解；並加 `assert`（越界 style 必走 owned）。
- **驗收**：註解表 + assert；AppVerifier/手動走查無洩漏。
- **檔案**：~L2164–2253。
- **測試**：連續 hover 全部 style 後關視窗，用 GDI 物件計數確認無洩漏。
- **相依**：無。**估時 1h**。

### GEO-035 ✅ 已做(2026-09-21) WM_CREATE 控制項建立失敗處理
- **內容**：`CreateWindowW` 三個控制項任一失敗時：status 顯示建立失敗或 graceful 降級（現在 NULL HWND 會繼續往下走，`MoveWindow(NULL,…)` 無害但 status_label=NULL 時 `gdi_set_status` 會對 NULL 呼叫）。
- **驗收**：控制項 NULL 時不當機；主視窗仍可用（僅少輸入列）。
- **檔案**：~L2702–2730、~L2568。
- **測試**：臨時把 class name 打錯模擬失敗。
- **相依**：無。**估時 45min**。⚡

### GEO-036 ⚡ 視窗縮到 0×0 / 最小化的 paint 路徑
- **內容**：`CreateCompatibleBitmap(0,0)` 會失敗已擋；但 `gdi_frame_transform` 在 client 寬高 ≤2·MARGIN 時 scale 可能 ≤0——已檢查 return。補：視窗極小時輸入列 MoveWindow 負座標防禦。
- **驗收**：把視窗拖到最小再還原，無異常、位圖重建正確。
- **檔案**：~L2672–2688、~L2497。
- **測試**：手動極端縮放。
- **相依**：無。**估時 45min**。

---

## 第 4 流：房間（room）功能收尾

### GEO-040 ⚡ room 六面盒範例檔入庫
- **內容**：新增 `room-box.scene`（六面封閉盒 + 一角材），收進 tests/cases。
- **驗收**：exit 0，輸出印「狀態：封閉（六面）」。
- **檔案**：新增 scene + tests 登錄。
- **測試**：GEO-002 跑過。
- **相依**：GEO-002。**估時 45min**。

### GEO-041 ⚡ room 一致性失敗的分類錯誤訊息
- **內容**：`room_bind` 現在只有一條通用訊息；回傳改 enum（面不存在/重複/槽位衝突/區間不一致/界值不吻合/lo≥hi），apply_room_line 各自翻譯。
- **驗收**：六種失敗各有一句可區分的訊息。
- **檔案**：~L3441、~L3958。
- **測試**：tests/cases 造六種失敗各一檔比對訊息。
- **相依**：GEO-002。**估時 1.5h**。

### GEO-042 ⚡ room 宣告與 guides/timbers 的歸屬檢查（警告級）
- **內容**：room 綁定後，檢查「該房的面上建立的 guide/放置的 timber」是否合理（例如 timber 放在房外面上給警告）。先只印 warning 不擋。
- **驗收**：定義「房外面」規則 + 文字報告出警告欄。
- **檔案**：apply_room_line / main 報告段。
- **測試**：故意把 timber 放非 room 面 → 出現警告。
- **相依**：GEO-041。**估時 2h**。

### GEO-043 room 體積/質心推導（報告用）
- **內容**：六面齊全時，由 bound/ext 推出房間尺寸並印「內部空間 W×D×H」。
- **驗收**：六面盒印出 4000×3000×2500。
- **檔案**：room_bind 結果結構 + main 房間段。
- **測試**：_t9 類 scene 看輸出。
- **相依**：GEO-041。**估時 1h**。⚡（與 GEO-042 摸不同段但同函式區，可平行但建議先後）

---

## 第 5 流：文件與導讀同步（RISKS F2/F9）

### GEO-050 ⚡ 修 check_panels.py 的三個失敗 callout
- **內容**：callout match 字串從 `"edge", 4, true,` 改成新表格式 `"edge", 4, 4, true,`；或改寬鬆比對。
- **驗收**：`check_panels.py` exit 0。
- **檔案**：`geometry-guide/current_geometry-導讀.html`（或 make_guide.py 內嵌模板）。
- **測試**：跑 check_panels.py。
- **相依**：無。**估時 30min**。

### GEO-051 重跑 make_guide.py 並補 room 章節 ← GEO-050
- **內容**：重產導讀 HTML；新增 §room：slot 表、區間一致性、內朝法向被拒的例子。
- **驗收**：check_panels 全綠；HTML 含 room 段落且其面板引用行號正確。
- **檔案**：`geometry-guide/make_guide.py`、產出 HTML。
- **測試**：check_panels.py + 肉眼開 HTML 看 room 面板。
- **相依**：GEO-050。**估時 1.5h**。

### GEO-052 ⚡ asm-analysis.md 標示版本或重產
- **內容**：檔頭加「對應 4,327 行版本、room 之前」；或重新 /FAcs 重產附錄函式表。
- **驗收**：讀者一眼知道它對應哪版。
- **檔案**：`asm-analysis.md`。
- **測試**：無（文件）。
- **相依**：無。**估時 30min**（只加標記）/ 2h（重產）。

### GEO-053 檔頭註解更新：功能清單補 room
- **內容**：`current_geometry.c` 頂部「目前整合版」清單加第 9 步（room 綁定）；「第一版限制」區更新（例如現在支援多面/房）。
- **驗收**：註解與實際功能一致。
- **檔案**：~L11–32。
- **測試**：對照 ARCHITECTURE.md §6。
- **相依**：無。**估時 30min**。⚡

---

## 第 6 流：程式碼衛生（RISKS F4/F6/F8）

### GEO-060 ⚡ 清編譯警告
- **內容**：刪 L1440 未使用的 `into`；7 個 `apply_*` 的 `count` 參數——只有 room 用到，其餘 `(void)count;`；重複 `#include <errno.h>` 刪一行。
- **驗收**：`cl /W4` 0 警告。
- **檔案**：~L1、~L1440、各 apply 函式頭。
- **測試**：build.bat 輸出無 warning。
- **相依**：GEO-001。**估時 30min**。

### GEO-061 ⚡ 源檔加 /utf-8 或 BOM
- **內容**：二選一：build.bat 加 `/utf-8`（建議，無侵入）；或源檔存成 UTF-8 BOM。兩者擇一並寫進 README。
- **驗收**：在 BIG5 系統字碼頁機器（或 `chcp 950` + 改碼測）中文輸出不亂碼。
- **檔案**：build.bat 或檔案本身。
- **測試**：`/utf-8` 下編譯，跑 --no-window 看中文。
- **相依**：GEO-001。**估時 30min**。

### GEO-062 emit_svg_three_views 檢查 fprintf 失敗
- **內容**：scene_render 後檢查 `ferror(out)`，失敗則刪除半成品 SVG 並回 false。
- **驗收**：模擬寫入失敗（例如 /dev/full 或唯讀檔）→ 回 false 且無半成品。
- **檔案**：~L1990。
- **測試**：`--out` 指向唯讀位置 → exit 1。
- **相依**：無。**估時 45min**。⚡

### GEO-063 ⚡ StyleSpec.text_mm 更名 text_px（SVG 實際當 px）
- **內容**：欄位更名 + 註解「GDI 端乘 scale 換 px、下限 10px」。
- **驗收**：命名不再誤導；行為不變。
- **檔案**：~L1180–1201、~L2335。
- **測試**：編譯 + 肉眼比對 SVG 字級。
- **相依**：無。**估時 30min**。

---

## 第 7 流：新功能（中張，可依優先序挑做）

### GEO-070 ⚡ `unplace` 指令
- **內容**：`unplace <角材id>`：placed=false、清錨點。注意 anchors 平行陣列對齊。
- **驗收**：unplace 後再 place 到新位置成功；文字輸出不再印該角材面。
- **檔案**：apply_* + SCENE_COMMANDS + main 報告。
- **測試**：scene：place→unplace→place 別處。
- **相依**：GEO-002。**估時 1.5h**。

### GEO-071 `delete` 指令（角材/參考線）← GEO-070
- **內容**：真刪除需搬移陣列元素——會弄亂 ScenePick 索引與 anchors 對齊；評估「墓碑標記」方案（count 不減、跳過未啟用項）。
- **驗收**：設計決定寫進程式；delete 後 id 可重用、索引不指錯。
- **檔案**：world_find_*、scene 走訪、pick。
- **測試**：place 3 支刪中間那支，SVG 剩 2 支。
- **相依**：GEO-070。**估時 2.5h**。

### GEO-072 ⚡ timber 互相碰撞/干涉檢查（警告）
- **內容**：放置時檢查新角材的 AABB 與既有角材的 AABB 是否重疊（全軸對齊所以 AABB 即精確）；重疊 → 警告不擋。
- **驗收**：兩支同位置角材 → 報告印「干涉警告」。
- **檔案**：apply_place_line、Timber 加 AABB 推導或即時算。
- **測試**：兩支疊放 scene。
- **相依**：無。**估時 1.5h**。

### GEO-073 ⚡ `guide` 指令支援以邊為基準（offset-from-edge 語法糖）
- **內容**：`guide id 面id 方向 edge:<邊id> ±d`——寫死 offset 時房間尺寸一改就要手改；以邊為基準的 offset 讓 scene 更有描述力。評估後實作或記錄不做的理由。
- **驗收**：新語法可解析且 offset = 邊位置 ±d；範圍仍由守門員把關。
- **檔案**：apply_guide_line、SCENE_COMMANDS。
- **測試**：scene 用新語法建線，與等價舊語法輸出一致。
- **相依**：GEO-002。**估時 2h**。

### GEO-074 ⚡ place 支援 B0 面接觸（翻面）
- **內容**：現在只能 A0 貼面；加 `face` 欄位（A0/B0）→ B0 貼面時角材 A 尺寸沿法線。評估對 `timber_place_a0_on_surface` 的一般化（place_face_on_surface）。
- **驗收**：B0 放置產出正確六面；向後相容（不寫 face = A0）。
- **檔案**：timber_place_*、apply_place_line、SCENE_COMMANDS（欄位數變，注意舊檔相容）。
- **測試**：同一 anchor 分別 A0/B0 貼，六面頂點人工核對。
- **相依**：GEO-002。**估時 2.5h**。

### GEO-075 ✅ 已做(2026-09-21) 文字輸出加「房間內部尺寸」與角材下料清單
- **內容**：cut list：每支角材 L×A×B + 所屬面 + 錨點；加總同規格數量。實用化第一步。
- **驗收**：room_a 輸出含「角材 1：1800×27×33 ×1」。
- **檔案**：main 報告段。
- **測試**：兩支同規格角材 → 數量 ×2。
- **實作**:`print_cut_list()` 依 (長度, 斷面 A, 斷面 B, 角色) 分組加總,印在逐支細節之後
  (總表是結論,放結尾才不會被幾十行座標沖掉)。排序固定為「長料先切」——長度遞減,
  同長度再依斷面與角色,**同一份場景永遠得到逐字相同的清單**(清單要能拿去比對)。
  未放置的角材不入清單。
- **刻意不用「L=」字樣**:`tests/run_tests.py` 的 `LEN_RE = r"L=(\d+)"` 會把輸出裡每個 `L=`
  都當成一支角材的長度,清單若沿用它會污染既有 128 個測試的長度比對。改用 `4000x20x20` 格式。
- **房間內部尺寸**:只印**兩側槽位都有面**的軸,用 `space_axis_bound()` 各查一次;
  推不出來的軸不猜、不補預設(R3)。
- **實測**:
  - `room_a`(3 支 2 規格):`4000x20x20 boundary x2（角材 90、91）` /
    `2960x27x33 primary x1（角材 1）` / `合計 3 支,2 種規格,總長 10960 mm`
    —— 驗收要求的「兩支同規格 → ×2」成立。
  - `_demo_ceiling`(7 支 3 規格):`合計 7 支,3 種規格,總長 20957 mm`。
  - `_rc_col_corner`(封閉六面):內部尺寸 X 4000 / Y 3000 / Z 2500。
  - `_ax_r16_top_drop`(top_drop 後 Y 軸少一面):**只印 X 與 Z,Y 不印**——R3 不猜。
  - `room_box`(只有 2 面):三軸都印不出來,整段不出現。
- **驗收已進測試**:`run_tests.py` 對上述三個場景加了 `contains` / `not_contains`;128/128 通過,
  `test_core_integrity` 80/80 通過。
- **相依**：無。**估時 1h**。

### GEO-076 ⚡ GDI 視窗顯示游標所在 mm 座標
- **內容**：status 列左側即時顯示 `view mm (x,y)` 與反解成功的 `(u,v)`。
- **驗收**：滑鼠移動時狀態列即時更新。
- **檔案**：WM_MOUSEMOVE、gdi_set_status。
- **測試**：手動。
- **相依**：GEO-020。**估時 1h**。

### GEO-077 ⚡ 場景檔 `include` 或分段
- **內容**：`include <相對路徑>` 引入共用片段（如標準房）；注意遞迴深度上限（≤8）與 line_no 報告。
- **驗收**：include 檔的錯誤報「檔名:行號」正確；循環 include 被拒。
- **檔案**：parse_scene_file（抽成可重入 + 堆疊）。
- **測試**：include 一個壞檔 → 錯誤定位正確。
- **相依**：GEO-002。**估時 2.5h**。

### GEO-078 ⚡ JSON 輸出（--emit-json）
- **內容**：場景幾何（面/邊/線/房/角材六面頂點）以 JSON 輸出，供外部工具（SketchUp 插件！）消費。手写 printf 即可，不引 library。
- **驗收**：輸出可被 python `json.loads` 解析；與文字輸出數值一致。
- **檔案**：新增 emit_json.c 段落 + main。
- **測試**：python 解析 + 抽樣對數值。
- **相依**：無。**估時 2h**。

---

## 第 8 流：結構演化（大張拆分前的準備，皆 ≤3h）

### GEO-080 ⚡ 抽出純幾何核心為可單元測試標的
- **內容**：把 §1–§5（型別+向量+表面+邊+線+角材）用 `#ifdef` 或拆檔方式讓一個 `test_geometry.c` 能 `#include` 進來直接呼叫 static 函式；先不切檔，只建立測試入口。
- **驗收**：`test_geometry.c` 能直接呼 `surface_point_to_room` 等，10 個斷言全過。
- **檔案**：新增 `tests/test_geometry.c`、current_geometry.c 加 `#ifndef CG_NO_MAIN`。
- **測試**：自建 main 跑斷言。
- **相依**：GEO-001。**估時 2h**。

### GEO-081 scene parser fuzz 測試 ← GEO-080
- **內容**：python 產生隨機 token 行 + 隨機截斷，跑 10k 次；exit code 只能是 0/1，不得 crash（Windows 下看 exit code 是否 0xC0000xxx）。
- **驗收**：10k 次無 crash；所有失敗都有 stderr 訊息。
- **檔案**：新增 tests/fuzz_scene.py。
- **測試**：跑一遍。
- **相依**：GEO-001、GEO-002。**估時 2h**。

### GEO-082 ⚡ 把 110+ 函式單檔拆成 geometry.c/view.c/scene_io.c/gdi_main.c 的計畫
- **內容**：只產出拆分計畫文件（不動手）：依賴圖、每檔公開介面、static→extern 清單。
- **驗收**：計畫經 review 後才動手；本工單只交文件。
- **檔案**：新增 docs/split-plan.md。
- **測試**：無。
- **相依**：GEO-080。**估時 2h**。

### GEO-083 ⚡ /analyze 與 /RTC1 納入建置
- **內容**：build.bat 加 `build_analyze.bat`（cl /analyze）與 debug 的 /RTC1；把「0 警告」列為完成定義。
- **驗收**：analyze 0 警告（現存 C28199/C6387 由 GEO-014/030 消）。
- **檔案**：build 腳本。
- **測試**：跑 analyze。
- **相依**：GEO-001、GEO-014、GEO-030。**估時 45min**。

---

## 工單統計

- 總數：**46 張**（GEO-001~004、010~018、020~026、030~036、040~043、050~053、060~063、070~078、080~083）
- 估時 30min：GEO-003、014、015、016、017、030、031、050、052(標記)、053、060、061、063
- 估時 45min~1h：GEO-001、004、010、012、013、020、021、022、023、024、026、032、033、034、035、036、040、043、062、075、076、083
- 估時 1.5h~3h：GEO-002、011、018、025、041、042、051、052(重產)、070、071、072、073、074、077、078、080、081、082

## 建議施工順序

1. **第一梯（全平行 ⚡）**：GEO-001、003、015、016、017、050、052、053、060、061、030、031 — 全部是獨立小修，清掉現有警告與壞檔。
2. **第二梯**：GEO-002（測試腳本）→ 之後所有改動都有安全網。
3. **第三梯（全平行 ⚡）**：GEO-010、012/013、014、020、021、022、023、024、026、032~036、040、041、062、063、075、076、078。
4. **第四梯（有相依）**：GEO-011←010、042/043←041、051←050、070→071、081←080。
5. **功能擴充**（GEO-072~078）與 **結構演化**（GEO-080~083）可依優先序插單。

---

## 變異測試（tests/mutate.py,40 個變異,2026-09 執行）

**結果**:36 殺死 / 4 存活(全部定讞為等效變異)/ 0 無效。
流程:`python tests/mutate.py` → 單點替換 → `_cl.bat` 編譯 → `run_tests.py` 全量(39 場景)。

### 等效變異定讞(任何測試都殺不死,公理結構保證)

| 變異 | 位置 | 等效理由 |
|---|---|---|
| M01 | `poly_point_on_edge` 直立邊端點含→嚴格 | 頂點恆為一條直立邊+一條水平邊的共同端點;水平邊分支的 u 範圍檢查未變異,仍接住所有頂點 |
| M09 | `boundary_contains_rect` 孔 bbox 相接當相交 | bbox 僅相接才進深層檢查,但頂點嚴格/邊穿入/罩住三檢查對純接觸全數放行 |
| M10 | 孔頂點嚴格在矩形內→含邊界 | 頂點在矩形邊上 ⇒ 該軸 bbox 必為相接 ⇒ 前置 bbox 快退已 `continue`,變異行不可達 |
| M23 | `pick_stop` 起點歧義(hits>1)放行 | 同座標兩面都涵蓋全寬 ⇒ 面所有者必撞掉逼近 cell(面積重疊)或邊界自體不合法(孔貼輪廓/孔孔相切)→ 結構不可達 |

### 本輪新增殺手場景(8 個)

`_mut_notch_straddle`(M08)、`_mut_reval_free_hole`(M18+M36)、
`_mut_through_boundary`(M19)、`_mut_free_hole_end`(M22)、
`_mut_edge_touch_only`(M24)、`_mut_grid_dup`(M31)、
`_mut_zero_len`(M35)、`_mut_neg_hole_ref`(M38)。

### 遺留觀察(非變異,未來可加強)

- 端面 FREE 檢查在兩處各自實作(放置路徑查外輪廓、auto span 查全部含孔);M22 能活下來正是因為放置路徑不查孔邊——若未來把孔邊 FREE 檢查也加進放置路徑,M22 會變等效。可考慮統一成單一公理實作點。
- 變異覆蓋的是「已枚舉的 40 點」;`collect_stop_faces` 的孔邊枚舉、`anchor_corner_from_rect` 的深度側、`grid` 下界檢查(M32 對側)等鄰近行尚未配對變異,後續可擴表。

---

## UI 重構衍生的 C 端工單候選(geometry-web Phase 1-5,2026-09-13)

> 來源:`geometry-web/docs/UI-REDESIGN-PLAN.md` §9 決策佇列 + 實作期間發現的 bridge 缺口。
> 這批全部屬 C 端(current_geometry.c / web_bridge.c)工單,UI 端已按「沒有就不做」處理。

### WEB-001 ✅ 已完成(2026-09-13,Q1 拍板做) `delete <kind> <id>`
- **內容**:刪除邊界面 / 參考線 / 空間成員關係,走既有交易重驗路徑。目前 UI 無法刪除任何物件,只能靠 undo。
- **驗收**:`delete boundary <id>` 後 `objects` 面數 -1;被刪面若為某空間成員,該空間 `closed` 正確重算;失敗(依他物引用)時回滾。
- **檔案**:`current_geometry.c`(指令表 + 交易)、`web_bridge.c`。
- **測試**:連續 delete + undo/redo 混合;刪除承載面後再 `render` 不殘留。
- **相依**:無。**估時 1.5h**。

### WEB-002 ✅ 參照物件結構化列舉
- **實作**：既有 `references` 一次回傳 guides、timbers、grids，包含承載面 id、參考線軸向及位置；UI 依承載面過濾，不再解析 dump 文字。
- **驗收**：空集合回空陣列；參照物件新增、移動、刪除後重新讀取一致。與 WEB-005 共用橋接回傳。

### WEB-003 🔶 部分完成(2026-09-14,RC Phase 6) 邊界面/參考線數量上限檢討(§9 Q1 附帶)
- **進度**:`WORLD_MAX_BOUNDARIES/PLACEMENTS` 8→16(commit ce02a80)——條帶裁切需 +4 面;兩間六面盒(12 面)現可共存。動態化/再加大仍開放。
- **內容**:`WORLD_MAX_BOUNDARIES = 8` 偏小——六面盒一間房就用掉 6 個;測試中多物件場景易撞界。評估提到 32/64 或改動態配置。
- **驗收**:同時建立兩間六面盒(12 面)不報「邊界面的數量超過上限」。
- **檔案**:`current_geometry.c` 常數定義區。
- **測試**:回歸全綠 + 新增 12 面場景。
- **相依**:無。**估時 1h**(若動態化另估)。

### WEB-004 ✅ 已由前端實作(Q2,commit 69f59fe) 正交頂點插入
- **結果**:核心公理拒絕共線頂點,正確原語是「矩形凹口(4 頂點)」;已於面內工具實作——點邊自動插凹口,走既有 `boundary` 重宣告交易,核心再驗。C 端原語不再必要,留檔備查。
- **驗收**:在邊中段插入合法凹口後 `boundary` 指令重驗通過;非法位置(撞孔/越界)回錯誤不落地。
- **檔案**:`current_geometry.c`。
- **測試**:四邊各插一次 + 撞孔案例 + undo。
- **相依**:無。**估時 2h**。

---

## 第 9 流：構件層級（公理層 D15–D17、I18–I22、R18–R20；2026-09-15 立）

> 來源：TimberScript Core Charter §2a 與拍板清單，形式化為「層級是段的性質」（D16）。
> 工單順序即依賴順序；每張都以公理層條文為驗收基準，條文與實作不一致時**改實作**。

### GEO-090 ⚡ `timber` 加 `role` 子句 + 場景檔遷移
- **內容**：`apply_timber_line` 解析 `role boundary|primary|secondary|custom [priority N]`（D15）；`Timber` 加 `role`/`cut_priority` 欄位；`world_dump_dsl` 輸出；沒 role / custom 沒 priority / priority 配非 custom → 拒絕（I18）。所有 `*.scene` 夾具與 web 六面盒模板、canvas_test/cdp_test 內嵌的 `timber` 行全部補角色。
- **驗收**：舊夾具不補角色時 parse 拒絕且訊息指名行號；補完後 dump→loadfile→dump 逐字相同；`newid`/`objects`/`delete` 不受影響。
- **檔案**：`current_geometry.c`（apply_timber_line 7640、dump 8316 附近）、`geometry-web/web_bridge.c`、`*.scene`、`geometry-web/app.js` 角材表單。
- **測試**：canvas_test 加「無 role 拒絕」「custom 無 priority 拒絕」「dump round-trip」。
- **相依**：無。**估時 2h**。

### GEO-091 主支軸一致（D17、I21）
- **內容**：`world_revalidate` 與 `apply_place_line` 內推導承載面主支軸（全部 primary 長度軸唯一；無 primary 時取 boundary 的垂直方向）；boundary/secondary 與主支軸平行 → `V_PRIMARY_AXIS`。
- **驗收**：同面第二支 primary 換軸 → 拒絕；先放 boundary 再放與它平行的 primary → 拒絕；刪掉唯一 primary 後軸由 boundary 推得。
- **檔案**：`current_geometry.c`。
- **測試**：夾具 `_role_axis_*.scene` 三個 + canvas_test。
- **相依**：GEO-090。**估時 1.5h**。

### GEO-092 端面優先序與延伸段（I19、I22）
- **內容**：`resolve_auto_span`（6436）與明寫放置的端面檢查：每個端面所頂擋面的擁有者優先級必須 < 自己（外輪廓/孔邊/柱面 = 0；轉角兩支 boundary 互頂例外）；違反 → `V_CUT_PRIORITY`。boundary 的固定段/延伸段切分（D16）：延伸段端面豁免 I19；延伸段側面作擋面時以優先級 2 計；非 boundary 角材不得有超出定位邊的段。
- **驗收**：主支端面頂 RC → 拒絕；副支端面頂 RC → 拒絕；主支端面頂副支側面 → 拒絕；L 形內邊 boundary 延伸過凹角停在長主支側面 → 接受且長主支 footprint 不變；同一支延伸段被主支端面頂 → 拒絕、被副支頂 → 接受；凸角處延伸 → 因 I5 出界拒絕（不需新錯誤碼）。
- **檔案**：`current_geometry.c`（collect_stop_faces 6244、resolve_auto_span 6436、apply_place_line 7979）。
- **測試**：夾具 `_role_priority_*.scene` 六個（對應上列驗收）+ 變異殺手（把 boundary 改 primary 必須被拒）。
- **相依**：GEO-090、GEO-091。**估時 3h**。

### GEO-093 邊界材整條覆蓋 + 角色衍生屬性（I20、R18）
- **內容**：R18 的 `onBoundary` / `coversEdge` / `boundaryEdge` 純幾何推導（只看外輪廓、不看孔邊、不看錨法）；I20：boundary 的固定段 ⊇ 邊區間、邊為 FIXED 外輪廓邊且 ⊥ 主支軸，否則 `V_BOUNDARY_ROLE`（訊息含料件、邊索引、覆蓋長度/邊長）；secondary 必 onBoundary=false。bridge `objects` 的 timbers 與 `dump` 註解一併輸出三個屬性。
- **驗收**：用 `through` 貼齊邊的料 onBoundary=true；at-edge 放卻被裁短的料 coversEdge=false 且若宣告 boundary → 拒絕；孔邊上的料 onBoundary=false；`objects` 回傳欄位存在。
- **檔案**：`current_geometry.c`、`web_bridge.c`。
- **測試**：夾具 `_role_cover_*.scene` 四個 + canvas_test 讀 objects 欄位。
- **相依**：GEO-092。**估時 2.5h**。

### GEO-094 連坐重驗（R20）+ 變異測試
- **內容**：刪除/移動/重宣告任一角材後同面全部角材重驗 I19–I22 與 R18，任一不過整筆回滾。補變異測試 M41–M50：各拿掉一條不變量的檢查，對應殺手夾具必須能抓到。
- **驗收**：刪掉被延伸段頂住的長主支 → 延伸段失去擋面 → 整筆拒絕（不留半成品）；`_run_tests_cmd.py` 全綠。
- **檔案**：`current_geometry.c`、`tests/`。
- **測試**：如上。
- **相依**：GEO-093。**估時 2h**。

### GEO-095 web UI：角色與層級可見
- **內容**：面內「角材」分頁的表單加角色選單（預設 primary；custom 顯示 priority 欄）；面內圖層列與卡片顯示角色徽章與 onBoundary/coversEdge；`V_CUT_PRIORITY`/`V_BOUNDARY_ROLE`/`V_PRIMARY_AXIS` 的 toast 原文顯示並高亮相關兩支料；DOM-CONTRACT 補新 id。
- **驗收**：cdp_test 新段：放 boundary→primary→secondary 各一支成功；放與主支軸平行的 boundary → toast 且畫面高亮；L 形延伸案例在 UI 內可完成。
- **檔案**：`geometry-web/app.js`、`app.css`、`index.html`、`cdp_test.js`、`docs/DOM-CONTRACT.md`。
- **測試**：cdp_test。
- **相依**：GEO-093。**估時 2.5h**。

### GEO-096 ⚡ 導讀與文件同步
- **內容**：`make_guide.py` 補「構件層級」章節（D15–D17、I18–I22、R18–R20 對應原始碼面板）、重跑、`check_panels.py` 全過；`geometry-model-v2.md` 補一節說明與 TimberScript Charter 的對應與差異（段框架取代延伸例外）。
- **驗收**：check_panels unresolved: none；導讀頁能點到 `apply_timber_line` 的 role 解析與 `V_CUT_PRIORITY` 判定處。
- **檔案**：`geometry-guide/make_guide.py`、`geometry-model-v2.md`。
- **相依**：GEO-090～094。**估時 1.5h**。

---

## 第 10 流：網格來源化與面材推導（公理層 D10、D10a、D18、I10、I13、I23、R6(c)、R13、R21；2026-09-16 立）

> 來源：timberscript-studio Core 的 `reference_grid` 模型（14 golden 簽核），形式化為「起算點具體化」（D10a）與「between 只買走唯一性、不買走物理條件」（R21）。
> 公理層條文已於 2026-09-16 開工前落版（改版前備份 `公理層.md.bak-geo097`）；工單順序即依賴順序，每張都以公理層條文為驗收基準，條文與實作不一致時**改實作**。
> 使用者拍板的八項決定見 `~/.claude/plans/linked-frolicking-hennessy.md`；其中三項最容易被誤改：**只存來源不存展開值**、**不引入 heap 配置**、**gap 奇數拒絕不取下取整**。
> 變異 id 從 **M51** 起（M41–M50 已由未完成的 GEO-094 預留）。
> **收流關卡**：本流全部完成後必須跑一次完整 40+ 個變異（`python tests/mutate.py` 不帶參數），
> 因為只跑子集會覆寫 `tests/mutants_results.json`；GEO-097 當下是先跑 M31–M33，再把結果併回備份 `tests/mutants_results.json.bak-geo097`。

### GEO-097 ⚡ `ReferenceGrid` 來源化重構（純重構，行為不變）
- **內容**：`ReferenceGrid` 改成 `GridAxisDef axis[2]`（1285），新增 `GridSource` 列舉（NONE / EXPLICIT / SERIES / PANEL）；`GRID_MAX_LINES` 32→64；新增唯一展開入口 `grid_axis_lines` 與薄包裝 `grid_line_coord`，本票只實作 EXPLICIT 分支；`grid_is_valid`（1306）改成迴圈跑兩軸、外接區間檢查移進 `grid_axis_lines`；`apply_grid_line`（8486）、`apply_place_line` 的 at-grid 分支（8800）、`world_dump_dsl`（11121）改用新欄位；死程式碼 `world_find_grid`（8384）復活並補 `world_find_grid_mut`，取代 8526／8802／10820 三處 inline 迴圈。
- **驗收**：`python _run_tests_cmd.py` 全綠且**輸出逐字不變**；`python tests/mutate.py M31 M32 M33` 仍 killed；dump→loadfile→dump 逐字相同；明寫 65 條座標 → reject「超過單軸上限」（現況 33 條的拒絕路徑無測試，本票補上）。
- **檔案**：`current_geometry.c`（1270-1348、8384-8393、8486-8643、8800-8838、10820、11121-11140）。
- **測試**：`_edge_grid_overflow.scene` 一筆進 `TESTS`；其餘靠既有夾具回歸。
- **相依**：無。**估時 3h**。

> **GEO-097 完成紀錄（2026-09-16，尚未 commit）**
> 關卡:編譯無警告;`_run_tests_cmd.py` 61/61,既有 60 筆與改版前**逐字相同**;
> 變異 M31/M32/M33 全 killed、0 invalid（M32 錨點已從 `grid_is_valid` 搬到
> `grid_axis_lines` 的 `if (out[k] < lo || out[k] > hi)`，確認全檔唯一）;
> 27 個 accept 夾具的 `dump` 輸出新舊**逐字相同**;`check_panels.py` 40 panels / unresolved: none。
> **記憶體實測**（不是估算）:`sizeof(ReferenceGrid)` 536 → **1176** bytes、
> `sizeof(World)` 121608 → **126728** bytes（+5120，+4.2%）。
> World 有 65 份靜態快照（`g_hist_undo[32]` + `g_hist_redo[32]` + group base）→ BSS 約 **+325 KB**;
> `World backup = *world;` 兩處是函式區域變數，單一呼叫框架約佔 **124 KB** 堆疊
> （改版前已是 119 KB，非新增的風險類別，但 GEO-106 若把 `WORLD_MAX_GRIDS` 提到 16 要重算）。
> **複驗提出的兩點觀察（非 FAIL，留給後續票）**:
> (1) `grid_line_coord` 取索引前會重跑 `grid_axis_lines`，連帶重驗 I10;舊版 at-grid 只比對
>     `u_count/v_count`，不重驗座標合法性。這是**刻意收緊**、且與 GEO-099 的 I23(b) 同向，
>     但目前 DSL 路徑不可達，GEO-099 應補一條回歸測試把它釘住。
> (2) 全檔無 `World` 的 `fwrite/fread` 或固定位元組序列化假設，歷史快照與 memmove 都用
>     `sizeof(World)` 動態算，容量放大不會打到任何序列化契約。

### GEO-098 `series` 來源（等差簡寫）
- **內容**：`apply_grid_line` 軸段解析加分派——`u`／`v` 後第一個 token 是 `series` 則吃 `start step count`（座標一定過 `parse_i64`、`series` 過不了，故無歧義）；`grid_axis_lines` 的 SERIES 分支（第 k 條 = start + k·step）；`step ≤ 0`／`count == 0`／任一條出界 → 拒絕；`world_dump_dsl` 輸出 `u series <start> <step> <count>`；`SCENE_COMMANDS` 的 grid 列（11390）usage 更新。
- **驗收**：`grid 1 on 1 u series 1000 2000 2` 與 `grid 1 on 1 u 1000 3000` 推出相同格線、相同角材長度（`lengths` 逐一相同）；dump 輸出 series 形式且重放逐字相同；`step 0`／`count 0`／尾端出界三種 reject 且訊息可辨。
- **檔案**：`current_geometry.c`。
- **測試**：`_test_grid_series.scene`（對照 `_edge_grid_twoline.scene`）、`_edge_grid_series_out.scene`、`_edge_grid_series_step0.scene`。
- **相依**：GEO-097。**估時 2h**。

> **GEO-098 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 65/65;`_test_grid_series.scene` 推出的長度 `[4000, 4000, 2960, 2960, 1973]`
> 與明寫版 `_edge_grid_twoline.scene` **逐一相同**，等價性成立;
> dump 輸出的是來源形式 `grid 1 on 1 u series 1000 2000 2`（不是展開座標），往返逐字相同;
> `check_panels.py` unresolved: none。

### GEO-099 ⚡ grid 交易化 + I23 網格引用鎖
- **內容**：`apply_grid_line` 回寫路徑改走交易——既有槽位用 `world_replace_object`（7258），新增槽位用 `World backup` + `world_revalidate`；移除 8584-8591 的「同軸一律不可重宣告」，改成 I23(a) 守門：對每個 `anchors[i].ref_grid == id && ref_grid_axis == axis` 的已放角材，用**舊定義**與**候選定義**各推一次該索引座標，不相等或候選推不出來 → `V_GRID_LOCKED`；`world_revalidate` 的角材迴圈加 I23(b)；`delete grid` 守門（10827）訊息統一成 `V_GRID_LOCKED`。
- **驗收**：往既有明寫軸追加格線 → accept；改動已錨定索引的座標 → reject `V_GRID_LOCKED`；錨在 u 軸後仍可補 v 軸 → accept；重宣告使某條被錨定的線消失 → 整筆回滾且 `dump` 與先前逐字相同；`_edge_grid_twoline.scene` 仍 accept 且 lengths 不變。
- **檔案**：`current_geometry.c`（8486-8643、7286-7330、10817-10837）。
- **測試**：`_test_grid_redeclare.scene`、`_edge_grid_locked.scene`、`_edge_grid_locked_other_axis.scene`、`_mut_grid_locked.scene`。變異加 **M51**（I23(a) 的座標比對拿掉）、**M52**（grid 回寫不呼叫 `world_revalidate`）。
- **相依**：GEO-097，可與 GEO-098 平行。**估時 3h**。

> **GEO-099 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 70/70;27 個 accept 夾具往返通過 30 筆、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M31/M32/M33/M51/M52 全部取得**真實死因**
> （M51 由 `_edge_grid_locked.scene` 的「應拒絕但接受」抓到，正是設計的殺手）。
> 合併後變異紀錄 42 個:38 殺 / 4 個既知等效存活 / 0 無效。
> **實作偏離規劃的一點**：`world_find_grid` 在 `world_revalidate`(7504) 被用到、
> 卻定義在 8557，補了一行前向宣告。
> **已知覆蓋缺口**：I23(b)（重驗時索引必須仍推導得出）目前**沒有殺手夾具**——
> EXPLICIT/SERIES 的條數是固定的，承載面一縮小 `grid_is_valid` 就先拒了，
> I23(b) 抓不到任何它抓得到的東西。要等 GEO-100 的 PANEL 來源落地
> （條數隨面大小變動）才變得可達，**GEO-100 必須補這條殺手**。
> **驗證環境警告**：跑變異時務必確認死因不是「例外 [WinError 4551]」——
> 那是 SAC 擋掉 `_mut.exe` 的假死，見 GEO-108。

### GEO-100 面材推導 PANEL_LAYOUT 對縫（D10a）
- **內容**：`GridAxisDef` 的 panel／gap／anchor 三欄；解析 `panel <p> gap <g> [from <c>]`，**anchor 宣告當下具體化**（未寫 `from` 取當下 `placement_local_bounds` 的該軸下界）並寫進定義；`grid_axis_lines` 的 PANEL 分支照 D10a 直譯（`c_k = a + k·T + panel + gap/2`，產生條件 `a+(k+1)·T < hi`）；gap 奇數／panel ≤ 0／gap < 0／anchor 出界／超上限各自的人話訊息；dump 輸出 `u panel P gap G [from A]`（`from` 只在 `anchor_explicit` 時輸出）；**`geometry-web/app.js:2252-2256` 的 `^grid` regex 收緊成只吃純數字串**，認不得的來源型式忽略不畫（停損，見流末）。
- **驗收**：3600×3000 面、`u panel 400 gap 20` → **恰 8 條線：410 / 830 / 1250 / 1670 / 2090 / 2510 / 2930 / 3350**；在 index 0 與 index 7 放 auto 主支，長度與明寫等價場景一致；`gap 21` → reject「縫寬必須為偶數」；`panel 1 gap 0` 於 4000 面 → reject「超過單軸上限」；面寬 300 小於 panel 400 → accept 且該軸零條線，此時 at-grid index 0 → reject「本軸共 0 條」；dump 重放逐字相同；web 面內編輯器載入 PANEL 場景不畫出錯誤格線。
- **檔案**：`current_geometry.c`、`geometry-web/app.js`（一行 regex）。
- **測試**：`_test_grid_panel.scene`、`_edge_grid_panel_odd_gap.scene`、`_edge_grid_panel_overflow.scene`、`_edge_grid_panel_empty.scene`、`_edge_grid_panel_from.scene`（L 形面 + 明寫 from）、`_mut_grid_panel_center.scene`。變異加 **M53**（中心線改成縫起點）、**M54**（產生條件 `< hi` 改 `<= hi`）、**M55**（gap 奇數改放行取下取整）。
- **相依**：GEO-099。**估時 4h**。

> **GEO-100 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 79/79;33 個 accept 夾具往返通過、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M53/M54/M55 全部取得真實死因。
> **公式已由實測釘住**（不是估算）:3600 寬的面配 `panel 400 gap 20` →
> 恰 8 條線，index 0 的中線 **410**、index 7 的中線 **3350**
> （角材原點 424 與 3364 減去半寬 14）；index 8 被拒且訊息寫「本軸共 8 條」。
> `from 1000` → index 0 的中線 **1410**（原點 1424），起算點具體化語意成立。
> **偏離規劃的一點**：規劃寫「`from` 只在 anchor_explicit 時輸出」，實作改成**一律輸出**。
> 理由:起算點已具體化進定義（D10a），省略它的話，承載面事後縮小時重放會取到不同的 a，
> R4 的「重放逐字相同」就破了。
> **2026-09-22 更正(GEO-173)**:下面這段在寫下當時(2026-09-16)是對的,但 2026-09-18
> R6(e)/I23 語意反轉(凍結 → 重算)之後,M56 變成**等價變異**:`world_validate_derived`
> 只在 `reference_rebuild` 成功後才跑,而 `reference_rebuild` 已對每個 AT_GRID 角材先跑
> 同一個 `grid_line_coord`,索引消失會先在那裡失敗;被變異那行永遠是 no-op。
> 實證:面縮到索引 7 消失的夾具,原始版與變異版輸出逐字相同。已在 `mutate.py` 標記為等價。
>
> **覆蓋缺口（誠實記錄）**：I23(b) 仍**沒有隔離殺手**，變異 **M56 存活**。
> 原因不是它等效，而是構造不出「線消失但所有角材都還在面內」的場景——
> 被錨定的主支必須靠沿 u 的邊界材提供擋面（主支不得直接頂外輪廓，見 GEO-109），
> 而那些邊界材必然橫跨全寬，面一縮就先出界（I5）觸發回滾。
> `_edge_grid_panel_shrink.scene` 保留為「縮面整筆回滾」的回歸測試，但它擋的是邊界材出界。
> 若 GEO-109 放寬「只有 boundary 可頂 RC」，這個殺手就做得出來。

### GEO-101 ⚡ `between(face, face)` 明寫兩端（D18、R21）
- **內容**：`StopFaceRef` 型別與解析（**重用 `parse_edge_ref` 8399**，只多一個 `t<id>` 分支）；`apply_place_line` 選擇器區（8886）加 `between` 分支，與 `through` 互斥；`resolve_auto_span`（6895）加 `const StopFaceRef *between` 參數，在選區間（7050）與兩端擋面檢查（7083）插入 R21(b)(c)(d) 的指名路徑——改用 `pick_stop` 的**條件**去驗被指名的那一面，而不是數有幾面；`SpanStatus`（6864）尾端追加 `SPAN_BETWEEN_BLOCKED`、`SPAN_BETWEEN_AMBIGUOUS`；`SCENE_COMMANDS` 的 `place` max_fields 12→**13**（11401）。
- **⚠ 連動**：`geometry-guide/make_guide.py:574` 的 callout `"place", 8, 12, true,` 必須同步改 13，否則 `check_panels.py` 會 unresolved（已實測確認）。
- **驗收**：`_edge_stop_ambiguous.scene` 的歧義場景改用 between → accept 且長度等於明寫值；between 指到 FREE 邊 → reject；兩端之間被已放角材擋住 → reject；`between t5 t9` 有兩組合法配對 → reject 並列舉全部候選；through 與 between 同寫 → reject；I19 違規的 between（主支端面頂 RC 邊）仍 reject `V_CUT_PRIORITY`；`check_panels.py` exit 0。
- **檔案**：`current_geometry.c`（6864-6875、6895-7125、8399-8444、8886-8896、11401-11406）、`geometry-guide/make_guide.py`。
- **測試**：`_test_between.scene`、`_edge_between_free.scene`、`_edge_between_blocked.scene`、`_edge_between_ambiguous.scene`、`_edge_between_conflict.scene`、`_role_between_priority.scene`。變異加 **M56**（between 跳過 FREE 邊檢查）、**M57**（between 跳過逐 cell 合法性）。
- **相依**：GEO-097（不依賴 PANEL，可與 GEO-100 平行）。**估時 4h**。

> **GEO-101 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 85/85;34 個 accept 夾具往返通過、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M57/M58 全部取得真實死因。
> **等價性已釘住**：`_test_between.scene` 與 `_edge_stop_ambiguous.scene` 是同一個幾何，
> 副支改用 `between t1 t5` 之後長度 `[1000, 1960, 3000, 2000, 3946]` **逐一相同**——
> between 只換寫法、不換結果。
> **偏離規劃的三點**：
> (1) `place` 的欄位數不是 12→13 而是 12→**15**。at-grid 帶 between 是 13 欄，
>     但要讓「through 與 between 同時寫」講得出互斥訊息（而不是被籠統的欄位數錯誤蓋掉），
>     表上限必須放到 15;at-grid／at-edge 兩個分支各自的 count 檢查也一併放寬。
>     `make_guide.py` 的 `"place", 8, 12, true,` callout 已同步成 15。
> (2) R21(e) 的夾具原本想用 primary，但 D17 的主支軸一致（I21）會先擋下，
>     改用 `custom priority 2`——D15 明寫 custom 不取得任何角色專屬義務，
>     所以 D17 不管它，能單獨把 I19 逼出來。
> (3) 規劃寫「`between t5 t9` 有兩組合法配對 → reject 並列舉」。實作與條文都照做了，
>     但**這條路徑目前不可達**：被指名的角材側面必須涵蓋端面全寬（R21(a)），
>     代表那支角材的本體橫跨中線，於是只有「兩支之間」那一組配對落得進合法區間。
>     變異 M58（拿掉區間檢查）的死因輸出可以看到 4 組候選被收斂成唯一的 [1020,2980]，
>     證明列舉邏輯會動。這是 R21(d) 要求的防禦性分支，保留但無夾具。

### GEO-102 ⚡ 導讀與文件同步（公理層已先落版）
- **內容**：`公理層.md` 已於 2026-09-16 開工前落版，本票不再改它，只做下游同步——`geometry-model-v2.md` 補一節說明與 timberscript-studio `reference_grid` 模型的對應與差異；`make_guide.py` 補「網格來源化」章節（`GridAxisDef`／`grid_axis_lines`／D10a 公式三個面板）並重跑；`current_geometry.c:6833-6836` 那段「未經授權不得修改公理層」的註解改成指向已修正的 I22 條文。
- **驗收**：`check_panels.py` unresolved: none 且 exit 0；導讀頁能點到 `grid_axis_lines` 的 PANEL 迴圈與 `V_GRID_LOCKED` 判定處；公理層每一條新條文都能在 `TESTS` 找到至少一筆對應夾具（對照表附在本票下方）。
- **檔案**：`geometry-guide/make_guide.py`、`geometry-model-v2.md`、`current_geometry.c`（註解）。
- **相依**：GEO-097～101。**估時 2.5h**。

### GEO-103 RUNNING_BOND 交丁排法（phases、row）— 第 2 期，條文未定案前不得實作
- **架構**：`GridAxisDef` 加 bond／phases／phase_count（`GRID_MAX_PHASES 8`）。交丁必須明寫 phases（不猜）；軸 X 宣告 RUNNING_BOND 時，垂直軸 Y 必須也是 PANEL_LAYOUT——「排」就是 Y 軸的面材本體 band。第 r 排的 X 軸格線 = `c_k + phases[r % phase_count]`。主方向無貫穿線，故 `at-grid` 不帶 `row` → 拒絕；帶 `row n` 時除了給中線，**同時給跨距的接觸範圍**（第 n 排在 Y 軸的 band 區間），直接餵進 `resolve_auto_span` 既有的 `has_contact／contact_lo／contact_hi` 參數——逐排縫段因此從 R6 自動掉出來，不需要新的幾何機器。
- **擬立條文**：D10b、I24、R22。
- **驗收方向**：兩相位交丁，第 0 排與第 1 排的同索引格線相差半週期；不帶 row 放置 → reject；row 超出排數 → reject；裁短片所在排的格線條數比完整排少。
- **相依**：GEO-100。**估時 6h**（含條文）。

### GEO-104 `support_step` 板縫落骨約束 — 第 2 期
- **架構**：宣告式約束，在 grid 宣告當下檢查。支撐線 = `lo + j·(span／n)`；`span % n != 0` → 拒絕；每條縫中心線必須與某條支撐線重合，否則拒絕。與 D10a 推導解耦：先推縫、再驗落骨。
- **⚠ 開工前需拍板**：「縫中心與支撐線座標相等」是直譯，實務也可能是「縫落在骨材寬度範圍內」（骨材 27 寬，縫中心在骨材 ±13 內即算落骨）——那是區間包含而非座標相等，條文寫法完全不同。
- **相依**：GEO-103。**估時 3h**。

### GEO-105 `subgrid` 子網格 — 第 3 期
- **架構**：`subgrid <id> parent <gid> axis u scope each_cell divisions by_span(v, <band...>)`。以父 cell 為單位等分某軸，band 是 `[min,max)` 依另一軸跨度選等分數；cell 寬不能整除 → 拒絕；交丁時等分的是完整面材本體，裁短片只保留落在片內的線。子網格本身是一個 `ReferenceGrid`，只存 parent_id／axis／bands，**仍然只存來源**。
- **擬立條文**：D19、I25、R23。
- **相依**：GEO-103。**估時 8h**。

### GEO-106 「一面一格」規則重定 + 容量重評 — 第 3 期
- **內容**：現行 8540-8546 的「一面一格」與子網格直接衝突（同面）。改成「一面一主格 + 若干子格」，定義刪父格時子格的連坐，`WORLD_MAX_GRIDS` 8→16，並重評 `GRID_MAX_LINES` 是否要到 96。
- **註**：公理層 D10 **刻意沒有重述「一面一格」**（它目前只活在實作與程式碼註解的 G1，I10 原文也沒寫），就是為了不在這裡挖坑。
- **相依**：GEO-105。**估時 3h**。

### WEB-005 ✅ 網格來源編輯器與推導線渲染
- **實作**：沿用既有 `references` 一次回傳 guides、timbers、grids；各軸新增來源定義欄位，推導線仍由核心唯一的 `grid_axis_lines` 產生。`grid-preview` 在 World 副本上走同一個網格解析與驗證，供面內編輯器即時預覽。UI 可獨立設定 u/v 的明寫、等差、面材來源，編輯既有網格並回填參數。
- **驗收**：預覽不改 World；明寫／等差／面材的線與儲存後相同；奇數縫寬依 D10a 向下取整；非法來源顯示錯誤且保持原網格；既有角材引用與 I8a 影響預覽仍走正式 `line` 交易。`tests/test_reference_contract.py` 與 `geometry-web/cdp_test.js` 覆蓋核心與瀏覽器流程。
- **範圍**：TimberScript 的施工相位、支撐步距與子網格須等本專案 D10b/I24/R22、D19/I25/R23 條文定案，未併入此票。

### WEB-006 ✅ 主網格格線的構件角色預設（2026-09-27）

- **決策**：使用者逐條審閱並批准 D10／D15／I10／I23 修訂。主網格選一個主支長度方向；沿該方向的格線預設 `primary / 2`，垂直格線預設 `secondary / 3`。邊界材仍按既有 D17／I20 判定 `boundary / 1`。格線只提供放置預設，角材宣告仍明寫角色且可明確覆寫。
- **相容性**：舊場景缺 `main-along` 時保持可讀且角色未設定；新圖形化建網格須選主支方向。改方向不改已存在角材的角色與格線引用。
- **實作與驗收**：核心保存、重放及交易式驗證方向；橋接回傳逐線角色／優先級；畫布以角色區分格線，可點格線放材，表單預填但保留手動角色。參考契約、正典閱讀器同步與實際瀏覽器流程均驗證。
- **保留**：D19／I25／R23 的子網格父格、等分、交丁與容量規則尚未定案，仍不得實作。

### 第 10 流的 web 停損說明（已解除）
先前 dump 的 `^grid` 正則解析會把 `panel` 來源誤讀成 `NaN`。現行面內渲染讀 `references` 的核心推導座標，WEB-005 也用相同來源預覽，因此這條風險已解除。

### GEO-107 ✅ 已完成(2026-09-16) 定位邊改成純幾何推導,不再讀 anchor_kind
- **狀態**：2026-09-16 於 GEO-097 的往返驗證中發現，**既有缺陷**（改版前後同樣重現，與網格來源化無關）。尚未修，需先拍板修法。
- **現象**：`_role_ext_stop_primary.scene` 可正常載入，但 `dump` 出來的結果無法重放——
  `place 4 on 1 at-edge e2 +u +n` 被 dump 成 `place 4 on 1 at 1014 1000 +u +n`，
  重放時回報 `V_CUT_PRIORITY：角材 4（優先級 1）端面頂到角材 3（優先級 2）側面`。
  27 個 accept 夾具中只有這一個踩到；其餘 26 個往返逐字相同。
- **成因**：D7 明訂「錨點 = place 當下凍結的 uv + **放法記錄**（anchor_kind、參照、through 等）」，
  但 `world_dump_dsl` 只輸出凍結的 uv 與明寫長度，把 `anchor_kind` 與 `ref_edge` 丟掉。
  重放後 `anchor_kind` 變成 `ANCHOR_AT`，而 `anchor_edge_interval` 要求 `ANCHOR_AT_EDGE`
  才認得定位邊，於是 D16 的固定段／延伸段切分不成立、I22 的豁免失效，
  端面改由 I19 裁決（1 vs 2，需 2 < 1）而被拒。
  幾何完全沒變，變的只有「這支料還算不算有延伸段」這項**放法**資訊。
- **這違反的是 R4**：「dump = World → DSL 序列化⋯⋯重放逐字相同」。目前對這一類場景不成立。
- **修法待拍板（紅燈，需使用者決定）**：
  1. **dump 補上放法記錄**（建議）：在凍結的 `at u v` 後面附一段來源註記，
     例如 `place 4 on 1 at 1014 1000 +u +n from-edge e2`，parser 讀到就還原
     `anchor_kind`／`ref_edge`，**但不重算幾何**（R6(e) 的凍結不受影響）。
     優點：D7 說錨點本來就含放法記錄，這只是把它真的寫出來；缺點：DSL 多一個尾綴。
  2. **dump 直接輸出原本的錨法**（`at-edge e2` + 明寫長度）：更短，
     但明寫長度配 at-edge 違反 I12 的語法配對，要一併改 I12。
  3. **把延伸段改成純幾何推導**（不看 anchor_kind）：最乾淨，但那是改 D16 的定義，
     影響 I20／I22／R18 一整組，風險最大。
- **驗收**：`_role_ext_stop_primary.scene` 的 dump → loadfile → dump 逐字相同；
  27 個 accept 夾具往返全通過；既有 61 筆測試不受影響。
- **檔案**：`current_geometry.c`（`world_dump_dsl` 的 timber 段、`apply_place_line`、
  `anchor_edge_interval`）。
- **測試**：把往返驗證固定成一個可重跑的關卡（目前是臨時腳本），對全部 accept 夾具執行。
- **相依**：無（與第 10 流平行）。**估時 依修法而定，方案 1 約 3h**。


> **GEO-107 完成紀錄(2026-09-16)**
> **這張票我自己寫錯了。** 票裡把它寫成三選一,其中方案三還說
> 「把延伸段改成純幾何推導最乾淨,但那是改 D16 的定義」。那是誤讀:
> D16 原文寫的是「固定段 = 與它所覆蓋的那條外輪廓 FIXED 邊(`boundaryEdge`)
> 在長度軸上重疊的部分」,而 R18 明寫 `boundaryEdge` 是
> 「純幾何,不看宣告與錨法」,還特別點名「用 `through` 放的料貼齊邊一樣 onBoundary」。
> **所以 D16 從一開始就是幾何定義,是實作讀 `anchor_kind` 違反了條文。**
> 這不是三選一,是把實作改回條文。動手前重讀條文才發現,已跟使用者確認後照新發現做。
>
> 修法:刪掉讀 `anchor_kind` 的 `anchor_edge_interval`,
> 換成 `boundary_edge_interval`——定位邊由 `timber_role_props`
> (R18 的那份推導)決定。`timber_end_face_check` 的 `anchor` 參數因此不再需要,一併移除。
> **不動 DSL,不動公理層。** R4 的往返破口是這個修正的副作用:
> dump 丟掉放法記錄之後幾何完全沒變,所以推導結果也不變。
>
> **行為擴大與它揭露的順序問題**:任何非 boundary 角材只要幾何上壓在外輪廓邊上,
> 現在也會受 I22「不得超出定位邊」約束(先前只有用 at-edge 放的才會)。
> 這正是 I22 條文的字面要求,但它讓 `_mut_notch_straddle.scene` 改以
> `V_EXTENSION` 被拒,而不是原本的「放不上去」——那支料橫跨凹口、
> 恰好與凹口底邊共線。問題出在檢查順序:`timber_place_a0_on_surface`(I5)
> 排在角色檢查之後。對一個連存在都不合法的 footprint 去問「它的定位邊是哪條」
> 沒有意義,而且會讓 M08 變成殺不死(變異前後都回 V_EXTENSION)。
> 解法是在 `boundary_edge_interval` 前面加一道 `boundary_contains_rect` 守門:
> D16 的切分本來就預設這支料放得上去。
>
> **驗證環境**:SAC 這輪是**持續性**封鎖,連換檔名重編也擋,
> 與先前「隨機、重跑就過」不同。所以測試改在 WSL 用 gcc 跑
> (`gcc -O2 -w -o /tmp/cg_wsl current_geometry.c -lm`),
> 這是 `sac-blocks-web-bridge` 記錄的備援路徑,實測可行。
> 之後 SAC 放行,Windows 端也複跑確認一致。
>
> 驗證:87/87 測試(WSL 與 Windows 兩邊都跑過);
> **dump 往返 36/36 全過**——先前唯一失敗的 `_role_ext_stop_primary.scene`
> 現在重放成功,R4 恢復成立;check_panels 40 面板無斷鏈;
> 矩陣仍是綠 26 / 黃 37 / 紅 0。
> 被刪掉的 `anchor_edge_interval` 沒有任何變異錨點或導讀面板引用它(已確認為 0)。

### GEO-108 🔁 已於檔末記錄完成 `tests/mutate.py` 把環境失敗誤判成 killed（驗證完整性漏洞）
- **狀態**：2026-09-16 於 GEO-099 驗證中發現,**既有缺陷**,尚未修。
- **現象**：`mutate.py:209` 的判決只看 `verdict = "killed" if test.returncode != 0`。
  本機 Smart App Control 會**間歇性**封鎖新編譯的 `tests/_mut.exe`（`WinError 4551`）,
  此時 `run_tests.py` 每一筆都失敗、returncode 非 0,於是**全部變異都被判成 killed**。
  實測:同一組 M31/M32/M33/M51/M52 連跑三次,第一次五個全是假死
  （死因寫著「例外 [WinError 4551] 應用程式控制原則已封鎖此檔案」）,
  第二次三個真死兩個假死,第三次才全部取得真實死因。
- **為什麼嚴重**：這是最壞的一種假綠燈——變異測試本身是用來證明「測試抓得到錯」的工具,
  它壞掉的時候看起來卻像全部通過。`mutants_results.json` 也會被寫進假結果。
- **修法**：`mutate.py` 建完 `_mut.exe` 後先做一次冒煙執行（跑任何一個已知 accept 的場景）,
  若啟動本身就失敗（exception / WinError,而不是測試斷言失敗）→ 判 `blocked`,不判 `killed`,
  並讓整批以非 0 退出,逼使用者重跑。另可掃 `run_tests.py` 的輸出:
  死因若是「FAIL 例外」而非「FAIL 錯誤不符／應接受但拒絕／應拒絕但接受／長度不符」,
  一律不算 killed。
- **驗收**：人為封鎖 `_mut.exe`（或改名成不存在）後跑 `mutate.py`,結果必須是 `blocked`／非 0 退出,
  不得出現任何 `killed`。
- **檔案**：`tests/mutate.py`（`main()` 的建置後與判決段,約 190–215 行）。
- **相依**：無。**估時 1h**。

### GEO-109 ✅ 已完成(2026-09-16) I19 補上「只有 boundary 可頂外輪廓邊」那一款
- **狀態**：2026-09-16 於 GEO-100 構造測試場景時發現,**既有不一致**,未動手（超出當次授權範圍）。
- **現象**：場景只有一支 `primary`、兩端直接頂外輪廓的 FIXED 邊 → 實作回
  `V_CUT_PRIORITY：角材 3 端面頂到外輪廓邊（RC）——只有 boundary 可頂 RC`。
- **條文怎麼說**：I19 寫的是「其擁有者的優先級必須**嚴格小於**自己（外輪廓/孔邊/柱面 = 0）」。
  `primary` 的優先級是 2，外輪廓是 0，**0 < 2 成立**，照條文應該放行。
  I19 只列了兩個例外（轉角兩支 boundary 互頂、延伸段見 I22），沒有「只有 boundary 可頂 RC」這一條。
- **哪一邊才對**：看 D15 的物理意義段——「連續的邊界材釘在 RC 上，被夾的主支長度成為模數」，
  以及 R19(c)(d)「層級 2 停在層級 1 下面」——**實作的意圖是對的**，
  是 I19 的條文漏寫了「空間邊界只能被 boundary 頂」這一款。
  依第 9 流總則「條文與實作不一致時**改實作**」的字面會改錯邊，這裡應該改條文。
- **建議修法（需使用者拍板）**：I19 補一款——
  「擋面擁有者是空間邊界（優先級 0）時，只有 `boundary` 可以頂它；
   其餘角色端面頂空間邊界一律拒絕（V_CUT_PRIORITY）。」
  並在 D15 的物理意義段加一句指回 I19，說明這是「邊界材連續、主支被夾」的直接後果。
- **附帶影響**：這條限制使「被錨定的主支必然依賴橫跨全寬的邊界材」，
  這正是 GEO-100 無法為 I23(b) 構造隔離殺手的原因（見 GEO-100 完成紀錄與變異 M56）。
  若日後放寬，I23(b) 的殺手就做得出來。
- **驗收**：條文補款後，`_role_priority_primary_rc.scene` 等既有夾具的拒絕理由能由條文推出；
  新增一筆正向夾具說明「boundary 頂 RC 合法」。
- **檔案**：`公理層.md`（I19、D15）。**估時 1h（純條文，不改實作）**。

> **GEO-109 完成紀錄(2026-09-16)**
> 使用者授權後改的是**條文**,不是實作——實作本來就對。
> **開票時我把限制範圍寫得比實作寬**:原票說「空間邊界(優先級 0)只有 boundary 可頂」,
> 但實作只攔 `STOP_OUTLINE_EDGE`,**孔邊與柱面完全不設限**。
> 這不是漏寫,是刻意的分界——`_test_hole_auto.scene` 的註解早就寫著
> 「主支起點頂在 e0 邊界材側面(主支端面不得頂 RC 外輪廓——I19),
> 終點頂在孔邊(孔邊=柱面,各角色可頂)」,而且與 I20「孔邊不算」、
> I21「孔邊上貼邊排的料角色由宣告決定」是同一個分界。
> 條文因此照實寫成兩句:外輪廓邊只有 boundary 可頂,孔邊與柱面不在此限。
>
> 改動三處:I19 補款、D15 物理意義那句指回 I19、§四 記錄補正。
> 原始碼只改註解不改邏輯:RC 那一款的註解改成指向 I19,
> 並把 `timber_end_face_check` 裡那段已經過期的
> 「公理層 I22 內部不一致、未經授權不得修改」改成指向本流已修正的 I22 條文。
>
> **測試完全不用改**:兩個負向夾具(`_role_priority_primary_rc`、
> `_role_priority_secondary_rc`)與正向的孔邊夾具(`_test_hole_auto`)本來就存在,
> 而且都已經在註解裡標了 I19。這從一開始就純粹是條文的缺口,不是覆蓋的缺口。
> **補了兩個夾具**,因為 fresh-context 複驗指出「boundary 頂外輪廓 → 接受」
> 只有隱含覆蓋、沒有專門命名的正向夾具:
>   `_role_rc_boundary_ok.scene`   — 正向對照組,與 `_role_priority_primary_rc`
>                                    同一片面、同樣兩端落在直立外輪廓邊上,差別只在角色。
>   `_role_rc_custom_reject.scene` — 釘住「這一款看角色不看優先級」:
>                                    custom priority 1 的數值與 boundary 完全相同,
>                                    但它不是 boundary,頂外輪廓邊仍然拒絕。
> 第二個一開始沒隔離到目標(起點先撞上角材側面的數值規則),改成兩端都落在
> 外輪廓邊上才真的把 RC 那一款逼出來。
>
> 驗證:87/87 測試;check_panels 40 面板無斷鏈;矩陣仍是綠 26 / 黃 37 / 紅 0。

### GEO-110 ✅ 已完成(2026-09-16) 公理層覆蓋率矩陣 `axiom_matrix.py`
- **動機**:公理層是驗收基準,但「條文」與「守衛它的東西」之間沒有任何機器查得動的連結,
  只有註解裡的散文。本 session 找到的三個條文/實作不一致(GEO-107、GEO-109、以及 I22 那句)
  都是靠手工逐條比對才撞到的。
- **內容**:`geometry-guide/axiom_matrix.py`。解析 `公理層.md` 的 63 條條文,
  對每一條列出:原始碼哪裡提到它(含所屬函式)、哪些 `*.scene` 夾具提到它、
  哪些變異的 desc 提到它;另外檢查條文宣告的每個 `V_*` 錯誤碼在原始碼裡找得到。
  `--strict` 在有紅燈時以非 0 退出。
- **判準是弱代理,這點寫在腳本開頭也印在輸出裡**:量的是「條號在哪裡被提到」,
  不是「哪裡實作了它」。紅燈代表沒有可追溯的連結,**不代表沒被測到**——
  像 I1 承載面框架合法,每個場景都在跑它,只是沒人寫下條號。
  要消紅燈的正確做法是補註解把連結寫下來,不是去改條文。
- **本次同時補完的標註**:原始碼 22 處、夾具 17 個、變異描述 46 筆。
- **結果**:紅燈 24 → **0**,綠燈 19 → 26,黃燈 20 → 37。
  黃燈全部是「有原始碼、缺夾具」,那是**誠實的狀態**——代表這條有實作但沒有專屬測試,
  不該為了讓數字變綠而硬掛一個不相干的夾具。
- **順帶暴露的事**:D15–D17、I19–I22 這整組角色層條文**變異數為 0**,
  與未完成的 GEO-094(補變異測試)完全對上。矩陣讓這件事不用讀 BACKLOG 就看得見。
- **注意**:別把 `--strict` 掛進 CI 之前先確認紅燈為 0,否則會擋住所有人。
- **檔案**:`geometry-guide/axiom_matrix.py`、`current_geometry.c`(註解)、
  `*.scene`(註解)、`tests/mutate.py`(desc)。

### GEO-108 ✅ 已完成(2026-09-16) 變異工具把環境失敗誤判成 killed
- **原問題**:判決只看 `returncode != 0`。SAC 間歇封鎖新編譯的 `_mut.exe` 時,
  `run_tests` 每一筆都以「FAIL 例外 [WinError 4551]」失敗,於是**全部變異被判成殺死**。
- **修法**:跑完先分辨死因是測試斷言還是執行檔沒跑起來。
  輸出含「FAIL 例外」或「FAIL 逾時」,或 `CreateProcess` 直接丟 `OSError`,
  一律重跑(`RUN_RETRIES = 3`);三次都不行就判 `blocked`,**絕不計入 killed**,
  整批以退出碼 2 結束並印出警告。`main()` 的退出碼現在會傳到 shell。
- **順手修掉同一張票的另一半**:跑子集時把結果**併回**既有紀錄而不是整份覆寫。
  原本 `python tests/mutate.py M31` 會把其餘 47 個判決清掉;本 session 踩了兩次,
  都靠手動備份再合併才補回來。現在同時印「本次」與「全檔」兩組統計。
- **驗證**:把 `_cl.bat` 暫時換成產生「存在但不可執行」的假 exe,跑 M31。
  修之前會回報 KILLED,修之後回報 **BLOCKED + 退出碼 2**,`_cl.bat` 已還原。
  正常路徑無回歸(M31 仍以真實死因 killed,M56 仍 survived)。
- **檔案**:`tests/mutate.py`(備份 `tests/mutate.py.bak-geo108`)。
> **收流關卡實測紀錄(2026-09-16)**
> 完整 48 個變異跑完:**43 殺死 / 5 存活 / 0 無效**。
> 存活的五個:M01、M09、M10、M23 是既有的等效變異(理由見第 427 行起的變異測試段),
> M56 是 I23(b) 的未覆蓋缺口(非等效,理由見 GEO-100 完成紀錄)。
> **2026-09-22 更正(GEO-173)**:現行語意下 M56 是等價變異,見 GEO-100 段落的更正註記。
>
> **GEO-108 的修正在第一次完整跑就證明了價值**:那一輪有 **10 個變異被 SAC 擋住**
> (M02、M09、M11、M17、M18、M20、M24、M28、M40、M55)。
> 修正之前,這 10 個會全部被判成「殺死」,整份結果會顯示 44 殺、毫無異狀——完全是假的。
> 修正之後它們被標成 `blocked` 並讓整批以退出碼 2 結束,逼人重跑;
> 重跑四輪之後全部取得真實死因(M09 落回既知的等效存活)。
> **2026-09-16 晚間補充:封鎖也可能是持續性的。** GEO-107 那輪連續 15 次都被擋,
> 換輸出檔名重編也一樣,與「重跑就過」的情形不同。`mutate.py` 目前只能用
> `_cl.bat`(MSVC),遇到持續封鎖就跑不動。**備援是 WSL + gcc**,實測可行:
> `gcc -O2 -w -o /tmp/mut.c ... && python3 tests/run_tests.py /tmp/mut`,
> M53 就是這樣拿到真實死因的。日後若常撞到,值得讓 mutate.py 支援
> 以環境變數切換建置指令,但那是另一張票。
> **SAC 的封鎖是隨機的,不是固定針對某個二進位**:M11 連續被擋 11 次,第 12 次就過了。
> 所以看到 `blocked` 就是重跑,不要改程式碼去迎合它。


### GEO-111 ✅ 已完成(2026-09-16) 公理層閱讀器 `make_axiom_reader.py`
- **動機**:使用者反映「貼出來或轉述時,部分細節有點模糊」,想要一個公理層的閱讀器。
  先量再做:63 條條文、65 次交叉引用,**平均每條只有 1.0 次、零懸空引用**——
  所以「通用閱讀器」解的是一個不大的問題,不值得做。
  真正難讀的是**樞紐**:R6 被引用 6 次、I19 與 I22 各 5 次、R3 與 I8 各 4 次、
  D9 3 次,這六條吃掉 65 次引用裡的 27 次。讀 R21 時要同時記住
  R6 的 (b)(c)(d)(e) 四款加 I19 加 D18,那才是腦袋裝不下的地方。
- **內容**:`geometry-guide/make_axiom_reader.py` → `geometry-guide/公理層-閱讀器.html`
  (單檔離線,無外部相依)。只解三件事:
  1. **交叉引用就地展開,而且帶子項的引用只給那一款**。
     全檔有 20 個子項、7 種帶子項的引用(`R6(b)(c)(d)(e)`、`I23(b)`、`R19(d)`、`R21(d)`),
     `R6(d)` 的 popover 只顯示 (d),不是整條 R6。實測驗證過。
  2. **反向引用**:這條被誰引用,改它會波及哪裡。
  3. **三向連結**:條文住在哪個函式、哪些夾具釘它、哪些變異殺得死它。
     資料直接 `import axiom_matrix`,不另外維護一份解析邏輯。
  另有樞紐徽章(被引用 ≥3 次)、紅黃綠燈、條號/標題搜尋。
- **紀律**:與 `make_guide.py` 相同——**產生出來的,不是手寫的**。
  公理層是 SSOT,這頁只是觀察者,絕不寫回。會過期的閱讀器比沒有更糟,
  所以 `current_geometry.c` 檔頭的流程註解已補上「條號註解有增減時一併重跑」。
  腳本本身在解析不到 60 條條文、或發現懸空引用時直接非 0 退出。
- **驗證**:不只「產生得出來」——起本機伺服器實際跑過互動:
  hover `R6(d)` 顯示的確實只有 (d) 那一款;I23 的三向連結面板顯示
  原始碼 `apply_grid_line` / `world_revalidate`、四個夾具、變異 M51 M56,
  反向引用列出 I10 與 R13。
- **刻意沒做**:通用的 markdown 閱讀器、條文編輯功能。前者資料顯示沒必要,
  後者會讓這頁變成第二個事實來源,違反「只讀不寫回」。
- **檔案**:`geometry-guide/make_axiom_reader.py`、`geometry-guide/公理層-閱讀器.html`、
  `current_geometry.c`(檔頭流程註解)。

### GEO-112 ✅ 已完成(2026-09-17) 公理層閱讀器 v2:每條條文附真實範例
- **動機**:v1(GEO-111)解了交叉引用展開,但使用者反映「光看條文還是不好懂,要範例」。
- **範例來源刻意選既有 `*.scene` 夾具,不是手寫散文**:夾具是真的跑過的測試,
  有明確的接受/拒絕與長度數字,**永遠不會跟實作漂移**;手寫的「例如⋯」只是轉述,
  會模糊、會過期、沒人驗——那正是使用者先前點名的問題。
- **三件新東西**:
  1. **每條附範例**。接受型直接渲染平面圖(仰視);拒絕型把場景截到違規行之前,
     重建「失敗前」的配置當圖。每個範例含:接受/拒絕徽章、夾具檔頭註解當旁白、
     圖、帶行號且違規行高亮的 DSL、以及 TESTS 裡的預期結果。
     預設只展開第一個(I19 有 13 個範例,全展開會爆版),附「全部展開」。
  2. **白話旁白**:`geometry-guide/公理層-白話.md`,63 條全寫,
     顯示時明標「白話,非條文」。公理層.md 一個字都沒動。
  3. **沒有夾具的 36 條老實標「尚無範例」**,不硬湊(補夾具見 GEO-113)。
- **實作要點**:
  - 裁切走**純 Python 後處理,不改 C**:抓第三個頂層 `<g>`(仰視)的
    translate + frame rect 算出 viewBox。**只換 viewBox、不刪內容**,
    所以「三視圖」按鈕只是把屬性換回 `data-full`。版面一變 assert 就炸,不會默默算錯。
    不改 C 是因為會牽動 check_panels 的 callout 與導讀重產,收益為零。
  - **拒絕型的截斷啟發式**(`axiom_examples.before_failure`):從 stderr 抓行號 N,
    取前 N-1 行重跑。砍掉 place 後 timber 會變孤兒(I9 的 EOF 檢查,**訊息沒有行號**),
    所以有一個移除孤兒宣告的迴圈,而且**頁面上必須明寫移除了哪幾支**。
    「有圖」要過三道:rc=0、三個視圖且第三個是仰視、仰視圖裡至少一片承載面。
    第三道專殺一種假綠燈——場景被截到只剩註解時 parse 仍會成功,
    `scene_compute_layout` 走空版面分支,會產出一張什麼都沒有的白框。
  - **不允許靜默略過**:exe 找不到或被 SAC 擋 → 整份失敗、退出碼 2、
    訊息教人用 WSL + gcc;要無圖版得明寫 `--no-render`,而且頁首會有紅字橫幅。
- **結果**:54 個夾具裡 53 個有圖。唯一沒有的是 `_mut_col_noz`(違規在第 2 行,
  截斷後場景是空的),正確標成「失敗前狀態無法單獨渲染」並附截斷版自己的錯誤。
  頁面 589 KB,單檔離線。
- **已知的取捨**:同一個夾具被多條條文引用時 SVG 會重複內嵌(54 個夾具 → 79 次)。
  沒有用 `<use>` 去重,因為 shadow tree 對 class 樣式的支援有雷,
  圖渲染不出樣式比多 300 KB 糟。頁首統計因此寫「圖 53/54 **個夾具**」而不是張數。
- **過程中修掉的兩個自己的 bug**(都是驗證抓到的,不是看起來對就算):
  1. `crop_bottom` 原本把整個 `<svg …>` 一起帶進去,變成巢狀 SVG,
     內層 viewBox 把裁切整個蓋掉——圖看起來仍是三視圖。
  2. DSL 用換行串接 `<span>`,但 `<pre>` 會把那些換行也算一行,變成雙倍行距。
- **驗證**:11 項靜態檢查全過(含「統計自洽」「樣式無汙染」「v1 未退化」);
  缺一條白話 → exit 0 且該條顯示「(尚無白話)」、統計誠實變 62/63;
  假 GEO_EXE → exit 2;`--no-render` → exit 0 且有紅字橫幅。
  **互動用本機伺服器實跑**:viewBox 在 `0 1540 4100 3640` 與 `0 0 7900 5180` 之間切換、
  按鈕文字跟著變、「全部展開」把 3 個範例都打開、SVG 實際渲染成 472×419 px。
  (截圖因為視窗在背景一直空白,改用 DOM 量測——那比截圖更硬。)
  `check_panels.py` 與 `axiom_matrix.py` 輸出不變。
- **檔案**:`geometry-guide/axiom_examples.py`(新)、`geometry-guide/公理層-白話.md`(新)、
  `geometry-guide/make_axiom_reader.py`、`geometry-guide/公理層-閱讀器.html`(重產)。

### GEO-113 ✅ 已完成(2026-09-17) 63 條全部補上範例
- **起因**:使用者打開 GEO-112 做的閱讀器實際看過,要求把那 36 條的「尚無範例」補完。
- **逐條量過之後發現不是補註解就好**。87 個夾具裡各指令的使用次數:
  `apply-proj` **0**、`canvas-pos` **0**、`reset` **0**、`delete` 1、`move` 1。
  也就是 R8–R17 那一整族、D12、I14、R20 **是真的沒有測到**,
  不是「有覆蓋只是沒寫條號」。這正是這張票原本要求逐條判斷的理由。
- **分三組處理**:
  1. **15 個既有夾具補檔頭註解**(D2 D3 D4 D5 D6 D7 D8 D9 D13 I1 I2 I3 I11 R18;
     R11 的標記加在新寫的 `_ax_r17_wall_column_face.scene` 上,它本來就會拆片)。
     零行為改動,加完測試輸出與基準**逐字相同**。
     每一行註解都是一個主張,逐檔讀過才寫,標準是
     「這個夾具如果壞了,是不是代表這條被違反了」。
     其中 D4 / D5 / D13 / I3 各補兩個互補的夾具(引用邊界面 vs 自帶 rect、
     六面封閉 vs 兩面不封閉、推得出 vs 推不出、fixity 明寫 vs 省略)。
  2. **28 個新夾具 `_ax_*.scene`**,一條一個最小場景,涵蓋 20 條條文。
     檔頭三行內講清楚條號、在示範什麼、預期什麼;DSL 只留逼出該條所需的最少行數。
  3. **3 條走 web bridge 實錄**(R1 拾取、R4 dump 往返、R5 拖曳 clamp)。
     這三條的行為根本不在場景 DSL 裡——`SCENE_COMMANDS` 沒有 pick / dump / drag,
     所以無論怎麼寫 `.scene` 都逼不出來。改成真的把 bridge 跑起來、
     把送出去的指令與收回來的原文貼進頁面(`geometry-guide/axiom_transcripts.py`)。
     R1 用三次 pick 對照:兩條參考線各自單獨經過的點回傳參考線,
     三者重疊的交點回傳最後畫的角材。R4 真的做完整往返,兩份 dump 各 1036 字元逐字相同。
     R5 三次拖曳分別得到 3000 / 0 / 1234——越界的夾回端點,區間內的原樣通過。
- **`apply-proj` 那一族先探路才動手**。它從來沒有任何夾具走過場景檔這條路,
  所以第一步只寫 R9 的拒絕案例確認走得通,過了才續寫其餘八條。結果全部可用,
  九條的錯誤訊息都與條文對得上(例如 R14 回「投影項橫跨拆分線,無法歸屬單一面片」)。
- **測試器加了 `not_contains` 欄位**。有些夾具主張的是「什麼都沒發生」——
  R12 的樑是條帶項、沒帶 `cut-strip` 就不動幾何——那種主張只能用「不該出現」來驗,
  光靠 accept 驗不到。加這個欄位是為了讓夾具真的在驗它宣稱的事。
- **結果**:閱讀器 **63/63 有範例、尚無範例 0 條**;圖 86/90 個夾具;實錄 3/3;頁面 977 KB。
  測試從 87 筆增為 **115 筆全過**。矩陣從綠 26 黃 37 升到 **綠 59 黃 4**。
- **4 個夾具沒有圖,都是誠實的情況**:違規就在第一條內容行(截斷後場景是空的),
  或錯誤訊息沒有行號(I9 的收尾檢查)。另外特地確認**沒有任何一條條文的範例全部缺圖**——
  I1、I2、R11 原本只有拒絕型範例,各補了一個有圖的正面對照。
- **降級路徑實測過**:bridge 找不到 → 頁面照樣產生、三條標紅、頁首橫幅、退出碼 1;
  明寫 `--no-bridge` → 退出碼 0。兩者的頁首統計都誠實寫成「實錄 0/3」。
- **剩下的 4 條黃燈,兩種原因,都不是漏做**:
  - R1 / R4 / R5:矩陣的「夾具」指的是 `.scene`,而這三條按定義不可能有 `.scene`。
    它們在閱讀器上有實錄,只是矩陣量不到。要讓矩陣認得實錄是另一回事,這裡不動它的定義。
  - R19:它**有**夾具,黃的原因是原始碼裡沒有任何註解寫下 R19。
    補一行註解就會變綠,但那要改 `current_geometry.c`,
    而那個檔當時有別人未提交的 grid-ref 工作,所以沒碰。
- **順手發現、只報告沒動手**:`_mut_col_noz.scene` 的檔頭寫「R11 推不出就拒絕」,
  但現行 R11 講的是「拆片面與生成面一律游離」,那句描述其實對應 D13 的末句。
  看起來是條文重編號後遺留的舊引用。已另外把 D13 標上去,原本那行沒改。
- **檔案**:16 個既有 `.scene`(只加註解)、28 個新 `_ax_*.scene`、
  `tests/run_tests.py`、`geometry-guide/axiom_transcripts.py`(新)、
  `geometry-guide/axiom_examples.py`、`geometry-guide/make_axiom_reader.py`、
  `geometry-guide/公理層-閱讀器.html`。

---

## 第 9 流：公理層閱讀器 第 3 版改版(GEO-114 ～ GEO-121)

> 起因:2026-09-17 使用者請外部 agent(ChatGPT / Product Design)做了一版閱讀器重新設計,
> 落在 `geometry-guide/axiom-reader-design/`(React + Vite 原型),
> 並附一份帶 15 項問題的設計審查 `geometry-guide/axiom-reader-design/設計定稿-第3版.html`。
>
> **使用者已拍板(🔒,2026-09-17)**:
> 1. **只搬設計、不搬技術棧**——產物維持「SSOT → `make_axiom_reader.py` → 單一自足 HTML」,
>    不引入 npm / React / 第二份資料。原型的 `src/content.json`(308KB、63 條 + 141 範例)
>    是第二份 SSOT,**不得**成為正式管線的一環。
> 2. 原型目錄進 git,排除 `node_modules/`、`dist/`(由 `axiom-reader-design/.gitignore` 管)。
> 3. 設計定稿快照(11.8MB 自足 HTML)進 repo 當視覺基準。
> 4. 閱讀模式與互動模型四問見 GEO-120:**維持單頁**、**hover 與參照欄並存**、
>    **雙主題深色預設**、**字型維持系統字體疊**。
>
> **施工圖是那份審查的「修正提案」,不是原型本身。**
> 審查第 1 項判定原型的示範畫面「是一張畫,不是版面系統」
> (`activeId === 'R21'` 寫死決定要不要出現條文重點與關聯範例),
> 第 2 項判定它「把唯一權威的原文折在按鈕後面」。後者現行閱讀器本來就做對了,
> 改版**不得**回歸成原型那樣。
>
> **這 15 項已經過對抗驗證(2026-09-17,fresh context,逐條回原型原始碼核對)**:
> 9 項完全屬實、6 項部分屬實,沒有一項整體不成立,可信度中高。但抓到 4 處具體錯誤,
> 照抄會把錯誤的驗收標準一起寫進生成器,已在對應工單就地訂正:
> (i) 修正 14 的「1000px → 主文 330px」算錯 breakpoint 邊界(實際約 455px);
> (ii) 修正 3 說兩個非條文標註「同字級同樣式」不準——附註是 11px vs 標題 17px;
> (iii) 修正 10 說五個區塊標題同級不成立——`.featured-example h2` 是 16px;
> (iv) 修正 8 說釘選「只寫在 title 屬性裡」不屬實——畫面有可見文字與圖示。
> 驗證另外補到兩個審查漏掉的缺陷,列為改版時的禁則:
> `aria-controls` 不得指向尚未掛載的 DOM id(原型 `src/App.jsx:168`);
> 參照面板的「已固定」狀態不得與「目前沒有參照內容」不同步(原型 `src/App.jsx:52,54`)。

### GEO-114 ✅ 已完成(2026-09-17) 安置第 3 版設計資產
- **內容**:把外部 agent 的產物收進 repo 並鎖定收法。設計定稿快照複製為
  `geometry-guide/axiom-reader-design/設計定稿-第3版.html`;原型目錄 35 個檔納入 git(共 20.8MB:
  快照 11.8MB、`qa/` 截圖證據 9.1MB、原始碼與 `content.json` 約 0.4MB)。
- **`public/assets/diagrams/*.svg` 刻意不入 git**:root `.gitignore` 全域忽略 `*.svg`,
  而那 127 個檔是 `scripts/sync-content.py` 從現行閱讀器再生的衍生物,不是來源。
- **驗收**:`git ls-files geometry-guide/axiom-reader-design/` 列得到 35 個檔;
  快照用本機 http server 開得起來、三欄與標註都正常算繪。
- **相依**:無。

### GEO-115 ✅ 已完成(2026-09-18) 閱讀器第 3 版設計規格定稿
- **產出**:`geometry-guide/閱讀器-設計規格.md`,§0–§8 共 9 節。是施工圖不是設計稿:
  原型的**程式不採用**,只採用視覺語言;審查的**修正提案**才是版面依據。
- **與原型分歧最大處**:拍板 2 維持單頁長捲,原型是一次一條。凡原型中為「單條聚焦」
  而生的機制(hash 路由、pushState、單條進場動畫、Toast)一律不移植,列入放棄清單。
- **本次規格新做的判斷**(不是抄原型):
  - **條文標題 40px → 28px**。原型 40px 是為「一次一條」設計的;63 條堆疊時會讓
    長捲軸變成一串巨標。
  - **斷點表重新推算**,標出「導覽 224 + 參照 36% 會把主文壓到 600px 以下」的例外區間。
    初稿把上界寫成 1300px,**經 fresh-context 驗證員重算後訂正為 1287.5px**
    (主文 = `0.64w − 224`,令 ≥600 得 `w ≥ 1287.5`;1201px 時主文僅 544.6px,
    1300px 其實已有 608px)。驗收要實測 1201px 與 1288px 兩個邊界。
  - **兩條會直接推翻拍板 2 的禁則**:條文原文不得放進預設收合的 `<details>`;
    搜尋不得對 `<article>` 套 `display:none`。收合/隱藏的內容多數瀏覽器 Ctrl+F 搜不到。
    已查證現行 `make_axiom_reader.py:700-705` 只隱藏 `nav a`、從不碰 `<article>`,
    所以這兩條是**保住現有行為**,不是新增限制。
  - **燈號與選取態的邊框衝突**:導覽項目左邊框已被可追溯性燈號佔用,選取態改用
    `box-shadow:inset` 疊在內側。
  - **`--accent` 與 `--geo-*` 色相差 ≥60°** 當成可檢查的閘門,取代「互動色與語意色分家」
    這種沒有裁判的說法。
- **四處審查錯誤已套用訂正值**並在規格 §7 留下對照表,避免日後有人回頭照抄審查原文。
- **驗證**:派 fresh-context verifier 逐條核對 14 項(5 處引用、7 組色票、3 個字級、
  3 處算術、內部一致性)。**12 通過、1 不通過**(上述 1300 → 1287.5 的算術錯誤,已訂正)、
  1 項措辭提醒(「8 節」實為 9 節,已改)。
- **驗收**:§8 列了 7 條逐項可檢查的閘門(grep 不到硬編碼條號分支、63 條區塊組成一致、
  grep 不到硬編碼色碼、色相差、原文不在收合區、六個寬度各截淺深兩張、建置期自檢退出碼 0)。
- **檔案**:新增 `geometry-guide/閱讀器-設計規格.md`。

### GEO-116 ❌ 已作廢(2026-09-20) 閱讀欄改版(審查修正 1 · 2 · 3 · 4 · 10 · 12)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-147(原文/白話順序)、GEO-140(計數單一來源)。原文保留供追溯。
- **內容**:改 `make_axiom_reader.py` 的 HTML/CSS 模板。要點:
  - **原文優先**(修正 2):原文預設展開且置於摘要之上,改寫可收合。現行已如此,**不得回歸**。
  - **一套版面吃 63 條**(修正 1):重點列表由資料驅動,不得有任何條號寫死的分支。
  - **三種文本命名一次定案**(修正 3):原文／重點／白話各給固定位置與固定標籤,
    禁止同一件事出現「完整原文」與「條文原文」兩種叫法。
  - **章節標題降級為標籤**(修正 10):改 12px 大寫標籤、弱對比寬字距,把重量讓給內容;
    不得出現同一屬性在同檔宣告兩次的補丁區。
  - **控制項回到可讀尺寸**(修正 4):白話展開鈕改段落下方一般文字鈕,14px、44px 觸擊區。
  - **原文行號常駐**(修正 12):`公理層.md:NNN` 併進標題下的 meta 行,任何寬度都不隱藏。
- **驗收**:重生後 63 條逐條檢查,**沒有任何一條掉回不同版面**;
  原文在所有條文都預設可見;行號在 1280px 與 390px 都看得到;
  腳本內建自檢(條文 ≥60、白話條號合法)照常通過。
- **檔案**:`geometry-guide/make_axiom_reader.py`、重生 `geometry-guide/公理層-閱讀器.html`。
- **相依**:GEO-115。**估時 2h**。

### GEO-117 ❌ 已作廢(2026-09-20) 參照欄(審查修正 7 · 8 · 9 · 11)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-146(參照欄與批註並存)、GEO-141(互動色與圖面色分家)。原文保留供追溯。
- **內容**:右側可固定的引用面板。要點:
  - 參照條號降為 15px chip(修正 7):現行原型的 `R6(d)` 是 49px,比主標題 40px 還大。
  - **實心按鈕給「查看全文」、返回退成次要**(修正 8):56px 實心藍主按鈕做的是返回/關閉,
    真正往前的入口卻是次要文字鈕;返回還有頁首與面板兩個重疊入口,擇一。
    (審查原文說「釘選行為只寫在 title 屬性裡」,對抗驗證判定**不屬實**——
    原型 `src/App.jsx:176` 有可見的「已固定/未固定」文字與圖示切換。釘選本身不必重做,
    但要確保狀態在畫面上說得清楚。)
  - 錯誤分類(如 `E_UNSUPPORTED_END`)不得縮成 11px 灰字(修正 9)——它是可查關鍵字。
  - 互動色與圖例色分家(修正 11)。
- **驗收**:從參照跳到全文再返回,原展開狀態與 scrollTop 還原;
  參照欄關閉後閱讀欄展開;鍵盤可全程操作。
- **相依**:GEO-116。**估時 2h**。

### GEO-118 ❌ 已作廢(2026-09-20) 導覽欄(審查修正 5 · 6)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-139(追溯燈號回歸)、GEO-149(證據強度可見)。原文保留供追溯。
- **內容**:**全列 63 條**、群組可收合;群組條數(19 / 23 / 21)常駐,不得只在 hover 出現。
  若要做重點,只能用資料裡真實存在的標記當篩選器,**禁止手寫白名單**
  (原型寫死 `['R6','R18','R19','R20','R21']`)。
- **驗收**:第一眼看得到 63 條的結構;觸控裝置看得到條數;無任何硬編碼條號清單。
- **相依**:GEO-116。**估時 1h**。

### GEO-119 ❌ 已作廢(2026-09-20) 響應式與手機(審查修正 13 · 14 · 15)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-148(斷點與手機底部列)。原文保留供追溯。
- **內容**:
  - **650–999px 補上真正的版面**(修正 14,P1):原型的漢堡鈕只在 ≤650px 出現
    (`src/reader.css:6,26,28`),所以 650–999px 側欄硬佔 190px 且收不起來;
    同區間參照面板是 `min(480px, 100vw − 210px)` 覆蓋層(`reader.css:25`)。
    **審查原文「1000px 時主文被夾到約 330px」經對抗驗證判定算錯**:1000px 不觸發 999px 查詢,
    而是落進 1280px 那段(`reader.css:24`,`--nav:195px`、`--reference:35%` 內聯欄非覆蓋層),
    主文實際約 455px。結構性問題(190px 段收不起來、999px 內是覆蓋層)成立,但驗收
    **不得**照抄 330px 這個數字。
    改成 ≤1200px 起導覽即抽屜、主文維持 ≥600px;參照在 ≤999px 改半高 sheet。
  - 手機頂欄從 112px(佔 390×844 的 13%)收成 56px 單列,下接可橫捲的條號 chips(修正 13)。
  - 工程圖在窄螢幕可點開全螢幕縮放,或改用裁切局部圖(修正 15)。
- **驗收**:390 / 700 / 1000 / 1280 / 1487px 五個寬度各自截圖;
  每個寬度都無水平溢位、主文可讀、主要控制未被裁切。
- **相依**:GEO-116、GEO-117、GEO-118。**估時 2h**。

### GEO-120 ✅ 已拍板(2026-09-17) 閱讀模式與互動模型三問
- **問題一:單頁長捲軸 vs 一次一條**。現行閱讀器是單頁攤平 63 條(`scrollHeight` 58,512px),
  Ctrl+F 搜得到任何一句條文;第 3 版設計是一次一條 + 參照欄,改過去等於放棄瀏覽器全文搜尋。
  這份文件的用途正是拿來核對引擎行為,全文搜尋是實質功能。設計審查沒評估這一項——
  它的對象是原型,而原型一開始就是一次一條。
  **拍板:維持單頁**。63 條繼續攤平在同一頁,只把外觀換成深色三欄(左導覽固定、
  右側加可固定參照欄),Ctrl+F 保住,現行功能全部不動。第 3 版的視覺主要收穫
  (三欄、深色、參照欄、手機抽屜)在單頁模式下都成立。
- **問題二:參照別條公理的互動**。現行是 hover 彈出預覽,第 3 版是點擊開固定側欄。
  **拍板:兩者並存**。hover 快速預覽留著當掃視用,點擊開右側可固定面板當深入用。
  砍掉 hover 是淨損失,且觸控裝置本來就沒有 hover,兩者不衝突。
- **問題三:主題**。第 3 版只有深色,現行有 `prefers-color-scheme` 雙主題。
  **拍板:維持雙主題,深色為預設**。第 3 版色票當深色那套,另調一套淺色。
- **問題四:中文字型**。第 3 版用 `@fontsource-variable/noto-sans-tc` 內嵌可變字重,
  現行是系統字體疊(`make_axiom_reader.py:520` 附近)。實測(非估算,fontTools 4.63.0):
  閱讀器可見文字共 **819 個不重複 codepoint**(CJK 704);完整字型 105 個 woff2 切片
  合計 4,194,768 bytes。以現行 978,983 bytes 為基準,base64 內嵌後——
  完整內嵌 **+587%**(6.73MB);子集化三字重(450/550/650)**+50%**(1.47MB);
  子集化單一字重 +16.5%(1.14MB,但等於放棄整個字重層級,比系統字體的 400/700 還糟)。
  另有 8 個字元(`⊆⊇⊉⌈⌉⌊⌋🔒`)Noto Sans TC 根本沒有字形,三案都得靠系統後備。
  **拍板:維持系統字體疊**。+0 bytes、管線不變、零新故障模式;代價是 450/550/650
  會被四捨五入。字重不是此次改版的主要收穫(版面、色票、層級、參照欄才是),
  日後要補子集化可以當純加項,但那時必須同步加一道「字元漏網就非 0 退出」的建置期閘門,
  否則公理層.md 新增字元時子集會靜默過期。

- **連帶約束(寫進 GEO-116～119 的驗收)**:現行閱讀器獨有的追溯類功能一律
  **不得丟失**——紅/黃/綠可追溯性燈號、三向連結(原始碼/夾具/變異)、樞紐徽章、
  web bridge 實錄專屬區塊、「全部展開/收合」、即時隱藏式搜尋,
  以及生成腳本的建置期強制檢查與非 0 退出(懸空引用、條文數 ≥60、白話條號合法)。
  第 3 版原型這些全都沒有,搬設計時最容易連同丟掉。

### GEO-121 ❌ 已作廢(2026-09-20) 修掉 SVG 樣式段不隨深色模式變的既有缺陷
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-141(色彩 token 化,範圍已擴大到 281 張例圖與見證圖)。原文保留供追溯。
- **起因**:改版盤點時發現,`make_axiom_reader.py:620-636` 的 SVG 專用樣式段**硬編碼色碼**,
  不在 `@media(prefers-color-scheme:dark)`(`:515-517`)的涵蓋範圍內。現行深色模式下
  工程圖的配色是錯的。這也正是設計審查第 11 項「互動色與資料語意色混用」的根源。
- **內容**:把 SVG 色碼收進 `:root` token(`:513-514` 已有 token 機制,只是這段沒用),
  並**把互動色與資料語意色分家**——`#88cafa` 目前同時是品牌/連結/條號/釘選狀態
  與工程圖的「邊界」;琥珀 `#efb765` 同時是強調色與「角材」。讀者無法從顏色判斷
  這是可點的還是一種構件。
- **驗收**:淺色與深色兩個模式各截一張含工程圖的畫面,圖例色與線段色一致且可辨識;
  全檔 grep 不到散落在 SVG 段的硬編碼色碼;互動色不再出現在任何圖例。
- **相依**:GEO-115(色票 token 表要先定案)。**估時 1h**。

---

## 第 9 流盤點結論(2026-09-17,四條併行調查線的產出)

1. **這是換皮,不是換血**。`make_axiom_reader.py` 共 714 行;資料層
   (`axiom_matrix.parse_clauses` `:47-69`)只回純 tuple/dict,HTML 在 `main()` 迴圈裡
   直接字串拼接,**沒有中間視圖層**。換三欄版面預估:CSS(`<style>` `:512-645`)
   新增 70–100 行 + 調整 20 行;HTML 骨架(`TEMPLATE` `:508-707`)< 30 行;
   JS(`<script>` `:651-706`)新增 60–100 行;**資料層完全不用動**。
2. **綁死的格式要同步改**:`ref_re` 正則(`:112`、`:319-332`)與卡片 id `c-%s`(`:447`)、
   nav href(`:462`)、JS 錨點(`:696`)、`DATA` key(`:401`、`:656`)四處格式互相咬合,
   動連結呈現要一起查。`build_examples` / `build_transcript` 分別綁死
   `axiom_examples.py` / `axiom_transcripts.py` 的回傳欄位名。
3. **體積基線**:現行單檔 978,983 bytes 裡,132 個內嵌 `<svg>` 佔 **615,022(62.8%)**,
   CSS 僅 7,827,JS 35,263,純文字/標記 320,871。換版面動到的是那 7,827 + 35,263,
   佔全檔 4.4%——體積不會因為改設計而顯著變動。
4. **原型漏掉實錄專區是意外,不是取捨**:`axiom-reader-design/scripts/sync-content.py:64-70`
   用同一條正則抓 `ex-wrap`,而 `build_transcript()`(`:219`)把 R1/R4/R5 實錄也包在
   `ex-wrap` 外殼裡,於是實錄被併進泛用 `examples` 陣列、結構化標籤丟失。

### GEO-122 ✅ 已處理(2026-09-18) D10a 奇數 gap 修正;等分軸定義提出但未採納
- **起因**:使用者在批註版閱讀器上對 D1 提問——「座標都是毫米,遇到均分怎麼辦?
  你要拒絕嗎?這樣這種工具還能用嗎」。
- **查證結果**:公理層並沒有「均分除不盡就拒絕」這條通則。
  `D10a:66` 明寫「不因『除不盡』而拒絕」;`R3:208` 的「除不盡 → 拒絕」限定在
  `unproject det=0` 的數值退化。**真正會擋人的只有一條**:D10a 的
  「gap 為奇數 → 中心線不是整數 → 拒絕」——而 3mm / 5mm 是實務上最常見的板縫寬。
- **判定是缺陷不是紀律的依據**:`I13:152` 對奇數角材寬用的是
  「多的 1mm 恆在 +cross 側」這種**定義好的取整**,沒有拒絕。同一份文件對同一類問題
  給了相反待遇,是自相矛盾。R3 的「拒絕不猜」管的是答案不確定(det=0、多解),
  不管「答案已知但不落在整數格上」。
- **已採納(使用者明示授權)**:D10a 的 `c_k` 改成 `a + k·T + panel + ⌊gap/2⌋`,
  gap 奇數時中心線偏向低座標側 0.5mm;刪除該拒絕條款並寫明理由。
- **提出但未採納**:另立一條「等分排法(DIVIDE)」軸定義,用整數分配
  (`q=⌊L/n⌋`、`r=L mod n`,前 r 份長 q+1;1000 分 3 = 334/333/333)使等分永不除不盡。
  **一度寫進公理層(D10c)後由使用者要求撤除**——授權當時問的是「修掉 gap 缺陷」,
  新增編號條文超出授權範圍。已完整回復:D10 的「四選一」、D10c 整條、I10 的
  DIVIDE 字句全部撤掉,閱讀器重出回到 63 條。
  **教訓**:改 🔒 公理層時,「修正既有條文」與「新增條文」是兩種授權,必須分開問。
- **相關但未處理**:`BACKLOG.md:684`(第 2/3 期的子網格 subgrid)已規劃了等分機制,
  且寫著「cell 寬不能整除 → 拒絕」——與本次的判斷同屬一類問題,條文未定案前先不動。
- **尚未跟上**:`current_geometry.c` 還會拒絕奇數 gap;
  `_edge_grid_panel_odd_gap.scene` 與 `tests/run_tests.py:99` 仍斷言 `expect: reject`。
  條文已改、實作未改,這三處現在與公理層矛盾。

### GEO-123 ✅ 已入層(2026-09-18) 禁止來歷不明的數字:參考線與角材放置只能引用
- **起因**:使用者在批註版閱讀器上逐條批註 D1 / D3 / D4 / D10 / I5,共同訴求是
  **「幾何要能依環境推導,不要逼使用者硬寫數字」**。I5 那則(`kind=missing`)寫得最直接:
  「角材放置前要決定角材長度,角材長度只能『引用』」。
- **兩批入層,先參考線後角材**:
  1. **參考線位置只能引用**(D6、D6a、D6b、I7、R5)。`D6` 的 offset 不再存自由數值,
     只存引用式;`D6a` 定義引用式 `offset = Σ cᵢ·qᵢ`,五類可引用量、求值後取下界;
     `D6b` 具名規格常數 `spec <名稱> <整數>` 是**全公理層唯一允許字面數字的地方**。
     **係數是比例不是尺寸**——cᵢ 無單位,帶 mm 的量一律不得寫字面數字。
     `R5` 拖曳改成吸附到最近的合法引用,寫入引用式而非座標。
  2. **角材放置只能引用**(D7、D11、I8a、I12、I13、I23、R2、R4、R6(e))。
     **長度不宣告**——廢除 `timber id L A B`,一律由 R6 推導、撞到佔用邊界即止。
     **位置只能引用**——`at-line`(中線對齊參考線或格線)、`at-face`(側向貼齊佔用邊界,
     含已放角材側面);廢除 `at` 自由 uv 與 `at-guides`。
- **使用者給出的關鍵洞見**:擋面的物理意義就是「已被佔用的空間不能再被佔用」。
  因此「邊」與「擋面」本來是同一件事——都是佔用邊界,差別只在相對長度軸的朝向:
  **垂直**者頂端面決定長度,**平行**者供側向貼齊決定位置。已寫進 `D11`。
  原本 `at-edge` 只吃輪廓邊與孔邊、漏掉已放角材側面,就是這個統一沒做完的後果。
- **三條 🔒 被反轉**:`R6(e)` 與 `R2` 原本明寫「凍結 / 不重放」,`D7` 的長度模式二選一
  也是 🔒。使用者拍板改成**跟著動**:被引用者移動即重新推導,沿依賴鏈取遞移閉包。
  `I23` 的引用鎖隨之解除(移動不再直接拒絕),`R4` 的 `grid-ref` / `span-auto` 整套作廢。
- **配套新增 `I8a` 影響預覽**:使用者在「整筆回滾 / 部分提交標紅 / 先預覽再套用」
  三者中選了預覽。移動已被引用的線或邊必須先在候選世界算出影響並逐項列出
  (受影響角材的遞移閉包、新舊中線與長度、每項違規的條號與預期/實際);
  零違規且使用者確認才套用,**有違規則不得套用**——World 永遠不進入非法狀態。
- **提出但撤除**:一度新增 `D10c 等分排法(DIVIDE)`,使用者要求撤除(見 GEO-122)。
  該次的教訓「修正既有條文與新增條文是兩種授權」,本批已照做——D6a/D6b 與 I8a
  都是單獨明確請求授權後才寫。
- **編號**:用 `D6a`/`D6b`/`I8a` 而非新數字,因為 `§四` 已把 `D19`/`R22`/`R23`
  預留給第 2、3 期的相位/交丁與子網格。
- **閱讀器同步**:63 → 66 條。原文直接從 `公理層.md` 抽,不手抄;
  8 條的白話原本描述舊規則(「兩種寫法…凍結」「明寫長度只能用 at」「不會跟著走」
  「凍結不重算」「引用鎖」),全部改寫,否則閱讀器會自相矛盾。
- **實作尚未跟上,且已知衝突**:`current_geometry.c` 一行未動;
  `_ax_i12_auto_with_at`、`_ax_i12_explicit_with_atgrid`、`_edge_grid_locked*`(3)、
  `_edge_freeze`、`_edge_grid_panel_odd_gap`、`_ax_r13_anchor_*` 等 20+ 個夾具
  仍斷言舊行為;`tests/run_tests.py:99,242,244` 直接測已作廢的規則。
  **現在跑測試必紅,原因是條文比實作新,不是程式壞了。**
  上一個 commit(c8a387a)的 grid-ref / span-auto 實作也被本批作廢。

### GEO-124 ✅ 已修(2026-09-18) 清掉 GEO-123 留下的新舊條文矛盾
- **起因**:使用者請另一個 agent 檢查閱讀器,指出「同一條文裡出現互相相反的要求」。
  逐條驗證後**屬實,且是 GEO-123 造成的**——改條文時只更新了 `body`,
  沒有同步 `clauses[].subs`(子款)與跨條文的交叉引用。
- **SSOT 修掉 7 處**:
  `D10a` 起算點「凍結,比照 R6(e)」→ R6(e) 已反轉,改標為本條自有的凍結;
  `D18`「與 at-edge 同一套寫法」→ at-face,並說明 at-face 取平行側面;
  `I10`「受 I23 的引用鎖限制」→ 引用鎖已解除,改走 I8a;
  `R6(c)`、`R18` 的 at-edge → at-face;
  `R21(f)`「兩端與長度在 place 當下凍結」→ **不凍結**,存擋面參照、移動即重推;
  `D15` 語法 `timber id [L] A B ...` → **移除 `[L]`**(D7 已廢除明寫長度)。
- **閱讀器修掉 4 處**:
  `clauses[].subs` 從 `公理層.md` 重新產生——原本 `I23(a)`、`I23(c)`、`R6(e)`、`R21(f)`
  四個子款仍是舊文,讀整條與只讀子款會得到相反指令(這正是對方指出的最嚴重項);
  `R18` 白話仍寫 at-edge;
  第 5 則批註(I5)只存在 JSON、沒有靜態 `inline-note`,只讀靜態正文的流程會漏掉它;
  可見文字仍寫「4 則批註」。
- **subs 解析器有驗證**:先用本次未改動的 `R19` 做 round-trip,重新解析的結果必須與
  檔案內既有的 subs **逐字相同**才繼續;通過後才套用到其餘條文。
- **對方另外兩點的處置**:
  - 「長度只能引用可能被縮窄成長度只能自動跨距」——**不是誤改**。使用者在 I5 批註之後
    明確口述了規則:「不用決定長度,他會依賴承載面上的幾何資訊來決定長度,
    只有在遇到擋面的時候會停止」,並在我提到長度的線性組合時糾正
    「這是參考線引用的常數的線性組合,跟角材有什麼關係」。後者取代前者。
    對方只讀檔案、讀不到這段對話,所以判斷合理但結論不成立。
  - 「D3/D4 的樑高度與材料厚度干涉未入層」——**屬實但是刻意的**:
    `§四:336-337` 明文把「完成面、面材厚度、完成面高程」與「樑投影的輪廓裁切」
    列為未來的層。使用者的 D3/D4 批註正是指向這塊留白,尚未拍板。
- **仍未處理**:實作與夾具(見 GEO-123 末段),以及 `_edge_grid_panel_odd_gap` 等 20+ 個
  仍斷言舊規則的 `.scene`。

### GEO-125 ✅ 已修（2026-09-18）實作跟隨 GEO-123 / GEO-124 新公理
- 公理層與正典閱讀器未由本次工作改動；遇到新舊規則衝突一律遵循新版。
- 加入具名規格、有理位置引用、at-line / at-face、引用依賴重算與 I8a 影響預覽；
  明寫長度、自由 uv、凍結 dump、grid-ref/span-auto、網格引用鎖等舊入口均拒絕。
- 保存引用與放置順序，確認前 World 不變；取消、無效／過期預覽、群組錯誤全部回滾。
  補正奇數板縫、共線擋面重複、自帶矩形角色驗證、單擊歷史、面內參考線扣孔裁切。
- 示例與測試一起遷移。121 場景、80 C 完整性、25 引用合約、9 保存、8 服務測試通過；
  412 畫布檢查、273 Chrome 操作檢查、12 最終引用流程檢查通過。
- 核心與保存／引用測試另通過 ASan/UBSan。MSVC 核心與 bridge 編譯通過；
  本機原生執行受 Smart App Control 限制，執行驗證與交付入口使用既有 WSL。
- 詳細對照、語法及驗證範圍見 `geometry-core/README.md`；可用
  `geometry-web/start.ps1` 重新編譯並啟動目前版本。

### GEO-126 ✅ 已修(2026-09-18) 全專案矛盾稽核;修掉子款 block 未同步與文件層過時宣稱
- **起因**:使用者要求全面檢查矛盾。派四條 fresh-context 稽核線(公理層內部 / 實作 /
  夾具測試 / 閱讀器與白話),外加自查文件層。
- **最嚴重的一項,是我造成的**:有子款的條文在閱讀器的 `blocks` 裡存**兩份**——
  `body.p01`(整條全文)與 `body.<letter>`(每個子款各一份)。先前的建置腳本
  **只改了 `p01`**,子款留著舊文。於是 `R6`、`R21`、`I23` 的頁面先顯示新版、再顯示相反的舊版。
  實際過期的 6 個:`R6.body.c`(at-edge)、`R6.body.e`(凍結)、`R21.body.f`(凍結)、
  `I23.body.a/b/c`(引用鎖)。已全部從 `公理層.md` 重新產生。
- **為什麼自我驗證抓不到**:先前用「blocks 串接 == clauses.body」當檢查,
  但 `clauses.body` 正是從 blocks 反推來的——**等於拿檔案跟自己比,永遠會過**。
  已改成**逐條對 `公理層.md` 比對**:`p01` 與每個 `body.<letter>` 都必須與 SSOT 逐字相同。
- **文件層三處過時宣稱(也是我寫的)**:
  `AGENTS.md` / `CLAUDE.md` 寫「閱讀器唯一產生方式是 make_axiom_reader.py」——**假的**,
  那支腳本現在輸出 `公理層-追溯診斷頁.html`;又寫「987KB、132 個 SVG」(實際 3.4MB、141 個)、
  「正典沒有批註功能」(已經有)。最危險的是「要改閱讀器 = 改 make_axiom_reader.py 模板整份重產」
  ——照做會產出另一份不同的閱讀器,正是該規則要防的事。已全部改寫,並補上五道完整性 assert 的說明。
  `閱讀器-設計規格.md` 的對象已換人(正典改成批註版),加了狀態標頭說明哪些仍有效、哪些失效。
- **稽核結論(四條線)**:
  - 實作:**行為層面與條文一致**。舊機制解析器全面拒絕(`current_geometry.c:8853-8864` 明寫長度、
    `:9401` span-auto、`geometry-core/references.inc:490` 四種舊錨法)。
    三處非行為性殘留:`current_geometry.c:9207` 孤兒註解寫「奇數 gap → 拒絕」但底下無程式碼、
    `ANCHOR_AT_GUIDES` 死列舉 `:11894`、`I23(b)` 訊息未帶 `V_GRID_LOCKED` 字樣。
    一處超出條文:I8a 預覽列**所有**已放角材而非嚴格依賴鏈子集;觸發指令集也比條文列舉的廣。
  - 夾具:行為都正確,但**多個檔頭註解仍描述已作廢的機制**
    (`_edge_grid_panel_odd_gap`、`_ax_i12_*`、`_edge_grid_locked*` 的歸因寫成 I23 實際是 I8a)。
    **覆蓋缺口**:I8a 預覽的**成功套用路徑(preview→confirm)零夾具**——
    R2「使用者確認才提交」從未被驗證過;I23(b) 單獨隔離也是 0。
  - 閱讀器:完整性三道 assert 全過,條目集合與 SSOT 零差集(66 條,D=21 I=24 R=21)。
- **仍未處理,留給使用者拍板**:
  1. `D6b:54`「唯一允許字面數字的地方」與 `D10:74` SERIES 的 `start`/`step`、
     `D10a:97` 的 `from c`/`panel`/`gap` 矛盾——那些都是裸 mm 字面值。
     要嘛把禁令擴及 D10/D10a(再一批條文改動),要嘛把 D6a/D6b 的措辭收進參考線範圍。
  2. `I8a:170` 的觸發清單沒列「重宣告邊界面而移動被 at-face 引用的邊」,
     但 `I13:204` 說被引用者移動一律走預覽。
  3. `R13:310`「角材以錨點 uv 判定」與 `D7:61`「不存凍結 uv」用語不一致。
  4. `geometry-guide/公理層-白話.md`(323 行)幾乎整份仍是舊制度
     (仍寫明寫長度、凍結、at-grid/at-edge/at/at-guides、引用鎖)。
     閱讀器內建的 `plain` 是新的,但**來源檔沒跟上**。

### GEO-127 ✅ 已修(2026-09-18) 收掉 GEO-126 列出的四項矛盾
- **D6a / D6b 的適用範圍**:原本寫「所有帶單位的量一律不得以字面數字出現」與
  「唯一允許字面數字的地方」,與 `D10` 的 SERIES `start`/`step`、`D10a` 的
  `panel`/`gap`/`from c` 仍收字面 mm 的事實互斥。措辭收斂為**參考線位置的引用式**範圍,
  並在 D6a 末段明寫:「這是已知的不一致,不是本條的例外」——按使用者「禁止來歷不明的
  數字」的原則,那些參數也該改成引用 D6b 具名常數(`spec 板寬 600`),
  沒有一併做是因為牽動 D10/D10a 條文、實作與 121 個夾具,**留待使用者拍板**。
- **I8a 觸發範圍**:原本列舉三種操作,漏掉「重宣告邊界面/承載面而改動被 at-face 引用的邊」
  與「改動被引用的具名常數」,與 `I13`「被引用者移動一律走預覽」不一致。
  改成以**「被引用者是否改變」為判準**,列舉只當舉例。
- **R13 用語**:「角材以錨點 uv 判定」與 `D7`「不存凍結 uv」字面打架。
  補明是**錨點求值後的 uv**(當下由 I13 的引用求出),不是欄位裡存著的座標。
- **I8a 正向路徑補夾具**:新增 `_edge_i8a_confirm.scene`,與 `_edge_freeze.scene` 成對——
  後者測「不預覽就直接改會被擋」,前者測「`preview` → `confirm <token>` → 真的套用」。
  `R2`「零違規且使用者確認才提交」先前**零夾具**,是條文寫了、實作做了、卻沒有任何
  測試證明的路徑。實測預覽輸出 `timber 1 center 500 -> 2000`,確認真的套用。
- **順帶查出一個會誤導所有人的坑**:`tests/run_tests.py:205` 預設用**repo 根目錄**的
  `cg_new.exe`,而那支是 GEO-125 之前的舊檔。照著跑會看到一堆假紅燈,
  錯誤訊息還是舊的「錨法只認得 at、at-guides、at-grid、at-edge」,
  會把人引去查錨法而不是查 exe。重建後 **122/122 全過**。

### GEO-128 ✅ 已採納（2026-09-18）跨面共用定位基準
- 使用者授權規劃與執行 agent 並行協作，後續明示檢查完成後提交合併；PR #1 經獨立審查及主審核對後批准合併。
- 公理逐條修改已審閱並正式採納。新增 D6c / I7a，未占用相位與子網格預留條號。
- 共同基準為房間 X/Y/Z 軸向無限平面，只引用具名規格；各承載面由唯一交線推導自己的 guide。
- 獨立 guide 存在與可見性分離，保留 grid I10 / I23 生成限制；R13 無法歸片仍拒絕。
- datum／spec／frame 改動需要跨面重算、預覽與原子提交；既有同面同軸局部引用限制保持。
- 範圍、逐條修改清單、交付驗收 A1–A11 與待決事項：`geometry-core/DATUM-PROPOSAL.md`。
- 實作、回歸與獨立審查已完成；實測明細見 `geometry-core/DATUM-VALIDATION.md`。A8 真瀏覽器建立／引用／預覽完成，取消／確認受自動審核拒絕仍未驗；A10 手機 runtime 未驗。主審接受此驗證範圍，未將未驗項視為通過。

### GEO-129 ✅ 已入層（2026-09-18）規格擴充：足以重建 3D 模型的確定性資料
- 使用者明示授權依建議擴充公理層；新增 D20–D25 / I26–I33 / R24–R30，保留既有預留條號。
- 定義具名法向區間擠出、可含多片同向面的邊界殼、複合空間／淨空、KEEP／UNION／DIFFERENCE、建模完整性及交換包。
- 舊 Space 保留 slot-space/1，不把槽位封閉誤稱水密；D3／D4 分離、D9 定義權威與 R8 快照語意保持。
- 確定性正交 cell 布林、標準面切分與三角化、來源特徵及摘要編碼已入規格；不得因模型／相機不同而猜另一份幾何。
- 逐條變更：`geometry-core/MODELING-CHANGES.md`；介面與驗收：`geometry-core/MODELING-CONTRACT.md`；18 組資料向量：`geometry-core/modeling-cases.json`。
- **現況：規格／白話／正典同步交付；新增 C 型別、幾何執行器、bridge、輸出與畫布功能尚未實作。** 向量只是未來驗收，不算實測通過。
- 實作順序：擠出及面輸出 → 殼拓撲／複合空間 → 正交布林 → 完整交換包與外部適配器；每個執行器先按 I32 宣告子能力。

### GEO-130 ✅ 已做（2026-09-19）實作：確定性 3D 參考執行器（後續項見條目末）
- 使用者授權「繼續實作」；不改公理條文，以 GEO-129 規格為基準。
- 完成 C 原場景 parser／World 接入與實際依賴快照，Python 精確擠出、殼、複合空間、布林及標準幾何。
- 交換包保留來源及摘要，可重建驗證；ModelWorld 提供預覽／確認／取消與失敗回滾。
- 提供 CLI、HTTP API、OBJ 匯出及帶孔牆／L 形空間範例。
- 36 項建模與 2 項傳輸整合測試通過；詳見 `geometry-core/MODELING-VALIDATION.md`。
- 後續：C World／舊 DSL 新型別整合、畫布建立與編輯、GLB／SketchUp 適配器及第二套完整引擎的跨實作驗收。

### GEO-131 ✅ 已拍板（2026-09-20）公理層見證圖：一條文一圖、圖變即警報
- 使用者定性：幾何相關條文須配示意圖，但**示意圖是條文的見證，不是文件**——
  條文為真 ⇒ 圖不變（所以沒有版本問題）；圖變了 ⇒ 是警報，代表夾具／引擎／條文之一動了，
  必須由使用者確認要改哪一邊，**絕不自動覆寫**。
- 為什麼不手繪：手繪圖跟白話一樣是人寫的，會跟條文一起錯、偵測不到漂移
  （`公理層-白話.md` 已整份落後過一次；閱讀器內 63 張例圖全標「未重新執行引擎」，
  其中 D1 例圖仍寫「奇數 gap → 拒絕」，與現行 D10a 及引擎行為相反）。引擎推導的圖才有「變了就是有事」的性質。
- 實作：`geometry-guide/witness.py`（`--build` 建圖 / `--check` 逐位元比對、有差即非 0 且不寫檔 / `--list`）
  + `geometry-guide/witness/manifest.json`（條號 → 夾具 → expect → 視圖）+ `witness/<條號>.svg`。
  沿用 `axiom_examples.py` 的 run_scene / crop_bottom / before_failure，不另做幾何或裁切。
  夾具必須在註解提到條號（`axiom_matrix.py` 同一判準），manifest 不能單獨成為連結。
  `.gitignore` 對 `geometry-guide/witness/*.svg` 開唯一例外（全域 `*.svg` 仍忽略）。
- 樣板：I19 ← `_role_rc_boundary_ok.scene`（仰視圖）。實測：同夾具兩次輸出逐位元相同；
  臨時把夾具房深 3000→3200 後 `--check` 正確報「夾具內容變了」並列 64 行 diff、rc=1、未覆寫。
- 已鋪 17 條（2026-09-20，使用者「都鋪」授權）：D2、D6、D6c、D10a、D11、D15、D16、D17、I13、I19、I22、
  R6、R7、R16、R17、R19、R21。新寫夾具 6 個（`_wit_*.scene`，已入 `tests/run_tests.py`，128/128 通過）：
  D2 牆 frame（view=all）、D6 參考線被孔切段／面外零段、D6c 三面共用 datum（view=all）、
  I13 寬 27 → footprint [987,1014]、R6 穿孔格線兩個 cell 各選一段、R19 邊界主支 2600−20−20=2560。
  既有夾具補條號註解 2 個（`_test_hole_auto` +D11、`_test_between` +R21）。
  D16 與 I22 共用 `_role_priority_ext_custom.scene`（同一現象：延伸段與其規則），圖檔仍各一張。
  `witness.py` 加 view=front/side/all（R16 看前視、R17 看側視、跨面條文看整張）。
- **暫無圖（不手繪頂替）**：D20 / D21 / D23 / R27 屬 GEO-129 `orthogonal-model/1`，
  C 核心與場景 DSL 尚未實作（I32：條文存在 ≠ 已實作），無夾具可推導；待 GEO-130 接入 C World 後補。
- 後續：閱讀器例圖槽改讀見證圖（須過 AGENTS.md 五道 assert）另開票；`公理層.md` 未動。
- 關聯決定（同日、尚未最終拍板）：使用者擬將本 repo 定性為「該領域世界的來源」，其他專案須遵守其公理；
  建議配套：舊 repo `geometry` 封存、公理層加版本號、下游以 `.scene` 夾具／契約測試證明遵守。

### GEO-132 ✅ 已做（2026-09-20）閱讀器例圖槽改讀見證圖
- 使用者指示「閱讀器例圖槽改讀見證圖,開票做」。做法:`sync_axiom_reader.py` 在每條卡片的歷史範例前
  插入 `<section class="witness-section">`,內容由 `geometry-guide/witness/<條號>.svg` **讀檔**嵌入
  (base64 data URI,引擎淺色 `<style>` 整段換成與歷史例圖相同的深色配色;非 all 視圖另附「展開三視圖」)。
  同步器**不執行引擎**——圖是否仍與夾具/引擎一致是 `witness.py --check` 的事,兩道守門不混。
- 歷史範例區塊與其批註身份原樣保留(AGENTS.md 五道 assert 不受影響;見證圖沒有 `.review-target`)。
- CSS `.witness-section` 一次性注入正典 `<style>`(冪等)。`validate()` 回報 `witness` 數量。
- 測試:`tests/test_axiom_reader.py::test_witness_figures_match_manifest_and_files`——manifest 有圖的條文
  每條恰嵌一張,且與同步器由當前檔案算出的完全相同;既有冪等測試因此成為「見證圖變了但沒重出閱讀器」的警報。
- 文件:READER-BUILD.md、AGENTS.md 補記。`公理層.md` 未動。

### GEO-133 ✅ 已做（2026-09-20）見證圖規範 v1：拓樸可見、全部同一套畫法
- 使用者指出(附截圖):20mm 料在 4000mm 房間裡只剩三條線,「角材怎麼一根一根排、誰停在誰身上」完全看不出來,
  而那正是 D15/I19/R19 的內容;並要求**所有示意圖用相同規範建立,不得各畫各的**。
- 規範:`geometry-guide/witness/規範.md`(v1)。每張固定三區——① 主圖(引擎視圖原樣,角材依角色四色著色,
  端面畫停止標記)② 接點列(每個角材端面一格,同一份幾何等比例放大,窗 = 8×料寬,格標題 `t3·END→t1` 用 D18 擋面參照寫法)
  ③ 圖例(每張相同)。沒角材的條文接點列為空,不是另一套版面。
- 拓樸來源:`witness.py` 從引擎文字輸出反推每個端面的擋面(共面 + 沿面內橫向涵蓋全寬;D11 三種來源),
  必須唯一否則失敗不出圖;結果另存 `<條號>.joints.json` 與 SVG 一起逐位元比對——**拓樸是見證本體,圖是呈現**。
  `--check` 失敗時能分辨:夾具變了 / 夾具沒變但拓樸變了 / 拓樸沒變只有幾何輸出變了。
- 反推時踩到一次:D11「涵蓋端面全寬」的寬是面內橫向,不含厚度方向(27×33 主支停在 20×20 邊界材側面合法);修正後 17/17 唯一。
- 17 張全部重出、閱讀器重出、`test_axiom_reader` 9/9、`run_tests` 128/128。`公理層.md` 未動。
- 已知:`axiom_matrix.py --strict` 本來就有 22 條紅燈(GEO-129 未實作條文、D5/D12/I11 等缺夾具),與本票無關;
  GEO-131 曾誤報「無紅燈」,是管線吃掉了退出碼,在此更正。

### GEO-134 ✅ 已做（2026-09-20）停止標記不得暗示占用；witness 自驗物理碰撞
- 使用者問「你知道物理碰撞嗎——相同空間不能同時被不同物體占用」。引擎(I11)與拓樸反推(端面共面 = 零面積接觸)都對,
  但**標註層**畫錯:停止標記中心線壓在接觸面上,一半粗度伸進對方料,看起來像穿透。
- 修:標記整條退到被裁料自己這一側(沿長度軸向內偏移半個粗度)。新增兩道自驗,違反即不出圖:
  (a) 同承載面任兩支 A0 footprint 正面積交集必須為 0(I11,witness 自己再驗一次,不依賴引擎);
  (b) 停止標記範圍不得進入擋面對方角材的 footprint。突變測試:把偏移設回 0 → `--check I22` 報「侵入」。
- 規範 §2/§4 補記;17 張重出;閱讀器重出;全部測試通過。

### GEO-135 ✅ 已做（2026-09-20）停止標記長度 = 料寬、不外延；碰撞檢查擴及所有相鄰角材
- 停止標記原本長 1.6× 料寬,外延部分會伸進貼在旁邊的另一支料——標註暗示了不存在的占用。
- 修:標記長 = 端面本身的寬、一個 mm 都不外延;`check_marks_outside` 從「只對被頂的那支」
  改為對**所有**其他角材的 A0 footprint 做正面積交集檢查,碰到即不出圖。
- 新增獨立驗證 `tests/test_witness_marks.py`(不 import witness.py,只讀 repo 內 SVG/joints.json
  用最笨的矩形交集重算):任兩角材不重疊、標記不侵入他料、每個接點在主圖都有標記。

### GEO-136 ✅ 已做（2026-09-20）接點格改 Python 內裁切,不用巢狀 viewBox
- 巢狀 `<svg viewBox>` 在多數檢視器不裁切,整個場景會不裁切地畫出來,看起來像料互相穿越。
- 修:`flat_tile()` 在 Python 裡把每個形狀(Sutherland–Hodgman 多邊形 / Liang–Barsky 線段)
  裁到視窗、算成版面座標,只輸出平面 polygon/line/rect——任何檢視器只能畫出同一個結果。
- `manifest.json` 的 D2 改 `view=front`(側視圖是牆的端面投影,兩支立料會投影重疊,
  獨立測試視為占用)。規範 §3 補記「不得用巢狀 viewBox/`<use>`/`<g transform>` 做放大裁切」。

### GEO-137 ✅ 已做（2026-09-20）停止標記改填色矩形:stroke 粗度是螢幕像素不是 mm
- 使用者一再指出圖上「藍色主支穿過琥珀色邊界材、穿過孔邊」。根因:引擎 CSS 的
  `vector-effect:non-scaling-stroke` 讓 `<line class="stop" stroke-width>` 的粗度變成
  **螢幕像素**而非 mm——圖縮小時 27mm 的料只剩約 5px,8~40px 粗的標記線直接穿過整支料。
  放大看「看起來對」、座標算「算起來對」,兩個都是假的。
- 修:`stop_mark_box()` 直接算標記矩形(端面寬 × 向被裁料內側 0.3×料寬),`stop_marks()`
  輸出 `<rect class="stop" fill=角色色>`;`check_marks_outside` 改用同一個 box;
  `flat_tile` 保留 `fill` 屬性;CSS `.stop{stroke:none}`;圖例樣本改 `<rect>`。
- `test_witness_marks.py` 同步改抓 rect/polygon 標記,新增「全檔不得出現 stroke 式 stop 標記」。
- 規範 §2 停止標記列改為填色矩形寫法。驗收方式改為**用眼睛看**:整張、480px 縮小、
  逐接點格放大三種尺度,30 格全數 Chrome 截圖目視通過(含原病徵的 t5·START→t1、
  t7·END→h0e0),閱讀器內嵌圖同版重出。
- 17 張重出、`--check` 17/17、test_witness_marks 4/4、閱讀器重出且冪等、
  test_axiom_reader 9/9、run_tests 128/128。`公理層.md` 未動。

### GEO-138 ✅ 已做（2026-09-20）閱讀器：條文瀏覽時示意圖同頁並排
- 使用者需求:翻頁式一條一頁介面下,見證圖埋在卡片下半要捲才看得到;
  希望**讀條文時對應示意圖就在旁邊**。使用者已拍板「兩者都做」:
  - 右欄 sticky 側欄,預設只顯示**主圖段落**(同一張 SVG 換 viewBox 露出主圖區,
    不重出圖、不動規範、不動 `witness.py`);可切換顯示完整三區圖;側欄可收合。
  - 完整版見證圖仍保留在卡片下方原位置,不搬走。
  - 89 條中只有 17 條有見證圖:無圖的條維持單欄,不出現空側欄。
  - 手機/窄寬不掉進並排:圖回卡片內 inline(現行版面)。
- 實作面:只動 `sync_axiom_reader.py` 模板 + CSS/JS 與 `閱讀器-設計規格.md`;
  五道 assert 必須照過;`公理層.md` 不碰。併入第 9 流閱讀器改版(GEO-114~121 之後)。

---

## 第 11 流：閱讀器可用性(2026-09-20 立;設計規格作廢後重新界定)

**來源**:外部 agent 的《公理層閱讀器 UI/UX 審查報告》16 條(R1～R16),
已逐條對現行 `geometry-guide/公理層-閱讀器.html` 用腳本核對,**數字全部屬實**
(僅檔案大小它寫 3.49 MB、現為 3.94 MB,因報告早於 GEO-137 重出)。

**依據的變更**:同日使用者拍板 `閱讀器-設計規格.md` **整份作廢**,
報告中引用該規格的論據(R16 引 §1、R3 引 §8 等)**一律不採為依據**。
改以 **GEO-120(🔒 已拍板,2026-09-17)** 為判準。交叉比對後發現:
**報告的 6 項發現其實是 GEO-120 拍板決定的回歸,不是設計偏好**——
這批屬於「違反已拍板決定」,必須修;其餘屬設計取捨,需使用者拍板後才動。

**根因(比 16 條本身重要)**:
1. 計數與版本沒有單一來源 → R2、R12、R14。
2. 色彩沒有 token 化、圖面色寫死在 base64 SVG 裡 → R6、R10、R11。
3. 「閱讀」與「校對」共用同一個版面 → R1、R5、R13。

### GEO-139 ✅ 已做(2026-09-20) 回歸修復:閱讀器違反 GEO-120 的四項拍板
- **性質**:🟢 違反 🔒 已拍板決定,不是設計偏好,直接修。
- **內容**:GEO-120 拍板了四件事,現行正典四件全破:
  1. **單頁長捲、Ctrl+F 保住**(拍板一)→ 現行 `var mode='single'`,
     `a.hidden = mode==='single' && a.id!==current`,首屏 88 條在 DOM 裡是 hidden,
     瀏覽器搜不到。(審查 R1,P0)
  2. **hover 快速預覽與點擊固定面板並存**(拍板二;原文寫「砍掉 hover 是淨損失」)
     → 全檔 grep 不到任何 hover 預覽。
  3. **雙主題、深色為預設**(拍板三)→ 現行 `<html data-theme="light">`,
     且全檔 `prefers-color-scheme` 出現 **0 次**,跟隨系統的機制也沒了。
  4. **追溯燈號/三向連結/樞紐徽章不得丟失**(連帶約束)
     → 全檔 grep `.trace` / `trace-ok` / `trace-partial` / `trace-none` / 「樞紐」皆為 **0**。(審查 R3,P1)
- **驗收**:(a) 首屏不 hidden 任何條文,瀏覽器 Ctrl+F 搜得到最後一條的條文字串;
  (b) 預設主題為深色且 `prefers-color-scheme` 生效;
  (c) 導覽項與條文 eyebrow 有追溯燈號(綠=原始碼+夾具、黃=其一、紅=皆無),資料由
  `axiom_matrix.py` 的既有判準產生,**不得手寫白名單**;
  (d) 條號連結有 hover 預覽,且點擊仍開固定參照欄。
- **檔案**:`geometry-guide/sync_axiom_reader.py`(模板與腳本)、重出正典。
- **進度**:
  - ✅ 拍板一 單頁長捲:`mode` 初值改 `'all'`,首屏 89 條全在 DOM、hidden=0(瀏覽器實測)。
  - ✅ 拍板三 深色預設 + `prefers-color-scheme`:系統深色→dark、系統淺色→light,已存偏好優先。
  - ✅ 連帶約束 追溯燈號/三向連結/樞紐徽章:**定義沿用專案原本的 `make_axiom_reader.py:431-433`,
    不自己發明門檻**——綠=原始碼且夾具、黃=其一、紅=皆無;樞紐=被引用數 ≥ 3。
    資料由 `axiom_matrix.py` 推導(唯一來源),導覽項左邊 4px 燈號、條文頭部燈號徽章與樞紐徽章、
    卡片底部「三向連結」可收合區(原始碼函式/夾具檔/變異 id)。
    實測分布:綠 54、黃 13、紅 22;樞紐 34 條。
  - ✅ 拍板二 hover 快速預覽:`a[data-ref]` 滑入即出浮卡(條號＋標題＋條文前 150 字,markdown 記號已去除),
    捲動/Esc 收起;只在 `(hover:hover)` 的裝置啟用,與觸控長按不衝突(拍板原文:砍掉 hover 是淨損失)。
    點擊開固定參照欄的行為不變,兩者並存。
- **相依**:無。**估時 3h**。

### GEO-140 ✅ 已實作（2026-09-28 補核對紀錄）計數與版本號要有單一來源
- **性質**:🟢 客觀錯誤(顯示的數字與事實不符)。
- **內容**:實際 89 條,但 `<title>` 寫「66 條」、切全文的 toast 寫「已顯示全部 66 條」、
  `#read-position` 靜態寫「12 / 63」、`#workspace-position` 寫「1 / 63」、
  `#review-count` 寫 4(說明寫 5)、`#review-revision` 寫「文字 r1」但 `<title>` 寫 r4。
  同步器已經算出 `clauses`/`comments`/`witness` 等數字,卻沒寫回 HTML 靜態值與 JS 字串。
  改為:同步器產出時把全部計數寫進**一組 `data-*` 或一個 JSON**,HTML 靜態值即真值,
  JS 一律從那裡取;**禁止在字串裡寫死數字**(含 toast)。(審查 R2 P0、R14 P3)
- **驗收**:全檔 grep 不到「66 條」「/ 63」「r1」這類硬編碼;
  `test_axiom_reader.py` 新增一項:HTML 裡出現的每個計數都等於由資料算出的值;
  首屏載入前後數字不跳動。
- **檔案**:`geometry-guide/sync_axiom_reader.py`、`tests/test_axiom_reader.py`、重出正典。
- **相依**:無。**估時 2h**。

- **2026-09-28 核對**：既有 `reader_counts()`／`apply_counts()` 與 `test_counts_have_a_single_source` 已落地，原工單狀態漏更新。本次未改產物；`sync_axiom_reader.py --check` 的 `counts_single_source` 通過，`tests/test_axiom_reader.py` 全部 24 項通過。此為來源／產物自動驗證，未新增首屏視覺量測。

### GEO-141 ✅ 已做(2026-09-21) 色彩 token 化;圖面色與互動色分家
- **性質**:🟢 全部可做(Q1 已於 2026-09-20 拍板 🔒)。
- **內容**:
  - head CSS 有 **40 個不同 hex**,批註系統整套色在 token 之外
    (`#c68d2a`×5、`#9a5200`×2、`#ad3424`、`#bb6c59`,深色模式再逐條覆寫 `#eac076`/`#ffb3a5`)。
    收成 `--note` / `--note-bg` / `--note-strong` / `--danger` 四個 token,兩套主題各一組,
    深色只改 token 值,刪掉逐條選擇器補丁。(R10 P2)
  - **281 張 base64 例圖與 17 張見證圖硬編碼深色底**(`svg{background:#181e24}` 等);
    淺色主題下是黑方塊。改吃 CSS 變數(`--geo-boundary`/`--geo-timber`/`--geo-guide`/`--geo-grid`),
    同步器嵌入時替換 style 段。**注意**:見證圖的深色化是 GEO-132 我方加的,屬同一問題。(R6 P1)
  - 焦點環寫死 `outline:3px solid #288b9c`,既不隨主題也不等於互動色 `--accent`;
    改 `outline:2px solid var(--accent); outline-offset:4px`。(R11 P2)
- **驗收**:全檔 CSS 規則內 grep 不到裸 hex(token 定義區除外);
  淺/深兩主題各開一次,例圖與見證圖的底色、線色都跟著主題走;
  見證圖 `witness.py --check` 仍 17/17(圖檔本身不因此改動,只有嵌入時的 style 段變)。
- **🔒 拍板(Q1)**:**只 token 化底色與線色**;見證圖的四個角色色屬 `witness/規範.md` v1、與條文語意綁定,
  **不動**,17 張見證圖不必重出。
- **進度**:
  - ✅ **批註四色 + 範例/實錄/命中色 + 圖卡底色**收成 13 個 token(`--note`/`--note-strong`/`--danger`/
    `--proposal`/`--figure-bg`/`--reject-*`/`--transcript-*`/`--hit-*`/`--link-underline`/`--sheet-ref-ink`),
    兩套主題各一組;**深色的三條逐條選擇器補丁已刪除**,值移進 `:root[data-theme=dark]`。
  - ✅ **焦點環** `outline:3px solid #288b9c` → `outline:2px solid var(--accent);outline-offset:4px`;
    `#288b9c` 全檔歸零。
  - ✅ `validate()` 與測試各加一道:CSS 規則內不得再有裸色碼(`@media print` 與 token 定義區除外)。
  - ✅ **圖「內」的顏色**(🔒 Q8:只改見證圖 17 張):見證圖改 **inline `<svg>`**,
    圖自帶的兩個 `<style>` 全部拿掉、改由 `WITNESS_DIAGRAM_CSS` 以 `.witness-diagram` 作用域提供
    (`.title`/`.label`/`.frame` 這些名字太通用,直接內聯會汙染整份文件)。
    新增 10 個 `--wit-*` token,兩套主題各一組;**角色色維持字面值不動**(🔒 Q1)。
    「展開三視圖」不再放第二份圖,改成同一個 `<svg>` 換 `viewBox`。
    右欄面板(GEO-138)改成**複製 svg 節點**而非複製 `src`。
    **實測(1440px)**:淺色 svg 底 `#eef2f5`、承載面 `#dbe9ff`、邊 `#3366cc`;
    深色 svg 底 `#181e24`、承載面 `#304557`、邊 `#84c8f6`;
    `role-primary` 兩個主題都是 `#63b3ed` —— 角色色確實沒動。
    見證圖區塊內 base64 歸零,`witness.py --check` 仍 17/17(圖檔本身未動)。
  - ⬜ **281 張範例圖維持 base64**,這是 Q8 拍板的一部分,不是遺漏。原因:
    281 張範例圖是 base64 `<img>`,`<img>` 裡的 SVG **看不到頁面的 CSS 變數與 `data-theme`**,
    只看得到系統的 `prefers-color-scheme`。要讓它們跟著閱讀器的主題切換,只有三條路:
    (a) 改成 inline `<svg>`(見證圖 17 張可行,且會比 base64 更小;281 張範例圖則會讓 DOM 爆炸)、
    (b) 出淺深兩份(檔案再大一倍)、(c) 只跟系統不跟使用者切換。
    **且範例圖被標為「歷史範例,未依本次條文重新執行」——重跑引擎重產會破壞這個語意。**
    已靠 `--figure-bg` 的圖卡底色減輕淺色主題下的突兀。
- **相依**:無。**估時 3h**。

### GEO-142 ✅ 已實作（2026-09-28 補核對紀錄）搜尋:跳轉不清空查詢;補 Ctrl/⌘K
- **性質**:🟢 客觀缺陷(功能自相矛盾)。
- **內容**:`navigate()` 內先呼叫 `resetSearch()`,把 `search.value` 清空、`activeGroup` 還原,
  所以「搜尋 → 點第 2 筆 → 想看第 3 筆」必須重打。方向鍵與 Enter 的鍵盤導覽做得很完整,
  卻在跳轉那一刻被自己清掉。改為:跳轉後保留查詢字串與命中清單,導覽顯示「第 n / m 筆」,
  Enter 連續跳下一筆,只有 × 或 Esc 才清空。(R7 P1)
- **對審查的更正**:R7 另稱「沒有全域聚焦搜尋的快捷鍵(規格 §4.4 要求 Ctrl+K)」——
  **不成立**。`reader-script` 早有 `document.addEventListener('keydown',…(e.ctrlKey||e.metaKey)&&e.key==='k'…)`,
  會 `openDirectory()` 並 `search.focus()`,實測可用。本票不含此項,只保留防回歸檢查。
- **驗收**:搜一個詞、連按 Enter 能依序走完所有命中且查詢字串不變;Esc 清空;Ctrl+K 聚焦。
- **相依**:無。**估時 1.5h**。

- **2026-09-28 核對**：既有 `apply_search_fixes()`／`search_regressions()` 與 `test_search_keeps_query_after_navigating` 已落地，原工單狀態漏更新。本次未改產物；`sync_axiom_reader.py --check` 的 `search` 通過，`tests/test_axiom_reader.py` 全部 24 項通過。此為程式與產物契約檢查，未把它當成本次真瀏覽器鍵盤操作證據。

### GEO-143 ❎ 不需要做(2026-09-20,實測推翻前提) 效能:例圖延後載入
- **性質**:🟢 可量測。
- **內容**:3.94 MB 單檔,281 張例圖全部 base64 內嵌,首屏一次付清
  (審查實測在預覽容器內 7 秒未完成排版)。單檔自足是刻意取捨(拍板 1),不動;
  但把預設收合的範例圖改成 `<template>` 內的原始 SVG、展開時才注入 DOM,
  或 `loading=lazy` + IntersectionObserver 延後解碼。優先處理 141 筆範例中預設收合的那些。(R9 P2)
- **驗收**:首屏可互動時間(以 DOMContentLoaded 後可捲動為準)明顯下降並記錄實測值;
  展開任一範例仍看得到圖;五道 assert 與冪等測試全綠。
- **實測(2026-09-20,Chromium,桌面 1440×900,本機 http)**——**前提不成立,不動它**:

  | 量測項 | 值 |
  |---|---|
  | `domContentLoaded` / `loadEventEnd` | **754ms / 758ms** |
  | 強制 layout | **0ms** |
  | 捲到底(頁高 101,459px) | **7.4ms** |
  | 展開 30 個收合範例 | **0.2ms** |
  | JS heap | **2MB** |
  | 282 張圖中 `complete=false` | **280 張** |
  | 282 張圖中 `naturalWidth=0` | **279 張** |

  **決定性的一項是最後兩列**:`loading="lazy"` 對 `data:` URI **是有效的**——
  282 張圖裡只有 2 張真的載入過,其餘連解碼都沒開始
  (`img.decode()` 對離屏的 lazy 圖根本不會 settle,我第一次量就是這樣掛了 45 秒)。
  也就是說本票想做的「延後載入」**瀏覽器早就做了**,而審查說的
  「281 張內嵌圖,首屏成本全付在載入時」**與事實相反**——首屏只付 HTML parse。

- **順手驗過的另一條路也不成立**:把 base64 改成 URL 編碼的 SVG。
  實測 base64 酬載 2.13MB、原始 SVG 1.60MB、URL 編碼後 **2.40MB**——
  因為圖裡有大量中文標籤要百分比編碼,**改了反而大 7%**。
- **唯一還在的成本**是 3.82MB 檔案本身的 parse(桌面約 750ms)。
  在拍板 1「單檔自足」不變的前提下,唯一能減的是把 281 張圖改成 inline `<svg>`
  (省掉 base64 的 4/3 膨脹,約 0.53MB),代價是 DOM 節點從 14,189 大約翻倍——
  **拿 14% 檔案換兩倍 DOM,不划算**。
- **未量到的情況(誠實標記)**:以上全在桌面 Chromium 量。低階手機的 parse 成本、
  以及 Firefox/Safari 是否同樣對 `data:` URI 套用 lazy,**都沒驗**。
  若日後在實機上真的慢,再回來開票,並且**要帶實機數字**,不要再用推測。
- **相依**:無。**改判:不做**。

### GEO-144 ✅ 已做(2026-09-21) 批註過期引文就地可重新綁定
- **性質**:🟢 可做(Q2 已於 2026-09-20 拍板 🔒)。
- **內容**:4 處 `.stale-note` 只寫「段落已改版;以下引文保留批註當時的快照,不自動重新配對」,
  但 `reanchor()` 只出現在「全部批註」清單的動作列,且要先過一個 `confirm()`。
  讀者在正文看到過期批註時沒有任何可點的下一步。建議:就地提供「重新綁定這段 / 看原引文」,
  `confirm()` 改為面板內的前後對照 + 主鈕。(R8 P1)
- **驗收**:過期批註可在正文就地重新綁定,且綁定前看得到前後差異。
- **🔒 拍板(Q2)**:就地提供「重新綁定這段」;拿掉 `confirm()`,改成面板內前後對照 + 主鈕;綁定後可復原一次。
- **實作**:`noteHTML()` 在 `anchorState!=='exact'` 時就地加一列動作(重新綁定這段 / 回到段落);
  `anchorHistory` 非空時另加「復原綁定(回到上一個定位)」。
  `reanchor()` 從一個 `confirm()` 改成 `dialog()` 面板:左「批註當時的引文」、右「目前的段落」,
  段落已不存在時不給主鈕並明說原因。新增 `reanchorConfirm()` / `undoReanchor()` 與對應 action 分派。
- **實測**:2 則過期批註各有就地動作列;點「重新綁定這段」開出標題
  「重新綁定 D1 · 原文 第1段」的面板,含「批註當時的引文 / 目前的段落」兩欄與確定鈕;
  全檔不再有舊的 confirm() 文案。
- **相依**:無。**估時 2h**。

### GEO-145 ✅ 已做(2026-09-20) 正文不常駐批註按鈕
- **性質**:🟢 可做(Q3 已於 2026-09-20 拍板 🔒)。
- **內容**:452 組 `.review-block > .block-tools` 每段固定掛一列(段落標籤 + 「＋批註這段」),
  純閱讀時與正文等權,每段之間插進 34–44px 控制列。建議改 hover/focus/長按才出現;
  已有批註的段落保留常駐琥珀左邊條與批註數徽章。(R5 P1)
- **驗收**:純閱讀時正文不被控制列切碎;觸控裝置仍有可達的批註入口;既有批註仍一眼可見。
- **🔒 拍板(Q3)**:改 hover / focus / 長按才出現;已有批註的段落保留常駐琥珀左邊條與數字徽章。
  **驗收另加一項:觸控裝置長按不得與瀏覽器原生選字衝突,須實機驗。**
- **實測**:452 個段落中 **447 個工具列收合成 0×0(opacity 0)**,只有 5 個有批註的段落常駐;
  鍵盤 Tab 進按鈕時 `:focus-within` 會展開,所以沒有「看不見卻可聚焦」的死角。
  觸控長按 500ms 展開且**不 preventDefault**,原生選字手勢仍可用;手指一移動即取消。
  ⚠ 觸控長按與原生選字並存這點是在桌面瀏覽器以事件模擬驗的,**尚未實機驗**(驗收條件仍掛著)。
- **相依**:無。**估時 2h**。

### GEO-146 ✅ 已做(2026-09-20) 參照欄與批註面板並存,不互相關閉
- **性質**:🟢 可做(Q4 已於 2026-09-20 拍板 🔒);與 **GEO-138** 合併施工。
- **內容**:`workspace-script` 的 `docked()` 模式下 `present(id)` 會把另一個面板 `hidden`,
  所以寫批註時點正文裡的條號連結,草稿面板直接被參照面板換掉;草稿只在
  `visibilitychange`/`beforeunload` 時 `captureDraft()`,切 tab 不觸發。
  校對的核心動作正是「一邊對照引用、一邊寫批註」,現在互斥。(R13 P2)
- **驗收**:讀引用與寫批註可同時存在;切換前草稿必被保留且有可見提示。
- **🔒 拍板(Q4)**:右欄改**上半固定見證圖(GEO-138)+ 下半 tab(參照/批註)**;
  切 tab 前一律先 `captureDraft()` 並顯示「草稿已保留」。見證圖常駐,不與參照/批註互斥。
- **實作**:`present()` 在 dock 模式下若從批註分頁切走,先 `window.axiomReviewUI.flushDraft()`
  再 toast「草稿已保留」。原本只有 `showReference()` 這一條路會 flush,從其他入口切換就會丟草稿。
  分頁本身維持「參照 / 批註」二選一(🔒 Q4 拍板:上半見證圖常駐、下半才是 tab)。
- **相依**:與 GEO-138 同一批施工。**估時 3h**。

### GEO-147 ✅ 已實作（2026-09-28 補核對紀錄）資訊層級:原文與白話的順序
- **性質**:🟢 可做(Q5 已於 2026-09-20 拍板 🔒)。**注意**:舊依據(設計規格 §4.2)已作廢,
  但頁尾文案「原文為準,白話輔助閱讀」與現行版面順序(白話在前)自相矛盾,這點客觀成立。
- **內容**:89 條一律 `plain-section` 先於 `original-section`;區塊標籤「白話解釋/條文原文」
  同為 14px h3,兩者同重。建議順序改 原文 → 白話 → 範例 → 見證圖 → 被引用,
  區塊標籤降為 12px/.08em muted。(R4 P1)
- **驗收**:順序與頁尾宣稱一致;五道 assert 全綠(區塊 id 與批註錨點不得因換順序而失聯)。
- **🔒 拍板(Q5)**:順序改 **原文 → 白話 → 範例 → 見證圖 → 被引用**;區塊標籤降為 12px/.08em muted。
- **相依**:無。**估時 1.5h**。

- **2026-09-28 核對**：同步器的區塊順序及樣式、`test_original_text_precedes_plain` 已落地，原工單狀態漏更新。本次未改產物；`sync_axiom_reader.py --check` 的五道 assert 與獨立 SSOT 對照通過，`tests/test_axiom_reader.py` 全部 24 項通過，包含區塊順序、重建冪等及批註保留；未新增手機或真瀏覽器操作驗證。

### GEO-148 ✅ 已做(2026-09-20) 斷點 960–1279px 與手機底部列
- **性質**:🟢 可做(Q6 已於 2026-09-20 拍板 🔒)。舊依據(設計規格 §1)已作廢,本票依 Q6 重新界定。
- **內容**:
  - `dockQuery=matchMedia('(min-width:1280px)')`,960–1279px 之間左欄已是固定導覽、
    右欄卻還沒出現,點條號走 `showModal()` 把正文整個蓋掉——與右欄文案
    「對照引用,不離開正文」矛盾。建議改底部半高 sheet。(R16 P3)
  - 手機底部列擠 5 個控制,`gap:3px`、按鈕 13px、位置指示 11px/最小寬 35px,359px 以下再降 12px。
    建議只留「目錄·上條·位置·下條」,批註入口移到條文內與頂列。(R15 P3)
- **驗收**:960/1100/1279px 三個寬度下點條號不蓋住正文;390px 下底部列字級 ≥14px 且無溢位。
- **🔒 拍板(Q6)**:中間寬度用**底部半高 sheet**;手機底部列只留四鍵,批註入口移到頂列。
- **實作**:中間寬度改用 `el.show()`(**非模態**)而非 `showModal()`——這是關鍵,
  模態即使把 backdrop 設透明,正文仍然不能操作,達不到「對照引用,不離開正文」。
  新增 `halfQuery`(960–1279px)與 `body.half-sheet-open` 讓位 padding,dialog 關閉時收回。
- **實測**:
  - 1100×860:sheet `open=true`、`:modal=false`、`position:fixed`、貼底、高 430px(正好半屏),
    `D6` 條文仍在畫面上 → 正文與引用同時可見**且可操作**。
  - 375×812:底部列剩「目錄 / 上條 / 1 / 89 / 下條」**四鍵**,按鈕 14px、位置 12px(原 13px/11px);
    「全部批註 5」已出現在頂列。
- **相依**:無。**估時 2h**。

### GEO-149 ✅ 已做(2026-09-20) 證據強度可見:哪些條有範例/見證圖
- **性質**:🟢 資料驅動(數字客觀);呈現方式併入 GEO-139 的燈號。
- **內容**:89 條裡 63 條有範例(26 條沒有)、17 條有見證圖(72 條沒有),
  但導覽與條文頭部沒有任何標示,讀者得逐條點開才知道這條是不是「只有文字」。
  在導覽項與 eyebrow 標「例 N · 見證圖 N」,導覽頂端給以真實資料為準的篩選 chip
  (有批註/有例圖/有見證圖/無證據);**禁止硬編碼條號白名單**。(R12 P2)
- **驗收**:標示數字等於實際數量(與 GEO-140 同一份計數來源);篩選 chip 結果與實際相符。
- **進度**:✅ 導覽項標「例 N · 見證圖」並帶 `data-trace/data-ex/data-wit/data-hub/data-note`;
  ✅ 導覽頂端四個篩選 chip(有批註 5 / 有例圖 63 / 有見證圖 17 / 無追溯 22),數量由資料算,
  **無硬編碼條號白名單**(被作廢的第 3 版原型正是寫死 `['R6','R18','R19','R20','R21']`)。
  與搜尋、分類篩選疊加——實測 89 → 點「有見證圖」17 → 再搜「參考線」4 條。
- **相依**:GEO-139、GEO-140。**估時 1.5h**。

---

## 第 0～8 流稽核結果(2026-09-20,fresh-context agent 唯讀盤點)

舊工單(GEO-001～083,實際 52 張;BACKLOG 開頭自稱 46 張是錯的)立於 2026-09-12,
從未標過完成狀態。2026-09-20 派 agent 以 repo 實況逐張核對(唯讀,未編譯未跑測試),
判準只採客觀證據(檔案存在與否、`current_geometry.c` 的函式/字串、`run_tests.py` 的 TESTS、夾具檔)。

**統計:已完成 19、未完成 24、已不適用 8、無法判定 1。**

### 仍值得做(依價值排序,agent 判斷)

1. **GEO-075** 下料清單加總同規格數量——離「能拿去現場用」最近的一步
2. **GEO-043** Space 尺寸/體積報告(W×D×H)——六面封閉都判得出來,卻不印房間淨尺寸
3. **GEO-030** `CreateFontW` 失敗未判 NULL 就 `SelectObject`——GDI 視窗真實當機風險
4. **GEO-014** BOM 檢查補 `length>=3`——一行修法,消除讀未初始化記憶體的隱患
5. **GEO-041** Space 錯誤訊息分類——六種失敗原因擠成一句話
6. **GEO-077** scene `include`——上百個 `.scene` 夾具重複房間宣告,維護成本高
7. **GEO-020** 負值像素捨入——拖曳參考線到視圖負值區仍有 1mm 偏移
8. **GEO-035** `WM_CREATE` 控制項 NULL 防護
9. **GEO-081** scene parser fuzz——延續既有 128 測試 + 40 變異測試的品質文化
10. **GEO-053** 檔頭功能清單更新——完全沒提 room/space/grid/RC/delete/apply-proj

### 建議標作廢(已不適用,且是被後續設計**刻意取代**,不是忘了做)

GEO-001、004、018、022、023、052、070、072。
例:GEO-022「跨角材拾取取最近者」已被公理 **R1 畫家演算法**取代;
GEO-023「錨點加已過期標記」已被 **R2 重放/重算**結構性解決;
GEO-018「scene 格式文件」已由 `公理層.md`(SSOT)承載。

### 稽核過程發現、BACKLOG 沒寫的缺口

1. BACKLOG 開頭的工單統計數字錯誤(46 vs 實際 52)。
2. 全檔 **0 處**使用 C `assert()`,但 3 張工單的驗收條件明寫要加 assert——制度與實作風格對不上。
3. `guide_line_intersection` / `ANCHOR_AT_GUIDES` / `at-guides` 整條「兩線交點錨點」**疑似死碼**
   (該函式全檔僅一處定義、未被呼叫),GEO-123 已廢除 `at-guides` 語法卻沒有工單追蹤該砍還是該修。
4. 第 3 流(GDI/Win32 互動層)**完全沒有自動化回歸測試覆蓋**,卻是七張裡六張未完成的高風險區。
5. `current_geometry.c` 檔頭沒有像 `ARCHITECTURE.md` 那樣自曝「已過時」。

### 逐張表格

> 稽核方法：唯讀比對 repo 實況（current_geometry.c 用 Python 二進位解碼；當時檔內仍有 NUL byte，2026-09-21 起已無，CRLF 仍在）、
> tests/run_tests.py、AGENTS.md/ARCHITECTURE.md/公理層.md、geometry-web/、geometry-guide/。
> 未編譯、未跑測試。current_geometry.c 全檔 0 處使用 C `assert()`——凡工單驗收條件明寫「加 assert」
> 但實作用註解/return false 達成同等效果者，仍記已完成，於理由欄註明。

## 第 0 流：基礎設施

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-001 | 已不適用 | 無 build.bat/build_debug.bat；tests/_clw.bat:1-3、package.json:6-7 | 建置已演化為 gcc(Unix)+ tests/_clw.bat/_cl.bat 參數化 cl 編譯（多檔架構：current_geometry.c/web_bridge.c/model_base.c），非單一 exe 的 root build.bat 設計 |
| GEO-002 | 已完成 | tests/run_tests.py:1-90+ | 完整測試執行器，比對 exit code/stdout/lengths/contains，收錄遠超原始需求的案例數 |
| GEO-003 | 已完成 | tests/run_tests.py:26-27（ceiling-a.scene / demo-two-timbers.scene 皆 expect accept） | 兩檔都已改新語法並通過 |
| GEO-004 | 已不適用 | 無 README-geometry.md；tests/README.md:1-40、ARCHITECTURE.md、geometry-core/README.md | 單檔 CLI 說明文件的前提已不成立，build/test/使用說明改分散到多個 README，系統已是多元件（core/web/GDI） |

## 第 1 流：解析層與輸入面

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-010 | 已完成 | current_geometry.c:43-47(COORD_LIMIT/coord_in_range), 6051-6064(parse_coord) | 上限 ±1e8 mm，parse_coord 檢查並設 g_coord_range_error |
| GEO-011 | 已完成 | current_geometry.c:2467-2486(mul_div_i64) | 用 __int128（gcc/clang）或 _mul128/_div128（MSVC）widen 乘法，註解寫明安全域推導，比原案的 assert 更徹底 |
| GEO-012 | 已完成 | current_geometry.c:11713-11722 | fgets 後檢查 `length>0 && 非\n && !feof` 才判太長，避免誤殺合法末行 |
| GEO-013 | 已完成 | current_geometry.c:3579(SCENE_MAX_LINE=2048), 11709 | buffer 遠大於原 511 字元邊界，與 GEO-012 同一段邏輯處理 |
| GEO-014 | 未完成 | current_geometry.c:11726-11732 | BOM 檢查仍只判 `line_no==1`，未檢查 `length>=3` 就讀 text[1]/text[2]，未初始化記憶體讀取風險依舊（C6387 模式未消） |
| GEO-015 | 未完成 | current_geometry.c:11813-11838(main argv 迴圈) | 迴圈只有 if/else if 四支，無 else 分支：未知參數被靜默忽略，無 --help |
| GEO-016 | 未完成 | current_geometry.c:11836 | `bench_iters = atoi(argv[++i]);` 仍用 atoi，無型別/範圍驗證 |
| GEO-017 | 已完成 | current_geometry.c:11683-11686 | 「不認得的指令」錯誤訊息硬編列出 11 個指令名（非動態拉表，但達成驗收：訊息含全部指令） |
| GEO-018 | 已不適用 | 全庫無 SCENE-FORMAT.md；公理層.md「新語法」節、geometry-core/README.md | scene 語法規格已改由 公理層.md（SSOT）承載，且語法已演化（spec/at-line/at-face/role/between 等），與原案設想的靜態文件形式不同 |

## 第 2 流：幾何核心正確性

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-020 | 未完成 | current_geometry.c:4710-4711 | gdi_screen_to_view 仍用 `(Coord)(v+0.5)`，非 floor/llround，負值捨入偏移問題依舊 |
| GEO-021 | 已完成 | current_geometry.c:3083-3087, 3107-3111 | det==0 語意已寫成註解（表面退化成線 / 答案非整數 mm 兩種拒絕情形），全檔不用 assert 是專案風格 |
| GEO-022 | 已不適用 | current_geometry.c:3223-3278（尤 3267-3278），公理 R1 註解 | 命中判定已正式定為「畫家演算法：同點多命中取最後畫的」（公理 R1），非原案建議的 distance4 最近者方案——是刻意的設計決定，取代而非達成原 ticket |
| GEO-023 | 已不適用 | current_geometry.c:3600-3614, 11915-11921；公理層.md:104(D7 不存凍結 uv), 428(R2) | 錨點系統改為引用制，移動參考線會重放（重算）所引用的角材（R2，2026-09-18 拍板），結構性解決比「印已過期標記」更徹底；僅 ANCHOR_AT_GUIDES 一種錨法仍標「交點凍結」屬另一個獨立設計決定 |
| GEO-024 | 未完成 | current_geometry.c:1230-1246（guide_line_intersection 全檔僅此一處，且未被任何函式呼叫） | 仍只靠 placement_id 比對間接拒絕跨面組合，無「參考線不在指定面上」專屬訊息；且此函式疑似死碼，舊 at-guides 兩線交點錨點路徑現況不明（見缺口 3） |
| GEO-025 | 已完成 | current_geometry.c:2580-2583, 2615 | timber_project_faces 註解已寫明退化面跳過策略、繪製與拾取共用同一份投影 |
| GEO-026 | 已完成 | current_geometry.c:1078-1086（`>=`/`<=`允許邊界值） | offset 允許與邊界重合，決定已正式收錄為公理 I7（比原案設想的 SCENE-FORMAT.md 記錄更正式） |

## 第 3 流：GDI / Win32 層

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-030 | ✅ 已完成(2026-09-21) | current_geometry.c `gdi_text` | 失敗時不換字型,也不拿 NULL 去還原 |
| GEO-031 | 未完成 | current_geometry.c:4013-4018 | gdi_color 未檢查 `hex[0]=='#'`或長度，直接 `strtoul(hex+1,...)` |
| GEO-032 | 未完成 | current_geometry.c:5824-5847 | bench_paint 的 sink/sink_bmp 建立失敗分支仍未釋放已取得的 screen DC |
| GEO-033 | 未完成 | current_geometry.c:4721, 5216-5217 | g_edit_orig_proc 仍是全域 WNDPROC，未改 SetWindowSubclass 或存於視窗自身 |
| GEO-034 | 無法判定 | current_geometry.c:4149-4155（owned 欄位行內註解） | 只有一行「true=未進快取用完要刪」的行內註解，未見整理成完整所有權表，也無 assert，證據不足以判定達成或未達成 |
| GEO-035 | ✅ 已完成(2026-09-21) | current_geometry.c `WM_CREATE` | 五個控制項任一為 NULL 即回傳 -1,讓視窗開不起來而不是半套 |
| GEO-036 | 未完成 | current_geometry.c:4745-4764（gdi_layout_input_bar） | 視窗極小時 `w-176` 等寬度運算無下限防禦，MoveWindow 可能收到負寬 |

## 第 4 流：房間（room→space）功能收尾

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-040 | 已完成 | room_box.scene（檔案存在）；tests/run_tests.py:29 | 六面盒範例檔存在且已收錄於測試 |
| GEO-041 | 未完成 | current_geometry.c:11208-11213（apply_space_line） | space_construct 失敗仍只回一句把六種原因全部列出的通用訊息，未分類 |
| GEO-042 | 未完成 | 全檔搜尋「房外面」「歸屬」皆無關聯命中 | 找不到 space 成員歸屬合理性警告的任何字串或邏輯 |
| GEO-043 | 未完成 | current_geometry.c:11898-11912 | 空間報告只印 ID/成員/開放狀態，無尺寸（W×D×H）或質心 |

> 註：room 概念已整體演化為 Space（`room_bind`→`space_construct`，current_geometry.c:6299-6302 註解「與舊 room_bind 同構」），GEO-040/041/042/043 的評估對象已改為 Space 等價功能。

## 第 5 流：文件與導讀同步

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-050 | 已完成 | geometry-guide/check_panels.py:92-112 | check_panels.py 機制已整個改寫為動態讀 HTML `data-panel` 屬性比對，原 ticket 描述的硬編字串比對缺陷已不存在 |
| GEO-051 | 已完成（部分無法完全確認） | geometry-guide/current_geometry-導讀.html（內嵌原始碼含 canvas-pos/apply-proj/space_construct 等最新符號） | 導讀頁持續與原始碼同步；但原案要求的「§room 章節」因 room 已改名 Space，是否有對應章節未能直接確認 |
| GEO-052 | 已不適用 | 全庫搜尋無 asm-analysis.md | 檔案不存在，組譯附錄式文件已被 公理層.md/ARCHITECTURE.md/geometry-core 系列文件取代 |
| GEO-053 | 未完成 | current_geometry.c:14-37（檔頭「目前整合版」清單） | 仍停在原始 8 步，未提及 room/space/grid/RC/delete/apply-proj 等後續功能，與 ARCHITECTURE.md 自陳「已過時」呼應（但 ARCHITECTURE.md 至少自曝過時，檔頭沒有） |

## 第 6 流：程式碼衛生

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-060 | 已完成 | current_geometry.c:1（僅1處 #include <errno.h>）, 10946/11479（(void)count） | 重複 include 已消除、count 參數消警告模式已見；未實際編譯確認 0 警告 |
| GEO-061 | 已完成 | tests/_clw.bat:3, geometry-web/build.bat:4 | 編譯腳本皆帶 `/utf-8` |
| GEO-062 | 未完成 | current_geometry.c:3502-3553（emit_svg_three_views） | 僅檢查 `fclose(out)==0`，無 ferror 檢查，也未刪除半成品 SVG |
| GEO-063 | 未完成 | current_geometry.c:3532-3533 等（text_mm 共5處） | StyleSpec 欄位仍叫 text_mm，未更名 text_px |

## 第 7 流：新功能

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-070 | 已不適用 | SCENE_COMMANDS（current_geometry.c:11553-11649）無 unplace | 被 delete + 重宣告的交易式工作流取代（見 GEO-071） |
| GEO-071 | 已完成 | current_geometry.c:11634-11638；BACKLOG.md「WEB-001 ✅ 已完成」段 | delete 指令存在，涵蓋 boundary/placement/guide/grid/timber/space/column/beam，走交易重驗路徑，比原案墓碑方案更完整 |
| GEO-072 | 已不適用 | tests/run_tests.py（`_test_collide.scene` expect reject error 'R6'） | 碰撞已由「警告」升級為公理 R6 直接拒絕，比原案更嚴格的設計決定 |
| GEO-073 | 已完成 | 公理層.md「新語法」表；current_geometry.c:11584-11586 | guide 位置引用式支援 edge:/spec:/vertex:/grid: 等任意運算組合，涵蓋且超越原案的 edge 基準語法糖 |
| GEO-074 | 未完成 | current_geometry.c:1790/6443/7957（函式名仍為 timber_place_a0_on_surface） | 仍硬綁 A0 面貼面，找不到 B0 貼面或 face 欄位的證據 |
| GEO-075 | ✅ 已完成(2026-09-21) | current_geometry.c `print_cut_list()` | 2026-09-21 補做:同規格加總 + 房間內部尺寸,驗收已進 run_tests |
| GEO-076 | 未完成 | current_geometry.c:5436-5600（WM_MOUSEMOVE） | 找不到滑鼠即時 mm 座標寫進狀態列的邏輯 |
| GEO-077 | 未完成 | current_geometry.c:11553-11649（SCENE_COMMANDS 無 include） | scene 檔案引入/分段語法未實作 |
| GEO-078 | 已完成 | geometry-web/web_bridge.c:4,15,30,117 | 提供完整 stdin/stdout JSON 橋，涵蓋且遠超原案的單次 --emit-json 輸出 |

## 第 8 流：結構演化

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-080 | 已完成 | tests/test_core_integrity.c:1-20（`#define main geometry_program_main` + `#include "../current_geometry.c"`） | 機制不同於原案 CG_NO_MAIN ifdef，但同樣達成「直接呼叫內部 static 函式並斷言」的目標 |
| GEO-081 | 未完成 | tests 目錄檔案列表（無 fuzz_scene.py） | tests/mutate.py 是變異測試（改程式碼），非輸入層 fuzz（隨機 token/截斷），目的不同 |
| GEO-082 | 未完成 | 全庫搜尋無 split-plan.md | 拆檔計畫文件未寫；專案已用 .inc（transactions.inc/references.inc 等）局部拆分，但無明文計畫 |
| GEO-083 | 未完成 | tests/_clw.bat、tests/_cl.bat、geometry-web/build.bat 全文 | 找不到 /analyze 或 /RTC1 相關建置腳本 |

---

## 統計

- 已完成：19（002,003,010,011,012,013,017,021,025,026,040,050,051,060,061,071,073,078,080）
- 未完成：24（014,015,016,020,024,030,031,032,033,035,036,041,042,043,053,062,063,074,075,076,077,081,082,083）
- 已不適用：8（001,004,018,022,023,052,070,072）
- 無法判定：1（034）
- 合計：52（BACKLOG 自稱 46，數字有誤）

## 建議施工優先序（真的還沒做、現在仍值得做）

1. **GEO-075** 下料清單加總——專案的實際用途是木作施工，逐支列印座標但不加總同規格數量，是離「能拿去現場用」最近的一步。
2. **GEO-043** Space 尺寸/體積報告——六面封閉都判出來了卻不印房間淨尺寸 W×D×H，基本實用資訊缺口。
3. **GEO-030** CreateFontW 失敗未判 NULL——GDI 互動視窗的真實當機風險，修法只要加一個 if。
4. **GEO-014** BOM 檢查補 length>=3——一行修法即可消除讀未初始化記憶體的隱患，CP 值最高。
5. **GEO-041** Space 錯誤訊息分類——六種失敗擠成一句話，且現在的 Space 比舊 room 更複雜，除錯需求更高。
6. **GEO-077** scene include——上百個 `.scene` 夾具有大量重複房間宣告，include 能顯著降低維護成本。
7. **GEO-020** 負值像素捨入——拖曳參考線到視圖負值區時仍有 1mm 偏移，互動正確性問題。
8. **GEO-035** WM_CREATE 控制項 NULL 防護——控制項建立失敗會對 NULL HWND 呼叫 API 的當機風險。
9. **GEO-081** scene parser fuzz——專案已有 128 項測試+40 個變異測試的品質文化，補上輸入層 fuzz 是自然延伸。
10. **GEO-053** 檔頭功能清單更新——完全沒提 room/space/grid/RC/delete/apply-proj，對新進 agent/讀者高度誤導。

## 建議標記作廢（已不適用）

- GEO-001（build.bat）——建置架構已演化為多檔 gcc/cl 參數化編譯。
- GEO-004（README-geometry.md）——單檔 CLI 說明前提不成立，文件已分散且更完整。
- GEO-018（SCENE-FORMAT.md）——已被 公理層.md 取代為 SSOT。
- GEO-022（distance4 最近拾取）——已被公理 R1「畫家演算法」取代，是刻意設計決定。
- GEO-023（過期錨點標記）——已被 R2「移動即重放」結構性解法取代。
- GEO-052（asm-analysis.md 標版本）——檔案已不存在，組譯附錄形式已被淘汰。
- GEO-070（unplace 指令）——已被 delete+重宣告工作流取代。
- GEO-072（碰撞警告）——已被公理 R6 硬性拒絕取代，比原案更嚴格。

## 盤點過程中發現的缺口（BACKLOG 沒寫，明顯該補）

1. **BACKLOG 自身統計數字錯誤**：統計行自稱「總數 46 張」，實際逐行數到 52 張（010~018 是 9 張不是想像中的較少、070~078 是 9 張等）——連審計基準點本身都不可靠，應先修統計行再談別的。
2. **assert() 制度與實作風格根本不合**：全檔 0 處使用 C `assert()`，但 GEO-011/021/034 三張工單的驗收條件都明寫「加 assert」——應該是工單描述過時要改，而不是繼續期待有人去補從未出現過的模式。
3. **`guide_line_intersection`／ANCHOR_AT_GUIDES／at-guides 整條「兩線交點錨點」路徑疑似死碼**：函式定義了但全檔無人呼叫，卻仍在 AnchorKind enum 與報告文字（「參考線交點」）中占一席之地——沒有工單記錄這條路徑該砍還是該修，文件（GEO-024）、實作（死碼）、印出邏輯三者對不上。
4. **第 3 流（GDI/Win32 互動層，GEO-030~036）完全沒有自動化回歸測試覆蓋**：tests/run_tests.py 全部跑 `--no-window`；七張工單裡六張未完成，卻是全專案唯一「改壞了不會被測試網接住」的模組，風險遠高於其他流，應優先建立至少手動驗收清單或有限度的 GDI 煙霧測試。
5. **current_geometry.c 檔頭注解沒有「已過時」自我標記**：ARCHITECTURE.md 已經在檔頭加警語承認過時並指向 公理層.md，但 current_geometry.c 自己的檔頭（GEO-053 想修的那段）完全沒有類似警語，對照專案「SSOT 優先、過時文件要自曝」的紀律不一致。

### GEO-150 ✅ 已做（2026-09-20）專案清理：移除失去依據的設計原型、給第二支產生器上閘門
- **起因**:使用者問「公理層閱讀器是唯一的嗎」。實地掃描結果:**是唯一的**——
  全 repo 15 個 `.html` 裡,只有 `geometry-guide/公理層-閱讀器.html` 含 `clause-data`/`axiom-review-data`;
  無 `dist/`、無離線版、無 `.bak`、無手機版分身。但掃出三個鬆動處,使用者指示「一併處理,我要乾淨的專案」。
- **移除 `geometry-guide/axiom-reader-design/`**(38 檔、21MB,占當時 repo 36%):
  第 3 版 React 設計原型,它服務的 `閱讀器-設計規格.md` 同日整份作廢,於是失去依據。
  **完整內容仍在 git 歷史**,考古用 `git show`,不要 checkout 回工作區。repo 58MB → 35MB。
- **`make_axiom_reader.py` 加寫檔閘門**:它產的是追溯診斷頁不是正典,但一跑就會在 repo 生出
  第二份像閱讀器的檔案。文字規則擋不住誤跑,改成機制——預設寫系統暫存目錄;
  `--in-repo` 才寫進 repo,且**正典存在時一律拒絕**並要求改用 `sync_axiom_reader.py`。實測拒絕成功。
- **清掉本機殘留**:`verify-GEO-137/`(前一個 agent 的 GEO-137 目視驗收產物)、`current_geometry.svg`、
  `current_geometry.obj`、兩個 `__pycache__/`。這些因為 `.gitignore` 是允許清單制而被歸為 ignored,
  **不會出現在 `git status`**——所以先前的「工作目錄乾淨」是假的。
  另停掉三支前一個 session 遺留的 `python -m http.server`(8765/8766/8791),其中一支卡住
  `verify-GEO-137/` 使其無法刪除。
- **連帶更新**:`AGENTS.md`、`CLAUDE.md` 改寫對應段落;`決策佇列.md` 新增 Q7
  (`make_axiom_reader.py` 714 行要留還是刪,與 `axiom_matrix.py` 功能重疊)。
- **驗收**:`test_axiom_reader` 12 項、`witness --check` 17/17、`test_witness_marks` 4 項、
  五道 assert 全綠;ignored 殘留只剩 `.claude/`(本機設定,正常)。

**GEO-138 實作紀錄(2026-09-20)**:右欄插入 `#workspace-witness`,位置在 `#dock-hub` 與
`.workspace-tabs` 之間——**上半固定見證圖、下半才是分頁**(🔒 Q4)。
圖直接取自條文卡裡那張的 `src`(同一個 data URI),**不另存第二份**,所以不增加檔案大小。
掛在 `sync()` 本來就會派發的 `axiom:current` 事件上,不必改 `sync()`。
只在 `min-width:1280px` 出現;窄螢幕維持卡片內 inline(拍板的第四點)。
實測 1440px:I13 顯示見證圖(13.7KB data URI)、D1 無圖時顯示「這一條沒有見證圖(89 條中有 17 條有)」,
右欄子元素順序 `dock-hub → workspace-witness → workspace-tabs → workspace-panels`。

### GEO-151 ✅ 已做（2026-09-21）補丁登記簿：讓「補丁被靜默跳過」變成不可能

- **起因**：使用者指出我反覆弄壞東西，而且「已經習慣了」。這不是偶發，是方法問題。
- **實際發生過的失效**（2026-09-20/21 一天之內四次，全在 repo 檔案上）：
  1. CSS 注入的守衛字串與實際插入的內容對不上 → 每重建一次就再插一次（踩兩次：GEO-147、GEO-139）。
  2. 保留歷史範例的切片終點沒涵蓋新區塊 → 見證圖 17→33、三向連結 89→136。
  3. `force()` 把 `changeMode()` 裡同形的尾巴誤判成「已套用」→ **補丁整個被跳過，沒有任何人會知道**。
  4. 同一段被兩個補丁先後修改 → 第二個把第一個的「改後」改掉，重建時兩邊都認不得。
- **根因**：補丁是對一份**會演化的產物**做文字替換，而「有沒有套用過」是用改前/改後的樣子判定的。
  被改的內容自己一變，判定就失效。我反應式地補了 `force()` 四次（唯一性、追加式、刪除式、已套用標記），
  每次都在下一個變體上再被咬一次——**補洞的速度追不上洞的產生速度**。
- **真正的問題不是「會壞」，是「壞得無聲」**：冪等檢查只說「結果不對」，不說「哪一個補丁失效」。
  四次裡有三次靠冪等檢查接住，第三次（靜默跳過）靠人眼才發現。
- **做法**：`PatchLog` 登記簿。每個補丁在套用時登記一個「套用後一定看得到／一定看不到」的標記，
  `rebuild()` 結束時一次驗完，失效時**指名是哪一個補丁**。
  `force()`（四條路徑）與 `inject_css()` 自動登記；兩處移除式改寫（見證圖面板、色彩 token）手動登記。
  目前一次同步登記 **99 個補丁**，`validate()` 的報告帶上 `"patches": 99`。
- **語意刻意選成「驗結果，不驗有沒有跑」**：冪等重跑時補丁本來就該跳過，那不是錯誤；
  錯的是「該在的東西不在」。
- **突變驗證**（兩段，第一段是反例）：
  1. 只讓 `inject_css` 靜默跳過 → **不報錯**。正確：正典裡本來就有那段 CSS，結果是對的。
  2. 同時把那段 CSS 從正典拿掉（忠於史實：內容不在了而補丁又被跳過）→
     報 `同步套用了 99 個補丁，其中 1 個沒有生效`，並指名
     `補丁「CSS .toc-facets{display:flex」套用後應該看得到的內容不見了`。
- **測試**：`test_axiom_reader.py::test_every_patch_actually_lands`（登記數 > 50 且驗證為空）。
- **未涵蓋（誠實標記）**：`--check` 模式不跑 `rebuild()`，登記簿是空的，所以那條路徑仍只靠既有的
  五道 assert 與各功能的防回歸檢查。要涵蓋就得把標記清單寫進產物，目前判斷不值得。
- **另一類錯，不在本票**：我在寫補丁腳本時三次用 Bash heredoc 包含跳脫字元的 Python，
  把 `\r\n` 寫成真的換行而弄壞腳本。那壞的是暫存腳本、不是 repo，但同樣是明知故犯。
  處置：這個 repo 的 `current_geometry.c` 是統一 CRLF 且被 `AGENTS.md` 列為地雷，
  **補丁腳本一律用檔案寫入工具產生，不用 heredoc**。

### GEO-152 ✅ 已做（2026-09-21）篩選 chip 的數字在第一次建置後就凍結了

- **怎麼被抓到**:做 GEO-041/043 時在 `current_geometry.c` 的註解裡引用了 I4、I33、D1、D5,
  `axiom_matrix` 抓到後有一條從「無追溯」變成「有追溯」——
  `test_facet_chips_are_data_driven` 立刻報 `22 != 21`。
- **根因**:`apply_facets()` 用 `force(template, anchor, anchor + markup, ...)` 插 chip,
  而 markup 裡有**算出來的數字**。force() 的「已套用」判定看到 `anchor + 舊 markup` 還在就返回,
  數字從此凍結在第一次建置的值。GEO-149 交付時只驗了第一次建置,所以當下是對的。
- **修法**:先用正則移除既有的 `<nav class="toc-facets">`,再插入當前版本
  (與見證圖面板、色彩 token 同一個處置)。
- **一般規則**(已寫進 `AGENTS.md`):**凡是內容會隨資料變的標記,一律「先移除再插入」,
  不得用 force() 的改前/改後判定**——那個判定只看「形狀在不在」,看不出「內容過期了」。
- **登記簿為什麼沒抓到**:`PatchLog` 驗的是「標記存不存在」,而標記確實存在(只是數字舊了)。
  這是登記簿設計上的已知邊界:它擋「補丁沒生效」,擋不住「補丁生效了但內容過期」。
  後者要靠針對資料一致性的測試——`test_facet_chips_are_data_driven` 正是這種測試,而它做到了。
- **我的流程錯誤**:這次我在 `test_axiom_reader` 報 FAILED 的情況下仍然先 commit 了
  (a3d5a69),修正在後一個 commit。正確做法是測試不綠就不 commit。

**GEO-030 / GEO-035 實作紀錄(2026-09-21)**

- **GEO-030**:`CreateFontW` 失敗時原本直接 `SelectObject(g->dc, font)`——傳 NULL 是錯誤呼叫、
  回傳 NULL,接著又拿這個 NULL 去「還原」,等於**把 DC 的字型狀態弄壞**,之後每一次畫字都受影響。
  改成:失敗就不換字型,用 DC 現有的字型把字畫出來;還原時也先判 NULL。
- **GEO-035**:五個控制項任一建不起來就回傳 -1 讓 `WM_CREATE` 失敗。
  原本不檢查,於是對 NULL HWND 呼叫 `WM_SETFONT` 與 `SetWindowLongPtrW`(靜默失敗),
  接著 `gdi_layout_input_bar()` 對 NULL 呼叫 `MoveWindow`,狀態列也再也更新不了——
  **視窗看起來開著,其實是壞的**。呼叫端本來就有 `if (window == NULL) return false;`,
  所以回傳 -1 是現成的退路。順帶把兩個按鈕的 handle 存下來,不再用 `GetDlgItem` 取。
- **⚠ 驗證限制(誠實標記)**:這兩張都在 `#ifdef _WIN32` 區塊內。
  `tests/_clw.bat` 沒有 `/U_WIN32`,所以**有被編譯、有過型別檢查**;
  但第 3 流(GDI/Win32 互動層)**完全沒有自動化回歸測試**(稽核缺口 4),
  我無法在這裡證明「字型建立失敗時畫面仍正確」或「控制項建不起來時視窗確實開不起來」——
  那需要在真實視窗下製造資源耗盡。**兩者都只驗到「程式碼正確」,沒驗到「行為正確」。**

---

## 外部審查(codex)報的四個問題 — GEO-153～156(2026-09-21)

四條全部**確認屬實**,全部修好,**每一條都做過突變測試**
(把修正拿掉、測試必紅;不只是「修完測試是綠的」)。

### GEO-153 ✅ 已做(2026-09-21)P1:CRLF 讓建模功能整個失效

- **現象**:Windows 上每一次建模都被擋成 `UNSUPPORTED / AXIOM_VERSION / I32`
  「Axiom source changed without a corresponding executor version」。
- **根因**:`AXIOM_SHA256` 是在 **LF bytes** 上算出來的,而 `公理層.md` 在 git 裡存 LF、
  `.gitattributes` **沒有**把它標成 `-text`(`current_geometry.c` 與見證 SVG 都有),
  所以 Windows 簽出來是 CRLF。`_axiom_hash()` 直接雜湊原始 bytes,於是**必然**對不上——
  不是機率問題。實測:工作區 620 CRLF / 0 lone LF,實際 `3092f91f…`,期待 `6958a10c…`,
  而**把 CRLF 正規化成 LF 後的雜湊恰好等於 `6958a10c…`**,反證那個常數的來歷。
- **修法**:雜湊前先 `raw.replace(b"\r\n", b"\n")`,與 `geometry-guide/witness.py::_sha`
  同一個判斷——行尾是簽出方式,不是內容。這也是 manifest 的 `axiom_sha256` 能跨平台同值的前提,
  否則「可重現的建模套件」根本不成立。常數不用動,`geometry-core/examples/*.model.json`
  裡的既有 golden 完全不受影響。
- **沒有改 `.gitattributes`**:標成 `-text` 只治新的 clone,治不了既有工作區,而且正規化之後它是多餘的。
- **端到端重現與驗證**:本機沒有 gcc 系編譯器,`BASE_COMPILER` 會比公理閘門**先**擋下來,
  整套測試的數字因此不會動——這代表端到端測不出修好沒有。改用 MSVC 編一支
  `geometry-core/model_base.c` 當 `GEOMETRY_MODEL_BASE` 之後:
  **修正前 `FAILED (errors=24)`,24 個全是 `AXIOM_VERSION`、0 個 `BASE_COMPILER`
  ——與外部審查報的「24 個錯誤」完全一致;修正後 39/39 通過。**
- **測試**:`test_modeling_runtime.py::AxiomSourceIdentity` 三條,刻意**不經過** `build_package`,
  沒有編譯器的機器也跑得動:(1) 雜湊等於常數;(2) 同一份條文的 LF 與 CRLF 兩種簽出得到同值;
  (3) **真的改一個字仍然要擋**——正規化不得把閘門關掉。
  另把 `test_modeling_runtime` 原本自己算的那個 oracle 抽成 `axiom_digest()` 並同樣正規化;
  它本來也內建了同一個錯誤假設。

### GEO-154 ✅ 已做(2026-09-21)P2:上傳失敗會毀掉還活著的場景

- **現象**:`/upload` 的新檔載入失敗後,畫面上還是舊場景,但「重新載入場景」從此壞掉。
- **根因**:順序反了。`serve.py` 先寫新暫存 → **刪光 `_upload_temps`** → 才
  `ask_bridge("loadfile …")`。而 bridge 的 `cmd_loadfile` 是**交易式**的
  (失敗時 `g_world = before`),所以舊場景確實還活著——活著,但來源檔已經沒了,
  前端 `curScene` 指向一個已刪的路徑。
- **修法**:**先載,成功了才動舊暫存**。失敗時反過來刪掉載不起來的那個新檔,
  並且不把 `path` 塞進回應(不得讓前端改指到一個沒載進去的檔)。
- **測試**:`test_serve.py::test_failed_upload_keeps_the_live_scene_reloadable`,
  三步:成功上傳 → 失敗上傳 → 再成功上傳,逐步檢查 `_upload_temps` 與檔案是否存在。
- **突變驗證**:把 `serve.py` 還原成 HEAD → `AssertionError: False is not true : 還活著的場景的來源檔被刪了`。
  (第一版測試的斷言順序讓它停在症狀 `'path' unexpectedly found` 上,已把最能指認病因的那條排到最前面。)

### GEO-155 ✅ 已做(2026-09-21)P2:批註合併漏擋「同一份備份內部」的同 ID

- **根因**:`known = {x["id"]: x for x in state[field]}` 在迴圈**外**建一次,append 時不更新,
  所以剛收下的紀錄對後面的紀錄是隱形的。同一份備份裡兩筆同 ID 異內容會**兩筆都被收下**。
- **為什麼五道 assert 攔不住**:那五道驗的是版面完整性,不檢查批註集合的 ID 唯一性。
- **修法**:append 之後補 `known[value["id"]] = value`。一行。
- **測試**:兩條。(1) 同 ID 異內容必須丟 `Conflicting review record`;
  (2) 一字不差的重複只是冗餘、不是衝突,但**只能收一次**。
- **突變驗證**:拿掉那一行 → 第一條 `ValueError not raised`,第二條 `2 != 1`
  ——後者正是那個靜默重複。

### GEO-156 ✅ 已做(2026-09-21)P2:newid 可能發出已被占用的 id

- **根因**:`cmd_newid()` 的 `max + 1` 在 uint32 上界回繞成 0。原本**只有 datum**
  有碰撞迴圈(那段註解寫著 "Overflow must not overwrite id 0"),其餘八種是裸 `+ 1`。
- **比原報告更精確的定性**:後果分兩種。
  `guide` / `grid` 的 id 0 **合法**,所以 newid 發出一個已存在的 id,畫布拿去宣告
  = I8 交易式重宣告 = **覆寫既有物件**;`surface` / `timber` / `column` 的 id 0 會被核心擋掉,
  症狀變成「新物件建不出來」。兩種都是錯的。
- **實測**:場景同時有 `guide 0`(位置 300)與 `guide 4294967295`(位置 2900)時,
  **載入合法**,而 `newid` 回 `"guide":0`。修正後回 `"guide":1`。
- **修法**:抽出 `WORLD_NEXT_ID(out, array, count)` 巨集,九種一致處理:
  從 `max + 1` 起找第一個沒被占用的 id。候選 count+1 個且兩兩相異、被占用的只有 count 個,
  所以迴圈必定找得到空位(終止性有證明,不是靠經驗)。
- **測試**:`test_bridge_integrity.py::test_newid_never_hands_out_an_id_already_in_use`。
- **突變驗證**:還原成 HEAD 重編 → `AssertionError: 0 unexpectedly found in {0, 4294967295}`。

### 回歸狀態(2026-09-21)

全綠:`run_tests.py` 131/131、`test_core_integrity` 80/80、`witness --check` 17/17、
`test_axiom_reader` 24、`test_bridge_integrity` 10、`test_serve` 9、`test_reference_contract` 25、
`test_datum_contract` 9、`test_modeling_runtime` 39(需 `GEOMETRY_MODEL_BASE`)。

**跑不動(誠實標記)**:`test_modeling_transport` 在 `setUpClass` 就寫死 `cc -std=c11 … -o`
去編 `web_bridge.c`,沒有環境變數可覆寫,本機沒有 gcc 系編譯器所以整組跳過。
查過了,它**沒有**碰 `/upload` 或 `newid`,所以這四張票的涵蓋沒有因此缺口;
但「Windows 上跑不動的測試檔」本身是既有問題,另開票。

### GEO-157 ✅ 已做(2026-09-21)P2:畫布自己湊 surface id,仍會覆寫既有物件

外部審查(codex)在 GEO-156 之後的追加回報,兩處都確認屬實。

- **背景**:`surface N` 是「boundary N + placement N」**合體一行**,所以它要的 id
  必須在**兩個** id 空間裡都是空的。`newid` 只保證各類別各自空。
- **兩個現場**:
  - `geometry-web/app.js` `emitNewSurface()`:`Math.max(ids.boundary, ids.placement)`。
  - `geometry-web/app.js` `submitBox6()`:`b0 = Math.max(...)` 之後 `b0+1 … b0+5` 連續加號。
- **為什麼以前「看起來」沒事,現在才浮出來**:沒有回繞時 `newid` 的兩個值都**大於**
  各自類別的所有既有 id,所以 max 與其後的加號也都大於全部——湊得出來是巧合,不是保證。
  **GEO-156 把回繞修掉之後,`newid` 會回小號碼**,這個巧合就不成立了。
  也就是說:上一張票修好了「發出去的 id」,卻讓「拿它做算術」這件事第一次真的咬人。
- **後果是靜默覆寫,不是報錯**:`surface` 對既有 id 是 I8 交易式重宣告。實測
  (真實瀏覽器、真實 `submitBox6`):世界 boundary {0,1,2,5,MAX}、placement {MAX} 時,
  舊碼用掉 3,4,5,6,7,8,既有的 `boundary 5 outline 0,0 90,0 90,90 0,90` 被換成
  `outline 0,0 4000,0 4000,2500 0,2500`,而狀態列顯示 **「✓ 六面盒空間 1(6 面含地板)」**。
  使用者看到的是成功訊息。
- **另一種症狀**:在別的世界裡整批會被 `history-abort` 回滾,變成「六面盒建不出來」。
  我第一次選的重現世界就是這種,**差點據此下結論說「舊碼沒事」**——是去看實際 dump
  才發現狀態列那句 ✓ 是上一次成功留下的殘影。教訓:狀態列不是證據,dump 才是。
- **修法(把不變式放回有資料的那一側)**:`newid [n]` 新增 `"surfaces": [n 個 id]`,
  每個都在 boundary 與 placement 兩邊都空、且彼此相異;n 預設 1,範圍 1..16,
  不合法一律 `ok:false` 且不回半套。既有的九個純量欄位**一個都沒動**(向後相容,
  `canvas_test.js` 既有案例不受影響)。畫布改用 `ids.surfaces[0]` 與 `newid 6`,
  六面盒的槽位維持 `[0]` 天花 / `[1]` 地板 / `[2..5]` 牆,所以「有沒有地板」
  不會改變牆的編號(保留原行為)。
- **順帶確認的兩件事實**:`surface 4294967300`(超出 uint32)是**被拒絕**不是回繞;
  `surface` 撞到既有 id 一律回 `ok:true` 並覆寫。
- **測試**(三層):
  1. `tests/test_bridge_integrity.py::test_newid_surface_ids_are_free_in_both_id_spaces`
     ——六個 id 兩邊都空且互異,並斷言舊算法在這個夾具裡**確實**會撞上(夾具保有牙齒)。
  2. 同檔 `::test_newid_rejects_a_count_it_cannot_honour`——數量邊界。
  3. `geometry-web/cdp_test.js` BF4「六面盒不覆寫既有面(GEO-157)」
     ——**唯一真的跑 app.js 的 harness**(headless Chrome 點 `box6Submit`)。
- **突變驗證**:
  - 橋接器:拿掉 `surface_id_taken()` 裡的 placement 檢查 → `0 unexpectedly found in {0, 4294967295}`。
  - 畫布:把 `app.js` 換回修正前 → cdp_test 報 `{"kept":false,"faces":10} ✗`
    (既有面被毀、面數少一),其餘 273 條照樣綠——這條測試精準指向缺陷。
- **回歸**:cdp_test **274 ✓ / 0 ✗**、canvas_test **412 pass / 0 fail**,
  其餘全套見下。

#### GEO-157 追加修正：回繞時排除保留編號 0（2026-09-21）

- 複查發現：只有 `surface 4294967295`、且 0 尚未占用時，`newid 6` 會回傳
  `[0,1,2,3,4,5]`。D4 規定 `boundary_id=0` 表示使用自帶矩形，不能拿來建立
  引用同號邊界面的合體 `surface`；實際新增面／六面盒會失敗並回滾。
- `next_surface_ids()` 每次檢查候選前都跳過 0，包含第一個候選、同批後續候選
  及避開既有編號途中發生的回繞；仍避開 boundary、placement 及本批已選編號。
- 新增橋接器回歸案例：上界／上界前一號 × 單面／六面 × 小編號空閒／已占用，
  共 8 種情況；不只檢查回傳編號，也實際建立每個面並確認原有定義保留。
  修正前可重現保留編號 0 被發出；修正後整組 bridge 測試 13 項通過。
- 新增 CDP 案例：在只有最大編號面的世界，實際點六面盒建立按鈕，檢查原面保留、
  面數增加至 7，且新增 1 個封閉空間；完整瀏覽器檢查 **275 ✓ / 0 ✗**。
- 驗證環境：MSVC 編譯成功，但新執行檔遭 Windows Smart App Control 封鎖；
  改由既有 WSL/GCC 執行核心測試，瀏覽器仍使用 Windows Chrome，不更動安全設定。

### 回歸狀態(2026-09-21,GEO-157 後、追加修正前)

場景 131/131、integrity 80/80、witness 17/17、閱讀器 24、bridge 12、serve 9、
reference 25、datum 9、modeling runtime 39(需 `GEOMETRY_MODEL_BASE`)、
canvas_test 412/0、cdp_test 274/0。

---

## 全專案複查(2026-09-21)— GEO-158～162

起因:使用者要求「重新檢查整個專案一遍」。我把專案切成五塊派對抗審查,
再把診斷整理成交叉確認單交給另一組 agent 獨立查證。**九條裡七條成立**,
其中一條是 P1(資料遺失)。下面每一條都經過:我自己重現 → 修 → 突變測試 → 交叉確認。

### 交叉確認改正了我四個說法(誠實記錄)

1. **「空間從封閉退化成部分」不是回繞造成的**——對照組也是「部分」,那是 split 本身。
   可歸因於回繞的證據是**重複 ID 與重載掉面**,不是封閉狀態。
2. **`column 0` / `beam 0` 是可用的**。我原本標「無結論」,對方在游離世界與完整封閉房間
   都建成功了,0 與 77 兩組皆過且存檔重載逐字一致。我的無結論來自**我建的世界本身足跡越界**,
   對照組跟著失敗——這正是「對照組也失敗就不能下結論」的用處。
3. **GDI 不是死碼**。靜態呼叫鏈:矩形/多邊形選單 → WM_COMMAND → WM_LBUTTONDOWN/UP →
   `gdi_canvas_down/up` → `canvas_emit_new_surface` → `canvas_next_id`。它會發出 `surface 0`;
   但**不能**把投影路徑「追加重複 ID 並掉面」的後果不加區分地套到 GDI。
4. **我說「沒有任何夾具使用接近 UINT32_MAX」是錯的**。既有 bridge 測試早就在用 4294967295
   (參考線回繞、surface 跨命名空間、範圍測試)。真正的缺口是**投影配號、純 boundary 配號、
   loadfile/歷史群組組合**這三處。

### GEO-158 ✅ 已做 P1:核心配號器回繞 → 重複 id → 存檔重載掉面

- `current_geometry.c:10489` `proj_next_surface_id()` 與 `:4816` `canvas_next_id()` 都是裸
  `max + 1`,註解寫「避免碰撞」但回繞之後並不避免。
- 實測(同一場景只差第六個面的編號):對照組 `1,2,3,4,5,6,7,8`;
  上界組 `1,2,3,4,5,MAX,0,0`。兩者 rc 都是 0、零錯誤訊息。
- **真正的傷害是往返**:dump 出兩行 `boundary 0`,再 `loadfile` 時後者靜默蓋掉前者,
  **少一個面**,而兩次載入都回 `ok:true`。
- 另一半是 `0` 本身:D4 用 `boundary_id == 0` 表示「不掛邊界面、自帶矩形」,
  所以 `surface 0` 建不起來。
- 修法:抽 `world_next_surface_id()`——從 max+1 起找第一個「兩邊都沒占用且非 0」的 id,
  任何一輪回繞到 0 都跳過;配不到回 0 當失敗哨兵。五個呼叫點全部加檢查。
- 測試 `test_projection_split_ids_survive_a_save_and_reload`(帶對照組);
  突變:還原成修正前 → `8 != 7 : boundary 出現重複 id`,且**只有上界那組紅**。
- 副作用:新註解引用了 D4 → 追溯矩陣多一個 code site → 正典必須重建。
  這是設計中的警報,不是誤報。

### GEO-159 ✅ 已做 P2:`newid.boundary` 會發出 D4 的保留值 0

- `boundary 0` 建得起來,但 `placement N on boundary 0` **永遠**被拒。
  `app.js:3469` `objEmitFace()` 直接用這個欄位 → 使用者拿到成功訊息和一個死面。
- 當時只驗到 boundary 需要跳過 0;後續 GEO-164 證實 space 也有游離柱樑哨兵衝突,
  已補上 space 的配號與明寫引用檢查。其餘類別仍允許 0。
- 測試不只看數字,而是拿發出來的 id 真的建面再掛承載面;並用 `boundary 0` 當對照
  證明斷言有牙齒。

### GEO-160 ✅ 已做 P2:`loadfile` 跨過未關閉的歷史交易

- `g_hist_grouping` / `g_hist_group_base` 是行程層全域,不在 `World` 裡,
  `cmd_loadfile` 的 World 快照救不到。群組還開著而 base 停在載入前的世界,
  之後 `history-end` 把舊世界推進 undo 疊——**按一次 undo,loadfile 與其後所有編輯一起消失**。
  **成功路徑也會踩到。** undo 後果由交叉確認實跑證實(我原本只有讀碼推論)。
- 照 `undo`/`redo` 的既有慣例一律拒絕。只拒絕、不自動中止群組:不靜默丟掉做到一半的編輯;
  `history-abort` 冪等且永遠回 ok,恢復路徑一直都在。

### GEO-161 ✅ 已做 P2:診斷頁的寫檔閘門被 `--out` 繞過

- `make_axiom_reader.py` 的 `resolve_out()`:`--out` 分支在閘門**之前**就 return,
  閘門只掛在 `--in-repo` 上。`--out <正典>` 與 `--in-repo --out <正典>` 都能覆寫唯一正典。
  檔頭宣稱「文字規則擋不住誤跑,所以改成機制」——那個機制有洞。
- 改成所有路徑都過同一道 `guard()`,用 `realpath` 比對,相對路徑與 `..` 都擋得住。
- 驗證只 import 後直接呼叫 `resolve_out()`,**沒有執行 main()、沒有碰正典**。

### GEO-162 ✅ 已做 P3:四處文件失真 + 契約與實作矛盾 + 兩處措辭過頭

- **NUL 地雷已失真**(`CLAUDE.md`、`AGENTS.md`、`BACKLOG.md`、`witness/交接-GEO-137.md`):
  現檔 NUL=0。`7f94145` 當時是 4——**寫下時是真的**,檔案後來改動後消失,四處都沒跟上。
  **CRLF 那半仍然成立**,所以是改寫不是刪除。
- **`AGENTS.md` 引用 `公理層.md:319` 行號錯**:該行是 I11,正確位置是 614。
- **`MODELING-CONTRACT.md:79` 與實作矛盾**:契約寫「UTF-8 原始 bytes」,
  實作(GEO-153 之後)是先 CRLF→LF 正規化。**是我 GEO-153 只改程式沒回補契約**,
  下游照契約字面實作會永遠對不上。
- **`--check` 的能力被我講過頭了**:交叉確認指出 `--check` 的介面本來就是「驗現有產物」,
  而且他們在記憶體跑 rebuild,99 個補丁全過、輸出逐位元相等——**管線是健康的**。
  問題只在 AGENTS.md 把三條指令並列卻沒說各驗各的。已改寫成明講
  「`--check` 綠燈不代表整條管線健康」並說明 `patches: 0` 的來由。
- **SAC 的措辭過頭**:我原本寫「等一下再啟動一次就好」,交叉確認指出**不保證**放行,
  他們就是持續被擋才改走 WSL/GCC。已改成「通常…但不保證」,並要求把
  「環境阻擋」與「程式失敗」分開記錄。

### GEO-163 ✅ 已做(🔒 2026-09-21 拍板選項 B)P2:解析器層拒絕保留的 boundary id 0

- **決定**(使用者拍板,決策佇列 Q9):只在**邊界面的 id 空間**就地拒絕,
  不動 `公理層.md`(那是選項 C),也不動其餘八類。
- **擋三個入口**,共用同一句話(`RESERVED_BOUNDARY_ID` 巨集),免得同一條規則
  在不同指令下講出不一樣的理由:
  - `boundary 0 …`(宣告)
  - `surface 0 … outline …`(合體宣告,**只在真的宣告 boundary 時**)
  - `placement N on boundary 0`(明寫的引用)
- **刻意不擋**:沒有 outline 的 `surface 0` 等同純 placement,0 對它合法,
  現在合法、以後也要合法。測試有專門一條守這件事。
- **修掉的是答非所問**:
  - `surface 0 … outline …` 原本回「重宣告後有物件失效」——而它其實是**首次宣告**。
  - `placement N on boundary 0` 原本回「不掛邊界面的承載面需要 rect」——
    使用者明明寫了 `on`,卻被當成「沒寫 on」的預設值。
- **測試**:`test_reserved_boundary_id_zero_is_refused_with_a_useful_message`,
  每條都帶對照組(換成非 0 的 id 必須成功,否則是指令寫錯不是 0 的問題)。
  突變:還原成修正前 → 3 個失敗,訊息正是那句「不掛邊界面的承載面需要 rect」。
- **連帶改到的既有測試**:GEO-159 的對照組原本寫「`boundary 0` 建得起來但掛不上
  承載面」,GEO-163 之後變成建都建不起來,前提跟著改寫(**改前提,不是刪斷言**)。
- 正典閱讀器一併重建:`apply_boundary_line` 現在實作 D4 的哨兵規則,
  追溯矩陣多一個 code site(D4 共 4 個)。99 補丁全過、五道 assert pass、
  `documentHash` 不變。

### GEO-164 ✅ 已做 P2:空間配號與明寫引用誤用游離柱樑的保留值 0

- `newid.space` 在 uint32 上界回繞後會發出 0。`space 0` 建立成功,但
  `column/beam ... in 0` 被當成游離物件,省略高度會失敗,明寫高度則繞過空間範圍檢查;
  存檔也不保留 `in 0`。這與 I17 的 `space_id=0` 游離標記衝突。
- 配號跳過 0 與既有編號;解析器在 `space 0`、`column ... in 0`、`beam ... in 0`
  三個入口明確拒絕,共用保留值訊息。游離柱樑省略 `in` 的寫法、柱樑本身 id 0、
  刪除空間後柱樑游離均保留。未修改 `公理層.md`。
- 新增三項橋接測試:回繞後實際建立柱樑、推導高度、拒絕越界、存檔重載;
  保留值的指令與檔案載入均拒絕且不改世界;合法游離物件與刪空間行為不回歸。
  舊版二進位重現 8 個失敗子案例,新版 20 項橋接完整性測試全過。
- 瀏覽器測試另實際按「六面盒」,確認已有空間 1 與最大編號時新建空間為 2,
  兩個既有空間均保留。

### GEO-165 ✅ 已做 P2:依既有 Q7 決策退役舊診斷頁產生器

- GEO-161 只擋住正典的精確路徑;`--out geometry-guide/公理層-追溯診斷頁.html`
  仍能繞過 `--in-repo` 的限制,在專案裡產生第二份閱讀頁。
- 依 Q7 已拍板的「下次壞掉或再造成困擾時就刪,不必搶救」移除
  `geometry-guide/make_axiom_reader.py`,同步更新 AGENTS、CLAUDE 與建置說明。
  Git 歷史保留舊工具;目前程式無匯入依賴,追溯診斷仍由 `axiom_matrix.py` 提供。
- 正典同步器重建完成(99 補丁、五道 assert 全過),內容與原正典相同;
  `--check` 與 24 項閱讀器測試通過,條文、批註及例圖均保留。

### GEO-166 ✅ 已做 P2:瀏覽器碰撞測試的過期夾具

- GEO-163 拒絕 `boundary 0` 後,BF4 仍拿它當前置物件且忽略失敗回應,
  導致預期 11 面、實得 10 面的假性失敗。
- 改用合法 boundary 9,保留舊配號算法仍會覆寫 boundary 5 的碰撞條件;
  reset 與每筆夾具建立都檢查成功,失敗即中止並指明指令,不再悄悄少建物件。
- 最終完整 Chrome 操作驗證 **276 通過 / 0 失敗**,含上述兩個編號回繞案例,未捕捉例外為 0。
  同輪橋接完整性 20/20、引用契約 25/25、基準線契約 9/9、C 核心 80/80、
  場景 131/131、正典閱讀器 24/24 全過。由當前原始碼以 WSL/GCC 重新編譯,
  Windows Chrome 實際操作;未執行新 Windows exe,不更動系統安全設定。
  測試產物與記錄在 `%TEMP%/geometry-tests/fix-164-166/`,截圖未寫入專案。

### 我沒有涵蓋的

解析器對畸形輸入的完整 fuzz;`geometry.py` 三角化的退化輸入(孔與外環共邊、自交、零厚度)。
交叉確認那一輪也同樣沒涵蓋。

### GEO-167 ✅ 已做(2026-09-21)P3:兩筆 🔒 追認 + 三處懸空引用

**交叉確認的產物**。GEO-164/165 由另一個 agent(codex)完成後,我做了一輪獨立覆驗:
突變測試證實新檢查有牙齒(關掉三處 `space_id == 0` → 測試紅 6 個),
並獨立重跑 cdp_test 得到 **276 ✓ / 0 ✗**(原本那個數字只有實作者自己的 log)。
剩下兩類問題不在程式碼,在流程與紀錄:

**兩筆 🔒 追認**(使用者 2026-09-21 補認可):
- **GEO-164 擴大了 Q9 的範圍**。Q9 原文明寫「**不動其餘八類**」,而 `space` 正是其中之一。
  擴大的理由成立——我當初那份 id 0 普查只問「建不建得起來、引不引用得到」,
  漏問「這個值在別處是不是已經有意義」,所以 Q9 就 `space` 而言是建立在不完整的證據上。
  但 🔒 的意義就是不得由 agent 自行延伸,**正確順序是先回到決策佇列問**。
- **GEO-165 自行判定了 Q7 的退役觸發條件**。「何時算壞掉」是判斷,不是事實。
  觸發條件本身經複驗成立(見下),但當時是 agent 自己認定的。
- 兩筆都已寫進 `決策佇列.md`,並標明「事後追認」與流程註記——**不粉飾成當時就授權**。

**三處懸空引用**(追溯門檻的出處):
- `geometry-guide/sync_axiom_reader.py:59`、`:1121`、`tests/test_axiom_reader.py:215`
  都引用 `make_axiom_reader.py:431-433`,而該檔已於 GEO-165 刪除。
  GEO-165 的條目只說「無匯入依賴」,沒盤到這三處註解;第三處是對抗審查找出來的。
- **複查發現行號在刪檔之前就已經過期**:HEAD(`1498bc4`)版的定義實際在 **464-466** 行,
  差了三十幾行。也就是說這個引用鏈斷過兩次,只是第一次沒人發現。
- 修法不是換個行號了事,而是**把判準本身寫進註解**
  (綠 = 原始碼且夾具、黃 = 其一、紅 = 皆無;樞紐 = 被引用數 >= 3),
  再附 `git show 1498bc4:…` 當考古入口。這樣即使 commit 參照再腐爛,判準也還在。

**順帶記下我自己在 GEO-163 犯的錯**(由 codex 抓到,我已實測坐實):
GEO-163 開始拒絕 `boundary 0` 之後,我自己寫的 cdp BF4 夾具就壞了——它拿 `boundary 0`
當前置物件,而且**忽略每一行的回應**,於是只建出 4 個面而非 5 個,
`faces === 11` 的斷言實得 10,**必定失敗**。我沒抓到,是因為**提交 GEO-163 時沒有重跑 cdp_test**
(回歸清單裡漏了它)。那個壞掉的測試跟著 commit `1498bc4` 推上了 main。
codex 的修法比我原本的嚴格:換成合法的 `boundary 9`,並給每條前置加
`if (result?.ok !== true) throw`,以後不可能再靜默建出錯的世界。
**教訓:動到解析器的接受/拒絕行為時,cdp_test 一定要跑**——它是唯一真的執行 `app.js` 的 harness。

### GEO-168 ✅ 已做(🔒 2026-09-21 授權)P2:I19 外輪廓邊那一款的理由不合物理

**起因**:使用者從物理機制反推條文:「未被固定的角材端面無法直接固定在 RC 面上;
被固定的角材端面也無法;但它已經固定了,所以端面有沒有頂到 RC 都不影響它已經固定;
未被固定的角材自然不是結構的一部分。」四句我用 physical-reasoning 跑過,四句都對,
工法知識也印證:壁邊材靠側面釘牆、主骨靠吊筋、副骨由主骨承托——**沒有任何一根是靠端面固定的**。

**問題**:I19 那一款的理由寫「外圍那圈是邊界材釘在 RC 上的位置,主支不直接觸牆」,
把「端面接觸」和「固定」混在一起。邊界材靠**側面**固定沒錯,但拿它解釋
「主支的**端面**不可頂牆」接不上——端面本來就不提供固定,頂不頂牆與固定無關。
同一個因果錯位也在 D15 的物理意義(「連續的邊界材釘在 RC 上(I19 因此另立一款…)」)。

**真正的不變式**:主支端面頂到外輪廓邊 ⟺ 那條邊還沒鋪邊界材 ⟺ 板靠牆的邊無骨可釘
(封板每條邊都要落在角材上)。邊界材鋪了,主支端面幾何上只會頂到它的側面。
所以 I19 那一款是在放置當下擋「邊界材漏鋪」,規則的**機制是對的,理由是錯位的**。

**改了什麼**(規則一字未動,只換理由):
- `公理層.md` D15 物理意義、I19 那一款的理由、孔邊例外的理由(改成「貼邊料角色由宣告決定,
  沒有先鋪邊界材的義務」,對齊 I21)
- `公理層-白話.md` I19
- `current_geometry.c:7447` 的註解(錯誤訊息不動——它陳述的是規則)
  **→ 2026-09-22 續:訊息也改了**,見本段末。
- `AXIOM_SHA256` 隨條文更新;正典閱讀器重建,textRevision r9 → r10

**也改了**:R19(d) 與白話的「層級 2 停在它下面」→「層級 2 的端面頂在它的側面」。
我先看成層級用語想保留,使用者指示一併修正:平釘是共平面,「停在下面」容易被讀成空間上下層,
而幾何上唯一正確的描述就是「端面頂在側面」。

**Q11 已拍板(🔒 2026-09-21)**:**不另立**全域「覆蓋」不變式,維持現狀。
世界是逐支放置的,全域不變式會在鋪第一根主支前就擋掉一切;I19 現行做法是正確的懶惰檢查。
要在更早時點整體驗「板邊無骨可釘」的話,另開票、另立時點明確的檢查,不改 I19。

**順帶修了一個測試 bug**:`test_counts_have_a_single_source` 用純子字串找鬼影「文字 r1」,
textRevision 走到 r10 之後它變成真值的子字串而誤判。改成帶數字邊界的比對,
「1 / 63」對「11 / 63」的同類隱患一併免疫。**這是 textRevision 第一次跨到兩位數,
那個測試從 2026-09-20 寫下時就埋著這顆雷。**

**追溯副作用**:C 註解新引用 I20/I21 → `timber_end_face_check` 成為它們的 code site。準確。

**回歸**:場景 131/131、integrity 80/80、witness 17/17、bridge 20、reference 25、datum 9、
serve 9、witness marks 4、modeling 39(新雜湊)、reader 24、sync --check 五道 assert pass。

**後續(下一個 commit)**:`AXIOM_REVISION` 依慣例指向改條文的那個 commit;
`geometry-core/examples/*.model.json` 內嵌的 axiom_sha256/axiom_revision 重產
(用 `modeling_cli.py example …`,幾何雜湊不應變)。

**方法論教訓(記進 memory)**:我查 M23 時一路在推程式碼邏輯,沒先問「這條規則的物理理由
站不站得住」——順序反了。使用者的做法是對的:**先從物理機制反推,再看條文和程式有沒有跟上**。

**續(2026-09-22)**:錯誤訊息從「只有 boundary 可頂 RC」改成「**那條邊還沒鋪邊界材**;只有 boundary 可頂 RC」——
講出使用者該做的事(先鋪邊界材),規則保留在後半;`run_tests.py` 三個夾具比對的前綴「端面頂到外輪廓邊(RC)」不變。
函式頂註解 `:7379` 也還寫著舊理由「邊界材是 RC 錨定層」,一併改成新說法。
全套件重跑:run_tests 132、integrity 80、witness 17、bridge 20、reference 25、datum 9、serve 9、transport 2、
marks 4、reader 24、modeling 63、sync --check pass。

### GEO-171 ✅ 已做(2026-09-21)P3:四筆小債——文件失真、transport 跑不動、mutate.py 撞檔、規格檔殘留

**`ARCHITECTURE.md:170`**:表格列了 `asm-analysis.md`,全庫 git log 查無此檔——**從未進版控**
(root `.gitignore` 是允許清單制,它不在清單)。改成明標不存在 + 取代它的三份文件 + GEO-052 考古線索。
整份 `ARCHITECTURE.md` 開頭自承過時,**不重寫**。

**`tests/test_modeling_transport.py`**:`setUpClass` 寫死 `cc`,Windows 整組爆。改成:有 `GEOMETRY_TEST_BRIDGE`
就直接用預編 bridge、不編;沒有就維持 `cc`;`cc` 不存在 → `SkipTest`(原本是 `FileNotFoundError` 炸掉)。
**第一次在 Windows 真的跑起來,掀出三件事**:
- `KeyError: 'derived'` 與 CLI 的 `BASE_COMPILER`——**不是 bug**,是子行程(serve.py / modeling_cli)
  也需要 `GEOMETRY_MODEL_BASE`;兩個變數都給就 `Ran 2 tests … OK`。已寫進 AGENTS.md。
- `tearDownClass` 用 `signal.SIGINT`,Windows 拋 `ValueError: Unsupported signal: 2` → service 沒關 →
  `service.log` 被佔住 → 暫存目錄清不掉,**每跑一次漏一個 serve.py 行程**(實際抓到三個,已清)。
  Windows 改 `terminate()`,其他平台不變。

**`tests/mutate.py`**:原本所有變異都編到 repo 內同一個 `tests/_mut.exe`——SAC 會擋 repo 目錄的新 exe,
而且兩個 agent 平行跑必撞。改成每變異一個 `%TEMP%` 子目錄放 exe;`.c` 留在 repo 根目錄
(`current_geometry.c` 的 `#include "geometry-core/…"` 以被包含檔所在目錄解析,搬去 `%TEMP%` 找不到),
獨立檔名、gitignore 忽略、編完即刪;`cl` 參數改 argv 分開傳(塞成一個字串時 `%~1` 剝不掉引號——
第一版就是這樣失敗的,錯誤訊息裡檔名連引號都算進去);`MUTATE_RESULTS` 可改結果檔路徑避免平行競態;
SAC 擋住時重試之間等 12 秒。煙霧測試:M02(先前 killed)→ 仍 **killed**,exe 落在 `%TEMP%`、
根目錄無殘留、repo 的 `mutants_results.json` 未被動到。

**`geometry-guide/閱讀器-設計規格.md`**:CLAUDE.md 早寫「作廢/移除」、檔頭自承整份作廢,檔案卻還在
(2026-09-21 文件稽核抓到的失真)。`git rm`,`sync --check` 五道 assert 仍 pass;AGENTS/CLAUDE 措辭對齊。

### GEO-170 ✅ 已做(2026-09-21)P2:建模引擎的退化幾何輸入——未發現違規

**新增** `tests/test_modeling_degenerate.py`(24 個測試,`DegenerateGeometryAcceptance`),由 agent 建立、
我 read-back 驗證:24 OK、每個測試都有斷言、0 個 expectedFailure / skip、oracle 與雜湊比對都用上。

**裁判**(每個輸入只允許兩種結果,第三種即違規):
(甲)明確 `ModelError` 帶非空 `code`/`clause`;(乙)package 通過 `test_modeling_runtime` 既有的
`assert_mesh`/`assert_package` oracle 且兩次建置 `geometry_sha256` 一致。

**實測結果**:
- 甲(被拒):孔邊共線相接、孔頂點落外環邊上、孔共用外環頂點、孔等於外環、孔在外環外、孔跨出外環、
  兩孔相接、兩孔重疊、孔含孔、外環自交(8 字)、相鄰/非相鄰重複頂點、座標超 `COORD_LIMIT`——
  這些**全部在 C 場景解析層**(`boundary_is_valid` / `poly_loop_is_valid`)就被擋下,Python 引擎根本收不到。
  另兩個在 `geometry.py` 層拒:擠出零厚度/負厚度(`NON_POSITIVE_SPAN`/I26)、跨距超 D1 範圍(`COORD_RANGE`/I26)。
- 乙(合法):共線多餘頂點、逆向繞向、座標貼近 D1 極限(體積 24 位大整數以字串精確表示)、座標恰等於 `COORD_LIMIT`。

**結論**:退化幾何在**進入 Python 引擎之前**就被 C 解析層的 `boundary_is_valid` 統一擋掉,
引擎自己只需要守厚度與座標範圍——分層是對的,沒有漏。這跟 GEO-172 對 M23 的實測互相印證:
「孔貼輪廓 / 兩孔相接」在核心層不合法,是同一道閘門。

**環境**:需 `GEOMETRY_MODEL_BASE`(本機無 gcc,否則每案都撞 `BASE_COMPILER`);與 runtime 合跑 63 OK。

### GEO-173 ✅ 已做(2026-09-22)P3:M01 / M56 判定為等價變異

由 agent 依「**先問物理 → 追程式路徑 → 原始版與變異版同夾具逐字比對**」的順序做,全程不碰 repo;
我 read-back:兩個夾具在原始版與變異版下輸出**逐字相同**,`world_validate_derived` 的呼叫順序也核對過。

**M01**(`poly_point_on_edge` 直立邊端點 含 → 嚴格):物理情境是角材/孔的角對角相碰。
變異只動**直立邊分支**;軸平行多邊形的任一頂點必同時是一條直立邊與一條水平邊的端點,
未變異的水平邊分支一定接住。**等價**,與 2026-09-16 稽核(BACKLOG:454)一致——這次是獨立重推同一結論。

**M56**(`world_validate_derived` I23(b)):物理情境是網格引用被錨定後面縮小、索引不再推導得出。
- 既有 `_ax_r13_anchor_*` 為何殺不掉:它們**零 timber**,M56 所在迴圈根本沒執行——不是被擋,是沒觸發。
- 真正的原因:`world_validate_derived`(8355)只在 `reference_rebuild`(8335)成功後才跑,而
  `reference_rebuild` 對每個 AT_GRID 角材已先跑同一個 `grid_line_coord`,索引消失會先在那裡失敗。
  被變異那行在現行語意下**永遠是 no-op**。**等價**。
- **這推翻了 GEO-100(2026-09-16)的「非等效、未覆蓋缺口」結論**。舊結論在當時是對的:
  那時 R6(e)/I23 是「凍結」語意,邊界材縮面會先出界(I5)蓋過此路徑;2026-09-18 反轉為「重算」後
  邊界材能自動重推長度,不再出界,擋下來的變成 `reference_rebuild` 的同款檢查。
  舊文字保留、加更正註記(BACKLOG:649、:896),不刪——當時的判斷有它的脈絡。

**處置**:兩個都在 `tests/mutate.py` 標記 `equivalent=`(附理由),`mutate.py` 對它們不編不跑、
verdict 記 `equivalent`。`mutants_results.json` 同步。**硬湊夾具去殺等價變異只會寫出假測試。**

**教訓**:「survived」有兩種——測試缺口,或**等價變異**。分不清就會追一個殺不掉的東西。
判別法就是 D 用的:同一夾具、原始版與變異版逐字比對;相同就去找「哪一道更早的檢查把它遮掉了」。

### GEO-172 ✅ 已做(2026-09-22)P2:M10 殺掉、M23 / M09 判等價——五個 survived 全部收斂

**結果**:`mutants_results.json` 從「43 killed / 5 survived」變成「**44 killed / 4 equivalent / 0 survived**」。
沒有一個是硬湊夾具去殺的;等價的四個都有「原始版與變異版同夾具逐字相同」的實證。

**M10**(`:690` 孔頂點嚴格在矩形內 `>` → `>=`)——**killed**。
新夾具 `_ax_i5_hole_vertex_touches_rect_edge.scene`:角材矩形 u∈[230,350]、v∈[250,330];
L 形孔的一個頂點 (320,250) 恰好落在角材上邊 v=250,而孔的 bbox 與角材真的重疊(所以 `:682` 快退不觸發)。
原始版接受(`L=120`);變異版把「頂點在邊上」算成相交而拒絕。正確答案是接受——
註解明寫「孔邊上接觸允許:角材可以貼著柱面走」。**難點在於要讓 bbox 重疊但孔本體只用一個頂點碰到**,
所以孔得是 L 形。`run_tests.py` 132/132。

**M09**(`:682` bbox 快退 `<=` → `<`)——**等價**。造了 U 軸相切、V 軸相切、對角相切、以及 M10 夾具本身
四組場景,原始版與 `mutants\M09\_mut.exe` 的 stdout+stderr **位元組級逐字相同**。
理由:相切只表示邊界重合、孔本體不在矩形內,快退跳過與細查三道(頂點嚴格在內/邊穿內部/孔罩矩形)殊途同歸。

**M23**(`:7884` 跨距起點 `hits > 1`)——**等價**。四類「兩個邊類擋面同座標」的組合用目前 core.exe 重跑:
孔貼輪廓 → I2 拒絕;兩孔共邊/共角 → I2 拒絕(分開才接受);任一為角材側面 → `stop_face_shadowed` 只留一個;
同一簡單多邊形兩邊同座標又涵蓋同段 → 強行構造即自交被拒。該分支在合法輸入下不可達。
(這條的物理面見 GEO-168 那輪的討論:擋面必須涵蓋角材全寬,兩個都全寬就代表兩側都是實體,角材放不進去。)

**機制**:`tests/mutate.py` 新增 `equivalent="<理由>"` 標記——有理由的變異不編不跑,verdict 記 `equivalent`,
摘要多一欄「等價」。標記由指揮官依證據填,agent 只回報理由。
survived 有兩種:測試缺口、或等價變異;分不清就會追一個殺不掉的東西。判別法是同夾具兩版逐字比對。

**環境**(同 GEO-171):每個變異都是新二進位,SAC 可能擋第一次;腳本重試並把「受阻」與「killed」分開。

### GEO-169 ✅ 已做(2026-09-22)P2:場景解析器的畸形輸入 fuzz——確定性、可重播、自動縮小

**新增** `tests/fuzz_scene.py`(agent 建立,我 read-back)。語料是根目錄 131 個合法夾具,22 種位元組層變形
(刪/插/換 token、數值邊界、截斷、超長 token/行、空白、編碼雜訊、指令大小寫、未知指令、重複欄位);
每個案例只是 (seed, index) 的函式,所以 `--replay N` / `--shrink N` 不必重跑前面。
每案例用一支**全新** bridge.exe(約 12ms):agent 實測「單一常駐行程 + reset」**不可重現**——
reset 清不掉 `g_input_line_no` 等行程層全域,案例之間互相污染,同 seed 兩次結果會漂。

**四條裁判**:(1) 不崩潰、回應與指令數對齊;(2) 交易性:ok:false 之後 dump 逐字不變;
(3) 往返:dump → 存檔 → loadfile → dump 逐字相同;(4) 拒絕有理由:error 非空、非亂碼。

**修正前第一次跑**(seed 1、500 案例):460 違規 / 232 案例——類 1=4、類 2=0、類 3=228、類 4=228。
歸納只有**兩個根因**(→ GEO-174):(a) 宣告了但沒 place 的角材,dump 後 loadfile 回 `error:""`;
(b) `js_string` 不驗 UTF-8,壞位元組與截斷剩下的半個字直接進 JSON。三次同 seed 逐字相同。

**裁判收窄兩處**(理由寫在檔頭):類 3 只放過「dump 裡真有未 place 的角材 **且** error 說的正是沒有 place」——
那是 I9 收尾檢查在條文要求下的拒絕,不是往返 bug(I9/R4 張力 → 決策佇列 **Q12**,2026-09-24 🔒 維持現狀);
類 4 在輸入那一行本身不是合法 UTF-8 時允許 U+FFFD(那是 GEO-174 的正確行為)。

**修正後**:seed 1 500 案例 0 違規;換 seed 2 又抓到 1 個(案例 301,名字夾壞位元組進了世界 → GEO-174 第 4 點,
先修前三點才浮得出來);四點都修完,seed 1 / 2 / 3 各 500 案例 **0 違規**,同 seed 兩次除耗時行外逐字相同。
22 種變形每種 33–60 案例。
**用法**:`GEOMETRY_TEST_BRIDGE=%TEMP%\geometry-tests\bridge.exe python tests/fuzz_scene.py --seed 1 --cases 500`;
產物在 `%TEMP%\fuzz-findings\`(REPORT.md + 最小重現)。不進 CI:每案例都要起行程,500 案例約 1 分鐘。

### GEO-174 ✅ 已做(2026-09-22)P2:fuzz 找到的四個缺口——loadfile 拒絕沒理由、JSON 吐無效 UTF-8、截斷切在字元中間、壞位元組進世界

四個都**先寫回歸測試、對舊 bridge.exe 跑紅**(2 FAIL + 2 UnicodeDecodeError),再修、再綠。
`tests/test_bridge_integrity.py` 20 → 24(新增位元組層的 `bridge_bytes()` 幫手)。

1. **loadfile 回 `error:""`**:`parse_scene_file` 收尾的未放置檢查(I9)只 `fprintf(stderr)`,沒寫 `g_scene_last_error`;
   bridge 的 `cmd_loadfile` 只拿得到緩衝。修:另記緩衝「角材 N 沒有 place(收尾時仍未放置,I9)」;
   stderr 原句不動(命令列使用者與 `_ax_i9_orphan_timber` 夾具都靠它)。世界不動已驗(前後 dump 相同)。
2. **無效 UTF-8 進 JSON**:`web_bridge.c` 的 `js_string` 原樣吐位元組。輸入夾壞位元組(fuzz 會,複製貼上也會)→
   I8a 預覽的 `command` 欄回顯 → 整條 JSON 壞,`serve.py:235` 的 `resp.decode("utf-8")` 直接炸。
   修:輸出層驗 UTF-8(`utf8_seq_len`,含過長編碼 / UTF-16 代理對 / 超過 U+10FFFF),無效序列逐位元組換 `\ufffd`——
   標出來、不吞掉;合法序列原樣通過。
3. **截斷切半個字**:`reference_issue` 的 `%.190s`、`references.inc` 的 `%.120s`、各 256 位元組緩衝都是**位元組**截斷;
   **完全合法**的 44 字中文規格名就會讓錯誤訊息尾巴剩 `\xe6\xb8`(手動重現,不靠 fuzz)。
   修:`utf8_trim_tail()`(current_geometry.c,`set_revalidate_error` 之前)在 `scene_error` / `set_revalidate_error` /
   `reference_issue`(msg 與 e->actual)/ `%.120s` 之後各套一次;訊息最多少最後一個字,不會壞。中段壞位元組交給第 2 點。
4. **名字夾壞位元組進了世界**(seed 2 案例 301,前三點修完再跑才浮出來):`spec 主支2中<0xFF 0xFE>線 1500` 回 ok:true,
   名字帶著壞位元組進世界,`cmd_dump` 用自己的跳脫迴圈(不是 `js_string`)原樣吐出 → 整條 JSON 壞。
   **在輸入層擋**:場景 DSL 是 UTF-8 文字格式,`parse_scene_file` 與 bridge `feed_line` 一行不是合法 UTF-8 就拒絕
   「這一行含無效的 UTF-8 位元組」、世界不動。只靠輸出層換 U+FFFD 不行——畫布看到的名字會跟世界裡的位元組
   不一樣,存回去就對不上(R4)。`utf8_seq_len` / `utf8_is_valid` 移進 current_geometry.c 供兩邊共用;
   `cmd_dump` 改走 `js_string_body`(同一道輸出檢查,防線不留單點)。這是實作層的格式規定,不是條文;若要入條文另開票。

**沒做、也不該在這裡做**:互動世界含未 place 角材的 dump 不能用 loadfile 載回——那是 I9 的要求不是 bug;
要不要放寬是條文問題,入決策佇列 **Q12**(2026-09-24 🔒 維持現狀)。

全套件:run_tests 132、integrity 80、witness 17、bridge 24、reference 25、datum 9、serve 9、transport 2、marks 4、
reader 24、modeling 63、sync --check pass;fuzz seed 1 / 2 / 3 各 500 案例 0 違規。

### GEO-175 ✅ 已做(2026-09-24)P3:導讀頁 `current_geometry-導讀.html` 自 2026-09-18 起未重產,callout 已飄

**修法**(只動 `make_guide.py` 的三個面板與緊鄰的一句 prose,重產 HTML):
- §8 `main：放置角材` → `main：場景來源——場景檔或內建預設`:`main` 已不自己放角材(改呼叫 `parse_scene_file` 或
  `reference_default_world`),舊的 `SURFACE_DIRECTION_POS_U,` / `SURFACE_DEPTH_POSITIVE_NORMAL` 已不在 `main` 裡。
- §10 SCENE_COMMANDS:`"place", 8, 16, true,`(錨法改成 at-line / at-face + through / between)、
  `"move", 3, SCENE_MAX_TOKENS, true,`(新位置是引用式)。
- §10 `apply_place_line` 現在是一行轉交 `apply_reference_place`(`references.inc`);單行函式本體 `{ … }` 不是獨立的 `{` 行,
  `findFunction` 會一路抓到下一個函式(舊報告的 9696–9737 其實是 `world_drop_canvas_pos`)。改用 `kind:"range"` 以
  `from`/`to` 圈出 place/span-auto/move 三個轉交函式。
- 重產:`core.exe --no-window --out current_geometry.svg`(先重編 core,舊 exe 比最後一次 C 修改早)→ `make_guide.py`
  → `check_panels.py`:**40 面板,unresolved: none**。headless Chrome 實際開頁:40 面板每個的高亮行數 = callout 數,無「找不到」。
- **守門**:新增 `tests/test_guide_panels.py`(跑 `check_panels.py`);對舊 HTML 跑紅、重產後綠。

- 順手改正 §10 一句與 SSOT 正面衝突的 prose:「移動參考線**不會**讓角材跟著走」→ 依公理層 R2(2026-09-18 反轉)改為「**要**重放」。

**範圍外、另開 GEO-182**:導讀頁的 prose(不是 callout)仍停在舊語法,check_panels 驗不到。

### GEO-182 ✅ 已做(2026-09-25)P3:導讀頁 prose 仍描述 2026-09-12 時代的語法與結構

GEO-175 修完 callout 後發現:`check_panels.py` 只驗面板符號與 callout,**不驗說明文字**。`make_guide.py` 的 prose 仍有:
§10 標題「七個指令」與 `surface`／`edge`／上限 8 片的描述(現行 `SCENE_COMMANDS` 18 列,含已廢除的 span-auto:boundary／placement／space／datum／grid／column／beam…)、
「邊、參考線、錨點都各自記著 `surface_id`」(現為 `placement_id`)、§9「滑鼠拖曳參考線實際執行 `guide_line_move()`」
(`guide_line_move(` 在 C 裡已無呼叫點;bridge 的 drag 組成指令走 `feed_line` → `apply_reference_move`,
`web_bridge.c:12` 的檔頭註解也還寫著 guide_line_move)等。
另:`current_geometry.c` 檔頭「配套」註解仍叫人重跑已退役的 `make_axiom_reader.py`(GEO-165),應改指 `sync_axiom_reader.py`。與 SSOT 正面衝突的 R2 那句已在 GEO-175 改正,其餘是過時而非矛盾。

**處理**(以 `公理層.md` 與 `geometry-core/README.md` 為準,bridge `references`/`dump` 實測預設世界核對數字):
- §0 流程條與心智模型圖:「兩條參考線→交點當錨點」改畫現行預設世界——前後邊各一支 at-face 邊界角材(e0/e2)、一條 guide 1(u=500,沿 V,spec:主支中線)、主支 at-line 跨 v=27→2973;viewBox 加高 80px 收進後側邊界角材。
- §9:拖曳實際路徑改寫為 `reference_snap` 對引用式→組 `move` 指令→同一條 `apply_scene_line()`(GDI 與 web bridge 同構);代價框補「實際長出的第三層是網頁(web_bridge.c → JSON ops 串流)」,raylib 降為未來選項。
- §10:標題「七個指令」→「十八列指令」;指令清單重寫為 宣告 9(spec/boundary/placement/surface/space/datum/column/beam/timber)+承載面 3(guide/grid/place)+操作 5(move/apply-proj/delete/reset/canvas-pos)+墓碑 1(span-auto);
  上限 8→`WORLD_MAX_BOUNDARIES` = 16;`surface_id`→`placement_id`(並刪去已非物件的「邊」);「main 裡硬編」→內建預設世界;
  `room_a.scene` 與內建預設**已不等價**(邊界角材 20×20 vs 27×33、id 與 spec 名不同,bridge dump 實測),改述為「現行語法完整範例」。
- 實驗台錨點標籤不再寫「參考線 N 的 offset」(現行錨點是 at-line/at-face 引用,不是兩線交點)。
- `current_geometry.c` 檔頭:`make_axiom_reader.py`→`sync_axiom_reader.py`;4431 行註解的 `guide_line_move` 一併清除。
- `web_bridge.c` 檔頭:`default → 等價 room_a.scene` 改正為 `reference_default_world`;drag 註解改為實際路徑。
- 驗證:`check_panels.py` 40 panels / unresolved: none;`test_guide_panels` OK;headless Chrome 實開 §0 圖確認繪製與標籤。

`check_panels.py` 對現況(舊頁 + 現在的 C)報 **8 個 unresolved**:main 面板的 `SURFACE_DIRECTION_POS_U,` /
`SURFACE_DEPTH_POSITIVE_NORMAL`;SCENE_COMMANDS 的 `"place", 8, 15, true,` / `"move", 3, 3, true,`;
apply_place_line 的四個(`if (timber->placed) {`、`world_find_placement(world, placement_id)`、
`placement, boundary, guide_a, guide_b, &anchor_uv`、`timber_place_a0_on_surface(`)。

**重產步驟**:`core.exe --out current_geometry.svg`(硬編房間 A 的三視圖;`*.svg` 被 .gitignore 全域忽略,本機沒有這個檔,
直接跑 `make_guide.py` 會把圖換成「尚未產生」佔位)→ `make_guide.py` → 對現在的 C 逐面板改 `make_guide.py` 的 callout →
`check_panels.py` unresolved: none。
**為什麼這輪不做**:第 5 流(文件與導讀同步)的工作,要逐面板重讀程式,不是順手能收的;
GEO-100 記過「改 C 要同步 make_guide.py 的 callout」但沒有守門測試,所以一路飄到現在——
建議做的時候順手把 `check_panels.py` 加進 tests 的固定清單,讓它以後會紅。

### GEO-180 ✅ 已做(2026-09-22)P1:「面·多邊形——逐點閉合(正交)」設計澄清落地(主畫布 P + 面內 e 共用狀態機)

使用者提供 dc 互動文件(12 條「修改建議 vs 現況」+ 7 格狀態畫面),由多個 agent 分工、fresh 驗證、對抗審查,
主迴圈只拆工與整合。**四個紅燈先一次問完**(決策佇列 Q13–Q16 🔒):直接在工作區做(與 codex 未提交變更共存)、
主畫布 P 的 Esc 三段照澄清做而面內 🔒 階梯不動、補直角兩處都做且共用狀態機、尺寸確認清單兩處都可編輯。

**規格層**:`RC-POLYGON-PLAN.md` §5.A.1(12 條改寫成可驗證規格句 + 狀態轉移表 + cdp 編號分配 + 舊測試相容)、
`DOM-CONTRACT.md` 新節、新檔 `docs/POLYDRAFT-API.md`(模組介面 SSOT,含閉合驗證設計原則)。基線 cdp 315 ✓。

**Stage 3a 尺寸確認清單**(diff#10,🔒 Q16):`edgeListRowsHTML(loops, idPrefix)` 共用列產生;主畫布與面內都呼叫同一份
`commitEdgeLength` / `commitEdgeFixity`;cdp §P33 九條(改長度 → dump outline 變、切 F/X → fixity 變、非法長度 → 世界不變、
兩處清單一致);315 → 324 ✓。fresh 驗證通過。

**Stage 2 主畫布 P 接線**(diff#1–9、#11):`objDrawDown / objPolyTryClose / objPolyEnter / objPolyBackspace / objPolyEscStep /
objPolyPreviewMove / renderPolyDraftLayer / objFinishPoly / objEmitFace` 全部改呼叫 `PolyDraft.*`;獨立草稿層 `#polyDraftLayer`
(`ocDrawCount` 當可觀測訊號);三段浮標 + 「閉合」鈕;格線吸附 `gridMm`(預設 250);鍵入長度;對齊參考線;三種閉合;Esc 三段;
閉合後卡片落 bbox 左上、視野不動、開檢視器、toast。cdp §P34 共 24 條;`serve.py` 白名單加 `/polydraft.js`。
順手修一個真 UX bug:畫多邊形時卡片「進入›」熱區會搶走點擊、不落頂點。324 → 345 ✓,3 條舊 P15 斷言與拍板語意矛盾留給 3b 更新。

**Stage 3b 面內 e 接線**(diff#12):`fe.draft` 對等 `oc.polyDraft`;`feGridStep()` 抽出 Phase 5 B4 依 zoom 的格距供格線與吸附共用;`feDown` redraw 分支改呼叫 `PolyDraft.place / tryClose`,`feMove` 分派 `feDraftPreviewMove`;`feDraftTryClose / feCommitDraft / feDraftApplyLen` 取代 `feDedupe / feRedrawClose / feRedrawApplyLen`(刪除,不留兩套);面內 Esc 🔒 七階不動,只把「清鍵入長度」「清草稿」兩級改呼叫模組;`#feDraftLayer` 沿用 `.draft-*` 樣式。三條舊 P15 斷言依拍板語意改(關吸附再測;Esc 拆成「第一次只清草稿」「第二次才離開」)。cdp §P35 13 條(格距、參考線、補角逐點比對、自身邊 CROSS、Enter = 點回起點、Esc 三級順序、清單列數、P 與 e 同序列同 outline);345 → 362 ✓。

**驗證**:fresh 驗證員(整體):cdp 362 ✓ / 0 ✗、polydraft 70/70、DOM 合約雙向一致、`serve.py` 只多一行、§2 與 Esc 🔒 段未動;指出三視圖舊 poly 工具仍是第二套手寫軸鎖(範圍外 → GEO-181)。對抗審查(UI 接線):未發現繞過模組,Esc 階梯與 pendingSlot 交互正確;4 個中低 finding 全部修掉、各有紅 → 綠斷言(§P36 8 條 + P34-8b + P35-9 補強):三處重置沒同步 `oc.polyDraft` 鏡射、undo 中草稿層閃空、鍵入長度出錯只有一次性 toast、兩處一致性測試用的矩形不走補角。最終 **371 ✓ / 0 ✗**。

**與 codex 的共存**:工作區同時有 codex 2026-09-22 02:47 未提交的「第二輪 UI 修正(40 項)」(app.js / app.css / index.html /
cdp_test.js / DOM-CONTRACT / UIUX-FIX-PLAN),使用者選擇直接在其上做(Q13),兩者在 app.js 內不可分,**同一 commit 進版**,
commit 訊息明寫。`objEmitFace` 的 `pendingSlot` 流程是 codex 的,本輪只在 P 工具閉合路徑依 §5.A.1.9 調整、§P32 全綠。

### GEO-176 ✅ 已做(2026-09-22)P1:`polydraft.js` 共用草稿狀態機 + core.exe 跨層裁判;第一輪對抗審查 F1/F2

`geometry-web/polydraft.js`(純邏輯、UMD、零 DOM)+ `polydraft_test.js`(node:test)。牙先行:前一個 agent 被中斷前已寫 44 條測試,
接手者審完再實作;**跨層裁判**:隨機正交草稿 `tryClose` 的結果組場景檔送 `core.exe --scene`,接受/拒絕必須一致。
第一版 44/44、210 例 100%——但對抗審查(adversarial-reviewer)抓到 **F1**:直接閉合分支完全不驗自交;**F2**:補直角候選只比對
`existingEdges`(主畫布傳空陣列,等於不驗);**F3**:兩個產生器都走不到收尾/補角路徑,「100% 一致」不構成反證。
修:`loopHasSelfCross` + 三個非單調產生器(220 例);47/47。

### GEO-177 ✅ 已做(2026-09-22)P2:polydraft 第二輪——G1 錯誤碼誤判、G2 裁判盲區

**G1**:補角候選與既有頂點重合時 `dedupeLoop` 單趟去重連坐吃掉真正角點,拒絕結論對但錯誤碼變 TOO_FEW(應 NO_CORNER)。
**G2**:`judgeAgainstCore` 對 TOO_FEW/DEGENERATE 直接 skip,錯誤碼正確性零偵測力。修:候選去共線後湊不齊 4 頂點視為不可行;
裁判不再 skip,核心只有兩句粗粒度拒絕訊息,對照表照實記錄不硬湊;50/50。

### GEO-178 ✅ 已做(2026-09-22)P1:polydraft 第三輪(升 opus)——閉合驗證改成原則設計,形狀守恆不變式

第三輪複審抓到 **G3**(嚴重):直接閉合分支在收尾段與首段共線重疊時,去共線把起點 F 吃掉,`tryClose` 靜默送出「巧合合法但不是
使用者畫的」矩形(raw 5 點核心拒、deduped 4 點核心收);**G4**(根因):`applyTypedLength` 完全不跑 CROSS/BACKTRACK。
同一子任務 sonnet 連兩輪修不到根因 → 依調度守則帶完整軌跡升 opus。重寫(匯出不變):
- 檔頭「閉合驗證的設計原則」:每段新邊同一道檢查;閉合驗證對 **raw 環**做(`ringGeometryError` 逐條對齊 `poly_loop_is_valid`
  含首末邊排除,外加相鄰邊只准共享端點);`dedupeLoop` 只化簡不判合法;`adjacencyRelation` 是共享端點兩段的唯一判準。
- **形狀守恆斷言**套在每個 ok:輸出頂點都來自 raw、raw 每個頂點落在輸出邊上、有向面積相等非零——先跑紅時連隨機走位都抓到 G3 同病。
- 三組產生器 210/220/120 一致率 100%;59/59。兩個舊測試期望被收緊(以前靠去共線丟掉使用者畫過的突出段才湊出 ok,現在 NO_CORNER),
  使用者端表現是「某些畫法要多補一個頂點」。第四輪複審:F1/F2/G1/G3/G4 全部 CONFIRMED 關閉,主線可定稿。

### GEO-179 ✅ 已做(2026-09-22)P2:polydraft 前置先驗補齊——頂點上限 TOO_MANY、座標範圍 OUT_OF_RANGE

核心 `POLY_MAX_VERTICES = 32`(`current_geometry.c:198`,解析層與 `poly_loop_is_valid` 各擋一次,錯誤訊息兼管太少與太多,
核心分不出)→ 模組鏡射,`evaluateNextPoint` 落點當下擋、`tryClose` 化簡後再擋;上限用 core.exe 實測(32 接受、33/34 拒絕),
核心改上限測試會紅。幾何事實:正交簡單環頂點數恆偶數,所以「32 + 補角 = 33」不可能,tryClose 的 TOO_MANY 只是最後一道防線。
第四輪複審 **H1**:座標範圍沒鏡射 `COORD_LIMIT`(±100,000,000 mm),超界的面 UI 閉合成功、核心拒絕。修:鏡射 `COORD_LIMIT`(來源 `:43-47`,兩端含等號;`:239` 逐點驗),落點當下回 `OUT_OF_RANGE`(含吸附/延長/鍵入長度算出的點與首點),`evaluateClosedRing` 對 raw 環逐頂點驗,補角分支照實回報不收斂成 NO_CORNER;邊界用 core.exe 實測定(±1e8 接受、±1e8+1 拒絕);70/70,三組產生器仍 100%。

**教訓**:同一根源連三輪各修一角,是「打補丁」而不是「改原則」的典型;對抗審查每輪都用 core.exe 交叉驗證才逼出原則重寫。
另:前景 subagent 會被使用者任何訊息中斷,長任務一律背景派工(已記 memory)。

### GEO-181 ✅ 已做(2026-09-24)P3:三視圖畫布的舊「多邊形」工具仍是第二套手寫軸鎖(`canvasDown / canvasMove`),UI 可達

**🔒 Q17(2026-09-24)選 (b) 移除**。已刪:`index.html` 的 `data-v3-tool="poly"` 按鈕與隱藏 `#tool` 的 `poly` 選項;
`app.js` 的 `canvasDown` / `canvasMove` poly 分支、`drawPts` 宣告與四處重置、`v3SetTool` 狀態文字的 poly 分支。
三視圖工具剩 view/rect/hole/edit;建多邊形面只走主畫布 P(`PolyDraft`)。`cdp_test.js` P19 D2 改斷言工具數 4 且無 `poly`;
DOM-CONTRACT 同步。

GEO-180 的 fresh 驗證指出:`app.js` 約 712–763 的三視圖 `tool === "poly"`(`index.html` `data-v3-tool="poly"` 按鈕)
仍用自己的軸鎖(`Math.abs(du) >= Math.abs(dv)`)與 Manhattan 式回起點閉合,不經 `PolyDraft`,沒有補直角、前端先驗、
頂點/座標上限。現況地圖與 DOM-CONTRACT 都把它標為「同名殭屍」、本輪範圍外,但它確實存在且使用者點得到。
**選項**(需拍板):(a) 改接 `PolyDraft`(三視圖座標系另接一組 opts,吸附格距沿用主畫布 250);(b) 移除按鈕與程式碼
(主畫布 P 工具已完整取代);(c) 保留但在 UI 標示「舊版,無先驗」。我傾向 (b):同一件事三套邏輯只會再飄。

### GEO-183 ✅ 已做(2026-09-24)P1:geometry-web 回報收件匣——操作當下留回報,agent 直接讀現場

**起因**(使用者 2026-09-24):測完再回憶、再描述,agent 還要從口述猜是哪個功能;測試當下感覺到的異常只能間接轉述。
**拍板**(當場問答):F8 + 右下常駐鈕;存 repo 內 `feedback/` 但不進 git;只自動存程式錯誤(規則拒絕不存);第一版只做 geometry-web。

- `geometry-web/feedback.js`(app.js 之前載入):黑盒子常駐記錄最近 1000 筆(api 指令/回應/耗時、點擊與元素描述、
  畫布座標、按鍵(連打合併)、改值、toast/狀態列、JS 錯誤、console.error);F8 面板(分類、說明、指出位置、Ctrl+V 貼截圖);
  Shift+F8 快速標記;未捕捉例外/Promise 拒絕/橋接器斷線自動存(節流 20 秒、同因 5 分鐘);寫入失敗暫存 localStorage 補送。
  面板開著時鍵盤不外洩給 app(Esc 不會退出工作區);指出位置那一下不交給 app。
- 送出內容:說明、元素、畫面名稱與 `oc`/`fe`/三視圖狀態、視窗、場景、git 版本、`world.scene`(bridge dump)、
  `page.html`(DOM 快照,內嵌 app.css、去 script、canvas 轉圖、紅框標元素,瀏覽器直接開就是當時畫面)。
- `feedback_store.py`:編號 `F-YYYYMMDD-NNN`,先寫暫存資料夾再改名(讀者不會看到寫一半);`report.md` 摘要 + 最後 40 筆操作;
  `INBOX.md` 每次由全部 meta 重產。`serve.py` 加 `POST /feedback`(32MB 上限、沿用 L3 本機限定)、`GEOMETRY_FEEDBACK_DIR`。
- `feedback_cli.py`:list / show / events / replay(列改世界的指令 + core.exe 載回世界)/ close。
- app.js 只加三個掛鉤(`apiRequest` / `toast` / `setStatus` 呼叫 `window.fbRecord?.`)。
- AGENTS.md 新節:開工或使用者提到回報時先 `feedback_cli.py list`,不要先請使用者重述;不得刪回報資料夾。

**驗證**:`tests/test_feedback_store.py` 7 項;cdp_test §P38 12 項(黑盒子記錄被拒指令、鈕可見且不在頂列、F8 焦點、
Esc 不退出面工作區、指出位置不觸發 app 分頁切換、Ctrl+Enter 寫檔、meta/events/world/page 內容、欄位清空、
JS 例外自動存 kind=auto、規則拒絕不自動存);完整 cdp_test **401 ✓ / 0 ✗**;test_serve 9 項。
page.html 以 headless Chrome 截圖確認:面工作區畫面完整、紅框落在指到的「參考線」分頁。
**尚未**:真實觸控裝置(長按無 F8)、Safari;公理層閱讀器的批註未匯入同一收件匣(範圍外,第一版只做 geometry-web)。

### GEO-184 ✅ 已做(2026-09-24)P2:主畫布 Delete/Backspace 刪除選取的卡片

使用者問「物件畫布沒有移除功能嗎」:功能在,但只有右欄檢視器最底下一顆鈕(面檢視器被放置表單與邊清單擠到要捲才看得到),
主畫布無快捷鍵、卡片無 ✕,而面內/空間工作區的列表都有 ✕。
**做法**:主畫布有 `oc.sel` 且無繪圖工具時,Delete/Backspace 呼叫同一個 `deleteObject`(可 Ctrl+Z、被引用時走 I8a 影響預覽);
輸入框內與矩形/多邊形/挖孔進行中不作用。右欄刪除鈕文案加「Delete 鍵」。
**驗證**:cdp §P39 8 項(Delete、Backspace、toast、Ctrl+Z 復原、輸入框不刪、多邊形工具中不刪、被引用 → 影響預覽、Esc 取消世界不變)。

### GEO-185 ✅ 已做(2026-09-24)P1:多邊形(主畫布 P)UI/UX 審查——實機操作找出 9 項,修 8 項

審查方式:headless Chrome 實際操作 P 工具逐步截圖(畫 L 形、靠近起點、鍵入長度、Esc、交叉、閉合、縮放)。使用者選修 1/2/3/5/6/7/8/9,第 4 項開 GEO-186。
1. **吸附格看不見**:預設吸附 250mm(100% = 250px),畫面卻畫 24/120px 格;L 形第 5 點被吸到與第 4 點同格而被吞,畫成 250×250 正方形。
   → 多邊形工具 + 吸附時格線改畫實際吸附間距(`ocGridApply`,`.poly-snap-grid` 加深);`--grid-x/y` 原本沒人設、格線不隨平移,一併修;間距選單不再被截成「2」。
2. **閉合就緒卻紅字「會交叉」**:`PolyDraft.previewMove` 把收尾段當普通下一點跑 `evaluateNextPoint`,吸附後游標正落在起點 → CROSS;
   實際點下去閉合成功,回饋矛盾。→ closeReady 時錯誤以 `tryClose` 為準(polydraft_test +2,舊版兩項皆紅)。
3. **「Esc 退回」其實清整份草稿**,且草稿不在 undo 歷史;退一點的 Backspace 沒提示。→ kbd 文案改寫;清掉的頂點存 `oc.polyStash`,Ctrl+Z 先還原草稿。
5. **有 toast 時浮標整個隱藏**(`body:has(.toast) .canvas-mode-hint{visibility:hidden}`)→ 改成 toast 讓到浮標下方。
6. **閉合成功 toast 重複兩則**(setStatus ✓ 自動發一次 + objEmitFace 再發)→ 拿掉第二則。
7. **鍵入長度時浮標不更新** → 數字鍵/退格後重畫浮標。
8. **新游離面放置表單預設 u=+x、v=+x**,一選取就紅字「u 軸與 v 軸必須垂直」、按鈕停用(`placeFormHTML` v 預設誤寫 +x)→ 改 +y。所有新面都中,不限多邊形。
9. 浮標「放開即可閉合」實為按下即閉合 → 改文案。
**驗證**:cdp §P40 13 項;完整 cdp_test **421 ✓ / 0 ✗**;polydraft 72/72。

### GEO-186 ✅ 已做(2026-09-24)P2:主畫布「畫的尺寸」與「得到的卡片」對不上(GEO-185 審查第 4 項)

主畫布 1 畫布單位 = 1 mm,畫 4000×3000 的房間要在 100% 下拖 4000px(或縮到 20%);閉合後卻是固定 200×156 的縮圖卡片放在 bbox 左上,
縮到 20% 卡片只剩一個點。根因是同一張畫布混用兩套座標:卡片排版(固定尺寸)與多邊形繪製(mm)。
候選:(a) 卡片依實際 mm 縮放;(b) P 工具改成先建空卡、進面內工作區用實際尺寸畫外環;(c) 維持。**使用者 2026-09-24 選 (b)。**

做法:P/「＋面·多邊形」改為一次性動作(`objNewPolyFace`)——`newid` + `boundary` 建預設外環
(4000×3000 矩形佔位)的面卡、落在當下視野中心 → `enterFocus` 自動進面內工作區 → `feSetTool("redraw")`
直接以實際 mm 逐點畫外環 → Esc 回畫布。核心不需支援「無外環面」:預設矩形是合法 boundary,
進面內後被 redraw 整份取代(`emitBoundary` 同一交易語意)。
pendingSlot 流程保留:槽位「＋放置」備妥 rect 後按 P,新面帶入 `pendingSlot.bid`、進面內直接開放置頁。

移除的畫布 poly 機器:`oc.polyDraft`/`oc.poly`/`oc.polyPreview`/`oc.polyStash`/`oc.gridMm`、
`#polyDraftLayer`/`#polyCloseBtn`/`#ocLenInput`/`#polyGridSize`、`renderPolyDraftLayer`/`objPoly*`/
`ocLenShow`、`.tool-poly`/`poly-snap-grid`、`.quick-create.active`、poly 鍵盤/雙擊/三段 Esc。
順修一個殘留狀態 bug:`enterFocus`/`leaveFocus` 清 `drawTool` 後要重算 `#canvasModeHint`
(原本只有 `ocCursor` 呼叫 `renderCanvasModeHint`,P 在 rect 備妥時按下會留下殘影浮標)。
保留:面內 `PolyDraft` 全流程(§P35/P36)、`#feDraftLayer`、`.draft-*` 樣式、rect 拖曳建面(`objEmitFace`)。

**驗證**:cdp §P34 改寫為新流程 6 項(建面卡→進面內、預設外環佔位、面內實際 mm 畫 L 外環、
Esc 回畫布卡片在視野內、pendingSlot 帶入);舊畫布 poly 斷言(P34 原 15 項、P36 畫布段、
P40 多邊形段、P35-9 兩側對照)隨機器移除,P40 改驗存活路徑(rect 浮標/toast/放置表單預設軸)。
完整 cdp_test **390 ✓ / 0 ✗**;polydraft 72/72。

### GEO-187 ✅ 已做(2026-09-24)P1:縮到很小後卡片找不回來

使用者:建了兩個面卻找不到,點清單、按「定位卡片」也一樣。實況:畫大多邊形時縮到 2–5%,卡片 200×156 只剩一個點;
面 2 的卡片在多邊形左上 (500,-3000),離面 1 很遠(GEO-186 的直接後果)。三個缺陷:
1. `centerOnNode` 只平移不縮放 → 縮很小時(< OC_COMPACT_ZOOM)先回 100% 再置中。清單點選的自動置中也走它。
2. 縮放比例鈕回 100% 時直接改 zoom 不調 pan,畫面中心的卡片飛出畫面 → 改用 `ocZoomAt(1/zoom)` 以中心為準。
3. 縮很小時格線間距不到 1px,整片畫布糊成灰色(GEO-185 把主格改成細格 5 倍後更明顯)→ 間距 < 8px 時改畫 5 倍、25 倍的線。
**驗證**:cdp §P41 3 項;完整 cdp_test **424 ✓ / 0 ✗**。
> **改號說明(2026-09-25 合併)**:下面兩票在遠端 `origin/main` 原編號 GEO-169/GEO-170,與本機已用掉的 GEO-169(fuzz harness)/GEO-170(退化幾何測試)撞號,合併時改號為 GEO-188/GEO-189;遠端 commit `4cf3501`/`6470755`/`03989b7` 的訊息仍寫舊號。

### GEO-188 ✅ 已做(2026-09-25)P2:面內形狀編輯——方案 A「邊優先」+ 方案 B「形狀頁」

**起因**:使用者交來 Claude Design 匯出的「形狀編輯提案」(五方案互動原型 + 分鏡板 + `shapeops.js`),
問「看一下」後拍板「直接實作」。原型與分鏡收進 `geometry-web/docs/uiux-review/`
(`形狀編輯提案.dc.html`、`形狀編輯 步驟板.dc.html`、`shapeops.js`;檔名沿用原始名稱,
因為分鏡板用 `dc-import name="形狀編輯提案"` 依名稱嵌場景,改名會斷)。

**評估(對照 SSOT)**:四個提案的幾何都落在 I2 之內(軸平行、閉合、不自交;孔在外環內不重疊)。
真正的缺口有三:(1) 「特徵」這個概念核心沒有,核心只認 `boundary` 重宣告後的最終輪廓(WEB-004);
(2) 插凹口會讓後面的邊全部改號,被 at-face 引用的 `e<i>` 依 I8a 必須先出影響預覽;
(3) 新邊 fixity 沒交代。取 A 為主軸(與現行「點邊插凹口」心智模型最近、工具列不必動),
B 的清單當同一份特徵堆疊的檢視器放右欄;C(步驟精靈)、D(拖矩形自動分類)不做。

**做了什麼**(`geometry-web/app.js`、`index.html`、`app.css`):
- select 工具**單擊邊 = 選取**(邊亮起),浮出 `#feActionBar`:外環邊「凹口／外凸／推拉／F⇄X」,
  孔邊只有 F⇄X;**單擊外環凸角**浮出「切角」。點操作 → `#feOpPanel` 就地填
  「定位(從左／置中／從右)+距離、寬、深」(推拉:往內／往外+距離;切角:a、b),
  畫布即時畫紅(減)／綠(加)預覽矩形與尺寸,`Enter`／「套用」落地、`Esc`／「取消」關。拖邊仍是推拉。
- 幾何:`feRectBool(loops, "sub"|"add", rect)` 純函式(頂點座標切格 → 取邊界環 → 去共線),
  移植自提案的 `shapeops.js`。面消失或拆成兩片在前端就擋(toast),不送指令。
  **新邊 fixity:與舊邊共線重疊者繼承,其餘 FIXED**(對齊 R7「套用產生的新邊 fixity 一律 FIXED」;
  注意 Phase 2 的凹口對話框把凹口三邊設成 X,兩條路徑不一致,見「待拍板」)。
  新環走向與起點盡量沿用舊環,沒被動到的邊保住 `e<i>` 編號。
- 結果一律走 `emitBoundary` 交易:核心 I2 守門;動到被引用邊時核心回 `preview`,
  `api()` 照舊開 I8a 影響預覽對話框,確認才落地——所以 (2) 不必另做閘門。
- 右欄新增「形狀」頁:基底外環 + 本次工作階段套用的特徵清單(寬、高、距左／右、距上／下,可改起算邊),
  改數字即落地(反向布林還原 → 正向套用)、可鏡射、可刪除(反向布林)。hover 列畫布高亮。
- **特徵堆疊 `fe.feats[bid]` 只存在記憶體,不寫進 .scene**——每次 `feAfterChange` 用
  `feFeatAlive`(減料的矩形中心該在面外、加料的該在面內)逐筆驗活,對不上現況(含 undo)的自動剔除。
- Esc 階梯在「方向小選單」之後加兩階:面板開著 → 關;有選取 → 清;再來才是草稿/離開。
- 舊的「凹口」工具(點邊開對話框)、「開口」、「外環」重畫、形狀庫都保留;
  Phase 2 的「單擊邊切 fixity」**改走浮動列**(§9f 測試同步改)。

**測試**:`cdp_test.js` 新增 §P7b(8 行 24 個判定:浮動列、預覽尺寸、Enter 套用 4→8、fixity 同步、
起點沿用、切角、形狀頁改數字/鏡射/刪除、undo 驗活、拆片拒絕、推拉、Esc 階梯);
§9f「單擊切 fixity」改為「選取 + 浮動列切」;P18 B2 三頁 → 四頁。
`docs/DOM-CONTRACT.md` 補 `#feActionBar`/`#feOpPanel`/形狀頁/全域函式;`README.md` 補操作說明與 Esc 階梯。

**順帶查出的環境問題**(與程式碼無關,記在 README 測試段):Linux 容器 + Chromium 141 跑 `cdp_test.js`
打 `localhost` 時,新版 HttpStreamPool 每次先試 `::1`(-109)再退 `127.0.0.1`,約 600 次請求後
socket pool 卡死,P5b 永遠等不到 `pick`。netlog 確認;改 `GEOMETRY_TEST_URL=http://127.0.0.1:<port>/`
+ `--disable-features=HappyEyeballsV3` 即過。

**續(2026-09-25,使用者拍板「把舊的設計移除、用新的取代」)**:舊「凹口」工具整組移除——
工具鈕 `[data-face-tool="insert"]`、`i` 快捷鍵、`#notchDialog`、`feInsertNotch`/`fePointInFace`/`feFlashEdges`
與對應 CSS;凹口只走「選邊 → 浮動列 → 面板」。連帶把原本待拍板第 2 項(對話框路徑新邊給 X、
布林路徑給 F 的不一致)一起消掉:現在只有一條路徑,新邊依 R7 為 F。
「開口」「外環」重畫與形狀庫保留——新設計沒有取代它們的流程。
cdp_test §P7、§9f「參數化凹口」、§P17(d)(g) 改走新流程。

**待拍板**(不動 SSOT,只列):
1. 特徵堆疊要不要進 .scene?要的話核心得多一個「衍生特徵」概念,或前端另存 sidecar;目前刻意不做。

**回歸**:cdp_test 306/306(Linux 容器,Chromium 141,`127.0.0.1` + `--disable-features=HappyEyeballsV3`);canvas_test(HTTP)412/412;test_serve 9/9。

### GEO-189 ✅ 已做(2026-09-25)P2:描繪「指定尺寸正交多邊形」的完整路徑

**起因**:使用者問「你沒有審查過這個互動流程嗎」——GEO-188 驗的是凹口/切角/推拉各自能動,
沒有以「使用者要畫出一個指定尺寸的多邊形」為目標用真實滑鼠鍵盤走完整條路。補走六個情境後找到五個問題:
(1) 減法流程要使用者先心算切掉多少,而不是填最終邊長;(2) 沒有「依序輸入邊長」的直接畫法——重畫外環能鍵入長度,
但方向靠游標在哪一側,不能純鍵盤;(3) 開口只能拖、不能給數字、孔不能刪;(4) 套用後畫布殘留藍色高亮;
(5) 特徵距邊以現況外接框起算,外凸後全部跟著跳。使用者拍板「照順序做、全部做完」。

**做了什麼**(`app.js`、`app.css`、`cdp_test.js`、README、DOM-CONTRACT):
1. **重畫外環純鍵盤**:數字 + `← → ↑ ↓` 一段(方向明確,不看游標);沒點第一點就打數字 → 從原點起;
   `Enter` 閉合時末點與起點不同軸自動補角(少打一段);成功後回選取工具;`Backspace` 無數字時退一點。
   一個 L 形 = `e 4000→ 1500↓ 2500← 1500↓ Enter`。
2. **「留下」欄**:切角面板「切 a/b」與「留 u/v 邊」連動(留 = 鄰邊長 − 切),填哪邊都行;凹口面板加「留底」。
   欄位改 2×2 版面;面板改放到預覽矩形與操作列的外側,不再蓋住預覽。
3. **開口併入新流程**:select 單擊面內空白 = 選一個點 → 浮動列「開口」→ 填寬、高、距左/右、距上/下,記進特徵堆疊;
   「開口」拖矩形工具改走同一套布林並記特徵(面內 = 孔、碰邊 = 凹口、蓋角 = 切角,矩形裁到外接框);圖層列孔列加刪除鈕。
4. 套用/鏡射後不再自動選取該特徵(高亮只在形狀頁點列時出現)。
5. 特徵的起算邊(距左/右、距上/下)在建立時取較近一側並固定,之後不翻轉;數字本身跟著現況外接框走
   (試過「凍結在套用當下」——推拉右邊後凹口仍顯示舊的距右,和畫面對不上,改回現況值)。鏡射後 ax/ay 換成對面那條邊。

**測試**:cdp_test 新增 §P7c(鍵盤重畫 L 形/退點/補角/回選取、留下連動雙向、點面內開口 600×400@(1000,800)、
刪孔、拖矩形記 hole+notch、推拉後距右 1400→600 且起算邊不翻轉);§P17(d) 改為「點面內 = 點選取 + 開口」。
cdp_test 323/323、canvas_test 412/412、test_serve 9/9。

**沒做、為什麼**:C(步驟精靈)與 D 的自動分類 UI 沒做——D 的分類邏輯已借給拖矩形工具用,精靈對這批使用者沒有價值。
特徵堆疊仍不進 .scene(見 GEO-188 待拍板)。

### GEO-190 ✅ 已做(2026-09-25)P2:面內工作區「底圖臨摹」

**起因**:使用者要把掃描/照片的平面圖放在面內工作區底下當底圖,照著描外環;之後會再加「向量平面圖幾何重建」,
所以底圖狀態要獨立、好擴充。核心引擎(`web_bridge.c`、`.scene` 格式、`公理層.md`)一律不動,純前端票。

**🔒 拍板**:
1. **儲存**:原為本次工作階段；2026-09-26 經使用者明示核准 GEO-198 擴充為可隨 `.gcanvas` 專案包保存。
   不寫 `.scene`、不寫 `localStorage`；`api("dump")` 輸出不得出現底圖資訊。未保存的來源仍只在本次工作階段。
2. **比例尺**:在圖上點兩點、填實際距離(mm),程式算 mm/px。
3. **UI**:右欄新增「底圖」分頁 `data-fi-tab="underlay"`,放在「網格」之後(分頁順序 prop,shape,guide,timber,grid,underlay,共 6 頁)。
4. **對位**:拖曳 + 數字微調(x/y 偏移 mm、旋轉 0/90/180/270)。

**做了什麼**(`geometry-web/app.js`、`index.html`、`app.css`):
- 狀態 `oc.underlays[bid] = {src,imgW,imgH,mmPerPx,x,y,rot,opacity,locked}`;`feUnderlaySet(bid,{src,imgW,imgH})`
  建立預設值(`mmPerPx=外接框寬/imgW`、`x,y=`外接框左上、`opacity 0.5`、`rot 0`、`locked false`)。
- `drawFaceEditor()` 在 `#faceEditorRoot` **第一個子節點**插 `<image id="feUnderlay">`(在格線與面之下),
  `transform="rotate(rot,cx,cy) translate(x,y) scale(mmPerPx)"`(`cx,cy` 是未旋轉時圖片中心的面座標,
  x/y 的語意——「未旋轉時左上角」——因此不因旋轉改變)。**只有**「底圖」分頁作用中、`select` 工具、
  且未鎖定時 `pointer-events:auto`,其餘一律 `none`,不擋既有的點邊/點角/點面/畫外環。切分頁
  (`fiShowTab`)、切工具(`feSetTool`)都用 `feUlSyncPointerEvents()` 就地同步這個屬性,不整份重畫。
- 量比例尺:`#ulCalibStart` → `fe.ulCalib={pts:[]}`(圖片原始像素座標);進行中的 `pointerdown` 不論落在
  哪、不論工具一律攔截去記校準點(不進 `feDown`,避免被 select 工具「點面內=選點」搶走);畫布
  `<g id="feUnderlayCalib">` 用 `feUlImgToMm`/`feUlMmToImg` 換算顯示。兩點齊了才能填距離套用,
  `mmPerPx = distMm / 兩點的px距離`,x/y 不變。Esc 階梯在「就地操作面板」之前插一階:量比例尺進行中
  只清 `fe.ulCalib`,不離開工作區;切離「底圖」分頁或切離 `select` 工具都連帶取消進行中的量比例尺。
- 拖曳:`pointermove` 只改 `oc.underlays[bid].x/y` 與 `#feUnderlay` 的 `transform` 屬性(不呼叫
  `drawFaceEditor()`,做法同既有的 pan),`pointerup` 才 `renderFaceInspector()` 同步 `#ulX`/`#ulY`。
- **另一位讀過原始碼的審查者**(未落地實作,只留意見)指出三個坑,已修:
  (1) 面內格線(`.fe-grid-line`)與原點標記(新增 `.fe-origin-mark` class)在 `app.css` 設
  `pointer-events:none`——這兩者本來沒有任何點擊處理,但底圖插在最底層時,滑鼠按在這些線上會讓
  `e.target` 變成線而不是 `#feUnderlay`,拖曳啟動不了;(2) 拖底圖的條件加上 `fe.tool==="select"`,
  不然分頁開著時按其他面內工具鍵(例如 `e` 描外環)點下去會被底圖吃成拖曳;(3) `fiShowTab`/`feSetTool`
  切離底圖分頁或切離 select 工具時,同步 `#feUnderlay` 的 `pointer-events` 並取消進行中的量比例尺。
- 測試用全域(cdp_test 用它們避開檔案對話框/滑鼠模擬):`feUnderlaySet`、`feUnderlayCalibStart`、
  `feUnderlayCalibPoint([px,py])`、`feUnderlayApplyScale(distMm)`、`feUnderlayRemove(bid)`。

**測試**:`cdp_test.js` 新增 §P42(9 組斷言:6 頁分頁順序、底圖建立預設值、量比例尺套用、不透明度/鎖定、
拖曳换算 mm 與跨分頁不拖、底圖存在時鍵盤重畫外環仍成功、量比例尺 Esc 取消、離開再進保留+dump 不洩漏、
移除底圖回到空頁);P18 B2「五頁」改六頁、F1/F3/F4 分頁數 5 → 6。`docs/DOM-CONTRACT.md`、`README.md` 同步補新
ids/全域/操作說明。**回歸**:cdp_test 449/449、canvas_test(HTTP)412/412(Windows,已編 bridge.exe,埠 8799)。

**沒做、為什麼**:向量平面圖幾何重建(使用者提到的下一步)不在本票範圍,留待另立票。旋轉的拖曳互動測試只涵蓋
預設 `rot=0`(驗收條件未要求非零旋轉下的拖曳數學);`feUlImgToMm`/`feUlMmToImg` 的旋轉换算是解析式互逆函式,
邏輯上對任意 rot 成立,但沒有額外測資覆蓋 90/180/270 度時的拖曳誤差。

### GEO-191 ✅ 已做(2026-09-25)P2:面內工作區角材可選取——點角材高亮、左右欄同步、可刪;不做就地改錨點

**起因**:面內工作區用選取工具點角材沒反應——角材矩形(`.face-timber`)沒有 `data-face-hit`,點下去被當成
點面內空白(GEO-189 的「點」選取)。使用者拍板:只做選取/高亮/刪除,不做就地改錨點/方向/截面(語意未拍板)。

**做了什麼**(`geometry-web/app.js`、`app.css`):
- 角材矩形加 `data-face-hit="t:<id>"`(`feTimberRect(t2)` 抽出算矩形的純函式,`drawFaceEditor`/`feSelAnchor`
  共用同一份,不各自重算);CSS 只在 `.face-editor-viewport.tool-select` 下 `.face-timber { pointer-events:auto }`,
  其餘工具一律 `none`——不擋既有的點邊/點角/點面/畫外環/放角材落點。
- select 工具命中 `t:<id>`(`feDown`)→ `fe.sel={kind:"timber",id}`,清 `fe.op`/`fe.selFeat`;矩形加 `.sel`、
  左欄該列(`.face-layer-row[data-timber-id]`)同步加 `.sel`;`#feActionBar` 只浮出一顆 `[data-fe-act="delete"]`
  (沿用既有 `feSelAnchor`/`fePlaceOverlays` 擺法)。
- 角材頁(`fiShowTab("timber")`)頂端加 `#tbSelected`:「已選角材 `<id>`」+ 宣告摘要(L×A×B、@(u,v)、dir/side、role,
  欄位照 `references` 回傳有什麼顯示什麼)+ `#tbSelDelete`,與畫布浮動列、左欄 ✕ 鈕共用 `feDeleteTimber(id)`
  (`delete timber <id>` 走 `emitLine`/mutate,可 Ctrl+Z)。
- 左欄角材列:hover → 矩形加 `.hover`;點列(非 ✕)= 與畫布點選相同效果。
- `feAfterShapeChange`(邊界變更/`feAfterChange` 收尾)與 `feDeleteTimber` 都驗:選取的 timber id 已不在
  `fe.timbers` → 清 `fe.sel`。Esc 既有階梯「有選取 → 清」自然涵蓋 timber,一併清左欄 `.sel`。

**測試**:`cdp_test.js` 新增 §P43(8 組斷言:命中層存在、點選高亮+浮動列、點空白仍是「點」選取、Esc 清選取、
左欄 hover/click 同步、角材頁摘要+刪除+Ctrl+Z 復原、切到重畫外環工具點角材位置仍成功落點)。
`docs/DOM-CONTRACT.md`、`README.md` 同步補新 ids/class/選取型別/操作說明。
**回歸**:cdp_test 459/459、canvas_test(HTTP)412/412(Windows,已編 bridge.exe,埠 8799)。

**沒做、為什麼**:就地改錨點/方向/截面——語意未拍板,按票面要求不做;特徵堆疊/底圖等既有機制不受影響。
刪除 `role boundary` 的角材會經過 I8a 角色衍生屬性重算,`api()` 自動開影響預覽對話框,
測試(§P43-7b)與畫布/左欄/檢視器三路刪除鈕都要等確認才真的落地(同既有 P22/P31/P39 模式)。

### GEO-192 ✅ 已做(2026-09-25)P2:面內四種游標互動——Alt 拖頂點捏缺口、拖預覽邊改尺寸、右鍵選單、雙擊直開面板

**起因**:純滑鼠使用者要能做缺口與改尺寸,並要右鍵/雙擊這兩種常見互動,不必每次都先點浮動列。

**使用者拍板 🔒**:
1. Alt + 拖頂點 = 捏缺口;不按 Alt 照舊「拉角」(`applyVertexEdit`),零改動。
2. 雙擊 = 直接開該目標最常用的操作面板(邊→凹口、凸角→切角、面內空白→開口且該點為選取點、角材→切到角材頁並選取)。
3. 右鍵選單的內容 = 浮動列同一套動作,同一資料來源,不另列。
4. 拖預覽矩形的邊改尺寸:做法由主迴圈(implementer)決定——見下方欄位對應規則。

**做了什麼**(`geometry-web/app.js`、`app.css`、`index.html`):
- **A(Alt 拖頂點捏缺口)**:`feDown` 新增 `k==="v" && ev.altKey && loop===0 && 凸角` 分支,進
  `fe.drag={kind:"pinch",...}`;`fePinchRect()` 算矩形(頂點到游標、吸附 `feGridStep()`、裁到鄰邊長);
  放開時走與切角面板**完全相同**的路徑(`feRectBool("sub",rect)` → `emitBoundary` → 記進 `fe.feats`
  `type:"corner"`,`feNearestSides` 定 `ax`/`ay`)。拖曳中畫 `.fe-ghost.sub`;Esc 借用既有「有 `fe.drag` → 清」
  那一階,不用另外處理。
- **B(拖預覽矩形邊)**:預覽矩形四邊加 `<line class="fe-ghost-handle" data-fe-handle="left|right|top|bottom">`
  (只在 select 工具、`fe.op` 存在時畫,粗描邊+對應 `cursor`)。`feApplyGhostDrag()` 的規則:與母邊平行的
  邊界動「寬 w」(連動改 `anchor:"start"`/`dist` 讓另一側不動)、與母邊垂直且不與母邊重合的邊界動「深 d」
  (push 動 `dist`);point/corner 目標比照對應欄位。放開不套用,仍要 Enter/`#feOpApply`。
  `feSyncOverlays()` 的 `show` 判斷放行 `fe.drag.kind==="opHandle"`,拖曳中面板才不會被「有 `fe.drag` 就隱藏」
  的既有邏輯關掉。
- **C(右鍵選單)**:新增 `#feCtxMenu`(`role="menu"`)。抽出 `feActionsFor(sel)`/`feRunAction(act)`,
  `#feActionBar` 與 `#feCtxMenu` 共用同一份清單與處理器(逐一相同)。抽出 `feClickSelectBlank`/
  `feClickSelectHit`,原本分散在 `feDown`(blank/timber 分支)與 `feUp`(vertex/edge 未移動分支)的選取邏輯
  合併成共用函式,`contextmenu` 事件也呼叫它們(不複製一份)。關閉:點選單外(`document` capture 階段的
  `pointerdown`)、Esc(階梯在「量比例尺」之前新增一階)、滾輪縮放。
- **D(雙擊)**:**不掛原生 `dblclick` 事件**——單擊選取(`feClickSelectHit`/`feStartOp`)會呼叫
  `drawFaceEditor()` 整份重繪 SVG、`feSyncOverlays()` 重建 `#feActionBar` 按鈕,第一下處理完那個節點就已經
  被拔掉,原生 `dblclick` 的 target 常常冒泡不到任何監聽器(`ev.detail` 在 CDP 送出的 `pointerdown` 上也量不到
  可靠的連續點擊數,實測恆為 0/1)。改成 `fevp` 的 `pointerdown` 監聽器自己量這次與 `fe.lastPD`(上一次
  pointerdown 的時間/螢幕座標)的差,450ms 內、位移 ≤6px 視為雙擊,呼叫 `feHandleDblClick(pt,ev,onOverlay)`;
  `onOverlay`(這次點在 `#feActionBar`/`#feOpPanel`/`#feCtxMenu`/`#feGuidePick` 上)時改沿用第一下已經定案的
  `fe.sel`,不重新命中畫布,並 `ev.preventDefault()` 壓下這一下補發的 `click`(避免浮動列按鈕,例如角材的
  「刪除」,被誤觸發)。這段判斷刻意放在既有「點在浮動 UI 上就 return」之前,否則第二下若剛好落在第一下才
  冒出來的按鈕上會被那條 return 攔截,永遠走不到雙擊判斷。`feDblOpenFor(sel)` 決定開哪個面板。

**測試**:`cdp_test.js` 新增 §P44(9 組場景,含 1 不按 Alt 拉角照舊、2 Alt 拖捏缺口+Ctrl+Z、3 拖到一半 Esc、
4 拖預覽邊改尺寸+套用、5 右鍵選單內容比對+點選單項目、6 右鍵面外空白/角材、7 四種目標雙擊、8 雙擊後單擊
面外空白不留殘留、9 既有斷言照舊)。`docs/DOM-CONTRACT.md`、`README.md` 同步補新 ids/函式/操作說明。
**回歸**:cdp_test 478/478、canvas_test(HTTP)412/412(Windows,已編 bridge.exe,埠 8799)。

**沒做、為什麼**:B 的欄位對應語意未拍板(票面明說「由主迴圈決定」),上面寫的規則是實作採用的具體規則,
不是使用者拍板——若日後語意有爭議,以此規則為準改測試與說明,不必回溯改行為;拖曳時的「留下」欄同步
沿用既有 `feSyncPanelValues` 的連動,沒有另立一套。

### GEO-193 ✅ 已做(2026-09-25)P3:重畫外環閉合併點提示(不擋)

**起因**:`polydraft.js` 的 `tryClose` 補直角時(末點與起點不同軸)先組出完整 raw 環再去共線
(GEO-178 三原則),去共線可能把使用者剛畫出來的一個轉折(與相鄰邊共線)悄悄併掉——
草稿 `(0,0)(4000,0)(4000,1000)(3000,1000)` 按 Enter 補 `(0,1000)` 閉合,`(3000,1000)`
與相鄰兩點共線被吃掉,得到 4000×1000 矩形,使用者畫的「缺口」靜默消失。但同樣的幾何結構
(補角+去共線把一個頂點併掉)也可能是使用者故意少畫最後一段、就是想要矩形——`(0,0)(4000,0)
(4000,3000)(2000,3000)` 補 `(0,3000)` 一樣會併掉 `(2000,3000)`,但這次是想要的結果。
兩者在幾何上完全無法區分,所以只能提示、不能擋。

**做了什麼**:
- `polydraft.js::tryClose` 成功時多回傳一個欄位 `dropped: number[][]`——草稿 `state.pts`
  裡有、輸出 `pts` 裡沒有的頂點(依座標比對純函式 `droppedVertices`),兩個分支(直接閉合、
  補角閉合)都算;沒有併掉任何點就是 `[]`。既有回傳欄位(`ok`/`pts`/`error`)不變。
- `app.js::feDraftTryClose`/`feCommitDraft`:閉合成功、`emitBoundary` 落地後,`dropped.length>0`
  才 `toast`+`setStatus`「已閉合;補角時 (x,y)、(x,y) 併入直線——若要保留該轉折,Ctrl+Z 後
  把下一段畫完再閉合」(座標依 `dropped` 順序、用「、」隔開)。不改變任何幾何結果、不彈對話框、
  不擋任何閉合。
- `README.md` 重畫外環段落補一句說明;`docs/DOM-CONTRACT.md`/`docs/POLYDRAFT-API.md` 補
  `dropped` 欄位契約。

**測試**:`polydraft_test.js` 加 3 條(缺口案例 `dropped=[[3000,1000]]`、少畫一段案例
`dropped=[[2000,3000]]`、直接同軸閉合 `dropped=[]`),全部透過既有 `tryCloseChecked` 包裝
(形狀守恆斷言照跑)。`cdp_test.js` 新增 §P45(2 條):(a) 鍵盤 `4000→ 1000↓ 1000← Enter` →
外環 4 頂點 4000×1000,狀態列含「(3000,1000)」與「併入直線」;(b) `4000→ 3000↓ Enter`
(直接同軸補角、無併點)→ 狀態列不含「併入直線」。

**回歸**:`polydraft_test.js` 75/75;`cdp_test.js`/`canvas_test.js` 結果見下一票(GEO-194)
一併跑的回歸段。

### GEO-194 ✅ 已做(2026-09-25)P2:面內角材就地編輯——同 id 刪掉重放一筆交易

**先查的事實**:`fe.timbers` 來自 `references` 橋接指令(`geometry-web/reference_bridge.inc::
cmd_references` → `json_reference_geometry`,經 `web_bridge.c` unity-build 併入
`current_geometry.c`),每支角材回傳 `{id, role, geometry:{surface,centerline,length,u,v,
dir,side,A,B,origin,axes}}`。**橋接不回傳 anchor/selector(at-face/at-line 的具體引用式)、
也不回傳 priority**——這兩者是 `place`/`timber` 宣告時的輸入參數,核心目前沒有把它們吐回來。
`place` 的完整語法(`current_geometry.c` 場景 DSL 表):`place 角材id on 承載面id at-line
guide 線id｜grid 網id u|v 索引 或 at-face e索引｜h孔e邊｜t角材`;`timber` 語法:`timber id
A尺寸 B尺寸 role boundary|primary|secondary|custom [priority N]`。本票**沒有**改
`web_bridge.c`、`.scene` 格式或核心。

**做了什麼**(`geometry-web/app.js`):
- 角材頁 `#tbSelected` 區塊(GEO-191 唯讀摘要)改成可編輯表單 `#tbEditForm`:A/B/方向
  (`#tbEditDir`)/側(`#tbEditSide`)/角色(`#tbEditRole`)+priority(`#tbEditPri`,
  只在 custom 顯示)這五組橋接有回傳,直接預填;定位引用(`#tbEditAnchor`)+選段
  (`#tbEditSelector`)重用放置表單的選項來源 `referenceAnchorOptions(bid, surf)`,但
  **固定不預填**(下拉第一項是空字串佔位「橋接不回傳現有錨點,請重選」)——套用前必須
  重新選擇,否則會被前端擋下(錨點必選,同放置表單既有驗證)。
- 按鈕「套用變更」(`#tbEditApply` → `feTimberEditApply(id)`):驗證與放置表單一致(A/B
  正整數、custom 要 priority、錨點必選,失敗 `feMarkInvalid` 標紅、不送指令),通過後組一筆
  `mutate([...])` 批次、同一個 id:`delete timber <id>` → `timber <id> A B role …` →
  `place <id> on <sid> anchor selector dir side`。成功後 `feLoadGuides()`、選取留在同一 id、
  重繪左右欄與畫布;失敗 `mutate()` 自己 toast 原文、不動狀態。
- `mutate()` 既有的 `history-begin`/`history-end` 群組本身就是原子的(任一行失敗核心整組
  回滾、abort 冪等驗證回滾)——**不需要**額外的 dump 先留底/undo 保底,三行是單一 history
  群組,`Ctrl+Z` 一次就回到編輯前。
- 影響預覽:`delete timber`/`place` 任一行觸發 I8a(角色衍生屬性重算)時,`mutate()`
  內部逐行呼叫的既有 `api()` 本來就會攔截 `result.preview` 開 `confirmReferenceImpact`
  對話框並等待使用者確認/取消——`feTimberEditApply` 不必另外處理,照舊等確認、不繞。

**測試**:`cdp_test.js` 新增 §P46(5 組,含 e 略過):(a) 選取後 `#tbEditForm` 出現且
A/B/dir/side 預填正確、錨點固定留空;(b) 改 A=40/B=60/side=-n、重選錨點 `at-face e0` →
套用 → `fe.timbers` 仍只有 id 10、欄位如預期、`fe.sel` 仍是 timber 10;(c) `Ctrl+Z` 一次
回 A=27/B=33(驗證 mutate 群組單步 undo);(d) 填 A=0 → 前端擋下、toast 出現、`fe.timbers`
不變;(e) 橋接不回傳錨點(已於 (a) 驗證),無法測「改錨點後位置改變」,略過並在測試 log
印出說明。

**橋接是否回傳錨點**:不回傳(見上「先查的事實」),已在表單與測試中如實處理,並在此記錄
供後續票參考:若日後 `cmd_references` 補上 anchor/selector,`#tbEditAnchor`/`#tbEditSelector`
可以改成預填現值。

**mutate 批次是否原子**:是——`history-begin`/`history-end`/`history-abort` 本來就是
既有機制,群組內任一行失敗核心自動整組回滾,群組整體是單一 undo 步驟。

**Ctrl+Z 實際步數**:1 步(三行 `delete`/`timber`/`place` 同一個 history 群組)。

**沒做、為什麼**:就地改截面/方向/側以外的欄位(例如手動指定 length、直接搬動 A0 原點)——
語意未拍板,按票面要求不做;錨點/選段預填——橋接沒有回傳來源資料,技術上做不到,已如實記錄
待續票(需要 `cmd_references` 先補欄位)。

**回歸**(GEO-193/194 合併一次跑;Windows,已編 bridge.exe,埠 8799):
`polydraft_test.js` 75/75;`cdp_test.js` 484/484(含新增 §P45 2 條、§P46 5 條);
`canvas_test.js`(HTTP)412/412。另以獨立聚焦腳本(`p45_p46_smoke.js`,只連同一個
serve.py+bridge、跳過與本票無關的既有測試)對 §P45/§P46 邏輯單獨跑過一次交叉驗證,
6/6 全過,確認 I8a 影響預覽對話框、`mutate` history 群組、Ctrl+Z 單步復原都是在
真實瀏覽器 + 真實核心下驗證,不是只過測試斷言字串。

### GEO-195 ✅ 已做(2026-09-26)P1:角材放置表單 UX 止血——預設挑空線、畫布預示落點、失敗訊息講人話、角色依主支軸排除

**起因**:使用者在已有 3 支角材(角材 1/2 boundary 分別在外輪廓邊 0/2、角材 3 primary
在參考線「主支中線」u=500)的面上開角材頁放第 4 支,表單預設「外輪廓邊 0、+u、+n、
primary」,在面內點了八次都收到 `line N: R6/I5/I6 timber 4: 中線上沒有任何合法跨距`,
以為沒有位置可放。真相:(a) 點擊位置被忽略、角材落在定位引用那條線上,畫面沒有任何
提示;(b) 預設的邊 0 已被角材 1 占滿;(c) 錯誤訊息是規則代號,沒說「換一條定位引用」;
(d) 角色有硬規則(boundary/secondary 必須垂直於主支軸、沿主支軸只能 primary),表單
不會排除。不改放置流程本身(點面內永遠只是「確認」)、不改引擎、不改 `.scene`。

**做了什麼**(`geometry-web/app.js`、`geometry-web/reference-ui.js`、`app.css`):
- **預設挑空線**:`feAnchorLineInfo(bid, anchorValue)` 把定位引用式換算成
  `{constAxis:"u"|"v", value}`(哪個座標軸固定、固定在哪個值);`feAnchorOccupied(bid,
  anchorValue)` 用它比對 `fe.timbers` 的足跡(`feTimberRect`)——**只比對角材的「深度
  軸」**(長度方向的垂直軸,角材沿 u 跑深度就在 v)。第一版漏了這個限制,直接拿軸對齊
  外接框比對,結果一支貫穿全長的角材(例如角材 1 橫跨整個 u 範圍)讓所有垂直於它的線
  (包含參考線、對向邊)全部被誤判成占用;cdp_test §P47 一開始就是靠這個假陽性抓到的
  (見下方「跑測試」的除錯記錄)。`referenceAnchorEntries(bid, surf)` 把每條定位引用
  包成 `{value,label,occupied}` 結構化清單,`referenceAnchorOptions`(reference-ui.js)
  據此排版:占用的文字後加「(已有角材 N)」並排到未占用之後,`<select>` 沒標 `selected`
  時瀏覽器預設選第一個 `<option>`,重排後自然是第一條未占用,不必另外設定;全部占用時
  不重排,`#tbAnchorAllOccupied` 出現提示「所有定位引用都已有角材，先加參考線(L)」。
- **畫布預示落點**:`fe.anchorPreview`(#tbAnchor 焦點/hover/改值)或角材工具啟用中,
  `drawFaceEditor()` 畫 `.fe-anchor-hi`(定位引用本身的虛線)+ `.fe-anchor-band`(依
  `#tbSide`/`#tbA` 示意角材占用的半透明帶,標「示意」——真正長度由引擎依支撐推導,這裡
  只畫全圖範圍近似;帶固定沿定位引用展開,不看 `#tbDir`)。切工具/切分頁就清除
  (`feSetTool`/`fiShowTab`)。角材工具下 `#faceCanvasHint`/狀態列改走
  `feTimberHintRefresh()`,文字「角材將沿「〈定位引用名〉」放置，點面內任一處確認；
  點擊位置不影響位置」。
- **失敗訊息講人話**:`feTimberPlaceErrorMessage(err, bid, surf, anchorValue)`——
  `mutate()` 新增可選第二參數 `opts.friendlyError(rawError)=>string`(不傳就是既有
  行為,不影響其他呼叫點),`feDown` 的角材分支傳入。依錯誤原文前置一句、原文接在後半:
  含「中線上沒有任何合法跨距」→「〈定位引用名〉已被角材 N 占滿——請換定位引用(可用:
  〈未占用清單〉)」(全部占用改「請先加參考線(L)」),並 `feMarkInvalid($("tbAnchor"))`;
  含 `V_PRIMARY_AXIS` →「主支軸是 〈u|v〉:沿它放只能選 primary;boundary/secondary
  要垂直於它」;含 `V_CUT_PRIORITY` →「貼外輪廓邊的角材要選 boundary」,兩者都
  `feMarkInvalid($("tbRole"))`;其他錯誤原文不動。
- **角色依主支軸排除**:`feTimberPrimaryAxis(bid)`——`fe.timbers` 若有 `role==="primary"`,
  主支軸 = 那支 `dir` 的軸;`feTimberRoleOptionsHTML` 依目前 `#tbDir` 算:平行 → 只有
  `primary` 可選,其餘 `disabled`;垂直 → `primary` `disabled`,其餘可選。`#tbDir` 的
  `change` 觸發 `feTimberSyncRoleOptions(pane)` 重算;原本選的角色若變成 `disabled`,
  自動跳到第一個可選項並 `toast` 一句說明。

**測試**:`cdp_test.js` 新增 §P47(6 組,對應驗收條件全部 ✓):(1) `#tbAnchor` 預設值
不是已占用的 e0/e2/guide 1,選項文字含占用標記;(2) 角材工具下畫出 `.fe-anchor-hi`/
`.fe-anchor-band`,浮標/狀態列含「點擊位置不影響位置」,切回 select 消失;(3) 方向
+u/+v 下 `#tbRole` 的 primary/boundary `disabled` 對調;(4) 強制選回已占滿的 e0、真
滑鼠點面內 → toast 含「已被角材 1 占滿」與「可用:」、`#tbAnchor` 標紅、`fe.timbers`
不變;(5) 用 `referenceAnchorEntries` 算出的第一條未占用值點面內 → 成功、`fe.timbers`
4 支,Ctrl+Z 回 3 支;(6) 用 JS 移除 disabled 強制選 boundary + 方向平行主支軸 → toast
含「主支軸是 v」、`fe.timbers` 不變。場景直接用 `api('default')` 還原(`geometry-core/
transactions.inc::reference_default_world` 剛好就是本票起因場景本身,不用手打 DSL)。
`docs/DOM-CONTRACT.md`(新增 GEO-195 節 + `#tbAnchorAllOccupied`/`.fe-anchor-hi`/
`.fe-anchor-band` 等契約)、`README.md`(角材放置段落補說明)同步更新。

**跑測試**(Windows,已編 bridge.exe;8799 當時被殘留的 `python.exe`(PID 21608)占用,
沒有動它,改走 8798;9333 未被占用):`cdp_test.js` 493/493(含新增 §P47 6 條);
`canvas_test.js`(HTTP)412/412。過程中 §P47-1/2a/5 起初各失敗一次:5 是測試本身的
瑕疵(`renderFaceInspector()` 的 `restoreInspectorState` 會刻意保留使用者上次在
`#tbAnchor` 打的草稿值,不會因為重繪就重算預設——這是既有的、給真人用的草稿保留機制,
不該為了測試改掉;改成測試直接用 `referenceAnchorEntries` 算出第一條未占用的值寫回
欄位,等同使用者自己重選);1/2a 是 `feAnchorOccupied` 真的漏了「只比對深度軸」這條,
已如上「做了什麼」段修正並在程式碼留下踩坑註解。跑完已 `taskkill` 自己起的 `python.exe`
(port 8798)、確認 9333 無殘留 chrome、`git checkout -- geometry-web/docs/screens/`、
`git status` 乾淨無 untracked。

**沒做、為什麼**:流程層「點畫布上的邊直接放」(取代/補強「定位引用」下拉,讓點擊位置
真正決定落點)不在本票範圍——票面明講「不改流程」,這是另一票的語意判斷,不擅自做。
占用判定的距離容許值(`A`/`B` + 1mm)是 UX 近似,不是引擎的精確拒絕判定,兩者可能在
極端案例(例如角材截面極薄)下不完全一致;這是預期中的近似,不是 bug。

### GEO-196 ✅ 已做(2026-09-26)P1:角材工具點畫布上的線直接放置——定位/方向/角色由點擊決定,厚度方向依表單(G196-R02 起),表單路徑不變

**起因**:GEO-195 讓人看得懂角材會落在哪,但流程仍是「先在右欄下拉挑線、再點面內確認」。
使用者的直覺是直接點想放的那條線。本票加一條**新的**路徑,舊路徑(表單 + 點面內空白)
一字不改。

> **G196 修復批注(2026-09-27,GEO-196 修復工單 R00–R06)**:初版有三個語意錯誤,已由
> 修復工單改正——(a) **側**原本由「點在線的哪一側」覆寫 `±n`,這是把面內左右誤當法線
> 厚度方向,已改為一律沿用右欄 `#tbSide`(R02);(b) **角色**的 `feTimberPrimaryAxis`
> 只看既有 primary,缺 D17 的 boundary 反推,無 primary 時會把平行主支軸的邊誤給
> boundary 讓核心拒絕——已改為 `fePrimaryAxisInfo` 完整推導(R04);(c) **預示帶**
> 原本用「線 + 側×A」畫單側偏移,且 `at-face` 可能畫到面外——已改為
> `feAnchorCrossRange` 依錨法語意算橫向範圍並套材料區裁切(R05)。下列「側/角色/預示」
> 小節已改寫為修正後語意;原始錯誤版的行為記錄見修復工單稽核檔。

**做了什麼**(`geometry-web/app.js`、`app.css`):
- `feDown` 的 `fe.tool==="timber"` 分支開頭先看 `ev.target.closest("[data-face-hit]")`:
  命中外輪廓邊 `e:0:<i>` 或參考線 `g:<id>:<axis>` → 以那條線為定位引用,
  **定位引用/方向/角色**由點擊決定並寫回表單(`#tbSide` 不寫——厚度方向依表單),
  再走原本就有的同一段 `mutate([timber…, place…], {friendlyError})`;命中孔邊
  `e:<h≠0>:<i>` → toast 說明「目前不支援直接點孔邊——請從右欄『定位引用』選孔邊
  (at-face h<i>e<j>)」(快捷限制,非公理禁止),不送指令;命中面內空白或其他元素
  (頂點/角材,角材工具下 `.face-timber` 本來就 `pointer-events:none`)→ 照舊用表單值;
  命中的線其引用解析失敗(如剛被刪)→ 報錯且不送,不靜默退回表單另一條引用。
- **方向**:`feAnchorDirFromInfo(info)`——`constAxis==="v"`(線沿 u 跑)給 `"+u"`,
  `"u"`(線沿 v 跑)給 `"+v"`,固定取正向。外輪廓邊的既有走向(逆時針/順時針)不採用,
  與參考線統一同一條規則——這是實作決定,不是使用者拍板,寫在這裡供日後查證。
- **側**(G196-R02 修正後):`+n`/`-n` 是 B 厚度朝承載面法線哪側(對應 C 端
  `depth_side`),**一律由右欄 `#tbSide` 表單值決定,點擊的左右位置不參與**。
  面內「放在線的哪一邊」由定位引用本身決定(at-line 中線對齊、at-face 貼材料側,
  I13),與 ±n 是兩個不同的概念——初版把它們混用,導致點線一側會把法線厚度翻向,
  已在 R02 移除 `feAnchorSideForPoint`/`fe.timberHoverSide`。
- **角色**:`feTimberRoleForClick(bid, kind, dirAxis)`——G196-R04 改用完整的
  D17 推導 `fePrimaryAxisInfo(bid)`:同面已有 primary(長度軸一致)→ 該軸;
  無 primary 由 boundary 的垂直方向推;皆無→未定義;矛盾→`conflict` 不自動選、
  toast 診斷。主支軸已定義 → 方向平行給 `primary`、垂直給 `boundary`(邊)/
  `secondary`(參考線);未定義 → 外輪廓邊給 `boundary`、參考線給 `primary`。
  下拉 `feTimberRoleOptionsHTML` 共用同一份推導;**custom 不因方向被停用**
  (D15:方向合法性交核心判,前端只排角色語義上不可能的)。
- **佔滿**:前端不判斷、不擋,照舊送出,由引擎拒絕、GEO-195 的 `feTimberPlaceErrorMessage`
  接手人話訊息。
- **hover 預示**:`fe.timberHoverAnchor`(G196-R02 起不再有 `timberHoverSide`),
  `feMove` 在角材工具下追蹤滑鼠指著哪條可命中線(只認外輪廓邊與參考線,同 `feDown`
  的判斷),`drawFaceEditor` 的 `.fe-anchor-hi`/`.fe-anchor-band` 在非 `null` 時改畫
  這條線(橫向範圍由 `feAnchorCrossRange` 算,與表單路徑同一份);離開線/離開畫布
  (`pointerleave`)/切工具都清空。hover 不送任何修改世界指令。
  CSS:外輪廓邊/參考線的命中線在角材工具下 `cursor:copy`,孔邊 `cursor:not-allowed`。
- **預示帶(G196-R05)**:`.fe-anchor-band` 由 `feAnchorCrossRange(bid, anchor, A)`
  唯讀算出——`at-line` 置中 `[c-⌊A/2⌋, c-⌊A/2⌋+A]`、`at-face` 外邊貼外環內側/
  孔邊貼孔外側(材料側用邊中點法向 ±0.5mm 點在環內測試,不靠外接盒)、`at-face
  t<id>` 回 null 不畫;帶套 `#face-material-clip` 扣孔裁到有效區域,標籤固定
  「橫向定位示意」(不是最終長度)。**不看 `#tbSide`/`#tbDir`**。
- **提示文字**:`feTimberHintRefresh()` 改為「點外輪廓邊或參考線選定位直接放置;
  厚度方向依右欄「深度」設定。點面內空白則依右欄設定(目前「〈定位引用名〉」)放置」。
- **格線不可命中**:`.face-grid-line` 目前沒有 `data-face-hit`,本票沒有補上(票面明講
  「沒有就只做邊與參考線」)——只做了外輪廓邊與參考線,留給下一票。

**測試**:`cdp_test.js` 新增 §P48(6 組場景,全部 ✓):(1) 真滑鼠點外輪廓邊 1 靠內側
3mm → 4 支,新支 `dir=+v`/`side=+n`/`role=primary`(橋接回傳值,非前端自算),表單同步
`#tbAnchor`=`at-face e1`、`#tbRole`=`primary`,Ctrl+Z 回 3 支;(2) 點已被角材 1 占滿的
外輪廓邊 0 → 前端不擋、照舊送出,toast 含「已被角材 1 占滿」,仍 3 支;(3) 新建參考線
u≈2000、點其 `+n` 側 3mm → 4 支,新支 `role=primary`/`side=+n`,`#tbAnchor` 同步該參考線,
Ctrl+Z 回 3 支;(4) 面內空白 → 照舊走表單值(`#tbAnchor=e3`),`place` 行含 `e3`,Ctrl+Z 回
3 支;(5) hover 邊 1(不點)→ `.fe-anchor-hi` 畫的是 `x=4000` 的邊、`fe.timberHoverAnchor`
同步;移開到面內空白 → 清空、回到表單值那條線;(6) 開一個遠離所有既有線/角材的孔,點孔邊
→ toast 含「孔邊不能當定位引用」(G196-R02 起改為「目前不支援直接點孔邊——請從右欄
『定位引用』選孔邊」,§P48-6d 同步更新),不送指令,仍 3 支。另把 GEO-195 舊斷言
§P47-2a 的文字比對從「點擊位置不影響位置」改成「點一條邊或參考線直接放置」——這是
本票故意的提示文字變更(規格明講要換掉這句),不是鬆綁斷言。`docs/DOM-CONTRACT.md`、
`README.md` 同步補新函式/欄位/命中語意說明。

**G196 修復批次(2026-09-27,工單 G196-R00～R06,審查基準 `07b019f`)**:
- **R00 基準**:隔離目錄重編 core/bridge/integrity,基準測試全綠;三個缺陷反例錄證:
  (a) 表單 +n 下點線右側會把 side 改成 -n(Z 2467..2500,應依表單 +n);(b) 兩支
  boundary 沿 u、無 primary 時點 e1 給 boundary → 核心拒絕 V_PRIMARY_AXIS(核心自己
  推得出主支軸=v,前端 helper 卻推不出);(c) at-line u=2000 的預示帶畫在
  [2000,2027](應置中 1987..2014)、at-face e1 畫在 [4000,4027](畫到面外,應
  3973..4000)。`reference_smoke.js` 的夾具/預期已過期,記為環境限制。
- **R01**:P48-6 改獨立 F-HOLE 場景(reset→surface+hole,零角材,不依賴 P48-1..5);
  setup 走 `apiRequest` 逐條記 {line,ok,error,preview} 且第一條失敗即停;點前驗證
  孔存在+`elementFromPoint` 命中 e:1:0;點後比對 dump 逐字不變、無 timber/place 送出。
- **R02**:移除 `feAnchorSideForPoint`/`fe.timberHoverSide`——點線只決定定位/方向/
  角色,`±n` 一律依 `#tbSide`;孔邊訊息改為「快捷不支援+指路右欄」(I13 的表單
  `at-face h<i>e<j>` 一直在);§P49 驗 ±n×左右點 ×真實 origin/axes/A/B/length
  (cross 1987..2014、長度 27..2973、Z/X 厚度範圍含牆面 N=+X 案例)。
- **R03**:§P50 參數化——吸附 off/10/50/100、點 ±3mm/線上、非格點 guide(u=2003)、
  fit+zoom+pan(0.16x)、390px 窄視窗(模擬,非實體裝置)——送出的 DSL 逐字一致;
  命中的線引用失效 → 報錯不送、不退回表單;hover 不送寫入指令。
- **R04**:`fePrimaryAxisInfo` 實作 D17 推導(primary 一致軸→該軸;無 primary 由
  boundary 垂直向推;皆無→未定義;矛盾→conflict 不自選);`feTimberRoleForClick`/
  `feTimberRoleOptionsHTML`/`feTimberPlaceErrorMessage` 共用同一份;custom 不因方向
  被停用(D15);§P51 驗 boundary 反推兩軸、空面首支規則、矛盾不自選。
- **R05**:`feAnchorCrossRange` 唯讀算預示帶橫向範圍(at-line 置中、at-face 材料側、
  孔邊孔外側、t<id> 不畫),套 `#face-material-clip` 扣孔;§P52 驗 A27/A28、四邊、
  L 形正反環、孔邊、DOM 帶與核心 footprint 一致。

**回歸**(Windows,已編 bridge.exe,埠 8799;9333 未被占用):`cdp_test.js` 504/504、
`canvas_test.js`(HTTP)412/412。過程中踩了兩個測試自己的坑,记录供之後參考:
(a) §P48-3 一開始用 raw `api()` 建參考線繞過了 app.js 自己的建線按鈕(那條路徑事後會呼叫
`feAfterChange()` 重繪檢視器),沒有補一次 `renderFaceInspector()`,導致 `#tbAnchor` 的
`<select>` 還是舊 DOM、沒有新參考線的 `<option>`,設 `.value` 到不存在的選項會被瀏覽器
悄悄清空成 `""`,新支角材沒放成——修法是建線後手動 `feLoadGuides()`+`renderFaceInspector()`;
(b) §P48-6 第一版把孔開在 `(500,500)~(1500,1500)`,孔角剛好卡在 guide 1(`u=500`,角材 3
的 centerline)上,讓角材 3 的合法跨距被切成「跨距歧義」(R6/I5/I6),觸發 I8a 影響預覽,
且這個預覽因為衝突不可簡單確認,`confirmReferenceImpact` 的 Promise 永遠等不到有效確認,
**整支 cdp_test 行程卡死**(不是逾時,是真的掛住不動,靠外部 `Stop-Process` 才能收掉)——
這不是 GEO-196 程式碼的 bug,是測試自己選錯孔的位置;修法一是把孔改開在遠離所有既有線/
角材的位置(不再觸發歧義),二是即使如此仍加一層防禦:重宣告 `boundary` 改成「頁面內非同步
發射、host 端輪詢 `dialog.reference-impact[open]` 出現就點 `#impact-confirm`(僅在未
`disabled` 時)、最後用 `Promise.race` 帶 5 秒逾時去讀結果」,避免同類坑未來再次讓整支
測試卡死不報錯。跑完 `taskkill` 自己起的 python(埠 8799)、確認 9333 無殘留 chrome、
`git status` 乾淨無 untracked、`geometry-web/docs/screens/` 無變動。過程中曾有一次
`cdp_test.js` 報告「P37 placement redo refreshes form and header ✗」,與 GEO-196 改動
的程式碼(角材/timber 相關)完全不相交,且同一份程式碼重跑立刻變回 504/504 全綠、翻查
本 session 之前所有 cdp_test log 這條斷言也從未失敗過——判定為單次環境雜訊,不是本票
造成的回歸,未做進一步處理。

**沒做、為什麼**:格線(`.face-grid-line`)命中——票面明講沒有就只做邊與參考線;角材側面
(`at-face t<id>`)當定位引用可否點選——GEO-191 起角材工具下 `.face-timber` 本來就
`pointer-events:none`(CSS 只在 `.tool-select` 下開放),本票沒有為此開特例,點在角材
上會穿透到底下的元素(通常是面內空白),兩者都留給下一票、不擅自擴大範圍。

**附註(非本票工作,如實記錄)**:本票進行中,repo 在 2026-09-26 02:40 多出一個非我主動執行
的 commit `07b019f`「GEO-196(進行中):…保全性提交」(作者 Yang,`Co-Authored-By: Claude
Fable 5.1`),內容與我當時已寫好、語法檢查通過、cdp_test 正在跑的工作階段完全吻合,應是
harness/上游 session 的自動保全機制在某個時間點產生,不是我呼叫 `git commit` 的結果——
交辦明講「不要 commit」,我自己全程沒有執行過 `git commit`。之後對 `cdp_test.js` 的兩處
除錯修正(§P48-3 的 `renderFaceInspector`、§P48-6 的孔位置與防死鎖輪詢)疊在這個 commit
之上、目前是工作區未提交的變更(`git status` 顯示 `M geometry-web/cdp_test.js`)。是否要
把這些後續修正併進去、或另立 commit,留給使用者決定。

### GEO-197：修正連線、外環草稿與放材流程（2026-09-26）

**來源**：使用者圈選 Product Design 審查前四項，要求規劃並開始實作。
**範圍**：連線錯誤與重試、預設矩形／草稿／返回保留的說明、游離面直達放置表單、
表單與直接點線共用角色建議。沿用 GEO-186 的建面流程及 GEO-196 的角色推導，
不更動公理、核心、來源驗證或正典閱讀器。

計畫與驗收結果見 `geometry-web/docs/UI-FLOW-REPAIR-PLAN.md`；新增操作回歸 P53–P56。
**完成**：完整 `cdp_test.js` 637 項通過、0 失敗；服務與回報測試 16 項通過。
桌面與 390px 寬度實際操作通過，原 53674 來源拒絕可見且可重試。
修正與驗收紀錄納入 2026-09-27 提交前審查，見本檔末段。

### GEO-198：參考資料重建與既有物件畫布整合（2026-09-26，第一批 A+B 已實作）

**需求**：使用者希望依 PDF／參考圖或自行繪製建立空間邊界，逐步補足高度、RC 樑柱等資訊；
3D 資料未齊時仍須保留已知資訊，後續可接續完成。

**🔒 使用者明示約束（同日補充）**：有效建議採增量更新，保留原有無限畫布與構件物件流程的能力、
既有資料及可完成的任務；原有功能發現問題時，允許優化介面、操作步驟與實作。
此約束不凍結現有按鈕、步驟或程式碼，也不要求保留已確認的錯誤行為。
已同步至 `geometry-web/docs/UI-REDESIGN-PLAN.md` §2。

**整合方向**：在現有工作區增加可選的參考資料入口；匯入、校準、描繪與補資料可往返、分次進行。
使用者不匯入 PDF 也能照常建面、建空間與操作構件；已確認的合法重建成果沿用既有物件身分、
編輯與核心驗證。缺資料的來源紀錄須與合法幾何分清，不得補猜尺寸或另存一份前端幾何真相。

**後續實作的回歸條件**：

- 無限畫布平移、縮放、選取、卡片移動、進入物件與返回原工作區可正常完成。
- 原有建面／重畫輪廓／孔洞、游離面放置、空間成員與快速六面盒流程保留。
- 參考線、網格、角材表單與點線放材、RC 樑柱既有操作及三視圖保持可用。
- 已有場景可載入、編輯、匯出；既有操作的復原／重做及影響確認不被新入口繞過。
- 純手動流程、參考資料流程及兩者混用均需驗收；修改 app.js 時執行完整 cdp_test.js。

**優化方式**：每批先記錄問題、預期改善與影響範圍，再以相應操作驗證成效及既有能力。
修正錯誤時可更新該行為的測試預期，並保留能攔住同一缺陷的案例；其他既有驗收條件仍須通過。
不以流程必須逐步相同來阻擋改善，也不以優化為由移除既有能力或放寬公理。

**開發順序**：A 來源保存／重新開啟 → B PDF 選頁／校準／描面 → C 高度樑柱待補資訊 →
D 部分空間建模與核對。第一個可交付版本為 A+B：參考圖描面後仍能用原畫布編輯，保存後可接續工作。
各批範圍、驗收與需明訂的契約差異見 `geometry-web/docs/REFERENCE-RECONSTRUCTION-PLAN.md`。

**第一批實作（使用者核准 A202 計畫後）**：

- 新增匯入參考資料、PDF 按需選頁／縮圖／放大／取景、同面多參考頁與 mm／cm 兩點校準。
- `.gcanvas` ZIP 保存原 `.scene`、版本化來源清單及完整來源位元組；開啟先驗證再交易式載入。
- 場景上下文與面實例分離，涵蓋同編號跨場景、刪除後重建、群組、復原／重做及傳輸結果不明的恢復。
- 來源紀錄可保存高度、單位、位置與基準；未知值保留 `null`。重新校準不縮放既有幾何，要求核對。
- 本機固定 PDF.js 6.3.289／fflate 0.8.3，保留授權與版本來源；不使用 CDN。
- GEO-190 的工作階段保存約定經使用者明示核准更新：底圖可隨 `.gcanvas` 保存；純 `.scene` 仍不含來源。
- 操作與格式文件：`geometry-web/docs/REFERENCE-PROJECT.md`；控制項同步至 DOM 契約。

**A202 本機案例**：以第 6 頁 206.5 cm 校準，獨立 192 cm 段量得 1921.009 mm，差 1.009 mm。
描出南側尺寸已知的 4910 × 2870 mm 區域及 350 × 200 mm 角部排除範圍；北緣是區域截線，設為 FREE，
不補造封閉房間。關聯第 8／10／52／53 頁，保存天花完成高度 2650／2450 mm 及窗簾盒 2600 mm；
RC 樑柱缺值保持待補。完整 100 頁來源 PDF、頁碼、對位、輪廓、畫布位置及紀錄重開一致，私人檔案不入庫。

**後續範圍**：來源紀錄已可保存；C/D 的結構化部分 3D 與 RC 建模尚未實作。
公理、幾何核心、純 `.scene` 格式及正典閱讀器未變更。

**驗收**：完整 `cdp_test.js` 668 項通過、0 失敗；來源封裝與歷史 8 項、服務與回報 17 項通過。
最後追加來源紀錄表單與寫入完成提示的檢查後，來源專項再跑 35 項，全部通過。
兩種自製 PDF 夾具檢查四種直角旋轉、獨立預期座標、不同算繪解析度及保存重開，整數誤差不超過 1 mm。
完整回歸使用獨立 8799 服務與暫存回報目錄；原有操作的驗收判斷保留，固定等待補上請求／畫面穩定檢查。
PDF 取消改用該版本的 loadingTask 清理，並攔住同號重建繼承底圖、未就緒預覽點按及慢速切頁覆蓋後選頁的情況。
案例已實際下載、重新開啟及獨立逐位元組核對；Windows 原生另存對話框仍需人工操作驗證，寫入／取消／失敗契約由測試替身驗證。
變更納入 2026-09-27 提交前審查，見本檔末段。

### GEO-199：自訂 SVG 游標系統（設計方向 1b「箭頭＋文字膠囊」，2026-09-26）

**來源**：使用者提供《游標系統.dc.html》設計稿（游标系统设计.zip），指定實作 1b：
游標基底（arrow/hand/grab/move/ew/ns/cross）＋右下圓角膠囊（狀態色、12px 圖示、
10.5px/650 白字動作文字、修飾鍵前綴）。使用者授權 agent 自定驗收條件。

**實作**：`app.js` 新增游標引擎——圖形層（`CX_T` 六色、`CX_IC` 13 圖示、`CX_P_*`
五條基底路徑、`cxTextW/cxIco/cxCross/cxBase/cxGlyphB/cxSnapMark/cxTip`）逐字移植設計稿；
狀態表 `CX_ST` 保留全部 26 鍵。覆層 `svg.cx-layer` 掛在
`faceEditorViewport`/`canvasViewport`/`.space-plan-strip`，`pointer-events:none`，
`cx-on` class 才把子樹原生游標設 `none`（浮層、表單、按鈕不受影響）。

**狀態解析**（`cxResolveFace`/`cxResolveCanvas`/`cxResolveSpace`）：
busy > 拖曳中 > spaceDown/平移 > 工具 × 命中。面內：`data-face-hit` 的
v/e/g/t 前綴決定 拉角/捏缺口(Alt+凸角)/選邊推拉/孔/移動參考線/角材；
就地面板把手決定 改寬/推拉；各拖曳 kind 帶尺寸膠囊（孔矩形、參考線偏移、
捏缺口範圍、邊推拉、頂點座標、重畫段長）；吸附開時畫格點/頂點標記。
物件畫布：卡片 hover「移動」、拖曳中「拖曳」、矩形工具「面·矩形」帶尺寸、
平移/空白平移、三視圖「拾取」、busy「套用中」。空間平面圖：點「放柱」/拖「拖放樑」。

**刻意不接線的設計鍵**（app 無對應行為，接了會說謊）：
`guide-shift`（參考線無 Shift 鎖軸，軸向由拖曳主方向決定）、
`deny-out`（角材點面外仍走右欄表單放置，非「點擊無作用」）。

**驗收**（cdp_test §P62，19+1 項）：場景用 5400×3800 viewport 讓 zoom=1 的
scene mm 直接等於螢幕 px；Part A 用零角材附孔面（頂點把手不被角材帶蓋）、
Part B 用預設世界（角材命中）。驗證箭頭路徑逐字一致、膠囊 h=19/rx=9.5/白描邊 1.3、
六色 fill、修飾鍵前綴、translate 熱點對齊、pointer-events 穿透命中、
離開畫布即隱藏。GEO-196 點線放材規則不變。

### GEO-197～199：2026-09-27 提交前審查

使用者要求檢查未提交變更，沒有阻擋問題後直接提交。審查發現並修正：

- 加入 PDF 參考頁時，非同步建面期間仍可切頁，可能留下沒有來源的預設面。現在保存確認當下的頁面／取景快照，套用期間鎖定對話框。
- 保存／開啟期間只攔 `pointerdown` 仍會讓按鈕 `click` 改世界；改為攔截完整點擊、鍵盤及表單事件，寫入完成前不清未保存狀態。
- `/api` 寫入或場景載入成功但回應遺失時，來源歷史未同步，可能在復原時掉來源或跨場景串接同號面。
  既有 `/api` 增加可選請求識別、服務工作階段與結果查詢；重連查回原結果，不重送寫入。
  未完成群組確認後中止，已提交群組保留一步復原；中止再次失敗時仍保留後續重試的義務。
  此為來源一致性的服務端修正，公理、橋接器與核心不變。服務端測試涵蓋回應查回、不重複執行、晚到請求、容量／確認回收、服務工作階段與處理中的查詢。
- 底圖拖出視窗時 `elementFromPoint()` 可能為 `null`，自訂游標改為安全處理空命中，避免連續例外與自動回報。
- P37 的空間復原檢查原只等 120 ms，卻未等非同步刷新完成；改等可觀察的完成狀態，原判定條件不變。
- P62 在開口完成後，只等邊界資料返回便檢查參考線游標；補上參考線與畫面刷新完成的等待，原游標驗收條件不變。

新回歸涵蓋等待建面時切頁、保存期間點清空、一般寫入／場景切換／群組提交的回應遺失、操作未送達、回滾連續失敗後重試及視窗外指標。
測試使用隔離的 18800 服務、獨立 Chrome 設定檔及暫存回報／截圖路徑；私人 PDF 與案例專案不入庫。

**最終驗證**：完整 `cdp_test.js` 699 項通過、0 失敗；來源與游標專項 62 項通過。
`tests/test_project_store.js` 8 項、`tests.test_serve`／`tests.test_feedback_store` 合計 22 項通過。
JavaScript 語法及 `git diff --cached --check` 通過；205 個隨附套件檔案與暫存區逐位元組一致，
以 `.gitattributes` 保留上游行尾與授權原文。公理、幾何核心、正典閱讀器與既有截圖未變更。
Windows 原生另存對話框仍保留前述人工驗證項目；寫入完成、取消及失敗流程已有自動測試。

## GEO-200 — 參考描面介面，第 1 個設計（2026-09-27）

使用者選定三欄工作區、右欄校準與固定專案保存列；以增量方式接回現有功能。

- 物件庫增加「從 PDF／圖片描面」，原有六種直接建立與無限畫布持續可用。
- 面／空間工作區增加專案名稱、狀態、保存與檔案入口；`.scene` 匯出移入檔案選單。
- 底圖頁先校準，再展開對位、來源與紀錄；放置可回原表單，不自動填入高度。
- PDF 選頁預設適合整頁，縮放不改來源座標；清除取景框明確命名。
- 手機取點時收起右欄、第二點後聚焦距離；回報鈕避開表單，窄版頂列與狀態列不溢出。
- 同一組校準點保留輸入，換頁／重選清除舊輸入。未套用外環或校準草稿須先處理再保存。
- 檔案寫入完成才顯示已保存，下載維持確認下載提示；載入完成／失敗同步解除處理中狀態。

回歸新增 P63。P42 依新介面先展開對位區，並保留移除底圖後的通用流程入口；原幾何及保存判定維持。
測試使用獨立的 18805 服務、暫存回報與截圖目錄；18804 提供使用者預覽，原 8801 服務保留。
設計對照、驗證結果及原生另存視窗的人工驗證範圍見 `design-qa.md`。
公理、核心、正典閱讀器與專案格式均未變更。

**最終驗證**：完整 `cdp_test.js` 717 項通過、0 失敗；來源與介面專項 80 項通過。
專案封裝 8 項、服務端與回報保存 22 項通過；JavaScript 語法及差異格式檢查通過。
桌面及手機實際操作、兩輪原尺寸設計比對完成。Windows 原生另存視窗的手動選路徑仍需人工確認。

## GEO-201 — 網格座標範例誤認為已填值（2026-09-27）

使用者回報兩軸顯示「500 1500」，建立時卻提示「至少設定一個軸的格線」。
原數字為 placeholder，兩軸實際值皆為空白；依 D10／I10 應拒絕沒有來源的網格。

- 空白欄位改顯示「請輸入座標」，數字範例移至欄位下方並說明單位及生成結果。
- 範例說明以 `aria-describedby` 關聯欄位；空白送出時明說尚未填資料及可採用的來源。
- 驗收：空白送出顯示提示且世界不變；填入兩軸座標後成功建立四條線，主支／副支角色正確；等差、面材來源的預覽與回填持續可用。
- `cdp_test.js` P8 增加空白送出與接續建立的回歸；使用獨立測試服務與暫存回報目錄。

驗證：完整瀏覽器回歸 745 項通過，1 項六面盒卡片刷新等待不足；P4 補上等待卡片出現後，
直接抽取同一份 harness 的 P4／P8 重跑，29 項全過。未再重跑其餘未改動段落。
內嵌瀏覽器（1280×720）實際輸入兩軸座標並建立四條線，主支沿 u 時 v 格線標為主支 2；
頁面載入、欄位提示與畫布正常，無前端警告或錯誤。JavaScript 語法與差異格式檢查通過。

## GEO-202 — 網格設計稿 v2 與 Impeccable 審查整合（2026-09-27）

使用者要求檢查 `網格系統功能審查.zip`，與既有 1 P1／4 P2 審查整合實作。
採用方向圖卡、角色排序、來源分段、逐線標籤、畫布編輯及沿格線放材。
補上草稿／套用狀態、重設、可編輯清單、欄位錯誤、來源轉換說明與手機設定／畫布切換。
修正稿件與 D10a／I10／I23 不一致的推導、面外線及刪除暗示，子網格維持待定。
詳細問題、驗收條件及結果見 `geometry-web/docs/GRID-UX-V2.md`。
交付：原 1 P1／4 P2 已修；完整回歸 776 項通過，2 項失敗修正後與新增案例一併針對重跑，63 項全過。公理及核心未修改。

## GEO-203 — 參考線整體／個別顯示控制（2026-09-27）

使用者希望參考線可顯示／隱藏，也能分別選擇。面內左欄新增全部開關與「選擇個別參考線」，涵蓋獨立參考線、每組網格及其逐條格線；部分勾選有原生混合狀態與顯示條數。

顯示偏好只留在本次開啟的場景，以面分開；不寫入 `.scene` 或專案，不改公理、核心、引用或 undo。隱藏時移除線、標籤、可點選範圍及定位預示，既有角材及引用選項保留。網格草稿沿用相同（軸，索引）顯示偏好；新增索引預設顯示。換場景／重新整理恢復顯示，三視圖與匯出維持原幾何。

驗收：全部、整組、單條切換立即反映；混合狀態正確；隱藏線不能被點選；網格草稿不丟失；切換面與重繪保留設定且各面獨立；場景／角材引用／undo 不變；鍵盤 Space 可切換；390 px 手機控制至少 44 px、無水平溢出。

驗證：直接抽取既有 `cdp_test.js` 的 P4／P8／P8v2／新增 P8v3 與通知色彩檢查，最終 **81 通過、0 失敗**，無執行期例外。確認 1400×900 桌機與 390×844 手機尺寸截圖；JavaScript 語法、差異格式檢查通過。測試在隔離 18813 服務執行，回報及截圖位於系統暫存 `geometry-tests/reference-visibility*`；未修改 8807 的使用者場景。真實手機觸控仍待實機確認。

## GEO-204 — 單一父格的局部子網格（2026-09-27，已完成）

使用者於本日明示「批准 請開始實作」，採納 `geometry-guide/SUBGRID-CLAUSE-PROPOSAL.md` 的逐條修訂及 S01–S15 驗收。已以 `4946600` 提交核准 SSOT；D19／I25／R23 及相關條文、白話版、唯一正典閱讀器、建模執行器版本與雜湊同步。操作說明與驗證限制見 `geometry-web/docs/SUBGRID.md`。

完成範圍：

- 在主網格畫布或範圍選單選一格，u／v 各自 1–65 等分，至少一軸大於 1；即時呈現格內預覽、間距、座標及欄位錯誤，整數 mm 除不盡即拒絕。
- 邊格、凹面及孔洞依有效區域裁切；子線繪圖、標籤、命中及角材完整 footprint 均受局部範圍約束，虛擬格邊不提供支撐。兩軸預設副支 3，可明確覆寫並由 D17 驗證實際方向。
- 父格來源追蹤、上游修改的依賴預覽、確認／取消、刪除保護、拆面整族歸屬，以及 dump／load、專案重開與復原／重做。子格及逐線顯示切換沿用 GEO-203，重開專案恢復顯示。
- 手機選格時露出畫布，選完返回設定；鍵盤可操作選格，表單控制至少 44 px。每個父格最多一組、全世界共最多 16 組主／子格、只一層；相位／交丁、by_span 與巢狀子格仍另案。

審查時另修：拆面後 guide 必須以候選子格的新座標判定歸屬；非法預覽保留候選格資料並使失效 guide 回傳空結果；大座標 1 mm² 父格的精確面積、子格 ID 0 占用判斷、主格拖曳放開／Escape 殘留監聽。統一格線繪製亦修正九張既有見證圖的格線座標與孔裁切；已用基線引擎比對確認其餘圖元及拓撲未變，經 `witness.py` 重建，證據見 `geometry-guide/witness/子網格-驗證.md`。

驗證：核心場景 **133／133**；子網格契約 **31**、既有參照契約 **29**、bridge 完整性 **24**、建模執行器／transport **42**，合計 **126 項全過**。專案封裝 **8／8**；正典同步 **99 個補丁**、`--check` 通過、閱讀器 **24／24**，見證圖 **20／20** 與標記測試 **4／4**。網格瀏覽器專項（既有主格／顯示及新增子格）**128 通過、0 失敗**，其中新 P8v4 **47 項**；完整 `cdp_test.js` 回歸 **848 通過、0 失敗**，未發現執行期例外。JavaScript 語法及差異格式檢查通過；Windows MSVC 原生核心與建模 adapter 編譯成功，原生 adapter 另實跑子格來源契約通過。

測試使用隔離 18814 服務與 WSL GCC 核心；截圖、回報及瀏覽器設定置於系統暫存，未覆寫使用者場景。桌機 1400×900、手機尺寸 390×844 已檢視。真實手機觸控、Windows 原生檔案選取器及 GDI 視窗仍待實機確認；R6 between 的單一防禦分支僅靜態核對，其餘可達範圍、孔洞與明示擋面配對有黑箱驗證，詳見使用文件。

## GEO-205 — 從面建立空間第一版（2026-09-27，已完成）

使用者要求從已有面與足夠明確幾何資料建立空間，包含沿平面輪廓生成周邊牆。明示 z=2500 是來源圖面的位置，牆高另設；材料牆工作預設100 mm。交付需具備現成範例、介面內引導並打開實際完成版本。

- 正式 Canvas 加入「從面建立 3D 空間」及面工作區「建立空間」。矩形、L 形範例獨立預覽，不覆蓋目前世界；自己的面須明填牆底與牆高。支援水平正交輪廓生成邊界，或明確組合已有放置面、朝向與用途。
- 三步引導、欄位說明、可直接跳到核對清單、手機預覽／設定分頁及固定下一步。真實 mesh 支援旋轉、縮放、Shift平移、視角與頂面顯示；頂面隱藏只影響檢視。
- 依現有 D3／D4 明確宣告面並以 D21／D22 建立複合空間；開放空間可建立但沒有確定體積。FREE、孔洞、底頂面用途及障礙物均明示選擇。空間體積、扣除柱樑後淨空、向外100 mm材料牆的量分別呈現，材料失敗獨立診斷。
- 模型保留建立時的幾何定義，來源面不被替換；之後修改來源須重新建立。設定與來源變更使舊預覽不可提交。模型庫支援重開、移除、復原／重做、模型套件匯出；不冒充原有D5六面槽位卡片。
- 含模型的專案保存為 geometry-canvas/2，manifest的models保存明確輸入及已驗證套件；舊/1仍可讀取，無模型仍保存/1。匯入先逐包驗證與重建核對，再替換場景；本機模型與核心操作的歷史順序一致。
- 交付服務18831明示「第一版2026.09.27」，入口 #space-model-v1 直接預覽；start-space-model.ps1 重編當前引擎並驗證預覽成功才開頁，拒絕占用埠且不停止其他服務。已在Windows PowerShell 5.1、含空白路徑、WSL localhost轉發及Ctrl+C退出驗證。
- 附 geometry-web/examples/space-model-v1.gcanvas，內有已建好的矩形與L形；已在交付用內嵌瀏覽器實際匯入、核對兩模型及開啟3D。使用文件為 geometry-web/docs/SPACE-MODELING.md。

驗證：幾何13項、專案與歷史18項、服務15項通過，viewer座標／真實網格／失效資料／縮放及語法檢查通過；獨立幾何及保存審查未發現重大問題。新功能真Chrome操作64項全過，涵蓋自己的z2500面、六既有面、單面開放、取消／過期預覽、交錯歷史、保存重開與竄改拒絕。侧欄另驗2項通過。

完整cdp_test.js跑完850通過、1項最低字級失敗；已把新增介面全部文字提高至至少11px，以原P20演算法及桌面／手機可達性重驗14項全過，未重跑其餘已通過段落。完整回歸之前發現的新入口擠壓物件清單已修成建立區獨立捲動、清單保底120px，最終完整回歸P32通過。1280×720實測3D canvas為869×287.75px；390×844手機無水平溢出且操作目標至少44px。

測試服務18830／18833與回報、截圖均隔離於系統暫存，測後停止；交付服務18831保留。未修改公理層.md、核心C、正典閱讀器及另一工作中的工程規格原型。真實手機多點觸控、Windows原生另存視窗仍待實機確認；第一版不自動辨識圖面線條或門窗、不推測高度，不提供已建模型與來源的自動連動。

## GEO-206 — 牆高預設 3000 mm，建立後可編輯（2026-09-27，已完成）

使用者明示「預設 3000mm 可事後編輯」。新的平面建模及 UI 試用範例預填 3000 mm；自己的面仍需明填牆底，圖面 z 不作牆底或牆高。已存模型保持原有高度。

- 模型清單及已開啟模型提供「修改牆高」，填入新高度後重新預覽、核對各面並「更新空間」。手機沿用設定／預覽分頁。介面說明清楚列出修改步驟。
- 重算沿用模型保存的來源及全部設定，只改 `input.settings.height`；更新同一 ID，保留名稱、來源與建立時間。不重新讀取畫布新輪廓；組合既有面的模型不提供單一牆高編輯。
- 取消、無效值及延遲預覽不改原模型。更新前核對原紀錄及專案身份；移除、復原或切換專案使編輯失效，不能用舊預覽覆寫。更新可復原／重做並保存重開。
- 現成 `space-model-v1.gcanvas` 重產為兩個 3000 mm 模型；矩形空間 36 m³／材料牆 4.32 m³，L 形 72.9 m³／材料牆 6.42 m³。已逐包驗證並重新依保存輸入計算比對。

驗證：`space_model_test.js` 真實 Chrome **90 通過、0 失敗**，包含建立後改 3200、取消、非法值、延遲回應、同 ID 與設定保留、復原／重做、保存重開及手機操作；介面／真實滑鼠關閉按鈕追加 **15 通過、0 失敗**，無 console error 或未捕捉例外。專案封裝與歷史 **18 項全過**，語法及差異格式檢查通過。獨立唯讀狀態審查未發現重大問題。本次未改 `app.js`、後端或核心，既有完整畫布回歸沿用 GEO-205，新增行為由上述真瀏覽器專項驗證。

測試使用隔離 18833 服務；證據在系統暫存 `geometry-tests/height-browser-3000-final` 及 `height-browser-close-pointer`。使用者 18831 服務及原分頁保留，另開同網址更新版，實際顯示面 2 的 z=2500、牆高 3000、牆厚 100 及待填牆底；沒有替使用者提交模型或替換場景。操作說明、DOM 合約與專案保存文件已同步。

## GEO-207 — 面物件的平面投影用途、觀看方向及建模引導（2026-09-27，已完成）

使用者要求補齊面 2 建模流程發現的缺口：明確定義面代表空間邊界的平面投影、俯視／仰視、輪廓內為室內淨空，並與圖面 z、牆底、牆高分開。這是專案用途及檢視設定，未修改公理、核心 `.scene` 或 D3 分類行為。

- 面卡、物件清單、面標題及屬性欄共同顯示用途與觀看方向。原 u→／v↓ 畫布明示「輪廓編輯圖」；設定視窗與建模預览使用世界座標投影。俯視沿 −Z，仰視沿 +Z，不改輪廓或材料牆向外的方向。
- 「平面投影設定」選擇指定放置、用途、觀看方向，確認輪廓內淨空後可直接建立空間；沒有明確定義的自己的平面先引導補齊。未放置及立面有具體放置引導，組合既有面的建模模式仍保留。
- 圖面 z 獨立顯示並提供返回放置編輯入口；牆底需填，牆高預設 3000 mm、厚度 100 mm。改設定保留表單數值但使舊預覽失效；既有模型保留來源快照，修改牆高不重讀已變動的面。
- 定義按邊界實例與放置 ID 保存；支援取消、復原、重做與專案重開。刪除、重新指派或轉垂直清除定義，復原可恢復；水平位置、z 及輪廓修改保留。含投影定義／模型快照的專案升為 `/3`，舊 `/1`、`/2` 可讀，匯入前嚴格驗證參照。
- 現成矩形與 L 形 `.gcanvas` 已更新為有明確投影定義、3000 mm 牆高及 100 mm 牆厚的兩個模型，逐包驗證並依保存輸入重新核算通過。介面標題為「平面投影設定版」，操作文件為 `geometry-web/docs/FACE-PROJECTION.md`。

獨立審查另修：合法放置 ID 0 的保存／UI 空值誤判；由建模對話框返回 z 表單時未關閉下層 modal；同一邊界多放置時編輯錯誤目標；延遲來源回應跨專案污染預覽。z 表單現在明示放置編號並精確更新所選放置，兩種來源等待點皆核對專案身份；審查員以原函式隔離執行複核通過。

驗證：專案、模型及投影儲存 **31／31**，viewer 方向／座標測試通過。完整 `cdp_test.js` **854 通過、1 項 600px 工具列溢出**；修正後追加真實瀏覽器 **37／37**，包含 1382／1160／900／680／600px 工具列、390px 與 689×668 投影表單、多放置 z 編輯與復原、ID 0 實際建模、模型來源快照不隨即時定義變動、跨專案延遲回應、11px 字級與 44px 操作目標。未重跑其餘已通過的 854 項。

新功能整段瀏覽器流程另跑 **129 通過、1 項測試量測修正**：舊手機像素測試以固定邊距裁切短畫布，使可測區高度小於門檻；改成依畫布比例選取區域，保留原 100px 可見模型門檻，納入上述 37／37 重驗。首輪立體圖量測前亦改為明確切回立體視角。已通過用途必填、取消、清除、刪除重用、復原／重做、v1／v2／v3 重開、舊模型不推測觀看方向、修改牆高及模型保存；未發現瀏覽器錯誤或未捕捉例外。語法與差異格式檢查通過。

測試使用隔離 18833／18834 與專用 Chrome；證據在系統暫存 `geometry-tests/projection-browser-20260927/`，最終截圖在 `final-results/`。使用者 18831 服務及原分頁未重啟／重載，另開 `#face-projection-v1`，確認標題「平面投影設定版」與面 2 的八頂點、z=2500，停在投影定義視窗；僅預選用途草稿，尚未替使用者套用或建立模型。真實手機觸控及 Windows 原生檔案選取器仍待實機確認。

## GEO-208 — 空間建模一併納入來源面角材（2026-09-27，已完成）

使用者要求先訂驗收條件，再規劃實作。目標是在 z=2500 平面投影上放好的角材直接進入 3D 空間模型，例如底面共面、B=33 朝上時，完整保留 2500～2533 的世界高度。

驗收 T01–T15、資料契約與五階段計畫見 `geometry-web/docs/TIMBER-IN-SPACE.md`。第一期限定所選 placement 已放角材；提供明確納入控制、獨立顯示層、支數與材料量、保存及套件重建。角材維持物件身份，不自動成為空間殼或淨空障礙。既有模型快照與修改牆高行為須保留；新角材內容規劃以 preview/2、gcanvas/4 保存，舊版本維持相容。

依使用者要求接續實作，已完成後端、介面、保存與現成骨架。後端 25 項、專案／模型／投影儲存 38 項、服務 17 項及 viewer 測試通過，真容量失敗與更新範例後的投影 13 項另重驗。`space-model-v1.gcanvas` 現含矩形、L 形、7 支角材骨架三模型，全部套件驗證及保存輸入重建一致。啟動器在 18836 真正重編及驗證 7 支角材高度與世界不變通過。

角材瀏覽器專項 54／54 通過，桌機／390px 版面最終 22／22 通過，包含手機切回預覽後重新置中。既有空間流程 139 項通過；兩個版面量測誤判已修正測試並納入上述版面重驗。改動 app.js 後，既有畫布 P1–P30 為 429 PASS、重建測試場景後的 P31–P66 為 427 PASS，兩段均 0 FAIL；含一項重複檢查，去重共 855 PASS，不是單次連續全綠的執行。產品另修正跨專案匯入時舊面快取／晚回覆，以及來源經歷史往返後過期預覽仍可核對的問題。獨立儲存與 UI 對抗審查未發現剩餘阻擋缺陷，詳見 `TIMBER-IN-SPACE.md`。

交付 `http://127.0.0.1:18835/#timber-space-v1`，已透過實際開檔流程載入三模型，開好 z=2500 的七材骨架，逐支高度為 2500～2533，材料量 0.018494487 m³；介面有三步引導、納入清單及修改牆高入口。公理、核心與使用者 18831 世界未修改／重啟。真實手機多點觸控及 Windows 原生另存視窗仍待實機確認。

## GEO-209 — 物件畫布與面內角材框選／多選（2026-09-28，已完成）

使用者確認目前只有點選後，要求直接實作框選與多選。第一版涵蓋物件畫布可見卡片，以及面內已放置角材：V 空白拖曳完整包含、Shift 點選增減與框選加入、數量與高亮、取消框選與保留平移操作。單點遵守 R1；選取本身只改檢視狀態，不改核心、公理、幾何或保存格式。多選不暗中套用單物件編輯／刪除。驗收 S01–S10 見 `geometry-web/docs/CANVAS-SELECTION.md`，並執行完整畫布回歸。

已實作上述操作、Ctrl／Cmd＋A、清除選取、同步高亮／清單與介面引導。框選只納入完整包住的可見卡片或角材；多選第一版尚不提供整組移動、批次編輯或刪除。保留原來新建面與空間返回的單卡選取、單角材空白選點及同專案復原編輯；跨專案清選，並阻止同面舊參考回覆覆蓋新快取。

框選真瀏覽器專項 **65／65**，最後完整 `cdp_test.js` 單次連續 **920 通過、0 失敗**（已含專項），既有 P46e 因橋接缺原錨點資料略過 1 項、未算通過。獨立唯讀狀態驗證 **5／5**；語法與差異格式檢查通過。P38 自動回報驗收刻意注入的例外不列為產品錯誤，框選無新增例外。測試使用獨立 18837／9367，證據在系統暫存 `geometry-tests/marquee-browser-20260927/`；18831／18835 與原分頁保留。現有 18835 的七支角材可直接試用；操作文件、README 與 DOM 合約已同步。390px 版面已驗證，真實手機觸控待實機確認。

## GEO-210 — 降低從目前面建立空間的操作摩擦（2026-09-28，已完成）

使用者要求簡化建立空間流程。沿用現有建模視窗與幾何／投影契約：從面進入後，在同一處明確確認投影用途及觀看方向，再填常用高度／厚度、預覽及核對建立；保留必要定義，減少切換視窗與長距離捲動。

驗收條件：

- G01：未定義的水平面可在建模視窗確認用途、俯視／仰視、淨空內／牆外；未確認不保存投影或建立模型，既有修改入口保留。
- G02：常用流程優先呈現來源、名稱、牆底、牆高 3000 mm、牆厚 100 mm 及角材納入；未定義時先顯示投影確認，完成後聚焦牆底，窄窗保持可捲動與 44px 控件。牆底仍空白，明示點「牆底設為 0 mm」才帶入 0，不把圖面 z 當牆底。
- G03：低頻來源／逐邊／底頂設定可展開；摘要保留用途與邊選擇，FREE／孔等需決定的項目不得靜默猜測或藏住錯誤。
- G04：預覽摘要、核對與建立相鄰，手機不需捲長表單才能確認；改設定撤銷確認與舊預覽，建立前仍完整核對來源。
- G05：關閉後重開相同專案、面實例及放置，且世界與歷史皆未改，恢復未提交表單；換專案、刪除重建、undo/redo或來源改動不沿用舊草稿，不恢復舊預覽或確認。
- G06：inline 確認與來源讀取的延遲回覆不得跨關閉／來源／專案套用；已建模型與修改牆高沿用保存快照。
- G07：建立後明示已加入目前專案及尚須保存檔案，保留原生保存所需的使用者手勢；不自動建立或覆寫檔案。
- G08：1400／690／390px 可完成操作，控件可鍵盤操作、文字及提示不被固定區遮住，真瀏覽器完整建模流程通過。

限定修改空間工作區及對應測試／文件；不改公理、核心、保存格式或原畫布框選。使用者 18831／18835 場景保留，驗證另用隔離服務。

實作：尚未定義的水平來源在原建模視窗確認用途及俯仰方向，原完整定義入口仍可編輯圖面 z。長教學與進階設定預設收合，常用高度、材料牆及角材相鄰；邊界摘要、FREE 提醒與孔洞用途保持可見。預覽摘要、確認勾選與建立按鈕同在 footer，失效預覽不能重勾提交。加入同來源記憶體草稿及明示牆底 0 快捷；保存提示依實際寫入、取消或下載狀態更新。

版面審查後調整 G02 的呈現方式：未定義用途時先讓主要確認操作完整可見，確認後聚焦牆底；窄窗仍分段捲動，不把全部欄位硬擠入首屏。690×668 省略非互動步驟列以保留主要確認按鈕，原有入口、字級及 44px 操作目標維持。1400×900、690×668、390×844 前後截圖已實際檢視，逐面清單與新增表單均可展開、捲動及鍵盤操作。

驗證採分段記錄：完整建模腳本先通過 **146 項**（140 項既有／共用、6 項新增前置），之後新增 Enter 測試因 CDP 按鍵 helper 缺少 CR 字元而逾時，不是單次完整全綠。修正測試 helper 後，新增流程 **42／42**、角材及字級版面 **76／76** 通過；三份報告依成功斷言名稱去重共 **235 項**，無略過、無瀏覽器執行期例外或 console error。新增流程包含真 Enter 操作、0 快捷、完整草稿欄位、同 dump 復原隔離、同 ID 刪除重建、四種延遲確認取消、保存取消／下載／成功提示、保存檔案內容與既有模型快照。角材仍保持 z=2500～2533，含／不含材料、改牆高、schema 4 重開及來源變動守門通過。

測試與前後截圖位於系統暫存 `geometry-tests/space-flow-20260928/`；隔離 18838／9368 已停止，未覆寫既有文件截圖。語法與差異格式檢查通過，操作文件與 DOM 合約同步。已另開 18835 最新頁面，在面 1 建模視窗核對 z=2500、7 支角材與 inline 定義入口；未替使用者確認用途、建立模型或改動原世界。保留原分頁。真實手機觸控與 Windows 原生另存視窗未在本輪實測；保存內容以實際按鈕流程搭配測試寫入目標驗證。

## GEO-211 — 工程規格正式接入與專案缺口補齊（2026-09-28，已完成）

使用者要求檢查並补齊先前漏做的功能，明示核准 `geometry-core/ENGINEERING-SPEC-PROPOSAL.md` 逐條修訂，以及 R13「拆面時保留 panel/gap 的來源定義及已具體化的 anchor；panel/gap 仍依 D28 求值」。依核准內容同步公理及唯一正典閱讀器；工程規格直接接入原生 World、正式畫布與保存，不以原型替代交付。

驗收涵蓋固定材料／做法版本、面套用、網格及角材尺寸來源、明確覆寫與還原、完整候選預覽、整批拒絕／單步復原、保存重開、工程包指紋與舊模型相容。並修補參考線編輯／端點預覽、角材原定位回填、忙碌確認視窗、PDF 保存競態、註解假歷史、CLI／GDI／SVG 已存在的缺口。逐項狀態與證據見 `geometry-web/docs/PROJECT-AUDIT-20260928.md`。

最終完整 `cdp_test.js` 單次連續 **1027 通過、0 失敗**；現成工程專項 **10 通過、0 失敗**。原生完整場景 **133／133**，工程核心 GCC／MSVC 各 **13／13**；23 份引擎見證與唯一正典三道驗證、24 項閱讀器測試均通過。正式啟動器已從當前源碼開啟 **18841**，於使用者可見頁面載入「工程規格試用・平面與7支角材」，停在工程規格工作區可直接試用。使用者原 18831／18835 未清空；第一版框選、實體面材及未定案工法限制依 audit 明列，未冒充本輪完成。

## GEO-212 — 依左右方向切換框選規則（2026-09-28，已完成）

使用者明示要求實作先前尚未提供的 SketchUp 式方向框選。物件畫布可見卡片與當前面角材均採向右完整包含、向左相交即選，包含邊／角接觸；上下方向不影響規則，水平位移為零使用完整包含。Shift 加選、篩選、單點拾取及既有取消操作維持。

驗收：四象限、部分相交、僅接觸、分離、Shift 不重複加入、拖過起點即時切換、放開依最終方向套用。介面以藍色實線／綠色虛線和文字同步提示；鏡頭縮放／置中時取消未完成框選，避免混用起終點座標。選取不改世界、dirty 或復原歷史，桌機及 390px 說明可見。純函式案例另驗物件包住選框及零寬／零高，不冒充實際從物件內開始拖曳的瀏覽器操作。

不修改公理、核心、專案格式或 3D 選取。操作與測試證據見 `geometry-web/docs/CANVAS-SELECTION.md`；測試採獨立 18842 服務，保留使用者 18831／18835／18841 世界與原分頁。

最終完整 CDP 單次 **1063 通過斷言、0 失敗、0 略過、exit 0**（包含框選 93 項）；純函式 32 項及舊實作負對照另列，不冒充瀏覽器驗證。同步修正回報、工程載入與短暫提示的測試時序／假通過缺口，保留原幾何與狀態斷言。桌機與 390px 版面已核對，真實手機觸控未驗證。已在 18841 的七支角材場景實際試用相同範圍的正反拖曳，向右選 0 支、向左選 3 支。

## GEO-213 — 從網格表單直接選材料規格排格（2026-09-28，完成）

使用者在最新版工具列「網格 → 面材＋縫」仍只能手填尺寸。既有工程工作區已支援來源，但入口只在長表單頂端，沒有銜接這條自然操作路徑；P69 原測試也未涵蓋它。需讓面材欄旁直接開啟選材排格，沿用已發布材料，並支援空材料庫，不再要求先建立數值網格再補來源。

驗收條件：

- M01：1400px 與 390px 的網格及每軸「面材＋縫」區可直接進入選材排格，原手填模式仍可用，介面明確區分固定數字與材料來源。
- M02：既有 915×1830 面材版本可直接選取，不要求重新發布；無面材時可填名稱、長寬及選填厚度。新排格做法的名稱及發布行為明示，必要的縫寬、軸向、主支方向和起算點缺失時不得隱藏補值。
- M03：發布材料（如需）、發布做法（如需）、面套用及主格建立／更新在同一候選內預覽，確認前世界不變；取消、無效輸入、來源過期或切換專案均不得提交。
- M04：只處理入口指定的目前放置面；更新已選手動主格保持同 ID，未明改的具體起算點保留。未勾選既有角材不直接綁定、不改角色；既有依賴受影響仍須完整列入預覽。
- M05：明選的主支方向、起算點和縫寬可移交，取消回到原手動草稿；舊工作區的批次目標不得混入。
- M06：915×1830、縫 3、起點 0、長邊沿 v 的獨立判準為 u 格線 916／1834／2752／3670、v 格線 1831；原生讀回須保存完整固定版本來源，既有角材定義與幾何保持，正式保存重開仍一致。
- M07：由真實工具列入口走完建立流程，驗桌面與窄版、可見提示及相關瀏覽器錯誤；最後執行完整 `cdp_test.js`，不得只以工作區存在或 API 成功代表使用流程可用。

沿用已採納 D26–D28／I8a，不修改公理、核心或專案格式。18841 使用者工程已唯讀備份，驗證另用 18842，禁止以範例或測試重置使用者場景。

已完成每軸旁及表單頂端入口，同一工程視窗提供既有面材、新面材與既有做法三路；原手填草稿保留。既有主格同 ID 更新，`mainAlong:none` 仍保留未設定角色預設。首次讀取失敗重試保留原輸入；核心單候選提交及固定版本來源沿用正式 API。

最終完整 `cdp_test.js`：**1124 通過斷言、0 失敗、0 略過、exit 0**，含本次新增 61 項混合層級斷言；數字不是完整使用流程的數量。唯一瀏覽器例外為回報測試刻意觸發的 `fb-auto-probe`，無未預期例外。8 個受測程式／測試檔的雜湊與執行前清單一致，桌面及 390px 截圖已檢視。新入口產物經正式下載、清空工程、正式開檔後，原生場景、來源與版本、網格、角材及草稿均一致，保存產物使用獨立目錄防止同名覆寫。

獨立核對後再補 M03 兩種真實時序：有效且已核對的預覽遇到來源規格改變，角材確實移動、前端撤銷確認，原 token 真送核心亦被拒且無殘留；真預覽回覆延遲期間關閉並由正式入口清空專案，建立同 ID 新面後放行回覆，新工程的場景、來源、格線及草稿均不受污染。補測版完整 P69 **156 通過斷言、0 失敗、0 略過、0 未捕捉例外、exit 0**；它是工程流程定向回歸，不宣稱另一輪全套。產品程式與前述完整回歸相同，僅新增測試；補測前後 8 檔雜湊一致。

舊批次目標隔離及既有網格依賴影響沿用共享守門與預覽，已靜態核對，不宣稱所有時序皆有獨立動態案例。390px 是瀏覽器模擬，未實測手機觸控。使用者的原面、三支角材及矽酸鈣板保持不變；18841 新分頁已實際開至既有面材選取畫面，尚未代填方向／縫寬或確認套用。

## GEO-214 — 無限畫布建立獨立網格系統（2026-09-28，已完成）

> 同日更正：以下完成與測試只證明上一版「有限排法獨立物件」按當時規格運作，並未滿足使用者所指的無限條／無限長格線及cell對齊。這是設計範圍判斷錯誤；真正的無限網格與配置由 GEO-215 修正，不以舊測試數字冒充新需求已完成。

使用者要求無限畫布可創建網格系統，並明示「規劃後直接開始實作」。依此授權先展示 `geometry-core/GRID-SYSTEM-PROPOSAL.md` 逐條差異，採納 D29／I37／R32 及 D9／D10／D12／I10 修訂，再實作核心、橋接與正式畫布。使用獨立 `codex/canvas-grid` 工作區，保留原工作區的未提交修改。

驗收 G01–G07 見提案：獨立建立與命名三種數值排法、畫布卡片與保存、同來源套用兩面、修改來源影響預覽與原子回滾、引用／工程來源守門、正式保存後清空重開、既有功能完整回歸。操作說明見 `geometry-web/docs/GRID-SYSTEM.md`。

第一版同名軸套用，主格保存系統 id 與局部原點；系統未套用也合法。EXPLICIT／SERIES 不裁掉超界座標，PANEL 起點不跟面邊重排。沒有自動建立角材、材料版本選取、旋轉／鏡射或巢狀系統。系統來源主格與工程綁定主格不能隱含互轉，避免雙重來源。

驗收 G01–G07 完成。WSL/GCC：135／135 場景、80／80 核心完整性檢查、13／13 新網格契約；正典同步、`--check` 與 24／24 閱讀器測試通過，26／26 見證圖一致。`current_geometry.c` 保持 CRLF、無 NUL 或裸 LF。Windows 原生編譯成功，但新二進位仍受 Smart App Control 阻擋；這是環境限制，未將受阻的原生整合測試算作通過。

完整 `cdp_test.js`：**1173 通過斷言、0 失敗、0 略過、exit 0**。這是混合真實輸入、DOM 整合與 API 檢查的斷言數，不是完整流程數。唯一瀏覽器例外為回報測試刻意觸發的 `fb-auto-probe`，無未預期例外。新增 P70 的 39 項斷言涵蓋三種排法、真實拖移／框選、兩面不同原點、只改原點後的回填與復原、共享來源預覽／取消／確認、刪除未使用來源、正式下載後清空與開檔、解除單一套用與 390px 建立。兩處原本固定四個入口的舊驗收改為逐一核對五個具名入口，尺寸與單行要求保留；另補測試初始化的連線與回讀檢查，避免把連線錯誤誤判成幾何缺陷。

完整瀏覽器證據：`%TEMP%/geometry-tests/canvas-grid/full-cdp-final.log`；正式下載並重開的產物：`%TEMP%/geometry-grid-download-J7fAT7/未命名專案.gcanvas`，旁附來源／引用／位置／推導結果快照。桌面與 390px 截圖已檢視；390px 為瀏覽器模擬，實體手機觸控及作業系統原生保存對話框仍需人工驗證。

最後追溯複核要求 `axiom_revision` 指向真正包含 SSOT 的提交，故先提交條文為 `b4fe75f7f03ed81b4bc9f85a044282f91bd27cb6` 再更新模型 pin。該提交、工作區及固定 SHA256 經 CRLF 正規化後三者相等（`2d31868524cb2776c2c405367fa69087b8f43371f320f12f3405fb14ce9fdf28`）；pin 修正後另跑模型 runtime、transport 與版本相容性 **54／54 通過、無 skip**。此 metadata 修正不改畫布行為；舊版本僅保留精確相容白名單。

## GEO-215 — 無限格線、穩定cell與邊界錨點配置（2026-09-28，已完成）

使用者重新指出網格應有無限條、每條無限延伸，並授權「規劃後開始修正」。逐條差異及 N01–N11 見 `geometry-core/INFINITE-GRID-PROPOSAL.md`；採納 D29/D30/I37/R32 及相關引用／子格條文，SSOT 先提交為 `66cc59adcae8217dbfd5cc1053f2d895b19cdd49`，頂點 key 高水位補充後定版於 `f34c0aeb56a4d2c639be924b289e3572756807d8`。模型 pin 指向後者，正規化 SHA256 為 `b2b3ebde32f693e3853ace3d39a8618e5717d42e437019510505b3453ae87c75`，已對照 Git 來源與工作區逐位相等。沿用 `codex/canvas-grid` 隔離工作區，原 D 工作區既有修改不在本次範圍。

新來源不填count，以signed lattice index保留身分；獨立配置保存boundary真實頂點key、cell與有理位置。未放置boundary也可組合，之後明確套到引用同一boundary的承載面，不暗建surface或角材。首次頂點選取與keyed幾何更新均有核心geometry-hash守門；半毫米不暗取整。查詢／顯示容量不定義網格本體有限，sample須明示。舊finite檔保留原義，不silentconvert。

v4 核心已通過 136／136 場景及 46／46 契約（19 無限、13 舊有限、14 模型版本相容）。新增大於 2^53 的 signed 引用、INT64_MAX cell 拒絕、乘法中間溢位而最終平移仍可表示、精確有理錨點、頂點高水位不重用、L 形與孔洞裁切等反例。保存重開修正曾使 scene 內 I8a 守門退步，已恢復既有六個拒絕案例，同時保持多配置 canonical 重放。GCC 與 MSVC 的 core／bridge／model-base 均編譯成功；執行證據來自 WSL，未把 Windows 編譯成功當成執行成功。

建模／傳輸／參照／子網格／工程／服務回歸共 139 次執行，138 通過、一個工程模型來源類別因缺少專用 bridge 環境變數略過；補齊後該類別 4／4 通過。另有 bridge integrity 24／24。唯一閱讀器重建、`--check`、24／24 閱讀器測試通過，五道 assert 與獨立 SSOT 比對通過，99 個補丁均套用；27／27 見證圖與 v4 一致。主 C 檔保持 CRLF、無 NUL 或裸 LF。

P70 定向真實瀏覽器 52 個斷言已通過：未放置邊界、兩份配置的實質影響預覽、真實負 cell／孔頂點拾取、四側擴邊、改距保持錨點、密集顯示、正式下載／清空／重開與 390px。P71 定向 8／8 通過：負索引命中、完整 cell 不被邊框替代、子格保存、依賴刪除提示、面內放大重新查詢及新格線帶入角材選項。先前 P71 測試初始化等待確認的問題已修成明確原生確認，不弱化產品預覽守門。

最終完整 `cdp_test.js`（無 scope filter、v4 bridge）：**1194 通過斷言、0 失敗、0 略過、exit 0**。包括 P70 52 項與 P71 8 項再跑；此數量是混合真實輸入／DOM 整合／API 的斷言數，不是流程數。唯一例外為回報測試刻意觸發的 `fb-auto-probe`，沒有未預期例外。證據 `%TEMP%/geometry-tests/infinite-grid/full-cdp-v4.log`；正式下載並重開檔案 `%TEMP%/geometry-infinite-grid-download-YA3F2A/未命名專案.gcanvas`，旁附 `infinite-grid-roundtrip.json`。

桌面及 390px 截圖已目視檢查；390px 仍是瀏覽器模擬，未宣稱實體手機觸控或作業系統原生保存對話框驗證。18862 同一試用服務已更新至 v4，更新前另存場景且載回後 dump 逐位相同；舊有限物件不被轉換。已在應用內瀏覽器開啟「建立無限網格」介面。原 D 工作區七項未提交修改保持不變。

## GEO-216 — 來源與配置的組合畫布介面（2026-09-28，已完成）

使用者明示以 Product Design 重新設計主畫布，從三張設計中選擇第 3 張。實作依第 3 個實際顯示的產圖結果，而非概念提案順序；設計來源、同尺寸畫面比對與修正紀錄見根目錄 `design-qa.md`。沿用 `codex/canvas-grid` 工作區，未修改 SSOT、核心行為或專案保存格式。

左側固定「建立物件」「網格系統」「邊界」，清單按來源／配置／空間與構件分組；繪圖工具浮在畫布上。選取物件才出現底部設定，網格來源可改名稱與等距間距，配置可改來源、邊界、實際頂點、signed cell 與格內位置。進階操作由「完整工作區」接續。關係線讀取真實引用，拖曳／取消、過濾與 compact 縮放會同步更新，不用畫面連線另造模型關係。

所有改動沿用原生候選預覽及確認：取消、切換專案、過期來源／邊界不得提交；復原與重做包含連動結果。格內九點是同一 cell 的角、邊中點與中心，保留自訂有理比例，沒有把圖稿的九宮外觀誤實作成另一個 cell。穩定頂點身分留在模型，介面以位置與頂點說明供人辨識。舊有限來源保留原義及相容入口。

最終完整 `cdp_test.js`：**1250 通過斷言、0 失敗、0 略過、exit 0**，無 scope filter，16 個產品／測試檔執行前後雜湊全相等。唯一瀏覽器例外是 P38 刻意注入且驗收的 `fb-auto-probe`，未預期例外為 0。證據 `%TEMP%/geometry-tests/composition-canvas/full-cdp-complete.log`、`full-cdp-result.json`、`final-validation-hash-check.json`；混合層級斷言數不冒充完整流程數。18 項服務回歸亦通過。

新增 P72 的 51 項涵蓋固定入口、鍵盤選單、來源／配置原生影響、預覽取消與確認、Undo／Redo、拖移取消與 compact 連線、極端合法間距有界縮圖、低處卡片雙擊及輸入框防誤開、正式保存與重開、390px 底部編輯及視野避讓。保存測試只替代 OS file picker／writable handle，真實打包 bytes 寫出後由正式開檔流程重開，逐一比較 scene、objects、references；既有 P70 真下載仍保留。完整執行留下展開篩選時，測試真點 summary 收起再選列，未以程式點擊穿透遮擋。

回歸同時修復焦點切換的版面測量時序：先同步面工作區版面再 fit，避免用主畫布欄寬把中心由 5000 錯移至 2675.49；新增置中檢查與原格線命中檢查均通過。卡片尺寸相關框選夾具按實際尺寸更新，包含／相交、邊角接觸與差 1 px 判準保留；跨專案 Undo 依既有 L1 分別驗模型還原與畫布位置保留。最終桌面／390px 與來源全圖、局部共同檢視完成，`design-qa.md` 為 `passed`；沒有未處理 P0／P1／P2 問題。

18862 試用服務更新前已保存最新場景，載回後 dump bytes 完全相同；新靜態檔可成功載入。原 D 工作區 dirty paths 與開工七項清單一致，未把本輪變更混入其中。實體手機觸控、作業系統原生保存視窗未驗證；完整 UI 操作證據由專案指定的 Chrome harness 產出，應用內瀏覽器另已開啟原場景供檢視。

## GEO-217 — Canvas UI/UX 審查修正（2026-09-28 立案，2026-09-29 完成）

使用者要求核對審查後「全部修一下」。驗收對照見 `geometry-web/docs/UIUX-FIXES-2026-09-28.md`。面／空間頂列改兩列、窄幅保留檔案與保存狀態；全圖視野隨容器重新適配，手動視角保留中心與倍率。三視圖移除框選提示，密集標籤避免彼此重疊，左欄可直接開啟完整清單。手機操作與次要文字對比同步修正。

開啟專案保留可一步復原的既有行為，提示加入具體操作及專案名稱；載入立即呈現真實階段並阻擋競態。內建工程專案保存卡片位置，開啟不因自動排版誤報變更，舊專案的自動排版則如實說明。空空間提供加入成員入口；網格主動作固定可見，未套用草稿禁止用保存專案關窗，離開及換邊界的取消／確認保留或明示捨棄草稿。來源輸入增加選擇器與完整軸向說明；六面盒 2500／空間建模 3000 明示用途與可修改性，未更動公理、核心或專案格式。

本輪另修復縮放控制被畫布 pointer capture 攔截，以及手機網格全圖預留標籤寬度不足。新增 P73／P73B 使用實際指標與鍵盤輸入，涵蓋載入與復原回饋、響應式畫面、清單可達性、來源選擇及延遲邊界查詢的草稿保護；原生世界逐字比對保留。使用本輪獨立 18861 服務及 `%TEMP%/geometry-tests/uiux-fixes-20260928/`，回報與截圖皆在 TEMP；短暫另起的 18862 診斷服務已核對為本輪新 PID 並於診斷後停止。

驗證採完整執行＋定向補驗：完整執行 1291 個通過斷言，3 個舊測試假設失敗，並因保留的空間分頁中止於最後 P73。修正測試互動、實際座標、可繪區中心與浮點精度後，P67 96／96、P71 9／9、P73／P73B 64／64 全數通過，0 略過、0 未捕捉例外，涵蓋所有失敗及剩餘尾段。這不是單次完整回歸全綠；精確紀錄及證據見修正報告。

獨立驗證員重算確認：該輪完整執行及補驗的 13 個產品檔未變，補驗前後 6017 個執行資產逐筆一致。另有 36／36 保存測試、21／21 載入競態、418／418 Canvas API 檢查通過。實體手機與作業系統原生檔案對話框不由瀏覽器模擬驗證代替。

最後預覽另發現工程視窗無編輯關閉也新增預設草稿。補上表單內容比較基準，純瀏覽不寫專案，真實編輯仍保存並更新狀態。此額外產品修正之後，P69 160／160、P73／P73B 65／65 通過；最終產品凍結補驗雜湊及截圖另存於報告所列 TEMP 證據。沒有將先前的雜湊相等結果誤用到這次後續修正。

## GEO-218 — Canvas 第二輪介面與專案生命週期（2026-09-29，完成）

使用者提出六點改善並同意繼續。全畫布文字增加固定粗細白描邊，面尺寸改為真實邊的外側尺寸線；三視圖常態只顯示角材編號，完整代碼仍可查看。工具教學只首次顯示、可關閉及重開，即時定位與選取持續更新。面與角材屬性分常用及詳細資料，保留精確引用能力。

建立選單只保留建立功能；範例移入檔案子選單，空間模型清單獨立。新專案建立新身份，清空專案內容保留原身份，兩者均確認且可一步復原。大型工作區使用同一頂列保存控制及一致返回位置，主要動作仍是預覽／建立／套用，草稿守門不變。

專案資訊區分服務現有場景、範例及檔案來源；保存時間只記真正完成寫入，下載只記產生時間。增加本分頁完整專案暫存，重新整理時核對服務與場景、完整驗證後才恢復附件及已記錄草稿；不恢復未套用的工具草稿與較早完整歷史。同一瀏覽器儲存環境、同一網站位址與服務工作階段以編輯鎖保護第二分頁；不同瀏覽器與網站別名不在此鎖的範圍。沒有改核心、公理層或專案檔案格式。

最終完整 `cdp_test.js`：**1375 個通過斷言、0 失敗、0 略過、exit 0**，scope 為 full 且沒有 filter。證據位於 `%TEMP%/geometry-tests/ux-refinement-20260929/full-cdp-release.log`，使用隔離服務 18864。唯一瀏覽器例外為 P38 刻意注入的 `fb-auto-probe`，未預期例外為 0；斷言數不冒充端到端流程數。47 個 geometry-web 頂層執行／測試檔於完整執行前後核對；另有 48／48 專案保存與競態測試、38／38 服務與回報測試通過。桌面與 390px 瀏覽器驗證不代替實體手機或 OS 原生檔案對話框驗證。

完整回歸另抓到已關閉首次教學後的框選中斷：即時摘要出現觸發自動適配，鏡頭更新又取消手勢。已將提示覆層與真正視窗縮放分開；明確全圖仍避讓提示，真正容器與底部控制列尺寸變化仍適配。P67 常規夾具涵蓋教學已讀狀態，精確邊角及差一像素的選取測試保留，定向 96／96 通過。

重整壓測另記錄到必要腳本 `app.js` 的 `net::ERR_CONNECTION_REFUSED`，繼而造成工作區無法啟動。本機 Python 3.14 的預設待接連線佇列只有 5；新增 `PreviewHTTPServer` 提高至 128，承受瀏覽器預載與重整時的突發請求。未更動服務位址、請求處理或原有未提交的上傳／回報改動。修正後驗證服務改用 18864，原服務保留。

修正後 P74 連續三輪各 52 項通過，再由完整回歸重跑一次；主頁網路記錄無腳本連線失敗，新分頁經真實操作驗證編輯權限與接管。測試等待延後建立的視窗、換頁後的新文件，以及原分頁真正消失且釋放編輯鎖後才點重新連接；保留原本資料比對、逾時及例外失敗判準。完整測試於保留既有未提交改動的工作區執行；提交範圍只含本輪 UI/UX、專案生命週期及已確認的服務佇列修正，原有核心／上傳／回報工作另行保留。

## GEO-219 — Canvas 介面減重：單選覆層與面工具列入口（2026-09-29）

使用者審查結論：面工作區與說明文字是真正的臃腫來源，要求「幫我做」減法。
依 2026-09-29 決策佇列 Q18–Q21（🔒）實作：

- Q18：`#ocSelectionSummary` 恢復 GEO-216 契約——0／1 選取視覺隱藏，多選與
  框選中顯示；`workspace-guidance.css` 的 `[data-guidance-dynamic]` 顯示規則
  排除 `data-count="1"`。`#feSelectionSummary` 不變。
- Q19：主畫布左欄快捷、建立選單與浮動工具列的重複入口維持現狀。
- Q20：`index.html` 面工作區工具列移除 `#btnFaceProjection`／
  `#btnFaceSpaceModel`；`FaceProjection.inspectorHTML({faceWorkspace:true})`
  對已放置面一律提供 `[data-fp-build]`（未定義走 `#smInlineProjection`，
  立面可在建模視窗切組合面模式）；主畫布檢視器入口條件不變。
  `space_model_test.js` 入口改走屬性欄 `facePropEntry` 真實點擊。
- Q21：`AGENTS.md` 新增「UI 減重紀律」兩條：新增入口／說明須寫明拿掉或
  合併什麼；每個工作畫面常駐說明區塊不超過 3 塊。

驗收條件：

- S1 主畫布單選後覆層不可見，`data-count=1` 與 live 節點仍在；多選與框選中可見。
- S2 面工具列不再有「平面投影」「建立空間」，畫圖工具與「工具說明」不受影響。
- S3 屬性欄對已放置面一律有建立入口；未定義水平面出現 `#smProjectionCallout`，
  立面可切 `faces` 模式並預覽。
- S4 主畫布檢視器 `[data-fp-build]` 仍限已定義且水平放置。
- S5 390px 從右側抽屜可用真實點擊命中兩顆入口，按鈕高度 ≥44px。
- S6 不改公理、核心或專案檔案格式。

驗證：`node --check`、`git diff --check`、`GEOMETRY_MARQUEE_ONLY` 定向、
`space_model_test.js` 全套、完整 `cdp_test.js`、1382 與 390px 截圖核對。

## GEO-220 — 游標白字被描邊糊住、離開網格後無法選取（2026-09-29）

使用者在 Edge 回報：面工作區看構件時仍亮著網格工具，畫布點選無反應；移動參考線與角材的游標文字變成白色塊狀。

- 原因一：GEO-218 的全域 SVG 文字白描邊也套到已有深色背景的游標白字。將游標覆層排除於白描邊規則，並明確令膠囊及尺寸提示文字不描邊；圖面尺寸、參考線標籤仍保留 3px 白描邊。
- 原因二：離開網格分區沒有退出網格工具；一般畫布點擊因此被網格模式守門略過。切回其他分區或在側欄選角材會恢復選取，保留網格草稿；工程來源等僅顯示資訊的網格不再進入無可用操作的網格模式，子格父格選擇仍明確進入網格工具。
- 減項：拿掉游標文字上多餘的白描邊；網格快捷鍵文案取代原本不適用的框選提示。沒有增加按鈕、入口或常駐說明區塊，未更動核心或公理。

回歸涵蓋真實點選、框選、格尺草稿、格線拖曳、切換後草稿保留、來源網格與子格，以及 1382／390px 游標標籤的實際 CSS 呈現。驗證紀錄存放於 `%TEMP%/geometry-tests/selection-labels-20260929/`。

已通過 P75 新回歸 37 項、P67 選取框選 96 項、P69 工程規格流程 160 項，三輪皆 0 失敗、0 略過、0 未捕捉瀏覽器例外。提交用獨立工作區另重跑 P75，37 項全數通過。桌面及 390px 截圖確認「移動參考線」「角材」「開口」及尺寸提示的白字可辨識；本次為相關群組定向驗證，未宣稱重跑全部測試。

## GEO-221 — 無限網格工作區依審查稿 1b 修正（2026-09-30，已完成）

來源：使用者提供的「網格檢視器界面審查」設計稿（1a 現況／1b 修正版）。對照現況後，1b 的 9 個項目只完成了按鈕可操作與文案，其餘照 1b 補齊。不改公理、核心、橋接器或專案檔案格式；相機仍只是呈現狀態。

- 等比例：`#igGridView` 移除 `preserveAspectRatio="none"`；viewBox 每次繪製都設為元素實際像素，u、v 共用同一 mm→px 比例（以相機中心做 contain 貼合），600×400 的格子維持 3:2。`ResizeObserver` 隨視窗大小重繪。拖曳平移改用同一比例。
- 尺規：索引移到上、左尺規列，置中對齊格線，只寫數字；左上角 `v＼u`；第 0 線加粗、標示強調藍 `#365bf5`。標籤依像素間距與位數以真正索引取整除稀疏化，超長索引用 `textLength` 壓進尺規欄，不截字。
- 基準點：兩條第 0 線交點畫圓點並標「基準 (0, 0)」；「回到基準」改為回到來源第 0 線（`phase`）附近，不再固定回 (0, 0)。
- 比例標示：工具列 `#igZoom` 顯示「1 格 600×400 mm · 132 px」。
- 填滿主區：`.ig-main` 改為直向 flex，`#igGridView` 撐滿剩餘高度（配置模式下邊界與結果區仍在其下捲動；390px 維持 270px）。
- 文案：footer 提示已同時列出「預覽並建立／預覽來源變更」，與按鈕在兩種狀態下都一致，沿用不改。
- 命中規則：只有繪圖區內的點擊會選 cell；尺規列不選。
- 減項（GEO-219 紀律）：拿掉格線上的「u 」「v 」前綴標籤與五個疊字（`u →　v ↓`、`← ∞`、`∞ →`、`↑ ∞`、`∞ ↓`），方向說明只留在標題列。新增的只有 `#igZoom` 一行比例文字（取代被拿掉的疊字，不新增按鈕或說明區塊）。

驗證：`grid_system_test.js`（P70）改用 `svg.dataset.igCamera` 與 `[data-ig-plot]` 換算點擊位置，不再假設相機等於整個 SVG；新增 6 項 1b 斷言（等比例、尺規對齊、無 ∞ 疊字、基準點、比例標示、填滿主區）。`GEOMETRY_GRID_SYSTEM_ONLY=1` 全部 67 項通過（含 P71）、0 未捕捉瀏覽器例外；桌面與 390px 截圖核對。

## GEO-222 — 無限網格工作區改為「製圖桌」（審查稿 3a，2026-09-30，已完成）

延續 GEO-221。依設計稿 3a 重排 `#infiniteGridWorkspace`：網格是畫面本體，設定集中到右側檢查器，兩層 header 與 footer 合併。不改公理、核心、橋接器或專案檔案格式；所有既有 `#ig*` 控制項 id 保留。

- 單列麵包屑：共用專案列（`#projectBar`）與 `.ig-header` 以 CSS grid 併成一列 56px——`← 返回畫布 | 專案名 / 無限網格 / 標題`，右側只留專案狀態與「保存」。「保存」在此工作區降為次要（白底）；「預覽並建立／預覽來源變更／預覽配置變更」是唯一主動作。專案名以 `data-project-name` 放進麵包屑，專案列自己的名稱在此工作區隱藏。
- 右側檢查器（360px）：名稱、u→／v↓ 兩軸、格子縮圖（隨間距即時改比例）、主支方向、格資訊、依模式出現的來源／配置表單；底部固定 footer（狀態說明與主動作）。390px 時檢查器攤平，footer 改為 sticky 貼底，首屏仍看得到主動作。
- 畫布：`.ig-canvas` 撐滿左側，操作說明（拖曳平移 · 滾輪縮放 · 點格子選取）與縮放列（− 比例 ＋ 回到基準）改為浮在畫布左下／右下。配置模式時邊界與結果區仍在畫布下方捲動。
- 主支方向：`#igMainAlong` 由 `<select>` 改成分段 radiogroup（不設定／沿 u／沿 v）；元素保留 `.value` 讀寫，草稿判定與提交流程不變。
- 格資訊：游標移入格子時，格子與上、左尺規同步高亮，`#igInfoCell`／`#igInfoRows` 列出 cell 索引、起點與尺寸；來源畫面點格可選取（再點取消，只是視窗狀態，不寫模型），配置模式維持點格填 `#igCellI/J`。
- 減項（GEO-219 紀律）：拿掉 `.ig-header` 的「無限網格 · 局部座標 u → v ↓」說明行（方向改由檢查器 `u→`／`v↓` 承擔）、主區標題「無限網格」與其說明段、來源表單標題「網格來源」與「格線向兩端無限延伸…」說明段、獨立 footer 列（併入檢查器底部）、專案列與 header 的兩層結構。「目前視窗完整顯示格線…」常駐說明改為只在稀疏顯示或大索引時出現。新增的只有檢查器內「格資訊」一塊與畫布浮動提示／縮放列（取代原標題列與工具列），沒有新增按鈕入口。常駐說明區塊：來源畫面為畫布提示、footer 狀態兩塊；配置畫面原有四塊（畫布提示、footer、邊界頂點說明、「只列出引用同一邊界的承載面」），依紀律第 2 條把最後一塊併入欄位標籤「承載面（僅列同一邊界）」，收斂為三塊。
- 第 0 線、基準點與選取改用 app 的 `--accent` `#4e67e8`，取代 GEO-221 用的 `#365bf5`，與檢查器強調色一致。
- 順帶修正：DOM 順序改成畫布在前後，`syncFields()` 原本以 `[data-ig-axis]` 取第一個符合的元素，會誤抓到 SVG 格線；改為 `fieldset[data-ig-axis]`。

- 覆查修正（同日，GEO-221／222 自我審查後以真實瀏覽器重現）：
  - 縮放漂移：等比例貼合每次都以「contain」重算，畫布高度一變（稀疏提示出現／消失、視窗縮放、手機轉向）比例就只放不收，來回 4 次縮小約 35 倍。改為新設的相機才做 contain 貼合，同一相機遇到版面尺寸改變時保持 mm/px 不變。
  - 焦點被搶：重繪時的 `sourceDraft()` 會對無效欄位呼叫 `focus()`；新增的 hover、ResizeObserver 讓滑過網格就把焦點從名稱欄搶到無效的間距欄。重繪改為靜默驗證（`quietDraft`），hover／點格改用上次重繪算好的 `s.defs`，不再重新解析草稿。
  - 單軸來源點網格會在狀態列顯示紅字「選擇 cell 需要兩軸皆有定義」；來源畫面改為無動作。
  - 草稿無效時一併清掉格資訊與縮圖，避免殘留舊值；ResizeObserver 每次重建工作區只保留一個。
  - 按「預覽」遇到無效欄位只顯示錯誤、焦點不動（修改前即存在：`operation()` 先停用全部欄位，`focus()` 對停用欄位無效）。改為記下錯誤欄位，`operation()` 恢復欄位後再移入焦點。
  - 390px 麵包屑原本只剩標題、看不到專案名稱；改為兩行：上行小字專案名稱、下行工作區標題。
  - 「基準 (0, 0)」指的是索引；第 0 線不在 0 mm 時改寫成「基準 (0, 0) · 300, 0 mm」，避免誤讀成 mm。

驗證：`grid_system_test.js`（P70）新增 12 項斷言（單列麵包屑與主動作、右側檢查器、縮圖比例、分段主支方向、游標格資訊與尺規高亮、點格選取與取消、版面改變不漂移、無效欄位不被搶焦點、單軸點格無錯誤、預覽錯誤移入焦點、基準標籤寫出 mm、390px 顯示專案名稱），並把分段控制的操作改走真實點擊。以隔離服務跑 `GEOMETRY_GRID_SYSTEM_ONLY`（79 項，含 P71）、`GEOMETRY_COMPOSITION_ONLY`（52 項）、`GEOMETRY_UIUX_FIX_ONLY`（65 項，含網格首屏 1382／900／390 與草稿守門）、`GEOMETRY_UX_REFINEMENT_ONLY`（52 項，含共用保存列）全部 0 失敗、0 未捕捉瀏覽器例外；桌面與 390px 截圖核對。未重跑完整 `cdp_test.js`。

## GEO-223 — 畫布參數卡與具型別算式（2026-09-30，條文已核准 🔒，實作完成，待人工驗收）

使用者要求執行已討論的參數實作計畫：畫布建立自訂欄位參數卡，支援尺寸、數量、比例、
精確分數、跨卡引用及四則算式；網格、角材截面與定位尺寸持續引用，可预覽連動、整筆復原、
完整專案保存與參數包匯入匯出。第一版來源由欄位選取；幾何向量、組件嵌套、拖線、共用庫與
縫中心／板邊模式留待後續。

- 計畫第一步已產出 `geometry-core/PARAMETERS-PROPOSAL.md`：第 1–16 節逐條 diff，
  新增 D31 / I38 / I39 / R33，並修訂分數／幾何邊界、定位來源、D29、交易與保存等既有條文。
- 使用者看過逐條 diff 後回覆「繼續」，依 Q22 採納條文並開始實作。
- UI 減項：新增「建立 → 參數」及共用編輯器時，將面內「規格名稱＋數值＋儲存具名規格」
  的獨立建立表單合併進共用入口；舊 spec 仍編輯原物件。選取時才顯示相關連線，常駐說明遵守三塊上限。
- 實作順序：條文核准 → 核心精確求值與來源 → 交易／保存／模型能力 → 正式畫布與表單 → 完整驗收。
- 驗收涵蓋同／跨卡依賴、精確分數、單位、循環、來源修改回滾、穩定身分、參數包閉包／重新配號、
  舊檔相容、過期回應／草稿守門、桌面／390px 及完整 CDP 回歸；詳見提案驗收矩陣。
- 核心、橋接、專案格式與正式畫布已完成並提交；206 原生測試、97 JavaScript 測試、
  136 既有場景及完整介面 1482 斷言全部通過，自動驗收結果見
  [驗收報告](geometry-web/docs/PARAMETERS-VALIDATION.md)。依 Q23-b，實體手機鍵盤與作業系統
  下載提示仍待使用者人工確認，完成前不標「已交付」。Q25／GEO-224 的參數編輯面板重設計
  已實作並通過自動驗收，見下方 GEO-224 條目。

## GEO-224 — 參數編輯面板重做（設計稿 4a，2026-09-30，已完成）

來源：使用者看過設計稿「建立參數 · 重新設計」（4a）與 agent 列出的六處缺口後，授權補全並落地（`決策佇列.md` Q25 🔒）；設計稿存於 `geometry-web/docs/uiux-review/建議-建立參數 4a.dc.html`。範圍是網頁版「建立參數／參數卡」編輯面板：純前端（`parameters.js`、`parameters.css`、`app.js` 版面旗標）加 DOM 契約與瀏覽器測試。不改公理、核心、橋接器、`PARAMETERS-CONTRACT.md` 或專案檔案格式；前端仍不做算式求值，有效值與錯誤全由核心預覽交易提供（Q25-2）。

- 版面：參數編輯（建立或編輯既有卡）時 `body.parameter-editing`；視窗 >900px 時檢視器改成畫布右側固定欄（寬 `clamp(380px, 30vw, 480px)`、內部捲動），畫布取其餘寬度。其他檢視器與 ≤900px（含 390px）維持畫布下方，既有版面決定不動。
- 面板結構：標頭（名稱、狀態徽章：草稿·未套用／已套用／有未套用修改）→ 從範本開始（三顆範本鈕 `[data-param-template]`、快速輸入與即時預告 `#paramQuickHint`，Enter 等同「建立欄位」）→ 緊湊欄位列表（每欄名稱、種類原生 `select`、核心算出的結果、輸入框，計數 n / 16）→ 說明 → 套用後的影響 → 摺疊區 `#paramUsage`／`#paramExchange` → 固定頁尾（狀態點與狀態、捨棄、重新試算、確認）。加欄、移除、上移、套範本只重繪欄位列，焦點落在新欄名稱、相鄰列或被移動列。
- 逐欄試算與錯誤（Q25-2、Q25-3）：沿用 450ms 防抖與過期守門。成功時每欄顯示核心回傳的精確值；核心 fail-fast 只指認第一個出錯欄，前端解析 `[pid:fid 卡.欄] -> … -> 根因` 前綴標紅該欄，其餘欄顯示「待試算」；核心錯誤碼對照中文短句（`ParameterUI.errorText`），原文收在該列 `<details>`。
- 引用晶片（Q25-6）：選中列才展開「卡名.欄名 值」晶片；排除自己與會造成循環的來源（以 AST 與草稿輸入內的引用 token 求傳遞閉包）；超過 8 個來源出現篩選框並限高。
- 畫布草稿卡：建立新卡期間畫布顯示虛線「草稿」卡（`.parameter-card.is-draft`），內容跟著欄位與試算結果更新；不寫 canvas-pos、不進 `oc.parameters`、不可選取或拖曳、不畫關係線。草稿卡是最後一個獨立 commit，未動選取、拖曳與小地圖邏輯（畫在獨立的 `#draftLayer`、`pointer-events: none`、不帶 `.ocard`）。
- 樣式：只用 `app.css :root` 既有 token，修掉 `parameters.css` 裡未定義的 `--text`、`--surface`；不載入設計稿的外部字型；所有可點控制（含晶片、範本鈕、上移、移除）≥44px。

減項（GEO-219 紀律）：範本下拉 `#paramTemplate` 併入三顆範本按鈕；每欄 `fieldset`／`legend` 拿掉，改緊湊列；「插入引用」下拉 `select[data-insert]` 併入帶值晶片；「轉成欄位草稿」併入「建立欄位」（也可直接 Enter）。新增的可見入口只有範本鈕（取代下拉）、晶片（取代下拉）與頁尾狀態點，沒有新增獨立按鈕入口。常駐說明區塊維持 3 塊（說明、`#paramResult`、`#paramStatus`）；`#paramQuickHint` 只在輸入時出現，屬即時預告，不計入。

驗證：`parameter_workflow_test.js`（P76）既有 35 條斷言語意不變，只把摺疊區選擇器由 `details:first-of-type`／`details:last-child` 改為 `#paramUsage`／`#paramExchange`；新增 21 條（第一輪 9 條：範本鈕、快速輸入預告與 Enter、每欄核心值、`=1/0` 只標出錯欄、循環來源排除、點晶片後試算成功、1280px 右側固定欄與 sticky 頁尾、390px 控制 ≥44px 與無溢出、畫布草稿卡；第二輪 12 條：見下段）。`GEOMETRY_PARAMETERS_ONLY=1` 56 通過；完整 `cdp_test.js` 1503 通過、0 失敗、0 略過群組；`tests/test_parameters_project_store.js`（5/5）、`tests.test_parameters_core`（19）、`tests/test_space_model_store.js`（17）、`tests/test_axiom_reader.py`（25）全部通過。突變證據：拿掉出錯欄歸屬、循環排除、`body.parameter-editing` 右側欄規則、sticky 頁尾、草稿卡繪製，對應斷言各自變紅。桌面與 390px 截圖（`docs/screens/parameters-*.png`）核對。

第二輪（對抗審查後）：合入 main 的 2caf00c（`createCard` 等待穩定化）；草稿卡位置改在右側欄版面定案後才排並平移入可視區，確認時以草稿座標寫入真卡（原本草稿用寬畫布、真卡用窄畫布，位置會不同）；進入參數編輯時選中卡平移入可視區；欄位列 `role="group"` 與各控制的可及名稱、`[data-error]` `role="alert"`、快速輸入預告 live region；多筆違規逐筆列出，欄位歸屬與錯誤碼改為只認分節開頭與根因段；≤900px 參數編輯時底部面板高度上限放寬為 `min(62dvh, 560px)`；輸入法組字中的 Enter 不建立欄位；明確按「重新試算」時撤掉尚在防抖的自動試算（否則它會再建一個候選，讓剛拿到的確認 token 失效）。新增測試：三層依賴鏈與草稿 token 建邊、草稿位置＝真卡位置、選中卡不被右欄遮住、離開路徑清除 class、特殊字元只當文字、過期回應不覆寫逐欄結果、可及名稱、多筆違規與訊息解析純函式、窄畫面面板高度、輸入法 Enter；「保存內容不含草稿」改為草稿還在畫布上時取 scene dump。

併入組立規則之後的 main 時，參數預覽的影響清單保留組構配置槽位 A／B 的前後值。上面的 1503 斷言是合入前的瀏覽器回歸，沒有覆蓋這一列。

## GEO-225 — 測試可信度與入口精煉（2026-10-01，進行中）

使用者問「測試會不會太多、要不要精煉」。盤點結論：量不是問題（測試約 26,000 行對產品碼約
30,000 行，沒有大面積重複），要精煉的是「綠燈可不可信」與「怎麼跑」。使用者指示依發現的問題改善；
`prototypes/engineering-spec/` 的去留明示先不管。不刪任何仍有效的測試、不拆 `cdp_test.js`。

- **a 二進位新舊與單一入口**：`tests/binaries.py`（來源指紋快取，沒變就不重編）、
  `tests/run_all.py`（一次跑完非瀏覽器測試，分列 pass／fail／skip／環境阻擋）。
- **b 靜默通過與看不見的 skip**：`test_parameters_core.py` 缺 `GEOMETRY_MODEL_BASE` 時後半段
  直接 return 算通過；class 級 skip 只記 1 筆；`cdp_test.js` 沒有每段斷言數地板。
- **c 變異測試結果過期**：`mutants_results.json` 有 12 個錨點已不在現行原始碼卻仍記 killed，
  且無來源雜湊。
- **d 孤兒與過時文件**：移除 `geometry-web/_cursor_test.js`、`_shot.js`（無入口、引用的
  `#notchDialog` 已於 GEO-188 移除、預設連 8765）；`reference_smoke.js` 也已移除（過期夾具、預設重置 8765，引用流程由完整 CDP 覆蓋；Q26）；
  更正 `AGENTS.md` 兩處（截圖已不寫 `docs/screens`、`space_model_test.js` 也執行 `app.js`）。
  `docs/UIUX-FIX-PLAN.md` 提到 `_cursor_test.js` 的字樣屬歷史紀錄，未改。
- **e 共用樣板**：抽出 `cdp_helpers.js` 與 `tests/_bridge.py`，保留各測試的等待、輸入及錯誤行為。
- **f 負例釘住拒絕理由**：格網負例同時驗拒絕原因與整個世界不變；補足 Q29 真實支撐的方向夾具。
- **收尾修正**：Q27 無效 benchmark 次數在取得 GDI 資源前返回；Q29 無限父格錯用有限 cell 的訊息指名正確原因。公理條文未修改。

接手核對與執行結果見 [GEO-225 驗證紀錄](tests/GEO225-VALIDATION.md)。新核心完整瀏覽器回歸
1490 斷言通過、0 失敗、0 略過，72 段與既有基準相符；Linux 非瀏覽器全套 1179 通過、
0 失敗，僅 Windows GDI 略過。GDI 在 Windows 仍遭 SAC 阻擋，完成前保留「進行中」。
Q28 🔒 已採 A：同一夾具連續存取違規記 `crashed`（算被偵測到，與 `killed` 分開），
啟動失敗與 WinError 4551 仍是 `blocked`。

## GEO-226：組構規則 authoring 與材料配置（PR #26）

Refs GitHub #19–#24。第一階段整合原生固定版本規則、局部型別接合、來源材料配置、交易预覽／確認、scene 重建、專案格式 7 與未完成草稿、正式畫布入口及桌面／390px 操作。

- **本次拿掉／合併**：移除建立選單的「更多物件」分隔標題；草稿、發布版本、材料配置合併成同一工作區，共用既有保存列，不另加專用保存入口。常駐說明收在目前編輯內容，拒絕訊息與預覽按需顯示。
- D12/D32/D33/I40/I41/R4/R34 依 #20 定案同步；正典閱讀器仍只有一份。
- 規則只 authoring，不生成施工角材；#25 仍是獨立後續工作。
- 可重開範例：`geometry-web/examples/assembly-rules-v1.gcanvas`；由 `tests/build_assembly_example.py` 經原生核心產生，含兩版、完整／未完成配置及草稿。
- 驗證、可重現命令、逐項矩陣與環境限制見 [組構驗收](geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md)。
- **連帶回歸修正**：保存能力按集合比對；交易確認移除巨大堆疊副本；重開舊格式模型避免遞迴刷新。小筆電恢復預覽高度，短螢幕收起重複範例捷徑，把空間留給設定與確認。面工具列測試改依現行 116／122px 契約驗證，仍檢查控制項不遮擋。
- **完整流程追加修正**：換版槽位名稱一律作文字顯示；網格與空間建立測試等實際資料就緒。參數手動試算取消待執行的自動試算，新候選回覆前停用確認，避免兩份候選互相覆蓋；以延遲回覆重現並驗證。
- **待人工驗收（open）**：A24 實體手機鍵盤、OS 檔案選擇器與下載位置。Windows GDI 已以重編版本單獨通過；其餘受 SAC 阻擋的全套執行改用同源 WSL 驗證。保留總工單 open。
- **收尾交接（2026-10-02）**：#20–#23 的實作已合併，依現行 SHA／CI 與聚焦回歸核對結案證據；#19／#24 保留真正未驗的 A24。步驟與空白紀錄集中在既有[驗收文件](geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md)。使用者選擇「先修復與收尾，其餘依原決策保留並整理規格」；#25 維持後續待核准，求值輸入、穩定身分與逐條公理差異整理在既有[組構契約](geometry-core/ASSEMBLY-RULES-CONTRACT.md#deferred-generator-handoff--25-2026-10-02)，未實作生成器、未改公理。
- **A15 配號修復與補驗（2026-10-02）**：修正 native 配號回繞後，JS 只跳草稿預留卻撞到既有配置的覆寫漏洞。同時檢查兩組占用身分、限制正 uint32、版本上限拒絕；配置草稿保存新增／編輯意圖與原始內容，预覽前重新檢查占用與來源，舊無意圖草稿不猜成更新。補 A04 局部差異保存、A13 錯型／容量、A18 各版本配置、A23 390px 空白建立及 sanitizer／mutation 證據。減項：沿用既有編輯與拒絕訊息，沒有新增入口或常駐說明。A24／#19／#24 仍保留 open，#25 及 #43–#49 不納入實作。
- **閱讀修正（2026-10-01）**：已發布圖說改寫「誰的起點／終點抵住誰的哪一側」，側面鈕顯示右側、左側、上側、下側，點選寫入的值仍是 +u、-u、+v、-v。已發布配置改寫槽位名稱、截面與已選的接觸面、擺向。預覽主文改寫差異；JSON 留在原摺疊區。對話框改為蓋滿視窗。沒有待確認變更時不顯示預覽三鈕；有預覽時確認與取消固定在底部，差異貼在這兩鈕上方。減項：拿掉圖說裡的 junction、dir、start 與側面代號，拿掉預覽的份數統計當主文，拿掉空狀態下的三個動作鈕。常駐說明仍是原本那句示意，改寫成「只表示誰抵住誰，尺寸見材料配置」，側面對照附在同一段。

## GEO-227 — 參數套到網格的圖解（2026-10-01）

使用者要求：建立參數（一方向 915、另一方向 1830）並套到網格時，要有任何人都看得懂的視覺教學，不能只靠文字。

- 同一張圖 `#paramGridLesson`。參數卡畫出寬 915（藍）與長 1830（琥珀）；格子的 u→ 間距與 v↓ 間距用同色箭頭對上這兩個數字。格子上的控制畫成「引用來源」選到「寬」，表示間距是選欄位，不是把數字再打一次。第二張把寬改成 1220，橫向間距變寬（舊線改虛線），直向 1830 不動。可點圖或兩個圓點；尚未按知道了時約 3.2 秒換張。系統設定減少動態時停在第一張。
- 參數編輯時圖放在畫布上、避開上方繪圖工具，不放進參數面板，避免把欄位擠出 390px 的可視範圍。寬度 ≤900px 且展開時，圖改貼在視窗下方，名稱與快速輸入留在圖的上方。知道了之後「圖解」回到畫布裡。網格來源表單開啟時，同一張圖移到名稱下方的 `#paramGridLessonSlot`，跟著表單排版，不蓋住格線。配置模式不顯示。
- 「知道了」才記住。寫入的是這組事實的 token（`localStorage` `geometry-param-grid-lesson`）。事實變了，舊的已讀不算，圖會再出現。舊鍵 `geometry-param-grid-lesson-v1` 的 `'1'` 只對應最初那組事實。之後只留一顆「圖解」，再打開停在第一張，不自動播放。
- 圖讀功能自己的事實：欄名與預設來自 `TEMPLATES.panel`（經 `ParameterUI.panelTemplate`），來源控制的無障礙名稱與控制項種類來自 `sourceControl` 產生的標記，軸標與間距名稱來自 `InfiniteGridWorkspace.lessonSurface`，卡片標題來自 `#btnNewParameter strong`。第二張的寬是預設寬 × 4/3，橫向空隙用同一個比例。箭頭、游標與兩張的前後關係仍是手畫的。`data-pgl-control` 寫死這張圖畫的 `select`；控制項不再是下拉時，`FeatureLessons.check()` 以 id `param-grid` 失敗。
- 減項（GEO-219）：沒有在參數面板和網格檢查器各加一段文字教學，也沒有新增常駐說明、可見入口或留下縮圖，也沒有併進 `WorkspaceGuidance`。參數面板常駐說明仍是 3 塊（`.param-help`、`#paramResult`、`#paramStatus`）。網格來源畫面常駐說明仍是畫布提示與 footer 狀態。
- 不改公理、核心、橋接器或參數指令。

## GEO-229 — 無限網格的相鄰格子相位差（2026-10-01）

使用者拍板「照這份做」。D10b / I24 / R22 採納交替相位差：一個整數毫米，掛在會錯開的無限軸。偶數格用原相位，奇數格加上這個差。差不必是間距的一半。明示 0 與間距整數倍拒絕，不改存成 0。

- 放置要寫出另一軸的格子。有相位差的主格不能有子網格；已有子網格時加上相位差整筆回滾。
- 減項（GEO-219）：不新增工作區、不新增常駐說明、底部檢查器不加輸入欄。只在既有無限軸欄位組加「相鄰格子相位差」。非零時，既有「第 0 線座標」那一行帶出數字。線改畫成停在另一軸格子邊界的段。
- 不實作：逐格累加、多段相位表、support_step、by_span、全格批次、巢狀子格，以及把相位差做進子網格子表單。

## GEO-228 — 畫布物件說詞、三組篩選、草稿門（2026-10-01）

卡片角標、左欄圖示和篩選改讀同一張種類表。離開畫布的物件寫「進入 ›」（面、空間、組構規則、材料配置、無限網格、網格配置）；留在畫布、打開右欄的物件寫「檢查 ›」（承載面、參數、柱、樑、舊有限網格）。點下去的行為不變。

- 減項（GEO-219）：篩選芯片由六顆（面、空間、柱、樑、網格系統、網格配置）收成三顆（來源、配置、空間與構件）。六個計數 `#faceCount`、`#spaceCount`、`#columnCount`、`#beamCount`、`#gridSystemCount`、`#gridBindingCount` 拿掉，改成 `#sourceCount`、`#bindingCount`、`#structureCount`。匯出按鈕上的 `<small>.scene</small>` 改成可見的排除範圍，副檔名留在 `title`。組構、工程規格、無限網格各加一句首次教學，不設「工具說明」按鈕，看過即收，不佔常駐說明名額。
- 關掉「來源」會同時隱藏面、參數、網格系統和組構規則；不能再單獨隱藏柱。這是六顆換三顆的代價。
- 未套用草稿改走一個 `DraftGate`。參數建立與跳轉仍直接問自己的確認。無限網格對話框自己的離開確認留在關閉時，不併進這道門。保存專案時參數草稿仍是硬拒絕。
- 不新增頂列視圖、建立選單項目、左側快速鈕或檔案選單目的地。不改 GEO-227 的參數套到網格圖解。不改公理、核心或橋接器。


## GEO-230 — 組構原生寫入防護與收尾（2026-10-03，PR #52）

- Native `create-binding` 拒絕占用身分；`edit-binding` 依來源定義指紋與交易 revision 防止過時修改。
  正式工作區改用這兩個入口；保留 #51 的草稿意圖、正 uint32 回繞及 format 7。
- #50 的原生防護由本 PR 接續；不整併其高水位配號／實驗 format 8，避免破壞 #51 合法回繞。
- Q30 已核對上游模型雜湊修復，移至歷史；#20–#23 已結案，#19/#24 僅保留未驗 A24。
- 減項：沿用既有編輯與拒絕訊息，不新增入口或常駐說明。
- [驗證紀錄](geometry-web/docs/ASSEMBLY-CLOSEOUT-20261003.md)：非瀏覽器 1289 通過、0 失敗，
  1 項 Windows GDI 平台略過；ASan/UBSan 32 通過；兩個防護故障注入須由行為斷言抓到。
- #25 的[具體契約與逐條公理提案](geometry-core/ASSEMBLY-GENERATION-PROPOSAL.md)已備妥；
  現有 native 見證僅驗證幾何可行與支撐拒絕，不代表生成器已實作。條文仍待使用者看過核准。


## AR06 — 使用者核准的最小角材生成（2026-10-03）

- **公理**：D34/I42/R35，精確差異見 ASSEMBLY-GENERATION-PROPOSAL；不擴大到任意拓撲。
- **新增**：材料配置選取後才出現生成／實例来源編輯；沿用組構工作區、預覽確認、共用歷史與保存。
- **UI 減項**：移除發布配置檢視中重複的「尺寸都已填好」說明；不增常駐工具列或另一保存入口。
- **原生**：三構件穩定映射、生成所有權、原子重算、明確換版本、持久化能力 assembly-timber-generation/1。
- **驗收**：tests/test_assembly_generation.py、專案／傳輸／舊版本相容回歸及真瀏覽器 assembly_generation_test.js。
- **獨立審查修復**：第 8 版匯入納入既有原生來源與服務能力預驗。補真瀏覽器負例：僅實例草稿的專案遇到缺生成能力的服務時，必須在上傳前拒絕，世界、草稿與歷史全部保留；原缺口下負例確實失敗。隔離 Chromium 組構回歸 128 通過、0 失敗、0 未捕捉例外，另驗專案／工作區／歷史及模型相容／傳輸共 88 項通過。沿用既有拒絕訊息，沒有新增 UI 或常駐說明。
- **審查整合**：PR55 exact head `6f69c295` 完整非瀏覽器 1312 pass／0 fail／1 GDI 平台略過；full Chromium 1704/0、74 段 golden matched，唯一 raw 例外為 P38 預期注入，未預期例外 0；CI run37108412008 七組 success。已先合併修正至生成分支並將 PR53 retarget main。
- **主支支撐欄位修正**：沿用現行 R21 無序 between，將誤導的起端／末端標籤改為兩個無序支撐選擇器；保存鍵與幾何不變，副支有序 joint 不變。補原生交換支撐後幾何及 mapping 不變的第 18 個測試，18/18 已通過；現有真 UI 斷言也核對正確標籤。沒有新增控制、公理或求值能力，整合 exact-head 完整回歸與 CI 另附 PR。
- **限制**：實體手機的鍵盤與系統檔案操作仍未驗；Linux 執行不構成 Windows GDI 手測。

## GEO-231 — 啟動版本與頁面元件一致性（2026-10-03）

- 使用者回報 F-20261003-001：10/1 啟動的服務仍讀取更新後的頁面，卻沒有 10/2
  新元件的路由；`grid-trial.js` 回 404，`GridTrial is not defined` 使網格視窗初始化中止。
- `runtime_version.py` 以程式／核心／公理來源的內容指紋識別版本（文字統一 LF）。
  服務啟動時固定捕捉 HTML、JS、CSS、vendor；引用缺檔拒絕啟動。靜態元件由捕捉清單
  提供，合併原本兩份手列的 CSS／JS 路由清單，避免新元件漏列。
- `/runtime` 提供版本、repository、工作階段與 fresh。`start.ps1` 在連接埠已占用時
  必須驗證，舊版／未知／過期服務拒絕沿用，不自動終止現場。更新來源後，首頁以 409
  明示需重啟，修改與推導拒絕，保留 dump、讀取與 receipt 供保存及收尾。
- 頁面 API 帶版本；舊頁面不能修改另一版服務。過期拒絕不建立未確認的 receipt，
  也不留下組構確認鎖。缺網格元件時使用既有錯誤提示，不再先開空白工作區。
- 減項：合併重複靜態路由清單，沿用既有錯誤提示；不新增常駐說明、工具鈕或工作區。
- 不改公理、核心幾何或閱讀器。AGENTS 與 README 記錄開啟／保全場景／重啟驗證紀律。
- 驗證：Windows 全庫 `run_all.py --build --update-expected`，1297 通過、0 失敗，
  1 項具名 POSIX `/dev/full` 平台略過；新增測試數由完整跑更新（runtime 5、serve 30）。
  隔離 Chrome 網格模式 P70/P71/P78 共 138 斷言通過，無瀏覽器例外。過期服務拒絕
  修改而允許 dump、舊頁面版本拒絕、缺元件拒絕啟動、同尺寸同時間戳修改及 vendor
  更新皆有回歸驗證。正式 8765 重啟前後 dump 全等；使用者 Edge 的 915×1830 草稿
  已還原且格線可見；正式啟動器沿用目前版本的驗證通過。F-20261003-001/002 結案。

## GEO-238 — #44 F1a 有界唯讀來源／影響與快照內容檢查（2026-10-03）

- 自有 source-inspector native／JS／transport／adapter modules，由 World 型別建立可丟棄索引；不改公理或保存格式，不做 F1b、不隱含重建。原基線 main d40dee0，現整合 PR56/main 693a1c8，保留 PR63 format9，不重做 #54。
- 減項（GEO-219）：既有參數 `paramUsage` 的局部使用清單合併到共用「來源／影響與參數交換」，匯出／刪除控制保留；其餘入口都是既有檢查器／模型庫的按需 disclosure，無新工作區或常駐教學。
- 比對 native 逐來源指紋與 typed closure；來源缺失／變更／不完整明示。原格式缺 durable incarnation，內容一致仍註明延續性未知，不以整場景 hash 或名稱推斷現況。I9 candidate 不當成求值支撐；#47 原生 exact support 在同一 live／candidate World 原子適配，核對 typed placed/surface/lengthAxis 與八欄 owner，端點／來源改變即使幾何同值也列 source-definition。
- 整合 main9e（已合併65／66），保留唯一 runtime 靜態 capture。暫存 snapshot partial-write／bridge-error cleanup 用真實 tempfiles 修正並有 assertion-red baseline；過期路徑展開先驗 context／stamp。沒有新 UI 入口、永久來源保存或間接支撐求值推定。
- single owner 接線 adapter 不競寫 app.js、reference-workspace.js、project-store.js 或 native common。介面見 `geometry-web/docs/SOURCE-INSPECTOR-CONTRACT.md`；product head e30d4a2 同版完整非瀏覽器 1412/0/1 具名 GDI、無 filter CDP 1809/0/0 skip 且 76 段 golden matched、space 183/0、真 F1a browser 18/0、native 10/10、JS 9/9；native AST edge 遺漏 mutant 正確被抓（1 fail、編譯正常、無 skip）。完整命令、scope、版本、前次失敗及 PNG 見 `geometry-web/docs/SOURCE-INSPECTOR-VALIDATION.md`。未測實體手機；F1b、新公理／durable incarnation 與 #47 支撐 record 另案。

## GEO-232 — 畫布繪圖、hover 與版本檢查效能（2026-10-03）

- 使用者依程式碼審查結果，授權三個 agent 並行修正背景格線、滑鼠拾取請求與來源版本檢查。
- 背景格線依 SVG 視窗反算局部可見範圍，仍以世界原點對齊；極小縮放只抽稀裝飾格線，
  不改吸附間距、來源格線索引或核心查詢。平移只更新格線群，保留既有場景節點及 pointer capture。
- 主三視圖與投影共用最新位置排程，每個畫格合併移動、最多一筆 hover 請求在途；
  點擊與拖曳交易仍直接執行。場景、視圖、幾何、離開與拖曳切換會使舊結果失效。
- 版本檢查直接比較啟動時捕捉的來源內容，未變內容不重做正規化與 SHA-256；
  每次仍讀完整來源，偵測同大小／同時間戳修改、增刪檔及讀取失敗，不使用 TTL 或時間戳放行。
  已版本化的網頁資源與版本計算共用同一份捕捉內容。
- 減項：合併分散的 hover 請求排程，減少畫布不可見格線及重複雜湊；不新增可見入口或常駐說明。
- 量測：100 公里大面在 1200×800、100% 縮放的規劃測試只產生 82 條背景線，
  實際桌機視窗為 62 條；120 次同畫格 hover 更新只送 1 次請求。
  同一凍結來源集合（117 檔、8,699,956 bytes）各 100 次交錯量測，版本檢查中位數
  63.62 → 39.08 ms，下降 38.6%；每次仍完整讀取來源，並增加啟動內容快照記憶體。
- 驗證：新增 35 項回歸；三個專項共 40 項通過。合併目前 HEAD 後，完整非瀏覽器
  42 組、1370 通過、0 失敗，另 1 項 Linux 固有 GDI 略過已在 Windows 單獨通過。
  Chrome 桌機／390px 手機格線、平移節點保留及 hover 請求數驗證通過；
  空間完整流程 183 項、材料與來源競態流程 79 項通過。
- 完整畫布回歸仍未取得全綠：已完成的一輪為 1773 通過、3 項 P3 雙擊時序誤判，
  以及由此造成的 1 項計數不符；其餘 74 段符合 golden。已保留原斷言及 golden，
  修正 P5 隱藏分頁測試與 P3 進入表單的等待；更新後 P3 局部 48 項、其中 P3 全部
  14 項通過。最後的整輪重跑因收斂本次驗證範圍而停止，不宣稱整輪通過。
- 不改公理、核心幾何、保存語意或正典閱讀器；不重置使用者服務。
## ISSUE-45 — 單一網格原始輸入保存／續編（2026-10-04，實作驗證中）

- 已核准範圍：一個專案至多一份來源或配置 raw form；空白、錯誤、非作用中欄位與前後空白可保存、重開原值，未確認前不改 World。只有真 native 預覽及使用者確認才能發布；同一步保存 native 變更並收起對應草稿，undo/redo 一起恢復／收起。來源、參數、邊界與頂點身分在發布前核對，不用同編號的新值替換舊草稿。
- 接線：既有無限網格建立入口續編保存的草稿；輸入事件與保存前 flush 擷取原字串；載入期间原始欄位鎖定且保存拒絕；遲到回覆不重寫整份 raw form。未知確認結果保留原稿及回執租約，暫停編輯，返回畫布後按同一 request receipt 恢復，不重送 mutation。
- 減項（GEO-219）：原 footer 的 `igStatus`、`igDraftNote` 兩個獨立段落合為同一個狀態段落，拿掉重複常駐「所有變更先預覽」說明；原始輸入保存與預覽／錯誤共用該狀態行。新增的「捨棄原始草稿」是明确放棄目前唯一 F 草稿的入口，不另增工作區、續編按鈕或常駐教學。既有建立入口同時負責續編，取消發布保留 raw、返回畫布保留 raw，只有明確捨棄才清稿。
- 證據仍須真 desktop／390px app、完整 ZIP 保存重開、載入／晚回覆負例、native 取消／確認與一步 undo/redo、未知結果 receipt recovery；CLI／VM 模擬不代替真瀏覽器，A24 實機 IME／chooser／下載另留未驗。
- restored raw 解讀／來源回歸：未知排格 enum 原字串可保存，解讀時明拒；保存與被動重開不補目前 catalog 的 pin，明選才建立證據。`grid_raw_provenance_browser_test.py` 必須跑真 v10 檔案入口、缺／錯 pin、native 刪除重建、真 ZIP 保存與 fresh browser 重開、明選正例、取消／確認及一步 undo/redo；local raw 編輯依既有 metadata history 記錄，不能冒稱 native 變更。

## ISSUE-77 — 來源歷史保全與多房間共享基準（2026-10-04，接線驗證中）

- 經使用者批准，含紀錄或原核對收據的明選原頁轉入 `source-rooms/2` 有界歷史附件；原紀錄未知 JSON 欄位、待補 null 與完整原收據保留。`source-room-history/1` 能力標記使不支援的閱讀器明拒，無歷史的既有 `source-rooms/1` 維持原格式。來源原檔隨歷史平面閉包保存；歷史邊界號不推定仍是現行原生物件。
- 減項（GEO-219）：原頁的可編輯紀錄與舊核對狀態合併到既有房間來源區／專案資訊的按需唯讀歷史，不增工具列或工作區。一次顯示所選原頁，舊收據不確認目前房間；共享基準改變只標記現行房間需複核。
- 明選 adoption 先驗原始 JSON 並凍結原頁、收據與附件，原生指紋回覆後再守住上下文；一筆 local undo 同時恢復原頁、紀錄、原收據與附件。解除房間列表保留歷史及原生幾何；含歷史的平面拒絕移除，避免默刪原檔或證據。
- 驗證須包含真 owner/browser 明選、完整 ZIP／fresh-context 原檔與原資料全等、一步 undo/redo、basis-change、stale/cancel/未知回執、新 ID 拒覆蓋與版本／容量拒絕保全；native 候選指紋由獨立 native owner 提供，同版 consumer 與完整 gates 通過前保持 draft。

## ISSUE-44 — 明選現行來源更新同一模型（2026-10-04，接線驗證中）

- 既有模型修改入口保留保存來源的牆高修改，另明選現行放置面、外環邊、角材／柱樑及投影用途；準備與差異候選不寫模型。確認前重讀來源、重跑完整 producer，最後 guard 後同步 `updateSpaceModel` 替換同 record，一筆 local undo 保存完整舊來源／input／全部結果包。
- `ReferenceWorkspace.getModelOperationState()` 提供凍結的操作快照與 opaque scalar 身分；模型 UI 不再讀 context/history 內部。保存／載入／group／未知確認／連線／編輯權限等拒絕由 owner 判定；服務 session 變更使候選失效。候選、明選及 pin 只在對話框內，取消丟棄，不增保存 schema 或 F 附件。
- 減項（GEO-219）：沿用「修改模型」與原牆高區；原高度摘要和獨立常駐說明合併，兩種來源差異在同摘要說明，移除重複 help 段，不另加模型列表或常駐更新提示。
- 必要驗證：真 owner 入口、fresh runtime／exact head、真 producer 全部交換包、新舊差異、cancel/stale／late reply 零寫、明選及 one undo/redo、完整 ZIP 重開。空間／投影／牆高專用瀏覽器回歸另外執行，A24 實機界線保持。

## GEO-242 — PDF 人工描繪原始線段吸附（2026-10-03）

- main `0f3c1a6` 真 Chromium 重現：人工描繪只吸網格／草稿頂點；9% 描繪實用 500 mm，工具列仍顯示 50 mm。原 main 在獨立來源端點 oracle 出現 assertion failure。
- 已校準 PDF 接原始直線端點与保守閉合線段交點，8 px 螢幕容差先於網格；明示來源頁與線段，取整 mm 且不投影成不存在的正交角。文字／曲線／虛線／裁切／影像不提供特徵，開放尺寸線交叉不提供交點；不宣稱牆角辨識或內緣。
- 減項：合併到既有描繪預览與座標列；格距欄取代誤導的手選值顯示，不加入口、常駐說明、保存格式或第二份正式幾何。公理、核心與房間候選推估未修改。
- 來源特徵僅執行期快取，遲到擷取不重放落點、不改 geometry/history；頁切換／對位改變後不顯示舊目標。私人 PDF 不上傳；public fixture 以真輸入驗證旋轉／校準／取消／undo／snap off／raster，完整與 exact-head 結果附 draft PR。

## GEO-243 — 一般啟動入口補齊空間預覽元件（2026-10-04，驗證中）

- 使用者已選面 #2、牆底 0／牆高 3000，畫面卻顯示「預覽回應缺少空間或摘要」。實際 HTTP 回應是 `UNSUPPORTED / BASE_COMPILER / I32`，預覽前後核心 dump 相同；一般入口只編畫布 bridge，未準備建模 adapter。
- `start.ps1` 同時編譯並實際驗證 WSL 建模 adapter。Windows Python 明示使用該 adapter，經獨立 argv 與路徑轉換呼叫；明確指定的原生執行檔仍優先。每次啟動使用獨立暫存執行目錄，避免測試或其他 port 重編使用者正在執行的二進位。
- 前端依正式建模 `status + diagnostics` 拒絕失敗回應，保留幾何诊斷，元件未就緒時顯示可採取的保存／重啟步驟，不再誤報成摘要缺失。
- 不新增 UI 入口或常駐說明；不改公理、來源幾何、保存格式或正典閱讀器。使用者服務重啟前保全完整 `.gcanvas`、核心 dump 與既有瀏覽器恢復資料；测试只使用獨立 port 與 TEMP 回報目錄。
- 驗證：WSL 真實 adapter 的 modeling runtime＋space modeling 72 項通過；Windows 呼叫 WSL 的模型保存／重開與錯誤回應 20 項通過、無 skip；隔離 8779 真 Chrome 預設空間套件 183 項通過、無例外／console error（該套件不含另外的 timber-material／timber-source-guards 組）。面 #2 的實際請求生成 8 面、0～3000 mm、37.285476 m³；預覽前後 dump 相同。
- 完整 `run_all.py --build --update-expected` 受 Windows `Path.stat()`／`os.fstat()` ctime 不一致阻擋，原生執行檔註冊失敗，不能視為全套通過；工具拒絕更新數量清單，新增測試的 census 更新仍待完成。未降低門檻或繞過執行檔來源驗證。
- 使用者後續画面已能預覽，8765 runtime 為目前來源的 `fresh:true`，面 #2 原 dump 保留；另一個方向一致性問題另記 GEO-244，本項測試不等於原圖方向驗收。

## #116 — 面內游標 v2 與 B 右鍵選單（2026-10-05，草稿 PR #125 交 dot；合併 gate 受阻）

- 採使用者提供圖片的 B／1b：272px 動作卡＋搜尋精簡清單、296px 側接參數表單，邊緣翻轉；資料與提交使用原有操作、預覽、影響確認、取消及歷史，不另建命令來源。
- 減項（GEO-219）：取代原右鍵純動作清單；右鍵開啟時收起重複浮動操作列，關閉再還原。停用理由合併至選單既有 footer，未增加常駐教學；側接表單重用唯一 `feOpPanel`。
- 先驗收面內完整切片；物件畫布、空間平面圖與三視圖仍列後續範圍。複製／貼上／重複與多選批改、觸控長按／偏移準星／雙指不假稱完成。
- PR #114 共用 app／index 的接線以最小 diff 保留；不動 ReferenceWorkspace、project-store、room-collection 或核心。整合交 dot，不自行合併或部署。
- 正式 gate：`tests/test_issue116_browser.js`＋`geometry-web/cdp_test.js`；證據與限制見 `geometry-web/docs/ISSUE116-B-HANDOFF.md` 和根目錄 `design-qa.md`。
- 87項真browser/native、共用73項、模型更新39項、多房間56項通過；dot首輪source review的未放置參考線P2已修正並補8項真驗收。最終`dce2975`／ee9f版本完整 `cdp_test.js`：1586通過／0失敗，但在P76等待逾時而未完成，未比對golden。實際trace為參數卡engineering-confirm拒絕Missing, invalid or unrelated engineering preview token後，等待!ParameterUI.pending逾時；沒有把0失敗斷言說成全量通過。詳細fatal與分段見validation.json。 CI未啟動及dot最終head／owner／實體裝置gate未驗，保持草稿。已rebase到#114合入後861b65e並保留雙方scripts；詳細分段與來源hashes見validation.json。

- 2026-10-05 更新：普通 merge 納入最新 main `4bea91a`／#124，原 B 與 owner 修改都保留。使用者追加 3D 旋轉裁切回報，`0e555ed` 補齊拖曳／方向鍵的投影 fit scale；沿用置中、缩放與平移，未新增 UI、未改網格／體積。B87、共用73、模型39、預設完整空間202及桌面／手機旋轉畫面驗證通過；原全量CDP／CI／dot gate維持，細節與限制見交接報告的本次更新段落。

- 同日再同步 main `417f4c0`／#127（普通 merge `b38c417`）：新版B87/87、預設完整空間202/202；完整CDP1407/1未完成止於P73引用線，native命令成功而斷言false，原因待定；未比對golden、不宣稱越過P76。掛載磁碟19/7及Linux browser746/1、8/2未完成均保留為失敗。8817 d6d來源當時fresh、保存場景逐字恢復，最終服務已停止，未重開使用者視窗。仍為草稿交dot，full／CI／owner／實體裝置gate保留。

- 最後同步 #126／main `8d134fc`，普通merge `1a21b5d`；共用保存／載入owner檔逐字保留，bridge依新include重編。最新來源B87/87、共用＋formal store106/106（0skip）通過；凍結b38來源的full／SPACE收據另列checkpoint，不冒稱為最新head完整回歸。最新combined full／SPACE及CI／owner交dot，草稿不自行合main；8817已關閉，原檔／備份保留。

## GEO-244 — 描面畫布與空間俯視方向不一致（2026-10-04，方向修正驗收通過；全量驗證限制見下）

- 使用者面 #2 的 191×913 mm 凸角在輪廓編輯圖左下，3D 俯視顯示在左上。編輯圖沿局部 u→／v↓，承載面卻是 U=+X／V=+Y，而世界俯視是 +X→／+Y↑。既有 GEO-207 的局部編輯圖／世界投影區分確實產生相反的上下畫面方向。
- 以使用者當下唯讀 dump 及隔離服務生成的真實 mesh 核對：z=0 與 z=3000 的六個原始轉角全部保留，頂底邊界（含引擎分割線段）精確等於來源六邊；37.285476 m³ 等於原輪廓面積×3000 mm。擠出未另改 XY，但這只能證明模型忠於已存座標，不能證明描繪的俯視圖已正確對齊世界方向。
- 使用者明示要求修正後，沿既有 D2／D4 放置及 I8／I8a 影響確認調整所選放置框架：保留 U，按原圖俯視／仰視決定 V 的方向，以局部 V 外框中線調整原點，保留世界外框及圖面 z。局部輪廓、PDF、其他放置及已建模型不被重寫；不改公理或核心 C。投影定義本身仍只保存用途資訊，不自動搬移既有場景。
- UI 減項／合併：重用原本的「確認用途與觀看方向」區塊與按鈕，保存定義但方向不一致時改作「依原圖對齊放置方向」；說明合併在既有段落，未增加常駐入口。完成後要求重新預覽；牆底、牆高、牆厚及納入角材的選擇保留。來源或歷史過期時零寫入，有角材時沿用原生影響預覽及取消，成功僅一筆復原。
- 檢視器使用真實網格；俯視仍沿 −Z、仰視仍沿 +Z，平面檢視沿原面 U 軸向右。已保存模型從其既有 `input.base_scene` 讀框架，不新增保存欄位、不改 mesh。
- 驗證：8 種水平放置×俯視／仰視的外框、方向、冪等及輸入不可變契約通過；隔離真 Chrome 投影／放置与版面 53 項、預設完整空間套件 196 項通過，無例外／console error（預設套件不含另列的 timber-material／timber-source-guards）。實際 191×913 mm 凸角的左下填色及左上空白像素通過，保存重開仍相同；選中放置之外的 dump 完全相同、單步復原／重做、過期來源拒絕、角材影響預覽取消均通過。初次全量的舊 fixture helper 以「確認區隱藏」當作已保存定義，新增對齊入口使此條件過期；修正 helper 為明確核對四個已保存語義及非忙碌狀態，未減少斷言或調低固定門檻。196 項通過的是對應修正後 helper 的 TEMP 驗證副本；工作區已同步，獨立 read-back 在還原副本的三個 require 路徑後與工作區逐字一致。新增真檢視器相機驗證亦通過：旋轉／反向 U 均向右、俯仰觀看側正確，mesh 與 bounds 不變。
- `cdp_test.js` 全量跑至 P73：1407 項通過、1 項失敗，未完成及未比對 golden。失敗是參考線「已知邊一半」的 UI 斷言；本次未修改該功能、app.js 或核心。另開全新隔離服務執行 `GEOMETRY_UIUX_FIX_ONLY=1`，包含同一斷言的 P73 65 項全部通過，無瀏覽器例外；此結果不能取代全量通過，長流程狀態／時序原因尚未判定。整體 `run_all.py` 的 Windows 執行檔身份檢查受阻及 census 未更新見 GEO-243，未繞過驗證。
- 使用者完整 `.gcanvas` 在重啟前與核心 dump 逐字一致，重開後再次一致且 PDF 底圖實際顯示。實際對齊後只有面 #2 的 placement 行變更，其他場景逐字不變；外框仍 X=4811～8635、Y=1165～4538、z=2700 mm。正式 adapter 產出 8 面／0～3000 mm；上下底面六條邊逐段核對完全一致，空間 37.285476 m³、100 mm 外側材料牆 4.4382 m³，預覽前後 dump 一致。
- 另存完整方向修正版並保留原檔，除場景指紋與 placement 外，清單、底圖 bytes、校準及投影定義全部一致。修正版已經正式專案匯入／重新匯出與真 Chrome 實際預覽驗證，來源 bytes 與面關聯保留、體積精確、俯視左下凸角像素成立，無例外／console error。私人 PDF、專案及截圖均留在使用者本機，不進 git。
- 最終工作區測試 helper 同步後，以一般入口重新啟動使用者 8765，`/runtime` 指紋符合目前 repository、`fresh:true`；載回修正後核心場景並逐字核對。完整修正版為本機 `D:\未命名專案-方向修正.gcanvas`，原檔未覆寫。Edge 擴充功能無本機檔案存取權，先前完整專案由使用者手動開啟；最終重啟後已請使用者手動載回修正版，尚未收到完成回覆，不宣稱最後這次瀏覽器已恢復 PDF。隔離測試服務已停止，使用者服務與分頁保留。

## #61 第一正式來源規則 UI 切片（2026-10-05，PR133，開發中）

採納範圍為兩軸無相位差 REPEAT 的 all-cells／單 signed cell 規則 CRUD，真 native 預覽／確認／取消、typed source baseline、單步 ContextHistory，以及有限原始規則草稿隨正式 ZIP 保存／新空白 context 重開。沿同一 2a 來源表單，不另造規則管理器或幾何求解器；raw `/2` 和格式 `/13` 保留舊 `/1` 讀取。

UI 減項（GEO-219）：規則預覽併入原固定頁尾，規則輸入期間收起來源預覽，維持單一主確認動作；等分說明收斂為情境式輸入區一行，不增加常駐教學卡或全域工具列。來源規則和本面手動子格仍依正式契約分開。

未宣稱完成：已確認子線 display/pick、RuleLineRef、guide/direct、跨面正常完整流程，SR24 實體手機仍人工待驗。不关闭 #61/#62。實測與精確 head 會回填 [切片驗收紀錄](geometry-web/docs/ISSUE61-SLICE1-20261005.md)。

## #61 第二正式來源規則 UI 切片（2026-10-05，開發中）

main d6b4b45 與 PR133 審查 tree 完全一致；接續原生規則子線顯示／命中／標籤、完整 RuleLineRef 來源→配置→套用追溯、同一來源規則編輯器定位，以及既有 guide／direct 引用。查詢只讀、過期回應零寫入，裁切與合法性由原生決定。跨面共用來源沿既有影響確認與 ContextHistory，不增加幾何求解或保存格式。

UI 減項（GEO-219）：規則線資訊併入既有 GridEditor 的來源／局部等分區；共用既有定位引用、guide 來源清單及來源規則編輯器。主格、来源規則子線、本面手動子格以既有區域內的文字／線型辨識，不新增工具列或獨立規則管理器。pending footer 合併提示已確認來源與未確認規則輸入；等分錯誤直接使用 1–65 的產品範圍。

先釘住 main 缺口：同一 synthetic native cell 回傳 3 條子線，正式畫布、角材選項及 guide 來源均為 0。SR24 實體手機仍保留人工 gate；#61/#62 不關閉，尚未驗收範圍不能以顯示完成冒稱。


## #49 正式案例接線 — shared integration checkpoint（2026-10-05）

- 六個有限案例沿用 PR141 元件、HTTP adapter 與既有真 C executor；在組構工作區按需開啟。共同附件註冊 `rule-cases` / `rule-case-workbench-data/1`，核對未占用後新增 `geometry-canvas/15`，既有 /1–14 行為保留。原 definition / receipt 分存；匯入及保留後重掛載只顯示歷史未核信。
- 以原始 ReferenceWorkspace stamp / frame / native revision / runtime 接短命 immutable binding；每 native context 獨立有限高水位与 late cancel tombstone，不能改 A/B editor allocator。關閉案例只撤銷其 adapter；不關 live native 或 AssemblyWorkspace 候選。保存沿共同 detached prepare 與同步 guarded metadata commit，完整 root/A/B manifest 容量與房間 lifecycle 預留均先驗；no-op 零 history，取消／晚到零寫入。
- **拿掉／合併（GEO-219）**：移除預設組構內容重複的「新增規則後，依序建立槽位、構件與局部接合」常駐說明，沿用既有工作區首課；案例輸入、作者預期、實際結果與歷史明細合併同一按需面板，沒有新增頂層工作區。
- 這是實作 checkpoint，完整 current-head aggregate／桌面及390px terminal 尚待完成；不宣稱 #49 完成，不借用 #137／#143 的舊 full receipts。產品／測試 source 可獨立審查，原始公開證據拒絕包維持 hold。
