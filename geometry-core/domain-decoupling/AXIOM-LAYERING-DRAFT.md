這是草稿，待使用者看稿；看稿前不改公理層。

基準是 `origin/main` `f6a1589153ce1f910cbec5d705b5b3bf9df6488d`。
`公理層.md` 先把 CRLF 換成 LF 後的 SHA-256 是 `7794a7782ea87347c8b1b2f3721287c954ee3a3fa74caab570f87f066d1f892d`。
分類 207 條。核心 66、木工 37、混合 104。

## 讀了什麼

指定的 `geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md` 在這份 main 上不存在，目錄裡也沒有這個檔名。分層定義改讀同目錄的 `PROPOSAL.md` 第 2 到第 4 節，以及公理文首的「分層契約」。
指定的 `tests/axiom_matrix.py` 不存在。診斷器是 `geometry-guide/axiom_matrix.py`。它只把 `current_geometry.c`、場景註解和 `tests/mutate.py` 的條號當成弱代理，不標 K、W、H 檔。
本表的程式落點用同一種條號搜尋掃產品檔，再依目錄歸成未拆單體、偏 K、偏 W、偏 H。條號出現不等於那一支函式實作了整條。沒有條號也不等於沒做。`geometry-core/domain-decoupling/` 裡的提案 JSON、證據日誌，以及測試和場景，不計入落點。
`clause-map.json` 的狀態是 `proposed-not-approved`，基準舊於現稿，而且少了 D64、I74、R60。本表不以它為準。

## 使用者要解耦的那一句

決策佇列「2026-10-12～15 使用者後續拍板」第 1 項，以 `>` 開頭的那一行，逐字如下：

> 這些可以存在裡面 但是是能夠解耦 並且是第一個被套用的部份

本表按這句來標。木工條文可以留在公理層，前提是拆得開，而且是第一個被套用的模板。核心指拿掉木工模板仍然成立的規則。它包含公理自標的 K，也包含沒有木工政策的宿主機制。所以本表的「核心」不等於 GEO-261 的 K。宿主條文若只是保存木工結果，標木工；若同一條裡又有機制又有木工白名單，標混合。

## 怎麼標

- 核心：領域無關。任何模板都成立。
- 木工：只對木工模板有意義。例如角材角色、主支、副支、端面優先級、板縫配方、鋸切視圖。
- 混合：同一條裡有核心骨架，也有木工內容，要拆成兩段才解得開。
- 公理文首已經自標 K 31、W 30、M 95、H 51。本表把這四種收成上面三種，不一致寫在最後一欄。
- 已有「核心契約」和「木工模板契約」兩段的條文，分類沿用這兩段，不另寫一套幾何。拆條號、策略旗標、身分帳涵蓋擴張，寫在文末「新方案」，不放進分類表。

## 分類表

最後一欄的詞：

- 木工內容的條號在未拆單體：`current_geometry.c` 仍點到這條。紙上拆開，程式還沒有模板邊界。
- 產品碼無條號：產品檔沒有這條條號。可能尚未實作，也可能做了但沒寫條號。
- 公理自標 H 或公理自標 M：本表的三種分類和公理文首的四種標籤不同。

這一輪，木工或混合且條號在未拆單體的有 64 條。產品碼無條號的有 38 條。

<!-- CLASSIFICATION-TABLE-START -->

| 條號 | 分類 | 公理自標 | 理由 | 程式落點 | 不一致 |
| --- | --- | --- | --- | --- | --- |
| D1 | 核心 | K | 整數毫米右手座標，任何模板都用同一套相等比較。 | 未拆單體 current_geometry.c；偏K grid_bindings.inc、grid_lattice.inc、grid_subdivision_query.inc（共13個）；偏W assembly_generation.inc、derived_placements.inc、engineering.inc（共6個）；偏H app.css、app.js、section_profile_diagnostics.inc（共4個） | — |
| D2 | 核心 | K | 有向平面框架是座標轉換，不認得材料或角色。 | 未拆單體 current_geometry.c；偏K modeling/geometry.py；偏W finish_surface_types.h、finish_surfaces.inc；偏H app.css、app.js、index.html | — |
| D3 | 混合 | M | 空間邊界面（SpaceBoundarySurface)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/geometry.py；偏W finish_surfaces.inc；偏H app.js | 木工內容的條號在未拆單體 |
| D4 | 混合 | M | 承載面（PlacementSurface)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/geometry.py、references.inc、section_profile_placement.inc；偏W derived_placements.inc、engineering.inc、finish_surface_types.h；偏H model_update.py、space_modeling.py、web_bridge.c | 木工內容的條號在未拆單體 |
| D5 | 混合 | M | 空間（Space)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| D12 | 核心 | H | 畫布座標只是顯示位置。類別裡的 boundary 是物件種類，不是角材角色。 | 未拆單體 current_geometry.c；偏K model_base.c、transactions.inc | 公理自標H |
| D6 | 混合 | M | 參考線（GuideLine)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc；偏H app.js | 木工內容的條號在未拆單體 |
| D6a | 混合 | M | 局部參考線位置的引用式前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K reference_types.h、references.inc；偏H app.js、source-inspector-bridge.inc | — |
| D6b | 混合 | M | 具名規格常數（SpecValue)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K reference_types.h、references.inc、section_profiles.inc | — |
| D6c | 核心 | K | 共用基準面是跨面的幾何參照，不是木工物件。 | 偏K reference_types.h、references.inc；偏H reference-ui.js | — |
| D7 | 混合 | M | 角材（Timber)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/geometry.py；偏W framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py、framing-template/core-probe/scene_reader.py（共4個）；偏H space_modeling.py | 木工內容的條號在未拆單體 |
| D8 | 混合 | M | 邊（SurfaceBoundaryEdge)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| D9 | 混合 | M | 定義與衍生值分開是核心；角材不存八角、材料版本算定義，是木工白名單，要拆出去。 | 未拆單體 current_geometry.c；偏K references.inc | 木工內容的條號在未拆單體 |
| D10 | 混合 | M | 參考網格（ReferenceGrid)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K subgrids.inc；偏H app.js | 木工內容的條號在未拆單體 |
| D10a | 混合 | M | 面材排法（PANEL_LAYOUT）的格線前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏W panel_layout_math.h；偏H app.js、prototypes/engineering-spec/tests/catalog.test.mjs | 木工內容的條號在未拆單體 |
| D11 | 混合 | M | 已有 K/W 兩段。K 對每個候選驗完整帶寬，並拒絕部分覆蓋與兩個平面拼成一個端面。W 列出三種來源。候選是否必須唯一寫在 R6，與這條的全寬不是同一件事。 | 未拆單體 current_geometry.c；偏H timber_support_projection.inc | 木工內容的條號在未拆單體 |
| D13 | 混合 | M | RC 柱（RcColumn)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K model_base.c | 木工內容的條號在未拆單體 |
| D14 | 混合 | M | RC 樑（RcBeam)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K model_base.c | 木工內容的條號在未拆單體 |
| D15 | 木工 | W | 角色名稱、優先級表和柱面等於 0 只服務木工角材。整條是木工，現行沒有另寫的核心段。 | 未拆單體 current_geometry.c；偏W framing-template/core-probe/gen_scenes.py；偏H app.js、web_bridge.c | 木工內容的條號在未拆單體 |
| D16 | 混合 | M | 同一直線上的區間差是核心；固定段必須蓋住外輪廓 FIXED 邊、延伸段算離開 RC，是木工。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| D17 | 木工 | W | 主支軸由 primary 與 boundary 的方向定義，離開這兩個木工角色就沒有對象。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/gen_scenes.py；偏H app.js | 木工內容的條號在未拆單體 |
| D18 | 混合 | M | 擋面參照（StopFaceRef)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc | 木工內容的條號在未拆單體 |
| D19 | 混合 | M | 子網格（Subgrid）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/base.py、subgrid_commands.inc、subgrids.inc；偏H app.js | 木工內容的條號在未拆單體 |
| D19a | 核心 | M | 來源子規則是精確等分與穩定引用。公理標 M 是因為同條有宿主段落，那段沒有另一套木工政策。 | 偏K grid_subdivision.inc、grid_subdivision_query.inc；偏H grid-rule-lines.js | 公理自標M |
| D20 | 核心 | K | 正交擠出是幾何。文首寫明這組正交實體尚未實作於現行 C 核心或物件畫布。 | 偏K modeling/engine.py；偏H space_modeling.py | — |
| D21 | 核心 | K | 有向邊界殼是幾何。purpose 的 boundary 是邊界用途，不是角材角色 boundary。 | 偏K modeling/engine.py、modeling/geometry.py；偏H space-workspace.js、space_modeling.py | — |
| D22 | 混合 | M | 複合空間（CompositeSpace；orthogonal-model/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/engine.py；偏H space-workspace.js、space_modeling.py | — |
| D23 | 核心 | K | 實體組合的 base 與 tools 是布林角色，不是角材的 primary／secondary。 | 偏K modeling/engine.py、modeling/geometry.py | — |
| D24 | 核心 | H | 建模請求的完整性是交換契約。這裡的角色是請求結構，不是角材角色。 | 偏K modeling/engine.py；偏H space_modeling.py | 公理自標H |
| D25 | 核心 | H | 建模交換包是宿主的封裝。正交模型尚未在 C 核心與畫布實作。 | 偏K model_base.c、modeling/__init__.py、modeling/base.py（共5個）；偏H modeling_cli.py、serve.py | 公理自標H |
| D26 | 混合 | M | 材料版本（MaterialVersion；engineering-spec/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py；偏W engineering.inc、engineering_types.h | — |
| D27 | 木工 | W | 工程做法版本（MethodVersion；engineering-spec/1）離開木工模板就沒有對象。 | 偏W engineering.inc | — |
| D28 | 混合 | M | 面套用與尺寸來源（EngineeringApplication / DimensionSource；engineering-spec/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py、transactions.inc；偏W engineering.inc、engineering_commands.inc、engineering_types.h | — |
| D29 | 混合 | M | 獨立網格系統（GridSystem)前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K grid_bindings.inc、grid_lattice.inc、grid_systems.inc（共4個）；偏W engineering.inc、engineering_commands.inc、panel_layout_math.h；偏H card_reference.inc、app.js、grid-system-workspace.js（共5個） | 木工內容的條號在未拆單體 |
| D10b | 混合 | M | 相鄰格子相位差（stagger）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K grid_bindings.inc、grid_lattice.inc、grid_systems.inc（共5個）；偏W panel_layout_math.h；偏H grid-system-workspace.js | 木工內容的條號在未拆單體 |
| D30 | 核心 | K | 網格配置保存錨點與帶符號 cell。這裡的 boundary 是輪廓頂點鍵，不是邊界材。 | 偏K boundary_vertex_keys.inc、grid_bindings.inc；偏H grid-system-workspace.js、grid_binding_bridge.inc、reference-ui.js | — |
| D31 | 混合 | M | 參數卡與欄位（ParameterSet / ParameterField；parameters/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K parameter_types.h；偏H parameters.js | — |
| D32 | 混合 | M | 構件分件與接合規則版本（AssemblyRuleVersion；assembly-rule-authoring/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W assembly.inc、assembly_types.h；偏H assembly_bridge.inc | — |
| D33 | 混合 | M | 組構綁定（AssemblyBinding；assembly-rule-authoring/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W assembly.inc、assembly_types.h；偏H assembly_bridge.inc | — |
| D34 | 木工 | W | 組構實例（AssemblyInstance；assembly-timber-generation/1）離開木工模板就沒有對象。 | 偏K modeling/__init__.py；偏W assembly_generation.inc | — |
| D35 | 核心 | K | 斷面是平面閉區域裡的幾何，本身不帶角材義務。 | 偏K model_base.c、section_profiles.inc | — |
| D36 | 混合 | M | 斷面構件（ProfileMember；section-profile/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K section_profiles.inc | — |
| D37 | 混合 | M | 拉伸件（ProfileRun；section-profile/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K section_profiles.inc | — |
| D38 | 混合 | M | 拉伸件定位（ProfilePlacement；section-profile/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K section_profile_placement.inc；偏H section_profile_transport.py | — |
| D39 | 核心 | K | 未定位拉伸件只表示還沒有宿主，任何模板都成立。 | 產品碼無條號 | 產品碼無條號 |
| D40 | 木工 | W | 面材規格（PanelSpec；section-profile/1）離開木工模板就沒有對象。 | 偏K model_base.c、section_profiles.inc | 木工條號在偏核心檔 |
| D41 | 混合 | M | 完成面（FinishSurface；panel-fill/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/__init__.py；偏W finish_surface_types.h、finish_surfaces.inc；偏H panel_fill_bridge.inc、web_bridge.c | 木工內容的條號在未拆單體 |
| D42 | 混合 | M | 面材試排（PanelFill；panel-fill/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W finish_surface_types.h、panel_fill_layout.inc | — |
| D43 | 混合 | M | 鋪排縫線與身分（panel-fill/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W panel_fill_layout.inc、panel_layout_math.h | — |
| D44 | 混合 | M | 承接門檻與結果（panel-fill/1）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K parameters.inc；偏W panel_fill_layout.inc | — |
| D45 | 木工 | W | 板縫上建議哪種角色的角材，是木工鋪排配方。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| D46 | 木工 | W | 鋸縫、修整與原材的裁切設定，離開加工視圖就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| D47 | 木工 | W | 原材種類（StockType；cutting-plan/1）離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| D48 | 木工 | W | 宣告餘料（DeclaredRemnant；cutting-plan/1）離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| D49 | 木工 | W | 計量世界與需求件（CuttingDemand；cutting-plan/1）離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| D50 | 木工 | W | 裁切方案（CuttingPlan；cutting-plan/1）離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| D51 | 核心 | H | 完整專案把一份世界和專案層資料包在一起，任何模板都要有專案。 | 偏K modeling/__init__.py | 公理自標H |
| D52 | 混合 | H | 附件容量是宿主機制；房間集合是建築模板的第一個領域物件，要拆開。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D53 | 混合 | H | 草稿這件事是宿主的；房間外環草稿是領域物件。 | 偏K modeling/__init__.py | 公理自標H |
| D54 | 混合 | H | 跨專案身分要分類，這是宿主；類別白名單把角材、面材、柱樑寫死，是木工型別表。 | 偏K modeling/__init__.py | 公理自標H |
| D55 | 混合 | H | 匯入的閉包與配號是宿主；閉包裡哪些木工定義可以走，是模板白名單。 | 偏K modeling/__init__.py | 公理自標H |
| D56 | 混合 | H | 未提交草稿是宿主；草稿內容寫到擋面和組構，是木工編輯。 | 偏K modeling/__init__.py | 公理自標H |
| D57 | 核心 | H | 網格編輯草稿保存的是格線來源，不是角材配方。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D58 | 木工 | W | 重複開間配置（BayRepeat；assembly-bay-repeat/1）離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| D59 | 混合 | H | 配號機制與受涵蓋清單寫在同一條。清單是現行七類，排除組構實例所有的角材，涵蓋域歸 H。本列不改這份清單。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D60 | 核心 | H | 存在期由一次提交的結果決定，與材料無關。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D61 | 核心 | H | 配號區段由宿主產生，核心不自己發號。這是身分機制。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D62 | 核心 | H | 身分引用與內容指紋用來對世界外的紀錄，不是木工政策。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D63 | 混合 | H | 保存模型是專案層快照；納入哪些角材與拉伸件是木工選擇。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| D64 | 核心 | K | 整張參數卡對到兩軸是來源綁定。2026-10-16 的分層追加把它放在共用核心，正文沒有木工政策。 | 偏K modeling/__init__.py；偏H card_reference.inc | — |
| I1 | 核心 | K | 承載面框架要合法，是框架幾何的守門，不是木工。 | 未拆單體 current_geometry.c；偏K modeling/geometry.py；偏W finish_surface_types.h、finish_surfaces.inc | — |
| I2 | 核心 | K | 邊界面輪廓是領域無關的幾何、來源或交易，任何模板都成立。 | 未拆單體 current_geometry.c；偏H app.js | — |
| I3 | 混合 | M | fixity 陣列長度 = 邊數；不寫 → 全 FIXED。前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏H parameters.js | 木工內容的條號在未拆單體 |
| I4 | 混合 | M | Space 建構前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| I5 | 混合 | M | 角材放置前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/__init__.py、references.inc | 木工內容的條號在未拆單體 |
| I6 | 木工 | W | 角材端面貼到輪廓邊時那一邊必須是 FIXED，是木工固定邊。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/parse_results.py | 木工內容的條號在未拆單體 |
| I7 | 混合 | M | 參考線有效性前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc | 木工內容的條號在未拆單體 |
| I7a | 核心 | K | 共用基準交線唯一性是領域無關的幾何、來源或交易，任何模板都成立。 | 未拆單體 current_geometry.c；偏K references.inc | — |
| I8 | 混合 | M | 原子候選交易是核心；依賴鏈寫死邊界面、參考線和角材，是木工物件圖。 | 未拆單體 current_geometry.c；偏K references.inc、subgrid_rebind.inc、transactions.inc；偏W engineering_commands.inc；偏H card_reference.inc、app.js、engineering_bridge.inc（共5個） | 木工內容的條號在未拆單體 |
| I8a | 混合 | M | 改動已被引用的來源要先預覽，這是核心；預覽單位寫死每一支角材和它的擋面，是木工。 | 未拆單體 current_geometry.c；偏K references.inc、subgrid_commands.inc、transactions.inc；偏W finish_surfaces.inc；偏H app.css、app.js、grid_binding_bridge.inc（共6個） | 木工內容的條號在未拆單體 |
| I9 | 混合 | M | DSL 順序即依賴順序前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K model_base.c、modeling/base.py、modeling/engine.py（共5個）；偏W framing-template/core-probe/parse_results.py；偏H engineering_bridge.inc、feedback_cli.py、model_update.py（共5個） | 木工內容的條號在未拆單體 |
| I10 | 混合 | M | 網格前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K grid_systems.inc、subgrid_commands.inc、subgrid_world.inc（共4個）；偏W engineering.inc、engineering_commands.inc；偏H app.js、engineering_bridge.inc、prototypes/engineering-spec/tests/catalog.test.mjs | 木工內容的條號在未拆單體 |
| I11 | 混合 | M | 實體不重疊前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc | 木工內容的條號在未拆單體 |
| I12 | 混合 | M | 錨法二選一前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc | 木工內容的條號在未拆單體 |
| I13 | 混合 | M | 錨法幾何約束前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K reference_types.h、references.inc；偏W framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py、framing-template/core-probe/scene_reader.py；偏H app.js、reference_bridge.inc | 木工內容的條號在未拆單體 |
| I14 | 核心 | H | canvas-pos 只要求物件存在，不重驗幾何。 | 未拆單體 current_geometry.c；偏K transactions.inc | 公理自標H |
| I15 | 混合 | M | 柱前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K model_base.c | 木工內容的條號在未拆單體 |
| I16 | 混合 | M | 樑前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| I17 | 混合 | M | 空間重宣告使推導範圍縮小 → 柱樑一併重驗，不過整筆回滾（I8 同軌）;前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| I18 | 木工 | W | 角色必填離開木工模板就沒有對象。 | 未拆單體 current_geometry.c；偏W framing-template/core-probe/parse_results.py | 木工內容的條號在未拆單體 |
| I19 | 木工 | W | 誰的端面可以頂誰，用的是邊界材、主支、副支和柱面這套木工優先級。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py、framing-template/oracle/framing_oracle.py（共4個）；偏H app.js | 木工內容的條號在未拆單體 |
| I20 | 木工 | W | 邊界材要整條蓋住適格外輪廓，是木工覆蓋義務。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/parse_results.py | 木工內容的條號在未拆單體 |
| I21 | 木工 | W | 主支彼此同軸、邊界材與副支要垂直於主支軸，是木工方向政策。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py；偏H app.js | 木工內容的條號在未拆單體 |
| I22 | 混合 | M | 區間伸出之後還要不要守端面，是策略；現行策略只豁免邊界材的延伸段，所以要拆開。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py、framing-template/oracle/framing_oracle.py（共4個） | 木工內容的條號在未拆單體 |
| I23 | 混合 | M | 網格引用的追溯與重算（2026-09-18 目的翻轉）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K grid_systems.inc、references.inc、subgrid_world.inc（共4個）；偏W framing-template/core-probe/parse_results.py；偏H app.js | 木工內容的條號在未拆單體 |
| I24 | 混合 | M | 相位差守門前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K grid_bindings.inc、grid_systems.inc、modeling/__init__.py（共5個）；偏H grid-system-workspace.js | 木工內容的條號在未拆單體 |
| I25 | 核心 | K | 子網格守門是整除與容量，不讀角色。 | 未拆單體 current_geometry.c；偏K references.inc、subgrid_commands.inc、subgrid_rebind.inc（共5個） | — |
| I25a | 混合 | M | 精確等分與使用中保護是核心；被角材線引用就不得改等分，是木工放置的保護。 | 未拆單體 current_geometry.c；偏K grid_subdivision.inc、references.inc；偏W framing-template/core-probe/parse_results.py | 木工內容的條號在未拆單體 |
| I26 | 核心 | K | 擠出構造守門是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K modeling/engine.py、modeling/geometry.py | — |
| I27 | 核心 | K | 殼接合守門是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K modeling/engine.py、modeling/geometry.py | — |
| I28 | 核心 | K | 封閉與體積守門是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K modeling/engine.py、modeling/geometry.py | — |
| I29 | 混合 | M | 組合守門前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/engine.py、modeling/geometry.py；偏H space_modeling.py | — |
| I30 | 混合 | M | 擴充交易與依賴前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py、modeling/engine.py | — |
| I31 | 核心 | H | 輸出缺依賴就拒絕，是交換守門。 | 偏K modeling/__init__.py；偏H model_update.py、scenario_verify.py、space_modeling.py | 公理自標H |
| I32 | 核心 | H | 執行器要宣告自己有的能力，未知就拒絕。 | 未拆單體 current_geometry.c；偏K model_base.c、modeling/__init__.py、modeling/base.py（共8個）；偏W engineering_commands.inc；偏H engineering_bridge.inc、model_update.py、scenario_verify.py（共4個） | 公理自標H |
| I33 | 核心 | K | 精確運算與容量是領域無關的幾何、來源或交易，任何模板都成立。 | 未拆單體 current_geometry.c；偏K model_base.c、modeling/__init__.py、modeling/base.py（共5個）；偏W derived_placements.inc、finish_surfaces.inc、panel_fill_layout.inc（共4個）；偏H model_update.py、space_modeling.py | — |
| I34 | 混合 | M | 版本用身分加內容指紋是核心；不得刪已引用的材料與做法版本，是木工目錄。 | 偏W engineering.inc、engineering_commands.inc | — |
| I35 | 混合 | M | 套用合法性前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W engineering.inc、engineering_commands.inc；偏H engineering_bridge.inc | — |
| I36 | 木工 | H | 保存已發布的材料與做法版本，只有木工工程規格用得到。 | 偏K modeling/base.py；偏W engineering_commands.inc | 公理自標H |
| I37 | 混合 | M | 網格系統與配置前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K boundary_vertex_keys.inc、grid_bindings.inc、grid_systems.inc（共5個）；偏H card_reference.inc、app.js | 木工內容的條號在未拆單體 |
| I38 | 核心 | K | 參數的單位、循環與精確求值，任何模板都成立。 | 偏K parameter_types.h、parameters.inc、references.inc（共4個）；偏W engineering.inc、engineering_commands.inc；偏H parameters.js | — |
| I39 | 核心 | H | 參數卡整張保存，包含未使用的卡。這是來源保存，不是放材。 | 未拆單體 current_geometry.c；偏K parameters.inc；偏W engineering_commands.inc；偏H engineering_bridge.inc | 公理自標H |
| I40 | 混合 | M | 組構編輯守門前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W assembly.inc；偏H assembly_bridge.inc | — |
| I41 | 木工 | H | 組構規則的保存與能力只服務木工組構。 | 未拆單體 current_geometry.c；偏W assembly.inc；偏H assembly_bridge.inc | 木工內容的條號在未拆單體、公理自標H |
| I42 | 混合 | M | 組構實例守門與保存前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/__init__.py、references.inc；偏W assembly_generation.inc、engineering.inc；偏H assembly_bridge.inc | 木工內容的條號在未拆單體 |
| I43 | 核心 | K | 斷面輪廓合法是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K section_profiles.inc；偏H section_profile_diagnostics.inc | — |
| I44 | 核心 | K | 構件在形狀內（定義推論）是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K section_profile_validation.inc；偏H section_profile_diagnostics.inc | — |
| I45 | 核心 | K | 構件互不重疊是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K section_profile_validation.inc；偏H section_profile_diagnostics.inc | — |
| I46 | 混合 | M | 尺寸、方位與座標前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K section_profile_validation.inc、section_profiles.inc；偏H section_profile_diagnostics.inc | — |
| I47 | 核心 | K | 拉伸長度（定義推論）是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K section_profile_validation.inc；偏H section_profile_diagnostics.inc | — |
| I48 | 核心 | K | 定位合法是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K section_profile_conversion.inc、section_profile_placement.inc、section_profile_validation.inc；偏H modeling_cli.py、section_profile_bridge.inc、section_profile_diagnostics.inc（共4個） | — |
| I49 | 混合 | M | 交易與依賴前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K section_profile_validation.inc、section_profiles.inc；偏H section_profile_bridge.inc、section_profile_diagnostics.inc | — |
| I50 | 混合 | M | 隔離前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| I51 | 核心 | H | 斷面能力的保存是幾何物件的持久化。面材規格的內容在 D40，不在這條。 | 偏K modeling/base.py、section_profile_conversion.inc、section_profiles.inc | 公理自標H |
| I52 | 混合 | M | 完成面與試排完整性前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py；偏W finish_surface_types.h、finish_surfaces.inc、panel_fill_layout.inc | — |
| I53 | 混合 | M | 分層與障礙前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K references.inc；偏W finish_surfaces.inc；偏H panel_fill_bridge.inc | — |
| I54 | 木工 | W | 比對與建立不得混用門檻離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| I55 | 混合 | M | 引用與交易前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏W derived_placements.inc、finish_surface_types.h、finish_surfaces.inc（共4個） | 木工內容的條號在未拆單體 |
| I56 | 木工 | H | 面材試排的保存與它依賴的工程規格，是木工鋪排。 | 未拆單體 current_geometry.c；偏W derived_placements.inc、engineering_commands.inc、finish_surface_types.h（共5個）；偏H engineering_bridge.inc、panel_fill_bridge.inc | 木工內容的條號在未拆單體、公理自標H |
| I57 | 混合 | M | 單一計算與共存前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py | — |
| I58 | 木工 | W | 裁切設定合法離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| I59 | 木工 | W | 需求合法、去重與歸屬（求值順序見 R47）離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| I60 | 混合 | M | 方案守恆，對每一支被使用的料逐支成立前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| I61 | 木工 | W | 唯讀與不回寫離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| I62 | 木工 | H | 裁切計畫的保存是鋸切視圖，不是幾何定義。 | 偏K modeling/__init__.py | 木工條號在偏核心檔、公理自標H |
| I63 | 核心 | H | 一個來源頁至多一個來源平面，是附件守門。 | 偏K modeling/__init__.py | 公理自標H |
| I64 | 混合 | H | 第一筆交易的形狀是宿主的；第一個房間是領域起步。 | 偏H serve.py | 公理自標H |
| I65 | 混合 | H | 草稿的數量與頂點上限是宿主；對象是房間外環。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I66 | 核心 | H | 依身分類別決定保留或重配，規則本身不指定角材。白名單在 D54。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I67 | 核心 | H | 匯入要一次做完，缺能力就拒絕。 | 偏K modeling/__init__.py；偏H serve.py | 公理自標H |
| I68 | 核心 | H | 網格草稿的唯一與孤兒規則，對象是格線。 | 偏K modeling/__init__.py | 公理自標H |
| I69 | 木工 | W | 重複開間守門離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| I70 | 核心 | H | 身分帳啟用之後，提交後與載入後都要完整。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I71 | 核心 | H | 沒有配號區段就整筆拒絕，世界不變。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I72 | 核心 | H | 身分帳的保存與能力宣告，是宿主持久化。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I73 | 混合 | H | 空間模型要不要納入拉伸件是快照選擇；條文把角材納入寫在同一條。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| I74 | 核心 | K | 一組來源要完整、唯一、合法，是來源圖的守門。2026-10-16 把它放在共用核心。 | 未拆單體 current_geometry.c；偏K grid_systems.inc、modeling/__init__.py、parameters.inc；偏H card_reference.inc | — |
| R1 | 核心 | H | 同一點多個命中取最後畫的，是拾取順序。 | 未拆單體 current_geometry.c | 公理自標H |
| R2 | 混合 | M | 移動參考線要重放引用它的角材（2026-09-18 拍板反轉，取代原先的凍結語意）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R3 | 核心 | K | 退化或不精確就拒絕、不猜，是幾何紀律。 | 未拆單體 current_geometry.c；偏K references.inc；偏W derived_placements.inc | — |
| R4 | 混合 | H | 單一 parser 是宿主；指令文法把角材、組構、鋪排寫進同一條。 | 未拆單體 current_geometry.c；偏K references.inc；偏W finish_surfaces.inc；偏H app.js、panel_fill_bridge.inc | 木工內容的條號在未拆單體、公理自標H |
| R5 | 核心 | H | 拖曳參考線吸附到引用式的求值結果，是幾何編輯。 | 未拆單體 current_geometry.c；偏K references.inc；偏H reference_bridge.inc、web_bridge.c | 公理自標H |
| R6 | 混合 | M | 已有 K/W 兩段。K 把端部的完整寬度、來源資格、優先規則分開驗，並把每端是否唯一留給策略。W 的 (d) 目前要求恰好一個全寬擋面。 | 未拆單體 current_geometry.c；偏K references.inc；偏W assembly_generation.inc、framing-template/core-probe/gen_scenes.py、framing-template/core-probe/parse_results.py（共5個）；偏H timber-schedule.js、timber-supports.js、timber_support_projection.inc | 木工內容的條號在未拆單體 |
| R7 | 混合 | M | 面上投影分類 = 單一「足跡 × 輪廓接觸關係」函式前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏H app.js、web_bridge.c | 木工內容的條號在未拆單體 |
| R8 | 混合 | M | 套用（apply-proj）是快照式衍生前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K model_base.c | 木工內容的條號在未拆單體 |
| R9 | 混合 | M | 只有已放置面可接收投影（R3 不猜）；平面/立面由承載面法向決定前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏H app.js、web_bridge.c | 木工內容的條號在未拆單體 |
| R10 | 核心 | K | 拆分時孔隨片重分配是領域無關的幾何、來源或交易，任何模板都成立。 | 未拆單體 current_geometry.c | — |
| R11 | 木工 | W | 拆分出來的面保持游離，講的是柱樑投影進空間之後的領域結果。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| R12 | 木工 | H | 柱與樑共用數字 id、用 c／b 前綴分開，只對這兩個木工障礙物有意義。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體、公理自標H |
| R13 | 混合 | M | 拆分時承載面輔助資料跟著含錨點的那片走（與 R10 同一條「資料跟材料走」）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K subgrid_rebind.inc、subgrid_world.inc；偏W engineering.inc | 木工內容的條號在未拆單體 |
| R14 | 混合 | M | apply-proj 逐項選片前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| R15 | 核心 | H | 點名的項目不存在就整筆拒絕，是交易守門。 | 未拆單體 current_geometry.c | 公理自標H |
| R16 | 混合 | M | top_drop（邊樑整段降低）= 半平面裁切前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| R17 | 混合 | M | 貼牆柱露出面在柱遠側緣平面前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| R18 | 混合 | M | 共線、覆蓋與穩定鍵是幾何。onBoundary 怎麼對到邊界材角色是木工。核心段已寫明不由宣告角色倒填。 | 未拆單體 current_geometry.c；偏K model_base.c、modeling/__init__.py、references.inc；偏H web_bridge.c | 木工內容的條號在未拆單體 |
| R19 | 木工 | W | 由端面規則推出轉角與漏鋪，不另存。前提是木工優先級。 | 偏W framing-template/core-probe/gen_scenes.py、framing-template/oracle/framing_oracle.py | — |
| R20 | 混合 | M | 重宣告/刪除連坐前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c | 木工內容的條號在未拆單體 |
| R21 | 混合 | M | 明寫跨距兩端（between）前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K references.inc；偏W framing-template/core-probe/gen_scenes.py；偏H app.js、timber_support_projection.inc | 木工內容的條號在未拆單體 |
| R22 | 混合 | M | 相位差求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K grid_bindings.inc | — |
| R23 | 混合 | M | 子格推導前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K subgrids.inc | 木工內容的條號在未拆單體 |
| R24 | 核心 | K | 擠出求值是領域無關的幾何、來源或交易，任何模板都成立。 | 產品碼無條號 | 產品碼無條號 |
| R25 | 核心 | K | 殼的開閉與法向是幾何。這裡的材料角色是實體與空洞，不是角材角色。 | 產品碼無條號 | 產品碼無條號 |
| R26 | 混合 | M | 複合空間求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R27 | 核心 | K | 正交布林是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K modeling/geometry.py | — |
| R28 | 核心 | M | 衍生面的來源追溯兩段是同一件事，沒有木工政策。公理標 M 只因為現行句子留在宿主段。 | 偏K modeling/geometry.py | 公理自標M |
| R29 | 核心 | K | 標準幾何輸出是領域無關的幾何、來源或交易，任何模板都成立。 | 偏K model_base.c、modeling/engine.py、modeling/geometry.py（共4個） | — |
| R30 | 核心 | H | 先驗來源與能力，再構造、再輸出。這是建模順序。 | 偏H modeling_cli.py | 公理自標H |
| R31 | 混合 | M | 工程來源求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏H engineering_bridge.inc、model_update.py | — |
| R32 | 混合 | M | 格線按 signed k 求值是核心；求完再放角材、支撐交給擋面規則，是木工下游。 | 偏K grid_bindings.inc、grid_lattice.inc、grid_subdivision.inc（共5個）；偏H grid_binding_bridge.inc、grid_system_bridge.inc | — |
| R33 | 核心 | M | 參數求值是來源圖。宿主段寫不自動放材，是在禁止把木工塞進核心。 | 偏K parameters.inc | 公理自標M |
| R34 | 混合 | M | 組構規則流程前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R35 | 木工 | W | 有限角材組構求值離開木工模板就沒有對象。 | 偏K modeling/__init__.py；偏W assembly_generation.inc | — |
| R36 | 混合 | M | 剖面矩形求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R37 | 混合 | M | 拉伸求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/section_profile.py | — |
| R38 | 混合 | M | 簡易定位求值前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R39 | 混合 | M | 預覽輸出前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/engine.py、modeling/section_profile.py | — |
| R40 | 核心 | M | 拉伸件重算是幾何。空間牆只是定位宿主的一個例子。 | 產品碼無條號 | 產品碼無條號、公理自標M |
| R41 | 混合 | M | 空間層次與衍生承載面前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 未拆單體 current_geometry.c；偏K modeling/__init__.py、references.inc、subgrids.inc；偏W derived_placements.inc、finish_surface_types.h、finish_surfaces.inc；偏H panel_fill_bridge.inc | 木工內容的條號在未拆單體 |
| R42 | 混合 | M | 板片、裁切與縫位前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏W panel_fill_layout.inc | — |
| R43 | 混合 | M | 每側承接判定前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 偏K modeling/__init__.py；偏W panel_fill_support.inc | — |
| R44 | 混合 | M | 來源網格重算與值快照前段是可共用的幾何或交易，後段把木工驗收寫在同一條，要拆開。 | 產品碼無條號 | 產品碼無條號 |
| R45 | 木工 | W | 建議、預覽與建立離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| R46 | 木工 | H | 重開面材試排要重播板片、縫和承接，是木工鋪排的重放。 | 偏K modeling/__init__.py | 木工條號在偏核心檔、公理自標H |
| R47 | 木工 | W | 求值順序離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| R48 | 木工 | W | 排料（確定性先適配遞減）離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| R49 | 木工 | W | 收尾與剩料離開木工模板就沒有對象。 | 產品碼無條號 | 產品碼無條號 |
| R50 | 木工 | H | 裁切方案匯出前要重讀計量世界，是鋸切視圖。 | 偏K modeling/__init__.py | 木工條號在偏核心檔、公理自標H |
| R51 | 核心 | H | 錨點指紋是標準 JSON 的雜湊。欄位內容由別條定義。 | 偏K modeling/__init__.py | 公理自標H |
| R52 | 混合 | H | 起步交易的步驟是宿主的；建立的對象是第一個房間。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| R53 | 核心 | H | 匯入時依類別重配身分，是宿主配號。 | 偏K modeling/__init__.py、parameters.inc | 公理自標H |
| R54 | 核心 | H | 網格草稿的生命週期，對象是格線編輯。 | 偏K modeling/__init__.py | 公理自標H |
| R55 | 木工 | W | 重複開間求值離開木工模板就沒有對象。 | 偏K modeling/__init__.py | 木工條號在偏核心檔 |
| R56 | 核心 | H | 一次成功提交結算一次身分，失敗不消耗。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| R57 | 核心 | H | 身分引用對目前世界做唯一判定，是比對順序。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| R58 | 核心 | H | 世界外的觀察值不是定義，勾選不改世界。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| R59 | 混合 | H | 空間模型對拉伸件做一次快照求值；角色與角材選擇是木工。 | 產品碼無條號 | 產品碼無條號、公理自標H |
| R60 | 核心 | H | 整卡的交易、求值與保存是宿主機制。2026-10-16 把它放在 H。正文沒有角材角色。 | 偏K modeling/__init__.py；偏W engineering_commands.inc；偏H card_reference.inc | 公理自標H |

