# 2026-10-09 外環邊長度：送出期間的較新輸入

產品提交的父節點是 `c0def319b49a45512489535b6bea526ccb5f6aec`。三輪都在工作樹 `D:\geometry-axiom-inspector-draft`，分支 `fix/inspector-draft-redraw-20261008`。bridge 沒有重編，SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`，783872 bytes。沒有新的未簽章 exe。port 8915 的舊服務沒有停。

測試是 `geometry-web/edge_draft_redraw_test.js`。它會自己開服務與 headless Chrome，並要求 `GEOMETRY_BRIDGE_EXECUTABLE`。這不是完整主介面，也不比較 golden。

## before

產品位元組仍是 `c0def31` 的 `app.js`，SHA-256 `e3ac17509120a90c635878530608400e0dbdf25f85f6938f47da404cda3c96b5`。測試檔 SHA-256 `76031182e1cc3c56ea24c098edebb77e867bfd49446684711a765760078e4f5e`，與後來提交的測試不同。runtime `4ffb7d8fba3018c0839dbb68b6f4c33ba68fc3b290db528dde8338f7603fd4ac`，fresh，pid 37228，session `471c009549044e29929d0259289c1a07`，port 51364，CDP 51365。`NODE_EXIT 1`。通過 6、失敗 16。

同一欄位在成功送出期間改成 `610` 後，欄位回到 `500`、世界是 `500`。拒絕期間改成 `620` 後，欄位回到 `400`、世界維持 `400`。主畫布 1400 與面內 1400、390 都是這個結果。

這一輪還有測試本身的失敗，沒有當成產品缺陷修：390 主欄去點了沒有盒子的 `#toggleRight`；成功套用與再次輸入在世界更新前就讀了寬度；三視圖後未送出的 `777` 仍在欄位，世界仍是 `400`。後者符合保留較新輸入，斷言在下一輪改成期望 `777` 留著且不套用。

## redraw-commit

這輪的 `app.js` SHA-256 是 `d6deb365c83a88b57b82f49abb1f02abf4b4e8b70e2dc69315409b3f7fea8079`。測試檔已是提交版本 `70c9fb4f8797ccf76408eb028029fe073929d3a78b90f64733e658fe1cfedb87`。runtime `1ba87593593fa0c5792325c8aed2e8440a652a3ccae6774d91c2222279065187`，fresh，pid 4676，session `a884f9420b6c4444911e012dd09e8231`，port 62190，CDP 62191。`EDGE_RESULT` 通過 18、失敗 8、completed false。log 裡的 `NODE_EXIT 0` 是 cmd 在 node 結束前就展開的 `%ERRORLEVEL%`，不是 node 的結束碼。

失敗是 1400 與 390、主畫布與面內：欄位 `610` 時世界也變成 `610`；欄位 `620` 時世界也變成 `620`。重繪移除聚焦欄位時，瀏覽器把較新的文字又送出一次。

## after

最終 `app.js` SHA-256 `a0545004a061402b645f785bbc883d60137b417399f9c46c5d0323dc7f2297d2`。測試檔 SHA-256 與上一輪相同。runtime `9db2394ed4b390e6a99b125fff34fda2fcf6e5cf534daeef6a6b600abbdce490`，fresh，pid 20348，session `973fc6a08015450b83c1b051250cb835`，port 51273，CDP 51274。`NODE_EXIT 0`。通過 26、失敗 0。

1400 與 390 都包含：成功套用 `500` 並在再重繪後維持；成功送出期間的 `610` 留在欄位且世界是 `500`；超過 100 km 的拒絕期間 `620` 留在欄位且世界是 `400`；`0` 回到模型且世界不變；同欄再輸入 `450` 會套用；未送出的 `777` 不會帶到另一個邊界，返回也不復活；三視圖不復活被拒絕的 `0`，未送出的 `777` 留在欄位且世界仍是 `400`。主畫布與面內都跑了送出期間的兩條路徑。沒有未捕捉例外，也沒有主控台錯誤。

實體手機、人工 IME、作業系統儲存對話框沒有驗。完整主介面沒有在這三輪重跑。
