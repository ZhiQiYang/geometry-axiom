# PF-1 原生完成面跟進驗證

本次受測來源 commit `869459949a59db5ab894f1d55e7944ea43ff06ab`，承接修前 `ba25d99c61de03d7813f073b2015894e8547b419`；2026-10-12 透過 WSL v3 排隊鎖執行。本文與突變結果是後續證據提交，產品／測試來源不變。行為依公理層 D41／I33／I52／I55／R41；PF-1 只交付原生定義、障礙投影、候選交易及場景保存，後續 UI／鋪排仍需另驗。

## 修正與反例

- I55：混合範圍外操作可回報已形成的候選 created id=1；候選整體無效，不可確認，正式 dump／revision／redo 保留。原來把候選差異要求為空的新增期待已依審查授權更正，零提交檢查保留。
- I33：原生完成面以獨立診斷類別區分能力／容量不足與幾何 INVALID；橋接器在候選狀態求值前保存分類，序列化也保留它。第 17 個完成面為 UNSUPPORTED／CAPACITY，缺失邊界仍為 INVALID。修前容量案例確實失敗。
- PF12：以 PF-0 `444a871c87d78f8a12fd40f8cd79c3e6621ff393` 獨立產生五份 dump bytes，凍結於 `tests/fixtures/pf1-legacy-dumps.json`。舊測試在空 dump 負控制下仍綠；新測試對五場景全部拒絕，還原通過。夾具 SHA-256 `422f04118aa785c56f516fa5fe2086eed808c02633b4b6f0e0cec5fd34874eea`。

## 執行結果

| 檢查 | 退出碼 | 秒數 |
|---|---|---|
| baseline-native | 0 | 9.749 |
| baseline-transport | 0 | 0.171 |
| baseline-http | 0 | 1.375 |
| restored-native | 0 | 5.952 |
| restored-transport | 0 | 0.336 |
| restored-http | 0 | 2.711 |
| full-mutation | 0 | 1033.663 |
| mutation-check | 0 | 0.599 |

前後各為原生 19/19、傳輸 7/7、HTTP 1/1，無錯誤或略過。14 個定向突變各在指定方法觸發行為斷言失敗；每個來源檔逐位元還原，末輪再次通過原生／傳輸／HTTP。橋接器 sidecar、實算二進位 SHA-256 與每次突變的來源及 patch SHA 皆在收據。

全表共 48 筆：40 killed、1 crashed、4 equivalent、3 retired；`mutate.py --check` exit 0。crashed 與 killed 分列；來源、include 閉包、變異與裁判指紋重新產生。

修前 18 次、修後 95 次排他取樣均未見外來程序。原始紀錄位於本次 scratchpad 的 `board-local-codex/pr190-red/` 與 `board-local-codex/pr190-proof-86945994/`，包含完整命令、秒數、退出碼、原始 log、fingerprints 及還原紀錄；後續附於 PR #190。這是定向測試與完整核心突變表，尚非七 job 裁判。

## 範圍

沒有新增 UI 入口。PF11 的新瀏覽器重開、`.gcanvas` 正式保存、I53 分層，以及 PF-2 至 PF-6 均待後續切片。標準 native／瀏覽器七 job 依落地優先序另排；CI 受帳號計費阻擋，以本機 WSL 收據代替。Windows 原生編譯未執行。