<!-- CLASSIFICATION-TABLE-END -->

## 混合條文的拆分草稿

這裡只把同一條的現行契約分成兩段來讀，條號維持現況。每一條先列還在用這個條號的其他條文。這些是現行引用，不是新條號。要不要另給核心段和木工段不同條號，寫在文末「新方案」的「拆條號」。本稿不採納那個方案，也不寫逐條差異。

### D3

現行位置：公理層第 101 行，空間邊界面（SpaceBoundarySurface)。公理自標 M。
拆開後要跟著改的引用：D4、D12、D21、D35、D41、D49、D52、D53、D54、D55、I5、I52、I63、I64、I65、R29、R41、R51、R52、R53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
局部正交區域是整數毫米平面內的有向外環與零個以上孔環；有效閉區域為外環內部及邊界扣除孔內部，拓撲須滿足 I2。它不含世界位置。每個環及其邊保留來源身分與順序；使用者屬性可隨邊保存，但核心的包含、求交、面積或拓撲不得由屬性名稱改變。既有邊索引、頂點 key 與重建規則由來源轉接提供，不以最近座標重新綁定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

純局部 2D 物件——不含世界位置。
內容：正交多邊形外輪廓、零個以上內孔、每邊 fixity（FIXED/FREE，不寫=全 FIXED)、
分類（UNSPECIFIED/ROOM_PLAN/WALL_ELEVATION)、ROOM_PLAN 專屬的柱/樑投影。
~~~~

### D4

現行位置：公理層第 111 行，承載面（PlacementSurface)。公理自標 M。
拆開後要跟著改的引用：D6、D7、D10、D10a、D20、D38、D41、D49、D54、D55、I56、R4、R53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有向區域宿主由 D2 框架與 D3 有效閉區域組成。直接來源保存框架及區域來源；衍生來源保存具型別的來源鍵與輸入引用，透過求值器產生框架、零個或多個區域分量及可追溯邊鍵，不另存可編輯結果副本。求值所得每個分量、孔及框架都須滿足 D1、I1、I2。引用使用宿主的 typed id，衍生邊使用來源鍵；同一 id 的變體切換、來源可變欄位與用途白名單由登記契約決定，不能由幾何結果相同推定可替換。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

frame + 有效範圍。
有效範圍 = 所引用的邊界面輪廓（含孔扣除）；不引用邊界面時（boundary_id=0）用自帶矩形 rect。
支援 `panel-fill/1` 時另有**衍生承載面**（板背承載面）變體：與一般承載面共用同一 id 空間與型別，
凡引用承載面 id 之處（D6、D7、D10、I13、R4 等）引用方式不變。它只保存 id、變體標記、來源 D42 試排 id、
角材截面高 h 的具型別來源（同 D7 的 B：直接整數、D6b、D26 timber 的 B 欄位、D31 尺寸欄位；不含 D28 面套用欄位）
與 D12 畫布位置；不保存 boundary_id、rect、frame、輪廓、孔或 fixity。
frame 與有效範圍每次依 R41 由來源試排的完成面、板厚 t、D41 障礙集合與 h 求得，不可直接編輯，也不另存輪廓副本。
h 於建立時明選，之後只可明確重宣告；來源試排建立後不可改指。每份試排至多一個衍生承載面；
同一 id 不可藉重宣告在一般與衍生兩種變體間轉換。
衍生有效範圍可為零個或多個分量：本層凡稱外輪廓邊者指任一分量外環的邊，孔邊指任一分量孔環的邊；
這些邊以 R41 的衍生邊鍵引用，不用 e<i>／h<i>e<j> 索引。
衍生承載面不是 D5／D21 成員，不作 D20 擠出、D38 定位的宿主或 D30 配置的邊界，不接受 D28 面套用、apply-proj 或 R13 拆分。
~~~~

### D5

現行位置：公理層第 130 行，空間（Space)。公理自標 M。
拆開後要跟著改的引用：D4、D21、D22、D38、D41、D52、D54、R11。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有位姿區域的集合可依明確成員與其世界框架求出逐軸最小／最大範圍；空集合不產生有限範圍或封閉證明。集合範圍不是幾何聯集，矩形外接盒不是集合所包圍的體積。水密、連通與有向封閉性須逐一通過 I27、I28；成員槽位齊全不可替代該驗證。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

建構子參數 = 一組邊界面 id；成員不可變。
成員數 ≥0：零成員 = 空容器（無界、恆非封閉），是畫布上先宣告再填面的合法態。
每個成員邊界面必須恰有一個承載面引用它（由此取得 3D 位置）；
未放置的邊界面（游離面）不能當成員。
推導：各軸 [min,max] 與封閉與否——只讀衍生，不算輸入。
此型別命名為 `slot-space/1`：封閉欄位僅表示既有槽位条件齊全，不能作為 I28 的
水密外殼證明。非矩形房間的多片邊界採 D21 / D22，不把外接盒當成房間本體。
~~~~

### D6

現行位置：公理層第 150 行，參考線（GuideLine)。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D6c、D54、D58、I13、I23。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
一條宿主局部直線由以下任一來源求值：(1) 指定沿 U 或 V，另一軸的位置由 D6a 求得；(2) 指定 D6c 平面，與宿主框架求唯一交線。直線本體無限；顯示片段為該線與宿主有效閉區域求交並扣除孔內部的所有分量，可為空且不刪除其 typed id。來源定義、求值方向／位置與顯示片段分開保存；可見性不得作為引用存在性的判準。沿線實例化物件需由呼叫方另給該物件契約。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

屬於某承載面，定義來源二選一：
  局部（LOCAL）——方向（沿 U / 沿 V）+ **位置引用式**（D6a）；
  共用基準（DATUM）——只引用一個 D6c 共用基準面，方向與位置由兩面唯一交線推導。
LOCAL 的 offset **不存自由數值**；DATUM 不另存方向或 offset（D9：只存定義）。
本體是兩端無限延伸的面內直線；可見線段 = 本體與承載面有效範圍（D4）的交集，
即時裁切並扣孔，可能一段、多段或零段；多段仍是同一 id，零段不刪除線或引用。
參考線可在面外存在並被合法引用；沿線放角材仍須通過 I5、I11、R6 等材料規則。
~~~~

### D6a

現行位置：公理層第 164 行，局部參考線位置的引用式。公理自標 M。
拆開後要跟著改的引用：D6、D7、D10、D36、D46、I7、I12、I13、R5、R32、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
來源化線性位置式為 Σ cᵢ·qᵢ，其中 cᵢ 是無單位精確有理數，qᵢ 是具長度單位與來源鍵的量。來源求值器回傳數值、單位、依賴鍵及明確的入值模式。含參數欄位者精確求完整和，結果必須是 D1 範圍內整數；既有非參數式只對完整和取下界，不能逐項取整。位置式不含匿名長度常數；可以供值的型別、同宿主／同軸限制由以下來源登記契約列舉。核心驗來源存在性、單位、循環與精確入值，不以來源的顯示名或維度數值猜其身分；此限制只屬本位置式，不擴散成所有幾何欄位禁止直接輸入。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

`offset = Σ cᵢ·qᵢ`，cᵢ 為有理**係數**；
不含 D31 參數引用的既有式，求值後**取下界**得整數座標（D1；比照 D10a 對奇數 gap 的處理）。
包含 D31 參數引用的式子，所有項精確相加後驗最終座標；非整數或超出 D1 即拒絕，不對各項或總和取整。
可引用量 qᵢ 限六類，(a)–(d) 須與本參考線**同承載面、同軸**：
  (a) 外輪廓邊、孔邊的該軸座標，與輪廓／孔頂點的該軸座標；
  (b) 同面其他參考線（含 D6 的 DATUM 來源）的位置，或主網格／子網格的（軸，索引）格線位置（D10/D10a/D19），以及 D19a 的來源規則線位置；
  (c) 面材尺寸：PANEL_LAYOUT 的 panel 與 gap；
  (d) 角材截面 A／B 寬，以及已放角材垂直於本軸的側面座標；
  (e) 具名規格常數（D6b）；
  (f) D31 參數卡的尺寸欄位，以 ParameterRef 的卡片 id 與欄位 id 引用。
引用子線的座標只引用該軸位置，不將父格範圍或預設角色附加給 D6 獨立參考線；獨立參考線仍依 D6 裁切可見段。
**沒有無名常數項**：有單位的字面數字只能經由 (e) 或具名的 (f) 進入。
**係數是比例，不是尺寸**——cᵢ 無單位，表達「幾根角材寬」「幾倍面材」這類結構關係；
**在參考線位置這個式子裡，帶單位的量（mm）一律不得以字面數字出現**，只能來自 (a)–(f)。
式子裡的裸 mm 數字 = 非法。

**本條的適用範圍**：本條管的是參考線位置 offset 的引用式，不是全公理層的通用禁令。
`engineering-spec/1` 另依 D26–D28 支援 D10a 的 panel / gap 及 D7 的 A / B 的具型別來源。
舊直接數值定義保持合法，來源明示為「既有直接輸入」；不經使用者明確選擇不轉換引用。
SERIES 的 start / step、EXPLICIT 座標與 PANEL_LAYOUT 的具體化起算點仍使用現有定義。
D31 的四則算式只存在參數定義中，不把本條的線性位置式擴成任意程式，也不讓材料厚度參與二維格線計算。
數量或比例欄位不能直接充當位置尺寸；須先在 D31 中得到尺寸欄位，再按本條引用。
~~~~

### D6b

現行位置：公理層第 193 行，具名規格常數（SpecValue)。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D6c、D20、D28、D31、D36、D37、D46、D54、D55、I8a。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
具名規格為名稱唯一的整數毫米值；名稱是身分，不是可任意改動的顯示文字。引用未知名稱拒絕。重宣告值須經 I8 候選交易，按來源圖重算全部下游；有效數值須通過使用欄位的正值／非負值及 D1 範圍限制。具名規格與不可變版本、參數欄位是不同來源種類，不自動複製、改名或互換。以下相容契約保留既有命令及允許欄位。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 層的具名整數 mm 值——
`spec <名稱> <整數>`，例如 `spec 崁燈離牆 150`、`spec 燈距 900`。
名稱唯一；未宣告即引用 → 拒絕（I9 順序即依賴順序）。
可重宣告，走 I8 交易：改值 → 全量重驗 → 全過才提交，否則整筆回滾。
**在參考線位置的引用式裡，字面尺寸必須經由本條具名規格或 D31 的具名尺寸欄位進場**——
數字帶意義，才看得出改它會動到什麼。D6c 的位置引用式亦可使用具名規格。
既有 spec 仍保存原名稱與整數值，不因提供參數卡介面而複製成另一份有效來源、改名或自動轉換引用。
  D6b 是可重宣告的具名常數，與 D26 的不可變材料版本分開。
  D28 可明示引用 D6b 作為 panel / gap / A / B 的尺寸來源；具名常數變更仍須重算完整引用鏈。
  實際有效值須符合所引用欄位的整數、正值／非負值及 D1 範圍要求。
~~~~

### D7

現行位置：公理層第 223 行，角材（Timber)。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D15、D34、D36、D45、D49、D54、I12、I35、I50、I54、I56、R2、R13、R31、R41、R45。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
直線矩形截面掃掠的求值資料為：原點 o、三個有身分的正交單位軸 E₀/E₁/E₂、截面尺寸 a>0、b>0 與軸向區間 [s₀,s₁]（s₁>s₀）。幾何體為 o+[0,a]E₀+[0,b]E₁+[s₀,s₁]E₂；八頂點及六個朝外面由此推導，不另存。尺寸來源與各軸對應須明確，交換相等數值不交換欄位／面身分。位置和區間可由登記的來源求值器推導；是否必須採引用定位、如何選取端部、是否可未定位存在，是該型別的建立契約。核心接受這組已解析資料作幾何求值，不因此新增可直接宣告任意掃掠體的命令或已保存物件種類。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

截面 A×B + placed flag + 局部三軸 + 原點。
**長度不宣告**——`timber id A B`，L 一律由跨距推導（R6），撞到佔用邊界（D11）即止。
2026-09-18 使用者拍板**廢除明寫長度** `timber id L A B`：長度是環境推導的結果，
不是可以憑空給的數字（與 D6a「禁止來歷不明的數字」同一原則）。
六個面由 TIMBER_FACE_SPEC/WALK 表推出，法向一律朝外。A0 = 接觸面。
錨點 = **位置引用**（I13：at-line 或 at-face）+ 放法記錄（anchor_kind、參照、through 等）；
**不存凍結 uv**——被引用的線或邊移動時，中線與長度重新推導（R6(e)）。
支援 `engineering-spec/1` 時，A / B 可各自保存 D28 的尺寸來源；展開截面是衍生值。
支援 `parameters/1` 時，A / B 可透過 D28 明示引用 D31 尺寸欄位；W / H 到 A / B 的對應須明選，不從欄位名稱或相機方向猜測。
原 `timber id A B` 仍合法。材料引用不提供 L、不改放法或角色，也不將未放置角材當成合法成品。
截面變更須重新推導既有錨點、中線、跨距、擋面與後續依賴，遵守 I8 / I8a / I11 / I13 / D17。
宿主為 D4 衍生承載面時，B 的有效值須等於該面的 h，B 向須朝該面 +N（結構側），見 I53。
~~~~

