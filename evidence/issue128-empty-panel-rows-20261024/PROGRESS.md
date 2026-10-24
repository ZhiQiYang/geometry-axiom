# #128 P2 空板列舉：目前狀態

來源分支 `codex/issue128-empty-panel-rows-20261024`，產品／測試 SHA `324034812bb6effca68e0413bc0468595337b317`；基底 #346 `a5f1806fb3cad2dada1a56e79e01d54f9f86700f`。本目錄是後續證據提交，不把證據 head 當成另一份已驗產品。

## 已完成

- W panel layout 在真正 row 範圍內檢查最多兩個奇偶 phase；沿軸都無板本體時跳過空 body 迴圈。原 raw seam 列舉、4096 容量、status、裁切、清空與列舉順序保留。
- 原十個 panel 方法與十個既有 controls 保留；新增三方法，expected 只把 `py:test_geo261_panel_native` 10 改 13，依 AST 計數，尚非實跑結果。
- 外部產品靜審 239/0、companion v2 靜審 40/0；原草稿、修正前註解／stdout轉送缺口及 peer 初 matcher 誤判原件保留。
- 純 Python 1150 個小案例與獨立 bbox 枚舉逐序列相符，含 488 個全空案例及 19 個第一 phase 空、後續有板案例。這不是 C 原件；5000／50000000 row 是公式推導，不是已量到的時間或 mutation killed。
- 新 checkout 使用私人 Git 與指向既有 objects 的 alternates；原 #346 工作區、index、config、HEAD 均核對不變。來源已一般 push，完整 Git argv、exit、stdout/stderr、環境及來源 SHA 留在 archive。

## 唯一 current-state

| 項目 | 結果 | 邊界 |
|---|---|---|
| 外部 git apply --check／四 leaf diff --check | 0 | 靜態來源檢查 |
| Python 獨立算術見證 | 0 | 1150 小案例；非產品執行 |
| 產品／companion 靜審 | 239/0、40/0 | 正式結果仍未觀察 |
| 13 方法原 panel suite | UNRUN | 含原十個方法，不減斷言 |
| 四組新撤回／恢復、原十個 controls | UNRUN | 必須真正常 assertion 紅，不接受 crash/error/timeout |
| PF-1／PF-2／PF-3 與完整 native、受影響 browser | UNRUN | 不借 L 或 #346 歷史通過 |
| 最終突變帳本、架構三裁判／四檔收據 | UNRUN | 由主代理排最終來源；本分支未自行重產 |

## 下一步

取得主代理重測時槽後，補齊來源閉包，以原 NativeBuild／60 秒單例限制跑完整 panel suite 和四組新反證，保 fixed／withdrawn／restored 真 C 操作數及每個子程序完整原件。依產品／測試影響更新帳本與架構，完成正式整合與審查後才可標 READY。

分支順序：#343 → #346 → 本 P2 → 512。後續 512 一般 merge 本線，避免重疊 expected。沒有合併 PR、沒有 force push、沒有改公理／決策佇列。

## 尚未處理及最不確定

本片只處理 body 外層；staggered raw seam 的空外層列舉尚未優化。#128 的 P1 JSON 精度、P3 UI 回執、P4 allocator 契約及 P5 舊工具另外處理。最不確定的是真 C 的成本／撤回輸出和既有完整整合結果；目前未跑，不能宣稱此 PR 或 #128 已完成。
