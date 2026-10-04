# 來源子網格規則提案：Q36 / #58（未採納）

**2026-10-04：**使用者已接受六條明寫的來源子規則建議；[精確六條／現行差異／oracle與writer順序](../geometry-guide/IMPLEMENTATION-QUEUE-20261004.md#58-六條採納映射與oracle先準備未改ssotnative)。下方保留原完整proposal歷史；額外allocator/query/工程預算等不整包採納。此文件提交尚未改SSOT/native，下一契約patch依六條逐段diff並獨立review，不以舊「未採納」停止已批准準備。

原始逐條來源查核基線：`ZhiQiYang/geometry-axiom` main `0f3c1a6fdd88bbcce4484a256d45900bd1d92313`，2026-10-03。後續文件基底 `9ebf52a1b6519356e9ff677e55b9cf167c47b70d`；核心及公理在兩基底間未變。工單需求見 [#57](https://github.com/ZhiQiYang/geometry-axiom/issues/57) 至 [#62](https://github.com/ZhiQiYang/geometry-axiom/issues/62)。本提案只有建議與待採納差異；本輪只整理文件／工單，不改公理、產品、服務，不重跑產品測試。行號對應原始查核基底，正式產品接手須再核最新版本。本提案是規格文件，不是已採納契約，且本輪未執行新產品測試。集中[選項與門檻](../geometry-guide/CONTINUATION-DECISIONS-20261003.md#q36)／[工作包](../geometry-guide/CONTINUATION-WORK-PACKAGES-20261003.md#wp58)。

**結論：#58 proposal、API/閉包草案、數值 oracle 與 #62 驗收準備可立即並行；#59–61 的新來源規則產品須先採納 Q36 的精確差異。未提交 grid 草稿保存另外依賴 Q31。** #57 原始授權是規劃／開工單，沒有因此採納全格批次、rule 身分或新保存能力。公理 `:1042` 仍明寫全格批次、by_span、巢狀子格未定案；願景 `geometry-guide/PRODUCT-VISION.md:3–5` 不是實作授權。

## 1. 現況與實際缺口

| 面向 | 已採納／已實作 | #57–62 要求的新增語義 |
|---|---|---|
| 所有權 | D19 手動子格有獨立 gridId、固定父主格、單一 cell、等分數；主／子格共用16容量 | 規則屬 GridSystem；實際子線由來源規則＋套用＋cell 推導，不新增每格 World.grid |
| 範圍 | 手動 cell 必須 `C∩F` 正面積；子線可見段可以零 | 來源規則不依賴面；selector 在某套用的面外仍保留、顯示零段；不得放寬舊手動守門 |
| 編輯 | I23:640 允許手動等分數改變；被用 innerIndex 仍存在就重算、消失才拒絕 | #58/59 提議只要 rule 有引用即禁止改 divisions/selector；這是較嚴的新差異，不是既有手動行為 |
| 引用 | guide `grid:G:axis:index`；角材 `at-line grid G axis index [band]` | systemId/ruleKey/signed cell/innerIndex 與 appliedGridId 的複合型別，不可假造子 gridId |
| 交易 | 所有來源、配置、手動子格、guide、角材已有 candidateWorld 全量重驗＋preview/confirm | 新 rule CRUD、比較、依賴、dump/hash、影響清單都須接入相同閉包，不能只加查詢或 UI |
| 保存 | 現有無限來源、配置、signed cell、keymap 已原生保存；format8 已有組構生成，format9 已被另一已存在功能使用 | 新 rule 能力、正式 DSL 與 gridDraft 附件尚無契約；不可沿用工單舊敘述把8/9當空號 |

精確接點：`公理層.md:250–259,624–643,654–659,718–733,968–975`；`current_geometry.c:1280–1285` 的 GridSystem 只有 id/name/axes/main_along，`:1317–1330` 的子格仍是獨立 ReferenceGrid。`geometry-core/subgrid_commands.inc:30–59` 和 `subgrids.inc:54–103,201–225` 驗手動類型、固定父格、stagger 拒絕、正面積與同 cell 唯一性。不能拿這些現成子格當來源規則的正式資料格式。

## 2. 可直接納入集中決策包的選項

### Q36a：來源規則的範圍與 selectors

- **建議 V1**：GridSystem 擁有具名規則；只接受兩軸均為無相位差的 REPEAT／REPEAT_PANEL，selector 為 `all-cells` 或單一 signed `cell(i,j)`；多條單格規則必須不同 cell。divisions u/v 各1…65，至少一軸>1，以完整 pitch 精確整除。來源與同來源的所有 bindings／applied grids 共用定義。無旋轉、覆寫、遞迴、範圍 selectors、by_span 或自動角材生成。
- **較小替代**：先只採單格 source rule，all-cells 保留待定；可先交來源繼承與引用，但不是 #57 整個 V1 的完成，SR02/11 亦未滿足。
- **維持現行替代**：僅手動子格，不新增來源規則；#59–61 全部新產品保留 blocked。
- 需明確採納：來源規則存在與零可見段合法；來源缺某軸／legacy-finite／任何 stagger 拒絕新增或保留 rule，不把不支持來源自動改型。禁止規則不等於禁止打開這些舊來源。

### Q36b：ruleKey、分配與生命週期

- **建議**：ruleKey 是 source-local **非零 uint32**，與名稱／排序無關；`nextRuleKey` 是下一個未分配 key，0 僅表示耗盡，active key 必須小於非零 next。systemId、appliedGridId 仍沿既有 uint32（**含0**）。刪除最高 key 不倒退高水位；耗盡只能拒絕 create，不能回繞或因改名新建 key。這沿現有 vertexKey 非零＋0耗盡慣例，並非既有 rule API。
- **0合法替代**：若 ruleKey 也要含0，耗盡必須獨立旗標／nullable 或更寬高水位；不能同時用0當有效 key 與耗盡。增加表示與驗收成本，須明選，不從其他 ID 空間推論。
- **草稿建議**：未提交新 rule 先只有 draft UUID、ownerSystemId、捕捉的來源 fingerprint；candidate preview 才選 next key，確認同一候選成功時建立正式 key 並前進高水位。未提交 rule 不可被 guide／timber 作正式引用，preview 或取消不消耗正式 key。這避免 raw draft 被迫改 World。
- **預先保留正式 key 替代**：若要草稿顯示／保存正式 ruleKey，Q31 須定義 project 附件 reservations、跨草稿去重、匯入／切案／移除／undo 清理及 native create/edit 意圖；不能把 `newid` 的只讀查詢當持久保留。此選项會阻擋含 reservations 的 #59 create 和 #60，而不是全專案其他工作。
- **必須補精確 undo 作用域**：现 `World` 是 POD 快照 (`current_geometry.c:3584–3586`)，vertex next_key 在普通交易不可倒退，但 undo 恢復整份 World。直接照抄不能證明「跨 undo 分支永久不重用」。決策包应区分：(A) 沿当前已提交沿革不重用、undo/redo 恢復完整歷史 identity，高水位可随歷史回復；舊 UI/draft refs 必須按 context/revision/fingerprint 失效；(B) 同一來源跨被捨棄 undo 分支也不重用，需要不随幾何 undo 倒退的 allocator 高水位及 reopen 保存契約。**建議先按既有整筆歷史語義限定 A 並明寫邊界；若使用者要 B，另採納 allocation/history 合同，不宣稱已有。** 此处不新增跨專案 durable incarnation。

### Q36c：複合引用與座標／context 分域

建議保存用 discriminated tuple（候選型別，尚非現行 JSON）：

```text
RuleLineRef = {
  kind: "grid-rule-line",
  appliedGridId: uint32,
  systemId: uint32,
  ruleKey: nonzero uint32,
  cellI: signed-int64 decimal string,
  cellJ: signed-int64 decimal string,
  axis: "u" | "v",                 // 座標軸；u線沿v走
  innerIndex: uint32                // 0..divisions[axis]-2；k=innerIndex+1
}
```

- **runtime envelope** 另帶 contextToken／definitionRevision／sourceFingerprint／查詢 target；這些是操作 freshness，**不寫進正式 DSL identity**。完整檔開啟會有新 runtime context，不能要求旧 token 才能重放。兩份專案即使所有數字相同也不接受彼此延遲回覆。
- native 解引用逐項驗 appliedGrid 在同承載面，現在的 binding 確實指向所存 systemId，該 source 的 ruleKey 存在，selector 命中 cell，innerIndex 合法，軸向與 guide/角材一致。換成另一 system 即使同 ruleKey 不得暗接。同 source 經不同 applied grids 放置，是不同有效引用；source rule 不是全域物理線 id。
- system query 沒有 appliedGridId、binding query 亦不一定有已放置主格，回傳的是 **query target 下的 preview line**；不能偽造 placed RuleLineRef。建立正式 guide／timber 時明選實際 applied grid，再由 native 建立／驗證完整 tuple。
- signed cell 用字符串傳輸與保存，不 Number；cell 上界要用 i+1/j+1，故 INT64_MAX 不能做合法 cell lower index。source 是 phase+k·pitch；binding/applied 使用既有 `vertex−fraction·pitch+(k−anchorCell)·pitch` 相對錨點，不先算巨大 i·pitch 再相減。來源合法不代表每個 requested 輸出都在 D1；只對有限實際查詢／保存引用驗幾何域。
- guide 只引用座標，沒有子格 footprint／角色繼承；直接 at-line 才要求寬度帶與整個推導跨度留在父 C，加上真正 D11/R6 支撐。角色 secondary/3 是明寫放置的 UI 預填，不能改已放角材。
- **替代**是展開每格子 gridId，但會碰16容量、取樣身分及來源重綁，且違反 #57 的不展開方向，不建議當本 V1。

### Q36d：使用中更新、衝突與省略欄位

- **建議 source rule V1 嚴格保護**：有正式 guide/角材引用的 rule 禁改 divisions、selector 或刪除；名稱／展示排序可變；pitch/phase／參數／錨點／邊界沿完整 candidate 重算，任一有限依賴失敗全部拒絕。這條要限定新 rule，保留現手動 I23「仍存在索引可重算」行為。
- **替代**：比照手動，只阻止失去索引，允許已用 divisions/selector 改動并重算。要額外決定 selector 是否仍命中原 cell、是否改指另一 rule，以及所有引用差異呈現；不是最窄首版。
- rule/rule：同 source 的 all-cells 與任何其他 rule 相衝突；兩條單格同 cell 相衝突。rule/manual：只看相同 applied parent 的同真實 cell；新增 rule、建 manual、重選 manual、rebind source 都雙向重驗。**拒絕、指名舊物件；不默認 priority／override。** 單格來源規則在某面外仍存在且零段；同位置手動子格仍拒絕 C∩F 無面積。
- **建議兼容操作**：舊 `grid-system` 完整軸宣告省略新 rule 欄位時，保留既有規則與高水位；刪改 rule 必須明示 typed CRUD／專用宣告。新 owner 的舊式宣告預設無 rule。canonical dump 要輸出完整 rule/highwater，restore 缺閉包不能以「省略保留」偷用舊 World 補齊。
- **替代 fail-closed**：已有 rules 的 owner 用不含 rules 的舊全宣告直接拒絕，并提示用新全宣告。比較安全但舊來源 UI 均须同步改造；不能採「省略就清空」。現 `grid_systems.inc:190–213` 由 `GridSystem s={0}` 全欄覆蓋，兩個 UI writer (`grid-system-workspace.js:420–428`、`grid-inspector.js:164–170`) 都只送舊欄位，這是新增能力必防的具體整合破口，**不是現在已有規則被丟掉的產品 bug**。

### Q36e：交易與工程預算

- 來源 rule 與上游尺寸／binding／boundary 更新均走同一 candidate：參數 → source rules 合法性 → 全 bindings/applied grids → rules與manual衝突 → finite saved guide/角材引用及支撐 → 全 World 檢查。來源無面或無任何引用也須驗等分整除和 rule overlap，不按「只查可見線」漏掉非法定義。
- 預覽列來源及所有受影響配置／已保存引用；無限 all-cells 不列無窮個衍生實例。保存 closure 的 fingerprint 必須包含 rules/highwater。現 definitions equality (`current_geometry.c:3781–3787`) 是跳過 canvas metadata 的整 World memcmp：新正式欄位放在 World 定義區即自動涵蓋，仍須測真 stale confirm；若 allocator／附件放在 World 外則不能假定已涵蓋。UI seq/context/owner 與 native token+revision+before World 都要守。
- **建議不用使用者選工程常數**：32 rules/source、1024 cells/query、4096 segments/query 只是工單起始測量點。先測 World/Preview/history 的容量与堆疊、64MiB+ASan、查詢耗時／JSON bytes，再鎖正式常數；16 systems/32 bindings/16 main+manual grids/64內線及其他World限制不跟著膨脹。新規則不是 child-grid slots。
- exact 超限回 `requiredCells`／`requiredSegments` 和明確 query capacity error，只拒絕查詢、不使來源非法、不改World或pending token；sample 明示不完整、真 cell索引及stride，選中一格的 exact/hit 不能沿 sampled 顯示格猜。count arithmetic 必須先溢位檢查，不能先枚舉再截斷。4096總格只是現 UI 下拉列舉切換門檻，不是來源合法性上限。
- 必測容量边界1／limit／limit+1、>4096個實際格但 World.grid count 不增、holes使同線多段、query失敗與新pending保留、signed extreme與輸出D1拒絕。

### Q36f：保存能力與 Q31 依賴

- **建議独立能力名稱** `grid-subdivision-rules/1`（草案名称，不是已支援）；正式 source DSL 包含 owner/rules/key/highwater、selector/divisions，導出的 coords/segments/取樣不保存。正式 guide/角材保存完整 RuleLineRef。未使用的 source rule 也保存，不能只遍歷被用線。
- capability 要由实际 rule/ref syntax 推導，不能只認 `requires` marker。manifest缺必要能力、adapter不支持、閉包缺 source/key、非法索引、容量超限或降版，一律在替換舊 World 之前拒絕；stripped marker 負例不能静默降為純坐標。
- **版本選項**：新 gcanvas 版本承載 rule capability＋Q31附件，或維持现 envelope 但以明确 capability 擴充。若有新 gridDraft top-level，嚴格 manifest key whitelist 本來就不接受，需要採納 schema/版本變化。不要現在填死版本號；現 format8/9 均已有用途。單用新能力但不含新附件的 canonical scene slice可獨立規格化，不能宣稱 raw gridDraft 已能保存。
- Q31 明定 gridDraft schema、source/binding/rule owner、新建draft UUID／分配選项、pinned base fingerprint、raw invalid inputs、选cell/changeflag与project flush；只有經使用者採納才加入 project-store/ReferenceWorkspace。旧工程／組構 drafts 並非 generic 未提交 grid 附件。
- 保存預覽不是保存批准；重開 pending draft 不自動確認、不能還原已失效 native token。导出純 scene 缺草稿时明确提示，`.gcanvas` 開新context後原生重放正式 closure並將草稿保留未提交狀態。
- model_base/modeling 實際可支持該能力才加入名单；否則應清楚 `UNSUPPORTED CAPABILITY`、不改現場世界。只改 axiom SHA／允許list不等於實作 parser/引用/來源契約。`.gcanvas` 支持而某建模profile不支持可以有界並存，不能宣稱該模型能力完整。

## 3. 逐項最小 slice、依賴、驗收與落點

| 工作包 | 最小可交付／验收 | 落點與依賴 | 可並行 ready 門檻 |
|---|---|---|---|
| #57 / WP57 總包 | 維護上述支援／不支援矩陣、單一integrator及freeze SHA；分項証據，不提前Closes | 總工單和集中文件；不碰其他產品owner | **现在 ready：只文件**。產品完成等各slice集成及owner驗收 |
| #58 / WP58 proposal | Q36a–f每个選項，逐條映射 D9/D19/D29、D6a/I13/R6、I8/I23/I25/I37/R32，typedAPI/DSL/query/errors/閉包；数值正反例 | 建議新增 `geometry-core/GRID-SUBDIVISION-RULES-PROPOSAL.md`，contract 僅先作未採納草案；Q31 gridDraft 定界；此轮不改 SSOT/reader | **现在 ready：文件＋oracle準備**；用户逐条採納後才同步正典与契約 |
| #59-A source CRUD + readonlyquery | 無套用 source 已可新增／讀／改／刪規則；精確cell/query、selector overlap、pitch整除、key/highwater保存；query不改live/history/pending | `GridSystem`/World/current_geometry.c、`grid_systems.inc`/`grid_lattice.inc`；`grid_system_bridge.inc`/`grid_binding_bridge.inc`；採納Q36a/b/e/f | Q36採納＋正式类型/token/limits冻结；native owner独写核心共享檔。不能只在 JS 補 rules |
| #59-B bindings/manual/typedrefs/atomic | 一來源兩配置、全部applied grids继承；bidirectionalmanualconflict；guide座標与direct完整cell+支撐；使用中身份保护、所有合法/非法候選 | `grid_bindings.inc`、`subgrids.inc`/`subgrid_world.inc`、`references.inc`/anchors、`transactions.inc`、`reference_bridge.inc`；依#59-A與Q36c/d | 契約和 native A API stable後開B；JS作者可依fixture準備但不得mock取代productionnative證据 |
| #60-A native scene／gcanvas正式閉包 | 未使用rules＋两bindings＋两个引用native dump/load新context相同；stripcapability/missingrule/wrongSystem/failedload oldWorld/history/pending不变 | native dump/parser/definitions_equal/hash；`project-store.js` capabilities/whitelist；`engineering_bridge.inc` preflight；`model_base.c`＋`modeling/common.py,base.py`实际support/refuse | spec可現在並行；產品等Q36f採納及native闭包fixture。無Q31可只交A并註草稿未做 |
| #60-B 未提交 gridDraft | source/binding/rule三種rawinvalidinput跨blur/close/save/reopen，newdraftUUID/owner/source pin、late切案拒絕、一笔confirm一笔World+附件history | `project-store.js`、`reference-workspace.js`、sourceworkspace；**Q31必要**，預先ruleKey預留另依Q36b | Q31採納＋history/attachmentowner決定后，不能用旧engineeringDraft硬套 |
| #61-A source rule UI | 既有來源workspace內新增細分模式，顯示source共用/單cell/allcell；合併manual/source divisions表單与重複常駐說明；stagger/finite缺軸既有source可看但原因明示 | `grid-system-workspace.js`、`grid-inspector.js`、`app.js` manual form與native query；WorkspaceShell；依Q36與#59API | 現在可紙面/DOM草案與縮減列表；產品等native read/query/CRUD穩定。共享app.js由單一integrationowner |
| #61-B 真placedref／互動保存 | blank→source/rule→兩binding→apply→真childhit→guide/timber→sourcechange兩處preview→cancel/confirm→save/reopen；負索引、sample、holes、390px／keyboard | #59-B＋#60正式保存；rawdraft體驗等#60-B；只使用native line tuples，不自行solver | typedfixture、capability、error與snapshotfrozen後實作；没有新常駐管理器／自动放材 |
| #62 / WP62驗收 | SR01–24拆 native数值/atomic，project負例，Node生命周期，正式無filterCDP；samefinalSHA/binary/served version、有意义mutant红 | newnative suite/Node/CDP plugin与正式index/counts；独立oracle；SSOT reader三檢只在採納後 | **現在 ready：期待值與負例設計**；真產品驗收等契約實作。SR24實機另列不阻礙cloud、不冒充pass |

## 4. 必留 oracle 与最小反例

1. source REPEAT兩軸phase0、pitch600×400、divisions3×2：cell(0,0)内部U=200/400、V=200；改U900后U=300/600。source cell(-2,1)原U內線=-1000/-800、V=600。用binding cell(-2,1)左上對vertex(100,200)後該格U內線=300/500、V=400；source pitch900後=400/700、V=400。驗真相對錨點與兩處套用，不把源座標照抄到配置。
2. repeat-panel panel915 gap2的pitch917，divisions7間距131；不可用panel915/7、更不可舍入。600/7、1×1、66、fraction或missingaxis/stagger拒絕時，old definitions/references/fingerprint/history不變。**readonly query/validate** 保留既有pending；**explicit impact preview** 依現 transactions.inc:585–590 會以請求的候選／invalid token 替換舊preview，不能仍呈現舊成功候選；不可把兩種操作的原子邊界混寫。
3. 兩系統 S0/S1 各有ruleKey1；G0從S0 rebind至S1時旧ref仍写S0，必须拒絕；同source兩appliedgrid同cell不能共享oneplacedidentity。rename/reorder不改key；delete/recreate、exhaustion、create/edit意圖与undo分支依Q36b採納的唯一边界驗。
4. 同parent cell已有manual，再加single-rule/all-rule拒絕；rule已有再create/reselectmanual拒絕；同来源未套用的一条rule在面外零段仍存在，而新manual面外仍拒絕正面積。縮小F導致某可見段零不等於line不存在；真正角材失效必须全來源回滾。
5. 一來源兩bindings，其中仅第二個实际角材失去合法支撐；sourcepreview必须整筆invalid，不能只驗當前工作面。正向两者都合法時show兩處差異、一confirm、完整undo/redo。
6. guide引用子線但角材沿guide放置，維持guide座標語義；direct at-line同尺寸必须额外cellfootprint限制。兩種正負例有真實支撐，以免測試被無關I13/R6先擋而假綠。
7. 新能力marker被移除、manifest被降版或缺 capability、rule/highwater缺失、missingowner／wrongsource／>2^53數字被Number污染：opening前拒絕且舊World/附件/UI selection/history/pending完整不變；規則不被丟掉、旧finite/manual/no-rule場景不被轉型。
8. mutators跳過整除、丟rulekey/highwater、忽略systemId、只驗第一binding、sample當真cell、漏holeclip、marker stripping及staleconfirm须以**預期assertion失败**检出。unknowncommand/compilefail并非有效红基线。

## 5. 必須列入實作閉包的非顯眼接點

- `geometry-core/grid_systems.inc:190–213` 全宣告覆蓋與`:259–281` dump；加欄位並不能解決所有writer遗漏。`geometry-web/grid_system_bridge.inc:30–65` objects只读source定义、preview`:68–86`都要真实rules/highwater。
- `geometry-core/references.inc:106–140` 的guide quantity parser仅5parts且只认识旧grid四段token，必须新增typed分支及依賴解析，保留old語義；`:329–340` directanchor涉及cellscope，不能只換返回coordinate；现候选引用`:750`亦只有旧token。
- `geometry-core/transactions.inc:71–77,98–110,409–446` 的source比较、geometry_changed、may_affect是专有字段／command列表；新增rule若漏此处可能没有影响preview或定义变动检测。`:542–554` token＋revision＋definitions_equal守门须包含rule定义，但查詢不得破坏该pending。
- `current_geometry.c:8579–8611` 全重驗順序已適合复用；不能把sourcequery当全World合法性证明。`:3781` definitions_equal与`geometry-web/engineering_bridge.inc:6–23` canonicalfp/requiredcaps需新闭包，而displaycanvas位置仍不纳入geometryfp。
- `grid-system-workspace.js:43,441–455` 和`grid-inspector.js:7,154–170` sourceKey目前不含rules；新增readonly字段后必须更新捕捉/对比或使用native sourcefp，否则只有rule变了旧UI也以为同source。newentry/latequery/重复retry不得repin成新的source silently。
- `project-store.js:8–15,76–90,178–210,354–356` formats/capability数量4/白名单/manifest严格key；`reference-workspace.js:300–335`仅现engineering/assemblydraft APIs。Q31需要正式gridDraft接口，不能claimgeneric附件已存在。
- `geometry-core/engineering_commands.inc:166–168` C requires名单；`model_base.c:342–345`仅宣告engineer/parameter；`modeling/common.py:11–34`语法推导、`base.py:63–70`能力preflight、1MiB限制；`serve.py:42` validate-project同1MiB、当前scene line16384/tokens640。查询/导出/新规则payload预算须分别测，不能把.gcanvas128MiB、bridge1MiB或32rules上限互相替代。
- 旧支持回归：`tests/test_subgrid_contract.py`现有 exactdivision／hole／guide scope／capacity16／support正例／preview stale／scene/history；`tests/test_infinite_grid_contract.py`源/binding/large signed query。新增SR应复用合法native夹具并增加source-rule专属裁判，不能以旧手动suite通过就宣称 #59–61 完成。

现在沒有需要採納新公理才能繼續的文件工作阻塞；本次唯一產品 gate 是 Q36，包含 raw gridDraft 的子slice另受 Q31阻擋。预算数字由工程实測，真iOS/OS SR24单独保留未驗。本报告不触碰 #47双向定位、已合併PR73 undo/redo及PR74 PDF snap產品流。


## 6. 介面／語法候選（未採納，現不能呼叫）

正式native owner採納前凍結命名；以下是可審查候選，不是目前已有commands：

建立／編輯／刪除沿既有ReferencePreview與批次候選交易管線，不新增獨立token、history或geometry solver；新操作只擴充正式typed輸入／差異契約。

- read：sourceID → rules/highwater/native source fingerprint；無修改或pending token消耗。
- create/edit/delete：`grid-subdivision-rule-transaction/1 {expectedRevision,sourcePin,operations}`，create有systemId/draftId/name/selector/divisions，edit有systemId/ruleKey及預期定義，delete有systemId/ruleKey；preview回proposedKey/前後差異/typedviolations，confirm同token/revision才正式提交，cancel不消耗key。
- readonlyquery：沿現`grid-query system|binding|grid`明寫target、rule、rect/cell、exact/sample/limit，返回真signedcell及線seg；system/binding無appliedgrid只previewline，不能產生假placedref。
- canonical scene候選：`grid-source-rule SID key K name-hex HEX selector all|cell I J divide U V`及`grid-source-rule-highwater SID next K|exhausted`；正式tuple引用候選分支`rule-line G SID K I J axis INDEX`，不冒用旧`grid:G:axis:index`。這些token只供diff/fixture規格審查；serializer/parser/required-capability推導必須同一owner確認，正式版本不得兩套可獨立改的rules宣告。
- typeddiagnostic候選enum：DIVISION_NOT_EXACT/RULE_OVERLAP/MANUAL_CONFLICT/RULE_REFERENCED/WRONG_SOURCE/INDEX_RANGE/QUERY_CAPACITY，相關fieldPath/systemId/ruleKey/cell/referrers一併回覆；現有message不能冒充這些已存在。

使用者採納需包含D9/D19/D29、D6a/I13/R6、I8/I23/I25/I37/R32與末節全格批次限制的精確diff，不藉本PR把以上語法當成已實作。Q31 raw草稿附件與Q36正式rule能力各自保留gate。
