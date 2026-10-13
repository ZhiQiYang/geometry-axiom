# PR217 承接 main 的三方整合

main 固定為 e95437877ed15e819fdd3dba3ce5a9d43b84eeda，本線 first parent ce95f2831b04378b88e36199b30ec545de56bea2；共同基底3156cc1c9dc4d2abc9c833974769d3ec66a9d46e。

比較兩邊對共同基底的全部改動，唯一交集tests/INTEGRATION-GATES.md；git merge-file -p ours base theirs 實跑exit0，沒有衝突標記。不是根據PR API mergeable推論。main的修改與本線必要fragment gate均保留，integration.diff是相對main的精確新增。

因直接git clone仍缺認證，使用GitHub Git-data建main base tree，保留本線current_geometry.c、subgrid_rebind.inc、四個diagnostic、變異帳本與7個新證據子樹，再建立first parent本線／second parent main的正常雙親merge commit。不是rebase、squash或force push，不合併PR。

對新tree逐一核對：公理層、決策佇列、BACKLOG、AGENTS與整個geometry-guide子樹的Git SHA均與main全等。這些只是承接已在main的內容，本線沒有改寫SSOT或閱讀器。其餘main新增/修改也由base tree保留，見audit.json。

這份提交只完成main整合；必要gate／mutation --check／完整native／正式七項的最終來源收據尚待。不將歷史有限測試說成合流後全量通過，保持draft。
