# 有界宿主快取下的子格堆疊回歸

第一輪完整 native（eb000675）為 2847 過／7 失敗／1 具名略過、actual exit 1；其中 6 題是正典 R41 追溯同步，另 1 題是子格重宣告 bridge 異常關閉。原件與 204 個原日誌的封存保留在 native-before-subgrid。

subgrid_commands.inc 原有 trial／backup 兩份 World 占同一函式 frame。新增宿主快取使 frame 增至 0x7688a8 bytes；trial 改 malloc，診斷擷取後 free，frame 降至 0x3b47d8。正常解析、候選、重驗及回滾順序不變；配置失敗在改世界前拒絕。

原有 31 題子格測試在同 16 MiB stack 下全綠，未改斷言或預期。撤回堆疊修正的控制另保存原生退出碼，與六個領域斷言型負控制分列；還原後再跑同一具名子格案例。ASAN 僅為堆疊診斷，O1 加儀器造成更早在 setup 主格建立時 overflow，不冒稱它是 release 精確失敗位置或已通過 sanitizer。

範圍外必要變更：model_base.c 3 增／1 刪，subgrid_commands.inc 7 增／4 刪，共 15 行變動；都是保留 16 MiB 預算的 World 儲存期調整。未改幾何、條文或 native 數量；依看板 ≤20 行必要例外直接做，附 143 場景、31 子格及撤回控制。完整 native 必須在本檢查點後重跑，不能把前一輪 7 紅當作已全部解除。
