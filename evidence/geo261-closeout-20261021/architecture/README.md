# GEO-261 收尾架構驗收

目前採用 R3 來源 S `ab6869b86a4ad82345359b72397fc055280d8308`，架構產物提交 A `7159530c0e494d3211e6ab1764eb691137211707`。R3 完整紀錄見 [`r3/README.md`](r3/README.md)，提交綁定見 `metadata-binding-v3.json`。本文件以下保留前輪與 R2 歷史紀錄；其中「最終」與產品 bytes 不變的結論只適用該輪，不延伸至已修改產品 `app.js` 的 R3。

本次靜態架構驗收通過，證據綁定下列兩個 commit：

- 分支：`codex/geo261-closeout-20261021`。
- 實際驗收來源 `sourceBaseHead`：`4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c`。
- 收據及架構 metadata 提交：`c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3`；其直接父節點就是上述來源 commit。
- 先前交接驗收來源：`7dae5f21c7ca401e660450d437e60ba566218da8`。

`c87c6d90` 僅提交 manifest、報告及收據；scan 雖實際重產，bytes 與舊版相同，故 Git 未列為變更。從 `4fe18b8b` 到 `c87c6d90`，全部 610 個架構輸入（含九支收尾工具）的 Git blob 逐一相同。收據沒有把 metadata commit 冒稱成測試當時的 HEAD。

## 實際執行與結果

正式 driver 已包含在來源 commit，執行時工作目錄是 `/workspace/geometry-axiom`：

```sh
python3 -B geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py \
  --root /workspace/geometry-axiom \
  --out /workspace/geo261-evidence/architecture/run-4fe18b8b \
  --source-head 4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c \
  --review-file /workspace/geo261-evidence/architecture/review.json
```

driver 結束碼為 `0`。總日誌是 `refresh-4fe18b8b.log`，各子程序的完整 argv、時間、結束碼及 stdout／stderr 原始雜湊均在 `run-4fe18b8b/<項目>/result.json`。以下三條命令確實重新執行：

重現這次刷新時，先在 `4fe18b8b` 建立乾淨工作樹，並把 `--out` 換成尚不存在的專用目錄；`c87c6d90` 是刷新完成後的產物提交。

