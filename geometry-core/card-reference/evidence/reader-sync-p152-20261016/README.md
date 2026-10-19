# P-152 正典標準同步與驗證

完整 native 受測 head：`82e439e32ba31c1eddd04cae58c967c4054d3295`。依 P-152 與 AGENTS.md，只執行既有 `sync_axiom_reader.py` 原位同步唯一正典；沒有 HTML 副本、手改 HTML、條文變更或測試放寬。雲端 native，非正式 WSL 收據。

實際追溯差異是 **I74 none → partial**；ok 維持 62，partial 32→33，none 113→112。原閱讀器測試由追溯器動態推導期望，沒有寫死 I74=partial，故完全未改測試。追溯器只以既有主檔條號／scene／官方 mutant 的弱代理推導；本輪沒有擴大掃描範圍或把 Python 具名測試冒充 scene 連結。

`trace-diff.json`、`i74-sites.json`、before/after.json 與 generated-trace.diff 提供全部變動、兩個原始碼條號位置與前後差異。正典只改四行。全部 reader state 欄位摘要相同（含條文、blocks、批註、提案、draft、document identity/hash），公理／白話／決策佇列／核心／同步器／閱讀器測試的 byte hash 均未變。

同步：exit 0、84 patches；check：exit 0、patches 0、207 條、五道 assert 與獨立 SSOT pass。直接閱讀器 41/41，118.666 秒；沒有 errors／skips。直接測試啟動於原 head 加同步後 HTML，隨即以相同 bytes 提交為本次完整受測 head；完整 native 在該已提交 head 重驗全部 41 題。

完整 `ulimit -s 16384; python -u tests/run_all.py --build`：99 suites、3031 計數／3030 pass／0 fail／1 既有 GDI skip、exit 0；原始 exit、時間與每個 suite 日誌見 summary.json／ZIP native/。沿用既有 expected，沒有 update-expected、降低數量、新增 skip。官方 mutation --check 另有原始輸出，原 B1 變異證據仍綁原始 9ba75476，這輪未重跑那些變異。

ZIP 收 256 份原件與逐檔 SHA-256；未收完整 HTML 副本或執行檔。上一輪六個閱讀器 failure 保留於 b1-adoption-20261016，沒有覆寫。本輪不接入 B2/S1；正式 WSL 七項、身分帳與 UI 邊界仍待後續。
