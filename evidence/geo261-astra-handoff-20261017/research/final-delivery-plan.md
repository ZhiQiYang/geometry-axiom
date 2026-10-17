# GEO-261 最終交付準備清單

Preparation snapshot：**2026-10-17T00:56:17Z（UTC）**；更新自 00:07:24Z 快照。這是外部交付規劃快照，**尚未正式交付，也不是完成、可合併或最新來源通過聲明**。本次只讀 Git／GitHub、原始碼、文件及既有收據；只刷新本文件與同目錄 `delivery-state-20261017.json`，沒有改 repo／Git／既有收據，沒有執行測試、C、native、WSL 或 browser。時間點之後的工作不自動納入本快照。

**目前阻擋正式交付：** integration `43305271770760a690e360ce18ce11cc07f35ea2` 仍明示 `coverage.complete=false`，#289 未合入／未啟用。599 原始結果維持 **36 PASS／1 FAIL／239 UNRUN**（計畫276、實跑37）；外部 corrected closeout 已保存，仍不屬四包 immutable P1。#279 的4aec只修harness正常live-context初始化；截至00:53:37Z，fresh-five仍等共享鎖，**C0／method0，後續276未啟動**，不能翻轉599 RED。新default八題、最終mutation／架構刷新、同源完整驗收均未完成；主協調者回報Claude OAuth expired，最終review尚未完成。

§2 保留 12 列實際物件與補充 API 對照；§3 保留使用者八項交付映射。歷史靜態架構結果封存來源仍為 `47d3bb4bcccddeeb034dd5899a7aa15c9cab0768`，不因本次文件刷新變成目前來源驗收。
## 1. 凍結來源與 PR 清冊

- 整合 checkout／#288：`43305271770760a690e360ce18ce11cc07f35ea2`（本機HEAD及GitHub head均已只讀核對）；已含最新#279 `4aec7f428b9307ed9596aba2ed893175b8db76a5` 與#286 `7b278d598ad9d5066fa0d756440af88d92cca55a`，以及四個browser launcher可攜性修正。本次 `git status --porcelain=v1 --untracked-files=all` 無輸出，只表示讀取當下clean，並非產品通過。
- GitHub main：`27f5c09bdd35b0ef9db2c6c636c8a63e47625de0`（#287；已含 #265）。它是 #288 的父系來源之一，不等於 GEO-261 已入 main。
- #289：`8f36f1a0dd7e1244c92aca926c0a80079451e7f0`，只包含較早整合 `9de9cd4f67417b7918842ce05ef11044f8a08b68`，未包含目前4330527；兩個 head 互不為祖先，共同祖先為該 9de9。新增八個真 C→Python default tests 已加強實際 candidate／Program.sources 觀察，仍 UNRUN。較早 174 項收據保持原來源 `f3c71065a62f2f961a26367c04216c01377383c3`。
- 下表 24 個 GEO-261 PR 均為 OPEN／draft（GitHub metadata 本次重讀）。22 個非整合、非 default 的 head 均為4330527的祖先，#288 是該 head 本身；#289 尚未合入。GitHub 未把這些 PR 標為 merged。不得將「已在整合候選中」寫成「已入 main」。

