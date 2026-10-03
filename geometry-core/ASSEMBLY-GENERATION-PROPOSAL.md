# AR-06 最小角材生成契約：已採納

Refs #25。基準 main `fc4f08bd5ecb31f26179334b9b35a21de21e928d`。
2026-10-03 使用者指示「開始實作」，核准本文件的 D34/I42/R35 差異。
条文已採納；公理來源提交 `cc6adff4c9c783ce78bcbd849754b69254690cab`。
實作、API 與驗收證據見 [生成器操作與驗收](../geometry-web/docs/ASSEMBLY-GENERATION.md)。下方 W1–W3 保留為提案階段的原生見證。

## 第一個可用流程

選已發布材料配置 → 指定同一承載面、兩支主支的定位線、中支定位線與既有兩端邊界材 →
預覽三支角材的完整來源、位置、完成料長與接合 → 確認整筆建立 → 保存重開。
先生成兩支平行主支及一支端接副支，不以角材示意圖代替實體。
主支本身也必須有兩端合法支撐。主支的兩個來源欄位沿用 R21 無序 between：
保存鍵 ends.start／ends.finish 表示兩個選擇器欄位，不能當成物理起末端的有序宣告；
實際端面依 +v 走向與原生求值決定。副支的 member 起末端則維持局部 joint 的有序接觸。
範例需要先存在兩支邊界材；它們不是暗建的生成結果。

## 原生幾何見證（已執行；不是生成器驗收）

`tests/build_assembly_generation_witness.py` 在隔離 bridge 中使用現有 place／references／scene 載入。
兩個正例的三支角材與引用均在新 bridge round-trip；缺支撐反例核對指定拒絕原因與 World 不變。

| 案例 | 承載面與輸入，mm | 既有原生核心實測 |
|---|---|---|
| W1 | 4000×3000；上下邊界材各寬20；主支中線500、2500；中支中線1500；截面27×33 | 主支各2960，中支1973；主支+v，中支+u，A0貼承載面，B沿+n |
| W2 | 同一面與邊界材；主支中線500、2800；中支1500；截面40×50 | 主支各2960，中支2260；方向與貼面不因截面改變而翻轉 |
| W3 | W1移除上下邊界材 | 第一支主支拒絕：`V_CUT_PRIORITY`，訊息包含「只有 boundary」；World不變 |

W1奇數寬27的實際內側面位於x=514、2487，不能以連續浮點的±13.5替代現行整數規則。
主支截面局部A軸實測為−U，中支A軸為+V；因此「世界+U側」不能固定寫死為某個B0/B1。
端面選擇必須由完整基底與面法向推導並核對，不依螢幕左右或分件排序猜測。
見證只證明上述現有幾何可成立，不證明下方實例、更新、UI或新能力已存在。

## 明確有限範圍

首版只接受以下拓撲：三個不同member；兩個primary member可共用slot；一個secondary member；
secondary的start、finish分別端抵兩個primary的相向側面。規則恰有這兩個end-to-side joint。
不支援ortho-split、反組法、成員重複展開、全屋自動排列、巢狀規則或有相位差格線。
不支援的合法authoring規則回報UNSUPPORTED，不能偷偷改role或刪除joint。

配置明選每個member的角色、同面guide與方向。首版primary都沿+v，secondary沿+u，深度側+n。
規則的side／dir在此執行器以指定承載面的U/V作為共同求值框架；旋轉畫布不改此框架。
允許的两處接合為secondary.start→primaryLeft的+u側、secondary.finish→primaryRight的−u側；dir=u。
binding必須選contactFace=A、orientation=A；此處orientation=A明確表示截面A沿各member的面內橫向，B沿+n。
這是首版生成器新增的幾何解讀，不由舊authoring示意圖推定。其他合法選擇回報UNSUPPORTED，不改原binding。
初期只接受guide與明指timber擋面；signed grid與多段span留待後續各自契約。
承載面邊界、孔洞及existing timber仍由現行I5/I19/R6驗證；首版UI不承諾任意凹形多跨距求解。

