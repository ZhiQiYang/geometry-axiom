# F-20261121-001 · 問題 · 2026-11-21 02:14:28

- 狀態:**open**
- 使用者說:L4 核對 D05：送出這一筆（20261121c）
- 指到的元素:`span < button.project-save[data-project-action="save"] < div#projectBar` 「保存」 位置 [1336, 17, 28, 20](元素用途查 geometry-web/docs/DOM-CONTRACT.md)
- 畫面:主畫布(工具 select)
- 狀態快照:`{"oc": {"on": true, "tool": "select", "drawTool": null, "focus": null, "stack": [], "sel": {"kind": "boundary", "id": 1}, "zoom": 1, "counts": {"faces": 1, "spaces": 0, "columns": 0, "beams": 0}}, "fe": {"tool": "redraw", "fiTab": "prop", "draftPts": 0, "lenBuf": ""}, "threeView": {"open": false, "tool": "view"}, "pendingSlot": null, "dialogs": [], "bodyClass": "canvas-composition canvas-has-inspector", "activeElement": "textarea#fbNote"}`
- 視窗:1400×900 @1x;場景:未命名專案.gcanvas(/tmp/tmpyvpjkpwd.scene)
- 程式版本:e4948263

## 回報前的操作(最後 40 筆,時間相對於按下回報)

-    -9.5s 狀態列 物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移
-    -9.5s api ✓ `dump-deidentified`
-    -9.4s api ✓ `objects`
-    -9.4s api ✓ `surfaces`
-    -9.4s api ✓ `boundary 1`
-    -9.4s api ✓ `surfaces`
-    -8.8s api ✓ `dump`
-    -7.6s 點 span.file-menu-label < button#fileMenuBtn
-    -7.6s api ✓ `engineering-read`
-    -7.4s 點 button#btnNewProject
-    -7.4s api ✓ `dump`
-    -7.3s api ✓ `objects`
-    -7.3s api ✓ `surfaces`
-    -7.3s 狀態列 ✓ 已建立空白新專案；可復原回上一份專案。
-    -7.3s toast[ok] 已建立空白新專案；可復原回上一份專案。
-    -6.7s api ✓ `dump`
-    -5.8s 點 svg < span[data-icon="vertex"] < button#btnNewPoly
-    -5.8s api ✓ `newid`
-    -5.8s api ✓ `line history-begin`
-    -5.7s api ✓ `line boundary 1 outline 0,0 4000,0 4000,3000 0,3000`
-    -5.7s api ✓ `section-profile-read`
-    -5.7s api ✓ `line canvas-pos boundary 1 431 298`
-    -5.6s api ✓ `line history-end`
-    -5.6s api ✓ `objects`
-    -5.6s api ✓ `surfaces`
-    -5.6s api ✓ `boundary 1`
-    -5.6s 狀態列 ✓ 面 1 已建立 · Ctrl+Z 復原
-    -5.6s toast[ok] 面 1 已建立 · Ctrl+Z 復原
-    -5.5s api ✓ `boundary 1`
-    -5.5s 狀態列 工具：選取
-    -5.5s 狀態列 面 1 · 選取
-    -5.5s 狀態列 工具：重畫外環
-    -5.5s 狀態列 面 1 已建立預設矩形；逐點畫出外環，完成草稿後取代。Esc 返回會保留此面，Ctrl+Z 可復原建立。
-    -5.1s api ✓ `dump`
-    -4.3s 鍵 Escape（body < html）
-    -4.3s 狀態列 物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移
-    -3.8s api ✓ `dump`
-    -1.5s api ✓ `dump`

## 附件

`world.scene`、`events.jsonl`、`page.html`

重現:`python geometry-web/feedback_cli.py replay F-20261121-001`
