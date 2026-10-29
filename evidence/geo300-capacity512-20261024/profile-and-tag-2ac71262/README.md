# 真512 profile與未採入hash-tag候選

正式PR產品仍F2/C，完整H7原1200逾時不變。本包不是解除阻擋或跨SHA宣告。

## 真512 profile

固定8b128aa7bf53b41b493dd3a0bee49f0d53391254，原O0分離K/W/H、16MiB stack、600秒限制，加-pg純診斷。首輪父/子整group被signal9中止，無終態且非OOM（cgroup memory.events均0），完整原件/當時proc-stat保留，不捏造原因或產品timeout。之後以同一支已建ELF、同stdin在獨立session恢復：00:41:46–00:47:58Z、371.171276565秒、exit0、wait4 RSS222660KiB；stdout/stderr與8b正式512 load逐byte完全相同。沒有丟棄已完成樣本，沒有重編替代原ELF。

gprof原件self：find_node24.13秒(13.06%)、node18.72(10.13%)、edge9.47(5.12%)、contact_facts9.13(4.94%)、face_covered8.35(4.52%)、face_index_before8.24(4.46%)、node_hash7.09(3.84%)、face_index_build6.88(3.72%)。這是插裝sample，不把self總和或含子函式比例冒成正式wall。原B/F2較小場景profile仍在原E18/formalF2；不把不同N或execution當一組同條件配對。

## hash-tag實驗與不採入決定

候選2ac7126205f0079feda8a282663996a75ea12d87已一般推獨立codex/geo300-consumer-scope-20261028。只多256個uint64 tag（每context +2048bytes），先拒錯hint，hash相同仍全identity。

- 原K29/slot6/scope17與hint10共62，exit0、0fail/error/skip；四個hint具名撤回各0/1/0，原low8碰撞案例未刪；新增真正16-byte full64碰撞避免用hash當身分。相關命令/原流/build皆留存。
- 172場景plain/trace 344新程序，exit0，完整有序node/edge/value/guard/allseal與固定B原件全等。沿用E18逐檔closure，不重跑B。
- 單次N256配對：原8b現成ELF34.701295152秒，2ac34.902486973秒；各exit0、原placed_geometry斷言通過、stdout/stderr全等。只可行性診斷，沒有新增門檻或抽樣到綠。
- **沒有證明加速，不採入正式產品或下一個W候選**。保留分支、補丁與所有測試，不刪歷史。下一W排序候選從8b另開codex/geo300-ordered-runs-20261029，無改寫歷史或force。

完整H7/native/帳本/架構/browser與上游來源鏈仍阻擋；不把62/172綠當整單完成。
