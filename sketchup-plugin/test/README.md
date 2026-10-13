# 插件獨立測試

測 `sketchup-plugin/geometry_framing/core/` 與 SU 轉接層不呼叫 API 的座標數學，
不啟動 SketchUp、不執行 geometry-axiom 原有驗收。
需要一般 Ruby 與 minitest；Ruby 3.2 為 SketchUp 2026 的目標環境。

```powershell
ruby sketchup-plugin/test/run.rb --seed 20261013
ruby sketchup-plugin/test/run_mutations.rb
ruby sketchup-plugin/test/run_mutations.rb --selftest
```

`fixtures/demo_oracle.json` 是從使用者確認的原始 demo 執行而得，並非從 Ruby 實作回填。
產生器載入完整原始內嵌 JavaScript，只停用畫面啟動，實際呼叫 `panelAxis`、`build`、
`check`、`primaryClashes`、`endFaces`、`rebuild3D`、`pfModel`、`pfChecks`、`pf3D`。
DOM 只提供不執行的事件登記；3D 僅攔截渲染器收到的盒子，保留 demo 的位置與端部讓位。
fixture 記錄來源檔名及正規化行尾後的 SHA-256。重新取樣需另備原始 HTML：

```powershell
node sketchup-plugin/test/demo_oracle.js D:/geometry-axiom-board/tasks/reference/framing-mode-demo.html
```

涵蓋五房間的每支料、板軸、記號、端面與所有 3D 盒子；八種方向/起鋪組合、參數變更、
柱邊料關閉、廚房衝突與替代方案、樑碰撞及降板；斷面兩個範例、旋轉、換邊、不同斷面與
拉伸參數及每支 3D 橫撐位置。明示驗收數字有專屬規則 assertion。
斷面另以 demo 的正反輸入證明搭接幾何會改變；fake 邊／頂點測試確認 SU 轉接遵守明示起點、
不受選邊順序影響，且拒絕缺起點、非端點與不存在的頂點 ID。

P076 加驗 D1 整數 mm 投影：12000×8000／30 mm 凹口掃描 3000 個角度，以及
3664×3668 收邊縫矩形掃描 400 個角度（含 0.2°）。障礙 API doubles 驗證前次插件產物排除、
hidden／Tag／上層 Tag 資料夾可見性、完整實例路徑；對話框 double 驗證延遲關閉回呼。
材質 double 驗證生成第二面天花不會重設第一面的使用者色彩，既有同名材質也不會被覆寫。
B1 在隔離 Ruby 子程序載入真正的 `test_su/run_all.rb`，以只有 `length`、沒有 `empty?` 的
Entities double 驗證入口，空模型只走到第一個 transaction sentinel；不產生幾何、不啟動 SketchUp。

工作流回歸另驗證選取／模型／參數快照的同步生成閘門、生成後檢查失效、起點重選及取消、
世界座標方向對應，以及舊 HtmlDialog 回呼不會影響新視窗。SelectionWatch 的 observer、timer、
模型切換與停止清理有獨立 double。狀態式 Undo journal 驗唯讀查詢保留 Redo 與一批一次復原；
真正的 SketchUp 透明交易、群組編輯及失敗回滾仍由 `test_su/` 的實機腳本判定。

突變 runner 先跑完整基準線，再複製來源與測試到系統暫存目錄，真正移除以下規則：
收邊挪縫、柱邊料、主支不可斷開、D1 取整、自產物排除、障礙可見性、對話框生命週期、
既有材質保留、B1 Entities API、過期快照不得生成、斷面起點重選、唯讀預覽保留 Undo/Redo、
群組編輯內生成的單次 Undo 邊界、建立失敗後恢復原選取，以及過期後持續更新目前選取。
D1 必須讓兩個角度掃描測試各自變紅；可見性必須讓實體及階層兩個測試各自變紅。
材質保留必須讓「第二面天花」及「原有同名材質」兩個測試各自變紅。
每個突變都要求 exit code 1、所有指定測試各有一項具規則名稱的 assertion failure、
零 errors/skips，不能靠另一個測試的失敗訊息通關。每次子程序限時 60 秒；
LoadError、啟動失敗或 timeout 均不能算偵測到。`--selftest` 包含真正的 LoadError、逾時程序及不存在的可執行檔，
驗證 runner 會拒絕這些假成功。正式程式沒有突變開關，結束前核對 core+su+test_su 的來源集合及每檔雜湊。

