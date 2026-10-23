# GEO-300 唯一 ID 遮蓋索引進度

本次產品 SHA：`1ee4e830399b124ebd63c5ff51064d87e53f38d9`。基底為 GEO260 分支 `codex/geo260-ac23-proof-20261024` 的公開 evidence `df230da57619e437c30527dbede8c67fd0ec6b50`（產品 `eb846c345881cc6fc73a53c457a291175365b88c`）。此提交只新增本 evidence prefix，不是另一個產品 SHA。

已完成：唯一 ID 正常路徑的單一見證 Fenwick 遮蓋查詢；全 facts 重複 ID 會保留原 live-set 後備；原收集、排序、容量截斷與輸出穩定序維持。新增原 harness 正反例與 10 刀，原 10 方法 AST 保留，舊 partial-shadow 精確重錨到正常快路並另保 legacy 專刀。依 root 共享棒只登記 wood_contact_world 10→11，其餘 expected 字典逐值全同。

靜審：完整草案 157／0、核心 15 機械＋8 語意觀察／0、新不可變來源與 expected／原 push 167／0。`STATIC_ORIGINALS.tar.gz` 含 203 個原檔與 index，共 204 成員，已逐件回讀 hash；它保存 draft 當時「external-only」原文，不能把該歷史文字當目前 Git 狀態。

來源與登記皆已一般 push、ls-remote 精確同 SHA。初次 git add 因允許清單拒絕 1，原 stderr 保留；核實原 tracked 的精確三 leaf 後使用 `git add --sparse -f` 成功，與 force push 無關。獨立 reviewer 的初始 quotePath checker 錯誤亦保留；其首次 stderr 被覆寫的捕捉限制有明列，不影響產品裁判，因本輪未執行產品。

| 目前項目 | 結果 |
| --- | --- |
| 原三套：11／15／7 方法，共 33 | UNRUN |
| 33／11／12 具名反證，共 56 | UNRUN |
| 額外索引與原 16MiB stack | UNRUN |
| 整條快路撤回 | UNRUN；正例預期等價 0/0/0，不能當 killed |
| 效能／正式 P-189 | UNMEASURED／UNRUN |
| 全 native、browser、全帳本、架構 | 未於此新 SHA 執行 |

原 member insertion sort、重複 ID 後備兩兩掃描、超容量 memmove、cut-list 平方儲存仍在；不宣稱整個 collector O(F log F)。四個 size_t[2432] 僅靜態算資料 77,824 bytes，實際 stack frame 尚未量。

下一步：在 root 釋出磁碟與 secondary 槽位後，以已綁定原三套入口、原 ASSERT／timeout／16MiB 跑完，保存全部紅燈並各刀原 0/1/0。成本／性能另等獨占窗口，不定新的數值門檻，不改 SSOT／決策或全帳本。
