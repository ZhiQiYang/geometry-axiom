# K3 識別與追溯擴充：共用身分帳（identity-ledger/1）與 #48／#44 首版契約提案（r5，定稿）

- 狀態：**r5 提案（定稿）；全部岔路暫定（依 2026-10-09 授權 L）**。r4 經第 5 輪 opus 聚焦審查：**`AXIOM-DIFF.md` 條文本身沒有問題**，剩 4 項在 PROPOSAL／decisions 的實作段須先改（S1–S4），外加 6 項僅記錄（R1–R6）。要點與主迴圈裁決原樣在 `review-round5-findings.md`，本版依該檔修訂，完成即定稿；仍未寫入 SSOT。r4 原文在 `r4/`，r3 原文在 `r3/`，r2 原文在 `r2/`，r4、r3、r2、r1 對照表留在下方，r0 原文在 `r0/`。
- 基準：`a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e`（`公理層.md` 與下列程式行號都是該 blob 的 LF 行號）。工作區 HEAD 不一定有這些行。
- r5 對 `origin/main`（`c254e1f`，2026-10-10）的核對：`公理層.md`、`current_geometry.c`、`geometry-web/web_bridge.c`、`geometry-core/*.inc`、`geometry-web/*.inc`（含 `engineering_bridge.inc`）、`geometry-web/scenario_verify.py`、`geometry-core/modeling/*` 與基準相同，行號照用；`serve.py` 的 `:290`、`:463` 兩行未動（檔案他處有改）；`scenario-workspace.js:64-65` 未動。`app.js`、`reference-workspace.js`、`space-workspace.js` 在 main 有位移：**§2.5 的兩張表把基準與 main 行號分欄標明，不混寫**（r5，R4）；本檔其餘處的行號以基準為準，涉及這三個檔案時另標 main。主要位移：握手 `app.js:491`→main `:565`、連線階段白名單 `:539`→`:613`（`if` 起於基準 `:538`／main `:612`）、匯出 `:1458`→`:1605`、`:4272`→`:4457`；`reference-workspace.js` 的 `restoreSession` 讀取 `:290／300`→`:293／303`（比對 `:291／301`→`:294／304`）、寫入 `:198-199`→`:201-202`、`:1262`→`:1265`、`:1413`→`:1416`、`:1451`→`:1546`、`:1772`→`:1867`、`:1824`→`:1919`（main 的 `:1824` 是 `fetch("/upload/prepare")`，不是 `recoverLoad`）；`space-workspace.js:435`→`:445`（其餘使用點 +10～+15 行，見 §2.5 表）。main 另新增 `reference-workspace.js:1517`、`:1522`（試改續接核對 `journal.sceneHash`），歸「維持完整 dump」（§2.5）。實作時以 main 再掃一次。
- 不改 repo、不 commit、不 push、不留言。條號一律佔位 `D⟨K3-n⟩`／`I⟨K3-n⟩`／`R⟨K3-n⟩`，寫入時由主迴圈統一配號（PF-0 修訂版已佔 D41–D45／I52–I57／R41–R46）。
- 配套：逐條差異 `AXIOM-DIFF.md`；岔路 `decisions-provisional.md`；本檔 §9 自檢。
- 限制標籤用 `K3-LIM`，不用 PF-0 已占用的「已知限制 K3」。

## r5 修訂對照表

全部暫定（依 2026-10-09 授權 L）。裁決全文見 `review-round5-findings.md`。第 5 輪審查結論：`AXIOM-DIFF.md` 條文本身沒有問題，須改的都在 PROPOSAL／decisions 的實作段。r5 完成即定稿。

| 項 | 裁決（含我核對到的事實） | 本版修在哪 |
|---|---|---|
| S1 | 去身分 dump 指令加進 `app.js` 連線階段白名單（main `:612-613`，基準 `:538-539`）；§2.5、§4、K3-Q30／Q35 補列；L-20 加突變「拿掉白名單項 → 兩案都紅」。核對：連線未就緒（`connection.phase==="loading"`）時，`apiRequest` 只放行九個指令（`objects`、`surfaces`、`boundary`、`references`、`obstacles`、`render`、`pick`、`bhit`、`dump`），且要求其後是空白或結尾；`dump-deidentified` 的 `dump` 後面是 `-`，比不到，回『場景尚未讀取完成』。初次載入（main `:10712` 呼叫 `recoverConnection`，`:557` 起）與重連的握手（main `:565`）和 `restoreSession`（main `:293`／`:303`，由 `:568` 呼叫）都在 `loading` 階段，頁面一律連不上。審查寫「初次載入（:481）」；基準 `:479-482` 是 `connectionFailed`，初次載入的實際入口是 main `:10712`，以後者為準，不影響結論 | §2.5：去身分 dump 列（指令名稱須同時在原生分派、`serve.py:463`、前端白名單三處）；使用點表新增「連線階段白名單」列與同名說明段；§4 檔案（`app.js`）；L-20（突變，r5 多了 (丙)，所以是三案都紅）；decisions K3-Q30、K3-Q35 |
| S2（含 R1） | 恢復資料改**本地剝除**：恢復時解開 `record.bytes` 的場景，依 I⟨K3-3⟩ 刪掉 `requires identity-ledger/1` 與 `identity` 行，在本地算探測指紋，與去身分 dump 的指紋比；不另存 `probeHash`、不做寫入端第二次 dump；刪掉「寫於 K3 之前」那句理由。核對：`restoreSession` 要求 `record.session===connection.session`（main `:294`），session 是每個行程的 uuid（`native_context.py`），K3 之前的紀錄永遠比不上；缺 `probeHash` 的是 K3 之後試改 Finish 寫的紀錄（main `:1572-1574` 建 `record` 與 `finishReceipt`，`scenarioTicketTransaction` 以 `recoveryKey` 與 `receiptKey` 兩個鍵寫入，`:1373`），`restoreSession` 會把它當 saved 取用（`:281-290`，`record=saved` 在 `:290`；審查記為 `:285-291`），用去身分 dump 對完整 `sceneHash` 比必不符，Finish 中斷恢復永久失效。**R1（revision 相等不保證同一快照）隨之消除**：本地剝除只用同一份 `record.bytes`，不再需要「寫入端去身分 dump 的 `revision` 等於 `exportSnapshot` 的 `nativeRevision`」 | §2.5：使用點表「恢復資料」列、「恢復資料（r5 重寫）」段、「維持完整」表；§4 檔案（`reference-workspace.js`：寫入端不改；`project-store.js`：`stripIdentityLedger`）；L-12（剝除與原生去身分 dump 逐位元一致）；L-18(m)；L-20 (甲)(乙)(丙)；§9.2-8；decisions K3-Q35；r4 表自行推出③標註撤回 |
| S3（含 R6） | 閘門寫成 `#ifdef _WIN32` 外的純判定函式（參數：宿主模式、World、tokens）；GDI `interactive_apply_line` 只呼叫它；L-23 在 Linux 測此函式（經橋接唯讀測試接縫），保留 L-07 對照與兩個突變；GDI 接線只做 read-back；測試接縫可指定宿主模式（參數或設旗標），「只由 GDI 宿主設定」限於產品路徑。核對：`#ifdef _WIN32` 在 `current_geometry.c:4151`，`#endif` 在 `:6171`；`interactive_apply_line`（`:4831`）與 `gdi_show_three_views`（`:5935`）都在其內；`apply_interactive_tokens`（`:3996`）、`split_tokens`（定義 `:6329`）在其外。CI 兩個 job 都是 `ubuntu-latest`（`.github/workflows/integration-tests.yml:17`、`:31`）；`tests/_bridge.py` 在非 Windows 以 `cc` 自動編 bridge，在 Windows 從不自動編（Smart App Control 擋新編 exe，stale／missing 就 SkipTest）。**R6**：L-23 的載入改為經 `gdi_load_scene_file`（`:4778`），`interactive_apply_line` 從不載入場景檔 | §2.2-4（K3-LIM-1 全段：旗標、純函式、測試接縫、K3-L 新增工作）；§2.5 橋接對照新增 `host-gate-check` 列與桌面段；§4 檔案（`current_geometry.c`、`web_bridge.c`）；L-23 重寫；§7；§9.2-6；§9.3；decisions K3-Q11 |
| S4 | 能力集合只加 `BRIDGE_CAPABILITIES`（`scenario_verify.py:46`），不加 `NATIVE_CAPABILITIES`；原生 `json_engineering_capabilities` 固定清單（`engineering_bridge.inc:19`）**無條件**加 `identity-ledger/1`，固定清單與 BRIDGE 一起加；`required_capabilities` 只在已啟用時加；補斷言「模型 `base_scene` 帶 `requires identity-ledger/1` 時被拒」。核對：`_capabilities` 預設 `supported=NATIVE_CAPABILITIES`（`:149`），`:576` 用它驗模型 `requiredCapabilities`，`:44-45` 註明模型輸入維持較窄契約；`:150` 以 `len(value) > len(supported)` 檢查長度；`:556-557` 的 `required - available` 要求固定清單含它（已啟用場景的 `requires identity-ledger/1` 進 `required`）；`:552`、`:556` 的 `native_required - scene_required` 使 `required_capabilities` 不可對未啟用場景多出一項 | §2.5「#46 方案」連帶段改寫；§4 檔案（`scenario_verify.py`、`engineering_bridge.inc`）；L-12（三層斷言）；L-13（唯一例外）；L-18(k)(l)；decisions K3-Q30，新增 K3-Q36；r4 表自行推出②標註更正 |
| R2 | 補寫「`/api` 送來的 `reset`／`default`／`loadfile`（`app.js:606` 的命令正規式）與 `/upload*` 成功之後，由宿主在 `bridge_lock` 內重設區段」；`recorded_api`（`serve.py:168`）兩條分支現況都直接 `ask_bridge(data["cmd"])`，無後續動作，列入 K3-L 工作。`bridge_lock` 是 `RLock`（`native_context.py`），`upload_scene` 已同時持有 `upload_lock` 與 `bridge_lock` | §2.2-4 新增「宿主何時重設區段」；§2.5 `identity-epoch` 列；§4 檔案（`serve.py`、`native_context.py`）；新 L-25；decisions「由定義推出」 |
| R3 | L-24 加一個未啟用 World 的對照組（完全相同的 put-parameter 冪等） | L-24 |
| R4 | 更正行號：`reference-workspace.js` `1413→1416`、`1451→1546`、`1772→1867`、`1824→1919`、`198-199→201-202`（main）；main 的 `:1824` 是 `fetch("/upload/prepare")`；§2.5 清單把基準與 main 行號分欄標明。我用逐行比對（difflib）重算了本檔引用到的 `app.js`、`reference-workspace.js`、`space-workspace.js` 全部行號，其餘位移見檔頭；`serve.py:290`、`:463`、`scenario-workspace.js:64-65` 未動 | 檔頭「對 `origin/main` 的核對」；§2.5 兩張表（使用點／維持完整）；§4 開頭註記；§2.2-1 的 `:1451-1453` 補 main；decisions K3-Q7、K3-Q30 |
| R5 | L-20 寫明「`app.js` main `:4457` 帳不完整時拿到 `dump.text\|\|""`，網格引用清空」是預期的降級 | L-20（新增「預期的降級」項）；§2.5 維持完整表 `app.js` 列 |
| `AXIOM-DIFF.md` | **未改動**（與 r4 逐位元相同，檔頭仍標 r4）。逐項核對：S1–S4 與 R1–R6 都落在宿主、前端、橋接與測試的實作段；A 沒有桌面唯讀、連線白名單、能力集合的字句；`I⟨K3-3⟩` 對去身分 dump 的定義（不含 `requires identity-ledger/1` 與 `identity` 行，與未啟用時逐位元相同）正是 S2 本地剝除要遵守的條文，不須改字 | — |
| r5 自行推出／補充（非裁決原文） | ① S4：`geometry-core/modeling/base.py:104-107` 的 `load_base` 有自己的 `supported` 集合（不含 `identity-ledger/1`），是模型輸入的第二道守門，所以「帶記號的 `base_scene` 被拒」這條端到端斷言單獨存在時抓不到「誤把它加進 NATIVE」的突變，L-12 必須另有常數層斷言；② S4：固定 `capabilities` 清單是未啟用狀態下**唯一**會變的橋接輸出（L-13 列為例外），本檔掃 `tests/` 與 `geometry-web/`（排除 `tests/evidence`、`tests/release-evidence` 歸檔）沒有活的斷言比對該陣列全文；`tests/test_modeling_transport.py:81` 的 8 來自 `serve.py` 的 `/model/capabilities`，是另一份清單；③ S2：本地剝除需要先解包再比對，現行 `restoreSession` 的第一次比對在解包之前（`:294` 早於 `readProjectContext`），實作須調整順序；④ S2：剝除函式必須與原生去身分 dump 逐位元一致，否則所有已啟用專案的恢復都誤判不一致，所以 L-12 加一致性斷言、L-18(m) 加突變；⑤ S3：測試接縫設計為唯讀橋接查詢 `host-gate-check`（以參數傳入宿主模式），及 GDI 接線的 read-back 清單；⑥ S3：`tests/binaries.py` 的指紋檔案集含 `current_geometry.c`，K3-L 一改它，Windows 上所有 exe（含既有 `gdi-contract`）都 stale，重編會撞 SAC，這是 L-23 不可走 Windows exe 的另一個理由；⑦ S2：L-20 加 (丙) Finish 中斷恢復案例，沿用 `tests/test_scenario_recovery_owner.js`（`:183`、`:198` 已驗 `finishReceipt` 寫入）；⑧ R2：新增 L-25 作為驗收；⑨ 新增 decisions K3-Q36 | 各處標「r5 自行推出」 |

## r4 修訂對照表

全部暫定（依 2026-10-09 授權 L）。裁決全文見 `review-round4-findings.md`。

| 項 | 裁決 | 本版修在哪 |
|---|---|---|
| 1【阻擋】 | 刪 D⟨K3-4⟩ 的「不據此拒絕」與 B8 r3 那一項；兩個反例（I39 改綁、I38 刪被引用卡）統一列為「既有核心缺陷，已登記 BACKLOG GEO-258，不在 K3 範圍、K3 不規範其行為」；L-21(a) 改用沒有被引用的卡；重寫 K3-Q33 理由 | AXIOM-DIFF 檔頭、D⟨K3-4⟩、B8、C 表 D31／I38 列；§2.2「明示刪除為何結束存在期」段與 r3 補充末項；§2.3「同一提交內明示刪除再同鍵建立」列；L-21(a)(c)(d)；L-18(g)；§7、§7.1（改名「既有核心缺陷 GEO-258」）；§8；§9.1 D31／I38 列；§9.2-7；decisions K3-Q33 |
| 2 | `changed` 以結算後（含記號）的 World 判定；延續的鍵保留原記號；補「內容不變的重宣告批次 → `history_changed:false`、修訂號不變」測試 | AXIOM-DIFF R⟨K3-1⟩；§2.1「提交」列；§2.2-2 新項；§2.5 批次確認列；§4 檔案（`engineering_bridge.inc`）；新 L-24；L-18(i)(j)；L-21(a) 補 `history_changed:true` 對照；§9.1 D12／I14 列；decisions K3-Q34 |
| 3 | 宿主模式旗標 `desktop`，由 GDI 宿主設定；唯讀閘門以旗標判定、放在 GDI `interactive_apply_line` 入口；`undo`／`redo` 豁免；L-23 改走 GDI 入口（r5 撤回：改測 `_WIN32` 外的純判定函式，見 r5 表 S3）；寫明是 K3-L 新增工作；核心（無旗標）與 L-07 不變 | §2.2-4 K3-LIM-1 全段；§2.5 桌面段；§4 檔案（`current_geometry.c`）；L-07（標「核心，無宿主旗標」）；L-23；§7；§9.2-6；decisions K3-Q11 |
| 4 | M-14、M-13(e) 標「目前走不到（建模不支援 assembly 能力）」，標記設計保留為未來規格；K3-Q32 理由改寫；與 M-09 對齊 | §2.4 末段；§6-1；M-09、M-13(e)、M-14；decisions K3-Q32 |
| 5 | 握手與恢復資料改用去身分 dump，§2.5 改列；L-20 加重連案例（r5 補：前端連線階段白名單，見 r5 表 S1） | §2.5 介面表「完整 dump」列、去身分使用點（新增握手、恢復資料兩項）、「維持完整」清單移出 `app.js:491`、`reference-workspace.js:290／300`；§4 檔案；L-12；L-20（甲、乙兩案與突變）；decisions K3-Q30、K3-Q31、K3-Q35 |
| 6 | 只有模型的 `base_scene` 去身分；方案的 `world.scene` 與 `final_scene` 維持完整；`scene-import-bridge.inc:31` 的 `final_scene` 歸「維持完整」 | §2.3「建立模型…」列；§2.5「維持完整」清單與新「#46 方案」段；§4 檔案（`scenario_verify.py` 改寫）；L-12；decisions K3-Q30 |
| 7（記錄） | `identity-epoch` 為不經 `line`、不進歷史的獨立指令；`definition-import-confirm` 列入對照表；`app.js:4272` 列入「維持完整、無害」；L-07 換成夾具 S 有的物件 | §2.5 介面表 `identity-epoch` 列與「互動輸入」列、橋接指令對照新增兩列；「維持完整」清單；§4 檔案（`web_bridge.c`、`serve.py`）；L-07；decisions「由定義推出」 |
| r4 自行推出（非裁決原文） | ① I⟨K3-3⟩ 原文「隔離求值（建模執行器、驗證程序等）一律去身分」字面包含方案驗證，與裁決 6 衝突，改為「建模執行器、規則案例等」，並補「核對完整專案或其方案快照本身的程序讀完整場景」；② `scenario_verify.py:42-46` 能力集合與 `json_engineering_capabilities` 要認得 `identity-ledger/1`，否則已啟用方案被 `SCENARIO_CAPABILITY` 拒（**r5 更正**：只加 `BRIDGE_CAPABILITIES`；固定清單無條件加、`required_capabilities` 只在已啟用時加；見 r5 表 S4）；③ 恢復資料改去身分比對時，紀錄另存同一快照的去身分指紋（`probeHash`），舊紀錄以 `sceneHash` 代用（**r5 撤回**：改本地剝除，不另存 `probeHash`；見 r5 表 S2）；比對通過後再讀完整 dump，被拒或只差記號就標未保存；④ `recoverLoad`（`reference-workspace.js:1824`）維持完整，並寫明為何正常流程不會被拒；⑤ `/api` 不轉送頁面送來的 `identity-epoch`；互動輸入的 `identity-epoch` 拒絕；⑥ L-20 重連分「定義不變」「定義已變」兩案：後者的恢復紀錄停在故障前，比對不符是正確結果；⑦ 檔頭補 main 位移對照（`app.js`、`reference-workspace.js`、`space-workspace.js`），並把 main 新增的 `reference-workspace.js:1517／1522` 歸「維持完整」；⑧ L-23 的突變與「核心對照案」；⑨ §9.2-8 新疑慮 | 各處標「r4 自行推出」 |

## r3 修訂對照表

