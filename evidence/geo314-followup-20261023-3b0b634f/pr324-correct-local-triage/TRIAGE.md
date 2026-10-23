# #324 最新狀態與重疊清點

遠端 `refs/pull/324/head` 為 `4e176e830b691269cc72d021ce7e1bc0b167d621`。fresh handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 的最新【ChatGPT 審查】是 2026-10-23T06:41:43Z，對象 head `4e176e8`；review SHA256 `2fe22d6815625848c970eb43d836c2a4118d98bdc34330be47b522d6aae10aff`。審查原文與讀取命令均已封存。

PR 自身兩提交為 718f5138、4e176e83，正確 local base 是 `7dae5f21c7ca401e660450d437e60ba566218da8`。與未合入整合鏈的 main 取 merge-base 會得到 adba 並混入大量既有整合歷史，不能把那些檔當 #324 新增 scope。第一次寬比較原 raw/hash 全保留，有 caveat；本清點只採 correct-pr-local/PR_LOCAL.diff（9442 bytes，SHA256 `039ab11108e4dfbbc7245306e4f013c722342928e5253ad93751d7264e6a6042`）。

實際只改三檔，121+/2-：

| 檔案 | #324 範圍 | 與現有堆疊重疊 |
|---|---|---|
| `geometry-templates/woodworking/geometry_woodworking/model_sources.py` | 拒絕 missing／非 list faces、非 dict face、非 str feature；沿原 I32 四元組 | F3d、S3b、目前 combined／323、已知 318/noWood source 的此 blob 均仍等 PR-local base，現未發現內容重疊；未經後續 merge，不能預稱無衝突 |
| `tests/test_geometry_host_sources.py` | 公開 evaluate 柱／樑反例及三 predicate controls | 上述各角色此 blob 同 base；本 PR 新增六方法（39→45），不刪舊 assertions |
| `tests/run_all.expected.json` | 只將 `py:test_geometry_host_sources` count 39→45 | 所有 owner 都改此共用登記檔；只能依 root 的 forward 順序 union 這一個 key，不能以整檔版本覆蓋 #314/combined/#318/#323/noWood 的 counts |

Git blob/mode 比較是各來源 SHA 的靜態 metadata；318/noWood 使用已知歷史 source，後續 owner 可能再前進，正式落地前須重核。沒有 checkout／實作／編譯／測試，也沒有修改其它 owner 的檔。

目前 team 名單未見 #324 專責 owner；共同 refs/worktree 清單也未見既有 #324 branch/worktree，只有本輪 private read-only PR ref。這只能證明本輪清點沒有找到，不能替 root 指派或聲稱沒有外部 owner。排程仍由 root 決定。

最新審查留下兩項工作：

1. 在同步後同一個可解析 final SHA 補 expected/registry/discovery、受影響 importer、native＋六 browser、帳本 check 的完整原件。原 Actions 零步驟 failure 仍只屬環境；局部 45 tests 不冒 aggregate 全綠。先依 root 共有來源 forward 落地，再按正式 closure 排程，不能先用此舊 head 的收據代最終堆疊。
2. 正文改成真 base/head、45 方法、三 predicate 自證及未跑矩陣，不能沿用 718f513／41 的舊正文，不能聲稱可合併。

前輪 predicate 覆蓋缺口已由最新審查接受，不重開決策／加新數值門檻。靜態看到原控制實際是：三個 baseline 逐案跑、三個單 predicate mutant 逐案跑，最後 bytes 還原後再跑第一個 list case；不能在新收據裡捏造成原 helper 已逐案跑三個 restored。需要各案完整 0/1/0 時，應以實際執行原 cases 的追加受控收據補齊，不改 assertions／不補造舊 stdout。

建議受影響 importer 清單先核 `test_geometry_host_sources`、`test_geometry_host_native`、`test_geometry_source_runtime`、`test_geometry_host_world`，再按實際 import/fixture closure 決定，不把這份靜態候選清單當已跑。product Python 與 tests/*.py 變更可能使帳本／架構 receipt 過期，仍由原 `mutate.py --check` 及三原架構裁判判定，不能由此自行豁免或重產全帳本。
