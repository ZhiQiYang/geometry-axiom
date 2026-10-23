# GEO-261／#288：P88 新 F 的四套原 native 補驗

本分支只封存 #288 在新產品 SHA 的四套受影響 native 補驗，產品來源為 `3d681636902371ecc528b20f51eea33e272581c9`，公開 evidence head 為 `c7214307d5ffc6a867089c8d832fef4bc94ae27c`。原指令在雲端於 2026-10-23 13:12:11–13:15:02 UTC 執行，808 個測試通過，0 fail、0 skip；這是原 runner 明示的 PARTIAL 範圍。#288 其他正式 gate 由整合分支的唯一主矩陣分列，這份元件正文不把它們標成本次已跑。

本元件唯一 current-state 矩陣：

| 項目／原 scope | Product SHA | Evidence head | 原 gate exit／結果 | 允許 skip／仍紅或未跑 |
|---|---|---|---|---|
| `py:test_local_launcher` | `3d681636` | `c7214307` | 0；17/17 | 0 skip |
| `py:test_modeling_transport` | `3d681636` | `c7214307` | 0；3/3 | 0 skip |
| `py:test_serve` | `3d681636` | `c7214307` | 0；51/51 | 0 skip |
| `node:tests-js` | `3d681636` | `c7214307` | 0；737/737 | 0 skip |
| 四套原 aggregate／reaper／outer／launch | `3d681636` | `c7214307` | 0／0／0／0；808/808，metadata complete | 原 PARTIAL；所選範圍無紅燈 |
| 完整 native、瀏覽器及其他專項 | 依整合主矩陣各自原 SHA | 依整合主矩陣 | 本分支沒有重跑其餘項 | 此列不授予 pass 或 skip |

實跑原指令：

```bash
python3 tests/run_all.py --build \
  --only test_local_launcher --only test_modeling_transport \
  --only test_serve --only node:tests-js
```

原 c387 Recorder／原 reaper bytes 未改，stack 由 8 MiB 設為 16 MiB，實際清除後的 `NODE_OPTIONS`／`PYTHONOPTIMIZE` 均為 null。所有 argv、cwd、env、退出碼、完整 stdout/stderr/hash 與 before/after 收據均封存。原 runner 自行判定 core／bridge／model-base 來源與 binary hash fresh 並 reuse；沒有自行組 Node 環境或更改 counts／assertion／threshold。

真版本命令皆 exit 0：Google Chrome 156.0.8078.47、Node v24.19.0、Python 3.12.14、GCC 14.2.0、fonts-noto-cjk 1:20240730+repack1-1。這四套 native 沒有啟動 Chrome，版本收據不冒瀏覽器驗收。

受限雲端磁碟依 root 授權使用稀疏 checkout，完整 Git 歷史／objects／24,213 項 index 保留；根 `evidence/` 與 `tests/evidence/` 未全面物化。原 Node 方法會讀的三個 `.gcanvas`（`legacy6a.gcanvas`、`legacy6a-with-scene.gcanvas`、`legacy/base49-capacity.gcanvas`）已精確物化並逐 bytes 比對同 F Git blob。其他產品、tests、fixtures 保留；不宣稱未物化檔的工作樹 bytes 全等。前後 HEAD／clean status／完整 index hash `41e0e47b1b7f6b166c56b9983b8ac64893272ffd0525a112d9c52fddef8b4f6d` 與 14 項具名輸入完全相同。

公開原件：`evidence/geo288-final-3d681636/` 中 `receipts/native-partial-four.json`、`raw/native-partial-four-01.tar.gz`、逐 member inventory／排除清單與 `SHA256SUMS`。原 receipt SHA-256：`21676d4ab5fd03f2733569d7e69373257d8604ad0cc6bd80f25375a69e4a2fa5`。封包包含原 native、外錄、clone／fixture／稀疏準備、凍結工具及準備／啟動腳本，並已逐 member 重開驗 bytes/hash。

封存過程另有一項已解環境錯誤：既有 publisher 的 `git add --sparse` 因 `.gitignore` 未放行這個新 evidence prefix 而 exit 1。保留原錯誤後，只對已授權精確 prefix 使用 `git add -f --sparse`，diff-check／英文 commit／一般 push／remote head 核對全為 0；未改 `.gitignore` 或產品，也未重跑或改標原 native gate。這項出版收據在 repo 外保留，交由 root 與最後 publication metadata 一併封存。

對抗審由 root 指定另一 owner 核原收據與公開包；尚未收到其終版結果，因此此處沒有冒稱「已審過」。最新主審對 P88 可見性／舊座標因果的限制，仍以整合主正文與獨立 P88 trace 報告為準。

沒有 force push、沒有合併 PR、沒有改 SSOT 或決策佇列。最不確定之處是四套以外的 gate 本分支沒有重跑，其效力必須逐項由整合主矩陣與 closure 證據判斷。