| 項 | 裁決（全文見 `review-round3-findings.md`） | 本版修在哪 |
|---|---|---|
| F1【阻擋】 | 刪 D⟨K3-4⟩「所以 World 內不會留下指向已結束存在期的引用」。改為：同一提交明示刪除後同鍵重建時，World 內引用依 id 解析到新存在期，本層不記此改綁。列為已知限制。不採「整筆拒絕」 | AXIOM-DIFF D⟨K3-4⟩、B8；§2.2 說明段；§2.3；L-21 主案與備援句；§7、§7.1（K3-LIM-2）；§9.1 D31／I38 列；K3-Q33 |
| F2 | D⟨K3-2⟩(2) 改為「任何交易中的 delete-parameter」。刪除記錄掛在 `parameter_remove` 內。L-21 補組構與斷面路徑 | AXIOM-DIFF D⟨K3-2⟩；§2.2 說明段；§4 檔案；L-21(c)(d) |
| F3 | 明示刪除的閉集改成原則句：「提交中任何操作使該受涵蓋物件不存在，即為明示刪除」。op 名列在契約層，含 PF-0 衍生承載面的刪除 | AXIOM-DIFF D⟨K3-2⟩；§2.1；§2.2 說明段；§8；§9.2-2；K3-Q5 |
| F4 | L-21 的斷面案例做不到。明寫「現行無同提交重建承載面路徑」，保留為未來案例 | L-21(e) |
| F5 | 對照表補 `line reset`（`apply_reset_line`，`current_geometry.c:11948`，可 undo）與桌面「清除」（`:5532`），兩者都是提交。結果：身分帳仍啟用、區段保留、World 空。K3-LIM-1 改寫：桌面版（GDI，不設區段）開啟已啟用專案時以唯讀模式載入，直到桌面支援區段 | AXIOM-DIFF D⟨K3-3⟩、R⟨K3-1⟩；§2.1；§2.2-4；§2.3；§2.5 對照表；L-22、L-23；§7；K3-Q11 |
| F6 | 每個不帶記號的根都標上理由（`uncovered:"assembly-owned"`）。驗證依標記，不依目前 World | §2.4；§6-1、§6-6；M-12、M-14；K3-Q32 |
| F7 | 補去身分 dump 使用點：`space-workspace.js:435／451／454、507／511`；`model-update-app.js:58／64／153／155／191`；`model_update.py` 約 `:401` 的 `_graph`；`rule_cases/executor.py:513／528`。`serve.py:463` 的唯讀白名單加去身分 dump 指令。`reference-workspace.js:1262`（`exportSnapshot`）列為維持完整 dump | §2.5；§4 檔案；L-12、L-14；K3-Q30 |
| F8 | 寫明：明示刪除集合隨候選存在 `g_preview`，`batch_confirm` 據此結算（它直接套 `g_preview.after`，不重跑 op） | AXIOM-DIFF R⟨K3-1⟩(b)；§2.2-2；§2.5 對照表；L-18(g) |
| F9（記錄） | 行號 `engineering_bridge.inc:110`→`:121`；`model_update.py:396`→見右欄 | §2.2-1；§2.5、§6-1 改寫為「`load_base` 呼叫在 `:394`，寫進 `inputs.base_scene` 在 `:396`」（另見回報疑點） |
| F10（記錄） | §9.2-4 改為「走不到」：結算失敗時 `current_geometry.c:4079` 一定整組回滾 | §2.2-2；§9.2-4；decisions「由定義推出」末條 |
| F11（記錄） | L-16 補互動 preview／confirm（`geometry-core/transactions.inc:551-558`） | §2.2-1；L-16 |
| F12（記錄） | 由 F3 解：K2a 孤兒判定的「刪除」與本案明示刪除用同一定義 | §8 |
| 自行推出（非裁決原文） | ① L-21 的匯入案例用夾具 S 拿不回同 id（`parameter_import` 從 0 找空號，S 沒有卡 0），改為先建卡 0；② 卡片重宣告省略的欄位也屬原則句的明示刪除，列入契約清單（現行 I38 擋住同提交再用，觀察不到）；③ 桌面「匯出 .scene」（`current_geometry.c:5621-5640`）與 `app.js:1458` 同屬交換格式，改去身分；④ 依 F6 同一原則，M-12 刪「未啟用專案卻有 `sourceIdentity` → 整份拒絕」，改為合法、比對得 `unknown`；⑤ 新增突變 L-18(g) 給 F8 牙齒；⑥ `line` 列的非提交例外補 `preview …`、`cancel-preview`、`history-begin`；⑦ `(placement,id)` 明寫含 PF-0 衍生承載面 | 各處標「r3 自行推出」 |

## r2 修訂對照表

| 項 | 裁決 | 本版修在哪 |
|---|---|---|
| #1【阻擋】 | K3-Q5 整體改 B：明示刪除即結束存在期。算刪除的只有互動 `delete`、`delete-parameter`（連同欄位）、`sp` 的 `delete-placement`（承載面）。重宣告仍延續 | K3-Q5；D⟨K3-2⟩；§2.2、§2.3；L-21；§7.1（既有核心缺陷，另開工單） |
| #2 | L-18(c) 改為「略過 `batch_confirm` 路徑的結算」，對 L-21 變紅 | §4 L-18 |
| #3 | 兩種寫法擇一：寫死「啟用使未確認預覽過期」，不拒絕啟用。判定來源見 §2.2-1 | §2.2-1、§3、§5-2、§6-2、E-14、M-11、K3-Q7 |
| #4 | 補漏的去身分使用點；匯出 `.scene` 與回報內容也去身分 | §2.5、§4 檔案與 L-12／L-14、K3-Q30 |
| #5 | 組構所有角材當模型根時，該根 `incarnation:null`、判 `unknown`，不整筆拒絕 | §6-1、M-14、K3-Q32 |
| #6 | D⟨K3-4⟩ 定義「內容指紋」；`definitionFingerprint` 等實作名稱只進正式契約 | D⟨K3-4⟩、R⟨K3-2⟩、§2.4、§8、用詞表 |
| #7 | 橋接指令對照表：`reset`／`default`／`loadfile`／`load-confirm` 為整體取代；`line`／`drag`／各類 `*-confirm`（不含 `load-confirm`）為提交 | §2.5 對照表、D⟨K3-3⟩、R⟨K3-1⟩ |
| (a) | 群組內結算失敗依群組語意整組回滾 | R⟨K3-1⟩、§2.3、I8 接續 |
| (b) | 第一次新增 ledger 證據會自動啟用，既有 legacy-v1 租約失效並轉 `needs-reassociation` | §5 E-08 |
| (c) | 完整 dump／完整專案保存被拒後，只靠復原回到完整帳；去身分 dump 不拒絕 | I⟨K3-1⟩(e)、§2.5 |
| (d) | D⟨K3-4⟩ 刪「若 D⟨K2b-4⟩ 採納」，改無條件陳述 | D⟨K3-4⟩、§9.1 |
| (e) | 限制標籤改 `K3-LIM-1` | §2.2-4、§7、K3-Q11 |
| (f) | 桌面載入路徑改為 `gdi_load_scene_file`（`current_geometry.c:4778`） | §2.2-4 |
| (g) | E-03 不再改不存在的參數卡 3，改重宣告 timber 6 | §5 E-03、夾具說明 |

## r1 修訂對照表

| 項 | 審查要點 → 裁決 | 本版修在哪 |
|---|---|---|
| F1 | 歷史群組內每行都直接改正式 World（`current_geometry.c:4066-4072`），群組內也能 confirm（`geometry-core/transactions.inc:551`）→ 每一筆成功的原生變更都是提交，history-end 不是 | §2.1、§2.2、§2.3；R⟨K3-1⟩ 刪「歷史群組結束」；D⟨K3-2⟩；L-04 期望反轉；K3-Q5 範圍縮為單一指令 |
| F2 | 組構批次 delete／create-instance 在最小空號重用角材 id（`geometry-core/assembly_generation.inc:105-115`），以鍵比對會誤判延續，違反 D34（`公理層.md:497`）→ 組構生成角材排除在身分帳與證據目標外 | D⟨K3-1⟩ 涵蓋定義；§2.3；L-19；K3-48 目標限制；§7；K3-Q6、K3-Q22 |
| F3 | 漏列 `eng_definition_hash`（`geometry-web/engineering_bridge.inc:6-16`，dump 整個 World）→ 以去身分 dump 計算；連帶 `source-inspector.js:199`、`model-update-app.js:194` 的 sourceFingerprint 比對 | §2.5「去身分 dump」列；K3-L 檔案；L-12；I⟨K3-3⟩；K3-Q30 |
| F4 | 原生只有 `g_definition_revision`，`world_definitions_equal` 只略過 canvas_pos（`current_geometry.c:3808-3815`）→ 改採 Q13-B「啟用即讓預覽過期」 | §2.2、§2.5；R⟨K3-1⟩ 末句；I8a 第 587、596 行；L-16 擴及工程／參數／組構／斷面批次預覽與場景匯入；K3-Q13 |
| F5 | 至少 11 處提交點，漏結算會讓存檔重開整份被拒 → 單一結算點設在指令分派層；dump／保存遇不完整身分帳一律拒絕 | §2.2-2、§2.5；I⟨K3-1⟩(e)；L-20；K3-Q31 |
| F6 | 條號建議與 PF-0 衝突 → 全用佔位 | 檔頭、§8、AXIOM-DIFF 檔頭 |
| F7 | 與 K2b `D⟨K2b-4⟩` 身分分類互斥 → K2b 已補 (f) 類「存在期記號：不跨專案、匯入一律新配」 | D⟨K3-4⟩ 加對應句；I39 修訂改為只附加一句；§9.1 |
| F8 | E-06 照字面做不到：邊界仍有承載面時不能刪（`current_geometry.c:11609-11613`）→ 改寫 | E-06 改用游離邊界 3；K3-48 夾具 S′ |
| Q15-B | `record.input.base_scene` 保持去身分，另存各根的身分引用；模型雜湊不改、保存格式號不整批改 | §2.6；K3-44 全節；K3-Q15；連帶 K3-Q16、K3-Q21 |
| 切分 | K3-L（七種鍵、排除組構生成角材；建模只在建立模型時取去身分 dump）→ K3-48 → K3-44 | §3；§4–§6 順序 |
| 記錄項 | 測試宿主禁止重用區段；檔案複製後 projectId 相同屬共享存在期；D34 實例更新保留角材 id（`assembly_generation.inc:111`）；「內容指紋」改寫為 definitionFingerprint／valueFingerprint；桌面 GDI（`current_geometry.c:4772`）不設區段＝已啟用專案在桌面版不能新建受涵蓋物件；F1b 新紀錄 base_scene 來自 `load_base`（`model_update.py:396`）；I8a 第 596 行與 587 行一起修；原生成本 ≤480 鍵×24 B≈11.5 KB／World | §2.2-4、§2.4、§2.6、§6、§9；AXIOM-DIFF B4；R⟨K3-2⟩ 用詞 |
| 連帶（非裁決原文，由 F4 推出） | 啟用會使預覽過期，故不能在任何預覽的「確認」途中自動啟用：證據新增／重新關聯（無預覽）仍自動另一步啟用，但有未確認原生預覽時拒絕並提示；建模與 F1b 改為對話中提供明確「啟用身分追蹤」入口 | §5-2、§6-1；K3-Q7、K3-Q16 |

## 0. 一句話

在 native World 上為七種物件各掛一個存在期記號 `E:s`（E 為每次載入換新的 128 位元亂數區段，s 為行程內只增不減的序號）。每一筆提交結算一次：同鍵前後都在且該提交沒有明示刪除它，就沿用；新出現、或被明示刪除後又以同鍵出現，就取新號；消失或被明示刪除，就結束。記號隨 World 保存與復原還原，永不重用。交換用的場景文字、回報與模型快照用去身分 dump，不含記號。World 外的紀錄（圖面證據、模型紀錄的 `sourceIdentity`）存「身分鍵＋記號」，以單一規則比對出 `unknown／conflict／absent／replaced／continuous` 之一。#48 與 #44 都只讀這一份帳。

## 1. 問題與既有邊界

- 現況一律「延續性未知」：F1a 固定 `identityContinuity:'unknown'`（`geometry-web/source-inspector.js:147`）；F1b 收據固定 `identity:'unknown'`、來源每次明選（`geometry-web/docs/MODEL-UPDATE-INTEGRATION.md`）；#48 以 `contextToken＋nativeRevision＋pin` 暫態租約判斷，**任何**原生修訂或重開即 `needs-reassociation`（`geometry-guide/EVIDENCE-LINKS-INTEGRATION-48.md`；`geometry-web/evidence-links.js:78,123`）。
- 既有決策把 durable ledger 列為另一大契約：`geometry-guide/CONTINUATION-DECISIONS-20261003.md:48,90`、`geometry-guide/IMPLEMENTATION-QUEUE-20261004.md:11,13`。EvidenceLink 的 `target.incarnation` 已預留且強制 `null`（`evidence-links.js:22`）。
- 現有身分機制都服務 World 內引用：D30 vertexKey（`公理層.md:444-449`）、D19a ruleKey（`:276-279`）。World 外引用沒有身分證據，這是缺口。
- 原生復原是整份 World POD 快照（`current_geometry.c:3843` 起；`history_restore_world` 對畫布座標另有展示保留處理，`:3924` 起）；歷史群組內每行直接改正式 World（`:4066-4072`）。

## 2. 共用身分帳模型

### 2.1 名詞

| 名詞 | 定義 | 條號 |
|---|---|---|
| 受涵蓋物件／身分鍵 | `(boundary,id)`、`(placement,id)`、`(column,id)`、`(beam,id)`、`(timber,id)`、`(parameter,id)`、`(parameter-field,parameterId,fieldId)`；角材只含**不屬任何 D34 實例所有權對應**者；柱樑共用數值 id 空間但鍵含類別。`(placement,id)` 也包含 PF-0 的衍生承載面（PF-0 r2 E4：與一般承載面共用 id 空間與型別）（r3 自行推出） | D⟨K3-1⟩ |
| 存在期記號（記號） | `E:s`；只做整串相等比較 | D⟨K3-1⟩ |
| 存在期 | 一個身分鍵從「某次提交後首次受涵蓋」到「被明示刪除，或某次提交後不再受涵蓋」 | D⟨K3-2⟩ |
| 明示刪除（r3 改為原則句） | **提交中任何操作使該受涵蓋物件不存在，即為明示刪除**，不論那一步出現在哪種交易裡、提交結束時同鍵是否又出現。重宣告是就地修改，不使物件不存在，所以不算。現行會這樣做的 op 名列在契約層（§8 清單），公理不列 op 名 | D⟨K3-2⟩、K3-Q5 |
| 提交 | 成功改變既有正式 World 的一筆：見 §2.5 對照表。有沒有改變以結算後的 World（含記號）判定，延續的鍵保留原記號（r4，§2.2-2）。互動清空（`line reset`、桌面「清除」）也是提交。`history-begin`／`history-end`、群組整組還原、復原／重做、純 canvas-pos、互動 `preview`／`cancel-preview` 不是提交 | R⟨K3-1⟩ |
| 整體取代 | 換掉整個正式 World 的入口：橋接 `reset`（`web_bridge.c:912-916`，清歷史）、`default`、`loadfile`、`load-confirm`，以及開檔、恢復資料、載入方案快照。不是提交。互動清空雖然也把 World 清空，但它是互動單行、記一步歷史，屬提交，不在此列（r3，F5） | D⟨K3-3⟩ |
| 內容指紋 | 只回答內容是否相同的指紋。分定義內容指紋與有效值內容指紋。公理不寫演算法與實作欄位名 | D⟨K3-4⟩ |
| 配號區段 E | 128 位元、宿主以密碼學亂數產生；行程啟動與每次整體取代後須重設 | D⟨K3-3⟩ |
| 身分引用 | World 外紀錄保存的「身分鍵＋記號」 | D⟨K3-4⟩ |
| 去身分 dump | 不含 `requires identity-ledger/1` 與 `identity …` 行的 dump；必與未啟用時的 dump 逐位元相同 | I⟨K3-3⟩ |

### 2.2 身分如何產生

1. **啟用**：互動指令 `identity-ledger activate`，須為單獨一筆提交（不得在歷史群組或候選交易內），依固定順序為全部現存受涵蓋物件取號；可復原；不提供停用；啟用前沿革一律未知。**有未確認預覽時仍然啟用，不拒絕**；啟用使那些預覽過期（Q13-B：原生只有單一 `g_definition_revision`，`world_definitions_equal` 只略過 canvas_pos）。過期的判定來源寫死為下面四個，不另設「有沒有預覽」的總開關：
   - 原生預覽格 `g_preview`（工程、參數、組構、斷面批次，以及互動 `preview …` 共用）：批次確認在 `batch_confirm` 查修訂號與 `world_definitions_equal`（`engineering_bridge.inc:121`；r3 依 F9 由 `:110` 更正）；互動 `confirm <token>` 在 `geometry-core/transactions.inc:551-566` 查同樣兩項（STALE 判定在 `:557-559`），桌面預覽確認也走這段（`transactions.inc:128` 起的 `reference_gdi_confirm` 最後送 `confirm`）。啟用使修訂號 +1，兩條路的確認都得到 STALE（r3 依 F11 補互動路徑）。使用者離開工作區時沒取消的孤兒預覽**不阻擋**啟用；之後那一格的確認被拒，須取消或重新預覽。
   - 場景匯入準備 `g_load`：`load-confirm` 查 `g_definition_revision` 與 `g_load_revision`（`scene-import-bridge.inc:63-64`）。啟用後這次匯入確認過期。它是整體取代的準備，不是提交。
   - 建模預覽與 F1b 候選**不是**原生預覽。它們記在各自對話裡，並記住當時的修訂號與去身分 dump。啟用後再確認時由該對話重比；不符即過期、零寫入（M-11）。
   - #46 試改保全不是啟用守門。`assertScenarioFrozen` 用完整 dump 指紋與 `nativeRevision` 比對（`reference-workspace.js:1451-1453`；main `:1546-1548`）。啟用後兩者都不符，保全過期，這次試改不能完成；不因此拒絕啟用。
