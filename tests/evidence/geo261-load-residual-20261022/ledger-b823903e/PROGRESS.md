# #323 整份突變帳本重產

產品／測試提交 P：`e9fffc1cb036b6e4538a23f4dd12a9e10c5136f9`。
本輪完整重產實跑來源 S：`b823903e44aea091b70fd2f45b74dff6229776dc`（執行前後 HEAD 相同且乾淨）。

| 原命令 | 真實退出碼 |
|---|---:|
| `python3 tests/mutate.py --check`（重產前） | 1：75 stale |
| `python3 tests/mutate.py`（整份） | 0 |
| `python3 tests/mutate.py --check`（重產後） | 0 |

外層 reaper 的原子程序退出碼也是 0。完整重產始於 2026-10-22 22:51 UTC，於 23:38 UTC 結束。
78 筆紀錄中，75 筆實跑的 `execution.head` 全為上述 S：70 killed、4 equivalent、1 crashed（M20）；另 3 retired。
沒有 survived／invalid／stale／blocked；M20 沒有冒稱斷言 killed。帳本保留原真實執行來源，不改成保存帳本的提交 SHA。

`primary-command-raw.tar.gz` 內的 `inner/` 與 `outer/` 保存原 argv／退出碼／完整 stdin、stdout、stderr、安全環境、SHA、堆疊與工具 bytes。
較大量的實際 mutant 原始碼、bridge build／test raw 正在獨立封存，後續補公開，原雲端檔案仍保留。
下一步：在保存本帳本的新提交上重產 Linux 架構四檔，固定可解析的正式驗收 F，再跑完整 #323 原清單。
