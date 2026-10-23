# 待複審釐清的驗收界線

本檔供後續審查判讀，不等待使用者回覆才做其他工作。未採用新的公理、數值門檻或忽略差異的規則。

## Q-323-ABC：跨功能版本的診斷文字差異

原 #323 固定歷史 base `b74f9a2ae7ade1555b9be45283adecc097fb76e3` 對列車 F `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9` 的原 175 場景／350 組比較真 exit 1。只有以下三個完整 stdout 不同：

- `_role_priority_mutant.scene`
- `_s1_p8_l_room_primary_through_reflex_extension.scene`
- `_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`

差異是列車既已採用的 #299 診斷文字：`V_EXTENSION` 增加定位邊與超出區間。來源 `6366304eb787b2a50282e4132f45e51eb7d21290`；產品的允許／拒絕、dump、完整有序來源圖及五 guards 保持一致。原 #299 的低側／高側／兩側精確文字與錯側排除均有既定正反例，不能為了舊跨版本比較轉綠而撤銷這項功能。

建議的處理是保留原跨版本 exact 紅燈與全部差異，另外使用同一列車、只撤回本次 memo 的對照版本，逐 byte 比較原175全部輸出／有序圖／guards，並做完整 memo 的性能撤回／恢復。這是新增的隔離修正證據，不把歷史紅燈重新標成綠，也不過濾 error 文字或刪除場景。N32/base、N64/main、source-call 比率的原性能分母與門檻完全不換。

後續審查須明確區分「刻意新增的診斷功能」與「#323 memo 的等價性」。在新的嚴格對照完成、審查確認這個界線以前，本線不標 READY-TO-MERGE。其他驗收、帳本、架構與後續工作照常進行。
