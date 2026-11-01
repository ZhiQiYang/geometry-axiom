# #338／#343 平面群查詢驗收

目前產品與測試來源 F：`df66452e7a514032453bea93b8b18ab74d7b1457`，分支 `codex/train337-plane-ranges-20261024`。

原三套定向裁判 wood-contact／contact-sources／reading-A 共 **36/36、零 skip、exit 0**；354 次原 compile/link 全為 0。完整撤回五處產品優化仍通過全部 39 個語意案例，工作量反證在 16 個 face 的 insert 區間得到 comparator calls **0／84／0**、正常退出 **0／1／0**。五個細控制均在具名 `plane-linear-range-oracle` 正常 assertion 轉紅並恢復。

原 `indexed-plane-coordinate` 反證也已恢復正常 0／1／0。補強只新增第三個同完整平面的較晚成員，原案例與斷言完整保留。這四行測試補強另外在同 F 做明確撤回：原 guard-controls 方法固定 0、撤回 1（`Guard survived: indexed-plane-coordinate`）、恢復 0；原來源最後乾淨還原。

歷史第一次來源 `7c4a40a…` 的 wood 13/14 紅與後兩套 `UNRUN_ENVIRONMENT` 原 100 MiB 守門紀錄完整保留。R1 的真 exit 1 沒有被改寫成 0。封包內準備時的 PROGRESS 是歷史快照，本檔為目前進度。

產品靜審 42/0、companion 198/0＋補強 19/0；正式 R2 原流獨審 3915/0、測試補強工具與原流獨審 4183/0。原件包含每項指令、退出碼、環境、SHA、完整輸出與實際編譯變體。

主代理已一般 merge 本來源，整合提交為 `8d2a69421560b83c0b69f3e82db8f5e97ccc037b`；上述 36 方法與反證的實際執行 SHA 仍是 F，沒有移標為整合提交。

尚未完成：這個 F 的完整 native／六 browser、最終帳本、架構衍生檔與正式效能量測。歷史 R5 在 `a22df116…` 的 N64/main = 1.3369644933292553 仍超過 1.3；本次工作量證據不能替代新的 wall gate。**非 READY-TO-MERGE**；主代理將另行完成整合來源的最終驗收。不 force push，不合併 PR。
