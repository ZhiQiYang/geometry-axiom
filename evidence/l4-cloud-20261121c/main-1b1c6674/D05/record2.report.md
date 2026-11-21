# F-20261121-002 · 不符預期 · 2026-11-21 02:14:31

- 狀態:**open**
- 使用者說:(快速標記:使用者按 Shift+F8,當下覺得不對)
- 畫面:主畫布(工具 select)
- 狀態快照:`{"oc": {"on": true, "tool": "select", "drawTool": null, "focus": null, "stack": [], "sel": {"kind": "boundary", "id": 1}, "zoom": 1, "counts": {"faces": 1, "spaces": 0, "columns": 0, "beams": 0}}, "fe": {"tool": "redraw", "fiTab": "prop", "draftPts": 0, "lenBuf": ""}, "threeView": {"open": false, "tool": "view"}, "pendingSlot": null, "dialogs": [], "bodyClass": "canvas-composition canvas-has-inspector", "activeElement": "body.canvas-composition.canvas-has-inspector < html"}`
- 視窗:1400×900 @1x;場景:未命名專案.gcanvas(/tmp/tmpyvpjkpwd.scene)
- 程式版本:e4948263

## 回報前的操作(最後 40 筆,時間相對於按下回報)

-   -12.6s 狀態列 物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移
-   -12.5s api ✓ `dump-deidentified`
-   -12.5s api ✓ `objects`
-   -12.5s api ✓ `surfaces`
-   -12.5s api ✓ `boundary 1`
-   -12.5s api ✓ `surfaces`
-   -11.9s api ✓ `dump`
-   -10.7s 點 span.file-menu-label < button#fileMenuBtn
-   -10.6s api ✓ `engineering-read`
-   -10.4s 點 button#btnNewProject
-   -10.4s api ✓ `dump`
-   -10.4s api ✓ `objects`
-   -10.4s api ✓ `surfaces`
-   -10.4s 狀態列 ✓ 已建立空白新專案；可復原回上一份專案。
-   -10.4s toast[ok] 已建立空白新專案；可復原回上一份專案。
-    -9.8s api ✓ `dump`
-    -8.9s 點 svg < span[data-icon="vertex"] < button#btnNewPoly
-    -8.9s api ✓ `newid`
-    -8.8s api ✓ `line history-begin`
-    -8.8s api ✓ `line boundary 1 outline 0,0 4000,0 4000,3000 0,3000`
-    -8.8s api ✓ `section-profile-read`
-    -8.7s api ✓ `line canvas-pos boundary 1 431 298`
-    -8.7s api ✓ `line history-end`
-    -8.7s api ✓ `objects`
-    -8.7s api ✓ `surfaces`
-    -8.7s api ✓ `boundary 1`
-    -8.6s 狀態列 ✓ 面 1 已建立 · Ctrl+Z 復原
-    -8.6s toast[ok] 面 1 已建立 · Ctrl+Z 復原
-    -8.6s api ✓ `boundary 1`
-    -8.6s 狀態列 工具：選取
-    -8.6s 狀態列 面 1 · 選取
-    -8.5s 狀態列 工具：重畫外環
-    -8.5s 狀態列 面 1 已建立預設矩形；逐點畫出外環，完成草稿後取代。Esc 返回會保留此面，Ctrl+Z 可復原建立。
-    -8.1s api ✓ `dump`
-    -7.3s 鍵 Escape（body < html）
-    -7.3s 狀態列 物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移
-    -6.9s api ✓ `dump`
-    -4.6s api ✓ `dump`
-    -0.0s 鍵 Shift+Shift（body.canvas-composition.canvas-has-inspector < html）

## 附件

`world.scene`、`events.jsonl`、`page.html`

重現:`python geometry-web/feedback_cli.py replay F-20261121-002`