2. **結算**（R⟨K3-1⟩）：單一結算點設在**原生指令分派層**（web bridge 指令分派、桌面互動入口），每個提交成功改完 World 之後結算一次，不在個別變更函式內各自結算。以指令前的 World 為身分帳狀態來源（候選不帶也不決定記號）。先取得該提交裡的明示刪除集合，再比較前後受涵蓋鍵：被明示刪除→舊存在期結束，提交後同鍵仍在則另取新號；未被刪除且兩邊都有→沿用（含重宣告）；只在後→取號；只在前→結束。再驗 I⟨K3-1⟩。
   - **明示刪除集合從哪來（r3，F8）**：凡會使受涵蓋物件不存在的 op，在執行當下把鍵記進「本次執行的明示刪除集合」（`delete-parameter` 記在 `parameter_remove` 內，見 F2）。互動單行（含互動 `confirm`，它會重跑原指令，`transactions.inc:562-565`）在本行執行時記下。批次預覽在候選上依序跑 op 時記下，集合**隨候選存在 `g_preview`**；`batch_confirm` 不重跑 op，直接套 `g_preview.after`（`engineering_bridge.inc:126`），所以確認時以 `g_preview` 裡的集合結算。預覽被取消、過期或被下一個預覽取代時，集合隨之作廢。
   - **失敗**：與其他驗證失敗同一條路。不在歷史群組內，回到該指令前的 World；在歷史群組內，**一律**整組回滾（`history_group_rollback`，同 `current_geometry.c:4078-4081`），不是只回到該行之前。`:4079` 的「預覽仍有效且 token 已變時不回滾」只在該行回傳失敗、且這一行剛產生新預覽時成立；那種行是預覽，不是提交，不結算。互動 `confirm` 會先把預覽設為非 ready（`transactions.inc:564`），所以結算失敗走不到不回滾的分支（r3，F10）。已取序號都不歸還。
   - **「有沒有改變」以結算後的 World 判定（r4，第 4 輪 F2）**：`batch_confirm` 以 `changed=!world_definitions_equal(&g_world,&g_preview.after)` 決定要不要記歷史、遞增修訂號（`engineering_bridge.inc:125-126`）；`world_definitions_equal` 以 `memcmp` 比整個 World，只跳過 canvas_pos（`current_geometry.c:3811-3814`），記號存在 World 內，所以一定被比到。規定：先在候選的副本上結算（記號依 R⟨K3-1⟩(a) 取自指令前的 World），再拿**結算後**的 World 與 `g_world` 比，決定 `changed`；變更時寫回的也是結算後的那份。延續的鍵必須保留原記號。結果：內容不變的重宣告批次結算後與 `g_world` 逐位元相同，`changed=false`，`history_changed:false`、修訂號不變、不取號（L-24）；只有明示刪除後同鍵重建（即使定義逐位元相同，L-21(a)）、新增或結束受涵蓋物件，才因記號不同而 `changed=true`。反過來，`changed=false` 時一定沒有取號：新取的號必定寫進結算後的 World，使它與 `g_world` 不同。這與 R⟨K3-1⟩「只有成功的提交取號」一致（AXIOM-DIFF R⟨K3-1⟩ 已補同義句）。互動單行照舊在套用前就 `history_record`（`current_geometry.c:4070-4071`），不受本條影響；它若沒有改變任何東西，結算也不取號。
3. **取號順序**：boundary → placement → column → beam → timber → parameter → parameter-field；同類 id 遞增，欄位 `(parameterId,fieldId)` 遞增。同一提交裡「結束舊的、配新的」都算取號，新號排在沿用判斷之後，仍用這個順序。
4. **配號器**：`identity-epoch <32hex>` 由宿主設定（session 層、不進場景與歷史）；序號是**行程全域**計數器，從 1 起只增不減、換區段不重新起算；只有成功提交取號；群組整組還原時，群組內已取的序號不歸還。整體取代 World 時區段清為未設定，宿主須重設一個不在目前 World 任何記號中的新值；`loadfile`／`load-confirm` 雖可 undo，undo 只還原 World 與記號，**不**把區段還原。**測試宿主同樣禁止重用區段**（每個行程用不同值）。**K3-LIM-1（r4 再改，第 4 輪 F3；r5 再改，第 5 輪 S3）**：桌面版（GDI）首版不設區段；它開啟已啟用專案時唯讀，直到桌面支援區段。唯讀的判定**不看「區段是否設定」**：r3 那樣寫會連核心一起擋，打破 L-07「核心、已啟用、未設區段、不需取號的提交成功」。改為：
   - **宿主模式旗標**：K3-L 新增一個行程層級的宿主模式旗標，值只有「未設」與 `desktop`。**產品路徑**只有 GDI 宿主設定它：在 `gdi_show_three_views`（`current_geometry.c:5935`；`main` 於 `:13036` 呼叫）進入視窗迴圈之前設為 `desktop`。web bridge、CLI（`--no-window`）與核心測試的產品路徑都不設，它們的行為與 L-07 完全相同。旗標變數的宣告放在 `#ifdef _WIN32`（`:4151`–`:6171`）之外（r5），賦值只出現在 `_WIN32` 內的 `gdi_show_three_views`；網頁與 CLI 路徑從不讀它。旗標不進 World、不進場景、不進歷史。「只由 GDI 宿主設定」是對產品路徑的約束；測試接縫（見下）可以另行指定宿主模式（以參數傳入，或設該旗標），不受此約束（r5，第 5 輪 S3）。
   - **閘門 = `_WIN32` 外的純判定函式（r5，第 5 輪 S3；取代 r4 的「閘門直接寫在 GDI 入口」）**：r4 把閘門寫在 GDI 的 `interactive_apply_line`（`:4831`）。這個函式與 `gdi_show_three_views`（`:5935`）都在 `#ifdef _WIN32`（`:4151`–`:6171`）內；CI 只有 ubuntu（`.github/workflows/integration-tests.yml:17`、`:31`），橋接測試在 Linux／WSL 以 `cc` 現編（`tests/_bridge.py`：非 Windows 自動編；Windows 不自動編，因為 Smart App Control 擋新編未簽章 exe）。照 r4 字面測 L-23，得新編一支 Windows exe。改為：判定寫成 `_WIN32` 之外的純函式（本檔暫稱 `host_gate_rejects`），放在 `apply_interactive_tokens`（`:3996`）旁。參數＝宿主模式、`const World *`、tokens 與個數；回傳是否拒絕，並給出診斷字串。條件：宿主模式為 `desktop` 且該 World 的身分帳已啟用；成立時，除「單獨一個 `undo`／`redo` token」外一律拒絕，診斷「桌面版尚不支援身分帳，唯讀開啟」。函式不讀任何全域（宿主模式由呼叫者傳入）、不改 World、不記歷史。GDI 的 `interactive_apply_line` 在 `split_tokens`（`:4845`）與 `count<=0` 返回之後、`apply_interactive_tokens`（`:4853`）之前呼叫它，傳入行程旗標；拒絕時只設狀態列並返回，不清輸入框，也不走 `reference_gdi_confirm` 分支（與既有失敗分支一致）。`undo`、`redo` 明確豁免：功能表的復原／重做（`:5562`、`:5567`）也經這個入口。
   - **為什麼一道閘門就夠**：桌面的一切變更都經這個入口——輸入框（`:5523`）、畫布繪製（`:5027`、`:5045`）、拖曳的 `move`（`:5731`）、「清除」按鈕（`:5533` 送 `reset`）；桌面預覽確認 `reference_gdi_confirm` 只在 `:4857` 由這個入口呼叫。GDI 程式碼裡改 World 的只有這個入口與 `gdi_load_scene_file`（`:4778`，整體取代）。
   - **照常的操作**：復原／重做、載入另一份檔案或範例（`gdi_load_scene_file`，整體取代，不經此入口）、匯出（去身分，見 §2.5）。換成未啟用的 World 後恢復可寫；undo 回到已啟用的 World 又是唯讀。
   - **K3-L 的新增工作**：現行桌面沒有宿主模式，也沒有唯讀。要新增：(1) 行程層級的宿主模式旗標（宣告在 `_WIN32` 外）；(2) 純判定函式；(3) GDI 兩處接線——`gdi_show_three_views` 設旗標、`interactive_apply_line` 呼叫判定；(4) 橋接唯讀測試接縫 `host-gate-check`（下一項）。(1)(2)(4) 在 Linux 可編可測；(3) 只能在 Windows 編譯，驗收以 read-back 確認（L-23），並照實報告「GDI 接線未於 Windows 實機執行」。這是桌面宿主的限制，不改 I⟨K3-2⟩ 的核心規則。
   - **測試接縫（r5，第 5 輪 S3）**：web bridge 新增一個唯讀查詢（名稱由正式契約定，本檔暫稱 `host-gate-check <desktop|none> <一行互動指令>`）：以參數指定宿主模式，對目前 `g_world` 呼叫上面的純函式，回 `{ok:true,rejected:bool,message}`。它不執行該行、不改 World、不進歷史、不遞增修訂號、不結算（§2.5 橋接對照新列）；不設行程旗標（實作若選擇設旗標也可以，斷言相同）。網頁與 CLI 路徑從不讀旗標，所以接縫即使被 `/api` 轉送也無害；`serve.py` 不需為它加白名單，測試直接經 `tests/_bridge.py` 的 `BridgeSession` 送。
   - **宿主何時重設區段（r5，僅記錄 R2）**：除行程啟動外，下列整體取代**成功**後，宿主必須在**同一次持有 `bridge_lock` 的區間內**送 `identity-epoch <新值>`，使其他請求看不到「World 已取代、區段未設定」的中間態：(1) 頁面經 `/api` 送來的 `reset`、`default`、`loadfile`（`app.js:606` 的命令正規式列出它們；`serve.py` 的 `recorded_api`〔`:168`〕兩條分支現況都直接 `ask_bridge(data["cmd"])`，沒有任何後續動作，這是 K3-L 要補的缺口）；(2) `/upload`（`loadfile` 形式）與 `/upload/confirm`（`load-confirm`），都在 `upload_scene` 內，該函式已同時持有 `upload_lock` 與 `bridge_lock`。只在回覆 `ok:true` 時重設（失敗時 World 未被取代）；`/upload/prepare`、`/upload/cancel` 不是取代；`undo` 不重設區段。`bridge_lock` 是 `RLock`（`native_context.py`），在 `recorded_api` 外包一層持鎖流程、內部再呼叫 `ask_bridge` 不會死鎖；實作形式由 K3-L 定。頁面經 `/api` 送來的 `identity-epoch` 一律不轉送（§2.5）。驗收見 L-25。
   - r2 寫「只擋需要配號的提交」，「清除」、刪除、移動仍會通過，所以 r3 改成整份唯讀；r3 以區段當閘門，r4 改為宿主旗標；r5 把判定抽成 `_WIN32` 外的純函式，讓它能在 Linux 測試。

明示刪除為何結束存在期：工程批次在同一個候選上依序做最多 256 個 op（`engineering_bridge.inc:97-104`）。`parameter_import` 從 0 起找最小空號（`parameters.inc:314`），所以 `[delete-parameter 0, import-parameters P]` 會讓匯入卡拿回 id 0。只比前後鍵集合會把它判成 continuous，與「匯入的新卡片均為新存在期」矛盾。`[delete-parameter 9, put-parameter{id:9}]` 也會讓已刪欄位 id 被同一批再用（`parameter_put` 的 I38 檢查要看到刪除前的舊卡，`parameters.inc:257`、`:264`）。（r4：兩例都指**沒有被引用**的卡片，I38 允許刪除；刪除仍被引用的卡片是另一回事，見 §7.1。）這兩種都算明示刪除：舊存在期結束，同鍵的新物件取新號。重宣告沒有先刪，仍然沿用。歷史群組內每行仍各是一次提交（F1）。組構實例批次在最小空號重用角材 id，以 id 判定會誤判，故組構生成角材不受涵蓋（F2；D34 的分件身分本就依 instance／member，不依角材 id）。

r3 補充（F2、F3）：
- `delete-parameter` 不只出現在工程交易。組構批次的 `assembly_operation` 對不認得的 op 轉交 `eng_operation`（`geometry-core/assembly.inc:213`）；組構生成批次的 `asm_generation_operation` 再轉交 `assembly_operation`（`assembly_generation.inc:101`）；斷面批次的 `sp_operation` 也轉交 `eng_operation`（`section_profiles.inc:131`）。所以 `engineering-preview`、`assembly-preview`、`assembly-generation-preview`、`section-profile-preview` 四條路都能刪參數卡。明示刪除記錄掛在 `parameter_remove`（`parameters.inc:277`）內，任何路徑都記得到，不在各橋接指令各自補。
- 閉集改成原則句後，PF-0 r2 的衍生承載面（與一般承載面共用 `(placement,id)`，同一交易可刪可建）自動落在原則內，不必再改公理。op 名在契約層列舉（§8）。
- **r4（第 4 輪 F1【阻擋】）：r3 的 K3-LIM-2 撤回**。r3 說「I38 允許」`[delete-parameter 2, put-parameter{id:2}]`，這是錯的：I38 的例外前提是「先明確改綁／解除引用，或在同一候選內完成解除與刪除」（`公理層.md:814`），這批沒有解除，卡 2 的 field(2,0) 仍被 timber 5 引用。原生能通過，只因 `parameter_remove` 不查引用（`parameters.inc:277-284`），這是 I38 的既有實作缺陷。r3 又把「不據此拒絕」寫進 D⟨K3-4⟩，緊接在「被引用者不得被刪除（I38）」之後，SSOT 自相矛盾。r4 刪掉那句，兩個反例（同批刪卡再匯入的 I39 改綁、同批刪除被引用卡再同 id 重建）統一列為**既有核心缺陷，已登記 BACKLOG GEO-258，不在 K3 範圍，K3 不規範其行為**（§7.1）。L-21 只用沒有被引用的卡。

### 2.3 生命週期表

| 事件 | 效果 | 依據 |
|---|---|---|
| 啟用 | 全部現存受涵蓋物件依序取號；一步可復原；使 §2.2-1 的四類未確認預覽過期，不拒絕啟用 | I⟨K3-2⟩、I8a 修訂 |
| 新建（互動、群組內一行、預覽確認、加入既有 World 的匯入確認） | 該次提交取號 | R⟨K3-1⟩ |
| 重宣告、改值、改來源、改名、拖卡片、改角色／截面、R13 改掛、I17 刪空間使柱游離 | 沿用。重宣告省略掉的欄位結束，保留的 fieldId 沿用 | D⟨K3-2⟩ |
| 同一提交內明示刪除再同鍵建立 | 舊存在期結束，新物件取新號。含任何交易中的 `delete-parameter` 後 `put-parameter` 或 `import-parameters`。承載面：基準 commit 沒有同一提交刪除後再建同一承載面的路徑（L-21(e)）；PF-0 衍生承載面實作後若出現，同樣適用。被刪物件若仍被引用，刪除受 I38 等既有保護約束；原生 `parameter_remove` 未檢查引用是既有核心缺陷 GEO-258，K3 不規範（§7.1；r4 撤回 r3 的 K3-LIM-2） | D⟨K3-2⟩、D⟨K3-4⟩、K3-Q5 |
| 互動清空（`line reset`、桌面「清除」）（r3，F5） | 一次提交。全部受涵蓋物件的存在期結束；**身分帳仍啟用、區段保留、World 空**（保存時有 `requires identity-ledger/1`、沒有記號行）。之後新建的物件用同一區段取號。一次 undo 回到清空前，記號原樣 | R⟨K3-1⟩(a)、D⟨K3-3⟩ |
| 歷史群組內刪除一行、建立另一行（同鍵） | 兩次提交：舊者結束、新者取新號 | D⟨K3-2⟩、F1 |
| 分兩筆指令刪除、建立同鍵 | 同上 | D⟨K3-2⟩ |
| R8 拆分：保留原 id 的片／新片 | 沿用／取新號；不記錄衍生關係 | D⟨K3-2⟩ |
| 參數卡重宣告：保留的 fieldId／新 fieldId／卡片刪除 | 沿用／取新號／其欄位全部結束 | D⟨K3-2⟩ |
| D34 組構實例生成、更新、刪除的角材 | 不受涵蓋，無記號；角材由普通變為組構所有（或反之）視同結束（或新建） | D⟨K3-1⟩、F2 |
| 復原／重做 | 還原當時完整 World 與記號；配號器不倒退 | D⟨K3-2⟩、D⟨K3-3⟩ |
| 預覽、取消、失敗、過期 | 無變化，不取號 | R⟨K3-1⟩ |
| 群組內某一行失敗（含結算失敗） | 依群組語意整組回到群組開始前（`current_geometry.c:4078-4081`），不是只回到該行之前；結算失敗一律整組回滾（§2.2-2）；已取序號不歸還 | D⟨K3-3⟩、R⟨K3-1⟩ |
| 保存 → 重開完整專案 | 記號逐字還原；區段清除，宿主重設 | I⟨K3-3⟩ |
| 上傳場景整體取代 World | 取檔內記號（檔內未啟用則未啟用）；區段清除 | D⟨K3-3⟩ |
| 參數包匯入（I39）／K2b 定義匯入 | 新卡片、欄位、物件於匯入提交取新號；包內不帶記號 | I39 修訂、D⟨K2b-4⟩(f) |
| #46 方案分支、檔案複製 | 分支或複製當下已存在的記號是**共享存在期**；之後各自載入各設新區段，新物件不撞號 | D⟨K3-3⟩ |
| 建立模型、計算內容指紋或定義摘要、交給隔離求值 | 一律取去身分 dump；輸出不含記號。例外：#46 方案的隔離驗證核對的是方案快照本身，讀完整場景（r4，§2.5） | I⟨K3-3⟩、D25 修訂 |
| D25 交換包、參數包、其他跨專案匯出 | 不含身分帳 | D⟨K3-4⟩ |

### 2.4 失效規則：單一比對（R⟨K3-2⟩）＋內容軸

| 序 | 狀態 | 條件 | 後續 |
|---|---|---|---|
| 1 | `unknown` | 引用無記號（啟用前建立），或目前 World 未啟用 | 只能明選重新關聯 |
| 2 | `conflict` | 該記號出現在目前 World 另一個身分鍵上（資料毀損） | 不得確認／沿用；明選重新關聯 |
| 3 | `absent` | 該身分鍵目前不受涵蓋（已刪除、已變為組構所有，或因復原回到建立前） | 明選重新關聯；保留歷史 |
| 4 | `replaced` | 該身分鍵受涵蓋但記號不同 | 明選重新關聯；不得自動改指 |
| 5 | `continuous` | 記號相同 | 進入內容軸 |

內容軸另以該物件的定義內容指紋與有效值內容指紋比對，與身分軸分開呈現。公理只定義這兩個詞（D⟨K3-4⟩）。正式契約裡對應的欄位名是 source-inspect 的 `definitionFingerprint`／`valueFingerprint`（現況見 `geometry-web/source-inspector-bridge.inc:190`）。任何狀態都不以名稱、編號或內容自動改指。預覽／確認流程保存了身分引用時，確認前重比，結果改變即過期。持有者與目前 World 是否屬同一專案，由各契約以 `projectScope`／`projectId` 先判；不同即 `unknown`（契約層）。檔案複製出的兩份專案 `projectId` 相同，複製前已存在的記號屬共享存在期，比對得 `continuous` 是正確結果，不是缺陷。組構所有角材沒有記號：把它當成模型根時，該根記 `incarnation:null`，並記下不帶記號的理由 `uncovered:"assembly-owned"`（r3，F6），比對為 `unknown`，其餘根照常（K3-Q32）。理由是寫入當時就記下的事實；之後驗證只看這個標記，不回頭查目前 World 裡那支角材是否仍屬組構（所有權會變，匯入時查不出寫入當時的狀態）。**r4（第 4 輪 F4）：這個情境在基準上目前走不到**——`base_scene` 是整個 World 的 dump，World 有 `owned`／`assembly` 行就帶 `assembly-*` 能力（`geometry-core/modeling/common.py:32-35`），建模入口只支援 engineering／parameters／section-profile（`geometry-core/modeling/base.py:104-107`），F1b 也拒（`geometry-web/model_update.py:64-66`），都回 UNSUPPORTED，存不出含組構角材根的模型。標記設計保留，作為建模日後支援 assembly 能力時的規格（§6-1、M-14）。

### 2.5 原生介面

