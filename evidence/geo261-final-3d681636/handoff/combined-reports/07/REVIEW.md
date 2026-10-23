# #333 ignore 修正獨立對抗審查

接受 02cb11b9762da429a3dbb0eed9151f45a65ed620 這份更窄的 ignore 修正，未發現可確立阻擋。相對 3d9bd947 僅刪 .gitignore 指定的註解及整層放行兩行；FIELD-RULES.md 原始 bytes/hash 不變，38 引文亦已與先前獨立保存的 main 決策佇列核對。遠端 source head、唯一 parent、clean status 與正常 push 符合。

23 個原 Git 指令及 1 個 launcher 的完整原 stdout/stderr/stdin、request/result、退出與時限逐一核驗。原 check-ignore 固定／撤回／恢復為 0/1/0：固定與恢復 stdout 精確指向 .gitignore:2:/*，撤回真 exit1 且 streams 空。FIELD 三階段皆維持 tracked 及同 bytes，最終恢復 fixed 並 clean。具名 ASSERT_FIELD_RULES_ALLOWLIST 是外部忽略規則斷言訊息；它不是 repo 原產品 unittest 的 AssertionError。

Fresh handoff b7e23a2 最新 #333 審查為 14:41:33Z/head3d9bd94，已說無阻擋、可合併；較早 12:35 那則才要求刪兩行。本文或新 PR 正文須保留這個時序，不能把較早須改說成最新狀態。本審查不將這項 ignore proof 冒 native/browser/SketchUp 或施工驗收，也未合 PR、未修改 live 正文。