| 命令 | 結束碼 | 結果 |
|---|---:|---|
| `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | 0 | 333 個 owned 來源、796 條依賴邊、0 項診斷；5.587 秒 |
| `python3 -B tests/test_architecture_contract.py` | 0 | 205 項通過、0 項失敗、0 項略過；0.465 秒 |
| `python3 -B tests/test_product_architecture.py` | 0 | 18 項通過、0 項失敗、0 項略過；10.301 秒 |

初始舊 manifest 的實際 CLI 先以 `EXCLUSION_DIGEST`、結束碼 `1` 拒絕已變更的 `geometry-web/cdp_test.js`。這是預期紅燈，不算上表新版驗收失敗。新版 manifest 含 **610 個完整輸入 = 333 個 owned 來源 + 277 個逐檔排除項目**；只更新兩個既有測試排除項目的 digest，新增九個具獨立理由及 digest 的收尾工具排除項目。來源根目錄、`sourceFiles`、既有責任分類、918 個禁止識別字及 55 個禁止字串皆未放寬。

## 突變自證

29 項負控制全部要求原始子程序結束碼 `1`，且診斷必須同時指中預期病因與目標檔案：

| 分類 | 項數 | 預期診斷 | 證據目錄 |
|---|---:|---|---|
| 撤回兩個既有測試檔的新 digest | 2 | `EXCLUSION_DIGEST` | `withdraw-digest-0/`、`withdraw-digest-1/` |
| 逐項移除新工具的登記 | 9 | `SOURCE_UNREGISTERED` | `withdraw-registration-0/` 至 `withdraw-registration-8/` |
| 逐項破壞新工具的 digest | 9 | `EXCLUSION_DIGEST` | `corrupt-new-digest-0/` 至 `corrupt-new-digest-8/` |
| 實際 H 來源文字在記憶體依賴各新工具 | 9 | `DEPENDENCY_EXCLUDED`，chain 必須是 `geometry-app/application.js` → 指定工具 | `owned-dependency-0/` 至 `owned-dependency-8/` |

九個工具按路徑排序為 `p189_verify.py`、`p189_verify_build.py`、`p189_verify_equivalence.py`、`p52_probe.js`、`p72_probe.js`、`q38_controls.py`、`refresh_receipt.py`、`run_controls.py`、`run_gates.py`。歷史 P-189 build／equivalence 工具保留完整原始 bytes，明示只服務當時收據溯源；不冒充最新正式 runner。依賴探針只在記憶體加入靜態 `require`，未寫回產品，也不聲稱跨語言依賴可在執行期載入。

這些負控制驗證的是架構登記、digest 與排除依賴守門；P52／P72B 產品驗收驅動器修正的行為突變自證，由另外的瀏覽器證據負責。

## SHA 綁定與不變範圍

新增的 `metadata-binding.json` 與 `gitdiff-7dae-c87.txt` 是完成 metadata commit 後的只讀核對，不更動任何原始執行紀錄。核對以各 commit 的 Git tree／blob 為準；`current_geometry.c` 及其 quoted include 皆以 bytes 讀取，LF 雜湊只做 CRLF→LF 正規化。整體檢查結束碼為 `0`。

| 比對範圍 | 檔案數 | 結果 |
|---|---:|---|
| `7dae5f21` → `c87c6d90` 的既有 owned 產品來源 | 333 | 每個 Git blob 相同 |
| 同範圍的 `sourceFiles`：`current_geometry.c`、`tests/__init__.py`、`tests/binaries.py` | 3 | 每個 Git blob 相同 |
| 同範圍全部版本化 `.c`／`.h`／`.inc` | 345 | 集合及每個 Git blob 相同 |
| 同範圍 `tests/` 下全部遞迴 `.py`（其中根層 `tests/*.py` 為 225 個） | 1471 | 集合及每個 Git blob 相同 |
| 同範圍從 `current_geometry.c` 與 `geometry-web/web_bridge.c` 遞迴跟隨本地 quoted include 的聯集 | 184 | 每個 Git blob 相同；另記 raw／LF SHA-256 |
| `4fe18b8b` → `c87c6d90` 的全部架構輸入 | 610 | 每個 Git blob 相同，含九支新工具 |

quoted include 核對沿用帳本來源收集器同類範圍：只跟隨相對於引用檔實際存在的本地檔案，不執行預處理器或解析編譯器搜尋路徑。30 筆無法在引用檔同目錄直接找到的引用完整列在 JSON；它們不是本次編譯錯誤宣告。另以全部 345 個版本化 C／header／include 檔案都不變的較廣核對覆蓋來源異動檢查。

架構輸入 LF 閉包 SHA-256：`60789fecfee767e1954f15ce7450e5d3a23b4966971d57b810675a2405dc01e3`。

本地 quoted include 聯集 LF 閉包 SHA-256：`872824fc382cb0467591d8df22e375c2e9a6649578b170365246ada795fcce63`。

可以另外直接執行的 Git 差異檢查，本次結束碼亦為 `0`：

```sh
git diff --exit-code 7dae5f21c7ca401e660450d437e60ba566218da8 \
  c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3 -- 'tests/*.py' '*.c' '*.h' '*.inc'
```

上述範圍不變，不等於宣稱兩個版本的整個 repository 相同：兩支瀏覽器測試驅動器確實改動，九支工具確實新增。此處也沒有重新執行突變帳本、native 或其他瀏覽器 job。

## 封裝清單

可直接封裝 `/workspace/geo261-evidence/architecture/` 下的以下明列路徑：

- `README.md`
- `PORTABILITY.md`
- `metadata-binding.json`
- `gitdiff-7dae-c87.txt`
- `review.json`
- `refresh-4fe18b8b.log`
- **完整 `run-4fe18b8b/`**

`run-4fe18b8b/` 共 129 個檔案、6,197,651 bytes；已檢查沒有可執行來源副檔名、執行權限檔案、編譯二進位或完整來源樹快照。它只含原始日誌、JSON、舊／新四份稽核產物及負控制 manifest，可以整份封裝，**run 目錄內無須排除任何檔案**。`previous/` 是四份非可執行稽核產物備份，應保留。

若封裝整個外層目錄，排除外層 **`refresh_receipt.py`** 與 **`__pycache__/`**；正式可執行 driver 已在來源 commit 的 `geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py`，證據包不再放第二份。其餘未列路徑也不要用通配符自動收進。原始收據內的絕對路徑保留作為實跑來源資訊；對外重現所需參數與歷史工具雜湊見 `PORTABILITY.md`。

## 未驗項與不確定性

此包只證明指定來源及其 metadata 後繼的靜態架構。它不證明 native、完整 canvas、Q38、§7 或 P-189 通過，也不把舊 WSL 綠燈重新綁成新 SHA 的實跑。最大限制是靜態依賴掃描與 Git bytes 不變性無法證明執行期行為；瀏覽器修正及 P-189 門檻結果須閱讀各自收據。

## P72 工具更新與用途描述矯正後的最終刷新

以上第一輪內容及 `run-4fe18b8b/` 保留。後續工具來源 `7afacf656912edccc7eb84cb9590990bccae1166` 僅更新既有 `p72_probe.js`，raw SHA-256 改為 `6884e80a843834630b777d2add24e1c07c12ccc33f075a18f02403256d0dfcbc`。產品來源、兩支已修正的瀏覽器驗收模組、其餘工具及架構責任分類沒有因此更動；P72 控制排程的版本界線見 `PORTABILITY.md` 補記。

中間輪 `run-7afacf65/` 的正式 driver 實跑 exit `0`：CLI `0`／5.081 秒，通用測試 `0`／205 項通過／skip 0／0.466 秒，產品測試 `0`／18 項通過／skip 0／10.904 秒；撤回 digest 以正確 `EXCLUSION_DIGEST`、exit `1` 拒絕 P72 工具。獨立複核另發現既有 manifest 理由仍寫舊版本 hash 與已停用的 Document 控制方式。因此該輪產物沒有作為當前 metadata 提交，而是保留全部原始執行紀錄供追溯。

接著將四份產物還原至該輪起點，只把 P72 exclusion 理由改成穩定的驗收工具用途，不含版本 hash，也不聲稱攔截 Document。這個理由修正單獨提交為 `55623598f23e4b630987bb27bbb3f55c10815ea9`（直接父節點 `7afacf656912edccc7eb84cb9590990bccae1166`）。然後用同一支正式 driver、同一份 `review-v2.json`，在此乾淨來源上重新執行；review 中的 `7afacf65` 指已審閱的工具來源 commit，其工具 bytes 與 `55623598` 相同。

```sh
python3 -B geometry-core/domain-decoupling/closeout-tools/refresh_receipt.py \
  --root /workspace/geometry-axiom \
  --out /workspace/geo261-evidence/architecture/run-55623598 \
  --source-head 55623598f23e4b630987bb27bbb3f55c10815ea9 \
  --review-file /workspace/geo261-evidence/architecture/review-v2.json
```

最終 driver 結束碼 `0`；正式 driver raw SHA-256 仍為 `80ecea0cd2d1189f244552d3e92ffc1a81335424410cf4557bac68cd25d15e86`。最新採用證據為 **`run-55623598/`**，它取代中間輪 `run-7afacf65/` 作為當前 metadata 依據，不改寫中間輪或第一輪 raw。

| 最終實跑命令／控制 | 結束碼 | 結果 |
|---|---:|---|
| `python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | 0 | 333 owned、796 edges、0 diagnostics；5.132 秒 |
| `python3 -B tests/test_architecture_contract.py` | 0 | 205／205 通過，skip 0；0.466 秒 |
| `python3 -B tests/test_product_architecture.py` | 0 | 18／18 通過，skip 0；11.150 秒 |
| 舊 manifest 與 `withdraw-digest-0/` | 各 1 | 均精確指出 `p72_probe.js` 的 `EXCLUSION_DIGEST`；0.215／0.265 秒 |

本輪 `updatedExclusions` 只有 P72 工具一項，`addedExclusions` 為空；因此新增工具的三類負控制不適用，沒有冒稱本輪又跑第一輪 29 項。完整輸入仍是 **610 = 333 owned + 277 exclusions**；相對前次封存只有 P72 工具內容變化，來源 LF 閉包 SHA-256 為 `9723ffce54ba1223948a591cf2fd133abb22ad03e43cefcea8a71e61cd14ab9b`。

最終五份執行紀錄及十份原始 stdout／stderr、610 個來源、三支裁判、四新／舊產物皆經獨立複核。第一輪 66 份及中間輪 10 份日誌雜湊也重新核對一致；先前理由矛盾已從當前 manifest 排除。這輪仍只證明靜態架構，不代表 native、完整 canvas 或 P-189 已通過。

封裝清單另追加：`review-v2.json`、`refresh-7afacf65.log`、`refresh-55623598.log`、完整 `run-7afacf65/` 與完整 `run-55623598/`。兩個新 run 各含 26 檔，分別為 1,810,018 與 1,810,138 bytes；均無可執行來源、執行權限檔案、二進位或來源快照，內部無須排除。外層原本的 `refresh_receipt.py` 與 `__pycache__/` 排除規則維持。

## 最終 metadata 提交綁定與交付封裝

最終 metadata commit 是 `366ef501b78105d1f7242dc1f4f4752cac9086b5`，直接父節點為實際驗收來源 `55623598f23e4b630987bb27bbb3f55c10815ea9`。該 commit 只提交 manifest、報告及收據；scan 有重產但 bytes 相同。四份提交後產物皆與 `run-55623598/final/` 原件逐位元組相同。全部 610 個來源輸入及九支工具在 source→metadata 間 Git blob 相同；收據仍誠實記錄實跑時的 `sourceBaseHead`。

`metadata-binding-v2.json` 與 `gitdiff-7dae-366ef501.txt` 保存最後提交後的只讀核對，結束碼 `0`。相對舊驗收來源 `7dae5f21c7ca401e660450d437e60ba566218da8`，333 個 owned、三個 `sourceFiles`、345 個版本化 `.c`／`.h`／`.inc`、1,471 個遞迴 tests Python 檔（其中根層 225 個）均保持相同集合與 Git blob；owned 責任欄位、來源根目錄及守門 policy 也相同。第一份 binding 的 184 個本地 quoted include 閉包檔案已再次核對 Git blob 與 raw／LF 指紋，閉包仍為 `872824fc382cb0467591d8df22e375c2e9a6649578b170365246ada795fcce63`；原先 30 筆無法由本地相對路徑解析的 include 與 collector 範圍限制仍保留，沒有冒稱編譯驗收。

相對第一輪 metadata `c87c6d90`，完整 610 項輸入只有 `p72_probe.js` 一項改變，來源閉包已正確更新為上節的 `9723ffce…`。三輪 raw 日誌共 **43 份執行紀錄、86 份 stdout／stderr** 再次逐一核對原始 SHA-256；沒有覆寫既有證據。

最終外部交付目錄為 `/workspace/geo261-evidence/final-bundle/architecture/`。除前面明列檔案外，加入 `metadata-binding-v2.json`、`gitdiff-7dae-366ef501.txt` 與 `INDEPENDENT_REVIEW.md`；三個完整 run 目錄都保留，`run-7afacf65/` 明示為已被用途描述矯正後重跑取代的中間輪。可執行工具只有 Git 正式來源一份，外部重複 `refresh_receipt.py` 與 `__pycache__/` 不進證據包。

## R3 追加交付

在上述歷史證據外追加完整 `run-ab6869b8/`、`refresh-ab6869b8.log`、`metadata-binding-v3.json`、`gitdiff-7dae-7159530c.txt`，以及 `r3/README.md`、`r3/INDEPENDENT_REVIEW.md`、`r3/review-ab6869b8.json`、`r3/driver-review.json`、`r3/refresh-receipt-report.patch`。外部候選副本 `r3/refresh_receipt.candidate.py` 不收入封裝；已採用的正式工具可由來源 S 取得。

R3 三條 gate 均為 exit `0`，205／18 項全通過、skip 0；五項架構負控制皆精確 exit `1`。A 與 S 的 611 個輸入及四產物綁定已核對。相對 `7dae5f21`，333 個 owned 之中 332 個 bytes 相同，**`geometry-web/app.js` 已變更**；345 個 C/include、1,471 個 tests Python 及 184 個本地 include 閉包檔案保持相同。此不免除產品改動後完整帳本與七項複測義務，詳見 R3 文件的限制。