| PR／用途 | 完整 head SHA | GitHub base（PR 或分支） |
|---|---|---|
| [261 提案](https://github.com/ZhiQiYang/geometry-axiom/pull/261) | `79c3f2b11e404abf8bf2ac461cb4d6d668d7cedb` | main |
| [266 採納](https://github.com/ZhiQiYang/geometry-axiom/pull/266) | `ddc6ee8383d2f822b17e47a82563aae5e73e9d69` | main |
| [267 F1](https://github.com/ZhiQiYang/geometry-axiom/pull/267) | `a219ccd13f55a79515fe967b464730b905cfdcff` | #266 adoption |
| [268 N1](https://github.com/ZhiQiYang/geometry-axiom/pull/268) | `74112ea90d77ea267d7f1a9499751889ce688a36` | #266 adoption |
| [269 PY1](https://github.com/ZhiQiYang/geometry-axiom/pull/269) | `3a9dc84b118123e237d1ddc20ee70689d5f21352` | #266 adoption |
| [270 region 修正](https://github.com/ZhiQiYang/geometry-axiom/pull/270) | `a88d3c57917d22aa28e3357b2c22e08c586a9f71` | #268 primitives |
| [271 F2](https://github.com/ZhiQiYang/geometry-axiom/pull/271) | `9d1ca613d34dc3036fb7ef61e31bcf5ab9c7aecb` | #267 frontend |
| [272 parameters](https://github.com/ZhiQiYang/geometry-axiom/pull/272) | `4aabd21cf82d495f5ab4902bedc9330ca5ed4e3b` | #268 primitives |
| [273 annotations](https://github.com/ZhiQiYang/geometry-axiom/pull/273) | `b370f753f22d0d119835c59d23b0a78344f8ee55` | #272 parameters |
| [274 F3](https://github.com/ZhiQiYang/geometry-axiom/pull/274) | `107d4515c88fa8782c6f2f9ae77ea7b084a1259b` | #271 policies |
| [275 第二模板](https://github.com/ZhiQiYang/geometry-axiom/pull/275) | `c65995221cf016cb02533a6cb0952f19c22bfeb9` | architecture/geo261-template-base-20261016 |
| [276 網格更名](https://github.com/ZhiQiYang/geometry-axiom/pull/276) | `73aca666e779527bd096e7f09a9bc12cdc38d051` | main |
| [277 N2](https://github.com/ZhiQiYang/geometry-axiom/pull/277) | `c28ea9639b79881f30995cd79ce843346373c31e` | #273 annotations |
| [278 PY2](https://github.com/ZhiQiYang/geometry-axiom/pull/278) | `a5945c4c98dd6de58de51d19d8a37e251641e9c0` | #269 geometry |
| [279 native source graph](https://github.com/ZhiQiYang/geometry-axiom/pull/279) | `4aec7f428b9307ed9596aba2ed893175b8db76a5` | #277 sources |
| [280 PY3](https://github.com/ZhiQiYang/geometry-axiom/pull/280) | `e7c6c38759634b543ee7be5bdf43372356512fba` | #278 runtime |
| [281 PY4](https://github.com/ZhiQiYang/geometry-axiom/pull/281) | `35408155818f4a2745d998b016344a6d3e6ebd71` | #280 native-host |
| [282 依賴守門](https://github.com/ZhiQiYang/geometry-axiom/pull/282) | `7aeccc235958849a9927561a6ec57b48e347c527` | #266 adoption |
| [283 transport](https://github.com/ZhiQiYang/geometry-axiom/pull/283) | `4b759d13adaf3d9259b5fb89b37bfced741d6c1d` | #281 typed-sources |
| [284 source runtime](https://github.com/ZhiQiYang/geometry-axiom/pull/284) | `29eda28406dcd26277a2e246d8de7bfcae80209c` | #283 transport |
| [285 Python 第二模板](https://github.com/ZhiQiYang/geometry-axiom/pull/285) | `5cc3be9327ed8f3191491578370203bd12e6b319` | #284 source-runtime |
| [286 歷史收據](https://github.com/ZhiQiYang/geometry-axiom/pull/286) | `7b278d598ad9d5066fa0d756440af88d92cca55a` | #279 source-graph |
| [288 整合](https://github.com/ZhiQiYang/geometry-axiom/pull/288) | `43305271770760a690e360ce18ce11cc07f35ea2` | main |
| [289 Python default](https://github.com/ZhiQiYang/geometry-axiom/pull/289) | `8f36f1a0dd7e1244c92aca926c0a80079451e7f0` | #288 integration |

### 祖先關係與交付順序

本次用 `git merge-base --is-ancestor` 對GitHub回傳的完整head作只讀核對；JSON另保留每筆GitHub原樣回傳的`baseRefName/baseRefOid/state/isDraft`，base metadata不當作已吸收最新base內容的證明。相較00:07快照，ours只有#279（599→4aec）及#288（d4b22→4330527）head改變；其餘22個head、24個base名稱／OPEN／draft與main未變。

| 完整來源關係 | 結果 |
|---|---|
| 舊599 `599f3414d333967dbd6c538a3ea50d1ac5b1baa6` → 最新#279 `4aec7f428b9307ed9596aba2ed893175b8db76a5`；舊599 → #286 `7b278d598ad9d5066fa0d756440af88d92cca55a` | 兩支各自從599前進；最新#279與#286互不為祖先，不能再寫成線性鏈 |
| 最新#279 `4aec7f428b9307ed9596aba2ed893175b8db76a5`、#286 `7b278d598ad9d5066fa0d756440af88d92cca55a` → #288 `43305271770760a690e360ce18ce11cc07f35ea2` | 兩個head皆已吸收於整合候選，仍未入main |
| #289 `8f36f1a0dd7e1244c92aca926c0a80079451e7f0` ↔ #288 `43305271770760a690e360ce18ce11cc07f35ea2` | 互不包含；共同祖先 `9de9cd4f67417b7918842ce05ef11044f8a08b68`，尚待一般 merge |

建議審閱順序仍為提案／採納 → native、Python、frontend 與依賴守門 → 第二模板／相容接線 → 歷史證據 → 整合 → default。剩餘工作須在4aec的harness初始化修正後完成同源coverage全驗，才啟用完整producer coverage、核收八題真C→default，並把#289一般merge入整合；不能把舊 174 項 mock 邊界結果視作啟用依據。現有已吸收 heads 不必機械重複合併。後續封版次序見 §8。

其他 owner／列車只讀參照：[open draft #290](https://github.com/ZhiQiYang/geometry-axiom/pull/290) head `9d0aa6161fecfd713ab237287725b3ffe216c80d` 未在4330527；[第19班 #287](https://github.com/ZhiQiYang/geometry-axiom/pull/287) head `945ae87ccd6f49dbfc22d439b3f9c28fed4ac40c` 已 MERGED，其 main merge 為 `27f5c09bdd35b0ef9db2c6c636c8a63e47625de0`。不把 #290 算入本次 24 PR，不修改它、列車、PR base/state 或 Git。#276 與 #265/#287 重疊修正沿現有整合結果審閱。
## 2. K ↔ W 概念與真實介面

以下物件表是目前公開 header／Python 定義的只讀對照，不替代同源 native 驗收，也不以 PROPOSAL 的理想責任表推定缺少的產品型別。H 持有公開 parser、能力／保存相容、完整 World 的交易與裝配。§1 是本次時間點的完整 head 快照；此 API 對照保留既有有限核對範圍，不改稱交付完成。

### 2.1 幾何概念與木工對應：交付主表

| 幾何名稱／實際 K 型別或 API | 木工名稱／實際 W owner | 界線與限制 |
|---|---|---|
| 有向矩形稜柱：[geometry.h][kg] 的 `GeoBox3`、`GeoFrame`、`geo_box_face()` | timber／角材：[members.h][wmember] 的 `WoodMember`、`wood_member_construct()`、`wood_member_face_room()` | K 無 timber 型別；A/B/length、auto_length、構件面名稱與角色屬 W。 |
| 方向：[geometry.h][kg] 的 `GeoVector3`、`GeoFrame`；K 無 primary/secondary/boundary enum | [members.h][wmember] 的 `WoodMemberRole`／`WOOD_MEMBER_ROLE_*`；[grid_application.h][wga] 的 `main_along`、`wood_grid_source_main_along()` | 主支、副支、邊界材及切斷優先級是 W 政策，不是三種幾何體。 |
| 局部平面區域：[regions.h][kregions] 的 `GeoRegionDefinition`、`GeoRegionLoop`、`geo_regions_put()` | 空間邊界面：[boundary_policy.h][wboundary] 的 `WoodBoundaryPolicy`／`WoodBoundaryKind`；[domain_values.h][wdomain] 的 `WoodBoundaryRegion` | K 擁有外環、孔洞、頂點身分；平面圖／立面分類與 FIXED/FREE 屬 W。 |
| 帶框架的平面域：[placements.h][kplacements] 的 `GeoPlacementDefinition`、`geo_placement_domain_view()` | 承載面：[boundary_policy.h][wboundary] 的 `WoodPlacementPolicy`；板背變體是 [finish.h][wfinish] 的 `DerivedPlacement`、[derived_placement.h][wderived] 的 `wood_dp_rebuild()` | K 存框架與 RECT/REGION_REF/REGION_SET；板背 fill/h 來源及固定邊重建屬 W。 |
| 方盒／軸向投影：[geometry.h][kg] 的 `GeoBox3`、`geo_aabb_project_uv()`、`geo_aabb_project_interval()` | RC column／beam：[obstacles.h][wobstacles] 的 `WoodColumn`、`WoodBeam`；[world_validation.h][wvalidation] 的 `wood_world_validate_obstacles()` | K 無 RcColumn/RcBeam 型別；space_id、樑水平軸、柱柱 footprint 檢查範圍是 W 政策。 |
| 有序區域成員與六向平面槽：[enclosure.h][kenclosure] 的 `GeoEnclosure`、`geo_enclosure_evaluate()`、`geo_enclosure_axis_bound()` | 既有 Space 使用中性 enclosure；W 的 [world_validation.h][wvalidation] 以 `WoodRoomBoundsLookup` 接收房間範圍，`WoodColumn`／`WoodBeam` 保留 space_id | 沒有獨立 WoodSpace 型別；`GeoEnclosure.closed` 只表示六向槽位齊全，並非一般封閉實體證明。 |
| 有向殼／內部／布林：[graph.py][kgraph] 的 `OrientedShellDef`、`InteriorDef`、`AssemblyDef`、`UnionDef`、`DifferenceDef` | shell／composite_space／composition：[model_policy.py][wmodelpolicy] 的 `WoodworkingModelProvider.admit_root()` | K 算拓撲／實體；enclosure、clearance、geometry 用途准入屬 W；CompositeSpace 與上述 D5 Space 不同。 |
| 斷面區域／矩形：[regions.h][kregions] 的 `GeoRegionDefinition`、[geometry.h][kg] 的 `GeoRect2`；Python [types.py][ktypes] 的 `RegionDef` | profile／member：[section_profile.h][wsection] 的 `SectionProfile`、`ProfileMember`、`wood_sp_put_profile()`、`wood_sp_put_member()` | 沒有同名 K 型別；timber/panel 類別、calcium-silicate-6、材料尺寸來源、成員排布是 W。 |
| 直線拉伸：[graph.py][kgraph] 的 `ExtrusionDef`；[geometry.py][kpygeometry] 的 `extrusion_geometry()` | run：[section_profile.h][wsection] 的 `ProfileRun`、`wood_sp_resolve_placement()`；[section_profile.py][wpysection] 的 `ProfileObject`、`profile_objects()` | K 接收框架、區域及上下界；run/profile/member 身分、live/copied host、簡易定位與材料註記由 W 解釋。 |
| 平面裁切碎片：[clip.h][kclip] 的 `GeoClipLoop`、`GeoClipComponent`、`geo_region_clip_rect_minus_rects()`；框架是 `GeoFrame` | panel／finish：[panel_layout.h][wpanel] 的 `WoodPanelTile`、`WoodPanelLayout`、`wood_panel_layout_build()`；[finish.h][wfinish] 的 `FinishSurface`、`PanelFill`、`wood_pf_build()`；[engineering.h][wengineering] 的 `EngMaterialVersion` | 板片碎片直接使用 K clip 型別；板材規格、完成面結構側、障礙選擇、鋪排身分與承接政策屬 W。 |
| 週期本體／間隙／交替偏移：[grid.h][kgrid] 的 `GeoFiniteSequence(body,gap)`、`geo_period_pitch()`、`geo_period_center()`、`geo_alternating_shift()`；[grid_store.h][kgridstore] 的 `GeoGridAxisDef` | grid panel/gap／交丁：[grid_application.h][wga] 的 `WoodGridApplication`；[panel_layout.h][wpanel] 的 `WoodPanelSeamLine`、`WoodPanelLayout`；[finish.h][wfinish] 的 `PanelFill(gap,stagger)` | body 是中性幾何寬度；將它解作板尺寸、縫中心及交丁鋪排，由 W 決定；K 不預設板材。 |
| cut／kerf／remainder：本次核對的 K/W 公開 API 未找到專用裁切計畫或餘料型別，不能把一般區間 API 說成已完成的裁切引擎 | 現有 [cut_list.h][wcutlist] 僅 `WoodCutGroup`、`WoodCutList`、`wood_cut_list_collect()`（料單分組） | 鋸縫、修整、原材、留用門檻、宣告餘料的 W 責任在 [PROPOSAL][proposal] 有列；[cutting-plan README][cuttingreadme] 明示實作另在 K1-a/K1-b，條文採納不等於目前功能完成。 |

### 2.2 來源、候選與裝配機制：補充表

| K 幾何概念／實際 API | W 木工對應／實際 API | 責任界線 |
|---|---|---|
| [source.h][ks] `GeoDefinitionValue`, `GEO_SOURCE_DEFINITION` | [definition_sources.h][wd] `WoodMemberDefinition`, `wood_definition_sources_member()` | K 保存 schema/canonical bytes；W 解釋角材 authored facts，定義不等於姿態快取。 |
| [source.h][ks] `GeoSourceRef {provider,key,key_size}` | [grid_sources.h][wg] `WoodGridSourceKey`, `wood_grid_source_ref()` | K key 為不透明精確 bytes；W 編碼種類、ID、欄位，不以 C padding 當身份。 |
| [source.h][ks] `GeoSourceProvider`, `geo_eval_register_many()` | [engineering_sources.h][we] `wood_engineering_sources_register()` | H 注入固定 provider 集合；K 不載入 W，callbacks 綁同候選。 |
| [source.h][ks] `geo_eval_source()`, `geo_eval_depend()`, `GeoDependencyKind` | [grid_sources.h][wg] `wood_grid_sources_definition()`, `wood_grid_sources_dimension()` | K 管型別／依賴／循環；W 決定領域所需定義與值。 |
| [candidate.h][kc] `geo_candidate_bind_state()`, `evaluate/seal/check/mark_published` | [document.h][wdoc] `WoodDocument` | W 改候選；K 驗 seal/revision/stamp；H 發布完整 K+W 並保留歷史。 |
| [document.h][kdoc] `GeoDocument`, `geo_document_*_view()` | [document.h][wdoc] `WoodDocument` | K 擁有參數／區域／定位／網格／版本 store；W 擁有角材／組構／工程／完成面政策。 |
| [geometry.h][kg] `GeoRegionSetView`, `geo_strip_intervals()` | [contacts.h][wcontact] `wood_member_end_contact_check()`；[supports.h][wstop] `wood_stop_pick()` | K 算幾何區間；W 判接觸順序、支撐與豁免。 |
| [grid.h][kgrid] `geo_lattice_coord()`, `geo_finite_sequence()`, `geo_interval_subdivide()` | [grid_application.h][wga] `WoodGridApplication`, `wood_grid_apply_system()` | K 精確分格；W 承載面應用、主支方向與子格政策。 |
| [version_sources.h][kv] `geo_version_definition_encode()`, `geo_version_sources_register()` | [engineering_sources.h][we] `wood_engineering_version_metadata_encode()` | K immutable identity/content/fingerprint/typed fields；W 材料／做法 metadata。 |
| K 不 import 裝配入口 | [frontend.js][wf] `woodworking/1`, `materialDraft()`；H [application.js][ha] `GeometryApplication.woodworking` | 固定第一模板，不新增公開模板切換、DSL 或可保存物件種類。 |
| [grid.h][kgrid] 共用 `geo_interval_subdivide()` | 第二模板 [rectangular_grid.h][rect] `rectangular_grid_evaluate()` | 無木工依賴的程式級見證；不另寫分格公式，也不宣稱產品已支援新 root。 |

## 3. 使用者八項交付要求逐項對應

原要求為本次接手對話 2026-10-15 18:14:37Z 的「交付（全部做完才算）」；完成定義是 Claude 審過、品質無阻擋、只差排列車。最終應在 [#248](https://github.com/ZhiQiYang/geometry-axiom/issues/248) 發布一則可逐條核對的交付，目前不得貼成完成。

| 要求 | 已有可引用材料 | 尚缺／交付時限制 |
|---|---|---|
| 1 每 PR 完整 SHA／順序 | 本文件 §1，GitHub 清冊與實際 ancestry | 原生失敗修復與 default 合入仍會推進來源；最後重取完整 heads，另列最終列車 SHA，不以本快照當未來 head。 |
| 2 幾何↔木工概念表 | 本文件 §2；[PROPOSAL][proposal]、[PRODUCT-ARCHITECTURE][architecture] | 必須連到真 API，不能只將舊函式改中性名稱就宣稱演算法已移層。 |
| 3 條文／核心程式／模板內容 | [APPROVAL][approval]、[ADOPTION 收據][adoption]、[clause-map][clausemap]、[merge-addendum][addendum]；K/W/H 路徑見 §2 | 207 條為 K31/M95/W30/H51；103 條分層改文，保留95條M完整上游正文。採納與實作完成分開。 |
| 4 依賴／拿掉模板／功能不變 | [架構收據][archreceipt]；[第二模板說明][rectreadme]；[舊 producer fixtures][fixtures]；[採納手冊][runbook] | 靜態拿掉69個K檔之外的模板不是 runtime 證明。最新同源 native、完整舊 `.scene`／模型包／`.gcanvas` 冷重開、前後數量及瀏覽器仍待核收。 |
| 5 突變帳本摘要 | [mutants_results][mutants]；[原生階段紀錄][stage]；各切片具名負控 | 帳本現有42 killed/1 crashed/4 equivalent/3 retired；47項執行來源是 `bbc59d4022feccb70ff3277b6f63dad912faa643`，不能冒稱目前來源。需最終整份重產與 `--check` exit0；本次未跑。 |
| 6 實際驗證 | [採納收據][adoption]、[歷史P0][validation]、[架構收據][archreceipt]、四包 immutable P1、599 RED原始結果／corrected closeout與外部catalog | 每筆寫 source SHA、裁判、命令、exit、pass/fail/skip、範圍；跨SHA方法聯集不可改稱同版全過。 |
| 7 未驗／風險 | 本文件開頭與 §4–6；[BACKLOG GEO-261][backlog] | coverage false、599 RED、4aec queued C0/method0、default八題UNRUN且未入整合；mutation／finalarch、相容／完整專案／全量裁判／七job／25入口仍待實跑；Claude OAuth expired、最終review未完成。 |
| 8 使用者拍板原話 | [決策佇列:45][decisions]、同檔46、50；[APPROVAL][approval] | 「批准此版本的逐條提案」綁17a25；「批准此更名缺陷修正」獨立；「批准此追加分層提案」綁c8ce964。不把實作授權擴成驗收通過。 |

## 4. 證據狀態與不可跨越的版本界線

| 收據來源 | 真正支持的結果 | 不能推出 |
|---|---|---|
| 採納 A `e744f5316fd7c896275bdee4c34ad22ae97d9d8e`，結果見 ADOPTION JSON | reader51、proposal29、adoption15、pure compatibility4；原生compatibility10 UNRUN；唯一reader有桌面/390px瀏覽器紀錄 | native解耦、完整gcanvas、最新整合通過；390px不等於實體手機 |
| 架構 `4a13551cc8aac3e116b53486fe44637c07374d49` | 573檔清冊、332 owned、796edges、0diagnostics、product18/18；generic205為204pass+1Windows權限skip的同裁判歷史重用 | 該歷史清冊已由下列47d有限刷新取代；兩份都不能冒用為目前4330527通過 |
| 後續靜態刷新 `47d3bb4bcccddeeb034dd5899a7aa15c9cab0768` | 576檔＝332 owned＋244 exact exclusions；796edges、0diagnostics；真CLI exit0、原18項全過無skip；3個新SP accessor負控另計；generic205仍僅歷史重用204pass＋1skip。receipt LF SHA256 `a4166fd433cb9477e87756f635b5491d5dfe457035974b10b03d6b33ddc676e7` | 不證明native／runtime／browser／#289；刷新提交為277bfdd3b477491c97f3d56b357ed7d782e3c71c，封存source仍為47d。第四包新增5個Python helpers/copies，當前清冊仍待final refresh |
| `15187e71fd9d5f645a63752ea744020df8abbfcf` | 5stage gatePASS；0PASS/4FAIL/57UNRUN，4failure events | 全61項通過 |
| `18edda3f2f4c08b5d7b192077637d16ce04940e6` | 5stage gatePASS；61PASS | 259同SHA通過；259索引是8來源SHA聯集 |
| `de62cd680d2cbc71df0becc111bc071c490eeb9b` | 5stage gatePASS；37PASS/4FAIL/189UNRUN；6failure events | 6個失敗方法；diagnostic exit0也不能翻轉FAIL |
| `f22dcccc5681418f99e5a55e60ef558e71dd0b31` | 5stage gatePASS；52PASS/2FAIL/166UNRUN；Parameter20/SP15全過，Version19為17過2失敗 | 後續H123、#279目前head或#288通過 |
| `fa5deb703152e2120e0a3b039b482f4d6f4f4754` | 5stage gatePASS；17PASS/2FAIL/257UNRUN。兩個負控原先因合法五行preview前綴被裁判拒絕；原stderr可精確重建，未保留stdout仍是缺口 | 不能翻轉原RED；599只修裁判後仍須新執行 |
| 599 RED `599f3414d333967dbd6c538a3ea50d1ac5b1baa6` | 計畫276／實跑37：Version19全PASS、HostAuthority18＝17PASS/1FAIL；36PASS/1FAIL/239UNRUN、exit1；外部corrected closeout保留原結果。五階段gate明示REUSED-fa5，599新gate執行0 | 不證明完整276、coverage、#288或default通過；不屬第四包 |
| 最新#279 `4aec7f428b9307ed9596aba2ed893175b8db76a5` | 只補harness的正常ctx.wanted／live-context初始化；原three-footprint、+17投影、hit count／anchor oracle與方法數保留。fresh-five在共享鎖排隊，C0／method0；276未啟動 | 修正原始碼不是修正後PASS；不翻轉599 RED |
| Python default `f3c71065a62f2f961a26367c04216c01377383c3` | 12suites/174PASS，合成envelope及mock process boundary | #289新8個真native/default測試通過；目前#289 complete coverage |

目前 [model_sources.inc:385][modelsrc] 仍輸出 `coverage.complete=false`；[engine.py:14][engine] 仍以 `native_loader=load_base` 裝配，沒有採用 #289 default。只讀兩個固定commit的 `run_all.expected.json`：4330527 integration 是 **205 suites／4,434 counted mixed-unit checks／6 exit-only suites**；8f36 default 分支為 **206／4,449／6**，後者才是合入後預期基數，最終仍依凍結來源清冊核對。**4,449 不是方法數**：其合計包含 test、C 檢查點、場景及 assertions 等不同單位；兩份都是清冊，不是實跑結果。P0歷史基準88 suites／2827 counted，P0候選89／2856；該P0 WSL當時未持共用排他鎖，不作正式列車通過證據。不同階段的計數與測試含義不得直接相減當回歸涵蓋率。

### 4.1 四包 immutable P1、599 closeout 與4aec待跑狀態

四包見 [P1 index][p1index]：original 24 receipts、follow-up 4、authority-source 22、closed-batch 12。這些是已完成歷史收據的保存數，不能相加當同來源產品測試數。第四包 [README][closeouts]／[CONTENT-MANIFEST][closeoutmanifest] 記錄 **370 logical originals／295 blobs／99,518,011 original bytes／79,097,380 unique bytes**；前三包393個已封存檔不變。主協調者轉述原owner確認：seal後確實實跑並保有tool transcript，主驗證時間為`2026-10-16T23:33:01.082871Z`、exit0、`packageFilesVerified=67`／`packageSealChecked=true`；獨立驗證為`2026-10-16T23:33:01.007806Z`、exit0，另有child 11/11 PASS，涵蓋370原件／295 blobs／前393檔不變。本次只讀核對檔案數字並引用此執行回報，沒有重跑驗證。該兩次未使用`--report`，**沒有另外的machine-readable收據檔／hash**；包內`VERIFICATION.json`仍是封印前讀回（0／false）。不得虛構外部收據路徑，或把封印前檔冒充封印後；若日後另存新驗證收據，應保留其新時間，不倒填。封包一致性不證明產品驗收。

第四包保留15187／18ed／de62／f22／fa5五次focused的原FAIL／UNRUN與兩次診斷。fa5的431及407-byte stderr由既有Python string literals精確重建，只是舊收據分析；成功baseline的stdout／stderr與負控stdout沒有保留，不能補稱已核對。diagnostic wrapper exit0僅代表捕捉完成；de62各case及f22原inventory仍exit1。fa5 build-gate的launch.ps1雖保存，舊runner hash map沒有它的執行時anchor。watchdog兩輪與啟動時來源缺口續見§7，均不得因封包驗證通過而消失。

後續另有**新時間的新驗證收據**：[sealed readback 2026-10-17][sealedreadback]，由root在d4b22重新執行一致性驗證後保存，`checkedUtc=2026-10-17T00:06:56.400461Z`、exit0／`ok=true`，370原件byte comparison、295 blobs、2,673 source hashes、393前包檔、67 sealed files、seal=true。原檔SHA-256為`7340471280223d4854790f19a76bd29622408eb0a484b804177d6288fdb1ee02`；本次只讀並計算此檔hash。這不倒填23:33的兩次transcript、不替換包內封印前收據、不洗去歷史FAIL／缺口，也沒有執行產品測試（`productTestsExecuted=false`）。

當前架構清冊待納入的五檔都在 `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/`：`prepare_publication.py`、`finalize_publication.py`、`extract_evidence.py`、`verify_publication.py`，以及 `readable/watchdog-envelope-v1/recovered-selftest-source-868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac.py`。即四個helper與一個歷史來源副本；加入排除清冊仍需逐檔雜湊，不能泛列整個目錄排除。

599的外部[corrected closeout][native599closeout]已存在；它只修正原closeout將「planned276」寫成「executed276」的limits句，原檔及36PASS／1FAIL／239UNRUN保持不變，尚未納入第四immutable包。原[test-result.json][native599result]／[unittest.log][native599log]記錄`first-failed-group-completed`、1 failure／0 errors，失敗方法為`tests.test_geo261_host_authority.HostAuthority.test_panel_support_projects_actual_member_boxes_without_authoring_changes`，baseline executable回1、預期0，訊息`ASSERT:host-pf-footprint-baseline`；不算mutation killed、預期拒絕或環境skip。原五階段gate明示沿用fa5，599新gate執行0，不補稱fresh。

既有[diagnostic cases][native599diagnostic]顯示三個member的`wanted=0`使baseline提早失敗；`062e2f351988e7a444d80e5639aa90d7ea1722a3`只在harness補正常reference_rebuild初始化並合入#279 `4aec7f428b9307ed9596aba2ed893175b8db76a5`，沒有改產品或原oracle。新[preparation][native4aecprep]與[276計畫][native4aecplan]限定22 modules／276 methods（41 portable＋235 native）。截至00:53:37Z，[shared-lock.log][native4aeclock]仍waiting、holder PID433／`train18p157-formal-r2`；fresh-five與focused兩個result summary均不存在，**C0／method0，276尚未啟動**。排隊及準備檔mtime不是執行起訖，也不是PASS。

### 4.2 default 八題與 browser tool v2 的證據界線

#289 的 `tests/test_geo261_default_native.py` 在8f36已加強：真正public loader只產生一個candidate；真正K evaluator收到同snapshot identity、全部source keys／types／contexts／dependencies／statuses，並核對legacy_snapshot未被改動；舊legacy路徑在observer中拒絕，獨立legacy比較在observer外。它觀察真native輸出，沒有替換正向envelope；但八題**尚未實跑**，需要完整native coverage及fresh同源binary，0 skip才可核收。舊f3c的174項只支持synthetic envelopes與mock process boundary，不能冒用。

[十個原始專案driver][browserreadme] 已備妥，tool v2既有純檢查18 resolver＋23 comparator與語法通過；[工具更新紀錄][toolv2] 明列沒有import真實Playwright或執行browser/native/WSL。實際選用既有Playwright-core 1.62.1、顯式套件路徑與Chrome，並釘選完整工具依賴閉包；準備成功不是runtime相容證明。原firstprep收據與review保持不變。
### 4.3 本次已完成的準備，尚非產品驗收

- `43305271770760a690e360ce18ce11cc07f35ea2`只修四個browser launcher：multi／rule-app／rule-races讀`GEOMETRY_CHROME`，ResizeObserver讀空白分隔`GEOMETRY_CHROME_FLAGS`。主協調者回報四支Node syntax、diff check及獨立read-back通過；defaults、assertions、count、timeout及隔離檢查不變，**尚無browser實跑結果**。
- [Python Playwright v2準備][pypwprep]為PREPARED：1.62.0＋greenlet3.5.6＋pyee13.0.1＋typing_extensions4.16.0；wheel官方SHA先核對、外部venv離線安裝及pip check通過。原1.62.1不可取得的v1失敗保留，Node Playwright仍為1.62.1，兩者分開記錄。
- [system Python map-check v2][pypwmap]在00:46:34.857552Z→00:46:36.199384Z exit0：`/usr/bin/python3` 3.12.3以程序限定`PYTHONPATH=/var/tmp/geo261-python-playwright-1.62.0-v2/venv/lib/python3.12/site-packages`匯入5 module、核對4 package版本；**沒有start Playwright driver／browser／產品測試，也沒有驗未來private namespace的python alias**。先前map-check-v1因外部probe命名`inspect.py`遮蔽stdlib而失敗，原結果保留。prep summary SHA `da1d6f6eb795cb5a9c290e23cf01b5985243980aa0d3d3f3cf977d26b3b9ff3a`；map summary SHA `8bef59faa0e05781d104e601d32d6024dd8df951fcbdc138a5132d6f06b5cdbb`。
- [25入口命令表][ownergatecommands]已完成並經獨立讀回：1 owner＋22 browser＋fragment-heap與grid-inspector兩診斷，含新服務、TEMP、輸出、session與exit保留；**全部是待執行命令**。本次不覆寫該表或其他driver。
- [final architecture driver][finalarchdriver] SHA `28d19479d6615f03cc9542571b98eb3b6d2dd62ccc808747ac10e7073ebb071c`已備妥；需完整最終SHA及新外部目錄，依`before → refresh → product_tests → report → seal`。AST／語法／純helper正反例及獨立文字審查屬準備檢查，沒有執行任何stage／scanner／18 product tests；generic仍僅歷史204PASS＋1skip，不新增probe。

## 5. 正式 native＋六 browser jobs 的命令映射

真實來源為 [integration-tests.yml][ci]（native:16–27；matrix:29–50；commands:116–121），[RELEASE-CANDIDATE 驗收矩陣][release] 與 [INTEGRATION-GATES][gates]。以下只是列出現有命令，**本次均未執行；最新完整候選的七項收據尚缺，正式七項train維持Claude原分工**。

| job | CI 實際命令（Linux） | 範圍／交付限制 |
|---|---|---|
| native | `ulimit -s 16384` 後 `python3 tests/run_all.py --build` | 全部登錄非browser；具名Windows GDI例外分列；不是全部owner/browser驗收。 |
| browser (assembly) | `GEOMETRY_CDP_PORT=9367 GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js` | 組構專項，partial，不是full canvas golden通過。 |
| browser (grid) | `GEOMETRY_CDP_PORT=9334 GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` | 格網專項，partial；不能替代完整來源保存鏈。 |
| browser (canvas) | `node geometry-web/cdp_test.js` | 無ONLY旗標的full；必須completed/scope及逐段golden一致；含P72B更名。 |
| browser (space) | `GEOMETRY_CDP_PORT=9347 node geometry-web/space_model_test.js` | full-space-suite：height/library、projection lifecycle/placement/close、font-layout、space-flow；不是timber專項。 |
| browser (timber) | `GEOMETRY_CDP_PORT=9348 GEOMETRY_TIMBER_ONLY=1 node geometry-web/space_model_test.js` | timber-material、timber guards、font-layout；與space獨立列結果。 |
| browser (documents) | `GEOMETRY_CDP_PORT=9366 node geometry-web/documents_browser_test.js` | 真文件入口／唯一正典／既有World及draft保全；不等於reader CLI assert。 |

CI共用前置：`npm run build` 實際為 `python3 geometry-web/start_local.py --build-only`（native build，不是新閱讀器產物）；自有18839服務、TEMP feedback/screens、Chrome與中文字體；`runtime_version.py --probe 18839` 必過。WSL canvas另保留wait trace，其他job清除其旗標。現有CI timeouts分別native15min、assembly15、documents10、grid15、canvas35、space15、timber20；這些是既有設定，不是本計畫放寬或承諾可在時限內完成。正式本機WSL由驗收owner使用既有共用鎖排隊，不依GitHub矩陣的max-parallel=2擅自並跑。

## 6. 已界定25入口的額外 gate 準備

來源為[run_all.py][runner]的`REQUIRED_OWNER_GATES/REQUIRED_BROWSER_GATES`及既有兩個native診斷；完整待執行命令見[25入口命令表][ownergatecommands]。本次只刷新這個已界定的1＋22＋2範圍，不擴展其他`NODE_EXCLUDED`或另寫driver。六個CI browser jobs與十項原始專案driver均沒有呼叫這22支相同入口，不能因Save/Open路徑相似就去重；P72B本身已在full CDP，另記第二native服務需要。括號為登錄assertion數，不是實跑數或端到端場景數。

| 類別／既有入口 | GEO-261 關聯與缺證 |
|---|---|
| K2a drafts(27)、native(42)、source repin(14)、ZIP(89)、rule repin(35)：`tests/k2a_*_browser.cjs` | 直接關聯source keys、定義／值、候選、失效與刪後重建。新來源完整ZIP、第二空服務冷重開尚缺；ZIP gate需額外 `GEOMETRY_FRESH_TEST_URL`。 |
| Q38 `test_section_profile_browser.js`(68)、`integration/q38_save_roundtrip.py`(18) | 直接關聯SP來源與default模型。需真正typed source、mesh、preview/cancel、定位轉換、全新process／chooser重開；不能用pure相容4項代替。 |
| `integration/model_library_history_browser.py`(35)、`integration/save_roundtrip_acceptance.cjs`(33) | 直接關聯模型接線、完整World/草稿/history/保存。download fallback不冒稱OS Save picker。 |
| room multi-candidate(34)、outline keyboard(396)、acceptance(253)、pan(32)、worker(78) | K region/enclosure及H candidate/World變動有直接或回歸關聯。區分真UI與API夾具／晚回覆故障注入，補同源dump、來源／附件、冷ZIP。 |
| rule-case standalone browser(91)、正式app(76)、races(30) | standalone服務沒有`/runtime`，不能用release_gate包裝或借別的服務背書；正式app與races另列。 |
| grid-rule reader(34)、`grid_raw_provenance_browser_test.py`(207) | 直接關聯格網authored bytes、pin／失效／重綁／相位差來源；不能以數值相同替代來源身份。 |
| `evidence_links_browser_check.js`(67)、`evidence_links_integration_test.js`(110) | 前者injected backend adapter，後者正式PDF/ZIP/history；H保存與source identity相容相關，兩者不可互換。 |
| `feedback_resize_observer_test.js`(38) | 間接關聯runtime/source freshness及錯誤保全；不是K幾何測試，不能因七job完成而自動計過。 |
| `integration/issue77_attachment_owner.js`(5) | repo已有真實`wp60_actual_owner_adapter.js`，可用最終own source自行啟動服務；缺adapter是pending失敗，不算skip/pass。 |
| P72B `grid_inspector_rename_test.js` | 已由full CDP載入；但另一原生程序重開需另設 `GEOMETRY_GRID_RENAME_FRESH_URL`，未設只證新JS context。 |

兩個native診斷均列入25入口：`grid_inspector_mutation_probe.py --native`需原版／恢復綠、兩個變異為真assertion紅，不能以setup error替代；INTEGRATION-GATES §#211/#217 的 `ulimit -s 16384; python3 tests/diagnostics/run_fragment_heap_gate.py --output <新外部目錄>` 不包含在run_all數量。H reference/candidate實作移動涉及它的指紋／OOM原子性，不能用舊binary收據自動沿用。`geometry-core/framing-template/oracle/` 目前checkout不存在；不宣稱執行過其selftest，也不移動／重建Claude分支內容。

所有後續收據須由驗收owner在自有服務／TEMP／profile記錄完整命令、head/tree、裁判／binary、runtime fresh/root/session/PID及raw結果。[release_gate.py規約][gates] 提醒native檔案收據不直接證明正在執行的process，仍需核對服務。這是既有收據要求，並未啟動任何服務或驗收。

## 7. 後續封包的 watchdog 限制

兩輪原始自測均須保留：首輪9項／1failure，次輪9/9。舊selftest來源已恢復為 [recovered-selftest-source][recovered]，SHA `868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac`。**恢復的bytes只對應首輪結束時磁碟SHA，不能證明執行開始時載入的bytes**；不得藉恢復檔把這項缺口轉成執行時完整來源證明。兩輪缺suite逐方法log，首輪失敗方法無法可靠還原；四項parser與sentinel存活僅受聚合摘要支持。60分鐘是外層watchdog設定，自測為短時間合成案例。先前外部catalog是恢復前快照；最終封包須顯式增補恢復檔與限制，不能靜默覆寫歷史收據。

## 8. 封版與正式交付仍待完成的次序

1. 保留599原RED及corrected closeout，在4aec修正後先完成fresh-five與coverage所需的同源全驗；fresh-five仍排隊、276未啟動，不能預先啟用coverage。
2. coverage全驗完成後才啟用producer；核收#289八題真C→default及必要同源相容結果，再將#289一般merge入integration。舊174項mock結果不能代替；此步未完成，不預填最終SHA。
3. 在合入default後的最後來源重新產生整份mutation並完成原`--check`，執行已備妥的final architecture driver／18 product tests；保留generic歷史204PASS＋1skip界線。將ledger／final manifest綁定source/tree、binary、工具、fixtures與裁判，不把準備物寫成PASS。
4. 依同一最終來源完成exact full aggregate（目前合入後預期206 suites／4,449 mixed-unit counted checks／6 exit-only，最終再核）、PF3／SP待驗controls、正式native＋六browser jobs及已界定25入口；FAIL／SKIP／UNRUN逐項保留，不能用跨SHA聯集代替。
5. 完成固定舊來源`a898ad6e12707104568679591fe1b21804bfc3df`對最終candidate的354 native inputs與375 format/package comparisons；十個原始專案兩版本browser為20 scored original Opens、20 saved-copy cold reopens、兩負控，另20 sentinel setup Opens不計通過。完整附件／草稿／來源與fresh sessions須保留；其餘139個`.gcanvas`未由此browser gate覆蓋。
6. 完成上述coverage全驗→啟用→merge default→mutation/finalarch→exact aggregate/fixtures/browser後，才進Claude最終review。目前OAuth expired且review未完成；待其對最終內容／證據無阻擋，才具備「只差排列車」的交付條件，再重取24個ours heads／順序並在#248發布八項交付。本次不發GitHub進度或交付。
本次未解項：4aec fresh-five與276仍未開始，coverage未啟用、default未合入；finalarch driver／25入口命令與Python import-only PASS都不是產品收據。最終mutation／aggregate／舊檔／browser／Claude仍缺同源完成證據。`final-fixture-reopen-plan.md`內舊b53147a5範例仍是歷史準備指令，正式執行要換尚未凍結的最終完整SHA；本次只刷新兩份交付快照，其他命令表、driver與原始收據原樣保留。
[ks]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/source.h
[wd]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/definition_sources.h
[wg]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/grid_sources.h
[we]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/engineering_sources.h
[kc]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/candidate.h
[kdoc]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/document.h
[wdoc]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/document.h
[kg]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/geometry.h
[wcontact]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/contacts.h
[wstop]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/supports.h
[kgrid]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/grid.h
[wga]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/grid_application.h
[kv]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/version_sources.h
[wf]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/frontend.js
[ha]: D:/geometry-axiom-work/geo261-integration/geometry-app/application.js
[rect]: D:/geometry-axiom-work/geo261-integration/geometry-templates/rectangular-grid/rectangular_grid.h
[proposal]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/PROPOSAL.md
[architecture]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md
[approval]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/APPROVAL.json
[adoption]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/ADOPTION-RECEIPT.md
[clausemap]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/clause-map.json
[addendum]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/merge-addendum.json
[archreceipt]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/product-architecture-receipt.json
[rectreadme]: D:/geometry-axiom-work/geo261-integration/geometry-templates/rectangular-grid/README.md
[fixtures]: D:/geometry-axiom-work/geo261-integration/tests/fixtures/domain-decoupling-main-a898ad6e/PROVENANCE.md
[runbook]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/ADOPTION-RUNBOOK.md
[mutants]: D:/geometry-axiom-work/geo261-integration/tests/mutants_results.json
[stage]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/NATIVE-STAGE-CHECKPOINT-20261016.md
[validation]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/VALIDATION.md
[backlog]: D:/geometry-axiom-work/geo261-integration/BACKLOG.md:329
[decisions]: D:/geometry-axiom-work/geo261-integration/決策佇列.md:45
[modelsrc]: D:/geometry-axiom-work/geo261-integration/geometry-app/native/model_sources.inc:385
[engine]: D:/geometry-axiom-work/geo261-integration/geometry-core/modeling/engine.py:14
[ci]: D:/geometry-axiom-work/geo261-integration/.github/workflows/integration-tests.yml
[release]: D:/geometry-axiom-work/geo261-integration/geometry-web/docs/RELEASE-CANDIDATE.md:56
[gates]: D:/geometry-axiom-work/geo261-integration/tests/INTEGRATION-GATES.md
[runner]: D:/geometry-axiom-work/geo261-integration/tests/run_all.py:306
[recovered]: D:/geometry-axiom-work/geo261-evidence/p1/watchdog-envelope-v1/recovered-selftest-source-868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac.py
[wmember]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/members.h
[kregions]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/regions.h
[wboundary]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/boundary_policy.h
[wdomain]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/domain_values.h
[kplacements]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/placements.h
[wfinish]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/finish.h
[wderived]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/derived_placement.h
[wobstacles]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/obstacles.h
[wvalidation]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/world_validation.h
[kenclosure]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/enclosure.h
[kgraph]: D:/geometry-axiom-work/geo261-integration/geometry-core/geometry_kernel/graph.py
[wmodelpolicy]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/geometry_woodworking/model_policy.py
[ktypes]: D:/geometry-axiom-work/geo261-integration/geometry-core/geometry_kernel/types.py
[wsection]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/section_profile.h
[kpygeometry]: D:/geometry-axiom-work/geo261-integration/geometry-core/geometry_kernel/geometry.py
[wpysection]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/geometry_woodworking/section_profile.py
[kclip]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/clip.h
[wpanel]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/panel_layout.h
[wengineering]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/engineering.h
[kgridstore]: D:/geometry-axiom-work/geo261-integration/geometry-core/kernel/grid_store.h
[wcutlist]: D:/geometry-axiom-work/geo261-integration/geometry-templates/woodworking/native/cut_list.h
[cuttingreadme]: D:/geometry-axiom-work/geo261-integration/geometry-core/cutting-plan/README.md
[p1index]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/evidence/NATIVE-P1-INDEX.md
[closeouts]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/README.md
[closeoutmanifest]: D:/geometry-axiom-work/geo261-integration/geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/CONTENT-MANIFEST.json
[native599result]: D:/geometry-axiom-work/geo261-evidence/p1/focused-599f3414-successor276-v1/result/test-result.json
[native599log]: D:/geometry-axiom-work/geo261-evidence/p1/focused-599f3414-successor276-v1/result/unittest.log
[browserreadme]: D:/geometry-axiom-work/geo261-evidence/p1/fixture-reopen/browser-originals/README.md
[toolv2]: D:/geometry-axiom-work/geo261-evidence/p1/fixture-reopen/browser-originals/PREPARATION-TOOLING-V2.md
[sealedreadback]: D:/geometry-axiom-work/geo261-research/native-p1-closeouts-sealed-readback-20261017.json
[native599closeout]: D:/geometry-axiom-work/geo261-evidence/p1/closeout-599f3414-corrected.json
[native599diagnostic]: D:/geometry-axiom-work/geo261-evidence/p1/diagnostic-599-host-v1/result/cases.json
[native4aecprep]: D:/geometry-axiom-work/geo261-evidence/p1/successor-4aec7f42-preparation.json
[native4aecplan]: D:/geometry-axiom-work/geo261-evidence/p1/plan-4aec7f42-276.json
[native4aeclock]: D:/geometry-axiom-work/geo261-evidence/p1/build-gate-4aec7f42-v1/shared-lock.log
[pypwprep]: D:/geometry-axiom-work/geo261-evidence/p1/python-playwright-prep-v2/result/summary.json
[pypwmap]: D:/geometry-axiom-work/geo261-evidence/p1/python-playwright-map-check-v2/result/summary.json
[ownergatecommands]: D:/geometry-axiom-work/geo261-research/final-owner-gates-commands.md
[finalarchdriver]: D:/geometry-axiom-work/geo261-research/refresh_product_architecture_final.py
