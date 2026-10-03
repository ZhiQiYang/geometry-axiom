# #44 F1a 唯讀來源／影響檢查器

整合基線：main `9e252ae`（已合併 PR56、PR63 / geometry-canvas/9、PR64、PR65 支撐與 PR66 靜態來源閉包；原切片基線 693a1c8）。行為依公理 D6–D9、D26–D34、I8/I9/I38–I42；產品願景仍是草案。未改公理；F1b 受控重建另案。

## 原生讀取與能力

`source-inspect` 回傳 `source-inspector/1`、目前 definition revision、最多 2048 nodes / 8192 edges、`complete`、原生逐節點 definition/value SHA256。
`source-inspect-file <server-owned scene>` 只在獨立 World 驗證保存來源，再建立同一索引；保留 live World、history、revision、pending preview/token。HTTP `/sources/snapshot` 接收上限 1 MiB UTF-8，伺服器建立並清理暫存檔；不收使用者提供路徑。

暫存檔建立後，部分寫入、close 與 bridge 例外都經同一 cleanup finally；真實 partial-write／bridge-error 檔案回歸驗證，不留下 snapshot。原版 partial-write 反例有 assertion failure，修正版通過；此修正不改 1 MiB 或 UTF-8／NUL 契約。

索引是可丟棄讀取資料，不保存到專案，不新增格式。UI 只適配及比較原生指紋，不自行求值。沒有模型生成／重建請求，不消耗既有 preview token。

`live:false` 的保存来源回覆另帶同一 candidate World 的 `timberReferences`，
重用原生 references serializer，供單一已保存模型的明選角材料單派生。
巢狀 `sourceFingerprint` 與索引完全相同，不借 live revision／尺寸／支撐；
live `source-inspect` 與 `references` 輸出保持不變。
計量、模型雜湊領域及匯出 owner 邊界見 [MODEL-SNAPSHOT-SCHEDULE.md](MODEL-SNAPSHOT-SCHEDULE.md)。

## 先驗現況與 typed 邊界

| 現有資料 | 可信來源及此次適配 |
| --- | --- |
| ParameterField.expression | 原生 AST ref，精確 parameterId/fieldId；card 0 / field 0 分開 |
| DimensionSource、override | 原生 kind/id/version/field；inactive 底層來源保留，實際 closure 排除 |
| Guide/Datum | 核心已驗證 D6a quantity grammar；以核心模組解析，不分析錯誤訊息 |
| GridSystem/GridBinding/Grid | 型別定義、signed index、parent、binding、boundary key、ParameterRef |
| 材料／做法／規則 | 固定 id/version，沿用原生發布內容指紋，不能升級到最新版本 |
| AssemblyInstance | instance/member→timber mapping、binding、固定 rule/hash |
| placement/boundary/space/RC | 原生位置、輪廓／孔／fixity、成員與凍結 RC 尺寸 |
| `references.definition.anchor/selector`, engineering `path`, violation `message` | 文字摘要；**不**從這些欄位推測 typed reference |
| model_base.dependencies | 現有幾何 closure，只涵蓋部分 placement/timber、含 I9 候選；不能當成確切支撐圖 |
| saved model input/source | 原有完整 base_scene、明選 placement/uses/obstacles/timbers、生成 settings；未提供 durable incarnation receipt |

`span-candidate` 是 I9 求值候選，與 `position` 引用分開；不當成已確認止端／支撐。不完整 AssemblyBinding 不虛構構件。不從鄰接幾何猜接合；#47 的原生精確端點投影按下述契約適配，證據缺失或非唯一仍未知。

## #47 精確支撐的原子適配

`source-inspect` 與 `source-inspect-file` 在同一個被讀取 World 追加 canonical
`sourceFingerprint` 與既有 `native-timber-supports/1`；saved snapshot 使用 candidate World，
不能借 live World 的指紋、支撐或 owner。沒有額外 JS references 請求，也不改 World。
角材節點附實際 `placed`、`surface`、`lengthAxis` 與 `nativeOwner`，由同一原生 owner helper 讀取。

JS 核對 projection schema、同次來源 fingerprint、unique typed ID（包含 timber/placement 0）、
實際 placed／same-surface facts、原生端面 axis／range／fixity 與局部面／法向格式。
row owner 與支撐 owner 的 instance/member/binding/rule/version 及三個 canonical fingerprints
共八欄，逐項對照獨立 native node facts，并核對現有 typed member／fixed-rule edges。
binding/instance 的 source node definitionFingerprint 使用自訂來源指紋方案；
不得把它與 canonical JSON owner fingerprint 比較。沒有在 JS 求面或解析 selector。

