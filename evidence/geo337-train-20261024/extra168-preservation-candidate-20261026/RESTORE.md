# 候選 168 葉逐 byte 保存：恢復界線
本包先供備份審查，不是刪除授權。只含 BYTE_MAP.json 列的 3 個已退役私有 index 與 165 個 GPU cache，33 個 cache 目錄 metadata 供恢復參考；沒有原始 receipts、fixtures、Git objects 或 refs。
恢復前須獨立取得指定路徑寫入授權、確認沒有活躍使用者與未知修改。不可盲目 tar extract 至原絕對路徑；逐一對 BYTE_MAP 的 archive_member 與 original_path，先比對 member SHA256 和完整 bytes，再在新批准操作中恢復。可恢復完整 byte、uid/gid/mode/mtime；inode/ctime 無法還原，後續驗收不得冒用舊身分。
原數據/備份完整性由 SNAPSHOT.tar.xz 全 XZ roundtrip、BYTE_MAP 與逐 member hash 複核。原資料在備份與遠端完整核對成功之前不得刪除；此次計畫未執行備份或刪除。
