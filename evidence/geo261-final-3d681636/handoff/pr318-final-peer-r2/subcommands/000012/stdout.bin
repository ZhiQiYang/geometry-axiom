# #318 閱讀 A：正式掃描已跑，三項回歸待修，階段交接

依使用者核可的第3版 issue 留言6357744513，已落 D11／I19例外三／R6(d)(e)的精確差異、正典閱讀器及 W／H／oracle 實作。固定來源上，原528與鏡像1056筆已逐筆觀察為 buildable；完整 selftest 仍因三項既有回歸 exit1，尚未達最終驗收。本階段依使用者最新指示停止並交接，沒有繼續修來源或啟下一個stage。

| 唯一 current-state 項目 | 結果與身份 |
|---|---|
| product/source SHA（含canonical） | `ae74e51bba1efef48949c077635966273a9e8990` |
| evidence head（之後僅收據／工具／交接） | `9c534879b05058d2d62d8082be76038605ef0268` |
| 本次最新審查來源 | handoff `b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6`，14:56:46Z普通fetch0；#318最新設計追蹤14:47:42Z，已完整讀 |
| 三原閱讀器命令 | 原生成0／--check0／原unit0；51tests、無skip；獨立actual/public875項核對0 |
| native原7組 | 原child0／reaper0／wrapper0；7tests無skip，38原執行紀錄；10W＋actual-H共11組具名0/1/0；獨立actual325項核對0，public續審狀態見交接 |
| oracle原13方法 | 原child0／reaper0／wrapper0；13tests無skip；builder與checker兩獨立來源各0/1/0 |
| selftest --mutants-only | 初輪1（缺PROPOSAL＋真紅），同S補物化後r2仍1；三項真紅如下，沒有放寬斷言 |
| selftest --quick | 初輪1（同缺檔）；r2於15:04:37Z原child／reaper／wrapper／launch皆1，414.317秒，初末source同S且clean |
| quick掃描分項（不代表整體通過） | 原39850次快速建構、390掃描秒；矩形一維逐mm LT_Y及原二維臨界帶、579房×8=4632均無不可施工／檢查失敗；原528／鏡像1056逐筆漏掃0、非buildable0；不是--full一維全8排法 |
| golden原8房64排法及非空見證 | 本次selftest內逐支比對0不一致，I22非空四元組／矩形綁定／id非index牙齒通過；獨立golden撤回proof及standalone generator／byte-compare未跑 |
| CLI place／loadfile／rebuild通路 | 未跑；原生actual-H已放World不能代替CLI可達性 |
| 架構三原裁判／衍生四檔 | 未跑／未重產 |
| 完整專案native與全域突變帳本 | 未跑／未重產；M140–M150僅登記，不能改稱全域killed；共同最終來源的完整帳本由主代理一次重產 |
| 本輪允許skip／active測試 | 未宣告任何skip；現在沒有active測試PID，slot2已歸還root |

三項真紅是：原 `rc_through_reflex` 負控期待 `C8_I19_BOUNDARY_END`，實得只有 `C8_I22_NON_BOUNDARY_EXTENDS`；`COLSTEP(3000)` 與 `FZ9` 原房及鏡像的Y向排法各12個由應有的 buildable 變成 core_limited。後者的逐料原因尚未診斷，不改預期為 core_limited，也不直接重填golden。原負控成功時列印的[紅]與這三個真紅分開記錄。

初輪 selftest 還遇到稀疏 checkout 未物化 `geometry-core/framing-template/PROPOSAL.md`。已補同一S的24個精確tracked小檔共321715bytes，前後HEAD與完整indexstage bytes不變、source clean，再重跑未完成兩項；原失敗exit與完整輸出仍保留。平台exec transport曾中斷，既有quick實際PID仍活並跑到真終態，沒有重啟或略過。所有原argv、exit、完整stdout/stderr、環境、版本、SHA及工具hash在原包／inventory。

證據根目錄是 `evidence/issue318-reading-a-20261023/`：`CURRENT_STATE.json` 是唯一目前矩陣，`NEXT.md` 是接手入口，`QUESTIONS_HANDOFF.md` 列尚未解決與未驗項。祖先Ec5445caf保存三reader原173成員包；Ec3c823bf保存native／oracle13原253成員包與reader獨立peer；最新phase-stop原包保所有selftest初輪／r2、環境修復guard、transport來源、最新審查原文與交接。Ec3c內 `NATIVE_SUMMARY.json` 是native完成當下歷史摘要，當時尚未跑oracle13；之後oracle13已0，以本矩陣為準，不回改祖先原件。

仍最不確定的是13mm兩支同向boundary的實際初放／重建順序；目前只有靜態風險與明確已放World見證，沒有實測CLI死結或成功。必須保已放／有序依賴語意；真修法若觸及已鎖定決策或額外公理，交決策處理，不能自行加batch豁免。最新審查還要求README的custom範圍改成第3版已排除；現README:136仍留待條文確認，這項文件同步未做，不能把custom原C8_I19_PRIORITY案例稱為解決。

只改已核可四處SSOT差異，沒有額外改公理／決策佇列。木工推理前已完整讀 main指定日期決策與PR333 FIELD-RULES，來源SHA與全文hash保留；不新增h_max。沒有force push、沒有合併PR、沒有反向merge後棒noWood。後續上游source合流、改base、資源窗口與全帳本／架構重產由主代理安排。
