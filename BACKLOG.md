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

### GEO-113 補那 36 條沒有夾具的條文
- **內容**:目前 63 條裡有 36 條沒有任何夾具指名它,閱讀器上標「尚無範例」。
  清單(由 `axiom_matrix.py` 產生,以它為準):
  D2 D3 D4 D5 D12 D6 D7 D8 D9 D13 I1 I2 I3 I4 I7 I9 I11 I12 I14 I16 I17 I18
  R1 R4 R5 R8 R9 R10 R12 R13 R14 R15 R16 R17 R18 R20
- **注意**:「沒有夾具指名它」不等於「沒被測到」。像 I1 承載面框架合法,
  每個場景都在跑它,只是沒人寫下條號。所以這張票有兩種做法,要逐條判斷:
  (a) 真的缺覆蓋 → 寫新夾具;
  (b) 其實有覆蓋、只是沒標 → 在既有夾具的檔頭註解補上條號即可。
  **不要為了讓數字變綠而硬寫不相干的夾具。**
- **驗收**:每補一條,`axiom_matrix.py` 的該條從黃/紅變綠,
  且閱讀器上那條的「尚無範例」消失、換成真的範例。
- **相依**:GEO-112。**估時 依逐條判斷結果而定**。
