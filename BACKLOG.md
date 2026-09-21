# BACKLOG — current_geometry.c 工單庫

> 產生日期：2026-09-12，對象 `current_geometry.c` @ 4,567 行。
> 估時以「熟悉此 codebase 的工程師」為準（30 分鐘～3 小時）。
> 平行標記：⚡= 可與同標記工單同時進行（不摸同一段程式碼）。
> 相依標記：`←` 後面列出必須先完成的工單。

---

## 第 0 流：基礎設施（先做，後面所有工單的驗收都靠它）

### GEO-001 ⚡ 建立一鍵建置腳本
- **內容**：`build.bat`：`vcvars64` + `cl /nologo /W4 /O2 /utf-8 current_geometry.c /Fe:current_geometry.exe`；另出 `build_debug.bat`（`/Od /Zi /RTC1 /W4`）。
- **驗收**：乾淨 checkout 下跑 `build.bat` 產生 exe；警告數量印在結尾。
- **檔案**：新增 `build.bat`、`build_debug.bat`。
- **測試**：手動跑兩支腳本各一次；debug 版跑 `--no-window` 無 RTC 攔截。
- **相依**：無。**估時 1h**。

### GEO-002 ⚡ 建立最小回歸測試腳本
- **內容**：`run_tests.bat`（或 python）：逐一執行 `--scene X --no-window --out Y`，比對 exit code 與 stdout 關鍵字。初版收錄：room_a（exit 0）、room_box（0）、各錯誤案例（exit 1）。
- **驗收**：`run_tests` 全綠才准 commit；失敗時印出哪個 case、預期/實際。
- **檔案**：新增 `tests/run_tests.py` + `tests/cases/*.scene`。
- **測試**：故意弄壞一個 scene 確認測試會紅。
- **相依**：GEO-001。**估時 1.5h**。

### GEO-003 ⚡ 修復壞掉的範例檔
- **內容**：`ceiling-a.scene`、`demo-two-timbers.scene` 改新語法（`place … on <面id> …`）；或若決定廢棄就刪除並在文件註明。
- **驗收**：兩個檔 `cg --scene` 皆 exit 0；`demo-two-timbers` 產出含兩支角材的 SVG。
- **檔案**：`ceiling-a.scene`、`demo-two-timbers.scene`。
- **測試**：GEO-002 納入這兩個檔。
- **相依**：無（測試納入相依 GEO-002）。**估時 30min**。

### GEO-004 寫建置/使用說明 README
- **內容**：`README-geometry.md`：編譯需求（VS BuildTools）、build 指令、CLI 參數表、scene 格式入口。
- **驗收**：照文件從零能編出 exe 並產出 SVG。
- **檔案**：新增 `README-geometry.md`。
- **測試**：找不熟的人照做一次（或自己刪 exe 重走流程）。
- **相依**：GEO-001。**估時 1h**。⚡ 與代碼類工單全平行。

---

## 第 1 流：解析層與輸入面（RISKS B1/B4、F5、A5/A6）

### GEO-010 ⚡ Coord 輸入上限
- **內容**：`parse_i64` 之外加 `parse_coord`：限制 `|v| ≤ 100,000,000` mm（=100 km，遠大於任何房間）；所有場景檔數值欄位改用它。id 仍走 `parse_u32`。
- **驗收**：`surface … 0 0 99999999999999 3000` 被拒（exit 1）；現有合法 scene 全部仍通過。
- **檔案**：`current_geometry.c`（parse 層 ~L3258）。
- **測試**：tests/cases 加超大座標、負座標、INT64_MAX、剛好上限±1 的邊界 case。
- **相依**：GEO-002。**估時 1h**。

### GEO-011 溢位安全評估與中間值加寬 ← GEO-010
- **內容**：GEO-010 擋住外部輸入後，盤點內部乘法鏈（`view_quad_area2`、`view_dist2_to_segment`、`view_unproject_on_surface`、`timber_place_a0_on_surface` 的 far_corner、`surface_point_to_room`）：在 1e8 上限內最大乘積 ~1e16 < int64；寫一份「安全域證明」註解進檔頭。若要支援更大座標則關鍵路徑換 `__int128`/檢查乘。
- **驗收**：檔內有一節註解寫明安全域推導；debug 版加 `assert` 擋越界輸入。
- **檔案**：`current_geometry.c`。
- **測試**：以 1e8 上限的極端 scene 跑 debug 版，無 assert 觸發。
- **相依**：GEO-010。**估時 2h**。

### GEO-012 ⚡ 修「無結尾換行超長末行」靜默截斷
- **內容**：`parse_scene_file`：`fgets` 讀滿且無 `\n` 時，不論 `feof` 都再讀一個字元確認是否真的到檔尾；超長一律報錯。
- **驗收**：511+ 字元無換行的末行報「這一行太長」。
- **檔案**：~L4092。
- **測試**：tests/cases 加兩個檔：恰好 510 字元末行（過）、600 字元無換行末行（拒）。
- **相依**：GEO-002。**估時 45min**。

### GEO-013 ⚡ 修 511 字元合法行被誤殺
- **內容**：同上區段，或把 `SCENE_MAX_LINE` 定義為「含 \n\0」並把 buffer 加大 2。
- **驗收**：510 字元內容 + `\n` 的行可解析；511+ 字元才報錯，錯誤訊息寫明上限。
- **檔案**：~L2020、~L4092。
- **測試**：邊界行長 509/510/511 各一個 case。
- **相依**：GEO-002。**估時 45min**。與 GEO-012 摸同一區塊，**不平行**。

### GEO-014 ⚡ BOM 檢查改為長度感知
- **內容**：`if (line_no==1 && length>=3 && text[0]==0xEF && …)`；順便消 C28199。
- **驗收**：`cl /analyze` 不再有 C28199；1-byte 場景檔不誤判。
- **檔案**：~L4101。
- **測試**：tests/cases 加 1 字元檔、含 BOM 檔、偽 BOM（EF BB 41）檔。
- **相依**：GEO-002。**估時 30min**。

### GEO-015 ⚡ 未知 CLI 參數要報錯
- **內容**：argv 掃描迴圈加 else：`fprintf(stderr, "不認得的參數：%s\n")` + return 1；順便把 `--help` 印用法。
- **驗收**：`--scen` 打錯會 exit 1 並提示；`--help` 印全部參數 exit 0。
- **檔案**：main ~L4177。
- **測試**：run_tests 加 `--bogus` case。
- **相依**：GEO-002。**估時 30min**。

### GEO-016 ⚡ `--bench` 參數改用 strtol 並驗範圍
- **內容**：換掉 `atoi`：非數字/負數/0 報錯；上限 1e6 防呆。
- **驗收**：`--bench abc`、`--bench -5` exit 1；`--bench 10` 正常。
- **檔案**：main ~L4194。
- **測試**：手動三個 case。
- **相依**：無。**估時 30min**。

### GEO-017 錯誤訊息列出全部指令名
- **內容**：`apply_scene_line` 的「不認得的指令」改為從 `SCENE_COMMANDS` 表動態列出（現在漏寫 move/room/reset）。
- **驗收**：輸入 `foo` 時訊息含全部 8 個指令。
- **檔案**：~L4065。
- **測試**：互動輸入列打 `foo` 看狀態列。
- **相依**：無。**估時 30min**。⚡

### GEO-018 ⚡ scene 檔規格文件
- **內容**：`SCENE-FORMAT.md`：每指令欄位、單位、座標系圖、錯誤語義（哪行錯報哪行）、reset 的中途生效行為。
- **驗收**：文件與 `SCENE_COMMANDS` 逐列對得上；含 room 的六面盒完整範例。
- **檔案**：新增 `SCENE-FORMAT.md`。
- **測試**：文件內每個範例實際餵給程式驗 exit code。
- **相依**：無。**估時 1.5h**。

---

## 第 2 流：幾何核心正確性（RISKS C1/C2/C6、D1/D5）

### GEO-020 ⚡ 修 GDI 滑鼠反解的負值四捨五入
- **內容**：`gdi_screen_to_view`：`(Coord)(v + 0.5)` 改成 `(Coord)floor(v + 0.5)` 或 `(Coord)llround(v)`；pick_radius 同理（恆正但也要一致）。
- **驗收**：游標在版面左/上界外（mm 為負）時，unproject 回來的 UV 不偏 1mm；用 GDI 拖曳把 guide 拉到負值區域能對齊整數格。
- **檔案**：~L2642。
- **測試**：手動 GDI 驗 + 在程式加一行 debug 印 px→mm 對照表人工核對。
- **相依**：無（需 include math.h）。**估時 45min**。

### GEO-021 釐清並註解 unproject 的 det 恆 ±1
- **內容**：`view_unproject_on_surface` 的 `% det != 0` 在單位軸前提下永不觸發——把這個證明（det = N·into ∈ {-1,0,1}）寫進註解，或改成 `assert`；同時決定：若未來支援非軸向面，這裡要改成什麼。
- **驗收**：註解或 assert 就位；沒有「以為有用其實沒用」的防禦碼。
- **檔案**：~L1704–1733。
- **測試**：紙面證明 + 三視圖各拖一次 guide 確認行為不變。
- **相依**：無。**估時 1h**。⚡

### GEO-022 ⚡ 跨角材拾取改為取視線最近者
- **內容**：`scene_pick_at` 對多支角材同點命中時，比較 `distance4` 取最小（最近），而非「索引最後」。
- **驗收**：兩支角材在俯視圖重疊時，點到的是最靠近觀者那支的面。
- **檔案**：~L1750–1761。
- **測試**：scene：兩支角材同 UV 不同深度側（+n/-n），互動點選確認選中上層。
- **相依**：無。**估時 1h**。

### GEO-023 ⚡ move 之後錨點報告加「已過期」標記
- **內容**：`from_guides` 錨點在 guide move 後不再等於交點；`main` 報告與（未來）UI 狀態列在 guide 動過後加印「（錨點為放置當時的交點）」或重算交點並標 `(原 500,300 → 現 700,300)`。
- **驗收**：move 後的輸出不會把舊交點當現況印。
- **檔案**：~L3880、~L4436。
- **測試**：scene 檔寫 place → move → 看輸出文字。
- **相依**：無。**估時 1h**。

### GEO-024 place at-guides 的 guides 必須屬於同一面——補明確錯誤
- **內容**：現在靠 `guide_line_intersection` 的 surface_id 檢查間接拒絕；在 `apply_place_line` 先分別檢查 `guide_a->surface_id == surface_id` 給出「參考線不在指定面上」的明確訊息。
- **驗收**：跨面 guide 組合報新訊息；同面同方向仍報舊訊息。
- **檔案**：~L3828。
- **測試**：tests/cases 加跨面 guide case，比對錯誤文字。
- **相依**：GEO-002。**估時 45min**。⚡

### GEO-025 ⚡ 退化面（area2==0）策略文件化
- **內容**：`timber_project_faces` 跳過退化面是對的（輪廓在相鄰面邊上），但「skip 的面不可被點選」這個副作用要寫進註解；評估是否讓退化面以「線」形式可被拾取。
- **驗收**：註解寫明；若決定可拾取則拾取半徑內退化面以 segment 命中。
- **檔案**：~L1411、~L1739。
- **測試**：END 面在正視圖退化成線 → 確認能否被點（依決定驗收）。
- **相依**：無。**估時 1.5h**。

### GEO-026 ⚡ guide 與邊重合（offset=邊界值）行為定義
- **內容**：`guide_offset_in_range` 允許 offset == min/max，與邊重合；決定：允許（現狀，寫進文件）或警告。若允許，scene_draw_view 應避免 guide 虛線與 edge 實線完全重疊看不出來（例如稍微內縮 1px 或改色）。
- **驗收**：決定寫進 SCENE-FORMAT.md；重疊時圖上可辨識。
- **檔案**：~L448、~L1517。
- **測試**：scene：guide offset=0 與 offset=max_v 各一條，看 SVG。
- **相依**：GEO-018。**估時 1h**。

---

## 第 3 流：GDI / Win32 層（RISKS A2/A3、E1/E2/E4）

### GEO-030 ✅ 已做(2026-09-21) CreateFontW 失敗時不 SelectObject(NULL)
- **內容**：`gdi_text`：`font==NULL` 時改用 `GetStockObject(SYSTEM_FONT)` 或直接 return；消 C6387。
- **驗收**：`cl /analyze` 無 C6387；故意讓 CreateFontW 失敗（破壞字型名）時不當機、文字用預設字型。
- **檔案**：~L2400。
- **測試**：暫時把字型名改成不存在字串跑一次。
- **相依**：無。**估時 30min**。

### GEO-031 ⚡ gdi_color 加格式檢查
- **內容**：檢查 `hex[0]=='#'` 且長度 ≥7、其餘為 hex 字元；不合法回黑並可選 debug 印。
- **驗收**：`gdi_color(NULL)`/格式錯誤不再 UB；STYLE_SPEC 現值全部通過。
- **檔案**：~L2127。
- **測試**：單元測試或臨時 printf 驗三種壞輸入。
- **相依**：無。**估時 30min**。

### GEO-032 ⚡ bench_paint 早期 return 補資源釋放
- **內容**：`sink`/`sink_bmp` 任失敗時：釋放已建物件 + `ReleaseDC(NULL, screen)`；用 goto cleanup 或 helper。
- **驗收**：程式碼走查確認所有 exit path 釋放配對；無行為改變。
- **檔案**：~L3080–3087。
- **測試**：人工走查 + GDI 物件計數工具前後比較（可選）。
- **相依**：無。**估時 45min**。

### GEO-033 ⚡ 多視窗/多實例安全：`g_edit_orig_proc` 移進 GdiApp
- **內容**：全域 WNDPROC 改成每個 EDIT 用 `SetWindowSubclass`（comctl32）或把原 proc 存 `GWLP_USERDATA`，去掉全域。
- **驗收**：理論上開兩個視窗互不覆寫；單視窗行為不變（Enter 仍送 WM_APP_APPLY_INPUT）。
- **檔案**：~L2653、WM_CREATE ~L2732。
- **測試**：編譯後開視窗按 Enter 驗證指令仍生效。
- **相依**：無。**估時 1h**。

### GEO-034 ⚡ style 快取與 owned 路徑走查 + 註解
- **內容**：`gdi_select_style`/`gdi_release_style`/`gdi_cache_release` 三處的「誰刪誰」規則整理成一張所有權表放註解；並加 `assert`（越界 style 必走 owned）。
- **驗收**：註解表 + assert；AppVerifier/手動走查無洩漏。
- **檔案**：~L2164–2253。
- **測試**：連續 hover 全部 style 後關視窗，用 GDI 物件計數確認無洩漏。
- **相依**：無。**估時 1h**。

### GEO-035 ✅ 已做(2026-09-21) WM_CREATE 控制項建立失敗處理
- **內容**：`CreateWindowW` 三個控制項任一失敗時：status 顯示建立失敗或 graceful 降級（現在 NULL HWND 會繼續往下走，`MoveWindow(NULL,…)` 無害但 status_label=NULL 時 `gdi_set_status` 會對 NULL 呼叫）。
- **驗收**：控制項 NULL 時不當機；主視窗仍可用（僅少輸入列）。
- **檔案**：~L2702–2730、~L2568。
- **測試**：臨時把 class name 打錯模擬失敗。
- **相依**：無。**估時 45min**。⚡

### GEO-036 ⚡ 視窗縮到 0×0 / 最小化的 paint 路徑
- **內容**：`CreateCompatibleBitmap(0,0)` 會失敗已擋；但 `gdi_frame_transform` 在 client 寬高 ≤2·MARGIN 時 scale 可能 ≤0——已檢查 return。補：視窗極小時輸入列 MoveWindow 負座標防禦。
- **驗收**：把視窗拖到最小再還原，無異常、位圖重建正確。
- **檔案**：~L2672–2688、~L2497。
- **測試**：手動極端縮放。
- **相依**：無。**估時 45min**。

---

## 第 4 流：房間（room）功能收尾

### GEO-040 ⚡ room 六面盒範例檔入庫
- **內容**：新增 `room-box.scene`（六面封閉盒 + 一角材），收進 tests/cases。
- **驗收**：exit 0，輸出印「狀態：封閉（六面）」。
- **檔案**：新增 scene + tests 登錄。
- **測試**：GEO-002 跑過。
- **相依**：GEO-002。**估時 45min**。

### GEO-041 ⚡ room 一致性失敗的分類錯誤訊息
- **內容**：`room_bind` 現在只有一條通用訊息；回傳改 enum（面不存在/重複/槽位衝突/區間不一致/界值不吻合/lo≥hi），apply_room_line 各自翻譯。
- **驗收**：六種失敗各有一句可區分的訊息。
- **檔案**：~L3441、~L3958。
- **測試**：tests/cases 造六種失敗各一檔比對訊息。
- **相依**：GEO-002。**估時 1.5h**。

### GEO-042 ⚡ room 宣告與 guides/timbers 的歸屬檢查（警告級）
- **內容**：room 綁定後，檢查「該房的面上建立的 guide/放置的 timber」是否合理（例如 timber 放在房外面上給警告）。先只印 warning 不擋。
- **驗收**：定義「房外面」規則 + 文字報告出警告欄。
- **檔案**：apply_room_line / main 報告段。
- **測試**：故意把 timber 放非 room 面 → 出現警告。
- **相依**：GEO-041。**估時 2h**。

### GEO-043 room 體積/質心推導（報告用）
- **內容**：六面齊全時，由 bound/ext 推出房間尺寸並印「內部空間 W×D×H」。
- **驗收**：六面盒印出 4000×3000×2500。
- **檔案**：room_bind 結果結構 + main 房間段。
- **測試**：_t9 類 scene 看輸出。
- **相依**：GEO-041。**估時 1h**。⚡（與 GEO-042 摸不同段但同函式區，可平行但建議先後）

---

## 第 5 流：文件與導讀同步（RISKS F2/F9）

### GEO-050 ⚡ 修 check_panels.py 的三個失敗 callout
- **內容**：callout match 字串從 `"edge", 4, true,` 改成新表格式 `"edge", 4, 4, true,`；或改寬鬆比對。
- **驗收**：`check_panels.py` exit 0。
- **檔案**：`geometry-guide/current_geometry-導讀.html`（或 make_guide.py 內嵌模板）。
- **測試**：跑 check_panels.py。
- **相依**：無。**估時 30min**。

### GEO-051 重跑 make_guide.py 並補 room 章節 ← GEO-050
- **內容**：重產導讀 HTML；新增 §room：slot 表、區間一致性、內朝法向被拒的例子。
- **驗收**：check_panels 全綠；HTML 含 room 段落且其面板引用行號正確。
- **檔案**：`geometry-guide/make_guide.py`、產出 HTML。
- **測試**：check_panels.py + 肉眼開 HTML 看 room 面板。
- **相依**：GEO-050。**估時 1.5h**。

### GEO-052 ⚡ asm-analysis.md 標示版本或重產
- **內容**：檔頭加「對應 4,327 行版本、room 之前」；或重新 /FAcs 重產附錄函式表。
- **驗收**：讀者一眼知道它對應哪版。
- **檔案**：`asm-analysis.md`。
- **測試**：無（文件）。
- **相依**：無。**估時 30min**（只加標記）/ 2h（重產）。

### GEO-053 檔頭註解更新：功能清單補 room
- **內容**：`current_geometry.c` 頂部「目前整合版」清單加第 9 步（room 綁定）；「第一版限制」區更新（例如現在支援多面/房）。
- **驗收**：註解與實際功能一致。
- **檔案**：~L11–32。
- **測試**：對照 ARCHITECTURE.md §6。
- **相依**：無。**估時 30min**。⚡

---

## 第 6 流：程式碼衛生（RISKS F4/F6/F8）

### GEO-060 ⚡ 清編譯警告
- **內容**：刪 L1440 未使用的 `into`；7 個 `apply_*` 的 `count` 參數——只有 room 用到，其餘 `(void)count;`；重複 `#include <errno.h>` 刪一行。
- **驗收**：`cl /W4` 0 警告。
- **檔案**：~L1、~L1440、各 apply 函式頭。
- **測試**：build.bat 輸出無 warning。
- **相依**：GEO-001。**估時 30min**。

### GEO-061 ⚡ 源檔加 /utf-8 或 BOM
- **內容**：二選一：build.bat 加 `/utf-8`（建議，無侵入）；或源檔存成 UTF-8 BOM。兩者擇一並寫進 README。
- **驗收**：在 BIG5 系統字碼頁機器（或 `chcp 950` + 改碼測）中文輸出不亂碼。
- **檔案**：build.bat 或檔案本身。
- **測試**：`/utf-8` 下編譯，跑 --no-window 看中文。
- **相依**：GEO-001。**估時 30min**。

### GEO-062 emit_svg_three_views 檢查 fprintf 失敗
- **內容**：scene_render 後檢查 `ferror(out)`，失敗則刪除半成品 SVG 並回 false。
- **驗收**：模擬寫入失敗（例如 /dev/full 或唯讀檔）→ 回 false 且無半成品。
- **檔案**：~L1990。
- **測試**：`--out` 指向唯讀位置 → exit 1。
- **相依**：無。**估時 45min**。⚡

### GEO-063 ⚡ StyleSpec.text_mm 更名 text_px（SVG 實際當 px）
- **內容**：欄位更名 + 註解「GDI 端乘 scale 換 px、下限 10px」。
- **驗收**：命名不再誤導；行為不變。
- **檔案**：~L1180–1201、~L2335。
- **測試**：編譯 + 肉眼比對 SVG 字級。
- **相依**：無。**估時 30min**。

---

## 第 7 流：新功能（中張，可依優先序挑做）

### GEO-070 ⚡ `unplace` 指令
- **內容**：`unplace <角材id>`：placed=false、清錨點。注意 anchors 平行陣列對齊。
- **驗收**：unplace 後再 place 到新位置成功；文字輸出不再印該角材面。
- **檔案**：apply_* + SCENE_COMMANDS + main 報告。
- **測試**：scene：place→unplace→place 別處。
- **相依**：GEO-002。**估時 1.5h**。

### GEO-071 `delete` 指令（角材/參考線）← GEO-070
- **內容**：真刪除需搬移陣列元素——會弄亂 ScenePick 索引與 anchors 對齊；評估「墓碑標記」方案（count 不減、跳過未啟用項）。
- **驗收**：設計決定寫進程式；delete 後 id 可重用、索引不指錯。
- **檔案**：world_find_*、scene 走訪、pick。
- **測試**：place 3 支刪中間那支，SVG 剩 2 支。
- **相依**：GEO-070。**估時 2.5h**。

### GEO-072 ⚡ timber 互相碰撞/干涉檢查（警告）
- **內容**：放置時檢查新角材的 AABB 與既有角材的 AABB 是否重疊（全軸對齊所以 AABB 即精確）；重疊 → 警告不擋。
- **驗收**：兩支同位置角材 → 報告印「干涉警告」。
- **檔案**：apply_place_line、Timber 加 AABB 推導或即時算。
- **測試**：兩支疊放 scene。
- **相依**：無。**估時 1.5h**。

### GEO-073 ⚡ `guide` 指令支援以邊為基準（offset-from-edge 語法糖）
- **內容**：`guide id 面id 方向 edge:<邊id> ±d`——寫死 offset 時房間尺寸一改就要手改；以邊為基準的 offset 讓 scene 更有描述力。評估後實作或記錄不做的理由。
- **驗收**：新語法可解析且 offset = 邊位置 ±d；範圍仍由守門員把關。
- **檔案**：apply_guide_line、SCENE_COMMANDS。
- **測試**：scene 用新語法建線，與等價舊語法輸出一致。
- **相依**：GEO-002。**估時 2h**。

### GEO-074 ⚡ place 支援 B0 面接觸（翻面）
- **內容**：現在只能 A0 貼面；加 `face` 欄位（A0/B0）→ B0 貼面時角材 A 尺寸沿法線。評估對 `timber_place_a0_on_surface` 的一般化（place_face_on_surface）。
- **驗收**：B0 放置產出正確六面；向後相容（不寫 face = A0）。
- **檔案**：timber_place_*、apply_place_line、SCENE_COMMANDS（欄位數變，注意舊檔相容）。
- **測試**：同一 anchor 分別 A0/B0 貼，六面頂點人工核對。
- **相依**：GEO-002。**估時 2.5h**。

### GEO-075 ✅ 已做(2026-09-21) 文字輸出加「房間內部尺寸」與角材下料清單
- **內容**：cut list：每支角材 L×A×B + 所屬面 + 錨點；加總同規格數量。實用化第一步。
- **驗收**：room_a 輸出含「角材 1：1800×27×33 ×1」。
- **檔案**：main 報告段。
- **測試**：兩支同規格角材 → 數量 ×2。
- **實作**:`print_cut_list()` 依 (長度, 斷面 A, 斷面 B, 角色) 分組加總,印在逐支細節之後
  (總表是結論,放結尾才不會被幾十行座標沖掉)。排序固定為「長料先切」——長度遞減,
  同長度再依斷面與角色,**同一份場景永遠得到逐字相同的清單**(清單要能拿去比對)。
  未放置的角材不入清單。
- **刻意不用「L=」字樣**:`tests/run_tests.py` 的 `LEN_RE = r"L=(\d+)"` 會把輸出裡每個 `L=`
  都當成一支角材的長度,清單若沿用它會污染既有 128 個測試的長度比對。改用 `4000x20x20` 格式。
- **房間內部尺寸**:只印**兩側槽位都有面**的軸,用 `space_axis_bound()` 各查一次;
  推不出來的軸不猜、不補預設(R3)。
- **實測**:
  - `room_a`(3 支 2 規格):`4000x20x20 boundary x2（角材 90、91）` /
    `2960x27x33 primary x1（角材 1）` / `合計 3 支,2 種規格,總長 10960 mm`
    —— 驗收要求的「兩支同規格 → ×2」成立。
  - `_demo_ceiling`(7 支 3 規格):`合計 7 支,3 種規格,總長 20957 mm`。
  - `_rc_col_corner`(封閉六面):內部尺寸 X 4000 / Y 3000 / Z 2500。
  - `_ax_r16_top_drop`(top_drop 後 Y 軸少一面):**只印 X 與 Z,Y 不印**——R3 不猜。
  - `room_box`(只有 2 面):三軸都印不出來,整段不出現。
- **驗收已進測試**:`run_tests.py` 對上述三個場景加了 `contains` / `not_contains`;128/128 通過,
  `test_core_integrity` 80/80 通過。
- **相依**：無。**估時 1h**。

### GEO-076 ⚡ GDI 視窗顯示游標所在 mm 座標
- **內容**：status 列左側即時顯示 `view mm (x,y)` 與反解成功的 `(u,v)`。
- **驗收**：滑鼠移動時狀態列即時更新。
- **檔案**：WM_MOUSEMOVE、gdi_set_status。
- **測試**：手動。
- **相依**：GEO-020。**估時 1h**。

### GEO-077 ⚡ 場景檔 `include` 或分段
- **內容**：`include <相對路徑>` 引入共用片段（如標準房）；注意遞迴深度上限（≤8）與 line_no 報告。
- **驗收**：include 檔的錯誤報「檔名:行號」正確；循環 include 被拒。
- **檔案**：parse_scene_file（抽成可重入 + 堆疊）。
- **測試**：include 一個壞檔 → 錯誤定位正確。
- **相依**：GEO-002。**估時 2.5h**。

