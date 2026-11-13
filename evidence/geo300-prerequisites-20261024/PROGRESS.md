# GEO-300 前置進度

目前產品 SHA：`aa0e3938f17dc996ef5e7410db4844b31856d2a6`。已普通 merge #339/#340 聯集 `1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599`，PR base 改為 `codex/geo324-faces-20261024`。原正式 C 證據固定在 `c493b7315d0cd3b16014add96af969c49ebf4660`，沒有改標成新來源重跑。共享 source／expected 棒已交 GEO260 owner，本 owner 後續只寫自己的 evidence／正文。

| 項目 | 結果與範圍 |
|---|---|
| 一般 merge #339/#340 | exit 0／零衝突，兩親 E383＋S1f0 |
| 相對 #339 的產品差異 | 原三 leaf＋expected 單一 count 9→10；SSOT、決策與 mutate 原樣 |
| 原 W 木接觸 | Sc493：10 methods／23 controls，原退出碼 0、0 skip |
| 原接觸來源 | Sc493：15 methods／11 controls，原退出碼 0、0 skip |
| 原 Reading A native | Sc493：7 methods／11W＋1H controls，原退出碼 0、0 skip |
| 反證 | 全 46 個普通 control 都是真編譯／原具名 ASSERT 0/1/0，含五新控制；另保留原 atomic bridge 額外事件 |
| 編譯／連結 | 原 111＋85＋86＝282 條全部 exit 0；不是 302，原口述算術錯與 peer finding 已封存 |
| 獨立 actual peer | 1020 checks／0 findings；只證 Sc493 部分原 C 裁判，不是完整 native／browser／效能 |
| expected 登記 | 只 wood_contact_world 9→10；原 9 方法 AST 全保，新方法共 10。noWood13／faces45 原樣。原 strict comparator 9 拒／10 收／11 拒；獨立 36／0 |
| C 裁判閉包 | Sc493→新 source 全部 C/H/inc、三原套件及 native 支援碼無差；actual SHA 仍保 Sc493，新 source 無額外執行聲稱 |
| 完整 native、browser、架構、全帳本 | 尚未對這個候選完成；全帳本由 root 唯一統籌 |
| 完整優化撤回、成本／效能 | UNRUN／UNMEASURED；不冒稱撤回應語意等價的原算法被殺，沒有新門檻 |

正式原件共 350 files／19,527,338 bytes，連同獨立 peer、原工具、merge／expected 原 streams，封入 `C493_THREE_SUITE_ORIGINALS_AND_PEER.tar.gz`：SHA-256 `145048fb4827ec6180e9798dd0beeec0facc2e4e45215c581d1b78e88df1bc0f`。456 個成員均完整讀回核 bytes/hash。原始資料未刪除或覆寫。

最壞配對 O(F²)、insertion sort、call-growth 與 cut-list 平方儲存仍在；本候選只消除標準容量路徑的反覆 memmove，不冒稱容量 512 前置已完成。下一步成本觀測須另排與完整帳本不重疊的時槽；若有新門檻，先列 QUESTIONS。
