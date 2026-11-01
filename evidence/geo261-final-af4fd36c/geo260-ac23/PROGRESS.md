# GEO260 AC23 具名反證進度

本次實測測試來源 S=`af4fd36c17d05b5da2411b70266ed040e22a6561`，固定基底 `5b0ce47d25393fad675bf506a9d296cbab43c35d`。本目錄是該來源的獨立證據；不是整合列車的新 SHA 全量驗收。

| 正式項目 | 原結果 | 範圍 |
|---|---|---|
| 原 Python gate 單元 | exit 0；Ran 30、OK | selection／exception-evidence 單元；不是 native aggregate 30 |
| 首輪 focused gate（c9269e13） | exit 2 | baseline 29：原 27 過、新 2 因錯讀 id 出現 KeyError；只 1 build、mutants 未啟動，原紅保留 |
| schema 修正 | af4，兩處 id → value.id | 六個字面矩形斷言全保，獨立靜審 16／0 |
| 修正後原 focused gate | exit 0 | baseline 29／0；SPM43、SPM44 各 exit 1、killed，皆唯一指定 AC23 AssertionError；3 builds |
| 同 hash baseline 恢復 | exit 0；Ran 2、OK | 各控制真 0／1／0；原保留 ELF 不動，以相同 bytes 的私有可執行副本恢復 |
| 獨立 actual 對抗審查 | 1252 checks／0 findings | 585 C 輸入、3 ELF、原 streams、具名失敗、固定 Git 閉包皆核；非 full44 或 aggregate30 |
| 完整 44-case gate／native30 aggregate | 未跑 | focused 不替代完整閘門；shared expected 28→30 仍待主代理合流順序更新 |
| full native／6 browser／帳本／架構 | 本分支未跑 | 全帳本 M 定義 123 未動，本分支不重產 |

原命令：`python3 -B tests/section_profile_mutation_check.py --group native --only SPM43 --only SPM44 --jobs 1 --receipt <out>/gate/gate-receipt.json --logs <out>/gate/gate-logs`。旁錄工具只保留原 cleanup 前輸入與 ELF，不改產品、測試函數、argv、退出碼或原 600／900 秒時限。原 runner 的 exception、cause 與 verdict 判官全保。

SPM43／44 使用原 SPM03／04 的故障及相同 PAIR_CORNERS 閉包，各 killer 只綁一個新的 AC23 方法。原 42 cases、28 方法及既有 killer 沒有更動；I45／R36 的正面積與等號接觸契約未改。

原件封包 `geo260-ac23-originals-af4fd36c.tar.gz`：1148 regular members、18,522,072 原 bytes；封包 SHA256 `228b54b277678d8dda80a1f67a025ac7602ca6d21914243c13f1042df510155d`。完整逐檔 hash／來源／ELF 排除清單在 RAW_INVENTORY.json；ELF 原件仍留雲端，沒有刪除。封包含首輪紅、修正、原完整輸出／環境／SHA、實際 C、單元與靜／動態 peer。封包本機解壓串接逐 bytes 核對已過；獨立 public Git／body peer 已核 E023 原包 2354 checks／0，SHA256 `a81e4c9f165f7a8436bb33b380cc33cbf57a544ac11858a98f0c2ef55507a28b`。全文及原 publisher 指令輸出在本目錄，非重測。

限制：首輪未在後續 schema 編輯前另錄 final-clean，照實保留；修正輪有初末 HEAD／clean。原子 exception row 沒有 SHA 欄，未填造欄位，以父命令與原輸入間接綁定。封包中的 preparation/PR_BODY.md、SCHEMA_CORRECTION_RESULT.json 是準備當時的歷史狀態，唯一 current-state 以本表為準。

下一步：依序合流更新 expected 28→30，再在最終 SHA 跑完整正式項目。GEO260 的實跑已釋放第二槽，沒有 C／Chrome consumer；#335 準備另放 repo 外，沒有混入本分支。