### GEO-078 ⚡ JSON 輸出（--emit-json）
- **內容**：場景幾何（面/邊/線/房/角材六面頂點）以 JSON 輸出，供外部工具（SketchUp 插件！）消費。手写 printf 即可，不引 library。
- **驗收**：輸出可被 python `json.loads` 解析；與文字輸出數值一致。
- **檔案**：新增 emit_json.c 段落 + main。
- **測試**：python 解析 + 抽樣對數值。
- **相依**：無。**估時 2h**。

---

## 第 8 流：結構演化（大張拆分前的準備，皆 ≤3h）

### GEO-080 ⚡ 抽出純幾何核心為可單元測試標的
- **內容**：把 §1–§5（型別+向量+表面+邊+線+角材）用 `#ifdef` 或拆檔方式讓一個 `test_geometry.c` 能 `#include` 進來直接呼叫 static 函式；先不切檔，只建立測試入口。
- **驗收**：`test_geometry.c` 能直接呼 `surface_point_to_room` 等，10 個斷言全過。
- **檔案**：新增 `tests/test_geometry.c`、current_geometry.c 加 `#ifndef CG_NO_MAIN`。
- **測試**：自建 main 跑斷言。
- **相依**：GEO-001。**估時 2h**。

### GEO-081 scene parser fuzz 測試 ← GEO-080
- **內容**：python 產生隨機 token 行 + 隨機截斷，跑 10k 次；exit code 只能是 0/1，不得 crash（Windows 下看 exit code 是否 0xC0000xxx）。
- **驗收**：10k 次無 crash；所有失敗都有 stderr 訊息。
- **檔案**：新增 tests/fuzz_scene.py。
- **測試**：跑一遍。
- **相依**：GEO-001、GEO-002。**估時 2h**。

### GEO-082 ⚡ 把 110+ 函式單檔拆成 geometry.c/view.c/scene_io.c/gdi_main.c 的計畫
- **內容**：只產出拆分計畫文件（不動手）：依賴圖、每檔公開介面、static→extern 清單。
- **驗收**：計畫經 review 後才動手；本工單只交文件。
- **檔案**：新增 docs/split-plan.md。
- **測試**：無。
- **相依**：GEO-080。**估時 2h**。

### GEO-083 ⚡ /analyze 與 /RTC1 納入建置
- **內容**：build.bat 加 `build_analyze.bat`（cl /analyze）與 debug 的 /RTC1；把「0 警告」列為完成定義。
- **驗收**：analyze 0 警告（現存 C28199/C6387 由 GEO-014/030 消）。
- **檔案**：build 腳本。
- **測試**：跑 analyze。
- **相依**：GEO-001、GEO-014、GEO-030。**估時 45min**。

---

## 工單統計

- 總數：**46 張**（GEO-001~004、010~018、020~026、030~036、040~043、050~053、060~063、070~078、080~083）
- 估時 30min：GEO-003、014、015、016、017、030、031、050、052(標記)、053、060、061、063
- 估時 45min~1h：GEO-001、004、010、012、013、020、021、022、023、024、026、032、033、034、035、036、040、043、062、075、076、083
- 估時 1.5h~3h：GEO-002、011、018、025、041、042、051、052(重產)、070、071、072、073、074、077、078、080、081、082

## 建議施工順序

1. **第一梯（全平行 ⚡）**：GEO-001、003、015、016、017、050、052、053、060、061、030、031 — 全部是獨立小修，清掉現有警告與壞檔。
2. **第二梯**：GEO-002（測試腳本）→ 之後所有改動都有安全網。
3. **第三梯（全平行 ⚡）**：GEO-010、012/013、014、020、021、022、023、024、026、032~036、040、041、062、063、075、076、078。
4. **第四梯（有相依）**：GEO-011←010、042/043←041、051←050、070→071、081←080。
5. **功能擴充**（GEO-072~078）與 **結構演化**（GEO-080~083）可依優先序插單。

---

## 變異測試（tests/mutate.py,40 個變異,2026-09 執行）

**結果**:36 殺死 / 4 存活(全部定讞為等效變異)/ 0 無效。
流程:`python tests/mutate.py` → 單點替換 → `_cl.bat` 編譯 → `run_tests.py` 全量(39 場景)。

### 等效變異定讞(任何測試都殺不死,公理結構保證)

| 變異 | 位置 | 等效理由 |
|---|---|---|
| M01 | `poly_point_on_edge` 直立邊端點含→嚴格 | 頂點恆為一條直立邊+一條水平邊的共同端點;水平邊分支的 u 範圍檢查未變異,仍接住所有頂點 |
| M09 | `boundary_contains_rect` 孔 bbox 相接當相交 | bbox 僅相接才進深層檢查,但頂點嚴格/邊穿入/罩住三檢查對純接觸全數放行 |
| M10 | 孔頂點嚴格在矩形內→含邊界 | 頂點在矩形邊上 ⇒ 該軸 bbox 必為相接 ⇒ 前置 bbox 快退已 `continue`,變異行不可達 |
| M23 | `pick_stop` 起點歧義(hits>1)放行 | 同座標兩面都涵蓋全寬 ⇒ 面所有者必撞掉逼近 cell(面積重疊)或邊界自體不合法(孔貼輪廓/孔孔相切)→ 結構不可達 |

### 本輪新增殺手場景(8 個)

`_mut_notch_straddle`(M08)、`_mut_reval_free_hole`(M18+M36)、
`_mut_through_boundary`(M19)、`_mut_free_hole_end`(M22)、
`_mut_edge_touch_only`(M24)、`_mut_grid_dup`(M31)、
`_mut_zero_len`(M35)、`_mut_neg_hole_ref`(M38)。

### 遺留觀察(非變異,未來可加強)

- 端面 FREE 檢查在兩處各自實作(放置路徑查外輪廓、auto span 查全部含孔);M22 能活下來正是因為放置路徑不查孔邊——若未來把孔邊 FREE 檢查也加進放置路徑,M22 會變等效。可考慮統一成單一公理實作點。
- 變異覆蓋的是「已枚舉的 40 點」;`collect_stop_faces` 的孔邊枚舉、`anchor_corner_from_rect` 的深度側、`grid` 下界檢查(M32 對側)等鄰近行尚未配對變異,後續可擴表。

---

## UI 重構衍生的 C 端工單候選(geometry-web Phase 1-5,2026-09-13)

> 來源:`geometry-web/docs/UI-REDESIGN-PLAN.md` §9 決策佇列 + 實作期間發現的 bridge 缺口。
> 這批全部屬 C 端(current_geometry.c / web_bridge.c)工單,UI 端已按「沒有就不做」處理。

### WEB-001 ✅ 已完成(2026-09-13,Q1 拍板做) `delete <kind> <id>`
- **內容**:刪除邊界面 / 參考線 / 空間成員關係,走既有交易重驗路徑。目前 UI 無法刪除任何物件,只能靠 undo。
- **驗收**:`delete boundary <id>` 後 `objects` 面數 -1;被刪面若為某空間成員,該空間 `closed` 正確重算;失敗(依他物引用)時回滾。
- **檔案**:`current_geometry.c`(指令表 + 交易)、`web_bridge.c`。
- **測試**:連續 delete + undo/redo 混合;刪除承載面後再 `render` 不殘留。
- **相依**:無。**估時 1.5h**。

### WEB-002 新增 `guides <sid>` 列舉指令
- **內容**:回傳指定承載面上的參考線(id/軸/offset)。目前 UI 只能 parse `dump` 文本的 `^guide` 行,脆弱且繞路。
  Q3 後 timber/place/grid 也走同一路徑解析——若做本單,建議擴成 `refs <sid>` 一次回傳 guides+timbers+grids。
- **驗收**:JSON 輸出 `{"ok":true,"guides":[{"id":..,"surface":..,"axis":"u","offset":..}]}`;空面回空陣列非錯誤。
- **檔案**:`web_bridge.c`(指令表)。
- **測試**:建 guide → 列舉 → move → 再列舉。
- **相依**:無。**估時 45min**。⚡ 與 WEB-001 平行。

### WEB-003 🔶 部分完成(2026-09-14,RC Phase 6) 邊界面/參考線數量上限檢討(§9 Q1 附帶)
- **進度**:`WORLD_MAX_BOUNDARIES/PLACEMENTS` 8→16(commit ce02a80)——條帶裁切需 +4 面;兩間六面盒(12 面)現可共存。動態化/再加大仍開放。
- **內容**:`WORLD_MAX_BOUNDARIES = 8` 偏小——六面盒一間房就用掉 6 個;測試中多物件場景易撞界。評估提到 32/64 或改動態配置。
- **驗收**:同時建立兩間六面盒(12 面)不報「邊界面的數量超過上限」。
- **檔案**:`current_geometry.c` 常數定義區。
- **測試**:回歸全綠 + 新增 12 面場景。
- **相依**:無。**估時 1h**(若動態化另估)。

### WEB-004 ✅ 已由前端實作(Q2,commit 69f59fe) 正交頂點插入
- **結果**:核心公理拒絕共線頂點,正確原語是「矩形凹口(4 頂點)」;已於面內工具實作——點邊自動插凹口,走既有 `boundary` 重宣告交易,核心再驗。C 端原語不再必要,留檔備查。
- **驗收**:在邊中段插入合法凹口後 `boundary` 指令重驗通過;非法位置(撞孔/越界)回錯誤不落地。
- **檔案**:`current_geometry.c`。
- **測試**:四邊各插一次 + 撞孔案例 + undo。
- **相依**:無。**估時 2h**。

---

## 第 9 流：構件層級（公理層 D15–D17、I18–I22、R18–R20；2026-09-15 立）

> 來源：TimberScript Core Charter §2a 與拍板清單，形式化為「層級是段的性質」（D16）。
> 工單順序即依賴順序；每張都以公理層條文為驗收基準，條文與實作不一致時**改實作**。

### GEO-090 ⚡ `timber` 加 `role` 子句 + 場景檔遷移
- **內容**：`apply_timber_line` 解析 `role boundary|primary|secondary|custom [priority N]`（D15）；`Timber` 加 `role`/`cut_priority` 欄位；`world_dump_dsl` 輸出；沒 role / custom 沒 priority / priority 配非 custom → 拒絕（I18）。所有 `*.scene` 夾具與 web 六面盒模板、canvas_test/cdp_test 內嵌的 `timber` 行全部補角色。
- **驗收**：舊夾具不補角色時 parse 拒絕且訊息指名行號；補完後 dump→loadfile→dump 逐字相同；`newid`/`objects`/`delete` 不受影響。
- **檔案**：`current_geometry.c`（apply_timber_line 7640、dump 8316 附近）、`geometry-web/web_bridge.c`、`*.scene`、`geometry-web/app.js` 角材表單。
- **測試**：canvas_test 加「無 role 拒絕」「custom 無 priority 拒絕」「dump round-trip」。
- **相依**：無。**估時 2h**。

### GEO-091 主支軸一致（D17、I21）
- **內容**：`world_revalidate` 與 `apply_place_line` 內推導承載面主支軸（全部 primary 長度軸唯一；無 primary 時取 boundary 的垂直方向）；boundary/secondary 與主支軸平行 → `V_PRIMARY_AXIS`。
- **驗收**：同面第二支 primary 換軸 → 拒絕；先放 boundary 再放與它平行的 primary → 拒絕；刪掉唯一 primary 後軸由 boundary 推得。
- **檔案**：`current_geometry.c`。
- **測試**：夾具 `_role_axis_*.scene` 三個 + canvas_test。
- **相依**：GEO-090。**估時 1.5h**。

### GEO-092 端面優先序與延伸段（I19、I22）
- **內容**：`resolve_auto_span`（6436）與明寫放置的端面檢查：每個端面所頂擋面的擁有者優先級必須 < 自己（外輪廓/孔邊/柱面 = 0；轉角兩支 boundary 互頂例外）；違反 → `V_CUT_PRIORITY`。boundary 的固定段/延伸段切分（D16）：延伸段端面豁免 I19；延伸段側面作擋面時以優先級 2 計；非 boundary 角材不得有超出定位邊的段。
- **驗收**：主支端面頂 RC → 拒絕；副支端面頂 RC → 拒絕；主支端面頂副支側面 → 拒絕；L 形內邊 boundary 延伸過凹角停在長主支側面 → 接受且長主支 footprint 不變；同一支延伸段被主支端面頂 → 拒絕、被副支頂 → 接受；凸角處延伸 → 因 I5 出界拒絕（不需新錯誤碼）。
- **檔案**：`current_geometry.c`（collect_stop_faces 6244、resolve_auto_span 6436、apply_place_line 7979）。
- **測試**：夾具 `_role_priority_*.scene` 六個（對應上列驗收）+ 變異殺手（把 boundary 改 primary 必須被拒）。
- **相依**：GEO-090、GEO-091。**估時 3h**。

### GEO-093 邊界材整條覆蓋 + 角色衍生屬性（I20、R18）
- **內容**：R18 的 `onBoundary` / `coversEdge` / `boundaryEdge` 純幾何推導（只看外輪廓、不看孔邊、不看錨法）；I20：boundary 的固定段 ⊇ 邊區間、邊為 FIXED 外輪廓邊且 ⊥ 主支軸，否則 `V_BOUNDARY_ROLE`（訊息含料件、邊索引、覆蓋長度/邊長）；secondary 必 onBoundary=false。bridge `objects` 的 timbers 與 `dump` 註解一併輸出三個屬性。
- **驗收**：用 `through` 貼齊邊的料 onBoundary=true；at-edge 放卻被裁短的料 coversEdge=false 且若宣告 boundary → 拒絕；孔邊上的料 onBoundary=false；`objects` 回傳欄位存在。
- **檔案**：`current_geometry.c`、`web_bridge.c`。
- **測試**：夾具 `_role_cover_*.scene` 四個 + canvas_test 讀 objects 欄位。
- **相依**：GEO-092。**估時 2.5h**。

### GEO-094 連坐重驗（R20）+ 變異測試
- **內容**：刪除/移動/重宣告任一角材後同面全部角材重驗 I19–I22 與 R18，任一不過整筆回滾。補變異測試 M41–M50：各拿掉一條不變量的檢查，對應殺手夾具必須能抓到。
- **驗收**：刪掉被延伸段頂住的長主支 → 延伸段失去擋面 → 整筆拒絕（不留半成品）；`_run_tests_cmd.py` 全綠。
- **檔案**：`current_geometry.c`、`tests/`。
- **測試**：如上。
- **相依**：GEO-093。**估時 2h**。

### GEO-095 web UI：角色與層級可見
- **內容**：面內「角材」分頁的表單加角色選單（預設 primary；custom 顯示 priority 欄）；面內圖層列與卡片顯示角色徽章與 onBoundary/coversEdge；`V_CUT_PRIORITY`/`V_BOUNDARY_ROLE`/`V_PRIMARY_AXIS` 的 toast 原文顯示並高亮相關兩支料；DOM-CONTRACT 補新 id。
- **驗收**：cdp_test 新段：放 boundary→primary→secondary 各一支成功；放與主支軸平行的 boundary → toast 且畫面高亮；L 形延伸案例在 UI 內可完成。
- **檔案**：`geometry-web/app.js`、`app.css`、`index.html`、`cdp_test.js`、`docs/DOM-CONTRACT.md`。
- **測試**：cdp_test。
- **相依**：GEO-093。**估時 2.5h**。

### GEO-096 ⚡ 導讀與文件同步
- **內容**：`make_guide.py` 補「構件層級」章節（D15–D17、I18–I22、R18–R20 對應原始碼面板）、重跑、`check_panels.py` 全過；`geometry-model-v2.md` 補一節說明與 TimberScript Charter 的對應與差異（段框架取代延伸例外）。
- **驗收**：check_panels unresolved: none；導讀頁能點到 `apply_timber_line` 的 role 解析與 `V_CUT_PRIORITY` 判定處。
- **檔案**：`geometry-guide/make_guide.py`、`geometry-model-v2.md`。
- **相依**：GEO-090～094。**估時 1.5h**。

---

## 第 10 流：網格來源化與面材推導（公理層 D10、D10a、D18、I10、I13、I23、R6(c)、R13、R21；2026-09-16 立）

> 來源：timberscript-studio Core 的 `reference_grid` 模型（14 golden 簽核），形式化為「起算點具體化」（D10a）與「between 只買走唯一性、不買走物理條件」（R21）。
> 公理層條文已於 2026-09-16 開工前落版（改版前備份 `公理層.md.bak-geo097`）；工單順序即依賴順序，每張都以公理層條文為驗收基準，條文與實作不一致時**改實作**。
> 使用者拍板的八項決定見 `~/.claude/plans/linked-frolicking-hennessy.md`；其中三項最容易被誤改：**只存來源不存展開值**、**不引入 heap 配置**、**gap 奇數拒絕不取下取整**。
> 變異 id 從 **M51** 起（M41–M50 已由未完成的 GEO-094 預留）。
> **收流關卡**：本流全部完成後必須跑一次完整 40+ 個變異（`python tests/mutate.py` 不帶參數），
> 因為只跑子集會覆寫 `tests/mutants_results.json`；GEO-097 當下是先跑 M31–M33，再把結果併回備份 `tests/mutants_results.json.bak-geo097`。

### GEO-097 ⚡ `ReferenceGrid` 來源化重構（純重構，行為不變）
- **內容**：`ReferenceGrid` 改成 `GridAxisDef axis[2]`（1285），新增 `GridSource` 列舉（NONE / EXPLICIT / SERIES / PANEL）；`GRID_MAX_LINES` 32→64；新增唯一展開入口 `grid_axis_lines` 與薄包裝 `grid_line_coord`，本票只實作 EXPLICIT 分支；`grid_is_valid`（1306）改成迴圈跑兩軸、外接區間檢查移進 `grid_axis_lines`；`apply_grid_line`（8486）、`apply_place_line` 的 at-grid 分支（8800）、`world_dump_dsl`（11121）改用新欄位；死程式碼 `world_find_grid`（8384）復活並補 `world_find_grid_mut`，取代 8526／8802／10820 三處 inline 迴圈。
- **驗收**：`python _run_tests_cmd.py` 全綠且**輸出逐字不變**；`python tests/mutate.py M31 M32 M33` 仍 killed；dump→loadfile→dump 逐字相同；明寫 65 條座標 → reject「超過單軸上限」（現況 33 條的拒絕路徑無測試，本票補上）。
- **檔案**：`current_geometry.c`（1270-1348、8384-8393、8486-8643、8800-8838、10820、11121-11140）。
- **測試**：`_edge_grid_overflow.scene` 一筆進 `TESTS`；其餘靠既有夾具回歸。
- **相依**：無。**估時 3h**。

> **GEO-097 完成紀錄（2026-09-16，尚未 commit）**
> 關卡:編譯無警告;`_run_tests_cmd.py` 61/61,既有 60 筆與改版前**逐字相同**;
> 變異 M31/M32/M33 全 killed、0 invalid（M32 錨點已從 `grid_is_valid` 搬到
> `grid_axis_lines` 的 `if (out[k] < lo || out[k] > hi)`，確認全檔唯一）;
> 27 個 accept 夾具的 `dump` 輸出新舊**逐字相同**;`check_panels.py` 40 panels / unresolved: none。
> **記憶體實測**（不是估算）:`sizeof(ReferenceGrid)` 536 → **1176** bytes、
> `sizeof(World)` 121608 → **126728** bytes（+5120，+4.2%）。
> World 有 65 份靜態快照（`g_hist_undo[32]` + `g_hist_redo[32]` + group base）→ BSS 約 **+325 KB**;
> `World backup = *world;` 兩處是函式區域變數，單一呼叫框架約佔 **124 KB** 堆疊
> （改版前已是 119 KB，非新增的風險類別，但 GEO-106 若把 `WORLD_MAX_GRIDS` 提到 16 要重算）。
> **複驗提出的兩點觀察（非 FAIL，留給後續票）**:
> (1) `grid_line_coord` 取索引前會重跑 `grid_axis_lines`，連帶重驗 I10;舊版 at-grid 只比對
>     `u_count/v_count`，不重驗座標合法性。這是**刻意收緊**、且與 GEO-099 的 I23(b) 同向，
>     但目前 DSL 路徑不可達，GEO-099 應補一條回歸測試把它釘住。
> (2) 全檔無 `World` 的 `fwrite/fread` 或固定位元組序列化假設，歷史快照與 memmove 都用
>     `sizeof(World)` 動態算，容量放大不會打到任何序列化契約。

### GEO-098 `series` 來源（等差簡寫）
- **內容**：`apply_grid_line` 軸段解析加分派——`u`／`v` 後第一個 token 是 `series` 則吃 `start step count`（座標一定過 `parse_i64`、`series` 過不了，故無歧義）；`grid_axis_lines` 的 SERIES 分支（第 k 條 = start + k·step）；`step ≤ 0`／`count == 0`／任一條出界 → 拒絕；`world_dump_dsl` 輸出 `u series <start> <step> <count>`；`SCENE_COMMANDS` 的 grid 列（11390）usage 更新。
- **驗收**：`grid 1 on 1 u series 1000 2000 2` 與 `grid 1 on 1 u 1000 3000` 推出相同格線、相同角材長度（`lengths` 逐一相同）；dump 輸出 series 形式且重放逐字相同；`step 0`／`count 0`／尾端出界三種 reject 且訊息可辨。
- **檔案**：`current_geometry.c`。
- **測試**：`_test_grid_series.scene`（對照 `_edge_grid_twoline.scene`）、`_edge_grid_series_out.scene`、`_edge_grid_series_step0.scene`。
- **相依**：GEO-097。**估時 2h**。

> **GEO-098 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 65/65;`_test_grid_series.scene` 推出的長度 `[4000, 4000, 2960, 2960, 1973]`
> 與明寫版 `_edge_grid_twoline.scene` **逐一相同**，等價性成立;
> dump 輸出的是來源形式 `grid 1 on 1 u series 1000 2000 2`（不是展開座標），往返逐字相同;
> `check_panels.py` unresolved: none。

### GEO-099 ⚡ grid 交易化 + I23 網格引用鎖
- **內容**：`apply_grid_line` 回寫路徑改走交易——既有槽位用 `world_replace_object`（7258），新增槽位用 `World backup` + `world_revalidate`；移除 8584-8591 的「同軸一律不可重宣告」，改成 I23(a) 守門：對每個 `anchors[i].ref_grid == id && ref_grid_axis == axis` 的已放角材，用**舊定義**與**候選定義**各推一次該索引座標，不相等或候選推不出來 → `V_GRID_LOCKED`；`world_revalidate` 的角材迴圈加 I23(b)；`delete grid` 守門（10827）訊息統一成 `V_GRID_LOCKED`。
- **驗收**：往既有明寫軸追加格線 → accept；改動已錨定索引的座標 → reject `V_GRID_LOCKED`；錨在 u 軸後仍可補 v 軸 → accept；重宣告使某條被錨定的線消失 → 整筆回滾且 `dump` 與先前逐字相同；`_edge_grid_twoline.scene` 仍 accept 且 lengths 不變。
- **檔案**：`current_geometry.c`（8486-8643、7286-7330、10817-10837）。
- **測試**：`_test_grid_redeclare.scene`、`_edge_grid_locked.scene`、`_edge_grid_locked_other_axis.scene`、`_mut_grid_locked.scene`。變異加 **M51**（I23(a) 的座標比對拿掉）、**M52**（grid 回寫不呼叫 `world_revalidate`）。
- **相依**：GEO-097，可與 GEO-098 平行。**估時 3h**。

> **GEO-099 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 70/70;27 個 accept 夾具往返通過 30 筆、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M31/M32/M33/M51/M52 全部取得**真實死因**
> （M51 由 `_edge_grid_locked.scene` 的「應拒絕但接受」抓到，正是設計的殺手）。
> 合併後變異紀錄 42 個:38 殺 / 4 個既知等效存活 / 0 無效。
> **實作偏離規劃的一點**：`world_find_grid` 在 `world_revalidate`(7504) 被用到、
> 卻定義在 8557，補了一行前向宣告。
> **已知覆蓋缺口**：I23(b)（重驗時索引必須仍推導得出）目前**沒有殺手夾具**——
> EXPLICIT/SERIES 的條數是固定的，承載面一縮小 `grid_is_valid` 就先拒了，
> I23(b) 抓不到任何它抓得到的東西。要等 GEO-100 的 PANEL 來源落地
> （條數隨面大小變動）才變得可達，**GEO-100 必須補這條殺手**。
> **驗證環境警告**：跑變異時務必確認死因不是「例外 [WinError 4551]」——
> 那是 SAC 擋掉 `_mut.exe` 的假死，見 GEO-108。

### GEO-100 面材推導 PANEL_LAYOUT 對縫（D10a）
- **內容**：`GridAxisDef` 的 panel／gap／anchor 三欄；解析 `panel <p> gap <g> [from <c>]`，**anchor 宣告當下具體化**（未寫 `from` 取當下 `placement_local_bounds` 的該軸下界）並寫進定義；`grid_axis_lines` 的 PANEL 分支照 D10a 直譯（`c_k = a + k·T + panel + gap/2`，產生條件 `a+(k+1)·T < hi`）；gap 奇數／panel ≤ 0／gap < 0／anchor 出界／超上限各自的人話訊息；dump 輸出 `u panel P gap G [from A]`（`from` 只在 `anchor_explicit` 時輸出）；**`geometry-web/app.js:2252-2256` 的 `^grid` regex 收緊成只吃純數字串**，認不得的來源型式忽略不畫（停損，見流末）。
- **驗收**：3600×3000 面、`u panel 400 gap 20` → **恰 8 條線：410 / 830 / 1250 / 1670 / 2090 / 2510 / 2930 / 3350**；在 index 0 與 index 7 放 auto 主支，長度與明寫等價場景一致；`gap 21` → reject「縫寬必須為偶數」；`panel 1 gap 0` 於 4000 面 → reject「超過單軸上限」；面寬 300 小於 panel 400 → accept 且該軸零條線，此時 at-grid index 0 → reject「本軸共 0 條」；dump 重放逐字相同；web 面內編輯器載入 PANEL 場景不畫出錯誤格線。
- **檔案**：`current_geometry.c`、`geometry-web/app.js`（一行 regex）。
- **測試**：`_test_grid_panel.scene`、`_edge_grid_panel_odd_gap.scene`、`_edge_grid_panel_overflow.scene`、`_edge_grid_panel_empty.scene`、`_edge_grid_panel_from.scene`（L 形面 + 明寫 from）、`_mut_grid_panel_center.scene`。變異加 **M53**（中心線改成縫起點）、**M54**（產生條件 `< hi` 改 `<= hi`）、**M55**（gap 奇數改放行取下取整）。
- **相依**：GEO-099。**估時 4h**。

> **GEO-100 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 79/79;33 個 accept 夾具往返通過、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M53/M54/M55 全部取得真實死因。
> **公式已由實測釘住**（不是估算）:3600 寬的面配 `panel 400 gap 20` →
> 恰 8 條線，index 0 的中線 **410**、index 7 的中線 **3350**
> （角材原點 424 與 3364 減去半寬 14）；index 8 被拒且訊息寫「本軸共 8 條」。
> `from 1000` → index 0 的中線 **1410**（原點 1424），起算點具體化語意成立。
> **偏離規劃的一點**：規劃寫「`from` 只在 anchor_explicit 時輸出」，實作改成**一律輸出**。
> 理由:起算點已具體化進定義（D10a），省略它的話，承載面事後縮小時重放會取到不同的 a，
> R4 的「重放逐字相同」就破了。
> **覆蓋缺口（誠實記錄）**：I23(b) 仍**沒有隔離殺手**，變異 **M56 存活**。
> 原因不是它等效，而是構造不出「線消失但所有角材都還在面內」的場景——
> 被錨定的主支必須靠沿 u 的邊界材提供擋面（主支不得直接頂外輪廓，見 GEO-109），
> 而那些邊界材必然橫跨全寬，面一縮就先出界（I5）觸發回滾。
> `_edge_grid_panel_shrink.scene` 保留為「縮面整筆回滾」的回歸測試，但它擋的是邊界材出界。
> 若 GEO-109 放寬「只有 boundary 可頂 RC」，這個殺手就做得出來。

