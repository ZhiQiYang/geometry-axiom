# 候選分支三葉採用工具：準備，尚未執行

原 mature `build_tree()` 遞迴核心不變。固定唯一可寫分支為 `codex/train337-recovered-evidence-20261026`；原train、publisher HEAD/index和舊WS provider保持原身份。

`adopt_candidate_three_leaves.py` 不是通用來源放寬工具：ledger執行S10與architecture執行A各固定完整SHA；A僅比S10多決策葉，兩端mode/OID/bytes/hash必真綁；E相對A非evidence零差，F相對A/parent各精確三葉。任何其他產品、測試、SSOT差異都拒絕。

原S10 ledger的terminal/INDEX/全部123列/120execution heads/完整原件peer保持驗證；A架構四檔、原三gate、604closure、source快照與獨審必真有產物，不能拿S10四檔填A。manifest/scan四bytes不變；report/receipt與ledger三葉各必真改變。

root填 `REQUEST.UNBOUND.json` 時：

1. 最新候選parent與原publisher index SHA；目前範例parent E9a57可能因後續證據提交而過期，執行前重新核。
2. S10→A決策葉old/new完整mode/OID/bytes/hash。只核原Git身份，不推定新白名單已批准；本工具不改決策。
3. 真A架構RESULT／四檔／actual peer path+size+SHA；S10 ledger/terminal/INDEX及兩個actual peers維持原來源。
4. root確認candidate ref唯一writer、原publisher provider凍結、原件/peer與當下容量後，才把原三lease加新candidate lease設true。lease欄本身不是外部情況的證明。
5. 新副本需獨立靜審及適配的tiny反證；本目錄仍沒有真採用或新F。

原64MiB＋3x payload＋2x index reserve保留，root仍需另外把整體兩OWN 2GiB與並行容量納入排程。此工具不刪資料、不改掛載/配額、不做cache退休。

真正的操作保持：commit-tree單parent→候選本地ref預期舊值CAS→普通push明名候選ref→remote commit/tree/parent/三blob全bytes核對；原HEAD/index不變，沒有checkout或merge到main。這個CAS只允正常增加子commit，不是force push。

本次新增的 `publisher_state()` 每個關鍵階段及finally都核原HEAD bytes/index/train ref/status；舊WS完整snapshot另維持。若push或verification失敗，保留新commit/ref及原流，不reset、不假稱交付；後續按實際收據恢復。

完整native/browser/oracle沒有在此工具執行。生成ledger的S10與生成架構的A不改名為F；F可解析後再跑正式原清單，F的新架構gate與生成外部收據歸 evidence，避免衍生receipt自我SHA循環。