## 提議的精確輸入

以下欄位已由原生生成交易實作。所有物件ID為正uint32，JSON不接受未知欄位；name不是身分。

```json
{
  "id":1,
  "name":"兩主支與中支",
  "bindingId":1,
  "rule":{"id":1,"version":1,"fingerprint":"<64 lowercase hex>"},
  "surfaceId":1,
  "members":[
    {"memberId":1,"role":"primary","guideId":1,"dir":"+v","depthSide":"+n",
     "ends":{"start":{"kind":"timber","id":90},"finish":{"kind":"timber","id":91}}},
    {"memberId":2,"role":"primary","guideId":2,"dir":"+v","depthSide":"+n",
     "ends":{"start":{"kind":"timber","id":90},"finish":{"kind":"timber","id":91}}},
    {"memberId":3,"role":"secondary","guideId":3,"dir":"+u","depthSide":"+n",
     "ends":{"start":{"kind":"member","memberId":1},"finish":{"kind":"member","memberId":2}}}
  ]
}
```

member集合必须恰與固定規則相同，不以列表順序配對。各member尺寸讀其slot的binding來源。
兩端參照選的是實際擋面族；依R21解析為唯一且全寬合法的面。多解仍拒絕，不挑最近者。
每個實測接觸須核對對應joint的指定側、端點、方向；僅料長相同不足以通過。
初次建立將目前binding定義指紋送作expectedBindingFingerprint，rule指紋固定。
binding仍是可編輯來源，合法編輯須在同一候選重算所有實例，不凍結成舊尺寸。

## 原生責任與穩定分件

新增World獨立AssemblyInstance，保存上述來源定義與memberId→timberId所有權對應。
生成角材只透過現行C構造、位置引用與全量驗證，前端不能另解料長或產生JSON實體。
首次生成由native在同一候選分配三個不占用的timberId；不得由JS連續加號湊號。
分件身分為(instanceId,memberId)，更新保留同一member的timberId；排序、改名不換料。
固定三member首版沒有拆分／合併對應問題；變更member集合須回UNSUPPORTED，不能默認重建。
實例擁有的角材不能在一般place／delete／工程綁定入口獨立覆寫。要改須編輯實例來源。
刪除實例在單一候選刪其三支owned timber；被外部來源引用時拒絕，不級聯刪除下游。
existing支撐材、guide、surface不歸實例所有；刪除仍被實例使用的來源拒絕。
兩支primary先求值，再求secondary；不能先求副支再把主支支撐檢查略過。

## 交易、更新與能力

沿用revision/token、候選World、全量重驗、receipt與ContextHistory。
擬新增`assembly-generation-transaction/1`：create-instance、edit-instance、delete-instance。
create檢查不存在；edit/delete檢查完整來源指紋。expectedRevision與指紋均須符合。
讀取與預覽列每支memberId/timberId、來源、兩端接觸、完成料長、新舊差異及diagnostics。
preview/cancel不改World；確認只提交已驗的同一候選；失效token拒絕；遺失回覆先查receipt不盲重送。
合法參數／guide／binding來源改動依I8a重算依賴；任何分件違規則全部回滾，並保留草稿。
規則／材料固定版本不自動升版；binding明確換版須保持原memberId集合與首版拓撲，否則UNSUPPORTED。
任何來源換版都列舊／新指紋，不以有效數字相同視為未變。

提議能力`assembly-timber-generation/1`，與`assembly-rule-authoring/1`分開。
提議完整專案`geometry-canvas/8`，含原生實例定義、owned mapping與必要來源閉包；/1–7照原義讀。
PR #50的experimental `/8`＋`assembly-rule-identities/1`不是本提案資料格式，不能當相容專案載入。
必須同時驗schema、capability與content；舊客戶端明確拒絕，不靜默丟實例。
重開在隔離候選內重建並比較owned mapping與衍生幾何；owned timber記錄不可單獨冒充普通料。
純OBJ/GLB是幾何快照，不宣稱保存可重建來源；無生成能力的model package入口仍明確拒絕。
保存、取消、undo/redo、切專案、延遲回覆、失敗匯入全部同現有主專案流程；不另造第二套保存。