| 介面 | 內容 |
|---|---|
| `identity-epoch <32 小寫 hex>` | session 層；不進場景、不進 undo；區段已出現在目前 World 記號中→拒。**獨立橋接指令，不經 `line`**（r4，第 4 輪記錄項）：經 `line` 會在套用前 `history_record`（`current_geometry.c:4070-4071`），違反 D⟨K3-3⟩「設定區段不進復原歷史」。只由宿主（`native_context.py`／`serve.py`）送出；`/api` 不轉送頁面送來的 `identity-epoch`，否則頁面可重用區段（r4 自行推出）。宿主設定的時機（r5，R2）：行程啟動，以及 `/api` 轉來的 `reset`／`default`／`loadfile` 與 `/upload*` 整體取代**成功**之後，在同一次持有 `bridge_lock` 的區間內重設（§2.2-4「宿主何時重設區段」；`recorded_api` 現況無後續動作，是 K3-L 要補的缺口；驗收 L-25） |
| `identity-ledger activate` | 互動、單獨一筆提交、可復原；未設區段／已啟用／在群組或候選內→拒。**不**因有未確認預覽而拒。遞增 `g_definition_revision`，§2.2-1 四類預覽因此過期 |
| 場景宣告 | 檔頭 `requires identity-ledger/1`；全部定義與 canvas-pos 之後依 2.2-3 順序、id 遞增輸出 `identity <kind> <id> [<fieldId>] <E:s>`。只出現在完整專案所保存的場景，不出現在交換用匯出 |
| 載入 | 只還原不取號；缺、多、重、格式錯、無 requires 有記號行、有 requires 缺記號→整份拒絕 |
| 完整 dump／完整專案保存 | 已啟用但不符 I⟨K3-1⟩ 時拒絕輸出，診斷指出缺記號的鍵；不寫出重開會被拒的檔。恢復只有一條：復原（undo）到上一個通過 I⟨K3-1⟩ 的提交。沒有補發、沒有「刪掉記號再存」。群組內的失敗不會把不完整帳留在 World 裡（整組回滾）。L-20 的故障注入若已寫進 World，就對那一筆做復原。r4（第 4 輪 F5）：這條恢復路要求頁面在帳不完整時仍能連上服務，所以連線握手與恢復資料不得依賴完整 dump，改用去身分 dump（見下方使用點） |
| 去身分 dump | 原生提供不含身分帳的 dump，是獨立的唯讀橋接指令（名稱由正式契約定，本檔暫稱 `dump-deidentified`；不沿用 `dump` 加參數，因為現行 `dump` 不檢查參數，`web_bridge.c:1028`）。**帳不完整時仍輸出**（不套用上一列的拒絕），並在診斷註明「身分帳不完整，此輸出不能還原記號」。載入這份文字得到未啟用 World，不會因缺記號被拒。指令名稱必須同時出現在三處：原生分派、`serve.py:463` 唯讀白名單、**`app.js` 連線階段白名單**（基準 `:538-539`，main `:612-613`）。第三處是 r4 漏的：連線未就緒時 `apiRequest` 只放行九個指令（`objects`、`surfaces`、`boundary`、`references`、`obstacles`、`render`、`pick`、`bhit`、`dump`），且要求其後是空白或結尾，獨立指令 `dump-deidentified` 比不到，握手與恢復資料的探測會被擋成「場景尚未讀取完成」（r5，第 5 輪 S1；說明見使用點表下方） |
| 互動輸入 `identity …` 行 | 拒；場景檔內出現 `identity-ledger activate` 亦拒；互動輸入（`line`、桌面輸入框）的 `identity-epoch` 亦拒，它只走上面的獨立指令（r4） |
| `source-inspect` | 頂層 `identityLedger:{schema:'identity-ledger/1',active:bool}`；受涵蓋物件記錄加 `incarnation:"E:s"|null`；組構所有角材與其他型別恆 `null` |
| 指紋 | 契約欄位 `definitionFingerprint`、`valueFingerprint`、既有 `geometry-hash`、`eng_definition_hash`、`sourceFingerprint`、D25 摘要一律不含記號。公理層只稱內容指紋 |
| 成本 | 每個受涵蓋物件 24 B（16 B 區段＋8 B 序號）；上限約 480 鍵，≈11.5 KB／World 快照 |

**橋接指令對照**（`web_bridge.c` 分派；基準 commit 的行號）：

| 指令 | 身分分類 | 依據 |
|---|---|---|
| `reset`（橋接指令） | 整體取代 | `web_bridge.c:912-916`：清空 World 並 `history_clear`。不可 undo 回清空前。注意與下面的 `line reset` 不同 |
| `default` | 整體取代 | `web_bridge.c:907-911` 呼叫 `world_default`，換掉整個 World 並清歷史 |
| `loadfile` | 整體取代，可 undo | 成功時 `history_record` 後換 World（`web_bridge.c:325` 一帶） |
| `load-confirm` | 整體取代，可 undo | `scene-import-bridge.inc:65`：`history_record` 後換成 `g_load_after`。名字雖是 confirm，不是提交 |
| `line` | 提交 | 互動 DSL 的入口。例外、不是提交：`undo`、`redo`、`canvas-pos`、`history-begin`、`history-end`、`history-abort`、`preview …`、`cancel-preview`，以及該行失敗（r3 補 `history-begin`、`preview …`、`cancel-preview`，它們都不改正式 World）。`line confirm <token>` 是提交：重跑預覽時的指令（`transactions.inc:562-565`） |
| `line reset`（r3 新列，F5） | 提交，可 undo | 走 DSL 的 `apply_reset_line`（`current_geometry.c:11948`），先 `history_record`（`:4070-4071`）再清空。結果：身分帳仍啟用（R⟨K3-1⟩(a)：身分帳狀態取自指令前的 World）、區段保留（不是整體取代，不清區段）、World 空，全部受涵蓋物件的存在期結束 |
| `drag` | 提交 | 喂入一筆改變 World 的 move |
| `engineering-confirm`、`assembly-confirm`、`section-profile-confirm` | 提交 | 都進 `batch_confirm`（斷面確認見 `section_profile_bridge.inc:109`）。一筆確認是一次提交，批內 op 不是各自一次提交。`batch_confirm` 不重跑 op，直接套 `g_preview.after`（`engineering_bridge.inc:126`），所以明示刪除集合必須在預覽時記下、隨候選存在 `g_preview`，確認時據此結算（r3，F8）。`changed`（`:125`）以**結算後**的 World 判定，延續的鍵保留原記號；內容不變的重宣告批次回 `history_changed:false`、修訂號不變（r4，第 4 輪 F2；§2.2-2、L-24） |
| `definition-import-confirm <token>`（K2b r4.1 新增；基準尚無，以 K2b `PROPOSAL.md` §2.3 為準）（r4 新列） | 提交 | R⟨K3-1⟩ 的「加入既有 World 的匯入確認」。匯入的參數卡與欄位於這筆提交取新號（I39 附加句、D⟨K2b-4⟩(f)）。預覽輸入的 `sourceScene` 若是已啟用專案的完整場景，其中的記號一律不進目標（D⟨K3-4⟩：跨專案匯入不攜帶記號）。若確認直接採用預覽候選而不重跑，`changed` 判定與明示刪除集合比照上一列（F8、r4-F2） |
| `identity-epoch <32hex>`（r4 新列，第 4 輪記錄項） | 不結算 | session 層獨立指令，不經 `line`、不呼叫 `history_record`（經 `line` 會在 `current_geometry.c:4070-4071` 記入歷史，違反 D⟨K3-3⟩「不進復原歷史」）。不改定義、不遞增修訂號 |
| `host-gate-check <desktop\|none> <一行互動指令>`（r5 新列，第 5 輪 S3；暫稱，測試接縫） | 不結算 | 唯讀查詢：以參數指定宿主模式，對目前 `g_world` 呼叫 `_WIN32` 外的純判定函式（§2.2-4），回 `{ok:true,rejected:bool,message}`。不執行該行、不改 World、不進歷史、不遞增修訂號。不設行程旗標；網頁與 CLI 路徑從不讀旗標，所以被 `/api` 轉送也無害，`serve.py` 不為它加白名單。只供 L-23 使用 |
| `load-prepare`、各類 `*-preview`、`*-cancel`、`render`、`dump`、去身分 dump、`pick`、各種 read／query | 不結算 | 不改正式 World，或只準備候選 |

桌面版沒有這張橋接表。改變 World 的桌面入口走 `interactive_apply_line`，與 `line` 同一套提交／復原區分；「清除」按鈕（`current_geometry.c:5532-5533`）就是 `interactive_apply_line(app, window, "reset")`，等同 `line reset`，是提交（r3，F5）。桌面預覽確認 `reference_gdi_confirm` 最後送互動 `confirm`，與 `line confirm` 同。載入走 `gdi_load_scene_file`（`:4778`），與 `loadfile` 一樣是可 undo 的整體取代。桌面「匯出 .scene…」（`IDM_EXPORT_SCENE`，`:5621-5640` 以 `world_dump_dsl` 寫檔）與 `app.js:1458`（main `:1605`）同屬交換格式，改用去身分 dump（r3 自行推出）。已啟用專案在桌面的唯讀模式見 K3-LIM-1（§2.2-4）：以宿主模式旗標 `desktop` 判定；判定本身是 `#ifdef _WIN32` 外的純函式，`interactive_apply_line` 入口只呼叫它（r5，第 5 輪 S3），`undo`／`redo` 豁免；桌面實際載入場景走 `gdi_load_scene_file`，不經 `interactive_apply_line`（r5，R6）；桌面沒有 `identity-epoch`。

**去身分 dump 的使用點**（要改成去身分；比對的兩邊都改，避免完整 dump 與去身分快照永遠不相等）。**行號分欄（r5，R4）**：「基準」欄是 `a7bff8f` 的行號，「main」欄是 `origin/main`（`c254e1f`）的行號，兩者不混寫；「同」表示該檔在這幾行於基準與 main 之間沒有位移。實作時以 main 為準，再掃一次。

| 使用點 | 基準行號 | main 行號 | 改法與備註 |
|---|---|---|---|
| 建模 `base_scene`、F1b 新紀錄的 `base_scene`、定義摘要、隔離求值輸入 | `model_update.py:394`（`load_base` 讀 `current_scene`）、`:396`（寫進 `inputs.base_scene`；r3 依 F9 更正行號）；`engineering_bridge.inc:6-16`（`eng_definition_hash`）；`source-inspector-bridge.inc`（`sourceFingerprint`） | 同 | 一律去身分 |
| 斷面建模 | `section-profile-workspace.js:98`（`buildModel` 把 dump 放進 `definitions.base_scene` 送 `/model`）、`:100`（匯出前比對 `dump.text!==pin.scene`）；`section_profile_transport.py:24`（`load_base` 讀它；結果寫進 `.model.json`） | 同 | `:98` 送去身分 dump；`:100` 的比對必須改比去身分 dump |
| 空間建模：擷取來源（「使用目前面」） | `space-workspace.js:435`（讀 dump）、`:451`、`:454`（重讀並比對） | `:445`、`:461`、`:464` | 擷取與比對兩邊都要去身分，否則 `base_scene` 帶記號，或去身分快照永遠比不上完整 dump |
| 空間建模：更新來源 | `space-workspace.js:507`（讀 `nextDump`）、`:511`（寫成 `source.base_scene`） | `:517`、`:521` | r3，F7 補 |
| 空間建模：要跟著改的比對 | `space-workspace.js:492、495、604、610、641` | `:502、505、619、625、656` | 同上 |
| F1b 前端 | `model-update-app.js:58`（`sourcePin` 的 `scene`，就是送給 `model_update.py` 的 `current_scene`）、`:64`、`:153`、`:155`、`:191`（各次讀 dump 與重讀比對） | 同 | r3，F7 補 |
| F1b 後端 | `model_update.py` 約 `:401-402` 的 `_graph`（`:181` 起） | 同 | 把舊 `base_scene` 與 `current_scene` 寫成暫存場景，交給子行程 `source-inspect-file`。兩邊都必須是去身分 dump，子行程載入的是未啟用 World；`sourceIdentity` 不從這裡取，取自目前 live World 的 `source-inspect`（§6-1）（r3，F7 補） |
| 規則案例隔離執行 | `geometry-core/rule_cases/executor.py:513`（`before_dump`）、`:528`（`after_dump`） | 同 | 雜湊寫進收據，改用去身分 dump。該私有 World 由 `reset` 開始，現況不會啟用，但收據的領域要與其他隔離求值一致（r3，F7 補） |
| 匯出 | `app.js:1458`（`api("dump")` 寫成 `canvas_export.scene`）；`current_geometry.c:5621-5640`（桌面「匯出 .scene…」） | `app.js:1605`；`current_geometry.c` 同 | 交換格式，去身分（桌面部分 r3 自行推出） |
| 回報 | `feedback.js:212` | 同 | 放進回報的 `world`，去身分。用回報重現時載入的是沒有記號的場景 |
| 服務過期時的唯讀白名單（服務端） | `serve.py:463` | 同 | 現列 `dump` 等唯讀指令，加入去身分 dump 指令，讓過期服務仍能匯出、回報、建模比對與握手（r3，F7；r4 加握手） |
| **連線階段白名單（頁面端；r5 新增，第 5 輪 S1）** | `app.js:538-539`（`apiRequest`） | `app.js:612-613` | 加入去身分 dump 指令；說明見下方 |
| 連線握手 | `app.js:491-492`（`connectionFailed` 在 `:479-482`） | `:565-566`（`connectionFailed` 在 `:553-556`） | r4，第 4 輪 F5；改送去身分 dump，並依上一列列入白名單（r5） |
| 恢復資料：讀取與核對（`restoreSession`） | `reference-workspace.js:290`（第一次 dump）、`:291`（比對）、`:300`（驗證 dump）、`:301`（比對） | `:293`、`:294`、`:303`、`:304` | r5 重寫為本地剝除，說明見下方 |
| 恢復資料：寫入與打包核對（**不改**） | `reference-workspace.js:198-199`（`exportSnapshot` 與 `sceneHash`）、`:201`（`finishReceipt`）、`:297`（打包內容核對 `sceneFingerprint(loaded.scene)!==record.sceneHash`） | `:201-202`、`:204`、`:300` | 寫入端不改、不另存 `probeHash`。試改 Finish 的寫入在 main `:1572-1574`，也不改 |
| `recoverLoad`（**不改**） | `reference-workspace.js:1824`（`pendingLoad` 判斷在 `:1813`） | `:1919`（`:1908`） | 說明見下方。注意 main 的 `:1824` 是 `fetch("/upload/prepare")`，不是它（r5，R4） |

**連線階段白名單（r5，第 5 輪 S1）**：`apiRequest`（`app.js`，基準 `:538-539`，main `:612-613`）在 `connection.phase==="loading"` 時，只放行指令開頭是 `objects`、`surfaces`、`boundary`、`references`、`obstacles`、`render`、`pick`、`bhit`、`dump` 九者之一、且其後為空白或結尾的指令（正規式 `^(objects|surfaces|boundary|references|obstacles|render|pick|bhit|dump)(\s|$)`）；不在名單的指令直接回 `{ok:false,transport:true,error:'場景尚未讀取完成'}`。`dump-deidentified`（暫名）是獨立指令，`dump` 後面接的是 `-`，不符 `(\s|$)`，比不到。握手（main `:565`）與 `restoreSession` 的兩次探測（main `:293`、`:303`，由 `recoverConnection` 的 `:568` 呼叫）都發生在 `phase` 為 `loading` 的 `recoverConnection`（main `:557`；初次載入由 main `:10712` 呼叫它，按「重試」也走它）裡，所以 r4 的設計會讓頁面一律連不上，不只是帳不完整時。修法：把該指令加進這條白名單（正規式多一個選項，或寫成 `dump(-deidentified)?`）。指令名稱要同時出現在三處——原生分派、`serve.py:463` 唯讀白名單、這條前端白名單——正式契約改名時三處一起改；L-20 的突變鎖住前端這一處。

**連線握手（r4，第 4 輪 F5；r5 補白名單）**：`app.js:491-492`（main `:565-566`）在還沒有服務工作階段時送 `api('dump')`，失敗即 `connectionFailed`（基準 `:479-482`，main `:553-556`）。它只為取得工作階段標頭，不用回傳文字。帳不完整時完整 dump 被拒（I⟨K3-1⟩(e)），頁面每次重連都停在錯誤，使用者連不上服務，也就做不了唯一的恢復動作（復原）。改送去身分 dump：它不因帳不完整被拒，也在 `serve.py:463` 白名單內，**並須列入上面的前端連線階段白名單**（r5）。

**恢復資料（r5 重寫，第 5 輪 S2；取代 r4 的 `probeHash`）**：`restoreSession`（基準 `reference-workspace.js:290`／`:300`，main `:293`／`:303`）以 `record.sceneHash` 核對服務目前的場景。`sceneHash` 取自完整場景（寫入端基準 `:198-199`，main `:201-202`；試改 Finish 的 main `:1572-1574`），而去身分 dump 不含記號，直接比必不符。r5 的做法是**本地剝除**：恢復時先解開 `record.bytes` 取出場景（並確認 `sceneFingerprint(場景)===record.sceneHash`，即 main `:300` 既有的打包內容核對；現行第一次比對在解包之前，實作要把解包與這項核對提前到第一次比對之前），依 I⟨K3-3⟩ 刪掉 `requires identity-ledger/1` 與全部 `identity …` 行（前端純函式 `stripIdentityLedger`，放在 `project-store.js` 的場景文字解析器旁；它必須與原生去身分 dump 逐位元一致，L-12 鎖住），再算 `sceneFingerprint` 得到**探測指紋**；main `:294` 與 `:304` 的兩次比對都改成「去身分 dump 的指紋」對「探測指紋」。不另存 `probeHash`、寫入端不改、不需要寫入端的第二次 dump。

為什麼 r4 的「另存 `probeHash`，舊紀錄以 `sceneHash` 代用」不成立：(1) `restoreSession` 要求 `record.session===connection.session`（main `:294`），session 是每個行程的 uuid（`native_context.py`），K3 之前寫的紀錄永遠比不上現在的 session，不存在「舊紀錄代用」的情形，「寫於 K3 之前」這個理由要刪；(2) 真正沒有 `probeHash` 的，是 K3 之後試改 Finish 寫的紀錄：main `:1572-1574` 建 `record` 並設 `finishReceipt`，`scenarioTicketTransaction` 以 `recoveryKey` 與 `receiptKey` 兩個鍵寫入（`:1373`）；`restoreSession` 會把它當 saved 取用（`:281-290`，`record=saved` 在 `:290`），已啟用專案的這份紀錄用去身分 dump 對完整 `sceneHash` 必不符，Finish 中斷後恢復永久失效。本地剝除不依賴紀錄有沒有額外欄位，兩條寫入路徑都適用。此法同時消除第 5 輪 R1：r4 要求寫入端去身分 dump 的 `revision` 等於 `exportSnapshot` 的 `nativeRevision`（main `:1273`），但 revision 相等並不保證兩次讀到同一個快照；本地剝除只用同一份 `record.bytes`，沒有這個問題。

去身分比對看不出「只有記號不同」，所以比對通過後仍再讀一次完整 dump（這是恢復時的讀取，不是寫入端的第二次 dump）：若它被拒（帳不完整），或其指紋不等於 `record.sceneHash`（只差記號），照樣恢復附件與草稿，但把專案標為未保存並說明原因（帳不完整時附「須先復原上一步才能保存」），不沿用紀錄裡的「已保存」（r4 自行推出，r5 保留）。