### GEO-101 ⚡ `between(face, face)` 明寫兩端（D18、R21）
- **內容**：`StopFaceRef` 型別與解析（**重用 `parse_edge_ref` 8399**，只多一個 `t<id>` 分支）；`apply_place_line` 選擇器區（8886）加 `between` 分支，與 `through` 互斥；`resolve_auto_span`（6895）加 `const StopFaceRef *between` 參數，在選區間（7050）與兩端擋面檢查（7083）插入 R21(b)(c)(d) 的指名路徑——改用 `pick_stop` 的**條件**去驗被指名的那一面，而不是數有幾面；`SpanStatus`（6864）尾端追加 `SPAN_BETWEEN_BLOCKED`、`SPAN_BETWEEN_AMBIGUOUS`；`SCENE_COMMANDS` 的 `place` max_fields 12→**13**（11401）。
- **⚠ 連動**：`geometry-guide/make_guide.py:574` 的 callout `"place", 8, 12, true,` 必須同步改 13，否則 `check_panels.py` 會 unresolved（已實測確認）。
- **驗收**：`_edge_stop_ambiguous.scene` 的歧義場景改用 between → accept 且長度等於明寫值；between 指到 FREE 邊 → reject；兩端之間被已放角材擋住 → reject；`between t5 t9` 有兩組合法配對 → reject 並列舉全部候選；through 與 between 同寫 → reject；I19 違規的 between（主支端面頂 RC 邊）仍 reject `V_CUT_PRIORITY`；`check_panels.py` exit 0。
- **檔案**：`current_geometry.c`（6864-6875、6895-7125、8399-8444、8886-8896、11401-11406）、`geometry-guide/make_guide.py`。
- **測試**：`_test_between.scene`、`_edge_between_free.scene`、`_edge_between_blocked.scene`、`_edge_between_ambiguous.scene`、`_edge_between_conflict.scene`、`_role_between_priority.scene`。變異加 **M56**（between 跳過 FREE 邊檢查）、**M57**（between 跳過逐 cell 合法性）。
- **相依**：GEO-097（不依賴 PANEL，可與 GEO-100 平行）。**估時 4h**。

> **GEO-101 完成紀錄（2026-09-16，尚未 commit）**
> `_run_tests_cmd.py` 85/85;34 個 accept 夾具往返通過、0 筆前後不同;
> `check_panels.py` unresolved: none;變異 M57/M58 全部取得真實死因。
> **等價性已釘住**：`_test_between.scene` 與 `_edge_stop_ambiguous.scene` 是同一個幾何，
> 副支改用 `between t1 t5` 之後長度 `[1000, 1960, 3000, 2000, 3946]` **逐一相同**——
> between 只換寫法、不換結果。
> **偏離規劃的三點**：
> (1) `place` 的欄位數不是 12→13 而是 12→**15**。at-grid 帶 between 是 13 欄，
>     但要讓「through 與 between 同時寫」講得出互斥訊息（而不是被籠統的欄位數錯誤蓋掉），
>     表上限必須放到 15;at-grid／at-edge 兩個分支各自的 count 檢查也一併放寬。
>     `make_guide.py` 的 `"place", 8, 12, true,` callout 已同步成 15。
> (2) R21(e) 的夾具原本想用 primary，但 D17 的主支軸一致（I21）會先擋下，
>     改用 `custom priority 2`——D15 明寫 custom 不取得任何角色專屬義務，
>     所以 D17 不管它，能單獨把 I19 逼出來。
> (3) 規劃寫「`between t5 t9` 有兩組合法配對 → reject 並列舉」。實作與條文都照做了，
>     但**這條路徑目前不可達**：被指名的角材側面必須涵蓋端面全寬（R21(a)），
>     代表那支角材的本體橫跨中線，於是只有「兩支之間」那一組配對落得進合法區間。
>     變異 M58（拿掉區間檢查）的死因輸出可以看到 4 組候選被收斂成唯一的 [1020,2980]，
>     證明列舉邏輯會動。這是 R21(d) 要求的防禦性分支，保留但無夾具。

### GEO-102 ⚡ 導讀與文件同步（公理層已先落版）
- **內容**：`公理層.md` 已於 2026-09-16 開工前落版，本票不再改它，只做下游同步——`geometry-model-v2.md` 補一節說明與 timberscript-studio `reference_grid` 模型的對應與差異；`make_guide.py` 補「網格來源化」章節（`GridAxisDef`／`grid_axis_lines`／D10a 公式三個面板）並重跑；`current_geometry.c:6833-6836` 那段「未經授權不得修改公理層」的註解改成指向已修正的 I22 條文。
- **驗收**：`check_panels.py` unresolved: none 且 exit 0；導讀頁能點到 `grid_axis_lines` 的 PANEL 迴圈與 `V_GRID_LOCKED` 判定處；公理層每一條新條文都能在 `TESTS` 找到至少一筆對應夾具（對照表附在本票下方）。
- **檔案**：`geometry-guide/make_guide.py`、`geometry-model-v2.md`、`current_geometry.c`（註解）。
- **相依**：GEO-097～101。**估時 2.5h**。

### GEO-103 RUNNING_BOND 交丁排法（phases、row）— 第 2 期，條文未定案前不得實作
- **架構**：`GridAxisDef` 加 bond／phases／phase_count（`GRID_MAX_PHASES 8`）。交丁必須明寫 phases（不猜）；軸 X 宣告 RUNNING_BOND 時，垂直軸 Y 必須也是 PANEL_LAYOUT——「排」就是 Y 軸的面材本體 band。第 r 排的 X 軸格線 = `c_k + phases[r % phase_count]`。主方向無貫穿線，故 `at-grid` 不帶 `row` → 拒絕；帶 `row n` 時除了給中線，**同時給跨距的接觸範圍**（第 n 排在 Y 軸的 band 區間），直接餵進 `resolve_auto_span` 既有的 `has_contact／contact_lo／contact_hi` 參數——逐排縫段因此從 R6 自動掉出來，不需要新的幾何機器。
- **擬立條文**：D10b、I24、R22。
- **驗收方向**：兩相位交丁，第 0 排與第 1 排的同索引格線相差半週期；不帶 row 放置 → reject；row 超出排數 → reject；裁短片所在排的格線條數比完整排少。
- **相依**：GEO-100。**估時 6h**（含條文）。

### GEO-104 `support_step` 板縫落骨約束 — 第 2 期
- **架構**：宣告式約束，在 grid 宣告當下檢查。支撐線 = `lo + j·(span／n)`；`span % n != 0` → 拒絕；每條縫中心線必須與某條支撐線重合，否則拒絕。與 D10a 推導解耦：先推縫、再驗落骨。
- **⚠ 開工前需拍板**：「縫中心與支撐線座標相等」是直譯，實務也可能是「縫落在骨材寬度範圍內」（骨材 27 寬，縫中心在骨材 ±13 內即算落骨）——那是區間包含而非座標相等，條文寫法完全不同。
- **相依**：GEO-103。**估時 3h**。

### GEO-105 `subgrid` 子網格 — 第 3 期
- **架構**：`subgrid <id> parent <gid> axis u scope each_cell divisions by_span(v, <band...>)`。以父 cell 為單位等分某軸，band 是 `[min,max)` 依另一軸跨度選等分數；cell 寬不能整除 → 拒絕；交丁時等分的是完整面材本體，裁短片只保留落在片內的線。子網格本身是一個 `ReferenceGrid`，只存 parent_id／axis／bands，**仍然只存來源**。
- **擬立條文**：D19、I25、R23。
- **相依**：GEO-103。**估時 8h**。

### GEO-106 「一面一格」規則重定 + 容量重評 — 第 3 期
- **內容**：現行 8540-8546 的「一面一格」與子網格直接衝突（同面）。改成「一面一主格 + 若干子格」，定義刪父格時子格的連坐，`WORLD_MAX_GRIDS` 8→16，並重評 `GRID_MAX_LINES` 是否要到 96。
- **註**：公理層 D10 **刻意沒有重述「一面一格」**（它目前只活在實作與程式碼註解的 G1，I10 原文也沒寫），就是為了不在這裡挖坑。
- **相依**：GEO-105。**估時 3h**。

### WEB-005 網格來源編輯器與推導線渲染
- **內容**：`web_bridge.c` 新增 `gridlines <sid>` 指令，回傳結構化的 `{id, axis, lines[], source, panel, gap}`；`app.js` 改用它渲染，不再 regex 解析 dump 的 `^grid` 行（2252-2256）；面內「網格」分頁加來源選單（明寫／等差／面材）與即時預覽。**本票同時做掉既有的 WEB-002**（改成 `refs <sid>` 一次回傳 guides+timbers+grids 亦可）。
- **相依**：GEO-100。**估時 4h**。

### 第 10 流的 web 停損說明
`geometry-web/app.js:2252-2256` 目前用正則解析 dump 的 `^grid` 行再 `.map(Number)`。GEO-100 一落地，`grid 1 on 1 u panel 400 gap 20 from 0` 會被解析成 `[NaN,400,NaN,20,NaN,0]`，面內編輯器畫出垃圾格線且不報錯。所以 GEO-100 的驗收含一行 regex 收緊（只吃純數字串，認不得就不畫），真正的網格編輯器留給 WEB-005。

### GEO-107 ✅ 已完成(2026-09-16) 定位邊改成純幾何推導,不再讀 anchor_kind
- **狀態**：2026-09-16 於 GEO-097 的往返驗證中發現，**既有缺陷**（改版前後同樣重現，與網格來源化無關）。尚未修，需先拍板修法。
- **現象**：`_role_ext_stop_primary.scene` 可正常載入，但 `dump` 出來的結果無法重放——
  `place 4 on 1 at-edge e2 +u +n` 被 dump 成 `place 4 on 1 at 1014 1000 +u +n`，
  重放時回報 `V_CUT_PRIORITY：角材 4（優先級 1）端面頂到角材 3（優先級 2）側面`。
  27 個 accept 夾具中只有這一個踩到；其餘 26 個往返逐字相同。
- **成因**：D7 明訂「錨點 = place 當下凍結的 uv + **放法記錄**（anchor_kind、參照、through 等）」，
  但 `world_dump_dsl` 只輸出凍結的 uv 與明寫長度，把 `anchor_kind` 與 `ref_edge` 丟掉。
  重放後 `anchor_kind` 變成 `ANCHOR_AT`，而 `anchor_edge_interval` 要求 `ANCHOR_AT_EDGE`
  才認得定位邊，於是 D16 的固定段／延伸段切分不成立、I22 的豁免失效，
  端面改由 I19 裁決（1 vs 2，需 2 < 1）而被拒。
  幾何完全沒變，變的只有「這支料還算不算有延伸段」這項**放法**資訊。
- **這違反的是 R4**：「dump = World → DSL 序列化⋯⋯重放逐字相同」。目前對這一類場景不成立。
- **修法待拍板（紅燈，需使用者決定）**：
  1. **dump 補上放法記錄**（建議）：在凍結的 `at u v` 後面附一段來源註記，
     例如 `place 4 on 1 at 1014 1000 +u +n from-edge e2`，parser 讀到就還原
     `anchor_kind`／`ref_edge`，**但不重算幾何**（R6(e) 的凍結不受影響）。
     優點：D7 說錨點本來就含放法記錄，這只是把它真的寫出來；缺點：DSL 多一個尾綴。
  2. **dump 直接輸出原本的錨法**（`at-edge e2` + 明寫長度）：更短，
     但明寫長度配 at-edge 違反 I12 的語法配對，要一併改 I12。
  3. **把延伸段改成純幾何推導**（不看 anchor_kind）：最乾淨，但那是改 D16 的定義，
     影響 I20／I22／R18 一整組，風險最大。
- **驗收**：`_role_ext_stop_primary.scene` 的 dump → loadfile → dump 逐字相同；
  27 個 accept 夾具往返全通過；既有 61 筆測試不受影響。
- **檔案**：`current_geometry.c`（`world_dump_dsl` 的 timber 段、`apply_place_line`、
  `anchor_edge_interval`）。
- **測試**：把往返驗證固定成一個可重跑的關卡（目前是臨時腳本），對全部 accept 夾具執行。
- **相依**：無（與第 10 流平行）。**估時 依修法而定，方案 1 約 3h**。


> **GEO-107 完成紀錄(2026-09-16)**
> **這張票我自己寫錯了。** 票裡把它寫成三選一,其中方案三還說
> 「把延伸段改成純幾何推導最乾淨,但那是改 D16 的定義」。那是誤讀:
> D16 原文寫的是「固定段 = 與它所覆蓋的那條外輪廓 FIXED 邊(`boundaryEdge`)
> 在長度軸上重疊的部分」,而 R18 明寫 `boundaryEdge` 是
> 「純幾何,不看宣告與錨法」,還特別點名「用 `through` 放的料貼齊邊一樣 onBoundary」。
> **所以 D16 從一開始就是幾何定義,是實作讀 `anchor_kind` 違反了條文。**
> 這不是三選一,是把實作改回條文。動手前重讀條文才發現,已跟使用者確認後照新發現做。
>
> 修法:刪掉讀 `anchor_kind` 的 `anchor_edge_interval`,
> 換成 `boundary_edge_interval`——定位邊由 `timber_role_props`
> (R18 的那份推導)決定。`timber_end_face_check` 的 `anchor` 參數因此不再需要,一併移除。
> **不動 DSL,不動公理層。** R4 的往返破口是這個修正的副作用:
> dump 丟掉放法記錄之後幾何完全沒變,所以推導結果也不變。
>
> **行為擴大與它揭露的順序問題**:任何非 boundary 角材只要幾何上壓在外輪廓邊上,
> 現在也會受 I22「不得超出定位邊」約束(先前只有用 at-edge 放的才會)。
> 這正是 I22 條文的字面要求,但它讓 `_mut_notch_straddle.scene` 改以
> `V_EXTENSION` 被拒,而不是原本的「放不上去」——那支料橫跨凹口、
> 恰好與凹口底邊共線。問題出在檢查順序:`timber_place_a0_on_surface`(I5)
> 排在角色檢查之後。對一個連存在都不合法的 footprint 去問「它的定位邊是哪條」
> 沒有意義,而且會讓 M08 變成殺不死(變異前後都回 V_EXTENSION)。
> 解法是在 `boundary_edge_interval` 前面加一道 `boundary_contains_rect` 守門:
> D16 的切分本來就預設這支料放得上去。
>
> **驗證環境**:SAC 這輪是**持續性**封鎖,連換檔名重編也擋,
> 與先前「隨機、重跑就過」不同。所以測試改在 WSL 用 gcc 跑
> (`gcc -O2 -w -o /tmp/cg_wsl current_geometry.c -lm`),
> 這是 `sac-blocks-web-bridge` 記錄的備援路徑,實測可行。
> 之後 SAC 放行,Windows 端也複跑確認一致。
>
> 驗證:87/87 測試(WSL 與 Windows 兩邊都跑過);
> **dump 往返 36/36 全過**——先前唯一失敗的 `_role_ext_stop_primary.scene`
> 現在重放成功,R4 恢復成立;check_panels 40 面板無斷鏈;
> 矩陣仍是綠 26 / 黃 37 / 紅 0。
> 被刪掉的 `anchor_edge_interval` 沒有任何變異錨點或導讀面板引用它(已確認為 0)。

### GEO-108 🔁 已於檔末記錄完成 `tests/mutate.py` 把環境失敗誤判成 killed（驗證完整性漏洞）
- **狀態**：2026-09-16 於 GEO-099 驗證中發現,**既有缺陷**,尚未修。
- **現象**：`mutate.py:209` 的判決只看 `verdict = "killed" if test.returncode != 0`。
  本機 Smart App Control 會**間歇性**封鎖新編譯的 `tests/_mut.exe`（`WinError 4551`）,
  此時 `run_tests.py` 每一筆都失敗、returncode 非 0,於是**全部變異都被判成 killed**。
  實測:同一組 M31/M32/M33/M51/M52 連跑三次,第一次五個全是假死
  （死因寫著「例外 [WinError 4551] 應用程式控制原則已封鎖此檔案」）,
  第二次三個真死兩個假死,第三次才全部取得真實死因。
- **為什麼嚴重**：這是最壞的一種假綠燈——變異測試本身是用來證明「測試抓得到錯」的工具,
  它壞掉的時候看起來卻像全部通過。`mutants_results.json` 也會被寫進假結果。
- **修法**：`mutate.py` 建完 `_mut.exe` 後先做一次冒煙執行（跑任何一個已知 accept 的場景）,
  若啟動本身就失敗（exception / WinError,而不是測試斷言失敗）→ 判 `blocked`,不判 `killed`,
  並讓整批以非 0 退出,逼使用者重跑。另可掃 `run_tests.py` 的輸出:
  死因若是「FAIL 例外」而非「FAIL 錯誤不符／應接受但拒絕／應拒絕但接受／長度不符」,
  一律不算 killed。
- **驗收**：人為封鎖 `_mut.exe`（或改名成不存在）後跑 `mutate.py`,結果必須是 `blocked`／非 0 退出,
  不得出現任何 `killed`。
- **檔案**：`tests/mutate.py`（`main()` 的建置後與判決段,約 190–215 行）。
- **相依**：無。**估時 1h**。

### GEO-109 ✅ 已完成(2026-09-16) I19 補上「只有 boundary 可頂外輪廓邊」那一款
- **狀態**：2026-09-16 於 GEO-100 構造測試場景時發現,**既有不一致**,未動手（超出當次授權範圍）。
- **現象**：場景只有一支 `primary`、兩端直接頂外輪廓的 FIXED 邊 → 實作回
  `V_CUT_PRIORITY：角材 3 端面頂到外輪廓邊（RC）——只有 boundary 可頂 RC`。
- **條文怎麼說**：I19 寫的是「其擁有者的優先級必須**嚴格小於**自己（外輪廓/孔邊/柱面 = 0）」。
  `primary` 的優先級是 2，外輪廓是 0，**0 < 2 成立**，照條文應該放行。
  I19 只列了兩個例外（轉角兩支 boundary 互頂、延伸段見 I22），沒有「只有 boundary 可頂 RC」這一條。
- **哪一邊才對**：看 D15 的物理意義段——「連續的邊界材釘在 RC 上，被夾的主支長度成為模數」，
  以及 R19(c)(d)「層級 2 停在層級 1 下面」——**實作的意圖是對的**，
  是 I19 的條文漏寫了「空間邊界只能被 boundary 頂」這一款。
  依第 9 流總則「條文與實作不一致時**改實作**」的字面會改錯邊，這裡應該改條文。
- **建議修法（需使用者拍板）**：I19 補一款——
  「擋面擁有者是空間邊界（優先級 0）時，只有 `boundary` 可以頂它；
   其餘角色端面頂空間邊界一律拒絕（V_CUT_PRIORITY）。」
  並在 D15 的物理意義段加一句指回 I19，說明這是「邊界材連續、主支被夾」的直接後果。
- **附帶影響**：這條限制使「被錨定的主支必然依賴橫跨全寬的邊界材」，
  這正是 GEO-100 無法為 I23(b) 構造隔離殺手的原因（見 GEO-100 完成紀錄與變異 M56）。
  若日後放寬，I23(b) 的殺手就做得出來。
- **驗收**：條文補款後，`_role_priority_primary_rc.scene` 等既有夾具的拒絕理由能由條文推出；
  新增一筆正向夾具說明「boundary 頂 RC 合法」。
- **檔案**：`公理層.md`（I19、D15）。**估時 1h（純條文，不改實作）**。

> **GEO-109 完成紀錄(2026-09-16)**
> 使用者授權後改的是**條文**,不是實作——實作本來就對。
> **開票時我把限制範圍寫得比實作寬**:原票說「空間邊界(優先級 0)只有 boundary 可頂」,
> 但實作只攔 `STOP_OUTLINE_EDGE`,**孔邊與柱面完全不設限**。
> 這不是漏寫,是刻意的分界——`_test_hole_auto.scene` 的註解早就寫著
> 「主支起點頂在 e0 邊界材側面(主支端面不得頂 RC 外輪廓——I19),
> 終點頂在孔邊(孔邊=柱面,各角色可頂)」,而且與 I20「孔邊不算」、
> I21「孔邊上貼邊排的料角色由宣告決定」是同一個分界。
> 條文因此照實寫成兩句:外輪廓邊只有 boundary 可頂,孔邊與柱面不在此限。
>
> 改動三處:I19 補款、D15 物理意義那句指回 I19、§四 記錄補正。
> 原始碼只改註解不改邏輯:RC 那一款的註解改成指向 I19,
> 並把 `timber_end_face_check` 裡那段已經過期的
> 「公理層 I22 內部不一致、未經授權不得修改」改成指向本流已修正的 I22 條文。
>
> **測試完全不用改**:兩個負向夾具(`_role_priority_primary_rc`、
> `_role_priority_secondary_rc`)與正向的孔邊夾具(`_test_hole_auto`)本來就存在,
> 而且都已經在註解裡標了 I19。這從一開始就純粹是條文的缺口,不是覆蓋的缺口。
> **補了兩個夾具**,因為 fresh-context 複驗指出「boundary 頂外輪廓 → 接受」
> 只有隱含覆蓋、沒有專門命名的正向夾具:
>   `_role_rc_boundary_ok.scene`   — 正向對照組,與 `_role_priority_primary_rc`
>                                    同一片面、同樣兩端落在直立外輪廓邊上,差別只在角色。
>   `_role_rc_custom_reject.scene` — 釘住「這一款看角色不看優先級」:
>                                    custom priority 1 的數值與 boundary 完全相同,
>                                    但它不是 boundary,頂外輪廓邊仍然拒絕。
> 第二個一開始沒隔離到目標(起點先撞上角材側面的數值規則),改成兩端都落在
> 外輪廓邊上才真的把 RC 那一款逼出來。
>
> 驗證:87/87 測試;check_panels 40 面板無斷鏈;矩陣仍是綠 26 / 黃 37 / 紅 0。

### GEO-110 ✅ 已完成(2026-09-16) 公理層覆蓋率矩陣 `axiom_matrix.py`
- **動機**:公理層是驗收基準,但「條文」與「守衛它的東西」之間沒有任何機器查得動的連結,
  只有註解裡的散文。本 session 找到的三個條文/實作不一致(GEO-107、GEO-109、以及 I22 那句)
  都是靠手工逐條比對才撞到的。
- **內容**:`geometry-guide/axiom_matrix.py`。解析 `公理層.md` 的 63 條條文,
  對每一條列出:原始碼哪裡提到它(含所屬函式)、哪些 `*.scene` 夾具提到它、
  哪些變異的 desc 提到它;另外檢查條文宣告的每個 `V_*` 錯誤碼在原始碼裡找得到。
  `--strict` 在有紅燈時以非 0 退出。
- **判準是弱代理,這點寫在腳本開頭也印在輸出裡**:量的是「條號在哪裡被提到」,
  不是「哪裡實作了它」。紅燈代表沒有可追溯的連結,**不代表沒被測到**——
  像 I1 承載面框架合法,每個場景都在跑它,只是沒人寫下條號。
  要消紅燈的正確做法是補註解把連結寫下來,不是去改條文。
- **本次同時補完的標註**:原始碼 22 處、夾具 17 個、變異描述 46 筆。
- **結果**:紅燈 24 → **0**,綠燈 19 → 26,黃燈 20 → 37。
  黃燈全部是「有原始碼、缺夾具」,那是**誠實的狀態**——代表這條有實作但沒有專屬測試,
  不該為了讓數字變綠而硬掛一個不相干的夾具。
- **順帶暴露的事**:D15–D17、I19–I22 這整組角色層條文**變異數為 0**,
  與未完成的 GEO-094(補變異測試)完全對上。矩陣讓這件事不用讀 BACKLOG 就看得見。
- **注意**:別把 `--strict` 掛進 CI 之前先確認紅燈為 0,否則會擋住所有人。
- **檔案**:`geometry-guide/axiom_matrix.py`、`current_geometry.c`(註解)、
  `*.scene`(註解)、`tests/mutate.py`(desc)。

### GEO-108 ✅ 已完成(2026-09-16) 變異工具把環境失敗誤判成 killed
- **原問題**:判決只看 `returncode != 0`。SAC 間歇封鎖新編譯的 `_mut.exe` 時,
  `run_tests` 每一筆都以「FAIL 例外 [WinError 4551]」失敗,於是**全部變異被判成殺死**。
- **修法**:跑完先分辨死因是測試斷言還是執行檔沒跑起來。
  輸出含「FAIL 例外」或「FAIL 逾時」,或 `CreateProcess` 直接丟 `OSError`,
  一律重跑(`RUN_RETRIES = 3`);三次都不行就判 `blocked`,**絕不計入 killed**,
  整批以退出碼 2 結束並印出警告。`main()` 的退出碼現在會傳到 shell。
- **順手修掉同一張票的另一半**:跑子集時把結果**併回**既有紀錄而不是整份覆寫。
  原本 `python tests/mutate.py M31` 會把其餘 47 個判決清掉;本 session 踩了兩次,
  都靠手動備份再合併才補回來。現在同時印「本次」與「全檔」兩組統計。
- **驗證**:把 `_cl.bat` 暫時換成產生「存在但不可執行」的假 exe,跑 M31。
  修之前會回報 KILLED,修之後回報 **BLOCKED + 退出碼 2**,`_cl.bat` 已還原。
  正常路徑無回歸(M31 仍以真實死因 killed,M56 仍 survived)。
- **檔案**:`tests/mutate.py`(備份 `tests/mutate.py.bak-geo108`)。
> **收流關卡實測紀錄(2026-09-16)**
> 完整 48 個變異跑完:**43 殺死 / 5 存活 / 0 無效**。
> 存活的五個:M01、M09、M10、M23 是既有的等效變異(理由見第 427 行起的變異測試段),
> M56 是 I23(b) 的未覆蓋缺口(非等效,理由見 GEO-100 完成紀錄)。
>
> **GEO-108 的修正在第一次完整跑就證明了價值**:那一輪有 **10 個變異被 SAC 擋住**
> (M02、M09、M11、M17、M18、M20、M24、M28、M40、M55)。
> 修正之前,這 10 個會全部被判成「殺死」,整份結果會顯示 44 殺、毫無異狀——完全是假的。
> 修正之後它們被標成 `blocked` 並讓整批以退出碼 2 結束,逼人重跑;
> 重跑四輪之後全部取得真實死因(M09 落回既知的等效存活)。
> **2026-09-16 晚間補充:封鎖也可能是持續性的。** GEO-107 那輪連續 15 次都被擋,
> 換輸出檔名重編也一樣,與「重跑就過」的情形不同。`mutate.py` 目前只能用
> `_cl.bat`(MSVC),遇到持續封鎖就跑不動。**備援是 WSL + gcc**,實測可行:
> `gcc -O2 -w -o /tmp/mut.c ... && python3 tests/run_tests.py /tmp/mut`,
> M53 就是這樣拿到真實死因的。日後若常撞到,值得讓 mutate.py 支援
> 以環境變數切換建置指令,但那是另一張票。
> **SAC 的封鎖是隨機的,不是固定針對某個二進位**:M11 連續被擋 11 次,第 12 次就過了。
> 所以看到 `blocked` 就是重跑,不要改程式碼去迎合它。