首版資源上限：每實例3member、World最多16實例；總timber/guide容量仍用現行上限。
新增定義每筆最多8191 UTF-8 bytes，採既有768-byte原生scene分塊；專案附件按現有大小上限。
容量超限回UNSUPPORTED/CAPACITY，不能部分新增或返回空成功。

## 已採納的公理差異

保留D1/D7/D15/D17/I19/R6及D33原文，不放寬任何支撐或方向底線。

```diff
+ D34 組構實例（AssemblyInstance；assembly-timber-generation/1）：
+ 與規則版本、材料綁定分離，保存固定規則版本及指紋、明選binding來源、
+ 有限member配置、承載面與定位／兩端支撐引用，以及member到原生角材的所有權對應。
+ 分件身分依instance/member，不依名稱、陣列或示意圖；完成料長依D7/R6推導。
+ binding本身不生成角材；具備本能力的實例求值才可建立owned角材。
+ 首版限兩支同向primary加一支端接secondary；接觸面A、截面A沿面內橫向、B沿深度。
+ 任一合法authoring規則超出此能力時回UNSUPPORTED，不改規則、role或binding。
+
+ I42 組構實例守門與保存：
+ 配置恰覆蓋固定規則member，來源完整有型別，逐件核對joint端點／側面／方向。
+ 主支自身支撐與副支兩端支撐均通過I19/R6；owned角材不接受獨立覆寫或刪除。
+ 來源改動、建立、更新、刪除均整筆候選重驗；失敗、取消及過期回覆保留原世界。
+ 完整專案保存實例、owned mapping與来源閉包並宣告獨立生成能力；重開重算核對。
+ 舊能力不足明確拒絕，不能展平為普通角材冒充保留組構来源。
+
+ R35 有限角材組構求值：
+ 驗能力與完整有限輸入 → 讀固定規則與binding來源 → 核對member/joint對應 →
+ 精確求尺寸 → 先求兩支主支及其支撐 → 求副支指定跨距與接觸 →
+ 全量碰撞、範圍、引用及所有權驗證 → 新舊分件預覽 → 確認同一候選 → 保存。
+ 卡片位置、示意旋轉、視窗範圍與可見格線不決定生成分件或長度。
```

## 必須執行的驗收（結果見生成器操作與驗收）

G01真正UI從既有規則/binding＋指定來源建立三支native角材，完整核對來源與接觸。
G02两種截面/configuration精確料長；同角色不同member不混淆；排序改名不換timberId。
G03缺輸入、缺支撐、多解、錯面、錯型、非整數、錯規則指紋及超容量各拒絕且World不變。
G04參數/guide/binding改動重算所有分件；source-only變更亦在預覽可見；取消/失敗全回滾。
G05owned角材的所有一般入口防覆寫，外部引用阻止刪除；互相引用與自我支撐循環拒絕。
G06保存真bytes、全新服務重開重算；/1–7回歸；假/8、缺能力、壞mapping原子拒絕。
G07建立/更新/刪除與來源改動undo/redo，dirty、mapping及草稿一致。
G08失效token、遺失確認回覆、延遲跨專案不雙提交、不串用；故障注入必須變紅。
G09桌面/390px真正操作，console、溢出與焦點核對；實體手機另記未驗。
G10最終SHA完整native/CDP/space/timber回歸；不得拿本文件W1–W3當G01–G10已通過。

UI由材料配置的選取檢視器按需提供生成／實例編輯，替換目前重複的能力說明，
不新增常駐工具列或第二套工作區保存鈕；BACKLOG須記減項，依AGENTS執行。
幾何端面接觸不等於釘接固定、施工可行或載重合格。工序、固定件、加工及力學不併入首版。
