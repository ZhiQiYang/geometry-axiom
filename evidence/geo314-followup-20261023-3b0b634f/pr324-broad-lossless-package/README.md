# 原始命令串流的無損分塊

這是既有原始輸出的封存表示，不是重新執行命令。原件保留。每塊依 MANIFEST 的 offset 排序；所有解壓 bytes 串接後已與原命令收據逐位元組雜湊核對。

還原（在本目錄，指定一個不存在的新輸出檔）：

```sh
gzip -dc stdout.part-0000.gz stdout.part-0001.gz > restored-stdout.bin
sha256sum restored-stdout.bin
```

預期 bytes：89526252；SHA-256：`b9cb7b4df2a509878c3483b54fadba14263c39192ae29c8bae2a69463a54872f`。
