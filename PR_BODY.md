這份同列車子分支消除來源圖新增edge時重複的hash/probe：lookup已找到的空槽在同容量下直接重用；rebuild時失效，calloc失敗仍沿原線性降級。edge/node陣列順序、公開API及nodehint/hash策略保持原樣。

唯一 current-state 矩陣：

| 欄位／gate | 目前來源與結果 |
|---|---|
| Product SHA | `9430bae568feb98805072930c92f9a03a1250d4e` |
| Product＋test final SHA | `a543eef67b81f8d8800f32d5dc4a5641840d2943`（只修Linux測試暫存目錄名稱） |
| Evidence head | `9b41d395fb2c5d6c971de4b13d4d2ac6701ff22c` |
| Base | 公開列車`b621a4fbc3cdea359b3676fb22dc8ef566968b8a`；未混入#343，先隔離probe因果 |
| SourceIndex 全17（原14＋新3） | Sa543實際exit0、0 skip |
| 編譯／連結、native原流 | 56次全0；43個native子程序完整stdout/stderr與ELF/source snapshots |
| 原8＋新2語意反證 | 10組實際0／具名assert1／原baseline重跑0；完整有序graph oracle保持 |
| 整段probe撤回／恢復 | 三版獨立編譯；有序graph皆0，精確hash次數21／31／21、cost exit0／1／0 |
| 本切片允許skip | 無 |
| 175/350 scene有序圖＋guards、原性能門檻 | 新整合F尚未跑，仍由root驗收；不宣稱N64/main≤1.3 |
| 完整native／6browser、帳本、架構 | 新整合F尚未跑／重產；由root最終統一處理 |
| 狀態 | 專項測試綠；未READY-TO-MERGE，不合併PR |

證據位於 `evidence/geo323-edge-probe-a543eef6/`：原始兩輪、全部編譯輸入、原子程序輸出與退出碼、來源SHA、環境、ELF、獨立審查及每檔hash索引。舊受驗L的N64/main1.4283仍是歷史真紅，不把新unit綠替代原perf裁判。

歷史第一輪S9430：17項全跑、16方法綠，whole三subphase因來源目錄與Linux輸出ELF同名而link失敗（ld `Is a directory`）。只改test work目錄前綴後以新Sa543完整重跑；不改斷言、golden、30秒case或300秒compile/link，不把編譯錯誤算mutation kill。root、combined與specials原靜態審查漏掉這點，原紅與修正前後檔案都保留。

沒有新公理、決策或數值門檻；沒有force push或合併PR。原完整帳本與架構重產仍依主列車最終SHA統一處理。

獨立審查：產品31/0、companion124/0、測試路徑修正13/0、source兩次實際出版390/0、C17實際原流1427/0。靜態審查不代替實跑；首輪漏項與審查helper初錯都留原件。
