# Generic hint 容量候選與一次靜態 profile

執行來源 1cff9d8c3deab815d5ae6562f3163c95e6f82ac9，父來源 8b128aa7bf53b41b493dd3a0bee49f0d53391254；不含前兩個無顯著收益的 tag 與 W run 候選。每 context 的提示槽由 256 改為 4096，64-bit 額外 30,720 bytes；完整身分、主索引、失敗降級及 reset/seal 維持。這是未採入正式產品的候選。

63 項核心回歸 exit 0；原七個 hint 測試保留，新增固定 512／1024 鍵集、完整 hash collision、全部槽清除及容量撤回具名反證。測試所選鍵只證明結構省工，不冒充真實世界加速。172 場景 plain/trace 共 344 新程序 exit 0，沿用原 B 收據逐 byte／有序 graph 比較。

一次 N256 候選 33.345950932 秒、RSS 110588 KiB、exit 0；對固定既有 8b 34.701295152 秒只約 3.9% 改善。原 placed_geometry 全過、stdout/stderr 逐 byte 相同，未重新抽樣 baseline，不代表 512 或 H7 已過。

為查明未計入動態 gprof 的 libc 成本，僅做一次同來源 N256 static -pg 診斷：每條原 compile 保持 O0，加 -pg；最後 link 加 -static。原 600 秒、16 MiB stack 維持。50.108729515 秒、RSS 111212 KiB、exit 0，來源前後不變、原流相同。profile 與正式時間不可混用；其 source_node、memset、memmove、contact facts 與 face sort 成本供下一修補選擇。所有 flags、libraries hash、ELF、stdin、原流與 gmon 原件保留。

8b 原 H7 1200 秒 timeout 仍成立，正式 F2/C 身分不變。鏈審計三段缺提交只改 evidence；50 葉聯集，固定 8b 已具其中 14 葉，預期淨差 36 葉。尚未實際合流，上游原件與 owner 限制見原報告。完整 ledger／architecture／native／browser 尚未完成。
