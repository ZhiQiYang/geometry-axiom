# M1 審查修正：執行中進度

分析器修正 `644f187fbca3ac085a48eb1310b0a150625479e3`；原 archive 重分析通過，12 個反例修前錯收／修後拒絕。完整結果後補。

第一輪完整 native 已保留：88 suites，有計數者 2775 pass / 0 fail / 1 個 Windows GDI 平台 skip，但整體 exit 1；mutation:check 額外指出共用快取 45 個 binary 的執行收據不符，因此**本輪不是 native 全綠**。完整 stdout、metadata、全套原日誌在 native-first.tar.gz。

診斷顯示本次帳本與目前來源閉包相符；預設 /tmp/geometry-tests/mutants 的 binary/sidecar 來自不同的舊來源閉包。保留共用快取、不改帳本，改以工具支援的獨立 MUTATE_CACHE 做乾淨 checkout 檢查，結果 stale 0、blocked 0、exit 0。這個可攜收據契約由 tests/mutate.py:723–735 及既有 test_portable_receipt_accepts_clean_checkout_without_temp_binary 明確支援；不是重新執行 45 個 mutant，也不宣稱新突變裁判。cache-diagnosis.json 保留 45 個逐一 binary/hash/closure 比較。

下一步：在相同產品／測試程式、獨立 MUTATE_CACHE 下重跑完整 native。首輪失敗永久保留，不與局部 check 拼成 aggregate 綠燈。不改產品、expected、帳本或來源／收據完整性檢查。