只有驗證過的 `exact` 才產生派生 `confirmed-support` 邊，按起端／末端保存完整 provenance；
原生 raw edges 不可自稱 `confirmed-support`。缺 projection、缺 entry、unknown／nonunique
或原生容量不足而缺 facts 時保持未知；明確矛盾、偽造 owner／型別／來源拒絕顯示。
既有 disclosure 顯示兩端局部面和固定版本，不新增 toolbar／工作區。
`identityContinuity` 與全域 `supportStatus` 保留 unknown，不由個別端點證據聲稱全部已確認。

模型比較仍排除 I9 candidates。`confirmed-support` 是接觸證據，**不遞迴擴張求值 closure**；
但對 roots／既有 closure 中每支角材逐端比較 authoritative endpoint tuple 及 owner provenance。
即使長度／幾何與節點指紋相同，exact source／localFace／固定 owner 改變仍標
`source-definition`。任一端證據缺失則該角材比較不宣稱完整一致；舊／雙方都無投影
沿用 legacy unknown 身分狀態。此策略不聲稱已核對所有間接支撐內容。

讀取前後同时核對 native revision 與 canonical source fingerprint；展開舊路徑／定位前
核對 session context／stamp，過期資料不得重新呈現為當前來源。

## 索引與快照狀態

每次讀取綁定 context 物件、history frame、project revision；讀取前後核對 native revision。取消、late response、換專案、來源持續變動都丟棄舊結果；定位前重新讀取並核对同 revision。

UI 預設最多 48 個關係、6 層；重複 key／環不重複展開，到容量明示不完整。原生容量不足也不給完整宣稱。下游用「修改可能涉及（未試算）」；F1a 不宣稱尺寸已試算會改。

保存模型只比較明選根及 active 求值來源 closure，保留 source-definition 和 effective-value 差異。I9 候選及凍結 RC 的空間歸屬仍可檢視，但不冒充實際求值依賴；原生結果值變動仍被檢出。不用整場景 hash；不相關 spec、名稱／卡片移動不讓模型一律變更。來源缺失標 missing，指紋／typed edge 改變標 changed，能力不足／舊資料／範例標 unknown。

**內容相同也保留 unknown**：現有格式無法證明跨刪除重建及保存重開的物件延續性。呈現「可追溯來源內容一致；物件延續性未知」，不給綠燈。沒有由名稱找回來源，沒有新增第二份永久來源真相。

## single-owner 接線契約

`source-inspector-app.js` 是可獨立 cherry-pick 的接線 adapter，index.html 載入。接既有 `inspectorContent`、`faceInspectorContent`、`smLibraryList`，不新增工作區。MutationObserver 只補按需 disclosure，不重建使用者表單。參數既有 `paramUsage` 使用清單合併為共用來源／影響，原匯出／刪除控制仍保留。

single owner 可將 adapter 的 `SourceInspectorApp.sync()` 移到既有 render hook；介面仍用 `SourceInspector.mount(host,{selection,context,stamp,read,readSnapshot,navigate,record})`。此次沒有競寫 app.js/reference-workspace.js/project-store.js/native common；web_bridge.c 僅 include 與兩條 dispatch，serve.py 僅唯讀路由／WSL 路徑入口。

可定位原生卡片、ParameterField（含 field 0）、面內 timber/grid/guide；linked placement 導到其邊界卡。尚無可靠只讀定位入口的材料、做法、舊規則版本、spec、datum 明示目前無入口，不冒稱已定位。這些 UI 導航增補不阻第一 slice；新公理及 durable lineage／受控重建另列。

## 驗證入口

`tests/test_source_inspector.py` 是真 C bridge，含零號、AST／signed index、來源更新／刪除、固定版本、同值改來源、override、snapshot replay、preview 保全。
`tests/test_source_inspector.js` 含有界 traversal、closure freshness、來源身分差異、late async / project switch / cancel。
`geometry-web/source_inspector_browser_check.js` 在明示隔離服務執行正式 app／native model／完整專案保存重開／390px；檢查晚到真實原生回應、取消、context switch、來源 revision 改變和欄位零定位。

未宣稱實體手機、多點觸控或 OS 選檔已驗證。GitHub Actions 額度已耗盡：使用 exact source 的 cloud 實測與獨立審查，不重跑未變 CI、不付費或改設定。Parent 已明確授權整合 owner 在完整證據及 review 後依序合併 65→66→67；本契約不作部署授權。