**`recoverLoad`**（基準 `reference-workspace.js:1824`，main `:1919`；main 的 `:1824` 是 `fetch("/upload/prepare")`）不改：它只在有未決的場景載入時讀 dump（基準 `:1813`，main `:1908`）。那時 World 若仍是載入前的狀態，當時 `uploadScene` 在基準 `:1772`（main `:1867`）讀完整 dump 已成功，帳是完整的；若已換成新場景，新場景通過了 I⟨K3-1⟩ 載入檢查。所以除非期間另有客戶端提交，它不會被拒；它要與 `serve.py:290` 的完整雜湊比，必須是完整 dump（r4 自行推出）。

**維持完整 dump**（含記號；用來核對目前專案本身，不是交換）。行號分欄同上（基準／main 不混寫）：

| 使用點 | 基準行號 | main 行號 | 備註 |
|---|---|---|---|
| `reference-workspace.js` `exportSnapshot`（完整專案打包） | `:1262`（函式起於 `:1256`） | `:1265`（`:1259`） | r3 依 F7 補列 |
| 試改完成收據核對（`verifyScenarioEditorRetirement`：解包後讀 dump 比 `pin.sceneHash`） | `:1413` | `:1416` | 完整領域；帳不完整時失敗，但 B 與完整保存收據仍保留 |
| 試改保全 `assertScenarioFrozen` | `:1451` | `:1546` | 見 §2.2-1 末項 |
| 場景載入準備的 `before` 快照（`uploadScene`） | `:1772` | `:1867` | |
| `recoverLoad` | `:1824` | `:1919` | 見上 |
| 試改續接核對（`journal.sceneHash`） | 基準尚無 | `:1517`、`:1522` | main 新增；要與打包場景的 `journal.sceneHash` 同領域；帳不完整時續接失敗但保留資料，不卡連線 |
| `serve.py` 上傳確認後的場景雜湊 | `:290` | 同 | |
| `scene-import-bridge.inc`：`load-prepare` 回執的 `final_scene` | `:31` | 同 | 候選 World 自身的序列化，該 World 已通過載入檢查（r4，第 4 輪 F6） |
| `app.js` 面編輯器的網格引用 | `:4272`（正規式在 `:4277`） | `:4457`（`:4462`） | 只用 `^place` 正規式讀 dump，記號行以 `identity` 開頭，比不到，無害（r4 記錄項）。**帳不完整時完整 dump 被拒，`dump.text\|\|""` 得到空字串，網格引用（`gridRefs`）清空，這是預期的降級**，不是缺陷（r5，R5；L-20） |
| #46 方案的 `world.scene` 與隔離驗證的 `final_scene` | `project-store.js:640`、`scenario_verify.py:521-522`、`scenario-integration.js:25、26、30`、`scenario-workspace.js:64-65` | 同 | 見下段 |

完整專案 `.gcanvas` 保存亦用完整 dump。r4 移出本清單：`app.js:491`（握手；main `:565`）、`reference-workspace.js:290`、`:300`（恢復資料；main `:293`、`:303`），理由見上。

**#46 方案（r4，第 4 輪 F6）**：**只有模型的 `base_scene` 去身分；方案的 `world.scene` 與 `final_scene` 維持完整 dump。** 方案快照是完整專案（經 `exportSnapshot`），`project-store.js:640` 以完整場景算 `manifest.sceneHash`；`scenario_verify.py:521-522` 要求輸入場景的 sha256 等於它；`scenario-integration.js:25` 要求隔離回執的 `scene_sha256` 等於它，`:26` 以它為鍵存 `final_scene`，`:30` 以它取回。若改成去身分，已啟用專案的方案驗證永遠不符。隔離驗證只做 `load-prepare` 與 `source-inspect-file`（`scenario_verify.py:540`），不提交，不需要區段。連帶（r4 自行推出）：
- **能力宣告怎麼加（r5 更正 r4，第 5 輪 S4）**：`identity-ledger/1` **只加進 `BRIDGE_CAPABILITIES`（`scenario_verify.py:46`）**，**不加** `NATIVE_CAPABILITIES`（`:42-43`）。理由：`_capabilities` 的預設 `supported=NATIVE_CAPABILITIES`（`:149`）正是 `:576` 驗模型 `requiredCapabilities` 的那一條，`:44-45` 註明「Model producer input retains its own narrower capability contract」；加進 NATIVE 會放寬模型輸入守門，讓帶記號的模型 `base_scene` 通過，違背 Q15-B（`base_scene` 一律去身分）。`_capabilities` 在 `:150` 以 `len(value) > len(supported)` 檢查清單長度，所以原生回覆的 `capabilities` 固定清單與 `BRIDGE_CAPABILITIES` 要**一起**加（6→7 項），否則 `:551` 的 `available` 驗證失敗。原生端：`json_engineering_capabilities`（`engineering_bridge.inc:17-27`）的固定 `capabilities` 清單（`:19`）**無條件**加 `identity-ledger/1`——已啟用場景的 `requires identity-ledger/1` 進 `required`，`:556-557` 的 `required - available` 必須為空，所以固定清單不能只在已啟用時列；`required_capabilities` 則**只在 World 已啟用時**列它（`:552`、`:556` 的 `native_required - scene_required` 才不會對未啟用場景多出一項），其餘各項的逗號判斷（`:20-25`）要把新項納入。r4 寫「`json_engineering_capabilities` 在已啟用 World 也回報它」只對了一半。驗證內的模型重算吃模型紀錄的 `base_scene`（已去身分），不受影響。`geometry-core/modeling/base.py:104-107` 的 `load_base` 另有自己的 `supported` 集合（不含 `identity-ledger/1`），是模型輸入的第二道守門（r5 自行推出；這就是 L-12 要有常數層斷言的原因）。固定清單多一項是未啟用狀態下**唯一**會變的橋接輸出（L-13 例外）。
- `scenario-workspace.js:64-65` 把 `final_scene` 原文顯示為「完整原生最終定義」。裡面的記號行屬本專案資料，不是交換，照顯示。
- AXIOM-DIFF I⟨K3-3⟩ 原寫「交給幾何的隔離求值（建模執行器、驗證程序等）一律使用去身分 dump」，字面上包含方案驗證，與本段衝突；r4 改為「建模執行器、規則案例等」，並補一句「核對完整專案或其方案快照本身的程序讀完整場景」。

### 2.6 保存與能力

- 新能力 `identity-ledger/1`（I32）。已啟用專案需要新的 `geometry-canvas/N`，由共用 owner 依 main 分配（提案時 main 最大為 `/16`，`geometry-web/project-store.js:12`；不預占）。未啟用專案的格式選擇不變。
- **模型（Q15-B）**：`record.input.base_scene` 一律為去身分 dump，`source.scene_hash`、`result.source_sha256` 的領域與數值都不變；另存可選欄位 `sourceIdentity`（只在建立或更新時身分帳已啟用才出現，見 §6），所以既有模型與未啟用專案的格式號不整批改。

## 3. PR 切分與相依

```
K3-L 身分帳基礎（七種鍵、排除組構生成角材；去身分 dump；宿主區段；保存與能力）
  └── K3-48 #48 首版（邊界／角材證據、耐久關聯、參數欄位採用值；引入「自動另一步啟用」輔助）
        └── K3-44 #44 首版（模型 sourceIdentity＝Q15-B、延續證明的受控更新、faces 多載體）
```

依序合併。K3-48 引入「未啟用時自動另一步啟用」，K3-44 的明確按鈕沿用同一步驟。兩邊都不因有未確認預覽而拒絕；啟用使 §2.2-1 的預覽過期。K3-L 不新增任何會自動啟用的產品入口。

## 4. K3-L 身分帳基礎 PR

**範圍**：§2 全部；讓已啟用專案走完所有既有流程不壞；不新增產品入口。

**受影響檔案**（行號以基準為準；`app.js`、`reference-workspace.js`、`space-workspace.js` 的 main 行號見 §2.5 兩張表，不在此混寫）：`current_geometry.c`（受涵蓋型別加記號欄位、行程配號器、`identity-epoch`／`identity-ledger activate`、指令分派層單一結算點、明示刪除集合、載入完整性、完整 dump 的完整性拒絕、去身分 dump、組構所有角材排除；r3 加：互動 `reset` 依 R⟨K3-1⟩(a) 保留啟用狀態、桌面匯出改去身分；r4 加：宿主模式旗標 `desktop`（`gdi_show_three_views` 設定）、互動輸入的 `identity-epoch` 拒絕；**r5 改**（第 5 輪 S3，K3-LIM-1）：唯讀閘門寫成 `#ifdef _WIN32`（`:4151`–`:6171`）之外的純判定函式 `host_gate_rejects`（放在 `apply_interactive_tokens`〔`:3996`〕旁；旗標變數宣告也在 `_WIN32` 外，賦值只在 `gdi_show_three_views`），GDI 的 `interactive_apply_line` 入口只呼叫它（`undo`／`redo` 豁免）；取消 r4「讓 L-23 不開視窗也能呼叫 GDI 入口的測試接縫」，改由 `web_bridge.c` 的唯讀測試接縫 `host-gate-check` 測純函式）；`geometry-core/parameters.inc`（`parameter_remove` 內記明示刪除；`parameter_put` 重宣告時省略的欄位同記，r3）；`geometry-core/section_profiles.inc`（`delete-placement` 記明示刪除，r3）；`geometry-core/transactions.inc` 與 `geometry-web/engineering_bridge.inc`（`g_preview` 帶明示刪除集合，`batch_preview` 寫入、`batch_confirm` 讀出結算，r3，F8）；`geometry-web/web_bridge.c`（依 §2.5 對照表在提交後結算、在整體取代後清區段、去身分 dump 指令；`identity-epoch` 為獨立指令、不經 `line`，r4；r5：唯讀測試接縫 `host-gate-check`，S3）；`geometry-core/rule_cases/executor.py`（`:513`、`:528` 改去身分 dump，r3）；`geometry-web/model-update-app.js`（`:58／64／153／155／191` 改去身分 dump，r3）；`geometry-web/source-inspector-bridge.inc`（`incarnation`、`identityLedger`、`sourceFingerprint` 改用去身分 dump）；`geometry-web/engineering_bridge.inc`（`eng_definition_hash` 改用去身分 dump；`batch_confirm` 是結算點之一，`:125` 的 `changed` 改以結算後 World 判定，r4；`json_engineering_capabilities` 的固定 `capabilities` 清單〔`:19`〕**無條件**加 `identity-ledger/1`、`required_capabilities` 只在 World 已啟用時加，且逗號判斷納入新項；r4 寫成「在已啟用 World 回報」，r5 更正，S4）；`geometry-web/native_context.py`、`geometry-web/serve.py`（行程啟動與每次整體取代**成功**後，在 `bridge_lock` 內以 `secrets.token_hex(16)` 設區段——含 `/api` 轉來的 `reset`／`default`／`loadfile`（`recorded_api` 現況直接 `ask_bridge`，無後續動作，要補，r5，R2）與 `/upload*`（`upload_scene`）；`serve.py:290` 的上傳雜湊仍用完整 dump；`:463` 唯讀白名單加去身分 dump 指令，r3；`/api` 不轉送頁面送來的 `identity-epoch`，r4）；`geometry-web/project-store.js`（能力、新格式號、前端場景文字解析器認得身分帳行；共用 owner；r5 加 `stripIdentityLedger`〔剝除 `requires identity-ledger/1` 與 `identity` 行的純函式，供 `restoreSession` 本地剝除，S2〕）；`geometry-web/space-workspace.js`（擷取 `:435、451、454`、更新 `:507、511` 與比對 `:492、495、604、610、641` 都改去身分 dump；r3 補前五處）、`geometry-web/section-profile-workspace.js`（`:98` 送給 `/model` 的 `base_scene`、`:100` 的匯出前比對）、`geometry-web/section_profile_transport.py`（`:24` 讀到的 `base_scene` 是去身分 dump）、`geometry-web/model_update.py`（`load_base` 讀到的 `current_scene` 與 `_graph` 的兩個輸入都是去身分 dump）、`geometry-web/app.js`：`:1458` 匯出（main `:1605`）、`:491-492` 握手（r4；main `:565-566`）、**連線階段白名單**加去身分 dump 指令（`:538-539`；main `:612-613`；r5，S1）、`geometry-web/feedback.js:212` 回報；`#49` 規則案例的隔離輸入；`geometry-web/scenario_verify.py`（方案輸入維持完整 dump，只在 `BRIDGE_CAPABILITIES`〔`:46`〕加 `identity-ledger/1`，**不加** `NATIVE_CAPABILITIES`〔`:42-43`，模型輸入守門，`:44-45`、`:149`、`:576`〕，r5 更正 r4 的泛稱，S4；r3 寫成「隔離輸入去身分」，與 `:521-522` 衝突）；新測試 `tests/test_identity_ledger.py` 與 store 測試增量。不改任何 golden。`reference-workspace.js`（r5 改，S2）：`restoreSession`（基準 `:290`／`:300`，main `:293`／`:303`）改讀去身分 dump，並以本地剝除得到的探測指紋核對（解開 `record.bytes` 的場景、刪 `requires identity-ledger/1` 與 `identity` 行後算 `sceneFingerprint`；解包與打包內容核對提前到第一次比對之前）；**寫入端（基準 `:198-199`，main `:201-202`；試改 Finish 的 main `:1572-1574`）不改**，不另存 `probeHash`；§2.5 列為維持完整 dump 的行（含 `exportSnapshot`）不改成去身分。

**驗收**——夾具 S：boundary 1（4000×3000）、placement 0 引用之、column 2、timber 5／6（27×33，主支）、參數卡 2（欄位 0＝3200 mm、欄位 1＝`=f0/2`）；E1＝`0123456789abcdef0123456789abcdef`，新行程。各案自 L-01 狀態獨立起算。

