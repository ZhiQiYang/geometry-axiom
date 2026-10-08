# 最後條文缺口補測

本包收凍結條文映射之後的新探針與結果；不覆蓋原 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4` full-CDP 收據或已凍結的 gate matrix。

新補測受測 head 是 `d8642b2e684038cbb8e24aba057c44e7aac1b231`。[來源比對](source-binding-5174-to-d864.json)實際查得兩 head 僅四份 evidence/doc 檔不同，產品來源相同；兩版 runtime version均為 `82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200`。這是來源同一性，不重標原實跑版本。

| 項目 | 當前狀態 | 精確證據 |
|---|---|---|
| SR18 角色鎖因 | 已補證 native 限定範圍 | [獨立審查](sr18-probe/run-01-independent-review.json)、[實跑receipt](gate-receipts/sr18-role-r1/receipt.json)、[原始結果](sr18-probe/run-01/result.json)：合法完整cell／真支持primary正對照成功，只改角色後精確D17/I21 `V_PRIMARY_AXIS`拒絕；dump/refs/revision/hash不變。 |
| SR15 參數與anchor更新 | r2 native限定範圍已補證；r1失敗保留 | [r2獨立審查](sr15-probe/r2-independent-review.json)、[實跑receipt](gate-receipts/sr15-parameter-anchor-r2/receipt.json)、[原始結果](sr15-probe/r2/result.json)。兩面參數、既有guide/direct、單一anchor、完整preview/cancel/history與精確非法拒絕；[r1](sr15-probe/r1/result.json)仍保留錯誤判定與原件。 |
| SR16／23 真UI下游拒絕與順序閉環 | 1400／390 限定流程已獨審核收 | [獨審](sr16-sr23-browser/independent-review/independent-review.json)、[實跑receipt](gate-receipts/sr16-sr23-browser-r1/receipt.json)、[逐寬原件](sr16-sr23-browser/r1/receipt.json)。真拒絕為 R6/I5/I6；兩檔實際皆 /11；完整 traces 保留私有 hash。 |
| ASan/UBSan與#62五類fault injection | 新 baseline 與五項語義反證已獨審；原 runner 退出 1 保留 | [獨審附記](sr62-sanitizer-mutations/independent-review/independent-review.json)、[原始 summary](sr62-sanitizer-mutations/r1/summary.json)、[gate](gate-receipts/sr62-sanitizer-mutations-r1/receipt.json)。M1/M3 原自動分類受 187/189 行 pin 影響，僅追加精確語義分類，不改 verdict；舊 152 原始資料仍 unknown。 |

[補測附錄](verification-addendum.md)解釋新結果如何解除原精確缺口；[凍結映射](../report-support/final-contract-mapping/README.md)保留缺口發現時的source/oracle逐條對照。每項 package-manifest 保存原始來源路徑、bytes 與 hash，[完整重現入口](REPRODUCE.md)列公開 CLI 與依賴。只封存合成 fixture、來源與 text/json 原件；native binaries 及完整 traces 保留私有，只引用身分雜湊。

## 可攜 SR18 重現入口

工作目錄為本證據bundle根目錄（`contract-gap-probes`的父目錄）。先按共同建置命令取得來源匹配的bridge，並檢查checkout完整head。以下所有路徑由執行者替換，`NEW_OUTPUT_DIRECTORY`必須尚不存在；不需要任何歷史 `/workspace` 或 `/tmp` 目錄。

```sh
ulimit -s 16384
GEOMETRY_TEST_BRIDGE=/absolute/path/to/fresh/bridge python3 -B contract-gap-probes/sr18-probe/sr18_role_probe.py --repo /absolute/path/to/checkout --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --out /absolute/path/to/NEW_OUTPUT_DIRECTORY
```

probe強制核source closure、binary sidecar與實際child binary；無自動build、未連既有使用者服務。以其他docs-only交付head執行時，`--head`必須填該次實際完整SHA，新收據亦記該SHA，不能沿抄舊head。

SR15 r2可攜入口（同樣先核fresh bridge，输出目錄須不存在）：

```sh
ulimit -s 16384
python3 -B contract-gap-probes/sr15-probe/r2/executed-probe.py --repo /absolute/path/to/checkout --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --bridge /absolute/path/to/fresh/bridge --out /absolute/path/to/NEW_OUTPUT_DIRECTORY
```

SR16/SR23使用已獲准的本機sandboxed Chromium與隔離HTTP/runtime服務；依本輪同源bridge/model-base啟動後執行，不使用公共tunnel或使用者原服務。其唯一repo helper由`--root`解析，不依賴歷史私有同目錄module。

```sh
python3 -B contract-gap-probes/sr16-sr23-browser/r1/executed-probe.py --root /absolute/path/to/checkout --url http://127.0.0.1:ISOLATED_PORT/ --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --bridge /absolute/path/to/fresh/bridge --model-base /absolute/path/to/fresh/model-base --chrome /absolute/path/to/chromium --out /absolute/path/to/NEW_OUTPUT_DIRECTORY
```
