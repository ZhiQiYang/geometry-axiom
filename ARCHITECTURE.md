# ARCHITECTURE — current_geometry.c 幾何系統

> **已過時（2026-09-17 審查）**：本文停在 2026-09-12、`current_geometry.c` 4,567 行／矩形面／`room`／8 指令。
> 現況約 13,000 行，物件是邊界面／承載面／Space／grid／RC，指令含 `grid`／`between`／`span-auto`／`delete`。
> **不要拿本文當地圖。** SSOT 是 `公理層.md`；工單與已知洞見 `BACKLOG.md`。
>
> 掃描日期：2026-09-12。對象版本：`current_geometry.c` @ 4,567 行（約 116 個函式）。
> 驗證方式：MSVC BuildTools（VS18）`cl /W4 /O2` 實際編譯 + 執行；scene 檔逐一餵入測試；
> `cl /analyze` 靜態分析；`geometry-guide/check_panels.py` 文件一致性檢查。
> 範圍聲明：本 repo（`D:\knowledgebase`）是多專案知識庫；本文只涵蓋 C 幾何系統
> （`current_geometry.c` + `*.scene` + `geometry-guide/`）。`BlockCAD-SketchUp-Plugin/`、
> `zealot/`、`github/` 是其他專案，不在本文範圍。

---

## 1. 系統定位

單檔 C11 程式，無外部相依（只用 C 標準庫 + Windows user32/gdi32）。用途：
在平釘天花板的空間邊界面上，用參考線定位、把角材（L×A×B 實木條）貼到面上，
輸出三視圖（SVG 檔 + 可互動的 GDI 視窗）。

核心設計原則（從程式碼與註解歸納）：

- **全整數幾何**：`Coord = int64_t`，單位 mm，無浮點；相等/正交判斷全部精確。
- **只存定義、不存推導結果**：邊不存端點、參考線不存線段、角材不存頂點，
  全部由父物件即時推導。
- **守門員模式**：每個 domain 動詞（`surface`/`edge`/`guide`/`timber`/`place`/`move`/`room`）
  都先全檢查、通過才寫入 `World`，失敗無副作用。
- **後端介面**：幾何只走訪一次，經 `DrawTarget` 函式表分派到 SVG 或 GDI；
  `target == NULL` 時同一段程式碼用來量測邊界。

## 2. 模組清單（檔內區段順序）

| # | 模組 | 行號區間 | 內容 |
|---|------|---------|------|
| 1 | 基礎幾何型別 | ~34–111 | `Coord`、`Point3`、`Vector3`、`SurfacePoint2`、`SurfaceSegment2`、`Segment3`、`Quad3`、`Plane3`；`vector_dot/cross/negate/equal` |
| 2 | 空間邊界面 | ~113–230 | `SurfaceFrame`、`SurfaceRegion2`、`SpaceBoundarySurface`；`surface_frame_is_valid`、`surface_point_to_room`、`surface_contains_point` |
| 3 | 四條正交邊 | ~232–425 | `SurfaceEdgeKind`、`SurfaceBoundaryEdge`；local segment / room segment / side plane 三種推導 |
| 4 | 參考線 | ~427–587 | `GuideDirection`、`GuideLine`；`create_guide_line`、`guide_line_move`、`guide_line_get_local_segment`、`guide_line_intersection` |
| 5 | 角材實體 | ~589–913 | `TimberFaceId`（A0/A1/B0/B1/START/END）、`TIMBER_FACE_SPEC`/`TIMBER_FACE_WALK`/`TIMBER_FACE_NAMES`、`Timber`、`SurfaceDirection`、`SurfaceDepthSide`；`timber_construct`、`timber_place_a0_on_surface`、`timber_local_to_room`、`timber_get_face_room` |
| 6 | 文字輸出 | ~915–1064 | `print_*` 系列：純排版，無幾何 |
| 7 | 三視圖幾何 | ~1066–1670 | `ViewFrame`/`VIEW_FRAMES`（前/側/仰）、`ViewPoint2`、`ViewBounds`、`Scene`（借用指標的唯讀視圖）、`DrawStyle`/`STYLE_SPEC`、`DrawTarget` vtable、`timber_project_faces`、`scene_draw_view`、`scene_compute_layout`、`scene_render` |
| 8 | 命中測試 | ~1672–1845 | `ScenePick`、`view_unproject_on_surface`（view mm → surface UV 反解）、`scene_pick_at`、`scene_draw_pick` |
| 9 | SVG 後端 | ~1847–2013 | `svg_*` 實作、`emit_svg_three_views`、`path_beside_source`（__FILE__ 相對路徑） |
| 10 | World 定義 | ~2020–2077 | 容量常數、`TimberAnchor`、`Room`、`World`、前向宣告 |
| 11 | GDI 後端 + 互動 | ~2079–3162（`#ifdef _WIN32`）| `GdiObjectCache`（筆/刷/字型快取）、`GdiContext`、樣式 scope、離屏緩衝、`gdi_window_proc`（拖曳參考線、點選、輸入列、載入範例）、`gdi_show_three_views`、`bench_paint` |
| 12 | 場景輸入層 | ~3164–4157 | `scene_from_world`、關鍵字查表、`parse_i64/u32`、`split_tokens`、`scene_error`（全域錯誤緩衝）、`world_find_*`、房間一致性（`axis_index`/`surface_extent_on_axis`/`room_bind`）、`apply_*_line` × 8、`SCENE_COMMANDS` 表、`apply_scene_line`、`parse_scene_file` |
| 13 | main | ~4163–4567 | 參數解析、內建房間 A 場景、文字報告、SVG 輸出、開視窗、bench |

