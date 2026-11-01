唯讀對抗審查完成。修訂後 PLAN 的原件界線、最小診斷方向與靜態候選可接受；兩項審查意見已在本次 pin 收斂，沒有未解的靜態準備阻擋項。這不代表 wrapper 已驗證、N512 已執行、正式 gate 通過或根因已確認。

審查只讀指定 package 及 FACTS 綁定的 21 個必要原件，執行讀檔、雜湊、JSON 與來源檢查；未執行產品、C 編譯、profile、browser、Git、fetch，也未改分支、原 collector 或原件。peer 只寫本目錄 REVIEW.md／REVIEW.json。複雜度另由唯讀子審查獨立核對，該子審查未寫檔。

輸入 pin：

- FACTS.json：`601bbed0cc5dabe8a823996adc1cdb67a06195c29f5dea5f018941e01850896b`。
- 最終 PLAN.md：`d876948f3e70c1c8d13d8d6118178cc0290095a2301cd49e77ed301bf386643d`。
- 初審 PLAN.md：`c5b5c068faa67966b820c5ab0978f43b657e914d798b24028c4096f76ab6ee2a`；作者收到意見後修改，peer 在產出前重新讀取、核對最終 pin。
- F0f：`0f695866c0ba12d2c70dfd7d40628d0fda0f905f`。完整 package inventory 與必要原件 hash 列於 REVIEW.json。

審查意見：

1. **D1，已收斂：`fgets(NULL)` 不能一律稱為 EOF。** 初審 PLAN:29 只有 stdin_eof；NULL 也可能代表讀錯。修訂後明列 stdin_eof／stdin_error，要求保存 feof／ferror，避免將讀錯誤標正常 EOF。未來工具實作仍須保留原 return／errno，並用合成讀錯案例驗證；本審查不是該驗證。
2. **D2，已收斂：contact collection 的條件。** 初審 PLAN:46「每個 member 都會」過強；`references.inc:647,649–650` 跳過未放置與前置失敗者。修訂後限定已放置且 anchor／host／footprint 前置成功，成功 fixture 的成本候選不變。

核對結果：

- **79／83 都是首次四指令整批 600 秒。** 同一 140-byte stdin，SHA256 `6589eb1c26654effdceee204dd0871d688f8a10c5bbe663ffc974983d63339ff`；順序 loadfile、dump、objects、references；兩筆均 TimeoutExpired、completed_process_returned=false、returncode=null，沒有 partial stdout／stderr。host test:224–231、242–254 顯示 canonical／sequential replay 都在首批成功後，因此不能歸因 loadfile、聲稱進入 replay 或把 null 改寫成子程序 exit 1。缺檔也不能證明子程序沒有輸出。80／81／82 的已存原輸出各四個 ok=true JSON 行、stdout hash 相同且 returncode=0，均未重跑。
- **collector 已保留例外 attributes。** `observe_bridge_bytes.py:317–337` 重拋原 failure，finally 讀取 result 或 failure 的 stdout／stderr 交給 retain；僅補同樣 TimeoutExpired attributes 不會提供新的當次資料。
- **F73 未重跑這兩個方法。** 原 RESULT source_sha=F73、full_H7_executed=false、unfixed_512_methods_rerun=false；phase selectors 不含兩個 placed512 方法。F0f 紅不可移標 F73／F8。
- **旗標、fixture 時序與 ELF 證據強度正確。** 原 compiler-input-snapshots 選取的四個相關 argv 均為 -O0。fixture 45,154 bytes、SHA256 `760a7169ea3577341b4b0ec1b56ea39c21c85c777434325ec906debe0a816f10`，512 timber／512 place；原 MANIFEST 明說第一個 timeout 後、第二次執行中取樣，非任一次 preexecution snapshot。原 ELF 為收據 hash，payload_retained=false。
- **來源與 Git 留存一致。** 12 份來源的 SHA256、git-r2 show 原流及 ls-tree Git blob ID 全部對應。15 筆成功 git-r2 皆為 show／ls-tree，另有保留的 git/001 exit128 與 initial script；總嘗試不能誤稱只有15。COLLECTION_NOTES 已說明初輪 repo 查詢失敗及 diff 僅限12個選定路徑。peer 沒有新跑 Git。21 個必要原件 hash 與 FACTS 全符。
- **沒有放寬 timeout／golden。** PLAN 保留 fresh bridge、N512 fixture、四指令順序、單一整批600秒、O0、原 subprocess.run／kill/reap、raw bytes；禁止拆批、重置timeout、減N、正規化、紅後重抽及挪用R8樣本。既有 oracle、canonical bytes、sequential replay、513/history及撤回／恢復反證仍須保留。
- **wrapper 邊界只支持粗階段判讀。** 僅 stdin-return 不能證明 handler 完成，須配對 flush-return 與完整原 JSON，JSON ok 另核。handler 內 printf／fputs 也可能在外層 flush 前因緩衝區寫滿而做 I/O，故缺 flush-enter 不等於幾何計算卡住；PLAN 未作此推論。未來須驗證 stream 過濾、單次原呼叫、errno、符號／callsite 覆蓋、事件完整性與觀察器 fault；故障或額外成本不能倒推原600秒根因。
- **Σk² 候選成立。** generator:228–230 交錯 timber／place，host test:123 使用 single；第 k 次成功 place 時有 k 個已放置member。`references.inc:847–848,734–736` 每次重驗，`current_geometry.c:6318–6320`、`references.inc:645–682` 保留兩兩遍歷；全部成功時累積ΣC(k,2)=Θ(N³)為靜態候選，非量測或根因。
- **dump 二次選取與既有索引沒有被誇大。** `references.inc:898–902` 每次選最早order都掃全陣列，全放置時Θ(N²)；`engineering_bridge.inc:10` canonical hash再走dump，loadfile／dump／references呼叫可由web_bridge:458,980,1000與reference_bridge:430核對。K node／edge hash indices、contact order index、stable sort與indexed dedup均已存在；fallback是否命中需數據。PLAN將這些列為條件候選，未聲稱占600秒主因。

結論僅適用上述最終 pin 的靜態準備。接下來可依 root 排程製作外部草稿與純Python工具自證；C編譯、符號校準及真實N512執行仍未發生，工具自證也不能充當產品撤回反證或正式gate。
