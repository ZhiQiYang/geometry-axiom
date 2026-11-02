Workbench HTTP fixture 的關閉輪詢改為 `poll_interval=0.05`，保留原19項斷言與1200秒時限。已普通 merge main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`，再普通 merge 已驗工具依賴 #366 `502a64ff6214dd6060927b7f14643a533536f20d`，沒有 rebase 或 force push。#366 尚未合併，#345 的合併目標維持 main。這是待 root 發布的正文草稿，尚未套用到 GitHub。

| 項目 | 目前來源／結果 |
|---|---|
| 本地 candidate M | `577b2e81967b3019352f65df5ffe6dc48eb6202f` |
| M 普通 merge parents | `c8db6777819c844064aa79baf089ff1ce58d5e5f` ＋ #366 `502a64ff6214dd6060927b7f14643a533536f20d` |
| 前輪 main 普通 merge | `c8db6777` 的 parents 為原 #345 `99646d418bc5e886a92bfdabe33e68780e88fe3b` ＋ main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` |
| 相對 main 的來源差異 | test fixture 的 `poll_interval=0.05` 單行＋#366四個原工具檔；另保留13個原歷史 evidence 檔，Git entries 未變 |
| 原 aggregate selected19 | 實際 execution 仍為 `c8db6777819c844064aa79baf089ff1ce58d5e5f`；`python -B tests/run_all.py --build --only test_rule_case_workbench_http`；19/19、0 fail/skip、strict expected19、原1200秒；exit0，unittest27.48秒，外層含bridge建置47.284686秒。未在M重跑／移標 |
| 新來源 closure | 195個 bridge source inputs 逐Git entry等 main；產品、公理、reader、registry／expected 與 main 完全相同 |
| 歷史正式比較與 components | execution 仍為 `2199cda8896b47c7ad2b6c10479e5e0cbdb67c83`；六次 correctness 原 exit0，本次沒有重跑或移標 |
| 歷史撤回性質 | 撤回只恢復原等待時間，正確性仍綠，是等價控制，沒有宣稱 killed mutant |
| M 原 mutation:check | 真 exit1、5.384694秒；123定義／123紀錄，62 killed／1 crashed／4 equivalent／53 stale／3 retired，survived／invalid／blocked均0。53筆bridge oracle因測試來源變動而stale；M20不改算killed |
| #366 依賴／新帳本 | #366未合；四個Git mode/type/blob精確原樣採入。M尚未完整重跑123／產生或採入fresh ledger，原ledger／expected／來源hash均未手改；待發布後原Mutation evidence workflow交新收據 |
| 完整 native／browser／required CI | 此本地工作未執行；等待發布後同 final head 的正式 workflow，selected19 不代替完整驗收 |
| 狀態 | 維持 draft，尚未 READY-TO-MERGE |

本次新原流保存在本地 `/tmp/geometry-resume-20261102/pr345/`，需由 root 在發布時提供可查 evidence 連結後再同步本段。新 selected 結果、shared binary/sidecar 前後身分、來源前後身分及獨立 peer 審查均保留。三個共享 row logs 先保存新原件再恢復原 bytes；新鮮 bridge 已另存 private copy 並由原 freshness oracle 核對。本次單輪不是新的 A/B 效能量測，不將27.48秒與歷史不同來源耗時直接比較。

歷史原件仍在 `evidence/geo345-final-2199cda8/` 與 `evidence/issue214-fixture-2199cda8/`。未降低斷言、golden、時限或 expected；未新增允許 skip，未變更產品、公理或決策。
