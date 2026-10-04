# 已批准工作、接口與單 writer 隊列（2026-10-04）

唯一開發庫 `ZhiQiYang/geometry-axiom`；整合基底 main `1075058be37d37b98a2a910f4f67b87583be85b3`。使用者接受八項具體建議：「那8條根據你的建議 我能接受」，並授權工程自行安排順序／並行／批次。下表明寫範圍已採納；舊 Q31–Q37 的全部候選字段、額外選項與公理沒有一併採納。採納不等於完成／驗收。

## 精確採納與範圍外差異

| 對應 | 已採納第一版 | 未隨此次採納 |
|---|---|---|
| #85 | 修正 M01 誤判後推送本庫、draft PR、獨立複審後由 root 合併。已合併 PR98 `847cb74`→main `1075058b`。 | 忽略反例、只憑 CI；保留原 owner。 |
| #45／Q31 | 未完成或錯誤網格輸入隨專案保存、原樣重開、不自動正式提交；每專案一份 active draft；先來源→邊界入口。 | 多份draft、draft互引用、複雜多選、擴大生成。來源子規則草稿待其正式契約接入，不稱此切片已支持。 |
| #44／Q32 | 明選現行來源→看差異→確認更新同一模型，一步復原完整舊模型；先普通單一平面；身分不明重新指定、固定版本不暗升。 | durable incarnation ledger、任意多carrier、owned／faces+timbers producer、自動同名／同號重關聯。 |
| #46／Q33 | A/B各保存完整独立專案快照，原圖去重共用；B不改A；比較後整體採用並可回復。 | 細部挑物件合併、搬舊undo堆疊。 |
| #48／Q34 | 原PDF區域→指定參數欄位；圖面標值／量測／正式值分存；核對不直接改幾何；換圖或身分不明再核對；連結與原圖可攜。 | 全物件kind、核對直接採用模型值、durable target ledger。 |
| #49／Q35 | 六個有限正反例：合法規則、同角色不同構件、只改一接合、合法未完成配置、錯參數型別、固定版本不可變；隔離執行；結果可留，規則／來源／原生執行檔／runtime與驗證程式的相關版本指紋變更即過期；crash/timeout/缺能力非pass。 | 任意脚本／JSONPath／eval、永久green、只靠截圖。 |
| #57–62／Q36 | 下節六條來源子規則語義；先契約／獨立oracle→單native writer→保存→UI。 | 整包舊proposal、跨discarded undo永久不reuse、額外query API；多層、任意區域、面別覆寫。具體容量／allocator為工程實測選擇。 |
| #77／Q37 | 同PDF一份共用比例尺／對位；各房名稱與boundary獨立；新增不覆蓋，明選才編輯；基準變更舊房需複核而不變形、新房用新基準；解除列表關聯不刪geometry，不建3D父子。 | native房間樹、自動transform繼承／移動、自動多房辨識成功；辨識仍接#54/#87。 |

本地更新、實體手機、部署、付費、新系統權限不在此次動作內。容量、TEMP路徑、模組拆分與測試方法由工程owner决定，不再作排程阻塞。

## 供平行 owner 使用的短接口

以下是整合邊界草案，共用owner落實後才是產品API。各owner先做纯模組／fixtures／測試；不能自行修改manifest/history/app。功能资料只經有版本、有界plain JSON附件；沒有任意type fallback或通用Composition真相層。

```text
manifest.featureAttachments = {
  schema: "geometry-feature-attachments/1",
  records: [{kind, schema: featureSchema, value: boundedPlainJSON}]
}
readFeatureAttachment(kind) -> deep copy | null
setFeatureAttachment(kind, value | null, expectedContextToken) -> one local history step
feature module: validate(value), references(value), immutable fixtures
```

kind為共用owner有限白名單，每kind至多一record（case/rooms可在其value中有界集合）；第一切片只有`grid-draft`，之後按正式validator接`source-rooms`、`rule-cases`等。每個附件有自己的schema/capability，format由共用owner統一分配，舊reader不足就拒；不塞legacy欄位偷過守門。函式、DOM、cache URL、preview token、任意可執行值不保存。未知schema／kind拒；全部附件列入完整A/B閉包。第一版候選保存format為未占用的`geometry-canvas/10`，實作前再核main；`grid-editor-draft/1`與native `grid-subdivision-rules/1`分別守門，前端編輯附件能力不冒充engine生成能力。

写入綁context token、history frame與busy門；deep clone、no-op不加history/dirty、save前同步flush最新raw。跨案／過期回覆拒寫；匯入先驗真native最終物件與原圖完整閉包，成功一次替換、失敗不動原World/project/history。正式native confirm的metadata由同一步協調，不能另push一筆。

