# #314 完整 native 診斷進度

這是 P2 `291ce90abf9c3bfaf68bd61c4969f2ff9a1be6f6` 的隔離診斷，非最終 SHA 正式驗收。原 227 個登錄項目全部跑至終態，2026-10-22T23:44:31.876772Z 結束，原 `tests/run_all.py --build` 真退出碼 1。環境介面切換清空了外層 exec session registry，外層 terminal code 無法重新取得；未把它代填為 0。原程式與 stdout 持續完成，沒有重跑或中斷。後續唯讀舊shell `/proc/571656/stat` 得OS wait-status0，另存original-shell-os-status.json；那只是shell層，不冒當原run_all退出碼，原native judge仍1。

原完整摘要：已計數 5268、pass 5231、fail 36、error 1。core 165/165 通過。原 mutation:check 為 100 definitions、78 records，其中 75 stale、3 retired、22 unrun；必須整份重產，未宣稱通過。

| 紅燈 | 分類／下一步 |
|---|---|
| assembly 原12：10通過／2失敗 | 1 舊取消工具錨點；1 缺既有 subreaper 導致 orphan zombie 的環境項。保原判準，重下語意錨點並以原 reaper 重跑原完整工具、12 unit、3 anchors。 |
| reader 原51：45通過／6失敗 | 新 mutant 追溯使唯一 canonical 衍生物過期；用原同步器機械更新，再做原51與撤回／恢復控制。 |
| candidate 原26：23通過／3失敗 | witness 把整個 operation 填 A5 後只初始化舊欄；補新有語意 count/steps/seal 的空值。原 padding A5、全部26 ASSERT與成本數字保留。 |
| graph 原5：4通過／1 error | 稀疏副本缺既有 tracked scene；只從 P2 exact blob 補檔並重原 suite。 |
| anchors 原3：1通過／2失敗 | 同 assembly 取消工具舊錨點，不加入 known drift。 |
| product architecture 原18：setUpClass 全阻擋 | 既有 JS exclusion LF digest 必須機械更新；一併登錄真新 H 檔及完整 W lexer union，其他 policy 不動。 |
| Node 原聚合：4失敗 | 稀疏副本缺三份既有 tracked gcanvas，已補原 P2 blobs；原兩檔 94/94、exit0、無 skip，reaper 完整回收。 |

集中修正已固定並普通推送 P3 `4f669733282613a6f1e4a627c448374716496daa`，僅四檔21+/3-；沒有修改產品規則或放寬斷言。W guard identifier 為原920與全部真W C token集合 union得928；strings55不變。新H `geometry-app/native/stagger_facts.inc`。JS LF digest `17e2c37434e1dcfeb6d8af90e98bb681ba49083fdee016e936052f13cae62803`。原同步器退出0。後續修正診斷已完成，詳見 `../geo314-repairs-4f669733/PROGRESS.md`：candidate26與三控制0/1/0、reader51前後與控制0/1/0、ASM原三裁判0/0/0（外包guard1另存）、graph5、架構三條均有真raw；此處仍保原P2完整native紅燈，不改標為綠。

## 原始證據與覆蓋界線

本目錄保留完整 aggregate stdout/stderr、原收據、全部610逐 suite原raw、ledger前後bytes、2187來源輸入的前後archive及官方privatecache原archive。詳細raw與metadata在 `native-forensics.tar.gz`；前後來源分別在 `source-inputs-before.tar.gz`、`source-inputs-after.tar.gz`，全部檔案SHA見PUBLICATION.json。`observed-source-buildlog-payloads.tar.gz`另保10173個真實file-version events或manifest所引用的來源／buildlog payload，共413488254原bytes；沒有補造原觀測缺口。完整原位置 `/workspace/geo314-work/native-p2-001/` 亦保留；optional ELF/object/assembly額外payload完整冷存在下列archive。原 OUT_DIR-only 外部環境適配，沒有改 compiler flags、smoke、fingerprint、suite或裁判；原前後 contract 比較完全相同。原生診斷本輪未外包既有 reaper，環境 zombie 紅如實保留；往後含子程序／負控制一律包原 reaper。

額外唯讀 inotify 只屬 observed-only。容量保護於23:34:10.820863Z把唯一 objects 目錄設0555，之後可選 payload PermissionError 與 race missing 全有紀錄；不能稱完整 transient capture。原 native、source、build log、stdio未改。終態後恢復原0700。root 將既有13438 blobs／1490402516 bytes串流冷存 `/tmp/geo314-native-p2-observed-objects.tar.gz`（344955200 bytes；SHA256 `bfa7cdf071b652425bedecf758b53679a29e1183eb7e73ade09edbd25de93b12`），逐成員 bytes/hash 驗同後才釋原可重建payload，元資料與COLD_STORAGE.md保留；不是刪除失敗證據。

後續原工具／reader／candidate的具名正常0/1/0、graph環境項及原架構三裁判診斷已收齊，詳見修正目錄；接著固定source S整份帳本，架構四檔／最終SHA完整驗收仍由root接續。本分支不 force push、不合併。
