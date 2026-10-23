# 接續 #337：閱讀 A 列車與相依資料快取修正

本 PR 接續 #337 的 #299+#316、#314、#318 閱讀 A，保留使用者 10-24 核可的 RC 未覆木連續段量法，並處理已包含在列車中的 #323。從 Claude `3cbeb759` 開自有分支後，一般 merge main `eda91c85`；原歷史保留。本 PR 通過正式驗收及最新審查後取代 #337，目前仍是 draft。

新修正為接觸資料的成功解碼增加獨立 key 的 memo；命中時仍向目前 consumer 記錄原相依 kind/order。兩個漂移的負控制改回正確 API 與實際讀取路徑，保留原斷言並增加四個 contact controls。尚未以效能結果證明收益。

## 唯一 current-state 矩陣

| 項目 | 來源／exit／狀態 |
|---|---|
| 產品 SHA F | `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`，已普通 push 並核對遠端 |
| 證據 head E | `59447bfe775ec9c918b9e4e3f29417eb725cf12f`；只有 evidence 差異，F 的四檔產品／測試採用指令、完整 raw、環境及 hash 已封存 |
| main／歷史 | `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` 含 #288；merge `3417ab93` 的新增差異只有歷史證據 |
| #314 題 3 | 指定 `3b0b634f` 的 17 完整 blob、23 突變定義及六 suite 103 項已存在於列車。靜態 peer 116 checks exit 0；新 F 動態驗收尚在執行，不冒稱通過 |
| #323 來源／新修正 | 來源產品與測試完整包含；四檔 exact candidate 採用 exit 0，peer 116 checks exit 0；13/22/15 原 suite 及具名 0/1/0 正在執行 |
| #323 ABC／PF3／效能／profile | 新 F 未跑；N32/base≤1、N64/main≤1.3、source calls 64/32≤4.5 不變；舊紅仍未被新量測解除 |
| #318 正典／閱讀器／oracle／掃描／核心 | 保留核可語意；新 F 原正式項與來源撤回證明待跑 |
| native 完整 | 新 F 未跑 |
| canvas／assembly／documents／grid／space／timber | 新 F 六項均未跑；Chrome 156 可用，沒有環境 skip |
| P52／Q38／§7／P-189／四組反證 | 新 F 待跑；不得以先前來源的綠燈填入 |
| 突變帳本 | 歷史帳本未更新。父來源 `3417ab93` 的初始 `--check` exit 1（107 stale、3 retired、13 unrun）；此數字不是 F 的正式結果。須由主代理整份重產 123 筆並在最終來源 check |
| 架構三原裁判及 manifest／scan／report／receipt | 待 Linux 重產與驗證；不等待舊 Windows driver |
| 允許的 skip／已知缺口 | 正式項尚未發生 skip；只接受原裁判具名平台豁免，例如 Linux 的 Windows GDI。#335 兩放置順序限制依既有核可另案處理，不改稱施工成功 |
| 仍紅／未跑 | 上列全部 UNRUN、歷史效能紅、過期帳本仍需處理。沒有 READY-TO-MERGE 宣告 |

逐項進度與封存：`evidence/geo337-train-20261024/PROGRESS.md`、`SOURCE_CHECKPOINT.json`、`source-checkpoint.tar.gz`。封存包含 404 個原件；包 SHA256 `c63223e83118c616994b59b9f9c6f9e658a5adb1ee7efee65edc2c53fb2f50b1`。初始帳本探測只有原 stdout/stderr 及 observed exit，未冒充完整正式環境收據。實際正式項需保留同 F、原命令、環境、exit、完整輸出及 hash。

修正不放寬 golden、斷言、時限或效能門檻；每項修正補撤回／恢復，效能及完整 canvas 獨占，其餘重測最多兩個。任何未核可公理變更只準備，不提交進列車。#325/#331/#333 不在本線範圍。來源修正完成後更新全帳本、架構及受影響 gate，通過獨立對抗審查後再請最新 ChatGPT 審查。
