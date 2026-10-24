已排序的成員接觸面原本仍進入完整合併排序，增加 `contact_order` 查詢。此修改在原索引初始化後先以完整 `uint64_t` 順序單次掃描；順序正確就保留原穩定次序，出現逆序時仍執行原合併排序，後續面索引完整初始化不變。

這是 #338／#343 的效能前置修正；主代理將普通合入列車。沒有新 wall-time 門檻，也尚未宣稱解掉 N64/main 紅燈。

| Current state | 固定值／結果 |
|---|---|
| Product / actual execution SHA | `aa16e73d6e1f2965e0a911581e2a545aaaf66870` |
| Ordinary parent | `ca7838e0f4950452b9befcf40899d606db9b81fa` |
| Evidence head | `39eaf977d76204f1506830e63beeaa645cfa6431` |
| wood-contact | 退出 0；13/13；零 skip |
| contact-sources | 退出 0；15/15；零 skip |
| reading-A native | 退出 0；7/7；零 skip |
| 編譯／連結 | 332 次，全部退出 0 |
| 完整優化撤回／恢復 | 原生退出 0/1/0；實測排序查詢 128/896/128；精確 `ASSERT:monotonic-linear-order-lookups` |
| 四個細部控制 | 各正常 0/1/0；最後逆序、漏最後面、完整 uint64、previous 更新的精確具名斷言 |
| 語意不變旁證 | 十組獨立序列 × fixed/withdrawn/restored，30 次全部退出 0 |
| 外層／driver／source | 原退出全 0；214 來源檔與 HEAD 完整比對、clean；雙 observer complete |
| 允許 skip | 無 |
| Full native / 六個 browser | 此來源尚未跑，待最終整合驗收 |
| 突變帳本／架構收據 | 待主代理在最終整合來源統一重產／驗收 |
| O2 效能／#341 四類成本 | 此來源未跑；不能由功能方法或靜態模型冒充 |
| 整體可合併狀態 | 尚未 READY-TO-MERGE |

保留原 12 個方法、所有舊控制與 golden／時限，新增一個方法；registry 只同步此 suite 的 12→13。工作量案例用 64 個合法成員事實供應 128 個面，加兩個 RC 前綴，不使用超容量 World。四個細部反證的紅燈分別是 `monotonic-last-inversion-full-fields`（兩項）、`monotonic-full-uint64-fields`、`monotonic-middle-inversion-full-fields`；都來自真正編譯後程序的正常 assertion 退出 1。

完整原件在 `evidence/geo343-monotonic-aa16e73d/`。`RAW_INDEX.json` 綁 4533 個 member 與原路徑／SHA256，完整 gzip SHA256 為 `b6ddba01b0e15b7aa17cef1239508ed438da997c9650a132c596a44e0f0e1abe`。保留所有原命令、退出碼、環境、stdout/stderr、編譯輸入與七個實際 included-TU 變體。原 text-mode 編譯／原生輸出依原 decoded-text 表示法封存；Bridge 原始位元組另有明確標記，原 NativeBuild cleanup 沒有改動。

歷史：U 的原 N64/main 為 `1.429347781620555 > 1.3`，仍紅；新來源需要原效能裁判重測。source 出版 R1 的 ignored-parent `git add` 退出 1 全文保留，當時四個正確檔案已暫存而尚未提交／推送；R2 精確核對後普通提交／推送，439 個 Git 指令全部退出 0。沒有 force push、合併 PR 或公理／決策變更。
