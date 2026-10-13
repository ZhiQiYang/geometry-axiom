# SketchUp 2026 內驗收

此目錄包含完整幾何驗收與較小的工作流回歸。一般 Ruby 語法檢查／minitest 不能代替
SketchUp 幾何、HtmlDialog、編輯 context 或復原的真機證據；實際通過狀態以該次原始輸出為準。

工作流修正優先用 `run_workflow_regressions.rb`：另開新的空白模型，在 Ruby 主控台執行下列命令。
它不開 HtmlDialog 或原生起點視窗，不透過 UI timer 或 `send_action`；只建立兩個小天花面與一條斷面。

```ruby
ENV['GEOMETRY_FRAMING_WORKFLOW_OUTPUT'] = 'D:/geometry-framing-workflow-evidence'
load 'D:/geometry-axiom/sketchup-plugin/test_su/run_workflow_regressions.rb'
```

這份小腳本直接使用與 UI 相同的 `Dialog.dispatch`，以真實模型驗證：

- 群組內預覽不增加 Undo 層：先建立一個標記，預覽後只呼叫一次 [`Sketchup.undo`](https://ruby.sketchup.com/Sketchup.html#undo-class_method)，必須移除標記並保留原輸入及編輯路徑。
- 群組內連續生成 A、B 兩批後，一次真正的 `Sketchup.undo` 必須只消除 B 的全部角色，A 與輸入仍在。
- 群組內保留前批時，暫時讓 `Builder.add_boxes` 完成第一件後在第二件拋錯，隨即還原原方法；驗證失敗當批完整回滾、前批與輸入及編輯路徑保留，根實體 ID、definitions／materials／layers 的數量與名稱皆回復。
- A 通過檢查後改選 B，直接生成必須回報過期且不更動模型；參數變更也必須過期。重新檢查 B 後才能生成。
- 同一斷面已通過檢查後仍能再次明示另一端為起點，核心 points 真正反向，L／cap／板厚／角材斷面參數保持不變。測試注入明示選擇 callback，不代替使用者猜端點。

預設輸出為 `Sketchup.temp_dir/geometry-framing-workflow-YYYYMMDD-HHMMSS/` 的 `output.txt` 與
`result.json`。此腳本是同步回歸，以最後的「工作流回歸完成，exit_code=0」為完成證據。
它不清除測試後模型；失敗時保留現場及原始紀錄。不要同時執行完整驗收，也不要在使用者工作模型上跑。
原生 Undo 可能清空目前選取；Undo 後只要求原編輯路徑與輸入保留，下一輪檢查由腳本明示重選輸入。

以下為既有完整幾何驗收 `run_all.rb` 的操作方式。

先在 SketchUp 2026 開一個新的空白模型，刪除預設人物等範本實體，再開啟「視窗 → Ruby 主控台」。腳本要求模型完全沒有實體且未進入群組編輯；不會清空既有模型。範本也不能預先帶有「下角材 面材」材質：保色驗收只修改本次新建的夾具材質，避免碰到既有材質。不要在使用者正在工作的模型執行。

以本機 repository 路徑執行：

```ruby
load 'D:/geometry-axiom/sketchup-plugin/test_su/run_all.rb'
```

若 repository 在其他位置，替換為實際絕對路徑。腳本會 `require_relative` 載入該 checkout 的核心與轉接器；若本次 SketchUp 已載入其他版本插件，請先重啟 SketchUp，避免 Ruby `require` 快取混用版本。

驗收包含非同步 UI 復原。`load` 返回時不代表完成，請等待 Ruby 主控台最後印出「SketchUp 驗收完成，exit_code=0」或「SketchUp 驗收失敗」。執行期間不要操作模型、切換模型或手動復原。腳本每次只送出一次 `editUndo:`，收到 `onTransactionUndo` 後才檢查；5 秒未收到事件會回報失敗。

預設證據資料夾為：

```text
Sketchup.temp_dir/geometry-framing-su-YYYYMMDD-HHMMSS/
  output.txt
  result.json
  flat.png
  flat-rerun.png
  profile.png
  nested-flat.png
```

也可在執行前指定資料夾：

```ruby
ENV['GEOMETRY_FRAMING_SU_OUTPUT'] = 'D:/geometry-framing-su-evidence'
load 'D:/geometry-axiom/sketchup-plugin/test_su/run_all.rb'
```

`result.json` 含 `passed`、`exit_code`、SketchUp/Ruby 版本與逐項原始記錄。`exit_code` 是驗收結果，腳本不呼叫 `Kernel.exit`，避免關閉 SketchUp。若發生失敗，保留目前模型與證據供重現；重新驗收請另開空白模型。

驗收項目：

- 5000 × 4800 mm L 形天花面，含 400 × 400 mm 柱孔；直接把腳本 `RINGS` 常數餵給 core 作為獨立期望，比對實際產物的每種角色數量，不拿 `Selection.read` 的快照重算裁判。未旋轉夾具預期為面材 16、沿邊料 10、主支 5、副支 69。
- 從直接由 `RINGS` 算出的構件中，各抽 1 支主支、1 支副支、1 支柱邊料；實際讀取已建立元件的頂點並套用真實實例變換，驗世界 X／Y／Z 的最小及最大值（誤差小於 0.001 mm）。未旋轉的獨立期望公式為 `(x, -y, z)`。比對依角色與世界位置找料，不依 SketchUp 可能重排的外圈起點編號。
- 頂層群組、角色子群組、每支料的元件、角色 Tag、斷面／長度／規則屬性；原始幾何放在 Untagged。
- 每件元件為封閉實體；L 形與孔位裁切的多個 box 合成外皮，不留內隔板。
- 平釘與斷面都可用一次復原刪除本次全部產物，保留輸入。
- 第一次平釘產物 A 仍在模型時，同一面由左上改成左下起鋪，第二次 B 的檢查及建立都必須成功；本插件前次產物不能被當成樑。再次建立的數量與位置也用 `RINGS` 的獨立期望比對，預期為面材 18、沿邊料 10、主支 5、副支 71。
- 材質保色：生成 A 後，用一個獨立操作把本次新建的「下角材 面材」改成紅色 `RGB(255, 0, 0)`，再生成 B；確認 A／B 全部面材共用同一材質實體，且 A／B 仍為紅色，不能被新生成操作重設為預設米色。`flat-rerun.png` 記錄紅色 B 產物。接著一次復原 B（保留 A 及紅色）、另一次只復原自訂顏色（保留 A 並還原原色），最後一次復原 A；每個生成動作仍各自只需一次復原。
- 未分組獨立樑以連通幾何 bounds 被攔截，失敗項目必須只有 `obstacles`；樑底 2510 − 面材 6 − 角材高 33，因此 `suggested_ceil` 必須是 **2471 mm**。檢查失敗不新增模型實體。
- 間接照明槽：斷面有 4 塊面材、6 支縱向料、每站 4 支橫撐，沿 L 產生的實際數量與直接使用 `PROFILE_POINTS` 常數的 core 一致。
- 兩端接同一樓板的斷面能依 demo 直接封閉，不虛構 RC 牆。
- 旋轉 1°、平移後的巢狀群組輸入：與未旋轉版逐角色數量相同，並重驗主支／副支／柱邊料的世界 X／Y／Z，還有頂層產物、編輯路徑與選取保全，以及一次復原。世界位置期望用已知夾具常數手算：先 `(x, -y, z)`，加內層平移 `(500, 800, 0)`，再用 `sin`／`cos` 旋轉 1°，最後加外層平移 `(30000, 20000, 0)`；不讀取 selection 的 frame，也不以 `Geom::Transformation` 重用被測座標管道。

上述幾何、座標與復原斷言必須在 SketchUp 2026 真機執行；目前已保存的實際結果見
[完整原生 audit](../test/evidence/native-full-result.json) 與
[工作流原生 audit](../test/evidence/native-workflow-result.json)，各檔記錄當次受測來源與 RBZ 雜湊。
一般 Ruby 的 `ruby -c sketchup-plugin/test_su/run_all.rb` 只確認語法；不會載入或執行驗收。
空白模型前置條件使用官方支援的 `Entities#length.zero?`，不呼叫 `Entities#empty?`。

腳本未自動點擊 HtmlDialog。驗收者另需手動確認兩個「擴充功能 → 下角材」入口、調整參數後檢查、失敗時禁止建立、成功時建立，以及右上／左上起鋪的差異。平釘的世界 Z 可在對話框調低；斷面兩端須貼住模型中的既有 RC 參照面，接面判斷不等同材料鑑定。

斷面每次按「檢查／選起點」時，會以原生對話框列出兩端的世界 mm 座標，必須明示選擇起點。
起點會改變 demo 的轉角面材搭接，不能由邊的選取順序或實體 ID 推定。已通過的同一折線可以再次選另一端，
保留目前參數；生成使用最後一次有效檢查的起點。取消或未選端點時不建模。
更換模型、編輯路徑、選取邊或參數後必須重新檢查，不能直接沿用舊檢查產生幾何。請手動驗證 UI 呈現及按鈕狀態。

自動驗收的斷面夾具使用 `SU::Dialog.evaluate(..., start_vertex_id: vertex.persistent_id)` 明示預期起點，因此不跳出原生對話框。非互動 API 沒有明示起點或選擇 callback 時會拒絕，不會替使用者猜方向。

轉接器依據的官方 API：

- [Model.active_path=／edit_transform 與操作](https://ruby.sketchup.com/Sketchup/Model.html)
- [Entities.length：取得實體數量](https://ruby.sketchup.com/Sketchup/Entities.html#length-instance_method)
- [Material.color=／Material.==：自訂顏色與材質同一性](https://ruby.sketchup.com/Sketchup/Material.html)
- [HtmlDialog 回呼](https://ruby.sketchup.com/UI/HtmlDialog.html)
- [UI.inputbox 原生選擇](https://ruby.sketchup.com/UI.html#inputbox-class_method)
- [Face.all_connected／classify_point](https://ruby.sketchup.com/Sketchup/Face.html)
- [ModelObserver.onTransactionUndo](https://ruby.sketchup.com/Sketchup/ModelObserver.html)
- [View.write_image](https://ruby.sketchup.com/Sketchup/View.html)
