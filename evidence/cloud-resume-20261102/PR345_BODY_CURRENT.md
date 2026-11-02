Workbench HTTP fixture 的關閉輪詢改為 `poll_interval=0.05`，保留原19項斷言與1200秒時限。已普通 merge main 與 #366 工具來源，base 已改 main，並普通快轉推送官方新帳本。維持 draft；最終新 CI 尚在核收，不宣告 READY-TO-MERGE。

| 項目 | 唯一 current-state |
|---|---|
| 完整目前 head E | `79cf0f16bca9ce55b2b19e793650d5e4e2e2c5e6`；tree `c05e281326b3fe9b959e9ea8d59fcac28c067137` |
| base／依賴 | main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`；#366 工具來源 `502a64ff6214dd6060927b7f14643a533536f20d` 尚未合入 main |
| 產品／舊 CI source M | `577b2e81967b3019352f65df5ffe6dc48eb6202f`；先普通 merge main 得 `c8db6777819c844064aa79baf089ff1ce58d5e5f`，再普通 merge #366；沒有 rebase／force |
| E 採入範圍 | sole parent M；唯一改動 `tests/mutants_results.json`，逐byte等官方 Mutation evidence 產物，120個 execution.head 全保留 M，不改標 E |
| 帳本完整原件 | [M 的 Mutation evidence 41382891805](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41382891805) 全綠；123定義／120 active＝114 killed／1 crashed／5 equivalent／3 retired，其餘0；原 verifier、七個 bad-cache 0／1／0、binary／sidecar／159 bridge raw 已核 |
| 採入 SHA256／閉包 | ledger `0be90a297b4f4b4fd5a2e60d528886845cc2c8d823e912ef3b0763ba68f7eb1c`；38688 tracked entries 唯一帳本不同；185 mutation inputs、core／53 bridge oracle、runner／compiler、7 native build fingerprints／1369 input identities 全同 M |
| E 原 freshness 裁判 | `python -B tests/mutate.py --check`，獨立 peer actual exit0；stale／blocked均0、cache前後不存在。這是邏輯新鮮度核驗；下載的binary與原raw另於M核收，採入時未重新執行產品 |
| selected19 正式局部 | execution仍 `c8db6777819c844064aa79baf089ff1ce58d5e5f`；`python -B tests/run_all.py --build --only test_rule_case_workbench_http`：19／19、0 fail／skip、strict19、exit0，unittest27.48秒，含build外層47.284686秒；不移標 M／E |
| selected→M→E 閉包 | 195個 bridge source inputs 逐Git entry等main；M→E除ledger外所有來源／產品／測試一致。相對main的唯一fixture差異仍為輪詢單行，另有四原樣工具與13歷史evidence |
| M 首輪整合紅燈（保留） | [41382891799](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41382891799)：native2／3的舊帳本check失敗，complete coverage依原規則拒絕聚合；230 suites已跑、5339 pass／0 counted fail／1原允許GDI skip，但有未計數 freshness fail，整體不算通過。六browser皆過。舊M check為53 bridge stale，不回寫成綠 |
| E 正式整合／突變 | 新自動PR run [integration41387497096](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41387497096)／[mutation41387497118](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41387497118) 已觸發，原件核收中；尚不宣告全綠。API synthetic merge `058f793590301e1e58074be072d0296d432e184b` 與E同tree，實際execution仍須從各job原log核對 |

[本輪 selected19 的原命令／退出碼／完整輸出／身分與peer](https://github.com/ZhiQiYang/geometry-axiom/tree/4d44c1c2d20c57ce4fae892e9e18d17988754327/evidence/cloud-resume-20261102/pr345) 已普通推送；未將runtime ELF冒稱包含在小型公開子集。E 的 ledger bytes 可從目前 head 與上述官方 artifact 直接核對。

歷史正式比較 execution `2199cda8896b47c7ad2b6c10479e5e0cbdb67c83`、六次 correctness exit0 與等價撤回0／0／0保留。撤回只恢復等待時間，沒有宣稱 killed mutant；本輪單次27.48秒也不是新的A／B效能證據。歷史原件仍在 `evidence/geo345-final-2199cda8/` 與 `evidence/issue214-fixture-2199cda8/`。

未降低斷言、golden、時限、expected或允許skip，未改產品、公理、正典閱讀器或決策；新CI終態核收後再交審，合main由本機Claude處理。