### GEO-111 ✅ 已完成(2026-09-16) 公理層閱讀器 `make_axiom_reader.py`
- **動機**:使用者反映「貼出來或轉述時,部分細節有點模糊」,想要一個公理層的閱讀器。
  先量再做:63 條條文、65 次交叉引用,**平均每條只有 1.0 次、零懸空引用**——
  所以「通用閱讀器」解的是一個不大的問題,不值得做。
  真正難讀的是**樞紐**:R6 被引用 6 次、I19 與 I22 各 5 次、R3 與 I8 各 4 次、
  D9 3 次,這六條吃掉 65 次引用裡的 27 次。讀 R21 時要同時記住
  R6 的 (b)(c)(d)(e) 四款加 I19 加 D18,那才是腦袋裝不下的地方。
- **內容**:`geometry-guide/make_axiom_reader.py` → `geometry-guide/公理層-閱讀器.html`
  (單檔離線,無外部相依)。只解三件事:
  1. **交叉引用就地展開,而且帶子項的引用只給那一款**。
     全檔有 20 個子項、7 種帶子項的引用(`R6(b)(c)(d)(e)`、`I23(b)`、`R19(d)`、`R21(d)`),
     `R6(d)` 的 popover 只顯示 (d),不是整條 R6。實測驗證過。
  2. **反向引用**:這條被誰引用,改它會波及哪裡。
  3. **三向連結**:條文住在哪個函式、哪些夾具釘它、哪些變異殺得死它。
     資料直接 `import axiom_matrix`,不另外維護一份解析邏輯。
  另有樞紐徽章(被引用 ≥3 次)、紅黃綠燈、條號/標題搜尋。
- **紀律**:與 `make_guide.py` 相同——**產生出來的,不是手寫的**。
  公理層是 SSOT,這頁只是觀察者,絕不寫回。會過期的閱讀器比沒有更糟,
  所以 `current_geometry.c` 檔頭的流程註解已補上「條號註解有增減時一併重跑」。
  腳本本身在解析不到 60 條條文、或發現懸空引用時直接非 0 退出。
- **驗證**:不只「產生得出來」——起本機伺服器實際跑過互動:
  hover `R6(d)` 顯示的確實只有 (d) 那一款;I23 的三向連結面板顯示
  原始碼 `apply_grid_line` / `world_revalidate`、四個夾具、變異 M51 M56,
  反向引用列出 I10 與 R13。
- **刻意沒做**:通用的 markdown 閱讀器、條文編輯功能。前者資料顯示沒必要,
  後者會讓這頁變成第二個事實來源,違反「只讀不寫回」。
- **檔案**:`geometry-guide/make_axiom_reader.py`、`geometry-guide/公理層-閱讀器.html`、
  `current_geometry.c`(檔頭流程註解)。

### GEO-112 ✅ 已完成(2026-09-17) 公理層閱讀器 v2:每條條文附真實範例
- **動機**:v1(GEO-111)解了交叉引用展開,但使用者反映「光看條文還是不好懂,要範例」。
- **範例來源刻意選既有 `*.scene` 夾具,不是手寫散文**:夾具是真的跑過的測試,
  有明確的接受/拒絕與長度數字,**永遠不會跟實作漂移**;手寫的「例如⋯」只是轉述,
  會模糊、會過期、沒人驗——那正是使用者先前點名的問題。
- **三件新東西**:
  1. **每條附範例**。接受型直接渲染平面圖(仰視);拒絕型把場景截到違規行之前,
     重建「失敗前」的配置當圖。每個範例含:接受/拒絕徽章、夾具檔頭註解當旁白、
     圖、帶行號且違規行高亮的 DSL、以及 TESTS 裡的預期結果。
     預設只展開第一個(I19 有 13 個範例,全展開會爆版),附「全部展開」。
  2. **白話旁白**:`geometry-guide/公理層-白話.md`,63 條全寫,
     顯示時明標「白話,非條文」。公理層.md 一個字都沒動。
  3. **沒有夾具的 36 條老實標「尚無範例」**,不硬湊(補夾具見 GEO-113)。
- **實作要點**:
  - 裁切走**純 Python 後處理,不改 C**:抓第三個頂層 `<g>`(仰視)的
    translate + frame rect 算出 viewBox。**只換 viewBox、不刪內容**,
    所以「三視圖」按鈕只是把屬性換回 `data-full`。版面一變 assert 就炸,不會默默算錯。
    不改 C 是因為會牽動 check_panels 的 callout 與導讀重產,收益為零。
  - **拒絕型的截斷啟發式**(`axiom_examples.before_failure`):從 stderr 抓行號 N,
    取前 N-1 行重跑。砍掉 place 後 timber 會變孤兒(I9 的 EOF 檢查,**訊息沒有行號**),
    所以有一個移除孤兒宣告的迴圈,而且**頁面上必須明寫移除了哪幾支**。
    「有圖」要過三道:rc=0、三個視圖且第三個是仰視、仰視圖裡至少一片承載面。
    第三道專殺一種假綠燈——場景被截到只剩註解時 parse 仍會成功,
    `scene_compute_layout` 走空版面分支,會產出一張什麼都沒有的白框。
  - **不允許靜默略過**:exe 找不到或被 SAC 擋 → 整份失敗、退出碼 2、
    訊息教人用 WSL + gcc;要無圖版得明寫 `--no-render`,而且頁首會有紅字橫幅。
- **結果**:54 個夾具裡 53 個有圖。唯一沒有的是 `_mut_col_noz`(違規在第 2 行,
  截斷後場景是空的),正確標成「失敗前狀態無法單獨渲染」並附截斷版自己的錯誤。
  頁面 589 KB,單檔離線。
- **已知的取捨**:同一個夾具被多條條文引用時 SVG 會重複內嵌(54 個夾具 → 79 次)。
  沒有用 `<use>` 去重,因為 shadow tree 對 class 樣式的支援有雷,
  圖渲染不出樣式比多 300 KB 糟。頁首統計因此寫「圖 53/54 **個夾具**」而不是張數。
- **過程中修掉的兩個自己的 bug**(都是驗證抓到的,不是看起來對就算):
  1. `crop_bottom` 原本把整個 `<svg …>` 一起帶進去,變成巢狀 SVG,
     內層 viewBox 把裁切整個蓋掉——圖看起來仍是三視圖。
  2. DSL 用換行串接 `<span>`,但 `<pre>` 會把那些換行也算一行,變成雙倍行距。
- **驗證**:11 項靜態檢查全過(含「統計自洽」「樣式無汙染」「v1 未退化」);
  缺一條白話 → exit 0 且該條顯示「(尚無白話)」、統計誠實變 62/63;
  假 GEO_EXE → exit 2;`--no-render` → exit 0 且有紅字橫幅。
  **互動用本機伺服器實跑**:viewBox 在 `0 1540 4100 3640` 與 `0 0 7900 5180` 之間切換、
  按鈕文字跟著變、「全部展開」把 3 個範例都打開、SVG 實際渲染成 472×419 px。
  (截圖因為視窗在背景一直空白,改用 DOM 量測——那比截圖更硬。)
  `check_panels.py` 與 `axiom_matrix.py` 輸出不變。
- **檔案**:`geometry-guide/axiom_examples.py`(新)、`geometry-guide/公理層-白話.md`(新)、
  `geometry-guide/make_axiom_reader.py`、`geometry-guide/公理層-閱讀器.html`(重產)。

### GEO-113 ✅ 已完成(2026-09-17) 63 條全部補上範例
- **起因**:使用者打開 GEO-112 做的閱讀器實際看過,要求把那 36 條的「尚無範例」補完。
- **逐條量過之後發現不是補註解就好**。87 個夾具裡各指令的使用次數:
  `apply-proj` **0**、`canvas-pos` **0**、`reset` **0**、`delete` 1、`move` 1。
  也就是 R8–R17 那一整族、D12、I14、R20 **是真的沒有測到**,
  不是「有覆蓋只是沒寫條號」。這正是這張票原本要求逐條判斷的理由。
- **分三組處理**:
  1. **15 個既有夾具補檔頭註解**(D2 D3 D4 D5 D6 D7 D8 D9 D13 I1 I2 I3 I11 R18;
     R11 的標記加在新寫的 `_ax_r17_wall_column_face.scene` 上,它本來就會拆片)。
     零行為改動,加完測試輸出與基準**逐字相同**。
     每一行註解都是一個主張,逐檔讀過才寫,標準是
     「這個夾具如果壞了,是不是代表這條被違反了」。
     其中 D4 / D5 / D13 / I3 各補兩個互補的夾具(引用邊界面 vs 自帶 rect、
     六面封閉 vs 兩面不封閉、推得出 vs 推不出、fixity 明寫 vs 省略)。
  2. **28 個新夾具 `_ax_*.scene`**,一條一個最小場景,涵蓋 20 條條文。
     檔頭三行內講清楚條號、在示範什麼、預期什麼;DSL 只留逼出該條所需的最少行數。
  3. **3 條走 web bridge 實錄**(R1 拾取、R4 dump 往返、R5 拖曳 clamp)。
     這三條的行為根本不在場景 DSL 裡——`SCENE_COMMANDS` 沒有 pick / dump / drag,
     所以無論怎麼寫 `.scene` 都逼不出來。改成真的把 bridge 跑起來、
     把送出去的指令與收回來的原文貼進頁面(`geometry-guide/axiom_transcripts.py`)。
     R1 用三次 pick 對照:兩條參考線各自單獨經過的點回傳參考線,
     三者重疊的交點回傳最後畫的角材。R4 真的做完整往返,兩份 dump 各 1036 字元逐字相同。
     R5 三次拖曳分別得到 3000 / 0 / 1234——越界的夾回端點,區間內的原樣通過。
- **`apply-proj` 那一族先探路才動手**。它從來沒有任何夾具走過場景檔這條路,
  所以第一步只寫 R9 的拒絕案例確認走得通,過了才續寫其餘八條。結果全部可用,
  九條的錯誤訊息都與條文對得上(例如 R14 回「投影項橫跨拆分線,無法歸屬單一面片」)。
- **測試器加了 `not_contains` 欄位**。有些夾具主張的是「什麼都沒發生」——
  R12 的樑是條帶項、沒帶 `cut-strip` 就不動幾何——那種主張只能用「不該出現」來驗,
  光靠 accept 驗不到。加這個欄位是為了讓夾具真的在驗它宣稱的事。
- **結果**:閱讀器 **63/63 有範例、尚無範例 0 條**;圖 86/90 個夾具;實錄 3/3;頁面 977 KB。
  測試從 87 筆增為 **115 筆全過**。矩陣從綠 26 黃 37 升到 **綠 59 黃 4**。
- **4 個夾具沒有圖,都是誠實的情況**:違規就在第一條內容行(截斷後場景是空的),
  或錯誤訊息沒有行號(I9 的收尾檢查)。另外特地確認**沒有任何一條條文的範例全部缺圖**——
  I1、I2、R11 原本只有拒絕型範例,各補了一個有圖的正面對照。
- **降級路徑實測過**:bridge 找不到 → 頁面照樣產生、三條標紅、頁首橫幅、退出碼 1;
  明寫 `--no-bridge` → 退出碼 0。兩者的頁首統計都誠實寫成「實錄 0/3」。
- **剩下的 4 條黃燈,兩種原因,都不是漏做**:
  - R1 / R4 / R5:矩陣的「夾具」指的是 `.scene`,而這三條按定義不可能有 `.scene`。
    它們在閱讀器上有實錄,只是矩陣量不到。要讓矩陣認得實錄是另一回事,這裡不動它的定義。
  - R19:它**有**夾具,黃的原因是原始碼裡沒有任何註解寫下 R19。
    補一行註解就會變綠,但那要改 `current_geometry.c`,
    而那個檔當時有別人未提交的 grid-ref 工作,所以沒碰。
- **順手發現、只報告沒動手**:`_mut_col_noz.scene` 的檔頭寫「R11 推不出就拒絕」,
  但現行 R11 講的是「拆片面與生成面一律游離」,那句描述其實對應 D13 的末句。
  看起來是條文重編號後遺留的舊引用。已另外把 D13 標上去,原本那行沒改。
- **檔案**:16 個既有 `.scene`(只加註解)、28 個新 `_ax_*.scene`、
  `tests/run_tests.py`、`geometry-guide/axiom_transcripts.py`(新)、
  `geometry-guide/axiom_examples.py`、`geometry-guide/make_axiom_reader.py`、
  `geometry-guide/公理層-閱讀器.html`。

---

## 第 9 流：公理層閱讀器 第 3 版改版(GEO-114 ～ GEO-121)

> 起因:2026-09-17 使用者請外部 agent(ChatGPT / Product Design)做了一版閱讀器重新設計,
> 落在 `geometry-guide/axiom-reader-design/`(React + Vite 原型),
> 並附一份帶 15 項問題的設計審查 `geometry-guide/axiom-reader-design/設計定稿-第3版.html`。
>
> **使用者已拍板(🔒,2026-09-17)**:
> 1. **只搬設計、不搬技術棧**——產物維持「SSOT → `make_axiom_reader.py` → 單一自足 HTML」,
>    不引入 npm / React / 第二份資料。原型的 `src/content.json`(308KB、63 條 + 141 範例)
>    是第二份 SSOT,**不得**成為正式管線的一環。
> 2. 原型目錄進 git,排除 `node_modules/`、`dist/`(由 `axiom-reader-design/.gitignore` 管)。
> 3. 設計定稿快照(11.8MB 自足 HTML)進 repo 當視覺基準。
> 4. 閱讀模式與互動模型四問見 GEO-120:**維持單頁**、**hover 與參照欄並存**、
>    **雙主題深色預設**、**字型維持系統字體疊**。
>
> **施工圖是那份審查的「修正提案」,不是原型本身。**
> 審查第 1 項判定原型的示範畫面「是一張畫,不是版面系統」
> (`activeId === 'R21'` 寫死決定要不要出現條文重點與關聯範例),
> 第 2 項判定它「把唯一權威的原文折在按鈕後面」。後者現行閱讀器本來就做對了,
> 改版**不得**回歸成原型那樣。
>
> **這 15 項已經過對抗驗證(2026-09-17,fresh context,逐條回原型原始碼核對)**:
> 9 項完全屬實、6 項部分屬實,沒有一項整體不成立,可信度中高。但抓到 4 處具體錯誤,
> 照抄會把錯誤的驗收標準一起寫進生成器,已在對應工單就地訂正:
> (i) 修正 14 的「1000px → 主文 330px」算錯 breakpoint 邊界(實際約 455px);
> (ii) 修正 3 說兩個非條文標註「同字級同樣式」不準——附註是 11px vs 標題 17px;
> (iii) 修正 10 說五個區塊標題同級不成立——`.featured-example h2` 是 16px;
> (iv) 修正 8 說釘選「只寫在 title 屬性裡」不屬實——畫面有可見文字與圖示。
> 驗證另外補到兩個審查漏掉的缺陷,列為改版時的禁則:
> `aria-controls` 不得指向尚未掛載的 DOM id(原型 `src/App.jsx:168`);
> 參照面板的「已固定」狀態不得與「目前沒有參照內容」不同步(原型 `src/App.jsx:52,54`)。

### GEO-114 ✅ 已完成(2026-09-17) 安置第 3 版設計資產
- **內容**:把外部 agent 的產物收進 repo 並鎖定收法。設計定稿快照複製為
  `geometry-guide/axiom-reader-design/設計定稿-第3版.html`;原型目錄 35 個檔納入 git(共 20.8MB:
  快照 11.8MB、`qa/` 截圖證據 9.1MB、原始碼與 `content.json` 約 0.4MB)。
- **`public/assets/diagrams/*.svg` 刻意不入 git**:root `.gitignore` 全域忽略 `*.svg`,
  而那 127 個檔是 `scripts/sync-content.py` 從現行閱讀器再生的衍生物,不是來源。
- **驗收**:`git ls-files geometry-guide/axiom-reader-design/` 列得到 35 個檔;
  快照用本機 http server 開得起來、三欄與標註都正常算繪。
- **相依**:無。

### GEO-115 ✅ 已完成(2026-09-18) 閱讀器第 3 版設計規格定稿
- **產出**:`geometry-guide/閱讀器-設計規格.md`,§0–§8 共 9 節。是施工圖不是設計稿:
  原型的**程式不採用**,只採用視覺語言;審查的**修正提案**才是版面依據。
- **與原型分歧最大處**:拍板 2 維持單頁長捲,原型是一次一條。凡原型中為「單條聚焦」
  而生的機制(hash 路由、pushState、單條進場動畫、Toast)一律不移植,列入放棄清單。
- **本次規格新做的判斷**(不是抄原型):
  - **條文標題 40px → 28px**。原型 40px 是為「一次一條」設計的;63 條堆疊時會讓
    長捲軸變成一串巨標。
  - **斷點表重新推算**,標出「導覽 224 + 參照 36% 會把主文壓到 600px 以下」的例外區間。
    初稿把上界寫成 1300px,**經 fresh-context 驗證員重算後訂正為 1287.5px**
    (主文 = `0.64w − 224`,令 ≥600 得 `w ≥ 1287.5`;1201px 時主文僅 544.6px,
    1300px 其實已有 608px)。驗收要實測 1201px 與 1288px 兩個邊界。
  - **兩條會直接推翻拍板 2 的禁則**:條文原文不得放進預設收合的 `<details>`;
    搜尋不得對 `<article>` 套 `display:none`。收合/隱藏的內容多數瀏覽器 Ctrl+F 搜不到。
    已查證現行 `make_axiom_reader.py:700-705` 只隱藏 `nav a`、從不碰 `<article>`,
    所以這兩條是**保住現有行為**,不是新增限制。
  - **燈號與選取態的邊框衝突**:導覽項目左邊框已被可追溯性燈號佔用,選取態改用
    `box-shadow:inset` 疊在內側。
  - **`--accent` 與 `--geo-*` 色相差 ≥60°** 當成可檢查的閘門,取代「互動色與語意色分家」
    這種沒有裁判的說法。
- **四處審查錯誤已套用訂正值**並在規格 §7 留下對照表,避免日後有人回頭照抄審查原文。
- **驗證**:派 fresh-context verifier 逐條核對 14 項(5 處引用、7 組色票、3 個字級、
  3 處算術、內部一致性)。**12 通過、1 不通過**(上述 1300 → 1287.5 的算術錯誤,已訂正)、
  1 項措辭提醒(「8 節」實為 9 節,已改)。
- **驗收**:§8 列了 7 條逐項可檢查的閘門(grep 不到硬編碼條號分支、63 條區塊組成一致、
  grep 不到硬編碼色碼、色相差、原文不在收合區、六個寬度各截淺深兩張、建置期自檢退出碼 0)。
- **檔案**:新增 `geometry-guide/閱讀器-設計規格.md`。

### GEO-116 ❌ 已作廢(2026-09-20) 閱讀欄改版(審查修正 1 · 2 · 3 · 4 · 10 · 12)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-147(原文/白話順序)、GEO-140(計數單一來源)。原文保留供追溯。
- **內容**:改 `make_axiom_reader.py` 的 HTML/CSS 模板。要點:
  - **原文優先**(修正 2):原文預設展開且置於摘要之上,改寫可收合。現行已如此,**不得回歸**。
  - **一套版面吃 63 條**(修正 1):重點列表由資料驅動,不得有任何條號寫死的分支。
  - **三種文本命名一次定案**(修正 3):原文／重點／白話各給固定位置與固定標籤,
    禁止同一件事出現「完整原文」與「條文原文」兩種叫法。
  - **章節標題降級為標籤**(修正 10):改 12px 大寫標籤、弱對比寬字距,把重量讓給內容;
    不得出現同一屬性在同檔宣告兩次的補丁區。
  - **控制項回到可讀尺寸**(修正 4):白話展開鈕改段落下方一般文字鈕,14px、44px 觸擊區。
  - **原文行號常駐**(修正 12):`公理層.md:NNN` 併進標題下的 meta 行,任何寬度都不隱藏。
- **驗收**:重生後 63 條逐條檢查,**沒有任何一條掉回不同版面**;
  原文在所有條文都預設可見;行號在 1280px 與 390px 都看得到;
  腳本內建自檢(條文 ≥60、白話條號合法)照常通過。
- **檔案**:`geometry-guide/make_axiom_reader.py`、重生 `geometry-guide/公理層-閱讀器.html`。
- **相依**:GEO-115。**估時 2h**。

### GEO-117 ❌ 已作廢(2026-09-20) 參照欄(審查修正 7 · 8 · 9 · 11)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-146(參照欄與批註並存)、GEO-141(互動色與圖面色分家)。原文保留供追溯。
- **內容**:右側可固定的引用面板。要點:
  - 參照條號降為 15px chip(修正 7):現行原型的 `R6(d)` 是 49px,比主標題 40px 還大。
  - **實心按鈕給「查看全文」、返回退成次要**(修正 8):56px 實心藍主按鈕做的是返回/關閉,
    真正往前的入口卻是次要文字鈕;返回還有頁首與面板兩個重疊入口,擇一。
    (審查原文說「釘選行為只寫在 title 屬性裡」,對抗驗證判定**不屬實**——
    原型 `src/App.jsx:176` 有可見的「已固定/未固定」文字與圖示切換。釘選本身不必重做,
    但要確保狀態在畫面上說得清楚。)
  - 錯誤分類(如 `E_UNSUPPORTED_END`)不得縮成 11px 灰字(修正 9)——它是可查關鍵字。
  - 互動色與圖例色分家(修正 11)。
- **驗收**:從參照跳到全文再返回,原展開狀態與 scrollTop 還原;
  參照欄關閉後閱讀欄展開;鍵盤可全程操作。
- **相依**:GEO-116。**估時 2h**。

### GEO-118 ❌ 已作廢(2026-09-20) 導覽欄(審查修正 5 · 6)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-139(追溯燈號回歸)、GEO-149(證據強度可見)。原文保留供追溯。
- **內容**:**全列 63 條**、群組可收合;群組條數(19 / 23 / 21)常駐,不得只在 hover 出現。
  若要做重點,只能用資料裡真實存在的標記當篩選器,**禁止手寫白名單**
  (原型寫死 `['R6','R18','R19','R20','R21']`)。
- **驗收**:第一眼看得到 63 條的結構;觸控裝置看得到條數;無任何硬編碼條號清單。
- **相依**:GEO-116。**估時 1h**。

### GEO-119 ❌ 已作廢(2026-09-20) 響應式與手機(審查修正 13 · 14 · 15)
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-148(斷點與手機底部列)。原文保留供追溯。
- **內容**:
  - **650–999px 補上真正的版面**(修正 14,P1):原型的漢堡鈕只在 ≤650px 出現
    (`src/reader.css:6,26,28`),所以 650–999px 側欄硬佔 190px 且收不起來;
    同區間參照面板是 `min(480px, 100vw − 210px)` 覆蓋層(`reader.css:25`)。
    **審查原文「1000px 時主文被夾到約 330px」經對抗驗證判定算錯**:1000px 不觸發 999px 查詢,
    而是落進 1280px 那段(`reader.css:24`,`--nav:195px`、`--reference:35%` 內聯欄非覆蓋層),
    主文實際約 455px。結構性問題(190px 段收不起來、999px 內是覆蓋層)成立,但驗收
    **不得**照抄 330px 這個數字。
    改成 ≤1200px 起導覽即抽屜、主文維持 ≥600px;參照在 ≤999px 改半高 sheet。
  - 手機頂欄從 112px(佔 390×844 的 13%)收成 56px 單列,下接可橫捲的條號 chips(修正 13)。
  - 工程圖在窄螢幕可點開全螢幕縮放,或改用裁切局部圖(修正 15)。
- **驗收**:390 / 700 / 1000 / 1280 / 1487px 五個寬度各自截圖;
  每個寬度都無水平溢位、主文可讀、主要控制未被裁切。
- **相依**:GEO-116、GEO-117、GEO-118。**估時 2h**。

### GEO-120 ✅ 已拍板(2026-09-17) 閱讀模式與互動模型三問
- **問題一:單頁長捲軸 vs 一次一條**。現行閱讀器是單頁攤平 63 條(`scrollHeight` 58,512px),
  Ctrl+F 搜得到任何一句條文;第 3 版設計是一次一條 + 參照欄,改過去等於放棄瀏覽器全文搜尋。
  這份文件的用途正是拿來核對引擎行為,全文搜尋是實質功能。設計審查沒評估這一項——
  它的對象是原型,而原型一開始就是一次一條。
  **拍板:維持單頁**。63 條繼續攤平在同一頁,只把外觀換成深色三欄(左導覽固定、
  右側加可固定參照欄),Ctrl+F 保住,現行功能全部不動。第 3 版的視覺主要收穫
  (三欄、深色、參照欄、手機抽屜)在單頁模式下都成立。
- **問題二:參照別條公理的互動**。現行是 hover 彈出預覽,第 3 版是點擊開固定側欄。
  **拍板:兩者並存**。hover 快速預覽留著當掃視用,點擊開右側可固定面板當深入用。
  砍掉 hover 是淨損失,且觸控裝置本來就沒有 hover,兩者不衝突。
- **問題三:主題**。第 3 版只有深色,現行有 `prefers-color-scheme` 雙主題。
  **拍板:維持雙主題,深色為預設**。第 3 版色票當深色那套,另調一套淺色。
- **問題四:中文字型**。第 3 版用 `@fontsource-variable/noto-sans-tc` 內嵌可變字重,
  現行是系統字體疊(`make_axiom_reader.py:520` 附近)。實測(非估算,fontTools 4.63.0):
  閱讀器可見文字共 **819 個不重複 codepoint**(CJK 704);完整字型 105 個 woff2 切片
  合計 4,194,768 bytes。以現行 978,983 bytes 為基準,base64 內嵌後——
  完整內嵌 **+587%**(6.73MB);子集化三字重(450/550/650)**+50%**(1.47MB);
  子集化單一字重 +16.5%(1.14MB,但等於放棄整個字重層級,比系統字體的 400/700 還糟)。
  另有 8 個字元(`⊆⊇⊉⌈⌉⌊⌋🔒`)Noto Sans TC 根本沒有字形,三案都得靠系統後備。
  **拍板:維持系統字體疊**。+0 bytes、管線不變、零新故障模式;代價是 450/550/650
  會被四捨五入。字重不是此次改版的主要收穫(版面、色票、層級、參照欄才是),
  日後要補子集化可以當純加項,但那時必須同步加一道「字元漏網就非 0 退出」的建置期閘門,
  否則公理層.md 新增字元時子集會靜默過期。

- **連帶約束(寫進 GEO-116～119 的驗收)**:現行閱讀器獨有的追溯類功能一律
  **不得丟失**——紅/黃/綠可追溯性燈號、三向連結(原始碼/夾具/變異)、樞紐徽章、
  web bridge 實錄專屬區塊、「全部展開/收合」、即時隱藏式搜尋,
  以及生成腳本的建置期強制檢查與非 0 退出(懸空引用、條文數 ≥60、白話條號合法)。
  第 3 版原型這些全都沒有,搬設計時最容易連同丟掉。