### D8

現行位置：公理層第 242 行，邊（SurfaceBoundaryEdge)。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
區域邊是具有來源身分的環中有序相鄰頂點對；端點、方向與將該邊沿框架法向延伸所得的側平面均從來源求值。邊屬性的存在與值不改變幾何邊本身；修改來源後，依來源鍵重求幾何並依 I8 重驗所有引用。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

邊界面的第 i 條輪廓邊，端點/側向平面皆衍生。
fixity 是邊的屬性，存在邊界面上。
~~~~

### D9

現行位置：公理層第 251 行，只存定義。公理自標 M。
拆開後要跟著改的引用：D6、D10、D16、D17、D19、D50、D51、D58、D63、R4、R38、R58。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

來源圖只保存具型別來源、來源引用和使用者明選。頂點、線段、範圍、求值尺寸、幾何結果和可重建索引都是衍生值，重算走完整依賴閉包，不得另存第二份權威定義。

**木工模板條文草案**

木工模板登記哪些東西算定義：角材不另存八角、已發布的材料與做法版本算定義、算出來的角材幾何不得回寫來源。核心不內建這份白名單。

### D10

現行位置：公理層第 282 行，參考網格（ReferenceGrid)。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D15、D19、D43、D45、D54、D58、I13。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有限正交格網由兩軸具身分的座標序列組成。每軸來源可為明列整數座標、起點／步距／數量的等距列，或 D10a 的本體加間隙週期列；求值保留來源模式、索引及全部依賴。格線本體與宿主區域的可見交段分開，格子由相鄰線包圍；從另一配置或有限裁切派生者保留原來源索引，不能依畫面排序重編。方向角色或材料預設是附加使用設定，不參與坐標生成；修改它們不能更改既有幾何或追溯身分。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

屬於某承載面 + 兩軸各一份**線的定義**——
u 軸定義（U 座標集 = 沿 V 走的直線）、v 軸定義（V 座標集 = 沿 U 走的直線）。
每軸的有限來源為下列三種之一，兩軸互相獨立、可用不同來源（D9：只存定義，展開的座標不存）；主格另可整格改用 D30 配置（from-binding）或 D42 鋪排（from-fill，`panel-fill/1`），見本條末兩段：
  明寫（EXPLICIT）——逐一列出座標；
  等差（SERIES)——起點 start、間距 step>0、條數 count，第 k 條 = start + k·step；
  面材（PANEL_LAYOUT)——面材本體 panel、縫寬 gap、起算點 anchor，格線 = 縫的中心線（D10a)。
支援 `engineering-spec/1` 時，PANEL_LAYOUT 的 panel / gap 可各自保存 D28 的尺寸來源。
支援 `parameters/1` 時，上述 panel / gap 亦可引用 D31 尺寸欄位；PANEL_LAYOUT 的具體化 anchor 與舊 SERIES / EXPLICIT 不因此新增參數引用。
同一欄位只能有一種生效來源；界面顯示展開值及完整來源，修改展開值須明示建立覆寫。
「該軸未宣告」與「該軸推導出零條線」是兩回事：前者是定義不存在，
後者是合法的推導結果（面小於一片面材）。
網格 = 參考線的集合，用（軸，索引）選線；既有有限來源索引 0-based，沿座標遞增方向數。
引用 D30 配置的主格使用帶符號 lattice 索引 k；索引是來源身分，不是裁切後陣列的位置。
主網格線段不存，用時由有效面輪廓截出——可能多段、可能空段。子網格的來源及局部範圍另依 D19。
主網格與子網格共用 grid id 空間；同一 id 不可藉重宣告在兩種類型間轉換。
主網格可另存主支長度方向 `main_along = u | v`，作為格線的**構件放置預設**；
它不改格線座標、可見段、D11 擋面，也不代表角材已放置。
沿 `main_along` 方向的格線預設 `primary / 2`，垂直方向的格線預設
`secondary / 3`。u 座標格線沿 v 走、v 座標格線沿 u 走，
因此角色按線的延伸方向判定，不按座標軸的字母猜。
未宣告 `main_along` 的舊網格仍可載入，但其格線角色為未設定；
不從畫布方向或格線順序猜主支。新建網格的圖形化流程須讓使用者選主支方向。
DSL：`grid <id> on <承載面> [main-along u|v|none] u ... [v ...]`。
同 id 重宣告時省略 `main-along` 保留原值，明寫 `none` 清除；
既有網格可只重宣告 `main-along`，新網格仍須有至少一軸的線來源。
格線不擁有或自動建立角材；預設角色只在沿線放置時帶入明寫的角材宣告，
不追改既有角材的角色。

主格可引用 D30 配置；承載面須引用該配置的同一邊界，兩軸及 main_along 從來源取得。
此時以 source phase、帶符號 k 及配置錨點精確求值；面外格線仍存在，可見段為空不刪除引用。
主格不能另存直接排法或工程尺寸綁定，不能改写為可見陣列；新語法為 grid G on P from-binding B。
舊有限主格及 D29 legacy-finite 的 from-system origin 維持原義；不自動轉換或用同 id 隱含改換索引空間。

支援 `panel-fill/1` 時，主格可整格以一份 D42 鋪排為來源（from-fill）：只保存鋪排 id 與可選 main_along，
兩軸格線均取自 D43 的縫中心線，不另存可獨立編輯的 panel／gap／anchor／相位差或縫位陣列。
所在承載面必須是該鋪排的 D4 衍生承載面；其他承載面不得引用鋪排來源。
格線身分為（軸，signed k）；被錯開軸的線另含 band（D43）。引用被錯開軸的線須寫 band，缺 band 或對未錯開軸寫 band 均拒絕；D6a(b) 引用同此。
座標依 D43 在完成面框架求值，再依 R41 映射到板背框架；鋪排變更後依 R44 按原身分重算，不按最近座標改綁。
比照 from-binding 的無限主格：不受 I10「全部來源線須在範圍內」限制，可見段為空不刪除引用，單次查詢容量依 I37；
對本來源，I10 的「座標序列嚴格遞增」指完成面框架的 c_X(k) 隨 signed k 嚴格遞增（T_X>0 恆成立），s=−1 時板背框架的 v 座標隨 k 遞減不違反 I10。
本版鋪排來源主格不得作 D19 子網格的父格，也不適用 D19a；不能另存直接排法或工程尺寸綁定。
本段不改 EXPLICIT／SERIES／PANEL_LAYOUT／from-binding、legacy-finite 及 D29／D30 的定義。
~~~~

### D10a

現行位置：公理層第 331 行，面材排法（PANEL_LAYOUT）的格線。公理自標 M。
拆開後要跟著改的引用：D6a、D10、D28、D29、D42、D43、I10、I13、I35、I52、R31、R42。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
週期排列輸入為本體長度 P>0、間隙 g≥0、有效範圍外接區間 [lo,hi] 與固定起算點 a；節距 T=P+g。第 k 個本體為 [a+kT,a+kT+P)，其後間隙為 [a+kT+P,a+(k+1)T)，間隙中心 cₖ=a+kT+P+floor(g/2)。本條有限來源取 k=0,1,2,…，僅在 a+(k+1)T<hi 時產生中心線，否則停止；起算時須 lo≤a<hi。奇數間隙中心偏向低座標側，不拒絕也不近似。起算點在宣告時具體化，之後不隨範圍或來源更新而自動改變；只可依明選操作換值。無限來源的 signed 索引與裁片列舉復用同一公式，但保留各自範圍與索引契約。來源值先精確驗整數與範圍，超出容量拒絕而不截斷。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

設該軸有效範圍的外接區間為 [lo, hi]
（D4，與 I10 用的是同一個區間；I7 不再限制參考線可見範圍），週期 T = panel + gap，起算點 a。
  第 k 片面材本體佔 [a+k·T, a+k·T+panel)，
  第 k 條縫佔 [a+k·T+panel, a+(k+1)·T)，k = 0,1,2,…
  第 k 條格線（縫中心線）座標 **c_k = a + k·T + panel + ⌊gap/2⌋**——
  gap 為奇數時中心線偏向低座標側 0.5mm（定義好的取整，不是猜；
  與 I13 對奇數角材寬「多的 1mm 恆在 +cross 側」同一條紀律）。
產生第 k 條的條件是 **a+(k+1)·T < hi**：整條縫落在範圍內，且其後仍有非空的面材本體。
不滿足即停止——末端是裁切片，合法；不因「除不盡」而拒絕，條數本來就是推導結果。
拒絕條件（D1 全整數、R3 退化就拒絕）：
  panel ≤ 0、gap < 0、a < lo、a ≥ hi → 拒絕；
  推導條數超過單軸上限 → 拒絕（不截斷、不靜默丟線）。
  **gap 為奇數不拒絕**：答案是確定的 gap/2，只是不落在整數格上，依上式取下界即可。
  R3 的「拒絕不猜」管的是答案不確定（unproject det=0、多解），不管「已知但需取整」。
  3mm / 5mm 是實務上最常見的板縫寬，把它們擋在門外是缺陷不是紀律。
**起算點在宣告當下具體化並寫進定義**（本條自有的凍結，**不再比照 R6(e)**——
R6(e) 已於 2026-09-18 反轉為重算；起算點 a 的凍結僅為保住索引編號不重排）：明寫 `from c` 取 c，
未明寫取宣告當下的 lo。之後承載面改變不重算 a——
因此已存在的索引永不被重新編號，能變的只有尾端條數。
panel / gap 的來源先按 D28 求值得整數 mm，再使用本條同一公式及拒絕条件。
起算點仍於套用／宣告當下具體化；可明選面邊作為當下取值來源，但之後輪廓變更不自動重排。
更新做法版本時，保留現有具體起算點，除非本次操作明選新的起算點。不得把來源更新解讀為自動置中。
~~~~

### D11

現行位置：公理層第 360 行，擋面（StopFace)。公理自標 M。
拆開後要跟著改的引用：D7、D10、D18、D19、D10b、I13、I19、I30、I50、R32。

**現行核心契約，原樣分開**

~~~~
接觸候選為具型別來源鍵的有向平面及其實際有限佔用區域。對一條有寬度的軸向掃掠帶，側向定位驗整條接觸邊共線，端向裁切驗垂直端面且覆蓋完整帶寬；相等比較精確，不以單點接觸、部分覆蓋或兩個不同平面拼湊成同一完整端面。候選是否可用、允許何種來源及優先關係由固定策略明列，核心只依傳入候選及策略結果求幾何，不從來源類名或角色字串自行放行。
~~~~

**現行木工模板契約，原樣分開**

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

可頂住角材端面的面，三種來源——
外輪廓邊、孔邊、同承載面已放角材的側面。
每面帶：垂直於角材長度軸的固定座標 + 沿軸涵蓋範圍 + fixity。
「頂到」= 擋面固定座標恰等於端面座標，且擋面涵蓋端面全寬。
**物理意義 = 已被佔用的空間邊界**，不能再被另一個物體佔用。因此同樣這三種來源的邊，
依相對於角材長度軸的朝向分兩種用途：**垂直**者為擋面，頂住端面、決定長度；
**平行**者供側向貼齊、決定位置（I13 at-face）。
放一支角材即新增其側面為邊；某側面與既有邊共線且重疊，則不新增（同一條邊不重複計）。
~~~~

### D13

現行位置：公理層第 375 行，RC 柱（RcColumn)。公理自標 M。
拆開後要跟著改的引用：D14、D22、D41、D54、I55。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
軸對齊長方體由 X/Y/Z 三個有界正長度區間的直積定義。框架投影、包含與正體積相交只用該三區間求值；區間來源必須明選，核心不從物件名稱猜高度、材料或空間歸屬。對同型別／異型別物件要查平面足跡或三維體積，由使用契約明確選取，不能將某個查詢擴為所有物件的全域排斥規則。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 中房間座標的軸對齊方塊（AABB)——
x/y/z 各一個整數區間。可屬於某空間（space_id>0）或游離（space_id=0);
是空間的障礙物，不是成員，不參與封閉推導。
DSL 省略 z → [空間 −Z 槽面高程， +Z 槽面高程]；游離或推不出 → 拒絕不猜（R3)。
~~~~

### D14

現行位置：公理層第 386 行，RC 樑（RcBeam)。公理自標 M。
拆開後要跟著改的引用：D22、D41、D54、I55。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有軸向的長方體以明選正交主軸、兩個橫向尺寸及軸向區間求值；各有效尺寸須正且滿足 D1。由中心線與整數寬度構造左右邊界時，既有奇數寬採負側 floor(width/2)、正側補足餘數的慣例；由頂座標與正深度構造底座標時採 bottom=top−depth。這些是明確來源映射，核心不自行要求主軸水平、不猜端點或宿主。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

同 D13 的 AABB，走向軸必為 x 或 y（水平）。
頂面 z_hi = 空間 +Z 槽面高程或明寫 top，底面 = z_hi − 深。
中線對齊：寬度 c±⌊w/2⌋/⌈w/2⌉（奇數多的 1mm 在 + 側，I13 慣例）。
~~~~

### D16

現行位置：公理層第 413 行，邊界材的固定段與延伸段。公理自標 M。
拆開後要跟著改的引用：D15、I22。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
在同一有向直線上，實例區間 J 與定位來源區間 E 的固定部分為 J∩E，超出部分為 J∖E；空集、單一連續區間與兩側分量均須按精確端點表示。共線、重疊及 E⊆J 是獨立可查的幾何關係；區間名稱不賦予優先級、接觸資格或例外。這些策略只由以下模板契約選取。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

一支 `boundary` 角材的 footprint 沿長度軸分兩段——
**固定段** = 與它所覆蓋的那條外輪廓 FIXED 邊（`boundaryEdge`）在長度軸上重疊的部分；
**延伸段** = 超出該邊端點、繼續進入面內的部分（可為空）。
層級 1 的一切性質只屬於固定段；延伸段是離開 RC 的懸出段，只受 I22 管。
兩段是同一支料的同一個 footprint，不另存（D9）。
~~~~

### D18

現行位置：公理層第 432 行，擋面參照（StopFaceRef)。公理自標 M。
拆開後要跟著改的引用：I13、R4、R21、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
引用鍵須同時含來源型別、物件 id 與所引用子元素的穩定身分；不得以裸數字 id、展示文字或幾何相等替代。端部候選同座標但來源鍵不同時保留為不同候選；若使用契約要求唯一而有多個合格來源，須明選或拒絕，不按遍歷順序猜選。以下定義現行可作接觸來源的編碼白名單；抽出引用機制不擴大它。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

DSL 指名一個 D11 擋面的寫法——
外輪廓邊 `e<i>`、孔邊 `h<i>e<j>`（與 at-face 同一套寫法）、
已放角材 `t<id>`（指該角材垂直於本支長度軸的兩個側面，二選一由 R21(d) 決定；
at-face 用同一套寫法指名**平行**於本支長度軸的側面，見 I13）。
參照只是「指名」，不改變擋面的任何性質，也不新增擋面來源（D11 仍是三種）。
~~~~

### D19

現行位置：公理層第 444 行，子網格（Subgrid）。公理自標 M。
拆開後要跟著改的引用：D6a、D10、D15、D19a、D10b、D54、D58、I13、I23、I25、I25a、R6、R23、R32。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
局部細分輸入是單一父矩形的來源鍵及各軸等分數 n；每軸 n 為 1…65 的整數，至少一軸大於 1，保持 I25 的既有子格建立範圍與容量契約。對長度 L 的一軸，L 必須被 n 整除；子線位置為父起點+k·L/n（k=1..n−1），n=1 合法且產生零條內部線。索引與父格身分共同構成引用；線只在該父矩形內有效，扣除宿主孔與有效域外部分。精確等分不接受餘數格，也不將父格或子線的可視邊界當成實體接觸來源。隨線攜帶的放置角色由模板解讀，與座標生成分開。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

依附一個 D10 主網格，定義只存自己的 grid id、父 grid id、父格四邊參照，以及 u/v 等分數。承載面由父格取得，展開座標與線段不存（D9）。父網格必須是主網格，不能再依附子網格。
有限主格的父格分界為：各軸主格推導座標，加上承載面有效範圍外接區間的 min/max，依座標排序去重。兩軸各取一對相鄰且不同的分界，形成閉矩形 C；其與有效面 F 的交集須有正面積。未定義或推導零條線的軸仍以 min/max 形成一個區間。
四邊參照各為 min、max 或 line:<index>；索引指主格該軸的 0-based 線。恰與外接邊界同座標時，以 min/max 為標準參照。這些邊只限定局部範圍，不新增 D11 擋面。面材來源的父格依縫中心線形成，不以面材本體邊緣另切一份格子。
設某軸兩界為 lo、hi，等分數 n。第 k 條內部子線位置為 lo + k × ((hi − lo) / n)，k = 1…n−1。只有內部線屬於子格；父格邊不重複生成。子線以（子格 id、軸、索引）引用，索引沿座標遞增；可見段為該線與 C∩F 的交集，可多段或零段。
子格兩軸的格線皆預設 secondary / 3；只提供放置預設，不擁有或自動建立角材，不繼承父格 main_along，不改既有角材角色。
DSL：subgrid <id> parent <grid-id> cell u <lo-ref> <hi-ref> v <lo-ref> <hi-ref> divisions u <n> v <n>。
重宣告須給完整定義，父 grid id 不變；可明確重選同一父網格中的格子及修改等分數，沿引用鏈重新推導並依 I8/I8a 提交。
引用D30配置的無限主格另用 lattice-cell i j：四邊固定為來源格線 i/i+1、j/j+1，
不以有效面 min/max 增補或重編 cell；兩軸須有來源，C∩F須有正面積。子線仍按上式等分及裁切，索引保持既有內線0-based語意。
DSL：subgrid SG parent G lattice-cell I J divisions u NU v NV；有限主格的cell語法與無限lattice-cell不得混用。
~~~~

### D22

現行位置：公理層第 498 行，複合空間（CompositeSpace；orthogonal-model/1）。公理自標 M。
拆開後要跟著改的引用：D5、D24、D41、D52、I28、R26、R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
由通過 I27、I28 的有向封閉殼得到有界區域 V；對明選且可求值的實體集合 Oᵢ，淨區域為 regularize(V∖⋃Oᵢ)，其中 regularize=closure(interior(·))。包圍區域、扣除後區域與來源各實體的材料量是不同輸出，不互換。沒有明選障礙不代表自動納入所有相交物件；外接盒與槽位資訊不得代替封閉殼。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

只存 id、一個 D21 殼引用、
明示的障礙實體引用集合。殼界定空間邊界，柱樑等障礙物仍不充當殼成員。
殼通過 I28 時，可推導有界空間區域 V；開放殼仍可作合法部分空間，但 V 與體積未定。
淨空僅在 V 已定且全部障礙幾何可求值時，依 `reg(V \ union(障礙實體))` 推導。
障礙可跨越殼邊界，僅交集部分影響淨空；不得自動補入附近柱樑、牆厚或未宣告物件。
未扣障礙的 V、扣除後淨空、材料體積是三種不同結果，輸出必須標明角色。
本條與 D5 的 id 空間和引用型別不同；D13 / D14 原有 `space_id` 仍只指 D5，
不得把新空間 id 塞入舊欄位或默默改 I15 / I16 的包容規則。
~~~~

### D26

現行位置：公理層第 561 行，材料版本（MaterialVersion；engineering-spec/1）。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D6b、D9、D27、D28、D36、D42、D47、D54、D55、D56、I8、I34、I56、R4。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
不可變的具型別版本來源由穩定 id、版本 id、規範化內容與內容指紋構成；同一版本身分不得原地改內容。來源字段有固定 field id、量綱與合法性條件，求值仍保留從欄位到版本的完整引用，不展平成裸數字。核心驗身份、指紋、欄位存在性與使用處的量綱／整數／範圍要求；版本 schema 的種類、欄位白名單及材料意義由模板提供。小數的來源值合法與它能否作整數幾何入值是兩層判斷。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

由穩定 id、正整數版本、內容指紋、
名稱、種類與具型別資料構成。種類為 panel 或 timber；panel 必有正整數 mm 的 width / length
及可選的正十進位 mm thickness；未指定厚度明寫未設定，不阻擋只使用長寬的排格（D42 面材試排除外：試排一律要求已明設的整數 mm 厚度，見 I52）。
timber 必有正整數 mm 的 A / B。參與幾何的數值遵守 D1。
thickness 以十進位字串精確保存，僅為型錄資料；不得靜默取整或因此宣稱支援小數幾何。
支援 `panel-fill/1` 的執行器得由 D42 明確引用 panel 固定版本的 thickness，按 I52 驗證後用於完成面層次；
沒有該能力或沒有明確引用時仍只是型錄資料。本能力的幾何輸出仍受 D1 限制，非整數 mm 厚度不得取整後放行。
可另存品牌、型號、來源備註；缺值保持缺值，不猜測。名稱不是身分，同名不同 id 可並存。
已發布版本不可改寫，改內容建立新版本；封存不使既有引用失效。未發布草稿不是可引用版本。
指紋由有版本的確定序列化規則對完整發布內容（排除指紋本身）計算，匯入須重算；不能僅信外來指紋。
~~~~

### D28

現行位置：公理層第 585 行，面套用與尺寸來源（EngineeringApplication / DimensionSource；engineering-spec/1）。公理自標 M。
拆開後要跟著改的引用：D4、D6a、D6b、D7、D9、D10、D10a、D36、D37、D46、D49、D54、D56、I8、I32、I66、R4、R13、R31、R32、R53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
型別化來源綁定指定目標物件／槽位／欄位及來源引用；每個解析結果回傳有效值、單位、終端來源身分與完整覆寫路徑。覆寫順序必須由契約明列，沿路均須驗型別，缺值不得以相同名稱或數值補猜。核心保存引用而不扁平化，並以來源圖進行重算、循環偵測與交易；哪些來源可綁到哪些槽位、角色是否相符及版本種類限制由以下模板 schema 決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

每個承載面最多一份有穩定 id 的套用，引用一個固定做法版本，並保存明選的面軸排列、
面覆寫、建立起點的選項、主支方向預設及明確綁定清單。更換做法是重宣告，不另留兩份互相競爭的套用。
已建主格的具體 anchor 只存在 D10a 的主格定義中；套用的起點選項只供新建時取值，
明選更新起點時修改同一主格 anchor，不在套用保存另一個可獨立變動的有效起算值。
主格 panel / gap 及角材 A / B 的來源各為：既有直接整數、D6b 名稱、D26 固定版本欄位，
本承載面套用的具名欄位，或支援 `parameters/1` 時的 D31 尺寸欄位。
來源含型別、完整 id / 版本 / 欄位；參數來源為 `ParameterRef(parameterId, fieldId)`，不以名稱或目前列表順序配對。
參數來源可用於本條物件來源與物件覆寫；本次不將可變參數加入 D26 / D27 已發布內容或面套用覆寫。
解除物件的參數來源須明示把當下合法有效值轉為直接整數；既有物件覆寫可移除以恢復原來源。
來源種類為材料版本引用時，格線 panel 只能接面材 width 或 length，角材 A / B 只能接 timber 的相應截面欄位。
gap 使用明設縫寬；直接整數、D6b 及覆寫按目標欄位驗值，不受上述材料引用型別限制。
沿用套用的欄位依序求值：明示物件覆寫 → 明示本面覆寫 → 指定做法版本的設定 →
該設定明指的材料版本欄位。這是同一來源路徑的查找，不把其他未選材料當成備援。
覆寫只准明定欄位；覆寫是附屬物件／面與欄位身分的定義，可移除以恢復沿用，仍須预覽重驗。
首版面覆寫限 gap、width / length 軸向對應、三角色 A / B 及主支方向預設；
物件覆寫限已綁定主格各軸 panel / gap 或已綁定角材 A / B。幾何值仍為有意義的具名欄位，
不以隱藏全域預設補缺。具體起算點是單獨的明示設定，依 D10a 保持。
套用時明選建立／更新哪個主格、綁定哪些已放角材，或只提供未來新建預設。
未選角材不自動綁定、不改角色；主支方向預設更新不追改既有角色。被既有引用連帶影響者仍須重算與列出。
角材綁定保存所選的 boundary / primary / secondary 材料槽位；若與既有角色不符，拒絕並請使用者另作明確處理。
custom 角色本期不綁定上述三槽位；可保留直接截面或明選相容材料版本欄位，不因此自動改角色。
~~~~

### D29

