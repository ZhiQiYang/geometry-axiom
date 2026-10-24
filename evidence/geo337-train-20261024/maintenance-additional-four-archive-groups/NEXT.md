# 儲存維護接續：四組追加 archive

四組歷史 archive 已完成保路徑硬連結去重：28 個原路徑及完整內容保留，24 次替換、25 次 consumer 守門，182 個原 Git 命令及外層退出碼均為 0。配置區塊總減量為 300,097,536 B；原 free-space 觀測為 48,926,720 → 345,350,144 B，兩者意義不同。這是儲存維護，不能把舊或新產品驗收的紅燈改判為綠。

完整原件包 359,949 B／1,597 members，封包獨審 6417／0；含初次 prefix 不含 tests/evidence 而退出 1 的原工具、partial captures 及明標的 direct-exec transcript，沒有回填獨立 OS 錄製。r2 準備僅補精確 archive 所在的 prefix，未修改產品、測試或斷言。所有 28 個 archive body 都留在原位置，未另複製入 metadata 包。

新增禁寫範圍在 FOUR_ADDITIONAL_IMMUTABLE_ALIAS_REGISTRY_20261024.json 的 4 groups／28 exact paths。七個已退休 owner 是 g261r2 的 codex-geo261-fe863b03/repo、q38/repo；g261a1 的 codex-geo261-a12d184e/repo、q38/repo；g261r1 的 codex-geo261-f2c8837a/repo、q38/repo、source-final。不可借為可寫測試 checkout，也不可直接 reset／checkout／clean；所有適用的 alias 須依另審計畫完整解除共用後才能再寫。

先前 423 cold receipt groups、2 cardref ELF groups、1 GEO339 六 alias group、3 大 archive groups 的禁寫規則仍有效。這份新 registry 不取代它們。

105 個普通來源副本退休工具僅完成 metadata 與靜態審查，prepare／execute 都未執行；root 已暫停，不能誤稱另回收 52 MiB。另餘 12 archive 群僅有 metadata 候選，未證 fresh body／Git 相同、未授 link，若將來需要空間再走完整守門與獨立審查。

本段不聲稱特定 publication SHA；實際 evidence commit／push 結果由 root 的批次出版收據與 PROGRESS 記錄。