### GEO-121 ❌ 已作廢(2026-09-20) 修掉 SVG 樣式段不隨深色模式變的既有缺陷
- **作廢理由**:本票的依據 `閱讀器-設計規格.md` 已由使用者拍板整份作廢,且本票的對象是 `make_axiom_reader.py` 產出的舊閱讀器(已非正典)。仍然成立的問題改由第 11 流承接:GEO-141(色彩 token 化,範圍已擴大到 281 張例圖與見證圖)。原文保留供追溯。
- **起因**:改版盤點時發現,`make_axiom_reader.py:620-636` 的 SVG 專用樣式段**硬編碼色碼**,
  不在 `@media(prefers-color-scheme:dark)`(`:515-517`)的涵蓋範圍內。現行深色模式下
  工程圖的配色是錯的。這也正是設計審查第 11 項「互動色與資料語意色混用」的根源。
- **內容**:把 SVG 色碼收進 `:root` token(`:513-514` 已有 token 機制,只是這段沒用),
  並**把互動色與資料語意色分家**——`#88cafa` 目前同時是品牌/連結/條號/釘選狀態
  與工程圖的「邊界」;琥珀 `#efb765` 同時是強調色與「角材」。讀者無法從顏色判斷
  這是可點的還是一種構件。
- **驗收**:淺色與深色兩個模式各截一張含工程圖的畫面,圖例色與線段色一致且可辨識;
  全檔 grep 不到散落在 SVG 段的硬編碼色碼;互動色不再出現在任何圖例。
- **相依**:GEO-115(色票 token 表要先定案)。**估時 1h**。

---

## 第 9 流盤點結論(2026-09-17,四條併行調查線的產出)

1. **這是換皮,不是換血**。`make_axiom_reader.py` 共 714 行;資料層
   (`axiom_matrix.parse_clauses` `:47-69`)只回純 tuple/dict,HTML 在 `main()` 迴圈裡
   直接字串拼接,**沒有中間視圖層**。換三欄版面預估:CSS(`<style>` `:512-645`)
   新增 70–100 行 + 調整 20 行;HTML 骨架(`TEMPLATE` `:508-707`)< 30 行;
   JS(`<script>` `:651-706`)新增 60–100 行;**資料層完全不用動**。
2. **綁死的格式要同步改**:`ref_re` 正則(`:112`、`:319-332`)與卡片 id `c-%s`(`:447`)、
   nav href(`:462`)、JS 錨點(`:696`)、`DATA` key(`:401`、`:656`)四處格式互相咬合,
   動連結呈現要一起查。`build_examples` / `build_transcript` 分別綁死
   `axiom_examples.py` / `axiom_transcripts.py` 的回傳欄位名。
3. **體積基線**:現行單檔 978,983 bytes 裡,132 個內嵌 `<svg>` 佔 **615,022(62.8%)**,
   CSS 僅 7,827,JS 35,263,純文字/標記 320,871。換版面動到的是那 7,827 + 35,263,
   佔全檔 4.4%——體積不會因為改設計而顯著變動。
4. **原型漏掉實錄專區是意外,不是取捨**:`axiom-reader-design/scripts/sync-content.py:64-70`
   用同一條正則抓 `ex-wrap`,而 `build_transcript()`(`:219`)把 R1/R4/R5 實錄也包在
   `ex-wrap` 外殼裡,於是實錄被併進泛用 `examples` 陣列、結構化標籤丟失。

### GEO-122 ✅ 已處理(2026-09-18) D10a 奇數 gap 修正;等分軸定義提出但未採納
- **起因**:使用者在批註版閱讀器上對 D1 提問——「座標都是毫米,遇到均分怎麼辦?
  你要拒絕嗎?這樣這種工具還能用嗎」。
- **查證結果**:公理層並沒有「均分除不盡就拒絕」這條通則。
  `D10a:66` 明寫「不因『除不盡』而拒絕」;`R3:208` 的「除不盡 → 拒絕」限定在
  `unproject det=0` 的數值退化。**真正會擋人的只有一條**:D10a 的
  「gap 為奇數 → 中心線不是整數 → 拒絕」——而 3mm / 5mm 是實務上最常見的板縫寬。
- **判定是缺陷不是紀律的依據**:`I13:152` 對奇數角材寬用的是
  「多的 1mm 恆在 +cross 側」這種**定義好的取整**,沒有拒絕。同一份文件對同一類問題
  給了相反待遇,是自相矛盾。R3 的「拒絕不猜」管的是答案不確定(det=0、多解),
  不管「答案已知但不落在整數格上」。
- **已採納(使用者明示授權)**:D10a 的 `c_k` 改成 `a + k·T + panel + ⌊gap/2⌋`,
  gap 奇數時中心線偏向低座標側 0.5mm;刪除該拒絕條款並寫明理由。
- **提出但未採納**:另立一條「等分排法(DIVIDE)」軸定義,用整數分配
  (`q=⌊L/n⌋`、`r=L mod n`,前 r 份長 q+1;1000 分 3 = 334/333/333)使等分永不除不盡。
  **一度寫進公理層(D10c)後由使用者要求撤除**——授權當時問的是「修掉 gap 缺陷」,
  新增編號條文超出授權範圍。已完整回復:D10 的「四選一」、D10c 整條、I10 的
  DIVIDE 字句全部撤掉,閱讀器重出回到 63 條。
  **教訓**:改 🔒 公理層時,「修正既有條文」與「新增條文」是兩種授權,必須分開問。
- **相關但未處理**:`BACKLOG.md:684`(第 2/3 期的子網格 subgrid)已規劃了等分機制,
  且寫著「cell 寬不能整除 → 拒絕」——與本次的判斷同屬一類問題,條文未定案前先不動。
- **尚未跟上**:`current_geometry.c` 還會拒絕奇數 gap;
  `_edge_grid_panel_odd_gap.scene` 與 `tests/run_tests.py:99` 仍斷言 `expect: reject`。
  條文已改、實作未改,這三處現在與公理層矛盾。

### GEO-123 ✅ 已入層(2026-09-18) 禁止來歷不明的數字:參考線與角材放置只能引用
- **起因**:使用者在批註版閱讀器上逐條批註 D1 / D3 / D4 / D10 / I5,共同訴求是
  **「幾何要能依環境推導,不要逼使用者硬寫數字」**。I5 那則(`kind=missing`)寫得最直接:
  「角材放置前要決定角材長度,角材長度只能『引用』」。
- **兩批入層,先參考線後角材**:
  1. **參考線位置只能引用**(D6、D6a、D6b、I7、R5)。`D6` 的 offset 不再存自由數值,
     只存引用式;`D6a` 定義引用式 `offset = Σ cᵢ·qᵢ`,五類可引用量、求值後取下界;
     `D6b` 具名規格常數 `spec <名稱> <整數>` 是**全公理層唯一允許字面數字的地方**。
     **係數是比例不是尺寸**——cᵢ 無單位,帶 mm 的量一律不得寫字面數字。
     `R5` 拖曳改成吸附到最近的合法引用,寫入引用式而非座標。
  2. **角材放置只能引用**(D7、D11、I8a、I12、I13、I23、R2、R4、R6(e))。
     **長度不宣告**——廢除 `timber id L A B`,一律由 R6 推導、撞到佔用邊界即止。
     **位置只能引用**——`at-line`(中線對齊參考線或格線)、`at-face`(側向貼齊佔用邊界,
     含已放角材側面);廢除 `at` 自由 uv 與 `at-guides`。
- **使用者給出的關鍵洞見**:擋面的物理意義就是「已被佔用的空間不能再被佔用」。
  因此「邊」與「擋面」本來是同一件事——都是佔用邊界,差別只在相對長度軸的朝向:
  **垂直**者頂端面決定長度,**平行**者供側向貼齊決定位置。已寫進 `D11`。
  原本 `at-edge` 只吃輪廓邊與孔邊、漏掉已放角材側面,就是這個統一沒做完的後果。
- **三條 🔒 被反轉**:`R6(e)` 與 `R2` 原本明寫「凍結 / 不重放」,`D7` 的長度模式二選一
  也是 🔒。使用者拍板改成**跟著動**:被引用者移動即重新推導,沿依賴鏈取遞移閉包。
  `I23` 的引用鎖隨之解除(移動不再直接拒絕),`R4` 的 `grid-ref` / `span-auto` 整套作廢。
- **配套新增 `I8a` 影響預覽**:使用者在「整筆回滾 / 部分提交標紅 / 先預覽再套用」
  三者中選了預覽。移動已被引用的線或邊必須先在候選世界算出影響並逐項列出
  (受影響角材的遞移閉包、新舊中線與長度、每項違規的條號與預期/實際);
  零違規且使用者確認才套用,**有違規則不得套用**——World 永遠不進入非法狀態。
- **提出但撤除**:一度新增 `D10c 等分排法(DIVIDE)`,使用者要求撤除(見 GEO-122)。
  該次的教訓「修正既有條文與新增條文是兩種授權」,本批已照做——D6a/D6b 與 I8a
  都是單獨明確請求授權後才寫。
- **編號**:用 `D6a`/`D6b`/`I8a` 而非新數字,因為 `§四` 已把 `D19`/`R22`/`R23`
  預留給第 2、3 期的相位/交丁與子網格。
- **閱讀器同步**:63 → 66 條。原文直接從 `公理層.md` 抽,不手抄;
  8 條的白話原本描述舊規則(「兩種寫法…凍結」「明寫長度只能用 at」「不會跟著走」
  「凍結不重算」「引用鎖」),全部改寫,否則閱讀器會自相矛盾。
- **實作尚未跟上,且已知衝突**:`current_geometry.c` 一行未動;
  `_ax_i12_auto_with_at`、`_ax_i12_explicit_with_atgrid`、`_edge_grid_locked*`(3)、
  `_edge_freeze`、`_edge_grid_panel_odd_gap`、`_ax_r13_anchor_*` 等 20+ 個夾具
  仍斷言舊行為;`tests/run_tests.py:99,242,244` 直接測已作廢的規則。
  **現在跑測試必紅,原因是條文比實作新,不是程式壞了。**
  上一個 commit(c8a387a)的 grid-ref / span-auto 實作也被本批作廢。

### GEO-124 ✅ 已修(2026-09-18) 清掉 GEO-123 留下的新舊條文矛盾
- **起因**:使用者請另一個 agent 檢查閱讀器,指出「同一條文裡出現互相相反的要求」。
  逐條驗證後**屬實,且是 GEO-123 造成的**——改條文時只更新了 `body`,
  沒有同步 `clauses[].subs`(子款)與跨條文的交叉引用。
- **SSOT 修掉 7 處**:
  `D10a` 起算點「凍結,比照 R6(e)」→ R6(e) 已反轉,改標為本條自有的凍結;
  `D18`「與 at-edge 同一套寫法」→ at-face,並說明 at-face 取平行側面;
  `I10`「受 I23 的引用鎖限制」→ 引用鎖已解除,改走 I8a;
  `R6(c)`、`R18` 的 at-edge → at-face;
  `R21(f)`「兩端與長度在 place 當下凍結」→ **不凍結**,存擋面參照、移動即重推;
  `D15` 語法 `timber id [L] A B ...` → **移除 `[L]`**(D7 已廢除明寫長度)。
- **閱讀器修掉 4 處**:
  `clauses[].subs` 從 `公理層.md` 重新產生——原本 `I23(a)`、`I23(c)`、`R6(e)`、`R21(f)`
  四個子款仍是舊文,讀整條與只讀子款會得到相反指令(這正是對方指出的最嚴重項);
  `R18` 白話仍寫 at-edge;
  第 5 則批註(I5)只存在 JSON、沒有靜態 `inline-note`,只讀靜態正文的流程會漏掉它;
  可見文字仍寫「4 則批註」。
- **subs 解析器有驗證**:先用本次未改動的 `R19` 做 round-trip,重新解析的結果必須與
  檔案內既有的 subs **逐字相同**才繼續;通過後才套用到其餘條文。
- **對方另外兩點的處置**:
  - 「長度只能引用可能被縮窄成長度只能自動跨距」——**不是誤改**。使用者在 I5 批註之後
    明確口述了規則:「不用決定長度,他會依賴承載面上的幾何資訊來決定長度,
    只有在遇到擋面的時候會停止」,並在我提到長度的線性組合時糾正
    「這是參考線引用的常數的線性組合,跟角材有什麼關係」。後者取代前者。
    對方只讀檔案、讀不到這段對話,所以判斷合理但結論不成立。
  - 「D3/D4 的樑高度與材料厚度干涉未入層」——**屬實但是刻意的**:
    `§四:336-337` 明文把「完成面、面材厚度、完成面高程」與「樑投影的輪廓裁切」
    列為未來的層。使用者的 D3/D4 批註正是指向這塊留白,尚未拍板。
- **仍未處理**:實作與夾具(見 GEO-123 末段),以及 `_edge_grid_panel_odd_gap` 等 20+ 個
  仍斷言舊規則的 `.scene`。

### GEO-125 ✅ 已修（2026-09-18）實作跟隨 GEO-123 / GEO-124 新公理
- 公理層與正典閱讀器未由本次工作改動；遇到新舊規則衝突一律遵循新版。
- 加入具名規格、有理位置引用、at-line / at-face、引用依賴重算與 I8a 影響預覽；
  明寫長度、自由 uv、凍結 dump、grid-ref/span-auto、網格引用鎖等舊入口均拒絕。
- 保存引用與放置順序，確認前 World 不變；取消、無效／過期預覽、群組錯誤全部回滾。
  補正奇數板縫、共線擋面重複、自帶矩形角色驗證、單擊歷史、面內參考線扣孔裁切。
- 示例與測試一起遷移。121 場景、80 C 完整性、25 引用合約、9 保存、8 服務測試通過；
  412 畫布檢查、273 Chrome 操作檢查、12 最終引用流程檢查通過。
- 核心與保存／引用測試另通過 ASan/UBSan。MSVC 核心與 bridge 編譯通過；
  本機原生執行受 Smart App Control 限制，執行驗證與交付入口使用既有 WSL。
- 詳細對照、語法及驗證範圍見 `geometry-core/README.md`；可用
  `geometry-web/start.ps1` 重新編譯並啟動目前版本。

### GEO-126 ✅ 已修(2026-09-18) 全專案矛盾稽核;修掉子款 block 未同步與文件層過時宣稱
- **起因**:使用者要求全面檢查矛盾。派四條 fresh-context 稽核線(公理層內部 / 實作 /
  夾具測試 / 閱讀器與白話),外加自查文件層。
- **最嚴重的一項,是我造成的**:有子款的條文在閱讀器的 `blocks` 裡存**兩份**——
  `body.p01`(整條全文)與 `body.<letter>`(每個子款各一份)。先前的建置腳本
  **只改了 `p01`**,子款留著舊文。於是 `R6`、`R21`、`I23` 的頁面先顯示新版、再顯示相反的舊版。
  實際過期的 6 個:`R6.body.c`(at-edge)、`R6.body.e`(凍結)、`R21.body.f`(凍結)、
  `I23.body.a/b/c`(引用鎖)。已全部從 `公理層.md` 重新產生。
- **為什麼自我驗證抓不到**:先前用「blocks 串接 == clauses.body」當檢查,
  但 `clauses.body` 正是從 blocks 反推來的——**等於拿檔案跟自己比,永遠會過**。
  已改成**逐條對 `公理層.md` 比對**:`p01` 與每個 `body.<letter>` 都必須與 SSOT 逐字相同。
- **文件層三處過時宣稱(也是我寫的)**:
  `AGENTS.md` / `CLAUDE.md` 寫「閱讀器唯一產生方式是 make_axiom_reader.py」——**假的**,
  那支腳本現在輸出 `公理層-追溯診斷頁.html`;又寫「987KB、132 個 SVG」(實際 3.4MB、141 個)、
  「正典沒有批註功能」(已經有)。最危險的是「要改閱讀器 = 改 make_axiom_reader.py 模板整份重產」
  ——照做會產出另一份不同的閱讀器,正是該規則要防的事。已全部改寫,並補上五道完整性 assert 的說明。
  `閱讀器-設計規格.md` 的對象已換人(正典改成批註版),加了狀態標頭說明哪些仍有效、哪些失效。
- **稽核結論(四條線)**:
  - 實作:**行為層面與條文一致**。舊機制解析器全面拒絕(`current_geometry.c:8853-8864` 明寫長度、
    `:9401` span-auto、`geometry-core/references.inc:490` 四種舊錨法)。
    三處非行為性殘留:`current_geometry.c:9207` 孤兒註解寫「奇數 gap → 拒絕」但底下無程式碼、
    `ANCHOR_AT_GUIDES` 死列舉 `:11894`、`I23(b)` 訊息未帶 `V_GRID_LOCKED` 字樣。
    一處超出條文:I8a 預覽列**所有**已放角材而非嚴格依賴鏈子集;觸發指令集也比條文列舉的廣。
  - 夾具:行為都正確,但**多個檔頭註解仍描述已作廢的機制**
    (`_edge_grid_panel_odd_gap`、`_ax_i12_*`、`_edge_grid_locked*` 的歸因寫成 I23 實際是 I8a)。
    **覆蓋缺口**:I8a 預覽的**成功套用路徑(preview→confirm)零夾具**——
    R2「使用者確認才提交」從未被驗證過;I23(b) 單獨隔離也是 0。
  - 閱讀器:完整性三道 assert 全過,條目集合與 SSOT 零差集(66 條,D=21 I=24 R=21)。
- **仍未處理,留給使用者拍板**:
  1. `D6b:54`「唯一允許字面數字的地方」與 `D10:74` SERIES 的 `start`/`step`、
     `D10a:97` 的 `from c`/`panel`/`gap` 矛盾——那些都是裸 mm 字面值。
     要嘛把禁令擴及 D10/D10a(再一批條文改動),要嘛把 D6a/D6b 的措辭收進參考線範圍。
  2. `I8a:170` 的觸發清單沒列「重宣告邊界面而移動被 at-face 引用的邊」,
     但 `I13:204` 說被引用者移動一律走預覽。
  3. `R13:310`「角材以錨點 uv 判定」與 `D7:61`「不存凍結 uv」用語不一致。
  4. `geometry-guide/公理層-白話.md`(323 行)幾乎整份仍是舊制度
     (仍寫明寫長度、凍結、at-grid/at-edge/at/at-guides、引用鎖)。
     閱讀器內建的 `plain` 是新的,但**來源檔沒跟上**。

### GEO-127 ✅ 已修(2026-09-18) 收掉 GEO-126 列出的四項矛盾
- **D6a / D6b 的適用範圍**:原本寫「所有帶單位的量一律不得以字面數字出現」與
  「唯一允許字面數字的地方」,與 `D10` 的 SERIES `start`/`step`、`D10a` 的
  `panel`/`gap`/`from c` 仍收字面 mm 的事實互斥。措辭收斂為**參考線位置的引用式**範圍,
  並在 D6a 末段明寫:「這是已知的不一致,不是本條的例外」——按使用者「禁止來歷不明的
  數字」的原則,那些參數也該改成引用 D6b 具名常數(`spec 板寬 600`),
  沒有一併做是因為牽動 D10/D10a 條文、實作與 121 個夾具,**留待使用者拍板**。
- **I8a 觸發範圍**:原本列舉三種操作,漏掉「重宣告邊界面/承載面而改動被 at-face 引用的邊」
  與「改動被引用的具名常數」,與 `I13`「被引用者移動一律走預覽」不一致。
  改成以**「被引用者是否改變」為判準**,列舉只當舉例。
- **R13 用語**:「角材以錨點 uv 判定」與 `D7`「不存凍結 uv」字面打架。
  補明是**錨點求值後的 uv**(當下由 I13 的引用求出),不是欄位裡存著的座標。
- **I8a 正向路徑補夾具**:新增 `_edge_i8a_confirm.scene`,與 `_edge_freeze.scene` 成對——
  後者測「不預覽就直接改會被擋」,前者測「`preview` → `confirm <token>` → 真的套用」。
  `R2`「零違規且使用者確認才提交」先前**零夾具**,是條文寫了、實作做了、卻沒有任何
  測試證明的路徑。實測預覽輸出 `timber 1 center 500 -> 2000`,確認真的套用。
- **順帶查出一個會誤導所有人的坑**:`tests/run_tests.py:205` 預設用**repo 根目錄**的
  `cg_new.exe`,而那支是 GEO-125 之前的舊檔。照著跑會看到一堆假紅燈,
  錯誤訊息還是舊的「錨法只認得 at、at-guides、at-grid、at-edge」,
  會把人引去查錨法而不是查 exe。重建後 **122/122 全過**。

### GEO-128 ✅ 已採納（2026-09-18）跨面共用定位基準
- 使用者授權規劃與執行 agent 並行協作，後續明示檢查完成後提交合併；PR #1 經獨立審查及主審核對後批准合併。
- 公理逐條修改已審閱並正式採納。新增 D6c / I7a，未占用相位與子網格預留條號。
- 共同基準為房間 X/Y/Z 軸向無限平面，只引用具名規格；各承載面由唯一交線推導自己的 guide。
- 獨立 guide 存在與可見性分離，保留 grid I10 / I23 生成限制；R13 無法歸片仍拒絕。
- datum／spec／frame 改動需要跨面重算、預覽與原子提交；既有同面同軸局部引用限制保持。
- 範圍、逐條修改清單、交付驗收 A1–A11 與待決事項：`geometry-core/DATUM-PROPOSAL.md`。
- 實作、回歸與獨立審查已完成；實測明細見 `geometry-core/DATUM-VALIDATION.md`。A8 真瀏覽器建立／引用／預覽完成，取消／確認受自動審核拒絕仍未驗；A10 手機 runtime 未驗。主審接受此驗證範圍，未將未驗項視為通過。

### GEO-129 ✅ 已入層（2026-09-18）規格擴充：足以重建 3D 模型的確定性資料
- 使用者明示授權依建議擴充公理層；新增 D20–D25 / I26–I33 / R24–R30，保留既有預留條號。
- 定義具名法向區間擠出、可含多片同向面的邊界殼、複合空間／淨空、KEEP／UNION／DIFFERENCE、建模完整性及交換包。
- 舊 Space 保留 slot-space/1，不把槽位封閉誤稱水密；D3／D4 分離、D9 定義權威與 R8 快照語意保持。
- 確定性正交 cell 布林、標準面切分與三角化、來源特徵及摘要編碼已入規格；不得因模型／相機不同而猜另一份幾何。
- 逐條變更：`geometry-core/MODELING-CHANGES.md`；介面與驗收：`geometry-core/MODELING-CONTRACT.md`；18 組資料向量：`geometry-core/modeling-cases.json`。
- **現況：規格／白話／正典同步交付；新增 C 型別、幾何執行器、bridge、輸出與畫布功能尚未實作。** 向量只是未來驗收，不算實測通過。
- 實作順序：擠出及面輸出 → 殼拓撲／複合空間 → 正交布林 → 完整交換包與外部適配器；每個執行器先按 I32 宣告子能力。

### GEO-130 ✅ 已做（2026-09-19）實作：確定性 3D 參考執行器（後續項見條目末）
- 使用者授權「繼續實作」；不改公理條文，以 GEO-129 規格為基準。
- 完成 C 原場景 parser／World 接入與實際依賴快照，Python 精確擠出、殼、複合空間、布林及標準幾何。
- 交換包保留來源及摘要，可重建驗證；ModelWorld 提供預覽／確認／取消與失敗回滾。
- 提供 CLI、HTTP API、OBJ 匯出及帶孔牆／L 形空間範例。
- 36 項建模與 2 項傳輸整合測試通過；詳見 `geometry-core/MODELING-VALIDATION.md`。
- 後續：C World／舊 DSL 新型別整合、畫布建立與編輯、GLB／SketchUp 適配器及第二套完整引擎的跨實作驗收。

### GEO-131 ✅ 已拍板（2026-09-20）公理層見證圖：一條文一圖、圖變即警報
- 使用者定性：幾何相關條文須配示意圖，但**示意圖是條文的見證，不是文件**——
  條文為真 ⇒ 圖不變（所以沒有版本問題）；圖變了 ⇒ 是警報，代表夾具／引擎／條文之一動了，
  必須由使用者確認要改哪一邊，**絕不自動覆寫**。
- 為什麼不手繪：手繪圖跟白話一樣是人寫的，會跟條文一起錯、偵測不到漂移
  （`公理層-白話.md` 已整份落後過一次；閱讀器內 63 張例圖全標「未重新執行引擎」，
  其中 D1 例圖仍寫「奇數 gap → 拒絕」，與現行 D10a 及引擎行為相反）。引擎推導的圖才有「變了就是有事」的性質。
- 實作：`geometry-guide/witness.py`（`--build` 建圖 / `--check` 逐位元比對、有差即非 0 且不寫檔 / `--list`）
  + `geometry-guide/witness/manifest.json`（條號 → 夾具 → expect → 視圖）+ `witness/<條號>.svg`。
  沿用 `axiom_examples.py` 的 run_scene / crop_bottom / before_failure，不另做幾何或裁切。
  夾具必須在註解提到條號（`axiom_matrix.py` 同一判準），manifest 不能單獨成為連結。
  `.gitignore` 對 `geometry-guide/witness/*.svg` 開唯一例外（全域 `*.svg` 仍忽略）。
- 樣板：I19 ← `_role_rc_boundary_ok.scene`（仰視圖）。實測：同夾具兩次輸出逐位元相同；
  臨時把夾具房深 3000→3200 後 `--check` 正確報「夾具內容變了」並列 64 行 diff、rc=1、未覆寫。
- 已鋪 17 條（2026-09-20，使用者「都鋪」授權）：D2、D6、D6c、D10a、D11、D15、D16、D17、I13、I19、I22、
  R6、R7、R16、R17、R19、R21。新寫夾具 6 個（`_wit_*.scene`，已入 `tests/run_tests.py`，128/128 通過）：
  D2 牆 frame（view=all）、D6 參考線被孔切段／面外零段、D6c 三面共用 datum（view=all）、
  I13 寬 27 → footprint [987,1014]、R6 穿孔格線兩個 cell 各選一段、R19 邊界主支 2600−20−20=2560。
  既有夾具補條號註解 2 個（`_test_hole_auto` +D11、`_test_between` +R21）。
  D16 與 I22 共用 `_role_priority_ext_custom.scene`（同一現象：延伸段與其規則），圖檔仍各一張。
  `witness.py` 加 view=front/side/all（R16 看前視、R17 看側視、跨面條文看整張）。
- **暫無圖（不手繪頂替）**：D20 / D21 / D23 / R27 屬 GEO-129 `orthogonal-model/1`，
  C 核心與場景 DSL 尚未實作（I32：條文存在 ≠ 已實作），無夾具可推導；待 GEO-130 接入 C World 後補。
- 後續：閱讀器例圖槽改讀見證圖（須過 AGENTS.md 五道 assert）另開票；`公理層.md` 未動。
- 關聯決定（同日、尚未最終拍板）：使用者擬將本 repo 定性為「該領域世界的來源」，其他專案須遵守其公理；
  建議配套：舊 repo `geometry` 封存、公理層加版本號、下游以 `.scene` 夾具／契約測試證明遵守。

### GEO-132 ✅ 已做（2026-09-20）閱讀器例圖槽改讀見證圖
- 使用者指示「閱讀器例圖槽改讀見證圖,開票做」。做法:`sync_axiom_reader.py` 在每條卡片的歷史範例前
  插入 `<section class="witness-section">`,內容由 `geometry-guide/witness/<條號>.svg` **讀檔**嵌入
  (base64 data URI,引擎淺色 `<style>` 整段換成與歷史例圖相同的深色配色;非 all 視圖另附「展開三視圖」)。
  同步器**不執行引擎**——圖是否仍與夾具/引擎一致是 `witness.py --check` 的事,兩道守門不混。
