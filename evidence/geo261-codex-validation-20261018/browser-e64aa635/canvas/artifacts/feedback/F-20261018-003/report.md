# F-20261018-003 · 自動擷取 · 2026-10-18 11:18:36

- 狀態:**open**
- 使用者說:(沒寫,看下面的操作紀錄與指到的元素)
- 畫面:主畫布(工具 select)
- 狀態快照:`{"oc": {"on": true, "tool": "select", "drawTool": null, "focus": null, "stack": [], "sel": null, "zoom": 1, "counts": {"faces": 1, "spaces": 0, "columns": 0, "beams": 0}}, "fe": {"tool": "select", "fiTab": "prop", "draftPts": 0, "lenBuf": ""}, "threeView": {"open": false, "tool": "view"}, "pendingSlot": null, "dialogs": [], "bodyClass": "canvas-composition connection-blocked", "activeElement": "body.canvas-composition.connection-blocked < html"}`
- 視窗:1400×1000 @1x;場景:來源未確認的場景
- 程式版本:e64aa635

## 回報前的操作(最後 40 筆,時間相對於按下回報)

-    -6.5s 狀態列 物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移
-    -6.5s api ✗ `dump` → 此網址未獲服務允許（403）。請使用啟動服務時顯示的本機網址。
-    -6.4s 鍵 p（body.connection-blocked < html）
-    -6.2s 點 button#connectionRetry
-    -6.2s api ✓ `dump`
-    -6.2s api ✓ `dump`
-    -0.3s api ✓ `dump`
-    -0.3s api ✓ `objects`
-    -0.3s api ✓ `surfaces`
-    -0.3s api ✓ `boundary 1`
-    -0.3s api ✓ `surfaces`
-    -0.2s api ✓ `dump`
-    -0.2s api ✓ `objects`
-    -0.2s api ✗ `surfaces` → Failed to execute 'json' on 'Response': Unexpected token '<', "<html>unav"... is not valid JSON
-    -0.2s 點 button#connectionRetry
-    -0.2s api ✗ `objects` → Failed to execute 'json' on 'Response': Unexpected token '<', "<html>unav"... is not valid JSON
-    -0.0s 點 button#connectionRetry
-    +0.0s api ✗ `objects` → Failed to fetch

## 附件

`events.jsonl`、`page.html`

重現:`python geometry-web/feedback_cli.py replay F-20261018-003`
