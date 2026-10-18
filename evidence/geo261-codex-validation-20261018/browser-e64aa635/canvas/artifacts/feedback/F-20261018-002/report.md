# F-20261018-002 · 自動擷取 · 2026-10-18 11:12:18

- 狀態:**open**
- 使用者說:(沒寫,看下面的操作紀錄與指到的元素)
- 畫面:面工作區 · 面 1(工具 select)
- 狀態快照:`{"oc": {"on": true, "tool": "select", "drawTool": null, "focus": {"t": "face", "id": 1}, "stack": [], "sel": null, "zoom": 1, "counts": {"faces": 1, "spaces": 0, "columns": 0, "beams": 0}}, "fe": {"tool": "select", "fiTab": "prop", "draftPts": 0, "lenBuf": ""}, "threeView": {"open": false, "tool": "view"}, "pendingSlot": null, "dialogs": [], "bodyClass": "", "activeElement": "body < html"}`
- 視窗:1382×900 @1x;場景:room_a.scene(/workspace/geometry-axiom/room_a.scene)
- 程式版本:e64aa635

## 回報前的操作(最後 40 筆,時間相對於按下回報)

-   -34.5s api ✓ `line canvas-pos boundary 1 60 60`
-   -34.5s api ✓ `boundary 1`
-   -34.5s api ✓ `obstacles 1`
-   -34.5s api ✓ `references`
-   -34.5s api ✓ `dump`
-   -34.5s api ✓ `source-inspect`
-   -34.5s 狀態列 工具：選取
-   -34.5s 狀態列 面 1 · 選取
-   -34.4s api ✓ `dump`
-   -34.4s 點 button#refParameterOpen
-   -34.4s api ✓ `references`
-   -34.2s 改值 select#paramSpec = "主支中線"
-   -34.2s 點 input#paramSpecValue
-   -34.0s 鍵 Ctrl+a（input#paramSpecValue）
-   -33.9s api ✓ `dump`
-   -33.7s 點 button#paramSpecSave
-   -33.7s 改值 input#paramSpecValue = "900"
-   -33.6s api ✗ `line spec 主支中線 900` → line 734: I8a: impact preview required; inspect preview, then confirm token (World unchanged)
-   -33.4s 鍵 Escape（button.btn < div.impact-actions < dialog.reference-impact < body < html）
-   -33.3s api ✓ `line cancel-preview`
-   -33.3s 狀態列 ✗ 已取消；場景保持原狀
-   -33.3s toast[error] 已取消；場景保持原狀
-   -33.1s api ✓ `dump`
-   -32.2s api ✓ `default`
-   -32.2s api ✓ `objects`
-   -32.2s api ✓ `surfaces`
-   -32.2s api ✓ `boundary 1`
-   -32.1s api ✓ `section-profile-read`
-   -31.9s api ✓ `line canvas-pos boundary 1 60 60`
-   -31.9s api ✓ `boundary 1`
-   -31.9s api ✓ `obstacles 1`
-   -31.9s api ✓ `references`
-   -31.9s api ✓ `dump`
-   -31.9s api ✓ `source-inspect`
-   -31.9s 狀態列 工具：選取
-   -31.9s 狀態列 面 1 · 選取
-   -31.7s api ✗ `line place 999 on 1 at-line guide 1` → line 737: 欄位數不對，用法：place 角材id on 承載面id at-line guide 線id｜grid 網id u|v 索引 或 at-face e索引｜h孔e邊｜t角材，可加 through 座標 或 between 擋面 擋面）
-   -31.3s api ✓ `dump`
-   -30.1s api ✗ `line place 998 on 1 at-line guide 1` → line 738: 欄位數不對，用法：place 角材id on 承載面id at-line guide 線id｜grid 網id u|v 索引 或 at-face e索引｜h孔e邊｜t角材，可加 through 座標 或 between 擋面 擋面）
-    +0.0s **錯誤** Uncaught Error: fb-auto-probe

## 錯誤

- Uncaught Error: fb-auto-probe
  ```
  Error: fb-auto-probe
    at eval (eval at <anonymous> (:1:142), <anonymous>:1:23)
  ```

## 附件

`world.scene`、`events.jsonl`、`page.html`

重現:`python geometry-web/feedback_cli.py replay F-20261018-002`
