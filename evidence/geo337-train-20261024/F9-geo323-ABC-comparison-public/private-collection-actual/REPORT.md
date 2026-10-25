SHM 五包 actual 收件核對通過：32,744 項／0 錯誤。所有 SHM 存取均使用正式 require_escalated exec 並經 auto_review；沒有用普通 sandbox 或 symlink 繞過。報告僅寫入 workspace，沒有更改 SHM 或來源、沒有解包到磁碟、沒有重收或重跑產品。

原 host、root launcher 與 collector 終態均為0；原 CLI 的 request/result、完整 stdout/stderr、hash、環境及實際執行腳本／root request／peer pins均符合。原 stdout 同時保存五個 budget、五個 complete 及最終 result，與各檔一致。

逐包讀完整 gzip stream 驗 CRC/trailer，再逐一核全部 tar members 的順序、type、mode、mtime、完整 bytes/hash，不解包寫檔。4,663 regular files＋4個literal ELF symlink＝4,667 members，全體恰一次。regular bytes為19,845,851；五個archive合計2,758,452 bytes。原comparison的4,645 regular與4個symlink完整在內，額外18檔是已固定的身份／審查原件。每個原來源的lstat與完整regular hash／literal symlink target亦重新唯讀核對，全部不變；沒有dereference或複製ELF。

每包原fresh free都滿足完整tar/gzip最壞上界＋64MiB reserve＋2MiB metadata，實際archive均低於上界，原每包完成後都保留64MiB。metadata upper為1,186,343 bytes，低於2MiB；原最後free為17,867,935,744 bytes。所有free皆取實際SHM輸出device，沒有使用WS/TMP空間代替。

| 包 | archive bytes | SHA256 |
|---|---:|---|
| 1 | 1503146 | `5b7163e98eb6332f1cf41fdefe98e176415bce68dc4157547a200ee332cdf7fa` |
| 2 | 245546 | `e3ec07cb0d84e291929db1dc5915ca4c81cd17e4c6517465a2113036b31ba630` |
| 3 | 229384 | `9e199cd1c73ecbcc0447d0d4d8f67b7fa0ad13d994d32c6ffda687a85df640de` |
| 4 | 468244 | `e1e01993677fb8248dccaea359f19bec727a8bca4282d72766af4da07d0328c4` |
| 5 | 312132 | `3dbf2a5e558339521893c445abe6b08407e1ffec25fa1a7c61065cafa072096d` |

F9來源為4f8a794f4167c3562eb182045102e86e9e37cca9；原R8 outer仍為1，性能未重跑。這是收件與完整roundtrip驗證，沒有重判整條列車或P-189。

**仍未交付：** storage_is_volatile=true、published=false、remote_hash_verified=false、delivered=false。必須由主代理完成正常push並核遠端hash後，才可變更出版／交付狀態。此報告不以volatile SHM存放取代持久證據。
