把既有角材上限從 64 擴至 512，將 W 的單一容量常數連到 H admission、真 document arrays、contact、cut-list 與 span scratch，並在 world validation 的 callback 前拒絕超容量輸入。新增具名編譯契約，避免 H／W 不同容量造成陣列或 scratch 不一致。其他邊界、placement、obstacle 等容量保留。

本片疊在 #128 P2，已正常 merge #346 的正式證據，順序為 #343 → #346 → P2 → 本 PR。它是 #300 的容量草稿，還沒有正式 C 或 browser 驗收，不關閉 #300。

## 唯一 current-state

| 欄位／gate | 目前值或退出碼 | 精確界線 |
|---|---|---|
| product SHA | `400a6d0ca50f3aca104fb569c77c8ef753c93355` | 七產品 leaf、六測試 leaf、兩 registry leaf |
| evidence head | `EVIDENCE_HEAD_PLACEHOLDER` | 只加入靜態準備原件與 UNRUN 進度 |
| base／普通 merge | P2 `6d9d46e8d16af75351924c6d47a078d3eb647cc0`；merge `696f7f07846c6224775dab5736bd1dc45541a4bf` | 第二 parent 為 #346 E `eaf15e239324a6464a04740647afccce3a3c17c7` |
| apply／diff check／一般 push | **0** | 公開 source 的 15 leaves 與已審草稿逐 bytes 相同；H 保留 CRLF |
| 獨立靜審 | **12/0、39/0、60/0、73/0、1780/0** | 計畫、W、H/registry v2、實際套用、公開 source/原件包；非 C 執行 |
| 新 W／H suites | **UNRUN** | AST 7／5 方法，尚未 runtime discovery 或編譯 |
| 新撤回／恢復與七 ABI 控制 | **UNRUN** | 只準備測試，不宣稱 killed 或正常執行 |
| 舊 contact／report／panel suites | **UNRUN at this S** | 保留原 64 witnesses、panel=13、report=11；不挪用舊 SHA 的綠燈 |
| 完整 native／六 browser／專項／效能 | **UNRUN** | 沒有新增時間門檻，也未聲稱擴容後效能通過 |
| 最終帳本／架構三裁判與四檔收據 | **UNRUN** | 主代理依最後來源統一處理；未改 tests/mutate.py 或重產帳本 |
| 允許 skip | 沒有新增 | 目前沒有正式執行，不能宣稱 0 skip |
| 合併狀態 | **NOT READY** | 正式 C 時槽尚未授權，所有 runtime gate 待跑 |

測試把原 64、真 512 與真 513 邊界分開。W 包含報表 ID 池／按值 copy、contact 穩定排序與 fallback、validation callback 邊界與宣告容量。H 使用真 bridge／World，準備 512 宣告、513 原子拒絕、既有 ID 更新、undo／redo／dump/load byte identity。512 validation 正例及 bridge 宣告是未放置成員，不能替代 512 個已放置角材的幾何、施工或 UI 驗收。

撤 guard 的負例避免越界：宣告只呼叫 direct API；H 只送缺 ID sentinel，必須在 append 前語法拒絕，不將有效第 513 成員送入已撤保護的固定陣列。七 ABI 負例只預期具名 typedef 編譯拒絕，再恢復原值重新編譯；不執行混用容量的 ABI 物件。所有正式反證目前均未跑。

`evidence/geo300-capacity512-20261024/RAW_INDEX.json` 保存 578 個原件的 path／bytes／SHA-256，archive `original-capacity512-drafts-and-static-reviews.tar.gz` 為 751,021 bytes，SHA-256 `0b6ea82d93952e40dc199483828c3e595401720f4e36da755022e9e8fe016542`。公開 source 的原 Git 命令、退出碼與 15 個 blobs 已保留；原 H v1、registry 排序修正前稿及 peer matcher 初錯誤也保留，皆與產品執行分開。

未改公理、決策佇列、K、斷言、golden 或原時限。最不確定的是尚未執行的 512 真 bridge／compiler／完整放置與效能結果；下一步在固定公開來源跑受影響的原裁判與新測試，依實際紅燈修正，最後統一重產帳本與架構。