- 歷史範例區塊與其批註身份原樣保留(AGENTS.md 五道 assert 不受影響;見證圖沒有 `.review-target`)。
- CSS `.witness-section` 一次性注入正典 `<style>`(冪等)。`validate()` 回報 `witness` 數量。
- 測試:`tests/test_axiom_reader.py::test_witness_figures_match_manifest_and_files`——manifest 有圖的條文
  每條恰嵌一張,且與同步器由當前檔案算出的完全相同;既有冪等測試因此成為「見證圖變了但沒重出閱讀器」的警報。
- 文件:READER-BUILD.md、AGENTS.md 補記。`公理層.md` 未動。

### GEO-133 ✅ 已做（2026-09-20）見證圖規範 v1：拓樸可見、全部同一套畫法
- 使用者指出(附截圖):20mm 料在 4000mm 房間裡只剩三條線,「角材怎麼一根一根排、誰停在誰身上」完全看不出來,
  而那正是 D15/I19/R19 的內容;並要求**所有示意圖用相同規範建立,不得各畫各的**。
- 規範:`geometry-guide/witness/規範.md`(v1)。每張固定三區——① 主圖(引擎視圖原樣,角材依角色四色著色,
  端面畫停止標記)② 接點列(每個角材端面一格,同一份幾何等比例放大,窗 = 8×料寬,格標題 `t3·END→t1` 用 D18 擋面參照寫法)
  ③ 圖例(每張相同)。沒角材的條文接點列為空,不是另一套版面。
- 拓樸來源:`witness.py` 從引擎文字輸出反推每個端面的擋面(共面 + 沿面內橫向涵蓋全寬;D11 三種來源),
  必須唯一否則失敗不出圖;結果另存 `<條號>.joints.json` 與 SVG 一起逐位元比對——**拓樸是見證本體,圖是呈現**。
  `--check` 失敗時能分辨:夾具變了 / 夾具沒變但拓樸變了 / 拓樸沒變只有幾何輸出變了。
- 反推時踩到一次:D11「涵蓋端面全寬」的寬是面內橫向,不含厚度方向(27×33 主支停在 20×20 邊界材側面合法);修正後 17/17 唯一。
- 17 張全部重出、閱讀器重出、`test_axiom_reader` 9/9、`run_tests` 128/128。`公理層.md` 未動。
- 已知:`axiom_matrix.py --strict` 本來就有 22 條紅燈(GEO-129 未實作條文、D5/D12/I11 等缺夾具),與本票無關;
  GEO-131 曾誤報「無紅燈」,是管線吃掉了退出碼,在此更正。

### GEO-134 ✅ 已做（2026-09-20）停止標記不得暗示占用；witness 自驗物理碰撞
- 使用者問「你知道物理碰撞嗎——相同空間不能同時被不同物體占用」。引擎(I11)與拓樸反推(端面共面 = 零面積接觸)都對,
  但**標註層**畫錯:停止標記中心線壓在接觸面上,一半粗度伸進對方料,看起來像穿透。
- 修:標記整條退到被裁料自己這一側(沿長度軸向內偏移半個粗度)。新增兩道自驗,違反即不出圖:
  (a) 同承載面任兩支 A0 footprint 正面積交集必須為 0(I11,witness 自己再驗一次,不依賴引擎);
  (b) 停止標記範圍不得進入擋面對方角材的 footprint。突變測試:把偏移設回 0 → `--check I22` 報「侵入」。
- 規範 §2/§4 補記;17 張重出;閱讀器重出;全部測試通過。

### GEO-135 ✅ 已做（2026-09-20）停止標記長度 = 料寬、不外延；碰撞檢查擴及所有相鄰角材
- 停止標記原本長 1.6× 料寬,外延部分會伸進貼在旁邊的另一支料——標註暗示了不存在的占用。
- 修:標記長 = 端面本身的寬、一個 mm 都不外延;`check_marks_outside` 從「只對被頂的那支」
  改為對**所有**其他角材的 A0 footprint 做正面積交集檢查,碰到即不出圖。
- 新增獨立驗證 `tests/test_witness_marks.py`(不 import witness.py,只讀 repo 內 SVG/joints.json
  用最笨的矩形交集重算):任兩角材不重疊、標記不侵入他料、每個接點在主圖都有標記。

### GEO-136 ✅ 已做（2026-09-20）接點格改 Python 內裁切,不用巢狀 viewBox
- 巢狀 `<svg viewBox>` 在多數檢視器不裁切,整個場景會不裁切地畫出來,看起來像料互相穿越。
- 修:`flat_tile()` 在 Python 裡把每個形狀(Sutherland–Hodgman 多邊形 / Liang–Barsky 線段)
  裁到視窗、算成版面座標,只輸出平面 polygon/line/rect——任何檢視器只能畫出同一個結果。
- `manifest.json` 的 D2 改 `view=front`(側視圖是牆的端面投影,兩支立料會投影重疊,
  獨立測試視為占用)。規範 §3 補記「不得用巢狀 viewBox/`<use>`/`<g transform>` 做放大裁切」。

### GEO-137 ✅ 已做（2026-09-20）停止標記改填色矩形:stroke 粗度是螢幕像素不是 mm
- 使用者一再指出圖上「藍色主支穿過琥珀色邊界材、穿過孔邊」。根因:引擎 CSS 的
  `vector-effect:non-scaling-stroke` 讓 `<line class="stop" stroke-width>` 的粗度變成
  **螢幕像素**而非 mm——圖縮小時 27mm 的料只剩約 5px,8~40px 粗的標記線直接穿過整支料。
  放大看「看起來對」、座標算「算起來對」,兩個都是假的。
- 修:`stop_mark_box()` 直接算標記矩形(端面寬 × 向被裁料內側 0.3×料寬),`stop_marks()`
  輸出 `<rect class="stop" fill=角色色>`;`check_marks_outside` 改用同一個 box;
  `flat_tile` 保留 `fill` 屬性;CSS `.stop{stroke:none}`;圖例樣本改 `<rect>`。
- `test_witness_marks.py` 同步改抓 rect/polygon 標記,新增「全檔不得出現 stroke 式 stop 標記」。
- 規範 §2 停止標記列改為填色矩形寫法。驗收方式改為**用眼睛看**:整張、480px 縮小、
  逐接點格放大三種尺度,30 格全數 Chrome 截圖目視通過(含原病徵的 t5·START→t1、
  t7·END→h0e0),閱讀器內嵌圖同版重出。
- 17 張重出、`--check` 17/17、test_witness_marks 4/4、閱讀器重出且冪等、
  test_axiom_reader 9/9、run_tests 128/128。`公理層.md` 未動。

### GEO-138 ✅ 已做（2026-09-20）閱讀器：條文瀏覽時示意圖同頁並排
- 使用者需求:翻頁式一條一頁介面下,見證圖埋在卡片下半要捲才看得到;
  希望**讀條文時對應示意圖就在旁邊**。使用者已拍板「兩者都做」:
  - 右欄 sticky 側欄,預設只顯示**主圖段落**(同一張 SVG 換 viewBox 露出主圖區,
    不重出圖、不動規範、不動 `witness.py`);可切換顯示完整三區圖;側欄可收合。
  - 完整版見證圖仍保留在卡片下方原位置,不搬走。
  - 89 條中只有 17 條有見證圖:無圖的條維持單欄,不出現空側欄。
  - 手機/窄寬不掉進並排:圖回卡片內 inline(現行版面)。
- 實作面:只動 `sync_axiom_reader.py` 模板 + CSS/JS 與 `閱讀器-設計規格.md`;
  五道 assert 必須照過;`公理層.md` 不碰。併入第 9 流閱讀器改版(GEO-114~121 之後)。

---

## 第 11 流：閱讀器可用性(2026-09-20 立;設計規格作廢後重新界定)

**來源**:外部 agent 的《公理層閱讀器 UI/UX 審查報告》16 條(R1～R16),
已逐條對現行 `geometry-guide/公理層-閱讀器.html` 用腳本核對,**數字全部屬實**
(僅檔案大小它寫 3.49 MB、現為 3.94 MB,因報告早於 GEO-137 重出)。

**依據的變更**:同日使用者拍板 `閱讀器-設計規格.md` **整份作廢**,
報告中引用該規格的論據(R16 引 §1、R3 引 §8 等)**一律不採為依據**。
改以 **GEO-120(🔒 已拍板,2026-09-17)** 為判準。交叉比對後發現:
**報告的 6 項發現其實是 GEO-120 拍板決定的回歸,不是設計偏好**——
這批屬於「違反已拍板決定」,必須修;其餘屬設計取捨,需使用者拍板後才動。

**根因(比 16 條本身重要)**:
1. 計數與版本沒有單一來源 → R2、R12、R14。
2. 色彩沒有 token 化、圖面色寫死在 base64 SVG 裡 → R6、R10、R11。
3. 「閱讀」與「校對」共用同一個版面 → R1、R5、R13。

### GEO-139 ✅ 已做(2026-09-20) 回歸修復:閱讀器違反 GEO-120 的四項拍板
- **性質**:🟢 違反 🔒 已拍板決定,不是設計偏好,直接修。
- **內容**:GEO-120 拍板了四件事,現行正典四件全破:
  1. **單頁長捲、Ctrl+F 保住**(拍板一)→ 現行 `var mode='single'`,
     `a.hidden = mode==='single' && a.id!==current`,首屏 88 條在 DOM 裡是 hidden,
     瀏覽器搜不到。(審查 R1,P0)
  2. **hover 快速預覽與點擊固定面板並存**(拍板二;原文寫「砍掉 hover 是淨損失」)
     → 全檔 grep 不到任何 hover 預覽。
  3. **雙主題、深色為預設**(拍板三)→ 現行 `<html data-theme="light">`,
     且全檔 `prefers-color-scheme` 出現 **0 次**,跟隨系統的機制也沒了。
  4. **追溯燈號/三向連結/樞紐徽章不得丟失**(連帶約束)
     → 全檔 grep `.trace` / `trace-ok` / `trace-partial` / `trace-none` / 「樞紐」皆為 **0**。(審查 R3,P1)
- **驗收**:(a) 首屏不 hidden 任何條文,瀏覽器 Ctrl+F 搜得到最後一條的條文字串;
  (b) 預設主題為深色且 `prefers-color-scheme` 生效;
  (c) 導覽項與條文 eyebrow 有追溯燈號(綠=原始碼+夾具、黃=其一、紅=皆無),資料由
  `axiom_matrix.py` 的既有判準產生,**不得手寫白名單**;
  (d) 條號連結有 hover 預覽,且點擊仍開固定參照欄。
- **檔案**:`geometry-guide/sync_axiom_reader.py`(模板與腳本)、重出正典。
- **進度**:
  - ✅ 拍板一 單頁長捲:`mode` 初值改 `'all'`,首屏 89 條全在 DOM、hidden=0(瀏覽器實測)。
  - ✅ 拍板三 深色預設 + `prefers-color-scheme`:系統深色→dark、系統淺色→light,已存偏好優先。
  - ✅ 連帶約束 追溯燈號/三向連結/樞紐徽章:**定義沿用專案原本的 `make_axiom_reader.py:431-433`,
    不自己發明門檻**——綠=原始碼且夾具、黃=其一、紅=皆無;樞紐=被引用數 ≥ 3。
    資料由 `axiom_matrix.py` 推導(唯一來源),導覽項左邊 4px 燈號、條文頭部燈號徽章與樞紐徽章、
    卡片底部「三向連結」可收合區(原始碼函式/夾具檔/變異 id)。
    實測分布:綠 54、黃 13、紅 22;樞紐 34 條。
  - ✅ 拍板二 hover 快速預覽:`a[data-ref]` 滑入即出浮卡(條號＋標題＋條文前 150 字,markdown 記號已去除),
    捲動/Esc 收起;只在 `(hover:hover)` 的裝置啟用,與觸控長按不衝突(拍板原文:砍掉 hover 是淨損失)。
    點擊開固定參照欄的行為不變,兩者並存。
- **相依**:無。**估時 3h**。

### GEO-140 計數與版本號要有單一來源
- **性質**:🟢 客觀錯誤(顯示的數字與事實不符)。
- **內容**:實際 89 條,但 `<title>` 寫「66 條」、切全文的 toast 寫「已顯示全部 66 條」、
  `#read-position` 靜態寫「12 / 63」、`#workspace-position` 寫「1 / 63」、
  `#review-count` 寫 4(說明寫 5)、`#review-revision` 寫「文字 r1」但 `<title>` 寫 r4。
  同步器已經算出 `clauses`/`comments`/`witness` 等數字,卻沒寫回 HTML 靜態值與 JS 字串。
  改為:同步器產出時把全部計數寫進**一組 `data-*` 或一個 JSON**,HTML 靜態值即真值,
  JS 一律從那裡取;**禁止在字串裡寫死數字**(含 toast)。(審查 R2 P0、R14 P3)
- **驗收**:全檔 grep 不到「66 條」「/ 63」「r1」這類硬編碼;
  `test_axiom_reader.py` 新增一項:HTML 裡出現的每個計數都等於由資料算出的值;
  首屏載入前後數字不跳動。
- **檔案**:`geometry-guide/sync_axiom_reader.py`、`tests/test_axiom_reader.py`、重出正典。
- **相依**:無。**估時 2h**。

### GEO-141 ✅ 已做(2026-09-21) 色彩 token 化;圖面色與互動色分家
- **性質**:🟢 全部可做(Q1 已於 2026-09-20 拍板 🔒)。
- **內容**:
  - head CSS 有 **40 個不同 hex**,批註系統整套色在 token 之外
    (`#c68d2a`×5、`#9a5200`×2、`#ad3424`、`#bb6c59`,深色模式再逐條覆寫 `#eac076`/`#ffb3a5`)。
    收成 `--note` / `--note-bg` / `--note-strong` / `--danger` 四個 token,兩套主題各一組,
    深色只改 token 值,刪掉逐條選擇器補丁。(R10 P2)
  - **281 張 base64 例圖與 17 張見證圖硬編碼深色底**(`svg{background:#181e24}` 等);
    淺色主題下是黑方塊。改吃 CSS 變數(`--geo-boundary`/`--geo-timber`/`--geo-guide`/`--geo-grid`),
    同步器嵌入時替換 style 段。**注意**:見證圖的深色化是 GEO-132 我方加的,屬同一問題。(R6 P1)
  - 焦點環寫死 `outline:3px solid #288b9c`,既不隨主題也不等於互動色 `--accent`;
    改 `outline:2px solid var(--accent); outline-offset:4px`。(R11 P2)
- **驗收**:全檔 CSS 規則內 grep 不到裸 hex(token 定義區除外);
  淺/深兩主題各開一次,例圖與見證圖的底色、線色都跟著主題走;
  見證圖 `witness.py --check` 仍 17/17(圖檔本身不因此改動,只有嵌入時的 style 段變)。
- **🔒 拍板(Q1)**:**只 token 化底色與線色**;見證圖的四個角色色屬 `witness/規範.md` v1、與條文語意綁定,
  **不動**,17 張見證圖不必重出。
- **進度**:
  - ✅ **批註四色 + 範例/實錄/命中色 + 圖卡底色**收成 13 個 token(`--note`/`--note-strong`/`--danger`/
    `--proposal`/`--figure-bg`/`--reject-*`/`--transcript-*`/`--hit-*`/`--link-underline`/`--sheet-ref-ink`),
    兩套主題各一組;**深色的三條逐條選擇器補丁已刪除**,值移進 `:root[data-theme=dark]`。
  - ✅ **焦點環** `outline:3px solid #288b9c` → `outline:2px solid var(--accent);outline-offset:4px`;
    `#288b9c` 全檔歸零。
  - ✅ `validate()` 與測試各加一道:CSS 規則內不得再有裸色碼(`@media print` 與 token 定義區除外)。
  - ✅ **圖「內」的顏色**(🔒 Q8:只改見證圖 17 張):見證圖改 **inline `<svg>`**,
    圖自帶的兩個 `<style>` 全部拿掉、改由 `WITNESS_DIAGRAM_CSS` 以 `.witness-diagram` 作用域提供
    (`.title`/`.label`/`.frame` 這些名字太通用,直接內聯會汙染整份文件)。
    新增 10 個 `--wit-*` token,兩套主題各一組;**角色色維持字面值不動**(🔒 Q1)。
    「展開三視圖」不再放第二份圖,改成同一個 `<svg>` 換 `viewBox`。
    右欄面板(GEO-138)改成**複製 svg 節點**而非複製 `src`。
    **實測(1440px)**:淺色 svg 底 `#eef2f5`、承載面 `#dbe9ff`、邊 `#3366cc`;
    深色 svg 底 `#181e24`、承載面 `#304557`、邊 `#84c8f6`;
    `role-primary` 兩個主題都是 `#63b3ed` —— 角色色確實沒動。
    見證圖區塊內 base64 歸零,`witness.py --check` 仍 17/17(圖檔本身未動)。
  - ⬜ **281 張範例圖維持 base64**,這是 Q8 拍板的一部分,不是遺漏。原因:
    281 張範例圖是 base64 `<img>`,`<img>` 裡的 SVG **看不到頁面的 CSS 變數與 `data-theme`**,
    只看得到系統的 `prefers-color-scheme`。要讓它們跟著閱讀器的主題切換,只有三條路:
    (a) 改成 inline `<svg>`(見證圖 17 張可行,且會比 base64 更小;281 張範例圖則會讓 DOM 爆炸)、
    (b) 出淺深兩份(檔案再大一倍)、(c) 只跟系統不跟使用者切換。
    **且範例圖被標為「歷史範例,未依本次條文重新執行」——重跑引擎重產會破壞這個語意。**
    已靠 `--figure-bg` 的圖卡底色減輕淺色主題下的突兀。
- **相依**:無。**估時 3h**。

### GEO-142 搜尋:跳轉不清空查詢;補 Ctrl/⌘K
- **性質**:🟢 客觀缺陷(功能自相矛盾)。
- **內容**:`navigate()` 內先呼叫 `resetSearch()`,把 `search.value` 清空、`activeGroup` 還原,
  所以「搜尋 → 點第 2 筆 → 想看第 3 筆」必須重打。方向鍵與 Enter 的鍵盤導覽做得很完整,
  卻在跳轉那一刻被自己清掉。改為:跳轉後保留查詢字串與命中清單,導覽顯示「第 n / m 筆」,
  Enter 連續跳下一筆,只有 × 或 Esc 才清空。(R7 P1)
- **對審查的更正**:R7 另稱「沒有全域聚焦搜尋的快捷鍵(規格 §4.4 要求 Ctrl+K)」——
  **不成立**。`reader-script` 早有 `document.addEventListener('keydown',…(e.ctrlKey||e.metaKey)&&e.key==='k'…)`,
  會 `openDirectory()` 並 `search.focus()`,實測可用。本票不含此項,只保留防回歸檢查。
- **驗收**:搜一個詞、連按 Enter 能依序走完所有命中且查詢字串不變;Esc 清空;Ctrl+K 聚焦。
- **相依**:無。**估時 1.5h**。

### GEO-143 ❎ 不需要做(2026-09-20,實測推翻前提) 效能:例圖延後載入
- **性質**:🟢 可量測。
- **內容**:3.94 MB 單檔,281 張例圖全部 base64 內嵌,首屏一次付清
  (審查實測在預覽容器內 7 秒未完成排版)。單檔自足是刻意取捨(拍板 1),不動;
  但把預設收合的範例圖改成 `<template>` 內的原始 SVG、展開時才注入 DOM,
  或 `loading=lazy` + IntersectionObserver 延後解碼。優先處理 141 筆範例中預設收合的那些。(R9 P2)
- **驗收**:首屏可互動時間(以 DOMContentLoaded 後可捲動為準)明顯下降並記錄實測值;
  展開任一範例仍看得到圖;五道 assert 與冪等測試全綠。
- **實測(2026-09-20,Chromium,桌面 1440×900,本機 http)**——**前提不成立,不動它**:

  | 量測項 | 值 |
  |---|---|
  | `domContentLoaded` / `loadEventEnd` | **754ms / 758ms** |
  | 強制 layout | **0ms** |
  | 捲到底(頁高 101,459px) | **7.4ms** |
  | 展開 30 個收合範例 | **0.2ms** |
  | JS heap | **2MB** |
  | 282 張圖中 `complete=false` | **280 張** |
  | 282 張圖中 `naturalWidth=0` | **279 張** |

  **決定性的一項是最後兩列**:`loading="lazy"` 對 `data:` URI **是有效的**——
  282 張圖裡只有 2 張真的載入過,其餘連解碼都沒開始
  (`img.decode()` 對離屏的 lazy 圖根本不會 settle,我第一次量就是這樣掛了 45 秒)。
  也就是說本票想做的「延後載入」**瀏覽器早就做了**,而審查說的
  「281 張內嵌圖,首屏成本全付在載入時」**與事實相反**——首屏只付 HTML parse。

- **順手驗過的另一條路也不成立**:把 base64 改成 URL 編碼的 SVG。
  實測 base64 酬載 2.13MB、原始 SVG 1.60MB、URL 編碼後 **2.40MB**——
  因為圖裡有大量中文標籤要百分比編碼,**改了反而大 7%**。
- **唯一還在的成本**是 3.82MB 檔案本身的 parse(桌面約 750ms)。
  在拍板 1「單檔自足」不變的前提下,唯一能減的是把 281 張圖改成 inline `<svg>`
  (省掉 base64 的 4/3 膨脹,約 0.53MB),代價是 DOM 節點從 14,189 大約翻倍——
  **拿 14% 檔案換兩倍 DOM,不划算**。
- **未量到的情況(誠實標記)**:以上全在桌面 Chromium 量。低階手機的 parse 成本、
  以及 Firefox/Safari 是否同樣對 `data:` URI 套用 lazy,**都沒驗**。
  若日後在實機上真的慢,再回來開票,並且**要帶實機數字**,不要再用推測。
- **相依**:無。**改判:不做**。

### GEO-144 ✅ 已做(2026-09-21) 批註過期引文就地可重新綁定
- **性質**:🟢 可做(Q2 已於 2026-09-20 拍板 🔒)。
- **內容**:4 處 `.stale-note` 只寫「段落已改版;以下引文保留批註當時的快照,不自動重新配對」,
  但 `reanchor()` 只出現在「全部批註」清單的動作列,且要先過一個 `confirm()`。
  讀者在正文看到過期批註時沒有任何可點的下一步。建議:就地提供「重新綁定這段 / 看原引文」,
  `confirm()` 改為面板內的前後對照 + 主鈕。(R8 P1)
- **驗收**:過期批註可在正文就地重新綁定,且綁定前看得到前後差異。
- **🔒 拍板(Q2)**:就地提供「重新綁定這段」;拿掉 `confirm()`,改成面板內前後對照 + 主鈕;綁定後可復原一次。
- **實作**:`noteHTML()` 在 `anchorState!=='exact'` 時就地加一列動作(重新綁定這段 / 回到段落);
  `anchorHistory` 非空時另加「復原綁定(回到上一個定位)」。
  `reanchor()` 從一個 `confirm()` 改成 `dialog()` 面板:左「批註當時的引文」、右「目前的段落」,
  段落已不存在時不給主鈕並明說原因。新增 `reanchorConfirm()` / `undoReanchor()` 與對應 action 分派。
- **實測**:2 則過期批註各有就地動作列;點「重新綁定這段」開出標題
  「重新綁定 D1 · 原文 第1段」的面板,含「批註當時的引文 / 目前的段落」兩欄與確定鈕;
  全檔不再有舊的 confirm() 文案。
- **相依**:無。**估時 2h**。

### GEO-145 ✅ 已做(2026-09-20) 正文不常駐批註按鈕
- **性質**:🟢 可做(Q3 已於 2026-09-20 拍板 🔒)。
- **內容**:452 組 `.review-block > .block-tools` 每段固定掛一列(段落標籤 + 「＋批註這段」),
  純閱讀時與正文等權,每段之間插進 34–44px 控制列。建議改 hover/focus/長按才出現;
  已有批註的段落保留常駐琥珀左邊條與批註數徽章。(R5 P1)
- **驗收**:純閱讀時正文不被控制列切碎;觸控裝置仍有可達的批註入口;既有批註仍一眼可見。
- **🔒 拍板(Q3)**:改 hover / focus / 長按才出現;已有批註的段落保留常駐琥珀左邊條與數字徽章。
  **驗收另加一項:觸控裝置長按不得與瀏覽器原生選字衝突,須實機驗。**
- **實測**:452 個段落中 **447 個工具列收合成 0×0(opacity 0)**,只有 5 個有批註的段落常駐;
  鍵盤 Tab 進按鈕時 `:focus-within` 會展開,所以沒有「看不見卻可聚焦」的死角。
  觸控長按 500ms 展開且**不 preventDefault**,原生選字手勢仍可用;手指一移動即取消。
  ⚠ 觸控長按與原生選字並存這點是在桌面瀏覽器以事件模擬驗的,**尚未實機驗**(驗收條件仍掛著)。
- **相依**:無。**估時 2h**。

### GEO-146 ✅ 已做(2026-09-20) 參照欄與批註面板並存,不互相關閉
- **性質**:🟢 可做(Q4 已於 2026-09-20 拍板 🔒);與 **GEO-138** 合併施工。
- **內容**:`workspace-script` 的 `docked()` 模式下 `present(id)` 會把另一個面板 `hidden`,
  所以寫批註時點正文裡的條號連結,草稿面板直接被參照面板換掉;草稿只在
  `visibilitychange`/`beforeunload` 時 `captureDraft()`,切 tab 不觸發。
  校對的核心動作正是「一邊對照引用、一邊寫批註」,現在互斥。(R13 P2)
- **驗收**:讀引用與寫批註可同時存在;切換前草稿必被保留且有可見提示。
- **🔒 拍板(Q4)**:右欄改**上半固定見證圖(GEO-138)+ 下半 tab(參照/批註)**;
  切 tab 前一律先 `captureDraft()` 並顯示「草稿已保留」。見證圖常駐,不與參照/批註互斥。
- **實作**:`present()` 在 dock 模式下若從批註分頁切走,先 `window.axiomReviewUI.flushDraft()`
  再 toast「草稿已保留」。原本只有 `showReference()` 這一條路會 flush,從其他入口切換就會丟草稿。
  分頁本身維持「參照 / 批註」二選一(🔒 Q4 拍板:上半見證圖常駐、下半才是 tab)。
- **相依**:與 GEO-138 同一批施工。**估時 3h**。

### GEO-147 資訊層級:原文與白話的順序
- **性質**:🟢 可做(Q5 已於 2026-09-20 拍板 🔒)。**注意**:舊依據(設計規格 §4.2)已作廢,
  但頁尾文案「原文為準,白話輔助閱讀」與現行版面順序(白話在前)自相矛盾,這點客觀成立。
- **內容**:89 條一律 `plain-section` 先於 `original-section`;區塊標籤「白話解釋/條文原文」
  同為 14px h3,兩者同重。建議順序改 原文 → 白話 → 範例 → 見證圖 → 被引用,
  區塊標籤降為 12px/.08em muted。(R4 P1)
- **驗收**:順序與頁尾宣稱一致;五道 assert 全綠(區塊 id 與批註錨點不得因換順序而失聯)。
- **🔒 拍板(Q5)**:順序改 **原文 → 白話 → 範例 → 見證圖 → 被引用**;區塊標籤降為 12px/.08em muted。
- **相依**:無。**估時 1.5h**。

