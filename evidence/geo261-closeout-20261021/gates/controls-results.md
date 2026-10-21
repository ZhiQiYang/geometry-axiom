# Q38 裁判控制逐項結果

來源 SHA：`7dae5f21c7ca401e660450d437e60ba566218da8`。
實際控制執行 155.070 秒；原始 gate exit **1**，外層精確核對 exit **0**。
兩組基準分別為 native 27 題、model 20 題，exit 0 且 failure／error／skip 全為 0。

12 個 ID、預期 verdict 與子測試 exit 在執行前已寫入 `run_controls.py` 的 `EXPECTED`；實際結果逐項吻合。9 個 `survived` 是刻意無效或不完整的撤防線控制；3 個 `unlabelled` 是確實轉紅，但病因不等於該正式突變欲偵測的故障，因此裁判拒絕計入 killed。這批控制的 killed／crashed／blocked／invalid 均為 0，不能把此處的「預期吻合」寫成 12 killed。

| 控制 | 撤除內容 | 預期 | 實際 | 子測試 exit |
|---|---|---|---|---:|
| XC36 | 修改已不在 source-graph 路徑上的 W legacy 包絡 | survived | survived | 0 |
| XC39 | 修改已不在 source-graph 路徑上的 W legacy u/v 讀取 | survived | survived | 0 |
| XC40A | 僅讓 K 選世界網格，保留 domain guard | unlabelled | unlabelled | 1 |
| XC40B | 僅刪除 mesh domain guard，保留逐 domain 網格選擇 | survived | survived | 0 |
| XC28L1 | member 缺 profile：只刪 I49 診斷 | survived | survived | 0 |
| XC28L12 | member 缺 profile：保留第三層防線 | survived | survived | 0 |
| XC28L13 | member 缺 profile：保留 profile-definition edge | survived | survived | 0 |
| XC29L1 | run 缺 profile：只刪 I49 診斷 | survived | survived | 0 |
| XC29L12 | run 缺 profile：保留第三層防線 | survived | survived | 0 |
| XC29L13 | run 缺 profile：保留 profile-definition edge | survived | survived | 0 |
| XC03L1 | 只把 u overlap 判式改成閉區間 | unlabelled | unlabelled | 1 |
| XC04L1 | 只把 v overlap 判式改成閉區間 | unlabelled | unlabelled | 1 |

XC40A 的實際終端例外為 `geometry_app.model_common.ModelError`，訊息為 `A mesh requires an arrangement from its coordinate domain`；與正式 SPM40 要求的 `A section-profile object must produce one complete solid` 不同，因此不誤記 killed。

XC03L1、XC04L1 的實際終端例外為 `builtins.AssertionError`。候選被拒的診斷為 `SECTION_PROFILE_INVALID`，訊息 `I51 CAPACITY: section profile source evaluation unavailable`；終端例外全文不含指定 cause `V_PROFILE_OVERLAP`，因此不誤記 killed。完整候選及例外訊息保留在對應 `.log` 與 `.exceptions.json`，沒有以此摘錄取代原件。

實際命令（cwd `/workspace/geo261-gates`，stack 16 MiB）：

```sh
python3 -B /workspace/geo261-evidence/gates/run_controls.py --root /workspace/geo261-gates --out /workspace/geo261-evidence/gates/controls --model-base /workspace/geo261-evidence/gates/bin/model-base --controls /workspace/geo261-evidence/gates/q38_controls.py --jobs 2
```

原始裁判的完整命令、環境、起迄時間與逐案預期／實際映射見 `controls/run-receipt.json`；本次沒有 `--explore`，也沒有省略任何交接控制。執行後工作樹保持乾淨。
