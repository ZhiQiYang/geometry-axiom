# #47 單一保存模型的角材快照料單

這個切片沿用 D1/D12、既有模型保存與原生角材料單契約，不修改公理或保存格式。
計量對象是一個已保存、通過既有模型驗證的紀錄內明選 `input.timbers`。
每個 typed timber ID 在該保存來源 World 中只計一次；兩個相同尺寸但不同 typed 根的角材仍是兩件。
不加入來源場景裡未明選的角材，不把現行 World 或另一個模型的表示相加。

## 原生資料與雜湊領域

既有 `/sources/snapshot` 在獨立 candidate World 驗證保存的 `input.base_scene`。
`source-inspect-file` 的 `live:false` 回覆追加 `timberReferences`，與外層索引來自同一個
World、同一個 canonical `sourceFingerprint`，並帶該 World 的原生截面、完成長度、
朝向、放置、定位、工程來源、精確支撐與組構 provenance。沒有第二次 live references 請求。

`json_references_world` 只重用既有原生 serializer；live `references` 回覆與換行保持不變。
巢狀 references 沒有借來的 live revision；外層讀取 revision 只用於前後 live 讀取守門。
暫存檔、UTF-8/NUL/1 MiB 拒絕、history 與 pending preview/token 保全沿用原契約。

模型 `source.scene_hash`／`result.source_sha256` 的 canonical scene、套件
`manifest.source_sha256` 的 canonical definitions JSON，以及 native World 的
`sourceFingerprint` 是不同領域。合法 `input.base_scene` 可保留註解而 canonical scene
不保留；不能要求 raw input bytes 的 SHA 與上述任一值相等。
先走既有 `GeometryProject.validateSpaceModel`，再核對同次 native snapshot 資料。
有角材的模型另以同一條唯讀 snapshot 路由檢查已保存套件的
`result.timbers.definitions.base_scene`；它與 input candidate 的 **native World**
fingerprint 必須相等。套件 canonical scene 的原字節 SHA 另外只與既有
`result.source_sha256` 比較；不跨上述領域。這避免輸入場景被換成 29 mm，
卻仍掛著 27 mm 的已生成模型。live 前後讀取包住兩個 candidate，沒有新的 parser／route。

## 派生與計量邊界

前端只把 typed 明選根按原生 surface 分組，交給既有、含支撐核對的
`TimberSchedule.derive`；不從 mesh、selector 字串、圖像或座標猜尺寸／端面。
零號 timber 與 placement 合法，重複、缺失、未放置、非精確或錯型根全部拒絕，不能補零。
既有 plan 模型的每支角材必須屬於保存的 `input.placement_id`。
工程尺寸來源核對同次 native typed edge 的對象、active／override 與 effective 值，
缺失、重複或不同欄位不能退化成直接尺寸；不解析 selector／path 或錯誤文字。
每列保留原生 A/B/L、dir/side、surface、來源與支撐；未知材料、加工及身分延續仍明示未知。

模型紀錄 UUID、範本、名稱、尺寸和整個 World fingerprint 都不能證明實物是否相同。
這個切片不新增跨模型／現行與快照的彙總，因此不需要假造實物去重鍵。
普通角材同 ID 刪除重建且內容相同，原生 dump/hash 可以完全相同；身分延續性仍 unknown。

保存模型引擎目前不接受 assembly-owned 場景：既有 modeling capability／definition
whitelist 明確拒絕。原生 snapshot 的 owned projection 可以独立核對，但不能製造
已保存 owned 模型正例或剝除能力／provenance 通過模型驗證；此限制另列缺口。
現有 `faces` 模型 producer 也拒絕 `timbers` 設定；不假造跨承載面保存模型正例。
合法 plan 模型中，同面兩個不同原點的明選角材可由真 producer 建立，仍逐件保留。

## 既有模型庫接線與匯出

在既有模型卡片的來源 disclosure 顯示「保存快照料單」、模型版本與來源狀態。
有明選角材時，一對一把原「重新檢查」替換為「核對並匯出快照 CSV」；其餘來源檢查入口維持。
不新增工具列、獨立工作區、保存附件或第二份可編輯幾何。

表格永遠讀保存 candidate，不隨現行角材變動或刪除偷換為 live 尺寸。
freshness 可顯示內容一致但身分未知、changed、missing 或 unknown；歷史快照與現行狀態分開。
快照列不能把同 ID 的現行新角材當成保存模型構件導航。

匯出重新核對 live→snapshot→live 與同一模型 owner，使用同次 candidate 的同一列集合。
專案 context、history frame、project revision、紀錄替換／移除、關閉、取消及遲到回覆
失效時不得建立 CSV Blob。連點只執行一筆匯出。CSV 帶模型／快照來源、版本、
精確 mm 與身分未知，沿用現有 quoting、CRLF/BOM 及公式字串防護。
檢查、呈現與匯出不修改 World、dirty、history 或已保存模型。

## 驗證與剩餘

真 native 測試核對 candidate 的尺寸／原點／零號多放置、typed parameter field0、
owned 支撐 provenance，以及成功／失敗讀取的 live World、history、pending token 保全。
baseline 新案例與 wrong-World 變異必須是 assertion-red，不能拿編譯或崩潰失敗充數。
前端另驗合法模型與不同雜湊領域、明選根、CSV 安全及 owner 時序；正式瀏覽器操作、
完整 suites、golden 與 exact head 結果在交付 PR 回填，未跑完不宣稱全綠。

跨表示實物計量／durable incarnation、assembly-owned 保存模型能力、此有限切片外的
雙向定位、F4b 加工／裁切／餘料，以及 A24 實體手機／OS 操作仍需獨立處理。

2026-10-04 使用者恢復 #47 的有限雙向定位：已驗證 ordinary plan 的 `input.timbers`
與同一保存 record 的唯一完整 `result.timbers.derived.objects[].root` 對照。
readonly 3D 原有 ID／世界 z 重複列併為快照料單；點列高亮並置中該 mesh，沿用
角材顯示／材料牆開關（定位時顯示角材、隱藏材料牆），點 3D 角材回選同列。
命中使用呈現中的實際三角形；不穿過不透明牆，半透明空間邊界作檢視輔助。
拖曳、平移、pinch 與取消不算點選。所有操作只改選取與 camera，沒有幾何回寫。
對照只在 native snapshot 與保存套件雙端核對後啟用；同一 context object、唯一
record 的 exact bytes、可見 workspace／disclosure 與 read session 持續守門。
模型替換、移除、切專案／模型、關閉或遲到回覆撤銷舊授權；重開需重新核對。
typed root 保留 uint32（含 0），不以 live ID、label、尺寸、component 或 array index
認物件；沒有新公理、保存 schema、route 或 F1b。

正式 CDP 的 P83 使用既有真 producer、兩支明選零號／多原點角材及獨立未選根，
真正下載 CSV 逐位元組核對 Blob（含 UTF-8 BOM），每次下載目錄隔離以容納同名覆寫。
負例只延遲真正 native 回覆，保留來源／專案／紀錄替換移除／關閉重開／改選／連點的
零 Blob 或單次 Blob 斷言；新專案視窗必須精確匹配既有確認訊息。P83 為 16 項，
原 1839 個 Chromium 斷言不減少；正式全量須不設 scope 或 update-golden。