現行位置：公理層第 613 行，獨立網格系統（GridSystem)。公理自標 M。
拆開後要跟著改的引用：D9、D10、D19a、D10b、D30、D31、D43、D54、D57、D64、I24、I37、I57、I69、I74、R22、R32、R42、R44、R60。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
無限格網來源有兩個整數索引軸。等距軸以 phase+k·step（k∈ℤ，step>0）求值；本體加間隙軸依 D10a 的同一週期公式求值。配置依 D30 保存來源、局部軸對應與精確錨點關係，再推導平移；現行配置不因此增加旋轉、鏡射或縮放。相鄰 signed 線索引決定 cell，查詢只列出與指定有限範圍相關的片段，不將列舉結果保存為來源。方向使用預設不參與座標公式。來源引用、容量與首版組合限制依以下相容契約，無限索引求值不等於解除已有能力限制。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 層獨立物件，保存 id、名稱、兩軸排法與可選 main_along；
不依附承載面，不包含邊界或材料。名稱為非空 UTF-8（至多 96 bytes），名稱不是身分，可重名。
新來源為無限排法：兩軸各為未定義、REPEAT 或 REPEAT_PANEL，至少一軸存在；不保存總條數。
REPEAT 保存整數 phase 與正 step，格線座標 c(k)=phase+k·step，k∈Z；每條線向兩端無限延伸。
REPEAT_PANEL 保存正 panel、非負 gap、anchor；pitch=panel+gap，phase=anchor+panel+floor(gap/2)，
c(k)=phase+k·pitch，k∈Z。這是無限縫中心線排法，不套用 D10a 的正向終止或起點必須在範圍內規則。
未設相位差時，格線身分為（系統、軸、signed k）。設了 D10b 相位差時，段的身分是（系統、軸、signed k、另一軸 cell 索引）。未設相位差時，cell(i,j) 由 u_i/u_(i+1)、v_j/v_(j+1) 圍成；有相位差時（同一系統至多一軸，D10b），圍成格子的線座標依 D10b，格子仍由未錯開的相鄰線切開。
cell 須兩軸都有定義；沒有某軸時不以邊界或視窗邊界補出假 cell。
來源在無範圍時已合法；原點是編號基準，不是第一條線。有限視窗／邊界只決定本次求值及顯示範圍。
機器索引支援 signed int64，實際被查詢或引用的幾何輸出按 D1 驗證；不要求無限本體全落在 D1。
卡片與視窗移動、縮放、顯示取樣都不改格距、索引或幾何來源；密集視窗的抽樣必明示且不冒充完整結果。
軸欄位可為原直接整數；支援 `parameters/1` 時，REPEAT 的 phase / step、REPEAT_PANEL 的 panel / gap / anchor，以及 D10b 的相位差，亦可各自明示引用 D31 尺寸欄位。
每個有效欄位恰有一個來源。未由 D64 供應的欄位，存直接值或 ParameterRef；
支援 grid-card-reference/1 時，兩軸各一個軸長度槽可共同由一份 D64 卡片引用供應。
該兩槽不另存直接值或 ParameterRef；其來源由整組引用及軸對應唯一決定。
所有引用的有效值先按 D1 與本條驗證，再使用原有排格公式。
phase / anchor 的參數變更依同一引用重算，不自行置中、不改帶符號線與 cell 的身分；D30 的頂點／cell 錨點關係維持。相位差的參數變更同樣只重算段座標，不改 signed 索引、band 或 cell 身分。
解除參數引用須明示轉為當下有效整數，經 I8a 預覽；不在網格內保存第二份可獨立編輯的有效值。
D64 整卡引用的建立、替換、對調及解除另依 R60，一次處理兩個軸長度槽；
其他逐欄引用的解除維持原義。相位、間隔、錨點及相位差不因長度對調而對調。
軸欄位不直接接受算式、材料版本或面工程套用，算式經 D31 欄位引用；仍不接受旋轉、鏡射或巢狀網格，不擁有或自動建立角材。
無限軸可另依 D10b 保存一個可選相位差；省略則本條的貫通直線維持不變。
相容例外：GEO-214 的 EXPLICIT／SERIES(count)／PANEL_LAYOUT 及 from-system origin 標為 legacy-finite，
保持原有限座標、索引及起算語意；兩軸不得混用新無限與舊有限排法，不因重開而轉换。新建介面使用無限排法。legacy-finite 不得帶 D10b 相位差。
~~~~

### D10b

現行位置：公理層第 644 行，相鄰格子相位差（stagger）。公理自標 M。
拆開後要跟著改的引用：D19a、D29、D30、D42、D58、I13、I25、I37、I52、I57、R22、R42、R60。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
交替相位差是指定無限軸在另一軸的 signed band 上採兩種平移：even band 位移 0，odd band 位移 δ；奇偶以數學模運算判定，負索引與正索引一致。δ 為合法非零整數毫米，並且不得是被位移軸節距的整數倍；各 band 內仍用原來源公式，不能把折線當整條直線。cell、band、全線及分段引用須分別保存；沒有 band 的單一位置若不唯一即拒絕。以下限制不增加多段相位表、逐格累加或其他尚未採納能力。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

只附加在 D29 的 REPEAT 或 REPEAT_PANEL 軸上，保存一個整數毫米相位差 δ，可正可負。省略該欄表示沒有相位差，格線維持 D29 的貫通直線。明示 0 不是省略：讀入即拒絕。不得把省略存成 0，也不得把非法值改存成 0。

相鄰單位是另一軸既有的帶符號 cell 索引，DSL 稱 band。不另建「排」或第二條軸。另一軸必須存在，且同為無限排法。同一份網格系統至多一軸有相位差（2026-10-16 使用者拍板）。兩軸同時錯開時，有些 cell 的四邊不是畫出的格線段，圍不成封閉的區域；板子以同一方向平行鋪滿一個面時，板縫也只能在一個方向錯開。

該軸未錯開座標 c(k) 沿用 D29。band 的奇偶以其最低位元判定：最低位元為 1（含 −1、−3）時，該段座標為 c(k)+δ；最低位元為 0（含 0、−2）時仍為 c(k)。再下一格回到 c(k)。δ 不必是間距的一半。間距：REPEAT 為 step，REPEAT_PANEL 為 panel+gap。

band 的切開用另一軸未加相位差的格線。u 線（常數 u、沿 v 延伸）在 band j 的沿線範圍是未錯開的 v(j)…v(j+1)；v 線同理。因此 cell(i,j) 仍是軸對齊矩形：它在某一軸上的兩條邊界，共用該軸對另一軸索引的同一個 δ。矩形邊長仍是兩軸間距。

相容例外：相位差軸數的比較只在提交（R56）時做。整體取代（D61：開新、恢復內建場景、載入場景檔、確認場景匯入、恢復資料、載入方案快照）、隔離重放（R46 重開、I31 交換包重建）及復原／重做（D60）不是提交，不做此比較，其中兩軸都已有相位差的系統照舊成立，求值、dump 與存回行為不變。兩軸系統上，提交後仍為兩軸而相位差值不變的編輯（例如改名稱、改間距）照常，移除一軸的編輯照常；提交後仍為兩軸而任一軸的相位差值有變者拒絕，要改須在同一筆編輯裡先移除一軸，再改剩下那軸的值。此時有些 cell 的四邊不全是畫出的格線段，相鄰 cell 可重疊或留空；不得把 cell 一律當成格線圍出的區域。

例：v 為 REPEAT，phase 0、step 1830、δ 400，u 無相位差。u 的第 0 格（band 0）裡，v 線位於 0、1830、3660；第 1 格位於 400、2230、4060；第 2 格回到 0、1830、3660。band −1 與 band 1 同一位移，band −2 與 band 0 不加 δ。

非零 δ 若為該軸間距的整數倍（含負倍數）則拒絕：奇數格的線會與偶數格的線重合，沒有錯開。錯誤須說明線會重合，並說明要貫通線應省略欄位。直接整數 0 在讀入時拒絕。參數引用先求值，求值後為 0 或間距整數倍同樣拒絕。相位與 δ 相加必須能以 int64 精確表示；被引用或被查詢的段座標另須在 D1。

相位差的來源與 D29 其他尺寸欄位相同：直接整數，或 D31 的 ParameterRef。每個欄位恰有一個來源。舊檔沒有 stagger token 即貫通直線。legacy-finite 的 EXPLICIT、SERIES、PANEL_LAYOUT 與 from-system origin 不得帶 stagger。

有相位差時，線段身分是（軸，索引 k，band）。同一 k 在不同 band 是不同段，座標不必相同。索引 k 是否存在仍按未錯開座標判斷；band 不把索引改號。段在另一軸的 cell 邊界停止。該邊界不是 D11 擋面。

本版任一軸已有相位差的主格不得有 D19 子網格。無相位差主格上既有的子網格維持。已有子網格的主格再加上相位差，整筆回滾。
~~~~

### D31

現行位置：公理層第 691 行，參數卡與欄位（ParameterSet / ParameterField；parameters/1）。公理自標 M。
拆開後要跟著改的引用：D1、D4、D6a、D6b、D6c、D7、D9、D10、D28、D29、D10b、D36、D37、D42、D44、D46、D54、D55、D60、D64、I56、R31、R53、R58。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
參數卡保存獨立 id、顯示名稱、欄位及順序；每欄以 (parameterId,fieldId) 為身分，保存 dimension（毫米有理數）、count（無單位非負整數）或 ratio（無單位有理數）以及字面值或結構化算式。名稱與順序不是引用身分，改名不重綁。算式允許括號、一元正負、加減乘除及欄位引用；字面小數／分數精確化為有理數，裸數字無單位，有單位常數明寫 mm。加減同量綱；乘法至少一端無單位；除以無單位數保留量綱，mm/mm 得無單位數，除零及其他量綱組合拒絕。來源只含參數欄位與常數，欄位層級的依賴圖無環；雙向跨卡引用不等於欄位循環。核心不從卡片名稱建立幾何或自動改綁舊來源；領域快捷配方與初值由模板提供；互動編輯與確認草稿由宿主管理。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

ParameterSet 是 World 獨立物件，保存卡片 id、非空名稱、欄位及其顯示順序；不擁有或自動建立幾何。
卡片有獨立 uint32 id 空間；欄位 id 在卡片內唯一。名稱不是身分，卡片可同名，同卡欄位顯示名稱須唯一。
卡片與欄位名稱均為非空有效 UTF-8、不含控制字元；同名判定依完整文字，不暗作大小寫或全半形轉換。
欄位引用 ParameterRef 為 `(parameterId, fieldId)`，不使用顯示名稱、欄位位置或畫布位置配對；改名、排序、拖移不重綁。
支援 grid-card-reference/1 時，D29 得以 D64 把一張卡片作為一個引用單位，另明示該卡兩個欄位與軸的對應。
卡片不因被整組引用而取得新型別；欄位型別、精確求值及欄位依賴圖維持本條。
每欄保存型別與一份字面值或結構化算式，三種型別為：
  (a) dimension：單位 mm 的有理數，可為負；
  (b) count：無單位非負整數；
  (c) ratio：無單位有理數，可為負。
數量和比例在運算中同屬無單位量，結果再按接收欄位型別驗證；整數比例不自動改成數量型別。
字面小數與分數均精確解析成有理數；直接輸入沿用欄位單位。
算式以 `=` 開頭，允許字面數、欄位引用、括號、一元正負與二元加減乘除。
算式中的裸數字為無單位數，有單位常數须明寫 mm；顯示用 `× / ÷ / −` 可對應相同運算節點。
引用透過來源選擇解析成固定身分，保存結構化運算節點；不以顯示字串或 JavaScript 程式作為引用身分。
加减兩端單位須相同；乘法至少一端無單位；除以無單位數保留原單位，mm 除以 mm 得無單位數。
無單位數除以 mm、mm 乘 mm 及其他面積／體積／反長度運算不在本能力內；除數不得為零。
可引用同卡或其他卡的欄位；來源僅參數欄位及常數，不反向引用幾何、材料、舊 spec 或工程套用。
參數圖的依賴單位是欄位；單卡內或跨卡的循環均拒絕，不能僅以卡片間有雙向關係就判定成環。
例如 A.x 引用 B.x、B.y 引用 A.y，若 A.y / B.x 無回引，仍是合法無環圖。
新參數不自動取代 D6b、發布材料版本或修改既有幾何來源；使用者須明選使用處。
單值、寬×長、W×H 是建立範本，不限制自訂欄位，也不表示座標向量或已放置角材。
`(915,1830)` 與 `W27H33` 可作尺寸組快捷輸入；須先展成具欄名、型別、單位的草稿供確認，不默默套用到物件。
~~~~

### D32

現行位置：公理層第 721 行，構件分件與接合規則版本（AssemblyRuleVersion；assembly-rule-authoring/1）。公理自標 M。
拆開後要跟著改的引用：D33、D54、D55、D56、I41、I66、R53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
版本化正交關係規則由具身分的成員、槽位及兩成員間的接合關係圖構成；成員局部軸明確、引用須存在且不能自接。關係類型和槽位 schema 由登記的契約提供；核心可驗平行／垂直、軸向映射、接觸面一致與閉合關係的一致性。幾何鄰接圖可有環，不代表來源依賴圖可有循環。規則定義、槽位綁定、可生成配方與生成實例是不同節點；可編輯某種關係不等於有任意規則的生成能力。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 可保存獨立的規則版本，具穩定規則身分、版本、名稱、角色槽位及局部接合定義。
規則以穩定槽位與接合身分引用，不以名稱、陣列順序、卡片位置或實例構件編號配對。
規則描述交接處的連續性、分段及端面與指定目標面的接觸關係；
不單憑角色名稱或一個全域數字推定全部局部接合。
本能力的接合語意為正交構件的幾何端接；不包含固定件、榫槽、施工順序或力學合格聲明。
規則不必綁定材料、網格、邊界或承載面；未綁定不代表規則無效。
其定義不得以某次算出的料長、合併外形或示意圖座標取代。
發布版本不可覆寫，修改建立新版本；草稿不是可引用版本。
定義合法與能產生施工幾何是不同命題，必須分別宣告能力與狀態。
~~~~

### D33

現行位置：公理層第 737 行，組構綁定（AssemblyBinding；assembly-rule-authoring/1）。公理自標 M。
拆開後要跟著改的引用：D54、D55、I41、R53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
槽位綁定保存規則固定版本、每個槽位的具型別尺寸來源與有身分的軸／面對應。引用完整但部分槽位未綁定可作為尚未完成的定義保存；引用缺失、型別不符或軸／面映射矛盾不是「未完成」，須拒絕。求值不得按欄位名稱、相等數值或相機方向自動推測映射；產生正式物件前須另通過生成配方的完備性與全部交易驗證。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 獨立物件，引用固定的 D32 規則版本，並保存角色槽位到角材材料來源的明確對應，
及已明選的接觸面與截面方向；沿用既有具型別材料／尺寸來源，不另建平行材料庫。
角色可使用相同或不同來源。缺少尚未選定的材料或方向可保存為未完成套用設定；
引用不存在或型別錯誤不是未完成設定，應拒絕。
發布新規則或材料版本不自動改動綁定；更新須明確選擇並預覽。
綁定本身不生成、擁有或隱含修改角材，不賦予越過既有公理的權利。
~~~~

### D36

現行位置：公理層第 765 行，斷面構件（ProfileMember；section-profile/1）。公理自標 M。
拆開後要跟著改的引用：D49。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
斷面中的矩形成員保存 id、尺寸來源、局部左上角 (u₀,v₀) 與明選的軸向映射。局部矩形為 [u₀,u₀+w]×[v₀,v₀+h]，w/h 由有身分的兩個尺寸欄位經方向映射求得；旋轉改變映射，不交換來源欄位身分。完整矩形須被斷面閉區域包含，與同斷面其他成員的內部不相交；接觸邊界合法。其軸向長度由所屬拉伸實例提供；本幾何求值不附加其他型別的角色、引用定位或端部接觸義務。模板登記允許的成員種類與尺寸來源。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

屬於一個斷面，保存 id、斷面 id、種類（角材 timber／面材 panel）、該種類的尺寸、方位，以及剖面矩形左上角的直接座標 (u0, v0)。
剖面是軸對齊矩形 R = [u0, u0+寬] × [v0, v0+高]，依 D35 必在 F 內。兩種構件的位置、方位、形狀內與不重疊規則相同，只差尺寸來源。
角材：截面 A×B，A / B 的來源沿用 D7 / D28 的既有型別（直接整數、D6b、D26 timber 欄位、D31 尺寸欄位）。方位只有兩值：A 沿 u（寬 A、高 B）或 A 沿 v（寬 B、高 A）。旋轉不交換 A / B 的身分，只改它們對應的軸。
面材：保存所用面材規格（D40）與斷面內寬度 w；板厚 t 取自規格，不逐構件填寫。方位只有兩值：厚沿 v（寬 w、高 t）或厚沿 u（寬 t、高 w）。矩形在正交斷面內只有這兩種方位，是定義推論。
左上角指 u 最小、v 最小的角點；旋轉後 (u0, v0) 仍指旋轉後占用矩形的左上角，不保存旋轉中心。
位置是直接座標，不保存對輪廓邊或其他構件的引用，也不收具名位移；D6a 只管參考線位置，I12 只管 D7 角材錨法，兩者都不適用於本條。
長度不宣告：構件長度 = 所屬拉伸件的 L（D37）。這與 D7「長度是環境推導的結果」同一原則，但來源是拉伸件，不是 R6 擋面。
構件不是 D7 角材，不取得角色、裁切優先級或擋面身分。
~~~~

### D37

現行位置：公理層第 780 行，拉伸件（ProfileRun；section-profile/1）。公理自標 M。
拆開後要跟著改的引用：D36、D54。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對局部有效閉區域 F 及長度 L>0，直線拉伸為 F×[0,L]；矩形成員 Cᵢ 的實體各為 Cᵢ×[0,L]。外部包絡與各成員實體分開，包絡只作參照，不加總為材料量。L 與輪廓各自保存來源，求值受 D1，不因外部型錄所示商品長度另設上限。未宣告的拼接、分段與補片不得由拉伸求值器自行生成。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

World 獨立物件，保存 id、斷面 id、長度 L 的來源，以及可省略的定位（D38）。
第一版只有直線拉伸。L 的來源為直接整數、D6b 或 D31 尺寸欄位（同 D28 的來源型別），不設與市售料長或板長相關的上限。
局部材料集合：每個構件 m 為 S_m = {(u,v,w) | (u,v)∈R_m, 0≤w≤L}。斷面包絡 E = {(u,v,w) | (u,v)∈F, 0≤w≤L} 只是參考幾何，不計材料量。
拉伸方向垂直於斷面是定義推論：斷面就是垂直於長軸的切面。同一斷面可被多條拉伸件引用，各有自己的 L 與定位。
反轉拉伸方向並把原點移到另一端，等於斷面在平面內左右鏡射，所以不另設鏡射參數。
~~~~

### D38

現行位置：公理層第 792 行，拉伸件定位（ProfilePlacement；section-profile/1）。公理自標 M。
拆開後要跟著改的引用：D4、D37、I73、R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
局部拉伸體的世界定位是 D2 形式的正交框架與局部到世界的精確映射。活引用保存宿主 typed id 與局部定位量，宿主改動按來源圖重算；一次取值快照則保存當時解析出的框架／座標，之後不建立隱含依賴。兩者不能因當前位置相同而互換。簡易定位與進階框架只有在能精確互推且保持相同幾何時才可轉換；不能靠近似或相機方向補足缺失軸。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

省略即未定位（D39）。
進階表示：原點 O（斷面局部 (0,0) 在 w=0 處的世界位置）與 D2 框架軸 U、V、N，U×V=N；
世界點 = O + u·U + v·V + w·N，拉伸沿 +N。U 由 V×N 推導，不另輸入；斷面在平面內的旋轉以 V 的四個選擇表達。
簡易表示：宿主、宿主面內的拉伸方向 d、宿主面上的基準點 (p, q)、圖面上方方向 up。宿主二選一：
  承載面引用——保存 World 中已放置承載面（D4，含 D5 空間成員）的 id，即時引用；宿主改變時依 R40 重算。
  空間牆取值——從已建立空間的某面牆或天花板取值，保存當下該面的框架 o_H、U_H、V_H、N_H 與有效範圍，
  並保存取值來源說明；介面須標明「依某空間牆取值，不隨空間變動」。來源說明只供顯示，不是身分或引用，不參與求值；
  取值後不保存對空間或其模型的引用，空間之後變動或刪除都不影響此定位。本條不建立空間與斷面之間的即時連動。
簡易表示依 R38 求值後必定得到一組進階表示，所以簡易是進階的子集。
簡易轉進階無損：改存求值所得的 O、U、V、N 並解除宿主，之後宿主改變不再帶動此拉伸件。
進階轉簡易有條件：須明選宿主；僅當 N 為宿主面內的軸、O 落在宿主平面與有效範圍內、V 對應合法的 up 時，反解出 (p, q)；
否則拒絕並列出不成立的項目，保持進階。
~~~~

### D41

現行位置：公理層第 819 行，完成面（FinishSurface；panel-fill/1）。公理自標 M。
拆開後要跟著改的引用：D4、D54、I53、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有向設計區域保存局部區域、D2 框架、法向側及明選障礙的 typed 引用。障礙先以其來源求得世界幾何，再依指定層區間判定正體積交集與投影；來源刪除或變動須進入完整依賴交易，不將最後一次投影靜默凍結成另一種來源。名稱、距離接近或畫面相交不自動建立障礙引用或集合歸屬。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

獨立的設計表面定義，保存 id、名稱（不是身分）、D3 邊界引用、
D2 框架（原點 O 與單位整數軸 U、V、N）、結構側符號 s∈{−1,+1}，以及明選的障礙集合。邊界的外輪廓扣孔即局部有效範圍 F；
位置及方向由框架明示，沒有高度預設，不把畫布位置當空間位置。
完成面局部 w=0，結構側單位向量 n=s·N。它不是 D4，不自動成為 D5／D21／D22 成員。
障礙集合是 D13 柱與 D14 樑的具型別引用（c<id>／b<id>）；集合內每件依 R41 對各層自動判定，
不保存逐件強制通過／裁切旗標；未列入者不按位置、名稱或所屬空間猜入。建立與修改時的預覽逐件列出本次納入的障礙、其投影 R_k 與 F 的關係（內部相交／只接觸／分離，R41）及各引用試排／衍生承載面可求值之對應層判定；尚無所需 t 或 h 時列出缺項；不據此推測該障礙是否曾 apply-proj，也不因此拒絕。
包樑側面、底面各是另一份完成面，不由本物件自動補齊。
~~~~

### D42

現行位置：公理層第 833 行，面材試排（PanelFill；panel-fill/1）。公理自標 M。
拆開後要跟著改的引用：D4、D10、D26、D43、D54、R37。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
來源化週期裁片由有限宿主區域、兩個有身分的正尺寸來源、間隙、明選軸映射、固定起算點、交替相位及比較參數來源定義。以 D10a／D10b 的同一週期機制列舉相關整數索引，再與有效閉區域精確求交得到全部片段；保存來源與輸入，不把生成片段另存為可編輯輪廓。尺寸欄位的軸向由 field id 的映射決定，不按大小重排。具體來源種類及有限列舉上限依模板能力契約。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

亦稱鋪排；為已提交的 World 定義。保存 id、完成面 id、D26 panel 固定版本引用、length 欄位沿 u 或 v（width 沿另一軸）、
起排點 (a_u,a_v)、縫寬來源、直排或交丁、交丁時的被錯開軸與相位差來源，以及 D44 門檻引用；
不保存逐片實體、裁切結果、縫段、承接結果或支撐結論。名稱若有，不是身分。
「長邊」一詞只指 D26 的 length 欄位，不論它的數值是否大於 width；正方形板也須明選 length 沿哪一軸。
板寬、板長及厚度取自同一明選材料版本；厚度須依 I52 已明設。起排點於建立或明確移動時以整數 mm 具體化（存直接整數，不存引用），
可在 F 內或外；輪廓或障礙改變不自動重置起排點。
縫寬與相位差的來源限 D10b 允許的集合：直接整數，或支援 `parameters/1` 時的 D31 尺寸欄位 ParameterRef；每欄恰一個來源。
直排不含相位差欄位。交丁只有一個被錯開軸 X 與一個相位差 δ：另一軸 Y 的板列索引 p 最低位元為 1（含負奇數）時，
X 軸的板片與縫整列平移 δ，最低位元為 0 時不平移；不逐列累加（D10b 同一奇偶函式；板列編號見 D43）。
所有排板量在完成面框架 (u,v) 求值（R42）；板片與縫只是推導結果。
完整覆蓋指 F 扣除孔及面材層障礙裁切區後，每處都推導為某片面材本體或某條板縫；不能把帶縫誤寫成板材本體連續覆蓋。
~~~~

### D43

現行位置：公理層第 851 行，鋪排縫線與身分（panel-fill/1）。公理自標 M。
拆開後要跟著改的引用：D10、D42、I13、I57、R42、R43、R44。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
裁片的追溯鍵包含來源實例、兩軸本體索引及切分量身分；相鄰本體之間的接縫只保留兩側均有有效裁片的子段。以與裁片邊界、宿主邊界及障礙投影的所有切點精確分段，不用視覺連續性合併不同來源。週期本體索引與以相鄰中心線界定的 cell 索引是不同座標約定；相互轉換須明列偏移，不能只改變字串中的名稱。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

