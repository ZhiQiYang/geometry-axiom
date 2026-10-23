# #314 新 guard 對抗審查：靜態結論

受審產品 leaf 為 `f61413ba785b67d2f455e4977e8b8da06050d654`，共修改 `grid_application.c` 與 `test_geo314_stagger_commit.py` 兩檔，20 行新增、2 行刪除。審查者為 combined owner，未啟動 compiler、掃描或測試。

本次未發現可確立的新靜態阻擋。修正針對已提出的漏洞：最終 ParameterRef 相同，不足以證明整筆候選都保留相同引用。它僅在最終有效 stagger 值有變，而且相同 system／axis 存在原始 ordered facts 時，改走原 `wood_grid_stagger_order_preserves`，不新增門檻、例外或公理文字。

兩個具名測項保留原 preview／confirm helpers：正例 A400→A500→direct500→A500 的 source switches 保值；反例 direct400→A500（軸已脫離 A）→重新綁 A500 的最後 source switch 為400→500，不可借相同最終 token 豁免。它們的 final ref／value 相同，正好隔離需依 ordered facts 歸因的差異。

額外對抗檢視以下邊界：

- 沒有 facts 的單行同引用改卡，仍保留原 I24 例外。
- 與其他 system／axis 無關的 facts 不強迫本軸走證據歸因。
- 前後最終 stagger 值相同仍照 I24 放行；不為中間變動後恢復同值另加拒絕，避免擴大已鎖定規則。
- 改值時仍走原連續 before／after、resolved、order、當下 source/value、最終 state 的完整核對，沒有直接放行新捷徑。

權威來源為已 fresh fetch 的 handoff `ea2748248d47563f8559638ccb70ec0ed21910d9`、`handoff/pr-reviews/314.md`、決策佇列 2026-10-22 題3B／4B與原 I24。本次使用者明示實作授權不代表 I24／D29／D10b 文本已另行核可或改動；本棒不改 SSOT 或決策。

尚未驗證：M121 撤回 guard 是否在同一新合流 source 產生正常 ASSERT 的 0／1／0；M102／M103／M105 anchors 在新合流後是否唯一；新增兩個橋接測項的完整原執行 streams。這些仍是待辦，不能以靜態覆核或 source push 冒稱產品驗收完成。root 已保留 M121；combined 仍只持有 M89–M98，不撞號。
