# 組構規則操作

Refs #19 #23. 能力 `assembly-rule-authoring/1` 只做規則編輯、驗證與角材來源綁定，不生成施工角材（#25）。

1. 正式畫布「建立物件 → 組構規則」。
2. 空白規則可新增角色、構件位置與局部接合。示意標明「規則示意，非施工尺寸」。
3. 草稿留在工作區；發布走 `assembly-preview` / `assembly-confirm`，取消不寫 World。
4. 組合用 `put-binding`，材料未選可保存，錯型或不存在的來源會被核心拒絕。

橋接指令：`assembly-read`、`assembly-preview <file>`、`assembly-confirm <token>`、`assembly-cancel <token>`。
