# PR #338 B3：精確三差與 P-189 正式終態

Evidence head：`288a8688ceffdcd1a9232bb81fcef13bde4c788b`。本分支只有 evidence，供主代理採入 PR #338；不另行聲稱整張列車可合併。

實際受驗 M：`0ae1728c2309e1d670369289a6b8da059fa63a50`。固定 main：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`；固定 base：`3e600772076465fc65a26ac09055028301c0fb0b`。

| 項目 | 狀態 |
|---|---|
| B3 精確比較 | 已實跑 exit0；175 場景、main/base/fix 525 程序；限定三場景精確文字／位置以外 bytes 與 returncode 不變 |
| B3 新 timing | 已實跑 exit0；36 原順序樣本，N16/32/48/64 fix/main=0.8928012519561815／1.118816930137685／1.0710556844547565／1.4289458902827186，皆 ≤2 |
| B3 反證 | 3 baseline 0、27 指定負例 1、3 restored 0；真 process 的原流 replay，不冒充產品再執行 |
| 舊 strict 紅 | 歷史 L driver1／timing-only overall false 保留；本輪未套政策三場景紅另存 |
| B1 whole-memo | 本分支未執行；三個原 R8 ELF 不能以新建 P189 binary 頂替 |
| B2 閉包 | 由主代理另一工作線交付；本分支未重抽 R8 |

原 P189 timing 的真正 source 是 L；L→M 有 source.c、references.inc、contact_world.c 三個編譯輸入變化，因此只重跑受影響 P189，沒有將 F9／F8 收據移標。185 個源檔逐 blob核對，donor/private gcc -E 完整相同。比較器不正規化訊息，錯字、錯位、第四差、dump byte、returncode 均具名轉紅。

原件與可重現指令：[B3.md](https://github.com/ZhiQiYang/geometry-axiom/blob/288a8688ceffdcd1a9232bb81fcef13bde4c788b/evidence/geo337-b3-p189-20261029/B3.md)。原始封包 SHA256：`319eaf847921990e159648cae96ee673ae044f2471005ad1cbec6a9a4461dbd5`，1,545,250 bytes、3,725 個原件逐檔核對。

本輪準備期 git archive 因 promisor fetch 滿碟 exit128、0產品樣本，原錯誤保留；其後採已 materialize 的 M compiler closure 私有複製，沒有降低任何容量／時限／產品門檻。另一執行者已唯讀對抗複核原件、closure、反證與 ratio，未發現 B3 阻擋。
