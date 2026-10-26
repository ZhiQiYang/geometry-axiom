【使用者裁決】Q-323-ABC 與 B3 的答案已寫入決策佇列(#349,合併提交 `405f8c5e`)

使用者 2026-10-25 選擇(選項原文):

> 讓 Codex 繼續做到審查通過

> A 接受這 3 筆 (Recommended)

> 延伸到所有 PR (Recommended)

> 先合併，帳本留下次 (Recommended)

對本 PR 的意思(本機 Claude 整理，非原話;全文見 `決策佇列.md`「2026-10-25 #338 列車」一節):
- **B2(#323 跨版本逐字比對)**:只放行 `_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene` 三個場景錯誤輸出中多出的那一段 #299 定位邊文字(決策佇列逐字列出);比較器實作成精確白名單，其餘 bytes／返回碼／有序圖／五 guards 仍須相同，多一筆或文字不同仍紅。效能門檻不在此裁決內，仍照原門檻。
- **B3(required CI)**:Actions 帳單停用期間，同一最終 SHA 上 7 項加專項全綠並保存指令、退出碼、完整輸出、環境與 SHA,即可代替 required CI;本機 WSL 或雲端 Codex 皆可。適用之後所有 PR。
- **突變帳本**:合併時若唯一紅燈是 `mutation:check` 因來源變動回報 stale,可以合併，說明寫明過期筆數，下一輪第一件事重產全帳本;survived／invalid／blocked 仍擋。
- 本機 Claude 不自行收尾合併，由 Codex 修到審查判可合併後再處理。

另:本機試併時發現 #344 改了 `geometry-web/cdp_test.js` 卻沒更新 `product-architecture.json` 的排除項 LF 雜湊(應為 `1f3e2e36283ed7bb…`),合入列車後架構裁判報 `EXCLUSION_DIGEST`。詳見 #344 留言。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
