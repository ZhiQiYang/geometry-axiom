成功恢復連線時清除 `connection.error` 的過時錯誤，保留失敗狀態、編輯停用與原協定守門。這是 #320 的替代實作線 #344。產品以一般 merge 納入目前 provider-hint 列車 F7；保留原測試、golden、斷言與時限。

唯一 current-state 矩陣：

| 項目 | 來源／原退出碼 | 現況與界線 |
|---|---|---|
| 產品 SHA | S7=`cbb318d76d7d242ae0db760ae15d57ef1cad4aa0` | 一般雙親 merge：原 E=`c5a9d099863afdf030a5262a6aa26be16f094dbf` 與 train F7=`6df0264f75e84f03adb70746b6ac3db07a9910fc`；來源合流不是測試執行 |
| Evidence head | E=`a5ec136baf3909453867b3eed50f1b93b229ca59` | 本輪 `evidence/issue344-converged-cbb318d7/`；原 S540 VM9／strict row 與其他歷史收據原樣保留 |
| 一般 merge／來源核對 | merge **0**；無衝突 | F7 所有 registry rows 保留，K source-index count18，加本線原 `node:connection_recovery` count9；相對 F7 只有原五個非證據路徑 |
| whitespace 診斷 | 完整 staged diff check **2**；全部非 evidence scope check **0** | 唯一警告檔是 F7 已存架構原 stdout；index blob 與 F7 blob 精確相等，原診斷未刪改，不冒完整 check0 |
| NodeVM9 executable closure | S7 app／原 test／cdp／runner bytes 與先前本線相同 | 最近原執行仍綁 S540=`5402765c795769a77a7b249de1e3db80045a41de`，沒有在 S7 重跑或移標 |
| 歷史 S540 原 VM9 fixed／withdrawn／restored | **0 / 1 / 0**；9／6／9 pass，零 skip | 撤回唯一 app 清錯行，三個原具名 ERR_ASSERTION；300 秒原值、測試不變；actual318／0、原包649／0 |
| 原 aggregate selected row | **0 on S7** | 原 `python3 -B tests/run_all.py --only node:connection_recovery`，完整 registry 原0、strict9/9、零skip；needs=[]、原300秒，未加--build |
| 完整 native | **UNRUN on S7** | 局部 Node 與 root 其他 SHA 的結果均不代完整 native |
| 完整 canvas fixed／withdrawn／restored | **UNRUN / UNRUN / UNRUN on S7** | 原完整預設 canvas、每相35分鐘、golden 與 P53/P61 assertions 不變；S7 的 app-only 控制 V7 尚未建立 |
| 其餘五 browser jobs | **UNRUN on S7** | 不移標 root 或舊 #344 的綠燈 |
| mutation check／完整帳本 | **UNRUN on S7** | 最後共同來源由 root 統一重產；本線不另重產、不改 execution.head |
| 架構三裁判／四檔 | **UNRUN on S7** | 納入 F7 的四檔源自 root M=`e321026fb9bc9bc19c54b8034af6e6eaec2857f9` 實跑；本線 app 是 H 層來源，這些原件不冒 S7 執行／有效收據 |
| base 收斂 | 已納入 F7 產品與其已採用四檔 | 未為其後純證據提交重跑產品；若新產品來源變動再正常合流並判斷影響 |
| 歷史 S0／V0 | S0=`7b45013da647b791acda8f5977475e4123d5f8c4`、V0=`082feb0662fea32131f3f7fb8ca451679ab6421d` | 只屬舊來源，V0 不當成 S7 的新 V7 |
| 允許 skip／合併狀態 | 無新增 skip；**未 READY** | 完整 canvas 三相與最終正式驗收未完成；不合併 PR |

S7 相對 F7 的五個非證據路徑為 `geometry-web/app.js`、`geometry-web/cdp_test.js`、`tests/run_all.py`、`tests/run_all.expected.json`、`tests/test_connection_recovery.js`。registry 為完整 F7 加原 node9，其他四檔逐 Git blob 等原本線 E。核心 C/H/inc、native 介面、SSOT、workflow、golden 與架構四檔均保 F7；本次沒有再改產品修法或放寬測試。S540 的 VM9 與 strict row 原件已公開在 `evidence/issue344-vm9-5402765c/`，不重寫其 execution SHA。

S540 原三相命令為 `node --test --test-reporter=spec tests/test_connection_recovery.js`，原300秒。撤回的三個正常斷言為 `successful recovery kept stale error`、`completed retry kept stale error`、`loading echoed stale error`；恢復後來源 bytes、HEAD、index、clean 全核。DOM、transport 與 ReferenceWorkspace 為明示替身，不能代真 Chrome、HTTP 或 native 恢復測試。原 strict row 的 globalcache／sidecar 前後hash和stablemetadata相同，新 rowlog 保原path及私有收據，沒有刪除舊／新原件。

S7 原 selected row 已真正完成：私有 TMP checkout 649 個普通 Git leaves、10,824,604 bytes，HEAD／index／工作樹乾淨。原1份全域 rowlog 已逐 bytes、mode、mtime 還原，新的輸出另存；binary／sidecar 前後原hash與stablemetadata相同。沒有 C、build、HTTP 或 Chrome 執行。

下一步依 root 排程，從公開 S7 建立乾淨 app-only V7，保其他 tracked path/mode/blob 完全相同。原 full canvas S7/V7/S7 使用 HTTP19681/19682/19683、CDP9731/9732/9733 與獨立 TMP/profile，canvas 獨占；新的 K/source.c 必反映在真正原生 build closure，不偽造側車。fixed/restored 必完整 matched，撤回須原 P53-3/P61-10/P61-11 stale-error 正常具名失敗；crash、timeout、clean-SHA 拒絕、其他 golden 差異不算有效反證。這些仍是未執行計畫，root 另線 R7 結果不作本線 Chrome 證據。

完整 staged whitespace2 的本輪唯一原路徑是 `evidence/geo337-train-20261024/architecture-e321-complete/originals/subcommands/000017/stdout.bin`；兩側 blob 都是 `f866ef8eefef203f856d8ec92df33094dc466fe1`。合流原命令、完整 stdout/stderr、退出碼、環境、registry 與來源閉包都保留。先前 S540 的48路徑警告保留於其歷史收據，不混成這輪計數。PR 留言沒有可合併判決可引用；本稿不標 READY。

本輪獨立審查：Scbb 原 selected row 與正常 source push 277／0；425 member 原包逐 bytes 往返 1707／0。兩份報告、逐項檢查與 reader 一併封存；沒有新增 VM、C、HTTP 或 Chrome 執行。
