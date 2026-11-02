# v5 後續使用邊界

這份草稿只完成工具契約自驗；正式抽樣仍由 root 排程。固定工具由 FINAL_PINS.json 指定，runtime HERE 僅是 tools-v5/ 六個檔案；不要把自驗、README 或其他可變檔案搬進該 runtime 目錄，因原 Session 會將 HERE 全部檔案列入工具閉包。

正式使用必須另建新的 OUT，保留 v4 的 U 原收據和真紅。不可將 v5 接到任何 v4 receipt，也不可為了新的性能數值回寫舊樣本。若同一 v5 OUT 分階段執行，原八 stage 清單、stage 唯一執行限制與完整工具 hash 一致性檢查仍適用。原 compare 紅時，後續 CLI 可能保留累積非零，須分開列原 stage execution、CLI 與 quantitative targets。

正式前由 root 固定乾淨 product SHA、原 base/main 完整 SHA、新 OUT、排程鎖及磁碟／RAM 預算。真 PIPE 將原輸出暫存記憶體，read_output=False 不再代表子程序輸出直接串流到檔案。perf 的所有 recorder 落盤延後至原 perf 返回；遭 SIGKILL 時記憶體內的缺件不可推作完整。flush 出錯則公開錄製失敗，不能擷取先前部分輸出標綠。

v4 原 source_role/source_sha 的 --base 啟發式未改，角色標籤仍須用 acceptance SHA、原 inner 及 source guards 解讀。此修正不變動任何產品碼、judge、比較式、樣本數、順序、timeout 或 timer 邊界，也未證明新性能必過。P52/P189 僅完成限定靜態檢查，詳 P52_P189_SCOPE.md。
