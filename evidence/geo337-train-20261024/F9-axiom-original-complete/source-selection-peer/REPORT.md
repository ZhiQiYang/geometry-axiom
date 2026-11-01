已完成 §7 axiom 原件封包的最小來源盤點；沒有重跑產品或獨審、讀 SHM、複製大型 raw、使用 Git。

原 raw 根目錄 `/tmp/geo337-F9-axiom-original-20261025/` 以 lstat 核得 **189 regular files、12,499,444 bytes、0 links**。本清單沒有重算所有大型 raw hash；完整串流與逐檔封包校驗由 collector 執行。

實際鏈路為 v2 `run_original_specials.py` → 原 c387 `capture.py` → `/workspace/geo261-environment/reap_children.py` → F9 `geometry-core/card-reference/run_axiom_mutations.py`。`binding_guards.py` 匯入並執行來源差異守門；PREPARATION 是讀入資料。六個 V5 工具只驗 hash，這次 axiom 分支沒有執行；仍應納入原 bytes，才能完整重現 PREPARATION 的工具守門。不能把同 hash 的 V5 reaper 路徑寫成實際 argv。

建議來源恰為：完整 raw189、PREPARATION＋files四檔、external_tools八檔、host終態一檔、peer三檔，共 **206 regular files、12,652,356 bytes**，不含本清單與 collector 自己的 manifest。逐檔 exact path、bytes、完整 SHA256 與執行身份見 FACTS.json。

host終態保存 exit0 與指向原 receipt 的 summary，沒有另一個 outer launcher argv；不可推定未記錄的 shell來源。原 peer 留有428 checks、exit0與空 blocking_findings；本次只核來源與 hash，沒有重跑該獨審。PREPARATION／README中的「尚未執行」是歷史準備身份，正式實績由F9原 receipt／host／peer判讀。
