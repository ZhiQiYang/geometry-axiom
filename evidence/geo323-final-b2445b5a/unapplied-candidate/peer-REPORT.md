# #323 合併 memo／反證候選 v1 靜態對抗審查

候選 `a44018ad1e3455af89dc9fbc19ea4ec3d9b0e4dfec56f9ddab5d2893d91871b0`，基底 b244。本次未發現可確立靜態阻擋；未套用、編譯、測試或量測效能。產品兩檔與已審 memo v2 逐 bytes 相同；本次新增檢查聚焦測試組合。

新 cache-contact 確走原真 contact facts 的 mode3，先驗自然 contact warm；原五個來源的種類／順序、兩 consumer、prefix、重複與 sealed 判定全留。contact-edge／kind 在唯一 shared H placement site 撤邊／換種類，場景呼叫新 contact reader；contact-order 在第二次 hit 先放入原 pose 邊，由原 ordered predicate 判錯，不接受崩潰或 loader 錯誤。contact-id 只撤新 key guard，沿原真 slot permutation 與原 order／footprint marker，沒有修改 memo。

兩個舊漂移控制已收窄：header API 保同一來源與順序目的；cross-consumer 同時封住同一 id3 邊的 W getter 與 H hit 替代路徑，原 placement exact assertion 保留，且明列為語意邊界聯合負控，不宣稱兩個站點各自必要。所有 13 測試方法保留，沒有變更數值門檻、golden、帳本或架構產物。

仍須在正式採用 SHA 實跑具名 0/1/0、原生命週期／failed read／sealed 等套件，以及原完整效能 protocol。新 contact 路徑的動態覆蓋與收益尚未證成；不可從本靜審或原 gprof 推論 ≤1.3、N32/base 或 source-call ratio 已通過。