對試排的每一軸 X，P_X 為該軸板尺寸（依 D42 的 length／width 對應），g 為縫寬，T_X=P_X+g。
第 k 片本體佔 [a_X+k·T_X, a_X+k·T_X+P_X)，第 k 條縫中心線 c_X(k)=a_X+k·T_X+P_X+⌊g/2⌋，k∈Z（與 D10a、D29 同一式）。
縫線身分為（試排 id，軸，signed k）；被錯開軸的縫線另含 band p：p 是另一軸的板列索引，
即 [c_Y(p−1), c_Y(p)] 之間、含第 p 列板本體的帶；p 最低位元為 1 時該段座標為 c_X(k)+δ。
此編號以板列為準：第 0 列（起排點所在列）不平移；它等於 D29 cell 索引加 1，奇偶因此相反，不得混用（I57）。
未錯開軸的縫線兩端無限延伸；被錯開軸的各段止於所屬 band 邊界；身分不因裁切、空段或可見範圍改變。
有效板縫 = 相鄰兩片面材分片之間、兩側皆有面材的正長度接縫段；以開區間計，單點不切斷。
外輪廓、孔邊及障礙裁切邊不是板縫；縫線上只有一側有板的部分不是有效板縫。
有效板縫段（面材層結果）與 D10 鋪排來源主格的可見段（衍生承載面結果）是不同結果，須分開表示。
既有 guide、grid 與角材引用縫線時沿原引用與 I8a 預覽契約，不以畫面最近線重配。
~~~~

### D44

現行位置：公理層第 868 行，承接門檻與結果（panel-fill/1）。公理自標 M。
拆開後要跟著改的引用：D42、I56。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對有方向的分段參照線與兩側有效區域，分別求其上每個子段相鄰於該線的連續覆蓋寬度；輸出左右各自的精確值與其來源。比較門檻必須是明示引用的正尺寸有理數 X，各側依同一 X 比較，不取整、不在求值器補預設、不把兩側寬度相加冒充單側連續寬度。比較結果是資料；是否警告、拒絕提交或仍可保存由使用契約決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

每份試排以 ParameterRef 明確引用一個 D31 dimension 欄位作承接門檻 X。
建立流程預設提議新建一個值為 8 mm 的 D31 dimension 欄位，使用者可改選既有 dimension 欄位；提交的試排必帶明確引用，並顯示其卡片、欄位名稱及引用。
執行器不得另藏可覆蓋引用的常數。X 求值後須為正；只作比較，不生成幾何座標，保留 D31 有理數語意。
改名／排序不改引用。引用必須存在且型別為 dimension：刪除被引用欄位依 I38 拒絕；
改型別、改算式或改值使引用不合（非 dimension，或 X≤0）的交易整筆拒絕。已提交的 World 中不存在「未定」的承接結果。
承接結果依 R43 逐縫段判定，只有「已承接」與「承接不足」兩種；承接不足顯示紅色及兩側實際寬度，不阻擋合法試排的建立、修改或保存。
8 mm 是使用者依現場經驗給定的承接下限（Q39-X），沒有規範出處；實寬 27 mm 角材在 3 mm 縫下以幾何中心對齊作對照時兩側各壓 12 mm，那是常態參考，不是第二道門檻。at-line 的實際承接寬度仍依 I13／R42／R43 求值。
~~~~

### D52

現行位置：公理層第 959 行，共享來源平面、房間集合與房間記錄（SourcePlane / RoomCollection / RoomRecord；source-room-collection/1）。公理自標 H。
拆開後要跟著改的引用：D51、I63。

**核心條文草案**

一個來源平面可以掛有限的附件。附件有容量和唯一性，核心只檢查引用存在。

**木工模板條文草案**

木工與建築模板的第一個附件是房間集合和房間記錄。房間不是幾何核心的內建種類。

### D53

現行位置：公理層第 969 行，房間候選草稿（RoomCandidateDraft；room-candidate-drafts/1）。公理自標 H。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**

宿主可以在正式世界之外保存一份未提交草稿，草稿有數量上限，提交前不改世界。

**木工模板條文草案**

這個模板的草稿內容是房間外環。外環的正交和整數毫米用核心的規則檢查，房間這個種類由模板登記。

### D54

現行位置：公理層第 978 行，身分類別（IdentityClass）。公理自標 H。
拆開後要跟著改的引用：D19a、D55、D63、I34、I39、I66、R53。

**核心條文草案**

每一種身分屬於一個類別。類別決定跨專案匯入時保留原號還是重配，不因對方碰巧有空號而改變。

**木工模板條文草案**

木工模板登記自己的類別表，包含角材、面材、柱、樑、組構和其他木工種類。核心不內建這張表。

### D55

現行位置：公理層第 993 行，跨專案定義匯入（DefinitionImport；definition-import/1）。公理自標 H。
拆開後要跟著改的引用：D25、D51、I39。

**核心條文草案**

從另一份專案匯入定義時，先取依賴閉包，再依身分類別重配，整筆成功才提交。

**木工模板條文草案**

哪些木工定義可以進入閉包，由木工模板的型別白名單決定。核心不認得角材或組構這兩個名字。

### D56

現行位置：公理層第 1001 行，編輯草稿（EditDraft）。公理自標 H。
拆開後要跟著改的引用：D53、D57。

**核心條文草案**

未提交的編輯資料留在世界之外，記錄使用者對某個目標的原始輸入。

**木工模板條文草案**

木工模板的草稿可以記組構和擋面的輸入。這些欄位是模板的，不是核心的內建欄位。

### D59

現行位置：公理層第 1048 行，物件身分帳（IdentityLedger；identity-ledger/1）。公理自標 H。
拆開後要跟著改的引用：D9、D25、D54、I39、I66、I70、R57。

本節只做分類，不改涵蓋範圍。現行受涵蓋的是七類：邊界面、承載面、RC 柱、RC 樑、角材、參數卡、參數欄位。屬於 D34 組構實例所有的角材排除在外。其他型別不帶記號，延續一律未知。分層契約第 75 行把特定型別涵蓋域交給 H。下面只把算法和這份現行清單分開描述。

**核心條文草案**（現行機制，不決定涵蓋名單）

世界可以啟用身分帳。啟用之後，受涵蓋物件在提交時結算存在期與配號。記號不參與幾何推導，也不進入幾何雜湊。核心不從模板名稱增刪受涵蓋型別。

**宿主契約草案**（現行涵蓋域，原樣）

受涵蓋物件與身分鍵維持公理層第 1050–1054 行：邊界面 (boundary, id)、承載面 (placement, id)、RC 柱 (column, id)、RC 樑 (beam, id)、角材 (timber, id)、參數卡 (parameter, id)、參數欄位 (parameter-field, parameterId, fieldId)。屬於 D34 組構實例所有權對應的角材不受涵蓋。其他型別不帶記號，其延續一律未知（R57）。這份清單由 H 負責，不因換木工模板而改寫。

### D63

現行位置：公理層第 1094 行，保存的空間模型（SavedSpaceModel）。公理自標 H。
拆開後要跟著改的引用：R40、R59。

**核心條文草案**

專案可以保存一份由來源快照推出的模型。快照之後不跟著活世界變，要更新就整筆替換來源。

**木工模板條文草案**

木工模板決定這份模型納入哪些角材和拉伸件。核心只負責按交代的來源求值。

### I3

現行位置：公理層第 1120 行，fixity 陣列長度 = 邊數；不寫 → 全 FIXED。。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
逐邊屬性陣列若由型別契約宣告，必須與其有身分的環邊一一對應；改輪廓時依同一候選驗證來源與屬性，不容許短陣列、越界或按外觀補配。核心不為任意區域默設特定屬性值；現行預設及合法值由以下模板 schema 提供。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

fixity 陣列長度 = 邊數；不寫 → 全 FIXED。
~~~~

### I4

現行位置：公理層第 1127 行，Space 建構。公理自標 M。
拆開後要跟著改的引用：D21、R11。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
集合建構先驗所有 typed 成員存在及定位引用符合集合契約，再對明確要求的區間一致性、唯一性與正長度逐一驗證。空集合是合法集合但不具有有限範圍或封閉體積。改成員清單為一次重宣告，須依 I8 驗證完整候選；核心不將特定槽位的數量或排列套用到一般邊界殼。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

Space 建構：成員數 ≥0；零成員 = 空容器，直接成立。
   有成員時：各成員邊界面恰有一個承載面；槽位一致性（同軸區間相等、
   無同槽位衝突、下界<上界）全過才成立。加面入空間 = 重宣告成員清單，
   走同一道建構子驗證。
~~~~

### I5

現行位置：公理層第 1137 行，角材放置。公理自標 M。
拆開後要跟著改的引用：D6、D45、I15、I22、I69、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
區域包含判式為完整矩形閉區域 Q⊆F；須檢查整個區域及所有孔，不能只驗錨點、兩角點或外接盒。Q 與 F 的邊界重合、端點相接不因此算越界；只有 Q 的點落在 F 之外才失敗。哪個物件的哪個面要通過此判式，由該型別契約指定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

角材放置：錨點在有效範圍內，且整個 A0 矩形 ⊆ 有效範圍、不跨任何孔。
   （多邊形下不再是「兩角點」捷徑——角材整支要在界內：有效範圍是外環內部與邊界、扣掉孔內部（D3），所以任何部分都不得在外輪廓之外（含輪廓上的凹口），也不得進入孔。RC 牆面在輪廓之外，不能穿過；柱子要先投影進這個面（apply-proj，R8），之後它的範圍不在有效範圍內，才同樣不能穿過。貼著邊、切齊仍在界內。貼上去合不合法（端面能不能頂、哪種角色可以頂）另依 I6、I19、I20。與已放角材之間同樣不能互相穿過，見 I11。）
~~~~

### I7

現行位置：公理層第 1147 行，參考線有效性。公理自標 M。
拆開後要跟著改的引用：D10a、I10、R13。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
來源化直線先驗 typed 引用存在、來源 schema、依賴無環及最終整數位置符合 D1，再算可見片段。直線位置不必落在宿主外接區間；可見片段為空不表示直線不存在。建立、修改與重宣告使用同一求值與驗證器。涉及具型別物件求值的來源，必須依 I9 在來源可求值後使用，不能引用尚未完成狀態。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

參考線有效性：LOCAL 引用式與 DATUM 交線推導的座標均須符合 D1；
   不再要求落在有效範圍的該軸外接區間。create / move / 重宣告都用同一規則，
   可見段為空仍是存在的直線。LOCAL 引用的量不存在、違反 D6a 同軸／同面要求 → 拒絕；
   參考線互相引用成環 → 拒絕（R3 不猜）。引用已放角材者受 I9 順序約束。
~~~~

### I8

現行位置：公理層第 1161 行，重宣告（同名 id 再宣告）= 交易。公理自標 M。
拆開後要跟著改的引用：D6b、D7、D8、D19、D39、D60、I4、I8a、I10、I13、I17、I23、I30、I49、I55、I64、R2、R4、R5、R6、R8、R20、R31、R40、R60。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

同一個 id 再宣告是一筆候選交易。候選裡先解析來源，再重算全部遞移依賴，全部驗證通過才一次替換正式世界；失敗、取消或過期都留在舊世界。

**木工模板條文草案**

木工模板登記自己的依賴鏈：邊界面、承載面、參考線、角材、空間，以及材料版本和參數改綁。模板只能把這條鏈交進同一筆候選，不能自己寫正式世界。

### I8a

現行位置：公理層第 1176 行，影響預覽。公理自標 M。
拆開後要跟著改的引用：D7、D19、D19a、D29、D43、I10、I13、I23、I30、I37、I39、I49、I55、I64、I69、I71、R2、R5、R6、R21、R31、R44、R56、R57、R58、R60。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

會改動已被引用來源的操作，先對完整候選做唯讀預覽。影響集合是具型別依賴圖的遞移閉包。確認時重跑同一候選；過期、違規或取消都不改正式世界。

**木工模板條文草案**

木工模板規定：被角材引用的線、邊和擋面必須進預覽。預覽逐支列出角材的新舊中線與長度，以及它違反的木工條文。

### I9

現行位置：公理層第 1216 行，DSL 順序即依賴順序。公理自標 M。
拆開後要跟著改的引用：D6b、D25、I7、I8、I8a、I72、R4、R19、R55、R60。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
依序提交的定義操作依序解析具型別來源，尚不存在的來源不可前向引用。明示原子包可先讀完包內定義，再依欄位／物件層級的無環依賴圖求值；兩種宣告單位不能混用；場景命令語法與逐行 parser 由宿主轉接為這些定義操作。完成候選前須檢查每個已登記型別的終態合法性，不能因具備可暫存資料結構就把未完成狀態當正式物件；不同型別可具有不同終態契約。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

DSL 順序即依賴順序：向前參照不存在的 id 自然失敗；
   收尾時仍有未放置角材 → 整份拒絕。
參數整包是明示的原子宣告單位：先讀完包內卡片與欄位定義，再檢查其完整欄位依賴圖並求值。
包內可引用本包其他欄位；包外來源須已存在於候選世界。包結束仍缺來源或成環即整包拒絕，不留半份卡片。
dump 可把全部參數定義放入一個原子包，先於其幾何使用者輸出；不能要求合法欄位圖一定能按卡片整張排序。
~~~~

### I10

現行位置：公理層第 1227 行，網格。公理自標 M。
拆開後要跟著改的引用：D10、D10a、I25、I25a、I35、I37、R13。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有限格網驗來源模式、每軸精確座標與有序索引、宿主存在、主格／子格關係及既有執行器容量。超出容量必須拒絕，不能截斷或以畫面抽樣代替正式格網。座標生成不讀方向角色設定；該設定的合法值及建立預設由模板驗證。有限格網的座標數上限不得誤用為無限來源可查索引範圍。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

網格：本條是網格集合的生成限制，不受 I7 對獨立參考線可見性的放寬影響。
    每軸的定義所推導出的座標序列必須嚴格遞增、且每條都落在承載面該軸的
    外接區間內（EXPLICIT / SERIES 推不出合法序列即拒絕；PANEL_LAYOUT 的條數由範圍
    決定，見 D10a）。單軸條數有上限，推導超限 → 拒絕。
    兩軸皆未宣告 → 拒絕；某軸推導為零條線 → 合法。
    `main_along` 只接受 u 或 v；宣告時須有對應格線軸的來源定義
    （沿 u 的線來自 v 座標軸，沿 v 的線來自 u 座標軸）。
    合法面材來源推導出零條線時仍合法。角色標註從定義及推導線求得，
    不另存逐線座標或角材清單。
    同一 grid id 可第二行補另一軸，也可重宣告既有的軸（來源種類可換），
    但受 I23 的追溯與重算規則限制（**引用鎖已於 2026-09-18 解除**，改走 I8a 影響預覽）。
    網格的新增與重宣告一律走 I8 交易：
    建候選 → 全量重驗 → 全過才提交、否則整筆回滾。
    每面最多一個主網格，可有多個子網格。全 World 的主格與子格合計上限為 16 組；有限來源及子格單軸上限為64條線，超限即拒絕，不截斷。無限主格不展開保存全部線，其每次查詢容量另依I37。
    本條 EXPLICIT/SERIES/PANEL_LAYOUT 及 main_along 的來源要求適用主網格；子網格的來源合法性依 I25，其推導座標亦須嚴格遞增且在承載面外接區間內。

本條承載面、範圍及主格／子格數量要求適用套用後的 ReferenceGrid；獨立網格系統另依 I37。
從系統套用的 EXPLICIT／SERIES 仍須全部落在範圍內，不能裁掉超界座標以改變既有索引。
from-binding 的無限主格不受「全部來源線須在範圍內」限制；來源線在面外仍存在，有限可見段按輪廓裁切。
~~~~

### I11

現行位置：公理層第 1253 行，實體不重疊。公理自標 M。
拆開後要跟著改的引用：D6、D7、D45、I5、I15、I30、I45、I50、I53、I69、R18。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
兩個閉區域的內部具有正面積交集才構成二維重疊；共享邊或端點面積為零。核心提供此精確判式，呼叫契約必須明列參與者集合及比較配對，不能由共用幾何型別推導全世界互斥。正式建立、重宣告與全量重驗對相同檢查域必須給出相同結果。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

實體不重疊：同一承載面上，任兩支已放角材的 footprint 正面積不得相交
    （端點/邊相接 = 零面積 = 合法接觸）。明寫與 auto 放置都過這關，
    world_revalidate 也兩兩重驗。
~~~~

### I12

現行位置：公理層第 1262 行，錨法二選一。公理自標 M。
拆開後要跟著改的引用：D36。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
引用定位的候選保存來源鍵、位置關係與必要選擇量，求值後得到位置而不把其凍結為無來源座標。可用的錨法、哪些型別允許直接局部座標以及哪些舊命令已作廢，均由該型別的建立契約明列；抽出位置求值器不能擴充既有公開輸入語法。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

錨法二選一：`at-line`（中線對齊一條線）、`at-face`（側向貼齊一個佔用邊界）。
    2026-09-18 拍板**廢除** `at`（自由 uv）與 `at-guides`：自由座標是來歷不明的數字
    （D6a 同一原則）。長度不再由錨法配對決定——長度一律推導（D7、R6）。
~~~~

### I13

現行位置：公理層第 1271 行，錨法幾何約束。公理自標 M。
拆開後要跟著改的引用：D4、D7、D10a、D11、D14、D18、D44、D45、I8a、I25、I69、R2、R4、R6、R13。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有序截面尺寸對軸向的映射、來源線／面的位置與放置方向共同決定矩形足跡。以整數寬度 A 在中線兩側展開時，負 cross 側取 floor(A/2)，正側取 A−floor(A/2)；不能交換來源尺寸身分來配合畫面。引用帶有限父區域或 band 的線段時，依該引用種類明確驗足跡的受限方向，不能將可見段、父格邊或查詢裁切邊當成實體接觸來源。引用改變依 I8／I8a 重求完整姿態及下游。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

錨法幾何約束：
    at-line——引用一條參考線（D6）或格線（D10/D10a/D19 的（軸，索引），或 D19a 的完整來源規則線引用）；中線對齊的幾何約束相同，直接引用子線另受下列局部範圍限制。
            線的座標軸必須 ⊥ 角材長度軸；中線 = 該線的位置（D6a 求值結果）；
            footprint = 中線 ± ⌊w/2⌋/⌈w/2⌉（奇數寬多的 1mm 恆在 +cross 側）。
    at-face——引用一個**平行於長度軸的佔用邊界**（D11 的三種來源），
            用 D18 的寫法指名：外輪廓邊 `e<i>`、孔邊 `h<i>e<j>`、
            已放角材 `t<id>`（取該角材平行於本支長度軸的兩個側面，二選一同 R21(d) 的規矩）；
            footprint 貼齊該邊、向材料側展一個寬度；孔邊材料側 = 外向法線側。
    兩者存的都是**引用**而非座標；被引用者移動 → 重新推導（R6(e)），並走 I8a 預覽。
    at-line 的格線引用包含 D19 子格，沿用 at-line grid <id> <axis> <index>。直接引用子線時，角材的完整 footprint 必須包含於該子格矩形 C，並照常通過有效面包含、兩端擋面、碰撞及角色檢查。子格邊界不能代替實際擋面。
    直接引用 D19a 來源規則線時，保存完整線引用，角材的完整 footprint 同樣須包含於該線所屬 cell 矩形 C，並通過上述有效面、擋面、碰撞及角色檢查。來源規則線及 cell 邊界均不是 D11 擋面，不能代替 R6 的實際支撐。D6a 引用該線座標時只取得位置，不把此 cell 範圍附加給獨立參考線。
    有 D10b 相位差的格線須寫成 at-line grid <id> <axis> <index> band <band>。缺 band 拒絕，不默認 band 0；無相位差的線寫上 band 也拒絕。角材沿該線走向的範圍必須落在該 band 未錯開 cell 的閉區間內，橫向仍只受有效面與碰撞限制。band 邊界不能代替實際擋面。
    引用 D10 鋪排來源主格被錯開軸的線時同樣須寫 band；band 是另一軸的板列索引 p（D43），角材沿該線走向的範圍須落在 [c_Y(p−1), c_Y(p)] 經 R41 映射到板背框架後的閉區間內（s=−1 且 Y=v 時為 [−c_v(p), −c_v(p−1)]），橫向仍只受有效面與碰撞限制；band 邊界不是擋面，兩端仍須各有真實擋面（R6）。
~~~~

### I15

現行位置：公理層第 1293 行，柱。公理自標 M。
拆開後要跟著改的引用：D22、I53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
長方體的每軸區間必須嚴格遞增且受 D1；指定的二維足跡包含與正面積相交判式依 I5、I11 精確計算。若契約只指定平面足跡域，就必須在該域檢查，不能偷偷改成三維正體積相交，亦不能因某些高度不相交而略過原定的足跡衝突。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

柱：AABB 非空（三軸 lo<hi)；屬空間時足跡（x/y 區間）⊆ 空間平面範圍；
    任兩柱 x/y 正面積不得相交（邊相接 = 零面積 = 合法）。游離柱不檢範圍。
~~~~

### I16

現行位置：公理層第 1301 行，樑。公理自標 M。
拆開後要跟著改的引用：D22。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有向長方體求值檢查主軸、端點、兩橫向尺寸、有效區間與來源存在性；未被使用契約要求的物件配對不自動加入碰撞驗證。查詢或顯示可以呈現交集，但未檢查的配對不得被標成「無碰撞」或「已驗證」。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

樑：AABB 非空；屬空間時足跡 ⊆ 空間平面範圍。柱-樑、樑-樑相交不檢（不同層）。
~~~~

### I17

現行位置：公理層第 1308 行，空間重宣告使推導範圍縮小 → 柱樑一併重驗，不過整筆回滾（I8 同軌）;。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
集合或宿主來源變更時，沿明確依賴閉包重新求值並按各型別契約驗證；刪除採用契約指定的拒絕、解除歸屬或刪除策略，不能由一般圖遍歷自行決定。解除歸屬與刪物件不同，解除後仍須保存原物件 id、定義與可獨立求值的幾何。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

空間重宣告使推導範圍縮小 → 柱樑一併重驗，不過整筆回滾（I8 同軌）;
    刪空間 → 其柱樑變游離（space_id=0)，不連坐刪除。
~~~~

### I22

現行位置：公理層第 1339 行，延伸段。公理自標 M。
拆開後要跟著改的引用：D15、D16、I19、I50、R18、R19、R20。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
定位來源區間與實例區間按 D16 精確分解；各分量的長度、全覆蓋與端點接觸均由核心判式求值。不同分量是否改變可用接觸候選、優先序或端部義務由顯式策略選擇，不能從「區間伸出」這個幾何結果自行賦予豁免。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

延伸段：只有 `boundary` 可有延伸段（其他角色的 footprint 必須完整落在兩個擋面之間，
    無「超出定位邊」的段）。延伸段的端面仍須恰有一個涵蓋全寬的擋面（R6(d)），
    但**不受 I19 限制**——可以頂任何優先級的側面，被頂的料不因此被裁斷
    （幾何上：被頂者 footprint 不變）。延伸段 ⊆ 有效範圍（I5）——因此只有凹角
    （反射角）端點才可能延伸，凸角處延伸即出界，不需另立規則。
    延伸段的側面作為別支料的擋面時，以優先級 2 計（懸出段不是固定邊界，
    主支端面不得頂它；可頂它的只有平行主支軸且優先級大於 2 的 custom 料）。
    違反本條 → 拒絕（V_EXTENSION），
    訊息指名料件、定位邊與超出的區間。
~~~~

### I23

現行位置：公理層第 1354 行，網格引用的追溯與重算（2026-09-18 目的翻轉）。公理自標 M。
拆開後要跟著改的引用：D62、I10、I35、R4、R13。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
來源引用由 typed id、穩定子元素 key 與來源定義決定；裁切後不可見、視窗外或幾何值沒變，不等於引用已消失。來源重宣告須按原引用規則重求子元素；不能依最近座標改綁。若引用消失或使用中保護不允許變更，整筆候選拒絕；可重算與不可改動兩種來源契約須分別登記。僅改變附加的使用預設，不得重寫已建立物件的明選設定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