### GEO-148 ✅ 已做(2026-09-20) 斷點 960–1279px 與手機底部列
- **性質**:🟢 可做(Q6 已於 2026-09-20 拍板 🔒)。舊依據(設計規格 §1)已作廢,本票依 Q6 重新界定。
- **內容**:
  - `dockQuery=matchMedia('(min-width:1280px)')`,960–1279px 之間左欄已是固定導覽、
    右欄卻還沒出現,點條號走 `showModal()` 把正文整個蓋掉——與右欄文案
    「對照引用,不離開正文」矛盾。建議改底部半高 sheet。(R16 P3)
  - 手機底部列擠 5 個控制,`gap:3px`、按鈕 13px、位置指示 11px/最小寬 35px,359px 以下再降 12px。
    建議只留「目錄·上條·位置·下條」,批註入口移到條文內與頂列。(R15 P3)
- **驗收**:960/1100/1279px 三個寬度下點條號不蓋住正文;390px 下底部列字級 ≥14px 且無溢位。
- **🔒 拍板(Q6)**:中間寬度用**底部半高 sheet**;手機底部列只留四鍵,批註入口移到頂列。
- **實作**:中間寬度改用 `el.show()`(**非模態**)而非 `showModal()`——這是關鍵,
  模態即使把 backdrop 設透明,正文仍然不能操作,達不到「對照引用,不離開正文」。
  新增 `halfQuery`(960–1279px)與 `body.half-sheet-open` 讓位 padding,dialog 關閉時收回。
- **實測**:
  - 1100×860:sheet `open=true`、`:modal=false`、`position:fixed`、貼底、高 430px(正好半屏),
    `D6` 條文仍在畫面上 → 正文與引用同時可見**且可操作**。
  - 375×812:底部列剩「目錄 / 上條 / 1 / 89 / 下條」**四鍵**,按鈕 14px、位置 12px(原 13px/11px);
    「全部批註 5」已出現在頂列。
- **相依**:無。**估時 2h**。

### GEO-149 ✅ 已做(2026-09-20) 證據強度可見:哪些條有範例/見證圖
- **性質**:🟢 資料驅動(數字客觀);呈現方式併入 GEO-139 的燈號。
- **內容**:89 條裡 63 條有範例(26 條沒有)、17 條有見證圖(72 條沒有),
  但導覽與條文頭部沒有任何標示,讀者得逐條點開才知道這條是不是「只有文字」。
  在導覽項與 eyebrow 標「例 N · 見證圖 N」,導覽頂端給以真實資料為準的篩選 chip
  (有批註/有例圖/有見證圖/無證據);**禁止硬編碼條號白名單**。(R12 P2)
- **驗收**:標示數字等於實際數量(與 GEO-140 同一份計數來源);篩選 chip 結果與實際相符。
- **進度**:✅ 導覽項標「例 N · 見證圖」並帶 `data-trace/data-ex/data-wit/data-hub/data-note`;
  ✅ 導覽頂端四個篩選 chip(有批註 5 / 有例圖 63 / 有見證圖 17 / 無追溯 22),數量由資料算,
  **無硬編碼條號白名單**(被作廢的第 3 版原型正是寫死 `['R6','R18','R19','R20','R21']`)。
  與搜尋、分類篩選疊加——實測 89 → 點「有見證圖」17 → 再搜「參考線」4 條。
- **相依**:GEO-139、GEO-140。**估時 1.5h**。

---

## 第 0～8 流稽核結果(2026-09-20,fresh-context agent 唯讀盤點)

舊工單(GEO-001～083,實際 52 張;BACKLOG 開頭自稱 46 張是錯的)立於 2026-09-12,
從未標過完成狀態。2026-09-20 派 agent 以 repo 實況逐張核對(唯讀,未編譯未跑測試),
判準只採客觀證據(檔案存在與否、`current_geometry.c` 的函式/字串、`run_tests.py` 的 TESTS、夾具檔)。

**統計:已完成 19、未完成 24、已不適用 8、無法判定 1。**

### 仍值得做(依價值排序,agent 判斷)

1. **GEO-075** 下料清單加總同規格數量——離「能拿去現場用」最近的一步
2. **GEO-043** Space 尺寸/體積報告(W×D×H)——六面封閉都判得出來,卻不印房間淨尺寸
3. **GEO-030** `CreateFontW` 失敗未判 NULL 就 `SelectObject`——GDI 視窗真實當機風險
4. **GEO-014** BOM 檢查補 `length>=3`——一行修法,消除讀未初始化記憶體的隱患
5. **GEO-041** Space 錯誤訊息分類——六種失敗原因擠成一句話
6. **GEO-077** scene `include`——上百個 `.scene` 夾具重複房間宣告,維護成本高
7. **GEO-020** 負值像素捨入——拖曳參考線到視圖負值區仍有 1mm 偏移
8. **GEO-035** `WM_CREATE` 控制項 NULL 防護
9. **GEO-081** scene parser fuzz——延續既有 128 測試 + 40 變異測試的品質文化
10. **GEO-053** 檔頭功能清單更新——完全沒提 room/space/grid/RC/delete/apply-proj

### 建議標作廢(已不適用,且是被後續設計**刻意取代**,不是忘了做)

GEO-001、004、018、022、023、052、070、072。
例:GEO-022「跨角材拾取取最近者」已被公理 **R1 畫家演算法**取代;
GEO-023「錨點加已過期標記」已被 **R2 重放/重算**結構性解決;
GEO-018「scene 格式文件」已由 `公理層.md`(SSOT)承載。

### 稽核過程發現、BACKLOG 沒寫的缺口

1. BACKLOG 開頭的工單統計數字錯誤(46 vs 實際 52)。
2. 全檔 **0 處**使用 C `assert()`,但 3 張工單的驗收條件明寫要加 assert——制度與實作風格對不上。
3. `guide_line_intersection` / `ANCHOR_AT_GUIDES` / `at-guides` 整條「兩線交點錨點」**疑似死碼**
   (該函式全檔僅一處定義、未被呼叫),GEO-123 已廢除 `at-guides` 語法卻沒有工單追蹤該砍還是該修。
4. 第 3 流(GDI/Win32 互動層)**完全沒有自動化回歸測試覆蓋**,卻是七張裡六張未完成的高風險區。
5. `current_geometry.c` 檔頭沒有像 `ARCHITECTURE.md` 那樣自曝「已過時」。

### 逐張表格

> 稽核方法：唯讀比對 repo 實況（current_geometry.c 用 Python 二進位解碼；當時檔內仍有 NUL byte，2026-09-21 起已無，CRLF 仍在）、
> tests/run_tests.py、AGENTS.md/ARCHITECTURE.md/公理層.md、geometry-web/、geometry-guide/。
> 未編譯、未跑測試。current_geometry.c 全檔 0 處使用 C `assert()`——凡工單驗收條件明寫「加 assert」
> 但實作用註解/return false 達成同等效果者，仍記已完成，於理由欄註明。

## 第 0 流：基礎設施

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-001 | 已不適用 | 無 build.bat/build_debug.bat；tests/_clw.bat:1-3、package.json:6-7 | 建置已演化為 gcc(Unix)+ tests/_clw.bat/_cl.bat 參數化 cl 編譯（多檔架構：current_geometry.c/web_bridge.c/model_base.c），非單一 exe 的 root build.bat 設計 |
| GEO-002 | 已完成 | tests/run_tests.py:1-90+ | 完整測試執行器，比對 exit code/stdout/lengths/contains，收錄遠超原始需求的案例數 |
| GEO-003 | 已完成 | tests/run_tests.py:26-27（ceiling-a.scene / demo-two-timbers.scene 皆 expect accept） | 兩檔都已改新語法並通過 |
| GEO-004 | 已不適用 | 無 README-geometry.md；tests/README.md:1-40、ARCHITECTURE.md、geometry-core/README.md | 單檔 CLI 說明文件的前提已不成立，build/test/使用說明改分散到多個 README，系統已是多元件（core/web/GDI） |

## 第 1 流：解析層與輸入面

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-010 | 已完成 | current_geometry.c:43-47(COORD_LIMIT/coord_in_range), 6051-6064(parse_coord) | 上限 ±1e8 mm，parse_coord 檢查並設 g_coord_range_error |
| GEO-011 | 已完成 | current_geometry.c:2467-2486(mul_div_i64) | 用 __int128（gcc/clang）或 _mul128/_div128（MSVC）widen 乘法，註解寫明安全域推導，比原案的 assert 更徹底 |
| GEO-012 | 已完成 | current_geometry.c:11713-11722 | fgets 後檢查 `length>0 && 非\n && !feof` 才判太長，避免誤殺合法末行 |
| GEO-013 | 已完成 | current_geometry.c:3579(SCENE_MAX_LINE=2048), 11709 | buffer 遠大於原 511 字元邊界，與 GEO-012 同一段邏輯處理 |
| GEO-014 | 未完成 | current_geometry.c:11726-11732 | BOM 檢查仍只判 `line_no==1`，未檢查 `length>=3` 就讀 text[1]/text[2]，未初始化記憶體讀取風險依舊（C6387 模式未消） |
| GEO-015 | 未完成 | current_geometry.c:11813-11838(main argv 迴圈) | 迴圈只有 if/else if 四支，無 else 分支：未知參數被靜默忽略，無 --help |
| GEO-016 | 未完成 | current_geometry.c:11836 | `bench_iters = atoi(argv[++i]);` 仍用 atoi，無型別/範圍驗證 |
| GEO-017 | 已完成 | current_geometry.c:11683-11686 | 「不認得的指令」錯誤訊息硬編列出 11 個指令名（非動態拉表，但達成驗收：訊息含全部指令） |
| GEO-018 | 已不適用 | 全庫無 SCENE-FORMAT.md；公理層.md「新語法」節、geometry-core/README.md | scene 語法規格已改由 公理層.md（SSOT）承載，且語法已演化（spec/at-line/at-face/role/between 等），與原案設想的靜態文件形式不同 |

## 第 2 流：幾何核心正確性

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-020 | 未完成 | current_geometry.c:4710-4711 | gdi_screen_to_view 仍用 `(Coord)(v+0.5)`，非 floor/llround，負值捨入偏移問題依舊 |
| GEO-021 | 已完成 | current_geometry.c:3083-3087, 3107-3111 | det==0 語意已寫成註解（表面退化成線 / 答案非整數 mm 兩種拒絕情形），全檔不用 assert 是專案風格 |
| GEO-022 | 已不適用 | current_geometry.c:3223-3278（尤 3267-3278），公理 R1 註解 | 命中判定已正式定為「畫家演算法：同點多命中取最後畫的」（公理 R1），非原案建議的 distance4 最近者方案——是刻意的設計決定，取代而非達成原 ticket |
| GEO-023 | 已不適用 | current_geometry.c:3600-3614, 11915-11921；公理層.md:104(D7 不存凍結 uv), 428(R2) | 錨點系統改為引用制，移動參考線會重放（重算）所引用的角材（R2，2026-09-18 拍板），結構性解決比「印已過期標記」更徹底；僅 ANCHOR_AT_GUIDES 一種錨法仍標「交點凍結」屬另一個獨立設計決定 |
| GEO-024 | 未完成 | current_geometry.c:1230-1246（guide_line_intersection 全檔僅此一處，且未被任何函式呼叫） | 仍只靠 placement_id 比對間接拒絕跨面組合，無「參考線不在指定面上」專屬訊息；且此函式疑似死碼，舊 at-guides 兩線交點錨點路徑現況不明（見缺口 3） |
| GEO-025 | 已完成 | current_geometry.c:2580-2583, 2615 | timber_project_faces 註解已寫明退化面跳過策略、繪製與拾取共用同一份投影 |
| GEO-026 | 已完成 | current_geometry.c:1078-1086（`>=`/`<=`允許邊界值） | offset 允許與邊界重合，決定已正式收錄為公理 I7（比原案設想的 SCENE-FORMAT.md 記錄更正式） |

## 第 3 流：GDI / Win32 層

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-030 | ✅ 已完成(2026-09-21) | current_geometry.c `gdi_text` | 失敗時不換字型,也不拿 NULL 去還原 |
| GEO-031 | 未完成 | current_geometry.c:4013-4018 | gdi_color 未檢查 `hex[0]=='#'`或長度，直接 `strtoul(hex+1,...)` |
| GEO-032 | 未完成 | current_geometry.c:5824-5847 | bench_paint 的 sink/sink_bmp 建立失敗分支仍未釋放已取得的 screen DC |
| GEO-033 | 未完成 | current_geometry.c:4721, 5216-5217 | g_edit_orig_proc 仍是全域 WNDPROC，未改 SetWindowSubclass 或存於視窗自身 |
| GEO-034 | 無法判定 | current_geometry.c:4149-4155（owned 欄位行內註解） | 只有一行「true=未進快取用完要刪」的行內註解，未見整理成完整所有權表，也無 assert，證據不足以判定達成或未達成 |
| GEO-035 | ✅ 已完成(2026-09-21) | current_geometry.c `WM_CREATE` | 五個控制項任一為 NULL 即回傳 -1,讓視窗開不起來而不是半套 |
| GEO-036 | 未完成 | current_geometry.c:4745-4764（gdi_layout_input_bar） | 視窗極小時 `w-176` 等寬度運算無下限防禦，MoveWindow 可能收到負寬 |

## 第 4 流：房間（room→space）功能收尾

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-040 | 已完成 | room_box.scene（檔案存在）；tests/run_tests.py:29 | 六面盒範例檔存在且已收錄於測試 |
| GEO-041 | 未完成 | current_geometry.c:11208-11213（apply_space_line） | space_construct 失敗仍只回一句把六種原因全部列出的通用訊息，未分類 |
| GEO-042 | 未完成 | 全檔搜尋「房外面」「歸屬」皆無關聯命中 | 找不到 space 成員歸屬合理性警告的任何字串或邏輯 |
| GEO-043 | 未完成 | current_geometry.c:11898-11912 | 空間報告只印 ID/成員/開放狀態，無尺寸（W×D×H）或質心 |

> 註：room 概念已整體演化為 Space（`room_bind`→`space_construct`，current_geometry.c:6299-6302 註解「與舊 room_bind 同構」），GEO-040/041/042/043 的評估對象已改為 Space 等價功能。

## 第 5 流：文件與導讀同步

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-050 | 已完成 | geometry-guide/check_panels.py:92-112 | check_panels.py 機制已整個改寫為動態讀 HTML `data-panel` 屬性比對，原 ticket 描述的硬編字串比對缺陷已不存在 |
| GEO-051 | 已完成（部分無法完全確認） | geometry-guide/current_geometry-導讀.html（內嵌原始碼含 canvas-pos/apply-proj/space_construct 等最新符號） | 導讀頁持續與原始碼同步；但原案要求的「§room 章節」因 room 已改名 Space，是否有對應章節未能直接確認 |
| GEO-052 | 已不適用 | 全庫搜尋無 asm-analysis.md | 檔案不存在，組譯附錄式文件已被 公理層.md/ARCHITECTURE.md/geometry-core 系列文件取代 |
| GEO-053 | 未完成 | current_geometry.c:14-37（檔頭「目前整合版」清單） | 仍停在原始 8 步，未提及 room/space/grid/RC/delete/apply-proj 等後續功能，與 ARCHITECTURE.md 自陳「已過時」呼應（但 ARCHITECTURE.md 至少自曝過時，檔頭沒有） |

## 第 6 流：程式碼衛生

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-060 | 已完成 | current_geometry.c:1（僅1處 #include <errno.h>）, 10946/11479（(void)count） | 重複 include 已消除、count 參數消警告模式已見；未實際編譯確認 0 警告 |
| GEO-061 | 已完成 | tests/_clw.bat:3, geometry-web/build.bat:4 | 編譯腳本皆帶 `/utf-8` |
| GEO-062 | 未完成 | current_geometry.c:3502-3553（emit_svg_three_views） | 僅檢查 `fclose(out)==0`，無 ferror 檢查，也未刪除半成品 SVG |
| GEO-063 | 未完成 | current_geometry.c:3532-3533 等（text_mm 共5處） | StyleSpec 欄位仍叫 text_mm，未更名 text_px |

## 第 7 流：新功能

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-070 | 已不適用 | SCENE_COMMANDS（current_geometry.c:11553-11649）無 unplace | 被 delete + 重宣告的交易式工作流取代（見 GEO-071） |
| GEO-071 | 已完成 | current_geometry.c:11634-11638；BACKLOG.md「WEB-001 ✅ 已完成」段 | delete 指令存在，涵蓋 boundary/placement/guide/grid/timber/space/column/beam，走交易重驗路徑，比原案墓碑方案更完整 |
| GEO-072 | 已不適用 | tests/run_tests.py（`_test_collide.scene` expect reject error 'R6'） | 碰撞已由「警告」升級為公理 R6 直接拒絕，比原案更嚴格的設計決定 |
| GEO-073 | 已完成 | 公理層.md「新語法」表；current_geometry.c:11584-11586 | guide 位置引用式支援 edge:/spec:/vertex:/grid: 等任意運算組合，涵蓋且超越原案的 edge 基準語法糖 |
| GEO-074 | 未完成 | current_geometry.c:1790/6443/7957（函式名仍為 timber_place_a0_on_surface） | 仍硬綁 A0 面貼面，找不到 B0 貼面或 face 欄位的證據 |
| GEO-075 | ✅ 已完成(2026-09-21) | current_geometry.c `print_cut_list()` | 2026-09-21 補做:同規格加總 + 房間內部尺寸,驗收已進 run_tests |
| GEO-076 | 未完成 | current_geometry.c:5436-5600（WM_MOUSEMOVE） | 找不到滑鼠即時 mm 座標寫進狀態列的邏輯 |
| GEO-077 | 未完成 | current_geometry.c:11553-11649（SCENE_COMMANDS 無 include） | scene 檔案引入/分段語法未實作 |
| GEO-078 | 已完成 | geometry-web/web_bridge.c:4,15,30,117 | 提供完整 stdin/stdout JSON 橋，涵蓋且遠超原案的單次 --emit-json 輸出 |

## 第 8 流：結構演化

| 工單 | 狀態 | 證據 | 理由 |
|---|---|---|---|
| GEO-080 | 已完成 | tests/test_core_integrity.c:1-20（`#define main geometry_program_main` + `#include "../current_geometry.c"`） | 機制不同於原案 CG_NO_MAIN ifdef，但同樣達成「直接呼叫內部 static 函式並斷言」的目標 |
| GEO-081 | 未完成 | tests 目錄檔案列表（無 fuzz_scene.py） | tests/mutate.py 是變異測試（改程式碼），非輸入層 fuzz（隨機 token/截斷），目的不同 |
| GEO-082 | 未完成 | 全庫搜尋無 split-plan.md | 拆檔計畫文件未寫；專案已用 .inc（transactions.inc/references.inc 等）局部拆分，但無明文計畫 |
| GEO-083 | 未完成 | tests/_clw.bat、tests/_cl.bat、geometry-web/build.bat 全文 | 找不到 /analyze 或 /RTC1 相關建置腳本 |

---

## 統計

- 已完成：19（002,003,010,011,012,013,017,021,025,026,040,050,051,060,061,071,073,078,080）
- 未完成：24（014,015,016,020,024,030,031,032,033,035,036,041,042,043,053,062,063,074,075,076,077,081,082,083）
- 已不適用：8（001,004,018,022,023,052,070,072）
- 無法判定：1（034）
- 合計：52（BACKLOG 自稱 46，數字有誤）

## 建議施工優先序（真的還沒做、現在仍值得做）

1. **GEO-075** 下料清單加總——專案的實際用途是木作施工，逐支列印座標但不加總同規格數量，是離「能拿去現場用」最近的一步。
2. **GEO-043** Space 尺寸/體積報告——六面封閉都判出來了卻不印房間淨尺寸 W×D×H，基本實用資訊缺口。
3. **GEO-030** CreateFontW 失敗未判 NULL——GDI 互動視窗的真實當機風險，修法只要加一個 if。
4. **GEO-014** BOM 檢查補 length>=3——一行修法即可消除讀未初始化記憶體的隱患，CP 值最高。
5. **GEO-041** Space 錯誤訊息分類——六種失敗擠成一句話，且現在的 Space 比舊 room 更複雜，除錯需求更高。
6. **GEO-077** scene include——上百個 `.scene` 夾具有大量重複房間宣告，include 能顯著降低維護成本。
7. **GEO-020** 負值像素捨入——拖曳參考線到視圖負值區時仍有 1mm 偏移，互動正確性問題。
8. **GEO-035** WM_CREATE 控制項 NULL 防護——控制項建立失敗會對 NULL HWND 呼叫 API 的當機風險。
9. **GEO-081** scene parser fuzz——專案已有 128 項測試+40 個變異測試的品質文化，補上輸入層 fuzz 是自然延伸。
10. **GEO-053** 檔頭功能清單更新——完全沒提 room/space/grid/RC/delete/apply-proj，對新進 agent/讀者高度誤導。

## 建議標記作廢（已不適用）

- GEO-001（build.bat）——建置架構已演化為多檔 gcc/cl 參數化編譯。
- GEO-004（README-geometry.md）——單檔 CLI 說明前提不成立，文件已分散且更完整。
- GEO-018（SCENE-FORMAT.md）——已被 公理層.md 取代為 SSOT。
- GEO-022（distance4 最近拾取）——已被公理 R1「畫家演算法」取代，是刻意設計決定。
- GEO-023（過期錨點標記）——已被 R2「移動即重放」結構性解法取代。
- GEO-052（asm-analysis.md 標版本）——檔案已不存在，組譯附錄形式已被淘汰。
- GEO-070（unplace 指令）——已被 delete+重宣告工作流取代。
- GEO-072（碰撞警告）——已被公理 R6 硬性拒絕取代，比原案更嚴格。

## 盤點過程中發現的缺口（BACKLOG 沒寫，明顯該補）

1. **BACKLOG 自身統計數字錯誤**：統計行自稱「總數 46 張」，實際逐行數到 52 張（010~018 是 9 張不是想像中的較少、070~078 是 9 張等）——連審計基準點本身都不可靠，應先修統計行再談別的。
2. **assert() 制度與實作風格根本不合**：全檔 0 處使用 C `assert()`，但 GEO-011/021/034 三張工單的驗收條件都明寫「加 assert」——應該是工單描述過時要改，而不是繼續期待有人去補從未出現過的模式。
3. **`guide_line_intersection`／ANCHOR_AT_GUIDES／at-guides 整條「兩線交點錨點」路徑疑似死碼**：函式定義了但全檔無人呼叫，卻仍在 AnchorKind enum 與報告文字（「參考線交點」）中占一席之地——沒有工單記錄這條路徑該砍還是該修，文件（GEO-024）、實作（死碼）、印出邏輯三者對不上。
4. **第 3 流（GDI/Win32 互動層，GEO-030~036）完全沒有自動化回歸測試覆蓋**：tests/run_tests.py 全部跑 `--no-window`；七張工單裡六張未完成，卻是全專案唯一「改壞了不會被測試網接住」的模組，風險遠高於其他流，應優先建立至少手動驗收清單或有限度的 GDI 煙霧測試。
5. **current_geometry.c 檔頭注解沒有「已過時」自我標記**：ARCHITECTURE.md 已經在檔頭加警語承認過時並指向 公理層.md，但 current_geometry.c 自己的檔頭（GEO-053 想修的那段）完全沒有類似警語，對照專案「SSOT 優先、過時文件要自曝」的紀律不一致。

### GEO-150 ✅ 已做（2026-09-20）專案清理：移除失去依據的設計原型、給第二支產生器上閘門
- **起因**:使用者問「公理層閱讀器是唯一的嗎」。實地掃描結果:**是唯一的**——
  全 repo 15 個 `.html` 裡,只有 `geometry-guide/公理層-閱讀器.html` 含 `clause-data`/`axiom-review-data`;
  無 `dist/`、無離線版、無 `.bak`、無手機版分身。但掃出三個鬆動處,使用者指示「一併處理,我要乾淨的專案」。
- **移除 `geometry-guide/axiom-reader-design/`**(38 檔、21MB,占當時 repo 36%):
  第 3 版 React 設計原型,它服務的 `閱讀器-設計規格.md` 同日整份作廢,於是失去依據。
  **完整內容仍在 git 歷史**,考古用 `git show`,不要 checkout 回工作區。repo 58MB → 35MB。
- **`make_axiom_reader.py` 加寫檔閘門**:它產的是追溯診斷頁不是正典,但一跑就會在 repo 生出
  第二份像閱讀器的檔案。文字規則擋不住誤跑,改成機制——預設寫系統暫存目錄;
  `--in-repo` 才寫進 repo,且**正典存在時一律拒絕**並要求改用 `sync_axiom_reader.py`。實測拒絕成功。
- **清掉本機殘留**:`verify-GEO-137/`(前一個 agent 的 GEO-137 目視驗收產物)、`current_geometry.svg`、
  `current_geometry.obj`、兩個 `__pycache__/`。這些因為 `.gitignore` 是允許清單制而被歸為 ignored,
  **不會出現在 `git status`**——所以先前的「工作目錄乾淨」是假的。
  另停掉三支前一個 session 遺留的 `python -m http.server`(8765/8766/8791),其中一支卡住
  `verify-GEO-137/` 使其無法刪除。
- **連帶更新**:`AGENTS.md`、`CLAUDE.md` 改寫對應段落;`決策佇列.md` 新增 Q7
  (`make_axiom_reader.py` 714 行要留還是刪,與 `axiom_matrix.py` 功能重疊)。
- **驗收**:`test_axiom_reader` 12 項、`witness --check` 17/17、`test_witness_marks` 4 項、
  五道 assert 全綠;ignored 殘留只剩 `.claude/`(本機設定,正常)。

**GEO-138 實作紀錄(2026-09-20)**:右欄插入 `#workspace-witness`,位置在 `#dock-hub` 與
`.workspace-tabs` 之間——**上半固定見證圖、下半才是分頁**(🔒 Q4)。
圖直接取自條文卡裡那張的 `src`(同一個 data URI),**不另存第二份**,所以不增加檔案大小。
掛在 `sync()` 本來就會派發的 `axiom:current` 事件上,不必改 `sync()`。
只在 `min-width:1280px` 出現;窄螢幕維持卡片內 inline(拍板的第四點)。
實測 1440px:I13 顯示見證圖(13.7KB data URI)、D1 無圖時顯示「這一條沒有見證圖(89 條中有 17 條有)」,
右欄子元素順序 `dock-hub → workspace-witness → workspace-tabs → workspace-panels`。

### GEO-151 ✅ 已做（2026-09-21）補丁登記簿：讓「補丁被靜默跳過」變成不可能

- **起因**：使用者指出我反覆弄壞東西，而且「已經習慣了」。這不是偶發，是方法問題。
- **實際發生過的失效**（2026-09-20/21 一天之內四次，全在 repo 檔案上）：
  1. CSS 注入的守衛字串與實際插入的內容對不上 → 每重建一次就再插一次（踩兩次：GEO-147、GEO-139）。
  2. 保留歷史範例的切片終點沒涵蓋新區塊 → 見證圖 17→33、三向連結 89→136。
  3. `force()` 把 `changeMode()` 裡同形的尾巴誤判成「已套用」→ **補丁整個被跳過，沒有任何人會知道**。
  4. 同一段被兩個補丁先後修改 → 第二個把第一個的「改後」改掉，重建時兩邊都認不得。
