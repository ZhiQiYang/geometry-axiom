# #314 對抗審查：靜態發現，動態待驗

審查對象的歷史產品為 `cc67e2518f6ab331b5ab9fdbcd5bd6334134377f`，來源分支 `codex/geo314-one-axis-stagger-20261022`。權威留言讀自 handoff `ea2748248d47563f8559638ccb70ec0ed21910d9` 的 `handoff/pr-reviews/314.md`，並對照 2026-10-22 鎖定的題 3B／4B。

靜態找到 `wood_grid_stagger_value_changed` 只因最終 ParameterRef 相同便直接回 false，使呼叫端略過該軸 ordered facts 的邊界。以舊 u=A400、v300，比較以下同最終 ref/value 的兩條路徑：

- 正例：A 改為 500 → u 換 direct500 → u 綁回 A500。兩次換來源的當下有效值均保值。
- 反例：u 換 direct400 → A 改為 500（u 已脫離 A，仍 400）→ u 綁回 A500。最後換來源由 400 變 500，依鎖定的當下值歸因不是保值。

兩條路徑的 final stores 與 final ParameterRef 完全相同，不能只看前後 token。這個反例不要求新增中間軸數限制或數值門檻。owner 已接手修正並準備具名正反例與撤回新 guard 的 M121；本審查尚未看到同一新 SHA 的實際 0／1／0，因此不宣稱缺陷已動態確證或修正驗收通過。

程序上，本次實作授權來自使用者目前指示及已鎖定決策，不把早先代理的解讀冒稱使用者已核可 I24／D29／D10b 全文差異；本分支不改 SSOT 或決策佇列。歷史 M110 是 equivalent，不能把 M99–M120 寫成全部 killed；原 paired controls 的證據與單一等價 mutant 要分列。

靜態未見新增第二次 candidate evaluate／seal／publish；私有參數快照與原橋接交易流程的檢視不能代替完整 P177 動態計數。巢狀參數包、超過八筆 facts/realloc/OOM 及 post-confirm fault 等既有未驗邊界仍須如實列出。
