# GEO-300 排序與跨 suite 反證錨點進度

目前 S `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`，產品 bytes／expected 與 `cc2ea1b3b42291f6ebb0ead6bd1c2180920d7041` 完全相同，只有 contact-sources placement-order tuple 從舊 insertion break 移到正常 comparator。原 case／具名 ASSERT／15 methods／11 controls／timeout不變；單leaf靜審15／0。

| 目前 S 的項目 | 結果 |
| --- | --- |
| 原三套34 methods／64 controls | UNRUN，等待root原100MiB／secondary槽授權 |
| tuple回撤／恢復 | UNRUN；另用原受影響一方法／8控制 fixed0→舊tuple紅1→restore0，不能冒完整15方法或全部11控制 |
| 16MiB／效能／512／完整native/browser/ledger/arch | 新S未跑／UNMEASURED／NOT READY |

前輪 Scc2 三套已22:47:26.381006～22:47:48.756991 UTC真終態：wood12/41 exit0，contact-sources15 exit1，ReadingA7/12 exit0；147＋85＋86＝318 builds全0，三套0skip，outer／primary／reaper／launcher全1，source HEAD/tree clean。唯一紅為舊placement-order反證還撤已被快路旁路的fallback，原native輸出 PASS ordering／exit0，故原meta-test正常失敗1；不是compile／crash／環境紅。原正常排序行為測項通過。

本批公開完整紅stderr、原inner/top receipts與單leaf patch／manifest／peer／正常push證據。其餘完整原streams／compiled C／logs仍原路徑保全，完整壓縮封包與actual/public peer待後續真正測試批次一併收，不宣稱已公開全raw。沒有覆寫本輪1。

歷史S1ee的33/56/302全0仍只屬原SHA；舊靜態172成員包與原實際366成員包全保。新S不繼承整體綠燈。正常unique bounded排序只改善該排序，duplicate/overflow平方後備、cut-list及call-growth仍在；無新容量／性能門檻。下一步修復後原三套一次重跑，另外留明確tuple撤回原meta紅／恢復綠證據，仍不改產品、公理、決策或全帳本。

出版的 git diff --check 原exit2：只有完整原stderr第8行既有尾空白，原bytes照存。其餘精確排除此一raw路徑的staged檢查0；不是產品或測試斷言放寬。完整失敗stdout/exit原件保留。
