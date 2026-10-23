本 PR 補 Q38 AC23「面材貼齊角材」的具名反證。原接觸判式雖已由角材案例打紅，寬 346 mm 的面材案例位於 focused gate 不納入的 source-index 方法，缺少自身的反證。新增 u/v 兩個字面幾何案例及各自專用 SPM43／44，保留原產品、公理與判官。

目前仍是 draft；完整閘門與合流 expected 契約未完成，不可合併。

唯一 current-state 矩陣如下。固定基底 `5b0ce47d25393fad675bf506a9d296cbab43c35d`；實測測試來源 S=`af4fd36c17d05b5da2411b70266ed040e22a6561`；證據 E=`5c5b63f967a33e75f299250f97629325fff2a775`，兩者皆已一般推送。來源分支 `codex/geo260-ac23-proof-20261024`，預期 base 為 `codex/train-337-continue-20261024`。

| Gate | 實測來源 | 原 exit／結果 | 範圍與限制 |
|---|---|---|---|
| 原 selection／exception-evidence Python 單元 | S | 0；Ran 30、OK | 初末 HEAD／clean；不是 native aggregate 30 |
| 第一輪原 native focused gate | `c9269e136f3b40fbb5f9b5e13daa79a32d88efc4` | 2；baseline 29，原27過、新2 errors | 新測試錯讀 id 的包裝層而 KeyError；只編譯 baseline 一次、mutants 未啟動，原紅完整保留 |
| schema 修正 | S | 兩處 `m["id"]` → `m["value"]["id"]` | 原6個 literal rect asserts 不動；窄靜審16／0 |
| 修正後原 focused gate | S | 0；baseline 29／0，SPM43／44各1、killed | 各 mutant 唯一指定 AC23 方法的正常 AssertionError；3 builds，585份實際 C 輸入及3 ELF原hash保留 |
| 原 baseline 恢復 | S | 0；Ran 2、OK | 每個控制真0／1／0；恢復以相同 baseline ELF bytes 的私有可執行副本，不改原保留件 |
| 獨立 actual 對抗審查 | S | 1252 checks／0 findings | SHA256 `19aa5a34d342745f19e135c8235568fe22b064d6348a1aff2b0e7279c625f1be`，全文入證據包；審查數不是產品測試數 |
| 完整44-case Q38閘門／native30 aggregate | 待合流來源 | 未跑 | 本輪focused排除原source-index方法，所以baseline29，不能冒充完整30 |
| shared expected／全整合／帳本／架構 | 待合流來源 | 未跑 | 方法數28→30待主代理依合流次序更新；本分支沒改expected，也未自行重產帳本 |

允許 skip：無。本輪原編譯600秒、child900秒與全部 assertions、goldens、exception／cause／verdict 判官不變。原42cases、28methods、SPM03／04 killers 與 PAIR_CORNERS 閉包皆保留。新增 SPM43／44沿用各原故障及跨層閉包，各自只認新 AC23 的具名失敗，避免其他 TOUCH 已紅遮住面材回歸；全帳本123個M定義未改。

兩個幾何例沿用27／346／373／400 mm與板厚6 mm，第二個只交換u/v，矩形期望值均為獨立字面量。I45／R36既有「正面積才重疊、等號接觸合法」未新增數值門檻。

完整原件在 `evidence/geo261-final-af4fd36c/geo260-ac23/`：封包1148 members、4,014,694 bytes，SHA256 `228b54b277678d8dda80a1f67a025ac7602ca6d21914243c13f1042df510155d`。逐檔hash／來源／排除清單在 `RAW_INVENTORY.json`；ELF只排除Git封包，原件仍留雲端。包含首輪紅、修正、全部原命令／退出碼／完整輸出／環境／SHA、實際C、單元與靜／動態peer；producer本機封包逐bytes roundtrip已過；獨立public Git／body peer已核原包E023339的2354 checks／0，報告SHA256 `a81e4c9f165f7a8436bb33b380cc33cbf57a544ac11858a98f0c2ef55507a28b`。最後E只補peer原件與原出版raw，沒有重測或改寫原包。

限制：首輪未在後續schema編輯前另錄final-clean，照實保留；修正輪初末HEAD／clean已封。原子exception row沒有SHA欄，未事後填造，以父命令與原輸入間接綁定。旁錄只保原cleanup前資料，不改受測函數或原退出碼；這份證據不外推列車新SHA全綠。
