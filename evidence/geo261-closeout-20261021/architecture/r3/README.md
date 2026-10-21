# R3 產品空態修正後的架構驗收

實際受測來源 S 為 `ab6869b86a4ad82345359b72397fc055280d8308`，分支 `codex/geo261-closeout-20261021`。本輪產品 `geometry-web/app.js` 已變更，保留原 H owned 分類；另更新既有 `uiux_review_test.js`、架構刷新工具，並新增第十支收尾工具 `p73_probe.js`。不能沿用 R2「333 個 owned 產品來源與 7dae 全部 bytes 相同」的結論。

前輪 `run-4fe18b8b/`、`run-7afacf65/`、`run-55623598/` 及 R2 提交 `366ef501b78105d1f7242dc1f4f4752cac9086b5` 的封裝均保留為歷史證據。本輪新增獨立 `run-ab6869b8/`，未覆寫舊 raw。

## 實際命令與結果

在 repository 根目錄執行已提交的正式工具：

```sh
python3 -B geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py \
  --root /workspace/geometry-axiom \
  --out /workspace/geo261-evidence/architecture/run-ab6869b8 \
  --source-head ab6869b86a4ad82345359b72397fc055280d8308 \
  --review-file /workspace/geo261-evidence/architecture/r3/review-ab6869b8.json
```

driver 結束碼為 `0`。完整輸出另存 `../refresh-ab6869b8.log`；每條子程序的 argv、來源 SHA、時間、結束碼及原始 stdout／stderr 雜湊位於 `../run-ab6869b8/<項目>/result.json`。

