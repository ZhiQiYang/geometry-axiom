# #323 Linux 架構四檔

本輪重產實跑來源／帳本保存提交 L：`b7ca7843532098c4d3433035cde8dc2c43654978`。
原三條裁判均真 0：`architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`、`test_architecture_contract.py`、`test_product_architecture.py`。
Linux 重產成功，601 executable files、333 owned sources、268 exclusions、796 edges、0 diagnostics；918 forbidden identifiers／55 forbidden strings。
manifest 原 bytes 未改。全部 input 的 raw／LF hashes、Git blobs、SSOT 與來源前後均核對，四個產物保留真 sourceBaseHead=L，不改寫為產物保存提交。

`linux-architecture-raw.tar.gz` 保存整輪原 argv、退出碼、完整 stdout／stderr、環境、工具、原始與新四檔、來源清單及 hash；每個封包成員已依 inventory 逐 bytes／SHA-256 核同。
下一步：一般推送這四份產物，固定正式驗收 F；等待其他診斷／封存停止重型工作後，依序執行 #323 完整清單與交錯性能量測。
