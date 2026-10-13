# 插件獨立測試

測 `sketchup-plugin/geometry_framing/core/` 與 SU 轉接層不呼叫 API 的座標數學，
不啟動 SketchUp、不執行 geometry-axiom 原有驗收。
需要一般 Ruby 與 minitest；Ruby 3.2 為 SketchUp 2026 的目標環境。

```powershell
ruby sketchup-plugin/test/run.rb --seed 20261013
ruby sketchup-plugin/test/run_mutations.rb
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

突變 runner 先跑完整基準線，再複製 core 與測試到系統暫存目錄，逐一真正改掉收邊挪縫、
柱邊料、主支不可斷開的實作，執行各自具名測試。只有 exit code 1、恰一項 assertion failure、
零 errors，且訊息含規則名稱才算偵測到。正式 core 沒有突變開關，結束前另核對原檔雜湊。

原始輸出可重新保存（會更新 `test/evidence/`）：

```powershell
ruby sketchup-plugin/test/record_evidence.rb
# 若也要重新生成並保存 demo oracle 執行輸出：
ruby sketchup-plugin/test/record_evidence.rb D:/geometry-axiom-board/tasks/reference/framing-mode-demo.html
```

證據檔的 Ruby 版本是實際執行環境；不能拿一般 Ruby 或 HtmlDialog 的 mock 測試冒充
SketchUp 2026 驗收。SketchUp 內的測試另見 `test_su/`。
