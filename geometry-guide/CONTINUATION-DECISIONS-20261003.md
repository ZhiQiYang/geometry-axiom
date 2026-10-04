# 可接續工作包的集中決策包

**2026-10-04 採納更新：**八項明寫建議已获批准；[精確範圍／額外未採納細節／單writer接口與隊列](IMPLEMENTATION-QUEUE-20261004.md)為目前入口。下方是2026-10-03完整proposal歷史，不能整包視為採納，也不能把已批准範圍繼續當待決而停止。

初始事實基線 `0f3c1a6fdd88bbcce4484a256d45900bd1d92313`；後續文件基底 `9ebf52a1b6519356e9ff677e55b9cf167c47b70d`。PR73/74/75於20:01:23 UTC被外部合併，PR75只含第一批索引；**合併文件不等於採納Q31–Q36**。使用者19:47只授權規格／依賴／文件及工單準備，以下全部是待選定proposal，不改SSOT或已採納契約。

對應[13項工作包（原12＋WP77）](CONTINUATION-WORK-PACKAGES-20261003.md)、[決策佇列](../決策佇列.md)和[#58逐條公理／API／相容提案](../geometry-core/GRID-SUBDIVISION-RULES-PROPOSAL.md)。#47雙向定位已取消，不重啟；既有D34/I42/R35三構件生成已採納，不重新批准現行行為。

## 選項、建議與阻擋範圍總表

|決策|建議（全部待採納）|需選的具體差異|阻擋／不阻擋|
|---|---|---|---|
|[Q31](#q31)|typed可攜grid草稿；raw空值／非法值不當成World|持久附件或session-only；一個active草稿或多份|阻WP45-B/60-B；不阻45-A現有配置規格|
|[Q32](#q32)|明選重新關聯來源、identity仍unknown；同model原子更新一筆undo|manual或durable沿革；同model更新或新副本|阻F1b；不阻F1a；不開#47|
|[Q33](#q33)|有界完整A/B快照與資產pool；採用另切|完整snapshot或incremental；未保存工具草稿處置|阻46新保存／採用；不需F1b全完成|
|[Q34](#q34)|project-contained EvidenceLink、原頁rect與轉錄核對|可攜或session-only；人工重關聯或durablereceipt|阻48新附件；不阻PDFsnap既有hotfix|
|[Q35](#q35)|有限typedpredicates、每run新nativeprocess、結果版本化|隔離方式；歷史receipt保存／freshness重驗|阻49產品；case/oracle規格可並行|
|[Q36](#q36)|一層all-cells／signedcell來源rule、完整typedref及全來源交易|a–f六項來源／引用／生命週期／相容差異|阻59–61；58proposal/62驗收稿ready|
|[Q37](#q37)|來源附件共享校準／對位＋native邊界集合，不暗改舊房geometry|共享定義或當次複製；新增/替換/更新及保存身份政策|阻WP77產品；資料與雙房fixture規格ready|

「ready」均先指文件／fixture規格可接續，不代表本輪已授權產品碼。工程容量、TEMP路徑及工具版本由工程實測固定，不需使用者逐項投票。新capability/schema可先提候選，**不先占下一個format號**；/8生成與/9輪廓收據均已有用途。共享術語不建立未採納萬用身分層來阻擋所有唯讀規格。

<a id="q31"></a>
## Q31 — 未提交grid來源／配置／rule草稿

**A（建議，待採納）**：可攜typed附件，首版每project至多一個active source/binding/rule editor草稿；多份另切。**B**：維持session-only，save時先確認／放棄，不承諾跨重開rawform。現有grid離開可discard、pending會saveBlocked；projectmanifest沒有gridDraft，engineering/assembly不是generic附件。

候選欄位，非正式API：
```text
GridDraft {draftId:UUID,kind:source|binding|source-rule,intent:create|edit,
 baseRef:null|{kind,id,nativeDefinitionPin},
 inputRefs:{system:null|typedPublishedRef,boundary:null|typedPublishedRef},
 rawForm:finiteAllowlistedStringsAndSelectors, view:optionalPresentation}
```
新source先正式确认才让binding/rule引用；首版不允许互相引用未提交draft。draftUUID不是正式grid/ruleKey。raw「1/0」／空軸／未選vertex可保存，但不改World／不假填0／不自動confirm。input change記owner草稿，save/leave/切案同步flush；確認中的busy操作等待已送請求／receipt，不重送mutation。重開source missing/changed保持stale，需明選處理；expiredpreviewtoken不恢復。

Q36 rule先draftUUID，candidatepreview才取formalkey，confirm成功前不消耗；預先reservation若選則另採跨草稿/匯入/切案/undo策略。metadata draft history與正式confirm只由單一ContextHistory owner協調，不能靠blur保存最後輸入。

**驗收／門檻**：rawinvalid重開原樣、World不變；unknowncap/schema/閉包缺source原project保留；lateflush不串案；取消leave保留草稿；confirm一物件一history不撞號。A阻45-B/60-B直至新附件採納；B使這兩功能維持未交付，不阻現行配置規格。

<a id="q32"></a>
## Q32 — F1b來源重建與模型處置

現F1a只核內容，identitycontinuity未知；「改牆高」用舊來源不是live重建。ordinaryplan支持工程/參數来源，owned/faces+timbers producer不支持要明示。

|軸|A|B|建議（待採納）|
|---|---|---|---|
|來源沿革|每次明選typed現行carrier/root；equalcontent仍unknown|native create/delete/undo/load/import全生命週期durableincarnationreceipt|先A；B是另大契約|
|模型處置|新model副本，保留舊model|同modelID原子替換source/input/result，舊完整record一步undo|B符合受控更新；A若採則名「另存新模型」|
|輸入範圍|普通單一plan，整份candidate來源＋原settings/明選已有supported欄位|任意partialpatch、多carrier/owned/faces+timbers|先A，B不列ready|

候選暫態intent為`modelId/recordSignature/context/historyFrame/projectRevision/chosenRoot/oldInput/candidateInput/allowedUpdatedFields/resultPackages/nativeRuntimePins/generation`。不往strict現有model record偷塞audit/incarnation。root/timbers/uses/obstacles或oldedgeindex與新輪廓不能可靠對齊時要求重新明選或拒絕；不按sameid／名稱猜接。source/raw/canonical/package/nativeWorld/per-nodefingerprints各驗領域。

隔離producer真候選→typed旧新input/source/settings及所有包差異→明確confirm才替換或建立完整record；取消／失敗／latecontext／model刪除或同IDrecord替換零更新。舊27/live29兩值保持；undo完整舊record；candidate不改live或消耗原assemblypreviewtoken；save/freshcontext真producer重驗。無reliablebinary/unsupportedcap不green，receiptlost沿既有不重送mutation。

**阻擋**：Q32只阻F1b更新契約；F1a缺少來源入口的typedlocator矩陣可獨立準備；取消#47料單—模型雙向導航不列入。若需要persistentaudit或Bdurableledger，另審新附件／能力，而不是因選模型更新一併採納。

<a id="q33"></a>
## Q33 — A/B快照閉包與整體採用

**A（建議，待採納）**：有界完整snapshot＋content-addressed原圖資產pool，scenario獨立namespace。**B**：incrementaleditlog/逐物件merge，首版不建議。

```text
Scenario {scenarioId,label,basis:null|{scenarioId,snapshotHash},
 snapshot:{projectManifest,worldScene,assetHashes},
 originMapping:explicitTypedCopyOriginPairs,closureHash,requiredCapabilities}
```
閉包包含正式scene、現已支持engineering/assemblydrafts、models/input/source/result、faceProjections、referencepages/reviews、所有引用原assetbytes；外部URI不足以叫portable。grid未提交草稿在Q31採納前必須明確解決，不能丟棄而宣稱完整；Q31採後才列closure。不承諾未採納EvidenceLink/ruleCase已能保存，不攜舊undo堆疊。

先46-A固定A/B保存freshcontext讀回；再B用自有nativeWorld/process/session真編輯、typed比較；最後46-C整體採用，重驗currentA/context/drafts/closure，保留A、一recoverablehistorystep。不能在用戶live /upload反覆切案或污染previewowner。sameid跨scenario分域；copyorigin只是來源複製證據，不是兩份數量同一實物證據；unknown保持unmatched。

**驗收／阻擋**：B改參數／joint不改AWorld/token/history/assets；sameoutline/newjoint和samevalue/newref列差異；缺資產/unknowncap/超量原子拒；staleA採用拒；真正save/reopen/adoptundo閉包一致。Q33阻新保存及採用；方案規格不以F1b或實物去重作前置。

<a id="q34"></a>
## Q34 — 人工EvidenceLink、原頁範圍與核對

**A（建議，待採納）**：完整專案附件；**B**：session-onlyannotation/export，不滿足可攜保存要求。target首版只parameter-field，不能順便開全部kind或模型導航。

```text
EvidenceLink {evidenceId,
 document:{sourceHash,page,coordinateSpace,pageWidth,pageHeight,rotationBasis,cropBasis},
 region:{x,y,width,height},
 target:{projectScope,kind:parameter-field,parameterId,fieldId,definitionPin,incarnation:null},
 observation:{rawText,rawValue:null|exactUserText,unit:null|mm|cm,kind:drawing|measurement,note},
 humanConfirmation:null|{documentHash,targetPin,confirmedAt},
 associationStatus:unchecked|confirmed-content|needs-reassociation}
```
PDF用現有原頁rotation後`getViewport({scale:1})`座標，image原像素，左上Y-down；rect存全原頁，crop/rotation保存標記時不變基準，zoom/viewport/dpr只改呈現。samefilename/page/rect但hash新版本不能沿用confirmation。

**目標沿革** A人工明選重新關聯（建議），B durabletargetreceipt另契約；讀回content相同不證明incarnation，刪重建sameid、missing/changedfield保持unknown/需重關聯。**核對語義** A核對轉錄/關聯（建議），B同時採用模型值（首版不選）：原圖值／現場值／正式幾何值分欄，衝突保存；fractional觀察保留text/rational，若作幾何仍D1/nativepreview。建立證據／勾核對不改World。

舊freepage records維持兼容；在既有「來源紀錄」整合typed evidence與重複建立說明，不刪舊註記，不另建PDFapp。四rotation/crop/zoom/390px同原區；parameter0/field0合法；badrect/page/hash/cap/source拒或需核對；latepage/context不串；trueZIPsave/reopen保留原bytes与衝突觀察。Q34阻48新附件，不阻已合併PDFsnap；真iOS框選/keyboard/OS另未驗。

<a id="q35"></a>
## Q35 — 有限案例、隔離與結果過期

**執行A（建議）**每run新nativeprocess/World和有界TEMP閉包；B重用独立namedWorld增加lease/cleanup契約。不使用用戶live/assemblypreview/reset，不消耗其token。**結果A（建議）**定義保存、歷史receipt可留但freshness按exactdomains重驗；B永久green/只截圖不符合可重現要求。

```text
RuleCase {caseId,label,input:{scene,transaction},sourcePins,requiredCapabilities,
 expect:{outcome:accepted|rejected,diagnostic:null|{code,clause}},assertions:[finiteTypedPredicate]}
CaseReceipt {caseId,definitionHash,status,
 executor:{nativeBinaryHash,validatorVersion,axiomHash,assertionSchemaHash},
 actualOutcome,actualDiagnostics,assertionResults,conditions}
```
finite predicates：recordexists/exacttypedref/completeflag/jointtupleequal/recordpinunchanged/diagnosticexact/rejectionWorldunchanged，僅有限typedkind/id/version/member/joint/field和常量，沒有任意JSONPath/eval/uploadJS/Python/shell。首個可交付集合共6case：合法rule、same-role不同member、修改authoring draft／發布新version時只換一joint另一不變（不覆寫固定published rule）、合法incompletebinding、wrongtypedimensionref、fixedversionimmutable/renameorderindependence。WP49-A先做其中member/joint/wrong-type3case，WP49-B補齊另外3case；25現有有限幾何case可後接，不增拓樸。

現native只有部分`ASSEMBLY_INVALID`/clause/message和timberissues，不能宣稱每failure有typedfieldPath/ref；若精確負例不能由currentcode獨立區分，就標需補typeddiagnosticcontract，不反解析文字或anyerror當pass。author expected與executoractual分欄；status=not-run/missing-capability/blocked/timeout/crashed/failed/passed/stale/unknown-runtime。binary未知不能green；input/source/native/validator/predicates变即stale，label是否影響definitionhash需明寫。

**驗收／阻擋**：freshprocess重現；wrongmember/略過immutableguard的隔離mutant使行為assertred，compilefail不算；missingcap/timeout/crash獨立nonpass；liveWorld/dump/history/dirty/token/project/feedback始終不變；latecase不回填另一project；badpredicate/缺閉包/重複ID/newcapwholeattachment拒；save/reopencase可再跑。Q35阻49產品；fixtures/oraclesready。沿固定rule原validationdisclosure整合案例與零散說明，不加永久globalmanager。

<a id="q36"></a>
## Q36a–f — 來源子規則新增公理／契約

具體逐條映射、完整RuleLineRef資料、CRUD/query／生命週期／相容與數值預期見[#58 proposal](../geometry-core/GRID-SUBDIVISION-RULES-PROPOSAL.md)。正式條號未占，SSOT未改；D1/D2/D11/D15/D17/I19／現manual/finite原義保持。

|子決策|A（建議，待採納）|B／其他選項|阻擋範圍|
|---|---|---|---|
|Q36a所有權／範圍|GridSystem一層rule，all-cells或signedcell；無stagger雙軸REPEAT/REPEAT_PANEL；1…65、非1×1、完整pitch整除；source無面及零visible合法|先single-cell（不完成SR02/11）；或維持manual全部blocked|sourcefamily/59-A/61|
|Q36b身分|source-local非零uint32key，0=耗盡；delete不倒退；draftUUID→candidate選key→confirm消耗；當前沿革不reuse、undo恢復完整World|key含0需額外耗盡表示；預先reservation需Q31；跨discardedundo分支永不reuse需undo外allocator/reopen新契約|create/edit/key/highwater、60保存／草稿|
|Q36c引用|正式tuple=appliedGrid/system/key/signedcell/axis/innerIndex；runtimecontext/revision另envelope；guide僅coord，directat-line完整footprint+真支撐|每cell展開gridId不建議，碰16容量/取樣identity|59-B typedref/60閉包/61placed操作|
|Q36d更新／衝突|**只新source-rule**有ref鎖divisions/selector/delete；all/single/manual雙向衝突拒；舊source宣告省略rules保留既有|比manualI23仍存在index可重算需更大ref差異契約；已有rule舊無rules宣告fail-closed；省略清空不選|sourceupdate、全部writer、依賴交易|
|Q36e查詢／交易|sourcewidecandidate驗所有bindings/已用guide/timber；exact有界count/sample明不完整、真正cell；readonly保pending，explicitimpactpreview更新candidate|只驗目前面／JS求值／取樣序號當真索引不符合需求|59全交易/61preview/62負例|
|Q36f能力／保存|獨立候選capability grid-subdivision-rules/1、完整rule/key/highwater/ref；採新projectschema統一新增附件，正式version待協調|純scenecapabilities slice可先規格化但不宣稱rawdraft可保存；Q31draft另gate|60/producerpreflight/59dump/parser|

**易誤認的現行與提案差異**：I23手動子格允許仍存在innerIndex的等分變更，新rule鎖定不可套舊manual；現vertexnextkey普通交易不退，但Worldundo恢復，不是跨undo分支永久不reuse。system/bindingquery沒appliedgrid只能previewline，不偽造placedref。nativeWorlddefinitions_equal是整Worldmemcmp，新增正式World欄位會入其範圍，仍需canonicaldump/hash/專有source比較/影響檢查和World外allocator契約。

工程預算初測32rule/source、1024cells/query、4096segments/query不是公理常數或已支持；existing16systems/32bindings/16main+manual/64內線不放寬。先測source/World/history/Preview/ASanstack、countoverflow、time/bytes、scene-line與1MiBbridge/project各限制，固定診斷。unknowncap/markerstrip/降版/缺source/key在改World前拒；modelprofile未支持繼續UNSUPPORTED，不能只換hash/allowlist。

**數值oracle（未跑產品）**：600×400U3/V2→U200/400,V200；改U900→U300/600；panel915+gap2/U7用917、間距131；sourcecell(-2,1)→U−1000/−800,V600，binding左上vertex100,200→U300/500,V400；600/7、stagger、同sourceoverlap、only第二面失支撐整筆拒。另有bigint>2^53decimal／L形孔／面外零visible／manual雙向冲突／wrongSystemsamekey／capability負例，見proposal逐項matrix。

<a id="q37"></a>
## Q37 — 共用PDF來源平面與多房間集合（#77）

使用者20:19授權加入工作排程／建單，**未採納native父子／共享校準新契約**。Boundary/PlacementSurface/Space/ReferencePage各是不同層；sourcebytes共用不能冒稱calibration共用。

|選項|模型與更新語義|代價／阻擋|建議|
|---|---|---|---|
|A|project附件SourcePlane保存唯一來源頁/calibration/對位；RoomCollection列nativeboundary引用；共享basis變更只標已建room需複核，新描用新basis|新附件/能力、來源owner/typedrefs/歷史/legacy兼容待採納；不新增native幾何父子|建議最小V1|
|B|建立下一房時複製已知校準／對位到各ReferencePage，之後每頁獨立|较小UI，但非真正shared，日後改一頁不影響另一；不能宣稱需求全完成|若A暫緩可明名「沿用當次基準」|
|C|native房間樹、parentframe自動transform繼承／整組移動|D3/D4/D5與依賴/身份/undo新增語義，須逐條公理diff|不列本V1ready|

A的候選定義：
```text
SourcePlane {planeId,sourceHash,page,coordinateSpace,pageSize,
 calibration,alignment, basisRevision}
RoomCollection {collectionId,planeId,roomIds}
RoomRecord {roomId,name,boundaryRef:{kind:'boundary',id,associationPin},
 optionalPlacementRef:null|{kind:'placement',id,boundaryId,associationPin},
 sourcePlaneId,acceptedBasisRevision,reviewState}
```
沒有第二份roompolygon/vertex/frame/volume，亦不把Space ID拿來表示PDFparent。SourcePlane的calibration/alignment是原頁→共同來源工作UV的唯一描圖／呈現基準，不是nativePlacementSurface.frame。新房間唯一outline照D1/現nativepreview確認；已有房間因sharedbasis改變不自動縮放/平移/旋轉。若要批次更新既有geometry，另明選nativepreview/完整差異並另審擴充，不因調PDF對位順帶改。

純Boundary room的optionalPlacementRef可null；存在時以native最終定義核對placement引用的boundaryId等於本room boundaryRef.id。缺失／pin失效保留需重新關聯狀態，不能fallback第一個同boundary placement；編輯／定位走QR3的顯式typed入口，不靠room名稱推導位置。

sharedroom view只存sourcePlaneRef与展示crop，不再各保存可獨立編輯的calibration/x/y shadow；adapter由同SourcePlane派生現有reference渲染資料。旧獨立ReferencePage不轉義；新正式schema/能力dispatch，strict舊reader拒。來源換hash/page/size/rotation基準不偷接旧review，參照缺失保留room關聯描述並標待複核；資料庫不以同名圖自動替換。

roomId是集合metadata身份，不是nativeincarnation證據。nativeRef仍type/ID/受驗证closure；本地被跟踪edit/undo可更新associationPin；刪除重建同號／跨project延遲／無可靠沿革時需明選重關聯。命名在room metadata，nativegeometry仍由既有boundary/placement唯一讀取。刪room只解除集合關聯，是否也刪nativeboundary必須另明選preview且保留被引用守門；删除SourcePlane保留已有geometry、要求明選解绑/保留missing，不默删所有房间。sourcefilebytes只由明选project资产pool携带，不上传私人PDF。

**MR-A採納門檻**：A/B/C選一；原圖座標與basis變更政策；新增vs明選replace；legacy page/未知cap/保存閉包、native身份延續未知處理。房間自己是否建立3D Space屬可選後續，不能預設每room已是D5。

**MR-B/C验收門檻（未跑）**：同源双房PDF一次calibrate、連續兩房A不被覆盖；A/Bname/nativeRef独立且save/freshcontext完整；basis變只reviewstate、新房取新basis；cancel/late/delete-recreate/badcap拒不留孤兒；newid.surfaces避免合體ID碰撞；undoRedo恢复source/rooms与native一致；desktop/390px可以总览来源关系、真iOS/OS另人工。UI沿既有來源workspace整合新增/编辑意图，不新做PDFapp，GEO-219减项須具體。

## 採納及實作責任

每一項記`decisionId／選項／精確diff或schema／使用者授權來源與時間／已選範圍／尚未採納項`；proposal被merge不填「採納」。Q36使用者看逐條差異後，另一產品PR才改SSOT/白話/唯一正典/見證並跑sync/rebuild/check/reader三道；此文件PR不做。

native正式World／serializer一owner；保存owner统一cap/schema/legacygate，app/歷史一integrationowner；独立oracle作者不照抄implementation計算。PR73/74已合併，可核其实际接口後排共享檔單owner，而不是因舊「尚在執行」文字停規格準備。

A24/SR24真iOSkeyboard/OSchooser/download與Windowsmanual另列；390px/CI/文件驗證不代替。#24/#57維持open，最終產品驗收及merge另審。本輪未跑新產品測試，只有文件路徑、錨點、範圍與契約狀態驗證。
