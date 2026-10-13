# 完整 CDP 未完成與 P87 局部診斷：原始失敗保留

本包保留四缺陷修復後，乾淨 `cb8d4e70d1659458017658d52139e2843cc5ba72` 的完整模式失敗，以及既有 GRID_SYSTEM_ONLY 模式的兩輪診斷。這是既有收據的公開整理，沒有重新執行產品、修改原件或把歷史受測 SHA 改標為後續提交。

| 輪次 | 完整受測 SHA | 模式／結果 | 完成／退出碼／golden |
|---|---|---|---|
| [完整 cb8](rounds/full-cdp-cb8-incomplete/receipt.public.json) | `cb8d4e70d1659458017658d52139e2843cc5ba72` | full，1383 通過斷言／0 失敗斷言／0 略過 | completed false，exit 1，未比較 |
| [基底局部](rounds/partial-grid-baseline-9029/receipt.public.json) | `9029a8f6bc00a9ff8de1d2b0deb844f331e032e3` | partial，346／0／0，P87 全 60 項 | completed true，exit 0，局部模式不比較 |
| [cb8 局部](rounds/partial-grid-cb8-incomplete/receipt.public.json) | `cb8d4e70d1659458017658d52139e2843cc5ba72` | partial，193／0／0，P87 僅 44 項 | completed false，exit 1，未比較 |

三輪前後 HEAD、tree、dirty 及 124 份來源雜湊各自一致，工作樹乾淨。各輪時間、實際命令、原始 log 路徑標籤及雜湊、runtime、配置 native 與當時實際直屬 bridge 身分均保留在收據及 [manifest](manifest.json)。不將三輪數字相加，也不以零失敗斷言宣稱完整通過。

完整與 cb8 局部均停在 P87 卡片 903 原 hit test：卡片中心 y=829 落在 Inspector，`Rule control unreachable`。原 layout logger 只讀幾何、hit 與 camera，沒有新增點擊、按鍵、scroll、重試或改動斷言。產品修復後的整合檢查確實執行；舊 EPERM 不能概括成這些檢查沒有執行。

後續 `3b2cc64b93a8db134706ca00d705242dc61522ad` 僅修 P87 測試進入前提：用既有真實 F 全圖快捷鍵一次，保留原 hit test、60 個 P87 斷言與拒絕 oracle。本包沒有該新 SHA 的通過結果；必要完整整合仍須另外收據，不能把 cb8 的原始失敗改綁或覆寫。

## 公開投影與身分缺口

`command.public.log`、`receipt.public.json`、解析的 `canonical-result.public.json` 只將機器根目錄、runtime 路徑及隔離 test/feedback/profile 路徑換成標籤。原始 log／收據在雲端 scratch 保留，manifest 記錄原件大小及 SHA-256；public projection 的 hash 與原件 hash 分開。逐 byte 未修改的已執行來源另有同一性記錄；公開 runner 路徑投影副本沒有被當成本輪實際執行檔。

完整 cb8 與基底局部的歷史收據沒有記錄當次 Node executable／version／hash，也沒有當次 Chromium executable hash；僅保留當次 scope PID／profile、Python version、runner 與來源 hash。其 interpreter／browser executable 身分保持 unknown，不能用現在的 Node／Chromium 補綁。cb8 局部輪自行記錄 configured executables 與當時 live Node/browser 綁定；不倒填前兩輪。三輪 actual direct-child native bridge 身分各自完整。

完整失敗的 `executor-byte-review.public.json` 是同一 executor 的 byte 核對，沒有宣稱獨立 actor，亦未宣稱重新執行。

## 另行獨立 actor 核對

[review report](independent-review/independent-actor-scoped-semantics-review.json) 與 [review receipt](independent-review/independent-actor-scoped-semantics-review-receipt.json) 由 `/root/race_review` 作者完成，executor 為 `/root/evidence_harness`。它唯讀核對同 clean cb8 七個限定 gate 的原始 network、完整 World、ownership／DOM、trusted events 與來源身分，沒有跑新的 browser／native 驗收。

report 原件 SHA-256 `c39122e2f0f79949f0d21243b85448a8f462f9c332ba92a222dec13792bf38e0`；receipt 原件 `4adddccec265c5bb75dc23d5cc40137512b1a17127b95eef19e1b865bd7a42a8`。公開投影 hash 另列於 manifest。reviewer 曾撰寫正式 20 案補測，因此不同 actor 不代表該 oracle 作者獨立；其他六個 gate 的 oracle 並非該 actor 撰寫。舊 executor 產生、檔名含 independent 的索引不是獨審，不收納為獨立結果。

review 初輪對 pre-commit dump 位置判讀錯誤的 scratch 報告與腳本亦保留；後續只按 native transport chronology 修核對腳本，產品與原 probes／oracle 未改。正式 EDGE38 當次 Node executable／version／hash 缺失維持 unknown；38 个斷言、原始 log 與實際 native 綁定仍保留。

私人 feedback、使用者資料、trace/profile、圖片、native binary／sidecar bytes 及私人 queue 原件都未公開。review report 可能保留排除 artifact 的路徑標籤與 hash metadata，沒有收入其內容。

## 歷史邊界與下一步

歷史完整 CDP 2207／0／0 仍只綁 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；9029 是後續文件與證據。#173 原完整 Windows 仍 1692／2、exit 1、completed false，dot 正在核收七份原始日誌，雲端未收到，保持 unknown；局部 P74/P75 不相加，未宣稱核過 golden。

下一步是在包含 P87 前提修正的新凍結候選保留原斷言並完成必要整合；本包的 incomplete／partial 結果維持原狀。安全 Resume、#123 已採納介面與 #54 單房成本由 root 在另外工作分支持續，不擴成 #87 多房。私人 queue v6 缺失，保留歷史 v5 水位與 current unknown，不建立空 DB。未合併或部署。
