# GEO-261 F2：組構實例的木工建立與換版規則

工作區原本自行決定三構件的主副支角色、方向與端點來源。這一片把既有規則搬至固定的
`woodworking/1` 前端 provider：`assemblyInstanceMembers`、`canRetargetAssemblyInstance`、
`assemblyInstanceEnd`。工作區保留來源刷新、配號、取消、草稿保存及顯示。

初建仍先檢查兩個端接與三構件限制，再向 native 配號。編輯已保存實例直接複製最新、指紋相符的
完整來源，不調用建立預設值；換版保留既有三構件身份與主副支限制。錯誤文字、原有端點更新順序、
UI 入口和保存格式維持。未改條文，沒有新增可見操作或常駐說明。

## 實際驗證

- 直接 `node --test tests/test_assembly_workspace.js tests/test_woodworking_frontend.js`：exit 0，
  69/69 通過，無 skip。兩組分別為 52（原 46，增加 6）與 17（原 15，增加 2）。
- `tests/geo261_frontend_mutations.py` 對 TEMP 真來源副本執行四個基準 suite，112 個 discovered，
  110 通過、2 個 Windows symlink 權限 skip；四個子程序均 exit 0。這不是 run_all 完整驗收。
  八個負控制各 exit 1，均要求對應測試的 `not ok`／`FAIL` 名稱與具體斷言失敗，不接受載入、語法或
  TypeError 代替抓到變異。本片新增三個控制，前五個為 F1 控制。原來源逐 byte 未變，TEMP 已移除。
- 第一輪控制腳本的草稿變異把所有構件變成主支，造成後續 TypeError；當輪因此明確 exit 1，未作
  成功證據。第二輪改為完整還原舊的工作區內建 recipe，八個控制才全達標。失敗原始記錄保存在
  repo 外 `geo261-evidence/frontend-f2-controls-v1`，成功收據與原始日志封存見本目錄
  `evidence/frontend-f2/`。
- `node:woodworking_frontend` 15 → 17、`node:tests-js` 711 → 717 已登記。後者是唯一改動子檔
  的實測增加 6；整個需要原生二進位的 `node:tests-js` aggregate 尚未重跑，不宣稱已執行。

尚未執行本片的真瀏覽器操作、native 重開舊夾具或完整 `run_all.py --build`，須由整合版後續驗收。
原生 typed annotation 與應用讀取仍是後續 F3；此片不代表全部前端木工相依已移除。
