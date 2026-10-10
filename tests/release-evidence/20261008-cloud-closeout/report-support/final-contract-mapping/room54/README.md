# #54 單房候選：契約、效率與現有證據核對

這是唯讀核對，未跑 browser/native/產品測試，也未修改 repo、public-candidate、queue 或外部工單。受測產品為 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；核對時 repo HEAD 是文件整合頭 `d8642b2e684038cbb8e24aba057c44e7aac1b231`，稍後觀察到另一 owner 正修改 `geometry-web/docs/RELEASE-CANDIDATE.md`，詳見 `review-command-evidence.json`，本核對不把它當成受測 dirty diff。

## 判定

1. **效率要求已有具體比較方法，並非整項未定案。** [issue 原文](issue54-body.txt) 第 41、105、113 行要求非機密矩形／L／凹口、同組夾具／起點／核對終點，比較實測操作次數或時間，包含修正及尺寸核對，報告改善和失敗案例。第 9 行的目標是降低取得所需輪廓的操作成本。後續 Agent 任務第 57 行保留原驗收要求。檢視來源中未找到採納的「至少少 N 步／快 X%／最多 Y 秒」、真人受試人數或固定入口數上限；不能自行補一條門檻。
2. **現有比較已實跑，但结果依操作協定而異。** 當前正式 room-acceptance 的六組完整修正／逐邊入值比較，候選各多 5／7／9 個計數動作；同版本完整 CDP P79 的單一已知邊長核對路徑則少 5／7／9 個計數動作，門洞失敗再備援多 2 個。不能把不同協定當版本退步，也不能只取有利一組宣稱全部更快。
3. **#153 pan 和 #155 Enter 的有界產品修正已有當前候選 browser 證據，兩份 PR 摘要更新已完成。** 整合 owner 於 2026-10-08 19:36:48／49Z 更新摘要，REST GET 逐字核對成功，原 head 與歷史 body 完整保留；見[摘要修訂收據](../../../report-support/pr153-pr155-summary-corrections.json)。兩 PR head 均為受測候選 ancestor（命令 exit 0）；不應再當成未整合實作。這不等於 #54 整單完成，更不等於效率目標已獲真人驗收。

## 已採納要求與未定義事項

| 類別 | 具體內容 | 來源／判定 |
|---|---|---|
| 已要求 | 記錄實測成本，與人工相同起終點比較；包含修正和尺寸核對；揭露失敗 | issue 第 41、105、113 行。比較本身不是等使用者再拍板才能做；現有兩套 raw 均已可核查。 |
| 已要求 | 利用現有「底圖 → 描外環」，不另建工作區／常駐入口；先記實際 UI 減項 | issue 第 30–34 行；AGENTS GEO-219；BACKLOG 第 198–230 行。實際移除 reference-intro/calibration-instruction、合併核對區；#153、#155 不新增可見入口。這是 UI 範圍約束，不是未公布的操作數上限。 |
| 已要求 | 原面在確認前不改，失敗／取消保全，成功可 undo/redo；保存真重開並對位 | issue 第 38–43、92–104 行；ROOM-OUTLINE.md 的候選與保存契約。 |
| 未找到採納決策 | 統一最低改善幅度、真人時間或受試者樣本設計、所有圖面一律更快 | 查閱範圍完整列在 source-manifest.json，包括 issue、兩 PR、BACKLOG、決策佇列、三份 continuation 文件、ROOM-OUTLINE/ISSUE54-VALIDATION/closeout 和 INTEGRATION-GATES。此為在該已取得來源內的查核結論，不聲稱不存在未交接私人決策。 |
| 明確排除 | 一鍵全屋、任意圖面、#87 多房；自動猜牆高／厚度；未授權公理變更 | issue 第 21、25–29、84、103、121 行；單房 closeout 範圍。#87 自己的 34 個 gate 不能挪來完成 #54 效率。 |

## clean 5174 的成本原始結果

來源：[room-acceptance canonical result](../../../gates/room-acceptance/artifacts/results.json) 的 `measurements`，無估算；抽取見 [acceptance-cost-measurements.json](acceptance-cost-measurements.json)。六例各有三個成功具名 oracle：`manual comparison starts from identical native scene`、`comparison source, camera, snap, review and disclosures share the same start`、`manual comparison ends at exact same reviewed geometry`。索引分別是 results 17–19、40–42、63–65、97–99、120–122、143–145。

| 夾具 | 候選動作 | 手繪動作 | 候選減手繪 | 候選／手繪機器 elapsedMs |
|---|---:|---:|---:|---:|
| PDF 矩形 | 21 | 16 | +5 | 3469 / 2175 |
| PDF L | 27 | 20 | +7 | 4353 / 2442 |
| PDF 凹口 | 33 | 24 | +9 | 5193 / 2662 |
| PNG 矩形 | 21 | 16 | +5 | 3228 / 2033 |
| PNG L | 27 | 20 | +7 | 4250 / 2381 |
| PNG 凹口 | 33 | 24 | +9 | 5297 / 2714 |