## 3. 核心資料型別

| 型別 | 定義 | 備註 |
|------|------|------|
| `Coord` | `int64_t` | 全域座標單位，1 = 1 mm |
| `Point3` / `Vector3` | `{x,y,z}` | 同構；僅語義區分（位置 vs 方向） |
| `SurfacePoint2` | `{u,v}` | 表面局部座標 |
| `SurfaceFrame` | `origin + axis_u + axis_v + normal` | 公理：`room = origin + u·U + v·V + w·N`；只接受單位正交整數軸且 `U×V=N` |
| `SpaceBoundarySurface` | `id + frame + region` | 矩形邊界面（如天花板） |
| `SurfaceBoundaryEdge` | `id + parent_surface_id + kind` | 不存端點，四種 kind（MIN_U/MAX_U/MIN_V/MAX_V） |
| `GuideLine` | `id + surface_id + direction + offset` | 非實體定位線；ALONG_U 固定 v=offset |
| `Timber` | `id + length/size_a/size_b + placed + origin/axis_length/axis_a/axis_b` | 未放置時框架是標準佔位值 |
| `TimberAnchor` | `surface_id + uv + from_guides` | 與 `World.timbers[]` 同索引的平行陣列 |
| `Room` | `id + faces[≤6] + face_count` | 一組被宣告為彼此一致的面；2–6 片 |
| `Scene` | 6 個 `const` 指標 + count | **借用** World 的陣列，World 變動後須重建 |
| `World` | 5 組定長陣列 + counts | 上限：8 面 / 32 邊 / 16 線 / 64 角材 / 4 房 |
| `DrawTarget` | `ctx` + 6 個函式指標 | begin/end_view、rect、polygon、line、text |
| `ScenePick` | `view + guide + timber + face` | -1 表示無命中 |
| `GdiApp` | world 指標 + scene/layout + 互動態 + 離屏緩衝 + 物件快取 | 視窗全部狀態 |

## 4. 資料流

```
scene 檔 / 視窗輸入列
        │  split_tokens → apply_scene_line → apply_*_line（守門員）
        ▼
      World（唯一定義源，定長陣列）
        │  scene_from_world()（借用指標）
        ▼
      Scene ──► scene_compute_layout（走訪 3 次，target=NULL 只量邊界）
        │            ▼
        │         SceneLayout（各視圖 bounds + tx/ty 平移）
        ▼
      scene_render ──► scene_draw_view × 3 視圖
                            │  DrawTarget vtable
              ┌─────────────┴─────────────┐
              ▼                           ▼
        SVG 後端（stdio）          GDI 後端（離屏位圖 → BitBlt）
```

互動迴圈（僅 Windows）：

