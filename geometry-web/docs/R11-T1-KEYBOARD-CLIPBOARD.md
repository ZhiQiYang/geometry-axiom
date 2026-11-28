# R11 T1：面內鍵盤選單與同空間直接 RC 重用

工作包：issue #476 T；交付與設計：issue #116。
完整基底：`48d5f3887e8cb8d222307db62dbdea287fda8442`。

本文件是已採納 R11 範圍內的宿主實作契約，不修改 `公理層.md`。
這份補丁尚無實作 PR，不提升需求帳 L0–L5；本地 Node／原生 fixture
不是 L4。真 Chromium、正式登錄計數／成本、完整 CI 與合入均待套用端。

## 使用路徑與邊界

| 工作區 | 入口 | 行為 |
|---|---|---|
| 面內 | 選普通角材，讓畫布取得焦點，按 ContextMenu 或 Shift+F10 | 開同一 B 選單並保持原單選／多選；複製、貼上與批改仍走 TimberEdit。 |
| 面內 | 無幾何點時以鍵盤開選單 | 螢幕中心只供擺放選單；不轉成幾何點。u／v 參考線等位置型動作顯示需先指定位置。 |
| 空間平面圖 | 右鍵單支普通直接 RC 柱／樑 → 重用柱樑 → 複製定義 | 只建立同一空間、短期記憶體配方；不呼叫 newid、不寫 World、metadata 或歷史。 |
| 空間平面圖 | 右鍵／鍵盤選單 → 重用柱樑 → 貼上… | 沿既有 RC 表單，尺寸／高度沿來源定義，新位置清空；真指標指定或在原欄位明填，確認前零寫入。 |
| 空間平面圖 | 貼上表單確認 | 沿原 rcSubmit 的驗證、newid、宣告與一次歷史；原物件不改。Esc／取消不建立。 |

三視圖保留唯讀／導覽；其餘畫布、跨面、跨空間、跨專案子圖及新觸控片
依設計切片後續處理。新配方不存系統剪貼簿或 `.gcanvas`，沒有存檔遷移。

同面 D7 保留原生 opaque recipe、typed ParameterRef／版本／override／role／priority；
不把 effective 尺寸當定義，也不自行配新角材 ID。RC 只接受原 rcDefinition
已支援的直接定義；source、sources、owner、group（含數值 0）仍拒絕。
不承諾保存 objects API 沒有表達的原 DSL 拼寫或省略欄位。

## 事件與過期狀態

鍵盤入口、其後瀏覽器原生 contextmenu 只開一次；鍵盤入口維持已明選集合，
真正右鍵 pointerdown 才切回舊命中路徑。輸入框／可編輯控制保留原輸入。
組字期間工作區 contextmenu 一律消音，包含 button 0／2 與非零座標；
repeat、keyCode 229、isComposing 已識別的選單鍵不得由後續事件重開。
compositionend 後真右鍵恢復原路徑。沒有增加任何時間上限。

面內選單及空間配方釘住專案、context token／revision、原生 revision、
history frame／undo／redo 頭／group、service session／phase 與 navigation。
空間另釘 typed source、定義與連線世代。舊 source 刪除後同號同內容重建
仍須失效；不以裸 JS 物件身分代替原生世代。
貼上表單繼續持有來源的 stamp，不換成空白右鍵位置的 stamp。
配方一旦被 sync 或讀取觀察到失效即鎖為 stale；Undo 不可令它復活，須重新複製。

## 必要具名契約遷移 T476_SPACE_REUSE_MENU

既有 `workspace_context_menu_cases_space.js` 的精確根選單：

| 原集合 | 新集合 |
|---|---|
| `delete,duplicate,size` | `delete,reuse,size` |
| `beam,column,view` | `beam,column,reuse,view` |

三處既有 duplicate 測試先開 reuse，再執行原 CONTROL_REACHABLE 檢查與原操作。
openReuse 只做導覽；不刪原斷言、不把集合改為 subset、不增減 P1161 成功計數。
新 suite 精確驗 reuse 中 `copy,paste,duplicate` 的順序。
該既有測試的 architecture exclusion pin 按審過的實際 LF bytes 更新，
由原 `architecture_contract.fragment_manifest_files()` 產生，不刷新其他 pin。