網格引用的追溯與重算（2026-09-18 目的翻轉：原為「引用鎖」，見下）：
    (a) 網格重宣告使某條被 at-line 錨定的線移動 → **不再直接拒絕**，
        改為重新推導引用它的角材並走 I8a 影響預覽；零違規且使用者確認才提交，
        否則整筆回滾、World 留在舊狀態。
    (b) 承載面縮小使某條被錨定的線**不再產生** → 該引用失去指涉對象，
        無從重算 → 拒絕（V_GRID_LOCKED），整筆回滾（I8 同軌）。
    (c) 刪除網格時其上有角材錨定 → 同 (b)，拒絕（V_GRID_LOCKED）。
    (d) 只改 `main_along` 而不改格線座標時，既有角材保留其 D15
        宣告角色與原格線索引；新的格線角色預設只作用於後續放置，
        不觸發既有角材角色重寫。
    不再產生索引不同於 D6 直線存在但可見段為空，後者不會自動失去引用。
    本條保護的是「索引指向哪一條線」這項追溯資訊仍然指得到東西；
    幾何本身不再由凍結保護，改由 R6(e) 的重算 + I8a 預覽保護。
    **原條文**（至 2026-09-17）要求「新舊兩份定義下推導出同一座標」，
    任何會移動已錨定線的改動一律拒絕。那是為了配合 R6(e) 的凍結語意；
    凍結既已反轉為重算，此鎖隨之解除——移動是合法操作，只是必須先看預覽。
    本條適用主格與 D19 手動子格；依賴鏈包含主格 → 子格 → guide／角材，以及其後的引用。座標改動重新推導；仍被 guide／角材引用的子線索引不再生成，或刪除仍被 guide／角材引用的子格，均拒絕且保留舊 World。不得把引用改指到鄰線。無引用的子線可因減少等分數而消失，保留下來且仍被引用的索引按其新位置重算。D19a 來源規則另依 I25a 保護其等分數、selector 及刪除，不將手動子格的此項可重算編輯套用於來源規則。
    主格仍有子格時不得刪除。有限主格在仍有子格的交易結果中不得增減任一軸推導線數；此限制同樣適用有效面變更及拆面造成的線數變化。先處理子格與下游引用，才可改動有限來源線數。
    有限主格線數相同的重宣告依既有索引語意視為線移動；須重新驗證父格四邊仍相鄰，並以 I8a 顯示其新舊範圍。這不宣稱有限父線具永久身份，也不按最近座標自動改綁。
    無限主格以signed k與lattice-cell保持來源身份，不以可見條數或sample密度限制父格變更；縮小範圍只改可見段，不能據此認定線不存在。仍须重驗C∩F、子線、guide與角材的各自合法性，任一失敗整筆回滾。
~~~~

### I24

現行位置：公理層第 1381 行，相位差守門。公理自標 M。
拆開後要跟著改的引用：I37、I52、R22。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
交替相位差只在宣告能力容許的無限軸間使用；δ=0、δ 為節距整數倍、缺少所需 band、或在不需要 band 時多寫 band，都拒絕。band 為 signed cell 身分，不能用視窗範圍判不存在；同索引在不同 band 的片段分別輸出並帶身分。精確查詢超容量不能丟段。相位差與局部細分的首版不共存限制、已有引用因新增／去除相位差而缺失必要資料的情形，都在完整候選內拒絕，不補猜或悄悄刪欄位。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

相位差守門：相位差只接受 D29 無限軸上的一個整數毫米。省略為貫通線。另一軸不存在、不是無限排法，或本軸不是 REPEAT／REPEAT_PANEL，一律拒絕。每一筆提交（R56）比較提交前後同一網格系統的相位差：由不足兩軸變為兩軸（含新建時兩軸都填、一軸已有再加另一軸）→ 拒絕，訊息說明同一份網格只能有一軸錯開；提交後仍為兩軸而任一軸的相位差值有變 → 拒絕，訊息說明要先在同一筆編輯裡移除一軸；要改成錯開另一個方向，請在同一筆編輯裡移除這一軸的相位差、再設另一軸。提交後仍為兩軸而相位差值不變（改名稱、改間距等）、以及移除一軸，照常。整體取代、隔離重放及復原／重做不是提交，不做此比較。相位差值以該系統自己的相位差欄位求出的值為準；相位差若引用參數欄位，改那張參數卡的值不算改相位差值。
    明示 stagger 0 拒絕。非零值若為該軸間距的整數倍（含負倍數）拒絕，並說明奇偶格的線會重合、要貫通應省略欄位；不得改存成 0。參數引用在候選內先求值，求值後為 0 或間距整數倍同樣拒絕。
    放置到有相位差的線必須寫 at-line grid <id> <axis> <index> band <band>。缺 band 拒絕，不默認 0。無相位差的線寫 band 也拒絕。band 是另一軸的帶符號 cell 索引，不要求它落在本次視窗內。
    角材 footprint 沿該線走向的範圍必須落在該 band 未錯開 cell 的閉區間內（含邊界）。線的寬度方向不受該 cell 限制。band 邊界不是擋面，兩端仍須各有真實擋面（R6）。越界整筆拒絕。
    既有放置與本次軸定義一起重驗。加上相位差後，舊的無 band 放置變為缺 band；去掉相位差後，舊的 band 放置變為多餘。兩者都整筆回滾，不暗中補 0 或刪掉 band。
    任一軸已有相位差的主格不得新增或保留子網格。已有子網格的主格加上相位差，整筆回滾。無相位差主格的子網格不受影響。
    同一索引在一次查詢中，每個相交 band 各成一段並標明 band。段數超過容量時 exact 查詢拒絕，不得丟段。索引是否存在仍按未錯開座標判斷。
    新建、重宣告及上游變更都在候選世界全量重驗；失敗整筆回滾，並指出系統、軸與拒絕原因。
~~~~

### I25a

現行位置：公理層第 1403 行，來源子規則守門。公理自標 M。
拆開後要跟著改的引用：I23、I37、R32。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

來源子規則先驗父格、軸型別、key 唯一和整數整除，再做精確等分。使用中的規則不得改成另一個幾何；失敗整筆退回。

**木工模板條文草案**

木工模板規定：正式參考線或角材線已經引用這條規則時，不得改等分數或刪除。這是放置對格線的使用保護，不是等分算法本身。

### I29

現行位置：公理層第 1429 行，組合守門。公理自標 M。
拆開後要跟著改的引用：R27。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
組合的來源須存在、型別正確且依賴無環，布林輸入全部可解算；先執行各來源型別本來要求的驗證，再做組合，KEEP 或 UNION 不豁免來源契約。結果的每個體積連通分量及內腔殼均驗 I28。完全扣除是合法空集合；全部分量、孔與尺寸必須保留，不能為配合輸出格式只留最大塊或重新填補。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

組合守門：D23 引用須存在、型別正確、依賴無環，布林輸入均須已解算。
    既有柱柱、同承載面角材等不變量先檢查，KEEP / UNION 不構成豁免。
    布林後逐一檢查每個體積連通分量，含全部內腔殼；任何分量非法即整筆拒絕。
    完全扣除是合法 EMPTY；多塊必完整輸出；尺寸、孔洞、分量不得因目標格式限制被靜默丟棄。
~~~~

### I30

現行位置：公理層第 1439 行，擴充交易與依賴。公理自標 M。
拆開後要跟著改的引用：I50、R11。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
幾何節點及其全部 typed 來源納入同一依賴圖；改值、重綁或刪除影響所有遞移下游。仍被引用的來源不得自行轉成快照或級聯刪除；刪除策略以登記契約為準。新求得的幾何只可用於已宣告的用途，不能因形狀等價而加入原先沒有的接觸來源或碰撞比較域。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

擴充交易與依賴：I8 擴及規格→擠出、輪廓→承載面→擠出／殼→複合空間／組合，
    以及它們的輸出依賴。重宣告先在候選世界求完整依賴閉包，全部成立才提交；
    刪除仍被引用的來源拒絕，除非同一顯式交易也移除／重宣告全部依賴者。
    成員與運算清單修改也是重宣告；不以局部成功留下半套模型。受影響角材仍須走 I8a。
    新擠出實體、殼與組合不自動成為 D11 擋面，也不擴大 I11 的既有碰撞檢查域。
~~~~

### I34

現行位置：公理層第 1475 行，工程版本完整性。公理自標 M。
拆開後要跟著改的引用：D9、D47、D55、I67。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

版本以穩定 id、版號和內容指紋一起識別。已發布的內容不能原地改。同身分同內容可以重用，同身分不同內容拒絕。

**木工模板條文草案**

木工模板把材料版本和做法版本送進這條規則。已被引用的木工版本不得刪除；封存仍可解析。

### I35

現行位置：公理層第 1485 行，套用合法性。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
具型別來源的解析成功只表示值與引用合法，仍須執行目標物件的完整幾何、來源範圍、容量與領域驗證；不能用新來源類型豁免既有約束。來源改變、覆寫及版本升級都在完整候選中重算全部下游，任一失敗整包回滾且保留原有效引用。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

套用合法性：來源有效值受 D1 / D7 / D10a 約束；未設定、循環、型別不合或引用懸空整包拒絕。
子格的父線數／索引／整除保護仍依 I23 / I25；容量依 I10 檢查整個 World，不能逐目標檢查後繞過總量。
不自動刪子格、改綁最近索引、改角材角色或忽略失敗目標。材料引用不放寬碰撞、錨點、擋面或放置順序。
~~~~

### I37

現行位置：公理層第 1500 行，網格系統與配置。公理自標 M。
拆開後要跟著改的引用：D10、D19a、D62、I10、I25a、R44。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
無限格網定義驗精確步距／本體／間隙及 signed 索引；配置驗穩定頂點鍵、精確比例和 D1 入值。精確查詢的有限範圍與容量只限制本次列舉，不改變無限來源；無可見線仍可存在。所有引用和配置在來源變更後重新驗證；顯示抽樣不得作合法性依據。角色預設、現有命令白名單及固定來源限制另由模板契約驗證。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

網格系統與配置：系統及配置各有獨立 uint32 id 空間（含 0），最多16份系統及32份配置。
拒絕缺名稱、無效 UTF-8、超長名稱、兩軸皆空、非法數值或新舊排法混用；舊有限來源仍按原64條限制驗證。
無限來源或配置不因範圍內線多、未指定範圍或沒有可見線而非法；64條僅限制一次具體查詢的每軸回傳量。
exact 查詢超限明確拒絕該查詢，不污染World；sample 須明示 stride 與非完整性，不得截斷冒充完整幾何。
signed 索引、比例及算術超出可表達範圍，或實際幾何不符合 D1 時明確拒絕；不得回繞、用浮點近似或暗取整。
main_along 可未設定，否則依 I10 要求具有對應格線來源；不猜主支方向。
配置須引用現存邊界、兩軸均有無限來源的系統、有效頂點key與精確cell錨點；單軸來源不能假裝有cell。
主格套用配置時，承載面必須引用同一邊界，並遵守每面最多一個主格及全部幾何／材料依賴限制。
系統、配置、keyed邊界新增與修改均在候選世界驗證；重算所有配置、主格、子格、guide 與角材。
有 D19a 來源規則時，同一候選並依 I25a 驗全部規則、所有配置的繼承與衝突及正式規則線引用；圖形介面預覽列出受影響來源、各配置及已引用物件，確認同一候選後整筆提交。
任一依賴不合法整筆回滾；圖形介面先顯示 I8a 影響預覽、確認同一候選後提交。
首次初始化key與配置建立為一筆交易；失敗不留下身份表、隱藏面或半份配置。
已被引用的系統／配置／頂點不得刪除，不級聯刪掉依賴。刪主格仍須通過既有依賴檢查。
來源式主格不得用普通 grid 軸、main-along 或工程綁定覆蓋；不同索引空間不得藉同id重宣告隱含互轉。
仍有工程尺寸綁定的主格必須先明確解除綁定才能改用配置，不隱含清除來源。legacy-finite 的 from-system origin 維持原義。
D29 的逐欄參數來源及 D64 整卡來源在候選內先求值，再驗本條所有限制；
配置及主格沿來源取得數值，不能另加參數覆蓋同一有效欄位。整卡來源另須符合 I74。
參數改值不改 signed 索引、vertexKey、cell 內比例或 band 身分。D10b 相位差與此處其他 D29 欄位同一順序求值，求值後才驗 I24。依賴不合法仍整筆回滾，不改綁最近格線。
~~~~

### I40

現行位置：公理層第 1561 行，組構編輯守門。公理自標 M。
拆開後要跟著改的引用：I67。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
關係規則驗成員／槽位／接合的身分唯一與完整引用、軸向映射及關係 schema；未知類型、自接、非法數值及矛盾關係拒絕。鄰接圖中的環可由幾何一致性判定，來源依賴中的環一律拒絕，兩者不可混為同一限制。能力登記只允許已定義關係，不以最相近的已知關係替代未知輸入。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

組構編輯守門：
身分、版本、槽位與接合引用完整且型別相容；禁止重複身分、失效引用及同一接合範圍內矛盾的配置。
定義引用或求值依賴不得循環；構件形成封閉框架所產生的幾何鄰接環不據此判為非法。
未知接合型別須拒絕，不降級為平接；面選擇不唯一時不得假造已完成的實例結果。
移除仍被發布規則或綁定使用的來源，須先在同一明確交易內完成合法改綁或解除，否則拒絕。
修改、刪除、版本切換與匯入均以候選世界驗證，失敗保留原世界。
本條不取消 D15、D17、I19、R6 或既有範圍、碰撞、擋面及引用規則。
~~~~

### I42

現行位置：公理層第 1585 行，組構實例守門與保存。公理自標 M。
拆開後要跟著改的引用：I69。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
生成實例保存來源規則固定版本、綁定及輸入選擇，且對生成物建立明確 owner 關係。候選內先生成全組、再驗各物件、所有相互約束及外部依賴，全部成功後一次提交；一般入口不能獨改或刪除 owned 子物件。重生成仍須保護穩定身分、外部引用與全部來源；具體成員數量、角色與支撐義務由以下配方契約提供。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

組構實例守門與保存：
配置恰覆蓋固定規則member，來源完整有型別，逐件核對joint端點／側面／方向。
主支自身支撐與副支兩端支撐均通過I19/R6；owned角材不接受獨立覆寫或刪除。
來源改動、建立、更新、刪除均整筆候選重驗；失敗、取消及過期回覆保留原世界。
完整專案保存實例、owned mapping與来源閉包並宣告獨立生成能力；重開重算核對。
舊能力不足明確拒絕，不能展平為普通角材冒充保留組構来源。
重複開間的「恰覆蓋固定規則member」指：每支主支出現同時對應規則的兩個同槽位 primary member，每個生成格子對應 secondary member；其餘依 I69。
~~~~

### I46

現行位置：公理層第 1605 行，尺寸、方位與座標。公理自標 M。
拆開後要跟著改的引用：I58。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
斷面矩形的有效兩尺寸必須正、方向映射必須在型別宣告的有限集合內，且所有座標、尺寸與推導端點符合 D1；不夾值、不交換尺寸身分。任何額外固定規格、嚴格上限或特定來源白名單由成員種類的 schema 驗證，核心包含／重疊判式不內建材料常數。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

尺寸、方位與座標：角材 A、B 求值後為正整數 mm。面材寬 w 為整數 mm，1 ≤ w < w_max（矽酸鈣板 1 ≤ w ≤ 914）；
    下限是矩形邊長為正的定義推論；w ≥ w_max 拒絕（V_PANEL_WIDTH），不截斷。面材厚度只能取自規格，不得逐構件改填。
    方位只能是該種類的兩值之一，其他角度拒絕。u0、v0 為整數 mm，可為負；u0+寬、v0+高 亦須在 D1 範圍內。
    小數、分數或超界輸入一律拒絕，不取整、不夾到範圍內。
~~~~

### I49

現行位置：公理層第 1621 行，交易與依賴。公理自標 M。
拆開後要跟著改的引用：D62、R40。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
輪廓、矩形成員、拉伸長度及定位來源組成 typed 依賴鏈；改來源須重算完整下游並整筆驗證。改輪廓只按新輪廓重驗成員原局部座標，不能自動搬移、裁短、刪除或把越界部分吞掉。活引用隨宿主重算，一次取值來源不跟隨；兩者的失效與刪除策略保持各自契約。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

交易與依賴：建立、修改、刪除斷面、構件、拉伸件或定位，都走 I8 候選交易，重驗 I43–I48 的完整依賴閉包，
    全過才提交，否則整筆回滾。
    修改斷面輪廓時構件座標不跟著動：候選世界以原 (u0, v0) 對新輪廓重驗 I44、I45；出界或重疊的構件在影響預覽中標成衝突，
    列出構件、原矩形、超出或重疊的範圍與條號；有任何衝突即不得提交，World 不變。
    不自動搬移、裁切、刪除構件，也不替構件保持貼邊；使用者改構件座標、改輪廓，或在同一筆交易中一併修改。
    輪廓改了而構件仍合法時照常提交，預覽列出原本貼邊、現在不再貼邊的構件，作為提醒，不是違規。
    會改變世界位置的操作（承載面宿主、L 或截面的具名來源）比照 I8a 先預覽：逐項列出受影響的構件與拉伸件、
    新舊剖面矩形、新舊世界範圍，以及每項違規的條號與預期值/實際值。
    刪除仍被構件或拉伸件引用的斷面，或仍被簡易定位以承載面引用的承載面 → 拒絕，除非同一顯式交易一併處理依賴者；
    不自動轉為進階。空間牆取值的定位不引用空間，空間的修改或刪除不觸發本條。
~~~~

### I50

現行位置：公理層第 1637 行，隔離。公理自標 M。
拆開後要跟著改的引用：R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
幾何型別共用不代表物件契約合併；碰撞比較、接觸來源、方向角色、集合歸屬和材料量計算都須由登記契約指明參與域。未登記的跨系統配對不新增合法性約束，亦不能輸出「已通過」；輪廓與參考包絡不得冒充正式實體。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

隔離：斷面構件不進入 D11 擋面、I11 同面碰撞、I18–I22 角色規則，也不被 D7 角材的錨法引用。
    拉伸件之間、拉伸件與空間、柱樑、面內角材之間不做碰撞檢查（與 I30 不擴大既有碰撞檢查域同一態度）；
    畫面不得宣稱已檢查。
~~~~

### I52

現行位置：公理層第 1648 行，完成面與試排完整性。公理自標 M。
拆開後要跟著改的引用：D26、D42、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
週期裁片的尺寸來源、軸向映射、起算點、間隙及宿主均須存在且可精確求值；作幾何厚度的有效值須為正整數毫米。來源型錄本身允許的數值不必然在此使用處合法。間隙可為零；列舉與裁切保留所有分量，超容量或精度不支援時拒絕，不近似、不丟片。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

完成面與試排完整性：完成面所引邊界須滿足 D3／I2，框架須滿足 D1／D2（I1）；引用存在、型別正確、依賴無環。
    試排所引 panel 版本的 width／length 為正整數 mm；thickness 須已明設，且其十進位值為正整數 mm。
    未設、零、非整數（含 9.5、12.5）→ 建立或保留該試排的交易拒絕，不取整、不以名稱推測；材料版本本身仍合法保留。
    此要求不因障礙集合為空而放寬。縫寬求值後為非負整數 mm；相位差求值後須非零，且不是被錯開軸 T_X 的整數倍（含負倍數），
    否則拒絕並說明奇偶列會重合（同 D10b／I24 的值域）。零縫寬保持 D10a 原有合法性，不暗增最小施工縫。
    所有被查詢或輸出的座標符合 D1。容量不足時依 I33 明確拒絕完整求值，不以部分板片或截短縫線冒充完整鋪排。
~~~~

### I53

現行位置：公理層第 1660 行，分層與障礙。公理自標 M。
拆開後要跟著改的引用：D7、R41、R45。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對有向區域 F、框架 (o,U,V,N) 與明選的法向層區間 [a,b]（a<b），層體為 {o+uU+vV+wN | (u,v)∈F,w∈[a,b]}。與障礙的內部有正體積交集才投影扣除；僅在端點層面接觸不扣。不同層各自求交，不能共用一次總厚度裁切而擴大扣除。偏移框架的原點為 o+aN；各尺寸與法向對應須明選，不從物件名稱推斷。具體分幾層、厚度來源與相鄰物件尺寸相等條件由模板組合契約決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

分層與障礙：面材層由完成面沿 n 至板背（厚 t），貼板角材層由板背再沿 n 延伸 h（衍生承載面的 h）。
    兩層分別與 D41 障礙集合的每一件判定：該層實體與障礙 AABB 的交集有正體積才算遇障礙，遇者在該層作邊界。
    交集只有面、邊或點是接觸，不算遇障礙，該層照常通過；包括板背恰等樑底、角材層頂恰等樑底、障礙側面與完成面輪廓邊共面等情形。
    與 I11、I15、I45、R36、D23 的「接觸不算相交」同一政策；不得以未說明的 epsilon 改成另一種接觸政策。
    不因另一層遇障礙就兩層一起裁掉，也不提供逐件手動豁免。
    衍生承載面只容許一種 h：其上每支角材的 B 有效值必須等於 h，B 向必須朝該面 +N；不符 → 拒絕（V_DERIVED_TIMBER，指名角材、B 值與 h）。
    h 或 B 來源的變更使任一支不相等時整筆拒絕，除非同一交易一併修改。
~~~~

### I55

現行位置：公理層第 1676 行，引用與交易。公理自標 M。
拆開後要跟著改的引用：R44。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
週期、宿主、障礙與比較參數均是來源圖中的節點；任一變更對整個下游重算並形成同一候選。只改比較參數仍須重新比較和顯示受影響結果，不得假造幾何移動；來源刪除不得暗換成最後值快照。確認、取消、過期及失敗回滾依 I8／I8a，不能僅保存新來源並凍結舊衍生物。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

引用與交易：完成面（邊界、框架、s、障礙集合）、D13／D14 障礙本身、材料版本選用、試排、門檻、衍生承載面 h 來源的任一變更，
    均在候選 World 重新求值完整下游依賴（衍生承載面、鋪排來源主格、guide、角材、承接結果）。
    凡移動已被角材引用的線、邊（含衍生邊）或世界框架者，先走 I8a 預覽；零違規並明確確認後才一次提交。
    門檻變更只改比對結果而不改幾何時，不偽造角材移動；仍更新依賴的比對狀態。
    已提交 World 中不存在缺失或型別不符的引用；會造成此狀態的操作整筆拒絕。
    未知或已失效的候選不能提交；取消、拒絕或失敗保留原 World、正式 metadata 與 history。
    刪除被引用的來源（邊界、柱、樑、材料版本、參數欄位、試排、衍生承載面）不得暗換成快照；須在同一交易明確解除依賴，否則整筆拒絕。
~~~~

### I57

現行位置：公理層第 1698 行，單一計算與共存。公理自標 M。
拆開後要跟著改的引用：D43、R44。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
有限週期線、無限週期線與有限域裁片使用同一套精確節距、間隙中心和 signed 奇偶函式；差別只在輸入來源、索引約定、列舉範圍及裁切區域。若兩個使用契約的索引原點不同，轉換必須以明確整數偏移表示並驗互逆。抽出共用機制不自動將既有物件升級、換型或另建來源。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

單一計算與共存：鋪排與既有 PANEL_LAYOUT／D29 REPEAT_PANEL／D10b 共用同一組精確週期、縫中心公式及最低位元奇偶函式，
    不得各自維護近似公式；有限主格、無限排法與完成面裁切只是不同的列舉／裁切範圍。
    唯一差異是 band 編號：鋪排以板列索引 p 編號，等於 D29 cell 索引加 1（D43）；兩者轉換須明寫，不得混用。
    不自動將舊網格、手動 apply-proj、斷面構件或一般角材升級為 FinishSurface 或衍生承載面。
~~~~

### I60

現行位置：公理層第 1742 行，方案守恆，對每一支被使用的料逐支成立。公理自標 M。
拆開後要跟著改的引用：R49。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
一維配置的每個容器有明確可用區間，每個需求實例以具型別身分恰出現一次。其分配區間必須位於容器內，正長度區間不得重疊；輸入全長須等於所有有效需求、明列消耗區間及末餘區間長度之和。核心以精確整數區間與加法驗守恆，不把任何損耗常數默設為零，也不由結果逆改需求長度。各消耗種類、切序解讀及可用容器由加工契約定義。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

方案守恆，對每一支被使用的料逐支成立：
    長度 = h + Σ C_i + (n − 1)·k + 末端耗損 + 剩料，各項都是非負整數。
    每件區間 [x_i, x_i + C_i] ⊆ [h, 長度 − t]；相鄰件的間距恰為 k；件與件不重疊。
    末端耗損、剩料與可用長度依 D50。
    下刀次數 = [h > 0] + (n − 1) + 末端下刀：恰到修整線時末端下刀為 [t > 0]，有末刀時為 1。
    每一需求件在方案中恰出現一次。未被使用的宣告餘料不切，也不計耗損。
    任何一支不成立都是執行器錯誤，不得顯示為完成，也不得匯出。
~~~~

### I64

現行位置：公理層第 1785 行，首房起步交易。公理自標 H。
拆開後要跟著改的引用：D53、I65、R52。

**核心條文草案**

尚無附件時，可以有一筆交易建立第一個附件。交易失敗不留半套。

**木工模板條文草案**

木工與建築模板的第一個附件是房間，宿主是一個空間邊界面。房間這個種類由模板登記。

### I65

現行位置：公理層第 1794 行，房間候選草稿守門。公理自標 H。
拆開後要跟著改的引用：R52。

**核心條文草案**

草稿有份數上限、列數上限，幾何不合法就整筆拒絕。

**木工模板條文草案**

這個模板的草稿列是房間外環。頂點必須正交且是整數毫米，幾何檢查呼叫核心。

### I73

現行位置：公理層第 1895 行，空間模型納入拉伸件守門。公理自標 H。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**

模型要納入哪些拉伸件必須明選。選了以後按來源快照求值，不跟著活世界改。

**木工模板條文草案**

木工模板規定角材與面材拉伸件怎麼被選進空間模型。核心不預設要納入角材。

### R2

