# F-20261018-001 · 不符預期 · 2026-10-18 11:11:47

- 狀態:**open**
- 使用者說:P38 測試:這裡怪怪的
- 指到的元素:`button.fi-tab[data-fi-tab="components"] < nav#faceInspectorTabs` 「構件」 位置 [1216, 62, 71, 33](元素用途查 geometry-web/docs/DOM-CONTRACT.md)
- 畫面:面工作區 · 面 1(工具 select)
- 狀態快照:`{"oc": {"on": true, "tool": "select", "drawTool": null, "focus": {"t": "face", "id": 1}, "stack": [], "sel": null, "zoom": 1, "counts": {"faces": 1, "spaces": 0, "columns": 0, "beams": 0}}, "fe": {"tool": "select", "fiTab": "prop", "draftPts": 0, "lenBuf": ""}, "threeView": {"open": false, "tool": "view"}, "pendingSlot": null, "dialogs": [], "bodyClass": "", "activeElement": "textarea#fbNote"}`
- 視窗:1382×900 @1x;場景:room_a.scene(/workspace/geometry-axiom/room_a.scene)
- 程式版本:e64aa635

## 回報前的操作(最後 40 筆,時間相對於按下回報)

-    -4.2s api ✓ `boundary 1`
-    -4.1s api ✓ `section-profile-read`
-    -4.0s api ✓ `line canvas-pos boundary 1 60 60`
-    -4.0s api ✓ `boundary 1`
-    -4.0s api ✓ `obstacles 1`
-    -4.0s api ✓ `references`
-    -4.0s api ✓ `dump`
-    -3.9s api ✓ `source-inspect`
-    -3.9s 狀態列 工具：選取
-    -3.9s 狀態列 面 1 · 選取
-    -3.9s api ✓ `dump`
-    -3.9s 點 button#refParameterOpen
-    -3.9s api ✓ `references`
-    -3.7s 改值 select#paramSpec = "主支中線"
-    -3.7s 點 input#paramSpecValue
-    -3.5s 鍵 Ctrl+a（input#paramSpecValue）
-    -3.4s api ✓ `dump`
-    -3.2s 點 button#paramSpecSave
-    -3.2s 改值 input#paramSpecValue = "900"
-    -3.0s api ✗ `line spec 主支中線 900` → line 734: I8a: impact preview required; inspect preview, then confirm token (World unchanged)
-    -2.8s 鍵 Escape（button.btn < div.impact-actions < dialog.reference-impact < body < html）
-    -2.7s api ✓ `line cancel-preview`
-    -2.7s 狀態列 ✗ 已取消；場景保持原狀
-    -2.7s toast[error] 已取消；場景保持原狀
-    -2.5s api ✓ `dump`
-    -1.7s api ✓ `default`
-    -1.6s api ✓ `objects`
-    -1.6s api ✓ `surfaces`
-    -1.6s api ✓ `boundary 1`
-    -1.6s api ✓ `section-profile-read`
-    -1.4s api ✓ `line canvas-pos boundary 1 60 60`
-    -1.4s api ✓ `boundary 1`
-    -1.4s api ✓ `obstacles 1`
-    -1.4s api ✓ `references`
-    -1.3s api ✓ `dump`
-    -1.3s api ✓ `source-inspect`
-    -1.3s 狀態列 工具：選取
-    -1.3s 狀態列 面 1 · 選取
-    -1.2s api ✗ `line place 999 on 1 at-line guide 1` → line 737: 欄位數不對，用法：place 角材id on 承載面id at-line guide 線id｜grid 網id u|v 索引 或 at-face e索引｜h孔e邊｜t角材，可加 through 座標 或 between 擋面 擋面）
-    -0.8s api ✓ `dump`

## 附件

`world.scene`、`events.jsonl`、`page.html`

重現:`python geometry-web/feedback_cli.py replay F-20261018-001`
