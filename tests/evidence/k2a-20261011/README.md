# K2a-A Linux 驗收收據

依據：GEO-252／決策 K #45，`geometry-core/drafts-topology/PROPOSAL.md` §A6，D56、D57、I68、R54；PR #199 的澄清 diff 已讀。此目錄不代表 WSL 裁判，也不代表雲端 CI。

| 驗收 | 本機結果與裁判 |
| --- | --- |
| M01 | 通過：真 Chromium／真 ZIP 兩份並存，無取代對話框；replacement-dialog 突變紅。 |
| M02 | 通過：真 ZIP、另一個全新服務與瀏覽器重開，raw 逐字一致及能力保存；first-only 突變紅。 |
| M03 | 通過：真 Chromium 續開原 draftId；fresh-continuation-id 突變紅。 |
| M04 | 通過：原生配置確認只清除該 draftId，一步 undo 還原配置與集合；clear-all 突變紅。 |
| M05 | 通過：原生來源變更使舊 pin 過期，明選後列新舊才重取；auto-rebase 突變紅。 |
| M06 | 通過：原生刪除同步孤兒、undo 回有效；no-scan 突變紅。 |
| M07 | 通過：集合及 ZIP validator 拒重複目標；duplicate-target 突變紅。 |
| M08 | 通過：第 17 份整筆拒；容量突變紅。 |
| M09 | 通過：草稿引用被拒；allow-draft-ref 突變紅。 |
| M10 | 通過：單份／孤兒集合／lost 集合分派，明選不同來源後可降回單份；orphan-to-single 突變紅。 |
| M11 | 通過：降版、剝能力、schema、orphans、各種非法 lost 均拒；validator／降版突變紅。 |
| M12 | 通過：舊 flush、舊介面、抹 lost 不生效且不改 history；對應突變紅。 |
| M13 | 通過：真 Chromium 1280／390px，44px 可達，無橫向溢出與未預期例外。 |
| M14 | 通過：原生刪除後同 id、同內容不復活孤兒；revive-orphan 突變紅。 |
| M14b | 通過：原生來源及參數卡缺失回執；同 id 重建拒重取；真 ZIP 冷重開保留 lost；不同來源明選確認；相關 lost／回執／無原生變更的 history 突變紅。 |
| M15 | 通過：真 UI 兩方比較，int／signed 正規化；取消不變，接受只 repin、不提交 World；literal-comparison／unreviewed-repin／cancel-updates-pin 突變紅。 |

瀏覽器測試使用真應用、原生 bridge 及 ZIP；另以可寫記憶體 handle 收集 OS 保存選擇器的結果，未宣稱驗 OS 選擇器。競態與突變測試有明確注入。四個獨立 Chromium gates 已登記在 run_all 的必要另驗名單；aggregate 不將其算成通過。

`current_geometry.c` 未改，因此原有 `tests/mutate.py` **mutate 無新覆蓋**，`tests/mutants_results.json` 未手改。額外裁判為 JS 隔離突變 20 個、Chromium 路由突變 3 個、原生 bridge 回執突變 2 個；各自先驗未修改基準通過，突變必須以斷言失敗而非環境錯誤判紅，還原透過隔離副本完成。

未驗：正式本機 WSL 裁判、雲端 CI、作業系統保存選擇器。非瀏覽器 aggregate 的其他既有 browser owners 依其具名另驗名單，不冒充本次新增覆蓋。

GEO-219：無新常駐工具列入口。沿用網格建立／編輯入口；移除取代舊草稿對話框與開啟時清除草稿的分支；來源下拉取代靜態來源文字，重新取得基底只在過期時出現。
