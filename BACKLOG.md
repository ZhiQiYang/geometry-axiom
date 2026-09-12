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

### GEO-030 ⚡ CreateFontW 失敗時不 SelectObject(NULL)
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

### GEO-035 WM_CREATE 控制項建立失敗處理
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

### GEO-075 ⚡ SVG/文字輸出加「房間內部尺寸」與角材下料清單
- **內容**：cut list：每支角材 L×A×B + 所屬面 + 錨點；加總同規格數量。實用化第一步。
- **驗收**：room_a 輸出含「角材 1：1800×27×33 ×1」。
- **檔案**：main 報告段。
- **測試**：兩支同規格角材 → 數量 ×2。
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
