# RISKS — current_geometry.c 風險清單

> **已過時（2026-09-17 審查）**：B1「座標無上限」、F1 壞範例、F3 無測試／無 git 都已不成立。
> 真正還在的洞見 `BACKLOG.md` 與 2026-09-17 審查結論（place 越界讀、三次乘溢位、互動 place 不重驗 I19）。
> **不要拿本文當現行風險清單。**
>
> 掃描日期：2026-09-12，對象 `current_geometry.c` @ 4,567 行。
> 每條風險標示：嚴重度（🔴高 / 🟡中 / ⚪低）、位置、佐證（編譯警告 / 實測 / 程式碼判讀）。
> 編譯器：MSVC（VS18 BuildTools）`cl /W4 /O2` + `cl /analyze`。

---

## A. 記憶體安全

整體評價：**好**。全程式無 heap 配置——World 用定長陣列、輸入用定長緩衝、
`snprintf`/`GetWindowTextW`/`fgets` 都有上限、`split_tokens` 超過 16 token 回 -1。
剩餘問題集中在少數邊界：

| # | 嚴重度 | 問題 | 位置 | 佐證 |
|---|--------|------|------|------|
| A1 | 🟡 | `parse_scene_file` 的 BOM 檢查：`text[0]==0xEF` 後直接讀 `text[1]`、`text[2]`。一行只有 1–2 byte 時讀到 `\0` 之後的未初始化堆疊（char 讀取非 UB，但 `/analyze` 判定「可能使用未初始化記憶體」） | ~L4101–4105 | `cl /analyze` C28199 |
| A2 | 🟡 | `gdi_text`：`CreateFontW` 失敗回 NULL 時仍 `SelectObject(g->dc, font)`（對 NULL 呼叫違反 API 規格，雖實務上 SelectObject 回錯不當機） | ~L2400 | `cl /analyze` C6387 |
| A3 | 🟡 | `gdi_color(hex)` 直接 `strtoul(hex + 1, …, 16)`：假定字串必為 `#rrggbb` 且 `hex` 非 NULL。新增 style 若 `line` 為 NULL 或格式不對 → NULL 解引用/解析錯誤 | ~L2127 | 判讀；目前 STYLE_SPEC 全部合法所以暫未觸發 |
| A4 | ⚪ | `path_beside_source` 用 `__FILE__` 推導目錄：把 exe 移到別處、或用相對路徑編譯，「載入範例」就找不到 `room_a.scene`。不是安全問題但屬部署脆弱點 | ~L2015 | 判讀 |
| A5 | ⚪ | 無結尾換行的最後一行若超過 511 byte：第一次 `fgets` 拿 511 byte、`feof` 為真 → 不報「這一行太長」，**靜默截斷**該行並照常解析 | ~L4092 | 判讀 |
| A6 | ⚪ | 行長度 off-by-one：buffer 512、`fgets` 最多讀 511 byte，所以恰好 511 字元 + `\n` 的合法行會被誤判「這一行太長」。實際上限是 510 字元 | ~L4092 | 判讀 |

## B. 未定義行為 / 整數溢位

全整數設計消除了浮點誤差，但代價是 **int64 有號溢位 = UB**，且場景檔可以接受
任意 int64 值（`parse_i64` 無上界檢查）：

| # | 嚴重度 | 問題 | 位置 | 佐證 |
|---|--------|------|------|------|
| B1 | 🔴 | **座標無上限 → 乘法溢位 UB**。實測 `surface … 0 0 99999999999999 3000` 被接受並產出 SVG；`view_quad_area2`/`view_dist2_to_segment`/`view_unproject_on_surface`/`timber_place_a0_on_surface`/`surface_point_to_room` 內的 `x*x`、`x*y` 在 ~1e9 mm 等級就會溢位 int64 | `parse_i64`(~L3258) + 全部視圖數學 | 實測接受 1e14 座標 |
| B2 | 🟡 | `view_dist2_to_segment` 的 `dx*dx`、`t_num` 等：`px`,`dx` 是兩點差，場景大可到 region 範圍；1e10 級座標即溢位 | ~L1287 | 判讀（B1 同族） |
| B3 | 🟡 | `view_unproject_on_surface` 的 `a*d-b*c`、`e*d-b*f` 等：det/分子都是座標乘積，溢位後 `% det`/`/ det` 結果無意義（不會當機但會給錯 UV） | ~L1718–1731 | 判讀 |
| B4 | ⚪ | `--bench` 用 `atoi`：溢出/非數字行為為 impl-defined；非數字得到 0 → 靜默不跑 | ~L4200 | 判讀 |
| B5 | ⚪ | `gdi_to_pixel` 的 `(LONG)(double)`：座標經 scale 後超出 LONG 範圍 → C 標準 impl-defined（MSVC 為飽和/截斷）；配合 B1 的大座標才會出現 | ~L2133 | 判讀 |
| B6 | ⚪ | `WM_MOUSEMOVE`/`WM_LBUTTONDOWN` 用 `(short)LOWORD/HIWORD` 取帶符號座標——正確寫法（支援多螢幕負座標），列此備查：無問題 | ~L2861,2934 | 判讀 |