## 可重跑驗證

T 先套在上述基底；原產品應在 `T476_FACE_KEYBOARD_SELECTION` 與
`T476_SPACE_REUSE_MENU` 打紅。P 後執行：

```bash
node --test --test-reporter=tap tests/test_r11_face_keyboard.js
node --test --test-reporter=tap tests/test_r11_space_clipboard.js
node geometry-web/workspace_context_menu_state_test.js
node --test --test-reporter=tap tests/test_timber_edit_ui.js
python3 -B tests/diagnostics/r11_t1_withdrawal.py --out /tmp/r11-t1-withdrawals.json
```

撤回 runner 的單階段 20 秒、全程 180 秒固定有界；在隔離實體檔案副本改產品來源，
每個變更 anchor 恰好一次。只接受唯一指定 Node test 的 ERR_ASSERTION／AssertionError，
基準／撤回／還原依序 0／1／0；語法錯誤、設定失敗、timeout、signal、其他斷言不算殺死。
還原逐 byte 相同後必須重跑同一裁判。原工作樹不變；JSON 是診斷報告，非正式 mutation 收據。

兩個 Node suite 使用真 adapter 與原 app RC／pointer 程式，DOM、shell、native transport
是邊界替身；不是瀏覽器或原生完整驗收。獨立 P1163 使用真 CDP 鍵盤／指標與原生讀回，
尺寸 1400×900、390×844。合成 composition 診斷有明示，不能冒稱實體 IME。
fixture／可達性失敗標 `P1163_SETUP`，不能冒稱第一個指定紅。

P1163 的第一個預期紅為 `P1163 T476_FACE_KEYBOARD_SELECTION_1400`。
後續驗同面 typed source、候選取消、多選 batch 入口／取消、無點不發明 anchor；
同空間直接 RC 真位置、確認新 ID／精確 box、原柱不變、一筆 history、Undo／Redo、stale 拒絕。
瀏覽器段完整成功的原始碼預期為 77 項；正式數字只由真 capture 採入，不能手寫。

## 片段量測與正式守門

兩個 native suite 片段由 `native_registry.py --init-suite` 產生，維持 pending-ci-census；
P1163 由 `canvas_registry.js stage-module --id P1163` 產生，assertions=0／cost=null
是未驗收佔位，不是放寬的零斷言。正式 runner 拒絕 pending 是預期行為。

套用端依 `tests/FRAGMENTED-REGISTRIES.md`：

1. 在確切 T／T+P 組合實跑新 Node 與 P1163，保留完整先紅後綠原始輸出。
2. `Native suite measurement` 分別量 `node:r11_face_keyboard`、`node:r11_space_clipboard`；
   grokbot／可下載官方 artifact 者用原 `--import-suite` 採入，產生獨立成本片段。
3. `Canvas section measurement` 量 P1163，原 `import-cost` 採入；保留 unit 2 尾 slot、P359 前。
   不需另寫 golden 產生器；不得更動任何歷史段計數。
4. 以原 `registry_migrate.py check --trusted-base <當下main完整SHA> --self-test` 驗全表。
5. 真重跑受影響的 R11 browser mutation、canvas 兩片／complete 和一般 CI。
   P1161 的入口遷移須跑原段並核原成功計數，不能因新段過而略過。
6. 產品／architecture manifest 輸入已變，架構原三命令與 Architecture evidence 必須重跑採入。
   mutation 先物化，再由原 `tests/mutate.py --check` 判定哪些逐筆證據過期；
   需要者跑正式 Mutation evidence，使用 store adopt，不手改收據雜湊。

本片不修改公理、正典閱讀器、kernel、app.js、既有 golden、大表或正式收據。
未建立新共用 source 給其他工作包；兩個 adapter、既有 P1161 case 與 BACKLOG
仍有實質合流交集，合併後要重驗來源與當前組合。