原始輸出可重新保存（會更新 `test/evidence/`）：

```powershell
ruby sketchup-plugin/test/record_evidence.rb
# 若也要重新生成並保存 demo oracle 執行輸出：
ruby sketchup-plugin/test/record_evidence.rb D:/geometry-axiom-board/tasks/reference/framing-mode-demo.html
```

記錄器更新 `minitest.txt`、`mutations.txt`、`mutation-runner-selftest.txt`，指定 demo 路徑時
也更新 `demo_oracle.txt`；每份含原始輸出、exit code、timeout 狀態與 core+su+test_su 來源摘要雜湊。
`p076-*.txt` 保留修前紅／修後綠的原始證據，不由記錄器覆寫。
`ux-workflow-before-abort-selection.*` 保留真 SketchUp 首輪工作流失敗：當批完整回滾後，
原生 abort 會清空選取。修正後同一 RBZ 的工作流驗收通過 73 項斷言，原始
[audit result](evidence/native-workflow-result.json) 與 [stdout/stderr](evidence/native-workflow-stdout.txt)
包含當次來源及 RBZ 雜湊；此結果來自真 SketchUp 2026。
同一份 RBZ 的完整原生套件也通過 2,874 項斷言：
[audit result](evidence/native-full-result.json)、[完整 stdout/stderr](evidence/native-full-stdout.txt)。
兩套 audit 的 runtime、loader 與 RBZ 雜湊完全一致，RBZ SHA-256 為
`77df4118d775117fc7e7f1d7f10bda24352547b45c7acd40ce521e7eb721d22a`。
原生 viewport 證據另有 [平釘](evidence/native-suite/flat.png)、
[斷面](evidence/native-suite/profile.png)、[巢狀編輯](evidence/native-suite/nested-flat.png)。
`ux-native-driver-before-runner-reset.*` 是驗收 driver 本身的首敗，產品測試尚未開始；
`ux-native-driver-reentry-{before,after}.txt` 是純 Ruby driver double 的兩輪重跑紅／綠證據，
確認既有 Runner 類別可重新建立，不宣稱驗過 SketchUp 或產品幾何。

`evidence/native-audit-driver.rb` 是本次實際使用的原生驗收入口原檔，不納入 RBZ。
它只供此 repository 在 SketchUp 2026 的獨立空模型中使用，預設從
`D:/geometry-axiom/sketchup-plugin` 讀 runtime 與 `test_su`。若驗證發行包，在 Ruby 主控台先設
`ENV['GEOMETRY_FRAMING_RUNTIME_ROOT']` 為已解壓 RBZ 的根目錄、
`ENV['GEOMETRY_FRAMING_RBZ']` 為同一份 RBZ 的絕對路徑，並設
`ENV['GEOMETRY_FRAMING_NATIVE_SUITE'] = 'workflow'` 或 `'full'`，再 `load` 此檔的絕對路徑。
兩套各用新的空白模型；它不清除既有模型。driver 複製來源快照並重新載入，保存 runtime／loader／
suite／RBZ 雜湊、完整 stdout/stderr、第一個失敗及 semantic exit code。尤其 `full` 會等候原生
Undo callback：**`load` 返回不代表通過**，只能以該次最後的 `NATIVE AUDIT PASS` 與
`audit-result.json` 的 `passed: true`、`semantic_exit_code: 0` 判定完成。

證據檔的 Ruby 版本是實際執行環境；不能拿一般 Ruby 或 HtmlDialog 的 mock 測試冒充
SketchUp 2026 驗收。SketchUp 內的測試另見 `test_su/`。