## C. 浮點數與幾何容差

幾何層零浮點；容差問題全部集中在「畫面像素 ↔ mm」的 GDI 互動層：

| # | 嚴重度 | 問題 | 位置 | 佐證 |
|---|--------|------|------|------|
| C1 | 🟡 | `gdi_screen_to_view` 的 `(Coord)(x + 0.5)` 四捨五入對**負值錯誤**（C 轉型向零截斷）：當 `(px-ox)/scale - tx` 為負時會往零方向偏 1mm。縮很小、視圖 tx 為正時游標 mm 常為負 → 命中測試與拖曳反解會系統性偏半格 | ~L2642–2643 | 判讀 |
| C2 | 🟡 | `view_unproject_on_surface` 用「`u_num % det != 0` 拒絕非整數解」。det 恆為 ±1（N·into，兩組單位軸向量），所以實際上永遠整除——這段檢查是死碼，但它的存在暗示設計者以為 det 可能 >1；若未來放寬軸限制此假設立刻失效 | ~L1726–1731 | 判讀 |
| C3 | ⚪ | `view_dist2_to_segment` 整數除法向零截斷：最近點誤差 <1mm（註解已自述）。對拾取影響極小，列此備查 | ~L1312 | 註解自述 |
| C4 | ⚪ | 拾取半徑 `8.0/scale + 0.5`（像素→mm）：scale 很小時半徑變大尚可接受；但 C1 的負值截斷同樣適用（此處恆正，無實害） | ~L2645 | 判讀 |
| C5 | ⚪ | `StyleSpec.text_mm` 名為 mm，SVG 輸出卻當 px 用（`font: bold 150px`）；GDI 才乘 scale。語義不一致，調字級時容易誤解 | STYLE_SPEC ~L1189 + svg ~L1975 | 判讀 |
| C6 | ⚪ | 拾取比較用 `d2 <= best2`：等距時**後寫入的贏**（索引大的參考線優先）；文件未載明此 tie-break | ~L1802 | 判讀 |

## D. 座標系混用風險

系統內有 5 套座標：房間 (x,y,z)、表面 (u,v,w)、角材局部 (長度,A,B)、
視圖 mm (2D)、螢幕像素。防線目前靠命名與型別，以下為弱點：

| # | 嚴重度 | 問題 | 佐證 |
|---|--------|------|------|
| D1 | 🟡 | **`move` 參考線後，`TimberAnchor.uv` 留下舊值**。註解明說「place 是事件不是約束」，但 `main` 的報告仍印「參考線交點 (u,v)」——move 之後印出來的不再是交點，也不加註「已過期」。語義上合法、輸出上誤導 | ~L3880 move、~L4436 印錨點 |
| D2 | 🟡 | `Scene` 是借用指標視圖：任何 World 寫入後忘記 `scene_from_world`+`scene_compute_layout`，繪製/拾取就讀到舊狀態。GDI 由 `app_refresh` 統一處理沒問題，但這是隱性契約、無 assert 保護 | ~L3172, ~L2556 |
| D3 | ⚪ | `scene_pick_at` 存的是**陣列索引**不是 id；World 目前只增不減所以穩定，但一旦加入刪除類指令（unplace/delete），索引型 pick 會立刻指錯物件 | ~L1691–1696 |
| D4 | ⚪ | `surface_get_edge_side_plane` 的 Plane3 是**無限平面**屬性（法向+一點），不是被邊界裁切的矩形。名字「側向承載平面」容易讓人以為它是面片 | ~L377–425 |
| D5 | ⚪ | 視圖投影丟掉 `into` 軸：三視圖中同一條參考線在多個視圖都可被點，且拾取時不知深度。`scene_pick_at` 對「疊在同處的多支角材」取**索引最後**而非視線最近——跨角材的正確性有限 | ~L1750–1761 |
| D6 | ⚪ | `room` 只驗「面彼此一致」，不驗「面之間真的相接成盒」（少面時是部分宣告，已文件化）；也沒有檢查角材/參考線歸屬的面是否在某間房裡——room 目前是純宣告層 | `room_bind` ~L3441 |

## E. 生命週期與所有權

