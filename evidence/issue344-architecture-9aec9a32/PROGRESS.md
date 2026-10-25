# #344 目前架構驗收與未完成項

成功恢復連線後清除過時的 `connection.error`；失敗狀態、編輯停用與原協定守門維持不變。本輪修正架構清單漏更新的 `cdp_test.js` LF 排除雜湊，並在固定來源重新執行原架構裁判與反證。**維持 draft；完整 browser 與基底驗收仍未完成。**

以下是唯一 current-state 矩陣；歷史收據不移標。

| 項目 | 來源／原退出碼 | 現況與界線 |
|---|---|---|
| 產品／本輪實際執行 S344 | `9aec9a32630fc65f94c53d49e99969e546574d6e` | 已普通 push；parent `a5ec136baf3909453867b3eed50f1b93b229ca59`，唯一變更是 manifest 的一個 LF digest |
| 證據及衍生檔採用 E | 本檔所在證據提交；完整 SHA 在另行 prbody 列明 | `evidence/issue344-architecture-9aec9a32/`；四檔實際執行來源仍為 S344 |
| 原架構三條 | **0 / 0 / 0 at S344** | scanner 334 owned／270 exclusions／6 trusted／798 edges／0 diagnostics；generic 205、product 18，零 skip |
| 完整來源閉包 | **604 inputs 前後一致** | 相對原架構執行 e321 只有 app.js、cdp_test.js 兩個 H 輸入變動，其餘 602 Git blobs 相同；三裁判、SSOT、HEAD 前後不變 |
| 單 digest 撤回／恢復 | **0 / 1 / 0 at S344** | 撤回只得到 `EXCLUSION_DIGEST geometry-web/cdp_test.js:1`；固定與恢復的完整 stdout 等於原正式 scan |
| 原九組 W policy guards | **各 0 / 1 / 0**；兩 neutral **0 / 0** | 937 identifiers／55 strings 未改；歷史 928 原件保留，撤回控制另存只同步同一 cdp digest，避免無關雜湊錯誤遮住具名政策反證 |
| 架構四檔 | **已重產並採入** | manifest、scan 與 S344 原 bytes 相同；報告、receipt 更新並明列 sourceBaseHead=S344；沒有聲稱執行發生在後來的 E |
| 歷史 VM9／strict selected row | S540 VM9 **0 / 1 / 0**；S7 strict9 **0** | 保留原有效收據，這輪未重跑；不冒 S344 的新執行 |
| 完整 native | **UNRUN at S344** | 局部架構與 Node 結果均不代完整 native |
| 完整 canvas fixed／withdrawn／restored | **UNRUN / UNRUN / UNRUN at S344** | 尚未建立新 app-only 撤回來源；列車 F9 的 canvas0 不適用本線新增的恢復測試 |
| assembly、documents、grid、space、timber | **各 UNRUN at S344** | 保留原 workflow、獨立埠／TMP、原時限與 golden |
| mutation check／完整帳本 | **UNRUN at S344** | 最後共同來源由主代理統一處理；本次不另產重複帳本 |
| required CI | 新 E **未讀** | a5ec136 審查所述七 job failure／steps 空保留為歷史；同源替代驗收條件亦尚未達成 |
| base／合併 | 仍疊 train F7；**NOT READY** | 未 merge F9、main 或其他支線；#338 基底與本線完整 browser 阻擋未解除 |

本輪唯一修正將 `product-architecture.json` 中 `geometry-web/cdp_test.js` 的 LF hash 從 `bb66742aa10b603b84362277f9f2c4275da8904925e75c618f252bd7df42cc3e` 更新為實際 `1f3e2e36283ed7bbf6c4ad2cf3dc12c685667356d186d9fbd47bc5f0520f07ee`。其餘 manifest bytes、分類、禁止識別字、字串政策皆不變。產品 JS、tests、golden、時限及公理／決策文件未改。

原命令逐項封存 argv、完整 stdout／stderr、退出碼、環境與完整 SHA：`python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`、`python3 -B tests/test_architecture_contract.py`、`python3 -B tests/test_product_architecture.py`。正式 driver 共 57 條原命令；outer／host 均真 exit0。閉包 SHA256=`71caf2df36a51b86da3d0553abd7ccebb7542d9dce2ec3f065e8d90a16ebbe0f`。只補齊既有 sparse checkout 的 613 必要檔，沒有編譯 C 或啟動 Chrome。

完整原件與獨立對抗審查見 [本輪 evidence](./)。來源發布獨審 257/0；架構 actual 2683/0。封存／工具審查不是額外產品 gate。

仍需完成最新 [#344 審查](https://github.com/ZhiQiYang/geometry-axiom/blob/6aa1c05fc94349866fe8c8f96b306b8a70d847db/handoff/pr-reviews/344.md) 的 B1–B3：完整 canvas 固定／只撤回 app 清錯行／恢復三相，撤回須由原 P53-3/P61-10/P61-11 具名 stale-error assertions 殺死，不能以 crash、timeout、來源拒絕或其他 golden 差異充數；另五 browser、完整正式驗收及已驗收 base 尚待排程。不新增 skip、不降低斷言，不合併 PR。

歷史 S540=`5402765c795769a77a7b249de1e3db80045a41de` 的 VM9 三相為 9／6／9 pass，三個失敗為 `successful recovery kept stale error`、`completed retry kept stale error`、`loading echoed stale error`；明示 DOM／transport／ReferenceWorkspace 替身，不代真 Chrome。S7=`cbb318d76d7d242ae0db760ae15d57ef1cad4aa0` 的原 aggregate selected row strict9/9 保留。舊完整正文與來源合流細節見 [歷史 D b169e27](https://github.com/ZhiQiYang/geometry-axiom/blob/b169e27ebb4b5835af50a4f070af290c7622630c/PR_BODY.md)，只作歷史，不作第二份 current-state。
