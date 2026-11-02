# #344 F 官方遠端 CI bytes 核收通過

Source F `d794a7447b98a82fb35c1dccaedc3443e2230933`；Integration
`41393748904`、Mutation `41393748942` 都是 pull_request／attempt 1，正式
success，合計 20 jobs。真 integration checkout
`4ad5a0a831073334c8f125d76ea366af3c325f34` 與 F 同 tree
`51b669da21513fbccf90620faf55b7aad77703b6`；原事件 parents 為 main
`5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` 加 F。

21 份官方 ZIP 的實際 SHA256 全等 API digest，安全解壓與成員雜湊已保留。
20 份直接 job log 與兩個官方 run ZIP 的整 job log 逐 byte 相同。原 native
聚合工具 exit 0、輸出逐 byte 等官方 summary：231 suites、77/77/77，
5349 counted＝5348 pass＋1 指定 Windows GDI skip，0 counted fail；官方
registry 負控制為真 0/1/0，沒有在本地重跑負控制。

六組 browser 原 raw／fresh runtime／實際 child exit 均通過：grid 356、space
242、canvas 2267、documents 47、timber 79、assembly 150，皆 0 fail。Canvas
是 full、空 filters/modifiers，85 段逐段等目前 source golden。

原 Mutation verifier 在固定 F source、fresh output 目錄 actual exit 0；輸出
ledger／summary 逐 byte 等官方聚合。123 定義／120 active＝114 killed、
1 crashed、5 equivalent、3 retired，其餘 0。原 binary／sidecar／source／tool／
closure 已核，七組官方 strict controls 真 0/1/0，159 bridge raw 結果吻合。
架構原三條 CLI 收據 exit 0；604-input closure、798 edges、0 diagnostics
及原 stdout／stderr／來源 SHA 均相符。原命令、cwd、退出碼及所有 stream hashes
見 `receipt.json`。

- 新 F artifact ledger SHA256：
  `4b02cae010f9b629ef55372468146e82bfbc73026cf21ab79ae9fe7897c263f8`。
- 新 F artifact summary SHA256：
  `38dd9b26e53eb6735b4e86f17c89e59b611506b5c293123a38641ede1996d50c`。
- Source 帳本仍為先前採入的 E503 execution 原 bytes，SHA256：
  `aaaad44b2470d5f5d937a8ba8f431dd554f0ee95a82958f9ff48b19aa86a5ee8`。
  新 F artifact 另存，沒有再次採入 source。E503 舊兩個 stale 紅燈與原件保留。

本輪依 root 明示 phase gap，以一個 artifact worker 完成純 bytes／原收據驗證；
下載的 ELF 沒有執行，沒有跑產品、Chrome、build、native suite、新 CI，沒有
修改 source／PR body／base。獨立輕量 peer 的 1750 項 raw／JSON／source 核對
通過，沒有重做大 ZIP／binary hashing。原 raw 全留在此小型公開子集之外。

此收據只接受官方遠端 F CI。Root／owner 另回報本地 fixed full 在 06:14:08
因 P76 private TMPDIR 的 geometry-tests parent ENOENT，actual exit 1、1827/0；
本輪未重核該 local 原件，遠端成功不涵蓋或覆寫它。
