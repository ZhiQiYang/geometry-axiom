Manifest 完整性靜態核對未見阻擋：28 leaves／2,679,224 bytes，目的路徑唯一、相對且限指定 evidence 前綴；9 個 workspace 原件 bytes/hash 相符。

archive 的189 raw＋13原工具＋1原host＋3原actual-peer＝206檔，與來源FACTS及既有package peer一致。外層另保留collector/preparer、root CLI、collection host、準備收據與collection actual-peer。兩層host／peer沒有混稱。

只核manifest及現有收據關聯；未讀SHM、未重算archive hash、未解包或重做roundtrip、未重跑產品。expected_parent仍為ROOT_MUST_BIND_AT_PUBLISH，發布時須另綁；published／remote_hash_verified／delivered均false。