| 真正執行的驗收 | 結束碼 | 結果 |
|---|---:|---|
| `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | 0 | 333 owned、796 edges、0 diagnostics；5.402 秒 |
| `python3 -B tests/test_architecture_contract.py` | 0 | 205／205 通過，skip 0；0.466 秒 |
| `python3 -B tests/test_product_architecture.py` | 0 | 18／18 通過，skip 0；12.457 秒 |

新版清單是 **611 inputs = 333 owned + 278 exclusions**；source roots、sourceFiles、責任分類及守門 policy 維持原契約。scan 確實重產，bytes 與前版相同，因此只有 manifest、report、receipt 三份產物形成 Git diff。`git diff --check` 結束碼 `0`。

## 五項負控制

初始舊 manifest 先以 `EXCLUSION_DIGEST`、exit `1` 拒絕變更；這不算新版驗收失敗。新版再逐項執行下列控制，全部精確命中預期目標與診斷，原始子程序均為 exit `1`：

| 證據子目錄 | 目標 | 必要診斷 |
|---|---|---|
| `withdraw-digest-0/` | `geometry-web/uiux_review_test.js` | `EXCLUSION_DIGEST` |
| `withdraw-digest-1/` | `geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py` | `EXCLUSION_DIGEST` |
| `withdraw-registration-0/` | 新增 `p73_probe.js` | `SOURCE_UNREGISTERED` |
| `corrupt-new-digest-0/` | 新增 `p73_probe.js` | `EXCLUSION_DIGEST` |
| `owned-dependency-0/` | 實際 H 來源 `geometry-app/application.js` 的記憶體文字加入對 P73 工具的靜態依賴 | `DEPENDENCY_EXCLUDED`；chain 必須精確指向該工具 |

這些控制只證明架構登記、摘要與禁止產品依賴排除工具的守門，不冒充 P73 行為突變自證。依賴探針未寫回產品，亦不聲稱任何跨語言依賴可在執行期載入。

## 完整來源變化與限制

來源 LF 閉包 SHA-256 為 `4be326e07260a35b456ef4e8d46f50c28432216f66e45c5afc56d46d5313ce9b`。收據的 `inputsChangedSincePreviousSeal` 明列以下四項：

| 路徑 | 本次 raw／LF SHA-256 |
|---|---|
| `geometry-web/app.js`，既有 H owned 產品來源 | `0913168bc7792c20d2bece26e574288ae160c45feed2fd2ea24ed0a2898fbc5f` |
| `geometry-web/uiux_review_test.js`，既有驗收排除項目 | `0925c130aa7488d54b5e2ed539ef21f5b653fbbdebd0910f71a1992871149604` |
| `geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py`，既有工具排除項目 | `b0b80afbdbbbb451ab29e774ffbdd1699f0438619b5f84280ef954c8b72fc5a3` |
| `geometry-core/domain-decoupling/closeout-tools/p73_probe.js`，新增逐檔工具排除項目 | `f12ab05083a0b2f994b34ee78b3990c8873aa749309ea132267ecfd599f32faf` |

全部 611 個來源、三支裁判及 HEAD 在每條命令前後和封存時重新核對；完整九份執行紀錄及十八份原始 stdout／stderr 已核對其 SHA-256。四份舊產物逐位元組保留於 `previous/`，新四份保留於 `final/`。

此輪只證明靜態架構。產品碼已改，因此完整突變帳本及七項驗收須依交接規則在適用來源另行實跑；即使 C/include 與 tests Python 的 Git bytes 不變，也不能拿架構證據取代那些關卡。native、完整 canvas、Q38、§7、P-189 及 P73 真瀏覽器控制均由各自收據負責，未在本輪架構命令內執行。

## 外部候選與封裝界線

`driver-review.json` 保存原版與候選 hash、語法及最小補丁核對；`refresh-receipt-report.patch` 是已採入來源 S 的文字修改。`refresh_receipt.candidate.py` 只供採用前對照，不收入證據包，正式可執行工具已在 Git 中。新 P73 工具的 repo 預設依正式檔案位置向上三層取得，重現時仍建議明示第一個 repository 路徑參數；實際來源替換、控制模式及瀏覽器結果須讀各自 `probeSha256` 與原始日誌。

## 提交 A 的綁定

架構產物提交 A 為 `7159530c0e494d3211e6ab1764eb691137211707`，直接父節點就是受測來源 S `ab6869b86a4ad82345359b72397fc055280d8308`。A 只改 manifest、report、receipt；scan 已重產但 bytes 相同。A 的四產物與 `run-ab6869b8/final/` 逐位元組一致，S 的四起始產物與 `previous/` 逐位元組一致；611 個來源及十支收尾工具在 S→A 間的 Git blob 全部相同。

`../metadata-binding-v3.json` 保存提交後只讀核對，結束碼 `0`。相對舊驗收來源 `7dae5f21c7ca401e660450d437e60ba566218da8`，333 個 owned 的責任欄位完全相同，但只有 **332 個內容不變**；唯一 owned 內容變更為 `geometry-web/app.js`，由 `362999f2ddd793c832f762f7fb882e7db647091dfde5b4ebb3ee5fd493a77b4b` 改為 `0913168bc7792c20d2bece26e574288ae160c45feed2fd2ea24ed0a2898fbc5f`。這項產品改動不是 exclusion。

同範圍三個 `sourceFiles`、345 個版本化 `.c`／`.h`／`.inc`、1,471 個遞迴 tests Python（根層 225 個）均保持集合與 Git blob 相同；另完整核對 `tests/` 的 15,851 個版本化檔案也相同。既有 184 個本地 quoted include 閉包檔案的 Git blob、raw／LF 指紋再次核對，閉包仍為 `872824fc382cb0467591d8df22e375c2e9a6649578b170365246ada795fcce63`。原 30 筆無法由引用檔同目錄解析的 include 與收集範圍限制仍保留，不代表預處理或編譯驗收。

四輪原始證據共 52 份執行紀錄、104 份 stdout／stderr 重新核對雜湊一致。R3 `run-ab6869b8/` 本身有 41 檔、2,470,884 bytes，沒有可執行來源、二進位、符號連結或檔案執行權限，可完整收入封裝，內部無須排除。

這些只讀 Git 核對不替代產品碼改動後的完整突變帳本或七項複測。原獨立審查代理已複核來源 S 的完整架構 gate 包；提交 A 的綁定由封裝代理另外執行並保存，沒有將兩者混稱為同一時刻的獨立重跑。
