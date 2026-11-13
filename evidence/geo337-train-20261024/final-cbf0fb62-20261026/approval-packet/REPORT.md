# 3156 個既有暫存檔案：待批准範圍

自動審核已拒絕這次回收。本文件只供確認具體範圍；沒有重試、拆批、改路徑、刪檔或回收空間。固定證據提交：`9a57aea2128a7bc3985064932c24e2229fd8fcb8`。

| 類別 | 檔數 | logical bytes | 記錄 allocated bytes | 固定完整清單 |
|---|---:|---:|---:|---|
| Git可還原的舊臨時原始碼／靜態副本 | 2439 | 61,260,421 | 68,423,680 | [manifest](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/original-prerequisites/0000.bin) |
| 舊P52 Chrome白名單cache | 691 | 15,179,307 | 10,350,592 | [manifest](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/original-prerequisites/0010.bin) |
| 兩個已封存的舊私有Git index | 2 | 9,209,691 | 9,216,000 | [manifest](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/original-prerequisites/0009.bin) |
| 四個pre-*cache中的舊編譯ELF | 24 | 19,200,272 | 19,243,008 | [manifest](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/original-prerequisites/0008.bin) |
| 合計 | **3156** | **104,849,691** | **107,233,280** | source 只含 `retained_rows`，Chrome 只含各組 `files` |

**原工具另會移除 108 個空目錄**：Chrome 清單內63個子目錄及45個白名單cache根目錄。只用 `rmdir`，需身份相符且已空；不刪profile根目錄。批准須明載此附帶範圍；未計其容量，不能默認包含。

歸屬依原任務固定checkout/Git blob、歷史退役與P52/P73終態、四個cache隔離及ELF fingerprint/owner原件；不是憑uid。沒有逐檔系統創建者audit，不能給「每一檔絕對由我建立」保證。原2439副本byte-validation與狀態收據支援可重建性；26 index/ELF有完整原件備份。這些是歷史證據，並非現在或將來沒有活躍writer的保證。任何owner或終態仍不明、使用者修改、未知alias、dirty drift或活躍命中都必須排除／拒絕；此包沒有替3156項重新取得fresh資格。

**保全狀態**：固定E9已普通push，606個唯一blob全bytes/hash/GitOID核對；26 raw＋26 gzip均有精確對應。獨立publication審查64,041項、exit0。source依保留Git blobs還原；Chrome cache依可重建性，沒有冒稱這兩類都有逐檔raw備份。

- [原PLAN](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/PLAN.json)
- [完整26payload保全結果](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-package/RESULT.json)
- [owner FACTS](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/original-owner-receipts/FACTS.json)
- [11份owner原收據＋24份fingerprint索引](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/native-TMP-preservation-recovered-20261026/resume-actual-peer/OWNER_ORIGINALS.json)

遠端實核原件在 `/dev/shm/geometry-axiom-geo337-20261025/recovery-publication-original-20261026/{RESULT.json,REMOTE_BLOBS.json}`；獨審在 `/tmp/geo337-recovery-publication-actual-peer-20261026/REVIEW.json`。這些回條在E9 push之後產生，不捏造E9內的對應連結；完整hash與52項對應見 `SCOPE.json`。

**排除**：原73個模糊來源（14個browser check＋59其他）、F9六個ELF、F8/R8/P-189及當前正式來源／快取／index、全部原始收據/raw/fixtures/Git objects與使用者修改；另165個GPU快取不屬本次3156項。

107,233,280B是原清單記錄的檔案毛allocated總量，不是已回收量；目前本次回收仍為0。批准後仍需root fresh consumer／狀態／hash／租約與原容量守門，不能據此宣告native128MiB已准入。