- **L-01 啟用與決定性**：設 E1、啟用 → boundary 1＝`E1:1`、placement 0＝`E1:2`、column 2＝`E1:3`、timber 5＝`E1:4`、timber 6＝`E1:5`、parameter 2＝`E1:6`、field(2,0)＝`E1:7`、field(2,1)＝`E1:8`；dump 含 requires 與 8 行記號且位在 canvas-pos 之後；新行程重放後 dump 逐位元相同。
- **L-02 延續**：重宣告 timber 5（B=40）→ 仍 `E1:4`、定義內容指紋變（契約欄位 `definitionFingerprint`）；改 field(2,0)=3235 → field(2,1) 記號不變、有效值內容指紋變（契約欄位 `valueFingerprint`）。
- **L-03 分次刪除重建**：刪 timber 6、再以相同定義建 timber 6 → `E1:9`；去身分 dump 與 L-01 逐位元相同。
- **L-04 群組內刪除重建（r1 反轉，r2 補序號順序）**：`history-begin`／刪 timber 6／建 timber 6／`history-end` → timber 6 為 `E1:9`（兩次提交）；整組一次 undo 回到 `E1:5`。另：同一群組先建 timber 9、再建 timber 7 → timber 9 的序號小於 timber 7（按行的先後，不在群組結束時按 id 重排）；整組一次 undo 後兩者都不在，這兩個序號不歸還。
- **L-05 復原**：刪 timber 5 後 undo → `E1:4` 回來；redo → 消失。
- **L-06 捨棄分支不重用**：建 timber 7（`E1:9`）→ undo → 建 timber 7 → `E1:10`。
- **L-07 重開**（核心，無宿主旗標；桌面見 L-23）：保存後新行程載入 → 記號逐字還原；未設區段建 timber 8 → 拒（World 不變）；重宣告 timber 5（B=40，不需取號）→ 成功、仍 `E1:4`（r4：r3 寫「改 guide 位置」，夾具 S 沒有 guide）；設 E2 後建 timber 8 → `E2:1`；設 E1 → 拒。
- **L-08 載入拒絕矩陣**（皆整份拒絕、World 不變）：缺一行；多一行指向不存在的 timber 9；同記號兩物件；大寫 hex；序號 0；前導零；有記號無 requires；有 requires 缺記號；場景檔含 `identity-ledger activate`；互動輸入 `identity timber 5 E1:99`。
- **L-09 啟用守門**：未設區段／重複啟用／群組內啟用 → 拒；啟用後 undo → 回到未啟用（dump 無身分帳）。
- **L-10 參數包**：匯出不含記號；匯入卡片取新號；原卡記號不變。
- **L-11 R8 拆分**：保留原 id 的片沿用、新片依序取號；R13 改掛的角材記號不變。
- **L-12 指紋與雜湊獨立（r2 再擴）**：同一 World 啟用前後，定義內容指紋、有效值內容指紋、`geometry-hash`、`eng_definition_hash`、source-inspect `sourceFingerprint`、D25 摘要逐位元相同；去身分 dump＝未啟用 dump；`source-inspector.js:199` 與 `model-update-app.js:194` 的 live／snapshot 比對在已啟用專案仍判一致。`app.js` 匯出（main `:1605`，基準 `:1458`）的 `.scene` 與 `feedback.js:212` 的 `world` 都不含身分帳行。`reference-workspace.js` main `:1546`（基準 `:1451`）與 `serve.py:290` 讀到的仍是完整 dump；`app.js` 握手（main `:565`，基準 `:491`）與 `reference-workspace.js` 恢復資料（main `:293`、`:303`，基準 `:290`、`:300`）讀的是去身分 dump（r4 改，r5 行號分欄）。r4 再擴（F6）：已啟用專案建立 #46 方案 → 方案的 `world.scene` 含 `requires identity-ledger/1` 與記號行，`scenario_verify.py` 回執的 `scene_sha256` 等於 `manifest.sceneHash`、驗證通過，`final_scene` 含記號；方案內模型紀錄的 `base_scene` 不含記號。r3 再擴（F7）：`model-update-app.js` 的 `sourcePin.scene`（`:58`）與送到 `model_update.py` 的 `current_scene` 不含身分帳行，`_graph` 兩個輸入亦然；`rule_cases/executor.py` 收據的 `beforeDumpHash`／`afterDumpHash` 等於去身分 dump 的雜湊；服務過期（`RUNTIME.fresh()` 為假）時去身分 dump 指令仍放行（`serve.py:463`），寫入類指令仍 409；`reference-workspace.js` 的 `exportSnapshot`（main `:1265`，基準 `:1262`）打包的是完整 dump（含記號）。 **r5 再擴（第 5 輪 S2）**：前端 `stripIdentityLedger` 對三種已啟用 World 的完整 dump——夾具 S 啟用後、空的已啟用 World（只有 `requires`、沒有記號行；L-22）、同時帶其他 `requires` 行的已啟用 World——輸出與 `dump-deidentified` 回傳文字逐位元相同，也等於同一 World 未啟用時的 dump；`sceneFingerprint`（CRLF 正規化後）相同。**r5 再擴（第 5 輪 S4）**，三層斷言：(i) 常數層：`'identity-ledger/1'` 在 `scenario_verify.BRIDGE_CAPABILITIES` 內、**不在** `NATIVE_CAPABILITIES` 內；`_capabilities(['identity-ledger/1'], path)`（預設 `supported=NATIVE_CAPABILITIES`，即 `:576` 驗模型 `requiredCapabilities` 用的那條）→ `SCENARIO_CAPABILITY`／`UNSUPPORTED`，`_capabilities([...], path, supported=BRIDGE_CAPABILITIES)` 通過；(ii) 端到端：手寫一份模型紀錄，其 `base_scene` 帶 `requires identity-ledger/1` → 整份被拒（這條有第二道守門：`modeling/base.py:104-107` 的 `load_base` 自己的 `supported` 不含它，所以 (ii) 單獨存在時抓不到「誤把它加進 NATIVE」，必須有 (i)）；(iii) 橋接回覆：固定 `capabilities` 清單含 `identity-ledger/1`（啟用與否皆含），`required_capabilities` 只在已啟用時含它；已啟用專案的 #46 方案驗證通過（`scenario_verify.py:556-557` 的 `required - available` 為空）。
- **L-13 未啟用零變更**：既有全部 golden、scene139、integrity88、CDP 82 段不改即通過。 r5（第 5 輪 S4）唯一例外：`json_engineering_capabilities` 的固定 `capabilities` 陣列無條件多一項 `identity-ledger/1`，未啟用 World 的橋接回覆也多這一項（`required_capabilities` 不變）；除此之外輸出逐位元不變。本檔掃 `tests/` 與 `geometry-web/`（排除 `tests/evidence`、`tests/release-evidence` 歸檔）沒有活的斷言比對該陣列全文或固定長度（`tests/test_modeling_transport.py:81` 的 8 來自 `serve.py` 的 `/model/capabilities`，是另一份清單）；實作時再掃一次。
- **L-14 建立模型（r2 再擴）**：已啟用專案做空間建模與斷面 `buildModel` → `base_scene` 不含任何身分帳行，與同一 World 未啟用時的 `base_scene`、`scene_hash`、套件逐位元相同；寫出的 `.model.json` 同樣不含記號。`space-workspace.js` 與 `section-profile-workspace.js:100` 的前後比對在啟用後仍判同一來源。F1b `load_base` 產出亦為去身分。r3 補（F7）：已啟用專案「使用目前面」擷取來源（`space-workspace.js:435／451／454`）得到的 `source.base_scene` 不含身分帳行；來源更新（`:507／511`）後亦然；擷取後不做任何變更，預覽與建立不因「來源已變更」被擋。
- **L-15 讀取**：七種節點 `incarnation` 正確；組構所有角材與其他節點 `null`；未啟用時 `active=false`、全 `null`。
- **L-16 啟用使預覽過期（r1 改寫，r3 補互動路徑）**：分別開好工程批次、參數、組構批次、斷面批次預覽、互動預覽（`line preview timber 6 …`，以 `line confirm <token>` 確認；`transactions.inc:551-566`）與已準備的場景匯入，再啟用 → 每一個的確認都被拒為過期、World 不變（互動路徑的診斷為 `I8a: preview is stale`，`:559`）；重新預覽後可確認，且確認結果依啟用後狀態取號。
- **L-17 既有流程 smoke（已啟用專案）**：保存重開、建模、F1b（維持 unknown）、#48 /1 證據、#46 方案、#49 規則案例、參數包匯入匯出，全部通過且輸出無記號洩漏。
- **L-18 突變**（皆須 assertion-red、訊息指出病因）：(a) undo 連配號器一起還原 → L-06 紅；(b) 移除載入完整性 → L-08 紅；(c) 略過 `batch_confirm` 路徑的結算 → L-21 紅（確認已經改了正式 World，新卡片卻沒有新記號）。不得再用「啟用後確認舊候選」：啟用使修訂號 +1，`world_definitions_equal` 又比對整個 World，那個舊候選在結算前就是 STALE，突變不會被執行到；(d) 讓任一內容指紋或 `eng_definition_hash` 含記號 → L-12 紅；(e) 群組改為結束時才結算一次、新物件按 id 排序取號 → L-04「timber 9 的序號小於 timber 7」紅。Q5 改成 B 之後，刪除再建同鍵在「整組一次結算」也會取新號，所以不能再靠 L-04 的 `E1:9` 抓這個突變；(f) 群組內第二行結算失敗時只回滾該行 → 斷言「World 與記號回到群組開始前」紅；(g)（r3，F8；r4 改卡號）`batch_confirm` 不讀 `g_preview` 帶的明示刪除集合，只比前後鍵 → L-21(a) 紅（卡 9 沿用 `E1:9`，訊息指出「明示刪除集合未隨預覽保存」）；(h)（r3，F2）明示刪除集合只在 `engineering-preview` 的批次寫入 `g_preview`（依橋接指令種類判斷），組構與斷面批次不寫 → L-21(c)(d) 紅。注意：把記錄放在 `eng_operation` 的 `delete-parameter` 分支不算突變，因為四條路都轉交到那裡，不會變紅；(i)（r4，第 4 輪 F2）`batch_confirm` 的 `changed` 比較時跳過記號、只比定義 → L-21(a) 紅（定義逐位元相同，`changed=false`，結算後的 World 沒寫回，卡 9 仍 `E1:9`、`history_changed:false`；訊息指出「changed 未計入記號」）；(j)（r4，第 4 輪 F2）結算時延續的鍵不保留原記號（對全部現存受涵蓋鍵重新取號）→ L-24 紅（`history_changed:true`、修訂號 +1、timber 5 不再是 `E1:4`）。 (k)（r5，第 5 輪 S4）把 `identity-ledger/1` 加進 `NATIVE_CAPABILITIES`（或讓 `_capabilities` 的預設改用 BRIDGE）→ L-12 (i) 紅（訊息指出「模型輸入守門被放寬」）；(l)（r5，S4）`json_engineering_capabilities` 的固定清單不含 `identity-ledger/1`，或改成只在已啟用時才列 → L-12 (iii) 紅（已啟用專案的 #46 方案被 `SCENARIO_CAPABILITY` 拒）；(m)（r5，第 5 輪 S2）`stripIdentityLedger` 只剝 `identity` 行、留下 `requires identity-ledger/1` → L-12 剝除一致性斷言紅，且 L-20 (甲)(丙) 紅。
- **L-19 組構角材排除（r1 新增）**：建組構實例（owned timber 10、11、12）→ 三支 `incarnation:null`、dump 無其記號行；同一批次 delete-instance＋create-instance 重用 10–12 → 仍無記號、不產生任何 continuous；普通 timber 10 於另一指令刪除後，實例在同一 id 生成 owned 角材 → 原記號結束。
- **L-20 不完整身分帳不得保存（r2 補恢復）**：測試用故障注入跳過某一分派路徑的結算 → 下一次完整 dump／完整專案保存被拒並指出缺記號的鍵，未寫出任何完整檔。同一狀態下去身分 dump 仍成功，診斷註明不能還原記號，且文字等於該 World 未啟用時的 dump。對那一筆做 undo → 回到結算完整的 World，完整 dump 恢復。不提供補發記號的指令。r4 加重連案例（第 4 輪 F5）；r5 改為本地剝除並加 (丙)（第 5 輪 S1、S2）。(甲)(乙) 在帳不完整的狀態下重新整理頁面（或另開分頁重連）：
  - (甲) 故障注入讓啟用那一步漏配某一鍵（定義不變）。帳不完整後的恢復寫入因完整 dump 被拒而沒寫（`exportSnapshot` 讀完整 dump，main `:1265`），恢復資料停在啟用前。重連 → 握手（`app.js` main `:565-566`，去身分 dump）成功，頁面進入 ready，不停在 `connectionFailed`；恢復資料（`reference-workspace.js` main `:293`、`:303`）以**本地剝除**的探測指紋比對通過（紀錄是啟用前的場景，剝除是 no-op，指紋等於去身分 dump 的指紋），附件與草稿恢復；再讀完整 dump 被拒，所以專案標為未保存並提示「身分帳不完整，須先復原上一步才能保存」；保存仍被拒。核心 undo（`line undo`）一次 → 完整 dump 與保存恢復。
  - (乙) 故障注入讓新建 timber 9 的那一步漏結算（定義已變）。恢復資料同樣停在故障前。重連 → 握手成功、頁面 ready；恢復比對不符，顯示不一致、不恢復、不覆寫目前場景，恢復紀錄保留。核心 undo 一次後再重新整理 → 比對通過，附件恢復。
  - (丙) Finish 中斷恢復（r5 新增，第 5 輪 S2；帳完整的已啟用專案）：已啟用夾具 S 的專案，完成一次試改 Finish（寫入 `record` 與 `finishReceipt`，main `:1572-1574`；`scenarioTicketTransaction` 同時以 `recoveryKey` 與 `receiptKey` 兩個鍵寫入，`:1373`），在本地 UI 確認之前中斷，重新整理頁面 → `restoreSession` 取到 Finish 紀錄（`record=saved`，main `:290`）；該紀錄的場景含 `requires identity-ledger/1` 與記號行，`sceneHash` 取自完整場景；本地剝除後的探測指紋等於去身分 dump 的指紋 → 恢復成功，專案狀態沿用（再讀完整 dump 通過且指紋等於 `record.sceneHash`，不標未保存）。沿用 `tests/test_scenario_recovery_owner.js`（`:183`、`:198` 已驗 `finishReceipt` 寫入）的夾具，把 `dump` 樁換成已啟用場景；`recoveryKey` 與 `receiptKey` 兩個鍵各驗一次。
  - 預期的降級（r5 新增，R5）：帳不完整時，`app.js` main `:4457`（基準 `:4272`）的 `api("dump")` 被拒，`dump.text||""`（main `:4462`）得到空字串，面編輯器的網格引用（`gridRefs`）清空、不顯示網格上的角材引用。這是預期的降級，不是缺陷：它維持完整 dump（§2.5），只在「必須先復原」的狀態出現。(甲)(乙) 要確認頁面仍 ready、不丟例外、復原後網格引用恢復；不加斷言去阻止降級本身。
  - 突變：握手改回 `api('dump')` → (甲)(乙) 都停在 `connectionFailed`，紅（訊息指出「握手依賴完整 dump」）；恢復比對改回完整 dump → (甲) 顯示不一致而未恢復附件，紅；恢復比對改回 r4 的「用 `record.sceneHash` 對去身分 dump」（`sceneHash` 代用）→ (丙) 紅（Finish 紀錄的完整 `sceneHash` 對不上去身分 dump，恢復失效）；**拿掉 `app.js` 連線階段白名單裡的去身分 dump 指令（r5，第 5 輪 S1）→ (甲)(乙)(丙) 都紅**：`apiRequest` 在 `loading` 階段回「場景尚未讀取完成」，握手 `connectionFailed`，`restoreSession` 的探測同被擋，訊息指出「連線階段白名單漏列去身分 dump」。審查原文寫「兩案都紅」，r5 多了 (丙)，所以是三案。
- **L-21 明示刪除（r2 新增，r3 改寫）**：各子案自 L-01 狀態起算。
  - (a) 主案（r4 改寫，第 4 輪 F1）：只用**沒有被引用**的卡。前置：一筆 `engineering-confirm` 執行 `[put-parameter{id:9，欄位 0＝1000 mm、欄位 1＝2000 mm}]`（兩欄都是字面值，沒有任何定義引用卡 9）→ 卡 9＝`E1:9`、field(9,0)＝`E1:10`、field(9,1)＝`E1:11`。主案：再一筆 `engineering-confirm` 執行 `[delete-parameter 9, put-parameter{id:9，與前置完全相同}]`。I38 允許（沒有引用要先解除）。斷言：卡 9＝`E1:12`、field(9,0)＝`E1:13`、field(9,1)＝`E1:14`，都不是 `E1:9`／`E1:10`／`E1:11`；夾具 S 的 8 個記號（`E1:1`–`E1:8`）不變；卡 9 的定義內容指紋與前置相同；回覆 `history_changed:true`、修訂號 +1（定義逐位元相同，只因記號不同而 `changed`，§2.2-2；與 L-24 對照）；一次 undo 回到 `E1:9`／`E1:10`／`E1:11`。r3 的主案用被 timber 5 引用的卡 2，那批違反 I38，只因 `parameter_remove` 不查引用才通過（既有核心缺陷 GEO-258，§7.1），r4 刪除；K3 不寫任何斷言規範「刪除被引用卡」的結果，不論通過或拒絕。
  - (b) 匯入拿回同 id（r3 自行推出的修正）：先以一筆 `engineering-confirm` 建一張沒有被引用的卡 0（一個欄位）→ 卡 0＝`E1:9`、field(0,0)＝`E1:10`。再一筆 `[delete-parameter 0, import-parameters P]`（P 只有一張卡、欄位 id 0）→ `parameter_import` 從 0 找最小空號（`parameters.inc:314`），匯入卡拿回 id 0 → 卡 0 與 field(0,0) 都是新記號（`E1:11`、`E1:12`），不得 `continuous`。r2 寫「先刪卡 2 再匯入」：夾具 S 沒有卡 0，匯入卡會拿到 id 0 而不是 2，碰不到同鍵，所以改案例。
  - (c) 組構路徑（r3，F2；r4 起前置與兩個 op 都同 (a) 的卡 9）：與 (a) 相同兩個 op 改用 `assembly-preview`＋`assembly-confirm`（`assembly_operation` 轉交 `eng_operation`，`assembly.inc:213`）→ 結果同 (a)。同兩個 op 改用 `assembly-generation-preview`（`asm_generation_operation` 轉交 `assembly_operation`，`assembly_generation.inc:101`），以 `assembly-confirm` 確認 → 同。
  - (d) 斷面路徑（r3，F2；r4 起同 (a) 的卡 9）：同兩個 op 改用 `section-profile-preview`＋`section-profile-confirm`（`sp_operation` 轉交 `eng_operation`，`section_profiles.inc:131`）→ 同。
  - (e) 承載面（r3，F4）：**現行沒有同一提交重建承載面的路徑**。`sp_operation` 對承載面只有 `delete-placement`（`section_profiles.inc:100-107`），沒有任何批次 op 能建 D4 承載面；夾具 S 的 placement 0 掛著 timber 5／6，刪它整批必失敗。保留為未來案例：PF-0 衍生承載面實作後，若同一交易能刪除再建同 id 的承載面，補「新記號、不得 continuous」一案。現行只驗刪除本身：另以互動建一個沒有東西掛著的矩形承載面 4，再以 `section-profile-confirm` `[delete-placement 4]` 刪除 → 該鍵結束、dump 沒有它的記號行、I⟨K3-1⟩ 通過。
  - (f) 重宣告 timber 5 仍是 L-02 的沿用，不走這條。
- **L-22 互動清空（r3，F5）**：已啟用夾具 S 送 `line reset` → 成功，且記一步歷史；source-inspect `identityLedger.active=true`；完整 dump 有 `requires identity-ledger/1`、沒有任何 `identity` 行；區段仍是 E1（不需重設），接著建 boundary 7（清空後沒有承載面，先建邊界）→ `E1:9`。一次 undo（撤銷 boundary 7）再一次 undo → 回到 L-01 的 8 個記號，逐字相同。對照：橋接 `reset` 之後身分帳未啟用、區段未設定、歷史清空。
- **L-23 桌面唯讀（r3，F5；r4 改走 GDI 入口，第 4 輪 F3；r5 改為在 Linux 測純判定函式，第 5 輪 S3，K3-LIM-1）**：
  - 為什麼不測 GDI 入口本身：`interactive_apply_line`（`:4831`）與 `gdi_show_three_views`（`:5935`）在 `#ifdef _WIN32`（`:4151`–`:6171`）內；CI 只有 ubuntu（`integration-tests.yml:17`、`:31`），橋接測試在 Linux／WSL 以 `cc` 現編（`tests/_bridge.py`：Windows 不自動編，Smart App Control 擋新編 exe）；`tests/binaries.py` 的指紋檔案集含 `current_geometry.c`，K3-L 一改它，Windows 上既有的 `gdi-contract` 夾具（`tests/gdi_contract_harness.c`，`win_only`）也會 stale。所以 L-23 測 `_WIN32` 外的純判定函式 `host_gate_rejects`（§2.2-4），經橋接唯讀測試接縫 `host-gate-check`（§2.5）；GDI 接線只做 read-back（下）。
  - 載入（r5，R6）：用核心的 `loadfile` 把已啟用場景載入橋接 World（核心的整體取代）。桌面實際以 `gdi_load_scene_file`（`:4778`）載入，不經 `interactive_apply_line`——r4 寫的「經 GDI 的 `interactive_apply_line` 入口載入已啟用場景」更正為「經 `gdi_load_scene_file` 載入」。
  - 斷言（接縫以 `desktop` 為宿主模式，World 為已啟用夾具 S）：下列各行皆 `rejected:true`，訊息「桌面版尚不支援身分帳，唯讀開啟」，且接縫呼叫前後完整 dump、8 個記號與修訂號逐位元不變：新增 `timber 8 …`、`delete timber 5`、`reset`（「清除」）、拖曳產生的 `move …`、`preview …`、`confirm <token>`、`history-begin`、`identity-ledger activate`。單獨的 `undo`、`redo` → `rejected:false`。
  - 換 World 後恢復可寫（對應 r4「載入未啟用場景後可正常提交；undo 回到已啟用場景後又是唯讀」）：以 `loadfile` 載入一份未啟用場景（可 undo 的整體取代）→ 接縫對 `timber 8 …` 回 `rejected:false`；再 `line undo` 回到已啟用 World → 同一行回 `rejected:true`。
  - 對照（證明閘門不是以區段判定）：接縫以 `none` 為宿主模式，同一份已啟用場景（核心，區段未設）對 `timber 8 …`、`delete timber 5` → `rejected:false`；實際送 `line` 重宣告 timber 5（B=40）→ 成功、仍 `E1:4`（同 L-07）。另驗已啟用條件：未啟用 World 以 `desktop` 為宿主模式 → `rejected:false`。匯出得到去身分場景（L-12 已驗）。
  - 突變（皆須 assertion-red）：(1) 判定改為「區段未設定」（r3 的寫法）→ `none` 對照案與 L-07 紅；(2) 不豁免 `undo`／`redo` → 單獨 `undo` 的 `rejected:false` 斷言紅；(3) 判定忽略「已啟用」條件 → 「未啟用 World 以 `desktop`」對照紅。
  - GDI 接線 read-back（Linux 不能執行；**只做確認，並照實報告「GDI 接線未於 Windows 實機執行」**）：逐行確認 (i) `interactive_apply_line` 在 `count<=0` 返回之後、`apply_interactive_tokens` 之前呼叫純函式，傳入的是行程旗標；拒絕時設狀態列「桌面版尚不支援身分帳，唯讀開啟」並返回，不清輸入框、不呼叫 `reference_gdi_confirm`；(ii) 旗標賦值只在 `gdi_show_three_views` 進入視窗迴圈之前這一處，其他路徑（含橋接與 CLI）從不讀它；(iii) `gdi_load_scene_file` 沒有被閘門攔（整體取代）；(iv) 桌面所有改 World 的入口（§2.2-4 清單）都經 `interactive_apply_line` 或 `gdi_load_scene_file`。可另加一個純文字結構斷言（讀原始碼、不編譯）鎖住 (i)(ii) 的相對位置，但它抓不到執行期錯誤，不算執行證據。
