# SketchUp 2026 內驗收

這份腳本已通過一般 Ruby 語法檢查，**尚未在 SketchUp 執行**。Minitest 通過不代表 SketchUp 幾何、HtmlDialog、編輯 context 或復原已驗收。

先在 SketchUp 2026 開一個新的空白模型，刪除預設人物等範本實體，再開啟「視窗 → Ruby 主控台」。腳本要求模型完全沒有實體且未進入群組編輯；不會清空既有模型。不要在使用者正在工作的模型執行。

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

- 5000 × 4800 mm L 形天花面，含 400 × 400 mm 柱孔；每種角色數量與 core 一致。
- 頂層群組、角色子群組、每支料的元件、角色 Tag、斷面／長度／規則屬性；原始幾何放在 Untagged。
- 每件元件為封閉實體；L 形與孔位裁切的多個 box 合成外皮，不留內隔板。
- 平釘與斷面都可用一次復原刪除本次全部產物，保留輸入。
- 未分組獨立樑以連通幾何 bounds 被攔截；檢查失敗不新增模型實體。
- 間接照明槽：斷面有 4 塊面材、6 支縱向料、每站 4 支橫撐，沿 L 產生的實際數量與 core 一致。
- 兩端接同一樓板的斷面能依 demo 直接封閉，不虛構 RC 牆。
- 旋轉 1°、平移後的巢狀群組輸入：數值正交、世界高度、頂層產物、編輯路徑與選取保全，以及一次復原。

腳本未自動點擊 HtmlDialog。驗收者另需手動確認兩個「擴充功能 → 下角材」入口、調整參數後檢查、失敗時禁止建立、成功時建立，以及右上／左上起鋪的差異。平釘的世界 Z 可在對話框調低；斷面兩端須貼住模型中的既有 RC 參照面，接面判斷不等同材料鑑定。

斷面首次按「檢查選取」時，會以原生對話框列出兩端的世界 mm 座標，必須明示選擇起點。起點會改變 demo 的轉角面材搭接，不能由邊的選取順序或實體 ID 推定。取消或未選端點時不建模；同一選取的後續檢查與建立沿用該起點，但每次都重驗它仍是端點。更換模型、編輯路徑或選取邊之後需重新檢查並選擇。重新開啟「斷面設計」也會清除起點選擇，便於改從另一端開始。請手動驗證這些互動。

自動驗收的斷面夾具使用 `SU::Dialog.evaluate(..., start_vertex_id: vertex.persistent_id)` 明示預期起點，因此不跳出原生對話框。非互動 API 沒有明示起點或選擇 callback 時會拒絕，不會替使用者猜方向。

轉接器依據的官方 API：

- [Model.active_path=／edit_transform 與操作](https://ruby.sketchup.com/Sketchup/Model.html)
- [HtmlDialog 回呼](https://ruby.sketchup.com/UI/HtmlDialog.html)
- [UI.inputbox 原生選擇](https://ruby.sketchup.com/UI.html#inputbox-class_method)
- [Face.all_connected／classify_point](https://ruby.sketchup.com/Sketchup/Face.html)
- [ModelObserver.onTransactionUndo](https://ruby.sketchup.com/Sketchup/ModelObserver.html)
- [View.write_image](https://ruby.sketchup.com/Sketchup/View.html)
