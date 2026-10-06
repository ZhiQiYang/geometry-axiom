# #123 S5：接上既有 900px 短高度規則

[#123 S5](https://github.com/ZhiQiYang/geometry-axiom/issues/123) 明文要求「短高度斷點 900px」。本切片從 main `11dc339152e05ea811972b8c0c15ff29520207cd` 出發，只把 `space-workspace.css` 既有桌面短高度 media query 的 `max-height:800px` 改為 `max-height:900px`。既有 `min-width:721px`、規則內容及其他斷點維持原來來源。

這不是 S5 全部 UI 設計的完成聲明。welcome、共用標頭、來源流程等原規格仍有其他切片；只改斷點可能保留原本的 welcome／視角擁擠。獨立驗收將這些矩形與實際畫面列為觀察，不把斷點已啟用冒充所有重疊已解決。

## 字級與 #148

此 PR 沿用 main 字級：桌面 guide／help／view-direction 11px；手機 guide 容器 12px，guide 段落與其餘兩組仍為 11px。沒有複製未合併的 #148 字級改動。#148 的三行末尾 override 與這個 media query 不重疊；兩者的可組合驗收另用獨立本地 checkout，`GEOMETRY_SHORT_HEIGHT_FONT=12px` 明確標示該来源，不能當成本 PR 自己提供 12px 的證據。

## 可重跑的獨立真 UI 驗收

`space-short-height-acceptance.cjs` 是 standalone Playwright gate，不改共享 floor／golden，也不加入既有 aggregate 的計數。需要既有 Playwright／Chromium，以及依 repo 二進位指紋工具驗為 fresh 的 native bridge／model-base。服務、feedback 與輸出都使用自己的獨立測試環境，不能對使用者正在編輯的服務執行。

```bash
# 在此 checkout 啟動自己的隔離服務；binary 路徑需由 tests/binaries.py 驗為 fresh。
GEOMETRY_BRIDGE=/tmp/your-native/bridge \
GEOMETRY_MODEL_BASE=/tmp/your-native/model-base \
GEOMETRY_FEEDBACK_DIR=/tmp/your-s5-feedback \
python3 geometry-web/serve.py 8898

# 另一個 shell，仍以此 checkout 為 cwd。
GEOMETRY_TEST_URL=http://127.0.0.1:8898/ \
GEOMETRY_CHROME=/usr/bin/chromium \
GEOMETRY_SHORT_HEIGHT_OUT=/tmp/your-s5-unique-run \
node geometry-web/space-short-height-acceptance.cjs
```

Gate 使用寬度 1382／900／390 × 高度 800／801／804／900／901，共 15 組。真 UI 路徑：檔案 → 空間模型 → 新增空間（welcome）→ 矩形範例 → 真 HTTP/native 預覽 → Cancel；重開範例後用 Tab／Space／Enter 確認及建立，檢查完整模型、單步 metadata history、Cancel edit、鍵盤 Undo／Redo，以及 native World／revision 不變。

另以作者自建八邊凹口經真 native `surface` 命令建立 fixture，正常 UI 設定平面投影後，要求材料牆預覽。實際有限容量診斷 `SPACE_CAPACITY · I33` 必須仍可讀，Create 停用，拒絕／Cancel 不改 native／history／models。這是 #119 mandatory-wall 全量拒絕語意的可到達性檢查，不模擬失敗 result，也不讀舊 ZIP 內的 PDF。

每次結果保存 exact HEAD／tree／runtime、執行 harness 雜湊、computed styles、矩形、原始 native/history/model 快照、HTTP statuses、console 與 screenshots，輸出留在 TEMP。修改空間工作區也另執行 repo 的 `space_model_test.js`；該既有 gate 的範圍與實際終態單獨報告，不能混算成此 gate 的 assertions。

Browser plugin 不可用時使用既有 Playwright；没有 CSS injection、force click 或核心 mock。實體手機、其他瀏覽器、OS picker 與私人設計附件不在此切片驗收內。
