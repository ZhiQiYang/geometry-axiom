# #323 合入目前整合樹後的進度

產品／測試來源 P：`5c29eba30a40f20ea5c7eb8dc139e5788235d3b6`。
一般 merge 的兩親為舊 #323 `239040fdc8f0b73b75640378669a1ede6a975890` 與目前整合分支 `22ad28f30c5b7c43cb004b95037583bc7b902f3c`。這是可審查的同步來源，尚非 #288 收尾之後的最終基底，也不是新的完整驗收通過聲明。

| 已做事項 | 結果 | 下一步 |
|---|---|---|
| 普通 merge 目前整合分支 | 原退出 1 停在七個 content conflicts；手動解決後 commit／一般 push 均退出 0，工作樹 clean；不 rebase、不 force push | #288 產品確定後，再普通 merge 最終整合 head |
| `reference_sources.inc` 的語意交集 | 保留 #288 的輕量 `wood_definition_sources_placement_contact`、原成功／失敗 prefix materialization；同 slot 換 member id 時清除舊 full anchor／footprint；保留 #323 其他成功值 memo 及逐 consumer kind／order 登記 | 原 load-residual、host-facts、PF3 與正式 A/B/C 重驗 |
| footprint memo 命中與 deferred raw snapshot | 命中成功明確處理 raw pending 0／2；依賴失敗保留原 prefix flush，避免完成 raw snapshot 時覆寫來源幾何 | 新具名控制：撤回 pending 修正必須正常 `ASSERT:footprint-cache-hit-preserves-source-out`、原 0／1／0 |
| 新控制夾具 | 真產品 provider 自然 warm canonical definition／BOX／footprint 後，僅把 H 的 UV 改成過期值；不偽填 memo、不改原門檻 | 尚未編譯或執行，不預填 0／1／0 |
| 靜態完整性 | 三套 AST 方法數 contact 15、host-facts 22、load-residual 13；expected JSON 可解析；三個精準撤回 anchor 均恰好一處；修改檔 diff check 0 | 等獨占測試槽實跑原工具 |
| CRLF／SSOT | `current_geometry.c`：10528 個 CRLF、0 個 bare LF；`公理層.md` 與 `決策佇列.md` 相對 incoming integration 無差異，決策 blob 為 `12d718fd62d3337c65eed7e3b13361475b948e9e` | 不改字；保留 main 合入的原文空白 |
| 帳本／架構 | 採 incoming integration 的原產物，沒有把其 SHA 改寫為新 P，沒有各自重產整份帳本 | 依 root 統一排程在最後來源上 check／必要時整份重產、重產四檔與原三裁判 |
| 對抗審查 | 已交 #318 owner；靜態審查進行中 | 修完審查再結案 |

本次開始時 repo clean、HEAD 為舊 #323，原 sparse 模式為關閉。磁碟緊縮時只將 tracked 根 `evidence/` 從此工作樹省略；5153 個路徑仍在 index／Git 歷史／遠端，原外部 streams 未刪，產品、tests、tests/evidence、fixtures 完整。模式為 `/*`、`!/evidence/`。前後觀察與完整 Git 輸出見同目錄 `SPARSE_MERGE_OBSERVATIONS.json`；這份是操作觀察紀錄，不冒稱正式測試收據。

本輪未跑任何編譯、Chrome、benchmark、native、PF3 或 mutation check；初期 root 的 P52 runtime measurement 獨占資源，後續正式測試等排程。所有未跑項的退出碼都是 null，不能以歷史 F 的綠燈替代。未修改 `tests/mutate.py`，未新增 M 編號；共同 expected 首棒已交 #314。

歷史 F=`f43e8d8b876f587c11778fa74a80b205b51396b6` 的完整收據仍留在原目錄。N64 fix/main `1.7457212386 > 1.3` 的歷史紅燈保留，沒有挪用 #288 的 2×；新 P 尚未量測。placement 單刪仍是合法生命期內的等價分類，配對反證只證第二防線，不宣稱單刪 killed。
