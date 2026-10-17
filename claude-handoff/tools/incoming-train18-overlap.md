# GEO-261／train 18：唯讀整合重疊預測（2026-10-17）

> **這是共同祖先 `27f5c09bdd35b0ef9db2c6c636c8a63e47625de0` → train `e8eb1da51f3b21df15869338a7e36e76e584ff9e`，以及同祖先 → GEO-261 `d4b22beb4bbf5b7938ad0a5349220e95b5d9b08b` 的精確快照。不是列車核准、將進入 main、整合成功或測試通過的聲明。**
>
> 主工作者告知 main 仍為下列 `27f5c09b…`。本次沒有 fetch、merge、建立合併狀態、修改分支或執行測試；不得以此文件作為合併外部 branch 的授權。只在實際 upstream 落地後，由主工作者重新核對 main 與來源增量。

## 快照與方法

| 角色 | 完整 SHA | 讀取位置 |
|---|---|---|
| 釘選 main／共同祖先 | `27f5c09bdd35b0ef9db2c6c636c8a63e47625de0` | 兩端共同祖先 |
| GEO-261 integration | `d4b22beb4bbf5b7938ad0a5349220e95b5d9b08b` | `D:/geometry-axiom-work/geo261-integration` |
| 尚未合入的 train 18 | `e8eb1da51f3b21df15869338a7e36e76e584ff9e` | `D:/geometry-axiom-work/board-local-codex/work/train18-p157` |

兩端 HEAD 均已以唯讀 Git 指令核實，檢查當時 `git status --short` 均無輸出。兩端 `merge-base` 恰為上列 main SHA，因此本文件比較的是各自相對該祖先的增量，沒有把已在共同祖先內的變更算成 incoming。

依 `git diff --name-only -z`：GEO-261 有 1,473 個變更路徑，train 有 1,728 個，多數為證據；兩端精確路徑交集為 **23 個**。這是路徑重疊預測，不是實際 Git conflict 清單。沒有執行 merge 或 merge-tree 模擬。

只讀取 Git 歷史、blob 與差異；`current_geometry.c` 透過 Python 讀取 Git blob bytes，沒有用文字工具改寫。GEO-261 該 blob 的 10,390 個行尾均為 CRLF。本次未執行 C 編譯、WSL、瀏覽器或測試，未修改任何 repository、`.codex` 或 `codex/*` 分支。此備忘錄是唯一新增檔案。

## 23 個精確重疊路徑

```text
current_geometry.c
geometry-core/assembly.inc
geometry-core/engineering_commands.inc
geometry-core/grid_bindings.inc
geometry-core/grid_systems.inc
geometry-core/parameter_types.h
geometry-core/parameters.inc
geometry-core/section_profiles.inc
geometry-core/subgrid_commands.inc
geometry-guide/公理層-閱讀器.html
geometry-web/assembly-workspace.js
geometry-web/assembly_bridge.inc
geometry-web/cdp_test.js
geometry-web/engineering-workspace.js
geometry-web/engineering_bridge.inc
geometry-web/panel_fill_bridge.inc
geometry-web/section-profile-workspace.js
geometry-web/section_profile_bridge.inc
geometry-web/web_bridge.c
tests/mutate.py
tests/run_all.expected.json
tests/run_all.py
tests/test_core_integrity.c
```

## 路徑／風險矩陣

下列風險是來源差異推論，尚未由合成來源編譯或執行驗證。

