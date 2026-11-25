# PF-6 App C1 v2：一般面表單接線

工作包 C（issue #454）及 R2（issue #461），設計及補丁交付在 issue #128。
作者基底：`b3c4b981bb96b118c1c05b7a1bd98062d710c8b2`。
原生 PF-6 已由 #447 進 main；本片是尚待套用、正式 CI 與真 Chrome 核對的 App 候選，
不把補丁交付、Node／原生測試或設計文件當成 L4。
不改 `公理層.md`、生成演算法、R43 門檻、既有歷史 golden 或存檔格式。

## 使用者路徑與範圍

既有物件面 → 面內屬性檢查器 →「面設定…」→「完成面／骨架…」→
「完成面與鋪排」表單 → 已確認鋪排的「建議角材」。
若面或鋪排仍有草稿，先走原流程確認；PF-6 不暗中把其他草稿併成交易。
子表單取代同一區域的內容及操作列，離開後回到原鋪排；不新增工具列或常駐入口。

1. 明選 A、B 來源和主／副方向。來源可以是直接值、既有規格、固定版本材料 A／B 欄、
   或工程參數卡的指定欄位。初態空白；不猜規格、不把同數值來源合併。
2.「取得建議」只分析。建議初態全不選，可以逐項勾選或全選／清空。
3. 明按預覽才以完整選集呼叫 `pf6-select`。任何選集或輸入變動立即撤銷本機可確認 token，
   完成舊候選精確取消後才建立新候選；不拿舊建議的長度冒充 selected 世界的結果。
4. 表單顯示同一 selected 候選的 A／B 來源及生效值、主格／宿主來源、各支前後尺寸、
   中線與世界幾何、去重後支數，以及完整既有 `panel-fill-workspace/1` 投影的逐片／縫／
   邊／R43 寬度和門檻。無效或不完整時仍可看診斷，但不能確認。
5. 取消只釋放候選與租約，不變 world、配號、保存狀態、附件或歷史。
   確認只使用原 token／session／context／revision，一次共享歷史；一次復原／重做回完整前後世界。
6. 正式結果是既有普通 D7、衍生宿主與 from-fill 主格，沿既有 `.gcanvas` 定義保存與開啟。
   不保存建議 token／setKey／generation，不增加 PF-6 recipe 或新 archive format。

第一片只對正式 fill 做 PF-6 建立：HTTP 明確要求 `pre:[]`、`post:[]`。
原生 builder 的任意外層 DSL、跨 fill 編輯／刪除或其他批次操作不在此 App 入口。
同一面重開功能會從當下正式世界重算，不自動復活先前候選。

## 與 R03、其他候選與派生宿主的關係

R03 與 PF-6 共用單一角材候選 owner，不能同時持有預覽；先完成或取消一方，再取得另一方。
邊界只要已有完成面，現行 R03 就必須回 `UNSUPPORTED_SCOPE`；PF-6 以正式鋪排為前提，
所以 PF-6 後在同一邊界執行 R03 必拒。取消 PF-6 候選後 R03 不再回 `PENDING`，
但已有完成面的限制仍然成立，不能把此時改回 `UNSUPPORTED_SCOPE` 寫成 R03 生成成功。

反向可分析：R03 先確認後，PF-6 使用 R03 已建的那份 fill、派生宿主和 from-fill 主格。
B 必須與宿主 h 相等，主格須同 fill，主支軸須一致。R45(3) 省略已有承接的外邊；
同位板縫候選沒有自動沿用既有角材的規則，仍由原生逐條求值拒絕不成立候選。
App 不另造跨流程去重、不重寫 R03 recipe；對 R03 的既有鎖定政策與生成規則零變更。

確認後派生宿主的物件畫布、面內畫布、宿主卡與參數使用處顯示由工作包 A 負責。
本片的實機核對範圍只有這個表單與既有三視圖；三視圖仍待真 Chrome 留原件，
不能把表單 SVG 或 Node renderer 當成三視圖驗收。

## 同一候選的原生投影

`panel_fill_builder_bridge.inc::pf6_json_app_view` 在既有 suggest／select JSON 增添 `appView`，
直接重用 `json_panel_fill_ui_contract`，不新增提交或驗證路徑。
schema 是 `panel-fill-builder-workspace/1`，revision、setKey、generation 保留精確文字。
`input` 保存完整 typed source；`host`／`grid` 表示同一交易的存在或建立；
`timbers` 列出候選前後世界中所有角材的來源、尺寸、中線與世界幾何；
`uiContract` 直接重用既有 PF 投影，完整性是所有子投影的合取。
`ok:true, valid:false, error` 代表整輪分析失敗，即使 entries 還有前段資料也全部不可勾。
預覽只帶 `createdDefinitions` 的 kind/tempKey/candidateId，並要求
`candidateIdsAreTemporary:true` 與 `idMap:null`；畫面標示暫號，正式 idMap 只讀確認回執。
逐項 clause 與原生診斷原樣呈現，不從 JS 解析訊息另推幾何規則。

原生 oracle `tests/pf6_app_oracle.py` 先自行建構預期角材，再用獨立區間聯集檢查 R43。
300×300、板 100×100、縫 3、X=8 的具名 fixture：A=27／B=30 時全選 16 個來源去重為
12 支；移除第一條主支的三個 alias，13 個明選來源重算為 9 支，副支最終長度為
`164,164,55,164,164,55`。六組 A 與結構側掃描、typed 來源、既有同值不同 h 來源、
mainAlong 保留都由原生測試逐值比較。這些是 oracle 幾何值，不是 canvas assertion count。

## HTTP、回執與本機 owner

