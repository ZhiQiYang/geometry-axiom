# PF-3：衍生宿主前置的範圍裁決

領取分支 `feat/pf3-panel-fill-20261013`，base 為 PF-2 #225 的
`077165010377cca974bece7fcda930cd005490a9`。本文件不是功能交付；
沒有修改產品、公理、核心 C、runner 或 expected。

## 實際基準與限制

原生 PF-2 fixture 建立 D41、材料版本、D44 threshold 引用及 D42 試排後，
bridge 的 effectiveSeams、support、derivedPlacement 均為 null。
`native-probe.json` 保留真原生輸出，probe 最後以
`PF3_SUPPORT_MISSING` assertion exit 1；不是把提案表當成驗收收據。

SSOT R43 只計入宿主為該試排 D4 衍生承載面的角材；其他面即使共面亦不計。
PF23/E1 的必要 fixture 是此宿主上的足跡 [90,120]×[0,300]，
不能改用一般 boundary placement，更不能讓 API 接受任意前端足跡冒充 World。

GEO-255 把板背面／分層判樑列在 PF-5；PF-2-NATIVE.md 也把
derivedPlacement 留給 PF-5。最新看板卻要求順序 PF-3→PF-6→PF-4→PF-5。
這是切片依賴的範圍問題，不是已採納 R43 的條文矛盾。

## 需 Claude 裁決的具體選項

建議把 **D4/R41 衍生宿主的最小原生實作併入 PF-3**，PF-5保留空間完成面流程。
必要範圍包括：

- 真 placement 變體：同 id 空間，來源 fill id、具型別 h 來源與畫布位置。
- 每次重算 R41 兩層與板背框架，複用既有 D7 放置、擋面、碰撞引擎。
- 新來源／刪除／過期 token／撤銷與 scene 保存都以來源定義為準；不保存輪廓 cache。
- 原生 bridge 建立／讀取／預覽／確認，及有效縫與 R43 對真宿主料的判定。

另一個選項是先把 PF-5 的衍生宿主前置獨立交付，再續 PF-3。
不建議把 PF-3降成只驗「沒有角材」的空集合，因為這無法交付 PF23／PF24。
這些 D4/placement 接入會超出20行小例外，且跨原定 PF-5 切片，故先報裁決，
沒有擅自調換實作範圍或重寫 SSOT。

## 已備妥的驗收 oracle（未實跑）

- PF23 E1：三段 (0,50)/(50,100)/(100,300)，寬度10/20、10/5、10/20；
  X8中段紅，X5全綠仍三段；移除板分片頂點切點必紅。
- PF24 E2/E3：R左界125／120，與沒有障礙逐字同一段10/20；移除同值合併必紅。
- PF05／06：threshold 唯一 ParameterRef、有理數精確比較；不足可保存；
  普通共面宿主不計入、移除宿主身分過濾必紅。
- D43：缺角／孔／障礙的單側區不形成有效縫；交丁保留band身分。
- D4/R41：反向結構側、垂直面、開區間、h變更、來源刪除、保存重開與交易全拒／全還原。

所有上列正式項目未驗，probe 的紅只證明基準缺能力；沒有產品突變 killed。
GEO-219：無新入口。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。