| owner 模組輸出 | 接口與整合責任 |
|---|---|
| #45 | `GridDraft {schema,draftId,kind:source|binding,intent:create|edit,baseRef,inputRefs,rawForm,view?}`，一份或null；空值／非法值保留raw strings/selectors，不當World；typed已發布引用＋內容pin，缺失／變更stale且明選，不自動confirm。 |
| #44 | 候選模块返回`{modelId,previousSignature,record,diff,sourcePins}`；record沿用現strict model schema，不增audit/incarnation。接線捕捉context/history/current signature，真producer驗後原子替換同record、一筆undo完整舊record；準備候選不改live。 |
| #77 | 版本化SourceRooms bundle、validator、asset refs及typed boundary/可選placement refs；一份basis、rooms只存名稱／引用／accepted basis，沒有第二polygon。native create/edit仍走既有candidate，由共用owner把metadata接同confirm步。 |
| #49 | 六個有界definitions/receipts、freshness pins與validator；每run新隔離process，不碰live token／World／feedback，未知runtime非pass；即使是已知且有能力的原生執行檔／runtime，換版指紋或驗證程式指紋變更也使舊pass過期。具體序列化字段由owner提報後統一接附件；不先競寫保存／入口／#85。 |

各模組可注入上述讀寫adapter獨立測試；不直接持有或修改`ReferenceWorkspace.context()`內Map。共享app/index/serve接線只有下表整合owner寫。

## 檔案 owner、順序與下一切片

| 單 writer | 獨占檔案／範圍 | 下一個可執行切片 |
|---|---|---|
| 此 cloud：共用格式／整合owner | project-store.js、reference-workspace.js、schema/capability、ContextHistory、app.js、共用index/serve/操作入口接線；#45 grid-system-workspace/context registry；決策隊列 | #24 PR97與新main相關gate；#45單rawdraft真ZIP/history/context骨架，沿既有來源→邊界入口。 |
| #85原owner | mutation/freshness/runner/expected必要修復 | PR98已合併；其他worker保留新scene139/integrity88/gate，不競寫基準。 |
| #44 thread `01a104fc-5524-76ea-93f1-9e6e632f709a` | 新候選／模型差異模組與独立tests；producer改動先協調 | 普通plan明選來源、真producer候選、cancel/stale差異oracle；store/app由共用owner接。 |
| #77 thread `01a104fc-a75a-728a-8d74-2e323f84d08c` | 新纯source-rooms模組、validator/雙房fixtures/tests | 共享basis、兩房refs/名稱、new vs edit、basis變更不改舊geometry；不競寫#54求解同檔。 |
| #49 thread `01a104ff-3a10-74c4-b1c8-8217c6fd308d` | 新有限案例／隔離executor與6fixtures/tests | 真隔離與crash/timeout/freshness/nonpass；保存／入口待共用骨架。 |
| #58契約／oracle準備 | GRID-SUBDIVISION-RULES-PROPOSAL.md與独立數學oracle | 下節精確差異／oracle，review後由root另指定native writer。 |
| #58/59 native thread `01a1050d-60bf-7207-844c-08bf99a520b0` | current_geometry.c、native inc/dump/parser/allocator/preview、web_bridge子網格核心 | 先六條精確差異/oracle再核心小slice；不與#54競寫；與共用owner協調native capability/dump，project schema/app及新format號由共用owner統一。 |

第一波#85/#24收尾、#45骨架、#44候選、#77人工多房、#49案例可並行。第二波共用接口穩定後接#46完整A/B、#48EvidenceLink、#49保存/入口。子網格分契約→native→保存→UI；自動辨識不阻擋人工多房。每slice先focused必要正反例／mutant，review可並行；同exact head跑stage必要完整gate，交root逐stage決定合併。按實際blob變動重跑受影響gate，不每個文案patch無差別全庫、不借舊head冒新pass；expected/golden由唯一owner協調。

## #58 六條採納映射與oracle（先準備，未改SSOT/native）

| 已採納條 | 現行差異與可審oracle |
|---|---|
| 一層source所有權，每主格或指定格，同source配置繼承 | 在D19旁增來源rule定义，無面亦可存在；雙配置同source同規則不同定位；拒多層／任意區域／面覆寫。 |
| 無錯縫雙軸重複，1…65、至少一軸>1、整數mm等分 | 不改D1；600×400、3×2→U200/400、V200；600/7、stagger拒，不四捨五入。第一個來源子規則切片限雙軸repeat；舊proposal的repeat-panel擴展未據此次整包採納。#45既有合法模式不受此新rule限制影響。 |
| 穩定rule/來源/主格/innerline引用；cancel不耗正式key；undo完整 | 增typed配置/source/rule/signedcell/axis/index，非sample序號／近鄰；wrongsource同key拒；cancel前後allocator/dump全等、undo完整恢復。位寬/highwater工程選擇，不當使用者逐字批准。 |
| 有ref鎖divisions/scope/delete，重疊及manual衝突拒 | 新source-rule有ref守門比manual I23嚴；不改舊manual可重算語義。rule-rule/manual雙向衝突明示，不默選優先序；三個鎖各有負例。 |
| source變更驗所有配置／已引用構件，任一失敗全拒；子線非支撐 | source-wide candidate閉包；第二配置失支撐時整World/history/dirty不改。子線僅定位，保留D11/D15/D17/I19真支撐。 |
| 完整保存rule/ref/capability，舊reader不足拒 | scene/project重開全等；缺cap／strip marker／降版／缺閉包替換前拒；不支持的model producer明示拒，不只換hash。 |

下一份SSOT契約patch按六條逐段diff，不整包搬proposal。工程预算32rules/1024cells等需測量；durable沿革、跨discarded undo永久不reuse、額外query API不是新採納公理。root審查後再進native單writer，不動#54或私人圖紙。