| 範圍 | Incoming 增量與 GEO-261 接縫 | eventual 整合時須保留的行為 |
|---|---|---|
| `current_geometry.c`、`geometry-web/web_bridge.c` | Incoming 改 R7 精確接觸分類、退化拒絕、R8 第三殘片及 R12／R14 不裁條帶歸屬，並新增 `OBSTACLE_DEGENERATE` 與 bridge 拒絕。GEO-261 的 `classify_rect_outline`、`proj_split_loop` 函式仍與共同祖先相同；周邊已改為核心 boundary／placement store 與 `wood` 柱樑領域。 | 搬入演算法與錯誤診斷時，保留 `app_boundary_read/stage`、逐片 staging 與 rollback；不得還原舊的 `World.boundaries/placements` 直接陣列寫入。`apply_boundary_line` 的 incoming 診斷也須保留 GEO-261 的 `app_boundary_replace`。 |
| `geometry-core/parameter_types.h`、`parameters.inc`、`engineering_commands.inc`、`assembly.inc`、`section_profiles.inc` | **最高風險。** Incoming 的刪除代次、明確重宣告與最後有效值快取附加到舊 `ParameterState`／`World.parameters`，求值還使用舊 `ParameterEval`。GEO-261 已以 `kernel/parameters.h` 型別別名取代舊 state，儲存／求值由 `geo.parameters` 負責；工程操作移至 `geometry-templates/woodworking/native/engineering_operations.c`，assembly／section profile 也有 W 層委派。 | 在現行擁有者與真實操作入口接入候選順序／引用保護，避免復活舊儲存、只修編譯卻漏掉委派路徑，或把只供明確 unbind 的快取混入一般求值。保留 live source 當下求值、已刪 source 的代次快取與最終全圖驗證。 |
| `geometry-web/engineering_bridge.inc`、`assembly_bridge.inc`、`section_profile_bridge.inc`、`panel_fill_bridge.inc` | Incoming 在舊 heap candidate 流程收集 declaration／retirement metadata，清除 scratch，再輸出 `redeclaredReferences`。GEO-261 已改用保留、封存且可重新驗證的 `AppWorldCandidate`，資料位於 `g_preview.transaction->{before,after}`，不是舊 `g_preview.before/after`。 | 保留 scratch 不進正式比較、封存、history 或交換格式的界線；metadata 應從同一次候選產生。不能因移植序列化而退回舊候選生命週期，或略過確認時重新驗證／發布。 |
| `geometry-core/grid_systems.inc`、`grid_bindings.inc`、`subgrid_commands.inc` | Incoming 增加具名 field／axis／id 診斷。GEO-261 已分離核心 store／驗證與木作套用，例如 `grid_system_valid` 多了 `main_along` 參數，child policy 透過 W 層處理。 | 保留精確診斷與現行驗證權威；不能為套用錯誤字串而恢復舊 predicate、舊 signature 或直接 store 存取。 |
| `geometry-web/assembly-workspace.js`、`engineering-workspace.js`、`section-profile-workspace.js` | Incoming 主要新增重宣告提示；GEO-261 修改模板預設與 `GeometryApplication.woodworking` 取值，修改區域大致不同。Incoming `geometry-web/parameters.js` 也新增提示，但該檔不是兩端重疊路徑。 | 兩組變更皆須保留；文字合併乾淨不代表提示正確，仍須確認上述 serializer 從同一候選輸出 metadata。 |
| `geometry-web/cdp_test.js` | Incoming 新增 Chrome startup stderr 與 CDP navigation send／reply 的時間、PID、內容證據記錄。Incoming `marquee_test.js` 另將固定等待改為同一 10 秒預算內等待幾何／選取狀態落定，但它不是雙邊重疊檔。 | 保留 GEO-261 的 frontend 測試接線與 incoming 證據記錄，不把 timing／logging 變更誤當產品功能或新測試通過收據。 |
| `tests/run_all.py`、`run_all.expected.json`、`test_core_integrity.c` | Integration registry 有 205 suites，incoming 有 99 suites，其中八套為相對共同祖先新增。Incoming 修改 C integrity 與多個舊套件的預期數，並新增舊 World 佈局下的 C 檢查。 | Registry 應保留雙邊聯集，不能整檔選 incoming 而丟失 GEO-261 註冊。新 C 檢查需接到現行 store／adapter，不能為測試還原舊產品結構。預期數不是實跑結果。 |
| `tests/mutate.py` | Incoming 增加 M61–M77、bridge oracle 路由及 core＋bridge 閉包；GEO-261 已遷移 M01–M60 至 K／W／H 錨點，加入唯一 nested include 展開與 `generated_source_sha256`。 | 同時保留新 oracle 與移動後錨點／閉包／生成來源指紋。合成來源須重新判定 freshness；不能沿用舊 killed 收據宣稱新來源已驗證。 |
| `geometry-guide/公理層-閱讀器.html` | Incoming 刷新追溯／mutation 資料；GEO-261 已採納新版 SSOT 與閱讀器內容。 | 不得整檔取 incoming 而倒退條文。真正整合後，依當時 SSOT、白話與追溯資料走唯一同步器，就地重建正典並通過完整三道管線檢查；不新增閱讀器。 |

## 模型／Python 預設與 framing／oracle

`27f5c09b…` → `e8eb1da5…` **沒有** `geometry-core/modeling/*`、`model_base.c` 或 `geometry-core/framing-template/*` 來源差異。不能把共同祖先已含內容，或 GEO-261 自己的抽取，誤列為這班 train 的新功能。

GEO-261 的 `geometry-core/modeling/engine.py:8–15` 已由 `geometry_app.bootstrap.default_provider()` 提供 woodworking policy；`geometry-app/geometry_app/model_runtime.py:110` 的 `source_graph` 預設仍為 `False`。Incoming 沒有相反的預設值修改。後續風險屬於新 native 行為經現有 adapter 消費後的相容性，而非已觀察到的雙邊 Python 預設衝突。

