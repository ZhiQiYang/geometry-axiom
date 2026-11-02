Product SHA：`bfbab207a92a809fca50fefcefb3fa4b2af05ea9`。

2026-10-23 雲端正式原入口已完成：外層 exit 0、原 driver exit 0，baseline 真 `Ran 13 tests`、零 skip；七階段原退出碼依序 `0/1/0/1/0/1/0`。三組正常撤回分別證實 woodworking import、K 引入 quoted/angle 模板 header 的層界守門、angle include parser。原核心格網整除反證另保 `0/1/0`。

原 11 個 Git inputs 逐檔綁定 Product SHA；77 個各階段來源、精確單 site 變異與還原全部保留。quoted 與 angle header 均真存在並先成功編譯執行，才由原層界裁判拒絕。負控以原具名 AssertionError 正常轉紅，沒有變更斷言、產品或 driver。

原排程鎖因第 1 槽帳本仍在執行，經 root 明確授權，僅把既有 `--heavy-lock` 參數改為第 2 槽 `/tmp/g261r3/secondary.lock`；原 EX|NB、忙鎖出口與全部時限保留。第 2 槽已在原 driver 終態釋放，交給 #324。

獨立 actual peer：530 checks、exit 0，報告 SHA256 `68fbc441248d9bb5acc906c7b682f6f95b8b4143d5b1174c69c035acca633f85`。完整原件與 peer 收於 `nowood-original-bfbab207.tar.gz`，逐檔清單為 `MEMBER_HASHES.json`。

封存包括原 c387 Python stdout/stderr 位元組、完整環境/SHA/退出碼與 65 筆編譯/連結文字輸出、121 筆原 native 記錄。原編譯器使用 text capture；未另存其 raw pipe，原暫存 C/ELF 依既有 cleanup 清除，沒有事後重建作原件。各 phase 的來源、變異與文字紀錄保留。

這份結果只適用本分支的固定 Product SHA。尚未採入列車的產品/測試 closure，不能借用列車帳本或宣稱專案全綠；全專案列車驗收、最終整合帳本與合併仍由 root 後續處理。本分支未重產帳本、未 merge PR、未 force push。下一步為一般推送證據與正文，供 root 普通合流並依新 closure 驗證。