| # | 嚴重度 | 問題 | 位置 | 佐證 |
|---|--------|------|------|------|
| E1 | 🟡 | `bench_paint` 早期 return 路徑漏資源：`sink`/`sink_bmp` 建立失敗時 `screen` DC 沒 `ReleaseDC`；若其中一個建成功另一個失敗，成功的也漏 | ~L3080–3087 | 判讀 |
| E2 | ⚪ | GDI 物件快取所有權規則分散三處（`gdi_select_style` 的 `owned` flag、`gdi_cache_release`、`gdi_app_release_objects`）：style 越界走 owned 路徑這設計正確但隱晦，改動時易漏 DeleteObject | ~L2164–2253 | 判讀 |
| E3 | ⚪ | `g_scene_last_error` 全域 256B 緩衝：單執行緒沒問題；但它是「錯誤同時去 stderr 與 UI」的唯一通道，任何未來多執行緒/重入都會踩到 | ~L3326 | 判讀 |
| E4 | ⚪ | `g_edit_orig_proc` 全域 WNDPROC：假設整個程式只有一個視窗一個 EDIT。再開第二個視窗會互相覆寫 | ~L2653 | 判讀 |
| E5 | ⚪ | `World.anchors[]` 與 `timbers[]` 是平行陣列靠索引同步：靠 `apply_place_line` 的 `timber - world->timbers` 指標差建立——正確但脆弱（刪除指令會破壞對齊） | ~L3871 | 判讀 |
| E6 | ⚪ | `emit_svg_three_views` 只檢查 `fclose` 結果；中途 `fprintf` 失敗（磁碟滿）會產生截斷但仍回報成功的 SVG | ~L1940–1995 | 判讀 |

## F. 工程面風險（非程式碼缺陷，但會咬人）

| # | 嚴重度 | 問題 | 佐證 |
|---|--------|------|------|
| F1 | 🔴 | **隨附範例檔 2/4 壞掉**：`ceiling-a.scene`、`demo-two-timbers.scene` 用舊 `place` 語法（無 `on <面id>`），實測 exit 1。使用者照範例學會學到錯的 | 實測 |
| F2 | 🟡 | **導讀頁已脫鉤**：`check_panels.py` 實測 3 個 callout unresolved（SCENE_COMMANDS 改 min/max 欄位格式後 HTML 未重跑）。檔頭註解要求「改動本檔後須重跑 make_guide.py + check_panels.py」——room 功能這次改動顯然沒跑 | 實測 check_panels exit 1 |
| F3 | 🟡 | 無建置腳本、無測試目錄、無 git 倉庫、無 CI。驗證完全靠手動執行 | 判讀 |
| F4 | 🟡 | 原始碼 UTF-8 **無 BOM**：MSVC 在非 UTF-8 系統字碼頁（如傳統 BIG5 950 機器）會把中文字串/註解誤判碼，輸出變亂碼甚至編譯錯誤。需 `/utf-8` flag 或加 BOM | 判讀（檔頭無 BOM 已驗） |
| F5 | ⚪ | 未知 CLI 參數靜默忽略（`--bogusflag` 實測照常跑 exit 0）：打錯 `--scen` 會默默用內建場景 | 實測 |
| F6 | ⚪ | `/W4` 警告未清：`into` 未用（L1440，scene_draw_view 裡的死碼）、7 個 `count` 參數未參考（C4100）——新版剛引入 | 編譯實測 |
| F7 | ⚪ | `room` 指令的錯誤訊息「不認得的指令（只有 surface edge guide timber place）」沒把 move/room/reset 列進去 | ~L4065 |
| F8 | ⚪ | `#include <errno.h>` 重複兩行（L1–L2） | 判讀 |
| F9 | ⚪ | `asm-analysis.md` 對應舊版（4,327 行），新版加了 room 功能後未同步——讀者會誤以為是最新 | 判讀 |
| F10 | ⚪ | `reset` 出現在 scene 檔中段是合法的（註解明載），但會讓「前面建好的面」消失且無警告；配合「needs_surface 只檢查 count>0」的粗判，語義上容易誤用 | ~L3967 |

## 風險彙總

- 🔴 高：B1（int64 溢位 UB，可由場景檔直接觸發）、F1（壞範例檔）
- 🟡 中：A1、A2、A3、B2、B3、C1、C2、D1、D2、E1、F2、F3、F4
- ⚪ 低：其餘

**最大系統性風險**：場景檔是使用者輸入面，`parse_i64` 接受全 int64 範圍，
而下游所有幾何都假設「mm 級的合理尺寸」。一個夠大的數字就能把
UB 溢位帶進投影/拾取/放置數學，且不會當機——只會給錯的答案。