Incoming 的 `geometry-core/framing-template/` 只有 `PROPOSAL.md` 與 evidence。`PROPOSAL.md:85–120` 的 FT01–FT06 是驗收 oracle 登記；`:120`、`:155` 明說模板尚未實作、驗收設計未執行，不能視為產品測試通過或 killed 證據。此目錄相對共同祖先沒有增量。

Incoming 實際新增的 oracle 工具是 `tests/bridge_mutation_oracle.py`、`tests/mutation_bridge.py`。後者的 sparse checkout 包含產品目錄，只排除 `tests/evidence` 與 `tests/release-evidence`，沒有排除 GEO-261 新增的 `geometry-app/`／`geometry-templates/`。真正需調和的是 mutation 路由、移動後來源錨點及來源指紋。

## 已有驗證入口：僅列計畫，全部未在本次執行

| 要確認的接縫 | 既有入口 |
|---|---|
| 投影接觸／拆分／不裁條帶及原生完整性 | `tests/run_tests.py`（incoming 加入 14 個場景）、`tests/test_core_integrity.c`、`geometry-web/space_model_test.js`、`geometry-web/cdp_test.js`。 |
| 參數刪除、重宣告、unbind 與候選值歷史 | Incoming 的 `tests/test_parameter_netzero.py`、`test_parameter_retirement_scope.py`、`test_parameters_candidate_value_history.py`、`test_parameters_deleted_unbind.py`、`test_parameters_final_candidate.py`、`test_parameters_unbind_scope.py`、`test_parameters_upstream_unbind.py`；既有 `test_parameters_core.py`、`test_assembly_rules.py`、`test_section_profile_native.py`。 |
| GEO-261 參數權威／W 層工程操作 | `tests/test_geo261_native_parameters.py`、`test_geo261_parameter_sources.py`、`test_geo261_wood_engineering_operations.py`。 |
| 預覽、保留候選、重新驗證與 scratch 界線 | `tests/test_geo261_host_candidate.py`、`test_geo261_staged_candidate_graph.py`、`test_geo261_candidate_cache.py`，搭配上述 incoming 參數測試。 |
| 網格具名診斷與新核心 codec／store | `tests/test_grid_system_contract.py`、`test_infinite_grid_contract.py`、`test_subgrid_contract.py`、`test_geo261_grid_definition_codec.py`。 |
| Frontend 模板取值與預覽提示 | `tests/test_assembly_workspace.js`、`test_section_profile_browser.js`、`test_woodworking_frontend.js`，以及實際執行 app.js 的 `geometry-web/cdp_test.js`；投影／空間另跑 `space_model_test.js`。 |
| Mutation 誠實性、閉包及遷移 | `tests/test_mutation_freshness.py`（incoming `BridgeMutationHonestyTests` 涵蓋 assertion／環境錯誤區分、方法清單、oracle hash、bridge 閉包）、`tests/test_geo261_mutation_migration.py`，以及 `tests/mutate.py --check`／`--selftest`。 |
| 舊模型／交換格式與新 host provider 相容 | `tests/test_engineering_model_compatibility.py`、`test_domain_decoupling_compatibility.py`、`test_modeling_runtime.py`、`test_modeling_transport.py`、`test_rectangular_python.py`、`test_rectangular_bridge.py`、`test_rectangular_template.py`。 |
| 來源驅動、provider／binary 漂移與拒絕 fallback | `tests/test_geometry_source_runtime.py`、`test_domain_source_pins.py`、`test_geometry_host_sources.py`。 |
| 正典閱讀器 | 依序 `python geometry-guide/sync_axiom_reader.py`、`python geometry-guide/sync_axiom_reader.py --check`、`python tests/test_axiom_reader.py`。 |

Incoming `run_all.expected.json` 的變動是預期登記，並非本次觀察到的通過數：C integrity `130→432`、core 場景 `143→157`、assembly rules `35→36`、mutation freshness `24→32`、parameters core `20→40`、reference contract `35→51`、section profile native `27→28`；另新增七套參數測試與 `test_recorded_api_receipts`。GEO-261 對這些既有 key 的預期值仍與共同祖先一致，其新增 suite 應一併保留。

真正 upstream 落地後，先重新確認落地 SHA／共同祖先，再按實際增量更新此預測。既有 Windows compiler、bridge／model-base 環境變數、SAC、隔離 feedback 及使用中服務保護紀律仍適用；本文件不宣稱已滿足它們。