現行位置：公理層第 1917 行，移動參考線要重放引用它的角材（2026-09-18 拍板反轉，取代原先的凍結語意）。公理自標 M。
拆開後要跟著改的引用：D63。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
活引用節點的上游變更時，依來源圖重求位置、方向與形狀及全部遞移下游；不能只更新同一宿主或只更新可見物件。若下游以另一物件的衍生面為來源，該面亦屬依賴鏈。按照 I8a 形成完整影響預覽，確認同一候選後依 I8 一次提交；原本明定為快照的來源仍按自己的契約處理。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

移動參考線**要**重放引用它的角材（2026-09-18 拍板反轉，取代原先的凍結語意）：
   中線與長度重新推導（R6(e)），先走 I8a 影響預覽，零違規且使用者確認才提交，
   失敗整筆回滾。理由：錨點存的是引用不是座標（D7、I13），引用的語意就是跟著動。
   修改共同 datum 或其規格來源，所有面的衍生線及其角材依賴一起重算，不凍結單一面。
~~~~

### R4

現行位置：公理層第 1929 行，場景檔是 SSOT；互動指令列 = 對同一 parser 的逐行追加。。公理自標 H。
拆開後要跟著改的引用：D4。

**核心條文草案**

場景檔是單一事實來源。互動指令列是對同一個 parser 逐行追加。宿主不另造第二套 parser。

**木工模板條文草案**

木工模板登記自己的指令：角材、組構、鋪排、承接和其他木工命令。核心 parser 只接收已登記的指令，不內建這些名字。

### R6

現行位置：公理層第 1958 行，auto 跨距推導（🔒 四項已拍板）。公理自標 M。
拆開後要跟著改的引用：D6、D7、D10a、D34、D36、D45、D49、D63、I12、I13、I19、I22、I23、I24、I25、I40、I42、I69、R2、R4、R21、R31、R32、R40、R41、R45、R55。

**現行核心契約，原樣分開**

~~~~
連續跨距求值的輸入為有效閉區域 F、有方向且寬度已定的直帶、明確參與碰撞的佔用區域集合，以及具來源鍵的接觸候選與篩選策略。將 F 的外環／孔頂點與佔用邊界投影到長軸得到有序切點；逐相鄰 cell 驗完整帶截面包含於 F 且與參與碰撞者無正面積重疊，合併相鄰合法 cell 得到全部合法連續區間。之後按錨點來源篩重疊、按父局部域驗帶寬及長向包含，再按明選 through 或 between 選段；between 必先枚舉實際接觸配對，驗其區間包含於原合法區間且完整落在父域，才判配對唯一性，不能先丟掉超出父域的原長區間。不得把合法區間硬裁至查詢／父域邊界並假造接觸面。端部的幾何完整寬度、來源資格與優先規則分開驗；是否要求每端有唯一候選由固定型別策略指定。輸出區間、完整接觸來源及逐項診斷，後續來源變更重新求值而不凍結端點。
~~~~

**現行木工模板契約，原樣分開**

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

auto 跨距推導（🔒 四項已拍板）：
   (a) 切點 = 輪廓頂點 + 孔頂點 + 已放角材 footprint 邊界，全投影到長度軸；
   (b) 逐 cell 檢查整支 footprint ⊆ 有效區域且不撞已放角材，相鄰合法 cell 合併；
       直接 at-line 引用 D19 子線時，先驗角材整個寬度帶在 C 的橫向範圍內。未使用 between 時，於選段前保留完整包含於 C 長向範圍的 R6(b) 合法跨距；through 只能選這些區間。
       使用 between 時，依 R21 枚舉實際擋面配對，驗跨距包含於原有 R6(b) 合法區間，並在配對唯一性判定前排除未完整包含於 C 的配對；不能僅因原 R6(b) 區間超出 C 就排除一組完整在 C 內的合法配對。
       不把跨距硬裁到 C 邊界，也不把 C 邊界當作擋面；兩端依 (d) 與 I19 檢查，between 保留 R21(b) 的指名擋面唯一性例外。無合法局部跨距則拒絕；最終 footprint 再驗包含於 C∩F。原 at-face 的重疊篩選語意不變。
   (c) at-face 先濾「必須與引用邊範圍重疊」；區間選擇器二選一——
       `through` 座標選段、`between` 明寫兩端選段（R21）；
       多段無選擇器 → 拒絕並列舉全部候選（不猜）；零段 → 拒絕；
   (d) 兩端各需「恰好一個涵蓋全寬的擋面」:0 個 = 懸空拒絕（E_UNSUPPORTED_END 類），
       多個 = 歧義拒絕，擋面是 FREE 邊 = 拒絕；
   (e) 推導出的中線與長度**不凍結**（2026-09-18 拍板反轉）：存的是位置引用（I13），
       被引用的線或邊移動 → 重新推導中線與長度，先走 I8a 影響預覽，
       零違規且使用者確認才提交；仍失敗整筆回滾（I8 同軌）。
       依賴鏈取遞移閉包——A 的側面是 B 的擋面，A 動則 B 一併重算。
       world_revalidate 仍重驗 footprint 合法 + 兩端各有恰好一個涵蓋全寬的擋面。
~~~~

### R7

現行位置：公理層第 1980 行，面上投影分類 = 單一「足跡 × 輪廓接觸關係」函式。公理自標 M。
拆開後要跟著改的引用：R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
精確分類矩形足跡與正交區域輪廓的接觸關係：完全在內、接一邊、接兩鄰邊、貫穿或接兩對邊，分別回傳幾何分類及相交來源；角點相切造成的退化不猜。分類輸出不自行更改物件，也不自行賦予新邊屬性；下游操作對各分類採何種作用與屬性來源由模板契約指定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

面上投影分類 = 單一「足跡 × 輪廓接觸關係」函式：
   足跡完全在內 = hole；貼一邊 = notch；貼兩鄰邊 = corner；
   貫穿/貼對邊 = strip（樑條帶）/split（柱拆片）；角點相切 = 退化拒絕，不猜。
   套用產生的新邊 fixity 一律 FIXED。
~~~~

### R8

現行位置：公理層第 1990 行，套用（apply-proj）是快照式衍生。公理自標 M。
拆開後要跟著改的引用：D60、I5、R11、R28。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
一次快照式幾何操作以觸發時解析出的全部輸入及候選基準求值，產生新的定義後不再保留原障礙的活引用。整個拆分、引用重新歸屬及集合成員調整在同一 I8 候選內驗證與提交；身份保留及新 id 配發策略須明列，不能用幾何運算的遍歷順序決定。快照操作不能冒充活布林依賴，重新套用也須是另一筆明選操作。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

套用（apply-proj）是快照式衍生：觸發當下以推導值生成孔/凹口/拆片/新面，
   之後與柱樑無連結；重套用 = 手動復原後對新鬼影再套用。
   整筆是單一交易（含空間成員重宣告）；拆分時原 id 給面積最大片（🔒)。
~~~~

### R9

現行位置：公理層第 1999 行，只有已放置面可接收投影（R3 不猜）；平面/立面由承載面法向決定。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
世界投影只能對具有已解析 D2 框架的目標求值；缺少世界位置時拒絕，不從畫布或名稱推估。投影方向及平／立面的幾何判斷依框架法向：±Z 為水平、水平法向為垂直。分類 metadata 只驗是否與框架契約相容，不能反過來建立框架。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

只有已放置面可接收投影（R3 不猜）；平面/立面由承載面法向決定
   （±Z = 平面，水平 = 立面）,boundary 的 kind 只當驗證用。
~~~~

### R13

現行位置：公理層第 2018 行，拆分時承載面輔助資料跟著含錨點的那片走（與 R10 同一條「資料跟材料走」）。公理自標 M。
拆開後要跟著改的引用：D4、D60。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
區域拆分後，逐個依賴型別以其明定的歸屬判式在每個候選分量求值：恰一片合法則歸該片，多片合法依既定保留策略，全部不合法則整筆拒絕。各物件保持同一 typed id，不複製成多份或靜默丟棄。父子集合需要共同歸屬時先整組求值，再一次選片；引用來源、固定索引與具體起算點不因分片重設。是否採可見線段、生成範圍或求值錨點，不能用同一通用捷徑代替型別契約。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

拆分時承載面輔助資料跟著含錨點的那片走（與 R10 同一條
    「資料跟材料走」):參考線以各候選片上的非空可見線段判定，不能以 I7
    「面外亦可存在」代替歸屬判定；網格仍依 I10 / I23 的生成範圍判定，角材以
    **錨點求值後的 uv** 判定(D7 已不存凍結 uv，這裡指當下由 I13 的引用
    求出來的 uv，不是欄位裡存著的座標)——只在保留片合法留原片、只在新片合法改掛
    新片、兩片都合法留原片、兩片都不含（錨點落在被移除的
    條帶區）= 無法依本規則選出承載面 → 整筆拒絕回滾，不靜默丟資料。
    原本已不可見的 guide 在兩片皆無可見段時也拒絕拆分；拒絕的是未定歸屬的拆分操作，
    不表示原 World 中的隱藏線非法。DATUM guide 改掛時保留同一 datum 引用；
    不自動複製 guide，不把一個 id 分派到多個承載面。
    面材排法的網格在拆片時來源定義與具體 anchor 不變；panel / gap 仍按 D28 求值，
    推導結果只在尾端隨新片的外接區間增減；被錨定的索引若因此消失 → I23(b) 整筆回滾。
    主格與其全部子格視為一個父子集合，先在各候選片共同求值，再依本條「只一片合法則歸該片、兩片合法留原片、皆不合法拒絕」規則選片，不複製 id、不拆散父子。合法性包含 I10/I23/I25；guide 與角材仍依本條歸屬並通過同面引用及全量重驗，任一依賴不能成立即整筆回滾。
~~~~

### R14

現行位置：公理層第 2038 行，apply-proj 逐項選片。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
同一快照交易的後續矩形操作，對原保留片及本交易已產生的同平面分量逐一做相同精確接觸分類。每項只能歸到契約允許的唯一分量；多片接觸或無片接觸均明報不能歸屬並回滾，不以最近分量或清單第一項猜選。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

apply-proj 逐項選片：同一筆交易內，每個指定項以其快照矩形
    對「原片 + 交易內拆出的同平面新片」逐一做接觸分類，
    套到唯一接觸的那片；橫跨拆分線（多片接觸）= 無法歸屬 →
    拒絕，不接觸任何片 = 拒絕。
~~~~

### R16

現行位置：公理層第 2051 行，top_drop（邊樑整段降低）= 半平面裁切。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對矩形閉區域做軸對齊半平面裁切，須先驗裁切區間跨滿所指定的垂向全幅且到達輪廓端緣；以保留側重建外環並驗非退化。輸入不是該運算支持的矩形、未到端緣或產生退化環就拒絕。求值只回傳有效幾何，是否解除原集合歸屬由模板操作契約決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

top_drop（邊樑整段降低）= 半平面裁切：矩形必跨滿垂直向
    全幅且到達輪廓端緣，保留側即新外環；否則（非矩形輪廓、
    未到端緣、退化環）→ 拒絕。降後不再滿室高 → 同 R11
    退出空間成員變游離面。
~~~~

### R17

現行位置：公理層第 2061 行，貼牆柱露出面在柱遠側緣平面。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對軸對齊長方體的指定座標軸區間 [lo,hi]，顯式側別 − 選 lo 平面、+ 選 hi 平面；以明選的法向與正交軸建立該實際坐標上的面框架。選哪個側別、是否沿用另一面法向以及哪些面要生成由呼叫契約明示，不能因兩面平行就假定它們共面或從建築名稱推選側別。模板的遠側選擇經此面求值器實現。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

貼牆柱露出面在柱遠側緣平面：拆分後生成的新立面與牆同
    法向（材料同側），但平面座標在柱遠離牆的那個棱線上
    （牆法向負側取柱 hi 緣、正側取 lo 緣），不在牆平面上。
~~~~

### R18

現行位置：公理層第 2070 行，角色衍生屬性（純幾何，不看宣告與錨法）。公理自標 M。
拆開後要跟著改的引用：D15、I21、R20、R41。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對矩形足跡與指定的區域邊集合求三項幾何結果：(1) 是否有側邊與某來源邊共線且有正長度交集；(2) 共線時實例長軸區間是否包含整個來源邊區間；(3) 相符來源邊的穩定鍵。這些結果只由幾何推出，不由宣告角色或錨法倒填。來源邊集合是否只取外環及結果對角色的約束由以下模板契約指定；輸出保持結構化欄位，不藏在展示標籤。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

角色衍生屬性（純幾何，不看宣告與錨法）：每支已放角材推出
    `onBoundary`（footprint 某一側面與外輪廓某邊共線且重疊長度 > 0）、
    `coversEdge`（onBoundary 且長度軸區間 ⊇ 該邊區間）、`boundaryEdge`（該邊索引，無則 −1）。
    只看外輪廓，不看孔邊。用 `through` 放的料貼齊邊一樣 onBoundary；用 at-face 放卻被裁短
    一樣 coversEdge=false。`boundary` 必 coversEdge=true；`primary` 的 onBoundary 可真可假（邊界主支為真）但 coversEdge 恆為假：凸角處兩端被層級 1 佔掉料寬（I11 不重疊）；凹角處 primary 不得超出它貼的外牆（I22），延伸段側面以優先級 2 計、primary 端面不得頂它（I22、I19）；
    `secondary` 必 onBoundary=false。bridge 的 objects/dump 一併輸出，不藏在標籤字串裡。
~~~~

### R20

現行位置：公理層第 2093 行，重宣告/刪除連坐。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
某個物件重宣告、移動或刪除後，除了它的顯式遞移依賴，還須重驗已登記的共享約束作用域內全部參與者，例如對同宿主的成對比較及共同方向關係。這個全域關聯不能因來源圖沒有單一有向邊而漏驗；任一失敗依 I8 整筆回滾。具體作用域與驗證器由型別／模板登記。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

重宣告/刪除連坐：刪除或移動任一角材後，world_revalidate 對同面全部角材重驗
    I19–I22 與 R18；任一不過 → 整筆拒絕回滾（I8 同軌）。
~~~~

### R21

現行位置：公理層第 2101 行，明寫跨距兩端（between）。公理自標 M。
拆開後要跟著改的引用：D18、D58、I13、I69、R6、R55。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
明選兩端來源是連續區間的選擇器，不豁免包含、碰撞、完整接觸或來源資格。先展開兩個 typed 引用各自的實際面候選，再枚舉配對，驗嚴格遞增端座標、非空區間、完整位於 R6 合法跨距及適用局部域；零組拒絕，多組仍報歧義，恰一組才選取。明選僅取代「同一坐標必須只有一個來源」的自動唯一性，不取代配對幾何合法性或模板策略。保存兩端引用，之後來源移動仍須重求並預覽。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

明寫跨距兩端（between）：auto 角材可用 `between <擋面參照> <擋面參照>`（D18）
    取代 `through`，兩者互斥（同時寫 → 拒絕）。
    它是**消解歧義的選擇器，不是放寬條件**：
    (a) 被指名的兩個擋面各自仍須滿足 R6(d) 的「涵蓋端面全寬」與「非 FREE 邊」；
        不涵蓋全寬 / 是 FREE 邊 → 拒絕，不因為明寫就放行；
    (b) 它取代的只有「恰好一個」這項唯一性要求——同一座標上有多個合法擋面時，
        改由宣告指定用哪一個，不再是「多個 = 歧義拒絕」；
    (c) 兩端固定座標必須一小一大、區間非空；跨距仍須逐 cell 通過 R6(b)
        （整支 footprint ⊆ 有效區域、不撞已放角材）——between 不能穿過實體；
    (d) 角材參照 `t<id>` 指它的兩個側面之一：枚舉全部候選配對，
        恰好一組能產生通過 (c) 的跨距 → 取它；零組 → 拒絕；
        多組 → 拒絕並列舉全部候選（不猜，與 R6(c) 同一條規矩）；
    (e) I19 的裁切優先序照常適用——between 不是豁免；
    (f) 推導出的兩端與長度一樣**不凍結**（比照 R6(e)，2026-09-18 反轉）：
        存的是擋面參照，被參照的面移動 → 重新推導，並走 I8a 影響預覽。
~~~~

### R22

現行位置：公理層第 2123 行，相位差求值。公理自標 M。
拆開後要跟著改的引用：R32。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
相位差沿用 D10b 的單一 signed 奇偶與精確位移函式；查詢依與有限範圍相交的另一軸 band 分段，每段標本軸索引、band 與完整來源。相位差 token 在候選先求值，再按 I24 驗非零／非整倍數及引用必要欄位；沒有相位差的既有輸入不新增 band。抽樣只能減少展示段，不能重編正式索引或替代精確命中／合法性驗證。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

相位差求值：未錯開座標 c(k) 沿用 D29。已設相位差時，band 最低位元為 1 的段座標為 c(k)+δ，最低位元為 0 的段座標為 c(k)。另一軸的 band 邊界用該軸未加相位差的格線，即使該軸自己也有相位差（只會出現在 D10b 相容例外的舊系統）。
    配置的錨點仍是 D30：選中 cell 的錯開角，加上 cell 內比例，對齊邊界頂點。無配置的系統或編輯預覽以該軸 phase 為原點、索引原點為 0，不減去選中 cell 的 shift，因此 band 0 停在輸入的相位，奇數 band 才加 δ。
    shift 全為 0 的求值必須與未設相位差的既有式相同，不得因本條改動舊場景的座標。中間算術溢位，或最終座標不在 D1，則拒絕，不暗取整。
    DSL：無限軸本體之後可接 stagger TOKEN。TOKEN 為整數或 param:<卡片id>:<欄位id>。dump 只在已設相位差時輸出，並保留來源 token。配置 DSL 不新增 stagger 欄位。
    查詢矩形內，凡段的錯開座標落在矩形內、且其 band 區間與矩形相交，就必須輸出該段；座標在矩形外的段不輸出。段數超過該線段容量時，exact 查詢回報容量不足，不得丟段。sample 若抽稀 band 或索引，必須明示 stride 與不完整。
~~~~

### R23

現行位置：公理層第 2135 行，子格推導。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
局部細分依父矩形求每軸整數 L/n，先驗可整除與容量，再列出具穩定索引的內線並與父矩形及宿主有效域求交。單純座標引用只取得座標值；直接引用子線的放置則保留父域限制，兩種引用不可混用。細分不自動生成正式幾何物件，不將虛擬線段或父域邊界變成接觸來源；附加角色預設由模板處理。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

子格推導：先生成主格座標，求 D19 父格四邊，再依等分數生成子線，最後裁切 C∩F；所有引用該子格的 guide／角材在這之後求值。父格 main_along 的變更不改子格角色預設或既有角材角色。
    dump／保存輸出父主格定義在前、子格定義在後，再按引用依賴輸出後續物件；子格不存展開座標或線段。讀回須恢復相同定義與推導結果；undo/redo 以完整交易為單位恢復整條依賴鏈。
    子格支援整組與逐線顯示切換。隱藏只改展示，不改幾何、引用、放材合法性或保存來源；隱藏線不留下畫布可點選的命中範圍。顯示偏好的保存範圍沿用現有面內參考線控制。
~~~~

### R26

現行位置：公理層第 2151 行，複合空間求值。公理自標 M。
拆開後要跟著改的引用：D21、R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對有效有向殼先求封閉區域 V，再按 D22 明選障礙集合求正規化差集。開口沒有顯式來源面就保持開放；若要求計算封口，必須先存在明確幾何面，並在殼的面使用中標為 calculation-cap。用途標記不自動新增面，不改變其拓撲判式，也不得把計算面回報成具材料的實體。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

複合空間求值：先驗殼、求 V，再按顯式障礙集合求淨空；未列障礙不自動扣除。
    開口存在而未另加定義面時保持開放；若需以虛擬封口計算體積，該封口必另建有來源的面，
    並在該殼面使用的 purpose 明寫 calculation-cap，不得把它輸出成 RC 牆體或擅自消除門窗。
~~~~

### R31

現行位置：公理層第 2196 行，工程來源求值。公理自標 M。
拆開後要跟著改的引用：D49。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
按以下固定順序解析來源：求精確參數值 → 核對固定版本及欄位身分 → 按登記覆寫順序解析終端來源 → 驗單位、整數及範圍 → 求目標幾何 → 重算完整依賴 → I8／I8a 候選預覽與提交。升級只能改動本次明選目標；未明寫清除的覆寫與已具體化起算點保持原來源／值，不能把版本更新當成自動重設。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

工程來源求值：有 D31 參數時先依 R33 精確求值 → 解析固定版本與套用 → 依 D28 覆寫優先序取得各欄位 →
驗型別、整數及範圍 → 依 D10a 展開格線及 D7 / R6 推導角材 → 重算完整依賴 → I8 / I8a 預覽與提交。
材料新版本要經新做法版本及明選使用位置才升級；預設保留既有覆寫與具體起算點，
任何清除覆寫或更換起算點均須在本次交易明寫並列入預覽。未升級位置保留舊來源。
~~~~

### R32

現行位置：公理層第 2207 行，網格求值與保存。公理自標 M。
拆開後要跟著改的引用：I25a。

現行條文的第二段是宿主及相容契約，不是木工模板契約。下面兩段是拆分草稿，不是把現行句子搬家。

**核心條文草案**

格線按帶符號索引精確求值。查詢用到的裁切不改變索引，也不把可重建的裁切陣列存成來源。

**木工模板條文草案**

木工模板在格線求值之後才放角材。角材的跨距和擋面仍走模板自己的跨距規則，不寫進格線核心。

### R34

現行位置：公理層第 2266 行，組構規則流程。公理自標 M。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
規則的草稿、已發布不可變版本、來源綁定及正式生成實例使用不同生命週期。先驗 typed 槽位與幾何關係才發布；綁定和修改經同一候選預覽／確認。示意位置與尺寸不得成為正式幾何來源。請求生成前分別核能力、完整輸入與關係一致性，缺能力、缺輸入及矛盾須分別診斷；不可改來源、刪成員或近似入值使請求通過。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

組構規則流程：
編輯草稿 → 驗證槽位與局部接合 → 發布規則版本 → 明選材料綁定 →
預覽變更 → 確認同一候選 → 提交與保存。
規則與綁定都可在未指定房間、網格或承載面時存在。
示意圖只呈現關係，不將示意尺寸寫入定義。
對只具 authoring 能力的執行器，不提供可誤認為已生成施工角材的成功結果。
需套用幾何時，必須先檢查求值能力及完整輸入，再依正式幾何規則執行；
缺能力、缺輸入、規則矛盾分別診斷，不藉由改角色、刪料或暗取整通過。
~~~~

### R36

現行位置：公理層第 2288 行，剖面矩形求值。公理自標 M。
拆開後要跟著改的引用：I53。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
先由具身分的尺寸與明選軸映射得矩形寬 w、高 h，再以保存的 (u₀,v₀) 得 Q=[u₀,u₀+w]×[v₀,v₀+h]。兩矩形 i,j 的正面積交集等價於 max(u₀ᵢ,u₀ⱼ)<min(u₁ᵢ,u₁ⱼ) 且 max(v₀ᵢ,v₀ⱼ)<min(v₁ᵢ,v₁ⱼ)；任一方向取等號只是接觸。完整 Q 另須包含於真實輪廓 F，不能以其 bbox 代替 F。全程整數加減與比較；種類到尺寸來源的映射由模板提供。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

剖面矩形求值：讀種類與方位得寬、高（角材 A 沿 u：寬 A、高 B；A 沿 v：寬 B、高 A；
    面材厚沿 v：寬 w、高 t；厚沿 u：寬 t、高 w）→ 取保存的 (u0, v0) → R = [u0, u0+寬] × [v0, v0+高]
    → 驗 I44（R ⊆ F）與 I45。設 u1 = u0+寬、v1 = v0+高，任兩構件 i、j 的交集面積 > 0
    ⇔ max(u0ᵢ,u0ⱼ) < min(u1ᵢ,u1ⱼ) 且 max(v0ᵢ,v0ⱼ) < min(v1ᵢ,v1ⱼ)；任一向取等號即貼齊（面積 0，合法）。
    全部是整數加減與比較，不需取整。
~~~~

### R37

現行位置：公理層第 2299 行，拉伸求值。公理自標 M。
拆開後要跟著改的引用：R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
每個矩形成員 Q 沿 [0,L] 拉伸為 Q×[0,L]；定位後由 O+uU+vV+wN 映射到世界。單個矩形體積為 w·h·L，任意正交外輪廓包絡按 R24 擠出，不能以外接矩形替代凹輪廓。包絡是參照，不計入成員體積。核心只求連續幾何，不依外部商品長度自行切段；是否另計分件、接縫或加工需求由模板能力決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

拉伸求值：每個構件產生一個長方體，局部範圍 R × [0, L]；有定位時以 O + u·U + v·V + w·N 轉為世界座標。
    斷面包絡依 R24 同法產生參考棱柱，L 形不得換成外接矩形。角材體積精確等於 A·B·L，面材等於 t·w·L。
    面材以連續板呈現，不依板長分段：L 超過板長時是多片板沿 L 相鄰排列，幾何上是同一段連續體積（D40 的定義推論）。
    斷面拉伸不求板片數量與接縫位置；完成面上的面材排板與縫位依 D42／R42（面材試排）。