- **L-24 內容不變的重宣告批次（r4 新增，第 4 輪 F2）**：已啟用夾具 S，一筆 `engineering-preview`＋`engineering-confirm` 執行 `[put-parameter{id:2，與現有完全相同：欄位 0＝3200 mm、欄位 1＝=f0/2}]` → 確認成功，回覆 `history_changed:false`、`revision` 等於 `before_revision`（修訂號不變）；8 個記號逐字不變；復原歷史沒有多一步；之後建 timber 7 得 `E1:9`（這筆確認沒有取號）。對照 L-21(a)：明示刪除後同鍵重建、定義相同，回覆 `history_changed:true`。突變見 L-18(i)(j)。 **對照組（r5 新增，R3）**：同一夾具 S **不啟用**（未設區段、無記號），送完全相同的 `engineering-preview`＋`engineering-confirm` `[put-parameter{id:2，欄位 0＝3200 mm、欄位 1＝=f0/2}]` → 同樣 `history_changed:false`、`revision` 等於 `before_revision`、復原歷史沒有多一步。證明 put-parameter 冪等本來就是 `world_definitions_equal` 的既有行為；L-24 抓的是「啟用後不得因記號而變成非冪等」，不是新增的特例。
- **L-25 宿主重設區段（r5 自行補充，僅記錄 R2 的驗收）**：以 `serve.py` 的 `/api` 與 `/upload*` 各走一次整體取代，之後立即經 `/api` 送一筆需取號的提交（建 boundary）。(a) `/api` 送 `reset`、`default`、`loadfile <已啟用場景>` 各一 → 每次回覆 `ok:true` 後，宿主已在同一次持有 `bridge_lock` 的區間內送了 `identity-epoch <新值>`；接著建 boundary 成功，取到的記號區段不同於整體取代前的區段，序號接續（行程全域，不從 1 重起）；(b) `/upload/confirm`（`load-confirm`）同；`/upload/prepare`、`/upload/cancel`，以及回覆非 `ok:true` 的 `loadfile`（World 未被取代）不重設；(c) 頁面經 `/api` 送 `identity-epoch …` → 被拒，區段不變。突變：拿掉 `recorded_api` 路徑的重設 → (a) 的建 boundary 以「未設定配號區段」被拒而紅。

**不做**：產品啟用入口；記號 UI；停用；衍生沿革；七種以外型別與組構生成角材；方案比較改用記號；桌面 GDI 宿主設區段。

## 5. K3-48 首版（#48）：邊界／角材證據、耐久關聯、參數欄位採用值

**範圍**（一個 PR）：

1. **附件 schema `geometry-evidence-links/2`**（新能力；/1 照舊可讀）。每筆加 `identityBasis:'ledger'|'legacy-v1'`；target 三型聯集：`parameter-field{projectScope,parameterId,fieldId}`、`boundary{projectScope,id}`、`timber{projectScope,id}`，皆含 `definitionPin, valuePin, incarnation`。`ledger` 者 `incarnation` 必為合法 `E:s`、`valuePin` 必為 64 hex；`legacy-v1` 者兩者必為 `null`。`humanConfirmation:null|{documentHash, definitionPin, valuePin, confirmedAt}`，pin 必等於 target pin。`adoption:null|{observation:'drawing'|'measurement', literal, value:{num,den}, definitionPinBefore, definitionPinAfter, adoptedAt}`（只留最近一次）。上限沿用 256 筆／2 MiB。
2. **建立／重新關聯**：`add`／`rebind` 只產生 `ledger` 連結。目前 World 未啟用時，以**另一筆可復原步驟**自動啟用，再重讀 stamp 與目標記號後寫入。有未確認預覽也啟用，不拒絕；該預覽依 §2.2-1 過期（K3-Q7）。邊界目標由邊界卡片選、角材目標由面編輯器選，經 `source-inspect` 的物件記錄取記號與兩個內容指紋；**組構所有角材不可作目標**（`incarnation:null`，拒絕並說明首版不支援）。
3. **狀態（唯一、依序）**：`source-missing` → `source-changed` → 身分軸：`legacy-v1` 完全沿用現行判定（租約＋`definitionPin`，結果為 `needs-reassociation`／`unchecked`／`confirmed-content` 之一）；`ledger` 依 R⟨K3-2⟩：`unknown`／`conflict`→`needs-reassociation`、`absent`→`target-missing`、`replaced`→`target-replaced`、`continuous`→內容軸 → 內容軸：target 的 `definitionPin` 或 `valuePin` 與目前不同→`target-changed`；相同且有核對→`confirmed-content`，否則 `unchecked`。`canConfirm` 只在 `unchecked`／`target-changed`／`confirmed-content` 為真；在 `target-changed` 核對會同時更新 target 與核對 pin。
4. **採用值**（只限參數欄位）：條件＝身分 `continuous`、原圖未換版／未缺、型別 dimension、欄位為字面值（非算式）、所選觀察值 `rawValue` 非空、`unit∈{mm,cm}` 且可精確解析為 D31 字面有理數；cm 以純函式精確 ×10。流程：證據面板「採用」→ 開既有參數卡編輯器並預填該欄 → 既有參數預覽（I8a）→ 確認同一候選 → 原生提交成功後**同一歷史步**寫入 `adoption`、更新 pin（沿 #77「native confirm＋metadata 同一步」協調）。前端比對原生解析的有理數與純函式預期值，不同即中止。
5. **反向列表**：邊界卡片與角材檢視器以 typed target 過濾同一份附件，不另建對照表。
6. **/1 升級**：開舊專案不改寫；首次寫入時整包升 /2，舊連結標 `legacy-v1`；`rebind` 後才轉 `ledger`。

**受影響檔案**：`geometry-web/evidence-links.js`、`evidence-links-app.js`、`evidence-links-ui.js`、`feature-attachments.js`（註冊 /2）、`project-store.js`（能力與格式，共用 owner）、`parameters.js`（外部預填與確認後 metadata 掛鉤）、`reference-workspace.js`（同一步協調、啟用輔助與預覽守門，共用 owner）；測試 `tests/test_evidence_links.js`、`tests/test_evidence_project_store.js`、`tests/test_evidence_link_native.py`、`geometry-web/evidence_links_integration_test.js`、`geometry-web/evidence_links_browser_check.js`。

**驗收**——夾具 S′＝L-01 狀態再建游離邊界 3（無承載面）→ `E1:9`；自製 1 頁 PDF。

- **E-01**：連到 boundary 1 → `ledger`、`incarnation=E1:1`、兩 pin 為 64 hex；World 不變。
- **E-02**：連到 timber 5、field(2,0)、boundary 3 各一筆，核對全部 → `confirmed-content`。
- **E-03 不再誤報（r2 改案例）**：重宣告 timber 6（B=40）。timber 6 在夾具裡，但不是這四筆的目標。四筆仍 `confirmed-content`。現行實作會因原生修訂號變化變成 `needs-reassociation`，作修前對照。夾具 S′ 沒有參數卡 3，不再用那張不存在的卡。
- **E-04**：重宣告 timber 5（B=40）→ `target-changed`、可核對；核對後回 `confirmed-content`。
- **E-05**：分兩筆刪除重建 timber 5 → `target-replaced`，核對被擋，`rebind` 後恢復。
- **E-06（r1 改寫）**：刪游離 boundary 3（無承載面，可刪）→ `target-missing`；專案仍可保存、觀察值與核對歷史保留；undo → 回 `confirmed-content`。另驗：試刪 boundary 1 被原生拒絕（仍有 placement 0），連結狀態不變。
- **E-07**：保存、新空白上下文重開 → 狀態不變、無需重新關聯。
- **E-08（r2 補租約）**：/1 舊專案在新增之前，狀態與現行一致。新增一筆 ledger 連結時先自動啟用（另一步，修訂號 +1），整包升 /2。舊筆仍是 `legacy-v1`，不改寫成 ledger；但它們的租約綁著啟用前的 `nativeRevision`（`evidence-links.js` 的 `leaseKnown`，基準檔約第 123 行；同檔第 105 行的定位 `sourceStamp` 也含啟用前基準），啟用後租約失效，狀態轉為 `needs-reassociation`。這是預期結果，不是漏改。新筆是 `ledger`。舊筆要 `rebind` 之後才轉 `ledger`。
- **E-09 採用**：field(2,0)=3200，圖面「3235」mm → 參數預覽列 3200→3235 與 timber 5 長度變化 → 確認 → 欄位 3235、`adoption` 與 pin 更新、`confirmed-content`；一次 undo 同時還原欄位與附件。
- **E-10 cm**：「323.5」cm → 3235；「1/3」cm → 10/3 mm，使用處要求整數時預覽列違規、不能確認。
- **E-11 採用拒絕**（World 與附件零變更）：unit null；型別 count／ratio；欄位為算式；身分非 continuous；原圖換版／缺失；預覽取消；預覽過期；boundary／timber 目標無採用入口。
- **E-12 反向列表**：boundary 1、boundary 3、timber 5 各只列自己的證據。
- **E-13 schema 負例**：未知 kind、`ledger` 卻 `incarnation:null`、`legacy-v1` 卻有記號、記號格式錯、超過 256 筆 → 拒，原專案不清空。
- **E-14 預覽不阻擋啟用（r2 改寫）**：未啟用專案中，另一工作區有未確認參數預覽時新增證據 → 不拒絕。歷史出現兩步（啟用、新增），新連結寫入。該參數預覽的確認被拒為過期，參數定義不變。取消或重新預覽後才可確認參數。另驗：原生 `g_preview` 佔著、使用者沒按取消就離開時，新增證據仍成功；之後那個預覽的確認被拒。#46 試改正在保全時新增證據亦成功，保全比對失敗，這次試改不能完成。
- **E-15 組構角材（r1 新增）**：選組構所有角材作目標 → 拒，附件不變。
- **E-16 突變**：(a) 身分改回租約判定 → E-03 紅；(b) 忽略有效值內容指紋 → field(2,1) 應 `target-changed` 案紅；(c) 採用跳過預覽直寫 → E-09「預覽先於提交」斷言紅；(d) cm 換算用 Number → E-10 的 1/3 案紅；(e) 改回「有預覽就拒絕啟用」 → E-14 紅。

**不做**：OCR／自動判讀；採用到邊界、角材或算式欄位；邊或尺寸層級目標；組構 member、組構所有角材、斷面構件目標；多筆採用歷史；跨專案證據搬移。

## 6. K3-44 首版（#44）：模型身分引用（Q15-B）、延續證明的受控更新、faces 多載體

**範圍**（一個 PR，於 K3-48 之後）：

1. **身分引用欄位 `sourceIdentity`**：模型紀錄新增可選欄位 `{schema:'model-source-identity/1', roots:[{role, kind, id, fieldId?, incarnation, uncovered?}]}`。`incarnation` 是 `E:s` 或 `null`。**r3（F6）：`null` 必須帶理由標記 `uncovered`，第一版只有一個值 `"assembly-owned"`**：寫入當時該角材屬 D34 組構所有（`sourceTimbers` 沒有濾掉它們，`space-workspace.js:361-363`）。**r4（第 4 輪 F4）：基準上目前走不到**。`base_scene` 是整個 World 的 dump；World 有 `owned`／`assembly` 行就帶 `assembly-*` 能力（`geometry-core/modeling/common.py:32-35`），建模只支援 engineering／parameters／section-profile（`geometry-core/modeling/base.py:104-107`），F1b 也拒（`model_update.py:64-66`），所以含組構角材的 World 建不出模型，`null` 根寫不出來。以下標記規則保留，作為建模日後支援 assembly 能力時的規格；M-12 的 schema 驗證仍可用手寫紀錄測。該根 R⟨K3-2⟩ 判 `unknown`，紀錄仍保存，不整筆拒絕（K3-Q32）。驗證規則只看紀錄本身：`incarnation:null` ⇔ 帶 `uncovered:"assembly-owned"`，且該根 `kind` 必為 `timber`；沒有標記的根必須是合法 `E:s`；`uncovered` 只能是已列的值。驗證**不**查目前 World 裡那支角材是否仍屬組構：所有權會變（實例刪除後同 id 可再建成普通角材，普通角材刪除後其 id 也可被實例重用，`assembly_generation.inc:105-115`），匯入時查不出寫入當時的狀態。`base_scene` 仍為去身分 dump。只在建立或更新確認時身分帳**已啟用**才寫入；roots 必須與紀錄的根集合完全相同——plan：`placement_id`、`boundary_id`（>0）、`timbers[]`、`obstacles[]`；faces：`uses[].placement_id`、`obstacles[]`。記號與 `uncovered` 標記在與 `base_scene` 同一原生修訂號內讀取（記號取自 live World 的 `source-inspect`），修訂號變了即過期重來。F1b 的新紀錄 `base_scene` 由 `load_base` 讀 `current_scene` 得到（`model_update.py:394`，寫進 `inputs.base_scene` 在 `:396`），同樣去身分；`sourceIdentity` 取自目前 live World，不取自 `_graph` 的子行程（那裡載入的是去身分場景）。
2. **啟用入口（r2 寫死）**：建模與 F1b 對話**不自動啟用**；未啟用時顯示「啟用物件身分追蹤後，日後可證明來源延續」與明確按鈕，沿用 K3-48 的啟用步驟（另一筆可復原步驟）。有未確認預覽時**仍可按**，不拒絕。按了之後，該建模或 F1b 預覽依 §2.2-1 過期，須重新預覽（M-11）。未啟用時照現行建立，紀錄無 `sourceIdentity`。
3. **F1b 延續判定與預填**：以舊紀錄 `sourceIdentity` 對目前 World 做 R⟨K3-2⟩。`continuous` 的根預填並標「身分延續已證明（可改選）」；`edges` 只在 boundary 為 `continuous` 且舊快照與目前的定義內容指紋相同時預填；`absent`／`replaced`／`conflict` 的根須明選改指或明確移除；`incarnation:null` 的根是 `unknown`，不預填；舊紀錄無 `sourceIdentity` → 全部 `unknown`、不預填，行為同現行。預填不等於確認。
4. **faces 多載體更新**：selection 變體 `{mode:'faces', uses:[{placement_id}], obstacles}`；個數與舊紀錄相同，第 i 項沿用舊第 i 項的 `orientation`／`purpose`；重複拒；走既有 `space_modeling.preview` faces 路徑；faces＋timbers 仍 UNSUPPORTED。
5. **收據與守門**：收據升 `geometry-model-update-candidate/2`（暫態）加 `identity:{ledger, roots:[{role,kind,id,before,current,status}]}`；確認時重做 R⟨K3-2⟩，任一根狀態或記號改變→過期、零寫入；同 `modelId`、一筆 undo（現行契約不變）。
6. **F1a 呈現**：模型層 `identityContinuity` 只由 `sourceIdentity` 的根彙總：全 `continuous`→「物件延續已證明」；有 `absent`／`replaced`／`conflict`→「部分來源物件已不存在或已刪除重建」並列出；有 `unknown`（含 `incarnation:null` 的組構角材根）或無 `sourceIdentity`→「物件延續性未知」。閉包內其他物件不保存引用，不作延續判定（K3-Q21）。

**受影響檔案**：`geometry-web/model_update.py`、`model-update.js`、`model-update-app.js`、`source-inspector.js`、`space-workspace.js`（`sourceIdentity` 擷取與啟用入口）、`project-store.js`（模型紀錄接受 `sourceIdentity` 及其與根集合一致性驗證；共用 owner）、`reference-workspace.js`（共用 owner）；測試 `tests/test_model_update.py`、`tests/test_model_update.js`、`tests/test_source_inspector.js`、`tests/test_space_model_store.js`、`geometry-web/model_update_browser_check.js`、`geometry-web/space_model_test.js`。

**驗收**——M1：plan，placement 0／boundary 1，edges `[0,1,2,3]`，timbers `[5,6]`，obstacles `[column 2]`，於已啟用 World 建立；M2：faces，uses `[{P1,+1,boundary},{P2,−1,boundary},{P3,+1,calculation-cap}]`。

- **M-01（r1 改寫）**：未啟用專案建 M1 → 無 `sourceIdentity`、格式號與現行相同。按啟用後重新預覽並建 M1′ → `sourceIdentity` 5 個根（placement、boundary、2 timbers、column）記號正確；兩者 `base_scene`、`scene_hash` 逐位元相同。
- **M-02**：改 field(2,0)=3235 → 開更新：全部根 `continuous`、edges 預填；確認 → 同 `modelId`、一筆 undo；保存重開再開更新仍全部 `continuous`。
- **M-03**：分兩筆刪除重建 timber 6 → `replaced`、未預填；未明選前不能預覽。
- **M-04**：刪 column 2 → `absent`；須明確移除。
- **M-05**：移動 boundary 1 一邊 → placement／boundary 預填、edges 留空。
- **M-06**：無 `sourceIdentity` 的舊紀錄 → 全 `unknown`、不預填，既有 22／39 個測試行為不變。
- **M-07 競態**：審閱後、確認前分兩筆刪除重建 timber 5 → 確認拒為過期，零變更。
- **M-08 faces**：改 P2 輪廓 → 三個 use `continuous` 預填、朝向用途沿用；確認 → 同 `modelId`。分兩筆刪除重建 P3 → `replaced` 須改指；把 uses 減為 2 → 拒。
- **M-09**：assembly-owned 與 faces＋timbers 仍 UNSUPPORTED。r4 補（第 4 輪 F4）：World 只要有 `owned`／`assembly` 行，建模（`base.py:104-107`）與 F1b（`model_update.py:64-66`）就回 UNSUPPORTED，與是否啟用身分帳無關；啟用前後回覆相同。這也是 M-14、M-13(e) 目前走不到的原因。
- **M-10 F1a**：M-02／M-03／M-06 三情形顯示三種彙總文字，唯讀前後 World、dirty、history 不變。
- **M-11 預覽中啟用（r2 定案）**：在建模預覽後按啟用 → 啟用成功，該預覽確認被拒為過期；重新預覽後可建立且帶 `sourceIdentity`。這條是啟用政策的驗收，不是例外。F1b 預覽同樣：按啟用後原候選過期。
- **M-12 schema（r2 補 null，r3 依 F6 改為依標記驗證）**：下列任一 → 整份匯入拒絕，原專案不變：`sourceIdentity` 的根集合與紀錄不符；沒有 `uncovered` 的根記號格式錯或寫成 `null`；有 `uncovered` 的根卻帶 `E:s`；`uncovered` 不是 `"assembly-owned"`；`uncovered` 出現在 `timber` 以外的根。合法：帶 `uncovered:"assembly-owned"` 的 `timber` 根 `incarnation:null`——即使目前 World 裡那支角材已變成普通角材，或已不存在。r3 刪除 r2 的「未啟用專案卻有 `sourceIdentity` → 拒絕」（r3 自行推出，依 F6 同一原則）：啟用那一步可被復原，前端歷史窗外的「只復原核心」退路又保留附件，所以專案可以合法地處於「World 未啟用、模型紀錄帶 `sourceIdentity`」；這時 R⟨K3-2⟩(1) 判 `unknown`，不拒絕重開。
- **M-14 組構角材根（r2 新增，r3 補標記；r4 標「目前走不到（建模不支援 assembly 能力）」，第 4 輪 F4）**：基準上這個 World 一建模就 UNSUPPORTED（M-09），本案不列入 K3-44 的驗收執行，保留為建模日後支援 assembly 能力時的規格。屆時：plan 的 `timbers[]` 含一支組構所有角材與一支普通角材，於已啟用 World 建立 → 紀錄保存。普通角材根有 `E:s`；組構角材根 `incarnation:null`、`uncovered:"assembly-owned"`、狀態 `unknown`，不預填。不因這一個根拒絕整筆。F1a 彙總為「物件延續性未知」。接著刪除該組構實例、以普通角材在同 id 建立 → 保存、重開：紀錄仍被接受（依標記驗證），該根仍 `unknown`。
- **M-13 突變**：(a) 預填改以同 id 判定 → M-03 紅；(b) 移除確認時重比 → M-07 紅；(c) 指紋變時仍預填 edges → M-05 紅；(d) `base_scene` 改用含記號 dump → M-01 逐位元相同斷言紅；(e)（r3，F6）`null` 根的合法性改查目前 World 的所有權、不看 `uncovered` → M-14 第二段（實例刪除後同 id 改為普通角材）重開被拒而紅。r4：**目前走不到（建模不支援 assembly 能力）**，與 M-14 一起保留為未來規格，不列入 K3-44 的突變執行；在那之前，「驗證不查目前 World」由 M-12 的手寫紀錄案例覆蓋。

