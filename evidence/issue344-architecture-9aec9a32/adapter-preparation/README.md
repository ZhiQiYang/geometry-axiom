# #344 exact 架構 adapter：待排程

此工具尚未執行正式架構、單 hash 反證或九組政策 guard。沒有改 checkout／分支、擴 sparse、建立大 checkout、編譯 C 或啟動 Chrome。舊 Node strict 9 不重跑。

`refresh_architecture_cdp_exclusion.py` 從原 K-only driver（`5b76f54d…`）精確適配；完整來源差分在 `ORIGINAL_TO_ADAPTER.diff`。預設只印 dry plan，未給 `--execute --root-scheduled-architecture-run` 不會讀 checkout、import recorder 或建立正式輸出目錄。Python `-O` 明確拒絕；本次僅做 default／`-O`／default 的工具入口 metadata `0/1/0`，**不是 EXCLUSION_DIGEST 或產品反證**。

只接受 `a5ec136baf3909453867b3eed50f1b93b229ca59` 的乾淨可解析後裔，與它相比非 evidence 差異只能是已審的一行 manifest 修復。若先合入新列車而多了其他產品差異，工具會拒絕；必須另核新的 closure，不能刪 guard 或改寬名單。

不改的標準：604 inputs、334 owned、270 exclusions、798 edges、6 trusted、937 identifiers／55 strings、原三裁判（205／18、零 skip），原所有來源／judges／SSOT 前後 hash，原九個 W guards 與兩個 neutral probe。只接受舊 receipt 實跑源 e321 的兩個已核實輸入變動：app.js 與 cdp_test.js，其餘602 Git blob必須相同；兩項新／舊 blob、LF 值與完整預期 closure 都固定。

唯一 manifest delta 是 cdp_test.js 的 LF digest `bb66742a…` → `1f3e2e36…`；還原後必須逐byte等於原 manifest。歷史928原件仍以 `80f44b8c…` 原樣保存；九個 W 反證實際使用另存衍生副本 `2661beb6…`，只同步同一 cdp digest，且與新 manifest 恰差原九 identifiers。收據明列衍生身分／hash，不冒原歷史 bytes。

新工具包含真正的單 hash fixed／withdrawn／restored 執行段：同源原 scanner 三次真 `0/1/0`；負例只允許 `geometry-web/cdp_test.js:1 EXCLUSION_DIGEST` 與原精確訊息，不能把其他錯誤算反證。固定／恢復完整 scan bytes 必須等於當次原正式 scan。所有四檔寫入來源外的 `new/`；只有全部原裁判與反證通過且來源／工具前後不變才產生成功收據。

主代理採用流程（目前未執行）：

1. 確認原 #344 head／遠端仍為 a5ec136b，從它開自己擁有的子分支；保留原 sparse／index／fixtures。套用先前獨審1793/0的 `fix-exclusion-digest.patch`，只提交一行 manifest 修復並普通 push，固定完整 `S344`。不推 Claude/Grok 分支。
2. 安排資源後提供完整604輸入及三裁判的同源乾淨 checkout；現有 sparse tree 缺 manifest，不能直接跑。本準備未配置該 checkout。新 output 必須不存在且在 source 外。
3. 用原 c387 wrapper 封存外層 argv／exit／完整stdout/stderr／環境／SHA，設 stack 16384 KiB，再執行：

   `python3 -B refresh_architecture_cdp_exclusion.py --execute --root-scheduled-architecture-run --root <完整乾淨S344-root> --sha <完整S344> --out <新鮮外部out>`

   工具固定 prior=e321／historical=ca7838，原 timeout 行為未改。任一失敗保留已執行原流，外層真 exit 必須封存；未完成項不得標綠。不得直接套用本次 dry-plan 的退出碼。
4. 將實際四檔／604 inputs／三裁判／單hash0-1-0／九組W guard與neutral原件交另一代理獨審，再由 owner 採入並普通 push。執行 SHA 與衍生檔採用 SHA 分列；不自行改寫 execution SHA。四檔不代 native、browser、ledger、性能。

本目錄 metadata 少於500KB。正式執行的輸出量須由 root 另作資源安排，這不是新的產品數值門檻。canvas 仍獨占，本次只做 AST、來源文字適配及乾燥入口檢查。
