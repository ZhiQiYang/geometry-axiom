# #323：同步目前 GEO-261 整合樹，保留來源讀取快取與原守門

同一次候選驗證可重用成功解碼的 member／pose／footprint，每個 consumer 仍登記原 dependency kind 與順序。本輪用普通 merge 同步目前 #288 整合分支，人工保留 #288 的輕量 contact decoder 與 raw snapshot 契約，並補 footprint memo 命中後不能被過期 H raw 值覆寫的控制。

**目前是可審查的來源同步，完整新來源驗收尚未執行，不能合併。** #288 最終來源確定後仍須再一般同步並固定 #323 final SHA。沒有 rebase、force push、合併 PR、改公理／決策原文、放寬斷言或數值門檻。

## 唯一 current-state 矩陣

| 角色／關卡 | 目前來源與原退出 | 狀態 |
|---|---|---|
| 本輪產品／測試 P | `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6` | 已一般 push；這是普通 merge commit |
| 本輪 evidence head E | `307a18ec5972619161a59df82dcb7e765d137c90` | 只增加進度與操作觀察，不替換 P 的產品內容 |
| merge 的兩親 | 舊 #323 `239040fdc8f0b73b75640378669a1ede6a975890`；整合 `22ad28f30c5b7c43cb004b95037583bc7b902f3c` | merge 原 1 停在七個 content conflicts，解完 commit／push 原 0 |
| #288 收尾後 final base／#323 final F | 未固定；exit `null` | #288 尚在雲端驗收，不能宣稱目前已是最終基底 |
| 靜態完整性 | 原 0 | AST 方法數 contact 15／host-facts 22／load-residual 13；expected JSON 可解析；修改檔 diff check 0；C 為全 CRLF |
| 新 raw-snapshot／memo 相容修正的撤回反證 | exit `null` | 新具名控制已提交，尚未編譯或執行；不得預填 0／1／0 |
| 完整 `ulimit -s 16384; python3 tests/run_all.py --build` | exit `null` | 新 P 尚未跑；#288 的 native 或舊 #323 收據不替代此項 |
| 必要八套／修復受影響 suites | exit `null` | 新 P 尚未跑 |
| 完整原 PF3（baseline20／19 mutants／restore20） | exit `null` | 新 P 尚未跑；不縮減 CASES |
| 175 場景 A/B/C | exit `null` | 新 final base／fix 的完整 stdout、每次 seal 有序圖、五 guard 計數待重驗 |
| 36 筆三方交錯載入性能 | exit `null` | 新 P 尚未量測；保留原順序與原門檻，不重抽樣 |
| 四次原 gprof | exit `null` | 新 P 尚未跑 |
| `tests/mutate.py --check`／完整帳本 | exit `null` | 目前採 incoming integration 的原帳本；由統一排程在最後來源 check、必要時整份重產，不改寫來源 SHA |
| 架構三條原裁判／四檔收據 | exit `null` | 目前採 incoming integration 的原四檔，尚未宣稱對新 P 有效；依最後來源統一刷新與重驗 |
| 對抗審查 | 尚未結案 | 由 #318 owner 審新來源；不能以本段靜態檢查當複審通過 |
| 允許 skip | 本輪尚無實跑 skip | 唯一預期可接受的是原具名 Windows GDI allowlist；其餘不得以環境理由改成通過 |

本輪證據：[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/307a18ec5972619161a59df82dcb7e765d137c90/tests/evidence/geo261-load-residual-20261023/postmerge-5c29eba3/PROGRESS.md)、[QUESTIONS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/307a18ec5972619161a59df82dcb7e765d137c90/tests/evidence/geo261-load-residual-20261023/postmerge-5c29eba3/QUESTIONS.md)。本輪尚未產生正式測試 streams；操作觀察紀錄不冒稱驗收收據。

## 最新審查回覆與修正範圍

最新審查以 handoff 分支 `handoff/pr-reviews/323.md` 收錄的 head `239040f`、2026-10-23 02:35:55 為準。

1. **final base 同步。** 已普通 merge 目前整合 head，人工處理 source conflict，沒有直接沿用舊 A/B/C。#288 收尾後還要再同步最終整合來源；PR retarget 到 main 仍等 #288 入 main，由使用者操作。
2. **current-state 與門檻 scope。** 上表只列本輪狀態。原 N64 fix/main ≤1.3 仍保留為要求；歷史 F 的 `1.7457212386 > 1.3` 與總 wrapper 1 沒有抹掉，尚未用新 P 關閉。沒有自行把門檻移往 #300，也沒有借用 #288 的 2×。若新量測仍未達，照實列紅並由使用者決定具名後續 owner／PR 或維持本 gate。

本輪 `5c29eba3` 的 source conflict 解法：

- contact 路徑保留 #288 的 `WoodMemberPlacementContact` 輕量 parser、完整格式驗證、每次原 source 讀取及失敗 prefix flush，未改回 full anchor decoder。
- 不新增第二份 contact anchor memo。成功讀 contact 欄位後若 storage slot 的 canonical member id 改變，清既有 full-anchor validity 與 footprint；full-anchor miss 共用同一具名 invalidator。其他 definition／pose key 與逐 consumer kind／order 不變。
- footprint memo 命中時維持 raw pending 0／2；dependency 失敗仍完成原已訪問 prefix。這防止最後 raw materialization 把正確 source footprint 蓋成過期 H 值。
- 新控制先用真產品 provider 自然 warm canonical definition／BOX／footprint，再只改 H UV 成過期值，未偽填 memo。撤回 pending 修正預期必須以 `ASSERT:footprint-cache-hit-preserves-source-out` 正常退出 1；真實 0／1／0 尚待執行。
- `tests/run_all.expected.json` 合併兩邊新增方法：contact 15、host-facts 22、load-residual 13，沒有降低原計數。`tests/mutate.py` 未改，未新增 M 編號。

先前 prompt 第1–5項的 harness、PF3 anchor、W collection kind/order、member id／失效、sealed guard 修復已由最新審查記錄接受；本輪保留這些測試與斷言，會在新 final closure 重驗，不能用舊綠燈替代。placement guard 單刪仍明列合法 immutable graph 內的 equivalent 0／0／0；先撤 anchor invalidator 的配對 0／1／0只證第二防線，沒有冒稱單 fault killed。

## 雲端環境與未跑項

本輪只讀與編輯時，root 正在獨占執行 #288 的 P52 runtime proof；沒有同時編譯、Chrome、benchmark 或重產帳本。後續正式驗收等雲端排程，不使用使用者電腦。

磁碟緊縮時，此 repo 只以 sparse checkout 省略 tracked 根 `evidence/` 的工作樹副本；5153 筆仍在 index、Git 歷史及遠端。產品、tests、tests/evidence、fixtures 完整，原外部 streams 未刪。模式與前後 HEAD／status／磁碟觀察均封存；這不構成任何測試 skip。

歷史完整證據仍在 `tests/evidence/geo261-load-residual-20261022/final-f43e8d8b/`，綁定舊 F=`f43e8d8b876f587c11778fa74a80b205b51396b6`；此處只保留其 provenance，不把數字套到本輪 P。

## 最不確定的地方

新整合 source conflict 的完整有序圖與 raw snapshot 等價尚待實跑；N64 原1.3目標的新實數未知；#288 最終產品來源尚未固定。以上皆保留未完成，收到審查缺陷會直接修正並做真撤回反證，不放寬原斷言。
