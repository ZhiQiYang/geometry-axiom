# R7 原終態單次封存

來源 F7 `6df0264f75e84f03adb70746b6ac3db07a9910fc`。本工具只封原件，不重測產品、不抽新樣本，不改 v5 原裁判或任何門檻。沿 R6 已審 collector 的完整 byte hashing、7 個 ELF 明確排除／原路徑保留、逐 member tar roundtrip、單包 36 MiB 與 native 128 MiB 餘量。全部新工具／包在 TMP；永久 Git object store 不在 scope。

R6 的判決不能硬套 R7。先由原六檔終態做小投影，保 175 scenes、36 個成功樣本與原 median 驗算、4 個 gprof 點；然後固定原六檔 hash 與當次完整 exit/quantitative_targets。collector 只驗其原 bytes 沒漂移，原產品紅綠由原裁判決定。collect/launch 的 PLAN pin 在真終態後一次綁定，原 templates 與差分保留。缺終態、原 source dirty、缺樣本／原件時拒絕，不補造或自動重試。

本輪 root 提供三個原 write_stdin poll JSON：直接逐 bytes 收錄，沒有改 output／exit 欄。它們與完整 outer Recorder／stage stdin/stdout/stderr 是不同原件；不推論整個 API 回覆序列皆已供給。原五階段只涵蓋 prepare/build/compare/perf/profile，不能冒八階段整體通過。收件成功不等於產品驗收通過。

R7 來源準備 447 檔與其全命令、v5 六工具及既有自驗來源一併收錄。tracked ledger check 實際在 root E51e（與 F7 非 evidence tree 相同）執行，原 1＝120 stale＋3 retired，driver 完成 0 分欄；不冒在薄性能來源直接執行。原 checker 初 reader schema 錯誤亦保留。

準備固定 membership 與工具後，先交獨立靜審；執行 `python3 -B launch.py` 前必須原正式流程終態，並取得一個非阻塞 shared heavy slot。collector 全部 producer stdout/stderr/exit 在本目錄 execution/；它及收件後的 package peer 需要另附出版，不能自稱在既定 tar 內。所有來源、ELF、原 raw 保留，沒有清理動作。

準備失敗與工具自驗：初 freeze 因參照 R6 不存在的 STORAGE_ROUTING.json 真1，未產生 PLAN／collector／包，保原稿與明示事後觀察；改收實存 PROVENANCE.json 後真0。原初 API tool object 沒另存，沒有補造；R2 producer stdout/stderr/exit 已實存。這些準備歷史與 SELFTEST_SUMMARY（純metadata guard 0/1/0）、實際包 peer、collector execution 都需出版時外附；不能宣稱早已放入固定 tar。自驗撤回的是 collector 中錯套 R6 雙紅的判斷，不撤回產品，不是產品性能突變。