- **根因**：補丁是對一份**會演化的產物**做文字替換，而「有沒有套用過」是用改前/改後的樣子判定的。
  被改的內容自己一變，判定就失效。我反應式地補了 `force()` 四次（唯一性、追加式、刪除式、已套用標記），
  每次都在下一個變體上再被咬一次——**補洞的速度追不上洞的產生速度**。
- **真正的問題不是「會壞」，是「壞得無聲」**：冪等檢查只說「結果不對」，不說「哪一個補丁失效」。
  四次裡有三次靠冪等檢查接住，第三次（靜默跳過）靠人眼才發現。
- **做法**：`PatchLog` 登記簿。每個補丁在套用時登記一個「套用後一定看得到／一定看不到」的標記，
  `rebuild()` 結束時一次驗完，失效時**指名是哪一個補丁**。
  `force()`（四條路徑）與 `inject_css()` 自動登記；兩處移除式改寫（見證圖面板、色彩 token）手動登記。
  目前一次同步登記 **99 個補丁**，`validate()` 的報告帶上 `"patches": 99`。
- **語意刻意選成「驗結果，不驗有沒有跑」**：冪等重跑時補丁本來就該跳過，那不是錯誤；
  錯的是「該在的東西不在」。
- **突變驗證**（兩段，第一段是反例）：
  1. 只讓 `inject_css` 靜默跳過 → **不報錯**。正確：正典裡本來就有那段 CSS，結果是對的。
  2. 同時把那段 CSS 從正典拿掉（忠於史實：內容不在了而補丁又被跳過）→
     報 `同步套用了 99 個補丁，其中 1 個沒有生效`，並指名
     `補丁「CSS .toc-facets{display:flex」套用後應該看得到的內容不見了`。
- **測試**：`test_axiom_reader.py::test_every_patch_actually_lands`（登記數 > 50 且驗證為空）。
- **未涵蓋（誠實標記）**：`--check` 模式不跑 `rebuild()`，登記簿是空的，所以那條路徑仍只靠既有的
  五道 assert 與各功能的防回歸檢查。要涵蓋就得把標記清單寫進產物，目前判斷不值得。
- **另一類錯，不在本票**：我在寫補丁腳本時三次用 Bash heredoc 包含跳脫字元的 Python，
  把 `\r\n` 寫成真的換行而弄壞腳本。那壞的是暫存腳本、不是 repo，但同樣是明知故犯。
  處置：這個 repo 的 `current_geometry.c` 是統一 CRLF 且被 `AGENTS.md` 列為地雷，
  **補丁腳本一律用檔案寫入工具產生，不用 heredoc**。

### GEO-152 ✅ 已做（2026-09-21）篩選 chip 的數字在第一次建置後就凍結了

- **怎麼被抓到**:做 GEO-041/043 時在 `current_geometry.c` 的註解裡引用了 I4、I33、D1、D5,
  `axiom_matrix` 抓到後有一條從「無追溯」變成「有追溯」——
  `test_facet_chips_are_data_driven` 立刻報 `22 != 21`。
- **根因**:`apply_facets()` 用 `force(template, anchor, anchor + markup, ...)` 插 chip,
  而 markup 裡有**算出來的數字**。force() 的「已套用」判定看到 `anchor + 舊 markup` 還在就返回,
  數字從此凍結在第一次建置的值。GEO-149 交付時只驗了第一次建置,所以當下是對的。
- **修法**:先用正則移除既有的 `<nav class="toc-facets">`,再插入當前版本
  (與見證圖面板、色彩 token 同一個處置)。
- **一般規則**(已寫進 `AGENTS.md`):**凡是內容會隨資料變的標記,一律「先移除再插入」,
  不得用 force() 的改前/改後判定**——那個判定只看「形狀在不在」,看不出「內容過期了」。
- **登記簿為什麼沒抓到**:`PatchLog` 驗的是「標記存不存在」,而標記確實存在(只是數字舊了)。
  這是登記簿設計上的已知邊界:它擋「補丁沒生效」,擋不住「補丁生效了但內容過期」。
  後者要靠針對資料一致性的測試——`test_facet_chips_are_data_driven` 正是這種測試,而它做到了。
- **我的流程錯誤**:這次我在 `test_axiom_reader` 報 FAILED 的情況下仍然先 commit 了
  (a3d5a69),修正在後一個 commit。正確做法是測試不綠就不 commit。

**GEO-030 / GEO-035 實作紀錄(2026-09-21)**

- **GEO-030**:`CreateFontW` 失敗時原本直接 `SelectObject(g->dc, font)`——傳 NULL 是錯誤呼叫、
  回傳 NULL,接著又拿這個 NULL 去「還原」,等於**把 DC 的字型狀態弄壞**,之後每一次畫字都受影響。
  改成:失敗就不換字型,用 DC 現有的字型把字畫出來;還原時也先判 NULL。
- **GEO-035**:五個控制項任一建不起來就回傳 -1 讓 `WM_CREATE` 失敗。
  原本不檢查,於是對 NULL HWND 呼叫 `WM_SETFONT` 與 `SetWindowLongPtrW`(靜默失敗),
  接著 `gdi_layout_input_bar()` 對 NULL 呼叫 `MoveWindow`,狀態列也再也更新不了——
  **視窗看起來開著,其實是壞的**。呼叫端本來就有 `if (window == NULL) return false;`,
  所以回傳 -1 是現成的退路。順帶把兩個按鈕的 handle 存下來,不再用 `GetDlgItem` 取。
- **⚠ 驗證限制(誠實標記)**:這兩張都在 `#ifdef _WIN32` 區塊內。
  `tests/_clw.bat` 沒有 `/U_WIN32`,所以**有被編譯、有過型別檢查**;
  但第 3 流(GDI/Win32 互動層)**完全沒有自動化回歸測試**(稽核缺口 4),
  我無法在這裡證明「字型建立失敗時畫面仍正確」或「控制項建不起來時視窗確實開不起來」——
  那需要在真實視窗下製造資源耗盡。**兩者都只驗到「程式碼正確」,沒驗到「行為正確」。**

---

## 外部審查(codex)報的四個問題 — GEO-153～156(2026-09-21)

四條全部**確認屬實**,全部修好,**每一條都做過突變測試**
(把修正拿掉、測試必紅;不只是「修完測試是綠的」)。

### GEO-153 ✅ 已做(2026-09-21)P1:CRLF 讓建模功能整個失效

- **現象**:Windows 上每一次建模都被擋成 `UNSUPPORTED / AXIOM_VERSION / I32`
  「Axiom source changed without a corresponding executor version」。
- **根因**:`AXIOM_SHA256` 是在 **LF bytes** 上算出來的,而 `公理層.md` 在 git 裡存 LF、
  `.gitattributes` **沒有**把它標成 `-text`(`current_geometry.c` 與見證 SVG 都有),
  所以 Windows 簽出來是 CRLF。`_axiom_hash()` 直接雜湊原始 bytes,於是**必然**對不上——
  不是機率問題。實測:工作區 620 CRLF / 0 lone LF,實際 `3092f91f…`,期待 `6958a10c…`,
  而**把 CRLF 正規化成 LF 後的雜湊恰好等於 `6958a10c…`**,反證那個常數的來歷。
- **修法**:雜湊前先 `raw.replace(b"\r\n", b"\n")`,與 `geometry-guide/witness.py::_sha`
  同一個判斷——行尾是簽出方式,不是內容。這也是 manifest 的 `axiom_sha256` 能跨平台同值的前提,
  否則「可重現的建模套件」根本不成立。常數不用動,`geometry-core/examples/*.model.json`
  裡的既有 golden 完全不受影響。
- **沒有改 `.gitattributes`**:標成 `-text` 只治新的 clone,治不了既有工作區,而且正規化之後它是多餘的。
- **端到端重現與驗證**:本機沒有 gcc 系編譯器,`BASE_COMPILER` 會比公理閘門**先**擋下來,
  整套測試的數字因此不會動——這代表端到端測不出修好沒有。改用 MSVC 編一支
  `geometry-core/model_base.c` 當 `GEOMETRY_MODEL_BASE` 之後:
  **修正前 `FAILED (errors=24)`,24 個全是 `AXIOM_VERSION`、0 個 `BASE_COMPILER`
  ——與外部審查報的「24 個錯誤」完全一致;修正後 39/39 通過。**
- **測試**:`test_modeling_runtime.py::AxiomSourceIdentity` 三條,刻意**不經過** `build_package`,
  沒有編譯器的機器也跑得動:(1) 雜湊等於常數;(2) 同一份條文的 LF 與 CRLF 兩種簽出得到同值;
  (3) **真的改一個字仍然要擋**——正規化不得把閘門關掉。
  另把 `test_modeling_runtime` 原本自己算的那個 oracle 抽成 `axiom_digest()` 並同樣正規化;
  它本來也內建了同一個錯誤假設。

### GEO-154 ✅ 已做(2026-09-21)P2:上傳失敗會毀掉還活著的場景

- **現象**:`/upload` 的新檔載入失敗後,畫面上還是舊場景,但「重新載入場景」從此壞掉。
- **根因**:順序反了。`serve.py` 先寫新暫存 → **刪光 `_upload_temps`** → 才
  `ask_bridge("loadfile …")`。而 bridge 的 `cmd_loadfile` 是**交易式**的
  (失敗時 `g_world = before`),所以舊場景確實還活著——活著,但來源檔已經沒了,
  前端 `curScene` 指向一個已刪的路徑。
- **修法**:**先載,成功了才動舊暫存**。失敗時反過來刪掉載不起來的那個新檔,
  並且不把 `path` 塞進回應(不得讓前端改指到一個沒載進去的檔)。
- **測試**:`test_serve.py::test_failed_upload_keeps_the_live_scene_reloadable`,
  三步:成功上傳 → 失敗上傳 → 再成功上傳,逐步檢查 `_upload_temps` 與檔案是否存在。
- **突變驗證**:把 `serve.py` 還原成 HEAD → `AssertionError: False is not true : 還活著的場景的來源檔被刪了`。
  (第一版測試的斷言順序讓它停在症狀 `'path' unexpectedly found` 上,已把最能指認病因的那條排到最前面。)

### GEO-155 ✅ 已做(2026-09-21)P2:批註合併漏擋「同一份備份內部」的同 ID

- **根因**:`known = {x["id"]: x for x in state[field]}` 在迴圈**外**建一次,append 時不更新,
  所以剛收下的紀錄對後面的紀錄是隱形的。同一份備份裡兩筆同 ID 異內容會**兩筆都被收下**。
- **為什麼五道 assert 攔不住**:那五道驗的是版面完整性,不檢查批註集合的 ID 唯一性。
- **修法**:append 之後補 `known[value["id"]] = value`。一行。
- **測試**:兩條。(1) 同 ID 異內容必須丟 `Conflicting review record`;
  (2) 一字不差的重複只是冗餘、不是衝突,但**只能收一次**。
- **突變驗證**:拿掉那一行 → 第一條 `ValueError not raised`,第二條 `2 != 1`
  ——後者正是那個靜默重複。

### GEO-156 ✅ 已做(2026-09-21)P2:newid 可能發出已被占用的 id

- **根因**:`cmd_newid()` 的 `max + 1` 在 uint32 上界回繞成 0。原本**只有 datum**
  有碰撞迴圈(那段註解寫著 "Overflow must not overwrite id 0"),其餘八種是裸 `+ 1`。
- **比原報告更精確的定性**:後果分兩種。
  `guide` / `grid` 的 id 0 **合法**,所以 newid 發出一個已存在的 id,畫布拿去宣告
  = I8 交易式重宣告 = **覆寫既有物件**;`surface` / `timber` / `column` 的 id 0 會被核心擋掉,
  症狀變成「新物件建不出來」。兩種都是錯的。
- **實測**:場景同時有 `guide 0`(位置 300)與 `guide 4294967295`(位置 2900)時,
  **載入合法**,而 `newid` 回 `"guide":0`。修正後回 `"guide":1`。
- **修法**:抽出 `WORLD_NEXT_ID(out, array, count)` 巨集,九種一致處理:
  從 `max + 1` 起找第一個沒被占用的 id。候選 count+1 個且兩兩相異、被占用的只有 count 個,
  所以迴圈必定找得到空位(終止性有證明,不是靠經驗)。
- **測試**:`test_bridge_integrity.py::test_newid_never_hands_out_an_id_already_in_use`。
- **突變驗證**:還原成 HEAD 重編 → `AssertionError: 0 unexpectedly found in {0, 4294967295}`。

### 回歸狀態(2026-09-21)

全綠:`run_tests.py` 131/131、`test_core_integrity` 80/80、`witness --check` 17/17、
`test_axiom_reader` 24、`test_bridge_integrity` 10、`test_serve` 9、`test_reference_contract` 25、
`test_datum_contract` 9、`test_modeling_runtime` 39(需 `GEOMETRY_MODEL_BASE`)。

**跑不動(誠實標記)**:`test_modeling_transport` 在 `setUpClass` 就寫死 `cc -std=c11 … -o`
去編 `web_bridge.c`,沒有環境變數可覆寫,本機沒有 gcc 系編譯器所以整組跳過。
查過了,它**沒有**碰 `/upload` 或 `newid`,所以這四張票的涵蓋沒有因此缺口;
但「Windows 上跑不動的測試檔」本身是既有問題,另開票。

### GEO-157 ✅ 已做(2026-09-21)P2:畫布自己湊 surface id,仍會覆寫既有物件

外部審查(codex)在 GEO-156 之後的追加回報,兩處都確認屬實。

- **背景**:`surface N` 是「boundary N + placement N」**合體一行**,所以它要的 id
  必須在**兩個** id 空間裡都是空的。`newid` 只保證各類別各自空。
- **兩個現場**:
  - `geometry-web/app.js` `emitNewSurface()`:`Math.max(ids.boundary, ids.placement)`。
  - `geometry-web/app.js` `submitBox6()`:`b0 = Math.max(...)` 之後 `b0+1 … b0+5` 連續加號。
- **為什麼以前「看起來」沒事,現在才浮出來**:沒有回繞時 `newid` 的兩個值都**大於**
  各自類別的所有既有 id,所以 max 與其後的加號也都大於全部——湊得出來是巧合,不是保證。
  **GEO-156 把回繞修掉之後,`newid` 會回小號碼**,這個巧合就不成立了。
  也就是說:上一張票修好了「發出去的 id」,卻讓「拿它做算術」這件事第一次真的咬人。
- **後果是靜默覆寫,不是報錯**:`surface` 對既有 id 是 I8 交易式重宣告。實測
  (真實瀏覽器、真實 `submitBox6`):世界 boundary {0,1,2,5,MAX}、placement {MAX} 時,
  舊碼用掉 3,4,5,6,7,8,既有的 `boundary 5 outline 0,0 90,0 90,90 0,90` 被換成
  `outline 0,0 4000,0 4000,2500 0,2500`,而狀態列顯示 **「✓ 六面盒空間 1(6 面含地板)」**。
  使用者看到的是成功訊息。
- **另一種症狀**:在別的世界裡整批會被 `history-abort` 回滾,變成「六面盒建不出來」。
  我第一次選的重現世界就是這種,**差點據此下結論說「舊碼沒事」**——是去看實際 dump
  才發現狀態列那句 ✓ 是上一次成功留下的殘影。教訓:狀態列不是證據,dump 才是。
- **修法(把不變式放回有資料的那一側)**:`newid [n]` 新增 `"surfaces": [n 個 id]`,
  每個都在 boundary 與 placement 兩邊都空、且彼此相異;n 預設 1,範圍 1..16,
  不合法一律 `ok:false` 且不回半套。既有的九個純量欄位**一個都沒動**(向後相容,
  `canvas_test.js` 既有案例不受影響)。畫布改用 `ids.surfaces[0]` 與 `newid 6`,
  六面盒的槽位維持 `[0]` 天花 / `[1]` 地板 / `[2..5]` 牆,所以「有沒有地板」
  不會改變牆的編號(保留原行為)。
- **順帶確認的兩件事實**:`surface 4294967300`(超出 uint32)是**被拒絕**不是回繞;
  `surface` 撞到既有 id 一律回 `ok:true` 並覆寫。
- **測試**(三層):
  1. `tests/test_bridge_integrity.py::test_newid_surface_ids_are_free_in_both_id_spaces`
     ——六個 id 兩邊都空且互異,並斷言舊算法在這個夾具裡**確實**會撞上(夾具保有牙齒)。
  2. 同檔 `::test_newid_rejects_a_count_it_cannot_honour`——數量邊界。
  3. `geometry-web/cdp_test.js` BF4「六面盒不覆寫既有面(GEO-157)」
     ——**唯一真的跑 app.js 的 harness**(headless Chrome 點 `box6Submit`)。
- **突變驗證**:
  - 橋接器:拿掉 `surface_id_taken()` 裡的 placement 檢查 → `0 unexpectedly found in {0, 4294967295}`。
  - 畫布:把 `app.js` 換回修正前 → cdp_test 報 `{"kept":false,"faces":10} ✗`
    (既有面被毀、面數少一),其餘 273 條照樣綠——這條測試精準指向缺陷。
- **回歸**:cdp_test **274 ✓ / 0 ✗**、canvas_test **412 pass / 0 fail**,
  其餘全套見下。

#### GEO-157 追加修正：回繞時排除保留編號 0（2026-09-21）

- 複查發現：只有 `surface 4294967295`、且 0 尚未占用時，`newid 6` 會回傳
  `[0,1,2,3,4,5]`。D4 規定 `boundary_id=0` 表示使用自帶矩形，不能拿來建立
  引用同號邊界面的合體 `surface`；實際新增面／六面盒會失敗並回滾。
- `next_surface_ids()` 每次檢查候選前都跳過 0，包含第一個候選、同批後續候選
  及避開既有編號途中發生的回繞；仍避開 boundary、placement 及本批已選編號。
- 新增橋接器回歸案例：上界／上界前一號 × 單面／六面 × 小編號空閒／已占用，
  共 8 種情況；不只檢查回傳編號，也實際建立每個面並確認原有定義保留。
  修正前可重現保留編號 0 被發出；修正後整組 bridge 測試 13 項通過。
- 新增 CDP 案例：在只有最大編號面的世界，實際點六面盒建立按鈕，檢查原面保留、
  面數增加至 7，且新增 1 個封閉空間；完整瀏覽器檢查 **275 ✓ / 0 ✗**。
- 驗證環境：MSVC 編譯成功，但新執行檔遭 Windows Smart App Control 封鎖；
  改由既有 WSL/GCC 執行核心測試，瀏覽器仍使用 Windows Chrome，不更動安全設定。

### 回歸狀態(2026-09-21,GEO-157 後、追加修正前)

場景 131/131、integrity 80/80、witness 17/17、閱讀器 24、bridge 12、serve 9、
reference 25、datum 9、modeling runtime 39(需 `GEOMETRY_MODEL_BASE`)、
canvas_test 412/0、cdp_test 274/0。

---

## 全專案複查(2026-09-21)— GEO-158～162

起因:使用者要求「重新檢查整個專案一遍」。我把專案切成五塊派對抗審查,
再把診斷整理成交叉確認單交給另一組 agent 獨立查證。**九條裡七條成立**,
其中一條是 P1(資料遺失)。下面每一條都經過:我自己重現 → 修 → 突變測試 → 交叉確認。

### 交叉確認改正了我四個說法(誠實記錄)

1. **「空間從封閉退化成部分」不是回繞造成的**——對照組也是「部分」,那是 split 本身。
   可歸因於回繞的證據是**重複 ID 與重載掉面**,不是封閉狀態。
2. **`column 0` / `beam 0` 是可用的**。我原本標「無結論」,對方在游離世界與完整封閉房間
   都建成功了,0 與 77 兩組皆過且存檔重載逐字一致。我的無結論來自**我建的世界本身足跡越界**,
   對照組跟著失敗——這正是「對照組也失敗就不能下結論」的用處。
3. **GDI 不是死碼**。靜態呼叫鏈:矩形/多邊形選單 → WM_COMMAND → WM_LBUTTONDOWN/UP →
   `gdi_canvas_down/up` → `canvas_emit_new_surface` → `canvas_next_id`。它會發出 `surface 0`;
   但**不能**把投影路徑「追加重複 ID 並掉面」的後果不加區分地套到 GDI。
4. **我說「沒有任何夾具使用接近 UINT32_MAX」是錯的**。既有 bridge 測試早就在用 4294967295
   (參考線回繞、surface 跨命名空間、範圍測試)。真正的缺口是**投影配號、純 boundary 配號、
   loadfile/歷史群組組合**這三處。

### GEO-158 ✅ 已做 P1:核心配號器回繞 → 重複 id → 存檔重載掉面

- `current_geometry.c:10489` `proj_next_surface_id()` 與 `:4816` `canvas_next_id()` 都是裸
  `max + 1`,註解寫「避免碰撞」但回繞之後並不避免。
- 實測(同一場景只差第六個面的編號):對照組 `1,2,3,4,5,6,7,8`;
  上界組 `1,2,3,4,5,MAX,0,0`。兩者 rc 都是 0、零錯誤訊息。
- **真正的傷害是往返**:dump 出兩行 `boundary 0`,再 `loadfile` 時後者靜默蓋掉前者,
  **少一個面**,而兩次載入都回 `ok:true`。
- 另一半是 `0` 本身:D4 用 `boundary_id == 0` 表示「不掛邊界面、自帶矩形」,
  所以 `surface 0` 建不起來。
- 修法:抽 `world_next_surface_id()`——從 max+1 起找第一個「兩邊都沒占用且非 0」的 id,
  任何一輪回繞到 0 都跳過;配不到回 0 當失敗哨兵。五個呼叫點全部加檢查。
- 測試 `test_projection_split_ids_survive_a_save_and_reload`(帶對照組);
  突變:還原成修正前 → `8 != 7 : boundary 出現重複 id`,且**只有上界那組紅**。
- 副作用:新註解引用了 D4 → 追溯矩陣多一個 code site → 正典必須重建。
  這是設計中的警報,不是誤報。

### GEO-159 ✅ 已做 P2:`newid.boundary` 會發出 D4 的保留值 0

- `boundary 0` 建得起來,但 `placement N on boundary 0` **永遠**被拒。
  `app.js:3469` `objEmitFace()` 直接用這個欄位 → 使用者拿到成功訊息和一個死面。
- 只有 boundary 需要跳過 0。其餘八類實測可用,不做無謂的行為變更。
- 測試不只看數字,而是拿發出來的 id 真的建面再掛承載面;並用 `boundary 0` 當對照
  證明斷言有牙齒。

### GEO-160 ✅ 已做 P2:`loadfile` 跨過未關閉的歷史交易

- `g_hist_grouping` / `g_hist_group_base` 是行程層全域,不在 `World` 裡,
  `cmd_loadfile` 的 World 快照救不到。群組還開著而 base 停在載入前的世界,
  之後 `history-end` 把舊世界推進 undo 疊——**按一次 undo,loadfile 與其後所有編輯一起消失**。
  **成功路徑也會踩到。** undo 後果由交叉確認實跑證實(我原本只有讀碼推論)。
- 照 `undo`/`redo` 的既有慣例一律拒絕。只拒絕、不自動中止群組:不靜默丟掉做到一半的編輯;
  `history-abort` 冪等且永遠回 ok,恢復路徑一直都在。

### GEO-161 ✅ 已做 P2:診斷頁的寫檔閘門被 `--out` 繞過

- `make_axiom_reader.py` 的 `resolve_out()`:`--out` 分支在閘門**之前**就 return,
  閘門只掛在 `--in-repo` 上。`--out <正典>` 與 `--in-repo --out <正典>` 都能覆寫唯一正典。
  檔頭宣稱「文字規則擋不住誤跑,所以改成機制」——那個機制有洞。
- 改成所有路徑都過同一道 `guard()`,用 `realpath` 比對,相對路徑與 `..` 都擋得住。
- 驗證只 import 後直接呼叫 `resolve_out()`,**沒有執行 main()、沒有碰正典**。

### GEO-162 ✅ 已做 P3:四處文件失真 + 契約與實作矛盾 + 兩處措辭過頭

- **NUL 地雷已失真**(`CLAUDE.md`、`AGENTS.md`、`BACKLOG.md`、`witness/交接-GEO-137.md`):
  現檔 NUL=0。`7f94145` 當時是 4——**寫下時是真的**,檔案後來改動後消失,四處都沒跟上。
  **CRLF 那半仍然成立**,所以是改寫不是刪除。
- **`AGENTS.md` 引用 `公理層.md:319` 行號錯**:該行是 I11,正確位置是 614。
- **`MODELING-CONTRACT.md:79` 與實作矛盾**:契約寫「UTF-8 原始 bytes」,
  實作(GEO-153 之後)是先 CRLF→LF 正規化。**是我 GEO-153 只改程式沒回補契約**,
  下游照契約字面實作會永遠對不上。
- **`--check` 的能力被我講過頭了**:交叉確認指出 `--check` 的介面本來就是「驗現有產物」,
  而且他們在記憶體跑 rebuild,99 個補丁全過、輸出逐位元相等——**管線是健康的**。
  問題只在 AGENTS.md 把三條指令並列卻沒說各驗各的。已改寫成明講
  「`--check` 綠燈不代表整條管線健康」並說明 `patches: 0` 的來由。
- **SAC 的措辭過頭**:我原本寫「等一下再啟動一次就好」,交叉確認指出**不保證**放行,
  他們就是持續被擋才改走 WSL/GCC。已改成「通常…但不保證」,並要求把
  「環境阻擋」與「程式失敗」分開記錄。

### GEO-163 ✅ 已做(🔒 2026-09-21 拍板選項 B)P2:解析器層拒絕保留的 boundary id 0

- **決定**(使用者拍板,決策佇列 Q9):只在**邊界面的 id 空間**就地拒絕,
  不動 `公理層.md`(那是選項 C),也不動其餘八類。
- **擋三個入口**,共用同一句話(`RESERVED_BOUNDARY_ID` 巨集),免得同一條規則
  在不同指令下講出不一樣的理由:
  - `boundary 0 …`(宣告)
  - `surface 0 … outline …`(合體宣告,**只在真的宣告 boundary 時**)
  - `placement N on boundary 0`(明寫的引用)
- **刻意不擋**:沒有 outline 的 `surface 0` 等同純 placement,0 對它合法,
  現在合法、以後也要合法。測試有專門一條守這件事。
- **修掉的是答非所問**:
  - `surface 0 … outline …` 原本回「重宣告後有物件失效」——而它其實是**首次宣告**。
  - `placement N on boundary 0` 原本回「不掛邊界面的承載面需要 rect」——
    使用者明明寫了 `on`,卻被當成「沒寫 on」的預設值。
- **測試**:`test_reserved_boundary_id_zero_is_refused_with_a_useful_message`,
  每條都帶對照組(換成非 0 的 id 必須成功,否則是指令寫錯不是 0 的問題)。
  突變:還原成修正前 → 3 個失敗,訊息正是那句「不掛邊界面的承載面需要 rect」。
- **連帶改到的既有測試**:GEO-159 的對照組原本寫「`boundary 0` 建得起來但掛不上
  承載面」,GEO-163 之後變成建都建不起來,前提跟著改寫(**改前提,不是刪斷言**)。
- 正典閱讀器一併重建:`apply_boundary_line` 現在實作 D4 的哨兵規則,
  追溯矩陣多一個 code site(D4 共 4 個)。99 補丁全過、五道 assert pass、
  `documentHash` 不變。

### 我沒有涵蓋的

解析器對畸形輸入的完整 fuzz;`geometry.py` 三角化的退化輸入(孔與外環共邊、自交、零厚度)。
交叉確認那一輪也同樣沒涵蓋。
