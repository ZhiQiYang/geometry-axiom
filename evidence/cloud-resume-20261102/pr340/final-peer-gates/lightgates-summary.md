# #340 final b3a 原 source lightgates

固定來源 `b3a248607d7eb68d3167abbb926cf491d9b35a26`；工作區 `/tmp/geometry-pr340-20261102`。執行前後 HEAD 相同、`git status --porcelain=v1` 空白。本輪產物均新存於本目錄；舊 `1605a6c27c97c2aa5e6405bddc7d3b31f1fdd965` 的 lightgate 結果仍屬於舊來源，沒有改標或沿用。

| 原命令 | 結果 |
|---|---|
| `python -B tests/mutate.py --check` | exit 0；表／原帳本 123／123，114 killed、1 crashed、5 equivalent、3 retired，其餘異常 0 |
| `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | exit 0；ok=true、798 edges、diagnostics=[] |
| `python -B tests/test_architecture_contract.py` | exit 0；205 tests、零 skip |
| `python -B tests/test_product_architecture.py` | exit 0；18 tests、零 skip |

精確命令、cwd、head、時間、exit 與原 stdout／stderr SHA-256 在 `lightgates-receipt.json`；raw 保留為四組同名 `.stdout`／`.stderr`。`MUTATE_CACHE` 指向本目錄新建空資料夾，事後仍空；沒有 build、重編或執行下載的二進位，也沒有觸及 shared mutation cache。

這次 `--check` 讀取的是 b3a 工作區中維持 main 原件的 `tests/mutants_results.json`，證明來源／裁判／既有執行收據一致；不宣稱 b3a 已有新的完整 mutation 執行或已核對本機二進位 bytes。正式 b3a integration／mutation CI 尚未由本輪產生或核收；#366 的 502a 綠燈不移標為 b3a。

只讀 GitHub metadata 本輪一次觀測到 main 仍為固定 `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d`；HTTP 200 與原件 hash 見 `metadata-receipt.json`。未更新 main、未跟隨遠端移動、未 push／留言／新開 CI。獨立來源 peer 的精確 diff／blob／lineage 核對另見 `source-peer-review.md`。
