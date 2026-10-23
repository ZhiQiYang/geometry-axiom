# #288 新 F 三輪 canvas 終態總結公開封包對抗審

結論：限定三輪原始 canvas 與公開總結，未發現可確立阻擋。source SHA `3d681636902371ecc528b20f51eea33e272581c9`；summary evidence SHA `fdf731e28257c50873cb38e030eed273eeee97fc`（其 parent 精確為第三輪 evidence `0a27637d646362ab20de49aa6621ae4fc0d01032`）。發布退出碼 0；審查時遠端 `a385ccb10adcfbc1aeac146cba05fd59ae7cc60a` 已包含 summary。

三輪均真終態、receipt_verified=true、accepted=true；各輪 launcher／outer／workflow／Node 原退出碼均 0，原 full canvas 均 2267/0、85 段原 golden matched、無 filter/modifier/skip；耗時依序 1741.884308179011、1748.520241596998、1765.1202577359945 秒，皆在原 35 分鐘內。三輪各自預期 fb-auto-probe 例外為 1，不能稱零例外。三輪依原時間序列串行，各 HTTP/CDP 埠與 scratch/profile 獨立。總 driver_exit=0、errors=[]、all_three_completed/all_receipts_verified/all_three_accepted 皆 true；終態為 2026-10-23T12:38:51.680728+00:00。

summary 原件／公開 Git／封包 receipt bytes 全同，SHA256 `c8b61489ee2bdb6e7ff2ceb921163af02b90e346da5d273bb13b9cb8861f60d4`。公開 archive 789,363 bytes、SHA256 `4ba23d6e6cada73cbace936b9fb2db6db468fb7c6a892b21e7ff40aa0e031188`，10 個檔案逐一 bytes/hash 對 inventory 及原 snapshot，excluded=[]。after 三命令原退出碼均 0，完整 index hash 與 sequence before/after 相同，HEAD=F 且 status 空。三個 summary rows 精確對已公開原 terminal rows，三份 receipt hash 對原件、公開 Git 及先前逐輪獨立完整封包審查相同；原 workflow/golden/P88 bytes 對 F 相同，無最佳化旗標。

只執行獨立證據檢查器，未執行任何產品／編譯／Chrome，未寫整合分支。第一次輔助檢查器把原 command returncode 欄位誤寫成 exit，退出 1（KeyError）；原版本與失敗分類已保留 reviewer-first-attempt.*，修正為原 schema 的 actual_process_returncode 後檢查退出 0。沒有變更原收據或產品，也不把這次 reviewer 錯誤當產品紅燈。

三輪綠代表原完整 canvas 已連續三次通過；不代表其他尚未驗收項通過，也未證明自然間歇失敗的根因。CHECKS.json 記錄每輪完整封包審查 hash、三方 receipt 綁定與各項範圍。
