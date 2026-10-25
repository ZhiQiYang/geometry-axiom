# F9 assembly 兩次完整原件

固定產品 SHA `4f8a794f4167c3562eb182045102e86e9e37cca9`。首次環境失敗 exit 1；第二次只縮短 fresh storage 路徑後，原 workflow／launcher／sampler／host 全 exit 0，150 assertions、零 fail／skip。兩次各守原 15 分鐘時限（85.372989／188.843305 秒）；首次尚未執行產品 assertions，不能改稱測試通過。

`package/INVENTORY.json` 逐一列出三個 `ORIGINAL_ASSEMBLY_PART*.tar.gz` 中的原始 argv、exit、完整 stdout／stderr、環境、SHA 與每一檔案 hash/stat。三包保留 828 regular files／35,366,094 B，加 5 symlink targets，gzip 合計 8,121,472 B。未省略 ELF、profile、cache、screens、diagnostic 或預期負例。5 個 sourceplan Git metadata／mutable latest 只記 hash；1 個 Unix socket 只記 metadata，原件未刪除；seed/source payload 不複製。

`collection-original/` 保存真正 c387 收件命令與全流；`collection-EXEC_FINAL.json` 是主機真 exit 0。`package-actual-peer/` 的獨審 6741／0 包含每 member bytes、type、link、mode、mtime；`r2-actual-peer/` 保留第二次產品裁判獨審。這些收件／審查出口不改首次產品 exit 1，也不代其他正式項。

本批只增加此 evidence prefix 並更新唯一 current-state PROGRESS；native 仍 exit 1，其餘未完成項維持。封包原 RESULT 的 delivered=false 是當時尚未出版的事實，保留原 bytes。正常 push 後仍須 GitHub API 下載每個公開 blob 核對完整 bytes／SHA256／Git OID，真驗證收據另列；不能以 ls-remote 或本 README 代替。
