# 最終 L P-189：門檻未通過

正式來源 `43f85313c32410ac01406ab585846bbacafea278`，分支 `codex/geo261-closeout-20261021`。本包保留正式真碼：generator selftest 0、判定器 selftest 0（16 控制，2 正／14 負）、build 0、equivalence 0、timing 0、**check 1、supervisor 1**。timing 回 0 僅表示收樣完成。

| N | main median 秒 | final median 秒 | final/main | 原門檻 ≤2 |
|---|---:|---:|---:|---|
| 16 | 0.13586991800184478 | 0.15163042600033805 | 1.115997037683347 | 通過 |
| 32 | 0.23936709299960057 | 0.4051768620010989 | 1.69270076735976 | 通過 |
| 48 | 0.357273334000638 | 0.7729609699999855 | 2.1635003131764803 | 失敗 |
| 64 | 0.554064053001639 | 1.5804454290009744 | 2.852459784097019 | 失敗 |

main `adbaebf9c73ea6801d7b4d5214e4b846b132923b`、base `3e600772076465fc65a26ac09055028301c0fb0b`；三方由固定 SHA git archive 新建置，`gcc -std=c11 -O2`，16 MiB stack，移除 PYTHONOPTIMIZE／無 Python -O。每 N 三輪正反交錯，共 36 筆有效樣本；t0 在 Popen 返回後，未宣稱完整程序啟動成本。原門檻與判準未改。

`formal/` 的 1178 檔皆逐 bytes 等同凍結來源與正式 out。175 場景（4 生成＋171 根場景）的三方完整 stdout 全同；100 根場景為預期拒絕。1122 個 stdout／stderr 檔全部保留（525 dump 與36 timing各兩流），共811191 bytes。check 的 dump／完整性／來源判定均通過，失敗原因為 N48 與 N64 速度。完整 argv、phase 真碼、build hash、來源索引、環境與 preflight 都在 formal/。

`first-preparation-failure/` 保留首次 generator-selftest 缺 `calib/f3-00.scene` 的真 exit1：當時未建 binary、未取樣。補同 handoff 固定 blob 的校準原 bytes 後另建正式 out，不覆寫首次原件，不是性能挑樣重跑。來源及校準 blob／hash 在正式 prepare-receipt；產生器原檔可由 handoff `59796b1af9259eb23d30134c2ce5a56317a06091` 還原。

`diagnostic/` 是正式紅後的一次獨立 `-O2 -g -pg -fno-omit-frame-pointer` 診斷，compile／load／gprof 真碼均0；不當正式門檻。完整 nm／objdump／gprof stdout 原 bytes 保存，原 gmon 在外部；包內只保存明示 base64，解碼已逐 bytes 核同。ELF 與來源 tar 不入包，完整來源／flags／hash／命令在 mapping 及原收據。實際成本與 gprof compiler-clone 錯名校正在「診斷說明.md」；單次75樣本不能推論正式牆鐘原因，2跨界樣本未強派。

`source-snapshots/` 是外部監督器、剖析調度及唯讀解析／封裝器實際原 bytes 的純文字來源快照（0644），不是新增產品入口或正式工具部署；外部 .py 原件仍在。正式 runner 使用 L 已登記工具，其來源映射單列，不能把快照當 E 的執行來源。

未驗：此包不是 wd_read 候選驗收，也沒有 main 同 flags profile。最不確定的是哪項成本造成正式倍率，以及固定寬度解碼能否足以解除2倍門檻。來源節點與接觸收集也有明顯成本；#323／#300 工作未混入，P177次數時機未改。PR #288 仍受本結果阻擋，不以本包代決門檻或合併。

`SHA256SUMS` 涵蓋除自身外的全部包內檔案；外部 `p189-final-L-copy-check.json` 保存本次 copy／base64 還原／全包 hash 的真核對結果。