```
WM_MOUSEMOVE ─► gdi_screen_to_view（px→view mm）─► scene_pick_at ─► hover 高亮
WM_LBUTTONDOWN 點到 guide ─► 拖曳：view_unproject_on_surface → clamp → guide_line_move → app_refresh
輸入列 Enter ─► WM_APP_APPLY_INPUT ─► interactive_apply_line ─► apply_scene_line ─► app_refresh
app_refresh = scene_from_world + scene_compute_layout + 清互動態 + InvalidateRect
```

## 5. 模組相依關係

```
main ──┬─► 場景輸入層 ──► domain 動詞（guide/edge/timber/place/move/room/surface）
       │        │              │
       │        │              ▼
       │        │         幾何核心（§1–§5）：無任何外部相依，純 int64 算術
       │        │
       │        └─► World/Scene ──► 三視圖幾何（§7）──► DrawTarget 介面
       │                                            ├─► SVG 後端（§9）
       │                                            └─► GDI 後端（§11，_WIN32）
       ├─► 命中測試（§8）：被 GDI 互動層使用，SVG 路徑不走
       └─► 文字輸出（§6）
```

- 幾何核心（§1–§5）不依賴任何上層模組——可以整段抽成獨立 library。
- `DrawTarget` 是唯一的後端抽象；新增後端（如 PDF/DX）不需動幾何層。
- GDI 互動層跨層呼叫解析層的 `apply_scene_line`/`parse_scene_file`/`scene_last_error`，
  因此 World 定義與前向宣告放在 GDI 之前（§10）。

## 6. 目前實際支援的功能（已逐一執行驗證）

**場景指令（8 個，scene 檔與視窗輸入列共用同一條路徑）**

| 指令 | 欄位 | 功能 |
|------|------|------|
| `surface` | 11 | 宣告矩形邊界面（原點 + ±x/±y/±z 兩軸 + UV 範圍），法向量由 U×V 推導 |
| `edge` | 4 | 宣告某面的邊（min_u/max_u/min_v/max_v） |
| `guide` | 5 | 面上參考線（u 或 v 方向 + offset） |
| `timber` | 5 | Construct 角材（長度、A、B 尺寸，皆須 >0） |
| `place` | 9 | `place <id> on <面id> at-guides <線1> <線2> <±u/±v> <±n>` 或 `at <u> <v>` |
| `move` | 3 | 改參考線 offset（有範圍檢查；已放置角材不追溯） |
| `room` | 4–8（變長） | 把 2–6 片面綁成一間房，檢查法向槽位不衝突、區間一致、法向朝外（實測六面封閉盒通過、內朝法向被拒） |
| `reset` | 1 | 清空整個 World |

**輸出**

- 文字報告：表面/邊（含側向承載平面）/參考線/房間/錨點/角材六面頂點。
- SVG 三視圖：前視（觀者 -Y）、側視（觀者 +X）、仰視（觀者 -Z），第三角法版面，
  深度排序畫角材面、退化面自動跳過。
- GDI 視窗：同一份幾何走訪；滑鼠 hover/點選高亮、拖曳參考線改 offset、
  底部指令列即時改場景、「載入範例」（讀 exe 旁 room_a.scene）、Esc 關閉。
- `--bench N`：量測 GDI 每幀 cold/warm 成本（實測 cold ≈ 5103µs / warm ≈ 2233µs）。

**CLI 參數**：`--scene <檔>`、`--out <svg>`、`--no-window`、`--bench <N>`。

**內建預設**：不給 `--scene` 時用硬編房間 A（4000×3000、天花高 2500、
兩條參考線、一支 1800×27×33 角材）——實測與 `room_a.scene` 輸出一致。

## 7. 已知的伴生資產

| 檔案 | 狀態 |
|------|------|
| `room_a.scene`、`room_box.scene`、`room_full.scene` | ✅ 可解析。`room_box` 含 2 面部分房；`room_full` 是六面封閉盒範例（實測 exit 0） |
| `ceiling-a.scene`、`demo-two-timbers.scene` | ❌ **壞的**——舊語法（`place` 無 `on`），執行 exit 1 |
| `current_geometry.svg` | 程式產出物 |
| `geometry-guide/make_guide.py` + `check_panels.py` | ⚠️ 導讀頁產生器；check_panels 現有 **3 個 callout 失敗**（SCENE_COMMANDS 表格改了 min/max 格式，HTML 未跟上） |
| `asm-analysis.md` | 舊版的組合語言逐行分析報告（對應 4,327 行版本） |