**不做**：owned 模型保存與更新；自動更新模型；以 vertexKey 對應邊；faces 增減面；閉包節點身分判定；#47 擴充。

## 7. 全域不做的事

- 七種以外型別、D34 組構生成角材、衍生沿革、邊／頂點層級身分、跨專案同一物件判定、停用身分帳。
- 不改 World 內引用（ParameterRef、at-line、at-face 等）的語法或語意；記號不參與任何幾何或內容指紋。
- 不以記號改寫 #46 方案比較或 #77 房間來源的既有 pin 機制（可作後續）。
- 不顯示、不允許編輯記號；不以記號自動重新關聯或自動更新。
- 桌面 GDI 宿主不設區段；已啟用專案在桌面版唯讀，以宿主模式旗標 `desktop` 判定；判定是 `_WIN32` 外的純函式，GDI 入口只呼叫它（K3-LIM-1，見 §2.2-4；r5，第 5 輪 S3）。
- 不部署、不付費、不改 CI 設定；實體手機／OS 選檔未驗不冒稱。
- 不修 §7.1 的既有核心缺陷 GEO-258，也不規範它目前的行為（不寫成允許，也不寫成拒絕）。

### 7.1 既有核心缺陷 GEO-258（不在 K3 範圍）

**r4（第 4 輪 F1【阻擋】）**：r3 的 K3-LIM-2（「同一提交明示刪除後同鍵重建時，World 內引用依 id 改綁到新存在期，K3 不記錄、不拒絕」）撤回。r3 的前提「I38 允許」是錯的：I38 的例外要求「先明確改綁／解除引用，或在同一候選內完成解除與刪除後整包驗證」（`公理層.md:814`），下面兩個反例都沒有解除引用。原生能通過，只因 `parameter_remove`（`geometry-core/parameters.inc:277-284`）不檢查引用。這是 I38 的既有實作缺陷；r3 把「不據此拒絕」寫進 D⟨K3-4⟩，緊接在「被引用者不得被刪除（I38）」之後，SSOT 自相矛盾。

兩個反例統一列為**既有核心缺陷，已登記 BACKLOG GEO-258**（在 `origin/docs/ledger-closeout-20261009` 的 `BACKLOG.md`；撰寫時尚未合入 main）。**不在 K3 範圍，K3 不規範其行為**：

- 反例一（I39 改綁）：同一批先 `delete-parameter 0`（卡 0 仍被引用）再 `import-parameters`。`parameter_import` 從 0 起找最小空號（`parameters.inc:314`），匯入卡拿回 id 0，World 裡原本指向卡 0 的 ParameterRef 改指這張匯入卡，違反 I39「建立與來源專案獨立的副本」（`公理層.md:821`）。
- 反例二（I38 刪除被引用卡）：同一批 `delete-parameter 2`（field(2,0) 仍被 timber 5 引用）再 `put-parameter{id:2}`。沒有解除就刪除，違反 I38；已刪欄位 id 也被同批再用。

K3 對這兩例的立場：
- 公理不描述它們的結果（AXIOM-DIFF D⟨K3-4⟩、B8 已刪 r3 句）；K3 的驗收不以任何斷言規範「刪除被引用卡」通過或被拒，L-21 只用沒有被引用的卡。
- 身分帳本身不受影響：只要這種提交在現行核心通過，它仍是明示刪除，同鍵新物件取新號，World 外的身分引用判 `replaced`，不會誤報延續。GEO-258 修好後這種提交被拒，World 不變，同樣不取號。兩種結果下 K3 的規則都不用改。
- 未來：PF-0 衍生承載面若允許同一交易刪除並重建同 id，被引用承載面的刪除同樣受既有保護約束，由 PF-0 定，不由 K3 定。

不在 K3 內「整筆拒絕」：那是 I38 本身的檢查，應由 GEO-258 修在 `parameter_remove`（或交易驗證）裡，不是身分帳的規則（K3-Q33）。

## 8. 寫入 SSOT 時的連帶工作

採納時：依 `AXIOM-DIFF.md` 改 `公理層.md`（Windows 工作區為 CRLF，二進位安全寫入），條號由主迴圈統一配發（PF-0 修訂版已佔 D41–D45／I52–I57／R41–R46；K2b 已引用 `D⟨K3-1⟩`、`R⟨K3-1⟩`，配號時一併替換）；同步 `geometry-guide/公理層-白話.md`、`sync_axiom_reader.py` 重建、`--check`、`tests/test_axiom_reader.py`；下一個 commit 把 `geometry-core/modeling/__init__.py:19` 的 `AXIOM_REVISION` 指向採納 commit，處理模型套件公理版本相容（`tests/test_engineering_model_compatibility.py`）；在 `geometry-core/` 建立正式契約，寫入內容指紋的演算法與欄位名（`definitionFingerprint`、`valueFingerprint`）、橋接指令對照、去身分 dump 指令的正式名稱，以及明示刪除的 op 清單；BACKLOG 記錄（§7.1 的既有核心缺陷已登記為 GEO-258，不另開；r4）。條文採納不等於任何 PR 完成。

**契約層的明示刪除 op 清單（r3，F3）**：公理只寫原則句（D⟨K3-2⟩：提交中任何操作使該受涵蓋物件不存在，即為明示刪除）。契約列出基準 commit 上會這樣做的 op，新增任何會移除受涵蓋物件的 op 時須同時登記，並在該 op 執行時把鍵記進明示刪除集合：

| op | 移除的鍵 | 會出現在 |
|---|---|---|
| 互動 `delete boundary｜placement｜timber｜column｜beam <id>` | 該鍵 | `line`、桌面輸入、群組內一行、互動預覽確認 |
| 互動 `reset` | 全部受涵蓋鍵 | `line reset`、桌面「清除」 |
| `delete-parameter` | 卡片與其全部欄位 | 工程、組構、組構生成、斷面四種批次（皆轉交 `eng_operation`）；記錄掛在 `parameter_remove` 內 |
| `put-parameter` 重宣告時省略的欄位 | 該 `(parameter-field,…)` 鍵 | 同上四種批次（r3 自行推出；現行 I38 擋住同提交再用該 fieldId，`parameters.inc:264`，所以目前觀察不到差異，列入是為了讓原則句閉合） |
| `delete-placement` | 該承載面 | 斷面批次（`section_profiles.inc:100-107`） |
| PF-0 衍生承載面的刪除 | 該 `(placement,id)` | op 名待 PF-0 實作切片定義（PF-0 r2 L4）；PF-0 先寫入時一併登記 |

D34 組構實例生成、更新、刪除所移除的角材不受涵蓋，不列。

**與 K2a 統一「刪除」的定義（r3，F12）**：K2a 的孤兒判定寫「本專案中任何一筆已提交的交易，只要在操作中刪了基底、或結果中基底不存在」，並要核心確認回執列出「本交易刪除的 `(kind,id)`」（K2a `PROPOSAL.md` A2-4 與 A4 孤兒掃描）。這與本案原則句是同一個定義。寫入 SSOT 時兩案共用同一份原生明示刪除集合：K3 用其中受涵蓋的鍵，K2a 另需 D29 網格系統與 D30 網格配置，由同一套記錄機制擴充種類，不另寫一套判定。本檔不改 K2a 檔案；主迴圈寫入時對齊。

## 9. 自檢

### 9.1 與既有條文的介面核對

| 既有條文（行） | 介面 | 結論 |
|---|---|---|
| D1（`:33-39`） | 記號不佔 ID、不改 ID 範圍 | 相容 |
| D9（`:135-149`） | 記號非定義但存於 World | 需修訂（B1） |
| D12／I14（`:59-63`、`:648-649`） | 原生對畫布座標有展示保留處理（`current_geometry.c:3924` 起），記號**不得**套用，須隨 World 還原；`world_definitions_equal` 只略過 canvas_pos，因此記號差異會被視為定義差異——與 Q13-B 一致；它也決定 `batch_confirm` 的 `changed`，須以結算後的 World 比（r4，第 4 輪 F2，§2.2-2） | 相容；實作注意 |
| D19a（`:276-279`） | ruleKey 服務 World 內引用、隨 World 還原；記號服務 World 外引用、配號器不倒退；身分帳只在專案內比對 | 相容，不改 |
| D26／D27／D32 | (id, version, 指紋) 不可變，不需記號 | 不涵蓋 |
| D29／D30（`:393-450`） | vertexKey 不受影響；邊層級身分延後 | 相容 |
| D31／I38（`:452-473`、`:805-815`） | World 內 ParameterRef 不加記號。重宣告保留的 fieldId 沿用；`delete-parameter`（任何交易）連欄位一起結束，同批再建是新存在期。r4（第 4 輪 F1）：不改 I38、不另訂例外。第 814 行的例外前提是先解除引用或在同一候選內完成解除；同批刪除仍被引用的卡而未解除（含先刪再匯入的 I39 改綁）是 I38 不允許、原生未檢查的既有核心缺陷 GEO-258，K3 不規範。r3 的 K3-LIM-2 撤回 | 相容；GEO-258 不在範圍（§7.1） |
| D34／I42（`:494-500`、`:843-848`） | 分件身分依 instance／member，不依角材 id；批次在最小空號重用 id（`assembly_generation.inc:105-115`），實例更新保留 id（`:111`）。以角材 id 判定會與 D34 矛盾，故不涵蓋 | 以排除解決 |
| D35–D40 | 不涵蓋 | 相容 |
| I8（`:566-573`） | 每個提交結算一次；群組內每行各自結算。結算失敗在群組內一律整組回滾（`current_geometry.c:4078-4081`；不回滾的分支只屬預覽行，走不到，§2.2-2） | 需修訂（B3） |
| I8a（`:574-602`） | 第 587、596 行：啟用雖不改定義，仍使未確認預覽過期（Q13-B）；身分引用重比 | 需修訂（B4） |
| I9（`:604-608`） | 記號行在全部定義與 canvas-pos 之後 | 相容 |
| I32（`:760-767`） | 新能力 | 需修訂（B5） |
| I36／I39／I41 | 記號隨保存與復原；參數包不帶記號、匯入取新號；I39 與 K2b 各只附加一句 | I39 附加（B6） |
| R4（`:891-910`） | 記號在 dump 內，重放只還原 | 需修訂（B7） |
| R8／R11／R13 | 原 id 片沿用、新片取號、改掛是修改 | 由 D⟨K3-2⟩ 推出 |
| R12 | 鍵含類別 | 相容 |
| D25（`:340-352`） | 交換包不含身分帳 | 需修訂（B2） |
| K2b `D⟨K2b-4⟩`(f)、`I⟨K2b-4⟩`(f) | 公理句不再寫「若採納」。D⟨K3-4⟩ 自己陳述：記號不跨專案、不寫入交換格式、匯入一律新配。與 K2b (f) 同義，但不互相當作條件。匯出 `.scene` 與回報依此去身分。K2b「base_scene 屬快照命名空間」與 Q15-B 一致 | 一致 |
| 原生歷史 32 步與前端 core-only 回退 | 附件可活得比原生歷史久；比對得 `absent`／`unknown`，保守正確 | 相容 |

### 9.2 仍推不出唯一行為／仍有疑慮之處

1. **區段唯一性是機率前提**：跨行程不撞號只靠 128 位元密碼學亂數，本層無法推導，只能列為前提；以「不得等於目前 World 已出現的區段」「行程全域序號」「測試宿主禁止重用」減輕。
2. **明示刪除改為原則句（r3，F3）後，剩下的是登記紀律**。公理不再有閉集；漏洞改在實作：新增會移除受涵蓋物件的 op 卻沒登記進 §8 清單、沒在執行時記進集合，同一提交刪後重建同鍵就會被判成延續。L-21(a)–(d) 與 L-18(g)(h) 只抓得到已登記的路徑。承載面目前沒有同提交重建的路徑（L-21(e)），PF-0 衍生承載面實作時要補案。
3. **內容指紋涵蓋哪些欄位仍由正式契約定**。公理只定義「定義內容指紋／有效值內容指紋」回答內容是否相同。boundary 的定義內容指紋是否含 vertexKey，要寫進契約，否則 `target-changed` 的靈敏度仍不唯一。
4. **群組失敗的既有條件：走不到（r3，F10）**。`current_geometry.c:4079` 的「預覽仍有效且 token 已變時不呼叫整組回滾」只在該行回傳失敗、且這一行剛產生新預覽時成立；那種行是預覽，不改 World，不結算。結算只發生在該行成功改了 World 之後；互動 `confirm` 先把預覽設為非 ready（`transactions.inc:564`）。所以結算失敗必定整組回滾，不會留下不完整帳。r2 列的疑慮撤銷。
5. **帳不完整時去身分 dump 仍成功**。完整保存被拒，但匯出 `.scene`、回報、建模仍拿得到不含記號的文字。使用者可能以為已經保存。診斷有寫，沒有第二道拒絕。
6. **桌面版限制（K3-LIM-1，r5 再改）**：已啟用專案在桌面 GDI 唯讀，直到桌面支援區段。判定是 `_WIN32` 外的純函式 `host_gate_rejects`（宿主模式旗標為 `desktop` 且 World 已啟用 → 除單獨 `undo`／`redo` 外拒絕），GDI 的 `interactive_apply_line` 入口只呼叫它；L-23 在 Linux 經橋接唯讀測試接縫 `host-gate-check` 測它，不新編 Windows exe（SAC；`tests/_bridge.py` Windows 不自動編）。核心（無旗標）行為與 L-07 不變。剩下的疑慮：GDI 兩處接線（`gdi_show_three_views` 設旗標、`interactive_apply_line` 呼叫判定）在 Linux 無法執行，只能 read-back；接線寫錯（判定放錯位置、漏了拒絕後的 return）不會被任何自動測試抓到，要在有 Windows 機器時人工驗一次，並在 PR 照實寫「未於 Windows 實機驗證」。另：K3-L 改動 `current_geometry.c`，`tests/binaries.py` 的指紋檔案集含它，Windows 上所有 exe 都會 stale，在 Windows 重編會撞 SAC，測試因此只在 Linux／WSL 現編。行號以基準的 `interactive_apply_line`（`:4831`）、`gdi_load_scene_file`（`:4778`）、「清除」（`:5533`）、復原／重做（`:5562`、`:5567`）為準。
7. **GEO-258（r4 取代 r3 的 K3-LIM-2）**：同批刪除仍被引用的參數卡（含先刪再匯入）是 I38／I39 的既有核心缺陷，K3 不規範其行為（§7.1）。身分帳在它修好前後都給出正確的存在期；World 內引用被靜默改綁，是 GEO-258 要修的事，不是 K3 的已知限制。
8. **恢復資料改去身分比對後的強度（r4 自行推出；r5 改為本地剝除，第 5 輪 S2）**：`restoreSession` 以去身分指紋核對，看不出「只有記號不同」。補法：比對通過後再讀一次完整 dump，被拒或指紋不等於 `record.sceneHash` 就標未保存（§2.5）。r4 的「另存 `probeHash`、舊紀錄以 `sceneHash` 代用」已撤回：`record.session===connection.session`（main `:294`）使 K3 之前的紀錄不可能匹配，而 K3 之後試改 Finish 寫的紀錄（main `:1572-1574`，`recoveryKey` 與 `receiptKey` 兩處）沒有 `probeHash`，會被當 saved 恢復（main `:281-290`），用去身分 dump 對完整 `sceneHash` 比必不符。本地剝除不需要新欄位，也不需要寫入端第二次 dump，所以 r4 的「revision 相等不保證同一快照」疑慮（第 5 輪 R1）一併消失。仍有的限制：這仍是同一服務工作階段內的核對，跨工作階段的情形照舊被 `record.session` 擋下；剝除函式必須與原生去身分 dump 逐位元一致（L-12 鎖住），否則所有已啟用專案的恢復都會誤判不一致。另一個不對稱：main 新增的試改續接（`reference-workspace.js:1517`、`:1522`）與 Finish 退休核對（main `:1416`）仍用完整 dump，帳不完整時續接失敗（保留資料、不卡連線），沒有改成去身分。
9. **固定能力清單是未啟用狀態也會變的唯一輸出（r5 自行推出，S4）**：`json_engineering_capabilities` 的固定 `capabilities` 陣列無條件多一項，所有呼叫它的回覆在未啟用 World 也多這一項（呼叫點：`engineering_bridge.inc:40`、`:163`，`scene-import-bridge.inc:42`、`:67`，`section_profile_bridge.inc:99`，`web_bridge.c:329`、`:854`）。本檔掃過 `tests/` 與 `geometry-web/` 未見活的斷言比對全文，但使用者自己的外部腳本若比對全文會變紅；`required_capabilities` 不變，所以不影響任何以 `required` 判斷能力的流程。
10. **`restoreSession` 的完整 dump 再讀（r5 自行補充，需主迴圈確認）**：S2 裁決寫「不做第二次 dump」，我理解為取消寫入端為取得 `probeHash` 而多做的那次去身分 dump（也就是 R1 的來源）。恢復時比對通過後「再讀一次完整 dump，被拒或指紋不等於 `record.sceneHash` 就標未保存」我保留，因為本地剝除與去身分 dump 都看不出「只差記號」與「帳不完整」。若裁決原意連這一步也要拿掉，這兩種情形就不再標未保存，L-20 (甲) 的「標未保存」斷言要刪，保存仍由完整 dump 被拒擋住。

### 9.3 剩餘風險

- K3-L 的指令分派層結算需涵蓋 web bridge 與桌面兩個入口；L-20 只保證漏結算時完整檔不會寫出，不保證操作不被擋。
- #77 房間來源與 #46 方案比較暫時保留各自 pin，與身分帳並存。啟用會使進行中的 #46 保全過期。
- 邊界層級證據較粗：任何輪廓變動都使核對變 `target-changed`。
- 實體手機、OS 選檔與 IME 未驗；CI 受計費阻擋時以本地同 head 證據為準並照實報告。 K3-LIM-1 的 GDI 兩處接線只能 read-back，Windows 實機未驗；PR 與回報照實寫「未於 Windows 實機執行」，不冒稱（r5，S3）。
