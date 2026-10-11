# PR #202：四項 workspace timeout 逐項耗時診斷

回應 ChatGPT `6112366196`、dot `6112393871`。兩次實際受測 head 均為
`7002a7b8fd186fff9f3d32c24e97df1b9a2bd78e`；before/after tracked diff 均空。
只透過 `--require preload.cjs` 計時，未修改產品、測試、斷言、5000ms timeout、
Node concurrency、case 選取或 expected counts。這是有插樁的 Linux 診斷，不是正式裁判。

| 原失敗案例（原檔行） | 歷史失敗 ms | 全 Node 探針 ms | 單檔探針 ms | 本次定位 |
|---|---:|---:|---:|---|
| detached prepare / Undo / Redo（948） | 5618.71 | 1400.01 | 647.79 | validate 117 次；commit 824.38 ms、prepare 460.47 ms；Undo/Redo 合計 0.92 ms |
| cancellation / native / metadata（959） | 7706.50 | 1609.34 | 834.81 | 三次 catalog Python 合計 253.17 ms；三次 prepare 合計 1335.75 ms，其中 validate 123 次合計 1004.11 ms |
| no-op / old prepared lease（967） | 6537.09 | 1380.16 | 1198.51 | 三次 prepare 合計 617.88 ms、三次 commit 合計 661.14 ms；validate 237 次合計 950.11 ms；Undo/Redo 合計 0.78 ms |
| near-limit full manifest（975） | 6914.71 | 1872.39 | 1603.26 | 建立 33×250000 字元 drafts；三次容量檢查合計 999.39 ms、validate 29 次合計 545.21 ms；prepare 於 HTTP 前以原 8 MB 錯誤拒絕 |

表內步驟包含巢狀呼叫，**不可相加當總耗時**。CPU usage 不包含 Python 子行程，
探針本身也有成本。`case-timings.json` 保留各步驟 count / total / maximum，
各 PID `.jsonl` 保留每次耗時、CPU、原錯誤；未記錄資料 payload 或憑證。

靜態路徑：`reference-workspace.js:454` 的 prepare 先 `Features.record`、
`featureProposal`，後者由 `assertMetadataCapacity` → manifest → capacity/feature
validators 反覆檢查完整附件；commit 在寫歷史前再次驗 proposal。取消案例刻意跑三種
狀態變更，no-op 案例刻意跑三次 prepare；容量案例在完整清單檢查階段拒絕，沒有 HTTP。
沒有為了省時移除任何驗證或改成延後容量檢查。

`whole-node/` 使用原 registry 全部 36 JS 檔及 fresh runner 環境，651/651，
0 fail/cancelled/skip，Popen 直接 returncode 0，90.69 秒。
`isolated/` 使用同一 fresh 環境與原 races 全檔，61/61、0 skip，直接 returncode 0，7.81 秒。
可用版本化 `run.py` 重建探針批次；路徑指向本次 `/tmp` scratch，非正式入口。

Node 回報 availableParallelism=4，cgroup 配額 4 CPU，觀察到最多 4 Node processes；
本次全 Node cgroup throttled delta=8 periods / 514474 µs。此資料涵蓋整個環境，
不證明歷史批次 CPU 爭用或 timeout 根因；半秒 `/proc` 抽樣也不是強制獨占。
沒有足夠證據將失敗歸因 native 幾何、Python catalog、HTTP、死鎖或 flaky。
原來 5.6–7.7 秒的四項 timeout **仍未重現，根因未定**。

`source-controls.json` 驗證 races、workspace、project-store、catalog 的 LF-normalized
bytes 與精確 base `635dd86ee368579aec444fb3ba16e48bccf4877e` 一致。
這只表示這四個檔未改，**不證明 main 同案例失敗或准許豁免**。
原完整 83 suite 的 2721 pass / 9 fail / 1 allowed GDI skip、returncode 1 仍有效；
這兩次診斷不能拼成全量綠燈。原 BrokenPipe 同樣未定位、未豁免。

正典同步 owner 仍為 PR #192，head `02c20374a7f2798794a5237072b2216ceba2af5c`；
`owner192.json` 保存本次遠端查詢。原 writer 已接受 Claude 授權並排隊，尚未交付同步。
須在最終整合 head 納入 R7/R12/R14/R15，原位 sync → check → 原 41 tests。
本線沒有修改正典；正式同 SHA 七 job、Windows GDI 與全程強制隔離仍待。
