# #314 修正撤回自證索引

本索引只整理已存在的原收據與輸出，沒有執行測試或改來源。精確 SHA、argv、退出碼、raw 路徑與 SHA-256 見 `FIX_PROOF_INDEX.json`；沒有證據的欄位保留 null，不拼接不同版本的紅綠。

| 修正／處理 | 真受驗來源 | 修正撤回自證 | 範圍與限制 |
|---|---|---|---|
| candidate witness 新 stagger 語義欄初始化 | P3 `4f669733`，實跑 evidence descendant `c0a20078`，414 inputs等P3 | 3原case各0/1/0 | 兩處初始化合併撤回；具名ASSERT為 file-replay-frame-final-seal、default-evaluation-succeeded、default-final-seal。非每欄獨立突變，也沒有 memcpy-only控制。 |
| 原canonical reader同步 | 同P3／c0a20078 | 具名idempotence原0/1/0；原51方法前後均0 | 只換舊canonical再放回，SSOT／白話／決策／Backlog不變；非產品突變。 |
| ASM cancelled-preview 工具舊anchor重錨 | 原診斷P3／c0a20078；修正自證c4aad5d7／負控238a5125 | **原anchor三方法真0/1/0** | 只撤一行舊anchor，2條正常AssertionError；001 collector/outer1保留，002只補restored0，無重抽／compiler；不是重跑完整ASM行為gate。 |
| ASM 外錄製guard分類 | 同P3／c0a20078 | 不要求新產品突變 | 原outer仍1；2187來源／裁判bytes分類只證evidence-only變動，不把原1改0。分類程序退出碼未被該JSON收錄，保null。 |
| manifest H登錄／完整W guard union／精確LF digest | P3由進度正文指明；本prepare目錄無實跑SHA/rc收據 | metadata，不要求新產品突變 | 920→928 IDs，55 strings不變；三原架構裁判與Linux四檔須另引真收據，這份inventory不冒稱已執行。 |
| 精確補既有tracked fixtures | P2 `291ce90a` | 環境修復，不要求新產品突變 | 兩受影響Node檔94/94、graph5/5原0；不是整套Node，也不是P3／最終F驗收。 |
| bridge equivalent runner相容性 | `c4aad5d7`；本地負控commit `160e9dc9` | 原M110 CLI真0/1/0 | fixed/restored各真baseline/mutant/restored 0/0/0，原單筆validator綠；負控invalid且無execution，不冒產品killed或全表strict0。原honesty74方法0。 |

ASM **anchor修正本身**的缺口已以原三方法、三態精確SHA與完整原raw補齊。001的原baseline0／withdrawn1沒有重抽，原collector／outer1仍保留；002只補缺失的restored0。與較早完整工具三個產品mutants／outer1分開，沒有拼接P2紅與P3綠，也不冒稱重跑完整ASM行為gate。封存見 `anchor-proof-publication-001/`。

生命週期唯讀審查沒有重現產品漏接；巢狀parameter-package Q3、>8 facts／realloc／OOM、確認後段逐分支故障、完整P177全域動態計數仍是該靜態審查的實證限制，不能寫成已動態測過。未因此改公理或鎖定決定。

進度PR正文仍是較早草稿。L／A／F角色在JSON故意保null，須由父代理依真正完成且公開的帳本／架構／正式驗收填入；以上診斷不改標為最終SHA。
