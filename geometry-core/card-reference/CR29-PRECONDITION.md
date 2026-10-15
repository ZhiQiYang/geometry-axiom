# 任務 20：CR29 前提核對，停止擴大實作

依 `ops/agent-board` 的 2026-10-15 晚平行工作窗口，只處理指定任務 20。
分支疊在 #193 `6236f5733052a19362132738a4eb79cac7924e0b`，沒有修改產品程式。
看板要求「若 CR29 的前提不成立（D25 匯出時角材的依賴閉包沒有含到 D29、D30），停手回報，不自行擴大閉包」。

## 實測與需要核對的邊界

對 #250 `f3f99a29` 的 CR29，先只檢查既有鏈 `T → N → B → G`：
角材 1 已合法放置於 `at-line grid 10 u -1`；主格 10 來自配置 2；配置 2 引用網格 4。
新整卡關係 `G → P → Q` 尚未實作，不用逐欄引用冒充整卡正例。

實際 D24 請求為 timber 1、role=geometry、target=solid-set、allow_partial=false。
`build_package` 得到 COMPLETE，`verify_package` 重算成功，但匯出器真正的 `selected` 根走訪集合只有：

```json
[["placement",1],["timber",1],["timber",90],["timber",91]]
```

其中沒有 D10 主格 10、D30 配置 2、D29 網格 4。C adapter 的 `dependencies` 同樣只有 placement/timber。
讀回位置：`geometry-core/model_base.c:186` 明示這是把 guide/grid 折疊後的幾何依賴；
`:191` 的集合只含 placements/timbers/guides；`:270` 起沒有發出主格、配置或網格的依賴紀錄。
`geometry-core/modeling/engine.py:415` 起依這份表計算根走訪集合。

**另一方面，不能說 D25 交換包已遺失 D29/D30 定義。**
`model_base.c:374` 使用完整 World dump，`engine.py:491` 原樣保留 canonical base_scene。
所以本次包的 definitions 確實含原始 grid/grid-binding/grid-system，保存來源關係且可成功重算。
另選沒有網格定位的收邊角材 90 為根，兩包的 base_scene 仍逐字相同：這是保留整份場景，不是該根走訪圖列出了網格。

需 Claude 核對看板的「依賴閉包含到 D29/D30」是否要求根走訪圖具有這條鏈，
還是完整場景已保留必要來源就足夠。若要求前者，必須補既有非幾何依賴閉包，正是看板明示不得自行擴大的前提；
若接受後者，可以保留現有幾何走訪並續做整卡來源。**這份報告不裁決哪一種解讀，也不宣稱既有 D25 違反公理。**
依停手紀律，此輪只交唯讀探針及原始證據，等待範圍核對，沒有先改閉包或整卡產品碼。

## 重現與證據

在 repo 根目錄執行，輸出目錄須不存在：

```sh
ulimit -s 16384
cc -std=c11 -O2 geometry-core/model_base.c -lm -o /tmp/geometry-task20/model-base
GEOMETRY_MODEL_BASE=/tmp/geometry-task20/model-base \
  python geometry-core/card-reference/probe_cr29_precondition.py --output /tmp/cr29-fresh
```

探針 exit 2 表示 `BLOCKED_SCOPE_REVIEW`，不是新產品測試 killed，也不是執行器拒絕此合法場景。
不改 native suite 或 expected，不新增 skip。`sys.settrace` 只在此次呼叫唯讀擷取真正 evaluate 的 selected，finally 還原 trace。

原始證據在 [evidence/cr29](evidence/cr29)：輸入場景、adapter snapshot、完整交換包、對照包、report、stdout 與實際退出碼。
`report.json` 保存當次來源 head、原始來源 bytes SHA256、探針 SHA256、實際 binary SHA256、OS、Python 與 stack limit。
證據是提交探針之前在 claim head `9a04d90547aa50727b8947131efedf7e17ebbf40` 執行的結果；
產品來源與 #193 head 相同，不把證據說成後續提交已跑的結果。

環境 Linux，gcc 14.2.0、Python 3.12.14，stack 16 MiB。adapter 編譯 exit 0；探針 exit 2；匯出／重算成功各一次，並執行一次不同根對照匯出。
**雲端 native,非正式 WSL 收據**。這只是前提定位，沒有執行完整 native，也沒有整卡實作、CR01–CR33 驗收、§7 真突變、官方突變帳本重產／check、完整專案保存或正式七項收據。

請 Claude 核對。
