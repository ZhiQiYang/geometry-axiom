# GEO-300 唯一 ID 遮蓋索引進度

產品 SHA 固定 `1ee4e830399b124ebd63c5ff51064d87e53f38d9`，沒有在測試中修改或合入來源。基底 GEO260 公開 E `df230da57619e437c30527dbede8c67fd0ec6b50`／產品 `eb846c345881cc6fc73a53c457a291175365b88c`。本 evidence 提交只改此 prefix。

原三套已於 2026-10-23 21:55:09.059797～21:55:31.974441 UTC 真實執行。它是原裁判的部分 native 範圍，不是性能量測或完整 native。

| 目前項目 | 結果 |
| --- | --- |
| wood-contact-world | exit 0；11 方法／33 具名反證原 0/1/0；0 skip；131 compile/link 全 0 |
| contact-sources | exit 0；15 方法／11 反證原 0/1/0；0 skip；85 compile/link 全 0 |
| Reading A native | exit 0；7 方法／12 反證（11 W＋1 H）原 0/1/0；0 skip；86 compile/link 全 0 |
| 合計 | 33 方法／56 反證／302 builds；driver、reaper、launcher、host tool 皆 0；source HEAD/tree/clean 全保 |
| 獨立 actual peer | 1140 checks／0 findings；完整 356 raw／20,889,604 bytes 逐 hash 核對 |
| 既定 16MiB | 上述原三套皆在原 limit 下通過；compiler frame 大小與完整場景上限尚未另測 |
| 整條快路撤回 | UNRUN；規劃原 7 正例等價 0/0/0，不冒 killed 或完整 11 方法 suite |
| 效能、正式 P-189、容量512 | UNMEASURED／UNRUN／未實作未驗 |
| 完整 native、browser、全帳本、架構 | 此新 SHA 尚未執行；NOT READY |

新原件包 THREE_SUITES_ORIGINALS_AND_PEER.tar.gz 保存 356 raw、實際使用的共用工具、準備審查與 actual peer，共 366 成員已逐件回讀。壓縮原件放 /tmp；Git blob 直接入庫，沒有再物化一份 archive。舊 STATIC_ORIGINALS 與其靜審仍完整保留。

只因可用空間，原受審 runner 的 out／TMPDIR／bound-observer／reaper-log 放 /tmp，原 100MiB 門檻也查實際 /tmp，沒有降低門檻。原三套入口、16MiB、child timeouts、ASSERT、compile flags 與 secondary lock 不變；沒有新 checkout。21:55:31 後已釋放 secondary，沒有繼續跑 C、Chrome 或性能。

限制：NativeBuild 原 logs／native events 保存完整解碼文字，不宣稱解碼前 OS bytes。最外 host tool exit0 依 API 原回覆，沒有獨立 host OS capture；reaper／driver／三套原 streams 均有 c387 收據。reviewer 兩個初始 metadata probe 錯誤與修正保留於 peer 原件，沒有 subject 重跑。

原 member insertion sort、重複 ID 後備配對、超容量 memmove、cut-list 平方儲存與 call-growth 仍在。原 #341／Sc493 的 32／46／282 沒有移標；本輪新 S 的 302 是原 logs 的 131＋85＋86。

下一步：先完成公開封包／正文獨立核對，之後待 root 排程做仍未跑項。性能與容量512未完成，不標 READY，不改 SSOT／決策，不由子代理重產全帳本。
