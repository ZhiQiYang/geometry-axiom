# #323 固定產品提交的對抗式靜態審查

審查者：`/root/own_318_reading_a`。審查對象為 `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6`，比較基底為整合分支 `22ad28f30c5b7c43cb004b95037583bc7b902f3c`。後續只加證據的 `307a18ec5972619161a59df82dcb7e765d137c90` 不冒充產品驗證 SHA。

已重新 fetch handoff，再讀 `handoff/pr-reviews/323.md`；本次權威快照為 `ea2748248d47563f8559638ccb70ec0ed21910d9`，其最新審查針對 `239040f`。本次只讀固定 tree；未啟動編譯器、測試、瀏覽器或量測。root 的 #288 獨占量測不受本次工作影響。

## 已檢查的風險

- 合流是否撤回 #288 的輕量 contact decoder：保留 `WoodMemberPlacementContact` 的原三欄解碼，以及失敗時 raw snapshot 前綴恢復。contact 沒有改成完整 anchor 解碼。
- 相同 storage slot 換 member ID 是否沿用舊值：contact 成功讀取後比較 canonical member ID，清除 full-anchor 與 footprint；full-anchor 命中也核對 ID。definition 與 pose 各自核對自己的 ID。
- 快取是否跳過 consumer 依賴：definition、anchor、pose、footprint 與 contact collection 命中仍呼叫 `geo_eval_depend`；依賴種類及插入順序有第二個真 consumer 的獨立斷言與精準撤回控制。
- 快取命中是否由 raw snapshot 蓋回過時 H 幾何：footprint 成功命中清除該 raw pending，依賴失敗仍完成原前綴。新增測例先由真 provider 自然 warm，再只改 H 的 UV；未直接灌入 memo。
- sealed graph 是否被命中捷徑改寫：sealed 路徑保留原 source 讀取；新增正反例核對完整已排序 node／edge、provider 次數、World bytes，未知 pose 仍拒絕。移除 sealed guard 的負控要求精確正常 ASSERT。
- contact collection hint 在 reset／預先 describe 後是否讀錯節點：命中核對 provider、完整 key、VALID 與 value；不符時走原求值路徑。reset／describe 測例核對節點及 edge 的插入順序。
- 直接 world-validation memo 是否跨候選或驗證存活：`app_world_validation_context` 每次重新 begin；host cache 成功才更新。所有改過的 caller 都提供有效的區域 `AppValidationInputs`，測例保留候選隔離、選定 component、原錯誤與 World 不變的斷言。
- 負控是否將 crash／build failure 算作有效反證：測試只接受正常 native exit 1 與指定 ASSERT；baseline／restored 明確要求 0。placement-key 單獨撤回仍等價的情況保留為 0/0/0，第二防線用配對控制，沒有冒稱獨立 kill。

## 結論與未完成條件

本次已讀產品差異及新增 harness／Python 控制，**未發現可由靜態證據確立的阻擋缺陷**。這僅表示程式審查目前沒有 blocker，**不是驗收通過**。

本提交仍須執行並保留：新增／受影響正式 suite、精準 0/1/0 原輸出、合流後相關架構裁判，以及新版三方 load 量測／逐位元組 dump 比對。先前 N64 的 `1.7457212386 > 1.3` 紅燈仍是原紅燈；本次沒有測量資料可改判，也未同意改門檻或搬移 gate。最終突變帳本由 root 在共同最終 SHA 整份重產，子代理不得另產一份冒充最終帳本。

後續正式對抗審結論須綁實際執行 SHA、命令、exit、完整輸出與檔案 hash；取得這些收據前，本文件不得被表述成 #323 全綠。
