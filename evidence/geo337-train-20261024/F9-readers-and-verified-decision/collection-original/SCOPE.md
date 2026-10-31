# F9 閱讀器與 API 身分證據兩包收件

本工具只封存既定 582 份原件，沒有重新執行產品／閱讀器、修改來源、推送或採用新裁判。最大原 source-read stdout 單獨 part1，其餘 581 份置於 part2。兩包合計代表 11,063,364 bytes 原件。

每包開始前以新鮮 WS 餘額判斷：完整未壓縮體積＋每成員 4096 bytes header/padding 上界＋10240 bytes tar 尾端對齊＋保守 gzip 最壞膨脹＋1 MiB metadata＋64 MiB reserve；沒有假定壓縮率。compresslevel=1；每個 tar 成員全部 bytes 回讀 SHA256，來源前／中／後 stat 與 SHA256 完全相同，582 目的地恰各一次。

原完整指令／stdout／stderr／環境與 exit 保存在本目錄 subcommands，collector 與原 c387／launcher 原件亦保留。真正 executor exit0 另存 `/workspace/geo337-F9-readers-and-identity-two-part-EXEC_FINAL-20261025.json`。collector v1 原稿未執行、未覆寫。

collection0 不是 native0。原閱讀器三項0／51 tests、原 native1、原 R8 exit1均依各原件保留；API 來源只用已核可公開 subset，完整 user profile 沒有進入固定 manifest。獨立 package peer 另外出具，不在本工具自稱已通過。