協定在 `tests/room_outline_acceptance_browser.js:209` 的 `correctAndReview` 與 `:237` 的 `manualComparison`：候選真改一次尺寸、經頂點文字修正回精確輪廓、每邊 select/fill/apply；手繪逐點畫、真改一次尺寸再改回、每邊填尺寸、核對。點擊、拖曳、選項、文字替換各算一動作，Tab 隸屬該文字替換，含工具／分頁／disclosure；匯入校準、保存開檔、locator 自動捲動不入成本。**此為已實作完整修正路徑在固定計數協定下成本較高的內部證據，並非一個被設成必須更快卻失敗的 gate assertion。** 不把 253 個 pass 解讀為成本改善。

來源：[full-cdp-r3 raw log](../../../gates/full-cdp-r3/command.log) 的 `ROOM_OUTLINE_MEASUREMENTS`；抽取見 [full-cdp-p79-cost-measurements.json](full-cdp-p79-cost-measurements.json)。P79 `geometry-web/room_outline_test.js:50` 和 `:69` 兩路都只入一個已知邊長，然後核對。六例候選均 7 動作，手繪矩形／L／凹口各 12／14／16，PDF／PNG 同；開門洞先失敗再備援 14 對 12。這保留了改善與失敗實測，但不是逐邊入值／真正尺寸變形後修正的同一測量協定。2026-10-03 `ISSUE54-VALIDATION.md` 的 7–8 對 12–16 是历史版本資料，也不能替代當前 253 gate 的較重協定。

兩套 elapsedMs 都包含 automation settling，並不量測人的閱讀、判讀、找點與核對時間。#155 Enter gate 證明可替代該次 apply 點按，沒有測完整候選流程的計数優化；當前 acceptance 比較仍使用按鈕，因此不能直接從 Enter pass 推出成本降幅。

## 原要求映到已完成有界證據

完整結果名稱／index 已抽取為各 `*-oracle-index.json`，沒有刪除失敗輪。版本、runtime、命令、exit 及 original artifact hash 由各 gate 的 receipt/audit 保存，摘要在 [gates.json](gates.json)。

| 原要求／已交付修正 | 當前具名 oracle 與證據 | 判定／界線 |
|---|---|---|
| 校準→PDF/影像候選，矩形/L/凹口，疊圖與未提交保全 | room-acceptance `expected local acquisition method`、`exact cyclic topology with correct concavity`、`candidate overlay and untouched original`；六例及 box、mobile、transform | 253/0 完整 gate，命令/gate exit 0。box 候選估計容差是來源一像素；正式結果仍精確 authored ordered oracle，不把估計寫成 mm 精確量測。 |
| 修正／核對，確認／取消，核心拒絕，Undo/Redo | `dimension changes candidate only`、`each displayed edge checked against independent oracle`、`Confirm creates exact ordered oracle geometry`、`Undo exact original`、`Redo exact confirmed`；results 246 `core rejects self-crossing orthogonal ring without changing original` | 已驗給定合成場景。不從通過數推人因效率。影響確認取消在 full CDP P79 既有原子拒絕/取消路徑，不能聲稱 253 gate 單獨包含一切。 |
| 門洞／鄰房不能猜牆、框選不能冒充房間 | results 237 `explicit failure leaves original scene and no completion receipt`；241 `connected neighbor is disclosed instead of silently excluded`；242 `explicit search separator excludes neighbor without editing source geometry` | 指定反例已保留；不是任意實圖辨識保證。 |
| Save/清空/Open，來源/校準/receipt/模型 | 每例 `new project is actually blank before Open`、`Open preserves exact native ordered topology`、`Open preserves source bytes, page, transform and calibration`、`Open preserves exact confirmed receipt`；pdf-notch results 71–81 驗全輪廓投影、完整 model、再次清空重開 | 真下載、新 browser context、產品 chooser。boundary-only model，明填高度，未驗所有凹口材料牆；非真 OS picker。 |
| 不誤報完成；重新校準／來源改變要重核 | results 247 `recalibration requires review and retains exact confirmed geometry`，249 `source replacement retains exact geometry and becomes unreviewed`；各例原矩形 unreviewed/candidate/confirmed | 已驗範圍內完成，不能把任意頂點當成功。 |
| #153 Space／中鍵／H 平移以及取消後續接 | room-pan 32/0，`picking Space moves camera by pointer delta`、`pending Space ...`、`reviewed Space released before pointerup ...`、`cancelled selection then Space ...`、`selection continues after cancelled selection and pan with exact room ring`，各比 draft/source/review/native | 當前候選已補 browser，不再只是 VM。初始 API fixture、pointercancel 注入明示；不是觸控硬體證明。 |
| 舊 Worker 不能復活候選或清新工作 | room-worker 78/0：cancel-pdf、cancel-image、recalibrate、close-reopen-face、change-pdf-page、replace-source 各 `explicitly injected late callback cannot revive old draft or clear newer job`、`late callback preserves exact native dump`、`only current ordered ring and source basis become an unreviewed candidate` | 12 個真正 Worker 計算；真 terminate 後送留存 consumer callback 是明示故障注入，不是自然仍送訊息或 memory cleanup 證明。 |
| #155 Enter 等价 click、所有權、非法值、IME guards | room-keyboard-r2 396/0、64 操作案例：desktop/narrow `real Enter changes nonzero edge exactly`、`Enter equals existing click draft result`、`one existing apply action per Enter`、`held Enter repeat does not apply again`、舊 detached/connected input 不套用、非法 Enter 保留模型 | 1440/390 真鍵鼠；composition/229/defaultPrevented 與舊節點是標示注入，實體 IME 未驗。原 room-keyboard 中斷輪保留 372 pass/1 fail、command/gate exit unknown，不以 r2 覆蓋。 |