`/panel-fill/builder/suggest` 與 `/select` 使用既有 1 MiB 限制，要求目前版本、session、
UUID requestId；回執綁原始 body SHA-256，重播不重做。server 自建短命 JSON 檔，
客戶端不能以 `/api` 提供檔案路徑。ACK 仍限 256 筆、互不重複、不得 ACK 本次 request。
terminal `pf6-confirm`／`pf6-cancel` 必須帶回執，token 是 1…4294967295 的精確正整數。
suggest 與空選 NO_OP 持共用租約但 token 為 null；非空 SELECTED 候選（含無效）才有正 token。
無效候選也要精確取消。宿主、工程參數卡及欄 ID `0` 仍合法，不能混同候選 token。
服務只把自己的暫存檔交給 bridge；`ask_bridge` 的 Windows→WSL 路徑轉換明列
`pf6-suggest` 與 `pf6-select`，兩者各有功能測試及具名撤回。

回覆中斷只查原 requestId／原 session，不重送。direct terminal 回覆也須帶原 session；
缺少或不同時不能直接寫本機歷史，只查原回執。退休表單仍以原 owner 核對 late receipt，
不拿新表單或新服務的回覆替代。尚未送出的連線 gate 明記 `sent:false`，不能進等待不存在
回執的 unknown；保留原候選供連線恢復後明示確認或精確取消，freshness 已變時只能清理。

`ReferenceWorkspace` 的 PF-6 綁定保留 uint64 十進位文字，不能先轉 Number 再比較。
共享 observer 同時處理既有數字回覆和 PF-6 文字回覆，host 各命令分類分別有斷言及撤回。
只有已觀察、native definition revision 不變的純 `canvas-pos` 可以更新 presentation pin；
真正世界變更、session／context 變更仍使候選過期。確認移交租約後的舊 owner 清理是安全空操作，
不清掉新 owner。pending 候選也納入既有開檔／切換／保存限制。

## 片段、來源 pin 與正式採證

兩處既有能力清單守門是具名遷移：原五項 `read, edit-definitions, read-layout,
read-support, create-from-fill-grid` 的內容與順序不變，恰好增加第六項 `suggest-timbers`。
仍以完整有序陣列判斷，未知、缺漏、重複、錯序均拒絕；舊五項不得啟用 PF-6。
UI14 原本禁止 PF-6 入口，現在改為恰一個正式 `data-pf-action="suggest-timbers"` 入口，
草稿／父候選時禁用，PF-4B／PF-5 仍未開放；保留原單一檢查及 assertion count。
這是本片明示的新能力契約，不以換 selector、略過測試或寬鬆集合判斷續綠。
UI14 的 exclusion SHA 由原 encoder 產生並列明前後值；UI13 原六項撤回名稱與殺點保留，
只把 requestId 錨點對齊現在先固定的 originSession。

新增五份 native suite 片段、P1286 strict module 片段與自己的架構 source／exclusion 片段。
不改 dispatcher、shared judge、driver 白名單或歷史大表。`pf6_app_stage.py` 用原架構 encoder
產生作者片段；新 suite 由原 `--init-suite` 產生 pending census，P1286 由原 `stage-module`
產生 candidate。成本、正式 count、ME、AE 都由原工具／workflow 實跑，不由本片填值。

`serve.py` 的新增路由已逐段重審：只新增 bounded PF-6 POST admission、server path 轉換與
受控 terminal；`do_GET`、scenario query 選取、index 路由及 iframe driver 未變。
`htmlEmbedRoutes` 只把這支已重審 router 的精確 LF SHA pin 更新；driver pin、load/reset
次數、receiver、target、query 等限制全保持原值。stage helper 限定 reviewed after SHA，
任一新 router bytes 必須重新審查，不提供 refresh-all。

由套用端先跑五個新 native suite 的正式 census／cost 導入，再跑 Canvas section measurement
量測 P1286；因 `serve.py` 在 P2052 driver identity 內，P2052 也須正式重新量測／導入。
之後完整 native 六片、canvas 兩片、complete coverage、其他 browser gate、ME、AE 及
API 對抗審查全部仍照原守門。候選 0/null／pending 記錄在正式導入前被拒絕是預期，不能續綠。

新的服務層自動裁判由 HTTP suggest → select → confirm → dump，停止舊服務後，
另起新程序及 session 載入原 scene，逐字比對 dump、typed source、派生鍵與 R43。
這不是一般 `.gcanvas` 開檔的 Chrome 驗收。可執行命令、待跑 Chrome 撤回、
另存／新服務新 profile 冷開及唯讀 probe，見
[`tests/diagnostics/pf6_app_browser_plan.md`](../../tests/diagnostics/pf6_app_browser_plan.md)。
診斷撤回收據不冒充正式 mutation ledger。作者環境已跑項目由 issue #128 的原始輸出記錄，
本文件不把未執行的 Chrome、Windows 對話框、實體觸控／IME、輔具或 L5 寫成通過。

## 後續順序與檔案交集

PF-4B 獨立快照應接在 C1 正式套用及核對之後，先定清楚跟隨來源與獨立定義的切換、
刪除／失來源、保存往返及一次歷史，沿既有原生交易與同一表單，不在本片偷偷複製 typed source。

PF-5 空間完成面及樑分層建議接 PF-4B 與工作包 A 的宿主呈現之後；先核對空間面方向、
完成面／結構側、宿主層級及樑影響，完整投影能人讀再接批次操作。本片不實作兩者。

與 A/F 可能交集：`app.js`、`reference-workspace.js`、`index.html`；與共用保存接線交集
`project-store.js`；若其他包改 `serve.py`，須在合流後重新審該來源 pin 與 P2052 成本。
原生 PF-6 bridge 投影、新 Session／Workspace 及 P1286 各有獨立檔案。
下一片等 C1 套用結果與真 Chrome 回報再出。
