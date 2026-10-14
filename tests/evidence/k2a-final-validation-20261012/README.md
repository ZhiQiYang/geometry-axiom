# K2a-A 最終增量驗證（2026-10-12，臺北時間）

本次回覆 dot 6112071119、ChatGPT 6112366046。保留歷史提案原文，在 PROPOSAL.md:136 加「採納後更正」，連到 SSOT D57／I68／R54；不得純移除曾缺失的引用，明選另一物件替換或整份捨棄才使舊引用離開。沒有改公理、閱讀器或鎖定文件。

本線既有完整非瀏覽器 83 suites：2641 pass／0 fail／1 允許 GDI skip，Node 676/676；五 gates 143 assertions，收據於 k2a-lifecycle-review-20261011/，產品與裁判沒有新增差異。

完整 CDP 已在乾淨 head 54f15179ae220776897c241a044d6311d83e24ad 重跑：84 段、2207 pass、0 fail、0 skip，golden 不變；一個 P38 刻意觸發的瀏覽器例外照實保留。before/after head/tree/status、1719 來源 SHA、fresh runtime/session、原生 bridge PID／實際 /proc/PID/exe／SHA 均核對。新交付只增加證據及以上提案註；產品／裁判來源閉包完全相同，沒有宣稱新證據提交 SHA 自己被執行。

真 K1-b e35c52384519fae77e6067e7a3305f860b9d3a12 與 K2a-A 54f1517 的隔離合併已實做，merge commit 904bebf1e28b27f0cf2f8d4f989a0e79d08befb2，候選最終 head d8ca084c361e36bff64a9e8935dfb51d3ca8320a。候選分支未推送；沒有合併任何 PR；tested-merge.bundle 可重建候選。正式 app 13 assertions：真 UI 保存 cutting settings、原生 cutting 計算 COMPLETE 且 World 不變、兩份網格草稿、共用 /17 與兩種能力、真 ZIP 在另一原生 session 冷開，raw／設定／完整 dump 相同。沒有用固定 validator 代替這次真合併。候選完整非瀏覽器 88 suites：2695 pass／0 fail／1 允許 GDI skip，Node 676/676；結果見 nonbrowser.log；OS picker 仍採記憶體 writable handle。

合併樹第一次完整執行確實失敗：HTTP workbench 拒 K1 原生合法 terminal leaf，保留原始失敗 log。候選只修有限 terminal schema（literal/spec/parameter/material，型別／欄位／版本／fingerprint 嚴格拒），production 9 changed lines＋既有登記測試 11 added lines＝20 行；20 項 HTTP 測試通過。測試先驗原生 receipt roundtrip 紅，再修正。兩個格式／dispatch 與三個 terminal 指定突變各 baseline/build/指定 assertion 紅/restored 綠，共 5；HTTP 外層完整 receipt guard 會遮蔽部分壞 terminal，故新測試也直接驗有限 schema，不把被其他 guard 拒絕算殺突變。

K1 upstream 改 engineering.inc，故隔離合併樹重跑原始 tests/mutate.py，自動產生 48 筆 ledger：40 killed、1 crashed、4 equivalent、3 retired、0 stale、0 survived。執行 head 904bebf1，後續 adapter/test/doc/expected 不改核心 producer／原生 oracle。K2a-A 本身 current_geometry.c 與核心 ledger 均未改，mutate 無新覆蓋；既有 41 指定反例仍為先前重跑 39＋producer/judge 未變而沿用 2，不灌入這次候選的 5。

未驗／阻擋仍保留：正式本機 WSL exact-head 七組、包含尚未合併 #199 的最終整合樹、候選整套 CDP、其他具名 browser owners、雲端 CI、OS 原生檔案選擇器。沒有執行 WSL；Linux 非瀏覽器／CDP／13 項共存不能替代正式七組。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。PR 繼續 draft，不宣稱可合併。

| 驗收 | 本線 Linux 結果 | 理由 |
|---|---|---|
| M01 | 過 | 多份並存，無取代對話框 |
| M02 | 過 | 真 ZIP 冷開 raw 逐字、能力保留 |
| M03 | 過 | 同 draftId 續開 |
| M04 | 過 | confirm 清本份，一步 Undo 還原 |
| M05 | 過 | 舊 pin 拒預覽、明選重取 |
| M06 | 過 | 原生刪除／Undo／Redo、掃描同步 |
| M07 | 過 | 非孤兒同目標整份拒 |
| M08 | 過 | 第 17 份拒、不截斷 |
| M09 | 過 | 草稿引用拒 |
| M10 | 過 | 三格式分派、容量 promotion |
| M11 | 過 | format/schema/capability/orphans/lost 負例 |
| M12 | 過 | 舊 flush/API、抹 lost、純移除及空來源拒 |
| M13 | 過 | 1280/390 真 Chromium、44px、無溢出 |
| M14 | 過 | 同 ID 同內容不復活 |
| M14b | 過 | lost 冷開保留、同 ID 重取拒 |
| M15 | 過 | 兩方比較、取消不變、完整 raw |

既有本線完整非瀏覽器 83 suites／2641 pass／0 fail／1 允許 GDI skip、Node 676，五 gates 143；原始收據保留於前一生命週期目錄。新 inventory 列本次原始／儲存 SHA；舊目錄不改。bundle 以前提提交 54f15179ae220776897c241a044d6311d83e24ad 與 e35c52384519fae77e6067e7a3305f860b9d3a12 為 prerequisites；在另行 clone/fetch 這兩個提交後，可 git bundle verify integration/tested-merge.bundle，再 git fetch 該 bundle HEAD 到本機審查分支。候選完整非瀏覽器不是正式 WSL 裁判；執行途中提案註記和直接 schema 斷言有提交，直接斷言在 HTTP suite 載入前已固定，HTTP 原始 log 證實 20/20。UI 收據另外在最終乾淨候選 head 核對 before/after。GEO-219：無新入口。K2a-B 疊本分支；PF／B 依看板暫停。