~~~~

### R38

現行位置：公理層第 2309 行，簡易定位求值。公理自標 M。
拆開後要跟著改的引用：D38、R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
給定宿主正交框架 o_H,U_H,V_H,N_H，明選 d∈{±U_H,±V_H}、局部定位 (p,q) 與 up，唯一求值為 N=d、V=−up、U=V×N、O=o_H+pU_H+qV_H，再驗 I48 的正交與方向條件。框架來自活引用或已保存的一次取值來源須明確；活引用不另存可獨立變動的 O/U/V/N，取值來源不跟隨原對象。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

簡易定位求值：宿主框架 o_H、U_H、V_H、N_H 取自承載面引用的現況，或空間牆取值所保存的值；
    給定 d ∈ {±U_H, ±V_H}、(p, q)、up：N = d；V = −up；U = V × N；O = o_H + p·U_H + q·V_H。結果須通過 I48。
    這是唯一的求值路徑；承載面引用的簡易定位不另存可獨立變動的 O/U/V/N（D9）。
~~~~

### R39

現行位置：公理層第 2318 行，預覽輸出。公理自標 M。
拆開後要跟著改的引用：R59。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
預覽輸出以 typed 根物件／成員路徑識別每個已求值實體，另列參考包絡並標示不計材料量。每個成員回傳有效尺寸、軸映射及範圍；未定位者只列局部範圍，不能冒充世界位置。尺寸的顯示欄名與材料分類由型別契約提供，預覽核對清單不自動成為加工或採購數量。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

預覽輸出：沿用 D24 建模請求（role=geometry、target=solid-set）的形式；每個構件一個物件，
    身分為（拉伸件 id、構件 id），另附包絡物件，標為參考角色、不計材料量。輸出列出構件數及每支的種類、
    尺寸（角材 A×B×L、面材 t×w×L）、方位與世界範圍（未定位則為局部範圍）。這是核對清單，不是料單。
~~~~

### R41

現行位置：公理層第 2337 行，空間層次與衍生承載面。公理自標 M。
拆開後要跟著改的引用：D4、D10、D41、I13、I56、R4、R42。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
給定原框架 (O,U,V,N)、側別 s∈{−1,+1}、n=sN 與層區間 [a,b]，先把明選障礙轉成局部矩形 R_k 與沿 n 的區間 W_k。僅當 int(R_k)∩int(F) 非空且 int(W_k)∩(a,b) 非空才對該層扣除 R_k；結果 G=closure(interior(F∖⋃R_k))。層起點框架為 (O+a·n,U,sV,n)，局部映射為 (u,v)→(u,sv)，保持右手系。按內部連通保留全部分量並驗 I2，點接觸不合成一個分量，空集合合法。衍生邊從原環邊與障礙側邊的留存極大連續段建立來源鍵；同位置多來源保留全序集合，鍵中含來源、段號及總段數，解引用只接受唯一完全相等的鍵，不找最近邊。來源排序、屬性繼承與用途限制由以下既有轉接契約提供，不另建第二套幾何求值器。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

空間層次與衍生承載面：設完成面原點 O、框架 U、V、N、結構側 n=s·N、板厚 t（I52）、衍生承載面的 h（I53）。
    障礙 k 的 AABB 在完成面框架為 R_k×W_k：R_k=[u0,u1]×[v0,v1]，W_k 是沿 n 的 q 區間（q=s·w）。
    面材層取 q∈[0,t]，貼板角材層取 q∈[t,t+h]。某層遇障礙 k ⇔ int(R_k)∩int(F)≠∅，且 W_k 與該層 q 區間的開區間交集非空（I53）。
    每層的有效區域 G_層 = reg(F \ ∪{R_k | k 遇該層})；遇障礙者在該層裁切，否則該層從障礙旁或下通過。
    水平完成面等價於比較 z 區間；垂直完成面沿其 n 計算，不能偷改成只比 z。
    板背框架為 (O+t·n, U, s·V, n)，仍是右手系（U×sV=sN=n）；完成面座標 (u,v) 映射為板背座標 (u, s·v)。
    衍生承載面的有效範圍是 G_角材層 經此映射的結果。它依內部連通拆成分量（只以點相接者是不同分量）；
    每個分量須能表為一個簡單外環加互不相接、不接外環的簡單孔環（I2）；不能時為退化，候選整筆拒絕（R3），不猜、不以 bbox 填補。
    G 為空是合法結果，其上任何角材依 I5 不成立。
    衍生邊 = 各環上方向相同、fixity 相同的極大直線段；繼承自 F 邊者沿用其 fixity，障礙裁切產生者為 FIXED（同 R7）。
    衍生邊鍵：邊界上每一點的來源，是含該點的 F 邊（外環 e<i>／孔 h<i>e<j>，依 D41 所引 D3 的索引），
    或障礙投影矩形的一側（c<id>／b<id> 加 u−、u+、v−、v+，板背框架）。每個來源在 G 邊界上的留存部分，
    依走向（F 邊依其 D3 頂點序；障礙側邊依板背框架中沿該側座標遞增的方向）切成極大連續段，從 0 編號，並記其總段數。衍生邊鍵 = 沿環的正規走向
    （板背框架中外環逆時針、孔環順時針）依序列出構成該邊的（來源、段號、總段數）；
    來源全序：F 外環邊（依 i）＜F 孔邊（依 i、再依 j）＜柱 c（依 id）＜樑 b（依 id），同一障礙依側別 u−＜u+＜v−＜v+；同一位置有多個來源時依此全序排列，衍生邊鍵之間依此全序作字典序比較。
    at-face、D18 擋面、D6a(a) 及 R18 的 boundaryEdge 對衍生邊一律保存鍵；候選中恰有一條鍵完全相等的衍生邊，
    解引用才成立；零條或多條 → 拒絕並列出，不找最近邊。D6a(a) 在衍生面上只引用衍生邊（以鍵）的該軸座標；正交輪廓的頂點座標必等於與之相接、垂直於該軸的衍生邊座標，故不另定頂點引用，頂點引用即拒絕。
    多分量或多跨距逐分量、逐段保留；R6 多解仍須明示選段。衍生承載面不另存輪廓副本，也不另做一套放置／碰撞引擎；
    其上的放置、碰撞、擋面一律用既有 D7／I／R。
~~~~

### R42

現行位置：公理層第 2362 行，板片、裁切與縫位。公理自標 M。
拆開後要跟著改的引用：D42、D44、R37。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
在來源框架中以 D10a／D10b 的共享公式列舉本體矩形，與該層有效區域精確求交並保留所有片段；間隙中心的 floor(g/2) 先在來源框架取，再變換到結果框架，不能在反向軸重新取下界。接縫按 D43 的來源鍵與兩側裁片存在性分段，只有兩側皆有有效區域的子段才輸出為有效接縫。列舉索引、帶號轉換與容量限制都保持現有契約，不用顯示抽樣或任意最大片近似。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

板片、裁切與縫位：所有排板量在完成面框架求值，再依 R41 映射；奇數 g 的 ⌊g/2⌋ 在完成面框架取，
    不在板背框架另取（s=−1 時兩者會差 1 mm，以完成面框架為準）。
    每一軸用 D43 的式子；以 signed (i,j)∈Z² 列舉本體與 G_面材層 有正面積交集的板片（交丁時被錯開軸再依板列奇偶平移 δ）。
    每片扣孔及面材層障礙後，依材料內部連通拆成分片，保留完整輪廓；只在一點相接不算連通。
    每個分片以材料在左的方向追蹤邊界；閉合走訪若重訪同一頂點，依重訪頂點的 (u,v) 字典序由小到大，
    在該頂點確定性地拆成簡單環，使每個環都是簡單環。逆時針為外環、順時針為孔；每個分片恰有一個外環。
    分片依最小頂點的 (u,v) 字典序排列；分片內先外環，孔依各自最小頂點的 (u,v) 字典序排列。
    每片以（試排 id，i，j）作推導追溯鍵；分片另加確定序號（依分片最小頂點的 (u,v) 字典序）。
    分片不是新正式物件，不以面積或 bbox 合併不同分片。有效板縫段依 D43，由面材層結果求得。
    既有有限 D10a 仍只列 k≥0 且 a+(k+1)T<hi 的線，不改其 from／停止條件。
    在相同起點、同一框架與共同列舉範圍，板縫中心必與既有 PANEL_LAYOUT 及 D29 REPEAT_PANEL 逐條完全一致。
~~~~

### R43

現行位置：公理層第 2379 行，每側承接判定。公理自標 M。
拆開後要跟著改的引用：D44。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
對每條有效接縫段，收集足跡聯集及兩側實際裁片頂點的縫向座標，以全部切點分成開區間。每段分左右求從該側片邊向外、位於相鄰有效片內且被參與者足跡聯集連續覆蓋的寬度 d_L、d_R；遇空隙即止，不能合計不相連區間或用中心線到遠端外緣距離替代。合併相鄰且兩側實值 (d_L,d_R) 皆相同的區間，得到極大子段；有限個切點本身不求值、不判定，也不阻斷相鄰同值段合併。各子段兩側分別與明示精確 X 比較，保留實值、來源及不足子段，不取平均或以最小值代替整條結果；參與者型別和結果是否阻止提交由模板決定。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

每側承接判定：承接角材 = 以該試排的衍生承載面 id 為宿主的全部已放角材；依引用判定，不依幾何巧合：
    其他承載面上的角材即使恰位於同一平面也不計。尚無衍生承載面時承接集合為空。
    足跡經 (u,v_d)→(u,s·v_d) 映回完成面框架後與板片比較。
    在每條有效板縫段上逐點量：於縫向座標 y 處沿垂直縫的方向，
    分別量兩側板邊進入「足跡聯集 ∩ 該側板分片」的連續覆蓋寬度 d_L(y)、d_R(y)：自板邊起算，遇板縫空隙、孔、障礙裁切區或足跡間斷即止。
    子段 = 有效板縫段內，除有限個點外兩側實值 (d_L, d_R) 皆不變的極大開區間；這些點本身不求值、不判定，也不阻斷相鄰同值段合併（開區間計，同 D43）。不改變兩側實值的邊界因此不增加子段。
    兩側實值只可能在足跡聯集或兩側板分片之頂點的縫向座標處改變——不只足跡，也含面材層障礙裁切、孔、外輪廓及板片的邊；
    以這些座標全部切開、逐段求值，再合併相鄰且兩側實值皆相同的段，即得同一組子段。
    每個子段 d_L≥X 且 d_R≥X 才標「已承接」，否則標「承接不足」並列出該子段與兩側實值；整條縫段的判定是逐子段結果，不取平均，也不以最小值代表整段。
    X 以精確有理數比較，不四捨五入。縫線上只有一側有板的部分不是有效板縫，不判定（顯示「外緣非兩板縫」）。
    這只是幾何承接比對，不證明釘距、載重、跨距或固定強度。
~~~~

### R44

現行位置：公理層第 2396 行，來源網格重算與值快照。公理自標 M。
拆開後要跟著改的引用：D10、R4。

**核心條文草案**（現行核心契約，原樣分開）

~~~~
由週期裁片來源建立有限格網時，保存來源實例引用與固定參數映射，格線位置使用同一週期函式並以明確索引偏移轉換原編號。保留活引用的衍生物在來源修改後沿完整依賴重算，不能另存可獨立編輯的來源輪廓或尺寸副本。明示導出的值快照則依下列既有契約建立獨立普通格網來源，複製當下有效值後不再引用原試排、邊界或材料，之後仍可依普通來源契約編輯。已具體化起算點、活引用與快照各依原生命週期，不因共用數學自動互換。
~~~~

**木工模板條文草案**（現行木工模板契約，原樣分開）

~~~~
以下完整保留現行輸入、用途與驗收條件；其中可共用的求值委由上述核心完成。

來源網格重算與值快照：鋪排來源主格依 D43 在完成面框架求兩軸及交丁段座標，再映射到板背框架（u 不變，v_d=s·v）。
    依賴方向：邊界、柱樑 → 完成面；完成面、材料、參數 → 試排 → 衍生承載面 → 鋪排來源主格 → guide → 角材；拒絕反向成環。
    來源改變按原身分（軸、signed k、band）重算；引用消失或型別不合則拒絕並列出，不找最近線代替。
    會移動既有角材的修改依 I55／I8a；不可只刷新畫面而留下舊引用。
    若需可重用的對齊網格，可由試排明確導出一份 D29 值快照：新建一份普通 D29，兩軸皆為 REPEAT_PANEL，
    panel／gap／anchor 取導出當下的整數有效值（P_X、g、a_X）。交丁時，被錯開軸改存 anchor=a_X+δ、相位差 −δ，
    使 D29 的 cell 奇偶（I57）下各列縫線與試排一致；名稱預設註記來源試排，名稱不是身分。
    快照不引用試排、邊界或材料，不隨試排變更；之後完全依 D29／D30／I37 原義運作，含 D30 的錨點平移。
~~~~

### R52

現行位置：公理層第 2475 行，首房起步求值。公理自標 H。
拆開後要跟著改的引用：（沒有其他條文用條號點它）。

**核心條文草案**

第一筆起步先驗宿主圖頁、來源位元組和容量，通過才建立暫定附件。

**木工模板條文草案**

木工與建築模板用這筆交易建立第一個房間。建立的種類由模板決定。

### R59

現行位置：公理層第 2557 行，空間模型納入拉伸件求值（快照）。公理自標 H。
拆開後要跟著改的引用：R40。

**核心條文草案**

已保存的模型用它自己的來源快照求值，不讀求值當下的活世界。

**木工模板條文草案**

木工模板決定快照裡哪些角材、哪個角色、哪些拉伸件要送進去求。

## 核心條文裡的木工概念

這裡只列「本表標成核心，或核心契約段仍在立法」的地方。純木工條文裡的木工詞不重複列。

### 查過、不是木工概念

- D21 的 `boundary` 是邊界殼的用途，不是角材角色 `boundary`。
- D23、R25 的角色是布林的 base／tools，或實體與空洞，不是主支副支。
- D30、D12 的 boundary 是輪廓或畫布類別。
- D24、D25 的角色是建模請求的結構。

### 核心契約段點到角色，但句子是把決定權交給模板

這些段出現「角色」或「放置角色」，內容是「核心不讀它，由模板驗證」。這是邊界句，不是把優先級表寫進核心。拆開時保留這句即可：

D10、D19、D28、D36、I10、I37、I42、I50、R18、R23。

### D11 與 R6 各自驗什麼

上一版把這兩句讀成互相矛盾。那個讀法不成立，這裡改寫。

- D11 第 362 行驗的是每一個接觸候選：端向裁切要覆蓋完整帶寬；部分覆蓋，或兩個不同平面，都不能拼成同一個完整端面。
- R6 第 1960 行把三件事分開：端部的幾何完整寬度、來源資格、優先規則。然後才說，是否要求每端有唯一候選，由固定型別策略指定。
- 每個候選都要全寬，與允許多個合格候選，可以同時成立。候選有幾個，和一個端面能不能由兩個平面拼成，是另外兩件事。
- 分類沿用這兩條現行的 K 段與 W 段。不把「必須全寬」改成策略旗標。

I8、I8a、I25a、I34、R32、D9 的核心段本身沒有角色表。木工內容在同一條的後段。它們標成混合，就是因為這個。

### 整條都是木工，但被別的條文當成幾何優先級

D15 與 I19 在公理文首標 W，本表標木工。它們不是核心條文。它們被 D11、R6、R18、I20、I21、I22、R19 當成裁切的幾何順序來引用，所以解耦時不能把引用留在核心段。

- D15 把優先級寫死：空間邊界（外輪廓邊、孔邊、柱面）0、邊界材 1、主支 2、副支 3、自訂料另寫。柱面在這張表裡是優先級 0 的擋面。
- I19 要求端面所頂的擋面，擁有者優先級嚴格小於自己。外輪廓邊只有邊界材可以頂。孔邊和柱面沒有先鋪邊界材的義務，任何角色都可以依數值頂。例外是兩支邊界材轉角互頂，以及延伸段。

角色表留在木工、中性整數比較留在核心，兩件事可以同時成立。現行正文沒有獨立的核心段。另寫一段「核心只做整數比較」是新方案，不在本節，也不收成二選一。

### 擋面包含柱面，和現場規則的落差

公理現文：

- D11 的木工契約寫三種端面來源：外輪廓邊、孔邊、同承載面已放角材的側面。頂到是指座標相等且覆蓋全寬。
- D15、I19 另把柱面放進優先級 0。I19 允許任何角色依數值頂柱面。
- R6(d) 與 I19 一起，要求端部的擋面涵蓋全寬。

決策佇列 2026-10-22 的記錄，公理正文都還沒改。後節取代的是前節留下的懸空容許量，不是把前節整節作廢。落實段是協調者推論，不是使用者原話。

- 「柱跨牆階」使用者原話是「我能接受」。該節曾把懸空容許量留成待決。該節落實段寫條文未定案前不得實作。
- 同日較後「角材端面只能固定在角材上，懸空不另設數值上限」使用者原話是「主要是你這個角材端面只能固定在角材上 你是不是聽不懂?」。該節落實段（使用者可推翻）寫明不另設懸空容許量，並寫前一節的待定由本節取代。端面要頂到角材，RC 面先貼角材。
- 「兩種實際排法圖使用者確認可以」使用者原話是「這是可以的」。圖上是柱貼牆，以及 13 mm 薄牆階。

現場記錄與現行 I19、D15 的差還在：公理把 RC 柱面當成可以選擇的擋面，I19 讓任何角色依數值頂它；較後的落實段要求 RC 面先貼角材，端面頂到角材。這份差的條文修改稿仍待看稿。看稿前程式遵循現行公理。本草稿不代決，也不把那份修改稿當成已採納。

同一天的壁柱偏好已經拍板，使用者原話是「用這個」，選原縫併料。落實段寫 oracle 與核心的行為不必改。一軸相位差的兩題也已經拍板，使用者原話是「題3 放行」「題4 不算」。混合邊界還沒寫進 I24 與 D29，所以本表不把 D10b、I24、R22 改判。那份條文差另案看稿。該節落實段裡、條文未定案前可以照該判定實作的那句，是協調者推論，本稿不把它當成授權。

## 分類和程式落點對不上的地方

預定的 `geometry-core/kernel/`、`geometry-templates/woodworking/`、`geometry-app/` 在這份 main 上還沒有。現在的實作仍是一支 `current_geometry.c`，加上 `geometry-core` 裡的 include、`geometry-web`，以及 `geometry-core/framing-template/` 的木工參考。

因此最主要的不一致不是某一條標錯，而是：本表標木工或混合的條文，有 64 條的條號仍出現在未拆的 C 單體裡。模板還不能單獨拿掉。

其次，公理自標 H、本表標核心的那些條，程式多半落在 `geometry-web` 或身分、參數、卡片的 include。這和「它不是木工」一致，和「它應該住進幾何核心」不一致。本表的核心包含宿主機制，不表示這些檔要搬進 K。

正交實體 D20–D25、I26–I33、R24–R30，文首寫明尚未實作於現行 C 核心或物件畫布。表上若有落點，是建模套件或測試點到條號，不是畫布已經會做。

面材鋪滿、裁切計畫、身分帳這幾組，文首也寫明條文採納不等於功能完成。表上的「產品碼無條號」或只有偏 W／偏 H 的點名，要連這句一起讀。

## 最不確定的地方

- 把沒有木工政策的 H 收進「核心」，核心的數量會比 GEO-261 的 K 大。若核心只准指幾何演算法，這 31 條左右要改標，但使用者要的三種分類裡沒有第四種。
- D11 與 R6 都標混合，因為兩條都有 K 段和 W 段。不再把「完整帶寬」和「候選是否唯一」讀成互相矛盾，也不建議刪掉現行的全寬句子。
- D19a、R28、R33、R40 公理標 M，本表標核心。若認為宿主段只要還在同一條就算混合，這四條要改回去。
- I36、I41、I56、I62、R12、R46、R50 公理標 H，本表標木工。它們是保存與前綴，不是放置算法。標木工是因為拿掉木工模板它們就沒有對象。
- 房間（D52、D53、I64、I65、R52）算木工模板還是另一個建築模板，正文沒有分開。本表把它們放在混合的模板段。
- 條號搜尋是弱代理。I1 這類每條路徑都在用、但註解沒寫條號的，會顯示產品碼無條號。不能把這一欄讀成沒有實作。
- 2026-10-22 的壁柱、相位差兩題、端面規則，決定已經寫在決策佇列。本表承接，不再問哪一節有效。新條文還沒寫進公理，那是看稿，不是把舊決定重新打開。

## 已記錄、不再列入待決

公理分類仍對 `origin/main` `f6a15891` 的公理層。決策佇列另讀了較新的 `origin/main` `20329738`：那次只多了「#288 最終驗收改在雲端 Codex 環境試行」，與條文分類無關。落實段是協調者推論，不是使用者原話。

1. 單一文件。公理層第 65 行寫本檔仍為單一驗收基準，條號與既有功能契約不分叉。決策佇列「2026-10-12～15 使用者後續拍板」的使用者原話見本文開頭。木工內容留在這一份公理裡，並且要拆得開、第一個被套用。這不是待決。
2. 壁柱。決策佇列「2026-10-22 壁柱：兩案都合格時，原縫併料優先」。使用者原話是「用這個」。選的是原縫併料。落實段寫 oracle 與核心的行為不必改。
3. 一軸相位差。決策佇列「2026-10-22 #314 一軸相位差的兩題邊界：混合操作放行、刪後重建不延續例外」。使用者原話是「題3 放行」「題4 不算」。分類不改判 D10b、I24、R22。混合邊界還沒寫進條文，那份差另案看稿。
4. 壁邊材端頭。程序已定：先看逐條修改稿，寫進公理之後才實作；之前遵循現行公理。不再問合成前程式維持哪一套。
   - 「柱跨牆階」使用者原話是「我能接受」。該節曾把懸空容許量留成待決。
   - 「角材端面只能固定在角材上，懸空不另設數值上限」使用者原話是「主要是你這個角材端面只能固定在角材上 你是不是聽不懂?」。落實段（使用者可推翻）寫不另設懸空容許量，並寫前一節的待定由本節取代。不再問兩節哪一節有效。
   - 「兩種實際排法圖使用者確認可以」使用者原話是「這是可以的」。
5. 上面第 4 點的新條文本身仍待看稿。這不把已經記錄的選擇重新打開。
6. #288 這一輪驗收改在雲端 Codex 試行。使用者原話是「如果可以的話我想要試試看  請codex他 在雲端環境跑  不然這台電腦 我想要做其他事情都被這個卡住 很煩」。這不是條文分類的決定，不列入待決。

## 要使用者拍板的點

1. 三種分類要不要改成四種，把沒有木工政策的宿主從「核心」裡分出去。現在的三種是分析視角，不取代公理文首的 K／W／H／M。

## 新方案（需完整逐條差異，待使用者看稿）

下面只列方案名稱、動機和影響範圍。都還沒有逐條差異，也沒有被採納。分類表和各條的現行契約不含這些方案。

### 拆條號

動機：混合條文若要在文件上分成兩條，會想讓核心段留原條號、木工段加後綴。
影響範圍：104 條混合，以及引用它們的條文。公理層第 65 行現在是條號與既有功能契約不分叉。這個方案會離開那句，所以不放進分類表。

### 端面策略旗標

動機：上一版把 D11 的完整帶寬和 R6 的候選唯一性讀成互相矛盾，並想把必須全寬、不准兩個平面拼接改成模板旗標。該讀法不成立，見上面「D11 與 R6 各自驗什麼」。
影響範圍：D11 的核心契約、R6 的核心契約，以及 R6(d) 的全寬擋面。若仍要把部分寬度或多平面放進策略，需要另寫完整的改前改後。本稿沿用現行句子。

### 身分帳涵蓋擴張

動機：上一版分類稿把組構放進 D59 的受涵蓋種類。現行沒有。反例是 D34：組構實例所有的角材，現行排除。
影響範圍：D59 的七類清單、D34 的排除、R57 的未知延續、分層契約裡 H 對特定型別涵蓋域的責任，以及保存與追溯。要擴張就另交改前改後。本版分類改回現行七類。

### D15／I19 另寫中性整數比較

動機：這兩條整條是木工，沒有現成的核心段。若要讓核心只做呼叫端給的整數比較，必須新寫文字，不是把現文拆開。
影響範圍：D15、I19，以及把它們當裁切順序引用的 D11、R6、R18、I20、I21、I22、R19。本稿不把這件事收成二選一。

## 核對

腳本 `geometry-core/domain-decoupling/check_axiom_layering.py.txt` 用和 `geometry-guide/axiom_matrix.py` 相同的條號正則，檢查上表每一個條號恰好出現一次，並檢查每一條混合都有拆分小節。條號恰好一次不能證明反向引用清單完整。同一支腳本另掃公理正文裡的條號，含中文緊鄰與斜線連寫（例如 `依D7/R6`），核對每個混合條的「拆開後要跟著改的引用」。破折號範圍不展開成中間條號。輸出如下：

~~~~
axiom 207
table 207
核心 66
木工 37
混合 104
OK each clause id appears once
OK reverse cites
~~~~
