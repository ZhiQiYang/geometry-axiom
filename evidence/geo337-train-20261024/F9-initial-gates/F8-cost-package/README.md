# #341 F8 fallback 成本實測原件封存

collection exit **0**；只接受檔案保全，沒有新增 performance acceptance，也不解除 whole-341 B1。

完整原 OUT 2,871 regular 檔（546 原 CLI、所有來源與 9 ELF）全部保留；加原工具終態、v2 PINS 與21個釘選來源，tar共2,894 regular members、19,312,640B。逐葉 hash/index 與 tar 回讀均一致。原文件 inode/mode/nlink/owner/size/atime/mtime/ctime 前後完全相同，原件未刪除、未移動、未改寫。

執行器 /tmp/geo341-F8-cost-collection-preparation-20261025/collect.py，原命令/退出碼/完整 stdout/stderr 在同目錄 COLLECT.*。封存後 /tmp 173,797,376B，保留64MiB門檻。獨立 package peer 尚待 cost_tool_adversarial；本包本身不代替原件實績審查。
