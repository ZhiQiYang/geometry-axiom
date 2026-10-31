# #314 F9 局部反證完整原件

來源固定為 `4f8a794f4167c3562eb182045102e86e9e37cca9`。本批只封存既有 v2 失敗與 v3 成功原件，未重跑產品，也不把收件成功當作完整 native 通過。

- v2 原 exit 1：局部修正／撤回／恢復反證成立，但原 ROOT index bytes/inode/metadata 保全裁判失敗；`INDEX_AFTER_FAILURE.bin` 與所有原流完整保留，不推定歷史寫入者。
- v3 原 exit 0：從第一條 Git 指令使用獨立 index／objects；完整 11 項 fixed/withdrawn/restored 與四個 K 負例恢復原件保留，獨審 349 項通過。`formal_F9_pass` 仍為 false，原 F9 native exit 1 不移標。
- 三個 gzip 完整收納 1,826 份 regular 原件、36,200,174 bytes；壓縮共 7,918,998 bytes。包含兩個完整 raw root、1,357 固定補件、private Git objects/index、原命令／環境／輸出與原工具。沒有 hash-only 排除或 socket 遺漏。
- 包獨審 14,194 項通過：逐原件 hash/stat、完整成員 bytes/type/mode/mtime、gzip EOF/CRC、來源前後及完整葉集合均核。原語意裁判沿用原獨立 349 項審查，不另抽產品樣本。

本清單只追加本目錄，沒有 PROGRESS、PR 正文、產品採用或正式 gate 變更。可隨較新證據 head 發布，全部原件仍標 F9。雲端 SHM 為暫存；只有後續正常 push 與遠端完整 blob 核對成功才算交付。所有原 payload 留原地，不刪除。