四 gate 均受測 clean 5174，runtime `82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200`。acceptance/pan/worker 的 session 為 `86b719350c9d4e3b90536403b05f9dcc`；keyboard-r2 為重啟後 `ca31be77efb542b89d45d5a88c3b1b45`，不混成同一服務工作階段。四命令依次為 `node tests/room_outline_{acceptance,pan,worker,keyboard}_browser.js`，實際 launcher/完整環境仍以原 `*.command.json` 和 receipts 為準，不能照舊文件中 --no-sandbox 重建。

#153 `349e2a590f98ab783b7d3eeb952e95151db8e39e` → #155 `f1e020cba5051a331dd150d567698060bf1642b1` → clean 5174 的祖先關係已核。PR 舊文 body 原件在 `pr153-body.txt`／`pr155-body.txt`；整合 owner 已完成本輪 exact-head browser 證據的摘要補充，原歷史 body 逐字保留，head 未變，不改寫歷史 native tree-equality 收據。REST PATCH／GET 命令均 exit 0，見[摘要修訂收據](../../../report-support/pr153-pr155-summary-corrections.json)。

## 仍缺什麼，由誰怎麼解除

| 類型 | 精確缺口／下一步 | 不應作的推論 |
|---|---|---|
| 內部產品目標／研究缺口 | 指定單房產品 owner 分解重協定的 select/fill/apply 與頂點修正成本，依既有 GEO-219 在現有入口評估有界減重；如改流程，保留同起終點、真正修正及核對的比較，公布好壞案例。第一步是核看上述兩套已封存協定，無須重新跑同版四 gate。 | 現有完整修正協定未顯示降低動作成本；不能說「只剩外部真人驗收」或「因未定數字所以可算完成」。也不能宣稱所有操作路徑都較慢。 |
| 已完成的報告修訂 | 本報告並列較輕 P79 改善與較重 253 協定成本增加；#153/#155 摘要已更新並經 REST GET 逐字核對，browser pending 保留為歷史敘述。Enter 全流程效率仍未量測。 | 摘要更新不證成 #54 完整修正路徑的降成本目標。 |
| 真外部裝置驗收 | 有實體裝置的 QA 在凍結候選核手機輸入/拖曳、實體 IME composition/Enter，以及 OS Save/Open picker。記具體版本、動作、原始輸出與失敗。 | 390 viewport、synthetic IME、download/file-chooser seam 不能代替。 |
| 真人效率證據／決策 | 使用者或產品 owner 如需真人速度結论，先指明受試任務與代表性使用者，按 issue 既有相同起終點規則收實際觀察；最低降幅與樣本數目前未找到採納值。 | 不自行規定 N 人/X%，也不拿 machine elapsedMs 當人的時間。這不阻擋承認現有自動動作量測已完成。 |
| 私人實圖可取得性 | 已封存 issue/closeout 記載 CaseA 歷史失敗、新頭未验與 Library network 取得失敗。持有已授權原檔的本機 owner 在最新候選重做既定 CaseA/CaseB 並回原始收據；若需交接，先核已獲准入口，不猜 URL、不公開私人圖。 | 此輪沒有取得／重驗私人 bytes；不能用合成 pass 消除歴史 edge-open/tooManySegments，也不能把私人檔不可得擴成所有公共夾具流程阻塞。 |
| CI 外部執行條件 | 對擬交付 exact head 由有帳務權限者恢復 runner 執行，再核 runner/steps。 | runner=0/steps=[] 是未執行；本核對不變更帳務，不用 CI 阻塞否認本輪本地證據。 |
| 後續範圍 | #87 同頁多房獨立既有授權；全屋、自動猜牆/尺寸/OCR、不明新公理仍排除。 | 不為 #54 收尾把提案或其他 issue 的 pass 合算。 |

可以接收 #153/#155 的有界修正及上述已驗流程；不能把 #54 整個目標描述為「只有外部條件」。最精確狀態是：**单房功能閉環與兩項修正已有整合候選證據；成本比較已做、結果混合，完整修正路徑的降成本目標尚未證實；外部裝置／真人／私人實圖驗收另列。**
